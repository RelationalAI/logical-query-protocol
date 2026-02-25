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
        _t1835 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1836 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1837 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1838 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1839 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1840 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1841 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1842 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1843 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1844 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1844
    _t1845 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1845
    _t1846 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1846
    _t1847 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1847
    _t1848 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1848
    _t1849 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1849
    _t1850 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1850
    _t1851 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1851
    _t1852 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1852
    _t1853 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1853
    _t1854 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1854
    _t1855 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1855
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1856 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1856
    _t1857 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1857
    _t1858 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1858
    _t1859 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1859
    _t1860 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1860
    _t1861 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1861
    _t1862 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1862
    _t1863 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1863
    _t1864 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1864
    _t1865 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1865
    _t1866 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1866
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1867 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1867
    _t1868 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1868
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
    _t1869 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1869
    _t1870 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1870
    _t1871 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1871
end

function export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1872 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1872
    _t1873 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1873
    _t1874 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1874
    _t1875 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1875
    _t1876 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1876
    _t1877 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1877
    _t1878 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1878
    _t1879 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1879
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start602 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    push_path!(parser, 2)
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1237 = parse_configure(parser)
        _t1236 = _t1237
    else
        _t1236 = nothing
    end
    configure592 = _t1236
    pop_path!(parser)
    push_path!(parser, 3)
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1239 = parse_sync(parser)
        _t1238 = _t1239
    else
        _t1238 = nothing
    end
    sync593 = _t1238
    pop_path!(parser)
    push_path!(parser, 1)
    xs598 = Proto.Epoch[]
    cond599 = match_lookahead_literal(parser, "(", 0)
    idx600 = 0
    while cond599
        push_path!(parser, idx600)
        _t1240 = parse_epoch(parser)
        item601 = _t1240
        pop_path!(parser)
        push!(xs598, item601)
        idx600 = (idx600 + 1)
        cond599 = match_lookahead_literal(parser, "(", 0)
    end
    epochs597 = xs598
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1241 = default_configure(parser)
    _t1242 = Proto.Transaction(epochs=epochs597, configure=(!isnothing(configure592) ? configure592 : _t1241), sync=sync593)
    result603 = _t1242
    record_span!(parser, span_start602)
    return result603
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start605 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1243 = parse_config_dict(parser)
    config_dict604 = _t1243
    consume_literal!(parser, ")")
    _t1244 = construct_configure(parser, config_dict604)
    result606 = _t1244
    record_span!(parser, span_start605)
    return result606
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    span_start611 = span_start(parser)
    consume_literal!(parser, "{")
    xs607 = Tuple{String, Proto.Value}[]
    cond608 = match_lookahead_literal(parser, ":", 0)
    while cond608
        _t1245 = parse_config_key_value(parser)
        item609 = _t1245
        push!(xs607, item609)
        cond608 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values610 = xs607
    consume_literal!(parser, "}")
    result612 = config_key_values610
    record_span!(parser, span_start611)
    return result612
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    span_start615 = span_start(parser)
    consume_literal!(parser, ":")
    symbol613 = consume_terminal!(parser, "SYMBOL")
    _t1246 = parse_value(parser)
    value614 = _t1246
    result616 = (symbol613, value614,)
    record_span!(parser, span_start615)
    return result616
end

function parse_value(parser::ParserState)::Proto.Value
    span_start627 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1247 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1248 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1249 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1251 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1252 = 0
                        else
                            _t1252 = -1
                        end
                        _t1251 = _t1252
                    end
                    _t1250 = _t1251
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1253 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1254 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t1255 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t1256 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t1257 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t1258 = 7
                                        else
                                            _t1258 = -1
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
                    _t1250 = _t1253
                end
                _t1249 = _t1250
            end
            _t1248 = _t1249
        end
        _t1247 = _t1248
    end
    prediction617 = _t1247
    if prediction617 == 9
        _t1260 = parse_boolean_value(parser)
        boolean_value626 = _t1260
        _t1261 = Proto.Value(value=OneOf(:boolean_value, boolean_value626))
        _t1259 = _t1261
    else
        if prediction617 == 8
            consume_literal!(parser, "missing")
            _t1263 = Proto.MissingValue()
            _t1264 = Proto.Value(value=OneOf(:missing_value, _t1263))
            _t1262 = _t1264
        else
            if prediction617 == 7
                decimal625 = consume_terminal!(parser, "DECIMAL")
                _t1266 = Proto.Value(value=OneOf(:decimal_value, decimal625))
                _t1265 = _t1266
            else
                if prediction617 == 6
                    int128624 = consume_terminal!(parser, "INT128")
                    _t1268 = Proto.Value(value=OneOf(:int128_value, int128624))
                    _t1267 = _t1268
                else
                    if prediction617 == 5
                        uint128623 = consume_terminal!(parser, "UINT128")
                        _t1270 = Proto.Value(value=OneOf(:uint128_value, uint128623))
                        _t1269 = _t1270
                    else
                        if prediction617 == 4
                            float622 = consume_terminal!(parser, "FLOAT")
                            _t1272 = Proto.Value(value=OneOf(:float_value, float622))
                            _t1271 = _t1272
                        else
                            if prediction617 == 3
                                int621 = consume_terminal!(parser, "INT")
                                _t1274 = Proto.Value(value=OneOf(:int_value, int621))
                                _t1273 = _t1274
                            else
                                if prediction617 == 2
                                    string620 = consume_terminal!(parser, "STRING")
                                    _t1276 = Proto.Value(value=OneOf(:string_value, string620))
                                    _t1275 = _t1276
                                else
                                    if prediction617 == 1
                                        _t1278 = parse_datetime(parser)
                                        datetime619 = _t1278
                                        _t1279 = Proto.Value(value=OneOf(:datetime_value, datetime619))
                                        _t1277 = _t1279
                                    else
                                        if prediction617 == 0
                                            _t1281 = parse_date(parser)
                                            date618 = _t1281
                                            _t1282 = Proto.Value(value=OneOf(:date_value, date618))
                                            _t1280 = _t1282
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1277 = _t1280
                                    end
                                    _t1275 = _t1277
                                end
                                _t1273 = _t1275
                            end
                            _t1271 = _t1273
                        end
                        _t1269 = _t1271
                    end
                    _t1267 = _t1269
                end
                _t1265 = _t1267
            end
            _t1262 = _t1265
        end
        _t1259 = _t1262
    end
    result628 = _t1259
    record_span!(parser, span_start627)
    return result628
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start632 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    push_path!(parser, 1)
    int629 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_3630 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 3)
    int_4631 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1283 = Proto.DateValue(year=Int32(int629), month=Int32(int_3630), day=Int32(int_4631))
    result633 = _t1283
    record_span!(parser, span_start632)
    return result633
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start641 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    push_path!(parser, 1)
    int634 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_3635 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 3)
    int_4636 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 4)
    int_5637 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 5)
    int_6638 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 6)
    int_7639 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 7)
    if match_lookahead_terminal(parser, "INT", 0)
        _t1284 = consume_terminal!(parser, "INT")
    else
        _t1284 = nothing
    end
    int_8640 = _t1284
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1285 = Proto.DateTimeValue(year=Int32(int634), month=Int32(int_3635), day=Int32(int_4636), hour=Int32(int_5637), minute=Int32(int_6638), second=Int32(int_7639), microsecond=Int32((!isnothing(int_8640) ? int_8640 : 0)))
    result642 = _t1285
    record_span!(parser, span_start641)
    return result642
end

function parse_boolean_value(parser::ParserState)::Bool
    span_start644 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1286 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1287 = 1
        else
            _t1287 = -1
        end
        _t1286 = _t1287
    end
    prediction643 = _t1286
    if prediction643 == 1
        consume_literal!(parser, "false")
        _t1288 = false
    else
        if prediction643 == 0
            consume_literal!(parser, "true")
            _t1289 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1288 = _t1289
    end
    result645 = _t1288
    record_span!(parser, span_start644)
    return result645
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start654 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    push_path!(parser, 1)
    xs650 = Proto.FragmentId[]
    cond651 = match_lookahead_literal(parser, ":", 0)
    idx652 = 0
    while cond651
        push_path!(parser, idx652)
        _t1290 = parse_fragment_id(parser)
        item653 = _t1290
        pop_path!(parser)
        push!(xs650, item653)
        idx652 = (idx652 + 1)
        cond651 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids649 = xs650
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1291 = Proto.Sync(fragments=fragment_ids649)
    result655 = _t1291
    record_span!(parser, span_start654)
    return result655
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start657 = span_start(parser)
    consume_literal!(parser, ":")
    symbol656 = consume_terminal!(parser, "SYMBOL")
    result658 = Proto.FragmentId(Vector{UInt8}(symbol656))
    record_span!(parser, span_start657)
    return result658
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start661 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    push_path!(parser, 1)
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1293 = parse_epoch_writes(parser)
        _t1292 = _t1293
    else
        _t1292 = nothing
    end
    epoch_writes659 = _t1292
    pop_path!(parser)
    push_path!(parser, 2)
    if match_lookahead_literal(parser, "(", 0)
        _t1295 = parse_epoch_reads(parser)
        _t1294 = _t1295
    else
        _t1294 = nothing
    end
    epoch_reads660 = _t1294
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1296 = Proto.Epoch(writes=(!isnothing(epoch_writes659) ? epoch_writes659 : Proto.Write[]), reads=(!isnothing(epoch_reads660) ? epoch_reads660 : Proto.Read[]))
    result662 = _t1296
    record_span!(parser, span_start661)
    return result662
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    span_start667 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs663 = Proto.Write[]
    cond664 = match_lookahead_literal(parser, "(", 0)
    while cond664
        _t1297 = parse_write(parser)
        item665 = _t1297
        push!(xs663, item665)
        cond664 = match_lookahead_literal(parser, "(", 0)
    end
    writes666 = xs663
    consume_literal!(parser, ")")
    result668 = writes666
    record_span!(parser, span_start667)
    return result668
end

function parse_write(parser::ParserState)::Proto.Write
    span_start674 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1299 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1300 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1301 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1302 = 2
                    else
                        _t1302 = -1
                    end
                    _t1301 = _t1302
                end
                _t1300 = _t1301
            end
            _t1299 = _t1300
        end
        _t1298 = _t1299
    else
        _t1298 = -1
    end
    prediction669 = _t1298
    if prediction669 == 3
        _t1304 = parse_snapshot(parser)
        snapshot673 = _t1304
        _t1305 = Proto.Write(write_type=OneOf(:snapshot, snapshot673))
        _t1303 = _t1305
    else
        if prediction669 == 2
            _t1307 = parse_context(parser)
            context672 = _t1307
            _t1308 = Proto.Write(write_type=OneOf(:context, context672))
            _t1306 = _t1308
        else
            if prediction669 == 1
                _t1310 = parse_undefine(parser)
                undefine671 = _t1310
                _t1311 = Proto.Write(write_type=OneOf(:undefine, undefine671))
                _t1309 = _t1311
            else
                if prediction669 == 0
                    _t1313 = parse_define(parser)
                    define670 = _t1313
                    _t1314 = Proto.Write(write_type=OneOf(:define, define670))
                    _t1312 = _t1314
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1309 = _t1312
            end
            _t1306 = _t1309
        end
        _t1303 = _t1306
    end
    result675 = _t1303
    record_span!(parser, span_start674)
    return result675
end

function parse_define(parser::ParserState)::Proto.Define
    span_start677 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    push_path!(parser, 1)
    _t1315 = parse_fragment(parser)
    fragment676 = _t1315
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1316 = Proto.Define(fragment=fragment676)
    result678 = _t1316
    record_span!(parser, span_start677)
    return result678
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start684 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1317 = parse_new_fragment_id(parser)
    new_fragment_id679 = _t1317
    xs680 = Proto.Declaration[]
    cond681 = match_lookahead_literal(parser, "(", 0)
    while cond681
        _t1318 = parse_declaration(parser)
        item682 = _t1318
        push!(xs680, item682)
        cond681 = match_lookahead_literal(parser, "(", 0)
    end
    declarations683 = xs680
    consume_literal!(parser, ")")
    result685 = construct_fragment(parser, new_fragment_id679, declarations683)
    record_span!(parser, span_start684)
    return result685
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start687 = span_start(parser)
    _t1319 = parse_fragment_id(parser)
    fragment_id686 = _t1319
    start_fragment!(parser, fragment_id686)
    result688 = fragment_id686
    record_span!(parser, span_start687)
    return result688
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start694 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1321 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1322 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1323 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1324 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1325 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1326 = 1
                            else
                                _t1326 = -1
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
    else
        _t1320 = -1
    end
    prediction689 = _t1320
    if prediction689 == 3
        _t1328 = parse_data(parser)
        data693 = _t1328
        _t1329 = Proto.Declaration(declaration_type=OneOf(:data, data693))
        _t1327 = _t1329
    else
        if prediction689 == 2
            _t1331 = parse_constraint(parser)
            constraint692 = _t1331
            _t1332 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint692))
            _t1330 = _t1332
        else
            if prediction689 == 1
                _t1334 = parse_algorithm(parser)
                algorithm691 = _t1334
                _t1335 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm691))
                _t1333 = _t1335
            else
                if prediction689 == 0
                    _t1337 = parse_def(parser)
                    def690 = _t1337
                    _t1338 = Proto.Declaration(declaration_type=OneOf(:def, def690))
                    _t1336 = _t1338
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1333 = _t1336
            end
            _t1330 = _t1333
        end
        _t1327 = _t1330
    end
    result695 = _t1327
    record_span!(parser, span_start694)
    return result695
end

function parse_def(parser::ParserState)::Proto.Def
    span_start699 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    push_path!(parser, 1)
    _t1339 = parse_relation_id(parser)
    relation_id696 = _t1339
    pop_path!(parser)
    push_path!(parser, 2)
    _t1340 = parse_abstraction(parser)
    abstraction697 = _t1340
    pop_path!(parser)
    push_path!(parser, 3)
    if match_lookahead_literal(parser, "(", 0)
        _t1342 = parse_attrs(parser)
        _t1341 = _t1342
    else
        _t1341 = nothing
    end
    attrs698 = _t1341
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1343 = Proto.Def(name=relation_id696, body=abstraction697, attrs=(!isnothing(attrs698) ? attrs698 : Proto.Attribute[]))
    result700 = _t1343
    record_span!(parser, span_start699)
    return result700
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start704 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1344 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1345 = 1
        else
            _t1345 = -1
        end
        _t1344 = _t1345
    end
    prediction701 = _t1344
    if prediction701 == 1
        uint128703 = consume_terminal!(parser, "UINT128")
        _t1346 = Proto.RelationId(uint128703.low, uint128703.high)
    else
        if prediction701 == 0
            consume_literal!(parser, ":")
            symbol702 = consume_terminal!(parser, "SYMBOL")
            _t1347 = relation_id_from_string(parser, symbol702)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1346 = _t1347
    end
    result705 = _t1346
    record_span!(parser, span_start704)
    return result705
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start708 = span_start(parser)
    consume_literal!(parser, "(")
    _t1348 = parse_bindings(parser)
    bindings706 = _t1348
    push_path!(parser, 2)
    _t1349 = parse_formula(parser)
    formula707 = _t1349
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1350 = Proto.Abstraction(vars=vcat(bindings706[1], !isnothing(bindings706[2]) ? bindings706[2] : []), value=formula707)
    result709 = _t1350
    record_span!(parser, span_start708)
    return result709
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    span_start715 = span_start(parser)
    consume_literal!(parser, "[")
    xs710 = Proto.Binding[]
    cond711 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond711
        _t1351 = parse_binding(parser)
        item712 = _t1351
        push!(xs710, item712)
        cond711 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings713 = xs710
    if match_lookahead_literal(parser, "|", 0)
        _t1353 = parse_value_bindings(parser)
        _t1352 = _t1353
    else
        _t1352 = nothing
    end
    value_bindings714 = _t1352
    consume_literal!(parser, "]")
    result716 = (bindings713, (!isnothing(value_bindings714) ? value_bindings714 : Proto.Binding[]),)
    record_span!(parser, span_start715)
    return result716
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start719 = span_start(parser)
    symbol717 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    push_path!(parser, 2)
    _t1354 = parse_type(parser)
    type718 = _t1354
    pop_path!(parser)
    _t1355 = Proto.Var(name=symbol717)
    _t1356 = Proto.Binding(var=_t1355, var"#type"=type718)
    result720 = _t1356
    record_span!(parser, span_start719)
    return result720
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start733 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1357 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t1358 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t1359 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t1360 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t1361 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t1362 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t1363 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t1364 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t1365 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t1366 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t1367 = 9
                                            else
                                                _t1367 = -1
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
    prediction721 = _t1357
    if prediction721 == 10
        _t1369 = parse_boolean_type(parser)
        boolean_type732 = _t1369
        _t1370 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type732))
        _t1368 = _t1370
    else
        if prediction721 == 9
            _t1372 = parse_decimal_type(parser)
            decimal_type731 = _t1372
            _t1373 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type731))
            _t1371 = _t1373
        else
            if prediction721 == 8
                _t1375 = parse_missing_type(parser)
                missing_type730 = _t1375
                _t1376 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type730))
                _t1374 = _t1376
            else
                if prediction721 == 7
                    _t1378 = parse_datetime_type(parser)
                    datetime_type729 = _t1378
                    _t1379 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type729))
                    _t1377 = _t1379
                else
                    if prediction721 == 6
                        _t1381 = parse_date_type(parser)
                        date_type728 = _t1381
                        _t1382 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type728))
                        _t1380 = _t1382
                    else
                        if prediction721 == 5
                            _t1384 = parse_int128_type(parser)
                            int128_type727 = _t1384
                            _t1385 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type727))
                            _t1383 = _t1385
                        else
                            if prediction721 == 4
                                _t1387 = parse_uint128_type(parser)
                                uint128_type726 = _t1387
                                _t1388 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type726))
                                _t1386 = _t1388
                            else
                                if prediction721 == 3
                                    _t1390 = parse_float_type(parser)
                                    float_type725 = _t1390
                                    _t1391 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type725))
                                    _t1389 = _t1391
                                else
                                    if prediction721 == 2
                                        _t1393 = parse_int_type(parser)
                                        int_type724 = _t1393
                                        _t1394 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type724))
                                        _t1392 = _t1394
                                    else
                                        if prediction721 == 1
                                            _t1396 = parse_string_type(parser)
                                            string_type723 = _t1396
                                            _t1397 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type723))
                                            _t1395 = _t1397
                                        else
                                            if prediction721 == 0
                                                _t1399 = parse_unspecified_type(parser)
                                                unspecified_type722 = _t1399
                                                _t1400 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type722))
                                                _t1398 = _t1400
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t1395 = _t1398
                                        end
                                        _t1392 = _t1395
                                    end
                                    _t1389 = _t1392
                                end
                                _t1386 = _t1389
                            end
                            _t1383 = _t1386
                        end
                        _t1380 = _t1383
                    end
                    _t1377 = _t1380
                end
                _t1374 = _t1377
            end
            _t1371 = _t1374
        end
        _t1368 = _t1371
    end
    result734 = _t1368
    record_span!(parser, span_start733)
    return result734
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start735 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1401 = Proto.UnspecifiedType()
    result736 = _t1401
    record_span!(parser, span_start735)
    return result736
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start737 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1402 = Proto.StringType()
    result738 = _t1402
    record_span!(parser, span_start737)
    return result738
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start739 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1403 = Proto.IntType()
    result740 = _t1403
    record_span!(parser, span_start739)
    return result740
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start741 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1404 = Proto.FloatType()
    result742 = _t1404
    record_span!(parser, span_start741)
    return result742
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start743 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1405 = Proto.UInt128Type()
    result744 = _t1405
    record_span!(parser, span_start743)
    return result744
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start745 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1406 = Proto.Int128Type()
    result746 = _t1406
    record_span!(parser, span_start745)
    return result746
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start747 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1407 = Proto.DateType()
    result748 = _t1407
    record_span!(parser, span_start747)
    return result748
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start749 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1408 = Proto.DateTimeType()
    result750 = _t1408
    record_span!(parser, span_start749)
    return result750
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start751 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1409 = Proto.MissingType()
    result752 = _t1409
    record_span!(parser, span_start751)
    return result752
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start755 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    push_path!(parser, 1)
    int753 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_3754 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1410 = Proto.DecimalType(precision=Int32(int753), scale=Int32(int_3754))
    result756 = _t1410
    record_span!(parser, span_start755)
    return result756
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start757 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1411 = Proto.BooleanType()
    result758 = _t1411
    record_span!(parser, span_start757)
    return result758
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    span_start763 = span_start(parser)
    consume_literal!(parser, "|")
    xs759 = Proto.Binding[]
    cond760 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond760
        _t1412 = parse_binding(parser)
        item761 = _t1412
        push!(xs759, item761)
        cond760 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings762 = xs759
    result764 = bindings762
    record_span!(parser, span_start763)
    return result764
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start779 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1414 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1415 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1416 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1417 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1418 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1419 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1420 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1421 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1422 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1423 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1424 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1425 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1426 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1427 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1428 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1429 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1430 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1431 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1432 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1433 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1434 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1435 = 10
                                                                                            else
                                                                                                _t1435 = -1
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
    else
        _t1413 = -1
    end
    prediction765 = _t1413
    if prediction765 == 12
        _t1437 = parse_cast(parser)
        cast778 = _t1437
        _t1438 = Proto.Formula(formula_type=OneOf(:cast, cast778))
        _t1436 = _t1438
    else
        if prediction765 == 11
            _t1440 = parse_rel_atom(parser)
            rel_atom777 = _t1440
            _t1441 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom777))
            _t1439 = _t1441
        else
            if prediction765 == 10
                _t1443 = parse_primitive(parser)
                primitive776 = _t1443
                _t1444 = Proto.Formula(formula_type=OneOf(:primitive, primitive776))
                _t1442 = _t1444
            else
                if prediction765 == 9
                    _t1446 = parse_pragma(parser)
                    pragma775 = _t1446
                    _t1447 = Proto.Formula(formula_type=OneOf(:pragma, pragma775))
                    _t1445 = _t1447
                else
                    if prediction765 == 8
                        _t1449 = parse_atom(parser)
                        atom774 = _t1449
                        _t1450 = Proto.Formula(formula_type=OneOf(:atom, atom774))
                        _t1448 = _t1450
                    else
                        if prediction765 == 7
                            _t1452 = parse_ffi(parser)
                            ffi773 = _t1452
                            _t1453 = Proto.Formula(formula_type=OneOf(:ffi, ffi773))
                            _t1451 = _t1453
                        else
                            if prediction765 == 6
                                _t1455 = parse_not(parser)
                                not772 = _t1455
                                _t1456 = Proto.Formula(formula_type=OneOf(:not, not772))
                                _t1454 = _t1456
                            else
                                if prediction765 == 5
                                    _t1458 = parse_disjunction(parser)
                                    disjunction771 = _t1458
                                    _t1459 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction771))
                                    _t1457 = _t1459
                                else
                                    if prediction765 == 4
                                        _t1461 = parse_conjunction(parser)
                                        conjunction770 = _t1461
                                        _t1462 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction770))
                                        _t1460 = _t1462
                                    else
                                        if prediction765 == 3
                                            _t1464 = parse_reduce(parser)
                                            reduce769 = _t1464
                                            _t1465 = Proto.Formula(formula_type=OneOf(:reduce, reduce769))
                                            _t1463 = _t1465
                                        else
                                            if prediction765 == 2
                                                _t1467 = parse_exists(parser)
                                                exists768 = _t1467
                                                _t1468 = Proto.Formula(formula_type=OneOf(:exists, exists768))
                                                _t1466 = _t1468
                                            else
                                                if prediction765 == 1
                                                    _t1470 = parse_false(parser)
                                                    false767 = _t1470
                                                    _t1471 = Proto.Formula(formula_type=OneOf(:disjunction, false767))
                                                    _t1469 = _t1471
                                                else
                                                    if prediction765 == 0
                                                        _t1473 = parse_true(parser)
                                                        true766 = _t1473
                                                        _t1474 = Proto.Formula(formula_type=OneOf(:conjunction, true766))
                                                        _t1472 = _t1474
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1469 = _t1472
                                                end
                                                _t1466 = _t1469
                                            end
                                            _t1463 = _t1466
                                        end
                                        _t1460 = _t1463
                                    end
                                    _t1457 = _t1460
                                end
                                _t1454 = _t1457
                            end
                            _t1451 = _t1454
                        end
                        _t1448 = _t1451
                    end
                    _t1445 = _t1448
                end
                _t1442 = _t1445
            end
            _t1439 = _t1442
        end
        _t1436 = _t1439
    end
    result780 = _t1436
    record_span!(parser, span_start779)
    return result780
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start781 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1475 = Proto.Conjunction(args=Proto.Formula[])
    result782 = _t1475
    record_span!(parser, span_start781)
    return result782
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start783 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1476 = Proto.Disjunction(args=Proto.Formula[])
    result784 = _t1476
    record_span!(parser, span_start783)
    return result784
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start787 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1477 = parse_bindings(parser)
    bindings785 = _t1477
    _t1478 = parse_formula(parser)
    formula786 = _t1478
    consume_literal!(parser, ")")
    _t1479 = Proto.Abstraction(vars=vcat(bindings785[1], !isnothing(bindings785[2]) ? bindings785[2] : []), value=formula786)
    _t1480 = Proto.Exists(body=_t1479)
    result788 = _t1480
    record_span!(parser, span_start787)
    return result788
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start792 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    push_path!(parser, 1)
    _t1481 = parse_abstraction(parser)
    abstraction789 = _t1481
    pop_path!(parser)
    push_path!(parser, 2)
    _t1482 = parse_abstraction(parser)
    abstraction_3790 = _t1482
    pop_path!(parser)
    push_path!(parser, 3)
    _t1483 = parse_terms(parser)
    terms791 = _t1483
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1484 = Proto.Reduce(op=abstraction789, body=abstraction_3790, terms=terms791)
    result793 = _t1484
    record_span!(parser, span_start792)
    return result793
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    span_start798 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs794 = Proto.Term[]
    cond795 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond795
        _t1485 = parse_term(parser)
        item796 = _t1485
        push!(xs794, item796)
        cond795 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms797 = xs794
    consume_literal!(parser, ")")
    result799 = terms797
    record_span!(parser, span_start798)
    return result799
end

function parse_term(parser::ParserState)::Proto.Term
    span_start803 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1486 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1487 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1488 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1489 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1490 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1491 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1492 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1493 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1494 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t1495 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
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
                    end
                    _t1489 = _t1490
                end
                _t1488 = _t1489
            end
            _t1487 = _t1488
        end
        _t1486 = _t1487
    end
    prediction800 = _t1486
    if prediction800 == 1
        _t1498 = parse_constant(parser)
        constant802 = _t1498
        _t1499 = Proto.Term(term_type=OneOf(:constant, constant802))
        _t1497 = _t1499
    else
        if prediction800 == 0
            _t1501 = parse_var(parser)
            var801 = _t1501
            _t1502 = Proto.Term(term_type=OneOf(:var, var801))
            _t1500 = _t1502
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1497 = _t1500
    end
    result804 = _t1497
    record_span!(parser, span_start803)
    return result804
end

function parse_var(parser::ParserState)::Proto.Var
    span_start806 = span_start(parser)
    symbol805 = consume_terminal!(parser, "SYMBOL")
    _t1503 = Proto.Var(name=symbol805)
    result807 = _t1503
    record_span!(parser, span_start806)
    return result807
end

function parse_constant(parser::ParserState)::Proto.Value
    span_start809 = span_start(parser)
    _t1504 = parse_value(parser)
    value808 = _t1504
    result810 = value808
    record_span!(parser, span_start809)
    return result810
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start819 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    push_path!(parser, 1)
    xs815 = Proto.Formula[]
    cond816 = match_lookahead_literal(parser, "(", 0)
    idx817 = 0
    while cond816
        push_path!(parser, idx817)
        _t1505 = parse_formula(parser)
        item818 = _t1505
        pop_path!(parser)
        push!(xs815, item818)
        idx817 = (idx817 + 1)
        cond816 = match_lookahead_literal(parser, "(", 0)
    end
    formulas814 = xs815
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1506 = Proto.Conjunction(args=formulas814)
    result820 = _t1506
    record_span!(parser, span_start819)
    return result820
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start829 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    push_path!(parser, 1)
    xs825 = Proto.Formula[]
    cond826 = match_lookahead_literal(parser, "(", 0)
    idx827 = 0
    while cond826
        push_path!(parser, idx827)
        _t1507 = parse_formula(parser)
        item828 = _t1507
        pop_path!(parser)
        push!(xs825, item828)
        idx827 = (idx827 + 1)
        cond826 = match_lookahead_literal(parser, "(", 0)
    end
    formulas824 = xs825
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1508 = Proto.Disjunction(args=formulas824)
    result830 = _t1508
    record_span!(parser, span_start829)
    return result830
end

function parse_not(parser::ParserState)::Proto.Not
    span_start832 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    push_path!(parser, 1)
    _t1509 = parse_formula(parser)
    formula831 = _t1509
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1510 = Proto.Not(arg=formula831)
    result833 = _t1510
    record_span!(parser, span_start832)
    return result833
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start837 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    push_path!(parser, 1)
    _t1511 = parse_name(parser)
    name834 = _t1511
    pop_path!(parser)
    push_path!(parser, 2)
    _t1512 = parse_ffi_args(parser)
    ffi_args835 = _t1512
    pop_path!(parser)
    push_path!(parser, 3)
    _t1513 = parse_terms(parser)
    terms836 = _t1513
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1514 = Proto.FFI(name=name834, args=ffi_args835, terms=terms836)
    result838 = _t1514
    record_span!(parser, span_start837)
    return result838
end

function parse_name(parser::ParserState)::String
    span_start840 = span_start(parser)
    consume_literal!(parser, ":")
    symbol839 = consume_terminal!(parser, "SYMBOL")
    result841 = symbol839
    record_span!(parser, span_start840)
    return result841
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    span_start846 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs842 = Proto.Abstraction[]
    cond843 = match_lookahead_literal(parser, "(", 0)
    while cond843
        _t1515 = parse_abstraction(parser)
        item844 = _t1515
        push!(xs842, item844)
        cond843 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions845 = xs842
    consume_literal!(parser, ")")
    result847 = abstractions845
    record_span!(parser, span_start846)
    return result847
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start857 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    push_path!(parser, 1)
    _t1516 = parse_relation_id(parser)
    relation_id848 = _t1516
    pop_path!(parser)
    push_path!(parser, 2)
    xs853 = Proto.Term[]
    cond854 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx855 = 0
    while cond854
        push_path!(parser, idx855)
        _t1517 = parse_term(parser)
        item856 = _t1517
        pop_path!(parser)
        push!(xs853, item856)
        idx855 = (idx855 + 1)
        cond854 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms852 = xs853
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1518 = Proto.Atom(name=relation_id848, terms=terms852)
    result858 = _t1518
    record_span!(parser, span_start857)
    return result858
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start868 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    push_path!(parser, 1)
    _t1519 = parse_name(parser)
    name859 = _t1519
    pop_path!(parser)
    push_path!(parser, 2)
    xs864 = Proto.Term[]
    cond865 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx866 = 0
    while cond865
        push_path!(parser, idx866)
        _t1520 = parse_term(parser)
        item867 = _t1520
        pop_path!(parser)
        push!(xs864, item867)
        idx866 = (idx866 + 1)
        cond865 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms863 = xs864
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1521 = Proto.Pragma(name=name859, terms=terms863)
    result869 = _t1521
    record_span!(parser, span_start868)
    return result869
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start889 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1523 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1524 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1525 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1526 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1527 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1528 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1529 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1530 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1531 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1532 = 7
                                            else
                                                _t1532 = -1
                                            end
                                            _t1531 = _t1532
                                        end
                                        _t1530 = _t1531
                                    end
                                    _t1529 = _t1530
                                end
                                _t1528 = _t1529
                            end
                            _t1527 = _t1528
                        end
                        _t1526 = _t1527
                    end
                    _t1525 = _t1526
                end
                _t1524 = _t1525
            end
            _t1523 = _t1524
        end
        _t1522 = _t1523
    else
        _t1522 = -1
    end
    prediction870 = _t1522
    if prediction870 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        push_path!(parser, 1)
        _t1534 = parse_name(parser)
        name880 = _t1534
        pop_path!(parser)
        push_path!(parser, 2)
        xs885 = Proto.RelTerm[]
        cond886 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        idx887 = 0
        while cond886
            push_path!(parser, idx887)
            _t1535 = parse_rel_term(parser)
            item888 = _t1535
            pop_path!(parser)
            push!(xs885, item888)
            idx887 = (idx887 + 1)
            cond886 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms884 = xs885
        pop_path!(parser)
        consume_literal!(parser, ")")
        _t1536 = Proto.Primitive(name=name880, terms=rel_terms884)
        _t1533 = _t1536
    else
        if prediction870 == 8
            _t1538 = parse_divide(parser)
            divide879 = _t1538
            _t1537 = divide879
        else
            if prediction870 == 7
                _t1540 = parse_multiply(parser)
                multiply878 = _t1540
                _t1539 = multiply878
            else
                if prediction870 == 6
                    _t1542 = parse_minus(parser)
                    minus877 = _t1542
                    _t1541 = minus877
                else
                    if prediction870 == 5
                        _t1544 = parse_add(parser)
                        add876 = _t1544
                        _t1543 = add876
                    else
                        if prediction870 == 4
                            _t1546 = parse_gt_eq(parser)
                            gt_eq875 = _t1546
                            _t1545 = gt_eq875
                        else
                            if prediction870 == 3
                                _t1548 = parse_gt(parser)
                                gt874 = _t1548
                                _t1547 = gt874
                            else
                                if prediction870 == 2
                                    _t1550 = parse_lt_eq(parser)
                                    lt_eq873 = _t1550
                                    _t1549 = lt_eq873
                                else
                                    if prediction870 == 1
                                        _t1552 = parse_lt(parser)
                                        lt872 = _t1552
                                        _t1551 = lt872
                                    else
                                        if prediction870 == 0
                                            _t1554 = parse_eq(parser)
                                            eq871 = _t1554
                                            _t1553 = eq871
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1551 = _t1553
                                    end
                                    _t1549 = _t1551
                                end
                                _t1547 = _t1549
                            end
                            _t1545 = _t1547
                        end
                        _t1543 = _t1545
                    end
                    _t1541 = _t1543
                end
                _t1539 = _t1541
            end
            _t1537 = _t1539
        end
        _t1533 = _t1537
    end
    result890 = _t1533
    record_span!(parser, span_start889)
    return result890
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start893 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1555 = parse_term(parser)
    term891 = _t1555
    _t1556 = parse_term(parser)
    term_3892 = _t1556
    consume_literal!(parser, ")")
    _t1557 = Proto.RelTerm(rel_term_type=OneOf(:term, term891))
    _t1558 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3892))
    _t1559 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1557, _t1558])
    result894 = _t1559
    record_span!(parser, span_start893)
    return result894
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start897 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1560 = parse_term(parser)
    term895 = _t1560
    _t1561 = parse_term(parser)
    term_3896 = _t1561
    consume_literal!(parser, ")")
    _t1562 = Proto.RelTerm(rel_term_type=OneOf(:term, term895))
    _t1563 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3896))
    _t1564 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1562, _t1563])
    result898 = _t1564
    record_span!(parser, span_start897)
    return result898
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start901 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1565 = parse_term(parser)
    term899 = _t1565
    _t1566 = parse_term(parser)
    term_3900 = _t1566
    consume_literal!(parser, ")")
    _t1567 = Proto.RelTerm(rel_term_type=OneOf(:term, term899))
    _t1568 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3900))
    _t1569 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1567, _t1568])
    result902 = _t1569
    record_span!(parser, span_start901)
    return result902
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start905 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1570 = parse_term(parser)
    term903 = _t1570
    _t1571 = parse_term(parser)
    term_3904 = _t1571
    consume_literal!(parser, ")")
    _t1572 = Proto.RelTerm(rel_term_type=OneOf(:term, term903))
    _t1573 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3904))
    _t1574 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1572, _t1573])
    result906 = _t1574
    record_span!(parser, span_start905)
    return result906
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start909 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1575 = parse_term(parser)
    term907 = _t1575
    _t1576 = parse_term(parser)
    term_3908 = _t1576
    consume_literal!(parser, ")")
    _t1577 = Proto.RelTerm(rel_term_type=OneOf(:term, term907))
    _t1578 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3908))
    _t1579 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1577, _t1578])
    result910 = _t1579
    record_span!(parser, span_start909)
    return result910
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start914 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1580 = parse_term(parser)
    term911 = _t1580
    _t1581 = parse_term(parser)
    term_3912 = _t1581
    _t1582 = parse_term(parser)
    term_4913 = _t1582
    consume_literal!(parser, ")")
    _t1583 = Proto.RelTerm(rel_term_type=OneOf(:term, term911))
    _t1584 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3912))
    _t1585 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4913))
    _t1586 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1583, _t1584, _t1585])
    result915 = _t1586
    record_span!(parser, span_start914)
    return result915
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start919 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1587 = parse_term(parser)
    term916 = _t1587
    _t1588 = parse_term(parser)
    term_3917 = _t1588
    _t1589 = parse_term(parser)
    term_4918 = _t1589
    consume_literal!(parser, ")")
    _t1590 = Proto.RelTerm(rel_term_type=OneOf(:term, term916))
    _t1591 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3917))
    _t1592 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4918))
    _t1593 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1590, _t1591, _t1592])
    result920 = _t1593
    record_span!(parser, span_start919)
    return result920
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start924 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1594 = parse_term(parser)
    term921 = _t1594
    _t1595 = parse_term(parser)
    term_3922 = _t1595
    _t1596 = parse_term(parser)
    term_4923 = _t1596
    consume_literal!(parser, ")")
    _t1597 = Proto.RelTerm(rel_term_type=OneOf(:term, term921))
    _t1598 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3922))
    _t1599 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4923))
    _t1600 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1597, _t1598, _t1599])
    result925 = _t1600
    record_span!(parser, span_start924)
    return result925
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start929 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1601 = parse_term(parser)
    term926 = _t1601
    _t1602 = parse_term(parser)
    term_3927 = _t1602
    _t1603 = parse_term(parser)
    term_4928 = _t1603
    consume_literal!(parser, ")")
    _t1604 = Proto.RelTerm(rel_term_type=OneOf(:term, term926))
    _t1605 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3927))
    _t1606 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4928))
    _t1607 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1604, _t1605, _t1606])
    result930 = _t1607
    record_span!(parser, span_start929)
    return result930
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start934 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1608 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1609 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1610 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1611 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1612 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1613 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1614 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1615 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1616 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1617 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1618 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1619 = 1
                                                else
                                                    _t1619 = -1
                                                end
                                                _t1618 = _t1619
                                            end
                                            _t1617 = _t1618
                                        end
                                        _t1616 = _t1617
                                    end
                                    _t1615 = _t1616
                                end
                                _t1614 = _t1615
                            end
                            _t1613 = _t1614
                        end
                        _t1612 = _t1613
                    end
                    _t1611 = _t1612
                end
                _t1610 = _t1611
            end
            _t1609 = _t1610
        end
        _t1608 = _t1609
    end
    prediction931 = _t1608
    if prediction931 == 1
        _t1621 = parse_term(parser)
        term933 = _t1621
        _t1622 = Proto.RelTerm(rel_term_type=OneOf(:term, term933))
        _t1620 = _t1622
    else
        if prediction931 == 0
            _t1624 = parse_specialized_value(parser)
            specialized_value932 = _t1624
            _t1625 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value932))
            _t1623 = _t1625
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1620 = _t1623
    end
    result935 = _t1620
    record_span!(parser, span_start934)
    return result935
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start937 = span_start(parser)
    consume_literal!(parser, "#")
    _t1626 = parse_value(parser)
    value936 = _t1626
    result938 = value936
    record_span!(parser, span_start937)
    return result938
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start948 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    push_path!(parser, 3)
    _t1627 = parse_name(parser)
    name939 = _t1627
    pop_path!(parser)
    push_path!(parser, 2)
    xs944 = Proto.RelTerm[]
    cond945 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx946 = 0
    while cond945
        push_path!(parser, idx946)
        _t1628 = parse_rel_term(parser)
        item947 = _t1628
        pop_path!(parser)
        push!(xs944, item947)
        idx946 = (idx946 + 1)
        cond945 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms943 = xs944
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1629 = Proto.RelAtom(name=name939, terms=rel_terms943)
    result949 = _t1629
    record_span!(parser, span_start948)
    return result949
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    push_path!(parser, 2)
    _t1630 = parse_term(parser)
    term950 = _t1630
    pop_path!(parser)
    push_path!(parser, 3)
    _t1631 = parse_term(parser)
    term_3951 = _t1631
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1632 = Proto.Cast(input=term950, result=term_3951)
    result953 = _t1632
    record_span!(parser, span_start952)
    return result953
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    span_start958 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs954 = Proto.Attribute[]
    cond955 = match_lookahead_literal(parser, "(", 0)
    while cond955
        _t1633 = parse_attribute(parser)
        item956 = _t1633
        push!(xs954, item956)
        cond955 = match_lookahead_literal(parser, "(", 0)
    end
    attributes957 = xs954
    consume_literal!(parser, ")")
    result959 = attributes957
    record_span!(parser, span_start958)
    return result959
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    push_path!(parser, 1)
    _t1634 = parse_name(parser)
    name960 = _t1634
    pop_path!(parser)
    push_path!(parser, 2)
    xs965 = Proto.Value[]
    cond966 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx967 = 0
    while cond966
        push_path!(parser, idx967)
        _t1635 = parse_value(parser)
        item968 = _t1635
        pop_path!(parser)
        push!(xs965, item968)
        idx967 = (idx967 + 1)
        cond966 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values964 = xs965
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1636 = Proto.Attribute(name=name960, args=values964)
    result970 = _t1636
    record_span!(parser, span_start969)
    return result970
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    push_path!(parser, 1)
    xs975 = Proto.RelationId[]
    cond976 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    idx977 = 0
    while cond976
        push_path!(parser, idx977)
        _t1637 = parse_relation_id(parser)
        item978 = _t1637
        pop_path!(parser)
        push!(xs975, item978)
        idx977 = (idx977 + 1)
        cond976 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids974 = xs975
    pop_path!(parser)
    push_path!(parser, 2)
    _t1638 = parse_script(parser)
    script979 = _t1638
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1639 = Proto.Algorithm(var"#global"=relation_ids974, body=script979)
    result981 = _t1639
    record_span!(parser, span_start980)
    return result981
end

function parse_script(parser::ParserState)::Proto.Script
    span_start990 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    push_path!(parser, 1)
    xs986 = Proto.Construct[]
    cond987 = match_lookahead_literal(parser, "(", 0)
    idx988 = 0
    while cond987
        push_path!(parser, idx988)
        _t1640 = parse_construct(parser)
        item989 = _t1640
        pop_path!(parser)
        push!(xs986, item989)
        idx988 = (idx988 + 1)
        cond987 = match_lookahead_literal(parser, "(", 0)
    end
    constructs985 = xs986
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1641 = Proto.Script(constructs=constructs985)
    result991 = _t1641
    record_span!(parser, span_start990)
    return result991
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start995 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1643 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1644 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1645 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1646 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1647 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1648 = 1
                            else
                                _t1648 = -1
                            end
                            _t1647 = _t1648
                        end
                        _t1646 = _t1647
                    end
                    _t1645 = _t1646
                end
                _t1644 = _t1645
            end
            _t1643 = _t1644
        end
        _t1642 = _t1643
    else
        _t1642 = -1
    end
    prediction992 = _t1642
    if prediction992 == 1
        _t1650 = parse_instruction(parser)
        instruction994 = _t1650
        _t1651 = Proto.Construct(construct_type=OneOf(:instruction, instruction994))
        _t1649 = _t1651
    else
        if prediction992 == 0
            _t1653 = parse_loop(parser)
            loop993 = _t1653
            _t1654 = Proto.Construct(construct_type=OneOf(:loop, loop993))
            _t1652 = _t1654
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1649 = _t1652
    end
    result996 = _t1649
    record_span!(parser, span_start995)
    return result996
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start999 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    push_path!(parser, 1)
    _t1655 = parse_init(parser)
    init997 = _t1655
    pop_path!(parser)
    push_path!(parser, 2)
    _t1656 = parse_script(parser)
    script998 = _t1656
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1657 = Proto.Loop(init=init997, body=script998)
    result1000 = _t1657
    record_span!(parser, span_start999)
    return result1000
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    span_start1005 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1001 = Proto.Instruction[]
    cond1002 = match_lookahead_literal(parser, "(", 0)
    while cond1002
        _t1658 = parse_instruction(parser)
        item1003 = _t1658
        push!(xs1001, item1003)
        cond1002 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1004 = xs1001
    consume_literal!(parser, ")")
    result1006 = instructions1004
    record_span!(parser, span_start1005)
    return result1006
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1013 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1660 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1661 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1662 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1663 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1664 = 0
                        else
                            _t1664 = -1
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
    else
        _t1659 = -1
    end
    prediction1007 = _t1659
    if prediction1007 == 4
        _t1666 = parse_monus_def(parser)
        monus_def1012 = _t1666
        _t1667 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1012))
        _t1665 = _t1667
    else
        if prediction1007 == 3
            _t1669 = parse_monoid_def(parser)
            monoid_def1011 = _t1669
            _t1670 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1011))
            _t1668 = _t1670
        else
            if prediction1007 == 2
                _t1672 = parse_break(parser)
                break1010 = _t1672
                _t1673 = Proto.Instruction(instr_type=OneOf(:var"#break", break1010))
                _t1671 = _t1673
            else
                if prediction1007 == 1
                    _t1675 = parse_upsert(parser)
                    upsert1009 = _t1675
                    _t1676 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1009))
                    _t1674 = _t1676
                else
                    if prediction1007 == 0
                        _t1678 = parse_assign(parser)
                        assign1008 = _t1678
                        _t1679 = Proto.Instruction(instr_type=OneOf(:assign, assign1008))
                        _t1677 = _t1679
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1674 = _t1677
                end
                _t1671 = _t1674
            end
            _t1668 = _t1671
        end
        _t1665 = _t1668
    end
    result1014 = _t1665
    record_span!(parser, span_start1013)
    return result1014
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1018 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    push_path!(parser, 1)
    _t1680 = parse_relation_id(parser)
    relation_id1015 = _t1680
    pop_path!(parser)
    push_path!(parser, 2)
    _t1681 = parse_abstraction(parser)
    abstraction1016 = _t1681
    pop_path!(parser)
    push_path!(parser, 3)
    if match_lookahead_literal(parser, "(", 0)
        _t1683 = parse_attrs(parser)
        _t1682 = _t1683
    else
        _t1682 = nothing
    end
    attrs1017 = _t1682
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1684 = Proto.Assign(name=relation_id1015, body=abstraction1016, attrs=(!isnothing(attrs1017) ? attrs1017 : Proto.Attribute[]))
    result1019 = _t1684
    record_span!(parser, span_start1018)
    return result1019
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1023 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    push_path!(parser, 1)
    _t1685 = parse_relation_id(parser)
    relation_id1020 = _t1685
    pop_path!(parser)
    _t1686 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1021 = _t1686
    push_path!(parser, 3)
    if match_lookahead_literal(parser, "(", 0)
        _t1688 = parse_attrs(parser)
        _t1687 = _t1688
    else
        _t1687 = nothing
    end
    attrs1022 = _t1687
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1689 = Proto.Upsert(name=relation_id1020, body=abstraction_with_arity1021[1], attrs=(!isnothing(attrs1022) ? attrs1022 : Proto.Attribute[]), value_arity=abstraction_with_arity1021[2])
    result1024 = _t1689
    record_span!(parser, span_start1023)
    return result1024
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    span_start1027 = span_start(parser)
    consume_literal!(parser, "(")
    _t1690 = parse_bindings(parser)
    bindings1025 = _t1690
    _t1691 = parse_formula(parser)
    formula1026 = _t1691
    consume_literal!(parser, ")")
    _t1692 = Proto.Abstraction(vars=vcat(bindings1025[1], !isnothing(bindings1025[2]) ? bindings1025[2] : []), value=formula1026)
    result1028 = (_t1692, length(bindings1025[2]),)
    record_span!(parser, span_start1027)
    return result1028
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1032 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    push_path!(parser, 1)
    _t1693 = parse_relation_id(parser)
    relation_id1029 = _t1693
    pop_path!(parser)
    push_path!(parser, 2)
    _t1694 = parse_abstraction(parser)
    abstraction1030 = _t1694
    pop_path!(parser)
    push_path!(parser, 3)
    if match_lookahead_literal(parser, "(", 0)
        _t1696 = parse_attrs(parser)
        _t1695 = _t1696
    else
        _t1695 = nothing
    end
    attrs1031 = _t1695
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1697 = Proto.Break(name=relation_id1029, body=abstraction1030, attrs=(!isnothing(attrs1031) ? attrs1031 : Proto.Attribute[]))
    result1033 = _t1697
    record_span!(parser, span_start1032)
    return result1033
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1038 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    push_path!(parser, 1)
    _t1698 = parse_monoid(parser)
    monoid1034 = _t1698
    pop_path!(parser)
    push_path!(parser, 2)
    _t1699 = parse_relation_id(parser)
    relation_id1035 = _t1699
    pop_path!(parser)
    _t1700 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1036 = _t1700
    push_path!(parser, 4)
    if match_lookahead_literal(parser, "(", 0)
        _t1702 = parse_attrs(parser)
        _t1701 = _t1702
    else
        _t1701 = nothing
    end
    attrs1037 = _t1701
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1703 = Proto.MonoidDef(monoid=monoid1034, name=relation_id1035, body=abstraction_with_arity1036[1], attrs=(!isnothing(attrs1037) ? attrs1037 : Proto.Attribute[]), value_arity=abstraction_with_arity1036[2])
    result1039 = _t1703
    record_span!(parser, span_start1038)
    return result1039
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1045 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1705 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1706 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1707 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1708 = 2
                    else
                        _t1708 = -1
                    end
                    _t1707 = _t1708
                end
                _t1706 = _t1707
            end
            _t1705 = _t1706
        end
        _t1704 = _t1705
    else
        _t1704 = -1
    end
    prediction1040 = _t1704
    if prediction1040 == 3
        _t1710 = parse_sum_monoid(parser)
        sum_monoid1044 = _t1710
        _t1711 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1044))
        _t1709 = _t1711
    else
        if prediction1040 == 2
            _t1713 = parse_max_monoid(parser)
            max_monoid1043 = _t1713
            _t1714 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1043))
            _t1712 = _t1714
        else
            if prediction1040 == 1
                _t1716 = parse_min_monoid(parser)
                min_monoid1042 = _t1716
                _t1717 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1042))
                _t1715 = _t1717
            else
                if prediction1040 == 0
                    _t1719 = parse_or_monoid(parser)
                    or_monoid1041 = _t1719
                    _t1720 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1041))
                    _t1718 = _t1720
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1715 = _t1718
            end
            _t1712 = _t1715
        end
        _t1709 = _t1712
    end
    result1046 = _t1709
    record_span!(parser, span_start1045)
    return result1046
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1047 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1721 = Proto.OrMonoid()
    result1048 = _t1721
    record_span!(parser, span_start1047)
    return result1048
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1050 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    push_path!(parser, 1)
    _t1722 = parse_type(parser)
    type1049 = _t1722
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1723 = Proto.MinMonoid(var"#type"=type1049)
    result1051 = _t1723
    record_span!(parser, span_start1050)
    return result1051
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1053 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    push_path!(parser, 1)
    _t1724 = parse_type(parser)
    type1052 = _t1724
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1725 = Proto.MaxMonoid(var"#type"=type1052)
    result1054 = _t1725
    record_span!(parser, span_start1053)
    return result1054
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1056 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    push_path!(parser, 1)
    _t1726 = parse_type(parser)
    type1055 = _t1726
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1727 = Proto.SumMonoid(var"#type"=type1055)
    result1057 = _t1727
    record_span!(parser, span_start1056)
    return result1057
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1062 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    push_path!(parser, 1)
    _t1728 = parse_monoid(parser)
    monoid1058 = _t1728
    pop_path!(parser)
    push_path!(parser, 2)
    _t1729 = parse_relation_id(parser)
    relation_id1059 = _t1729
    pop_path!(parser)
    _t1730 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1060 = _t1730
    push_path!(parser, 4)
    if match_lookahead_literal(parser, "(", 0)
        _t1732 = parse_attrs(parser)
        _t1731 = _t1732
    else
        _t1731 = nothing
    end
    attrs1061 = _t1731
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1733 = Proto.MonusDef(monoid=monoid1058, name=relation_id1059, body=abstraction_with_arity1060[1], attrs=(!isnothing(attrs1061) ? attrs1061 : Proto.Attribute[]), value_arity=abstraction_with_arity1060[2])
    result1063 = _t1733
    record_span!(parser, span_start1062)
    return result1063
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1068 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    push_path!(parser, 2)
    _t1734 = parse_relation_id(parser)
    relation_id1064 = _t1734
    pop_path!(parser)
    _t1735 = parse_abstraction(parser)
    abstraction1065 = _t1735
    _t1736 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1066 = _t1736
    _t1737 = parse_functional_dependency_values(parser)
    functional_dependency_values1067 = _t1737
    consume_literal!(parser, ")")
    _t1738 = Proto.FunctionalDependency(guard=abstraction1065, keys=functional_dependency_keys1066, values=functional_dependency_values1067)
    _t1739 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1738), name=relation_id1064)
    result1069 = _t1739
    record_span!(parser, span_start1068)
    return result1069
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    span_start1074 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1070 = Proto.Var[]
    cond1071 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1071
        _t1740 = parse_var(parser)
        item1072 = _t1740
        push!(xs1070, item1072)
        cond1071 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1073 = xs1070
    consume_literal!(parser, ")")
    result1075 = vars1073
    record_span!(parser, span_start1074)
    return result1075
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    span_start1080 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1076 = Proto.Var[]
    cond1077 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1077
        _t1741 = parse_var(parser)
        item1078 = _t1741
        push!(xs1076, item1078)
        cond1077 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1079 = xs1076
    consume_literal!(parser, ")")
    result1081 = vars1079
    record_span!(parser, span_start1080)
    return result1081
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1086 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1743 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1744 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1745 = 1
                else
                    _t1745 = -1
                end
                _t1744 = _t1745
            end
            _t1743 = _t1744
        end
        _t1742 = _t1743
    else
        _t1742 = -1
    end
    prediction1082 = _t1742
    if prediction1082 == 2
        _t1747 = parse_csv_data(parser)
        csv_data1085 = _t1747
        _t1748 = Proto.Data(data_type=OneOf(:csv_data, csv_data1085))
        _t1746 = _t1748
    else
        if prediction1082 == 1
            _t1750 = parse_betree_relation(parser)
            betree_relation1084 = _t1750
            _t1751 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1084))
            _t1749 = _t1751
        else
            if prediction1082 == 0
                _t1753 = parse_rel_edb(parser)
                rel_edb1083 = _t1753
                _t1754 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb1083))
                _t1752 = _t1754
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1749 = _t1752
        end
        _t1746 = _t1749
    end
    result1087 = _t1746
    record_span!(parser, span_start1086)
    return result1087
end

function parse_rel_edb(parser::ParserState)::Proto.RelEDB
    span_start1091 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    push_path!(parser, 1)
    _t1755 = parse_relation_id(parser)
    relation_id1088 = _t1755
    pop_path!(parser)
    push_path!(parser, 2)
    _t1756 = parse_rel_edb_path(parser)
    rel_edb_path1089 = _t1756
    pop_path!(parser)
    push_path!(parser, 3)
    _t1757 = parse_rel_edb_types(parser)
    rel_edb_types1090 = _t1757
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1758 = Proto.RelEDB(target_id=relation_id1088, path=rel_edb_path1089, types=rel_edb_types1090)
    result1092 = _t1758
    record_span!(parser, span_start1091)
    return result1092
end

function parse_rel_edb_path(parser::ParserState)::Vector{String}
    span_start1097 = span_start(parser)
    consume_literal!(parser, "[")
    xs1093 = String[]
    cond1094 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1094
        item1095 = consume_terminal!(parser, "STRING")
        push!(xs1093, item1095)
        cond1094 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1096 = xs1093
    consume_literal!(parser, "]")
    result1098 = strings1096
    record_span!(parser, span_start1097)
    return result1098
end

function parse_rel_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1103 = span_start(parser)
    consume_literal!(parser, "[")
    xs1099 = Proto.var"#Type"[]
    cond1100 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1100
        _t1759 = parse_type(parser)
        item1101 = _t1759
        push!(xs1099, item1101)
        cond1100 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1102 = xs1099
    consume_literal!(parser, "]")
    result1104 = types1102
    record_span!(parser, span_start1103)
    return result1104
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1107 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    push_path!(parser, 1)
    _t1760 = parse_relation_id(parser)
    relation_id1105 = _t1760
    pop_path!(parser)
    push_path!(parser, 2)
    _t1761 = parse_betree_info(parser)
    betree_info1106 = _t1761
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1762 = Proto.BeTreeRelation(name=relation_id1105, relation_info=betree_info1106)
    result1108 = _t1762
    record_span!(parser, span_start1107)
    return result1108
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1112 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1763 = parse_betree_info_key_types(parser)
    betree_info_key_types1109 = _t1763
    _t1764 = parse_betree_info_value_types(parser)
    betree_info_value_types1110 = _t1764
    _t1765 = parse_config_dict(parser)
    config_dict1111 = _t1765
    consume_literal!(parser, ")")
    _t1766 = construct_betree_info(parser, betree_info_key_types1109, betree_info_value_types1110, config_dict1111)
    result1113 = _t1766
    record_span!(parser, span_start1112)
    return result1113
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1118 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1114 = Proto.var"#Type"[]
    cond1115 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1115
        _t1767 = parse_type(parser)
        item1116 = _t1767
        push!(xs1114, item1116)
        cond1115 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1117 = xs1114
    consume_literal!(parser, ")")
    result1119 = types1117
    record_span!(parser, span_start1118)
    return result1119
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    span_start1124 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1120 = Proto.var"#Type"[]
    cond1121 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1121
        _t1768 = parse_type(parser)
        item1122 = _t1768
        push!(xs1120, item1122)
        cond1121 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1123 = xs1120
    consume_literal!(parser, ")")
    result1125 = types1123
    record_span!(parser, span_start1124)
    return result1125
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1130 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    push_path!(parser, 1)
    _t1769 = parse_csvlocator(parser)
    csvlocator1126 = _t1769
    pop_path!(parser)
    push_path!(parser, 2)
    _t1770 = parse_csv_config(parser)
    csv_config1127 = _t1770
    pop_path!(parser)
    push_path!(parser, 3)
    _t1771 = parse_csv_columns(parser)
    csv_columns1128 = _t1771
    pop_path!(parser)
    push_path!(parser, 4)
    _t1772 = parse_csv_asof(parser)
    csv_asof1129 = _t1772
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1773 = Proto.CSVData(locator=csvlocator1126, config=csv_config1127, columns=csv_columns1128, asof=csv_asof1129)
    result1131 = _t1773
    record_span!(parser, span_start1130)
    return result1131
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1134 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    push_path!(parser, 1)
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1775 = parse_csv_locator_paths(parser)
        _t1774 = _t1775
    else
        _t1774 = nothing
    end
    csv_locator_paths1132 = _t1774
    pop_path!(parser)
    push_path!(parser, 2)
    if match_lookahead_literal(parser, "(", 0)
        _t1777 = parse_csv_locator_inline_data(parser)
        _t1776 = _t1777
    else
        _t1776 = nothing
    end
    csv_locator_inline_data1133 = _t1776
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1778 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1132) ? csv_locator_paths1132 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1133) ? csv_locator_inline_data1133 : "")))
    result1135 = _t1778
    record_span!(parser, span_start1134)
    return result1135
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    span_start1140 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1136 = String[]
    cond1137 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1137
        item1138 = consume_terminal!(parser, "STRING")
        push!(xs1136, item1138)
        cond1137 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1139 = xs1136
    consume_literal!(parser, ")")
    result1141 = strings1139
    record_span!(parser, span_start1140)
    return result1141
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    span_start1143 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1142 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1144 = string1142
    record_span!(parser, span_start1143)
    return result1144
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1146 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1779 = parse_config_dict(parser)
    config_dict1145 = _t1779
    consume_literal!(parser, ")")
    _t1780 = construct_csv_config(parser, config_dict1145)
    result1147 = _t1780
    record_span!(parser, span_start1146)
    return result1147
end

function parse_csv_columns(parser::ParserState)::Vector{Proto.CSVColumn}
    span_start1152 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1148 = Proto.CSVColumn[]
    cond1149 = match_lookahead_literal(parser, "(", 0)
    while cond1149
        _t1781 = parse_csv_column(parser)
        item1150 = _t1781
        push!(xs1148, item1150)
        cond1149 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns1151 = xs1148
    consume_literal!(parser, ")")
    result1153 = csv_columns1151
    record_span!(parser, span_start1152)
    return result1153
end

function parse_csv_column(parser::ParserState)::Proto.CSVColumn
    span_start1164 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    push_path!(parser, 1)
    string1154 = consume_terminal!(parser, "STRING")
    pop_path!(parser)
    push_path!(parser, 2)
    _t1782 = parse_relation_id(parser)
    relation_id1155 = _t1782
    pop_path!(parser)
    consume_literal!(parser, "[")
    push_path!(parser, 3)
    xs1160 = Proto.var"#Type"[]
    cond1161 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx1162 = 0
    while cond1161
        push_path!(parser, idx1162)
        _t1783 = parse_type(parser)
        item1163 = _t1783
        pop_path!(parser)
        push!(xs1160, item1163)
        idx1162 = (idx1162 + 1)
        cond1161 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1159 = xs1160
    pop_path!(parser)
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1784 = Proto.CSVColumn(column_name=string1154, target_id=relation_id1155, types=types1159)
    result1165 = _t1784
    record_span!(parser, span_start1164)
    return result1165
end

function parse_csv_asof(parser::ParserState)::String
    span_start1167 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1166 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1168 = string1166
    record_span!(parser, span_start1167)
    return result1168
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1170 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    push_path!(parser, 1)
    _t1785 = parse_fragment_id(parser)
    fragment_id1169 = _t1785
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1786 = Proto.Undefine(fragment_id=fragment_id1169)
    result1171 = _t1786
    record_span!(parser, span_start1170)
    return result1171
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1180 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    push_path!(parser, 1)
    xs1176 = Proto.RelationId[]
    cond1177 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    idx1178 = 0
    while cond1177
        push_path!(parser, idx1178)
        _t1787 = parse_relation_id(parser)
        item1179 = _t1787
        pop_path!(parser)
        push!(xs1176, item1179)
        idx1178 = (idx1178 + 1)
        cond1177 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1175 = xs1176
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1788 = Proto.Context(relations=relation_ids1175)
    result1181 = _t1788
    record_span!(parser, span_start1180)
    return result1181
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1184 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    push_path!(parser, 1)
    _t1789 = parse_rel_edb_path(parser)
    rel_edb_path1182 = _t1789
    pop_path!(parser)
    push_path!(parser, 2)
    _t1790 = parse_relation_id(parser)
    relation_id1183 = _t1790
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1791 = Proto.Snapshot(destination_path=rel_edb_path1182, source_relation=relation_id1183)
    result1185 = _t1791
    record_span!(parser, span_start1184)
    return result1185
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    span_start1190 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1186 = Proto.Read[]
    cond1187 = match_lookahead_literal(parser, "(", 0)
    while cond1187
        _t1792 = parse_read(parser)
        item1188 = _t1792
        push!(xs1186, item1188)
        cond1187 = match_lookahead_literal(parser, "(", 0)
    end
    reads1189 = xs1186
    consume_literal!(parser, ")")
    result1191 = reads1189
    record_span!(parser, span_start1190)
    return result1191
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1198 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1794 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1795 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1796 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1797 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1798 = 3
                        else
                            _t1798 = -1
                        end
                        _t1797 = _t1798
                    end
                    _t1796 = _t1797
                end
                _t1795 = _t1796
            end
            _t1794 = _t1795
        end
        _t1793 = _t1794
    else
        _t1793 = -1
    end
    prediction1192 = _t1793
    if prediction1192 == 4
        _t1800 = parse_export(parser)
        export1197 = _t1800
        _t1801 = Proto.Read(read_type=OneOf(:var"#export", export1197))
        _t1799 = _t1801
    else
        if prediction1192 == 3
            _t1803 = parse_abort(parser)
            abort1196 = _t1803
            _t1804 = Proto.Read(read_type=OneOf(:abort, abort1196))
            _t1802 = _t1804
        else
            if prediction1192 == 2
                _t1806 = parse_what_if(parser)
                what_if1195 = _t1806
                _t1807 = Proto.Read(read_type=OneOf(:what_if, what_if1195))
                _t1805 = _t1807
            else
                if prediction1192 == 1
                    _t1809 = parse_output(parser)
                    output1194 = _t1809
                    _t1810 = Proto.Read(read_type=OneOf(:output, output1194))
                    _t1808 = _t1810
                else
                    if prediction1192 == 0
                        _t1812 = parse_demand(parser)
                        demand1193 = _t1812
                        _t1813 = Proto.Read(read_type=OneOf(:demand, demand1193))
                        _t1811 = _t1813
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1808 = _t1811
                end
                _t1805 = _t1808
            end
            _t1802 = _t1805
        end
        _t1799 = _t1802
    end
    result1199 = _t1799
    record_span!(parser, span_start1198)
    return result1199
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1201 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    push_path!(parser, 1)
    _t1814 = parse_relation_id(parser)
    relation_id1200 = _t1814
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1815 = Proto.Demand(relation_id=relation_id1200)
    result1202 = _t1815
    record_span!(parser, span_start1201)
    return result1202
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1205 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    push_path!(parser, 1)
    _t1816 = parse_name(parser)
    name1203 = _t1816
    pop_path!(parser)
    push_path!(parser, 2)
    _t1817 = parse_relation_id(parser)
    relation_id1204 = _t1817
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1818 = Proto.Output(name=name1203, relation_id=relation_id1204)
    result1206 = _t1818
    record_span!(parser, span_start1205)
    return result1206
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1209 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    push_path!(parser, 1)
    _t1819 = parse_name(parser)
    name1207 = _t1819
    pop_path!(parser)
    push_path!(parser, 2)
    _t1820 = parse_epoch(parser)
    epoch1208 = _t1820
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1821 = Proto.WhatIf(branch=name1207, epoch=epoch1208)
    result1210 = _t1821
    record_span!(parser, span_start1209)
    return result1210
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1213 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    push_path!(parser, 1)
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1823 = parse_name(parser)
        _t1822 = _t1823
    else
        _t1822 = nothing
    end
    name1211 = _t1822
    pop_path!(parser)
    push_path!(parser, 2)
    _t1824 = parse_relation_id(parser)
    relation_id1212 = _t1824
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1825 = Proto.Abort(name=(!isnothing(name1211) ? name1211 : "abort"), relation_id=relation_id1212)
    result1214 = _t1825
    record_span!(parser, span_start1213)
    return result1214
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1216 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    push_path!(parser, 1)
    _t1826 = parse_export_csv_config(parser)
    export_csv_config1215 = _t1826
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1827 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1215))
    result1217 = _t1827
    record_span!(parser, span_start1216)
    return result1217
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1221 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1828 = parse_export_csv_path(parser)
    export_csv_path1218 = _t1828
    _t1829 = parse_export_csv_columns(parser)
    export_csv_columns1219 = _t1829
    _t1830 = parse_config_dict(parser)
    config_dict1220 = _t1830
    consume_literal!(parser, ")")
    _t1831 = export_csv_config(parser, export_csv_path1218, export_csv_columns1219, config_dict1220)
    result1222 = _t1831
    record_span!(parser, span_start1221)
    return result1222
end

function parse_export_csv_path(parser::ParserState)::String
    span_start1224 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1223 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result1225 = string1223
    record_span!(parser, span_start1224)
    return result1225
end

function parse_export_csv_columns(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    span_start1230 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1226 = Proto.ExportCSVColumn[]
    cond1227 = match_lookahead_literal(parser, "(", 0)
    while cond1227
        _t1832 = parse_export_csv_column(parser)
        item1228 = _t1832
        push!(xs1226, item1228)
        cond1227 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1229 = xs1226
    consume_literal!(parser, ")")
    result1231 = export_csv_columns1229
    record_span!(parser, span_start1230)
    return result1231
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1234 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    push_path!(parser, 1)
    string1232 = consume_terminal!(parser, "STRING")
    pop_path!(parser)
    push_path!(parser, 2)
    _t1833 = parse_relation_id(parser)
    relation_id1233 = _t1833
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1834 = Proto.ExportCSVColumn(column_name=string1232, column_data=relation_id1233)
    result1235 = _t1834
    record_span!(parser, span_start1234)
    return result1235
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
