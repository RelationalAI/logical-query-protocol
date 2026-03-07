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
    _t1494 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1494
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1495 = Proto.Value(value=OneOf(:int_value, v))
    return _t1495
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1496 = Proto.Value(value=OneOf(:float_value, v))
    return _t1496
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1497 = Proto.Value(value=OneOf(:string_value, v))
    return _t1497
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1498 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1498
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1499 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1499
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1500 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1500,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1501 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1501,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1502 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1502,))
            end
        end
    end
    _t1503 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1503,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1504 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1504,))
    _t1505 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1505,))
    if msg.new_line != ""
        _t1506 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1506,))
    end
    _t1507 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1507,))
    _t1508 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1508,))
    _t1509 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1509,))
    if msg.comment != ""
        _t1510 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1510,))
    end
    for missing_string in msg.missing_strings
        _t1511 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1511,))
    end
    _t1512 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1512,))
    _t1513 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1513,))
    _t1514 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1514,))
    if msg.partition_size_mb != 0
        _t1515 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1515,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1516 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1516,))
    _t1517 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1517,))
    _t1518 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1518,))
    _t1519 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1519,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1520 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1520,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1521 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1521,))
        end
    end
    _t1522 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1522,))
    _t1523 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1523,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1524 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1524,))
    end
    if !isnothing(msg.compression)
        _t1525 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1525,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1526 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1526,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1527 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1527,))
    end
    if !isnothing(msg.syntax_delim)
        _t1528 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1528,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1529 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1529,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1530 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1530,))
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
        _t1531 = nothing
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
    flat678 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat678)
        write(pp, flat678)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1338 = _dollar_dollar.configure
        else
            _t1338 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1339 = _dollar_dollar.sync
        else
            _t1339 = nothing
        end
        fields669 = (_t1338, _t1339, _dollar_dollar.epochs,)
        unwrapped_fields670 = fields669
        write(pp, "(transaction")
        indent_sexp!(pp)
        field671 = unwrapped_fields670[1]
        if !isnothing(field671)
            newline(pp)
            opt_val672 = field671
            pretty_configure(pp, opt_val672)
        end
        field673 = unwrapped_fields670[2]
        if !isnothing(field673)
            newline(pp)
            opt_val674 = field673
            pretty_sync(pp, opt_val674)
        end
        field675 = unwrapped_fields670[3]
        if !isempty(field675)
            newline(pp)
            for (i1340, elem676) in enumerate(field675)
                i677 = i1340 - 1
                if (i677 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem676)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat681 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat681)
        write(pp, flat681)
        return nothing
    else
        _dollar_dollar = msg
        _t1341 = deconstruct_configure(pp, _dollar_dollar)
        fields679 = _t1341
        unwrapped_fields680 = fields679
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields680)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat685 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat685)
        write(pp, flat685)
        return nothing
    else
        fields682 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields682)
            newline(pp)
            for (i1342, elem683) in enumerate(fields682)
                i684 = i1342 - 1
                if (i684 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem683)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat690 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat690)
        write(pp, flat690)
        return nothing
    else
        _dollar_dollar = msg
        fields686 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields687 = fields686
        write(pp, ":")
        field688 = unwrapped_fields687[1]
        write(pp, field688)
        write(pp, " ")
        field689 = unwrapped_fields687[2]
        pretty_value(pp, field689)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat716 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat716)
        write(pp, flat716)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1343 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1343 = nothing
        end
        deconstruct_result714 = _t1343
        if !isnothing(deconstruct_result714)
            unwrapped715 = deconstruct_result714
            pretty_date(pp, unwrapped715)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1344 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1344 = nothing
            end
            deconstruct_result712 = _t1344
            if !isnothing(deconstruct_result712)
                unwrapped713 = deconstruct_result712
                pretty_datetime(pp, unwrapped713)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1345 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1345 = nothing
                end
                deconstruct_result710 = _t1345
                if !isnothing(deconstruct_result710)
                    unwrapped711 = deconstruct_result710
                    write(pp, format_string(pp, unwrapped711))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                        _t1346 = _get_oneof_field(_dollar_dollar, :int_value)
                    else
                        _t1346 = nothing
                    end
                    deconstruct_result708 = _t1346
                    if !isnothing(deconstruct_result708)
                        unwrapped709 = deconstruct_result708
                        write(pp, format_int(pp, unwrapped709))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                            _t1347 = _get_oneof_field(_dollar_dollar, :float_value)
                        else
                            _t1347 = nothing
                        end
                        deconstruct_result706 = _t1347
                        if !isnothing(deconstruct_result706)
                            unwrapped707 = deconstruct_result706
                            write(pp, format_float(pp, unwrapped707))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                _t1348 = _get_oneof_field(_dollar_dollar, :uint128_value)
                            else
                                _t1348 = nothing
                            end
                            deconstruct_result704 = _t1348
                            if !isnothing(deconstruct_result704)
                                unwrapped705 = deconstruct_result704
                                write(pp, format_uint128(pp, unwrapped705))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                    _t1349 = _get_oneof_field(_dollar_dollar, :int128_value)
                                else
                                    _t1349 = nothing
                                end
                                deconstruct_result702 = _t1349
                                if !isnothing(deconstruct_result702)
                                    unwrapped703 = deconstruct_result702
                                    write(pp, format_int128(pp, unwrapped703))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                        _t1350 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                    else
                                        _t1350 = nothing
                                    end
                                    deconstruct_result700 = _t1350
                                    if !isnothing(deconstruct_result700)
                                        unwrapped701 = deconstruct_result700
                                        write(pp, format_decimal(pp, unwrapped701))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                            _t1351 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                        else
                                            _t1351 = nothing
                                        end
                                        deconstruct_result698 = _t1351
                                        if !isnothing(deconstruct_result698)
                                            unwrapped699 = deconstruct_result698
                                            pretty_boolean_value(pp, unwrapped699)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                                                _t1352 = _get_oneof_field(_dollar_dollar, :int32_value)
                                            else
                                                _t1352 = nothing
                                            end
                                            deconstruct_result696 = _t1352
                                            if !isnothing(deconstruct_result696)
                                                unwrapped697 = deconstruct_result696
                                                write(pp, (string(Int64(unwrapped697)) * "i32"))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                                    _t1353 = _get_oneof_field(_dollar_dollar, :float32_value)
                                                else
                                                    _t1353 = nothing
                                                end
                                                deconstruct_result694 = _t1353
                                                if !isnothing(deconstruct_result694)
                                                    unwrapped695 = deconstruct_result694
                                                    write(pp, (lowercase(string(unwrapped695)) * "f32"))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                                        _t1354 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                                    else
                                                        _t1354 = nothing
                                                    end
                                                    deconstruct_result692 = _t1354
                                                    if !isnothing(deconstruct_result692)
                                                        unwrapped693 = deconstruct_result692
                                                        write(pp, (string(Int64(unwrapped693)) * "u32"))
                                                    else
                                                        fields691 = msg
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
    flat722 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat722)
        write(pp, flat722)
        return nothing
    else
        _dollar_dollar = msg
        fields717 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields718 = fields717
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field719 = unwrapped_fields718[1]
        write(pp, format_int(pp, field719))
        newline(pp)
        field720 = unwrapped_fields718[2]
        write(pp, format_int(pp, field720))
        newline(pp)
        field721 = unwrapped_fields718[3]
        write(pp, format_int(pp, field721))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat733 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat733)
        write(pp, flat733)
        return nothing
    else
        _dollar_dollar = msg
        fields723 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields724 = fields723
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field725 = unwrapped_fields724[1]
        write(pp, format_int(pp, field725))
        newline(pp)
        field726 = unwrapped_fields724[2]
        write(pp, format_int(pp, field726))
        newline(pp)
        field727 = unwrapped_fields724[3]
        write(pp, format_int(pp, field727))
        newline(pp)
        field728 = unwrapped_fields724[4]
        write(pp, format_int(pp, field728))
        newline(pp)
        field729 = unwrapped_fields724[5]
        write(pp, format_int(pp, field729))
        newline(pp)
        field730 = unwrapped_fields724[6]
        write(pp, format_int(pp, field730))
        field731 = unwrapped_fields724[7]
        if !isnothing(field731)
            newline(pp)
            opt_val732 = field731
            write(pp, format_int(pp, opt_val732))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1355 = ()
    else
        _t1355 = nothing
    end
    deconstruct_result736 = _t1355
    if !isnothing(deconstruct_result736)
        unwrapped737 = deconstruct_result736
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1356 = ()
        else
            _t1356 = nothing
        end
        deconstruct_result734 = _t1356
        if !isnothing(deconstruct_result734)
            unwrapped735 = deconstruct_result734
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat742 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat742)
        write(pp, flat742)
        return nothing
    else
        _dollar_dollar = msg
        fields738 = _dollar_dollar.fragments
        unwrapped_fields739 = fields738
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields739)
            newline(pp)
            for (i1357, elem740) in enumerate(unwrapped_fields739)
                i741 = i1357 - 1
                if (i741 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem740)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat745 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat745)
        write(pp, flat745)
        return nothing
    else
        _dollar_dollar = msg
        fields743 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields744 = fields743
        write(pp, ":")
        write(pp, unwrapped_fields744)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat752 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat752)
        write(pp, flat752)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1358 = _dollar_dollar.writes
        else
            _t1358 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1359 = _dollar_dollar.reads
        else
            _t1359 = nothing
        end
        fields746 = (_t1358, _t1359,)
        unwrapped_fields747 = fields746
        write(pp, "(epoch")
        indent_sexp!(pp)
        field748 = unwrapped_fields747[1]
        if !isnothing(field748)
            newline(pp)
            opt_val749 = field748
            pretty_epoch_writes(pp, opt_val749)
        end
        field750 = unwrapped_fields747[2]
        if !isnothing(field750)
            newline(pp)
            opt_val751 = field750
            pretty_epoch_reads(pp, opt_val751)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat756 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat756)
        write(pp, flat756)
        return nothing
    else
        fields753 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields753)
            newline(pp)
            for (i1360, elem754) in enumerate(fields753)
                i755 = i1360 - 1
                if (i755 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem754)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat765 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat765)
        write(pp, flat765)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1361 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1361 = nothing
        end
        deconstruct_result763 = _t1361
        if !isnothing(deconstruct_result763)
            unwrapped764 = deconstruct_result763
            pretty_define(pp, unwrapped764)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1362 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1362 = nothing
            end
            deconstruct_result761 = _t1362
            if !isnothing(deconstruct_result761)
                unwrapped762 = deconstruct_result761
                pretty_undefine(pp, unwrapped762)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1363 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1363 = nothing
                end
                deconstruct_result759 = _t1363
                if !isnothing(deconstruct_result759)
                    unwrapped760 = deconstruct_result759
                    pretty_context(pp, unwrapped760)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1364 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1364 = nothing
                    end
                    deconstruct_result757 = _t1364
                    if !isnothing(deconstruct_result757)
                        unwrapped758 = deconstruct_result757
                        pretty_snapshot(pp, unwrapped758)
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
    flat768 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat768)
        write(pp, flat768)
        return nothing
    else
        _dollar_dollar = msg
        fields766 = _dollar_dollar.fragment
        unwrapped_fields767 = fields766
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields767)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat775 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat775)
        write(pp, flat775)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields769 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields770 = fields769
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field771 = unwrapped_fields770[1]
        pretty_new_fragment_id(pp, field771)
        field772 = unwrapped_fields770[2]
        if !isempty(field772)
            newline(pp)
            for (i1365, elem773) in enumerate(field772)
                i774 = i1365 - 1
                if (i774 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem773)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat777 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat777)
        write(pp, flat777)
        return nothing
    else
        fields776 = msg
        pretty_fragment_id(pp, fields776)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat786 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat786)
        write(pp, flat786)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1366 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1366 = nothing
        end
        deconstruct_result784 = _t1366
        if !isnothing(deconstruct_result784)
            unwrapped785 = deconstruct_result784
            pretty_def(pp, unwrapped785)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1367 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1367 = nothing
            end
            deconstruct_result782 = _t1367
            if !isnothing(deconstruct_result782)
                unwrapped783 = deconstruct_result782
                pretty_algorithm(pp, unwrapped783)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1368 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1368 = nothing
                end
                deconstruct_result780 = _t1368
                if !isnothing(deconstruct_result780)
                    unwrapped781 = deconstruct_result780
                    pretty_constraint(pp, unwrapped781)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1369 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1369 = nothing
                    end
                    deconstruct_result778 = _t1369
                    if !isnothing(deconstruct_result778)
                        unwrapped779 = deconstruct_result778
                        pretty_data(pp, unwrapped779)
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
    flat793 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat793)
        write(pp, flat793)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1370 = _dollar_dollar.attrs
        else
            _t1370 = nothing
        end
        fields787 = (_dollar_dollar.name, _dollar_dollar.body, _t1370,)
        unwrapped_fields788 = fields787
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field789 = unwrapped_fields788[1]
        pretty_relation_id(pp, field789)
        newline(pp)
        field790 = unwrapped_fields788[2]
        pretty_abstraction(pp, field790)
        field791 = unwrapped_fields788[3]
        if !isnothing(field791)
            newline(pp)
            opt_val792 = field791
            pretty_attrs(pp, opt_val792)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat798 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat798)
        write(pp, flat798)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1372 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1371 = _t1372
        else
            _t1371 = nothing
        end
        deconstruct_result796 = _t1371
        if !isnothing(deconstruct_result796)
            unwrapped797 = deconstruct_result796
            write(pp, ":")
            write(pp, unwrapped797)
        else
            _dollar_dollar = msg
            _t1373 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result794 = _t1373
            if !isnothing(deconstruct_result794)
                unwrapped795 = deconstruct_result794
                write(pp, format_uint128(pp, unwrapped795))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat803 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat803)
        write(pp, flat803)
        return nothing
    else
        _dollar_dollar = msg
        _t1374 = deconstruct_bindings(pp, _dollar_dollar)
        fields799 = (_t1374, _dollar_dollar.value,)
        unwrapped_fields800 = fields799
        write(pp, "(")
        indent!(pp)
        field801 = unwrapped_fields800[1]
        pretty_bindings(pp, field801)
        newline(pp)
        field802 = unwrapped_fields800[2]
        pretty_formula(pp, field802)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat811 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat811)
        write(pp, flat811)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1375 = _dollar_dollar[2]
        else
            _t1375 = nothing
        end
        fields804 = (_dollar_dollar[1], _t1375,)
        unwrapped_fields805 = fields804
        write(pp, "[")
        indent!(pp)
        field806 = unwrapped_fields805[1]
        for (i1376, elem807) in enumerate(field806)
            i808 = i1376 - 1
            if (i808 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem807)
        end
        field809 = unwrapped_fields805[2]
        if !isnothing(field809)
            newline(pp)
            opt_val810 = field809
            pretty_value_bindings(pp, opt_val810)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat816 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat816)
        write(pp, flat816)
        return nothing
    else
        _dollar_dollar = msg
        fields812 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields813 = fields812
        field814 = unwrapped_fields813[1]
        write(pp, field814)
        write(pp, "::")
        field815 = unwrapped_fields813[2]
        pretty_type(pp, field815)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat845 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat845)
        write(pp, flat845)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1377 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1377 = nothing
        end
        deconstruct_result843 = _t1377
        if !isnothing(deconstruct_result843)
            unwrapped844 = deconstruct_result843
            pretty_unspecified_type(pp, unwrapped844)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1378 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1378 = nothing
            end
            deconstruct_result841 = _t1378
            if !isnothing(deconstruct_result841)
                unwrapped842 = deconstruct_result841
                pretty_string_type(pp, unwrapped842)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1379 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1379 = nothing
                end
                deconstruct_result839 = _t1379
                if !isnothing(deconstruct_result839)
                    unwrapped840 = deconstruct_result839
                    pretty_int_type(pp, unwrapped840)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1380 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1380 = nothing
                    end
                    deconstruct_result837 = _t1380
                    if !isnothing(deconstruct_result837)
                        unwrapped838 = deconstruct_result837
                        pretty_float_type(pp, unwrapped838)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1381 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1381 = nothing
                        end
                        deconstruct_result835 = _t1381
                        if !isnothing(deconstruct_result835)
                            unwrapped836 = deconstruct_result835
                            pretty_uint128_type(pp, unwrapped836)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1382 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1382 = nothing
                            end
                            deconstruct_result833 = _t1382
                            if !isnothing(deconstruct_result833)
                                unwrapped834 = deconstruct_result833
                                pretty_int128_type(pp, unwrapped834)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1383 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1383 = nothing
                                end
                                deconstruct_result831 = _t1383
                                if !isnothing(deconstruct_result831)
                                    unwrapped832 = deconstruct_result831
                                    pretty_date_type(pp, unwrapped832)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1384 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1384 = nothing
                                    end
                                    deconstruct_result829 = _t1384
                                    if !isnothing(deconstruct_result829)
                                        unwrapped830 = deconstruct_result829
                                        pretty_datetime_type(pp, unwrapped830)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1385 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1385 = nothing
                                        end
                                        deconstruct_result827 = _t1385
                                        if !isnothing(deconstruct_result827)
                                            unwrapped828 = deconstruct_result827
                                            pretty_missing_type(pp, unwrapped828)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1386 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1386 = nothing
                                            end
                                            deconstruct_result825 = _t1386
                                            if !isnothing(deconstruct_result825)
                                                unwrapped826 = deconstruct_result825
                                                pretty_decimal_type(pp, unwrapped826)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1387 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1387 = nothing
                                                end
                                                deconstruct_result823 = _t1387
                                                if !isnothing(deconstruct_result823)
                                                    unwrapped824 = deconstruct_result823
                                                    pretty_boolean_type(pp, unwrapped824)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1388 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1388 = nothing
                                                    end
                                                    deconstruct_result821 = _t1388
                                                    if !isnothing(deconstruct_result821)
                                                        unwrapped822 = deconstruct_result821
                                                        pretty_int32_type(pp, unwrapped822)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1389 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1389 = nothing
                                                        end
                                                        deconstruct_result819 = _t1389
                                                        if !isnothing(deconstruct_result819)
                                                            unwrapped820 = deconstruct_result819
                                                            pretty_float32_type(pp, unwrapped820)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1390 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1390 = nothing
                                                            end
                                                            deconstruct_result817 = _t1390
                                                            if !isnothing(deconstruct_result817)
                                                                unwrapped818 = deconstruct_result817
                                                                pretty_uint32_type(pp, unwrapped818)
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
    fields846 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields847 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields848 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields849 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields850 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields851 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields852 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields853 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields854 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat859 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat859)
        write(pp, flat859)
        return nothing
    else
        _dollar_dollar = msg
        fields855 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields856 = fields855
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field857 = unwrapped_fields856[1]
        write(pp, format_int(pp, field857))
        newline(pp)
        field858 = unwrapped_fields856[2]
        write(pp, format_int(pp, field858))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields860 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields861 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields862 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields863 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat867 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat867)
        write(pp, flat867)
        return nothing
    else
        fields864 = msg
        write(pp, "|")
        if !isempty(fields864)
            write(pp, " ")
            for (i1391, elem865) in enumerate(fields864)
                i866 = i1391 - 1
                if (i866 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem865)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat894 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat894)
        write(pp, flat894)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1392 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1392 = nothing
        end
        deconstruct_result892 = _t1392
        if !isnothing(deconstruct_result892)
            unwrapped893 = deconstruct_result892
            pretty_true(pp, unwrapped893)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1393 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1393 = nothing
            end
            deconstruct_result890 = _t1393
            if !isnothing(deconstruct_result890)
                unwrapped891 = deconstruct_result890
                pretty_false(pp, unwrapped891)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1394 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1394 = nothing
                end
                deconstruct_result888 = _t1394
                if !isnothing(deconstruct_result888)
                    unwrapped889 = deconstruct_result888
                    pretty_exists(pp, unwrapped889)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1395 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1395 = nothing
                    end
                    deconstruct_result886 = _t1395
                    if !isnothing(deconstruct_result886)
                        unwrapped887 = deconstruct_result886
                        pretty_reduce(pp, unwrapped887)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1396 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1396 = nothing
                        end
                        deconstruct_result884 = _t1396
                        if !isnothing(deconstruct_result884)
                            unwrapped885 = deconstruct_result884
                            pretty_conjunction(pp, unwrapped885)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1397 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1397 = nothing
                            end
                            deconstruct_result882 = _t1397
                            if !isnothing(deconstruct_result882)
                                unwrapped883 = deconstruct_result882
                                pretty_disjunction(pp, unwrapped883)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1398 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1398 = nothing
                                end
                                deconstruct_result880 = _t1398
                                if !isnothing(deconstruct_result880)
                                    unwrapped881 = deconstruct_result880
                                    pretty_not(pp, unwrapped881)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1399 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1399 = nothing
                                    end
                                    deconstruct_result878 = _t1399
                                    if !isnothing(deconstruct_result878)
                                        unwrapped879 = deconstruct_result878
                                        pretty_ffi(pp, unwrapped879)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1400 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1400 = nothing
                                        end
                                        deconstruct_result876 = _t1400
                                        if !isnothing(deconstruct_result876)
                                            unwrapped877 = deconstruct_result876
                                            pretty_atom(pp, unwrapped877)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1401 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1401 = nothing
                                            end
                                            deconstruct_result874 = _t1401
                                            if !isnothing(deconstruct_result874)
                                                unwrapped875 = deconstruct_result874
                                                pretty_pragma(pp, unwrapped875)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1402 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1402 = nothing
                                                end
                                                deconstruct_result872 = _t1402
                                                if !isnothing(deconstruct_result872)
                                                    unwrapped873 = deconstruct_result872
                                                    pretty_primitive(pp, unwrapped873)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1403 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1403 = nothing
                                                    end
                                                    deconstruct_result870 = _t1403
                                                    if !isnothing(deconstruct_result870)
                                                        unwrapped871 = deconstruct_result870
                                                        pretty_rel_atom(pp, unwrapped871)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1404 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1404 = nothing
                                                        end
                                                        deconstruct_result868 = _t1404
                                                        if !isnothing(deconstruct_result868)
                                                            unwrapped869 = deconstruct_result868
                                                            pretty_cast(pp, unwrapped869)
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
    fields895 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields896 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat901 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat901)
        write(pp, flat901)
        return nothing
    else
        _dollar_dollar = msg
        _t1405 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields897 = (_t1405, _dollar_dollar.body.value,)
        unwrapped_fields898 = fields897
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field899 = unwrapped_fields898[1]
        pretty_bindings(pp, field899)
        newline(pp)
        field900 = unwrapped_fields898[2]
        pretty_formula(pp, field900)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat907 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat907)
        write(pp, flat907)
        return nothing
    else
        _dollar_dollar = msg
        fields902 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields903 = fields902
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field904 = unwrapped_fields903[1]
        pretty_abstraction(pp, field904)
        newline(pp)
        field905 = unwrapped_fields903[2]
        pretty_abstraction(pp, field905)
        newline(pp)
        field906 = unwrapped_fields903[3]
        pretty_terms(pp, field906)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat911 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat911)
        write(pp, flat911)
        return nothing
    else
        fields908 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields908)
            newline(pp)
            for (i1406, elem909) in enumerate(fields908)
                i910 = i1406 - 1
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

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat916 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat916)
        write(pp, flat916)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1407 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1407 = nothing
        end
        deconstruct_result914 = _t1407
        if !isnothing(deconstruct_result914)
            unwrapped915 = deconstruct_result914
            pretty_var(pp, unwrapped915)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1408 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1408 = nothing
            end
            deconstruct_result912 = _t1408
            if !isnothing(deconstruct_result912)
                unwrapped913 = deconstruct_result912
                pretty_constant(pp, unwrapped913)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat919 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat919)
        write(pp, flat919)
        return nothing
    else
        _dollar_dollar = msg
        fields917 = _dollar_dollar.name
        unwrapped_fields918 = fields917
        write(pp, unwrapped_fields918)
    end
    return nothing
end

function pretty_constant(pp::PrettyPrinter, msg::Proto.Value)
    flat921 = try_flat(pp, msg, pretty_constant)
    if !isnothing(flat921)
        write(pp, flat921)
        return nothing
    else
        fields920 = msg
        pretty_value(pp, fields920)
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat926 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat926)
        write(pp, flat926)
        return nothing
    else
        _dollar_dollar = msg
        fields922 = _dollar_dollar.args
        unwrapped_fields923 = fields922
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields923)
            newline(pp)
            for (i1409, elem924) in enumerate(unwrapped_fields923)
                i925 = i1409 - 1
                if (i925 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem924)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat931 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat931)
        write(pp, flat931)
        return nothing
    else
        _dollar_dollar = msg
        fields927 = _dollar_dollar.args
        unwrapped_fields928 = fields927
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields928)
            newline(pp)
            for (i1410, elem929) in enumerate(unwrapped_fields928)
                i930 = i1410 - 1
                if (i930 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem929)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat934 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat934)
        write(pp, flat934)
        return nothing
    else
        _dollar_dollar = msg
        fields932 = _dollar_dollar.arg
        unwrapped_fields933 = fields932
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields933)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat940 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat940)
        write(pp, flat940)
        return nothing
    else
        _dollar_dollar = msg
        fields935 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields936 = fields935
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field937 = unwrapped_fields936[1]
        pretty_name(pp, field937)
        newline(pp)
        field938 = unwrapped_fields936[2]
        pretty_ffi_args(pp, field938)
        newline(pp)
        field939 = unwrapped_fields936[3]
        pretty_terms(pp, field939)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat942 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat942)
        write(pp, flat942)
        return nothing
    else
        fields941 = msg
        write(pp, ":")
        write(pp, fields941)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat946 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        fields943 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields943)
            newline(pp)
            for (i1411, elem944) in enumerate(fields943)
                i945 = i1411 - 1
                if (i945 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem944)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat953 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat953)
        write(pp, flat953)
        return nothing
    else
        _dollar_dollar = msg
        fields947 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields948 = fields947
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field949 = unwrapped_fields948[1]
        pretty_relation_id(pp, field949)
        field950 = unwrapped_fields948[2]
        if !isempty(field950)
            newline(pp)
            for (i1412, elem951) in enumerate(field950)
                i952 = i1412 - 1
                if (i952 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem951)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat960 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat960)
        write(pp, flat960)
        return nothing
    else
        _dollar_dollar = msg
        fields954 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields955 = fields954
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field956 = unwrapped_fields955[1]
        pretty_name(pp, field956)
        field957 = unwrapped_fields955[2]
        if !isempty(field957)
            newline(pp)
            for (i1413, elem958) in enumerate(field957)
                i959 = i1413 - 1
                if (i959 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem958)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat976 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat976)
        write(pp, flat976)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1414 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1414 = nothing
        end
        guard_result975 = _t1414
        if !isnothing(guard_result975)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1415 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1415 = nothing
            end
            guard_result974 = _t1415
            if !isnothing(guard_result974)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1416 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1416 = nothing
                end
                guard_result973 = _t1416
                if !isnothing(guard_result973)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1417 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1417 = nothing
                    end
                    guard_result972 = _t1417
                    if !isnothing(guard_result972)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1418 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1418 = nothing
                        end
                        guard_result971 = _t1418
                        if !isnothing(guard_result971)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1419 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1419 = nothing
                            end
                            guard_result970 = _t1419
                            if !isnothing(guard_result970)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1420 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1420 = nothing
                                end
                                guard_result969 = _t1420
                                if !isnothing(guard_result969)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1421 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1421 = nothing
                                    end
                                    guard_result968 = _t1421
                                    if !isnothing(guard_result968)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1422 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1422 = nothing
                                        end
                                        guard_result967 = _t1422
                                        if !isnothing(guard_result967)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields961 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields962 = fields961
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field963 = unwrapped_fields962[1]
                                            pretty_name(pp, field963)
                                            field964 = unwrapped_fields962[2]
                                            if !isempty(field964)
                                                newline(pp)
                                                for (i1423, elem965) in enumerate(field964)
                                                    i966 = i1423 - 1
                                                    if (i966 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem965)
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
    flat981 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat981)
        write(pp, flat981)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1424 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1424 = nothing
        end
        fields977 = _t1424
        unwrapped_fields978 = fields977
        write(pp, "(=")
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

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat986 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat986)
        write(pp, flat986)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1425 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1425 = nothing
        end
        fields982 = _t1425
        unwrapped_fields983 = fields982
        write(pp, "(<")
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

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat991 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat991)
        write(pp, flat991)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1426 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1426 = nothing
        end
        fields987 = _t1426
        unwrapped_fields988 = fields987
        write(pp, "(<=")
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

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat996 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat996)
        write(pp, flat996)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1427 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1427 = nothing
        end
        fields992 = _t1427
        unwrapped_fields993 = fields992
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field994 = unwrapped_fields993[1]
        pretty_term(pp, field994)
        newline(pp)
        field995 = unwrapped_fields993[2]
        pretty_term(pp, field995)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1001 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1001)
        write(pp, flat1001)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1428 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1428 = nothing
        end
        fields997 = _t1428
        unwrapped_fields998 = fields997
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field999 = unwrapped_fields998[1]
        pretty_term(pp, field999)
        newline(pp)
        field1000 = unwrapped_fields998[2]
        pretty_term(pp, field1000)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1007 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1007)
        write(pp, flat1007)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1429 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1429 = nothing
        end
        fields1002 = _t1429
        unwrapped_fields1003 = fields1002
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1004 = unwrapped_fields1003[1]
        pretty_term(pp, field1004)
        newline(pp)
        field1005 = unwrapped_fields1003[2]
        pretty_term(pp, field1005)
        newline(pp)
        field1006 = unwrapped_fields1003[3]
        pretty_term(pp, field1006)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1013 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1013)
        write(pp, flat1013)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1430 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1430 = nothing
        end
        fields1008 = _t1430
        unwrapped_fields1009 = fields1008
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1010 = unwrapped_fields1009[1]
        pretty_term(pp, field1010)
        newline(pp)
        field1011 = unwrapped_fields1009[2]
        pretty_term(pp, field1011)
        newline(pp)
        field1012 = unwrapped_fields1009[3]
        pretty_term(pp, field1012)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1019 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1019)
        write(pp, flat1019)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1431 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1431 = nothing
        end
        fields1014 = _t1431
        unwrapped_fields1015 = fields1014
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1016 = unwrapped_fields1015[1]
        pretty_term(pp, field1016)
        newline(pp)
        field1017 = unwrapped_fields1015[2]
        pretty_term(pp, field1017)
        newline(pp)
        field1018 = unwrapped_fields1015[3]
        pretty_term(pp, field1018)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1025 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1025)
        write(pp, flat1025)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1432 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1432 = nothing
        end
        fields1020 = _t1432
        unwrapped_fields1021 = fields1020
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1022 = unwrapped_fields1021[1]
        pretty_term(pp, field1022)
        newline(pp)
        field1023 = unwrapped_fields1021[2]
        pretty_term(pp, field1023)
        newline(pp)
        field1024 = unwrapped_fields1021[3]
        pretty_term(pp, field1024)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1030 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1030)
        write(pp, flat1030)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1433 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1433 = nothing
        end
        deconstruct_result1028 = _t1433
        if !isnothing(deconstruct_result1028)
            unwrapped1029 = deconstruct_result1028
            pretty_specialized_value(pp, unwrapped1029)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1434 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1434 = nothing
            end
            deconstruct_result1026 = _t1434
            if !isnothing(deconstruct_result1026)
                unwrapped1027 = deconstruct_result1026
                pretty_term(pp, unwrapped1027)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1032 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1032)
        write(pp, flat1032)
        return nothing
    else
        fields1031 = msg
        write(pp, "#")
        pretty_value(pp, fields1031)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1039 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1039)
        write(pp, flat1039)
        return nothing
    else
        _dollar_dollar = msg
        fields1033 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1034 = fields1033
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1035 = unwrapped_fields1034[1]
        pretty_name(pp, field1035)
        field1036 = unwrapped_fields1034[2]
        if !isempty(field1036)
            newline(pp)
            for (i1435, elem1037) in enumerate(field1036)
                i1038 = i1435 - 1
                if (i1038 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1037)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1044 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1044)
        write(pp, flat1044)
        return nothing
    else
        _dollar_dollar = msg
        fields1040 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1041 = fields1040
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1042 = unwrapped_fields1041[1]
        pretty_term(pp, field1042)
        newline(pp)
        field1043 = unwrapped_fields1041[2]
        pretty_term(pp, field1043)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1048 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1048)
        write(pp, flat1048)
        return nothing
    else
        fields1045 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1045)
            newline(pp)
            for (i1436, elem1046) in enumerate(fields1045)
                i1047 = i1436 - 1
                if (i1047 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1046)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1055 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1055)
        write(pp, flat1055)
        return nothing
    else
        _dollar_dollar = msg
        fields1049 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1050 = fields1049
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1051 = unwrapped_fields1050[1]
        pretty_name(pp, field1051)
        field1052 = unwrapped_fields1050[2]
        if !isempty(field1052)
            newline(pp)
            for (i1437, elem1053) in enumerate(field1052)
                i1054 = i1437 - 1
                if (i1054 > 0)
                    newline(pp)
                end
                pretty_value(pp, elem1053)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1062 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1062)
        write(pp, flat1062)
        return nothing
    else
        _dollar_dollar = msg
        fields1056 = (_dollar_dollar.var"#global", _dollar_dollar.body,)
        unwrapped_fields1057 = fields1056
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1058 = unwrapped_fields1057[1]
        if !isempty(field1058)
            newline(pp)
            for (i1438, elem1059) in enumerate(field1058)
                i1060 = i1438 - 1
                if (i1060 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1059)
            end
        end
        newline(pp)
        field1061 = unwrapped_fields1057[2]
        pretty_script(pp, field1061)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1067 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1067)
        write(pp, flat1067)
        return nothing
    else
        _dollar_dollar = msg
        fields1063 = _dollar_dollar.constructs
        unwrapped_fields1064 = fields1063
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1064)
            newline(pp)
            for (i1439, elem1065) in enumerate(unwrapped_fields1064)
                i1066 = i1439 - 1
                if (i1066 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1065)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1072 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1072)
        write(pp, flat1072)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1440 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1440 = nothing
        end
        deconstruct_result1070 = _t1440
        if !isnothing(deconstruct_result1070)
            unwrapped1071 = deconstruct_result1070
            pretty_loop(pp, unwrapped1071)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1441 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1441 = nothing
            end
            deconstruct_result1068 = _t1441
            if !isnothing(deconstruct_result1068)
                unwrapped1069 = deconstruct_result1068
                pretty_instruction(pp, unwrapped1069)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1077 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1077)
        write(pp, flat1077)
        return nothing
    else
        _dollar_dollar = msg
        fields1073 = (_dollar_dollar.init, _dollar_dollar.body,)
        unwrapped_fields1074 = fields1073
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1075 = unwrapped_fields1074[1]
        pretty_init(pp, field1075)
        newline(pp)
        field1076 = unwrapped_fields1074[2]
        pretty_script(pp, field1076)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1081 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1081)
        write(pp, flat1081)
        return nothing
    else
        fields1078 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1078)
            newline(pp)
            for (i1442, elem1079) in enumerate(fields1078)
                i1080 = i1442 - 1
                if (i1080 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1079)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1092 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1092)
        write(pp, flat1092)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1443 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1443 = nothing
        end
        deconstruct_result1090 = _t1443
        if !isnothing(deconstruct_result1090)
            unwrapped1091 = deconstruct_result1090
            pretty_assign(pp, unwrapped1091)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1444 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1444 = nothing
            end
            deconstruct_result1088 = _t1444
            if !isnothing(deconstruct_result1088)
                unwrapped1089 = deconstruct_result1088
                pretty_upsert(pp, unwrapped1089)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1445 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1445 = nothing
                end
                deconstruct_result1086 = _t1445
                if !isnothing(deconstruct_result1086)
                    unwrapped1087 = deconstruct_result1086
                    pretty_break(pp, unwrapped1087)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1446 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1446 = nothing
                    end
                    deconstruct_result1084 = _t1446
                    if !isnothing(deconstruct_result1084)
                        unwrapped1085 = deconstruct_result1084
                        pretty_monoid_def(pp, unwrapped1085)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1447 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1447 = nothing
                        end
                        deconstruct_result1082 = _t1447
                        if !isnothing(deconstruct_result1082)
                            unwrapped1083 = deconstruct_result1082
                            pretty_monus_def(pp, unwrapped1083)
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
    flat1099 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1099)
        write(pp, flat1099)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1448 = _dollar_dollar.attrs
        else
            _t1448 = nothing
        end
        fields1093 = (_dollar_dollar.name, _dollar_dollar.body, _t1448,)
        unwrapped_fields1094 = fields1093
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1095 = unwrapped_fields1094[1]
        pretty_relation_id(pp, field1095)
        newline(pp)
        field1096 = unwrapped_fields1094[2]
        pretty_abstraction(pp, field1096)
        field1097 = unwrapped_fields1094[3]
        if !isnothing(field1097)
            newline(pp)
            opt_val1098 = field1097
            pretty_attrs(pp, opt_val1098)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1106 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1106)
        write(pp, flat1106)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1449 = _dollar_dollar.attrs
        else
            _t1449 = nothing
        end
        fields1100 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1449,)
        unwrapped_fields1101 = fields1100
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1102 = unwrapped_fields1101[1]
        pretty_relation_id(pp, field1102)
        newline(pp)
        field1103 = unwrapped_fields1101[2]
        pretty_abstraction_with_arity(pp, field1103)
        field1104 = unwrapped_fields1101[3]
        if !isnothing(field1104)
            newline(pp)
            opt_val1105 = field1104
            pretty_attrs(pp, opt_val1105)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1111 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1111)
        write(pp, flat1111)
        return nothing
    else
        _dollar_dollar = msg
        _t1450 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1107 = (_t1450, _dollar_dollar[1].value,)
        unwrapped_fields1108 = fields1107
        write(pp, "(")
        indent!(pp)
        field1109 = unwrapped_fields1108[1]
        pretty_bindings(pp, field1109)
        newline(pp)
        field1110 = unwrapped_fields1108[2]
        pretty_formula(pp, field1110)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1118 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1118)
        write(pp, flat1118)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1451 = _dollar_dollar.attrs
        else
            _t1451 = nothing
        end
        fields1112 = (_dollar_dollar.name, _dollar_dollar.body, _t1451,)
        unwrapped_fields1113 = fields1112
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1114 = unwrapped_fields1113[1]
        pretty_relation_id(pp, field1114)
        newline(pp)
        field1115 = unwrapped_fields1113[2]
        pretty_abstraction(pp, field1115)
        field1116 = unwrapped_fields1113[3]
        if !isnothing(field1116)
            newline(pp)
            opt_val1117 = field1116
            pretty_attrs(pp, opt_val1117)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1126 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1126)
        write(pp, flat1126)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1452 = _dollar_dollar.attrs
        else
            _t1452 = nothing
        end
        fields1119 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1452,)
        unwrapped_fields1120 = fields1119
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1121 = unwrapped_fields1120[1]
        pretty_monoid(pp, field1121)
        newline(pp)
        field1122 = unwrapped_fields1120[2]
        pretty_relation_id(pp, field1122)
        newline(pp)
        field1123 = unwrapped_fields1120[3]
        pretty_abstraction_with_arity(pp, field1123)
        field1124 = unwrapped_fields1120[4]
        if !isnothing(field1124)
            newline(pp)
            opt_val1125 = field1124
            pretty_attrs(pp, opt_val1125)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1135 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1135)
        write(pp, flat1135)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1453 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1453 = nothing
        end
        deconstruct_result1133 = _t1453
        if !isnothing(deconstruct_result1133)
            unwrapped1134 = deconstruct_result1133
            pretty_or_monoid(pp, unwrapped1134)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1454 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1454 = nothing
            end
            deconstruct_result1131 = _t1454
            if !isnothing(deconstruct_result1131)
                unwrapped1132 = deconstruct_result1131
                pretty_min_monoid(pp, unwrapped1132)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1455 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1455 = nothing
                end
                deconstruct_result1129 = _t1455
                if !isnothing(deconstruct_result1129)
                    unwrapped1130 = deconstruct_result1129
                    pretty_max_monoid(pp, unwrapped1130)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1456 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1456 = nothing
                    end
                    deconstruct_result1127 = _t1456
                    if !isnothing(deconstruct_result1127)
                        unwrapped1128 = deconstruct_result1127
                        pretty_sum_monoid(pp, unwrapped1128)
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
    fields1136 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1139 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1139)
        write(pp, flat1139)
        return nothing
    else
        _dollar_dollar = msg
        fields1137 = _dollar_dollar.var"#type"
        unwrapped_fields1138 = fields1137
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1138)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1142 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1142)
        write(pp, flat1142)
        return nothing
    else
        _dollar_dollar = msg
        fields1140 = _dollar_dollar.var"#type"
        unwrapped_fields1141 = fields1140
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1141)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1145 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1145)
        write(pp, flat1145)
        return nothing
    else
        _dollar_dollar = msg
        fields1143 = _dollar_dollar.var"#type"
        unwrapped_fields1144 = fields1143
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1144)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1153 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1153)
        write(pp, flat1153)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1457 = _dollar_dollar.attrs
        else
            _t1457 = nothing
        end
        fields1146 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1457,)
        unwrapped_fields1147 = fields1146
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1148 = unwrapped_fields1147[1]
        pretty_monoid(pp, field1148)
        newline(pp)
        field1149 = unwrapped_fields1147[2]
        pretty_relation_id(pp, field1149)
        newline(pp)
        field1150 = unwrapped_fields1147[3]
        pretty_abstraction_with_arity(pp, field1150)
        field1151 = unwrapped_fields1147[4]
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

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1160 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1160)
        write(pp, flat1160)
        return nothing
    else
        _dollar_dollar = msg
        fields1154 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1155 = fields1154
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1156 = unwrapped_fields1155[1]
        pretty_relation_id(pp, field1156)
        newline(pp)
        field1157 = unwrapped_fields1155[2]
        pretty_abstraction(pp, field1157)
        newline(pp)
        field1158 = unwrapped_fields1155[3]
        pretty_functional_dependency_keys(pp, field1158)
        newline(pp)
        field1159 = unwrapped_fields1155[4]
        pretty_functional_dependency_values(pp, field1159)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1164 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1164)
        write(pp, flat1164)
        return nothing
    else
        fields1161 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1161)
            newline(pp)
            for (i1458, elem1162) in enumerate(fields1161)
                i1163 = i1458 - 1
                if (i1163 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1162)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1168 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1168)
        write(pp, flat1168)
        return nothing
    else
        fields1165 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1165)
            newline(pp)
            for (i1459, elem1166) in enumerate(fields1165)
                i1167 = i1459 - 1
                if (i1167 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1166)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1175 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1175)
        write(pp, flat1175)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1460 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1460 = nothing
        end
        deconstruct_result1173 = _t1460
        if !isnothing(deconstruct_result1173)
            unwrapped1174 = deconstruct_result1173
            pretty_edb(pp, unwrapped1174)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1461 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1461 = nothing
            end
            deconstruct_result1171 = _t1461
            if !isnothing(deconstruct_result1171)
                unwrapped1172 = deconstruct_result1171
                pretty_betree_relation(pp, unwrapped1172)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1462 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1462 = nothing
                end
                deconstruct_result1169 = _t1462
                if !isnothing(deconstruct_result1169)
                    unwrapped1170 = deconstruct_result1169
                    pretty_csv_data(pp, unwrapped1170)
                else
                    throw(ParseError("No matching rule for data"))
                end
            end
        end
    end
    return nothing
end

function pretty_edb(pp::PrettyPrinter, msg::Proto.EDB)
    flat1181 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1181)
        write(pp, flat1181)
        return nothing
    else
        _dollar_dollar = msg
        fields1176 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1177 = fields1176
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1178 = unwrapped_fields1177[1]
        pretty_relation_id(pp, field1178)
        newline(pp)
        field1179 = unwrapped_fields1177[2]
        pretty_edb_path(pp, field1179)
        newline(pp)
        field1180 = unwrapped_fields1177[3]
        pretty_edb_types(pp, field1180)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1185 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1185)
        write(pp, flat1185)
        return nothing
    else
        fields1182 = msg
        write(pp, "[")
        indent!(pp)
        for (i1463, elem1183) in enumerate(fields1182)
            i1184 = i1463 - 1
            if (i1184 > 0)
                newline(pp)
            end
            write(pp, format_string(pp, elem1183))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1189 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1189)
        write(pp, flat1189)
        return nothing
    else
        fields1186 = msg
        write(pp, "[")
        indent!(pp)
        for (i1464, elem1187) in enumerate(fields1186)
            i1188 = i1464 - 1
            if (i1188 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1187)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1194 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1194)
        write(pp, flat1194)
        return nothing
    else
        _dollar_dollar = msg
        fields1190 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1191 = fields1190
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1192 = unwrapped_fields1191[1]
        pretty_relation_id(pp, field1192)
        newline(pp)
        field1193 = unwrapped_fields1191[2]
        pretty_betree_info(pp, field1193)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1200 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1200)
        write(pp, flat1200)
        return nothing
    else
        _dollar_dollar = msg
        _t1465 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1195 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1465,)
        unwrapped_fields1196 = fields1195
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1197 = unwrapped_fields1196[1]
        pretty_betree_info_key_types(pp, field1197)
        newline(pp)
        field1198 = unwrapped_fields1196[2]
        pretty_betree_info_value_types(pp, field1198)
        newline(pp)
        field1199 = unwrapped_fields1196[3]
        pretty_config_dict(pp, field1199)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1204 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1204)
        write(pp, flat1204)
        return nothing
    else
        fields1201 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1201)
            newline(pp)
            for (i1466, elem1202) in enumerate(fields1201)
                i1203 = i1466 - 1
                if (i1203 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1202)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1208 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1208)
        write(pp, flat1208)
        return nothing
    else
        fields1205 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1205)
            newline(pp)
            for (i1467, elem1206) in enumerate(fields1205)
                i1207 = i1467 - 1
                if (i1207 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1206)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1215 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        _dollar_dollar = msg
        fields1209 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1210 = fields1209
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1211 = unwrapped_fields1210[1]
        pretty_csvlocator(pp, field1211)
        newline(pp)
        field1212 = unwrapped_fields1210[2]
        pretty_csv_config(pp, field1212)
        newline(pp)
        field1213 = unwrapped_fields1210[3]
        pretty_gnf_columns(pp, field1213)
        newline(pp)
        field1214 = unwrapped_fields1210[4]
        pretty_csv_asof(pp, field1214)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1222 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1222)
        write(pp, flat1222)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1468 = _dollar_dollar.paths
        else
            _t1468 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1469 = String(copy(_dollar_dollar.inline_data))
        else
            _t1469 = nothing
        end
        fields1216 = (_t1468, _t1469,)
        unwrapped_fields1217 = fields1216
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1218 = unwrapped_fields1217[1]
        if !isnothing(field1218)
            newline(pp)
            opt_val1219 = field1218
            pretty_csv_locator_paths(pp, opt_val1219)
        end
        field1220 = unwrapped_fields1217[2]
        if !isnothing(field1220)
            newline(pp)
            opt_val1221 = field1220
            pretty_csv_locator_inline_data(pp, opt_val1221)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1226 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1226)
        write(pp, flat1226)
        return nothing
    else
        fields1223 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1223)
            newline(pp)
            for (i1470, elem1224) in enumerate(fields1223)
                i1225 = i1470 - 1
                if (i1225 > 0)
                    newline(pp)
                end
                write(pp, format_string(pp, elem1224))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1228 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1228)
        write(pp, flat1228)
        return nothing
    else
        fields1227 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1227))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1231 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1231)
        write(pp, flat1231)
        return nothing
    else
        _dollar_dollar = msg
        _t1471 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1229 = _t1471
        unwrapped_fields1230 = fields1229
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1230)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1235 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1235)
        write(pp, flat1235)
        return nothing
    else
        fields1232 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1232)
            newline(pp)
            for (i1472, elem1233) in enumerate(fields1232)
                i1234 = i1472 - 1
                if (i1234 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1233)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1244 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1244)
        write(pp, flat1244)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1473 = _dollar_dollar.target_id
        else
            _t1473 = nothing
        end
        fields1236 = (_dollar_dollar.column_path, _t1473, _dollar_dollar.types,)
        unwrapped_fields1237 = fields1236
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1238 = unwrapped_fields1237[1]
        pretty_gnf_column_path(pp, field1238)
        field1239 = unwrapped_fields1237[2]
        if !isnothing(field1239)
            newline(pp)
            opt_val1240 = field1239
            pretty_relation_id(pp, opt_val1240)
        end
        newline(pp)
        write(pp, "[")
        field1241 = unwrapped_fields1237[3]
        for (i1474, elem1242) in enumerate(field1241)
            i1243 = i1474 - 1
            if (i1243 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1242)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1251 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1251)
        write(pp, flat1251)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1475 = _dollar_dollar[1]
        else
            _t1475 = nothing
        end
        deconstruct_result1249 = _t1475
        if !isnothing(deconstruct_result1249)
            unwrapped1250 = deconstruct_result1249
            write(pp, format_string(pp, unwrapped1250))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1476 = _dollar_dollar
            else
                _t1476 = nothing
            end
            deconstruct_result1245 = _t1476
            if !isnothing(deconstruct_result1245)
                unwrapped1246 = deconstruct_result1245
                write(pp, "[")
                indent!(pp)
                for (i1477, elem1247) in enumerate(unwrapped1246)
                    i1248 = i1477 - 1
                    if (i1248 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(pp, elem1247))
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
    flat1253 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1253)
        write(pp, flat1253)
        return nothing
    else
        fields1252 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1252))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1256 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1256)
        write(pp, flat1256)
        return nothing
    else
        _dollar_dollar = msg
        fields1254 = _dollar_dollar.fragment_id
        unwrapped_fields1255 = fields1254
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1255)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1261 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1261)
        write(pp, flat1261)
        return nothing
    else
        _dollar_dollar = msg
        fields1257 = _dollar_dollar.relations
        unwrapped_fields1258 = fields1257
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1258)
            newline(pp)
            for (i1478, elem1259) in enumerate(unwrapped_fields1258)
                i1260 = i1478 - 1
                if (i1260 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1259)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1266 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1266)
        write(pp, flat1266)
        return nothing
    else
        _dollar_dollar = msg
        fields1262 = _dollar_dollar.mappings
        unwrapped_fields1263 = fields1262
        write(pp, "(snapshot")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1263)
            newline(pp)
            for (i1479, elem1264) in enumerate(unwrapped_fields1263)
                i1265 = i1479 - 1
                if (i1265 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1264)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1271 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1271)
        write(pp, flat1271)
        return nothing
    else
        _dollar_dollar = msg
        fields1267 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1268 = fields1267
        field1269 = unwrapped_fields1268[1]
        pretty_edb_path(pp, field1269)
        write(pp, " ")
        field1270 = unwrapped_fields1268[2]
        pretty_relation_id(pp, field1270)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1275 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1275)
        write(pp, flat1275)
        return nothing
    else
        fields1272 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1272)
            newline(pp)
            for (i1480, elem1273) in enumerate(fields1272)
                i1274 = i1480 - 1
                if (i1274 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1273)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1286 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1286)
        write(pp, flat1286)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1481 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1481 = nothing
        end
        deconstruct_result1284 = _t1481
        if !isnothing(deconstruct_result1284)
            unwrapped1285 = deconstruct_result1284
            pretty_demand(pp, unwrapped1285)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1482 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1482 = nothing
            end
            deconstruct_result1282 = _t1482
            if !isnothing(deconstruct_result1282)
                unwrapped1283 = deconstruct_result1282
                pretty_output(pp, unwrapped1283)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1483 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1483 = nothing
                end
                deconstruct_result1280 = _t1483
                if !isnothing(deconstruct_result1280)
                    unwrapped1281 = deconstruct_result1280
                    pretty_what_if(pp, unwrapped1281)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1484 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1484 = nothing
                    end
                    deconstruct_result1278 = _t1484
                    if !isnothing(deconstruct_result1278)
                        unwrapped1279 = deconstruct_result1278
                        pretty_abort(pp, unwrapped1279)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1485 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1485 = nothing
                        end
                        deconstruct_result1276 = _t1485
                        if !isnothing(deconstruct_result1276)
                            unwrapped1277 = deconstruct_result1276
                            pretty_export(pp, unwrapped1277)
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
    flat1289 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1289)
        write(pp, flat1289)
        return nothing
    else
        _dollar_dollar = msg
        fields1287 = _dollar_dollar.relation_id
        unwrapped_fields1288 = fields1287
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1288)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1294 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1294)
        write(pp, flat1294)
        return nothing
    else
        _dollar_dollar = msg
        fields1290 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1291 = fields1290
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1292 = unwrapped_fields1291[1]
        pretty_name(pp, field1292)
        newline(pp)
        field1293 = unwrapped_fields1291[2]
        pretty_relation_id(pp, field1293)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1299 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1299)
        write(pp, flat1299)
        return nothing
    else
        _dollar_dollar = msg
        fields1295 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1296 = fields1295
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1297 = unwrapped_fields1296[1]
        pretty_name(pp, field1297)
        newline(pp)
        field1298 = unwrapped_fields1296[2]
        pretty_epoch(pp, field1298)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1305 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1305)
        write(pp, flat1305)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1486 = _dollar_dollar.name
        else
            _t1486 = nothing
        end
        fields1300 = (_t1486, _dollar_dollar.relation_id,)
        unwrapped_fields1301 = fields1300
        write(pp, "(abort")
        indent_sexp!(pp)
        field1302 = unwrapped_fields1301[1]
        if !isnothing(field1302)
            newline(pp)
            opt_val1303 = field1302
            pretty_name(pp, opt_val1303)
        end
        newline(pp)
        field1304 = unwrapped_fields1301[2]
        pretty_relation_id(pp, field1304)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1308 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1308)
        write(pp, flat1308)
        return nothing
    else
        _dollar_dollar = msg
        fields1306 = _get_oneof_field(_dollar_dollar, :csv_config)
        unwrapped_fields1307 = fields1306
        write(pp, "(export")
        indent_sexp!(pp)
        newline(pp)
        pretty_export_csv_config(pp, unwrapped_fields1307)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)
    flat1319 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1319)
        write(pp, flat1319)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1487 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1487 = nothing
        end
        deconstruct_result1314 = _t1487
        if !isnothing(deconstruct_result1314)
            unwrapped1315 = deconstruct_result1314
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1316 = unwrapped1315[1]
            pretty_export_csv_path(pp, field1316)
            newline(pp)
            field1317 = unwrapped1315[2]
            pretty_export_csv_source(pp, field1317)
            newline(pp)
            field1318 = unwrapped1315[3]
            pretty_csv_config(pp, field1318)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1489 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1488 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1489,)
            else
                _t1488 = nothing
            end
            deconstruct_result1309 = _t1488
            if !isnothing(deconstruct_result1309)
                unwrapped1310 = deconstruct_result1309
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1311 = unwrapped1310[1]
                pretty_export_csv_path(pp, field1311)
                newline(pp)
                field1312 = unwrapped1310[2]
                pretty_export_csv_columns_list(pp, field1312)
                newline(pp)
                field1313 = unwrapped1310[3]
                pretty_config_dict(pp, field1313)
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
    flat1321 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1321)
        write(pp, flat1321)
        return nothing
    else
        fields1320 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(pp, fields1320))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1328 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1328)
        write(pp, flat1328)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1490 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1490 = nothing
        end
        deconstruct_result1324 = _t1490
        if !isnothing(deconstruct_result1324)
            unwrapped1325 = deconstruct_result1324
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1325)
                newline(pp)
                for (i1491, elem1326) in enumerate(unwrapped1325)
                    i1327 = i1491 - 1
                    if (i1327 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1326)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1492 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1492 = nothing
            end
            deconstruct_result1322 = _t1492
            if !isnothing(deconstruct_result1322)
                unwrapped1323 = deconstruct_result1322
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1323)
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
    flat1333 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1333)
        write(pp, flat1333)
        return nothing
    else
        _dollar_dollar = msg
        fields1329 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1330 = fields1329
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1331 = unwrapped_fields1330[1]
        write(pp, format_string(pp, field1331))
        newline(pp)
        field1332 = unwrapped_fields1330[2]
        pretty_relation_id(pp, field1332)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1337 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1337)
        write(pp, flat1337)
        return nothing
    else
        fields1334 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1334)
            newline(pp)
            for (i1493, elem1335) in enumerate(fields1334)
                i1336 = i1493 - 1
                if (i1336 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1335)
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
    for (i1532, _rid) in enumerate(msg.ids)
        _idx = i1532 - 1
        newline(pp)
        write(pp, "(")
        _t1533 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1533)
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
    for (i1534, _elem) in enumerate(msg.keys)
        _idx = i1534 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1535, _elem) in enumerate(msg.values)
        _idx = i1535 - 1
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
    for (i1536, _elem) in enumerate(msg.columns)
        _idx = i1536 - 1
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
