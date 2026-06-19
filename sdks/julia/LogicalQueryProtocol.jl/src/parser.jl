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
        _t2116 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2117 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2118 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2119 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2120 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2121 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2122 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2123 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2124 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2125 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2125
    _t2126 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2126
    _t2127 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2127
    _t2128 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2128
    _t2129 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2129
    _t2130 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2130
    _t2131 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2131
    _t2132 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2132
    _t2133 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2133
    _t2134 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2134
    _t2135 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2135
    _t2136 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2136
    _t2137 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2137
    _t2138 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2138
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2139 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2140 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2141 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2142 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2143 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2144 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2145 = Proto.StorageIntegration(provider=_t2140, azure_sas_token=_t2141, s3_region=_t2142, s3_access_key_id=_t2143, s3_secret_access_key=_t2144)
    return _t2145
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2146 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2146
    _t2147 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2147
    _t2148 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2148
    _t2149 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2149
    _t2150 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2150
    _t2151 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2151
    _t2152 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2152
    _t2153 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2153
    _t2154 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2154
    _t2155 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2155
    _t2156 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2156
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2157 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2157
    _t2158 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2158
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
    _t2159 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2159
    _t2160 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2160
    _t2161 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2161
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2162 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2162
    _t2163 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2163
    _t2164 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2164
    _t2165 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2165
    _t2166 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2166
    _t2167 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2167
    _t2168 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2168
    _t2169 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2169
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2170 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2170
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2171 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2171
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2172 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2172
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2173 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2173
    _t2174 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2174
    _t2175 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2175
    table_props = Dict(table_property_pairs)
    _t2176 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2176
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start682 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1353 = parse_configure(parser)
        _t1352 = _t1353
    else
        _t1352 = nothing
    end
    configure676 = _t1352
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1355 = parse_sync(parser)
        _t1354 = _t1355
    else
        _t1354 = nothing
    end
    sync677 = _t1354
    xs678 = Proto.Epoch[]
    cond679 = match_lookahead_literal(parser, "(", 0)
    while cond679
        _t1356 = parse_epoch(parser)
        item680 = _t1356
        push!(xs678, item680)
        cond679 = match_lookahead_literal(parser, "(", 0)
    end
    epochs681 = xs678
    consume_literal!(parser, ")")
    _t1357 = default_configure(parser)
    _t1358 = Proto.Transaction(epochs=epochs681, configure=(!isnothing(configure676) ? configure676 : _t1357), sync=sync677)
    result683 = _t1358
    record_span!(parser, span_start682, "Transaction")
    return result683
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start685 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1359 = parse_config_dict(parser)
    config_dict684 = _t1359
    consume_literal!(parser, ")")
    _t1360 = construct_configure(parser, config_dict684)
    result686 = _t1360
    record_span!(parser, span_start685, "Configure")
    return result686
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs687 = Tuple{String, Proto.Value}[]
    cond688 = match_lookahead_literal(parser, ":", 0)
    while cond688
        _t1361 = parse_config_key_value(parser)
        item689 = _t1361
        push!(xs687, item689)
        cond688 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values690 = xs687
    consume_literal!(parser, "}")
    return config_key_values690
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol691 = consume_terminal!(parser, "SYMBOL")
    _t1362 = parse_raw_value(parser)
    raw_value692 = _t1362
    return (symbol691, raw_value692,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start706 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1363 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1364 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1365 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1367 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1368 = 0
                        else
                            _t1368 = -1
                        end
                        _t1367 = _t1368
                    end
                    _t1366 = _t1367
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1369 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1370 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1371 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1372 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1373 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1374 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1375 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1376 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1377 = 10
                                                    else
                                                        _t1377 = -1
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
                            _t1370 = _t1371
                        end
                        _t1369 = _t1370
                    end
                    _t1366 = _t1369
                end
                _t1365 = _t1366
            end
            _t1364 = _t1365
        end
        _t1363 = _t1364
    end
    prediction693 = _t1363
    if prediction693 == 12
        _t1379 = parse_boolean_value(parser)
        boolean_value705 = _t1379
        _t1380 = Proto.Value(value=OneOf(:boolean_value, boolean_value705))
        _t1378 = _t1380
    else
        if prediction693 == 11
            consume_literal!(parser, "missing")
            _t1382 = Proto.MissingValue()
            _t1383 = Proto.Value(value=OneOf(:missing_value, _t1382))
            _t1381 = _t1383
        else
            if prediction693 == 10
                decimal704 = consume_terminal!(parser, "DECIMAL")
                _t1385 = Proto.Value(value=OneOf(:decimal_value, decimal704))
                _t1384 = _t1385
            else
                if prediction693 == 9
                    int128703 = consume_terminal!(parser, "INT128")
                    _t1387 = Proto.Value(value=OneOf(:int128_value, int128703))
                    _t1386 = _t1387
                else
                    if prediction693 == 8
                        uint128702 = consume_terminal!(parser, "UINT128")
                        _t1389 = Proto.Value(value=OneOf(:uint128_value, uint128702))
                        _t1388 = _t1389
                    else
                        if prediction693 == 7
                            uint32701 = consume_terminal!(parser, "UINT32")
                            _t1391 = Proto.Value(value=OneOf(:uint32_value, uint32701))
                            _t1390 = _t1391
                        else
                            if prediction693 == 6
                                float700 = consume_terminal!(parser, "FLOAT")
                                _t1393 = Proto.Value(value=OneOf(:float_value, float700))
                                _t1392 = _t1393
                            else
                                if prediction693 == 5
                                    float32699 = consume_terminal!(parser, "FLOAT32")
                                    _t1395 = Proto.Value(value=OneOf(:float32_value, float32699))
                                    _t1394 = _t1395
                                else
                                    if prediction693 == 4
                                        int698 = consume_terminal!(parser, "INT")
                                        _t1397 = Proto.Value(value=OneOf(:int_value, int698))
                                        _t1396 = _t1397
                                    else
                                        if prediction693 == 3
                                            int32697 = consume_terminal!(parser, "INT32")
                                            _t1399 = Proto.Value(value=OneOf(:int32_value, int32697))
                                            _t1398 = _t1399
                                        else
                                            if prediction693 == 2
                                                string696 = consume_terminal!(parser, "STRING")
                                                _t1401 = Proto.Value(value=OneOf(:string_value, string696))
                                                _t1400 = _t1401
                                            else
                                                if prediction693 == 1
                                                    _t1403 = parse_raw_datetime(parser)
                                                    raw_datetime695 = _t1403
                                                    _t1404 = Proto.Value(value=OneOf(:datetime_value, raw_datetime695))
                                                    _t1402 = _t1404
                                                else
                                                    if prediction693 == 0
                                                        _t1406 = parse_raw_date(parser)
                                                        raw_date694 = _t1406
                                                        _t1407 = Proto.Value(value=OneOf(:date_value, raw_date694))
                                                        _t1405 = _t1407
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1402 = _t1405
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
                _t1384 = _t1386
            end
            _t1381 = _t1384
        end
        _t1378 = _t1381
    end
    result707 = _t1378
    record_span!(parser, span_start706, "Value")
    return result707
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start711 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int708 = consume_terminal!(parser, "INT")
    int_3709 = consume_terminal!(parser, "INT")
    int_4710 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1408 = Proto.DateValue(year=Int32(int708), month=Int32(int_3709), day=Int32(int_4710))
    result712 = _t1408
    record_span!(parser, span_start711, "DateValue")
    return result712
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start720 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int713 = consume_terminal!(parser, "INT")
    int_3714 = consume_terminal!(parser, "INT")
    int_4715 = consume_terminal!(parser, "INT")
    int_5716 = consume_terminal!(parser, "INT")
    int_6717 = consume_terminal!(parser, "INT")
    int_7718 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1409 = consume_terminal!(parser, "INT")
    else
        _t1409 = nothing
    end
    int_8719 = _t1409
    consume_literal!(parser, ")")
    _t1410 = Proto.DateTimeValue(year=Int32(int713), month=Int32(int_3714), day=Int32(int_4715), hour=Int32(int_5716), minute=Int32(int_6717), second=Int32(int_7718), microsecond=Int32((!isnothing(int_8719) ? int_8719 : 0)))
    result721 = _t1410
    record_span!(parser, span_start720, "DateTimeValue")
    return result721
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1411 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1412 = 1
        else
            _t1412 = -1
        end
        _t1411 = _t1412
    end
    prediction722 = _t1411
    if prediction722 == 1
        consume_literal!(parser, "false")
        _t1413 = false
    else
        if prediction722 == 0
            consume_literal!(parser, "true")
            _t1414 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1413 = _t1414
    end
    return _t1413
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start727 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs723 = Proto.FragmentId[]
    cond724 = match_lookahead_literal(parser, ":", 0)
    while cond724
        _t1415 = parse_fragment_id(parser)
        item725 = _t1415
        push!(xs723, item725)
        cond724 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids726 = xs723
    consume_literal!(parser, ")")
    _t1416 = Proto.Sync(fragments=fragment_ids726)
    result728 = _t1416
    record_span!(parser, span_start727, "Sync")
    return result728
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start730 = span_start(parser)
    consume_literal!(parser, ":")
    symbol729 = consume_terminal!(parser, "SYMBOL")
    result731 = Proto.FragmentId(Vector{UInt8}(symbol729))
    record_span!(parser, span_start730, "FragmentId")
    return result731
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start734 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1418 = parse_epoch_writes(parser)
        _t1417 = _t1418
    else
        _t1417 = nothing
    end
    epoch_writes732 = _t1417
    if match_lookahead_literal(parser, "(", 0)
        _t1420 = parse_epoch_reads(parser)
        _t1419 = _t1420
    else
        _t1419 = nothing
    end
    epoch_reads733 = _t1419
    consume_literal!(parser, ")")
    _t1421 = Proto.Epoch(writes=(!isnothing(epoch_writes732) ? epoch_writes732 : Proto.Write[]), reads=(!isnothing(epoch_reads733) ? epoch_reads733 : Proto.Read[]))
    result735 = _t1421
    record_span!(parser, span_start734, "Epoch")
    return result735
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs736 = Proto.Write[]
    cond737 = match_lookahead_literal(parser, "(", 0)
    while cond737
        _t1422 = parse_write(parser)
        item738 = _t1422
        push!(xs736, item738)
        cond737 = match_lookahead_literal(parser, "(", 0)
    end
    writes739 = xs736
    consume_literal!(parser, ")")
    return writes739
end

function parse_write(parser::ParserState)::Proto.Write
    span_start745 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1424 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1425 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1426 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1427 = 2
                    else
                        _t1427 = -1
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
    prediction740 = _t1423
    if prediction740 == 3
        _t1429 = parse_snapshot(parser)
        snapshot744 = _t1429
        _t1430 = Proto.Write(write_type=OneOf(:snapshot, snapshot744))
        _t1428 = _t1430
    else
        if prediction740 == 2
            _t1432 = parse_context(parser)
            context743 = _t1432
            _t1433 = Proto.Write(write_type=OneOf(:context, context743))
            _t1431 = _t1433
        else
            if prediction740 == 1
                _t1435 = parse_undefine(parser)
                undefine742 = _t1435
                _t1436 = Proto.Write(write_type=OneOf(:undefine, undefine742))
                _t1434 = _t1436
            else
                if prediction740 == 0
                    _t1438 = parse_define(parser)
                    define741 = _t1438
                    _t1439 = Proto.Write(write_type=OneOf(:define, define741))
                    _t1437 = _t1439
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1434 = _t1437
            end
            _t1431 = _t1434
        end
        _t1428 = _t1431
    end
    result746 = _t1428
    record_span!(parser, span_start745, "Write")
    return result746
end

function parse_define(parser::ParserState)::Proto.Define
    span_start748 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1440 = parse_fragment(parser)
    fragment747 = _t1440
    consume_literal!(parser, ")")
    _t1441 = Proto.Define(fragment=fragment747)
    result749 = _t1441
    record_span!(parser, span_start748, "Define")
    return result749
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start755 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1442 = parse_new_fragment_id(parser)
    new_fragment_id750 = _t1442
    xs751 = Proto.Declaration[]
    cond752 = match_lookahead_literal(parser, "(", 0)
    while cond752
        _t1443 = parse_declaration(parser)
        item753 = _t1443
        push!(xs751, item753)
        cond752 = match_lookahead_literal(parser, "(", 0)
    end
    declarations754 = xs751
    consume_literal!(parser, ")")
    result756 = construct_fragment(parser, new_fragment_id750, declarations754)
    record_span!(parser, span_start755, "Fragment")
    return result756
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start758 = span_start(parser)
    _t1444 = parse_fragment_id(parser)
    fragment_id757 = _t1444
    start_fragment!(parser, fragment_id757)
    result759 = fragment_id757
    record_span!(parser, span_start758, "FragmentId")
    return result759
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start765 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1446 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1447 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1448 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1449 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1450 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1451 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1452 = 1
                                else
                                    _t1452 = -1
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
    else
        _t1445 = -1
    end
    prediction760 = _t1445
    if prediction760 == 3
        _t1454 = parse_data(parser)
        data764 = _t1454
        _t1455 = Proto.Declaration(declaration_type=OneOf(:data, data764))
        _t1453 = _t1455
    else
        if prediction760 == 2
            _t1457 = parse_constraint(parser)
            constraint763 = _t1457
            _t1458 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint763))
            _t1456 = _t1458
        else
            if prediction760 == 1
                _t1460 = parse_algorithm(parser)
                algorithm762 = _t1460
                _t1461 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm762))
                _t1459 = _t1461
            else
                if prediction760 == 0
                    _t1463 = parse_def(parser)
                    def761 = _t1463
                    _t1464 = Proto.Declaration(declaration_type=OneOf(:def, def761))
                    _t1462 = _t1464
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1459 = _t1462
            end
            _t1456 = _t1459
        end
        _t1453 = _t1456
    end
    result766 = _t1453
    record_span!(parser, span_start765, "Declaration")
    return result766
end

function parse_def(parser::ParserState)::Proto.Def
    span_start770 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1465 = parse_relation_id(parser)
    relation_id767 = _t1465
    _t1466 = parse_abstraction(parser)
    abstraction768 = _t1466
    if match_lookahead_literal(parser, "(", 0)
        _t1468 = parse_attrs(parser)
        _t1467 = _t1468
    else
        _t1467 = nothing
    end
    attrs769 = _t1467
    consume_literal!(parser, ")")
    _t1469 = Proto.Def(name=relation_id767, body=abstraction768, attrs=(!isnothing(attrs769) ? attrs769 : Proto.Attribute[]))
    result771 = _t1469
    record_span!(parser, span_start770, "Def")
    return result771
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start775 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1470 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1471 = 1
        else
            _t1471 = -1
        end
        _t1470 = _t1471
    end
    prediction772 = _t1470
    if prediction772 == 1
        uint128774 = consume_terminal!(parser, "UINT128")
        _t1472 = Proto.RelationId(uint128774.low, uint128774.high)
    else
        if prediction772 == 0
            consume_literal!(parser, ":")
            symbol773 = consume_terminal!(parser, "SYMBOL")
            _t1473 = relation_id_from_string(parser, symbol773)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1472 = _t1473
    end
    result776 = _t1472
    record_span!(parser, span_start775, "RelationId")
    return result776
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start779 = span_start(parser)
    consume_literal!(parser, "(")
    _t1474 = parse_bindings(parser)
    bindings777 = _t1474
    _t1475 = parse_formula(parser)
    formula778 = _t1475
    consume_literal!(parser, ")")
    _t1476 = Proto.Abstraction(vars=vcat(bindings777[1], !isnothing(bindings777[2]) ? bindings777[2] : []), value=formula778)
    result780 = _t1476
    record_span!(parser, span_start779, "Abstraction")
    return result780
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs781 = Proto.Binding[]
    cond782 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond782
        _t1477 = parse_binding(parser)
        item783 = _t1477
        push!(xs781, item783)
        cond782 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings784 = xs781
    if match_lookahead_literal(parser, "|", 0)
        _t1479 = parse_value_bindings(parser)
        _t1478 = _t1479
    else
        _t1478 = nothing
    end
    value_bindings785 = _t1478
    consume_literal!(parser, "]")
    return (bindings784, (!isnothing(value_bindings785) ? value_bindings785 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start788 = span_start(parser)
    symbol786 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1480 = parse_type(parser)
    type787 = _t1480
    _t1481 = Proto.Var(name=symbol786)
    _t1482 = Proto.Binding(var=_t1481, var"#type"=type787)
    result789 = _t1482
    record_span!(parser, span_start788, "Binding")
    return result789
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start805 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1483 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1484 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1485 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1486 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1487 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1488 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1489 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1490 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1491 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1492 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1493 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1494 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1495 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1496 = 9
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
                _t1485 = _t1486
            end
            _t1484 = _t1485
        end
        _t1483 = _t1484
    end
    prediction790 = _t1483
    if prediction790 == 13
        _t1498 = parse_uint32_type(parser)
        uint32_type804 = _t1498
        _t1499 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type804))
        _t1497 = _t1499
    else
        if prediction790 == 12
            _t1501 = parse_float32_type(parser)
            float32_type803 = _t1501
            _t1502 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type803))
            _t1500 = _t1502
        else
            if prediction790 == 11
                _t1504 = parse_int32_type(parser)
                int32_type802 = _t1504
                _t1505 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type802))
                _t1503 = _t1505
            else
                if prediction790 == 10
                    _t1507 = parse_boolean_type(parser)
                    boolean_type801 = _t1507
                    _t1508 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type801))
                    _t1506 = _t1508
                else
                    if prediction790 == 9
                        _t1510 = parse_decimal_type(parser)
                        decimal_type800 = _t1510
                        _t1511 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type800))
                        _t1509 = _t1511
                    else
                        if prediction790 == 8
                            _t1513 = parse_missing_type(parser)
                            missing_type799 = _t1513
                            _t1514 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type799))
                            _t1512 = _t1514
                        else
                            if prediction790 == 7
                                _t1516 = parse_datetime_type(parser)
                                datetime_type798 = _t1516
                                _t1517 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type798))
                                _t1515 = _t1517
                            else
                                if prediction790 == 6
                                    _t1519 = parse_date_type(parser)
                                    date_type797 = _t1519
                                    _t1520 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type797))
                                    _t1518 = _t1520
                                else
                                    if prediction790 == 5
                                        _t1522 = parse_int128_type(parser)
                                        int128_type796 = _t1522
                                        _t1523 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type796))
                                        _t1521 = _t1523
                                    else
                                        if prediction790 == 4
                                            _t1525 = parse_uint128_type(parser)
                                            uint128_type795 = _t1525
                                            _t1526 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type795))
                                            _t1524 = _t1526
                                        else
                                            if prediction790 == 3
                                                _t1528 = parse_float_type(parser)
                                                float_type794 = _t1528
                                                _t1529 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type794))
                                                _t1527 = _t1529
                                            else
                                                if prediction790 == 2
                                                    _t1531 = parse_int_type(parser)
                                                    int_type793 = _t1531
                                                    _t1532 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type793))
                                                    _t1530 = _t1532
                                                else
                                                    if prediction790 == 1
                                                        _t1534 = parse_string_type(parser)
                                                        string_type792 = _t1534
                                                        _t1535 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type792))
                                                        _t1533 = _t1535
                                                    else
                                                        if prediction790 == 0
                                                            _t1537 = parse_unspecified_type(parser)
                                                            unspecified_type791 = _t1537
                                                            _t1538 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type791))
                                                            _t1536 = _t1538
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1533 = _t1536
                                                    end
                                                    _t1530 = _t1533
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
    result806 = _t1497
    record_span!(parser, span_start805, "Type")
    return result806
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start807 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1539 = Proto.UnspecifiedType()
    result808 = _t1539
    record_span!(parser, span_start807, "UnspecifiedType")
    return result808
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start809 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1540 = Proto.StringType()
    result810 = _t1540
    record_span!(parser, span_start809, "StringType")
    return result810
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start811 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1541 = Proto.IntType()
    result812 = _t1541
    record_span!(parser, span_start811, "IntType")
    return result812
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start813 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1542 = Proto.FloatType()
    result814 = _t1542
    record_span!(parser, span_start813, "FloatType")
    return result814
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start815 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1543 = Proto.UInt128Type()
    result816 = _t1543
    record_span!(parser, span_start815, "UInt128Type")
    return result816
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start817 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1544 = Proto.Int128Type()
    result818 = _t1544
    record_span!(parser, span_start817, "Int128Type")
    return result818
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start819 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1545 = Proto.DateType()
    result820 = _t1545
    record_span!(parser, span_start819, "DateType")
    return result820
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start821 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1546 = Proto.DateTimeType()
    result822 = _t1546
    record_span!(parser, span_start821, "DateTimeType")
    return result822
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start823 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1547 = Proto.MissingType()
    result824 = _t1547
    record_span!(parser, span_start823, "MissingType")
    return result824
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start827 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int825 = consume_terminal!(parser, "INT")
    int_3826 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1548 = Proto.DecimalType(precision=Int32(int825), scale=Int32(int_3826))
    result828 = _t1548
    record_span!(parser, span_start827, "DecimalType")
    return result828
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start829 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1549 = Proto.BooleanType()
    result830 = _t1549
    record_span!(parser, span_start829, "BooleanType")
    return result830
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start831 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1550 = Proto.Int32Type()
    result832 = _t1550
    record_span!(parser, span_start831, "Int32Type")
    return result832
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start833 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1551 = Proto.Float32Type()
    result834 = _t1551
    record_span!(parser, span_start833, "Float32Type")
    return result834
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start835 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1552 = Proto.UInt32Type()
    result836 = _t1552
    record_span!(parser, span_start835, "UInt32Type")
    return result836
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs837 = Proto.Binding[]
    cond838 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond838
        _t1553 = parse_binding(parser)
        item839 = _t1553
        push!(xs837, item839)
        cond838 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings840 = xs837
    return bindings840
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start855 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1555 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1556 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1557 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1558 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1559 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1560 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1561 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1562 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1563 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1564 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1565 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1566 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1567 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1568 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1569 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1570 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1571 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1572 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1573 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1574 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1575 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1576 = 10
                                                                                            else
                                                                                                _t1576 = -1
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
            end
            _t1555 = _t1556
        end
        _t1554 = _t1555
    else
        _t1554 = -1
    end
    prediction841 = _t1554
    if prediction841 == 12
        _t1578 = parse_cast(parser)
        cast854 = _t1578
        _t1579 = Proto.Formula(formula_type=OneOf(:cast, cast854))
        _t1577 = _t1579
    else
        if prediction841 == 11
            _t1581 = parse_rel_atom(parser)
            rel_atom853 = _t1581
            _t1582 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom853))
            _t1580 = _t1582
        else
            if prediction841 == 10
                _t1584 = parse_primitive(parser)
                primitive852 = _t1584
                _t1585 = Proto.Formula(formula_type=OneOf(:primitive, primitive852))
                _t1583 = _t1585
            else
                if prediction841 == 9
                    _t1587 = parse_pragma(parser)
                    pragma851 = _t1587
                    _t1588 = Proto.Formula(formula_type=OneOf(:pragma, pragma851))
                    _t1586 = _t1588
                else
                    if prediction841 == 8
                        _t1590 = parse_atom(parser)
                        atom850 = _t1590
                        _t1591 = Proto.Formula(formula_type=OneOf(:atom, atom850))
                        _t1589 = _t1591
                    else
                        if prediction841 == 7
                            _t1593 = parse_ffi(parser)
                            ffi849 = _t1593
                            _t1594 = Proto.Formula(formula_type=OneOf(:ffi, ffi849))
                            _t1592 = _t1594
                        else
                            if prediction841 == 6
                                _t1596 = parse_not(parser)
                                not848 = _t1596
                                _t1597 = Proto.Formula(formula_type=OneOf(:not, not848))
                                _t1595 = _t1597
                            else
                                if prediction841 == 5
                                    _t1599 = parse_disjunction(parser)
                                    disjunction847 = _t1599
                                    _t1600 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction847))
                                    _t1598 = _t1600
                                else
                                    if prediction841 == 4
                                        _t1602 = parse_conjunction(parser)
                                        conjunction846 = _t1602
                                        _t1603 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction846))
                                        _t1601 = _t1603
                                    else
                                        if prediction841 == 3
                                            _t1605 = parse_reduce(parser)
                                            reduce845 = _t1605
                                            _t1606 = Proto.Formula(formula_type=OneOf(:reduce, reduce845))
                                            _t1604 = _t1606
                                        else
                                            if prediction841 == 2
                                                _t1608 = parse_exists(parser)
                                                exists844 = _t1608
                                                _t1609 = Proto.Formula(formula_type=OneOf(:exists, exists844))
                                                _t1607 = _t1609
                                            else
                                                if prediction841 == 1
                                                    _t1611 = parse_false(parser)
                                                    false843 = _t1611
                                                    _t1612 = Proto.Formula(formula_type=OneOf(:disjunction, false843))
                                                    _t1610 = _t1612
                                                else
                                                    if prediction841 == 0
                                                        _t1614 = parse_true(parser)
                                                        true842 = _t1614
                                                        _t1615 = Proto.Formula(formula_type=OneOf(:conjunction, true842))
                                                        _t1613 = _t1615
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1610 = _t1613
                                                end
                                                _t1607 = _t1610
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
    result856 = _t1577
    record_span!(parser, span_start855, "Formula")
    return result856
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start857 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1616 = Proto.Conjunction(args=Proto.Formula[])
    result858 = _t1616
    record_span!(parser, span_start857, "Conjunction")
    return result858
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start859 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1617 = Proto.Disjunction(args=Proto.Formula[])
    result860 = _t1617
    record_span!(parser, span_start859, "Disjunction")
    return result860
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start863 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1618 = parse_bindings(parser)
    bindings861 = _t1618
    _t1619 = parse_formula(parser)
    formula862 = _t1619
    consume_literal!(parser, ")")
    _t1620 = Proto.Abstraction(vars=vcat(bindings861[1], !isnothing(bindings861[2]) ? bindings861[2] : []), value=formula862)
    _t1621 = Proto.Exists(body=_t1620)
    result864 = _t1621
    record_span!(parser, span_start863, "Exists")
    return result864
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start868 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1622 = parse_abstraction(parser)
    abstraction865 = _t1622
    _t1623 = parse_abstraction(parser)
    abstraction_3866 = _t1623
    _t1624 = parse_terms(parser)
    terms867 = _t1624
    consume_literal!(parser, ")")
    _t1625 = Proto.Reduce(op=abstraction865, body=abstraction_3866, terms=terms867)
    result869 = _t1625
    record_span!(parser, span_start868, "Reduce")
    return result869
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs870 = Proto.Term[]
    cond871 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond871
        _t1626 = parse_term(parser)
        item872 = _t1626
        push!(xs870, item872)
        cond871 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms873 = xs870
    consume_literal!(parser, ")")
    return terms873
end

function parse_term(parser::ParserState)::Proto.Term
    span_start877 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1627 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1628 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1629 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1630 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1631 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1632 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1633 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1634 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1635 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1636 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1637 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1638 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1639 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1640 = 1
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
    prediction874 = _t1627
    if prediction874 == 1
        _t1642 = parse_value(parser)
        value876 = _t1642
        _t1643 = Proto.Term(term_type=OneOf(:constant, value876))
        _t1641 = _t1643
    else
        if prediction874 == 0
            _t1645 = parse_var(parser)
            var875 = _t1645
            _t1646 = Proto.Term(term_type=OneOf(:var, var875))
            _t1644 = _t1646
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1641 = _t1644
    end
    result878 = _t1641
    record_span!(parser, span_start877, "Term")
    return result878
end

function parse_var(parser::ParserState)::Proto.Var
    span_start880 = span_start(parser)
    symbol879 = consume_terminal!(parser, "SYMBOL")
    _t1647 = Proto.Var(name=symbol879)
    result881 = _t1647
    record_span!(parser, span_start880, "Var")
    return result881
end

function parse_value(parser::ParserState)::Proto.Value
    span_start895 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1648 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1649 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1650 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1652 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1653 = 0
                        else
                            _t1653 = -1
                        end
                        _t1652 = _t1653
                    end
                    _t1651 = _t1652
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1654 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1655 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1656 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1657 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1658 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1659 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1660 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1661 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1662 = 10
                                                    else
                                                        _t1662 = -1
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
                            _t1655 = _t1656
                        end
                        _t1654 = _t1655
                    end
                    _t1651 = _t1654
                end
                _t1650 = _t1651
            end
            _t1649 = _t1650
        end
        _t1648 = _t1649
    end
    prediction882 = _t1648
    if prediction882 == 12
        _t1664 = parse_boolean_value(parser)
        boolean_value894 = _t1664
        _t1665 = Proto.Value(value=OneOf(:boolean_value, boolean_value894))
        _t1663 = _t1665
    else
        if prediction882 == 11
            consume_literal!(parser, "missing")
            _t1667 = Proto.MissingValue()
            _t1668 = Proto.Value(value=OneOf(:missing_value, _t1667))
            _t1666 = _t1668
        else
            if prediction882 == 10
                formatted_decimal893 = consume_terminal!(parser, "DECIMAL")
                _t1670 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal893))
                _t1669 = _t1670
            else
                if prediction882 == 9
                    formatted_int128892 = consume_terminal!(parser, "INT128")
                    _t1672 = Proto.Value(value=OneOf(:int128_value, formatted_int128892))
                    _t1671 = _t1672
                else
                    if prediction882 == 8
                        formatted_uint128891 = consume_terminal!(parser, "UINT128")
                        _t1674 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128891))
                        _t1673 = _t1674
                    else
                        if prediction882 == 7
                            formatted_uint32890 = consume_terminal!(parser, "UINT32")
                            _t1676 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32890))
                            _t1675 = _t1676
                        else
                            if prediction882 == 6
                                formatted_float889 = consume_terminal!(parser, "FLOAT")
                                _t1678 = Proto.Value(value=OneOf(:float_value, formatted_float889))
                                _t1677 = _t1678
                            else
                                if prediction882 == 5
                                    formatted_float32888 = consume_terminal!(parser, "FLOAT32")
                                    _t1680 = Proto.Value(value=OneOf(:float32_value, formatted_float32888))
                                    _t1679 = _t1680
                                else
                                    if prediction882 == 4
                                        formatted_int887 = consume_terminal!(parser, "INT")
                                        _t1682 = Proto.Value(value=OneOf(:int_value, formatted_int887))
                                        _t1681 = _t1682
                                    else
                                        if prediction882 == 3
                                            formatted_int32886 = consume_terminal!(parser, "INT32")
                                            _t1684 = Proto.Value(value=OneOf(:int32_value, formatted_int32886))
                                            _t1683 = _t1684
                                        else
                                            if prediction882 == 2
                                                formatted_string885 = consume_terminal!(parser, "STRING")
                                                _t1686 = Proto.Value(value=OneOf(:string_value, formatted_string885))
                                                _t1685 = _t1686
                                            else
                                                if prediction882 == 1
                                                    _t1688 = parse_datetime(parser)
                                                    datetime884 = _t1688
                                                    _t1689 = Proto.Value(value=OneOf(:datetime_value, datetime884))
                                                    _t1687 = _t1689
                                                else
                                                    if prediction882 == 0
                                                        _t1691 = parse_date(parser)
                                                        date883 = _t1691
                                                        _t1692 = Proto.Value(value=OneOf(:date_value, date883))
                                                        _t1690 = _t1692
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1687 = _t1690
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
                _t1669 = _t1671
            end
            _t1666 = _t1669
        end
        _t1663 = _t1666
    end
    result896 = _t1663
    record_span!(parser, span_start895, "Value")
    return result896
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start900 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int897 = consume_terminal!(parser, "INT")
    formatted_int_3898 = consume_terminal!(parser, "INT")
    formatted_int_4899 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1693 = Proto.DateValue(year=Int32(formatted_int897), month=Int32(formatted_int_3898), day=Int32(formatted_int_4899))
    result901 = _t1693
    record_span!(parser, span_start900, "DateValue")
    return result901
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start909 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int902 = consume_terminal!(parser, "INT")
    formatted_int_3903 = consume_terminal!(parser, "INT")
    formatted_int_4904 = consume_terminal!(parser, "INT")
    formatted_int_5905 = consume_terminal!(parser, "INT")
    formatted_int_6906 = consume_terminal!(parser, "INT")
    formatted_int_7907 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1694 = consume_terminal!(parser, "INT")
    else
        _t1694 = nothing
    end
    formatted_int_8908 = _t1694
    consume_literal!(parser, ")")
    _t1695 = Proto.DateTimeValue(year=Int32(formatted_int902), month=Int32(formatted_int_3903), day=Int32(formatted_int_4904), hour=Int32(formatted_int_5905), minute=Int32(formatted_int_6906), second=Int32(formatted_int_7907), microsecond=Int32((!isnothing(formatted_int_8908) ? formatted_int_8908 : 0)))
    result910 = _t1695
    record_span!(parser, span_start909, "DateTimeValue")
    return result910
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start915 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs911 = Proto.Formula[]
    cond912 = match_lookahead_literal(parser, "(", 0)
    while cond912
        _t1696 = parse_formula(parser)
        item913 = _t1696
        push!(xs911, item913)
        cond912 = match_lookahead_literal(parser, "(", 0)
    end
    formulas914 = xs911
    consume_literal!(parser, ")")
    _t1697 = Proto.Conjunction(args=formulas914)
    result916 = _t1697
    record_span!(parser, span_start915, "Conjunction")
    return result916
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start921 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs917 = Proto.Formula[]
    cond918 = match_lookahead_literal(parser, "(", 0)
    while cond918
        _t1698 = parse_formula(parser)
        item919 = _t1698
        push!(xs917, item919)
        cond918 = match_lookahead_literal(parser, "(", 0)
    end
    formulas920 = xs917
    consume_literal!(parser, ")")
    _t1699 = Proto.Disjunction(args=formulas920)
    result922 = _t1699
    record_span!(parser, span_start921, "Disjunction")
    return result922
end

function parse_not(parser::ParserState)::Proto.Not
    span_start924 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1700 = parse_formula(parser)
    formula923 = _t1700
    consume_literal!(parser, ")")
    _t1701 = Proto.Not(arg=formula923)
    result925 = _t1701
    record_span!(parser, span_start924, "Not")
    return result925
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start929 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1702 = parse_name(parser)
    name926 = _t1702
    _t1703 = parse_ffi_args(parser)
    ffi_args927 = _t1703
    _t1704 = parse_terms(parser)
    terms928 = _t1704
    consume_literal!(parser, ")")
    _t1705 = Proto.FFI(name=name926, args=ffi_args927, terms=terms928)
    result930 = _t1705
    record_span!(parser, span_start929, "FFI")
    return result930
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol931 = consume_terminal!(parser, "SYMBOL")
    return symbol931
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs932 = Proto.Abstraction[]
    cond933 = match_lookahead_literal(parser, "(", 0)
    while cond933
        _t1706 = parse_abstraction(parser)
        item934 = _t1706
        push!(xs932, item934)
        cond933 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions935 = xs932
    consume_literal!(parser, ")")
    return abstractions935
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start941 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1707 = parse_relation_id(parser)
    relation_id936 = _t1707
    xs937 = Proto.Term[]
    cond938 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond938
        _t1708 = parse_term(parser)
        item939 = _t1708
        push!(xs937, item939)
        cond938 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms940 = xs937
    consume_literal!(parser, ")")
    _t1709 = Proto.Atom(name=relation_id936, terms=terms940)
    result942 = _t1709
    record_span!(parser, span_start941, "Atom")
    return result942
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start948 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1710 = parse_name(parser)
    name943 = _t1710
    xs944 = Proto.Term[]
    cond945 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond945
        _t1711 = parse_term(parser)
        item946 = _t1711
        push!(xs944, item946)
        cond945 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms947 = xs944
    consume_literal!(parser, ")")
    _t1712 = Proto.Pragma(name=name943, terms=terms947)
    result949 = _t1712
    record_span!(parser, span_start948, "Pragma")
    return result949
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start965 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1714 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1715 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1716 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1717 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1718 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1719 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1720 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1721 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1722 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1723 = 7
                                            else
                                                _t1723 = -1
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
            end
            _t1714 = _t1715
        end
        _t1713 = _t1714
    else
        _t1713 = -1
    end
    prediction950 = _t1713
    if prediction950 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1725 = parse_name(parser)
        name960 = _t1725
        xs961 = Proto.RelTerm[]
        cond962 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond962
            _t1726 = parse_rel_term(parser)
            item963 = _t1726
            push!(xs961, item963)
            cond962 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms964 = xs961
        consume_literal!(parser, ")")
        _t1727 = Proto.Primitive(name=name960, terms=rel_terms964)
        _t1724 = _t1727
    else
        if prediction950 == 8
            _t1729 = parse_divide(parser)
            divide959 = _t1729
            _t1728 = divide959
        else
            if prediction950 == 7
                _t1731 = parse_multiply(parser)
                multiply958 = _t1731
                _t1730 = multiply958
            else
                if prediction950 == 6
                    _t1733 = parse_minus(parser)
                    minus957 = _t1733
                    _t1732 = minus957
                else
                    if prediction950 == 5
                        _t1735 = parse_add(parser)
                        add956 = _t1735
                        _t1734 = add956
                    else
                        if prediction950 == 4
                            _t1737 = parse_gt_eq(parser)
                            gt_eq955 = _t1737
                            _t1736 = gt_eq955
                        else
                            if prediction950 == 3
                                _t1739 = parse_gt(parser)
                                gt954 = _t1739
                                _t1738 = gt954
                            else
                                if prediction950 == 2
                                    _t1741 = parse_lt_eq(parser)
                                    lt_eq953 = _t1741
                                    _t1740 = lt_eq953
                                else
                                    if prediction950 == 1
                                        _t1743 = parse_lt(parser)
                                        lt952 = _t1743
                                        _t1742 = lt952
                                    else
                                        if prediction950 == 0
                                            _t1745 = parse_eq(parser)
                                            eq951 = _t1745
                                            _t1744 = eq951
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
            _t1728 = _t1730
        end
        _t1724 = _t1728
    end
    result966 = _t1724
    record_span!(parser, span_start965, "Primitive")
    return result966
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1746 = parse_term(parser)
    term967 = _t1746
    _t1747 = parse_term(parser)
    term_3968 = _t1747
    consume_literal!(parser, ")")
    _t1748 = Proto.RelTerm(rel_term_type=OneOf(:term, term967))
    _t1749 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3968))
    _t1750 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1748, _t1749])
    result970 = _t1750
    record_span!(parser, span_start969, "Primitive")
    return result970
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start973 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1751 = parse_term(parser)
    term971 = _t1751
    _t1752 = parse_term(parser)
    term_3972 = _t1752
    consume_literal!(parser, ")")
    _t1753 = Proto.RelTerm(rel_term_type=OneOf(:term, term971))
    _t1754 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3972))
    _t1755 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1753, _t1754])
    result974 = _t1755
    record_span!(parser, span_start973, "Primitive")
    return result974
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start977 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1756 = parse_term(parser)
    term975 = _t1756
    _t1757 = parse_term(parser)
    term_3976 = _t1757
    consume_literal!(parser, ")")
    _t1758 = Proto.RelTerm(rel_term_type=OneOf(:term, term975))
    _t1759 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3976))
    _t1760 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1758, _t1759])
    result978 = _t1760
    record_span!(parser, span_start977, "Primitive")
    return result978
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start981 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1761 = parse_term(parser)
    term979 = _t1761
    _t1762 = parse_term(parser)
    term_3980 = _t1762
    consume_literal!(parser, ")")
    _t1763 = Proto.RelTerm(rel_term_type=OneOf(:term, term979))
    _t1764 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3980))
    _t1765 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1763, _t1764])
    result982 = _t1765
    record_span!(parser, span_start981, "Primitive")
    return result982
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start985 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1766 = parse_term(parser)
    term983 = _t1766
    _t1767 = parse_term(parser)
    term_3984 = _t1767
    consume_literal!(parser, ")")
    _t1768 = Proto.RelTerm(rel_term_type=OneOf(:term, term983))
    _t1769 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3984))
    _t1770 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1768, _t1769])
    result986 = _t1770
    record_span!(parser, span_start985, "Primitive")
    return result986
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start990 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1771 = parse_term(parser)
    term987 = _t1771
    _t1772 = parse_term(parser)
    term_3988 = _t1772
    _t1773 = parse_term(parser)
    term_4989 = _t1773
    consume_literal!(parser, ")")
    _t1774 = Proto.RelTerm(rel_term_type=OneOf(:term, term987))
    _t1775 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3988))
    _t1776 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4989))
    _t1777 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1774, _t1775, _t1776])
    result991 = _t1777
    record_span!(parser, span_start990, "Primitive")
    return result991
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start995 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1778 = parse_term(parser)
    term992 = _t1778
    _t1779 = parse_term(parser)
    term_3993 = _t1779
    _t1780 = parse_term(parser)
    term_4994 = _t1780
    consume_literal!(parser, ")")
    _t1781 = Proto.RelTerm(rel_term_type=OneOf(:term, term992))
    _t1782 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3993))
    _t1783 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4994))
    _t1784 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1781, _t1782, _t1783])
    result996 = _t1784
    record_span!(parser, span_start995, "Primitive")
    return result996
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1000 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1785 = parse_term(parser)
    term997 = _t1785
    _t1786 = parse_term(parser)
    term_3998 = _t1786
    _t1787 = parse_term(parser)
    term_4999 = _t1787
    consume_literal!(parser, ")")
    _t1788 = Proto.RelTerm(rel_term_type=OneOf(:term, term997))
    _t1789 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3998))
    _t1790 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4999))
    _t1791 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1788, _t1789, _t1790])
    result1001 = _t1791
    record_span!(parser, span_start1000, "Primitive")
    return result1001
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1005 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1792 = parse_term(parser)
    term1002 = _t1792
    _t1793 = parse_term(parser)
    term_31003 = _t1793
    _t1794 = parse_term(parser)
    term_41004 = _t1794
    consume_literal!(parser, ")")
    _t1795 = Proto.RelTerm(rel_term_type=OneOf(:term, term1002))
    _t1796 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31003))
    _t1797 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41004))
    _t1798 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1795, _t1796, _t1797])
    result1006 = _t1798
    record_span!(parser, span_start1005, "Primitive")
    return result1006
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1010 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1799 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1800 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1801 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1802 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1803 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1804 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1805 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1806 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1807 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1808 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1809 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1810 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1811 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1812 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1813 = 1
                                                            else
                                                                _t1813 = -1
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
            _t1800 = _t1801
        end
        _t1799 = _t1800
    end
    prediction1007 = _t1799
    if prediction1007 == 1
        _t1815 = parse_term(parser)
        term1009 = _t1815
        _t1816 = Proto.RelTerm(rel_term_type=OneOf(:term, term1009))
        _t1814 = _t1816
    else
        if prediction1007 == 0
            _t1818 = parse_specialized_value(parser)
            specialized_value1008 = _t1818
            _t1819 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1008))
            _t1817 = _t1819
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1814 = _t1817
    end
    result1011 = _t1814
    record_span!(parser, span_start1010, "RelTerm")
    return result1011
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1013 = span_start(parser)
    consume_literal!(parser, "#")
    _t1820 = parse_raw_value(parser)
    raw_value1012 = _t1820
    result1014 = raw_value1012
    record_span!(parser, span_start1013, "Value")
    return result1014
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1020 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1821 = parse_name(parser)
    name1015 = _t1821
    xs1016 = Proto.RelTerm[]
    cond1017 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1017
        _t1822 = parse_rel_term(parser)
        item1018 = _t1822
        push!(xs1016, item1018)
        cond1017 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1019 = xs1016
    consume_literal!(parser, ")")
    _t1823 = Proto.RelAtom(name=name1015, terms=rel_terms1019)
    result1021 = _t1823
    record_span!(parser, span_start1020, "RelAtom")
    return result1021
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1024 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1824 = parse_term(parser)
    term1022 = _t1824
    _t1825 = parse_term(parser)
    term_31023 = _t1825
    consume_literal!(parser, ")")
    _t1826 = Proto.Cast(input=term1022, result=term_31023)
    result1025 = _t1826
    record_span!(parser, span_start1024, "Cast")
    return result1025
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1026 = Proto.Attribute[]
    cond1027 = match_lookahead_literal(parser, "(", 0)
    while cond1027
        _t1827 = parse_attribute(parser)
        item1028 = _t1827
        push!(xs1026, item1028)
        cond1027 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1029 = xs1026
    consume_literal!(parser, ")")
    return attributes1029
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1035 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1828 = parse_name(parser)
    name1030 = _t1828
    xs1031 = Proto.Value[]
    cond1032 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1032
        _t1829 = parse_raw_value(parser)
        item1033 = _t1829
        push!(xs1031, item1033)
        cond1032 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1034 = xs1031
    consume_literal!(parser, ")")
    _t1830 = Proto.Attribute(name=name1030, args=raw_values1034)
    result1036 = _t1830
    record_span!(parser, span_start1035, "Attribute")
    return result1036
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1043 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1037 = Proto.RelationId[]
    cond1038 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1038
        _t1831 = parse_relation_id(parser)
        item1039 = _t1831
        push!(xs1037, item1039)
        cond1038 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1040 = xs1037
    _t1832 = parse_script(parser)
    script1041 = _t1832
    if match_lookahead_literal(parser, "(", 0)
        _t1834 = parse_attrs(parser)
        _t1833 = _t1834
    else
        _t1833 = nothing
    end
    attrs1042 = _t1833
    consume_literal!(parser, ")")
    _t1835 = Proto.Algorithm(var"#global"=relation_ids1040, body=script1041, attrs=(!isnothing(attrs1042) ? attrs1042 : Proto.Attribute[]))
    result1044 = _t1835
    record_span!(parser, span_start1043, "Algorithm")
    return result1044
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1049 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1045 = Proto.Construct[]
    cond1046 = match_lookahead_literal(parser, "(", 0)
    while cond1046
        _t1836 = parse_construct(parser)
        item1047 = _t1836
        push!(xs1045, item1047)
        cond1046 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1048 = xs1045
    consume_literal!(parser, ")")
    _t1837 = Proto.Script(constructs=constructs1048)
    result1050 = _t1837
    record_span!(parser, span_start1049, "Script")
    return result1050
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1054 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1839 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1840 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1841 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1842 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1843 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1844 = 1
                            else
                                _t1844 = -1
                            end
                            _t1843 = _t1844
                        end
                        _t1842 = _t1843
                    end
                    _t1841 = _t1842
                end
                _t1840 = _t1841
            end
            _t1839 = _t1840
        end
        _t1838 = _t1839
    else
        _t1838 = -1
    end
    prediction1051 = _t1838
    if prediction1051 == 1
        _t1846 = parse_instruction(parser)
        instruction1053 = _t1846
        _t1847 = Proto.Construct(construct_type=OneOf(:instruction, instruction1053))
        _t1845 = _t1847
    else
        if prediction1051 == 0
            _t1849 = parse_loop(parser)
            loop1052 = _t1849
            _t1850 = Proto.Construct(construct_type=OneOf(:loop, loop1052))
            _t1848 = _t1850
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1845 = _t1848
    end
    result1055 = _t1845
    record_span!(parser, span_start1054, "Construct")
    return result1055
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1059 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1851 = parse_init(parser)
    init1056 = _t1851
    _t1852 = parse_script(parser)
    script1057 = _t1852
    if match_lookahead_literal(parser, "(", 0)
        _t1854 = parse_attrs(parser)
        _t1853 = _t1854
    else
        _t1853 = nothing
    end
    attrs1058 = _t1853
    consume_literal!(parser, ")")
    _t1855 = Proto.Loop(init=init1056, body=script1057, attrs=(!isnothing(attrs1058) ? attrs1058 : Proto.Attribute[]))
    result1060 = _t1855
    record_span!(parser, span_start1059, "Loop")
    return result1060
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1061 = Proto.Instruction[]
    cond1062 = match_lookahead_literal(parser, "(", 0)
    while cond1062
        _t1856 = parse_instruction(parser)
        item1063 = _t1856
        push!(xs1061, item1063)
        cond1062 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1064 = xs1061
    consume_literal!(parser, ")")
    return instructions1064
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1071 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1858 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1859 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1860 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1861 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1862 = 0
                        else
                            _t1862 = -1
                        end
                        _t1861 = _t1862
                    end
                    _t1860 = _t1861
                end
                _t1859 = _t1860
            end
            _t1858 = _t1859
        end
        _t1857 = _t1858
    else
        _t1857 = -1
    end
    prediction1065 = _t1857
    if prediction1065 == 4
        _t1864 = parse_monus_def(parser)
        monus_def1070 = _t1864
        _t1865 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1070))
        _t1863 = _t1865
    else
        if prediction1065 == 3
            _t1867 = parse_monoid_def(parser)
            monoid_def1069 = _t1867
            _t1868 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1069))
            _t1866 = _t1868
        else
            if prediction1065 == 2
                _t1870 = parse_break(parser)
                break1068 = _t1870
                _t1871 = Proto.Instruction(instr_type=OneOf(:var"#break", break1068))
                _t1869 = _t1871
            else
                if prediction1065 == 1
                    _t1873 = parse_upsert(parser)
                    upsert1067 = _t1873
                    _t1874 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1067))
                    _t1872 = _t1874
                else
                    if prediction1065 == 0
                        _t1876 = parse_assign(parser)
                        assign1066 = _t1876
                        _t1877 = Proto.Instruction(instr_type=OneOf(:assign, assign1066))
                        _t1875 = _t1877
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1872 = _t1875
                end
                _t1869 = _t1872
            end
            _t1866 = _t1869
        end
        _t1863 = _t1866
    end
    result1072 = _t1863
    record_span!(parser, span_start1071, "Instruction")
    return result1072
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1076 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1878 = parse_relation_id(parser)
    relation_id1073 = _t1878
    _t1879 = parse_abstraction(parser)
    abstraction1074 = _t1879
    if match_lookahead_literal(parser, "(", 0)
        _t1881 = parse_attrs(parser)
        _t1880 = _t1881
    else
        _t1880 = nothing
    end
    attrs1075 = _t1880
    consume_literal!(parser, ")")
    _t1882 = Proto.Assign(name=relation_id1073, body=abstraction1074, attrs=(!isnothing(attrs1075) ? attrs1075 : Proto.Attribute[]))
    result1077 = _t1882
    record_span!(parser, span_start1076, "Assign")
    return result1077
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1081 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1883 = parse_relation_id(parser)
    relation_id1078 = _t1883
    _t1884 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1079 = _t1884
    if match_lookahead_literal(parser, "(", 0)
        _t1886 = parse_attrs(parser)
        _t1885 = _t1886
    else
        _t1885 = nothing
    end
    attrs1080 = _t1885
    consume_literal!(parser, ")")
    _t1887 = Proto.Upsert(name=relation_id1078, body=abstraction_with_arity1079[1], attrs=(!isnothing(attrs1080) ? attrs1080 : Proto.Attribute[]), value_arity=abstraction_with_arity1079[2])
    result1082 = _t1887
    record_span!(parser, span_start1081, "Upsert")
    return result1082
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1888 = parse_bindings(parser)
    bindings1083 = _t1888
    _t1889 = parse_formula(parser)
    formula1084 = _t1889
    consume_literal!(parser, ")")
    _t1890 = Proto.Abstraction(vars=vcat(bindings1083[1], !isnothing(bindings1083[2]) ? bindings1083[2] : []), value=formula1084)
    return (_t1890, length(bindings1083[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1088 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1891 = parse_relation_id(parser)
    relation_id1085 = _t1891
    _t1892 = parse_abstraction(parser)
    abstraction1086 = _t1892
    if match_lookahead_literal(parser, "(", 0)
        _t1894 = parse_attrs(parser)
        _t1893 = _t1894
    else
        _t1893 = nothing
    end
    attrs1087 = _t1893
    consume_literal!(parser, ")")
    _t1895 = Proto.Break(name=relation_id1085, body=abstraction1086, attrs=(!isnothing(attrs1087) ? attrs1087 : Proto.Attribute[]))
    result1089 = _t1895
    record_span!(parser, span_start1088, "Break")
    return result1089
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1094 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1896 = parse_monoid(parser)
    monoid1090 = _t1896
    _t1897 = parse_relation_id(parser)
    relation_id1091 = _t1897
    _t1898 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1092 = _t1898
    if match_lookahead_literal(parser, "(", 0)
        _t1900 = parse_attrs(parser)
        _t1899 = _t1900
    else
        _t1899 = nothing
    end
    attrs1093 = _t1899
    consume_literal!(parser, ")")
    _t1901 = Proto.MonoidDef(monoid=monoid1090, name=relation_id1091, body=abstraction_with_arity1092[1], attrs=(!isnothing(attrs1093) ? attrs1093 : Proto.Attribute[]), value_arity=abstraction_with_arity1092[2])
    result1095 = _t1901
    record_span!(parser, span_start1094, "MonoidDef")
    return result1095
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1101 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1903 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1904 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1905 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1906 = 2
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
    prediction1096 = _t1902
    if prediction1096 == 3
        _t1908 = parse_sum_monoid(parser)
        sum_monoid1100 = _t1908
        _t1909 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1100))
        _t1907 = _t1909
    else
        if prediction1096 == 2
            _t1911 = parse_max_monoid(parser)
            max_monoid1099 = _t1911
            _t1912 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1099))
            _t1910 = _t1912
        else
            if prediction1096 == 1
                _t1914 = parse_min_monoid(parser)
                min_monoid1098 = _t1914
                _t1915 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1098))
                _t1913 = _t1915
            else
                if prediction1096 == 0
                    _t1917 = parse_or_monoid(parser)
                    or_monoid1097 = _t1917
                    _t1918 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1097))
                    _t1916 = _t1918
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1913 = _t1916
            end
            _t1910 = _t1913
        end
        _t1907 = _t1910
    end
    result1102 = _t1907
    record_span!(parser, span_start1101, "Monoid")
    return result1102
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1103 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1919 = Proto.OrMonoid()
    result1104 = _t1919
    record_span!(parser, span_start1103, "OrMonoid")
    return result1104
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1106 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1920 = parse_type(parser)
    type1105 = _t1920
    consume_literal!(parser, ")")
    _t1921 = Proto.MinMonoid(var"#type"=type1105)
    result1107 = _t1921
    record_span!(parser, span_start1106, "MinMonoid")
    return result1107
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1109 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1922 = parse_type(parser)
    type1108 = _t1922
    consume_literal!(parser, ")")
    _t1923 = Proto.MaxMonoid(var"#type"=type1108)
    result1110 = _t1923
    record_span!(parser, span_start1109, "MaxMonoid")
    return result1110
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1112 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1924 = parse_type(parser)
    type1111 = _t1924
    consume_literal!(parser, ")")
    _t1925 = Proto.SumMonoid(var"#type"=type1111)
    result1113 = _t1925
    record_span!(parser, span_start1112, "SumMonoid")
    return result1113
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1118 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1926 = parse_monoid(parser)
    monoid1114 = _t1926
    _t1927 = parse_relation_id(parser)
    relation_id1115 = _t1927
    _t1928 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1116 = _t1928
    if match_lookahead_literal(parser, "(", 0)
        _t1930 = parse_attrs(parser)
        _t1929 = _t1930
    else
        _t1929 = nothing
    end
    attrs1117 = _t1929
    consume_literal!(parser, ")")
    _t1931 = Proto.MonusDef(monoid=monoid1114, name=relation_id1115, body=abstraction_with_arity1116[1], attrs=(!isnothing(attrs1117) ? attrs1117 : Proto.Attribute[]), value_arity=abstraction_with_arity1116[2])
    result1119 = _t1931
    record_span!(parser, span_start1118, "MonusDef")
    return result1119
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1124 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1932 = parse_relation_id(parser)
    relation_id1120 = _t1932
    _t1933 = parse_abstraction(parser)
    abstraction1121 = _t1933
    _t1934 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1122 = _t1934
    _t1935 = parse_functional_dependency_values(parser)
    functional_dependency_values1123 = _t1935
    consume_literal!(parser, ")")
    _t1936 = Proto.FunctionalDependency(guard=abstraction1121, keys=functional_dependency_keys1122, values=functional_dependency_values1123)
    _t1937 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1936), name=relation_id1120)
    result1125 = _t1937
    record_span!(parser, span_start1124, "Constraint")
    return result1125
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1126 = Proto.Var[]
    cond1127 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1127
        _t1938 = parse_var(parser)
        item1128 = _t1938
        push!(xs1126, item1128)
        cond1127 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1129 = xs1126
    consume_literal!(parser, ")")
    return vars1129
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1130 = Proto.Var[]
    cond1131 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1131
        _t1939 = parse_var(parser)
        item1132 = _t1939
        push!(xs1130, item1132)
        cond1131 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1133 = xs1130
    consume_literal!(parser, ")")
    return vars1133
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1139 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1941 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1942 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1943 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1944 = 1
                    else
                        _t1944 = -1
                    end
                    _t1943 = _t1944
                end
                _t1942 = _t1943
            end
            _t1941 = _t1942
        end
        _t1940 = _t1941
    else
        _t1940 = -1
    end
    prediction1134 = _t1940
    if prediction1134 == 3
        _t1946 = parse_iceberg_data(parser)
        iceberg_data1138 = _t1946
        _t1947 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1138))
        _t1945 = _t1947
    else
        if prediction1134 == 2
            _t1949 = parse_csv_data(parser)
            csv_data1137 = _t1949
            _t1950 = Proto.Data(data_type=OneOf(:csv_data, csv_data1137))
            _t1948 = _t1950
        else
            if prediction1134 == 1
                _t1952 = parse_betree_relation(parser)
                betree_relation1136 = _t1952
                _t1953 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1136))
                _t1951 = _t1953
            else
                if prediction1134 == 0
                    _t1955 = parse_edb(parser)
                    edb1135 = _t1955
                    _t1956 = Proto.Data(data_type=OneOf(:edb, edb1135))
                    _t1954 = _t1956
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1951 = _t1954
            end
            _t1948 = _t1951
        end
        _t1945 = _t1948
    end
    result1140 = _t1945
    record_span!(parser, span_start1139, "Data")
    return result1140
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1144 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1957 = parse_relation_id(parser)
    relation_id1141 = _t1957
    _t1958 = parse_edb_path(parser)
    edb_path1142 = _t1958
    _t1959 = parse_edb_types(parser)
    edb_types1143 = _t1959
    consume_literal!(parser, ")")
    _t1960 = Proto.EDB(target_id=relation_id1141, path=edb_path1142, types=edb_types1143)
    result1145 = _t1960
    record_span!(parser, span_start1144, "EDB")
    return result1145
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1146 = String[]
    cond1147 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1147
        item1148 = consume_terminal!(parser, "STRING")
        push!(xs1146, item1148)
        cond1147 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1149 = xs1146
    consume_literal!(parser, "]")
    return strings1149
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1150 = Proto.var"#Type"[]
    cond1151 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1151
        _t1961 = parse_type(parser)
        item1152 = _t1961
        push!(xs1150, item1152)
        cond1151 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1153 = xs1150
    consume_literal!(parser, "]")
    return types1153
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1156 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1962 = parse_relation_id(parser)
    relation_id1154 = _t1962
    _t1963 = parse_betree_info(parser)
    betree_info1155 = _t1963
    consume_literal!(parser, ")")
    _t1964 = Proto.BeTreeRelation(name=relation_id1154, relation_info=betree_info1155)
    result1157 = _t1964
    record_span!(parser, span_start1156, "BeTreeRelation")
    return result1157
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1161 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1965 = parse_betree_info_key_types(parser)
    betree_info_key_types1158 = _t1965
    _t1966 = parse_betree_info_value_types(parser)
    betree_info_value_types1159 = _t1966
    _t1967 = parse_config_dict(parser)
    config_dict1160 = _t1967
    consume_literal!(parser, ")")
    _t1968 = construct_betree_info(parser, betree_info_key_types1158, betree_info_value_types1159, config_dict1160)
    result1162 = _t1968
    record_span!(parser, span_start1161, "BeTreeInfo")
    return result1162
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1163 = Proto.var"#Type"[]
    cond1164 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1164
        _t1969 = parse_type(parser)
        item1165 = _t1969
        push!(xs1163, item1165)
        cond1164 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1166 = xs1163
    consume_literal!(parser, ")")
    return types1166
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1167 = Proto.var"#Type"[]
    cond1168 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1168
        _t1970 = parse_type(parser)
        item1169 = _t1970
        push!(xs1167, item1169)
        cond1168 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1170 = xs1167
    consume_literal!(parser, ")")
    return types1170
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1175 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1971 = parse_csvlocator(parser)
    csvlocator1171 = _t1971
    _t1972 = parse_csv_config(parser)
    csv_config1172 = _t1972
    _t1973 = parse_gnf_columns(parser)
    gnf_columns1173 = _t1973
    _t1974 = parse_csv_asof(parser)
    csv_asof1174 = _t1974
    consume_literal!(parser, ")")
    _t1975 = Proto.CSVData(locator=csvlocator1171, config=csv_config1172, columns=gnf_columns1173, asof=csv_asof1174)
    result1176 = _t1975
    record_span!(parser, span_start1175, "CSVData")
    return result1176
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1179 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1977 = parse_csv_locator_paths(parser)
        _t1976 = _t1977
    else
        _t1976 = nothing
    end
    csv_locator_paths1177 = _t1976
    if match_lookahead_literal(parser, "(", 0)
        _t1979 = parse_csv_locator_inline_data(parser)
        _t1978 = _t1979
    else
        _t1978 = nothing
    end
    csv_locator_inline_data1178 = _t1978
    consume_literal!(parser, ")")
    _t1980 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1177) ? csv_locator_paths1177 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1178) ? csv_locator_inline_data1178 : "")))
    result1180 = _t1980
    record_span!(parser, span_start1179, "CSVLocator")
    return result1180
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1181 = String[]
    cond1182 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1182
        item1183 = consume_terminal!(parser, "STRING")
        push!(xs1181, item1183)
        cond1182 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1184 = xs1181
    consume_literal!(parser, ")")
    return strings1184
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1185 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1185
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1188 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1981 = parse_config_dict(parser)
    config_dict1186 = _t1981
    if match_lookahead_literal(parser, "(", 0)
        _t1983 = parse__storage_integration(parser)
        _t1982 = _t1983
    else
        _t1982 = nothing
    end
    _storage_integration1187 = _t1982
    consume_literal!(parser, ")")
    _t1984 = construct_csv_config(parser, config_dict1186, _storage_integration1187)
    result1189 = _t1984
    record_span!(parser, span_start1188, "CSVConfig")
    return result1189
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t1985 = parse_config_dict(parser)
    config_dict1190 = _t1985
    consume_literal!(parser, ")")
    return config_dict1190
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1191 = Proto.GNFColumn[]
    cond1192 = match_lookahead_literal(parser, "(", 0)
    while cond1192
        _t1986 = parse_gnf_column(parser)
        item1193 = _t1986
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
    _t1987 = parse_gnf_column_path(parser)
    gnf_column_path1195 = _t1987
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1989 = parse_relation_id(parser)
        _t1988 = _t1989
    else
        _t1988 = nothing
    end
    relation_id1196 = _t1988
    consume_literal!(parser, "[")
    xs1197 = Proto.var"#Type"[]
    cond1198 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1198
        _t1990 = parse_type(parser)
        item1199 = _t1990
        push!(xs1197, item1199)
        cond1198 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1200 = xs1197
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1991 = Proto.GNFColumn(column_path=gnf_column_path1195, target_id=relation_id1196, types=types1200)
    result1202 = _t1991
    record_span!(parser, span_start1201, "GNFColumn")
    return result1202
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1992 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1993 = 0
        else
            _t1993 = -1
        end
        _t1992 = _t1993
    end
    prediction1203 = _t1992
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
        _t1994 = strings1208
    else
        if prediction1203 == 0
            string1204 = consume_terminal!(parser, "STRING")
            _t1995 = String[string1204]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1994 = _t1995
    end
    return _t1994
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1209 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1209
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1216 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1996 = parse_iceberg_locator(parser)
    iceberg_locator1210 = _t1996
    _t1997 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1211 = _t1997
    _t1998 = parse_gnf_columns(parser)
    gnf_columns1212 = _t1998
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2000 = parse_iceberg_from_snapshot(parser)
        _t1999 = _t2000
    else
        _t1999 = nothing
    end
    iceberg_from_snapshot1213 = _t1999
    if match_lookahead_literal(parser, "(", 0)
        _t2002 = parse_iceberg_to_snapshot(parser)
        _t2001 = _t2002
    else
        _t2001 = nothing
    end
    iceberg_to_snapshot1214 = _t2001
    _t2003 = parse_boolean_value(parser)
    boolean_value1215 = _t2003
    consume_literal!(parser, ")")
    _t2004 = construct_iceberg_data(parser, iceberg_locator1210, iceberg_catalog_config1211, gnf_columns1212, iceberg_from_snapshot1213, iceberg_to_snapshot1214, boolean_value1215)
    result1217 = _t2004
    record_span!(parser, span_start1216, "IcebergData")
    return result1217
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1221 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2005 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1218 = _t2005
    _t2006 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1219 = _t2006
    _t2007 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1220 = _t2007
    consume_literal!(parser, ")")
    _t2008 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1218, namespace=iceberg_locator_namespace1219, warehouse=iceberg_locator_warehouse1220)
    result1222 = _t2008
    record_span!(parser, span_start1221, "IcebergLocator")
    return result1222
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1223 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1223
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1224 = String[]
    cond1225 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1225
        item1226 = consume_terminal!(parser, "STRING")
        push!(xs1224, item1226)
        cond1225 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1227 = xs1224
    consume_literal!(parser, ")")
    return strings1227
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1228 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1228
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1233 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2009 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1229 = _t2009
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2011 = parse_iceberg_catalog_config_scope(parser)
        _t2010 = _t2011
    else
        _t2010 = nothing
    end
    iceberg_catalog_config_scope1230 = _t2010
    _t2012 = parse_iceberg_properties(parser)
    iceberg_properties1231 = _t2012
    _t2013 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1232 = _t2013
    consume_literal!(parser, ")")
    _t2014 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1229, iceberg_catalog_config_scope1230, iceberg_properties1231, iceberg_auth_properties1232)
    result1234 = _t2014
    record_span!(parser, span_start1233, "IcebergCatalogConfig")
    return result1234
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1235 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1235
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1236 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1236
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1237 = Tuple{String, String}[]
    cond1238 = match_lookahead_literal(parser, "(", 0)
    while cond1238
        _t2015 = parse_iceberg_property_entry(parser)
        item1239 = _t2015
        push!(xs1237, item1239)
        cond1238 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1240 = xs1237
    consume_literal!(parser, ")")
    return iceberg_property_entrys1240
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1241 = consume_terminal!(parser, "STRING")
    string_31242 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1241, string_31242,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1243 = Tuple{String, String}[]
    cond1244 = match_lookahead_literal(parser, "(", 0)
    while cond1244
        _t2016 = parse_iceberg_masked_property_entry(parser)
        item1245 = _t2016
        push!(xs1243, item1245)
        cond1244 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1246 = xs1243
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1246
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1247 = consume_terminal!(parser, "STRING")
    string_31248 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1247, string_31248,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1249 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1249
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1250 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1250
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1252 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2017 = parse_fragment_id(parser)
    fragment_id1251 = _t2017
    consume_literal!(parser, ")")
    _t2018 = Proto.Undefine(fragment_id=fragment_id1251)
    result1253 = _t2018
    record_span!(parser, span_start1252, "Undefine")
    return result1253
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1258 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1254 = Proto.RelationId[]
    cond1255 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1255
        _t2019 = parse_relation_id(parser)
        item1256 = _t2019
        push!(xs1254, item1256)
        cond1255 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1257 = xs1254
    consume_literal!(parser, ")")
    _t2020 = Proto.Context(relations=relation_ids1257)
    result1259 = _t2020
    record_span!(parser, span_start1258, "Context")
    return result1259
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1265 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2021 = parse_edb_path(parser)
    edb_path1260 = _t2021
    xs1261 = Proto.SnapshotMapping[]
    cond1262 = match_lookahead_literal(parser, "[", 0)
    while cond1262
        _t2022 = parse_snapshot_mapping(parser)
        item1263 = _t2022
        push!(xs1261, item1263)
        cond1262 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1264 = xs1261
    consume_literal!(parser, ")")
    _t2023 = Proto.Snapshot(mappings=snapshot_mappings1264, prefix=edb_path1260)
    result1266 = _t2023
    record_span!(parser, span_start1265, "Snapshot")
    return result1266
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1269 = span_start(parser)
    _t2024 = parse_edb_path(parser)
    edb_path1267 = _t2024
    _t2025 = parse_relation_id(parser)
    relation_id1268 = _t2025
    _t2026 = Proto.SnapshotMapping(destination_path=edb_path1267, source_relation=relation_id1268)
    result1270 = _t2026
    record_span!(parser, span_start1269, "SnapshotMapping")
    return result1270
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1271 = Proto.Read[]
    cond1272 = match_lookahead_literal(parser, "(", 0)
    while cond1272
        _t2027 = parse_read(parser)
        item1273 = _t2027
        push!(xs1271, item1273)
        cond1272 = match_lookahead_literal(parser, "(", 0)
    end
    reads1274 = xs1271
    consume_literal!(parser, ")")
    return reads1274
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1282 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2029 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2030 = 1
            else
                if match_lookahead_literal(parser, "export_output", 1)
                    _t2031 = 5
                else
                    if match_lookahead_literal(parser, "export_iceberg", 1)
                        _t2032 = 4
                    else
                        if match_lookahead_literal(parser, "export", 1)
                            _t2033 = 4
                        else
                            if match_lookahead_literal(parser, "demand", 1)
                                _t2034 = 0
                            else
                                if match_lookahead_literal(parser, "abort", 1)
                                    _t2035 = 3
                                else
                                    _t2035 = -1
                                end
                                _t2034 = _t2035
                            end
                            _t2033 = _t2034
                        end
                        _t2032 = _t2033
                    end
                    _t2031 = _t2032
                end
                _t2030 = _t2031
            end
            _t2029 = _t2030
        end
        _t2028 = _t2029
    else
        _t2028 = -1
    end
    prediction1275 = _t2028
    if prediction1275 == 5
        _t2037 = parse_export_output(parser)
        export_output1281 = _t2037
        _t2038 = Proto.Read(read_type=OneOf(:export_output, export_output1281))
        _t2036 = _t2038
    else
        if prediction1275 == 4
            _t2040 = parse_export(parser)
            export1280 = _t2040
            _t2041 = Proto.Read(read_type=OneOf(:var"#export", export1280))
            _t2039 = _t2041
        else
            if prediction1275 == 3
                _t2043 = parse_abort(parser)
                abort1279 = _t2043
                _t2044 = Proto.Read(read_type=OneOf(:abort, abort1279))
                _t2042 = _t2044
            else
                if prediction1275 == 2
                    _t2046 = parse_what_if(parser)
                    what_if1278 = _t2046
                    _t2047 = Proto.Read(read_type=OneOf(:what_if, what_if1278))
                    _t2045 = _t2047
                else
                    if prediction1275 == 1
                        _t2049 = parse_output(parser)
                        output1277 = _t2049
                        _t2050 = Proto.Read(read_type=OneOf(:output, output1277))
                        _t2048 = _t2050
                    else
                        if prediction1275 == 0
                            _t2052 = parse_demand(parser)
                            demand1276 = _t2052
                            _t2053 = Proto.Read(read_type=OneOf(:demand, demand1276))
                            _t2051 = _t2053
                        else
                            throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                        end
                        _t2048 = _t2051
                    end
                    _t2045 = _t2048
                end
                _t2042 = _t2045
            end
            _t2039 = _t2042
        end
        _t2036 = _t2039
    end
    result1283 = _t2036
    record_span!(parser, span_start1282, "Read")
    return result1283
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1285 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2054 = parse_relation_id(parser)
    relation_id1284 = _t2054
    consume_literal!(parser, ")")
    _t2055 = Proto.Demand(relation_id=relation_id1284)
    result1286 = _t2055
    record_span!(parser, span_start1285, "Demand")
    return result1286
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1289 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2056 = parse_name(parser)
    name1287 = _t2056
    _t2057 = parse_relation_id(parser)
    relation_id1288 = _t2057
    consume_literal!(parser, ")")
    _t2058 = Proto.Output(name=name1287, relation_id=relation_id1288)
    result1290 = _t2058
    record_span!(parser, span_start1289, "Output")
    return result1290
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1293 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2059 = parse_name(parser)
    name1291 = _t2059
    _t2060 = parse_epoch(parser)
    epoch1292 = _t2060
    consume_literal!(parser, ")")
    _t2061 = Proto.WhatIf(branch=name1291, epoch=epoch1292)
    result1294 = _t2061
    record_span!(parser, span_start1293, "WhatIf")
    return result1294
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1297 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2063 = parse_name(parser)
        _t2062 = _t2063
    else
        _t2062 = nothing
    end
    name1295 = _t2062
    _t2064 = parse_relation_id(parser)
    relation_id1296 = _t2064
    consume_literal!(parser, ")")
    _t2065 = Proto.Abort(name=(!isnothing(name1295) ? name1295 : "abort"), relation_id=relation_id1296)
    result1298 = _t2065
    record_span!(parser, span_start1297, "Abort")
    return result1298
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1302 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2067 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2068 = 0
            else
                _t2068 = -1
            end
            _t2067 = _t2068
        end
        _t2066 = _t2067
    else
        _t2066 = -1
    end
    prediction1299 = _t2066
    if prediction1299 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2070 = parse_export_iceberg_config(parser)
        export_iceberg_config1301 = _t2070
        consume_literal!(parser, ")")
        _t2071 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1301))
        _t2069 = _t2071
    else
        if prediction1299 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2073 = parse_export_csv_config(parser)
            export_csv_config1300 = _t2073
            consume_literal!(parser, ")")
            _t2074 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1300))
            _t2072 = _t2074
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2069 = _t2072
    end
    result1303 = _t2069
    record_span!(parser, span_start1302, "Export")
    return result1303
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1311 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2076 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2077 = 1
            else
                _t2077 = -1
            end
            _t2076 = _t2077
        end
        _t2075 = _t2076
    else
        _t2075 = -1
    end
    prediction1304 = _t2075
    if prediction1304 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2079 = parse_export_csv_path(parser)
        export_csv_path1308 = _t2079
        _t2080 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1309 = _t2080
        _t2081 = parse_config_dict(parser)
        config_dict1310 = _t2081
        consume_literal!(parser, ")")
        _t2082 = construct_export_csv_config(parser, export_csv_path1308, export_csv_columns_list1309, config_dict1310)
        _t2078 = _t2082
    else
        if prediction1304 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2084 = parse_export_csv_path(parser)
            export_csv_path1305 = _t2084
            _t2085 = parse_export_csv_source(parser)
            export_csv_source1306 = _t2085
            _t2086 = parse_csv_config(parser)
            csv_config1307 = _t2086
            consume_literal!(parser, ")")
            _t2087 = construct_export_csv_config_with_source(parser, export_csv_path1305, export_csv_source1306, csv_config1307)
            _t2083 = _t2087
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2078 = _t2083
    end
    result1312 = _t2078
    record_span!(parser, span_start1311, "ExportCSVConfig")
    return result1312
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1313 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1313
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1320 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2089 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2090 = 0
            else
                _t2090 = -1
            end
            _t2089 = _t2090
        end
        _t2088 = _t2089
    else
        _t2088 = -1
    end
    prediction1314 = _t2088
    if prediction1314 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2092 = parse_relation_id(parser)
        relation_id1319 = _t2092
        consume_literal!(parser, ")")
        _t2093 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1319))
        _t2091 = _t2093
    else
        if prediction1314 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1315 = Proto.ExportCSVColumn[]
            cond1316 = match_lookahead_literal(parser, "(", 0)
            while cond1316
                _t2095 = parse_export_csv_column(parser)
                item1317 = _t2095
                push!(xs1315, item1317)
                cond1316 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1318 = xs1315
            consume_literal!(parser, ")")
            _t2096 = Proto.ExportCSVColumns(columns=export_csv_columns1318)
            _t2097 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2096))
            _t2094 = _t2097
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2091 = _t2094
    end
    result1321 = _t2091
    record_span!(parser, span_start1320, "ExportCSVSource")
    return result1321
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1324 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1322 = consume_terminal!(parser, "STRING")
    _t2098 = parse_relation_id(parser)
    relation_id1323 = _t2098
    consume_literal!(parser, ")")
    _t2099 = Proto.ExportCSVColumn(column_name=string1322, column_data=relation_id1323)
    result1325 = _t2099
    record_span!(parser, span_start1324, "ExportCSVColumn")
    return result1325
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1326 = Proto.ExportCSVColumn[]
    cond1327 = match_lookahead_literal(parser, "(", 0)
    while cond1327
        _t2100 = parse_export_csv_column(parser)
        item1328 = _t2100
        push!(xs1326, item1328)
        cond1327 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1329 = xs1326
    consume_literal!(parser, ")")
    return export_csv_columns1329
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1335 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2101 = parse_iceberg_locator(parser)
    iceberg_locator1330 = _t2101
    _t2102 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1331 = _t2102
    _t2103 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1332 = _t2103
    _t2104 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1333 = _t2104
    if match_lookahead_literal(parser, "{", 0)
        _t2106 = parse_config_dict(parser)
        _t2105 = _t2106
    else
        _t2105 = nothing
    end
    config_dict1334 = _t2105
    consume_literal!(parser, ")")
    _t2107 = construct_export_iceberg_config_full(parser, iceberg_locator1330, iceberg_catalog_config1331, export_iceberg_table_def1332, iceberg_table_properties1333, config_dict1334)
    result1336 = _t2107
    record_span!(parser, span_start1335, "ExportIcebergConfig")
    return result1336
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1338 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2108 = parse_relation_id(parser)
    relation_id1337 = _t2108
    consume_literal!(parser, ")")
    result1339 = relation_id1337
    record_span!(parser, span_start1338, "RelationId")
    return result1339
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1340 = Tuple{String, String}[]
    cond1341 = match_lookahead_literal(parser, "(", 0)
    while cond1341
        _t2109 = parse_iceberg_property_entry(parser)
        item1342 = _t2109
        push!(xs1340, item1342)
        cond1341 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1343 = xs1340
    consume_literal!(parser, ")")
    return iceberg_property_entrys1343
end

function parse_export_output(parser::ParserState)::Proto.ExportOutput
    span_start1346 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_output")
    _t2110 = parse_name(parser)
    name1344 = _t2110
    _t2111 = parse_export_csv_output(parser)
    export_csv_output1345 = _t2111
    consume_literal!(parser, ")")
    _t2112 = Proto.ExportOutput(export_output=OneOf(:csv, export_csv_output1345), name=name1344)
    result1347 = _t2112
    record_span!(parser, span_start1346, "ExportOutput")
    return result1347
end

function parse_export_csv_output(parser::ParserState)::Proto.ExportCSVOutput
    span_start1350 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv")
    _t2113 = parse_export_csv_source(parser)
    export_csv_source1348 = _t2113
    _t2114 = parse_csv_config(parser)
    csv_config1349 = _t2114
    consume_literal!(parser, ")")
    _t2115 = Proto.ExportCSVOutput(csv_source=export_csv_source1348, csv_config=csv_config1349)
    result1351 = _t2115
    record_span!(parser, span_start1350, "ExportCSVOutput")
    return result1351
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
