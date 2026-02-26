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
    _path::Vector{Int}
    _line_starts::Vector{Int}

    function ParserState(tokens::Vector{Token}, input_str::String)
        return new(tokens, 1, Dict(), nothing, Dict(), Dict(), Int[], _compute_line_starts(input_str))
    end
end


function _make_location(parser::ParserState, offset::Int)::Location
    line_idx = searchsortedlast(parser._line_starts, offset)
    col = offset - parser._line_starts[line_idx]
    return Location(line_idx, col + 1, offset)
end

function push_path!(parser::ParserState, n::Int)
    push!(parser._path, n)
    return nothing
end

function pop_path!(parser::ParserState)
    pop!(parser._path)
    return nothing
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
    parser.provenance[Tuple(parser._path)] = s
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
        _t1911 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1912 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1913 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1914 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1915 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1916 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1917 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1918 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1919 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1920 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1920
    _t1921 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1921
    _t1922 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1922
    _t1923 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1923
    _t1924 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1924
    _t1925 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1925
    _t1926 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1926
    _t1927 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1927
    _t1928 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1928
    _t1929 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1929
    _t1930 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1930
    _t1931 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1931
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1932 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1932
    _t1933 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1933
    _t1934 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1934
    _t1935 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1935
    _t1936 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1936
    _t1937 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1937
    _t1938 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1938
    _t1939 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1939
    _t1940 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1940
    _t1941 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1941
    _t1942 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1942
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1943 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1943
    _t1944 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1944
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
    _t1945 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1945
    _t1946 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1946
    _t1947 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1947
end

function export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1948 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1948
    _t1949 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1949
    _t1950 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1950
    _t1951 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1951
    _t1952 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1952
    _t1953 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1953
    _t1954 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1954
    _t1955 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1955
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start602 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    push_path!(parser, 2)
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1313 = parse_configure(parser)
        _t1312 = _t1313
    else
        _t1312 = nothing
    end
    configure592 = _t1312
    pop_path!(parser)
    push_path!(parser, 3)
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1315 = parse_sync(parser)
        _t1314 = _t1315
    else
        _t1314 = nothing
    end
    sync593 = _t1314
    pop_path!(parser)
    push_path!(parser, 1)
    xs598 = Proto.Epoch[]
    cond599 = match_lookahead_literal(parser, "(", 0)
    idx600 = 0
    while cond599
        push_path!(parser, idx600)
        _t1316 = parse_epoch(parser)
        item601 = _t1316
        pop_path!(parser)
        push!(xs598, item601)
        idx600 = (idx600 + 1)
        cond599 = match_lookahead_literal(parser, "(", 0)
    end
    epochs597 = xs598
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1317 = default_configure(parser)
    _t1318 = Proto.Transaction(epochs=epochs597, configure=(!isnothing(configure592) ? configure592 : _t1317), sync=sync593)
    result603 = _t1318
    record_span!(parser, span_start602)
    return result603
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start605 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1319 = parse_config_dict(parser)
    config_dict604 = _t1319
    consume_literal!(parser, ")")
    _t1320 = construct_configure(parser, config_dict604)
    result606 = _t1320
    record_span!(parser, span_start605)
    return result606
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    span_start615 = span_start(parser)
    consume_literal!(parser, "{")
    xs611 = Tuple{String, Proto.Value}[]
    cond612 = match_lookahead_literal(parser, ":", 0)
    idx613 = 0
    while cond612
        push_path!(parser, idx613)
        _t1321 = parse_config_key_value(parser)
        item614 = _t1321
        pop_path!(parser)
        push!(xs611, item614)
        idx613 = (idx613 + 1)
        cond612 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values610 = xs611
    consume_literal!(parser, "}")
    result616 = config_key_values610
    record_span!(parser, span_start615)
    return result616
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    span_start619 = span_start(parser)
    consume_literal!(parser, ":")
    symbol617 = consume_terminal!(parser, "SYMBOL")
    _t1322 = parse_value(parser)
    value618 = _t1322
    result620 = (symbol617, value618,)
    record_span!(parser, span_start619)
    return result620
end

function parse_value(parser::ParserState)::Proto.Value
    span_start631 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1323 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1324 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1325 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1327 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1328 = 0
                        else
                            _t1328 = -1
                        end
                        _t1327 = _t1328
                    end
                    _t1326 = _t1327
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1329 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1330 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t1331 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t1332 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t1333 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t1334 = 7
                                        else
                                            _t1334 = -1
                                        end
                                        _t1333 = _t1334
                                    end
                                    _t1332 = _t1333
                                end
                                _t1331 = _t1332
                            end
                            _t1330 = _t1331
                        end
                        _t1329 = _t1330
                    end
                    _t1326 = _t1329
                end
                _t1325 = _t1326
            end
            _t1324 = _t1325
        end
        _t1323 = _t1324
    end
    prediction621 = _t1323
    if prediction621 == 9
        push_path!(parser, 10)
        _t1336 = parse_boolean_value(parser)
        boolean_value630 = _t1336
        pop_path!(parser)
        _t1337 = Proto.Value(value=OneOf(:boolean_value, boolean_value630))
        _t1335 = _t1337
    else
        if prediction621 == 8
            consume_literal!(parser, "missing")
            _t1339 = Proto.MissingValue()
            _t1340 = Proto.Value(value=OneOf(:missing_value, _t1339))
            _t1338 = _t1340
        else
            if prediction621 == 7
                decimal629 = consume_terminal!(parser, "DECIMAL")
                _t1342 = Proto.Value(value=OneOf(:decimal_value, decimal629))
                _t1341 = _t1342
            else
                if prediction621 == 6
                    int128628 = consume_terminal!(parser, "INT128")
                    _t1344 = Proto.Value(value=OneOf(:int128_value, int128628))
                    _t1343 = _t1344
                else
                    if prediction621 == 5
                        uint128627 = consume_terminal!(parser, "UINT128")
                        _t1346 = Proto.Value(value=OneOf(:uint128_value, uint128627))
                        _t1345 = _t1346
                    else
                        if prediction621 == 4
                            float626 = consume_terminal!(parser, "FLOAT")
                            _t1348 = Proto.Value(value=OneOf(:float_value, float626))
                            _t1347 = _t1348
                        else
                            if prediction621 == 3
                                int625 = consume_terminal!(parser, "INT")
                                _t1350 = Proto.Value(value=OneOf(:int_value, int625))
                                _t1349 = _t1350
                            else
                                if prediction621 == 2
                                    string624 = consume_terminal!(parser, "STRING")
                                    _t1352 = Proto.Value(value=OneOf(:string_value, string624))
                                    _t1351 = _t1352
                                else
                                    if prediction621 == 1
                                        push_path!(parser, 8)
                                        _t1354 = parse_datetime(parser)
                                        datetime623 = _t1354
                                        pop_path!(parser)
                                        _t1355 = Proto.Value(value=OneOf(:datetime_value, datetime623))
                                        _t1353 = _t1355
                                    else
                                        if prediction621 == 0
                                            push_path!(parser, 7)
                                            _t1357 = parse_date(parser)
                                            date622 = _t1357
                                            pop_path!(parser)
                                            _t1358 = Proto.Value(value=OneOf(:date_value, date622))
                                            _t1356 = _t1358
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1353 = _t1356
                                    end
                                    _t1351 = _t1353
                                end
                                _t1349 = _t1351
                            end
                            _t1347 = _t1349
                        end
                        _t1345 = _t1347
                    end
                    _t1343 = _t1345
                end
                _t1341 = _t1343
            end
            _t1338 = _t1341
        end
        _t1335 = _t1338
    end
    result632 = _t1335
    record_span!(parser, span_start631)
    return result632
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start636 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    push_path!(parser, 1)
    int633 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_3634 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 3)
    int_4635 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1359 = Proto.DateValue(year=Int32(int633), month=Int32(int_3634), day=Int32(int_4635))
    result637 = _t1359
    record_span!(parser, span_start636)
    return result637
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start645 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    push_path!(parser, 1)
    int638 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_3639 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 3)
    int_4640 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 4)
    int_5641 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 5)
    int_6642 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 6)
    int_7643 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 7)
    if match_lookahead_terminal(parser, "INT", 0)
        _t1360 = consume_terminal!(parser, "INT")
    else
        _t1360 = nothing
    end
    int_8644 = _t1360
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1361 = Proto.DateTimeValue(year=Int32(int638), month=Int32(int_3639), day=Int32(int_4640), hour=Int32(int_5641), minute=Int32(int_6642), second=Int32(int_7643), microsecond=Int32((!isnothing(int_8644) ? int_8644 : 0)))
    result646 = _t1361
    record_span!(parser, span_start645)
    return result646
end

function parse_boolean_value(parser::ParserState)::Bool
    span_start648 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1362 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1363 = 1
        else
            _t1363 = -1
        end
        _t1362 = _t1363
    end
    prediction647 = _t1362
    if prediction647 == 1
        consume_literal!(parser, "false")
        _t1364 = false
    else
        if prediction647 == 0
            consume_literal!(parser, "true")
            _t1365 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1364 = _t1365
    end
    result649 = _t1364
    record_span!(parser, span_start648)
    return result649
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start658 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    push_path!(parser, 1)
    xs654 = Proto.FragmentId[]
    cond655 = match_lookahead_literal(parser, ":", 0)
    idx656 = 0
    while cond655
        push_path!(parser, idx656)
        _t1366 = parse_fragment_id(parser)
        item657 = _t1366
        pop_path!(parser)
        push!(xs654, item657)
        idx656 = (idx656 + 1)
        cond655 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids653 = xs654
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1367 = Proto.Sync(fragments=fragment_ids653)
    result659 = _t1367
    record_span!(parser, span_start658)
    return result659
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start661 = span_start(parser)
    consume_literal!(parser, ":")
    symbol660 = consume_terminal!(parser, "SYMBOL")
    result662 = Proto.FragmentId(Vector{UInt8}(symbol660))
    record_span!(parser, span_start661)
    return result662
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start665 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    push_path!(parser, 1)
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1369 = parse_epoch_writes(parser)
        _t1368 = _t1369
    else
        _t1368 = nothing
    end
    epoch_writes663 = _t1368
    pop_path!(parser)
    push_path!(parser, 2)
    if match_lookahead_literal(parser, "(", 0)
        _t1371 = parse_epoch_reads(parser)
        _t1370 = _t1371
    else
        _t1370 = nothing
    end
    epoch_reads664 = _t1370
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1372 = Proto.Epoch(writes=(!isnothing(epoch_writes663) ? epoch_writes663 : Proto.Write[]), reads=(!isnothing(epoch_reads664) ? epoch_reads664 : Proto.Read[]))
    result666 = _t1372
    record_span!(parser, span_start665)
    return result666
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    span_start675 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs671 = Proto.Write[]
    cond672 = match_lookahead_literal(parser, "(", 0)
    idx673 = 0
    while cond672
        push_path!(parser, idx673)
        _t1373 = parse_write(parser)
        item674 = _t1373
        pop_path!(parser)
        push!(xs671, item674)
        idx673 = (idx673 + 1)
        cond672 = match_lookahead_literal(parser, "(", 0)
    end
    writes670 = xs671
    consume_literal!(parser, ")")
    result676 = writes670
    record_span!(parser, span_start675)
    return result676
end

function parse_write(parser::ParserState)::Proto.Write
    span_start682 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1375 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1376 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1377 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1378 = 2
                    else
                        _t1378 = -1
                    end
                    _t1377 = _t1378
                end
                _t1376 = _t1377
            end
            _t1375 = _t1376
        end
        _t1374 = _t1375
    else
        _t1374 = -1
    end
    prediction677 = _t1374
    if prediction677 == 3
        push_path!(parser, 5)
        _t1380 = parse_snapshot(parser)
        snapshot681 = _t1380
        pop_path!(parser)
        _t1381 = Proto.Write(write_type=OneOf(:snapshot, snapshot681))
        _t1379 = _t1381
    else
        if prediction677 == 2
            push_path!(parser, 3)
            _t1383 = parse_context(parser)
            context680 = _t1383
            pop_path!(parser)
            _t1384 = Proto.Write(write_type=OneOf(:context, context680))
            _t1382 = _t1384
        else
            if prediction677 == 1
                push_path!(parser, 2)
                _t1386 = parse_undefine(parser)
                undefine679 = _t1386
                pop_path!(parser)
                _t1387 = Proto.Write(write_type=OneOf(:undefine, undefine679))
                _t1385 = _t1387
            else
                if prediction677 == 0
                    push_path!(parser, 1)
                    _t1389 = parse_define(parser)
                    define678 = _t1389
                    pop_path!(parser)
                    _t1390 = Proto.Write(write_type=OneOf(:define, define678))
                    _t1388 = _t1390
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1385 = _t1388
            end
            _t1382 = _t1385
        end
        _t1379 = _t1382
    end
    result683 = _t1379
    record_span!(parser, span_start682)
    return result683
end

function parse_define(parser::ParserState)::Proto.Define
    span_start685 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    push_path!(parser, 1)
    _t1391 = parse_fragment(parser)
    fragment684 = _t1391
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1392 = Proto.Define(fragment=fragment684)
    result686 = _t1392
    record_span!(parser, span_start685)
    return result686
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start696 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1393 = parse_new_fragment_id(parser)
    new_fragment_id687 = _t1393
    push_path!(parser, 2)
    xs692 = Proto.Declaration[]
    cond693 = match_lookahead_literal(parser, "(", 0)
    idx694 = 0
    while cond693
        push_path!(parser, idx694)
        _t1394 = parse_declaration(parser)
        item695 = _t1394
        pop_path!(parser)
        push!(xs692, item695)
        idx694 = (idx694 + 1)
        cond693 = match_lookahead_literal(parser, "(", 0)
    end
    declarations691 = xs692
    pop_path!(parser)
    consume_literal!(parser, ")")
    result697 = construct_fragment(parser, new_fragment_id687, declarations691)
    record_span!(parser, span_start696)
    return result697
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start699 = span_start(parser)
    _t1395 = parse_fragment_id(parser)
    fragment_id698 = _t1395
    start_fragment!(parser, fragment_id698)
    result700 = fragment_id698
    record_span!(parser, span_start699)
    return result700
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start706 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1397 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1398 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1399 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1400 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1401 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1402 = 1
                            else
                                _t1402 = -1
                            end
                            _t1401 = _t1402
                        end
                        _t1400 = _t1401
                    end
                    _t1399 = _t1400
                end
                _t1398 = _t1399
            end
            _t1397 = _t1398
        end
        _t1396 = _t1397
    else
        _t1396 = -1
    end
    prediction701 = _t1396
    if prediction701 == 3
        push_path!(parser, 4)
        _t1404 = parse_data(parser)
        data705 = _t1404
        pop_path!(parser)
        _t1405 = Proto.Declaration(declaration_type=OneOf(:data, data705))
        _t1403 = _t1405
    else
        if prediction701 == 2
            push_path!(parser, 3)
            _t1407 = parse_constraint(parser)
            constraint704 = _t1407
            pop_path!(parser)
            _t1408 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint704))
            _t1406 = _t1408
        else
            if prediction701 == 1
                push_path!(parser, 2)
                _t1410 = parse_algorithm(parser)
                algorithm703 = _t1410
                pop_path!(parser)
                _t1411 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm703))
                _t1409 = _t1411
            else
                if prediction701 == 0
                    push_path!(parser, 1)
                    _t1413 = parse_def(parser)
                    def702 = _t1413
                    pop_path!(parser)
                    _t1414 = Proto.Declaration(declaration_type=OneOf(:def, def702))
                    _t1412 = _t1414
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1409 = _t1412
            end
            _t1406 = _t1409
        end
        _t1403 = _t1406
    end
    result707 = _t1403
    record_span!(parser, span_start706)
    return result707
end

function parse_def(parser::ParserState)::Proto.Def
    span_start711 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    push_path!(parser, 1)
    _t1415 = parse_relation_id(parser)
    relation_id708 = _t1415
    pop_path!(parser)
    push_path!(parser, 2)
    _t1416 = parse_abstraction(parser)
    abstraction709 = _t1416
    pop_path!(parser)
    push_path!(parser, 3)
    if match_lookahead_literal(parser, "(", 0)
        _t1418 = parse_attrs(parser)
        _t1417 = _t1418
    else
        _t1417 = nothing
    end
    attrs710 = _t1417
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1419 = Proto.Def(name=relation_id708, body=abstraction709, attrs=(!isnothing(attrs710) ? attrs710 : Proto.Attribute[]))
    result712 = _t1419
    record_span!(parser, span_start711)
    return result712
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start716 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1420 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1421 = 1
        else
            _t1421 = -1
        end
        _t1420 = _t1421
    end
    prediction713 = _t1420
    if prediction713 == 1
        uint128715 = consume_terminal!(parser, "UINT128")
        _t1422 = Proto.RelationId(uint128715.low, uint128715.high)
    else
        if prediction713 == 0
            consume_literal!(parser, ":")
            symbol714 = consume_terminal!(parser, "SYMBOL")
            _t1423 = relation_id_from_string(parser, symbol714)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1422 = _t1423
    end
    result717 = _t1422
    record_span!(parser, span_start716)
    return result717
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start720 = span_start(parser)
    consume_literal!(parser, "(")
    _t1424 = parse_bindings(parser)
    bindings718 = _t1424
    push_path!(parser, 2)
    _t1425 = parse_formula(parser)
    formula719 = _t1425
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1426 = Proto.Abstraction(vars=vcat(bindings718[1], !isnothing(bindings718[2]) ? bindings718[2] : []), value=formula719)
    result721 = _t1426
    record_span!(parser, span_start720)
    return result721
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    span_start731 = span_start(parser)
    consume_literal!(parser, "[")
    xs726 = Proto.Binding[]
    cond727 = match_lookahead_terminal(parser, "SYMBOL", 0)
    idx728 = 0
    while cond727
        push_path!(parser, idx728)
        _t1427 = parse_binding(parser)
        item729 = _t1427
        pop_path!(parser)
        push!(xs726, item729)
        idx728 = (idx728 + 1)
        cond727 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings725 = xs726
    if match_lookahead_literal(parser, "|", 0)
        _t1429 = parse_value_bindings(parser)
        _t1428 = _t1429
    else
        _t1428 = nothing
    end
    value_bindings730 = _t1428
    consume_literal!(parser, "]")
    result732 = (bindings725, (!isnothing(value_bindings730) ? value_bindings730 : Proto.Binding[]),)
    record_span!(parser, span_start731)
    return result732
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start735 = span_start(parser)
    symbol733 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    push_path!(parser, 2)
    _t1430 = parse_type(parser)
    type734 = _t1430
    pop_path!(parser)
    _t1431 = Proto.Var(name=symbol733)
    _t1432 = Proto.Binding(var=_t1431, var"#type"=type734)
    result736 = _t1432
    record_span!(parser, span_start735)
    return result736
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start749 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1433 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t1434 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t1435 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t1436 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t1437 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t1438 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t1439 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t1440 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t1441 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t1442 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t1443 = 9
                                            else
                                                _t1443 = -1
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
        _t1433 = _t1434
    end
    prediction737 = _t1433
    if prediction737 == 10
        push_path!(parser, 11)
        _t1445 = parse_boolean_type(parser)
        boolean_type748 = _t1445
        pop_path!(parser)
        _t1446 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type748))
        _t1444 = _t1446
    else
        if prediction737 == 9
            push_path!(parser, 10)
            _t1448 = parse_decimal_type(parser)
            decimal_type747 = _t1448
            pop_path!(parser)
            _t1449 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type747))
            _t1447 = _t1449
        else
            if prediction737 == 8
                push_path!(parser, 9)
                _t1451 = parse_missing_type(parser)
                missing_type746 = _t1451
                pop_path!(parser)
                _t1452 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type746))
                _t1450 = _t1452
            else
                if prediction737 == 7
                    push_path!(parser, 8)
                    _t1454 = parse_datetime_type(parser)
                    datetime_type745 = _t1454
                    pop_path!(parser)
                    _t1455 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type745))
                    _t1453 = _t1455
                else
                    if prediction737 == 6
                        push_path!(parser, 7)
                        _t1457 = parse_date_type(parser)
                        date_type744 = _t1457
                        pop_path!(parser)
                        _t1458 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type744))
                        _t1456 = _t1458
                    else
                        if prediction737 == 5
                            push_path!(parser, 6)
                            _t1460 = parse_int128_type(parser)
                            int128_type743 = _t1460
                            pop_path!(parser)
                            _t1461 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type743))
                            _t1459 = _t1461
                        else
                            if prediction737 == 4
                                push_path!(parser, 5)
                                _t1463 = parse_uint128_type(parser)
                                uint128_type742 = _t1463
                                pop_path!(parser)
                                _t1464 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type742))
                                _t1462 = _t1464
                            else
                                if prediction737 == 3
                                    push_path!(parser, 4)
                                    _t1466 = parse_float_type(parser)
                                    float_type741 = _t1466
                                    pop_path!(parser)
                                    _t1467 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type741))
                                    _t1465 = _t1467
                                else
                                    if prediction737 == 2
                                        push_path!(parser, 3)
                                        _t1469 = parse_int_type(parser)
                                        int_type740 = _t1469
                                        pop_path!(parser)
                                        _t1470 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type740))
                                        _t1468 = _t1470
                                    else
                                        if prediction737 == 1
                                            push_path!(parser, 2)
                                            _t1472 = parse_string_type(parser)
                                            string_type739 = _t1472
                                            pop_path!(parser)
                                            _t1473 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type739))
                                            _t1471 = _t1473
                                        else
                                            if prediction737 == 0
                                                push_path!(parser, 1)
                                                _t1475 = parse_unspecified_type(parser)
                                                unspecified_type738 = _t1475
                                                pop_path!(parser)
                                                _t1476 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type738))
                                                _t1474 = _t1476
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t1471 = _t1474
                                        end
                                        _t1468 = _t1471
                                    end
                                    _t1465 = _t1468
                                end
                                _t1462 = _t1465
                            end
                            _t1459 = _t1462
                        end
                        _t1456 = _t1459
                    end
                    _t1453 = _t1456
                end
                _t1450 = _t1453
            end
            _t1447 = _t1450
        end
        _t1444 = _t1447
    end
    result750 = _t1444
    record_span!(parser, span_start749)
    return result750
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start751 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1477 = Proto.UnspecifiedType()
    result752 = _t1477
    record_span!(parser, span_start751)
    return result752
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start753 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1478 = Proto.StringType()
    result754 = _t1478
    record_span!(parser, span_start753)
    return result754
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start755 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1479 = Proto.IntType()
    result756 = _t1479
    record_span!(parser, span_start755)
    return result756
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start757 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1480 = Proto.FloatType()
    result758 = _t1480
    record_span!(parser, span_start757)
    return result758
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start759 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1481 = Proto.UInt128Type()
    result760 = _t1481
    record_span!(parser, span_start759)
    return result760
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start761 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1482 = Proto.Int128Type()
    result762 = _t1482
    record_span!(parser, span_start761)
    return result762
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start763 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1483 = Proto.DateType()
    result764 = _t1483
    record_span!(parser, span_start763)
    return result764
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start765 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1484 = Proto.DateTimeType()
    result766 = _t1484
    record_span!(parser, span_start765)
    return result766
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start767 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1485 = Proto.MissingType()
    result768 = _t1485
    record_span!(parser, span_start767)
    return result768
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start771 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    push_path!(parser, 1)
    int769 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_3770 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1486 = Proto.DecimalType(precision=Int32(int769), scale=Int32(int_3770))
    result772 = _t1486
    record_span!(parser, span_start771)
    return result772
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start773 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1487 = Proto.BooleanType()
    result774 = _t1487
    record_span!(parser, span_start773)
    return result774
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    span_start783 = span_start(parser)
    consume_literal!(parser, "|")
    xs779 = Proto.Binding[]
    cond780 = match_lookahead_terminal(parser, "SYMBOL", 0)
    idx781 = 0
    while cond780
        push_path!(parser, idx781)
        _t1488 = parse_binding(parser)
        item782 = _t1488
        pop_path!(parser)
        push!(xs779, item782)
        idx781 = (idx781 + 1)
        cond780 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings778 = xs779
    result784 = bindings778
    record_span!(parser, span_start783)
    return result784
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start799 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1490 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1491 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1492 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1493 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1494 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1495 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1496 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1497 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1498 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1499 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1500 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1501 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1502 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1503 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1504 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1505 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1506 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1507 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1508 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1509 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1510 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1511 = 10
                                                                                            else
                                                                                                _t1511 = -1
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
                                                                _t1503 = _t1504
                                                            end
                                                            _t1502 = _t1503
                                                        end
                                                        _t1501 = _t1502
                                                    end
                                                    _t1500 = _t1501
                                                end
                                                _t1499 = _t1500
                                            end
                                            _t1498 = _t1499
                                        end
                                        _t1497 = _t1498
                                    end
                                    _t1496 = _t1497
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
        end
        _t1489 = _t1490
    else
        _t1489 = -1
    end
    prediction785 = _t1489
    if prediction785 == 12
        push_path!(parser, 11)
        _t1513 = parse_cast(parser)
        cast798 = _t1513
        pop_path!(parser)
        _t1514 = Proto.Formula(formula_type=OneOf(:cast, cast798))
        _t1512 = _t1514
    else
        if prediction785 == 11
            push_path!(parser, 10)
            _t1516 = parse_rel_atom(parser)
            rel_atom797 = _t1516
            pop_path!(parser)
            _t1517 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom797))
            _t1515 = _t1517
        else
            if prediction785 == 10
                push_path!(parser, 9)
                _t1519 = parse_primitive(parser)
                primitive796 = _t1519
                pop_path!(parser)
                _t1520 = Proto.Formula(formula_type=OneOf(:primitive, primitive796))
                _t1518 = _t1520
            else
                if prediction785 == 9
                    push_path!(parser, 8)
                    _t1522 = parse_pragma(parser)
                    pragma795 = _t1522
                    pop_path!(parser)
                    _t1523 = Proto.Formula(formula_type=OneOf(:pragma, pragma795))
                    _t1521 = _t1523
                else
                    if prediction785 == 8
                        push_path!(parser, 7)
                        _t1525 = parse_atom(parser)
                        atom794 = _t1525
                        pop_path!(parser)
                        _t1526 = Proto.Formula(formula_type=OneOf(:atom, atom794))
                        _t1524 = _t1526
                    else
                        if prediction785 == 7
                            push_path!(parser, 6)
                            _t1528 = parse_ffi(parser)
                            ffi793 = _t1528
                            pop_path!(parser)
                            _t1529 = Proto.Formula(formula_type=OneOf(:ffi, ffi793))
                            _t1527 = _t1529
                        else
                            if prediction785 == 6
                                push_path!(parser, 5)
                                _t1531 = parse_not(parser)
                                not792 = _t1531
                                pop_path!(parser)
                                _t1532 = Proto.Formula(formula_type=OneOf(:not, not792))
                                _t1530 = _t1532
                            else
                                if prediction785 == 5
                                    push_path!(parser, 4)
                                    _t1534 = parse_disjunction(parser)
                                    disjunction791 = _t1534
                                    pop_path!(parser)
                                    _t1535 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction791))
                                    _t1533 = _t1535
                                else
                                    if prediction785 == 4
                                        push_path!(parser, 3)
                                        _t1537 = parse_conjunction(parser)
                                        conjunction790 = _t1537
                                        pop_path!(parser)
                                        _t1538 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction790))
                                        _t1536 = _t1538
                                    else
                                        if prediction785 == 3
                                            push_path!(parser, 2)
                                            _t1540 = parse_reduce(parser)
                                            reduce789 = _t1540
                                            pop_path!(parser)
                                            _t1541 = Proto.Formula(formula_type=OneOf(:reduce, reduce789))
                                            _t1539 = _t1541
                                        else
                                            if prediction785 == 2
                                                push_path!(parser, 1)
                                                _t1543 = parse_exists(parser)
                                                exists788 = _t1543
                                                pop_path!(parser)
                                                _t1544 = Proto.Formula(formula_type=OneOf(:exists, exists788))
                                                _t1542 = _t1544
                                            else
                                                if prediction785 == 1
                                                    push_path!(parser, 4)
                                                    _t1546 = parse_false(parser)
                                                    false787 = _t1546
                                                    pop_path!(parser)
                                                    _t1547 = Proto.Formula(formula_type=OneOf(:disjunction, false787))
                                                    _t1545 = _t1547
                                                else
                                                    if prediction785 == 0
                                                        push_path!(parser, 3)
                                                        _t1549 = parse_true(parser)
                                                        true786 = _t1549
                                                        pop_path!(parser)
                                                        _t1550 = Proto.Formula(formula_type=OneOf(:conjunction, true786))
                                                        _t1548 = _t1550
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1545 = _t1548
                                                end
                                                _t1542 = _t1545
                                            end
                                            _t1539 = _t1542
                                        end
                                        _t1536 = _t1539
                                    end
                                    _t1533 = _t1536
                                end
                                _t1530 = _t1533
                            end
                            _t1527 = _t1530
                        end
                        _t1524 = _t1527
                    end
                    _t1521 = _t1524
                end
                _t1518 = _t1521
            end
            _t1515 = _t1518
        end
        _t1512 = _t1515
    end
    result800 = _t1512
    record_span!(parser, span_start799)
    return result800
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start801 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1551 = Proto.Conjunction(args=Proto.Formula[])
    result802 = _t1551
    record_span!(parser, span_start801)
    return result802
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start803 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1552 = Proto.Disjunction(args=Proto.Formula[])
    result804 = _t1552
    record_span!(parser, span_start803)
    return result804
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start807 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1553 = parse_bindings(parser)
    bindings805 = _t1553
    _t1554 = parse_formula(parser)
    formula806 = _t1554
    consume_literal!(parser, ")")
    _t1555 = Proto.Abstraction(vars=vcat(bindings805[1], !isnothing(bindings805[2]) ? bindings805[2] : []), value=formula806)
    _t1556 = Proto.Exists(body=_t1555)
    result808 = _t1556
    record_span!(parser, span_start807)
    return result808
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start812 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    push_path!(parser, 1)
    _t1557 = parse_abstraction(parser)
    abstraction809 = _t1557
    pop_path!(parser)
    push_path!(parser, 2)
    _t1558 = parse_abstraction(parser)
    abstraction_3810 = _t1558
    pop_path!(parser)
    push_path!(parser, 3)
    _t1559 = parse_terms(parser)
    terms811 = _t1559
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1560 = Proto.Reduce(op=abstraction809, body=abstraction_3810, terms=terms811)
    result813 = _t1560
    record_span!(parser, span_start812)
    return result813
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    span_start822 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs818 = Proto.Term[]
    cond819 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx820 = 0
    while cond819
        push_path!(parser, idx820)
        _t1561 = parse_term(parser)
        item821 = _t1561
        pop_path!(parser)
        push!(xs818, item821)
        idx820 = (idx820 + 1)
        cond819 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms817 = xs818
    consume_literal!(parser, ")")
    result823 = terms817
    record_span!(parser, span_start822)
    return result823
end

function parse_term(parser::ParserState)::Proto.Term
    span_start827 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1562 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1563 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1564 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1565 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1566 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1567 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1568 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1569 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1570 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t1571 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t1572 = 1
                                            else
                                                _t1572 = -1
                                            end
                                            _t1571 = _t1572
                                        end
                                        _t1570 = _t1571
                                    end
                                    _t1569 = _t1570
                                end
                                _t1568 = _t1569
                            end
                            _t1567 = _t1568
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
    prediction824 = _t1562
    if prediction824 == 1
        push_path!(parser, 2)
        _t1574 = parse_constant(parser)
        constant826 = _t1574
        pop_path!(parser)
        _t1575 = Proto.Term(term_type=OneOf(:constant, constant826))
        _t1573 = _t1575
    else
        if prediction824 == 0
            push_path!(parser, 1)
            _t1577 = parse_var(parser)
            var825 = _t1577
            pop_path!(parser)
            _t1578 = Proto.Term(term_type=OneOf(:var, var825))
            _t1576 = _t1578
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1573 = _t1576
    end
    result828 = _t1573
    record_span!(parser, span_start827)
    return result828
end

function parse_var(parser::ParserState)::Proto.Var
    span_start830 = span_start(parser)
    symbol829 = consume_terminal!(parser, "SYMBOL")
    _t1579 = Proto.Var(name=symbol829)
    result831 = _t1579
    record_span!(parser, span_start830)
    return result831
end

function parse_constant(parser::ParserState)::Proto.Value
    span_start833 = span_start(parser)
    _t1580 = parse_value(parser)
    value832 = _t1580
    result834 = value832
    record_span!(parser, span_start833)
    return result834
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start843 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    push_path!(parser, 1)
    xs839 = Proto.Formula[]
    cond840 = match_lookahead_literal(parser, "(", 0)
    idx841 = 0
    while cond840
        push_path!(parser, idx841)
        _t1581 = parse_formula(parser)
        item842 = _t1581
        pop_path!(parser)
        push!(xs839, item842)
        idx841 = (idx841 + 1)
        cond840 = match_lookahead_literal(parser, "(", 0)
    end
    formulas838 = xs839
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1582 = Proto.Conjunction(args=formulas838)
    result844 = _t1582
    record_span!(parser, span_start843)
    return result844
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start853 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    push_path!(parser, 1)
    xs849 = Proto.Formula[]
    cond850 = match_lookahead_literal(parser, "(", 0)
    idx851 = 0
    while cond850
        push_path!(parser, idx851)
        _t1583 = parse_formula(parser)
        item852 = _t1583
        pop_path!(parser)
        push!(xs849, item852)
        idx851 = (idx851 + 1)
        cond850 = match_lookahead_literal(parser, "(", 0)
    end
    formulas848 = xs849
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1584 = Proto.Disjunction(args=formulas848)
    result854 = _t1584
    record_span!(parser, span_start853)
    return result854
end

function parse_not(parser::ParserState)::Proto.Not
    span_start856 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    push_path!(parser, 1)
    _t1585 = parse_formula(parser)
    formula855 = _t1585
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1586 = Proto.Not(arg=formula855)
    result857 = _t1586
    record_span!(parser, span_start856)
    return result857
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start861 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    push_path!(parser, 1)
    _t1587 = parse_name(parser)
    name858 = _t1587
    pop_path!(parser)
    push_path!(parser, 2)
    _t1588 = parse_ffi_args(parser)
    ffi_args859 = _t1588
    pop_path!(parser)
    push_path!(parser, 3)
    _t1589 = parse_terms(parser)
    terms860 = _t1589
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1590 = Proto.FFI(name=name858, args=ffi_args859, terms=terms860)
    result862 = _t1590
    record_span!(parser, span_start861)
    return result862
end

function parse_name(parser::ParserState)::String
    span_start864 = span_start(parser)
    consume_literal!(parser, ":")
    symbol863 = consume_terminal!(parser, "SYMBOL")
    result865 = symbol863
    record_span!(parser, span_start864)
    return result865
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    span_start874 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs870 = Proto.Abstraction[]
    cond871 = match_lookahead_literal(parser, "(", 0)
    idx872 = 0
    while cond871
        push_path!(parser, idx872)
        _t1591 = parse_abstraction(parser)
        item873 = _t1591
        pop_path!(parser)
        push!(xs870, item873)
        idx872 = (idx872 + 1)
        cond871 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions869 = xs870
    consume_literal!(parser, ")")
    result875 = abstractions869
    record_span!(parser, span_start874)
    return result875
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start885 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    push_path!(parser, 1)
    _t1592 = parse_relation_id(parser)
    relation_id876 = _t1592
    pop_path!(parser)
    push_path!(parser, 2)
    xs881 = Proto.Term[]
    cond882 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx883 = 0
    while cond882
        push_path!(parser, idx883)
        _t1593 = parse_term(parser)
        item884 = _t1593
        pop_path!(parser)
        push!(xs881, item884)
        idx883 = (idx883 + 1)
        cond882 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms880 = xs881
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1594 = Proto.Atom(name=relation_id876, terms=terms880)
    result886 = _t1594
    record_span!(parser, span_start885)
    return result886
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start896 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    push_path!(parser, 1)
    _t1595 = parse_name(parser)
    name887 = _t1595
    pop_path!(parser)
    push_path!(parser, 2)
    xs892 = Proto.Term[]
    cond893 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx894 = 0
    while cond893
        push_path!(parser, idx894)
        _t1596 = parse_term(parser)
        item895 = _t1596
        pop_path!(parser)
        push!(xs892, item895)
        idx894 = (idx894 + 1)
        cond893 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms891 = xs892
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1597 = Proto.Pragma(name=name887, terms=terms891)
    result897 = _t1597
    record_span!(parser, span_start896)
    return result897
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start917 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1599 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1600 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1601 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1602 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1603 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1604 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1605 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1606 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1607 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1608 = 7
                                            else
                                                _t1608 = -1
                                            end
                                            _t1607 = _t1608
                                        end
                                        _t1606 = _t1607
                                    end
                                    _t1605 = _t1606
                                end
                                _t1604 = _t1605
                            end
                            _t1603 = _t1604
                        end
                        _t1602 = _t1603
                    end
                    _t1601 = _t1602
                end
                _t1600 = _t1601
            end
            _t1599 = _t1600
        end
        _t1598 = _t1599
    else
        _t1598 = -1
    end
    prediction898 = _t1598
    if prediction898 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        push_path!(parser, 1)
        _t1610 = parse_name(parser)
        name908 = _t1610
        pop_path!(parser)
        push_path!(parser, 2)
        xs913 = Proto.RelTerm[]
        cond914 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        idx915 = 0
        while cond914
            push_path!(parser, idx915)
            _t1611 = parse_rel_term(parser)
            item916 = _t1611
            pop_path!(parser)
            push!(xs913, item916)
            idx915 = (idx915 + 1)
            cond914 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms912 = xs913
        pop_path!(parser)
        consume_literal!(parser, ")")
        _t1612 = Proto.Primitive(name=name908, terms=rel_terms912)
        _t1609 = _t1612
    else
        if prediction898 == 8
            _t1614 = parse_divide(parser)
            divide907 = _t1614
            _t1613 = divide907
        else
            if prediction898 == 7
                _t1616 = parse_multiply(parser)
                multiply906 = _t1616
                _t1615 = multiply906
            else
                if prediction898 == 6
                    _t1618 = parse_minus(parser)
                    minus905 = _t1618
                    _t1617 = minus905
                else
                    if prediction898 == 5
                        _t1620 = parse_add(parser)
                        add904 = _t1620
                        _t1619 = add904
                    else
                        if prediction898 == 4
                            _t1622 = parse_gt_eq(parser)
                            gt_eq903 = _t1622
                            _t1621 = gt_eq903
                        else
                            if prediction898 == 3
                                _t1624 = parse_gt(parser)
                                gt902 = _t1624
                                _t1623 = gt902
                            else
                                if prediction898 == 2
                                    _t1626 = parse_lt_eq(parser)
                                    lt_eq901 = _t1626
                                    _t1625 = lt_eq901
                                else
                                    if prediction898 == 1
                                        _t1628 = parse_lt(parser)
                                        lt900 = _t1628
                                        _t1627 = lt900
                                    else
                                        if prediction898 == 0
                                            _t1630 = parse_eq(parser)
                                            eq899 = _t1630
                                            _t1629 = eq899
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1627 = _t1629
                                    end
                                    _t1625 = _t1627
                                end
                                _t1623 = _t1625
                            end
                            _t1621 = _t1623
                        end
                        _t1619 = _t1621
                    end
                    _t1617 = _t1619
                end
                _t1615 = _t1617
            end
            _t1613 = _t1615
        end
        _t1609 = _t1613
    end
    result918 = _t1609
    record_span!(parser, span_start917)
    return result918
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start921 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1631 = parse_term(parser)
    term919 = _t1631
    _t1632 = parse_term(parser)
    term_3920 = _t1632
    consume_literal!(parser, ")")
    _t1633 = Proto.RelTerm(rel_term_type=OneOf(:term, term919))
    _t1634 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3920))
    _t1635 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1633, _t1634])
    result922 = _t1635
    record_span!(parser, span_start921)
    return result922
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start925 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1636 = parse_term(parser)
    term923 = _t1636
    _t1637 = parse_term(parser)
    term_3924 = _t1637
    consume_literal!(parser, ")")
    _t1638 = Proto.RelTerm(rel_term_type=OneOf(:term, term923))
    _t1639 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3924))
    _t1640 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1638, _t1639])
    result926 = _t1640
    record_span!(parser, span_start925)
    return result926
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start929 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1641 = parse_term(parser)
    term927 = _t1641
    _t1642 = parse_term(parser)
    term_3928 = _t1642
    consume_literal!(parser, ")")
    _t1643 = Proto.RelTerm(rel_term_type=OneOf(:term, term927))
    _t1644 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3928))
    _t1645 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1643, _t1644])
    result930 = _t1645
    record_span!(parser, span_start929)
    return result930
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start933 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1646 = parse_term(parser)
    term931 = _t1646
    _t1647 = parse_term(parser)
    term_3932 = _t1647
    consume_literal!(parser, ")")
    _t1648 = Proto.RelTerm(rel_term_type=OneOf(:term, term931))
    _t1649 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3932))
    _t1650 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1648, _t1649])
    result934 = _t1650
    record_span!(parser, span_start933)
    return result934
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start937 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1651 = parse_term(parser)
    term935 = _t1651
    _t1652 = parse_term(parser)
    term_3936 = _t1652
    consume_literal!(parser, ")")
    _t1653 = Proto.RelTerm(rel_term_type=OneOf(:term, term935))
    _t1654 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3936))
    _t1655 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1653, _t1654])
    result938 = _t1655
    record_span!(parser, span_start937)
    return result938
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start942 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1656 = parse_term(parser)
    term939 = _t1656
    _t1657 = parse_term(parser)
    term_3940 = _t1657
    _t1658 = parse_term(parser)
    term_4941 = _t1658
    consume_literal!(parser, ")")
    _t1659 = Proto.RelTerm(rel_term_type=OneOf(:term, term939))
    _t1660 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3940))
    _t1661 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4941))
    _t1662 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1659, _t1660, _t1661])
    result943 = _t1662
    record_span!(parser, span_start942)
    return result943
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start947 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1663 = parse_term(parser)
    term944 = _t1663
    _t1664 = parse_term(parser)
    term_3945 = _t1664
    _t1665 = parse_term(parser)
    term_4946 = _t1665
    consume_literal!(parser, ")")
    _t1666 = Proto.RelTerm(rel_term_type=OneOf(:term, term944))
    _t1667 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3945))
    _t1668 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4946))
    _t1669 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1666, _t1667, _t1668])
    result948 = _t1669
    record_span!(parser, span_start947)
    return result948
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1670 = parse_term(parser)
    term949 = _t1670
    _t1671 = parse_term(parser)
    term_3950 = _t1671
    _t1672 = parse_term(parser)
    term_4951 = _t1672
    consume_literal!(parser, ")")
    _t1673 = Proto.RelTerm(rel_term_type=OneOf(:term, term949))
    _t1674 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3950))
    _t1675 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4951))
    _t1676 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1673, _t1674, _t1675])
    result953 = _t1676
    record_span!(parser, span_start952)
    return result953
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start957 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1677 = parse_term(parser)
    term954 = _t1677
    _t1678 = parse_term(parser)
    term_3955 = _t1678
    _t1679 = parse_term(parser)
    term_4956 = _t1679
    consume_literal!(parser, ")")
    _t1680 = Proto.RelTerm(rel_term_type=OneOf(:term, term954))
    _t1681 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3955))
    _t1682 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4956))
    _t1683 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1680, _t1681, _t1682])
    result958 = _t1683
    record_span!(parser, span_start957)
    return result958
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start962 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1684 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1685 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1686 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1687 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1688 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1689 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1690 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1691 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1692 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1693 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1694 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1695 = 1
                                                else
                                                    _t1695 = -1
                                                end
                                                _t1694 = _t1695
                                            end
                                            _t1693 = _t1694
                                        end
                                        _t1692 = _t1693
                                    end
                                    _t1691 = _t1692
                                end
                                _t1690 = _t1691
                            end
                            _t1689 = _t1690
                        end
                        _t1688 = _t1689
                    end
                    _t1687 = _t1688
                end
                _t1686 = _t1687
            end
            _t1685 = _t1686
        end
        _t1684 = _t1685
    end
    prediction959 = _t1684
    if prediction959 == 1
        push_path!(parser, 2)
        _t1697 = parse_term(parser)
        term961 = _t1697
        pop_path!(parser)
        _t1698 = Proto.RelTerm(rel_term_type=OneOf(:term, term961))
        _t1696 = _t1698
    else
        if prediction959 == 0
            push_path!(parser, 1)
            _t1700 = parse_specialized_value(parser)
            specialized_value960 = _t1700
            pop_path!(parser)
            _t1701 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value960))
            _t1699 = _t1701
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1696 = _t1699
    end
    result963 = _t1696
    record_span!(parser, span_start962)
    return result963
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start965 = span_start(parser)
    consume_literal!(parser, "#")
    _t1702 = parse_value(parser)
    value964 = _t1702
    result966 = value964
    record_span!(parser, span_start965)
    return result966
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start976 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    push_path!(parser, 3)
    _t1703 = parse_name(parser)
    name967 = _t1703
    pop_path!(parser)
    push_path!(parser, 2)
    xs972 = Proto.RelTerm[]
    cond973 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx974 = 0
    while cond973
        push_path!(parser, idx974)
        _t1704 = parse_rel_term(parser)
        item975 = _t1704
        pop_path!(parser)
        push!(xs972, item975)
        idx974 = (idx974 + 1)
        cond973 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms971 = xs972
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1705 = Proto.RelAtom(name=name967, terms=rel_terms971)
    result977 = _t1705
    record_span!(parser, span_start976)
    return result977
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    push_path!(parser, 2)
    _t1706 = parse_term(parser)
    term978 = _t1706
    pop_path!(parser)
    push_path!(parser, 3)
    _t1707 = parse_term(parser)
    term_3979 = _t1707
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1708 = Proto.Cast(input=term978, result=term_3979)
    result981 = _t1708
    record_span!(parser, span_start980)
    return result981
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    span_start990 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs986 = Proto.Attribute[]
    cond987 = match_lookahead_literal(parser, "(", 0)
    idx988 = 0
    while cond987
        push_path!(parser, idx988)
        _t1709 = parse_attribute(parser)
        item989 = _t1709
        pop_path!(parser)
        push!(xs986, item989)
        idx988 = (idx988 + 1)
        cond987 = match_lookahead_literal(parser, "(", 0)
    end
    attributes985 = xs986
    consume_literal!(parser, ")")
    result991 = attributes985
    record_span!(parser, span_start990)
    return result991
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1001 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    push_path!(parser, 1)
    _t1710 = parse_name(parser)
    name992 = _t1710
    pop_path!(parser)
    push_path!(parser, 2)
    xs997 = Proto.Value[]
    cond998 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx999 = 0
    while cond998
        push_path!(parser, idx999)
        _t1711 = parse_value(parser)
        item1000 = _t1711
        pop_path!(parser)
        push!(xs997, item1000)
        idx999 = (idx999 + 1)
        cond998 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values996 = xs997
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1712 = Proto.Attribute(name=name992, args=values996)
    result1002 = _t1712
    record_span!(parser, span_start1001)
    return result1002
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1012 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    push_path!(parser, 1)
    xs1007 = Proto.RelationId[]
    cond1008 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    idx1009 = 0
    while cond1008
        push_path!(parser, idx1009)
        _t1713 = parse_relation_id(parser)
        item1010 = _t1713
        pop_path!(parser)
        push!(xs1007, item1010)
        idx1009 = (idx1009 + 1)
        cond1008 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1006 = xs1007
    pop_path!(parser)
    push_path!(parser, 2)
    _t1714 = parse_script(parser)
    script1011 = _t1714
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1715 = Proto.Algorithm(var"#global"=relation_ids1006, body=script1011)
    result1013 = _t1715
    record_span!(parser, span_start1012)
    return result1013
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1022 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    push_path!(parser, 1)
    xs1018 = Proto.Construct[]
    cond1019 = match_lookahead_literal(parser, "(", 0)
    idx1020 = 0
    while cond1019
        push_path!(parser, idx1020)
        _t1716 = parse_construct(parser)
        item1021 = _t1716
        pop_path!(parser)
        push!(xs1018, item1021)
        idx1020 = (idx1020 + 1)
        cond1019 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1017 = xs1018
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1717 = Proto.Script(constructs=constructs1017)
    result1023 = _t1717
    record_span!(parser, span_start1022)
    return result1023
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1027 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1719 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1720 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1721 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1722 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1723 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1724 = 1
                            else
                                _t1724 = -1
                            end
                            _t1723 = _t1724
                        end
                        _t1722 = _t1723
                    end
                    _t1721 = _t1722
                end
                _t1720 = _t1721
            end
            _t1719 = _t1720
        end
        _t1718 = _t1719
    else
        _t1718 = -1
    end
    prediction1024 = _t1718
    if prediction1024 == 1
        push_path!(parser, 2)
        _t1726 = parse_instruction(parser)
        instruction1026 = _t1726
        pop_path!(parser)
        _t1727 = Proto.Construct(construct_type=OneOf(:instruction, instruction1026))
        _t1725 = _t1727
    else
        if prediction1024 == 0
            push_path!(parser, 1)
            _t1729 = parse_loop(parser)
            loop1025 = _t1729
            pop_path!(parser)
            _t1730 = Proto.Construct(construct_type=OneOf(:loop, loop1025))
            _t1728 = _t1730
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1725 = _t1728
    end
    result1028 = _t1725
    record_span!(parser, span_start1027)
    return result1028
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1031 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    push_path!(parser, 1)
    _t1731 = parse_init(parser)
    init1029 = _t1731
    pop_path!(parser)
    push_path!(parser, 2)
    _t1732 = parse_script(parser)
    script1030 = _t1732
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1733 = Proto.Loop(init=init1029, body=script1030)
    result1032 = _t1733
    record_span!(parser, span_start1031)
    return result1032
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    span_start1041 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1037 = Proto.Instruction[]
    cond1038 = match_lookahead_literal(parser, "(", 0)
    idx1039 = 0
    while cond1038
        push_path!(parser, idx1039)
        _t1734 = parse_instruction(parser)
        item1040 = _t1734
        pop_path!(parser)
        push!(xs1037, item1040)
        idx1039 = (idx1039 + 1)
        cond1038 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1036 = xs1037
    consume_literal!(parser, ")")
    result1042 = instructions1036
    record_span!(parser, span_start1041)
    return result1042
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1049 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1736 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1737 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1738 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1739 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1740 = 0
                        else
                            _t1740 = -1
                        end
                        _t1739 = _t1740
                    end
                    _t1738 = _t1739
                end
                _t1737 = _t1738
            end
            _t1736 = _t1737
        end
        _t1735 = _t1736
    else
        _t1735 = -1
    end
    prediction1043 = _t1735
    if prediction1043 == 4
        push_path!(parser, 6)
        _t1742 = parse_monus_def(parser)
        monus_def1048 = _t1742
        pop_path!(parser)
        _t1743 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1048))
        _t1741 = _t1743
    else
        if prediction1043 == 3
            push_path!(parser, 5)
            _t1745 = parse_monoid_def(parser)
            monoid_def1047 = _t1745
            pop_path!(parser)
            _t1746 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1047))
            _t1744 = _t1746
        else
            if prediction1043 == 2
                push_path!(parser, 3)
                _t1748 = parse_break(parser)
                break1046 = _t1748
                pop_path!(parser)
                _t1749 = Proto.Instruction(instr_type=OneOf(:var"#break", break1046))
                _t1747 = _t1749
            else
                if prediction1043 == 1
                    push_path!(parser, 2)
                    _t1751 = parse_upsert(parser)
                    upsert1045 = _t1751
                    pop_path!(parser)
                    _t1752 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1045))
                    _t1750 = _t1752
                else
                    if prediction1043 == 0
                        push_path!(parser, 1)
                        _t1754 = parse_assign(parser)
                        assign1044 = _t1754
                        pop_path!(parser)
                        _t1755 = Proto.Instruction(instr_type=OneOf(:assign, assign1044))
                        _t1753 = _t1755
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1750 = _t1753
                end
                _t1747 = _t1750
            end
            _t1744 = _t1747
        end
        _t1741 = _t1744
    end
    result1050 = _t1741
    record_span!(parser, span_start1049)
    return result1050
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1054 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    push_path!(parser, 1)
    _t1756 = parse_relation_id(parser)
    relation_id1051 = _t1756
    pop_path!(parser)
    push_path!(parser, 2)
    _t1757 = parse_abstraction(parser)
    abstraction1052 = _t1757
    pop_path!(parser)
    push_path!(parser, 3)
    if match_lookahead_literal(parser, "(", 0)
        _t1759 = parse_attrs(parser)
        _t1758 = _t1759
    else
        _t1758 = nothing
    end
    attrs1053 = _t1758
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1760 = Proto.Assign(name=relation_id1051, body=abstraction1052, attrs=(!isnothing(attrs1053) ? attrs1053 : Proto.Attribute[]))
    result1055 = _t1760
    record_span!(parser, span_start1054)
    return result1055
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1059 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    push_path!(parser, 1)
    _t1761 = parse_relation_id(parser)
    relation_id1056 = _t1761
    pop_path!(parser)
    _t1762 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1057 = _t1762
    push_path!(parser, 3)
    if match_lookahead_literal(parser, "(", 0)
        _t1764 = parse_attrs(parser)
        _t1763 = _t1764
    else
        _t1763 = nothing
    end
    attrs1058 = _t1763
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1765 = Proto.Upsert(name=relation_id1056, body=abstraction_with_arity1057[1], attrs=(!isnothing(attrs1058) ? attrs1058 : Proto.Attribute[]), value_arity=abstraction_with_arity1057[2])
    result1060 = _t1765
    record_span!(parser, span_start1059)
    return result1060
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    span_start1063 = span_start(parser)
    consume_literal!(parser, "(")
    _t1766 = parse_bindings(parser)
    bindings1061 = _t1766
    _t1767 = parse_formula(parser)
    formula1062 = _t1767
    consume_literal!(parser, ")")
    _t1768 = Proto.Abstraction(vars=vcat(bindings1061[1], !isnothing(bindings1061[2]) ? bindings1061[2] : []), value=formula1062)
    result1064 = (_t1768, length(bindings1061[2]),)
    record_span!(parser, span_start1063)
    return result1064
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1068 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    push_path!(parser, 1)
    _t1769 = parse_relation_id(parser)
    relation_id1065 = _t1769
    pop_path!(parser)
    push_path!(parser, 2)
    _t1770 = parse_abstraction(parser)
    abstraction1066 = _t1770
    pop_path!(parser)
    push_path!(parser, 3)
    if match_lookahead_literal(parser, "(", 0)
        _t1772 = parse_attrs(parser)
        _t1771 = _t1772
    else
        _t1771 = nothing
    end
    attrs1067 = _t1771
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1773 = Proto.Break(name=relation_id1065, body=abstraction1066, attrs=(!isnothing(attrs1067) ? attrs1067 : Proto.Attribute[]))
    result1069 = _t1773
    record_span!(parser, span_start1068)
    return result1069
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1074 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    push_path!(parser, 1)
    _t1774 = parse_monoid(parser)
    monoid1070 = _t1774
    pop_path!(parser)
    push_path!(parser, 2)
    _t1775 = parse_relation_id(parser)
    relation_id1071 = _t1775
    pop_path!(parser)
    _t1776 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1072 = _t1776
    push_path!(parser, 4)
    if match_lookahead_literal(parser, "(", 0)
        _t1778 = parse_attrs(parser)
        _t1777 = _t1778
    else
        _t1777 = nothing
    end
    attrs1073 = _t1777
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1779 = Proto.MonoidDef(monoid=monoid1070, name=relation_id1071, body=abstraction_with_arity1072[1], attrs=(!isnothing(attrs1073) ? attrs1073 : Proto.Attribute[]), value_arity=abstraction_with_arity1072[2])
    result1075 = _t1779
    record_span!(parser, span_start1074)
    return result1075
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1081 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1781 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1782 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1783 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1784 = 2
                    else
                        _t1784 = -1
                    end
                    _t1783 = _t1784
                end
                _t1782 = _t1783
            end
            _t1781 = _t1782
        end
        _t1780 = _t1781
    else
        _t1780 = -1
    end
    prediction1076 = _t1780
    if prediction1076 == 3
        push_path!(parser, 4)
        _t1786 = parse_sum_monoid(parser)
        sum_monoid1080 = _t1786
        pop_path!(parser)
        _t1787 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1080))
        _t1785 = _t1787
    else
        if prediction1076 == 2
            push_path!(parser, 3)
            _t1789 = parse_max_monoid(parser)
            max_monoid1079 = _t1789
            pop_path!(parser)
            _t1790 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1079))
            _t1788 = _t1790
        else
            if prediction1076 == 1
                push_path!(parser, 2)
                _t1792 = parse_min_monoid(parser)
                min_monoid1078 = _t1792
                pop_path!(parser)
                _t1793 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1078))
                _t1791 = _t1793
            else
                if prediction1076 == 0
                    push_path!(parser, 1)
                    _t1795 = parse_or_monoid(parser)
                    or_monoid1077 = _t1795
                    pop_path!(parser)
                    _t1796 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1077))
                    _t1794 = _t1796
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1791 = _t1794
            end
            _t1788 = _t1791
        end
        _t1785 = _t1788
    end
    result1082 = _t1785
    record_span!(parser, span_start1081)
    return result1082
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1083 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1797 = Proto.OrMonoid()
    result1084 = _t1797
    record_span!(parser, span_start1083)
    return result1084
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1086 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    push_path!(parser, 1)
    _t1798 = parse_type(parser)
    type1085 = _t1798
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1799 = Proto.MinMonoid(var"#type"=type1085)
    result1087 = _t1799
    record_span!(parser, span_start1086)
    return result1087
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1089 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    push_path!(parser, 1)
    _t1800 = parse_type(parser)
    type1088 = _t1800
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1801 = Proto.MaxMonoid(var"#type"=type1088)
    result1090 = _t1801
    record_span!(parser, span_start1089)
    return result1090
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1092 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    push_path!(parser, 1)
    _t1802 = parse_type(parser)
    type1091 = _t1802
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1803 = Proto.SumMonoid(var"#type"=type1091)
    result1093 = _t1803
    record_span!(parser, span_start1092)
    return result1093
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1098 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    push_path!(parser, 1)
    _t1804 = parse_monoid(parser)
    monoid1094 = _t1804
    pop_path!(parser)
    push_path!(parser, 2)
    _t1805 = parse_relation_id(parser)
    relation_id1095 = _t1805
    pop_path!(parser)
    _t1806 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1096 = _t1806
    push_path!(parser, 4)
    if match_lookahead_literal(parser, "(", 0)
        _t1808 = parse_attrs(parser)
        _t1807 = _t1808
    else
        _t1807 = nothing
    end
    attrs1097 = _t1807
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1809 = Proto.MonusDef(monoid=monoid1094, name=relation_id1095, body=abstraction_with_arity1096[1], attrs=(!isnothing(attrs1097) ? attrs1097 : Proto.Attribute[]), value_arity=abstraction_with_arity1096[2])
    result1099 = _t1809
    record_span!(parser, span_start1098)
    return result1099
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1104 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    push_path!(parser, 2)
    _t1810 = parse_relation_id(parser)
    relation_id1100 = _t1810
    pop_path!(parser)
    _t1811 = parse_abstraction(parser)
    abstraction1101 = _t1811
    _t1812 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1102 = _t1812
    _t1813 = parse_functional_dependency_values(parser)
    functional_dependency_values1103 = _t1813
    consume_literal!(parser, ")")
    _t1814 = Proto.FunctionalDependency(guard=abstraction1101, keys=functional_dependency_keys1102, values=functional_dependency_values1103)
    _t1815 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1814), name=relation_id1100)
    result1105 = _t1815
    record_span!(parser, span_start1104)
    return result1105
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    span_start1114 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1110 = Proto.Var[]
    cond1111 = match_lookahead_terminal(parser, "SYMBOL", 0)
    idx1112 = 0
    while cond1111
        push_path!(parser, idx1112)
        _t1816 = parse_var(parser)
        item1113 = _t1816
        pop_path!(parser)
        push!(xs1110, item1113)
        idx1112 = (idx1112 + 1)
        cond1111 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1109 = xs1110
    consume_literal!(parser, ")")
    result1115 = vars1109
    record_span!(parser, span_start1114)
    return result1115
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    span_start1124 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1120 = Proto.Var[]
    cond1121 = match_lookahead_terminal(parser, "SYMBOL", 0)
    idx1122 = 0
    while cond1121
        push_path!(parser, idx1122)
        _t1817 = parse_var(parser)
        item1123 = _t1817
        pop_path!(parser)
        push!(xs1120, item1123)
        idx1122 = (idx1122 + 1)
        cond1121 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1119 = xs1120
    consume_literal!(parser, ")")
    result1125 = vars1119
    record_span!(parser, span_start1124)
    return result1125
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1130 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1819 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1820 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1821 = 1
                else
                    _t1821 = -1
                end
                _t1820 = _t1821
            end
            _t1819 = _t1820
        end
        _t1818 = _t1819
    else
        _t1818 = -1
    end
    prediction1126 = _t1818
    if prediction1126 == 2
        push_path!(parser, 3)
        _t1823 = parse_csv_data(parser)
        csv_data1129 = _t1823
        pop_path!(parser)
        _t1824 = Proto.Data(data_type=OneOf(:csv_data, csv_data1129))
        _t1822 = _t1824
    else
        if prediction1126 == 1
            push_path!(parser, 2)
            _t1826 = parse_betree_relation(parser)
            betree_relation1128 = _t1826
            pop_path!(parser)
            _t1827 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1128))
            _t1825 = _t1827
        else
            if prediction1126 == 0
                push_path!(parser, 1)
                _t1829 = parse_rel_edb(parser)
                rel_edb1127 = _t1829
                pop_path!(parser)
                _t1830 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb1127))
                _t1828 = _t1830
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1825 = _t1828
        end
        _t1822 = _t1825
    end
    result1131 = _t1822
    record_span!(parser, span_start1130)
    return result1131
end

function parse_rel_edb(parser::ParserState)::Proto.RelEDB
    span_start1135 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    push_path!(parser, 1)
    _t1831 = parse_relation_id(parser)
    relation_id1132 = _t1831
    pop_path!(parser)
    push_path!(parser, 2)
    _t1832 = parse_rel_edb_path(parser)
    rel_edb_path1133 = _t1832
    pop_path!(parser)
    push_path!(parser, 3)
    _t1833 = parse_rel_edb_types(parser)
    rel_edb_types1134 = _t1833
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1834 = Proto.RelEDB(target_id=relation_id1132, path=rel_edb_path1133, types=rel_edb_types1134)
    result1136 = _t1834
    record_span!(parser, span_start1135)
    return result1136
end

function parse_rel_edb_path(parser::ParserState)::Vector{String}
    span_start1145 = span_start(parser)
    consume_literal!(parser, "[")
    xs1141 = String[]
    cond1142 = match_lookahead_terminal(parser, "STRING", 0)
    idx1143 = 0
    while cond1142
        push_path!(parser, idx1143)
        item1144 = consume_terminal!(parser, "STRING")
        pop_path!(parser)
        push!(xs1141, item1144)
        idx1143 = (idx1143 + 1)
        cond1142 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1140 = xs1141
    consume_literal!(parser, "]")
    result1146 = strings1140
    record_span!(parser, span_start1145)
    return result1146
end

function parse_rel_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1155 = span_start(parser)
    consume_literal!(parser, "[")
    xs1151 = Proto.var"#Type"[]
    cond1152 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx1153 = 0
    while cond1152
        push_path!(parser, idx1153)
        _t1835 = parse_type(parser)
        item1154 = _t1835
        pop_path!(parser)
        push!(xs1151, item1154)
        idx1153 = (idx1153 + 1)
        cond1152 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1150 = xs1151
    consume_literal!(parser, "]")
    result1156 = types1150
    record_span!(parser, span_start1155)
    return result1156
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1159 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    push_path!(parser, 1)
    _t1836 = parse_relation_id(parser)
    relation_id1157 = _t1836
    pop_path!(parser)
    push_path!(parser, 2)
    _t1837 = parse_betree_info(parser)
    betree_info1158 = _t1837
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1838 = Proto.BeTreeRelation(name=relation_id1157, relation_info=betree_info1158)
    result1160 = _t1838
    record_span!(parser, span_start1159)
    return result1160
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1164 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1839 = parse_betree_info_key_types(parser)
    betree_info_key_types1161 = _t1839
    _t1840 = parse_betree_info_value_types(parser)
    betree_info_value_types1162 = _t1840
    _t1841 = parse_config_dict(parser)
    config_dict1163 = _t1841
    consume_literal!(parser, ")")
    _t1842 = construct_betree_info(parser, betree_info_key_types1161, betree_info_value_types1162, config_dict1163)
    result1165 = _t1842
    record_span!(parser, span_start1164)
    return result1165
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1174 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1170 = Proto.var"#Type"[]
    cond1171 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx1172 = 0
    while cond1171
        push_path!(parser, idx1172)
        _t1843 = parse_type(parser)
        item1173 = _t1843
        pop_path!(parser)
        push!(xs1170, item1173)
        idx1172 = (idx1172 + 1)
        cond1171 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1169 = xs1170
    consume_literal!(parser, ")")
    result1175 = types1169
    record_span!(parser, span_start1174)
    return result1175
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1184 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1180 = Proto.var"#Type"[]
    cond1181 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx1182 = 0
    while cond1181
        push_path!(parser, idx1182)
        _t1844 = parse_type(parser)
        item1183 = _t1844
        pop_path!(parser)
        push!(xs1180, item1183)
        idx1182 = (idx1182 + 1)
        cond1181 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1179 = xs1180
    consume_literal!(parser, ")")
    result1185 = types1179
    record_span!(parser, span_start1184)
    return result1185
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1190 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    push_path!(parser, 1)
    _t1845 = parse_csvlocator(parser)
    csvlocator1186 = _t1845
    pop_path!(parser)
    push_path!(parser, 2)
    _t1846 = parse_csv_config(parser)
    csv_config1187 = _t1846
    pop_path!(parser)
    push_path!(parser, 3)
    _t1847 = parse_csv_columns(parser)
    csv_columns1188 = _t1847
    pop_path!(parser)
    push_path!(parser, 4)
    _t1848 = parse_csv_asof(parser)
    csv_asof1189 = _t1848
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1849 = Proto.CSVData(locator=csvlocator1186, config=csv_config1187, columns=csv_columns1188, asof=csv_asof1189)
    result1191 = _t1849
    record_span!(parser, span_start1190)
    return result1191
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1194 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    push_path!(parser, 1)
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1851 = parse_csv_locator_paths(parser)
        _t1850 = _t1851
    else
        _t1850 = nothing
    end
    csv_locator_paths1192 = _t1850
    pop_path!(parser)
    push_path!(parser, 2)
    if match_lookahead_literal(parser, "(", 0)
        _t1853 = parse_csv_locator_inline_data(parser)
        _t1852 = _t1853
    else
        _t1852 = nothing
    end
    csv_locator_inline_data1193 = _t1852
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1854 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1192) ? csv_locator_paths1192 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1193) ? csv_locator_inline_data1193 : "")))
    result1195 = _t1854
    record_span!(parser, span_start1194)
    return result1195
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    span_start1204 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1200 = String[]
    cond1201 = match_lookahead_terminal(parser, "STRING", 0)
    idx1202 = 0
    while cond1201
        push_path!(parser, idx1202)
        item1203 = consume_terminal!(parser, "STRING")
        pop_path!(parser)
        push!(xs1200, item1203)
        idx1202 = (idx1202 + 1)
        cond1201 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1199 = xs1200
    consume_literal!(parser, ")")
    result1205 = strings1199
    record_span!(parser, span_start1204)
    return result1205
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    span_start1207 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1206 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1208 = string1206
    record_span!(parser, span_start1207)
    return result1208
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1210 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1855 = parse_config_dict(parser)
    config_dict1209 = _t1855
    consume_literal!(parser, ")")
    _t1856 = construct_csv_config(parser, config_dict1209)
    result1211 = _t1856
    record_span!(parser, span_start1210)
    return result1211
end

function parse_csv_columns(parser::ParserState)::Vector{Proto.CSVColumn}
    span_start1220 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1216 = Proto.CSVColumn[]
    cond1217 = match_lookahead_literal(parser, "(", 0)
    idx1218 = 0
    while cond1217
        push_path!(parser, idx1218)
        _t1857 = parse_csv_column(parser)
        item1219 = _t1857
        pop_path!(parser)
        push!(xs1216, item1219)
        idx1218 = (idx1218 + 1)
        cond1217 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns1215 = xs1216
    consume_literal!(parser, ")")
    result1221 = csv_columns1215
    record_span!(parser, span_start1220)
    return result1221
end

function parse_csv_column(parser::ParserState)::Proto.CSVColumn
    span_start1232 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    push_path!(parser, 1)
    string1222 = consume_terminal!(parser, "STRING")
    pop_path!(parser)
    push_path!(parser, 2)
    _t1858 = parse_relation_id(parser)
    relation_id1223 = _t1858
    pop_path!(parser)
    consume_literal!(parser, "[")
    push_path!(parser, 3)
    xs1228 = Proto.var"#Type"[]
    cond1229 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx1230 = 0
    while cond1229
        push_path!(parser, idx1230)
        _t1859 = parse_type(parser)
        item1231 = _t1859
        pop_path!(parser)
        push!(xs1228, item1231)
        idx1230 = (idx1230 + 1)
        cond1229 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1227 = xs1228
    pop_path!(parser)
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1860 = Proto.CSVColumn(column_name=string1222, target_id=relation_id1223, types=types1227)
    result1233 = _t1860
    record_span!(parser, span_start1232)
    return result1233
end

function parse_csv_asof(parser::ParserState)::String
    span_start1235 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1234 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1236 = string1234
    record_span!(parser, span_start1235)
    return result1236
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1238 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    push_path!(parser, 1)
    _t1861 = parse_fragment_id(parser)
    fragment_id1237 = _t1861
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1862 = Proto.Undefine(fragment_id=fragment_id1237)
    result1239 = _t1862
    record_span!(parser, span_start1238)
    return result1239
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1248 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    push_path!(parser, 1)
    xs1244 = Proto.RelationId[]
    cond1245 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    idx1246 = 0
    while cond1245
        push_path!(parser, idx1246)
        _t1863 = parse_relation_id(parser)
        item1247 = _t1863
        pop_path!(parser)
        push!(xs1244, item1247)
        idx1246 = (idx1246 + 1)
        cond1245 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1243 = xs1244
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1864 = Proto.Context(relations=relation_ids1243)
    result1249 = _t1864
    record_span!(parser, span_start1248)
    return result1249
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1252 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    push_path!(parser, 1)
    _t1865 = parse_rel_edb_path(parser)
    rel_edb_path1250 = _t1865
    pop_path!(parser)
    push_path!(parser, 2)
    _t1866 = parse_relation_id(parser)
    relation_id1251 = _t1866
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1867 = Proto.Snapshot(destination_path=rel_edb_path1250, source_relation=relation_id1251)
    result1253 = _t1867
    record_span!(parser, span_start1252)
    return result1253
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    span_start1262 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1258 = Proto.Read[]
    cond1259 = match_lookahead_literal(parser, "(", 0)
    idx1260 = 0
    while cond1259
        push_path!(parser, idx1260)
        _t1868 = parse_read(parser)
        item1261 = _t1868
        pop_path!(parser)
        push!(xs1258, item1261)
        idx1260 = (idx1260 + 1)
        cond1259 = match_lookahead_literal(parser, "(", 0)
    end
    reads1257 = xs1258
    consume_literal!(parser, ")")
    result1263 = reads1257
    record_span!(parser, span_start1262)
    return result1263
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1270 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1870 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1871 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1872 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1873 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1874 = 3
                        else
                            _t1874 = -1
                        end
                        _t1873 = _t1874
                    end
                    _t1872 = _t1873
                end
                _t1871 = _t1872
            end
            _t1870 = _t1871
        end
        _t1869 = _t1870
    else
        _t1869 = -1
    end
    prediction1264 = _t1869
    if prediction1264 == 4
        push_path!(parser, 5)
        _t1876 = parse_export(parser)
        export1269 = _t1876
        pop_path!(parser)
        _t1877 = Proto.Read(read_type=OneOf(:var"#export", export1269))
        _t1875 = _t1877
    else
        if prediction1264 == 3
            push_path!(parser, 4)
            _t1879 = parse_abort(parser)
            abort1268 = _t1879
            pop_path!(parser)
            _t1880 = Proto.Read(read_type=OneOf(:abort, abort1268))
            _t1878 = _t1880
        else
            if prediction1264 == 2
                push_path!(parser, 3)
                _t1882 = parse_what_if(parser)
                what_if1267 = _t1882
                pop_path!(parser)
                _t1883 = Proto.Read(read_type=OneOf(:what_if, what_if1267))
                _t1881 = _t1883
            else
                if prediction1264 == 1
                    push_path!(parser, 2)
                    _t1885 = parse_output(parser)
                    output1266 = _t1885
                    pop_path!(parser)
                    _t1886 = Proto.Read(read_type=OneOf(:output, output1266))
                    _t1884 = _t1886
                else
                    if prediction1264 == 0
                        push_path!(parser, 1)
                        _t1888 = parse_demand(parser)
                        demand1265 = _t1888
                        pop_path!(parser)
                        _t1889 = Proto.Read(read_type=OneOf(:demand, demand1265))
                        _t1887 = _t1889
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1884 = _t1887
                end
                _t1881 = _t1884
            end
            _t1878 = _t1881
        end
        _t1875 = _t1878
    end
    result1271 = _t1875
    record_span!(parser, span_start1270)
    return result1271
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1273 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    push_path!(parser, 1)
    _t1890 = parse_relation_id(parser)
    relation_id1272 = _t1890
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1891 = Proto.Demand(relation_id=relation_id1272)
    result1274 = _t1891
    record_span!(parser, span_start1273)
    return result1274
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1277 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    push_path!(parser, 1)
    _t1892 = parse_name(parser)
    name1275 = _t1892
    pop_path!(parser)
    push_path!(parser, 2)
    _t1893 = parse_relation_id(parser)
    relation_id1276 = _t1893
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1894 = Proto.Output(name=name1275, relation_id=relation_id1276)
    result1278 = _t1894
    record_span!(parser, span_start1277)
    return result1278
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1281 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    push_path!(parser, 1)
    _t1895 = parse_name(parser)
    name1279 = _t1895
    pop_path!(parser)
    push_path!(parser, 2)
    _t1896 = parse_epoch(parser)
    epoch1280 = _t1896
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1897 = Proto.WhatIf(branch=name1279, epoch=epoch1280)
    result1282 = _t1897
    record_span!(parser, span_start1281)
    return result1282
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1285 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    push_path!(parser, 1)
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1899 = parse_name(parser)
        _t1898 = _t1899
    else
        _t1898 = nothing
    end
    name1283 = _t1898
    pop_path!(parser)
    push_path!(parser, 2)
    _t1900 = parse_relation_id(parser)
    relation_id1284 = _t1900
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1901 = Proto.Abort(name=(!isnothing(name1283) ? name1283 : "abort"), relation_id=relation_id1284)
    result1286 = _t1901
    record_span!(parser, span_start1285)
    return result1286
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1288 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    push_path!(parser, 1)
    _t1902 = parse_export_csv_config(parser)
    export_csv_config1287 = _t1902
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1903 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1287))
    result1289 = _t1903
    record_span!(parser, span_start1288)
    return result1289
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1293 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1904 = parse_export_csv_path(parser)
    export_csv_path1290 = _t1904
    _t1905 = parse_export_csv_columns(parser)
    export_csv_columns1291 = _t1905
    _t1906 = parse_config_dict(parser)
    config_dict1292 = _t1906
    consume_literal!(parser, ")")
    _t1907 = export_csv_config(parser, export_csv_path1290, export_csv_columns1291, config_dict1292)
    result1294 = _t1907
    record_span!(parser, span_start1293)
    return result1294
end

function parse_export_csv_path(parser::ParserState)::String
    span_start1296 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1295 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1297 = string1295
    record_span!(parser, span_start1296)
    return result1297
end

function parse_export_csv_columns(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    span_start1306 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1302 = Proto.ExportCSVColumn[]
    cond1303 = match_lookahead_literal(parser, "(", 0)
    idx1304 = 0
    while cond1303
        push_path!(parser, idx1304)
        _t1908 = parse_export_csv_column(parser)
        item1305 = _t1908
        pop_path!(parser)
        push!(xs1302, item1305)
        idx1304 = (idx1304 + 1)
        cond1303 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1301 = xs1302
    consume_literal!(parser, ")")
    result1307 = export_csv_columns1301
    record_span!(parser, span_start1306)
    return result1307
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1310 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    push_path!(parser, 1)
    string1308 = consume_terminal!(parser, "STRING")
    pop_path!(parser)
    push_path!(parser, 2)
    _t1909 = parse_relation_id(parser)
    relation_id1309 = _t1909
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1910 = Proto.ExportCSVColumn(column_name=string1308, column_data=relation_id1309)
    result1311 = _t1910
    record_span!(parser, span_start1310)
    return result1311
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
