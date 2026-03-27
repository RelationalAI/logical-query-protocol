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

function scan_float32(f::String)
    if f == "inf32"
        return Float32(Inf)
    elseif f == "nan32"
        return Float32(NaN)
    end
    return Base.parse(Float32, f[1:end-3])  # Remove "f32" suffix
end

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
    ("FLOAT32", r"([-]?\d+\.\d+f32|inf32|nan32)", scan_float32),
    ("FLOAT", r"([-]?\d+\.\d+|inf|nan)", scan_float),
    ("INT32", r"[-]?\d+i32", scan_int32),
    ("INT", r"[-]?\d+", scan_int),
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
        _t2059 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2060 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2061 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2062 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2063 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2064 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2065 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2066 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2067 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2068 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2068
    _t2069 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2069
    _t2070 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2070
    _t2071 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2071
    _t2072 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2072
    _t2073 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2073
    _t2074 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2074
    _t2075 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2075
    _t2076 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2076
    _t2077 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2077
    _t2078 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2078
    _t2079 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2079
    _t2080 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2080
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2081 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2081
    _t2082 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2082
    _t2083 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2083
    _t2084 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2084
    _t2085 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2085
    _t2086 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2086
    _t2087 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2087
    _t2088 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2088
    _t2089 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2089
    _t2090 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2090
    _t2091 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2091
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2092 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2092
    _t2093 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2093
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
    _t2094 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2094
    _t2095 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2095
    _t2096 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2096
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2097 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2097
    _t2098 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2098
    _t2099 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2099
    _t2100 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2100
    _t2101 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2101
    _t2102 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2102
    _t2103 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2103
    _t2104 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2104
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2105 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2105
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2106 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2106
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Proto.ExportIcebergColumns, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2107 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2107
    _t2108 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2108
    _t2109 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2109
    table_props = Dict(table_property_pairs)
    _t2110 = Proto.ExportIcebergConfig(locator=locator, config=config, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2110
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start665 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1319 = parse_configure(parser)
        _t1318 = _t1319
    else
        _t1318 = nothing
    end
    configure659 = _t1318
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1321 = parse_sync(parser)
        _t1320 = _t1321
    else
        _t1320 = nothing
    end
    sync660 = _t1320
    xs661 = Proto.Epoch[]
    cond662 = match_lookahead_literal(parser, "(", 0)
    while cond662
        _t1322 = parse_epoch(parser)
        item663 = _t1322
        push!(xs661, item663)
        cond662 = match_lookahead_literal(parser, "(", 0)
    end
    epochs664 = xs661
    consume_literal!(parser, ")")
    _t1323 = default_configure(parser)
    _t1324 = Proto.Transaction(epochs=epochs664, configure=(!isnothing(configure659) ? configure659 : _t1323), sync=sync660)
    result666 = _t1324
    record_span!(parser, span_start665, "Transaction")
    return result666
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start668 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1325 = parse_config_dict(parser)
    config_dict667 = _t1325
    consume_literal!(parser, ")")
    _t1326 = construct_configure(parser, config_dict667)
    result669 = _t1326
    record_span!(parser, span_start668, "Configure")
    return result669
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs670 = Tuple{String, Proto.Value}[]
    cond671 = match_lookahead_literal(parser, ":", 0)
    while cond671
        _t1327 = parse_config_key_value(parser)
        item672 = _t1327
        push!(xs670, item672)
        cond671 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values673 = xs670
    consume_literal!(parser, "}")
    return config_key_values673
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol674 = consume_terminal!(parser, "SYMBOL")
    _t1328 = parse_raw_value(parser)
    raw_value675 = _t1328
    return (symbol674, raw_value675,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start689 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1329 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1330 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1331 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1333 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1334 = 0
                        else
                            _t1334 = -1
                        end
                        _t1333 = _t1334
                    end
                    _t1332 = _t1333
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1335 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1336 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1337 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1338 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1339 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1340 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1341 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1342 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1343 = 10
                                                    else
                                                        _t1343 = -1
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
                    _t1332 = _t1335
                end
                _t1331 = _t1332
            end
            _t1330 = _t1331
        end
        _t1329 = _t1330
    end
    prediction676 = _t1329
    if prediction676 == 12
        _t1345 = parse_boolean_value(parser)
        boolean_value688 = _t1345
        _t1346 = Proto.Value(value=OneOf(:boolean_value, boolean_value688))
        _t1344 = _t1346
    else
        if prediction676 == 11
            consume_literal!(parser, "missing")
            _t1348 = Proto.MissingValue()
            _t1349 = Proto.Value(value=OneOf(:missing_value, _t1348))
            _t1347 = _t1349
        else
            if prediction676 == 10
                decimal687 = consume_terminal!(parser, "DECIMAL")
                _t1351 = Proto.Value(value=OneOf(:decimal_value, decimal687))
                _t1350 = _t1351
            else
                if prediction676 == 9
                    int128686 = consume_terminal!(parser, "INT128")
                    _t1353 = Proto.Value(value=OneOf(:int128_value, int128686))
                    _t1352 = _t1353
                else
                    if prediction676 == 8
                        uint128685 = consume_terminal!(parser, "UINT128")
                        _t1355 = Proto.Value(value=OneOf(:uint128_value, uint128685))
                        _t1354 = _t1355
                    else
                        if prediction676 == 7
                            uint32684 = consume_terminal!(parser, "UINT32")
                            _t1357 = Proto.Value(value=OneOf(:uint32_value, uint32684))
                            _t1356 = _t1357
                        else
                            if prediction676 == 6
                                float683 = consume_terminal!(parser, "FLOAT")
                                _t1359 = Proto.Value(value=OneOf(:float_value, float683))
                                _t1358 = _t1359
                            else
                                if prediction676 == 5
                                    float32682 = consume_terminal!(parser, "FLOAT32")
                                    _t1361 = Proto.Value(value=OneOf(:float32_value, float32682))
                                    _t1360 = _t1361
                                else
                                    if prediction676 == 4
                                        int681 = consume_terminal!(parser, "INT")
                                        _t1363 = Proto.Value(value=OneOf(:int_value, int681))
                                        _t1362 = _t1363
                                    else
                                        if prediction676 == 3
                                            int32680 = consume_terminal!(parser, "INT32")
                                            _t1365 = Proto.Value(value=OneOf(:int32_value, int32680))
                                            _t1364 = _t1365
                                        else
                                            if prediction676 == 2
                                                string679 = consume_terminal!(parser, "STRING")
                                                _t1367 = Proto.Value(value=OneOf(:string_value, string679))
                                                _t1366 = _t1367
                                            else
                                                if prediction676 == 1
                                                    _t1369 = parse_raw_datetime(parser)
                                                    raw_datetime678 = _t1369
                                                    _t1370 = Proto.Value(value=OneOf(:datetime_value, raw_datetime678))
                                                    _t1368 = _t1370
                                                else
                                                    if prediction676 == 0
                                                        _t1372 = parse_raw_date(parser)
                                                        raw_date677 = _t1372
                                                        _t1373 = Proto.Value(value=OneOf(:date_value, raw_date677))
                                                        _t1371 = _t1373
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1368 = _t1371
                                                end
                                                _t1366 = _t1368
                                            end
                                            _t1364 = _t1366
                                        end
                                        _t1362 = _t1364
                                    end
                                    _t1360 = _t1362
                                end
                                _t1358 = _t1360
                            end
                            _t1356 = _t1358
                        end
                        _t1354 = _t1356
                    end
                    _t1352 = _t1354
                end
                _t1350 = _t1352
            end
            _t1347 = _t1350
        end
        _t1344 = _t1347
    end
    result690 = _t1344
    record_span!(parser, span_start689, "Value")
    return result690
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start694 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int691 = consume_terminal!(parser, "INT")
    int_3692 = consume_terminal!(parser, "INT")
    int_4693 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1374 = Proto.DateValue(year=Int32(int691), month=Int32(int_3692), day=Int32(int_4693))
    result695 = _t1374
    record_span!(parser, span_start694, "DateValue")
    return result695
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start703 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int696 = consume_terminal!(parser, "INT")
    int_3697 = consume_terminal!(parser, "INT")
    int_4698 = consume_terminal!(parser, "INT")
    int_5699 = consume_terminal!(parser, "INT")
    int_6700 = consume_terminal!(parser, "INT")
    int_7701 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1375 = consume_terminal!(parser, "INT")
    else
        _t1375 = nothing
    end
    int_8702 = _t1375
    consume_literal!(parser, ")")
    _t1376 = Proto.DateTimeValue(year=Int32(int696), month=Int32(int_3697), day=Int32(int_4698), hour=Int32(int_5699), minute=Int32(int_6700), second=Int32(int_7701), microsecond=Int32((!isnothing(int_8702) ? int_8702 : 0)))
    result704 = _t1376
    record_span!(parser, span_start703, "DateTimeValue")
    return result704
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1377 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1378 = 1
        else
            _t1378 = -1
        end
        _t1377 = _t1378
    end
    prediction705 = _t1377
    if prediction705 == 1
        consume_literal!(parser, "false")
        _t1379 = false
    else
        if prediction705 == 0
            consume_literal!(parser, "true")
            _t1380 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1379 = _t1380
    end
    return _t1379
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start710 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs706 = Proto.FragmentId[]
    cond707 = match_lookahead_literal(parser, ":", 0)
    while cond707
        _t1381 = parse_fragment_id(parser)
        item708 = _t1381
        push!(xs706, item708)
        cond707 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids709 = xs706
    consume_literal!(parser, ")")
    _t1382 = Proto.Sync(fragments=fragment_ids709)
    result711 = _t1382
    record_span!(parser, span_start710, "Sync")
    return result711
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start713 = span_start(parser)
    consume_literal!(parser, ":")
    symbol712 = consume_terminal!(parser, "SYMBOL")
    result714 = Proto.FragmentId(Vector{UInt8}(symbol712))
    record_span!(parser, span_start713, "FragmentId")
    return result714
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start717 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1384 = parse_epoch_writes(parser)
        _t1383 = _t1384
    else
        _t1383 = nothing
    end
    epoch_writes715 = _t1383
    if match_lookahead_literal(parser, "(", 0)
        _t1386 = parse_epoch_reads(parser)
        _t1385 = _t1386
    else
        _t1385 = nothing
    end
    epoch_reads716 = _t1385
    consume_literal!(parser, ")")
    _t1387 = Proto.Epoch(writes=(!isnothing(epoch_writes715) ? epoch_writes715 : Proto.Write[]), reads=(!isnothing(epoch_reads716) ? epoch_reads716 : Proto.Read[]))
    result718 = _t1387
    record_span!(parser, span_start717, "Epoch")
    return result718
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs719 = Proto.Write[]
    cond720 = match_lookahead_literal(parser, "(", 0)
    while cond720
        _t1388 = parse_write(parser)
        item721 = _t1388
        push!(xs719, item721)
        cond720 = match_lookahead_literal(parser, "(", 0)
    end
    writes722 = xs719
    consume_literal!(parser, ")")
    return writes722
end

function parse_write(parser::ParserState)::Proto.Write
    span_start728 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1390 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1391 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1392 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1393 = 2
                    else
                        _t1393 = -1
                    end
                    _t1392 = _t1393
                end
                _t1391 = _t1392
            end
            _t1390 = _t1391
        end
        _t1389 = _t1390
    else
        _t1389 = -1
    end
    prediction723 = _t1389
    if prediction723 == 3
        _t1395 = parse_snapshot(parser)
        snapshot727 = _t1395
        _t1396 = Proto.Write(write_type=OneOf(:snapshot, snapshot727))
        _t1394 = _t1396
    else
        if prediction723 == 2
            _t1398 = parse_context(parser)
            context726 = _t1398
            _t1399 = Proto.Write(write_type=OneOf(:context, context726))
            _t1397 = _t1399
        else
            if prediction723 == 1
                _t1401 = parse_undefine(parser)
                undefine725 = _t1401
                _t1402 = Proto.Write(write_type=OneOf(:undefine, undefine725))
                _t1400 = _t1402
            else
                if prediction723 == 0
                    _t1404 = parse_define(parser)
                    define724 = _t1404
                    _t1405 = Proto.Write(write_type=OneOf(:define, define724))
                    _t1403 = _t1405
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1400 = _t1403
            end
            _t1397 = _t1400
        end
        _t1394 = _t1397
    end
    result729 = _t1394
    record_span!(parser, span_start728, "Write")
    return result729
end

function parse_define(parser::ParserState)::Proto.Define
    span_start731 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1406 = parse_fragment(parser)
    fragment730 = _t1406
    consume_literal!(parser, ")")
    _t1407 = Proto.Define(fragment=fragment730)
    result732 = _t1407
    record_span!(parser, span_start731, "Define")
    return result732
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start738 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1408 = parse_new_fragment_id(parser)
    new_fragment_id733 = _t1408
    xs734 = Proto.Declaration[]
    cond735 = match_lookahead_literal(parser, "(", 0)
    while cond735
        _t1409 = parse_declaration(parser)
        item736 = _t1409
        push!(xs734, item736)
        cond735 = match_lookahead_literal(parser, "(", 0)
    end
    declarations737 = xs734
    consume_literal!(parser, ")")
    result739 = construct_fragment(parser, new_fragment_id733, declarations737)
    record_span!(parser, span_start738, "Fragment")
    return result739
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start741 = span_start(parser)
    _t1410 = parse_fragment_id(parser)
    fragment_id740 = _t1410
    start_fragment!(parser, fragment_id740)
    result742 = fragment_id740
    record_span!(parser, span_start741, "FragmentId")
    return result742
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start748 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1412 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1413 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1414 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1415 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1416 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1417 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1418 = 1
                                else
                                    _t1418 = -1
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
    else
        _t1411 = -1
    end
    prediction743 = _t1411
    if prediction743 == 3
        _t1420 = parse_data(parser)
        data747 = _t1420
        _t1421 = Proto.Declaration(declaration_type=OneOf(:data, data747))
        _t1419 = _t1421
    else
        if prediction743 == 2
            _t1423 = parse_constraint(parser)
            constraint746 = _t1423
            _t1424 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint746))
            _t1422 = _t1424
        else
            if prediction743 == 1
                _t1426 = parse_algorithm(parser)
                algorithm745 = _t1426
                _t1427 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm745))
                _t1425 = _t1427
            else
                if prediction743 == 0
                    _t1429 = parse_def(parser)
                    def744 = _t1429
                    _t1430 = Proto.Declaration(declaration_type=OneOf(:def, def744))
                    _t1428 = _t1430
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1425 = _t1428
            end
            _t1422 = _t1425
        end
        _t1419 = _t1422
    end
    result749 = _t1419
    record_span!(parser, span_start748, "Declaration")
    return result749
end

function parse_def(parser::ParserState)::Proto.Def
    span_start753 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1431 = parse_relation_id(parser)
    relation_id750 = _t1431
    _t1432 = parse_abstraction(parser)
    abstraction751 = _t1432
    if match_lookahead_literal(parser, "(", 0)
        _t1434 = parse_attrs(parser)
        _t1433 = _t1434
    else
        _t1433 = nothing
    end
    attrs752 = _t1433
    consume_literal!(parser, ")")
    _t1435 = Proto.Def(name=relation_id750, body=abstraction751, attrs=(!isnothing(attrs752) ? attrs752 : Proto.Attribute[]))
    result754 = _t1435
    record_span!(parser, span_start753, "Def")
    return result754
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start758 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1436 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1437 = 1
        else
            _t1437 = -1
        end
        _t1436 = _t1437
    end
    prediction755 = _t1436
    if prediction755 == 1
        uint128757 = consume_terminal!(parser, "UINT128")
        _t1438 = Proto.RelationId(uint128757.low, uint128757.high)
    else
        if prediction755 == 0
            consume_literal!(parser, ":")
            symbol756 = consume_terminal!(parser, "SYMBOL")
            _t1439 = relation_id_from_string(parser, symbol756)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1438 = _t1439
    end
    result759 = _t1438
    record_span!(parser, span_start758, "RelationId")
    return result759
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start762 = span_start(parser)
    consume_literal!(parser, "(")
    _t1440 = parse_bindings(parser)
    bindings760 = _t1440
    _t1441 = parse_formula(parser)
    formula761 = _t1441
    consume_literal!(parser, ")")
    _t1442 = Proto.Abstraction(vars=vcat(bindings760[1], !isnothing(bindings760[2]) ? bindings760[2] : []), value=formula761)
    result763 = _t1442
    record_span!(parser, span_start762, "Abstraction")
    return result763
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs764 = Proto.Binding[]
    cond765 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond765
        _t1443 = parse_binding(parser)
        item766 = _t1443
        push!(xs764, item766)
        cond765 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings767 = xs764
    if match_lookahead_literal(parser, "|", 0)
        _t1445 = parse_value_bindings(parser)
        _t1444 = _t1445
    else
        _t1444 = nothing
    end
    value_bindings768 = _t1444
    consume_literal!(parser, "]")
    return (bindings767, (!isnothing(value_bindings768) ? value_bindings768 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start771 = span_start(parser)
    symbol769 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1446 = parse_type(parser)
    type770 = _t1446
    _t1447 = Proto.Var(name=symbol769)
    _t1448 = Proto.Binding(var=_t1447, var"#type"=type770)
    result772 = _t1448
    record_span!(parser, span_start771, "Binding")
    return result772
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start788 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1449 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1450 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1451 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1452 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1453 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1454 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1455 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1456 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1457 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1458 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1459 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1460 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1461 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1462 = 9
                                                        else
                                                            _t1462 = -1
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
                                _t1455 = _t1456
                            end
                            _t1454 = _t1455
                        end
                        _t1453 = _t1454
                    end
                    _t1452 = _t1453
                end
                _t1451 = _t1452
            end
            _t1450 = _t1451
        end
        _t1449 = _t1450
    end
    prediction773 = _t1449
    if prediction773 == 13
        _t1464 = parse_uint32_type(parser)
        uint32_type787 = _t1464
        _t1465 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type787))
        _t1463 = _t1465
    else
        if prediction773 == 12
            _t1467 = parse_float32_type(parser)
            float32_type786 = _t1467
            _t1468 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type786))
            _t1466 = _t1468
        else
            if prediction773 == 11
                _t1470 = parse_int32_type(parser)
                int32_type785 = _t1470
                _t1471 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type785))
                _t1469 = _t1471
            else
                if prediction773 == 10
                    _t1473 = parse_boolean_type(parser)
                    boolean_type784 = _t1473
                    _t1474 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type784))
                    _t1472 = _t1474
                else
                    if prediction773 == 9
                        _t1476 = parse_decimal_type(parser)
                        decimal_type783 = _t1476
                        _t1477 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type783))
                        _t1475 = _t1477
                    else
                        if prediction773 == 8
                            _t1479 = parse_missing_type(parser)
                            missing_type782 = _t1479
                            _t1480 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type782))
                            _t1478 = _t1480
                        else
                            if prediction773 == 7
                                _t1482 = parse_datetime_type(parser)
                                datetime_type781 = _t1482
                                _t1483 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type781))
                                _t1481 = _t1483
                            else
                                if prediction773 == 6
                                    _t1485 = parse_date_type(parser)
                                    date_type780 = _t1485
                                    _t1486 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type780))
                                    _t1484 = _t1486
                                else
                                    if prediction773 == 5
                                        _t1488 = parse_int128_type(parser)
                                        int128_type779 = _t1488
                                        _t1489 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type779))
                                        _t1487 = _t1489
                                    else
                                        if prediction773 == 4
                                            _t1491 = parse_uint128_type(parser)
                                            uint128_type778 = _t1491
                                            _t1492 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type778))
                                            _t1490 = _t1492
                                        else
                                            if prediction773 == 3
                                                _t1494 = parse_float_type(parser)
                                                float_type777 = _t1494
                                                _t1495 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type777))
                                                _t1493 = _t1495
                                            else
                                                if prediction773 == 2
                                                    _t1497 = parse_int_type(parser)
                                                    int_type776 = _t1497
                                                    _t1498 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type776))
                                                    _t1496 = _t1498
                                                else
                                                    if prediction773 == 1
                                                        _t1500 = parse_string_type(parser)
                                                        string_type775 = _t1500
                                                        _t1501 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type775))
                                                        _t1499 = _t1501
                                                    else
                                                        if prediction773 == 0
                                                            _t1503 = parse_unspecified_type(parser)
                                                            unspecified_type774 = _t1503
                                                            _t1504 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type774))
                                                            _t1502 = _t1504
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1499 = _t1502
                                                    end
                                                    _t1496 = _t1499
                                                end
                                                _t1493 = _t1496
                                            end
                                            _t1490 = _t1493
                                        end
                                        _t1487 = _t1490
                                    end
                                    _t1484 = _t1487
                                end
                                _t1481 = _t1484
                            end
                            _t1478 = _t1481
                        end
                        _t1475 = _t1478
                    end
                    _t1472 = _t1475
                end
                _t1469 = _t1472
            end
            _t1466 = _t1469
        end
        _t1463 = _t1466
    end
    result789 = _t1463
    record_span!(parser, span_start788, "Type")
    return result789
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start790 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1505 = Proto.UnspecifiedType()
    result791 = _t1505
    record_span!(parser, span_start790, "UnspecifiedType")
    return result791
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start792 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1506 = Proto.StringType()
    result793 = _t1506
    record_span!(parser, span_start792, "StringType")
    return result793
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start794 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1507 = Proto.IntType()
    result795 = _t1507
    record_span!(parser, span_start794, "IntType")
    return result795
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start796 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1508 = Proto.FloatType()
    result797 = _t1508
    record_span!(parser, span_start796, "FloatType")
    return result797
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start798 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1509 = Proto.UInt128Type()
    result799 = _t1509
    record_span!(parser, span_start798, "UInt128Type")
    return result799
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start800 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1510 = Proto.Int128Type()
    result801 = _t1510
    record_span!(parser, span_start800, "Int128Type")
    return result801
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start802 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1511 = Proto.DateType()
    result803 = _t1511
    record_span!(parser, span_start802, "DateType")
    return result803
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start804 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1512 = Proto.DateTimeType()
    result805 = _t1512
    record_span!(parser, span_start804, "DateTimeType")
    return result805
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start806 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1513 = Proto.MissingType()
    result807 = _t1513
    record_span!(parser, span_start806, "MissingType")
    return result807
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start810 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int808 = consume_terminal!(parser, "INT")
    int_3809 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1514 = Proto.DecimalType(precision=Int32(int808), scale=Int32(int_3809))
    result811 = _t1514
    record_span!(parser, span_start810, "DecimalType")
    return result811
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start812 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1515 = Proto.BooleanType()
    result813 = _t1515
    record_span!(parser, span_start812, "BooleanType")
    return result813
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start814 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1516 = Proto.Int32Type()
    result815 = _t1516
    record_span!(parser, span_start814, "Int32Type")
    return result815
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start816 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1517 = Proto.Float32Type()
    result817 = _t1517
    record_span!(parser, span_start816, "Float32Type")
    return result817
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start818 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1518 = Proto.UInt32Type()
    result819 = _t1518
    record_span!(parser, span_start818, "UInt32Type")
    return result819
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs820 = Proto.Binding[]
    cond821 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond821
        _t1519 = parse_binding(parser)
        item822 = _t1519
        push!(xs820, item822)
        cond821 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings823 = xs820
    return bindings823
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start838 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1521 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1522 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1523 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1524 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1525 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1526 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1527 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1528 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1529 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1530 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1531 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1532 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1533 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1534 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1535 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1536 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1537 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1538 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1539 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1540 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1541 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1542 = 10
                                                                                            else
                                                                                                _t1542 = -1
                                                                                            end
                                                                                            _t1541 = _t1542
                                                                                        end
                                                                                        _t1540 = _t1541
                                                                                    end
                                                                                    _t1539 = _t1540
                                                                                end
                                                                                _t1538 = _t1539
                                                                            end
                                                                            _t1537 = _t1538
                                                                        end
                                                                        _t1536 = _t1537
                                                                    end
                                                                    _t1535 = _t1536
                                                                end
                                                                _t1534 = _t1535
                                                            end
                                                            _t1533 = _t1534
                                                        end
                                                        _t1532 = _t1533
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
            end
            _t1521 = _t1522
        end
        _t1520 = _t1521
    else
        _t1520 = -1
    end
    prediction824 = _t1520
    if prediction824 == 12
        _t1544 = parse_cast(parser)
        cast837 = _t1544
        _t1545 = Proto.Formula(formula_type=OneOf(:cast, cast837))
        _t1543 = _t1545
    else
        if prediction824 == 11
            _t1547 = parse_rel_atom(parser)
            rel_atom836 = _t1547
            _t1548 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom836))
            _t1546 = _t1548
        else
            if prediction824 == 10
                _t1550 = parse_primitive(parser)
                primitive835 = _t1550
                _t1551 = Proto.Formula(formula_type=OneOf(:primitive, primitive835))
                _t1549 = _t1551
            else
                if prediction824 == 9
                    _t1553 = parse_pragma(parser)
                    pragma834 = _t1553
                    _t1554 = Proto.Formula(formula_type=OneOf(:pragma, pragma834))
                    _t1552 = _t1554
                else
                    if prediction824 == 8
                        _t1556 = parse_atom(parser)
                        atom833 = _t1556
                        _t1557 = Proto.Formula(formula_type=OneOf(:atom, atom833))
                        _t1555 = _t1557
                    else
                        if prediction824 == 7
                            _t1559 = parse_ffi(parser)
                            ffi832 = _t1559
                            _t1560 = Proto.Formula(formula_type=OneOf(:ffi, ffi832))
                            _t1558 = _t1560
                        else
                            if prediction824 == 6
                                _t1562 = parse_not(parser)
                                not831 = _t1562
                                _t1563 = Proto.Formula(formula_type=OneOf(:not, not831))
                                _t1561 = _t1563
                            else
                                if prediction824 == 5
                                    _t1565 = parse_disjunction(parser)
                                    disjunction830 = _t1565
                                    _t1566 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction830))
                                    _t1564 = _t1566
                                else
                                    if prediction824 == 4
                                        _t1568 = parse_conjunction(parser)
                                        conjunction829 = _t1568
                                        _t1569 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction829))
                                        _t1567 = _t1569
                                    else
                                        if prediction824 == 3
                                            _t1571 = parse_reduce(parser)
                                            reduce828 = _t1571
                                            _t1572 = Proto.Formula(formula_type=OneOf(:reduce, reduce828))
                                            _t1570 = _t1572
                                        else
                                            if prediction824 == 2
                                                _t1574 = parse_exists(parser)
                                                exists827 = _t1574
                                                _t1575 = Proto.Formula(formula_type=OneOf(:exists, exists827))
                                                _t1573 = _t1575
                                            else
                                                if prediction824 == 1
                                                    _t1577 = parse_false(parser)
                                                    false826 = _t1577
                                                    _t1578 = Proto.Formula(formula_type=OneOf(:disjunction, false826))
                                                    _t1576 = _t1578
                                                else
                                                    if prediction824 == 0
                                                        _t1580 = parse_true(parser)
                                                        true825 = _t1580
                                                        _t1581 = Proto.Formula(formula_type=OneOf(:conjunction, true825))
                                                        _t1579 = _t1581
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1576 = _t1579
                                                end
                                                _t1573 = _t1576
                                            end
                                            _t1570 = _t1573
                                        end
                                        _t1567 = _t1570
                                    end
                                    _t1564 = _t1567
                                end
                                _t1561 = _t1564
                            end
                            _t1558 = _t1561
                        end
                        _t1555 = _t1558
                    end
                    _t1552 = _t1555
                end
                _t1549 = _t1552
            end
            _t1546 = _t1549
        end
        _t1543 = _t1546
    end
    result839 = _t1543
    record_span!(parser, span_start838, "Formula")
    return result839
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start840 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1582 = Proto.Conjunction(args=Proto.Formula[])
    result841 = _t1582
    record_span!(parser, span_start840, "Conjunction")
    return result841
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start842 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1583 = Proto.Disjunction(args=Proto.Formula[])
    result843 = _t1583
    record_span!(parser, span_start842, "Disjunction")
    return result843
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start846 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1584 = parse_bindings(parser)
    bindings844 = _t1584
    _t1585 = parse_formula(parser)
    formula845 = _t1585
    consume_literal!(parser, ")")
    _t1586 = Proto.Abstraction(vars=vcat(bindings844[1], !isnothing(bindings844[2]) ? bindings844[2] : []), value=formula845)
    _t1587 = Proto.Exists(body=_t1586)
    result847 = _t1587
    record_span!(parser, span_start846, "Exists")
    return result847
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start851 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1588 = parse_abstraction(parser)
    abstraction848 = _t1588
    _t1589 = parse_abstraction(parser)
    abstraction_3849 = _t1589
    _t1590 = parse_terms(parser)
    terms850 = _t1590
    consume_literal!(parser, ")")
    _t1591 = Proto.Reduce(op=abstraction848, body=abstraction_3849, terms=terms850)
    result852 = _t1591
    record_span!(parser, span_start851, "Reduce")
    return result852
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs853 = Proto.Term[]
    cond854 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond854
        _t1592 = parse_term(parser)
        item855 = _t1592
        push!(xs853, item855)
        cond854 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms856 = xs853
    consume_literal!(parser, ")")
    return terms856
end

function parse_term(parser::ParserState)::Proto.Term
    span_start860 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1593 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1594 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1595 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1596 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1597 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1598 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1599 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1600 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1601 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1602 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1603 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1604 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1605 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1606 = 1
                                                        else
                                                            _t1606 = -1
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
                        end
                        _t1597 = _t1598
                    end
                    _t1596 = _t1597
                end
                _t1595 = _t1596
            end
            _t1594 = _t1595
        end
        _t1593 = _t1594
    end
    prediction857 = _t1593
    if prediction857 == 1
        _t1608 = parse_value(parser)
        value859 = _t1608
        _t1609 = Proto.Term(term_type=OneOf(:constant, value859))
        _t1607 = _t1609
    else
        if prediction857 == 0
            _t1611 = parse_var(parser)
            var858 = _t1611
            _t1612 = Proto.Term(term_type=OneOf(:var, var858))
            _t1610 = _t1612
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1607 = _t1610
    end
    result861 = _t1607
    record_span!(parser, span_start860, "Term")
    return result861
end

function parse_var(parser::ParserState)::Proto.Var
    span_start863 = span_start(parser)
    symbol862 = consume_terminal!(parser, "SYMBOL")
    _t1613 = Proto.Var(name=symbol862)
    result864 = _t1613
    record_span!(parser, span_start863, "Var")
    return result864
end

function parse_value(parser::ParserState)::Proto.Value
    span_start878 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1614 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1615 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1616 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1618 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1619 = 0
                        else
                            _t1619 = -1
                        end
                        _t1618 = _t1619
                    end
                    _t1617 = _t1618
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1620 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1621 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1622 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1623 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1624 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1625 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1626 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1627 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1628 = 10
                                                    else
                                                        _t1628 = -1
                                                    end
                                                    _t1627 = _t1628
                                                end
                                                _t1626 = _t1627
                                            end
                                            _t1625 = _t1626
                                        end
                                        _t1624 = _t1625
                                    end
                                    _t1623 = _t1624
                                end
                                _t1622 = _t1623
                            end
                            _t1621 = _t1622
                        end
                        _t1620 = _t1621
                    end
                    _t1617 = _t1620
                end
                _t1616 = _t1617
            end
            _t1615 = _t1616
        end
        _t1614 = _t1615
    end
    prediction865 = _t1614
    if prediction865 == 12
        _t1630 = parse_boolean_value(parser)
        boolean_value877 = _t1630
        _t1631 = Proto.Value(value=OneOf(:boolean_value, boolean_value877))
        _t1629 = _t1631
    else
        if prediction865 == 11
            consume_literal!(parser, "missing")
            _t1633 = Proto.MissingValue()
            _t1634 = Proto.Value(value=OneOf(:missing_value, _t1633))
            _t1632 = _t1634
        else
            if prediction865 == 10
                formatted_decimal876 = consume_terminal!(parser, "DECIMAL")
                _t1636 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal876))
                _t1635 = _t1636
            else
                if prediction865 == 9
                    formatted_int128875 = consume_terminal!(parser, "INT128")
                    _t1638 = Proto.Value(value=OneOf(:int128_value, formatted_int128875))
                    _t1637 = _t1638
                else
                    if prediction865 == 8
                        formatted_uint128874 = consume_terminal!(parser, "UINT128")
                        _t1640 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128874))
                        _t1639 = _t1640
                    else
                        if prediction865 == 7
                            formatted_uint32873 = consume_terminal!(parser, "UINT32")
                            _t1642 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32873))
                            _t1641 = _t1642
                        else
                            if prediction865 == 6
                                formatted_float872 = consume_terminal!(parser, "FLOAT")
                                _t1644 = Proto.Value(value=OneOf(:float_value, formatted_float872))
                                _t1643 = _t1644
                            else
                                if prediction865 == 5
                                    formatted_float32871 = consume_terminal!(parser, "FLOAT32")
                                    _t1646 = Proto.Value(value=OneOf(:float32_value, formatted_float32871))
                                    _t1645 = _t1646
                                else
                                    if prediction865 == 4
                                        formatted_int870 = consume_terminal!(parser, "INT")
                                        _t1648 = Proto.Value(value=OneOf(:int_value, formatted_int870))
                                        _t1647 = _t1648
                                    else
                                        if prediction865 == 3
                                            formatted_int32869 = consume_terminal!(parser, "INT32")
                                            _t1650 = Proto.Value(value=OneOf(:int32_value, formatted_int32869))
                                            _t1649 = _t1650
                                        else
                                            if prediction865 == 2
                                                formatted_string868 = consume_terminal!(parser, "STRING")
                                                _t1652 = Proto.Value(value=OneOf(:string_value, formatted_string868))
                                                _t1651 = _t1652
                                            else
                                                if prediction865 == 1
                                                    _t1654 = parse_datetime(parser)
                                                    datetime867 = _t1654
                                                    _t1655 = Proto.Value(value=OneOf(:datetime_value, datetime867))
                                                    _t1653 = _t1655
                                                else
                                                    if prediction865 == 0
                                                        _t1657 = parse_date(parser)
                                                        date866 = _t1657
                                                        _t1658 = Proto.Value(value=OneOf(:date_value, date866))
                                                        _t1656 = _t1658
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1653 = _t1656
                                                end
                                                _t1651 = _t1653
                                            end
                                            _t1649 = _t1651
                                        end
                                        _t1647 = _t1649
                                    end
                                    _t1645 = _t1647
                                end
                                _t1643 = _t1645
                            end
                            _t1641 = _t1643
                        end
                        _t1639 = _t1641
                    end
                    _t1637 = _t1639
                end
                _t1635 = _t1637
            end
            _t1632 = _t1635
        end
        _t1629 = _t1632
    end
    result879 = _t1629
    record_span!(parser, span_start878, "Value")
    return result879
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start883 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int880 = consume_terminal!(parser, "INT")
    formatted_int_3881 = consume_terminal!(parser, "INT")
    formatted_int_4882 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1659 = Proto.DateValue(year=Int32(formatted_int880), month=Int32(formatted_int_3881), day=Int32(formatted_int_4882))
    result884 = _t1659
    record_span!(parser, span_start883, "DateValue")
    return result884
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start892 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int885 = consume_terminal!(parser, "INT")
    formatted_int_3886 = consume_terminal!(parser, "INT")
    formatted_int_4887 = consume_terminal!(parser, "INT")
    formatted_int_5888 = consume_terminal!(parser, "INT")
    formatted_int_6889 = consume_terminal!(parser, "INT")
    formatted_int_7890 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1660 = consume_terminal!(parser, "INT")
    else
        _t1660 = nothing
    end
    formatted_int_8891 = _t1660
    consume_literal!(parser, ")")
    _t1661 = Proto.DateTimeValue(year=Int32(formatted_int885), month=Int32(formatted_int_3886), day=Int32(formatted_int_4887), hour=Int32(formatted_int_5888), minute=Int32(formatted_int_6889), second=Int32(formatted_int_7890), microsecond=Int32((!isnothing(formatted_int_8891) ? formatted_int_8891 : 0)))
    result893 = _t1661
    record_span!(parser, span_start892, "DateTimeValue")
    return result893
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start898 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs894 = Proto.Formula[]
    cond895 = match_lookahead_literal(parser, "(", 0)
    while cond895
        _t1662 = parse_formula(parser)
        item896 = _t1662
        push!(xs894, item896)
        cond895 = match_lookahead_literal(parser, "(", 0)
    end
    formulas897 = xs894
    consume_literal!(parser, ")")
    _t1663 = Proto.Conjunction(args=formulas897)
    result899 = _t1663
    record_span!(parser, span_start898, "Conjunction")
    return result899
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start904 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs900 = Proto.Formula[]
    cond901 = match_lookahead_literal(parser, "(", 0)
    while cond901
        _t1664 = parse_formula(parser)
        item902 = _t1664
        push!(xs900, item902)
        cond901 = match_lookahead_literal(parser, "(", 0)
    end
    formulas903 = xs900
    consume_literal!(parser, ")")
    _t1665 = Proto.Disjunction(args=formulas903)
    result905 = _t1665
    record_span!(parser, span_start904, "Disjunction")
    return result905
end

function parse_not(parser::ParserState)::Proto.Not
    span_start907 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1666 = parse_formula(parser)
    formula906 = _t1666
    consume_literal!(parser, ")")
    _t1667 = Proto.Not(arg=formula906)
    result908 = _t1667
    record_span!(parser, span_start907, "Not")
    return result908
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start912 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1668 = parse_name(parser)
    name909 = _t1668
    _t1669 = parse_ffi_args(parser)
    ffi_args910 = _t1669
    _t1670 = parse_terms(parser)
    terms911 = _t1670
    consume_literal!(parser, ")")
    _t1671 = Proto.FFI(name=name909, args=ffi_args910, terms=terms911)
    result913 = _t1671
    record_span!(parser, span_start912, "FFI")
    return result913
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol914 = consume_terminal!(parser, "SYMBOL")
    return symbol914
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs915 = Proto.Abstraction[]
    cond916 = match_lookahead_literal(parser, "(", 0)
    while cond916
        _t1672 = parse_abstraction(parser)
        item917 = _t1672
        push!(xs915, item917)
        cond916 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions918 = xs915
    consume_literal!(parser, ")")
    return abstractions918
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start924 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1673 = parse_relation_id(parser)
    relation_id919 = _t1673
    xs920 = Proto.Term[]
    cond921 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond921
        _t1674 = parse_term(parser)
        item922 = _t1674
        push!(xs920, item922)
        cond921 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms923 = xs920
    consume_literal!(parser, ")")
    _t1675 = Proto.Atom(name=relation_id919, terms=terms923)
    result925 = _t1675
    record_span!(parser, span_start924, "Atom")
    return result925
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start931 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1676 = parse_name(parser)
    name926 = _t1676
    xs927 = Proto.Term[]
    cond928 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond928
        _t1677 = parse_term(parser)
        item929 = _t1677
        push!(xs927, item929)
        cond928 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms930 = xs927
    consume_literal!(parser, ")")
    _t1678 = Proto.Pragma(name=name926, terms=terms930)
    result932 = _t1678
    record_span!(parser, span_start931, "Pragma")
    return result932
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start948 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1680 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1681 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1682 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1683 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1684 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1685 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1686 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1687 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1688 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1689 = 7
                                            else
                                                _t1689 = -1
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
                        _t1683 = _t1684
                    end
                    _t1682 = _t1683
                end
                _t1681 = _t1682
            end
            _t1680 = _t1681
        end
        _t1679 = _t1680
    else
        _t1679 = -1
    end
    prediction933 = _t1679
    if prediction933 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1691 = parse_name(parser)
        name943 = _t1691
        xs944 = Proto.RelTerm[]
        cond945 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond945
            _t1692 = parse_rel_term(parser)
            item946 = _t1692
            push!(xs944, item946)
            cond945 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms947 = xs944
        consume_literal!(parser, ")")
        _t1693 = Proto.Primitive(name=name943, terms=rel_terms947)
        _t1690 = _t1693
    else
        if prediction933 == 8
            _t1695 = parse_divide(parser)
            divide942 = _t1695
            _t1694 = divide942
        else
            if prediction933 == 7
                _t1697 = parse_multiply(parser)
                multiply941 = _t1697
                _t1696 = multiply941
            else
                if prediction933 == 6
                    _t1699 = parse_minus(parser)
                    minus940 = _t1699
                    _t1698 = minus940
                else
                    if prediction933 == 5
                        _t1701 = parse_add(parser)
                        add939 = _t1701
                        _t1700 = add939
                    else
                        if prediction933 == 4
                            _t1703 = parse_gt_eq(parser)
                            gt_eq938 = _t1703
                            _t1702 = gt_eq938
                        else
                            if prediction933 == 3
                                _t1705 = parse_gt(parser)
                                gt937 = _t1705
                                _t1704 = gt937
                            else
                                if prediction933 == 2
                                    _t1707 = parse_lt_eq(parser)
                                    lt_eq936 = _t1707
                                    _t1706 = lt_eq936
                                else
                                    if prediction933 == 1
                                        _t1709 = parse_lt(parser)
                                        lt935 = _t1709
                                        _t1708 = lt935
                                    else
                                        if prediction933 == 0
                                            _t1711 = parse_eq(parser)
                                            eq934 = _t1711
                                            _t1710 = eq934
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1708 = _t1710
                                    end
                                    _t1706 = _t1708
                                end
                                _t1704 = _t1706
                            end
                            _t1702 = _t1704
                        end
                        _t1700 = _t1702
                    end
                    _t1698 = _t1700
                end
                _t1696 = _t1698
            end
            _t1694 = _t1696
        end
        _t1690 = _t1694
    end
    result949 = _t1690
    record_span!(parser, span_start948, "Primitive")
    return result949
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1712 = parse_term(parser)
    term950 = _t1712
    _t1713 = parse_term(parser)
    term_3951 = _t1713
    consume_literal!(parser, ")")
    _t1714 = Proto.RelTerm(rel_term_type=OneOf(:term, term950))
    _t1715 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3951))
    _t1716 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1714, _t1715])
    result953 = _t1716
    record_span!(parser, span_start952, "Primitive")
    return result953
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start956 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1717 = parse_term(parser)
    term954 = _t1717
    _t1718 = parse_term(parser)
    term_3955 = _t1718
    consume_literal!(parser, ")")
    _t1719 = Proto.RelTerm(rel_term_type=OneOf(:term, term954))
    _t1720 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3955))
    _t1721 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1719, _t1720])
    result957 = _t1721
    record_span!(parser, span_start956, "Primitive")
    return result957
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1722 = parse_term(parser)
    term958 = _t1722
    _t1723 = parse_term(parser)
    term_3959 = _t1723
    consume_literal!(parser, ")")
    _t1724 = Proto.RelTerm(rel_term_type=OneOf(:term, term958))
    _t1725 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3959))
    _t1726 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1724, _t1725])
    result961 = _t1726
    record_span!(parser, span_start960, "Primitive")
    return result961
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start964 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1727 = parse_term(parser)
    term962 = _t1727
    _t1728 = parse_term(parser)
    term_3963 = _t1728
    consume_literal!(parser, ")")
    _t1729 = Proto.RelTerm(rel_term_type=OneOf(:term, term962))
    _t1730 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3963))
    _t1731 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1729, _t1730])
    result965 = _t1731
    record_span!(parser, span_start964, "Primitive")
    return result965
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start968 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1732 = parse_term(parser)
    term966 = _t1732
    _t1733 = parse_term(parser)
    term_3967 = _t1733
    consume_literal!(parser, ")")
    _t1734 = Proto.RelTerm(rel_term_type=OneOf(:term, term966))
    _t1735 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3967))
    _t1736 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1734, _t1735])
    result969 = _t1736
    record_span!(parser, span_start968, "Primitive")
    return result969
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start973 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1737 = parse_term(parser)
    term970 = _t1737
    _t1738 = parse_term(parser)
    term_3971 = _t1738
    _t1739 = parse_term(parser)
    term_4972 = _t1739
    consume_literal!(parser, ")")
    _t1740 = Proto.RelTerm(rel_term_type=OneOf(:term, term970))
    _t1741 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3971))
    _t1742 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4972))
    _t1743 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1740, _t1741, _t1742])
    result974 = _t1743
    record_span!(parser, span_start973, "Primitive")
    return result974
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start978 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1744 = parse_term(parser)
    term975 = _t1744
    _t1745 = parse_term(parser)
    term_3976 = _t1745
    _t1746 = parse_term(parser)
    term_4977 = _t1746
    consume_literal!(parser, ")")
    _t1747 = Proto.RelTerm(rel_term_type=OneOf(:term, term975))
    _t1748 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3976))
    _t1749 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4977))
    _t1750 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1747, _t1748, _t1749])
    result979 = _t1750
    record_span!(parser, span_start978, "Primitive")
    return result979
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start983 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1751 = parse_term(parser)
    term980 = _t1751
    _t1752 = parse_term(parser)
    term_3981 = _t1752
    _t1753 = parse_term(parser)
    term_4982 = _t1753
    consume_literal!(parser, ")")
    _t1754 = Proto.RelTerm(rel_term_type=OneOf(:term, term980))
    _t1755 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3981))
    _t1756 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4982))
    _t1757 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1754, _t1755, _t1756])
    result984 = _t1757
    record_span!(parser, span_start983, "Primitive")
    return result984
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start988 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1758 = parse_term(parser)
    term985 = _t1758
    _t1759 = parse_term(parser)
    term_3986 = _t1759
    _t1760 = parse_term(parser)
    term_4987 = _t1760
    consume_literal!(parser, ")")
    _t1761 = Proto.RelTerm(rel_term_type=OneOf(:term, term985))
    _t1762 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3986))
    _t1763 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4987))
    _t1764 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1761, _t1762, _t1763])
    result989 = _t1764
    record_span!(parser, span_start988, "Primitive")
    return result989
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start993 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1765 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1766 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1767 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1768 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1769 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1770 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1771 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1772 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1773 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1774 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1775 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1776 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1777 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1778 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1779 = 1
                                                            else
                                                                _t1779 = -1
                                                            end
                                                            _t1778 = _t1779
                                                        end
                                                        _t1777 = _t1778
                                                    end
                                                    _t1776 = _t1777
                                                end
                                                _t1775 = _t1776
                                            end
                                            _t1774 = _t1775
                                        end
                                        _t1773 = _t1774
                                    end
                                    _t1772 = _t1773
                                end
                                _t1771 = _t1772
                            end
                            _t1770 = _t1771
                        end
                        _t1769 = _t1770
                    end
                    _t1768 = _t1769
                end
                _t1767 = _t1768
            end
            _t1766 = _t1767
        end
        _t1765 = _t1766
    end
    prediction990 = _t1765
    if prediction990 == 1
        _t1781 = parse_term(parser)
        term992 = _t1781
        _t1782 = Proto.RelTerm(rel_term_type=OneOf(:term, term992))
        _t1780 = _t1782
    else
        if prediction990 == 0
            _t1784 = parse_specialized_value(parser)
            specialized_value991 = _t1784
            _t1785 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value991))
            _t1783 = _t1785
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1780 = _t1783
    end
    result994 = _t1780
    record_span!(parser, span_start993, "RelTerm")
    return result994
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start996 = span_start(parser)
    consume_literal!(parser, "#")
    _t1786 = parse_raw_value(parser)
    raw_value995 = _t1786
    result997 = raw_value995
    record_span!(parser, span_start996, "Value")
    return result997
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1003 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1787 = parse_name(parser)
    name998 = _t1787
    xs999 = Proto.RelTerm[]
    cond1000 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1000
        _t1788 = parse_rel_term(parser)
        item1001 = _t1788
        push!(xs999, item1001)
        cond1000 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1002 = xs999
    consume_literal!(parser, ")")
    _t1789 = Proto.RelAtom(name=name998, terms=rel_terms1002)
    result1004 = _t1789
    record_span!(parser, span_start1003, "RelAtom")
    return result1004
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1007 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1790 = parse_term(parser)
    term1005 = _t1790
    _t1791 = parse_term(parser)
    term_31006 = _t1791
    consume_literal!(parser, ")")
    _t1792 = Proto.Cast(input=term1005, result=term_31006)
    result1008 = _t1792
    record_span!(parser, span_start1007, "Cast")
    return result1008
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1009 = Proto.Attribute[]
    cond1010 = match_lookahead_literal(parser, "(", 0)
    while cond1010
        _t1793 = parse_attribute(parser)
        item1011 = _t1793
        push!(xs1009, item1011)
        cond1010 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1012 = xs1009
    consume_literal!(parser, ")")
    return attributes1012
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1018 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1794 = parse_name(parser)
    name1013 = _t1794
    xs1014 = Proto.Value[]
    cond1015 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1015
        _t1795 = parse_raw_value(parser)
        item1016 = _t1795
        push!(xs1014, item1016)
        cond1015 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1017 = xs1014
    consume_literal!(parser, ")")
    _t1796 = Proto.Attribute(name=name1013, args=raw_values1017)
    result1019 = _t1796
    record_span!(parser, span_start1018, "Attribute")
    return result1019
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1025 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1020 = Proto.RelationId[]
    cond1021 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1021
        _t1797 = parse_relation_id(parser)
        item1022 = _t1797
        push!(xs1020, item1022)
        cond1021 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1023 = xs1020
    _t1798 = parse_script(parser)
    script1024 = _t1798
    consume_literal!(parser, ")")
    _t1799 = Proto.Algorithm(var"#global"=relation_ids1023, body=script1024)
    result1026 = _t1799
    record_span!(parser, span_start1025, "Algorithm")
    return result1026
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1031 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1027 = Proto.Construct[]
    cond1028 = match_lookahead_literal(parser, "(", 0)
    while cond1028
        _t1800 = parse_construct(parser)
        item1029 = _t1800
        push!(xs1027, item1029)
        cond1028 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1030 = xs1027
    consume_literal!(parser, ")")
    _t1801 = Proto.Script(constructs=constructs1030)
    result1032 = _t1801
    record_span!(parser, span_start1031, "Script")
    return result1032
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1036 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1803 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1804 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1805 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1806 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1807 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1808 = 1
                            else
                                _t1808 = -1
                            end
                            _t1807 = _t1808
                        end
                        _t1806 = _t1807
                    end
                    _t1805 = _t1806
                end
                _t1804 = _t1805
            end
            _t1803 = _t1804
        end
        _t1802 = _t1803
    else
        _t1802 = -1
    end
    prediction1033 = _t1802
    if prediction1033 == 1
        _t1810 = parse_instruction(parser)
        instruction1035 = _t1810
        _t1811 = Proto.Construct(construct_type=OneOf(:instruction, instruction1035))
        _t1809 = _t1811
    else
        if prediction1033 == 0
            _t1813 = parse_loop(parser)
            loop1034 = _t1813
            _t1814 = Proto.Construct(construct_type=OneOf(:loop, loop1034))
            _t1812 = _t1814
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1809 = _t1812
    end
    result1037 = _t1809
    record_span!(parser, span_start1036, "Construct")
    return result1037
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1040 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1815 = parse_init(parser)
    init1038 = _t1815
    _t1816 = parse_script(parser)
    script1039 = _t1816
    consume_literal!(parser, ")")
    _t1817 = Proto.Loop(init=init1038, body=script1039)
    result1041 = _t1817
    record_span!(parser, span_start1040, "Loop")
    return result1041
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1042 = Proto.Instruction[]
    cond1043 = match_lookahead_literal(parser, "(", 0)
    while cond1043
        _t1818 = parse_instruction(parser)
        item1044 = _t1818
        push!(xs1042, item1044)
        cond1043 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1045 = xs1042
    consume_literal!(parser, ")")
    return instructions1045
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1052 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1820 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1821 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1822 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1823 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1824 = 0
                        else
                            _t1824 = -1
                        end
                        _t1823 = _t1824
                    end
                    _t1822 = _t1823
                end
                _t1821 = _t1822
            end
            _t1820 = _t1821
        end
        _t1819 = _t1820
    else
        _t1819 = -1
    end
    prediction1046 = _t1819
    if prediction1046 == 4
        _t1826 = parse_monus_def(parser)
        monus_def1051 = _t1826
        _t1827 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1051))
        _t1825 = _t1827
    else
        if prediction1046 == 3
            _t1829 = parse_monoid_def(parser)
            monoid_def1050 = _t1829
            _t1830 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1050))
            _t1828 = _t1830
        else
            if prediction1046 == 2
                _t1832 = parse_break(parser)
                break1049 = _t1832
                _t1833 = Proto.Instruction(instr_type=OneOf(:var"#break", break1049))
                _t1831 = _t1833
            else
                if prediction1046 == 1
                    _t1835 = parse_upsert(parser)
                    upsert1048 = _t1835
                    _t1836 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1048))
                    _t1834 = _t1836
                else
                    if prediction1046 == 0
                        _t1838 = parse_assign(parser)
                        assign1047 = _t1838
                        _t1839 = Proto.Instruction(instr_type=OneOf(:assign, assign1047))
                        _t1837 = _t1839
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1834 = _t1837
                end
                _t1831 = _t1834
            end
            _t1828 = _t1831
        end
        _t1825 = _t1828
    end
    result1053 = _t1825
    record_span!(parser, span_start1052, "Instruction")
    return result1053
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1057 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1840 = parse_relation_id(parser)
    relation_id1054 = _t1840
    _t1841 = parse_abstraction(parser)
    abstraction1055 = _t1841
    if match_lookahead_literal(parser, "(", 0)
        _t1843 = parse_attrs(parser)
        _t1842 = _t1843
    else
        _t1842 = nothing
    end
    attrs1056 = _t1842
    consume_literal!(parser, ")")
    _t1844 = Proto.Assign(name=relation_id1054, body=abstraction1055, attrs=(!isnothing(attrs1056) ? attrs1056 : Proto.Attribute[]))
    result1058 = _t1844
    record_span!(parser, span_start1057, "Assign")
    return result1058
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1062 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1845 = parse_relation_id(parser)
    relation_id1059 = _t1845
    _t1846 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1060 = _t1846
    if match_lookahead_literal(parser, "(", 0)
        _t1848 = parse_attrs(parser)
        _t1847 = _t1848
    else
        _t1847 = nothing
    end
    attrs1061 = _t1847
    consume_literal!(parser, ")")
    _t1849 = Proto.Upsert(name=relation_id1059, body=abstraction_with_arity1060[1], attrs=(!isnothing(attrs1061) ? attrs1061 : Proto.Attribute[]), value_arity=abstraction_with_arity1060[2])
    result1063 = _t1849
    record_span!(parser, span_start1062, "Upsert")
    return result1063
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1850 = parse_bindings(parser)
    bindings1064 = _t1850
    _t1851 = parse_formula(parser)
    formula1065 = _t1851
    consume_literal!(parser, ")")
    _t1852 = Proto.Abstraction(vars=vcat(bindings1064[1], !isnothing(bindings1064[2]) ? bindings1064[2] : []), value=formula1065)
    return (_t1852, length(bindings1064[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1069 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1853 = parse_relation_id(parser)
    relation_id1066 = _t1853
    _t1854 = parse_abstraction(parser)
    abstraction1067 = _t1854
    if match_lookahead_literal(parser, "(", 0)
        _t1856 = parse_attrs(parser)
        _t1855 = _t1856
    else
        _t1855 = nothing
    end
    attrs1068 = _t1855
    consume_literal!(parser, ")")
    _t1857 = Proto.Break(name=relation_id1066, body=abstraction1067, attrs=(!isnothing(attrs1068) ? attrs1068 : Proto.Attribute[]))
    result1070 = _t1857
    record_span!(parser, span_start1069, "Break")
    return result1070
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1075 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1858 = parse_monoid(parser)
    monoid1071 = _t1858
    _t1859 = parse_relation_id(parser)
    relation_id1072 = _t1859
    _t1860 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1073 = _t1860
    if match_lookahead_literal(parser, "(", 0)
        _t1862 = parse_attrs(parser)
        _t1861 = _t1862
    else
        _t1861 = nothing
    end
    attrs1074 = _t1861
    consume_literal!(parser, ")")
    _t1863 = Proto.MonoidDef(monoid=monoid1071, name=relation_id1072, body=abstraction_with_arity1073[1], attrs=(!isnothing(attrs1074) ? attrs1074 : Proto.Attribute[]), value_arity=abstraction_with_arity1073[2])
    result1076 = _t1863
    record_span!(parser, span_start1075, "MonoidDef")
    return result1076
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1082 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1865 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1866 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1867 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1868 = 2
                    else
                        _t1868 = -1
                    end
                    _t1867 = _t1868
                end
                _t1866 = _t1867
            end
            _t1865 = _t1866
        end
        _t1864 = _t1865
    else
        _t1864 = -1
    end
    prediction1077 = _t1864
    if prediction1077 == 3
        _t1870 = parse_sum_monoid(parser)
        sum_monoid1081 = _t1870
        _t1871 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1081))
        _t1869 = _t1871
    else
        if prediction1077 == 2
            _t1873 = parse_max_monoid(parser)
            max_monoid1080 = _t1873
            _t1874 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1080))
            _t1872 = _t1874
        else
            if prediction1077 == 1
                _t1876 = parse_min_monoid(parser)
                min_monoid1079 = _t1876
                _t1877 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1079))
                _t1875 = _t1877
            else
                if prediction1077 == 0
                    _t1879 = parse_or_monoid(parser)
                    or_monoid1078 = _t1879
                    _t1880 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1078))
                    _t1878 = _t1880
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1875 = _t1878
            end
            _t1872 = _t1875
        end
        _t1869 = _t1872
    end
    result1083 = _t1869
    record_span!(parser, span_start1082, "Monoid")
    return result1083
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1084 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1881 = Proto.OrMonoid()
    result1085 = _t1881
    record_span!(parser, span_start1084, "OrMonoid")
    return result1085
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1087 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1882 = parse_type(parser)
    type1086 = _t1882
    consume_literal!(parser, ")")
    _t1883 = Proto.MinMonoid(var"#type"=type1086)
    result1088 = _t1883
    record_span!(parser, span_start1087, "MinMonoid")
    return result1088
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1090 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1884 = parse_type(parser)
    type1089 = _t1884
    consume_literal!(parser, ")")
    _t1885 = Proto.MaxMonoid(var"#type"=type1089)
    result1091 = _t1885
    record_span!(parser, span_start1090, "MaxMonoid")
    return result1091
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1093 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1886 = parse_type(parser)
    type1092 = _t1886
    consume_literal!(parser, ")")
    _t1887 = Proto.SumMonoid(var"#type"=type1092)
    result1094 = _t1887
    record_span!(parser, span_start1093, "SumMonoid")
    return result1094
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1099 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1888 = parse_monoid(parser)
    monoid1095 = _t1888
    _t1889 = parse_relation_id(parser)
    relation_id1096 = _t1889
    _t1890 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1097 = _t1890
    if match_lookahead_literal(parser, "(", 0)
        _t1892 = parse_attrs(parser)
        _t1891 = _t1892
    else
        _t1891 = nothing
    end
    attrs1098 = _t1891
    consume_literal!(parser, ")")
    _t1893 = Proto.MonusDef(monoid=monoid1095, name=relation_id1096, body=abstraction_with_arity1097[1], attrs=(!isnothing(attrs1098) ? attrs1098 : Proto.Attribute[]), value_arity=abstraction_with_arity1097[2])
    result1100 = _t1893
    record_span!(parser, span_start1099, "MonusDef")
    return result1100
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1105 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1894 = parse_relation_id(parser)
    relation_id1101 = _t1894
    _t1895 = parse_abstraction(parser)
    abstraction1102 = _t1895
    _t1896 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1103 = _t1896
    _t1897 = parse_functional_dependency_values(parser)
    functional_dependency_values1104 = _t1897
    consume_literal!(parser, ")")
    _t1898 = Proto.FunctionalDependency(guard=abstraction1102, keys=functional_dependency_keys1103, values=functional_dependency_values1104)
    _t1899 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1898), name=relation_id1101)
    result1106 = _t1899
    record_span!(parser, span_start1105, "Constraint")
    return result1106
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1107 = Proto.Var[]
    cond1108 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1108
        _t1900 = parse_var(parser)
        item1109 = _t1900
        push!(xs1107, item1109)
        cond1108 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1110 = xs1107
    consume_literal!(parser, ")")
    return vars1110
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1111 = Proto.Var[]
    cond1112 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1112
        _t1901 = parse_var(parser)
        item1113 = _t1901
        push!(xs1111, item1113)
        cond1112 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1114 = xs1111
    consume_literal!(parser, ")")
    return vars1114
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1120 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1903 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1904 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1905 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1906 = 1
                    else
                        _t1906 = -1
                    end
                    _t1905 = _t1906
                end
                _t1904 = _t1905
            end
            _t1903 = _t1904
        end
        _t1902 = _t1903
    else
        _t1902 = -1
    end
    prediction1115 = _t1902
    if prediction1115 == 3
        _t1908 = parse_iceberg_data(parser)
        iceberg_data1119 = _t1908
        _t1909 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1119))
        _t1907 = _t1909
    else
        if prediction1115 == 2
            _t1911 = parse_csv_data(parser)
            csv_data1118 = _t1911
            _t1912 = Proto.Data(data_type=OneOf(:csv_data, csv_data1118))
            _t1910 = _t1912
        else
            if prediction1115 == 1
                _t1914 = parse_betree_relation(parser)
                betree_relation1117 = _t1914
                _t1915 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1117))
                _t1913 = _t1915
            else
                if prediction1115 == 0
                    _t1917 = parse_edb(parser)
                    edb1116 = _t1917
                    _t1918 = Proto.Data(data_type=OneOf(:edb, edb1116))
                    _t1916 = _t1918
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1913 = _t1916
            end
            _t1910 = _t1913
        end
        _t1907 = _t1910
    end
    result1121 = _t1907
    record_span!(parser, span_start1120, "Data")
    return result1121
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1125 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1919 = parse_relation_id(parser)
    relation_id1122 = _t1919
    _t1920 = parse_edb_path(parser)
    edb_path1123 = _t1920
    _t1921 = parse_edb_types(parser)
    edb_types1124 = _t1921
    consume_literal!(parser, ")")
    _t1922 = Proto.EDB(target_id=relation_id1122, path=edb_path1123, types=edb_types1124)
    result1126 = _t1922
    record_span!(parser, span_start1125, "EDB")
    return result1126
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1127 = String[]
    cond1128 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1128
        item1129 = consume_terminal!(parser, "STRING")
        push!(xs1127, item1129)
        cond1128 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1130 = xs1127
    consume_literal!(parser, "]")
    return strings1130
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1131 = Proto.var"#Type"[]
    cond1132 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1132
        _t1923 = parse_type(parser)
        item1133 = _t1923
        push!(xs1131, item1133)
        cond1132 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1134 = xs1131
    consume_literal!(parser, "]")
    return types1134
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1137 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1924 = parse_relation_id(parser)
    relation_id1135 = _t1924
    _t1925 = parse_betree_info(parser)
    betree_info1136 = _t1925
    consume_literal!(parser, ")")
    _t1926 = Proto.BeTreeRelation(name=relation_id1135, relation_info=betree_info1136)
    result1138 = _t1926
    record_span!(parser, span_start1137, "BeTreeRelation")
    return result1138
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1142 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1927 = parse_betree_info_key_types(parser)
    betree_info_key_types1139 = _t1927
    _t1928 = parse_betree_info_value_types(parser)
    betree_info_value_types1140 = _t1928
    _t1929 = parse_config_dict(parser)
    config_dict1141 = _t1929
    consume_literal!(parser, ")")
    _t1930 = construct_betree_info(parser, betree_info_key_types1139, betree_info_value_types1140, config_dict1141)
    result1143 = _t1930
    record_span!(parser, span_start1142, "BeTreeInfo")
    return result1143
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1144 = Proto.var"#Type"[]
    cond1145 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1145
        _t1931 = parse_type(parser)
        item1146 = _t1931
        push!(xs1144, item1146)
        cond1145 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1147 = xs1144
    consume_literal!(parser, ")")
    return types1147
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1148 = Proto.var"#Type"[]
    cond1149 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1149
        _t1932 = parse_type(parser)
        item1150 = _t1932
        push!(xs1148, item1150)
        cond1149 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1151 = xs1148
    consume_literal!(parser, ")")
    return types1151
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1156 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1933 = parse_csvlocator(parser)
    csvlocator1152 = _t1933
    _t1934 = parse_csv_config(parser)
    csv_config1153 = _t1934
    _t1935 = parse_gnf_columns(parser)
    gnf_columns1154 = _t1935
    _t1936 = parse_csv_asof(parser)
    csv_asof1155 = _t1936
    consume_literal!(parser, ")")
    _t1937 = Proto.CSVData(locator=csvlocator1152, config=csv_config1153, columns=gnf_columns1154, asof=csv_asof1155)
    result1157 = _t1937
    record_span!(parser, span_start1156, "CSVData")
    return result1157
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1160 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1939 = parse_csv_locator_paths(parser)
        _t1938 = _t1939
    else
        _t1938 = nothing
    end
    csv_locator_paths1158 = _t1938
    if match_lookahead_literal(parser, "(", 0)
        _t1941 = parse_csv_locator_inline_data(parser)
        _t1940 = _t1941
    else
        _t1940 = nothing
    end
    csv_locator_inline_data1159 = _t1940
    consume_literal!(parser, ")")
    _t1942 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1158) ? csv_locator_paths1158 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1159) ? csv_locator_inline_data1159 : "")))
    result1161 = _t1942
    record_span!(parser, span_start1160, "CSVLocator")
    return result1161
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1162 = String[]
    cond1163 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1163
        item1164 = consume_terminal!(parser, "STRING")
        push!(xs1162, item1164)
        cond1163 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1165 = xs1162
    consume_literal!(parser, ")")
    return strings1165
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1166 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1166
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1168 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1943 = parse_config_dict(parser)
    config_dict1167 = _t1943
    consume_literal!(parser, ")")
    _t1944 = construct_csv_config(parser, config_dict1167)
    result1169 = _t1944
    record_span!(parser, span_start1168, "CSVConfig")
    return result1169
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1170 = Proto.GNFColumn[]
    cond1171 = match_lookahead_literal(parser, "(", 0)
    while cond1171
        _t1945 = parse_gnf_column(parser)
        item1172 = _t1945
        push!(xs1170, item1172)
        cond1171 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1173 = xs1170
    consume_literal!(parser, ")")
    return gnf_columns1173
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1180 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1946 = parse_gnf_column_path(parser)
    gnf_column_path1174 = _t1946
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1948 = parse_relation_id(parser)
        _t1947 = _t1948
    else
        _t1947 = nothing
    end
    relation_id1175 = _t1947
    consume_literal!(parser, "[")
    xs1176 = Proto.var"#Type"[]
    cond1177 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1177
        _t1949 = parse_type(parser)
        item1178 = _t1949
        push!(xs1176, item1178)
        cond1177 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1179 = xs1176
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1950 = Proto.GNFColumn(column_path=gnf_column_path1174, target_id=relation_id1175, types=types1179)
    result1181 = _t1950
    record_span!(parser, span_start1180, "GNFColumn")
    return result1181
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1951 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1952 = 0
        else
            _t1952 = -1
        end
        _t1951 = _t1952
    end
    prediction1182 = _t1951
    if prediction1182 == 1
        consume_literal!(parser, "[")
        xs1184 = String[]
        cond1185 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1185
            item1186 = consume_terminal!(parser, "STRING")
            push!(xs1184, item1186)
            cond1185 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1187 = xs1184
        consume_literal!(parser, "]")
        _t1953 = strings1187
    else
        if prediction1182 == 0
            string1183 = consume_terminal!(parser, "STRING")
            _t1954 = String[string1183]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1953 = _t1954
    end
    return _t1953
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1188 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1188
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1193 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1955 = parse_iceberg_locator(parser)
    iceberg_locator1189 = _t1955
    _t1956 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1190 = _t1956
    _t1957 = parse_gnf_columns(parser)
    gnf_columns1191 = _t1957
    if match_lookahead_literal(parser, "(", 0)
        _t1959 = parse_iceberg_to_snapshot(parser)
        _t1958 = _t1959
    else
        _t1958 = nothing
    end
    iceberg_to_snapshot1192 = _t1958
    consume_literal!(parser, ")")
    _t1960 = Proto.IcebergData(locator=iceberg_locator1189, config=iceberg_catalog_config1190, columns=gnf_columns1191, to_snapshot=(!isnothing(iceberg_to_snapshot1192) ? iceberg_to_snapshot1192 : ""))
    result1194 = _t1960
    record_span!(parser, span_start1193, "IcebergData")
    return result1194
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1201 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1195 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1196 = String[]
    cond1197 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1197
        item1198 = consume_terminal!(parser, "STRING")
        push!(xs1196, item1198)
        cond1197 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1199 = xs1196
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string_121200 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1961 = Proto.IcebergLocator(table_name=string1195, namespace=strings1199, warehouse=string_121200)
    result1202 = _t1961
    record_span!(parser, span_start1201, "IcebergLocator")
    return result1202
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1213 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1203 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1963 = parse_iceberg_catalog_config_scope(parser)
        _t1962 = _t1963
    else
        _t1962 = nothing
    end
    iceberg_catalog_config_scope1204 = _t1962
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1205 = Tuple{String, String}[]
    cond1206 = match_lookahead_literal(parser, "(", 0)
    while cond1206
        _t1964 = parse_iceberg_property_entry(parser)
        item1207 = _t1964
        push!(xs1205, item1207)
        cond1206 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1208 = xs1205
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1209 = Tuple{String, String}[]
    cond1210 = match_lookahead_literal(parser, "(", 0)
    while cond1210
        _t1965 = parse_iceberg_property_entry(parser)
        item1211 = _t1965
        push!(xs1209, item1211)
        cond1210 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys_131212 = xs1209
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1966 = construct_iceberg_catalog_config(parser, string1203, iceberg_catalog_config_scope1204, iceberg_property_entrys1208, iceberg_property_entrys_131212)
    result1214 = _t1966
    record_span!(parser, span_start1213, "IcebergCatalogConfig")
    return result1214
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1215 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1215
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1216 = consume_terminal!(parser, "STRING")
    string_31217 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1216, string_31217,)
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1218 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1218
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1220 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1967 = parse_fragment_id(parser)
    fragment_id1219 = _t1967
    consume_literal!(parser, ")")
    _t1968 = Proto.Undefine(fragment_id=fragment_id1219)
    result1221 = _t1968
    record_span!(parser, span_start1220, "Undefine")
    return result1221
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1226 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1222 = Proto.RelationId[]
    cond1223 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1223
        _t1969 = parse_relation_id(parser)
        item1224 = _t1969
        push!(xs1222, item1224)
        cond1223 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1225 = xs1222
    consume_literal!(parser, ")")
    _t1970 = Proto.Context(relations=relation_ids1225)
    result1227 = _t1970
    record_span!(parser, span_start1226, "Context")
    return result1227
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1232 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1228 = Proto.SnapshotMapping[]
    cond1229 = match_lookahead_literal(parser, "[", 0)
    while cond1229
        _t1971 = parse_snapshot_mapping(parser)
        item1230 = _t1971
        push!(xs1228, item1230)
        cond1229 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1231 = xs1228
    consume_literal!(parser, ")")
    _t1972 = Proto.Snapshot(mappings=snapshot_mappings1231)
    result1233 = _t1972
    record_span!(parser, span_start1232, "Snapshot")
    return result1233
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1236 = span_start(parser)
    _t1973 = parse_edb_path(parser)
    edb_path1234 = _t1973
    _t1974 = parse_relation_id(parser)
    relation_id1235 = _t1974
    _t1975 = Proto.SnapshotMapping(destination_path=edb_path1234, source_relation=relation_id1235)
    result1237 = _t1975
    record_span!(parser, span_start1236, "SnapshotMapping")
    return result1237
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1238 = Proto.Read[]
    cond1239 = match_lookahead_literal(parser, "(", 0)
    while cond1239
        _t1976 = parse_read(parser)
        item1240 = _t1976
        push!(xs1238, item1240)
        cond1239 = match_lookahead_literal(parser, "(", 0)
    end
    reads1241 = xs1238
    consume_literal!(parser, ")")
    return reads1241
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1248 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1978 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1979 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t1980 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t1981 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t1982 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t1983 = 3
                            else
                                _t1983 = -1
                            end
                            _t1982 = _t1983
                        end
                        _t1981 = _t1982
                    end
                    _t1980 = _t1981
                end
                _t1979 = _t1980
            end
            _t1978 = _t1979
        end
        _t1977 = _t1978
    else
        _t1977 = -1
    end
    prediction1242 = _t1977
    if prediction1242 == 4
        _t1985 = parse_export(parser)
        export1247 = _t1985
        _t1986 = Proto.Read(read_type=OneOf(:var"#export", export1247))
        _t1984 = _t1986
    else
        if prediction1242 == 3
            _t1988 = parse_abort(parser)
            abort1246 = _t1988
            _t1989 = Proto.Read(read_type=OneOf(:abort, abort1246))
            _t1987 = _t1989
        else
            if prediction1242 == 2
                _t1991 = parse_what_if(parser)
                what_if1245 = _t1991
                _t1992 = Proto.Read(read_type=OneOf(:what_if, what_if1245))
                _t1990 = _t1992
            else
                if prediction1242 == 1
                    _t1994 = parse_output(parser)
                    output1244 = _t1994
                    _t1995 = Proto.Read(read_type=OneOf(:output, output1244))
                    _t1993 = _t1995
                else
                    if prediction1242 == 0
                        _t1997 = parse_demand(parser)
                        demand1243 = _t1997
                        _t1998 = Proto.Read(read_type=OneOf(:demand, demand1243))
                        _t1996 = _t1998
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1993 = _t1996
                end
                _t1990 = _t1993
            end
            _t1987 = _t1990
        end
        _t1984 = _t1987
    end
    result1249 = _t1984
    record_span!(parser, span_start1248, "Read")
    return result1249
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1251 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1999 = parse_relation_id(parser)
    relation_id1250 = _t1999
    consume_literal!(parser, ")")
    _t2000 = Proto.Demand(relation_id=relation_id1250)
    result1252 = _t2000
    record_span!(parser, span_start1251, "Demand")
    return result1252
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1255 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2001 = parse_name(parser)
    name1253 = _t2001
    _t2002 = parse_relation_id(parser)
    relation_id1254 = _t2002
    consume_literal!(parser, ")")
    _t2003 = Proto.Output(name=name1253, relation_id=relation_id1254)
    result1256 = _t2003
    record_span!(parser, span_start1255, "Output")
    return result1256
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1259 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2004 = parse_name(parser)
    name1257 = _t2004
    _t2005 = parse_epoch(parser)
    epoch1258 = _t2005
    consume_literal!(parser, ")")
    _t2006 = Proto.WhatIf(branch=name1257, epoch=epoch1258)
    result1260 = _t2006
    record_span!(parser, span_start1259, "WhatIf")
    return result1260
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1263 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2008 = parse_name(parser)
        _t2007 = _t2008
    else
        _t2007 = nothing
    end
    name1261 = _t2007
    _t2009 = parse_relation_id(parser)
    relation_id1262 = _t2009
    consume_literal!(parser, ")")
    _t2010 = Proto.Abort(name=(!isnothing(name1261) ? name1261 : "abort"), relation_id=relation_id1262)
    result1264 = _t2010
    record_span!(parser, span_start1263, "Abort")
    return result1264
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1268 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2012 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2013 = 0
            else
                _t2013 = -1
            end
            _t2012 = _t2013
        end
        _t2011 = _t2012
    else
        _t2011 = -1
    end
    prediction1265 = _t2011
    if prediction1265 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2015 = parse_export_iceberg_config(parser)
        export_iceberg_config1267 = _t2015
        consume_literal!(parser, ")")
        _t2016 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1267))
        _t2014 = _t2016
    else
        if prediction1265 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2018 = parse_export_csv_config(parser)
            export_csv_config1266 = _t2018
            consume_literal!(parser, ")")
            _t2019 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1266))
            _t2017 = _t2019
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2014 = _t2017
    end
    result1269 = _t2014
    record_span!(parser, span_start1268, "Export")
    return result1269
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1277 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2021 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2022 = 1
            else
                _t2022 = -1
            end
            _t2021 = _t2022
        end
        _t2020 = _t2021
    else
        _t2020 = -1
    end
    prediction1270 = _t2020
    if prediction1270 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2024 = parse_export_csv_path(parser)
        export_csv_path1274 = _t2024
        _t2025 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1275 = _t2025
        _t2026 = parse_config_dict(parser)
        config_dict1276 = _t2026
        consume_literal!(parser, ")")
        _t2027 = construct_export_csv_config(parser, export_csv_path1274, export_csv_columns_list1275, config_dict1276)
        _t2023 = _t2027
    else
        if prediction1270 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2029 = parse_export_csv_path(parser)
            export_csv_path1271 = _t2029
            _t2030 = parse_export_csv_source(parser)
            export_csv_source1272 = _t2030
            _t2031 = parse_csv_config(parser)
            csv_config1273 = _t2031
            consume_literal!(parser, ")")
            _t2032 = construct_export_csv_config_with_source(parser, export_csv_path1271, export_csv_source1272, csv_config1273)
            _t2028 = _t2032
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2023 = _t2028
    end
    result1278 = _t2023
    record_span!(parser, span_start1277, "ExportCSVConfig")
    return result1278
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1279 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1279
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1286 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2034 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2035 = 0
            else
                _t2035 = -1
            end
            _t2034 = _t2035
        end
        _t2033 = _t2034
    else
        _t2033 = -1
    end
    prediction1280 = _t2033
    if prediction1280 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2037 = parse_relation_id(parser)
        relation_id1285 = _t2037
        consume_literal!(parser, ")")
        _t2038 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1285))
        _t2036 = _t2038
    else
        if prediction1280 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1281 = Proto.ExportCSVColumn[]
            cond1282 = match_lookahead_literal(parser, "(", 0)
            while cond1282
                _t2040 = parse_export_csv_column(parser)
                item1283 = _t2040
                push!(xs1281, item1283)
                cond1282 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1284 = xs1281
            consume_literal!(parser, ")")
            _t2041 = Proto.ExportCSVColumns(columns=export_csv_columns1284)
            _t2042 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2041))
            _t2039 = _t2042
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2036 = _t2039
    end
    result1287 = _t2036
    record_span!(parser, span_start1286, "ExportCSVSource")
    return result1287
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1290 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1288 = consume_terminal!(parser, "STRING")
    _t2043 = parse_relation_id(parser)
    relation_id1289 = _t2043
    consume_literal!(parser, ")")
    _t2044 = Proto.ExportCSVColumn(column_name=string1288, column_data=relation_id1289)
    result1291 = _t2044
    record_span!(parser, span_start1290, "ExportCSVColumn")
    return result1291
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1292 = Proto.ExportCSVColumn[]
    cond1293 = match_lookahead_literal(parser, "(", 0)
    while cond1293
        _t2045 = parse_export_csv_column(parser)
        item1294 = _t2045
        push!(xs1292, item1294)
        cond1293 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1295 = xs1292
    consume_literal!(parser, ")")
    return export_csv_columns1295
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1304 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2046 = parse_iceberg_locator(parser)
    iceberg_locator1296 = _t2046
    _t2047 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1297 = _t2047
    _t2048 = parse_export_iceberg_columns(parser)
    export_iceberg_columns1298 = _t2048
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1299 = Tuple{String, String}[]
    cond1300 = match_lookahead_literal(parser, "(", 0)
    while cond1300
        _t2049 = parse_iceberg_property_entry(parser)
        item1301 = _t2049
        push!(xs1299, item1301)
        cond1300 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1302 = xs1299
    consume_literal!(parser, ")")
    if match_lookahead_literal(parser, "{", 0)
        _t2051 = parse_config_dict(parser)
        _t2050 = _t2051
    else
        _t2050 = nothing
    end
    config_dict1303 = _t2050
    consume_literal!(parser, ")")
    _t2052 = construct_export_iceberg_config_full(parser, iceberg_locator1296, iceberg_catalog_config1297, export_iceberg_columns1298, iceberg_property_entrys1302, config_dict1303)
    result1305 = _t2052
    record_span!(parser, span_start1304, "ExportIcebergConfig")
    return result1305
end

function parse_export_iceberg_columns(parser::ParserState)::Proto.ExportIcebergColumns
    span_start1311 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    _t2053 = parse_relation_id(parser)
    relation_id1306 = _t2053
    consume_literal!(parser, "(")
    consume_literal!(parser, "target_columns")
    xs1307 = Proto.ExportIcebergColumn[]
    cond1308 = match_lookahead_literal(parser, "(", 0)
    while cond1308
        _t2054 = parse_export_iceberg_column(parser)
        item1309 = _t2054
        push!(xs1307, item1309)
        cond1308 = match_lookahead_literal(parser, "(", 0)
    end
    export_iceberg_columns1310 = xs1307
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t2055 = Proto.ExportIcebergColumns(source_table_def=relation_id1306, target_columns=export_iceberg_columns1310)
    result1312 = _t2055
    record_span!(parser, span_start1311, "ExportIcebergColumns")
    return result1312
end

function parse_export_iceberg_column(parser::ParserState)::Proto.ExportIcebergColumn
    span_start1316 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_column")
    string1313 = consume_terminal!(parser, "STRING")
    _t2056 = parse_type(parser)
    type1314 = _t2056
    _t2057 = parse_boolean_value(parser)
    boolean_value1315 = _t2057
    consume_literal!(parser, ")")
    _t2058 = Proto.ExportIcebergColumn(name=string1313, var"#type"=type1314, nullable=boolean_value1315)
    result1317 = _t2058
    record_span!(parser, span_start1316, "ExportIcebergColumn")
    return result1317
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
