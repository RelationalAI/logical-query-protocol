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
    _computing::Set{Tuple{UInt,UInt}}
    _memo::Dict{Tuple{UInt,UInt},String}
    _memo_refs::Vector{Any}
    print_symbolic_relation_ids::Bool
    debug_info::Dict{Tuple{UInt64,UInt64},String}
    constant_formatter::ConstantFormatter
end

function PrettyPrinter(; max_width::Int=92, print_symbolic_relation_ids::Bool=true, constant_formatter::ConstantFormatter=DEFAULT_CONSTANT_FORMATTER)
    return PrettyPrinter(
        IOBuffer(), [0], 0, true, "\n", max_width,
        Set{Tuple{UInt,UInt}}(), Dict{Tuple{UInt,UInt},String}(), Any[],
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
    memo_key = (objectid(msg), objectid(pretty_fn))
    if !haskey(pp._memo, memo_key) && !(memo_key in pp._computing)
        push!(pp._computing, memo_key)
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
            pp._memo[memo_key] = String(copy(pp.io.data[1:pp.io.size]))
            push!(pp._memo_refs, msg)
        finally
            pp.io = saved_io
            pp.separator = saved_sep
            pp.indent_stack = saved_indent
            pp.column = saved_col
            pp.at_line_start = saved_at_line_start
            delete!(pp._computing, memo_key)
        end
    end
    if haskey(pp._memo, memo_key)
        flat = pp._memo[memo_key]
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
    _t1791 = Proto.Value(value=OneOf(:int32_value, v))
    return _t1791
end

function _make_value_int64(pp::PrettyPrinter, v::Int64)::Proto.Value
    _t1792 = Proto.Value(value=OneOf(:int_value, v))
    return _t1792
end

function _make_value_float64(pp::PrettyPrinter, v::Float64)::Proto.Value
    _t1793 = Proto.Value(value=OneOf(:float_value, v))
    return _t1793
end

function _make_value_string(pp::PrettyPrinter, v::String)::Proto.Value
    _t1794 = Proto.Value(value=OneOf(:string_value, v))
    return _t1794
end

function _make_value_boolean(pp::PrettyPrinter, v::Bool)::Proto.Value
    _t1795 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1795
end

function _make_value_uint128(pp::PrettyPrinter, v::Proto.UInt128Value)::Proto.Value
    _t1796 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1796
end

function deconstruct_configure(pp::PrettyPrinter, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t1797 = _make_value_string(pp, "auto")
        push!(result, ("ivm.maintenance_level", _t1797,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1798 = _make_value_string(pp, "all")
            push!(result, ("ivm.maintenance_level", _t1798,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1799 = _make_value_string(pp, "off")
                push!(result, ("ivm.maintenance_level", _t1799,))
            end
        end
    end
    _t1800 = _make_value_int64(pp, msg.semantics_version)
    push!(result, ("semantics_version", _t1800,))
    return sort(result)
end

function deconstruct_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1801 = _make_value_int32(pp, msg.header_row)
    push!(result, ("csv_header_row", _t1801,))
    _t1802 = _make_value_int64(pp, msg.skip)
    push!(result, ("csv_skip", _t1802,))
    if msg.new_line != ""
        _t1803 = _make_value_string(pp, msg.new_line)
        push!(result, ("csv_new_line", _t1803,))
    end
    _t1804 = _make_value_string(pp, msg.delimiter)
    push!(result, ("csv_delimiter", _t1804,))
    _t1805 = _make_value_string(pp, msg.quotechar)
    push!(result, ("csv_quotechar", _t1805,))
    _t1806 = _make_value_string(pp, msg.escapechar)
    push!(result, ("csv_escapechar", _t1806,))
    if msg.comment != ""
        _t1807 = _make_value_string(pp, msg.comment)
        push!(result, ("csv_comment", _t1807,))
    end
    for missing_string in msg.missing_strings
        _t1808 = _make_value_string(pp, missing_string)
        push!(result, ("csv_missing_strings", _t1808,))
    end
    _t1809 = _make_value_string(pp, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1809,))
    _t1810 = _make_value_string(pp, msg.encoding)
    push!(result, ("csv_encoding", _t1810,))
    _t1811 = _make_value_string(pp, msg.compression)
    push!(result, ("csv_compression", _t1811,))
    if msg.partition_size_mb != 0
        _t1812 = _make_value_int64(pp, msg.partition_size_mb)
        push!(result, ("csv_partition_size_mb", _t1812,))
    end
    return sort(result)
end

function deconstruct_betree_info_config(pp::PrettyPrinter, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1813 = _make_value_float64(pp, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1813,))
    _t1814 = _make_value_int64(pp, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1814,))
    _t1815 = _make_value_int64(pp, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1815,))
    _t1816 = _make_value_int64(pp, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1816,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1817 = _make_value_uint128(pp, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1817,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1818 = _make_value_string(pp, String(copy(_get_oneof_field(msg.relation_locator, :inline_data))))
            push!(result, ("betree_locator_inline_data", _t1818,))
        end
    end
    _t1819 = _make_value_int64(pp, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1819,))
    _t1820 = _make_value_int64(pp, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1820,))
    return sort(result)
end

function deconstruct_export_csv_config(pp::PrettyPrinter, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1821 = _make_value_int64(pp, msg.partition_size)
        push!(result, ("partition_size", _t1821,))
    end
    if !isnothing(msg.compression)
        _t1822 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1822,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1823 = _make_value_boolean(pp, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1823,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1824 = _make_value_string(pp, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1824,))
    end
    if !isnothing(msg.syntax_delim)
        _t1825 = _make_value_string(pp, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1825,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1826 = _make_value_string(pp, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1826,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1827 = _make_value_string(pp, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1827,))
    end
    return sort(result)
end

function mask_secret_value(pp::PrettyPrinter, pair::Tuple{String, String})::String
    return "***"
end

function deconstruct_iceberg_catalog_config_scope_optional(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)::Union{Nothing, String}
    if msg.scope != ""
        return msg.scope
    else
        _t1828 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_from_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.from_snapshot != ""
        return msg.from_snapshot
    else
        _t1829 = nothing
    end
    return nothing
end

function deconstruct_iceberg_data_to_snapshot_optional(pp::PrettyPrinter, msg::Proto.IcebergData)::Union{Nothing, String}
    if msg.to_snapshot != ""
        return msg.to_snapshot
    else
        _t1830 = nothing
    end
    return nothing
end

function deconstruct_export_iceberg_config_optional(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)::Union{Nothing, Vector{Tuple{String, Proto.Value}}}
    result = Tuple{String, Proto.Value}[]
    if msg.prefix != ""
        _t1831 = _make_value_string(pp, msg.prefix)
        push!(result, ("prefix", _t1831,))
    end
    if msg.target_file_size_bytes != 0
        _t1832 = _make_value_int64(pp, msg.target_file_size_bytes)
        push!(result, ("target_file_size_bytes", _t1832,))
    end
    if msg.compression != ""
        _t1833 = _make_value_string(pp, msg.compression)
        push!(result, ("compression", _t1833,))
    end
    if length(result) == 0
        return nothing
    else
        _t1834 = nothing
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
        _t1835 = nothing
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
    flat813 = try_flat(pp, msg, pretty_transaction)
    if !isnothing(flat813)
        write(pp, flat813)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("configure"))
            _t1608 = _dollar_dollar.configure
        else
            _t1608 = nothing
        end
        if _has_proto_field(_dollar_dollar, Symbol("sync"))
            _t1609 = _dollar_dollar.sync
        else
            _t1609 = nothing
        end
        fields804 = (_t1608, _t1609, _dollar_dollar.epochs,)
        unwrapped_fields805 = fields804
        write(pp, "(transaction")
        indent_sexp!(pp)
        field806 = unwrapped_fields805[1]
        if !isnothing(field806)
            newline(pp)
            opt_val807 = field806
            pretty_configure(pp, opt_val807)
        end
        field808 = unwrapped_fields805[2]
        if !isnothing(field808)
            newline(pp)
            opt_val809 = field808
            pretty_sync(pp, opt_val809)
        end
        field810 = unwrapped_fields805[3]
        if !isempty(field810)
            newline(pp)
            for (i1610, elem811) in enumerate(field810)
                i812 = i1610 - 1
                if (i812 > 0)
                    newline(pp)
                end
                pretty_epoch(pp, elem811)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_configure(pp::PrettyPrinter, msg::Proto.Configure)
    flat816 = try_flat(pp, msg, pretty_configure)
    if !isnothing(flat816)
        write(pp, flat816)
        return nothing
    else
        _dollar_dollar = msg
        _t1611 = deconstruct_configure(pp, _dollar_dollar)
        fields814 = _t1611
        unwrapped_fields815 = fields814
        write(pp, "(configure")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields815)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_config_dict(pp::PrettyPrinter, msg::Vector{Tuple{String, Proto.Value}})
    flat820 = try_flat(pp, msg, pretty_config_dict)
    if !isnothing(flat820)
        write(pp, flat820)
        return nothing
    else
        fields817 = msg
        write(pp, "{")
        indent!(pp)
        if !isempty(fields817)
            newline(pp)
            for (i1612, elem818) in enumerate(fields817)
                i819 = i1612 - 1
                if (i819 > 0)
                    newline(pp)
                end
                pretty_config_key_value(pp, elem818)
            end
        end
        dedent!(pp)
        write(pp, "}")
    end
    return nothing
end

function pretty_config_key_value(pp::PrettyPrinter, msg::Tuple{String, Proto.Value})
    flat825 = try_flat(pp, msg, pretty_config_key_value)
    if !isnothing(flat825)
        write(pp, flat825)
        return nothing
    else
        _dollar_dollar = msg
        fields821 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields822 = fields821
        write(pp, ":")
        field823 = unwrapped_fields822[1]
        write(pp, field823)
        write(pp, " ")
        field824 = unwrapped_fields822[2]
        pretty_raw_value(pp, field824)
    end
    return nothing
end

function pretty_raw_value(pp::PrettyPrinter, msg::Proto.Value)
    flat851 = try_flat(pp, msg, pretty_raw_value)
    if !isnothing(flat851)
        write(pp, flat851)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1613 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1613 = nothing
        end
        deconstruct_result849 = _t1613
        if !isnothing(deconstruct_result849)
            unwrapped850 = deconstruct_result849
            pretty_raw_date(pp, unwrapped850)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1614 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1614 = nothing
            end
            deconstruct_result847 = _t1614
            if !isnothing(deconstruct_result847)
                unwrapped848 = deconstruct_result847
                pretty_raw_datetime(pp, unwrapped848)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1615 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1615 = nothing
                end
                deconstruct_result845 = _t1615
                if !isnothing(deconstruct_result845)
                    unwrapped846 = deconstruct_result845
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped846))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1616 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1616 = nothing
                    end
                    deconstruct_result843 = _t1616
                    if !isnothing(deconstruct_result843)
                        unwrapped844 = deconstruct_result843
                        write(pp, (string(Int64(unwrapped844)) * "i32"))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1617 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1617 = nothing
                        end
                        deconstruct_result841 = _t1617
                        if !isnothing(deconstruct_result841)
                            unwrapped842 = deconstruct_result841
                            write(pp, string(unwrapped842))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1618 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1618 = nothing
                            end
                            deconstruct_result839 = _t1618
                            if !isnothing(deconstruct_result839)
                                unwrapped840 = deconstruct_result839
                                write(pp, format_float32_literal(unwrapped840))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1619 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1619 = nothing
                                end
                                deconstruct_result837 = _t1619
                                if !isnothing(deconstruct_result837)
                                    unwrapped838 = deconstruct_result837
                                    write(pp, lowercase(string(unwrapped838)))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1620 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1620 = nothing
                                    end
                                    deconstruct_result835 = _t1620
                                    if !isnothing(deconstruct_result835)
                                        unwrapped836 = deconstruct_result835
                                        write(pp, (string(Int64(unwrapped836)) * "u32"))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1621 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1621 = nothing
                                        end
                                        deconstruct_result833 = _t1621
                                        if !isnothing(deconstruct_result833)
                                            unwrapped834 = deconstruct_result833
                                            write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped834))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1622 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1622 = nothing
                                            end
                                            deconstruct_result831 = _t1622
                                            if !isnothing(deconstruct_result831)
                                                unwrapped832 = deconstruct_result831
                                                write(pp, format_int128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped832))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1623 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1623 = nothing
                                                end
                                                deconstruct_result829 = _t1623
                                                if !isnothing(deconstruct_result829)
                                                    unwrapped830 = deconstruct_result829
                                                    write(pp, format_decimal(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped830))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1624 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1624 = nothing
                                                    end
                                                    deconstruct_result827 = _t1624
                                                    if !isnothing(deconstruct_result827)
                                                        unwrapped828 = deconstruct_result827
                                                        pretty_boolean_value(pp, unwrapped828)
                                                    else
                                                        fields826 = msg
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
    flat857 = try_flat(pp, msg, pretty_raw_date)
    if !isnothing(flat857)
        write(pp, flat857)
        return nothing
    else
        _dollar_dollar = msg
        fields852 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields853 = fields852
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field854 = unwrapped_fields853[1]
        write(pp, string(field854))
        newline(pp)
        field855 = unwrapped_fields853[2]
        write(pp, string(field855))
        newline(pp)
        field856 = unwrapped_fields853[3]
        write(pp, string(field856))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_raw_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat868 = try_flat(pp, msg, pretty_raw_datetime)
    if !isnothing(flat868)
        write(pp, flat868)
        return nothing
    else
        _dollar_dollar = msg
        fields858 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields859 = fields858
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field860 = unwrapped_fields859[1]
        write(pp, string(field860))
        newline(pp)
        field861 = unwrapped_fields859[2]
        write(pp, string(field861))
        newline(pp)
        field862 = unwrapped_fields859[3]
        write(pp, string(field862))
        newline(pp)
        field863 = unwrapped_fields859[4]
        write(pp, string(field863))
        newline(pp)
        field864 = unwrapped_fields859[5]
        write(pp, string(field864))
        newline(pp)
        field865 = unwrapped_fields859[6]
        write(pp, string(field865))
        field866 = unwrapped_fields859[7]
        if !isnothing(field866)
            newline(pp)
            opt_val867 = field866
            write(pp, string(opt_val867))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_value(pp::PrettyPrinter, msg::Bool)
    _dollar_dollar = msg
    if _dollar_dollar
        _t1625 = ()
    else
        _t1625 = nothing
    end
    deconstruct_result871 = _t1625
    if !isnothing(deconstruct_result871)
        unwrapped872 = deconstruct_result871
        write(pp, "true")
    else
        _dollar_dollar = msg
        if !_dollar_dollar
            _t1626 = ()
        else
            _t1626 = nothing
        end
        deconstruct_result869 = _t1626
        if !isnothing(deconstruct_result869)
            unwrapped870 = deconstruct_result869
            write(pp, "false")
        else
            throw(ParseError("No matching rule for boolean_value"))
        end
    end
    return nothing
end

function pretty_sync(pp::PrettyPrinter, msg::Proto.Sync)
    flat877 = try_flat(pp, msg, pretty_sync)
    if !isnothing(flat877)
        write(pp, flat877)
        return nothing
    else
        _dollar_dollar = msg
        fields873 = _dollar_dollar.fragments
        unwrapped_fields874 = fields873
        write(pp, "(sync")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields874)
            newline(pp)
            for (i1627, elem875) in enumerate(unwrapped_fields874)
                i876 = i1627 - 1
                if (i876 > 0)
                    newline(pp)
                end
                pretty_fragment_id(pp, elem875)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat880 = try_flat(pp, msg, pretty_fragment_id)
    if !isnothing(flat880)
        write(pp, flat880)
        return nothing
    else
        _dollar_dollar = msg
        fields878 = fragment_id_to_string(pp, _dollar_dollar)
        unwrapped_fields879 = fields878
        write(pp, ":")
        write(pp, unwrapped_fields879)
    end
    return nothing
end

function pretty_epoch(pp::PrettyPrinter, msg::Proto.Epoch)
    flat887 = try_flat(pp, msg, pretty_epoch)
    if !isnothing(flat887)
        write(pp, flat887)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.writes)
            _t1628 = _dollar_dollar.writes
        else
            _t1628 = nothing
        end
        if !isempty(_dollar_dollar.reads)
            _t1629 = _dollar_dollar.reads
        else
            _t1629 = nothing
        end
        fields881 = (_t1628, _t1629,)
        unwrapped_fields882 = fields881
        write(pp, "(epoch")
        indent_sexp!(pp)
        field883 = unwrapped_fields882[1]
        if !isnothing(field883)
            newline(pp)
            opt_val884 = field883
            pretty_epoch_writes(pp, opt_val884)
        end
        field885 = unwrapped_fields882[2]
        if !isnothing(field885)
            newline(pp)
            opt_val886 = field885
            pretty_epoch_reads(pp, opt_val886)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_epoch_writes(pp::PrettyPrinter, msg::Vector{Proto.Write})
    flat891 = try_flat(pp, msg, pretty_epoch_writes)
    if !isnothing(flat891)
        write(pp, flat891)
        return nothing
    else
        fields888 = msg
        write(pp, "(writes")
        indent_sexp!(pp)
        if !isempty(fields888)
            newline(pp)
            for (i1630, elem889) in enumerate(fields888)
                i890 = i1630 - 1
                if (i890 > 0)
                    newline(pp)
                end
                pretty_write(pp, elem889)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_write(pp::PrettyPrinter, msg::Proto.Write)
    flat900 = try_flat(pp, msg, pretty_write)
    if !isnothing(flat900)
        write(pp, flat900)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("define"))
            _t1631 = _get_oneof_field(_dollar_dollar, :define)
        else
            _t1631 = nothing
        end
        deconstruct_result898 = _t1631
        if !isnothing(deconstruct_result898)
            unwrapped899 = deconstruct_result898
            pretty_define(pp, unwrapped899)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("undefine"))
                _t1632 = _get_oneof_field(_dollar_dollar, :undefine)
            else
                _t1632 = nothing
            end
            deconstruct_result896 = _t1632
            if !isnothing(deconstruct_result896)
                unwrapped897 = deconstruct_result896
                pretty_undefine(pp, unwrapped897)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("context"))
                    _t1633 = _get_oneof_field(_dollar_dollar, :context)
                else
                    _t1633 = nothing
                end
                deconstruct_result894 = _t1633
                if !isnothing(deconstruct_result894)
                    unwrapped895 = deconstruct_result894
                    pretty_context(pp, unwrapped895)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("snapshot"))
                        _t1634 = _get_oneof_field(_dollar_dollar, :snapshot)
                    else
                        _t1634 = nothing
                    end
                    deconstruct_result892 = _t1634
                    if !isnothing(deconstruct_result892)
                        unwrapped893 = deconstruct_result892
                        pretty_snapshot(pp, unwrapped893)
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
    flat903 = try_flat(pp, msg, pretty_define)
    if !isnothing(flat903)
        write(pp, flat903)
        return nothing
    else
        _dollar_dollar = msg
        fields901 = _dollar_dollar.fragment
        unwrapped_fields902 = fields901
        write(pp, "(define")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment(pp, unwrapped_fields902)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_fragment(pp::PrettyPrinter, msg::Proto.Fragment)
    flat910 = try_flat(pp, msg, pretty_fragment)
    if !isnothing(flat910)
        write(pp, flat910)
        return nothing
    else
        _dollar_dollar = msg
        start_pretty_fragment(pp, _dollar_dollar)
        fields904 = (_dollar_dollar.id, _dollar_dollar.declarations,)
        unwrapped_fields905 = fields904
        write(pp, "(fragment")
        indent_sexp!(pp)
        newline(pp)
        field906 = unwrapped_fields905[1]
        pretty_new_fragment_id(pp, field906)
        field907 = unwrapped_fields905[2]
        if !isempty(field907)
            newline(pp)
            for (i1635, elem908) in enumerate(field907)
                i909 = i1635 - 1
                if (i909 > 0)
                    newline(pp)
                end
                pretty_declaration(pp, elem908)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_new_fragment_id(pp::PrettyPrinter, msg::Proto.FragmentId)
    flat912 = try_flat(pp, msg, pretty_new_fragment_id)
    if !isnothing(flat912)
        write(pp, flat912)
        return nothing
    else
        fields911 = msg
        pretty_fragment_id(pp, fields911)
    end
    return nothing
end

function pretty_declaration(pp::PrettyPrinter, msg::Proto.Declaration)
    flat921 = try_flat(pp, msg, pretty_declaration)
    if !isnothing(flat921)
        write(pp, flat921)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("def"))
            _t1636 = _get_oneof_field(_dollar_dollar, :def)
        else
            _t1636 = nothing
        end
        deconstruct_result919 = _t1636
        if !isnothing(deconstruct_result919)
            unwrapped920 = deconstruct_result919
            pretty_def(pp, unwrapped920)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("algorithm"))
                _t1637 = _get_oneof_field(_dollar_dollar, :algorithm)
            else
                _t1637 = nothing
            end
            deconstruct_result917 = _t1637
            if !isnothing(deconstruct_result917)
                unwrapped918 = deconstruct_result917
                pretty_algorithm(pp, unwrapped918)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("constraint"))
                    _t1638 = _get_oneof_field(_dollar_dollar, :constraint)
                else
                    _t1638 = nothing
                end
                deconstruct_result915 = _t1638
                if !isnothing(deconstruct_result915)
                    unwrapped916 = deconstruct_result915
                    pretty_constraint(pp, unwrapped916)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("data"))
                        _t1639 = _get_oneof_field(_dollar_dollar, :data)
                    else
                        _t1639 = nothing
                    end
                    deconstruct_result913 = _t1639
                    if !isnothing(deconstruct_result913)
                        unwrapped914 = deconstruct_result913
                        pretty_data(pp, unwrapped914)
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
    flat928 = try_flat(pp, msg, pretty_def)
    if !isnothing(flat928)
        write(pp, flat928)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1640 = _dollar_dollar.attrs
        else
            _t1640 = nothing
        end
        fields922 = (_dollar_dollar.name, _dollar_dollar.body, _t1640,)
        unwrapped_fields923 = fields922
        write(pp, "(def")
        indent_sexp!(pp)
        newline(pp)
        field924 = unwrapped_fields923[1]
        pretty_relation_id(pp, field924)
        newline(pp)
        field925 = unwrapped_fields923[2]
        pretty_abstraction(pp, field925)
        field926 = unwrapped_fields923[3]
        if !isnothing(field926)
            newline(pp)
            opt_val927 = field926
            pretty_attrs(pp, opt_val927)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_relation_id(pp::PrettyPrinter, msg::Proto.RelationId)
    flat933 = try_flat(pp, msg, pretty_relation_id)
    if !isnothing(flat933)
        write(pp, flat933)
        return nothing
    else
        _dollar_dollar = msg
        if !isnothing(relation_id_to_string(pp, _dollar_dollar))
            _t1642 = deconstruct_relation_id_string(pp, _dollar_dollar)
            _t1641 = _t1642
        else
            _t1641 = nothing
        end
        deconstruct_result931 = _t1641
        if !isnothing(deconstruct_result931)
            unwrapped932 = deconstruct_result931
            write(pp, ":")
            write(pp, unwrapped932)
        else
            _dollar_dollar = msg
            _t1643 = deconstruct_relation_id_uint128(pp, _dollar_dollar)
            deconstruct_result929 = _t1643
            if !isnothing(deconstruct_result929)
                unwrapped930 = deconstruct_result929
                write(pp, format_uint128(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped930))
            else
                throw(ParseError("No matching rule for relation_id"))
            end
        end
    end
    return nothing
end

function pretty_abstraction(pp::PrettyPrinter, msg::Proto.Abstraction)
    flat938 = try_flat(pp, msg, pretty_abstraction)
    if !isnothing(flat938)
        write(pp, flat938)
        return nothing
    else
        _dollar_dollar = msg
        _t1644 = deconstruct_bindings(pp, _dollar_dollar)
        fields934 = (_t1644, _dollar_dollar.value,)
        unwrapped_fields935 = fields934
        write(pp, "(")
        indent!(pp)
        field936 = unwrapped_fields935[1]
        pretty_bindings(pp, field936)
        newline(pp)
        field937 = unwrapped_fields935[2]
        pretty_formula(pp, field937)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_bindings(pp::PrettyPrinter, msg::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}})
    flat946 = try_flat(pp, msg, pretty_bindings)
    if !isnothing(flat946)
        write(pp, flat946)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar[2])
            _t1645 = _dollar_dollar[2]
        else
            _t1645 = nothing
        end
        fields939 = (_dollar_dollar[1], _t1645,)
        unwrapped_fields940 = fields939
        write(pp, "[")
        indent!(pp)
        field941 = unwrapped_fields940[1]
        for (i1646, elem942) in enumerate(field941)
            i943 = i1646 - 1
            if (i943 > 0)
                newline(pp)
            end
            pretty_binding(pp, elem942)
        end
        field944 = unwrapped_fields940[2]
        if !isnothing(field944)
            newline(pp)
            opt_val945 = field944
            pretty_value_bindings(pp, opt_val945)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_binding(pp::PrettyPrinter, msg::Proto.Binding)
    flat951 = try_flat(pp, msg, pretty_binding)
    if !isnothing(flat951)
        write(pp, flat951)
        return nothing
    else
        _dollar_dollar = msg
        fields947 = (_dollar_dollar.var.name, _dollar_dollar.var"#type",)
        unwrapped_fields948 = fields947
        field949 = unwrapped_fields948[1]
        write(pp, field949)
        write(pp, "::")
        field950 = unwrapped_fields948[2]
        pretty_type(pp, field950)
    end
    return nothing
end

function pretty_type(pp::PrettyPrinter, msg::Proto.var"#Type")
    flat980 = try_flat(pp, msg, pretty_type)
    if !isnothing(flat980)
        write(pp, flat980)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("unspecified_type"))
            _t1647 = _get_oneof_field(_dollar_dollar, :unspecified_type)
        else
            _t1647 = nothing
        end
        deconstruct_result978 = _t1647
        if !isnothing(deconstruct_result978)
            unwrapped979 = deconstruct_result978
            pretty_unspecified_type(pp, unwrapped979)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("string_type"))
                _t1648 = _get_oneof_field(_dollar_dollar, :string_type)
            else
                _t1648 = nothing
            end
            deconstruct_result976 = _t1648
            if !isnothing(deconstruct_result976)
                unwrapped977 = deconstruct_result976
                pretty_string_type(pp, unwrapped977)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("int_type"))
                    _t1649 = _get_oneof_field(_dollar_dollar, :int_type)
                else
                    _t1649 = nothing
                end
                deconstruct_result974 = _t1649
                if !isnothing(deconstruct_result974)
                    unwrapped975 = deconstruct_result974
                    pretty_int_type(pp, unwrapped975)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("float_type"))
                        _t1650 = _get_oneof_field(_dollar_dollar, :float_type)
                    else
                        _t1650 = nothing
                    end
                    deconstruct_result972 = _t1650
                    if !isnothing(deconstruct_result972)
                        unwrapped973 = deconstruct_result972
                        pretty_float_type(pp, unwrapped973)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("uint128_type"))
                            _t1651 = _get_oneof_field(_dollar_dollar, :uint128_type)
                        else
                            _t1651 = nothing
                        end
                        deconstruct_result970 = _t1651
                        if !isnothing(deconstruct_result970)
                            unwrapped971 = deconstruct_result970
                            pretty_uint128_type(pp, unwrapped971)
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("int128_type"))
                                _t1652 = _get_oneof_field(_dollar_dollar, :int128_type)
                            else
                                _t1652 = nothing
                            end
                            deconstruct_result968 = _t1652
                            if !isnothing(deconstruct_result968)
                                unwrapped969 = deconstruct_result968
                                pretty_int128_type(pp, unwrapped969)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("date_type"))
                                    _t1653 = _get_oneof_field(_dollar_dollar, :date_type)
                                else
                                    _t1653 = nothing
                                end
                                deconstruct_result966 = _t1653
                                if !isnothing(deconstruct_result966)
                                    unwrapped967 = deconstruct_result966
                                    pretty_date_type(pp, unwrapped967)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("datetime_type"))
                                        _t1654 = _get_oneof_field(_dollar_dollar, :datetime_type)
                                    else
                                        _t1654 = nothing
                                    end
                                    deconstruct_result964 = _t1654
                                    if !isnothing(deconstruct_result964)
                                        unwrapped965 = deconstruct_result964
                                        pretty_datetime_type(pp, unwrapped965)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("missing_type"))
                                            _t1655 = _get_oneof_field(_dollar_dollar, :missing_type)
                                        else
                                            _t1655 = nothing
                                        end
                                        deconstruct_result962 = _t1655
                                        if !isnothing(deconstruct_result962)
                                            unwrapped963 = deconstruct_result962
                                            pretty_missing_type(pp, unwrapped963)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("decimal_type"))
                                                _t1656 = _get_oneof_field(_dollar_dollar, :decimal_type)
                                            else
                                                _t1656 = nothing
                                            end
                                            deconstruct_result960 = _t1656
                                            if !isnothing(deconstruct_result960)
                                                unwrapped961 = deconstruct_result960
                                                pretty_decimal_type(pp, unwrapped961)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("boolean_type"))
                                                    _t1657 = _get_oneof_field(_dollar_dollar, :boolean_type)
                                                else
                                                    _t1657 = nothing
                                                end
                                                deconstruct_result958 = _t1657
                                                if !isnothing(deconstruct_result958)
                                                    unwrapped959 = deconstruct_result958
                                                    pretty_boolean_type(pp, unwrapped959)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("int32_type"))
                                                        _t1658 = _get_oneof_field(_dollar_dollar, :int32_type)
                                                    else
                                                        _t1658 = nothing
                                                    end
                                                    deconstruct_result956 = _t1658
                                                    if !isnothing(deconstruct_result956)
                                                        unwrapped957 = deconstruct_result956
                                                        pretty_int32_type(pp, unwrapped957)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("float32_type"))
                                                            _t1659 = _get_oneof_field(_dollar_dollar, :float32_type)
                                                        else
                                                            _t1659 = nothing
                                                        end
                                                        deconstruct_result954 = _t1659
                                                        if !isnothing(deconstruct_result954)
                                                            unwrapped955 = deconstruct_result954
                                                            pretty_float32_type(pp, unwrapped955)
                                                        else
                                                            _dollar_dollar = msg
                                                            if _has_proto_field(_dollar_dollar, Symbol("uint32_type"))
                                                                _t1660 = _get_oneof_field(_dollar_dollar, :uint32_type)
                                                            else
                                                                _t1660 = nothing
                                                            end
                                                            deconstruct_result952 = _t1660
                                                            if !isnothing(deconstruct_result952)
                                                                unwrapped953 = deconstruct_result952
                                                                pretty_uint32_type(pp, unwrapped953)
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
    fields981 = msg
    write(pp, "UNKNOWN")
    return nothing
end

function pretty_string_type(pp::PrettyPrinter, msg::Proto.StringType)
    fields982 = msg
    write(pp, "STRING")
    return nothing
end

function pretty_int_type(pp::PrettyPrinter, msg::Proto.IntType)
    fields983 = msg
    write(pp, "INT")
    return nothing
end

function pretty_float_type(pp::PrettyPrinter, msg::Proto.FloatType)
    fields984 = msg
    write(pp, "FLOAT")
    return nothing
end

function pretty_uint128_type(pp::PrettyPrinter, msg::Proto.UInt128Type)
    fields985 = msg
    write(pp, "UINT128")
    return nothing
end

function pretty_int128_type(pp::PrettyPrinter, msg::Proto.Int128Type)
    fields986 = msg
    write(pp, "INT128")
    return nothing
end

function pretty_date_type(pp::PrettyPrinter, msg::Proto.DateType)
    fields987 = msg
    write(pp, "DATE")
    return nothing
end

function pretty_datetime_type(pp::PrettyPrinter, msg::Proto.DateTimeType)
    fields988 = msg
    write(pp, "DATETIME")
    return nothing
end

function pretty_missing_type(pp::PrettyPrinter, msg::Proto.MissingType)
    fields989 = msg
    write(pp, "MISSING")
    return nothing
end

function pretty_decimal_type(pp::PrettyPrinter, msg::Proto.DecimalType)
    flat994 = try_flat(pp, msg, pretty_decimal_type)
    if !isnothing(flat994)
        write(pp, flat994)
        return nothing
    else
        _dollar_dollar = msg
        fields990 = (Int64(_dollar_dollar.precision), Int64(_dollar_dollar.scale),)
        unwrapped_fields991 = fields990
        write(pp, "(DECIMAL")
        indent_sexp!(pp)
        newline(pp)
        field992 = unwrapped_fields991[1]
        write(pp, string(field992))
        newline(pp)
        field993 = unwrapped_fields991[2]
        write(pp, string(field993))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_boolean_type(pp::PrettyPrinter, msg::Proto.BooleanType)
    fields995 = msg
    write(pp, "BOOLEAN")
    return nothing
end

function pretty_int32_type(pp::PrettyPrinter, msg::Proto.Int32Type)
    fields996 = msg
    write(pp, "INT32")
    return nothing
end

function pretty_float32_type(pp::PrettyPrinter, msg::Proto.Float32Type)
    fields997 = msg
    write(pp, "FLOAT32")
    return nothing
end

function pretty_uint32_type(pp::PrettyPrinter, msg::Proto.UInt32Type)
    fields998 = msg
    write(pp, "UINT32")
    return nothing
end

function pretty_value_bindings(pp::PrettyPrinter, msg::Vector{Proto.Binding})
    flat1002 = try_flat(pp, msg, pretty_value_bindings)
    if !isnothing(flat1002)
        write(pp, flat1002)
        return nothing
    else
        fields999 = msg
        write(pp, "|")
        if !isempty(fields999)
            write(pp, " ")
            for (i1661, elem1000) in enumerate(fields999)
                i1001 = i1661 - 1
                if (i1001 > 0)
                    newline(pp)
                end
                pretty_binding(pp, elem1000)
            end
        end
    end
    return nothing
end

function pretty_formula(pp::PrettyPrinter, msg::Proto.Formula)
    flat1029 = try_flat(pp, msg, pretty_formula)
    if !isnothing(flat1029)
        write(pp, flat1029)
        return nothing
    else
        _dollar_dollar = msg
        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
            _t1662 = _get_oneof_field(_dollar_dollar, :conjunction)
        else
            _t1662 = nothing
        end
        deconstruct_result1027 = _t1662
        if !isnothing(deconstruct_result1027)
            unwrapped1028 = deconstruct_result1027
            pretty_true(pp, unwrapped1028)
        else
            _dollar_dollar = msg
            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                _t1663 = _get_oneof_field(_dollar_dollar, :disjunction)
            else
                _t1663 = nothing
            end
            deconstruct_result1025 = _t1663
            if !isnothing(deconstruct_result1025)
                unwrapped1026 = deconstruct_result1025
                pretty_false(pp, unwrapped1026)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("exists"))
                    _t1664 = _get_oneof_field(_dollar_dollar, :exists)
                else
                    _t1664 = nothing
                end
                deconstruct_result1023 = _t1664
                if !isnothing(deconstruct_result1023)
                    unwrapped1024 = deconstruct_result1023
                    pretty_exists(pp, unwrapped1024)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("reduce"))
                        _t1665 = _get_oneof_field(_dollar_dollar, :reduce)
                    else
                        _t1665 = nothing
                    end
                    deconstruct_result1021 = _t1665
                    if !isnothing(deconstruct_result1021)
                        unwrapped1022 = deconstruct_result1021
                        pretty_reduce(pp, unwrapped1022)
                    else
                        _dollar_dollar = msg
                        if (_has_proto_field(_dollar_dollar, Symbol("conjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :conjunction).args))
                            _t1666 = _get_oneof_field(_dollar_dollar, :conjunction)
                        else
                            _t1666 = nothing
                        end
                        deconstruct_result1019 = _t1666
                        if !isnothing(deconstruct_result1019)
                            unwrapped1020 = deconstruct_result1019
                            pretty_conjunction(pp, unwrapped1020)
                        else
                            _dollar_dollar = msg
                            if (_has_proto_field(_dollar_dollar, Symbol("disjunction")) && !isempty(_get_oneof_field(_dollar_dollar, :disjunction).args))
                                _t1667 = _get_oneof_field(_dollar_dollar, :disjunction)
                            else
                                _t1667 = nothing
                            end
                            deconstruct_result1017 = _t1667
                            if !isnothing(deconstruct_result1017)
                                unwrapped1018 = deconstruct_result1017
                                pretty_disjunction(pp, unwrapped1018)
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("not"))
                                    _t1668 = _get_oneof_field(_dollar_dollar, :not)
                                else
                                    _t1668 = nothing
                                end
                                deconstruct_result1015 = _t1668
                                if !isnothing(deconstruct_result1015)
                                    unwrapped1016 = deconstruct_result1015
                                    pretty_not(pp, unwrapped1016)
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("ffi"))
                                        _t1669 = _get_oneof_field(_dollar_dollar, :ffi)
                                    else
                                        _t1669 = nothing
                                    end
                                    deconstruct_result1013 = _t1669
                                    if !isnothing(deconstruct_result1013)
                                        unwrapped1014 = deconstruct_result1013
                                        pretty_ffi(pp, unwrapped1014)
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("atom"))
                                            _t1670 = _get_oneof_field(_dollar_dollar, :atom)
                                        else
                                            _t1670 = nothing
                                        end
                                        deconstruct_result1011 = _t1670
                                        if !isnothing(deconstruct_result1011)
                                            unwrapped1012 = deconstruct_result1011
                                            pretty_atom(pp, unwrapped1012)
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("pragma"))
                                                _t1671 = _get_oneof_field(_dollar_dollar, :pragma)
                                            else
                                                _t1671 = nothing
                                            end
                                            deconstruct_result1009 = _t1671
                                            if !isnothing(deconstruct_result1009)
                                                unwrapped1010 = deconstruct_result1009
                                                pretty_pragma(pp, unwrapped1010)
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("primitive"))
                                                    _t1672 = _get_oneof_field(_dollar_dollar, :primitive)
                                                else
                                                    _t1672 = nothing
                                                end
                                                deconstruct_result1007 = _t1672
                                                if !isnothing(deconstruct_result1007)
                                                    unwrapped1008 = deconstruct_result1007
                                                    pretty_primitive(pp, unwrapped1008)
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("rel_atom"))
                                                        _t1673 = _get_oneof_field(_dollar_dollar, :rel_atom)
                                                    else
                                                        _t1673 = nothing
                                                    end
                                                    deconstruct_result1005 = _t1673
                                                    if !isnothing(deconstruct_result1005)
                                                        unwrapped1006 = deconstruct_result1005
                                                        pretty_rel_atom(pp, unwrapped1006)
                                                    else
                                                        _dollar_dollar = msg
                                                        if _has_proto_field(_dollar_dollar, Symbol("cast"))
                                                            _t1674 = _get_oneof_field(_dollar_dollar, :cast)
                                                        else
                                                            _t1674 = nothing
                                                        end
                                                        deconstruct_result1003 = _t1674
                                                        if !isnothing(deconstruct_result1003)
                                                            unwrapped1004 = deconstruct_result1003
                                                            pretty_cast(pp, unwrapped1004)
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
    fields1030 = msg
    write(pp, "(true)")
    return nothing
end

function pretty_false(pp::PrettyPrinter, msg::Proto.Disjunction)
    fields1031 = msg
    write(pp, "(false)")
    return nothing
end

function pretty_exists(pp::PrettyPrinter, msg::Proto.Exists)
    flat1036 = try_flat(pp, msg, pretty_exists)
    if !isnothing(flat1036)
        write(pp, flat1036)
        return nothing
    else
        _dollar_dollar = msg
        _t1675 = deconstruct_bindings(pp, _dollar_dollar.body)
        fields1032 = (_t1675, _dollar_dollar.body.value,)
        unwrapped_fields1033 = fields1032
        write(pp, "(exists")
        indent_sexp!(pp)
        newline(pp)
        field1034 = unwrapped_fields1033[1]
        pretty_bindings(pp, field1034)
        newline(pp)
        field1035 = unwrapped_fields1033[2]
        pretty_formula(pp, field1035)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_reduce(pp::PrettyPrinter, msg::Proto.Reduce)
    flat1042 = try_flat(pp, msg, pretty_reduce)
    if !isnothing(flat1042)
        write(pp, flat1042)
        return nothing
    else
        _dollar_dollar = msg
        fields1037 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        unwrapped_fields1038 = fields1037
        write(pp, "(reduce")
        indent_sexp!(pp)
        newline(pp)
        field1039 = unwrapped_fields1038[1]
        pretty_abstraction(pp, field1039)
        newline(pp)
        field1040 = unwrapped_fields1038[2]
        pretty_abstraction(pp, field1040)
        newline(pp)
        field1041 = unwrapped_fields1038[3]
        pretty_terms(pp, field1041)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_terms(pp::PrettyPrinter, msg::Vector{Proto.Term})
    flat1046 = try_flat(pp, msg, pretty_terms)
    if !isnothing(flat1046)
        write(pp, flat1046)
        return nothing
    else
        fields1043 = msg
        write(pp, "(terms")
        indent_sexp!(pp)
        if !isempty(fields1043)
            newline(pp)
            for (i1676, elem1044) in enumerate(fields1043)
                i1045 = i1676 - 1
                if (i1045 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1044)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_term(pp::PrettyPrinter, msg::Proto.Term)
    flat1051 = try_flat(pp, msg, pretty_term)
    if !isnothing(flat1051)
        write(pp, flat1051)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("var"))
            _t1677 = _get_oneof_field(_dollar_dollar, :var)
        else
            _t1677 = nothing
        end
        deconstruct_result1049 = _t1677
        if !isnothing(deconstruct_result1049)
            unwrapped1050 = deconstruct_result1049
            pretty_var(pp, unwrapped1050)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("constant"))
                _t1678 = _get_oneof_field(_dollar_dollar, :constant)
            else
                _t1678 = nothing
            end
            deconstruct_result1047 = _t1678
            if !isnothing(deconstruct_result1047)
                unwrapped1048 = deconstruct_result1047
                pretty_value(pp, unwrapped1048)
            else
                throw(ParseError("No matching rule for term"))
            end
        end
    end
    return nothing
end

function pretty_var(pp::PrettyPrinter, msg::Proto.Var)
    flat1054 = try_flat(pp, msg, pretty_var)
    if !isnothing(flat1054)
        write(pp, flat1054)
        return nothing
    else
        _dollar_dollar = msg
        fields1052 = _dollar_dollar.name
        unwrapped_fields1053 = fields1052
        write(pp, unwrapped_fields1053)
    end
    return nothing
end

function pretty_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1080 = try_flat(pp, msg, pretty_value)
    if !isnothing(flat1080)
        write(pp, flat1080)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("date_value"))
            _t1679 = _get_oneof_field(_dollar_dollar, :date_value)
        else
            _t1679 = nothing
        end
        deconstruct_result1078 = _t1679
        if !isnothing(deconstruct_result1078)
            unwrapped1079 = deconstruct_result1078
            pretty_date(pp, unwrapped1079)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("datetime_value"))
                _t1680 = _get_oneof_field(_dollar_dollar, :datetime_value)
            else
                _t1680 = nothing
            end
            deconstruct_result1076 = _t1680
            if !isnothing(deconstruct_result1076)
                unwrapped1077 = deconstruct_result1076
                pretty_datetime(pp, unwrapped1077)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("string_value"))
                    _t1681 = _get_oneof_field(_dollar_dollar, :string_value)
                else
                    _t1681 = nothing
                end
                deconstruct_result1074 = _t1681
                if !isnothing(deconstruct_result1074)
                    unwrapped1075 = deconstruct_result1074
                    write(pp, format_string(pp, unwrapped1075))
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("int32_value"))
                        _t1682 = _get_oneof_field(_dollar_dollar, :int32_value)
                    else
                        _t1682 = nothing
                    end
                    deconstruct_result1072 = _t1682
                    if !isnothing(deconstruct_result1072)
                        unwrapped1073 = deconstruct_result1072
                        write(pp, format_int32(pp, unwrapped1073))
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("int_value"))
                            _t1683 = _get_oneof_field(_dollar_dollar, :int_value)
                        else
                            _t1683 = nothing
                        end
                        deconstruct_result1070 = _t1683
                        if !isnothing(deconstruct_result1070)
                            unwrapped1071 = deconstruct_result1070
                            write(pp, format_int(pp, unwrapped1071))
                        else
                            _dollar_dollar = msg
                            if _has_proto_field(_dollar_dollar, Symbol("float32_value"))
                                _t1684 = _get_oneof_field(_dollar_dollar, :float32_value)
                            else
                                _t1684 = nothing
                            end
                            deconstruct_result1068 = _t1684
                            if !isnothing(deconstruct_result1068)
                                unwrapped1069 = deconstruct_result1068
                                write(pp, format_float32(pp, unwrapped1069))
                            else
                                _dollar_dollar = msg
                                if _has_proto_field(_dollar_dollar, Symbol("float_value"))
                                    _t1685 = _get_oneof_field(_dollar_dollar, :float_value)
                                else
                                    _t1685 = nothing
                                end
                                deconstruct_result1066 = _t1685
                                if !isnothing(deconstruct_result1066)
                                    unwrapped1067 = deconstruct_result1066
                                    write(pp, format_float(pp, unwrapped1067))
                                else
                                    _dollar_dollar = msg
                                    if _has_proto_field(_dollar_dollar, Symbol("uint32_value"))
                                        _t1686 = _get_oneof_field(_dollar_dollar, :uint32_value)
                                    else
                                        _t1686 = nothing
                                    end
                                    deconstruct_result1064 = _t1686
                                    if !isnothing(deconstruct_result1064)
                                        unwrapped1065 = deconstruct_result1064
                                        write(pp, format_uint32(pp, unwrapped1065))
                                    else
                                        _dollar_dollar = msg
                                        if _has_proto_field(_dollar_dollar, Symbol("uint128_value"))
                                            _t1687 = _get_oneof_field(_dollar_dollar, :uint128_value)
                                        else
                                            _t1687 = nothing
                                        end
                                        deconstruct_result1062 = _t1687
                                        if !isnothing(deconstruct_result1062)
                                            unwrapped1063 = deconstruct_result1062
                                            write(pp, format_uint128(pp, unwrapped1063))
                                        else
                                            _dollar_dollar = msg
                                            if _has_proto_field(_dollar_dollar, Symbol("int128_value"))
                                                _t1688 = _get_oneof_field(_dollar_dollar, :int128_value)
                                            else
                                                _t1688 = nothing
                                            end
                                            deconstruct_result1060 = _t1688
                                            if !isnothing(deconstruct_result1060)
                                                unwrapped1061 = deconstruct_result1060
                                                write(pp, format_int128(pp, unwrapped1061))
                                            else
                                                _dollar_dollar = msg
                                                if _has_proto_field(_dollar_dollar, Symbol("decimal_value"))
                                                    _t1689 = _get_oneof_field(_dollar_dollar, :decimal_value)
                                                else
                                                    _t1689 = nothing
                                                end
                                                deconstruct_result1058 = _t1689
                                                if !isnothing(deconstruct_result1058)
                                                    unwrapped1059 = deconstruct_result1058
                                                    write(pp, format_decimal(pp, unwrapped1059))
                                                else
                                                    _dollar_dollar = msg
                                                    if _has_proto_field(_dollar_dollar, Symbol("boolean_value"))
                                                        _t1690 = _get_oneof_field(_dollar_dollar, :boolean_value)
                                                    else
                                                        _t1690 = nothing
                                                    end
                                                    deconstruct_result1056 = _t1690
                                                    if !isnothing(deconstruct_result1056)
                                                        unwrapped1057 = deconstruct_result1056
                                                        pretty_boolean_value(pp, unwrapped1057)
                                                    else
                                                        fields1055 = msg
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
    flat1086 = try_flat(pp, msg, pretty_date)
    if !isnothing(flat1086)
        write(pp, flat1086)
        return nothing
    else
        _dollar_dollar = msg
        fields1081 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day),)
        unwrapped_fields1082 = fields1081
        write(pp, "(date")
        indent_sexp!(pp)
        newline(pp)
        field1083 = unwrapped_fields1082[1]
        write(pp, format_int(pp, field1083))
        newline(pp)
        field1084 = unwrapped_fields1082[2]
        write(pp, format_int(pp, field1084))
        newline(pp)
        field1085 = unwrapped_fields1082[3]
        write(pp, format_int(pp, field1085))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_datetime(pp::PrettyPrinter, msg::Proto.DateTimeValue)
    flat1097 = try_flat(pp, msg, pretty_datetime)
    if !isnothing(flat1097)
        write(pp, flat1097)
        return nothing
    else
        _dollar_dollar = msg
        fields1087 = (Int64(_dollar_dollar.year), Int64(_dollar_dollar.month), Int64(_dollar_dollar.day), Int64(_dollar_dollar.hour), Int64(_dollar_dollar.minute), Int64(_dollar_dollar.second), Int64(_dollar_dollar.microsecond),)
        unwrapped_fields1088 = fields1087
        write(pp, "(datetime")
        indent_sexp!(pp)
        newline(pp)
        field1089 = unwrapped_fields1088[1]
        write(pp, format_int(pp, field1089))
        newline(pp)
        field1090 = unwrapped_fields1088[2]
        write(pp, format_int(pp, field1090))
        newline(pp)
        field1091 = unwrapped_fields1088[3]
        write(pp, format_int(pp, field1091))
        newline(pp)
        field1092 = unwrapped_fields1088[4]
        write(pp, format_int(pp, field1092))
        newline(pp)
        field1093 = unwrapped_fields1088[5]
        write(pp, format_int(pp, field1093))
        newline(pp)
        field1094 = unwrapped_fields1088[6]
        write(pp, format_int(pp, field1094))
        field1095 = unwrapped_fields1088[7]
        if !isnothing(field1095)
            newline(pp)
            opt_val1096 = field1095
            write(pp, format_int(pp, opt_val1096))
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_conjunction(pp::PrettyPrinter, msg::Proto.Conjunction)
    flat1102 = try_flat(pp, msg, pretty_conjunction)
    if !isnothing(flat1102)
        write(pp, flat1102)
        return nothing
    else
        _dollar_dollar = msg
        fields1098 = _dollar_dollar.args
        unwrapped_fields1099 = fields1098
        write(pp, "(and")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1099)
            newline(pp)
            for (i1691, elem1100) in enumerate(unwrapped_fields1099)
                i1101 = i1691 - 1
                if (i1101 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1100)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_disjunction(pp::PrettyPrinter, msg::Proto.Disjunction)
    flat1107 = try_flat(pp, msg, pretty_disjunction)
    if !isnothing(flat1107)
        write(pp, flat1107)
        return nothing
    else
        _dollar_dollar = msg
        fields1103 = _dollar_dollar.args
        unwrapped_fields1104 = fields1103
        write(pp, "(or")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1104)
            newline(pp)
            for (i1692, elem1105) in enumerate(unwrapped_fields1104)
                i1106 = i1692 - 1
                if (i1106 > 0)
                    newline(pp)
                end
                pretty_formula(pp, elem1105)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_not(pp::PrettyPrinter, msg::Proto.Not)
    flat1110 = try_flat(pp, msg, pretty_not)
    if !isnothing(flat1110)
        write(pp, flat1110)
        return nothing
    else
        _dollar_dollar = msg
        fields1108 = _dollar_dollar.arg
        unwrapped_fields1109 = fields1108
        write(pp, "(not")
        indent_sexp!(pp)
        newline(pp)
        pretty_formula(pp, unwrapped_fields1109)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_ffi(pp::PrettyPrinter, msg::Proto.FFI)
    flat1116 = try_flat(pp, msg, pretty_ffi)
    if !isnothing(flat1116)
        write(pp, flat1116)
        return nothing
    else
        _dollar_dollar = msg
        fields1111 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        unwrapped_fields1112 = fields1111
        write(pp, "(ffi")
        indent_sexp!(pp)
        newline(pp)
        field1113 = unwrapped_fields1112[1]
        pretty_name(pp, field1113)
        newline(pp)
        field1114 = unwrapped_fields1112[2]
        pretty_ffi_args(pp, field1114)
        newline(pp)
        field1115 = unwrapped_fields1112[3]
        pretty_terms(pp, field1115)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_name(pp::PrettyPrinter, msg::String)
    flat1118 = try_flat(pp, msg, pretty_name)
    if !isnothing(flat1118)
        write(pp, flat1118)
        return nothing
    else
        fields1117 = msg
        write(pp, ":")
        write(pp, fields1117)
    end
    return nothing
end

function pretty_ffi_args(pp::PrettyPrinter, msg::Vector{Proto.Abstraction})
    flat1122 = try_flat(pp, msg, pretty_ffi_args)
    if !isnothing(flat1122)
        write(pp, flat1122)
        return nothing
    else
        fields1119 = msg
        write(pp, "(args")
        indent_sexp!(pp)
        if !isempty(fields1119)
            newline(pp)
            for (i1693, elem1120) in enumerate(fields1119)
                i1121 = i1693 - 1
                if (i1121 > 0)
                    newline(pp)
                end
                pretty_abstraction(pp, elem1120)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_atom(pp::PrettyPrinter, msg::Proto.Atom)
    flat1129 = try_flat(pp, msg, pretty_atom)
    if !isnothing(flat1129)
        write(pp, flat1129)
        return nothing
    else
        _dollar_dollar = msg
        fields1123 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1124 = fields1123
        write(pp, "(atom")
        indent_sexp!(pp)
        newline(pp)
        field1125 = unwrapped_fields1124[1]
        pretty_relation_id(pp, field1125)
        field1126 = unwrapped_fields1124[2]
        if !isempty(field1126)
            newline(pp)
            for (i1694, elem1127) in enumerate(field1126)
                i1128 = i1694 - 1
                if (i1128 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1127)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_pragma(pp::PrettyPrinter, msg::Proto.Pragma)
    flat1136 = try_flat(pp, msg, pretty_pragma)
    if !isnothing(flat1136)
        write(pp, flat1136)
        return nothing
    else
        _dollar_dollar = msg
        fields1130 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1131 = fields1130
        write(pp, "(pragma")
        indent_sexp!(pp)
        newline(pp)
        field1132 = unwrapped_fields1131[1]
        pretty_name(pp, field1132)
        field1133 = unwrapped_fields1131[2]
        if !isempty(field1133)
            newline(pp)
            for (i1695, elem1134) in enumerate(field1133)
                i1135 = i1695 - 1
                if (i1135 > 0)
                    newline(pp)
                end
                pretty_term(pp, elem1134)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_primitive(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1152 = try_flat(pp, msg, pretty_primitive)
    if !isnothing(flat1152)
        write(pp, flat1152)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1696 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1696 = nothing
        end
        guard_result1151 = _t1696
        if !isnothing(guard_result1151)
            pretty_eq(pp, msg)
        else
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype"
                _t1697 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
            else
                _t1697 = nothing
            end
            guard_result1150 = _t1697
            if !isnothing(guard_result1150)
                pretty_lt(pp, msg)
            else
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
                    _t1698 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                else
                    _t1698 = nothing
                end
                guard_result1149 = _t1698
                if !isnothing(guard_result1149)
                    pretty_lt_eq(pp, msg)
                else
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_gt_monotype"
                        _t1699 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                    else
                        _t1699 = nothing
                    end
                    guard_result1148 = _t1699
                    if !isnothing(guard_result1148)
                        pretty_gt(pp, msg)
                    else
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
                            _t1700 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
                        else
                            _t1700 = nothing
                        end
                        guard_result1147 = _t1700
                        if !isnothing(guard_result1147)
                            pretty_gt_eq(pp, msg)
                        else
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_add_monotype"
                                _t1701 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                            else
                                _t1701 = nothing
                            end
                            guard_result1146 = _t1701
                            if !isnothing(guard_result1146)
                                pretty_add(pp, msg)
                            else
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_subtract_monotype"
                                    _t1702 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                else
                                    _t1702 = nothing
                                end
                                guard_result1145 = _t1702
                                if !isnothing(guard_result1145)
                                    pretty_minus(pp, msg)
                                else
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_multiply_monotype"
                                        _t1703 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                    else
                                        _t1703 = nothing
                                    end
                                    guard_result1144 = _t1703
                                    if !isnothing(guard_result1144)
                                        pretty_multiply(pp, msg)
                                    else
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_divide_monotype"
                                            _t1704 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
                                        else
                                            _t1704 = nothing
                                        end
                                        guard_result1143 = _t1704
                                        if !isnothing(guard_result1143)
                                            pretty_divide(pp, msg)
                                        else
                                            _dollar_dollar = msg
                                            fields1137 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                            unwrapped_fields1138 = fields1137
                                            write(pp, "(primitive")
                                            indent_sexp!(pp)
                                            newline(pp)
                                            field1139 = unwrapped_fields1138[1]
                                            pretty_name(pp, field1139)
                                            field1140 = unwrapped_fields1138[2]
                                            if !isempty(field1140)
                                                newline(pp)
                                                for (i1705, elem1141) in enumerate(field1140)
                                                    i1142 = i1705 - 1
                                                    if (i1142 > 0)
                                                        newline(pp)
                                                    end
                                                    pretty_rel_term(pp, elem1141)
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
    flat1157 = try_flat(pp, msg, pretty_eq)
    if !isnothing(flat1157)
        write(pp, flat1157)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_eq"
            _t1706 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1706 = nothing
        end
        fields1153 = _t1706
        unwrapped_fields1154 = fields1153
        write(pp, "(=")
        indent_sexp!(pp)
        newline(pp)
        field1155 = unwrapped_fields1154[1]
        pretty_term(pp, field1155)
        newline(pp)
        field1156 = unwrapped_fields1154[2]
        pretty_term(pp, field1156)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1162 = try_flat(pp, msg, pretty_lt)
    if !isnothing(flat1162)
        write(pp, flat1162)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_monotype"
            _t1707 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1707 = nothing
        end
        fields1158 = _t1707
        unwrapped_fields1159 = fields1158
        write(pp, "(<")
        indent_sexp!(pp)
        newline(pp)
        field1160 = unwrapped_fields1159[1]
        pretty_term(pp, field1160)
        newline(pp)
        field1161 = unwrapped_fields1159[2]
        pretty_term(pp, field1161)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_lt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1167 = try_flat(pp, msg, pretty_lt_eq)
    if !isnothing(flat1167)
        write(pp, flat1167)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype"
            _t1708 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1708 = nothing
        end
        fields1163 = _t1708
        unwrapped_fields1164 = fields1163
        write(pp, "(<=")
        indent_sexp!(pp)
        newline(pp)
        field1165 = unwrapped_fields1164[1]
        pretty_term(pp, field1165)
        newline(pp)
        field1166 = unwrapped_fields1164[2]
        pretty_term(pp, field1166)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1172 = try_flat(pp, msg, pretty_gt)
    if !isnothing(flat1172)
        write(pp, flat1172)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_monotype"
            _t1709 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1709 = nothing
        end
        fields1168 = _t1709
        unwrapped_fields1169 = fields1168
        write(pp, "(>")
        indent_sexp!(pp)
        newline(pp)
        field1170 = unwrapped_fields1169[1]
        pretty_term(pp, field1170)
        newline(pp)
        field1171 = unwrapped_fields1169[2]
        pretty_term(pp, field1171)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gt_eq(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1177 = try_flat(pp, msg, pretty_gt_eq)
    if !isnothing(flat1177)
        write(pp, flat1177)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_gt_eq_monotype"
            _t1710 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term),)
        else
            _t1710 = nothing
        end
        fields1173 = _t1710
        unwrapped_fields1174 = fields1173
        write(pp, "(>=")
        indent_sexp!(pp)
        newline(pp)
        field1175 = unwrapped_fields1174[1]
        pretty_term(pp, field1175)
        newline(pp)
        field1176 = unwrapped_fields1174[2]
        pretty_term(pp, field1176)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_add(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1183 = try_flat(pp, msg, pretty_add)
    if !isnothing(flat1183)
        write(pp, flat1183)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_add_monotype"
            _t1711 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1711 = nothing
        end
        fields1178 = _t1711
        unwrapped_fields1179 = fields1178
        write(pp, "(+")
        indent_sexp!(pp)
        newline(pp)
        field1180 = unwrapped_fields1179[1]
        pretty_term(pp, field1180)
        newline(pp)
        field1181 = unwrapped_fields1179[2]
        pretty_term(pp, field1181)
        newline(pp)
        field1182 = unwrapped_fields1179[3]
        pretty_term(pp, field1182)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_minus(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1189 = try_flat(pp, msg, pretty_minus)
    if !isnothing(flat1189)
        write(pp, flat1189)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_subtract_monotype"
            _t1712 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1712 = nothing
        end
        fields1184 = _t1712
        unwrapped_fields1185 = fields1184
        write(pp, "(-")
        indent_sexp!(pp)
        newline(pp)
        field1186 = unwrapped_fields1185[1]
        pretty_term(pp, field1186)
        newline(pp)
        field1187 = unwrapped_fields1185[2]
        pretty_term(pp, field1187)
        newline(pp)
        field1188 = unwrapped_fields1185[3]
        pretty_term(pp, field1188)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_multiply(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1195 = try_flat(pp, msg, pretty_multiply)
    if !isnothing(flat1195)
        write(pp, flat1195)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_multiply_monotype"
            _t1713 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1713 = nothing
        end
        fields1190 = _t1713
        unwrapped_fields1191 = fields1190
        write(pp, "(*")
        indent_sexp!(pp)
        newline(pp)
        field1192 = unwrapped_fields1191[1]
        pretty_term(pp, field1192)
        newline(pp)
        field1193 = unwrapped_fields1191[2]
        pretty_term(pp, field1193)
        newline(pp)
        field1194 = unwrapped_fields1191[3]
        pretty_term(pp, field1194)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_divide(pp::PrettyPrinter, msg::Proto.Primitive)
    flat1201 = try_flat(pp, msg, pretty_divide)
    if !isnothing(flat1201)
        write(pp, flat1201)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name == "rel_primitive_divide_monotype"
            _t1714 = (_get_oneof_field(_dollar_dollar.terms[1], :term), _get_oneof_field(_dollar_dollar.terms[2], :term), _get_oneof_field(_dollar_dollar.terms[3], :term),)
        else
            _t1714 = nothing
        end
        fields1196 = _t1714
        unwrapped_fields1197 = fields1196
        write(pp, "(/")
        indent_sexp!(pp)
        newline(pp)
        field1198 = unwrapped_fields1197[1]
        pretty_term(pp, field1198)
        newline(pp)
        field1199 = unwrapped_fields1197[2]
        pretty_term(pp, field1199)
        newline(pp)
        field1200 = unwrapped_fields1197[3]
        pretty_term(pp, field1200)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_rel_term(pp::PrettyPrinter, msg::Proto.RelTerm)
    flat1206 = try_flat(pp, msg, pretty_rel_term)
    if !isnothing(flat1206)
        write(pp, flat1206)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("specialized_value"))
            _t1715 = _get_oneof_field(_dollar_dollar, :specialized_value)
        else
            _t1715 = nothing
        end
        deconstruct_result1204 = _t1715
        if !isnothing(deconstruct_result1204)
            unwrapped1205 = deconstruct_result1204
            pretty_specialized_value(pp, unwrapped1205)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("term"))
                _t1716 = _get_oneof_field(_dollar_dollar, :term)
            else
                _t1716 = nothing
            end
            deconstruct_result1202 = _t1716
            if !isnothing(deconstruct_result1202)
                unwrapped1203 = deconstruct_result1202
                pretty_term(pp, unwrapped1203)
            else
                throw(ParseError("No matching rule for rel_term"))
            end
        end
    end
    return nothing
end

function pretty_specialized_value(pp::PrettyPrinter, msg::Proto.Value)
    flat1208 = try_flat(pp, msg, pretty_specialized_value)
    if !isnothing(flat1208)
        write(pp, flat1208)
        return nothing
    else
        fields1207 = msg
        write(pp, "#")
        pretty_raw_value(pp, fields1207)
    end
    return nothing
end

function pretty_rel_atom(pp::PrettyPrinter, msg::Proto.RelAtom)
    flat1215 = try_flat(pp, msg, pretty_rel_atom)
    if !isnothing(flat1215)
        write(pp, flat1215)
        return nothing
    else
        _dollar_dollar = msg
        fields1209 = (_dollar_dollar.name, _dollar_dollar.terms,)
        unwrapped_fields1210 = fields1209
        write(pp, "(relatom")
        indent_sexp!(pp)
        newline(pp)
        field1211 = unwrapped_fields1210[1]
        pretty_name(pp, field1211)
        field1212 = unwrapped_fields1210[2]
        if !isempty(field1212)
            newline(pp)
            for (i1717, elem1213) in enumerate(field1212)
                i1214 = i1717 - 1
                if (i1214 > 0)
                    newline(pp)
                end
                pretty_rel_term(pp, elem1213)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_cast(pp::PrettyPrinter, msg::Proto.Cast)
    flat1220 = try_flat(pp, msg, pretty_cast)
    if !isnothing(flat1220)
        write(pp, flat1220)
        return nothing
    else
        _dollar_dollar = msg
        fields1216 = (_dollar_dollar.input, _dollar_dollar.result,)
        unwrapped_fields1217 = fields1216
        write(pp, "(cast")
        indent_sexp!(pp)
        newline(pp)
        field1218 = unwrapped_fields1217[1]
        pretty_term(pp, field1218)
        newline(pp)
        field1219 = unwrapped_fields1217[2]
        pretty_term(pp, field1219)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attrs(pp::PrettyPrinter, msg::Vector{Proto.Attribute})
    flat1224 = try_flat(pp, msg, pretty_attrs)
    if !isnothing(flat1224)
        write(pp, flat1224)
        return nothing
    else
        fields1221 = msg
        write(pp, "(attrs")
        indent_sexp!(pp)
        if !isempty(fields1221)
            newline(pp)
            for (i1718, elem1222) in enumerate(fields1221)
                i1223 = i1718 - 1
                if (i1223 > 0)
                    newline(pp)
                end
                pretty_attribute(pp, elem1222)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_attribute(pp::PrettyPrinter, msg::Proto.Attribute)
    flat1231 = try_flat(pp, msg, pretty_attribute)
    if !isnothing(flat1231)
        write(pp, flat1231)
        return nothing
    else
        _dollar_dollar = msg
        fields1225 = (_dollar_dollar.name, _dollar_dollar.args,)
        unwrapped_fields1226 = fields1225
        write(pp, "(attribute")
        indent_sexp!(pp)
        newline(pp)
        field1227 = unwrapped_fields1226[1]
        pretty_name(pp, field1227)
        field1228 = unwrapped_fields1226[2]
        if !isempty(field1228)
            newline(pp)
            for (i1719, elem1229) in enumerate(field1228)
                i1230 = i1719 - 1
                if (i1230 > 0)
                    newline(pp)
                end
                pretty_raw_value(pp, elem1229)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_algorithm(pp::PrettyPrinter, msg::Proto.Algorithm)
    flat1240 = try_flat(pp, msg, pretty_algorithm)
    if !isnothing(flat1240)
        write(pp, flat1240)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1720 = _dollar_dollar.attrs
        else
            _t1720 = nothing
        end
        fields1232 = (_dollar_dollar.var"#global", _dollar_dollar.body, _t1720,)
        unwrapped_fields1233 = fields1232
        write(pp, "(algorithm")
        indent_sexp!(pp)
        field1234 = unwrapped_fields1233[1]
        if !isempty(field1234)
            newline(pp)
            for (i1721, elem1235) in enumerate(field1234)
                i1236 = i1721 - 1
                if (i1236 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1235)
            end
        end
        newline(pp)
        field1237 = unwrapped_fields1233[2]
        pretty_script(pp, field1237)
        field1238 = unwrapped_fields1233[3]
        if !isnothing(field1238)
            newline(pp)
            opt_val1239 = field1238
            pretty_attrs(pp, opt_val1239)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_script(pp::PrettyPrinter, msg::Proto.Script)
    flat1245 = try_flat(pp, msg, pretty_script)
    if !isnothing(flat1245)
        write(pp, flat1245)
        return nothing
    else
        _dollar_dollar = msg
        fields1241 = _dollar_dollar.constructs
        unwrapped_fields1242 = fields1241
        write(pp, "(script")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1242)
            newline(pp)
            for (i1722, elem1243) in enumerate(unwrapped_fields1242)
                i1244 = i1722 - 1
                if (i1244 > 0)
                    newline(pp)
                end
                pretty_construct(pp, elem1243)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_construct(pp::PrettyPrinter, msg::Proto.Construct)
    flat1250 = try_flat(pp, msg, pretty_construct)
    if !isnothing(flat1250)
        write(pp, flat1250)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("loop"))
            _t1723 = _get_oneof_field(_dollar_dollar, :loop)
        else
            _t1723 = nothing
        end
        deconstruct_result1248 = _t1723
        if !isnothing(deconstruct_result1248)
            unwrapped1249 = deconstruct_result1248
            pretty_loop(pp, unwrapped1249)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("instruction"))
                _t1724 = _get_oneof_field(_dollar_dollar, :instruction)
            else
                _t1724 = nothing
            end
            deconstruct_result1246 = _t1724
            if !isnothing(deconstruct_result1246)
                unwrapped1247 = deconstruct_result1246
                pretty_instruction(pp, unwrapped1247)
            else
                throw(ParseError("No matching rule for construct"))
            end
        end
    end
    return nothing
end

function pretty_loop(pp::PrettyPrinter, msg::Proto.Loop)
    flat1257 = try_flat(pp, msg, pretty_loop)
    if !isnothing(flat1257)
        write(pp, flat1257)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1725 = _dollar_dollar.attrs
        else
            _t1725 = nothing
        end
        fields1251 = (_dollar_dollar.init, _dollar_dollar.body, _t1725,)
        unwrapped_fields1252 = fields1251
        write(pp, "(loop")
        indent_sexp!(pp)
        newline(pp)
        field1253 = unwrapped_fields1252[1]
        pretty_init(pp, field1253)
        newline(pp)
        field1254 = unwrapped_fields1252[2]
        pretty_script(pp, field1254)
        field1255 = unwrapped_fields1252[3]
        if !isnothing(field1255)
            newline(pp)
            opt_val1256 = field1255
            pretty_attrs(pp, opt_val1256)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_init(pp::PrettyPrinter, msg::Vector{Proto.Instruction})
    flat1261 = try_flat(pp, msg, pretty_init)
    if !isnothing(flat1261)
        write(pp, flat1261)
        return nothing
    else
        fields1258 = msg
        write(pp, "(init")
        indent_sexp!(pp)
        if !isempty(fields1258)
            newline(pp)
            for (i1726, elem1259) in enumerate(fields1258)
                i1260 = i1726 - 1
                if (i1260 > 0)
                    newline(pp)
                end
                pretty_instruction(pp, elem1259)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_instruction(pp::PrettyPrinter, msg::Proto.Instruction)
    flat1272 = try_flat(pp, msg, pretty_instruction)
    if !isnothing(flat1272)
        write(pp, flat1272)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("assign"))
            _t1727 = _get_oneof_field(_dollar_dollar, :assign)
        else
            _t1727 = nothing
        end
        deconstruct_result1270 = _t1727
        if !isnothing(deconstruct_result1270)
            unwrapped1271 = deconstruct_result1270
            pretty_assign(pp, unwrapped1271)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("upsert"))
                _t1728 = _get_oneof_field(_dollar_dollar, :upsert)
            else
                _t1728 = nothing
            end
            deconstruct_result1268 = _t1728
            if !isnothing(deconstruct_result1268)
                unwrapped1269 = deconstruct_result1268
                pretty_upsert(pp, unwrapped1269)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("#break"))
                    _t1729 = _get_oneof_field(_dollar_dollar, :var"#break")
                else
                    _t1729 = nothing
                end
                deconstruct_result1266 = _t1729
                if !isnothing(deconstruct_result1266)
                    unwrapped1267 = deconstruct_result1266
                    pretty_break(pp, unwrapped1267)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("monoid_def"))
                        _t1730 = _get_oneof_field(_dollar_dollar, :monoid_def)
                    else
                        _t1730 = nothing
                    end
                    deconstruct_result1264 = _t1730
                    if !isnothing(deconstruct_result1264)
                        unwrapped1265 = deconstruct_result1264
                        pretty_monoid_def(pp, unwrapped1265)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("monus_def"))
                            _t1731 = _get_oneof_field(_dollar_dollar, :monus_def)
                        else
                            _t1731 = nothing
                        end
                        deconstruct_result1262 = _t1731
                        if !isnothing(deconstruct_result1262)
                            unwrapped1263 = deconstruct_result1262
                            pretty_monus_def(pp, unwrapped1263)
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
    flat1279 = try_flat(pp, msg, pretty_assign)
    if !isnothing(flat1279)
        write(pp, flat1279)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1732 = _dollar_dollar.attrs
        else
            _t1732 = nothing
        end
        fields1273 = (_dollar_dollar.name, _dollar_dollar.body, _t1732,)
        unwrapped_fields1274 = fields1273
        write(pp, "(assign")
        indent_sexp!(pp)
        newline(pp)
        field1275 = unwrapped_fields1274[1]
        pretty_relation_id(pp, field1275)
        newline(pp)
        field1276 = unwrapped_fields1274[2]
        pretty_abstraction(pp, field1276)
        field1277 = unwrapped_fields1274[3]
        if !isnothing(field1277)
            newline(pp)
            opt_val1278 = field1277
            pretty_attrs(pp, opt_val1278)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_upsert(pp::PrettyPrinter, msg::Proto.Upsert)
    flat1286 = try_flat(pp, msg, pretty_upsert)
    if !isnothing(flat1286)
        write(pp, flat1286)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1733 = _dollar_dollar.attrs
        else
            _t1733 = nothing
        end
        fields1280 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1733,)
        unwrapped_fields1281 = fields1280
        write(pp, "(upsert")
        indent_sexp!(pp)
        newline(pp)
        field1282 = unwrapped_fields1281[1]
        pretty_relation_id(pp, field1282)
        newline(pp)
        field1283 = unwrapped_fields1281[2]
        pretty_abstraction_with_arity(pp, field1283)
        field1284 = unwrapped_fields1281[3]
        if !isnothing(field1284)
            newline(pp)
            opt_val1285 = field1284
            pretty_attrs(pp, opt_val1285)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abstraction_with_arity(pp::PrettyPrinter, msg::Tuple{Proto.Abstraction, Int64})
    flat1291 = try_flat(pp, msg, pretty_abstraction_with_arity)
    if !isnothing(flat1291)
        write(pp, flat1291)
        return nothing
    else
        _dollar_dollar = msg
        _t1734 = deconstruct_bindings_with_arity(pp, _dollar_dollar[1], _dollar_dollar[2])
        fields1287 = (_t1734, _dollar_dollar[1].value,)
        unwrapped_fields1288 = fields1287
        write(pp, "(")
        indent!(pp)
        field1289 = unwrapped_fields1288[1]
        pretty_bindings(pp, field1289)
        newline(pp)
        field1290 = unwrapped_fields1288[2]
        pretty_formula(pp, field1290)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_break(pp::PrettyPrinter, msg::Proto.Break)
    flat1298 = try_flat(pp, msg, pretty_break)
    if !isnothing(flat1298)
        write(pp, flat1298)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1735 = _dollar_dollar.attrs
        else
            _t1735 = nothing
        end
        fields1292 = (_dollar_dollar.name, _dollar_dollar.body, _t1735,)
        unwrapped_fields1293 = fields1292
        write(pp, "(break")
        indent_sexp!(pp)
        newline(pp)
        field1294 = unwrapped_fields1293[1]
        pretty_relation_id(pp, field1294)
        newline(pp)
        field1295 = unwrapped_fields1293[2]
        pretty_abstraction(pp, field1295)
        field1296 = unwrapped_fields1293[3]
        if !isnothing(field1296)
            newline(pp)
            opt_val1297 = field1296
            pretty_attrs(pp, opt_val1297)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid_def(pp::PrettyPrinter, msg::Proto.MonoidDef)
    flat1306 = try_flat(pp, msg, pretty_monoid_def)
    if !isnothing(flat1306)
        write(pp, flat1306)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1736 = _dollar_dollar.attrs
        else
            _t1736 = nothing
        end
        fields1299 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1736,)
        unwrapped_fields1300 = fields1299
        write(pp, "(monoid")
        indent_sexp!(pp)
        newline(pp)
        field1301 = unwrapped_fields1300[1]
        pretty_monoid(pp, field1301)
        newline(pp)
        field1302 = unwrapped_fields1300[2]
        pretty_relation_id(pp, field1302)
        newline(pp)
        field1303 = unwrapped_fields1300[3]
        pretty_abstraction_with_arity(pp, field1303)
        field1304 = unwrapped_fields1300[4]
        if !isnothing(field1304)
            newline(pp)
            opt_val1305 = field1304
            pretty_attrs(pp, opt_val1305)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monoid(pp::PrettyPrinter, msg::Proto.Monoid)
    flat1315 = try_flat(pp, msg, pretty_monoid)
    if !isnothing(flat1315)
        write(pp, flat1315)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("or_monoid"))
            _t1737 = _get_oneof_field(_dollar_dollar, :or_monoid)
        else
            _t1737 = nothing
        end
        deconstruct_result1313 = _t1737
        if !isnothing(deconstruct_result1313)
            unwrapped1314 = deconstruct_result1313
            pretty_or_monoid(pp, unwrapped1314)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("min_monoid"))
                _t1738 = _get_oneof_field(_dollar_dollar, :min_monoid)
            else
                _t1738 = nothing
            end
            deconstruct_result1311 = _t1738
            if !isnothing(deconstruct_result1311)
                unwrapped1312 = deconstruct_result1311
                pretty_min_monoid(pp, unwrapped1312)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("max_monoid"))
                    _t1739 = _get_oneof_field(_dollar_dollar, :max_monoid)
                else
                    _t1739 = nothing
                end
                deconstruct_result1309 = _t1739
                if !isnothing(deconstruct_result1309)
                    unwrapped1310 = deconstruct_result1309
                    pretty_max_monoid(pp, unwrapped1310)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("sum_monoid"))
                        _t1740 = _get_oneof_field(_dollar_dollar, :sum_monoid)
                    else
                        _t1740 = nothing
                    end
                    deconstruct_result1307 = _t1740
                    if !isnothing(deconstruct_result1307)
                        unwrapped1308 = deconstruct_result1307
                        pretty_sum_monoid(pp, unwrapped1308)
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
    fields1316 = msg
    write(pp, "(or)")
    return nothing
end

function pretty_min_monoid(pp::PrettyPrinter, msg::Proto.MinMonoid)
    flat1319 = try_flat(pp, msg, pretty_min_monoid)
    if !isnothing(flat1319)
        write(pp, flat1319)
        return nothing
    else
        _dollar_dollar = msg
        fields1317 = _dollar_dollar.var"#type"
        unwrapped_fields1318 = fields1317
        write(pp, "(min")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1318)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_max_monoid(pp::PrettyPrinter, msg::Proto.MaxMonoid)
    flat1322 = try_flat(pp, msg, pretty_max_monoid)
    if !isnothing(flat1322)
        write(pp, flat1322)
        return nothing
    else
        _dollar_dollar = msg
        fields1320 = _dollar_dollar.var"#type"
        unwrapped_fields1321 = fields1320
        write(pp, "(max")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1321)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_sum_monoid(pp::PrettyPrinter, msg::Proto.SumMonoid)
    flat1325 = try_flat(pp, msg, pretty_sum_monoid)
    if !isnothing(flat1325)
        write(pp, flat1325)
        return nothing
    else
        _dollar_dollar = msg
        fields1323 = _dollar_dollar.var"#type"
        unwrapped_fields1324 = fields1323
        write(pp, "(sum")
        indent_sexp!(pp)
        newline(pp)
        pretty_type(pp, unwrapped_fields1324)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_monus_def(pp::PrettyPrinter, msg::Proto.MonusDef)
    flat1333 = try_flat(pp, msg, pretty_monus_def)
    if !isnothing(flat1333)
        write(pp, flat1333)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.attrs)
            _t1741 = _dollar_dollar.attrs
        else
            _t1741 = nothing
        end
        fields1326 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1741,)
        unwrapped_fields1327 = fields1326
        write(pp, "(monus")
        indent_sexp!(pp)
        newline(pp)
        field1328 = unwrapped_fields1327[1]
        pretty_monoid(pp, field1328)
        newline(pp)
        field1329 = unwrapped_fields1327[2]
        pretty_relation_id(pp, field1329)
        newline(pp)
        field1330 = unwrapped_fields1327[3]
        pretty_abstraction_with_arity(pp, field1330)
        field1331 = unwrapped_fields1327[4]
        if !isnothing(field1331)
            newline(pp)
            opt_val1332 = field1331
            pretty_attrs(pp, opt_val1332)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_constraint(pp::PrettyPrinter, msg::Proto.Constraint)
    flat1340 = try_flat(pp, msg, pretty_constraint)
    if !isnothing(flat1340)
        write(pp, flat1340)
        return nothing
    else
        _dollar_dollar = msg
        fields1334 = (_dollar_dollar.name, _get_oneof_field(_dollar_dollar, :functional_dependency).guard, _get_oneof_field(_dollar_dollar, :functional_dependency).keys, _get_oneof_field(_dollar_dollar, :functional_dependency).values,)
        unwrapped_fields1335 = fields1334
        write(pp, "(functional_dependency")
        indent_sexp!(pp)
        newline(pp)
        field1336 = unwrapped_fields1335[1]
        pretty_relation_id(pp, field1336)
        newline(pp)
        field1337 = unwrapped_fields1335[2]
        pretty_abstraction(pp, field1337)
        newline(pp)
        field1338 = unwrapped_fields1335[3]
        pretty_functional_dependency_keys(pp, field1338)
        newline(pp)
        field1339 = unwrapped_fields1335[4]
        pretty_functional_dependency_values(pp, field1339)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_keys(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1344 = try_flat(pp, msg, pretty_functional_dependency_keys)
    if !isnothing(flat1344)
        write(pp, flat1344)
        return nothing
    else
        fields1341 = msg
        write(pp, "(keys")
        indent_sexp!(pp)
        if !isempty(fields1341)
            newline(pp)
            for (i1742, elem1342) in enumerate(fields1341)
                i1343 = i1742 - 1
                if (i1343 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1342)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_functional_dependency_values(pp::PrettyPrinter, msg::Vector{Proto.Var})
    flat1348 = try_flat(pp, msg, pretty_functional_dependency_values)
    if !isnothing(flat1348)
        write(pp, flat1348)
        return nothing
    else
        fields1345 = msg
        write(pp, "(values")
        indent_sexp!(pp)
        if !isempty(fields1345)
            newline(pp)
            for (i1743, elem1346) in enumerate(fields1345)
                i1347 = i1743 - 1
                if (i1347 > 0)
                    newline(pp)
                end
                pretty_var(pp, elem1346)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_data(pp::PrettyPrinter, msg::Proto.Data)
    flat1357 = try_flat(pp, msg, pretty_data)
    if !isnothing(flat1357)
        write(pp, flat1357)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("edb"))
            _t1744 = _get_oneof_field(_dollar_dollar, :edb)
        else
            _t1744 = nothing
        end
        deconstruct_result1355 = _t1744
        if !isnothing(deconstruct_result1355)
            unwrapped1356 = deconstruct_result1355
            pretty_edb(pp, unwrapped1356)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("betree_relation"))
                _t1745 = _get_oneof_field(_dollar_dollar, :betree_relation)
            else
                _t1745 = nothing
            end
            deconstruct_result1353 = _t1745
            if !isnothing(deconstruct_result1353)
                unwrapped1354 = deconstruct_result1353
                pretty_betree_relation(pp, unwrapped1354)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("csv_data"))
                    _t1746 = _get_oneof_field(_dollar_dollar, :csv_data)
                else
                    _t1746 = nothing
                end
                deconstruct_result1351 = _t1746
                if !isnothing(deconstruct_result1351)
                    unwrapped1352 = deconstruct_result1351
                    pretty_csv_data(pp, unwrapped1352)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("iceberg_data"))
                        _t1747 = _get_oneof_field(_dollar_dollar, :iceberg_data)
                    else
                        _t1747 = nothing
                    end
                    deconstruct_result1349 = _t1747
                    if !isnothing(deconstruct_result1349)
                        unwrapped1350 = deconstruct_result1349
                        pretty_iceberg_data(pp, unwrapped1350)
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
    flat1363 = try_flat(pp, msg, pretty_edb)
    if !isnothing(flat1363)
        write(pp, flat1363)
        return nothing
    else
        _dollar_dollar = msg
        fields1358 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        unwrapped_fields1359 = fields1358
        write(pp, "(edb")
        indent_sexp!(pp)
        newline(pp)
        field1360 = unwrapped_fields1359[1]
        pretty_relation_id(pp, field1360)
        newline(pp)
        field1361 = unwrapped_fields1359[2]
        pretty_edb_path(pp, field1361)
        newline(pp)
        field1362 = unwrapped_fields1359[3]
        pretty_edb_types(pp, field1362)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_edb_path(pp::PrettyPrinter, msg::Vector{String})
    flat1367 = try_flat(pp, msg, pretty_edb_path)
    if !isnothing(flat1367)
        write(pp, flat1367)
        return nothing
    else
        fields1364 = msg
        write(pp, "[")
        indent!(pp)
        for (i1748, elem1365) in enumerate(fields1364)
            i1366 = i1748 - 1
            if (i1366 > 0)
                newline(pp)
            end
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1365))
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_edb_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1371 = try_flat(pp, msg, pretty_edb_types)
    if !isnothing(flat1371)
        write(pp, flat1371)
        return nothing
    else
        fields1368 = msg
        write(pp, "[")
        indent!(pp)
        for (i1749, elem1369) in enumerate(fields1368)
            i1370 = i1749 - 1
            if (i1370 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1369)
        end
        dedent!(pp)
        write(pp, "]")
    end
    return nothing
end

function pretty_betree_relation(pp::PrettyPrinter, msg::Proto.BeTreeRelation)
    flat1376 = try_flat(pp, msg, pretty_betree_relation)
    if !isnothing(flat1376)
        write(pp, flat1376)
        return nothing
    else
        _dollar_dollar = msg
        fields1372 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
        unwrapped_fields1373 = fields1372
        write(pp, "(betree_relation")
        indent_sexp!(pp)
        newline(pp)
        field1374 = unwrapped_fields1373[1]
        pretty_relation_id(pp, field1374)
        newline(pp)
        field1375 = unwrapped_fields1373[2]
        pretty_betree_info(pp, field1375)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info(pp::PrettyPrinter, msg::Proto.BeTreeInfo)
    flat1382 = try_flat(pp, msg, pretty_betree_info)
    if !isnothing(flat1382)
        write(pp, flat1382)
        return nothing
    else
        _dollar_dollar = msg
        _t1750 = deconstruct_betree_info_config(pp, _dollar_dollar)
        fields1377 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1750,)
        unwrapped_fields1378 = fields1377
        write(pp, "(betree_info")
        indent_sexp!(pp)
        newline(pp)
        field1379 = unwrapped_fields1378[1]
        pretty_betree_info_key_types(pp, field1379)
        newline(pp)
        field1380 = unwrapped_fields1378[2]
        pretty_betree_info_value_types(pp, field1380)
        newline(pp)
        field1381 = unwrapped_fields1378[3]
        pretty_config_dict(pp, field1381)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_key_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1386 = try_flat(pp, msg, pretty_betree_info_key_types)
    if !isnothing(flat1386)
        write(pp, flat1386)
        return nothing
    else
        fields1383 = msg
        write(pp, "(key_types")
        indent_sexp!(pp)
        if !isempty(fields1383)
            newline(pp)
            for (i1751, elem1384) in enumerate(fields1383)
                i1385 = i1751 - 1
                if (i1385 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1384)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_betree_info_value_types(pp::PrettyPrinter, msg::Vector{Proto.var"#Type"})
    flat1390 = try_flat(pp, msg, pretty_betree_info_value_types)
    if !isnothing(flat1390)
        write(pp, flat1390)
        return nothing
    else
        fields1387 = msg
        write(pp, "(value_types")
        indent_sexp!(pp)
        if !isempty(fields1387)
            newline(pp)
            for (i1752, elem1388) in enumerate(fields1387)
                i1389 = i1752 - 1
                if (i1389 > 0)
                    newline(pp)
                end
                pretty_type(pp, elem1388)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_data(pp::PrettyPrinter, msg::Proto.CSVData)
    flat1397 = try_flat(pp, msg, pretty_csv_data)
    if !isnothing(flat1397)
        write(pp, flat1397)
        return nothing
    else
        _dollar_dollar = msg
        fields1391 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        unwrapped_fields1392 = fields1391
        write(pp, "(csv_data")
        indent_sexp!(pp)
        newline(pp)
        field1393 = unwrapped_fields1392[1]
        pretty_csvlocator(pp, field1393)
        newline(pp)
        field1394 = unwrapped_fields1392[2]
        pretty_csv_config(pp, field1394)
        newline(pp)
        field1395 = unwrapped_fields1392[3]
        pretty_gnf_columns(pp, field1395)
        newline(pp)
        field1396 = unwrapped_fields1392[4]
        pretty_csv_asof(pp, field1396)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csvlocator(pp::PrettyPrinter, msg::Proto.CSVLocator)
    flat1404 = try_flat(pp, msg, pretty_csvlocator)
    if !isnothing(flat1404)
        write(pp, flat1404)
        return nothing
    else
        _dollar_dollar = msg
        if !isempty(_dollar_dollar.paths)
            _t1753 = _dollar_dollar.paths
        else
            _t1753 = nothing
        end
        if String(copy(_dollar_dollar.inline_data)) != ""
            _t1754 = String(copy(_dollar_dollar.inline_data))
        else
            _t1754 = nothing
        end
        fields1398 = (_t1753, _t1754,)
        unwrapped_fields1399 = fields1398
        write(pp, "(csv_locator")
        indent_sexp!(pp)
        field1400 = unwrapped_fields1399[1]
        if !isnothing(field1400)
            newline(pp)
            opt_val1401 = field1400
            pretty_csv_locator_paths(pp, opt_val1401)
        end
        field1402 = unwrapped_fields1399[2]
        if !isnothing(field1402)
            newline(pp)
            opt_val1403 = field1402
            pretty_csv_locator_inline_data(pp, opt_val1403)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_paths(pp::PrettyPrinter, msg::Vector{String})
    flat1408 = try_flat(pp, msg, pretty_csv_locator_paths)
    if !isnothing(flat1408)
        write(pp, flat1408)
        return nothing
    else
        fields1405 = msg
        write(pp, "(paths")
        indent_sexp!(pp)
        if !isempty(fields1405)
            newline(pp)
            for (i1755, elem1406) in enumerate(fields1405)
                i1407 = i1755 - 1
                if (i1407 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1406))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_locator_inline_data(pp::PrettyPrinter, msg::String)
    flat1410 = try_flat(pp, msg, pretty_csv_locator_inline_data)
    if !isnothing(flat1410)
        write(pp, flat1410)
        return nothing
    else
        fields1409 = msg
        write(pp, "(inline_data")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1409))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_csv_config(pp::PrettyPrinter, msg::Proto.CSVConfig)
    flat1413 = try_flat(pp, msg, pretty_csv_config)
    if !isnothing(flat1413)
        write(pp, flat1413)
        return nothing
    else
        _dollar_dollar = msg
        _t1756 = deconstruct_csv_config(pp, _dollar_dollar)
        fields1411 = _t1756
        unwrapped_fields1412 = fields1411
        write(pp, "(csv_config")
        indent_sexp!(pp)
        newline(pp)
        pretty_config_dict(pp, unwrapped_fields1412)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_columns(pp::PrettyPrinter, msg::Vector{Proto.GNFColumn})
    flat1417 = try_flat(pp, msg, pretty_gnf_columns)
    if !isnothing(flat1417)
        write(pp, flat1417)
        return nothing
    else
        fields1414 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1414)
            newline(pp)
            for (i1757, elem1415) in enumerate(fields1414)
                i1416 = i1757 - 1
                if (i1416 > 0)
                    newline(pp)
                end
                pretty_gnf_column(pp, elem1415)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column(pp::PrettyPrinter, msg::Proto.GNFColumn)
    flat1426 = try_flat(pp, msg, pretty_gnf_column)
    if !isnothing(flat1426)
        write(pp, flat1426)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("target_id"))
            _t1758 = _dollar_dollar.target_id
        else
            _t1758 = nothing
        end
        fields1418 = (_dollar_dollar.column_path, _t1758, _dollar_dollar.types,)
        unwrapped_fields1419 = fields1418
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1420 = unwrapped_fields1419[1]
        pretty_gnf_column_path(pp, field1420)
        field1421 = unwrapped_fields1419[2]
        if !isnothing(field1421)
            newline(pp)
            opt_val1422 = field1421
            pretty_relation_id(pp, opt_val1422)
        end
        newline(pp)
        write(pp, "[")
        field1423 = unwrapped_fields1419[3]
        for (i1759, elem1424) in enumerate(field1423)
            i1425 = i1759 - 1
            if (i1425 > 0)
                newline(pp)
            end
            pretty_type(pp, elem1424)
        end
        write(pp, "]")
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_gnf_column_path(pp::PrettyPrinter, msg::Vector{String})
    flat1433 = try_flat(pp, msg, pretty_gnf_column_path)
    if !isnothing(flat1433)
        write(pp, flat1433)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar) == 1
            _t1760 = _dollar_dollar[1]
        else
            _t1760 = nothing
        end
        deconstruct_result1431 = _t1760
        if !isnothing(deconstruct_result1431)
            unwrapped1432 = deconstruct_result1431
            write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, unwrapped1432))
        else
            _dollar_dollar = msg
            if length(_dollar_dollar) != 1
                _t1761 = _dollar_dollar
            else
                _t1761 = nothing
            end
            deconstruct_result1427 = _t1761
            if !isnothing(deconstruct_result1427)
                unwrapped1428 = deconstruct_result1427
                write(pp, "[")
                indent!(pp)
                for (i1762, elem1429) in enumerate(unwrapped1428)
                    i1430 = i1762 - 1
                    if (i1430 > 0)
                        newline(pp)
                    end
                    write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1429))
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
    flat1435 = try_flat(pp, msg, pretty_csv_asof)
    if !isnothing(flat1435)
        write(pp, flat1435)
        return nothing
    else
        fields1434 = msg
        write(pp, "(asof")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1434))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_data(pp::PrettyPrinter, msg::Proto.IcebergData)
    flat1446 = try_flat(pp, msg, pretty_iceberg_data)
    if !isnothing(flat1446)
        write(pp, flat1446)
        return nothing
    else
        _dollar_dollar = msg
        _t1763 = deconstruct_iceberg_data_from_snapshot_optional(pp, _dollar_dollar)
        _t1764 = deconstruct_iceberg_data_to_snapshot_optional(pp, _dollar_dollar)
        fields1436 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1763, _t1764, _dollar_dollar.returns_delta,)
        unwrapped_fields1437 = fields1436
        write(pp, "(iceberg_data")
        indent_sexp!(pp)
        newline(pp)
        field1438 = unwrapped_fields1437[1]
        pretty_iceberg_locator(pp, field1438)
        newline(pp)
        field1439 = unwrapped_fields1437[2]
        pretty_iceberg_catalog_config(pp, field1439)
        newline(pp)
        field1440 = unwrapped_fields1437[3]
        pretty_gnf_columns(pp, field1440)
        field1441 = unwrapped_fields1437[4]
        if !isnothing(field1441)
            newline(pp)
            opt_val1442 = field1441
            pretty_iceberg_from_snapshot(pp, opt_val1442)
        end
        field1443 = unwrapped_fields1437[5]
        if !isnothing(field1443)
            newline(pp)
            opt_val1444 = field1443
            pretty_iceberg_to_snapshot(pp, opt_val1444)
        end
        newline(pp)
        field1445 = unwrapped_fields1437[6]
        pretty_boolean_value(pp, field1445)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator(pp::PrettyPrinter, msg::Proto.IcebergLocator)
    flat1452 = try_flat(pp, msg, pretty_iceberg_locator)
    if !isnothing(flat1452)
        write(pp, flat1452)
        return nothing
    else
        _dollar_dollar = msg
        fields1447 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
        unwrapped_fields1448 = fields1447
        write(pp, "(iceberg_locator")
        indent_sexp!(pp)
        newline(pp)
        field1449 = unwrapped_fields1448[1]
        pretty_iceberg_locator_table_name(pp, field1449)
        newline(pp)
        field1450 = unwrapped_fields1448[2]
        pretty_iceberg_locator_namespace(pp, field1450)
        newline(pp)
        field1451 = unwrapped_fields1448[3]
        pretty_iceberg_locator_warehouse(pp, field1451)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_table_name(pp::PrettyPrinter, msg::String)
    flat1454 = try_flat(pp, msg, pretty_iceberg_locator_table_name)
    if !isnothing(flat1454)
        write(pp, flat1454)
        return nothing
    else
        fields1453 = msg
        write(pp, "(table_name")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1453))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_namespace(pp::PrettyPrinter, msg::Vector{String})
    flat1458 = try_flat(pp, msg, pretty_iceberg_locator_namespace)
    if !isnothing(flat1458)
        write(pp, flat1458)
        return nothing
    else
        fields1455 = msg
        write(pp, "(namespace")
        indent_sexp!(pp)
        if !isempty(fields1455)
            newline(pp)
            for (i1765, elem1456) in enumerate(fields1455)
                i1457 = i1765 - 1
                if (i1457 > 0)
                    newline(pp)
                end
                write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, elem1456))
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_locator_warehouse(pp::PrettyPrinter, msg::String)
    flat1460 = try_flat(pp, msg, pretty_iceberg_locator_warehouse)
    if !isnothing(flat1460)
        write(pp, flat1460)
        return nothing
    else
        fields1459 = msg
        write(pp, "(warehouse")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1459))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config(pp::PrettyPrinter, msg::Proto.IcebergCatalogConfig)
    flat1468 = try_flat(pp, msg, pretty_iceberg_catalog_config)
    if !isnothing(flat1468)
        write(pp, flat1468)
        return nothing
    else
        _dollar_dollar = msg
        _t1766 = deconstruct_iceberg_catalog_config_scope_optional(pp, _dollar_dollar)
        fields1461 = (_dollar_dollar.catalog_uri, _t1766, sort([(k, v) for (k, v) in _dollar_dollar.properties]), sort([(k, v) for (k, v) in _dollar_dollar.auth_properties]),)
        unwrapped_fields1462 = fields1461
        write(pp, "(iceberg_catalog_config")
        indent_sexp!(pp)
        newline(pp)
        field1463 = unwrapped_fields1462[1]
        pretty_iceberg_catalog_uri(pp, field1463)
        field1464 = unwrapped_fields1462[2]
        if !isnothing(field1464)
            newline(pp)
            opt_val1465 = field1464
            pretty_iceberg_catalog_config_scope(pp, opt_val1465)
        end
        newline(pp)
        field1466 = unwrapped_fields1462[3]
        pretty_iceberg_properties(pp, field1466)
        newline(pp)
        field1467 = unwrapped_fields1462[4]
        pretty_iceberg_auth_properties(pp, field1467)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_uri(pp::PrettyPrinter, msg::String)
    flat1470 = try_flat(pp, msg, pretty_iceberg_catalog_uri)
    if !isnothing(flat1470)
        write(pp, flat1470)
        return nothing
    else
        fields1469 = msg
        write(pp, "(catalog_uri")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1469))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_catalog_config_scope(pp::PrettyPrinter, msg::String)
    flat1472 = try_flat(pp, msg, pretty_iceberg_catalog_config_scope)
    if !isnothing(flat1472)
        write(pp, flat1472)
        return nothing
    else
        fields1471 = msg
        write(pp, "(scope")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1471))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1476 = try_flat(pp, msg, pretty_iceberg_properties)
    if !isnothing(flat1476)
        write(pp, flat1476)
        return nothing
    else
        fields1473 = msg
        write(pp, "(properties")
        indent_sexp!(pp)
        if !isempty(fields1473)
            newline(pp)
            for (i1767, elem1474) in enumerate(fields1473)
                i1475 = i1767 - 1
                if (i1475 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1474)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1481 = try_flat(pp, msg, pretty_iceberg_property_entry)
    if !isnothing(flat1481)
        write(pp, flat1481)
        return nothing
    else
        _dollar_dollar = msg
        fields1477 = (_dollar_dollar[1], _dollar_dollar[2],)
        unwrapped_fields1478 = fields1477
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1479 = unwrapped_fields1478[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1479))
        newline(pp)
        field1480 = unwrapped_fields1478[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1480))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_auth_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1485 = try_flat(pp, msg, pretty_iceberg_auth_properties)
    if !isnothing(flat1485)
        write(pp, flat1485)
        return nothing
    else
        fields1482 = msg
        write(pp, "(auth_properties")
        indent_sexp!(pp)
        if !isempty(fields1482)
            newline(pp)
            for (i1768, elem1483) in enumerate(fields1482)
                i1484 = i1768 - 1
                if (i1484 > 0)
                    newline(pp)
                end
                pretty_iceberg_masked_property_entry(pp, elem1483)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_masked_property_entry(pp::PrettyPrinter, msg::Tuple{String, String})
    flat1490 = try_flat(pp, msg, pretty_iceberg_masked_property_entry)
    if !isnothing(flat1490)
        write(pp, flat1490)
        return nothing
    else
        _dollar_dollar = msg
        _t1769 = mask_secret_value(pp, _dollar_dollar)
        fields1486 = (_dollar_dollar[1], _t1769,)
        unwrapped_fields1487 = fields1486
        write(pp, "(prop")
        indent_sexp!(pp)
        newline(pp)
        field1488 = unwrapped_fields1487[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1488))
        newline(pp)
        field1489 = unwrapped_fields1487[2]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1489))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_from_snapshot(pp::PrettyPrinter, msg::String)
    flat1492 = try_flat(pp, msg, pretty_iceberg_from_snapshot)
    if !isnothing(flat1492)
        write(pp, flat1492)
        return nothing
    else
        fields1491 = msg
        write(pp, "(from_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1491))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_to_snapshot(pp::PrettyPrinter, msg::String)
    flat1494 = try_flat(pp, msg, pretty_iceberg_to_snapshot)
    if !isnothing(flat1494)
        write(pp, flat1494)
        return nothing
    else
        fields1493 = msg
        write(pp, "(to_snapshot")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1493))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_undefine(pp::PrettyPrinter, msg::Proto.Undefine)
    flat1497 = try_flat(pp, msg, pretty_undefine)
    if !isnothing(flat1497)
        write(pp, flat1497)
        return nothing
    else
        _dollar_dollar = msg
        fields1495 = _dollar_dollar.fragment_id
        unwrapped_fields1496 = fields1495
        write(pp, "(undefine")
        indent_sexp!(pp)
        newline(pp)
        pretty_fragment_id(pp, unwrapped_fields1496)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_context(pp::PrettyPrinter, msg::Proto.Context)
    flat1502 = try_flat(pp, msg, pretty_context)
    if !isnothing(flat1502)
        write(pp, flat1502)
        return nothing
    else
        _dollar_dollar = msg
        fields1498 = _dollar_dollar.relations
        unwrapped_fields1499 = fields1498
        write(pp, "(context")
        indent_sexp!(pp)
        if !isempty(unwrapped_fields1499)
            newline(pp)
            for (i1770, elem1500) in enumerate(unwrapped_fields1499)
                i1501 = i1770 - 1
                if (i1501 > 0)
                    newline(pp)
                end
                pretty_relation_id(pp, elem1500)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot(pp::PrettyPrinter, msg::Proto.Snapshot)
    flat1509 = try_flat(pp, msg, pretty_snapshot)
    if !isnothing(flat1509)
        write(pp, flat1509)
        return nothing
    else
        _dollar_dollar = msg
        fields1503 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
        unwrapped_fields1504 = fields1503
        write(pp, "(snapshot")
        indent_sexp!(pp)
        newline(pp)
        field1505 = unwrapped_fields1504[1]
        pretty_edb_path(pp, field1505)
        field1506 = unwrapped_fields1504[2]
        if !isempty(field1506)
            newline(pp)
            for (i1771, elem1507) in enumerate(field1506)
                i1508 = i1771 - 1
                if (i1508 > 0)
                    newline(pp)
                end
                pretty_snapshot_mapping(pp, elem1507)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_snapshot_mapping(pp::PrettyPrinter, msg::Proto.SnapshotMapping)
    flat1514 = try_flat(pp, msg, pretty_snapshot_mapping)
    if !isnothing(flat1514)
        write(pp, flat1514)
        return nothing
    else
        _dollar_dollar = msg
        fields1510 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        unwrapped_fields1511 = fields1510
        field1512 = unwrapped_fields1511[1]
        pretty_edb_path(pp, field1512)
        write(pp, " ")
        field1513 = unwrapped_fields1511[2]
        pretty_relation_id(pp, field1513)
    end
    return nothing
end

function pretty_epoch_reads(pp::PrettyPrinter, msg::Vector{Proto.Read})
    flat1518 = try_flat(pp, msg, pretty_epoch_reads)
    if !isnothing(flat1518)
        write(pp, flat1518)
        return nothing
    else
        fields1515 = msg
        write(pp, "(reads")
        indent_sexp!(pp)
        if !isempty(fields1515)
            newline(pp)
            for (i1772, elem1516) in enumerate(fields1515)
                i1517 = i1772 - 1
                if (i1517 > 0)
                    newline(pp)
                end
                pretty_read(pp, elem1516)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_read(pp::PrettyPrinter, msg::Proto.Read)
    flat1529 = try_flat(pp, msg, pretty_read)
    if !isnothing(flat1529)
        write(pp, flat1529)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("demand"))
            _t1773 = _get_oneof_field(_dollar_dollar, :demand)
        else
            _t1773 = nothing
        end
        deconstruct_result1527 = _t1773
        if !isnothing(deconstruct_result1527)
            unwrapped1528 = deconstruct_result1527
            pretty_demand(pp, unwrapped1528)
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("output"))
                _t1774 = _get_oneof_field(_dollar_dollar, :output)
            else
                _t1774 = nothing
            end
            deconstruct_result1525 = _t1774
            if !isnothing(deconstruct_result1525)
                unwrapped1526 = deconstruct_result1525
                pretty_output(pp, unwrapped1526)
            else
                _dollar_dollar = msg
                if _has_proto_field(_dollar_dollar, Symbol("what_if"))
                    _t1775 = _get_oneof_field(_dollar_dollar, :what_if)
                else
                    _t1775 = nothing
                end
                deconstruct_result1523 = _t1775
                if !isnothing(deconstruct_result1523)
                    unwrapped1524 = deconstruct_result1523
                    pretty_what_if(pp, unwrapped1524)
                else
                    _dollar_dollar = msg
                    if _has_proto_field(_dollar_dollar, Symbol("abort"))
                        _t1776 = _get_oneof_field(_dollar_dollar, :abort)
                    else
                        _t1776 = nothing
                    end
                    deconstruct_result1521 = _t1776
                    if !isnothing(deconstruct_result1521)
                        unwrapped1522 = deconstruct_result1521
                        pretty_abort(pp, unwrapped1522)
                    else
                        _dollar_dollar = msg
                        if _has_proto_field(_dollar_dollar, Symbol("#export"))
                            _t1777 = _get_oneof_field(_dollar_dollar, :var"#export")
                        else
                            _t1777 = nothing
                        end
                        deconstruct_result1519 = _t1777
                        if !isnothing(deconstruct_result1519)
                            unwrapped1520 = deconstruct_result1519
                            pretty_export(pp, unwrapped1520)
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
    flat1532 = try_flat(pp, msg, pretty_demand)
    if !isnothing(flat1532)
        write(pp, flat1532)
        return nothing
    else
        _dollar_dollar = msg
        fields1530 = _dollar_dollar.relation_id
        unwrapped_fields1531 = fields1530
        write(pp, "(demand")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, unwrapped_fields1531)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_output(pp::PrettyPrinter, msg::Proto.Output)
    flat1537 = try_flat(pp, msg, pretty_output)
    if !isnothing(flat1537)
        write(pp, flat1537)
        return nothing
    else
        _dollar_dollar = msg
        fields1533 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
        unwrapped_fields1534 = fields1533
        write(pp, "(output")
        indent_sexp!(pp)
        newline(pp)
        field1535 = unwrapped_fields1534[1]
        pretty_name(pp, field1535)
        newline(pp)
        field1536 = unwrapped_fields1534[2]
        pretty_relation_id(pp, field1536)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_what_if(pp::PrettyPrinter, msg::Proto.WhatIf)
    flat1542 = try_flat(pp, msg, pretty_what_if)
    if !isnothing(flat1542)
        write(pp, flat1542)
        return nothing
    else
        _dollar_dollar = msg
        fields1538 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
        unwrapped_fields1539 = fields1538
        write(pp, "(what_if")
        indent_sexp!(pp)
        newline(pp)
        field1540 = unwrapped_fields1539[1]
        pretty_name(pp, field1540)
        newline(pp)
        field1541 = unwrapped_fields1539[2]
        pretty_epoch(pp, field1541)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_abort(pp::PrettyPrinter, msg::Proto.Abort)
    flat1548 = try_flat(pp, msg, pretty_abort)
    if !isnothing(flat1548)
        write(pp, flat1548)
        return nothing
    else
        _dollar_dollar = msg
        if _dollar_dollar.name != "abort"
            _t1778 = _dollar_dollar.name
        else
            _t1778 = nothing
        end
        fields1543 = (_t1778, _dollar_dollar.relation_id,)
        unwrapped_fields1544 = fields1543
        write(pp, "(abort")
        indent_sexp!(pp)
        field1545 = unwrapped_fields1544[1]
        if !isnothing(field1545)
            newline(pp)
            opt_val1546 = field1545
            pretty_name(pp, opt_val1546)
        end
        newline(pp)
        field1547 = unwrapped_fields1544[2]
        pretty_relation_id(pp, field1547)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export(pp::PrettyPrinter, msg::Proto.Export)
    flat1553 = try_flat(pp, msg, pretty_export)
    if !isnothing(flat1553)
        write(pp, flat1553)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("csv_config"))
            _t1779 = _get_oneof_field(_dollar_dollar, :csv_config)
        else
            _t1779 = nothing
        end
        deconstruct_result1551 = _t1779
        if !isnothing(deconstruct_result1551)
            unwrapped1552 = deconstruct_result1551
            write(pp, "(export")
            indent_sexp!(pp)
            newline(pp)
            pretty_export_csv_config(pp, unwrapped1552)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("iceberg_config"))
                _t1780 = _get_oneof_field(_dollar_dollar, :iceberg_config)
            else
                _t1780 = nothing
            end
            deconstruct_result1549 = _t1780
            if !isnothing(deconstruct_result1549)
                unwrapped1550 = deconstruct_result1549
                write(pp, "(export_iceberg")
                indent_sexp!(pp)
                newline(pp)
                pretty_export_iceberg_config(pp, unwrapped1550)
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
    flat1564 = try_flat(pp, msg, pretty_export_csv_config)
    if !isnothing(flat1564)
        write(pp, flat1564)
        return nothing
    else
        _dollar_dollar = msg
        if length(_dollar_dollar.data_columns) == 0
            _t1781 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
        else
            _t1781 = nothing
        end
        deconstruct_result1559 = _t1781
        if !isnothing(deconstruct_result1559)
            unwrapped1560 = deconstruct_result1559
            write(pp, "(export_csv_config_v2")
            indent_sexp!(pp)
            newline(pp)
            field1561 = unwrapped1560[1]
            pretty_export_csv_path(pp, field1561)
            newline(pp)
            field1562 = unwrapped1560[2]
            pretty_export_csv_source(pp, field1562)
            newline(pp)
            field1563 = unwrapped1560[3]
            pretty_csv_config(pp, field1563)
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if length(_dollar_dollar.data_columns) != 0
                _t1783 = deconstruct_export_csv_config(pp, _dollar_dollar)
                _t1782 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1783,)
            else
                _t1782 = nothing
            end
            deconstruct_result1554 = _t1782
            if !isnothing(deconstruct_result1554)
                unwrapped1555 = deconstruct_result1554
                write(pp, "(export_csv_config")
                indent_sexp!(pp)
                newline(pp)
                field1556 = unwrapped1555[1]
                pretty_export_csv_path(pp, field1556)
                newline(pp)
                field1557 = unwrapped1555[2]
                pretty_export_csv_columns_list(pp, field1557)
                newline(pp)
                field1558 = unwrapped1555[3]
                pretty_config_dict(pp, field1558)
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
    flat1566 = try_flat(pp, msg, pretty_export_csv_path)
    if !isnothing(flat1566)
        write(pp, flat1566)
        return nothing
    else
        fields1565 = msg
        write(pp, "(path")
        indent_sexp!(pp)
        newline(pp)
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, fields1565))
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_source(pp::PrettyPrinter, msg::Proto.ExportCSVSource)
    flat1573 = try_flat(pp, msg, pretty_export_csv_source)
    if !isnothing(flat1573)
        write(pp, flat1573)
        return nothing
    else
        _dollar_dollar = msg
        if _has_proto_field(_dollar_dollar, Symbol("gnf_columns"))
            _t1784 = _get_oneof_field(_dollar_dollar, :gnf_columns).columns
        else
            _t1784 = nothing
        end
        deconstruct_result1569 = _t1784
        if !isnothing(deconstruct_result1569)
            unwrapped1570 = deconstruct_result1569
            write(pp, "(gnf_columns")
            indent_sexp!(pp)
            if !isempty(unwrapped1570)
                newline(pp)
                for (i1785, elem1571) in enumerate(unwrapped1570)
                    i1572 = i1785 - 1
                    if (i1572 > 0)
                        newline(pp)
                    end
                    pretty_export_csv_column(pp, elem1571)
                end
            end
            dedent!(pp)
            write(pp, ")")
        else
            _dollar_dollar = msg
            if _has_proto_field(_dollar_dollar, Symbol("table_def"))
                _t1786 = _get_oneof_field(_dollar_dollar, :table_def)
            else
                _t1786 = nothing
            end
            deconstruct_result1567 = _t1786
            if !isnothing(deconstruct_result1567)
                unwrapped1568 = deconstruct_result1567
                write(pp, "(table_def")
                indent_sexp!(pp)
                newline(pp)
                pretty_relation_id(pp, unwrapped1568)
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
    flat1578 = try_flat(pp, msg, pretty_export_csv_column)
    if !isnothing(flat1578)
        write(pp, flat1578)
        return nothing
    else
        _dollar_dollar = msg
        fields1574 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        unwrapped_fields1575 = fields1574
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1576 = unwrapped_fields1575[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1576))
        newline(pp)
        field1577 = unwrapped_fields1575[2]
        pretty_relation_id(pp, field1577)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_csv_columns_list(pp::PrettyPrinter, msg::Vector{Proto.ExportCSVColumn})
    flat1582 = try_flat(pp, msg, pretty_export_csv_columns_list)
    if !isnothing(flat1582)
        write(pp, flat1582)
        return nothing
    else
        fields1579 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1579)
            newline(pp)
            for (i1787, elem1580) in enumerate(fields1579)
                i1581 = i1787 - 1
                if (i1581 > 0)
                    newline(pp)
                end
                pretty_export_csv_column(pp, elem1580)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_config(pp::PrettyPrinter, msg::Proto.ExportIcebergConfig)
    flat1592 = try_flat(pp, msg, pretty_export_iceberg_config)
    if !isnothing(flat1592)
        write(pp, flat1592)
        return nothing
    else
        _dollar_dollar = msg
        _t1788 = deconstruct_export_iceberg_config_optional(pp, _dollar_dollar)
        fields1583 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, _dollar_dollar.columns, sort([(k, v) for (k, v) in _dollar_dollar.table_properties]), _t1788,)
        unwrapped_fields1584 = fields1583
        write(pp, "(export_iceberg_config")
        indent_sexp!(pp)
        newline(pp)
        field1585 = unwrapped_fields1584[1]
        pretty_iceberg_locator(pp, field1585)
        newline(pp)
        field1586 = unwrapped_fields1584[2]
        pretty_iceberg_catalog_config(pp, field1586)
        newline(pp)
        field1587 = unwrapped_fields1584[3]
        pretty_export_iceberg_table_def(pp, field1587)
        newline(pp)
        field1588 = unwrapped_fields1584[4]
        pretty_export_iceberg_columns(pp, field1588)
        newline(pp)
        field1589 = unwrapped_fields1584[5]
        pretty_iceberg_table_properties(pp, field1589)
        field1590 = unwrapped_fields1584[6]
        if !isnothing(field1590)
            newline(pp)
            opt_val1591 = field1590
            pretty_config_dict(pp, opt_val1591)
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_table_def(pp::PrettyPrinter, msg::Proto.RelationId)
    flat1594 = try_flat(pp, msg, pretty_export_iceberg_table_def)
    if !isnothing(flat1594)
        write(pp, flat1594)
        return nothing
    else
        fields1593 = msg
        write(pp, "(table_def")
        indent_sexp!(pp)
        newline(pp)
        pretty_relation_id(pp, fields1593)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_columns(pp::PrettyPrinter, msg::Vector{Proto.ExportColumn})
    flat1598 = try_flat(pp, msg, pretty_export_iceberg_columns)
    if !isnothing(flat1598)
        write(pp, flat1598)
        return nothing
    else
        fields1595 = msg
        write(pp, "(columns")
        indent_sexp!(pp)
        if !isempty(fields1595)
            newline(pp)
            for (i1789, elem1596) in enumerate(fields1595)
                i1597 = i1789 - 1
                if (i1597 > 0)
                    newline(pp)
                end
                pretty_export_iceberg_column(pp, elem1596)
            end
        end
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_export_iceberg_column(pp::PrettyPrinter, msg::Proto.ExportColumn)
    flat1603 = try_flat(pp, msg, pretty_export_iceberg_column)
    if !isnothing(flat1603)
        write(pp, flat1603)
        return nothing
    else
        _dollar_dollar = msg
        fields1599 = (_dollar_dollar.name, _dollar_dollar.nullable,)
        unwrapped_fields1600 = fields1599
        write(pp, "(column")
        indent_sexp!(pp)
        newline(pp)
        field1601 = unwrapped_fields1600[1]
        write(pp, format_string(DEFAULT_CONSTANT_FORMATTER, pp, field1601))
        newline(pp)
        field1602 = unwrapped_fields1600[2]
        pretty_boolean_value(pp, field1602)
        dedent!(pp)
        write(pp, ")")
    end
    return nothing
end

function pretty_iceberg_table_properties(pp::PrettyPrinter, msg::Vector{Tuple{String, String}})
    flat1607 = try_flat(pp, msg, pretty_iceberg_table_properties)
    if !isnothing(flat1607)
        write(pp, flat1607)
        return nothing
    else
        fields1604 = msg
        write(pp, "(table_properties")
        indent_sexp!(pp)
        if !isempty(fields1604)
            newline(pp)
            for (i1790, elem1605) in enumerate(fields1604)
                i1606 = i1790 - 1
                if (i1606 > 0)
                    newline(pp)
                end
                pretty_iceberg_property_entry(pp, elem1605)
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
    for (i1836, _rid) in enumerate(msg.ids)
        _idx = i1836 - 1
        newline(pp)
        write(pp, "(")
        _t1837 = Proto.UInt128Value(low=_rid.id_low, high=_rid.id_high)
        _pprint_dispatch(pp, _t1837)
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
    for (i1838, _elem) in enumerate(msg.keys)
        _idx = i1838 - 1
        if (_idx > 0)
            write(pp, " ")
        end
        _pprint_dispatch(pp, _elem)
    end
    write(pp, ")")
    newline(pp)
    write(pp, ":values (")
    for (i1839, _elem) in enumerate(msg.values)
        _idx = i1839 - 1
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
    for (i1840, _elem) in enumerate(msg.columns)
        _idx = i1840 - 1
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
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Tuple{String, String}}) = pretty_iceberg_properties(pp, x)
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
_pprint_dispatch(pp::PrettyPrinter, x::Vector{Proto.ExportColumn}) = pretty_export_iceberg_columns(pp, x)
_pprint_dispatch(pp::PrettyPrinter, x::Proto.ExportColumn) = pretty_export_iceberg_column(pp, x)
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
