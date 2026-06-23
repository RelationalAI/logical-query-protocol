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
        _t2100 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2101 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2102 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2103 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2104 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2105 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2106 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2107 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2108 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2109 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2109
    _t2110 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2110
    _t2111 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2111
    _t2112 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2112
    _t2113 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2113
    _t2114 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2114
    _t2115 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2115
    _t2116 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2116
    _t2117 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2117
    _t2118 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2118
    _t2119 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2119
    _t2120 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2120
    _t2121 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2121
    _t2122 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2122
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2123 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2124 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2125 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2126 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2127 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2128 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2129 = Proto.StorageIntegration(provider=_t2124, azure_sas_token=_t2125, s3_region=_t2126, s3_access_key_id=_t2127, s3_secret_access_key=_t2128)
    return _t2129
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2130 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2130
    _t2131 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2131
    _t2132 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2132
    _t2133 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2133
    _t2134 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2134
    _t2135 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2135
    _t2136 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2136
    _t2137 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2137
    _t2138 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2138
    _t2139 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2139
    _t2140 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2140
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2141 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2141
    _t2142 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2142
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
    _t2143 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2143
    _t2144 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2144
    _t2145 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2145
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2146 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2146
    _t2147 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2147
    _t2148 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2148
    _t2149 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2149
    _t2150 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2150
    _t2151 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2151
    _t2152 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2152
    _t2153 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2153
end

function construct_export_csv_config_with_location(parser::ParserState, location::Tuple{String, String}, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2154 = Proto.ExportCSVConfig(path=location[1], transaction_output_name=location[2], csv_source=csv_source, csv_config=csv_config)
    return _t2154
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2155 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2155
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2156 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2156
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2157 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2157
    _t2158 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2158
    _t2159 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2159
    table_props = Dict(table_property_pairs)
    _t2160 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2160
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start676 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1341 = parse_configure(parser)
        _t1340 = _t1341
    else
        _t1340 = nothing
    end
    configure670 = _t1340
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1343 = parse_sync(parser)
        _t1342 = _t1343
    else
        _t1342 = nothing
    end
    sync671 = _t1342
    xs672 = Proto.Epoch[]
    cond673 = match_lookahead_literal(parser, "(", 0)
    while cond673
        _t1344 = parse_epoch(parser)
        item674 = _t1344
        push!(xs672, item674)
        cond673 = match_lookahead_literal(parser, "(", 0)
    end
    epochs675 = xs672
    consume_literal!(parser, ")")
    _t1345 = default_configure(parser)
    _t1346 = Proto.Transaction(epochs=epochs675, configure=(!isnothing(configure670) ? configure670 : _t1345), sync=sync671)
    result677 = _t1346
    record_span!(parser, span_start676, "Transaction")
    return result677
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start679 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1347 = parse_config_dict(parser)
    config_dict678 = _t1347
    consume_literal!(parser, ")")
    _t1348 = construct_configure(parser, config_dict678)
    result680 = _t1348
    record_span!(parser, span_start679, "Configure")
    return result680
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs681 = Tuple{String, Proto.Value}[]
    cond682 = match_lookahead_literal(parser, ":", 0)
    while cond682
        _t1349 = parse_config_key_value(parser)
        item683 = _t1349
        push!(xs681, item683)
        cond682 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values684 = xs681
    consume_literal!(parser, "}")
    return config_key_values684
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol685 = consume_terminal!(parser, "SYMBOL")
    _t1350 = parse_raw_value(parser)
    raw_value686 = _t1350
    return (symbol685, raw_value686,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start700 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1351 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1352 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1353 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1355 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1356 = 0
                        else
                            _t1356 = -1
                        end
                        _t1355 = _t1356
                    end
                    _t1354 = _t1355
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1357 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1358 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1359 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1360 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1361 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1362 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1363 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1364 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1365 = 10
                                                    else
                                                        _t1365 = -1
                                                    end
                                                    _t1364 = _t1365
                                                end
                                                _t1363 = _t1364
                                            end
                                            _t1362 = _t1363
                                        end
                                        _t1361 = _t1362
                                    end
                                    _t1360 = _t1361
                                end
                                _t1359 = _t1360
                            end
                            _t1358 = _t1359
                        end
                        _t1357 = _t1358
                    end
                    _t1354 = _t1357
                end
                _t1353 = _t1354
            end
            _t1352 = _t1353
        end
        _t1351 = _t1352
    end
    prediction687 = _t1351
    if prediction687 == 12
        _t1367 = parse_boolean_value(parser)
        boolean_value699 = _t1367
        _t1368 = Proto.Value(value=OneOf(:boolean_value, boolean_value699))
        _t1366 = _t1368
    else
        if prediction687 == 11
            consume_literal!(parser, "missing")
            _t1370 = Proto.MissingValue()
            _t1371 = Proto.Value(value=OneOf(:missing_value, _t1370))
            _t1369 = _t1371
        else
            if prediction687 == 10
                decimal698 = consume_terminal!(parser, "DECIMAL")
                _t1373 = Proto.Value(value=OneOf(:decimal_value, decimal698))
                _t1372 = _t1373
            else
                if prediction687 == 9
                    int128697 = consume_terminal!(parser, "INT128")
                    _t1375 = Proto.Value(value=OneOf(:int128_value, int128697))
                    _t1374 = _t1375
                else
                    if prediction687 == 8
                        uint128696 = consume_terminal!(parser, "UINT128")
                        _t1377 = Proto.Value(value=OneOf(:uint128_value, uint128696))
                        _t1376 = _t1377
                    else
                        if prediction687 == 7
                            uint32695 = consume_terminal!(parser, "UINT32")
                            _t1379 = Proto.Value(value=OneOf(:uint32_value, uint32695))
                            _t1378 = _t1379
                        else
                            if prediction687 == 6
                                float694 = consume_terminal!(parser, "FLOAT")
                                _t1381 = Proto.Value(value=OneOf(:float_value, float694))
                                _t1380 = _t1381
                            else
                                if prediction687 == 5
                                    float32693 = consume_terminal!(parser, "FLOAT32")
                                    _t1383 = Proto.Value(value=OneOf(:float32_value, float32693))
                                    _t1382 = _t1383
                                else
                                    if prediction687 == 4
                                        int692 = consume_terminal!(parser, "INT")
                                        _t1385 = Proto.Value(value=OneOf(:int_value, int692))
                                        _t1384 = _t1385
                                    else
                                        if prediction687 == 3
                                            int32691 = consume_terminal!(parser, "INT32")
                                            _t1387 = Proto.Value(value=OneOf(:int32_value, int32691))
                                            _t1386 = _t1387
                                        else
                                            if prediction687 == 2
                                                string690 = consume_terminal!(parser, "STRING")
                                                _t1389 = Proto.Value(value=OneOf(:string_value, string690))
                                                _t1388 = _t1389
                                            else
                                                if prediction687 == 1
                                                    _t1391 = parse_raw_datetime(parser)
                                                    raw_datetime689 = _t1391
                                                    _t1392 = Proto.Value(value=OneOf(:datetime_value, raw_datetime689))
                                                    _t1390 = _t1392
                                                else
                                                    if prediction687 == 0
                                                        _t1394 = parse_raw_date(parser)
                                                        raw_date688 = _t1394
                                                        _t1395 = Proto.Value(value=OneOf(:date_value, raw_date688))
                                                        _t1393 = _t1395
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1390 = _t1393
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
                        _t1376 = _t1378
                    end
                    _t1374 = _t1376
                end
                _t1372 = _t1374
            end
            _t1369 = _t1372
        end
        _t1366 = _t1369
    end
    result701 = _t1366
    record_span!(parser, span_start700, "Value")
    return result701
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start705 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int702 = consume_terminal!(parser, "INT")
    int_3703 = consume_terminal!(parser, "INT")
    int_4704 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1396 = Proto.DateValue(year=Int32(int702), month=Int32(int_3703), day=Int32(int_4704))
    result706 = _t1396
    record_span!(parser, span_start705, "DateValue")
    return result706
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start714 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int707 = consume_terminal!(parser, "INT")
    int_3708 = consume_terminal!(parser, "INT")
    int_4709 = consume_terminal!(parser, "INT")
    int_5710 = consume_terminal!(parser, "INT")
    int_6711 = consume_terminal!(parser, "INT")
    int_7712 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1397 = consume_terminal!(parser, "INT")
    else
        _t1397 = nothing
    end
    int_8713 = _t1397
    consume_literal!(parser, ")")
    _t1398 = Proto.DateTimeValue(year=Int32(int707), month=Int32(int_3708), day=Int32(int_4709), hour=Int32(int_5710), minute=Int32(int_6711), second=Int32(int_7712), microsecond=Int32((!isnothing(int_8713) ? int_8713 : 0)))
    result715 = _t1398
    record_span!(parser, span_start714, "DateTimeValue")
    return result715
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1399 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1400 = 1
        else
            _t1400 = -1
        end
        _t1399 = _t1400
    end
    prediction716 = _t1399
    if prediction716 == 1
        consume_literal!(parser, "false")
        _t1401 = false
    else
        if prediction716 == 0
            consume_literal!(parser, "true")
            _t1402 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1401 = _t1402
    end
    return _t1401
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start721 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs717 = Proto.FragmentId[]
    cond718 = match_lookahead_literal(parser, ":", 0)
    while cond718
        _t1403 = parse_fragment_id(parser)
        item719 = _t1403
        push!(xs717, item719)
        cond718 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids720 = xs717
    consume_literal!(parser, ")")
    _t1404 = Proto.Sync(fragments=fragment_ids720)
    result722 = _t1404
    record_span!(parser, span_start721, "Sync")
    return result722
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start724 = span_start(parser)
    consume_literal!(parser, ":")
    symbol723 = consume_terminal!(parser, "SYMBOL")
    result725 = Proto.FragmentId(Vector{UInt8}(symbol723))
    record_span!(parser, span_start724, "FragmentId")
    return result725
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start728 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1406 = parse_epoch_writes(parser)
        _t1405 = _t1406
    else
        _t1405 = nothing
    end
    epoch_writes726 = _t1405
    if match_lookahead_literal(parser, "(", 0)
        _t1408 = parse_epoch_reads(parser)
        _t1407 = _t1408
    else
        _t1407 = nothing
    end
    epoch_reads727 = _t1407
    consume_literal!(parser, ")")
    _t1409 = Proto.Epoch(writes=(!isnothing(epoch_writes726) ? epoch_writes726 : Proto.Write[]), reads=(!isnothing(epoch_reads727) ? epoch_reads727 : Proto.Read[]))
    result729 = _t1409
    record_span!(parser, span_start728, "Epoch")
    return result729
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs730 = Proto.Write[]
    cond731 = match_lookahead_literal(parser, "(", 0)
    while cond731
        _t1410 = parse_write(parser)
        item732 = _t1410
        push!(xs730, item732)
        cond731 = match_lookahead_literal(parser, "(", 0)
    end
    writes733 = xs730
    consume_literal!(parser, ")")
    return writes733
end

function parse_write(parser::ParserState)::Proto.Write
    span_start739 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1412 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1413 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1414 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1415 = 2
                    else
                        _t1415 = -1
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
    prediction734 = _t1411
    if prediction734 == 3
        _t1417 = parse_snapshot(parser)
        snapshot738 = _t1417
        _t1418 = Proto.Write(write_type=OneOf(:snapshot, snapshot738))
        _t1416 = _t1418
    else
        if prediction734 == 2
            _t1420 = parse_context(parser)
            context737 = _t1420
            _t1421 = Proto.Write(write_type=OneOf(:context, context737))
            _t1419 = _t1421
        else
            if prediction734 == 1
                _t1423 = parse_undefine(parser)
                undefine736 = _t1423
                _t1424 = Proto.Write(write_type=OneOf(:undefine, undefine736))
                _t1422 = _t1424
            else
                if prediction734 == 0
                    _t1426 = parse_define(parser)
                    define735 = _t1426
                    _t1427 = Proto.Write(write_type=OneOf(:define, define735))
                    _t1425 = _t1427
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1422 = _t1425
            end
            _t1419 = _t1422
        end
        _t1416 = _t1419
    end
    result740 = _t1416
    record_span!(parser, span_start739, "Write")
    return result740
end

function parse_define(parser::ParserState)::Proto.Define
    span_start742 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1428 = parse_fragment(parser)
    fragment741 = _t1428
    consume_literal!(parser, ")")
    _t1429 = Proto.Define(fragment=fragment741)
    result743 = _t1429
    record_span!(parser, span_start742, "Define")
    return result743
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start749 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1430 = parse_new_fragment_id(parser)
    new_fragment_id744 = _t1430
    xs745 = Proto.Declaration[]
    cond746 = match_lookahead_literal(parser, "(", 0)
    while cond746
        _t1431 = parse_declaration(parser)
        item747 = _t1431
        push!(xs745, item747)
        cond746 = match_lookahead_literal(parser, "(", 0)
    end
    declarations748 = xs745
    consume_literal!(parser, ")")
    result750 = construct_fragment(parser, new_fragment_id744, declarations748)
    record_span!(parser, span_start749, "Fragment")
    return result750
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start752 = span_start(parser)
    _t1432 = parse_fragment_id(parser)
    fragment_id751 = _t1432
    start_fragment!(parser, fragment_id751)
    result753 = fragment_id751
    record_span!(parser, span_start752, "FragmentId")
    return result753
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start759 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1434 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1435 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1436 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1437 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1438 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1439 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1440 = 1
                                else
                                    _t1440 = -1
                                end
                                _t1439 = _t1440
                            end
                            _t1438 = _t1439
                        end
                        _t1437 = _t1438
                    end
                    _t1436 = _t1437
                end
                _t1435 = _t1436
            end
            _t1434 = _t1435
        end
        _t1433 = _t1434
    else
        _t1433 = -1
    end
    prediction754 = _t1433
    if prediction754 == 3
        _t1442 = parse_data(parser)
        data758 = _t1442
        _t1443 = Proto.Declaration(declaration_type=OneOf(:data, data758))
        _t1441 = _t1443
    else
        if prediction754 == 2
            _t1445 = parse_constraint(parser)
            constraint757 = _t1445
            _t1446 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint757))
            _t1444 = _t1446
        else
            if prediction754 == 1
                _t1448 = parse_algorithm(parser)
                algorithm756 = _t1448
                _t1449 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm756))
                _t1447 = _t1449
            else
                if prediction754 == 0
                    _t1451 = parse_def(parser)
                    def755 = _t1451
                    _t1452 = Proto.Declaration(declaration_type=OneOf(:def, def755))
                    _t1450 = _t1452
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1447 = _t1450
            end
            _t1444 = _t1447
        end
        _t1441 = _t1444
    end
    result760 = _t1441
    record_span!(parser, span_start759, "Declaration")
    return result760
end

function parse_def(parser::ParserState)::Proto.Def
    span_start764 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1453 = parse_relation_id(parser)
    relation_id761 = _t1453
    _t1454 = parse_abstraction(parser)
    abstraction762 = _t1454
    if match_lookahead_literal(parser, "(", 0)
        _t1456 = parse_attrs(parser)
        _t1455 = _t1456
    else
        _t1455 = nothing
    end
    attrs763 = _t1455
    consume_literal!(parser, ")")
    _t1457 = Proto.Def(name=relation_id761, body=abstraction762, attrs=(!isnothing(attrs763) ? attrs763 : Proto.Attribute[]))
    result765 = _t1457
    record_span!(parser, span_start764, "Def")
    return result765
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start769 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1458 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1459 = 1
        else
            _t1459 = -1
        end
        _t1458 = _t1459
    end
    prediction766 = _t1458
    if prediction766 == 1
        uint128768 = consume_terminal!(parser, "UINT128")
        _t1460 = Proto.RelationId(uint128768.low, uint128768.high)
    else
        if prediction766 == 0
            consume_literal!(parser, ":")
            symbol767 = consume_terminal!(parser, "SYMBOL")
            _t1461 = relation_id_from_string(parser, symbol767)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1460 = _t1461
    end
    result770 = _t1460
    record_span!(parser, span_start769, "RelationId")
    return result770
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start773 = span_start(parser)
    consume_literal!(parser, "(")
    _t1462 = parse_bindings(parser)
    bindings771 = _t1462
    _t1463 = parse_formula(parser)
    formula772 = _t1463
    consume_literal!(parser, ")")
    _t1464 = Proto.Abstraction(vars=vcat(bindings771[1], !isnothing(bindings771[2]) ? bindings771[2] : []), value=formula772)
    result774 = _t1464
    record_span!(parser, span_start773, "Abstraction")
    return result774
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs775 = Proto.Binding[]
    cond776 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond776
        _t1465 = parse_binding(parser)
        item777 = _t1465
        push!(xs775, item777)
        cond776 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings778 = xs775
    if match_lookahead_literal(parser, "|", 0)
        _t1467 = parse_value_bindings(parser)
        _t1466 = _t1467
    else
        _t1466 = nothing
    end
    value_bindings779 = _t1466
    consume_literal!(parser, "]")
    return (bindings778, (!isnothing(value_bindings779) ? value_bindings779 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start782 = span_start(parser)
    symbol780 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1468 = parse_type(parser)
    type781 = _t1468
    _t1469 = Proto.Var(name=symbol780)
    _t1470 = Proto.Binding(var=_t1469, var"#type"=type781)
    result783 = _t1470
    record_span!(parser, span_start782, "Binding")
    return result783
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start799 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1471 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1472 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1473 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1474 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1475 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1476 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1477 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1478 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1479 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1480 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1481 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1482 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1483 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1484 = 9
                                                        else
                                                            _t1484 = -1
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
    prediction784 = _t1471
    if prediction784 == 13
        _t1486 = parse_uint32_type(parser)
        uint32_type798 = _t1486
        _t1487 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type798))
        _t1485 = _t1487
    else
        if prediction784 == 12
            _t1489 = parse_float32_type(parser)
            float32_type797 = _t1489
            _t1490 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type797))
            _t1488 = _t1490
        else
            if prediction784 == 11
                _t1492 = parse_int32_type(parser)
                int32_type796 = _t1492
                _t1493 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type796))
                _t1491 = _t1493
            else
                if prediction784 == 10
                    _t1495 = parse_boolean_type(parser)
                    boolean_type795 = _t1495
                    _t1496 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type795))
                    _t1494 = _t1496
                else
                    if prediction784 == 9
                        _t1498 = parse_decimal_type(parser)
                        decimal_type794 = _t1498
                        _t1499 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type794))
                        _t1497 = _t1499
                    else
                        if prediction784 == 8
                            _t1501 = parse_missing_type(parser)
                            missing_type793 = _t1501
                            _t1502 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type793))
                            _t1500 = _t1502
                        else
                            if prediction784 == 7
                                _t1504 = parse_datetime_type(parser)
                                datetime_type792 = _t1504
                                _t1505 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type792))
                                _t1503 = _t1505
                            else
                                if prediction784 == 6
                                    _t1507 = parse_date_type(parser)
                                    date_type791 = _t1507
                                    _t1508 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type791))
                                    _t1506 = _t1508
                                else
                                    if prediction784 == 5
                                        _t1510 = parse_int128_type(parser)
                                        int128_type790 = _t1510
                                        _t1511 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type790))
                                        _t1509 = _t1511
                                    else
                                        if prediction784 == 4
                                            _t1513 = parse_uint128_type(parser)
                                            uint128_type789 = _t1513
                                            _t1514 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type789))
                                            _t1512 = _t1514
                                        else
                                            if prediction784 == 3
                                                _t1516 = parse_float_type(parser)
                                                float_type788 = _t1516
                                                _t1517 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type788))
                                                _t1515 = _t1517
                                            else
                                                if prediction784 == 2
                                                    _t1519 = parse_int_type(parser)
                                                    int_type787 = _t1519
                                                    _t1520 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type787))
                                                    _t1518 = _t1520
                                                else
                                                    if prediction784 == 1
                                                        _t1522 = parse_string_type(parser)
                                                        string_type786 = _t1522
                                                        _t1523 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type786))
                                                        _t1521 = _t1523
                                                    else
                                                        if prediction784 == 0
                                                            _t1525 = parse_unspecified_type(parser)
                                                            unspecified_type785 = _t1525
                                                            _t1526 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type785))
                                                            _t1524 = _t1526
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
            _t1488 = _t1491
        end
        _t1485 = _t1488
    end
    result800 = _t1485
    record_span!(parser, span_start799, "Type")
    return result800
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start801 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1527 = Proto.UnspecifiedType()
    result802 = _t1527
    record_span!(parser, span_start801, "UnspecifiedType")
    return result802
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start803 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1528 = Proto.StringType()
    result804 = _t1528
    record_span!(parser, span_start803, "StringType")
    return result804
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start805 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1529 = Proto.IntType()
    result806 = _t1529
    record_span!(parser, span_start805, "IntType")
    return result806
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start807 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1530 = Proto.FloatType()
    result808 = _t1530
    record_span!(parser, span_start807, "FloatType")
    return result808
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start809 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1531 = Proto.UInt128Type()
    result810 = _t1531
    record_span!(parser, span_start809, "UInt128Type")
    return result810
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start811 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1532 = Proto.Int128Type()
    result812 = _t1532
    record_span!(parser, span_start811, "Int128Type")
    return result812
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start813 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1533 = Proto.DateType()
    result814 = _t1533
    record_span!(parser, span_start813, "DateType")
    return result814
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start815 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1534 = Proto.DateTimeType()
    result816 = _t1534
    record_span!(parser, span_start815, "DateTimeType")
    return result816
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start817 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1535 = Proto.MissingType()
    result818 = _t1535
    record_span!(parser, span_start817, "MissingType")
    return result818
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start821 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int819 = consume_terminal!(parser, "INT")
    int_3820 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1536 = Proto.DecimalType(precision=Int32(int819), scale=Int32(int_3820))
    result822 = _t1536
    record_span!(parser, span_start821, "DecimalType")
    return result822
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start823 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1537 = Proto.BooleanType()
    result824 = _t1537
    record_span!(parser, span_start823, "BooleanType")
    return result824
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start825 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1538 = Proto.Int32Type()
    result826 = _t1538
    record_span!(parser, span_start825, "Int32Type")
    return result826
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start827 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1539 = Proto.Float32Type()
    result828 = _t1539
    record_span!(parser, span_start827, "Float32Type")
    return result828
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start829 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1540 = Proto.UInt32Type()
    result830 = _t1540
    record_span!(parser, span_start829, "UInt32Type")
    return result830
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs831 = Proto.Binding[]
    cond832 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond832
        _t1541 = parse_binding(parser)
        item833 = _t1541
        push!(xs831, item833)
        cond832 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings834 = xs831
    return bindings834
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start849 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1543 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1544 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1545 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1546 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1547 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1548 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1549 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1550 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1551 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1552 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1553 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1554 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1555 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1556 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1557 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1558 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1559 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1560 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1561 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1562 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1563 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1564 = 10
                                                                                            else
                                                                                                _t1564 = -1
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
    else
        _t1542 = -1
    end
    prediction835 = _t1542
    if prediction835 == 12
        _t1566 = parse_cast(parser)
        cast848 = _t1566
        _t1567 = Proto.Formula(formula_type=OneOf(:cast, cast848))
        _t1565 = _t1567
    else
        if prediction835 == 11
            _t1569 = parse_rel_atom(parser)
            rel_atom847 = _t1569
            _t1570 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom847))
            _t1568 = _t1570
        else
            if prediction835 == 10
                _t1572 = parse_primitive(parser)
                primitive846 = _t1572
                _t1573 = Proto.Formula(formula_type=OneOf(:primitive, primitive846))
                _t1571 = _t1573
            else
                if prediction835 == 9
                    _t1575 = parse_pragma(parser)
                    pragma845 = _t1575
                    _t1576 = Proto.Formula(formula_type=OneOf(:pragma, pragma845))
                    _t1574 = _t1576
                else
                    if prediction835 == 8
                        _t1578 = parse_atom(parser)
                        atom844 = _t1578
                        _t1579 = Proto.Formula(formula_type=OneOf(:atom, atom844))
                        _t1577 = _t1579
                    else
                        if prediction835 == 7
                            _t1581 = parse_ffi(parser)
                            ffi843 = _t1581
                            _t1582 = Proto.Formula(formula_type=OneOf(:ffi, ffi843))
                            _t1580 = _t1582
                        else
                            if prediction835 == 6
                                _t1584 = parse_not(parser)
                                not842 = _t1584
                                _t1585 = Proto.Formula(formula_type=OneOf(:not, not842))
                                _t1583 = _t1585
                            else
                                if prediction835 == 5
                                    _t1587 = parse_disjunction(parser)
                                    disjunction841 = _t1587
                                    _t1588 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction841))
                                    _t1586 = _t1588
                                else
                                    if prediction835 == 4
                                        _t1590 = parse_conjunction(parser)
                                        conjunction840 = _t1590
                                        _t1591 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction840))
                                        _t1589 = _t1591
                                    else
                                        if prediction835 == 3
                                            _t1593 = parse_reduce(parser)
                                            reduce839 = _t1593
                                            _t1594 = Proto.Formula(formula_type=OneOf(:reduce, reduce839))
                                            _t1592 = _t1594
                                        else
                                            if prediction835 == 2
                                                _t1596 = parse_exists(parser)
                                                exists838 = _t1596
                                                _t1597 = Proto.Formula(formula_type=OneOf(:exists, exists838))
                                                _t1595 = _t1597
                                            else
                                                if prediction835 == 1
                                                    _t1599 = parse_false(parser)
                                                    false837 = _t1599
                                                    _t1600 = Proto.Formula(formula_type=OneOf(:disjunction, false837))
                                                    _t1598 = _t1600
                                                else
                                                    if prediction835 == 0
                                                        _t1602 = parse_true(parser)
                                                        true836 = _t1602
                                                        _t1603 = Proto.Formula(formula_type=OneOf(:conjunction, true836))
                                                        _t1601 = _t1603
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
            _t1568 = _t1571
        end
        _t1565 = _t1568
    end
    result850 = _t1565
    record_span!(parser, span_start849, "Formula")
    return result850
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start851 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1604 = Proto.Conjunction(args=Proto.Formula[])
    result852 = _t1604
    record_span!(parser, span_start851, "Conjunction")
    return result852
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start853 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1605 = Proto.Disjunction(args=Proto.Formula[])
    result854 = _t1605
    record_span!(parser, span_start853, "Disjunction")
    return result854
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start857 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1606 = parse_bindings(parser)
    bindings855 = _t1606
    _t1607 = parse_formula(parser)
    formula856 = _t1607
    consume_literal!(parser, ")")
    _t1608 = Proto.Abstraction(vars=vcat(bindings855[1], !isnothing(bindings855[2]) ? bindings855[2] : []), value=formula856)
    _t1609 = Proto.Exists(body=_t1608)
    result858 = _t1609
    record_span!(parser, span_start857, "Exists")
    return result858
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start862 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1610 = parse_abstraction(parser)
    abstraction859 = _t1610
    _t1611 = parse_abstraction(parser)
    abstraction_3860 = _t1611
    _t1612 = parse_terms(parser)
    terms861 = _t1612
    consume_literal!(parser, ")")
    _t1613 = Proto.Reduce(op=abstraction859, body=abstraction_3860, terms=terms861)
    result863 = _t1613
    record_span!(parser, span_start862, "Reduce")
    return result863
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs864 = Proto.Term[]
    cond865 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond865
        _t1614 = parse_term(parser)
        item866 = _t1614
        push!(xs864, item866)
        cond865 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms867 = xs864
    consume_literal!(parser, ")")
    return terms867
end

function parse_term(parser::ParserState)::Proto.Term
    span_start871 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1615 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1616 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1617 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1618 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1619 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1620 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1621 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1622 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1623 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1624 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1625 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1626 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1627 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1628 = 1
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
    prediction868 = _t1615
    if prediction868 == 1
        _t1630 = parse_value(parser)
        value870 = _t1630
        _t1631 = Proto.Term(term_type=OneOf(:constant, value870))
        _t1629 = _t1631
    else
        if prediction868 == 0
            _t1633 = parse_var(parser)
            var869 = _t1633
            _t1634 = Proto.Term(term_type=OneOf(:var, var869))
            _t1632 = _t1634
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1629 = _t1632
    end
    result872 = _t1629
    record_span!(parser, span_start871, "Term")
    return result872
end

function parse_var(parser::ParserState)::Proto.Var
    span_start874 = span_start(parser)
    symbol873 = consume_terminal!(parser, "SYMBOL")
    _t1635 = Proto.Var(name=symbol873)
    result875 = _t1635
    record_span!(parser, span_start874, "Var")
    return result875
end

function parse_value(parser::ParserState)::Proto.Value
    span_start889 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1636 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1637 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1638 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1640 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1641 = 0
                        else
                            _t1641 = -1
                        end
                        _t1640 = _t1641
                    end
                    _t1639 = _t1640
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1642 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1643 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1644 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1645 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1646 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1647 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1648 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1649 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1650 = 10
                                                    else
                                                        _t1650 = -1
                                                    end
                                                    _t1649 = _t1650
                                                end
                                                _t1648 = _t1649
                                            end
                                            _t1647 = _t1648
                                        end
                                        _t1646 = _t1647
                                    end
                                    _t1645 = _t1646
                                end
                                _t1644 = _t1645
                            end
                            _t1643 = _t1644
                        end
                        _t1642 = _t1643
                    end
                    _t1639 = _t1642
                end
                _t1638 = _t1639
            end
            _t1637 = _t1638
        end
        _t1636 = _t1637
    end
    prediction876 = _t1636
    if prediction876 == 12
        _t1652 = parse_boolean_value(parser)
        boolean_value888 = _t1652
        _t1653 = Proto.Value(value=OneOf(:boolean_value, boolean_value888))
        _t1651 = _t1653
    else
        if prediction876 == 11
            consume_literal!(parser, "missing")
            _t1655 = Proto.MissingValue()
            _t1656 = Proto.Value(value=OneOf(:missing_value, _t1655))
            _t1654 = _t1656
        else
            if prediction876 == 10
                formatted_decimal887 = consume_terminal!(parser, "DECIMAL")
                _t1658 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal887))
                _t1657 = _t1658
            else
                if prediction876 == 9
                    formatted_int128886 = consume_terminal!(parser, "INT128")
                    _t1660 = Proto.Value(value=OneOf(:int128_value, formatted_int128886))
                    _t1659 = _t1660
                else
                    if prediction876 == 8
                        formatted_uint128885 = consume_terminal!(parser, "UINT128")
                        _t1662 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128885))
                        _t1661 = _t1662
                    else
                        if prediction876 == 7
                            formatted_uint32884 = consume_terminal!(parser, "UINT32")
                            _t1664 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32884))
                            _t1663 = _t1664
                        else
                            if prediction876 == 6
                                formatted_float883 = consume_terminal!(parser, "FLOAT")
                                _t1666 = Proto.Value(value=OneOf(:float_value, formatted_float883))
                                _t1665 = _t1666
                            else
                                if prediction876 == 5
                                    formatted_float32882 = consume_terminal!(parser, "FLOAT32")
                                    _t1668 = Proto.Value(value=OneOf(:float32_value, formatted_float32882))
                                    _t1667 = _t1668
                                else
                                    if prediction876 == 4
                                        formatted_int881 = consume_terminal!(parser, "INT")
                                        _t1670 = Proto.Value(value=OneOf(:int_value, formatted_int881))
                                        _t1669 = _t1670
                                    else
                                        if prediction876 == 3
                                            formatted_int32880 = consume_terminal!(parser, "INT32")
                                            _t1672 = Proto.Value(value=OneOf(:int32_value, formatted_int32880))
                                            _t1671 = _t1672
                                        else
                                            if prediction876 == 2
                                                formatted_string879 = consume_terminal!(parser, "STRING")
                                                _t1674 = Proto.Value(value=OneOf(:string_value, formatted_string879))
                                                _t1673 = _t1674
                                            else
                                                if prediction876 == 1
                                                    _t1676 = parse_datetime(parser)
                                                    datetime878 = _t1676
                                                    _t1677 = Proto.Value(value=OneOf(:datetime_value, datetime878))
                                                    _t1675 = _t1677
                                                else
                                                    if prediction876 == 0
                                                        _t1679 = parse_date(parser)
                                                        date877 = _t1679
                                                        _t1680 = Proto.Value(value=OneOf(:date_value, date877))
                                                        _t1678 = _t1680
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1675 = _t1678
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
                        _t1661 = _t1663
                    end
                    _t1659 = _t1661
                end
                _t1657 = _t1659
            end
            _t1654 = _t1657
        end
        _t1651 = _t1654
    end
    result890 = _t1651
    record_span!(parser, span_start889, "Value")
    return result890
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start894 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int891 = consume_terminal!(parser, "INT")
    formatted_int_3892 = consume_terminal!(parser, "INT")
    formatted_int_4893 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1681 = Proto.DateValue(year=Int32(formatted_int891), month=Int32(formatted_int_3892), day=Int32(formatted_int_4893))
    result895 = _t1681
    record_span!(parser, span_start894, "DateValue")
    return result895
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start903 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int896 = consume_terminal!(parser, "INT")
    formatted_int_3897 = consume_terminal!(parser, "INT")
    formatted_int_4898 = consume_terminal!(parser, "INT")
    formatted_int_5899 = consume_terminal!(parser, "INT")
    formatted_int_6900 = consume_terminal!(parser, "INT")
    formatted_int_7901 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1682 = consume_terminal!(parser, "INT")
    else
        _t1682 = nothing
    end
    formatted_int_8902 = _t1682
    consume_literal!(parser, ")")
    _t1683 = Proto.DateTimeValue(year=Int32(formatted_int896), month=Int32(formatted_int_3897), day=Int32(formatted_int_4898), hour=Int32(formatted_int_5899), minute=Int32(formatted_int_6900), second=Int32(formatted_int_7901), microsecond=Int32((!isnothing(formatted_int_8902) ? formatted_int_8902 : 0)))
    result904 = _t1683
    record_span!(parser, span_start903, "DateTimeValue")
    return result904
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start909 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs905 = Proto.Formula[]
    cond906 = match_lookahead_literal(parser, "(", 0)
    while cond906
        _t1684 = parse_formula(parser)
        item907 = _t1684
        push!(xs905, item907)
        cond906 = match_lookahead_literal(parser, "(", 0)
    end
    formulas908 = xs905
    consume_literal!(parser, ")")
    _t1685 = Proto.Conjunction(args=formulas908)
    result910 = _t1685
    record_span!(parser, span_start909, "Conjunction")
    return result910
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start915 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs911 = Proto.Formula[]
    cond912 = match_lookahead_literal(parser, "(", 0)
    while cond912
        _t1686 = parse_formula(parser)
        item913 = _t1686
        push!(xs911, item913)
        cond912 = match_lookahead_literal(parser, "(", 0)
    end
    formulas914 = xs911
    consume_literal!(parser, ")")
    _t1687 = Proto.Disjunction(args=formulas914)
    result916 = _t1687
    record_span!(parser, span_start915, "Disjunction")
    return result916
end

function parse_not(parser::ParserState)::Proto.Not
    span_start918 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1688 = parse_formula(parser)
    formula917 = _t1688
    consume_literal!(parser, ")")
    _t1689 = Proto.Not(arg=formula917)
    result919 = _t1689
    record_span!(parser, span_start918, "Not")
    return result919
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start923 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1690 = parse_name(parser)
    name920 = _t1690
    _t1691 = parse_ffi_args(parser)
    ffi_args921 = _t1691
    _t1692 = parse_terms(parser)
    terms922 = _t1692
    consume_literal!(parser, ")")
    _t1693 = Proto.FFI(name=name920, args=ffi_args921, terms=terms922)
    result924 = _t1693
    record_span!(parser, span_start923, "FFI")
    return result924
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol925 = consume_terminal!(parser, "SYMBOL")
    return symbol925
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs926 = Proto.Abstraction[]
    cond927 = match_lookahead_literal(parser, "(", 0)
    while cond927
        _t1694 = parse_abstraction(parser)
        item928 = _t1694
        push!(xs926, item928)
        cond927 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions929 = xs926
    consume_literal!(parser, ")")
    return abstractions929
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start935 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1695 = parse_relation_id(parser)
    relation_id930 = _t1695
    xs931 = Proto.Term[]
    cond932 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond932
        _t1696 = parse_term(parser)
        item933 = _t1696
        push!(xs931, item933)
        cond932 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms934 = xs931
    consume_literal!(parser, ")")
    _t1697 = Proto.Atom(name=relation_id930, terms=terms934)
    result936 = _t1697
    record_span!(parser, span_start935, "Atom")
    return result936
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start942 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1698 = parse_name(parser)
    name937 = _t1698
    xs938 = Proto.Term[]
    cond939 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond939
        _t1699 = parse_term(parser)
        item940 = _t1699
        push!(xs938, item940)
        cond939 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms941 = xs938
    consume_literal!(parser, ")")
    _t1700 = Proto.Pragma(name=name937, terms=terms941)
    result943 = _t1700
    record_span!(parser, span_start942, "Pragma")
    return result943
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start959 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1702 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1703 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1704 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1705 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1706 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1707 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1708 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1709 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1710 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1711 = 7
                                            else
                                                _t1711 = -1
                                            end
                                            _t1710 = _t1711
                                        end
                                        _t1709 = _t1710
                                    end
                                    _t1708 = _t1709
                                end
                                _t1707 = _t1708
                            end
                            _t1706 = _t1707
                        end
                        _t1705 = _t1706
                    end
                    _t1704 = _t1705
                end
                _t1703 = _t1704
            end
            _t1702 = _t1703
        end
        _t1701 = _t1702
    else
        _t1701 = -1
    end
    prediction944 = _t1701
    if prediction944 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1713 = parse_name(parser)
        name954 = _t1713
        xs955 = Proto.RelTerm[]
        cond956 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond956
            _t1714 = parse_rel_term(parser)
            item957 = _t1714
            push!(xs955, item957)
            cond956 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms958 = xs955
        consume_literal!(parser, ")")
        _t1715 = Proto.Primitive(name=name954, terms=rel_terms958)
        _t1712 = _t1715
    else
        if prediction944 == 8
            _t1717 = parse_divide(parser)
            divide953 = _t1717
            _t1716 = divide953
        else
            if prediction944 == 7
                _t1719 = parse_multiply(parser)
                multiply952 = _t1719
                _t1718 = multiply952
            else
                if prediction944 == 6
                    _t1721 = parse_minus(parser)
                    minus951 = _t1721
                    _t1720 = minus951
                else
                    if prediction944 == 5
                        _t1723 = parse_add(parser)
                        add950 = _t1723
                        _t1722 = add950
                    else
                        if prediction944 == 4
                            _t1725 = parse_gt_eq(parser)
                            gt_eq949 = _t1725
                            _t1724 = gt_eq949
                        else
                            if prediction944 == 3
                                _t1727 = parse_gt(parser)
                                gt948 = _t1727
                                _t1726 = gt948
                            else
                                if prediction944 == 2
                                    _t1729 = parse_lt_eq(parser)
                                    lt_eq947 = _t1729
                                    _t1728 = lt_eq947
                                else
                                    if prediction944 == 1
                                        _t1731 = parse_lt(parser)
                                        lt946 = _t1731
                                        _t1730 = lt946
                                    else
                                        if prediction944 == 0
                                            _t1733 = parse_eq(parser)
                                            eq945 = _t1733
                                            _t1732 = eq945
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
                    _t1720 = _t1722
                end
                _t1718 = _t1720
            end
            _t1716 = _t1718
        end
        _t1712 = _t1716
    end
    result960 = _t1712
    record_span!(parser, span_start959, "Primitive")
    return result960
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start963 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1734 = parse_term(parser)
    term961 = _t1734
    _t1735 = parse_term(parser)
    term_3962 = _t1735
    consume_literal!(parser, ")")
    _t1736 = Proto.RelTerm(rel_term_type=OneOf(:term, term961))
    _t1737 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3962))
    _t1738 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1736, _t1737])
    result964 = _t1738
    record_span!(parser, span_start963, "Primitive")
    return result964
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start967 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1739 = parse_term(parser)
    term965 = _t1739
    _t1740 = parse_term(parser)
    term_3966 = _t1740
    consume_literal!(parser, ")")
    _t1741 = Proto.RelTerm(rel_term_type=OneOf(:term, term965))
    _t1742 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3966))
    _t1743 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1741, _t1742])
    result968 = _t1743
    record_span!(parser, span_start967, "Primitive")
    return result968
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start971 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1744 = parse_term(parser)
    term969 = _t1744
    _t1745 = parse_term(parser)
    term_3970 = _t1745
    consume_literal!(parser, ")")
    _t1746 = Proto.RelTerm(rel_term_type=OneOf(:term, term969))
    _t1747 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3970))
    _t1748 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1746, _t1747])
    result972 = _t1748
    record_span!(parser, span_start971, "Primitive")
    return result972
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start975 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1749 = parse_term(parser)
    term973 = _t1749
    _t1750 = parse_term(parser)
    term_3974 = _t1750
    consume_literal!(parser, ")")
    _t1751 = Proto.RelTerm(rel_term_type=OneOf(:term, term973))
    _t1752 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3974))
    _t1753 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1751, _t1752])
    result976 = _t1753
    record_span!(parser, span_start975, "Primitive")
    return result976
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start979 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1754 = parse_term(parser)
    term977 = _t1754
    _t1755 = parse_term(parser)
    term_3978 = _t1755
    consume_literal!(parser, ")")
    _t1756 = Proto.RelTerm(rel_term_type=OneOf(:term, term977))
    _t1757 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3978))
    _t1758 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1756, _t1757])
    result980 = _t1758
    record_span!(parser, span_start979, "Primitive")
    return result980
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start984 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1759 = parse_term(parser)
    term981 = _t1759
    _t1760 = parse_term(parser)
    term_3982 = _t1760
    _t1761 = parse_term(parser)
    term_4983 = _t1761
    consume_literal!(parser, ")")
    _t1762 = Proto.RelTerm(rel_term_type=OneOf(:term, term981))
    _t1763 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3982))
    _t1764 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4983))
    _t1765 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1762, _t1763, _t1764])
    result985 = _t1765
    record_span!(parser, span_start984, "Primitive")
    return result985
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start989 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1766 = parse_term(parser)
    term986 = _t1766
    _t1767 = parse_term(parser)
    term_3987 = _t1767
    _t1768 = parse_term(parser)
    term_4988 = _t1768
    consume_literal!(parser, ")")
    _t1769 = Proto.RelTerm(rel_term_type=OneOf(:term, term986))
    _t1770 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3987))
    _t1771 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4988))
    _t1772 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1769, _t1770, _t1771])
    result990 = _t1772
    record_span!(parser, span_start989, "Primitive")
    return result990
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start994 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1773 = parse_term(parser)
    term991 = _t1773
    _t1774 = parse_term(parser)
    term_3992 = _t1774
    _t1775 = parse_term(parser)
    term_4993 = _t1775
    consume_literal!(parser, ")")
    _t1776 = Proto.RelTerm(rel_term_type=OneOf(:term, term991))
    _t1777 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3992))
    _t1778 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4993))
    _t1779 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1776, _t1777, _t1778])
    result995 = _t1779
    record_span!(parser, span_start994, "Primitive")
    return result995
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start999 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1780 = parse_term(parser)
    term996 = _t1780
    _t1781 = parse_term(parser)
    term_3997 = _t1781
    _t1782 = parse_term(parser)
    term_4998 = _t1782
    consume_literal!(parser, ")")
    _t1783 = Proto.RelTerm(rel_term_type=OneOf(:term, term996))
    _t1784 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3997))
    _t1785 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4998))
    _t1786 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1783, _t1784, _t1785])
    result1000 = _t1786
    record_span!(parser, span_start999, "Primitive")
    return result1000
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1004 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1787 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1788 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1789 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1790 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1791 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1792 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1793 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1794 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1795 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1796 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1797 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1798 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1799 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1800 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1801 = 1
                                                            else
                                                                _t1801 = -1
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
    prediction1001 = _t1787
    if prediction1001 == 1
        _t1803 = parse_term(parser)
        term1003 = _t1803
        _t1804 = Proto.RelTerm(rel_term_type=OneOf(:term, term1003))
        _t1802 = _t1804
    else
        if prediction1001 == 0
            _t1806 = parse_specialized_value(parser)
            specialized_value1002 = _t1806
            _t1807 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1002))
            _t1805 = _t1807
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1802 = _t1805
    end
    result1005 = _t1802
    record_span!(parser, span_start1004, "RelTerm")
    return result1005
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1007 = span_start(parser)
    consume_literal!(parser, "#")
    _t1808 = parse_raw_value(parser)
    raw_value1006 = _t1808
    result1008 = raw_value1006
    record_span!(parser, span_start1007, "Value")
    return result1008
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1014 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1809 = parse_name(parser)
    name1009 = _t1809
    xs1010 = Proto.RelTerm[]
    cond1011 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1011
        _t1810 = parse_rel_term(parser)
        item1012 = _t1810
        push!(xs1010, item1012)
        cond1011 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1013 = xs1010
    consume_literal!(parser, ")")
    _t1811 = Proto.RelAtom(name=name1009, terms=rel_terms1013)
    result1015 = _t1811
    record_span!(parser, span_start1014, "RelAtom")
    return result1015
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1018 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1812 = parse_term(parser)
    term1016 = _t1812
    _t1813 = parse_term(parser)
    term_31017 = _t1813
    consume_literal!(parser, ")")
    _t1814 = Proto.Cast(input=term1016, result=term_31017)
    result1019 = _t1814
    record_span!(parser, span_start1018, "Cast")
    return result1019
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1020 = Proto.Attribute[]
    cond1021 = match_lookahead_literal(parser, "(", 0)
    while cond1021
        _t1815 = parse_attribute(parser)
        item1022 = _t1815
        push!(xs1020, item1022)
        cond1021 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1023 = xs1020
    consume_literal!(parser, ")")
    return attributes1023
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1029 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1816 = parse_name(parser)
    name1024 = _t1816
    xs1025 = Proto.Value[]
    cond1026 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1026
        _t1817 = parse_raw_value(parser)
        item1027 = _t1817
        push!(xs1025, item1027)
        cond1026 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1028 = xs1025
    consume_literal!(parser, ")")
    _t1818 = Proto.Attribute(name=name1024, args=raw_values1028)
    result1030 = _t1818
    record_span!(parser, span_start1029, "Attribute")
    return result1030
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1037 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1031 = Proto.RelationId[]
    cond1032 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1032
        _t1819 = parse_relation_id(parser)
        item1033 = _t1819
        push!(xs1031, item1033)
        cond1032 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1034 = xs1031
    _t1820 = parse_script(parser)
    script1035 = _t1820
    if match_lookahead_literal(parser, "(", 0)
        _t1822 = parse_attrs(parser)
        _t1821 = _t1822
    else
        _t1821 = nothing
    end
    attrs1036 = _t1821
    consume_literal!(parser, ")")
    _t1823 = Proto.Algorithm(var"#global"=relation_ids1034, body=script1035, attrs=(!isnothing(attrs1036) ? attrs1036 : Proto.Attribute[]))
    result1038 = _t1823
    record_span!(parser, span_start1037, "Algorithm")
    return result1038
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1043 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1039 = Proto.Construct[]
    cond1040 = match_lookahead_literal(parser, "(", 0)
    while cond1040
        _t1824 = parse_construct(parser)
        item1041 = _t1824
        push!(xs1039, item1041)
        cond1040 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1042 = xs1039
    consume_literal!(parser, ")")
    _t1825 = Proto.Script(constructs=constructs1042)
    result1044 = _t1825
    record_span!(parser, span_start1043, "Script")
    return result1044
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1048 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1827 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1828 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1829 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1830 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1831 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1832 = 1
                            else
                                _t1832 = -1
                            end
                            _t1831 = _t1832
                        end
                        _t1830 = _t1831
                    end
                    _t1829 = _t1830
                end
                _t1828 = _t1829
            end
            _t1827 = _t1828
        end
        _t1826 = _t1827
    else
        _t1826 = -1
    end
    prediction1045 = _t1826
    if prediction1045 == 1
        _t1834 = parse_instruction(parser)
        instruction1047 = _t1834
        _t1835 = Proto.Construct(construct_type=OneOf(:instruction, instruction1047))
        _t1833 = _t1835
    else
        if prediction1045 == 0
            _t1837 = parse_loop(parser)
            loop1046 = _t1837
            _t1838 = Proto.Construct(construct_type=OneOf(:loop, loop1046))
            _t1836 = _t1838
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1833 = _t1836
    end
    result1049 = _t1833
    record_span!(parser, span_start1048, "Construct")
    return result1049
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1053 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1839 = parse_init(parser)
    init1050 = _t1839
    _t1840 = parse_script(parser)
    script1051 = _t1840
    if match_lookahead_literal(parser, "(", 0)
        _t1842 = parse_attrs(parser)
        _t1841 = _t1842
    else
        _t1841 = nothing
    end
    attrs1052 = _t1841
    consume_literal!(parser, ")")
    _t1843 = Proto.Loop(init=init1050, body=script1051, attrs=(!isnothing(attrs1052) ? attrs1052 : Proto.Attribute[]))
    result1054 = _t1843
    record_span!(parser, span_start1053, "Loop")
    return result1054
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1055 = Proto.Instruction[]
    cond1056 = match_lookahead_literal(parser, "(", 0)
    while cond1056
        _t1844 = parse_instruction(parser)
        item1057 = _t1844
        push!(xs1055, item1057)
        cond1056 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1058 = xs1055
    consume_literal!(parser, ")")
    return instructions1058
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1065 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1846 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1847 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1848 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1849 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1850 = 0
                        else
                            _t1850 = -1
                        end
                        _t1849 = _t1850
                    end
                    _t1848 = _t1849
                end
                _t1847 = _t1848
            end
            _t1846 = _t1847
        end
        _t1845 = _t1846
    else
        _t1845 = -1
    end
    prediction1059 = _t1845
    if prediction1059 == 4
        _t1852 = parse_monus_def(parser)
        monus_def1064 = _t1852
        _t1853 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1064))
        _t1851 = _t1853
    else
        if prediction1059 == 3
            _t1855 = parse_monoid_def(parser)
            monoid_def1063 = _t1855
            _t1856 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1063))
            _t1854 = _t1856
        else
            if prediction1059 == 2
                _t1858 = parse_break(parser)
                break1062 = _t1858
                _t1859 = Proto.Instruction(instr_type=OneOf(:var"#break", break1062))
                _t1857 = _t1859
            else
                if prediction1059 == 1
                    _t1861 = parse_upsert(parser)
                    upsert1061 = _t1861
                    _t1862 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1061))
                    _t1860 = _t1862
                else
                    if prediction1059 == 0
                        _t1864 = parse_assign(parser)
                        assign1060 = _t1864
                        _t1865 = Proto.Instruction(instr_type=OneOf(:assign, assign1060))
                        _t1863 = _t1865
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1860 = _t1863
                end
                _t1857 = _t1860
            end
            _t1854 = _t1857
        end
        _t1851 = _t1854
    end
    result1066 = _t1851
    record_span!(parser, span_start1065, "Instruction")
    return result1066
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1070 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1866 = parse_relation_id(parser)
    relation_id1067 = _t1866
    _t1867 = parse_abstraction(parser)
    abstraction1068 = _t1867
    if match_lookahead_literal(parser, "(", 0)
        _t1869 = parse_attrs(parser)
        _t1868 = _t1869
    else
        _t1868 = nothing
    end
    attrs1069 = _t1868
    consume_literal!(parser, ")")
    _t1870 = Proto.Assign(name=relation_id1067, body=abstraction1068, attrs=(!isnothing(attrs1069) ? attrs1069 : Proto.Attribute[]))
    result1071 = _t1870
    record_span!(parser, span_start1070, "Assign")
    return result1071
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1075 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1871 = parse_relation_id(parser)
    relation_id1072 = _t1871
    _t1872 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1073 = _t1872
    if match_lookahead_literal(parser, "(", 0)
        _t1874 = parse_attrs(parser)
        _t1873 = _t1874
    else
        _t1873 = nothing
    end
    attrs1074 = _t1873
    consume_literal!(parser, ")")
    _t1875 = Proto.Upsert(name=relation_id1072, body=abstraction_with_arity1073[1], attrs=(!isnothing(attrs1074) ? attrs1074 : Proto.Attribute[]), value_arity=abstraction_with_arity1073[2])
    result1076 = _t1875
    record_span!(parser, span_start1075, "Upsert")
    return result1076
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1876 = parse_bindings(parser)
    bindings1077 = _t1876
    _t1877 = parse_formula(parser)
    formula1078 = _t1877
    consume_literal!(parser, ")")
    _t1878 = Proto.Abstraction(vars=vcat(bindings1077[1], !isnothing(bindings1077[2]) ? bindings1077[2] : []), value=formula1078)
    return (_t1878, length(bindings1077[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1082 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1879 = parse_relation_id(parser)
    relation_id1079 = _t1879
    _t1880 = parse_abstraction(parser)
    abstraction1080 = _t1880
    if match_lookahead_literal(parser, "(", 0)
        _t1882 = parse_attrs(parser)
        _t1881 = _t1882
    else
        _t1881 = nothing
    end
    attrs1081 = _t1881
    consume_literal!(parser, ")")
    _t1883 = Proto.Break(name=relation_id1079, body=abstraction1080, attrs=(!isnothing(attrs1081) ? attrs1081 : Proto.Attribute[]))
    result1083 = _t1883
    record_span!(parser, span_start1082, "Break")
    return result1083
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1088 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1884 = parse_monoid(parser)
    monoid1084 = _t1884
    _t1885 = parse_relation_id(parser)
    relation_id1085 = _t1885
    _t1886 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1086 = _t1886
    if match_lookahead_literal(parser, "(", 0)
        _t1888 = parse_attrs(parser)
        _t1887 = _t1888
    else
        _t1887 = nothing
    end
    attrs1087 = _t1887
    consume_literal!(parser, ")")
    _t1889 = Proto.MonoidDef(monoid=monoid1084, name=relation_id1085, body=abstraction_with_arity1086[1], attrs=(!isnothing(attrs1087) ? attrs1087 : Proto.Attribute[]), value_arity=abstraction_with_arity1086[2])
    result1089 = _t1889
    record_span!(parser, span_start1088, "MonoidDef")
    return result1089
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1095 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1891 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1892 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1893 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1894 = 2
                    else
                        _t1894 = -1
                    end
                    _t1893 = _t1894
                end
                _t1892 = _t1893
            end
            _t1891 = _t1892
        end
        _t1890 = _t1891
    else
        _t1890 = -1
    end
    prediction1090 = _t1890
    if prediction1090 == 3
        _t1896 = parse_sum_monoid(parser)
        sum_monoid1094 = _t1896
        _t1897 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1094))
        _t1895 = _t1897
    else
        if prediction1090 == 2
            _t1899 = parse_max_monoid(parser)
            max_monoid1093 = _t1899
            _t1900 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1093))
            _t1898 = _t1900
        else
            if prediction1090 == 1
                _t1902 = parse_min_monoid(parser)
                min_monoid1092 = _t1902
                _t1903 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1092))
                _t1901 = _t1903
            else
                if prediction1090 == 0
                    _t1905 = parse_or_monoid(parser)
                    or_monoid1091 = _t1905
                    _t1906 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1091))
                    _t1904 = _t1906
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1901 = _t1904
            end
            _t1898 = _t1901
        end
        _t1895 = _t1898
    end
    result1096 = _t1895
    record_span!(parser, span_start1095, "Monoid")
    return result1096
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1097 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1907 = Proto.OrMonoid()
    result1098 = _t1907
    record_span!(parser, span_start1097, "OrMonoid")
    return result1098
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1100 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1908 = parse_type(parser)
    type1099 = _t1908
    consume_literal!(parser, ")")
    _t1909 = Proto.MinMonoid(var"#type"=type1099)
    result1101 = _t1909
    record_span!(parser, span_start1100, "MinMonoid")
    return result1101
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1103 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1910 = parse_type(parser)
    type1102 = _t1910
    consume_literal!(parser, ")")
    _t1911 = Proto.MaxMonoid(var"#type"=type1102)
    result1104 = _t1911
    record_span!(parser, span_start1103, "MaxMonoid")
    return result1104
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1106 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1912 = parse_type(parser)
    type1105 = _t1912
    consume_literal!(parser, ")")
    _t1913 = Proto.SumMonoid(var"#type"=type1105)
    result1107 = _t1913
    record_span!(parser, span_start1106, "SumMonoid")
    return result1107
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1112 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1914 = parse_monoid(parser)
    monoid1108 = _t1914
    _t1915 = parse_relation_id(parser)
    relation_id1109 = _t1915
    _t1916 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1110 = _t1916
    if match_lookahead_literal(parser, "(", 0)
        _t1918 = parse_attrs(parser)
        _t1917 = _t1918
    else
        _t1917 = nothing
    end
    attrs1111 = _t1917
    consume_literal!(parser, ")")
    _t1919 = Proto.MonusDef(monoid=monoid1108, name=relation_id1109, body=abstraction_with_arity1110[1], attrs=(!isnothing(attrs1111) ? attrs1111 : Proto.Attribute[]), value_arity=abstraction_with_arity1110[2])
    result1113 = _t1919
    record_span!(parser, span_start1112, "MonusDef")
    return result1113
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1118 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1920 = parse_relation_id(parser)
    relation_id1114 = _t1920
    _t1921 = parse_abstraction(parser)
    abstraction1115 = _t1921
    _t1922 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1116 = _t1922
    _t1923 = parse_functional_dependency_values(parser)
    functional_dependency_values1117 = _t1923
    consume_literal!(parser, ")")
    _t1924 = Proto.FunctionalDependency(guard=abstraction1115, keys=functional_dependency_keys1116, values=functional_dependency_values1117)
    _t1925 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1924), name=relation_id1114)
    result1119 = _t1925
    record_span!(parser, span_start1118, "Constraint")
    return result1119
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1120 = Proto.Var[]
    cond1121 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1121
        _t1926 = parse_var(parser)
        item1122 = _t1926
        push!(xs1120, item1122)
        cond1121 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1123 = xs1120
    consume_literal!(parser, ")")
    return vars1123
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1124 = Proto.Var[]
    cond1125 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1125
        _t1927 = parse_var(parser)
        item1126 = _t1927
        push!(xs1124, item1126)
        cond1125 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1127 = xs1124
    consume_literal!(parser, ")")
    return vars1127
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1133 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1929 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1930 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1931 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1932 = 1
                    else
                        _t1932 = -1
                    end
                    _t1931 = _t1932
                end
                _t1930 = _t1931
            end
            _t1929 = _t1930
        end
        _t1928 = _t1929
    else
        _t1928 = -1
    end
    prediction1128 = _t1928
    if prediction1128 == 3
        _t1934 = parse_iceberg_data(parser)
        iceberg_data1132 = _t1934
        _t1935 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1132))
        _t1933 = _t1935
    else
        if prediction1128 == 2
            _t1937 = parse_csv_data(parser)
            csv_data1131 = _t1937
            _t1938 = Proto.Data(data_type=OneOf(:csv_data, csv_data1131))
            _t1936 = _t1938
        else
            if prediction1128 == 1
                _t1940 = parse_betree_relation(parser)
                betree_relation1130 = _t1940
                _t1941 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1130))
                _t1939 = _t1941
            else
                if prediction1128 == 0
                    _t1943 = parse_edb(parser)
                    edb1129 = _t1943
                    _t1944 = Proto.Data(data_type=OneOf(:edb, edb1129))
                    _t1942 = _t1944
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1939 = _t1942
            end
            _t1936 = _t1939
        end
        _t1933 = _t1936
    end
    result1134 = _t1933
    record_span!(parser, span_start1133, "Data")
    return result1134
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1138 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1945 = parse_relation_id(parser)
    relation_id1135 = _t1945
    _t1946 = parse_edb_path(parser)
    edb_path1136 = _t1946
    _t1947 = parse_edb_types(parser)
    edb_types1137 = _t1947
    consume_literal!(parser, ")")
    _t1948 = Proto.EDB(target_id=relation_id1135, path=edb_path1136, types=edb_types1137)
    result1139 = _t1948
    record_span!(parser, span_start1138, "EDB")
    return result1139
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1140 = String[]
    cond1141 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1141
        item1142 = consume_terminal!(parser, "STRING")
        push!(xs1140, item1142)
        cond1141 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1143 = xs1140
    consume_literal!(parser, "]")
    return strings1143
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1144 = Proto.var"#Type"[]
    cond1145 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1145
        _t1949 = parse_type(parser)
        item1146 = _t1949
        push!(xs1144, item1146)
        cond1145 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1147 = xs1144
    consume_literal!(parser, "]")
    return types1147
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1150 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1950 = parse_relation_id(parser)
    relation_id1148 = _t1950
    _t1951 = parse_betree_info(parser)
    betree_info1149 = _t1951
    consume_literal!(parser, ")")
    _t1952 = Proto.BeTreeRelation(name=relation_id1148, relation_info=betree_info1149)
    result1151 = _t1952
    record_span!(parser, span_start1150, "BeTreeRelation")
    return result1151
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1155 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1953 = parse_betree_info_key_types(parser)
    betree_info_key_types1152 = _t1953
    _t1954 = parse_betree_info_value_types(parser)
    betree_info_value_types1153 = _t1954
    _t1955 = parse_config_dict(parser)
    config_dict1154 = _t1955
    consume_literal!(parser, ")")
    _t1956 = construct_betree_info(parser, betree_info_key_types1152, betree_info_value_types1153, config_dict1154)
    result1156 = _t1956
    record_span!(parser, span_start1155, "BeTreeInfo")
    return result1156
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1157 = Proto.var"#Type"[]
    cond1158 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1158
        _t1957 = parse_type(parser)
        item1159 = _t1957
        push!(xs1157, item1159)
        cond1158 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1160 = xs1157
    consume_literal!(parser, ")")
    return types1160
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1161 = Proto.var"#Type"[]
    cond1162 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1162
        _t1958 = parse_type(parser)
        item1163 = _t1958
        push!(xs1161, item1163)
        cond1162 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1164 = xs1161
    consume_literal!(parser, ")")
    return types1164
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1169 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1959 = parse_csvlocator(parser)
    csvlocator1165 = _t1959
    _t1960 = parse_csv_config(parser)
    csv_config1166 = _t1960
    _t1961 = parse_gnf_columns(parser)
    gnf_columns1167 = _t1961
    _t1962 = parse_csv_asof(parser)
    csv_asof1168 = _t1962
    consume_literal!(parser, ")")
    _t1963 = Proto.CSVData(locator=csvlocator1165, config=csv_config1166, columns=gnf_columns1167, asof=csv_asof1168)
    result1170 = _t1963
    record_span!(parser, span_start1169, "CSVData")
    return result1170
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1173 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1965 = parse_csv_locator_paths(parser)
        _t1964 = _t1965
    else
        _t1964 = nothing
    end
    csv_locator_paths1171 = _t1964
    if match_lookahead_literal(parser, "(", 0)
        _t1967 = parse_csv_locator_inline_data(parser)
        _t1966 = _t1967
    else
        _t1966 = nothing
    end
    csv_locator_inline_data1172 = _t1966
    consume_literal!(parser, ")")
    _t1968 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1171) ? csv_locator_paths1171 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1172) ? csv_locator_inline_data1172 : "")))
    result1174 = _t1968
    record_span!(parser, span_start1173, "CSVLocator")
    return result1174
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1175 = String[]
    cond1176 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1176
        item1177 = consume_terminal!(parser, "STRING")
        push!(xs1175, item1177)
        cond1176 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1178 = xs1175
    consume_literal!(parser, ")")
    return strings1178
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1179 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1179
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1182 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1969 = parse_config_dict(parser)
    config_dict1180 = _t1969
    if match_lookahead_literal(parser, "(", 0)
        _t1971 = parse__storage_integration(parser)
        _t1970 = _t1971
    else
        _t1970 = nothing
    end
    _storage_integration1181 = _t1970
    consume_literal!(parser, ")")
    _t1972 = construct_csv_config(parser, config_dict1180, _storage_integration1181)
    result1183 = _t1972
    record_span!(parser, span_start1182, "CSVConfig")
    return result1183
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t1973 = parse_config_dict(parser)
    config_dict1184 = _t1973
    consume_literal!(parser, ")")
    return config_dict1184
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1185 = Proto.GNFColumn[]
    cond1186 = match_lookahead_literal(parser, "(", 0)
    while cond1186
        _t1974 = parse_gnf_column(parser)
        item1187 = _t1974
        push!(xs1185, item1187)
        cond1186 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1188 = xs1185
    consume_literal!(parser, ")")
    return gnf_columns1188
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1195 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1975 = parse_gnf_column_path(parser)
    gnf_column_path1189 = _t1975
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1977 = parse_relation_id(parser)
        _t1976 = _t1977
    else
        _t1976 = nothing
    end
    relation_id1190 = _t1976
    consume_literal!(parser, "[")
    xs1191 = Proto.var"#Type"[]
    cond1192 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1192
        _t1978 = parse_type(parser)
        item1193 = _t1978
        push!(xs1191, item1193)
        cond1192 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1194 = xs1191
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1979 = Proto.GNFColumn(column_path=gnf_column_path1189, target_id=relation_id1190, types=types1194)
    result1196 = _t1979
    record_span!(parser, span_start1195, "GNFColumn")
    return result1196
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1980 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1981 = 0
        else
            _t1981 = -1
        end
        _t1980 = _t1981
    end
    prediction1197 = _t1980
    if prediction1197 == 1
        consume_literal!(parser, "[")
        xs1199 = String[]
        cond1200 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1200
            item1201 = consume_terminal!(parser, "STRING")
            push!(xs1199, item1201)
            cond1200 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1202 = xs1199
        consume_literal!(parser, "]")
        _t1982 = strings1202
    else
        if prediction1197 == 0
            string1198 = consume_terminal!(parser, "STRING")
            _t1983 = String[string1198]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1982 = _t1983
    end
    return _t1982
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1203 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1203
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1210 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1984 = parse_iceberg_locator(parser)
    iceberg_locator1204 = _t1984
    _t1985 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1205 = _t1985
    _t1986 = parse_gnf_columns(parser)
    gnf_columns1206 = _t1986
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1988 = parse_iceberg_from_snapshot(parser)
        _t1987 = _t1988
    else
        _t1987 = nothing
    end
    iceberg_from_snapshot1207 = _t1987
    if match_lookahead_literal(parser, "(", 0)
        _t1990 = parse_iceberg_to_snapshot(parser)
        _t1989 = _t1990
    else
        _t1989 = nothing
    end
    iceberg_to_snapshot1208 = _t1989
    _t1991 = parse_boolean_value(parser)
    boolean_value1209 = _t1991
    consume_literal!(parser, ")")
    _t1992 = construct_iceberg_data(parser, iceberg_locator1204, iceberg_catalog_config1205, gnf_columns1206, iceberg_from_snapshot1207, iceberg_to_snapshot1208, boolean_value1209)
    result1211 = _t1992
    record_span!(parser, span_start1210, "IcebergData")
    return result1211
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1215 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t1993 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1212 = _t1993
    _t1994 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1213 = _t1994
    _t1995 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1214 = _t1995
    consume_literal!(parser, ")")
    _t1996 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1212, namespace=iceberg_locator_namespace1213, warehouse=iceberg_locator_warehouse1214)
    result1216 = _t1996
    record_span!(parser, span_start1215, "IcebergLocator")
    return result1216
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1217 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1217
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1218 = String[]
    cond1219 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1219
        item1220 = consume_terminal!(parser, "STRING")
        push!(xs1218, item1220)
        cond1219 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1221 = xs1218
    consume_literal!(parser, ")")
    return strings1221
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1222 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1222
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1227 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t1997 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1223 = _t1997
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1999 = parse_iceberg_catalog_config_scope(parser)
        _t1998 = _t1999
    else
        _t1998 = nothing
    end
    iceberg_catalog_config_scope1224 = _t1998
    _t2000 = parse_iceberg_properties(parser)
    iceberg_properties1225 = _t2000
    _t2001 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1226 = _t2001
    consume_literal!(parser, ")")
    _t2002 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1223, iceberg_catalog_config_scope1224, iceberg_properties1225, iceberg_auth_properties1226)
    result1228 = _t2002
    record_span!(parser, span_start1227, "IcebergCatalogConfig")
    return result1228
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1229 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1229
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1230 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1230
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1231 = Tuple{String, String}[]
    cond1232 = match_lookahead_literal(parser, "(", 0)
    while cond1232
        _t2003 = parse_iceberg_property_entry(parser)
        item1233 = _t2003
        push!(xs1231, item1233)
        cond1232 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1234 = xs1231
    consume_literal!(parser, ")")
    return iceberg_property_entrys1234
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1235 = consume_terminal!(parser, "STRING")
    string_31236 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1235, string_31236,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1237 = Tuple{String, String}[]
    cond1238 = match_lookahead_literal(parser, "(", 0)
    while cond1238
        _t2004 = parse_iceberg_masked_property_entry(parser)
        item1239 = _t2004
        push!(xs1237, item1239)
        cond1238 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1240 = xs1237
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1240
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1241 = consume_terminal!(parser, "STRING")
    string_31242 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1241, string_31242,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1243 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1243
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1244 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1244
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1246 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2005 = parse_fragment_id(parser)
    fragment_id1245 = _t2005
    consume_literal!(parser, ")")
    _t2006 = Proto.Undefine(fragment_id=fragment_id1245)
    result1247 = _t2006
    record_span!(parser, span_start1246, "Undefine")
    return result1247
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1252 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1248 = Proto.RelationId[]
    cond1249 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1249
        _t2007 = parse_relation_id(parser)
        item1250 = _t2007
        push!(xs1248, item1250)
        cond1249 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1251 = xs1248
    consume_literal!(parser, ")")
    _t2008 = Proto.Context(relations=relation_ids1251)
    result1253 = _t2008
    record_span!(parser, span_start1252, "Context")
    return result1253
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1259 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2009 = parse_edb_path(parser)
    edb_path1254 = _t2009
    xs1255 = Proto.SnapshotMapping[]
    cond1256 = match_lookahead_literal(parser, "[", 0)
    while cond1256
        _t2010 = parse_snapshot_mapping(parser)
        item1257 = _t2010
        push!(xs1255, item1257)
        cond1256 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1258 = xs1255
    consume_literal!(parser, ")")
    _t2011 = Proto.Snapshot(mappings=snapshot_mappings1258, prefix=edb_path1254)
    result1260 = _t2011
    record_span!(parser, span_start1259, "Snapshot")
    return result1260
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1263 = span_start(parser)
    _t2012 = parse_edb_path(parser)
    edb_path1261 = _t2012
    _t2013 = parse_relation_id(parser)
    relation_id1262 = _t2013
    _t2014 = Proto.SnapshotMapping(destination_path=edb_path1261, source_relation=relation_id1262)
    result1264 = _t2014
    record_span!(parser, span_start1263, "SnapshotMapping")
    return result1264
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1265 = Proto.Read[]
    cond1266 = match_lookahead_literal(parser, "(", 0)
    while cond1266
        _t2015 = parse_read(parser)
        item1267 = _t2015
        push!(xs1265, item1267)
        cond1266 = match_lookahead_literal(parser, "(", 0)
    end
    reads1268 = xs1265
    consume_literal!(parser, ")")
    return reads1268
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1275 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2017 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2018 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2019 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2020 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2021 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2022 = 3
                            else
                                _t2022 = -1
                            end
                            _t2021 = _t2022
                        end
                        _t2020 = _t2021
                    end
                    _t2019 = _t2020
                end
                _t2018 = _t2019
            end
            _t2017 = _t2018
        end
        _t2016 = _t2017
    else
        _t2016 = -1
    end
    prediction1269 = _t2016
    if prediction1269 == 4
        _t2024 = parse_export(parser)
        export1274 = _t2024
        _t2025 = Proto.Read(read_type=OneOf(:var"#export", export1274))
        _t2023 = _t2025
    else
        if prediction1269 == 3
            _t2027 = parse_abort(parser)
            abort1273 = _t2027
            _t2028 = Proto.Read(read_type=OneOf(:abort, abort1273))
            _t2026 = _t2028
        else
            if prediction1269 == 2
                _t2030 = parse_what_if(parser)
                what_if1272 = _t2030
                _t2031 = Proto.Read(read_type=OneOf(:what_if, what_if1272))
                _t2029 = _t2031
            else
                if prediction1269 == 1
                    _t2033 = parse_output(parser)
                    output1271 = _t2033
                    _t2034 = Proto.Read(read_type=OneOf(:output, output1271))
                    _t2032 = _t2034
                else
                    if prediction1269 == 0
                        _t2036 = parse_demand(parser)
                        demand1270 = _t2036
                        _t2037 = Proto.Read(read_type=OneOf(:demand, demand1270))
                        _t2035 = _t2037
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2032 = _t2035
                end
                _t2029 = _t2032
            end
            _t2026 = _t2029
        end
        _t2023 = _t2026
    end
    result1276 = _t2023
    record_span!(parser, span_start1275, "Read")
    return result1276
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1278 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2038 = parse_relation_id(parser)
    relation_id1277 = _t2038
    consume_literal!(parser, ")")
    _t2039 = Proto.Demand(relation_id=relation_id1277)
    result1279 = _t2039
    record_span!(parser, span_start1278, "Demand")
    return result1279
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1282 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2040 = parse_name(parser)
    name1280 = _t2040
    _t2041 = parse_relation_id(parser)
    relation_id1281 = _t2041
    consume_literal!(parser, ")")
    _t2042 = Proto.Output(name=name1280, relation_id=relation_id1281)
    result1283 = _t2042
    record_span!(parser, span_start1282, "Output")
    return result1283
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1286 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2043 = parse_name(parser)
    name1284 = _t2043
    _t2044 = parse_epoch(parser)
    epoch1285 = _t2044
    consume_literal!(parser, ")")
    _t2045 = Proto.WhatIf(branch=name1284, epoch=epoch1285)
    result1287 = _t2045
    record_span!(parser, span_start1286, "WhatIf")
    return result1287
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1290 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2047 = parse_name(parser)
        _t2046 = _t2047
    else
        _t2046 = nothing
    end
    name1288 = _t2046
    _t2048 = parse_relation_id(parser)
    relation_id1289 = _t2048
    consume_literal!(parser, ")")
    _t2049 = Proto.Abort(name=(!isnothing(name1288) ? name1288 : "abort"), relation_id=relation_id1289)
    result1291 = _t2049
    record_span!(parser, span_start1290, "Abort")
    return result1291
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1295 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2051 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2052 = 0
            else
                _t2052 = -1
            end
            _t2051 = _t2052
        end
        _t2050 = _t2051
    else
        _t2050 = -1
    end
    prediction1292 = _t2050
    if prediction1292 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2054 = parse_export_iceberg_config(parser)
        export_iceberg_config1294 = _t2054
        consume_literal!(parser, ")")
        _t2055 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1294))
        _t2053 = _t2055
    else
        if prediction1292 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2057 = parse_export_csv_config(parser)
            export_csv_config1293 = _t2057
            consume_literal!(parser, ")")
            _t2058 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1293))
            _t2056 = _t2058
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2053 = _t2056
    end
    result1296 = _t2053
    record_span!(parser, span_start1295, "Export")
    return result1296
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1304 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2060 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2061 = 1
            else
                _t2061 = -1
            end
            _t2060 = _t2061
        end
        _t2059 = _t2060
    else
        _t2059 = -1
    end
    prediction1297 = _t2059
    if prediction1297 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2063 = parse_export_csv_path(parser)
        export_csv_path1301 = _t2063
        _t2064 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1302 = _t2064
        _t2065 = parse_config_dict(parser)
        config_dict1303 = _t2065
        consume_literal!(parser, ")")
        _t2066 = construct_export_csv_config(parser, export_csv_path1301, export_csv_columns_list1302, config_dict1303)
        _t2062 = _t2066
    else
        if prediction1297 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2068 = parse_export_csv_output_location(parser)
            export_csv_output_location1298 = _t2068
            _t2069 = parse_export_csv_source(parser)
            export_csv_source1299 = _t2069
            _t2070 = parse_csv_config(parser)
            csv_config1300 = _t2070
            consume_literal!(parser, ")")
            _t2071 = construct_export_csv_config_with_location(parser, export_csv_output_location1298, export_csv_source1299, csv_config1300)
            _t2067 = _t2071
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2062 = _t2067
    end
    result1305 = _t2062
    record_span!(parser, span_start1304, "ExportCSVConfig")
    return result1305
end

function parse_export_csv_output_location(parser::ParserState)::Tuple{String, String}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "transaction_output_name", 1)
            _t2073 = 1
        else
            if match_lookahead_literal(parser, "path", 1)
                _t2074 = 0
            else
                _t2074 = -1
            end
            _t2073 = _t2074
        end
        _t2072 = _t2073
    else
        _t2072 = -1
    end
    prediction1306 = _t2072
    if prediction1306 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "transaction_output_name")
        _t2076 = parse_name(parser)
        name1308 = _t2076
        consume_literal!(parser, ")")
        _t2075 = ("", name1308,)
    else
        if prediction1306 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "path")
            string1307 = consume_terminal!(parser, "STRING")
            consume_literal!(parser, ")")
            _t2077 = (string1307, "",)
        else
            throw(ParseError("Unexpected token in export_csv_output_location" * ": " * string(lookahead(parser, 0))))
        end
        _t2075 = _t2077
    end
    return _t2075
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1315 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2079 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2080 = 0
            else
                _t2080 = -1
            end
            _t2079 = _t2080
        end
        _t2078 = _t2079
    else
        _t2078 = -1
    end
    prediction1309 = _t2078
    if prediction1309 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2082 = parse_relation_id(parser)
        relation_id1314 = _t2082
        consume_literal!(parser, ")")
        _t2083 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1314))
        _t2081 = _t2083
    else
        if prediction1309 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1310 = Proto.ExportCSVColumn[]
            cond1311 = match_lookahead_literal(parser, "(", 0)
            while cond1311
                _t2085 = parse_export_csv_column(parser)
                item1312 = _t2085
                push!(xs1310, item1312)
                cond1311 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1313 = xs1310
            consume_literal!(parser, ")")
            _t2086 = Proto.ExportCSVColumns(columns=export_csv_columns1313)
            _t2087 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2086))
            _t2084 = _t2087
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2081 = _t2084
    end
    result1316 = _t2081
    record_span!(parser, span_start1315, "ExportCSVSource")
    return result1316
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1319 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1317 = consume_terminal!(parser, "STRING")
    _t2088 = parse_relation_id(parser)
    relation_id1318 = _t2088
    consume_literal!(parser, ")")
    _t2089 = Proto.ExportCSVColumn(column_name=string1317, column_data=relation_id1318)
    result1320 = _t2089
    record_span!(parser, span_start1319, "ExportCSVColumn")
    return result1320
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1321 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1321
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1322 = Proto.ExportCSVColumn[]
    cond1323 = match_lookahead_literal(parser, "(", 0)
    while cond1323
        _t2090 = parse_export_csv_column(parser)
        item1324 = _t2090
        push!(xs1322, item1324)
        cond1323 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1325 = xs1322
    consume_literal!(parser, ")")
    return export_csv_columns1325
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1331 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2091 = parse_iceberg_locator(parser)
    iceberg_locator1326 = _t2091
    _t2092 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1327 = _t2092
    _t2093 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1328 = _t2093
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
    _t2097 = construct_export_iceberg_config_full(parser, iceberg_locator1326, iceberg_catalog_config1327, export_iceberg_table_def1328, iceberg_table_properties1329, config_dict1330)
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

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1336 = Tuple{String, String}[]
    cond1337 = match_lookahead_literal(parser, "(", 0)
    while cond1337
        _t2099 = parse_iceberg_property_entry(parser)
        item1338 = _t2099
        push!(xs1336, item1338)
        cond1337 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1339 = xs1336
    consume_literal!(parser, ")")
    return iceberg_property_entrys1339
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
