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

scan_int32(n::String) = Base.parse(Int32, n[1:end-3])  # Remove "i32" suffix

scan_uint32(n::String) = Base.parse(UInt32, n[1:end-3])  # Remove "u32" suffix

scan_float32(f::String) = Base.parse(Float32, f[1:end-3])  # Remove "f32" suffix

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
    ("FLOAT32", r"[-]?\d+\.\d+f32", scan_float32),
    ("INT", r"[-]?\d+", scan_int),
    ("INT32", r"[-]?\d+i32", scan_int32),
    ("UINT32", r"\d+u32", scan_uint32),
    ("INT128", r"[-]?\d+i128", scan_int128),
    ("STRING", r"\"(?:[^\"\\]|\\.)*\"", scan_string),
    ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_./#-]*", scan_symbol),
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
    provenance::Dict{Any,Span}
    _line_starts::Vector{Int}

    function ParserState(tokens::Vector{Token}, input_str::String)
        return new(tokens, 1, Dict(), nothing, Dict(), Dict{Any,Span}(), _compute_line_starts(input_str))
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
    # Use big-endian and the lower 128 bits of the hash, consistent with pyrel.
    id_high = ntoh(reinterpret(UInt64, hash_bytes[17:24])[1])
    id_low = ntoh(reinterpret(UInt64, hash_bytes[25:32])[1])
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
    if (!isnothing(value) && _has_proto_field(value, Symbol("int32_value")))
        return _get_oneof_field(value, :int32_value)
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
    _t1931 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t1931
    _t1932 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t1932
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1933 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1933
    _t1934 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1934
    _t1935 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1935
    _t1936 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1936
    _t1937 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1937
    _t1938 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1938
    _t1939 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1939
    _t1940 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1940
    _t1941 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1941
    _t1942 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1942
    _t1943 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1943
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1944 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1944
    _t1945 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1945
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
    _t1946 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1946
    _t1947 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1947
    _t1948 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1948
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1949 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1949
    _t1950 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1950
    _t1951 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1951
    _t1952 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1952
    _t1953 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1953
    _t1954 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1954
    _t1955 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1955
    _t1956 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1956
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1957 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1957
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start610 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1209 = parse_configure(parser)
        _t1208 = _t1209
    else
        _t1208 = nothing
    end
    configure604 = _t1208
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1211 = parse_sync(parser)
        _t1210 = _t1211
    else
        _t1210 = nothing
    end
    sync605 = _t1210
    xs606 = Proto.Epoch[]
    cond607 = match_lookahead_literal(parser, "(", 0)
    while cond607
        _t1212 = parse_epoch(parser)
        item608 = _t1212
        push!(xs606, item608)
        cond607 = match_lookahead_literal(parser, "(", 0)
    end
    epochs609 = xs606
    consume_literal!(parser, ")")
    _t1213 = default_configure(parser)
    _t1214 = Proto.Transaction(epochs=epochs609, configure=(!isnothing(configure604) ? configure604 : _t1213), sync=sync605)
    result611 = _t1214
    record_span!(parser, span_start610, "Transaction")
    return result611
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start613 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1215 = parse_config_dict(parser)
    config_dict612 = _t1215
    consume_literal!(parser, ")")
    _t1216 = construct_configure(parser, config_dict612)
    result614 = _t1216
    record_span!(parser, span_start613, "Configure")
    return result614
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs615 = Tuple{String, Proto.Value}[]
    cond616 = match_lookahead_literal(parser, ":", 0)
    while cond616
        _t1217 = parse_config_key_value(parser)
        item617 = _t1217
        push!(xs615, item617)
        cond616 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values618 = xs615
    consume_literal!(parser, "}")
    return config_key_values618
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol619 = consume_terminal!(parser, "SYMBOL")
    _t1218 = parse_raw_value(parser)
    raw_value620 = _t1218
    return (symbol619, raw_value620,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start634 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1219 = 11
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1220 = 10
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1221 = 11
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1223 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1224 = 0
                        else
                            _t1224 = -1
                        end
                        _t1223 = _t1224
                    end
                    _t1222 = _t1223
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1225 = 12
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1226 = 7
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1227 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1228 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1229 = 8
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1230 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1231 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1232 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1233 = 9
                                                    else
                                                        _t1233 = -1
                                                    end
                                                    _t1232 = _t1233
                                                end
                                                _t1231 = _t1232
                                            end
                                            _t1230 = _t1231
                                        end
                                        _t1229 = _t1230
                                    end
                                    _t1228 = _t1229
                                end
                                _t1227 = _t1228
                            end
                            _t1226 = _t1227
                        end
                        _t1225 = _t1226
                    end
                    _t1222 = _t1225
                end
                _t1221 = _t1222
            end
            _t1220 = _t1221
        end
        _t1219 = _t1220
    end
    prediction621 = _t1219
    if prediction621 == 12
        uint32633 = consume_terminal!(parser, "UINT32")
        _t1235 = Proto.Value(value=OneOf(:uint32_value, uint32633))
        _t1234 = _t1235
    else
        if prediction621 == 11
            _t1237 = parse_boolean_value(parser)
            boolean_value632 = _t1237
            _t1238 = Proto.Value(value=OneOf(:boolean_value, boolean_value632))
            _t1236 = _t1238
        else
            if prediction621 == 10
                consume_literal!(parser, "missing")
                _t1240 = Proto.MissingValue()
                _t1241 = Proto.Value(value=OneOf(:missing_value, _t1240))
                _t1239 = _t1241
            else
                if prediction621 == 9
                    decimal631 = consume_terminal!(parser, "DECIMAL")
                    _t1243 = Proto.Value(value=OneOf(:decimal_value, decimal631))
                    _t1242 = _t1243
                else
                    if prediction621 == 8
                        int128630 = consume_terminal!(parser, "INT128")
                        _t1245 = Proto.Value(value=OneOf(:int128_value, int128630))
                        _t1244 = _t1245
                    else
                        if prediction621 == 7
                            uint128629 = consume_terminal!(parser, "UINT128")
                            _t1247 = Proto.Value(value=OneOf(:uint128_value, uint128629))
                            _t1246 = _t1247
                        else
                            if prediction621 == 6
                                float628 = consume_terminal!(parser, "FLOAT")
                                _t1249 = Proto.Value(value=OneOf(:float_value, float628))
                                _t1248 = _t1249
                            else
                                if prediction621 == 5
                                    float32627 = consume_terminal!(parser, "FLOAT32")
                                    _t1251 = Proto.Value(value=OneOf(:float32_value, float32627))
                                    _t1250 = _t1251
                                else
                                    if prediction621 == 4
                                        int626 = consume_terminal!(parser, "INT")
                                        _t1253 = Proto.Value(value=OneOf(:int_value, int626))
                                        _t1252 = _t1253
                                    else
                                        if prediction621 == 3
                                            int32625 = consume_terminal!(parser, "INT32")
                                            _t1255 = Proto.Value(value=OneOf(:int32_value, int32625))
                                            _t1254 = _t1255
                                        else
                                            if prediction621 == 2
                                                string624 = consume_terminal!(parser, "STRING")
                                                _t1257 = Proto.Value(value=OneOf(:string_value, string624))
                                                _t1256 = _t1257
                                            else
                                                if prediction621 == 1
                                                    _t1259 = parse_raw_datetime(parser)
                                                    raw_datetime623 = _t1259
                                                    _t1260 = Proto.Value(value=OneOf(:datetime_value, raw_datetime623))
                                                    _t1258 = _t1260
                                                else
                                                    if prediction621 == 0
                                                        _t1262 = parse_raw_date(parser)
                                                        raw_date622 = _t1262
                                                        _t1263 = Proto.Value(value=OneOf(:date_value, raw_date622))
                                                        _t1261 = _t1263
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1258 = _t1261
                                                end
                                                _t1256 = _t1258
                                            end
                                            _t1254 = _t1256
                                        end
                                        _t1252 = _t1254
                                    end
                                    _t1250 = _t1252
                                end
                                _t1248 = _t1250
                            end
                            _t1246 = _t1248
                        end
                        _t1244 = _t1246
                    end
                    _t1242 = _t1244
                end
                _t1239 = _t1242
            end
            _t1236 = _t1239
        end
        _t1234 = _t1236
    end
    result635 = _t1234
    record_span!(parser, span_start634, "Value")
    return result635
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start639 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int636 = consume_terminal!(parser, "INT")
    int_3637 = consume_terminal!(parser, "INT")
    int_4638 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1264 = Proto.DateValue(year=Int32(int636), month=Int32(int_3637), day=Int32(int_4638))
    result640 = _t1264
    record_span!(parser, span_start639, "DateValue")
    return result640
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start648 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int641 = consume_terminal!(parser, "INT")
    int_3642 = consume_terminal!(parser, "INT")
    int_4643 = consume_terminal!(parser, "INT")
    int_5644 = consume_terminal!(parser, "INT")
    int_6645 = consume_terminal!(parser, "INT")
    int_7646 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1265 = consume_terminal!(parser, "INT")
    else
        _t1265 = nothing
    end
    int_8647 = _t1265
    consume_literal!(parser, ")")
    _t1266 = Proto.DateTimeValue(year=Int32(int641), month=Int32(int_3642), day=Int32(int_4643), hour=Int32(int_5644), minute=Int32(int_6645), second=Int32(int_7646), microsecond=Int32((!isnothing(int_8647) ? int_8647 : 0)))
    result649 = _t1266
    record_span!(parser, span_start648, "DateTimeValue")
    return result649
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1267 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1268 = 1
        else
            _t1268 = -1
        end
        _t1267 = _t1268
    end
    prediction650 = _t1267
    if prediction650 == 1
        consume_literal!(parser, "false")
        _t1269 = false
    else
        if prediction650 == 0
            consume_literal!(parser, "true")
            _t1270 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1269 = _t1270
    end
    return _t1269
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start655 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs651 = Proto.FragmentId[]
    cond652 = match_lookahead_literal(parser, ":", 0)
    while cond652
        _t1271 = parse_fragment_id(parser)
        item653 = _t1271
        push!(xs651, item653)
        cond652 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids654 = xs651
    consume_literal!(parser, ")")
    _t1272 = Proto.Sync(fragments=fragment_ids654)
    result656 = _t1272
    record_span!(parser, span_start655, "Sync")
    return result656
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start658 = span_start(parser)
    consume_literal!(parser, ":")
    symbol657 = consume_terminal!(parser, "SYMBOL")
    result659 = Proto.FragmentId(Vector{UInt8}(symbol657))
    record_span!(parser, span_start658, "FragmentId")
    return result659
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start662 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1274 = parse_epoch_writes(parser)
        _t1273 = _t1274
    else
        _t1273 = nothing
    end
    epoch_writes660 = _t1273
    if match_lookahead_literal(parser, "(", 0)
        _t1276 = parse_epoch_reads(parser)
        _t1275 = _t1276
    else
        _t1275 = nothing
    end
    epoch_reads661 = _t1275
    consume_literal!(parser, ")")
    _t1277 = Proto.Epoch(writes=(!isnothing(epoch_writes660) ? epoch_writes660 : Proto.Write[]), reads=(!isnothing(epoch_reads661) ? epoch_reads661 : Proto.Read[]))
    result663 = _t1277
    record_span!(parser, span_start662, "Epoch")
    return result663
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs664 = Proto.Write[]
    cond665 = match_lookahead_literal(parser, "(", 0)
    while cond665
        _t1278 = parse_write(parser)
        item666 = _t1278
        push!(xs664, item666)
        cond665 = match_lookahead_literal(parser, "(", 0)
    end
    writes667 = xs664
    consume_literal!(parser, ")")
    return writes667
end

function parse_write(parser::ParserState)::Proto.Write
    span_start673 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1280 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1281 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1282 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1283 = 2
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
    else
        _t1279 = -1
    end
    prediction668 = _t1279
    if prediction668 == 3
        _t1285 = parse_snapshot(parser)
        snapshot672 = _t1285
        _t1286 = Proto.Write(write_type=OneOf(:snapshot, snapshot672))
        _t1284 = _t1286
    else
        if prediction668 == 2
            _t1288 = parse_context(parser)
            context671 = _t1288
            _t1289 = Proto.Write(write_type=OneOf(:context, context671))
            _t1287 = _t1289
        else
            if prediction668 == 1
                _t1291 = parse_undefine(parser)
                undefine670 = _t1291
                _t1292 = Proto.Write(write_type=OneOf(:undefine, undefine670))
                _t1290 = _t1292
            else
                if prediction668 == 0
                    _t1294 = parse_define(parser)
                    define669 = _t1294
                    _t1295 = Proto.Write(write_type=OneOf(:define, define669))
                    _t1293 = _t1295
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1290 = _t1293
            end
            _t1287 = _t1290
        end
        _t1284 = _t1287
    end
    result674 = _t1284
    record_span!(parser, span_start673, "Write")
    return result674
end

function parse_define(parser::ParserState)::Proto.Define
    span_start676 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1296 = parse_fragment(parser)
    fragment675 = _t1296
    consume_literal!(parser, ")")
    _t1297 = Proto.Define(fragment=fragment675)
    result677 = _t1297
    record_span!(parser, span_start676, "Define")
    return result677
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start683 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1298 = parse_new_fragment_id(parser)
    new_fragment_id678 = _t1298
    xs679 = Proto.Declaration[]
    cond680 = match_lookahead_literal(parser, "(", 0)
    while cond680
        _t1299 = parse_declaration(parser)
        item681 = _t1299
        push!(xs679, item681)
        cond680 = match_lookahead_literal(parser, "(", 0)
    end
    declarations682 = xs679
    consume_literal!(parser, ")")
    result684 = construct_fragment(parser, new_fragment_id678, declarations682)
    record_span!(parser, span_start683, "Fragment")
    return result684
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start686 = span_start(parser)
    _t1300 = parse_fragment_id(parser)
    fragment_id685 = _t1300
    start_fragment!(parser, fragment_id685)
    result687 = fragment_id685
    record_span!(parser, span_start686, "FragmentId")
    return result687
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start693 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "functional_dependency", 1)
            _t1302 = 2
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1303 = 3
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1304 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1305 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1306 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1307 = 1
                            else
                                _t1307 = -1
                            end
                            _t1306 = _t1307
                        end
                        _t1305 = _t1306
                    end
                    _t1304 = _t1305
                end
                _t1303 = _t1304
            end
            _t1302 = _t1303
        end
        _t1301 = _t1302
    else
        _t1301 = -1
    end
    prediction688 = _t1301
    if prediction688 == 3
        _t1309 = parse_data(parser)
        data692 = _t1309
        _t1310 = Proto.Declaration(declaration_type=OneOf(:data, data692))
        _t1308 = _t1310
    else
        if prediction688 == 2
            _t1312 = parse_constraint(parser)
            constraint691 = _t1312
            _t1313 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint691))
            _t1311 = _t1313
        else
            if prediction688 == 1
                _t1315 = parse_algorithm(parser)
                algorithm690 = _t1315
                _t1316 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm690))
                _t1314 = _t1316
            else
                if prediction688 == 0
                    _t1318 = parse_def(parser)
                    def689 = _t1318
                    _t1319 = Proto.Declaration(declaration_type=OneOf(:def, def689))
                    _t1317 = _t1319
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1314 = _t1317
            end
            _t1311 = _t1314
        end
        _t1308 = _t1311
    end
    result694 = _t1308
    record_span!(parser, span_start693, "Declaration")
    return result694
end

function parse_def(parser::ParserState)::Proto.Def
    span_start698 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1320 = parse_relation_id(parser)
    relation_id695 = _t1320
    _t1321 = parse_abstraction(parser)
    abstraction696 = _t1321
    if match_lookahead_literal(parser, "(", 0)
        _t1323 = parse_attrs(parser)
        _t1322 = _t1323
    else
        _t1322 = nothing
    end
    attrs697 = _t1322
    consume_literal!(parser, ")")
    _t1324 = Proto.Def(name=relation_id695, body=abstraction696, attrs=(!isnothing(attrs697) ? attrs697 : Proto.Attribute[]))
    result699 = _t1324
    record_span!(parser, span_start698, "Def")
    return result699
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start703 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1325 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1326 = 1
        else
            _t1326 = -1
        end
        _t1325 = _t1326
    end
    prediction700 = _t1325
    if prediction700 == 1
        uint128702 = consume_terminal!(parser, "UINT128")
        _t1327 = Proto.RelationId(uint128702.low, uint128702.high)
    else
        if prediction700 == 0
            consume_literal!(parser, ":")
            symbol701 = consume_terminal!(parser, "SYMBOL")
            _t1328 = relation_id_from_string(parser, symbol701)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1327 = _t1328
    end
    result704 = _t1327
    record_span!(parser, span_start703, "RelationId")
    return result704
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start707 = span_start(parser)
    consume_literal!(parser, "(")
    _t1329 = parse_bindings(parser)
    bindings705 = _t1329
    _t1330 = parse_formula(parser)
    formula706 = _t1330
    consume_literal!(parser, ")")
    _t1331 = Proto.Abstraction(vars=vcat(bindings705[1], !isnothing(bindings705[2]) ? bindings705[2] : []), value=formula706)
    result708 = _t1331
    record_span!(parser, span_start707, "Abstraction")
    return result708
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs709 = Proto.Binding[]
    cond710 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond710
        _t1332 = parse_binding(parser)
        item711 = _t1332
        push!(xs709, item711)
        cond710 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings712 = xs709
    if match_lookahead_literal(parser, "|", 0)
        _t1334 = parse_value_bindings(parser)
        _t1333 = _t1334
    else
        _t1333 = nothing
    end
    value_bindings713 = _t1333
    consume_literal!(parser, "]")
    return (bindings712, (!isnothing(value_bindings713) ? value_bindings713 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start716 = span_start(parser)
    symbol714 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1335 = parse_type(parser)
    type715 = _t1335
    _t1336 = Proto.Var(name=symbol714)
    _t1337 = Proto.Binding(var=_t1336, var"#type"=type715)
    result717 = _t1337
    record_span!(parser, span_start716, "Binding")
    return result717
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start733 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1338 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1339 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1340 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1341 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1342 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1343 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1344 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1345 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1346 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1347 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1348 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1349 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1350 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1351 = 9
                                                        else
                                                            _t1351 = -1
                                                        end
                                                        _t1350 = _t1351
                                                    end
                                                    _t1349 = _t1350
                                                end
                                                _t1348 = _t1349
                                            end
                                            _t1347 = _t1348
                                        end
                                        _t1346 = _t1347
                                    end
                                    _t1345 = _t1346
                                end
                                _t1344 = _t1345
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
    prediction718 = _t1338
    if prediction718 == 13
        _t1353 = parse_uint32_type(parser)
        uint32_type732 = _t1353
        _t1354 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type732))
        _t1352 = _t1354
    else
        if prediction718 == 12
            _t1356 = parse_float32_type(parser)
            float32_type731 = _t1356
            _t1357 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type731))
            _t1355 = _t1357
        else
            if prediction718 == 11
                _t1359 = parse_int32_type(parser)
                int32_type730 = _t1359
                _t1360 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type730))
                _t1358 = _t1360
            else
                if prediction718 == 10
                    _t1362 = parse_boolean_type(parser)
                    boolean_type729 = _t1362
                    _t1363 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type729))
                    _t1361 = _t1363
                else
                    if prediction718 == 9
                        _t1365 = parse_decimal_type(parser)
                        decimal_type728 = _t1365
                        _t1366 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type728))
                        _t1364 = _t1366
                    else
                        if prediction718 == 8
                            _t1368 = parse_missing_type(parser)
                            missing_type727 = _t1368
                            _t1369 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type727))
                            _t1367 = _t1369
                        else
                            if prediction718 == 7
                                _t1371 = parse_datetime_type(parser)
                                datetime_type726 = _t1371
                                _t1372 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type726))
                                _t1370 = _t1372
                            else
                                if prediction718 == 6
                                    _t1374 = parse_date_type(parser)
                                    date_type725 = _t1374
                                    _t1375 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type725))
                                    _t1373 = _t1375
                                else
                                    if prediction718 == 5
                                        _t1377 = parse_int128_type(parser)
                                        int128_type724 = _t1377
                                        _t1378 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type724))
                                        _t1376 = _t1378
                                    else
                                        if prediction718 == 4
                                            _t1380 = parse_uint128_type(parser)
                                            uint128_type723 = _t1380
                                            _t1381 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type723))
                                            _t1379 = _t1381
                                        else
                                            if prediction718 == 3
                                                _t1383 = parse_float_type(parser)
                                                float_type722 = _t1383
                                                _t1384 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type722))
                                                _t1382 = _t1384
                                            else
                                                if prediction718 == 2
                                                    _t1386 = parse_int_type(parser)
                                                    int_type721 = _t1386
                                                    _t1387 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type721))
                                                    _t1385 = _t1387
                                                else
                                                    if prediction718 == 1
                                                        _t1389 = parse_string_type(parser)
                                                        string_type720 = _t1389
                                                        _t1390 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type720))
                                                        _t1388 = _t1390
                                                    else
                                                        if prediction718 == 0
                                                            _t1392 = parse_unspecified_type(parser)
                                                            unspecified_type719 = _t1392
                                                            _t1393 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type719))
                                                            _t1391 = _t1393
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1388 = _t1391
                                                    end
                                                    _t1385 = _t1388
                                                end
                                                _t1382 = _t1385
                                            end
                                            _t1379 = _t1382
                                        end
                                        _t1376 = _t1379
                                    end
                                    _t1373 = _t1376
                                end
                                _t1370 = _t1373
                            end
                            _t1367 = _t1370
                        end
                        _t1364 = _t1367
                    end
                    _t1361 = _t1364
                end
                _t1358 = _t1361
            end
            _t1355 = _t1358
        end
        _t1352 = _t1355
    end
    result734 = _t1352
    record_span!(parser, span_start733, "Type")
    return result734
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start735 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1394 = Proto.UnspecifiedType()
    result736 = _t1394
    record_span!(parser, span_start735, "UnspecifiedType")
    return result736
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start737 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1395 = Proto.StringType()
    result738 = _t1395
    record_span!(parser, span_start737, "StringType")
    return result738
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start739 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1396 = Proto.IntType()
    result740 = _t1396
    record_span!(parser, span_start739, "IntType")
    return result740
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start741 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1397 = Proto.FloatType()
    result742 = _t1397
    record_span!(parser, span_start741, "FloatType")
    return result742
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start743 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1398 = Proto.UInt128Type()
    result744 = _t1398
    record_span!(parser, span_start743, "UInt128Type")
    return result744
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start745 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1399 = Proto.Int128Type()
    result746 = _t1399
    record_span!(parser, span_start745, "Int128Type")
    return result746
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start747 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1400 = Proto.DateType()
    result748 = _t1400
    record_span!(parser, span_start747, "DateType")
    return result748
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start749 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1401 = Proto.DateTimeType()
    result750 = _t1401
    record_span!(parser, span_start749, "DateTimeType")
    return result750
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start751 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1402 = Proto.MissingType()
    result752 = _t1402
    record_span!(parser, span_start751, "MissingType")
    return result752
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start755 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int753 = consume_terminal!(parser, "INT")
    int_3754 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1403 = Proto.DecimalType(precision=Int32(int753), scale=Int32(int_3754))
    result756 = _t1403
    record_span!(parser, span_start755, "DecimalType")
    return result756
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start757 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1404 = Proto.BooleanType()
    result758 = _t1404
    record_span!(parser, span_start757, "BooleanType")
    return result758
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start759 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1405 = Proto.Int32Type()
    result760 = _t1405
    record_span!(parser, span_start759, "Int32Type")
    return result760
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start761 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1406 = Proto.Float32Type()
    result762 = _t1406
    record_span!(parser, span_start761, "Float32Type")
    return result762
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start763 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1407 = Proto.UInt32Type()
    result764 = _t1407
    record_span!(parser, span_start763, "UInt32Type")
    return result764
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs765 = Proto.Binding[]
    cond766 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond766
        _t1408 = parse_binding(parser)
        item767 = _t1408
        push!(xs765, item767)
        cond766 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings768 = xs765
    return bindings768
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start783 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1410 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1411 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1412 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1413 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1414 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1415 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1416 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1417 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1418 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1419 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1420 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1421 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1422 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1423 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1424 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1425 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1426 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1427 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1428 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1429 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1430 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1431 = 10
                                                                                            else
                                                                                                _t1431 = -1
                                                                                            end
                                                                                            _t1430 = _t1431
                                                                                        end
                                                                                        _t1429 = _t1430
                                                                                    end
                                                                                    _t1428 = _t1429
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
                                        end
                                        _t1417 = _t1418
                                    end
                                    _t1416 = _t1417
                                end
                                _t1415 = _t1416
                            end
                            _t1414 = _t1415
                        end
                        _t1413 = _t1414
                    end
                    _t1412 = _t1413
                end
                _t1411 = _t1412
            end
            _t1410 = _t1411
        end
        _t1409 = _t1410
    else
        _t1409 = -1
    end
    prediction769 = _t1409
    if prediction769 == 12
        _t1433 = parse_cast(parser)
        cast782 = _t1433
        _t1434 = Proto.Formula(formula_type=OneOf(:cast, cast782))
        _t1432 = _t1434
    else
        if prediction769 == 11
            _t1436 = parse_rel_atom(parser)
            rel_atom781 = _t1436
            _t1437 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom781))
            _t1435 = _t1437
        else
            if prediction769 == 10
                _t1439 = parse_primitive(parser)
                primitive780 = _t1439
                _t1440 = Proto.Formula(formula_type=OneOf(:primitive, primitive780))
                _t1438 = _t1440
            else
                if prediction769 == 9
                    _t1442 = parse_pragma(parser)
                    pragma779 = _t1442
                    _t1443 = Proto.Formula(formula_type=OneOf(:pragma, pragma779))
                    _t1441 = _t1443
                else
                    if prediction769 == 8
                        _t1445 = parse_atom(parser)
                        atom778 = _t1445
                        _t1446 = Proto.Formula(formula_type=OneOf(:atom, atom778))
                        _t1444 = _t1446
                    else
                        if prediction769 == 7
                            _t1448 = parse_ffi(parser)
                            ffi777 = _t1448
                            _t1449 = Proto.Formula(formula_type=OneOf(:ffi, ffi777))
                            _t1447 = _t1449
                        else
                            if prediction769 == 6
                                _t1451 = parse_not(parser)
                                not776 = _t1451
                                _t1452 = Proto.Formula(formula_type=OneOf(:not, not776))
                                _t1450 = _t1452
                            else
                                if prediction769 == 5
                                    _t1454 = parse_disjunction(parser)
                                    disjunction775 = _t1454
                                    _t1455 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction775))
                                    _t1453 = _t1455
                                else
                                    if prediction769 == 4
                                        _t1457 = parse_conjunction(parser)
                                        conjunction774 = _t1457
                                        _t1458 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction774))
                                        _t1456 = _t1458
                                    else
                                        if prediction769 == 3
                                            _t1460 = parse_reduce(parser)
                                            reduce773 = _t1460
                                            _t1461 = Proto.Formula(formula_type=OneOf(:reduce, reduce773))
                                            _t1459 = _t1461
                                        else
                                            if prediction769 == 2
                                                _t1463 = parse_exists(parser)
                                                exists772 = _t1463
                                                _t1464 = Proto.Formula(formula_type=OneOf(:exists, exists772))
                                                _t1462 = _t1464
                                            else
                                                if prediction769 == 1
                                                    _t1466 = parse_false(parser)
                                                    false771 = _t1466
                                                    _t1467 = Proto.Formula(formula_type=OneOf(:disjunction, false771))
                                                    _t1465 = _t1467
                                                else
                                                    if prediction769 == 0
                                                        _t1469 = parse_true(parser)
                                                        true770 = _t1469
                                                        _t1470 = Proto.Formula(formula_type=OneOf(:conjunction, true770))
                                                        _t1468 = _t1470
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
                    _t1441 = _t1444
                end
                _t1438 = _t1441
            end
            _t1435 = _t1438
        end
        _t1432 = _t1435
    end
    result784 = _t1432
    record_span!(parser, span_start783, "Formula")
    return result784
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start785 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1471 = Proto.Conjunction(args=Proto.Formula[])
    result786 = _t1471
    record_span!(parser, span_start785, "Conjunction")
    return result786
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start787 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1472 = Proto.Disjunction(args=Proto.Formula[])
    result788 = _t1472
    record_span!(parser, span_start787, "Disjunction")
    return result788
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start791 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1473 = parse_bindings(parser)
    bindings789 = _t1473
    _t1474 = parse_formula(parser)
    formula790 = _t1474
    consume_literal!(parser, ")")
    _t1475 = Proto.Abstraction(vars=vcat(bindings789[1], !isnothing(bindings789[2]) ? bindings789[2] : []), value=formula790)
    _t1476 = Proto.Exists(body=_t1475)
    result792 = _t1476
    record_span!(parser, span_start791, "Exists")
    return result792
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start796 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1477 = parse_abstraction(parser)
    abstraction793 = _t1477
    _t1478 = parse_abstraction(parser)
    abstraction_3794 = _t1478
    _t1479 = parse_terms(parser)
    terms795 = _t1479
    consume_literal!(parser, ")")
    _t1480 = Proto.Reduce(op=abstraction793, body=abstraction_3794, terms=terms795)
    result797 = _t1480
    record_span!(parser, span_start796, "Reduce")
    return result797
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs798 = Proto.Term[]
    cond799 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond799
        _t1481 = parse_term(parser)
        item800 = _t1481
        push!(xs798, item800)
        cond799 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms801 = xs798
    consume_literal!(parser, ")")
    return terms801
end

function parse_term(parser::ParserState)::Proto.Term
    span_start805 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1482 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1483 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1484 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1485 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1486 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1487 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1488 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1489 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1490 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1491 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1492 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1493 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1494 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1495 = 1
                                                        else
                                                            _t1495 = -1
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
                                end
                                _t1488 = _t1489
                            end
                            _t1487 = _t1488
                        end
                        _t1486 = _t1487
                    end
                    _t1485 = _t1486
                end
                _t1484 = _t1485
            end
            _t1483 = _t1484
        end
        _t1482 = _t1483
    end
    prediction802 = _t1482
    if prediction802 == 1
        _t1497 = parse_value(parser)
        value804 = _t1497
        _t1498 = Proto.Term(term_type=OneOf(:constant, value804))
        _t1496 = _t1498
    else
        if prediction802 == 0
            _t1500 = parse_var(parser)
            var803 = _t1500
            _t1501 = Proto.Term(term_type=OneOf(:var, var803))
            _t1499 = _t1501
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1496 = _t1499
    end
    result806 = _t1496
    record_span!(parser, span_start805, "Term")
    return result806
end

function parse_var(parser::ParserState)::Proto.Var
    span_start808 = span_start(parser)
    symbol807 = consume_terminal!(parser, "SYMBOL")
    _t1502 = Proto.Var(name=symbol807)
    result809 = _t1502
    record_span!(parser, span_start808, "Var")
    return result809
end

function parse_value(parser::ParserState)::Proto.Value
    span_start823 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1503 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1504 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1505 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1507 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1508 = 0
                        else
                            _t1508 = -1
                        end
                        _t1507 = _t1508
                    end
                    _t1506 = _t1507
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1509 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1510 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1511 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1512 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1513 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1514 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1515 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1516 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1517 = 10
                                                    else
                                                        _t1517 = -1
                                                    end
                                                    _t1516 = _t1517
                                                end
                                                _t1515 = _t1516
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
                    _t1506 = _t1509
                end
                _t1505 = _t1506
            end
            _t1504 = _t1505
        end
        _t1503 = _t1504
    end
    prediction810 = _t1503
    if prediction810 == 12
        _t1519 = parse_boolean_value(parser)
        boolean_value822 = _t1519
        _t1520 = Proto.Value(value=OneOf(:boolean_value, boolean_value822))
        _t1518 = _t1520
    else
        if prediction810 == 11
            consume_literal!(parser, "missing")
            _t1522 = Proto.MissingValue()
            _t1523 = Proto.Value(value=OneOf(:missing_value, _t1522))
            _t1521 = _t1523
        else
            if prediction810 == 10
                formatted_decimal821 = consume_terminal!(parser, "DECIMAL")
                _t1525 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal821))
                _t1524 = _t1525
            else
                if prediction810 == 9
                    formatted_int128820 = consume_terminal!(parser, "INT128")
                    _t1527 = Proto.Value(value=OneOf(:int128_value, formatted_int128820))
                    _t1526 = _t1527
                else
                    if prediction810 == 8
                        formatted_uint128819 = consume_terminal!(parser, "UINT128")
                        _t1529 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128819))
                        _t1528 = _t1529
                    else
                        if prediction810 == 7
                            formatted_uint32818 = consume_terminal!(parser, "UINT32")
                            _t1531 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32818))
                            _t1530 = _t1531
                        else
                            if prediction810 == 6
                                formatted_float817 = consume_terminal!(parser, "FLOAT")
                                _t1533 = Proto.Value(value=OneOf(:float_value, formatted_float817))
                                _t1532 = _t1533
                            else
                                if prediction810 == 5
                                    formatted_float32816 = consume_terminal!(parser, "FLOAT32")
                                    _t1535 = Proto.Value(value=OneOf(:float32_value, formatted_float32816))
                                    _t1534 = _t1535
                                else
                                    if prediction810 == 4
                                        formatted_int815 = consume_terminal!(parser, "INT")
                                        _t1537 = Proto.Value(value=OneOf(:int_value, formatted_int815))
                                        _t1536 = _t1537
                                    else
                                        if prediction810 == 3
                                            formatted_int32814 = consume_terminal!(parser, "INT32")
                                            _t1539 = Proto.Value(value=OneOf(:int32_value, formatted_int32814))
                                            _t1538 = _t1539
                                        else
                                            if prediction810 == 2
                                                formatted_string813 = consume_terminal!(parser, "STRING")
                                                _t1541 = Proto.Value(value=OneOf(:string_value, formatted_string813))
                                                _t1540 = _t1541
                                            else
                                                if prediction810 == 1
                                                    _t1543 = parse_datetime(parser)
                                                    datetime812 = _t1543
                                                    _t1544 = Proto.Value(value=OneOf(:datetime_value, datetime812))
                                                    _t1542 = _t1544
                                                else
                                                    if prediction810 == 0
                                                        _t1546 = parse_date(parser)
                                                        date811 = _t1546
                                                        _t1547 = Proto.Value(value=OneOf(:date_value, date811))
                                                        _t1545 = _t1547
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1542 = _t1545
                                                end
                                                _t1540 = _t1542
                                            end
                                            _t1538 = _t1540
                                        end
                                        _t1536 = _t1538
                                    end
                                    _t1534 = _t1536
                                end
                                _t1532 = _t1534
                            end
                            _t1530 = _t1532
                        end
                        _t1528 = _t1530
                    end
                    _t1526 = _t1528
                end
                _t1524 = _t1526
            end
            _t1521 = _t1524
        end
        _t1518 = _t1521
    end
    result824 = _t1518
    record_span!(parser, span_start823, "Value")
    return result824
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start828 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int825 = consume_terminal!(parser, "INT")
    formatted_int_3826 = consume_terminal!(parser, "INT")
    formatted_int_4827 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1548 = Proto.DateValue(year=Int32(formatted_int825), month=Int32(formatted_int_3826), day=Int32(formatted_int_4827))
    result829 = _t1548
    record_span!(parser, span_start828, "DateValue")
    return result829
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start837 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int830 = consume_terminal!(parser, "INT")
    formatted_int_3831 = consume_terminal!(parser, "INT")
    formatted_int_4832 = consume_terminal!(parser, "INT")
    formatted_int_5833 = consume_terminal!(parser, "INT")
    formatted_int_6834 = consume_terminal!(parser, "INT")
    formatted_int_7835 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1549 = consume_terminal!(parser, "INT")
    else
        _t1549 = nothing
    end
    formatted_int_8836 = _t1549
    consume_literal!(parser, ")")
    _t1550 = Proto.DateTimeValue(year=Int32(formatted_int830), month=Int32(formatted_int_3831), day=Int32(formatted_int_4832), hour=Int32(formatted_int_5833), minute=Int32(formatted_int_6834), second=Int32(formatted_int_7835), microsecond=Int32((!isnothing(formatted_int_8836) ? formatted_int_8836 : 0)))
    result838 = _t1550
    record_span!(parser, span_start837, "DateTimeValue")
    return result838
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start843 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs839 = Proto.Formula[]
    cond840 = match_lookahead_literal(parser, "(", 0)
    while cond840
        _t1551 = parse_formula(parser)
        item841 = _t1551
        push!(xs839, item841)
        cond840 = match_lookahead_literal(parser, "(", 0)
    end
    formulas842 = xs839
    consume_literal!(parser, ")")
    _t1552 = Proto.Conjunction(args=formulas842)
    result844 = _t1552
    record_span!(parser, span_start843, "Conjunction")
    return result844
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start849 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs845 = Proto.Formula[]
    cond846 = match_lookahead_literal(parser, "(", 0)
    while cond846
        _t1553 = parse_formula(parser)
        item847 = _t1553
        push!(xs845, item847)
        cond846 = match_lookahead_literal(parser, "(", 0)
    end
    formulas848 = xs845
    consume_literal!(parser, ")")
    _t1554 = Proto.Disjunction(args=formulas848)
    result850 = _t1554
    record_span!(parser, span_start849, "Disjunction")
    return result850
end

function parse_not(parser::ParserState)::Proto.Not
    span_start852 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1555 = parse_formula(parser)
    formula851 = _t1555
    consume_literal!(parser, ")")
    _t1556 = Proto.Not(arg=formula851)
    result853 = _t1556
    record_span!(parser, span_start852, "Not")
    return result853
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start857 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1557 = parse_name(parser)
    name854 = _t1557
    _t1558 = parse_ffi_args(parser)
    ffi_args855 = _t1558
    _t1559 = parse_terms(parser)
    terms856 = _t1559
    consume_literal!(parser, ")")
    _t1560 = Proto.FFI(name=name854, args=ffi_args855, terms=terms856)
    result858 = _t1560
    record_span!(parser, span_start857, "FFI")
    return result858
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol859 = consume_terminal!(parser, "SYMBOL")
    return symbol859
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs860 = Proto.Abstraction[]
    cond861 = match_lookahead_literal(parser, "(", 0)
    while cond861
        _t1561 = parse_abstraction(parser)
        item862 = _t1561
        push!(xs860, item862)
        cond861 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions863 = xs860
    consume_literal!(parser, ")")
    return abstractions863
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start869 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1562 = parse_relation_id(parser)
    relation_id864 = _t1562
    xs865 = Proto.Term[]
    cond866 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond866
        _t1563 = parse_term(parser)
        item867 = _t1563
        push!(xs865, item867)
        cond866 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms868 = xs865
    consume_literal!(parser, ")")
    _t1564 = Proto.Atom(name=relation_id864, terms=terms868)
    result870 = _t1564
    record_span!(parser, span_start869, "Atom")
    return result870
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start876 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1565 = parse_name(parser)
    name871 = _t1565
    xs872 = Proto.Term[]
    cond873 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond873
        _t1566 = parse_term(parser)
        item874 = _t1566
        push!(xs872, item874)
        cond873 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms875 = xs872
    consume_literal!(parser, ")")
    _t1567 = Proto.Pragma(name=name871, terms=terms875)
    result877 = _t1567
    record_span!(parser, span_start876, "Pragma")
    return result877
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start893 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1569 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1570 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1571 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1572 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1573 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1574 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1575 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1576 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1577 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1578 = 7
                                            else
                                                _t1578 = -1
                                            end
                                            _t1577 = _t1578
                                        end
                                        _t1576 = _t1577
                                    end
                                    _t1575 = _t1576
                                end
                                _t1574 = _t1575
                            end
                            _t1573 = _t1574
                        end
                        _t1572 = _t1573
                    end
                    _t1571 = _t1572
                end
                _t1570 = _t1571
            end
            _t1569 = _t1570
        end
        _t1568 = _t1569
    else
        _t1568 = -1
    end
    prediction878 = _t1568
    if prediction878 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1580 = parse_name(parser)
        name888 = _t1580
        xs889 = Proto.RelTerm[]
        cond890 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond890
            _t1581 = parse_rel_term(parser)
            item891 = _t1581
            push!(xs889, item891)
            cond890 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms892 = xs889
        consume_literal!(parser, ")")
        _t1582 = Proto.Primitive(name=name888, terms=rel_terms892)
        _t1579 = _t1582
    else
        if prediction878 == 8
            _t1584 = parse_divide(parser)
            divide887 = _t1584
            _t1583 = divide887
        else
            if prediction878 == 7
                _t1586 = parse_multiply(parser)
                multiply886 = _t1586
                _t1585 = multiply886
            else
                if prediction878 == 6
                    _t1588 = parse_minus(parser)
                    minus885 = _t1588
                    _t1587 = minus885
                else
                    if prediction878 == 5
                        _t1590 = parse_add(parser)
                        add884 = _t1590
                        _t1589 = add884
                    else
                        if prediction878 == 4
                            _t1592 = parse_gt_eq(parser)
                            gt_eq883 = _t1592
                            _t1591 = gt_eq883
                        else
                            if prediction878 == 3
                                _t1594 = parse_gt(parser)
                                gt882 = _t1594
                                _t1593 = gt882
                            else
                                if prediction878 == 2
                                    _t1596 = parse_lt_eq(parser)
                                    lt_eq881 = _t1596
                                    _t1595 = lt_eq881
                                else
                                    if prediction878 == 1
                                        _t1598 = parse_lt(parser)
                                        lt880 = _t1598
                                        _t1597 = lt880
                                    else
                                        if prediction878 == 0
                                            _t1600 = parse_eq(parser)
                                            eq879 = _t1600
                                            _t1599 = eq879
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1597 = _t1599
                                    end
                                    _t1595 = _t1597
                                end
                                _t1593 = _t1595
                            end
                            _t1591 = _t1593
                        end
                        _t1589 = _t1591
                    end
                    _t1587 = _t1589
                end
                _t1585 = _t1587
            end
            _t1583 = _t1585
        end
        _t1579 = _t1583
    end
    result894 = _t1579
    record_span!(parser, span_start893, "Primitive")
    return result894
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start897 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1601 = parse_term(parser)
    term895 = _t1601
    _t1602 = parse_term(parser)
    term_3896 = _t1602
    consume_literal!(parser, ")")
    _t1603 = Proto.RelTerm(rel_term_type=OneOf(:term, term895))
    _t1604 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3896))
    _t1605 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1603, _t1604])
    result898 = _t1605
    record_span!(parser, span_start897, "Primitive")
    return result898
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start901 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1606 = parse_term(parser)
    term899 = _t1606
    _t1607 = parse_term(parser)
    term_3900 = _t1607
    consume_literal!(parser, ")")
    _t1608 = Proto.RelTerm(rel_term_type=OneOf(:term, term899))
    _t1609 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3900))
    _t1610 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1608, _t1609])
    result902 = _t1610
    record_span!(parser, span_start901, "Primitive")
    return result902
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start905 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1611 = parse_term(parser)
    term903 = _t1611
    _t1612 = parse_term(parser)
    term_3904 = _t1612
    consume_literal!(parser, ")")
    _t1613 = Proto.RelTerm(rel_term_type=OneOf(:term, term903))
    _t1614 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3904))
    _t1615 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1613, _t1614])
    result906 = _t1615
    record_span!(parser, span_start905, "Primitive")
    return result906
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start909 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1616 = parse_term(parser)
    term907 = _t1616
    _t1617 = parse_term(parser)
    term_3908 = _t1617
    consume_literal!(parser, ")")
    _t1618 = Proto.RelTerm(rel_term_type=OneOf(:term, term907))
    _t1619 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3908))
    _t1620 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1618, _t1619])
    result910 = _t1620
    record_span!(parser, span_start909, "Primitive")
    return result910
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start913 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1621 = parse_term(parser)
    term911 = _t1621
    _t1622 = parse_term(parser)
    term_3912 = _t1622
    consume_literal!(parser, ")")
    _t1623 = Proto.RelTerm(rel_term_type=OneOf(:term, term911))
    _t1624 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3912))
    _t1625 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1623, _t1624])
    result914 = _t1625
    record_span!(parser, span_start913, "Primitive")
    return result914
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start918 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1626 = parse_term(parser)
    term915 = _t1626
    _t1627 = parse_term(parser)
    term_3916 = _t1627
    _t1628 = parse_term(parser)
    term_4917 = _t1628
    consume_literal!(parser, ")")
    _t1629 = Proto.RelTerm(rel_term_type=OneOf(:term, term915))
    _t1630 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3916))
    _t1631 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4917))
    _t1632 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1629, _t1630, _t1631])
    result919 = _t1632
    record_span!(parser, span_start918, "Primitive")
    return result919
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start923 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1633 = parse_term(parser)
    term920 = _t1633
    _t1634 = parse_term(parser)
    term_3921 = _t1634
    _t1635 = parse_term(parser)
    term_4922 = _t1635
    consume_literal!(parser, ")")
    _t1636 = Proto.RelTerm(rel_term_type=OneOf(:term, term920))
    _t1637 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3921))
    _t1638 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4922))
    _t1639 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1636, _t1637, _t1638])
    result924 = _t1639
    record_span!(parser, span_start923, "Primitive")
    return result924
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start928 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1640 = parse_term(parser)
    term925 = _t1640
    _t1641 = parse_term(parser)
    term_3926 = _t1641
    _t1642 = parse_term(parser)
    term_4927 = _t1642
    consume_literal!(parser, ")")
    _t1643 = Proto.RelTerm(rel_term_type=OneOf(:term, term925))
    _t1644 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3926))
    _t1645 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4927))
    _t1646 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1643, _t1644, _t1645])
    result929 = _t1646
    record_span!(parser, span_start928, "Primitive")
    return result929
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start933 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1647 = parse_term(parser)
    term930 = _t1647
    _t1648 = parse_term(parser)
    term_3931 = _t1648
    _t1649 = parse_term(parser)
    term_4932 = _t1649
    consume_literal!(parser, ")")
    _t1650 = Proto.RelTerm(rel_term_type=OneOf(:term, term930))
    _t1651 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3931))
    _t1652 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4932))
    _t1653 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1650, _t1651, _t1652])
    result934 = _t1653
    record_span!(parser, span_start933, "Primitive")
    return result934
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start938 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1654 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1655 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1656 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1657 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1658 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1659 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1660 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1661 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1662 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1663 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1664 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1665 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1666 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1667 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1668 = 1
                                                            else
                                                                _t1668 = -1
                                                            end
                                                            _t1667 = _t1668
                                                        end
                                                        _t1666 = _t1667
                                                    end
                                                    _t1665 = _t1666
                                                end
                                                _t1664 = _t1665
                                            end
                                            _t1663 = _t1664
                                        end
                                        _t1662 = _t1663
                                    end
                                    _t1661 = _t1662
                                end
                                _t1660 = _t1661
                            end
                            _t1659 = _t1660
                        end
                        _t1658 = _t1659
                    end
                    _t1657 = _t1658
                end
                _t1656 = _t1657
            end
            _t1655 = _t1656
        end
        _t1654 = _t1655
    end
    prediction935 = _t1654
    if prediction935 == 1
        _t1670 = parse_term(parser)
        term937 = _t1670
        _t1671 = Proto.RelTerm(rel_term_type=OneOf(:term, term937))
        _t1669 = _t1671
    else
        if prediction935 == 0
            _t1673 = parse_specialized_value(parser)
            specialized_value936 = _t1673
            _t1674 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value936))
            _t1672 = _t1674
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1669 = _t1672
    end
    result939 = _t1669
    record_span!(parser, span_start938, "RelTerm")
    return result939
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start941 = span_start(parser)
    consume_literal!(parser, "#")
    _t1675 = parse_raw_value(parser)
    raw_value940 = _t1675
    result942 = raw_value940
    record_span!(parser, span_start941, "Value")
    return result942
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start948 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1676 = parse_name(parser)
    name943 = _t1676
    xs944 = Proto.RelTerm[]
    cond945 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond945
        _t1677 = parse_rel_term(parser)
        item946 = _t1677
        push!(xs944, item946)
        cond945 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms947 = xs944
    consume_literal!(parser, ")")
    _t1678 = Proto.RelAtom(name=name943, terms=rel_terms947)
    result949 = _t1678
    record_span!(parser, span_start948, "RelAtom")
    return result949
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1679 = parse_term(parser)
    term950 = _t1679
    _t1680 = parse_term(parser)
    term_3951 = _t1680
    consume_literal!(parser, ")")
    _t1681 = Proto.Cast(input=term950, result=term_3951)
    result953 = _t1681
    record_span!(parser, span_start952, "Cast")
    return result953
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs954 = Proto.Attribute[]
    cond955 = match_lookahead_literal(parser, "(", 0)
    while cond955
        _t1682 = parse_attribute(parser)
        item956 = _t1682
        push!(xs954, item956)
        cond955 = match_lookahead_literal(parser, "(", 0)
    end
    attributes957 = xs954
    consume_literal!(parser, ")")
    return attributes957
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start963 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1683 = parse_name(parser)
    name958 = _t1683
    xs959 = Proto.Value[]
    cond960 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond960
        _t1684 = parse_raw_value(parser)
        item961 = _t1684
        push!(xs959, item961)
        cond960 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values962 = xs959
    consume_literal!(parser, ")")
    _t1685 = Proto.Attribute(name=name958, args=raw_values962)
    result964 = _t1685
    record_span!(parser, span_start963, "Attribute")
    return result964
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start970 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs965 = Proto.RelationId[]
    cond966 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond966
        _t1686 = parse_relation_id(parser)
        item967 = _t1686
        push!(xs965, item967)
        cond966 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids968 = xs965
    _t1687 = parse_script(parser)
    script969 = _t1687
    consume_literal!(parser, ")")
    _t1688 = Proto.Algorithm(var"#global"=relation_ids968, body=script969)
    result971 = _t1688
    record_span!(parser, span_start970, "Algorithm")
    return result971
end

function parse_script(parser::ParserState)::Proto.Script
    span_start976 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs972 = Proto.Construct[]
    cond973 = match_lookahead_literal(parser, "(", 0)
    while cond973
        _t1689 = parse_construct(parser)
        item974 = _t1689
        push!(xs972, item974)
        cond973 = match_lookahead_literal(parser, "(", 0)
    end
    constructs975 = xs972
    consume_literal!(parser, ")")
    _t1690 = Proto.Script(constructs=constructs975)
    result977 = _t1690
    record_span!(parser, span_start976, "Script")
    return result977
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start981 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1692 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1693 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1694 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1695 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1696 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1697 = 1
                            else
                                _t1697 = -1
                            end
                            _t1696 = _t1697
                        end
                        _t1695 = _t1696
                    end
                    _t1694 = _t1695
                end
                _t1693 = _t1694
            end
            _t1692 = _t1693
        end
        _t1691 = _t1692
    else
        _t1691 = -1
    end
    prediction978 = _t1691
    if prediction978 == 1
        _t1699 = parse_instruction(parser)
        instruction980 = _t1699
        _t1700 = Proto.Construct(construct_type=OneOf(:instruction, instruction980))
        _t1698 = _t1700
    else
        if prediction978 == 0
            _t1702 = parse_loop(parser)
            loop979 = _t1702
            _t1703 = Proto.Construct(construct_type=OneOf(:loop, loop979))
            _t1701 = _t1703
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1698 = _t1701
    end
    result982 = _t1698
    record_span!(parser, span_start981, "Construct")
    return result982
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start985 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1704 = parse_init(parser)
    init983 = _t1704
    _t1705 = parse_script(parser)
    script984 = _t1705
    consume_literal!(parser, ")")
    _t1706 = Proto.Loop(init=init983, body=script984)
    result986 = _t1706
    record_span!(parser, span_start985, "Loop")
    return result986
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs987 = Proto.Instruction[]
    cond988 = match_lookahead_literal(parser, "(", 0)
    while cond988
        _t1707 = parse_instruction(parser)
        item989 = _t1707
        push!(xs987, item989)
        cond988 = match_lookahead_literal(parser, "(", 0)
    end
    instructions990 = xs987
    consume_literal!(parser, ")")
    return instructions990
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start997 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1709 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1710 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1711 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1712 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1713 = 0
                        else
                            _t1713 = -1
                        end
                        _t1712 = _t1713
                    end
                    _t1711 = _t1712
                end
                _t1710 = _t1711
            end
            _t1709 = _t1710
        end
        _t1708 = _t1709
    else
        _t1708 = -1
    end
    prediction991 = _t1708
    if prediction991 == 4
        _t1715 = parse_monus_def(parser)
        monus_def996 = _t1715
        _t1716 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def996))
        _t1714 = _t1716
    else
        if prediction991 == 3
            _t1718 = parse_monoid_def(parser)
            monoid_def995 = _t1718
            _t1719 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def995))
            _t1717 = _t1719
        else
            if prediction991 == 2
                _t1721 = parse_break(parser)
                break994 = _t1721
                _t1722 = Proto.Instruction(instr_type=OneOf(:var"#break", break994))
                _t1720 = _t1722
            else
                if prediction991 == 1
                    _t1724 = parse_upsert(parser)
                    upsert993 = _t1724
                    _t1725 = Proto.Instruction(instr_type=OneOf(:upsert, upsert993))
                    _t1723 = _t1725
                else
                    if prediction991 == 0
                        _t1727 = parse_assign(parser)
                        assign992 = _t1727
                        _t1728 = Proto.Instruction(instr_type=OneOf(:assign, assign992))
                        _t1726 = _t1728
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1723 = _t1726
                end
                _t1720 = _t1723
            end
            _t1717 = _t1720
        end
        _t1714 = _t1717
    end
    result998 = _t1714
    record_span!(parser, span_start997, "Instruction")
    return result998
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1002 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1729 = parse_relation_id(parser)
    relation_id999 = _t1729
    _t1730 = parse_abstraction(parser)
    abstraction1000 = _t1730
    if match_lookahead_literal(parser, "(", 0)
        _t1732 = parse_attrs(parser)
        _t1731 = _t1732
    else
        _t1731 = nothing
    end
    attrs1001 = _t1731
    consume_literal!(parser, ")")
    _t1733 = Proto.Assign(name=relation_id999, body=abstraction1000, attrs=(!isnothing(attrs1001) ? attrs1001 : Proto.Attribute[]))
    result1003 = _t1733
    record_span!(parser, span_start1002, "Assign")
    return result1003
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1007 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1734 = parse_relation_id(parser)
    relation_id1004 = _t1734
    _t1735 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1005 = _t1735
    if match_lookahead_literal(parser, "(", 0)
        _t1737 = parse_attrs(parser)
        _t1736 = _t1737
    else
        _t1736 = nothing
    end
    attrs1006 = _t1736
    consume_literal!(parser, ")")
    _t1738 = Proto.Upsert(name=relation_id1004, body=abstraction_with_arity1005[1], attrs=(!isnothing(attrs1006) ? attrs1006 : Proto.Attribute[]), value_arity=abstraction_with_arity1005[2])
    result1008 = _t1738
    record_span!(parser, span_start1007, "Upsert")
    return result1008
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1739 = parse_bindings(parser)
    bindings1009 = _t1739
    _t1740 = parse_formula(parser)
    formula1010 = _t1740
    consume_literal!(parser, ")")
    _t1741 = Proto.Abstraction(vars=vcat(bindings1009[1], !isnothing(bindings1009[2]) ? bindings1009[2] : []), value=formula1010)
    return (_t1741, length(bindings1009[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1014 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1742 = parse_relation_id(parser)
    relation_id1011 = _t1742
    _t1743 = parse_abstraction(parser)
    abstraction1012 = _t1743
    if match_lookahead_literal(parser, "(", 0)
        _t1745 = parse_attrs(parser)
        _t1744 = _t1745
    else
        _t1744 = nothing
    end
    attrs1013 = _t1744
    consume_literal!(parser, ")")
    _t1746 = Proto.Break(name=relation_id1011, body=abstraction1012, attrs=(!isnothing(attrs1013) ? attrs1013 : Proto.Attribute[]))
    result1015 = _t1746
    record_span!(parser, span_start1014, "Break")
    return result1015
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1020 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1747 = parse_monoid(parser)
    monoid1016 = _t1747
    _t1748 = parse_relation_id(parser)
    relation_id1017 = _t1748
    _t1749 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1018 = _t1749
    if match_lookahead_literal(parser, "(", 0)
        _t1751 = parse_attrs(parser)
        _t1750 = _t1751
    else
        _t1750 = nothing
    end
    attrs1019 = _t1750
    consume_literal!(parser, ")")
    _t1752 = Proto.MonoidDef(monoid=monoid1016, name=relation_id1017, body=abstraction_with_arity1018[1], attrs=(!isnothing(attrs1019) ? attrs1019 : Proto.Attribute[]), value_arity=abstraction_with_arity1018[2])
    result1021 = _t1752
    record_span!(parser, span_start1020, "MonoidDef")
    return result1021
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1027 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1754 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1755 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1756 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1757 = 2
                    else
                        _t1757 = -1
                    end
                    _t1756 = _t1757
                end
                _t1755 = _t1756
            end
            _t1754 = _t1755
        end
        _t1753 = _t1754
    else
        _t1753 = -1
    end
    prediction1022 = _t1753
    if prediction1022 == 3
        _t1759 = parse_sum_monoid(parser)
        sum_monoid1026 = _t1759
        _t1760 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1026))
        _t1758 = _t1760
    else
        if prediction1022 == 2
            _t1762 = parse_max_monoid(parser)
            max_monoid1025 = _t1762
            _t1763 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1025))
            _t1761 = _t1763
        else
            if prediction1022 == 1
                _t1765 = parse_min_monoid(parser)
                min_monoid1024 = _t1765
                _t1766 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1024))
                _t1764 = _t1766
            else
                if prediction1022 == 0
                    _t1768 = parse_or_monoid(parser)
                    or_monoid1023 = _t1768
                    _t1769 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1023))
                    _t1767 = _t1769
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1764 = _t1767
            end
            _t1761 = _t1764
        end
        _t1758 = _t1761
    end
    result1028 = _t1758
    record_span!(parser, span_start1027, "Monoid")
    return result1028
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1029 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1770 = Proto.OrMonoid()
    result1030 = _t1770
    record_span!(parser, span_start1029, "OrMonoid")
    return result1030
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1032 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1771 = parse_type(parser)
    type1031 = _t1771
    consume_literal!(parser, ")")
    _t1772 = Proto.MinMonoid(var"#type"=type1031)
    result1033 = _t1772
    record_span!(parser, span_start1032, "MinMonoid")
    return result1033
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1035 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1773 = parse_type(parser)
    type1034 = _t1773
    consume_literal!(parser, ")")
    _t1774 = Proto.MaxMonoid(var"#type"=type1034)
    result1036 = _t1774
    record_span!(parser, span_start1035, "MaxMonoid")
    return result1036
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1038 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1775 = parse_type(parser)
    type1037 = _t1775
    consume_literal!(parser, ")")
    _t1776 = Proto.SumMonoid(var"#type"=type1037)
    result1039 = _t1776
    record_span!(parser, span_start1038, "SumMonoid")
    return result1039
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1044 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1777 = parse_monoid(parser)
    monoid1040 = _t1777
    _t1778 = parse_relation_id(parser)
    relation_id1041 = _t1778
    _t1779 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1042 = _t1779
    if match_lookahead_literal(parser, "(", 0)
        _t1781 = parse_attrs(parser)
        _t1780 = _t1781
    else
        _t1780 = nothing
    end
    attrs1043 = _t1780
    consume_literal!(parser, ")")
    _t1782 = Proto.MonusDef(monoid=monoid1040, name=relation_id1041, body=abstraction_with_arity1042[1], attrs=(!isnothing(attrs1043) ? attrs1043 : Proto.Attribute[]), value_arity=abstraction_with_arity1042[2])
    result1045 = _t1782
    record_span!(parser, span_start1044, "MonusDef")
    return result1045
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1050 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1783 = parse_relation_id(parser)
    relation_id1046 = _t1783
    _t1784 = parse_abstraction(parser)
    abstraction1047 = _t1784
    _t1785 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1048 = _t1785
    _t1786 = parse_functional_dependency_values(parser)
    functional_dependency_values1049 = _t1786
    consume_literal!(parser, ")")
    _t1787 = Proto.FunctionalDependency(guard=abstraction1047, keys=functional_dependency_keys1048, values=functional_dependency_values1049)
    _t1788 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1787), name=relation_id1046)
    result1051 = _t1788
    record_span!(parser, span_start1050, "Constraint")
    return result1051
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1052 = Proto.Var[]
    cond1053 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1053
        _t1789 = parse_var(parser)
        item1054 = _t1789
        push!(xs1052, item1054)
        cond1053 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1055 = xs1052
    consume_literal!(parser, ")")
    return vars1055
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1056 = Proto.Var[]
    cond1057 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1057
        _t1790 = parse_var(parser)
        item1058 = _t1790
        push!(xs1056, item1058)
        cond1057 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1059 = xs1056
    consume_literal!(parser, ")")
    return vars1059
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1064 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "edb", 1)
            _t1792 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1793 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1794 = 1
                else
                    _t1794 = -1
                end
                _t1793 = _t1794
            end
            _t1792 = _t1793
        end
        _t1791 = _t1792
    else
        _t1791 = -1
    end
    prediction1060 = _t1791
    if prediction1060 == 2
        _t1796 = parse_csv_data(parser)
        csv_data1063 = _t1796
        _t1797 = Proto.Data(data_type=OneOf(:csv_data, csv_data1063))
        _t1795 = _t1797
    else
        if prediction1060 == 1
            _t1799 = parse_betree_relation(parser)
            betree_relation1062 = _t1799
            _t1800 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1062))
            _t1798 = _t1800
        else
            if prediction1060 == 0
                _t1802 = parse_edb(parser)
                edb1061 = _t1802
                _t1803 = Proto.Data(data_type=OneOf(:edb, edb1061))
                _t1801 = _t1803
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1798 = _t1801
        end
        _t1795 = _t1798
    end
    result1065 = _t1795
    record_span!(parser, span_start1064, "Data")
    return result1065
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1069 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1804 = parse_relation_id(parser)
    relation_id1066 = _t1804
    _t1805 = parse_edb_path(parser)
    edb_path1067 = _t1805
    _t1806 = parse_edb_types(parser)
    edb_types1068 = _t1806
    consume_literal!(parser, ")")
    _t1807 = Proto.EDB(target_id=relation_id1066, path=edb_path1067, types=edb_types1068)
    result1070 = _t1807
    record_span!(parser, span_start1069, "EDB")
    return result1070
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1071 = String[]
    cond1072 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1072
        item1073 = consume_terminal!(parser, "STRING")
        push!(xs1071, item1073)
        cond1072 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1074 = xs1071
    consume_literal!(parser, "]")
    return strings1074
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1075 = Proto.var"#Type"[]
    cond1076 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1076
        _t1808 = parse_type(parser)
        item1077 = _t1808
        push!(xs1075, item1077)
        cond1076 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1078 = xs1075
    consume_literal!(parser, "]")
    return types1078
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1081 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1809 = parse_relation_id(parser)
    relation_id1079 = _t1809
    _t1810 = parse_betree_info(parser)
    betree_info1080 = _t1810
    consume_literal!(parser, ")")
    _t1811 = Proto.BeTreeRelation(name=relation_id1079, relation_info=betree_info1080)
    result1082 = _t1811
    record_span!(parser, span_start1081, "BeTreeRelation")
    return result1082
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1086 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1812 = parse_betree_info_key_types(parser)
    betree_info_key_types1083 = _t1812
    _t1813 = parse_betree_info_value_types(parser)
    betree_info_value_types1084 = _t1813
    _t1814 = parse_config_dict(parser)
    config_dict1085 = _t1814
    consume_literal!(parser, ")")
    _t1815 = construct_betree_info(parser, betree_info_key_types1083, betree_info_value_types1084, config_dict1085)
    result1087 = _t1815
    record_span!(parser, span_start1086, "BeTreeInfo")
    return result1087
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1088 = Proto.var"#Type"[]
    cond1089 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1089
        _t1816 = parse_type(parser)
        item1090 = _t1816
        push!(xs1088, item1090)
        cond1089 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1091 = xs1088
    consume_literal!(parser, ")")
    return types1091
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1092 = Proto.var"#Type"[]
    cond1093 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1093
        _t1817 = parse_type(parser)
        item1094 = _t1817
        push!(xs1092, item1094)
        cond1093 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1095 = xs1092
    consume_literal!(parser, ")")
    return types1095
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1100 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1818 = parse_csvlocator(parser)
    csvlocator1096 = _t1818
    _t1819 = parse_csv_config(parser)
    csv_config1097 = _t1819
    _t1820 = parse_gnf_columns(parser)
    gnf_columns1098 = _t1820
    _t1821 = parse_csv_asof(parser)
    csv_asof1099 = _t1821
    consume_literal!(parser, ")")
    _t1822 = Proto.CSVData(locator=csvlocator1096, config=csv_config1097, columns=gnf_columns1098, asof=csv_asof1099)
    result1101 = _t1822
    record_span!(parser, span_start1100, "CSVData")
    return result1101
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1104 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1824 = parse_csv_locator_paths(parser)
        _t1823 = _t1824
    else
        _t1823 = nothing
    end
    csv_locator_paths1102 = _t1823
    if match_lookahead_literal(parser, "(", 0)
        _t1826 = parse_csv_locator_inline_data(parser)
        _t1825 = _t1826
    else
        _t1825 = nothing
    end
    csv_locator_inline_data1103 = _t1825
    consume_literal!(parser, ")")
    _t1827 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1102) ? csv_locator_paths1102 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1103) ? csv_locator_inline_data1103 : "")))
    result1105 = _t1827
    record_span!(parser, span_start1104, "CSVLocator")
    return result1105
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1106 = String[]
    cond1107 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1107
        item1108 = consume_terminal!(parser, "STRING")
        push!(xs1106, item1108)
        cond1107 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1109 = xs1106
    consume_literal!(parser, ")")
    return strings1109
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1110 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1110
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1112 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1828 = parse_config_dict(parser)
    config_dict1111 = _t1828
    consume_literal!(parser, ")")
    _t1829 = construct_csv_config(parser, config_dict1111)
    result1113 = _t1829
    record_span!(parser, span_start1112, "CSVConfig")
    return result1113
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1114 = Proto.GNFColumn[]
    cond1115 = match_lookahead_literal(parser, "(", 0)
    while cond1115
        _t1830 = parse_gnf_column(parser)
        item1116 = _t1830
        push!(xs1114, item1116)
        cond1115 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1117 = xs1114
    consume_literal!(parser, ")")
    return gnf_columns1117
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1124 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1831 = parse_gnf_column_path(parser)
    gnf_column_path1118 = _t1831
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1833 = parse_relation_id(parser)
        _t1832 = _t1833
    else
        _t1832 = nothing
    end
    relation_id1119 = _t1832
    consume_literal!(parser, "[")
    xs1120 = Proto.var"#Type"[]
    cond1121 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1121
        _t1834 = parse_type(parser)
        item1122 = _t1834
        push!(xs1120, item1122)
        cond1121 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1123 = xs1120
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1835 = Proto.GNFColumn(column_path=gnf_column_path1118, target_id=relation_id1119, types=types1123)
    result1125 = _t1835
    record_span!(parser, span_start1124, "GNFColumn")
    return result1125
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1836 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1837 = 0
        else
            _t1837 = -1
        end
        _t1836 = _t1837
    end
    prediction1126 = _t1836
    if prediction1126 == 1
        consume_literal!(parser, "[")
        xs1128 = String[]
        cond1129 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1129
            item1130 = consume_terminal!(parser, "STRING")
            push!(xs1128, item1130)
            cond1129 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1131 = xs1128
        consume_literal!(parser, "]")
        _t1838 = strings1131
    else
        if prediction1126 == 0
            string1127 = consume_terminal!(parser, "STRING")
            _t1839 = String[string1127]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1838 = _t1839
    end
    return _t1838
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1132 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1132
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1134 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1840 = parse_fragment_id(parser)
    fragment_id1133 = _t1840
    consume_literal!(parser, ")")
    _t1841 = Proto.Undefine(fragment_id=fragment_id1133)
    result1135 = _t1841
    record_span!(parser, span_start1134, "Undefine")
    return result1135
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1140 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1136 = Proto.RelationId[]
    cond1137 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1137
        _t1842 = parse_relation_id(parser)
        item1138 = _t1842
        push!(xs1136, item1138)
        cond1137 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1139 = xs1136
    consume_literal!(parser, ")")
    _t1843 = Proto.Context(relations=relation_ids1139)
    result1141 = _t1843
    record_span!(parser, span_start1140, "Context")
    return result1141
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1146 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1142 = Proto.SnapshotMapping[]
    cond1143 = match_lookahead_literal(parser, "[", 0)
    while cond1143
        _t1844 = parse_snapshot_mapping(parser)
        item1144 = _t1844
        push!(xs1142, item1144)
        cond1143 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1145 = xs1142
    consume_literal!(parser, ")")
    _t1845 = Proto.Snapshot(mappings=snapshot_mappings1145)
    result1147 = _t1845
    record_span!(parser, span_start1146, "Snapshot")
    return result1147
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1150 = span_start(parser)
    _t1846 = parse_edb_path(parser)
    edb_path1148 = _t1846
    _t1847 = parse_relation_id(parser)
    relation_id1149 = _t1847
    _t1848 = Proto.SnapshotMapping(destination_path=edb_path1148, source_relation=relation_id1149)
    result1151 = _t1848
    record_span!(parser, span_start1150, "SnapshotMapping")
    return result1151
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1152 = Proto.Read[]
    cond1153 = match_lookahead_literal(parser, "(", 0)
    while cond1153
        _t1849 = parse_read(parser)
        item1154 = _t1849
        push!(xs1152, item1154)
        cond1153 = match_lookahead_literal(parser, "(", 0)
    end
    reads1155 = xs1152
    consume_literal!(parser, ")")
    return reads1155
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1162 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1851 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1852 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1853 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1854 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1855 = 3
                        else
                            _t1855 = -1
                        end
                        _t1854 = _t1855
                    end
                    _t1853 = _t1854
                end
                _t1852 = _t1853
            end
            _t1851 = _t1852
        end
        _t1850 = _t1851
    else
        _t1850 = -1
    end
    prediction1156 = _t1850
    if prediction1156 == 4
        _t1857 = parse_export(parser)
        export1161 = _t1857
        _t1858 = Proto.Read(read_type=OneOf(:var"#export", export1161))
        _t1856 = _t1858
    else
        if prediction1156 == 3
            _t1860 = parse_abort(parser)
            abort1160 = _t1860
            _t1861 = Proto.Read(read_type=OneOf(:abort, abort1160))
            _t1859 = _t1861
        else
            if prediction1156 == 2
                _t1863 = parse_what_if(parser)
                what_if1159 = _t1863
                _t1864 = Proto.Read(read_type=OneOf(:what_if, what_if1159))
                _t1862 = _t1864
            else
                if prediction1156 == 1
                    _t1866 = parse_output(parser)
                    output1158 = _t1866
                    _t1867 = Proto.Read(read_type=OneOf(:output, output1158))
                    _t1865 = _t1867
                else
                    if prediction1156 == 0
                        _t1869 = parse_demand(parser)
                        demand1157 = _t1869
                        _t1870 = Proto.Read(read_type=OneOf(:demand, demand1157))
                        _t1868 = _t1870
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1865 = _t1868
                end
                _t1862 = _t1865
            end
            _t1859 = _t1862
        end
        _t1856 = _t1859
    end
    result1163 = _t1856
    record_span!(parser, span_start1162, "Read")
    return result1163
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1165 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1871 = parse_relation_id(parser)
    relation_id1164 = _t1871
    consume_literal!(parser, ")")
    _t1872 = Proto.Demand(relation_id=relation_id1164)
    result1166 = _t1872
    record_span!(parser, span_start1165, "Demand")
    return result1166
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1169 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1873 = parse_name(parser)
    name1167 = _t1873
    _t1874 = parse_relation_id(parser)
    relation_id1168 = _t1874
    consume_literal!(parser, ")")
    _t1875 = Proto.Output(name=name1167, relation_id=relation_id1168)
    result1170 = _t1875
    record_span!(parser, span_start1169, "Output")
    return result1170
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1173 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1876 = parse_name(parser)
    name1171 = _t1876
    _t1877 = parse_epoch(parser)
    epoch1172 = _t1877
    consume_literal!(parser, ")")
    _t1878 = Proto.WhatIf(branch=name1171, epoch=epoch1172)
    result1174 = _t1878
    record_span!(parser, span_start1173, "WhatIf")
    return result1174
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1177 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1880 = parse_name(parser)
        _t1879 = _t1880
    else
        _t1879 = nothing
    end
    name1175 = _t1879
    _t1881 = parse_relation_id(parser)
    relation_id1176 = _t1881
    consume_literal!(parser, ")")
    _t1882 = Proto.Abort(name=(!isnothing(name1175) ? name1175 : "abort"), relation_id=relation_id1176)
    result1178 = _t1882
    record_span!(parser, span_start1177, "Abort")
    return result1178
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1180 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1883 = parse_export_csv_config(parser)
    export_csv_config1179 = _t1883
    consume_literal!(parser, ")")
    _t1884 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1179))
    result1181 = _t1884
    record_span!(parser, span_start1180, "Export")
    return result1181
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1189 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1886 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1887 = 1
            else
                _t1887 = -1
            end
            _t1886 = _t1887
        end
        _t1885 = _t1886
    else
        _t1885 = -1
    end
    prediction1182 = _t1885
    if prediction1182 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1889 = parse_export_csv_path(parser)
        export_csv_path1186 = _t1889
        _t1890 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1187 = _t1890
        _t1891 = parse_config_dict(parser)
        config_dict1188 = _t1891
        consume_literal!(parser, ")")
        _t1892 = construct_export_csv_config(parser, export_csv_path1186, export_csv_columns_list1187, config_dict1188)
        _t1888 = _t1892
    else
        if prediction1182 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1894 = parse_export_csv_path(parser)
            export_csv_path1183 = _t1894
            _t1895 = parse_export_csv_source(parser)
            export_csv_source1184 = _t1895
            _t1896 = parse_csv_config(parser)
            csv_config1185 = _t1896
            consume_literal!(parser, ")")
            _t1897 = construct_export_csv_config_with_source(parser, export_csv_path1183, export_csv_source1184, csv_config1185)
            _t1893 = _t1897
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1888 = _t1893
    end
    result1190 = _t1888
    record_span!(parser, span_start1189, "ExportCSVConfig")
    return result1190
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1191 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1191
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1198 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1899 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1900 = 0
            else
                _t1900 = -1
            end
            _t1899 = _t1900
        end
        _t1898 = _t1899
    else
        _t1898 = -1
    end
    prediction1192 = _t1898
    if prediction1192 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1902 = parse_relation_id(parser)
        relation_id1197 = _t1902
        consume_literal!(parser, ")")
        _t1903 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1197))
        _t1901 = _t1903
    else
        if prediction1192 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1193 = Proto.ExportCSVColumn[]
            cond1194 = match_lookahead_literal(parser, "(", 0)
            while cond1194
                _t1905 = parse_export_csv_column(parser)
                item1195 = _t1905
                push!(xs1193, item1195)
                cond1194 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1196 = xs1193
            consume_literal!(parser, ")")
            _t1906 = Proto.ExportCSVColumns(columns=export_csv_columns1196)
            _t1907 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1906))
            _t1904 = _t1907
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1901 = _t1904
    end
    result1199 = _t1901
    record_span!(parser, span_start1198, "ExportCSVSource")
    return result1199
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1202 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1200 = consume_terminal!(parser, "STRING")
    _t1908 = parse_relation_id(parser)
    relation_id1201 = _t1908
    consume_literal!(parser, ")")
    _t1909 = Proto.ExportCSVColumn(column_name=string1200, column_data=relation_id1201)
    result1203 = _t1909
    record_span!(parser, span_start1202, "ExportCSVColumn")
    return result1203
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1204 = Proto.ExportCSVColumn[]
    cond1205 = match_lookahead_literal(parser, "(", 0)
    while cond1205
        _t1910 = parse_export_csv_column(parser)
        item1206 = _t1910
        push!(xs1204, item1206)
        cond1205 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1207 = xs1204
    consume_literal!(parser, ")")
    return export_csv_columns1207
end


function _check_eof(parser::ParserState)
    if parser.pos <= length(parser.tokens)
        remaining_token = lookahead(parser, 0)
        if remaining_token.type != "\$"
            throw(ParseError("Unexpected token at end of input: $remaining_token"))
        end
    end
    return nothing
end

function parse_transaction(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens, input)
    result = parse_transaction(parser)
    _check_eof(parser)
    return result
end

function parse_fragment(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens, input)
    result = parse_fragment(parser)
    _check_eof(parser)
    return result
end

function parse(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens, input)
    result = parse_transaction(parser)
    _check_eof(parser)
    # Add root span at () key
    root_offset = lexer.tokens[1].start_pos
    if haskey(parser.provenance, root_offset)
        parser.provenance[()] = parser.provenance[root_offset]
    end
    return result, parser.provenance
end

# Export main parse functions and error type
export parse, parse_transaction, parse_fragment, ParseError
# Export scanner functions for testing
export scan_string, scan_int, scan_int32, scan_uint32, scan_float, scan_float32, scan_int128, scan_uint128, scan_decimal
# Export Lexer and provenance types for testing
export Lexer, Location, Span

end # module Parser
