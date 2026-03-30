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
        _t2057 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2058 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2059 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2060 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2061 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2062 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2063 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2064 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2065 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2066 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2066
    _t2067 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2067
    _t2068 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2068
    _t2069 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2069
    _t2070 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2070
    _t2071 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2071
    _t2072 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2072
    _t2073 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2073
    _t2074 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2074
    _t2075 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2075
    _t2076 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2076
    _t2077 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2077
    _t2078 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2078
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2079 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2079
    _t2080 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2080
    _t2081 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2081
    _t2082 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2082
    _t2083 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2083
    _t2084 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2084
    _t2085 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2085
    _t2086 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2086
    _t2087 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2087
    _t2088 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2088
    _t2089 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2089
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2090 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2090
    _t2091 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2091
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
    _t2092 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2092
    _t2093 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2093
    _t2094 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2094
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2095 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2095
    _t2096 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2096
    _t2097 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2097
    _t2098 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2098
    _t2099 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2099
    _t2100 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2100
    _t2101 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2101
    _t2102 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2102
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2103 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2103
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2104 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2104
end

function construct_iceberg_locator(parser::ParserState, table_name::String, namespace::Vector{String}, warehouse::String, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String})::Proto.IcebergLocator
    _t2105 = Proto.IcebergLocator(table_name=table_name, namespace=namespace, warehouse=warehouse, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""))
    return _t2105
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, columns::Vector{Proto.ExportGNFColumn}, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2106 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2106
    _t2107 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2107
    _t2108 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2108
    table_props = Dict(table_property_pairs)
    _t2109 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2109
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start664 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1317 = parse_configure(parser)
        _t1316 = _t1317
    else
        _t1316 = nothing
    end
    configure658 = _t1316
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1319 = parse_sync(parser)
        _t1318 = _t1319
    else
        _t1318 = nothing
    end
    sync659 = _t1318
    xs660 = Proto.Epoch[]
    cond661 = match_lookahead_literal(parser, "(", 0)
    while cond661
        _t1320 = parse_epoch(parser)
        item662 = _t1320
        push!(xs660, item662)
        cond661 = match_lookahead_literal(parser, "(", 0)
    end
    epochs663 = xs660
    consume_literal!(parser, ")")
    _t1321 = default_configure(parser)
    _t1322 = Proto.Transaction(epochs=epochs663, configure=(!isnothing(configure658) ? configure658 : _t1321), sync=sync659)
    result665 = _t1322
    record_span!(parser, span_start664, "Transaction")
    return result665
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start667 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1323 = parse_config_dict(parser)
    config_dict666 = _t1323
    consume_literal!(parser, ")")
    _t1324 = construct_configure(parser, config_dict666)
    result668 = _t1324
    record_span!(parser, span_start667, "Configure")
    return result668
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs669 = Tuple{String, Proto.Value}[]
    cond670 = match_lookahead_literal(parser, ":", 0)
    while cond670
        _t1325 = parse_config_key_value(parser)
        item671 = _t1325
        push!(xs669, item671)
        cond670 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values672 = xs669
    consume_literal!(parser, "}")
    return config_key_values672
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol673 = consume_terminal!(parser, "SYMBOL")
    _t1326 = parse_raw_value(parser)
    raw_value674 = _t1326
    return (symbol673, raw_value674,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start688 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1327 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1328 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1329 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1331 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1332 = 0
                        else
                            _t1332 = -1
                        end
                        _t1331 = _t1332
                    end
                    _t1330 = _t1331
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1333 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1334 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1335 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1336 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1337 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1338 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1339 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1340 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1341 = 10
                                                    else
                                                        _t1341 = -1
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
                        _t1333 = _t1334
                    end
                    _t1330 = _t1333
                end
                _t1329 = _t1330
            end
            _t1328 = _t1329
        end
        _t1327 = _t1328
    end
    prediction675 = _t1327
    if prediction675 == 12
        _t1343 = parse_boolean_value(parser)
        boolean_value687 = _t1343
        _t1344 = Proto.Value(value=OneOf(:boolean_value, boolean_value687))
        _t1342 = _t1344
    else
        if prediction675 == 11
            consume_literal!(parser, "missing")
            _t1346 = Proto.MissingValue()
            _t1347 = Proto.Value(value=OneOf(:missing_value, _t1346))
            _t1345 = _t1347
        else
            if prediction675 == 10
                decimal686 = consume_terminal!(parser, "DECIMAL")
                _t1349 = Proto.Value(value=OneOf(:decimal_value, decimal686))
                _t1348 = _t1349
            else
                if prediction675 == 9
                    int128685 = consume_terminal!(parser, "INT128")
                    _t1351 = Proto.Value(value=OneOf(:int128_value, int128685))
                    _t1350 = _t1351
                else
                    if prediction675 == 8
                        uint128684 = consume_terminal!(parser, "UINT128")
                        _t1353 = Proto.Value(value=OneOf(:uint128_value, uint128684))
                        _t1352 = _t1353
                    else
                        if prediction675 == 7
                            uint32683 = consume_terminal!(parser, "UINT32")
                            _t1355 = Proto.Value(value=OneOf(:uint32_value, uint32683))
                            _t1354 = _t1355
                        else
                            if prediction675 == 6
                                float682 = consume_terminal!(parser, "FLOAT")
                                _t1357 = Proto.Value(value=OneOf(:float_value, float682))
                                _t1356 = _t1357
                            else
                                if prediction675 == 5
                                    float32681 = consume_terminal!(parser, "FLOAT32")
                                    _t1359 = Proto.Value(value=OneOf(:float32_value, float32681))
                                    _t1358 = _t1359
                                else
                                    if prediction675 == 4
                                        int680 = consume_terminal!(parser, "INT")
                                        _t1361 = Proto.Value(value=OneOf(:int_value, int680))
                                        _t1360 = _t1361
                                    else
                                        if prediction675 == 3
                                            int32679 = consume_terminal!(parser, "INT32")
                                            _t1363 = Proto.Value(value=OneOf(:int32_value, int32679))
                                            _t1362 = _t1363
                                        else
                                            if prediction675 == 2
                                                string678 = consume_terminal!(parser, "STRING")
                                                _t1365 = Proto.Value(value=OneOf(:string_value, string678))
                                                _t1364 = _t1365
                                            else
                                                if prediction675 == 1
                                                    _t1367 = parse_raw_datetime(parser)
                                                    raw_datetime677 = _t1367
                                                    _t1368 = Proto.Value(value=OneOf(:datetime_value, raw_datetime677))
                                                    _t1366 = _t1368
                                                else
                                                    if prediction675 == 0
                                                        _t1370 = parse_raw_date(parser)
                                                        raw_date676 = _t1370
                                                        _t1371 = Proto.Value(value=OneOf(:date_value, raw_date676))
                                                        _t1369 = _t1371
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1366 = _t1369
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
                _t1348 = _t1350
            end
            _t1345 = _t1348
        end
        _t1342 = _t1345
    end
    result689 = _t1342
    record_span!(parser, span_start688, "Value")
    return result689
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start693 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int690 = consume_terminal!(parser, "INT")
    int_3691 = consume_terminal!(parser, "INT")
    int_4692 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1372 = Proto.DateValue(year=Int32(int690), month=Int32(int_3691), day=Int32(int_4692))
    result694 = _t1372
    record_span!(parser, span_start693, "DateValue")
    return result694
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start702 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int695 = consume_terminal!(parser, "INT")
    int_3696 = consume_terminal!(parser, "INT")
    int_4697 = consume_terminal!(parser, "INT")
    int_5698 = consume_terminal!(parser, "INT")
    int_6699 = consume_terminal!(parser, "INT")
    int_7700 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1373 = consume_terminal!(parser, "INT")
    else
        _t1373 = nothing
    end
    int_8701 = _t1373
    consume_literal!(parser, ")")
    _t1374 = Proto.DateTimeValue(year=Int32(int695), month=Int32(int_3696), day=Int32(int_4697), hour=Int32(int_5698), minute=Int32(int_6699), second=Int32(int_7700), microsecond=Int32((!isnothing(int_8701) ? int_8701 : 0)))
    result703 = _t1374
    record_span!(parser, span_start702, "DateTimeValue")
    return result703
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1375 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1376 = 1
        else
            _t1376 = -1
        end
        _t1375 = _t1376
    end
    prediction704 = _t1375
    if prediction704 == 1
        consume_literal!(parser, "false")
        _t1377 = false
    else
        if prediction704 == 0
            consume_literal!(parser, "true")
            _t1378 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1377 = _t1378
    end
    return _t1377
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start709 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs705 = Proto.FragmentId[]
    cond706 = match_lookahead_literal(parser, ":", 0)
    while cond706
        _t1379 = parse_fragment_id(parser)
        item707 = _t1379
        push!(xs705, item707)
        cond706 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids708 = xs705
    consume_literal!(parser, ")")
    _t1380 = Proto.Sync(fragments=fragment_ids708)
    result710 = _t1380
    record_span!(parser, span_start709, "Sync")
    return result710
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start712 = span_start(parser)
    consume_literal!(parser, ":")
    symbol711 = consume_terminal!(parser, "SYMBOL")
    result713 = Proto.FragmentId(Vector{UInt8}(symbol711))
    record_span!(parser, span_start712, "FragmentId")
    return result713
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start716 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1382 = parse_epoch_writes(parser)
        _t1381 = _t1382
    else
        _t1381 = nothing
    end
    epoch_writes714 = _t1381
    if match_lookahead_literal(parser, "(", 0)
        _t1384 = parse_epoch_reads(parser)
        _t1383 = _t1384
    else
        _t1383 = nothing
    end
    epoch_reads715 = _t1383
    consume_literal!(parser, ")")
    _t1385 = Proto.Epoch(writes=(!isnothing(epoch_writes714) ? epoch_writes714 : Proto.Write[]), reads=(!isnothing(epoch_reads715) ? epoch_reads715 : Proto.Read[]))
    result717 = _t1385
    record_span!(parser, span_start716, "Epoch")
    return result717
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs718 = Proto.Write[]
    cond719 = match_lookahead_literal(parser, "(", 0)
    while cond719
        _t1386 = parse_write(parser)
        item720 = _t1386
        push!(xs718, item720)
        cond719 = match_lookahead_literal(parser, "(", 0)
    end
    writes721 = xs718
    consume_literal!(parser, ")")
    return writes721
end

function parse_write(parser::ParserState)::Proto.Write
    span_start727 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1388 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1389 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1390 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1391 = 2
                    else
                        _t1391 = -1
                    end
                    _t1390 = _t1391
                end
                _t1389 = _t1390
            end
            _t1388 = _t1389
        end
        _t1387 = _t1388
    else
        _t1387 = -1
    end
    prediction722 = _t1387
    if prediction722 == 3
        _t1393 = parse_snapshot(parser)
        snapshot726 = _t1393
        _t1394 = Proto.Write(write_type=OneOf(:snapshot, snapshot726))
        _t1392 = _t1394
    else
        if prediction722 == 2
            _t1396 = parse_context(parser)
            context725 = _t1396
            _t1397 = Proto.Write(write_type=OneOf(:context, context725))
            _t1395 = _t1397
        else
            if prediction722 == 1
                _t1399 = parse_undefine(parser)
                undefine724 = _t1399
                _t1400 = Proto.Write(write_type=OneOf(:undefine, undefine724))
                _t1398 = _t1400
            else
                if prediction722 == 0
                    _t1402 = parse_define(parser)
                    define723 = _t1402
                    _t1403 = Proto.Write(write_type=OneOf(:define, define723))
                    _t1401 = _t1403
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1398 = _t1401
            end
            _t1395 = _t1398
        end
        _t1392 = _t1395
    end
    result728 = _t1392
    record_span!(parser, span_start727, "Write")
    return result728
end

function parse_define(parser::ParserState)::Proto.Define
    span_start730 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1404 = parse_fragment(parser)
    fragment729 = _t1404
    consume_literal!(parser, ")")
    _t1405 = Proto.Define(fragment=fragment729)
    result731 = _t1405
    record_span!(parser, span_start730, "Define")
    return result731
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start737 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1406 = parse_new_fragment_id(parser)
    new_fragment_id732 = _t1406
    xs733 = Proto.Declaration[]
    cond734 = match_lookahead_literal(parser, "(", 0)
    while cond734
        _t1407 = parse_declaration(parser)
        item735 = _t1407
        push!(xs733, item735)
        cond734 = match_lookahead_literal(parser, "(", 0)
    end
    declarations736 = xs733
    consume_literal!(parser, ")")
    result738 = construct_fragment(parser, new_fragment_id732, declarations736)
    record_span!(parser, span_start737, "Fragment")
    return result738
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start740 = span_start(parser)
    _t1408 = parse_fragment_id(parser)
    fragment_id739 = _t1408
    start_fragment!(parser, fragment_id739)
    result741 = fragment_id739
    record_span!(parser, span_start740, "FragmentId")
    return result741
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start747 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1410 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1411 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1412 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1413 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1414 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1415 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1416 = 1
                                else
                                    _t1416 = -1
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
    prediction742 = _t1409
    if prediction742 == 3
        _t1418 = parse_data(parser)
        data746 = _t1418
        _t1419 = Proto.Declaration(declaration_type=OneOf(:data, data746))
        _t1417 = _t1419
    else
        if prediction742 == 2
            _t1421 = parse_constraint(parser)
            constraint745 = _t1421
            _t1422 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint745))
            _t1420 = _t1422
        else
            if prediction742 == 1
                _t1424 = parse_algorithm(parser)
                algorithm744 = _t1424
                _t1425 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm744))
                _t1423 = _t1425
            else
                if prediction742 == 0
                    _t1427 = parse_def(parser)
                    def743 = _t1427
                    _t1428 = Proto.Declaration(declaration_type=OneOf(:def, def743))
                    _t1426 = _t1428
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1423 = _t1426
            end
            _t1420 = _t1423
        end
        _t1417 = _t1420
    end
    result748 = _t1417
    record_span!(parser, span_start747, "Declaration")
    return result748
end

function parse_def(parser::ParserState)::Proto.Def
    span_start752 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1429 = parse_relation_id(parser)
    relation_id749 = _t1429
    _t1430 = parse_abstraction(parser)
    abstraction750 = _t1430
    if match_lookahead_literal(parser, "(", 0)
        _t1432 = parse_attrs(parser)
        _t1431 = _t1432
    else
        _t1431 = nothing
    end
    attrs751 = _t1431
    consume_literal!(parser, ")")
    _t1433 = Proto.Def(name=relation_id749, body=abstraction750, attrs=(!isnothing(attrs751) ? attrs751 : Proto.Attribute[]))
    result753 = _t1433
    record_span!(parser, span_start752, "Def")
    return result753
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start757 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1434 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1435 = 1
        else
            _t1435 = -1
        end
        _t1434 = _t1435
    end
    prediction754 = _t1434
    if prediction754 == 1
        uint128756 = consume_terminal!(parser, "UINT128")
        _t1436 = Proto.RelationId(uint128756.low, uint128756.high)
    else
        if prediction754 == 0
            consume_literal!(parser, ":")
            symbol755 = consume_terminal!(parser, "SYMBOL")
            _t1437 = relation_id_from_string(parser, symbol755)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1436 = _t1437
    end
    result758 = _t1436
    record_span!(parser, span_start757, "RelationId")
    return result758
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start761 = span_start(parser)
    consume_literal!(parser, "(")
    _t1438 = parse_bindings(parser)
    bindings759 = _t1438
    _t1439 = parse_formula(parser)
    formula760 = _t1439
    consume_literal!(parser, ")")
    _t1440 = Proto.Abstraction(vars=vcat(bindings759[1], !isnothing(bindings759[2]) ? bindings759[2] : []), value=formula760)
    result762 = _t1440
    record_span!(parser, span_start761, "Abstraction")
    return result762
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs763 = Proto.Binding[]
    cond764 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond764
        _t1441 = parse_binding(parser)
        item765 = _t1441
        push!(xs763, item765)
        cond764 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings766 = xs763
    if match_lookahead_literal(parser, "|", 0)
        _t1443 = parse_value_bindings(parser)
        _t1442 = _t1443
    else
        _t1442 = nothing
    end
    value_bindings767 = _t1442
    consume_literal!(parser, "]")
    return (bindings766, (!isnothing(value_bindings767) ? value_bindings767 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start770 = span_start(parser)
    symbol768 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1444 = parse_type(parser)
    type769 = _t1444
    _t1445 = Proto.Var(name=symbol768)
    _t1446 = Proto.Binding(var=_t1445, var"#type"=type769)
    result771 = _t1446
    record_span!(parser, span_start770, "Binding")
    return result771
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start787 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1447 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1448 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1449 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1450 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1451 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1452 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1453 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1454 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1455 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1456 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1457 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1458 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1459 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1460 = 9
                                                        else
                                                            _t1460 = -1
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
            _t1448 = _t1449
        end
        _t1447 = _t1448
    end
    prediction772 = _t1447
    if prediction772 == 13
        _t1462 = parse_uint32_type(parser)
        uint32_type786 = _t1462
        _t1463 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type786))
        _t1461 = _t1463
    else
        if prediction772 == 12
            _t1465 = parse_float32_type(parser)
            float32_type785 = _t1465
            _t1466 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type785))
            _t1464 = _t1466
        else
            if prediction772 == 11
                _t1468 = parse_int32_type(parser)
                int32_type784 = _t1468
                _t1469 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type784))
                _t1467 = _t1469
            else
                if prediction772 == 10
                    _t1471 = parse_boolean_type(parser)
                    boolean_type783 = _t1471
                    _t1472 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type783))
                    _t1470 = _t1472
                else
                    if prediction772 == 9
                        _t1474 = parse_decimal_type(parser)
                        decimal_type782 = _t1474
                        _t1475 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type782))
                        _t1473 = _t1475
                    else
                        if prediction772 == 8
                            _t1477 = parse_missing_type(parser)
                            missing_type781 = _t1477
                            _t1478 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type781))
                            _t1476 = _t1478
                        else
                            if prediction772 == 7
                                _t1480 = parse_datetime_type(parser)
                                datetime_type780 = _t1480
                                _t1481 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type780))
                                _t1479 = _t1481
                            else
                                if prediction772 == 6
                                    _t1483 = parse_date_type(parser)
                                    date_type779 = _t1483
                                    _t1484 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type779))
                                    _t1482 = _t1484
                                else
                                    if prediction772 == 5
                                        _t1486 = parse_int128_type(parser)
                                        int128_type778 = _t1486
                                        _t1487 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type778))
                                        _t1485 = _t1487
                                    else
                                        if prediction772 == 4
                                            _t1489 = parse_uint128_type(parser)
                                            uint128_type777 = _t1489
                                            _t1490 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type777))
                                            _t1488 = _t1490
                                        else
                                            if prediction772 == 3
                                                _t1492 = parse_float_type(parser)
                                                float_type776 = _t1492
                                                _t1493 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type776))
                                                _t1491 = _t1493
                                            else
                                                if prediction772 == 2
                                                    _t1495 = parse_int_type(parser)
                                                    int_type775 = _t1495
                                                    _t1496 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type775))
                                                    _t1494 = _t1496
                                                else
                                                    if prediction772 == 1
                                                        _t1498 = parse_string_type(parser)
                                                        string_type774 = _t1498
                                                        _t1499 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type774))
                                                        _t1497 = _t1499
                                                    else
                                                        if prediction772 == 0
                                                            _t1501 = parse_unspecified_type(parser)
                                                            unspecified_type773 = _t1501
                                                            _t1502 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type773))
                                                            _t1500 = _t1502
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1497 = _t1500
                                                    end
                                                    _t1494 = _t1497
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
    result788 = _t1461
    record_span!(parser, span_start787, "Type")
    return result788
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start789 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1503 = Proto.UnspecifiedType()
    result790 = _t1503
    record_span!(parser, span_start789, "UnspecifiedType")
    return result790
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start791 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1504 = Proto.StringType()
    result792 = _t1504
    record_span!(parser, span_start791, "StringType")
    return result792
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start793 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1505 = Proto.IntType()
    result794 = _t1505
    record_span!(parser, span_start793, "IntType")
    return result794
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start795 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1506 = Proto.FloatType()
    result796 = _t1506
    record_span!(parser, span_start795, "FloatType")
    return result796
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start797 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1507 = Proto.UInt128Type()
    result798 = _t1507
    record_span!(parser, span_start797, "UInt128Type")
    return result798
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start799 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1508 = Proto.Int128Type()
    result800 = _t1508
    record_span!(parser, span_start799, "Int128Type")
    return result800
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start801 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1509 = Proto.DateType()
    result802 = _t1509
    record_span!(parser, span_start801, "DateType")
    return result802
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start803 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1510 = Proto.DateTimeType()
    result804 = _t1510
    record_span!(parser, span_start803, "DateTimeType")
    return result804
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start805 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1511 = Proto.MissingType()
    result806 = _t1511
    record_span!(parser, span_start805, "MissingType")
    return result806
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start809 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int807 = consume_terminal!(parser, "INT")
    int_3808 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1512 = Proto.DecimalType(precision=Int32(int807), scale=Int32(int_3808))
    result810 = _t1512
    record_span!(parser, span_start809, "DecimalType")
    return result810
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start811 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1513 = Proto.BooleanType()
    result812 = _t1513
    record_span!(parser, span_start811, "BooleanType")
    return result812
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start813 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1514 = Proto.Int32Type()
    result814 = _t1514
    record_span!(parser, span_start813, "Int32Type")
    return result814
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start815 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1515 = Proto.Float32Type()
    result816 = _t1515
    record_span!(parser, span_start815, "Float32Type")
    return result816
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start817 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1516 = Proto.UInt32Type()
    result818 = _t1516
    record_span!(parser, span_start817, "UInt32Type")
    return result818
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs819 = Proto.Binding[]
    cond820 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond820
        _t1517 = parse_binding(parser)
        item821 = _t1517
        push!(xs819, item821)
        cond820 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings822 = xs819
    return bindings822
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start837 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1519 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1520 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1521 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1522 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1523 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1524 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1525 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1526 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1527 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1528 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1529 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1530 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1531 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1532 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1533 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1534 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1535 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1536 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1537 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1538 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1539 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1540 = 10
                                                                                            else
                                                                                                _t1540 = -1
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
            end
            _t1519 = _t1520
        end
        _t1518 = _t1519
    else
        _t1518 = -1
    end
    prediction823 = _t1518
    if prediction823 == 12
        _t1542 = parse_cast(parser)
        cast836 = _t1542
        _t1543 = Proto.Formula(formula_type=OneOf(:cast, cast836))
        _t1541 = _t1543
    else
        if prediction823 == 11
            _t1545 = parse_rel_atom(parser)
            rel_atom835 = _t1545
            _t1546 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom835))
            _t1544 = _t1546
        else
            if prediction823 == 10
                _t1548 = parse_primitive(parser)
                primitive834 = _t1548
                _t1549 = Proto.Formula(formula_type=OneOf(:primitive, primitive834))
                _t1547 = _t1549
            else
                if prediction823 == 9
                    _t1551 = parse_pragma(parser)
                    pragma833 = _t1551
                    _t1552 = Proto.Formula(formula_type=OneOf(:pragma, pragma833))
                    _t1550 = _t1552
                else
                    if prediction823 == 8
                        _t1554 = parse_atom(parser)
                        atom832 = _t1554
                        _t1555 = Proto.Formula(formula_type=OneOf(:atom, atom832))
                        _t1553 = _t1555
                    else
                        if prediction823 == 7
                            _t1557 = parse_ffi(parser)
                            ffi831 = _t1557
                            _t1558 = Proto.Formula(formula_type=OneOf(:ffi, ffi831))
                            _t1556 = _t1558
                        else
                            if prediction823 == 6
                                _t1560 = parse_not(parser)
                                not830 = _t1560
                                _t1561 = Proto.Formula(formula_type=OneOf(:not, not830))
                                _t1559 = _t1561
                            else
                                if prediction823 == 5
                                    _t1563 = parse_disjunction(parser)
                                    disjunction829 = _t1563
                                    _t1564 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction829))
                                    _t1562 = _t1564
                                else
                                    if prediction823 == 4
                                        _t1566 = parse_conjunction(parser)
                                        conjunction828 = _t1566
                                        _t1567 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction828))
                                        _t1565 = _t1567
                                    else
                                        if prediction823 == 3
                                            _t1569 = parse_reduce(parser)
                                            reduce827 = _t1569
                                            _t1570 = Proto.Formula(formula_type=OneOf(:reduce, reduce827))
                                            _t1568 = _t1570
                                        else
                                            if prediction823 == 2
                                                _t1572 = parse_exists(parser)
                                                exists826 = _t1572
                                                _t1573 = Proto.Formula(formula_type=OneOf(:exists, exists826))
                                                _t1571 = _t1573
                                            else
                                                if prediction823 == 1
                                                    _t1575 = parse_false(parser)
                                                    false825 = _t1575
                                                    _t1576 = Proto.Formula(formula_type=OneOf(:disjunction, false825))
                                                    _t1574 = _t1576
                                                else
                                                    if prediction823 == 0
                                                        _t1578 = parse_true(parser)
                                                        true824 = _t1578
                                                        _t1579 = Proto.Formula(formula_type=OneOf(:conjunction, true824))
                                                        _t1577 = _t1579
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1574 = _t1577
                                                end
                                                _t1571 = _t1574
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
    result838 = _t1541
    record_span!(parser, span_start837, "Formula")
    return result838
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start839 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1580 = Proto.Conjunction(args=Proto.Formula[])
    result840 = _t1580
    record_span!(parser, span_start839, "Conjunction")
    return result840
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start841 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1581 = Proto.Disjunction(args=Proto.Formula[])
    result842 = _t1581
    record_span!(parser, span_start841, "Disjunction")
    return result842
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start845 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1582 = parse_bindings(parser)
    bindings843 = _t1582
    _t1583 = parse_formula(parser)
    formula844 = _t1583
    consume_literal!(parser, ")")
    _t1584 = Proto.Abstraction(vars=vcat(bindings843[1], !isnothing(bindings843[2]) ? bindings843[2] : []), value=formula844)
    _t1585 = Proto.Exists(body=_t1584)
    result846 = _t1585
    record_span!(parser, span_start845, "Exists")
    return result846
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start850 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1586 = parse_abstraction(parser)
    abstraction847 = _t1586
    _t1587 = parse_abstraction(parser)
    abstraction_3848 = _t1587
    _t1588 = parse_terms(parser)
    terms849 = _t1588
    consume_literal!(parser, ")")
    _t1589 = Proto.Reduce(op=abstraction847, body=abstraction_3848, terms=terms849)
    result851 = _t1589
    record_span!(parser, span_start850, "Reduce")
    return result851
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs852 = Proto.Term[]
    cond853 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond853
        _t1590 = parse_term(parser)
        item854 = _t1590
        push!(xs852, item854)
        cond853 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms855 = xs852
    consume_literal!(parser, ")")
    return terms855
end

function parse_term(parser::ParserState)::Proto.Term
    span_start859 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1591 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1592 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1593 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1594 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1595 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1596 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1597 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1598 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1599 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1600 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1601 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1602 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1603 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1604 = 1
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
            _t1592 = _t1593
        end
        _t1591 = _t1592
    end
    prediction856 = _t1591
    if prediction856 == 1
        _t1606 = parse_value(parser)
        value858 = _t1606
        _t1607 = Proto.Term(term_type=OneOf(:constant, value858))
        _t1605 = _t1607
    else
        if prediction856 == 0
            _t1609 = parse_var(parser)
            var857 = _t1609
            _t1610 = Proto.Term(term_type=OneOf(:var, var857))
            _t1608 = _t1610
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1605 = _t1608
    end
    result860 = _t1605
    record_span!(parser, span_start859, "Term")
    return result860
end

function parse_var(parser::ParserState)::Proto.Var
    span_start862 = span_start(parser)
    symbol861 = consume_terminal!(parser, "SYMBOL")
    _t1611 = Proto.Var(name=symbol861)
    result863 = _t1611
    record_span!(parser, span_start862, "Var")
    return result863
end

function parse_value(parser::ParserState)::Proto.Value
    span_start877 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1612 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1613 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1614 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1616 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1617 = 0
                        else
                            _t1617 = -1
                        end
                        _t1616 = _t1617
                    end
                    _t1615 = _t1616
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1618 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1619 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1620 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1621 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1622 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1623 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1624 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1625 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1626 = 10
                                                    else
                                                        _t1626 = -1
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
                            _t1619 = _t1620
                        end
                        _t1618 = _t1619
                    end
                    _t1615 = _t1618
                end
                _t1614 = _t1615
            end
            _t1613 = _t1614
        end
        _t1612 = _t1613
    end
    prediction864 = _t1612
    if prediction864 == 12
        _t1628 = parse_boolean_value(parser)
        boolean_value876 = _t1628
        _t1629 = Proto.Value(value=OneOf(:boolean_value, boolean_value876))
        _t1627 = _t1629
    else
        if prediction864 == 11
            consume_literal!(parser, "missing")
            _t1631 = Proto.MissingValue()
            _t1632 = Proto.Value(value=OneOf(:missing_value, _t1631))
            _t1630 = _t1632
        else
            if prediction864 == 10
                formatted_decimal875 = consume_terminal!(parser, "DECIMAL")
                _t1634 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal875))
                _t1633 = _t1634
            else
                if prediction864 == 9
                    formatted_int128874 = consume_terminal!(parser, "INT128")
                    _t1636 = Proto.Value(value=OneOf(:int128_value, formatted_int128874))
                    _t1635 = _t1636
                else
                    if prediction864 == 8
                        formatted_uint128873 = consume_terminal!(parser, "UINT128")
                        _t1638 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128873))
                        _t1637 = _t1638
                    else
                        if prediction864 == 7
                            formatted_uint32872 = consume_terminal!(parser, "UINT32")
                            _t1640 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32872))
                            _t1639 = _t1640
                        else
                            if prediction864 == 6
                                formatted_float871 = consume_terminal!(parser, "FLOAT")
                                _t1642 = Proto.Value(value=OneOf(:float_value, formatted_float871))
                                _t1641 = _t1642
                            else
                                if prediction864 == 5
                                    formatted_float32870 = consume_terminal!(parser, "FLOAT32")
                                    _t1644 = Proto.Value(value=OneOf(:float32_value, formatted_float32870))
                                    _t1643 = _t1644
                                else
                                    if prediction864 == 4
                                        formatted_int869 = consume_terminal!(parser, "INT")
                                        _t1646 = Proto.Value(value=OneOf(:int_value, formatted_int869))
                                        _t1645 = _t1646
                                    else
                                        if prediction864 == 3
                                            formatted_int32868 = consume_terminal!(parser, "INT32")
                                            _t1648 = Proto.Value(value=OneOf(:int32_value, formatted_int32868))
                                            _t1647 = _t1648
                                        else
                                            if prediction864 == 2
                                                formatted_string867 = consume_terminal!(parser, "STRING")
                                                _t1650 = Proto.Value(value=OneOf(:string_value, formatted_string867))
                                                _t1649 = _t1650
                                            else
                                                if prediction864 == 1
                                                    _t1652 = parse_datetime(parser)
                                                    datetime866 = _t1652
                                                    _t1653 = Proto.Value(value=OneOf(:datetime_value, datetime866))
                                                    _t1651 = _t1653
                                                else
                                                    if prediction864 == 0
                                                        _t1655 = parse_date(parser)
                                                        date865 = _t1655
                                                        _t1656 = Proto.Value(value=OneOf(:date_value, date865))
                                                        _t1654 = _t1656
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1651 = _t1654
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
                _t1633 = _t1635
            end
            _t1630 = _t1633
        end
        _t1627 = _t1630
    end
    result878 = _t1627
    record_span!(parser, span_start877, "Value")
    return result878
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start882 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int879 = consume_terminal!(parser, "INT")
    formatted_int_3880 = consume_terminal!(parser, "INT")
    formatted_int_4881 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1657 = Proto.DateValue(year=Int32(formatted_int879), month=Int32(formatted_int_3880), day=Int32(formatted_int_4881))
    result883 = _t1657
    record_span!(parser, span_start882, "DateValue")
    return result883
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start891 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int884 = consume_terminal!(parser, "INT")
    formatted_int_3885 = consume_terminal!(parser, "INT")
    formatted_int_4886 = consume_terminal!(parser, "INT")
    formatted_int_5887 = consume_terminal!(parser, "INT")
    formatted_int_6888 = consume_terminal!(parser, "INT")
    formatted_int_7889 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1658 = consume_terminal!(parser, "INT")
    else
        _t1658 = nothing
    end
    formatted_int_8890 = _t1658
    consume_literal!(parser, ")")
    _t1659 = Proto.DateTimeValue(year=Int32(formatted_int884), month=Int32(formatted_int_3885), day=Int32(formatted_int_4886), hour=Int32(formatted_int_5887), minute=Int32(formatted_int_6888), second=Int32(formatted_int_7889), microsecond=Int32((!isnothing(formatted_int_8890) ? formatted_int_8890 : 0)))
    result892 = _t1659
    record_span!(parser, span_start891, "DateTimeValue")
    return result892
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start897 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs893 = Proto.Formula[]
    cond894 = match_lookahead_literal(parser, "(", 0)
    while cond894
        _t1660 = parse_formula(parser)
        item895 = _t1660
        push!(xs893, item895)
        cond894 = match_lookahead_literal(parser, "(", 0)
    end
    formulas896 = xs893
    consume_literal!(parser, ")")
    _t1661 = Proto.Conjunction(args=formulas896)
    result898 = _t1661
    record_span!(parser, span_start897, "Conjunction")
    return result898
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start903 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs899 = Proto.Formula[]
    cond900 = match_lookahead_literal(parser, "(", 0)
    while cond900
        _t1662 = parse_formula(parser)
        item901 = _t1662
        push!(xs899, item901)
        cond900 = match_lookahead_literal(parser, "(", 0)
    end
    formulas902 = xs899
    consume_literal!(parser, ")")
    _t1663 = Proto.Disjunction(args=formulas902)
    result904 = _t1663
    record_span!(parser, span_start903, "Disjunction")
    return result904
end

function parse_not(parser::ParserState)::Proto.Not
    span_start906 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1664 = parse_formula(parser)
    formula905 = _t1664
    consume_literal!(parser, ")")
    _t1665 = Proto.Not(arg=formula905)
    result907 = _t1665
    record_span!(parser, span_start906, "Not")
    return result907
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start911 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1666 = parse_name(parser)
    name908 = _t1666
    _t1667 = parse_ffi_args(parser)
    ffi_args909 = _t1667
    _t1668 = parse_terms(parser)
    terms910 = _t1668
    consume_literal!(parser, ")")
    _t1669 = Proto.FFI(name=name908, args=ffi_args909, terms=terms910)
    result912 = _t1669
    record_span!(parser, span_start911, "FFI")
    return result912
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol913 = consume_terminal!(parser, "SYMBOL")
    return symbol913
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs914 = Proto.Abstraction[]
    cond915 = match_lookahead_literal(parser, "(", 0)
    while cond915
        _t1670 = parse_abstraction(parser)
        item916 = _t1670
        push!(xs914, item916)
        cond915 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions917 = xs914
    consume_literal!(parser, ")")
    return abstractions917
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start923 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1671 = parse_relation_id(parser)
    relation_id918 = _t1671
    xs919 = Proto.Term[]
    cond920 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond920
        _t1672 = parse_term(parser)
        item921 = _t1672
        push!(xs919, item921)
        cond920 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms922 = xs919
    consume_literal!(parser, ")")
    _t1673 = Proto.Atom(name=relation_id918, terms=terms922)
    result924 = _t1673
    record_span!(parser, span_start923, "Atom")
    return result924
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start930 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1674 = parse_name(parser)
    name925 = _t1674
    xs926 = Proto.Term[]
    cond927 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond927
        _t1675 = parse_term(parser)
        item928 = _t1675
        push!(xs926, item928)
        cond927 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms929 = xs926
    consume_literal!(parser, ")")
    _t1676 = Proto.Pragma(name=name925, terms=terms929)
    result931 = _t1676
    record_span!(parser, span_start930, "Pragma")
    return result931
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start947 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1678 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1679 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1680 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1681 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1682 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1683 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1684 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1685 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1686 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1687 = 7
                                            else
                                                _t1687 = -1
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
            end
            _t1678 = _t1679
        end
        _t1677 = _t1678
    else
        _t1677 = -1
    end
    prediction932 = _t1677
    if prediction932 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1689 = parse_name(parser)
        name942 = _t1689
        xs943 = Proto.RelTerm[]
        cond944 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond944
            _t1690 = parse_rel_term(parser)
            item945 = _t1690
            push!(xs943, item945)
            cond944 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms946 = xs943
        consume_literal!(parser, ")")
        _t1691 = Proto.Primitive(name=name942, terms=rel_terms946)
        _t1688 = _t1691
    else
        if prediction932 == 8
            _t1693 = parse_divide(parser)
            divide941 = _t1693
            _t1692 = divide941
        else
            if prediction932 == 7
                _t1695 = parse_multiply(parser)
                multiply940 = _t1695
                _t1694 = multiply940
            else
                if prediction932 == 6
                    _t1697 = parse_minus(parser)
                    minus939 = _t1697
                    _t1696 = minus939
                else
                    if prediction932 == 5
                        _t1699 = parse_add(parser)
                        add938 = _t1699
                        _t1698 = add938
                    else
                        if prediction932 == 4
                            _t1701 = parse_gt_eq(parser)
                            gt_eq937 = _t1701
                            _t1700 = gt_eq937
                        else
                            if prediction932 == 3
                                _t1703 = parse_gt(parser)
                                gt936 = _t1703
                                _t1702 = gt936
                            else
                                if prediction932 == 2
                                    _t1705 = parse_lt_eq(parser)
                                    lt_eq935 = _t1705
                                    _t1704 = lt_eq935
                                else
                                    if prediction932 == 1
                                        _t1707 = parse_lt(parser)
                                        lt934 = _t1707
                                        _t1706 = lt934
                                    else
                                        if prediction932 == 0
                                            _t1709 = parse_eq(parser)
                                            eq933 = _t1709
                                            _t1708 = eq933
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
            _t1692 = _t1694
        end
        _t1688 = _t1692
    end
    result948 = _t1688
    record_span!(parser, span_start947, "Primitive")
    return result948
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start951 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1710 = parse_term(parser)
    term949 = _t1710
    _t1711 = parse_term(parser)
    term_3950 = _t1711
    consume_literal!(parser, ")")
    _t1712 = Proto.RelTerm(rel_term_type=OneOf(:term, term949))
    _t1713 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3950))
    _t1714 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1712, _t1713])
    result952 = _t1714
    record_span!(parser, span_start951, "Primitive")
    return result952
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start955 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1715 = parse_term(parser)
    term953 = _t1715
    _t1716 = parse_term(parser)
    term_3954 = _t1716
    consume_literal!(parser, ")")
    _t1717 = Proto.RelTerm(rel_term_type=OneOf(:term, term953))
    _t1718 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3954))
    _t1719 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1717, _t1718])
    result956 = _t1719
    record_span!(parser, span_start955, "Primitive")
    return result956
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start959 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1720 = parse_term(parser)
    term957 = _t1720
    _t1721 = parse_term(parser)
    term_3958 = _t1721
    consume_literal!(parser, ")")
    _t1722 = Proto.RelTerm(rel_term_type=OneOf(:term, term957))
    _t1723 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3958))
    _t1724 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1722, _t1723])
    result960 = _t1724
    record_span!(parser, span_start959, "Primitive")
    return result960
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start963 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1725 = parse_term(parser)
    term961 = _t1725
    _t1726 = parse_term(parser)
    term_3962 = _t1726
    consume_literal!(parser, ")")
    _t1727 = Proto.RelTerm(rel_term_type=OneOf(:term, term961))
    _t1728 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3962))
    _t1729 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1727, _t1728])
    result964 = _t1729
    record_span!(parser, span_start963, "Primitive")
    return result964
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start967 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1730 = parse_term(parser)
    term965 = _t1730
    _t1731 = parse_term(parser)
    term_3966 = _t1731
    consume_literal!(parser, ")")
    _t1732 = Proto.RelTerm(rel_term_type=OneOf(:term, term965))
    _t1733 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3966))
    _t1734 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1732, _t1733])
    result968 = _t1734
    record_span!(parser, span_start967, "Primitive")
    return result968
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start972 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1735 = parse_term(parser)
    term969 = _t1735
    _t1736 = parse_term(parser)
    term_3970 = _t1736
    _t1737 = parse_term(parser)
    term_4971 = _t1737
    consume_literal!(parser, ")")
    _t1738 = Proto.RelTerm(rel_term_type=OneOf(:term, term969))
    _t1739 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3970))
    _t1740 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4971))
    _t1741 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1738, _t1739, _t1740])
    result973 = _t1741
    record_span!(parser, span_start972, "Primitive")
    return result973
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start977 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1742 = parse_term(parser)
    term974 = _t1742
    _t1743 = parse_term(parser)
    term_3975 = _t1743
    _t1744 = parse_term(parser)
    term_4976 = _t1744
    consume_literal!(parser, ")")
    _t1745 = Proto.RelTerm(rel_term_type=OneOf(:term, term974))
    _t1746 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3975))
    _t1747 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4976))
    _t1748 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1745, _t1746, _t1747])
    result978 = _t1748
    record_span!(parser, span_start977, "Primitive")
    return result978
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start982 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1749 = parse_term(parser)
    term979 = _t1749
    _t1750 = parse_term(parser)
    term_3980 = _t1750
    _t1751 = parse_term(parser)
    term_4981 = _t1751
    consume_literal!(parser, ")")
    _t1752 = Proto.RelTerm(rel_term_type=OneOf(:term, term979))
    _t1753 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3980))
    _t1754 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4981))
    _t1755 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1752, _t1753, _t1754])
    result983 = _t1755
    record_span!(parser, span_start982, "Primitive")
    return result983
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start987 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1756 = parse_term(parser)
    term984 = _t1756
    _t1757 = parse_term(parser)
    term_3985 = _t1757
    _t1758 = parse_term(parser)
    term_4986 = _t1758
    consume_literal!(parser, ")")
    _t1759 = Proto.RelTerm(rel_term_type=OneOf(:term, term984))
    _t1760 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3985))
    _t1761 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4986))
    _t1762 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1759, _t1760, _t1761])
    result988 = _t1762
    record_span!(parser, span_start987, "Primitive")
    return result988
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start992 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1763 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1764 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1765 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1766 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1767 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1768 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1769 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1770 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1771 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1772 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1773 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1774 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1775 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1776 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1777 = 1
                                                            else
                                                                _t1777 = -1
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
            _t1764 = _t1765
        end
        _t1763 = _t1764
    end
    prediction989 = _t1763
    if prediction989 == 1
        _t1779 = parse_term(parser)
        term991 = _t1779
        _t1780 = Proto.RelTerm(rel_term_type=OneOf(:term, term991))
        _t1778 = _t1780
    else
        if prediction989 == 0
            _t1782 = parse_specialized_value(parser)
            specialized_value990 = _t1782
            _t1783 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value990))
            _t1781 = _t1783
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1778 = _t1781
    end
    result993 = _t1778
    record_span!(parser, span_start992, "RelTerm")
    return result993
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start995 = span_start(parser)
    consume_literal!(parser, "#")
    _t1784 = parse_raw_value(parser)
    raw_value994 = _t1784
    result996 = raw_value994
    record_span!(parser, span_start995, "Value")
    return result996
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1002 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1785 = parse_name(parser)
    name997 = _t1785
    xs998 = Proto.RelTerm[]
    cond999 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond999
        _t1786 = parse_rel_term(parser)
        item1000 = _t1786
        push!(xs998, item1000)
        cond999 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1001 = xs998
    consume_literal!(parser, ")")
    _t1787 = Proto.RelAtom(name=name997, terms=rel_terms1001)
    result1003 = _t1787
    record_span!(parser, span_start1002, "RelAtom")
    return result1003
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1006 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1788 = parse_term(parser)
    term1004 = _t1788
    _t1789 = parse_term(parser)
    term_31005 = _t1789
    consume_literal!(parser, ")")
    _t1790 = Proto.Cast(input=term1004, result=term_31005)
    result1007 = _t1790
    record_span!(parser, span_start1006, "Cast")
    return result1007
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1008 = Proto.Attribute[]
    cond1009 = match_lookahead_literal(parser, "(", 0)
    while cond1009
        _t1791 = parse_attribute(parser)
        item1010 = _t1791
        push!(xs1008, item1010)
        cond1009 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1011 = xs1008
    consume_literal!(parser, ")")
    return attributes1011
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1017 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1792 = parse_name(parser)
    name1012 = _t1792
    xs1013 = Proto.Value[]
    cond1014 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1014
        _t1793 = parse_raw_value(parser)
        item1015 = _t1793
        push!(xs1013, item1015)
        cond1014 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1016 = xs1013
    consume_literal!(parser, ")")
    _t1794 = Proto.Attribute(name=name1012, args=raw_values1016)
    result1018 = _t1794
    record_span!(parser, span_start1017, "Attribute")
    return result1018
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1024 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1019 = Proto.RelationId[]
    cond1020 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1020
        _t1795 = parse_relation_id(parser)
        item1021 = _t1795
        push!(xs1019, item1021)
        cond1020 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1022 = xs1019
    _t1796 = parse_script(parser)
    script1023 = _t1796
    consume_literal!(parser, ")")
    _t1797 = Proto.Algorithm(var"#global"=relation_ids1022, body=script1023)
    result1025 = _t1797
    record_span!(parser, span_start1024, "Algorithm")
    return result1025
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1030 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1026 = Proto.Construct[]
    cond1027 = match_lookahead_literal(parser, "(", 0)
    while cond1027
        _t1798 = parse_construct(parser)
        item1028 = _t1798
        push!(xs1026, item1028)
        cond1027 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1029 = xs1026
    consume_literal!(parser, ")")
    _t1799 = Proto.Script(constructs=constructs1029)
    result1031 = _t1799
    record_span!(parser, span_start1030, "Script")
    return result1031
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1035 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1801 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1802 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1803 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1804 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1805 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1806 = 1
                            else
                                _t1806 = -1
                            end
                            _t1805 = _t1806
                        end
                        _t1804 = _t1805
                    end
                    _t1803 = _t1804
                end
                _t1802 = _t1803
            end
            _t1801 = _t1802
        end
        _t1800 = _t1801
    else
        _t1800 = -1
    end
    prediction1032 = _t1800
    if prediction1032 == 1
        _t1808 = parse_instruction(parser)
        instruction1034 = _t1808
        _t1809 = Proto.Construct(construct_type=OneOf(:instruction, instruction1034))
        _t1807 = _t1809
    else
        if prediction1032 == 0
            _t1811 = parse_loop(parser)
            loop1033 = _t1811
            _t1812 = Proto.Construct(construct_type=OneOf(:loop, loop1033))
            _t1810 = _t1812
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1807 = _t1810
    end
    result1036 = _t1807
    record_span!(parser, span_start1035, "Construct")
    return result1036
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1039 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1813 = parse_init(parser)
    init1037 = _t1813
    _t1814 = parse_script(parser)
    script1038 = _t1814
    consume_literal!(parser, ")")
    _t1815 = Proto.Loop(init=init1037, body=script1038)
    result1040 = _t1815
    record_span!(parser, span_start1039, "Loop")
    return result1040
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1041 = Proto.Instruction[]
    cond1042 = match_lookahead_literal(parser, "(", 0)
    while cond1042
        _t1816 = parse_instruction(parser)
        item1043 = _t1816
        push!(xs1041, item1043)
        cond1042 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1044 = xs1041
    consume_literal!(parser, ")")
    return instructions1044
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1051 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1818 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1819 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1820 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1821 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1822 = 0
                        else
                            _t1822 = -1
                        end
                        _t1821 = _t1822
                    end
                    _t1820 = _t1821
                end
                _t1819 = _t1820
            end
            _t1818 = _t1819
        end
        _t1817 = _t1818
    else
        _t1817 = -1
    end
    prediction1045 = _t1817
    if prediction1045 == 4
        _t1824 = parse_monus_def(parser)
        monus_def1050 = _t1824
        _t1825 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1050))
        _t1823 = _t1825
    else
        if prediction1045 == 3
            _t1827 = parse_monoid_def(parser)
            monoid_def1049 = _t1827
            _t1828 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1049))
            _t1826 = _t1828
        else
            if prediction1045 == 2
                _t1830 = parse_break(parser)
                break1048 = _t1830
                _t1831 = Proto.Instruction(instr_type=OneOf(:var"#break", break1048))
                _t1829 = _t1831
            else
                if prediction1045 == 1
                    _t1833 = parse_upsert(parser)
                    upsert1047 = _t1833
                    _t1834 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1047))
                    _t1832 = _t1834
                else
                    if prediction1045 == 0
                        _t1836 = parse_assign(parser)
                        assign1046 = _t1836
                        _t1837 = Proto.Instruction(instr_type=OneOf(:assign, assign1046))
                        _t1835 = _t1837
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1832 = _t1835
                end
                _t1829 = _t1832
            end
            _t1826 = _t1829
        end
        _t1823 = _t1826
    end
    result1052 = _t1823
    record_span!(parser, span_start1051, "Instruction")
    return result1052
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1056 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1838 = parse_relation_id(parser)
    relation_id1053 = _t1838
    _t1839 = parse_abstraction(parser)
    abstraction1054 = _t1839
    if match_lookahead_literal(parser, "(", 0)
        _t1841 = parse_attrs(parser)
        _t1840 = _t1841
    else
        _t1840 = nothing
    end
    attrs1055 = _t1840
    consume_literal!(parser, ")")
    _t1842 = Proto.Assign(name=relation_id1053, body=abstraction1054, attrs=(!isnothing(attrs1055) ? attrs1055 : Proto.Attribute[]))
    result1057 = _t1842
    record_span!(parser, span_start1056, "Assign")
    return result1057
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1061 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1843 = parse_relation_id(parser)
    relation_id1058 = _t1843
    _t1844 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1059 = _t1844
    if match_lookahead_literal(parser, "(", 0)
        _t1846 = parse_attrs(parser)
        _t1845 = _t1846
    else
        _t1845 = nothing
    end
    attrs1060 = _t1845
    consume_literal!(parser, ")")
    _t1847 = Proto.Upsert(name=relation_id1058, body=abstraction_with_arity1059[1], attrs=(!isnothing(attrs1060) ? attrs1060 : Proto.Attribute[]), value_arity=abstraction_with_arity1059[2])
    result1062 = _t1847
    record_span!(parser, span_start1061, "Upsert")
    return result1062
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1848 = parse_bindings(parser)
    bindings1063 = _t1848
    _t1849 = parse_formula(parser)
    formula1064 = _t1849
    consume_literal!(parser, ")")
    _t1850 = Proto.Abstraction(vars=vcat(bindings1063[1], !isnothing(bindings1063[2]) ? bindings1063[2] : []), value=formula1064)
    return (_t1850, length(bindings1063[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1068 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1851 = parse_relation_id(parser)
    relation_id1065 = _t1851
    _t1852 = parse_abstraction(parser)
    abstraction1066 = _t1852
    if match_lookahead_literal(parser, "(", 0)
        _t1854 = parse_attrs(parser)
        _t1853 = _t1854
    else
        _t1853 = nothing
    end
    attrs1067 = _t1853
    consume_literal!(parser, ")")
    _t1855 = Proto.Break(name=relation_id1065, body=abstraction1066, attrs=(!isnothing(attrs1067) ? attrs1067 : Proto.Attribute[]))
    result1069 = _t1855
    record_span!(parser, span_start1068, "Break")
    return result1069
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1074 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1856 = parse_monoid(parser)
    monoid1070 = _t1856
    _t1857 = parse_relation_id(parser)
    relation_id1071 = _t1857
    _t1858 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1072 = _t1858
    if match_lookahead_literal(parser, "(", 0)
        _t1860 = parse_attrs(parser)
        _t1859 = _t1860
    else
        _t1859 = nothing
    end
    attrs1073 = _t1859
    consume_literal!(parser, ")")
    _t1861 = Proto.MonoidDef(monoid=monoid1070, name=relation_id1071, body=abstraction_with_arity1072[1], attrs=(!isnothing(attrs1073) ? attrs1073 : Proto.Attribute[]), value_arity=abstraction_with_arity1072[2])
    result1075 = _t1861
    record_span!(parser, span_start1074, "MonoidDef")
    return result1075
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1081 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1863 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1864 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1865 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1866 = 2
                    else
                        _t1866 = -1
                    end
                    _t1865 = _t1866
                end
                _t1864 = _t1865
            end
            _t1863 = _t1864
        end
        _t1862 = _t1863
    else
        _t1862 = -1
    end
    prediction1076 = _t1862
    if prediction1076 == 3
        _t1868 = parse_sum_monoid(parser)
        sum_monoid1080 = _t1868
        _t1869 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1080))
        _t1867 = _t1869
    else
        if prediction1076 == 2
            _t1871 = parse_max_monoid(parser)
            max_monoid1079 = _t1871
            _t1872 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1079))
            _t1870 = _t1872
        else
            if prediction1076 == 1
                _t1874 = parse_min_monoid(parser)
                min_monoid1078 = _t1874
                _t1875 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1078))
                _t1873 = _t1875
            else
                if prediction1076 == 0
                    _t1877 = parse_or_monoid(parser)
                    or_monoid1077 = _t1877
                    _t1878 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1077))
                    _t1876 = _t1878
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1873 = _t1876
            end
            _t1870 = _t1873
        end
        _t1867 = _t1870
    end
    result1082 = _t1867
    record_span!(parser, span_start1081, "Monoid")
    return result1082
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1083 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1879 = Proto.OrMonoid()
    result1084 = _t1879
    record_span!(parser, span_start1083, "OrMonoid")
    return result1084
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1086 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1880 = parse_type(parser)
    type1085 = _t1880
    consume_literal!(parser, ")")
    _t1881 = Proto.MinMonoid(var"#type"=type1085)
    result1087 = _t1881
    record_span!(parser, span_start1086, "MinMonoid")
    return result1087
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1089 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1882 = parse_type(parser)
    type1088 = _t1882
    consume_literal!(parser, ")")
    _t1883 = Proto.MaxMonoid(var"#type"=type1088)
    result1090 = _t1883
    record_span!(parser, span_start1089, "MaxMonoid")
    return result1090
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1092 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1884 = parse_type(parser)
    type1091 = _t1884
    consume_literal!(parser, ")")
    _t1885 = Proto.SumMonoid(var"#type"=type1091)
    result1093 = _t1885
    record_span!(parser, span_start1092, "SumMonoid")
    return result1093
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1098 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1886 = parse_monoid(parser)
    monoid1094 = _t1886
    _t1887 = parse_relation_id(parser)
    relation_id1095 = _t1887
    _t1888 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1096 = _t1888
    if match_lookahead_literal(parser, "(", 0)
        _t1890 = parse_attrs(parser)
        _t1889 = _t1890
    else
        _t1889 = nothing
    end
    attrs1097 = _t1889
    consume_literal!(parser, ")")
    _t1891 = Proto.MonusDef(monoid=monoid1094, name=relation_id1095, body=abstraction_with_arity1096[1], attrs=(!isnothing(attrs1097) ? attrs1097 : Proto.Attribute[]), value_arity=abstraction_with_arity1096[2])
    result1099 = _t1891
    record_span!(parser, span_start1098, "MonusDef")
    return result1099
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1104 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1892 = parse_relation_id(parser)
    relation_id1100 = _t1892
    _t1893 = parse_abstraction(parser)
    abstraction1101 = _t1893
    _t1894 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1102 = _t1894
    _t1895 = parse_functional_dependency_values(parser)
    functional_dependency_values1103 = _t1895
    consume_literal!(parser, ")")
    _t1896 = Proto.FunctionalDependency(guard=abstraction1101, keys=functional_dependency_keys1102, values=functional_dependency_values1103)
    _t1897 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1896), name=relation_id1100)
    result1105 = _t1897
    record_span!(parser, span_start1104, "Constraint")
    return result1105
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1106 = Proto.Var[]
    cond1107 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1107
        _t1898 = parse_var(parser)
        item1108 = _t1898
        push!(xs1106, item1108)
        cond1107 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1109 = xs1106
    consume_literal!(parser, ")")
    return vars1109
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1110 = Proto.Var[]
    cond1111 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1111
        _t1899 = parse_var(parser)
        item1112 = _t1899
        push!(xs1110, item1112)
        cond1111 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1113 = xs1110
    consume_literal!(parser, ")")
    return vars1113
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1119 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1901 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1902 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1903 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1904 = 1
                    else
                        _t1904 = -1
                    end
                    _t1903 = _t1904
                end
                _t1902 = _t1903
            end
            _t1901 = _t1902
        end
        _t1900 = _t1901
    else
        _t1900 = -1
    end
    prediction1114 = _t1900
    if prediction1114 == 3
        _t1906 = parse_iceberg_data(parser)
        iceberg_data1118 = _t1906
        _t1907 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1118))
        _t1905 = _t1907
    else
        if prediction1114 == 2
            _t1909 = parse_csv_data(parser)
            csv_data1117 = _t1909
            _t1910 = Proto.Data(data_type=OneOf(:csv_data, csv_data1117))
            _t1908 = _t1910
        else
            if prediction1114 == 1
                _t1912 = parse_betree_relation(parser)
                betree_relation1116 = _t1912
                _t1913 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1116))
                _t1911 = _t1913
            else
                if prediction1114 == 0
                    _t1915 = parse_edb(parser)
                    edb1115 = _t1915
                    _t1916 = Proto.Data(data_type=OneOf(:edb, edb1115))
                    _t1914 = _t1916
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1911 = _t1914
            end
            _t1908 = _t1911
        end
        _t1905 = _t1908
    end
    result1120 = _t1905
    record_span!(parser, span_start1119, "Data")
    return result1120
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1124 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1917 = parse_relation_id(parser)
    relation_id1121 = _t1917
    _t1918 = parse_edb_path(parser)
    edb_path1122 = _t1918
    _t1919 = parse_edb_types(parser)
    edb_types1123 = _t1919
    consume_literal!(parser, ")")
    _t1920 = Proto.EDB(target_id=relation_id1121, path=edb_path1122, types=edb_types1123)
    result1125 = _t1920
    record_span!(parser, span_start1124, "EDB")
    return result1125
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1126 = String[]
    cond1127 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1127
        item1128 = consume_terminal!(parser, "STRING")
        push!(xs1126, item1128)
        cond1127 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1129 = xs1126
    consume_literal!(parser, "]")
    return strings1129
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1130 = Proto.var"#Type"[]
    cond1131 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1131
        _t1921 = parse_type(parser)
        item1132 = _t1921
        push!(xs1130, item1132)
        cond1131 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1133 = xs1130
    consume_literal!(parser, "]")
    return types1133
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1136 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1922 = parse_relation_id(parser)
    relation_id1134 = _t1922
    _t1923 = parse_betree_info(parser)
    betree_info1135 = _t1923
    consume_literal!(parser, ")")
    _t1924 = Proto.BeTreeRelation(name=relation_id1134, relation_info=betree_info1135)
    result1137 = _t1924
    record_span!(parser, span_start1136, "BeTreeRelation")
    return result1137
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1141 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1925 = parse_betree_info_key_types(parser)
    betree_info_key_types1138 = _t1925
    _t1926 = parse_betree_info_value_types(parser)
    betree_info_value_types1139 = _t1926
    _t1927 = parse_config_dict(parser)
    config_dict1140 = _t1927
    consume_literal!(parser, ")")
    _t1928 = construct_betree_info(parser, betree_info_key_types1138, betree_info_value_types1139, config_dict1140)
    result1142 = _t1928
    record_span!(parser, span_start1141, "BeTreeInfo")
    return result1142
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1143 = Proto.var"#Type"[]
    cond1144 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1144
        _t1929 = parse_type(parser)
        item1145 = _t1929
        push!(xs1143, item1145)
        cond1144 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1146 = xs1143
    consume_literal!(parser, ")")
    return types1146
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1147 = Proto.var"#Type"[]
    cond1148 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1148
        _t1930 = parse_type(parser)
        item1149 = _t1930
        push!(xs1147, item1149)
        cond1148 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1150 = xs1147
    consume_literal!(parser, ")")
    return types1150
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1155 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1931 = parse_csvlocator(parser)
    csvlocator1151 = _t1931
    _t1932 = parse_csv_config(parser)
    csv_config1152 = _t1932
    _t1933 = parse_gnf_columns(parser)
    gnf_columns1153 = _t1933
    _t1934 = parse_csv_asof(parser)
    csv_asof1154 = _t1934
    consume_literal!(parser, ")")
    _t1935 = Proto.CSVData(locator=csvlocator1151, config=csv_config1152, columns=gnf_columns1153, asof=csv_asof1154)
    result1156 = _t1935
    record_span!(parser, span_start1155, "CSVData")
    return result1156
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1159 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1937 = parse_csv_locator_paths(parser)
        _t1936 = _t1937
    else
        _t1936 = nothing
    end
    csv_locator_paths1157 = _t1936
    if match_lookahead_literal(parser, "(", 0)
        _t1939 = parse_csv_locator_inline_data(parser)
        _t1938 = _t1939
    else
        _t1938 = nothing
    end
    csv_locator_inline_data1158 = _t1938
    consume_literal!(parser, ")")
    _t1940 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1157) ? csv_locator_paths1157 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1158) ? csv_locator_inline_data1158 : "")))
    result1160 = _t1940
    record_span!(parser, span_start1159, "CSVLocator")
    return result1160
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1161 = String[]
    cond1162 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1162
        item1163 = consume_terminal!(parser, "STRING")
        push!(xs1161, item1163)
        cond1162 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1164 = xs1161
    consume_literal!(parser, ")")
    return strings1164
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1165 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1165
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1167 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1941 = parse_config_dict(parser)
    config_dict1166 = _t1941
    consume_literal!(parser, ")")
    _t1942 = construct_csv_config(parser, config_dict1166)
    result1168 = _t1942
    record_span!(parser, span_start1167, "CSVConfig")
    return result1168
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1169 = Proto.GNFColumn[]
    cond1170 = match_lookahead_literal(parser, "(", 0)
    while cond1170
        _t1943 = parse_gnf_column(parser)
        item1171 = _t1943
        push!(xs1169, item1171)
        cond1170 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1172 = xs1169
    consume_literal!(parser, ")")
    return gnf_columns1172
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1179 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1944 = parse_gnf_column_path(parser)
    gnf_column_path1173 = _t1944
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1946 = parse_relation_id(parser)
        _t1945 = _t1946
    else
        _t1945 = nothing
    end
    relation_id1174 = _t1945
    consume_literal!(parser, "[")
    xs1175 = Proto.var"#Type"[]
    cond1176 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1176
        _t1947 = parse_type(parser)
        item1177 = _t1947
        push!(xs1175, item1177)
        cond1176 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1178 = xs1175
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1948 = Proto.GNFColumn(column_path=gnf_column_path1173, target_id=relation_id1174, types=types1178)
    result1180 = _t1948
    record_span!(parser, span_start1179, "GNFColumn")
    return result1180
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1949 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1950 = 0
        else
            _t1950 = -1
        end
        _t1949 = _t1950
    end
    prediction1181 = _t1949
    if prediction1181 == 1
        consume_literal!(parser, "[")
        xs1183 = String[]
        cond1184 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1184
            item1185 = consume_terminal!(parser, "STRING")
            push!(xs1183, item1185)
            cond1184 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1186 = xs1183
        consume_literal!(parser, "]")
        _t1951 = strings1186
    else
        if prediction1181 == 0
            string1182 = consume_terminal!(parser, "STRING")
            _t1952 = String[string1182]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1951 = _t1952
    end
    return _t1951
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1187 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1187
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1192 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1953 = parse_iceberg_locator(parser)
    iceberg_locator1188 = _t1953
    _t1954 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1189 = _t1954
    _t1955 = parse_gnf_columns(parser)
    gnf_columns1190 = _t1955
    _t1956 = parse_boolean_value(parser)
    boolean_value1191 = _t1956
    consume_literal!(parser, ")")
    _t1957 = Proto.IcebergData(locator=iceberg_locator1188, config=iceberg_catalog_config1189, columns=gnf_columns1190, returns_delta=boolean_value1191)
    result1193 = _t1957
    record_span!(parser, span_start1192, "IcebergData")
    return result1193
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1202 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1194 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1195 = String[]
    cond1196 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1196
        item1197 = consume_terminal!(parser, "STRING")
        push!(xs1195, item1197)
        cond1196 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1198 = xs1195
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string_121199 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1959 = parse_iceberg_from_snapshot(parser)
        _t1958 = _t1959
    else
        _t1958 = nothing
    end
    iceberg_from_snapshot1200 = _t1958
    if match_lookahead_literal(parser, "(", 0)
        _t1961 = parse_iceberg_to_snapshot(parser)
        _t1960 = _t1961
    else
        _t1960 = nothing
    end
    iceberg_to_snapshot1201 = _t1960
    consume_literal!(parser, ")")
    _t1962 = construct_iceberg_locator(parser, string1194, strings1198, string_121199, iceberg_from_snapshot1200, iceberg_to_snapshot1201)
    result1203 = _t1962
    record_span!(parser, span_start1202, "IcebergLocator")
    return result1203
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1204 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1204
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1205 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1205
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1216 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1206 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1964 = parse_iceberg_catalog_config_scope(parser)
        _t1963 = _t1964
    else
        _t1963 = nothing
    end
    iceberg_catalog_config_scope1207 = _t1963
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1208 = Tuple{String, String}[]
    cond1209 = match_lookahead_literal(parser, "(", 0)
    while cond1209
        _t1965 = parse_iceberg_property_entry(parser)
        item1210 = _t1965
        push!(xs1208, item1210)
        cond1209 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1211 = xs1208
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1212 = Tuple{String, String}[]
    cond1213 = match_lookahead_literal(parser, "(", 0)
    while cond1213
        _t1966 = parse_iceberg_property_entry(parser)
        item1214 = _t1966
        push!(xs1212, item1214)
        cond1213 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys_131215 = xs1212
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1967 = construct_iceberg_catalog_config(parser, string1206, iceberg_catalog_config_scope1207, iceberg_property_entrys1211, iceberg_property_entrys_131215)
    result1217 = _t1967
    record_span!(parser, span_start1216, "IcebergCatalogConfig")
    return result1217
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1218 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1218
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1219 = consume_terminal!(parser, "STRING")
    string_31220 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1219, string_31220,)
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1222 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1968 = parse_fragment_id(parser)
    fragment_id1221 = _t1968
    consume_literal!(parser, ")")
    _t1969 = Proto.Undefine(fragment_id=fragment_id1221)
    result1223 = _t1969
    record_span!(parser, span_start1222, "Undefine")
    return result1223
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1228 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1224 = Proto.RelationId[]
    cond1225 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1225
        _t1970 = parse_relation_id(parser)
        item1226 = _t1970
        push!(xs1224, item1226)
        cond1225 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1227 = xs1224
    consume_literal!(parser, ")")
    _t1971 = Proto.Context(relations=relation_ids1227)
    result1229 = _t1971
    record_span!(parser, span_start1228, "Context")
    return result1229
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1234 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1230 = Proto.SnapshotMapping[]
    cond1231 = match_lookahead_literal(parser, "[", 0)
    while cond1231
        _t1972 = parse_snapshot_mapping(parser)
        item1232 = _t1972
        push!(xs1230, item1232)
        cond1231 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1233 = xs1230
    consume_literal!(parser, ")")
    _t1973 = Proto.Snapshot(mappings=snapshot_mappings1233)
    result1235 = _t1973
    record_span!(parser, span_start1234, "Snapshot")
    return result1235
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1238 = span_start(parser)
    _t1974 = parse_edb_path(parser)
    edb_path1236 = _t1974
    _t1975 = parse_relation_id(parser)
    relation_id1237 = _t1975
    _t1976 = Proto.SnapshotMapping(destination_path=edb_path1236, source_relation=relation_id1237)
    result1239 = _t1976
    record_span!(parser, span_start1238, "SnapshotMapping")
    return result1239
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1240 = Proto.Read[]
    cond1241 = match_lookahead_literal(parser, "(", 0)
    while cond1241
        _t1977 = parse_read(parser)
        item1242 = _t1977
        push!(xs1240, item1242)
        cond1241 = match_lookahead_literal(parser, "(", 0)
    end
    reads1243 = xs1240
    consume_literal!(parser, ")")
    return reads1243
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1250 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1979 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1980 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t1981 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t1982 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t1983 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t1984 = 3
                            else
                                _t1984 = -1
                            end
                            _t1983 = _t1984
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
    else
        _t1978 = -1
    end
    prediction1244 = _t1978
    if prediction1244 == 4
        _t1986 = parse_export(parser)
        export1249 = _t1986
        _t1987 = Proto.Read(read_type=OneOf(:var"#export", export1249))
        _t1985 = _t1987
    else
        if prediction1244 == 3
            _t1989 = parse_abort(parser)
            abort1248 = _t1989
            _t1990 = Proto.Read(read_type=OneOf(:abort, abort1248))
            _t1988 = _t1990
        else
            if prediction1244 == 2
                _t1992 = parse_what_if(parser)
                what_if1247 = _t1992
                _t1993 = Proto.Read(read_type=OneOf(:what_if, what_if1247))
                _t1991 = _t1993
            else
                if prediction1244 == 1
                    _t1995 = parse_output(parser)
                    output1246 = _t1995
                    _t1996 = Proto.Read(read_type=OneOf(:output, output1246))
                    _t1994 = _t1996
                else
                    if prediction1244 == 0
                        _t1998 = parse_demand(parser)
                        demand1245 = _t1998
                        _t1999 = Proto.Read(read_type=OneOf(:demand, demand1245))
                        _t1997 = _t1999
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1994 = _t1997
                end
                _t1991 = _t1994
            end
            _t1988 = _t1991
        end
        _t1985 = _t1988
    end
    result1251 = _t1985
    record_span!(parser, span_start1250, "Read")
    return result1251
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1253 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2000 = parse_relation_id(parser)
    relation_id1252 = _t2000
    consume_literal!(parser, ")")
    _t2001 = Proto.Demand(relation_id=relation_id1252)
    result1254 = _t2001
    record_span!(parser, span_start1253, "Demand")
    return result1254
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1257 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2002 = parse_name(parser)
    name1255 = _t2002
    _t2003 = parse_relation_id(parser)
    relation_id1256 = _t2003
    consume_literal!(parser, ")")
    _t2004 = Proto.Output(name=name1255, relation_id=relation_id1256)
    result1258 = _t2004
    record_span!(parser, span_start1257, "Output")
    return result1258
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1261 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2005 = parse_name(parser)
    name1259 = _t2005
    _t2006 = parse_epoch(parser)
    epoch1260 = _t2006
    consume_literal!(parser, ")")
    _t2007 = Proto.WhatIf(branch=name1259, epoch=epoch1260)
    result1262 = _t2007
    record_span!(parser, span_start1261, "WhatIf")
    return result1262
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1265 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2009 = parse_name(parser)
        _t2008 = _t2009
    else
        _t2008 = nothing
    end
    name1263 = _t2008
    _t2010 = parse_relation_id(parser)
    relation_id1264 = _t2010
    consume_literal!(parser, ")")
    _t2011 = Proto.Abort(name=(!isnothing(name1263) ? name1263 : "abort"), relation_id=relation_id1264)
    result1266 = _t2011
    record_span!(parser, span_start1265, "Abort")
    return result1266
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1270 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2013 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2014 = 0
            else
                _t2014 = -1
            end
            _t2013 = _t2014
        end
        _t2012 = _t2013
    else
        _t2012 = -1
    end
    prediction1267 = _t2012
    if prediction1267 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2016 = parse_export_iceberg_config(parser)
        export_iceberg_config1269 = _t2016
        consume_literal!(parser, ")")
        _t2017 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1269))
        _t2015 = _t2017
    else
        if prediction1267 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2019 = parse_export_csv_config(parser)
            export_csv_config1268 = _t2019
            consume_literal!(parser, ")")
            _t2020 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1268))
            _t2018 = _t2020
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2015 = _t2018
    end
    result1271 = _t2015
    record_span!(parser, span_start1270, "Export")
    return result1271
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1279 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2022 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2023 = 1
            else
                _t2023 = -1
            end
            _t2022 = _t2023
        end
        _t2021 = _t2022
    else
        _t2021 = -1
    end
    prediction1272 = _t2021
    if prediction1272 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2025 = parse_export_csv_path(parser)
        export_csv_path1276 = _t2025
        _t2026 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1277 = _t2026
        _t2027 = parse_config_dict(parser)
        config_dict1278 = _t2027
        consume_literal!(parser, ")")
        _t2028 = construct_export_csv_config(parser, export_csv_path1276, export_csv_columns_list1277, config_dict1278)
        _t2024 = _t2028
    else
        if prediction1272 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2030 = parse_export_csv_path(parser)
            export_csv_path1273 = _t2030
            _t2031 = parse_export_csv_source(parser)
            export_csv_source1274 = _t2031
            _t2032 = parse_csv_config(parser)
            csv_config1275 = _t2032
            consume_literal!(parser, ")")
            _t2033 = construct_export_csv_config_with_source(parser, export_csv_path1273, export_csv_source1274, csv_config1275)
            _t2029 = _t2033
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2024 = _t2029
    end
    result1280 = _t2024
    record_span!(parser, span_start1279, "ExportCSVConfig")
    return result1280
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1281 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1281
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1288 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2035 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2036 = 0
            else
                _t2036 = -1
            end
            _t2035 = _t2036
        end
        _t2034 = _t2035
    else
        _t2034 = -1
    end
    prediction1282 = _t2034
    if prediction1282 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2038 = parse_relation_id(parser)
        relation_id1287 = _t2038
        consume_literal!(parser, ")")
        _t2039 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1287))
        _t2037 = _t2039
    else
        if prediction1282 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1283 = Proto.ExportCSVColumn[]
            cond1284 = match_lookahead_literal(parser, "(", 0)
            while cond1284
                _t2041 = parse_export_csv_column(parser)
                item1285 = _t2041
                push!(xs1283, item1285)
                cond1284 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1286 = xs1283
            consume_literal!(parser, ")")
            _t2042 = Proto.ExportCSVColumns(columns=export_csv_columns1286)
            _t2043 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2042))
            _t2040 = _t2043
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2037 = _t2040
    end
    result1289 = _t2037
    record_span!(parser, span_start1288, "ExportCSVSource")
    return result1289
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1292 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1290 = consume_terminal!(parser, "STRING")
    _t2044 = parse_relation_id(parser)
    relation_id1291 = _t2044
    consume_literal!(parser, ")")
    _t2045 = Proto.ExportCSVColumn(column_name=string1290, column_data=relation_id1291)
    result1293 = _t2045
    record_span!(parser, span_start1292, "ExportCSVColumn")
    return result1293
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1294 = Proto.ExportCSVColumn[]
    cond1295 = match_lookahead_literal(parser, "(", 0)
    while cond1295
        _t2046 = parse_export_csv_column(parser)
        item1296 = _t2046
        push!(xs1294, item1296)
        cond1295 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1297 = xs1294
    consume_literal!(parser, ")")
    return export_csv_columns1297
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1310 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2047 = parse_iceberg_locator(parser)
    iceberg_locator1298 = _t2047
    _t2048 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1299 = _t2048
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2049 = parse_relation_id(parser)
    relation_id1300 = _t2049
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1301 = Proto.ExportGNFColumn[]
    cond1302 = match_lookahead_literal(parser, "(", 0)
    while cond1302
        _t2050 = parse_export_gnf_column(parser)
        item1303 = _t2050
        push!(xs1301, item1303)
        cond1302 = match_lookahead_literal(parser, "(", 0)
    end
    export_gnf_columns1304 = xs1301
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1305 = Tuple{String, String}[]
    cond1306 = match_lookahead_literal(parser, "(", 0)
    while cond1306
        _t2051 = parse_iceberg_property_entry(parser)
        item1307 = _t2051
        push!(xs1305, item1307)
        cond1306 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1308 = xs1305
    consume_literal!(parser, ")")
    if match_lookahead_literal(parser, "{", 0)
        _t2053 = parse_config_dict(parser)
        _t2052 = _t2053
    else
        _t2052 = nothing
    end
    config_dict1309 = _t2052
    consume_literal!(parser, ")")
    _t2054 = construct_export_iceberg_config_full(parser, iceberg_locator1298, iceberg_catalog_config1299, relation_id1300, export_gnf_columns1304, iceberg_property_entrys1308, config_dict1309)
    result1311 = _t2054
    record_span!(parser, span_start1310, "ExportIcebergConfig")
    return result1311
end

function parse_export_gnf_column(parser::ParserState)::Proto.ExportGNFColumn
    span_start1314 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "gnf_column")
    string1312 = consume_terminal!(parser, "STRING")
    _t2055 = parse_boolean_value(parser)
    boolean_value1313 = _t2055
    consume_literal!(parser, ")")
    _t2056 = Proto.ExportGNFColumn(name=string1312, nullable=boolean_value1313)
    result1315 = _t2056
    record_span!(parser, span_start1314, "ExportGNFColumn")
    return result1315
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
