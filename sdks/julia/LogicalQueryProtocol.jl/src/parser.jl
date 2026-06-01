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
        _t2103 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2104 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2105 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2106 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2107 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2108 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2109 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2110 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2111 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2112 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2112
    _t2113 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2113
    _t2114 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2114
    _t2115 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2115
    _t2116 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2116
    _t2117 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2117
    _t2118 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2118
    _t2119 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2119
    _t2120 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2120
    _t2121 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2121
    _t2122 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2122
    _t2123 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2123
    _t2124 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2124
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2125 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2125
    _t2126 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2126
    _t2127 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2127
    _t2128 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2128
    _t2129 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2129
    _t2130 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2130
    _t2131 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2131
    _t2132 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2132
    _t2133 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2133
    _t2134 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2134
    _t2135 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2135
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2136 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2136
    _t2137 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2137
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
    _t2138 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2138
    _t2139 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2139
    _t2140 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2140
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2141 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2141
    _t2142 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2142
    _t2143 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2143
    _t2144 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2144
    _t2145 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2145
    _t2146 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2146
    _t2147 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2147
    _t2148 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2148
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2149 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2149
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2150 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2150
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, target_opt::Union{Nothing, Proto.IcebergTarget}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2151 = Proto.IcebergData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta, target=target_opt)
    return _t2151
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2152 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2152
    _t2153 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2153
    _t2154 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2154
    table_props = Dict(table_property_pairs)
    _t2155 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2155
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start679 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1347 = parse_configure(parser)
        _t1346 = _t1347
    else
        _t1346 = nothing
    end
    configure673 = _t1346
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1349 = parse_sync(parser)
        _t1348 = _t1349
    else
        _t1348 = nothing
    end
    sync674 = _t1348
    xs675 = Proto.Epoch[]
    cond676 = match_lookahead_literal(parser, "(", 0)
    while cond676
        _t1350 = parse_epoch(parser)
        item677 = _t1350
        push!(xs675, item677)
        cond676 = match_lookahead_literal(parser, "(", 0)
    end
    epochs678 = xs675
    consume_literal!(parser, ")")
    _t1351 = default_configure(parser)
    _t1352 = Proto.Transaction(epochs=epochs678, configure=(!isnothing(configure673) ? configure673 : _t1351), sync=sync674)
    result680 = _t1352
    record_span!(parser, span_start679, "Transaction")
    return result680
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start682 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1353 = parse_config_dict(parser)
    config_dict681 = _t1353
    consume_literal!(parser, ")")
    _t1354 = construct_configure(parser, config_dict681)
    result683 = _t1354
    record_span!(parser, span_start682, "Configure")
    return result683
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs684 = Tuple{String, Proto.Value}[]
    cond685 = match_lookahead_literal(parser, ":", 0)
    while cond685
        _t1355 = parse_config_key_value(parser)
        item686 = _t1355
        push!(xs684, item686)
        cond685 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values687 = xs684
    consume_literal!(parser, "}")
    return config_key_values687
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol688 = consume_terminal!(parser, "SYMBOL")
    _t1356 = parse_raw_value(parser)
    raw_value689 = _t1356
    return (symbol688, raw_value689,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start703 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1357 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1358 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1359 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1361 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1362 = 0
                        else
                            _t1362 = -1
                        end
                        _t1361 = _t1362
                    end
                    _t1360 = _t1361
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1363 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1364 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1365 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1366 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1367 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1368 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1369 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1370 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1371 = 10
                                                    else
                                                        _t1371 = -1
                                                    end
                                                    _t1370 = _t1371
                                                end
                                                _t1369 = _t1370
                                            end
                                            _t1368 = _t1369
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
                    _t1360 = _t1363
                end
                _t1359 = _t1360
            end
            _t1358 = _t1359
        end
        _t1357 = _t1358
    end
    prediction690 = _t1357
    if prediction690 == 12
        _t1373 = parse_boolean_value(parser)
        boolean_value702 = _t1373
        _t1374 = Proto.Value(value=OneOf(:boolean_value, boolean_value702))
        _t1372 = _t1374
    else
        if prediction690 == 11
            consume_literal!(parser, "missing")
            _t1376 = Proto.MissingValue()
            _t1377 = Proto.Value(value=OneOf(:missing_value, _t1376))
            _t1375 = _t1377
        else
            if prediction690 == 10
                decimal701 = consume_terminal!(parser, "DECIMAL")
                _t1379 = Proto.Value(value=OneOf(:decimal_value, decimal701))
                _t1378 = _t1379
            else
                if prediction690 == 9
                    int128700 = consume_terminal!(parser, "INT128")
                    _t1381 = Proto.Value(value=OneOf(:int128_value, int128700))
                    _t1380 = _t1381
                else
                    if prediction690 == 8
                        uint128699 = consume_terminal!(parser, "UINT128")
                        _t1383 = Proto.Value(value=OneOf(:uint128_value, uint128699))
                        _t1382 = _t1383
                    else
                        if prediction690 == 7
                            uint32698 = consume_terminal!(parser, "UINT32")
                            _t1385 = Proto.Value(value=OneOf(:uint32_value, uint32698))
                            _t1384 = _t1385
                        else
                            if prediction690 == 6
                                float697 = consume_terminal!(parser, "FLOAT")
                                _t1387 = Proto.Value(value=OneOf(:float_value, float697))
                                _t1386 = _t1387
                            else
                                if prediction690 == 5
                                    float32696 = consume_terminal!(parser, "FLOAT32")
                                    _t1389 = Proto.Value(value=OneOf(:float32_value, float32696))
                                    _t1388 = _t1389
                                else
                                    if prediction690 == 4
                                        int695 = consume_terminal!(parser, "INT")
                                        _t1391 = Proto.Value(value=OneOf(:int_value, int695))
                                        _t1390 = _t1391
                                    else
                                        if prediction690 == 3
                                            int32694 = consume_terminal!(parser, "INT32")
                                            _t1393 = Proto.Value(value=OneOf(:int32_value, int32694))
                                            _t1392 = _t1393
                                        else
                                            if prediction690 == 2
                                                string693 = consume_terminal!(parser, "STRING")
                                                _t1395 = Proto.Value(value=OneOf(:string_value, string693))
                                                _t1394 = _t1395
                                            else
                                                if prediction690 == 1
                                                    _t1397 = parse_raw_datetime(parser)
                                                    raw_datetime692 = _t1397
                                                    _t1398 = Proto.Value(value=OneOf(:datetime_value, raw_datetime692))
                                                    _t1396 = _t1398
                                                else
                                                    if prediction690 == 0
                                                        _t1400 = parse_raw_date(parser)
                                                        raw_date691 = _t1400
                                                        _t1401 = Proto.Value(value=OneOf(:date_value, raw_date691))
                                                        _t1399 = _t1401
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1396 = _t1399
                                                end
                                                _t1394 = _t1396
                                            end
                                            _t1392 = _t1394
                                        end
                                        _t1390 = _t1392
                                    end
                                    _t1388 = _t1390
                                end
                                _t1386 = _t1388
                            end
                            _t1384 = _t1386
                        end
                        _t1382 = _t1384
                    end
                    _t1380 = _t1382
                end
                _t1378 = _t1380
            end
            _t1375 = _t1378
        end
        _t1372 = _t1375
    end
    result704 = _t1372
    record_span!(parser, span_start703, "Value")
    return result704
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start708 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int705 = consume_terminal!(parser, "INT")
    int_3706 = consume_terminal!(parser, "INT")
    int_4707 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1402 = Proto.DateValue(year=Int32(int705), month=Int32(int_3706), day=Int32(int_4707))
    result709 = _t1402
    record_span!(parser, span_start708, "DateValue")
    return result709
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start717 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int710 = consume_terminal!(parser, "INT")
    int_3711 = consume_terminal!(parser, "INT")
    int_4712 = consume_terminal!(parser, "INT")
    int_5713 = consume_terminal!(parser, "INT")
    int_6714 = consume_terminal!(parser, "INT")
    int_7715 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1403 = consume_terminal!(parser, "INT")
    else
        _t1403 = nothing
    end
    int_8716 = _t1403
    consume_literal!(parser, ")")
    _t1404 = Proto.DateTimeValue(year=Int32(int710), month=Int32(int_3711), day=Int32(int_4712), hour=Int32(int_5713), minute=Int32(int_6714), second=Int32(int_7715), microsecond=Int32((!isnothing(int_8716) ? int_8716 : 0)))
    result718 = _t1404
    record_span!(parser, span_start717, "DateTimeValue")
    return result718
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1405 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1406 = 1
        else
            _t1406 = -1
        end
        _t1405 = _t1406
    end
    prediction719 = _t1405
    if prediction719 == 1
        consume_literal!(parser, "false")
        _t1407 = false
    else
        if prediction719 == 0
            consume_literal!(parser, "true")
            _t1408 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1407 = _t1408
    end
    return _t1407
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start724 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs720 = Proto.FragmentId[]
    cond721 = match_lookahead_literal(parser, ":", 0)
    while cond721
        _t1409 = parse_fragment_id(parser)
        item722 = _t1409
        push!(xs720, item722)
        cond721 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids723 = xs720
    consume_literal!(parser, ")")
    _t1410 = Proto.Sync(fragments=fragment_ids723)
    result725 = _t1410
    record_span!(parser, span_start724, "Sync")
    return result725
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start727 = span_start(parser)
    consume_literal!(parser, ":")
    symbol726 = consume_terminal!(parser, "SYMBOL")
    result728 = Proto.FragmentId(Vector{UInt8}(symbol726))
    record_span!(parser, span_start727, "FragmentId")
    return result728
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start731 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1412 = parse_epoch_writes(parser)
        _t1411 = _t1412
    else
        _t1411 = nothing
    end
    epoch_writes729 = _t1411
    if match_lookahead_literal(parser, "(", 0)
        _t1414 = parse_epoch_reads(parser)
        _t1413 = _t1414
    else
        _t1413 = nothing
    end
    epoch_reads730 = _t1413
    consume_literal!(parser, ")")
    _t1415 = Proto.Epoch(writes=(!isnothing(epoch_writes729) ? epoch_writes729 : Proto.Write[]), reads=(!isnothing(epoch_reads730) ? epoch_reads730 : Proto.Read[]))
    result732 = _t1415
    record_span!(parser, span_start731, "Epoch")
    return result732
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs733 = Proto.Write[]
    cond734 = match_lookahead_literal(parser, "(", 0)
    while cond734
        _t1416 = parse_write(parser)
        item735 = _t1416
        push!(xs733, item735)
        cond734 = match_lookahead_literal(parser, "(", 0)
    end
    writes736 = xs733
    consume_literal!(parser, ")")
    return writes736
end

function parse_write(parser::ParserState)::Proto.Write
    span_start742 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1418 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1419 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1420 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1421 = 2
                    else
                        _t1421 = -1
                    end
                    _t1420 = _t1421
                end
                _t1419 = _t1420
            end
            _t1418 = _t1419
        end
        _t1417 = _t1418
    else
        _t1417 = -1
    end
    prediction737 = _t1417
    if prediction737 == 3
        _t1423 = parse_snapshot(parser)
        snapshot741 = _t1423
        _t1424 = Proto.Write(write_type=OneOf(:snapshot, snapshot741))
        _t1422 = _t1424
    else
        if prediction737 == 2
            _t1426 = parse_context(parser)
            context740 = _t1426
            _t1427 = Proto.Write(write_type=OneOf(:context, context740))
            _t1425 = _t1427
        else
            if prediction737 == 1
                _t1429 = parse_undefine(parser)
                undefine739 = _t1429
                _t1430 = Proto.Write(write_type=OneOf(:undefine, undefine739))
                _t1428 = _t1430
            else
                if prediction737 == 0
                    _t1432 = parse_define(parser)
                    define738 = _t1432
                    _t1433 = Proto.Write(write_type=OneOf(:define, define738))
                    _t1431 = _t1433
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1428 = _t1431
            end
            _t1425 = _t1428
        end
        _t1422 = _t1425
    end
    result743 = _t1422
    record_span!(parser, span_start742, "Write")
    return result743
end

function parse_define(parser::ParserState)::Proto.Define
    span_start745 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1434 = parse_fragment(parser)
    fragment744 = _t1434
    consume_literal!(parser, ")")
    _t1435 = Proto.Define(fragment=fragment744)
    result746 = _t1435
    record_span!(parser, span_start745, "Define")
    return result746
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start752 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1436 = parse_new_fragment_id(parser)
    new_fragment_id747 = _t1436
    xs748 = Proto.Declaration[]
    cond749 = match_lookahead_literal(parser, "(", 0)
    while cond749
        _t1437 = parse_declaration(parser)
        item750 = _t1437
        push!(xs748, item750)
        cond749 = match_lookahead_literal(parser, "(", 0)
    end
    declarations751 = xs748
    consume_literal!(parser, ")")
    result753 = construct_fragment(parser, new_fragment_id747, declarations751)
    record_span!(parser, span_start752, "Fragment")
    return result753
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start755 = span_start(parser)
    _t1438 = parse_fragment_id(parser)
    fragment_id754 = _t1438
    start_fragment!(parser, fragment_id754)
    result756 = fragment_id754
    record_span!(parser, span_start755, "FragmentId")
    return result756
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start762 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1440 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1441 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1442 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1443 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1444 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1445 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1446 = 1
                                else
                                    _t1446 = -1
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
    else
        _t1439 = -1
    end
    prediction757 = _t1439
    if prediction757 == 3
        _t1448 = parse_data(parser)
        data761 = _t1448
        _t1449 = Proto.Declaration(declaration_type=OneOf(:data, data761))
        _t1447 = _t1449
    else
        if prediction757 == 2
            _t1451 = parse_constraint(parser)
            constraint760 = _t1451
            _t1452 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint760))
            _t1450 = _t1452
        else
            if prediction757 == 1
                _t1454 = parse_algorithm(parser)
                algorithm759 = _t1454
                _t1455 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm759))
                _t1453 = _t1455
            else
                if prediction757 == 0
                    _t1457 = parse_def(parser)
                    def758 = _t1457
                    _t1458 = Proto.Declaration(declaration_type=OneOf(:def, def758))
                    _t1456 = _t1458
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1453 = _t1456
            end
            _t1450 = _t1453
        end
        _t1447 = _t1450
    end
    result763 = _t1447
    record_span!(parser, span_start762, "Declaration")
    return result763
end

function parse_def(parser::ParserState)::Proto.Def
    span_start767 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1459 = parse_relation_id(parser)
    relation_id764 = _t1459
    _t1460 = parse_abstraction(parser)
    abstraction765 = _t1460
    if match_lookahead_literal(parser, "(", 0)
        _t1462 = parse_attrs(parser)
        _t1461 = _t1462
    else
        _t1461 = nothing
    end
    attrs766 = _t1461
    consume_literal!(parser, ")")
    _t1463 = Proto.Def(name=relation_id764, body=abstraction765, attrs=(!isnothing(attrs766) ? attrs766 : Proto.Attribute[]))
    result768 = _t1463
    record_span!(parser, span_start767, "Def")
    return result768
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start772 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1464 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1465 = 1
        else
            _t1465 = -1
        end
        _t1464 = _t1465
    end
    prediction769 = _t1464
    if prediction769 == 1
        uint128771 = consume_terminal!(parser, "UINT128")
        _t1466 = Proto.RelationId(uint128771.low, uint128771.high)
    else
        if prediction769 == 0
            consume_literal!(parser, ":")
            symbol770 = consume_terminal!(parser, "SYMBOL")
            _t1467 = relation_id_from_string(parser, symbol770)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1466 = _t1467
    end
    result773 = _t1466
    record_span!(parser, span_start772, "RelationId")
    return result773
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start776 = span_start(parser)
    consume_literal!(parser, "(")
    _t1468 = parse_bindings(parser)
    bindings774 = _t1468
    _t1469 = parse_formula(parser)
    formula775 = _t1469
    consume_literal!(parser, ")")
    _t1470 = Proto.Abstraction(vars=vcat(bindings774[1], !isnothing(bindings774[2]) ? bindings774[2] : []), value=formula775)
    result777 = _t1470
    record_span!(parser, span_start776, "Abstraction")
    return result777
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs778 = Proto.Binding[]
    cond779 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond779
        _t1471 = parse_binding(parser)
        item780 = _t1471
        push!(xs778, item780)
        cond779 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings781 = xs778
    if match_lookahead_literal(parser, "|", 0)
        _t1473 = parse_value_bindings(parser)
        _t1472 = _t1473
    else
        _t1472 = nothing
    end
    value_bindings782 = _t1472
    consume_literal!(parser, "]")
    return (bindings781, (!isnothing(value_bindings782) ? value_bindings782 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start785 = span_start(parser)
    symbol783 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1474 = parse_type(parser)
    type784 = _t1474
    _t1475 = Proto.Var(name=symbol783)
    _t1476 = Proto.Binding(var=_t1475, var"#type"=type784)
    result786 = _t1476
    record_span!(parser, span_start785, "Binding")
    return result786
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start802 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1477 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1478 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1479 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1480 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1481 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1482 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1483 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1484 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1485 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1486 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1487 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1488 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1489 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1490 = 9
                                                        else
                                                            _t1490 = -1
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
                        _t1481 = _t1482
                    end
                    _t1480 = _t1481
                end
                _t1479 = _t1480
            end
            _t1478 = _t1479
        end
        _t1477 = _t1478
    end
    prediction787 = _t1477
    if prediction787 == 13
        _t1492 = parse_uint32_type(parser)
        uint32_type801 = _t1492
        _t1493 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type801))
        _t1491 = _t1493
    else
        if prediction787 == 12
            _t1495 = parse_float32_type(parser)
            float32_type800 = _t1495
            _t1496 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type800))
            _t1494 = _t1496
        else
            if prediction787 == 11
                _t1498 = parse_int32_type(parser)
                int32_type799 = _t1498
                _t1499 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type799))
                _t1497 = _t1499
            else
                if prediction787 == 10
                    _t1501 = parse_boolean_type(parser)
                    boolean_type798 = _t1501
                    _t1502 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type798))
                    _t1500 = _t1502
                else
                    if prediction787 == 9
                        _t1504 = parse_decimal_type(parser)
                        decimal_type797 = _t1504
                        _t1505 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type797))
                        _t1503 = _t1505
                    else
                        if prediction787 == 8
                            _t1507 = parse_missing_type(parser)
                            missing_type796 = _t1507
                            _t1508 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type796))
                            _t1506 = _t1508
                        else
                            if prediction787 == 7
                                _t1510 = parse_datetime_type(parser)
                                datetime_type795 = _t1510
                                _t1511 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type795))
                                _t1509 = _t1511
                            else
                                if prediction787 == 6
                                    _t1513 = parse_date_type(parser)
                                    date_type794 = _t1513
                                    _t1514 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type794))
                                    _t1512 = _t1514
                                else
                                    if prediction787 == 5
                                        _t1516 = parse_int128_type(parser)
                                        int128_type793 = _t1516
                                        _t1517 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type793))
                                        _t1515 = _t1517
                                    else
                                        if prediction787 == 4
                                            _t1519 = parse_uint128_type(parser)
                                            uint128_type792 = _t1519
                                            _t1520 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type792))
                                            _t1518 = _t1520
                                        else
                                            if prediction787 == 3
                                                _t1522 = parse_float_type(parser)
                                                float_type791 = _t1522
                                                _t1523 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type791))
                                                _t1521 = _t1523
                                            else
                                                if prediction787 == 2
                                                    _t1525 = parse_int_type(parser)
                                                    int_type790 = _t1525
                                                    _t1526 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type790))
                                                    _t1524 = _t1526
                                                else
                                                    if prediction787 == 1
                                                        _t1528 = parse_string_type(parser)
                                                        string_type789 = _t1528
                                                        _t1529 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type789))
                                                        _t1527 = _t1529
                                                    else
                                                        if prediction787 == 0
                                                            _t1531 = parse_unspecified_type(parser)
                                                            unspecified_type788 = _t1531
                                                            _t1532 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type788))
                                                            _t1530 = _t1532
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                                _t1509 = _t1512
                            end
                            _t1506 = _t1509
                        end
                        _t1503 = _t1506
                    end
                    _t1500 = _t1503
                end
                _t1497 = _t1500
            end
            _t1494 = _t1497
        end
        _t1491 = _t1494
    end
    result803 = _t1491
    record_span!(parser, span_start802, "Type")
    return result803
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start804 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1533 = Proto.UnspecifiedType()
    result805 = _t1533
    record_span!(parser, span_start804, "UnspecifiedType")
    return result805
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start806 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1534 = Proto.StringType()
    result807 = _t1534
    record_span!(parser, span_start806, "StringType")
    return result807
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start808 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1535 = Proto.IntType()
    result809 = _t1535
    record_span!(parser, span_start808, "IntType")
    return result809
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start810 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1536 = Proto.FloatType()
    result811 = _t1536
    record_span!(parser, span_start810, "FloatType")
    return result811
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start812 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1537 = Proto.UInt128Type()
    result813 = _t1537
    record_span!(parser, span_start812, "UInt128Type")
    return result813
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start814 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1538 = Proto.Int128Type()
    result815 = _t1538
    record_span!(parser, span_start814, "Int128Type")
    return result815
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start816 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1539 = Proto.DateType()
    result817 = _t1539
    record_span!(parser, span_start816, "DateType")
    return result817
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start818 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1540 = Proto.DateTimeType()
    result819 = _t1540
    record_span!(parser, span_start818, "DateTimeType")
    return result819
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start820 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1541 = Proto.MissingType()
    result821 = _t1541
    record_span!(parser, span_start820, "MissingType")
    return result821
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start824 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int822 = consume_terminal!(parser, "INT")
    int_3823 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1542 = Proto.DecimalType(precision=Int32(int822), scale=Int32(int_3823))
    result825 = _t1542
    record_span!(parser, span_start824, "DecimalType")
    return result825
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start826 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1543 = Proto.BooleanType()
    result827 = _t1543
    record_span!(parser, span_start826, "BooleanType")
    return result827
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start828 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1544 = Proto.Int32Type()
    result829 = _t1544
    record_span!(parser, span_start828, "Int32Type")
    return result829
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start830 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1545 = Proto.Float32Type()
    result831 = _t1545
    record_span!(parser, span_start830, "Float32Type")
    return result831
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start832 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1546 = Proto.UInt32Type()
    result833 = _t1546
    record_span!(parser, span_start832, "UInt32Type")
    return result833
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs834 = Proto.Binding[]
    cond835 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond835
        _t1547 = parse_binding(parser)
        item836 = _t1547
        push!(xs834, item836)
        cond835 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings837 = xs834
    return bindings837
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start852 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1549 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1550 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1551 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1552 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1553 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1554 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1555 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1556 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1557 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1558 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1559 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1560 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1561 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1562 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1563 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1564 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1565 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1566 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1567 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1568 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1569 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1570 = 10
                                                                                            else
                                                                                                _t1570 = -1
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
                                                            _t1561 = _t1562
                                                        end
                                                        _t1560 = _t1561
                                                    end
                                                    _t1559 = _t1560
                                                end
                                                _t1558 = _t1559
                                            end
                                            _t1557 = _t1558
                                        end
                                        _t1556 = _t1557
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
    else
        _t1548 = -1
    end
    prediction838 = _t1548
    if prediction838 == 12
        _t1572 = parse_cast(parser)
        cast851 = _t1572
        _t1573 = Proto.Formula(formula_type=OneOf(:cast, cast851))
        _t1571 = _t1573
    else
        if prediction838 == 11
            _t1575 = parse_rel_atom(parser)
            rel_atom850 = _t1575
            _t1576 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom850))
            _t1574 = _t1576
        else
            if prediction838 == 10
                _t1578 = parse_primitive(parser)
                primitive849 = _t1578
                _t1579 = Proto.Formula(formula_type=OneOf(:primitive, primitive849))
                _t1577 = _t1579
            else
                if prediction838 == 9
                    _t1581 = parse_pragma(parser)
                    pragma848 = _t1581
                    _t1582 = Proto.Formula(formula_type=OneOf(:pragma, pragma848))
                    _t1580 = _t1582
                else
                    if prediction838 == 8
                        _t1584 = parse_atom(parser)
                        atom847 = _t1584
                        _t1585 = Proto.Formula(formula_type=OneOf(:atom, atom847))
                        _t1583 = _t1585
                    else
                        if prediction838 == 7
                            _t1587 = parse_ffi(parser)
                            ffi846 = _t1587
                            _t1588 = Proto.Formula(formula_type=OneOf(:ffi, ffi846))
                            _t1586 = _t1588
                        else
                            if prediction838 == 6
                                _t1590 = parse_not(parser)
                                not845 = _t1590
                                _t1591 = Proto.Formula(formula_type=OneOf(:not, not845))
                                _t1589 = _t1591
                            else
                                if prediction838 == 5
                                    _t1593 = parse_disjunction(parser)
                                    disjunction844 = _t1593
                                    _t1594 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction844))
                                    _t1592 = _t1594
                                else
                                    if prediction838 == 4
                                        _t1596 = parse_conjunction(parser)
                                        conjunction843 = _t1596
                                        _t1597 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction843))
                                        _t1595 = _t1597
                                    else
                                        if prediction838 == 3
                                            _t1599 = parse_reduce(parser)
                                            reduce842 = _t1599
                                            _t1600 = Proto.Formula(formula_type=OneOf(:reduce, reduce842))
                                            _t1598 = _t1600
                                        else
                                            if prediction838 == 2
                                                _t1602 = parse_exists(parser)
                                                exists841 = _t1602
                                                _t1603 = Proto.Formula(formula_type=OneOf(:exists, exists841))
                                                _t1601 = _t1603
                                            else
                                                if prediction838 == 1
                                                    _t1605 = parse_false(parser)
                                                    false840 = _t1605
                                                    _t1606 = Proto.Formula(formula_type=OneOf(:disjunction, false840))
                                                    _t1604 = _t1606
                                                else
                                                    if prediction838 == 0
                                                        _t1608 = parse_true(parser)
                                                        true839 = _t1608
                                                        _t1609 = Proto.Formula(formula_type=OneOf(:conjunction, true839))
                                                        _t1607 = _t1609
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1604 = _t1607
                                                end
                                                _t1601 = _t1604
                                            end
                                            _t1598 = _t1601
                                        end
                                        _t1595 = _t1598
                                    end
                                    _t1592 = _t1595
                                end
                                _t1589 = _t1592
                            end
                            _t1586 = _t1589
                        end
                        _t1583 = _t1586
                    end
                    _t1580 = _t1583
                end
                _t1577 = _t1580
            end
            _t1574 = _t1577
        end
        _t1571 = _t1574
    end
    result853 = _t1571
    record_span!(parser, span_start852, "Formula")
    return result853
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start854 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1610 = Proto.Conjunction(args=Proto.Formula[])
    result855 = _t1610
    record_span!(parser, span_start854, "Conjunction")
    return result855
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start856 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1611 = Proto.Disjunction(args=Proto.Formula[])
    result857 = _t1611
    record_span!(parser, span_start856, "Disjunction")
    return result857
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start860 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1612 = parse_bindings(parser)
    bindings858 = _t1612
    _t1613 = parse_formula(parser)
    formula859 = _t1613
    consume_literal!(parser, ")")
    _t1614 = Proto.Abstraction(vars=vcat(bindings858[1], !isnothing(bindings858[2]) ? bindings858[2] : []), value=formula859)
    _t1615 = Proto.Exists(body=_t1614)
    result861 = _t1615
    record_span!(parser, span_start860, "Exists")
    return result861
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start865 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1616 = parse_abstraction(parser)
    abstraction862 = _t1616
    _t1617 = parse_abstraction(parser)
    abstraction_3863 = _t1617
    _t1618 = parse_terms(parser)
    terms864 = _t1618
    consume_literal!(parser, ")")
    _t1619 = Proto.Reduce(op=abstraction862, body=abstraction_3863, terms=terms864)
    result866 = _t1619
    record_span!(parser, span_start865, "Reduce")
    return result866
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs867 = Proto.Term[]
    cond868 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond868
        _t1620 = parse_term(parser)
        item869 = _t1620
        push!(xs867, item869)
        cond868 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms870 = xs867
    consume_literal!(parser, ")")
    return terms870
end

function parse_term(parser::ParserState)::Proto.Term
    span_start874 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1621 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1622 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1623 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1624 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1625 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1626 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1627 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1628 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1629 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1630 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1631 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1632 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1633 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1634 = 1
                                                        else
                                                            _t1634 = -1
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
                _t1623 = _t1624
            end
            _t1622 = _t1623
        end
        _t1621 = _t1622
    end
    prediction871 = _t1621
    if prediction871 == 1
        _t1636 = parse_value(parser)
        value873 = _t1636
        _t1637 = Proto.Term(term_type=OneOf(:constant, value873))
        _t1635 = _t1637
    else
        if prediction871 == 0
            _t1639 = parse_var(parser)
            var872 = _t1639
            _t1640 = Proto.Term(term_type=OneOf(:var, var872))
            _t1638 = _t1640
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1635 = _t1638
    end
    result875 = _t1635
    record_span!(parser, span_start874, "Term")
    return result875
end

function parse_var(parser::ParserState)::Proto.Var
    span_start877 = span_start(parser)
    symbol876 = consume_terminal!(parser, "SYMBOL")
    _t1641 = Proto.Var(name=symbol876)
    result878 = _t1641
    record_span!(parser, span_start877, "Var")
    return result878
end

function parse_value(parser::ParserState)::Proto.Value
    span_start892 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1642 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1643 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1644 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1646 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1647 = 0
                        else
                            _t1647 = -1
                        end
                        _t1646 = _t1647
                    end
                    _t1645 = _t1646
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1648 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1649 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1650 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1651 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1652 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1653 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1654 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1655 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1656 = 10
                                                    else
                                                        _t1656 = -1
                                                    end
                                                    _t1655 = _t1656
                                                end
                                                _t1654 = _t1655
                                            end
                                            _t1653 = _t1654
                                        end
                                        _t1652 = _t1653
                                    end
                                    _t1651 = _t1652
                                end
                                _t1650 = _t1651
                            end
                            _t1649 = _t1650
                        end
                        _t1648 = _t1649
                    end
                    _t1645 = _t1648
                end
                _t1644 = _t1645
            end
            _t1643 = _t1644
        end
        _t1642 = _t1643
    end
    prediction879 = _t1642
    if prediction879 == 12
        _t1658 = parse_boolean_value(parser)
        boolean_value891 = _t1658
        _t1659 = Proto.Value(value=OneOf(:boolean_value, boolean_value891))
        _t1657 = _t1659
    else
        if prediction879 == 11
            consume_literal!(parser, "missing")
            _t1661 = Proto.MissingValue()
            _t1662 = Proto.Value(value=OneOf(:missing_value, _t1661))
            _t1660 = _t1662
        else
            if prediction879 == 10
                formatted_decimal890 = consume_terminal!(parser, "DECIMAL")
                _t1664 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal890))
                _t1663 = _t1664
            else
                if prediction879 == 9
                    formatted_int128889 = consume_terminal!(parser, "INT128")
                    _t1666 = Proto.Value(value=OneOf(:int128_value, formatted_int128889))
                    _t1665 = _t1666
                else
                    if prediction879 == 8
                        formatted_uint128888 = consume_terminal!(parser, "UINT128")
                        _t1668 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128888))
                        _t1667 = _t1668
                    else
                        if prediction879 == 7
                            formatted_uint32887 = consume_terminal!(parser, "UINT32")
                            _t1670 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32887))
                            _t1669 = _t1670
                        else
                            if prediction879 == 6
                                formatted_float886 = consume_terminal!(parser, "FLOAT")
                                _t1672 = Proto.Value(value=OneOf(:float_value, formatted_float886))
                                _t1671 = _t1672
                            else
                                if prediction879 == 5
                                    formatted_float32885 = consume_terminal!(parser, "FLOAT32")
                                    _t1674 = Proto.Value(value=OneOf(:float32_value, formatted_float32885))
                                    _t1673 = _t1674
                                else
                                    if prediction879 == 4
                                        formatted_int884 = consume_terminal!(parser, "INT")
                                        _t1676 = Proto.Value(value=OneOf(:int_value, formatted_int884))
                                        _t1675 = _t1676
                                    else
                                        if prediction879 == 3
                                            formatted_int32883 = consume_terminal!(parser, "INT32")
                                            _t1678 = Proto.Value(value=OneOf(:int32_value, formatted_int32883))
                                            _t1677 = _t1678
                                        else
                                            if prediction879 == 2
                                                formatted_string882 = consume_terminal!(parser, "STRING")
                                                _t1680 = Proto.Value(value=OneOf(:string_value, formatted_string882))
                                                _t1679 = _t1680
                                            else
                                                if prediction879 == 1
                                                    _t1682 = parse_datetime(parser)
                                                    datetime881 = _t1682
                                                    _t1683 = Proto.Value(value=OneOf(:datetime_value, datetime881))
                                                    _t1681 = _t1683
                                                else
                                                    if prediction879 == 0
                                                        _t1685 = parse_date(parser)
                                                        date880 = _t1685
                                                        _t1686 = Proto.Value(value=OneOf(:date_value, date880))
                                                        _t1684 = _t1686
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1681 = _t1684
                                                end
                                                _t1679 = _t1681
                                            end
                                            _t1677 = _t1679
                                        end
                                        _t1675 = _t1677
                                    end
                                    _t1673 = _t1675
                                end
                                _t1671 = _t1673
                            end
                            _t1669 = _t1671
                        end
                        _t1667 = _t1669
                    end
                    _t1665 = _t1667
                end
                _t1663 = _t1665
            end
            _t1660 = _t1663
        end
        _t1657 = _t1660
    end
    result893 = _t1657
    record_span!(parser, span_start892, "Value")
    return result893
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start897 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int894 = consume_terminal!(parser, "INT")
    formatted_int_3895 = consume_terminal!(parser, "INT")
    formatted_int_4896 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1687 = Proto.DateValue(year=Int32(formatted_int894), month=Int32(formatted_int_3895), day=Int32(formatted_int_4896))
    result898 = _t1687
    record_span!(parser, span_start897, "DateValue")
    return result898
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start906 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int899 = consume_terminal!(parser, "INT")
    formatted_int_3900 = consume_terminal!(parser, "INT")
    formatted_int_4901 = consume_terminal!(parser, "INT")
    formatted_int_5902 = consume_terminal!(parser, "INT")
    formatted_int_6903 = consume_terminal!(parser, "INT")
    formatted_int_7904 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1688 = consume_terminal!(parser, "INT")
    else
        _t1688 = nothing
    end
    formatted_int_8905 = _t1688
    consume_literal!(parser, ")")
    _t1689 = Proto.DateTimeValue(year=Int32(formatted_int899), month=Int32(formatted_int_3900), day=Int32(formatted_int_4901), hour=Int32(formatted_int_5902), minute=Int32(formatted_int_6903), second=Int32(formatted_int_7904), microsecond=Int32((!isnothing(formatted_int_8905) ? formatted_int_8905 : 0)))
    result907 = _t1689
    record_span!(parser, span_start906, "DateTimeValue")
    return result907
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start912 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs908 = Proto.Formula[]
    cond909 = match_lookahead_literal(parser, "(", 0)
    while cond909
        _t1690 = parse_formula(parser)
        item910 = _t1690
        push!(xs908, item910)
        cond909 = match_lookahead_literal(parser, "(", 0)
    end
    formulas911 = xs908
    consume_literal!(parser, ")")
    _t1691 = Proto.Conjunction(args=formulas911)
    result913 = _t1691
    record_span!(parser, span_start912, "Conjunction")
    return result913
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start918 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs914 = Proto.Formula[]
    cond915 = match_lookahead_literal(parser, "(", 0)
    while cond915
        _t1692 = parse_formula(parser)
        item916 = _t1692
        push!(xs914, item916)
        cond915 = match_lookahead_literal(parser, "(", 0)
    end
    formulas917 = xs914
    consume_literal!(parser, ")")
    _t1693 = Proto.Disjunction(args=formulas917)
    result919 = _t1693
    record_span!(parser, span_start918, "Disjunction")
    return result919
end

function parse_not(parser::ParserState)::Proto.Not
    span_start921 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1694 = parse_formula(parser)
    formula920 = _t1694
    consume_literal!(parser, ")")
    _t1695 = Proto.Not(arg=formula920)
    result922 = _t1695
    record_span!(parser, span_start921, "Not")
    return result922
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start926 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1696 = parse_name(parser)
    name923 = _t1696
    _t1697 = parse_ffi_args(parser)
    ffi_args924 = _t1697
    _t1698 = parse_terms(parser)
    terms925 = _t1698
    consume_literal!(parser, ")")
    _t1699 = Proto.FFI(name=name923, args=ffi_args924, terms=terms925)
    result927 = _t1699
    record_span!(parser, span_start926, "FFI")
    return result927
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol928 = consume_terminal!(parser, "SYMBOL")
    return symbol928
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs929 = Proto.Abstraction[]
    cond930 = match_lookahead_literal(parser, "(", 0)
    while cond930
        _t1700 = parse_abstraction(parser)
        item931 = _t1700
        push!(xs929, item931)
        cond930 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions932 = xs929
    consume_literal!(parser, ")")
    return abstractions932
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start938 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1701 = parse_relation_id(parser)
    relation_id933 = _t1701
    xs934 = Proto.Term[]
    cond935 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond935
        _t1702 = parse_term(parser)
        item936 = _t1702
        push!(xs934, item936)
        cond935 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms937 = xs934
    consume_literal!(parser, ")")
    _t1703 = Proto.Atom(name=relation_id933, terms=terms937)
    result939 = _t1703
    record_span!(parser, span_start938, "Atom")
    return result939
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start945 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1704 = parse_name(parser)
    name940 = _t1704
    xs941 = Proto.Term[]
    cond942 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond942
        _t1705 = parse_term(parser)
        item943 = _t1705
        push!(xs941, item943)
        cond942 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms944 = xs941
    consume_literal!(parser, ")")
    _t1706 = Proto.Pragma(name=name940, terms=terms944)
    result946 = _t1706
    record_span!(parser, span_start945, "Pragma")
    return result946
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start962 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1708 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1709 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1710 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1711 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1712 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1713 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1714 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1715 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1716 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1717 = 7
                                            else
                                                _t1717 = -1
                                            end
                                            _t1716 = _t1717
                                        end
                                        _t1715 = _t1716
                                    end
                                    _t1714 = _t1715
                                end
                                _t1713 = _t1714
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
        end
        _t1707 = _t1708
    else
        _t1707 = -1
    end
    prediction947 = _t1707
    if prediction947 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1719 = parse_name(parser)
        name957 = _t1719
        xs958 = Proto.RelTerm[]
        cond959 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond959
            _t1720 = parse_rel_term(parser)
            item960 = _t1720
            push!(xs958, item960)
            cond959 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms961 = xs958
        consume_literal!(parser, ")")
        _t1721 = Proto.Primitive(name=name957, terms=rel_terms961)
        _t1718 = _t1721
    else
        if prediction947 == 8
            _t1723 = parse_divide(parser)
            divide956 = _t1723
            _t1722 = divide956
        else
            if prediction947 == 7
                _t1725 = parse_multiply(parser)
                multiply955 = _t1725
                _t1724 = multiply955
            else
                if prediction947 == 6
                    _t1727 = parse_minus(parser)
                    minus954 = _t1727
                    _t1726 = minus954
                else
                    if prediction947 == 5
                        _t1729 = parse_add(parser)
                        add953 = _t1729
                        _t1728 = add953
                    else
                        if prediction947 == 4
                            _t1731 = parse_gt_eq(parser)
                            gt_eq952 = _t1731
                            _t1730 = gt_eq952
                        else
                            if prediction947 == 3
                                _t1733 = parse_gt(parser)
                                gt951 = _t1733
                                _t1732 = gt951
                            else
                                if prediction947 == 2
                                    _t1735 = parse_lt_eq(parser)
                                    lt_eq950 = _t1735
                                    _t1734 = lt_eq950
                                else
                                    if prediction947 == 1
                                        _t1737 = parse_lt(parser)
                                        lt949 = _t1737
                                        _t1736 = lt949
                                    else
                                        if prediction947 == 0
                                            _t1739 = parse_eq(parser)
                                            eq948 = _t1739
                                            _t1738 = eq948
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1736 = _t1738
                                    end
                                    _t1734 = _t1736
                                end
                                _t1732 = _t1734
                            end
                            _t1730 = _t1732
                        end
                        _t1728 = _t1730
                    end
                    _t1726 = _t1728
                end
                _t1724 = _t1726
            end
            _t1722 = _t1724
        end
        _t1718 = _t1722
    end
    result963 = _t1718
    record_span!(parser, span_start962, "Primitive")
    return result963
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start966 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1740 = parse_term(parser)
    term964 = _t1740
    _t1741 = parse_term(parser)
    term_3965 = _t1741
    consume_literal!(parser, ")")
    _t1742 = Proto.RelTerm(rel_term_type=OneOf(:term, term964))
    _t1743 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3965))
    _t1744 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1742, _t1743])
    result967 = _t1744
    record_span!(parser, span_start966, "Primitive")
    return result967
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start970 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1745 = parse_term(parser)
    term968 = _t1745
    _t1746 = parse_term(parser)
    term_3969 = _t1746
    consume_literal!(parser, ")")
    _t1747 = Proto.RelTerm(rel_term_type=OneOf(:term, term968))
    _t1748 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3969))
    _t1749 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1747, _t1748])
    result971 = _t1749
    record_span!(parser, span_start970, "Primitive")
    return result971
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1750 = parse_term(parser)
    term972 = _t1750
    _t1751 = parse_term(parser)
    term_3973 = _t1751
    consume_literal!(parser, ")")
    _t1752 = Proto.RelTerm(rel_term_type=OneOf(:term, term972))
    _t1753 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3973))
    _t1754 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1752, _t1753])
    result975 = _t1754
    record_span!(parser, span_start974, "Primitive")
    return result975
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start978 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1755 = parse_term(parser)
    term976 = _t1755
    _t1756 = parse_term(parser)
    term_3977 = _t1756
    consume_literal!(parser, ")")
    _t1757 = Proto.RelTerm(rel_term_type=OneOf(:term, term976))
    _t1758 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3977))
    _t1759 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1757, _t1758])
    result979 = _t1759
    record_span!(parser, span_start978, "Primitive")
    return result979
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start982 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1760 = parse_term(parser)
    term980 = _t1760
    _t1761 = parse_term(parser)
    term_3981 = _t1761
    consume_literal!(parser, ")")
    _t1762 = Proto.RelTerm(rel_term_type=OneOf(:term, term980))
    _t1763 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3981))
    _t1764 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1762, _t1763])
    result983 = _t1764
    record_span!(parser, span_start982, "Primitive")
    return result983
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start987 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1765 = parse_term(parser)
    term984 = _t1765
    _t1766 = parse_term(parser)
    term_3985 = _t1766
    _t1767 = parse_term(parser)
    term_4986 = _t1767
    consume_literal!(parser, ")")
    _t1768 = Proto.RelTerm(rel_term_type=OneOf(:term, term984))
    _t1769 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3985))
    _t1770 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4986))
    _t1771 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1768, _t1769, _t1770])
    result988 = _t1771
    record_span!(parser, span_start987, "Primitive")
    return result988
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start992 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1772 = parse_term(parser)
    term989 = _t1772
    _t1773 = parse_term(parser)
    term_3990 = _t1773
    _t1774 = parse_term(parser)
    term_4991 = _t1774
    consume_literal!(parser, ")")
    _t1775 = Proto.RelTerm(rel_term_type=OneOf(:term, term989))
    _t1776 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3990))
    _t1777 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4991))
    _t1778 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1775, _t1776, _t1777])
    result993 = _t1778
    record_span!(parser, span_start992, "Primitive")
    return result993
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start997 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1779 = parse_term(parser)
    term994 = _t1779
    _t1780 = parse_term(parser)
    term_3995 = _t1780
    _t1781 = parse_term(parser)
    term_4996 = _t1781
    consume_literal!(parser, ")")
    _t1782 = Proto.RelTerm(rel_term_type=OneOf(:term, term994))
    _t1783 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3995))
    _t1784 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4996))
    _t1785 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1782, _t1783, _t1784])
    result998 = _t1785
    record_span!(parser, span_start997, "Primitive")
    return result998
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1002 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1786 = parse_term(parser)
    term999 = _t1786
    _t1787 = parse_term(parser)
    term_31000 = _t1787
    _t1788 = parse_term(parser)
    term_41001 = _t1788
    consume_literal!(parser, ")")
    _t1789 = Proto.RelTerm(rel_term_type=OneOf(:term, term999))
    _t1790 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31000))
    _t1791 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41001))
    _t1792 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1789, _t1790, _t1791])
    result1003 = _t1792
    record_span!(parser, span_start1002, "Primitive")
    return result1003
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1007 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1793 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1794 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1795 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1796 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1797 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1798 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1799 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1800 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1801 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1802 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1803 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1804 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1805 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1806 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1807 = 1
                                                            else
                                                                _t1807 = -1
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
                                        end
                                        _t1801 = _t1802
                                    end
                                    _t1800 = _t1801
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
        end
        _t1793 = _t1794
    end
    prediction1004 = _t1793
    if prediction1004 == 1
        _t1809 = parse_term(parser)
        term1006 = _t1809
        _t1810 = Proto.RelTerm(rel_term_type=OneOf(:term, term1006))
        _t1808 = _t1810
    else
        if prediction1004 == 0
            _t1812 = parse_specialized_value(parser)
            specialized_value1005 = _t1812
            _t1813 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1005))
            _t1811 = _t1813
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1808 = _t1811
    end
    result1008 = _t1808
    record_span!(parser, span_start1007, "RelTerm")
    return result1008
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1010 = span_start(parser)
    consume_literal!(parser, "#")
    _t1814 = parse_raw_value(parser)
    raw_value1009 = _t1814
    result1011 = raw_value1009
    record_span!(parser, span_start1010, "Value")
    return result1011
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1017 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1815 = parse_name(parser)
    name1012 = _t1815
    xs1013 = Proto.RelTerm[]
    cond1014 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1014
        _t1816 = parse_rel_term(parser)
        item1015 = _t1816
        push!(xs1013, item1015)
        cond1014 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1016 = xs1013
    consume_literal!(parser, ")")
    _t1817 = Proto.RelAtom(name=name1012, terms=rel_terms1016)
    result1018 = _t1817
    record_span!(parser, span_start1017, "RelAtom")
    return result1018
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1021 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1818 = parse_term(parser)
    term1019 = _t1818
    _t1819 = parse_term(parser)
    term_31020 = _t1819
    consume_literal!(parser, ")")
    _t1820 = Proto.Cast(input=term1019, result=term_31020)
    result1022 = _t1820
    record_span!(parser, span_start1021, "Cast")
    return result1022
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1023 = Proto.Attribute[]
    cond1024 = match_lookahead_literal(parser, "(", 0)
    while cond1024
        _t1821 = parse_attribute(parser)
        item1025 = _t1821
        push!(xs1023, item1025)
        cond1024 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1026 = xs1023
    consume_literal!(parser, ")")
    return attributes1026
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1032 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1822 = parse_name(parser)
    name1027 = _t1822
    xs1028 = Proto.Value[]
    cond1029 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1029
        _t1823 = parse_raw_value(parser)
        item1030 = _t1823
        push!(xs1028, item1030)
        cond1029 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1031 = xs1028
    consume_literal!(parser, ")")
    _t1824 = Proto.Attribute(name=name1027, args=raw_values1031)
    result1033 = _t1824
    record_span!(parser, span_start1032, "Attribute")
    return result1033
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1040 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1034 = Proto.RelationId[]
    cond1035 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1035
        _t1825 = parse_relation_id(parser)
        item1036 = _t1825
        push!(xs1034, item1036)
        cond1035 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1037 = xs1034
    _t1826 = parse_script(parser)
    script1038 = _t1826
    if match_lookahead_literal(parser, "(", 0)
        _t1828 = parse_attrs(parser)
        _t1827 = _t1828
    else
        _t1827 = nothing
    end
    attrs1039 = _t1827
    consume_literal!(parser, ")")
    _t1829 = Proto.Algorithm(var"#global"=relation_ids1037, body=script1038, attrs=(!isnothing(attrs1039) ? attrs1039 : Proto.Attribute[]))
    result1041 = _t1829
    record_span!(parser, span_start1040, "Algorithm")
    return result1041
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1046 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1042 = Proto.Construct[]
    cond1043 = match_lookahead_literal(parser, "(", 0)
    while cond1043
        _t1830 = parse_construct(parser)
        item1044 = _t1830
        push!(xs1042, item1044)
        cond1043 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1045 = xs1042
    consume_literal!(parser, ")")
    _t1831 = Proto.Script(constructs=constructs1045)
    result1047 = _t1831
    record_span!(parser, span_start1046, "Script")
    return result1047
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1051 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1833 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1834 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1835 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1836 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1837 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1838 = 1
                            else
                                _t1838 = -1
                            end
                            _t1837 = _t1838
                        end
                        _t1836 = _t1837
                    end
                    _t1835 = _t1836
                end
                _t1834 = _t1835
            end
            _t1833 = _t1834
        end
        _t1832 = _t1833
    else
        _t1832 = -1
    end
    prediction1048 = _t1832
    if prediction1048 == 1
        _t1840 = parse_instruction(parser)
        instruction1050 = _t1840
        _t1841 = Proto.Construct(construct_type=OneOf(:instruction, instruction1050))
        _t1839 = _t1841
    else
        if prediction1048 == 0
            _t1843 = parse_loop(parser)
            loop1049 = _t1843
            _t1844 = Proto.Construct(construct_type=OneOf(:loop, loop1049))
            _t1842 = _t1844
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1839 = _t1842
    end
    result1052 = _t1839
    record_span!(parser, span_start1051, "Construct")
    return result1052
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1056 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1845 = parse_init(parser)
    init1053 = _t1845
    _t1846 = parse_script(parser)
    script1054 = _t1846
    if match_lookahead_literal(parser, "(", 0)
        _t1848 = parse_attrs(parser)
        _t1847 = _t1848
    else
        _t1847 = nothing
    end
    attrs1055 = _t1847
    consume_literal!(parser, ")")
    _t1849 = Proto.Loop(init=init1053, body=script1054, attrs=(!isnothing(attrs1055) ? attrs1055 : Proto.Attribute[]))
    result1057 = _t1849
    record_span!(parser, span_start1056, "Loop")
    return result1057
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1058 = Proto.Instruction[]
    cond1059 = match_lookahead_literal(parser, "(", 0)
    while cond1059
        _t1850 = parse_instruction(parser)
        item1060 = _t1850
        push!(xs1058, item1060)
        cond1059 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1061 = xs1058
    consume_literal!(parser, ")")
    return instructions1061
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1068 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1852 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1853 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1854 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1855 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1856 = 0
                        else
                            _t1856 = -1
                        end
                        _t1855 = _t1856
                    end
                    _t1854 = _t1855
                end
                _t1853 = _t1854
            end
            _t1852 = _t1853
        end
        _t1851 = _t1852
    else
        _t1851 = -1
    end
    prediction1062 = _t1851
    if prediction1062 == 4
        _t1858 = parse_monus_def(parser)
        monus_def1067 = _t1858
        _t1859 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1067))
        _t1857 = _t1859
    else
        if prediction1062 == 3
            _t1861 = parse_monoid_def(parser)
            monoid_def1066 = _t1861
            _t1862 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1066))
            _t1860 = _t1862
        else
            if prediction1062 == 2
                _t1864 = parse_break(parser)
                break1065 = _t1864
                _t1865 = Proto.Instruction(instr_type=OneOf(:var"#break", break1065))
                _t1863 = _t1865
            else
                if prediction1062 == 1
                    _t1867 = parse_upsert(parser)
                    upsert1064 = _t1867
                    _t1868 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1064))
                    _t1866 = _t1868
                else
                    if prediction1062 == 0
                        _t1870 = parse_assign(parser)
                        assign1063 = _t1870
                        _t1871 = Proto.Instruction(instr_type=OneOf(:assign, assign1063))
                        _t1869 = _t1871
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1866 = _t1869
                end
                _t1863 = _t1866
            end
            _t1860 = _t1863
        end
        _t1857 = _t1860
    end
    result1069 = _t1857
    record_span!(parser, span_start1068, "Instruction")
    return result1069
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1073 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1872 = parse_relation_id(parser)
    relation_id1070 = _t1872
    _t1873 = parse_abstraction(parser)
    abstraction1071 = _t1873
    if match_lookahead_literal(parser, "(", 0)
        _t1875 = parse_attrs(parser)
        _t1874 = _t1875
    else
        _t1874 = nothing
    end
    attrs1072 = _t1874
    consume_literal!(parser, ")")
    _t1876 = Proto.Assign(name=relation_id1070, body=abstraction1071, attrs=(!isnothing(attrs1072) ? attrs1072 : Proto.Attribute[]))
    result1074 = _t1876
    record_span!(parser, span_start1073, "Assign")
    return result1074
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1078 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1877 = parse_relation_id(parser)
    relation_id1075 = _t1877
    _t1878 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1076 = _t1878
    if match_lookahead_literal(parser, "(", 0)
        _t1880 = parse_attrs(parser)
        _t1879 = _t1880
    else
        _t1879 = nothing
    end
    attrs1077 = _t1879
    consume_literal!(parser, ")")
    _t1881 = Proto.Upsert(name=relation_id1075, body=abstraction_with_arity1076[1], attrs=(!isnothing(attrs1077) ? attrs1077 : Proto.Attribute[]), value_arity=abstraction_with_arity1076[2])
    result1079 = _t1881
    record_span!(parser, span_start1078, "Upsert")
    return result1079
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1882 = parse_bindings(parser)
    bindings1080 = _t1882
    _t1883 = parse_formula(parser)
    formula1081 = _t1883
    consume_literal!(parser, ")")
    _t1884 = Proto.Abstraction(vars=vcat(bindings1080[1], !isnothing(bindings1080[2]) ? bindings1080[2] : []), value=formula1081)
    return (_t1884, length(bindings1080[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1085 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1885 = parse_relation_id(parser)
    relation_id1082 = _t1885
    _t1886 = parse_abstraction(parser)
    abstraction1083 = _t1886
    if match_lookahead_literal(parser, "(", 0)
        _t1888 = parse_attrs(parser)
        _t1887 = _t1888
    else
        _t1887 = nothing
    end
    attrs1084 = _t1887
    consume_literal!(parser, ")")
    _t1889 = Proto.Break(name=relation_id1082, body=abstraction1083, attrs=(!isnothing(attrs1084) ? attrs1084 : Proto.Attribute[]))
    result1086 = _t1889
    record_span!(parser, span_start1085, "Break")
    return result1086
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1091 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1890 = parse_monoid(parser)
    monoid1087 = _t1890
    _t1891 = parse_relation_id(parser)
    relation_id1088 = _t1891
    _t1892 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1089 = _t1892
    if match_lookahead_literal(parser, "(", 0)
        _t1894 = parse_attrs(parser)
        _t1893 = _t1894
    else
        _t1893 = nothing
    end
    attrs1090 = _t1893
    consume_literal!(parser, ")")
    _t1895 = Proto.MonoidDef(monoid=monoid1087, name=relation_id1088, body=abstraction_with_arity1089[1], attrs=(!isnothing(attrs1090) ? attrs1090 : Proto.Attribute[]), value_arity=abstraction_with_arity1089[2])
    result1092 = _t1895
    record_span!(parser, span_start1091, "MonoidDef")
    return result1092
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1098 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1897 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1898 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1899 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1900 = 2
                    else
                        _t1900 = -1
                    end
                    _t1899 = _t1900
                end
                _t1898 = _t1899
            end
            _t1897 = _t1898
        end
        _t1896 = _t1897
    else
        _t1896 = -1
    end
    prediction1093 = _t1896
    if prediction1093 == 3
        _t1902 = parse_sum_monoid(parser)
        sum_monoid1097 = _t1902
        _t1903 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1097))
        _t1901 = _t1903
    else
        if prediction1093 == 2
            _t1905 = parse_max_monoid(parser)
            max_monoid1096 = _t1905
            _t1906 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1096))
            _t1904 = _t1906
        else
            if prediction1093 == 1
                _t1908 = parse_min_monoid(parser)
                min_monoid1095 = _t1908
                _t1909 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1095))
                _t1907 = _t1909
            else
                if prediction1093 == 0
                    _t1911 = parse_or_monoid(parser)
                    or_monoid1094 = _t1911
                    _t1912 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1094))
                    _t1910 = _t1912
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1907 = _t1910
            end
            _t1904 = _t1907
        end
        _t1901 = _t1904
    end
    result1099 = _t1901
    record_span!(parser, span_start1098, "Monoid")
    return result1099
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1100 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1913 = Proto.OrMonoid()
    result1101 = _t1913
    record_span!(parser, span_start1100, "OrMonoid")
    return result1101
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1103 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1914 = parse_type(parser)
    type1102 = _t1914
    consume_literal!(parser, ")")
    _t1915 = Proto.MinMonoid(var"#type"=type1102)
    result1104 = _t1915
    record_span!(parser, span_start1103, "MinMonoid")
    return result1104
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1106 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1916 = parse_type(parser)
    type1105 = _t1916
    consume_literal!(parser, ")")
    _t1917 = Proto.MaxMonoid(var"#type"=type1105)
    result1107 = _t1917
    record_span!(parser, span_start1106, "MaxMonoid")
    return result1107
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1109 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1918 = parse_type(parser)
    type1108 = _t1918
    consume_literal!(parser, ")")
    _t1919 = Proto.SumMonoid(var"#type"=type1108)
    result1110 = _t1919
    record_span!(parser, span_start1109, "SumMonoid")
    return result1110
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1115 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1920 = parse_monoid(parser)
    monoid1111 = _t1920
    _t1921 = parse_relation_id(parser)
    relation_id1112 = _t1921
    _t1922 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1113 = _t1922
    if match_lookahead_literal(parser, "(", 0)
        _t1924 = parse_attrs(parser)
        _t1923 = _t1924
    else
        _t1923 = nothing
    end
    attrs1114 = _t1923
    consume_literal!(parser, ")")
    _t1925 = Proto.MonusDef(monoid=monoid1111, name=relation_id1112, body=abstraction_with_arity1113[1], attrs=(!isnothing(attrs1114) ? attrs1114 : Proto.Attribute[]), value_arity=abstraction_with_arity1113[2])
    result1116 = _t1925
    record_span!(parser, span_start1115, "MonusDef")
    return result1116
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1121 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1926 = parse_relation_id(parser)
    relation_id1117 = _t1926
    _t1927 = parse_abstraction(parser)
    abstraction1118 = _t1927
    _t1928 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1119 = _t1928
    _t1929 = parse_functional_dependency_values(parser)
    functional_dependency_values1120 = _t1929
    consume_literal!(parser, ")")
    _t1930 = Proto.FunctionalDependency(guard=abstraction1118, keys=functional_dependency_keys1119, values=functional_dependency_values1120)
    _t1931 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1930), name=relation_id1117)
    result1122 = _t1931
    record_span!(parser, span_start1121, "Constraint")
    return result1122
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1123 = Proto.Var[]
    cond1124 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1124
        _t1932 = parse_var(parser)
        item1125 = _t1932
        push!(xs1123, item1125)
        cond1124 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1126 = xs1123
    consume_literal!(parser, ")")
    return vars1126
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1127 = Proto.Var[]
    cond1128 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1128
        _t1933 = parse_var(parser)
        item1129 = _t1933
        push!(xs1127, item1129)
        cond1128 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1130 = xs1127
    consume_literal!(parser, ")")
    return vars1130
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1136 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1935 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1936 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1937 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1938 = 1
                    else
                        _t1938 = -1
                    end
                    _t1937 = _t1938
                end
                _t1936 = _t1937
            end
            _t1935 = _t1936
        end
        _t1934 = _t1935
    else
        _t1934 = -1
    end
    prediction1131 = _t1934
    if prediction1131 == 3
        _t1940 = parse_iceberg_data(parser)
        iceberg_data1135 = _t1940
        _t1941 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1135))
        _t1939 = _t1941
    else
        if prediction1131 == 2
            _t1943 = parse_csv_data(parser)
            csv_data1134 = _t1943
            _t1944 = Proto.Data(data_type=OneOf(:csv_data, csv_data1134))
            _t1942 = _t1944
        else
            if prediction1131 == 1
                _t1946 = parse_betree_relation(parser)
                betree_relation1133 = _t1946
                _t1947 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1133))
                _t1945 = _t1947
            else
                if prediction1131 == 0
                    _t1949 = parse_edb(parser)
                    edb1132 = _t1949
                    _t1950 = Proto.Data(data_type=OneOf(:edb, edb1132))
                    _t1948 = _t1950
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1945 = _t1948
            end
            _t1942 = _t1945
        end
        _t1939 = _t1942
    end
    result1137 = _t1939
    record_span!(parser, span_start1136, "Data")
    return result1137
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1141 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1951 = parse_relation_id(parser)
    relation_id1138 = _t1951
    _t1952 = parse_edb_path(parser)
    edb_path1139 = _t1952
    _t1953 = parse_edb_types(parser)
    edb_types1140 = _t1953
    consume_literal!(parser, ")")
    _t1954 = Proto.EDB(target_id=relation_id1138, path=edb_path1139, types=edb_types1140)
    result1142 = _t1954
    record_span!(parser, span_start1141, "EDB")
    return result1142
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1143 = String[]
    cond1144 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1144
        item1145 = consume_terminal!(parser, "STRING")
        push!(xs1143, item1145)
        cond1144 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1146 = xs1143
    consume_literal!(parser, "]")
    return strings1146
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1147 = Proto.var"#Type"[]
    cond1148 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1148
        _t1955 = parse_type(parser)
        item1149 = _t1955
        push!(xs1147, item1149)
        cond1148 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1150 = xs1147
    consume_literal!(parser, "]")
    return types1150
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1153 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1956 = parse_relation_id(parser)
    relation_id1151 = _t1956
    _t1957 = parse_betree_info(parser)
    betree_info1152 = _t1957
    consume_literal!(parser, ")")
    _t1958 = Proto.BeTreeRelation(name=relation_id1151, relation_info=betree_info1152)
    result1154 = _t1958
    record_span!(parser, span_start1153, "BeTreeRelation")
    return result1154
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1158 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1959 = parse_betree_info_key_types(parser)
    betree_info_key_types1155 = _t1959
    _t1960 = parse_betree_info_value_types(parser)
    betree_info_value_types1156 = _t1960
    _t1961 = parse_config_dict(parser)
    config_dict1157 = _t1961
    consume_literal!(parser, ")")
    _t1962 = construct_betree_info(parser, betree_info_key_types1155, betree_info_value_types1156, config_dict1157)
    result1159 = _t1962
    record_span!(parser, span_start1158, "BeTreeInfo")
    return result1159
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1160 = Proto.var"#Type"[]
    cond1161 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1161
        _t1963 = parse_type(parser)
        item1162 = _t1963
        push!(xs1160, item1162)
        cond1161 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1163 = xs1160
    consume_literal!(parser, ")")
    return types1163
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1164 = Proto.var"#Type"[]
    cond1165 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1165
        _t1964 = parse_type(parser)
        item1166 = _t1964
        push!(xs1164, item1166)
        cond1165 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1167 = xs1164
    consume_literal!(parser, ")")
    return types1167
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1172 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1965 = parse_csvlocator(parser)
    csvlocator1168 = _t1965
    _t1966 = parse_csv_config(parser)
    csv_config1169 = _t1966
    _t1967 = parse_gnf_columns(parser)
    gnf_columns1170 = _t1967
    _t1968 = parse_csv_asof(parser)
    csv_asof1171 = _t1968
    consume_literal!(parser, ")")
    _t1969 = Proto.CSVData(locator=csvlocator1168, config=csv_config1169, columns=gnf_columns1170, asof=csv_asof1171)
    result1173 = _t1969
    record_span!(parser, span_start1172, "CSVData")
    return result1173
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1176 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1971 = parse_csv_locator_paths(parser)
        _t1970 = _t1971
    else
        _t1970 = nothing
    end
    csv_locator_paths1174 = _t1970
    if match_lookahead_literal(parser, "(", 0)
        _t1973 = parse_csv_locator_inline_data(parser)
        _t1972 = _t1973
    else
        _t1972 = nothing
    end
    csv_locator_inline_data1175 = _t1972
    consume_literal!(parser, ")")
    _t1974 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1174) ? csv_locator_paths1174 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1175) ? csv_locator_inline_data1175 : "")))
    result1177 = _t1974
    record_span!(parser, span_start1176, "CSVLocator")
    return result1177
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1178 = String[]
    cond1179 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1179
        item1180 = consume_terminal!(parser, "STRING")
        push!(xs1178, item1180)
        cond1179 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1181 = xs1178
    consume_literal!(parser, ")")
    return strings1181
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1182 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1182
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1184 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1975 = parse_config_dict(parser)
    config_dict1183 = _t1975
    consume_literal!(parser, ")")
    _t1976 = construct_csv_config(parser, config_dict1183)
    result1185 = _t1976
    record_span!(parser, span_start1184, "CSVConfig")
    return result1185
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1186 = Proto.GNFColumn[]
    cond1187 = match_lookahead_literal(parser, "(", 0)
    while cond1187
        _t1977 = parse_gnf_column(parser)
        item1188 = _t1977
        push!(xs1186, item1188)
        cond1187 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1189 = xs1186
    consume_literal!(parser, ")")
    return gnf_columns1189
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1196 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1978 = parse_gnf_column_path(parser)
    gnf_column_path1190 = _t1978
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1980 = parse_relation_id(parser)
        _t1979 = _t1980
    else
        _t1979 = nothing
    end
    relation_id1191 = _t1979
    consume_literal!(parser, "[")
    xs1192 = Proto.var"#Type"[]
    cond1193 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1193
        _t1981 = parse_type(parser)
        item1194 = _t1981
        push!(xs1192, item1194)
        cond1193 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1195 = xs1192
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1982 = Proto.GNFColumn(column_path=gnf_column_path1190, target_id=relation_id1191, types=types1195)
    result1197 = _t1982
    record_span!(parser, span_start1196, "GNFColumn")
    return result1197
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1983 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1984 = 0
        else
            _t1984 = -1
        end
        _t1983 = _t1984
    end
    prediction1198 = _t1983
    if prediction1198 == 1
        consume_literal!(parser, "[")
        xs1200 = String[]
        cond1201 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1201
            item1202 = consume_terminal!(parser, "STRING")
            push!(xs1200, item1202)
            cond1201 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1203 = xs1200
        consume_literal!(parser, "]")
        _t1985 = strings1203
    else
        if prediction1198 == 0
            string1199 = consume_terminal!(parser, "STRING")
            _t1986 = String[string1199]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1985 = _t1986
    end
    return _t1985
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1204 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1204
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1212 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1987 = parse_iceberg_locator(parser)
    iceberg_locator1205 = _t1987
    _t1988 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1206 = _t1988
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t1990 = parse_gnf_columns(parser)
        _t1989 = _t1990
    else
        _t1989 = nothing
    end
    gnf_columns1207 = _t1989
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "full_table", 1))
        _t1992 = parse_full_table(parser)
        _t1991 = _t1992
    else
        _t1991 = nothing
    end
    full_table1208 = _t1991
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1994 = parse_iceberg_from_snapshot(parser)
        _t1993 = _t1994
    else
        _t1993 = nothing
    end
    iceberg_from_snapshot1209 = _t1993
    if match_lookahead_literal(parser, "(", 0)
        _t1996 = parse_iceberg_to_snapshot(parser)
        _t1995 = _t1996
    else
        _t1995 = nothing
    end
    iceberg_to_snapshot1210 = _t1995
    _t1997 = parse_boolean_value(parser)
    boolean_value1211 = _t1997
    consume_literal!(parser, ")")
    _t1998 = construct_iceberg_data(parser, iceberg_locator1205, iceberg_catalog_config1206, gnf_columns1207, full_table1208, iceberg_from_snapshot1209, iceberg_to_snapshot1210, boolean_value1211)
    result1213 = _t1998
    record_span!(parser, span_start1212, "IcebergData")
    return result1213
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1217 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t1999 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1214 = _t1999
    _t2000 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1215 = _t2000
    _t2001 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1216 = _t2001
    consume_literal!(parser, ")")
    _t2002 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1214, namespace=iceberg_locator_namespace1215, warehouse=iceberg_locator_warehouse1216)
    result1218 = _t2002
    record_span!(parser, span_start1217, "IcebergLocator")
    return result1218
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1219 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1219
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1220 = String[]
    cond1221 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1221
        item1222 = consume_terminal!(parser, "STRING")
        push!(xs1220, item1222)
        cond1221 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1223 = xs1220
    consume_literal!(parser, ")")
    return strings1223
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1224 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1224
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1229 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2003 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1225 = _t2003
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2005 = parse_iceberg_catalog_config_scope(parser)
        _t2004 = _t2005
    else
        _t2004 = nothing
    end
    iceberg_catalog_config_scope1226 = _t2004
    _t2006 = parse_iceberg_properties(parser)
    iceberg_properties1227 = _t2006
    _t2007 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1228 = _t2007
    consume_literal!(parser, ")")
    _t2008 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1225, iceberg_catalog_config_scope1226, iceberg_properties1227, iceberg_auth_properties1228)
    result1230 = _t2008
    record_span!(parser, span_start1229, "IcebergCatalogConfig")
    return result1230
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1231 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1231
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1232 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1232
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1233 = Tuple{String, String}[]
    cond1234 = match_lookahead_literal(parser, "(", 0)
    while cond1234
        _t2009 = parse_iceberg_property_entry(parser)
        item1235 = _t2009
        push!(xs1233, item1235)
        cond1234 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1236 = xs1233
    consume_literal!(parser, ")")
    return iceberg_property_entrys1236
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1237 = consume_terminal!(parser, "STRING")
    string_31238 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1237, string_31238,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1239 = Tuple{String, String}[]
    cond1240 = match_lookahead_literal(parser, "(", 0)
    while cond1240
        _t2010 = parse_iceberg_masked_property_entry(parser)
        item1241 = _t2010
        push!(xs1239, item1241)
        cond1240 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1242 = xs1239
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1242
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1243 = consume_terminal!(parser, "STRING")
    string_31244 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1243, string_31244,)
end

function parse_full_table(parser::ParserState)::Proto.IcebergTarget
    span_start1250 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "full_table")
    _t2011 = parse_relation_id(parser)
    relation_id1245 = _t2011
    consume_literal!(parser, "[")
    xs1246 = Proto.var"#Type"[]
    cond1247 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1247
        _t2012 = parse_type(parser)
        item1248 = _t2012
        push!(xs1246, item1248)
        cond1247 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1249 = xs1246
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2013 = Proto.IcebergTarget(target_id=relation_id1245, types=types1249)
    result1251 = _t2013
    record_span!(parser, span_start1250, "IcebergTarget")
    return result1251
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1252 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1252
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1253 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1253
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1255 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2014 = parse_fragment_id(parser)
    fragment_id1254 = _t2014
    consume_literal!(parser, ")")
    _t2015 = Proto.Undefine(fragment_id=fragment_id1254)
    result1256 = _t2015
    record_span!(parser, span_start1255, "Undefine")
    return result1256
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1261 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1257 = Proto.RelationId[]
    cond1258 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1258
        _t2016 = parse_relation_id(parser)
        item1259 = _t2016
        push!(xs1257, item1259)
        cond1258 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1260 = xs1257
    consume_literal!(parser, ")")
    _t2017 = Proto.Context(relations=relation_ids1260)
    result1262 = _t2017
    record_span!(parser, span_start1261, "Context")
    return result1262
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1268 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2018 = parse_edb_path(parser)
    edb_path1263 = _t2018
    xs1264 = Proto.SnapshotMapping[]
    cond1265 = match_lookahead_literal(parser, "[", 0)
    while cond1265
        _t2019 = parse_snapshot_mapping(parser)
        item1266 = _t2019
        push!(xs1264, item1266)
        cond1265 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1267 = xs1264
    consume_literal!(parser, ")")
    _t2020 = Proto.Snapshot(mappings=snapshot_mappings1267, prefix=edb_path1263)
    result1269 = _t2020
    record_span!(parser, span_start1268, "Snapshot")
    return result1269
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1272 = span_start(parser)
    _t2021 = parse_edb_path(parser)
    edb_path1270 = _t2021
    _t2022 = parse_relation_id(parser)
    relation_id1271 = _t2022
    _t2023 = Proto.SnapshotMapping(destination_path=edb_path1270, source_relation=relation_id1271)
    result1273 = _t2023
    record_span!(parser, span_start1272, "SnapshotMapping")
    return result1273
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1274 = Proto.Read[]
    cond1275 = match_lookahead_literal(parser, "(", 0)
    while cond1275
        _t2024 = parse_read(parser)
        item1276 = _t2024
        push!(xs1274, item1276)
        cond1275 = match_lookahead_literal(parser, "(", 0)
    end
    reads1277 = xs1274
    consume_literal!(parser, ")")
    return reads1277
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1284 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2026 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2027 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2028 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2029 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2030 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2031 = 3
                            else
                                _t2031 = -1
                            end
                            _t2030 = _t2031
                        end
                        _t2029 = _t2030
                    end
                    _t2028 = _t2029
                end
                _t2027 = _t2028
            end
            _t2026 = _t2027
        end
        _t2025 = _t2026
    else
        _t2025 = -1
    end
    prediction1278 = _t2025
    if prediction1278 == 4
        _t2033 = parse_export(parser)
        export1283 = _t2033
        _t2034 = Proto.Read(read_type=OneOf(:var"#export", export1283))
        _t2032 = _t2034
    else
        if prediction1278 == 3
            _t2036 = parse_abort(parser)
            abort1282 = _t2036
            _t2037 = Proto.Read(read_type=OneOf(:abort, abort1282))
            _t2035 = _t2037
        else
            if prediction1278 == 2
                _t2039 = parse_what_if(parser)
                what_if1281 = _t2039
                _t2040 = Proto.Read(read_type=OneOf(:what_if, what_if1281))
                _t2038 = _t2040
            else
                if prediction1278 == 1
                    _t2042 = parse_output(parser)
                    output1280 = _t2042
                    _t2043 = Proto.Read(read_type=OneOf(:output, output1280))
                    _t2041 = _t2043
                else
                    if prediction1278 == 0
                        _t2045 = parse_demand(parser)
                        demand1279 = _t2045
                        _t2046 = Proto.Read(read_type=OneOf(:demand, demand1279))
                        _t2044 = _t2046
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2041 = _t2044
                end
                _t2038 = _t2041
            end
            _t2035 = _t2038
        end
        _t2032 = _t2035
    end
    result1285 = _t2032
    record_span!(parser, span_start1284, "Read")
    return result1285
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1287 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2047 = parse_relation_id(parser)
    relation_id1286 = _t2047
    consume_literal!(parser, ")")
    _t2048 = Proto.Demand(relation_id=relation_id1286)
    result1288 = _t2048
    record_span!(parser, span_start1287, "Demand")
    return result1288
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1291 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2049 = parse_name(parser)
    name1289 = _t2049
    _t2050 = parse_relation_id(parser)
    relation_id1290 = _t2050
    consume_literal!(parser, ")")
    _t2051 = Proto.Output(name=name1289, relation_id=relation_id1290)
    result1292 = _t2051
    record_span!(parser, span_start1291, "Output")
    return result1292
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1295 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2052 = parse_name(parser)
    name1293 = _t2052
    _t2053 = parse_epoch(parser)
    epoch1294 = _t2053
    consume_literal!(parser, ")")
    _t2054 = Proto.WhatIf(branch=name1293, epoch=epoch1294)
    result1296 = _t2054
    record_span!(parser, span_start1295, "WhatIf")
    return result1296
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1299 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2056 = parse_name(parser)
        _t2055 = _t2056
    else
        _t2055 = nothing
    end
    name1297 = _t2055
    _t2057 = parse_relation_id(parser)
    relation_id1298 = _t2057
    consume_literal!(parser, ")")
    _t2058 = Proto.Abort(name=(!isnothing(name1297) ? name1297 : "abort"), relation_id=relation_id1298)
    result1300 = _t2058
    record_span!(parser, span_start1299, "Abort")
    return result1300
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1304 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2060 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
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
    prediction1301 = _t2059
    if prediction1301 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2063 = parse_export_iceberg_config(parser)
        export_iceberg_config1303 = _t2063
        consume_literal!(parser, ")")
        _t2064 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1303))
        _t2062 = _t2064
    else
        if prediction1301 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2066 = parse_export_csv_config(parser)
            export_csv_config1302 = _t2066
            consume_literal!(parser, ")")
            _t2067 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1302))
            _t2065 = _t2067
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2062 = _t2065
    end
    result1305 = _t2062
    record_span!(parser, span_start1304, "Export")
    return result1305
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1313 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2069 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2070 = 1
            else
                _t2070 = -1
            end
            _t2069 = _t2070
        end
        _t2068 = _t2069
    else
        _t2068 = -1
    end
    prediction1306 = _t2068
    if prediction1306 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2072 = parse_export_csv_path(parser)
        export_csv_path1310 = _t2072
        _t2073 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1311 = _t2073
        _t2074 = parse_config_dict(parser)
        config_dict1312 = _t2074
        consume_literal!(parser, ")")
        _t2075 = construct_export_csv_config(parser, export_csv_path1310, export_csv_columns_list1311, config_dict1312)
        _t2071 = _t2075
    else
        if prediction1306 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2077 = parse_export_csv_path(parser)
            export_csv_path1307 = _t2077
            _t2078 = parse_export_csv_source(parser)
            export_csv_source1308 = _t2078
            _t2079 = parse_csv_config(parser)
            csv_config1309 = _t2079
            consume_literal!(parser, ")")
            _t2080 = construct_export_csv_config_with_source(parser, export_csv_path1307, export_csv_source1308, csv_config1309)
            _t2076 = _t2080
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2071 = _t2076
    end
    result1314 = _t2071
    record_span!(parser, span_start1313, "ExportCSVConfig")
    return result1314
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1315 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1315
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1322 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2082 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2083 = 0
            else
                _t2083 = -1
            end
            _t2082 = _t2083
        end
        _t2081 = _t2082
    else
        _t2081 = -1
    end
    prediction1316 = _t2081
    if prediction1316 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2085 = parse_relation_id(parser)
        relation_id1321 = _t2085
        consume_literal!(parser, ")")
        _t2086 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1321))
        _t2084 = _t2086
    else
        if prediction1316 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1317 = Proto.ExportCSVColumn[]
            cond1318 = match_lookahead_literal(parser, "(", 0)
            while cond1318
                _t2088 = parse_export_csv_column(parser)
                item1319 = _t2088
                push!(xs1317, item1319)
                cond1318 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1320 = xs1317
            consume_literal!(parser, ")")
            _t2089 = Proto.ExportCSVColumns(columns=export_csv_columns1320)
            _t2090 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2089))
            _t2087 = _t2090
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2084 = _t2087
    end
    result1323 = _t2084
    record_span!(parser, span_start1322, "ExportCSVSource")
    return result1323
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1326 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1324 = consume_terminal!(parser, "STRING")
    _t2091 = parse_relation_id(parser)
    relation_id1325 = _t2091
    consume_literal!(parser, ")")
    _t2092 = Proto.ExportCSVColumn(column_name=string1324, column_data=relation_id1325)
    result1327 = _t2092
    record_span!(parser, span_start1326, "ExportCSVColumn")
    return result1327
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1328 = Proto.ExportCSVColumn[]
    cond1329 = match_lookahead_literal(parser, "(", 0)
    while cond1329
        _t2093 = parse_export_csv_column(parser)
        item1330 = _t2093
        push!(xs1328, item1330)
        cond1329 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1331 = xs1328
    consume_literal!(parser, ")")
    return export_csv_columns1331
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1337 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2094 = parse_iceberg_locator(parser)
    iceberg_locator1332 = _t2094
    _t2095 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1333 = _t2095
    _t2096 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1334 = _t2096
    _t2097 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1335 = _t2097
    if match_lookahead_literal(parser, "{", 0)
        _t2099 = parse_config_dict(parser)
        _t2098 = _t2099
    else
        _t2098 = nothing
    end
    config_dict1336 = _t2098
    consume_literal!(parser, ")")
    _t2100 = construct_export_iceberg_config_full(parser, iceberg_locator1332, iceberg_catalog_config1333, export_iceberg_table_def1334, iceberg_table_properties1335, config_dict1336)
    result1338 = _t2100
    record_span!(parser, span_start1337, "ExportIcebergConfig")
    return result1338
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1340 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2101 = parse_relation_id(parser)
    relation_id1339 = _t2101
    consume_literal!(parser, ")")
    result1341 = relation_id1339
    record_span!(parser, span_start1340, "RelationId")
    return result1341
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1342 = Tuple{String, String}[]
    cond1343 = match_lookahead_literal(parser, "(", 0)
    while cond1343
        _t2102 = parse_iceberg_property_entry(parser)
        item1344 = _t2102
        push!(xs1342, item1344)
        cond1343 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1345 = xs1342
    consume_literal!(parser, ")")
    return iceberg_property_entrys1345
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
