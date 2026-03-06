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
        _t1888 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1889 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1890 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1891 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1892 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1893 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1894 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1895 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1896 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1897 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1897
    _t1898 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1898
    _t1899 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1899
    _t1900 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1900
    _t1901 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1901
    _t1902 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1902
    _t1903 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1903
    _t1904 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1904
    _t1905 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1905
    _t1906 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1906
    _t1907 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1907
    _t1908 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t1908
    _t1909 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t1909
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1910 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1910
    _t1911 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1911
    _t1912 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1912
    _t1913 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1913
    _t1914 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1914
    _t1915 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1915
    _t1916 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1916
    _t1917 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1917
    _t1918 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1918
    _t1919 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1919
    _t1920 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1920
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1921 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1921
    _t1922 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1922
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
    _t1923 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1923
    _t1924 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1924
    _t1925 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1925
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1926 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1926
    _t1927 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1927
    _t1928 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1928
    _t1929 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1929
    _t1930 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1930
    _t1931 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1931
    _t1932 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1932
    _t1933 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1933
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1934 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1934
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start605 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1199 = parse_configure(parser)
        _t1198 = _t1199
    else
        _t1198 = nothing
    end
    configure599 = _t1198
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1201 = parse_sync(parser)
        _t1200 = _t1201
    else
        _t1200 = nothing
    end
    sync600 = _t1200
    xs601 = Proto.Epoch[]
    cond602 = match_lookahead_literal(parser, "(", 0)
    while cond602
        _t1202 = parse_epoch(parser)
        item603 = _t1202
        push!(xs601, item603)
        cond602 = match_lookahead_literal(parser, "(", 0)
    end
    epochs604 = xs601
    consume_literal!(parser, ")")
    _t1203 = default_configure(parser)
    _t1204 = Proto.Transaction(epochs=epochs604, configure=(!isnothing(configure599) ? configure599 : _t1203), sync=sync600)
    result606 = _t1204
    record_span!(parser, span_start605, "Transaction")
    return result606
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start608 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1205 = parse_config_dict(parser)
    config_dict607 = _t1205
    consume_literal!(parser, ")")
    _t1206 = construct_configure(parser, config_dict607)
    result609 = _t1206
    record_span!(parser, span_start608, "Configure")
    return result609
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs610 = Tuple{String, Proto.Value}[]
    cond611 = match_lookahead_literal(parser, ":", 0)
    while cond611
        _t1207 = parse_config_key_value(parser)
        item612 = _t1207
        push!(xs610, item612)
        cond611 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values613 = xs610
    consume_literal!(parser, "}")
    return config_key_values613
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol614 = consume_terminal!(parser, "SYMBOL")
    _t1208 = parse_raw_value(parser)
    raw_value615 = _t1208
    return (symbol614, raw_value615,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start628 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1209 = 11
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1210 = 10
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1211 = 11
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1213 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1214 = 0
                        else
                            _t1214 = -1
                        end
                        _t1213 = _t1214
                    end
                    _t1212 = _t1213
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1215 = 7
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1216 = 2
                        else
                            if match_lookahead_terminal(parser, "INT32", 0)
                                _t1217 = 3
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1218 = 8
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1219 = 4
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT32", 0)
                                            _t1220 = 5
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1221 = 6
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1222 = 9
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
                        end
                        _t1215 = _t1216
                    end
                    _t1212 = _t1215
                end
                _t1211 = _t1212
            end
            _t1210 = _t1211
        end
        _t1209 = _t1210
    end
    prediction616 = _t1209
    if prediction616 == 11
        _t1224 = parse_boolean_value(parser)
        boolean_value627 = _t1224
        _t1225 = Proto.Value(value=OneOf(:boolean_value, boolean_value627))
        _t1223 = _t1225
    else
        if prediction616 == 10
            consume_literal!(parser, "missing")
            _t1227 = Proto.MissingValue()
            _t1228 = Proto.Value(value=OneOf(:missing_value, _t1227))
            _t1226 = _t1228
        else
            if prediction616 == 9
                decimal626 = consume_terminal!(parser, "DECIMAL")
                _t1230 = Proto.Value(value=OneOf(:decimal_value, decimal626))
                _t1229 = _t1230
            else
                if prediction616 == 8
                    int128625 = consume_terminal!(parser, "INT128")
                    _t1232 = Proto.Value(value=OneOf(:int128_value, int128625))
                    _t1231 = _t1232
                else
                    if prediction616 == 7
                        uint128624 = consume_terminal!(parser, "UINT128")
                        _t1234 = Proto.Value(value=OneOf(:uint128_value, uint128624))
                        _t1233 = _t1234
                    else
                        if prediction616 == 6
                            float623 = consume_terminal!(parser, "FLOAT")
                            _t1236 = Proto.Value(value=OneOf(:float_value, float623))
                            _t1235 = _t1236
                        else
                            if prediction616 == 5
                                float32622 = consume_terminal!(parser, "FLOAT32")
                                _t1238 = Proto.Value(value=OneOf(:float32_value, float32622))
                                _t1237 = _t1238
                            else
                                if prediction616 == 4
                                    int621 = consume_terminal!(parser, "INT")
                                    _t1240 = Proto.Value(value=OneOf(:int_value, int621))
                                    _t1239 = _t1240
                                else
                                    if prediction616 == 3
                                        int32620 = consume_terminal!(parser, "INT32")
                                        _t1242 = Proto.Value(value=OneOf(:int32_value, int32620))
                                        _t1241 = _t1242
                                    else
                                        if prediction616 == 2
                                            string619 = consume_terminal!(parser, "STRING")
                                            _t1244 = Proto.Value(value=OneOf(:string_value, string619))
                                            _t1243 = _t1244
                                        else
                                            if prediction616 == 1
                                                _t1246 = parse_raw_datetime(parser)
                                                raw_datetime618 = _t1246
                                                _t1247 = Proto.Value(value=OneOf(:datetime_value, raw_datetime618))
                                                _t1245 = _t1247
                                            else
                                                if prediction616 == 0
                                                    _t1249 = parse_raw_date(parser)
                                                    raw_date617 = _t1249
                                                    _t1250 = Proto.Value(value=OneOf(:date_value, raw_date617))
                                                    _t1248 = _t1250
                                                else
                                                    throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                end
                                                _t1245 = _t1248
                                            end
                                            _t1243 = _t1245
                                        end
                                        _t1241 = _t1243
                                    end
                                    _t1239 = _t1241
                                end
                                _t1237 = _t1239
                            end
                            _t1235 = _t1237
                        end
                        _t1233 = _t1235
                    end
                    _t1231 = _t1233
                end
                _t1229 = _t1231
            end
            _t1226 = _t1229
        end
        _t1223 = _t1226
    end
    result629 = _t1223
    record_span!(parser, span_start628, "Value")
    return result629
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start633 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int630 = consume_terminal!(parser, "INT")
    int_3631 = consume_terminal!(parser, "INT")
    int_4632 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1251 = Proto.DateValue(year=Int32(int630), month=Int32(int_3631), day=Int32(int_4632))
    result634 = _t1251
    record_span!(parser, span_start633, "DateValue")
    return result634
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start642 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int635 = consume_terminal!(parser, "INT")
    int_3636 = consume_terminal!(parser, "INT")
    int_4637 = consume_terminal!(parser, "INT")
    int_5638 = consume_terminal!(parser, "INT")
    int_6639 = consume_terminal!(parser, "INT")
    int_7640 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1252 = consume_terminal!(parser, "INT")
    else
        _t1252 = nothing
    end
    int_8641 = _t1252
    consume_literal!(parser, ")")
    _t1253 = Proto.DateTimeValue(year=Int32(int635), month=Int32(int_3636), day=Int32(int_4637), hour=Int32(int_5638), minute=Int32(int_6639), second=Int32(int_7640), microsecond=Int32((!isnothing(int_8641) ? int_8641 : 0)))
    result643 = _t1253
    record_span!(parser, span_start642, "DateTimeValue")
    return result643
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1254 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1255 = 1
        else
            _t1255 = -1
        end
        _t1254 = _t1255
    end
    prediction644 = _t1254
    if prediction644 == 1
        consume_literal!(parser, "false")
        _t1256 = false
    else
        if prediction644 == 0
            consume_literal!(parser, "true")
            _t1257 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1256 = _t1257
    end
    return _t1256
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start649 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs645 = Proto.FragmentId[]
    cond646 = match_lookahead_literal(parser, ":", 0)
    while cond646
        _t1258 = parse_fragment_id(parser)
        item647 = _t1258
        push!(xs645, item647)
        cond646 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids648 = xs645
    consume_literal!(parser, ")")
    _t1259 = Proto.Sync(fragments=fragment_ids648)
    result650 = _t1259
    record_span!(parser, span_start649, "Sync")
    return result650
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start652 = span_start(parser)
    consume_literal!(parser, ":")
    symbol651 = consume_terminal!(parser, "SYMBOL")
    result653 = Proto.FragmentId(Vector{UInt8}(symbol651))
    record_span!(parser, span_start652, "FragmentId")
    return result653
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start656 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1261 = parse_epoch_writes(parser)
        _t1260 = _t1261
    else
        _t1260 = nothing
    end
    epoch_writes654 = _t1260
    if match_lookahead_literal(parser, "(", 0)
        _t1263 = parse_epoch_reads(parser)
        _t1262 = _t1263
    else
        _t1262 = nothing
    end
    epoch_reads655 = _t1262
    consume_literal!(parser, ")")
    _t1264 = Proto.Epoch(writes=(!isnothing(epoch_writes654) ? epoch_writes654 : Proto.Write[]), reads=(!isnothing(epoch_reads655) ? epoch_reads655 : Proto.Read[]))
    result657 = _t1264
    record_span!(parser, span_start656, "Epoch")
    return result657
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs658 = Proto.Write[]
    cond659 = match_lookahead_literal(parser, "(", 0)
    while cond659
        _t1265 = parse_write(parser)
        item660 = _t1265
        push!(xs658, item660)
        cond659 = match_lookahead_literal(parser, "(", 0)
    end
    writes661 = xs658
    consume_literal!(parser, ")")
    return writes661
end

function parse_write(parser::ParserState)::Proto.Write
    span_start667 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1267 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1268 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1269 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1270 = 2
                    else
                        _t1270 = -1
                    end
                    _t1269 = _t1270
                end
                _t1268 = _t1269
            end
            _t1267 = _t1268
        end
        _t1266 = _t1267
    else
        _t1266 = -1
    end
    prediction662 = _t1266
    if prediction662 == 3
        _t1272 = parse_snapshot(parser)
        snapshot666 = _t1272
        _t1273 = Proto.Write(write_type=OneOf(:snapshot, snapshot666))
        _t1271 = _t1273
    else
        if prediction662 == 2
            _t1275 = parse_context(parser)
            context665 = _t1275
            _t1276 = Proto.Write(write_type=OneOf(:context, context665))
            _t1274 = _t1276
        else
            if prediction662 == 1
                _t1278 = parse_undefine(parser)
                undefine664 = _t1278
                _t1279 = Proto.Write(write_type=OneOf(:undefine, undefine664))
                _t1277 = _t1279
            else
                if prediction662 == 0
                    _t1281 = parse_define(parser)
                    define663 = _t1281
                    _t1282 = Proto.Write(write_type=OneOf(:define, define663))
                    _t1280 = _t1282
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1277 = _t1280
            end
            _t1274 = _t1277
        end
        _t1271 = _t1274
    end
    result668 = _t1271
    record_span!(parser, span_start667, "Write")
    return result668
end

function parse_define(parser::ParserState)::Proto.Define
    span_start670 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1283 = parse_fragment(parser)
    fragment669 = _t1283
    consume_literal!(parser, ")")
    _t1284 = Proto.Define(fragment=fragment669)
    result671 = _t1284
    record_span!(parser, span_start670, "Define")
    return result671
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start677 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1285 = parse_new_fragment_id(parser)
    new_fragment_id672 = _t1285
    xs673 = Proto.Declaration[]
    cond674 = match_lookahead_literal(parser, "(", 0)
    while cond674
        _t1286 = parse_declaration(parser)
        item675 = _t1286
        push!(xs673, item675)
        cond674 = match_lookahead_literal(parser, "(", 0)
    end
    declarations676 = xs673
    consume_literal!(parser, ")")
    result678 = construct_fragment(parser, new_fragment_id672, declarations676)
    record_span!(parser, span_start677, "Fragment")
    return result678
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start680 = span_start(parser)
    _t1287 = parse_fragment_id(parser)
    fragment_id679 = _t1287
    start_fragment!(parser, fragment_id679)
    result681 = fragment_id679
    record_span!(parser, span_start680, "FragmentId")
    return result681
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start687 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "functional_dependency", 1)
            _t1289 = 2
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1290 = 3
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1291 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1292 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1293 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1294 = 1
                            else
                                _t1294 = -1
                            end
                            _t1293 = _t1294
                        end
                        _t1292 = _t1293
                    end
                    _t1291 = _t1292
                end
                _t1290 = _t1291
            end
            _t1289 = _t1290
        end
        _t1288 = _t1289
    else
        _t1288 = -1
    end
    prediction682 = _t1288
    if prediction682 == 3
        _t1296 = parse_data(parser)
        data686 = _t1296
        _t1297 = Proto.Declaration(declaration_type=OneOf(:data, data686))
        _t1295 = _t1297
    else
        if prediction682 == 2
            _t1299 = parse_constraint(parser)
            constraint685 = _t1299
            _t1300 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint685))
            _t1298 = _t1300
        else
            if prediction682 == 1
                _t1302 = parse_algorithm(parser)
                algorithm684 = _t1302
                _t1303 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm684))
                _t1301 = _t1303
            else
                if prediction682 == 0
                    _t1305 = parse_def(parser)
                    def683 = _t1305
                    _t1306 = Proto.Declaration(declaration_type=OneOf(:def, def683))
                    _t1304 = _t1306
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1301 = _t1304
            end
            _t1298 = _t1301
        end
        _t1295 = _t1298
    end
    result688 = _t1295
    record_span!(parser, span_start687, "Declaration")
    return result688
end

function parse_def(parser::ParserState)::Proto.Def
    span_start692 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1307 = parse_relation_id(parser)
    relation_id689 = _t1307
    _t1308 = parse_abstraction(parser)
    abstraction690 = _t1308
    if match_lookahead_literal(parser, "(", 0)
        _t1310 = parse_attrs(parser)
        _t1309 = _t1310
    else
        _t1309 = nothing
    end
    attrs691 = _t1309
    consume_literal!(parser, ")")
    _t1311 = Proto.Def(name=relation_id689, body=abstraction690, attrs=(!isnothing(attrs691) ? attrs691 : Proto.Attribute[]))
    result693 = _t1311
    record_span!(parser, span_start692, "Def")
    return result693
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start697 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1312 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1313 = 1
        else
            _t1313 = -1
        end
        _t1312 = _t1313
    end
    prediction694 = _t1312
    if prediction694 == 1
        uint128696 = consume_terminal!(parser, "UINT128")
        _t1314 = Proto.RelationId(uint128696.low, uint128696.high)
    else
        if prediction694 == 0
            consume_literal!(parser, ":")
            symbol695 = consume_terminal!(parser, "SYMBOL")
            _t1315 = relation_id_from_string(parser, symbol695)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1314 = _t1315
    end
    result698 = _t1314
    record_span!(parser, span_start697, "RelationId")
    return result698
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start701 = span_start(parser)
    consume_literal!(parser, "(")
    _t1316 = parse_bindings(parser)
    bindings699 = _t1316
    _t1317 = parse_formula(parser)
    formula700 = _t1317
    consume_literal!(parser, ")")
    _t1318 = Proto.Abstraction(vars=vcat(bindings699[1], !isnothing(bindings699[2]) ? bindings699[2] : []), value=formula700)
    result702 = _t1318
    record_span!(parser, span_start701, "Abstraction")
    return result702
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs703 = Proto.Binding[]
    cond704 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond704
        _t1319 = parse_binding(parser)
        item705 = _t1319
        push!(xs703, item705)
        cond704 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings706 = xs703
    if match_lookahead_literal(parser, "|", 0)
        _t1321 = parse_value_bindings(parser)
        _t1320 = _t1321
    else
        _t1320 = nothing
    end
    value_bindings707 = _t1320
    consume_literal!(parser, "]")
    return (bindings706, (!isnothing(value_bindings707) ? value_bindings707 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start710 = span_start(parser)
    symbol708 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1322 = parse_type(parser)
    type709 = _t1322
    _t1323 = Proto.Var(name=symbol708)
    _t1324 = Proto.Binding(var=_t1323, var"#type"=type709)
    result711 = _t1324
    record_span!(parser, span_start710, "Binding")
    return result711
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start726 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1325 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t1326 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t1327 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t1328 = 8
                else
                    if match_lookahead_literal(parser, "INT32", 0)
                        _t1329 = 11
                    else
                        if match_lookahead_literal(parser, "INT128", 0)
                            _t1330 = 5
                        else
                            if match_lookahead_literal(parser, "INT", 0)
                                _t1331 = 2
                            else
                                if match_lookahead_literal(parser, "FLOAT32", 0)
                                    _t1332 = 12
                                else
                                    if match_lookahead_literal(parser, "FLOAT", 0)
                                        _t1333 = 3
                                    else
                                        if match_lookahead_literal(parser, "DATETIME", 0)
                                            _t1334 = 7
                                        else
                                            if match_lookahead_literal(parser, "DATE", 0)
                                                _t1335 = 6
                                            else
                                                if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                    _t1336 = 10
                                                else
                                                    if match_lookahead_literal(parser, "(", 0)
                                                        _t1337 = 9
                                                    else
                                                        _t1337 = -1
                                                    end
                                                    _t1336 = _t1337
                                                end
                                                _t1335 = _t1336
                                            end
                                            _t1334 = _t1335
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
                    _t1328 = _t1329
                end
                _t1327 = _t1328
            end
            _t1326 = _t1327
        end
        _t1325 = _t1326
    end
    prediction712 = _t1325
    if prediction712 == 12
        _t1339 = parse_float32_type(parser)
        float32_type725 = _t1339
        _t1340 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type725))
        _t1338 = _t1340
    else
        if prediction712 == 11
            _t1342 = parse_int32_type(parser)
            int32_type724 = _t1342
            _t1343 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type724))
            _t1341 = _t1343
        else
            if prediction712 == 10
                _t1345 = parse_boolean_type(parser)
                boolean_type723 = _t1345
                _t1346 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type723))
                _t1344 = _t1346
            else
                if prediction712 == 9
                    _t1348 = parse_decimal_type(parser)
                    decimal_type722 = _t1348
                    _t1349 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type722))
                    _t1347 = _t1349
                else
                    if prediction712 == 8
                        _t1351 = parse_missing_type(parser)
                        missing_type721 = _t1351
                        _t1352 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type721))
                        _t1350 = _t1352
                    else
                        if prediction712 == 7
                            _t1354 = parse_datetime_type(parser)
                            datetime_type720 = _t1354
                            _t1355 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type720))
                            _t1353 = _t1355
                        else
                            if prediction712 == 6
                                _t1357 = parse_date_type(parser)
                                date_type719 = _t1357
                                _t1358 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type719))
                                _t1356 = _t1358
                            else
                                if prediction712 == 5
                                    _t1360 = parse_int128_type(parser)
                                    int128_type718 = _t1360
                                    _t1361 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type718))
                                    _t1359 = _t1361
                                else
                                    if prediction712 == 4
                                        _t1363 = parse_uint128_type(parser)
                                        uint128_type717 = _t1363
                                        _t1364 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type717))
                                        _t1362 = _t1364
                                    else
                                        if prediction712 == 3
                                            _t1366 = parse_float_type(parser)
                                            float_type716 = _t1366
                                            _t1367 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type716))
                                            _t1365 = _t1367
                                        else
                                            if prediction712 == 2
                                                _t1369 = parse_int_type(parser)
                                                int_type715 = _t1369
                                                _t1370 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type715))
                                                _t1368 = _t1370
                                            else
                                                if prediction712 == 1
                                                    _t1372 = parse_string_type(parser)
                                                    string_type714 = _t1372
                                                    _t1373 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type714))
                                                    _t1371 = _t1373
                                                else
                                                    if prediction712 == 0
                                                        _t1375 = parse_unspecified_type(parser)
                                                        unspecified_type713 = _t1375
                                                        _t1376 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type713))
                                                        _t1374 = _t1376
                                                    else
                                                        throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1371 = _t1374
                                                end
                                                _t1368 = _t1371
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
    result727 = _t1338
    record_span!(parser, span_start726, "Type")
    return result727
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start728 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1377 = Proto.UnspecifiedType()
    result729 = _t1377
    record_span!(parser, span_start728, "UnspecifiedType")
    return result729
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start730 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1378 = Proto.StringType()
    result731 = _t1378
    record_span!(parser, span_start730, "StringType")
    return result731
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start732 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1379 = Proto.IntType()
    result733 = _t1379
    record_span!(parser, span_start732, "IntType")
    return result733
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start734 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1380 = Proto.FloatType()
    result735 = _t1380
    record_span!(parser, span_start734, "FloatType")
    return result735
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start736 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1381 = Proto.UInt128Type()
    result737 = _t1381
    record_span!(parser, span_start736, "UInt128Type")
    return result737
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start738 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1382 = Proto.Int128Type()
    result739 = _t1382
    record_span!(parser, span_start738, "Int128Type")
    return result739
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start740 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1383 = Proto.DateType()
    result741 = _t1383
    record_span!(parser, span_start740, "DateType")
    return result741
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start742 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1384 = Proto.DateTimeType()
    result743 = _t1384
    record_span!(parser, span_start742, "DateTimeType")
    return result743
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start744 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1385 = Proto.MissingType()
    result745 = _t1385
    record_span!(parser, span_start744, "MissingType")
    return result745
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start748 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int746 = consume_terminal!(parser, "INT")
    int_3747 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1386 = Proto.DecimalType(precision=Int32(int746), scale=Int32(int_3747))
    result749 = _t1386
    record_span!(parser, span_start748, "DecimalType")
    return result749
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start750 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1387 = Proto.BooleanType()
    result751 = _t1387
    record_span!(parser, span_start750, "BooleanType")
    return result751
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start752 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1388 = Proto.Int32Type()
    result753 = _t1388
    record_span!(parser, span_start752, "Int32Type")
    return result753
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start754 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1389 = Proto.Float32Type()
    result755 = _t1389
    record_span!(parser, span_start754, "Float32Type")
    return result755
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs756 = Proto.Binding[]
    cond757 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond757
        _t1390 = parse_binding(parser)
        item758 = _t1390
        push!(xs756, item758)
        cond757 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings759 = xs756
    return bindings759
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start774 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1392 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1393 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1394 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1395 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1396 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1397 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1398 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1399 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1400 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1401 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1402 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1403 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1404 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1405 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1406 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1407 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1408 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1409 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1410 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1411 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1412 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1413 = 10
                                                                                            else
                                                                                                _t1413 = -1
                                                                                            end
                                                                                            _t1412 = _t1413
                                                                                        end
                                                                                        _t1411 = _t1412
                                                                                    end
                                                                                    _t1410 = _t1411
                                                                                end
                                                                                _t1409 = _t1410
                                                                            end
                                                                            _t1408 = _t1409
                                                                        end
                                                                        _t1407 = _t1408
                                                                    end
                                                                    _t1406 = _t1407
                                                                end
                                                                _t1405 = _t1406
                                                            end
                                                            _t1404 = _t1405
                                                        end
                                                        _t1403 = _t1404
                                                    end
                                                    _t1402 = _t1403
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
                        end
                        _t1395 = _t1396
                    end
                    _t1394 = _t1395
                end
                _t1393 = _t1394
            end
            _t1392 = _t1393
        end
        _t1391 = _t1392
    else
        _t1391 = -1
    end
    prediction760 = _t1391
    if prediction760 == 12
        _t1415 = parse_cast(parser)
        cast773 = _t1415
        _t1416 = Proto.Formula(formula_type=OneOf(:cast, cast773))
        _t1414 = _t1416
    else
        if prediction760 == 11
            _t1418 = parse_rel_atom(parser)
            rel_atom772 = _t1418
            _t1419 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom772))
            _t1417 = _t1419
        else
            if prediction760 == 10
                _t1421 = parse_primitive(parser)
                primitive771 = _t1421
                _t1422 = Proto.Formula(formula_type=OneOf(:primitive, primitive771))
                _t1420 = _t1422
            else
                if prediction760 == 9
                    _t1424 = parse_pragma(parser)
                    pragma770 = _t1424
                    _t1425 = Proto.Formula(formula_type=OneOf(:pragma, pragma770))
                    _t1423 = _t1425
                else
                    if prediction760 == 8
                        _t1427 = parse_atom(parser)
                        atom769 = _t1427
                        _t1428 = Proto.Formula(formula_type=OneOf(:atom, atom769))
                        _t1426 = _t1428
                    else
                        if prediction760 == 7
                            _t1430 = parse_ffi(parser)
                            ffi768 = _t1430
                            _t1431 = Proto.Formula(formula_type=OneOf(:ffi, ffi768))
                            _t1429 = _t1431
                        else
                            if prediction760 == 6
                                _t1433 = parse_not(parser)
                                not767 = _t1433
                                _t1434 = Proto.Formula(formula_type=OneOf(:not, not767))
                                _t1432 = _t1434
                            else
                                if prediction760 == 5
                                    _t1436 = parse_disjunction(parser)
                                    disjunction766 = _t1436
                                    _t1437 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction766))
                                    _t1435 = _t1437
                                else
                                    if prediction760 == 4
                                        _t1439 = parse_conjunction(parser)
                                        conjunction765 = _t1439
                                        _t1440 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction765))
                                        _t1438 = _t1440
                                    else
                                        if prediction760 == 3
                                            _t1442 = parse_reduce(parser)
                                            reduce764 = _t1442
                                            _t1443 = Proto.Formula(formula_type=OneOf(:reduce, reduce764))
                                            _t1441 = _t1443
                                        else
                                            if prediction760 == 2
                                                _t1445 = parse_exists(parser)
                                                exists763 = _t1445
                                                _t1446 = Proto.Formula(formula_type=OneOf(:exists, exists763))
                                                _t1444 = _t1446
                                            else
                                                if prediction760 == 1
                                                    _t1448 = parse_false(parser)
                                                    false762 = _t1448
                                                    _t1449 = Proto.Formula(formula_type=OneOf(:disjunction, false762))
                                                    _t1447 = _t1449
                                                else
                                                    if prediction760 == 0
                                                        _t1451 = parse_true(parser)
                                                        true761 = _t1451
                                                        _t1452 = Proto.Formula(formula_type=OneOf(:conjunction, true761))
                                                        _t1450 = _t1452
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
                            _t1429 = _t1432
                        end
                        _t1426 = _t1429
                    end
                    _t1423 = _t1426
                end
                _t1420 = _t1423
            end
            _t1417 = _t1420
        end
        _t1414 = _t1417
    end
    result775 = _t1414
    record_span!(parser, span_start774, "Formula")
    return result775
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start776 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1453 = Proto.Conjunction(args=Proto.Formula[])
    result777 = _t1453
    record_span!(parser, span_start776, "Conjunction")
    return result777
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start778 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1454 = Proto.Disjunction(args=Proto.Formula[])
    result779 = _t1454
    record_span!(parser, span_start778, "Disjunction")
    return result779
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start782 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1455 = parse_bindings(parser)
    bindings780 = _t1455
    _t1456 = parse_formula(parser)
    formula781 = _t1456
    consume_literal!(parser, ")")
    _t1457 = Proto.Abstraction(vars=vcat(bindings780[1], !isnothing(bindings780[2]) ? bindings780[2] : []), value=formula781)
    _t1458 = Proto.Exists(body=_t1457)
    result783 = _t1458
    record_span!(parser, span_start782, "Exists")
    return result783
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start787 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1459 = parse_abstraction(parser)
    abstraction784 = _t1459
    _t1460 = parse_abstraction(parser)
    abstraction_3785 = _t1460
    _t1461 = parse_terms(parser)
    terms786 = _t1461
    consume_literal!(parser, ")")
    _t1462 = Proto.Reduce(op=abstraction784, body=abstraction_3785, terms=terms786)
    result788 = _t1462
    record_span!(parser, span_start787, "Reduce")
    return result788
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs789 = Proto.Term[]
    cond790 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond790
        _t1463 = parse_term(parser)
        item791 = _t1463
        push!(xs789, item791)
        cond790 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms792 = xs789
    consume_literal!(parser, ")")
    return terms792
end

function parse_term(parser::ParserState)::Proto.Term
    span_start796 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1464 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1465 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1466 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1467 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1468 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1469 = 1
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1470 = 1
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1471 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1472 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1473 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1474 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1475 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1476 = 1
                                                    else
                                                        _t1476 = -1
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
                            end
                            _t1469 = _t1470
                        end
                        _t1468 = _t1469
                    end
                    _t1467 = _t1468
                end
                _t1466 = _t1467
            end
            _t1465 = _t1466
        end
        _t1464 = _t1465
    end
    prediction793 = _t1464
    if prediction793 == 1
        _t1478 = parse_value(parser)
        value795 = _t1478
        _t1479 = Proto.Term(term_type=OneOf(:constant, value795))
        _t1477 = _t1479
    else
        if prediction793 == 0
            _t1481 = parse_var(parser)
            var794 = _t1481
            _t1482 = Proto.Term(term_type=OneOf(:var, var794))
            _t1480 = _t1482
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1477 = _t1480
    end
    result797 = _t1477
    record_span!(parser, span_start796, "Term")
    return result797
end

function parse_var(parser::ParserState)::Proto.Var
    span_start799 = span_start(parser)
    symbol798 = consume_terminal!(parser, "SYMBOL")
    _t1483 = Proto.Var(name=symbol798)
    result800 = _t1483
    record_span!(parser, span_start799, "Var")
    return result800
end

function parse_value(parser::ParserState)::Proto.Value
    span_start813 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1484 = 11
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1485 = 10
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1486 = 11
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1488 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1489 = 0
                        else
                            _t1489 = -1
                        end
                        _t1488 = _t1489
                    end
                    _t1487 = _t1488
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1490 = 7
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1491 = 2
                        else
                            if match_lookahead_terminal(parser, "INT32", 0)
                                _t1492 = 3
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1493 = 8
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1494 = 4
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT32", 0)
                                            _t1495 = 5
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1496 = 6
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1497 = 9
                                                else
                                                    _t1497 = -1
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
                    _t1487 = _t1490
                end
                _t1486 = _t1487
            end
            _t1485 = _t1486
        end
        _t1484 = _t1485
    end
    prediction801 = _t1484
    if prediction801 == 11
        _t1499 = parse_boolean_value(parser)
        boolean_value812 = _t1499
        _t1500 = Proto.Value(value=OneOf(:boolean_value, boolean_value812))
        _t1498 = _t1500
    else
        if prediction801 == 10
            consume_literal!(parser, "missing")
            _t1502 = Proto.MissingValue()
            _t1503 = Proto.Value(value=OneOf(:missing_value, _t1502))
            _t1501 = _t1503
        else
            if prediction801 == 9
                formatted_decimal811 = consume_terminal!(parser, "DECIMAL")
                _t1505 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal811))
                _t1504 = _t1505
            else
                if prediction801 == 8
                    formatted_int128810 = consume_terminal!(parser, "INT128")
                    _t1507 = Proto.Value(value=OneOf(:int128_value, formatted_int128810))
                    _t1506 = _t1507
                else
                    if prediction801 == 7
                        formatted_uint128809 = consume_terminal!(parser, "UINT128")
                        _t1509 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128809))
                        _t1508 = _t1509
                    else
                        if prediction801 == 6
                            formatted_float808 = consume_terminal!(parser, "FLOAT")
                            _t1511 = Proto.Value(value=OneOf(:float_value, formatted_float808))
                            _t1510 = _t1511
                        else
                            if prediction801 == 5
                                formatted_float32807 = consume_terminal!(parser, "FLOAT32")
                                _t1513 = Proto.Value(value=OneOf(:float32_value, formatted_float32807))
                                _t1512 = _t1513
                            else
                                if prediction801 == 4
                                    formatted_int806 = consume_terminal!(parser, "INT")
                                    _t1515 = Proto.Value(value=OneOf(:int_value, formatted_int806))
                                    _t1514 = _t1515
                                else
                                    if prediction801 == 3
                                        formatted_int32805 = consume_terminal!(parser, "INT32")
                                        _t1517 = Proto.Value(value=OneOf(:int32_value, formatted_int32805))
                                        _t1516 = _t1517
                                    else
                                        if prediction801 == 2
                                            formatted_string804 = consume_terminal!(parser, "STRING")
                                            _t1519 = Proto.Value(value=OneOf(:string_value, formatted_string804))
                                            _t1518 = _t1519
                                        else
                                            if prediction801 == 1
                                                _t1521 = parse_datetime(parser)
                                                datetime803 = _t1521
                                                _t1522 = Proto.Value(value=OneOf(:datetime_value, datetime803))
                                                _t1520 = _t1522
                                            else
                                                if prediction801 == 0
                                                    _t1524 = parse_date(parser)
                                                    date802 = _t1524
                                                    _t1525 = Proto.Value(value=OneOf(:date_value, date802))
                                                    _t1523 = _t1525
                                                else
                                                    throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                end
                                                _t1520 = _t1523
                                            end
                                            _t1518 = _t1520
                                        end
                                        _t1516 = _t1518
                                    end
                                    _t1514 = _t1516
                                end
                                _t1512 = _t1514
                            end
                            _t1510 = _t1512
                        end
                        _t1508 = _t1510
                    end
                    _t1506 = _t1508
                end
                _t1504 = _t1506
            end
            _t1501 = _t1504
        end
        _t1498 = _t1501
    end
    result814 = _t1498
    record_span!(parser, span_start813, "Value")
    return result814
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start818 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int815 = consume_terminal!(parser, "INT")
    formatted_int_3816 = consume_terminal!(parser, "INT")
    formatted_int_4817 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1526 = Proto.DateValue(year=Int32(formatted_int815), month=Int32(formatted_int_3816), day=Int32(formatted_int_4817))
    result819 = _t1526
    record_span!(parser, span_start818, "DateValue")
    return result819
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start827 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int820 = consume_terminal!(parser, "INT")
    formatted_int_3821 = consume_terminal!(parser, "INT")
    formatted_int_4822 = consume_terminal!(parser, "INT")
    formatted_int_5823 = consume_terminal!(parser, "INT")
    formatted_int_6824 = consume_terminal!(parser, "INT")
    formatted_int_7825 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1527 = consume_terminal!(parser, "INT")
    else
        _t1527 = nothing
    end
    formatted_int_8826 = _t1527
    consume_literal!(parser, ")")
    _t1528 = Proto.DateTimeValue(year=Int32(formatted_int820), month=Int32(formatted_int_3821), day=Int32(formatted_int_4822), hour=Int32(formatted_int_5823), minute=Int32(formatted_int_6824), second=Int32(formatted_int_7825), microsecond=Int32((!isnothing(formatted_int_8826) ? formatted_int_8826 : 0)))
    result828 = _t1528
    record_span!(parser, span_start827, "DateTimeValue")
    return result828
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start833 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs829 = Proto.Formula[]
    cond830 = match_lookahead_literal(parser, "(", 0)
    while cond830
        _t1529 = parse_formula(parser)
        item831 = _t1529
        push!(xs829, item831)
        cond830 = match_lookahead_literal(parser, "(", 0)
    end
    formulas832 = xs829
    consume_literal!(parser, ")")
    _t1530 = Proto.Conjunction(args=formulas832)
    result834 = _t1530
    record_span!(parser, span_start833, "Conjunction")
    return result834
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start839 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs835 = Proto.Formula[]
    cond836 = match_lookahead_literal(parser, "(", 0)
    while cond836
        _t1531 = parse_formula(parser)
        item837 = _t1531
        push!(xs835, item837)
        cond836 = match_lookahead_literal(parser, "(", 0)
    end
    formulas838 = xs835
    consume_literal!(parser, ")")
    _t1532 = Proto.Disjunction(args=formulas838)
    result840 = _t1532
    record_span!(parser, span_start839, "Disjunction")
    return result840
end

function parse_not(parser::ParserState)::Proto.Not
    span_start842 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1533 = parse_formula(parser)
    formula841 = _t1533
    consume_literal!(parser, ")")
    _t1534 = Proto.Not(arg=formula841)
    result843 = _t1534
    record_span!(parser, span_start842, "Not")
    return result843
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start847 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1535 = parse_name(parser)
    name844 = _t1535
    _t1536 = parse_ffi_args(parser)
    ffi_args845 = _t1536
    _t1537 = parse_terms(parser)
    terms846 = _t1537
    consume_literal!(parser, ")")
    _t1538 = Proto.FFI(name=name844, args=ffi_args845, terms=terms846)
    result848 = _t1538
    record_span!(parser, span_start847, "FFI")
    return result848
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol849 = consume_terminal!(parser, "SYMBOL")
    return symbol849
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs850 = Proto.Abstraction[]
    cond851 = match_lookahead_literal(parser, "(", 0)
    while cond851
        _t1539 = parse_abstraction(parser)
        item852 = _t1539
        push!(xs850, item852)
        cond851 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions853 = xs850
    consume_literal!(parser, ")")
    return abstractions853
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start859 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1540 = parse_relation_id(parser)
    relation_id854 = _t1540
    xs855 = Proto.Term[]
    cond856 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond856
        _t1541 = parse_term(parser)
        item857 = _t1541
        push!(xs855, item857)
        cond856 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms858 = xs855
    consume_literal!(parser, ")")
    _t1542 = Proto.Atom(name=relation_id854, terms=terms858)
    result860 = _t1542
    record_span!(parser, span_start859, "Atom")
    return result860
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start866 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1543 = parse_name(parser)
    name861 = _t1543
    xs862 = Proto.Term[]
    cond863 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond863
        _t1544 = parse_term(parser)
        item864 = _t1544
        push!(xs862, item864)
        cond863 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms865 = xs862
    consume_literal!(parser, ")")
    _t1545 = Proto.Pragma(name=name861, terms=terms865)
    result867 = _t1545
    record_span!(parser, span_start866, "Pragma")
    return result867
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start883 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1547 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1548 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1549 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1550 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1551 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1552 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1553 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1554 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1555 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1556 = 7
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
                            end
                            _t1551 = _t1552
                        end
                        _t1550 = _t1551
                    end
                    _t1549 = _t1550
                end
                _t1548 = _t1549
            end
            _t1547 = _t1548
        end
        _t1546 = _t1547
    else
        _t1546 = -1
    end
    prediction868 = _t1546
    if prediction868 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1558 = parse_name(parser)
        name878 = _t1558
        xs879 = Proto.RelTerm[]
        cond880 = (((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond880
            _t1559 = parse_rel_term(parser)
            item881 = _t1559
            push!(xs879, item881)
            cond880 = (((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms882 = xs879
        consume_literal!(parser, ")")
        _t1560 = Proto.Primitive(name=name878, terms=rel_terms882)
        _t1557 = _t1560
    else
        if prediction868 == 8
            _t1562 = parse_divide(parser)
            divide877 = _t1562
            _t1561 = divide877
        else
            if prediction868 == 7
                _t1564 = parse_multiply(parser)
                multiply876 = _t1564
                _t1563 = multiply876
            else
                if prediction868 == 6
                    _t1566 = parse_minus(parser)
                    minus875 = _t1566
                    _t1565 = minus875
                else
                    if prediction868 == 5
                        _t1568 = parse_add(parser)
                        add874 = _t1568
                        _t1567 = add874
                    else
                        if prediction868 == 4
                            _t1570 = parse_gt_eq(parser)
                            gt_eq873 = _t1570
                            _t1569 = gt_eq873
                        else
                            if prediction868 == 3
                                _t1572 = parse_gt(parser)
                                gt872 = _t1572
                                _t1571 = gt872
                            else
                                if prediction868 == 2
                                    _t1574 = parse_lt_eq(parser)
                                    lt_eq871 = _t1574
                                    _t1573 = lt_eq871
                                else
                                    if prediction868 == 1
                                        _t1576 = parse_lt(parser)
                                        lt870 = _t1576
                                        _t1575 = lt870
                                    else
                                        if prediction868 == 0
                                            _t1578 = parse_eq(parser)
                                            eq869 = _t1578
                                            _t1577 = eq869
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1575 = _t1577
                                    end
                                    _t1573 = _t1575
                                end
                                _t1571 = _t1573
                            end
                            _t1569 = _t1571
                        end
                        _t1567 = _t1569
                    end
                    _t1565 = _t1567
                end
                _t1563 = _t1565
            end
            _t1561 = _t1563
        end
        _t1557 = _t1561
    end
    result884 = _t1557
    record_span!(parser, span_start883, "Primitive")
    return result884
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start887 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1579 = parse_term(parser)
    term885 = _t1579
    _t1580 = parse_term(parser)
    term_3886 = _t1580
    consume_literal!(parser, ")")
    _t1581 = Proto.RelTerm(rel_term_type=OneOf(:term, term885))
    _t1582 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3886))
    _t1583 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1581, _t1582])
    result888 = _t1583
    record_span!(parser, span_start887, "Primitive")
    return result888
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start891 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1584 = parse_term(parser)
    term889 = _t1584
    _t1585 = parse_term(parser)
    term_3890 = _t1585
    consume_literal!(parser, ")")
    _t1586 = Proto.RelTerm(rel_term_type=OneOf(:term, term889))
    _t1587 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3890))
    _t1588 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1586, _t1587])
    result892 = _t1588
    record_span!(parser, span_start891, "Primitive")
    return result892
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start895 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1589 = parse_term(parser)
    term893 = _t1589
    _t1590 = parse_term(parser)
    term_3894 = _t1590
    consume_literal!(parser, ")")
    _t1591 = Proto.RelTerm(rel_term_type=OneOf(:term, term893))
    _t1592 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3894))
    _t1593 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1591, _t1592])
    result896 = _t1593
    record_span!(parser, span_start895, "Primitive")
    return result896
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start899 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1594 = parse_term(parser)
    term897 = _t1594
    _t1595 = parse_term(parser)
    term_3898 = _t1595
    consume_literal!(parser, ")")
    _t1596 = Proto.RelTerm(rel_term_type=OneOf(:term, term897))
    _t1597 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3898))
    _t1598 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1596, _t1597])
    result900 = _t1598
    record_span!(parser, span_start899, "Primitive")
    return result900
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start903 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1599 = parse_term(parser)
    term901 = _t1599
    _t1600 = parse_term(parser)
    term_3902 = _t1600
    consume_literal!(parser, ")")
    _t1601 = Proto.RelTerm(rel_term_type=OneOf(:term, term901))
    _t1602 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3902))
    _t1603 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1601, _t1602])
    result904 = _t1603
    record_span!(parser, span_start903, "Primitive")
    return result904
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start908 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1604 = parse_term(parser)
    term905 = _t1604
    _t1605 = parse_term(parser)
    term_3906 = _t1605
    _t1606 = parse_term(parser)
    term_4907 = _t1606
    consume_literal!(parser, ")")
    _t1607 = Proto.RelTerm(rel_term_type=OneOf(:term, term905))
    _t1608 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3906))
    _t1609 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4907))
    _t1610 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1607, _t1608, _t1609])
    result909 = _t1610
    record_span!(parser, span_start908, "Primitive")
    return result909
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start913 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1611 = parse_term(parser)
    term910 = _t1611
    _t1612 = parse_term(parser)
    term_3911 = _t1612
    _t1613 = parse_term(parser)
    term_4912 = _t1613
    consume_literal!(parser, ")")
    _t1614 = Proto.RelTerm(rel_term_type=OneOf(:term, term910))
    _t1615 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3911))
    _t1616 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4912))
    _t1617 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1614, _t1615, _t1616])
    result914 = _t1617
    record_span!(parser, span_start913, "Primitive")
    return result914
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start918 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1618 = parse_term(parser)
    term915 = _t1618
    _t1619 = parse_term(parser)
    term_3916 = _t1619
    _t1620 = parse_term(parser)
    term_4917 = _t1620
    consume_literal!(parser, ")")
    _t1621 = Proto.RelTerm(rel_term_type=OneOf(:term, term915))
    _t1622 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3916))
    _t1623 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4917))
    _t1624 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1621, _t1622, _t1623])
    result919 = _t1624
    record_span!(parser, span_start918, "Primitive")
    return result919
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start923 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1625 = parse_term(parser)
    term920 = _t1625
    _t1626 = parse_term(parser)
    term_3921 = _t1626
    _t1627 = parse_term(parser)
    term_4922 = _t1627
    consume_literal!(parser, ")")
    _t1628 = Proto.RelTerm(rel_term_type=OneOf(:term, term920))
    _t1629 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3921))
    _t1630 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4922))
    _t1631 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1628, _t1629, _t1630])
    result924 = _t1631
    record_span!(parser, span_start923, "Primitive")
    return result924
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start928 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1632 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1633 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1634 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1635 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1636 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1637 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1638 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1639 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1640 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1641 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1642 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1643 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1644 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1645 = 1
                                                        else
                                                            _t1645 = -1
                                                        end
                                                        _t1644 = _t1645
                                                    end
                                                    _t1643 = _t1644
                                                end
                                                _t1642 = _t1643
                                            end
                                            _t1641 = _t1642
                                        end
                                        _t1640 = _t1641
                                    end
                                    _t1639 = _t1640
                                end
                                _t1638 = _t1639
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
    prediction925 = _t1632
    if prediction925 == 1
        _t1647 = parse_term(parser)
        term927 = _t1647
        _t1648 = Proto.RelTerm(rel_term_type=OneOf(:term, term927))
        _t1646 = _t1648
    else
        if prediction925 == 0
            _t1650 = parse_specialized_value(parser)
            specialized_value926 = _t1650
            _t1651 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value926))
            _t1649 = _t1651
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1646 = _t1649
    end
    result929 = _t1646
    record_span!(parser, span_start928, "RelTerm")
    return result929
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start931 = span_start(parser)
    consume_literal!(parser, "#")
    _t1652 = parse_raw_value(parser)
    raw_value930 = _t1652
    result932 = raw_value930
    record_span!(parser, span_start931, "Value")
    return result932
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start938 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1653 = parse_name(parser)
    name933 = _t1653
    xs934 = Proto.RelTerm[]
    cond935 = (((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond935
        _t1654 = parse_rel_term(parser)
        item936 = _t1654
        push!(xs934, item936)
        cond935 = (((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms937 = xs934
    consume_literal!(parser, ")")
    _t1655 = Proto.RelAtom(name=name933, terms=rel_terms937)
    result939 = _t1655
    record_span!(parser, span_start938, "RelAtom")
    return result939
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start942 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1656 = parse_term(parser)
    term940 = _t1656
    _t1657 = parse_term(parser)
    term_3941 = _t1657
    consume_literal!(parser, ")")
    _t1658 = Proto.Cast(input=term940, result=term_3941)
    result943 = _t1658
    record_span!(parser, span_start942, "Cast")
    return result943
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs944 = Proto.Attribute[]
    cond945 = match_lookahead_literal(parser, "(", 0)
    while cond945
        _t1659 = parse_attribute(parser)
        item946 = _t1659
        push!(xs944, item946)
        cond945 = match_lookahead_literal(parser, "(", 0)
    end
    attributes947 = xs944
    consume_literal!(parser, ")")
    return attributes947
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start953 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1660 = parse_name(parser)
    name948 = _t1660
    xs949 = Proto.Value[]
    cond950 = (((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond950
        _t1661 = parse_raw_value(parser)
        item951 = _t1661
        push!(xs949, item951)
        cond950 = (((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    raw_values952 = xs949
    consume_literal!(parser, ")")
    _t1662 = Proto.Attribute(name=name948, args=raw_values952)
    result954 = _t1662
    record_span!(parser, span_start953, "Attribute")
    return result954
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs955 = Proto.RelationId[]
    cond956 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond956
        _t1663 = parse_relation_id(parser)
        item957 = _t1663
        push!(xs955, item957)
        cond956 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids958 = xs955
    _t1664 = parse_script(parser)
    script959 = _t1664
    consume_literal!(parser, ")")
    _t1665 = Proto.Algorithm(var"#global"=relation_ids958, body=script959)
    result961 = _t1665
    record_span!(parser, span_start960, "Algorithm")
    return result961
end

function parse_script(parser::ParserState)::Proto.Script
    span_start966 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs962 = Proto.Construct[]
    cond963 = match_lookahead_literal(parser, "(", 0)
    while cond963
        _t1666 = parse_construct(parser)
        item964 = _t1666
        push!(xs962, item964)
        cond963 = match_lookahead_literal(parser, "(", 0)
    end
    constructs965 = xs962
    consume_literal!(parser, ")")
    _t1667 = Proto.Script(constructs=constructs965)
    result967 = _t1667
    record_span!(parser, span_start966, "Script")
    return result967
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start971 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1669 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1670 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1671 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1672 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1673 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1674 = 1
                            else
                                _t1674 = -1
                            end
                            _t1673 = _t1674
                        end
                        _t1672 = _t1673
                    end
                    _t1671 = _t1672
                end
                _t1670 = _t1671
            end
            _t1669 = _t1670
        end
        _t1668 = _t1669
    else
        _t1668 = -1
    end
    prediction968 = _t1668
    if prediction968 == 1
        _t1676 = parse_instruction(parser)
        instruction970 = _t1676
        _t1677 = Proto.Construct(construct_type=OneOf(:instruction, instruction970))
        _t1675 = _t1677
    else
        if prediction968 == 0
            _t1679 = parse_loop(parser)
            loop969 = _t1679
            _t1680 = Proto.Construct(construct_type=OneOf(:loop, loop969))
            _t1678 = _t1680
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1675 = _t1678
    end
    result972 = _t1675
    record_span!(parser, span_start971, "Construct")
    return result972
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start975 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1681 = parse_init(parser)
    init973 = _t1681
    _t1682 = parse_script(parser)
    script974 = _t1682
    consume_literal!(parser, ")")
    _t1683 = Proto.Loop(init=init973, body=script974)
    result976 = _t1683
    record_span!(parser, span_start975, "Loop")
    return result976
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs977 = Proto.Instruction[]
    cond978 = match_lookahead_literal(parser, "(", 0)
    while cond978
        _t1684 = parse_instruction(parser)
        item979 = _t1684
        push!(xs977, item979)
        cond978 = match_lookahead_literal(parser, "(", 0)
    end
    instructions980 = xs977
    consume_literal!(parser, ")")
    return instructions980
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start987 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1686 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1687 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1688 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1689 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1690 = 0
                        else
                            _t1690 = -1
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
    else
        _t1685 = -1
    end
    prediction981 = _t1685
    if prediction981 == 4
        _t1692 = parse_monus_def(parser)
        monus_def986 = _t1692
        _t1693 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def986))
        _t1691 = _t1693
    else
        if prediction981 == 3
            _t1695 = parse_monoid_def(parser)
            monoid_def985 = _t1695
            _t1696 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def985))
            _t1694 = _t1696
        else
            if prediction981 == 2
                _t1698 = parse_break(parser)
                break984 = _t1698
                _t1699 = Proto.Instruction(instr_type=OneOf(:var"#break", break984))
                _t1697 = _t1699
            else
                if prediction981 == 1
                    _t1701 = parse_upsert(parser)
                    upsert983 = _t1701
                    _t1702 = Proto.Instruction(instr_type=OneOf(:upsert, upsert983))
                    _t1700 = _t1702
                else
                    if prediction981 == 0
                        _t1704 = parse_assign(parser)
                        assign982 = _t1704
                        _t1705 = Proto.Instruction(instr_type=OneOf(:assign, assign982))
                        _t1703 = _t1705
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1700 = _t1703
                end
                _t1697 = _t1700
            end
            _t1694 = _t1697
        end
        _t1691 = _t1694
    end
    result988 = _t1691
    record_span!(parser, span_start987, "Instruction")
    return result988
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start992 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1706 = parse_relation_id(parser)
    relation_id989 = _t1706
    _t1707 = parse_abstraction(parser)
    abstraction990 = _t1707
    if match_lookahead_literal(parser, "(", 0)
        _t1709 = parse_attrs(parser)
        _t1708 = _t1709
    else
        _t1708 = nothing
    end
    attrs991 = _t1708
    consume_literal!(parser, ")")
    _t1710 = Proto.Assign(name=relation_id989, body=abstraction990, attrs=(!isnothing(attrs991) ? attrs991 : Proto.Attribute[]))
    result993 = _t1710
    record_span!(parser, span_start992, "Assign")
    return result993
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start997 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1711 = parse_relation_id(parser)
    relation_id994 = _t1711
    _t1712 = parse_abstraction_with_arity(parser)
    abstraction_with_arity995 = _t1712
    if match_lookahead_literal(parser, "(", 0)
        _t1714 = parse_attrs(parser)
        _t1713 = _t1714
    else
        _t1713 = nothing
    end
    attrs996 = _t1713
    consume_literal!(parser, ")")
    _t1715 = Proto.Upsert(name=relation_id994, body=abstraction_with_arity995[1], attrs=(!isnothing(attrs996) ? attrs996 : Proto.Attribute[]), value_arity=abstraction_with_arity995[2])
    result998 = _t1715
    record_span!(parser, span_start997, "Upsert")
    return result998
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1716 = parse_bindings(parser)
    bindings999 = _t1716
    _t1717 = parse_formula(parser)
    formula1000 = _t1717
    consume_literal!(parser, ")")
    _t1718 = Proto.Abstraction(vars=vcat(bindings999[1], !isnothing(bindings999[2]) ? bindings999[2] : []), value=formula1000)
    return (_t1718, length(bindings999[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1004 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1719 = parse_relation_id(parser)
    relation_id1001 = _t1719
    _t1720 = parse_abstraction(parser)
    abstraction1002 = _t1720
    if match_lookahead_literal(parser, "(", 0)
        _t1722 = parse_attrs(parser)
        _t1721 = _t1722
    else
        _t1721 = nothing
    end
    attrs1003 = _t1721
    consume_literal!(parser, ")")
    _t1723 = Proto.Break(name=relation_id1001, body=abstraction1002, attrs=(!isnothing(attrs1003) ? attrs1003 : Proto.Attribute[]))
    result1005 = _t1723
    record_span!(parser, span_start1004, "Break")
    return result1005
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1010 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1724 = parse_monoid(parser)
    monoid1006 = _t1724
    _t1725 = parse_relation_id(parser)
    relation_id1007 = _t1725
    _t1726 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1008 = _t1726
    if match_lookahead_literal(parser, "(", 0)
        _t1728 = parse_attrs(parser)
        _t1727 = _t1728
    else
        _t1727 = nothing
    end
    attrs1009 = _t1727
    consume_literal!(parser, ")")
    _t1729 = Proto.MonoidDef(monoid=monoid1006, name=relation_id1007, body=abstraction_with_arity1008[1], attrs=(!isnothing(attrs1009) ? attrs1009 : Proto.Attribute[]), value_arity=abstraction_with_arity1008[2])
    result1011 = _t1729
    record_span!(parser, span_start1010, "MonoidDef")
    return result1011
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1017 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1731 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1732 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1733 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1734 = 2
                    else
                        _t1734 = -1
                    end
                    _t1733 = _t1734
                end
                _t1732 = _t1733
            end
            _t1731 = _t1732
        end
        _t1730 = _t1731
    else
        _t1730 = -1
    end
    prediction1012 = _t1730
    if prediction1012 == 3
        _t1736 = parse_sum_monoid(parser)
        sum_monoid1016 = _t1736
        _t1737 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1016))
        _t1735 = _t1737
    else
        if prediction1012 == 2
            _t1739 = parse_max_monoid(parser)
            max_monoid1015 = _t1739
            _t1740 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1015))
            _t1738 = _t1740
        else
            if prediction1012 == 1
                _t1742 = parse_min_monoid(parser)
                min_monoid1014 = _t1742
                _t1743 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1014))
                _t1741 = _t1743
            else
                if prediction1012 == 0
                    _t1745 = parse_or_monoid(parser)
                    or_monoid1013 = _t1745
                    _t1746 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1013))
                    _t1744 = _t1746
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1741 = _t1744
            end
            _t1738 = _t1741
        end
        _t1735 = _t1738
    end
    result1018 = _t1735
    record_span!(parser, span_start1017, "Monoid")
    return result1018
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1019 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1747 = Proto.OrMonoid()
    result1020 = _t1747
    record_span!(parser, span_start1019, "OrMonoid")
    return result1020
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1022 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1748 = parse_type(parser)
    type1021 = _t1748
    consume_literal!(parser, ")")
    _t1749 = Proto.MinMonoid(var"#type"=type1021)
    result1023 = _t1749
    record_span!(parser, span_start1022, "MinMonoid")
    return result1023
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1025 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1750 = parse_type(parser)
    type1024 = _t1750
    consume_literal!(parser, ")")
    _t1751 = Proto.MaxMonoid(var"#type"=type1024)
    result1026 = _t1751
    record_span!(parser, span_start1025, "MaxMonoid")
    return result1026
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1028 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1752 = parse_type(parser)
    type1027 = _t1752
    consume_literal!(parser, ")")
    _t1753 = Proto.SumMonoid(var"#type"=type1027)
    result1029 = _t1753
    record_span!(parser, span_start1028, "SumMonoid")
    return result1029
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1034 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1754 = parse_monoid(parser)
    monoid1030 = _t1754
    _t1755 = parse_relation_id(parser)
    relation_id1031 = _t1755
    _t1756 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1032 = _t1756
    if match_lookahead_literal(parser, "(", 0)
        _t1758 = parse_attrs(parser)
        _t1757 = _t1758
    else
        _t1757 = nothing
    end
    attrs1033 = _t1757
    consume_literal!(parser, ")")
    _t1759 = Proto.MonusDef(monoid=monoid1030, name=relation_id1031, body=abstraction_with_arity1032[1], attrs=(!isnothing(attrs1033) ? attrs1033 : Proto.Attribute[]), value_arity=abstraction_with_arity1032[2])
    result1035 = _t1759
    record_span!(parser, span_start1034, "MonusDef")
    return result1035
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1040 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1760 = parse_relation_id(parser)
    relation_id1036 = _t1760
    _t1761 = parse_abstraction(parser)
    abstraction1037 = _t1761
    _t1762 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1038 = _t1762
    _t1763 = parse_functional_dependency_values(parser)
    functional_dependency_values1039 = _t1763
    consume_literal!(parser, ")")
    _t1764 = Proto.FunctionalDependency(guard=abstraction1037, keys=functional_dependency_keys1038, values=functional_dependency_values1039)
    _t1765 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1764), name=relation_id1036)
    result1041 = _t1765
    record_span!(parser, span_start1040, "Constraint")
    return result1041
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1042 = Proto.Var[]
    cond1043 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1043
        _t1766 = parse_var(parser)
        item1044 = _t1766
        push!(xs1042, item1044)
        cond1043 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1045 = xs1042
    consume_literal!(parser, ")")
    return vars1045
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1046 = Proto.Var[]
    cond1047 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1047
        _t1767 = parse_var(parser)
        item1048 = _t1767
        push!(xs1046, item1048)
        cond1047 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1049 = xs1046
    consume_literal!(parser, ")")
    return vars1049
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1054 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "edb", 1)
            _t1769 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1770 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1771 = 1
                else
                    _t1771 = -1
                end
                _t1770 = _t1771
            end
            _t1769 = _t1770
        end
        _t1768 = _t1769
    else
        _t1768 = -1
    end
    prediction1050 = _t1768
    if prediction1050 == 2
        _t1773 = parse_csv_data(parser)
        csv_data1053 = _t1773
        _t1774 = Proto.Data(data_type=OneOf(:csv_data, csv_data1053))
        _t1772 = _t1774
    else
        if prediction1050 == 1
            _t1776 = parse_betree_relation(parser)
            betree_relation1052 = _t1776
            _t1777 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1052))
            _t1775 = _t1777
        else
            if prediction1050 == 0
                _t1779 = parse_edb(parser)
                edb1051 = _t1779
                _t1780 = Proto.Data(data_type=OneOf(:edb, edb1051))
                _t1778 = _t1780
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1775 = _t1778
        end
        _t1772 = _t1775
    end
    result1055 = _t1772
    record_span!(parser, span_start1054, "Data")
    return result1055
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1059 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1781 = parse_relation_id(parser)
    relation_id1056 = _t1781
    _t1782 = parse_edb_path(parser)
    edb_path1057 = _t1782
    _t1783 = parse_edb_types(parser)
    edb_types1058 = _t1783
    consume_literal!(parser, ")")
    _t1784 = Proto.EDB(target_id=relation_id1056, path=edb_path1057, types=edb_types1058)
    result1060 = _t1784
    record_span!(parser, span_start1059, "EDB")
    return result1060
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1061 = String[]
    cond1062 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1062
        item1063 = consume_terminal!(parser, "STRING")
        push!(xs1061, item1063)
        cond1062 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1064 = xs1061
    consume_literal!(parser, "]")
    return strings1064
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1065 = Proto.var"#Type"[]
    cond1066 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1066
        _t1785 = parse_type(parser)
        item1067 = _t1785
        push!(xs1065, item1067)
        cond1066 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1068 = xs1065
    consume_literal!(parser, "]")
    return types1068
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1071 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1786 = parse_relation_id(parser)
    relation_id1069 = _t1786
    _t1787 = parse_betree_info(parser)
    betree_info1070 = _t1787
    consume_literal!(parser, ")")
    _t1788 = Proto.BeTreeRelation(name=relation_id1069, relation_info=betree_info1070)
    result1072 = _t1788
    record_span!(parser, span_start1071, "BeTreeRelation")
    return result1072
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1076 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1789 = parse_betree_info_key_types(parser)
    betree_info_key_types1073 = _t1789
    _t1790 = parse_betree_info_value_types(parser)
    betree_info_value_types1074 = _t1790
    _t1791 = parse_config_dict(parser)
    config_dict1075 = _t1791
    consume_literal!(parser, ")")
    _t1792 = construct_betree_info(parser, betree_info_key_types1073, betree_info_value_types1074, config_dict1075)
    result1077 = _t1792
    record_span!(parser, span_start1076, "BeTreeInfo")
    return result1077
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1078 = Proto.var"#Type"[]
    cond1079 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1079
        _t1793 = parse_type(parser)
        item1080 = _t1793
        push!(xs1078, item1080)
        cond1079 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1081 = xs1078
    consume_literal!(parser, ")")
    return types1081
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1082 = Proto.var"#Type"[]
    cond1083 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1083
        _t1794 = parse_type(parser)
        item1084 = _t1794
        push!(xs1082, item1084)
        cond1083 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1085 = xs1082
    consume_literal!(parser, ")")
    return types1085
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1090 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1795 = parse_csvlocator(parser)
    csvlocator1086 = _t1795
    _t1796 = parse_csv_config(parser)
    csv_config1087 = _t1796
    _t1797 = parse_gnf_columns(parser)
    gnf_columns1088 = _t1797
    _t1798 = parse_csv_asof(parser)
    csv_asof1089 = _t1798
    consume_literal!(parser, ")")
    _t1799 = Proto.CSVData(locator=csvlocator1086, config=csv_config1087, columns=gnf_columns1088, asof=csv_asof1089)
    result1091 = _t1799
    record_span!(parser, span_start1090, "CSVData")
    return result1091
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1094 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1801 = parse_csv_locator_paths(parser)
        _t1800 = _t1801
    else
        _t1800 = nothing
    end
    csv_locator_paths1092 = _t1800
    if match_lookahead_literal(parser, "(", 0)
        _t1803 = parse_csv_locator_inline_data(parser)
        _t1802 = _t1803
    else
        _t1802 = nothing
    end
    csv_locator_inline_data1093 = _t1802
    consume_literal!(parser, ")")
    _t1804 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1092) ? csv_locator_paths1092 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1093) ? csv_locator_inline_data1093 : "")))
    result1095 = _t1804
    record_span!(parser, span_start1094, "CSVLocator")
    return result1095
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1096 = String[]
    cond1097 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1097
        item1098 = consume_terminal!(parser, "STRING")
        push!(xs1096, item1098)
        cond1097 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1099 = xs1096
    consume_literal!(parser, ")")
    return strings1099
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1100 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1100
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1102 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1805 = parse_config_dict(parser)
    config_dict1101 = _t1805
    consume_literal!(parser, ")")
    _t1806 = construct_csv_config(parser, config_dict1101)
    result1103 = _t1806
    record_span!(parser, span_start1102, "CSVConfig")
    return result1103
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1104 = Proto.GNFColumn[]
    cond1105 = match_lookahead_literal(parser, "(", 0)
    while cond1105
        _t1807 = parse_gnf_column(parser)
        item1106 = _t1807
        push!(xs1104, item1106)
        cond1105 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1107 = xs1104
    consume_literal!(parser, ")")
    return gnf_columns1107
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1114 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1808 = parse_gnf_column_path(parser)
    gnf_column_path1108 = _t1808
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1810 = parse_relation_id(parser)
        _t1809 = _t1810
    else
        _t1809 = nothing
    end
    relation_id1109 = _t1809
    consume_literal!(parser, "[")
    xs1110 = Proto.var"#Type"[]
    cond1111 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1111
        _t1811 = parse_type(parser)
        item1112 = _t1811
        push!(xs1110, item1112)
        cond1111 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1113 = xs1110
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1812 = Proto.GNFColumn(column_path=gnf_column_path1108, target_id=relation_id1109, types=types1113)
    result1115 = _t1812
    record_span!(parser, span_start1114, "GNFColumn")
    return result1115
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1813 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1814 = 0
        else
            _t1814 = -1
        end
        _t1813 = _t1814
    end
    prediction1116 = _t1813
    if prediction1116 == 1
        consume_literal!(parser, "[")
        xs1118 = String[]
        cond1119 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1119
            item1120 = consume_terminal!(parser, "STRING")
            push!(xs1118, item1120)
            cond1119 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1121 = xs1118
        consume_literal!(parser, "]")
        _t1815 = strings1121
    else
        if prediction1116 == 0
            string1117 = consume_terminal!(parser, "STRING")
            _t1816 = String[string1117]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1815 = _t1816
    end
    return _t1815
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1122 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1122
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1124 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1817 = parse_fragment_id(parser)
    fragment_id1123 = _t1817
    consume_literal!(parser, ")")
    _t1818 = Proto.Undefine(fragment_id=fragment_id1123)
    result1125 = _t1818
    record_span!(parser, span_start1124, "Undefine")
    return result1125
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1130 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1126 = Proto.RelationId[]
    cond1127 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1127
        _t1819 = parse_relation_id(parser)
        item1128 = _t1819
        push!(xs1126, item1128)
        cond1127 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1129 = xs1126
    consume_literal!(parser, ")")
    _t1820 = Proto.Context(relations=relation_ids1129)
    result1131 = _t1820
    record_span!(parser, span_start1130, "Context")
    return result1131
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1136 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1132 = Proto.SnapshotMapping[]
    cond1133 = match_lookahead_literal(parser, "[", 0)
    while cond1133
        _t1821 = parse_snapshot_mapping(parser)
        item1134 = _t1821
        push!(xs1132, item1134)
        cond1133 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1135 = xs1132
    consume_literal!(parser, ")")
    _t1822 = Proto.Snapshot(mappings=snapshot_mappings1135)
    result1137 = _t1822
    record_span!(parser, span_start1136, "Snapshot")
    return result1137
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1140 = span_start(parser)
    _t1823 = parse_edb_path(parser)
    edb_path1138 = _t1823
    _t1824 = parse_relation_id(parser)
    relation_id1139 = _t1824
    _t1825 = Proto.SnapshotMapping(destination_path=edb_path1138, source_relation=relation_id1139)
    result1141 = _t1825
    record_span!(parser, span_start1140, "SnapshotMapping")
    return result1141
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1142 = Proto.Read[]
    cond1143 = match_lookahead_literal(parser, "(", 0)
    while cond1143
        _t1826 = parse_read(parser)
        item1144 = _t1826
        push!(xs1142, item1144)
        cond1143 = match_lookahead_literal(parser, "(", 0)
    end
    reads1145 = xs1142
    consume_literal!(parser, ")")
    return reads1145
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1152 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1828 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1829 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1830 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1831 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1832 = 3
                        else
                            _t1832 = -1
                        end
                        _t1831 = _t1832
                    end
                    _t1830 = _t1831
                end
                _t1829 = _t1830
            end
            _t1828 = _t1829
        end
        _t1827 = _t1828
    else
        _t1827 = -1
    end
    prediction1146 = _t1827
    if prediction1146 == 4
        _t1834 = parse_export(parser)
        export1151 = _t1834
        _t1835 = Proto.Read(read_type=OneOf(:var"#export", export1151))
        _t1833 = _t1835
    else
        if prediction1146 == 3
            _t1837 = parse_abort(parser)
            abort1150 = _t1837
            _t1838 = Proto.Read(read_type=OneOf(:abort, abort1150))
            _t1836 = _t1838
        else
            if prediction1146 == 2
                _t1840 = parse_what_if(parser)
                what_if1149 = _t1840
                _t1841 = Proto.Read(read_type=OneOf(:what_if, what_if1149))
                _t1839 = _t1841
            else
                if prediction1146 == 1
                    _t1843 = parse_output(parser)
                    output1148 = _t1843
                    _t1844 = Proto.Read(read_type=OneOf(:output, output1148))
                    _t1842 = _t1844
                else
                    if prediction1146 == 0
                        _t1846 = parse_demand(parser)
                        demand1147 = _t1846
                        _t1847 = Proto.Read(read_type=OneOf(:demand, demand1147))
                        _t1845 = _t1847
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1842 = _t1845
                end
                _t1839 = _t1842
            end
            _t1836 = _t1839
        end
        _t1833 = _t1836
    end
    result1153 = _t1833
    record_span!(parser, span_start1152, "Read")
    return result1153
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1155 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1848 = parse_relation_id(parser)
    relation_id1154 = _t1848
    consume_literal!(parser, ")")
    _t1849 = Proto.Demand(relation_id=relation_id1154)
    result1156 = _t1849
    record_span!(parser, span_start1155, "Demand")
    return result1156
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1159 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1850 = parse_name(parser)
    name1157 = _t1850
    _t1851 = parse_relation_id(parser)
    relation_id1158 = _t1851
    consume_literal!(parser, ")")
    _t1852 = Proto.Output(name=name1157, relation_id=relation_id1158)
    result1160 = _t1852
    record_span!(parser, span_start1159, "Output")
    return result1160
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1163 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1853 = parse_name(parser)
    name1161 = _t1853
    _t1854 = parse_epoch(parser)
    epoch1162 = _t1854
    consume_literal!(parser, ")")
    _t1855 = Proto.WhatIf(branch=name1161, epoch=epoch1162)
    result1164 = _t1855
    record_span!(parser, span_start1163, "WhatIf")
    return result1164
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1167 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1857 = parse_name(parser)
        _t1856 = _t1857
    else
        _t1856 = nothing
    end
    name1165 = _t1856
    _t1858 = parse_relation_id(parser)
    relation_id1166 = _t1858
    consume_literal!(parser, ")")
    _t1859 = Proto.Abort(name=(!isnothing(name1165) ? name1165 : "abort"), relation_id=relation_id1166)
    result1168 = _t1859
    record_span!(parser, span_start1167, "Abort")
    return result1168
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1170 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1860 = parse_export_csv_config(parser)
    export_csv_config1169 = _t1860
    consume_literal!(parser, ")")
    _t1861 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1169))
    result1171 = _t1861
    record_span!(parser, span_start1170, "Export")
    return result1171
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1179 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1863 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1864 = 1
            else
                _t1864 = -1
            end
            _t1863 = _t1864
        end
        _t1862 = _t1863
    else
        _t1862 = -1
    end
    prediction1172 = _t1862
    if prediction1172 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1866 = parse_export_csv_path(parser)
        export_csv_path1176 = _t1866
        _t1867 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1177 = _t1867
        _t1868 = parse_config_dict(parser)
        config_dict1178 = _t1868
        consume_literal!(parser, ")")
        _t1869 = construct_export_csv_config(parser, export_csv_path1176, export_csv_columns_list1177, config_dict1178)
        _t1865 = _t1869
    else
        if prediction1172 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1871 = parse_export_csv_path(parser)
            export_csv_path1173 = _t1871
            _t1872 = parse_export_csv_source(parser)
            export_csv_source1174 = _t1872
            _t1873 = parse_csv_config(parser)
            csv_config1175 = _t1873
            consume_literal!(parser, ")")
            _t1874 = construct_export_csv_config_with_source(parser, export_csv_path1173, export_csv_source1174, csv_config1175)
            _t1870 = _t1874
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1865 = _t1870
    end
    result1180 = _t1865
    record_span!(parser, span_start1179, "ExportCSVConfig")
    return result1180
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1181 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1181
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1188 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1876 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1877 = 0
            else
                _t1877 = -1
            end
            _t1876 = _t1877
        end
        _t1875 = _t1876
    else
        _t1875 = -1
    end
    prediction1182 = _t1875
    if prediction1182 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1879 = parse_relation_id(parser)
        relation_id1187 = _t1879
        consume_literal!(parser, ")")
        _t1880 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1187))
        _t1878 = _t1880
    else
        if prediction1182 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1183 = Proto.ExportCSVColumn[]
            cond1184 = match_lookahead_literal(parser, "(", 0)
            while cond1184
                _t1882 = parse_export_csv_column(parser)
                item1185 = _t1882
                push!(xs1183, item1185)
                cond1184 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1186 = xs1183
            consume_literal!(parser, ")")
            _t1883 = Proto.ExportCSVColumns(columns=export_csv_columns1186)
            _t1884 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1883))
            _t1881 = _t1884
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1878 = _t1881
    end
    result1189 = _t1878
    record_span!(parser, span_start1188, "ExportCSVSource")
    return result1189
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1192 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1190 = consume_terminal!(parser, "STRING")
    _t1885 = parse_relation_id(parser)
    relation_id1191 = _t1885
    consume_literal!(parser, ")")
    _t1886 = Proto.ExportCSVColumn(column_name=string1190, column_data=relation_id1191)
    result1193 = _t1886
    record_span!(parser, span_start1192, "ExportCSVColumn")
    return result1193
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1194 = Proto.ExportCSVColumn[]
    cond1195 = match_lookahead_literal(parser, "(", 0)
    while cond1195
        _t1887 = parse_export_csv_column(parser)
        item1196 = _t1887
        push!(xs1194, item1196)
        cond1195 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1197 = xs1194
    consume_literal!(parser, ")")
    return export_csv_columns1197
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
export scan_string, scan_int, scan_int32, scan_float, scan_float32, scan_int128, scan_uint128, scan_decimal
# Export Lexer and provenance types for testing
export Lexer, Location, Span

end # module Parser
