"""
    Parser

Auto-generated LL(k) recursive-descent parser module.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `meta/` or edit the protobuf specification in `proto/v1`.

Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --parser julia
"""
module Parser

using SHA
using ProtoBuf: OneOf

# Import protobuf modules and helpers from parent
using ..relationalai: relationalai
using ..relationalai.lqp.v1
using ..LogicalQueryProtocol: _has_proto_field, _get_oneof_field
const Proto = relationalai.lqp.v1


struct ParseError <: Exception
    msg::String
end

Base.showerror(io::IO, e::ParseError) = print(io, "ParseError: ", e.msg)


struct Location
    line::Int
    column::Int
    offset::Int
end

struct Span
    start::Location
    stop::Location
    type_name::String
end

struct Token
    type::String
    value::Any
    start_pos::Int
    end_pos::Int
end

Base.show(io::IO, t::Token) = print(io, "Token(", t.type, ", ", repr(t.value), ", ", t.start_pos, ")")
Base.getproperty(t::Token, s::Symbol) = s === :pos ? getfield(t, :start_pos) : getfield(t, s)


mutable struct Lexer
    input::String
    pos::Int
    tokens::Vector{Token}

    function Lexer(input::String)
        lexer = new(input, 1, Token[])
        tokenize!(lexer)
        return lexer
    end
end


# Scanner functions for each token type
scan_symbol(s::String) = s
function scan_string(s::String)
    # Strip quotes using Unicode-safe chop (handles multi-byte characters)
    content = chop(s, head=1, tail=1)
    # Process \\ first so that \\n doesn't become a newline.
    result = replace(content, "\\\\" => "\x00")
    result = replace(result, "\\n" => "\n")
    result = replace(result, "\\t" => "\t")
    result = replace(result, "\\r" => "\r")
    result = replace(result, "\\\"" => "\"")
    result = replace(result, "\x00" => "\\")
    return result
end

scan_int(n::String) = Base.parse(Int64, n)

function scan_float(f::String)
    if f == "inf"
        return Inf
    elseif f == "nan"
        return NaN
    end
    return Base.parse(Float64, f)
end

function scan_uint128(u::String)
    # Remove the '0x' prefix
    hex_str = u[3:end]
    uint128_val = Base.parse(UInt128, hex_str, base=16)
    low = UInt64(uint128_val & 0xFFFFFFFFFFFFFFFF)
    high = UInt64((uint128_val >> 64) & 0xFFFFFFFFFFFFFFFF)
    return Proto.UInt128Value(low, high)
end

function scan_int128(u::String)
    # Remove the 'i128' suffix
    u = u[1:end-4]
    int128_val = Base.parse(Int128, u)
    low = UInt64(int128_val & 0xFFFFFFFFFFFFFFFF)
    high = UInt64((int128_val >> 64) & 0xFFFFFFFFFFFFFFFF)
    return Proto.Int128Value(low, high)
end

function scan_decimal(d::String)
    # Decimal is a string like '123.456d12' where the last part after `d` is the
    # precision, and the scale is the number of digits between the decimal point and `d`
    parts = split(d, 'd')
    if length(parts) != 2
        throw(ArgumentError("Invalid decimal format: $d"))
    end
    scale = length(split(parts[1], '.')[2])
    precision = Base.parse(Int32, parts[2])
    # Parse the integer value
    int_str = replace(parts[1], "." => "")
    int128_val = Base.parse(Int128, int_str)
    low = UInt64(int128_val & 0xFFFFFFFFFFFFFFFF)
    high = UInt64((int128_val >> 64) & 0xFFFFFFFFFFFFFFFF)
    value = Proto.Int128Value(low, high)
    return Proto.DecimalValue(precision, scale, value)
end

const _WHITESPACE_RE = r"\s+"
const _COMMENT_RE = r";;.*"
const _TOKEN_SPECS = [
    ("LITERAL", r"::", identity),
    ("LITERAL", r"<=", identity),
    ("LITERAL", r">=", identity),
    ("LITERAL", r"\#", identity),
    ("LITERAL", r"\(", identity),
    ("LITERAL", r"\)", identity),
    ("LITERAL", r"\*", identity),
    ("LITERAL", r"\+", identity),
    ("LITERAL", r"\-", identity),
    ("LITERAL", r"/", identity),
    ("LITERAL", r":", identity),
    ("LITERAL", r"<", identity),
    ("LITERAL", r"=", identity),
    ("LITERAL", r">", identity),
    ("LITERAL", r"\[", identity),
    ("LITERAL", r"\]", identity),
    ("LITERAL", r"\{", identity),
    ("LITERAL", r"\|", identity),
    ("LITERAL", r"\}", identity),
    ("DECIMAL", r"[-]?\d+\.\d+d\d+", scan_decimal),
    ("FLOAT", r"([-]?\d+\.\d+|inf|nan)", scan_float),
    ("INT", r"[-]?\d+", scan_int),
    ("INT128", r"[-]?\d+i128", scan_int128),
    ("STRING", r"\"(?:[^\"\\]|\\.)*\"", scan_string),
    ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_.-]*", scan_symbol),
    ("UINT128", r"0x[0-9a-fA-F]+", scan_uint128),
]

function tokenize!(lexer::Lexer)
    # Use ncodeunits for byte-based position tracking (UTF-8 safe)
    while lexer.pos <= ncodeunits(lexer.input)
        # Skip whitespace
        m = match(_WHITESPACE_RE, lexer.input, lexer.pos)
        if m !== nothing && m.offset == lexer.pos
            lexer.pos = m.offset + ncodeunits(m.match)
            continue
        end

        # Skip comments
        m = match(_COMMENT_RE, lexer.input, lexer.pos)
        if m !== nothing && m.offset == lexer.pos
            lexer.pos = m.offset + ncodeunits(m.match)
            continue
        end

        # Collect all matching tokens
        candidates = Tuple{String,String,Function,Int}[]

        for (token_type, regex, action) in _TOKEN_SPECS
            m = match(regex, lexer.input, lexer.pos)
            if m !== nothing && m.offset == lexer.pos
                value = m.match
                push!(candidates, (token_type, value, action, m.offset + ncodeunits(value)))
            end
        end

        if isempty(candidates)
            throw(ParseError("Unexpected character at position $(lexer.pos): $(repr(lexer.input[lexer.pos]))"))
        end

        # Pick the longest match
        token_type, value, action, end_pos = candidates[argmax([c[4] for c in candidates])]
        push!(lexer.tokens, Token(token_type, action(value), lexer.pos, end_pos))
        lexer.pos = end_pos
    end

    push!(lexer.tokens, Token("\$", "", lexer.pos, lexer.pos))
    return nothing
end


function _compute_line_starts(text::String)::Vector{Int}
    starts = [1]
    for i in eachindex(text)
        if text[i] == '\n'
            push!(starts, nextind(text, i))
        end
    end
    return starts
end

mutable struct ParserState
    tokens::Vector{Token}
    pos::Int
    id_to_debuginfo::Dict{Vector{UInt8},Vector{Pair{Tuple{UInt64,UInt64},String}}}
    _current_fragment_id::Union{Nothing,Vector{UInt8}}
    _relation_id_to_name::Dict{Tuple{UInt64,UInt64},String}
    provenance::Dict{Int,Span}
    _line_starts::Vector{Int}

    function ParserState(tokens::Vector{Token}, input_str::String)
        return new(tokens, 1, Dict(), nothing, Dict(), Dict(), _compute_line_starts(input_str))
    end
end


function _make_location(parser::ParserState, offset::Int)::Location
    line_idx = searchsortedlast(parser._line_starts, offset)
    col = offset - parser._line_starts[line_idx]
    return Location(line_idx, col + 1, offset)
end

function span_start(parser::ParserState)::Int
    return lookahead(parser, 0).start_pos
end

function record_span!(parser::ParserState, start_offset::Int, type_name::String="")
    # First-wins: innermost parse function records first; outer wrappers
    # that share the same offset do not overwrite.
    haskey(parser.provenance, start_offset) && return nothing
    if parser.pos > 1
        end_offset = parser.tokens[parser.pos - 1].end_pos
    else
        end_offset = start_offset
    end
    s = Span(_make_location(parser, start_offset), _make_location(parser, end_offset), type_name)
    parser.provenance[start_offset] = s
    return nothing
end

function lookahead(parser::ParserState, k::Int=0)::Token
    idx = parser.pos + k
    return idx <= length(parser.tokens) ? parser.tokens[idx] : Token("\$", "", -1, -1)
end


function consume_literal!(parser::ParserState, expected::String)
    if !match_lookahead_literal(parser, expected, 0)
        token = lookahead(parser, 0)
        throw(ParseError("Expected literal $(repr(expected)) but got $(token.type)=`$(repr(token.value))` at position $(token.pos)"))
    end
    parser.pos += 1
    return nothing
end


function consume_terminal!(parser::ParserState, expected::String)
    if !match_lookahead_terminal(parser, expected, 0)
        token = lookahead(parser, 0)
        throw(ParseError("Expected terminal $expected but got $(token.type)=`$(repr(token.value))` at position $(token.pos)"))
    end
    token = lookahead(parser, 0)
    parser.pos += 1
    return token.value
end


function match_lookahead_literal(parser::ParserState, literal::String, k::Int)::Bool
    token = lookahead(parser, k)
    # Support soft keywords: alphanumeric literals are lexed as SYMBOL tokens
    if token.type == "LITERAL" && token.value == literal
        return true
    end
    if token.type == "SYMBOL" && token.value == literal
        return true
    end
    return false
end


function match_lookahead_terminal(parser::ParserState, terminal::String, k::Int)::Bool
    token = lookahead(parser, k)
    return token.type == terminal
end


function start_fragment!(parser::ParserState, fragment_id::Proto.FragmentId)
    parser._current_fragment_id = fragment_id.id
    return fragment_id
end


function relation_id_from_string(parser::ParserState, name::String)
    # Create RelationId from string and track mapping for debug info
    hash_bytes = sha256(name)
    id_low = Base.parse(UInt64, bytes2hex(hash_bytes[1:8]), base=16)
    id_high = UInt64(0)
    relation_id = Proto.RelationId(id_low, id_high)

    # Store the mapping for the current fragment if we're inside one
    if parser._current_fragment_id !== nothing
        if !haskey(parser.id_to_debuginfo, parser._current_fragment_id)
            parser.id_to_debuginfo[parser._current_fragment_id] = Pair{Tuple{UInt64,UInt64},String}[]
        end
        entries = parser.id_to_debuginfo[parser._current_fragment_id]
        key = (relation_id.id_low, relation_id.id_high)
        if !any(p -> p.first == key, entries)
            push!(entries, key => name)
        end
    end

    return relation_id
end

function construct_fragment(
    parser::ParserState,
    fragment_id::Proto.FragmentId,
    declarations::Vector{Proto.Declaration}
)
    # Get the debug info for this fragment
    debug_info_entries = get(parser.id_to_debuginfo, fragment_id.id, Pair{Tuple{UInt64,UInt64},String}[])

    # Convert to DebugInfo protobuf (preserving insertion order)
    ids = Proto.RelationId[]
    orig_names = String[]
    for (key, name) in debug_info_entries
        push!(ids, Proto.RelationId(key[1], key[2]))
        push!(orig_names, name)
    end

    # Create DebugInfo
    debug_info = Proto.DebugInfo(ids, orig_names)

    # Clear _current_fragment_id before the return
    parser._current_fragment_id = nothing

    # Create and return Fragment
    return Proto.Fragment(fragment_id, declarations, debug_info)
end

# --- Helper functions ---

function _extract_value_int32(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int32
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return Int32(_get_oneof_field(value, :int_value))
    else
        _t1758 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1759 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1760 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1761 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1762 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1763 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1764 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1765 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1766 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1767 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1767
    _t1768 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1768
    _t1769 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1769
    _t1770 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1770
    _t1771 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1771
    _t1772 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1772
    _t1773 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1773
    _t1774 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1774
    _t1775 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1775
    _t1776 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1776
    _t1777 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1777
    _t1778 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t1778
    _t1779 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t1779
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1780 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1780
    _t1781 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1781
    _t1782 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1782
    _t1783 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1783
    _t1784 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1784
    _t1785 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1785
    _t1786 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1786
    _t1787 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1787
    _t1788 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1788
    _t1789 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1789
    _t1790 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1790
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1791 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1791
    _t1792 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1792
end

function construct_configure(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.Configure
    config = Dict(config_dict)
    maintenance_level_val = get(config, "ivm.maintenance_level", nothing)
    maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
    if (!isnothing(maintenance_level_val) && _has_proto_field(maintenance_level_val, Symbol("string_value")))
        if _get_oneof_field(maintenance_level_val, :string_value) == "off"
            maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        else
            if _get_oneof_field(maintenance_level_val, :string_value) == "auto"
                maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
            else
                if _get_oneof_field(maintenance_level_val, :string_value) == "all"
                    maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
                else
                    maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                end
            end
        end
    end
    _t1793 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1793
    _t1794 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1794
    _t1795 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1795
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1796 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1796
    _t1797 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1797
    _t1798 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1798
    _t1799 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1799
    _t1800 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1800
    _t1801 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1801
    _t1802 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1802
    _t1803 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1803
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1804 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1804
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start572 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1133 = parse_configure(parser)
        _t1132 = _t1133
    else
        _t1132 = nothing
    end
    configure566 = _t1132
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1135 = parse_sync(parser)
        _t1134 = _t1135
    else
        _t1134 = nothing
    end
    sync567 = _t1134
    xs568 = Proto.Epoch[]
    cond569 = match_lookahead_literal(parser, "(", 0)
    while cond569
        _t1136 = parse_epoch(parser)
        item570 = _t1136
        push!(xs568, item570)
        cond569 = match_lookahead_literal(parser, "(", 0)
    end
    epochs571 = xs568
    consume_literal!(parser, ")")
    _t1137 = default_configure(parser)
    _t1138 = Proto.Transaction(epochs=epochs571, configure=(!isnothing(configure566) ? configure566 : _t1137), sync=sync567)
    result573 = _t1138
    record_span!(parser, span_start572, "Transaction")
    return result573
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start575 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1139 = parse_config_dict(parser)
    config_dict574 = _t1139
    consume_literal!(parser, ")")
    _t1140 = construct_configure(parser, config_dict574)
    result576 = _t1140
    record_span!(parser, span_start575, "Configure")
    return result576
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs577 = Tuple{String, Proto.Value}[]
    cond578 = match_lookahead_literal(parser, ":", 0)
    while cond578
        _t1141 = parse_config_key_value(parser)
        item579 = _t1141
        push!(xs577, item579)
        cond578 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values580 = xs577
    consume_literal!(parser, "}")
    return config_key_values580
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol581 = consume_terminal!(parser, "SYMBOL")
    _t1142 = parse_value(parser)
    value582 = _t1142
    return (symbol581, value582,)
end

function parse_value(parser::ParserState)::Proto.Value
    span_start593 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1143 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1144 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1145 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1147 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1148 = 0
                        else
                            _t1148 = -1
                        end
                        _t1147 = _t1148
                    end
                    _t1146 = _t1147
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1149 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1150 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t1151 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t1152 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t1153 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t1154 = 7
                                        else
                                            _t1154 = -1
                                        end
                                        _t1153 = _t1154
                                    end
                                    _t1152 = _t1153
                                end
                                _t1151 = _t1152
                            end
                            _t1150 = _t1151
                        end
                        _t1149 = _t1150
                    end
                    _t1146 = _t1149
                end
                _t1145 = _t1146
            end
            _t1144 = _t1145
        end
        _t1143 = _t1144
    end
    prediction583 = _t1143
    if prediction583 == 9
        _t1156 = parse_boolean_value(parser)
        boolean_value592 = _t1156
        _t1157 = Proto.Value(value=OneOf(:boolean_value, boolean_value592))
        _t1155 = _t1157
    else
        if prediction583 == 8
            consume_literal!(parser, "missing")
            _t1159 = Proto.MissingValue()
            _t1160 = Proto.Value(value=OneOf(:missing_value, _t1159))
            _t1158 = _t1160
        else
            if prediction583 == 7
                decimal591 = consume_terminal!(parser, "DECIMAL")
                _t1162 = Proto.Value(value=OneOf(:decimal_value, decimal591))
                _t1161 = _t1162
            else
                if prediction583 == 6
                    int128590 = consume_terminal!(parser, "INT128")
                    _t1164 = Proto.Value(value=OneOf(:int128_value, int128590))
                    _t1163 = _t1164
                else
                    if prediction583 == 5
                        uint128589 = consume_terminal!(parser, "UINT128")
                        _t1166 = Proto.Value(value=OneOf(:uint128_value, uint128589))
                        _t1165 = _t1166
                    else
                        if prediction583 == 4
                            float588 = consume_terminal!(parser, "FLOAT")
                            _t1168 = Proto.Value(value=OneOf(:float_value, float588))
                            _t1167 = _t1168
                        else
                            if prediction583 == 3
                                int587 = consume_terminal!(parser, "INT")
                                _t1170 = Proto.Value(value=OneOf(:int_value, int587))
                                _t1169 = _t1170
                            else
                                if prediction583 == 2
                                    string586 = consume_terminal!(parser, "STRING")
                                    _t1172 = Proto.Value(value=OneOf(:string_value, string586))
                                    _t1171 = _t1172
                                else
                                    if prediction583 == 1
                                        _t1174 = parse_datetime(parser)
                                        datetime585 = _t1174
                                        _t1175 = Proto.Value(value=OneOf(:datetime_value, datetime585))
                                        _t1173 = _t1175
                                    else
                                        if prediction583 == 0
                                            _t1177 = parse_date(parser)
                                            date584 = _t1177
                                            _t1178 = Proto.Value(value=OneOf(:date_value, date584))
                                            _t1176 = _t1178
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1173 = _t1176
                                    end
                                    _t1171 = _t1173
                                end
                                _t1169 = _t1171
                            end
                            _t1167 = _t1169
                        end
                        _t1165 = _t1167
                    end
                    _t1163 = _t1165
                end
                _t1161 = _t1163
            end
            _t1158 = _t1161
        end
        _t1155 = _t1158
    end
    result594 = _t1155
    record_span!(parser, span_start593, "Value")
    return result594
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start598 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int595 = consume_terminal!(parser, "INT")
    int_3596 = consume_terminal!(parser, "INT")
    int_4597 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1179 = Proto.DateValue(year=Int32(int595), month=Int32(int_3596), day=Int32(int_4597))
    result599 = _t1179
    record_span!(parser, span_start598, "DateValue")
    return result599
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start607 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int600 = consume_terminal!(parser, "INT")
    int_3601 = consume_terminal!(parser, "INT")
    int_4602 = consume_terminal!(parser, "INT")
    int_5603 = consume_terminal!(parser, "INT")
    int_6604 = consume_terminal!(parser, "INT")
    int_7605 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1180 = consume_terminal!(parser, "INT")
    else
        _t1180 = nothing
    end
    int_8606 = _t1180
    consume_literal!(parser, ")")
    _t1181 = Proto.DateTimeValue(year=Int32(int600), month=Int32(int_3601), day=Int32(int_4602), hour=Int32(int_5603), minute=Int32(int_6604), second=Int32(int_7605), microsecond=Int32((!isnothing(int_8606) ? int_8606 : 0)))
    result608 = _t1181
    record_span!(parser, span_start607, "DateTimeValue")
    return result608
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1182 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1183 = 1
        else
            _t1183 = -1
        end
        _t1182 = _t1183
    end
    prediction609 = _t1182
    if prediction609 == 1
        consume_literal!(parser, "false")
        _t1184 = false
    else
        if prediction609 == 0
            consume_literal!(parser, "true")
            _t1185 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1184 = _t1185
    end
    return _t1184
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start614 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs610 = Proto.FragmentId[]
    cond611 = match_lookahead_literal(parser, ":", 0)
    while cond611
        _t1186 = parse_fragment_id(parser)
        item612 = _t1186
        push!(xs610, item612)
        cond611 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids613 = xs610
    consume_literal!(parser, ")")
    _t1187 = Proto.Sync(fragments=fragment_ids613)
    result615 = _t1187
    record_span!(parser, span_start614, "Sync")
    return result615
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start617 = span_start(parser)
    consume_literal!(parser, ":")
    symbol616 = consume_terminal!(parser, "SYMBOL")
    result618 = Proto.FragmentId(Vector{UInt8}(symbol616))
    record_span!(parser, span_start617, "FragmentId")
    return result618
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start621 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1189 = parse_epoch_writes(parser)
        _t1188 = _t1189
    else
        _t1188 = nothing
    end
    epoch_writes619 = _t1188
    if match_lookahead_literal(parser, "(", 0)
        _t1191 = parse_epoch_reads(parser)
        _t1190 = _t1191
    else
        _t1190 = nothing
    end
    epoch_reads620 = _t1190
    consume_literal!(parser, ")")
    _t1192 = Proto.Epoch(writes=(!isnothing(epoch_writes619) ? epoch_writes619 : Proto.Write[]), reads=(!isnothing(epoch_reads620) ? epoch_reads620 : Proto.Read[]))
    result622 = _t1192
    record_span!(parser, span_start621, "Epoch")
    return result622
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs623 = Proto.Write[]
    cond624 = match_lookahead_literal(parser, "(", 0)
    while cond624
        _t1193 = parse_write(parser)
        item625 = _t1193
        push!(xs623, item625)
        cond624 = match_lookahead_literal(parser, "(", 0)
    end
    writes626 = xs623
    consume_literal!(parser, ")")
    return writes626
end

function parse_write(parser::ParserState)::Proto.Write
    span_start632 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1195 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1196 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1197 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1198 = 2
                    else
                        _t1198 = -1
                    end
                    _t1197 = _t1198
                end
                _t1196 = _t1197
            end
            _t1195 = _t1196
        end
        _t1194 = _t1195
    else
        _t1194 = -1
    end
    prediction627 = _t1194
    if prediction627 == 3
        _t1200 = parse_snapshot(parser)
        snapshot631 = _t1200
        _t1201 = Proto.Write(write_type=OneOf(:snapshot, snapshot631))
        _t1199 = _t1201
    else
        if prediction627 == 2
            _t1203 = parse_context(parser)
            context630 = _t1203
            _t1204 = Proto.Write(write_type=OneOf(:context, context630))
            _t1202 = _t1204
        else
            if prediction627 == 1
                _t1206 = parse_undefine(parser)
                undefine629 = _t1206
                _t1207 = Proto.Write(write_type=OneOf(:undefine, undefine629))
                _t1205 = _t1207
            else
                if prediction627 == 0
                    _t1209 = parse_define(parser)
                    define628 = _t1209
                    _t1210 = Proto.Write(write_type=OneOf(:define, define628))
                    _t1208 = _t1210
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1205 = _t1208
            end
            _t1202 = _t1205
        end
        _t1199 = _t1202
    end
    result633 = _t1199
    record_span!(parser, span_start632, "Write")
    return result633
end

function parse_define(parser::ParserState)::Proto.Define
    span_start635 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1211 = parse_fragment(parser)
    fragment634 = _t1211
    consume_literal!(parser, ")")
    _t1212 = Proto.Define(fragment=fragment634)
    result636 = _t1212
    record_span!(parser, span_start635, "Define")
    return result636
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start642 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1213 = parse_new_fragment_id(parser)
    new_fragment_id637 = _t1213
    xs638 = Proto.Declaration[]
    cond639 = match_lookahead_literal(parser, "(", 0)
    while cond639
        _t1214 = parse_declaration(parser)
        item640 = _t1214
        push!(xs638, item640)
        cond639 = match_lookahead_literal(parser, "(", 0)
    end
    declarations641 = xs638
    consume_literal!(parser, ")")
    result643 = construct_fragment(parser, new_fragment_id637, declarations641)
    record_span!(parser, span_start642, "Fragment")
    return result643
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start645 = span_start(parser)
    _t1215 = parse_fragment_id(parser)
    fragment_id644 = _t1215
    start_fragment!(parser, fragment_id644)
    result646 = fragment_id644
    record_span!(parser, span_start645, "FragmentId")
    return result646
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start652 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "functional_dependency", 1)
            _t1217 = 2
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1218 = 3
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1219 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1220 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1221 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1222 = 1
                            else
                                _t1222 = -1
                            end
                            _t1221 = _t1222
                        end
                        _t1220 = _t1221
                    end
                    _t1219 = _t1220
                end
                _t1218 = _t1219
            end
            _t1217 = _t1218
        end
        _t1216 = _t1217
    else
        _t1216 = -1
    end
    prediction647 = _t1216
    if prediction647 == 3
        _t1224 = parse_data(parser)
        data651 = _t1224
        _t1225 = Proto.Declaration(declaration_type=OneOf(:data, data651))
        _t1223 = _t1225
    else
        if prediction647 == 2
            _t1227 = parse_constraint(parser)
            constraint650 = _t1227
            _t1228 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint650))
            _t1226 = _t1228
        else
            if prediction647 == 1
                _t1230 = parse_algorithm(parser)
                algorithm649 = _t1230
                _t1231 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm649))
                _t1229 = _t1231
            else
                if prediction647 == 0
                    _t1233 = parse_def(parser)
                    def648 = _t1233
                    _t1234 = Proto.Declaration(declaration_type=OneOf(:def, def648))
                    _t1232 = _t1234
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1229 = _t1232
            end
            _t1226 = _t1229
        end
        _t1223 = _t1226
    end
    result653 = _t1223
    record_span!(parser, span_start652, "Declaration")
    return result653
end

function parse_def(parser::ParserState)::Proto.Def
    span_start657 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1235 = parse_relation_id(parser)
    relation_id654 = _t1235
    _t1236 = parse_abstraction(parser)
    abstraction655 = _t1236
    if match_lookahead_literal(parser, "(", 0)
        _t1238 = parse_attrs(parser)
        _t1237 = _t1238
    else
        _t1237 = nothing
    end
    attrs656 = _t1237
    consume_literal!(parser, ")")
    _t1239 = Proto.Def(name=relation_id654, body=abstraction655, attrs=(!isnothing(attrs656) ? attrs656 : Proto.Attribute[]))
    result658 = _t1239
    record_span!(parser, span_start657, "Def")
    return result658
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start662 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1240 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1241 = 1
        else
            _t1241 = -1
        end
        _t1240 = _t1241
    end
    prediction659 = _t1240
    if prediction659 == 1
        uint128661 = consume_terminal!(parser, "UINT128")
        _t1242 = Proto.RelationId(uint128661.low, uint128661.high)
    else
        if prediction659 == 0
            consume_literal!(parser, ":")
            symbol660 = consume_terminal!(parser, "SYMBOL")
            _t1243 = relation_id_from_string(parser, symbol660)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1242 = _t1243
    end
    result663 = _t1242
    record_span!(parser, span_start662, "RelationId")
    return result663
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start666 = span_start(parser)
    consume_literal!(parser, "(")
    _t1244 = parse_bindings(parser)
    bindings664 = _t1244
    _t1245 = parse_formula(parser)
    formula665 = _t1245
    consume_literal!(parser, ")")
    _t1246 = Proto.Abstraction(vars=vcat(bindings664[1], !isnothing(bindings664[2]) ? bindings664[2] : []), value=formula665)
    result667 = _t1246
    record_span!(parser, span_start666, "Abstraction")
    return result667
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs668 = Proto.Binding[]
    cond669 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond669
        _t1247 = parse_binding(parser)
        item670 = _t1247
        push!(xs668, item670)
        cond669 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings671 = xs668
    if match_lookahead_literal(parser, "|", 0)
        _t1249 = parse_value_bindings(parser)
        _t1248 = _t1249
    else
        _t1248 = nothing
    end
    value_bindings672 = _t1248
    consume_literal!(parser, "]")
    return (bindings671, (!isnothing(value_bindings672) ? value_bindings672 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start675 = span_start(parser)
    symbol673 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1250 = parse_type(parser)
    type674 = _t1250
    _t1251 = Proto.Var(name=symbol673)
    _t1252 = Proto.Binding(var=_t1251, var"#type"=type674)
    result676 = _t1252
    record_span!(parser, span_start675, "Binding")
    return result676
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start689 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1253 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t1254 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t1255 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t1256 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t1257 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t1258 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t1259 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t1260 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t1261 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t1262 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t1263 = 9
                                            else
                                                _t1263 = -1
                                            end
                                            _t1262 = _t1263
                                        end
                                        _t1261 = _t1262
                                    end
                                    _t1260 = _t1261
                                end
                                _t1259 = _t1260
                            end
                            _t1258 = _t1259
                        end
                        _t1257 = _t1258
                    end
                    _t1256 = _t1257
                end
                _t1255 = _t1256
            end
            _t1254 = _t1255
        end
        _t1253 = _t1254
    end
    prediction677 = _t1253
    if prediction677 == 10
        _t1265 = parse_boolean_type(parser)
        boolean_type688 = _t1265
        _t1266 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type688))
        _t1264 = _t1266
    else
        if prediction677 == 9
            _t1268 = parse_decimal_type(parser)
            decimal_type687 = _t1268
            _t1269 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type687))
            _t1267 = _t1269
        else
            if prediction677 == 8
                _t1271 = parse_missing_type(parser)
                missing_type686 = _t1271
                _t1272 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type686))
                _t1270 = _t1272
            else
                if prediction677 == 7
                    _t1274 = parse_datetime_type(parser)
                    datetime_type685 = _t1274
                    _t1275 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type685))
                    _t1273 = _t1275
                else
                    if prediction677 == 6
                        _t1277 = parse_date_type(parser)
                        date_type684 = _t1277
                        _t1278 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type684))
                        _t1276 = _t1278
                    else
                        if prediction677 == 5
                            _t1280 = parse_int128_type(parser)
                            int128_type683 = _t1280
                            _t1281 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type683))
                            _t1279 = _t1281
                        else
                            if prediction677 == 4
                                _t1283 = parse_uint128_type(parser)
                                uint128_type682 = _t1283
                                _t1284 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type682))
                                _t1282 = _t1284
                            else
                                if prediction677 == 3
                                    _t1286 = parse_float_type(parser)
                                    float_type681 = _t1286
                                    _t1287 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type681))
                                    _t1285 = _t1287
                                else
                                    if prediction677 == 2
                                        _t1289 = parse_int_type(parser)
                                        int_type680 = _t1289
                                        _t1290 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type680))
                                        _t1288 = _t1290
                                    else
                                        if prediction677 == 1
                                            _t1292 = parse_string_type(parser)
                                            string_type679 = _t1292
                                            _t1293 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type679))
                                            _t1291 = _t1293
                                        else
                                            if prediction677 == 0
                                                _t1295 = parse_unspecified_type(parser)
                                                unspecified_type678 = _t1295
                                                _t1296 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type678))
                                                _t1294 = _t1296
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t1291 = _t1294
                                        end
                                        _t1288 = _t1291
                                    end
                                    _t1285 = _t1288
                                end
                                _t1282 = _t1285
                            end
                            _t1279 = _t1282
                        end
                        _t1276 = _t1279
                    end
                    _t1273 = _t1276
                end
                _t1270 = _t1273
            end
            _t1267 = _t1270
        end
        _t1264 = _t1267
    end
    result690 = _t1264
    record_span!(parser, span_start689, "Type")
    return result690
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start691 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1297 = Proto.UnspecifiedType()
    result692 = _t1297
    record_span!(parser, span_start691, "UnspecifiedType")
    return result692
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start693 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1298 = Proto.StringType()
    result694 = _t1298
    record_span!(parser, span_start693, "StringType")
    return result694
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start695 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1299 = Proto.IntType()
    result696 = _t1299
    record_span!(parser, span_start695, "IntType")
    return result696
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start697 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1300 = Proto.FloatType()
    result698 = _t1300
    record_span!(parser, span_start697, "FloatType")
    return result698
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start699 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1301 = Proto.UInt128Type()
    result700 = _t1301
    record_span!(parser, span_start699, "UInt128Type")
    return result700
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start701 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1302 = Proto.Int128Type()
    result702 = _t1302
    record_span!(parser, span_start701, "Int128Type")
    return result702
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start703 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1303 = Proto.DateType()
    result704 = _t1303
    record_span!(parser, span_start703, "DateType")
    return result704
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start705 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1304 = Proto.DateTimeType()
    result706 = _t1304
    record_span!(parser, span_start705, "DateTimeType")
    return result706
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start707 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1305 = Proto.MissingType()
    result708 = _t1305
    record_span!(parser, span_start707, "MissingType")
    return result708
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start711 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int709 = consume_terminal!(parser, "INT")
    int_3710 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1306 = Proto.DecimalType(precision=Int32(int709), scale=Int32(int_3710))
    result712 = _t1306
    record_span!(parser, span_start711, "DecimalType")
    return result712
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start713 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1307 = Proto.BooleanType()
    result714 = _t1307
    record_span!(parser, span_start713, "BooleanType")
    return result714
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs715 = Proto.Binding[]
    cond716 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond716
        _t1308 = parse_binding(parser)
        item717 = _t1308
        push!(xs715, item717)
        cond716 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings718 = xs715
    return bindings718
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start733 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1310 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1311 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1312 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1313 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1314 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1315 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1316 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1317 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1318 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1319 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1320 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1321 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1322 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1323 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1324 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1325 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1326 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1327 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1328 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1329 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1330 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1331 = 10
                                                                                            else
                                                                                                _t1331 = -1
                                                                                            end
                                                                                            _t1330 = _t1331
                                                                                        end
                                                                                        _t1329 = _t1330
                                                                                    end
                                                                                    _t1328 = _t1329
                                                                                end
                                                                                _t1327 = _t1328
                                                                            end
                                                                            _t1326 = _t1327
                                                                        end
                                                                        _t1325 = _t1326
                                                                    end
                                                                    _t1324 = _t1325
                                                                end
                                                                _t1323 = _t1324
                                                            end
                                                            _t1322 = _t1323
                                                        end
                                                        _t1321 = _t1322
                                                    end
                                                    _t1320 = _t1321
                                                end
                                                _t1319 = _t1320
                                            end
                                            _t1318 = _t1319
                                        end
                                        _t1317 = _t1318
                                    end
                                    _t1316 = _t1317
                                end
                                _t1315 = _t1316
                            end
                            _t1314 = _t1315
                        end
                        _t1313 = _t1314
                    end
                    _t1312 = _t1313
                end
                _t1311 = _t1312
            end
            _t1310 = _t1311
        end
        _t1309 = _t1310
    else
        _t1309 = -1
    end
    prediction719 = _t1309
    if prediction719 == 12
        _t1333 = parse_cast(parser)
        cast732 = _t1333
        _t1334 = Proto.Formula(formula_type=OneOf(:cast, cast732))
        _t1332 = _t1334
    else
        if prediction719 == 11
            _t1336 = parse_rel_atom(parser)
            rel_atom731 = _t1336
            _t1337 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom731))
            _t1335 = _t1337
        else
            if prediction719 == 10
                _t1339 = parse_primitive(parser)
                primitive730 = _t1339
                _t1340 = Proto.Formula(formula_type=OneOf(:primitive, primitive730))
                _t1338 = _t1340
            else
                if prediction719 == 9
                    _t1342 = parse_pragma(parser)
                    pragma729 = _t1342
                    _t1343 = Proto.Formula(formula_type=OneOf(:pragma, pragma729))
                    _t1341 = _t1343
                else
                    if prediction719 == 8
                        _t1345 = parse_atom(parser)
                        atom728 = _t1345
                        _t1346 = Proto.Formula(formula_type=OneOf(:atom, atom728))
                        _t1344 = _t1346
                    else
                        if prediction719 == 7
                            _t1348 = parse_ffi(parser)
                            ffi727 = _t1348
                            _t1349 = Proto.Formula(formula_type=OneOf(:ffi, ffi727))
                            _t1347 = _t1349
                        else
                            if prediction719 == 6
                                _t1351 = parse_not(parser)
                                not726 = _t1351
                                _t1352 = Proto.Formula(formula_type=OneOf(:not, not726))
                                _t1350 = _t1352
                            else
                                if prediction719 == 5
                                    _t1354 = parse_disjunction(parser)
                                    disjunction725 = _t1354
                                    _t1355 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction725))
                                    _t1353 = _t1355
                                else
                                    if prediction719 == 4
                                        _t1357 = parse_conjunction(parser)
                                        conjunction724 = _t1357
                                        _t1358 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction724))
                                        _t1356 = _t1358
                                    else
                                        if prediction719 == 3
                                            _t1360 = parse_reduce(parser)
                                            reduce723 = _t1360
                                            _t1361 = Proto.Formula(formula_type=OneOf(:reduce, reduce723))
                                            _t1359 = _t1361
                                        else
                                            if prediction719 == 2
                                                _t1363 = parse_exists(parser)
                                                exists722 = _t1363
                                                _t1364 = Proto.Formula(formula_type=OneOf(:exists, exists722))
                                                _t1362 = _t1364
                                            else
                                                if prediction719 == 1
                                                    _t1366 = parse_false(parser)
                                                    false721 = _t1366
                                                    _t1367 = Proto.Formula(formula_type=OneOf(:disjunction, false721))
                                                    _t1365 = _t1367
                                                else
                                                    if prediction719 == 0
                                                        _t1369 = parse_true(parser)
                                                        true720 = _t1369
                                                        _t1370 = Proto.Formula(formula_type=OneOf(:conjunction, true720))
                                                        _t1368 = _t1370
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1365 = _t1368
                                                end
                                                _t1362 = _t1365
                                            end
                                            _t1359 = _t1362
                                        end
                                        _t1356 = _t1359
                                    end
                                    _t1353 = _t1356
                                end
                                _t1350 = _t1353
                            end
                            _t1347 = _t1350
                        end
                        _t1344 = _t1347
                    end
                    _t1341 = _t1344
                end
                _t1338 = _t1341
            end
            _t1335 = _t1338
        end
        _t1332 = _t1335
    end
    result734 = _t1332
    record_span!(parser, span_start733, "Formula")
    return result734
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start735 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1371 = Proto.Conjunction(args=Proto.Formula[])
    result736 = _t1371
    record_span!(parser, span_start735, "Conjunction")
    return result736
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start737 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1372 = Proto.Disjunction(args=Proto.Formula[])
    result738 = _t1372
    record_span!(parser, span_start737, "Disjunction")
    return result738
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start741 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1373 = parse_bindings(parser)
    bindings739 = _t1373
    _t1374 = parse_formula(parser)
    formula740 = _t1374
    consume_literal!(parser, ")")
    _t1375 = Proto.Abstraction(vars=vcat(bindings739[1], !isnothing(bindings739[2]) ? bindings739[2] : []), value=formula740)
    _t1376 = Proto.Exists(body=_t1375)
    result742 = _t1376
    record_span!(parser, span_start741, "Exists")
    return result742
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start746 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1377 = parse_abstraction(parser)
    abstraction743 = _t1377
    _t1378 = parse_abstraction(parser)
    abstraction_3744 = _t1378
    _t1379 = parse_terms(parser)
    terms745 = _t1379
    consume_literal!(parser, ")")
    _t1380 = Proto.Reduce(op=abstraction743, body=abstraction_3744, terms=terms745)
    result747 = _t1380
    record_span!(parser, span_start746, "Reduce")
    return result747
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs748 = Proto.Term[]
    cond749 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond749
        _t1381 = parse_term(parser)
        item750 = _t1381
        push!(xs748, item750)
        cond749 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms751 = xs748
    consume_literal!(parser, ")")
    return terms751
end

function parse_term(parser::ParserState)::Proto.Term
    span_start755 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1382 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1383 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1384 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1385 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1386 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1387 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1388 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1389 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1390 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t1391 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t1392 = 1
                                            else
                                                _t1392 = -1
                                            end
                                            _t1391 = _t1392
                                        end
                                        _t1390 = _t1391
                                    end
                                    _t1389 = _t1390
                                end
                                _t1388 = _t1389
                            end
                            _t1387 = _t1388
                        end
                        _t1386 = _t1387
                    end
                    _t1385 = _t1386
                end
                _t1384 = _t1385
            end
            _t1383 = _t1384
        end
        _t1382 = _t1383
    end
    prediction752 = _t1382
    if prediction752 == 1
        _t1394 = parse_constant(parser)
        constant754 = _t1394
        _t1395 = Proto.Term(term_type=OneOf(:constant, constant754))
        _t1393 = _t1395
    else
        if prediction752 == 0
            _t1397 = parse_var(parser)
            var753 = _t1397
            _t1398 = Proto.Term(term_type=OneOf(:var, var753))
            _t1396 = _t1398
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1393 = _t1396
    end
    result756 = _t1393
    record_span!(parser, span_start755, "Term")
    return result756
end

function parse_var(parser::ParserState)::Proto.Var
    span_start758 = span_start(parser)
    symbol757 = consume_terminal!(parser, "SYMBOL")
    _t1399 = Proto.Var(name=symbol757)
    result759 = _t1399
    record_span!(parser, span_start758, "Var")
    return result759
end

function parse_constant(parser::ParserState)::Proto.Value
    span_start761 = span_start(parser)
    _t1400 = parse_value(parser)
    value760 = _t1400
    result762 = value760
    record_span!(parser, span_start761, "Value")
    return result762
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start767 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs763 = Proto.Formula[]
    cond764 = match_lookahead_literal(parser, "(", 0)
    while cond764
        _t1401 = parse_formula(parser)
        item765 = _t1401
        push!(xs763, item765)
        cond764 = match_lookahead_literal(parser, "(", 0)
    end
    formulas766 = xs763
    consume_literal!(parser, ")")
    _t1402 = Proto.Conjunction(args=formulas766)
    result768 = _t1402
    record_span!(parser, span_start767, "Conjunction")
    return result768
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start773 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs769 = Proto.Formula[]
    cond770 = match_lookahead_literal(parser, "(", 0)
    while cond770
        _t1403 = parse_formula(parser)
        item771 = _t1403
        push!(xs769, item771)
        cond770 = match_lookahead_literal(parser, "(", 0)
    end
    formulas772 = xs769
    consume_literal!(parser, ")")
    _t1404 = Proto.Disjunction(args=formulas772)
    result774 = _t1404
    record_span!(parser, span_start773, "Disjunction")
    return result774
end

function parse_not(parser::ParserState)::Proto.Not
    span_start776 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1405 = parse_formula(parser)
    formula775 = _t1405
    consume_literal!(parser, ")")
    _t1406 = Proto.Not(arg=formula775)
    result777 = _t1406
    record_span!(parser, span_start776, "Not")
    return result777
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start781 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1407 = parse_name(parser)
    name778 = _t1407
    _t1408 = parse_ffi_args(parser)
    ffi_args779 = _t1408
    _t1409 = parse_terms(parser)
    terms780 = _t1409
    consume_literal!(parser, ")")
    _t1410 = Proto.FFI(name=name778, args=ffi_args779, terms=terms780)
    result782 = _t1410
    record_span!(parser, span_start781, "FFI")
    return result782
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol783 = consume_terminal!(parser, "SYMBOL")
    return symbol783
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs784 = Proto.Abstraction[]
    cond785 = match_lookahead_literal(parser, "(", 0)
    while cond785
        _t1411 = parse_abstraction(parser)
        item786 = _t1411
        push!(xs784, item786)
        cond785 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions787 = xs784
    consume_literal!(parser, ")")
    return abstractions787
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start793 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1412 = parse_relation_id(parser)
    relation_id788 = _t1412
    xs789 = Proto.Term[]
    cond790 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond790
        _t1413 = parse_term(parser)
        item791 = _t1413
        push!(xs789, item791)
        cond790 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms792 = xs789
    consume_literal!(parser, ")")
    _t1414 = Proto.Atom(name=relation_id788, terms=terms792)
    result794 = _t1414
    record_span!(parser, span_start793, "Atom")
    return result794
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start800 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1415 = parse_name(parser)
    name795 = _t1415
    xs796 = Proto.Term[]
    cond797 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond797
        _t1416 = parse_term(parser)
        item798 = _t1416
        push!(xs796, item798)
        cond797 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms799 = xs796
    consume_literal!(parser, ")")
    _t1417 = Proto.Pragma(name=name795, terms=terms799)
    result801 = _t1417
    record_span!(parser, span_start800, "Pragma")
    return result801
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start817 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1419 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1420 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1421 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1422 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1423 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1424 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1425 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1426 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1427 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1428 = 7
                                            else
                                                _t1428 = -1
                                            end
                                            _t1427 = _t1428
                                        end
                                        _t1426 = _t1427
                                    end
                                    _t1425 = _t1426
                                end
                                _t1424 = _t1425
                            end
                            _t1423 = _t1424
                        end
                        _t1422 = _t1423
                    end
                    _t1421 = _t1422
                end
                _t1420 = _t1421
            end
            _t1419 = _t1420
        end
        _t1418 = _t1419
    else
        _t1418 = -1
    end
    prediction802 = _t1418
    if prediction802 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1430 = parse_name(parser)
        name812 = _t1430
        xs813 = Proto.RelTerm[]
        cond814 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond814
            _t1431 = parse_rel_term(parser)
            item815 = _t1431
            push!(xs813, item815)
            cond814 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms816 = xs813
        consume_literal!(parser, ")")
        _t1432 = Proto.Primitive(name=name812, terms=rel_terms816)
        _t1429 = _t1432
    else
        if prediction802 == 8
            _t1434 = parse_divide(parser)
            divide811 = _t1434
            _t1433 = divide811
        else
            if prediction802 == 7
                _t1436 = parse_multiply(parser)
                multiply810 = _t1436
                _t1435 = multiply810
            else
                if prediction802 == 6
                    _t1438 = parse_minus(parser)
                    minus809 = _t1438
                    _t1437 = minus809
                else
                    if prediction802 == 5
                        _t1440 = parse_add(parser)
                        add808 = _t1440
                        _t1439 = add808
                    else
                        if prediction802 == 4
                            _t1442 = parse_gt_eq(parser)
                            gt_eq807 = _t1442
                            _t1441 = gt_eq807
                        else
                            if prediction802 == 3
                                _t1444 = parse_gt(parser)
                                gt806 = _t1444
                                _t1443 = gt806
                            else
                                if prediction802 == 2
                                    _t1446 = parse_lt_eq(parser)
                                    lt_eq805 = _t1446
                                    _t1445 = lt_eq805
                                else
                                    if prediction802 == 1
                                        _t1448 = parse_lt(parser)
                                        lt804 = _t1448
                                        _t1447 = lt804
                                    else
                                        if prediction802 == 0
                                            _t1450 = parse_eq(parser)
                                            eq803 = _t1450
                                            _t1449 = eq803
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1447 = _t1449
                                    end
                                    _t1445 = _t1447
                                end
                                _t1443 = _t1445
                            end
                            _t1441 = _t1443
                        end
                        _t1439 = _t1441
                    end
                    _t1437 = _t1439
                end
                _t1435 = _t1437
            end
            _t1433 = _t1435
        end
        _t1429 = _t1433
    end
    result818 = _t1429
    record_span!(parser, span_start817, "Primitive")
    return result818
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start821 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1451 = parse_term(parser)
    term819 = _t1451
    _t1452 = parse_term(parser)
    term_3820 = _t1452
    consume_literal!(parser, ")")
    _t1453 = Proto.RelTerm(rel_term_type=OneOf(:term, term819))
    _t1454 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3820))
    _t1455 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1453, _t1454])
    result822 = _t1455
    record_span!(parser, span_start821, "Primitive")
    return result822
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start825 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1456 = parse_term(parser)
    term823 = _t1456
    _t1457 = parse_term(parser)
    term_3824 = _t1457
    consume_literal!(parser, ")")
    _t1458 = Proto.RelTerm(rel_term_type=OneOf(:term, term823))
    _t1459 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3824))
    _t1460 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1458, _t1459])
    result826 = _t1460
    record_span!(parser, span_start825, "Primitive")
    return result826
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start829 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1461 = parse_term(parser)
    term827 = _t1461
    _t1462 = parse_term(parser)
    term_3828 = _t1462
    consume_literal!(parser, ")")
    _t1463 = Proto.RelTerm(rel_term_type=OneOf(:term, term827))
    _t1464 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3828))
    _t1465 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1463, _t1464])
    result830 = _t1465
    record_span!(parser, span_start829, "Primitive")
    return result830
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start833 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1466 = parse_term(parser)
    term831 = _t1466
    _t1467 = parse_term(parser)
    term_3832 = _t1467
    consume_literal!(parser, ")")
    _t1468 = Proto.RelTerm(rel_term_type=OneOf(:term, term831))
    _t1469 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3832))
    _t1470 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1468, _t1469])
    result834 = _t1470
    record_span!(parser, span_start833, "Primitive")
    return result834
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start837 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1471 = parse_term(parser)
    term835 = _t1471
    _t1472 = parse_term(parser)
    term_3836 = _t1472
    consume_literal!(parser, ")")
    _t1473 = Proto.RelTerm(rel_term_type=OneOf(:term, term835))
    _t1474 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3836))
    _t1475 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1473, _t1474])
    result838 = _t1475
    record_span!(parser, span_start837, "Primitive")
    return result838
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start842 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1476 = parse_term(parser)
    term839 = _t1476
    _t1477 = parse_term(parser)
    term_3840 = _t1477
    _t1478 = parse_term(parser)
    term_4841 = _t1478
    consume_literal!(parser, ")")
    _t1479 = Proto.RelTerm(rel_term_type=OneOf(:term, term839))
    _t1480 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3840))
    _t1481 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4841))
    _t1482 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1479, _t1480, _t1481])
    result843 = _t1482
    record_span!(parser, span_start842, "Primitive")
    return result843
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start847 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1483 = parse_term(parser)
    term844 = _t1483
    _t1484 = parse_term(parser)
    term_3845 = _t1484
    _t1485 = parse_term(parser)
    term_4846 = _t1485
    consume_literal!(parser, ")")
    _t1486 = Proto.RelTerm(rel_term_type=OneOf(:term, term844))
    _t1487 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3845))
    _t1488 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4846))
    _t1489 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1486, _t1487, _t1488])
    result848 = _t1489
    record_span!(parser, span_start847, "Primitive")
    return result848
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start852 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1490 = parse_term(parser)
    term849 = _t1490
    _t1491 = parse_term(parser)
    term_3850 = _t1491
    _t1492 = parse_term(parser)
    term_4851 = _t1492
    consume_literal!(parser, ")")
    _t1493 = Proto.RelTerm(rel_term_type=OneOf(:term, term849))
    _t1494 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3850))
    _t1495 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4851))
    _t1496 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1493, _t1494, _t1495])
    result853 = _t1496
    record_span!(parser, span_start852, "Primitive")
    return result853
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start857 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1497 = parse_term(parser)
    term854 = _t1497
    _t1498 = parse_term(parser)
    term_3855 = _t1498
    _t1499 = parse_term(parser)
    term_4856 = _t1499
    consume_literal!(parser, ")")
    _t1500 = Proto.RelTerm(rel_term_type=OneOf(:term, term854))
    _t1501 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3855))
    _t1502 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4856))
    _t1503 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1500, _t1501, _t1502])
    result858 = _t1503
    record_span!(parser, span_start857, "Primitive")
    return result858
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start862 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1504 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1505 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1506 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1507 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1508 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1509 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1510 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1511 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1512 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1513 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1514 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1515 = 1
                                                else
                                                    _t1515 = -1
                                                end
                                                _t1514 = _t1515
                                            end
                                            _t1513 = _t1514
                                        end
                                        _t1512 = _t1513
                                    end
                                    _t1511 = _t1512
                                end
                                _t1510 = _t1511
                            end
                            _t1509 = _t1510
                        end
                        _t1508 = _t1509
                    end
                    _t1507 = _t1508
                end
                _t1506 = _t1507
            end
            _t1505 = _t1506
        end
        _t1504 = _t1505
    end
    prediction859 = _t1504
    if prediction859 == 1
        _t1517 = parse_term(parser)
        term861 = _t1517
        _t1518 = Proto.RelTerm(rel_term_type=OneOf(:term, term861))
        _t1516 = _t1518
    else
        if prediction859 == 0
            _t1520 = parse_specialized_value(parser)
            specialized_value860 = _t1520
            _t1521 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value860))
            _t1519 = _t1521
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1516 = _t1519
    end
    result863 = _t1516
    record_span!(parser, span_start862, "RelTerm")
    return result863
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start865 = span_start(parser)
    consume_literal!(parser, "#")
    _t1522 = parse_value(parser)
    value864 = _t1522
    result866 = value864
    record_span!(parser, span_start865, "Value")
    return result866
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start872 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1523 = parse_name(parser)
    name867 = _t1523
    xs868 = Proto.RelTerm[]
    cond869 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond869
        _t1524 = parse_rel_term(parser)
        item870 = _t1524
        push!(xs868, item870)
        cond869 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms871 = xs868
    consume_literal!(parser, ")")
    _t1525 = Proto.RelAtom(name=name867, terms=rel_terms871)
    result873 = _t1525
    record_span!(parser, span_start872, "RelAtom")
    return result873
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start876 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1526 = parse_term(parser)
    term874 = _t1526
    _t1527 = parse_term(parser)
    term_3875 = _t1527
    consume_literal!(parser, ")")
    _t1528 = Proto.Cast(input=term874, result=term_3875)
    result877 = _t1528
    record_span!(parser, span_start876, "Cast")
    return result877
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs878 = Proto.Attribute[]
    cond879 = match_lookahead_literal(parser, "(", 0)
    while cond879
        _t1529 = parse_attribute(parser)
        item880 = _t1529
        push!(xs878, item880)
        cond879 = match_lookahead_literal(parser, "(", 0)
    end
    attributes881 = xs878
    consume_literal!(parser, ")")
    return attributes881
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start887 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1530 = parse_name(parser)
    name882 = _t1530
    xs883 = Proto.Value[]
    cond884 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond884
        _t1531 = parse_value(parser)
        item885 = _t1531
        push!(xs883, item885)
        cond884 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values886 = xs883
    consume_literal!(parser, ")")
    _t1532 = Proto.Attribute(name=name882, args=values886)
    result888 = _t1532
    record_span!(parser, span_start887, "Attribute")
    return result888
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start894 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs889 = Proto.RelationId[]
    cond890 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond890
        _t1533 = parse_relation_id(parser)
        item891 = _t1533
        push!(xs889, item891)
        cond890 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids892 = xs889
    _t1534 = parse_script(parser)
    script893 = _t1534
    consume_literal!(parser, ")")
    _t1535 = Proto.Algorithm(var"#global"=relation_ids892, body=script893)
    result895 = _t1535
    record_span!(parser, span_start894, "Algorithm")
    return result895
end

function parse_script(parser::ParserState)::Proto.Script
    span_start900 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs896 = Proto.Construct[]
    cond897 = match_lookahead_literal(parser, "(", 0)
    while cond897
        _t1536 = parse_construct(parser)
        item898 = _t1536
        push!(xs896, item898)
        cond897 = match_lookahead_literal(parser, "(", 0)
    end
    constructs899 = xs896
    consume_literal!(parser, ")")
    _t1537 = Proto.Script(constructs=constructs899)
    result901 = _t1537
    record_span!(parser, span_start900, "Script")
    return result901
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start905 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1539 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1540 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1541 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1542 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1543 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1544 = 1
                            else
                                _t1544 = -1
                            end
                            _t1543 = _t1544
                        end
                        _t1542 = _t1543
                    end
                    _t1541 = _t1542
                end
                _t1540 = _t1541
            end
            _t1539 = _t1540
        end
        _t1538 = _t1539
    else
        _t1538 = -1
    end
    prediction902 = _t1538
    if prediction902 == 1
        _t1546 = parse_instruction(parser)
        instruction904 = _t1546
        _t1547 = Proto.Construct(construct_type=OneOf(:instruction, instruction904))
        _t1545 = _t1547
    else
        if prediction902 == 0
            _t1549 = parse_loop(parser)
            loop903 = _t1549
            _t1550 = Proto.Construct(construct_type=OneOf(:loop, loop903))
            _t1548 = _t1550
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1545 = _t1548
    end
    result906 = _t1545
    record_span!(parser, span_start905, "Construct")
    return result906
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start909 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1551 = parse_init(parser)
    init907 = _t1551
    _t1552 = parse_script(parser)
    script908 = _t1552
    consume_literal!(parser, ")")
    _t1553 = Proto.Loop(init=init907, body=script908)
    result910 = _t1553
    record_span!(parser, span_start909, "Loop")
    return result910
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs911 = Proto.Instruction[]
    cond912 = match_lookahead_literal(parser, "(", 0)
    while cond912
        _t1554 = parse_instruction(parser)
        item913 = _t1554
        push!(xs911, item913)
        cond912 = match_lookahead_literal(parser, "(", 0)
    end
    instructions914 = xs911
    consume_literal!(parser, ")")
    return instructions914
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start921 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1556 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1557 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1558 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1559 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1560 = 0
                        else
                            _t1560 = -1
                        end
                        _t1559 = _t1560
                    end
                    _t1558 = _t1559
                end
                _t1557 = _t1558
            end
            _t1556 = _t1557
        end
        _t1555 = _t1556
    else
        _t1555 = -1
    end
    prediction915 = _t1555
    if prediction915 == 4
        _t1562 = parse_monus_def(parser)
        monus_def920 = _t1562
        _t1563 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def920))
        _t1561 = _t1563
    else
        if prediction915 == 3
            _t1565 = parse_monoid_def(parser)
            monoid_def919 = _t1565
            _t1566 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def919))
            _t1564 = _t1566
        else
            if prediction915 == 2
                _t1568 = parse_break(parser)
                break918 = _t1568
                _t1569 = Proto.Instruction(instr_type=OneOf(:var"#break", break918))
                _t1567 = _t1569
            else
                if prediction915 == 1
                    _t1571 = parse_upsert(parser)
                    upsert917 = _t1571
                    _t1572 = Proto.Instruction(instr_type=OneOf(:upsert, upsert917))
                    _t1570 = _t1572
                else
                    if prediction915 == 0
                        _t1574 = parse_assign(parser)
                        assign916 = _t1574
                        _t1575 = Proto.Instruction(instr_type=OneOf(:assign, assign916))
                        _t1573 = _t1575
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1570 = _t1573
                end
                _t1567 = _t1570
            end
            _t1564 = _t1567
        end
        _t1561 = _t1564
    end
    result922 = _t1561
    record_span!(parser, span_start921, "Instruction")
    return result922
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start926 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1576 = parse_relation_id(parser)
    relation_id923 = _t1576
    _t1577 = parse_abstraction(parser)
    abstraction924 = _t1577
    if match_lookahead_literal(parser, "(", 0)
        _t1579 = parse_attrs(parser)
        _t1578 = _t1579
    else
        _t1578 = nothing
    end
    attrs925 = _t1578
    consume_literal!(parser, ")")
    _t1580 = Proto.Assign(name=relation_id923, body=abstraction924, attrs=(!isnothing(attrs925) ? attrs925 : Proto.Attribute[]))
    result927 = _t1580
    record_span!(parser, span_start926, "Assign")
    return result927
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start931 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1581 = parse_relation_id(parser)
    relation_id928 = _t1581
    _t1582 = parse_abstraction_with_arity(parser)
    abstraction_with_arity929 = _t1582
    if match_lookahead_literal(parser, "(", 0)
        _t1584 = parse_attrs(parser)
        _t1583 = _t1584
    else
        _t1583 = nothing
    end
    attrs930 = _t1583
    consume_literal!(parser, ")")
    _t1585 = Proto.Upsert(name=relation_id928, body=abstraction_with_arity929[1], attrs=(!isnothing(attrs930) ? attrs930 : Proto.Attribute[]), value_arity=abstraction_with_arity929[2])
    result932 = _t1585
    record_span!(parser, span_start931, "Upsert")
    return result932
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1586 = parse_bindings(parser)
    bindings933 = _t1586
    _t1587 = parse_formula(parser)
    formula934 = _t1587
    consume_literal!(parser, ")")
    _t1588 = Proto.Abstraction(vars=vcat(bindings933[1], !isnothing(bindings933[2]) ? bindings933[2] : []), value=formula934)
    return (_t1588, length(bindings933[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start938 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1589 = parse_relation_id(parser)
    relation_id935 = _t1589
    _t1590 = parse_abstraction(parser)
    abstraction936 = _t1590
    if match_lookahead_literal(parser, "(", 0)
        _t1592 = parse_attrs(parser)
        _t1591 = _t1592
    else
        _t1591 = nothing
    end
    attrs937 = _t1591
    consume_literal!(parser, ")")
    _t1593 = Proto.Break(name=relation_id935, body=abstraction936, attrs=(!isnothing(attrs937) ? attrs937 : Proto.Attribute[]))
    result939 = _t1593
    record_span!(parser, span_start938, "Break")
    return result939
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start944 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1594 = parse_monoid(parser)
    monoid940 = _t1594
    _t1595 = parse_relation_id(parser)
    relation_id941 = _t1595
    _t1596 = parse_abstraction_with_arity(parser)
    abstraction_with_arity942 = _t1596
    if match_lookahead_literal(parser, "(", 0)
        _t1598 = parse_attrs(parser)
        _t1597 = _t1598
    else
        _t1597 = nothing
    end
    attrs943 = _t1597
    consume_literal!(parser, ")")
    _t1599 = Proto.MonoidDef(monoid=monoid940, name=relation_id941, body=abstraction_with_arity942[1], attrs=(!isnothing(attrs943) ? attrs943 : Proto.Attribute[]), value_arity=abstraction_with_arity942[2])
    result945 = _t1599
    record_span!(parser, span_start944, "MonoidDef")
    return result945
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start951 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1601 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1602 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1603 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1604 = 2
                    else
                        _t1604 = -1
                    end
                    _t1603 = _t1604
                end
                _t1602 = _t1603
            end
            _t1601 = _t1602
        end
        _t1600 = _t1601
    else
        _t1600 = -1
    end
    prediction946 = _t1600
    if prediction946 == 3
        _t1606 = parse_sum_monoid(parser)
        sum_monoid950 = _t1606
        _t1607 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid950))
        _t1605 = _t1607
    else
        if prediction946 == 2
            _t1609 = parse_max_monoid(parser)
            max_monoid949 = _t1609
            _t1610 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid949))
            _t1608 = _t1610
        else
            if prediction946 == 1
                _t1612 = parse_min_monoid(parser)
                min_monoid948 = _t1612
                _t1613 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid948))
                _t1611 = _t1613
            else
                if prediction946 == 0
                    _t1615 = parse_or_monoid(parser)
                    or_monoid947 = _t1615
                    _t1616 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid947))
                    _t1614 = _t1616
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1611 = _t1614
            end
            _t1608 = _t1611
        end
        _t1605 = _t1608
    end
    result952 = _t1605
    record_span!(parser, span_start951, "Monoid")
    return result952
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start953 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1617 = Proto.OrMonoid()
    result954 = _t1617
    record_span!(parser, span_start953, "OrMonoid")
    return result954
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start956 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1618 = parse_type(parser)
    type955 = _t1618
    consume_literal!(parser, ")")
    _t1619 = Proto.MinMonoid(var"#type"=type955)
    result957 = _t1619
    record_span!(parser, span_start956, "MinMonoid")
    return result957
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start959 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1620 = parse_type(parser)
    type958 = _t1620
    consume_literal!(parser, ")")
    _t1621 = Proto.MaxMonoid(var"#type"=type958)
    result960 = _t1621
    record_span!(parser, span_start959, "MaxMonoid")
    return result960
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start962 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1622 = parse_type(parser)
    type961 = _t1622
    consume_literal!(parser, ")")
    _t1623 = Proto.SumMonoid(var"#type"=type961)
    result963 = _t1623
    record_span!(parser, span_start962, "SumMonoid")
    return result963
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start968 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1624 = parse_monoid(parser)
    monoid964 = _t1624
    _t1625 = parse_relation_id(parser)
    relation_id965 = _t1625
    _t1626 = parse_abstraction_with_arity(parser)
    abstraction_with_arity966 = _t1626
    if match_lookahead_literal(parser, "(", 0)
        _t1628 = parse_attrs(parser)
        _t1627 = _t1628
    else
        _t1627 = nothing
    end
    attrs967 = _t1627
    consume_literal!(parser, ")")
    _t1629 = Proto.MonusDef(monoid=monoid964, name=relation_id965, body=abstraction_with_arity966[1], attrs=(!isnothing(attrs967) ? attrs967 : Proto.Attribute[]), value_arity=abstraction_with_arity966[2])
    result969 = _t1629
    record_span!(parser, span_start968, "MonusDef")
    return result969
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1630 = parse_relation_id(parser)
    relation_id970 = _t1630
    _t1631 = parse_abstraction(parser)
    abstraction971 = _t1631
    _t1632 = parse_functional_dependency_keys(parser)
    functional_dependency_keys972 = _t1632
    _t1633 = parse_functional_dependency_values(parser)
    functional_dependency_values973 = _t1633
    consume_literal!(parser, ")")
    _t1634 = Proto.FunctionalDependency(guard=abstraction971, keys=functional_dependency_keys972, values=functional_dependency_values973)
    _t1635 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1634), name=relation_id970)
    result975 = _t1635
    record_span!(parser, span_start974, "Constraint")
    return result975
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs976 = Proto.Var[]
    cond977 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond977
        _t1636 = parse_var(parser)
        item978 = _t1636
        push!(xs976, item978)
        cond977 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars979 = xs976
    consume_literal!(parser, ")")
    return vars979
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs980 = Proto.Var[]
    cond981 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond981
        _t1637 = parse_var(parser)
        item982 = _t1637
        push!(xs980, item982)
        cond981 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars983 = xs980
    consume_literal!(parser, ")")
    return vars983
end

function parse_data(parser::ParserState)::Proto.Data
    span_start988 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "edb", 1)
            _t1639 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1640 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1641 = 1
                else
                    _t1641 = -1
                end
                _t1640 = _t1641
            end
            _t1639 = _t1640
        end
        _t1638 = _t1639
    else
        _t1638 = -1
    end
    prediction984 = _t1638
    if prediction984 == 2
        _t1643 = parse_csv_data(parser)
        csv_data987 = _t1643
        _t1644 = Proto.Data(data_type=OneOf(:csv_data, csv_data987))
        _t1642 = _t1644
    else
        if prediction984 == 1
            _t1646 = parse_betree_relation(parser)
            betree_relation986 = _t1646
            _t1647 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation986))
            _t1645 = _t1647
        else
            if prediction984 == 0
                _t1649 = parse_edb(parser)
                edb985 = _t1649
                _t1650 = Proto.Data(data_type=OneOf(:edb, edb985))
                _t1648 = _t1650
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1645 = _t1648
        end
        _t1642 = _t1645
    end
    result989 = _t1642
    record_span!(parser, span_start988, "Data")
    return result989
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start993 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1651 = parse_relation_id(parser)
    relation_id990 = _t1651
    _t1652 = parse_edb_path(parser)
    edb_path991 = _t1652
    _t1653 = parse_edb_types(parser)
    edb_types992 = _t1653
    consume_literal!(parser, ")")
    _t1654 = Proto.EDB(target_id=relation_id990, path=edb_path991, types=edb_types992)
    result994 = _t1654
    record_span!(parser, span_start993, "EDB")
    return result994
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs995 = String[]
    cond996 = match_lookahead_terminal(parser, "STRING", 0)
    while cond996
        item997 = consume_terminal!(parser, "STRING")
        push!(xs995, item997)
        cond996 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings998 = xs995
    consume_literal!(parser, "]")
    return strings998
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs999 = Proto.var"#Type"[]
    cond1000 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1000
        _t1655 = parse_type(parser)
        item1001 = _t1655
        push!(xs999, item1001)
        cond1000 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1002 = xs999
    consume_literal!(parser, "]")
    return types1002
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1005 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1656 = parse_relation_id(parser)
    relation_id1003 = _t1656
    _t1657 = parse_betree_info(parser)
    betree_info1004 = _t1657
    consume_literal!(parser, ")")
    _t1658 = Proto.BeTreeRelation(name=relation_id1003, relation_info=betree_info1004)
    result1006 = _t1658
    record_span!(parser, span_start1005, "BeTreeRelation")
    return result1006
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1010 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1659 = parse_betree_info_key_types(parser)
    betree_info_key_types1007 = _t1659
    _t1660 = parse_betree_info_value_types(parser)
    betree_info_value_types1008 = _t1660
    _t1661 = parse_config_dict(parser)
    config_dict1009 = _t1661
    consume_literal!(parser, ")")
    _t1662 = construct_betree_info(parser, betree_info_key_types1007, betree_info_value_types1008, config_dict1009)
    result1011 = _t1662
    record_span!(parser, span_start1010, "BeTreeInfo")
    return result1011
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1012 = Proto.var"#Type"[]
    cond1013 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1013
        _t1663 = parse_type(parser)
        item1014 = _t1663
        push!(xs1012, item1014)
        cond1013 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1015 = xs1012
    consume_literal!(parser, ")")
    return types1015
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1016 = Proto.var"#Type"[]
    cond1017 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1017
        _t1664 = parse_type(parser)
        item1018 = _t1664
        push!(xs1016, item1018)
        cond1017 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1019 = xs1016
    consume_literal!(parser, ")")
    return types1019
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1024 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1665 = parse_csvlocator(parser)
    csvlocator1020 = _t1665
    _t1666 = parse_csv_config(parser)
    csv_config1021 = _t1666
    _t1667 = parse_gnf_columns(parser)
    gnf_columns1022 = _t1667
    _t1668 = parse_csv_asof(parser)
    csv_asof1023 = _t1668
    consume_literal!(parser, ")")
    _t1669 = Proto.CSVData(locator=csvlocator1020, config=csv_config1021, columns=gnf_columns1022, asof=csv_asof1023)
    result1025 = _t1669
    record_span!(parser, span_start1024, "CSVData")
    return result1025
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1028 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1671 = parse_csv_locator_paths(parser)
        _t1670 = _t1671
    else
        _t1670 = nothing
    end
    csv_locator_paths1026 = _t1670
    if match_lookahead_literal(parser, "(", 0)
        _t1673 = parse_csv_locator_inline_data(parser)
        _t1672 = _t1673
    else
        _t1672 = nothing
    end
    csv_locator_inline_data1027 = _t1672
    consume_literal!(parser, ")")
    _t1674 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1026) ? csv_locator_paths1026 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1027) ? csv_locator_inline_data1027 : "")))
    result1029 = _t1674
    record_span!(parser, span_start1028, "CSVLocator")
    return result1029
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1030 = String[]
    cond1031 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1031
        item1032 = consume_terminal!(parser, "STRING")
        push!(xs1030, item1032)
        cond1031 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1033 = xs1030
    consume_literal!(parser, ")")
    return strings1033
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1034 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1034
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1036 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1675 = parse_config_dict(parser)
    config_dict1035 = _t1675
    consume_literal!(parser, ")")
    _t1676 = construct_csv_config(parser, config_dict1035)
    result1037 = _t1676
    record_span!(parser, span_start1036, "CSVConfig")
    return result1037
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1038 = Proto.GNFColumn[]
    cond1039 = match_lookahead_literal(parser, "(", 0)
    while cond1039
        _t1677 = parse_gnf_column(parser)
        item1040 = _t1677
        push!(xs1038, item1040)
        cond1039 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1041 = xs1038
    consume_literal!(parser, ")")
    return gnf_columns1041
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1048 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1678 = parse_gnf_column_path(parser)
    gnf_column_path1042 = _t1678
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1680 = parse_relation_id(parser)
        _t1679 = _t1680
    else
        _t1679 = nothing
    end
    relation_id1043 = _t1679
    consume_literal!(parser, "[")
    xs1044 = Proto.var"#Type"[]
    cond1045 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1045
        _t1681 = parse_type(parser)
        item1046 = _t1681
        push!(xs1044, item1046)
        cond1045 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1047 = xs1044
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1682 = Proto.GNFColumn(column_path=gnf_column_path1042, target_id=relation_id1043, types=types1047)
    result1049 = _t1682
    record_span!(parser, span_start1048, "GNFColumn")
    return result1049
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1683 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1684 = 0
        else
            _t1684 = -1
        end
        _t1683 = _t1684
    end
    prediction1050 = _t1683
    if prediction1050 == 1
        consume_literal!(parser, "[")
        xs1052 = String[]
        cond1053 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1053
            item1054 = consume_terminal!(parser, "STRING")
            push!(xs1052, item1054)
            cond1053 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1055 = xs1052
        consume_literal!(parser, "]")
        _t1685 = strings1055
    else
        if prediction1050 == 0
            string1051 = consume_terminal!(parser, "STRING")
            _t1686 = String[string1051]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1685 = _t1686
    end
    return _t1685
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1056 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1056
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1058 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1687 = parse_fragment_id(parser)
    fragment_id1057 = _t1687
    consume_literal!(parser, ")")
    _t1688 = Proto.Undefine(fragment_id=fragment_id1057)
    result1059 = _t1688
    record_span!(parser, span_start1058, "Undefine")
    return result1059
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1064 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1060 = Proto.RelationId[]
    cond1061 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1061
        _t1689 = parse_relation_id(parser)
        item1062 = _t1689
        push!(xs1060, item1062)
        cond1061 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1063 = xs1060
    consume_literal!(parser, ")")
    _t1690 = Proto.Context(relations=relation_ids1063)
    result1065 = _t1690
    record_span!(parser, span_start1064, "Context")
    return result1065
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1070 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1066 = Proto.SnapshotMapping[]
    cond1067 = match_lookahead_literal(parser, "[", 0)
    while cond1067
        _t1691 = parse_snapshot_mapping(parser)
        item1068 = _t1691
        push!(xs1066, item1068)
        cond1067 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1069 = xs1066
    consume_literal!(parser, ")")
    _t1692 = Proto.Snapshot(mappings=snapshot_mappings1069)
    result1071 = _t1692
    record_span!(parser, span_start1070, "Snapshot")
    return result1071
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1074 = span_start(parser)
    _t1693 = parse_edb_path(parser)
    edb_path1072 = _t1693
    _t1694 = parse_relation_id(parser)
    relation_id1073 = _t1694
    _t1695 = Proto.SnapshotMapping(destination_path=edb_path1072, source_relation=relation_id1073)
    result1075 = _t1695
    record_span!(parser, span_start1074, "SnapshotMapping")
    return result1075
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1076 = Proto.Read[]
    cond1077 = match_lookahead_literal(parser, "(", 0)
    while cond1077
        _t1696 = parse_read(parser)
        item1078 = _t1696
        push!(xs1076, item1078)
        cond1077 = match_lookahead_literal(parser, "(", 0)
    end
    reads1079 = xs1076
    consume_literal!(parser, ")")
    return reads1079
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1086 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1698 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1699 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1700 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1701 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1702 = 3
                        else
                            _t1702 = -1
                        end
                        _t1701 = _t1702
                    end
                    _t1700 = _t1701
                end
                _t1699 = _t1700
            end
            _t1698 = _t1699
        end
        _t1697 = _t1698
    else
        _t1697 = -1
    end
    prediction1080 = _t1697
    if prediction1080 == 4
        _t1704 = parse_export(parser)
        export1085 = _t1704
        _t1705 = Proto.Read(read_type=OneOf(:var"#export", export1085))
        _t1703 = _t1705
    else
        if prediction1080 == 3
            _t1707 = parse_abort(parser)
            abort1084 = _t1707
            _t1708 = Proto.Read(read_type=OneOf(:abort, abort1084))
            _t1706 = _t1708
        else
            if prediction1080 == 2
                _t1710 = parse_what_if(parser)
                what_if1083 = _t1710
                _t1711 = Proto.Read(read_type=OneOf(:what_if, what_if1083))
                _t1709 = _t1711
            else
                if prediction1080 == 1
                    _t1713 = parse_output(parser)
                    output1082 = _t1713
                    _t1714 = Proto.Read(read_type=OneOf(:output, output1082))
                    _t1712 = _t1714
                else
                    if prediction1080 == 0
                        _t1716 = parse_demand(parser)
                        demand1081 = _t1716
                        _t1717 = Proto.Read(read_type=OneOf(:demand, demand1081))
                        _t1715 = _t1717
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1712 = _t1715
                end
                _t1709 = _t1712
            end
            _t1706 = _t1709
        end
        _t1703 = _t1706
    end
    result1087 = _t1703
    record_span!(parser, span_start1086, "Read")
    return result1087
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1089 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1718 = parse_relation_id(parser)
    relation_id1088 = _t1718
    consume_literal!(parser, ")")
    _t1719 = Proto.Demand(relation_id=relation_id1088)
    result1090 = _t1719
    record_span!(parser, span_start1089, "Demand")
    return result1090
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1093 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1720 = parse_name(parser)
    name1091 = _t1720
    _t1721 = parse_relation_id(parser)
    relation_id1092 = _t1721
    consume_literal!(parser, ")")
    _t1722 = Proto.Output(name=name1091, relation_id=relation_id1092)
    result1094 = _t1722
    record_span!(parser, span_start1093, "Output")
    return result1094
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1097 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1723 = parse_name(parser)
    name1095 = _t1723
    _t1724 = parse_epoch(parser)
    epoch1096 = _t1724
    consume_literal!(parser, ")")
    _t1725 = Proto.WhatIf(branch=name1095, epoch=epoch1096)
    result1098 = _t1725
    record_span!(parser, span_start1097, "WhatIf")
    return result1098
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1101 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1727 = parse_name(parser)
        _t1726 = _t1727
    else
        _t1726 = nothing
    end
    name1099 = _t1726
    _t1728 = parse_relation_id(parser)
    relation_id1100 = _t1728
    consume_literal!(parser, ")")
    _t1729 = Proto.Abort(name=(!isnothing(name1099) ? name1099 : "abort"), relation_id=relation_id1100)
    result1102 = _t1729
    record_span!(parser, span_start1101, "Abort")
    return result1102
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1104 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1730 = parse_export_csv_config(parser)
    export_csv_config1103 = _t1730
    consume_literal!(parser, ")")
    _t1731 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1103))
    result1105 = _t1731
    record_span!(parser, span_start1104, "Export")
    return result1105
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1113 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1733 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1734 = 1
            else
                _t1734 = -1
            end
            _t1733 = _t1734
        end
        _t1732 = _t1733
    else
        _t1732 = -1
    end
    prediction1106 = _t1732
    if prediction1106 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1736 = parse_export_csv_path(parser)
        export_csv_path1110 = _t1736
        _t1737 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1111 = _t1737
        _t1738 = parse_config_dict(parser)
        config_dict1112 = _t1738
        consume_literal!(parser, ")")
        _t1739 = construct_export_csv_config(parser, export_csv_path1110, export_csv_columns_list1111, config_dict1112)
        _t1735 = _t1739
    else
        if prediction1106 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1741 = parse_export_csv_path(parser)
            export_csv_path1107 = _t1741
            _t1742 = parse_export_csv_source(parser)
            export_csv_source1108 = _t1742
            _t1743 = parse_csv_config(parser)
            csv_config1109 = _t1743
            consume_literal!(parser, ")")
            _t1744 = construct_export_csv_config_with_source(parser, export_csv_path1107, export_csv_source1108, csv_config1109)
            _t1740 = _t1744
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1735 = _t1740
    end
    result1114 = _t1735
    record_span!(parser, span_start1113, "ExportCSVConfig")
    return result1114
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1115 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1115
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1122 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1746 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1747 = 0
            else
                _t1747 = -1
            end
            _t1746 = _t1747
        end
        _t1745 = _t1746
    else
        _t1745 = -1
    end
    prediction1116 = _t1745
    if prediction1116 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1749 = parse_relation_id(parser)
        relation_id1121 = _t1749
        consume_literal!(parser, ")")
        _t1750 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1121))
        _t1748 = _t1750
    else
        if prediction1116 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1117 = Proto.ExportCSVColumn[]
            cond1118 = match_lookahead_literal(parser, "(", 0)
            while cond1118
                _t1752 = parse_export_csv_column(parser)
                item1119 = _t1752
                push!(xs1117, item1119)
                cond1118 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1120 = xs1117
            consume_literal!(parser, ")")
            _t1753 = Proto.ExportCSVColumns(columns=export_csv_columns1120)
            _t1754 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1753))
            _t1751 = _t1754
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1748 = _t1751
    end
    result1123 = _t1748
    record_span!(parser, span_start1122, "ExportCSVSource")
    return result1123
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1126 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1124 = consume_terminal!(parser, "STRING")
    _t1755 = parse_relation_id(parser)
    relation_id1125 = _t1755
    consume_literal!(parser, ")")
    _t1756 = Proto.ExportCSVColumn(column_name=string1124, column_data=relation_id1125)
    result1127 = _t1756
    record_span!(parser, span_start1126, "ExportCSVColumn")
    return result1127
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1128 = Proto.ExportCSVColumn[]
    cond1129 = match_lookahead_literal(parser, "(", 0)
    while cond1129
        _t1757 = parse_export_csv_column(parser)
        item1130 = _t1757
        push!(xs1128, item1130)
        cond1129 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1131 = xs1128
    consume_literal!(parser, ")")
    return export_csv_columns1131
end


function parse_transaction(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens, input)
    result = parse_transaction(parser)
    # Check for unconsumed tokens (except EOF)
    if parser.pos <= length(parser.tokens)
        remaining_token = lookahead(parser, 0)
        if remaining_token.type != "\$"
            throw(ParseError("Unexpected token at end of input: $remaining_token"))
        end
    end
    return result, parser.provenance
end

function parse_fragment(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens, input)
    result = parse_fragment(parser)
    # Check for unconsumed tokens (except EOF)
    if parser.pos <= length(parser.tokens)
        remaining_token = lookahead(parser, 0)
        if remaining_token.type != "\$"
            throw(ParseError("Unexpected token at end of input: $remaining_token"))
        end
    end
    return result, parser.provenance
end

function parse(input::String)
    return parse_transaction(input)
end

# Export main parse functions and error type
export parse, parse_transaction, parse_fragment, ParseError
# Export scanner functions for testing
export scan_string, scan_int, scan_float, scan_int128, scan_uint128, scan_decimal
# Export Lexer and provenance types for testing
export Lexer, Location, Span

end # module Parser
