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
        _t2088 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2089 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2090 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2091 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2092 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2093 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2094 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2095 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2096 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2097 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2097
    _t2098 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2098
    _t2099 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2099
    _t2100 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2100
    _t2101 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2101
    _t2102 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2102
    _t2103 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2103
    _t2104 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2104
    _t2105 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2105
    _t2106 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2106
    _t2107 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2107
    _t2108 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2108
    _t2109 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2109
    _t2110 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2110
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.CSVStorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2111 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2112 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2113 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2114 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2115 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2116 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2117 = Proto.CSVStorageIntegration(provider=_t2112, azure_sas_token=_t2113, s3_region=_t2114, s3_access_key_id=_t2115, s3_secret_access_key=_t2116)
    return _t2117
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2118 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2118
    _t2119 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2119
    _t2120 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2120
    _t2121 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2121
    _t2122 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2122
    _t2123 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2123
    _t2124 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2124
    _t2125 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2125
    _t2126 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2126
    _t2127 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2127
    _t2128 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2128
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2129 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2129
    _t2130 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2130
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
    _t2131 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2131
    _t2132 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2132
    _t2133 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2133
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2134 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2134
    _t2135 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2135
    _t2136 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2136
    _t2137 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2137
    _t2138 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2138
    _t2139 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2139
    _t2140 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2140
    _t2141 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2141
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2142 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2142
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2143 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2143
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2144 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2144
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2145 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2145
    _t2146 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2146
    _t2147 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2147
    table_props = Dict(table_property_pairs)
    _t2148 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2148
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start673 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1335 = parse_configure(parser)
        _t1334 = _t1335
    else
        _t1334 = nothing
    end
    configure667 = _t1334
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1337 = parse_sync(parser)
        _t1336 = _t1337
    else
        _t1336 = nothing
    end
    sync668 = _t1336
    xs669 = Proto.Epoch[]
    cond670 = match_lookahead_literal(parser, "(", 0)
    while cond670
        _t1338 = parse_epoch(parser)
        item671 = _t1338
        push!(xs669, item671)
        cond670 = match_lookahead_literal(parser, "(", 0)
    end
    epochs672 = xs669
    consume_literal!(parser, ")")
    _t1339 = default_configure(parser)
    _t1340 = Proto.Transaction(epochs=epochs672, configure=(!isnothing(configure667) ? configure667 : _t1339), sync=sync668)
    result674 = _t1340
    record_span!(parser, span_start673, "Transaction")
    return result674
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start676 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1341 = parse_config_dict(parser)
    config_dict675 = _t1341
    consume_literal!(parser, ")")
    _t1342 = construct_configure(parser, config_dict675)
    result677 = _t1342
    record_span!(parser, span_start676, "Configure")
    return result677
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs678 = Tuple{String, Proto.Value}[]
    cond679 = match_lookahead_literal(parser, ":", 0)
    while cond679
        _t1343 = parse_config_key_value(parser)
        item680 = _t1343
        push!(xs678, item680)
        cond679 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values681 = xs678
    consume_literal!(parser, "}")
    return config_key_values681
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol682 = consume_terminal!(parser, "SYMBOL")
    _t1344 = parse_raw_value(parser)
    raw_value683 = _t1344
    return (symbol682, raw_value683,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start697 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1345 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1346 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1347 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1349 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1350 = 0
                        else
                            _t1350 = -1
                        end
                        _t1349 = _t1350
                    end
                    _t1348 = _t1349
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1351 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1352 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1353 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1354 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1355 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1356 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1357 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1358 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1359 = 10
                                                    else
                                                        _t1359 = -1
                                                    end
                                                    _t1358 = _t1359
                                                end
                                                _t1357 = _t1358
                                            end
                                            _t1356 = _t1357
                                        end
                                        _t1355 = _t1356
                                    end
                                    _t1354 = _t1355
                                end
                                _t1353 = _t1354
                            end
                            _t1352 = _t1353
                        end
                        _t1351 = _t1352
                    end
                    _t1348 = _t1351
                end
                _t1347 = _t1348
            end
            _t1346 = _t1347
        end
        _t1345 = _t1346
    end
    prediction684 = _t1345
    if prediction684 == 12
        _t1361 = parse_boolean_value(parser)
        boolean_value696 = _t1361
        _t1362 = Proto.Value(value=OneOf(:boolean_value, boolean_value696))
        _t1360 = _t1362
    else
        if prediction684 == 11
            consume_literal!(parser, "missing")
            _t1364 = Proto.MissingValue()
            _t1365 = Proto.Value(value=OneOf(:missing_value, _t1364))
            _t1363 = _t1365
        else
            if prediction684 == 10
                decimal695 = consume_terminal!(parser, "DECIMAL")
                _t1367 = Proto.Value(value=OneOf(:decimal_value, decimal695))
                _t1366 = _t1367
            else
                if prediction684 == 9
                    int128694 = consume_terminal!(parser, "INT128")
                    _t1369 = Proto.Value(value=OneOf(:int128_value, int128694))
                    _t1368 = _t1369
                else
                    if prediction684 == 8
                        uint128693 = consume_terminal!(parser, "UINT128")
                        _t1371 = Proto.Value(value=OneOf(:uint128_value, uint128693))
                        _t1370 = _t1371
                    else
                        if prediction684 == 7
                            uint32692 = consume_terminal!(parser, "UINT32")
                            _t1373 = Proto.Value(value=OneOf(:uint32_value, uint32692))
                            _t1372 = _t1373
                        else
                            if prediction684 == 6
                                float691 = consume_terminal!(parser, "FLOAT")
                                _t1375 = Proto.Value(value=OneOf(:float_value, float691))
                                _t1374 = _t1375
                            else
                                if prediction684 == 5
                                    float32690 = consume_terminal!(parser, "FLOAT32")
                                    _t1377 = Proto.Value(value=OneOf(:float32_value, float32690))
                                    _t1376 = _t1377
                                else
                                    if prediction684 == 4
                                        int689 = consume_terminal!(parser, "INT")
                                        _t1379 = Proto.Value(value=OneOf(:int_value, int689))
                                        _t1378 = _t1379
                                    else
                                        if prediction684 == 3
                                            int32688 = consume_terminal!(parser, "INT32")
                                            _t1381 = Proto.Value(value=OneOf(:int32_value, int32688))
                                            _t1380 = _t1381
                                        else
                                            if prediction684 == 2
                                                string687 = consume_terminal!(parser, "STRING")
                                                _t1383 = Proto.Value(value=OneOf(:string_value, string687))
                                                _t1382 = _t1383
                                            else
                                                if prediction684 == 1
                                                    _t1385 = parse_raw_datetime(parser)
                                                    raw_datetime686 = _t1385
                                                    _t1386 = Proto.Value(value=OneOf(:datetime_value, raw_datetime686))
                                                    _t1384 = _t1386
                                                else
                                                    if prediction684 == 0
                                                        _t1388 = parse_raw_date(parser)
                                                        raw_date685 = _t1388
                                                        _t1389 = Proto.Value(value=OneOf(:date_value, raw_date685))
                                                        _t1387 = _t1389
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1384 = _t1387
                                                end
                                                _t1382 = _t1384
                                            end
                                            _t1380 = _t1382
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
            _t1363 = _t1366
        end
        _t1360 = _t1363
    end
    result698 = _t1360
    record_span!(parser, span_start697, "Value")
    return result698
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start702 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int699 = consume_terminal!(parser, "INT")
    int_3700 = consume_terminal!(parser, "INT")
    int_4701 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1390 = Proto.DateValue(year=Int32(int699), month=Int32(int_3700), day=Int32(int_4701))
    result703 = _t1390
    record_span!(parser, span_start702, "DateValue")
    return result703
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start711 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int704 = consume_terminal!(parser, "INT")
    int_3705 = consume_terminal!(parser, "INT")
    int_4706 = consume_terminal!(parser, "INT")
    int_5707 = consume_terminal!(parser, "INT")
    int_6708 = consume_terminal!(parser, "INT")
    int_7709 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1391 = consume_terminal!(parser, "INT")
    else
        _t1391 = nothing
    end
    int_8710 = _t1391
    consume_literal!(parser, ")")
    _t1392 = Proto.DateTimeValue(year=Int32(int704), month=Int32(int_3705), day=Int32(int_4706), hour=Int32(int_5707), minute=Int32(int_6708), second=Int32(int_7709), microsecond=Int32((!isnothing(int_8710) ? int_8710 : 0)))
    result712 = _t1392
    record_span!(parser, span_start711, "DateTimeValue")
    return result712
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1393 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1394 = 1
        else
            _t1394 = -1
        end
        _t1393 = _t1394
    end
    prediction713 = _t1393
    if prediction713 == 1
        consume_literal!(parser, "false")
        _t1395 = false
    else
        if prediction713 == 0
            consume_literal!(parser, "true")
            _t1396 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1395 = _t1396
    end
    return _t1395
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start718 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs714 = Proto.FragmentId[]
    cond715 = match_lookahead_literal(parser, ":", 0)
    while cond715
        _t1397 = parse_fragment_id(parser)
        item716 = _t1397
        push!(xs714, item716)
        cond715 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids717 = xs714
    consume_literal!(parser, ")")
    _t1398 = Proto.Sync(fragments=fragment_ids717)
    result719 = _t1398
    record_span!(parser, span_start718, "Sync")
    return result719
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start721 = span_start(parser)
    consume_literal!(parser, ":")
    symbol720 = consume_terminal!(parser, "SYMBOL")
    result722 = Proto.FragmentId(Vector{UInt8}(symbol720))
    record_span!(parser, span_start721, "FragmentId")
    return result722
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start725 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1400 = parse_epoch_writes(parser)
        _t1399 = _t1400
    else
        _t1399 = nothing
    end
    epoch_writes723 = _t1399
    if match_lookahead_literal(parser, "(", 0)
        _t1402 = parse_epoch_reads(parser)
        _t1401 = _t1402
    else
        _t1401 = nothing
    end
    epoch_reads724 = _t1401
    consume_literal!(parser, ")")
    _t1403 = Proto.Epoch(writes=(!isnothing(epoch_writes723) ? epoch_writes723 : Proto.Write[]), reads=(!isnothing(epoch_reads724) ? epoch_reads724 : Proto.Read[]))
    result726 = _t1403
    record_span!(parser, span_start725, "Epoch")
    return result726
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs727 = Proto.Write[]
    cond728 = match_lookahead_literal(parser, "(", 0)
    while cond728
        _t1404 = parse_write(parser)
        item729 = _t1404
        push!(xs727, item729)
        cond728 = match_lookahead_literal(parser, "(", 0)
    end
    writes730 = xs727
    consume_literal!(parser, ")")
    return writes730
end

function parse_write(parser::ParserState)::Proto.Write
    span_start736 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1406 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1407 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1408 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1409 = 2
                    else
                        _t1409 = -1
                    end
                    _t1408 = _t1409
                end
                _t1407 = _t1408
            end
            _t1406 = _t1407
        end
        _t1405 = _t1406
    else
        _t1405 = -1
    end
    prediction731 = _t1405
    if prediction731 == 3
        _t1411 = parse_snapshot(parser)
        snapshot735 = _t1411
        _t1412 = Proto.Write(write_type=OneOf(:snapshot, snapshot735))
        _t1410 = _t1412
    else
        if prediction731 == 2
            _t1414 = parse_context(parser)
            context734 = _t1414
            _t1415 = Proto.Write(write_type=OneOf(:context, context734))
            _t1413 = _t1415
        else
            if prediction731 == 1
                _t1417 = parse_undefine(parser)
                undefine733 = _t1417
                _t1418 = Proto.Write(write_type=OneOf(:undefine, undefine733))
                _t1416 = _t1418
            else
                if prediction731 == 0
                    _t1420 = parse_define(parser)
                    define732 = _t1420
                    _t1421 = Proto.Write(write_type=OneOf(:define, define732))
                    _t1419 = _t1421
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1416 = _t1419
            end
            _t1413 = _t1416
        end
        _t1410 = _t1413
    end
    result737 = _t1410
    record_span!(parser, span_start736, "Write")
    return result737
end

function parse_define(parser::ParserState)::Proto.Define
    span_start739 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1422 = parse_fragment(parser)
    fragment738 = _t1422
    consume_literal!(parser, ")")
    _t1423 = Proto.Define(fragment=fragment738)
    result740 = _t1423
    record_span!(parser, span_start739, "Define")
    return result740
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start746 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1424 = parse_new_fragment_id(parser)
    new_fragment_id741 = _t1424
    xs742 = Proto.Declaration[]
    cond743 = match_lookahead_literal(parser, "(", 0)
    while cond743
        _t1425 = parse_declaration(parser)
        item744 = _t1425
        push!(xs742, item744)
        cond743 = match_lookahead_literal(parser, "(", 0)
    end
    declarations745 = xs742
    consume_literal!(parser, ")")
    result747 = construct_fragment(parser, new_fragment_id741, declarations745)
    record_span!(parser, span_start746, "Fragment")
    return result747
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start749 = span_start(parser)
    _t1426 = parse_fragment_id(parser)
    fragment_id748 = _t1426
    start_fragment!(parser, fragment_id748)
    result750 = fragment_id748
    record_span!(parser, span_start749, "FragmentId")
    return result750
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start756 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1428 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1429 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1430 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1431 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1432 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1433 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1434 = 1
                                else
                                    _t1434 = -1
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
    else
        _t1427 = -1
    end
    prediction751 = _t1427
    if prediction751 == 3
        _t1436 = parse_data(parser)
        data755 = _t1436
        _t1437 = Proto.Declaration(declaration_type=OneOf(:data, data755))
        _t1435 = _t1437
    else
        if prediction751 == 2
            _t1439 = parse_constraint(parser)
            constraint754 = _t1439
            _t1440 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint754))
            _t1438 = _t1440
        else
            if prediction751 == 1
                _t1442 = parse_algorithm(parser)
                algorithm753 = _t1442
                _t1443 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm753))
                _t1441 = _t1443
            else
                if prediction751 == 0
                    _t1445 = parse_def(parser)
                    def752 = _t1445
                    _t1446 = Proto.Declaration(declaration_type=OneOf(:def, def752))
                    _t1444 = _t1446
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1441 = _t1444
            end
            _t1438 = _t1441
        end
        _t1435 = _t1438
    end
    result757 = _t1435
    record_span!(parser, span_start756, "Declaration")
    return result757
end

function parse_def(parser::ParserState)::Proto.Def
    span_start761 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1447 = parse_relation_id(parser)
    relation_id758 = _t1447
    _t1448 = parse_abstraction(parser)
    abstraction759 = _t1448
    if match_lookahead_literal(parser, "(", 0)
        _t1450 = parse_attrs(parser)
        _t1449 = _t1450
    else
        _t1449 = nothing
    end
    attrs760 = _t1449
    consume_literal!(parser, ")")
    _t1451 = Proto.Def(name=relation_id758, body=abstraction759, attrs=(!isnothing(attrs760) ? attrs760 : Proto.Attribute[]))
    result762 = _t1451
    record_span!(parser, span_start761, "Def")
    return result762
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start766 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1452 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1453 = 1
        else
            _t1453 = -1
        end
        _t1452 = _t1453
    end
    prediction763 = _t1452
    if prediction763 == 1
        uint128765 = consume_terminal!(parser, "UINT128")
        _t1454 = Proto.RelationId(uint128765.low, uint128765.high)
    else
        if prediction763 == 0
            consume_literal!(parser, ":")
            symbol764 = consume_terminal!(parser, "SYMBOL")
            _t1455 = relation_id_from_string(parser, symbol764)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1454 = _t1455
    end
    result767 = _t1454
    record_span!(parser, span_start766, "RelationId")
    return result767
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start770 = span_start(parser)
    consume_literal!(parser, "(")
    _t1456 = parse_bindings(parser)
    bindings768 = _t1456
    _t1457 = parse_formula(parser)
    formula769 = _t1457
    consume_literal!(parser, ")")
    _t1458 = Proto.Abstraction(vars=vcat(bindings768[1], !isnothing(bindings768[2]) ? bindings768[2] : []), value=formula769)
    result771 = _t1458
    record_span!(parser, span_start770, "Abstraction")
    return result771
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs772 = Proto.Binding[]
    cond773 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond773
        _t1459 = parse_binding(parser)
        item774 = _t1459
        push!(xs772, item774)
        cond773 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings775 = xs772
    if match_lookahead_literal(parser, "|", 0)
        _t1461 = parse_value_bindings(parser)
        _t1460 = _t1461
    else
        _t1460 = nothing
    end
    value_bindings776 = _t1460
    consume_literal!(parser, "]")
    return (bindings775, (!isnothing(value_bindings776) ? value_bindings776 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start779 = span_start(parser)
    symbol777 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1462 = parse_type(parser)
    type778 = _t1462
    _t1463 = Proto.Var(name=symbol777)
    _t1464 = Proto.Binding(var=_t1463, var"#type"=type778)
    result780 = _t1464
    record_span!(parser, span_start779, "Binding")
    return result780
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start796 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1465 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1466 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1467 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1468 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1469 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1470 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1471 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1472 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1473 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1474 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1475 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1476 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1477 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1478 = 9
                                                        else
                                                            _t1478 = -1
                                                        end
                                                        _t1477 = _t1478
                                                    end
                                                    _t1476 = _t1477
                                                end
                                                _t1475 = _t1476
                                            end
                                            _t1474 = _t1475
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
    prediction781 = _t1465
    if prediction781 == 13
        _t1480 = parse_uint32_type(parser)
        uint32_type795 = _t1480
        _t1481 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type795))
        _t1479 = _t1481
    else
        if prediction781 == 12
            _t1483 = parse_float32_type(parser)
            float32_type794 = _t1483
            _t1484 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type794))
            _t1482 = _t1484
        else
            if prediction781 == 11
                _t1486 = parse_int32_type(parser)
                int32_type793 = _t1486
                _t1487 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type793))
                _t1485 = _t1487
            else
                if prediction781 == 10
                    _t1489 = parse_boolean_type(parser)
                    boolean_type792 = _t1489
                    _t1490 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type792))
                    _t1488 = _t1490
                else
                    if prediction781 == 9
                        _t1492 = parse_decimal_type(parser)
                        decimal_type791 = _t1492
                        _t1493 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type791))
                        _t1491 = _t1493
                    else
                        if prediction781 == 8
                            _t1495 = parse_missing_type(parser)
                            missing_type790 = _t1495
                            _t1496 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type790))
                            _t1494 = _t1496
                        else
                            if prediction781 == 7
                                _t1498 = parse_datetime_type(parser)
                                datetime_type789 = _t1498
                                _t1499 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type789))
                                _t1497 = _t1499
                            else
                                if prediction781 == 6
                                    _t1501 = parse_date_type(parser)
                                    date_type788 = _t1501
                                    _t1502 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type788))
                                    _t1500 = _t1502
                                else
                                    if prediction781 == 5
                                        _t1504 = parse_int128_type(parser)
                                        int128_type787 = _t1504
                                        _t1505 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type787))
                                        _t1503 = _t1505
                                    else
                                        if prediction781 == 4
                                            _t1507 = parse_uint128_type(parser)
                                            uint128_type786 = _t1507
                                            _t1508 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type786))
                                            _t1506 = _t1508
                                        else
                                            if prediction781 == 3
                                                _t1510 = parse_float_type(parser)
                                                float_type785 = _t1510
                                                _t1511 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type785))
                                                _t1509 = _t1511
                                            else
                                                if prediction781 == 2
                                                    _t1513 = parse_int_type(parser)
                                                    int_type784 = _t1513
                                                    _t1514 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type784))
                                                    _t1512 = _t1514
                                                else
                                                    if prediction781 == 1
                                                        _t1516 = parse_string_type(parser)
                                                        string_type783 = _t1516
                                                        _t1517 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type783))
                                                        _t1515 = _t1517
                                                    else
                                                        if prediction781 == 0
                                                            _t1519 = parse_unspecified_type(parser)
                                                            unspecified_type782 = _t1519
                                                            _t1520 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type782))
                                                            _t1518 = _t1520
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                    _t1488 = _t1491
                end
                _t1485 = _t1488
            end
            _t1482 = _t1485
        end
        _t1479 = _t1482
    end
    result797 = _t1479
    record_span!(parser, span_start796, "Type")
    return result797
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start798 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1521 = Proto.UnspecifiedType()
    result799 = _t1521
    record_span!(parser, span_start798, "UnspecifiedType")
    return result799
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start800 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1522 = Proto.StringType()
    result801 = _t1522
    record_span!(parser, span_start800, "StringType")
    return result801
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start802 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1523 = Proto.IntType()
    result803 = _t1523
    record_span!(parser, span_start802, "IntType")
    return result803
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start804 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1524 = Proto.FloatType()
    result805 = _t1524
    record_span!(parser, span_start804, "FloatType")
    return result805
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start806 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1525 = Proto.UInt128Type()
    result807 = _t1525
    record_span!(parser, span_start806, "UInt128Type")
    return result807
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start808 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1526 = Proto.Int128Type()
    result809 = _t1526
    record_span!(parser, span_start808, "Int128Type")
    return result809
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start810 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1527 = Proto.DateType()
    result811 = _t1527
    record_span!(parser, span_start810, "DateType")
    return result811
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start812 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1528 = Proto.DateTimeType()
    result813 = _t1528
    record_span!(parser, span_start812, "DateTimeType")
    return result813
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start814 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1529 = Proto.MissingType()
    result815 = _t1529
    record_span!(parser, span_start814, "MissingType")
    return result815
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start818 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int816 = consume_terminal!(parser, "INT")
    int_3817 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1530 = Proto.DecimalType(precision=Int32(int816), scale=Int32(int_3817))
    result819 = _t1530
    record_span!(parser, span_start818, "DecimalType")
    return result819
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start820 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1531 = Proto.BooleanType()
    result821 = _t1531
    record_span!(parser, span_start820, "BooleanType")
    return result821
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start822 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1532 = Proto.Int32Type()
    result823 = _t1532
    record_span!(parser, span_start822, "Int32Type")
    return result823
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start824 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1533 = Proto.Float32Type()
    result825 = _t1533
    record_span!(parser, span_start824, "Float32Type")
    return result825
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start826 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1534 = Proto.UInt32Type()
    result827 = _t1534
    record_span!(parser, span_start826, "UInt32Type")
    return result827
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs828 = Proto.Binding[]
    cond829 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond829
        _t1535 = parse_binding(parser)
        item830 = _t1535
        push!(xs828, item830)
        cond829 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings831 = xs828
    return bindings831
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start846 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1537 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1538 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1539 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1540 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1541 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1542 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1543 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1544 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1545 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1546 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1547 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1548 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1549 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1550 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1551 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1552 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1553 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1554 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1555 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1556 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1557 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1558 = 10
                                                                                            else
                                                                                                _t1558 = -1
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
    else
        _t1536 = -1
    end
    prediction832 = _t1536
    if prediction832 == 12
        _t1560 = parse_cast(parser)
        cast845 = _t1560
        _t1561 = Proto.Formula(formula_type=OneOf(:cast, cast845))
        _t1559 = _t1561
    else
        if prediction832 == 11
            _t1563 = parse_rel_atom(parser)
            rel_atom844 = _t1563
            _t1564 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom844))
            _t1562 = _t1564
        else
            if prediction832 == 10
                _t1566 = parse_primitive(parser)
                primitive843 = _t1566
                _t1567 = Proto.Formula(formula_type=OneOf(:primitive, primitive843))
                _t1565 = _t1567
            else
                if prediction832 == 9
                    _t1569 = parse_pragma(parser)
                    pragma842 = _t1569
                    _t1570 = Proto.Formula(formula_type=OneOf(:pragma, pragma842))
                    _t1568 = _t1570
                else
                    if prediction832 == 8
                        _t1572 = parse_atom(parser)
                        atom841 = _t1572
                        _t1573 = Proto.Formula(formula_type=OneOf(:atom, atom841))
                        _t1571 = _t1573
                    else
                        if prediction832 == 7
                            _t1575 = parse_ffi(parser)
                            ffi840 = _t1575
                            _t1576 = Proto.Formula(formula_type=OneOf(:ffi, ffi840))
                            _t1574 = _t1576
                        else
                            if prediction832 == 6
                                _t1578 = parse_not(parser)
                                not839 = _t1578
                                _t1579 = Proto.Formula(formula_type=OneOf(:not, not839))
                                _t1577 = _t1579
                            else
                                if prediction832 == 5
                                    _t1581 = parse_disjunction(parser)
                                    disjunction838 = _t1581
                                    _t1582 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction838))
                                    _t1580 = _t1582
                                else
                                    if prediction832 == 4
                                        _t1584 = parse_conjunction(parser)
                                        conjunction837 = _t1584
                                        _t1585 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction837))
                                        _t1583 = _t1585
                                    else
                                        if prediction832 == 3
                                            _t1587 = parse_reduce(parser)
                                            reduce836 = _t1587
                                            _t1588 = Proto.Formula(formula_type=OneOf(:reduce, reduce836))
                                            _t1586 = _t1588
                                        else
                                            if prediction832 == 2
                                                _t1590 = parse_exists(parser)
                                                exists835 = _t1590
                                                _t1591 = Proto.Formula(formula_type=OneOf(:exists, exists835))
                                                _t1589 = _t1591
                                            else
                                                if prediction832 == 1
                                                    _t1593 = parse_false(parser)
                                                    false834 = _t1593
                                                    _t1594 = Proto.Formula(formula_type=OneOf(:disjunction, false834))
                                                    _t1592 = _t1594
                                                else
                                                    if prediction832 == 0
                                                        _t1596 = parse_true(parser)
                                                        true833 = _t1596
                                                        _t1597 = Proto.Formula(formula_type=OneOf(:conjunction, true833))
                                                        _t1595 = _t1597
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
                    _t1568 = _t1571
                end
                _t1565 = _t1568
            end
            _t1562 = _t1565
        end
        _t1559 = _t1562
    end
    result847 = _t1559
    record_span!(parser, span_start846, "Formula")
    return result847
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start848 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1598 = Proto.Conjunction(args=Proto.Formula[])
    result849 = _t1598
    record_span!(parser, span_start848, "Conjunction")
    return result849
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start850 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1599 = Proto.Disjunction(args=Proto.Formula[])
    result851 = _t1599
    record_span!(parser, span_start850, "Disjunction")
    return result851
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start854 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1600 = parse_bindings(parser)
    bindings852 = _t1600
    _t1601 = parse_formula(parser)
    formula853 = _t1601
    consume_literal!(parser, ")")
    _t1602 = Proto.Abstraction(vars=vcat(bindings852[1], !isnothing(bindings852[2]) ? bindings852[2] : []), value=formula853)
    _t1603 = Proto.Exists(body=_t1602)
    result855 = _t1603
    record_span!(parser, span_start854, "Exists")
    return result855
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start859 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1604 = parse_abstraction(parser)
    abstraction856 = _t1604
    _t1605 = parse_abstraction(parser)
    abstraction_3857 = _t1605
    _t1606 = parse_terms(parser)
    terms858 = _t1606
    consume_literal!(parser, ")")
    _t1607 = Proto.Reduce(op=abstraction856, body=abstraction_3857, terms=terms858)
    result860 = _t1607
    record_span!(parser, span_start859, "Reduce")
    return result860
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs861 = Proto.Term[]
    cond862 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond862
        _t1608 = parse_term(parser)
        item863 = _t1608
        push!(xs861, item863)
        cond862 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms864 = xs861
    consume_literal!(parser, ")")
    return terms864
end

function parse_term(parser::ParserState)::Proto.Term
    span_start868 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1609 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1610 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1611 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1612 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1613 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1614 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1615 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1616 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1617 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1618 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1619 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1620 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1621 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1622 = 1
                                                        else
                                                            _t1622 = -1
                                                        end
                                                        _t1621 = _t1622
                                                    end
                                                    _t1620 = _t1621
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
                _t1611 = _t1612
            end
            _t1610 = _t1611
        end
        _t1609 = _t1610
    end
    prediction865 = _t1609
    if prediction865 == 1
        _t1624 = parse_value(parser)
        value867 = _t1624
        _t1625 = Proto.Term(term_type=OneOf(:constant, value867))
        _t1623 = _t1625
    else
        if prediction865 == 0
            _t1627 = parse_var(parser)
            var866 = _t1627
            _t1628 = Proto.Term(term_type=OneOf(:var, var866))
            _t1626 = _t1628
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1623 = _t1626
    end
    result869 = _t1623
    record_span!(parser, span_start868, "Term")
    return result869
end

function parse_var(parser::ParserState)::Proto.Var
    span_start871 = span_start(parser)
    symbol870 = consume_terminal!(parser, "SYMBOL")
    _t1629 = Proto.Var(name=symbol870)
    result872 = _t1629
    record_span!(parser, span_start871, "Var")
    return result872
end

function parse_value(parser::ParserState)::Proto.Value
    span_start886 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1630 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1631 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1632 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1634 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1635 = 0
                        else
                            _t1635 = -1
                        end
                        _t1634 = _t1635
                    end
                    _t1633 = _t1634
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1636 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1637 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1638 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1639 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1640 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1641 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1642 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1643 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1644 = 10
                                                    else
                                                        _t1644 = -1
                                                    end
                                                    _t1643 = _t1644
                                                end
                                                _t1642 = _t1643
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
                    _t1633 = _t1636
                end
                _t1632 = _t1633
            end
            _t1631 = _t1632
        end
        _t1630 = _t1631
    end
    prediction873 = _t1630
    if prediction873 == 12
        _t1646 = parse_boolean_value(parser)
        boolean_value885 = _t1646
        _t1647 = Proto.Value(value=OneOf(:boolean_value, boolean_value885))
        _t1645 = _t1647
    else
        if prediction873 == 11
            consume_literal!(parser, "missing")
            _t1649 = Proto.MissingValue()
            _t1650 = Proto.Value(value=OneOf(:missing_value, _t1649))
            _t1648 = _t1650
        else
            if prediction873 == 10
                formatted_decimal884 = consume_terminal!(parser, "DECIMAL")
                _t1652 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal884))
                _t1651 = _t1652
            else
                if prediction873 == 9
                    formatted_int128883 = consume_terminal!(parser, "INT128")
                    _t1654 = Proto.Value(value=OneOf(:int128_value, formatted_int128883))
                    _t1653 = _t1654
                else
                    if prediction873 == 8
                        formatted_uint128882 = consume_terminal!(parser, "UINT128")
                        _t1656 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128882))
                        _t1655 = _t1656
                    else
                        if prediction873 == 7
                            formatted_uint32881 = consume_terminal!(parser, "UINT32")
                            _t1658 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32881))
                            _t1657 = _t1658
                        else
                            if prediction873 == 6
                                formatted_float880 = consume_terminal!(parser, "FLOAT")
                                _t1660 = Proto.Value(value=OneOf(:float_value, formatted_float880))
                                _t1659 = _t1660
                            else
                                if prediction873 == 5
                                    formatted_float32879 = consume_terminal!(parser, "FLOAT32")
                                    _t1662 = Proto.Value(value=OneOf(:float32_value, formatted_float32879))
                                    _t1661 = _t1662
                                else
                                    if prediction873 == 4
                                        formatted_int878 = consume_terminal!(parser, "INT")
                                        _t1664 = Proto.Value(value=OneOf(:int_value, formatted_int878))
                                        _t1663 = _t1664
                                    else
                                        if prediction873 == 3
                                            formatted_int32877 = consume_terminal!(parser, "INT32")
                                            _t1666 = Proto.Value(value=OneOf(:int32_value, formatted_int32877))
                                            _t1665 = _t1666
                                        else
                                            if prediction873 == 2
                                                formatted_string876 = consume_terminal!(parser, "STRING")
                                                _t1668 = Proto.Value(value=OneOf(:string_value, formatted_string876))
                                                _t1667 = _t1668
                                            else
                                                if prediction873 == 1
                                                    _t1670 = parse_datetime(parser)
                                                    datetime875 = _t1670
                                                    _t1671 = Proto.Value(value=OneOf(:datetime_value, datetime875))
                                                    _t1669 = _t1671
                                                else
                                                    if prediction873 == 0
                                                        _t1673 = parse_date(parser)
                                                        date874 = _t1673
                                                        _t1674 = Proto.Value(value=OneOf(:date_value, date874))
                                                        _t1672 = _t1674
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1669 = _t1672
                                                end
                                                _t1667 = _t1669
                                            end
                                            _t1665 = _t1667
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
            _t1648 = _t1651
        end
        _t1645 = _t1648
    end
    result887 = _t1645
    record_span!(parser, span_start886, "Value")
    return result887
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start891 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int888 = consume_terminal!(parser, "INT")
    formatted_int_3889 = consume_terminal!(parser, "INT")
    formatted_int_4890 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1675 = Proto.DateValue(year=Int32(formatted_int888), month=Int32(formatted_int_3889), day=Int32(formatted_int_4890))
    result892 = _t1675
    record_span!(parser, span_start891, "DateValue")
    return result892
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start900 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int893 = consume_terminal!(parser, "INT")
    formatted_int_3894 = consume_terminal!(parser, "INT")
    formatted_int_4895 = consume_terminal!(parser, "INT")
    formatted_int_5896 = consume_terminal!(parser, "INT")
    formatted_int_6897 = consume_terminal!(parser, "INT")
    formatted_int_7898 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1676 = consume_terminal!(parser, "INT")
    else
        _t1676 = nothing
    end
    formatted_int_8899 = _t1676
    consume_literal!(parser, ")")
    _t1677 = Proto.DateTimeValue(year=Int32(formatted_int893), month=Int32(formatted_int_3894), day=Int32(formatted_int_4895), hour=Int32(formatted_int_5896), minute=Int32(formatted_int_6897), second=Int32(formatted_int_7898), microsecond=Int32((!isnothing(formatted_int_8899) ? formatted_int_8899 : 0)))
    result901 = _t1677
    record_span!(parser, span_start900, "DateTimeValue")
    return result901
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start906 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs902 = Proto.Formula[]
    cond903 = match_lookahead_literal(parser, "(", 0)
    while cond903
        _t1678 = parse_formula(parser)
        item904 = _t1678
        push!(xs902, item904)
        cond903 = match_lookahead_literal(parser, "(", 0)
    end
    formulas905 = xs902
    consume_literal!(parser, ")")
    _t1679 = Proto.Conjunction(args=formulas905)
    result907 = _t1679
    record_span!(parser, span_start906, "Conjunction")
    return result907
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start912 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs908 = Proto.Formula[]
    cond909 = match_lookahead_literal(parser, "(", 0)
    while cond909
        _t1680 = parse_formula(parser)
        item910 = _t1680
        push!(xs908, item910)
        cond909 = match_lookahead_literal(parser, "(", 0)
    end
    formulas911 = xs908
    consume_literal!(parser, ")")
    _t1681 = Proto.Disjunction(args=formulas911)
    result913 = _t1681
    record_span!(parser, span_start912, "Disjunction")
    return result913
end

function parse_not(parser::ParserState)::Proto.Not
    span_start915 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1682 = parse_formula(parser)
    formula914 = _t1682
    consume_literal!(parser, ")")
    _t1683 = Proto.Not(arg=formula914)
    result916 = _t1683
    record_span!(parser, span_start915, "Not")
    return result916
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start920 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1684 = parse_name(parser)
    name917 = _t1684
    _t1685 = parse_ffi_args(parser)
    ffi_args918 = _t1685
    _t1686 = parse_terms(parser)
    terms919 = _t1686
    consume_literal!(parser, ")")
    _t1687 = Proto.FFI(name=name917, args=ffi_args918, terms=terms919)
    result921 = _t1687
    record_span!(parser, span_start920, "FFI")
    return result921
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol922 = consume_terminal!(parser, "SYMBOL")
    return symbol922
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs923 = Proto.Abstraction[]
    cond924 = match_lookahead_literal(parser, "(", 0)
    while cond924
        _t1688 = parse_abstraction(parser)
        item925 = _t1688
        push!(xs923, item925)
        cond924 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions926 = xs923
    consume_literal!(parser, ")")
    return abstractions926
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start932 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1689 = parse_relation_id(parser)
    relation_id927 = _t1689
    xs928 = Proto.Term[]
    cond929 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond929
        _t1690 = parse_term(parser)
        item930 = _t1690
        push!(xs928, item930)
        cond929 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms931 = xs928
    consume_literal!(parser, ")")
    _t1691 = Proto.Atom(name=relation_id927, terms=terms931)
    result933 = _t1691
    record_span!(parser, span_start932, "Atom")
    return result933
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start939 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1692 = parse_name(parser)
    name934 = _t1692
    xs935 = Proto.Term[]
    cond936 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond936
        _t1693 = parse_term(parser)
        item937 = _t1693
        push!(xs935, item937)
        cond936 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms938 = xs935
    consume_literal!(parser, ")")
    _t1694 = Proto.Pragma(name=name934, terms=terms938)
    result940 = _t1694
    record_span!(parser, span_start939, "Pragma")
    return result940
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start956 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1696 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1697 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1698 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1699 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1700 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1701 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1702 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1703 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1704 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1705 = 7
                                            else
                                                _t1705 = -1
                                            end
                                            _t1704 = _t1705
                                        end
                                        _t1703 = _t1704
                                    end
                                    _t1702 = _t1703
                                end
                                _t1701 = _t1702
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
    else
        _t1695 = -1
    end
    prediction941 = _t1695
    if prediction941 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1707 = parse_name(parser)
        name951 = _t1707
        xs952 = Proto.RelTerm[]
        cond953 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond953
            _t1708 = parse_rel_term(parser)
            item954 = _t1708
            push!(xs952, item954)
            cond953 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms955 = xs952
        consume_literal!(parser, ")")
        _t1709 = Proto.Primitive(name=name951, terms=rel_terms955)
        _t1706 = _t1709
    else
        if prediction941 == 8
            _t1711 = parse_divide(parser)
            divide950 = _t1711
            _t1710 = divide950
        else
            if prediction941 == 7
                _t1713 = parse_multiply(parser)
                multiply949 = _t1713
                _t1712 = multiply949
            else
                if prediction941 == 6
                    _t1715 = parse_minus(parser)
                    minus948 = _t1715
                    _t1714 = minus948
                else
                    if prediction941 == 5
                        _t1717 = parse_add(parser)
                        add947 = _t1717
                        _t1716 = add947
                    else
                        if prediction941 == 4
                            _t1719 = parse_gt_eq(parser)
                            gt_eq946 = _t1719
                            _t1718 = gt_eq946
                        else
                            if prediction941 == 3
                                _t1721 = parse_gt(parser)
                                gt945 = _t1721
                                _t1720 = gt945
                            else
                                if prediction941 == 2
                                    _t1723 = parse_lt_eq(parser)
                                    lt_eq944 = _t1723
                                    _t1722 = lt_eq944
                                else
                                    if prediction941 == 1
                                        _t1725 = parse_lt(parser)
                                        lt943 = _t1725
                                        _t1724 = lt943
                                    else
                                        if prediction941 == 0
                                            _t1727 = parse_eq(parser)
                                            eq942 = _t1727
                                            _t1726 = eq942
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1724 = _t1726
                                    end
                                    _t1722 = _t1724
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
        _t1706 = _t1710
    end
    result957 = _t1706
    record_span!(parser, span_start956, "Primitive")
    return result957
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1728 = parse_term(parser)
    term958 = _t1728
    _t1729 = parse_term(parser)
    term_3959 = _t1729
    consume_literal!(parser, ")")
    _t1730 = Proto.RelTerm(rel_term_type=OneOf(:term, term958))
    _t1731 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3959))
    _t1732 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1730, _t1731])
    result961 = _t1732
    record_span!(parser, span_start960, "Primitive")
    return result961
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start964 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1733 = parse_term(parser)
    term962 = _t1733
    _t1734 = parse_term(parser)
    term_3963 = _t1734
    consume_literal!(parser, ")")
    _t1735 = Proto.RelTerm(rel_term_type=OneOf(:term, term962))
    _t1736 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3963))
    _t1737 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1735, _t1736])
    result965 = _t1737
    record_span!(parser, span_start964, "Primitive")
    return result965
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start968 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1738 = parse_term(parser)
    term966 = _t1738
    _t1739 = parse_term(parser)
    term_3967 = _t1739
    consume_literal!(parser, ")")
    _t1740 = Proto.RelTerm(rel_term_type=OneOf(:term, term966))
    _t1741 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3967))
    _t1742 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1740, _t1741])
    result969 = _t1742
    record_span!(parser, span_start968, "Primitive")
    return result969
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start972 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1743 = parse_term(parser)
    term970 = _t1743
    _t1744 = parse_term(parser)
    term_3971 = _t1744
    consume_literal!(parser, ")")
    _t1745 = Proto.RelTerm(rel_term_type=OneOf(:term, term970))
    _t1746 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3971))
    _t1747 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1745, _t1746])
    result973 = _t1747
    record_span!(parser, span_start972, "Primitive")
    return result973
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start976 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1748 = parse_term(parser)
    term974 = _t1748
    _t1749 = parse_term(parser)
    term_3975 = _t1749
    consume_literal!(parser, ")")
    _t1750 = Proto.RelTerm(rel_term_type=OneOf(:term, term974))
    _t1751 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3975))
    _t1752 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1750, _t1751])
    result977 = _t1752
    record_span!(parser, span_start976, "Primitive")
    return result977
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start981 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1753 = parse_term(parser)
    term978 = _t1753
    _t1754 = parse_term(parser)
    term_3979 = _t1754
    _t1755 = parse_term(parser)
    term_4980 = _t1755
    consume_literal!(parser, ")")
    _t1756 = Proto.RelTerm(rel_term_type=OneOf(:term, term978))
    _t1757 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3979))
    _t1758 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4980))
    _t1759 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1756, _t1757, _t1758])
    result982 = _t1759
    record_span!(parser, span_start981, "Primitive")
    return result982
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start986 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1760 = parse_term(parser)
    term983 = _t1760
    _t1761 = parse_term(parser)
    term_3984 = _t1761
    _t1762 = parse_term(parser)
    term_4985 = _t1762
    consume_literal!(parser, ")")
    _t1763 = Proto.RelTerm(rel_term_type=OneOf(:term, term983))
    _t1764 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3984))
    _t1765 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4985))
    _t1766 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1763, _t1764, _t1765])
    result987 = _t1766
    record_span!(parser, span_start986, "Primitive")
    return result987
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start991 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1767 = parse_term(parser)
    term988 = _t1767
    _t1768 = parse_term(parser)
    term_3989 = _t1768
    _t1769 = parse_term(parser)
    term_4990 = _t1769
    consume_literal!(parser, ")")
    _t1770 = Proto.RelTerm(rel_term_type=OneOf(:term, term988))
    _t1771 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3989))
    _t1772 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4990))
    _t1773 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1770, _t1771, _t1772])
    result992 = _t1773
    record_span!(parser, span_start991, "Primitive")
    return result992
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start996 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1774 = parse_term(parser)
    term993 = _t1774
    _t1775 = parse_term(parser)
    term_3994 = _t1775
    _t1776 = parse_term(parser)
    term_4995 = _t1776
    consume_literal!(parser, ")")
    _t1777 = Proto.RelTerm(rel_term_type=OneOf(:term, term993))
    _t1778 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3994))
    _t1779 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4995))
    _t1780 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1777, _t1778, _t1779])
    result997 = _t1780
    record_span!(parser, span_start996, "Primitive")
    return result997
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1001 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1781 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1782 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1783 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1784 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1785 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1786 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1787 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1788 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1789 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1790 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1791 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1792 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1793 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1794 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1795 = 1
                                                            else
                                                                _t1795 = -1
                                                            end
                                                            _t1794 = _t1795
                                                        end
                                                        _t1793 = _t1794
                                                    end
                                                    _t1792 = _t1793
                                                end
                                                _t1791 = _t1792
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
    prediction998 = _t1781
    if prediction998 == 1
        _t1797 = parse_term(parser)
        term1000 = _t1797
        _t1798 = Proto.RelTerm(rel_term_type=OneOf(:term, term1000))
        _t1796 = _t1798
    else
        if prediction998 == 0
            _t1800 = parse_specialized_value(parser)
            specialized_value999 = _t1800
            _t1801 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value999))
            _t1799 = _t1801
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1796 = _t1799
    end
    result1002 = _t1796
    record_span!(parser, span_start1001, "RelTerm")
    return result1002
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1004 = span_start(parser)
    consume_literal!(parser, "#")
    _t1802 = parse_raw_value(parser)
    raw_value1003 = _t1802
    result1005 = raw_value1003
    record_span!(parser, span_start1004, "Value")
    return result1005
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1011 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1803 = parse_name(parser)
    name1006 = _t1803
    xs1007 = Proto.RelTerm[]
    cond1008 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1008
        _t1804 = parse_rel_term(parser)
        item1009 = _t1804
        push!(xs1007, item1009)
        cond1008 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1010 = xs1007
    consume_literal!(parser, ")")
    _t1805 = Proto.RelAtom(name=name1006, terms=rel_terms1010)
    result1012 = _t1805
    record_span!(parser, span_start1011, "RelAtom")
    return result1012
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1015 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1806 = parse_term(parser)
    term1013 = _t1806
    _t1807 = parse_term(parser)
    term_31014 = _t1807
    consume_literal!(parser, ")")
    _t1808 = Proto.Cast(input=term1013, result=term_31014)
    result1016 = _t1808
    record_span!(parser, span_start1015, "Cast")
    return result1016
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1017 = Proto.Attribute[]
    cond1018 = match_lookahead_literal(parser, "(", 0)
    while cond1018
        _t1809 = parse_attribute(parser)
        item1019 = _t1809
        push!(xs1017, item1019)
        cond1018 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1020 = xs1017
    consume_literal!(parser, ")")
    return attributes1020
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1026 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1810 = parse_name(parser)
    name1021 = _t1810
    xs1022 = Proto.Value[]
    cond1023 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1023
        _t1811 = parse_raw_value(parser)
        item1024 = _t1811
        push!(xs1022, item1024)
        cond1023 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1025 = xs1022
    consume_literal!(parser, ")")
    _t1812 = Proto.Attribute(name=name1021, args=raw_values1025)
    result1027 = _t1812
    record_span!(parser, span_start1026, "Attribute")
    return result1027
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1034 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1028 = Proto.RelationId[]
    cond1029 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1029
        _t1813 = parse_relation_id(parser)
        item1030 = _t1813
        push!(xs1028, item1030)
        cond1029 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1031 = xs1028
    _t1814 = parse_script(parser)
    script1032 = _t1814
    if match_lookahead_literal(parser, "(", 0)
        _t1816 = parse_attrs(parser)
        _t1815 = _t1816
    else
        _t1815 = nothing
    end
    attrs1033 = _t1815
    consume_literal!(parser, ")")
    _t1817 = Proto.Algorithm(var"#global"=relation_ids1031, body=script1032, attrs=(!isnothing(attrs1033) ? attrs1033 : Proto.Attribute[]))
    result1035 = _t1817
    record_span!(parser, span_start1034, "Algorithm")
    return result1035
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1040 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1036 = Proto.Construct[]
    cond1037 = match_lookahead_literal(parser, "(", 0)
    while cond1037
        _t1818 = parse_construct(parser)
        item1038 = _t1818
        push!(xs1036, item1038)
        cond1037 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1039 = xs1036
    consume_literal!(parser, ")")
    _t1819 = Proto.Script(constructs=constructs1039)
    result1041 = _t1819
    record_span!(parser, span_start1040, "Script")
    return result1041
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1045 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1821 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1822 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1823 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1824 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1825 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1826 = 1
                            else
                                _t1826 = -1
                            end
                            _t1825 = _t1826
                        end
                        _t1824 = _t1825
                    end
                    _t1823 = _t1824
                end
                _t1822 = _t1823
            end
            _t1821 = _t1822
        end
        _t1820 = _t1821
    else
        _t1820 = -1
    end
    prediction1042 = _t1820
    if prediction1042 == 1
        _t1828 = parse_instruction(parser)
        instruction1044 = _t1828
        _t1829 = Proto.Construct(construct_type=OneOf(:instruction, instruction1044))
        _t1827 = _t1829
    else
        if prediction1042 == 0
            _t1831 = parse_loop(parser)
            loop1043 = _t1831
            _t1832 = Proto.Construct(construct_type=OneOf(:loop, loop1043))
            _t1830 = _t1832
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1827 = _t1830
    end
    result1046 = _t1827
    record_span!(parser, span_start1045, "Construct")
    return result1046
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1050 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1833 = parse_init(parser)
    init1047 = _t1833
    _t1834 = parse_script(parser)
    script1048 = _t1834
    if match_lookahead_literal(parser, "(", 0)
        _t1836 = parse_attrs(parser)
        _t1835 = _t1836
    else
        _t1835 = nothing
    end
    attrs1049 = _t1835
    consume_literal!(parser, ")")
    _t1837 = Proto.Loop(init=init1047, body=script1048, attrs=(!isnothing(attrs1049) ? attrs1049 : Proto.Attribute[]))
    result1051 = _t1837
    record_span!(parser, span_start1050, "Loop")
    return result1051
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1052 = Proto.Instruction[]
    cond1053 = match_lookahead_literal(parser, "(", 0)
    while cond1053
        _t1838 = parse_instruction(parser)
        item1054 = _t1838
        push!(xs1052, item1054)
        cond1053 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1055 = xs1052
    consume_literal!(parser, ")")
    return instructions1055
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1062 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1840 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1841 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1842 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1843 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1844 = 0
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
    else
        _t1839 = -1
    end
    prediction1056 = _t1839
    if prediction1056 == 4
        _t1846 = parse_monus_def(parser)
        monus_def1061 = _t1846
        _t1847 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1061))
        _t1845 = _t1847
    else
        if prediction1056 == 3
            _t1849 = parse_monoid_def(parser)
            monoid_def1060 = _t1849
            _t1850 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1060))
            _t1848 = _t1850
        else
            if prediction1056 == 2
                _t1852 = parse_break(parser)
                break1059 = _t1852
                _t1853 = Proto.Instruction(instr_type=OneOf(:var"#break", break1059))
                _t1851 = _t1853
            else
                if prediction1056 == 1
                    _t1855 = parse_upsert(parser)
                    upsert1058 = _t1855
                    _t1856 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1058))
                    _t1854 = _t1856
                else
                    if prediction1056 == 0
                        _t1858 = parse_assign(parser)
                        assign1057 = _t1858
                        _t1859 = Proto.Instruction(instr_type=OneOf(:assign, assign1057))
                        _t1857 = _t1859
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1854 = _t1857
                end
                _t1851 = _t1854
            end
            _t1848 = _t1851
        end
        _t1845 = _t1848
    end
    result1063 = _t1845
    record_span!(parser, span_start1062, "Instruction")
    return result1063
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1067 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1860 = parse_relation_id(parser)
    relation_id1064 = _t1860
    _t1861 = parse_abstraction(parser)
    abstraction1065 = _t1861
    if match_lookahead_literal(parser, "(", 0)
        _t1863 = parse_attrs(parser)
        _t1862 = _t1863
    else
        _t1862 = nothing
    end
    attrs1066 = _t1862
    consume_literal!(parser, ")")
    _t1864 = Proto.Assign(name=relation_id1064, body=abstraction1065, attrs=(!isnothing(attrs1066) ? attrs1066 : Proto.Attribute[]))
    result1068 = _t1864
    record_span!(parser, span_start1067, "Assign")
    return result1068
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1072 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1865 = parse_relation_id(parser)
    relation_id1069 = _t1865
    _t1866 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1070 = _t1866
    if match_lookahead_literal(parser, "(", 0)
        _t1868 = parse_attrs(parser)
        _t1867 = _t1868
    else
        _t1867 = nothing
    end
    attrs1071 = _t1867
    consume_literal!(parser, ")")
    _t1869 = Proto.Upsert(name=relation_id1069, body=abstraction_with_arity1070[1], attrs=(!isnothing(attrs1071) ? attrs1071 : Proto.Attribute[]), value_arity=abstraction_with_arity1070[2])
    result1073 = _t1869
    record_span!(parser, span_start1072, "Upsert")
    return result1073
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1870 = parse_bindings(parser)
    bindings1074 = _t1870
    _t1871 = parse_formula(parser)
    formula1075 = _t1871
    consume_literal!(parser, ")")
    _t1872 = Proto.Abstraction(vars=vcat(bindings1074[1], !isnothing(bindings1074[2]) ? bindings1074[2] : []), value=formula1075)
    return (_t1872, length(bindings1074[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1079 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1873 = parse_relation_id(parser)
    relation_id1076 = _t1873
    _t1874 = parse_abstraction(parser)
    abstraction1077 = _t1874
    if match_lookahead_literal(parser, "(", 0)
        _t1876 = parse_attrs(parser)
        _t1875 = _t1876
    else
        _t1875 = nothing
    end
    attrs1078 = _t1875
    consume_literal!(parser, ")")
    _t1877 = Proto.Break(name=relation_id1076, body=abstraction1077, attrs=(!isnothing(attrs1078) ? attrs1078 : Proto.Attribute[]))
    result1080 = _t1877
    record_span!(parser, span_start1079, "Break")
    return result1080
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1085 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1878 = parse_monoid(parser)
    monoid1081 = _t1878
    _t1879 = parse_relation_id(parser)
    relation_id1082 = _t1879
    _t1880 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1083 = _t1880
    if match_lookahead_literal(parser, "(", 0)
        _t1882 = parse_attrs(parser)
        _t1881 = _t1882
    else
        _t1881 = nothing
    end
    attrs1084 = _t1881
    consume_literal!(parser, ")")
    _t1883 = Proto.MonoidDef(monoid=monoid1081, name=relation_id1082, body=abstraction_with_arity1083[1], attrs=(!isnothing(attrs1084) ? attrs1084 : Proto.Attribute[]), value_arity=abstraction_with_arity1083[2])
    result1086 = _t1883
    record_span!(parser, span_start1085, "MonoidDef")
    return result1086
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1092 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1885 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1886 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1887 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1888 = 2
                    else
                        _t1888 = -1
                    end
                    _t1887 = _t1888
                end
                _t1886 = _t1887
            end
            _t1885 = _t1886
        end
        _t1884 = _t1885
    else
        _t1884 = -1
    end
    prediction1087 = _t1884
    if prediction1087 == 3
        _t1890 = parse_sum_monoid(parser)
        sum_monoid1091 = _t1890
        _t1891 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1091))
        _t1889 = _t1891
    else
        if prediction1087 == 2
            _t1893 = parse_max_monoid(parser)
            max_monoid1090 = _t1893
            _t1894 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1090))
            _t1892 = _t1894
        else
            if prediction1087 == 1
                _t1896 = parse_min_monoid(parser)
                min_monoid1089 = _t1896
                _t1897 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1089))
                _t1895 = _t1897
            else
                if prediction1087 == 0
                    _t1899 = parse_or_monoid(parser)
                    or_monoid1088 = _t1899
                    _t1900 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1088))
                    _t1898 = _t1900
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1895 = _t1898
            end
            _t1892 = _t1895
        end
        _t1889 = _t1892
    end
    result1093 = _t1889
    record_span!(parser, span_start1092, "Monoid")
    return result1093
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1094 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1901 = Proto.OrMonoid()
    result1095 = _t1901
    record_span!(parser, span_start1094, "OrMonoid")
    return result1095
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1097 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1902 = parse_type(parser)
    type1096 = _t1902
    consume_literal!(parser, ")")
    _t1903 = Proto.MinMonoid(var"#type"=type1096)
    result1098 = _t1903
    record_span!(parser, span_start1097, "MinMonoid")
    return result1098
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1100 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1904 = parse_type(parser)
    type1099 = _t1904
    consume_literal!(parser, ")")
    _t1905 = Proto.MaxMonoid(var"#type"=type1099)
    result1101 = _t1905
    record_span!(parser, span_start1100, "MaxMonoid")
    return result1101
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1103 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1906 = parse_type(parser)
    type1102 = _t1906
    consume_literal!(parser, ")")
    _t1907 = Proto.SumMonoid(var"#type"=type1102)
    result1104 = _t1907
    record_span!(parser, span_start1103, "SumMonoid")
    return result1104
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1109 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1908 = parse_monoid(parser)
    monoid1105 = _t1908
    _t1909 = parse_relation_id(parser)
    relation_id1106 = _t1909
    _t1910 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1107 = _t1910
    if match_lookahead_literal(parser, "(", 0)
        _t1912 = parse_attrs(parser)
        _t1911 = _t1912
    else
        _t1911 = nothing
    end
    attrs1108 = _t1911
    consume_literal!(parser, ")")
    _t1913 = Proto.MonusDef(monoid=monoid1105, name=relation_id1106, body=abstraction_with_arity1107[1], attrs=(!isnothing(attrs1108) ? attrs1108 : Proto.Attribute[]), value_arity=abstraction_with_arity1107[2])
    result1110 = _t1913
    record_span!(parser, span_start1109, "MonusDef")
    return result1110
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1115 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1914 = parse_relation_id(parser)
    relation_id1111 = _t1914
    _t1915 = parse_abstraction(parser)
    abstraction1112 = _t1915
    _t1916 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1113 = _t1916
    _t1917 = parse_functional_dependency_values(parser)
    functional_dependency_values1114 = _t1917
    consume_literal!(parser, ")")
    _t1918 = Proto.FunctionalDependency(guard=abstraction1112, keys=functional_dependency_keys1113, values=functional_dependency_values1114)
    _t1919 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1918), name=relation_id1111)
    result1116 = _t1919
    record_span!(parser, span_start1115, "Constraint")
    return result1116
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1117 = Proto.Var[]
    cond1118 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1118
        _t1920 = parse_var(parser)
        item1119 = _t1920
        push!(xs1117, item1119)
        cond1118 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1120 = xs1117
    consume_literal!(parser, ")")
    return vars1120
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1121 = Proto.Var[]
    cond1122 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1122
        _t1921 = parse_var(parser)
        item1123 = _t1921
        push!(xs1121, item1123)
        cond1122 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1124 = xs1121
    consume_literal!(parser, ")")
    return vars1124
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1130 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1923 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1924 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1925 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1926 = 1
                    else
                        _t1926 = -1
                    end
                    _t1925 = _t1926
                end
                _t1924 = _t1925
            end
            _t1923 = _t1924
        end
        _t1922 = _t1923
    else
        _t1922 = -1
    end
    prediction1125 = _t1922
    if prediction1125 == 3
        _t1928 = parse_iceberg_data(parser)
        iceberg_data1129 = _t1928
        _t1929 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1129))
        _t1927 = _t1929
    else
        if prediction1125 == 2
            _t1931 = parse_csv_data(parser)
            csv_data1128 = _t1931
            _t1932 = Proto.Data(data_type=OneOf(:csv_data, csv_data1128))
            _t1930 = _t1932
        else
            if prediction1125 == 1
                _t1934 = parse_betree_relation(parser)
                betree_relation1127 = _t1934
                _t1935 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1127))
                _t1933 = _t1935
            else
                if prediction1125 == 0
                    _t1937 = parse_edb(parser)
                    edb1126 = _t1937
                    _t1938 = Proto.Data(data_type=OneOf(:edb, edb1126))
                    _t1936 = _t1938
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1933 = _t1936
            end
            _t1930 = _t1933
        end
        _t1927 = _t1930
    end
    result1131 = _t1927
    record_span!(parser, span_start1130, "Data")
    return result1131
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1135 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1939 = parse_relation_id(parser)
    relation_id1132 = _t1939
    _t1940 = parse_edb_path(parser)
    edb_path1133 = _t1940
    _t1941 = parse_edb_types(parser)
    edb_types1134 = _t1941
    consume_literal!(parser, ")")
    _t1942 = Proto.EDB(target_id=relation_id1132, path=edb_path1133, types=edb_types1134)
    result1136 = _t1942
    record_span!(parser, span_start1135, "EDB")
    return result1136
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1137 = String[]
    cond1138 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1138
        item1139 = consume_terminal!(parser, "STRING")
        push!(xs1137, item1139)
        cond1138 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1140 = xs1137
    consume_literal!(parser, "]")
    return strings1140
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1141 = Proto.var"#Type"[]
    cond1142 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1142
        _t1943 = parse_type(parser)
        item1143 = _t1943
        push!(xs1141, item1143)
        cond1142 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1144 = xs1141
    consume_literal!(parser, "]")
    return types1144
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1147 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1944 = parse_relation_id(parser)
    relation_id1145 = _t1944
    _t1945 = parse_betree_info(parser)
    betree_info1146 = _t1945
    consume_literal!(parser, ")")
    _t1946 = Proto.BeTreeRelation(name=relation_id1145, relation_info=betree_info1146)
    result1148 = _t1946
    record_span!(parser, span_start1147, "BeTreeRelation")
    return result1148
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1152 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1947 = parse_betree_info_key_types(parser)
    betree_info_key_types1149 = _t1947
    _t1948 = parse_betree_info_value_types(parser)
    betree_info_value_types1150 = _t1948
    _t1949 = parse_config_dict(parser)
    config_dict1151 = _t1949
    consume_literal!(parser, ")")
    _t1950 = construct_betree_info(parser, betree_info_key_types1149, betree_info_value_types1150, config_dict1151)
    result1153 = _t1950
    record_span!(parser, span_start1152, "BeTreeInfo")
    return result1153
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1154 = Proto.var"#Type"[]
    cond1155 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1155
        _t1951 = parse_type(parser)
        item1156 = _t1951
        push!(xs1154, item1156)
        cond1155 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1157 = xs1154
    consume_literal!(parser, ")")
    return types1157
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1158 = Proto.var"#Type"[]
    cond1159 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1159
        _t1952 = parse_type(parser)
        item1160 = _t1952
        push!(xs1158, item1160)
        cond1159 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1161 = xs1158
    consume_literal!(parser, ")")
    return types1161
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1166 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1953 = parse_csvlocator(parser)
    csvlocator1162 = _t1953
    _t1954 = parse_csv_config(parser)
    csv_config1163 = _t1954
    _t1955 = parse_gnf_columns(parser)
    gnf_columns1164 = _t1955
    _t1956 = parse_csv_asof(parser)
    csv_asof1165 = _t1956
    consume_literal!(parser, ")")
    _t1957 = Proto.CSVData(locator=csvlocator1162, config=csv_config1163, columns=gnf_columns1164, asof=csv_asof1165)
    result1167 = _t1957
    record_span!(parser, span_start1166, "CSVData")
    return result1167
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1170 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1959 = parse_csv_locator_paths(parser)
        _t1958 = _t1959
    else
        _t1958 = nothing
    end
    csv_locator_paths1168 = _t1958
    if match_lookahead_literal(parser, "(", 0)
        _t1961 = parse_csv_locator_inline_data(parser)
        _t1960 = _t1961
    else
        _t1960 = nothing
    end
    csv_locator_inline_data1169 = _t1960
    consume_literal!(parser, ")")
    _t1962 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1168) ? csv_locator_paths1168 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1169) ? csv_locator_inline_data1169 : "")))
    result1171 = _t1962
    record_span!(parser, span_start1170, "CSVLocator")
    return result1171
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1172 = String[]
    cond1173 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1173
        item1174 = consume_terminal!(parser, "STRING")
        push!(xs1172, item1174)
        cond1173 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1175 = xs1172
    consume_literal!(parser, ")")
    return strings1175
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1176 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1176
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1179 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1963 = parse_config_dict(parser)
    config_dict1177 = _t1963
    if match_lookahead_literal(parser, "(", 0)
        _t1965 = parse_csv_storage_integration(parser)
        _t1964 = _t1965
    else
        _t1964 = nothing
    end
    csv_storage_integration1178 = _t1964
    consume_literal!(parser, ")")
    _t1966 = construct_csv_config(parser, config_dict1177, csv_storage_integration1178)
    result1180 = _t1966
    record_span!(parser, span_start1179, "CSVConfig")
    return result1180
end

function parse_csv_storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t1967 = parse_config_dict(parser)
    config_dict1181 = _t1967
    consume_literal!(parser, ")")
    return config_dict1181
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1182 = Proto.GNFColumn[]
    cond1183 = match_lookahead_literal(parser, "(", 0)
    while cond1183
        _t1968 = parse_gnf_column(parser)
        item1184 = _t1968
        push!(xs1182, item1184)
        cond1183 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1185 = xs1182
    consume_literal!(parser, ")")
    return gnf_columns1185
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1192 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1969 = parse_gnf_column_path(parser)
    gnf_column_path1186 = _t1969
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1971 = parse_relation_id(parser)
        _t1970 = _t1971
    else
        _t1970 = nothing
    end
    relation_id1187 = _t1970
    consume_literal!(parser, "[")
    xs1188 = Proto.var"#Type"[]
    cond1189 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1189
        _t1972 = parse_type(parser)
        item1190 = _t1972
        push!(xs1188, item1190)
        cond1189 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1191 = xs1188
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1973 = Proto.GNFColumn(column_path=gnf_column_path1186, target_id=relation_id1187, types=types1191)
    result1193 = _t1973
    record_span!(parser, span_start1192, "GNFColumn")
    return result1193
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1974 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1975 = 0
        else
            _t1975 = -1
        end
        _t1974 = _t1975
    end
    prediction1194 = _t1974
    if prediction1194 == 1
        consume_literal!(parser, "[")
        xs1196 = String[]
        cond1197 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1197
            item1198 = consume_terminal!(parser, "STRING")
            push!(xs1196, item1198)
            cond1197 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1199 = xs1196
        consume_literal!(parser, "]")
        _t1976 = strings1199
    else
        if prediction1194 == 0
            string1195 = consume_terminal!(parser, "STRING")
            _t1977 = String[string1195]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1976 = _t1977
    end
    return _t1976
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1200 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1200
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1207 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1978 = parse_iceberg_locator(parser)
    iceberg_locator1201 = _t1978
    _t1979 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1202 = _t1979
    _t1980 = parse_gnf_columns(parser)
    gnf_columns1203 = _t1980
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1982 = parse_iceberg_from_snapshot(parser)
        _t1981 = _t1982
    else
        _t1981 = nothing
    end
    iceberg_from_snapshot1204 = _t1981
    if match_lookahead_literal(parser, "(", 0)
        _t1984 = parse_iceberg_to_snapshot(parser)
        _t1983 = _t1984
    else
        _t1983 = nothing
    end
    iceberg_to_snapshot1205 = _t1983
    _t1985 = parse_boolean_value(parser)
    boolean_value1206 = _t1985
    consume_literal!(parser, ")")
    _t1986 = construct_iceberg_data(parser, iceberg_locator1201, iceberg_catalog_config1202, gnf_columns1203, iceberg_from_snapshot1204, iceberg_to_snapshot1205, boolean_value1206)
    result1208 = _t1986
    record_span!(parser, span_start1207, "IcebergData")
    return result1208
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1212 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t1987 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1209 = _t1987
    _t1988 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1210 = _t1988
    _t1989 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1211 = _t1989
    consume_literal!(parser, ")")
    _t1990 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1209, namespace=iceberg_locator_namespace1210, warehouse=iceberg_locator_warehouse1211)
    result1213 = _t1990
    record_span!(parser, span_start1212, "IcebergLocator")
    return result1213
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1214 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1214
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1215 = String[]
    cond1216 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1216
        item1217 = consume_terminal!(parser, "STRING")
        push!(xs1215, item1217)
        cond1216 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1218 = xs1215
    consume_literal!(parser, ")")
    return strings1218
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1219 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1219
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1224 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t1991 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1220 = _t1991
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1993 = parse_iceberg_catalog_config_scope(parser)
        _t1992 = _t1993
    else
        _t1992 = nothing
    end
    iceberg_catalog_config_scope1221 = _t1992
    _t1994 = parse_iceberg_properties(parser)
    iceberg_properties1222 = _t1994
    _t1995 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1223 = _t1995
    consume_literal!(parser, ")")
    _t1996 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1220, iceberg_catalog_config_scope1221, iceberg_properties1222, iceberg_auth_properties1223)
    result1225 = _t1996
    record_span!(parser, span_start1224, "IcebergCatalogConfig")
    return result1225
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1226 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1226
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1227 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1227
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1228 = Tuple{String, String}[]
    cond1229 = match_lookahead_literal(parser, "(", 0)
    while cond1229
        _t1997 = parse_iceberg_property_entry(parser)
        item1230 = _t1997
        push!(xs1228, item1230)
        cond1229 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1231 = xs1228
    consume_literal!(parser, ")")
    return iceberg_property_entrys1231
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1232 = consume_terminal!(parser, "STRING")
    string_31233 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1232, string_31233,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1234 = Tuple{String, String}[]
    cond1235 = match_lookahead_literal(parser, "(", 0)
    while cond1235
        _t1998 = parse_iceberg_masked_property_entry(parser)
        item1236 = _t1998
        push!(xs1234, item1236)
        cond1235 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1237 = xs1234
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1237
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1238 = consume_terminal!(parser, "STRING")
    string_31239 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1238, string_31239,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1240 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1240
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1241 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1241
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1243 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1999 = parse_fragment_id(parser)
    fragment_id1242 = _t1999
    consume_literal!(parser, ")")
    _t2000 = Proto.Undefine(fragment_id=fragment_id1242)
    result1244 = _t2000
    record_span!(parser, span_start1243, "Undefine")
    return result1244
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1249 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1245 = Proto.RelationId[]
    cond1246 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1246
        _t2001 = parse_relation_id(parser)
        item1247 = _t2001
        push!(xs1245, item1247)
        cond1246 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1248 = xs1245
    consume_literal!(parser, ")")
    _t2002 = Proto.Context(relations=relation_ids1248)
    result1250 = _t2002
    record_span!(parser, span_start1249, "Context")
    return result1250
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1256 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2003 = parse_edb_path(parser)
    edb_path1251 = _t2003
    xs1252 = Proto.SnapshotMapping[]
    cond1253 = match_lookahead_literal(parser, "[", 0)
    while cond1253
        _t2004 = parse_snapshot_mapping(parser)
        item1254 = _t2004
        push!(xs1252, item1254)
        cond1253 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1255 = xs1252
    consume_literal!(parser, ")")
    _t2005 = Proto.Snapshot(mappings=snapshot_mappings1255, prefix=edb_path1251)
    result1257 = _t2005
    record_span!(parser, span_start1256, "Snapshot")
    return result1257
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1260 = span_start(parser)
    _t2006 = parse_edb_path(parser)
    edb_path1258 = _t2006
    _t2007 = parse_relation_id(parser)
    relation_id1259 = _t2007
    _t2008 = Proto.SnapshotMapping(destination_path=edb_path1258, source_relation=relation_id1259)
    result1261 = _t2008
    record_span!(parser, span_start1260, "SnapshotMapping")
    return result1261
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1262 = Proto.Read[]
    cond1263 = match_lookahead_literal(parser, "(", 0)
    while cond1263
        _t2009 = parse_read(parser)
        item1264 = _t2009
        push!(xs1262, item1264)
        cond1263 = match_lookahead_literal(parser, "(", 0)
    end
    reads1265 = xs1262
    consume_literal!(parser, ")")
    return reads1265
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1272 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2011 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2012 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2013 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2014 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2015 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2016 = 3
                            else
                                _t2016 = -1
                            end
                            _t2015 = _t2016
                        end
                        _t2014 = _t2015
                    end
                    _t2013 = _t2014
                end
                _t2012 = _t2013
            end
            _t2011 = _t2012
        end
        _t2010 = _t2011
    else
        _t2010 = -1
    end
    prediction1266 = _t2010
    if prediction1266 == 4
        _t2018 = parse_export(parser)
        export1271 = _t2018
        _t2019 = Proto.Read(read_type=OneOf(:var"#export", export1271))
        _t2017 = _t2019
    else
        if prediction1266 == 3
            _t2021 = parse_abort(parser)
            abort1270 = _t2021
            _t2022 = Proto.Read(read_type=OneOf(:abort, abort1270))
            _t2020 = _t2022
        else
            if prediction1266 == 2
                _t2024 = parse_what_if(parser)
                what_if1269 = _t2024
                _t2025 = Proto.Read(read_type=OneOf(:what_if, what_if1269))
                _t2023 = _t2025
            else
                if prediction1266 == 1
                    _t2027 = parse_output(parser)
                    output1268 = _t2027
                    _t2028 = Proto.Read(read_type=OneOf(:output, output1268))
                    _t2026 = _t2028
                else
                    if prediction1266 == 0
                        _t2030 = parse_demand(parser)
                        demand1267 = _t2030
                        _t2031 = Proto.Read(read_type=OneOf(:demand, demand1267))
                        _t2029 = _t2031
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2026 = _t2029
                end
                _t2023 = _t2026
            end
            _t2020 = _t2023
        end
        _t2017 = _t2020
    end
    result1273 = _t2017
    record_span!(parser, span_start1272, "Read")
    return result1273
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1275 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2032 = parse_relation_id(parser)
    relation_id1274 = _t2032
    consume_literal!(parser, ")")
    _t2033 = Proto.Demand(relation_id=relation_id1274)
    result1276 = _t2033
    record_span!(parser, span_start1275, "Demand")
    return result1276
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1279 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2034 = parse_name(parser)
    name1277 = _t2034
    _t2035 = parse_relation_id(parser)
    relation_id1278 = _t2035
    consume_literal!(parser, ")")
    _t2036 = Proto.Output(name=name1277, relation_id=relation_id1278)
    result1280 = _t2036
    record_span!(parser, span_start1279, "Output")
    return result1280
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1283 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2037 = parse_name(parser)
    name1281 = _t2037
    _t2038 = parse_epoch(parser)
    epoch1282 = _t2038
    consume_literal!(parser, ")")
    _t2039 = Proto.WhatIf(branch=name1281, epoch=epoch1282)
    result1284 = _t2039
    record_span!(parser, span_start1283, "WhatIf")
    return result1284
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1287 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2041 = parse_name(parser)
        _t2040 = _t2041
    else
        _t2040 = nothing
    end
    name1285 = _t2040
    _t2042 = parse_relation_id(parser)
    relation_id1286 = _t2042
    consume_literal!(parser, ")")
    _t2043 = Proto.Abort(name=(!isnothing(name1285) ? name1285 : "abort"), relation_id=relation_id1286)
    result1288 = _t2043
    record_span!(parser, span_start1287, "Abort")
    return result1288
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1292 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2045 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2046 = 0
            else
                _t2046 = -1
            end
            _t2045 = _t2046
        end
        _t2044 = _t2045
    else
        _t2044 = -1
    end
    prediction1289 = _t2044
    if prediction1289 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2048 = parse_export_iceberg_config(parser)
        export_iceberg_config1291 = _t2048
        consume_literal!(parser, ")")
        _t2049 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1291))
        _t2047 = _t2049
    else
        if prediction1289 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2051 = parse_export_csv_config(parser)
            export_csv_config1290 = _t2051
            consume_literal!(parser, ")")
            _t2052 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1290))
            _t2050 = _t2052
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2047 = _t2050
    end
    result1293 = _t2047
    record_span!(parser, span_start1292, "Export")
    return result1293
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1301 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2054 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2055 = 1
            else
                _t2055 = -1
            end
            _t2054 = _t2055
        end
        _t2053 = _t2054
    else
        _t2053 = -1
    end
    prediction1294 = _t2053
    if prediction1294 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2057 = parse_export_csv_path(parser)
        export_csv_path1298 = _t2057
        _t2058 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1299 = _t2058
        _t2059 = parse_config_dict(parser)
        config_dict1300 = _t2059
        consume_literal!(parser, ")")
        _t2060 = construct_export_csv_config(parser, export_csv_path1298, export_csv_columns_list1299, config_dict1300)
        _t2056 = _t2060
    else
        if prediction1294 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2062 = parse_export_csv_path(parser)
            export_csv_path1295 = _t2062
            _t2063 = parse_export_csv_source(parser)
            export_csv_source1296 = _t2063
            _t2064 = parse_csv_config(parser)
            csv_config1297 = _t2064
            consume_literal!(parser, ")")
            _t2065 = construct_export_csv_config_with_source(parser, export_csv_path1295, export_csv_source1296, csv_config1297)
            _t2061 = _t2065
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2056 = _t2061
    end
    result1302 = _t2056
    record_span!(parser, span_start1301, "ExportCSVConfig")
    return result1302
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1303 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1303
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1310 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2067 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
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
    prediction1304 = _t2066
    if prediction1304 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2070 = parse_relation_id(parser)
        relation_id1309 = _t2070
        consume_literal!(parser, ")")
        _t2071 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1309))
        _t2069 = _t2071
    else
        if prediction1304 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1305 = Proto.ExportCSVColumn[]
            cond1306 = match_lookahead_literal(parser, "(", 0)
            while cond1306
                _t2073 = parse_export_csv_column(parser)
                item1307 = _t2073
                push!(xs1305, item1307)
                cond1306 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1308 = xs1305
            consume_literal!(parser, ")")
            _t2074 = Proto.ExportCSVColumns(columns=export_csv_columns1308)
            _t2075 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2074))
            _t2072 = _t2075
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2069 = _t2072
    end
    result1311 = _t2069
    record_span!(parser, span_start1310, "ExportCSVSource")
    return result1311
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1314 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1312 = consume_terminal!(parser, "STRING")
    _t2076 = parse_relation_id(parser)
    relation_id1313 = _t2076
    consume_literal!(parser, ")")
    _t2077 = Proto.ExportCSVColumn(column_name=string1312, column_data=relation_id1313)
    result1315 = _t2077
    record_span!(parser, span_start1314, "ExportCSVColumn")
    return result1315
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1316 = Proto.ExportCSVColumn[]
    cond1317 = match_lookahead_literal(parser, "(", 0)
    while cond1317
        _t2078 = parse_export_csv_column(parser)
        item1318 = _t2078
        push!(xs1316, item1318)
        cond1317 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1319 = xs1316
    consume_literal!(parser, ")")
    return export_csv_columns1319
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1325 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2079 = parse_iceberg_locator(parser)
    iceberg_locator1320 = _t2079
    _t2080 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1321 = _t2080
    _t2081 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1322 = _t2081
    _t2082 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1323 = _t2082
    if match_lookahead_literal(parser, "{", 0)
        _t2084 = parse_config_dict(parser)
        _t2083 = _t2084
    else
        _t2083 = nothing
    end
    config_dict1324 = _t2083
    consume_literal!(parser, ")")
    _t2085 = construct_export_iceberg_config_full(parser, iceberg_locator1320, iceberg_catalog_config1321, export_iceberg_table_def1322, iceberg_table_properties1323, config_dict1324)
    result1326 = _t2085
    record_span!(parser, span_start1325, "ExportIcebergConfig")
    return result1326
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1328 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2086 = parse_relation_id(parser)
    relation_id1327 = _t2086
    consume_literal!(parser, ")")
    result1329 = relation_id1327
    record_span!(parser, span_start1328, "RelationId")
    return result1329
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1330 = Tuple{String, String}[]
    cond1331 = match_lookahead_literal(parser, "(", 0)
    while cond1331
        _t2087 = parse_iceberg_property_entry(parser)
        item1332 = _t2087
        push!(xs1330, item1332)
        cond1331 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1333 = xs1330
    consume_literal!(parser, ")")
    return iceberg_property_entrys1333
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
