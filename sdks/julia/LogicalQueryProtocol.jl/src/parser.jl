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
        _t2113 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2114 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2115 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2116 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2117 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2118 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2119 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2120 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2121 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2122 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2122
    _t2123 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2123
    _t2124 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2124
    _t2125 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2125
    _t2126 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2126
    _t2127 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2127
    _t2128 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2128
    _t2129 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2129
    _t2130 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2130
    _t2131 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2131
    _t2132 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2132
    _t2133 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2133
    _t2134 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2134
    _t2135 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2135
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2136 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2137 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2138 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2139 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2140 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2141 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2142 = Proto.StorageIntegration(provider=_t2137, azure_sas_token=_t2138, s3_region=_t2139, s3_access_key_id=_t2140, s3_secret_access_key=_t2141)
    return _t2142
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2143 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2143
    _t2144 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2144
    _t2145 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2145
    _t2146 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2146
    _t2147 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2147
    _t2148 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2148
    _t2149 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2149
    _t2150 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2150
    _t2151 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2151
    _t2152 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2152
    _t2153 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2153
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2154 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2154
    _t2155 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2155
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
    _t2156 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2156
    _t2157 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2157
    _t2158 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2158
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2159 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2159
    _t2160 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2160
    _t2161 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2161
    _t2162 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2162
    _t2163 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2163
    _t2164 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2164
    _t2165 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2165
    _t2166 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2166
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2167 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2167
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2168 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2168
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2169 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2169
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2170 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2170
    _t2171 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2171
    _t2172 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2172
    table_props = Dict(table_property_pairs)
    _t2173 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2173
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start681 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1351 = parse_configure(parser)
        _t1350 = _t1351
    else
        _t1350 = nothing
    end
    configure675 = _t1350
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1353 = parse_sync(parser)
        _t1352 = _t1353
    else
        _t1352 = nothing
    end
    sync676 = _t1352
    xs677 = Proto.Epoch[]
    cond678 = match_lookahead_literal(parser, "(", 0)
    while cond678
        _t1354 = parse_epoch(parser)
        item679 = _t1354
        push!(xs677, item679)
        cond678 = match_lookahead_literal(parser, "(", 0)
    end
    epochs680 = xs677
    consume_literal!(parser, ")")
    _t1355 = default_configure(parser)
    _t1356 = Proto.Transaction(epochs=epochs680, configure=(!isnothing(configure675) ? configure675 : _t1355), sync=sync676)
    result682 = _t1356
    record_span!(parser, span_start681, "Transaction")
    return result682
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start684 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1357 = parse_config_dict(parser)
    config_dict683 = _t1357
    consume_literal!(parser, ")")
    _t1358 = construct_configure(parser, config_dict683)
    result685 = _t1358
    record_span!(parser, span_start684, "Configure")
    return result685
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs686 = Tuple{String, Proto.Value}[]
    cond687 = match_lookahead_literal(parser, ":", 0)
    while cond687
        _t1359 = parse_config_key_value(parser)
        item688 = _t1359
        push!(xs686, item688)
        cond687 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values689 = xs686
    consume_literal!(parser, "}")
    return config_key_values689
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol690 = consume_terminal!(parser, "SYMBOL")
    _t1360 = parse_raw_value(parser)
    raw_value691 = _t1360
    return (symbol690, raw_value691,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start705 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1361 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1362 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1363 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1365 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1366 = 0
                        else
                            _t1366 = -1
                        end
                        _t1365 = _t1366
                    end
                    _t1364 = _t1365
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1367 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1368 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1369 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1370 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1371 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1372 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1373 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1374 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1375 = 10
                                                    else
                                                        _t1375 = -1
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
                            _t1368 = _t1369
                        end
                        _t1367 = _t1368
                    end
                    _t1364 = _t1367
                end
                _t1363 = _t1364
            end
            _t1362 = _t1363
        end
        _t1361 = _t1362
    end
    prediction692 = _t1361
    if prediction692 == 12
        _t1377 = parse_boolean_value(parser)
        boolean_value704 = _t1377
        _t1378 = Proto.Value(value=OneOf(:boolean_value, boolean_value704))
        _t1376 = _t1378
    else
        if prediction692 == 11
            consume_literal!(parser, "missing")
            _t1380 = Proto.MissingValue()
            _t1381 = Proto.Value(value=OneOf(:missing_value, _t1380))
            _t1379 = _t1381
        else
            if prediction692 == 10
                decimal703 = consume_terminal!(parser, "DECIMAL")
                _t1383 = Proto.Value(value=OneOf(:decimal_value, decimal703))
                _t1382 = _t1383
            else
                if prediction692 == 9
                    int128702 = consume_terminal!(parser, "INT128")
                    _t1385 = Proto.Value(value=OneOf(:int128_value, int128702))
                    _t1384 = _t1385
                else
                    if prediction692 == 8
                        uint128701 = consume_terminal!(parser, "UINT128")
                        _t1387 = Proto.Value(value=OneOf(:uint128_value, uint128701))
                        _t1386 = _t1387
                    else
                        if prediction692 == 7
                            uint32700 = consume_terminal!(parser, "UINT32")
                            _t1389 = Proto.Value(value=OneOf(:uint32_value, uint32700))
                            _t1388 = _t1389
                        else
                            if prediction692 == 6
                                float699 = consume_terminal!(parser, "FLOAT")
                                _t1391 = Proto.Value(value=OneOf(:float_value, float699))
                                _t1390 = _t1391
                            else
                                if prediction692 == 5
                                    float32698 = consume_terminal!(parser, "FLOAT32")
                                    _t1393 = Proto.Value(value=OneOf(:float32_value, float32698))
                                    _t1392 = _t1393
                                else
                                    if prediction692 == 4
                                        int697 = consume_terminal!(parser, "INT")
                                        _t1395 = Proto.Value(value=OneOf(:int_value, int697))
                                        _t1394 = _t1395
                                    else
                                        if prediction692 == 3
                                            int32696 = consume_terminal!(parser, "INT32")
                                            _t1397 = Proto.Value(value=OneOf(:int32_value, int32696))
                                            _t1396 = _t1397
                                        else
                                            if prediction692 == 2
                                                string695 = consume_terminal!(parser, "STRING")
                                                _t1399 = Proto.Value(value=OneOf(:string_value, string695))
                                                _t1398 = _t1399
                                            else
                                                if prediction692 == 1
                                                    _t1401 = parse_raw_datetime(parser)
                                                    raw_datetime694 = _t1401
                                                    _t1402 = Proto.Value(value=OneOf(:datetime_value, raw_datetime694))
                                                    _t1400 = _t1402
                                                else
                                                    if prediction692 == 0
                                                        _t1404 = parse_raw_date(parser)
                                                        raw_date693 = _t1404
                                                        _t1405 = Proto.Value(value=OneOf(:date_value, raw_date693))
                                                        _t1403 = _t1405
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1400 = _t1403
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
                _t1382 = _t1384
            end
            _t1379 = _t1382
        end
        _t1376 = _t1379
    end
    result706 = _t1376
    record_span!(parser, span_start705, "Value")
    return result706
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start710 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int707 = consume_terminal!(parser, "INT")
    int_3708 = consume_terminal!(parser, "INT")
    int_4709 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1406 = Proto.DateValue(year=Int32(int707), month=Int32(int_3708), day=Int32(int_4709))
    result711 = _t1406
    record_span!(parser, span_start710, "DateValue")
    return result711
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start719 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int712 = consume_terminal!(parser, "INT")
    int_3713 = consume_terminal!(parser, "INT")
    int_4714 = consume_terminal!(parser, "INT")
    int_5715 = consume_terminal!(parser, "INT")
    int_6716 = consume_terminal!(parser, "INT")
    int_7717 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1407 = consume_terminal!(parser, "INT")
    else
        _t1407 = nothing
    end
    int_8718 = _t1407
    consume_literal!(parser, ")")
    _t1408 = Proto.DateTimeValue(year=Int32(int712), month=Int32(int_3713), day=Int32(int_4714), hour=Int32(int_5715), minute=Int32(int_6716), second=Int32(int_7717), microsecond=Int32((!isnothing(int_8718) ? int_8718 : 0)))
    result720 = _t1408
    record_span!(parser, span_start719, "DateTimeValue")
    return result720
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1409 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1410 = 1
        else
            _t1410 = -1
        end
        _t1409 = _t1410
    end
    prediction721 = _t1409
    if prediction721 == 1
        consume_literal!(parser, "false")
        _t1411 = false
    else
        if prediction721 == 0
            consume_literal!(parser, "true")
            _t1412 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1411 = _t1412
    end
    return _t1411
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start726 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs722 = Proto.FragmentId[]
    cond723 = match_lookahead_literal(parser, ":", 0)
    while cond723
        _t1413 = parse_fragment_id(parser)
        item724 = _t1413
        push!(xs722, item724)
        cond723 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids725 = xs722
    consume_literal!(parser, ")")
    _t1414 = Proto.Sync(fragments=fragment_ids725)
    result727 = _t1414
    record_span!(parser, span_start726, "Sync")
    return result727
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start729 = span_start(parser)
    consume_literal!(parser, ":")
    symbol728 = consume_terminal!(parser, "SYMBOL")
    result730 = Proto.FragmentId(Vector{UInt8}(symbol728))
    record_span!(parser, span_start729, "FragmentId")
    return result730
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start733 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1416 = parse_epoch_writes(parser)
        _t1415 = _t1416
    else
        _t1415 = nothing
    end
    epoch_writes731 = _t1415
    if match_lookahead_literal(parser, "(", 0)
        _t1418 = parse_epoch_reads(parser)
        _t1417 = _t1418
    else
        _t1417 = nothing
    end
    epoch_reads732 = _t1417
    consume_literal!(parser, ")")
    _t1419 = Proto.Epoch(writes=(!isnothing(epoch_writes731) ? epoch_writes731 : Proto.Write[]), reads=(!isnothing(epoch_reads732) ? epoch_reads732 : Proto.Read[]))
    result734 = _t1419
    record_span!(parser, span_start733, "Epoch")
    return result734
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs735 = Proto.Write[]
    cond736 = match_lookahead_literal(parser, "(", 0)
    while cond736
        _t1420 = parse_write(parser)
        item737 = _t1420
        push!(xs735, item737)
        cond736 = match_lookahead_literal(parser, "(", 0)
    end
    writes738 = xs735
    consume_literal!(parser, ")")
    return writes738
end

function parse_write(parser::ParserState)::Proto.Write
    span_start744 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1422 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1423 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1424 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1425 = 2
                    else
                        _t1425 = -1
                    end
                    _t1424 = _t1425
                end
                _t1423 = _t1424
            end
            _t1422 = _t1423
        end
        _t1421 = _t1422
    else
        _t1421 = -1
    end
    prediction739 = _t1421
    if prediction739 == 3
        _t1427 = parse_snapshot(parser)
        snapshot743 = _t1427
        _t1428 = Proto.Write(write_type=OneOf(:snapshot, snapshot743))
        _t1426 = _t1428
    else
        if prediction739 == 2
            _t1430 = parse_context(parser)
            context742 = _t1430
            _t1431 = Proto.Write(write_type=OneOf(:context, context742))
            _t1429 = _t1431
        else
            if prediction739 == 1
                _t1433 = parse_undefine(parser)
                undefine741 = _t1433
                _t1434 = Proto.Write(write_type=OneOf(:undefine, undefine741))
                _t1432 = _t1434
            else
                if prediction739 == 0
                    _t1436 = parse_define(parser)
                    define740 = _t1436
                    _t1437 = Proto.Write(write_type=OneOf(:define, define740))
                    _t1435 = _t1437
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1432 = _t1435
            end
            _t1429 = _t1432
        end
        _t1426 = _t1429
    end
    result745 = _t1426
    record_span!(parser, span_start744, "Write")
    return result745
end

function parse_define(parser::ParserState)::Proto.Define
    span_start747 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1438 = parse_fragment(parser)
    fragment746 = _t1438
    consume_literal!(parser, ")")
    _t1439 = Proto.Define(fragment=fragment746)
    result748 = _t1439
    record_span!(parser, span_start747, "Define")
    return result748
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start754 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1440 = parse_new_fragment_id(parser)
    new_fragment_id749 = _t1440
    xs750 = Proto.Declaration[]
    cond751 = match_lookahead_literal(parser, "(", 0)
    while cond751
        _t1441 = parse_declaration(parser)
        item752 = _t1441
        push!(xs750, item752)
        cond751 = match_lookahead_literal(parser, "(", 0)
    end
    declarations753 = xs750
    consume_literal!(parser, ")")
    result755 = construct_fragment(parser, new_fragment_id749, declarations753)
    record_span!(parser, span_start754, "Fragment")
    return result755
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start757 = span_start(parser)
    _t1442 = parse_fragment_id(parser)
    fragment_id756 = _t1442
    start_fragment!(parser, fragment_id756)
    result758 = fragment_id756
    record_span!(parser, span_start757, "FragmentId")
    return result758
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start764 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1444 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1445 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1446 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1447 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1448 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1449 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1450 = 1
                                else
                                    _t1450 = -1
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
    else
        _t1443 = -1
    end
    prediction759 = _t1443
    if prediction759 == 3
        _t1452 = parse_data(parser)
        data763 = _t1452
        _t1453 = Proto.Declaration(declaration_type=OneOf(:data, data763))
        _t1451 = _t1453
    else
        if prediction759 == 2
            _t1455 = parse_constraint(parser)
            constraint762 = _t1455
            _t1456 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint762))
            _t1454 = _t1456
        else
            if prediction759 == 1
                _t1458 = parse_algorithm(parser)
                algorithm761 = _t1458
                _t1459 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm761))
                _t1457 = _t1459
            else
                if prediction759 == 0
                    _t1461 = parse_def(parser)
                    def760 = _t1461
                    _t1462 = Proto.Declaration(declaration_type=OneOf(:def, def760))
                    _t1460 = _t1462
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1457 = _t1460
            end
            _t1454 = _t1457
        end
        _t1451 = _t1454
    end
    result765 = _t1451
    record_span!(parser, span_start764, "Declaration")
    return result765
end

function parse_def(parser::ParserState)::Proto.Def
    span_start769 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1463 = parse_relation_id(parser)
    relation_id766 = _t1463
    _t1464 = parse_abstraction(parser)
    abstraction767 = _t1464
    if match_lookahead_literal(parser, "(", 0)
        _t1466 = parse_attrs(parser)
        _t1465 = _t1466
    else
        _t1465 = nothing
    end
    attrs768 = _t1465
    consume_literal!(parser, ")")
    _t1467 = Proto.Def(name=relation_id766, body=abstraction767, attrs=(!isnothing(attrs768) ? attrs768 : Proto.Attribute[]))
    result770 = _t1467
    record_span!(parser, span_start769, "Def")
    return result770
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start774 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1468 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1469 = 1
        else
            _t1469 = -1
        end
        _t1468 = _t1469
    end
    prediction771 = _t1468
    if prediction771 == 1
        uint128773 = consume_terminal!(parser, "UINT128")
        _t1470 = Proto.RelationId(uint128773.low, uint128773.high)
    else
        if prediction771 == 0
            consume_literal!(parser, ":")
            symbol772 = consume_terminal!(parser, "SYMBOL")
            _t1471 = relation_id_from_string(parser, symbol772)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1470 = _t1471
    end
    result775 = _t1470
    record_span!(parser, span_start774, "RelationId")
    return result775
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start778 = span_start(parser)
    consume_literal!(parser, "(")
    _t1472 = parse_bindings(parser)
    bindings776 = _t1472
    _t1473 = parse_formula(parser)
    formula777 = _t1473
    consume_literal!(parser, ")")
    _t1474 = Proto.Abstraction(vars=vcat(bindings776[1], !isnothing(bindings776[2]) ? bindings776[2] : []), value=formula777)
    result779 = _t1474
    record_span!(parser, span_start778, "Abstraction")
    return result779
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs780 = Proto.Binding[]
    cond781 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond781
        _t1475 = parse_binding(parser)
        item782 = _t1475
        push!(xs780, item782)
        cond781 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings783 = xs780
    if match_lookahead_literal(parser, "|", 0)
        _t1477 = parse_value_bindings(parser)
        _t1476 = _t1477
    else
        _t1476 = nothing
    end
    value_bindings784 = _t1476
    consume_literal!(parser, "]")
    return (bindings783, (!isnothing(value_bindings784) ? value_bindings784 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start787 = span_start(parser)
    symbol785 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1478 = parse_type(parser)
    type786 = _t1478
    _t1479 = Proto.Var(name=symbol785)
    _t1480 = Proto.Binding(var=_t1479, var"#type"=type786)
    result788 = _t1480
    record_span!(parser, span_start787, "Binding")
    return result788
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start804 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1481 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1482 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1483 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1484 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1485 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1486 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1487 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1488 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1489 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1490 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1491 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1492 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1493 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1494 = 9
                                                        else
                                                            _t1494 = -1
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
            _t1482 = _t1483
        end
        _t1481 = _t1482
    end
    prediction789 = _t1481
    if prediction789 == 13
        _t1496 = parse_uint32_type(parser)
        uint32_type803 = _t1496
        _t1497 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type803))
        _t1495 = _t1497
    else
        if prediction789 == 12
            _t1499 = parse_float32_type(parser)
            float32_type802 = _t1499
            _t1500 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type802))
            _t1498 = _t1500
        else
            if prediction789 == 11
                _t1502 = parse_int32_type(parser)
                int32_type801 = _t1502
                _t1503 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type801))
                _t1501 = _t1503
            else
                if prediction789 == 10
                    _t1505 = parse_boolean_type(parser)
                    boolean_type800 = _t1505
                    _t1506 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type800))
                    _t1504 = _t1506
                else
                    if prediction789 == 9
                        _t1508 = parse_decimal_type(parser)
                        decimal_type799 = _t1508
                        _t1509 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type799))
                        _t1507 = _t1509
                    else
                        if prediction789 == 8
                            _t1511 = parse_missing_type(parser)
                            missing_type798 = _t1511
                            _t1512 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type798))
                            _t1510 = _t1512
                        else
                            if prediction789 == 7
                                _t1514 = parse_datetime_type(parser)
                                datetime_type797 = _t1514
                                _t1515 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type797))
                                _t1513 = _t1515
                            else
                                if prediction789 == 6
                                    _t1517 = parse_date_type(parser)
                                    date_type796 = _t1517
                                    _t1518 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type796))
                                    _t1516 = _t1518
                                else
                                    if prediction789 == 5
                                        _t1520 = parse_int128_type(parser)
                                        int128_type795 = _t1520
                                        _t1521 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type795))
                                        _t1519 = _t1521
                                    else
                                        if prediction789 == 4
                                            _t1523 = parse_uint128_type(parser)
                                            uint128_type794 = _t1523
                                            _t1524 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type794))
                                            _t1522 = _t1524
                                        else
                                            if prediction789 == 3
                                                _t1526 = parse_float_type(parser)
                                                float_type793 = _t1526
                                                _t1527 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type793))
                                                _t1525 = _t1527
                                            else
                                                if prediction789 == 2
                                                    _t1529 = parse_int_type(parser)
                                                    int_type792 = _t1529
                                                    _t1530 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type792))
                                                    _t1528 = _t1530
                                                else
                                                    if prediction789 == 1
                                                        _t1532 = parse_string_type(parser)
                                                        string_type791 = _t1532
                                                        _t1533 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type791))
                                                        _t1531 = _t1533
                                                    else
                                                        if prediction789 == 0
                                                            _t1535 = parse_unspecified_type(parser)
                                                            unspecified_type790 = _t1535
                                                            _t1536 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type790))
                                                            _t1534 = _t1536
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1531 = _t1534
                                                    end
                                                    _t1528 = _t1531
                                                end
                                                _t1525 = _t1528
                                            end
                                            _t1522 = _t1525
                                        end
                                        _t1519 = _t1522
                                    end
                                    _t1516 = _t1519
                                end
                                _t1513 = _t1516
                            end
                            _t1510 = _t1513
                        end
                        _t1507 = _t1510
                    end
                    _t1504 = _t1507
                end
                _t1501 = _t1504
            end
            _t1498 = _t1501
        end
        _t1495 = _t1498
    end
    result805 = _t1495
    record_span!(parser, span_start804, "Type")
    return result805
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start806 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1537 = Proto.UnspecifiedType()
    result807 = _t1537
    record_span!(parser, span_start806, "UnspecifiedType")
    return result807
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start808 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1538 = Proto.StringType()
    result809 = _t1538
    record_span!(parser, span_start808, "StringType")
    return result809
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start810 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1539 = Proto.IntType()
    result811 = _t1539
    record_span!(parser, span_start810, "IntType")
    return result811
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start812 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1540 = Proto.FloatType()
    result813 = _t1540
    record_span!(parser, span_start812, "FloatType")
    return result813
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start814 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1541 = Proto.UInt128Type()
    result815 = _t1541
    record_span!(parser, span_start814, "UInt128Type")
    return result815
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start816 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1542 = Proto.Int128Type()
    result817 = _t1542
    record_span!(parser, span_start816, "Int128Type")
    return result817
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start818 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1543 = Proto.DateType()
    result819 = _t1543
    record_span!(parser, span_start818, "DateType")
    return result819
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start820 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1544 = Proto.DateTimeType()
    result821 = _t1544
    record_span!(parser, span_start820, "DateTimeType")
    return result821
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start822 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1545 = Proto.MissingType()
    result823 = _t1545
    record_span!(parser, span_start822, "MissingType")
    return result823
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start826 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int824 = consume_terminal!(parser, "INT")
    int_3825 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1546 = Proto.DecimalType(precision=Int32(int824), scale=Int32(int_3825))
    result827 = _t1546
    record_span!(parser, span_start826, "DecimalType")
    return result827
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start828 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1547 = Proto.BooleanType()
    result829 = _t1547
    record_span!(parser, span_start828, "BooleanType")
    return result829
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start830 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1548 = Proto.Int32Type()
    result831 = _t1548
    record_span!(parser, span_start830, "Int32Type")
    return result831
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start832 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1549 = Proto.Float32Type()
    result833 = _t1549
    record_span!(parser, span_start832, "Float32Type")
    return result833
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start834 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1550 = Proto.UInt32Type()
    result835 = _t1550
    record_span!(parser, span_start834, "UInt32Type")
    return result835
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs836 = Proto.Binding[]
    cond837 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond837
        _t1551 = parse_binding(parser)
        item838 = _t1551
        push!(xs836, item838)
        cond837 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings839 = xs836
    return bindings839
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start854 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1553 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1554 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1555 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1556 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1557 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1558 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1559 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1560 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1561 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1562 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1563 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1564 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1565 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1566 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1567 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1568 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1569 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1570 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1571 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1572 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1573 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1574 = 10
                                                                                            else
                                                                                                _t1574 = -1
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
            end
            _t1553 = _t1554
        end
        _t1552 = _t1553
    else
        _t1552 = -1
    end
    prediction840 = _t1552
    if prediction840 == 12
        _t1576 = parse_cast(parser)
        cast853 = _t1576
        _t1577 = Proto.Formula(formula_type=OneOf(:cast, cast853))
        _t1575 = _t1577
    else
        if prediction840 == 11
            _t1579 = parse_rel_atom(parser)
            rel_atom852 = _t1579
            _t1580 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom852))
            _t1578 = _t1580
        else
            if prediction840 == 10
                _t1582 = parse_primitive(parser)
                primitive851 = _t1582
                _t1583 = Proto.Formula(formula_type=OneOf(:primitive, primitive851))
                _t1581 = _t1583
            else
                if prediction840 == 9
                    _t1585 = parse_pragma(parser)
                    pragma850 = _t1585
                    _t1586 = Proto.Formula(formula_type=OneOf(:pragma, pragma850))
                    _t1584 = _t1586
                else
                    if prediction840 == 8
                        _t1588 = parse_atom(parser)
                        atom849 = _t1588
                        _t1589 = Proto.Formula(formula_type=OneOf(:atom, atom849))
                        _t1587 = _t1589
                    else
                        if prediction840 == 7
                            _t1591 = parse_ffi(parser)
                            ffi848 = _t1591
                            _t1592 = Proto.Formula(formula_type=OneOf(:ffi, ffi848))
                            _t1590 = _t1592
                        else
                            if prediction840 == 6
                                _t1594 = parse_not(parser)
                                not847 = _t1594
                                _t1595 = Proto.Formula(formula_type=OneOf(:not, not847))
                                _t1593 = _t1595
                            else
                                if prediction840 == 5
                                    _t1597 = parse_disjunction(parser)
                                    disjunction846 = _t1597
                                    _t1598 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction846))
                                    _t1596 = _t1598
                                else
                                    if prediction840 == 4
                                        _t1600 = parse_conjunction(parser)
                                        conjunction845 = _t1600
                                        _t1601 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction845))
                                        _t1599 = _t1601
                                    else
                                        if prediction840 == 3
                                            _t1603 = parse_reduce(parser)
                                            reduce844 = _t1603
                                            _t1604 = Proto.Formula(formula_type=OneOf(:reduce, reduce844))
                                            _t1602 = _t1604
                                        else
                                            if prediction840 == 2
                                                _t1606 = parse_exists(parser)
                                                exists843 = _t1606
                                                _t1607 = Proto.Formula(formula_type=OneOf(:exists, exists843))
                                                _t1605 = _t1607
                                            else
                                                if prediction840 == 1
                                                    _t1609 = parse_false(parser)
                                                    false842 = _t1609
                                                    _t1610 = Proto.Formula(formula_type=OneOf(:disjunction, false842))
                                                    _t1608 = _t1610
                                                else
                                                    if prediction840 == 0
                                                        _t1612 = parse_true(parser)
                                                        true841 = _t1612
                                                        _t1613 = Proto.Formula(formula_type=OneOf(:conjunction, true841))
                                                        _t1611 = _t1613
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1608 = _t1611
                                                end
                                                _t1605 = _t1608
                                            end
                                            _t1602 = _t1605
                                        end
                                        _t1599 = _t1602
                                    end
                                    _t1596 = _t1599
                                end
                                _t1593 = _t1596
                            end
                            _t1590 = _t1593
                        end
                        _t1587 = _t1590
                    end
                    _t1584 = _t1587
                end
                _t1581 = _t1584
            end
            _t1578 = _t1581
        end
        _t1575 = _t1578
    end
    result855 = _t1575
    record_span!(parser, span_start854, "Formula")
    return result855
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start856 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1614 = Proto.Conjunction(args=Proto.Formula[])
    result857 = _t1614
    record_span!(parser, span_start856, "Conjunction")
    return result857
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start858 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1615 = Proto.Disjunction(args=Proto.Formula[])
    result859 = _t1615
    record_span!(parser, span_start858, "Disjunction")
    return result859
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start862 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1616 = parse_bindings(parser)
    bindings860 = _t1616
    _t1617 = parse_formula(parser)
    formula861 = _t1617
    consume_literal!(parser, ")")
    _t1618 = Proto.Abstraction(vars=vcat(bindings860[1], !isnothing(bindings860[2]) ? bindings860[2] : []), value=formula861)
    _t1619 = Proto.Exists(body=_t1618)
    result863 = _t1619
    record_span!(parser, span_start862, "Exists")
    return result863
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start867 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1620 = parse_abstraction(parser)
    abstraction864 = _t1620
    _t1621 = parse_abstraction(parser)
    abstraction_3865 = _t1621
    _t1622 = parse_terms(parser)
    terms866 = _t1622
    consume_literal!(parser, ")")
    _t1623 = Proto.Reduce(op=abstraction864, body=abstraction_3865, terms=terms866)
    result868 = _t1623
    record_span!(parser, span_start867, "Reduce")
    return result868
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs869 = Proto.Term[]
    cond870 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond870
        _t1624 = parse_term(parser)
        item871 = _t1624
        push!(xs869, item871)
        cond870 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms872 = xs869
    consume_literal!(parser, ")")
    return terms872
end

function parse_term(parser::ParserState)::Proto.Term
    span_start876 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1625 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1626 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1627 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1628 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1629 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1630 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1631 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1632 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1633 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1634 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1635 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1636 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1637 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1638 = 1
                                                        else
                                                            _t1638 = -1
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
            _t1626 = _t1627
        end
        _t1625 = _t1626
    end
    prediction873 = _t1625
    if prediction873 == 1
        _t1640 = parse_value(parser)
        value875 = _t1640
        _t1641 = Proto.Term(term_type=OneOf(:constant, value875))
        _t1639 = _t1641
    else
        if prediction873 == 0
            _t1643 = parse_var(parser)
            var874 = _t1643
            _t1644 = Proto.Term(term_type=OneOf(:var, var874))
            _t1642 = _t1644
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1639 = _t1642
    end
    result877 = _t1639
    record_span!(parser, span_start876, "Term")
    return result877
end

function parse_var(parser::ParserState)::Proto.Var
    span_start879 = span_start(parser)
    symbol878 = consume_terminal!(parser, "SYMBOL")
    _t1645 = Proto.Var(name=symbol878)
    result880 = _t1645
    record_span!(parser, span_start879, "Var")
    return result880
end

function parse_value(parser::ParserState)::Proto.Value
    span_start894 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1646 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1647 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1648 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1650 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1651 = 0
                        else
                            _t1651 = -1
                        end
                        _t1650 = _t1651
                    end
                    _t1649 = _t1650
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1652 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1653 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1654 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1655 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1656 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1657 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1658 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1659 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1660 = 10
                                                    else
                                                        _t1660 = -1
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
                            _t1653 = _t1654
                        end
                        _t1652 = _t1653
                    end
                    _t1649 = _t1652
                end
                _t1648 = _t1649
            end
            _t1647 = _t1648
        end
        _t1646 = _t1647
    end
    prediction881 = _t1646
    if prediction881 == 12
        _t1662 = parse_boolean_value(parser)
        boolean_value893 = _t1662
        _t1663 = Proto.Value(value=OneOf(:boolean_value, boolean_value893))
        _t1661 = _t1663
    else
        if prediction881 == 11
            consume_literal!(parser, "missing")
            _t1665 = Proto.MissingValue()
            _t1666 = Proto.Value(value=OneOf(:missing_value, _t1665))
            _t1664 = _t1666
        else
            if prediction881 == 10
                formatted_decimal892 = consume_terminal!(parser, "DECIMAL")
                _t1668 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal892))
                _t1667 = _t1668
            else
                if prediction881 == 9
                    formatted_int128891 = consume_terminal!(parser, "INT128")
                    _t1670 = Proto.Value(value=OneOf(:int128_value, formatted_int128891))
                    _t1669 = _t1670
                else
                    if prediction881 == 8
                        formatted_uint128890 = consume_terminal!(parser, "UINT128")
                        _t1672 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128890))
                        _t1671 = _t1672
                    else
                        if prediction881 == 7
                            formatted_uint32889 = consume_terminal!(parser, "UINT32")
                            _t1674 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32889))
                            _t1673 = _t1674
                        else
                            if prediction881 == 6
                                formatted_float888 = consume_terminal!(parser, "FLOAT")
                                _t1676 = Proto.Value(value=OneOf(:float_value, formatted_float888))
                                _t1675 = _t1676
                            else
                                if prediction881 == 5
                                    formatted_float32887 = consume_terminal!(parser, "FLOAT32")
                                    _t1678 = Proto.Value(value=OneOf(:float32_value, formatted_float32887))
                                    _t1677 = _t1678
                                else
                                    if prediction881 == 4
                                        formatted_int886 = consume_terminal!(parser, "INT")
                                        _t1680 = Proto.Value(value=OneOf(:int_value, formatted_int886))
                                        _t1679 = _t1680
                                    else
                                        if prediction881 == 3
                                            formatted_int32885 = consume_terminal!(parser, "INT32")
                                            _t1682 = Proto.Value(value=OneOf(:int32_value, formatted_int32885))
                                            _t1681 = _t1682
                                        else
                                            if prediction881 == 2
                                                formatted_string884 = consume_terminal!(parser, "STRING")
                                                _t1684 = Proto.Value(value=OneOf(:string_value, formatted_string884))
                                                _t1683 = _t1684
                                            else
                                                if prediction881 == 1
                                                    _t1686 = parse_datetime(parser)
                                                    datetime883 = _t1686
                                                    _t1687 = Proto.Value(value=OneOf(:datetime_value, datetime883))
                                                    _t1685 = _t1687
                                                else
                                                    if prediction881 == 0
                                                        _t1689 = parse_date(parser)
                                                        date882 = _t1689
                                                        _t1690 = Proto.Value(value=OneOf(:date_value, date882))
                                                        _t1688 = _t1690
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1685 = _t1688
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
                _t1667 = _t1669
            end
            _t1664 = _t1667
        end
        _t1661 = _t1664
    end
    result895 = _t1661
    record_span!(parser, span_start894, "Value")
    return result895
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start899 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int896 = consume_terminal!(parser, "INT")
    formatted_int_3897 = consume_terminal!(parser, "INT")
    formatted_int_4898 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1691 = Proto.DateValue(year=Int32(formatted_int896), month=Int32(formatted_int_3897), day=Int32(formatted_int_4898))
    result900 = _t1691
    record_span!(parser, span_start899, "DateValue")
    return result900
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start908 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int901 = consume_terminal!(parser, "INT")
    formatted_int_3902 = consume_terminal!(parser, "INT")
    formatted_int_4903 = consume_terminal!(parser, "INT")
    formatted_int_5904 = consume_terminal!(parser, "INT")
    formatted_int_6905 = consume_terminal!(parser, "INT")
    formatted_int_7906 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1692 = consume_terminal!(parser, "INT")
    else
        _t1692 = nothing
    end
    formatted_int_8907 = _t1692
    consume_literal!(parser, ")")
    _t1693 = Proto.DateTimeValue(year=Int32(formatted_int901), month=Int32(formatted_int_3902), day=Int32(formatted_int_4903), hour=Int32(formatted_int_5904), minute=Int32(formatted_int_6905), second=Int32(formatted_int_7906), microsecond=Int32((!isnothing(formatted_int_8907) ? formatted_int_8907 : 0)))
    result909 = _t1693
    record_span!(parser, span_start908, "DateTimeValue")
    return result909
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start914 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs910 = Proto.Formula[]
    cond911 = match_lookahead_literal(parser, "(", 0)
    while cond911
        _t1694 = parse_formula(parser)
        item912 = _t1694
        push!(xs910, item912)
        cond911 = match_lookahead_literal(parser, "(", 0)
    end
    formulas913 = xs910
    consume_literal!(parser, ")")
    _t1695 = Proto.Conjunction(args=formulas913)
    result915 = _t1695
    record_span!(parser, span_start914, "Conjunction")
    return result915
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start920 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs916 = Proto.Formula[]
    cond917 = match_lookahead_literal(parser, "(", 0)
    while cond917
        _t1696 = parse_formula(parser)
        item918 = _t1696
        push!(xs916, item918)
        cond917 = match_lookahead_literal(parser, "(", 0)
    end
    formulas919 = xs916
    consume_literal!(parser, ")")
    _t1697 = Proto.Disjunction(args=formulas919)
    result921 = _t1697
    record_span!(parser, span_start920, "Disjunction")
    return result921
end

function parse_not(parser::ParserState)::Proto.Not
    span_start923 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1698 = parse_formula(parser)
    formula922 = _t1698
    consume_literal!(parser, ")")
    _t1699 = Proto.Not(arg=formula922)
    result924 = _t1699
    record_span!(parser, span_start923, "Not")
    return result924
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start928 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1700 = parse_name(parser)
    name925 = _t1700
    _t1701 = parse_ffi_args(parser)
    ffi_args926 = _t1701
    _t1702 = parse_terms(parser)
    terms927 = _t1702
    consume_literal!(parser, ")")
    _t1703 = Proto.FFI(name=name925, args=ffi_args926, terms=terms927)
    result929 = _t1703
    record_span!(parser, span_start928, "FFI")
    return result929
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol930 = consume_terminal!(parser, "SYMBOL")
    return symbol930
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs931 = Proto.Abstraction[]
    cond932 = match_lookahead_literal(parser, "(", 0)
    while cond932
        _t1704 = parse_abstraction(parser)
        item933 = _t1704
        push!(xs931, item933)
        cond932 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions934 = xs931
    consume_literal!(parser, ")")
    return abstractions934
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start940 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1705 = parse_relation_id(parser)
    relation_id935 = _t1705
    xs936 = Proto.Term[]
    cond937 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond937
        _t1706 = parse_term(parser)
        item938 = _t1706
        push!(xs936, item938)
        cond937 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms939 = xs936
    consume_literal!(parser, ")")
    _t1707 = Proto.Atom(name=relation_id935, terms=terms939)
    result941 = _t1707
    record_span!(parser, span_start940, "Atom")
    return result941
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start947 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1708 = parse_name(parser)
    name942 = _t1708
    xs943 = Proto.Term[]
    cond944 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond944
        _t1709 = parse_term(parser)
        item945 = _t1709
        push!(xs943, item945)
        cond944 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms946 = xs943
    consume_literal!(parser, ")")
    _t1710 = Proto.Pragma(name=name942, terms=terms946)
    result948 = _t1710
    record_span!(parser, span_start947, "Pragma")
    return result948
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start964 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1712 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1713 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1714 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1715 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1716 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1717 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1718 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1719 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1720 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1721 = 7
                                            else
                                                _t1721 = -1
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
            end
            _t1712 = _t1713
        end
        _t1711 = _t1712
    else
        _t1711 = -1
    end
    prediction949 = _t1711
    if prediction949 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1723 = parse_name(parser)
        name959 = _t1723
        xs960 = Proto.RelTerm[]
        cond961 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond961
            _t1724 = parse_rel_term(parser)
            item962 = _t1724
            push!(xs960, item962)
            cond961 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms963 = xs960
        consume_literal!(parser, ")")
        _t1725 = Proto.Primitive(name=name959, terms=rel_terms963)
        _t1722 = _t1725
    else
        if prediction949 == 8
            _t1727 = parse_divide(parser)
            divide958 = _t1727
            _t1726 = divide958
        else
            if prediction949 == 7
                _t1729 = parse_multiply(parser)
                multiply957 = _t1729
                _t1728 = multiply957
            else
                if prediction949 == 6
                    _t1731 = parse_minus(parser)
                    minus956 = _t1731
                    _t1730 = minus956
                else
                    if prediction949 == 5
                        _t1733 = parse_add(parser)
                        add955 = _t1733
                        _t1732 = add955
                    else
                        if prediction949 == 4
                            _t1735 = parse_gt_eq(parser)
                            gt_eq954 = _t1735
                            _t1734 = gt_eq954
                        else
                            if prediction949 == 3
                                _t1737 = parse_gt(parser)
                                gt953 = _t1737
                                _t1736 = gt953
                            else
                                if prediction949 == 2
                                    _t1739 = parse_lt_eq(parser)
                                    lt_eq952 = _t1739
                                    _t1738 = lt_eq952
                                else
                                    if prediction949 == 1
                                        _t1741 = parse_lt(parser)
                                        lt951 = _t1741
                                        _t1740 = lt951
                                    else
                                        if prediction949 == 0
                                            _t1743 = parse_eq(parser)
                                            eq950 = _t1743
                                            _t1742 = eq950
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
            _t1726 = _t1728
        end
        _t1722 = _t1726
    end
    result965 = _t1722
    record_span!(parser, span_start964, "Primitive")
    return result965
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start968 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1744 = parse_term(parser)
    term966 = _t1744
    _t1745 = parse_term(parser)
    term_3967 = _t1745
    consume_literal!(parser, ")")
    _t1746 = Proto.RelTerm(rel_term_type=OneOf(:term, term966))
    _t1747 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3967))
    _t1748 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1746, _t1747])
    result969 = _t1748
    record_span!(parser, span_start968, "Primitive")
    return result969
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start972 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1749 = parse_term(parser)
    term970 = _t1749
    _t1750 = parse_term(parser)
    term_3971 = _t1750
    consume_literal!(parser, ")")
    _t1751 = Proto.RelTerm(rel_term_type=OneOf(:term, term970))
    _t1752 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3971))
    _t1753 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1751, _t1752])
    result973 = _t1753
    record_span!(parser, span_start972, "Primitive")
    return result973
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start976 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1754 = parse_term(parser)
    term974 = _t1754
    _t1755 = parse_term(parser)
    term_3975 = _t1755
    consume_literal!(parser, ")")
    _t1756 = Proto.RelTerm(rel_term_type=OneOf(:term, term974))
    _t1757 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3975))
    _t1758 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1756, _t1757])
    result977 = _t1758
    record_span!(parser, span_start976, "Primitive")
    return result977
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1759 = parse_term(parser)
    term978 = _t1759
    _t1760 = parse_term(parser)
    term_3979 = _t1760
    consume_literal!(parser, ")")
    _t1761 = Proto.RelTerm(rel_term_type=OneOf(:term, term978))
    _t1762 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3979))
    _t1763 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1761, _t1762])
    result981 = _t1763
    record_span!(parser, span_start980, "Primitive")
    return result981
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start984 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1764 = parse_term(parser)
    term982 = _t1764
    _t1765 = parse_term(parser)
    term_3983 = _t1765
    consume_literal!(parser, ")")
    _t1766 = Proto.RelTerm(rel_term_type=OneOf(:term, term982))
    _t1767 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3983))
    _t1768 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1766, _t1767])
    result985 = _t1768
    record_span!(parser, span_start984, "Primitive")
    return result985
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start989 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1769 = parse_term(parser)
    term986 = _t1769
    _t1770 = parse_term(parser)
    term_3987 = _t1770
    _t1771 = parse_term(parser)
    term_4988 = _t1771
    consume_literal!(parser, ")")
    _t1772 = Proto.RelTerm(rel_term_type=OneOf(:term, term986))
    _t1773 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3987))
    _t1774 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4988))
    _t1775 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1772, _t1773, _t1774])
    result990 = _t1775
    record_span!(parser, span_start989, "Primitive")
    return result990
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start994 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1776 = parse_term(parser)
    term991 = _t1776
    _t1777 = parse_term(parser)
    term_3992 = _t1777
    _t1778 = parse_term(parser)
    term_4993 = _t1778
    consume_literal!(parser, ")")
    _t1779 = Proto.RelTerm(rel_term_type=OneOf(:term, term991))
    _t1780 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3992))
    _t1781 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4993))
    _t1782 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1779, _t1780, _t1781])
    result995 = _t1782
    record_span!(parser, span_start994, "Primitive")
    return result995
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start999 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1783 = parse_term(parser)
    term996 = _t1783
    _t1784 = parse_term(parser)
    term_3997 = _t1784
    _t1785 = parse_term(parser)
    term_4998 = _t1785
    consume_literal!(parser, ")")
    _t1786 = Proto.RelTerm(rel_term_type=OneOf(:term, term996))
    _t1787 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3997))
    _t1788 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4998))
    _t1789 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1786, _t1787, _t1788])
    result1000 = _t1789
    record_span!(parser, span_start999, "Primitive")
    return result1000
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1004 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1790 = parse_term(parser)
    term1001 = _t1790
    _t1791 = parse_term(parser)
    term_31002 = _t1791
    _t1792 = parse_term(parser)
    term_41003 = _t1792
    consume_literal!(parser, ")")
    _t1793 = Proto.RelTerm(rel_term_type=OneOf(:term, term1001))
    _t1794 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31002))
    _t1795 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41003))
    _t1796 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1793, _t1794, _t1795])
    result1005 = _t1796
    record_span!(parser, span_start1004, "Primitive")
    return result1005
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1009 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1797 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1798 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1799 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1800 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1801 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1802 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1803 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1804 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1805 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1806 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1807 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1808 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1809 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1810 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1811 = 1
                                                            else
                                                                _t1811 = -1
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
            _t1798 = _t1799
        end
        _t1797 = _t1798
    end
    prediction1006 = _t1797
    if prediction1006 == 1
        _t1813 = parse_term(parser)
        term1008 = _t1813
        _t1814 = Proto.RelTerm(rel_term_type=OneOf(:term, term1008))
        _t1812 = _t1814
    else
        if prediction1006 == 0
            _t1816 = parse_specialized_value(parser)
            specialized_value1007 = _t1816
            _t1817 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1007))
            _t1815 = _t1817
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1812 = _t1815
    end
    result1010 = _t1812
    record_span!(parser, span_start1009, "RelTerm")
    return result1010
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1012 = span_start(parser)
    consume_literal!(parser, "#")
    _t1818 = parse_raw_value(parser)
    raw_value1011 = _t1818
    result1013 = raw_value1011
    record_span!(parser, span_start1012, "Value")
    return result1013
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1019 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1819 = parse_name(parser)
    name1014 = _t1819
    xs1015 = Proto.RelTerm[]
    cond1016 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1016
        _t1820 = parse_rel_term(parser)
        item1017 = _t1820
        push!(xs1015, item1017)
        cond1016 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1018 = xs1015
    consume_literal!(parser, ")")
    _t1821 = Proto.RelAtom(name=name1014, terms=rel_terms1018)
    result1020 = _t1821
    record_span!(parser, span_start1019, "RelAtom")
    return result1020
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1023 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1822 = parse_term(parser)
    term1021 = _t1822
    _t1823 = parse_term(parser)
    term_31022 = _t1823
    consume_literal!(parser, ")")
    _t1824 = Proto.Cast(input=term1021, result=term_31022)
    result1024 = _t1824
    record_span!(parser, span_start1023, "Cast")
    return result1024
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1025 = Proto.Attribute[]
    cond1026 = match_lookahead_literal(parser, "(", 0)
    while cond1026
        _t1825 = parse_attribute(parser)
        item1027 = _t1825
        push!(xs1025, item1027)
        cond1026 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1028 = xs1025
    consume_literal!(parser, ")")
    return attributes1028
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1034 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1826 = parse_name(parser)
    name1029 = _t1826
    xs1030 = Proto.Value[]
    cond1031 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1031
        _t1827 = parse_raw_value(parser)
        item1032 = _t1827
        push!(xs1030, item1032)
        cond1031 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1033 = xs1030
    consume_literal!(parser, ")")
    _t1828 = Proto.Attribute(name=name1029, args=raw_values1033)
    result1035 = _t1828
    record_span!(parser, span_start1034, "Attribute")
    return result1035
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1042 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1036 = Proto.RelationId[]
    cond1037 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1037
        _t1829 = parse_relation_id(parser)
        item1038 = _t1829
        push!(xs1036, item1038)
        cond1037 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1039 = xs1036
    _t1830 = parse_script(parser)
    script1040 = _t1830
    if match_lookahead_literal(parser, "(", 0)
        _t1832 = parse_attrs(parser)
        _t1831 = _t1832
    else
        _t1831 = nothing
    end
    attrs1041 = _t1831
    consume_literal!(parser, ")")
    _t1833 = Proto.Algorithm(var"#global"=relation_ids1039, body=script1040, attrs=(!isnothing(attrs1041) ? attrs1041 : Proto.Attribute[]))
    result1043 = _t1833
    record_span!(parser, span_start1042, "Algorithm")
    return result1043
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1048 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1044 = Proto.Construct[]
    cond1045 = match_lookahead_literal(parser, "(", 0)
    while cond1045
        _t1834 = parse_construct(parser)
        item1046 = _t1834
        push!(xs1044, item1046)
        cond1045 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1047 = xs1044
    consume_literal!(parser, ")")
    _t1835 = Proto.Script(constructs=constructs1047)
    result1049 = _t1835
    record_span!(parser, span_start1048, "Script")
    return result1049
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1053 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1837 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1838 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1839 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1840 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1841 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1842 = 1
                            else
                                _t1842 = -1
                            end
                            _t1841 = _t1842
                        end
                        _t1840 = _t1841
                    end
                    _t1839 = _t1840
                end
                _t1838 = _t1839
            end
            _t1837 = _t1838
        end
        _t1836 = _t1837
    else
        _t1836 = -1
    end
    prediction1050 = _t1836
    if prediction1050 == 1
        _t1844 = parse_instruction(parser)
        instruction1052 = _t1844
        _t1845 = Proto.Construct(construct_type=OneOf(:instruction, instruction1052))
        _t1843 = _t1845
    else
        if prediction1050 == 0
            _t1847 = parse_loop(parser)
            loop1051 = _t1847
            _t1848 = Proto.Construct(construct_type=OneOf(:loop, loop1051))
            _t1846 = _t1848
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1843 = _t1846
    end
    result1054 = _t1843
    record_span!(parser, span_start1053, "Construct")
    return result1054
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1058 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1849 = parse_init(parser)
    init1055 = _t1849
    _t1850 = parse_script(parser)
    script1056 = _t1850
    if match_lookahead_literal(parser, "(", 0)
        _t1852 = parse_attrs(parser)
        _t1851 = _t1852
    else
        _t1851 = nothing
    end
    attrs1057 = _t1851
    consume_literal!(parser, ")")
    _t1853 = Proto.Loop(init=init1055, body=script1056, attrs=(!isnothing(attrs1057) ? attrs1057 : Proto.Attribute[]))
    result1059 = _t1853
    record_span!(parser, span_start1058, "Loop")
    return result1059
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1060 = Proto.Instruction[]
    cond1061 = match_lookahead_literal(parser, "(", 0)
    while cond1061
        _t1854 = parse_instruction(parser)
        item1062 = _t1854
        push!(xs1060, item1062)
        cond1061 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1063 = xs1060
    consume_literal!(parser, ")")
    return instructions1063
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1070 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1856 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1857 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1858 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1859 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1860 = 0
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
        end
        _t1855 = _t1856
    else
        _t1855 = -1
    end
    prediction1064 = _t1855
    if prediction1064 == 4
        _t1862 = parse_monus_def(parser)
        monus_def1069 = _t1862
        _t1863 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1069))
        _t1861 = _t1863
    else
        if prediction1064 == 3
            _t1865 = parse_monoid_def(parser)
            monoid_def1068 = _t1865
            _t1866 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1068))
            _t1864 = _t1866
        else
            if prediction1064 == 2
                _t1868 = parse_break(parser)
                break1067 = _t1868
                _t1869 = Proto.Instruction(instr_type=OneOf(:var"#break", break1067))
                _t1867 = _t1869
            else
                if prediction1064 == 1
                    _t1871 = parse_upsert(parser)
                    upsert1066 = _t1871
                    _t1872 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1066))
                    _t1870 = _t1872
                else
                    if prediction1064 == 0
                        _t1874 = parse_assign(parser)
                        assign1065 = _t1874
                        _t1875 = Proto.Instruction(instr_type=OneOf(:assign, assign1065))
                        _t1873 = _t1875
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1870 = _t1873
                end
                _t1867 = _t1870
            end
            _t1864 = _t1867
        end
        _t1861 = _t1864
    end
    result1071 = _t1861
    record_span!(parser, span_start1070, "Instruction")
    return result1071
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1075 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1876 = parse_relation_id(parser)
    relation_id1072 = _t1876
    _t1877 = parse_abstraction(parser)
    abstraction1073 = _t1877
    if match_lookahead_literal(parser, "(", 0)
        _t1879 = parse_attrs(parser)
        _t1878 = _t1879
    else
        _t1878 = nothing
    end
    attrs1074 = _t1878
    consume_literal!(parser, ")")
    _t1880 = Proto.Assign(name=relation_id1072, body=abstraction1073, attrs=(!isnothing(attrs1074) ? attrs1074 : Proto.Attribute[]))
    result1076 = _t1880
    record_span!(parser, span_start1075, "Assign")
    return result1076
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1080 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1881 = parse_relation_id(parser)
    relation_id1077 = _t1881
    _t1882 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1078 = _t1882
    if match_lookahead_literal(parser, "(", 0)
        _t1884 = parse_attrs(parser)
        _t1883 = _t1884
    else
        _t1883 = nothing
    end
    attrs1079 = _t1883
    consume_literal!(parser, ")")
    _t1885 = Proto.Upsert(name=relation_id1077, body=abstraction_with_arity1078[1], attrs=(!isnothing(attrs1079) ? attrs1079 : Proto.Attribute[]), value_arity=abstraction_with_arity1078[2])
    result1081 = _t1885
    record_span!(parser, span_start1080, "Upsert")
    return result1081
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1886 = parse_bindings(parser)
    bindings1082 = _t1886
    _t1887 = parse_formula(parser)
    formula1083 = _t1887
    consume_literal!(parser, ")")
    _t1888 = Proto.Abstraction(vars=vcat(bindings1082[1], !isnothing(bindings1082[2]) ? bindings1082[2] : []), value=formula1083)
    return (_t1888, length(bindings1082[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1087 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1889 = parse_relation_id(parser)
    relation_id1084 = _t1889
    _t1890 = parse_abstraction(parser)
    abstraction1085 = _t1890
    if match_lookahead_literal(parser, "(", 0)
        _t1892 = parse_attrs(parser)
        _t1891 = _t1892
    else
        _t1891 = nothing
    end
    attrs1086 = _t1891
    consume_literal!(parser, ")")
    _t1893 = Proto.Break(name=relation_id1084, body=abstraction1085, attrs=(!isnothing(attrs1086) ? attrs1086 : Proto.Attribute[]))
    result1088 = _t1893
    record_span!(parser, span_start1087, "Break")
    return result1088
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1093 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1894 = parse_monoid(parser)
    monoid1089 = _t1894
    _t1895 = parse_relation_id(parser)
    relation_id1090 = _t1895
    _t1896 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1091 = _t1896
    if match_lookahead_literal(parser, "(", 0)
        _t1898 = parse_attrs(parser)
        _t1897 = _t1898
    else
        _t1897 = nothing
    end
    attrs1092 = _t1897
    consume_literal!(parser, ")")
    _t1899 = Proto.MonoidDef(monoid=monoid1089, name=relation_id1090, body=abstraction_with_arity1091[1], attrs=(!isnothing(attrs1092) ? attrs1092 : Proto.Attribute[]), value_arity=abstraction_with_arity1091[2])
    result1094 = _t1899
    record_span!(parser, span_start1093, "MonoidDef")
    return result1094
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1100 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1901 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1902 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1903 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1904 = 2
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
    prediction1095 = _t1900
    if prediction1095 == 3
        _t1906 = parse_sum_monoid(parser)
        sum_monoid1099 = _t1906
        _t1907 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1099))
        _t1905 = _t1907
    else
        if prediction1095 == 2
            _t1909 = parse_max_monoid(parser)
            max_monoid1098 = _t1909
            _t1910 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1098))
            _t1908 = _t1910
        else
            if prediction1095 == 1
                _t1912 = parse_min_monoid(parser)
                min_monoid1097 = _t1912
                _t1913 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1097))
                _t1911 = _t1913
            else
                if prediction1095 == 0
                    _t1915 = parse_or_monoid(parser)
                    or_monoid1096 = _t1915
                    _t1916 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1096))
                    _t1914 = _t1916
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1911 = _t1914
            end
            _t1908 = _t1911
        end
        _t1905 = _t1908
    end
    result1101 = _t1905
    record_span!(parser, span_start1100, "Monoid")
    return result1101
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1102 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1917 = Proto.OrMonoid()
    result1103 = _t1917
    record_span!(parser, span_start1102, "OrMonoid")
    return result1103
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1105 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1918 = parse_type(parser)
    type1104 = _t1918
    consume_literal!(parser, ")")
    _t1919 = Proto.MinMonoid(var"#type"=type1104)
    result1106 = _t1919
    record_span!(parser, span_start1105, "MinMonoid")
    return result1106
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1108 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1920 = parse_type(parser)
    type1107 = _t1920
    consume_literal!(parser, ")")
    _t1921 = Proto.MaxMonoid(var"#type"=type1107)
    result1109 = _t1921
    record_span!(parser, span_start1108, "MaxMonoid")
    return result1109
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1111 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1922 = parse_type(parser)
    type1110 = _t1922
    consume_literal!(parser, ")")
    _t1923 = Proto.SumMonoid(var"#type"=type1110)
    result1112 = _t1923
    record_span!(parser, span_start1111, "SumMonoid")
    return result1112
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1117 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1924 = parse_monoid(parser)
    monoid1113 = _t1924
    _t1925 = parse_relation_id(parser)
    relation_id1114 = _t1925
    _t1926 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1115 = _t1926
    if match_lookahead_literal(parser, "(", 0)
        _t1928 = parse_attrs(parser)
        _t1927 = _t1928
    else
        _t1927 = nothing
    end
    attrs1116 = _t1927
    consume_literal!(parser, ")")
    _t1929 = Proto.MonusDef(monoid=monoid1113, name=relation_id1114, body=abstraction_with_arity1115[1], attrs=(!isnothing(attrs1116) ? attrs1116 : Proto.Attribute[]), value_arity=abstraction_with_arity1115[2])
    result1118 = _t1929
    record_span!(parser, span_start1117, "MonusDef")
    return result1118
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1123 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1930 = parse_relation_id(parser)
    relation_id1119 = _t1930
    _t1931 = parse_abstraction(parser)
    abstraction1120 = _t1931
    _t1932 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1121 = _t1932
    _t1933 = parse_functional_dependency_values(parser)
    functional_dependency_values1122 = _t1933
    consume_literal!(parser, ")")
    _t1934 = Proto.FunctionalDependency(guard=abstraction1120, keys=functional_dependency_keys1121, values=functional_dependency_values1122)
    _t1935 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1934), name=relation_id1119)
    result1124 = _t1935
    record_span!(parser, span_start1123, "Constraint")
    return result1124
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1125 = Proto.Var[]
    cond1126 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1126
        _t1936 = parse_var(parser)
        item1127 = _t1936
        push!(xs1125, item1127)
        cond1126 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1128 = xs1125
    consume_literal!(parser, ")")
    return vars1128
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1129 = Proto.Var[]
    cond1130 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1130
        _t1937 = parse_var(parser)
        item1131 = _t1937
        push!(xs1129, item1131)
        cond1130 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1132 = xs1129
    consume_literal!(parser, ")")
    return vars1132
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1138 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1939 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1940 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1941 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1942 = 1
                    else
                        _t1942 = -1
                    end
                    _t1941 = _t1942
                end
                _t1940 = _t1941
            end
            _t1939 = _t1940
        end
        _t1938 = _t1939
    else
        _t1938 = -1
    end
    prediction1133 = _t1938
    if prediction1133 == 3
        _t1944 = parse_iceberg_data(parser)
        iceberg_data1137 = _t1944
        _t1945 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1137))
        _t1943 = _t1945
    else
        if prediction1133 == 2
            _t1947 = parse_csv_data(parser)
            csv_data1136 = _t1947
            _t1948 = Proto.Data(data_type=OneOf(:csv_data, csv_data1136))
            _t1946 = _t1948
        else
            if prediction1133 == 1
                _t1950 = parse_betree_relation(parser)
                betree_relation1135 = _t1950
                _t1951 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1135))
                _t1949 = _t1951
            else
                if prediction1133 == 0
                    _t1953 = parse_edb(parser)
                    edb1134 = _t1953
                    _t1954 = Proto.Data(data_type=OneOf(:edb, edb1134))
                    _t1952 = _t1954
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1949 = _t1952
            end
            _t1946 = _t1949
        end
        _t1943 = _t1946
    end
    result1139 = _t1943
    record_span!(parser, span_start1138, "Data")
    return result1139
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1143 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1955 = parse_relation_id(parser)
    relation_id1140 = _t1955
    _t1956 = parse_edb_path(parser)
    edb_path1141 = _t1956
    _t1957 = parse_edb_types(parser)
    edb_types1142 = _t1957
    consume_literal!(parser, ")")
    _t1958 = Proto.EDB(target_id=relation_id1140, path=edb_path1141, types=edb_types1142)
    result1144 = _t1958
    record_span!(parser, span_start1143, "EDB")
    return result1144
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1145 = String[]
    cond1146 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1146
        item1147 = consume_terminal!(parser, "STRING")
        push!(xs1145, item1147)
        cond1146 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1148 = xs1145
    consume_literal!(parser, "]")
    return strings1148
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1149 = Proto.var"#Type"[]
    cond1150 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1150
        _t1959 = parse_type(parser)
        item1151 = _t1959
        push!(xs1149, item1151)
        cond1150 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1152 = xs1149
    consume_literal!(parser, "]")
    return types1152
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1155 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1960 = parse_relation_id(parser)
    relation_id1153 = _t1960
    _t1961 = parse_betree_info(parser)
    betree_info1154 = _t1961
    consume_literal!(parser, ")")
    _t1962 = Proto.BeTreeRelation(name=relation_id1153, relation_info=betree_info1154)
    result1156 = _t1962
    record_span!(parser, span_start1155, "BeTreeRelation")
    return result1156
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1160 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1963 = parse_betree_info_key_types(parser)
    betree_info_key_types1157 = _t1963
    _t1964 = parse_betree_info_value_types(parser)
    betree_info_value_types1158 = _t1964
    _t1965 = parse_config_dict(parser)
    config_dict1159 = _t1965
    consume_literal!(parser, ")")
    _t1966 = construct_betree_info(parser, betree_info_key_types1157, betree_info_value_types1158, config_dict1159)
    result1161 = _t1966
    record_span!(parser, span_start1160, "BeTreeInfo")
    return result1161
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1162 = Proto.var"#Type"[]
    cond1163 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1163
        _t1967 = parse_type(parser)
        item1164 = _t1967
        push!(xs1162, item1164)
        cond1163 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1165 = xs1162
    consume_literal!(parser, ")")
    return types1165
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1166 = Proto.var"#Type"[]
    cond1167 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1167
        _t1968 = parse_type(parser)
        item1168 = _t1968
        push!(xs1166, item1168)
        cond1167 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1169 = xs1166
    consume_literal!(parser, ")")
    return types1169
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1174 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1969 = parse_csvlocator(parser)
    csvlocator1170 = _t1969
    _t1970 = parse_csv_config(parser)
    csv_config1171 = _t1970
    _t1971 = parse_gnf_columns(parser)
    gnf_columns1172 = _t1971
    _t1972 = parse_csv_asof(parser)
    csv_asof1173 = _t1972
    consume_literal!(parser, ")")
    _t1973 = Proto.CSVData(locator=csvlocator1170, config=csv_config1171, columns=gnf_columns1172, asof=csv_asof1173)
    result1175 = _t1973
    record_span!(parser, span_start1174, "CSVData")
    return result1175
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1178 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1975 = parse_csv_locator_paths(parser)
        _t1974 = _t1975
    else
        _t1974 = nothing
    end
    csv_locator_paths1176 = _t1974
    if match_lookahead_literal(parser, "(", 0)
        _t1977 = parse_csv_locator_inline_data(parser)
        _t1976 = _t1977
    else
        _t1976 = nothing
    end
    csv_locator_inline_data1177 = _t1976
    consume_literal!(parser, ")")
    _t1978 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1176) ? csv_locator_paths1176 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1177) ? csv_locator_inline_data1177 : "")))
    result1179 = _t1978
    record_span!(parser, span_start1178, "CSVLocator")
    return result1179
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1180 = String[]
    cond1181 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1181
        item1182 = consume_terminal!(parser, "STRING")
        push!(xs1180, item1182)
        cond1181 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1183 = xs1180
    consume_literal!(parser, ")")
    return strings1183
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1184 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1184
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1187 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1979 = parse_config_dict(parser)
    config_dict1185 = _t1979
    if match_lookahead_literal(parser, "(", 0)
        _t1981 = parse__storage_integration(parser)
        _t1980 = _t1981
    else
        _t1980 = nothing
    end
    _storage_integration1186 = _t1980
    consume_literal!(parser, ")")
    _t1982 = construct_csv_config(parser, config_dict1185, _storage_integration1186)
    result1188 = _t1982
    record_span!(parser, span_start1187, "CSVConfig")
    return result1188
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t1983 = parse_config_dict(parser)
    config_dict1189 = _t1983
    consume_literal!(parser, ")")
    return config_dict1189
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1190 = Proto.GNFColumn[]
    cond1191 = match_lookahead_literal(parser, "(", 0)
    while cond1191
        _t1984 = parse_gnf_column(parser)
        item1192 = _t1984
        push!(xs1190, item1192)
        cond1191 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1193 = xs1190
    consume_literal!(parser, ")")
    return gnf_columns1193
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1200 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1985 = parse_gnf_column_path(parser)
    gnf_column_path1194 = _t1985
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1987 = parse_relation_id(parser)
        _t1986 = _t1987
    else
        _t1986 = nothing
    end
    relation_id1195 = _t1986
    consume_literal!(parser, "[")
    xs1196 = Proto.var"#Type"[]
    cond1197 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1197
        _t1988 = parse_type(parser)
        item1198 = _t1988
        push!(xs1196, item1198)
        cond1197 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1199 = xs1196
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1989 = Proto.GNFColumn(column_path=gnf_column_path1194, target_id=relation_id1195, types=types1199)
    result1201 = _t1989
    record_span!(parser, span_start1200, "GNFColumn")
    return result1201
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1990 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1991 = 0
        else
            _t1991 = -1
        end
        _t1990 = _t1991
    end
    prediction1202 = _t1990
    if prediction1202 == 1
        consume_literal!(parser, "[")
        xs1204 = String[]
        cond1205 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1205
            item1206 = consume_terminal!(parser, "STRING")
            push!(xs1204, item1206)
            cond1205 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1207 = xs1204
        consume_literal!(parser, "]")
        _t1992 = strings1207
    else
        if prediction1202 == 0
            string1203 = consume_terminal!(parser, "STRING")
            _t1993 = String[string1203]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1992 = _t1993
    end
    return _t1992
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1208 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1208
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1215 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1994 = parse_iceberg_locator(parser)
    iceberg_locator1209 = _t1994
    _t1995 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1210 = _t1995
    _t1996 = parse_gnf_columns(parser)
    gnf_columns1211 = _t1996
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1998 = parse_iceberg_from_snapshot(parser)
        _t1997 = _t1998
    else
        _t1997 = nothing
    end
    iceberg_from_snapshot1212 = _t1997
    if match_lookahead_literal(parser, "(", 0)
        _t2000 = parse_iceberg_to_snapshot(parser)
        _t1999 = _t2000
    else
        _t1999 = nothing
    end
    iceberg_to_snapshot1213 = _t1999
    _t2001 = parse_boolean_value(parser)
    boolean_value1214 = _t2001
    consume_literal!(parser, ")")
    _t2002 = construct_iceberg_data(parser, iceberg_locator1209, iceberg_catalog_config1210, gnf_columns1211, iceberg_from_snapshot1212, iceberg_to_snapshot1213, boolean_value1214)
    result1216 = _t2002
    record_span!(parser, span_start1215, "IcebergData")
    return result1216
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1220 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2003 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1217 = _t2003
    _t2004 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1218 = _t2004
    _t2005 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1219 = _t2005
    consume_literal!(parser, ")")
    _t2006 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1217, namespace=iceberg_locator_namespace1218, warehouse=iceberg_locator_warehouse1219)
    result1221 = _t2006
    record_span!(parser, span_start1220, "IcebergLocator")
    return result1221
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1222 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1222
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1223 = String[]
    cond1224 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1224
        item1225 = consume_terminal!(parser, "STRING")
        push!(xs1223, item1225)
        cond1224 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1226 = xs1223
    consume_literal!(parser, ")")
    return strings1226
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1227 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1227
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1232 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2007 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1228 = _t2007
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2009 = parse_iceberg_catalog_config_scope(parser)
        _t2008 = _t2009
    else
        _t2008 = nothing
    end
    iceberg_catalog_config_scope1229 = _t2008
    _t2010 = parse_iceberg_properties(parser)
    iceberg_properties1230 = _t2010
    _t2011 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1231 = _t2011
    consume_literal!(parser, ")")
    _t2012 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1228, iceberg_catalog_config_scope1229, iceberg_properties1230, iceberg_auth_properties1231)
    result1233 = _t2012
    record_span!(parser, span_start1232, "IcebergCatalogConfig")
    return result1233
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1234 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1234
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1235 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1235
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1236 = Tuple{String, String}[]
    cond1237 = match_lookahead_literal(parser, "(", 0)
    while cond1237
        _t2013 = parse_iceberg_property_entry(parser)
        item1238 = _t2013
        push!(xs1236, item1238)
        cond1237 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1239 = xs1236
    consume_literal!(parser, ")")
    return iceberg_property_entrys1239
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1240 = consume_terminal!(parser, "STRING")
    string_31241 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1240, string_31241,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1242 = Tuple{String, String}[]
    cond1243 = match_lookahead_literal(parser, "(", 0)
    while cond1243
        _t2014 = parse_iceberg_masked_property_entry(parser)
        item1244 = _t2014
        push!(xs1242, item1244)
        cond1243 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1245 = xs1242
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1245
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1246 = consume_terminal!(parser, "STRING")
    string_31247 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1246, string_31247,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1248 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1248
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1249 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1249
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1251 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2015 = parse_fragment_id(parser)
    fragment_id1250 = _t2015
    consume_literal!(parser, ")")
    _t2016 = Proto.Undefine(fragment_id=fragment_id1250)
    result1252 = _t2016
    record_span!(parser, span_start1251, "Undefine")
    return result1252
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1257 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1253 = Proto.RelationId[]
    cond1254 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1254
        _t2017 = parse_relation_id(parser)
        item1255 = _t2017
        push!(xs1253, item1255)
        cond1254 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1256 = xs1253
    consume_literal!(parser, ")")
    _t2018 = Proto.Context(relations=relation_ids1256)
    result1258 = _t2018
    record_span!(parser, span_start1257, "Context")
    return result1258
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1264 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2019 = parse_edb_path(parser)
    edb_path1259 = _t2019
    xs1260 = Proto.SnapshotMapping[]
    cond1261 = match_lookahead_literal(parser, "[", 0)
    while cond1261
        _t2020 = parse_snapshot_mapping(parser)
        item1262 = _t2020
        push!(xs1260, item1262)
        cond1261 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1263 = xs1260
    consume_literal!(parser, ")")
    _t2021 = Proto.Snapshot(mappings=snapshot_mappings1263, prefix=edb_path1259)
    result1265 = _t2021
    record_span!(parser, span_start1264, "Snapshot")
    return result1265
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1268 = span_start(parser)
    _t2022 = parse_edb_path(parser)
    edb_path1266 = _t2022
    _t2023 = parse_relation_id(parser)
    relation_id1267 = _t2023
    _t2024 = Proto.SnapshotMapping(destination_path=edb_path1266, source_relation=relation_id1267)
    result1269 = _t2024
    record_span!(parser, span_start1268, "SnapshotMapping")
    return result1269
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1270 = Proto.Read[]
    cond1271 = match_lookahead_literal(parser, "(", 0)
    while cond1271
        _t2025 = parse_read(parser)
        item1272 = _t2025
        push!(xs1270, item1272)
        cond1271 = match_lookahead_literal(parser, "(", 0)
    end
    reads1273 = xs1270
    consume_literal!(parser, ")")
    return reads1273
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1281 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2027 = 2
        else
            if match_lookahead_literal(parser, "output_export", 1)
                _t2028 = 5
            else
                if match_lookahead_literal(parser, "output", 1)
                    _t2029 = 1
                else
                    if match_lookahead_literal(parser, "export_iceberg", 1)
                        _t2030 = 4
                    else
                        if match_lookahead_literal(parser, "export", 1)
                            _t2031 = 4
                        else
                            if match_lookahead_literal(parser, "demand", 1)
                                _t2032 = 0
                            else
                                if match_lookahead_literal(parser, "abort", 1)
                                    _t2033 = 3
                                else
                                    _t2033 = -1
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
            end
            _t2027 = _t2028
        end
        _t2026 = _t2027
    else
        _t2026 = -1
    end
    prediction1274 = _t2026
    if prediction1274 == 5
        _t2035 = parse_export_output(parser)
        export_output1280 = _t2035
        _t2036 = Proto.Read(read_type=OneOf(:export_output, export_output1280))
        _t2034 = _t2036
    else
        if prediction1274 == 4
            _t2038 = parse_export(parser)
            export1279 = _t2038
            _t2039 = Proto.Read(read_type=OneOf(:var"#export", export1279))
            _t2037 = _t2039
        else
            if prediction1274 == 3
                _t2041 = parse_abort(parser)
                abort1278 = _t2041
                _t2042 = Proto.Read(read_type=OneOf(:abort, abort1278))
                _t2040 = _t2042
            else
                if prediction1274 == 2
                    _t2044 = parse_what_if(parser)
                    what_if1277 = _t2044
                    _t2045 = Proto.Read(read_type=OneOf(:what_if, what_if1277))
                    _t2043 = _t2045
                else
                    if prediction1274 == 1
                        _t2047 = parse_output(parser)
                        output1276 = _t2047
                        _t2048 = Proto.Read(read_type=OneOf(:output, output1276))
                        _t2046 = _t2048
                    else
                        if prediction1274 == 0
                            _t2050 = parse_demand(parser)
                            demand1275 = _t2050
                            _t2051 = Proto.Read(read_type=OneOf(:demand, demand1275))
                            _t2049 = _t2051
                        else
                            throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                        end
                        _t2046 = _t2049
                    end
                    _t2043 = _t2046
                end
                _t2040 = _t2043
            end
            _t2037 = _t2040
        end
        _t2034 = _t2037
    end
    result1282 = _t2034
    record_span!(parser, span_start1281, "Read")
    return result1282
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1284 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2052 = parse_relation_id(parser)
    relation_id1283 = _t2052
    consume_literal!(parser, ")")
    _t2053 = Proto.Demand(relation_id=relation_id1283)
    result1285 = _t2053
    record_span!(parser, span_start1284, "Demand")
    return result1285
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1288 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2054 = parse_name(parser)
    name1286 = _t2054
    _t2055 = parse_relation_id(parser)
    relation_id1287 = _t2055
    consume_literal!(parser, ")")
    _t2056 = Proto.Output(name=name1286, relation_id=relation_id1287)
    result1289 = _t2056
    record_span!(parser, span_start1288, "Output")
    return result1289
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1292 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2057 = parse_name(parser)
    name1290 = _t2057
    _t2058 = parse_epoch(parser)
    epoch1291 = _t2058
    consume_literal!(parser, ")")
    _t2059 = Proto.WhatIf(branch=name1290, epoch=epoch1291)
    result1293 = _t2059
    record_span!(parser, span_start1292, "WhatIf")
    return result1293
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1296 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2061 = parse_name(parser)
        _t2060 = _t2061
    else
        _t2060 = nothing
    end
    name1294 = _t2060
    _t2062 = parse_relation_id(parser)
    relation_id1295 = _t2062
    consume_literal!(parser, ")")
    _t2063 = Proto.Abort(name=(!isnothing(name1294) ? name1294 : "abort"), relation_id=relation_id1295)
    result1297 = _t2063
    record_span!(parser, span_start1296, "Abort")
    return result1297
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1301 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2065 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2066 = 0
            else
                _t2066 = -1
            end
            _t2065 = _t2066
        end
        _t2064 = _t2065
    else
        _t2064 = -1
    end
    prediction1298 = _t2064
    if prediction1298 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2068 = parse_export_iceberg_config(parser)
        export_iceberg_config1300 = _t2068
        consume_literal!(parser, ")")
        _t2069 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1300))
        _t2067 = _t2069
    else
        if prediction1298 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2071 = parse_export_csv_config(parser)
            export_csv_config1299 = _t2071
            consume_literal!(parser, ")")
            _t2072 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1299))
            _t2070 = _t2072
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2067 = _t2070
    end
    result1302 = _t2067
    record_span!(parser, span_start1301, "Export")
    return result1302
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1310 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2074 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2075 = 1
            else
                _t2075 = -1
            end
            _t2074 = _t2075
        end
        _t2073 = _t2074
    else
        _t2073 = -1
    end
    prediction1303 = _t2073
    if prediction1303 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2077 = parse_export_csv_path(parser)
        export_csv_path1307 = _t2077
        _t2078 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1308 = _t2078
        _t2079 = parse_config_dict(parser)
        config_dict1309 = _t2079
        consume_literal!(parser, ")")
        _t2080 = construct_export_csv_config(parser, export_csv_path1307, export_csv_columns_list1308, config_dict1309)
        _t2076 = _t2080
    else
        if prediction1303 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2082 = parse_export_csv_path(parser)
            export_csv_path1304 = _t2082
            _t2083 = parse_export_csv_source(parser)
            export_csv_source1305 = _t2083
            _t2084 = parse_csv_config(parser)
            csv_config1306 = _t2084
            consume_literal!(parser, ")")
            _t2085 = construct_export_csv_config_with_source(parser, export_csv_path1304, export_csv_source1305, csv_config1306)
            _t2081 = _t2085
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2076 = _t2081
    end
    result1311 = _t2076
    record_span!(parser, span_start1310, "ExportCSVConfig")
    return result1311
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1312 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1312
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1319 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2087 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2088 = 0
            else
                _t2088 = -1
            end
            _t2087 = _t2088
        end
        _t2086 = _t2087
    else
        _t2086 = -1
    end
    prediction1313 = _t2086
    if prediction1313 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2090 = parse_relation_id(parser)
        relation_id1318 = _t2090
        consume_literal!(parser, ")")
        _t2091 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1318))
        _t2089 = _t2091
    else
        if prediction1313 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1314 = Proto.ExportCSVColumn[]
            cond1315 = match_lookahead_literal(parser, "(", 0)
            while cond1315
                _t2093 = parse_export_csv_column(parser)
                item1316 = _t2093
                push!(xs1314, item1316)
                cond1315 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1317 = xs1314
            consume_literal!(parser, ")")
            _t2094 = Proto.ExportCSVColumns(columns=export_csv_columns1317)
            _t2095 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2094))
            _t2092 = _t2095
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2089 = _t2092
    end
    result1320 = _t2089
    record_span!(parser, span_start1319, "ExportCSVSource")
    return result1320
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1323 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1321 = consume_terminal!(parser, "STRING")
    _t2096 = parse_relation_id(parser)
    relation_id1322 = _t2096
    consume_literal!(parser, ")")
    _t2097 = Proto.ExportCSVColumn(column_name=string1321, column_data=relation_id1322)
    result1324 = _t2097
    record_span!(parser, span_start1323, "ExportCSVColumn")
    return result1324
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1325 = Proto.ExportCSVColumn[]
    cond1326 = match_lookahead_literal(parser, "(", 0)
    while cond1326
        _t2098 = parse_export_csv_column(parser)
        item1327 = _t2098
        push!(xs1325, item1327)
        cond1326 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1328 = xs1325
    consume_literal!(parser, ")")
    return export_csv_columns1328
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1334 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2099 = parse_iceberg_locator(parser)
    iceberg_locator1329 = _t2099
    _t2100 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1330 = _t2100
    _t2101 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1331 = _t2101
    _t2102 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1332 = _t2102
    if match_lookahead_literal(parser, "{", 0)
        _t2104 = parse_config_dict(parser)
        _t2103 = _t2104
    else
        _t2103 = nothing
    end
    config_dict1333 = _t2103
    consume_literal!(parser, ")")
    _t2105 = construct_export_iceberg_config_full(parser, iceberg_locator1329, iceberg_catalog_config1330, export_iceberg_table_def1331, iceberg_table_properties1332, config_dict1333)
    result1335 = _t2105
    record_span!(parser, span_start1334, "ExportIcebergConfig")
    return result1335
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1337 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2106 = parse_relation_id(parser)
    relation_id1336 = _t2106
    consume_literal!(parser, ")")
    result1338 = relation_id1336
    record_span!(parser, span_start1337, "RelationId")
    return result1338
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1339 = Tuple{String, String}[]
    cond1340 = match_lookahead_literal(parser, "(", 0)
    while cond1340
        _t2107 = parse_iceberg_property_entry(parser)
        item1341 = _t2107
        push!(xs1339, item1341)
        cond1340 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1342 = xs1339
    consume_literal!(parser, ")")
    return iceberg_property_entrys1342
end

function parse_export_output(parser::ParserState)::Proto.ExportOutput
    span_start1344 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output_export")
    _t2108 = parse_export_csv_output(parser)
    export_csv_output1343 = _t2108
    consume_literal!(parser, ")")
    _t2109 = Proto.ExportOutput(export_output=OneOf(:csv, export_csv_output1343))
    result1345 = _t2109
    record_span!(parser, span_start1344, "ExportOutput")
    return result1345
end

function parse_export_csv_output(parser::ParserState)::Proto.ExportCSVOutput
    span_start1348 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv")
    _t2110 = parse_export_csv_source(parser)
    export_csv_source1346 = _t2110
    _t2111 = parse_csv_config(parser)
    csv_config1347 = _t2111
    consume_literal!(parser, ")")
    _t2112 = Proto.ExportCSVOutput(csv_source=export_csv_source1346, csv_config=csv_config1347)
    result1349 = _t2112
    record_span!(parser, span_start1348, "ExportCSVOutput")
    return result1349
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
