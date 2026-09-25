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
    if isnothing(value)
        return Int32(default)
    else
        _t2233 = nothing
    end
    if _has_proto_field(value, Symbol("int32_value"))
        return _get_oneof_field(value, :int32_value)
    else
        _t2234 = nothing
    end
    throw(ParseError("expected an int32 value (e.g. `1i32`) for this config field"))
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2235 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2236 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2237 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2238 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2239 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2240 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2241 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2242 = nothing
    end
    return nothing
end

function construct_non_cdc_relations(parser::ParserState, targets::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2243 = Proto.PlainTargets(targets=targets)
    _t2244 = Proto.TargetRelations(body=OneOf(:plain, _t2243), keys=Proto.NamedColumn[])
    return _t2244
end

function construct_cdc_relations(parser::ParserState, inserts::Vector{Proto.TargetRelation}, deletes::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2245 = Proto.CDCTargets(inserts=inserts, deletes=deletes)
    _t2246 = Proto.TargetRelations(body=OneOf(:cdc, _t2245), keys=Proto.NamedColumn[])
    return _t2246
end

function construct_relations(parser::ParserState, keys::Tuple{Vector{Proto.NamedColumn}, Bool}, body::Proto.TargetRelations, load_errors_opt::Union{Nothing, Proto.RelationId})::Proto.TargetRelations
    if _has_proto_field(body, Symbol("plain"))
        _t2248 = Proto.TargetRelations(body=OneOf(:plain, _get_oneof_field(body, :plain)), keys=keys[1], synthetic_key=keys[2], load_errors=load_errors_opt)
        return _t2248
    else
        _t2247 = nothing
    end
    _t2249 = Proto.TargetRelations(body=OneOf(:cdc, _get_oneof_field(body, :cdc)), keys=keys[1], synthetic_key=keys[2], load_errors=load_errors_opt)
    return _t2249
end

function construct_csv_data(parser::ParserState, locator::Proto.CSVLocator, config::Proto.CSVConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, relations_opt::Union{Nothing, Proto.TargetRelations}, asof::String)::Proto.CSVData
    _t2250 = Proto.CSVData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), asof=asof, relations=relations_opt)
    return _t2250
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2251 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2251
    _t2252 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2252
    _t2253 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2253
    _t2254 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2254
    _t2255 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2255
    _t2256 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2256
    _t2257 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2257
    _t2258 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2258
    _t2259 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2259
    _t2260 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2260
    _t2261 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2261
    _t2262 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2262
    _t2263 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2263
    _t2264 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2264
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2265 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2266 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2267 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2268 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2269 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2270 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2271 = Proto.StorageIntegration(provider=_t2266, azure_sas_token=_t2267, s3_region=_t2268, s3_access_key_id=_t2269, s3_secret_access_key=_t2270)
    return _t2271
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2272 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2272
    _t2273 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2273
    _t2274 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2274
    _t2275 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2275
    _t2276 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2276
    _t2277 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2277
    _t2278 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2278
    _t2279 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2279
    _t2280 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2280
    _t2281 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2281
    _t2282 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2282
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2283 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2283
    _t2284 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2284
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
    _t2285 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2285
    _t2286 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2286
    config_values_pairs = Tuple{String, Proto.Value}[]
    for pair in config_dict
        if (pair[1] != "semantics_version" && pair[1] != "ivm.maintenance_level")
            push!(config_values_pairs, pair)
        end
    end
    configuration_values = Dict(config_values_pairs)
    _t2287 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config, configuration_values=configuration_values)
    return _t2287
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2288 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2288
    _t2289 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2289
    _t2290 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2290
    _t2291 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2291
    _t2292 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2292
    _t2293 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2293
    _t2294 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2294
    _t2295 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2295
end

function construct_export_csv_config_with_location(parser::ParserState, location::Tuple{String, String}, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2296 = Proto.ExportCSVConfig(path=location[1], transaction_output_name=location[2], csv_source=csv_source, csv_config=csv_config)
    return _t2296
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2297 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2297
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2298 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2298
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2299 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2299
    _t2300 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2300
    _t2301 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2301
    table_props = Dict(table_property_pairs)
    _t2302 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2302
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start722 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1433 = parse_configure(parser)
        _t1432 = _t1433
    else
        _t1432 = nothing
    end
    configure716 = _t1432
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1435 = parse_sync(parser)
        _t1434 = _t1435
    else
        _t1434 = nothing
    end
    sync717 = _t1434
    xs718 = Proto.Epoch[]
    cond719 = match_lookahead_literal(parser, "(", 0)
    while cond719
        _t1436 = parse_epoch(parser)
        item720 = _t1436
        push!(xs718, item720)
        cond719 = match_lookahead_literal(parser, "(", 0)
    end
    epochs721 = xs718
    consume_literal!(parser, ")")
    _t1437 = default_configure(parser)
    _t1438 = Proto.Transaction(epochs=epochs721, configure=(!isnothing(configure716) ? configure716 : _t1437), sync=sync717)
    result723 = _t1438
    record_span!(parser, span_start722, "Transaction")
    return result723
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start725 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1439 = parse_config_dict(parser)
    config_dict724 = _t1439
    consume_literal!(parser, ")")
    _t1440 = construct_configure(parser, config_dict724)
    result726 = _t1440
    record_span!(parser, span_start725, "Configure")
    return result726
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs727 = Tuple{String, Proto.Value}[]
    cond728 = match_lookahead_literal(parser, ":", 0)
    while cond728
        _t1441 = parse_config_key_value(parser)
        item729 = _t1441
        push!(xs727, item729)
        cond728 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values730 = xs727
    consume_literal!(parser, "}")
    return config_key_values730
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol731 = consume_terminal!(parser, "SYMBOL")
    _t1442 = parse_raw_value(parser)
    raw_value732 = _t1442
    return (symbol731, raw_value732,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start746 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1443 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1444 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1445 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1447 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1448 = 0
                        else
                            _t1448 = -1
                        end
                        _t1447 = _t1448
                    end
                    _t1446 = _t1447
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1449 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1450 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1451 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1452 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1453 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1454 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1455 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1456 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1457 = 10
                                                    else
                                                        _t1457 = -1
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
                    _t1446 = _t1449
                end
                _t1445 = _t1446
            end
            _t1444 = _t1445
        end
        _t1443 = _t1444
    end
    prediction733 = _t1443
    if prediction733 == 12
        _t1459 = parse_boolean_value(parser)
        boolean_value745 = _t1459
        _t1460 = Proto.Value(value=OneOf(:boolean_value, boolean_value745))
        _t1458 = _t1460
    else
        if prediction733 == 11
            consume_literal!(parser, "missing")
            _t1462 = Proto.MissingValue()
            _t1463 = Proto.Value(value=OneOf(:missing_value, _t1462))
            _t1461 = _t1463
        else
            if prediction733 == 10
                decimal744 = consume_terminal!(parser, "DECIMAL")
                _t1465 = Proto.Value(value=OneOf(:decimal_value, decimal744))
                _t1464 = _t1465
            else
                if prediction733 == 9
                    int128743 = consume_terminal!(parser, "INT128")
                    _t1467 = Proto.Value(value=OneOf(:int128_value, int128743))
                    _t1466 = _t1467
                else
                    if prediction733 == 8
                        uint128742 = consume_terminal!(parser, "UINT128")
                        _t1469 = Proto.Value(value=OneOf(:uint128_value, uint128742))
                        _t1468 = _t1469
                    else
                        if prediction733 == 7
                            uint32741 = consume_terminal!(parser, "UINT32")
                            _t1471 = Proto.Value(value=OneOf(:uint32_value, uint32741))
                            _t1470 = _t1471
                        else
                            if prediction733 == 6
                                float740 = consume_terminal!(parser, "FLOAT")
                                _t1473 = Proto.Value(value=OneOf(:float_value, float740))
                                _t1472 = _t1473
                            else
                                if prediction733 == 5
                                    float32739 = consume_terminal!(parser, "FLOAT32")
                                    _t1475 = Proto.Value(value=OneOf(:float32_value, float32739))
                                    _t1474 = _t1475
                                else
                                    if prediction733 == 4
                                        int738 = consume_terminal!(parser, "INT")
                                        _t1477 = Proto.Value(value=OneOf(:int_value, int738))
                                        _t1476 = _t1477
                                    else
                                        if prediction733 == 3
                                            int32737 = consume_terminal!(parser, "INT32")
                                            _t1479 = Proto.Value(value=OneOf(:int32_value, int32737))
                                            _t1478 = _t1479
                                        else
                                            if prediction733 == 2
                                                string736 = consume_terminal!(parser, "STRING")
                                                _t1481 = Proto.Value(value=OneOf(:string_value, string736))
                                                _t1480 = _t1481
                                            else
                                                if prediction733 == 1
                                                    _t1483 = parse_raw_datetime(parser)
                                                    raw_datetime735 = _t1483
                                                    _t1484 = Proto.Value(value=OneOf(:datetime_value, raw_datetime735))
                                                    _t1482 = _t1484
                                                else
                                                    if prediction733 == 0
                                                        _t1486 = parse_raw_date(parser)
                                                        raw_date734 = _t1486
                                                        _t1487 = Proto.Value(value=OneOf(:date_value, raw_date734))
                                                        _t1485 = _t1487
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1482 = _t1485
                                                end
                                                _t1480 = _t1482
                                            end
                                            _t1478 = _t1480
                                        end
                                        _t1476 = _t1478
                                    end
                                    _t1474 = _t1476
                                end
                                _t1472 = _t1474
                            end
                            _t1470 = _t1472
                        end
                        _t1468 = _t1470
                    end
                    _t1466 = _t1468
                end
                _t1464 = _t1466
            end
            _t1461 = _t1464
        end
        _t1458 = _t1461
    end
    result747 = _t1458
    record_span!(parser, span_start746, "Value")
    return result747
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start751 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int748 = consume_terminal!(parser, "INT")
    int_3749 = consume_terminal!(parser, "INT")
    int_4750 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1488 = Proto.DateValue(year=Int32(int748), month=Int32(int_3749), day=Int32(int_4750))
    result752 = _t1488
    record_span!(parser, span_start751, "DateValue")
    return result752
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start760 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int753 = consume_terminal!(parser, "INT")
    int_3754 = consume_terminal!(parser, "INT")
    int_4755 = consume_terminal!(parser, "INT")
    int_5756 = consume_terminal!(parser, "INT")
    int_6757 = consume_terminal!(parser, "INT")
    int_7758 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1489 = consume_terminal!(parser, "INT")
    else
        _t1489 = nothing
    end
    int_8759 = _t1489
    consume_literal!(parser, ")")
    _t1490 = Proto.DateTimeValue(year=Int32(int753), month=Int32(int_3754), day=Int32(int_4755), hour=Int32(int_5756), minute=Int32(int_6757), second=Int32(int_7758), microsecond=Int32((!isnothing(int_8759) ? int_8759 : 0)))
    result761 = _t1490
    record_span!(parser, span_start760, "DateTimeValue")
    return result761
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1491 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1492 = 1
        else
            _t1492 = -1
        end
        _t1491 = _t1492
    end
    prediction762 = _t1491
    if prediction762 == 1
        consume_literal!(parser, "false")
        _t1493 = false
    else
        if prediction762 == 0
            consume_literal!(parser, "true")
            _t1494 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1493 = _t1494
    end
    return _t1493
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start767 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs763 = Proto.FragmentId[]
    cond764 = match_lookahead_literal(parser, ":", 0)
    while cond764
        _t1495 = parse_fragment_id(parser)
        item765 = _t1495
        push!(xs763, item765)
        cond764 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids766 = xs763
    consume_literal!(parser, ")")
    _t1496 = Proto.Sync(fragments=fragment_ids766)
    result768 = _t1496
    record_span!(parser, span_start767, "Sync")
    return result768
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start770 = span_start(parser)
    consume_literal!(parser, ":")
    symbol769 = consume_terminal!(parser, "SYMBOL")
    result771 = Proto.FragmentId(Vector{UInt8}(symbol769))
    record_span!(parser, span_start770, "FragmentId")
    return result771
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start774 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1498 = parse_epoch_writes(parser)
        _t1497 = _t1498
    else
        _t1497 = nothing
    end
    epoch_writes772 = _t1497
    if match_lookahead_literal(parser, "(", 0)
        _t1500 = parse_epoch_reads(parser)
        _t1499 = _t1500
    else
        _t1499 = nothing
    end
    epoch_reads773 = _t1499
    consume_literal!(parser, ")")
    _t1501 = Proto.Epoch(writes=(!isnothing(epoch_writes772) ? epoch_writes772 : Proto.Write[]), reads=(!isnothing(epoch_reads773) ? epoch_reads773 : Proto.Read[]))
    result775 = _t1501
    record_span!(parser, span_start774, "Epoch")
    return result775
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs776 = Proto.Write[]
    cond777 = match_lookahead_literal(parser, "(", 0)
    while cond777
        _t1502 = parse_write(parser)
        item778 = _t1502
        push!(xs776, item778)
        cond777 = match_lookahead_literal(parser, "(", 0)
    end
    writes779 = xs776
    consume_literal!(parser, ")")
    return writes779
end

function parse_write(parser::ParserState)::Proto.Write
    span_start785 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1504 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1505 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1506 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1507 = 2
                    else
                        _t1507 = -1
                    end
                    _t1506 = _t1507
                end
                _t1505 = _t1506
            end
            _t1504 = _t1505
        end
        _t1503 = _t1504
    else
        _t1503 = -1
    end
    prediction780 = _t1503
    if prediction780 == 3
        _t1509 = parse_snapshot(parser)
        snapshot784 = _t1509
        _t1510 = Proto.Write(write_type=OneOf(:snapshot, snapshot784))
        _t1508 = _t1510
    else
        if prediction780 == 2
            _t1512 = parse_context(parser)
            context783 = _t1512
            _t1513 = Proto.Write(write_type=OneOf(:context, context783))
            _t1511 = _t1513
        else
            if prediction780 == 1
                _t1515 = parse_undefine(parser)
                undefine782 = _t1515
                _t1516 = Proto.Write(write_type=OneOf(:undefine, undefine782))
                _t1514 = _t1516
            else
                if prediction780 == 0
                    _t1518 = parse_define(parser)
                    define781 = _t1518
                    _t1519 = Proto.Write(write_type=OneOf(:define, define781))
                    _t1517 = _t1519
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1514 = _t1517
            end
            _t1511 = _t1514
        end
        _t1508 = _t1511
    end
    result786 = _t1508
    record_span!(parser, span_start785, "Write")
    return result786
end

function parse_define(parser::ParserState)::Proto.Define
    span_start788 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1520 = parse_fragment(parser)
    fragment787 = _t1520
    consume_literal!(parser, ")")
    _t1521 = Proto.Define(fragment=fragment787)
    result789 = _t1521
    record_span!(parser, span_start788, "Define")
    return result789
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start795 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1522 = parse_new_fragment_id(parser)
    new_fragment_id790 = _t1522
    xs791 = Proto.Declaration[]
    cond792 = match_lookahead_literal(parser, "(", 0)
    while cond792
        _t1523 = parse_declaration(parser)
        item793 = _t1523
        push!(xs791, item793)
        cond792 = match_lookahead_literal(parser, "(", 0)
    end
    declarations794 = xs791
    consume_literal!(parser, ")")
    result796 = construct_fragment(parser, new_fragment_id790, declarations794)
    record_span!(parser, span_start795, "Fragment")
    return result796
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start798 = span_start(parser)
    _t1524 = parse_fragment_id(parser)
    fragment_id797 = _t1524
    start_fragment!(parser, fragment_id797)
    result799 = fragment_id797
    record_span!(parser, span_start798, "FragmentId")
    return result799
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start805 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1526 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1527 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1528 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1529 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1530 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1531 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1532 = 1
                                else
                                    _t1532 = -1
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
    else
        _t1525 = -1
    end
    prediction800 = _t1525
    if prediction800 == 3
        _t1534 = parse_data(parser)
        data804 = _t1534
        _t1535 = Proto.Declaration(declaration_type=OneOf(:data, data804))
        _t1533 = _t1535
    else
        if prediction800 == 2
            _t1537 = parse_constraint(parser)
            constraint803 = _t1537
            _t1538 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint803))
            _t1536 = _t1538
        else
            if prediction800 == 1
                _t1540 = parse_algorithm(parser)
                algorithm802 = _t1540
                _t1541 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm802))
                _t1539 = _t1541
            else
                if prediction800 == 0
                    _t1543 = parse_def(parser)
                    def801 = _t1543
                    _t1544 = Proto.Declaration(declaration_type=OneOf(:def, def801))
                    _t1542 = _t1544
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1539 = _t1542
            end
            _t1536 = _t1539
        end
        _t1533 = _t1536
    end
    result806 = _t1533
    record_span!(parser, span_start805, "Declaration")
    return result806
end

function parse_def(parser::ParserState)::Proto.Def
    span_start810 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1545 = parse_relation_id(parser)
    relation_id807 = _t1545
    _t1546 = parse_abstraction(parser)
    abstraction808 = _t1546
    if match_lookahead_literal(parser, "(", 0)
        _t1548 = parse_attrs(parser)
        _t1547 = _t1548
    else
        _t1547 = nothing
    end
    attrs809 = _t1547
    consume_literal!(parser, ")")
    _t1549 = Proto.Def(name=relation_id807, body=abstraction808, attrs=(!isnothing(attrs809) ? attrs809 : Proto.Attribute[]))
    result811 = _t1549
    record_span!(parser, span_start810, "Def")
    return result811
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start815 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1550 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1551 = 1
        else
            _t1551 = -1
        end
        _t1550 = _t1551
    end
    prediction812 = _t1550
    if prediction812 == 1
        uint128814 = consume_terminal!(parser, "UINT128")
        _t1552 = Proto.RelationId(uint128814.low, uint128814.high)
    else
        if prediction812 == 0
            consume_literal!(parser, ":")
            symbol813 = consume_terminal!(parser, "SYMBOL")
            _t1553 = relation_id_from_string(parser, symbol813)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1552 = _t1553
    end
    result816 = _t1552
    record_span!(parser, span_start815, "RelationId")
    return result816
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start819 = span_start(parser)
    consume_literal!(parser, "(")
    _t1554 = parse_bindings(parser)
    bindings817 = _t1554
    _t1555 = parse_formula(parser)
    formula818 = _t1555
    consume_literal!(parser, ")")
    _t1556 = Proto.Abstraction(vars=vcat(bindings817[1], !isnothing(bindings817[2]) ? bindings817[2] : []), value=formula818)
    result820 = _t1556
    record_span!(parser, span_start819, "Abstraction")
    return result820
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs821 = Proto.Binding[]
    cond822 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond822
        _t1557 = parse_binding(parser)
        item823 = _t1557
        push!(xs821, item823)
        cond822 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings824 = xs821
    if match_lookahead_literal(parser, "|", 0)
        _t1559 = parse_value_bindings(parser)
        _t1558 = _t1559
    else
        _t1558 = nothing
    end
    value_bindings825 = _t1558
    consume_literal!(parser, "]")
    return (bindings824, (!isnothing(value_bindings825) ? value_bindings825 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start828 = span_start(parser)
    symbol826 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1560 = parse_type(parser)
    type827 = _t1560
    _t1561 = Proto.Var(name=symbol826)
    _t1562 = Proto.Binding(var=_t1561, var"#type"=type827)
    result829 = _t1562
    record_span!(parser, span_start828, "Binding")
    return result829
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start846 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1563 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1564 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1565 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1566 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1567 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1568 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1569 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1570 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1571 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1572 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1573 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1574 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1575 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            if match_lookahead_literal(parser, "FIXED", 1)
                                                                _t1577 = 14
                                                            else
                                                                if match_lookahead_literal(parser, "DECIMAL", 1)
                                                                    _t1578 = 9
                                                                else
                                                                    _t1578 = -1
                                                                end
                                                                _t1577 = _t1578
                                                            end
                                                            _t1576 = _t1577
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
    prediction830 = _t1563
    if prediction830 == 14
        _t1580 = parse_fixed_type(parser)
        fixed_type845 = _t1580
        _t1581 = Proto.var"#Type"(var"#type"=OneOf(:fixed_type, fixed_type845))
        _t1579 = _t1581
    else
        if prediction830 == 13
            _t1583 = parse_uint32_type(parser)
            uint32_type844 = _t1583
            _t1584 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type844))
            _t1582 = _t1584
        else
            if prediction830 == 12
                _t1586 = parse_float32_type(parser)
                float32_type843 = _t1586
                _t1587 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type843))
                _t1585 = _t1587
            else
                if prediction830 == 11
                    _t1589 = parse_int32_type(parser)
                    int32_type842 = _t1589
                    _t1590 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type842))
                    _t1588 = _t1590
                else
                    if prediction830 == 10
                        _t1592 = parse_boolean_type(parser)
                        boolean_type841 = _t1592
                        _t1593 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type841))
                        _t1591 = _t1593
                    else
                        if prediction830 == 9
                            _t1595 = parse_decimal_type(parser)
                            decimal_type840 = _t1595
                            _t1596 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type840))
                            _t1594 = _t1596
                        else
                            if prediction830 == 8
                                _t1598 = parse_missing_type(parser)
                                missing_type839 = _t1598
                                _t1599 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type839))
                                _t1597 = _t1599
                            else
                                if prediction830 == 7
                                    _t1601 = parse_datetime_type(parser)
                                    datetime_type838 = _t1601
                                    _t1602 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type838))
                                    _t1600 = _t1602
                                else
                                    if prediction830 == 6
                                        _t1604 = parse_date_type(parser)
                                        date_type837 = _t1604
                                        _t1605 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type837))
                                        _t1603 = _t1605
                                    else
                                        if prediction830 == 5
                                            _t1607 = parse_int128_type(parser)
                                            int128_type836 = _t1607
                                            _t1608 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type836))
                                            _t1606 = _t1608
                                        else
                                            if prediction830 == 4
                                                _t1610 = parse_uint128_type(parser)
                                                uint128_type835 = _t1610
                                                _t1611 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type835))
                                                _t1609 = _t1611
                                            else
                                                if prediction830 == 3
                                                    _t1613 = parse_float_type(parser)
                                                    float_type834 = _t1613
                                                    _t1614 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type834))
                                                    _t1612 = _t1614
                                                else
                                                    if prediction830 == 2
                                                        _t1616 = parse_int_type(parser)
                                                        int_type833 = _t1616
                                                        _t1617 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type833))
                                                        _t1615 = _t1617
                                                    else
                                                        if prediction830 == 1
                                                            _t1619 = parse_string_type(parser)
                                                            string_type832 = _t1619
                                                            _t1620 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type832))
                                                            _t1618 = _t1620
                                                        else
                                                            if prediction830 == 0
                                                                _t1622 = parse_unspecified_type(parser)
                                                                unspecified_type831 = _t1622
                                                                _t1623 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type831))
                                                                _t1621 = _t1623
                                                            else
                                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                            end
                                                            _t1618 = _t1621
                                                        end
                                                        _t1615 = _t1618
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
    result847 = _t1579
    record_span!(parser, span_start846, "Type")
    return result847
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start848 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1624 = Proto.UnspecifiedType()
    result849 = _t1624
    record_span!(parser, span_start848, "UnspecifiedType")
    return result849
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start850 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1625 = Proto.StringType()
    result851 = _t1625
    record_span!(parser, span_start850, "StringType")
    return result851
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start852 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1626 = Proto.IntType()
    result853 = _t1626
    record_span!(parser, span_start852, "IntType")
    return result853
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start854 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1627 = Proto.FloatType()
    result855 = _t1627
    record_span!(parser, span_start854, "FloatType")
    return result855
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start856 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1628 = Proto.UInt128Type()
    result857 = _t1628
    record_span!(parser, span_start856, "UInt128Type")
    return result857
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start858 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1629 = Proto.Int128Type()
    result859 = _t1629
    record_span!(parser, span_start858, "Int128Type")
    return result859
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start860 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1630 = Proto.DateType()
    result861 = _t1630
    record_span!(parser, span_start860, "DateType")
    return result861
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start862 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1631 = Proto.DateTimeType()
    result863 = _t1631
    record_span!(parser, span_start862, "DateTimeType")
    return result863
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start864 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1632 = Proto.MissingType()
    result865 = _t1632
    record_span!(parser, span_start864, "MissingType")
    return result865
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start868 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int866 = consume_terminal!(parser, "INT")
    int_3867 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1633 = Proto.DecimalType(precision=Int32(int866), scale=Int32(int_3867))
    result869 = _t1633
    record_span!(parser, span_start868, "DecimalType")
    return result869
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start870 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1634 = Proto.BooleanType()
    result871 = _t1634
    record_span!(parser, span_start870, "BooleanType")
    return result871
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start872 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1635 = Proto.Int32Type()
    result873 = _t1635
    record_span!(parser, span_start872, "Int32Type")
    return result873
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start874 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1636 = Proto.Float32Type()
    result875 = _t1636
    record_span!(parser, span_start874, "Float32Type")
    return result875
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start876 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1637 = Proto.UInt32Type()
    result877 = _t1637
    record_span!(parser, span_start876, "UInt32Type")
    return result877
end

function parse_fixed_type(parser::ParserState)::Proto.FixedType
    span_start879 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "FIXED")
    int878 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1638 = Proto.FixedType(length=Int32(int878))
    result880 = _t1638
    record_span!(parser, span_start879, "FixedType")
    return result880
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs881 = Proto.Binding[]
    cond882 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond882
        _t1639 = parse_binding(parser)
        item883 = _t1639
        push!(xs881, item883)
        cond882 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings884 = xs881
    return bindings884
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start899 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1641 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1642 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1643 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1644 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1645 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1646 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1647 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1648 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1649 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1650 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1651 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1652 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1653 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1654 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1655 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1656 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1657 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1658 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1659 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1660 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1661 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
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
            _t1641 = _t1642
        end
        _t1640 = _t1641
    else
        _t1640 = -1
    end
    prediction885 = _t1640
    if prediction885 == 12
        _t1664 = parse_cast(parser)
        cast898 = _t1664
        _t1665 = Proto.Formula(formula_type=OneOf(:cast, cast898))
        _t1663 = _t1665
    else
        if prediction885 == 11
            _t1667 = parse_rel_atom(parser)
            rel_atom897 = _t1667
            _t1668 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom897))
            _t1666 = _t1668
        else
            if prediction885 == 10
                _t1670 = parse_primitive(parser)
                primitive896 = _t1670
                _t1671 = Proto.Formula(formula_type=OneOf(:primitive, primitive896))
                _t1669 = _t1671
            else
                if prediction885 == 9
                    _t1673 = parse_pragma(parser)
                    pragma895 = _t1673
                    _t1674 = Proto.Formula(formula_type=OneOf(:pragma, pragma895))
                    _t1672 = _t1674
                else
                    if prediction885 == 8
                        _t1676 = parse_atom(parser)
                        atom894 = _t1676
                        _t1677 = Proto.Formula(formula_type=OneOf(:atom, atom894))
                        _t1675 = _t1677
                    else
                        if prediction885 == 7
                            _t1679 = parse_ffi(parser)
                            ffi893 = _t1679
                            _t1680 = Proto.Formula(formula_type=OneOf(:ffi, ffi893))
                            _t1678 = _t1680
                        else
                            if prediction885 == 6
                                _t1682 = parse_not(parser)
                                not892 = _t1682
                                _t1683 = Proto.Formula(formula_type=OneOf(:not, not892))
                                _t1681 = _t1683
                            else
                                if prediction885 == 5
                                    _t1685 = parse_disjunction(parser)
                                    disjunction891 = _t1685
                                    _t1686 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction891))
                                    _t1684 = _t1686
                                else
                                    if prediction885 == 4
                                        _t1688 = parse_conjunction(parser)
                                        conjunction890 = _t1688
                                        _t1689 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction890))
                                        _t1687 = _t1689
                                    else
                                        if prediction885 == 3
                                            _t1691 = parse_reduce(parser)
                                            reduce889 = _t1691
                                            _t1692 = Proto.Formula(formula_type=OneOf(:reduce, reduce889))
                                            _t1690 = _t1692
                                        else
                                            if prediction885 == 2
                                                _t1694 = parse_exists(parser)
                                                exists888 = _t1694
                                                _t1695 = Proto.Formula(formula_type=OneOf(:exists, exists888))
                                                _t1693 = _t1695
                                            else
                                                if prediction885 == 1
                                                    _t1697 = parse_false(parser)
                                                    false887 = _t1697
                                                    _t1698 = Proto.Formula(formula_type=OneOf(:disjunction, false887))
                                                    _t1696 = _t1698
                                                else
                                                    if prediction885 == 0
                                                        _t1700 = parse_true(parser)
                                                        true886 = _t1700
                                                        _t1701 = Proto.Formula(formula_type=OneOf(:conjunction, true886))
                                                        _t1699 = _t1701
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1696 = _t1699
                                                end
                                                _t1693 = _t1696
                                            end
                                            _t1690 = _t1693
                                        end
                                        _t1687 = _t1690
                                    end
                                    _t1684 = _t1687
                                end
                                _t1681 = _t1684
                            end
                            _t1678 = _t1681
                        end
                        _t1675 = _t1678
                    end
                    _t1672 = _t1675
                end
                _t1669 = _t1672
            end
            _t1666 = _t1669
        end
        _t1663 = _t1666
    end
    result900 = _t1663
    record_span!(parser, span_start899, "Formula")
    return result900
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start901 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1702 = Proto.Conjunction(args=Proto.Formula[])
    result902 = _t1702
    record_span!(parser, span_start901, "Conjunction")
    return result902
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start903 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1703 = Proto.Disjunction(args=Proto.Formula[])
    result904 = _t1703
    record_span!(parser, span_start903, "Disjunction")
    return result904
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start907 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1704 = parse_bindings(parser)
    bindings905 = _t1704
    _t1705 = parse_formula(parser)
    formula906 = _t1705
    consume_literal!(parser, ")")
    _t1706 = Proto.Abstraction(vars=vcat(bindings905[1], !isnothing(bindings905[2]) ? bindings905[2] : []), value=formula906)
    _t1707 = Proto.Exists(body=_t1706)
    result908 = _t1707
    record_span!(parser, span_start907, "Exists")
    return result908
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start912 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1708 = parse_abstraction(parser)
    abstraction909 = _t1708
    _t1709 = parse_abstraction(parser)
    abstraction_3910 = _t1709
    _t1710 = parse_terms(parser)
    terms911 = _t1710
    consume_literal!(parser, ")")
    _t1711 = Proto.Reduce(op=abstraction909, body=abstraction_3910, terms=terms911)
    result913 = _t1711
    record_span!(parser, span_start912, "Reduce")
    return result913
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs914 = Proto.Term[]
    cond915 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond915
        _t1712 = parse_term(parser)
        item916 = _t1712
        push!(xs914, item916)
        cond915 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms917 = xs914
    consume_literal!(parser, ")")
    return terms917
end

function parse_term(parser::ParserState)::Proto.Term
    span_start921 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1713 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1714 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1715 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1716 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1717 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1718 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1719 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1720 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1721 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1722 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1723 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1724 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1725 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1726 = 1
                                                        else
                                                            _t1726 = -1
                                                        end
                                                        _t1725 = _t1726
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
            end
            _t1714 = _t1715
        end
        _t1713 = _t1714
    end
    prediction918 = _t1713
    if prediction918 == 1
        _t1728 = parse_value(parser)
        value920 = _t1728
        _t1729 = Proto.Term(term_type=OneOf(:constant, value920))
        _t1727 = _t1729
    else
        if prediction918 == 0
            _t1731 = parse_var(parser)
            var919 = _t1731
            _t1732 = Proto.Term(term_type=OneOf(:var, var919))
            _t1730 = _t1732
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1727 = _t1730
    end
    result922 = _t1727
    record_span!(parser, span_start921, "Term")
    return result922
end

function parse_var(parser::ParserState)::Proto.Var
    span_start924 = span_start(parser)
    symbol923 = consume_terminal!(parser, "SYMBOL")
    _t1733 = Proto.Var(name=symbol923)
    result925 = _t1733
    record_span!(parser, span_start924, "Var")
    return result925
end

function parse_value(parser::ParserState)::Proto.Value
    span_start939 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1734 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1735 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1736 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1738 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1739 = 0
                        else
                            _t1739 = -1
                        end
                        _t1738 = _t1739
                    end
                    _t1737 = _t1738
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1740 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1741 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1742 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1743 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1744 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1745 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1746 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1747 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1748 = 10
                                                    else
                                                        _t1748 = -1
                                                    end
                                                    _t1747 = _t1748
                                                end
                                                _t1746 = _t1747
                                            end
                                            _t1745 = _t1746
                                        end
                                        _t1744 = _t1745
                                    end
                                    _t1743 = _t1744
                                end
                                _t1742 = _t1743
                            end
                            _t1741 = _t1742
                        end
                        _t1740 = _t1741
                    end
                    _t1737 = _t1740
                end
                _t1736 = _t1737
            end
            _t1735 = _t1736
        end
        _t1734 = _t1735
    end
    prediction926 = _t1734
    if prediction926 == 12
        _t1750 = parse_boolean_value(parser)
        boolean_value938 = _t1750
        _t1751 = Proto.Value(value=OneOf(:boolean_value, boolean_value938))
        _t1749 = _t1751
    else
        if prediction926 == 11
            consume_literal!(parser, "missing")
            _t1753 = Proto.MissingValue()
            _t1754 = Proto.Value(value=OneOf(:missing_value, _t1753))
            _t1752 = _t1754
        else
            if prediction926 == 10
                formatted_decimal937 = consume_terminal!(parser, "DECIMAL")
                _t1756 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal937))
                _t1755 = _t1756
            else
                if prediction926 == 9
                    formatted_int128936 = consume_terminal!(parser, "INT128")
                    _t1758 = Proto.Value(value=OneOf(:int128_value, formatted_int128936))
                    _t1757 = _t1758
                else
                    if prediction926 == 8
                        formatted_uint128935 = consume_terminal!(parser, "UINT128")
                        _t1760 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128935))
                        _t1759 = _t1760
                    else
                        if prediction926 == 7
                            formatted_uint32934 = consume_terminal!(parser, "UINT32")
                            _t1762 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32934))
                            _t1761 = _t1762
                        else
                            if prediction926 == 6
                                formatted_float933 = consume_terminal!(parser, "FLOAT")
                                _t1764 = Proto.Value(value=OneOf(:float_value, formatted_float933))
                                _t1763 = _t1764
                            else
                                if prediction926 == 5
                                    formatted_float32932 = consume_terminal!(parser, "FLOAT32")
                                    _t1766 = Proto.Value(value=OneOf(:float32_value, formatted_float32932))
                                    _t1765 = _t1766
                                else
                                    if prediction926 == 4
                                        formatted_int931 = consume_terminal!(parser, "INT")
                                        _t1768 = Proto.Value(value=OneOf(:int_value, formatted_int931))
                                        _t1767 = _t1768
                                    else
                                        if prediction926 == 3
                                            formatted_int32930 = consume_terminal!(parser, "INT32")
                                            _t1770 = Proto.Value(value=OneOf(:int32_value, formatted_int32930))
                                            _t1769 = _t1770
                                        else
                                            if prediction926 == 2
                                                formatted_string929 = consume_terminal!(parser, "STRING")
                                                _t1772 = Proto.Value(value=OneOf(:string_value, formatted_string929))
                                                _t1771 = _t1772
                                            else
                                                if prediction926 == 1
                                                    _t1774 = parse_datetime(parser)
                                                    datetime928 = _t1774
                                                    _t1775 = Proto.Value(value=OneOf(:datetime_value, datetime928))
                                                    _t1773 = _t1775
                                                else
                                                    if prediction926 == 0
                                                        _t1777 = parse_date(parser)
                                                        date927 = _t1777
                                                        _t1778 = Proto.Value(value=OneOf(:date_value, date927))
                                                        _t1776 = _t1778
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1773 = _t1776
                                                end
                                                _t1771 = _t1773
                                            end
                                            _t1769 = _t1771
                                        end
                                        _t1767 = _t1769
                                    end
                                    _t1765 = _t1767
                                end
                                _t1763 = _t1765
                            end
                            _t1761 = _t1763
                        end
                        _t1759 = _t1761
                    end
                    _t1757 = _t1759
                end
                _t1755 = _t1757
            end
            _t1752 = _t1755
        end
        _t1749 = _t1752
    end
    result940 = _t1749
    record_span!(parser, span_start939, "Value")
    return result940
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start944 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int941 = consume_terminal!(parser, "INT")
    formatted_int_3942 = consume_terminal!(parser, "INT")
    formatted_int_4943 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1779 = Proto.DateValue(year=Int32(formatted_int941), month=Int32(formatted_int_3942), day=Int32(formatted_int_4943))
    result945 = _t1779
    record_span!(parser, span_start944, "DateValue")
    return result945
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start953 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int946 = consume_terminal!(parser, "INT")
    formatted_int_3947 = consume_terminal!(parser, "INT")
    formatted_int_4948 = consume_terminal!(parser, "INT")
    formatted_int_5949 = consume_terminal!(parser, "INT")
    formatted_int_6950 = consume_terminal!(parser, "INT")
    formatted_int_7951 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1780 = consume_terminal!(parser, "INT")
    else
        _t1780 = nothing
    end
    formatted_int_8952 = _t1780
    consume_literal!(parser, ")")
    _t1781 = Proto.DateTimeValue(year=Int32(formatted_int946), month=Int32(formatted_int_3947), day=Int32(formatted_int_4948), hour=Int32(formatted_int_5949), minute=Int32(formatted_int_6950), second=Int32(formatted_int_7951), microsecond=Int32((!isnothing(formatted_int_8952) ? formatted_int_8952 : 0)))
    result954 = _t1781
    record_span!(parser, span_start953, "DateTimeValue")
    return result954
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start959 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs955 = Proto.Formula[]
    cond956 = match_lookahead_literal(parser, "(", 0)
    while cond956
        _t1782 = parse_formula(parser)
        item957 = _t1782
        push!(xs955, item957)
        cond956 = match_lookahead_literal(parser, "(", 0)
    end
    formulas958 = xs955
    consume_literal!(parser, ")")
    _t1783 = Proto.Conjunction(args=formulas958)
    result960 = _t1783
    record_span!(parser, span_start959, "Conjunction")
    return result960
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start965 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs961 = Proto.Formula[]
    cond962 = match_lookahead_literal(parser, "(", 0)
    while cond962
        _t1784 = parse_formula(parser)
        item963 = _t1784
        push!(xs961, item963)
        cond962 = match_lookahead_literal(parser, "(", 0)
    end
    formulas964 = xs961
    consume_literal!(parser, ")")
    _t1785 = Proto.Disjunction(args=formulas964)
    result966 = _t1785
    record_span!(parser, span_start965, "Disjunction")
    return result966
end

function parse_not(parser::ParserState)::Proto.Not
    span_start968 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1786 = parse_formula(parser)
    formula967 = _t1786
    consume_literal!(parser, ")")
    _t1787 = Proto.Not(arg=formula967)
    result969 = _t1787
    record_span!(parser, span_start968, "Not")
    return result969
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start973 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1788 = parse_name(parser)
    name970 = _t1788
    _t1789 = parse_ffi_args(parser)
    ffi_args971 = _t1789
    _t1790 = parse_terms(parser)
    terms972 = _t1790
    consume_literal!(parser, ")")
    _t1791 = Proto.FFI(name=name970, args=ffi_args971, terms=terms972)
    result974 = _t1791
    record_span!(parser, span_start973, "FFI")
    return result974
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol975 = consume_terminal!(parser, "SYMBOL")
    return symbol975
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs976 = Proto.Abstraction[]
    cond977 = match_lookahead_literal(parser, "(", 0)
    while cond977
        _t1792 = parse_abstraction(parser)
        item978 = _t1792
        push!(xs976, item978)
        cond977 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions979 = xs976
    consume_literal!(parser, ")")
    return abstractions979
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start985 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1793 = parse_relation_id(parser)
    relation_id980 = _t1793
    xs981 = Proto.Term[]
    cond982 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond982
        _t1794 = parse_term(parser)
        item983 = _t1794
        push!(xs981, item983)
        cond982 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms984 = xs981
    consume_literal!(parser, ")")
    _t1795 = Proto.Atom(name=relation_id980, terms=terms984)
    result986 = _t1795
    record_span!(parser, span_start985, "Atom")
    return result986
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start992 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1796 = parse_name(parser)
    name987 = _t1796
    xs988 = Proto.Term[]
    cond989 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond989
        _t1797 = parse_term(parser)
        item990 = _t1797
        push!(xs988, item990)
        cond989 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms991 = xs988
    consume_literal!(parser, ")")
    _t1798 = Proto.Pragma(name=name987, terms=terms991)
    result993 = _t1798
    record_span!(parser, span_start992, "Pragma")
    return result993
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start1009 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1800 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1801 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1802 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1803 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1804 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1805 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1806 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1807 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1808 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1809 = 7
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
    else
        _t1799 = -1
    end
    prediction994 = _t1799
    if prediction994 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1811 = parse_name(parser)
        name1004 = _t1811
        xs1005 = Proto.RelTerm[]
        cond1006 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond1006
            _t1812 = parse_rel_term(parser)
            item1007 = _t1812
            push!(xs1005, item1007)
            cond1006 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms1008 = xs1005
        consume_literal!(parser, ")")
        _t1813 = Proto.Primitive(name=name1004, terms=rel_terms1008)
        _t1810 = _t1813
    else
        if prediction994 == 8
            _t1815 = parse_divide(parser)
            divide1003 = _t1815
            _t1814 = divide1003
        else
            if prediction994 == 7
                _t1817 = parse_multiply(parser)
                multiply1002 = _t1817
                _t1816 = multiply1002
            else
                if prediction994 == 6
                    _t1819 = parse_minus(parser)
                    minus1001 = _t1819
                    _t1818 = minus1001
                else
                    if prediction994 == 5
                        _t1821 = parse_add(parser)
                        add1000 = _t1821
                        _t1820 = add1000
                    else
                        if prediction994 == 4
                            _t1823 = parse_gt_eq(parser)
                            gt_eq999 = _t1823
                            _t1822 = gt_eq999
                        else
                            if prediction994 == 3
                                _t1825 = parse_gt(parser)
                                gt998 = _t1825
                                _t1824 = gt998
                            else
                                if prediction994 == 2
                                    _t1827 = parse_lt_eq(parser)
                                    lt_eq997 = _t1827
                                    _t1826 = lt_eq997
                                else
                                    if prediction994 == 1
                                        _t1829 = parse_lt(parser)
                                        lt996 = _t1829
                                        _t1828 = lt996
                                    else
                                        if prediction994 == 0
                                            _t1831 = parse_eq(parser)
                                            eq995 = _t1831
                                            _t1830 = eq995
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1828 = _t1830
                                    end
                                    _t1826 = _t1828
                                end
                                _t1824 = _t1826
                            end
                            _t1822 = _t1824
                        end
                        _t1820 = _t1822
                    end
                    _t1818 = _t1820
                end
                _t1816 = _t1818
            end
            _t1814 = _t1816
        end
        _t1810 = _t1814
    end
    result1010 = _t1810
    record_span!(parser, span_start1009, "Primitive")
    return result1010
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start1013 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1832 = parse_term(parser)
    term1011 = _t1832
    _t1833 = parse_term(parser)
    term_31012 = _t1833
    consume_literal!(parser, ")")
    _t1834 = Proto.RelTerm(rel_term_type=OneOf(:term, term1011))
    _t1835 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31012))
    _t1836 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1834, _t1835])
    result1014 = _t1836
    record_span!(parser, span_start1013, "Primitive")
    return result1014
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start1017 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1837 = parse_term(parser)
    term1015 = _t1837
    _t1838 = parse_term(parser)
    term_31016 = _t1838
    consume_literal!(parser, ")")
    _t1839 = Proto.RelTerm(rel_term_type=OneOf(:term, term1015))
    _t1840 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31016))
    _t1841 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1839, _t1840])
    result1018 = _t1841
    record_span!(parser, span_start1017, "Primitive")
    return result1018
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start1021 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1842 = parse_term(parser)
    term1019 = _t1842
    _t1843 = parse_term(parser)
    term_31020 = _t1843
    consume_literal!(parser, ")")
    _t1844 = Proto.RelTerm(rel_term_type=OneOf(:term, term1019))
    _t1845 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31020))
    _t1846 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1844, _t1845])
    result1022 = _t1846
    record_span!(parser, span_start1021, "Primitive")
    return result1022
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start1025 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1847 = parse_term(parser)
    term1023 = _t1847
    _t1848 = parse_term(parser)
    term_31024 = _t1848
    consume_literal!(parser, ")")
    _t1849 = Proto.RelTerm(rel_term_type=OneOf(:term, term1023))
    _t1850 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31024))
    _t1851 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1849, _t1850])
    result1026 = _t1851
    record_span!(parser, span_start1025, "Primitive")
    return result1026
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start1029 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1852 = parse_term(parser)
    term1027 = _t1852
    _t1853 = parse_term(parser)
    term_31028 = _t1853
    consume_literal!(parser, ")")
    _t1854 = Proto.RelTerm(rel_term_type=OneOf(:term, term1027))
    _t1855 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31028))
    _t1856 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1854, _t1855])
    result1030 = _t1856
    record_span!(parser, span_start1029, "Primitive")
    return result1030
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start1034 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1857 = parse_term(parser)
    term1031 = _t1857
    _t1858 = parse_term(parser)
    term_31032 = _t1858
    _t1859 = parse_term(parser)
    term_41033 = _t1859
    consume_literal!(parser, ")")
    _t1860 = Proto.RelTerm(rel_term_type=OneOf(:term, term1031))
    _t1861 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31032))
    _t1862 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41033))
    _t1863 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1860, _t1861, _t1862])
    result1035 = _t1863
    record_span!(parser, span_start1034, "Primitive")
    return result1035
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start1039 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1864 = parse_term(parser)
    term1036 = _t1864
    _t1865 = parse_term(parser)
    term_31037 = _t1865
    _t1866 = parse_term(parser)
    term_41038 = _t1866
    consume_literal!(parser, ")")
    _t1867 = Proto.RelTerm(rel_term_type=OneOf(:term, term1036))
    _t1868 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31037))
    _t1869 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41038))
    _t1870 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1867, _t1868, _t1869])
    result1040 = _t1870
    record_span!(parser, span_start1039, "Primitive")
    return result1040
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1044 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1871 = parse_term(parser)
    term1041 = _t1871
    _t1872 = parse_term(parser)
    term_31042 = _t1872
    _t1873 = parse_term(parser)
    term_41043 = _t1873
    consume_literal!(parser, ")")
    _t1874 = Proto.RelTerm(rel_term_type=OneOf(:term, term1041))
    _t1875 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31042))
    _t1876 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41043))
    _t1877 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1874, _t1875, _t1876])
    result1045 = _t1877
    record_span!(parser, span_start1044, "Primitive")
    return result1045
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1049 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1878 = parse_term(parser)
    term1046 = _t1878
    _t1879 = parse_term(parser)
    term_31047 = _t1879
    _t1880 = parse_term(parser)
    term_41048 = _t1880
    consume_literal!(parser, ")")
    _t1881 = Proto.RelTerm(rel_term_type=OneOf(:term, term1046))
    _t1882 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31047))
    _t1883 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41048))
    _t1884 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1881, _t1882, _t1883])
    result1050 = _t1884
    record_span!(parser, span_start1049, "Primitive")
    return result1050
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1054 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1885 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1886 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1887 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1888 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1889 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1890 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1891 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1892 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1893 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1894 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1895 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1896 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1897 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1898 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1899 = 1
                                                            else
                                                                _t1899 = -1
                                                            end
                                                            _t1898 = _t1899
                                                        end
                                                        _t1897 = _t1898
                                                    end
                                                    _t1896 = _t1897
                                                end
                                                _t1895 = _t1896
                                            end
                                            _t1894 = _t1895
                                        end
                                        _t1893 = _t1894
                                    end
                                    _t1892 = _t1893
                                end
                                _t1891 = _t1892
                            end
                            _t1890 = _t1891
                        end
                        _t1889 = _t1890
                    end
                    _t1888 = _t1889
                end
                _t1887 = _t1888
            end
            _t1886 = _t1887
        end
        _t1885 = _t1886
    end
    prediction1051 = _t1885
    if prediction1051 == 1
        _t1901 = parse_term(parser)
        term1053 = _t1901
        _t1902 = Proto.RelTerm(rel_term_type=OneOf(:term, term1053))
        _t1900 = _t1902
    else
        if prediction1051 == 0
            _t1904 = parse_specialized_value(parser)
            specialized_value1052 = _t1904
            _t1905 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1052))
            _t1903 = _t1905
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1900 = _t1903
    end
    result1055 = _t1900
    record_span!(parser, span_start1054, "RelTerm")
    return result1055
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1057 = span_start(parser)
    consume_literal!(parser, "#")
    _t1906 = parse_raw_value(parser)
    raw_value1056 = _t1906
    result1058 = raw_value1056
    record_span!(parser, span_start1057, "Value")
    return result1058
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1064 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1907 = parse_name(parser)
    name1059 = _t1907
    xs1060 = Proto.RelTerm[]
    cond1061 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1061
        _t1908 = parse_rel_term(parser)
        item1062 = _t1908
        push!(xs1060, item1062)
        cond1061 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1063 = xs1060
    consume_literal!(parser, ")")
    _t1909 = Proto.RelAtom(name=name1059, terms=rel_terms1063)
    result1065 = _t1909
    record_span!(parser, span_start1064, "RelAtom")
    return result1065
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1068 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1910 = parse_term(parser)
    term1066 = _t1910
    _t1911 = parse_term(parser)
    term_31067 = _t1911
    consume_literal!(parser, ")")
    _t1912 = Proto.Cast(input=term1066, result=term_31067)
    result1069 = _t1912
    record_span!(parser, span_start1068, "Cast")
    return result1069
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1070 = Proto.Attribute[]
    cond1071 = match_lookahead_literal(parser, "(", 0)
    while cond1071
        _t1913 = parse_attribute(parser)
        item1072 = _t1913
        push!(xs1070, item1072)
        cond1071 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1073 = xs1070
    consume_literal!(parser, ")")
    return attributes1073
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1079 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1914 = parse_name(parser)
    name1074 = _t1914
    xs1075 = Proto.Value[]
    cond1076 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1076
        _t1915 = parse_raw_value(parser)
        item1077 = _t1915
        push!(xs1075, item1077)
        cond1076 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1078 = xs1075
    consume_literal!(parser, ")")
    _t1916 = Proto.Attribute(name=name1074, args=raw_values1078)
    result1080 = _t1916
    record_span!(parser, span_start1079, "Attribute")
    return result1080
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1087 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1081 = Proto.RelationId[]
    cond1082 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1082
        _t1917 = parse_relation_id(parser)
        item1083 = _t1917
        push!(xs1081, item1083)
        cond1082 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1084 = xs1081
    _t1918 = parse_script(parser)
    script1085 = _t1918
    if match_lookahead_literal(parser, "(", 0)
        _t1920 = parse_attrs(parser)
        _t1919 = _t1920
    else
        _t1919 = nothing
    end
    attrs1086 = _t1919
    consume_literal!(parser, ")")
    _t1921 = Proto.Algorithm(var"#global"=relation_ids1084, body=script1085, attrs=(!isnothing(attrs1086) ? attrs1086 : Proto.Attribute[]))
    result1088 = _t1921
    record_span!(parser, span_start1087, "Algorithm")
    return result1088
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1093 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1089 = Proto.Construct[]
    cond1090 = match_lookahead_literal(parser, "(", 0)
    while cond1090
        _t1922 = parse_construct(parser)
        item1091 = _t1922
        push!(xs1089, item1091)
        cond1090 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1092 = xs1089
    consume_literal!(parser, ")")
    _t1923 = Proto.Script(constructs=constructs1092)
    result1094 = _t1923
    record_span!(parser, span_start1093, "Script")
    return result1094
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1098 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1925 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1926 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1927 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1928 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1929 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1930 = 1
                            else
                                _t1930 = -1
                            end
                            _t1929 = _t1930
                        end
                        _t1928 = _t1929
                    end
                    _t1927 = _t1928
                end
                _t1926 = _t1927
            end
            _t1925 = _t1926
        end
        _t1924 = _t1925
    else
        _t1924 = -1
    end
    prediction1095 = _t1924
    if prediction1095 == 1
        _t1932 = parse_instruction(parser)
        instruction1097 = _t1932
        _t1933 = Proto.Construct(construct_type=OneOf(:instruction, instruction1097))
        _t1931 = _t1933
    else
        if prediction1095 == 0
            _t1935 = parse_loop(parser)
            loop1096 = _t1935
            _t1936 = Proto.Construct(construct_type=OneOf(:loop, loop1096))
            _t1934 = _t1936
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1931 = _t1934
    end
    result1099 = _t1931
    record_span!(parser, span_start1098, "Construct")
    return result1099
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1103 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1937 = parse_init(parser)
    init1100 = _t1937
    _t1938 = parse_script(parser)
    script1101 = _t1938
    if match_lookahead_literal(parser, "(", 0)
        _t1940 = parse_attrs(parser)
        _t1939 = _t1940
    else
        _t1939 = nothing
    end
    attrs1102 = _t1939
    consume_literal!(parser, ")")
    _t1941 = Proto.Loop(init=init1100, body=script1101, attrs=(!isnothing(attrs1102) ? attrs1102 : Proto.Attribute[]))
    result1104 = _t1941
    record_span!(parser, span_start1103, "Loop")
    return result1104
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1105 = Proto.Instruction[]
    cond1106 = match_lookahead_literal(parser, "(", 0)
    while cond1106
        _t1942 = parse_instruction(parser)
        item1107 = _t1942
        push!(xs1105, item1107)
        cond1106 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1108 = xs1105
    consume_literal!(parser, ")")
    return instructions1108
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1115 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1944 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1945 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1946 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1947 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1948 = 0
                        else
                            _t1948 = -1
                        end
                        _t1947 = _t1948
                    end
                    _t1946 = _t1947
                end
                _t1945 = _t1946
            end
            _t1944 = _t1945
        end
        _t1943 = _t1944
    else
        _t1943 = -1
    end
    prediction1109 = _t1943
    if prediction1109 == 4
        _t1950 = parse_monus_def(parser)
        monus_def1114 = _t1950
        _t1951 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1114))
        _t1949 = _t1951
    else
        if prediction1109 == 3
            _t1953 = parse_monoid_def(parser)
            monoid_def1113 = _t1953
            _t1954 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1113))
            _t1952 = _t1954
        else
            if prediction1109 == 2
                _t1956 = parse_break(parser)
                break1112 = _t1956
                _t1957 = Proto.Instruction(instr_type=OneOf(:var"#break", break1112))
                _t1955 = _t1957
            else
                if prediction1109 == 1
                    _t1959 = parse_upsert(parser)
                    upsert1111 = _t1959
                    _t1960 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1111))
                    _t1958 = _t1960
                else
                    if prediction1109 == 0
                        _t1962 = parse_assign(parser)
                        assign1110 = _t1962
                        _t1963 = Proto.Instruction(instr_type=OneOf(:assign, assign1110))
                        _t1961 = _t1963
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1958 = _t1961
                end
                _t1955 = _t1958
            end
            _t1952 = _t1955
        end
        _t1949 = _t1952
    end
    result1116 = _t1949
    record_span!(parser, span_start1115, "Instruction")
    return result1116
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1120 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1964 = parse_relation_id(parser)
    relation_id1117 = _t1964
    _t1965 = parse_abstraction(parser)
    abstraction1118 = _t1965
    if match_lookahead_literal(parser, "(", 0)
        _t1967 = parse_attrs(parser)
        _t1966 = _t1967
    else
        _t1966 = nothing
    end
    attrs1119 = _t1966
    consume_literal!(parser, ")")
    _t1968 = Proto.Assign(name=relation_id1117, body=abstraction1118, attrs=(!isnothing(attrs1119) ? attrs1119 : Proto.Attribute[]))
    result1121 = _t1968
    record_span!(parser, span_start1120, "Assign")
    return result1121
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1125 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1969 = parse_relation_id(parser)
    relation_id1122 = _t1969
    _t1970 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1123 = _t1970
    if match_lookahead_literal(parser, "(", 0)
        _t1972 = parse_attrs(parser)
        _t1971 = _t1972
    else
        _t1971 = nothing
    end
    attrs1124 = _t1971
    consume_literal!(parser, ")")
    _t1973 = Proto.Upsert(name=relation_id1122, body=abstraction_with_arity1123[1], attrs=(!isnothing(attrs1124) ? attrs1124 : Proto.Attribute[]), value_arity=abstraction_with_arity1123[2])
    result1126 = _t1973
    record_span!(parser, span_start1125, "Upsert")
    return result1126
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1974 = parse_bindings(parser)
    bindings1127 = _t1974
    _t1975 = parse_formula(parser)
    formula1128 = _t1975
    consume_literal!(parser, ")")
    _t1976 = Proto.Abstraction(vars=vcat(bindings1127[1], !isnothing(bindings1127[2]) ? bindings1127[2] : []), value=formula1128)
    return (_t1976, length(bindings1127[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1132 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1977 = parse_relation_id(parser)
    relation_id1129 = _t1977
    _t1978 = parse_abstraction(parser)
    abstraction1130 = _t1978
    if match_lookahead_literal(parser, "(", 0)
        _t1980 = parse_attrs(parser)
        _t1979 = _t1980
    else
        _t1979 = nothing
    end
    attrs1131 = _t1979
    consume_literal!(parser, ")")
    _t1981 = Proto.Break(name=relation_id1129, body=abstraction1130, attrs=(!isnothing(attrs1131) ? attrs1131 : Proto.Attribute[]))
    result1133 = _t1981
    record_span!(parser, span_start1132, "Break")
    return result1133
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1138 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1982 = parse_monoid(parser)
    monoid1134 = _t1982
    _t1983 = parse_relation_id(parser)
    relation_id1135 = _t1983
    _t1984 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1136 = _t1984
    if match_lookahead_literal(parser, "(", 0)
        _t1986 = parse_attrs(parser)
        _t1985 = _t1986
    else
        _t1985 = nothing
    end
    attrs1137 = _t1985
    consume_literal!(parser, ")")
    _t1987 = Proto.MonoidDef(monoid=monoid1134, name=relation_id1135, body=abstraction_with_arity1136[1], attrs=(!isnothing(attrs1137) ? attrs1137 : Proto.Attribute[]), value_arity=abstraction_with_arity1136[2])
    result1139 = _t1987
    record_span!(parser, span_start1138, "MonoidDef")
    return result1139
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1145 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1989 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1990 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1991 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1992 = 2
                    else
                        _t1992 = -1
                    end
                    _t1991 = _t1992
                end
                _t1990 = _t1991
            end
            _t1989 = _t1990
        end
        _t1988 = _t1989
    else
        _t1988 = -1
    end
    prediction1140 = _t1988
    if prediction1140 == 3
        _t1994 = parse_sum_monoid(parser)
        sum_monoid1144 = _t1994
        _t1995 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1144))
        _t1993 = _t1995
    else
        if prediction1140 == 2
            _t1997 = parse_max_monoid(parser)
            max_monoid1143 = _t1997
            _t1998 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1143))
            _t1996 = _t1998
        else
            if prediction1140 == 1
                _t2000 = parse_min_monoid(parser)
                min_monoid1142 = _t2000
                _t2001 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1142))
                _t1999 = _t2001
            else
                if prediction1140 == 0
                    _t2003 = parse_or_monoid(parser)
                    or_monoid1141 = _t2003
                    _t2004 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1141))
                    _t2002 = _t2004
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1999 = _t2002
            end
            _t1996 = _t1999
        end
        _t1993 = _t1996
    end
    result1146 = _t1993
    record_span!(parser, span_start1145, "Monoid")
    return result1146
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1147 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t2005 = Proto.OrMonoid()
    result1148 = _t2005
    record_span!(parser, span_start1147, "OrMonoid")
    return result1148
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1150 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t2006 = parse_type(parser)
    type1149 = _t2006
    consume_literal!(parser, ")")
    _t2007 = Proto.MinMonoid(var"#type"=type1149)
    result1151 = _t2007
    record_span!(parser, span_start1150, "MinMonoid")
    return result1151
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1153 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t2008 = parse_type(parser)
    type1152 = _t2008
    consume_literal!(parser, ")")
    _t2009 = Proto.MaxMonoid(var"#type"=type1152)
    result1154 = _t2009
    record_span!(parser, span_start1153, "MaxMonoid")
    return result1154
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1156 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t2010 = parse_type(parser)
    type1155 = _t2010
    consume_literal!(parser, ")")
    _t2011 = Proto.SumMonoid(var"#type"=type1155)
    result1157 = _t2011
    record_span!(parser, span_start1156, "SumMonoid")
    return result1157
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1162 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t2012 = parse_monoid(parser)
    monoid1158 = _t2012
    _t2013 = parse_relation_id(parser)
    relation_id1159 = _t2013
    _t2014 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1160 = _t2014
    if match_lookahead_literal(parser, "(", 0)
        _t2016 = parse_attrs(parser)
        _t2015 = _t2016
    else
        _t2015 = nothing
    end
    attrs1161 = _t2015
    consume_literal!(parser, ")")
    _t2017 = Proto.MonusDef(monoid=monoid1158, name=relation_id1159, body=abstraction_with_arity1160[1], attrs=(!isnothing(attrs1161) ? attrs1161 : Proto.Attribute[]), value_arity=abstraction_with_arity1160[2])
    result1163 = _t2017
    record_span!(parser, span_start1162, "MonusDef")
    return result1163
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1168 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t2018 = parse_relation_id(parser)
    relation_id1164 = _t2018
    _t2019 = parse_abstraction(parser)
    abstraction1165 = _t2019
    _t2020 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1166 = _t2020
    _t2021 = parse_functional_dependency_values(parser)
    functional_dependency_values1167 = _t2021
    consume_literal!(parser, ")")
    _t2022 = Proto.FunctionalDependency(guard=abstraction1165, keys=functional_dependency_keys1166, values=functional_dependency_values1167)
    _t2023 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t2022), name=relation_id1164)
    result1169 = _t2023
    record_span!(parser, span_start1168, "Constraint")
    return result1169
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1170 = Proto.Var[]
    cond1171 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1171
        _t2024 = parse_var(parser)
        item1172 = _t2024
        push!(xs1170, item1172)
        cond1171 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1173 = xs1170
    consume_literal!(parser, ")")
    return vars1173
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1174 = Proto.Var[]
    cond1175 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1175
        _t2025 = parse_var(parser)
        item1176 = _t2025
        push!(xs1174, item1176)
        cond1175 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1177 = xs1174
    consume_literal!(parser, ")")
    return vars1177
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1183 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t2027 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t2028 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t2029 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t2030 = 1
                    else
                        _t2030 = -1
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
    prediction1178 = _t2026
    if prediction1178 == 3
        _t2032 = parse_iceberg_data(parser)
        iceberg_data1182 = _t2032
        _t2033 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1182))
        _t2031 = _t2033
    else
        if prediction1178 == 2
            _t2035 = parse_csv_data(parser)
            csv_data1181 = _t2035
            _t2036 = Proto.Data(data_type=OneOf(:csv_data, csv_data1181))
            _t2034 = _t2036
        else
            if prediction1178 == 1
                _t2038 = parse_betree_relation(parser)
                betree_relation1180 = _t2038
                _t2039 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1180))
                _t2037 = _t2039
            else
                if prediction1178 == 0
                    _t2041 = parse_edb(parser)
                    edb1179 = _t2041
                    _t2042 = Proto.Data(data_type=OneOf(:edb, edb1179))
                    _t2040 = _t2042
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t2037 = _t2040
            end
            _t2034 = _t2037
        end
        _t2031 = _t2034
    end
    result1184 = _t2031
    record_span!(parser, span_start1183, "Data")
    return result1184
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1188 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t2043 = parse_relation_id(parser)
    relation_id1185 = _t2043
    _t2044 = parse_edb_path(parser)
    edb_path1186 = _t2044
    _t2045 = parse_edb_types(parser)
    edb_types1187 = _t2045
    consume_literal!(parser, ")")
    _t2046 = Proto.EDB(target_id=relation_id1185, path=edb_path1186, types=edb_types1187)
    result1189 = _t2046
    record_span!(parser, span_start1188, "EDB")
    return result1189
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1190 = String[]
    cond1191 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1191
        item1192 = consume_terminal!(parser, "STRING")
        push!(xs1190, item1192)
        cond1191 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1193 = xs1190
    consume_literal!(parser, "]")
    return strings1193
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1194 = Proto.var"#Type"[]
    cond1195 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1195
        _t2047 = parse_type(parser)
        item1196 = _t2047
        push!(xs1194, item1196)
        cond1195 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1197 = xs1194
    consume_literal!(parser, "]")
    return types1197
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1200 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t2048 = parse_relation_id(parser)
    relation_id1198 = _t2048
    _t2049 = parse_betree_info(parser)
    betree_info1199 = _t2049
    consume_literal!(parser, ")")
    _t2050 = Proto.BeTreeRelation(name=relation_id1198, relation_info=betree_info1199)
    result1201 = _t2050
    record_span!(parser, span_start1200, "BeTreeRelation")
    return result1201
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1205 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t2051 = parse_betree_info_key_types(parser)
    betree_info_key_types1202 = _t2051
    _t2052 = parse_betree_info_value_types(parser)
    betree_info_value_types1203 = _t2052
    _t2053 = parse_config_dict(parser)
    config_dict1204 = _t2053
    consume_literal!(parser, ")")
    _t2054 = construct_betree_info(parser, betree_info_key_types1202, betree_info_value_types1203, config_dict1204)
    result1206 = _t2054
    record_span!(parser, span_start1205, "BeTreeInfo")
    return result1206
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1207 = Proto.var"#Type"[]
    cond1208 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1208
        _t2055 = parse_type(parser)
        item1209 = _t2055
        push!(xs1207, item1209)
        cond1208 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1210 = xs1207
    consume_literal!(parser, ")")
    return types1210
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1211 = Proto.var"#Type"[]
    cond1212 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1212
        _t2056 = parse_type(parser)
        item1213 = _t2056
        push!(xs1211, item1213)
        cond1212 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1214 = xs1211
    consume_literal!(parser, ")")
    return types1214
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1220 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t2057 = parse_csvlocator(parser)
    csvlocator1215 = _t2057
    _t2058 = parse_csv_config(parser)
    csv_config1216 = _t2058
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t2060 = parse_gnf_columns(parser)
        _t2059 = _t2060
    else
        _t2059 = nothing
    end
    gnf_columns1217 = _t2059
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relations", 1))
        _t2062 = parse_target_relations(parser)
        _t2061 = _t2062
    else
        _t2061 = nothing
    end
    target_relations1218 = _t2061
    _t2063 = parse_csv_asof(parser)
    csv_asof1219 = _t2063
    consume_literal!(parser, ")")
    _t2064 = construct_csv_data(parser, csvlocator1215, csv_config1216, gnf_columns1217, target_relations1218, csv_asof1219)
    result1221 = _t2064
    record_span!(parser, span_start1220, "CSVData")
    return result1221
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1224 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t2066 = parse_csv_locator_paths(parser)
        _t2065 = _t2066
    else
        _t2065 = nothing
    end
    csv_locator_paths1222 = _t2065
    if match_lookahead_literal(parser, "(", 0)
        _t2068 = parse_csv_locator_inline_data(parser)
        _t2067 = _t2068
    else
        _t2067 = nothing
    end
    csv_locator_inline_data1223 = _t2067
    consume_literal!(parser, ")")
    _t2069 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1222) ? csv_locator_paths1222 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1223) ? csv_locator_inline_data1223 : "")))
    result1225 = _t2069
    record_span!(parser, span_start1224, "CSVLocator")
    return result1225
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1226 = String[]
    cond1227 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1227
        item1228 = consume_terminal!(parser, "STRING")
        push!(xs1226, item1228)
        cond1227 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1229 = xs1226
    consume_literal!(parser, ")")
    return strings1229
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1230 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1230
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1233 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t2070 = parse_config_dict(parser)
    config_dict1231 = _t2070
    if match_lookahead_literal(parser, "(", 0)
        _t2072 = parse__storage_integration(parser)
        _t2071 = _t2072
    else
        _t2071 = nothing
    end
    _storage_integration1232 = _t2071
    consume_literal!(parser, ")")
    _t2073 = construct_csv_config(parser, config_dict1231, _storage_integration1232)
    result1234 = _t2073
    record_span!(parser, span_start1233, "CSVConfig")
    return result1234
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t2074 = parse_config_dict(parser)
    config_dict1235 = _t2074
    consume_literal!(parser, ")")
    return config_dict1235
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1236 = Proto.GNFColumn[]
    cond1237 = match_lookahead_literal(parser, "(", 0)
    while cond1237
        _t2075 = parse_gnf_column(parser)
        item1238 = _t2075
        push!(xs1236, item1238)
        cond1237 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1239 = xs1236
    consume_literal!(parser, ")")
    return gnf_columns1239
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1246 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t2076 = parse_gnf_column_path(parser)
    gnf_column_path1240 = _t2076
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t2078 = parse_relation_id(parser)
        _t2077 = _t2078
    else
        _t2077 = nothing
    end
    relation_id1241 = _t2077
    consume_literal!(parser, "[")
    xs1242 = Proto.var"#Type"[]
    cond1243 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1243
        _t2079 = parse_type(parser)
        item1244 = _t2079
        push!(xs1242, item1244)
        cond1243 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1245 = xs1242
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2080 = Proto.GNFColumn(column_path=gnf_column_path1240, target_id=relation_id1241, types=types1245)
    result1247 = _t2080
    record_span!(parser, span_start1246, "GNFColumn")
    return result1247
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t2081 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t2082 = 0
        else
            _t2082 = -1
        end
        _t2081 = _t2082
    end
    prediction1248 = _t2081
    if prediction1248 == 1
        consume_literal!(parser, "[")
        xs1250 = String[]
        cond1251 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1251
            item1252 = consume_terminal!(parser, "STRING")
            push!(xs1250, item1252)
            cond1251 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1253 = xs1250
        consume_literal!(parser, "]")
        _t2083 = strings1253
    else
        if prediction1248 == 0
            string1249 = consume_terminal!(parser, "STRING")
            _t2084 = String[string1249]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t2083 = _t2084
    end
    return _t2083
end

function parse_target_relations(parser::ParserState)::Proto.TargetRelations
    span_start1257 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relations")
    _t2085 = parse_relation_keys(parser)
    relation_keys1254 = _t2085
    _t2086 = parse_relation_body(parser)
    relation_body1255 = _t2086
    if match_lookahead_literal(parser, "(", 0)
        _t2088 = parse_load_errors(parser)
        _t2087 = _t2088
    else
        _t2087 = nothing
    end
    load_errors1256 = _t2087
    consume_literal!(parser, ")")
    _t2089 = construct_relations(parser, relation_keys1254, relation_body1255, load_errors1256)
    result1258 = _t2089
    record_span!(parser, span_start1257, "TargetRelations")
    return result1258
end

function parse_relation_keys(parser::ParserState)::Tuple{Vector{Proto.NamedColumn}, Bool}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "keys", 1)
            if match_lookahead_literal(parser, "synthetic", 2)
                _t2092 = 1
            else
                if match_lookahead_literal(parser, ")", 2)
                    _t2093 = 0
                else
                    if match_lookahead_literal(parser, "(", 2)
                        _t2094 = 0
                    else
                        _t2094 = -1
                    end
                    _t2093 = _t2094
                end
                _t2092 = _t2093
            end
            _t2091 = _t2092
        else
            _t2091 = -1
        end
        _t2090 = _t2091
    else
        _t2090 = -1
    end
    prediction1259 = _t2090
    if prediction1259 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "keys")
        consume_literal!(parser, "synthetic")
        consume_literal!(parser, ")")
        _t2095 = (Proto.NamedColumn[], true,)
    else
        if prediction1259 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "keys")
            xs1260 = Proto.NamedColumn[]
            cond1261 = match_lookahead_literal(parser, "(", 0)
            while cond1261
                _t2097 = parse_named_column(parser)
                item1262 = _t2097
                push!(xs1260, item1262)
                cond1261 = match_lookahead_literal(parser, "(", 0)
            end
            named_columns1263 = xs1260
            consume_literal!(parser, ")")
            _t2096 = (named_columns1263, false,)
        else
            throw(ParseError("Unexpected token in relation_keys" * ": " * string(lookahead(parser, 0))))
        end
        _t2095 = _t2096
    end
    return _t2095
end

function parse_named_column(parser::ParserState)::Proto.NamedColumn
    span_start1266 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1264 = consume_terminal!(parser, "STRING")
    _t2098 = parse_type(parser)
    type1265 = _t2098
    consume_literal!(parser, ")")
    _t2099 = Proto.NamedColumn(name=string1264, var"#type"=type1265)
    result1267 = _t2099
    record_span!(parser, span_start1266, "NamedColumn")
    return result1267
end

function parse_relation_body(parser::ParserState)::Proto.TargetRelations
    span_start1272 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "relation", 1)
            _t2101 = 0
        else
            if match_lookahead_literal(parser, "inserts", 1)
                _t2102 = 1
            else
                _t2102 = 0
            end
            _t2101 = _t2102
        end
        _t2100 = _t2101
    else
        _t2100 = 0
    end
    prediction1268 = _t2100
    if prediction1268 == 1
        _t2104 = parse_cdc_inserts(parser)
        cdc_inserts1270 = _t2104
        _t2105 = parse_cdc_deletes(parser)
        cdc_deletes1271 = _t2105
        _t2106 = construct_cdc_relations(parser, cdc_inserts1270, cdc_deletes1271)
        _t2103 = _t2106
    else
        if prediction1268 == 0
            _t2108 = parse_non_cdc_relations(parser)
            non_cdc_relations1269 = _t2108
            _t2109 = construct_non_cdc_relations(parser, non_cdc_relations1269)
            _t2107 = _t2109
        else
            throw(ParseError("Unexpected token in relation_body" * ": " * string(lookahead(parser, 0))))
        end
        _t2103 = _t2107
    end
    result1273 = _t2103
    record_span!(parser, span_start1272, "TargetRelations")
    return result1273
end

function parse_non_cdc_relations(parser::ParserState)::Vector{Proto.TargetRelation}
    xs1274 = Proto.TargetRelation[]
    cond1275 = (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relation", 1))
    while cond1275
        _t2110 = parse_target_relation(parser)
        item1276 = _t2110
        push!(xs1274, item1276)
        cond1275 = (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relation", 1))
    end
    return xs1274
end

function parse_target_relation(parser::ParserState)::Proto.TargetRelation
    span_start1282 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relation")
    _t2111 = parse_relation_id(parser)
    relation_id1277 = _t2111
    xs1278 = Proto.NamedColumn[]
    cond1279 = match_lookahead_literal(parser, "(", 0)
    while cond1279
        _t2112 = parse_named_column(parser)
        item1280 = _t2112
        push!(xs1278, item1280)
        cond1279 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1281 = xs1278
    consume_literal!(parser, ")")
    _t2113 = Proto.TargetRelation(target_id=relation_id1277, values=named_columns1281)
    result1283 = _t2113
    record_span!(parser, span_start1282, "TargetRelation")
    return result1283
end

function parse_cdc_inserts(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "inserts")
    xs1284 = Proto.TargetRelation[]
    cond1285 = match_lookahead_literal(parser, "(", 0)
    while cond1285
        _t2114 = parse_target_relation(parser)
        item1286 = _t2114
        push!(xs1284, item1286)
        cond1285 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1287 = xs1284
    consume_literal!(parser, ")")
    return target_relations1287
end

function parse_cdc_deletes(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "deletes")
    xs1288 = Proto.TargetRelation[]
    cond1289 = match_lookahead_literal(parser, "(", 0)
    while cond1289
        _t2115 = parse_target_relation(parser)
        item1290 = _t2115
        push!(xs1288, item1290)
        cond1289 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1291 = xs1288
    consume_literal!(parser, ")")
    return target_relations1291
end

function parse_load_errors(parser::ParserState)::Proto.RelationId
    span_start1293 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "load_errors")
    _t2116 = parse_relation_id(parser)
    relation_id1292 = _t2116
    consume_literal!(parser, ")")
    result1294 = relation_id1292
    record_span!(parser, span_start1293, "RelationId")
    return result1294
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1295 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1295
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1302 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t2117 = parse_iceberg_locator(parser)
    iceberg_locator1296 = _t2117
    _t2118 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1297 = _t2118
    _t2119 = parse_gnf_columns(parser)
    gnf_columns1298 = _t2119
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2121 = parse_iceberg_from_snapshot(parser)
        _t2120 = _t2121
    else
        _t2120 = nothing
    end
    iceberg_from_snapshot1299 = _t2120
    if match_lookahead_literal(parser, "(", 0)
        _t2123 = parse_iceberg_to_snapshot(parser)
        _t2122 = _t2123
    else
        _t2122 = nothing
    end
    iceberg_to_snapshot1300 = _t2122
    _t2124 = parse_boolean_value(parser)
    boolean_value1301 = _t2124
    consume_literal!(parser, ")")
    _t2125 = construct_iceberg_data(parser, iceberg_locator1296, iceberg_catalog_config1297, gnf_columns1298, iceberg_from_snapshot1299, iceberg_to_snapshot1300, boolean_value1301)
    result1303 = _t2125
    record_span!(parser, span_start1302, "IcebergData")
    return result1303
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1307 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2126 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1304 = _t2126
    _t2127 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1305 = _t2127
    _t2128 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1306 = _t2128
    consume_literal!(parser, ")")
    _t2129 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1304, namespace=iceberg_locator_namespace1305, warehouse=iceberg_locator_warehouse1306)
    result1308 = _t2129
    record_span!(parser, span_start1307, "IcebergLocator")
    return result1308
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1309 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1309
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1310 = String[]
    cond1311 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1311
        item1312 = consume_terminal!(parser, "STRING")
        push!(xs1310, item1312)
        cond1311 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1313 = xs1310
    consume_literal!(parser, ")")
    return strings1313
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1314 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1314
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1319 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2130 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1315 = _t2130
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2132 = parse_iceberg_catalog_config_scope(parser)
        _t2131 = _t2132
    else
        _t2131 = nothing
    end
    iceberg_catalog_config_scope1316 = _t2131
    _t2133 = parse_iceberg_properties(parser)
    iceberg_properties1317 = _t2133
    _t2134 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1318 = _t2134
    consume_literal!(parser, ")")
    _t2135 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1315, iceberg_catalog_config_scope1316, iceberg_properties1317, iceberg_auth_properties1318)
    result1320 = _t2135
    record_span!(parser, span_start1319, "IcebergCatalogConfig")
    return result1320
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1321 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1321
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1322 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1322
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1323 = Tuple{String, String}[]
    cond1324 = match_lookahead_literal(parser, "(", 0)
    while cond1324
        _t2136 = parse_iceberg_property_entry(parser)
        item1325 = _t2136
        push!(xs1323, item1325)
        cond1324 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1326 = xs1323
    consume_literal!(parser, ")")
    return iceberg_property_entrys1326
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1327 = consume_terminal!(parser, "STRING")
    string_31328 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1327, string_31328,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1329 = Tuple{String, String}[]
    cond1330 = match_lookahead_literal(parser, "(", 0)
    while cond1330
        _t2137 = parse_iceberg_masked_property_entry(parser)
        item1331 = _t2137
        push!(xs1329, item1331)
        cond1330 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1332 = xs1329
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1332
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1333 = consume_terminal!(parser, "STRING")
    string_31334 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1333, string_31334,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1335 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1335
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1336 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1336
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1338 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2138 = parse_fragment_id(parser)
    fragment_id1337 = _t2138
    consume_literal!(parser, ")")
    _t2139 = Proto.Undefine(fragment_id=fragment_id1337)
    result1339 = _t2139
    record_span!(parser, span_start1338, "Undefine")
    return result1339
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1344 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1340 = Proto.RelationId[]
    cond1341 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1341
        _t2140 = parse_relation_id(parser)
        item1342 = _t2140
        push!(xs1340, item1342)
        cond1341 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1343 = xs1340
    consume_literal!(parser, ")")
    _t2141 = Proto.Context(relations=relation_ids1343)
    result1345 = _t2141
    record_span!(parser, span_start1344, "Context")
    return result1345
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1351 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2142 = parse_edb_path(parser)
    edb_path1346 = _t2142
    xs1347 = Proto.SnapshotMapping[]
    cond1348 = match_lookahead_literal(parser, "[", 0)
    while cond1348
        _t2143 = parse_snapshot_mapping(parser)
        item1349 = _t2143
        push!(xs1347, item1349)
        cond1348 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1350 = xs1347
    consume_literal!(parser, ")")
    _t2144 = Proto.Snapshot(mappings=snapshot_mappings1350, prefix=edb_path1346)
    result1352 = _t2144
    record_span!(parser, span_start1351, "Snapshot")
    return result1352
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1355 = span_start(parser)
    _t2145 = parse_edb_path(parser)
    edb_path1353 = _t2145
    _t2146 = parse_relation_id(parser)
    relation_id1354 = _t2146
    _t2147 = Proto.SnapshotMapping(destination_path=edb_path1353, source_relation=relation_id1354)
    result1356 = _t2147
    record_span!(parser, span_start1355, "SnapshotMapping")
    return result1356
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1357 = Proto.Read[]
    cond1358 = match_lookahead_literal(parser, "(", 0)
    while cond1358
        _t2148 = parse_read(parser)
        item1359 = _t2148
        push!(xs1357, item1359)
        cond1358 = match_lookahead_literal(parser, "(", 0)
    end
    reads1360 = xs1357
    consume_literal!(parser, ")")
    return reads1360
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1367 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2150 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2151 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2152 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2153 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2154 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2155 = 3
                            else
                                _t2155 = -1
                            end
                            _t2154 = _t2155
                        end
                        _t2153 = _t2154
                    end
                    _t2152 = _t2153
                end
                _t2151 = _t2152
            end
            _t2150 = _t2151
        end
        _t2149 = _t2150
    else
        _t2149 = -1
    end
    prediction1361 = _t2149
    if prediction1361 == 4
        _t2157 = parse_export(parser)
        export1366 = _t2157
        _t2158 = Proto.Read(read_type=OneOf(:var"#export", export1366))
        _t2156 = _t2158
    else
        if prediction1361 == 3
            _t2160 = parse_abort(parser)
            abort1365 = _t2160
            _t2161 = Proto.Read(read_type=OneOf(:abort, abort1365))
            _t2159 = _t2161
        else
            if prediction1361 == 2
                _t2163 = parse_what_if(parser)
                what_if1364 = _t2163
                _t2164 = Proto.Read(read_type=OneOf(:what_if, what_if1364))
                _t2162 = _t2164
            else
                if prediction1361 == 1
                    _t2166 = parse_output(parser)
                    output1363 = _t2166
                    _t2167 = Proto.Read(read_type=OneOf(:output, output1363))
                    _t2165 = _t2167
                else
                    if prediction1361 == 0
                        _t2169 = parse_demand(parser)
                        demand1362 = _t2169
                        _t2170 = Proto.Read(read_type=OneOf(:demand, demand1362))
                        _t2168 = _t2170
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2165 = _t2168
                end
                _t2162 = _t2165
            end
            _t2159 = _t2162
        end
        _t2156 = _t2159
    end
    result1368 = _t2156
    record_span!(parser, span_start1367, "Read")
    return result1368
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1370 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2171 = parse_relation_id(parser)
    relation_id1369 = _t2171
    consume_literal!(parser, ")")
    _t2172 = Proto.Demand(relation_id=relation_id1369)
    result1371 = _t2172
    record_span!(parser, span_start1370, "Demand")
    return result1371
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1374 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2173 = parse_name(parser)
    name1372 = _t2173
    _t2174 = parse_relation_id(parser)
    relation_id1373 = _t2174
    consume_literal!(parser, ")")
    _t2175 = Proto.Output(name=name1372, relation_id=relation_id1373)
    result1375 = _t2175
    record_span!(parser, span_start1374, "Output")
    return result1375
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1378 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2176 = parse_name(parser)
    name1376 = _t2176
    _t2177 = parse_epoch(parser)
    epoch1377 = _t2177
    consume_literal!(parser, ")")
    _t2178 = Proto.WhatIf(branch=name1376, epoch=epoch1377)
    result1379 = _t2178
    record_span!(parser, span_start1378, "WhatIf")
    return result1379
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1382 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2180 = parse_name(parser)
        _t2179 = _t2180
    else
        _t2179 = nothing
    end
    name1380 = _t2179
    _t2181 = parse_relation_id(parser)
    relation_id1381 = _t2181
    consume_literal!(parser, ")")
    _t2182 = Proto.Abort(name=(!isnothing(name1380) ? name1380 : "abort"), relation_id=relation_id1381)
    result1383 = _t2182
    record_span!(parser, span_start1382, "Abort")
    return result1383
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1387 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2184 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2185 = 0
            else
                _t2185 = -1
            end
            _t2184 = _t2185
        end
        _t2183 = _t2184
    else
        _t2183 = -1
    end
    prediction1384 = _t2183
    if prediction1384 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2187 = parse_export_iceberg_config(parser)
        export_iceberg_config1386 = _t2187
        consume_literal!(parser, ")")
        _t2188 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1386))
        _t2186 = _t2188
    else
        if prediction1384 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2190 = parse_export_csv_config(parser)
            export_csv_config1385 = _t2190
            consume_literal!(parser, ")")
            _t2191 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1385))
            _t2189 = _t2191
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2186 = _t2189
    end
    result1388 = _t2186
    record_span!(parser, span_start1387, "Export")
    return result1388
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1396 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2193 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2194 = 1
            else
                _t2194 = -1
            end
            _t2193 = _t2194
        end
        _t2192 = _t2193
    else
        _t2192 = -1
    end
    prediction1389 = _t2192
    if prediction1389 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2196 = parse_export_csv_path(parser)
        export_csv_path1393 = _t2196
        _t2197 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1394 = _t2197
        _t2198 = parse_config_dict(parser)
        config_dict1395 = _t2198
        consume_literal!(parser, ")")
        _t2199 = construct_export_csv_config(parser, export_csv_path1393, export_csv_columns_list1394, config_dict1395)
        _t2195 = _t2199
    else
        if prediction1389 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2201 = parse_export_csv_output_location(parser)
            export_csv_output_location1390 = _t2201
            _t2202 = parse_export_csv_source(parser)
            export_csv_source1391 = _t2202
            _t2203 = parse_csv_config(parser)
            csv_config1392 = _t2203
            consume_literal!(parser, ")")
            _t2204 = construct_export_csv_config_with_location(parser, export_csv_output_location1390, export_csv_source1391, csv_config1392)
            _t2200 = _t2204
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2195 = _t2200
    end
    result1397 = _t2195
    record_span!(parser, span_start1396, "ExportCSVConfig")
    return result1397
end

function parse_export_csv_output_location(parser::ParserState)::Tuple{String, String}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "transaction_output_name", 1)
            _t2206 = 1
        else
            if match_lookahead_literal(parser, "path", 1)
                _t2207 = 0
            else
                _t2207 = -1
            end
            _t2206 = _t2207
        end
        _t2205 = _t2206
    else
        _t2205 = -1
    end
    prediction1398 = _t2205
    if prediction1398 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "transaction_output_name")
        _t2209 = parse_name(parser)
        name1400 = _t2209
        consume_literal!(parser, ")")
        _t2208 = ("", name1400,)
    else
        if prediction1398 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "path")
            string1399 = consume_terminal!(parser, "STRING")
            consume_literal!(parser, ")")
            _t2210 = (string1399, "",)
        else
            throw(ParseError("Unexpected token in export_csv_output_location" * ": " * string(lookahead(parser, 0))))
        end
        _t2208 = _t2210
    end
    return _t2208
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1407 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2212 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2213 = 0
            else
                _t2213 = -1
            end
            _t2212 = _t2213
        end
        _t2211 = _t2212
    else
        _t2211 = -1
    end
    prediction1401 = _t2211
    if prediction1401 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2215 = parse_relation_id(parser)
        relation_id1406 = _t2215
        consume_literal!(parser, ")")
        _t2216 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1406))
        _t2214 = _t2216
    else
        if prediction1401 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1402 = Proto.ExportCSVColumn[]
            cond1403 = match_lookahead_literal(parser, "(", 0)
            while cond1403
                _t2218 = parse_export_csv_column(parser)
                item1404 = _t2218
                push!(xs1402, item1404)
                cond1403 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1405 = xs1402
            consume_literal!(parser, ")")
            _t2219 = Proto.ExportCSVColumns(columns=export_csv_columns1405)
            _t2220 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2219))
            _t2217 = _t2220
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2214 = _t2217
    end
    result1408 = _t2214
    record_span!(parser, span_start1407, "ExportCSVSource")
    return result1408
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1411 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1409 = consume_terminal!(parser, "STRING")
    _t2221 = parse_relation_id(parser)
    relation_id1410 = _t2221
    consume_literal!(parser, ")")
    _t2222 = Proto.ExportCSVColumn(column_name=string1409, column_data=relation_id1410)
    result1412 = _t2222
    record_span!(parser, span_start1411, "ExportCSVColumn")
    return result1412
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1413 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1413
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1414 = Proto.ExportCSVColumn[]
    cond1415 = match_lookahead_literal(parser, "(", 0)
    while cond1415
        _t2223 = parse_export_csv_column(parser)
        item1416 = _t2223
        push!(xs1414, item1416)
        cond1415 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1417 = xs1414
    consume_literal!(parser, ")")
    return export_csv_columns1417
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1423 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2224 = parse_iceberg_locator(parser)
    iceberg_locator1418 = _t2224
    _t2225 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1419 = _t2225
    _t2226 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1420 = _t2226
    _t2227 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1421 = _t2227
    if match_lookahead_literal(parser, "{", 0)
        _t2229 = parse_config_dict(parser)
        _t2228 = _t2229
    else
        _t2228 = nothing
    end
    config_dict1422 = _t2228
    consume_literal!(parser, ")")
    _t2230 = construct_export_iceberg_config_full(parser, iceberg_locator1418, iceberg_catalog_config1419, export_iceberg_table_def1420, iceberg_table_properties1421, config_dict1422)
    result1424 = _t2230
    record_span!(parser, span_start1423, "ExportIcebergConfig")
    return result1424
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1426 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2231 = parse_relation_id(parser)
    relation_id1425 = _t2231
    consume_literal!(parser, ")")
    result1427 = relation_id1425
    record_span!(parser, span_start1426, "RelationId")
    return result1427
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1428 = Tuple{String, String}[]
    cond1429 = match_lookahead_literal(parser, "(", 0)
    while cond1429
        _t2232 = parse_iceberg_property_entry(parser)
        item1430 = _t2232
        push!(xs1428, item1430)
        cond1429 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1431 = xs1428
    consume_literal!(parser, ")")
    return iceberg_property_entrys1431
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
