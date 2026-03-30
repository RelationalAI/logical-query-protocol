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
        _t2048 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2049 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2050 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2051 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2052 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2053 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2054 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2055 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2056 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2057 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2057
    _t2058 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2058
    _t2059 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2059
    _t2060 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2060
    _t2061 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2061
    _t2062 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2062
    _t2063 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2063
    _t2064 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2064
    _t2065 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2065
    _t2066 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2066
    _t2067 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2067
    _t2068 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2068
    _t2069 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2069
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2070 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2070
    _t2071 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2071
    _t2072 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2072
    _t2073 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2073
    _t2074 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2074
    _t2075 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2075
    _t2076 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2076
    _t2077 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2077
    _t2078 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2078
    _t2079 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2079
    _t2080 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2080
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2081 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2081
    _t2082 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2082
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
    _t2083 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2083
    _t2084 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2084
    _t2085 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2085
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2086 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2086
    _t2087 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2087
    _t2088 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2088
    _t2089 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2089
    _t2090 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2090
    _t2091 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2091
    _t2092 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2092
    _t2093 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2093
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2094 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2094
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2095 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2095
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, columns::Vector{Proto.ExportIcebergColumn}, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2096 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2096
    _t2097 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2097
    _t2098 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2098
    table_props = Dict(table_property_pairs)
    _t2099 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2099
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start661 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1311 = parse_configure(parser)
        _t1310 = _t1311
    else
        _t1310 = nothing
    end
    configure655 = _t1310
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1313 = parse_sync(parser)
        _t1312 = _t1313
    else
        _t1312 = nothing
    end
    sync656 = _t1312
    xs657 = Proto.Epoch[]
    cond658 = match_lookahead_literal(parser, "(", 0)
    while cond658
        _t1314 = parse_epoch(parser)
        item659 = _t1314
        push!(xs657, item659)
        cond658 = match_lookahead_literal(parser, "(", 0)
    end
    epochs660 = xs657
    consume_literal!(parser, ")")
    _t1315 = default_configure(parser)
    _t1316 = Proto.Transaction(epochs=epochs660, configure=(!isnothing(configure655) ? configure655 : _t1315), sync=sync656)
    result662 = _t1316
    record_span!(parser, span_start661, "Transaction")
    return result662
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start664 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1317 = parse_config_dict(parser)
    config_dict663 = _t1317
    consume_literal!(parser, ")")
    _t1318 = construct_configure(parser, config_dict663)
    result665 = _t1318
    record_span!(parser, span_start664, "Configure")
    return result665
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs666 = Tuple{String, Proto.Value}[]
    cond667 = match_lookahead_literal(parser, ":", 0)
    while cond667
        _t1319 = parse_config_key_value(parser)
        item668 = _t1319
        push!(xs666, item668)
        cond667 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values669 = xs666
    consume_literal!(parser, "}")
    return config_key_values669
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol670 = consume_terminal!(parser, "SYMBOL")
    _t1320 = parse_raw_value(parser)
    raw_value671 = _t1320
    return (symbol670, raw_value671,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start685 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1321 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1322 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1323 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1325 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1326 = 0
                        else
                            _t1326 = -1
                        end
                        _t1325 = _t1326
                    end
                    _t1324 = _t1325
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1327 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1328 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1329 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1330 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1331 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1332 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1333 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1334 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1335 = 10
                                                    else
                                                        _t1335 = -1
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
                    _t1324 = _t1327
                end
                _t1323 = _t1324
            end
            _t1322 = _t1323
        end
        _t1321 = _t1322
    end
    prediction672 = _t1321
    if prediction672 == 12
        _t1337 = parse_boolean_value(parser)
        boolean_value684 = _t1337
        _t1338 = Proto.Value(value=OneOf(:boolean_value, boolean_value684))
        _t1336 = _t1338
    else
        if prediction672 == 11
            consume_literal!(parser, "missing")
            _t1340 = Proto.MissingValue()
            _t1341 = Proto.Value(value=OneOf(:missing_value, _t1340))
            _t1339 = _t1341
        else
            if prediction672 == 10
                decimal683 = consume_terminal!(parser, "DECIMAL")
                _t1343 = Proto.Value(value=OneOf(:decimal_value, decimal683))
                _t1342 = _t1343
            else
                if prediction672 == 9
                    int128682 = consume_terminal!(parser, "INT128")
                    _t1345 = Proto.Value(value=OneOf(:int128_value, int128682))
                    _t1344 = _t1345
                else
                    if prediction672 == 8
                        uint128681 = consume_terminal!(parser, "UINT128")
                        _t1347 = Proto.Value(value=OneOf(:uint128_value, uint128681))
                        _t1346 = _t1347
                    else
                        if prediction672 == 7
                            uint32680 = consume_terminal!(parser, "UINT32")
                            _t1349 = Proto.Value(value=OneOf(:uint32_value, uint32680))
                            _t1348 = _t1349
                        else
                            if prediction672 == 6
                                float679 = consume_terminal!(parser, "FLOAT")
                                _t1351 = Proto.Value(value=OneOf(:float_value, float679))
                                _t1350 = _t1351
                            else
                                if prediction672 == 5
                                    float32678 = consume_terminal!(parser, "FLOAT32")
                                    _t1353 = Proto.Value(value=OneOf(:float32_value, float32678))
                                    _t1352 = _t1353
                                else
                                    if prediction672 == 4
                                        int677 = consume_terminal!(parser, "INT")
                                        _t1355 = Proto.Value(value=OneOf(:int_value, int677))
                                        _t1354 = _t1355
                                    else
                                        if prediction672 == 3
                                            int32676 = consume_terminal!(parser, "INT32")
                                            _t1357 = Proto.Value(value=OneOf(:int32_value, int32676))
                                            _t1356 = _t1357
                                        else
                                            if prediction672 == 2
                                                string675 = consume_terminal!(parser, "STRING")
                                                _t1359 = Proto.Value(value=OneOf(:string_value, string675))
                                                _t1358 = _t1359
                                            else
                                                if prediction672 == 1
                                                    _t1361 = parse_raw_datetime(parser)
                                                    raw_datetime674 = _t1361
                                                    _t1362 = Proto.Value(value=OneOf(:datetime_value, raw_datetime674))
                                                    _t1360 = _t1362
                                                else
                                                    if prediction672 == 0
                                                        _t1364 = parse_raw_date(parser)
                                                        raw_date673 = _t1364
                                                        _t1365 = Proto.Value(value=OneOf(:date_value, raw_date673))
                                                        _t1363 = _t1365
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1360 = _t1363
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
                            _t1348 = _t1350
                        end
                        _t1346 = _t1348
                    end
                    _t1344 = _t1346
                end
                _t1342 = _t1344
            end
            _t1339 = _t1342
        end
        _t1336 = _t1339
    end
    result686 = _t1336
    record_span!(parser, span_start685, "Value")
    return result686
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start690 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int687 = consume_terminal!(parser, "INT")
    int_3688 = consume_terminal!(parser, "INT")
    int_4689 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1366 = Proto.DateValue(year=Int32(int687), month=Int32(int_3688), day=Int32(int_4689))
    result691 = _t1366
    record_span!(parser, span_start690, "DateValue")
    return result691
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start699 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int692 = consume_terminal!(parser, "INT")
    int_3693 = consume_terminal!(parser, "INT")
    int_4694 = consume_terminal!(parser, "INT")
    int_5695 = consume_terminal!(parser, "INT")
    int_6696 = consume_terminal!(parser, "INT")
    int_7697 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1367 = consume_terminal!(parser, "INT")
    else
        _t1367 = nothing
    end
    int_8698 = _t1367
    consume_literal!(parser, ")")
    _t1368 = Proto.DateTimeValue(year=Int32(int692), month=Int32(int_3693), day=Int32(int_4694), hour=Int32(int_5695), minute=Int32(int_6696), second=Int32(int_7697), microsecond=Int32((!isnothing(int_8698) ? int_8698 : 0)))
    result700 = _t1368
    record_span!(parser, span_start699, "DateTimeValue")
    return result700
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1369 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1370 = 1
        else
            _t1370 = -1
        end
        _t1369 = _t1370
    end
    prediction701 = _t1369
    if prediction701 == 1
        consume_literal!(parser, "false")
        _t1371 = false
    else
        if prediction701 == 0
            consume_literal!(parser, "true")
            _t1372 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1371 = _t1372
    end
    return _t1371
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start706 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs702 = Proto.FragmentId[]
    cond703 = match_lookahead_literal(parser, ":", 0)
    while cond703
        _t1373 = parse_fragment_id(parser)
        item704 = _t1373
        push!(xs702, item704)
        cond703 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids705 = xs702
    consume_literal!(parser, ")")
    _t1374 = Proto.Sync(fragments=fragment_ids705)
    result707 = _t1374
    record_span!(parser, span_start706, "Sync")
    return result707
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start709 = span_start(parser)
    consume_literal!(parser, ":")
    symbol708 = consume_terminal!(parser, "SYMBOL")
    result710 = Proto.FragmentId(Vector{UInt8}(symbol708))
    record_span!(parser, span_start709, "FragmentId")
    return result710
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start713 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1376 = parse_epoch_writes(parser)
        _t1375 = _t1376
    else
        _t1375 = nothing
    end
    epoch_writes711 = _t1375
    if match_lookahead_literal(parser, "(", 0)
        _t1378 = parse_epoch_reads(parser)
        _t1377 = _t1378
    else
        _t1377 = nothing
    end
    epoch_reads712 = _t1377
    consume_literal!(parser, ")")
    _t1379 = Proto.Epoch(writes=(!isnothing(epoch_writes711) ? epoch_writes711 : Proto.Write[]), reads=(!isnothing(epoch_reads712) ? epoch_reads712 : Proto.Read[]))
    result714 = _t1379
    record_span!(parser, span_start713, "Epoch")
    return result714
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs715 = Proto.Write[]
    cond716 = match_lookahead_literal(parser, "(", 0)
    while cond716
        _t1380 = parse_write(parser)
        item717 = _t1380
        push!(xs715, item717)
        cond716 = match_lookahead_literal(parser, "(", 0)
    end
    writes718 = xs715
    consume_literal!(parser, ")")
    return writes718
end

function parse_write(parser::ParserState)::Proto.Write
    span_start724 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1382 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1383 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1384 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1385 = 2
                    else
                        _t1385 = -1
                    end
                    _t1384 = _t1385
                end
                _t1383 = _t1384
            end
            _t1382 = _t1383
        end
        _t1381 = _t1382
    else
        _t1381 = -1
    end
    prediction719 = _t1381
    if prediction719 == 3
        _t1387 = parse_snapshot(parser)
        snapshot723 = _t1387
        _t1388 = Proto.Write(write_type=OneOf(:snapshot, snapshot723))
        _t1386 = _t1388
    else
        if prediction719 == 2
            _t1390 = parse_context(parser)
            context722 = _t1390
            _t1391 = Proto.Write(write_type=OneOf(:context, context722))
            _t1389 = _t1391
        else
            if prediction719 == 1
                _t1393 = parse_undefine(parser)
                undefine721 = _t1393
                _t1394 = Proto.Write(write_type=OneOf(:undefine, undefine721))
                _t1392 = _t1394
            else
                if prediction719 == 0
                    _t1396 = parse_define(parser)
                    define720 = _t1396
                    _t1397 = Proto.Write(write_type=OneOf(:define, define720))
                    _t1395 = _t1397
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1392 = _t1395
            end
            _t1389 = _t1392
        end
        _t1386 = _t1389
    end
    result725 = _t1386
    record_span!(parser, span_start724, "Write")
    return result725
end

function parse_define(parser::ParserState)::Proto.Define
    span_start727 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1398 = parse_fragment(parser)
    fragment726 = _t1398
    consume_literal!(parser, ")")
    _t1399 = Proto.Define(fragment=fragment726)
    result728 = _t1399
    record_span!(parser, span_start727, "Define")
    return result728
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start734 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1400 = parse_new_fragment_id(parser)
    new_fragment_id729 = _t1400
    xs730 = Proto.Declaration[]
    cond731 = match_lookahead_literal(parser, "(", 0)
    while cond731
        _t1401 = parse_declaration(parser)
        item732 = _t1401
        push!(xs730, item732)
        cond731 = match_lookahead_literal(parser, "(", 0)
    end
    declarations733 = xs730
    consume_literal!(parser, ")")
    result735 = construct_fragment(parser, new_fragment_id729, declarations733)
    record_span!(parser, span_start734, "Fragment")
    return result735
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start737 = span_start(parser)
    _t1402 = parse_fragment_id(parser)
    fragment_id736 = _t1402
    start_fragment!(parser, fragment_id736)
    result738 = fragment_id736
    record_span!(parser, span_start737, "FragmentId")
    return result738
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start744 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1404 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1405 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1406 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1407 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1408 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1409 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1410 = 1
                                else
                                    _t1410 = -1
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
    else
        _t1403 = -1
    end
    prediction739 = _t1403
    if prediction739 == 3
        _t1412 = parse_data(parser)
        data743 = _t1412
        _t1413 = Proto.Declaration(declaration_type=OneOf(:data, data743))
        _t1411 = _t1413
    else
        if prediction739 == 2
            _t1415 = parse_constraint(parser)
            constraint742 = _t1415
            _t1416 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint742))
            _t1414 = _t1416
        else
            if prediction739 == 1
                _t1418 = parse_algorithm(parser)
                algorithm741 = _t1418
                _t1419 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm741))
                _t1417 = _t1419
            else
                if prediction739 == 0
                    _t1421 = parse_def(parser)
                    def740 = _t1421
                    _t1422 = Proto.Declaration(declaration_type=OneOf(:def, def740))
                    _t1420 = _t1422
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1417 = _t1420
            end
            _t1414 = _t1417
        end
        _t1411 = _t1414
    end
    result745 = _t1411
    record_span!(parser, span_start744, "Declaration")
    return result745
end

function parse_def(parser::ParserState)::Proto.Def
    span_start749 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1423 = parse_relation_id(parser)
    relation_id746 = _t1423
    _t1424 = parse_abstraction(parser)
    abstraction747 = _t1424
    if match_lookahead_literal(parser, "(", 0)
        _t1426 = parse_attrs(parser)
        _t1425 = _t1426
    else
        _t1425 = nothing
    end
    attrs748 = _t1425
    consume_literal!(parser, ")")
    _t1427 = Proto.Def(name=relation_id746, body=abstraction747, attrs=(!isnothing(attrs748) ? attrs748 : Proto.Attribute[]))
    result750 = _t1427
    record_span!(parser, span_start749, "Def")
    return result750
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start754 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1428 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1429 = 1
        else
            _t1429 = -1
        end
        _t1428 = _t1429
    end
    prediction751 = _t1428
    if prediction751 == 1
        uint128753 = consume_terminal!(parser, "UINT128")
        _t1430 = Proto.RelationId(uint128753.low, uint128753.high)
    else
        if prediction751 == 0
            consume_literal!(parser, ":")
            symbol752 = consume_terminal!(parser, "SYMBOL")
            _t1431 = relation_id_from_string(parser, symbol752)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1430 = _t1431
    end
    result755 = _t1430
    record_span!(parser, span_start754, "RelationId")
    return result755
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start758 = span_start(parser)
    consume_literal!(parser, "(")
    _t1432 = parse_bindings(parser)
    bindings756 = _t1432
    _t1433 = parse_formula(parser)
    formula757 = _t1433
    consume_literal!(parser, ")")
    _t1434 = Proto.Abstraction(vars=vcat(bindings756[1], !isnothing(bindings756[2]) ? bindings756[2] : []), value=formula757)
    result759 = _t1434
    record_span!(parser, span_start758, "Abstraction")
    return result759
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs760 = Proto.Binding[]
    cond761 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond761
        _t1435 = parse_binding(parser)
        item762 = _t1435
        push!(xs760, item762)
        cond761 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings763 = xs760
    if match_lookahead_literal(parser, "|", 0)
        _t1437 = parse_value_bindings(parser)
        _t1436 = _t1437
    else
        _t1436 = nothing
    end
    value_bindings764 = _t1436
    consume_literal!(parser, "]")
    return (bindings763, (!isnothing(value_bindings764) ? value_bindings764 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start767 = span_start(parser)
    symbol765 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1438 = parse_type(parser)
    type766 = _t1438
    _t1439 = Proto.Var(name=symbol765)
    _t1440 = Proto.Binding(var=_t1439, var"#type"=type766)
    result768 = _t1440
    record_span!(parser, span_start767, "Binding")
    return result768
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start784 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1441 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1442 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1443 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1444 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1445 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1446 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1447 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1448 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1449 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1450 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1451 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1452 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1453 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1454 = 9
                                                        else
                                                            _t1454 = -1
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
                                    _t1448 = _t1449
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
    prediction769 = _t1441
    if prediction769 == 13
        _t1456 = parse_uint32_type(parser)
        uint32_type783 = _t1456
        _t1457 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type783))
        _t1455 = _t1457
    else
        if prediction769 == 12
            _t1459 = parse_float32_type(parser)
            float32_type782 = _t1459
            _t1460 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type782))
            _t1458 = _t1460
        else
            if prediction769 == 11
                _t1462 = parse_int32_type(parser)
                int32_type781 = _t1462
                _t1463 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type781))
                _t1461 = _t1463
            else
                if prediction769 == 10
                    _t1465 = parse_boolean_type(parser)
                    boolean_type780 = _t1465
                    _t1466 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type780))
                    _t1464 = _t1466
                else
                    if prediction769 == 9
                        _t1468 = parse_decimal_type(parser)
                        decimal_type779 = _t1468
                        _t1469 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type779))
                        _t1467 = _t1469
                    else
                        if prediction769 == 8
                            _t1471 = parse_missing_type(parser)
                            missing_type778 = _t1471
                            _t1472 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type778))
                            _t1470 = _t1472
                        else
                            if prediction769 == 7
                                _t1474 = parse_datetime_type(parser)
                                datetime_type777 = _t1474
                                _t1475 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type777))
                                _t1473 = _t1475
                            else
                                if prediction769 == 6
                                    _t1477 = parse_date_type(parser)
                                    date_type776 = _t1477
                                    _t1478 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type776))
                                    _t1476 = _t1478
                                else
                                    if prediction769 == 5
                                        _t1480 = parse_int128_type(parser)
                                        int128_type775 = _t1480
                                        _t1481 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type775))
                                        _t1479 = _t1481
                                    else
                                        if prediction769 == 4
                                            _t1483 = parse_uint128_type(parser)
                                            uint128_type774 = _t1483
                                            _t1484 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type774))
                                            _t1482 = _t1484
                                        else
                                            if prediction769 == 3
                                                _t1486 = parse_float_type(parser)
                                                float_type773 = _t1486
                                                _t1487 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type773))
                                                _t1485 = _t1487
                                            else
                                                if prediction769 == 2
                                                    _t1489 = parse_int_type(parser)
                                                    int_type772 = _t1489
                                                    _t1490 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type772))
                                                    _t1488 = _t1490
                                                else
                                                    if prediction769 == 1
                                                        _t1492 = parse_string_type(parser)
                                                        string_type771 = _t1492
                                                        _t1493 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type771))
                                                        _t1491 = _t1493
                                                    else
                                                        if prediction769 == 0
                                                            _t1495 = parse_unspecified_type(parser)
                                                            unspecified_type770 = _t1495
                                                            _t1496 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type770))
                                                            _t1494 = _t1496
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1491 = _t1494
                                                    end
                                                    _t1488 = _t1491
                                                end
                                                _t1485 = _t1488
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
    result785 = _t1455
    record_span!(parser, span_start784, "Type")
    return result785
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start786 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1497 = Proto.UnspecifiedType()
    result787 = _t1497
    record_span!(parser, span_start786, "UnspecifiedType")
    return result787
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start788 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1498 = Proto.StringType()
    result789 = _t1498
    record_span!(parser, span_start788, "StringType")
    return result789
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start790 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1499 = Proto.IntType()
    result791 = _t1499
    record_span!(parser, span_start790, "IntType")
    return result791
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start792 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1500 = Proto.FloatType()
    result793 = _t1500
    record_span!(parser, span_start792, "FloatType")
    return result793
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start794 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1501 = Proto.UInt128Type()
    result795 = _t1501
    record_span!(parser, span_start794, "UInt128Type")
    return result795
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start796 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1502 = Proto.Int128Type()
    result797 = _t1502
    record_span!(parser, span_start796, "Int128Type")
    return result797
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start798 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1503 = Proto.DateType()
    result799 = _t1503
    record_span!(parser, span_start798, "DateType")
    return result799
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start800 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1504 = Proto.DateTimeType()
    result801 = _t1504
    record_span!(parser, span_start800, "DateTimeType")
    return result801
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start802 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1505 = Proto.MissingType()
    result803 = _t1505
    record_span!(parser, span_start802, "MissingType")
    return result803
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start806 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int804 = consume_terminal!(parser, "INT")
    int_3805 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1506 = Proto.DecimalType(precision=Int32(int804), scale=Int32(int_3805))
    result807 = _t1506
    record_span!(parser, span_start806, "DecimalType")
    return result807
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start808 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1507 = Proto.BooleanType()
    result809 = _t1507
    record_span!(parser, span_start808, "BooleanType")
    return result809
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start810 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1508 = Proto.Int32Type()
    result811 = _t1508
    record_span!(parser, span_start810, "Int32Type")
    return result811
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start812 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1509 = Proto.Float32Type()
    result813 = _t1509
    record_span!(parser, span_start812, "Float32Type")
    return result813
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start814 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1510 = Proto.UInt32Type()
    result815 = _t1510
    record_span!(parser, span_start814, "UInt32Type")
    return result815
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs816 = Proto.Binding[]
    cond817 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond817
        _t1511 = parse_binding(parser)
        item818 = _t1511
        push!(xs816, item818)
        cond817 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings819 = xs816
    return bindings819
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start834 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1513 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1514 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1515 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1516 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1517 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1518 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1519 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1520 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1521 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1522 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1523 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1524 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1525 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1526 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1527 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1528 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1529 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1530 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1531 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1532 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1533 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1534 = 10
                                                                                            else
                                                                                                _t1534 = -1
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
                                    end
                                    _t1519 = _t1520
                                end
                                _t1518 = _t1519
                            end
                            _t1517 = _t1518
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
    else
        _t1512 = -1
    end
    prediction820 = _t1512
    if prediction820 == 12
        _t1536 = parse_cast(parser)
        cast833 = _t1536
        _t1537 = Proto.Formula(formula_type=OneOf(:cast, cast833))
        _t1535 = _t1537
    else
        if prediction820 == 11
            _t1539 = parse_rel_atom(parser)
            rel_atom832 = _t1539
            _t1540 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom832))
            _t1538 = _t1540
        else
            if prediction820 == 10
                _t1542 = parse_primitive(parser)
                primitive831 = _t1542
                _t1543 = Proto.Formula(formula_type=OneOf(:primitive, primitive831))
                _t1541 = _t1543
            else
                if prediction820 == 9
                    _t1545 = parse_pragma(parser)
                    pragma830 = _t1545
                    _t1546 = Proto.Formula(formula_type=OneOf(:pragma, pragma830))
                    _t1544 = _t1546
                else
                    if prediction820 == 8
                        _t1548 = parse_atom(parser)
                        atom829 = _t1548
                        _t1549 = Proto.Formula(formula_type=OneOf(:atom, atom829))
                        _t1547 = _t1549
                    else
                        if prediction820 == 7
                            _t1551 = parse_ffi(parser)
                            ffi828 = _t1551
                            _t1552 = Proto.Formula(formula_type=OneOf(:ffi, ffi828))
                            _t1550 = _t1552
                        else
                            if prediction820 == 6
                                _t1554 = parse_not(parser)
                                not827 = _t1554
                                _t1555 = Proto.Formula(formula_type=OneOf(:not, not827))
                                _t1553 = _t1555
                            else
                                if prediction820 == 5
                                    _t1557 = parse_disjunction(parser)
                                    disjunction826 = _t1557
                                    _t1558 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction826))
                                    _t1556 = _t1558
                                else
                                    if prediction820 == 4
                                        _t1560 = parse_conjunction(parser)
                                        conjunction825 = _t1560
                                        _t1561 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction825))
                                        _t1559 = _t1561
                                    else
                                        if prediction820 == 3
                                            _t1563 = parse_reduce(parser)
                                            reduce824 = _t1563
                                            _t1564 = Proto.Formula(formula_type=OneOf(:reduce, reduce824))
                                            _t1562 = _t1564
                                        else
                                            if prediction820 == 2
                                                _t1566 = parse_exists(parser)
                                                exists823 = _t1566
                                                _t1567 = Proto.Formula(formula_type=OneOf(:exists, exists823))
                                                _t1565 = _t1567
                                            else
                                                if prediction820 == 1
                                                    _t1569 = parse_false(parser)
                                                    false822 = _t1569
                                                    _t1570 = Proto.Formula(formula_type=OneOf(:disjunction, false822))
                                                    _t1568 = _t1570
                                                else
                                                    if prediction820 == 0
                                                        _t1572 = parse_true(parser)
                                                        true821 = _t1572
                                                        _t1573 = Proto.Formula(formula_type=OneOf(:conjunction, true821))
                                                        _t1571 = _t1573
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1568 = _t1571
                                                end
                                                _t1565 = _t1568
                                            end
                                            _t1562 = _t1565
                                        end
                                        _t1559 = _t1562
                                    end
                                    _t1556 = _t1559
                                end
                                _t1553 = _t1556
                            end
                            _t1550 = _t1553
                        end
                        _t1547 = _t1550
                    end
                    _t1544 = _t1547
                end
                _t1541 = _t1544
            end
            _t1538 = _t1541
        end
        _t1535 = _t1538
    end
    result835 = _t1535
    record_span!(parser, span_start834, "Formula")
    return result835
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start836 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1574 = Proto.Conjunction(args=Proto.Formula[])
    result837 = _t1574
    record_span!(parser, span_start836, "Conjunction")
    return result837
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start838 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1575 = Proto.Disjunction(args=Proto.Formula[])
    result839 = _t1575
    record_span!(parser, span_start838, "Disjunction")
    return result839
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start842 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1576 = parse_bindings(parser)
    bindings840 = _t1576
    _t1577 = parse_formula(parser)
    formula841 = _t1577
    consume_literal!(parser, ")")
    _t1578 = Proto.Abstraction(vars=vcat(bindings840[1], !isnothing(bindings840[2]) ? bindings840[2] : []), value=formula841)
    _t1579 = Proto.Exists(body=_t1578)
    result843 = _t1579
    record_span!(parser, span_start842, "Exists")
    return result843
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start847 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1580 = parse_abstraction(parser)
    abstraction844 = _t1580
    _t1581 = parse_abstraction(parser)
    abstraction_3845 = _t1581
    _t1582 = parse_terms(parser)
    terms846 = _t1582
    consume_literal!(parser, ")")
    _t1583 = Proto.Reduce(op=abstraction844, body=abstraction_3845, terms=terms846)
    result848 = _t1583
    record_span!(parser, span_start847, "Reduce")
    return result848
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs849 = Proto.Term[]
    cond850 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond850
        _t1584 = parse_term(parser)
        item851 = _t1584
        push!(xs849, item851)
        cond850 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms852 = xs849
    consume_literal!(parser, ")")
    return terms852
end

function parse_term(parser::ParserState)::Proto.Term
    span_start856 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1585 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1586 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1587 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1588 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1589 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1590 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1591 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1592 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1593 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1594 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1595 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1596 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1597 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1598 = 1
                                                        else
                                                            _t1598 = -1
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
                                    _t1592 = _t1593
                                end
                                _t1591 = _t1592
                            end
                            _t1590 = _t1591
                        end
                        _t1589 = _t1590
                    end
                    _t1588 = _t1589
                end
                _t1587 = _t1588
            end
            _t1586 = _t1587
        end
        _t1585 = _t1586
    end
    prediction853 = _t1585
    if prediction853 == 1
        _t1600 = parse_value(parser)
        value855 = _t1600
        _t1601 = Proto.Term(term_type=OneOf(:constant, value855))
        _t1599 = _t1601
    else
        if prediction853 == 0
            _t1603 = parse_var(parser)
            var854 = _t1603
            _t1604 = Proto.Term(term_type=OneOf(:var, var854))
            _t1602 = _t1604
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1599 = _t1602
    end
    result857 = _t1599
    record_span!(parser, span_start856, "Term")
    return result857
end

function parse_var(parser::ParserState)::Proto.Var
    span_start859 = span_start(parser)
    symbol858 = consume_terminal!(parser, "SYMBOL")
    _t1605 = Proto.Var(name=symbol858)
    result860 = _t1605
    record_span!(parser, span_start859, "Var")
    return result860
end

function parse_value(parser::ParserState)::Proto.Value
    span_start874 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1606 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1607 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1608 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1610 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1611 = 0
                        else
                            _t1611 = -1
                        end
                        _t1610 = _t1611
                    end
                    _t1609 = _t1610
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1612 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1613 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1614 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1615 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1616 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1617 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1618 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1619 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1620 = 10
                                                    else
                                                        _t1620 = -1
                                                    end
                                                    _t1619 = _t1620
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
                    _t1609 = _t1612
                end
                _t1608 = _t1609
            end
            _t1607 = _t1608
        end
        _t1606 = _t1607
    end
    prediction861 = _t1606
    if prediction861 == 12
        _t1622 = parse_boolean_value(parser)
        boolean_value873 = _t1622
        _t1623 = Proto.Value(value=OneOf(:boolean_value, boolean_value873))
        _t1621 = _t1623
    else
        if prediction861 == 11
            consume_literal!(parser, "missing")
            _t1625 = Proto.MissingValue()
            _t1626 = Proto.Value(value=OneOf(:missing_value, _t1625))
            _t1624 = _t1626
        else
            if prediction861 == 10
                formatted_decimal872 = consume_terminal!(parser, "DECIMAL")
                _t1628 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal872))
                _t1627 = _t1628
            else
                if prediction861 == 9
                    formatted_int128871 = consume_terminal!(parser, "INT128")
                    _t1630 = Proto.Value(value=OneOf(:int128_value, formatted_int128871))
                    _t1629 = _t1630
                else
                    if prediction861 == 8
                        formatted_uint128870 = consume_terminal!(parser, "UINT128")
                        _t1632 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128870))
                        _t1631 = _t1632
                    else
                        if prediction861 == 7
                            formatted_uint32869 = consume_terminal!(parser, "UINT32")
                            _t1634 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32869))
                            _t1633 = _t1634
                        else
                            if prediction861 == 6
                                formatted_float868 = consume_terminal!(parser, "FLOAT")
                                _t1636 = Proto.Value(value=OneOf(:float_value, formatted_float868))
                                _t1635 = _t1636
                            else
                                if prediction861 == 5
                                    formatted_float32867 = consume_terminal!(parser, "FLOAT32")
                                    _t1638 = Proto.Value(value=OneOf(:float32_value, formatted_float32867))
                                    _t1637 = _t1638
                                else
                                    if prediction861 == 4
                                        formatted_int866 = consume_terminal!(parser, "INT")
                                        _t1640 = Proto.Value(value=OneOf(:int_value, formatted_int866))
                                        _t1639 = _t1640
                                    else
                                        if prediction861 == 3
                                            formatted_int32865 = consume_terminal!(parser, "INT32")
                                            _t1642 = Proto.Value(value=OneOf(:int32_value, formatted_int32865))
                                            _t1641 = _t1642
                                        else
                                            if prediction861 == 2
                                                formatted_string864 = consume_terminal!(parser, "STRING")
                                                _t1644 = Proto.Value(value=OneOf(:string_value, formatted_string864))
                                                _t1643 = _t1644
                                            else
                                                if prediction861 == 1
                                                    _t1646 = parse_datetime(parser)
                                                    datetime863 = _t1646
                                                    _t1647 = Proto.Value(value=OneOf(:datetime_value, datetime863))
                                                    _t1645 = _t1647
                                                else
                                                    if prediction861 == 0
                                                        _t1649 = parse_date(parser)
                                                        date862 = _t1649
                                                        _t1650 = Proto.Value(value=OneOf(:date_value, date862))
                                                        _t1648 = _t1650
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1645 = _t1648
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
                            _t1633 = _t1635
                        end
                        _t1631 = _t1633
                    end
                    _t1629 = _t1631
                end
                _t1627 = _t1629
            end
            _t1624 = _t1627
        end
        _t1621 = _t1624
    end
    result875 = _t1621
    record_span!(parser, span_start874, "Value")
    return result875
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start879 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int876 = consume_terminal!(parser, "INT")
    formatted_int_3877 = consume_terminal!(parser, "INT")
    formatted_int_4878 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1651 = Proto.DateValue(year=Int32(formatted_int876), month=Int32(formatted_int_3877), day=Int32(formatted_int_4878))
    result880 = _t1651
    record_span!(parser, span_start879, "DateValue")
    return result880
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start888 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int881 = consume_terminal!(parser, "INT")
    formatted_int_3882 = consume_terminal!(parser, "INT")
    formatted_int_4883 = consume_terminal!(parser, "INT")
    formatted_int_5884 = consume_terminal!(parser, "INT")
    formatted_int_6885 = consume_terminal!(parser, "INT")
    formatted_int_7886 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1652 = consume_terminal!(parser, "INT")
    else
        _t1652 = nothing
    end
    formatted_int_8887 = _t1652
    consume_literal!(parser, ")")
    _t1653 = Proto.DateTimeValue(year=Int32(formatted_int881), month=Int32(formatted_int_3882), day=Int32(formatted_int_4883), hour=Int32(formatted_int_5884), minute=Int32(formatted_int_6885), second=Int32(formatted_int_7886), microsecond=Int32((!isnothing(formatted_int_8887) ? formatted_int_8887 : 0)))
    result889 = _t1653
    record_span!(parser, span_start888, "DateTimeValue")
    return result889
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start894 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs890 = Proto.Formula[]
    cond891 = match_lookahead_literal(parser, "(", 0)
    while cond891
        _t1654 = parse_formula(parser)
        item892 = _t1654
        push!(xs890, item892)
        cond891 = match_lookahead_literal(parser, "(", 0)
    end
    formulas893 = xs890
    consume_literal!(parser, ")")
    _t1655 = Proto.Conjunction(args=formulas893)
    result895 = _t1655
    record_span!(parser, span_start894, "Conjunction")
    return result895
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start900 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs896 = Proto.Formula[]
    cond897 = match_lookahead_literal(parser, "(", 0)
    while cond897
        _t1656 = parse_formula(parser)
        item898 = _t1656
        push!(xs896, item898)
        cond897 = match_lookahead_literal(parser, "(", 0)
    end
    formulas899 = xs896
    consume_literal!(parser, ")")
    _t1657 = Proto.Disjunction(args=formulas899)
    result901 = _t1657
    record_span!(parser, span_start900, "Disjunction")
    return result901
end

function parse_not(parser::ParserState)::Proto.Not
    span_start903 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1658 = parse_formula(parser)
    formula902 = _t1658
    consume_literal!(parser, ")")
    _t1659 = Proto.Not(arg=formula902)
    result904 = _t1659
    record_span!(parser, span_start903, "Not")
    return result904
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start908 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1660 = parse_name(parser)
    name905 = _t1660
    _t1661 = parse_ffi_args(parser)
    ffi_args906 = _t1661
    _t1662 = parse_terms(parser)
    terms907 = _t1662
    consume_literal!(parser, ")")
    _t1663 = Proto.FFI(name=name905, args=ffi_args906, terms=terms907)
    result909 = _t1663
    record_span!(parser, span_start908, "FFI")
    return result909
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol910 = consume_terminal!(parser, "SYMBOL")
    return symbol910
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs911 = Proto.Abstraction[]
    cond912 = match_lookahead_literal(parser, "(", 0)
    while cond912
        _t1664 = parse_abstraction(parser)
        item913 = _t1664
        push!(xs911, item913)
        cond912 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions914 = xs911
    consume_literal!(parser, ")")
    return abstractions914
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start920 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1665 = parse_relation_id(parser)
    relation_id915 = _t1665
    xs916 = Proto.Term[]
    cond917 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond917
        _t1666 = parse_term(parser)
        item918 = _t1666
        push!(xs916, item918)
        cond917 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms919 = xs916
    consume_literal!(parser, ")")
    _t1667 = Proto.Atom(name=relation_id915, terms=terms919)
    result921 = _t1667
    record_span!(parser, span_start920, "Atom")
    return result921
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start927 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1668 = parse_name(parser)
    name922 = _t1668
    xs923 = Proto.Term[]
    cond924 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond924
        _t1669 = parse_term(parser)
        item925 = _t1669
        push!(xs923, item925)
        cond924 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms926 = xs923
    consume_literal!(parser, ")")
    _t1670 = Proto.Pragma(name=name922, terms=terms926)
    result928 = _t1670
    record_span!(parser, span_start927, "Pragma")
    return result928
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start944 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1672 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1673 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1674 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1675 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1676 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1677 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1678 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1679 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1680 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1681 = 7
                                            else
                                                _t1681 = -1
                                            end
                                            _t1680 = _t1681
                                        end
                                        _t1679 = _t1680
                                    end
                                    _t1678 = _t1679
                                end
                                _t1677 = _t1678
                            end
                            _t1676 = _t1677
                        end
                        _t1675 = _t1676
                    end
                    _t1674 = _t1675
                end
                _t1673 = _t1674
            end
            _t1672 = _t1673
        end
        _t1671 = _t1672
    else
        _t1671 = -1
    end
    prediction929 = _t1671
    if prediction929 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1683 = parse_name(parser)
        name939 = _t1683
        xs940 = Proto.RelTerm[]
        cond941 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond941
            _t1684 = parse_rel_term(parser)
            item942 = _t1684
            push!(xs940, item942)
            cond941 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms943 = xs940
        consume_literal!(parser, ")")
        _t1685 = Proto.Primitive(name=name939, terms=rel_terms943)
        _t1682 = _t1685
    else
        if prediction929 == 8
            _t1687 = parse_divide(parser)
            divide938 = _t1687
            _t1686 = divide938
        else
            if prediction929 == 7
                _t1689 = parse_multiply(parser)
                multiply937 = _t1689
                _t1688 = multiply937
            else
                if prediction929 == 6
                    _t1691 = parse_minus(parser)
                    minus936 = _t1691
                    _t1690 = minus936
                else
                    if prediction929 == 5
                        _t1693 = parse_add(parser)
                        add935 = _t1693
                        _t1692 = add935
                    else
                        if prediction929 == 4
                            _t1695 = parse_gt_eq(parser)
                            gt_eq934 = _t1695
                            _t1694 = gt_eq934
                        else
                            if prediction929 == 3
                                _t1697 = parse_gt(parser)
                                gt933 = _t1697
                                _t1696 = gt933
                            else
                                if prediction929 == 2
                                    _t1699 = parse_lt_eq(parser)
                                    lt_eq932 = _t1699
                                    _t1698 = lt_eq932
                                else
                                    if prediction929 == 1
                                        _t1701 = parse_lt(parser)
                                        lt931 = _t1701
                                        _t1700 = lt931
                                    else
                                        if prediction929 == 0
                                            _t1703 = parse_eq(parser)
                                            eq930 = _t1703
                                            _t1702 = eq930
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1700 = _t1702
                                    end
                                    _t1698 = _t1700
                                end
                                _t1696 = _t1698
                            end
                            _t1694 = _t1696
                        end
                        _t1692 = _t1694
                    end
                    _t1690 = _t1692
                end
                _t1688 = _t1690
            end
            _t1686 = _t1688
        end
        _t1682 = _t1686
    end
    result945 = _t1682
    record_span!(parser, span_start944, "Primitive")
    return result945
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start948 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1704 = parse_term(parser)
    term946 = _t1704
    _t1705 = parse_term(parser)
    term_3947 = _t1705
    consume_literal!(parser, ")")
    _t1706 = Proto.RelTerm(rel_term_type=OneOf(:term, term946))
    _t1707 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3947))
    _t1708 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1706, _t1707])
    result949 = _t1708
    record_span!(parser, span_start948, "Primitive")
    return result949
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1709 = parse_term(parser)
    term950 = _t1709
    _t1710 = parse_term(parser)
    term_3951 = _t1710
    consume_literal!(parser, ")")
    _t1711 = Proto.RelTerm(rel_term_type=OneOf(:term, term950))
    _t1712 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3951))
    _t1713 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1711, _t1712])
    result953 = _t1713
    record_span!(parser, span_start952, "Primitive")
    return result953
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start956 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1714 = parse_term(parser)
    term954 = _t1714
    _t1715 = parse_term(parser)
    term_3955 = _t1715
    consume_literal!(parser, ")")
    _t1716 = Proto.RelTerm(rel_term_type=OneOf(:term, term954))
    _t1717 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3955))
    _t1718 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1716, _t1717])
    result957 = _t1718
    record_span!(parser, span_start956, "Primitive")
    return result957
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1719 = parse_term(parser)
    term958 = _t1719
    _t1720 = parse_term(parser)
    term_3959 = _t1720
    consume_literal!(parser, ")")
    _t1721 = Proto.RelTerm(rel_term_type=OneOf(:term, term958))
    _t1722 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3959))
    _t1723 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1721, _t1722])
    result961 = _t1723
    record_span!(parser, span_start960, "Primitive")
    return result961
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start964 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1724 = parse_term(parser)
    term962 = _t1724
    _t1725 = parse_term(parser)
    term_3963 = _t1725
    consume_literal!(parser, ")")
    _t1726 = Proto.RelTerm(rel_term_type=OneOf(:term, term962))
    _t1727 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3963))
    _t1728 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1726, _t1727])
    result965 = _t1728
    record_span!(parser, span_start964, "Primitive")
    return result965
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1729 = parse_term(parser)
    term966 = _t1729
    _t1730 = parse_term(parser)
    term_3967 = _t1730
    _t1731 = parse_term(parser)
    term_4968 = _t1731
    consume_literal!(parser, ")")
    _t1732 = Proto.RelTerm(rel_term_type=OneOf(:term, term966))
    _t1733 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3967))
    _t1734 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4968))
    _t1735 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1732, _t1733, _t1734])
    result970 = _t1735
    record_span!(parser, span_start969, "Primitive")
    return result970
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1736 = parse_term(parser)
    term971 = _t1736
    _t1737 = parse_term(parser)
    term_3972 = _t1737
    _t1738 = parse_term(parser)
    term_4973 = _t1738
    consume_literal!(parser, ")")
    _t1739 = Proto.RelTerm(rel_term_type=OneOf(:term, term971))
    _t1740 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3972))
    _t1741 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4973))
    _t1742 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1739, _t1740, _t1741])
    result975 = _t1742
    record_span!(parser, span_start974, "Primitive")
    return result975
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start979 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1743 = parse_term(parser)
    term976 = _t1743
    _t1744 = parse_term(parser)
    term_3977 = _t1744
    _t1745 = parse_term(parser)
    term_4978 = _t1745
    consume_literal!(parser, ")")
    _t1746 = Proto.RelTerm(rel_term_type=OneOf(:term, term976))
    _t1747 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3977))
    _t1748 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4978))
    _t1749 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1746, _t1747, _t1748])
    result980 = _t1749
    record_span!(parser, span_start979, "Primitive")
    return result980
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start984 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1750 = parse_term(parser)
    term981 = _t1750
    _t1751 = parse_term(parser)
    term_3982 = _t1751
    _t1752 = parse_term(parser)
    term_4983 = _t1752
    consume_literal!(parser, ")")
    _t1753 = Proto.RelTerm(rel_term_type=OneOf(:term, term981))
    _t1754 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3982))
    _t1755 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4983))
    _t1756 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1753, _t1754, _t1755])
    result985 = _t1756
    record_span!(parser, span_start984, "Primitive")
    return result985
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start989 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1757 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1758 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1759 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1760 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1761 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1762 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1763 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1764 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1765 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1766 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1767 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1768 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1769 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1770 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1771 = 1
                                                            else
                                                                _t1771 = -1
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
                                    _t1764 = _t1765
                                end
                                _t1763 = _t1764
                            end
                            _t1762 = _t1763
                        end
                        _t1761 = _t1762
                    end
                    _t1760 = _t1761
                end
                _t1759 = _t1760
            end
            _t1758 = _t1759
        end
        _t1757 = _t1758
    end
    prediction986 = _t1757
    if prediction986 == 1
        _t1773 = parse_term(parser)
        term988 = _t1773
        _t1774 = Proto.RelTerm(rel_term_type=OneOf(:term, term988))
        _t1772 = _t1774
    else
        if prediction986 == 0
            _t1776 = parse_specialized_value(parser)
            specialized_value987 = _t1776
            _t1777 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value987))
            _t1775 = _t1777
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1772 = _t1775
    end
    result990 = _t1772
    record_span!(parser, span_start989, "RelTerm")
    return result990
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start992 = span_start(parser)
    consume_literal!(parser, "#")
    _t1778 = parse_raw_value(parser)
    raw_value991 = _t1778
    result993 = raw_value991
    record_span!(parser, span_start992, "Value")
    return result993
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start999 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1779 = parse_name(parser)
    name994 = _t1779
    xs995 = Proto.RelTerm[]
    cond996 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond996
        _t1780 = parse_rel_term(parser)
        item997 = _t1780
        push!(xs995, item997)
        cond996 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms998 = xs995
    consume_literal!(parser, ")")
    _t1781 = Proto.RelAtom(name=name994, terms=rel_terms998)
    result1000 = _t1781
    record_span!(parser, span_start999, "RelAtom")
    return result1000
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1003 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1782 = parse_term(parser)
    term1001 = _t1782
    _t1783 = parse_term(parser)
    term_31002 = _t1783
    consume_literal!(parser, ")")
    _t1784 = Proto.Cast(input=term1001, result=term_31002)
    result1004 = _t1784
    record_span!(parser, span_start1003, "Cast")
    return result1004
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1005 = Proto.Attribute[]
    cond1006 = match_lookahead_literal(parser, "(", 0)
    while cond1006
        _t1785 = parse_attribute(parser)
        item1007 = _t1785
        push!(xs1005, item1007)
        cond1006 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1008 = xs1005
    consume_literal!(parser, ")")
    return attributes1008
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1014 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1786 = parse_name(parser)
    name1009 = _t1786
    xs1010 = Proto.Value[]
    cond1011 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1011
        _t1787 = parse_raw_value(parser)
        item1012 = _t1787
        push!(xs1010, item1012)
        cond1011 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1013 = xs1010
    consume_literal!(parser, ")")
    _t1788 = Proto.Attribute(name=name1009, args=raw_values1013)
    result1015 = _t1788
    record_span!(parser, span_start1014, "Attribute")
    return result1015
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1021 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1016 = Proto.RelationId[]
    cond1017 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1017
        _t1789 = parse_relation_id(parser)
        item1018 = _t1789
        push!(xs1016, item1018)
        cond1017 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1019 = xs1016
    _t1790 = parse_script(parser)
    script1020 = _t1790
    consume_literal!(parser, ")")
    _t1791 = Proto.Algorithm(var"#global"=relation_ids1019, body=script1020)
    result1022 = _t1791
    record_span!(parser, span_start1021, "Algorithm")
    return result1022
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1027 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1023 = Proto.Construct[]
    cond1024 = match_lookahead_literal(parser, "(", 0)
    while cond1024
        _t1792 = parse_construct(parser)
        item1025 = _t1792
        push!(xs1023, item1025)
        cond1024 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1026 = xs1023
    consume_literal!(parser, ")")
    _t1793 = Proto.Script(constructs=constructs1026)
    result1028 = _t1793
    record_span!(parser, span_start1027, "Script")
    return result1028
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1032 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1795 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1796 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1797 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1798 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1799 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1800 = 1
                            else
                                _t1800 = -1
                            end
                            _t1799 = _t1800
                        end
                        _t1798 = _t1799
                    end
                    _t1797 = _t1798
                end
                _t1796 = _t1797
            end
            _t1795 = _t1796
        end
        _t1794 = _t1795
    else
        _t1794 = -1
    end
    prediction1029 = _t1794
    if prediction1029 == 1
        _t1802 = parse_instruction(parser)
        instruction1031 = _t1802
        _t1803 = Proto.Construct(construct_type=OneOf(:instruction, instruction1031))
        _t1801 = _t1803
    else
        if prediction1029 == 0
            _t1805 = parse_loop(parser)
            loop1030 = _t1805
            _t1806 = Proto.Construct(construct_type=OneOf(:loop, loop1030))
            _t1804 = _t1806
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1801 = _t1804
    end
    result1033 = _t1801
    record_span!(parser, span_start1032, "Construct")
    return result1033
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1036 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1807 = parse_init(parser)
    init1034 = _t1807
    _t1808 = parse_script(parser)
    script1035 = _t1808
    consume_literal!(parser, ")")
    _t1809 = Proto.Loop(init=init1034, body=script1035)
    result1037 = _t1809
    record_span!(parser, span_start1036, "Loop")
    return result1037
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1038 = Proto.Instruction[]
    cond1039 = match_lookahead_literal(parser, "(", 0)
    while cond1039
        _t1810 = parse_instruction(parser)
        item1040 = _t1810
        push!(xs1038, item1040)
        cond1039 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1041 = xs1038
    consume_literal!(parser, ")")
    return instructions1041
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1048 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1812 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1813 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1814 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1815 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1816 = 0
                        else
                            _t1816 = -1
                        end
                        _t1815 = _t1816
                    end
                    _t1814 = _t1815
                end
                _t1813 = _t1814
            end
            _t1812 = _t1813
        end
        _t1811 = _t1812
    else
        _t1811 = -1
    end
    prediction1042 = _t1811
    if prediction1042 == 4
        _t1818 = parse_monus_def(parser)
        monus_def1047 = _t1818
        _t1819 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1047))
        _t1817 = _t1819
    else
        if prediction1042 == 3
            _t1821 = parse_monoid_def(parser)
            monoid_def1046 = _t1821
            _t1822 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1046))
            _t1820 = _t1822
        else
            if prediction1042 == 2
                _t1824 = parse_break(parser)
                break1045 = _t1824
                _t1825 = Proto.Instruction(instr_type=OneOf(:var"#break", break1045))
                _t1823 = _t1825
            else
                if prediction1042 == 1
                    _t1827 = parse_upsert(parser)
                    upsert1044 = _t1827
                    _t1828 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1044))
                    _t1826 = _t1828
                else
                    if prediction1042 == 0
                        _t1830 = parse_assign(parser)
                        assign1043 = _t1830
                        _t1831 = Proto.Instruction(instr_type=OneOf(:assign, assign1043))
                        _t1829 = _t1831
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1826 = _t1829
                end
                _t1823 = _t1826
            end
            _t1820 = _t1823
        end
        _t1817 = _t1820
    end
    result1049 = _t1817
    record_span!(parser, span_start1048, "Instruction")
    return result1049
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1053 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1832 = parse_relation_id(parser)
    relation_id1050 = _t1832
    _t1833 = parse_abstraction(parser)
    abstraction1051 = _t1833
    if match_lookahead_literal(parser, "(", 0)
        _t1835 = parse_attrs(parser)
        _t1834 = _t1835
    else
        _t1834 = nothing
    end
    attrs1052 = _t1834
    consume_literal!(parser, ")")
    _t1836 = Proto.Assign(name=relation_id1050, body=abstraction1051, attrs=(!isnothing(attrs1052) ? attrs1052 : Proto.Attribute[]))
    result1054 = _t1836
    record_span!(parser, span_start1053, "Assign")
    return result1054
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1058 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1837 = parse_relation_id(parser)
    relation_id1055 = _t1837
    _t1838 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1056 = _t1838
    if match_lookahead_literal(parser, "(", 0)
        _t1840 = parse_attrs(parser)
        _t1839 = _t1840
    else
        _t1839 = nothing
    end
    attrs1057 = _t1839
    consume_literal!(parser, ")")
    _t1841 = Proto.Upsert(name=relation_id1055, body=abstraction_with_arity1056[1], attrs=(!isnothing(attrs1057) ? attrs1057 : Proto.Attribute[]), value_arity=abstraction_with_arity1056[2])
    result1059 = _t1841
    record_span!(parser, span_start1058, "Upsert")
    return result1059
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1842 = parse_bindings(parser)
    bindings1060 = _t1842
    _t1843 = parse_formula(parser)
    formula1061 = _t1843
    consume_literal!(parser, ")")
    _t1844 = Proto.Abstraction(vars=vcat(bindings1060[1], !isnothing(bindings1060[2]) ? bindings1060[2] : []), value=formula1061)
    return (_t1844, length(bindings1060[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1065 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1845 = parse_relation_id(parser)
    relation_id1062 = _t1845
    _t1846 = parse_abstraction(parser)
    abstraction1063 = _t1846
    if match_lookahead_literal(parser, "(", 0)
        _t1848 = parse_attrs(parser)
        _t1847 = _t1848
    else
        _t1847 = nothing
    end
    attrs1064 = _t1847
    consume_literal!(parser, ")")
    _t1849 = Proto.Break(name=relation_id1062, body=abstraction1063, attrs=(!isnothing(attrs1064) ? attrs1064 : Proto.Attribute[]))
    result1066 = _t1849
    record_span!(parser, span_start1065, "Break")
    return result1066
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1071 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1850 = parse_monoid(parser)
    monoid1067 = _t1850
    _t1851 = parse_relation_id(parser)
    relation_id1068 = _t1851
    _t1852 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1069 = _t1852
    if match_lookahead_literal(parser, "(", 0)
        _t1854 = parse_attrs(parser)
        _t1853 = _t1854
    else
        _t1853 = nothing
    end
    attrs1070 = _t1853
    consume_literal!(parser, ")")
    _t1855 = Proto.MonoidDef(monoid=monoid1067, name=relation_id1068, body=abstraction_with_arity1069[1], attrs=(!isnothing(attrs1070) ? attrs1070 : Proto.Attribute[]), value_arity=abstraction_with_arity1069[2])
    result1072 = _t1855
    record_span!(parser, span_start1071, "MonoidDef")
    return result1072
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1078 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1857 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1858 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1859 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1860 = 2
                    else
                        _t1860 = -1
                    end
                    _t1859 = _t1860
                end
                _t1858 = _t1859
            end
            _t1857 = _t1858
        end
        _t1856 = _t1857
    else
        _t1856 = -1
    end
    prediction1073 = _t1856
    if prediction1073 == 3
        _t1862 = parse_sum_monoid(parser)
        sum_monoid1077 = _t1862
        _t1863 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1077))
        _t1861 = _t1863
    else
        if prediction1073 == 2
            _t1865 = parse_max_monoid(parser)
            max_monoid1076 = _t1865
            _t1866 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1076))
            _t1864 = _t1866
        else
            if prediction1073 == 1
                _t1868 = parse_min_monoid(parser)
                min_monoid1075 = _t1868
                _t1869 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1075))
                _t1867 = _t1869
            else
                if prediction1073 == 0
                    _t1871 = parse_or_monoid(parser)
                    or_monoid1074 = _t1871
                    _t1872 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1074))
                    _t1870 = _t1872
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1867 = _t1870
            end
            _t1864 = _t1867
        end
        _t1861 = _t1864
    end
    result1079 = _t1861
    record_span!(parser, span_start1078, "Monoid")
    return result1079
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1080 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1873 = Proto.OrMonoid()
    result1081 = _t1873
    record_span!(parser, span_start1080, "OrMonoid")
    return result1081
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1083 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1874 = parse_type(parser)
    type1082 = _t1874
    consume_literal!(parser, ")")
    _t1875 = Proto.MinMonoid(var"#type"=type1082)
    result1084 = _t1875
    record_span!(parser, span_start1083, "MinMonoid")
    return result1084
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1086 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1876 = parse_type(parser)
    type1085 = _t1876
    consume_literal!(parser, ")")
    _t1877 = Proto.MaxMonoid(var"#type"=type1085)
    result1087 = _t1877
    record_span!(parser, span_start1086, "MaxMonoid")
    return result1087
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1089 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1878 = parse_type(parser)
    type1088 = _t1878
    consume_literal!(parser, ")")
    _t1879 = Proto.SumMonoid(var"#type"=type1088)
    result1090 = _t1879
    record_span!(parser, span_start1089, "SumMonoid")
    return result1090
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1095 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1880 = parse_monoid(parser)
    monoid1091 = _t1880
    _t1881 = parse_relation_id(parser)
    relation_id1092 = _t1881
    _t1882 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1093 = _t1882
    if match_lookahead_literal(parser, "(", 0)
        _t1884 = parse_attrs(parser)
        _t1883 = _t1884
    else
        _t1883 = nothing
    end
    attrs1094 = _t1883
    consume_literal!(parser, ")")
    _t1885 = Proto.MonusDef(monoid=monoid1091, name=relation_id1092, body=abstraction_with_arity1093[1], attrs=(!isnothing(attrs1094) ? attrs1094 : Proto.Attribute[]), value_arity=abstraction_with_arity1093[2])
    result1096 = _t1885
    record_span!(parser, span_start1095, "MonusDef")
    return result1096
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1101 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1886 = parse_relation_id(parser)
    relation_id1097 = _t1886
    _t1887 = parse_abstraction(parser)
    abstraction1098 = _t1887
    _t1888 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1099 = _t1888
    _t1889 = parse_functional_dependency_values(parser)
    functional_dependency_values1100 = _t1889
    consume_literal!(parser, ")")
    _t1890 = Proto.FunctionalDependency(guard=abstraction1098, keys=functional_dependency_keys1099, values=functional_dependency_values1100)
    _t1891 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1890), name=relation_id1097)
    result1102 = _t1891
    record_span!(parser, span_start1101, "Constraint")
    return result1102
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1103 = Proto.Var[]
    cond1104 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1104
        _t1892 = parse_var(parser)
        item1105 = _t1892
        push!(xs1103, item1105)
        cond1104 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1106 = xs1103
    consume_literal!(parser, ")")
    return vars1106
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1107 = Proto.Var[]
    cond1108 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1108
        _t1893 = parse_var(parser)
        item1109 = _t1893
        push!(xs1107, item1109)
        cond1108 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1110 = xs1107
    consume_literal!(parser, ")")
    return vars1110
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1116 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1895 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1896 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1897 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1898 = 1
                    else
                        _t1898 = -1
                    end
                    _t1897 = _t1898
                end
                _t1896 = _t1897
            end
            _t1895 = _t1896
        end
        _t1894 = _t1895
    else
        _t1894 = -1
    end
    prediction1111 = _t1894
    if prediction1111 == 3
        _t1900 = parse_iceberg_data(parser)
        iceberg_data1115 = _t1900
        _t1901 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1115))
        _t1899 = _t1901
    else
        if prediction1111 == 2
            _t1903 = parse_csv_data(parser)
            csv_data1114 = _t1903
            _t1904 = Proto.Data(data_type=OneOf(:csv_data, csv_data1114))
            _t1902 = _t1904
        else
            if prediction1111 == 1
                _t1906 = parse_betree_relation(parser)
                betree_relation1113 = _t1906
                _t1907 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1113))
                _t1905 = _t1907
            else
                if prediction1111 == 0
                    _t1909 = parse_edb(parser)
                    edb1112 = _t1909
                    _t1910 = Proto.Data(data_type=OneOf(:edb, edb1112))
                    _t1908 = _t1910
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1905 = _t1908
            end
            _t1902 = _t1905
        end
        _t1899 = _t1902
    end
    result1117 = _t1899
    record_span!(parser, span_start1116, "Data")
    return result1117
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1121 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1911 = parse_relation_id(parser)
    relation_id1118 = _t1911
    _t1912 = parse_edb_path(parser)
    edb_path1119 = _t1912
    _t1913 = parse_edb_types(parser)
    edb_types1120 = _t1913
    consume_literal!(parser, ")")
    _t1914 = Proto.EDB(target_id=relation_id1118, path=edb_path1119, types=edb_types1120)
    result1122 = _t1914
    record_span!(parser, span_start1121, "EDB")
    return result1122
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1123 = String[]
    cond1124 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1124
        item1125 = consume_terminal!(parser, "STRING")
        push!(xs1123, item1125)
        cond1124 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1126 = xs1123
    consume_literal!(parser, "]")
    return strings1126
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1127 = Proto.var"#Type"[]
    cond1128 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1128
        _t1915 = parse_type(parser)
        item1129 = _t1915
        push!(xs1127, item1129)
        cond1128 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1130 = xs1127
    consume_literal!(parser, "]")
    return types1130
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1133 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1916 = parse_relation_id(parser)
    relation_id1131 = _t1916
    _t1917 = parse_betree_info(parser)
    betree_info1132 = _t1917
    consume_literal!(parser, ")")
    _t1918 = Proto.BeTreeRelation(name=relation_id1131, relation_info=betree_info1132)
    result1134 = _t1918
    record_span!(parser, span_start1133, "BeTreeRelation")
    return result1134
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1138 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1919 = parse_betree_info_key_types(parser)
    betree_info_key_types1135 = _t1919
    _t1920 = parse_betree_info_value_types(parser)
    betree_info_value_types1136 = _t1920
    _t1921 = parse_config_dict(parser)
    config_dict1137 = _t1921
    consume_literal!(parser, ")")
    _t1922 = construct_betree_info(parser, betree_info_key_types1135, betree_info_value_types1136, config_dict1137)
    result1139 = _t1922
    record_span!(parser, span_start1138, "BeTreeInfo")
    return result1139
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1140 = Proto.var"#Type"[]
    cond1141 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1141
        _t1923 = parse_type(parser)
        item1142 = _t1923
        push!(xs1140, item1142)
        cond1141 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1143 = xs1140
    consume_literal!(parser, ")")
    return types1143
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1144 = Proto.var"#Type"[]
    cond1145 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1145
        _t1924 = parse_type(parser)
        item1146 = _t1924
        push!(xs1144, item1146)
        cond1145 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1147 = xs1144
    consume_literal!(parser, ")")
    return types1147
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1152 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1925 = parse_csvlocator(parser)
    csvlocator1148 = _t1925
    _t1926 = parse_csv_config(parser)
    csv_config1149 = _t1926
    _t1927 = parse_gnf_columns(parser)
    gnf_columns1150 = _t1927
    _t1928 = parse_csv_asof(parser)
    csv_asof1151 = _t1928
    consume_literal!(parser, ")")
    _t1929 = Proto.CSVData(locator=csvlocator1148, config=csv_config1149, columns=gnf_columns1150, asof=csv_asof1151)
    result1153 = _t1929
    record_span!(parser, span_start1152, "CSVData")
    return result1153
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1156 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1931 = parse_csv_locator_paths(parser)
        _t1930 = _t1931
    else
        _t1930 = nothing
    end
    csv_locator_paths1154 = _t1930
    if match_lookahead_literal(parser, "(", 0)
        _t1933 = parse_csv_locator_inline_data(parser)
        _t1932 = _t1933
    else
        _t1932 = nothing
    end
    csv_locator_inline_data1155 = _t1932
    consume_literal!(parser, ")")
    _t1934 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1154) ? csv_locator_paths1154 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1155) ? csv_locator_inline_data1155 : "")))
    result1157 = _t1934
    record_span!(parser, span_start1156, "CSVLocator")
    return result1157
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1158 = String[]
    cond1159 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1159
        item1160 = consume_terminal!(parser, "STRING")
        push!(xs1158, item1160)
        cond1159 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1161 = xs1158
    consume_literal!(parser, ")")
    return strings1161
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1162 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1162
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1164 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1935 = parse_config_dict(parser)
    config_dict1163 = _t1935
    consume_literal!(parser, ")")
    _t1936 = construct_csv_config(parser, config_dict1163)
    result1165 = _t1936
    record_span!(parser, span_start1164, "CSVConfig")
    return result1165
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1166 = Proto.GNFColumn[]
    cond1167 = match_lookahead_literal(parser, "(", 0)
    while cond1167
        _t1937 = parse_gnf_column(parser)
        item1168 = _t1937
        push!(xs1166, item1168)
        cond1167 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1169 = xs1166
    consume_literal!(parser, ")")
    return gnf_columns1169
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1176 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1938 = parse_gnf_column_path(parser)
    gnf_column_path1170 = _t1938
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1940 = parse_relation_id(parser)
        _t1939 = _t1940
    else
        _t1939 = nothing
    end
    relation_id1171 = _t1939
    consume_literal!(parser, "[")
    xs1172 = Proto.var"#Type"[]
    cond1173 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1173
        _t1941 = parse_type(parser)
        item1174 = _t1941
        push!(xs1172, item1174)
        cond1173 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1175 = xs1172
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1942 = Proto.GNFColumn(column_path=gnf_column_path1170, target_id=relation_id1171, types=types1175)
    result1177 = _t1942
    record_span!(parser, span_start1176, "GNFColumn")
    return result1177
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1943 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1944 = 0
        else
            _t1944 = -1
        end
        _t1943 = _t1944
    end
    prediction1178 = _t1943
    if prediction1178 == 1
        consume_literal!(parser, "[")
        xs1180 = String[]
        cond1181 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1181
            item1182 = consume_terminal!(parser, "STRING")
            push!(xs1180, item1182)
            cond1181 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1183 = xs1180
        consume_literal!(parser, "]")
        _t1945 = strings1183
    else
        if prediction1178 == 0
            string1179 = consume_terminal!(parser, "STRING")
            _t1946 = String[string1179]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1945 = _t1946
    end
    return _t1945
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1184 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1184
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1189 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1947 = parse_iceberg_locator(parser)
    iceberg_locator1185 = _t1947
    _t1948 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1186 = _t1948
    _t1949 = parse_gnf_columns(parser)
    gnf_columns1187 = _t1949
    if match_lookahead_literal(parser, "(", 0)
        _t1951 = parse_iceberg_to_snapshot(parser)
        _t1950 = _t1951
    else
        _t1950 = nothing
    end
    iceberg_to_snapshot1188 = _t1950
    consume_literal!(parser, ")")
    _t1952 = Proto.IcebergData(locator=iceberg_locator1185, config=iceberg_catalog_config1186, columns=gnf_columns1187, to_snapshot=(!isnothing(iceberg_to_snapshot1188) ? iceberg_to_snapshot1188 : ""))
    result1190 = _t1952
    record_span!(parser, span_start1189, "IcebergData")
    return result1190
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1197 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1191 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1192 = String[]
    cond1193 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1193
        item1194 = consume_terminal!(parser, "STRING")
        push!(xs1192, item1194)
        cond1193 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1195 = xs1192
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string_121196 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1953 = Proto.IcebergLocator(table_name=string1191, namespace=strings1195, warehouse=string_121196)
    result1198 = _t1953
    record_span!(parser, span_start1197, "IcebergLocator")
    return result1198
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1209 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1199 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1955 = parse_iceberg_catalog_config_scope(parser)
        _t1954 = _t1955
    else
        _t1954 = nothing
    end
    iceberg_catalog_config_scope1200 = _t1954
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1201 = Tuple{String, String}[]
    cond1202 = match_lookahead_literal(parser, "(", 0)
    while cond1202
        _t1956 = parse_iceberg_property_entry(parser)
        item1203 = _t1956
        push!(xs1201, item1203)
        cond1202 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1204 = xs1201
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1205 = Tuple{String, String}[]
    cond1206 = match_lookahead_literal(parser, "(", 0)
    while cond1206
        _t1957 = parse_iceberg_property_entry(parser)
        item1207 = _t1957
        push!(xs1205, item1207)
        cond1206 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys_131208 = xs1205
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1958 = construct_iceberg_catalog_config(parser, string1199, iceberg_catalog_config_scope1200, iceberg_property_entrys1204, iceberg_property_entrys_131208)
    result1210 = _t1958
    record_span!(parser, span_start1209, "IcebergCatalogConfig")
    return result1210
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1211 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1211
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1212 = consume_terminal!(parser, "STRING")
    string_31213 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1212, string_31213,)
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1214 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1214
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1216 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1959 = parse_fragment_id(parser)
    fragment_id1215 = _t1959
    consume_literal!(parser, ")")
    _t1960 = Proto.Undefine(fragment_id=fragment_id1215)
    result1217 = _t1960
    record_span!(parser, span_start1216, "Undefine")
    return result1217
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1222 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1218 = Proto.RelationId[]
    cond1219 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1219
        _t1961 = parse_relation_id(parser)
        item1220 = _t1961
        push!(xs1218, item1220)
        cond1219 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1221 = xs1218
    consume_literal!(parser, ")")
    _t1962 = Proto.Context(relations=relation_ids1221)
    result1223 = _t1962
    record_span!(parser, span_start1222, "Context")
    return result1223
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1228 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1224 = Proto.SnapshotMapping[]
    cond1225 = match_lookahead_literal(parser, "[", 0)
    while cond1225
        _t1963 = parse_snapshot_mapping(parser)
        item1226 = _t1963
        push!(xs1224, item1226)
        cond1225 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1227 = xs1224
    consume_literal!(parser, ")")
    _t1964 = Proto.Snapshot(mappings=snapshot_mappings1227)
    result1229 = _t1964
    record_span!(parser, span_start1228, "Snapshot")
    return result1229
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1232 = span_start(parser)
    _t1965 = parse_edb_path(parser)
    edb_path1230 = _t1965
    _t1966 = parse_relation_id(parser)
    relation_id1231 = _t1966
    _t1967 = Proto.SnapshotMapping(destination_path=edb_path1230, source_relation=relation_id1231)
    result1233 = _t1967
    record_span!(parser, span_start1232, "SnapshotMapping")
    return result1233
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1234 = Proto.Read[]
    cond1235 = match_lookahead_literal(parser, "(", 0)
    while cond1235
        _t1968 = parse_read(parser)
        item1236 = _t1968
        push!(xs1234, item1236)
        cond1235 = match_lookahead_literal(parser, "(", 0)
    end
    reads1237 = xs1234
    consume_literal!(parser, ")")
    return reads1237
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1244 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1970 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1971 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t1972 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t1973 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t1974 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t1975 = 3
                            else
                                _t1975 = -1
                            end
                            _t1974 = _t1975
                        end
                        _t1973 = _t1974
                    end
                    _t1972 = _t1973
                end
                _t1971 = _t1972
            end
            _t1970 = _t1971
        end
        _t1969 = _t1970
    else
        _t1969 = -1
    end
    prediction1238 = _t1969
    if prediction1238 == 4
        _t1977 = parse_export(parser)
        export1243 = _t1977
        _t1978 = Proto.Read(read_type=OneOf(:var"#export", export1243))
        _t1976 = _t1978
    else
        if prediction1238 == 3
            _t1980 = parse_abort(parser)
            abort1242 = _t1980
            _t1981 = Proto.Read(read_type=OneOf(:abort, abort1242))
            _t1979 = _t1981
        else
            if prediction1238 == 2
                _t1983 = parse_what_if(parser)
                what_if1241 = _t1983
                _t1984 = Proto.Read(read_type=OneOf(:what_if, what_if1241))
                _t1982 = _t1984
            else
                if prediction1238 == 1
                    _t1986 = parse_output(parser)
                    output1240 = _t1986
                    _t1987 = Proto.Read(read_type=OneOf(:output, output1240))
                    _t1985 = _t1987
                else
                    if prediction1238 == 0
                        _t1989 = parse_demand(parser)
                        demand1239 = _t1989
                        _t1990 = Proto.Read(read_type=OneOf(:demand, demand1239))
                        _t1988 = _t1990
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1985 = _t1988
                end
                _t1982 = _t1985
            end
            _t1979 = _t1982
        end
        _t1976 = _t1979
    end
    result1245 = _t1976
    record_span!(parser, span_start1244, "Read")
    return result1245
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1247 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1991 = parse_relation_id(parser)
    relation_id1246 = _t1991
    consume_literal!(parser, ")")
    _t1992 = Proto.Demand(relation_id=relation_id1246)
    result1248 = _t1992
    record_span!(parser, span_start1247, "Demand")
    return result1248
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1251 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1993 = parse_name(parser)
    name1249 = _t1993
    _t1994 = parse_relation_id(parser)
    relation_id1250 = _t1994
    consume_literal!(parser, ")")
    _t1995 = Proto.Output(name=name1249, relation_id=relation_id1250)
    result1252 = _t1995
    record_span!(parser, span_start1251, "Output")
    return result1252
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1255 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1996 = parse_name(parser)
    name1253 = _t1996
    _t1997 = parse_epoch(parser)
    epoch1254 = _t1997
    consume_literal!(parser, ")")
    _t1998 = Proto.WhatIf(branch=name1253, epoch=epoch1254)
    result1256 = _t1998
    record_span!(parser, span_start1255, "WhatIf")
    return result1256
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1259 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2000 = parse_name(parser)
        _t1999 = _t2000
    else
        _t1999 = nothing
    end
    name1257 = _t1999
    _t2001 = parse_relation_id(parser)
    relation_id1258 = _t2001
    consume_literal!(parser, ")")
    _t2002 = Proto.Abort(name=(!isnothing(name1257) ? name1257 : "abort"), relation_id=relation_id1258)
    result1260 = _t2002
    record_span!(parser, span_start1259, "Abort")
    return result1260
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1264 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2004 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2005 = 0
            else
                _t2005 = -1
            end
            _t2004 = _t2005
        end
        _t2003 = _t2004
    else
        _t2003 = -1
    end
    prediction1261 = _t2003
    if prediction1261 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2007 = parse_export_iceberg_config(parser)
        export_iceberg_config1263 = _t2007
        consume_literal!(parser, ")")
        _t2008 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1263))
        _t2006 = _t2008
    else
        if prediction1261 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2010 = parse_export_csv_config(parser)
            export_csv_config1262 = _t2010
            consume_literal!(parser, ")")
            _t2011 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1262))
            _t2009 = _t2011
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2006 = _t2009
    end
    result1265 = _t2006
    record_span!(parser, span_start1264, "Export")
    return result1265
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1273 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2013 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2014 = 1
            else
                _t2014 = -1
            end
            _t2013 = _t2014
        end
        _t2012 = _t2013
    else
        _t2012 = -1
    end
    prediction1266 = _t2012
    if prediction1266 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2016 = parse_export_csv_path(parser)
        export_csv_path1270 = _t2016
        _t2017 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1271 = _t2017
        _t2018 = parse_config_dict(parser)
        config_dict1272 = _t2018
        consume_literal!(parser, ")")
        _t2019 = construct_export_csv_config(parser, export_csv_path1270, export_csv_columns_list1271, config_dict1272)
        _t2015 = _t2019
    else
        if prediction1266 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2021 = parse_export_csv_path(parser)
            export_csv_path1267 = _t2021
            _t2022 = parse_export_csv_source(parser)
            export_csv_source1268 = _t2022
            _t2023 = parse_csv_config(parser)
            csv_config1269 = _t2023
            consume_literal!(parser, ")")
            _t2024 = construct_export_csv_config_with_source(parser, export_csv_path1267, export_csv_source1268, csv_config1269)
            _t2020 = _t2024
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2015 = _t2020
    end
    result1274 = _t2015
    record_span!(parser, span_start1273, "ExportCSVConfig")
    return result1274
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1275 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1275
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1282 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2026 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2027 = 0
            else
                _t2027 = -1
            end
            _t2026 = _t2027
        end
        _t2025 = _t2026
    else
        _t2025 = -1
    end
    prediction1276 = _t2025
    if prediction1276 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2029 = parse_relation_id(parser)
        relation_id1281 = _t2029
        consume_literal!(parser, ")")
        _t2030 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1281))
        _t2028 = _t2030
    else
        if prediction1276 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1277 = Proto.ExportCSVColumn[]
            cond1278 = match_lookahead_literal(parser, "(", 0)
            while cond1278
                _t2032 = parse_export_csv_column(parser)
                item1279 = _t2032
                push!(xs1277, item1279)
                cond1278 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1280 = xs1277
            consume_literal!(parser, ")")
            _t2033 = Proto.ExportCSVColumns(columns=export_csv_columns1280)
            _t2034 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2033))
            _t2031 = _t2034
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2028 = _t2031
    end
    result1283 = _t2028
    record_span!(parser, span_start1282, "ExportCSVSource")
    return result1283
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1286 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1284 = consume_terminal!(parser, "STRING")
    _t2035 = parse_relation_id(parser)
    relation_id1285 = _t2035
    consume_literal!(parser, ")")
    _t2036 = Proto.ExportCSVColumn(column_name=string1284, column_data=relation_id1285)
    result1287 = _t2036
    record_span!(parser, span_start1286, "ExportCSVColumn")
    return result1287
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1288 = Proto.ExportCSVColumn[]
    cond1289 = match_lookahead_literal(parser, "(", 0)
    while cond1289
        _t2037 = parse_export_csv_column(parser)
        item1290 = _t2037
        push!(xs1288, item1290)
        cond1289 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1291 = xs1288
    consume_literal!(parser, ")")
    return export_csv_columns1291
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1304 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2038 = parse_iceberg_locator(parser)
    iceberg_locator1292 = _t2038
    _t2039 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1293 = _t2039
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2040 = parse_relation_id(parser)
    relation_id1294 = _t2040
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1295 = Proto.ExportIcebergColumn[]
    cond1296 = match_lookahead_literal(parser, "(", 0)
    while cond1296
        _t2041 = parse_export_iceberg_column(parser)
        item1297 = _t2041
        push!(xs1295, item1297)
        cond1296 = match_lookahead_literal(parser, "(", 0)
    end
    export_iceberg_columns1298 = xs1295
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1299 = Tuple{String, String}[]
    cond1300 = match_lookahead_literal(parser, "(", 0)
    while cond1300
        _t2042 = parse_iceberg_property_entry(parser)
        item1301 = _t2042
        push!(xs1299, item1301)
        cond1300 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1302 = xs1299
    consume_literal!(parser, ")")
    if match_lookahead_literal(parser, "{", 0)
        _t2044 = parse_config_dict(parser)
        _t2043 = _t2044
    else
        _t2043 = nothing
    end
    config_dict1303 = _t2043
    consume_literal!(parser, ")")
    _t2045 = construct_export_iceberg_config_full(parser, iceberg_locator1292, iceberg_catalog_config1293, relation_id1294, export_iceberg_columns1298, iceberg_property_entrys1302, config_dict1303)
    result1305 = _t2045
    record_span!(parser, span_start1304, "ExportIcebergConfig")
    return result1305
end

function parse_export_iceberg_column(parser::ParserState)::Proto.ExportIcebergColumn
    span_start1308 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_column")
    string1306 = consume_terminal!(parser, "STRING")
    _t2046 = parse_boolean_value(parser)
    boolean_value1307 = _t2046
    consume_literal!(parser, ")")
    _t2047 = Proto.ExportIcebergColumn(name=string1306, nullable=boolean_value1307)
    result1309 = _t2047
    record_span!(parser, span_start1308, "ExportIcebergColumn")
    return result1309
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
