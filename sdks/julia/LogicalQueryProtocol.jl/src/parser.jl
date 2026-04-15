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

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2151 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2151
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, columns::Vector{Proto.ExportColumn}, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2152 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2152
    _t2153 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2153
    _t2154 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2154
    table_props = Dict(table_property_pairs)
    _t2155 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2155
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start680 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1349 = parse_configure(parser)
        _t1348 = _t1349
    else
        _t1348 = nothing
    end
    configure674 = _t1348
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1351 = parse_sync(parser)
        _t1350 = _t1351
    else
        _t1350 = nothing
    end
    sync675 = _t1350
    xs676 = Proto.Epoch[]
    cond677 = match_lookahead_literal(parser, "(", 0)
    while cond677
        _t1352 = parse_epoch(parser)
        item678 = _t1352
        push!(xs676, item678)
        cond677 = match_lookahead_literal(parser, "(", 0)
    end
    epochs679 = xs676
    consume_literal!(parser, ")")
    _t1353 = default_configure(parser)
    _t1354 = Proto.Transaction(epochs=epochs679, configure=(!isnothing(configure674) ? configure674 : _t1353), sync=sync675)
    result681 = _t1354
    record_span!(parser, span_start680, "Transaction")
    return result681
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start683 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1355 = parse_config_dict(parser)
    config_dict682 = _t1355
    consume_literal!(parser, ")")
    _t1356 = construct_configure(parser, config_dict682)
    result684 = _t1356
    record_span!(parser, span_start683, "Configure")
    return result684
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs685 = Tuple{String, Proto.Value}[]
    cond686 = match_lookahead_literal(parser, ":", 0)
    while cond686
        _t1357 = parse_config_key_value(parser)
        item687 = _t1357
        push!(xs685, item687)
        cond686 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values688 = xs685
    consume_literal!(parser, "}")
    return config_key_values688
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol689 = consume_terminal!(parser, "SYMBOL")
    _t1358 = parse_raw_value(parser)
    raw_value690 = _t1358
    return (symbol689, raw_value690,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start704 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1359 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1360 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1361 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1363 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1364 = 0
                        else
                            _t1364 = -1
                        end
                        _t1363 = _t1364
                    end
                    _t1362 = _t1363
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1365 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1366 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1367 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1368 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1369 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1370 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1371 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1372 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1373 = 10
                                                    else
                                                        _t1373 = -1
                                                    end
                                                    _t1372 = _t1373
                                                end
                                                _t1371 = _t1372
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
                    _t1362 = _t1365
                end
                _t1361 = _t1362
            end
            _t1360 = _t1361
        end
        _t1359 = _t1360
    end
    prediction691 = _t1359
    if prediction691 == 12
        _t1375 = parse_boolean_value(parser)
        boolean_value703 = _t1375
        _t1376 = Proto.Value(value=OneOf(:boolean_value, boolean_value703))
        _t1374 = _t1376
    else
        if prediction691 == 11
            consume_literal!(parser, "missing")
            _t1378 = Proto.MissingValue()
            _t1379 = Proto.Value(value=OneOf(:missing_value, _t1378))
            _t1377 = _t1379
        else
            if prediction691 == 10
                decimal702 = consume_terminal!(parser, "DECIMAL")
                _t1381 = Proto.Value(value=OneOf(:decimal_value, decimal702))
                _t1380 = _t1381
            else
                if prediction691 == 9
                    int128701 = consume_terminal!(parser, "INT128")
                    _t1383 = Proto.Value(value=OneOf(:int128_value, int128701))
                    _t1382 = _t1383
                else
                    if prediction691 == 8
                        uint128700 = consume_terminal!(parser, "UINT128")
                        _t1385 = Proto.Value(value=OneOf(:uint128_value, uint128700))
                        _t1384 = _t1385
                    else
                        if prediction691 == 7
                            uint32699 = consume_terminal!(parser, "UINT32")
                            _t1387 = Proto.Value(value=OneOf(:uint32_value, uint32699))
                            _t1386 = _t1387
                        else
                            if prediction691 == 6
                                float698 = consume_terminal!(parser, "FLOAT")
                                _t1389 = Proto.Value(value=OneOf(:float_value, float698))
                                _t1388 = _t1389
                            else
                                if prediction691 == 5
                                    float32697 = consume_terminal!(parser, "FLOAT32")
                                    _t1391 = Proto.Value(value=OneOf(:float32_value, float32697))
                                    _t1390 = _t1391
                                else
                                    if prediction691 == 4
                                        int696 = consume_terminal!(parser, "INT")
                                        _t1393 = Proto.Value(value=OneOf(:int_value, int696))
                                        _t1392 = _t1393
                                    else
                                        if prediction691 == 3
                                            int32695 = consume_terminal!(parser, "INT32")
                                            _t1395 = Proto.Value(value=OneOf(:int32_value, int32695))
                                            _t1394 = _t1395
                                        else
                                            if prediction691 == 2
                                                string694 = consume_terminal!(parser, "STRING")
                                                _t1397 = Proto.Value(value=OneOf(:string_value, string694))
                                                _t1396 = _t1397
                                            else
                                                if prediction691 == 1
                                                    _t1399 = parse_raw_datetime(parser)
                                                    raw_datetime693 = _t1399
                                                    _t1400 = Proto.Value(value=OneOf(:datetime_value, raw_datetime693))
                                                    _t1398 = _t1400
                                                else
                                                    if prediction691 == 0
                                                        _t1402 = parse_raw_date(parser)
                                                        raw_date692 = _t1402
                                                        _t1403 = Proto.Value(value=OneOf(:date_value, raw_date692))
                                                        _t1401 = _t1403
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1398 = _t1401
                                                end
                                                _t1396 = _t1398
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
            _t1377 = _t1380
        end
        _t1374 = _t1377
    end
    result705 = _t1374
    record_span!(parser, span_start704, "Value")
    return result705
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start709 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int706 = consume_terminal!(parser, "INT")
    int_3707 = consume_terminal!(parser, "INT")
    int_4708 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1404 = Proto.DateValue(year=Int32(int706), month=Int32(int_3707), day=Int32(int_4708))
    result710 = _t1404
    record_span!(parser, span_start709, "DateValue")
    return result710
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start718 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int711 = consume_terminal!(parser, "INT")
    int_3712 = consume_terminal!(parser, "INT")
    int_4713 = consume_terminal!(parser, "INT")
    int_5714 = consume_terminal!(parser, "INT")
    int_6715 = consume_terminal!(parser, "INT")
    int_7716 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1405 = consume_terminal!(parser, "INT")
    else
        _t1405 = nothing
    end
    int_8717 = _t1405
    consume_literal!(parser, ")")
    _t1406 = Proto.DateTimeValue(year=Int32(int711), month=Int32(int_3712), day=Int32(int_4713), hour=Int32(int_5714), minute=Int32(int_6715), second=Int32(int_7716), microsecond=Int32((!isnothing(int_8717) ? int_8717 : 0)))
    result719 = _t1406
    record_span!(parser, span_start718, "DateTimeValue")
    return result719
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1407 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1408 = 1
        else
            _t1408 = -1
        end
        _t1407 = _t1408
    end
    prediction720 = _t1407
    if prediction720 == 1
        consume_literal!(parser, "false")
        _t1409 = false
    else
        if prediction720 == 0
            consume_literal!(parser, "true")
            _t1410 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1409 = _t1410
    end
    return _t1409
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start725 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs721 = Proto.FragmentId[]
    cond722 = match_lookahead_literal(parser, ":", 0)
    while cond722
        _t1411 = parse_fragment_id(parser)
        item723 = _t1411
        push!(xs721, item723)
        cond722 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids724 = xs721
    consume_literal!(parser, ")")
    _t1412 = Proto.Sync(fragments=fragment_ids724)
    result726 = _t1412
    record_span!(parser, span_start725, "Sync")
    return result726
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start728 = span_start(parser)
    consume_literal!(parser, ":")
    symbol727 = consume_terminal!(parser, "SYMBOL")
    result729 = Proto.FragmentId(Vector{UInt8}(symbol727))
    record_span!(parser, span_start728, "FragmentId")
    return result729
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start732 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1414 = parse_epoch_writes(parser)
        _t1413 = _t1414
    else
        _t1413 = nothing
    end
    epoch_writes730 = _t1413
    if match_lookahead_literal(parser, "(", 0)
        _t1416 = parse_epoch_reads(parser)
        _t1415 = _t1416
    else
        _t1415 = nothing
    end
    epoch_reads731 = _t1415
    consume_literal!(parser, ")")
    _t1417 = Proto.Epoch(writes=(!isnothing(epoch_writes730) ? epoch_writes730 : Proto.Write[]), reads=(!isnothing(epoch_reads731) ? epoch_reads731 : Proto.Read[]))
    result733 = _t1417
    record_span!(parser, span_start732, "Epoch")
    return result733
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs734 = Proto.Write[]
    cond735 = match_lookahead_literal(parser, "(", 0)
    while cond735
        _t1418 = parse_write(parser)
        item736 = _t1418
        push!(xs734, item736)
        cond735 = match_lookahead_literal(parser, "(", 0)
    end
    writes737 = xs734
    consume_literal!(parser, ")")
    return writes737
end

function parse_write(parser::ParserState)::Proto.Write
    span_start743 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1420 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1421 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1422 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1423 = 2
                    else
                        _t1423 = -1
                    end
                    _t1422 = _t1423
                end
                _t1421 = _t1422
            end
            _t1420 = _t1421
        end
        _t1419 = _t1420
    else
        _t1419 = -1
    end
    prediction738 = _t1419
    if prediction738 == 3
        _t1425 = parse_snapshot(parser)
        snapshot742 = _t1425
        _t1426 = Proto.Write(write_type=OneOf(:snapshot, snapshot742))
        _t1424 = _t1426
    else
        if prediction738 == 2
            _t1428 = parse_context(parser)
            context741 = _t1428
            _t1429 = Proto.Write(write_type=OneOf(:context, context741))
            _t1427 = _t1429
        else
            if prediction738 == 1
                _t1431 = parse_undefine(parser)
                undefine740 = _t1431
                _t1432 = Proto.Write(write_type=OneOf(:undefine, undefine740))
                _t1430 = _t1432
            else
                if prediction738 == 0
                    _t1434 = parse_define(parser)
                    define739 = _t1434
                    _t1435 = Proto.Write(write_type=OneOf(:define, define739))
                    _t1433 = _t1435
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1430 = _t1433
            end
            _t1427 = _t1430
        end
        _t1424 = _t1427
    end
    result744 = _t1424
    record_span!(parser, span_start743, "Write")
    return result744
end

function parse_define(parser::ParserState)::Proto.Define
    span_start746 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1436 = parse_fragment(parser)
    fragment745 = _t1436
    consume_literal!(parser, ")")
    _t1437 = Proto.Define(fragment=fragment745)
    result747 = _t1437
    record_span!(parser, span_start746, "Define")
    return result747
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start753 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1438 = parse_new_fragment_id(parser)
    new_fragment_id748 = _t1438
    xs749 = Proto.Declaration[]
    cond750 = match_lookahead_literal(parser, "(", 0)
    while cond750
        _t1439 = parse_declaration(parser)
        item751 = _t1439
        push!(xs749, item751)
        cond750 = match_lookahead_literal(parser, "(", 0)
    end
    declarations752 = xs749
    consume_literal!(parser, ")")
    result754 = construct_fragment(parser, new_fragment_id748, declarations752)
    record_span!(parser, span_start753, "Fragment")
    return result754
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start756 = span_start(parser)
    _t1440 = parse_fragment_id(parser)
    fragment_id755 = _t1440
    start_fragment!(parser, fragment_id755)
    result757 = fragment_id755
    record_span!(parser, span_start756, "FragmentId")
    return result757
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start763 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1442 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1443 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1444 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1445 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1446 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1447 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1448 = 1
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
    else
        _t1441 = -1
    end
    prediction758 = _t1441
    if prediction758 == 3
        _t1450 = parse_data(parser)
        data762 = _t1450
        _t1451 = Proto.Declaration(declaration_type=OneOf(:data, data762))
        _t1449 = _t1451
    else
        if prediction758 == 2
            _t1453 = parse_constraint(parser)
            constraint761 = _t1453
            _t1454 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint761))
            _t1452 = _t1454
        else
            if prediction758 == 1
                _t1456 = parse_algorithm(parser)
                algorithm760 = _t1456
                _t1457 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm760))
                _t1455 = _t1457
            else
                if prediction758 == 0
                    _t1459 = parse_def(parser)
                    def759 = _t1459
                    _t1460 = Proto.Declaration(declaration_type=OneOf(:def, def759))
                    _t1458 = _t1460
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1455 = _t1458
            end
            _t1452 = _t1455
        end
        _t1449 = _t1452
    end
    result764 = _t1449
    record_span!(parser, span_start763, "Declaration")
    return result764
end

function parse_def(parser::ParserState)::Proto.Def
    span_start768 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1461 = parse_relation_id(parser)
    relation_id765 = _t1461
    _t1462 = parse_abstraction(parser)
    abstraction766 = _t1462
    if match_lookahead_literal(parser, "(", 0)
        _t1464 = parse_attrs(parser)
        _t1463 = _t1464
    else
        _t1463 = nothing
    end
    attrs767 = _t1463
    consume_literal!(parser, ")")
    _t1465 = Proto.Def(name=relation_id765, body=abstraction766, attrs=(!isnothing(attrs767) ? attrs767 : Proto.Attribute[]))
    result769 = _t1465
    record_span!(parser, span_start768, "Def")
    return result769
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start773 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1466 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1467 = 1
        else
            _t1467 = -1
        end
        _t1466 = _t1467
    end
    prediction770 = _t1466
    if prediction770 == 1
        uint128772 = consume_terminal!(parser, "UINT128")
        _t1468 = Proto.RelationId(uint128772.low, uint128772.high)
    else
        if prediction770 == 0
            consume_literal!(parser, ":")
            symbol771 = consume_terminal!(parser, "SYMBOL")
            _t1469 = relation_id_from_string(parser, symbol771)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1468 = _t1469
    end
    result774 = _t1468
    record_span!(parser, span_start773, "RelationId")
    return result774
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start777 = span_start(parser)
    consume_literal!(parser, "(")
    _t1470 = parse_bindings(parser)
    bindings775 = _t1470
    _t1471 = parse_formula(parser)
    formula776 = _t1471
    consume_literal!(parser, ")")
    _t1472 = Proto.Abstraction(vars=vcat(bindings775[1], !isnothing(bindings775[2]) ? bindings775[2] : []), value=formula776)
    result778 = _t1472
    record_span!(parser, span_start777, "Abstraction")
    return result778
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs779 = Proto.Binding[]
    cond780 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond780
        _t1473 = parse_binding(parser)
        item781 = _t1473
        push!(xs779, item781)
        cond780 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings782 = xs779
    if match_lookahead_literal(parser, "|", 0)
        _t1475 = parse_value_bindings(parser)
        _t1474 = _t1475
    else
        _t1474 = nothing
    end
    value_bindings783 = _t1474
    consume_literal!(parser, "]")
    return (bindings782, (!isnothing(value_bindings783) ? value_bindings783 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start786 = span_start(parser)
    symbol784 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1476 = parse_type(parser)
    type785 = _t1476
    _t1477 = Proto.Var(name=symbol784)
    _t1478 = Proto.Binding(var=_t1477, var"#type"=type785)
    result787 = _t1478
    record_span!(parser, span_start786, "Binding")
    return result787
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start803 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1479 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1480 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1481 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1482 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1483 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1484 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1485 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1486 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1487 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1488 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1489 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1490 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1491 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1492 = 9
                                                        else
                                                            _t1492 = -1
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
                _t1481 = _t1482
            end
            _t1480 = _t1481
        end
        _t1479 = _t1480
    end
    prediction788 = _t1479
    if prediction788 == 13
        _t1494 = parse_uint32_type(parser)
        uint32_type802 = _t1494
        _t1495 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type802))
        _t1493 = _t1495
    else
        if prediction788 == 12
            _t1497 = parse_float32_type(parser)
            float32_type801 = _t1497
            _t1498 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type801))
            _t1496 = _t1498
        else
            if prediction788 == 11
                _t1500 = parse_int32_type(parser)
                int32_type800 = _t1500
                _t1501 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type800))
                _t1499 = _t1501
            else
                if prediction788 == 10
                    _t1503 = parse_boolean_type(parser)
                    boolean_type799 = _t1503
                    _t1504 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type799))
                    _t1502 = _t1504
                else
                    if prediction788 == 9
                        _t1506 = parse_decimal_type(parser)
                        decimal_type798 = _t1506
                        _t1507 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type798))
                        _t1505 = _t1507
                    else
                        if prediction788 == 8
                            _t1509 = parse_missing_type(parser)
                            missing_type797 = _t1509
                            _t1510 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type797))
                            _t1508 = _t1510
                        else
                            if prediction788 == 7
                                _t1512 = parse_datetime_type(parser)
                                datetime_type796 = _t1512
                                _t1513 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type796))
                                _t1511 = _t1513
                            else
                                if prediction788 == 6
                                    _t1515 = parse_date_type(parser)
                                    date_type795 = _t1515
                                    _t1516 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type795))
                                    _t1514 = _t1516
                                else
                                    if prediction788 == 5
                                        _t1518 = parse_int128_type(parser)
                                        int128_type794 = _t1518
                                        _t1519 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type794))
                                        _t1517 = _t1519
                                    else
                                        if prediction788 == 4
                                            _t1521 = parse_uint128_type(parser)
                                            uint128_type793 = _t1521
                                            _t1522 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type793))
                                            _t1520 = _t1522
                                        else
                                            if prediction788 == 3
                                                _t1524 = parse_float_type(parser)
                                                float_type792 = _t1524
                                                _t1525 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type792))
                                                _t1523 = _t1525
                                            else
                                                if prediction788 == 2
                                                    _t1527 = parse_int_type(parser)
                                                    int_type791 = _t1527
                                                    _t1528 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type791))
                                                    _t1526 = _t1528
                                                else
                                                    if prediction788 == 1
                                                        _t1530 = parse_string_type(parser)
                                                        string_type790 = _t1530
                                                        _t1531 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type790))
                                                        _t1529 = _t1531
                                                    else
                                                        if prediction788 == 0
                                                            _t1533 = parse_unspecified_type(parser)
                                                            unspecified_type789 = _t1533
                                                            _t1534 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type789))
                                                            _t1532 = _t1534
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1529 = _t1532
                                                    end
                                                    _t1526 = _t1529
                                                end
                                                _t1523 = _t1526
                                            end
                                            _t1520 = _t1523
                                        end
                                        _t1517 = _t1520
                                    end
                                    _t1514 = _t1517
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
    result804 = _t1493
    record_span!(parser, span_start803, "Type")
    return result804
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start805 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1535 = Proto.UnspecifiedType()
    result806 = _t1535
    record_span!(parser, span_start805, "UnspecifiedType")
    return result806
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start807 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1536 = Proto.StringType()
    result808 = _t1536
    record_span!(parser, span_start807, "StringType")
    return result808
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start809 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1537 = Proto.IntType()
    result810 = _t1537
    record_span!(parser, span_start809, "IntType")
    return result810
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start811 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1538 = Proto.FloatType()
    result812 = _t1538
    record_span!(parser, span_start811, "FloatType")
    return result812
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start813 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1539 = Proto.UInt128Type()
    result814 = _t1539
    record_span!(parser, span_start813, "UInt128Type")
    return result814
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start815 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1540 = Proto.Int128Type()
    result816 = _t1540
    record_span!(parser, span_start815, "Int128Type")
    return result816
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start817 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1541 = Proto.DateType()
    result818 = _t1541
    record_span!(parser, span_start817, "DateType")
    return result818
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start819 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1542 = Proto.DateTimeType()
    result820 = _t1542
    record_span!(parser, span_start819, "DateTimeType")
    return result820
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start821 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1543 = Proto.MissingType()
    result822 = _t1543
    record_span!(parser, span_start821, "MissingType")
    return result822
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start825 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int823 = consume_terminal!(parser, "INT")
    int_3824 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1544 = Proto.DecimalType(precision=Int32(int823), scale=Int32(int_3824))
    result826 = _t1544
    record_span!(parser, span_start825, "DecimalType")
    return result826
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start827 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1545 = Proto.BooleanType()
    result828 = _t1545
    record_span!(parser, span_start827, "BooleanType")
    return result828
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start829 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1546 = Proto.Int32Type()
    result830 = _t1546
    record_span!(parser, span_start829, "Int32Type")
    return result830
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start831 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1547 = Proto.Float32Type()
    result832 = _t1547
    record_span!(parser, span_start831, "Float32Type")
    return result832
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start833 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1548 = Proto.UInt32Type()
    result834 = _t1548
    record_span!(parser, span_start833, "UInt32Type")
    return result834
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs835 = Proto.Binding[]
    cond836 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond836
        _t1549 = parse_binding(parser)
        item837 = _t1549
        push!(xs835, item837)
        cond836 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings838 = xs835
    return bindings838
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start853 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1551 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1552 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1553 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1554 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1555 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1556 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1557 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1558 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1559 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1560 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1561 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1562 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1563 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1564 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1565 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1566 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1567 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1568 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1569 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1570 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1571 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1572 = 10
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
    else
        _t1550 = -1
    end
    prediction839 = _t1550
    if prediction839 == 12
        _t1574 = parse_cast(parser)
        cast852 = _t1574
        _t1575 = Proto.Formula(formula_type=OneOf(:cast, cast852))
        _t1573 = _t1575
    else
        if prediction839 == 11
            _t1577 = parse_rel_atom(parser)
            rel_atom851 = _t1577
            _t1578 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom851))
            _t1576 = _t1578
        else
            if prediction839 == 10
                _t1580 = parse_primitive(parser)
                primitive850 = _t1580
                _t1581 = Proto.Formula(formula_type=OneOf(:primitive, primitive850))
                _t1579 = _t1581
            else
                if prediction839 == 9
                    _t1583 = parse_pragma(parser)
                    pragma849 = _t1583
                    _t1584 = Proto.Formula(formula_type=OneOf(:pragma, pragma849))
                    _t1582 = _t1584
                else
                    if prediction839 == 8
                        _t1586 = parse_atom(parser)
                        atom848 = _t1586
                        _t1587 = Proto.Formula(formula_type=OneOf(:atom, atom848))
                        _t1585 = _t1587
                    else
                        if prediction839 == 7
                            _t1589 = parse_ffi(parser)
                            ffi847 = _t1589
                            _t1590 = Proto.Formula(formula_type=OneOf(:ffi, ffi847))
                            _t1588 = _t1590
                        else
                            if prediction839 == 6
                                _t1592 = parse_not(parser)
                                not846 = _t1592
                                _t1593 = Proto.Formula(formula_type=OneOf(:not, not846))
                                _t1591 = _t1593
                            else
                                if prediction839 == 5
                                    _t1595 = parse_disjunction(parser)
                                    disjunction845 = _t1595
                                    _t1596 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction845))
                                    _t1594 = _t1596
                                else
                                    if prediction839 == 4
                                        _t1598 = parse_conjunction(parser)
                                        conjunction844 = _t1598
                                        _t1599 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction844))
                                        _t1597 = _t1599
                                    else
                                        if prediction839 == 3
                                            _t1601 = parse_reduce(parser)
                                            reduce843 = _t1601
                                            _t1602 = Proto.Formula(formula_type=OneOf(:reduce, reduce843))
                                            _t1600 = _t1602
                                        else
                                            if prediction839 == 2
                                                _t1604 = parse_exists(parser)
                                                exists842 = _t1604
                                                _t1605 = Proto.Formula(formula_type=OneOf(:exists, exists842))
                                                _t1603 = _t1605
                                            else
                                                if prediction839 == 1
                                                    _t1607 = parse_false(parser)
                                                    false841 = _t1607
                                                    _t1608 = Proto.Formula(formula_type=OneOf(:disjunction, false841))
                                                    _t1606 = _t1608
                                                else
                                                    if prediction839 == 0
                                                        _t1610 = parse_true(parser)
                                                        true840 = _t1610
                                                        _t1611 = Proto.Formula(formula_type=OneOf(:conjunction, true840))
                                                        _t1609 = _t1611
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1606 = _t1609
                                                end
                                                _t1603 = _t1606
                                            end
                                            _t1600 = _t1603
                                        end
                                        _t1597 = _t1600
                                    end
                                    _t1594 = _t1597
                                end
                                _t1591 = _t1594
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
    result854 = _t1573
    record_span!(parser, span_start853, "Formula")
    return result854
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start855 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1612 = Proto.Conjunction(args=Proto.Formula[])
    result856 = _t1612
    record_span!(parser, span_start855, "Conjunction")
    return result856
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start857 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1613 = Proto.Disjunction(args=Proto.Formula[])
    result858 = _t1613
    record_span!(parser, span_start857, "Disjunction")
    return result858
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start861 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1614 = parse_bindings(parser)
    bindings859 = _t1614
    _t1615 = parse_formula(parser)
    formula860 = _t1615
    consume_literal!(parser, ")")
    _t1616 = Proto.Abstraction(vars=vcat(bindings859[1], !isnothing(bindings859[2]) ? bindings859[2] : []), value=formula860)
    _t1617 = Proto.Exists(body=_t1616)
    result862 = _t1617
    record_span!(parser, span_start861, "Exists")
    return result862
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start866 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1618 = parse_abstraction(parser)
    abstraction863 = _t1618
    _t1619 = parse_abstraction(parser)
    abstraction_3864 = _t1619
    _t1620 = parse_terms(parser)
    terms865 = _t1620
    consume_literal!(parser, ")")
    _t1621 = Proto.Reduce(op=abstraction863, body=abstraction_3864, terms=terms865)
    result867 = _t1621
    record_span!(parser, span_start866, "Reduce")
    return result867
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs868 = Proto.Term[]
    cond869 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond869
        _t1622 = parse_term(parser)
        item870 = _t1622
        push!(xs868, item870)
        cond869 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms871 = xs868
    consume_literal!(parser, ")")
    return terms871
end

function parse_term(parser::ParserState)::Proto.Term
    span_start875 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1623 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1624 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1625 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1626 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1627 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1628 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1629 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1630 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1631 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1632 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1633 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1634 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1635 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1636 = 1
                                                        else
                                                            _t1636 = -1
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
        _t1623 = _t1624
    end
    prediction872 = _t1623
    if prediction872 == 1
        _t1638 = parse_value(parser)
        value874 = _t1638
        _t1639 = Proto.Term(term_type=OneOf(:constant, value874))
        _t1637 = _t1639
    else
        if prediction872 == 0
            _t1641 = parse_var(parser)
            var873 = _t1641
            _t1642 = Proto.Term(term_type=OneOf(:var, var873))
            _t1640 = _t1642
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1637 = _t1640
    end
    result876 = _t1637
    record_span!(parser, span_start875, "Term")
    return result876
end

function parse_var(parser::ParserState)::Proto.Var
    span_start878 = span_start(parser)
    symbol877 = consume_terminal!(parser, "SYMBOL")
    _t1643 = Proto.Var(name=symbol877)
    result879 = _t1643
    record_span!(parser, span_start878, "Var")
    return result879
end

function parse_value(parser::ParserState)::Proto.Value
    span_start893 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1644 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1645 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1646 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1648 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1649 = 0
                        else
                            _t1649 = -1
                        end
                        _t1648 = _t1649
                    end
                    _t1647 = _t1648
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1650 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1651 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1652 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1653 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1654 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1655 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1656 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1657 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1658 = 10
                                                    else
                                                        _t1658 = -1
                                                    end
                                                    _t1657 = _t1658
                                                end
                                                _t1656 = _t1657
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
                    _t1647 = _t1650
                end
                _t1646 = _t1647
            end
            _t1645 = _t1646
        end
        _t1644 = _t1645
    end
    prediction880 = _t1644
    if prediction880 == 12
        _t1660 = parse_boolean_value(parser)
        boolean_value892 = _t1660
        _t1661 = Proto.Value(value=OneOf(:boolean_value, boolean_value892))
        _t1659 = _t1661
    else
        if prediction880 == 11
            consume_literal!(parser, "missing")
            _t1663 = Proto.MissingValue()
            _t1664 = Proto.Value(value=OneOf(:missing_value, _t1663))
            _t1662 = _t1664
        else
            if prediction880 == 10
                formatted_decimal891 = consume_terminal!(parser, "DECIMAL")
                _t1666 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal891))
                _t1665 = _t1666
            else
                if prediction880 == 9
                    formatted_int128890 = consume_terminal!(parser, "INT128")
                    _t1668 = Proto.Value(value=OneOf(:int128_value, formatted_int128890))
                    _t1667 = _t1668
                else
                    if prediction880 == 8
                        formatted_uint128889 = consume_terminal!(parser, "UINT128")
                        _t1670 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128889))
                        _t1669 = _t1670
                    else
                        if prediction880 == 7
                            formatted_uint32888 = consume_terminal!(parser, "UINT32")
                            _t1672 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32888))
                            _t1671 = _t1672
                        else
                            if prediction880 == 6
                                formatted_float887 = consume_terminal!(parser, "FLOAT")
                                _t1674 = Proto.Value(value=OneOf(:float_value, formatted_float887))
                                _t1673 = _t1674
                            else
                                if prediction880 == 5
                                    formatted_float32886 = consume_terminal!(parser, "FLOAT32")
                                    _t1676 = Proto.Value(value=OneOf(:float32_value, formatted_float32886))
                                    _t1675 = _t1676
                                else
                                    if prediction880 == 4
                                        formatted_int885 = consume_terminal!(parser, "INT")
                                        _t1678 = Proto.Value(value=OneOf(:int_value, formatted_int885))
                                        _t1677 = _t1678
                                    else
                                        if prediction880 == 3
                                            formatted_int32884 = consume_terminal!(parser, "INT32")
                                            _t1680 = Proto.Value(value=OneOf(:int32_value, formatted_int32884))
                                            _t1679 = _t1680
                                        else
                                            if prediction880 == 2
                                                formatted_string883 = consume_terminal!(parser, "STRING")
                                                _t1682 = Proto.Value(value=OneOf(:string_value, formatted_string883))
                                                _t1681 = _t1682
                                            else
                                                if prediction880 == 1
                                                    _t1684 = parse_datetime(parser)
                                                    datetime882 = _t1684
                                                    _t1685 = Proto.Value(value=OneOf(:datetime_value, datetime882))
                                                    _t1683 = _t1685
                                                else
                                                    if prediction880 == 0
                                                        _t1687 = parse_date(parser)
                                                        date881 = _t1687
                                                        _t1688 = Proto.Value(value=OneOf(:date_value, date881))
                                                        _t1686 = _t1688
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1683 = _t1686
                                                end
                                                _t1681 = _t1683
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
            _t1662 = _t1665
        end
        _t1659 = _t1662
    end
    result894 = _t1659
    record_span!(parser, span_start893, "Value")
    return result894
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start898 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int895 = consume_terminal!(parser, "INT")
    formatted_int_3896 = consume_terminal!(parser, "INT")
    formatted_int_4897 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1689 = Proto.DateValue(year=Int32(formatted_int895), month=Int32(formatted_int_3896), day=Int32(formatted_int_4897))
    result899 = _t1689
    record_span!(parser, span_start898, "DateValue")
    return result899
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start907 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int900 = consume_terminal!(parser, "INT")
    formatted_int_3901 = consume_terminal!(parser, "INT")
    formatted_int_4902 = consume_terminal!(parser, "INT")
    formatted_int_5903 = consume_terminal!(parser, "INT")
    formatted_int_6904 = consume_terminal!(parser, "INT")
    formatted_int_7905 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1690 = consume_terminal!(parser, "INT")
    else
        _t1690 = nothing
    end
    formatted_int_8906 = _t1690
    consume_literal!(parser, ")")
    _t1691 = Proto.DateTimeValue(year=Int32(formatted_int900), month=Int32(formatted_int_3901), day=Int32(formatted_int_4902), hour=Int32(formatted_int_5903), minute=Int32(formatted_int_6904), second=Int32(formatted_int_7905), microsecond=Int32((!isnothing(formatted_int_8906) ? formatted_int_8906 : 0)))
    result908 = _t1691
    record_span!(parser, span_start907, "DateTimeValue")
    return result908
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start913 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs909 = Proto.Formula[]
    cond910 = match_lookahead_literal(parser, "(", 0)
    while cond910
        _t1692 = parse_formula(parser)
        item911 = _t1692
        push!(xs909, item911)
        cond910 = match_lookahead_literal(parser, "(", 0)
    end
    formulas912 = xs909
    consume_literal!(parser, ")")
    _t1693 = Proto.Conjunction(args=formulas912)
    result914 = _t1693
    record_span!(parser, span_start913, "Conjunction")
    return result914
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start919 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs915 = Proto.Formula[]
    cond916 = match_lookahead_literal(parser, "(", 0)
    while cond916
        _t1694 = parse_formula(parser)
        item917 = _t1694
        push!(xs915, item917)
        cond916 = match_lookahead_literal(parser, "(", 0)
    end
    formulas918 = xs915
    consume_literal!(parser, ")")
    _t1695 = Proto.Disjunction(args=formulas918)
    result920 = _t1695
    record_span!(parser, span_start919, "Disjunction")
    return result920
end

function parse_not(parser::ParserState)::Proto.Not
    span_start922 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1696 = parse_formula(parser)
    formula921 = _t1696
    consume_literal!(parser, ")")
    _t1697 = Proto.Not(arg=formula921)
    result923 = _t1697
    record_span!(parser, span_start922, "Not")
    return result923
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start927 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1698 = parse_name(parser)
    name924 = _t1698
    _t1699 = parse_ffi_args(parser)
    ffi_args925 = _t1699
    _t1700 = parse_terms(parser)
    terms926 = _t1700
    consume_literal!(parser, ")")
    _t1701 = Proto.FFI(name=name924, args=ffi_args925, terms=terms926)
    result928 = _t1701
    record_span!(parser, span_start927, "FFI")
    return result928
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol929 = consume_terminal!(parser, "SYMBOL")
    return symbol929
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs930 = Proto.Abstraction[]
    cond931 = match_lookahead_literal(parser, "(", 0)
    while cond931
        _t1702 = parse_abstraction(parser)
        item932 = _t1702
        push!(xs930, item932)
        cond931 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions933 = xs930
    consume_literal!(parser, ")")
    return abstractions933
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start939 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1703 = parse_relation_id(parser)
    relation_id934 = _t1703
    xs935 = Proto.Term[]
    cond936 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond936
        _t1704 = parse_term(parser)
        item937 = _t1704
        push!(xs935, item937)
        cond936 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms938 = xs935
    consume_literal!(parser, ")")
    _t1705 = Proto.Atom(name=relation_id934, terms=terms938)
    result940 = _t1705
    record_span!(parser, span_start939, "Atom")
    return result940
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start946 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1706 = parse_name(parser)
    name941 = _t1706
    xs942 = Proto.Term[]
    cond943 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond943
        _t1707 = parse_term(parser)
        item944 = _t1707
        push!(xs942, item944)
        cond943 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms945 = xs942
    consume_literal!(parser, ")")
    _t1708 = Proto.Pragma(name=name941, terms=terms945)
    result947 = _t1708
    record_span!(parser, span_start946, "Pragma")
    return result947
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start963 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1710 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1711 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1712 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1713 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1714 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1715 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1716 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1717 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1718 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1719 = 7
                                            else
                                                _t1719 = -1
                                            end
                                            _t1718 = _t1719
                                        end
                                        _t1717 = _t1718
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
    else
        _t1709 = -1
    end
    prediction948 = _t1709
    if prediction948 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1721 = parse_name(parser)
        name958 = _t1721
        xs959 = Proto.RelTerm[]
        cond960 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond960
            _t1722 = parse_rel_term(parser)
            item961 = _t1722
            push!(xs959, item961)
            cond960 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms962 = xs959
        consume_literal!(parser, ")")
        _t1723 = Proto.Primitive(name=name958, terms=rel_terms962)
        _t1720 = _t1723
    else
        if prediction948 == 8
            _t1725 = parse_divide(parser)
            divide957 = _t1725
            _t1724 = divide957
        else
            if prediction948 == 7
                _t1727 = parse_multiply(parser)
                multiply956 = _t1727
                _t1726 = multiply956
            else
                if prediction948 == 6
                    _t1729 = parse_minus(parser)
                    minus955 = _t1729
                    _t1728 = minus955
                else
                    if prediction948 == 5
                        _t1731 = parse_add(parser)
                        add954 = _t1731
                        _t1730 = add954
                    else
                        if prediction948 == 4
                            _t1733 = parse_gt_eq(parser)
                            gt_eq953 = _t1733
                            _t1732 = gt_eq953
                        else
                            if prediction948 == 3
                                _t1735 = parse_gt(parser)
                                gt952 = _t1735
                                _t1734 = gt952
                            else
                                if prediction948 == 2
                                    _t1737 = parse_lt_eq(parser)
                                    lt_eq951 = _t1737
                                    _t1736 = lt_eq951
                                else
                                    if prediction948 == 1
                                        _t1739 = parse_lt(parser)
                                        lt950 = _t1739
                                        _t1738 = lt950
                                    else
                                        if prediction948 == 0
                                            _t1741 = parse_eq(parser)
                                            eq949 = _t1741
                                            _t1740 = eq949
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1738 = _t1740
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
        _t1720 = _t1724
    end
    result964 = _t1720
    record_span!(parser, span_start963, "Primitive")
    return result964
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start967 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1742 = parse_term(parser)
    term965 = _t1742
    _t1743 = parse_term(parser)
    term_3966 = _t1743
    consume_literal!(parser, ")")
    _t1744 = Proto.RelTerm(rel_term_type=OneOf(:term, term965))
    _t1745 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3966))
    _t1746 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1744, _t1745])
    result968 = _t1746
    record_span!(parser, span_start967, "Primitive")
    return result968
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start971 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1747 = parse_term(parser)
    term969 = _t1747
    _t1748 = parse_term(parser)
    term_3970 = _t1748
    consume_literal!(parser, ")")
    _t1749 = Proto.RelTerm(rel_term_type=OneOf(:term, term969))
    _t1750 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3970))
    _t1751 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1749, _t1750])
    result972 = _t1751
    record_span!(parser, span_start971, "Primitive")
    return result972
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start975 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1752 = parse_term(parser)
    term973 = _t1752
    _t1753 = parse_term(parser)
    term_3974 = _t1753
    consume_literal!(parser, ")")
    _t1754 = Proto.RelTerm(rel_term_type=OneOf(:term, term973))
    _t1755 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3974))
    _t1756 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1754, _t1755])
    result976 = _t1756
    record_span!(parser, span_start975, "Primitive")
    return result976
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start979 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1757 = parse_term(parser)
    term977 = _t1757
    _t1758 = parse_term(parser)
    term_3978 = _t1758
    consume_literal!(parser, ")")
    _t1759 = Proto.RelTerm(rel_term_type=OneOf(:term, term977))
    _t1760 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3978))
    _t1761 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1759, _t1760])
    result980 = _t1761
    record_span!(parser, span_start979, "Primitive")
    return result980
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start983 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1762 = parse_term(parser)
    term981 = _t1762
    _t1763 = parse_term(parser)
    term_3982 = _t1763
    consume_literal!(parser, ")")
    _t1764 = Proto.RelTerm(rel_term_type=OneOf(:term, term981))
    _t1765 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3982))
    _t1766 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1764, _t1765])
    result984 = _t1766
    record_span!(parser, span_start983, "Primitive")
    return result984
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start988 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1767 = parse_term(parser)
    term985 = _t1767
    _t1768 = parse_term(parser)
    term_3986 = _t1768
    _t1769 = parse_term(parser)
    term_4987 = _t1769
    consume_literal!(parser, ")")
    _t1770 = Proto.RelTerm(rel_term_type=OneOf(:term, term985))
    _t1771 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3986))
    _t1772 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4987))
    _t1773 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1770, _t1771, _t1772])
    result989 = _t1773
    record_span!(parser, span_start988, "Primitive")
    return result989
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start993 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1774 = parse_term(parser)
    term990 = _t1774
    _t1775 = parse_term(parser)
    term_3991 = _t1775
    _t1776 = parse_term(parser)
    term_4992 = _t1776
    consume_literal!(parser, ")")
    _t1777 = Proto.RelTerm(rel_term_type=OneOf(:term, term990))
    _t1778 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3991))
    _t1779 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4992))
    _t1780 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1777, _t1778, _t1779])
    result994 = _t1780
    record_span!(parser, span_start993, "Primitive")
    return result994
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start998 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1781 = parse_term(parser)
    term995 = _t1781
    _t1782 = parse_term(parser)
    term_3996 = _t1782
    _t1783 = parse_term(parser)
    term_4997 = _t1783
    consume_literal!(parser, ")")
    _t1784 = Proto.RelTerm(rel_term_type=OneOf(:term, term995))
    _t1785 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3996))
    _t1786 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4997))
    _t1787 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1784, _t1785, _t1786])
    result999 = _t1787
    record_span!(parser, span_start998, "Primitive")
    return result999
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1003 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1788 = parse_term(parser)
    term1000 = _t1788
    _t1789 = parse_term(parser)
    term_31001 = _t1789
    _t1790 = parse_term(parser)
    term_41002 = _t1790
    consume_literal!(parser, ")")
    _t1791 = Proto.RelTerm(rel_term_type=OneOf(:term, term1000))
    _t1792 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31001))
    _t1793 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41002))
    _t1794 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1791, _t1792, _t1793])
    result1004 = _t1794
    record_span!(parser, span_start1003, "Primitive")
    return result1004
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1008 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1795 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1796 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1797 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1798 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1799 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1800 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1801 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1802 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1803 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1804 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1805 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1806 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1807 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1808 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1809 = 1
                                                            else
                                                                _t1809 = -1
                                                            end
                                                            _t1808 = _t1809
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
    prediction1005 = _t1795
    if prediction1005 == 1
        _t1811 = parse_term(parser)
        term1007 = _t1811
        _t1812 = Proto.RelTerm(rel_term_type=OneOf(:term, term1007))
        _t1810 = _t1812
    else
        if prediction1005 == 0
            _t1814 = parse_specialized_value(parser)
            specialized_value1006 = _t1814
            _t1815 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1006))
            _t1813 = _t1815
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1810 = _t1813
    end
    result1009 = _t1810
    record_span!(parser, span_start1008, "RelTerm")
    return result1009
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1011 = span_start(parser)
    consume_literal!(parser, "#")
    _t1816 = parse_raw_value(parser)
    raw_value1010 = _t1816
    result1012 = raw_value1010
    record_span!(parser, span_start1011, "Value")
    return result1012
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1018 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1817 = parse_name(parser)
    name1013 = _t1817
    xs1014 = Proto.RelTerm[]
    cond1015 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1015
        _t1818 = parse_rel_term(parser)
        item1016 = _t1818
        push!(xs1014, item1016)
        cond1015 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1017 = xs1014
    consume_literal!(parser, ")")
    _t1819 = Proto.RelAtom(name=name1013, terms=rel_terms1017)
    result1019 = _t1819
    record_span!(parser, span_start1018, "RelAtom")
    return result1019
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1022 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1820 = parse_term(parser)
    term1020 = _t1820
    _t1821 = parse_term(parser)
    term_31021 = _t1821
    consume_literal!(parser, ")")
    _t1822 = Proto.Cast(input=term1020, result=term_31021)
    result1023 = _t1822
    record_span!(parser, span_start1022, "Cast")
    return result1023
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1024 = Proto.Attribute[]
    cond1025 = match_lookahead_literal(parser, "(", 0)
    while cond1025
        _t1823 = parse_attribute(parser)
        item1026 = _t1823
        push!(xs1024, item1026)
        cond1025 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1027 = xs1024
    consume_literal!(parser, ")")
    return attributes1027
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1033 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1824 = parse_name(parser)
    name1028 = _t1824
    xs1029 = Proto.Value[]
    cond1030 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1030
        _t1825 = parse_raw_value(parser)
        item1031 = _t1825
        push!(xs1029, item1031)
        cond1030 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1032 = xs1029
    consume_literal!(parser, ")")
    _t1826 = Proto.Attribute(name=name1028, args=raw_values1032)
    result1034 = _t1826
    record_span!(parser, span_start1033, "Attribute")
    return result1034
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1041 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1035 = Proto.RelationId[]
    cond1036 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1036
        _t1827 = parse_relation_id(parser)
        item1037 = _t1827
        push!(xs1035, item1037)
        cond1036 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1038 = xs1035
    _t1828 = parse_script(parser)
    script1039 = _t1828
    if match_lookahead_literal(parser, "(", 0)
        _t1830 = parse_attrs(parser)
        _t1829 = _t1830
    else
        _t1829 = nothing
    end
    attrs1040 = _t1829
    consume_literal!(parser, ")")
    _t1831 = Proto.Algorithm(var"#global"=relation_ids1038, body=script1039, attrs=(!isnothing(attrs1040) ? attrs1040 : Proto.Attribute[]))
    result1042 = _t1831
    record_span!(parser, span_start1041, "Algorithm")
    return result1042
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1047 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1043 = Proto.Construct[]
    cond1044 = match_lookahead_literal(parser, "(", 0)
    while cond1044
        _t1832 = parse_construct(parser)
        item1045 = _t1832
        push!(xs1043, item1045)
        cond1044 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1046 = xs1043
    consume_literal!(parser, ")")
    _t1833 = Proto.Script(constructs=constructs1046)
    result1048 = _t1833
    record_span!(parser, span_start1047, "Script")
    return result1048
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1052 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1835 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1836 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1837 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1838 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1839 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1840 = 1
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
        end
        _t1834 = _t1835
    else
        _t1834 = -1
    end
    prediction1049 = _t1834
    if prediction1049 == 1
        _t1842 = parse_instruction(parser)
        instruction1051 = _t1842
        _t1843 = Proto.Construct(construct_type=OneOf(:instruction, instruction1051))
        _t1841 = _t1843
    else
        if prediction1049 == 0
            _t1845 = parse_loop(parser)
            loop1050 = _t1845
            _t1846 = Proto.Construct(construct_type=OneOf(:loop, loop1050))
            _t1844 = _t1846
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1841 = _t1844
    end
    result1053 = _t1841
    record_span!(parser, span_start1052, "Construct")
    return result1053
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1057 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1847 = parse_init(parser)
    init1054 = _t1847
    _t1848 = parse_script(parser)
    script1055 = _t1848
    if match_lookahead_literal(parser, "(", 0)
        _t1850 = parse_attrs(parser)
        _t1849 = _t1850
    else
        _t1849 = nothing
    end
    attrs1056 = _t1849
    consume_literal!(parser, ")")
    _t1851 = Proto.Loop(init=init1054, body=script1055, attrs=(!isnothing(attrs1056) ? attrs1056 : Proto.Attribute[]))
    result1058 = _t1851
    record_span!(parser, span_start1057, "Loop")
    return result1058
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1059 = Proto.Instruction[]
    cond1060 = match_lookahead_literal(parser, "(", 0)
    while cond1060
        _t1852 = parse_instruction(parser)
        item1061 = _t1852
        push!(xs1059, item1061)
        cond1060 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1062 = xs1059
    consume_literal!(parser, ")")
    return instructions1062
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1069 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1854 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1855 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1856 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1857 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1858 = 0
                        else
                            _t1858 = -1
                        end
                        _t1857 = _t1858
                    end
                    _t1856 = _t1857
                end
                _t1855 = _t1856
            end
            _t1854 = _t1855
        end
        _t1853 = _t1854
    else
        _t1853 = -1
    end
    prediction1063 = _t1853
    if prediction1063 == 4
        _t1860 = parse_monus_def(parser)
        monus_def1068 = _t1860
        _t1861 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1068))
        _t1859 = _t1861
    else
        if prediction1063 == 3
            _t1863 = parse_monoid_def(parser)
            monoid_def1067 = _t1863
            _t1864 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1067))
            _t1862 = _t1864
        else
            if prediction1063 == 2
                _t1866 = parse_break(parser)
                break1066 = _t1866
                _t1867 = Proto.Instruction(instr_type=OneOf(:var"#break", break1066))
                _t1865 = _t1867
            else
                if prediction1063 == 1
                    _t1869 = parse_upsert(parser)
                    upsert1065 = _t1869
                    _t1870 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1065))
                    _t1868 = _t1870
                else
                    if prediction1063 == 0
                        _t1872 = parse_assign(parser)
                        assign1064 = _t1872
                        _t1873 = Proto.Instruction(instr_type=OneOf(:assign, assign1064))
                        _t1871 = _t1873
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1868 = _t1871
                end
                _t1865 = _t1868
            end
            _t1862 = _t1865
        end
        _t1859 = _t1862
    end
    result1070 = _t1859
    record_span!(parser, span_start1069, "Instruction")
    return result1070
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1074 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1874 = parse_relation_id(parser)
    relation_id1071 = _t1874
    _t1875 = parse_abstraction(parser)
    abstraction1072 = _t1875
    if match_lookahead_literal(parser, "(", 0)
        _t1877 = parse_attrs(parser)
        _t1876 = _t1877
    else
        _t1876 = nothing
    end
    attrs1073 = _t1876
    consume_literal!(parser, ")")
    _t1878 = Proto.Assign(name=relation_id1071, body=abstraction1072, attrs=(!isnothing(attrs1073) ? attrs1073 : Proto.Attribute[]))
    result1075 = _t1878
    record_span!(parser, span_start1074, "Assign")
    return result1075
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1079 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1879 = parse_relation_id(parser)
    relation_id1076 = _t1879
    _t1880 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1077 = _t1880
    if match_lookahead_literal(parser, "(", 0)
        _t1882 = parse_attrs(parser)
        _t1881 = _t1882
    else
        _t1881 = nothing
    end
    attrs1078 = _t1881
    consume_literal!(parser, ")")
    _t1883 = Proto.Upsert(name=relation_id1076, body=abstraction_with_arity1077[1], attrs=(!isnothing(attrs1078) ? attrs1078 : Proto.Attribute[]), value_arity=abstraction_with_arity1077[2])
    result1080 = _t1883
    record_span!(parser, span_start1079, "Upsert")
    return result1080
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1884 = parse_bindings(parser)
    bindings1081 = _t1884
    _t1885 = parse_formula(parser)
    formula1082 = _t1885
    consume_literal!(parser, ")")
    _t1886 = Proto.Abstraction(vars=vcat(bindings1081[1], !isnothing(bindings1081[2]) ? bindings1081[2] : []), value=formula1082)
    return (_t1886, length(bindings1081[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1086 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1887 = parse_relation_id(parser)
    relation_id1083 = _t1887
    _t1888 = parse_abstraction(parser)
    abstraction1084 = _t1888
    if match_lookahead_literal(parser, "(", 0)
        _t1890 = parse_attrs(parser)
        _t1889 = _t1890
    else
        _t1889 = nothing
    end
    attrs1085 = _t1889
    consume_literal!(parser, ")")
    _t1891 = Proto.Break(name=relation_id1083, body=abstraction1084, attrs=(!isnothing(attrs1085) ? attrs1085 : Proto.Attribute[]))
    result1087 = _t1891
    record_span!(parser, span_start1086, "Break")
    return result1087
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1092 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1892 = parse_monoid(parser)
    monoid1088 = _t1892
    _t1893 = parse_relation_id(parser)
    relation_id1089 = _t1893
    _t1894 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1090 = _t1894
    if match_lookahead_literal(parser, "(", 0)
        _t1896 = parse_attrs(parser)
        _t1895 = _t1896
    else
        _t1895 = nothing
    end
    attrs1091 = _t1895
    consume_literal!(parser, ")")
    _t1897 = Proto.MonoidDef(monoid=monoid1088, name=relation_id1089, body=abstraction_with_arity1090[1], attrs=(!isnothing(attrs1091) ? attrs1091 : Proto.Attribute[]), value_arity=abstraction_with_arity1090[2])
    result1093 = _t1897
    record_span!(parser, span_start1092, "MonoidDef")
    return result1093
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1099 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1899 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1900 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1901 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1902 = 2
                    else
                        _t1902 = -1
                    end
                    _t1901 = _t1902
                end
                _t1900 = _t1901
            end
            _t1899 = _t1900
        end
        _t1898 = _t1899
    else
        _t1898 = -1
    end
    prediction1094 = _t1898
    if prediction1094 == 3
        _t1904 = parse_sum_monoid(parser)
        sum_monoid1098 = _t1904
        _t1905 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1098))
        _t1903 = _t1905
    else
        if prediction1094 == 2
            _t1907 = parse_max_monoid(parser)
            max_monoid1097 = _t1907
            _t1908 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1097))
            _t1906 = _t1908
        else
            if prediction1094 == 1
                _t1910 = parse_min_monoid(parser)
                min_monoid1096 = _t1910
                _t1911 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1096))
                _t1909 = _t1911
            else
                if prediction1094 == 0
                    _t1913 = parse_or_monoid(parser)
                    or_monoid1095 = _t1913
                    _t1914 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1095))
                    _t1912 = _t1914
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1909 = _t1912
            end
            _t1906 = _t1909
        end
        _t1903 = _t1906
    end
    result1100 = _t1903
    record_span!(parser, span_start1099, "Monoid")
    return result1100
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1101 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1915 = Proto.OrMonoid()
    result1102 = _t1915
    record_span!(parser, span_start1101, "OrMonoid")
    return result1102
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1104 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1916 = parse_type(parser)
    type1103 = _t1916
    consume_literal!(parser, ")")
    _t1917 = Proto.MinMonoid(var"#type"=type1103)
    result1105 = _t1917
    record_span!(parser, span_start1104, "MinMonoid")
    return result1105
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1107 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1918 = parse_type(parser)
    type1106 = _t1918
    consume_literal!(parser, ")")
    _t1919 = Proto.MaxMonoid(var"#type"=type1106)
    result1108 = _t1919
    record_span!(parser, span_start1107, "MaxMonoid")
    return result1108
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1110 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1920 = parse_type(parser)
    type1109 = _t1920
    consume_literal!(parser, ")")
    _t1921 = Proto.SumMonoid(var"#type"=type1109)
    result1111 = _t1921
    record_span!(parser, span_start1110, "SumMonoid")
    return result1111
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1116 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1922 = parse_monoid(parser)
    monoid1112 = _t1922
    _t1923 = parse_relation_id(parser)
    relation_id1113 = _t1923
    _t1924 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1114 = _t1924
    if match_lookahead_literal(parser, "(", 0)
        _t1926 = parse_attrs(parser)
        _t1925 = _t1926
    else
        _t1925 = nothing
    end
    attrs1115 = _t1925
    consume_literal!(parser, ")")
    _t1927 = Proto.MonusDef(monoid=monoid1112, name=relation_id1113, body=abstraction_with_arity1114[1], attrs=(!isnothing(attrs1115) ? attrs1115 : Proto.Attribute[]), value_arity=abstraction_with_arity1114[2])
    result1117 = _t1927
    record_span!(parser, span_start1116, "MonusDef")
    return result1117
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1122 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1928 = parse_relation_id(parser)
    relation_id1118 = _t1928
    _t1929 = parse_abstraction(parser)
    abstraction1119 = _t1929
    _t1930 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1120 = _t1930
    _t1931 = parse_functional_dependency_values(parser)
    functional_dependency_values1121 = _t1931
    consume_literal!(parser, ")")
    _t1932 = Proto.FunctionalDependency(guard=abstraction1119, keys=functional_dependency_keys1120, values=functional_dependency_values1121)
    _t1933 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1932), name=relation_id1118)
    result1123 = _t1933
    record_span!(parser, span_start1122, "Constraint")
    return result1123
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1124 = Proto.Var[]
    cond1125 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1125
        _t1934 = parse_var(parser)
        item1126 = _t1934
        push!(xs1124, item1126)
        cond1125 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1127 = xs1124
    consume_literal!(parser, ")")
    return vars1127
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1128 = Proto.Var[]
    cond1129 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1129
        _t1935 = parse_var(parser)
        item1130 = _t1935
        push!(xs1128, item1130)
        cond1129 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1131 = xs1128
    consume_literal!(parser, ")")
    return vars1131
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1137 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1937 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1938 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1939 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1940 = 1
                    else
                        _t1940 = -1
                    end
                    _t1939 = _t1940
                end
                _t1938 = _t1939
            end
            _t1937 = _t1938
        end
        _t1936 = _t1937
    else
        _t1936 = -1
    end
    prediction1132 = _t1936
    if prediction1132 == 3
        _t1942 = parse_iceberg_data(parser)
        iceberg_data1136 = _t1942
        _t1943 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1136))
        _t1941 = _t1943
    else
        if prediction1132 == 2
            _t1945 = parse_csv_data(parser)
            csv_data1135 = _t1945
            _t1946 = Proto.Data(data_type=OneOf(:csv_data, csv_data1135))
            _t1944 = _t1946
        else
            if prediction1132 == 1
                _t1948 = parse_betree_relation(parser)
                betree_relation1134 = _t1948
                _t1949 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1134))
                _t1947 = _t1949
            else
                if prediction1132 == 0
                    _t1951 = parse_edb(parser)
                    edb1133 = _t1951
                    _t1952 = Proto.Data(data_type=OneOf(:edb, edb1133))
                    _t1950 = _t1952
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1947 = _t1950
            end
            _t1944 = _t1947
        end
        _t1941 = _t1944
    end
    result1138 = _t1941
    record_span!(parser, span_start1137, "Data")
    return result1138
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1142 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1953 = parse_relation_id(parser)
    relation_id1139 = _t1953
    _t1954 = parse_edb_path(parser)
    edb_path1140 = _t1954
    _t1955 = parse_edb_types(parser)
    edb_types1141 = _t1955
    consume_literal!(parser, ")")
    _t1956 = Proto.EDB(target_id=relation_id1139, path=edb_path1140, types=edb_types1141)
    result1143 = _t1956
    record_span!(parser, span_start1142, "EDB")
    return result1143
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1144 = String[]
    cond1145 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1145
        item1146 = consume_terminal!(parser, "STRING")
        push!(xs1144, item1146)
        cond1145 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1147 = xs1144
    consume_literal!(parser, "]")
    return strings1147
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1148 = Proto.var"#Type"[]
    cond1149 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1149
        _t1957 = parse_type(parser)
        item1150 = _t1957
        push!(xs1148, item1150)
        cond1149 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1151 = xs1148
    consume_literal!(parser, "]")
    return types1151
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1154 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1958 = parse_relation_id(parser)
    relation_id1152 = _t1958
    _t1959 = parse_betree_info(parser)
    betree_info1153 = _t1959
    consume_literal!(parser, ")")
    _t1960 = Proto.BeTreeRelation(name=relation_id1152, relation_info=betree_info1153)
    result1155 = _t1960
    record_span!(parser, span_start1154, "BeTreeRelation")
    return result1155
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1159 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1961 = parse_betree_info_key_types(parser)
    betree_info_key_types1156 = _t1961
    _t1962 = parse_betree_info_value_types(parser)
    betree_info_value_types1157 = _t1962
    _t1963 = parse_config_dict(parser)
    config_dict1158 = _t1963
    consume_literal!(parser, ")")
    _t1964 = construct_betree_info(parser, betree_info_key_types1156, betree_info_value_types1157, config_dict1158)
    result1160 = _t1964
    record_span!(parser, span_start1159, "BeTreeInfo")
    return result1160
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1161 = Proto.var"#Type"[]
    cond1162 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1162
        _t1965 = parse_type(parser)
        item1163 = _t1965
        push!(xs1161, item1163)
        cond1162 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1164 = xs1161
    consume_literal!(parser, ")")
    return types1164
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1165 = Proto.var"#Type"[]
    cond1166 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1166
        _t1966 = parse_type(parser)
        item1167 = _t1966
        push!(xs1165, item1167)
        cond1166 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1168 = xs1165
    consume_literal!(parser, ")")
    return types1168
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1173 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1967 = parse_csvlocator(parser)
    csvlocator1169 = _t1967
    _t1968 = parse_csv_config(parser)
    csv_config1170 = _t1968
    _t1969 = parse_gnf_columns(parser)
    gnf_columns1171 = _t1969
    _t1970 = parse_csv_asof(parser)
    csv_asof1172 = _t1970
    consume_literal!(parser, ")")
    _t1971 = Proto.CSVData(locator=csvlocator1169, config=csv_config1170, columns=gnf_columns1171, asof=csv_asof1172)
    result1174 = _t1971
    record_span!(parser, span_start1173, "CSVData")
    return result1174
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1177 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1973 = parse_csv_locator_paths(parser)
        _t1972 = _t1973
    else
        _t1972 = nothing
    end
    csv_locator_paths1175 = _t1972
    if match_lookahead_literal(parser, "(", 0)
        _t1975 = parse_csv_locator_inline_data(parser)
        _t1974 = _t1975
    else
        _t1974 = nothing
    end
    csv_locator_inline_data1176 = _t1974
    consume_literal!(parser, ")")
    _t1976 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1175) ? csv_locator_paths1175 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1176) ? csv_locator_inline_data1176 : "")))
    result1178 = _t1976
    record_span!(parser, span_start1177, "CSVLocator")
    return result1178
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1179 = String[]
    cond1180 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1180
        item1181 = consume_terminal!(parser, "STRING")
        push!(xs1179, item1181)
        cond1180 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1182 = xs1179
    consume_literal!(parser, ")")
    return strings1182
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1183 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1183
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1185 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1977 = parse_config_dict(parser)
    config_dict1184 = _t1977
    consume_literal!(parser, ")")
    _t1978 = construct_csv_config(parser, config_dict1184)
    result1186 = _t1978
    record_span!(parser, span_start1185, "CSVConfig")
    return result1186
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1187 = Proto.GNFColumn[]
    cond1188 = match_lookahead_literal(parser, "(", 0)
    while cond1188
        _t1979 = parse_gnf_column(parser)
        item1189 = _t1979
        push!(xs1187, item1189)
        cond1188 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1190 = xs1187
    consume_literal!(parser, ")")
    return gnf_columns1190
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1197 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1980 = parse_gnf_column_path(parser)
    gnf_column_path1191 = _t1980
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1982 = parse_relation_id(parser)
        _t1981 = _t1982
    else
        _t1981 = nothing
    end
    relation_id1192 = _t1981
    consume_literal!(parser, "[")
    xs1193 = Proto.var"#Type"[]
    cond1194 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1194
        _t1983 = parse_type(parser)
        item1195 = _t1983
        push!(xs1193, item1195)
        cond1194 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1196 = xs1193
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1984 = Proto.GNFColumn(column_path=gnf_column_path1191, target_id=relation_id1192, types=types1196)
    result1198 = _t1984
    record_span!(parser, span_start1197, "GNFColumn")
    return result1198
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1985 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1986 = 0
        else
            _t1986 = -1
        end
        _t1985 = _t1986
    end
    prediction1199 = _t1985
    if prediction1199 == 1
        consume_literal!(parser, "[")
        xs1201 = String[]
        cond1202 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1202
            item1203 = consume_terminal!(parser, "STRING")
            push!(xs1201, item1203)
            cond1202 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1204 = xs1201
        consume_literal!(parser, "]")
        _t1987 = strings1204
    else
        if prediction1199 == 0
            string1200 = consume_terminal!(parser, "STRING")
            _t1988 = String[string1200]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1987 = _t1988
    end
    return _t1987
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1205 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1205
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1212 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1989 = parse_iceberg_locator(parser)
    iceberg_locator1206 = _t1989
    _t1990 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1207 = _t1990
    _t1991 = parse_gnf_columns(parser)
    gnf_columns1208 = _t1991
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1993 = parse_iceberg_from_snapshot(parser)
        _t1992 = _t1993
    else
        _t1992 = nothing
    end
    iceberg_from_snapshot1209 = _t1992
    if match_lookahead_literal(parser, "(", 0)
        _t1995 = parse_iceberg_to_snapshot(parser)
        _t1994 = _t1995
    else
        _t1994 = nothing
    end
    iceberg_to_snapshot1210 = _t1994
    _t1996 = parse_boolean_value(parser)
    boolean_value1211 = _t1996
    consume_literal!(parser, ")")
    _t1997 = construct_iceberg_data(parser, iceberg_locator1206, iceberg_catalog_config1207, gnf_columns1208, iceberg_from_snapshot1209, iceberg_to_snapshot1210, boolean_value1211)
    result1213 = _t1997
    record_span!(parser, span_start1212, "IcebergData")
    return result1213
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1217 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t1998 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1214 = _t1998
    _t1999 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1215 = _t1999
    _t2000 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1216 = _t2000
    consume_literal!(parser, ")")
    _t2001 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1214, namespace=iceberg_locator_namespace1215, warehouse=iceberg_locator_warehouse1216)
    result1218 = _t2001
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
    _t2002 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1225 = _t2002
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2004 = parse_iceberg_catalog_config_scope(parser)
        _t2003 = _t2004
    else
        _t2003 = nothing
    end
    iceberg_catalog_config_scope1226 = _t2003
    _t2005 = parse_iceberg_properties(parser)
    iceberg_properties1227 = _t2005
    _t2006 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1228 = _t2006
    consume_literal!(parser, ")")
    _t2007 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1225, iceberg_catalog_config_scope1226, iceberg_properties1227, iceberg_auth_properties1228)
    result1230 = _t2007
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
        _t2008 = parse_iceberg_property_entry(parser)
        item1235 = _t2008
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
        _t2009 = parse_iceberg_masked_property_entry(parser)
        item1241 = _t2009
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

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1245 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1245
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1246 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1246
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1248 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2010 = parse_fragment_id(parser)
    fragment_id1247 = _t2010
    consume_literal!(parser, ")")
    _t2011 = Proto.Undefine(fragment_id=fragment_id1247)
    result1249 = _t2011
    record_span!(parser, span_start1248, "Undefine")
    return result1249
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1254 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1250 = Proto.RelationId[]
    cond1251 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1251
        _t2012 = parse_relation_id(parser)
        item1252 = _t2012
        push!(xs1250, item1252)
        cond1251 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1253 = xs1250
    consume_literal!(parser, ")")
    _t2013 = Proto.Context(relations=relation_ids1253)
    result1255 = _t2013
    record_span!(parser, span_start1254, "Context")
    return result1255
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1261 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2014 = parse_edb_path(parser)
    edb_path1256 = _t2014
    xs1257 = Proto.SnapshotMapping[]
    cond1258 = match_lookahead_literal(parser, "[", 0)
    while cond1258
        _t2015 = parse_snapshot_mapping(parser)
        item1259 = _t2015
        push!(xs1257, item1259)
        cond1258 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1260 = xs1257
    consume_literal!(parser, ")")
    _t2016 = Proto.Snapshot(mappings=snapshot_mappings1260, prefix=edb_path1256)
    result1262 = _t2016
    record_span!(parser, span_start1261, "Snapshot")
    return result1262
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1265 = span_start(parser)
    _t2017 = parse_edb_path(parser)
    edb_path1263 = _t2017
    _t2018 = parse_relation_id(parser)
    relation_id1264 = _t2018
    _t2019 = Proto.SnapshotMapping(destination_path=edb_path1263, source_relation=relation_id1264)
    result1266 = _t2019
    record_span!(parser, span_start1265, "SnapshotMapping")
    return result1266
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1267 = Proto.Read[]
    cond1268 = match_lookahead_literal(parser, "(", 0)
    while cond1268
        _t2020 = parse_read(parser)
        item1269 = _t2020
        push!(xs1267, item1269)
        cond1268 = match_lookahead_literal(parser, "(", 0)
    end
    reads1270 = xs1267
    consume_literal!(parser, ")")
    return reads1270
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1277 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2022 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2023 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2024 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2025 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2026 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2027 = 3
                            else
                                _t2027 = -1
                            end
                            _t2026 = _t2027
                        end
                        _t2025 = _t2026
                    end
                    _t2024 = _t2025
                end
                _t2023 = _t2024
            end
            _t2022 = _t2023
        end
        _t2021 = _t2022
    else
        _t2021 = -1
    end
    prediction1271 = _t2021
    if prediction1271 == 4
        _t2029 = parse_export(parser)
        export1276 = _t2029
        _t2030 = Proto.Read(read_type=OneOf(:var"#export", export1276))
        _t2028 = _t2030
    else
        if prediction1271 == 3
            _t2032 = parse_abort(parser)
            abort1275 = _t2032
            _t2033 = Proto.Read(read_type=OneOf(:abort, abort1275))
            _t2031 = _t2033
        else
            if prediction1271 == 2
                _t2035 = parse_what_if(parser)
                what_if1274 = _t2035
                _t2036 = Proto.Read(read_type=OneOf(:what_if, what_if1274))
                _t2034 = _t2036
            else
                if prediction1271 == 1
                    _t2038 = parse_output(parser)
                    output1273 = _t2038
                    _t2039 = Proto.Read(read_type=OneOf(:output, output1273))
                    _t2037 = _t2039
                else
                    if prediction1271 == 0
                        _t2041 = parse_demand(parser)
                        demand1272 = _t2041
                        _t2042 = Proto.Read(read_type=OneOf(:demand, demand1272))
                        _t2040 = _t2042
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2037 = _t2040
                end
                _t2034 = _t2037
            end
            _t2031 = _t2034
        end
        _t2028 = _t2031
    end
    result1278 = _t2028
    record_span!(parser, span_start1277, "Read")
    return result1278
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1280 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2043 = parse_relation_id(parser)
    relation_id1279 = _t2043
    consume_literal!(parser, ")")
    _t2044 = Proto.Demand(relation_id=relation_id1279)
    result1281 = _t2044
    record_span!(parser, span_start1280, "Demand")
    return result1281
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1284 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2045 = parse_name(parser)
    name1282 = _t2045
    _t2046 = parse_relation_id(parser)
    relation_id1283 = _t2046
    consume_literal!(parser, ")")
    _t2047 = Proto.Output(name=name1282, relation_id=relation_id1283)
    result1285 = _t2047
    record_span!(parser, span_start1284, "Output")
    return result1285
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1288 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2048 = parse_name(parser)
    name1286 = _t2048
    _t2049 = parse_epoch(parser)
    epoch1287 = _t2049
    consume_literal!(parser, ")")
    _t2050 = Proto.WhatIf(branch=name1286, epoch=epoch1287)
    result1289 = _t2050
    record_span!(parser, span_start1288, "WhatIf")
    return result1289
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1292 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2052 = parse_name(parser)
        _t2051 = _t2052
    else
        _t2051 = nothing
    end
    name1290 = _t2051
    _t2053 = parse_relation_id(parser)
    relation_id1291 = _t2053
    consume_literal!(parser, ")")
    _t2054 = Proto.Abort(name=(!isnothing(name1290) ? name1290 : "abort"), relation_id=relation_id1291)
    result1293 = _t2054
    record_span!(parser, span_start1292, "Abort")
    return result1293
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1297 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2056 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2057 = 0
            else
                _t2057 = -1
            end
            _t2056 = _t2057
        end
        _t2055 = _t2056
    else
        _t2055 = -1
    end
    prediction1294 = _t2055
    if prediction1294 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2059 = parse_export_iceberg_config(parser)
        export_iceberg_config1296 = _t2059
        consume_literal!(parser, ")")
        _t2060 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1296))
        _t2058 = _t2060
    else
        if prediction1294 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2062 = parse_export_csv_config(parser)
            export_csv_config1295 = _t2062
            consume_literal!(parser, ")")
            _t2063 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1295))
            _t2061 = _t2063
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2058 = _t2061
    end
    result1298 = _t2058
    record_span!(parser, span_start1297, "Export")
    return result1298
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1306 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2065 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2066 = 1
            else
                _t2066 = -1
            end
            _t2065 = _t2066
        end
        _t2064 = _t2065
    else
        _t2064 = -1
    end
    prediction1299 = _t2064
    if prediction1299 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2068 = parse_export_csv_path(parser)
        export_csv_path1303 = _t2068
        _t2069 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1304 = _t2069
        _t2070 = parse_config_dict(parser)
        config_dict1305 = _t2070
        consume_literal!(parser, ")")
        _t2071 = construct_export_csv_config(parser, export_csv_path1303, export_csv_columns_list1304, config_dict1305)
        _t2067 = _t2071
    else
        if prediction1299 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2073 = parse_export_csv_path(parser)
            export_csv_path1300 = _t2073
            _t2074 = parse_export_csv_source(parser)
            export_csv_source1301 = _t2074
            _t2075 = parse_csv_config(parser)
            csv_config1302 = _t2075
            consume_literal!(parser, ")")
            _t2076 = construct_export_csv_config_with_source(parser, export_csv_path1300, export_csv_source1301, csv_config1302)
            _t2072 = _t2076
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2067 = _t2072
    end
    result1307 = _t2067
    record_span!(parser, span_start1306, "ExportCSVConfig")
    return result1307
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1308 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1308
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1315 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2078 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2079 = 0
            else
                _t2079 = -1
            end
            _t2078 = _t2079
        end
        _t2077 = _t2078
    else
        _t2077 = -1
    end
    prediction1309 = _t2077
    if prediction1309 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2081 = parse_relation_id(parser)
        relation_id1314 = _t2081
        consume_literal!(parser, ")")
        _t2082 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1314))
        _t2080 = _t2082
    else
        if prediction1309 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1310 = Proto.ExportCSVColumn[]
            cond1311 = match_lookahead_literal(parser, "(", 0)
            while cond1311
                _t2084 = parse_export_csv_column(parser)
                item1312 = _t2084
                push!(xs1310, item1312)
                cond1311 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1313 = xs1310
            consume_literal!(parser, ")")
            _t2085 = Proto.ExportCSVColumns(columns=export_csv_columns1313)
            _t2086 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2085))
            _t2083 = _t2086
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2080 = _t2083
    end
    result1316 = _t2080
    record_span!(parser, span_start1315, "ExportCSVSource")
    return result1316
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1319 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1317 = consume_terminal!(parser, "STRING")
    _t2087 = parse_relation_id(parser)
    relation_id1318 = _t2087
    consume_literal!(parser, ")")
    _t2088 = Proto.ExportCSVColumn(column_name=string1317, column_data=relation_id1318)
    result1320 = _t2088
    record_span!(parser, span_start1319, "ExportCSVColumn")
    return result1320
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1321 = Proto.ExportCSVColumn[]
    cond1322 = match_lookahead_literal(parser, "(", 0)
    while cond1322
        _t2089 = parse_export_csv_column(parser)
        item1323 = _t2089
        push!(xs1321, item1323)
        cond1322 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1324 = xs1321
    consume_literal!(parser, ")")
    return export_csv_columns1324
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1331 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2090 = parse_iceberg_locator(parser)
    iceberg_locator1325 = _t2090
    _t2091 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1326 = _t2091
    _t2092 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1327 = _t2092
    _t2093 = parse_export_iceberg_columns(parser)
    export_iceberg_columns1328 = _t2093
    _t2094 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1329 = _t2094
    if match_lookahead_literal(parser, "{", 0)
        _t2096 = parse_config_dict(parser)
        _t2095 = _t2096
    else
        _t2095 = nothing
    end
    config_dict1330 = _t2095
    consume_literal!(parser, ")")
    _t2097 = construct_export_iceberg_config_full(parser, iceberg_locator1325, iceberg_catalog_config1326, export_iceberg_table_def1327, export_iceberg_columns1328, iceberg_table_properties1329, config_dict1330)
    result1332 = _t2097
    record_span!(parser, span_start1331, "ExportIcebergConfig")
    return result1332
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1334 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2098 = parse_relation_id(parser)
    relation_id1333 = _t2098
    consume_literal!(parser, ")")
    result1335 = relation_id1333
    record_span!(parser, span_start1334, "RelationId")
    return result1335
end

function parse_export_iceberg_columns(parser::ParserState)::Vector{Proto.ExportColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1336 = Proto.ExportColumn[]
    cond1337 = match_lookahead_literal(parser, "(", 0)
    while cond1337
        _t2099 = parse_export_iceberg_column(parser)
        item1338 = _t2099
        push!(xs1336, item1338)
        cond1337 = match_lookahead_literal(parser, "(", 0)
    end
    export_iceberg_columns1339 = xs1336
    consume_literal!(parser, ")")
    return export_iceberg_columns1339
end

function parse_export_iceberg_column(parser::ParserState)::Proto.ExportColumn
    span_start1342 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1340 = consume_terminal!(parser, "STRING")
    _t2100 = parse_boolean_value(parser)
    boolean_value1341 = _t2100
    consume_literal!(parser, ")")
    _t2101 = Proto.ExportColumn(name=string1340, nullable=boolean_value1341)
    result1343 = _t2101
    record_span!(parser, span_start1342, "ExportColumn")
    return result1343
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1344 = Tuple{String, String}[]
    cond1345 = match_lookahead_literal(parser, "(", 0)
    while cond1345
        _t2102 = parse_iceberg_property_entry(parser)
        item1346 = _t2102
        push!(xs1344, item1346)
        cond1345 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1347 = xs1344
    consume_literal!(parser, ")")
    return iceberg_property_entrys1347
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
