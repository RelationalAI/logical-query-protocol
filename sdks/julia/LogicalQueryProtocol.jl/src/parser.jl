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
    ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_.#/-]*", scan_symbol),
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
        _t2081 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2082 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2083 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2084 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2085 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2086 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2087 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2088 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2089 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2090 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2090
    _t2091 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2091
    _t2092 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2092
    _t2093 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2093
    _t2094 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2094
    _t2095 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2095
    _t2096 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2096
    _t2097 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2097
    _t2098 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2098
    _t2099 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2099
    _t2100 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2100
    _t2101 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2101
    _t2102 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2102
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2103 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2103
    _t2104 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2104
    _t2105 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2105
    _t2106 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2106
    _t2107 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2107
    _t2108 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2108
    _t2109 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2109
    _t2110 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2110
    _t2111 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2111
    _t2112 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2112
    _t2113 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2113
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2114 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2114
    _t2115 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2115
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
    _t2116 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2116
    _t2117 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2117
    _t2118 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2118
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2119 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2119
    _t2120 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2120
    _t2121 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2121
    _t2122 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2122
    _t2123 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2123
    _t2124 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2124
    _t2125 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2125
    _t2126 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2126
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2127 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2127
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2128 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2128
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2129 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2129
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2130 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2130
    _t2131 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2131
    _t2132 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2132
    table_props = Dict(table_property_pairs)
    _t2133 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2133
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start671 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1331 = parse_configure(parser)
        _t1330 = _t1331
    else
        _t1330 = nothing
    end
    configure665 = _t1330
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1333 = parse_sync(parser)
        _t1332 = _t1333
    else
        _t1332 = nothing
    end
    sync666 = _t1332
    xs667 = Proto.Epoch[]
    cond668 = match_lookahead_literal(parser, "(", 0)
    while cond668
        _t1334 = parse_epoch(parser)
        item669 = _t1334
        push!(xs667, item669)
        cond668 = match_lookahead_literal(parser, "(", 0)
    end
    epochs670 = xs667
    consume_literal!(parser, ")")
    _t1335 = default_configure(parser)
    _t1336 = Proto.Transaction(epochs=epochs670, configure=(!isnothing(configure665) ? configure665 : _t1335), sync=sync666)
    result672 = _t1336
    record_span!(parser, span_start671, "Transaction")
    return result672
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start674 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1337 = parse_config_dict(parser)
    config_dict673 = _t1337
    consume_literal!(parser, ")")
    _t1338 = construct_configure(parser, config_dict673)
    result675 = _t1338
    record_span!(parser, span_start674, "Configure")
    return result675
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs676 = Tuple{String, Proto.Value}[]
    cond677 = match_lookahead_literal(parser, ":", 0)
    while cond677
        _t1339 = parse_config_key_value(parser)
        item678 = _t1339
        push!(xs676, item678)
        cond677 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values679 = xs676
    consume_literal!(parser, "}")
    return config_key_values679
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol680 = consume_terminal!(parser, "SYMBOL")
    _t1340 = parse_raw_value(parser)
    raw_value681 = _t1340
    return (symbol680, raw_value681,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start695 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1341 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1342 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1343 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1345 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1346 = 0
                        else
                            _t1346 = -1
                        end
                        _t1345 = _t1346
                    end
                    _t1344 = _t1345
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1347 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1348 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1349 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1350 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1351 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1352 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1353 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1354 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1355 = 10
                                                    else
                                                        _t1355 = -1
                                                    end
                                                    _t1354 = _t1355
                                                end
                                                _t1353 = _t1354
                                            end
                                            _t1352 = _t1353
                                        end
                                        _t1351 = _t1352
                                    end
                                    _t1350 = _t1351
                                end
                                _t1349 = _t1350
                            end
                            _t1348 = _t1349
                        end
                        _t1347 = _t1348
                    end
                    _t1344 = _t1347
                end
                _t1343 = _t1344
            end
            _t1342 = _t1343
        end
        _t1341 = _t1342
    end
    prediction682 = _t1341
    if prediction682 == 12
        _t1357 = parse_boolean_value(parser)
        boolean_value694 = _t1357
        _t1358 = Proto.Value(value=OneOf(:boolean_value, boolean_value694))
        _t1356 = _t1358
    else
        if prediction682 == 11
            consume_literal!(parser, "missing")
            _t1360 = Proto.MissingValue()
            _t1361 = Proto.Value(value=OneOf(:missing_value, _t1360))
            _t1359 = _t1361
        else
            if prediction682 == 10
                decimal693 = consume_terminal!(parser, "DECIMAL")
                _t1363 = Proto.Value(value=OneOf(:decimal_value, decimal693))
                _t1362 = _t1363
            else
                if prediction682 == 9
                    int128692 = consume_terminal!(parser, "INT128")
                    _t1365 = Proto.Value(value=OneOf(:int128_value, int128692))
                    _t1364 = _t1365
                else
                    if prediction682 == 8
                        uint128691 = consume_terminal!(parser, "UINT128")
                        _t1367 = Proto.Value(value=OneOf(:uint128_value, uint128691))
                        _t1366 = _t1367
                    else
                        if prediction682 == 7
                            uint32690 = consume_terminal!(parser, "UINT32")
                            _t1369 = Proto.Value(value=OneOf(:uint32_value, uint32690))
                            _t1368 = _t1369
                        else
                            if prediction682 == 6
                                float689 = consume_terminal!(parser, "FLOAT")
                                _t1371 = Proto.Value(value=OneOf(:float_value, float689))
                                _t1370 = _t1371
                            else
                                if prediction682 == 5
                                    float32688 = consume_terminal!(parser, "FLOAT32")
                                    _t1373 = Proto.Value(value=OneOf(:float32_value, float32688))
                                    _t1372 = _t1373
                                else
                                    if prediction682 == 4
                                        int687 = consume_terminal!(parser, "INT")
                                        _t1375 = Proto.Value(value=OneOf(:int_value, int687))
                                        _t1374 = _t1375
                                    else
                                        if prediction682 == 3
                                            int32686 = consume_terminal!(parser, "INT32")
                                            _t1377 = Proto.Value(value=OneOf(:int32_value, int32686))
                                            _t1376 = _t1377
                                        else
                                            if prediction682 == 2
                                                string685 = consume_terminal!(parser, "STRING")
                                                _t1379 = Proto.Value(value=OneOf(:string_value, string685))
                                                _t1378 = _t1379
                                            else
                                                if prediction682 == 1
                                                    _t1381 = parse_raw_datetime(parser)
                                                    raw_datetime684 = _t1381
                                                    _t1382 = Proto.Value(value=OneOf(:datetime_value, raw_datetime684))
                                                    _t1380 = _t1382
                                                else
                                                    if prediction682 == 0
                                                        _t1384 = parse_raw_date(parser)
                                                        raw_date683 = _t1384
                                                        _t1385 = Proto.Value(value=OneOf(:date_value, raw_date683))
                                                        _t1383 = _t1385
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1380 = _t1383
                                                end
                                                _t1378 = _t1380
                                            end
                                            _t1376 = _t1378
                                        end
                                        _t1374 = _t1376
                                    end
                                    _t1372 = _t1374
                                end
                                _t1370 = _t1372
                            end
                            _t1368 = _t1370
                        end
                        _t1366 = _t1368
                    end
                    _t1364 = _t1366
                end
                _t1362 = _t1364
            end
            _t1359 = _t1362
        end
        _t1356 = _t1359
    end
    result696 = _t1356
    record_span!(parser, span_start695, "Value")
    return result696
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start700 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int697 = consume_terminal!(parser, "INT")
    int_3698 = consume_terminal!(parser, "INT")
    int_4699 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1386 = Proto.DateValue(year=Int32(int697), month=Int32(int_3698), day=Int32(int_4699))
    result701 = _t1386
    record_span!(parser, span_start700, "DateValue")
    return result701
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start709 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int702 = consume_terminal!(parser, "INT")
    int_3703 = consume_terminal!(parser, "INT")
    int_4704 = consume_terminal!(parser, "INT")
    int_5705 = consume_terminal!(parser, "INT")
    int_6706 = consume_terminal!(parser, "INT")
    int_7707 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1387 = consume_terminal!(parser, "INT")
    else
        _t1387 = nothing
    end
    int_8708 = _t1387
    consume_literal!(parser, ")")
    _t1388 = Proto.DateTimeValue(year=Int32(int702), month=Int32(int_3703), day=Int32(int_4704), hour=Int32(int_5705), minute=Int32(int_6706), second=Int32(int_7707), microsecond=Int32((!isnothing(int_8708) ? int_8708 : 0)))
    result710 = _t1388
    record_span!(parser, span_start709, "DateTimeValue")
    return result710
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1389 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1390 = 1
        else
            _t1390 = -1
        end
        _t1389 = _t1390
    end
    prediction711 = _t1389
    if prediction711 == 1
        consume_literal!(parser, "false")
        _t1391 = false
    else
        if prediction711 == 0
            consume_literal!(parser, "true")
            _t1392 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1391 = _t1392
    end
    return _t1391
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start716 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs712 = Proto.FragmentId[]
    cond713 = match_lookahead_literal(parser, ":", 0)
    while cond713
        _t1393 = parse_fragment_id(parser)
        item714 = _t1393
        push!(xs712, item714)
        cond713 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids715 = xs712
    consume_literal!(parser, ")")
    _t1394 = Proto.Sync(fragments=fragment_ids715)
    result717 = _t1394
    record_span!(parser, span_start716, "Sync")
    return result717
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start719 = span_start(parser)
    consume_literal!(parser, ":")
    symbol718 = consume_terminal!(parser, "SYMBOL")
    result720 = Proto.FragmentId(Vector{UInt8}(symbol718))
    record_span!(parser, span_start719, "FragmentId")
    return result720
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start723 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1396 = parse_epoch_writes(parser)
        _t1395 = _t1396
    else
        _t1395 = nothing
    end
    epoch_writes721 = _t1395
    if match_lookahead_literal(parser, "(", 0)
        _t1398 = parse_epoch_reads(parser)
        _t1397 = _t1398
    else
        _t1397 = nothing
    end
    epoch_reads722 = _t1397
    consume_literal!(parser, ")")
    _t1399 = Proto.Epoch(writes=(!isnothing(epoch_writes721) ? epoch_writes721 : Proto.Write[]), reads=(!isnothing(epoch_reads722) ? epoch_reads722 : Proto.Read[]))
    result724 = _t1399
    record_span!(parser, span_start723, "Epoch")
    return result724
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs725 = Proto.Write[]
    cond726 = match_lookahead_literal(parser, "(", 0)
    while cond726
        _t1400 = parse_write(parser)
        item727 = _t1400
        push!(xs725, item727)
        cond726 = match_lookahead_literal(parser, "(", 0)
    end
    writes728 = xs725
    consume_literal!(parser, ")")
    return writes728
end

function parse_write(parser::ParserState)::Proto.Write
    span_start734 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1402 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1403 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1404 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1405 = 2
                    else
                        _t1405 = -1
                    end
                    _t1404 = _t1405
                end
                _t1403 = _t1404
            end
            _t1402 = _t1403
        end
        _t1401 = _t1402
    else
        _t1401 = -1
    end
    prediction729 = _t1401
    if prediction729 == 3
        _t1407 = parse_snapshot(parser)
        snapshot733 = _t1407
        _t1408 = Proto.Write(write_type=OneOf(:snapshot, snapshot733))
        _t1406 = _t1408
    else
        if prediction729 == 2
            _t1410 = parse_context(parser)
            context732 = _t1410
            _t1411 = Proto.Write(write_type=OneOf(:context, context732))
            _t1409 = _t1411
        else
            if prediction729 == 1
                _t1413 = parse_undefine(parser)
                undefine731 = _t1413
                _t1414 = Proto.Write(write_type=OneOf(:undefine, undefine731))
                _t1412 = _t1414
            else
                if prediction729 == 0
                    _t1416 = parse_define(parser)
                    define730 = _t1416
                    _t1417 = Proto.Write(write_type=OneOf(:define, define730))
                    _t1415 = _t1417
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1412 = _t1415
            end
            _t1409 = _t1412
        end
        _t1406 = _t1409
    end
    result735 = _t1406
    record_span!(parser, span_start734, "Write")
    return result735
end

function parse_define(parser::ParserState)::Proto.Define
    span_start737 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1418 = parse_fragment(parser)
    fragment736 = _t1418
    consume_literal!(parser, ")")
    _t1419 = Proto.Define(fragment=fragment736)
    result738 = _t1419
    record_span!(parser, span_start737, "Define")
    return result738
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start744 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1420 = parse_new_fragment_id(parser)
    new_fragment_id739 = _t1420
    xs740 = Proto.Declaration[]
    cond741 = match_lookahead_literal(parser, "(", 0)
    while cond741
        _t1421 = parse_declaration(parser)
        item742 = _t1421
        push!(xs740, item742)
        cond741 = match_lookahead_literal(parser, "(", 0)
    end
    declarations743 = xs740
    consume_literal!(parser, ")")
    result745 = construct_fragment(parser, new_fragment_id739, declarations743)
    record_span!(parser, span_start744, "Fragment")
    return result745
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start747 = span_start(parser)
    _t1422 = parse_fragment_id(parser)
    fragment_id746 = _t1422
    start_fragment!(parser, fragment_id746)
    result748 = fragment_id746
    record_span!(parser, span_start747, "FragmentId")
    return result748
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start754 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1424 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1425 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1426 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1427 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1428 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1429 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1430 = 1
                                else
                                    _t1430 = -1
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
    else
        _t1423 = -1
    end
    prediction749 = _t1423
    if prediction749 == 3
        _t1432 = parse_data(parser)
        data753 = _t1432
        _t1433 = Proto.Declaration(declaration_type=OneOf(:data, data753))
        _t1431 = _t1433
    else
        if prediction749 == 2
            _t1435 = parse_constraint(parser)
            constraint752 = _t1435
            _t1436 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint752))
            _t1434 = _t1436
        else
            if prediction749 == 1
                _t1438 = parse_algorithm(parser)
                algorithm751 = _t1438
                _t1439 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm751))
                _t1437 = _t1439
            else
                if prediction749 == 0
                    _t1441 = parse_def(parser)
                    def750 = _t1441
                    _t1442 = Proto.Declaration(declaration_type=OneOf(:def, def750))
                    _t1440 = _t1442
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1437 = _t1440
            end
            _t1434 = _t1437
        end
        _t1431 = _t1434
    end
    result755 = _t1431
    record_span!(parser, span_start754, "Declaration")
    return result755
end

function parse_def(parser::ParserState)::Proto.Def
    span_start759 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1443 = parse_relation_id(parser)
    relation_id756 = _t1443
    _t1444 = parse_abstraction(parser)
    abstraction757 = _t1444
    if match_lookahead_literal(parser, "(", 0)
        _t1446 = parse_attrs(parser)
        _t1445 = _t1446
    else
        _t1445 = nothing
    end
    attrs758 = _t1445
    consume_literal!(parser, ")")
    _t1447 = Proto.Def(name=relation_id756, body=abstraction757, attrs=(!isnothing(attrs758) ? attrs758 : Proto.Attribute[]))
    result760 = _t1447
    record_span!(parser, span_start759, "Def")
    return result760
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start764 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1448 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1449 = 1
        else
            _t1449 = -1
        end
        _t1448 = _t1449
    end
    prediction761 = _t1448
    if prediction761 == 1
        uint128763 = consume_terminal!(parser, "UINT128")
        _t1450 = Proto.RelationId(uint128763.low, uint128763.high)
    else
        if prediction761 == 0
            consume_literal!(parser, ":")
            symbol762 = consume_terminal!(parser, "SYMBOL")
            _t1451 = relation_id_from_string(parser, symbol762)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1450 = _t1451
    end
    result765 = _t1450
    record_span!(parser, span_start764, "RelationId")
    return result765
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start768 = span_start(parser)
    consume_literal!(parser, "(")
    _t1452 = parse_bindings(parser)
    bindings766 = _t1452
    _t1453 = parse_formula(parser)
    formula767 = _t1453
    consume_literal!(parser, ")")
    _t1454 = Proto.Abstraction(vars=vcat(bindings766[1], !isnothing(bindings766[2]) ? bindings766[2] : []), value=formula767)
    result769 = _t1454
    record_span!(parser, span_start768, "Abstraction")
    return result769
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs770 = Proto.Binding[]
    cond771 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond771
        _t1455 = parse_binding(parser)
        item772 = _t1455
        push!(xs770, item772)
        cond771 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings773 = xs770
    if match_lookahead_literal(parser, "|", 0)
        _t1457 = parse_value_bindings(parser)
        _t1456 = _t1457
    else
        _t1456 = nothing
    end
    value_bindings774 = _t1456
    consume_literal!(parser, "]")
    return (bindings773, (!isnothing(value_bindings774) ? value_bindings774 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start777 = span_start(parser)
    symbol775 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1458 = parse_type(parser)
    type776 = _t1458
    _t1459 = Proto.Var(name=symbol775)
    _t1460 = Proto.Binding(var=_t1459, var"#type"=type776)
    result778 = _t1460
    record_span!(parser, span_start777, "Binding")
    return result778
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start794 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1461 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1462 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1463 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1464 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1465 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1466 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1467 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1468 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1469 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1470 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1471 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1472 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1473 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1474 = 9
                                                        else
                                                            _t1474 = -1
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
                _t1463 = _t1464
            end
            _t1462 = _t1463
        end
        _t1461 = _t1462
    end
    prediction779 = _t1461
    if prediction779 == 13
        _t1476 = parse_uint32_type(parser)
        uint32_type793 = _t1476
        _t1477 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type793))
        _t1475 = _t1477
    else
        if prediction779 == 12
            _t1479 = parse_float32_type(parser)
            float32_type792 = _t1479
            _t1480 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type792))
            _t1478 = _t1480
        else
            if prediction779 == 11
                _t1482 = parse_int32_type(parser)
                int32_type791 = _t1482
                _t1483 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type791))
                _t1481 = _t1483
            else
                if prediction779 == 10
                    _t1485 = parse_boolean_type(parser)
                    boolean_type790 = _t1485
                    _t1486 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type790))
                    _t1484 = _t1486
                else
                    if prediction779 == 9
                        _t1488 = parse_decimal_type(parser)
                        decimal_type789 = _t1488
                        _t1489 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type789))
                        _t1487 = _t1489
                    else
                        if prediction779 == 8
                            _t1491 = parse_missing_type(parser)
                            missing_type788 = _t1491
                            _t1492 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type788))
                            _t1490 = _t1492
                        else
                            if prediction779 == 7
                                _t1494 = parse_datetime_type(parser)
                                datetime_type787 = _t1494
                                _t1495 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type787))
                                _t1493 = _t1495
                            else
                                if prediction779 == 6
                                    _t1497 = parse_date_type(parser)
                                    date_type786 = _t1497
                                    _t1498 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type786))
                                    _t1496 = _t1498
                                else
                                    if prediction779 == 5
                                        _t1500 = parse_int128_type(parser)
                                        int128_type785 = _t1500
                                        _t1501 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type785))
                                        _t1499 = _t1501
                                    else
                                        if prediction779 == 4
                                            _t1503 = parse_uint128_type(parser)
                                            uint128_type784 = _t1503
                                            _t1504 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type784))
                                            _t1502 = _t1504
                                        else
                                            if prediction779 == 3
                                                _t1506 = parse_float_type(parser)
                                                float_type783 = _t1506
                                                _t1507 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type783))
                                                _t1505 = _t1507
                                            else
                                                if prediction779 == 2
                                                    _t1509 = parse_int_type(parser)
                                                    int_type782 = _t1509
                                                    _t1510 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type782))
                                                    _t1508 = _t1510
                                                else
                                                    if prediction779 == 1
                                                        _t1512 = parse_string_type(parser)
                                                        string_type781 = _t1512
                                                        _t1513 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type781))
                                                        _t1511 = _t1513
                                                    else
                                                        if prediction779 == 0
                                                            _t1515 = parse_unspecified_type(parser)
                                                            unspecified_type780 = _t1515
                                                            _t1516 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type780))
                                                            _t1514 = _t1516
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1511 = _t1514
                                                    end
                                                    _t1508 = _t1511
                                                end
                                                _t1505 = _t1508
                                            end
                                            _t1502 = _t1505
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
    result795 = _t1475
    record_span!(parser, span_start794, "Type")
    return result795
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start796 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1517 = Proto.UnspecifiedType()
    result797 = _t1517
    record_span!(parser, span_start796, "UnspecifiedType")
    return result797
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start798 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1518 = Proto.StringType()
    result799 = _t1518
    record_span!(parser, span_start798, "StringType")
    return result799
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start800 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1519 = Proto.IntType()
    result801 = _t1519
    record_span!(parser, span_start800, "IntType")
    return result801
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start802 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1520 = Proto.FloatType()
    result803 = _t1520
    record_span!(parser, span_start802, "FloatType")
    return result803
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start804 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1521 = Proto.UInt128Type()
    result805 = _t1521
    record_span!(parser, span_start804, "UInt128Type")
    return result805
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start806 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1522 = Proto.Int128Type()
    result807 = _t1522
    record_span!(parser, span_start806, "Int128Type")
    return result807
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start808 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1523 = Proto.DateType()
    result809 = _t1523
    record_span!(parser, span_start808, "DateType")
    return result809
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start810 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1524 = Proto.DateTimeType()
    result811 = _t1524
    record_span!(parser, span_start810, "DateTimeType")
    return result811
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start812 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1525 = Proto.MissingType()
    result813 = _t1525
    record_span!(parser, span_start812, "MissingType")
    return result813
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start816 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int814 = consume_terminal!(parser, "INT")
    int_3815 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1526 = Proto.DecimalType(precision=Int32(int814), scale=Int32(int_3815))
    result817 = _t1526
    record_span!(parser, span_start816, "DecimalType")
    return result817
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start818 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1527 = Proto.BooleanType()
    result819 = _t1527
    record_span!(parser, span_start818, "BooleanType")
    return result819
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start820 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1528 = Proto.Int32Type()
    result821 = _t1528
    record_span!(parser, span_start820, "Int32Type")
    return result821
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start822 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1529 = Proto.Float32Type()
    result823 = _t1529
    record_span!(parser, span_start822, "Float32Type")
    return result823
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start824 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1530 = Proto.UInt32Type()
    result825 = _t1530
    record_span!(parser, span_start824, "UInt32Type")
    return result825
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs826 = Proto.Binding[]
    cond827 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond827
        _t1531 = parse_binding(parser)
        item828 = _t1531
        push!(xs826, item828)
        cond827 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings829 = xs826
    return bindings829
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start844 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1533 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1534 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1535 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1536 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1537 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1538 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1539 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1540 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1541 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1542 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1543 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1544 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1545 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1546 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1547 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1548 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1549 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1550 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1551 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1552 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1553 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1554 = 10
                                                                                            else
                                                                                                _t1554 = -1
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
    else
        _t1532 = -1
    end
    prediction830 = _t1532
    if prediction830 == 12
        _t1556 = parse_cast(parser)
        cast843 = _t1556
        _t1557 = Proto.Formula(formula_type=OneOf(:cast, cast843))
        _t1555 = _t1557
    else
        if prediction830 == 11
            _t1559 = parse_rel_atom(parser)
            rel_atom842 = _t1559
            _t1560 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom842))
            _t1558 = _t1560
        else
            if prediction830 == 10
                _t1562 = parse_primitive(parser)
                primitive841 = _t1562
                _t1563 = Proto.Formula(formula_type=OneOf(:primitive, primitive841))
                _t1561 = _t1563
            else
                if prediction830 == 9
                    _t1565 = parse_pragma(parser)
                    pragma840 = _t1565
                    _t1566 = Proto.Formula(formula_type=OneOf(:pragma, pragma840))
                    _t1564 = _t1566
                else
                    if prediction830 == 8
                        _t1568 = parse_atom(parser)
                        atom839 = _t1568
                        _t1569 = Proto.Formula(formula_type=OneOf(:atom, atom839))
                        _t1567 = _t1569
                    else
                        if prediction830 == 7
                            _t1571 = parse_ffi(parser)
                            ffi838 = _t1571
                            _t1572 = Proto.Formula(formula_type=OneOf(:ffi, ffi838))
                            _t1570 = _t1572
                        else
                            if prediction830 == 6
                                _t1574 = parse_not(parser)
                                not837 = _t1574
                                _t1575 = Proto.Formula(formula_type=OneOf(:not, not837))
                                _t1573 = _t1575
                            else
                                if prediction830 == 5
                                    _t1577 = parse_disjunction(parser)
                                    disjunction836 = _t1577
                                    _t1578 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction836))
                                    _t1576 = _t1578
                                else
                                    if prediction830 == 4
                                        _t1580 = parse_conjunction(parser)
                                        conjunction835 = _t1580
                                        _t1581 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction835))
                                        _t1579 = _t1581
                                    else
                                        if prediction830 == 3
                                            _t1583 = parse_reduce(parser)
                                            reduce834 = _t1583
                                            _t1584 = Proto.Formula(formula_type=OneOf(:reduce, reduce834))
                                            _t1582 = _t1584
                                        else
                                            if prediction830 == 2
                                                _t1586 = parse_exists(parser)
                                                exists833 = _t1586
                                                _t1587 = Proto.Formula(formula_type=OneOf(:exists, exists833))
                                                _t1585 = _t1587
                                            else
                                                if prediction830 == 1
                                                    _t1589 = parse_false(parser)
                                                    false832 = _t1589
                                                    _t1590 = Proto.Formula(formula_type=OneOf(:disjunction, false832))
                                                    _t1588 = _t1590
                                                else
                                                    if prediction830 == 0
                                                        _t1592 = parse_true(parser)
                                                        true831 = _t1592
                                                        _t1593 = Proto.Formula(formula_type=OneOf(:conjunction, true831))
                                                        _t1591 = _t1593
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1588 = _t1591
                                                end
                                                _t1585 = _t1588
                                            end
                                            _t1582 = _t1585
                                        end
                                        _t1579 = _t1582
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
    result845 = _t1555
    record_span!(parser, span_start844, "Formula")
    return result845
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start846 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1594 = Proto.Conjunction(args=Proto.Formula[])
    result847 = _t1594
    record_span!(parser, span_start846, "Conjunction")
    return result847
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start848 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1595 = Proto.Disjunction(args=Proto.Formula[])
    result849 = _t1595
    record_span!(parser, span_start848, "Disjunction")
    return result849
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start852 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1596 = parse_bindings(parser)
    bindings850 = _t1596
    _t1597 = parse_formula(parser)
    formula851 = _t1597
    consume_literal!(parser, ")")
    _t1598 = Proto.Abstraction(vars=vcat(bindings850[1], !isnothing(bindings850[2]) ? bindings850[2] : []), value=formula851)
    _t1599 = Proto.Exists(body=_t1598)
    result853 = _t1599
    record_span!(parser, span_start852, "Exists")
    return result853
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start857 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1600 = parse_abstraction(parser)
    abstraction854 = _t1600
    _t1601 = parse_abstraction(parser)
    abstraction_3855 = _t1601
    _t1602 = parse_terms(parser)
    terms856 = _t1602
    consume_literal!(parser, ")")
    _t1603 = Proto.Reduce(op=abstraction854, body=abstraction_3855, terms=terms856)
    result858 = _t1603
    record_span!(parser, span_start857, "Reduce")
    return result858
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs859 = Proto.Term[]
    cond860 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond860
        _t1604 = parse_term(parser)
        item861 = _t1604
        push!(xs859, item861)
        cond860 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms862 = xs859
    consume_literal!(parser, ")")
    return terms862
end

function parse_term(parser::ParserState)::Proto.Term
    span_start866 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1605 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1606 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1607 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1608 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1609 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1610 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1611 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1612 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1613 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1614 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1615 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1616 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1617 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1618 = 1
                                                        else
                                                            _t1618 = -1
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
                _t1607 = _t1608
            end
            _t1606 = _t1607
        end
        _t1605 = _t1606
    end
    prediction863 = _t1605
    if prediction863 == 1
        _t1620 = parse_value(parser)
        value865 = _t1620
        _t1621 = Proto.Term(term_type=OneOf(:constant, value865))
        _t1619 = _t1621
    else
        if prediction863 == 0
            _t1623 = parse_var(parser)
            var864 = _t1623
            _t1624 = Proto.Term(term_type=OneOf(:var, var864))
            _t1622 = _t1624
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1619 = _t1622
    end
    result867 = _t1619
    record_span!(parser, span_start866, "Term")
    return result867
end

function parse_var(parser::ParserState)::Proto.Var
    span_start869 = span_start(parser)
    symbol868 = consume_terminal!(parser, "SYMBOL")
    _t1625 = Proto.Var(name=symbol868)
    result870 = _t1625
    record_span!(parser, span_start869, "Var")
    return result870
end

function parse_value(parser::ParserState)::Proto.Value
    span_start884 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1626 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1627 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1628 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1630 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1631 = 0
                        else
                            _t1631 = -1
                        end
                        _t1630 = _t1631
                    end
                    _t1629 = _t1630
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1632 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1633 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1634 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1635 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1636 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1637 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1638 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1639 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1640 = 10
                                                    else
                                                        _t1640 = -1
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
                    _t1629 = _t1632
                end
                _t1628 = _t1629
            end
            _t1627 = _t1628
        end
        _t1626 = _t1627
    end
    prediction871 = _t1626
    if prediction871 == 12
        _t1642 = parse_boolean_value(parser)
        boolean_value883 = _t1642
        _t1643 = Proto.Value(value=OneOf(:boolean_value, boolean_value883))
        _t1641 = _t1643
    else
        if prediction871 == 11
            consume_literal!(parser, "missing")
            _t1645 = Proto.MissingValue()
            _t1646 = Proto.Value(value=OneOf(:missing_value, _t1645))
            _t1644 = _t1646
        else
            if prediction871 == 10
                formatted_decimal882 = consume_terminal!(parser, "DECIMAL")
                _t1648 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal882))
                _t1647 = _t1648
            else
                if prediction871 == 9
                    formatted_int128881 = consume_terminal!(parser, "INT128")
                    _t1650 = Proto.Value(value=OneOf(:int128_value, formatted_int128881))
                    _t1649 = _t1650
                else
                    if prediction871 == 8
                        formatted_uint128880 = consume_terminal!(parser, "UINT128")
                        _t1652 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128880))
                        _t1651 = _t1652
                    else
                        if prediction871 == 7
                            formatted_uint32879 = consume_terminal!(parser, "UINT32")
                            _t1654 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32879))
                            _t1653 = _t1654
                        else
                            if prediction871 == 6
                                formatted_float878 = consume_terminal!(parser, "FLOAT")
                                _t1656 = Proto.Value(value=OneOf(:float_value, formatted_float878))
                                _t1655 = _t1656
                            else
                                if prediction871 == 5
                                    formatted_float32877 = consume_terminal!(parser, "FLOAT32")
                                    _t1658 = Proto.Value(value=OneOf(:float32_value, formatted_float32877))
                                    _t1657 = _t1658
                                else
                                    if prediction871 == 4
                                        formatted_int876 = consume_terminal!(parser, "INT")
                                        _t1660 = Proto.Value(value=OneOf(:int_value, formatted_int876))
                                        _t1659 = _t1660
                                    else
                                        if prediction871 == 3
                                            formatted_int32875 = consume_terminal!(parser, "INT32")
                                            _t1662 = Proto.Value(value=OneOf(:int32_value, formatted_int32875))
                                            _t1661 = _t1662
                                        else
                                            if prediction871 == 2
                                                formatted_string874 = consume_terminal!(parser, "STRING")
                                                _t1664 = Proto.Value(value=OneOf(:string_value, formatted_string874))
                                                _t1663 = _t1664
                                            else
                                                if prediction871 == 1
                                                    _t1666 = parse_datetime(parser)
                                                    datetime873 = _t1666
                                                    _t1667 = Proto.Value(value=OneOf(:datetime_value, datetime873))
                                                    _t1665 = _t1667
                                                else
                                                    if prediction871 == 0
                                                        _t1669 = parse_date(parser)
                                                        date872 = _t1669
                                                        _t1670 = Proto.Value(value=OneOf(:date_value, date872))
                                                        _t1668 = _t1670
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1665 = _t1668
                                                end
                                                _t1663 = _t1665
                                            end
                                            _t1661 = _t1663
                                        end
                                        _t1659 = _t1661
                                    end
                                    _t1657 = _t1659
                                end
                                _t1655 = _t1657
                            end
                            _t1653 = _t1655
                        end
                        _t1651 = _t1653
                    end
                    _t1649 = _t1651
                end
                _t1647 = _t1649
            end
            _t1644 = _t1647
        end
        _t1641 = _t1644
    end
    result885 = _t1641
    record_span!(parser, span_start884, "Value")
    return result885
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start889 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int886 = consume_terminal!(parser, "INT")
    formatted_int_3887 = consume_terminal!(parser, "INT")
    formatted_int_4888 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1671 = Proto.DateValue(year=Int32(formatted_int886), month=Int32(formatted_int_3887), day=Int32(formatted_int_4888))
    result890 = _t1671
    record_span!(parser, span_start889, "DateValue")
    return result890
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start898 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int891 = consume_terminal!(parser, "INT")
    formatted_int_3892 = consume_terminal!(parser, "INT")
    formatted_int_4893 = consume_terminal!(parser, "INT")
    formatted_int_5894 = consume_terminal!(parser, "INT")
    formatted_int_6895 = consume_terminal!(parser, "INT")
    formatted_int_7896 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1672 = consume_terminal!(parser, "INT")
    else
        _t1672 = nothing
    end
    formatted_int_8897 = _t1672
    consume_literal!(parser, ")")
    _t1673 = Proto.DateTimeValue(year=Int32(formatted_int891), month=Int32(formatted_int_3892), day=Int32(formatted_int_4893), hour=Int32(formatted_int_5894), minute=Int32(formatted_int_6895), second=Int32(formatted_int_7896), microsecond=Int32((!isnothing(formatted_int_8897) ? formatted_int_8897 : 0)))
    result899 = _t1673
    record_span!(parser, span_start898, "DateTimeValue")
    return result899
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start904 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs900 = Proto.Formula[]
    cond901 = match_lookahead_literal(parser, "(", 0)
    while cond901
        _t1674 = parse_formula(parser)
        item902 = _t1674
        push!(xs900, item902)
        cond901 = match_lookahead_literal(parser, "(", 0)
    end
    formulas903 = xs900
    consume_literal!(parser, ")")
    _t1675 = Proto.Conjunction(args=formulas903)
    result905 = _t1675
    record_span!(parser, span_start904, "Conjunction")
    return result905
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start910 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs906 = Proto.Formula[]
    cond907 = match_lookahead_literal(parser, "(", 0)
    while cond907
        _t1676 = parse_formula(parser)
        item908 = _t1676
        push!(xs906, item908)
        cond907 = match_lookahead_literal(parser, "(", 0)
    end
    formulas909 = xs906
    consume_literal!(parser, ")")
    _t1677 = Proto.Disjunction(args=formulas909)
    result911 = _t1677
    record_span!(parser, span_start910, "Disjunction")
    return result911
end

function parse_not(parser::ParserState)::Proto.Not
    span_start913 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1678 = parse_formula(parser)
    formula912 = _t1678
    consume_literal!(parser, ")")
    _t1679 = Proto.Not(arg=formula912)
    result914 = _t1679
    record_span!(parser, span_start913, "Not")
    return result914
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start918 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1680 = parse_name(parser)
    name915 = _t1680
    _t1681 = parse_ffi_args(parser)
    ffi_args916 = _t1681
    _t1682 = parse_terms(parser)
    terms917 = _t1682
    consume_literal!(parser, ")")
    _t1683 = Proto.FFI(name=name915, args=ffi_args916, terms=terms917)
    result919 = _t1683
    record_span!(parser, span_start918, "FFI")
    return result919
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol920 = consume_terminal!(parser, "SYMBOL")
    return symbol920
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs921 = Proto.Abstraction[]
    cond922 = match_lookahead_literal(parser, "(", 0)
    while cond922
        _t1684 = parse_abstraction(parser)
        item923 = _t1684
        push!(xs921, item923)
        cond922 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions924 = xs921
    consume_literal!(parser, ")")
    return abstractions924
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start930 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1685 = parse_relation_id(parser)
    relation_id925 = _t1685
    xs926 = Proto.Term[]
    cond927 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond927
        _t1686 = parse_term(parser)
        item928 = _t1686
        push!(xs926, item928)
        cond927 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms929 = xs926
    consume_literal!(parser, ")")
    _t1687 = Proto.Atom(name=relation_id925, terms=terms929)
    result931 = _t1687
    record_span!(parser, span_start930, "Atom")
    return result931
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start937 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1688 = parse_name(parser)
    name932 = _t1688
    xs933 = Proto.Term[]
    cond934 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond934
        _t1689 = parse_term(parser)
        item935 = _t1689
        push!(xs933, item935)
        cond934 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms936 = xs933
    consume_literal!(parser, ")")
    _t1690 = Proto.Pragma(name=name932, terms=terms936)
    result938 = _t1690
    record_span!(parser, span_start937, "Pragma")
    return result938
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start954 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1692 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1693 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1694 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1695 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1696 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1697 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1698 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1699 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1700 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1701 = 7
                                            else
                                                _t1701 = -1
                                            end
                                            _t1700 = _t1701
                                        end
                                        _t1699 = _t1700
                                    end
                                    _t1698 = _t1699
                                end
                                _t1697 = _t1698
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
    prediction939 = _t1691
    if prediction939 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1703 = parse_name(parser)
        name949 = _t1703
        xs950 = Proto.RelTerm[]
        cond951 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond951
            _t1704 = parse_rel_term(parser)
            item952 = _t1704
            push!(xs950, item952)
            cond951 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms953 = xs950
        consume_literal!(parser, ")")
        _t1705 = Proto.Primitive(name=name949, terms=rel_terms953)
        _t1702 = _t1705
    else
        if prediction939 == 8
            _t1707 = parse_divide(parser)
            divide948 = _t1707
            _t1706 = divide948
        else
            if prediction939 == 7
                _t1709 = parse_multiply(parser)
                multiply947 = _t1709
                _t1708 = multiply947
            else
                if prediction939 == 6
                    _t1711 = parse_minus(parser)
                    minus946 = _t1711
                    _t1710 = minus946
                else
                    if prediction939 == 5
                        _t1713 = parse_add(parser)
                        add945 = _t1713
                        _t1712 = add945
                    else
                        if prediction939 == 4
                            _t1715 = parse_gt_eq(parser)
                            gt_eq944 = _t1715
                            _t1714 = gt_eq944
                        else
                            if prediction939 == 3
                                _t1717 = parse_gt(parser)
                                gt943 = _t1717
                                _t1716 = gt943
                            else
                                if prediction939 == 2
                                    _t1719 = parse_lt_eq(parser)
                                    lt_eq942 = _t1719
                                    _t1718 = lt_eq942
                                else
                                    if prediction939 == 1
                                        _t1721 = parse_lt(parser)
                                        lt941 = _t1721
                                        _t1720 = lt941
                                    else
                                        if prediction939 == 0
                                            _t1723 = parse_eq(parser)
                                            eq940 = _t1723
                                            _t1722 = eq940
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1720 = _t1722
                                    end
                                    _t1718 = _t1720
                                end
                                _t1716 = _t1718
                            end
                            _t1714 = _t1716
                        end
                        _t1712 = _t1714
                    end
                    _t1710 = _t1712
                end
                _t1708 = _t1710
            end
            _t1706 = _t1708
        end
        _t1702 = _t1706
    end
    result955 = _t1702
    record_span!(parser, span_start954, "Primitive")
    return result955
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start958 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1724 = parse_term(parser)
    term956 = _t1724
    _t1725 = parse_term(parser)
    term_3957 = _t1725
    consume_literal!(parser, ")")
    _t1726 = Proto.RelTerm(rel_term_type=OneOf(:term, term956))
    _t1727 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3957))
    _t1728 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1726, _t1727])
    result959 = _t1728
    record_span!(parser, span_start958, "Primitive")
    return result959
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start962 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1729 = parse_term(parser)
    term960 = _t1729
    _t1730 = parse_term(parser)
    term_3961 = _t1730
    consume_literal!(parser, ")")
    _t1731 = Proto.RelTerm(rel_term_type=OneOf(:term, term960))
    _t1732 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3961))
    _t1733 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1731, _t1732])
    result963 = _t1733
    record_span!(parser, span_start962, "Primitive")
    return result963
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start966 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1734 = parse_term(parser)
    term964 = _t1734
    _t1735 = parse_term(parser)
    term_3965 = _t1735
    consume_literal!(parser, ")")
    _t1736 = Proto.RelTerm(rel_term_type=OneOf(:term, term964))
    _t1737 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3965))
    _t1738 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1736, _t1737])
    result967 = _t1738
    record_span!(parser, span_start966, "Primitive")
    return result967
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start970 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1739 = parse_term(parser)
    term968 = _t1739
    _t1740 = parse_term(parser)
    term_3969 = _t1740
    consume_literal!(parser, ")")
    _t1741 = Proto.RelTerm(rel_term_type=OneOf(:term, term968))
    _t1742 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3969))
    _t1743 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1741, _t1742])
    result971 = _t1743
    record_span!(parser, span_start970, "Primitive")
    return result971
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1744 = parse_term(parser)
    term972 = _t1744
    _t1745 = parse_term(parser)
    term_3973 = _t1745
    consume_literal!(parser, ")")
    _t1746 = Proto.RelTerm(rel_term_type=OneOf(:term, term972))
    _t1747 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3973))
    _t1748 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1746, _t1747])
    result975 = _t1748
    record_span!(parser, span_start974, "Primitive")
    return result975
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start979 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1749 = parse_term(parser)
    term976 = _t1749
    _t1750 = parse_term(parser)
    term_3977 = _t1750
    _t1751 = parse_term(parser)
    term_4978 = _t1751
    consume_literal!(parser, ")")
    _t1752 = Proto.RelTerm(rel_term_type=OneOf(:term, term976))
    _t1753 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3977))
    _t1754 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4978))
    _t1755 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1752, _t1753, _t1754])
    result980 = _t1755
    record_span!(parser, span_start979, "Primitive")
    return result980
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start984 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1756 = parse_term(parser)
    term981 = _t1756
    _t1757 = parse_term(parser)
    term_3982 = _t1757
    _t1758 = parse_term(parser)
    term_4983 = _t1758
    consume_literal!(parser, ")")
    _t1759 = Proto.RelTerm(rel_term_type=OneOf(:term, term981))
    _t1760 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3982))
    _t1761 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4983))
    _t1762 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1759, _t1760, _t1761])
    result985 = _t1762
    record_span!(parser, span_start984, "Primitive")
    return result985
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start989 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1763 = parse_term(parser)
    term986 = _t1763
    _t1764 = parse_term(parser)
    term_3987 = _t1764
    _t1765 = parse_term(parser)
    term_4988 = _t1765
    consume_literal!(parser, ")")
    _t1766 = Proto.RelTerm(rel_term_type=OneOf(:term, term986))
    _t1767 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3987))
    _t1768 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4988))
    _t1769 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1766, _t1767, _t1768])
    result990 = _t1769
    record_span!(parser, span_start989, "Primitive")
    return result990
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start994 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1770 = parse_term(parser)
    term991 = _t1770
    _t1771 = parse_term(parser)
    term_3992 = _t1771
    _t1772 = parse_term(parser)
    term_4993 = _t1772
    consume_literal!(parser, ")")
    _t1773 = Proto.RelTerm(rel_term_type=OneOf(:term, term991))
    _t1774 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3992))
    _t1775 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4993))
    _t1776 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1773, _t1774, _t1775])
    result995 = _t1776
    record_span!(parser, span_start994, "Primitive")
    return result995
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start999 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1777 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1778 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1779 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1780 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1781 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1782 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1783 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1784 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1785 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1786 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1787 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1788 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1789 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1790 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1791 = 1
                                                            else
                                                                _t1791 = -1
                                                            end
                                                            _t1790 = _t1791
                                                        end
                                                        _t1789 = _t1790
                                                    end
                                                    _t1788 = _t1789
                                                end
                                                _t1787 = _t1788
                                            end
                                            _t1786 = _t1787
                                        end
                                        _t1785 = _t1786
                                    end
                                    _t1784 = _t1785
                                end
                                _t1783 = _t1784
                            end
                            _t1782 = _t1783
                        end
                        _t1781 = _t1782
                    end
                    _t1780 = _t1781
                end
                _t1779 = _t1780
            end
            _t1778 = _t1779
        end
        _t1777 = _t1778
    end
    prediction996 = _t1777
    if prediction996 == 1
        _t1793 = parse_term(parser)
        term998 = _t1793
        _t1794 = Proto.RelTerm(rel_term_type=OneOf(:term, term998))
        _t1792 = _t1794
    else
        if prediction996 == 0
            _t1796 = parse_specialized_value(parser)
            specialized_value997 = _t1796
            _t1797 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value997))
            _t1795 = _t1797
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1792 = _t1795
    end
    result1000 = _t1792
    record_span!(parser, span_start999, "RelTerm")
    return result1000
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1002 = span_start(parser)
    consume_literal!(parser, "#")
    _t1798 = parse_raw_value(parser)
    raw_value1001 = _t1798
    result1003 = raw_value1001
    record_span!(parser, span_start1002, "Value")
    return result1003
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1009 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1799 = parse_name(parser)
    name1004 = _t1799
    xs1005 = Proto.RelTerm[]
    cond1006 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1006
        _t1800 = parse_rel_term(parser)
        item1007 = _t1800
        push!(xs1005, item1007)
        cond1006 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1008 = xs1005
    consume_literal!(parser, ")")
    _t1801 = Proto.RelAtom(name=name1004, terms=rel_terms1008)
    result1010 = _t1801
    record_span!(parser, span_start1009, "RelAtom")
    return result1010
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1013 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1802 = parse_term(parser)
    term1011 = _t1802
    _t1803 = parse_term(parser)
    term_31012 = _t1803
    consume_literal!(parser, ")")
    _t1804 = Proto.Cast(input=term1011, result=term_31012)
    result1014 = _t1804
    record_span!(parser, span_start1013, "Cast")
    return result1014
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1015 = Proto.Attribute[]
    cond1016 = match_lookahead_literal(parser, "(", 0)
    while cond1016
        _t1805 = parse_attribute(parser)
        item1017 = _t1805
        push!(xs1015, item1017)
        cond1016 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1018 = xs1015
    consume_literal!(parser, ")")
    return attributes1018
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1024 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1806 = parse_name(parser)
    name1019 = _t1806
    xs1020 = Proto.Value[]
    cond1021 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1021
        _t1807 = parse_raw_value(parser)
        item1022 = _t1807
        push!(xs1020, item1022)
        cond1021 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1023 = xs1020
    consume_literal!(parser, ")")
    _t1808 = Proto.Attribute(name=name1019, args=raw_values1023)
    result1025 = _t1808
    record_span!(parser, span_start1024, "Attribute")
    return result1025
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1032 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1026 = Proto.RelationId[]
    cond1027 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1027
        _t1809 = parse_relation_id(parser)
        item1028 = _t1809
        push!(xs1026, item1028)
        cond1027 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1029 = xs1026
    _t1810 = parse_script(parser)
    script1030 = _t1810
    if match_lookahead_literal(parser, "(", 0)
        _t1812 = parse_attrs(parser)
        _t1811 = _t1812
    else
        _t1811 = nothing
    end
    attrs1031 = _t1811
    consume_literal!(parser, ")")
    _t1813 = Proto.Algorithm(var"#global"=relation_ids1029, body=script1030, attrs=(!isnothing(attrs1031) ? attrs1031 : Proto.Attribute[]))
    result1033 = _t1813
    record_span!(parser, span_start1032, "Algorithm")
    return result1033
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1038 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1034 = Proto.Construct[]
    cond1035 = match_lookahead_literal(parser, "(", 0)
    while cond1035
        _t1814 = parse_construct(parser)
        item1036 = _t1814
        push!(xs1034, item1036)
        cond1035 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1037 = xs1034
    consume_literal!(parser, ")")
    _t1815 = Proto.Script(constructs=constructs1037)
    result1039 = _t1815
    record_span!(parser, span_start1038, "Script")
    return result1039
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1043 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1817 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1818 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1819 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1820 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1821 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1822 = 1
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
        end
        _t1816 = _t1817
    else
        _t1816 = -1
    end
    prediction1040 = _t1816
    if prediction1040 == 1
        _t1824 = parse_instruction(parser)
        instruction1042 = _t1824
        _t1825 = Proto.Construct(construct_type=OneOf(:instruction, instruction1042))
        _t1823 = _t1825
    else
        if prediction1040 == 0
            _t1827 = parse_loop(parser)
            loop1041 = _t1827
            _t1828 = Proto.Construct(construct_type=OneOf(:loop, loop1041))
            _t1826 = _t1828
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1823 = _t1826
    end
    result1044 = _t1823
    record_span!(parser, span_start1043, "Construct")
    return result1044
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1048 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1829 = parse_init(parser)
    init1045 = _t1829
    _t1830 = parse_script(parser)
    script1046 = _t1830
    if match_lookahead_literal(parser, "(", 0)
        _t1832 = parse_attrs(parser)
        _t1831 = _t1832
    else
        _t1831 = nothing
    end
    attrs1047 = _t1831
    consume_literal!(parser, ")")
    _t1833 = Proto.Loop(init=init1045, body=script1046, attrs=(!isnothing(attrs1047) ? attrs1047 : Proto.Attribute[]))
    result1049 = _t1833
    record_span!(parser, span_start1048, "Loop")
    return result1049
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1050 = Proto.Instruction[]
    cond1051 = match_lookahead_literal(parser, "(", 0)
    while cond1051
        _t1834 = parse_instruction(parser)
        item1052 = _t1834
        push!(xs1050, item1052)
        cond1051 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1053 = xs1050
    consume_literal!(parser, ")")
    return instructions1053
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1060 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1836 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1837 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1838 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1839 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1840 = 0
                        else
                            _t1840 = -1
                        end
                        _t1839 = _t1840
                    end
                    _t1838 = _t1839
                end
                _t1837 = _t1838
            end
            _t1836 = _t1837
        end
        _t1835 = _t1836
    else
        _t1835 = -1
    end
    prediction1054 = _t1835
    if prediction1054 == 4
        _t1842 = parse_monus_def(parser)
        monus_def1059 = _t1842
        _t1843 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1059))
        _t1841 = _t1843
    else
        if prediction1054 == 3
            _t1845 = parse_monoid_def(parser)
            monoid_def1058 = _t1845
            _t1846 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1058))
            _t1844 = _t1846
        else
            if prediction1054 == 2
                _t1848 = parse_break(parser)
                break1057 = _t1848
                _t1849 = Proto.Instruction(instr_type=OneOf(:var"#break", break1057))
                _t1847 = _t1849
            else
                if prediction1054 == 1
                    _t1851 = parse_upsert(parser)
                    upsert1056 = _t1851
                    _t1852 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1056))
                    _t1850 = _t1852
                else
                    if prediction1054 == 0
                        _t1854 = parse_assign(parser)
                        assign1055 = _t1854
                        _t1855 = Proto.Instruction(instr_type=OneOf(:assign, assign1055))
                        _t1853 = _t1855
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1850 = _t1853
                end
                _t1847 = _t1850
            end
            _t1844 = _t1847
        end
        _t1841 = _t1844
    end
    result1061 = _t1841
    record_span!(parser, span_start1060, "Instruction")
    return result1061
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1065 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1856 = parse_relation_id(parser)
    relation_id1062 = _t1856
    _t1857 = parse_abstraction(parser)
    abstraction1063 = _t1857
    if match_lookahead_literal(parser, "(", 0)
        _t1859 = parse_attrs(parser)
        _t1858 = _t1859
    else
        _t1858 = nothing
    end
    attrs1064 = _t1858
    consume_literal!(parser, ")")
    _t1860 = Proto.Assign(name=relation_id1062, body=abstraction1063, attrs=(!isnothing(attrs1064) ? attrs1064 : Proto.Attribute[]))
    result1066 = _t1860
    record_span!(parser, span_start1065, "Assign")
    return result1066
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1070 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1861 = parse_relation_id(parser)
    relation_id1067 = _t1861
    _t1862 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1068 = _t1862
    if match_lookahead_literal(parser, "(", 0)
        _t1864 = parse_attrs(parser)
        _t1863 = _t1864
    else
        _t1863 = nothing
    end
    attrs1069 = _t1863
    consume_literal!(parser, ")")
    _t1865 = Proto.Upsert(name=relation_id1067, body=abstraction_with_arity1068[1], attrs=(!isnothing(attrs1069) ? attrs1069 : Proto.Attribute[]), value_arity=abstraction_with_arity1068[2])
    result1071 = _t1865
    record_span!(parser, span_start1070, "Upsert")
    return result1071
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1866 = parse_bindings(parser)
    bindings1072 = _t1866
    _t1867 = parse_formula(parser)
    formula1073 = _t1867
    consume_literal!(parser, ")")
    _t1868 = Proto.Abstraction(vars=vcat(bindings1072[1], !isnothing(bindings1072[2]) ? bindings1072[2] : []), value=formula1073)
    return (_t1868, length(bindings1072[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1077 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1869 = parse_relation_id(parser)
    relation_id1074 = _t1869
    _t1870 = parse_abstraction(parser)
    abstraction1075 = _t1870
    if match_lookahead_literal(parser, "(", 0)
        _t1872 = parse_attrs(parser)
        _t1871 = _t1872
    else
        _t1871 = nothing
    end
    attrs1076 = _t1871
    consume_literal!(parser, ")")
    _t1873 = Proto.Break(name=relation_id1074, body=abstraction1075, attrs=(!isnothing(attrs1076) ? attrs1076 : Proto.Attribute[]))
    result1078 = _t1873
    record_span!(parser, span_start1077, "Break")
    return result1078
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1083 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1874 = parse_monoid(parser)
    monoid1079 = _t1874
    _t1875 = parse_relation_id(parser)
    relation_id1080 = _t1875
    _t1876 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1081 = _t1876
    if match_lookahead_literal(parser, "(", 0)
        _t1878 = parse_attrs(parser)
        _t1877 = _t1878
    else
        _t1877 = nothing
    end
    attrs1082 = _t1877
    consume_literal!(parser, ")")
    _t1879 = Proto.MonoidDef(monoid=monoid1079, name=relation_id1080, body=abstraction_with_arity1081[1], attrs=(!isnothing(attrs1082) ? attrs1082 : Proto.Attribute[]), value_arity=abstraction_with_arity1081[2])
    result1084 = _t1879
    record_span!(parser, span_start1083, "MonoidDef")
    return result1084
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1090 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1881 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1882 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1883 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1884 = 2
                    else
                        _t1884 = -1
                    end
                    _t1883 = _t1884
                end
                _t1882 = _t1883
            end
            _t1881 = _t1882
        end
        _t1880 = _t1881
    else
        _t1880 = -1
    end
    prediction1085 = _t1880
    if prediction1085 == 3
        _t1886 = parse_sum_monoid(parser)
        sum_monoid1089 = _t1886
        _t1887 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1089))
        _t1885 = _t1887
    else
        if prediction1085 == 2
            _t1889 = parse_max_monoid(parser)
            max_monoid1088 = _t1889
            _t1890 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1088))
            _t1888 = _t1890
        else
            if prediction1085 == 1
                _t1892 = parse_min_monoid(parser)
                min_monoid1087 = _t1892
                _t1893 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1087))
                _t1891 = _t1893
            else
                if prediction1085 == 0
                    _t1895 = parse_or_monoid(parser)
                    or_monoid1086 = _t1895
                    _t1896 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1086))
                    _t1894 = _t1896
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1891 = _t1894
            end
            _t1888 = _t1891
        end
        _t1885 = _t1888
    end
    result1091 = _t1885
    record_span!(parser, span_start1090, "Monoid")
    return result1091
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1092 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1897 = Proto.OrMonoid()
    result1093 = _t1897
    record_span!(parser, span_start1092, "OrMonoid")
    return result1093
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1095 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1898 = parse_type(parser)
    type1094 = _t1898
    consume_literal!(parser, ")")
    _t1899 = Proto.MinMonoid(var"#type"=type1094)
    result1096 = _t1899
    record_span!(parser, span_start1095, "MinMonoid")
    return result1096
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1098 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1900 = parse_type(parser)
    type1097 = _t1900
    consume_literal!(parser, ")")
    _t1901 = Proto.MaxMonoid(var"#type"=type1097)
    result1099 = _t1901
    record_span!(parser, span_start1098, "MaxMonoid")
    return result1099
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1101 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1902 = parse_type(parser)
    type1100 = _t1902
    consume_literal!(parser, ")")
    _t1903 = Proto.SumMonoid(var"#type"=type1100)
    result1102 = _t1903
    record_span!(parser, span_start1101, "SumMonoid")
    return result1102
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1107 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1904 = parse_monoid(parser)
    monoid1103 = _t1904
    _t1905 = parse_relation_id(parser)
    relation_id1104 = _t1905
    _t1906 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1105 = _t1906
    if match_lookahead_literal(parser, "(", 0)
        _t1908 = parse_attrs(parser)
        _t1907 = _t1908
    else
        _t1907 = nothing
    end
    attrs1106 = _t1907
    consume_literal!(parser, ")")
    _t1909 = Proto.MonusDef(monoid=monoid1103, name=relation_id1104, body=abstraction_with_arity1105[1], attrs=(!isnothing(attrs1106) ? attrs1106 : Proto.Attribute[]), value_arity=abstraction_with_arity1105[2])
    result1108 = _t1909
    record_span!(parser, span_start1107, "MonusDef")
    return result1108
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1113 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1910 = parse_relation_id(parser)
    relation_id1109 = _t1910
    _t1911 = parse_abstraction(parser)
    abstraction1110 = _t1911
    _t1912 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1111 = _t1912
    _t1913 = parse_functional_dependency_values(parser)
    functional_dependency_values1112 = _t1913
    consume_literal!(parser, ")")
    _t1914 = Proto.FunctionalDependency(guard=abstraction1110, keys=functional_dependency_keys1111, values=functional_dependency_values1112)
    _t1915 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1914), name=relation_id1109)
    result1114 = _t1915
    record_span!(parser, span_start1113, "Constraint")
    return result1114
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1115 = Proto.Var[]
    cond1116 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1116
        _t1916 = parse_var(parser)
        item1117 = _t1916
        push!(xs1115, item1117)
        cond1116 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1118 = xs1115
    consume_literal!(parser, ")")
    return vars1118
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1119 = Proto.Var[]
    cond1120 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1120
        _t1917 = parse_var(parser)
        item1121 = _t1917
        push!(xs1119, item1121)
        cond1120 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1122 = xs1119
    consume_literal!(parser, ")")
    return vars1122
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1128 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1919 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1920 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1921 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1922 = 1
                    else
                        _t1922 = -1
                    end
                    _t1921 = _t1922
                end
                _t1920 = _t1921
            end
            _t1919 = _t1920
        end
        _t1918 = _t1919
    else
        _t1918 = -1
    end
    prediction1123 = _t1918
    if prediction1123 == 3
        _t1924 = parse_iceberg_data(parser)
        iceberg_data1127 = _t1924
        _t1925 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1127))
        _t1923 = _t1925
    else
        if prediction1123 == 2
            _t1927 = parse_csv_data(parser)
            csv_data1126 = _t1927
            _t1928 = Proto.Data(data_type=OneOf(:csv_data, csv_data1126))
            _t1926 = _t1928
        else
            if prediction1123 == 1
                _t1930 = parse_betree_relation(parser)
                betree_relation1125 = _t1930
                _t1931 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1125))
                _t1929 = _t1931
            else
                if prediction1123 == 0
                    _t1933 = parse_edb(parser)
                    edb1124 = _t1933
                    _t1934 = Proto.Data(data_type=OneOf(:edb, edb1124))
                    _t1932 = _t1934
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1929 = _t1932
            end
            _t1926 = _t1929
        end
        _t1923 = _t1926
    end
    result1129 = _t1923
    record_span!(parser, span_start1128, "Data")
    return result1129
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1133 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1935 = parse_relation_id(parser)
    relation_id1130 = _t1935
    _t1936 = parse_edb_path(parser)
    edb_path1131 = _t1936
    _t1937 = parse_edb_types(parser)
    edb_types1132 = _t1937
    consume_literal!(parser, ")")
    _t1938 = Proto.EDB(target_id=relation_id1130, path=edb_path1131, types=edb_types1132)
    result1134 = _t1938
    record_span!(parser, span_start1133, "EDB")
    return result1134
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1135 = String[]
    cond1136 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1136
        item1137 = consume_terminal!(parser, "STRING")
        push!(xs1135, item1137)
        cond1136 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1138 = xs1135
    consume_literal!(parser, "]")
    return strings1138
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1139 = Proto.var"#Type"[]
    cond1140 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1140
        _t1939 = parse_type(parser)
        item1141 = _t1939
        push!(xs1139, item1141)
        cond1140 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1142 = xs1139
    consume_literal!(parser, "]")
    return types1142
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1145 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1940 = parse_relation_id(parser)
    relation_id1143 = _t1940
    _t1941 = parse_betree_info(parser)
    betree_info1144 = _t1941
    consume_literal!(parser, ")")
    _t1942 = Proto.BeTreeRelation(name=relation_id1143, relation_info=betree_info1144)
    result1146 = _t1942
    record_span!(parser, span_start1145, "BeTreeRelation")
    return result1146
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1150 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1943 = parse_betree_info_key_types(parser)
    betree_info_key_types1147 = _t1943
    _t1944 = parse_betree_info_value_types(parser)
    betree_info_value_types1148 = _t1944
    _t1945 = parse_config_dict(parser)
    config_dict1149 = _t1945
    consume_literal!(parser, ")")
    _t1946 = construct_betree_info(parser, betree_info_key_types1147, betree_info_value_types1148, config_dict1149)
    result1151 = _t1946
    record_span!(parser, span_start1150, "BeTreeInfo")
    return result1151
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1152 = Proto.var"#Type"[]
    cond1153 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1153
        _t1947 = parse_type(parser)
        item1154 = _t1947
        push!(xs1152, item1154)
        cond1153 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1155 = xs1152
    consume_literal!(parser, ")")
    return types1155
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1156 = Proto.var"#Type"[]
    cond1157 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1157
        _t1948 = parse_type(parser)
        item1158 = _t1948
        push!(xs1156, item1158)
        cond1157 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1159 = xs1156
    consume_literal!(parser, ")")
    return types1159
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1164 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1949 = parse_csvlocator(parser)
    csvlocator1160 = _t1949
    _t1950 = parse_csv_config(parser)
    csv_config1161 = _t1950
    _t1951 = parse_gnf_columns(parser)
    gnf_columns1162 = _t1951
    _t1952 = parse_csv_asof(parser)
    csv_asof1163 = _t1952
    consume_literal!(parser, ")")
    _t1953 = Proto.CSVData(locator=csvlocator1160, config=csv_config1161, columns=gnf_columns1162, asof=csv_asof1163)
    result1165 = _t1953
    record_span!(parser, span_start1164, "CSVData")
    return result1165
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1168 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1955 = parse_csv_locator_paths(parser)
        _t1954 = _t1955
    else
        _t1954 = nothing
    end
    csv_locator_paths1166 = _t1954
    if match_lookahead_literal(parser, "(", 0)
        _t1957 = parse_csv_locator_inline_data(parser)
        _t1956 = _t1957
    else
        _t1956 = nothing
    end
    csv_locator_inline_data1167 = _t1956
    consume_literal!(parser, ")")
    _t1958 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1166) ? csv_locator_paths1166 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1167) ? csv_locator_inline_data1167 : "")))
    result1169 = _t1958
    record_span!(parser, span_start1168, "CSVLocator")
    return result1169
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1170 = String[]
    cond1171 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1171
        item1172 = consume_terminal!(parser, "STRING")
        push!(xs1170, item1172)
        cond1171 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1173 = xs1170
    consume_literal!(parser, ")")
    return strings1173
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1174 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1174
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1176 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1959 = parse_config_dict(parser)
    config_dict1175 = _t1959
    consume_literal!(parser, ")")
    _t1960 = construct_csv_config(parser, config_dict1175)
    result1177 = _t1960
    record_span!(parser, span_start1176, "CSVConfig")
    return result1177
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1178 = Proto.GNFColumn[]
    cond1179 = match_lookahead_literal(parser, "(", 0)
    while cond1179
        _t1961 = parse_gnf_column(parser)
        item1180 = _t1961
        push!(xs1178, item1180)
        cond1179 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1181 = xs1178
    consume_literal!(parser, ")")
    return gnf_columns1181
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1188 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1962 = parse_gnf_column_path(parser)
    gnf_column_path1182 = _t1962
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1964 = parse_relation_id(parser)
        _t1963 = _t1964
    else
        _t1963 = nothing
    end
    relation_id1183 = _t1963
    consume_literal!(parser, "[")
    xs1184 = Proto.var"#Type"[]
    cond1185 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1185
        _t1965 = parse_type(parser)
        item1186 = _t1965
        push!(xs1184, item1186)
        cond1185 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1187 = xs1184
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1966 = Proto.GNFColumn(column_path=gnf_column_path1182, target_id=relation_id1183, types=types1187)
    result1189 = _t1966
    record_span!(parser, span_start1188, "GNFColumn")
    return result1189
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1967 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1968 = 0
        else
            _t1968 = -1
        end
        _t1967 = _t1968
    end
    prediction1190 = _t1967
    if prediction1190 == 1
        consume_literal!(parser, "[")
        xs1192 = String[]
        cond1193 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1193
            item1194 = consume_terminal!(parser, "STRING")
            push!(xs1192, item1194)
            cond1193 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1195 = xs1192
        consume_literal!(parser, "]")
        _t1969 = strings1195
    else
        if prediction1190 == 0
            string1191 = consume_terminal!(parser, "STRING")
            _t1970 = String[string1191]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1969 = _t1970
    end
    return _t1969
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1196 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1196
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1203 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1971 = parse_iceberg_locator(parser)
    iceberg_locator1197 = _t1971
    _t1972 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1198 = _t1972
    _t1973 = parse_gnf_columns(parser)
    gnf_columns1199 = _t1973
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1975 = parse_iceberg_from_snapshot(parser)
        _t1974 = _t1975
    else
        _t1974 = nothing
    end
    iceberg_from_snapshot1200 = _t1974
    if match_lookahead_literal(parser, "(", 0)
        _t1977 = parse_iceberg_to_snapshot(parser)
        _t1976 = _t1977
    else
        _t1976 = nothing
    end
    iceberg_to_snapshot1201 = _t1976
    _t1978 = parse_boolean_value(parser)
    boolean_value1202 = _t1978
    consume_literal!(parser, ")")
    _t1979 = construct_iceberg_data(parser, iceberg_locator1197, iceberg_catalog_config1198, gnf_columns1199, iceberg_from_snapshot1200, iceberg_to_snapshot1201, boolean_value1202)
    result1204 = _t1979
    record_span!(parser, span_start1203, "IcebergData")
    return result1204
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1208 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t1980 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1205 = _t1980
    _t1981 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1206 = _t1981
    _t1982 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1207 = _t1982
    consume_literal!(parser, ")")
    _t1983 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1205, namespace=iceberg_locator_namespace1206, warehouse=iceberg_locator_warehouse1207)
    result1209 = _t1983
    record_span!(parser, span_start1208, "IcebergLocator")
    return result1209
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1210 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1210
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1211 = String[]
    cond1212 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1212
        item1213 = consume_terminal!(parser, "STRING")
        push!(xs1211, item1213)
        cond1212 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1214 = xs1211
    consume_literal!(parser, ")")
    return strings1214
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1215 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1215
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1220 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t1984 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1216 = _t1984
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1986 = parse_iceberg_catalog_config_scope(parser)
        _t1985 = _t1986
    else
        _t1985 = nothing
    end
    iceberg_catalog_config_scope1217 = _t1985
    _t1987 = parse_iceberg_properties(parser)
    iceberg_properties1218 = _t1987
    _t1988 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1219 = _t1988
    consume_literal!(parser, ")")
    _t1989 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1216, iceberg_catalog_config_scope1217, iceberg_properties1218, iceberg_auth_properties1219)
    result1221 = _t1989
    record_span!(parser, span_start1220, "IcebergCatalogConfig")
    return result1221
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1222 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1222
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1223 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1223
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1224 = Tuple{String, String}[]
    cond1225 = match_lookahead_literal(parser, "(", 0)
    while cond1225
        _t1990 = parse_iceberg_property_entry(parser)
        item1226 = _t1990
        push!(xs1224, item1226)
        cond1225 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1227 = xs1224
    consume_literal!(parser, ")")
    return iceberg_property_entrys1227
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1228 = consume_terminal!(parser, "STRING")
    string_31229 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1228, string_31229,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1230 = Tuple{String, String}[]
    cond1231 = match_lookahead_literal(parser, "(", 0)
    while cond1231
        _t1991 = parse_iceberg_masked_property_entry(parser)
        item1232 = _t1991
        push!(xs1230, item1232)
        cond1231 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1233 = xs1230
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1233
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1234 = consume_terminal!(parser, "STRING")
    string_31235 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1234, string_31235,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1236 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1236
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1237 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1237
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1239 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1992 = parse_fragment_id(parser)
    fragment_id1238 = _t1992
    consume_literal!(parser, ")")
    _t1993 = Proto.Undefine(fragment_id=fragment_id1238)
    result1240 = _t1993
    record_span!(parser, span_start1239, "Undefine")
    return result1240
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1245 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1241 = Proto.RelationId[]
    cond1242 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1242
        _t1994 = parse_relation_id(parser)
        item1243 = _t1994
        push!(xs1241, item1243)
        cond1242 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1244 = xs1241
    consume_literal!(parser, ")")
    _t1995 = Proto.Context(relations=relation_ids1244)
    result1246 = _t1995
    record_span!(parser, span_start1245, "Context")
    return result1246
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1252 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t1996 = parse_edb_path(parser)
    edb_path1247 = _t1996
    xs1248 = Proto.SnapshotMapping[]
    cond1249 = match_lookahead_literal(parser, "[", 0)
    while cond1249
        _t1997 = parse_snapshot_mapping(parser)
        item1250 = _t1997
        push!(xs1248, item1250)
        cond1249 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1251 = xs1248
    consume_literal!(parser, ")")
    _t1998 = Proto.Snapshot(mappings=snapshot_mappings1251, prefix=edb_path1247)
    result1253 = _t1998
    record_span!(parser, span_start1252, "Snapshot")
    return result1253
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1256 = span_start(parser)
    _t1999 = parse_edb_path(parser)
    edb_path1254 = _t1999
    _t2000 = parse_relation_id(parser)
    relation_id1255 = _t2000
    _t2001 = Proto.SnapshotMapping(destination_path=edb_path1254, source_relation=relation_id1255)
    result1257 = _t2001
    record_span!(parser, span_start1256, "SnapshotMapping")
    return result1257
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1258 = Proto.Read[]
    cond1259 = match_lookahead_literal(parser, "(", 0)
    while cond1259
        _t2002 = parse_read(parser)
        item1260 = _t2002
        push!(xs1258, item1260)
        cond1259 = match_lookahead_literal(parser, "(", 0)
    end
    reads1261 = xs1258
    consume_literal!(parser, ")")
    return reads1261
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1268 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2004 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2005 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2006 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2007 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2008 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2009 = 3
                            else
                                _t2009 = -1
                            end
                            _t2008 = _t2009
                        end
                        _t2007 = _t2008
                    end
                    _t2006 = _t2007
                end
                _t2005 = _t2006
            end
            _t2004 = _t2005
        end
        _t2003 = _t2004
    else
        _t2003 = -1
    end
    prediction1262 = _t2003
    if prediction1262 == 4
        _t2011 = parse_export(parser)
        export1267 = _t2011
        _t2012 = Proto.Read(read_type=OneOf(:var"#export", export1267))
        _t2010 = _t2012
    else
        if prediction1262 == 3
            _t2014 = parse_abort(parser)
            abort1266 = _t2014
            _t2015 = Proto.Read(read_type=OneOf(:abort, abort1266))
            _t2013 = _t2015
        else
            if prediction1262 == 2
                _t2017 = parse_what_if(parser)
                what_if1265 = _t2017
                _t2018 = Proto.Read(read_type=OneOf(:what_if, what_if1265))
                _t2016 = _t2018
            else
                if prediction1262 == 1
                    _t2020 = parse_output(parser)
                    output1264 = _t2020
                    _t2021 = Proto.Read(read_type=OneOf(:output, output1264))
                    _t2019 = _t2021
                else
                    if prediction1262 == 0
                        _t2023 = parse_demand(parser)
                        demand1263 = _t2023
                        _t2024 = Proto.Read(read_type=OneOf(:demand, demand1263))
                        _t2022 = _t2024
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2019 = _t2022
                end
                _t2016 = _t2019
            end
            _t2013 = _t2016
        end
        _t2010 = _t2013
    end
    result1269 = _t2010
    record_span!(parser, span_start1268, "Read")
    return result1269
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1271 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2025 = parse_relation_id(parser)
    relation_id1270 = _t2025
    consume_literal!(parser, ")")
    _t2026 = Proto.Demand(relation_id=relation_id1270)
    result1272 = _t2026
    record_span!(parser, span_start1271, "Demand")
    return result1272
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1275 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2027 = parse_name(parser)
    name1273 = _t2027
    _t2028 = parse_relation_id(parser)
    relation_id1274 = _t2028
    consume_literal!(parser, ")")
    _t2029 = Proto.Output(name=name1273, relation_id=relation_id1274)
    result1276 = _t2029
    record_span!(parser, span_start1275, "Output")
    return result1276
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1279 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2030 = parse_name(parser)
    name1277 = _t2030
    _t2031 = parse_epoch(parser)
    epoch1278 = _t2031
    consume_literal!(parser, ")")
    _t2032 = Proto.WhatIf(branch=name1277, epoch=epoch1278)
    result1280 = _t2032
    record_span!(parser, span_start1279, "WhatIf")
    return result1280
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1283 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2034 = parse_name(parser)
        _t2033 = _t2034
    else
        _t2033 = nothing
    end
    name1281 = _t2033
    _t2035 = parse_relation_id(parser)
    relation_id1282 = _t2035
    consume_literal!(parser, ")")
    _t2036 = Proto.Abort(name=(!isnothing(name1281) ? name1281 : "abort"), relation_id=relation_id1282)
    result1284 = _t2036
    record_span!(parser, span_start1283, "Abort")
    return result1284
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1288 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2038 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2039 = 0
            else
                _t2039 = -1
            end
            _t2038 = _t2039
        end
        _t2037 = _t2038
    else
        _t2037 = -1
    end
    prediction1285 = _t2037
    if prediction1285 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2041 = parse_export_iceberg_config(parser)
        export_iceberg_config1287 = _t2041
        consume_literal!(parser, ")")
        _t2042 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1287))
        _t2040 = _t2042
    else
        if prediction1285 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2044 = parse_export_csv_config(parser)
            export_csv_config1286 = _t2044
            consume_literal!(parser, ")")
            _t2045 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1286))
            _t2043 = _t2045
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2040 = _t2043
    end
    result1289 = _t2040
    record_span!(parser, span_start1288, "Export")
    return result1289
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1297 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2047 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2048 = 1
            else
                _t2048 = -1
            end
            _t2047 = _t2048
        end
        _t2046 = _t2047
    else
        _t2046 = -1
    end
    prediction1290 = _t2046
    if prediction1290 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2050 = parse_export_csv_path(parser)
        export_csv_path1294 = _t2050
        _t2051 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1295 = _t2051
        _t2052 = parse_config_dict(parser)
        config_dict1296 = _t2052
        consume_literal!(parser, ")")
        _t2053 = construct_export_csv_config(parser, export_csv_path1294, export_csv_columns_list1295, config_dict1296)
        _t2049 = _t2053
    else
        if prediction1290 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2055 = parse_export_csv_path(parser)
            export_csv_path1291 = _t2055
            _t2056 = parse_export_csv_source(parser)
            export_csv_source1292 = _t2056
            _t2057 = parse_csv_config(parser)
            csv_config1293 = _t2057
            consume_literal!(parser, ")")
            _t2058 = construct_export_csv_config_with_source(parser, export_csv_path1291, export_csv_source1292, csv_config1293)
            _t2054 = _t2058
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2049 = _t2054
    end
    result1298 = _t2049
    record_span!(parser, span_start1297, "ExportCSVConfig")
    return result1298
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1299 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1299
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1306 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2060 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2061 = 0
            else
                _t2061 = -1
            end
            _t2060 = _t2061
        end
        _t2059 = _t2060
    else
        _t2059 = -1
    end
    prediction1300 = _t2059
    if prediction1300 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2063 = parse_relation_id(parser)
        relation_id1305 = _t2063
        consume_literal!(parser, ")")
        _t2064 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1305))
        _t2062 = _t2064
    else
        if prediction1300 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1301 = Proto.ExportCSVColumn[]
            cond1302 = match_lookahead_literal(parser, "(", 0)
            while cond1302
                _t2066 = parse_export_csv_column(parser)
                item1303 = _t2066
                push!(xs1301, item1303)
                cond1302 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1304 = xs1301
            consume_literal!(parser, ")")
            _t2067 = Proto.ExportCSVColumns(columns=export_csv_columns1304)
            _t2068 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2067))
            _t2065 = _t2068
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2062 = _t2065
    end
    result1307 = _t2062
    record_span!(parser, span_start1306, "ExportCSVSource")
    return result1307
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1310 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1308 = consume_terminal!(parser, "STRING")
    _t2069 = parse_relation_id(parser)
    relation_id1309 = _t2069
    consume_literal!(parser, ")")
    _t2070 = Proto.ExportCSVColumn(column_name=string1308, column_data=relation_id1309)
    result1311 = _t2070
    record_span!(parser, span_start1310, "ExportCSVColumn")
    return result1311
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1312 = Proto.ExportCSVColumn[]
    cond1313 = match_lookahead_literal(parser, "(", 0)
    while cond1313
        _t2071 = parse_export_csv_column(parser)
        item1314 = _t2071
        push!(xs1312, item1314)
        cond1313 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1315 = xs1312
    consume_literal!(parser, ")")
    return export_csv_columns1315
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1321 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2072 = parse_iceberg_locator(parser)
    iceberg_locator1316 = _t2072
    _t2073 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1317 = _t2073
    _t2074 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1318 = _t2074
    _t2075 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1319 = _t2075
    if match_lookahead_literal(parser, "{", 0)
        _t2077 = parse_config_dict(parser)
        _t2076 = _t2077
    else
        _t2076 = nothing
    end
    config_dict1320 = _t2076
    consume_literal!(parser, ")")
    _t2078 = construct_export_iceberg_config_full(parser, iceberg_locator1316, iceberg_catalog_config1317, export_iceberg_table_def1318, iceberg_table_properties1319, config_dict1320)
    result1322 = _t2078
    record_span!(parser, span_start1321, "ExportIcebergConfig")
    return result1322
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1324 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2079 = parse_relation_id(parser)
    relation_id1323 = _t2079
    consume_literal!(parser, ")")
    result1325 = relation_id1323
    record_span!(parser, span_start1324, "RelationId")
    return result1325
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1326 = Tuple{String, String}[]
    cond1327 = match_lookahead_literal(parser, "(", 0)
    while cond1327
        _t2080 = parse_iceberg_property_entry(parser)
        item1328 = _t2080
        push!(xs1326, item1328)
        cond1327 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1329 = xs1326
    consume_literal!(parser, ")")
    return iceberg_property_entrys1329
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
