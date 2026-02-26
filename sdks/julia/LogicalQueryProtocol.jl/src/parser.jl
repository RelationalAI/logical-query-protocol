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
    provenance::Dict{Tuple{Vararg{Int}},Span}
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

function record_span!(parser::ParserState, start_offset::Int)
    if parser.pos > 1
        end_offset = parser.tokens[parser.pos - 1].end_pos
    else
        end_offset = start_offset
    end
    s = Span(_make_location(parser, start_offset), _make_location(parser, end_offset))
    parser.provenance[tuple()] = s
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
        _t1783 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1784 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1785 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1786 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1787 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1788 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1789 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1790 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1791 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1792 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1792
    _t1793 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1793
    _t1794 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1794
    _t1795 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1795
    _t1796 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1796
    _t1797 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1797
    _t1798 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1798
    _t1799 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1799
    _t1800 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1800
    _t1801 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1801
    _t1802 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1802
    _t1803 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1803
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1804 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1804
    _t1805 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1805
    _t1806 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1806
    _t1807 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1807
    _t1808 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1808
    _t1809 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1809
    _t1810 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1810
    _t1811 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1811
    _t1812 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1812
    _t1813 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1813
    _t1814 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1814
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1815 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1815
    _t1816 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1816
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
    _t1817 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1817
    _t1818 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1818
    _t1819 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1819
end

function export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1820 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1820
    _t1821 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1821
    _t1822 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1822
    _t1823 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1823
    _t1824 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1824
    _t1825 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1825
    _t1826 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1826
    _t1827 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1827
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start598 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1185 = parse_configure(parser)
        _t1184 = _t1185
    else
        _t1184 = nothing
    end
    configure592 = _t1184
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1187 = parse_sync(parser)
        _t1186 = _t1187
    else
        _t1186 = nothing
    end
    sync593 = _t1186
    xs594 = Proto.Epoch[]
    cond595 = match_lookahead_literal(parser, "(", 0)
    while cond595
        _t1188 = parse_epoch(parser)
        item596 = _t1188
        push!(xs594, item596)
        cond595 = match_lookahead_literal(parser, "(", 0)
    end
    epochs597 = xs594
    consume_literal!(parser, ")")
    _t1189 = default_configure(parser)
    _t1190 = Proto.Transaction(epochs=epochs597, configure=(!isnothing(configure592) ? configure592 : _t1189), sync=sync593)
    result599 = _t1190
    record_span!(parser, span_start598)
    return result599
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start601 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1191 = parse_config_dict(parser)
    config_dict600 = _t1191
    consume_literal!(parser, ")")
    _t1192 = construct_configure(parser, config_dict600)
    result602 = _t1192
    record_span!(parser, span_start601)
    return result602
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    span_start607 = span_start(parser)
    consume_literal!(parser, "{")
    xs603 = Tuple{String, Proto.Value}[]
    cond604 = match_lookahead_literal(parser, ":", 0)
    while cond604
        _t1193 = parse_config_key_value(parser)
        item605 = _t1193
        push!(xs603, item605)
        cond604 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values606 = xs603
    consume_literal!(parser, "}")
    result608 = config_key_values606
    record_span!(parser, span_start607)
    return result608
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    span_start611 = span_start(parser)
    consume_literal!(parser, ":")
    symbol609 = consume_terminal!(parser, "SYMBOL")
    _t1194 = parse_value(parser)
    value610 = _t1194
    result612 = (symbol609, value610,)
    record_span!(parser, span_start611)
    return result612
end

function parse_value(parser::ParserState)::Proto.Value
    span_start623 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1195 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1196 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1197 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1199 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1200 = 0
                        else
                            _t1200 = -1
                        end
                        _t1199 = _t1200
                    end
                    _t1198 = _t1199
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1201 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1202 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t1203 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t1204 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t1205 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t1206 = 7
                                        else
                                            _t1206 = -1
                                        end
                                        _t1205 = _t1206
                                    end
                                    _t1204 = _t1205
                                end
                                _t1203 = _t1204
                            end
                            _t1202 = _t1203
                        end
                        _t1201 = _t1202
                    end
                    _t1198 = _t1201
                end
                _t1197 = _t1198
            end
            _t1196 = _t1197
        end
        _t1195 = _t1196
    end
    prediction613 = _t1195
    if prediction613 == 9
        _t1208 = parse_boolean_value(parser)
        boolean_value622 = _t1208
        _t1209 = Proto.Value(value=OneOf(:boolean_value, boolean_value622))
        _t1207 = _t1209
    else
        if prediction613 == 8
            consume_literal!(parser, "missing")
            _t1211 = Proto.MissingValue()
            _t1212 = Proto.Value(value=OneOf(:missing_value, _t1211))
            _t1210 = _t1212
        else
            if prediction613 == 7
                decimal621 = consume_terminal!(parser, "DECIMAL")
                _t1214 = Proto.Value(value=OneOf(:decimal_value, decimal621))
                _t1213 = _t1214
            else
                if prediction613 == 6
                    int128620 = consume_terminal!(parser, "INT128")
                    _t1216 = Proto.Value(value=OneOf(:int128_value, int128620))
                    _t1215 = _t1216
                else
                    if prediction613 == 5
                        uint128619 = consume_terminal!(parser, "UINT128")
                        _t1218 = Proto.Value(value=OneOf(:uint128_value, uint128619))
                        _t1217 = _t1218
                    else
                        if prediction613 == 4
                            float618 = consume_terminal!(parser, "FLOAT")
                            _t1220 = Proto.Value(value=OneOf(:float_value, float618))
                            _t1219 = _t1220
                        else
                            if prediction613 == 3
                                int617 = consume_terminal!(parser, "INT")
                                _t1222 = Proto.Value(value=OneOf(:int_value, int617))
                                _t1221 = _t1222
                            else
                                if prediction613 == 2
                                    string616 = consume_terminal!(parser, "STRING")
                                    _t1224 = Proto.Value(value=OneOf(:string_value, string616))
                                    _t1223 = _t1224
                                else
                                    if prediction613 == 1
                                        _t1226 = parse_datetime(parser)
                                        datetime615 = _t1226
                                        _t1227 = Proto.Value(value=OneOf(:datetime_value, datetime615))
                                        _t1225 = _t1227
                                    else
                                        if prediction613 == 0
                                            _t1229 = parse_date(parser)
                                            date614 = _t1229
                                            _t1230 = Proto.Value(value=OneOf(:date_value, date614))
                                            _t1228 = _t1230
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1225 = _t1228
                                    end
                                    _t1223 = _t1225
                                end
                                _t1221 = _t1223
                            end
                            _t1219 = _t1221
                        end
                        _t1217 = _t1219
                    end
                    _t1215 = _t1217
                end
                _t1213 = _t1215
            end
            _t1210 = _t1213
        end
        _t1207 = _t1210
    end
    result624 = _t1207
    record_span!(parser, span_start623)
    return result624
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start628 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int625 = consume_terminal!(parser, "INT")
    int_3626 = consume_terminal!(parser, "INT")
    int_4627 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1231 = Proto.DateValue(year=Int32(int625), month=Int32(int_3626), day=Int32(int_4627))
    result629 = _t1231
    record_span!(parser, span_start628)
    return result629
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start637 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int630 = consume_terminal!(parser, "INT")
    int_3631 = consume_terminal!(parser, "INT")
    int_4632 = consume_terminal!(parser, "INT")
    int_5633 = consume_terminal!(parser, "INT")
    int_6634 = consume_terminal!(parser, "INT")
    int_7635 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1232 = consume_terminal!(parser, "INT")
    else
        _t1232 = nothing
    end
    int_8636 = _t1232
    consume_literal!(parser, ")")
    _t1233 = Proto.DateTimeValue(year=Int32(int630), month=Int32(int_3631), day=Int32(int_4632), hour=Int32(int_5633), minute=Int32(int_6634), second=Int32(int_7635), microsecond=Int32((!isnothing(int_8636) ? int_8636 : 0)))
    result638 = _t1233
    record_span!(parser, span_start637)
    return result638
end

function parse_boolean_value(parser::ParserState)::Bool
    span_start640 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1234 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1235 = 1
        else
            _t1235 = -1
        end
        _t1234 = _t1235
    end
    prediction639 = _t1234
    if prediction639 == 1
        consume_literal!(parser, "false")
        _t1236 = false
    else
        if prediction639 == 0
            consume_literal!(parser, "true")
            _t1237 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1236 = _t1237
    end
    result641 = _t1236
    record_span!(parser, span_start640)
    return result641
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start646 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs642 = Proto.FragmentId[]
    cond643 = match_lookahead_literal(parser, ":", 0)
    while cond643
        _t1238 = parse_fragment_id(parser)
        item644 = _t1238
        push!(xs642, item644)
        cond643 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids645 = xs642
    consume_literal!(parser, ")")
    _t1239 = Proto.Sync(fragments=fragment_ids645)
    result647 = _t1239
    record_span!(parser, span_start646)
    return result647
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start649 = span_start(parser)
    consume_literal!(parser, ":")
    symbol648 = consume_terminal!(parser, "SYMBOL")
    result650 = Proto.FragmentId(Vector{UInt8}(symbol648))
    record_span!(parser, span_start649)
    return result650
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start653 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1241 = parse_epoch_writes(parser)
        _t1240 = _t1241
    else
        _t1240 = nothing
    end
    epoch_writes651 = _t1240
    if match_lookahead_literal(parser, "(", 0)
        _t1243 = parse_epoch_reads(parser)
        _t1242 = _t1243
    else
        _t1242 = nothing
    end
    epoch_reads652 = _t1242
    consume_literal!(parser, ")")
    _t1244 = Proto.Epoch(writes=(!isnothing(epoch_writes651) ? epoch_writes651 : Proto.Write[]), reads=(!isnothing(epoch_reads652) ? epoch_reads652 : Proto.Read[]))
    result654 = _t1244
    record_span!(parser, span_start653)
    return result654
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    span_start659 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs655 = Proto.Write[]
    cond656 = match_lookahead_literal(parser, "(", 0)
    while cond656
        _t1245 = parse_write(parser)
        item657 = _t1245
        push!(xs655, item657)
        cond656 = match_lookahead_literal(parser, "(", 0)
    end
    writes658 = xs655
    consume_literal!(parser, ")")
    result660 = writes658
    record_span!(parser, span_start659)
    return result660
end

function parse_write(parser::ParserState)::Proto.Write
    span_start666 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1247 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1248 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1249 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1250 = 2
                    else
                        _t1250 = -1
                    end
                    _t1249 = _t1250
                end
                _t1248 = _t1249
            end
            _t1247 = _t1248
        end
        _t1246 = _t1247
    else
        _t1246 = -1
    end
    prediction661 = _t1246
    if prediction661 == 3
        _t1252 = parse_snapshot(parser)
        snapshot665 = _t1252
        _t1253 = Proto.Write(write_type=OneOf(:snapshot, snapshot665))
        _t1251 = _t1253
    else
        if prediction661 == 2
            _t1255 = parse_context(parser)
            context664 = _t1255
            _t1256 = Proto.Write(write_type=OneOf(:context, context664))
            _t1254 = _t1256
        else
            if prediction661 == 1
                _t1258 = parse_undefine(parser)
                undefine663 = _t1258
                _t1259 = Proto.Write(write_type=OneOf(:undefine, undefine663))
                _t1257 = _t1259
            else
                if prediction661 == 0
                    _t1261 = parse_define(parser)
                    define662 = _t1261
                    _t1262 = Proto.Write(write_type=OneOf(:define, define662))
                    _t1260 = _t1262
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1257 = _t1260
            end
            _t1254 = _t1257
        end
        _t1251 = _t1254
    end
    result667 = _t1251
    record_span!(parser, span_start666)
    return result667
end

function parse_define(parser::ParserState)::Proto.Define
    span_start669 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1263 = parse_fragment(parser)
    fragment668 = _t1263
    consume_literal!(parser, ")")
    _t1264 = Proto.Define(fragment=fragment668)
    result670 = _t1264
    record_span!(parser, span_start669)
    return result670
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start676 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1265 = parse_new_fragment_id(parser)
    new_fragment_id671 = _t1265
    xs672 = Proto.Declaration[]
    cond673 = match_lookahead_literal(parser, "(", 0)
    while cond673
        _t1266 = parse_declaration(parser)
        item674 = _t1266
        push!(xs672, item674)
        cond673 = match_lookahead_literal(parser, "(", 0)
    end
    declarations675 = xs672
    consume_literal!(parser, ")")
    result677 = construct_fragment(parser, new_fragment_id671, declarations675)
    record_span!(parser, span_start676)
    return result677
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start679 = span_start(parser)
    _t1267 = parse_fragment_id(parser)
    fragment_id678 = _t1267
    start_fragment!(parser, fragment_id678)
    result680 = fragment_id678
    record_span!(parser, span_start679)
    return result680
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start686 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1269 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1270 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1271 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1272 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1273 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1274 = 1
                            else
                                _t1274 = -1
                            end
                            _t1273 = _t1274
                        end
                        _t1272 = _t1273
                    end
                    _t1271 = _t1272
                end
                _t1270 = _t1271
            end
            _t1269 = _t1270
        end
        _t1268 = _t1269
    else
        _t1268 = -1
    end
    prediction681 = _t1268
    if prediction681 == 3
        _t1276 = parse_data(parser)
        data685 = _t1276
        _t1277 = Proto.Declaration(declaration_type=OneOf(:data, data685))
        _t1275 = _t1277
    else
        if prediction681 == 2
            _t1279 = parse_constraint(parser)
            constraint684 = _t1279
            _t1280 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint684))
            _t1278 = _t1280
        else
            if prediction681 == 1
                _t1282 = parse_algorithm(parser)
                algorithm683 = _t1282
                _t1283 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm683))
                _t1281 = _t1283
            else
                if prediction681 == 0
                    _t1285 = parse_def(parser)
                    def682 = _t1285
                    _t1286 = Proto.Declaration(declaration_type=OneOf(:def, def682))
                    _t1284 = _t1286
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1281 = _t1284
            end
            _t1278 = _t1281
        end
        _t1275 = _t1278
    end
    result687 = _t1275
    record_span!(parser, span_start686)
    return result687
end

function parse_def(parser::ParserState)::Proto.Def
    span_start691 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1287 = parse_relation_id(parser)
    relation_id688 = _t1287
    _t1288 = parse_abstraction(parser)
    abstraction689 = _t1288
    if match_lookahead_literal(parser, "(", 0)
        _t1290 = parse_attrs(parser)
        _t1289 = _t1290
    else
        _t1289 = nothing
    end
    attrs690 = _t1289
    consume_literal!(parser, ")")
    _t1291 = Proto.Def(name=relation_id688, body=abstraction689, attrs=(!isnothing(attrs690) ? attrs690 : Proto.Attribute[]))
    result692 = _t1291
    record_span!(parser, span_start691)
    return result692
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start696 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1292 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1293 = 1
        else
            _t1293 = -1
        end
        _t1292 = _t1293
    end
    prediction693 = _t1292
    if prediction693 == 1
        uint128695 = consume_terminal!(parser, "UINT128")
        _t1294 = Proto.RelationId(uint128695.low, uint128695.high)
    else
        if prediction693 == 0
            consume_literal!(parser, ":")
            symbol694 = consume_terminal!(parser, "SYMBOL")
            _t1295 = relation_id_from_string(parser, symbol694)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1294 = _t1295
    end
    result697 = _t1294
    record_span!(parser, span_start696)
    return result697
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start700 = span_start(parser)
    consume_literal!(parser, "(")
    _t1296 = parse_bindings(parser)
    bindings698 = _t1296
    _t1297 = parse_formula(parser)
    formula699 = _t1297
    consume_literal!(parser, ")")
    _t1298 = Proto.Abstraction(vars=vcat(bindings698[1], !isnothing(bindings698[2]) ? bindings698[2] : []), value=formula699)
    result701 = _t1298
    record_span!(parser, span_start700)
    return result701
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    span_start707 = span_start(parser)
    consume_literal!(parser, "[")
    xs702 = Proto.Binding[]
    cond703 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond703
        _t1299 = parse_binding(parser)
        item704 = _t1299
        push!(xs702, item704)
        cond703 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings705 = xs702
    if match_lookahead_literal(parser, "|", 0)
        _t1301 = parse_value_bindings(parser)
        _t1300 = _t1301
    else
        _t1300 = nothing
    end
    value_bindings706 = _t1300
    consume_literal!(parser, "]")
    result708 = (bindings705, (!isnothing(value_bindings706) ? value_bindings706 : Proto.Binding[]),)
    record_span!(parser, span_start707)
    return result708
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start711 = span_start(parser)
    symbol709 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1302 = parse_type(parser)
    type710 = _t1302
    _t1303 = Proto.Var(name=symbol709)
    _t1304 = Proto.Binding(var=_t1303, var"#type"=type710)
    result712 = _t1304
    record_span!(parser, span_start711)
    return result712
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start725 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1305 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t1306 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t1307 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t1308 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t1309 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t1310 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t1311 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t1312 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t1313 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t1314 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t1315 = 9
                                            else
                                                _t1315 = -1
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
                    end
                    _t1308 = _t1309
                end
                _t1307 = _t1308
            end
            _t1306 = _t1307
        end
        _t1305 = _t1306
    end
    prediction713 = _t1305
    if prediction713 == 10
        _t1317 = parse_boolean_type(parser)
        boolean_type724 = _t1317
        _t1318 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type724))
        _t1316 = _t1318
    else
        if prediction713 == 9
            _t1320 = parse_decimal_type(parser)
            decimal_type723 = _t1320
            _t1321 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type723))
            _t1319 = _t1321
        else
            if prediction713 == 8
                _t1323 = parse_missing_type(parser)
                missing_type722 = _t1323
                _t1324 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type722))
                _t1322 = _t1324
            else
                if prediction713 == 7
                    _t1326 = parse_datetime_type(parser)
                    datetime_type721 = _t1326
                    _t1327 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type721))
                    _t1325 = _t1327
                else
                    if prediction713 == 6
                        _t1329 = parse_date_type(parser)
                        date_type720 = _t1329
                        _t1330 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type720))
                        _t1328 = _t1330
                    else
                        if prediction713 == 5
                            _t1332 = parse_int128_type(parser)
                            int128_type719 = _t1332
                            _t1333 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type719))
                            _t1331 = _t1333
                        else
                            if prediction713 == 4
                                _t1335 = parse_uint128_type(parser)
                                uint128_type718 = _t1335
                                _t1336 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type718))
                                _t1334 = _t1336
                            else
                                if prediction713 == 3
                                    _t1338 = parse_float_type(parser)
                                    float_type717 = _t1338
                                    _t1339 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type717))
                                    _t1337 = _t1339
                                else
                                    if prediction713 == 2
                                        _t1341 = parse_int_type(parser)
                                        int_type716 = _t1341
                                        _t1342 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type716))
                                        _t1340 = _t1342
                                    else
                                        if prediction713 == 1
                                            _t1344 = parse_string_type(parser)
                                            string_type715 = _t1344
                                            _t1345 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type715))
                                            _t1343 = _t1345
                                        else
                                            if prediction713 == 0
                                                _t1347 = parse_unspecified_type(parser)
                                                unspecified_type714 = _t1347
                                                _t1348 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type714))
                                                _t1346 = _t1348
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t1343 = _t1346
                                        end
                                        _t1340 = _t1343
                                    end
                                    _t1337 = _t1340
                                end
                                _t1334 = _t1337
                            end
                            _t1331 = _t1334
                        end
                        _t1328 = _t1331
                    end
                    _t1325 = _t1328
                end
                _t1322 = _t1325
            end
            _t1319 = _t1322
        end
        _t1316 = _t1319
    end
    result726 = _t1316
    record_span!(parser, span_start725)
    return result726
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start727 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1349 = Proto.UnspecifiedType()
    result728 = _t1349
    record_span!(parser, span_start727)
    return result728
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start729 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1350 = Proto.StringType()
    result730 = _t1350
    record_span!(parser, span_start729)
    return result730
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start731 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1351 = Proto.IntType()
    result732 = _t1351
    record_span!(parser, span_start731)
    return result732
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start733 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1352 = Proto.FloatType()
    result734 = _t1352
    record_span!(parser, span_start733)
    return result734
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start735 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1353 = Proto.UInt128Type()
    result736 = _t1353
    record_span!(parser, span_start735)
    return result736
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start737 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1354 = Proto.Int128Type()
    result738 = _t1354
    record_span!(parser, span_start737)
    return result738
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start739 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1355 = Proto.DateType()
    result740 = _t1355
    record_span!(parser, span_start739)
    return result740
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start741 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1356 = Proto.DateTimeType()
    result742 = _t1356
    record_span!(parser, span_start741)
    return result742
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start743 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1357 = Proto.MissingType()
    result744 = _t1357
    record_span!(parser, span_start743)
    return result744
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start747 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int745 = consume_terminal!(parser, "INT")
    int_3746 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1358 = Proto.DecimalType(precision=Int32(int745), scale=Int32(int_3746))
    result748 = _t1358
    record_span!(parser, span_start747)
    return result748
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start749 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1359 = Proto.BooleanType()
    result750 = _t1359
    record_span!(parser, span_start749)
    return result750
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    span_start755 = span_start(parser)
    consume_literal!(parser, "|")
    xs751 = Proto.Binding[]
    cond752 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond752
        _t1360 = parse_binding(parser)
        item753 = _t1360
        push!(xs751, item753)
        cond752 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings754 = xs751
    result756 = bindings754
    record_span!(parser, span_start755)
    return result756
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start771 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1362 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1363 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1364 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1365 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1366 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1367 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1368 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1369 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1370 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1371 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1372 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1373 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1374 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1375 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1376 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1377 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1378 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1379 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1380 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1381 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1382 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1383 = 10
                                                                                            else
                                                                                                _t1383 = -1
                                                                                            end
                                                                                            _t1382 = _t1383
                                                                                        end
                                                                                        _t1381 = _t1382
                                                                                    end
                                                                                    _t1380 = _t1381
                                                                                end
                                                                                _t1379 = _t1380
                                                                            end
                                                                            _t1378 = _t1379
                                                                        end
                                                                        _t1377 = _t1378
                                                                    end
                                                                    _t1376 = _t1377
                                                                end
                                                                _t1375 = _t1376
                                                            end
                                                            _t1374 = _t1375
                                                        end
                                                        _t1373 = _t1374
                                                    end
                                                    _t1372 = _t1373
                                                end
                                                _t1371 = _t1372
                                            end
                                            _t1370 = _t1371
                                        end
                                        _t1369 = _t1370
                                    end
                                    _t1368 = _t1369
                                end
                                _t1367 = _t1368
                            end
                            _t1366 = _t1367
                        end
                        _t1365 = _t1366
                    end
                    _t1364 = _t1365
                end
                _t1363 = _t1364
            end
            _t1362 = _t1363
        end
        _t1361 = _t1362
    else
        _t1361 = -1
    end
    prediction757 = _t1361
    if prediction757 == 12
        _t1385 = parse_cast(parser)
        cast770 = _t1385
        _t1386 = Proto.Formula(formula_type=OneOf(:cast, cast770))
        _t1384 = _t1386
    else
        if prediction757 == 11
            _t1388 = parse_rel_atom(parser)
            rel_atom769 = _t1388
            _t1389 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom769))
            _t1387 = _t1389
        else
            if prediction757 == 10
                _t1391 = parse_primitive(parser)
                primitive768 = _t1391
                _t1392 = Proto.Formula(formula_type=OneOf(:primitive, primitive768))
                _t1390 = _t1392
            else
                if prediction757 == 9
                    _t1394 = parse_pragma(parser)
                    pragma767 = _t1394
                    _t1395 = Proto.Formula(formula_type=OneOf(:pragma, pragma767))
                    _t1393 = _t1395
                else
                    if prediction757 == 8
                        _t1397 = parse_atom(parser)
                        atom766 = _t1397
                        _t1398 = Proto.Formula(formula_type=OneOf(:atom, atom766))
                        _t1396 = _t1398
                    else
                        if prediction757 == 7
                            _t1400 = parse_ffi(parser)
                            ffi765 = _t1400
                            _t1401 = Proto.Formula(formula_type=OneOf(:ffi, ffi765))
                            _t1399 = _t1401
                        else
                            if prediction757 == 6
                                _t1403 = parse_not(parser)
                                not764 = _t1403
                                _t1404 = Proto.Formula(formula_type=OneOf(:not, not764))
                                _t1402 = _t1404
                            else
                                if prediction757 == 5
                                    _t1406 = parse_disjunction(parser)
                                    disjunction763 = _t1406
                                    _t1407 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction763))
                                    _t1405 = _t1407
                                else
                                    if prediction757 == 4
                                        _t1409 = parse_conjunction(parser)
                                        conjunction762 = _t1409
                                        _t1410 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction762))
                                        _t1408 = _t1410
                                    else
                                        if prediction757 == 3
                                            _t1412 = parse_reduce(parser)
                                            reduce761 = _t1412
                                            _t1413 = Proto.Formula(formula_type=OneOf(:reduce, reduce761))
                                            _t1411 = _t1413
                                        else
                                            if prediction757 == 2
                                                _t1415 = parse_exists(parser)
                                                exists760 = _t1415
                                                _t1416 = Proto.Formula(formula_type=OneOf(:exists, exists760))
                                                _t1414 = _t1416
                                            else
                                                if prediction757 == 1
                                                    _t1418 = parse_false(parser)
                                                    false759 = _t1418
                                                    _t1419 = Proto.Formula(formula_type=OneOf(:disjunction, false759))
                                                    _t1417 = _t1419
                                                else
                                                    if prediction757 == 0
                                                        _t1421 = parse_true(parser)
                                                        true758 = _t1421
                                                        _t1422 = Proto.Formula(formula_type=OneOf(:conjunction, true758))
                                                        _t1420 = _t1422
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1417 = _t1420
                                                end
                                                _t1414 = _t1417
                                            end
                                            _t1411 = _t1414
                                        end
                                        _t1408 = _t1411
                                    end
                                    _t1405 = _t1408
                                end
                                _t1402 = _t1405
                            end
                            _t1399 = _t1402
                        end
                        _t1396 = _t1399
                    end
                    _t1393 = _t1396
                end
                _t1390 = _t1393
            end
            _t1387 = _t1390
        end
        _t1384 = _t1387
    end
    result772 = _t1384
    record_span!(parser, span_start771)
    return result772
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start773 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1423 = Proto.Conjunction(args=Proto.Formula[])
    result774 = _t1423
    record_span!(parser, span_start773)
    return result774
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start775 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1424 = Proto.Disjunction(args=Proto.Formula[])
    result776 = _t1424
    record_span!(parser, span_start775)
    return result776
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start779 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1425 = parse_bindings(parser)
    bindings777 = _t1425
    _t1426 = parse_formula(parser)
    formula778 = _t1426
    consume_literal!(parser, ")")
    _t1427 = Proto.Abstraction(vars=vcat(bindings777[1], !isnothing(bindings777[2]) ? bindings777[2] : []), value=formula778)
    _t1428 = Proto.Exists(body=_t1427)
    result780 = _t1428
    record_span!(parser, span_start779)
    return result780
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start784 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1429 = parse_abstraction(parser)
    abstraction781 = _t1429
    _t1430 = parse_abstraction(parser)
    abstraction_3782 = _t1430
    _t1431 = parse_terms(parser)
    terms783 = _t1431
    consume_literal!(parser, ")")
    _t1432 = Proto.Reduce(op=abstraction781, body=abstraction_3782, terms=terms783)
    result785 = _t1432
    record_span!(parser, span_start784)
    return result785
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    span_start790 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs786 = Proto.Term[]
    cond787 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond787
        _t1433 = parse_term(parser)
        item788 = _t1433
        push!(xs786, item788)
        cond787 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms789 = xs786
    consume_literal!(parser, ")")
    result791 = terms789
    record_span!(parser, span_start790)
    return result791
end

function parse_term(parser::ParserState)::Proto.Term
    span_start795 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1434 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1435 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1436 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1437 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1438 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1439 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1440 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1441 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1442 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t1443 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t1444 = 1
                                            else
                                                _t1444 = -1
                                            end
                                            _t1443 = _t1444
                                        end
                                        _t1442 = _t1443
                                    end
                                    _t1441 = _t1442
                                end
                                _t1440 = _t1441
                            end
                            _t1439 = _t1440
                        end
                        _t1438 = _t1439
                    end
                    _t1437 = _t1438
                end
                _t1436 = _t1437
            end
            _t1435 = _t1436
        end
        _t1434 = _t1435
    end
    prediction792 = _t1434
    if prediction792 == 1
        _t1446 = parse_constant(parser)
        constant794 = _t1446
        _t1447 = Proto.Term(term_type=OneOf(:constant, constant794))
        _t1445 = _t1447
    else
        if prediction792 == 0
            _t1449 = parse_var(parser)
            var793 = _t1449
            _t1450 = Proto.Term(term_type=OneOf(:var, var793))
            _t1448 = _t1450
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1445 = _t1448
    end
    result796 = _t1445
    record_span!(parser, span_start795)
    return result796
end

function parse_var(parser::ParserState)::Proto.Var
    span_start798 = span_start(parser)
    symbol797 = consume_terminal!(parser, "SYMBOL")
    _t1451 = Proto.Var(name=symbol797)
    result799 = _t1451
    record_span!(parser, span_start798)
    return result799
end

function parse_constant(parser::ParserState)::Proto.Value
    span_start801 = span_start(parser)
    _t1452 = parse_value(parser)
    value800 = _t1452
    result802 = value800
    record_span!(parser, span_start801)
    return result802
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start807 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs803 = Proto.Formula[]
    cond804 = match_lookahead_literal(parser, "(", 0)
    while cond804
        _t1453 = parse_formula(parser)
        item805 = _t1453
        push!(xs803, item805)
        cond804 = match_lookahead_literal(parser, "(", 0)
    end
    formulas806 = xs803
    consume_literal!(parser, ")")
    _t1454 = Proto.Conjunction(args=formulas806)
    result808 = _t1454
    record_span!(parser, span_start807)
    return result808
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start813 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs809 = Proto.Formula[]
    cond810 = match_lookahead_literal(parser, "(", 0)
    while cond810
        _t1455 = parse_formula(parser)
        item811 = _t1455
        push!(xs809, item811)
        cond810 = match_lookahead_literal(parser, "(", 0)
    end
    formulas812 = xs809
    consume_literal!(parser, ")")
    _t1456 = Proto.Disjunction(args=formulas812)
    result814 = _t1456
    record_span!(parser, span_start813)
    return result814
end

function parse_not(parser::ParserState)::Proto.Not
    span_start816 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1457 = parse_formula(parser)
    formula815 = _t1457
    consume_literal!(parser, ")")
    _t1458 = Proto.Not(arg=formula815)
    result817 = _t1458
    record_span!(parser, span_start816)
    return result817
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start821 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1459 = parse_name(parser)
    name818 = _t1459
    _t1460 = parse_ffi_args(parser)
    ffi_args819 = _t1460
    _t1461 = parse_terms(parser)
    terms820 = _t1461
    consume_literal!(parser, ")")
    _t1462 = Proto.FFI(name=name818, args=ffi_args819, terms=terms820)
    result822 = _t1462
    record_span!(parser, span_start821)
    return result822
end

function parse_name(parser::ParserState)::String
    span_start824 = span_start(parser)
    consume_literal!(parser, ":")
    symbol823 = consume_terminal!(parser, "SYMBOL")
    result825 = symbol823
    record_span!(parser, span_start824)
    return result825
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    span_start830 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs826 = Proto.Abstraction[]
    cond827 = match_lookahead_literal(parser, "(", 0)
    while cond827
        _t1463 = parse_abstraction(parser)
        item828 = _t1463
        push!(xs826, item828)
        cond827 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions829 = xs826
    consume_literal!(parser, ")")
    result831 = abstractions829
    record_span!(parser, span_start830)
    return result831
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start837 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1464 = parse_relation_id(parser)
    relation_id832 = _t1464
    xs833 = Proto.Term[]
    cond834 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond834
        _t1465 = parse_term(parser)
        item835 = _t1465
        push!(xs833, item835)
        cond834 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms836 = xs833
    consume_literal!(parser, ")")
    _t1466 = Proto.Atom(name=relation_id832, terms=terms836)
    result838 = _t1466
    record_span!(parser, span_start837)
    return result838
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start844 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1467 = parse_name(parser)
    name839 = _t1467
    xs840 = Proto.Term[]
    cond841 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond841
        _t1468 = parse_term(parser)
        item842 = _t1468
        push!(xs840, item842)
        cond841 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms843 = xs840
    consume_literal!(parser, ")")
    _t1469 = Proto.Pragma(name=name839, terms=terms843)
    result845 = _t1469
    record_span!(parser, span_start844)
    return result845
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start861 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1471 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1472 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1473 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1474 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1475 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1476 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1477 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1478 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1479 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1480 = 7
                                            else
                                                _t1480 = -1
                                            end
                                            _t1479 = _t1480
                                        end
                                        _t1478 = _t1479
                                    end
                                    _t1477 = _t1478
                                end
                                _t1476 = _t1477
                            end
                            _t1475 = _t1476
                        end
                        _t1474 = _t1475
                    end
                    _t1473 = _t1474
                end
                _t1472 = _t1473
            end
            _t1471 = _t1472
        end
        _t1470 = _t1471
    else
        _t1470 = -1
    end
    prediction846 = _t1470
    if prediction846 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1482 = parse_name(parser)
        name856 = _t1482
        xs857 = Proto.RelTerm[]
        cond858 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond858
            _t1483 = parse_rel_term(parser)
            item859 = _t1483
            push!(xs857, item859)
            cond858 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms860 = xs857
        consume_literal!(parser, ")")
        _t1484 = Proto.Primitive(name=name856, terms=rel_terms860)
        _t1481 = _t1484
    else
        if prediction846 == 8
            _t1486 = parse_divide(parser)
            divide855 = _t1486
            _t1485 = divide855
        else
            if prediction846 == 7
                _t1488 = parse_multiply(parser)
                multiply854 = _t1488
                _t1487 = multiply854
            else
                if prediction846 == 6
                    _t1490 = parse_minus(parser)
                    minus853 = _t1490
                    _t1489 = minus853
                else
                    if prediction846 == 5
                        _t1492 = parse_add(parser)
                        add852 = _t1492
                        _t1491 = add852
                    else
                        if prediction846 == 4
                            _t1494 = parse_gt_eq(parser)
                            gt_eq851 = _t1494
                            _t1493 = gt_eq851
                        else
                            if prediction846 == 3
                                _t1496 = parse_gt(parser)
                                gt850 = _t1496
                                _t1495 = gt850
                            else
                                if prediction846 == 2
                                    _t1498 = parse_lt_eq(parser)
                                    lt_eq849 = _t1498
                                    _t1497 = lt_eq849
                                else
                                    if prediction846 == 1
                                        _t1500 = parse_lt(parser)
                                        lt848 = _t1500
                                        _t1499 = lt848
                                    else
                                        if prediction846 == 0
                                            _t1502 = parse_eq(parser)
                                            eq847 = _t1502
                                            _t1501 = eq847
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1499 = _t1501
                                    end
                                    _t1497 = _t1499
                                end
                                _t1495 = _t1497
                            end
                            _t1493 = _t1495
                        end
                        _t1491 = _t1493
                    end
                    _t1489 = _t1491
                end
                _t1487 = _t1489
            end
            _t1485 = _t1487
        end
        _t1481 = _t1485
    end
    result862 = _t1481
    record_span!(parser, span_start861)
    return result862
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start865 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1503 = parse_term(parser)
    term863 = _t1503
    _t1504 = parse_term(parser)
    term_3864 = _t1504
    consume_literal!(parser, ")")
    _t1505 = Proto.RelTerm(rel_term_type=OneOf(:term, term863))
    _t1506 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3864))
    _t1507 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1505, _t1506])
    result866 = _t1507
    record_span!(parser, span_start865)
    return result866
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start869 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1508 = parse_term(parser)
    term867 = _t1508
    _t1509 = parse_term(parser)
    term_3868 = _t1509
    consume_literal!(parser, ")")
    _t1510 = Proto.RelTerm(rel_term_type=OneOf(:term, term867))
    _t1511 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3868))
    _t1512 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1510, _t1511])
    result870 = _t1512
    record_span!(parser, span_start869)
    return result870
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start873 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1513 = parse_term(parser)
    term871 = _t1513
    _t1514 = parse_term(parser)
    term_3872 = _t1514
    consume_literal!(parser, ")")
    _t1515 = Proto.RelTerm(rel_term_type=OneOf(:term, term871))
    _t1516 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3872))
    _t1517 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1515, _t1516])
    result874 = _t1517
    record_span!(parser, span_start873)
    return result874
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start877 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1518 = parse_term(parser)
    term875 = _t1518
    _t1519 = parse_term(parser)
    term_3876 = _t1519
    consume_literal!(parser, ")")
    _t1520 = Proto.RelTerm(rel_term_type=OneOf(:term, term875))
    _t1521 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3876))
    _t1522 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1520, _t1521])
    result878 = _t1522
    record_span!(parser, span_start877)
    return result878
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start881 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1523 = parse_term(parser)
    term879 = _t1523
    _t1524 = parse_term(parser)
    term_3880 = _t1524
    consume_literal!(parser, ")")
    _t1525 = Proto.RelTerm(rel_term_type=OneOf(:term, term879))
    _t1526 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3880))
    _t1527 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1525, _t1526])
    result882 = _t1527
    record_span!(parser, span_start881)
    return result882
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start886 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1528 = parse_term(parser)
    term883 = _t1528
    _t1529 = parse_term(parser)
    term_3884 = _t1529
    _t1530 = parse_term(parser)
    term_4885 = _t1530
    consume_literal!(parser, ")")
    _t1531 = Proto.RelTerm(rel_term_type=OneOf(:term, term883))
    _t1532 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3884))
    _t1533 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4885))
    _t1534 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1531, _t1532, _t1533])
    result887 = _t1534
    record_span!(parser, span_start886)
    return result887
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start891 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1535 = parse_term(parser)
    term888 = _t1535
    _t1536 = parse_term(parser)
    term_3889 = _t1536
    _t1537 = parse_term(parser)
    term_4890 = _t1537
    consume_literal!(parser, ")")
    _t1538 = Proto.RelTerm(rel_term_type=OneOf(:term, term888))
    _t1539 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3889))
    _t1540 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4890))
    _t1541 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1538, _t1539, _t1540])
    result892 = _t1541
    record_span!(parser, span_start891)
    return result892
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start896 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1542 = parse_term(parser)
    term893 = _t1542
    _t1543 = parse_term(parser)
    term_3894 = _t1543
    _t1544 = parse_term(parser)
    term_4895 = _t1544
    consume_literal!(parser, ")")
    _t1545 = Proto.RelTerm(rel_term_type=OneOf(:term, term893))
    _t1546 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3894))
    _t1547 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4895))
    _t1548 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1545, _t1546, _t1547])
    result897 = _t1548
    record_span!(parser, span_start896)
    return result897
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start901 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1549 = parse_term(parser)
    term898 = _t1549
    _t1550 = parse_term(parser)
    term_3899 = _t1550
    _t1551 = parse_term(parser)
    term_4900 = _t1551
    consume_literal!(parser, ")")
    _t1552 = Proto.RelTerm(rel_term_type=OneOf(:term, term898))
    _t1553 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3899))
    _t1554 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4900))
    _t1555 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1552, _t1553, _t1554])
    result902 = _t1555
    record_span!(parser, span_start901)
    return result902
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start906 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1556 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1557 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1558 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1559 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1560 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1561 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1562 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1563 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1564 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1565 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1566 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1567 = 1
                                                else
                                                    _t1567 = -1
                                                end
                                                _t1566 = _t1567
                                            end
                                            _t1565 = _t1566
                                        end
                                        _t1564 = _t1565
                                    end
                                    _t1563 = _t1564
                                end
                                _t1562 = _t1563
                            end
                            _t1561 = _t1562
                        end
                        _t1560 = _t1561
                    end
                    _t1559 = _t1560
                end
                _t1558 = _t1559
            end
            _t1557 = _t1558
        end
        _t1556 = _t1557
    end
    prediction903 = _t1556
    if prediction903 == 1
        _t1569 = parse_term(parser)
        term905 = _t1569
        _t1570 = Proto.RelTerm(rel_term_type=OneOf(:term, term905))
        _t1568 = _t1570
    else
        if prediction903 == 0
            _t1572 = parse_specialized_value(parser)
            specialized_value904 = _t1572
            _t1573 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value904))
            _t1571 = _t1573
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1568 = _t1571
    end
    result907 = _t1568
    record_span!(parser, span_start906)
    return result907
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start909 = span_start(parser)
    consume_literal!(parser, "#")
    _t1574 = parse_value(parser)
    value908 = _t1574
    result910 = value908
    record_span!(parser, span_start909)
    return result910
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start916 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1575 = parse_name(parser)
    name911 = _t1575
    xs912 = Proto.RelTerm[]
    cond913 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond913
        _t1576 = parse_rel_term(parser)
        item914 = _t1576
        push!(xs912, item914)
        cond913 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms915 = xs912
    consume_literal!(parser, ")")
    _t1577 = Proto.RelAtom(name=name911, terms=rel_terms915)
    result917 = _t1577
    record_span!(parser, span_start916)
    return result917
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start920 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1578 = parse_term(parser)
    term918 = _t1578
    _t1579 = parse_term(parser)
    term_3919 = _t1579
    consume_literal!(parser, ")")
    _t1580 = Proto.Cast(input=term918, result=term_3919)
    result921 = _t1580
    record_span!(parser, span_start920)
    return result921
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    span_start926 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs922 = Proto.Attribute[]
    cond923 = match_lookahead_literal(parser, "(", 0)
    while cond923
        _t1581 = parse_attribute(parser)
        item924 = _t1581
        push!(xs922, item924)
        cond923 = match_lookahead_literal(parser, "(", 0)
    end
    attributes925 = xs922
    consume_literal!(parser, ")")
    result927 = attributes925
    record_span!(parser, span_start926)
    return result927
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start933 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1582 = parse_name(parser)
    name928 = _t1582
    xs929 = Proto.Value[]
    cond930 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond930
        _t1583 = parse_value(parser)
        item931 = _t1583
        push!(xs929, item931)
        cond930 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values932 = xs929
    consume_literal!(parser, ")")
    _t1584 = Proto.Attribute(name=name928, args=values932)
    result934 = _t1584
    record_span!(parser, span_start933)
    return result934
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start940 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs935 = Proto.RelationId[]
    cond936 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond936
        _t1585 = parse_relation_id(parser)
        item937 = _t1585
        push!(xs935, item937)
        cond936 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids938 = xs935
    _t1586 = parse_script(parser)
    script939 = _t1586
    consume_literal!(parser, ")")
    _t1587 = Proto.Algorithm(var"#global"=relation_ids938, body=script939)
    result941 = _t1587
    record_span!(parser, span_start940)
    return result941
end

function parse_script(parser::ParserState)::Proto.Script
    span_start946 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs942 = Proto.Construct[]
    cond943 = match_lookahead_literal(parser, "(", 0)
    while cond943
        _t1588 = parse_construct(parser)
        item944 = _t1588
        push!(xs942, item944)
        cond943 = match_lookahead_literal(parser, "(", 0)
    end
    constructs945 = xs942
    consume_literal!(parser, ")")
    _t1589 = Proto.Script(constructs=constructs945)
    result947 = _t1589
    record_span!(parser, span_start946)
    return result947
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start951 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1591 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1592 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1593 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1594 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1595 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1596 = 1
                            else
                                _t1596 = -1
                            end
                            _t1595 = _t1596
                        end
                        _t1594 = _t1595
                    end
                    _t1593 = _t1594
                end
                _t1592 = _t1593
            end
            _t1591 = _t1592
        end
        _t1590 = _t1591
    else
        _t1590 = -1
    end
    prediction948 = _t1590
    if prediction948 == 1
        _t1598 = parse_instruction(parser)
        instruction950 = _t1598
        _t1599 = Proto.Construct(construct_type=OneOf(:instruction, instruction950))
        _t1597 = _t1599
    else
        if prediction948 == 0
            _t1601 = parse_loop(parser)
            loop949 = _t1601
            _t1602 = Proto.Construct(construct_type=OneOf(:loop, loop949))
            _t1600 = _t1602
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1597 = _t1600
    end
    result952 = _t1597
    record_span!(parser, span_start951)
    return result952
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start955 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1603 = parse_init(parser)
    init953 = _t1603
    _t1604 = parse_script(parser)
    script954 = _t1604
    consume_literal!(parser, ")")
    _t1605 = Proto.Loop(init=init953, body=script954)
    result956 = _t1605
    record_span!(parser, span_start955)
    return result956
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    span_start961 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs957 = Proto.Instruction[]
    cond958 = match_lookahead_literal(parser, "(", 0)
    while cond958
        _t1606 = parse_instruction(parser)
        item959 = _t1606
        push!(xs957, item959)
        cond958 = match_lookahead_literal(parser, "(", 0)
    end
    instructions960 = xs957
    consume_literal!(parser, ")")
    result962 = instructions960
    record_span!(parser, span_start961)
    return result962
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start969 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1608 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1609 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1610 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1611 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1612 = 0
                        else
                            _t1612 = -1
                        end
                        _t1611 = _t1612
                    end
                    _t1610 = _t1611
                end
                _t1609 = _t1610
            end
            _t1608 = _t1609
        end
        _t1607 = _t1608
    else
        _t1607 = -1
    end
    prediction963 = _t1607
    if prediction963 == 4
        _t1614 = parse_monus_def(parser)
        monus_def968 = _t1614
        _t1615 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def968))
        _t1613 = _t1615
    else
        if prediction963 == 3
            _t1617 = parse_monoid_def(parser)
            monoid_def967 = _t1617
            _t1618 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def967))
            _t1616 = _t1618
        else
            if prediction963 == 2
                _t1620 = parse_break(parser)
                break966 = _t1620
                _t1621 = Proto.Instruction(instr_type=OneOf(:var"#break", break966))
                _t1619 = _t1621
            else
                if prediction963 == 1
                    _t1623 = parse_upsert(parser)
                    upsert965 = _t1623
                    _t1624 = Proto.Instruction(instr_type=OneOf(:upsert, upsert965))
                    _t1622 = _t1624
                else
                    if prediction963 == 0
                        _t1626 = parse_assign(parser)
                        assign964 = _t1626
                        _t1627 = Proto.Instruction(instr_type=OneOf(:assign, assign964))
                        _t1625 = _t1627
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1622 = _t1625
                end
                _t1619 = _t1622
            end
            _t1616 = _t1619
        end
        _t1613 = _t1616
    end
    result970 = _t1613
    record_span!(parser, span_start969)
    return result970
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1628 = parse_relation_id(parser)
    relation_id971 = _t1628
    _t1629 = parse_abstraction(parser)
    abstraction972 = _t1629
    if match_lookahead_literal(parser, "(", 0)
        _t1631 = parse_attrs(parser)
        _t1630 = _t1631
    else
        _t1630 = nothing
    end
    attrs973 = _t1630
    consume_literal!(parser, ")")
    _t1632 = Proto.Assign(name=relation_id971, body=abstraction972, attrs=(!isnothing(attrs973) ? attrs973 : Proto.Attribute[]))
    result975 = _t1632
    record_span!(parser, span_start974)
    return result975
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start979 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1633 = parse_relation_id(parser)
    relation_id976 = _t1633
    _t1634 = parse_abstraction_with_arity(parser)
    abstraction_with_arity977 = _t1634
    if match_lookahead_literal(parser, "(", 0)
        _t1636 = parse_attrs(parser)
        _t1635 = _t1636
    else
        _t1635 = nothing
    end
    attrs978 = _t1635
    consume_literal!(parser, ")")
    _t1637 = Proto.Upsert(name=relation_id976, body=abstraction_with_arity977[1], attrs=(!isnothing(attrs978) ? attrs978 : Proto.Attribute[]), value_arity=abstraction_with_arity977[2])
    result980 = _t1637
    record_span!(parser, span_start979)
    return result980
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    span_start983 = span_start(parser)
    consume_literal!(parser, "(")
    _t1638 = parse_bindings(parser)
    bindings981 = _t1638
    _t1639 = parse_formula(parser)
    formula982 = _t1639
    consume_literal!(parser, ")")
    _t1640 = Proto.Abstraction(vars=vcat(bindings981[1], !isnothing(bindings981[2]) ? bindings981[2] : []), value=formula982)
    result984 = (_t1640, length(bindings981[2]),)
    record_span!(parser, span_start983)
    return result984
end

function parse_break(parser::ParserState)::Proto.Break
    span_start988 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1641 = parse_relation_id(parser)
    relation_id985 = _t1641
    _t1642 = parse_abstraction(parser)
    abstraction986 = _t1642
    if match_lookahead_literal(parser, "(", 0)
        _t1644 = parse_attrs(parser)
        _t1643 = _t1644
    else
        _t1643 = nothing
    end
    attrs987 = _t1643
    consume_literal!(parser, ")")
    _t1645 = Proto.Break(name=relation_id985, body=abstraction986, attrs=(!isnothing(attrs987) ? attrs987 : Proto.Attribute[]))
    result989 = _t1645
    record_span!(parser, span_start988)
    return result989
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start994 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1646 = parse_monoid(parser)
    monoid990 = _t1646
    _t1647 = parse_relation_id(parser)
    relation_id991 = _t1647
    _t1648 = parse_abstraction_with_arity(parser)
    abstraction_with_arity992 = _t1648
    if match_lookahead_literal(parser, "(", 0)
        _t1650 = parse_attrs(parser)
        _t1649 = _t1650
    else
        _t1649 = nothing
    end
    attrs993 = _t1649
    consume_literal!(parser, ")")
    _t1651 = Proto.MonoidDef(monoid=monoid990, name=relation_id991, body=abstraction_with_arity992[1], attrs=(!isnothing(attrs993) ? attrs993 : Proto.Attribute[]), value_arity=abstraction_with_arity992[2])
    result995 = _t1651
    record_span!(parser, span_start994)
    return result995
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1001 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1653 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1654 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1655 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1656 = 2
                    else
                        _t1656 = -1
                    end
                    _t1655 = _t1656
                end
                _t1654 = _t1655
            end
            _t1653 = _t1654
        end
        _t1652 = _t1653
    else
        _t1652 = -1
    end
    prediction996 = _t1652
    if prediction996 == 3
        _t1658 = parse_sum_monoid(parser)
        sum_monoid1000 = _t1658
        _t1659 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1000))
        _t1657 = _t1659
    else
        if prediction996 == 2
            _t1661 = parse_max_monoid(parser)
            max_monoid999 = _t1661
            _t1662 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid999))
            _t1660 = _t1662
        else
            if prediction996 == 1
                _t1664 = parse_min_monoid(parser)
                min_monoid998 = _t1664
                _t1665 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid998))
                _t1663 = _t1665
            else
                if prediction996 == 0
                    _t1667 = parse_or_monoid(parser)
                    or_monoid997 = _t1667
                    _t1668 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid997))
                    _t1666 = _t1668
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1663 = _t1666
            end
            _t1660 = _t1663
        end
        _t1657 = _t1660
    end
    result1002 = _t1657
    record_span!(parser, span_start1001)
    return result1002
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1003 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1669 = Proto.OrMonoid()
    result1004 = _t1669
    record_span!(parser, span_start1003)
    return result1004
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1006 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1670 = parse_type(parser)
    type1005 = _t1670
    consume_literal!(parser, ")")
    _t1671 = Proto.MinMonoid(var"#type"=type1005)
    result1007 = _t1671
    record_span!(parser, span_start1006)
    return result1007
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1009 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1672 = parse_type(parser)
    type1008 = _t1672
    consume_literal!(parser, ")")
    _t1673 = Proto.MaxMonoid(var"#type"=type1008)
    result1010 = _t1673
    record_span!(parser, span_start1009)
    return result1010
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1012 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1674 = parse_type(parser)
    type1011 = _t1674
    consume_literal!(parser, ")")
    _t1675 = Proto.SumMonoid(var"#type"=type1011)
    result1013 = _t1675
    record_span!(parser, span_start1012)
    return result1013
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1018 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1676 = parse_monoid(parser)
    monoid1014 = _t1676
    _t1677 = parse_relation_id(parser)
    relation_id1015 = _t1677
    _t1678 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1016 = _t1678
    if match_lookahead_literal(parser, "(", 0)
        _t1680 = parse_attrs(parser)
        _t1679 = _t1680
    else
        _t1679 = nothing
    end
    attrs1017 = _t1679
    consume_literal!(parser, ")")
    _t1681 = Proto.MonusDef(monoid=monoid1014, name=relation_id1015, body=abstraction_with_arity1016[1], attrs=(!isnothing(attrs1017) ? attrs1017 : Proto.Attribute[]), value_arity=abstraction_with_arity1016[2])
    result1019 = _t1681
    record_span!(parser, span_start1018)
    return result1019
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1024 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1682 = parse_relation_id(parser)
    relation_id1020 = _t1682
    _t1683 = parse_abstraction(parser)
    abstraction1021 = _t1683
    _t1684 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1022 = _t1684
    _t1685 = parse_functional_dependency_values(parser)
    functional_dependency_values1023 = _t1685
    consume_literal!(parser, ")")
    _t1686 = Proto.FunctionalDependency(guard=abstraction1021, keys=functional_dependency_keys1022, values=functional_dependency_values1023)
    _t1687 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1686), name=relation_id1020)
    result1025 = _t1687
    record_span!(parser, span_start1024)
    return result1025
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    span_start1030 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1026 = Proto.Var[]
    cond1027 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1027
        _t1688 = parse_var(parser)
        item1028 = _t1688
        push!(xs1026, item1028)
        cond1027 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1029 = xs1026
    consume_literal!(parser, ")")
    result1031 = vars1029
    record_span!(parser, span_start1030)
    return result1031
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    span_start1036 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1032 = Proto.Var[]
    cond1033 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1033
        _t1689 = parse_var(parser)
        item1034 = _t1689
        push!(xs1032, item1034)
        cond1033 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1035 = xs1032
    consume_literal!(parser, ")")
    result1037 = vars1035
    record_span!(parser, span_start1036)
    return result1037
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1042 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1691 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1692 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1693 = 1
                else
                    _t1693 = -1
                end
                _t1692 = _t1693
            end
            _t1691 = _t1692
        end
        _t1690 = _t1691
    else
        _t1690 = -1
    end
    prediction1038 = _t1690
    if prediction1038 == 2
        _t1695 = parse_csv_data(parser)
        csv_data1041 = _t1695
        _t1696 = Proto.Data(data_type=OneOf(:csv_data, csv_data1041))
        _t1694 = _t1696
    else
        if prediction1038 == 1
            _t1698 = parse_betree_relation(parser)
            betree_relation1040 = _t1698
            _t1699 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1040))
            _t1697 = _t1699
        else
            if prediction1038 == 0
                _t1701 = parse_rel_edb(parser)
                rel_edb1039 = _t1701
                _t1702 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb1039))
                _t1700 = _t1702
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1697 = _t1700
        end
        _t1694 = _t1697
    end
    result1043 = _t1694
    record_span!(parser, span_start1042)
    return result1043
end

function parse_rel_edb(parser::ParserState)::Proto.RelEDB
    span_start1047 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t1703 = parse_relation_id(parser)
    relation_id1044 = _t1703
    _t1704 = parse_rel_edb_path(parser)
    rel_edb_path1045 = _t1704
    _t1705 = parse_rel_edb_types(parser)
    rel_edb_types1046 = _t1705
    consume_literal!(parser, ")")
    _t1706 = Proto.RelEDB(target_id=relation_id1044, path=rel_edb_path1045, types=rel_edb_types1046)
    result1048 = _t1706
    record_span!(parser, span_start1047)
    return result1048
end

function parse_rel_edb_path(parser::ParserState)::Vector{String}
    span_start1053 = span_start(parser)
    consume_literal!(parser, "[")
    xs1049 = String[]
    cond1050 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1050
        item1051 = consume_terminal!(parser, "STRING")
        push!(xs1049, item1051)
        cond1050 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1052 = xs1049
    consume_literal!(parser, "]")
    result1054 = strings1052
    record_span!(parser, span_start1053)
    return result1054
end

function parse_rel_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1059 = span_start(parser)
    consume_literal!(parser, "[")
    xs1055 = Proto.var"#Type"[]
    cond1056 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1056
        _t1707 = parse_type(parser)
        item1057 = _t1707
        push!(xs1055, item1057)
        cond1056 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1058 = xs1055
    consume_literal!(parser, "]")
    result1060 = types1058
    record_span!(parser, span_start1059)
    return result1060
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1063 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1708 = parse_relation_id(parser)
    relation_id1061 = _t1708
    _t1709 = parse_betree_info(parser)
    betree_info1062 = _t1709
    consume_literal!(parser, ")")
    _t1710 = Proto.BeTreeRelation(name=relation_id1061, relation_info=betree_info1062)
    result1064 = _t1710
    record_span!(parser, span_start1063)
    return result1064
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1068 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1711 = parse_betree_info_key_types(parser)
    betree_info_key_types1065 = _t1711
    _t1712 = parse_betree_info_value_types(parser)
    betree_info_value_types1066 = _t1712
    _t1713 = parse_config_dict(parser)
    config_dict1067 = _t1713
    consume_literal!(parser, ")")
    _t1714 = construct_betree_info(parser, betree_info_key_types1065, betree_info_value_types1066, config_dict1067)
    result1069 = _t1714
    record_span!(parser, span_start1068)
    return result1069
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1074 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1070 = Proto.var"#Type"[]
    cond1071 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1071
        _t1715 = parse_type(parser)
        item1072 = _t1715
        push!(xs1070, item1072)
        cond1071 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1073 = xs1070
    consume_literal!(parser, ")")
    result1075 = types1073
    record_span!(parser, span_start1074)
    return result1075
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1080 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1076 = Proto.var"#Type"[]
    cond1077 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1077
        _t1716 = parse_type(parser)
        item1078 = _t1716
        push!(xs1076, item1078)
        cond1077 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1079 = xs1076
    consume_literal!(parser, ")")
    result1081 = types1079
    record_span!(parser, span_start1080)
    return result1081
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1086 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1717 = parse_csvlocator(parser)
    csvlocator1082 = _t1717
    _t1718 = parse_csv_config(parser)
    csv_config1083 = _t1718
    _t1719 = parse_csv_columns(parser)
    csv_columns1084 = _t1719
    _t1720 = parse_csv_asof(parser)
    csv_asof1085 = _t1720
    consume_literal!(parser, ")")
    _t1721 = Proto.CSVData(locator=csvlocator1082, config=csv_config1083, columns=csv_columns1084, asof=csv_asof1085)
    result1087 = _t1721
    record_span!(parser, span_start1086)
    return result1087
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1090 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1723 = parse_csv_locator_paths(parser)
        _t1722 = _t1723
    else
        _t1722 = nothing
    end
    csv_locator_paths1088 = _t1722
    if match_lookahead_literal(parser, "(", 0)
        _t1725 = parse_csv_locator_inline_data(parser)
        _t1724 = _t1725
    else
        _t1724 = nothing
    end
    csv_locator_inline_data1089 = _t1724
    consume_literal!(parser, ")")
    _t1726 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1088) ? csv_locator_paths1088 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1089) ? csv_locator_inline_data1089 : "")))
    result1091 = _t1726
    record_span!(parser, span_start1090)
    return result1091
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    span_start1096 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1092 = String[]
    cond1093 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1093
        item1094 = consume_terminal!(parser, "STRING")
        push!(xs1092, item1094)
        cond1093 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1095 = xs1092
    consume_literal!(parser, ")")
    result1097 = strings1095
    record_span!(parser, span_start1096)
    return result1097
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    span_start1099 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1098 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1100 = string1098
    record_span!(parser, span_start1099)
    return result1100
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1102 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1727 = parse_config_dict(parser)
    config_dict1101 = _t1727
    consume_literal!(parser, ")")
    _t1728 = construct_csv_config(parser, config_dict1101)
    result1103 = _t1728
    record_span!(parser, span_start1102)
    return result1103
end

function parse_csv_columns(parser::ParserState)::Vector{Proto.CSVColumn}
    span_start1108 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1104 = Proto.CSVColumn[]
    cond1105 = match_lookahead_literal(parser, "(", 0)
    while cond1105
        _t1729 = parse_csv_column(parser)
        item1106 = _t1729
        push!(xs1104, item1106)
        cond1105 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns1107 = xs1104
    consume_literal!(parser, ")")
    result1109 = csv_columns1107
    record_span!(parser, span_start1108)
    return result1109
end

function parse_csv_column(parser::ParserState)::Proto.CSVColumn
    span_start1116 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1110 = consume_terminal!(parser, "STRING")
    _t1730 = parse_relation_id(parser)
    relation_id1111 = _t1730
    consume_literal!(parser, "[")
    xs1112 = Proto.var"#Type"[]
    cond1113 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1113
        _t1731 = parse_type(parser)
        item1114 = _t1731
        push!(xs1112, item1114)
        cond1113 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1115 = xs1112
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1732 = Proto.CSVColumn(column_name=string1110, target_id=relation_id1111, types=types1115)
    result1117 = _t1732
    record_span!(parser, span_start1116)
    return result1117
end

function parse_csv_asof(parser::ParserState)::String
    span_start1119 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1118 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1120 = string1118
    record_span!(parser, span_start1119)
    return result1120
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1122 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1733 = parse_fragment_id(parser)
    fragment_id1121 = _t1733
    consume_literal!(parser, ")")
    _t1734 = Proto.Undefine(fragment_id=fragment_id1121)
    result1123 = _t1734
    record_span!(parser, span_start1122)
    return result1123
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1128 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1124 = Proto.RelationId[]
    cond1125 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1125
        _t1735 = parse_relation_id(parser)
        item1126 = _t1735
        push!(xs1124, item1126)
        cond1125 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1127 = xs1124
    consume_literal!(parser, ")")
    _t1736 = Proto.Context(relations=relation_ids1127)
    result1129 = _t1736
    record_span!(parser, span_start1128)
    return result1129
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1132 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t1737 = parse_rel_edb_path(parser)
    rel_edb_path1130 = _t1737
    _t1738 = parse_relation_id(parser)
    relation_id1131 = _t1738
    consume_literal!(parser, ")")
    _t1739 = Proto.Snapshot(destination_path=rel_edb_path1130, source_relation=relation_id1131)
    result1133 = _t1739
    record_span!(parser, span_start1132)
    return result1133
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    span_start1138 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1134 = Proto.Read[]
    cond1135 = match_lookahead_literal(parser, "(", 0)
    while cond1135
        _t1740 = parse_read(parser)
        item1136 = _t1740
        push!(xs1134, item1136)
        cond1135 = match_lookahead_literal(parser, "(", 0)
    end
    reads1137 = xs1134
    consume_literal!(parser, ")")
    result1139 = reads1137
    record_span!(parser, span_start1138)
    return result1139
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1146 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1742 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1743 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1744 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1745 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1746 = 3
                        else
                            _t1746 = -1
                        end
                        _t1745 = _t1746
                    end
                    _t1744 = _t1745
                end
                _t1743 = _t1744
            end
            _t1742 = _t1743
        end
        _t1741 = _t1742
    else
        _t1741 = -1
    end
    prediction1140 = _t1741
    if prediction1140 == 4
        _t1748 = parse_export(parser)
        export1145 = _t1748
        _t1749 = Proto.Read(read_type=OneOf(:var"#export", export1145))
        _t1747 = _t1749
    else
        if prediction1140 == 3
            _t1751 = parse_abort(parser)
            abort1144 = _t1751
            _t1752 = Proto.Read(read_type=OneOf(:abort, abort1144))
            _t1750 = _t1752
        else
            if prediction1140 == 2
                _t1754 = parse_what_if(parser)
                what_if1143 = _t1754
                _t1755 = Proto.Read(read_type=OneOf(:what_if, what_if1143))
                _t1753 = _t1755
            else
                if prediction1140 == 1
                    _t1757 = parse_output(parser)
                    output1142 = _t1757
                    _t1758 = Proto.Read(read_type=OneOf(:output, output1142))
                    _t1756 = _t1758
                else
                    if prediction1140 == 0
                        _t1760 = parse_demand(parser)
                        demand1141 = _t1760
                        _t1761 = Proto.Read(read_type=OneOf(:demand, demand1141))
                        _t1759 = _t1761
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1756 = _t1759
                end
                _t1753 = _t1756
            end
            _t1750 = _t1753
        end
        _t1747 = _t1750
    end
    result1147 = _t1747
    record_span!(parser, span_start1146)
    return result1147
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1149 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1762 = parse_relation_id(parser)
    relation_id1148 = _t1762
    consume_literal!(parser, ")")
    _t1763 = Proto.Demand(relation_id=relation_id1148)
    result1150 = _t1763
    record_span!(parser, span_start1149)
    return result1150
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1153 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1764 = parse_name(parser)
    name1151 = _t1764
    _t1765 = parse_relation_id(parser)
    relation_id1152 = _t1765
    consume_literal!(parser, ")")
    _t1766 = Proto.Output(name=name1151, relation_id=relation_id1152)
    result1154 = _t1766
    record_span!(parser, span_start1153)
    return result1154
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1157 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1767 = parse_name(parser)
    name1155 = _t1767
    _t1768 = parse_epoch(parser)
    epoch1156 = _t1768
    consume_literal!(parser, ")")
    _t1769 = Proto.WhatIf(branch=name1155, epoch=epoch1156)
    result1158 = _t1769
    record_span!(parser, span_start1157)
    return result1158
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1161 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1771 = parse_name(parser)
        _t1770 = _t1771
    else
        _t1770 = nothing
    end
    name1159 = _t1770
    _t1772 = parse_relation_id(parser)
    relation_id1160 = _t1772
    consume_literal!(parser, ")")
    _t1773 = Proto.Abort(name=(!isnothing(name1159) ? name1159 : "abort"), relation_id=relation_id1160)
    result1162 = _t1773
    record_span!(parser, span_start1161)
    return result1162
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1164 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1774 = parse_export_csv_config(parser)
    export_csv_config1163 = _t1774
    consume_literal!(parser, ")")
    _t1775 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1163))
    result1165 = _t1775
    record_span!(parser, span_start1164)
    return result1165
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1169 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1776 = parse_export_csv_path(parser)
    export_csv_path1166 = _t1776
    _t1777 = parse_export_csv_columns(parser)
    export_csv_columns1167 = _t1777
    _t1778 = parse_config_dict(parser)
    config_dict1168 = _t1778
    consume_literal!(parser, ")")
    _t1779 = export_csv_config(parser, export_csv_path1166, export_csv_columns1167, config_dict1168)
    result1170 = _t1779
    record_span!(parser, span_start1169)
    return result1170
end

function parse_export_csv_path(parser::ParserState)::String
    span_start1172 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1171 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1173 = string1171
    record_span!(parser, span_start1172)
    return result1173
end

function parse_export_csv_columns(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    span_start1178 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1174 = Proto.ExportCSVColumn[]
    cond1175 = match_lookahead_literal(parser, "(", 0)
    while cond1175
        _t1780 = parse_export_csv_column(parser)
        item1176 = _t1780
        push!(xs1174, item1176)
        cond1175 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1177 = xs1174
    consume_literal!(parser, ")")
    result1179 = export_csv_columns1177
    record_span!(parser, span_start1178)
    return result1179
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1182 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1180 = consume_terminal!(parser, "STRING")
    _t1781 = parse_relation_id(parser)
    relation_id1181 = _t1781
    consume_literal!(parser, ")")
    _t1782 = Proto.ExportCSVColumn(column_name=string1180, column_data=relation_id1181)
    result1183 = _t1782
    record_span!(parser, span_start1182)
    return result1183
end


function parse(input::String)
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

# Export main parse function and error type
export parse, ParseError
# Export scanner functions for testing
export scan_string, scan_int, scan_float, scan_int128, scan_uint128, scan_decimal
# Export Lexer and provenance types for testing
export Lexer, Location, Span

end # module Parser
