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
        _t1683 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1684 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1685 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1686 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1687 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1688 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1689 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1690 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1691 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1692 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1692
    _t1693 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1693
    _t1694 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1694
    _t1695 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1695
    _t1696 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1696
    _t1697 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1697
    _t1698 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1698
    _t1699 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1699
    _t1700 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1700
    _t1701 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1701
    _t1702 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1702
    _t1703 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1703
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1704 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1704
    _t1705 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1705
    _t1706 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1706
    _t1707 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1707
    _t1708 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1708
    _t1709 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1709
    _t1710 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1710
    _t1711 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1711
    _t1712 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1712
    _t1713 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1713
    _t1714 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1714
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1715 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1715
    _t1716 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1716
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
    _t1717 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1717
    _t1718 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1718
    _t1719 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1719
end

function export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1720 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1720
    _t1721 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1721
    _t1722 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1722
    _t1723 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1723
    _t1724 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1724
    _t1725 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1725
    _t1726 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1726
    _t1727 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1727
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start548 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1085 = parse_configure(parser)
        _t1084 = _t1085
    else
        _t1084 = nothing
    end
    configure542 = _t1084
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1087 = parse_sync(parser)
        _t1086 = _t1087
    else
        _t1086 = nothing
    end
    sync543 = _t1086
    xs544 = Proto.Epoch[]
    cond545 = match_lookahead_literal(parser, "(", 0)
    while cond545
        _t1088 = parse_epoch(parser)
        item546 = _t1088
        push!(xs544, item546)
        cond545 = match_lookahead_literal(parser, "(", 0)
    end
    epochs547 = xs544
    consume_literal!(parser, ")")
    _t1089 = default_configure(parser)
    _t1090 = Proto.Transaction(epochs=epochs547, configure=(!isnothing(configure542) ? configure542 : _t1089), sync=sync543)
    result549 = _t1090
    record_span!(parser, span_start548, "Transaction")
    return result549
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start551 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1091 = parse_config_dict(parser)
    config_dict550 = _t1091
    consume_literal!(parser, ")")
    _t1092 = construct_configure(parser, config_dict550)
    result552 = _t1092
    record_span!(parser, span_start551, "Configure")
    return result552
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs553 = Tuple{String, Proto.Value}[]
    cond554 = match_lookahead_literal(parser, ":", 0)
    while cond554
        _t1093 = parse_config_key_value(parser)
        item555 = _t1093
        push!(xs553, item555)
        cond554 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values556 = xs553
    consume_literal!(parser, "}")
    return config_key_values556
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol557 = consume_terminal!(parser, "SYMBOL")
    _t1094 = parse_value(parser)
    value558 = _t1094
    return (symbol557, value558,)
end

function parse_value(parser::ParserState)::Proto.Value
    span_start569 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1095 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1096 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1097 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1099 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1100 = 0
                        else
                            _t1100 = -1
                        end
                        _t1099 = _t1100
                    end
                    _t1098 = _t1099
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1101 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1102 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t1103 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t1104 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t1105 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t1106 = 7
                                        else
                                            _t1106 = -1
                                        end
                                        _t1105 = _t1106
                                    end
                                    _t1104 = _t1105
                                end
                                _t1103 = _t1104
                            end
                            _t1102 = _t1103
                        end
                        _t1101 = _t1102
                    end
                    _t1098 = _t1101
                end
                _t1097 = _t1098
            end
            _t1096 = _t1097
        end
        _t1095 = _t1096
    end
    prediction559 = _t1095
    if prediction559 == 9
        _t1108 = parse_boolean_value(parser)
        boolean_value568 = _t1108
        _t1109 = Proto.Value(value=OneOf(:boolean_value, boolean_value568))
        _t1107 = _t1109
    else
        if prediction559 == 8
            consume_literal!(parser, "missing")
            _t1111 = Proto.MissingValue()
            _t1112 = Proto.Value(value=OneOf(:missing_value, _t1111))
            _t1110 = _t1112
        else
            if prediction559 == 7
                decimal567 = consume_terminal!(parser, "DECIMAL")
                _t1114 = Proto.Value(value=OneOf(:decimal_value, decimal567))
                _t1113 = _t1114
            else
                if prediction559 == 6
                    int128566 = consume_terminal!(parser, "INT128")
                    _t1116 = Proto.Value(value=OneOf(:int128_value, int128566))
                    _t1115 = _t1116
                else
                    if prediction559 == 5
                        uint128565 = consume_terminal!(parser, "UINT128")
                        _t1118 = Proto.Value(value=OneOf(:uint128_value, uint128565))
                        _t1117 = _t1118
                    else
                        if prediction559 == 4
                            float564 = consume_terminal!(parser, "FLOAT")
                            _t1120 = Proto.Value(value=OneOf(:float_value, float564))
                            _t1119 = _t1120
                        else
                            if prediction559 == 3
                                int563 = consume_terminal!(parser, "INT")
                                _t1122 = Proto.Value(value=OneOf(:int_value, int563))
                                _t1121 = _t1122
                            else
                                if prediction559 == 2
                                    string562 = consume_terminal!(parser, "STRING")
                                    _t1124 = Proto.Value(value=OneOf(:string_value, string562))
                                    _t1123 = _t1124
                                else
                                    if prediction559 == 1
                                        _t1126 = parse_datetime(parser)
                                        datetime561 = _t1126
                                        _t1127 = Proto.Value(value=OneOf(:datetime_value, datetime561))
                                        _t1125 = _t1127
                                    else
                                        if prediction559 == 0
                                            _t1129 = parse_date(parser)
                                            date560 = _t1129
                                            _t1130 = Proto.Value(value=OneOf(:date_value, date560))
                                            _t1128 = _t1130
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1125 = _t1128
                                    end
                                    _t1123 = _t1125
                                end
                                _t1121 = _t1123
                            end
                            _t1119 = _t1121
                        end
                        _t1117 = _t1119
                    end
                    _t1115 = _t1117
                end
                _t1113 = _t1115
            end
            _t1110 = _t1113
        end
        _t1107 = _t1110
    end
    result570 = _t1107
    record_span!(parser, span_start569, "Value")
    return result570
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start574 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int571 = consume_terminal!(parser, "INT")
    int_3572 = consume_terminal!(parser, "INT")
    int_4573 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1131 = Proto.DateValue(year=Int32(int571), month=Int32(int_3572), day=Int32(int_4573))
    result575 = _t1131
    record_span!(parser, span_start574, "DateValue")
    return result575
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start583 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int576 = consume_terminal!(parser, "INT")
    int_3577 = consume_terminal!(parser, "INT")
    int_4578 = consume_terminal!(parser, "INT")
    int_5579 = consume_terminal!(parser, "INT")
    int_6580 = consume_terminal!(parser, "INT")
    int_7581 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1132 = consume_terminal!(parser, "INT")
    else
        _t1132 = nothing
    end
    int_8582 = _t1132
    consume_literal!(parser, ")")
    _t1133 = Proto.DateTimeValue(year=Int32(int576), month=Int32(int_3577), day=Int32(int_4578), hour=Int32(int_5579), minute=Int32(int_6580), second=Int32(int_7581), microsecond=Int32((!isnothing(int_8582) ? int_8582 : 0)))
    result584 = _t1133
    record_span!(parser, span_start583, "DateTimeValue")
    return result584
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1134 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1135 = 1
        else
            _t1135 = -1
        end
        _t1134 = _t1135
    end
    prediction585 = _t1134
    if prediction585 == 1
        consume_literal!(parser, "false")
        _t1136 = false
    else
        if prediction585 == 0
            consume_literal!(parser, "true")
            _t1137 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1136 = _t1137
    end
    return _t1136
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start590 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs586 = Proto.FragmentId[]
    cond587 = match_lookahead_literal(parser, ":", 0)
    while cond587
        _t1138 = parse_fragment_id(parser)
        item588 = _t1138
        push!(xs586, item588)
        cond587 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids589 = xs586
    consume_literal!(parser, ")")
    _t1139 = Proto.Sync(fragments=fragment_ids589)
    result591 = _t1139
    record_span!(parser, span_start590, "Sync")
    return result591
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start593 = span_start(parser)
    consume_literal!(parser, ":")
    symbol592 = consume_terminal!(parser, "SYMBOL")
    result594 = Proto.FragmentId(Vector{UInt8}(symbol592))
    record_span!(parser, span_start593, "FragmentId")
    return result594
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start597 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1141 = parse_epoch_writes(parser)
        _t1140 = _t1141
    else
        _t1140 = nothing
    end
    epoch_writes595 = _t1140
    if match_lookahead_literal(parser, "(", 0)
        _t1143 = parse_epoch_reads(parser)
        _t1142 = _t1143
    else
        _t1142 = nothing
    end
    epoch_reads596 = _t1142
    consume_literal!(parser, ")")
    _t1144 = Proto.Epoch(writes=(!isnothing(epoch_writes595) ? epoch_writes595 : Proto.Write[]), reads=(!isnothing(epoch_reads596) ? epoch_reads596 : Proto.Read[]))
    result598 = _t1144
    record_span!(parser, span_start597, "Epoch")
    return result598
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs599 = Proto.Write[]
    cond600 = match_lookahead_literal(parser, "(", 0)
    while cond600
        _t1145 = parse_write(parser)
        item601 = _t1145
        push!(xs599, item601)
        cond600 = match_lookahead_literal(parser, "(", 0)
    end
    writes602 = xs599
    consume_literal!(parser, ")")
    return writes602
end

function parse_write(parser::ParserState)::Proto.Write
    span_start608 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1147 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1148 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1149 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1150 = 2
                    else
                        _t1150 = -1
                    end
                    _t1149 = _t1150
                end
                _t1148 = _t1149
            end
            _t1147 = _t1148
        end
        _t1146 = _t1147
    else
        _t1146 = -1
    end
    prediction603 = _t1146
    if prediction603 == 3
        _t1152 = parse_snapshot(parser)
        snapshot607 = _t1152
        _t1153 = Proto.Write(write_type=OneOf(:snapshot, snapshot607))
        _t1151 = _t1153
    else
        if prediction603 == 2
            _t1155 = parse_context(parser)
            context606 = _t1155
            _t1156 = Proto.Write(write_type=OneOf(:context, context606))
            _t1154 = _t1156
        else
            if prediction603 == 1
                _t1158 = parse_undefine(parser)
                undefine605 = _t1158
                _t1159 = Proto.Write(write_type=OneOf(:undefine, undefine605))
                _t1157 = _t1159
            else
                if prediction603 == 0
                    _t1161 = parse_define(parser)
                    define604 = _t1161
                    _t1162 = Proto.Write(write_type=OneOf(:define, define604))
                    _t1160 = _t1162
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1157 = _t1160
            end
            _t1154 = _t1157
        end
        _t1151 = _t1154
    end
    result609 = _t1151
    record_span!(parser, span_start608, "Write")
    return result609
end

function parse_define(parser::ParserState)::Proto.Define
    span_start611 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1163 = parse_fragment(parser)
    fragment610 = _t1163
    consume_literal!(parser, ")")
    _t1164 = Proto.Define(fragment=fragment610)
    result612 = _t1164
    record_span!(parser, span_start611, "Define")
    return result612
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start618 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1165 = parse_new_fragment_id(parser)
    new_fragment_id613 = _t1165
    xs614 = Proto.Declaration[]
    cond615 = match_lookahead_literal(parser, "(", 0)
    while cond615
        _t1166 = parse_declaration(parser)
        item616 = _t1166
        push!(xs614, item616)
        cond615 = match_lookahead_literal(parser, "(", 0)
    end
    declarations617 = xs614
    consume_literal!(parser, ")")
    result619 = construct_fragment(parser, new_fragment_id613, declarations617)
    record_span!(parser, span_start618, "Fragment")
    return result619
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start621 = span_start(parser)
    _t1167 = parse_fragment_id(parser)
    fragment_id620 = _t1167
    start_fragment!(parser, fragment_id620)
    result622 = fragment_id620
    record_span!(parser, span_start621, "FragmentId")
    return result622
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start628 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1169 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1170 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1171 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1172 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1173 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1174 = 1
                            else
                                _t1174 = -1
                            end
                            _t1173 = _t1174
                        end
                        _t1172 = _t1173
                    end
                    _t1171 = _t1172
                end
                _t1170 = _t1171
            end
            _t1169 = _t1170
        end
        _t1168 = _t1169
    else
        _t1168 = -1
    end
    prediction623 = _t1168
    if prediction623 == 3
        _t1176 = parse_data(parser)
        data627 = _t1176
        _t1177 = Proto.Declaration(declaration_type=OneOf(:data, data627))
        _t1175 = _t1177
    else
        if prediction623 == 2
            _t1179 = parse_constraint(parser)
            constraint626 = _t1179
            _t1180 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint626))
            _t1178 = _t1180
        else
            if prediction623 == 1
                _t1182 = parse_algorithm(parser)
                algorithm625 = _t1182
                _t1183 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm625))
                _t1181 = _t1183
            else
                if prediction623 == 0
                    _t1185 = parse_def(parser)
                    def624 = _t1185
                    _t1186 = Proto.Declaration(declaration_type=OneOf(:def, def624))
                    _t1184 = _t1186
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1181 = _t1184
            end
            _t1178 = _t1181
        end
        _t1175 = _t1178
    end
    result629 = _t1175
    record_span!(parser, span_start628, "Declaration")
    return result629
end

function parse_def(parser::ParserState)::Proto.Def
    span_start633 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1187 = parse_relation_id(parser)
    relation_id630 = _t1187
    _t1188 = parse_abstraction(parser)
    abstraction631 = _t1188
    if match_lookahead_literal(parser, "(", 0)
        _t1190 = parse_attrs(parser)
        _t1189 = _t1190
    else
        _t1189 = nothing
    end
    attrs632 = _t1189
    consume_literal!(parser, ")")
    _t1191 = Proto.Def(name=relation_id630, body=abstraction631, attrs=(!isnothing(attrs632) ? attrs632 : Proto.Attribute[]))
    result634 = _t1191
    record_span!(parser, span_start633, "Def")
    return result634
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start638 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1192 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1193 = 1
        else
            _t1193 = -1
        end
        _t1192 = _t1193
    end
    prediction635 = _t1192
    if prediction635 == 1
        uint128637 = consume_terminal!(parser, "UINT128")
        _t1194 = Proto.RelationId(uint128637.low, uint128637.high)
    else
        if prediction635 == 0
            consume_literal!(parser, ":")
            symbol636 = consume_terminal!(parser, "SYMBOL")
            _t1195 = relation_id_from_string(parser, symbol636)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1194 = _t1195
    end
    result639 = _t1194
    record_span!(parser, span_start638, "RelationId")
    return result639
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start642 = span_start(parser)
    consume_literal!(parser, "(")
    _t1196 = parse_bindings(parser)
    bindings640 = _t1196
    _t1197 = parse_formula(parser)
    formula641 = _t1197
    consume_literal!(parser, ")")
    _t1198 = Proto.Abstraction(vars=vcat(bindings640[1], !isnothing(bindings640[2]) ? bindings640[2] : []), value=formula641)
    result643 = _t1198
    record_span!(parser, span_start642, "Abstraction")
    return result643
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs644 = Proto.Binding[]
    cond645 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond645
        _t1199 = parse_binding(parser)
        item646 = _t1199
        push!(xs644, item646)
        cond645 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings647 = xs644
    if match_lookahead_literal(parser, "|", 0)
        _t1201 = parse_value_bindings(parser)
        _t1200 = _t1201
    else
        _t1200 = nothing
    end
    value_bindings648 = _t1200
    consume_literal!(parser, "]")
    return (bindings647, (!isnothing(value_bindings648) ? value_bindings648 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start651 = span_start(parser)
    symbol649 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1202 = parse_type(parser)
    type650 = _t1202
    _t1203 = Proto.Var(name=symbol649)
    _t1204 = Proto.Binding(var=_t1203, var"#type"=type650)
    result652 = _t1204
    record_span!(parser, span_start651, "Binding")
    return result652
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start665 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1205 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t1206 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t1207 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t1208 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t1209 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t1210 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t1211 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t1212 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t1213 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t1214 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t1215 = 9
                                            else
                                                _t1215 = -1
                                            end
                                            _t1214 = _t1215
                                        end
                                        _t1213 = _t1214
                                    end
                                    _t1212 = _t1213
                                end
                                _t1211 = _t1212
                            end
                            _t1210 = _t1211
                        end
                        _t1209 = _t1210
                    end
                    _t1208 = _t1209
                end
                _t1207 = _t1208
            end
            _t1206 = _t1207
        end
        _t1205 = _t1206
    end
    prediction653 = _t1205
    if prediction653 == 10
        _t1217 = parse_boolean_type(parser)
        boolean_type664 = _t1217
        _t1218 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type664))
        _t1216 = _t1218
    else
        if prediction653 == 9
            _t1220 = parse_decimal_type(parser)
            decimal_type663 = _t1220
            _t1221 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type663))
            _t1219 = _t1221
        else
            if prediction653 == 8
                _t1223 = parse_missing_type(parser)
                missing_type662 = _t1223
                _t1224 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type662))
                _t1222 = _t1224
            else
                if prediction653 == 7
                    _t1226 = parse_datetime_type(parser)
                    datetime_type661 = _t1226
                    _t1227 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type661))
                    _t1225 = _t1227
                else
                    if prediction653 == 6
                        _t1229 = parse_date_type(parser)
                        date_type660 = _t1229
                        _t1230 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type660))
                        _t1228 = _t1230
                    else
                        if prediction653 == 5
                            _t1232 = parse_int128_type(parser)
                            int128_type659 = _t1232
                            _t1233 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type659))
                            _t1231 = _t1233
                        else
                            if prediction653 == 4
                                _t1235 = parse_uint128_type(parser)
                                uint128_type658 = _t1235
                                _t1236 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type658))
                                _t1234 = _t1236
                            else
                                if prediction653 == 3
                                    _t1238 = parse_float_type(parser)
                                    float_type657 = _t1238
                                    _t1239 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type657))
                                    _t1237 = _t1239
                                else
                                    if prediction653 == 2
                                        _t1241 = parse_int_type(parser)
                                        int_type656 = _t1241
                                        _t1242 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type656))
                                        _t1240 = _t1242
                                    else
                                        if prediction653 == 1
                                            _t1244 = parse_string_type(parser)
                                            string_type655 = _t1244
                                            _t1245 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type655))
                                            _t1243 = _t1245
                                        else
                                            if prediction653 == 0
                                                _t1247 = parse_unspecified_type(parser)
                                                unspecified_type654 = _t1247
                                                _t1248 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type654))
                                                _t1246 = _t1248
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t1243 = _t1246
                                        end
                                        _t1240 = _t1243
                                    end
                                    _t1237 = _t1240
                                end
                                _t1234 = _t1237
                            end
                            _t1231 = _t1234
                        end
                        _t1228 = _t1231
                    end
                    _t1225 = _t1228
                end
                _t1222 = _t1225
            end
            _t1219 = _t1222
        end
        _t1216 = _t1219
    end
    result666 = _t1216
    record_span!(parser, span_start665, "Type")
    return result666
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start667 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1249 = Proto.UnspecifiedType()
    result668 = _t1249
    record_span!(parser, span_start667, "UnspecifiedType")
    return result668
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start669 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1250 = Proto.StringType()
    result670 = _t1250
    record_span!(parser, span_start669, "StringType")
    return result670
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start671 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1251 = Proto.IntType()
    result672 = _t1251
    record_span!(parser, span_start671, "IntType")
    return result672
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start673 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1252 = Proto.FloatType()
    result674 = _t1252
    record_span!(parser, span_start673, "FloatType")
    return result674
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start675 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1253 = Proto.UInt128Type()
    result676 = _t1253
    record_span!(parser, span_start675, "UInt128Type")
    return result676
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start677 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1254 = Proto.Int128Type()
    result678 = _t1254
    record_span!(parser, span_start677, "Int128Type")
    return result678
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start679 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1255 = Proto.DateType()
    result680 = _t1255
    record_span!(parser, span_start679, "DateType")
    return result680
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start681 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1256 = Proto.DateTimeType()
    result682 = _t1256
    record_span!(parser, span_start681, "DateTimeType")
    return result682
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start683 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1257 = Proto.MissingType()
    result684 = _t1257
    record_span!(parser, span_start683, "MissingType")
    return result684
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start687 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int685 = consume_terminal!(parser, "INT")
    int_3686 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1258 = Proto.DecimalType(precision=Int32(int685), scale=Int32(int_3686))
    result688 = _t1258
    record_span!(parser, span_start687, "DecimalType")
    return result688
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start689 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1259 = Proto.BooleanType()
    result690 = _t1259
    record_span!(parser, span_start689, "BooleanType")
    return result690
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs691 = Proto.Binding[]
    cond692 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond692
        _t1260 = parse_binding(parser)
        item693 = _t1260
        push!(xs691, item693)
        cond692 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings694 = xs691
    return bindings694
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start709 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1262 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1263 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1264 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1265 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1266 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1267 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1268 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1269 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1270 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1271 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1272 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1273 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1274 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1275 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1276 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1277 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1278 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1279 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1280 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1281 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1282 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1283 = 10
                                                                                            else
                                                                                                _t1283 = -1
                                                                                            end
                                                                                            _t1282 = _t1283
                                                                                        end
                                                                                        _t1281 = _t1282
                                                                                    end
                                                                                    _t1280 = _t1281
                                                                                end
                                                                                _t1279 = _t1280
                                                                            end
                                                                            _t1278 = _t1279
                                                                        end
                                                                        _t1277 = _t1278
                                                                    end
                                                                    _t1276 = _t1277
                                                                end
                                                                _t1275 = _t1276
                                                            end
                                                            _t1274 = _t1275
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
                                end
                                _t1267 = _t1268
                            end
                            _t1266 = _t1267
                        end
                        _t1265 = _t1266
                    end
                    _t1264 = _t1265
                end
                _t1263 = _t1264
            end
            _t1262 = _t1263
        end
        _t1261 = _t1262
    else
        _t1261 = -1
    end
    prediction695 = _t1261
    if prediction695 == 12
        _t1285 = parse_cast(parser)
        cast708 = _t1285
        _t1286 = Proto.Formula(formula_type=OneOf(:cast, cast708))
        _t1284 = _t1286
    else
        if prediction695 == 11
            _t1288 = parse_rel_atom(parser)
            rel_atom707 = _t1288
            _t1289 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom707))
            _t1287 = _t1289
        else
            if prediction695 == 10
                _t1291 = parse_primitive(parser)
                primitive706 = _t1291
                _t1292 = Proto.Formula(formula_type=OneOf(:primitive, primitive706))
                _t1290 = _t1292
            else
                if prediction695 == 9
                    _t1294 = parse_pragma(parser)
                    pragma705 = _t1294
                    _t1295 = Proto.Formula(formula_type=OneOf(:pragma, pragma705))
                    _t1293 = _t1295
                else
                    if prediction695 == 8
                        _t1297 = parse_atom(parser)
                        atom704 = _t1297
                        _t1298 = Proto.Formula(formula_type=OneOf(:atom, atom704))
                        _t1296 = _t1298
                    else
                        if prediction695 == 7
                            _t1300 = parse_ffi(parser)
                            ffi703 = _t1300
                            _t1301 = Proto.Formula(formula_type=OneOf(:ffi, ffi703))
                            _t1299 = _t1301
                        else
                            if prediction695 == 6
                                _t1303 = parse_not(parser)
                                not702 = _t1303
                                _t1304 = Proto.Formula(formula_type=OneOf(:not, not702))
                                _t1302 = _t1304
                            else
                                if prediction695 == 5
                                    _t1306 = parse_disjunction(parser)
                                    disjunction701 = _t1306
                                    _t1307 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction701))
                                    _t1305 = _t1307
                                else
                                    if prediction695 == 4
                                        _t1309 = parse_conjunction(parser)
                                        conjunction700 = _t1309
                                        _t1310 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction700))
                                        _t1308 = _t1310
                                    else
                                        if prediction695 == 3
                                            _t1312 = parse_reduce(parser)
                                            reduce699 = _t1312
                                            _t1313 = Proto.Formula(formula_type=OneOf(:reduce, reduce699))
                                            _t1311 = _t1313
                                        else
                                            if prediction695 == 2
                                                _t1315 = parse_exists(parser)
                                                exists698 = _t1315
                                                _t1316 = Proto.Formula(formula_type=OneOf(:exists, exists698))
                                                _t1314 = _t1316
                                            else
                                                if prediction695 == 1
                                                    _t1318 = parse_false(parser)
                                                    false697 = _t1318
                                                    _t1319 = Proto.Formula(formula_type=OneOf(:disjunction, false697))
                                                    _t1317 = _t1319
                                                else
                                                    if prediction695 == 0
                                                        _t1321 = parse_true(parser)
                                                        true696 = _t1321
                                                        _t1322 = Proto.Formula(formula_type=OneOf(:conjunction, true696))
                                                        _t1320 = _t1322
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1317 = _t1320
                                                end
                                                _t1314 = _t1317
                                            end
                                            _t1311 = _t1314
                                        end
                                        _t1308 = _t1311
                                    end
                                    _t1305 = _t1308
                                end
                                _t1302 = _t1305
                            end
                            _t1299 = _t1302
                        end
                        _t1296 = _t1299
                    end
                    _t1293 = _t1296
                end
                _t1290 = _t1293
            end
            _t1287 = _t1290
        end
        _t1284 = _t1287
    end
    result710 = _t1284
    record_span!(parser, span_start709, "Formula")
    return result710
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start711 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1323 = Proto.Conjunction(args=Proto.Formula[])
    result712 = _t1323
    record_span!(parser, span_start711, "Conjunction")
    return result712
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start713 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1324 = Proto.Disjunction(args=Proto.Formula[])
    result714 = _t1324
    record_span!(parser, span_start713, "Disjunction")
    return result714
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start717 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1325 = parse_bindings(parser)
    bindings715 = _t1325
    _t1326 = parse_formula(parser)
    formula716 = _t1326
    consume_literal!(parser, ")")
    _t1327 = Proto.Abstraction(vars=vcat(bindings715[1], !isnothing(bindings715[2]) ? bindings715[2] : []), value=formula716)
    _t1328 = Proto.Exists(body=_t1327)
    result718 = _t1328
    record_span!(parser, span_start717, "Exists")
    return result718
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start722 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1329 = parse_abstraction(parser)
    abstraction719 = _t1329
    _t1330 = parse_abstraction(parser)
    abstraction_3720 = _t1330
    _t1331 = parse_terms(parser)
    terms721 = _t1331
    consume_literal!(parser, ")")
    _t1332 = Proto.Reduce(op=abstraction719, body=abstraction_3720, terms=terms721)
    result723 = _t1332
    record_span!(parser, span_start722, "Reduce")
    return result723
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs724 = Proto.Term[]
    cond725 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond725
        _t1333 = parse_term(parser)
        item726 = _t1333
        push!(xs724, item726)
        cond725 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms727 = xs724
    consume_literal!(parser, ")")
    return terms727
end

function parse_term(parser::ParserState)::Proto.Term
    span_start731 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1334 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1335 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1336 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1337 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1338 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1339 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1340 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1341 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1342 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t1343 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t1344 = 1
                                            else
                                                _t1344 = -1
                                            end
                                            _t1343 = _t1344
                                        end
                                        _t1342 = _t1343
                                    end
                                    _t1341 = _t1342
                                end
                                _t1340 = _t1341
                            end
                            _t1339 = _t1340
                        end
                        _t1338 = _t1339
                    end
                    _t1337 = _t1338
                end
                _t1336 = _t1337
            end
            _t1335 = _t1336
        end
        _t1334 = _t1335
    end
    prediction728 = _t1334
    if prediction728 == 1
        _t1346 = parse_constant(parser)
        constant730 = _t1346
        _t1347 = Proto.Term(term_type=OneOf(:constant, constant730))
        _t1345 = _t1347
    else
        if prediction728 == 0
            _t1349 = parse_var(parser)
            var729 = _t1349
            _t1350 = Proto.Term(term_type=OneOf(:var, var729))
            _t1348 = _t1350
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1345 = _t1348
    end
    result732 = _t1345
    record_span!(parser, span_start731, "Term")
    return result732
end

function parse_var(parser::ParserState)::Proto.Var
    span_start734 = span_start(parser)
    symbol733 = consume_terminal!(parser, "SYMBOL")
    _t1351 = Proto.Var(name=symbol733)
    result735 = _t1351
    record_span!(parser, span_start734, "Var")
    return result735
end

function parse_constant(parser::ParserState)::Proto.Value
    span_start737 = span_start(parser)
    _t1352 = parse_value(parser)
    value736 = _t1352
    result738 = value736
    record_span!(parser, span_start737, "Value")
    return result738
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start743 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs739 = Proto.Formula[]
    cond740 = match_lookahead_literal(parser, "(", 0)
    while cond740
        _t1353 = parse_formula(parser)
        item741 = _t1353
        push!(xs739, item741)
        cond740 = match_lookahead_literal(parser, "(", 0)
    end
    formulas742 = xs739
    consume_literal!(parser, ")")
    _t1354 = Proto.Conjunction(args=formulas742)
    result744 = _t1354
    record_span!(parser, span_start743, "Conjunction")
    return result744
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start749 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs745 = Proto.Formula[]
    cond746 = match_lookahead_literal(parser, "(", 0)
    while cond746
        _t1355 = parse_formula(parser)
        item747 = _t1355
        push!(xs745, item747)
        cond746 = match_lookahead_literal(parser, "(", 0)
    end
    formulas748 = xs745
    consume_literal!(parser, ")")
    _t1356 = Proto.Disjunction(args=formulas748)
    result750 = _t1356
    record_span!(parser, span_start749, "Disjunction")
    return result750
end

function parse_not(parser::ParserState)::Proto.Not
    span_start752 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1357 = parse_formula(parser)
    formula751 = _t1357
    consume_literal!(parser, ")")
    _t1358 = Proto.Not(arg=formula751)
    result753 = _t1358
    record_span!(parser, span_start752, "Not")
    return result753
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start757 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1359 = parse_name(parser)
    name754 = _t1359
    _t1360 = parse_ffi_args(parser)
    ffi_args755 = _t1360
    _t1361 = parse_terms(parser)
    terms756 = _t1361
    consume_literal!(parser, ")")
    _t1362 = Proto.FFI(name=name754, args=ffi_args755, terms=terms756)
    result758 = _t1362
    record_span!(parser, span_start757, "FFI")
    return result758
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol759 = consume_terminal!(parser, "SYMBOL")
    return symbol759
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs760 = Proto.Abstraction[]
    cond761 = match_lookahead_literal(parser, "(", 0)
    while cond761
        _t1363 = parse_abstraction(parser)
        item762 = _t1363
        push!(xs760, item762)
        cond761 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions763 = xs760
    consume_literal!(parser, ")")
    return abstractions763
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start769 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1364 = parse_relation_id(parser)
    relation_id764 = _t1364
    xs765 = Proto.Term[]
    cond766 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond766
        _t1365 = parse_term(parser)
        item767 = _t1365
        push!(xs765, item767)
        cond766 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms768 = xs765
    consume_literal!(parser, ")")
    _t1366 = Proto.Atom(name=relation_id764, terms=terms768)
    result770 = _t1366
    record_span!(parser, span_start769, "Atom")
    return result770
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start776 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1367 = parse_name(parser)
    name771 = _t1367
    xs772 = Proto.Term[]
    cond773 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond773
        _t1368 = parse_term(parser)
        item774 = _t1368
        push!(xs772, item774)
        cond773 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms775 = xs772
    consume_literal!(parser, ")")
    _t1369 = Proto.Pragma(name=name771, terms=terms775)
    result777 = _t1369
    record_span!(parser, span_start776, "Pragma")
    return result777
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start793 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1371 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1372 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1373 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1374 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1375 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1376 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1377 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1378 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1379 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1380 = 7
                                            else
                                                _t1380 = -1
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
    else
        _t1370 = -1
    end
    prediction778 = _t1370
    if prediction778 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1382 = parse_name(parser)
        name788 = _t1382
        xs789 = Proto.RelTerm[]
        cond790 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond790
            _t1383 = parse_rel_term(parser)
            item791 = _t1383
            push!(xs789, item791)
            cond790 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms792 = xs789
        consume_literal!(parser, ")")
        _t1384 = Proto.Primitive(name=name788, terms=rel_terms792)
        _t1381 = _t1384
    else
        if prediction778 == 8
            _t1386 = parse_divide(parser)
            divide787 = _t1386
            _t1385 = divide787
        else
            if prediction778 == 7
                _t1388 = parse_multiply(parser)
                multiply786 = _t1388
                _t1387 = multiply786
            else
                if prediction778 == 6
                    _t1390 = parse_minus(parser)
                    minus785 = _t1390
                    _t1389 = minus785
                else
                    if prediction778 == 5
                        _t1392 = parse_add(parser)
                        add784 = _t1392
                        _t1391 = add784
                    else
                        if prediction778 == 4
                            _t1394 = parse_gt_eq(parser)
                            gt_eq783 = _t1394
                            _t1393 = gt_eq783
                        else
                            if prediction778 == 3
                                _t1396 = parse_gt(parser)
                                gt782 = _t1396
                                _t1395 = gt782
                            else
                                if prediction778 == 2
                                    _t1398 = parse_lt_eq(parser)
                                    lt_eq781 = _t1398
                                    _t1397 = lt_eq781
                                else
                                    if prediction778 == 1
                                        _t1400 = parse_lt(parser)
                                        lt780 = _t1400
                                        _t1399 = lt780
                                    else
                                        if prediction778 == 0
                                            _t1402 = parse_eq(parser)
                                            eq779 = _t1402
                                            _t1401 = eq779
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1399 = _t1401
                                    end
                                    _t1397 = _t1399
                                end
                                _t1395 = _t1397
                            end
                            _t1393 = _t1395
                        end
                        _t1391 = _t1393
                    end
                    _t1389 = _t1391
                end
                _t1387 = _t1389
            end
            _t1385 = _t1387
        end
        _t1381 = _t1385
    end
    result794 = _t1381
    record_span!(parser, span_start793, "Primitive")
    return result794
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start797 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1403 = parse_term(parser)
    term795 = _t1403
    _t1404 = parse_term(parser)
    term_3796 = _t1404
    consume_literal!(parser, ")")
    _t1405 = Proto.RelTerm(rel_term_type=OneOf(:term, term795))
    _t1406 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3796))
    _t1407 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1405, _t1406])
    result798 = _t1407
    record_span!(parser, span_start797, "Primitive")
    return result798
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start801 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1408 = parse_term(parser)
    term799 = _t1408
    _t1409 = parse_term(parser)
    term_3800 = _t1409
    consume_literal!(parser, ")")
    _t1410 = Proto.RelTerm(rel_term_type=OneOf(:term, term799))
    _t1411 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3800))
    _t1412 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1410, _t1411])
    result802 = _t1412
    record_span!(parser, span_start801, "Primitive")
    return result802
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start805 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1413 = parse_term(parser)
    term803 = _t1413
    _t1414 = parse_term(parser)
    term_3804 = _t1414
    consume_literal!(parser, ")")
    _t1415 = Proto.RelTerm(rel_term_type=OneOf(:term, term803))
    _t1416 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3804))
    _t1417 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1415, _t1416])
    result806 = _t1417
    record_span!(parser, span_start805, "Primitive")
    return result806
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start809 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1418 = parse_term(parser)
    term807 = _t1418
    _t1419 = parse_term(parser)
    term_3808 = _t1419
    consume_literal!(parser, ")")
    _t1420 = Proto.RelTerm(rel_term_type=OneOf(:term, term807))
    _t1421 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3808))
    _t1422 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1420, _t1421])
    result810 = _t1422
    record_span!(parser, span_start809, "Primitive")
    return result810
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start813 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1423 = parse_term(parser)
    term811 = _t1423
    _t1424 = parse_term(parser)
    term_3812 = _t1424
    consume_literal!(parser, ")")
    _t1425 = Proto.RelTerm(rel_term_type=OneOf(:term, term811))
    _t1426 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3812))
    _t1427 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1425, _t1426])
    result814 = _t1427
    record_span!(parser, span_start813, "Primitive")
    return result814
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start818 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1428 = parse_term(parser)
    term815 = _t1428
    _t1429 = parse_term(parser)
    term_3816 = _t1429
    _t1430 = parse_term(parser)
    term_4817 = _t1430
    consume_literal!(parser, ")")
    _t1431 = Proto.RelTerm(rel_term_type=OneOf(:term, term815))
    _t1432 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3816))
    _t1433 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4817))
    _t1434 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1431, _t1432, _t1433])
    result819 = _t1434
    record_span!(parser, span_start818, "Primitive")
    return result819
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start823 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1435 = parse_term(parser)
    term820 = _t1435
    _t1436 = parse_term(parser)
    term_3821 = _t1436
    _t1437 = parse_term(parser)
    term_4822 = _t1437
    consume_literal!(parser, ")")
    _t1438 = Proto.RelTerm(rel_term_type=OneOf(:term, term820))
    _t1439 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3821))
    _t1440 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4822))
    _t1441 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1438, _t1439, _t1440])
    result824 = _t1441
    record_span!(parser, span_start823, "Primitive")
    return result824
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start828 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1442 = parse_term(parser)
    term825 = _t1442
    _t1443 = parse_term(parser)
    term_3826 = _t1443
    _t1444 = parse_term(parser)
    term_4827 = _t1444
    consume_literal!(parser, ")")
    _t1445 = Proto.RelTerm(rel_term_type=OneOf(:term, term825))
    _t1446 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3826))
    _t1447 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4827))
    _t1448 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1445, _t1446, _t1447])
    result829 = _t1448
    record_span!(parser, span_start828, "Primitive")
    return result829
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start833 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1449 = parse_term(parser)
    term830 = _t1449
    _t1450 = parse_term(parser)
    term_3831 = _t1450
    _t1451 = parse_term(parser)
    term_4832 = _t1451
    consume_literal!(parser, ")")
    _t1452 = Proto.RelTerm(rel_term_type=OneOf(:term, term830))
    _t1453 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3831))
    _t1454 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4832))
    _t1455 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1452, _t1453, _t1454])
    result834 = _t1455
    record_span!(parser, span_start833, "Primitive")
    return result834
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start838 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1456 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1457 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1458 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1459 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1460 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1461 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1462 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1463 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1464 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1465 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1466 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1467 = 1
                                                else
                                                    _t1467 = -1
                                                end
                                                _t1466 = _t1467
                                            end
                                            _t1465 = _t1466
                                        end
                                        _t1464 = _t1465
                                    end
                                    _t1463 = _t1464
                                end
                                _t1462 = _t1463
                            end
                            _t1461 = _t1462
                        end
                        _t1460 = _t1461
                    end
                    _t1459 = _t1460
                end
                _t1458 = _t1459
            end
            _t1457 = _t1458
        end
        _t1456 = _t1457
    end
    prediction835 = _t1456
    if prediction835 == 1
        _t1469 = parse_term(parser)
        term837 = _t1469
        _t1470 = Proto.RelTerm(rel_term_type=OneOf(:term, term837))
        _t1468 = _t1470
    else
        if prediction835 == 0
            _t1472 = parse_specialized_value(parser)
            specialized_value836 = _t1472
            _t1473 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value836))
            _t1471 = _t1473
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1468 = _t1471
    end
    result839 = _t1468
    record_span!(parser, span_start838, "RelTerm")
    return result839
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start841 = span_start(parser)
    consume_literal!(parser, "#")
    _t1474 = parse_value(parser)
    value840 = _t1474
    result842 = value840
    record_span!(parser, span_start841, "Value")
    return result842
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start848 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1475 = parse_name(parser)
    name843 = _t1475
    xs844 = Proto.RelTerm[]
    cond845 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond845
        _t1476 = parse_rel_term(parser)
        item846 = _t1476
        push!(xs844, item846)
        cond845 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms847 = xs844
    consume_literal!(parser, ")")
    _t1477 = Proto.RelAtom(name=name843, terms=rel_terms847)
    result849 = _t1477
    record_span!(parser, span_start848, "RelAtom")
    return result849
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start852 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1478 = parse_term(parser)
    term850 = _t1478
    _t1479 = parse_term(parser)
    term_3851 = _t1479
    consume_literal!(parser, ")")
    _t1480 = Proto.Cast(input=term850, result=term_3851)
    result853 = _t1480
    record_span!(parser, span_start852, "Cast")
    return result853
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs854 = Proto.Attribute[]
    cond855 = match_lookahead_literal(parser, "(", 0)
    while cond855
        _t1481 = parse_attribute(parser)
        item856 = _t1481
        push!(xs854, item856)
        cond855 = match_lookahead_literal(parser, "(", 0)
    end
    attributes857 = xs854
    consume_literal!(parser, ")")
    return attributes857
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start863 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1482 = parse_name(parser)
    name858 = _t1482
    xs859 = Proto.Value[]
    cond860 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond860
        _t1483 = parse_value(parser)
        item861 = _t1483
        push!(xs859, item861)
        cond860 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values862 = xs859
    consume_literal!(parser, ")")
    _t1484 = Proto.Attribute(name=name858, args=values862)
    result864 = _t1484
    record_span!(parser, span_start863, "Attribute")
    return result864
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start870 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs865 = Proto.RelationId[]
    cond866 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond866
        _t1485 = parse_relation_id(parser)
        item867 = _t1485
        push!(xs865, item867)
        cond866 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids868 = xs865
    _t1486 = parse_script(parser)
    script869 = _t1486
    consume_literal!(parser, ")")
    _t1487 = Proto.Algorithm(var"#global"=relation_ids868, body=script869)
    result871 = _t1487
    record_span!(parser, span_start870, "Algorithm")
    return result871
end

function parse_script(parser::ParserState)::Proto.Script
    span_start876 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs872 = Proto.Construct[]
    cond873 = match_lookahead_literal(parser, "(", 0)
    while cond873
        _t1488 = parse_construct(parser)
        item874 = _t1488
        push!(xs872, item874)
        cond873 = match_lookahead_literal(parser, "(", 0)
    end
    constructs875 = xs872
    consume_literal!(parser, ")")
    _t1489 = Proto.Script(constructs=constructs875)
    result877 = _t1489
    record_span!(parser, span_start876, "Script")
    return result877
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start881 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1491 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1492 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1493 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1494 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1495 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1496 = 1
                            else
                                _t1496 = -1
                            end
                            _t1495 = _t1496
                        end
                        _t1494 = _t1495
                    end
                    _t1493 = _t1494
                end
                _t1492 = _t1493
            end
            _t1491 = _t1492
        end
        _t1490 = _t1491
    else
        _t1490 = -1
    end
    prediction878 = _t1490
    if prediction878 == 1
        _t1498 = parse_instruction(parser)
        instruction880 = _t1498
        _t1499 = Proto.Construct(construct_type=OneOf(:instruction, instruction880))
        _t1497 = _t1499
    else
        if prediction878 == 0
            _t1501 = parse_loop(parser)
            loop879 = _t1501
            _t1502 = Proto.Construct(construct_type=OneOf(:loop, loop879))
            _t1500 = _t1502
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1497 = _t1500
    end
    result882 = _t1497
    record_span!(parser, span_start881, "Construct")
    return result882
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start885 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1503 = parse_init(parser)
    init883 = _t1503
    _t1504 = parse_script(parser)
    script884 = _t1504
    consume_literal!(parser, ")")
    _t1505 = Proto.Loop(init=init883, body=script884)
    result886 = _t1505
    record_span!(parser, span_start885, "Loop")
    return result886
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs887 = Proto.Instruction[]
    cond888 = match_lookahead_literal(parser, "(", 0)
    while cond888
        _t1506 = parse_instruction(parser)
        item889 = _t1506
        push!(xs887, item889)
        cond888 = match_lookahead_literal(parser, "(", 0)
    end
    instructions890 = xs887
    consume_literal!(parser, ")")
    return instructions890
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start897 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1508 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1509 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1510 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1511 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1512 = 0
                        else
                            _t1512 = -1
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
    else
        _t1507 = -1
    end
    prediction891 = _t1507
    if prediction891 == 4
        _t1514 = parse_monus_def(parser)
        monus_def896 = _t1514
        _t1515 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def896))
        _t1513 = _t1515
    else
        if prediction891 == 3
            _t1517 = parse_monoid_def(parser)
            monoid_def895 = _t1517
            _t1518 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def895))
            _t1516 = _t1518
        else
            if prediction891 == 2
                _t1520 = parse_break(parser)
                break894 = _t1520
                _t1521 = Proto.Instruction(instr_type=OneOf(:var"#break", break894))
                _t1519 = _t1521
            else
                if prediction891 == 1
                    _t1523 = parse_upsert(parser)
                    upsert893 = _t1523
                    _t1524 = Proto.Instruction(instr_type=OneOf(:upsert, upsert893))
                    _t1522 = _t1524
                else
                    if prediction891 == 0
                        _t1526 = parse_assign(parser)
                        assign892 = _t1526
                        _t1527 = Proto.Instruction(instr_type=OneOf(:assign, assign892))
                        _t1525 = _t1527
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1522 = _t1525
                end
                _t1519 = _t1522
            end
            _t1516 = _t1519
        end
        _t1513 = _t1516
    end
    result898 = _t1513
    record_span!(parser, span_start897, "Instruction")
    return result898
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start902 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1528 = parse_relation_id(parser)
    relation_id899 = _t1528
    _t1529 = parse_abstraction(parser)
    abstraction900 = _t1529
    if match_lookahead_literal(parser, "(", 0)
        _t1531 = parse_attrs(parser)
        _t1530 = _t1531
    else
        _t1530 = nothing
    end
    attrs901 = _t1530
    consume_literal!(parser, ")")
    _t1532 = Proto.Assign(name=relation_id899, body=abstraction900, attrs=(!isnothing(attrs901) ? attrs901 : Proto.Attribute[]))
    result903 = _t1532
    record_span!(parser, span_start902, "Assign")
    return result903
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start907 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1533 = parse_relation_id(parser)
    relation_id904 = _t1533
    _t1534 = parse_abstraction_with_arity(parser)
    abstraction_with_arity905 = _t1534
    if match_lookahead_literal(parser, "(", 0)
        _t1536 = parse_attrs(parser)
        _t1535 = _t1536
    else
        _t1535 = nothing
    end
    attrs906 = _t1535
    consume_literal!(parser, ")")
    _t1537 = Proto.Upsert(name=relation_id904, body=abstraction_with_arity905[1], attrs=(!isnothing(attrs906) ? attrs906 : Proto.Attribute[]), value_arity=abstraction_with_arity905[2])
    result908 = _t1537
    record_span!(parser, span_start907, "Upsert")
    return result908
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1538 = parse_bindings(parser)
    bindings909 = _t1538
    _t1539 = parse_formula(parser)
    formula910 = _t1539
    consume_literal!(parser, ")")
    _t1540 = Proto.Abstraction(vars=vcat(bindings909[1], !isnothing(bindings909[2]) ? bindings909[2] : []), value=formula910)
    return (_t1540, length(bindings909[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start914 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1541 = parse_relation_id(parser)
    relation_id911 = _t1541
    _t1542 = parse_abstraction(parser)
    abstraction912 = _t1542
    if match_lookahead_literal(parser, "(", 0)
        _t1544 = parse_attrs(parser)
        _t1543 = _t1544
    else
        _t1543 = nothing
    end
    attrs913 = _t1543
    consume_literal!(parser, ")")
    _t1545 = Proto.Break(name=relation_id911, body=abstraction912, attrs=(!isnothing(attrs913) ? attrs913 : Proto.Attribute[]))
    result915 = _t1545
    record_span!(parser, span_start914, "Break")
    return result915
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start920 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1546 = parse_monoid(parser)
    monoid916 = _t1546
    _t1547 = parse_relation_id(parser)
    relation_id917 = _t1547
    _t1548 = parse_abstraction_with_arity(parser)
    abstraction_with_arity918 = _t1548
    if match_lookahead_literal(parser, "(", 0)
        _t1550 = parse_attrs(parser)
        _t1549 = _t1550
    else
        _t1549 = nothing
    end
    attrs919 = _t1549
    consume_literal!(parser, ")")
    _t1551 = Proto.MonoidDef(monoid=monoid916, name=relation_id917, body=abstraction_with_arity918[1], attrs=(!isnothing(attrs919) ? attrs919 : Proto.Attribute[]), value_arity=abstraction_with_arity918[2])
    result921 = _t1551
    record_span!(parser, span_start920, "MonoidDef")
    return result921
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start927 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1553 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1554 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1555 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1556 = 2
                    else
                        _t1556 = -1
                    end
                    _t1555 = _t1556
                end
                _t1554 = _t1555
            end
            _t1553 = _t1554
        end
        _t1552 = _t1553
    else
        _t1552 = -1
    end
    prediction922 = _t1552
    if prediction922 == 3
        _t1558 = parse_sum_monoid(parser)
        sum_monoid926 = _t1558
        _t1559 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid926))
        _t1557 = _t1559
    else
        if prediction922 == 2
            _t1561 = parse_max_monoid(parser)
            max_monoid925 = _t1561
            _t1562 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid925))
            _t1560 = _t1562
        else
            if prediction922 == 1
                _t1564 = parse_min_monoid(parser)
                min_monoid924 = _t1564
                _t1565 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid924))
                _t1563 = _t1565
            else
                if prediction922 == 0
                    _t1567 = parse_or_monoid(parser)
                    or_monoid923 = _t1567
                    _t1568 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid923))
                    _t1566 = _t1568
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1563 = _t1566
            end
            _t1560 = _t1563
        end
        _t1557 = _t1560
    end
    result928 = _t1557
    record_span!(parser, span_start927, "Monoid")
    return result928
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start929 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1569 = Proto.OrMonoid()
    result930 = _t1569
    record_span!(parser, span_start929, "OrMonoid")
    return result930
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start932 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1570 = parse_type(parser)
    type931 = _t1570
    consume_literal!(parser, ")")
    _t1571 = Proto.MinMonoid(var"#type"=type931)
    result933 = _t1571
    record_span!(parser, span_start932, "MinMonoid")
    return result933
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start935 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1572 = parse_type(parser)
    type934 = _t1572
    consume_literal!(parser, ")")
    _t1573 = Proto.MaxMonoid(var"#type"=type934)
    result936 = _t1573
    record_span!(parser, span_start935, "MaxMonoid")
    return result936
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start938 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1574 = parse_type(parser)
    type937 = _t1574
    consume_literal!(parser, ")")
    _t1575 = Proto.SumMonoid(var"#type"=type937)
    result939 = _t1575
    record_span!(parser, span_start938, "SumMonoid")
    return result939
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start944 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1576 = parse_monoid(parser)
    monoid940 = _t1576
    _t1577 = parse_relation_id(parser)
    relation_id941 = _t1577
    _t1578 = parse_abstraction_with_arity(parser)
    abstraction_with_arity942 = _t1578
    if match_lookahead_literal(parser, "(", 0)
        _t1580 = parse_attrs(parser)
        _t1579 = _t1580
    else
        _t1579 = nothing
    end
    attrs943 = _t1579
    consume_literal!(parser, ")")
    _t1581 = Proto.MonusDef(monoid=monoid940, name=relation_id941, body=abstraction_with_arity942[1], attrs=(!isnothing(attrs943) ? attrs943 : Proto.Attribute[]), value_arity=abstraction_with_arity942[2])
    result945 = _t1581
    record_span!(parser, span_start944, "MonusDef")
    return result945
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start950 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1582 = parse_relation_id(parser)
    relation_id946 = _t1582
    _t1583 = parse_abstraction(parser)
    abstraction947 = _t1583
    _t1584 = parse_functional_dependency_keys(parser)
    functional_dependency_keys948 = _t1584
    _t1585 = parse_functional_dependency_values(parser)
    functional_dependency_values949 = _t1585
    consume_literal!(parser, ")")
    _t1586 = Proto.FunctionalDependency(guard=abstraction947, keys=functional_dependency_keys948, values=functional_dependency_values949)
    _t1587 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1586), name=relation_id946)
    result951 = _t1587
    record_span!(parser, span_start950, "Constraint")
    return result951
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs952 = Proto.Var[]
    cond953 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond953
        _t1588 = parse_var(parser)
        item954 = _t1588
        push!(xs952, item954)
        cond953 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars955 = xs952
    consume_literal!(parser, ")")
    return vars955
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs956 = Proto.Var[]
    cond957 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond957
        _t1589 = parse_var(parser)
        item958 = _t1589
        push!(xs956, item958)
        cond957 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars959 = xs956
    consume_literal!(parser, ")")
    return vars959
end

function parse_data(parser::ParserState)::Proto.Data
    span_start964 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1591 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1592 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1593 = 1
                else
                    _t1593 = -1
                end
                _t1592 = _t1593
            end
            _t1591 = _t1592
        end
        _t1590 = _t1591
    else
        _t1590 = -1
    end
    prediction960 = _t1590
    if prediction960 == 2
        _t1595 = parse_csv_data(parser)
        csv_data963 = _t1595
        _t1596 = Proto.Data(data_type=OneOf(:csv_data, csv_data963))
        _t1594 = _t1596
    else
        if prediction960 == 1
            _t1598 = parse_betree_relation(parser)
            betree_relation962 = _t1598
            _t1599 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation962))
            _t1597 = _t1599
        else
            if prediction960 == 0
                _t1601 = parse_rel_edb(parser)
                rel_edb961 = _t1601
                _t1602 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb961))
                _t1600 = _t1602
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1597 = _t1600
        end
        _t1594 = _t1597
    end
    result965 = _t1594
    record_span!(parser, span_start964, "Data")
    return result965
end

function parse_rel_edb(parser::ParserState)::Proto.RelEDB
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t1603 = parse_relation_id(parser)
    relation_id966 = _t1603
    _t1604 = parse_rel_edb_path(parser)
    rel_edb_path967 = _t1604
    _t1605 = parse_rel_edb_types(parser)
    rel_edb_types968 = _t1605
    consume_literal!(parser, ")")
    _t1606 = Proto.RelEDB(target_id=relation_id966, path=rel_edb_path967, types=rel_edb_types968)
    result970 = _t1606
    record_span!(parser, span_start969, "RelEDB")
    return result970
end

function parse_rel_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs971 = String[]
    cond972 = match_lookahead_terminal(parser, "STRING", 0)
    while cond972
        item973 = consume_terminal!(parser, "STRING")
        push!(xs971, item973)
        cond972 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings974 = xs971
    consume_literal!(parser, "]")
    return strings974
end

function parse_rel_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs975 = Proto.var"#Type"[]
    cond976 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond976
        _t1607 = parse_type(parser)
        item977 = _t1607
        push!(xs975, item977)
        cond976 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types978 = xs975
    consume_literal!(parser, "]")
    return types978
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start981 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1608 = parse_relation_id(parser)
    relation_id979 = _t1608
    _t1609 = parse_betree_info(parser)
    betree_info980 = _t1609
    consume_literal!(parser, ")")
    _t1610 = Proto.BeTreeRelation(name=relation_id979, relation_info=betree_info980)
    result982 = _t1610
    record_span!(parser, span_start981, "BeTreeRelation")
    return result982
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start986 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1611 = parse_betree_info_key_types(parser)
    betree_info_key_types983 = _t1611
    _t1612 = parse_betree_info_value_types(parser)
    betree_info_value_types984 = _t1612
    _t1613 = parse_config_dict(parser)
    config_dict985 = _t1613
    consume_literal!(parser, ")")
    _t1614 = construct_betree_info(parser, betree_info_key_types983, betree_info_value_types984, config_dict985)
    result987 = _t1614
    record_span!(parser, span_start986, "BeTreeInfo")
    return result987
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs988 = Proto.var"#Type"[]
    cond989 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond989
        _t1615 = parse_type(parser)
        item990 = _t1615
        push!(xs988, item990)
        cond989 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types991 = xs988
    consume_literal!(parser, ")")
    return types991
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs992 = Proto.var"#Type"[]
    cond993 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond993
        _t1616 = parse_type(parser)
        item994 = _t1616
        push!(xs992, item994)
        cond993 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types995 = xs992
    consume_literal!(parser, ")")
    return types995
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1000 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1617 = parse_csvlocator(parser)
    csvlocator996 = _t1617
    _t1618 = parse_csv_config(parser)
    csv_config997 = _t1618
    _t1619 = parse_csv_columns(parser)
    csv_columns998 = _t1619
    _t1620 = parse_csv_asof(parser)
    csv_asof999 = _t1620
    consume_literal!(parser, ")")
    _t1621 = Proto.CSVData(locator=csvlocator996, config=csv_config997, columns=csv_columns998, asof=csv_asof999)
    result1001 = _t1621
    record_span!(parser, span_start1000, "CSVData")
    return result1001
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1004 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1623 = parse_csv_locator_paths(parser)
        _t1622 = _t1623
    else
        _t1622 = nothing
    end
    csv_locator_paths1002 = _t1622
    if match_lookahead_literal(parser, "(", 0)
        _t1625 = parse_csv_locator_inline_data(parser)
        _t1624 = _t1625
    else
        _t1624 = nothing
    end
    csv_locator_inline_data1003 = _t1624
    consume_literal!(parser, ")")
    _t1626 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1002) ? csv_locator_paths1002 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1003) ? csv_locator_inline_data1003 : "")))
    result1005 = _t1626
    record_span!(parser, span_start1004, "CSVLocator")
    return result1005
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1006 = String[]
    cond1007 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1007
        item1008 = consume_terminal!(parser, "STRING")
        push!(xs1006, item1008)
        cond1007 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1009 = xs1006
    consume_literal!(parser, ")")
    return strings1009
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1010 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1010
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1012 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1627 = parse_config_dict(parser)
    config_dict1011 = _t1627
    consume_literal!(parser, ")")
    _t1628 = construct_csv_config(parser, config_dict1011)
    result1013 = _t1628
    record_span!(parser, span_start1012, "CSVConfig")
    return result1013
end

function parse_csv_columns(parser::ParserState)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1014 = Proto.CSVColumn[]
    cond1015 = match_lookahead_literal(parser, "(", 0)
    while cond1015
        _t1629 = parse_csv_column(parser)
        item1016 = _t1629
        push!(xs1014, item1016)
        cond1015 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns1017 = xs1014
    consume_literal!(parser, ")")
    return csv_columns1017
end

function parse_csv_column(parser::ParserState)::Proto.CSVColumn
    span_start1024 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1018 = consume_terminal!(parser, "STRING")
    _t1630 = parse_relation_id(parser)
    relation_id1019 = _t1630
    consume_literal!(parser, "[")
    xs1020 = Proto.var"#Type"[]
    cond1021 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1021
        _t1631 = parse_type(parser)
        item1022 = _t1631
        push!(xs1020, item1022)
        cond1021 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1023 = xs1020
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1632 = Proto.CSVColumn(column_name=string1018, target_id=relation_id1019, types=types1023)
    result1025 = _t1632
    record_span!(parser, span_start1024, "CSVColumn")
    return result1025
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1026 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1026
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1028 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1633 = parse_fragment_id(parser)
    fragment_id1027 = _t1633
    consume_literal!(parser, ")")
    _t1634 = Proto.Undefine(fragment_id=fragment_id1027)
    result1029 = _t1634
    record_span!(parser, span_start1028, "Undefine")
    return result1029
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1034 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1030 = Proto.RelationId[]
    cond1031 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1031
        _t1635 = parse_relation_id(parser)
        item1032 = _t1635
        push!(xs1030, item1032)
        cond1031 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1033 = xs1030
    consume_literal!(parser, ")")
    _t1636 = Proto.Context(relations=relation_ids1033)
    result1035 = _t1636
    record_span!(parser, span_start1034, "Context")
    return result1035
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1038 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t1637 = parse_rel_edb_path(parser)
    rel_edb_path1036 = _t1637
    _t1638 = parse_relation_id(parser)
    relation_id1037 = _t1638
    consume_literal!(parser, ")")
    _t1639 = Proto.Snapshot(destination_path=rel_edb_path1036, source_relation=relation_id1037)
    result1039 = _t1639
    record_span!(parser, span_start1038, "Snapshot")
    return result1039
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1040 = Proto.Read[]
    cond1041 = match_lookahead_literal(parser, "(", 0)
    while cond1041
        _t1640 = parse_read(parser)
        item1042 = _t1640
        push!(xs1040, item1042)
        cond1041 = match_lookahead_literal(parser, "(", 0)
    end
    reads1043 = xs1040
    consume_literal!(parser, ")")
    return reads1043
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1050 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1642 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1643 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1644 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1645 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1646 = 3
                        else
                            _t1646 = -1
                        end
                        _t1645 = _t1646
                    end
                    _t1644 = _t1645
                end
                _t1643 = _t1644
            end
            _t1642 = _t1643
        end
        _t1641 = _t1642
    else
        _t1641 = -1
    end
    prediction1044 = _t1641
    if prediction1044 == 4
        _t1648 = parse_export(parser)
        export1049 = _t1648
        _t1649 = Proto.Read(read_type=OneOf(:var"#export", export1049))
        _t1647 = _t1649
    else
        if prediction1044 == 3
            _t1651 = parse_abort(parser)
            abort1048 = _t1651
            _t1652 = Proto.Read(read_type=OneOf(:abort, abort1048))
            _t1650 = _t1652
        else
            if prediction1044 == 2
                _t1654 = parse_what_if(parser)
                what_if1047 = _t1654
                _t1655 = Proto.Read(read_type=OneOf(:what_if, what_if1047))
                _t1653 = _t1655
            else
                if prediction1044 == 1
                    _t1657 = parse_output(parser)
                    output1046 = _t1657
                    _t1658 = Proto.Read(read_type=OneOf(:output, output1046))
                    _t1656 = _t1658
                else
                    if prediction1044 == 0
                        _t1660 = parse_demand(parser)
                        demand1045 = _t1660
                        _t1661 = Proto.Read(read_type=OneOf(:demand, demand1045))
                        _t1659 = _t1661
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1656 = _t1659
                end
                _t1653 = _t1656
            end
            _t1650 = _t1653
        end
        _t1647 = _t1650
    end
    result1051 = _t1647
    record_span!(parser, span_start1050, "Read")
    return result1051
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1053 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1662 = parse_relation_id(parser)
    relation_id1052 = _t1662
    consume_literal!(parser, ")")
    _t1663 = Proto.Demand(relation_id=relation_id1052)
    result1054 = _t1663
    record_span!(parser, span_start1053, "Demand")
    return result1054
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1057 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1664 = parse_name(parser)
    name1055 = _t1664
    _t1665 = parse_relation_id(parser)
    relation_id1056 = _t1665
    consume_literal!(parser, ")")
    _t1666 = Proto.Output(name=name1055, relation_id=relation_id1056)
    result1058 = _t1666
    record_span!(parser, span_start1057, "Output")
    return result1058
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1061 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1667 = parse_name(parser)
    name1059 = _t1667
    _t1668 = parse_epoch(parser)
    epoch1060 = _t1668
    consume_literal!(parser, ")")
    _t1669 = Proto.WhatIf(branch=name1059, epoch=epoch1060)
    result1062 = _t1669
    record_span!(parser, span_start1061, "WhatIf")
    return result1062
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1065 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1671 = parse_name(parser)
        _t1670 = _t1671
    else
        _t1670 = nothing
    end
    name1063 = _t1670
    _t1672 = parse_relation_id(parser)
    relation_id1064 = _t1672
    consume_literal!(parser, ")")
    _t1673 = Proto.Abort(name=(!isnothing(name1063) ? name1063 : "abort"), relation_id=relation_id1064)
    result1066 = _t1673
    record_span!(parser, span_start1065, "Abort")
    return result1066
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1068 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1674 = parse_export_csv_config(parser)
    export_csv_config1067 = _t1674
    consume_literal!(parser, ")")
    _t1675 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1067))
    result1069 = _t1675
    record_span!(parser, span_start1068, "Export")
    return result1069
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1073 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1676 = parse_export_csv_path(parser)
    export_csv_path1070 = _t1676
    _t1677 = parse_export_csv_columns(parser)
    export_csv_columns1071 = _t1677
    _t1678 = parse_config_dict(parser)
    config_dict1072 = _t1678
    consume_literal!(parser, ")")
    _t1679 = export_csv_config(parser, export_csv_path1070, export_csv_columns1071, config_dict1072)
    result1074 = _t1679
    record_span!(parser, span_start1073, "ExportCSVConfig")
    return result1074
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1075 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1075
end

function parse_export_csv_columns(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1076 = Proto.ExportCSVColumn[]
    cond1077 = match_lookahead_literal(parser, "(", 0)
    while cond1077
        _t1680 = parse_export_csv_column(parser)
        item1078 = _t1680
        push!(xs1076, item1078)
        cond1077 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1079 = xs1076
    consume_literal!(parser, ")")
    return export_csv_columns1079
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1082 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1080 = consume_terminal!(parser, "STRING")
    _t1681 = parse_relation_id(parser)
    relation_id1081 = _t1681
    consume_literal!(parser, ")")
    _t1682 = Proto.ExportCSVColumn(column_name=string1080, column_data=relation_id1081)
    result1083 = _t1682
    record_span!(parser, span_start1082, "ExportCSVColumn")
    return result1083
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
