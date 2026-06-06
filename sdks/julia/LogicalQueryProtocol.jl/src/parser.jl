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
        _t2111 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2112 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2113 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2114 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2115 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2116 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2117 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2118 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2119 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2120 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2120
    _t2121 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2121
    _t2122 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2122
    _t2123 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2123
    _t2124 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2124
    _t2125 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2125
    _t2126 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2126
    _t2127 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2127
    _t2128 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2128
    _t2129 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2129
    _t2130 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2130
    _t2131 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2131
    _t2132 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2132
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2133 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2133
    _t2134 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2134
    _t2135 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2135
    _t2136 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2136
    _t2137 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2137
    _t2138 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2138
    _t2139 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2139
    _t2140 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2140
    _t2141 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2141
    _t2142 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2142
    _t2143 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2143
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2144 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2144
    _t2145 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2145
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
    _t2146 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2146
    _t2147 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2147
    _t2148 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2148
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2149 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2149
    _t2150 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2150
    _t2151 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2151
    _t2152 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2152
    _t2153 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2153
    _t2154 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2154
    _t2155 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2155
    _t2156 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2156
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2157 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2157
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2158 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2158
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2159 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2159
end

function construct_csv_data(parser::ParserState, locator::Proto.CSVLocator, config::Proto.CSVConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, target_opt::Union{Nothing, Proto.CSVTarget}, asof::String)::Proto.CSVData
    _t2160 = Proto.CSVData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), asof=asof, target=target_opt)
    return _t2160
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2161 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2161
    _t2162 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2162
    _t2163 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2163
    table_props = Dict(table_property_pairs)
    _t2164 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2164
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start683 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1355 = parse_configure(parser)
        _t1354 = _t1355
    else
        _t1354 = nothing
    end
    configure677 = _t1354
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1357 = parse_sync(parser)
        _t1356 = _t1357
    else
        _t1356 = nothing
    end
    sync678 = _t1356
    xs679 = Proto.Epoch[]
    cond680 = match_lookahead_literal(parser, "(", 0)
    while cond680
        _t1358 = parse_epoch(parser)
        item681 = _t1358
        push!(xs679, item681)
        cond680 = match_lookahead_literal(parser, "(", 0)
    end
    epochs682 = xs679
    consume_literal!(parser, ")")
    _t1359 = default_configure(parser)
    _t1360 = Proto.Transaction(epochs=epochs682, configure=(!isnothing(configure677) ? configure677 : _t1359), sync=sync678)
    result684 = _t1360
    record_span!(parser, span_start683, "Transaction")
    return result684
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start686 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1361 = parse_config_dict(parser)
    config_dict685 = _t1361
    consume_literal!(parser, ")")
    _t1362 = construct_configure(parser, config_dict685)
    result687 = _t1362
    record_span!(parser, span_start686, "Configure")
    return result687
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs688 = Tuple{String, Proto.Value}[]
    cond689 = match_lookahead_literal(parser, ":", 0)
    while cond689
        _t1363 = parse_config_key_value(parser)
        item690 = _t1363
        push!(xs688, item690)
        cond689 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values691 = xs688
    consume_literal!(parser, "}")
    return config_key_values691
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol692 = consume_terminal!(parser, "SYMBOL")
    _t1364 = parse_raw_value(parser)
    raw_value693 = _t1364
    return (symbol692, raw_value693,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start707 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1365 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1366 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1367 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1369 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1370 = 0
                        else
                            _t1370 = -1
                        end
                        _t1369 = _t1370
                    end
                    _t1368 = _t1369
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1371 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1372 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1373 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1374 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1375 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1376 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1377 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1378 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1379 = 10
                                                    else
                                                        _t1379 = -1
                                                    end
                                                    _t1378 = _t1379
                                                end
                                                _t1377 = _t1378
                                            end
                                            _t1376 = _t1377
                                        end
                                        _t1375 = _t1376
                                    end
                                    _t1374 = _t1375
                                end
                                _t1373 = _t1374
                            end
                            _t1372 = _t1373
                        end
                        _t1371 = _t1372
                    end
                    _t1368 = _t1371
                end
                _t1367 = _t1368
            end
            _t1366 = _t1367
        end
        _t1365 = _t1366
    end
    prediction694 = _t1365
    if prediction694 == 12
        _t1381 = parse_boolean_value(parser)
        boolean_value706 = _t1381
        _t1382 = Proto.Value(value=OneOf(:boolean_value, boolean_value706))
        _t1380 = _t1382
    else
        if prediction694 == 11
            consume_literal!(parser, "missing")
            _t1384 = Proto.MissingValue()
            _t1385 = Proto.Value(value=OneOf(:missing_value, _t1384))
            _t1383 = _t1385
        else
            if prediction694 == 10
                decimal705 = consume_terminal!(parser, "DECIMAL")
                _t1387 = Proto.Value(value=OneOf(:decimal_value, decimal705))
                _t1386 = _t1387
            else
                if prediction694 == 9
                    int128704 = consume_terminal!(parser, "INT128")
                    _t1389 = Proto.Value(value=OneOf(:int128_value, int128704))
                    _t1388 = _t1389
                else
                    if prediction694 == 8
                        uint128703 = consume_terminal!(parser, "UINT128")
                        _t1391 = Proto.Value(value=OneOf(:uint128_value, uint128703))
                        _t1390 = _t1391
                    else
                        if prediction694 == 7
                            uint32702 = consume_terminal!(parser, "UINT32")
                            _t1393 = Proto.Value(value=OneOf(:uint32_value, uint32702))
                            _t1392 = _t1393
                        else
                            if prediction694 == 6
                                float701 = consume_terminal!(parser, "FLOAT")
                                _t1395 = Proto.Value(value=OneOf(:float_value, float701))
                                _t1394 = _t1395
                            else
                                if prediction694 == 5
                                    float32700 = consume_terminal!(parser, "FLOAT32")
                                    _t1397 = Proto.Value(value=OneOf(:float32_value, float32700))
                                    _t1396 = _t1397
                                else
                                    if prediction694 == 4
                                        int699 = consume_terminal!(parser, "INT")
                                        _t1399 = Proto.Value(value=OneOf(:int_value, int699))
                                        _t1398 = _t1399
                                    else
                                        if prediction694 == 3
                                            int32698 = consume_terminal!(parser, "INT32")
                                            _t1401 = Proto.Value(value=OneOf(:int32_value, int32698))
                                            _t1400 = _t1401
                                        else
                                            if prediction694 == 2
                                                string697 = consume_terminal!(parser, "STRING")
                                                _t1403 = Proto.Value(value=OneOf(:string_value, string697))
                                                _t1402 = _t1403
                                            else
                                                if prediction694 == 1
                                                    _t1405 = parse_raw_datetime(parser)
                                                    raw_datetime696 = _t1405
                                                    _t1406 = Proto.Value(value=OneOf(:datetime_value, raw_datetime696))
                                                    _t1404 = _t1406
                                                else
                                                    if prediction694 == 0
                                                        _t1408 = parse_raw_date(parser)
                                                        raw_date695 = _t1408
                                                        _t1409 = Proto.Value(value=OneOf(:date_value, raw_date695))
                                                        _t1407 = _t1409
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1404 = _t1407
                                                end
                                                _t1402 = _t1404
                                            end
                                            _t1400 = _t1402
                                        end
                                        _t1398 = _t1400
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
            _t1383 = _t1386
        end
        _t1380 = _t1383
    end
    result708 = _t1380
    record_span!(parser, span_start707, "Value")
    return result708
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start712 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int709 = consume_terminal!(parser, "INT")
    int_3710 = consume_terminal!(parser, "INT")
    int_4711 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1410 = Proto.DateValue(year=Int32(int709), month=Int32(int_3710), day=Int32(int_4711))
    result713 = _t1410
    record_span!(parser, span_start712, "DateValue")
    return result713
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start721 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int714 = consume_terminal!(parser, "INT")
    int_3715 = consume_terminal!(parser, "INT")
    int_4716 = consume_terminal!(parser, "INT")
    int_5717 = consume_terminal!(parser, "INT")
    int_6718 = consume_terminal!(parser, "INT")
    int_7719 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1411 = consume_terminal!(parser, "INT")
    else
        _t1411 = nothing
    end
    int_8720 = _t1411
    consume_literal!(parser, ")")
    _t1412 = Proto.DateTimeValue(year=Int32(int714), month=Int32(int_3715), day=Int32(int_4716), hour=Int32(int_5717), minute=Int32(int_6718), second=Int32(int_7719), microsecond=Int32((!isnothing(int_8720) ? int_8720 : 0)))
    result722 = _t1412
    record_span!(parser, span_start721, "DateTimeValue")
    return result722
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1413 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1414 = 1
        else
            _t1414 = -1
        end
        _t1413 = _t1414
    end
    prediction723 = _t1413
    if prediction723 == 1
        consume_literal!(parser, "false")
        _t1415 = false
    else
        if prediction723 == 0
            consume_literal!(parser, "true")
            _t1416 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1415 = _t1416
    end
    return _t1415
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start728 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs724 = Proto.FragmentId[]
    cond725 = match_lookahead_literal(parser, ":", 0)
    while cond725
        _t1417 = parse_fragment_id(parser)
        item726 = _t1417
        push!(xs724, item726)
        cond725 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids727 = xs724
    consume_literal!(parser, ")")
    _t1418 = Proto.Sync(fragments=fragment_ids727)
    result729 = _t1418
    record_span!(parser, span_start728, "Sync")
    return result729
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start731 = span_start(parser)
    consume_literal!(parser, ":")
    symbol730 = consume_terminal!(parser, "SYMBOL")
    result732 = Proto.FragmentId(Vector{UInt8}(symbol730))
    record_span!(parser, span_start731, "FragmentId")
    return result732
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start735 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1420 = parse_epoch_writes(parser)
        _t1419 = _t1420
    else
        _t1419 = nothing
    end
    epoch_writes733 = _t1419
    if match_lookahead_literal(parser, "(", 0)
        _t1422 = parse_epoch_reads(parser)
        _t1421 = _t1422
    else
        _t1421 = nothing
    end
    epoch_reads734 = _t1421
    consume_literal!(parser, ")")
    _t1423 = Proto.Epoch(writes=(!isnothing(epoch_writes733) ? epoch_writes733 : Proto.Write[]), reads=(!isnothing(epoch_reads734) ? epoch_reads734 : Proto.Read[]))
    result736 = _t1423
    record_span!(parser, span_start735, "Epoch")
    return result736
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs737 = Proto.Write[]
    cond738 = match_lookahead_literal(parser, "(", 0)
    while cond738
        _t1424 = parse_write(parser)
        item739 = _t1424
        push!(xs737, item739)
        cond738 = match_lookahead_literal(parser, "(", 0)
    end
    writes740 = xs737
    consume_literal!(parser, ")")
    return writes740
end

function parse_write(parser::ParserState)::Proto.Write
    span_start746 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1426 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1427 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1428 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1429 = 2
                    else
                        _t1429 = -1
                    end
                    _t1428 = _t1429
                end
                _t1427 = _t1428
            end
            _t1426 = _t1427
        end
        _t1425 = _t1426
    else
        _t1425 = -1
    end
    prediction741 = _t1425
    if prediction741 == 3
        _t1431 = parse_snapshot(parser)
        snapshot745 = _t1431
        _t1432 = Proto.Write(write_type=OneOf(:snapshot, snapshot745))
        _t1430 = _t1432
    else
        if prediction741 == 2
            _t1434 = parse_context(parser)
            context744 = _t1434
            _t1435 = Proto.Write(write_type=OneOf(:context, context744))
            _t1433 = _t1435
        else
            if prediction741 == 1
                _t1437 = parse_undefine(parser)
                undefine743 = _t1437
                _t1438 = Proto.Write(write_type=OneOf(:undefine, undefine743))
                _t1436 = _t1438
            else
                if prediction741 == 0
                    _t1440 = parse_define(parser)
                    define742 = _t1440
                    _t1441 = Proto.Write(write_type=OneOf(:define, define742))
                    _t1439 = _t1441
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1436 = _t1439
            end
            _t1433 = _t1436
        end
        _t1430 = _t1433
    end
    result747 = _t1430
    record_span!(parser, span_start746, "Write")
    return result747
end

function parse_define(parser::ParserState)::Proto.Define
    span_start749 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1442 = parse_fragment(parser)
    fragment748 = _t1442
    consume_literal!(parser, ")")
    _t1443 = Proto.Define(fragment=fragment748)
    result750 = _t1443
    record_span!(parser, span_start749, "Define")
    return result750
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start756 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1444 = parse_new_fragment_id(parser)
    new_fragment_id751 = _t1444
    xs752 = Proto.Declaration[]
    cond753 = match_lookahead_literal(parser, "(", 0)
    while cond753
        _t1445 = parse_declaration(parser)
        item754 = _t1445
        push!(xs752, item754)
        cond753 = match_lookahead_literal(parser, "(", 0)
    end
    declarations755 = xs752
    consume_literal!(parser, ")")
    result757 = construct_fragment(parser, new_fragment_id751, declarations755)
    record_span!(parser, span_start756, "Fragment")
    return result757
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start759 = span_start(parser)
    _t1446 = parse_fragment_id(parser)
    fragment_id758 = _t1446
    start_fragment!(parser, fragment_id758)
    result760 = fragment_id758
    record_span!(parser, span_start759, "FragmentId")
    return result760
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start766 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1448 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1449 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1450 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1451 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1452 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1453 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1454 = 1
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
    else
        _t1447 = -1
    end
    prediction761 = _t1447
    if prediction761 == 3
        _t1456 = parse_data(parser)
        data765 = _t1456
        _t1457 = Proto.Declaration(declaration_type=OneOf(:data, data765))
        _t1455 = _t1457
    else
        if prediction761 == 2
            _t1459 = parse_constraint(parser)
            constraint764 = _t1459
            _t1460 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint764))
            _t1458 = _t1460
        else
            if prediction761 == 1
                _t1462 = parse_algorithm(parser)
                algorithm763 = _t1462
                _t1463 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm763))
                _t1461 = _t1463
            else
                if prediction761 == 0
                    _t1465 = parse_def(parser)
                    def762 = _t1465
                    _t1466 = Proto.Declaration(declaration_type=OneOf(:def, def762))
                    _t1464 = _t1466
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1461 = _t1464
            end
            _t1458 = _t1461
        end
        _t1455 = _t1458
    end
    result767 = _t1455
    record_span!(parser, span_start766, "Declaration")
    return result767
end

function parse_def(parser::ParserState)::Proto.Def
    span_start771 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1467 = parse_relation_id(parser)
    relation_id768 = _t1467
    _t1468 = parse_abstraction(parser)
    abstraction769 = _t1468
    if match_lookahead_literal(parser, "(", 0)
        _t1470 = parse_attrs(parser)
        _t1469 = _t1470
    else
        _t1469 = nothing
    end
    attrs770 = _t1469
    consume_literal!(parser, ")")
    _t1471 = Proto.Def(name=relation_id768, body=abstraction769, attrs=(!isnothing(attrs770) ? attrs770 : Proto.Attribute[]))
    result772 = _t1471
    record_span!(parser, span_start771, "Def")
    return result772
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start776 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1472 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1473 = 1
        else
            _t1473 = -1
        end
        _t1472 = _t1473
    end
    prediction773 = _t1472
    if prediction773 == 1
        uint128775 = consume_terminal!(parser, "UINT128")
        _t1474 = Proto.RelationId(uint128775.low, uint128775.high)
    else
        if prediction773 == 0
            consume_literal!(parser, ":")
            symbol774 = consume_terminal!(parser, "SYMBOL")
            _t1475 = relation_id_from_string(parser, symbol774)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1474 = _t1475
    end
    result777 = _t1474
    record_span!(parser, span_start776, "RelationId")
    return result777
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start780 = span_start(parser)
    consume_literal!(parser, "(")
    _t1476 = parse_bindings(parser)
    bindings778 = _t1476
    _t1477 = parse_formula(parser)
    formula779 = _t1477
    consume_literal!(parser, ")")
    _t1478 = Proto.Abstraction(vars=vcat(bindings778[1], !isnothing(bindings778[2]) ? bindings778[2] : []), value=formula779)
    result781 = _t1478
    record_span!(parser, span_start780, "Abstraction")
    return result781
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs782 = Proto.Binding[]
    cond783 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond783
        _t1479 = parse_binding(parser)
        item784 = _t1479
        push!(xs782, item784)
        cond783 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings785 = xs782
    if match_lookahead_literal(parser, "|", 0)
        _t1481 = parse_value_bindings(parser)
        _t1480 = _t1481
    else
        _t1480 = nothing
    end
    value_bindings786 = _t1480
    consume_literal!(parser, "]")
    return (bindings785, (!isnothing(value_bindings786) ? value_bindings786 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start789 = span_start(parser)
    symbol787 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1482 = parse_type(parser)
    type788 = _t1482
    _t1483 = Proto.Var(name=symbol787)
    _t1484 = Proto.Binding(var=_t1483, var"#type"=type788)
    result790 = _t1484
    record_span!(parser, span_start789, "Binding")
    return result790
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start806 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1485 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1486 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1487 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1488 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1489 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1490 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1491 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1492 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1493 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1494 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1495 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1496 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1497 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1498 = 9
                                                        else
                                                            _t1498 = -1
                                                        end
                                                        _t1497 = _t1498
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
    prediction791 = _t1485
    if prediction791 == 13
        _t1500 = parse_uint32_type(parser)
        uint32_type805 = _t1500
        _t1501 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type805))
        _t1499 = _t1501
    else
        if prediction791 == 12
            _t1503 = parse_float32_type(parser)
            float32_type804 = _t1503
            _t1504 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type804))
            _t1502 = _t1504
        else
            if prediction791 == 11
                _t1506 = parse_int32_type(parser)
                int32_type803 = _t1506
                _t1507 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type803))
                _t1505 = _t1507
            else
                if prediction791 == 10
                    _t1509 = parse_boolean_type(parser)
                    boolean_type802 = _t1509
                    _t1510 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type802))
                    _t1508 = _t1510
                else
                    if prediction791 == 9
                        _t1512 = parse_decimal_type(parser)
                        decimal_type801 = _t1512
                        _t1513 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type801))
                        _t1511 = _t1513
                    else
                        if prediction791 == 8
                            _t1515 = parse_missing_type(parser)
                            missing_type800 = _t1515
                            _t1516 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type800))
                            _t1514 = _t1516
                        else
                            if prediction791 == 7
                                _t1518 = parse_datetime_type(parser)
                                datetime_type799 = _t1518
                                _t1519 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type799))
                                _t1517 = _t1519
                            else
                                if prediction791 == 6
                                    _t1521 = parse_date_type(parser)
                                    date_type798 = _t1521
                                    _t1522 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type798))
                                    _t1520 = _t1522
                                else
                                    if prediction791 == 5
                                        _t1524 = parse_int128_type(parser)
                                        int128_type797 = _t1524
                                        _t1525 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type797))
                                        _t1523 = _t1525
                                    else
                                        if prediction791 == 4
                                            _t1527 = parse_uint128_type(parser)
                                            uint128_type796 = _t1527
                                            _t1528 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type796))
                                            _t1526 = _t1528
                                        else
                                            if prediction791 == 3
                                                _t1530 = parse_float_type(parser)
                                                float_type795 = _t1530
                                                _t1531 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type795))
                                                _t1529 = _t1531
                                            else
                                                if prediction791 == 2
                                                    _t1533 = parse_int_type(parser)
                                                    int_type794 = _t1533
                                                    _t1534 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type794))
                                                    _t1532 = _t1534
                                                else
                                                    if prediction791 == 1
                                                        _t1536 = parse_string_type(parser)
                                                        string_type793 = _t1536
                                                        _t1537 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type793))
                                                        _t1535 = _t1537
                                                    else
                                                        if prediction791 == 0
                                                            _t1539 = parse_unspecified_type(parser)
                                                            unspecified_type792 = _t1539
                                                            _t1540 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type792))
                                                            _t1538 = _t1540
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1535 = _t1538
                                                    end
                                                    _t1532 = _t1535
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
    result807 = _t1499
    record_span!(parser, span_start806, "Type")
    return result807
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start808 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1541 = Proto.UnspecifiedType()
    result809 = _t1541
    record_span!(parser, span_start808, "UnspecifiedType")
    return result809
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start810 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1542 = Proto.StringType()
    result811 = _t1542
    record_span!(parser, span_start810, "StringType")
    return result811
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start812 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1543 = Proto.IntType()
    result813 = _t1543
    record_span!(parser, span_start812, "IntType")
    return result813
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start814 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1544 = Proto.FloatType()
    result815 = _t1544
    record_span!(parser, span_start814, "FloatType")
    return result815
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start816 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1545 = Proto.UInt128Type()
    result817 = _t1545
    record_span!(parser, span_start816, "UInt128Type")
    return result817
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start818 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1546 = Proto.Int128Type()
    result819 = _t1546
    record_span!(parser, span_start818, "Int128Type")
    return result819
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start820 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1547 = Proto.DateType()
    result821 = _t1547
    record_span!(parser, span_start820, "DateType")
    return result821
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start822 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1548 = Proto.DateTimeType()
    result823 = _t1548
    record_span!(parser, span_start822, "DateTimeType")
    return result823
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start824 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1549 = Proto.MissingType()
    result825 = _t1549
    record_span!(parser, span_start824, "MissingType")
    return result825
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start828 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int826 = consume_terminal!(parser, "INT")
    int_3827 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1550 = Proto.DecimalType(precision=Int32(int826), scale=Int32(int_3827))
    result829 = _t1550
    record_span!(parser, span_start828, "DecimalType")
    return result829
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start830 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1551 = Proto.BooleanType()
    result831 = _t1551
    record_span!(parser, span_start830, "BooleanType")
    return result831
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start832 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1552 = Proto.Int32Type()
    result833 = _t1552
    record_span!(parser, span_start832, "Int32Type")
    return result833
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start834 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1553 = Proto.Float32Type()
    result835 = _t1553
    record_span!(parser, span_start834, "Float32Type")
    return result835
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start836 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1554 = Proto.UInt32Type()
    result837 = _t1554
    record_span!(parser, span_start836, "UInt32Type")
    return result837
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs838 = Proto.Binding[]
    cond839 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond839
        _t1555 = parse_binding(parser)
        item840 = _t1555
        push!(xs838, item840)
        cond839 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings841 = xs838
    return bindings841
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start856 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1557 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1558 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1559 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1560 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1561 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1562 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1563 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1564 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1565 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1566 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1567 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1568 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1569 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1570 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1571 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1572 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1573 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1574 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1575 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1576 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1577 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1578 = 10
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
    else
        _t1556 = -1
    end
    prediction842 = _t1556
    if prediction842 == 12
        _t1580 = parse_cast(parser)
        cast855 = _t1580
        _t1581 = Proto.Formula(formula_type=OneOf(:cast, cast855))
        _t1579 = _t1581
    else
        if prediction842 == 11
            _t1583 = parse_rel_atom(parser)
            rel_atom854 = _t1583
            _t1584 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom854))
            _t1582 = _t1584
        else
            if prediction842 == 10
                _t1586 = parse_primitive(parser)
                primitive853 = _t1586
                _t1587 = Proto.Formula(formula_type=OneOf(:primitive, primitive853))
                _t1585 = _t1587
            else
                if prediction842 == 9
                    _t1589 = parse_pragma(parser)
                    pragma852 = _t1589
                    _t1590 = Proto.Formula(formula_type=OneOf(:pragma, pragma852))
                    _t1588 = _t1590
                else
                    if prediction842 == 8
                        _t1592 = parse_atom(parser)
                        atom851 = _t1592
                        _t1593 = Proto.Formula(formula_type=OneOf(:atom, atom851))
                        _t1591 = _t1593
                    else
                        if prediction842 == 7
                            _t1595 = parse_ffi(parser)
                            ffi850 = _t1595
                            _t1596 = Proto.Formula(formula_type=OneOf(:ffi, ffi850))
                            _t1594 = _t1596
                        else
                            if prediction842 == 6
                                _t1598 = parse_not(parser)
                                not849 = _t1598
                                _t1599 = Proto.Formula(formula_type=OneOf(:not, not849))
                                _t1597 = _t1599
                            else
                                if prediction842 == 5
                                    _t1601 = parse_disjunction(parser)
                                    disjunction848 = _t1601
                                    _t1602 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction848))
                                    _t1600 = _t1602
                                else
                                    if prediction842 == 4
                                        _t1604 = parse_conjunction(parser)
                                        conjunction847 = _t1604
                                        _t1605 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction847))
                                        _t1603 = _t1605
                                    else
                                        if prediction842 == 3
                                            _t1607 = parse_reduce(parser)
                                            reduce846 = _t1607
                                            _t1608 = Proto.Formula(formula_type=OneOf(:reduce, reduce846))
                                            _t1606 = _t1608
                                        else
                                            if prediction842 == 2
                                                _t1610 = parse_exists(parser)
                                                exists845 = _t1610
                                                _t1611 = Proto.Formula(formula_type=OneOf(:exists, exists845))
                                                _t1609 = _t1611
                                            else
                                                if prediction842 == 1
                                                    _t1613 = parse_false(parser)
                                                    false844 = _t1613
                                                    _t1614 = Proto.Formula(formula_type=OneOf(:disjunction, false844))
                                                    _t1612 = _t1614
                                                else
                                                    if prediction842 == 0
                                                        _t1616 = parse_true(parser)
                                                        true843 = _t1616
                                                        _t1617 = Proto.Formula(formula_type=OneOf(:conjunction, true843))
                                                        _t1615 = _t1617
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1612 = _t1615
                                                end
                                                _t1609 = _t1612
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
    result857 = _t1579
    record_span!(parser, span_start856, "Formula")
    return result857
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start858 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1618 = Proto.Conjunction(args=Proto.Formula[])
    result859 = _t1618
    record_span!(parser, span_start858, "Conjunction")
    return result859
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start860 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1619 = Proto.Disjunction(args=Proto.Formula[])
    result861 = _t1619
    record_span!(parser, span_start860, "Disjunction")
    return result861
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start864 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1620 = parse_bindings(parser)
    bindings862 = _t1620
    _t1621 = parse_formula(parser)
    formula863 = _t1621
    consume_literal!(parser, ")")
    _t1622 = Proto.Abstraction(vars=vcat(bindings862[1], !isnothing(bindings862[2]) ? bindings862[2] : []), value=formula863)
    _t1623 = Proto.Exists(body=_t1622)
    result865 = _t1623
    record_span!(parser, span_start864, "Exists")
    return result865
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start869 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1624 = parse_abstraction(parser)
    abstraction866 = _t1624
    _t1625 = parse_abstraction(parser)
    abstraction_3867 = _t1625
    _t1626 = parse_terms(parser)
    terms868 = _t1626
    consume_literal!(parser, ")")
    _t1627 = Proto.Reduce(op=abstraction866, body=abstraction_3867, terms=terms868)
    result870 = _t1627
    record_span!(parser, span_start869, "Reduce")
    return result870
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs871 = Proto.Term[]
    cond872 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond872
        _t1628 = parse_term(parser)
        item873 = _t1628
        push!(xs871, item873)
        cond872 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms874 = xs871
    consume_literal!(parser, ")")
    return terms874
end

function parse_term(parser::ParserState)::Proto.Term
    span_start878 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1629 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1630 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1631 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1632 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1633 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1634 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1635 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1636 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1637 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1638 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1639 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1640 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1641 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1642 = 1
                                                        else
                                                            _t1642 = -1
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
                _t1631 = _t1632
            end
            _t1630 = _t1631
        end
        _t1629 = _t1630
    end
    prediction875 = _t1629
    if prediction875 == 1
        _t1644 = parse_value(parser)
        value877 = _t1644
        _t1645 = Proto.Term(term_type=OneOf(:constant, value877))
        _t1643 = _t1645
    else
        if prediction875 == 0
            _t1647 = parse_var(parser)
            var876 = _t1647
            _t1648 = Proto.Term(term_type=OneOf(:var, var876))
            _t1646 = _t1648
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1643 = _t1646
    end
    result879 = _t1643
    record_span!(parser, span_start878, "Term")
    return result879
end

function parse_var(parser::ParserState)::Proto.Var
    span_start881 = span_start(parser)
    symbol880 = consume_terminal!(parser, "SYMBOL")
    _t1649 = Proto.Var(name=symbol880)
    result882 = _t1649
    record_span!(parser, span_start881, "Var")
    return result882
end

function parse_value(parser::ParserState)::Proto.Value
    span_start896 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1650 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1651 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1652 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1654 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1655 = 0
                        else
                            _t1655 = -1
                        end
                        _t1654 = _t1655
                    end
                    _t1653 = _t1654
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1656 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1657 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1658 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1659 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1660 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1661 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1662 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1663 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1664 = 10
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
                                end
                                _t1658 = _t1659
                            end
                            _t1657 = _t1658
                        end
                        _t1656 = _t1657
                    end
                    _t1653 = _t1656
                end
                _t1652 = _t1653
            end
            _t1651 = _t1652
        end
        _t1650 = _t1651
    end
    prediction883 = _t1650
    if prediction883 == 12
        _t1666 = parse_boolean_value(parser)
        boolean_value895 = _t1666
        _t1667 = Proto.Value(value=OneOf(:boolean_value, boolean_value895))
        _t1665 = _t1667
    else
        if prediction883 == 11
            consume_literal!(parser, "missing")
            _t1669 = Proto.MissingValue()
            _t1670 = Proto.Value(value=OneOf(:missing_value, _t1669))
            _t1668 = _t1670
        else
            if prediction883 == 10
                formatted_decimal894 = consume_terminal!(parser, "DECIMAL")
                _t1672 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal894))
                _t1671 = _t1672
            else
                if prediction883 == 9
                    formatted_int128893 = consume_terminal!(parser, "INT128")
                    _t1674 = Proto.Value(value=OneOf(:int128_value, formatted_int128893))
                    _t1673 = _t1674
                else
                    if prediction883 == 8
                        formatted_uint128892 = consume_terminal!(parser, "UINT128")
                        _t1676 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128892))
                        _t1675 = _t1676
                    else
                        if prediction883 == 7
                            formatted_uint32891 = consume_terminal!(parser, "UINT32")
                            _t1678 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32891))
                            _t1677 = _t1678
                        else
                            if prediction883 == 6
                                formatted_float890 = consume_terminal!(parser, "FLOAT")
                                _t1680 = Proto.Value(value=OneOf(:float_value, formatted_float890))
                                _t1679 = _t1680
                            else
                                if prediction883 == 5
                                    formatted_float32889 = consume_terminal!(parser, "FLOAT32")
                                    _t1682 = Proto.Value(value=OneOf(:float32_value, formatted_float32889))
                                    _t1681 = _t1682
                                else
                                    if prediction883 == 4
                                        formatted_int888 = consume_terminal!(parser, "INT")
                                        _t1684 = Proto.Value(value=OneOf(:int_value, formatted_int888))
                                        _t1683 = _t1684
                                    else
                                        if prediction883 == 3
                                            formatted_int32887 = consume_terminal!(parser, "INT32")
                                            _t1686 = Proto.Value(value=OneOf(:int32_value, formatted_int32887))
                                            _t1685 = _t1686
                                        else
                                            if prediction883 == 2
                                                formatted_string886 = consume_terminal!(parser, "STRING")
                                                _t1688 = Proto.Value(value=OneOf(:string_value, formatted_string886))
                                                _t1687 = _t1688
                                            else
                                                if prediction883 == 1
                                                    _t1690 = parse_datetime(parser)
                                                    datetime885 = _t1690
                                                    _t1691 = Proto.Value(value=OneOf(:datetime_value, datetime885))
                                                    _t1689 = _t1691
                                                else
                                                    if prediction883 == 0
                                                        _t1693 = parse_date(parser)
                                                        date884 = _t1693
                                                        _t1694 = Proto.Value(value=OneOf(:date_value, date884))
                                                        _t1692 = _t1694
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1689 = _t1692
                                                end
                                                _t1687 = _t1689
                                            end
                                            _t1685 = _t1687
                                        end
                                        _t1683 = _t1685
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
            _t1668 = _t1671
        end
        _t1665 = _t1668
    end
    result897 = _t1665
    record_span!(parser, span_start896, "Value")
    return result897
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start901 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int898 = consume_terminal!(parser, "INT")
    formatted_int_3899 = consume_terminal!(parser, "INT")
    formatted_int_4900 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1695 = Proto.DateValue(year=Int32(formatted_int898), month=Int32(formatted_int_3899), day=Int32(formatted_int_4900))
    result902 = _t1695
    record_span!(parser, span_start901, "DateValue")
    return result902
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start910 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int903 = consume_terminal!(parser, "INT")
    formatted_int_3904 = consume_terminal!(parser, "INT")
    formatted_int_4905 = consume_terminal!(parser, "INT")
    formatted_int_5906 = consume_terminal!(parser, "INT")
    formatted_int_6907 = consume_terminal!(parser, "INT")
    formatted_int_7908 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1696 = consume_terminal!(parser, "INT")
    else
        _t1696 = nothing
    end
    formatted_int_8909 = _t1696
    consume_literal!(parser, ")")
    _t1697 = Proto.DateTimeValue(year=Int32(formatted_int903), month=Int32(formatted_int_3904), day=Int32(formatted_int_4905), hour=Int32(formatted_int_5906), minute=Int32(formatted_int_6907), second=Int32(formatted_int_7908), microsecond=Int32((!isnothing(formatted_int_8909) ? formatted_int_8909 : 0)))
    result911 = _t1697
    record_span!(parser, span_start910, "DateTimeValue")
    return result911
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start916 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs912 = Proto.Formula[]
    cond913 = match_lookahead_literal(parser, "(", 0)
    while cond913
        _t1698 = parse_formula(parser)
        item914 = _t1698
        push!(xs912, item914)
        cond913 = match_lookahead_literal(parser, "(", 0)
    end
    formulas915 = xs912
    consume_literal!(parser, ")")
    _t1699 = Proto.Conjunction(args=formulas915)
    result917 = _t1699
    record_span!(parser, span_start916, "Conjunction")
    return result917
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start922 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs918 = Proto.Formula[]
    cond919 = match_lookahead_literal(parser, "(", 0)
    while cond919
        _t1700 = parse_formula(parser)
        item920 = _t1700
        push!(xs918, item920)
        cond919 = match_lookahead_literal(parser, "(", 0)
    end
    formulas921 = xs918
    consume_literal!(parser, ")")
    _t1701 = Proto.Disjunction(args=formulas921)
    result923 = _t1701
    record_span!(parser, span_start922, "Disjunction")
    return result923
end

function parse_not(parser::ParserState)::Proto.Not
    span_start925 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1702 = parse_formula(parser)
    formula924 = _t1702
    consume_literal!(parser, ")")
    _t1703 = Proto.Not(arg=formula924)
    result926 = _t1703
    record_span!(parser, span_start925, "Not")
    return result926
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start930 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1704 = parse_name(parser)
    name927 = _t1704
    _t1705 = parse_ffi_args(parser)
    ffi_args928 = _t1705
    _t1706 = parse_terms(parser)
    terms929 = _t1706
    consume_literal!(parser, ")")
    _t1707 = Proto.FFI(name=name927, args=ffi_args928, terms=terms929)
    result931 = _t1707
    record_span!(parser, span_start930, "FFI")
    return result931
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol932 = consume_terminal!(parser, "SYMBOL")
    return symbol932
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs933 = Proto.Abstraction[]
    cond934 = match_lookahead_literal(parser, "(", 0)
    while cond934
        _t1708 = parse_abstraction(parser)
        item935 = _t1708
        push!(xs933, item935)
        cond934 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions936 = xs933
    consume_literal!(parser, ")")
    return abstractions936
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start942 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1709 = parse_relation_id(parser)
    relation_id937 = _t1709
    xs938 = Proto.Term[]
    cond939 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond939
        _t1710 = parse_term(parser)
        item940 = _t1710
        push!(xs938, item940)
        cond939 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms941 = xs938
    consume_literal!(parser, ")")
    _t1711 = Proto.Atom(name=relation_id937, terms=terms941)
    result943 = _t1711
    record_span!(parser, span_start942, "Atom")
    return result943
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start949 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1712 = parse_name(parser)
    name944 = _t1712
    xs945 = Proto.Term[]
    cond946 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond946
        _t1713 = parse_term(parser)
        item947 = _t1713
        push!(xs945, item947)
        cond946 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms948 = xs945
    consume_literal!(parser, ")")
    _t1714 = Proto.Pragma(name=name944, terms=terms948)
    result950 = _t1714
    record_span!(parser, span_start949, "Pragma")
    return result950
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start966 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1716 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1717 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1718 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1719 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1720 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1721 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1722 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1723 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1724 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1725 = 7
                                            else
                                                _t1725 = -1
                                            end
                                            _t1724 = _t1725
                                        end
                                        _t1723 = _t1724
                                    end
                                    _t1722 = _t1723
                                end
                                _t1721 = _t1722
                            end
                            _t1720 = _t1721
                        end
                        _t1719 = _t1720
                    end
                    _t1718 = _t1719
                end
                _t1717 = _t1718
            end
            _t1716 = _t1717
        end
        _t1715 = _t1716
    else
        _t1715 = -1
    end
    prediction951 = _t1715
    if prediction951 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1727 = parse_name(parser)
        name961 = _t1727
        xs962 = Proto.RelTerm[]
        cond963 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond963
            _t1728 = parse_rel_term(parser)
            item964 = _t1728
            push!(xs962, item964)
            cond963 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms965 = xs962
        consume_literal!(parser, ")")
        _t1729 = Proto.Primitive(name=name961, terms=rel_terms965)
        _t1726 = _t1729
    else
        if prediction951 == 8
            _t1731 = parse_divide(parser)
            divide960 = _t1731
            _t1730 = divide960
        else
            if prediction951 == 7
                _t1733 = parse_multiply(parser)
                multiply959 = _t1733
                _t1732 = multiply959
            else
                if prediction951 == 6
                    _t1735 = parse_minus(parser)
                    minus958 = _t1735
                    _t1734 = minus958
                else
                    if prediction951 == 5
                        _t1737 = parse_add(parser)
                        add957 = _t1737
                        _t1736 = add957
                    else
                        if prediction951 == 4
                            _t1739 = parse_gt_eq(parser)
                            gt_eq956 = _t1739
                            _t1738 = gt_eq956
                        else
                            if prediction951 == 3
                                _t1741 = parse_gt(parser)
                                gt955 = _t1741
                                _t1740 = gt955
                            else
                                if prediction951 == 2
                                    _t1743 = parse_lt_eq(parser)
                                    lt_eq954 = _t1743
                                    _t1742 = lt_eq954
                                else
                                    if prediction951 == 1
                                        _t1745 = parse_lt(parser)
                                        lt953 = _t1745
                                        _t1744 = lt953
                                    else
                                        if prediction951 == 0
                                            _t1747 = parse_eq(parser)
                                            eq952 = _t1747
                                            _t1746 = eq952
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1744 = _t1746
                                    end
                                    _t1742 = _t1744
                                end
                                _t1740 = _t1742
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
        _t1726 = _t1730
    end
    result967 = _t1726
    record_span!(parser, span_start966, "Primitive")
    return result967
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start970 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1748 = parse_term(parser)
    term968 = _t1748
    _t1749 = parse_term(parser)
    term_3969 = _t1749
    consume_literal!(parser, ")")
    _t1750 = Proto.RelTerm(rel_term_type=OneOf(:term, term968))
    _t1751 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3969))
    _t1752 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1750, _t1751])
    result971 = _t1752
    record_span!(parser, span_start970, "Primitive")
    return result971
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1753 = parse_term(parser)
    term972 = _t1753
    _t1754 = parse_term(parser)
    term_3973 = _t1754
    consume_literal!(parser, ")")
    _t1755 = Proto.RelTerm(rel_term_type=OneOf(:term, term972))
    _t1756 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3973))
    _t1757 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1755, _t1756])
    result975 = _t1757
    record_span!(parser, span_start974, "Primitive")
    return result975
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start978 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1758 = parse_term(parser)
    term976 = _t1758
    _t1759 = parse_term(parser)
    term_3977 = _t1759
    consume_literal!(parser, ")")
    _t1760 = Proto.RelTerm(rel_term_type=OneOf(:term, term976))
    _t1761 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3977))
    _t1762 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1760, _t1761])
    result979 = _t1762
    record_span!(parser, span_start978, "Primitive")
    return result979
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start982 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1763 = parse_term(parser)
    term980 = _t1763
    _t1764 = parse_term(parser)
    term_3981 = _t1764
    consume_literal!(parser, ")")
    _t1765 = Proto.RelTerm(rel_term_type=OneOf(:term, term980))
    _t1766 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3981))
    _t1767 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1765, _t1766])
    result983 = _t1767
    record_span!(parser, span_start982, "Primitive")
    return result983
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start986 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1768 = parse_term(parser)
    term984 = _t1768
    _t1769 = parse_term(parser)
    term_3985 = _t1769
    consume_literal!(parser, ")")
    _t1770 = Proto.RelTerm(rel_term_type=OneOf(:term, term984))
    _t1771 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3985))
    _t1772 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1770, _t1771])
    result987 = _t1772
    record_span!(parser, span_start986, "Primitive")
    return result987
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start991 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1773 = parse_term(parser)
    term988 = _t1773
    _t1774 = parse_term(parser)
    term_3989 = _t1774
    _t1775 = parse_term(parser)
    term_4990 = _t1775
    consume_literal!(parser, ")")
    _t1776 = Proto.RelTerm(rel_term_type=OneOf(:term, term988))
    _t1777 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3989))
    _t1778 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4990))
    _t1779 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1776, _t1777, _t1778])
    result992 = _t1779
    record_span!(parser, span_start991, "Primitive")
    return result992
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start996 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1780 = parse_term(parser)
    term993 = _t1780
    _t1781 = parse_term(parser)
    term_3994 = _t1781
    _t1782 = parse_term(parser)
    term_4995 = _t1782
    consume_literal!(parser, ")")
    _t1783 = Proto.RelTerm(rel_term_type=OneOf(:term, term993))
    _t1784 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3994))
    _t1785 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4995))
    _t1786 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1783, _t1784, _t1785])
    result997 = _t1786
    record_span!(parser, span_start996, "Primitive")
    return result997
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1001 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1787 = parse_term(parser)
    term998 = _t1787
    _t1788 = parse_term(parser)
    term_3999 = _t1788
    _t1789 = parse_term(parser)
    term_41000 = _t1789
    consume_literal!(parser, ")")
    _t1790 = Proto.RelTerm(rel_term_type=OneOf(:term, term998))
    _t1791 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3999))
    _t1792 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41000))
    _t1793 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1790, _t1791, _t1792])
    result1002 = _t1793
    record_span!(parser, span_start1001, "Primitive")
    return result1002
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1006 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1794 = parse_term(parser)
    term1003 = _t1794
    _t1795 = parse_term(parser)
    term_31004 = _t1795
    _t1796 = parse_term(parser)
    term_41005 = _t1796
    consume_literal!(parser, ")")
    _t1797 = Proto.RelTerm(rel_term_type=OneOf(:term, term1003))
    _t1798 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31004))
    _t1799 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41005))
    _t1800 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1797, _t1798, _t1799])
    result1007 = _t1800
    record_span!(parser, span_start1006, "Primitive")
    return result1007
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1011 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1801 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1802 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1803 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1804 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1805 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1806 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1807 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1808 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1809 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1810 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1811 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1812 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1813 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1814 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1815 = 1
                                                            else
                                                                _t1815 = -1
                                                            end
                                                            _t1814 = _t1815
                                                        end
                                                        _t1813 = _t1814
                                                    end
                                                    _t1812 = _t1813
                                                end
                                                _t1811 = _t1812
                                            end
                                            _t1810 = _t1811
                                        end
                                        _t1809 = _t1810
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
    prediction1008 = _t1801
    if prediction1008 == 1
        _t1817 = parse_term(parser)
        term1010 = _t1817
        _t1818 = Proto.RelTerm(rel_term_type=OneOf(:term, term1010))
        _t1816 = _t1818
    else
        if prediction1008 == 0
            _t1820 = parse_specialized_value(parser)
            specialized_value1009 = _t1820
            _t1821 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1009))
            _t1819 = _t1821
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1816 = _t1819
    end
    result1012 = _t1816
    record_span!(parser, span_start1011, "RelTerm")
    return result1012
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1014 = span_start(parser)
    consume_literal!(parser, "#")
    _t1822 = parse_raw_value(parser)
    raw_value1013 = _t1822
    result1015 = raw_value1013
    record_span!(parser, span_start1014, "Value")
    return result1015
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1021 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1823 = parse_name(parser)
    name1016 = _t1823
    xs1017 = Proto.RelTerm[]
    cond1018 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1018
        _t1824 = parse_rel_term(parser)
        item1019 = _t1824
        push!(xs1017, item1019)
        cond1018 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1020 = xs1017
    consume_literal!(parser, ")")
    _t1825 = Proto.RelAtom(name=name1016, terms=rel_terms1020)
    result1022 = _t1825
    record_span!(parser, span_start1021, "RelAtom")
    return result1022
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1025 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1826 = parse_term(parser)
    term1023 = _t1826
    _t1827 = parse_term(parser)
    term_31024 = _t1827
    consume_literal!(parser, ")")
    _t1828 = Proto.Cast(input=term1023, result=term_31024)
    result1026 = _t1828
    record_span!(parser, span_start1025, "Cast")
    return result1026
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1027 = Proto.Attribute[]
    cond1028 = match_lookahead_literal(parser, "(", 0)
    while cond1028
        _t1829 = parse_attribute(parser)
        item1029 = _t1829
        push!(xs1027, item1029)
        cond1028 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1030 = xs1027
    consume_literal!(parser, ")")
    return attributes1030
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1036 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1830 = parse_name(parser)
    name1031 = _t1830
    xs1032 = Proto.Value[]
    cond1033 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1033
        _t1831 = parse_raw_value(parser)
        item1034 = _t1831
        push!(xs1032, item1034)
        cond1033 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1035 = xs1032
    consume_literal!(parser, ")")
    _t1832 = Proto.Attribute(name=name1031, args=raw_values1035)
    result1037 = _t1832
    record_span!(parser, span_start1036, "Attribute")
    return result1037
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1044 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1038 = Proto.RelationId[]
    cond1039 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1039
        _t1833 = parse_relation_id(parser)
        item1040 = _t1833
        push!(xs1038, item1040)
        cond1039 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1041 = xs1038
    _t1834 = parse_script(parser)
    script1042 = _t1834
    if match_lookahead_literal(parser, "(", 0)
        _t1836 = parse_attrs(parser)
        _t1835 = _t1836
    else
        _t1835 = nothing
    end
    attrs1043 = _t1835
    consume_literal!(parser, ")")
    _t1837 = Proto.Algorithm(var"#global"=relation_ids1041, body=script1042, attrs=(!isnothing(attrs1043) ? attrs1043 : Proto.Attribute[]))
    result1045 = _t1837
    record_span!(parser, span_start1044, "Algorithm")
    return result1045
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1050 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1046 = Proto.Construct[]
    cond1047 = match_lookahead_literal(parser, "(", 0)
    while cond1047
        _t1838 = parse_construct(parser)
        item1048 = _t1838
        push!(xs1046, item1048)
        cond1047 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1049 = xs1046
    consume_literal!(parser, ")")
    _t1839 = Proto.Script(constructs=constructs1049)
    result1051 = _t1839
    record_span!(parser, span_start1050, "Script")
    return result1051
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1055 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1841 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1842 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1843 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1844 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1845 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1846 = 1
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
        end
        _t1840 = _t1841
    else
        _t1840 = -1
    end
    prediction1052 = _t1840
    if prediction1052 == 1
        _t1848 = parse_instruction(parser)
        instruction1054 = _t1848
        _t1849 = Proto.Construct(construct_type=OneOf(:instruction, instruction1054))
        _t1847 = _t1849
    else
        if prediction1052 == 0
            _t1851 = parse_loop(parser)
            loop1053 = _t1851
            _t1852 = Proto.Construct(construct_type=OneOf(:loop, loop1053))
            _t1850 = _t1852
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1847 = _t1850
    end
    result1056 = _t1847
    record_span!(parser, span_start1055, "Construct")
    return result1056
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1060 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1853 = parse_init(parser)
    init1057 = _t1853
    _t1854 = parse_script(parser)
    script1058 = _t1854
    if match_lookahead_literal(parser, "(", 0)
        _t1856 = parse_attrs(parser)
        _t1855 = _t1856
    else
        _t1855 = nothing
    end
    attrs1059 = _t1855
    consume_literal!(parser, ")")
    _t1857 = Proto.Loop(init=init1057, body=script1058, attrs=(!isnothing(attrs1059) ? attrs1059 : Proto.Attribute[]))
    result1061 = _t1857
    record_span!(parser, span_start1060, "Loop")
    return result1061
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1062 = Proto.Instruction[]
    cond1063 = match_lookahead_literal(parser, "(", 0)
    while cond1063
        _t1858 = parse_instruction(parser)
        item1064 = _t1858
        push!(xs1062, item1064)
        cond1063 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1065 = xs1062
    consume_literal!(parser, ")")
    return instructions1065
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1072 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1860 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1861 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1862 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1863 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1864 = 0
                        else
                            _t1864 = -1
                        end
                        _t1863 = _t1864
                    end
                    _t1862 = _t1863
                end
                _t1861 = _t1862
            end
            _t1860 = _t1861
        end
        _t1859 = _t1860
    else
        _t1859 = -1
    end
    prediction1066 = _t1859
    if prediction1066 == 4
        _t1866 = parse_monus_def(parser)
        monus_def1071 = _t1866
        _t1867 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1071))
        _t1865 = _t1867
    else
        if prediction1066 == 3
            _t1869 = parse_monoid_def(parser)
            monoid_def1070 = _t1869
            _t1870 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1070))
            _t1868 = _t1870
        else
            if prediction1066 == 2
                _t1872 = parse_break(parser)
                break1069 = _t1872
                _t1873 = Proto.Instruction(instr_type=OneOf(:var"#break", break1069))
                _t1871 = _t1873
            else
                if prediction1066 == 1
                    _t1875 = parse_upsert(parser)
                    upsert1068 = _t1875
                    _t1876 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1068))
                    _t1874 = _t1876
                else
                    if prediction1066 == 0
                        _t1878 = parse_assign(parser)
                        assign1067 = _t1878
                        _t1879 = Proto.Instruction(instr_type=OneOf(:assign, assign1067))
                        _t1877 = _t1879
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1874 = _t1877
                end
                _t1871 = _t1874
            end
            _t1868 = _t1871
        end
        _t1865 = _t1868
    end
    result1073 = _t1865
    record_span!(parser, span_start1072, "Instruction")
    return result1073
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1077 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1880 = parse_relation_id(parser)
    relation_id1074 = _t1880
    _t1881 = parse_abstraction(parser)
    abstraction1075 = _t1881
    if match_lookahead_literal(parser, "(", 0)
        _t1883 = parse_attrs(parser)
        _t1882 = _t1883
    else
        _t1882 = nothing
    end
    attrs1076 = _t1882
    consume_literal!(parser, ")")
    _t1884 = Proto.Assign(name=relation_id1074, body=abstraction1075, attrs=(!isnothing(attrs1076) ? attrs1076 : Proto.Attribute[]))
    result1078 = _t1884
    record_span!(parser, span_start1077, "Assign")
    return result1078
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1082 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1885 = parse_relation_id(parser)
    relation_id1079 = _t1885
    _t1886 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1080 = _t1886
    if match_lookahead_literal(parser, "(", 0)
        _t1888 = parse_attrs(parser)
        _t1887 = _t1888
    else
        _t1887 = nothing
    end
    attrs1081 = _t1887
    consume_literal!(parser, ")")
    _t1889 = Proto.Upsert(name=relation_id1079, body=abstraction_with_arity1080[1], attrs=(!isnothing(attrs1081) ? attrs1081 : Proto.Attribute[]), value_arity=abstraction_with_arity1080[2])
    result1083 = _t1889
    record_span!(parser, span_start1082, "Upsert")
    return result1083
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1890 = parse_bindings(parser)
    bindings1084 = _t1890
    _t1891 = parse_formula(parser)
    formula1085 = _t1891
    consume_literal!(parser, ")")
    _t1892 = Proto.Abstraction(vars=vcat(bindings1084[1], !isnothing(bindings1084[2]) ? bindings1084[2] : []), value=formula1085)
    return (_t1892, length(bindings1084[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1089 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1893 = parse_relation_id(parser)
    relation_id1086 = _t1893
    _t1894 = parse_abstraction(parser)
    abstraction1087 = _t1894
    if match_lookahead_literal(parser, "(", 0)
        _t1896 = parse_attrs(parser)
        _t1895 = _t1896
    else
        _t1895 = nothing
    end
    attrs1088 = _t1895
    consume_literal!(parser, ")")
    _t1897 = Proto.Break(name=relation_id1086, body=abstraction1087, attrs=(!isnothing(attrs1088) ? attrs1088 : Proto.Attribute[]))
    result1090 = _t1897
    record_span!(parser, span_start1089, "Break")
    return result1090
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1095 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1898 = parse_monoid(parser)
    monoid1091 = _t1898
    _t1899 = parse_relation_id(parser)
    relation_id1092 = _t1899
    _t1900 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1093 = _t1900
    if match_lookahead_literal(parser, "(", 0)
        _t1902 = parse_attrs(parser)
        _t1901 = _t1902
    else
        _t1901 = nothing
    end
    attrs1094 = _t1901
    consume_literal!(parser, ")")
    _t1903 = Proto.MonoidDef(monoid=monoid1091, name=relation_id1092, body=abstraction_with_arity1093[1], attrs=(!isnothing(attrs1094) ? attrs1094 : Proto.Attribute[]), value_arity=abstraction_with_arity1093[2])
    result1096 = _t1903
    record_span!(parser, span_start1095, "MonoidDef")
    return result1096
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1102 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1905 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1906 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1907 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1908 = 2
                    else
                        _t1908 = -1
                    end
                    _t1907 = _t1908
                end
                _t1906 = _t1907
            end
            _t1905 = _t1906
        end
        _t1904 = _t1905
    else
        _t1904 = -1
    end
    prediction1097 = _t1904
    if prediction1097 == 3
        _t1910 = parse_sum_monoid(parser)
        sum_monoid1101 = _t1910
        _t1911 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1101))
        _t1909 = _t1911
    else
        if prediction1097 == 2
            _t1913 = parse_max_monoid(parser)
            max_monoid1100 = _t1913
            _t1914 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1100))
            _t1912 = _t1914
        else
            if prediction1097 == 1
                _t1916 = parse_min_monoid(parser)
                min_monoid1099 = _t1916
                _t1917 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1099))
                _t1915 = _t1917
            else
                if prediction1097 == 0
                    _t1919 = parse_or_monoid(parser)
                    or_monoid1098 = _t1919
                    _t1920 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1098))
                    _t1918 = _t1920
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1915 = _t1918
            end
            _t1912 = _t1915
        end
        _t1909 = _t1912
    end
    result1103 = _t1909
    record_span!(parser, span_start1102, "Monoid")
    return result1103
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1104 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1921 = Proto.OrMonoid()
    result1105 = _t1921
    record_span!(parser, span_start1104, "OrMonoid")
    return result1105
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1107 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1922 = parse_type(parser)
    type1106 = _t1922
    consume_literal!(parser, ")")
    _t1923 = Proto.MinMonoid(var"#type"=type1106)
    result1108 = _t1923
    record_span!(parser, span_start1107, "MinMonoid")
    return result1108
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1110 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1924 = parse_type(parser)
    type1109 = _t1924
    consume_literal!(parser, ")")
    _t1925 = Proto.MaxMonoid(var"#type"=type1109)
    result1111 = _t1925
    record_span!(parser, span_start1110, "MaxMonoid")
    return result1111
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1113 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1926 = parse_type(parser)
    type1112 = _t1926
    consume_literal!(parser, ")")
    _t1927 = Proto.SumMonoid(var"#type"=type1112)
    result1114 = _t1927
    record_span!(parser, span_start1113, "SumMonoid")
    return result1114
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1119 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1928 = parse_monoid(parser)
    monoid1115 = _t1928
    _t1929 = parse_relation_id(parser)
    relation_id1116 = _t1929
    _t1930 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1117 = _t1930
    if match_lookahead_literal(parser, "(", 0)
        _t1932 = parse_attrs(parser)
        _t1931 = _t1932
    else
        _t1931 = nothing
    end
    attrs1118 = _t1931
    consume_literal!(parser, ")")
    _t1933 = Proto.MonusDef(monoid=monoid1115, name=relation_id1116, body=abstraction_with_arity1117[1], attrs=(!isnothing(attrs1118) ? attrs1118 : Proto.Attribute[]), value_arity=abstraction_with_arity1117[2])
    result1120 = _t1933
    record_span!(parser, span_start1119, "MonusDef")
    return result1120
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1125 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1934 = parse_relation_id(parser)
    relation_id1121 = _t1934
    _t1935 = parse_abstraction(parser)
    abstraction1122 = _t1935
    _t1936 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1123 = _t1936
    _t1937 = parse_functional_dependency_values(parser)
    functional_dependency_values1124 = _t1937
    consume_literal!(parser, ")")
    _t1938 = Proto.FunctionalDependency(guard=abstraction1122, keys=functional_dependency_keys1123, values=functional_dependency_values1124)
    _t1939 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1938), name=relation_id1121)
    result1126 = _t1939
    record_span!(parser, span_start1125, "Constraint")
    return result1126
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1127 = Proto.Var[]
    cond1128 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1128
        _t1940 = parse_var(parser)
        item1129 = _t1940
        push!(xs1127, item1129)
        cond1128 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1130 = xs1127
    consume_literal!(parser, ")")
    return vars1130
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1131 = Proto.Var[]
    cond1132 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1132
        _t1941 = parse_var(parser)
        item1133 = _t1941
        push!(xs1131, item1133)
        cond1132 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1134 = xs1131
    consume_literal!(parser, ")")
    return vars1134
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1140 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1943 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1944 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1945 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1946 = 1
                    else
                        _t1946 = -1
                    end
                    _t1945 = _t1946
                end
                _t1944 = _t1945
            end
            _t1943 = _t1944
        end
        _t1942 = _t1943
    else
        _t1942 = -1
    end
    prediction1135 = _t1942
    if prediction1135 == 3
        _t1948 = parse_iceberg_data(parser)
        iceberg_data1139 = _t1948
        _t1949 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1139))
        _t1947 = _t1949
    else
        if prediction1135 == 2
            _t1951 = parse_csv_data(parser)
            csv_data1138 = _t1951
            _t1952 = Proto.Data(data_type=OneOf(:csv_data, csv_data1138))
            _t1950 = _t1952
        else
            if prediction1135 == 1
                _t1954 = parse_betree_relation(parser)
                betree_relation1137 = _t1954
                _t1955 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1137))
                _t1953 = _t1955
            else
                if prediction1135 == 0
                    _t1957 = parse_edb(parser)
                    edb1136 = _t1957
                    _t1958 = Proto.Data(data_type=OneOf(:edb, edb1136))
                    _t1956 = _t1958
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1953 = _t1956
            end
            _t1950 = _t1953
        end
        _t1947 = _t1950
    end
    result1141 = _t1947
    record_span!(parser, span_start1140, "Data")
    return result1141
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1145 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1959 = parse_relation_id(parser)
    relation_id1142 = _t1959
    _t1960 = parse_edb_path(parser)
    edb_path1143 = _t1960
    _t1961 = parse_edb_types(parser)
    edb_types1144 = _t1961
    consume_literal!(parser, ")")
    _t1962 = Proto.EDB(target_id=relation_id1142, path=edb_path1143, types=edb_types1144)
    result1146 = _t1962
    record_span!(parser, span_start1145, "EDB")
    return result1146
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1147 = String[]
    cond1148 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1148
        item1149 = consume_terminal!(parser, "STRING")
        push!(xs1147, item1149)
        cond1148 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1150 = xs1147
    consume_literal!(parser, "]")
    return strings1150
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1151 = Proto.var"#Type"[]
    cond1152 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1152
        _t1963 = parse_type(parser)
        item1153 = _t1963
        push!(xs1151, item1153)
        cond1152 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1154 = xs1151
    consume_literal!(parser, "]")
    return types1154
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1157 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1964 = parse_relation_id(parser)
    relation_id1155 = _t1964
    _t1965 = parse_betree_info(parser)
    betree_info1156 = _t1965
    consume_literal!(parser, ")")
    _t1966 = Proto.BeTreeRelation(name=relation_id1155, relation_info=betree_info1156)
    result1158 = _t1966
    record_span!(parser, span_start1157, "BeTreeRelation")
    return result1158
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1162 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1967 = parse_betree_info_key_types(parser)
    betree_info_key_types1159 = _t1967
    _t1968 = parse_betree_info_value_types(parser)
    betree_info_value_types1160 = _t1968
    _t1969 = parse_config_dict(parser)
    config_dict1161 = _t1969
    consume_literal!(parser, ")")
    _t1970 = construct_betree_info(parser, betree_info_key_types1159, betree_info_value_types1160, config_dict1161)
    result1163 = _t1970
    record_span!(parser, span_start1162, "BeTreeInfo")
    return result1163
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1164 = Proto.var"#Type"[]
    cond1165 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1165
        _t1971 = parse_type(parser)
        item1166 = _t1971
        push!(xs1164, item1166)
        cond1165 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1167 = xs1164
    consume_literal!(parser, ")")
    return types1167
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1168 = Proto.var"#Type"[]
    cond1169 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1169
        _t1972 = parse_type(parser)
        item1170 = _t1972
        push!(xs1168, item1170)
        cond1169 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1171 = xs1168
    consume_literal!(parser, ")")
    return types1171
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1177 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1973 = parse_csvlocator(parser)
    csvlocator1172 = _t1973
    _t1974 = parse_csv_config(parser)
    csv_config1173 = _t1974
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t1976 = parse_gnf_columns(parser)
        _t1975 = _t1976
    else
        _t1975 = nothing
    end
    gnf_columns1174 = _t1975
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "table", 1))
        _t1978 = parse_csv_table(parser)
        _t1977 = _t1978
    else
        _t1977 = nothing
    end
    csv_table1175 = _t1977
    _t1979 = parse_csv_asof(parser)
    csv_asof1176 = _t1979
    consume_literal!(parser, ")")
    _t1980 = construct_csv_data(parser, csvlocator1172, csv_config1173, gnf_columns1174, csv_table1175, csv_asof1176)
    result1178 = _t1980
    record_span!(parser, span_start1177, "CSVData")
    return result1178
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1181 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1982 = parse_csv_locator_paths(parser)
        _t1981 = _t1982
    else
        _t1981 = nothing
    end
    csv_locator_paths1179 = _t1981
    if match_lookahead_literal(parser, "(", 0)
        _t1984 = parse_csv_locator_inline_data(parser)
        _t1983 = _t1984
    else
        _t1983 = nothing
    end
    csv_locator_inline_data1180 = _t1983
    consume_literal!(parser, ")")
    _t1985 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1179) ? csv_locator_paths1179 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1180) ? csv_locator_inline_data1180 : "")))
    result1182 = _t1985
    record_span!(parser, span_start1181, "CSVLocator")
    return result1182
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1183 = String[]
    cond1184 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1184
        item1185 = consume_terminal!(parser, "STRING")
        push!(xs1183, item1185)
        cond1184 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1186 = xs1183
    consume_literal!(parser, ")")
    return strings1186
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1187 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1187
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1189 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1986 = parse_config_dict(parser)
    config_dict1188 = _t1986
    consume_literal!(parser, ")")
    _t1987 = construct_csv_config(parser, config_dict1188)
    result1190 = _t1987
    record_span!(parser, span_start1189, "CSVConfig")
    return result1190
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1191 = Proto.GNFColumn[]
    cond1192 = match_lookahead_literal(parser, "(", 0)
    while cond1192
        _t1988 = parse_gnf_column(parser)
        item1193 = _t1988
        push!(xs1191, item1193)
        cond1192 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1194 = xs1191
    consume_literal!(parser, ")")
    return gnf_columns1194
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1201 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1989 = parse_gnf_column_path(parser)
    gnf_column_path1195 = _t1989
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1991 = parse_relation_id(parser)
        _t1990 = _t1991
    else
        _t1990 = nothing
    end
    relation_id1196 = _t1990
    consume_literal!(parser, "[")
    xs1197 = Proto.var"#Type"[]
    cond1198 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1198
        _t1992 = parse_type(parser)
        item1199 = _t1992
        push!(xs1197, item1199)
        cond1198 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1200 = xs1197
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1993 = Proto.GNFColumn(column_path=gnf_column_path1195, target_id=relation_id1196, types=types1200)
    result1202 = _t1993
    record_span!(parser, span_start1201, "GNFColumn")
    return result1202
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1994 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1995 = 0
        else
            _t1995 = -1
        end
        _t1994 = _t1995
    end
    prediction1203 = _t1994
    if prediction1203 == 1
        consume_literal!(parser, "[")
        xs1205 = String[]
        cond1206 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1206
            item1207 = consume_terminal!(parser, "STRING")
            push!(xs1205, item1207)
            cond1206 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1208 = xs1205
        consume_literal!(parser, "]")
        _t1996 = strings1208
    else
        if prediction1203 == 0
            string1204 = consume_terminal!(parser, "STRING")
            _t1997 = String[string1204]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1996 = _t1997
    end
    return _t1996
end

function parse_csv_table(parser::ParserState)::Proto.CSVTarget
    span_start1218 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table")
    _t1998 = parse_relation_id(parser)
    relation_id1209 = _t1998
    consume_literal!(parser, "[")
    xs1210 = String[]
    cond1211 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1211
        item1212 = consume_terminal!(parser, "STRING")
        push!(xs1210, item1212)
        cond1211 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1213 = xs1210
    consume_literal!(parser, "]")
    consume_literal!(parser, "[")
    xs1214 = Proto.var"#Type"[]
    cond1215 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1215
        _t1999 = parse_type(parser)
        item1216 = _t1999
        push!(xs1214, item1216)
        cond1215 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1217 = xs1214
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2000 = Proto.CSVTarget(target_id=relation_id1209, column_names=strings1213, types=types1217)
    result1219 = _t2000
    record_span!(parser, span_start1218, "CSVTarget")
    return result1219
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1220 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1220
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1227 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t2001 = parse_iceberg_locator(parser)
    iceberg_locator1221 = _t2001
    _t2002 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1222 = _t2002
    _t2003 = parse_gnf_columns(parser)
    gnf_columns1223 = _t2003
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2005 = parse_iceberg_from_snapshot(parser)
        _t2004 = _t2005
    else
        _t2004 = nothing
    end
    iceberg_from_snapshot1224 = _t2004
    if match_lookahead_literal(parser, "(", 0)
        _t2007 = parse_iceberg_to_snapshot(parser)
        _t2006 = _t2007
    else
        _t2006 = nothing
    end
    iceberg_to_snapshot1225 = _t2006
    _t2008 = parse_boolean_value(parser)
    boolean_value1226 = _t2008
    consume_literal!(parser, ")")
    _t2009 = construct_iceberg_data(parser, iceberg_locator1221, iceberg_catalog_config1222, gnf_columns1223, iceberg_from_snapshot1224, iceberg_to_snapshot1225, boolean_value1226)
    result1228 = _t2009
    record_span!(parser, span_start1227, "IcebergData")
    return result1228
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1232 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2010 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1229 = _t2010
    _t2011 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1230 = _t2011
    _t2012 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1231 = _t2012
    consume_literal!(parser, ")")
    _t2013 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1229, namespace=iceberg_locator_namespace1230, warehouse=iceberg_locator_warehouse1231)
    result1233 = _t2013
    record_span!(parser, span_start1232, "IcebergLocator")
    return result1233
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1234 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1234
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1235 = String[]
    cond1236 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1236
        item1237 = consume_terminal!(parser, "STRING")
        push!(xs1235, item1237)
        cond1236 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1238 = xs1235
    consume_literal!(parser, ")")
    return strings1238
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1239 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1239
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1244 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2014 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1240 = _t2014
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2016 = parse_iceberg_catalog_config_scope(parser)
        _t2015 = _t2016
    else
        _t2015 = nothing
    end
    iceberg_catalog_config_scope1241 = _t2015
    _t2017 = parse_iceberg_properties(parser)
    iceberg_properties1242 = _t2017
    _t2018 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1243 = _t2018
    consume_literal!(parser, ")")
    _t2019 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1240, iceberg_catalog_config_scope1241, iceberg_properties1242, iceberg_auth_properties1243)
    result1245 = _t2019
    record_span!(parser, span_start1244, "IcebergCatalogConfig")
    return result1245
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1246 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1246
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1247 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1247
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1248 = Tuple{String, String}[]
    cond1249 = match_lookahead_literal(parser, "(", 0)
    while cond1249
        _t2020 = parse_iceberg_property_entry(parser)
        item1250 = _t2020
        push!(xs1248, item1250)
        cond1249 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1251 = xs1248
    consume_literal!(parser, ")")
    return iceberg_property_entrys1251
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1252 = consume_terminal!(parser, "STRING")
    string_31253 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1252, string_31253,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1254 = Tuple{String, String}[]
    cond1255 = match_lookahead_literal(parser, "(", 0)
    while cond1255
        _t2021 = parse_iceberg_masked_property_entry(parser)
        item1256 = _t2021
        push!(xs1254, item1256)
        cond1255 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1257 = xs1254
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1257
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1258 = consume_terminal!(parser, "STRING")
    string_31259 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1258, string_31259,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1260 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1260
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1261 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1261
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1263 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2022 = parse_fragment_id(parser)
    fragment_id1262 = _t2022
    consume_literal!(parser, ")")
    _t2023 = Proto.Undefine(fragment_id=fragment_id1262)
    result1264 = _t2023
    record_span!(parser, span_start1263, "Undefine")
    return result1264
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1269 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1265 = Proto.RelationId[]
    cond1266 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1266
        _t2024 = parse_relation_id(parser)
        item1267 = _t2024
        push!(xs1265, item1267)
        cond1266 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1268 = xs1265
    consume_literal!(parser, ")")
    _t2025 = Proto.Context(relations=relation_ids1268)
    result1270 = _t2025
    record_span!(parser, span_start1269, "Context")
    return result1270
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1276 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2026 = parse_edb_path(parser)
    edb_path1271 = _t2026
    xs1272 = Proto.SnapshotMapping[]
    cond1273 = match_lookahead_literal(parser, "[", 0)
    while cond1273
        _t2027 = parse_snapshot_mapping(parser)
        item1274 = _t2027
        push!(xs1272, item1274)
        cond1273 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1275 = xs1272
    consume_literal!(parser, ")")
    _t2028 = Proto.Snapshot(mappings=snapshot_mappings1275, prefix=edb_path1271)
    result1277 = _t2028
    record_span!(parser, span_start1276, "Snapshot")
    return result1277
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1280 = span_start(parser)
    _t2029 = parse_edb_path(parser)
    edb_path1278 = _t2029
    _t2030 = parse_relation_id(parser)
    relation_id1279 = _t2030
    _t2031 = Proto.SnapshotMapping(destination_path=edb_path1278, source_relation=relation_id1279)
    result1281 = _t2031
    record_span!(parser, span_start1280, "SnapshotMapping")
    return result1281
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1282 = Proto.Read[]
    cond1283 = match_lookahead_literal(parser, "(", 0)
    while cond1283
        _t2032 = parse_read(parser)
        item1284 = _t2032
        push!(xs1282, item1284)
        cond1283 = match_lookahead_literal(parser, "(", 0)
    end
    reads1285 = xs1282
    consume_literal!(parser, ")")
    return reads1285
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1292 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2034 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2035 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2036 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2037 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2038 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2039 = 3
                            else
                                _t2039 = -1
                            end
                            _t2038 = _t2039
                        end
                        _t2037 = _t2038
                    end
                    _t2036 = _t2037
                end
                _t2035 = _t2036
            end
            _t2034 = _t2035
        end
        _t2033 = _t2034
    else
        _t2033 = -1
    end
    prediction1286 = _t2033
    if prediction1286 == 4
        _t2041 = parse_export(parser)
        export1291 = _t2041
        _t2042 = Proto.Read(read_type=OneOf(:var"#export", export1291))
        _t2040 = _t2042
    else
        if prediction1286 == 3
            _t2044 = parse_abort(parser)
            abort1290 = _t2044
            _t2045 = Proto.Read(read_type=OneOf(:abort, abort1290))
            _t2043 = _t2045
        else
            if prediction1286 == 2
                _t2047 = parse_what_if(parser)
                what_if1289 = _t2047
                _t2048 = Proto.Read(read_type=OneOf(:what_if, what_if1289))
                _t2046 = _t2048
            else
                if prediction1286 == 1
                    _t2050 = parse_output(parser)
                    output1288 = _t2050
                    _t2051 = Proto.Read(read_type=OneOf(:output, output1288))
                    _t2049 = _t2051
                else
                    if prediction1286 == 0
                        _t2053 = parse_demand(parser)
                        demand1287 = _t2053
                        _t2054 = Proto.Read(read_type=OneOf(:demand, demand1287))
                        _t2052 = _t2054
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2049 = _t2052
                end
                _t2046 = _t2049
            end
            _t2043 = _t2046
        end
        _t2040 = _t2043
    end
    result1293 = _t2040
    record_span!(parser, span_start1292, "Read")
    return result1293
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1295 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2055 = parse_relation_id(parser)
    relation_id1294 = _t2055
    consume_literal!(parser, ")")
    _t2056 = Proto.Demand(relation_id=relation_id1294)
    result1296 = _t2056
    record_span!(parser, span_start1295, "Demand")
    return result1296
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1299 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2057 = parse_name(parser)
    name1297 = _t2057
    _t2058 = parse_relation_id(parser)
    relation_id1298 = _t2058
    consume_literal!(parser, ")")
    _t2059 = Proto.Output(name=name1297, relation_id=relation_id1298)
    result1300 = _t2059
    record_span!(parser, span_start1299, "Output")
    return result1300
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1303 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2060 = parse_name(parser)
    name1301 = _t2060
    _t2061 = parse_epoch(parser)
    epoch1302 = _t2061
    consume_literal!(parser, ")")
    _t2062 = Proto.WhatIf(branch=name1301, epoch=epoch1302)
    result1304 = _t2062
    record_span!(parser, span_start1303, "WhatIf")
    return result1304
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1307 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2064 = parse_name(parser)
        _t2063 = _t2064
    else
        _t2063 = nothing
    end
    name1305 = _t2063
    _t2065 = parse_relation_id(parser)
    relation_id1306 = _t2065
    consume_literal!(parser, ")")
    _t2066 = Proto.Abort(name=(!isnothing(name1305) ? name1305 : "abort"), relation_id=relation_id1306)
    result1308 = _t2066
    record_span!(parser, span_start1307, "Abort")
    return result1308
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1312 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2068 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2069 = 0
            else
                _t2069 = -1
            end
            _t2068 = _t2069
        end
        _t2067 = _t2068
    else
        _t2067 = -1
    end
    prediction1309 = _t2067
    if prediction1309 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2071 = parse_export_iceberg_config(parser)
        export_iceberg_config1311 = _t2071
        consume_literal!(parser, ")")
        _t2072 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1311))
        _t2070 = _t2072
    else
        if prediction1309 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2074 = parse_export_csv_config(parser)
            export_csv_config1310 = _t2074
            consume_literal!(parser, ")")
            _t2075 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1310))
            _t2073 = _t2075
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2070 = _t2073
    end
    result1313 = _t2070
    record_span!(parser, span_start1312, "Export")
    return result1313
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1321 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2077 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2078 = 1
            else
                _t2078 = -1
            end
            _t2077 = _t2078
        end
        _t2076 = _t2077
    else
        _t2076 = -1
    end
    prediction1314 = _t2076
    if prediction1314 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2080 = parse_export_csv_path(parser)
        export_csv_path1318 = _t2080
        _t2081 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1319 = _t2081
        _t2082 = parse_config_dict(parser)
        config_dict1320 = _t2082
        consume_literal!(parser, ")")
        _t2083 = construct_export_csv_config(parser, export_csv_path1318, export_csv_columns_list1319, config_dict1320)
        _t2079 = _t2083
    else
        if prediction1314 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2085 = parse_export_csv_path(parser)
            export_csv_path1315 = _t2085
            _t2086 = parse_export_csv_source(parser)
            export_csv_source1316 = _t2086
            _t2087 = parse_csv_config(parser)
            csv_config1317 = _t2087
            consume_literal!(parser, ")")
            _t2088 = construct_export_csv_config_with_source(parser, export_csv_path1315, export_csv_source1316, csv_config1317)
            _t2084 = _t2088
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2079 = _t2084
    end
    result1322 = _t2079
    record_span!(parser, span_start1321, "ExportCSVConfig")
    return result1322
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1323 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1323
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1330 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2090 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2091 = 0
            else
                _t2091 = -1
            end
            _t2090 = _t2091
        end
        _t2089 = _t2090
    else
        _t2089 = -1
    end
    prediction1324 = _t2089
    if prediction1324 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2093 = parse_relation_id(parser)
        relation_id1329 = _t2093
        consume_literal!(parser, ")")
        _t2094 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1329))
        _t2092 = _t2094
    else
        if prediction1324 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1325 = Proto.ExportCSVColumn[]
            cond1326 = match_lookahead_literal(parser, "(", 0)
            while cond1326
                _t2096 = parse_export_csv_column(parser)
                item1327 = _t2096
                push!(xs1325, item1327)
                cond1326 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1328 = xs1325
            consume_literal!(parser, ")")
            _t2097 = Proto.ExportCSVColumns(columns=export_csv_columns1328)
            _t2098 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2097))
            _t2095 = _t2098
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2092 = _t2095
    end
    result1331 = _t2092
    record_span!(parser, span_start1330, "ExportCSVSource")
    return result1331
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1334 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1332 = consume_terminal!(parser, "STRING")
    _t2099 = parse_relation_id(parser)
    relation_id1333 = _t2099
    consume_literal!(parser, ")")
    _t2100 = Proto.ExportCSVColumn(column_name=string1332, column_data=relation_id1333)
    result1335 = _t2100
    record_span!(parser, span_start1334, "ExportCSVColumn")
    return result1335
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1336 = Proto.ExportCSVColumn[]
    cond1337 = match_lookahead_literal(parser, "(", 0)
    while cond1337
        _t2101 = parse_export_csv_column(parser)
        item1338 = _t2101
        push!(xs1336, item1338)
        cond1337 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1339 = xs1336
    consume_literal!(parser, ")")
    return export_csv_columns1339
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1345 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2102 = parse_iceberg_locator(parser)
    iceberg_locator1340 = _t2102
    _t2103 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1341 = _t2103
    _t2104 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1342 = _t2104
    _t2105 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1343 = _t2105
    if match_lookahead_literal(parser, "{", 0)
        _t2107 = parse_config_dict(parser)
        _t2106 = _t2107
    else
        _t2106 = nothing
    end
    config_dict1344 = _t2106
    consume_literal!(parser, ")")
    _t2108 = construct_export_iceberg_config_full(parser, iceberg_locator1340, iceberg_catalog_config1341, export_iceberg_table_def1342, iceberg_table_properties1343, config_dict1344)
    result1346 = _t2108
    record_span!(parser, span_start1345, "ExportIcebergConfig")
    return result1346
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1348 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2109 = parse_relation_id(parser)
    relation_id1347 = _t2109
    consume_literal!(parser, ")")
    result1349 = relation_id1347
    record_span!(parser, span_start1348, "RelationId")
    return result1349
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1350 = Tuple{String, String}[]
    cond1351 = match_lookahead_literal(parser, "(", 0)
    while cond1351
        _t2110 = parse_iceberg_property_entry(parser)
        item1352 = _t2110
        push!(xs1350, item1352)
        cond1351 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1353 = xs1350
    consume_literal!(parser, ")")
    return iceberg_property_entrys1353
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
