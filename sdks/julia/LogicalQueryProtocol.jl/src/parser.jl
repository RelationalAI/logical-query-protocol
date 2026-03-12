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
        _t1902 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1903 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1904 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1905 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1906 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1907 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1908 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1909 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1910 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1911 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1911
    _t1912 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1912
    _t1913 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1913
    _t1914 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1914
    _t1915 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1915
    _t1916 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1916
    _t1917 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1917
    _t1918 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1918
    _t1919 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1919
    _t1920 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1920
    _t1921 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1921
    _t1922 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t1922
    _t1923 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t1923
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1924 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1924
    _t1925 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1925
    _t1926 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1926
    _t1927 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1927
    _t1928 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1928
    _t1929 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1929
    _t1930 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1930
    _t1931 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1931
    _t1932 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1932
    _t1933 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1933
    _t1934 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1934
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1935 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1935
    _t1936 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1936
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
    _t1937 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1937
    _t1938 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1938
    _t1939 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1939
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1940 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1940
    _t1941 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1941
    _t1942 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1942
    _t1943 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1943
    _t1944 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1944
    _t1945 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1945
    _t1946 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1946
    _t1947 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1947
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1948 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1948
end

function construct_iceberg_config(parser::ParserState, catalog_uri::String, scope::Union{Nothing, String}, properties::Union{Nothing, Vector{Tuple{String, String}}}, credentials::Union{Nothing, Vector{Tuple{String, String}}})::Proto.IcebergConfig
    props = Dict((!isnothing(properties) ? properties : Tuple{String, String}[]))
    creds = Dict((!isnothing(credentials) ? credentials : Tuple{String, String}[]))
    _t1949 = Proto.IcebergConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope) ? scope : ""), properties=props, credentials=creds)
    return _t1949
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start618 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1225 = parse_configure(parser)
        _t1224 = _t1225
    else
        _t1224 = nothing
    end
    configure612 = _t1224
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1227 = parse_sync(parser)
        _t1226 = _t1227
    else
        _t1226 = nothing
    end
    sync613 = _t1226
    xs614 = Proto.Epoch[]
    cond615 = match_lookahead_literal(parser, "(", 0)
    while cond615
        _t1228 = parse_epoch(parser)
        item616 = _t1228
        push!(xs614, item616)
        cond615 = match_lookahead_literal(parser, "(", 0)
    end
    epochs617 = xs614
    consume_literal!(parser, ")")
    _t1229 = default_configure(parser)
    _t1230 = Proto.Transaction(epochs=epochs617, configure=(!isnothing(configure612) ? configure612 : _t1229), sync=sync613)
    result619 = _t1230
    record_span!(parser, span_start618, "Transaction")
    return result619
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start621 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1231 = parse_config_dict(parser)
    config_dict620 = _t1231
    consume_literal!(parser, ")")
    _t1232 = construct_configure(parser, config_dict620)
    result622 = _t1232
    record_span!(parser, span_start621, "Configure")
    return result622
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs623 = Tuple{String, Proto.Value}[]
    cond624 = match_lookahead_literal(parser, ":", 0)
    while cond624
        _t1233 = parse_config_key_value(parser)
        item625 = _t1233
        push!(xs623, item625)
        cond624 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values626 = xs623
    consume_literal!(parser, "}")
    return config_key_values626
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol627 = consume_terminal!(parser, "SYMBOL")
    _t1234 = parse_value(parser)
    value628 = _t1234
    return (symbol627, value628,)
end

function parse_value(parser::ParserState)::Proto.Value
    span_start642 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1235 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1236 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1237 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1239 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1240 = 0
                        else
                            _t1240 = -1
                        end
                        _t1239 = _t1240
                    end
                    _t1238 = _t1239
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1241 = 12
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1242 = 5
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1243 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1244 = 10
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1245 = 6
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1246 = 3
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1247 = 11
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1248 = 4
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1249 = 7
                                                    else
                                                        _t1249 = -1
                                                    end
                                                    _t1248 = _t1249
                                                end
                                                _t1247 = _t1248
                                            end
                                            _t1246 = _t1247
                                        end
                                        _t1245 = _t1246
                                    end
                                    _t1244 = _t1245
                                end
                                _t1243 = _t1244
                            end
                            _t1242 = _t1243
                        end
                        _t1241 = _t1242
                    end
                    _t1238 = _t1241
                end
                _t1237 = _t1238
            end
            _t1236 = _t1237
        end
        _t1235 = _t1236
    end
    prediction629 = _t1235
    if prediction629 == 12
        uint32641 = consume_terminal!(parser, "UINT32")
        _t1251 = Proto.Value(value=OneOf(:uint32_value, uint32641))
        _t1250 = _t1251
    else
        if prediction629 == 11
            float32640 = consume_terminal!(parser, "FLOAT32")
            _t1253 = Proto.Value(value=OneOf(:float32_value, float32640))
            _t1252 = _t1253
        else
            if prediction629 == 10
                int32639 = consume_terminal!(parser, "INT32")
                _t1255 = Proto.Value(value=OneOf(:int32_value, int32639))
                _t1254 = _t1255
            else
                if prediction629 == 9
                    _t1257 = parse_boolean_value(parser)
                    boolean_value638 = _t1257
                    _t1258 = Proto.Value(value=OneOf(:boolean_value, boolean_value638))
                    _t1256 = _t1258
                else
                    if prediction629 == 8
                        consume_literal!(parser, "missing")
                        _t1260 = Proto.MissingValue()
                        _t1261 = Proto.Value(value=OneOf(:missing_value, _t1260))
                        _t1259 = _t1261
                    else
                        if prediction629 == 7
                            decimal637 = consume_terminal!(parser, "DECIMAL")
                            _t1263 = Proto.Value(value=OneOf(:decimal_value, decimal637))
                            _t1262 = _t1263
                        else
                            if prediction629 == 6
                                int128636 = consume_terminal!(parser, "INT128")
                                _t1265 = Proto.Value(value=OneOf(:int128_value, int128636))
                                _t1264 = _t1265
                            else
                                if prediction629 == 5
                                    uint128635 = consume_terminal!(parser, "UINT128")
                                    _t1267 = Proto.Value(value=OneOf(:uint128_value, uint128635))
                                    _t1266 = _t1267
                                else
                                    if prediction629 == 4
                                        float634 = consume_terminal!(parser, "FLOAT")
                                        _t1269 = Proto.Value(value=OneOf(:float_value, float634))
                                        _t1268 = _t1269
                                    else
                                        if prediction629 == 3
                                            int633 = consume_terminal!(parser, "INT")
                                            _t1271 = Proto.Value(value=OneOf(:int_value, int633))
                                            _t1270 = _t1271
                                        else
                                            if prediction629 == 2
                                                string632 = consume_terminal!(parser, "STRING")
                                                _t1273 = Proto.Value(value=OneOf(:string_value, string632))
                                                _t1272 = _t1273
                                            else
                                                if prediction629 == 1
                                                    _t1275 = parse_datetime(parser)
                                                    datetime631 = _t1275
                                                    _t1276 = Proto.Value(value=OneOf(:datetime_value, datetime631))
                                                    _t1274 = _t1276
                                                else
                                                    if prediction629 == 0
                                                        _t1278 = parse_date(parser)
                                                        date630 = _t1278
                                                        _t1279 = Proto.Value(value=OneOf(:date_value, date630))
                                                        _t1277 = _t1279
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1274 = _t1277
                                                end
                                                _t1272 = _t1274
                                            end
                                            _t1270 = _t1272
                                        end
                                        _t1268 = _t1270
                                    end
                                    _t1266 = _t1268
                                end
                                _t1264 = _t1266
                            end
                            _t1262 = _t1264
                        end
                        _t1259 = _t1262
                    end
                    _t1256 = _t1259
                end
                _t1254 = _t1256
            end
            _t1252 = _t1254
        end
        _t1250 = _t1252
    end
    result643 = _t1250
    record_span!(parser, span_start642, "Value")
    return result643
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start647 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int644 = consume_terminal!(parser, "INT")
    int_3645 = consume_terminal!(parser, "INT")
    int_4646 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1280 = Proto.DateValue(year=Int32(int644), month=Int32(int_3645), day=Int32(int_4646))
    result648 = _t1280
    record_span!(parser, span_start647, "DateValue")
    return result648
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start656 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int649 = consume_terminal!(parser, "INT")
    int_3650 = consume_terminal!(parser, "INT")
    int_4651 = consume_terminal!(parser, "INT")
    int_5652 = consume_terminal!(parser, "INT")
    int_6653 = consume_terminal!(parser, "INT")
    int_7654 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1281 = consume_terminal!(parser, "INT")
    else
        _t1281 = nothing
    end
    int_8655 = _t1281
    consume_literal!(parser, ")")
    _t1282 = Proto.DateTimeValue(year=Int32(int649), month=Int32(int_3650), day=Int32(int_4651), hour=Int32(int_5652), minute=Int32(int_6653), second=Int32(int_7654), microsecond=Int32((!isnothing(int_8655) ? int_8655 : 0)))
    result657 = _t1282
    record_span!(parser, span_start656, "DateTimeValue")
    return result657
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1283 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1284 = 1
        else
            _t1284 = -1
        end
        _t1283 = _t1284
    end
    prediction658 = _t1283
    if prediction658 == 1
        consume_literal!(parser, "false")
        _t1285 = false
    else
        if prediction658 == 0
            consume_literal!(parser, "true")
            _t1286 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1285 = _t1286
    end
    return _t1285
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start663 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs659 = Proto.FragmentId[]
    cond660 = match_lookahead_literal(parser, ":", 0)
    while cond660
        _t1287 = parse_fragment_id(parser)
        item661 = _t1287
        push!(xs659, item661)
        cond660 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids662 = xs659
    consume_literal!(parser, ")")
    _t1288 = Proto.Sync(fragments=fragment_ids662)
    result664 = _t1288
    record_span!(parser, span_start663, "Sync")
    return result664
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start666 = span_start(parser)
    consume_literal!(parser, ":")
    symbol665 = consume_terminal!(parser, "SYMBOL")
    result667 = Proto.FragmentId(Vector{UInt8}(symbol665))
    record_span!(parser, span_start666, "FragmentId")
    return result667
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start670 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1290 = parse_epoch_writes(parser)
        _t1289 = _t1290
    else
        _t1289 = nothing
    end
    epoch_writes668 = _t1289
    if match_lookahead_literal(parser, "(", 0)
        _t1292 = parse_epoch_reads(parser)
        _t1291 = _t1292
    else
        _t1291 = nothing
    end
    epoch_reads669 = _t1291
    consume_literal!(parser, ")")
    _t1293 = Proto.Epoch(writes=(!isnothing(epoch_writes668) ? epoch_writes668 : Proto.Write[]), reads=(!isnothing(epoch_reads669) ? epoch_reads669 : Proto.Read[]))
    result671 = _t1293
    record_span!(parser, span_start670, "Epoch")
    return result671
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs672 = Proto.Write[]
    cond673 = match_lookahead_literal(parser, "(", 0)
    while cond673
        _t1294 = parse_write(parser)
        item674 = _t1294
        push!(xs672, item674)
        cond673 = match_lookahead_literal(parser, "(", 0)
    end
    writes675 = xs672
    consume_literal!(parser, ")")
    return writes675
end

function parse_write(parser::ParserState)::Proto.Write
    span_start681 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1296 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1297 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1298 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1299 = 2
                    else
                        _t1299 = -1
                    end
                    _t1298 = _t1299
                end
                _t1297 = _t1298
            end
            _t1296 = _t1297
        end
        _t1295 = _t1296
    else
        _t1295 = -1
    end
    prediction676 = _t1295
    if prediction676 == 3
        _t1301 = parse_snapshot(parser)
        snapshot680 = _t1301
        _t1302 = Proto.Write(write_type=OneOf(:snapshot, snapshot680))
        _t1300 = _t1302
    else
        if prediction676 == 2
            _t1304 = parse_context(parser)
            context679 = _t1304
            _t1305 = Proto.Write(write_type=OneOf(:context, context679))
            _t1303 = _t1305
        else
            if prediction676 == 1
                _t1307 = parse_undefine(parser)
                undefine678 = _t1307
                _t1308 = Proto.Write(write_type=OneOf(:undefine, undefine678))
                _t1306 = _t1308
            else
                if prediction676 == 0
                    _t1310 = parse_define(parser)
                    define677 = _t1310
                    _t1311 = Proto.Write(write_type=OneOf(:define, define677))
                    _t1309 = _t1311
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1306 = _t1309
            end
            _t1303 = _t1306
        end
        _t1300 = _t1303
    end
    result682 = _t1300
    record_span!(parser, span_start681, "Write")
    return result682
end

function parse_define(parser::ParserState)::Proto.Define
    span_start684 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1312 = parse_fragment(parser)
    fragment683 = _t1312
    consume_literal!(parser, ")")
    _t1313 = Proto.Define(fragment=fragment683)
    result685 = _t1313
    record_span!(parser, span_start684, "Define")
    return result685
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start691 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1314 = parse_new_fragment_id(parser)
    new_fragment_id686 = _t1314
    xs687 = Proto.Declaration[]
    cond688 = match_lookahead_literal(parser, "(", 0)
    while cond688
        _t1315 = parse_declaration(parser)
        item689 = _t1315
        push!(xs687, item689)
        cond688 = match_lookahead_literal(parser, "(", 0)
    end
    declarations690 = xs687
    consume_literal!(parser, ")")
    result692 = construct_fragment(parser, new_fragment_id686, declarations690)
    record_span!(parser, span_start691, "Fragment")
    return result692
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start694 = span_start(parser)
    _t1316 = parse_fragment_id(parser)
    fragment_id693 = _t1316
    start_fragment!(parser, fragment_id693)
    result695 = fragment_id693
    record_span!(parser, span_start694, "FragmentId")
    return result695
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start701 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1318 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1319 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1320 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1321 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1322 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1323 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1324 = 1
                                else
                                    _t1324 = -1
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
    else
        _t1317 = -1
    end
    prediction696 = _t1317
    if prediction696 == 3
        _t1326 = parse_data(parser)
        data700 = _t1326
        _t1327 = Proto.Declaration(declaration_type=OneOf(:data, data700))
        _t1325 = _t1327
    else
        if prediction696 == 2
            _t1329 = parse_constraint(parser)
            constraint699 = _t1329
            _t1330 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint699))
            _t1328 = _t1330
        else
            if prediction696 == 1
                _t1332 = parse_algorithm(parser)
                algorithm698 = _t1332
                _t1333 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm698))
                _t1331 = _t1333
            else
                if prediction696 == 0
                    _t1335 = parse_def(parser)
                    def697 = _t1335
                    _t1336 = Proto.Declaration(declaration_type=OneOf(:def, def697))
                    _t1334 = _t1336
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1331 = _t1334
            end
            _t1328 = _t1331
        end
        _t1325 = _t1328
    end
    result702 = _t1325
    record_span!(parser, span_start701, "Declaration")
    return result702
end

function parse_def(parser::ParserState)::Proto.Def
    span_start706 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1337 = parse_relation_id(parser)
    relation_id703 = _t1337
    _t1338 = parse_abstraction(parser)
    abstraction704 = _t1338
    if match_lookahead_literal(parser, "(", 0)
        _t1340 = parse_attrs(parser)
        _t1339 = _t1340
    else
        _t1339 = nothing
    end
    attrs705 = _t1339
    consume_literal!(parser, ")")
    _t1341 = Proto.Def(name=relation_id703, body=abstraction704, attrs=(!isnothing(attrs705) ? attrs705 : Proto.Attribute[]))
    result707 = _t1341
    record_span!(parser, span_start706, "Def")
    return result707
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start711 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1342 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1343 = 1
        else
            _t1343 = -1
        end
        _t1342 = _t1343
    end
    prediction708 = _t1342
    if prediction708 == 1
        uint128710 = consume_terminal!(parser, "UINT128")
        _t1344 = Proto.RelationId(uint128710.low, uint128710.high)
    else
        if prediction708 == 0
            consume_literal!(parser, ":")
            symbol709 = consume_terminal!(parser, "SYMBOL")
            _t1345 = relation_id_from_string(parser, symbol709)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1344 = _t1345
    end
    result712 = _t1344
    record_span!(parser, span_start711, "RelationId")
    return result712
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start715 = span_start(parser)
    consume_literal!(parser, "(")
    _t1346 = parse_bindings(parser)
    bindings713 = _t1346
    _t1347 = parse_formula(parser)
    formula714 = _t1347
    consume_literal!(parser, ")")
    _t1348 = Proto.Abstraction(vars=vcat(bindings713[1], !isnothing(bindings713[2]) ? bindings713[2] : []), value=formula714)
    result716 = _t1348
    record_span!(parser, span_start715, "Abstraction")
    return result716
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs717 = Proto.Binding[]
    cond718 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond718
        _t1349 = parse_binding(parser)
        item719 = _t1349
        push!(xs717, item719)
        cond718 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings720 = xs717
    if match_lookahead_literal(parser, "|", 0)
        _t1351 = parse_value_bindings(parser)
        _t1350 = _t1351
    else
        _t1350 = nothing
    end
    value_bindings721 = _t1350
    consume_literal!(parser, "]")
    return (bindings720, (!isnothing(value_bindings721) ? value_bindings721 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start724 = span_start(parser)
    symbol722 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1352 = parse_type(parser)
    type723 = _t1352
    _t1353 = Proto.Var(name=symbol722)
    _t1354 = Proto.Binding(var=_t1353, var"#type"=type723)
    result725 = _t1354
    record_span!(parser, span_start724, "Binding")
    return result725
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start741 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1355 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1356 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1357 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1358 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1359 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1360 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1361 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1362 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1363 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1364 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1365 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1366 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1367 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1368 = 9
                                                        else
                                                            _t1368 = -1
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
                            end
                            _t1360 = _t1361
                        end
                        _t1359 = _t1360
                    end
                    _t1358 = _t1359
                end
                _t1357 = _t1358
            end
            _t1356 = _t1357
        end
        _t1355 = _t1356
    end
    prediction726 = _t1355
    if prediction726 == 13
        _t1370 = parse_uint32_type(parser)
        uint32_type740 = _t1370
        _t1371 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type740))
        _t1369 = _t1371
    else
        if prediction726 == 12
            _t1373 = parse_float32_type(parser)
            float32_type739 = _t1373
            _t1374 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type739))
            _t1372 = _t1374
        else
            if prediction726 == 11
                _t1376 = parse_int32_type(parser)
                int32_type738 = _t1376
                _t1377 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type738))
                _t1375 = _t1377
            else
                if prediction726 == 10
                    _t1379 = parse_boolean_type(parser)
                    boolean_type737 = _t1379
                    _t1380 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type737))
                    _t1378 = _t1380
                else
                    if prediction726 == 9
                        _t1382 = parse_decimal_type(parser)
                        decimal_type736 = _t1382
                        _t1383 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type736))
                        _t1381 = _t1383
                    else
                        if prediction726 == 8
                            _t1385 = parse_missing_type(parser)
                            missing_type735 = _t1385
                            _t1386 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type735))
                            _t1384 = _t1386
                        else
                            if prediction726 == 7
                                _t1388 = parse_datetime_type(parser)
                                datetime_type734 = _t1388
                                _t1389 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type734))
                                _t1387 = _t1389
                            else
                                if prediction726 == 6
                                    _t1391 = parse_date_type(parser)
                                    date_type733 = _t1391
                                    _t1392 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type733))
                                    _t1390 = _t1392
                                else
                                    if prediction726 == 5
                                        _t1394 = parse_int128_type(parser)
                                        int128_type732 = _t1394
                                        _t1395 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type732))
                                        _t1393 = _t1395
                                    else
                                        if prediction726 == 4
                                            _t1397 = parse_uint128_type(parser)
                                            uint128_type731 = _t1397
                                            _t1398 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type731))
                                            _t1396 = _t1398
                                        else
                                            if prediction726 == 3
                                                _t1400 = parse_float_type(parser)
                                                float_type730 = _t1400
                                                _t1401 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type730))
                                                _t1399 = _t1401
                                            else
                                                if prediction726 == 2
                                                    _t1403 = parse_int_type(parser)
                                                    int_type729 = _t1403
                                                    _t1404 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type729))
                                                    _t1402 = _t1404
                                                else
                                                    if prediction726 == 1
                                                        _t1406 = parse_string_type(parser)
                                                        string_type728 = _t1406
                                                        _t1407 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type728))
                                                        _t1405 = _t1407
                                                    else
                                                        if prediction726 == 0
                                                            _t1409 = parse_unspecified_type(parser)
                                                            unspecified_type727 = _t1409
                                                            _t1410 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type727))
                                                            _t1408 = _t1410
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                        _t1381 = _t1384
                    end
                    _t1378 = _t1381
                end
                _t1375 = _t1378
            end
            _t1372 = _t1375
        end
        _t1369 = _t1372
    end
    result742 = _t1369
    record_span!(parser, span_start741, "Type")
    return result742
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start743 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1411 = Proto.UnspecifiedType()
    result744 = _t1411
    record_span!(parser, span_start743, "UnspecifiedType")
    return result744
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start745 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1412 = Proto.StringType()
    result746 = _t1412
    record_span!(parser, span_start745, "StringType")
    return result746
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start747 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1413 = Proto.IntType()
    result748 = _t1413
    record_span!(parser, span_start747, "IntType")
    return result748
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start749 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1414 = Proto.FloatType()
    result750 = _t1414
    record_span!(parser, span_start749, "FloatType")
    return result750
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start751 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1415 = Proto.UInt128Type()
    result752 = _t1415
    record_span!(parser, span_start751, "UInt128Type")
    return result752
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start753 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1416 = Proto.Int128Type()
    result754 = _t1416
    record_span!(parser, span_start753, "Int128Type")
    return result754
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start755 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1417 = Proto.DateType()
    result756 = _t1417
    record_span!(parser, span_start755, "DateType")
    return result756
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start757 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1418 = Proto.DateTimeType()
    result758 = _t1418
    record_span!(parser, span_start757, "DateTimeType")
    return result758
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start759 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1419 = Proto.MissingType()
    result760 = _t1419
    record_span!(parser, span_start759, "MissingType")
    return result760
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start763 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int761 = consume_terminal!(parser, "INT")
    int_3762 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1420 = Proto.DecimalType(precision=Int32(int761), scale=Int32(int_3762))
    result764 = _t1420
    record_span!(parser, span_start763, "DecimalType")
    return result764
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start765 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1421 = Proto.BooleanType()
    result766 = _t1421
    record_span!(parser, span_start765, "BooleanType")
    return result766
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start767 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1422 = Proto.Int32Type()
    result768 = _t1422
    record_span!(parser, span_start767, "Int32Type")
    return result768
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start769 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1423 = Proto.Float32Type()
    result770 = _t1423
    record_span!(parser, span_start769, "Float32Type")
    return result770
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start771 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1424 = Proto.UInt32Type()
    result772 = _t1424
    record_span!(parser, span_start771, "UInt32Type")
    return result772
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs773 = Proto.Binding[]
    cond774 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond774
        _t1425 = parse_binding(parser)
        item775 = _t1425
        push!(xs773, item775)
        cond774 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings776 = xs773
    return bindings776
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start791 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1427 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1428 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1429 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1430 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1431 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1432 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1433 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1434 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1435 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1436 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1437 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1438 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1439 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1440 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1441 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1442 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1443 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1444 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1445 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1446 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1447 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1448 = 10
                                                                                            else
                                                                                                _t1448 = -1
                                                                                            end
                                                                                            _t1447 = _t1448
                                                                                        end
                                                                                        _t1446 = _t1447
                                                                                    end
                                                                                    _t1445 = _t1446
                                                                                end
                                                                                _t1444 = _t1445
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
                                    _t1433 = _t1434
                                end
                                _t1432 = _t1433
                            end
                            _t1431 = _t1432
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
    else
        _t1426 = -1
    end
    prediction777 = _t1426
    if prediction777 == 12
        _t1450 = parse_cast(parser)
        cast790 = _t1450
        _t1451 = Proto.Formula(formula_type=OneOf(:cast, cast790))
        _t1449 = _t1451
    else
        if prediction777 == 11
            _t1453 = parse_rel_atom(parser)
            rel_atom789 = _t1453
            _t1454 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom789))
            _t1452 = _t1454
        else
            if prediction777 == 10
                _t1456 = parse_primitive(parser)
                primitive788 = _t1456
                _t1457 = Proto.Formula(formula_type=OneOf(:primitive, primitive788))
                _t1455 = _t1457
            else
                if prediction777 == 9
                    _t1459 = parse_pragma(parser)
                    pragma787 = _t1459
                    _t1460 = Proto.Formula(formula_type=OneOf(:pragma, pragma787))
                    _t1458 = _t1460
                else
                    if prediction777 == 8
                        _t1462 = parse_atom(parser)
                        atom786 = _t1462
                        _t1463 = Proto.Formula(formula_type=OneOf(:atom, atom786))
                        _t1461 = _t1463
                    else
                        if prediction777 == 7
                            _t1465 = parse_ffi(parser)
                            ffi785 = _t1465
                            _t1466 = Proto.Formula(formula_type=OneOf(:ffi, ffi785))
                            _t1464 = _t1466
                        else
                            if prediction777 == 6
                                _t1468 = parse_not(parser)
                                not784 = _t1468
                                _t1469 = Proto.Formula(formula_type=OneOf(:not, not784))
                                _t1467 = _t1469
                            else
                                if prediction777 == 5
                                    _t1471 = parse_disjunction(parser)
                                    disjunction783 = _t1471
                                    _t1472 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction783))
                                    _t1470 = _t1472
                                else
                                    if prediction777 == 4
                                        _t1474 = parse_conjunction(parser)
                                        conjunction782 = _t1474
                                        _t1475 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction782))
                                        _t1473 = _t1475
                                    else
                                        if prediction777 == 3
                                            _t1477 = parse_reduce(parser)
                                            reduce781 = _t1477
                                            _t1478 = Proto.Formula(formula_type=OneOf(:reduce, reduce781))
                                            _t1476 = _t1478
                                        else
                                            if prediction777 == 2
                                                _t1480 = parse_exists(parser)
                                                exists780 = _t1480
                                                _t1481 = Proto.Formula(formula_type=OneOf(:exists, exists780))
                                                _t1479 = _t1481
                                            else
                                                if prediction777 == 1
                                                    _t1483 = parse_false(parser)
                                                    false779 = _t1483
                                                    _t1484 = Proto.Formula(formula_type=OneOf(:disjunction, false779))
                                                    _t1482 = _t1484
                                                else
                                                    if prediction777 == 0
                                                        _t1486 = parse_true(parser)
                                                        true778 = _t1486
                                                        _t1487 = Proto.Formula(formula_type=OneOf(:conjunction, true778))
                                                        _t1485 = _t1487
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1482 = _t1485
                                                end
                                                _t1479 = _t1482
                                            end
                                            _t1476 = _t1479
                                        end
                                        _t1473 = _t1476
                                    end
                                    _t1470 = _t1473
                                end
                                _t1467 = _t1470
                            end
                            _t1464 = _t1467
                        end
                        _t1461 = _t1464
                    end
                    _t1458 = _t1461
                end
                _t1455 = _t1458
            end
            _t1452 = _t1455
        end
        _t1449 = _t1452
    end
    result792 = _t1449
    record_span!(parser, span_start791, "Formula")
    return result792
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start793 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1488 = Proto.Conjunction(args=Proto.Formula[])
    result794 = _t1488
    record_span!(parser, span_start793, "Conjunction")
    return result794
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start795 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1489 = Proto.Disjunction(args=Proto.Formula[])
    result796 = _t1489
    record_span!(parser, span_start795, "Disjunction")
    return result796
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start799 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1490 = parse_bindings(parser)
    bindings797 = _t1490
    _t1491 = parse_formula(parser)
    formula798 = _t1491
    consume_literal!(parser, ")")
    _t1492 = Proto.Abstraction(vars=vcat(bindings797[1], !isnothing(bindings797[2]) ? bindings797[2] : []), value=formula798)
    _t1493 = Proto.Exists(body=_t1492)
    result800 = _t1493
    record_span!(parser, span_start799, "Exists")
    return result800
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start804 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1494 = parse_abstraction(parser)
    abstraction801 = _t1494
    _t1495 = parse_abstraction(parser)
    abstraction_3802 = _t1495
    _t1496 = parse_terms(parser)
    terms803 = _t1496
    consume_literal!(parser, ")")
    _t1497 = Proto.Reduce(op=abstraction801, body=abstraction_3802, terms=terms803)
    result805 = _t1497
    record_span!(parser, span_start804, "Reduce")
    return result805
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs806 = Proto.Term[]
    cond807 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond807
        _t1498 = parse_term(parser)
        item808 = _t1498
        push!(xs806, item808)
        cond807 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    terms809 = xs806
    consume_literal!(parser, ")")
    return terms809
end

function parse_term(parser::ParserState)::Proto.Term
    span_start813 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1499 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1500 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1501 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1502 = 1
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1503 = 1
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1504 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1505 = 0
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1506 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1507 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1508 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1509 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1510 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1511 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1512 = 1
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
    prediction810 = _t1499
    if prediction810 == 1
        _t1514 = parse_constant(parser)
        constant812 = _t1514
        _t1515 = Proto.Term(term_type=OneOf(:constant, constant812))
        _t1513 = _t1515
    else
        if prediction810 == 0
            _t1517 = parse_var(parser)
            var811 = _t1517
            _t1518 = Proto.Term(term_type=OneOf(:var, var811))
            _t1516 = _t1518
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1513 = _t1516
    end
    result814 = _t1513
    record_span!(parser, span_start813, "Term")
    return result814
end

function parse_var(parser::ParserState)::Proto.Var
    span_start816 = span_start(parser)
    symbol815 = consume_terminal!(parser, "SYMBOL")
    _t1519 = Proto.Var(name=symbol815)
    result817 = _t1519
    record_span!(parser, span_start816, "Var")
    return result817
end

function parse_constant(parser::ParserState)::Proto.Value
    span_start819 = span_start(parser)
    _t1520 = parse_value(parser)
    value818 = _t1520
    result820 = value818
    record_span!(parser, span_start819, "Value")
    return result820
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start825 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs821 = Proto.Formula[]
    cond822 = match_lookahead_literal(parser, "(", 0)
    while cond822
        _t1521 = parse_formula(parser)
        item823 = _t1521
        push!(xs821, item823)
        cond822 = match_lookahead_literal(parser, "(", 0)
    end
    formulas824 = xs821
    consume_literal!(parser, ")")
    _t1522 = Proto.Conjunction(args=formulas824)
    result826 = _t1522
    record_span!(parser, span_start825, "Conjunction")
    return result826
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start831 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs827 = Proto.Formula[]
    cond828 = match_lookahead_literal(parser, "(", 0)
    while cond828
        _t1523 = parse_formula(parser)
        item829 = _t1523
        push!(xs827, item829)
        cond828 = match_lookahead_literal(parser, "(", 0)
    end
    formulas830 = xs827
    consume_literal!(parser, ")")
    _t1524 = Proto.Disjunction(args=formulas830)
    result832 = _t1524
    record_span!(parser, span_start831, "Disjunction")
    return result832
end

function parse_not(parser::ParserState)::Proto.Not
    span_start834 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1525 = parse_formula(parser)
    formula833 = _t1525
    consume_literal!(parser, ")")
    _t1526 = Proto.Not(arg=formula833)
    result835 = _t1526
    record_span!(parser, span_start834, "Not")
    return result835
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start839 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1527 = parse_name(parser)
    name836 = _t1527
    _t1528 = parse_ffi_args(parser)
    ffi_args837 = _t1528
    _t1529 = parse_terms(parser)
    terms838 = _t1529
    consume_literal!(parser, ")")
    _t1530 = Proto.FFI(name=name836, args=ffi_args837, terms=terms838)
    result840 = _t1530
    record_span!(parser, span_start839, "FFI")
    return result840
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol841 = consume_terminal!(parser, "SYMBOL")
    return symbol841
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs842 = Proto.Abstraction[]
    cond843 = match_lookahead_literal(parser, "(", 0)
    while cond843
        _t1531 = parse_abstraction(parser)
        item844 = _t1531
        push!(xs842, item844)
        cond843 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions845 = xs842
    consume_literal!(parser, ")")
    return abstractions845
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start851 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1532 = parse_relation_id(parser)
    relation_id846 = _t1532
    xs847 = Proto.Term[]
    cond848 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond848
        _t1533 = parse_term(parser)
        item849 = _t1533
        push!(xs847, item849)
        cond848 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    terms850 = xs847
    consume_literal!(parser, ")")
    _t1534 = Proto.Atom(name=relation_id846, terms=terms850)
    result852 = _t1534
    record_span!(parser, span_start851, "Atom")
    return result852
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start858 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1535 = parse_name(parser)
    name853 = _t1535
    xs854 = Proto.Term[]
    cond855 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond855
        _t1536 = parse_term(parser)
        item856 = _t1536
        push!(xs854, item856)
        cond855 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    terms857 = xs854
    consume_literal!(parser, ")")
    _t1537 = Proto.Pragma(name=name853, terms=terms857)
    result859 = _t1537
    record_span!(parser, span_start858, "Pragma")
    return result859
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start875 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1539 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1540 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1541 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1542 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1543 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1544 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1545 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1546 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1547 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1548 = 7
                                            else
                                                _t1548 = -1
                                            end
                                            _t1547 = _t1548
                                        end
                                        _t1546 = _t1547
                                    end
                                    _t1545 = _t1546
                                end
                                _t1544 = _t1545
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
    prediction860 = _t1538
    if prediction860 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1550 = parse_name(parser)
        name870 = _t1550
        xs871 = Proto.RelTerm[]
        cond872 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
        while cond872
            _t1551 = parse_rel_term(parser)
            item873 = _t1551
            push!(xs871, item873)
            cond872 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
        end
        rel_terms874 = xs871
        consume_literal!(parser, ")")
        _t1552 = Proto.Primitive(name=name870, terms=rel_terms874)
        _t1549 = _t1552
    else
        if prediction860 == 8
            _t1554 = parse_divide(parser)
            divide869 = _t1554
            _t1553 = divide869
        else
            if prediction860 == 7
                _t1556 = parse_multiply(parser)
                multiply868 = _t1556
                _t1555 = multiply868
            else
                if prediction860 == 6
                    _t1558 = parse_minus(parser)
                    minus867 = _t1558
                    _t1557 = minus867
                else
                    if prediction860 == 5
                        _t1560 = parse_add(parser)
                        add866 = _t1560
                        _t1559 = add866
                    else
                        if prediction860 == 4
                            _t1562 = parse_gt_eq(parser)
                            gt_eq865 = _t1562
                            _t1561 = gt_eq865
                        else
                            if prediction860 == 3
                                _t1564 = parse_gt(parser)
                                gt864 = _t1564
                                _t1563 = gt864
                            else
                                if prediction860 == 2
                                    _t1566 = parse_lt_eq(parser)
                                    lt_eq863 = _t1566
                                    _t1565 = lt_eq863
                                else
                                    if prediction860 == 1
                                        _t1568 = parse_lt(parser)
                                        lt862 = _t1568
                                        _t1567 = lt862
                                    else
                                        if prediction860 == 0
                                            _t1570 = parse_eq(parser)
                                            eq861 = _t1570
                                            _t1569 = eq861
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1567 = _t1569
                                    end
                                    _t1565 = _t1567
                                end
                                _t1563 = _t1565
                            end
                            _t1561 = _t1563
                        end
                        _t1559 = _t1561
                    end
                    _t1557 = _t1559
                end
                _t1555 = _t1557
            end
            _t1553 = _t1555
        end
        _t1549 = _t1553
    end
    result876 = _t1549
    record_span!(parser, span_start875, "Primitive")
    return result876
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start879 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1571 = parse_term(parser)
    term877 = _t1571
    _t1572 = parse_term(parser)
    term_3878 = _t1572
    consume_literal!(parser, ")")
    _t1573 = Proto.RelTerm(rel_term_type=OneOf(:term, term877))
    _t1574 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3878))
    _t1575 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1573, _t1574])
    result880 = _t1575
    record_span!(parser, span_start879, "Primitive")
    return result880
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start883 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1576 = parse_term(parser)
    term881 = _t1576
    _t1577 = parse_term(parser)
    term_3882 = _t1577
    consume_literal!(parser, ")")
    _t1578 = Proto.RelTerm(rel_term_type=OneOf(:term, term881))
    _t1579 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3882))
    _t1580 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1578, _t1579])
    result884 = _t1580
    record_span!(parser, span_start883, "Primitive")
    return result884
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start887 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1581 = parse_term(parser)
    term885 = _t1581
    _t1582 = parse_term(parser)
    term_3886 = _t1582
    consume_literal!(parser, ")")
    _t1583 = Proto.RelTerm(rel_term_type=OneOf(:term, term885))
    _t1584 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3886))
    _t1585 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1583, _t1584])
    result888 = _t1585
    record_span!(parser, span_start887, "Primitive")
    return result888
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start891 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1586 = parse_term(parser)
    term889 = _t1586
    _t1587 = parse_term(parser)
    term_3890 = _t1587
    consume_literal!(parser, ")")
    _t1588 = Proto.RelTerm(rel_term_type=OneOf(:term, term889))
    _t1589 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3890))
    _t1590 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1588, _t1589])
    result892 = _t1590
    record_span!(parser, span_start891, "Primitive")
    return result892
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start895 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1591 = parse_term(parser)
    term893 = _t1591
    _t1592 = parse_term(parser)
    term_3894 = _t1592
    consume_literal!(parser, ")")
    _t1593 = Proto.RelTerm(rel_term_type=OneOf(:term, term893))
    _t1594 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3894))
    _t1595 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1593, _t1594])
    result896 = _t1595
    record_span!(parser, span_start895, "Primitive")
    return result896
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start900 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1596 = parse_term(parser)
    term897 = _t1596
    _t1597 = parse_term(parser)
    term_3898 = _t1597
    _t1598 = parse_term(parser)
    term_4899 = _t1598
    consume_literal!(parser, ")")
    _t1599 = Proto.RelTerm(rel_term_type=OneOf(:term, term897))
    _t1600 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3898))
    _t1601 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4899))
    _t1602 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1599, _t1600, _t1601])
    result901 = _t1602
    record_span!(parser, span_start900, "Primitive")
    return result901
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start905 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1603 = parse_term(parser)
    term902 = _t1603
    _t1604 = parse_term(parser)
    term_3903 = _t1604
    _t1605 = parse_term(parser)
    term_4904 = _t1605
    consume_literal!(parser, ")")
    _t1606 = Proto.RelTerm(rel_term_type=OneOf(:term, term902))
    _t1607 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3903))
    _t1608 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4904))
    _t1609 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1606, _t1607, _t1608])
    result906 = _t1609
    record_span!(parser, span_start905, "Primitive")
    return result906
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start910 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1610 = parse_term(parser)
    term907 = _t1610
    _t1611 = parse_term(parser)
    term_3908 = _t1611
    _t1612 = parse_term(parser)
    term_4909 = _t1612
    consume_literal!(parser, ")")
    _t1613 = Proto.RelTerm(rel_term_type=OneOf(:term, term907))
    _t1614 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3908))
    _t1615 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4909))
    _t1616 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1613, _t1614, _t1615])
    result911 = _t1616
    record_span!(parser, span_start910, "Primitive")
    return result911
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start915 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1617 = parse_term(parser)
    term912 = _t1617
    _t1618 = parse_term(parser)
    term_3913 = _t1618
    _t1619 = parse_term(parser)
    term_4914 = _t1619
    consume_literal!(parser, ")")
    _t1620 = Proto.RelTerm(rel_term_type=OneOf(:term, term912))
    _t1621 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3913))
    _t1622 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4914))
    _t1623 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1620, _t1621, _t1622])
    result916 = _t1623
    record_span!(parser, span_start915, "Primitive")
    return result916
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start920 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1624 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1625 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1626 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1627 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1628 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1629 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1630 = 1
                            else
                                if match_lookahead_terminal(parser, "SYMBOL", 0)
                                    _t1631 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1632 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1633 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1634 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1635 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1636 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1637 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1638 = 1
                                                            else
                                                                _t1638 = -1
                                                            end
                                                            _t1637 = _t1638
                                                        end
                                                        _t1636 = _t1637
                                                    end
                                                    _t1635 = _t1636
                                                end
                                                _t1634 = _t1635
                                            end
                                            _t1633 = _t1634
                                        end
                                        _t1632 = _t1633
                                    end
                                    _t1631 = _t1632
                                end
                                _t1630 = _t1631
                            end
                            _t1629 = _t1630
                        end
                        _t1628 = _t1629
                    end
                    _t1627 = _t1628
                end
                _t1626 = _t1627
            end
            _t1625 = _t1626
        end
        _t1624 = _t1625
    end
    prediction917 = _t1624
    if prediction917 == 1
        _t1640 = parse_term(parser)
        term919 = _t1640
        _t1641 = Proto.RelTerm(rel_term_type=OneOf(:term, term919))
        _t1639 = _t1641
    else
        if prediction917 == 0
            _t1643 = parse_specialized_value(parser)
            specialized_value918 = _t1643
            _t1644 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value918))
            _t1642 = _t1644
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1639 = _t1642
    end
    result921 = _t1639
    record_span!(parser, span_start920, "RelTerm")
    return result921
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start923 = span_start(parser)
    consume_literal!(parser, "#")
    _t1645 = parse_value(parser)
    value922 = _t1645
    result924 = value922
    record_span!(parser, span_start923, "Value")
    return result924
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start930 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1646 = parse_name(parser)
    name925 = _t1646
    xs926 = Proto.RelTerm[]
    cond927 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond927
        _t1647 = parse_rel_term(parser)
        item928 = _t1647
        push!(xs926, item928)
        cond927 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    rel_terms929 = xs926
    consume_literal!(parser, ")")
    _t1648 = Proto.RelAtom(name=name925, terms=rel_terms929)
    result931 = _t1648
    record_span!(parser, span_start930, "RelAtom")
    return result931
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start934 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1649 = parse_term(parser)
    term932 = _t1649
    _t1650 = parse_term(parser)
    term_3933 = _t1650
    consume_literal!(parser, ")")
    _t1651 = Proto.Cast(input=term932, result=term_3933)
    result935 = _t1651
    record_span!(parser, span_start934, "Cast")
    return result935
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs936 = Proto.Attribute[]
    cond937 = match_lookahead_literal(parser, "(", 0)
    while cond937
        _t1652 = parse_attribute(parser)
        item938 = _t1652
        push!(xs936, item938)
        cond937 = match_lookahead_literal(parser, "(", 0)
    end
    attributes939 = xs936
    consume_literal!(parser, ")")
    return attributes939
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start945 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1653 = parse_name(parser)
    name940 = _t1653
    xs941 = Proto.Value[]
    cond942 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond942
        _t1654 = parse_value(parser)
        item943 = _t1654
        push!(xs941, item943)
        cond942 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    values944 = xs941
    consume_literal!(parser, ")")
    _t1655 = Proto.Attribute(name=name940, args=values944)
    result946 = _t1655
    record_span!(parser, span_start945, "Attribute")
    return result946
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs947 = Proto.RelationId[]
    cond948 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond948
        _t1656 = parse_relation_id(parser)
        item949 = _t1656
        push!(xs947, item949)
        cond948 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids950 = xs947
    _t1657 = parse_script(parser)
    script951 = _t1657
    consume_literal!(parser, ")")
    _t1658 = Proto.Algorithm(var"#global"=relation_ids950, body=script951)
    result953 = _t1658
    record_span!(parser, span_start952, "Algorithm")
    return result953
end

function parse_script(parser::ParserState)::Proto.Script
    span_start958 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs954 = Proto.Construct[]
    cond955 = match_lookahead_literal(parser, "(", 0)
    while cond955
        _t1659 = parse_construct(parser)
        item956 = _t1659
        push!(xs954, item956)
        cond955 = match_lookahead_literal(parser, "(", 0)
    end
    constructs957 = xs954
    consume_literal!(parser, ")")
    _t1660 = Proto.Script(constructs=constructs957)
    result959 = _t1660
    record_span!(parser, span_start958, "Script")
    return result959
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start963 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1662 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1663 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1664 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1665 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1666 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1667 = 1
                            else
                                _t1667 = -1
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
    else
        _t1661 = -1
    end
    prediction960 = _t1661
    if prediction960 == 1
        _t1669 = parse_instruction(parser)
        instruction962 = _t1669
        _t1670 = Proto.Construct(construct_type=OneOf(:instruction, instruction962))
        _t1668 = _t1670
    else
        if prediction960 == 0
            _t1672 = parse_loop(parser)
            loop961 = _t1672
            _t1673 = Proto.Construct(construct_type=OneOf(:loop, loop961))
            _t1671 = _t1673
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1668 = _t1671
    end
    result964 = _t1668
    record_span!(parser, span_start963, "Construct")
    return result964
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start967 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1674 = parse_init(parser)
    init965 = _t1674
    _t1675 = parse_script(parser)
    script966 = _t1675
    consume_literal!(parser, ")")
    _t1676 = Proto.Loop(init=init965, body=script966)
    result968 = _t1676
    record_span!(parser, span_start967, "Loop")
    return result968
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs969 = Proto.Instruction[]
    cond970 = match_lookahead_literal(parser, "(", 0)
    while cond970
        _t1677 = parse_instruction(parser)
        item971 = _t1677
        push!(xs969, item971)
        cond970 = match_lookahead_literal(parser, "(", 0)
    end
    instructions972 = xs969
    consume_literal!(parser, ")")
    return instructions972
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start979 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1679 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1680 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1681 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1682 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1683 = 0
                        else
                            _t1683 = -1
                        end
                        _t1682 = _t1683
                    end
                    _t1681 = _t1682
                end
                _t1680 = _t1681
            end
            _t1679 = _t1680
        end
        _t1678 = _t1679
    else
        _t1678 = -1
    end
    prediction973 = _t1678
    if prediction973 == 4
        _t1685 = parse_monus_def(parser)
        monus_def978 = _t1685
        _t1686 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def978))
        _t1684 = _t1686
    else
        if prediction973 == 3
            _t1688 = parse_monoid_def(parser)
            monoid_def977 = _t1688
            _t1689 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def977))
            _t1687 = _t1689
        else
            if prediction973 == 2
                _t1691 = parse_break(parser)
                break976 = _t1691
                _t1692 = Proto.Instruction(instr_type=OneOf(:var"#break", break976))
                _t1690 = _t1692
            else
                if prediction973 == 1
                    _t1694 = parse_upsert(parser)
                    upsert975 = _t1694
                    _t1695 = Proto.Instruction(instr_type=OneOf(:upsert, upsert975))
                    _t1693 = _t1695
                else
                    if prediction973 == 0
                        _t1697 = parse_assign(parser)
                        assign974 = _t1697
                        _t1698 = Proto.Instruction(instr_type=OneOf(:assign, assign974))
                        _t1696 = _t1698
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1693 = _t1696
                end
                _t1690 = _t1693
            end
            _t1687 = _t1690
        end
        _t1684 = _t1687
    end
    result980 = _t1684
    record_span!(parser, span_start979, "Instruction")
    return result980
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start984 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1699 = parse_relation_id(parser)
    relation_id981 = _t1699
    _t1700 = parse_abstraction(parser)
    abstraction982 = _t1700
    if match_lookahead_literal(parser, "(", 0)
        _t1702 = parse_attrs(parser)
        _t1701 = _t1702
    else
        _t1701 = nothing
    end
    attrs983 = _t1701
    consume_literal!(parser, ")")
    _t1703 = Proto.Assign(name=relation_id981, body=abstraction982, attrs=(!isnothing(attrs983) ? attrs983 : Proto.Attribute[]))
    result985 = _t1703
    record_span!(parser, span_start984, "Assign")
    return result985
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start989 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1704 = parse_relation_id(parser)
    relation_id986 = _t1704
    _t1705 = parse_abstraction_with_arity(parser)
    abstraction_with_arity987 = _t1705
    if match_lookahead_literal(parser, "(", 0)
        _t1707 = parse_attrs(parser)
        _t1706 = _t1707
    else
        _t1706 = nothing
    end
    attrs988 = _t1706
    consume_literal!(parser, ")")
    _t1708 = Proto.Upsert(name=relation_id986, body=abstraction_with_arity987[1], attrs=(!isnothing(attrs988) ? attrs988 : Proto.Attribute[]), value_arity=abstraction_with_arity987[2])
    result990 = _t1708
    record_span!(parser, span_start989, "Upsert")
    return result990
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1709 = parse_bindings(parser)
    bindings991 = _t1709
    _t1710 = parse_formula(parser)
    formula992 = _t1710
    consume_literal!(parser, ")")
    _t1711 = Proto.Abstraction(vars=vcat(bindings991[1], !isnothing(bindings991[2]) ? bindings991[2] : []), value=formula992)
    return (_t1711, length(bindings991[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start996 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1712 = parse_relation_id(parser)
    relation_id993 = _t1712
    _t1713 = parse_abstraction(parser)
    abstraction994 = _t1713
    if match_lookahead_literal(parser, "(", 0)
        _t1715 = parse_attrs(parser)
        _t1714 = _t1715
    else
        _t1714 = nothing
    end
    attrs995 = _t1714
    consume_literal!(parser, ")")
    _t1716 = Proto.Break(name=relation_id993, body=abstraction994, attrs=(!isnothing(attrs995) ? attrs995 : Proto.Attribute[]))
    result997 = _t1716
    record_span!(parser, span_start996, "Break")
    return result997
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1002 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1717 = parse_monoid(parser)
    monoid998 = _t1717
    _t1718 = parse_relation_id(parser)
    relation_id999 = _t1718
    _t1719 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1000 = _t1719
    if match_lookahead_literal(parser, "(", 0)
        _t1721 = parse_attrs(parser)
        _t1720 = _t1721
    else
        _t1720 = nothing
    end
    attrs1001 = _t1720
    consume_literal!(parser, ")")
    _t1722 = Proto.MonoidDef(monoid=monoid998, name=relation_id999, body=abstraction_with_arity1000[1], attrs=(!isnothing(attrs1001) ? attrs1001 : Proto.Attribute[]), value_arity=abstraction_with_arity1000[2])
    result1003 = _t1722
    record_span!(parser, span_start1002, "MonoidDef")
    return result1003
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1009 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1724 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1725 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1726 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1727 = 2
                    else
                        _t1727 = -1
                    end
                    _t1726 = _t1727
                end
                _t1725 = _t1726
            end
            _t1724 = _t1725
        end
        _t1723 = _t1724
    else
        _t1723 = -1
    end
    prediction1004 = _t1723
    if prediction1004 == 3
        _t1729 = parse_sum_monoid(parser)
        sum_monoid1008 = _t1729
        _t1730 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1008))
        _t1728 = _t1730
    else
        if prediction1004 == 2
            _t1732 = parse_max_monoid(parser)
            max_monoid1007 = _t1732
            _t1733 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1007))
            _t1731 = _t1733
        else
            if prediction1004 == 1
                _t1735 = parse_min_monoid(parser)
                min_monoid1006 = _t1735
                _t1736 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1006))
                _t1734 = _t1736
            else
                if prediction1004 == 0
                    _t1738 = parse_or_monoid(parser)
                    or_monoid1005 = _t1738
                    _t1739 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1005))
                    _t1737 = _t1739
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1734 = _t1737
            end
            _t1731 = _t1734
        end
        _t1728 = _t1731
    end
    result1010 = _t1728
    record_span!(parser, span_start1009, "Monoid")
    return result1010
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1011 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1740 = Proto.OrMonoid()
    result1012 = _t1740
    record_span!(parser, span_start1011, "OrMonoid")
    return result1012
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1014 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1741 = parse_type(parser)
    type1013 = _t1741
    consume_literal!(parser, ")")
    _t1742 = Proto.MinMonoid(var"#type"=type1013)
    result1015 = _t1742
    record_span!(parser, span_start1014, "MinMonoid")
    return result1015
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1017 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1743 = parse_type(parser)
    type1016 = _t1743
    consume_literal!(parser, ")")
    _t1744 = Proto.MaxMonoid(var"#type"=type1016)
    result1018 = _t1744
    record_span!(parser, span_start1017, "MaxMonoid")
    return result1018
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1020 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1745 = parse_type(parser)
    type1019 = _t1745
    consume_literal!(parser, ")")
    _t1746 = Proto.SumMonoid(var"#type"=type1019)
    result1021 = _t1746
    record_span!(parser, span_start1020, "SumMonoid")
    return result1021
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1026 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1747 = parse_monoid(parser)
    monoid1022 = _t1747
    _t1748 = parse_relation_id(parser)
    relation_id1023 = _t1748
    _t1749 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1024 = _t1749
    if match_lookahead_literal(parser, "(", 0)
        _t1751 = parse_attrs(parser)
        _t1750 = _t1751
    else
        _t1750 = nothing
    end
    attrs1025 = _t1750
    consume_literal!(parser, ")")
    _t1752 = Proto.MonusDef(monoid=monoid1022, name=relation_id1023, body=abstraction_with_arity1024[1], attrs=(!isnothing(attrs1025) ? attrs1025 : Proto.Attribute[]), value_arity=abstraction_with_arity1024[2])
    result1027 = _t1752
    record_span!(parser, span_start1026, "MonusDef")
    return result1027
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1032 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1753 = parse_relation_id(parser)
    relation_id1028 = _t1753
    _t1754 = parse_abstraction(parser)
    abstraction1029 = _t1754
    _t1755 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1030 = _t1755
    _t1756 = parse_functional_dependency_values(parser)
    functional_dependency_values1031 = _t1756
    consume_literal!(parser, ")")
    _t1757 = Proto.FunctionalDependency(guard=abstraction1029, keys=functional_dependency_keys1030, values=functional_dependency_values1031)
    _t1758 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1757), name=relation_id1028)
    result1033 = _t1758
    record_span!(parser, span_start1032, "Constraint")
    return result1033
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1034 = Proto.Var[]
    cond1035 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1035
        _t1759 = parse_var(parser)
        item1036 = _t1759
        push!(xs1034, item1036)
        cond1035 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1037 = xs1034
    consume_literal!(parser, ")")
    return vars1037
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1038 = Proto.Var[]
    cond1039 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1039
        _t1760 = parse_var(parser)
        item1040 = _t1760
        push!(xs1038, item1040)
        cond1039 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1041 = xs1038
    consume_literal!(parser, ")")
    return vars1041
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1047 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1762 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1763 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1764 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1765 = 1
                    else
                        _t1765 = -1
                    end
                    _t1764 = _t1765
                end
                _t1763 = _t1764
            end
            _t1762 = _t1763
        end
        _t1761 = _t1762
    else
        _t1761 = -1
    end
    prediction1042 = _t1761
    if prediction1042 == 3
        _t1767 = parse_iceberg_data(parser)
        iceberg_data1046 = _t1767
        _t1768 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1046))
        _t1766 = _t1768
    else
        if prediction1042 == 2
            _t1770 = parse_csv_data(parser)
            csv_data1045 = _t1770
            _t1771 = Proto.Data(data_type=OneOf(:csv_data, csv_data1045))
            _t1769 = _t1771
        else
            if prediction1042 == 1
                _t1773 = parse_betree_relation(parser)
                betree_relation1044 = _t1773
                _t1774 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1044))
                _t1772 = _t1774
            else
                if prediction1042 == 0
                    _t1776 = parse_edb(parser)
                    edb1043 = _t1776
                    _t1777 = Proto.Data(data_type=OneOf(:edb, edb1043))
                    _t1775 = _t1777
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1772 = _t1775
            end
            _t1769 = _t1772
        end
        _t1766 = _t1769
    end
    result1048 = _t1766
    record_span!(parser, span_start1047, "Data")
    return result1048
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1052 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1778 = parse_relation_id(parser)
    relation_id1049 = _t1778
    _t1779 = parse_edb_path(parser)
    edb_path1050 = _t1779
    _t1780 = parse_edb_types(parser)
    edb_types1051 = _t1780
    consume_literal!(parser, ")")
    _t1781 = Proto.EDB(target_id=relation_id1049, path=edb_path1050, types=edb_types1051)
    result1053 = _t1781
    record_span!(parser, span_start1052, "EDB")
    return result1053
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1054 = String[]
    cond1055 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1055
        item1056 = consume_terminal!(parser, "STRING")
        push!(xs1054, item1056)
        cond1055 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1057 = xs1054
    consume_literal!(parser, "]")
    return strings1057
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1058 = Proto.var"#Type"[]
    cond1059 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1059
        _t1782 = parse_type(parser)
        item1060 = _t1782
        push!(xs1058, item1060)
        cond1059 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1061 = xs1058
    consume_literal!(parser, "]")
    return types1061
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1064 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1783 = parse_relation_id(parser)
    relation_id1062 = _t1783
    _t1784 = parse_betree_info(parser)
    betree_info1063 = _t1784
    consume_literal!(parser, ")")
    _t1785 = Proto.BeTreeRelation(name=relation_id1062, relation_info=betree_info1063)
    result1065 = _t1785
    record_span!(parser, span_start1064, "BeTreeRelation")
    return result1065
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1069 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1786 = parse_betree_info_key_types(parser)
    betree_info_key_types1066 = _t1786
    _t1787 = parse_betree_info_value_types(parser)
    betree_info_value_types1067 = _t1787
    _t1788 = parse_config_dict(parser)
    config_dict1068 = _t1788
    consume_literal!(parser, ")")
    _t1789 = construct_betree_info(parser, betree_info_key_types1066, betree_info_value_types1067, config_dict1068)
    result1070 = _t1789
    record_span!(parser, span_start1069, "BeTreeInfo")
    return result1070
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1071 = Proto.var"#Type"[]
    cond1072 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1072
        _t1790 = parse_type(parser)
        item1073 = _t1790
        push!(xs1071, item1073)
        cond1072 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1074 = xs1071
    consume_literal!(parser, ")")
    return types1074
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1075 = Proto.var"#Type"[]
    cond1076 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1076
        _t1791 = parse_type(parser)
        item1077 = _t1791
        push!(xs1075, item1077)
        cond1076 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1078 = xs1075
    consume_literal!(parser, ")")
    return types1078
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1083 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1792 = parse_csvlocator(parser)
    csvlocator1079 = _t1792
    _t1793 = parse_csv_config(parser)
    csv_config1080 = _t1793
    _t1794 = parse_gnf_columns(parser)
    gnf_columns1081 = _t1794
    _t1795 = parse_csv_asof(parser)
    csv_asof1082 = _t1795
    consume_literal!(parser, ")")
    _t1796 = Proto.CSVData(locator=csvlocator1079, config=csv_config1080, columns=gnf_columns1081, asof=csv_asof1082)
    result1084 = _t1796
    record_span!(parser, span_start1083, "CSVData")
    return result1084
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1087 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1798 = parse_csv_locator_paths(parser)
        _t1797 = _t1798
    else
        _t1797 = nothing
    end
    csv_locator_paths1085 = _t1797
    if match_lookahead_literal(parser, "(", 0)
        _t1800 = parse_csv_locator_inline_data(parser)
        _t1799 = _t1800
    else
        _t1799 = nothing
    end
    csv_locator_inline_data1086 = _t1799
    consume_literal!(parser, ")")
    _t1801 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1085) ? csv_locator_paths1085 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1086) ? csv_locator_inline_data1086 : "")))
    result1088 = _t1801
    record_span!(parser, span_start1087, "CSVLocator")
    return result1088
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1089 = String[]
    cond1090 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1090
        item1091 = consume_terminal!(parser, "STRING")
        push!(xs1089, item1091)
        cond1090 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1092 = xs1089
    consume_literal!(parser, ")")
    return strings1092
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1093 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1093
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1095 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1802 = parse_config_dict(parser)
    config_dict1094 = _t1802
    consume_literal!(parser, ")")
    _t1803 = construct_csv_config(parser, config_dict1094)
    result1096 = _t1803
    record_span!(parser, span_start1095, "CSVConfig")
    return result1096
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1097 = Proto.GNFColumn[]
    cond1098 = match_lookahead_literal(parser, "(", 0)
    while cond1098
        _t1804 = parse_gnf_column(parser)
        item1099 = _t1804
        push!(xs1097, item1099)
        cond1098 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1100 = xs1097
    consume_literal!(parser, ")")
    return gnf_columns1100
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1107 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1805 = parse_gnf_column_path(parser)
    gnf_column_path1101 = _t1805
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1807 = parse_relation_id(parser)
        _t1806 = _t1807
    else
        _t1806 = nothing
    end
    relation_id1102 = _t1806
    consume_literal!(parser, "[")
    xs1103 = Proto.var"#Type"[]
    cond1104 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1104
        _t1808 = parse_type(parser)
        item1105 = _t1808
        push!(xs1103, item1105)
        cond1104 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1106 = xs1103
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1809 = Proto.GNFColumn(column_path=gnf_column_path1101, target_id=relation_id1102, types=types1106)
    result1108 = _t1809
    record_span!(parser, span_start1107, "GNFColumn")
    return result1108
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1810 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1811 = 0
        else
            _t1811 = -1
        end
        _t1810 = _t1811
    end
    prediction1109 = _t1810
    if prediction1109 == 1
        consume_literal!(parser, "[")
        xs1111 = String[]
        cond1112 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1112
            item1113 = consume_terminal!(parser, "STRING")
            push!(xs1111, item1113)
            cond1112 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1114 = xs1111
        consume_literal!(parser, "]")
        _t1812 = strings1114
    else
        if prediction1109 == 0
            string1110 = consume_terminal!(parser, "STRING")
            _t1813 = String[string1110]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1812 = _t1813
    end
    return _t1812
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1115 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1115
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1120 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1814 = parse_iceberg_locator(parser)
    iceberg_locator1116 = _t1814
    _t1815 = parse_iceberg_config(parser)
    iceberg_config1117 = _t1815
    _t1816 = parse_gnf_columns(parser)
    gnf_columns1118 = _t1816
    if match_lookahead_literal(parser, "(", 0)
        _t1818 = parse_iceberg_to_snapshot(parser)
        _t1817 = _t1818
    else
        _t1817 = nothing
    end
    iceberg_to_snapshot1119 = _t1817
    consume_literal!(parser, ")")
    _t1819 = Proto.IcebergData(locator=iceberg_locator1116, config=iceberg_config1117, columns=gnf_columns1118, to_snapshot=iceberg_to_snapshot1119)
    result1121 = _t1819
    record_span!(parser, span_start1120, "IcebergData")
    return result1121
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1125 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    string1122 = consume_terminal!(parser, "STRING")
    _t1820 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1123 = _t1820
    string_41124 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    _t1821 = Proto.IcebergLocator(table_name=string1122, namespace=iceberg_locator_namespace1123, warehouse=string_41124)
    result1126 = _t1821
    record_span!(parser, span_start1125, "IcebergLocator")
    return result1126
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1127 = String[]
    cond1128 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1128
        item1129 = consume_terminal!(parser, "STRING")
        push!(xs1127, item1129)
        cond1128 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1130 = xs1127
    consume_literal!(parser, ")")
    return strings1130
end

function parse_iceberg_config(parser::ParserState)::Proto.IcebergConfig
    span_start1135 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_config")
    string1131 = consume_terminal!(parser, "STRING")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1823 = parse_iceberg_config_scope(parser)
        _t1822 = _t1823
    else
        _t1822 = nothing
    end
    iceberg_config_scope1132 = _t1822
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "properties", 1))
        _t1825 = parse_iceberg_config_properties(parser)
        _t1824 = _t1825
    else
        _t1824 = nothing
    end
    iceberg_config_properties1133 = _t1824
    if match_lookahead_literal(parser, "(", 0)
        _t1827 = parse_iceberg_config_credentials(parser)
        _t1826 = _t1827
    else
        _t1826 = nothing
    end
    iceberg_config_credentials1134 = _t1826
    consume_literal!(parser, ")")
    _t1828 = construct_iceberg_config(parser, string1131, iceberg_config_scope1132, iceberg_config_properties1133, iceberg_config_credentials1134)
    result1136 = _t1828
    record_span!(parser, span_start1135, "IcebergConfig")
    return result1136
end

function parse_iceberg_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1137 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1137
end

function parse_iceberg_config_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1138 = Tuple{String, String}[]
    cond1139 = match_lookahead_literal(parser, "(", 0)
    while cond1139
        _t1829 = parse_iceberg_kv_pair(parser)
        item1140 = _t1829
        push!(xs1138, item1140)
        cond1139 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_kv_pairs1141 = xs1138
    consume_literal!(parser, ")")
    return iceberg_kv_pairs1141
end

function parse_iceberg_kv_pair(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    string1142 = consume_terminal!(parser, "STRING")
    string_21143 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1142, string_21143,)
end

function parse_iceberg_config_credentials(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "credentials")
    xs1144 = Tuple{String, String}[]
    cond1145 = match_lookahead_literal(parser, "(", 0)
    while cond1145
        _t1830 = parse_iceberg_kv_pair(parser)
        item1146 = _t1830
        push!(xs1144, item1146)
        cond1145 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_kv_pairs1147 = xs1144
    consume_literal!(parser, ")")
    return iceberg_kv_pairs1147
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1148 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1148
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1150 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1831 = parse_fragment_id(parser)
    fragment_id1149 = _t1831
    consume_literal!(parser, ")")
    _t1832 = Proto.Undefine(fragment_id=fragment_id1149)
    result1151 = _t1832
    record_span!(parser, span_start1150, "Undefine")
    return result1151
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1156 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1152 = Proto.RelationId[]
    cond1153 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1153
        _t1833 = parse_relation_id(parser)
        item1154 = _t1833
        push!(xs1152, item1154)
        cond1153 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1155 = xs1152
    consume_literal!(parser, ")")
    _t1834 = Proto.Context(relations=relation_ids1155)
    result1157 = _t1834
    record_span!(parser, span_start1156, "Context")
    return result1157
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1162 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1158 = Proto.SnapshotMapping[]
    cond1159 = match_lookahead_literal(parser, "[", 0)
    while cond1159
        _t1835 = parse_snapshot_mapping(parser)
        item1160 = _t1835
        push!(xs1158, item1160)
        cond1159 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1161 = xs1158
    consume_literal!(parser, ")")
    _t1836 = Proto.Snapshot(mappings=snapshot_mappings1161)
    result1163 = _t1836
    record_span!(parser, span_start1162, "Snapshot")
    return result1163
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1166 = span_start(parser)
    _t1837 = parse_edb_path(parser)
    edb_path1164 = _t1837
    _t1838 = parse_relation_id(parser)
    relation_id1165 = _t1838
    _t1839 = Proto.SnapshotMapping(destination_path=edb_path1164, source_relation=relation_id1165)
    result1167 = _t1839
    record_span!(parser, span_start1166, "SnapshotMapping")
    return result1167
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1168 = Proto.Read[]
    cond1169 = match_lookahead_literal(parser, "(", 0)
    while cond1169
        _t1840 = parse_read(parser)
        item1170 = _t1840
        push!(xs1168, item1170)
        cond1169 = match_lookahead_literal(parser, "(", 0)
    end
    reads1171 = xs1168
    consume_literal!(parser, ")")
    return reads1171
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1178 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1842 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1843 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1844 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1845 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1846 = 3
                        else
                            _t1846 = -1
                        end
                        _t1845 = _t1846
                    end
                    _t1844 = _t1845
                end
                _t1843 = _t1844
            end
            _t1842 = _t1843
        end
        _t1841 = _t1842
    else
        _t1841 = -1
    end
    prediction1172 = _t1841
    if prediction1172 == 4
        _t1848 = parse_export(parser)
        export1177 = _t1848
        _t1849 = Proto.Read(read_type=OneOf(:var"#export", export1177))
        _t1847 = _t1849
    else
        if prediction1172 == 3
            _t1851 = parse_abort(parser)
            abort1176 = _t1851
            _t1852 = Proto.Read(read_type=OneOf(:abort, abort1176))
            _t1850 = _t1852
        else
            if prediction1172 == 2
                _t1854 = parse_what_if(parser)
                what_if1175 = _t1854
                _t1855 = Proto.Read(read_type=OneOf(:what_if, what_if1175))
                _t1853 = _t1855
            else
                if prediction1172 == 1
                    _t1857 = parse_output(parser)
                    output1174 = _t1857
                    _t1858 = Proto.Read(read_type=OneOf(:output, output1174))
                    _t1856 = _t1858
                else
                    if prediction1172 == 0
                        _t1860 = parse_demand(parser)
                        demand1173 = _t1860
                        _t1861 = Proto.Read(read_type=OneOf(:demand, demand1173))
                        _t1859 = _t1861
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1856 = _t1859
                end
                _t1853 = _t1856
            end
            _t1850 = _t1853
        end
        _t1847 = _t1850
    end
    result1179 = _t1847
    record_span!(parser, span_start1178, "Read")
    return result1179
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1181 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1862 = parse_relation_id(parser)
    relation_id1180 = _t1862
    consume_literal!(parser, ")")
    _t1863 = Proto.Demand(relation_id=relation_id1180)
    result1182 = _t1863
    record_span!(parser, span_start1181, "Demand")
    return result1182
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1185 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1864 = parse_name(parser)
    name1183 = _t1864
    _t1865 = parse_relation_id(parser)
    relation_id1184 = _t1865
    consume_literal!(parser, ")")
    _t1866 = Proto.Output(name=name1183, relation_id=relation_id1184)
    result1186 = _t1866
    record_span!(parser, span_start1185, "Output")
    return result1186
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1189 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1867 = parse_name(parser)
    name1187 = _t1867
    _t1868 = parse_epoch(parser)
    epoch1188 = _t1868
    consume_literal!(parser, ")")
    _t1869 = Proto.WhatIf(branch=name1187, epoch=epoch1188)
    result1190 = _t1869
    record_span!(parser, span_start1189, "WhatIf")
    return result1190
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1193 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1871 = parse_name(parser)
        _t1870 = _t1871
    else
        _t1870 = nothing
    end
    name1191 = _t1870
    _t1872 = parse_relation_id(parser)
    relation_id1192 = _t1872
    consume_literal!(parser, ")")
    _t1873 = Proto.Abort(name=(!isnothing(name1191) ? name1191 : "abort"), relation_id=relation_id1192)
    result1194 = _t1873
    record_span!(parser, span_start1193, "Abort")
    return result1194
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1196 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1874 = parse_export_csv_config(parser)
    export_csv_config1195 = _t1874
    consume_literal!(parser, ")")
    _t1875 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1195))
    result1197 = _t1875
    record_span!(parser, span_start1196, "Export")
    return result1197
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1205 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1877 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1878 = 1
            else
                _t1878 = -1
            end
            _t1877 = _t1878
        end
        _t1876 = _t1877
    else
        _t1876 = -1
    end
    prediction1198 = _t1876
    if prediction1198 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1880 = parse_export_csv_path(parser)
        export_csv_path1202 = _t1880
        _t1881 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1203 = _t1881
        _t1882 = parse_config_dict(parser)
        config_dict1204 = _t1882
        consume_literal!(parser, ")")
        _t1883 = construct_export_csv_config(parser, export_csv_path1202, export_csv_columns_list1203, config_dict1204)
        _t1879 = _t1883
    else
        if prediction1198 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1885 = parse_export_csv_path(parser)
            export_csv_path1199 = _t1885
            _t1886 = parse_export_csv_source(parser)
            export_csv_source1200 = _t1886
            _t1887 = parse_csv_config(parser)
            csv_config1201 = _t1887
            consume_literal!(parser, ")")
            _t1888 = construct_export_csv_config_with_source(parser, export_csv_path1199, export_csv_source1200, csv_config1201)
            _t1884 = _t1888
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1879 = _t1884
    end
    result1206 = _t1879
    record_span!(parser, span_start1205, "ExportCSVConfig")
    return result1206
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1207 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1207
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1214 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1890 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1891 = 0
            else
                _t1891 = -1
            end
            _t1890 = _t1891
        end
        _t1889 = _t1890
    else
        _t1889 = -1
    end
    prediction1208 = _t1889
    if prediction1208 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1893 = parse_relation_id(parser)
        relation_id1213 = _t1893
        consume_literal!(parser, ")")
        _t1894 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1213))
        _t1892 = _t1894
    else
        if prediction1208 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1209 = Proto.ExportCSVColumn[]
            cond1210 = match_lookahead_literal(parser, "(", 0)
            while cond1210
                _t1896 = parse_export_csv_column(parser)
                item1211 = _t1896
                push!(xs1209, item1211)
                cond1210 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1212 = xs1209
            consume_literal!(parser, ")")
            _t1897 = Proto.ExportCSVColumns(columns=export_csv_columns1212)
            _t1898 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1897))
            _t1895 = _t1898
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1892 = _t1895
    end
    result1215 = _t1892
    record_span!(parser, span_start1214, "ExportCSVSource")
    return result1215
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1218 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1216 = consume_terminal!(parser, "STRING")
    _t1899 = parse_relation_id(parser)
    relation_id1217 = _t1899
    consume_literal!(parser, ")")
    _t1900 = Proto.ExportCSVColumn(column_name=string1216, column_data=relation_id1217)
    result1219 = _t1900
    record_span!(parser, span_start1218, "ExportCSVColumn")
    return result1219
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1220 = Proto.ExportCSVColumn[]
    cond1221 = match_lookahead_literal(parser, "(", 0)
    while cond1221
        _t1901 = parse_export_csv_column(parser)
        item1222 = _t1901
        push!(xs1220, item1222)
        cond1221 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1223 = xs1220
    consume_literal!(parser, ")")
    return export_csv_columns1223
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
