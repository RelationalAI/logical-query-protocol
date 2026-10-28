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
        _t2238 = nothing
    end
    if _has_proto_field(value, Symbol("int32_value"))
        return _get_oneof_field(value, :int32_value)
    else
        _t2239 = nothing
    end
    throw(ParseError("expected an int32 value (e.g. `1i32`) for this config field"))
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2240 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2241 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2242 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2243 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2244 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2245 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2246 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2247 = nothing
    end
    return nothing
end

function construct_non_cdc_relations(parser::ParserState, targets::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2248 = Proto.PlainTargets(targets=targets)
    _t2249 = Proto.TargetRelations(body=OneOf(:plain, _t2248), keys=Proto.NamedColumn[])
    return _t2249
end

function construct_cdc_relations(parser::ParserState, inserts::Vector{Proto.TargetRelation}, deletes::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2250 = Proto.CDCTargets(inserts=inserts, deletes=deletes)
    _t2251 = Proto.TargetRelations(body=OneOf(:cdc, _t2250), keys=Proto.NamedColumn[])
    return _t2251
end

function construct_relations(parser::ParserState, keys::Tuple{Vector{Proto.NamedColumn}, Bool}, body::Proto.TargetRelations, load_errors_opt::Union{Nothing, Proto.RelationId})::Proto.TargetRelations
    if _has_proto_field(body, Symbol("plain"))
        _t2253 = Proto.TargetRelations(body=OneOf(:plain, _get_oneof_field(body, :plain)), keys=keys[1], synthetic_key=keys[2], load_errors=load_errors_opt)
        return _t2253
    else
        _t2252 = nothing
    end
    _t2254 = Proto.TargetRelations(body=OneOf(:cdc, _get_oneof_field(body, :cdc)), keys=keys[1], synthetic_key=keys[2], load_errors=load_errors_opt)
    return _t2254
end

function construct_csv_data(parser::ParserState, locator::Proto.CSVLocator, config::Proto.CSVConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, relations_opt::Union{Nothing, Proto.TargetRelations}, asof::String)::Proto.CSVData
    _t2255 = Proto.CSVData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), asof=asof, relations=relations_opt)
    return _t2255
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2256 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2256
    _t2257 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2257
    _t2258 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2258
    _t2259 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2259
    _t2260 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2260
    _t2261 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2261
    _t2262 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2262
    _t2263 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2263
    _t2264 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2264
    _t2265 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2265
    _t2266 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2266
    _t2267 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2267
    _t2268 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2268
    _t2269 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2269
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2270 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2271 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2272 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2273 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2274 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2275 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2276 = Proto.StorageIntegration(provider=_t2271, azure_sas_token=_t2272, s3_region=_t2273, s3_access_key_id=_t2274, s3_secret_access_key=_t2275)
    return _t2276
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2277 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2277
    _t2278 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2278
    _t2279 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2279
    _t2280 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2280
    _t2281 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2281
    _t2282 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2282
    _t2283 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2283
    _t2284 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2284
    _t2285 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2285
    _t2286 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2286
    _t2287 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2287
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2288 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2288
    _t2289 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2289
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
    _t2290 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2290
    _t2291 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2291
    config_values_pairs = Tuple{String, Proto.Value}[]
    for pair in config_dict
        if (pair[1] != "semantics_version" && pair[1] != "ivm.maintenance_level")
            push!(config_values_pairs, pair)
        end
    end
    configuration_values = Dict(config_values_pairs)
    _t2292 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config, configuration_values=configuration_values)
    return _t2292
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2293 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2293
    _t2294 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2294
    _t2295 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2295
    _t2296 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2296
    _t2297 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2297
    _t2298 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2298
    _t2299 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2299
    _t2300 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2300
end

function construct_export_csv_config_with_location(parser::ParserState, location::Tuple{String, String}, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2301 = Proto.ExportCSVConfig(path=location[1], transaction_output_name=location[2], csv_source=csv_source, csv_config=csv_config)
    return _t2301
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2302 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2302
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, relations_opt::Union{Nothing, Proto.TargetRelations}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2303 = Proto.IcebergData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta, relations=relations_opt)
    return _t2303
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2304 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2304
    _t2305 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2305
    _t2306 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2306
    table_props = Dict(table_property_pairs)
    _t2307 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2307
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start723 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1435 = parse_configure(parser)
        _t1434 = _t1435
    else
        _t1434 = nothing
    end
    configure717 = _t1434
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1437 = parse_sync(parser)
        _t1436 = _t1437
    else
        _t1436 = nothing
    end
    sync718 = _t1436
    xs719 = Proto.Epoch[]
    cond720 = match_lookahead_literal(parser, "(", 0)
    while cond720
        _t1438 = parse_epoch(parser)
        item721 = _t1438
        push!(xs719, item721)
        cond720 = match_lookahead_literal(parser, "(", 0)
    end
    epochs722 = xs719
    consume_literal!(parser, ")")
    _t1439 = default_configure(parser)
    _t1440 = Proto.Transaction(epochs=epochs722, configure=(!isnothing(configure717) ? configure717 : _t1439), sync=sync718)
    result724 = _t1440
    record_span!(parser, span_start723, "Transaction")
    return result724
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start726 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1441 = parse_config_dict(parser)
    config_dict725 = _t1441
    consume_literal!(parser, ")")
    _t1442 = construct_configure(parser, config_dict725)
    result727 = _t1442
    record_span!(parser, span_start726, "Configure")
    return result727
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs728 = Tuple{String, Proto.Value}[]
    cond729 = match_lookahead_literal(parser, ":", 0)
    while cond729
        _t1443 = parse_config_key_value(parser)
        item730 = _t1443
        push!(xs728, item730)
        cond729 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values731 = xs728
    consume_literal!(parser, "}")
    return config_key_values731
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol732 = consume_terminal!(parser, "SYMBOL")
    _t1444 = parse_raw_value(parser)
    raw_value733 = _t1444
    return (symbol732, raw_value733,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start747 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1445 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1446 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1447 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1449 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1450 = 0
                        else
                            _t1450 = -1
                        end
                        _t1449 = _t1450
                    end
                    _t1448 = _t1449
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1451 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1452 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1453 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1454 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1455 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1456 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1457 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1458 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1459 = 10
                                                    else
                                                        _t1459 = -1
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
                    _t1448 = _t1451
                end
                _t1447 = _t1448
            end
            _t1446 = _t1447
        end
        _t1445 = _t1446
    end
    prediction734 = _t1445
    if prediction734 == 12
        _t1461 = parse_boolean_value(parser)
        boolean_value746 = _t1461
        _t1462 = Proto.Value(value=OneOf(:boolean_value, boolean_value746))
        _t1460 = _t1462
    else
        if prediction734 == 11
            consume_literal!(parser, "missing")
            _t1464 = Proto.MissingValue()
            _t1465 = Proto.Value(value=OneOf(:missing_value, _t1464))
            _t1463 = _t1465
        else
            if prediction734 == 10
                decimal745 = consume_terminal!(parser, "DECIMAL")
                _t1467 = Proto.Value(value=OneOf(:decimal_value, decimal745))
                _t1466 = _t1467
            else
                if prediction734 == 9
                    int128744 = consume_terminal!(parser, "INT128")
                    _t1469 = Proto.Value(value=OneOf(:int128_value, int128744))
                    _t1468 = _t1469
                else
                    if prediction734 == 8
                        uint128743 = consume_terminal!(parser, "UINT128")
                        _t1471 = Proto.Value(value=OneOf(:uint128_value, uint128743))
                        _t1470 = _t1471
                    else
                        if prediction734 == 7
                            uint32742 = consume_terminal!(parser, "UINT32")
                            _t1473 = Proto.Value(value=OneOf(:uint32_value, uint32742))
                            _t1472 = _t1473
                        else
                            if prediction734 == 6
                                float741 = consume_terminal!(parser, "FLOAT")
                                _t1475 = Proto.Value(value=OneOf(:float_value, float741))
                                _t1474 = _t1475
                            else
                                if prediction734 == 5
                                    float32740 = consume_terminal!(parser, "FLOAT32")
                                    _t1477 = Proto.Value(value=OneOf(:float32_value, float32740))
                                    _t1476 = _t1477
                                else
                                    if prediction734 == 4
                                        int739 = consume_terminal!(parser, "INT")
                                        _t1479 = Proto.Value(value=OneOf(:int_value, int739))
                                        _t1478 = _t1479
                                    else
                                        if prediction734 == 3
                                            int32738 = consume_terminal!(parser, "INT32")
                                            _t1481 = Proto.Value(value=OneOf(:int32_value, int32738))
                                            _t1480 = _t1481
                                        else
                                            if prediction734 == 2
                                                string737 = consume_terminal!(parser, "STRING")
                                                _t1483 = Proto.Value(value=OneOf(:string_value, string737))
                                                _t1482 = _t1483
                                            else
                                                if prediction734 == 1
                                                    _t1485 = parse_raw_datetime(parser)
                                                    raw_datetime736 = _t1485
                                                    _t1486 = Proto.Value(value=OneOf(:datetime_value, raw_datetime736))
                                                    _t1484 = _t1486
                                                else
                                                    if prediction734 == 0
                                                        _t1488 = parse_raw_date(parser)
                                                        raw_date735 = _t1488
                                                        _t1489 = Proto.Value(value=OneOf(:date_value, raw_date735))
                                                        _t1487 = _t1489
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1484 = _t1487
                                                end
                                                _t1482 = _t1484
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
            _t1463 = _t1466
        end
        _t1460 = _t1463
    end
    result748 = _t1460
    record_span!(parser, span_start747, "Value")
    return result748
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start752 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int749 = consume_terminal!(parser, "INT")
    int_3750 = consume_terminal!(parser, "INT")
    int_4751 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1490 = Proto.DateValue(year=Int32(int749), month=Int32(int_3750), day=Int32(int_4751))
    result753 = _t1490
    record_span!(parser, span_start752, "DateValue")
    return result753
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start761 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int754 = consume_terminal!(parser, "INT")
    int_3755 = consume_terminal!(parser, "INT")
    int_4756 = consume_terminal!(parser, "INT")
    int_5757 = consume_terminal!(parser, "INT")
    int_6758 = consume_terminal!(parser, "INT")
    int_7759 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1491 = consume_terminal!(parser, "INT")
    else
        _t1491 = nothing
    end
    int_8760 = _t1491
    consume_literal!(parser, ")")
    _t1492 = Proto.DateTimeValue(year=Int32(int754), month=Int32(int_3755), day=Int32(int_4756), hour=Int32(int_5757), minute=Int32(int_6758), second=Int32(int_7759), microsecond=Int32((!isnothing(int_8760) ? int_8760 : 0)))
    result762 = _t1492
    record_span!(parser, span_start761, "DateTimeValue")
    return result762
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1493 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1494 = 1
        else
            _t1494 = -1
        end
        _t1493 = _t1494
    end
    prediction763 = _t1493
    if prediction763 == 1
        consume_literal!(parser, "false")
        _t1495 = false
    else
        if prediction763 == 0
            consume_literal!(parser, "true")
            _t1496 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1495 = _t1496
    end
    return _t1495
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start768 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs764 = Proto.FragmentId[]
    cond765 = match_lookahead_literal(parser, ":", 0)
    while cond765
        _t1497 = parse_fragment_id(parser)
        item766 = _t1497
        push!(xs764, item766)
        cond765 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids767 = xs764
    consume_literal!(parser, ")")
    _t1498 = Proto.Sync(fragments=fragment_ids767)
    result769 = _t1498
    record_span!(parser, span_start768, "Sync")
    return result769
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start771 = span_start(parser)
    consume_literal!(parser, ":")
    symbol770 = consume_terminal!(parser, "SYMBOL")
    result772 = Proto.FragmentId(Vector{UInt8}(symbol770))
    record_span!(parser, span_start771, "FragmentId")
    return result772
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start775 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1500 = parse_epoch_writes(parser)
        _t1499 = _t1500
    else
        _t1499 = nothing
    end
    epoch_writes773 = _t1499
    if match_lookahead_literal(parser, "(", 0)
        _t1502 = parse_epoch_reads(parser)
        _t1501 = _t1502
    else
        _t1501 = nothing
    end
    epoch_reads774 = _t1501
    consume_literal!(parser, ")")
    _t1503 = Proto.Epoch(writes=(!isnothing(epoch_writes773) ? epoch_writes773 : Proto.Write[]), reads=(!isnothing(epoch_reads774) ? epoch_reads774 : Proto.Read[]))
    result776 = _t1503
    record_span!(parser, span_start775, "Epoch")
    return result776
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs777 = Proto.Write[]
    cond778 = match_lookahead_literal(parser, "(", 0)
    while cond778
        _t1504 = parse_write(parser)
        item779 = _t1504
        push!(xs777, item779)
        cond778 = match_lookahead_literal(parser, "(", 0)
    end
    writes780 = xs777
    consume_literal!(parser, ")")
    return writes780
end

function parse_write(parser::ParserState)::Proto.Write
    span_start786 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1506 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1507 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1508 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1509 = 2
                    else
                        _t1509 = -1
                    end
                    _t1508 = _t1509
                end
                _t1507 = _t1508
            end
            _t1506 = _t1507
        end
        _t1505 = _t1506
    else
        _t1505 = -1
    end
    prediction781 = _t1505
    if prediction781 == 3
        _t1511 = parse_snapshot(parser)
        snapshot785 = _t1511
        _t1512 = Proto.Write(write_type=OneOf(:snapshot, snapshot785))
        _t1510 = _t1512
    else
        if prediction781 == 2
            _t1514 = parse_context(parser)
            context784 = _t1514
            _t1515 = Proto.Write(write_type=OneOf(:context, context784))
            _t1513 = _t1515
        else
            if prediction781 == 1
                _t1517 = parse_undefine(parser)
                undefine783 = _t1517
                _t1518 = Proto.Write(write_type=OneOf(:undefine, undefine783))
                _t1516 = _t1518
            else
                if prediction781 == 0
                    _t1520 = parse_define(parser)
                    define782 = _t1520
                    _t1521 = Proto.Write(write_type=OneOf(:define, define782))
                    _t1519 = _t1521
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1516 = _t1519
            end
            _t1513 = _t1516
        end
        _t1510 = _t1513
    end
    result787 = _t1510
    record_span!(parser, span_start786, "Write")
    return result787
end

function parse_define(parser::ParserState)::Proto.Define
    span_start789 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1522 = parse_fragment(parser)
    fragment788 = _t1522
    consume_literal!(parser, ")")
    _t1523 = Proto.Define(fragment=fragment788)
    result790 = _t1523
    record_span!(parser, span_start789, "Define")
    return result790
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start796 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1524 = parse_new_fragment_id(parser)
    new_fragment_id791 = _t1524
    xs792 = Proto.Declaration[]
    cond793 = match_lookahead_literal(parser, "(", 0)
    while cond793
        _t1525 = parse_declaration(parser)
        item794 = _t1525
        push!(xs792, item794)
        cond793 = match_lookahead_literal(parser, "(", 0)
    end
    declarations795 = xs792
    consume_literal!(parser, ")")
    result797 = construct_fragment(parser, new_fragment_id791, declarations795)
    record_span!(parser, span_start796, "Fragment")
    return result797
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start799 = span_start(parser)
    _t1526 = parse_fragment_id(parser)
    fragment_id798 = _t1526
    start_fragment!(parser, fragment_id798)
    result800 = fragment_id798
    record_span!(parser, span_start799, "FragmentId")
    return result800
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start806 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1528 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1529 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1530 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1531 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1532 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1533 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1534 = 1
                                else
                                    _t1534 = -1
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
    else
        _t1527 = -1
    end
    prediction801 = _t1527
    if prediction801 == 3
        _t1536 = parse_data(parser)
        data805 = _t1536
        _t1537 = Proto.Declaration(declaration_type=OneOf(:data, data805))
        _t1535 = _t1537
    else
        if prediction801 == 2
            _t1539 = parse_constraint(parser)
            constraint804 = _t1539
            _t1540 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint804))
            _t1538 = _t1540
        else
            if prediction801 == 1
                _t1542 = parse_algorithm(parser)
                algorithm803 = _t1542
                _t1543 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm803))
                _t1541 = _t1543
            else
                if prediction801 == 0
                    _t1545 = parse_def(parser)
                    def802 = _t1545
                    _t1546 = Proto.Declaration(declaration_type=OneOf(:def, def802))
                    _t1544 = _t1546
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1541 = _t1544
            end
            _t1538 = _t1541
        end
        _t1535 = _t1538
    end
    result807 = _t1535
    record_span!(parser, span_start806, "Declaration")
    return result807
end

function parse_def(parser::ParserState)::Proto.Def
    span_start811 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1547 = parse_relation_id(parser)
    relation_id808 = _t1547
    _t1548 = parse_abstraction(parser)
    abstraction809 = _t1548
    if match_lookahead_literal(parser, "(", 0)
        _t1550 = parse_attrs(parser)
        _t1549 = _t1550
    else
        _t1549 = nothing
    end
    attrs810 = _t1549
    consume_literal!(parser, ")")
    _t1551 = Proto.Def(name=relation_id808, body=abstraction809, attrs=(!isnothing(attrs810) ? attrs810 : Proto.Attribute[]))
    result812 = _t1551
    record_span!(parser, span_start811, "Def")
    return result812
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start816 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1552 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1553 = 1
        else
            _t1553 = -1
        end
        _t1552 = _t1553
    end
    prediction813 = _t1552
    if prediction813 == 1
        uint128815 = consume_terminal!(parser, "UINT128")
        _t1554 = Proto.RelationId(uint128815.low, uint128815.high)
    else
        if prediction813 == 0
            consume_literal!(parser, ":")
            symbol814 = consume_terminal!(parser, "SYMBOL")
            _t1555 = relation_id_from_string(parser, symbol814)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1554 = _t1555
    end
    result817 = _t1554
    record_span!(parser, span_start816, "RelationId")
    return result817
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start820 = span_start(parser)
    consume_literal!(parser, "(")
    _t1556 = parse_bindings(parser)
    bindings818 = _t1556
    _t1557 = parse_formula(parser)
    formula819 = _t1557
    consume_literal!(parser, ")")
    _t1558 = Proto.Abstraction(vars=vcat(bindings818[1], !isnothing(bindings818[2]) ? bindings818[2] : []), value=formula819)
    result821 = _t1558
    record_span!(parser, span_start820, "Abstraction")
    return result821
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs822 = Proto.Binding[]
    cond823 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond823
        _t1559 = parse_binding(parser)
        item824 = _t1559
        push!(xs822, item824)
        cond823 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings825 = xs822
    if match_lookahead_literal(parser, "|", 0)
        _t1561 = parse_value_bindings(parser)
        _t1560 = _t1561
    else
        _t1560 = nothing
    end
    value_bindings826 = _t1560
    consume_literal!(parser, "]")
    return (bindings825, (!isnothing(value_bindings826) ? value_bindings826 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start829 = span_start(parser)
    symbol827 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1562 = parse_type(parser)
    type828 = _t1562
    _t1563 = Proto.Var(name=symbol827)
    _t1564 = Proto.Binding(var=_t1563, var"#type"=type828)
    result830 = _t1564
    record_span!(parser, span_start829, "Binding")
    return result830
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start847 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1565 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1566 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1567 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1568 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1569 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1570 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1571 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1572 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1573 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1574 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1575 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1576 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1577 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            if match_lookahead_literal(parser, "FIXED", 1)
                                                                _t1579 = 14
                                                            else
                                                                if match_lookahead_literal(parser, "DECIMAL", 1)
                                                                    _t1580 = 9
                                                                else
                                                                    _t1580 = -1
                                                                end
                                                                _t1579 = _t1580
                                                            end
                                                            _t1578 = _t1579
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
    prediction831 = _t1565
    if prediction831 == 14
        _t1582 = parse_fixed_type(parser)
        fixed_type846 = _t1582
        _t1583 = Proto.var"#Type"(var"#type"=OneOf(:fixed_type, fixed_type846))
        _t1581 = _t1583
    else
        if prediction831 == 13
            _t1585 = parse_uint32_type(parser)
            uint32_type845 = _t1585
            _t1586 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type845))
            _t1584 = _t1586
        else
            if prediction831 == 12
                _t1588 = parse_float32_type(parser)
                float32_type844 = _t1588
                _t1589 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type844))
                _t1587 = _t1589
            else
                if prediction831 == 11
                    _t1591 = parse_int32_type(parser)
                    int32_type843 = _t1591
                    _t1592 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type843))
                    _t1590 = _t1592
                else
                    if prediction831 == 10
                        _t1594 = parse_boolean_type(parser)
                        boolean_type842 = _t1594
                        _t1595 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type842))
                        _t1593 = _t1595
                    else
                        if prediction831 == 9
                            _t1597 = parse_decimal_type(parser)
                            decimal_type841 = _t1597
                            _t1598 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type841))
                            _t1596 = _t1598
                        else
                            if prediction831 == 8
                                _t1600 = parse_missing_type(parser)
                                missing_type840 = _t1600
                                _t1601 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type840))
                                _t1599 = _t1601
                            else
                                if prediction831 == 7
                                    _t1603 = parse_datetime_type(parser)
                                    datetime_type839 = _t1603
                                    _t1604 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type839))
                                    _t1602 = _t1604
                                else
                                    if prediction831 == 6
                                        _t1606 = parse_date_type(parser)
                                        date_type838 = _t1606
                                        _t1607 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type838))
                                        _t1605 = _t1607
                                    else
                                        if prediction831 == 5
                                            _t1609 = parse_int128_type(parser)
                                            int128_type837 = _t1609
                                            _t1610 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type837))
                                            _t1608 = _t1610
                                        else
                                            if prediction831 == 4
                                                _t1612 = parse_uint128_type(parser)
                                                uint128_type836 = _t1612
                                                _t1613 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type836))
                                                _t1611 = _t1613
                                            else
                                                if prediction831 == 3
                                                    _t1615 = parse_float_type(parser)
                                                    float_type835 = _t1615
                                                    _t1616 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type835))
                                                    _t1614 = _t1616
                                                else
                                                    if prediction831 == 2
                                                        _t1618 = parse_int_type(parser)
                                                        int_type834 = _t1618
                                                        _t1619 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type834))
                                                        _t1617 = _t1619
                                                    else
                                                        if prediction831 == 1
                                                            _t1621 = parse_string_type(parser)
                                                            string_type833 = _t1621
                                                            _t1622 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type833))
                                                            _t1620 = _t1622
                                                        else
                                                            if prediction831 == 0
                                                                _t1624 = parse_unspecified_type(parser)
                                                                unspecified_type832 = _t1624
                                                                _t1625 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type832))
                                                                _t1623 = _t1625
                                                            else
                                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                            end
                                                            _t1620 = _t1623
                                                        end
                                                        _t1617 = _t1620
                                                    end
                                                    _t1614 = _t1617
                                                end
                                                _t1611 = _t1614
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
    result848 = _t1581
    record_span!(parser, span_start847, "Type")
    return result848
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start849 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1626 = Proto.UnspecifiedType()
    result850 = _t1626
    record_span!(parser, span_start849, "UnspecifiedType")
    return result850
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start851 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1627 = Proto.StringType()
    result852 = _t1627
    record_span!(parser, span_start851, "StringType")
    return result852
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start853 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1628 = Proto.IntType()
    result854 = _t1628
    record_span!(parser, span_start853, "IntType")
    return result854
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start855 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1629 = Proto.FloatType()
    result856 = _t1629
    record_span!(parser, span_start855, "FloatType")
    return result856
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start857 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1630 = Proto.UInt128Type()
    result858 = _t1630
    record_span!(parser, span_start857, "UInt128Type")
    return result858
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start859 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1631 = Proto.Int128Type()
    result860 = _t1631
    record_span!(parser, span_start859, "Int128Type")
    return result860
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start861 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1632 = Proto.DateType()
    result862 = _t1632
    record_span!(parser, span_start861, "DateType")
    return result862
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start863 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1633 = Proto.DateTimeType()
    result864 = _t1633
    record_span!(parser, span_start863, "DateTimeType")
    return result864
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start865 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1634 = Proto.MissingType()
    result866 = _t1634
    record_span!(parser, span_start865, "MissingType")
    return result866
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start869 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int867 = consume_terminal!(parser, "INT")
    int_3868 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1635 = Proto.DecimalType(precision=Int32(int867), scale=Int32(int_3868))
    result870 = _t1635
    record_span!(parser, span_start869, "DecimalType")
    return result870
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start871 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1636 = Proto.BooleanType()
    result872 = _t1636
    record_span!(parser, span_start871, "BooleanType")
    return result872
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start873 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1637 = Proto.Int32Type()
    result874 = _t1637
    record_span!(parser, span_start873, "Int32Type")
    return result874
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start875 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1638 = Proto.Float32Type()
    result876 = _t1638
    record_span!(parser, span_start875, "Float32Type")
    return result876
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start877 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1639 = Proto.UInt32Type()
    result878 = _t1639
    record_span!(parser, span_start877, "UInt32Type")
    return result878
end

function parse_fixed_type(parser::ParserState)::Proto.FixedType
    span_start880 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "FIXED")
    int879 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1640 = Proto.FixedType(length=Int32(int879))
    result881 = _t1640
    record_span!(parser, span_start880, "FixedType")
    return result881
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs882 = Proto.Binding[]
    cond883 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond883
        _t1641 = parse_binding(parser)
        item884 = _t1641
        push!(xs882, item884)
        cond883 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings885 = xs882
    return bindings885
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start900 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1643 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1644 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1645 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1646 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1647 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1648 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1649 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1650 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1651 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1652 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1653 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1654 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1655 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1656 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1657 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1658 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1659 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1660 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1661 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1662 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1663 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
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
    else
        _t1642 = -1
    end
    prediction886 = _t1642
    if prediction886 == 12
        _t1666 = parse_cast(parser)
        cast899 = _t1666
        _t1667 = Proto.Formula(formula_type=OneOf(:cast, cast899))
        _t1665 = _t1667
    else
        if prediction886 == 11
            _t1669 = parse_rel_atom(parser)
            rel_atom898 = _t1669
            _t1670 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom898))
            _t1668 = _t1670
        else
            if prediction886 == 10
                _t1672 = parse_primitive(parser)
                primitive897 = _t1672
                _t1673 = Proto.Formula(formula_type=OneOf(:primitive, primitive897))
                _t1671 = _t1673
            else
                if prediction886 == 9
                    _t1675 = parse_pragma(parser)
                    pragma896 = _t1675
                    _t1676 = Proto.Formula(formula_type=OneOf(:pragma, pragma896))
                    _t1674 = _t1676
                else
                    if prediction886 == 8
                        _t1678 = parse_atom(parser)
                        atom895 = _t1678
                        _t1679 = Proto.Formula(formula_type=OneOf(:atom, atom895))
                        _t1677 = _t1679
                    else
                        if prediction886 == 7
                            _t1681 = parse_ffi(parser)
                            ffi894 = _t1681
                            _t1682 = Proto.Formula(formula_type=OneOf(:ffi, ffi894))
                            _t1680 = _t1682
                        else
                            if prediction886 == 6
                                _t1684 = parse_not(parser)
                                not893 = _t1684
                                _t1685 = Proto.Formula(formula_type=OneOf(:not, not893))
                                _t1683 = _t1685
                            else
                                if prediction886 == 5
                                    _t1687 = parse_disjunction(parser)
                                    disjunction892 = _t1687
                                    _t1688 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction892))
                                    _t1686 = _t1688
                                else
                                    if prediction886 == 4
                                        _t1690 = parse_conjunction(parser)
                                        conjunction891 = _t1690
                                        _t1691 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction891))
                                        _t1689 = _t1691
                                    else
                                        if prediction886 == 3
                                            _t1693 = parse_reduce(parser)
                                            reduce890 = _t1693
                                            _t1694 = Proto.Formula(formula_type=OneOf(:reduce, reduce890))
                                            _t1692 = _t1694
                                        else
                                            if prediction886 == 2
                                                _t1696 = parse_exists(parser)
                                                exists889 = _t1696
                                                _t1697 = Proto.Formula(formula_type=OneOf(:exists, exists889))
                                                _t1695 = _t1697
                                            else
                                                if prediction886 == 1
                                                    _t1699 = parse_false(parser)
                                                    false888 = _t1699
                                                    _t1700 = Proto.Formula(formula_type=OneOf(:disjunction, false888))
                                                    _t1698 = _t1700
                                                else
                                                    if prediction886 == 0
                                                        _t1702 = parse_true(parser)
                                                        true887 = _t1702
                                                        _t1703 = Proto.Formula(formula_type=OneOf(:conjunction, true887))
                                                        _t1701 = _t1703
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1698 = _t1701
                                                end
                                                _t1695 = _t1698
                                            end
                                            _t1692 = _t1695
                                        end
                                        _t1689 = _t1692
                                    end
                                    _t1686 = _t1689
                                end
                                _t1683 = _t1686
                            end
                            _t1680 = _t1683
                        end
                        _t1677 = _t1680
                    end
                    _t1674 = _t1677
                end
                _t1671 = _t1674
            end
            _t1668 = _t1671
        end
        _t1665 = _t1668
    end
    result901 = _t1665
    record_span!(parser, span_start900, "Formula")
    return result901
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start902 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1704 = Proto.Conjunction(args=Proto.Formula[])
    result903 = _t1704
    record_span!(parser, span_start902, "Conjunction")
    return result903
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start904 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1705 = Proto.Disjunction(args=Proto.Formula[])
    result905 = _t1705
    record_span!(parser, span_start904, "Disjunction")
    return result905
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start908 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1706 = parse_bindings(parser)
    bindings906 = _t1706
    _t1707 = parse_formula(parser)
    formula907 = _t1707
    consume_literal!(parser, ")")
    _t1708 = Proto.Abstraction(vars=vcat(bindings906[1], !isnothing(bindings906[2]) ? bindings906[2] : []), value=formula907)
    _t1709 = Proto.Exists(body=_t1708)
    result909 = _t1709
    record_span!(parser, span_start908, "Exists")
    return result909
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start913 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1710 = parse_abstraction(parser)
    abstraction910 = _t1710
    _t1711 = parse_abstraction(parser)
    abstraction_3911 = _t1711
    _t1712 = parse_terms(parser)
    terms912 = _t1712
    consume_literal!(parser, ")")
    _t1713 = Proto.Reduce(op=abstraction910, body=abstraction_3911, terms=terms912)
    result914 = _t1713
    record_span!(parser, span_start913, "Reduce")
    return result914
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs915 = Proto.Term[]
    cond916 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond916
        _t1714 = parse_term(parser)
        item917 = _t1714
        push!(xs915, item917)
        cond916 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms918 = xs915
    consume_literal!(parser, ")")
    return terms918
end

function parse_term(parser::ParserState)::Proto.Term
    span_start922 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1715 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1716 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1717 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1718 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1719 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1720 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1721 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1722 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1723 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1724 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1725 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1726 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1727 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1728 = 1
                                                        else
                                                            _t1728 = -1
                                                        end
                                                        _t1727 = _t1728
                                                    end
                                                    _t1726 = _t1727
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
    prediction919 = _t1715
    if prediction919 == 1
        _t1730 = parse_value(parser)
        value921 = _t1730
        _t1731 = Proto.Term(term_type=OneOf(:constant, value921))
        _t1729 = _t1731
    else
        if prediction919 == 0
            _t1733 = parse_var(parser)
            var920 = _t1733
            _t1734 = Proto.Term(term_type=OneOf(:var, var920))
            _t1732 = _t1734
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1729 = _t1732
    end
    result923 = _t1729
    record_span!(parser, span_start922, "Term")
    return result923
end

function parse_var(parser::ParserState)::Proto.Var
    span_start925 = span_start(parser)
    symbol924 = consume_terminal!(parser, "SYMBOL")
    _t1735 = Proto.Var(name=symbol924)
    result926 = _t1735
    record_span!(parser, span_start925, "Var")
    return result926
end

function parse_value(parser::ParserState)::Proto.Value
    span_start940 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1736 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1737 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1738 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1740 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1741 = 0
                        else
                            _t1741 = -1
                        end
                        _t1740 = _t1741
                    end
                    _t1739 = _t1740
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1742 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1743 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1744 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1745 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1746 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1747 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1748 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1749 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1750 = 10
                                                    else
                                                        _t1750 = -1
                                                    end
                                                    _t1749 = _t1750
                                                end
                                                _t1748 = _t1749
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
                    _t1739 = _t1742
                end
                _t1738 = _t1739
            end
            _t1737 = _t1738
        end
        _t1736 = _t1737
    end
    prediction927 = _t1736
    if prediction927 == 12
        _t1752 = parse_boolean_value(parser)
        boolean_value939 = _t1752
        _t1753 = Proto.Value(value=OneOf(:boolean_value, boolean_value939))
        _t1751 = _t1753
    else
        if prediction927 == 11
            consume_literal!(parser, "missing")
            _t1755 = Proto.MissingValue()
            _t1756 = Proto.Value(value=OneOf(:missing_value, _t1755))
            _t1754 = _t1756
        else
            if prediction927 == 10
                formatted_decimal938 = consume_terminal!(parser, "DECIMAL")
                _t1758 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal938))
                _t1757 = _t1758
            else
                if prediction927 == 9
                    formatted_int128937 = consume_terminal!(parser, "INT128")
                    _t1760 = Proto.Value(value=OneOf(:int128_value, formatted_int128937))
                    _t1759 = _t1760
                else
                    if prediction927 == 8
                        formatted_uint128936 = consume_terminal!(parser, "UINT128")
                        _t1762 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128936))
                        _t1761 = _t1762
                    else
                        if prediction927 == 7
                            formatted_uint32935 = consume_terminal!(parser, "UINT32")
                            _t1764 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32935))
                            _t1763 = _t1764
                        else
                            if prediction927 == 6
                                formatted_float934 = consume_terminal!(parser, "FLOAT")
                                _t1766 = Proto.Value(value=OneOf(:float_value, formatted_float934))
                                _t1765 = _t1766
                            else
                                if prediction927 == 5
                                    formatted_float32933 = consume_terminal!(parser, "FLOAT32")
                                    _t1768 = Proto.Value(value=OneOf(:float32_value, formatted_float32933))
                                    _t1767 = _t1768
                                else
                                    if prediction927 == 4
                                        formatted_int932 = consume_terminal!(parser, "INT")
                                        _t1770 = Proto.Value(value=OneOf(:int_value, formatted_int932))
                                        _t1769 = _t1770
                                    else
                                        if prediction927 == 3
                                            formatted_int32931 = consume_terminal!(parser, "INT32")
                                            _t1772 = Proto.Value(value=OneOf(:int32_value, formatted_int32931))
                                            _t1771 = _t1772
                                        else
                                            if prediction927 == 2
                                                formatted_string930 = consume_terminal!(parser, "STRING")
                                                _t1774 = Proto.Value(value=OneOf(:string_value, formatted_string930))
                                                _t1773 = _t1774
                                            else
                                                if prediction927 == 1
                                                    _t1776 = parse_datetime(parser)
                                                    datetime929 = _t1776
                                                    _t1777 = Proto.Value(value=OneOf(:datetime_value, datetime929))
                                                    _t1775 = _t1777
                                                else
                                                    if prediction927 == 0
                                                        _t1779 = parse_date(parser)
                                                        date928 = _t1779
                                                        _t1780 = Proto.Value(value=OneOf(:date_value, date928))
                                                        _t1778 = _t1780
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1775 = _t1778
                                                end
                                                _t1773 = _t1775
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
            _t1754 = _t1757
        end
        _t1751 = _t1754
    end
    result941 = _t1751
    record_span!(parser, span_start940, "Value")
    return result941
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start945 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int942 = consume_terminal!(parser, "INT")
    formatted_int_3943 = consume_terminal!(parser, "INT")
    formatted_int_4944 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1781 = Proto.DateValue(year=Int32(formatted_int942), month=Int32(formatted_int_3943), day=Int32(formatted_int_4944))
    result946 = _t1781
    record_span!(parser, span_start945, "DateValue")
    return result946
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start954 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int947 = consume_terminal!(parser, "INT")
    formatted_int_3948 = consume_terminal!(parser, "INT")
    formatted_int_4949 = consume_terminal!(parser, "INT")
    formatted_int_5950 = consume_terminal!(parser, "INT")
    formatted_int_6951 = consume_terminal!(parser, "INT")
    formatted_int_7952 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1782 = consume_terminal!(parser, "INT")
    else
        _t1782 = nothing
    end
    formatted_int_8953 = _t1782
    consume_literal!(parser, ")")
    _t1783 = Proto.DateTimeValue(year=Int32(formatted_int947), month=Int32(formatted_int_3948), day=Int32(formatted_int_4949), hour=Int32(formatted_int_5950), minute=Int32(formatted_int_6951), second=Int32(formatted_int_7952), microsecond=Int32((!isnothing(formatted_int_8953) ? formatted_int_8953 : 0)))
    result955 = _t1783
    record_span!(parser, span_start954, "DateTimeValue")
    return result955
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs956 = Proto.Formula[]
    cond957 = match_lookahead_literal(parser, "(", 0)
    while cond957
        _t1784 = parse_formula(parser)
        item958 = _t1784
        push!(xs956, item958)
        cond957 = match_lookahead_literal(parser, "(", 0)
    end
    formulas959 = xs956
    consume_literal!(parser, ")")
    _t1785 = Proto.Conjunction(args=formulas959)
    result961 = _t1785
    record_span!(parser, span_start960, "Conjunction")
    return result961
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start966 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs962 = Proto.Formula[]
    cond963 = match_lookahead_literal(parser, "(", 0)
    while cond963
        _t1786 = parse_formula(parser)
        item964 = _t1786
        push!(xs962, item964)
        cond963 = match_lookahead_literal(parser, "(", 0)
    end
    formulas965 = xs962
    consume_literal!(parser, ")")
    _t1787 = Proto.Disjunction(args=formulas965)
    result967 = _t1787
    record_span!(parser, span_start966, "Disjunction")
    return result967
end

function parse_not(parser::ParserState)::Proto.Not
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1788 = parse_formula(parser)
    formula968 = _t1788
    consume_literal!(parser, ")")
    _t1789 = Proto.Not(arg=formula968)
    result970 = _t1789
    record_span!(parser, span_start969, "Not")
    return result970
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1790 = parse_name(parser)
    name971 = _t1790
    _t1791 = parse_ffi_args(parser)
    ffi_args972 = _t1791
    _t1792 = parse_terms(parser)
    terms973 = _t1792
    consume_literal!(parser, ")")
    _t1793 = Proto.FFI(name=name971, args=ffi_args972, terms=terms973)
    result975 = _t1793
    record_span!(parser, span_start974, "FFI")
    return result975
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol976 = consume_terminal!(parser, "SYMBOL")
    return symbol976
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs977 = Proto.Abstraction[]
    cond978 = match_lookahead_literal(parser, "(", 0)
    while cond978
        _t1794 = parse_abstraction(parser)
        item979 = _t1794
        push!(xs977, item979)
        cond978 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions980 = xs977
    consume_literal!(parser, ")")
    return abstractions980
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start986 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1795 = parse_relation_id(parser)
    relation_id981 = _t1795
    xs982 = Proto.Term[]
    cond983 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond983
        _t1796 = parse_term(parser)
        item984 = _t1796
        push!(xs982, item984)
        cond983 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms985 = xs982
    consume_literal!(parser, ")")
    _t1797 = Proto.Atom(name=relation_id981, terms=terms985)
    result987 = _t1797
    record_span!(parser, span_start986, "Atom")
    return result987
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start993 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1798 = parse_name(parser)
    name988 = _t1798
    xs989 = Proto.Term[]
    cond990 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond990
        _t1799 = parse_term(parser)
        item991 = _t1799
        push!(xs989, item991)
        cond990 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms992 = xs989
    consume_literal!(parser, ")")
    _t1800 = Proto.Pragma(name=name988, terms=terms992)
    result994 = _t1800
    record_span!(parser, span_start993, "Pragma")
    return result994
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start1010 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1802 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1803 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1804 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1805 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1806 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1807 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1808 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1809 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1810 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1811 = 7
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
    else
        _t1801 = -1
    end
    prediction995 = _t1801
    if prediction995 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1813 = parse_name(parser)
        name1005 = _t1813
        xs1006 = Proto.RelTerm[]
        cond1007 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond1007
            _t1814 = parse_rel_term(parser)
            item1008 = _t1814
            push!(xs1006, item1008)
            cond1007 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms1009 = xs1006
        consume_literal!(parser, ")")
        _t1815 = Proto.Primitive(name=name1005, terms=rel_terms1009)
        _t1812 = _t1815
    else
        if prediction995 == 8
            _t1817 = parse_divide(parser)
            divide1004 = _t1817
            _t1816 = divide1004
        else
            if prediction995 == 7
                _t1819 = parse_multiply(parser)
                multiply1003 = _t1819
                _t1818 = multiply1003
            else
                if prediction995 == 6
                    _t1821 = parse_minus(parser)
                    minus1002 = _t1821
                    _t1820 = minus1002
                else
                    if prediction995 == 5
                        _t1823 = parse_add(parser)
                        add1001 = _t1823
                        _t1822 = add1001
                    else
                        if prediction995 == 4
                            _t1825 = parse_gt_eq(parser)
                            gt_eq1000 = _t1825
                            _t1824 = gt_eq1000
                        else
                            if prediction995 == 3
                                _t1827 = parse_gt(parser)
                                gt999 = _t1827
                                _t1826 = gt999
                            else
                                if prediction995 == 2
                                    _t1829 = parse_lt_eq(parser)
                                    lt_eq998 = _t1829
                                    _t1828 = lt_eq998
                                else
                                    if prediction995 == 1
                                        _t1831 = parse_lt(parser)
                                        lt997 = _t1831
                                        _t1830 = lt997
                                    else
                                        if prediction995 == 0
                                            _t1833 = parse_eq(parser)
                                            eq996 = _t1833
                                            _t1832 = eq996
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1830 = _t1832
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
        _t1812 = _t1816
    end
    result1011 = _t1812
    record_span!(parser, span_start1010, "Primitive")
    return result1011
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start1014 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1834 = parse_term(parser)
    term1012 = _t1834
    _t1835 = parse_term(parser)
    term_31013 = _t1835
    consume_literal!(parser, ")")
    _t1836 = Proto.RelTerm(rel_term_type=OneOf(:term, term1012))
    _t1837 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31013))
    _t1838 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1836, _t1837])
    result1015 = _t1838
    record_span!(parser, span_start1014, "Primitive")
    return result1015
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start1018 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1839 = parse_term(parser)
    term1016 = _t1839
    _t1840 = parse_term(parser)
    term_31017 = _t1840
    consume_literal!(parser, ")")
    _t1841 = Proto.RelTerm(rel_term_type=OneOf(:term, term1016))
    _t1842 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31017))
    _t1843 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1841, _t1842])
    result1019 = _t1843
    record_span!(parser, span_start1018, "Primitive")
    return result1019
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start1022 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1844 = parse_term(parser)
    term1020 = _t1844
    _t1845 = parse_term(parser)
    term_31021 = _t1845
    consume_literal!(parser, ")")
    _t1846 = Proto.RelTerm(rel_term_type=OneOf(:term, term1020))
    _t1847 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31021))
    _t1848 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1846, _t1847])
    result1023 = _t1848
    record_span!(parser, span_start1022, "Primitive")
    return result1023
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start1026 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1849 = parse_term(parser)
    term1024 = _t1849
    _t1850 = parse_term(parser)
    term_31025 = _t1850
    consume_literal!(parser, ")")
    _t1851 = Proto.RelTerm(rel_term_type=OneOf(:term, term1024))
    _t1852 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31025))
    _t1853 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1851, _t1852])
    result1027 = _t1853
    record_span!(parser, span_start1026, "Primitive")
    return result1027
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start1030 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1854 = parse_term(parser)
    term1028 = _t1854
    _t1855 = parse_term(parser)
    term_31029 = _t1855
    consume_literal!(parser, ")")
    _t1856 = Proto.RelTerm(rel_term_type=OneOf(:term, term1028))
    _t1857 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31029))
    _t1858 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1856, _t1857])
    result1031 = _t1858
    record_span!(parser, span_start1030, "Primitive")
    return result1031
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start1035 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1859 = parse_term(parser)
    term1032 = _t1859
    _t1860 = parse_term(parser)
    term_31033 = _t1860
    _t1861 = parse_term(parser)
    term_41034 = _t1861
    consume_literal!(parser, ")")
    _t1862 = Proto.RelTerm(rel_term_type=OneOf(:term, term1032))
    _t1863 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31033))
    _t1864 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41034))
    _t1865 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1862, _t1863, _t1864])
    result1036 = _t1865
    record_span!(parser, span_start1035, "Primitive")
    return result1036
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start1040 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1866 = parse_term(parser)
    term1037 = _t1866
    _t1867 = parse_term(parser)
    term_31038 = _t1867
    _t1868 = parse_term(parser)
    term_41039 = _t1868
    consume_literal!(parser, ")")
    _t1869 = Proto.RelTerm(rel_term_type=OneOf(:term, term1037))
    _t1870 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31038))
    _t1871 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41039))
    _t1872 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1869, _t1870, _t1871])
    result1041 = _t1872
    record_span!(parser, span_start1040, "Primitive")
    return result1041
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1045 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1873 = parse_term(parser)
    term1042 = _t1873
    _t1874 = parse_term(parser)
    term_31043 = _t1874
    _t1875 = parse_term(parser)
    term_41044 = _t1875
    consume_literal!(parser, ")")
    _t1876 = Proto.RelTerm(rel_term_type=OneOf(:term, term1042))
    _t1877 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31043))
    _t1878 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41044))
    _t1879 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1876, _t1877, _t1878])
    result1046 = _t1879
    record_span!(parser, span_start1045, "Primitive")
    return result1046
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1050 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1880 = parse_term(parser)
    term1047 = _t1880
    _t1881 = parse_term(parser)
    term_31048 = _t1881
    _t1882 = parse_term(parser)
    term_41049 = _t1882
    consume_literal!(parser, ")")
    _t1883 = Proto.RelTerm(rel_term_type=OneOf(:term, term1047))
    _t1884 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31048))
    _t1885 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41049))
    _t1886 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1883, _t1884, _t1885])
    result1051 = _t1886
    record_span!(parser, span_start1050, "Primitive")
    return result1051
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1055 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1887 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1888 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1889 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1890 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1891 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1892 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1893 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1894 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1895 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1896 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1897 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1898 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1899 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1900 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1901 = 1
                                                            else
                                                                _t1901 = -1
                                                            end
                                                            _t1900 = _t1901
                                                        end
                                                        _t1899 = _t1900
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
    prediction1052 = _t1887
    if prediction1052 == 1
        _t1903 = parse_term(parser)
        term1054 = _t1903
        _t1904 = Proto.RelTerm(rel_term_type=OneOf(:term, term1054))
        _t1902 = _t1904
    else
        if prediction1052 == 0
            _t1906 = parse_specialized_value(parser)
            specialized_value1053 = _t1906
            _t1907 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1053))
            _t1905 = _t1907
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1902 = _t1905
    end
    result1056 = _t1902
    record_span!(parser, span_start1055, "RelTerm")
    return result1056
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1058 = span_start(parser)
    consume_literal!(parser, "#")
    _t1908 = parse_raw_value(parser)
    raw_value1057 = _t1908
    result1059 = raw_value1057
    record_span!(parser, span_start1058, "Value")
    return result1059
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1065 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1909 = parse_name(parser)
    name1060 = _t1909
    xs1061 = Proto.RelTerm[]
    cond1062 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1062
        _t1910 = parse_rel_term(parser)
        item1063 = _t1910
        push!(xs1061, item1063)
        cond1062 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1064 = xs1061
    consume_literal!(parser, ")")
    _t1911 = Proto.RelAtom(name=name1060, terms=rel_terms1064)
    result1066 = _t1911
    record_span!(parser, span_start1065, "RelAtom")
    return result1066
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1069 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1912 = parse_term(parser)
    term1067 = _t1912
    _t1913 = parse_term(parser)
    term_31068 = _t1913
    consume_literal!(parser, ")")
    _t1914 = Proto.Cast(input=term1067, result=term_31068)
    result1070 = _t1914
    record_span!(parser, span_start1069, "Cast")
    return result1070
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1071 = Proto.Attribute[]
    cond1072 = match_lookahead_literal(parser, "(", 0)
    while cond1072
        _t1915 = parse_attribute(parser)
        item1073 = _t1915
        push!(xs1071, item1073)
        cond1072 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1074 = xs1071
    consume_literal!(parser, ")")
    return attributes1074
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1080 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1916 = parse_name(parser)
    name1075 = _t1916
    xs1076 = Proto.Value[]
    cond1077 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1077
        _t1917 = parse_raw_value(parser)
        item1078 = _t1917
        push!(xs1076, item1078)
        cond1077 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1079 = xs1076
    consume_literal!(parser, ")")
    _t1918 = Proto.Attribute(name=name1075, args=raw_values1079)
    result1081 = _t1918
    record_span!(parser, span_start1080, "Attribute")
    return result1081
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1088 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1082 = Proto.RelationId[]
    cond1083 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1083
        _t1919 = parse_relation_id(parser)
        item1084 = _t1919
        push!(xs1082, item1084)
        cond1083 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1085 = xs1082
    _t1920 = parse_script(parser)
    script1086 = _t1920
    if match_lookahead_literal(parser, "(", 0)
        _t1922 = parse_attrs(parser)
        _t1921 = _t1922
    else
        _t1921 = nothing
    end
    attrs1087 = _t1921
    consume_literal!(parser, ")")
    _t1923 = Proto.Algorithm(var"#global"=relation_ids1085, body=script1086, attrs=(!isnothing(attrs1087) ? attrs1087 : Proto.Attribute[]))
    result1089 = _t1923
    record_span!(parser, span_start1088, "Algorithm")
    return result1089
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1094 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1090 = Proto.Construct[]
    cond1091 = match_lookahead_literal(parser, "(", 0)
    while cond1091
        _t1924 = parse_construct(parser)
        item1092 = _t1924
        push!(xs1090, item1092)
        cond1091 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1093 = xs1090
    consume_literal!(parser, ")")
    _t1925 = Proto.Script(constructs=constructs1093)
    result1095 = _t1925
    record_span!(parser, span_start1094, "Script")
    return result1095
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1099 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1927 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1928 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1929 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1930 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1931 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
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
            end
            _t1927 = _t1928
        end
        _t1926 = _t1927
    else
        _t1926 = -1
    end
    prediction1096 = _t1926
    if prediction1096 == 1
        _t1934 = parse_instruction(parser)
        instruction1098 = _t1934
        _t1935 = Proto.Construct(construct_type=OneOf(:instruction, instruction1098))
        _t1933 = _t1935
    else
        if prediction1096 == 0
            _t1937 = parse_loop(parser)
            loop1097 = _t1937
            _t1938 = Proto.Construct(construct_type=OneOf(:loop, loop1097))
            _t1936 = _t1938
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1933 = _t1936
    end
    result1100 = _t1933
    record_span!(parser, span_start1099, "Construct")
    return result1100
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1104 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1939 = parse_init(parser)
    init1101 = _t1939
    _t1940 = parse_script(parser)
    script1102 = _t1940
    if match_lookahead_literal(parser, "(", 0)
        _t1942 = parse_attrs(parser)
        _t1941 = _t1942
    else
        _t1941 = nothing
    end
    attrs1103 = _t1941
    consume_literal!(parser, ")")
    _t1943 = Proto.Loop(init=init1101, body=script1102, attrs=(!isnothing(attrs1103) ? attrs1103 : Proto.Attribute[]))
    result1105 = _t1943
    record_span!(parser, span_start1104, "Loop")
    return result1105
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1106 = Proto.Instruction[]
    cond1107 = match_lookahead_literal(parser, "(", 0)
    while cond1107
        _t1944 = parse_instruction(parser)
        item1108 = _t1944
        push!(xs1106, item1108)
        cond1107 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1109 = xs1106
    consume_literal!(parser, ")")
    return instructions1109
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1116 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1946 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1947 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1948 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1949 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1950 = 0
                        else
                            _t1950 = -1
                        end
                        _t1949 = _t1950
                    end
                    _t1948 = _t1949
                end
                _t1947 = _t1948
            end
            _t1946 = _t1947
        end
        _t1945 = _t1946
    else
        _t1945 = -1
    end
    prediction1110 = _t1945
    if prediction1110 == 4
        _t1952 = parse_monus_def(parser)
        monus_def1115 = _t1952
        _t1953 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1115))
        _t1951 = _t1953
    else
        if prediction1110 == 3
            _t1955 = parse_monoid_def(parser)
            monoid_def1114 = _t1955
            _t1956 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1114))
            _t1954 = _t1956
        else
            if prediction1110 == 2
                _t1958 = parse_break(parser)
                break1113 = _t1958
                _t1959 = Proto.Instruction(instr_type=OneOf(:var"#break", break1113))
                _t1957 = _t1959
            else
                if prediction1110 == 1
                    _t1961 = parse_upsert(parser)
                    upsert1112 = _t1961
                    _t1962 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1112))
                    _t1960 = _t1962
                else
                    if prediction1110 == 0
                        _t1964 = parse_assign(parser)
                        assign1111 = _t1964
                        _t1965 = Proto.Instruction(instr_type=OneOf(:assign, assign1111))
                        _t1963 = _t1965
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1960 = _t1963
                end
                _t1957 = _t1960
            end
            _t1954 = _t1957
        end
        _t1951 = _t1954
    end
    result1117 = _t1951
    record_span!(parser, span_start1116, "Instruction")
    return result1117
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1121 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1966 = parse_relation_id(parser)
    relation_id1118 = _t1966
    _t1967 = parse_abstraction(parser)
    abstraction1119 = _t1967
    if match_lookahead_literal(parser, "(", 0)
        _t1969 = parse_attrs(parser)
        _t1968 = _t1969
    else
        _t1968 = nothing
    end
    attrs1120 = _t1968
    consume_literal!(parser, ")")
    _t1970 = Proto.Assign(name=relation_id1118, body=abstraction1119, attrs=(!isnothing(attrs1120) ? attrs1120 : Proto.Attribute[]))
    result1122 = _t1970
    record_span!(parser, span_start1121, "Assign")
    return result1122
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1126 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1971 = parse_relation_id(parser)
    relation_id1123 = _t1971
    _t1972 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1124 = _t1972
    if match_lookahead_literal(parser, "(", 0)
        _t1974 = parse_attrs(parser)
        _t1973 = _t1974
    else
        _t1973 = nothing
    end
    attrs1125 = _t1973
    consume_literal!(parser, ")")
    _t1975 = Proto.Upsert(name=relation_id1123, body=abstraction_with_arity1124[1], attrs=(!isnothing(attrs1125) ? attrs1125 : Proto.Attribute[]), value_arity=abstraction_with_arity1124[2])
    result1127 = _t1975
    record_span!(parser, span_start1126, "Upsert")
    return result1127
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1976 = parse_bindings(parser)
    bindings1128 = _t1976
    _t1977 = parse_formula(parser)
    formula1129 = _t1977
    consume_literal!(parser, ")")
    _t1978 = Proto.Abstraction(vars=vcat(bindings1128[1], !isnothing(bindings1128[2]) ? bindings1128[2] : []), value=formula1129)
    return (_t1978, length(bindings1128[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1133 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1979 = parse_relation_id(parser)
    relation_id1130 = _t1979
    _t1980 = parse_abstraction(parser)
    abstraction1131 = _t1980
    if match_lookahead_literal(parser, "(", 0)
        _t1982 = parse_attrs(parser)
        _t1981 = _t1982
    else
        _t1981 = nothing
    end
    attrs1132 = _t1981
    consume_literal!(parser, ")")
    _t1983 = Proto.Break(name=relation_id1130, body=abstraction1131, attrs=(!isnothing(attrs1132) ? attrs1132 : Proto.Attribute[]))
    result1134 = _t1983
    record_span!(parser, span_start1133, "Break")
    return result1134
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1139 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1984 = parse_monoid(parser)
    monoid1135 = _t1984
    _t1985 = parse_relation_id(parser)
    relation_id1136 = _t1985
    _t1986 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1137 = _t1986
    if match_lookahead_literal(parser, "(", 0)
        _t1988 = parse_attrs(parser)
        _t1987 = _t1988
    else
        _t1987 = nothing
    end
    attrs1138 = _t1987
    consume_literal!(parser, ")")
    _t1989 = Proto.MonoidDef(monoid=monoid1135, name=relation_id1136, body=abstraction_with_arity1137[1], attrs=(!isnothing(attrs1138) ? attrs1138 : Proto.Attribute[]), value_arity=abstraction_with_arity1137[2])
    result1140 = _t1989
    record_span!(parser, span_start1139, "MonoidDef")
    return result1140
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1146 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1991 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1992 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1993 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1994 = 2
                    else
                        _t1994 = -1
                    end
                    _t1993 = _t1994
                end
                _t1992 = _t1993
            end
            _t1991 = _t1992
        end
        _t1990 = _t1991
    else
        _t1990 = -1
    end
    prediction1141 = _t1990
    if prediction1141 == 3
        _t1996 = parse_sum_monoid(parser)
        sum_monoid1145 = _t1996
        _t1997 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1145))
        _t1995 = _t1997
    else
        if prediction1141 == 2
            _t1999 = parse_max_monoid(parser)
            max_monoid1144 = _t1999
            _t2000 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1144))
            _t1998 = _t2000
        else
            if prediction1141 == 1
                _t2002 = parse_min_monoid(parser)
                min_monoid1143 = _t2002
                _t2003 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1143))
                _t2001 = _t2003
            else
                if prediction1141 == 0
                    _t2005 = parse_or_monoid(parser)
                    or_monoid1142 = _t2005
                    _t2006 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1142))
                    _t2004 = _t2006
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t2001 = _t2004
            end
            _t1998 = _t2001
        end
        _t1995 = _t1998
    end
    result1147 = _t1995
    record_span!(parser, span_start1146, "Monoid")
    return result1147
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1148 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t2007 = Proto.OrMonoid()
    result1149 = _t2007
    record_span!(parser, span_start1148, "OrMonoid")
    return result1149
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1151 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t2008 = parse_type(parser)
    type1150 = _t2008
    consume_literal!(parser, ")")
    _t2009 = Proto.MinMonoid(var"#type"=type1150)
    result1152 = _t2009
    record_span!(parser, span_start1151, "MinMonoid")
    return result1152
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1154 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t2010 = parse_type(parser)
    type1153 = _t2010
    consume_literal!(parser, ")")
    _t2011 = Proto.MaxMonoid(var"#type"=type1153)
    result1155 = _t2011
    record_span!(parser, span_start1154, "MaxMonoid")
    return result1155
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1157 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t2012 = parse_type(parser)
    type1156 = _t2012
    consume_literal!(parser, ")")
    _t2013 = Proto.SumMonoid(var"#type"=type1156)
    result1158 = _t2013
    record_span!(parser, span_start1157, "SumMonoid")
    return result1158
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1163 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t2014 = parse_monoid(parser)
    monoid1159 = _t2014
    _t2015 = parse_relation_id(parser)
    relation_id1160 = _t2015
    _t2016 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1161 = _t2016
    if match_lookahead_literal(parser, "(", 0)
        _t2018 = parse_attrs(parser)
        _t2017 = _t2018
    else
        _t2017 = nothing
    end
    attrs1162 = _t2017
    consume_literal!(parser, ")")
    _t2019 = Proto.MonusDef(monoid=monoid1159, name=relation_id1160, body=abstraction_with_arity1161[1], attrs=(!isnothing(attrs1162) ? attrs1162 : Proto.Attribute[]), value_arity=abstraction_with_arity1161[2])
    result1164 = _t2019
    record_span!(parser, span_start1163, "MonusDef")
    return result1164
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1169 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t2020 = parse_relation_id(parser)
    relation_id1165 = _t2020
    _t2021 = parse_abstraction(parser)
    abstraction1166 = _t2021
    _t2022 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1167 = _t2022
    _t2023 = parse_functional_dependency_values(parser)
    functional_dependency_values1168 = _t2023
    consume_literal!(parser, ")")
    _t2024 = Proto.FunctionalDependency(guard=abstraction1166, keys=functional_dependency_keys1167, values=functional_dependency_values1168)
    _t2025 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t2024), name=relation_id1165)
    result1170 = _t2025
    record_span!(parser, span_start1169, "Constraint")
    return result1170
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1171 = Proto.Var[]
    cond1172 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1172
        _t2026 = parse_var(parser)
        item1173 = _t2026
        push!(xs1171, item1173)
        cond1172 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1174 = xs1171
    consume_literal!(parser, ")")
    return vars1174
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1175 = Proto.Var[]
    cond1176 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1176
        _t2027 = parse_var(parser)
        item1177 = _t2027
        push!(xs1175, item1177)
        cond1176 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1178 = xs1175
    consume_literal!(parser, ")")
    return vars1178
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1184 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t2029 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t2030 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t2031 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t2032 = 1
                    else
                        _t2032 = -1
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
    prediction1179 = _t2028
    if prediction1179 == 3
        _t2034 = parse_iceberg_data(parser)
        iceberg_data1183 = _t2034
        _t2035 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1183))
        _t2033 = _t2035
    else
        if prediction1179 == 2
            _t2037 = parse_csv_data(parser)
            csv_data1182 = _t2037
            _t2038 = Proto.Data(data_type=OneOf(:csv_data, csv_data1182))
            _t2036 = _t2038
        else
            if prediction1179 == 1
                _t2040 = parse_betree_relation(parser)
                betree_relation1181 = _t2040
                _t2041 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1181))
                _t2039 = _t2041
            else
                if prediction1179 == 0
                    _t2043 = parse_edb(parser)
                    edb1180 = _t2043
                    _t2044 = Proto.Data(data_type=OneOf(:edb, edb1180))
                    _t2042 = _t2044
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t2039 = _t2042
            end
            _t2036 = _t2039
        end
        _t2033 = _t2036
    end
    result1185 = _t2033
    record_span!(parser, span_start1184, "Data")
    return result1185
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1189 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t2045 = parse_relation_id(parser)
    relation_id1186 = _t2045
    _t2046 = parse_edb_path(parser)
    edb_path1187 = _t2046
    _t2047 = parse_edb_types(parser)
    edb_types1188 = _t2047
    consume_literal!(parser, ")")
    _t2048 = Proto.EDB(target_id=relation_id1186, path=edb_path1187, types=edb_types1188)
    result1190 = _t2048
    record_span!(parser, span_start1189, "EDB")
    return result1190
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1191 = String[]
    cond1192 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1192
        item1193 = consume_terminal!(parser, "STRING")
        push!(xs1191, item1193)
        cond1192 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1194 = xs1191
    consume_literal!(parser, "]")
    return strings1194
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1195 = Proto.var"#Type"[]
    cond1196 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1196
        _t2049 = parse_type(parser)
        item1197 = _t2049
        push!(xs1195, item1197)
        cond1196 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1198 = xs1195
    consume_literal!(parser, "]")
    return types1198
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1201 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t2050 = parse_relation_id(parser)
    relation_id1199 = _t2050
    _t2051 = parse_betree_info(parser)
    betree_info1200 = _t2051
    consume_literal!(parser, ")")
    _t2052 = Proto.BeTreeRelation(name=relation_id1199, relation_info=betree_info1200)
    result1202 = _t2052
    record_span!(parser, span_start1201, "BeTreeRelation")
    return result1202
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1206 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t2053 = parse_betree_info_key_types(parser)
    betree_info_key_types1203 = _t2053
    _t2054 = parse_betree_info_value_types(parser)
    betree_info_value_types1204 = _t2054
    _t2055 = parse_config_dict(parser)
    config_dict1205 = _t2055
    consume_literal!(parser, ")")
    _t2056 = construct_betree_info(parser, betree_info_key_types1203, betree_info_value_types1204, config_dict1205)
    result1207 = _t2056
    record_span!(parser, span_start1206, "BeTreeInfo")
    return result1207
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1208 = Proto.var"#Type"[]
    cond1209 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1209
        _t2057 = parse_type(parser)
        item1210 = _t2057
        push!(xs1208, item1210)
        cond1209 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1211 = xs1208
    consume_literal!(parser, ")")
    return types1211
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1212 = Proto.var"#Type"[]
    cond1213 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1213
        _t2058 = parse_type(parser)
        item1214 = _t2058
        push!(xs1212, item1214)
        cond1213 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1215 = xs1212
    consume_literal!(parser, ")")
    return types1215
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1221 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t2059 = parse_csvlocator(parser)
    csvlocator1216 = _t2059
    _t2060 = parse_csv_config(parser)
    csv_config1217 = _t2060
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t2062 = parse_gnf_columns(parser)
        _t2061 = _t2062
    else
        _t2061 = nothing
    end
    gnf_columns1218 = _t2061
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relations", 1))
        _t2064 = parse_target_relations(parser)
        _t2063 = _t2064
    else
        _t2063 = nothing
    end
    target_relations1219 = _t2063
    _t2065 = parse_csv_asof(parser)
    csv_asof1220 = _t2065
    consume_literal!(parser, ")")
    _t2066 = construct_csv_data(parser, csvlocator1216, csv_config1217, gnf_columns1218, target_relations1219, csv_asof1220)
    result1222 = _t2066
    record_span!(parser, span_start1221, "CSVData")
    return result1222
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1225 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t2068 = parse_csv_locator_paths(parser)
        _t2067 = _t2068
    else
        _t2067 = nothing
    end
    csv_locator_paths1223 = _t2067
    if match_lookahead_literal(parser, "(", 0)
        _t2070 = parse_csv_locator_inline_data(parser)
        _t2069 = _t2070
    else
        _t2069 = nothing
    end
    csv_locator_inline_data1224 = _t2069
    consume_literal!(parser, ")")
    _t2071 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1223) ? csv_locator_paths1223 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1224) ? csv_locator_inline_data1224 : "")))
    result1226 = _t2071
    record_span!(parser, span_start1225, "CSVLocator")
    return result1226
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1227 = String[]
    cond1228 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1228
        item1229 = consume_terminal!(parser, "STRING")
        push!(xs1227, item1229)
        cond1228 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1230 = xs1227
    consume_literal!(parser, ")")
    return strings1230
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1231 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1231
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1234 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t2072 = parse_config_dict(parser)
    config_dict1232 = _t2072
    if match_lookahead_literal(parser, "(", 0)
        _t2074 = parse__storage_integration(parser)
        _t2073 = _t2074
    else
        _t2073 = nothing
    end
    _storage_integration1233 = _t2073
    consume_literal!(parser, ")")
    _t2075 = construct_csv_config(parser, config_dict1232, _storage_integration1233)
    result1235 = _t2075
    record_span!(parser, span_start1234, "CSVConfig")
    return result1235
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t2076 = parse_config_dict(parser)
    config_dict1236 = _t2076
    consume_literal!(parser, ")")
    return config_dict1236
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1237 = Proto.GNFColumn[]
    cond1238 = match_lookahead_literal(parser, "(", 0)
    while cond1238
        _t2077 = parse_gnf_column(parser)
        item1239 = _t2077
        push!(xs1237, item1239)
        cond1238 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1240 = xs1237
    consume_literal!(parser, ")")
    return gnf_columns1240
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1247 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t2078 = parse_gnf_column_path(parser)
    gnf_column_path1241 = _t2078
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t2080 = parse_relation_id(parser)
        _t2079 = _t2080
    else
        _t2079 = nothing
    end
    relation_id1242 = _t2079
    consume_literal!(parser, "[")
    xs1243 = Proto.var"#Type"[]
    cond1244 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1244
        _t2081 = parse_type(parser)
        item1245 = _t2081
        push!(xs1243, item1245)
        cond1244 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1246 = xs1243
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2082 = Proto.GNFColumn(column_path=gnf_column_path1241, target_id=relation_id1242, types=types1246)
    result1248 = _t2082
    record_span!(parser, span_start1247, "GNFColumn")
    return result1248
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t2083 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t2084 = 0
        else
            _t2084 = -1
        end
        _t2083 = _t2084
    end
    prediction1249 = _t2083
    if prediction1249 == 1
        consume_literal!(parser, "[")
        xs1251 = String[]
        cond1252 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1252
            item1253 = consume_terminal!(parser, "STRING")
            push!(xs1251, item1253)
            cond1252 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1254 = xs1251
        consume_literal!(parser, "]")
        _t2085 = strings1254
    else
        if prediction1249 == 0
            string1250 = consume_terminal!(parser, "STRING")
            _t2086 = String[string1250]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t2085 = _t2086
    end
    return _t2085
end

function parse_target_relations(parser::ParserState)::Proto.TargetRelations
    span_start1258 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relations")
    _t2087 = parse_relation_keys(parser)
    relation_keys1255 = _t2087
    _t2088 = parse_relation_body(parser)
    relation_body1256 = _t2088
    if match_lookahead_literal(parser, "(", 0)
        _t2090 = parse_load_errors(parser)
        _t2089 = _t2090
    else
        _t2089 = nothing
    end
    load_errors1257 = _t2089
    consume_literal!(parser, ")")
    _t2091 = construct_relations(parser, relation_keys1255, relation_body1256, load_errors1257)
    result1259 = _t2091
    record_span!(parser, span_start1258, "TargetRelations")
    return result1259
end

function parse_relation_keys(parser::ParserState)::Tuple{Vector{Proto.NamedColumn}, Bool}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "keys", 1)
            if match_lookahead_literal(parser, "synthetic", 2)
                _t2094 = 1
            else
                if match_lookahead_literal(parser, ")", 2)
                    _t2095 = 0
                else
                    if match_lookahead_literal(parser, "(", 2)
                        _t2096 = 0
                    else
                        _t2096 = -1
                    end
                    _t2095 = _t2096
                end
                _t2094 = _t2095
            end
            _t2093 = _t2094
        else
            _t2093 = -1
        end
        _t2092 = _t2093
    else
        _t2092 = -1
    end
    prediction1260 = _t2092
    if prediction1260 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "keys")
        consume_literal!(parser, "synthetic")
        consume_literal!(parser, ")")
        _t2097 = (Proto.NamedColumn[], true,)
    else
        if prediction1260 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "keys")
            xs1261 = Proto.NamedColumn[]
            cond1262 = match_lookahead_literal(parser, "(", 0)
            while cond1262
                _t2099 = parse_named_column(parser)
                item1263 = _t2099
                push!(xs1261, item1263)
                cond1262 = match_lookahead_literal(parser, "(", 0)
            end
            named_columns1264 = xs1261
            consume_literal!(parser, ")")
            _t2098 = (named_columns1264, false,)
        else
            throw(ParseError("Unexpected token in relation_keys" * ": " * string(lookahead(parser, 0))))
        end
        _t2097 = _t2098
    end
    return _t2097
end

function parse_named_column(parser::ParserState)::Proto.NamedColumn
    span_start1267 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1265 = consume_terminal!(parser, "STRING")
    _t2100 = parse_type(parser)
    type1266 = _t2100
    consume_literal!(parser, ")")
    _t2101 = Proto.NamedColumn(name=string1265, var"#type"=type1266)
    result1268 = _t2101
    record_span!(parser, span_start1267, "NamedColumn")
    return result1268
end

function parse_relation_body(parser::ParserState)::Proto.TargetRelations
    span_start1273 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "relation", 1)
            _t2103 = 0
        else
            if match_lookahead_literal(parser, "inserts", 1)
                _t2104 = 1
            else
                _t2104 = 0
            end
            _t2103 = _t2104
        end
        _t2102 = _t2103
    else
        _t2102 = 0
    end
    prediction1269 = _t2102
    if prediction1269 == 1
        _t2106 = parse_cdc_inserts(parser)
        cdc_inserts1271 = _t2106
        _t2107 = parse_cdc_deletes(parser)
        cdc_deletes1272 = _t2107
        _t2108 = construct_cdc_relations(parser, cdc_inserts1271, cdc_deletes1272)
        _t2105 = _t2108
    else
        if prediction1269 == 0
            _t2110 = parse_non_cdc_relations(parser)
            non_cdc_relations1270 = _t2110
            _t2111 = construct_non_cdc_relations(parser, non_cdc_relations1270)
            _t2109 = _t2111
        else
            throw(ParseError("Unexpected token in relation_body" * ": " * string(lookahead(parser, 0))))
        end
        _t2105 = _t2109
    end
    result1274 = _t2105
    record_span!(parser, span_start1273, "TargetRelations")
    return result1274
end

function parse_non_cdc_relations(parser::ParserState)::Vector{Proto.TargetRelation}
    xs1275 = Proto.TargetRelation[]
    cond1276 = (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relation", 1))
    while cond1276
        _t2112 = parse_target_relation(parser)
        item1277 = _t2112
        push!(xs1275, item1277)
        cond1276 = (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relation", 1))
    end
    return xs1275
end

function parse_target_relation(parser::ParserState)::Proto.TargetRelation
    span_start1283 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relation")
    _t2113 = parse_relation_id(parser)
    relation_id1278 = _t2113
    xs1279 = Proto.NamedColumn[]
    cond1280 = match_lookahead_literal(parser, "(", 0)
    while cond1280
        _t2114 = parse_named_column(parser)
        item1281 = _t2114
        push!(xs1279, item1281)
        cond1280 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1282 = xs1279
    consume_literal!(parser, ")")
    _t2115 = Proto.TargetRelation(target_id=relation_id1278, values=named_columns1282)
    result1284 = _t2115
    record_span!(parser, span_start1283, "TargetRelation")
    return result1284
end

function parse_cdc_inserts(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "inserts")
    xs1285 = Proto.TargetRelation[]
    cond1286 = match_lookahead_literal(parser, "(", 0)
    while cond1286
        _t2116 = parse_target_relation(parser)
        item1287 = _t2116
        push!(xs1285, item1287)
        cond1286 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1288 = xs1285
    consume_literal!(parser, ")")
    return target_relations1288
end

function parse_cdc_deletes(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "deletes")
    xs1289 = Proto.TargetRelation[]
    cond1290 = match_lookahead_literal(parser, "(", 0)
    while cond1290
        _t2117 = parse_target_relation(parser)
        item1291 = _t2117
        push!(xs1289, item1291)
        cond1290 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1292 = xs1289
    consume_literal!(parser, ")")
    return target_relations1292
end

function parse_load_errors(parser::ParserState)::Proto.RelationId
    span_start1294 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "load_errors")
    _t2118 = parse_relation_id(parser)
    relation_id1293 = _t2118
    consume_literal!(parser, ")")
    result1295 = relation_id1293
    record_span!(parser, span_start1294, "RelationId")
    return result1295
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1296 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1296
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1304 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t2119 = parse_iceberg_locator(parser)
    iceberg_locator1297 = _t2119
    _t2120 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1298 = _t2120
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t2122 = parse_gnf_columns(parser)
        _t2121 = _t2122
    else
        _t2121 = nothing
    end
    gnf_columns1299 = _t2121
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relations", 1))
        _t2124 = parse_target_relations(parser)
        _t2123 = _t2124
    else
        _t2123 = nothing
    end
    target_relations1300 = _t2123
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2126 = parse_iceberg_from_snapshot(parser)
        _t2125 = _t2126
    else
        _t2125 = nothing
    end
    iceberg_from_snapshot1301 = _t2125
    if match_lookahead_literal(parser, "(", 0)
        _t2128 = parse_iceberg_to_snapshot(parser)
        _t2127 = _t2128
    else
        _t2127 = nothing
    end
    iceberg_to_snapshot1302 = _t2127
    _t2129 = parse_boolean_value(parser)
    boolean_value1303 = _t2129
    consume_literal!(parser, ")")
    _t2130 = construct_iceberg_data(parser, iceberg_locator1297, iceberg_catalog_config1298, gnf_columns1299, target_relations1300, iceberg_from_snapshot1301, iceberg_to_snapshot1302, boolean_value1303)
    result1305 = _t2130
    record_span!(parser, span_start1304, "IcebergData")
    return result1305
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1309 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2131 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1306 = _t2131
    _t2132 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1307 = _t2132
    _t2133 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1308 = _t2133
    consume_literal!(parser, ")")
    _t2134 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1306, namespace=iceberg_locator_namespace1307, warehouse=iceberg_locator_warehouse1308)
    result1310 = _t2134
    record_span!(parser, span_start1309, "IcebergLocator")
    return result1310
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1311 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1311
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1312 = String[]
    cond1313 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1313
        item1314 = consume_terminal!(parser, "STRING")
        push!(xs1312, item1314)
        cond1313 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1315 = xs1312
    consume_literal!(parser, ")")
    return strings1315
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1316 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1316
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1321 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2135 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1317 = _t2135
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2137 = parse_iceberg_catalog_config_scope(parser)
        _t2136 = _t2137
    else
        _t2136 = nothing
    end
    iceberg_catalog_config_scope1318 = _t2136
    _t2138 = parse_iceberg_properties(parser)
    iceberg_properties1319 = _t2138
    _t2139 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1320 = _t2139
    consume_literal!(parser, ")")
    _t2140 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1317, iceberg_catalog_config_scope1318, iceberg_properties1319, iceberg_auth_properties1320)
    result1322 = _t2140
    record_span!(parser, span_start1321, "IcebergCatalogConfig")
    return result1322
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1323 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1323
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1324 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1324
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1325 = Tuple{String, String}[]
    cond1326 = match_lookahead_literal(parser, "(", 0)
    while cond1326
        _t2141 = parse_iceberg_property_entry(parser)
        item1327 = _t2141
        push!(xs1325, item1327)
        cond1326 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1328 = xs1325
    consume_literal!(parser, ")")
    return iceberg_property_entrys1328
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1329 = consume_terminal!(parser, "STRING")
    string_31330 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1329, string_31330,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1331 = Tuple{String, String}[]
    cond1332 = match_lookahead_literal(parser, "(", 0)
    while cond1332
        _t2142 = parse_iceberg_masked_property_entry(parser)
        item1333 = _t2142
        push!(xs1331, item1333)
        cond1332 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1334 = xs1331
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1334
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1335 = consume_terminal!(parser, "STRING")
    string_31336 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1335, string_31336,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1337 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1337
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1338 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1338
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1340 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2143 = parse_fragment_id(parser)
    fragment_id1339 = _t2143
    consume_literal!(parser, ")")
    _t2144 = Proto.Undefine(fragment_id=fragment_id1339)
    result1341 = _t2144
    record_span!(parser, span_start1340, "Undefine")
    return result1341
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1346 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1342 = Proto.RelationId[]
    cond1343 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1343
        _t2145 = parse_relation_id(parser)
        item1344 = _t2145
        push!(xs1342, item1344)
        cond1343 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1345 = xs1342
    consume_literal!(parser, ")")
    _t2146 = Proto.Context(relations=relation_ids1345)
    result1347 = _t2146
    record_span!(parser, span_start1346, "Context")
    return result1347
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1353 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2147 = parse_edb_path(parser)
    edb_path1348 = _t2147
    xs1349 = Proto.SnapshotMapping[]
    cond1350 = match_lookahead_literal(parser, "[", 0)
    while cond1350
        _t2148 = parse_snapshot_mapping(parser)
        item1351 = _t2148
        push!(xs1349, item1351)
        cond1350 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1352 = xs1349
    consume_literal!(parser, ")")
    _t2149 = Proto.Snapshot(mappings=snapshot_mappings1352, prefix=edb_path1348)
    result1354 = _t2149
    record_span!(parser, span_start1353, "Snapshot")
    return result1354
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1357 = span_start(parser)
    _t2150 = parse_edb_path(parser)
    edb_path1355 = _t2150
    _t2151 = parse_relation_id(parser)
    relation_id1356 = _t2151
    _t2152 = Proto.SnapshotMapping(destination_path=edb_path1355, source_relation=relation_id1356)
    result1358 = _t2152
    record_span!(parser, span_start1357, "SnapshotMapping")
    return result1358
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1359 = Proto.Read[]
    cond1360 = match_lookahead_literal(parser, "(", 0)
    while cond1360
        _t2153 = parse_read(parser)
        item1361 = _t2153
        push!(xs1359, item1361)
        cond1360 = match_lookahead_literal(parser, "(", 0)
    end
    reads1362 = xs1359
    consume_literal!(parser, ")")
    return reads1362
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1369 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2155 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2156 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2157 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2158 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2159 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2160 = 3
                            else
                                _t2160 = -1
                            end
                            _t2159 = _t2160
                        end
                        _t2158 = _t2159
                    end
                    _t2157 = _t2158
                end
                _t2156 = _t2157
            end
            _t2155 = _t2156
        end
        _t2154 = _t2155
    else
        _t2154 = -1
    end
    prediction1363 = _t2154
    if prediction1363 == 4
        _t2162 = parse_export(parser)
        export1368 = _t2162
        _t2163 = Proto.Read(read_type=OneOf(:var"#export", export1368))
        _t2161 = _t2163
    else
        if prediction1363 == 3
            _t2165 = parse_abort(parser)
            abort1367 = _t2165
            _t2166 = Proto.Read(read_type=OneOf(:abort, abort1367))
            _t2164 = _t2166
        else
            if prediction1363 == 2
                _t2168 = parse_what_if(parser)
                what_if1366 = _t2168
                _t2169 = Proto.Read(read_type=OneOf(:what_if, what_if1366))
                _t2167 = _t2169
            else
                if prediction1363 == 1
                    _t2171 = parse_output(parser)
                    output1365 = _t2171
                    _t2172 = Proto.Read(read_type=OneOf(:output, output1365))
                    _t2170 = _t2172
                else
                    if prediction1363 == 0
                        _t2174 = parse_demand(parser)
                        demand1364 = _t2174
                        _t2175 = Proto.Read(read_type=OneOf(:demand, demand1364))
                        _t2173 = _t2175
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2170 = _t2173
                end
                _t2167 = _t2170
            end
            _t2164 = _t2167
        end
        _t2161 = _t2164
    end
    result1370 = _t2161
    record_span!(parser, span_start1369, "Read")
    return result1370
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1372 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2176 = parse_relation_id(parser)
    relation_id1371 = _t2176
    consume_literal!(parser, ")")
    _t2177 = Proto.Demand(relation_id=relation_id1371)
    result1373 = _t2177
    record_span!(parser, span_start1372, "Demand")
    return result1373
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1376 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2178 = parse_name(parser)
    name1374 = _t2178
    _t2179 = parse_relation_id(parser)
    relation_id1375 = _t2179
    consume_literal!(parser, ")")
    _t2180 = Proto.Output(name=name1374, relation_id=relation_id1375)
    result1377 = _t2180
    record_span!(parser, span_start1376, "Output")
    return result1377
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1380 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2181 = parse_name(parser)
    name1378 = _t2181
    _t2182 = parse_epoch(parser)
    epoch1379 = _t2182
    consume_literal!(parser, ")")
    _t2183 = Proto.WhatIf(branch=name1378, epoch=epoch1379)
    result1381 = _t2183
    record_span!(parser, span_start1380, "WhatIf")
    return result1381
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1384 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2185 = parse_name(parser)
        _t2184 = _t2185
    else
        _t2184 = nothing
    end
    name1382 = _t2184
    _t2186 = parse_relation_id(parser)
    relation_id1383 = _t2186
    consume_literal!(parser, ")")
    _t2187 = Proto.Abort(name=(!isnothing(name1382) ? name1382 : "abort"), relation_id=relation_id1383)
    result1385 = _t2187
    record_span!(parser, span_start1384, "Abort")
    return result1385
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1389 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2189 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2190 = 0
            else
                _t2190 = -1
            end
            _t2189 = _t2190
        end
        _t2188 = _t2189
    else
        _t2188 = -1
    end
    prediction1386 = _t2188
    if prediction1386 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2192 = parse_export_iceberg_config(parser)
        export_iceberg_config1388 = _t2192
        consume_literal!(parser, ")")
        _t2193 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1388))
        _t2191 = _t2193
    else
        if prediction1386 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2195 = parse_export_csv_config(parser)
            export_csv_config1387 = _t2195
            consume_literal!(parser, ")")
            _t2196 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1387))
            _t2194 = _t2196
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2191 = _t2194
    end
    result1390 = _t2191
    record_span!(parser, span_start1389, "Export")
    return result1390
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1398 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2198 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2199 = 1
            else
                _t2199 = -1
            end
            _t2198 = _t2199
        end
        _t2197 = _t2198
    else
        _t2197 = -1
    end
    prediction1391 = _t2197
    if prediction1391 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2201 = parse_export_csv_path(parser)
        export_csv_path1395 = _t2201
        _t2202 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1396 = _t2202
        _t2203 = parse_config_dict(parser)
        config_dict1397 = _t2203
        consume_literal!(parser, ")")
        _t2204 = construct_export_csv_config(parser, export_csv_path1395, export_csv_columns_list1396, config_dict1397)
        _t2200 = _t2204
    else
        if prediction1391 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2206 = parse_export_csv_output_location(parser)
            export_csv_output_location1392 = _t2206
            _t2207 = parse_export_csv_source(parser)
            export_csv_source1393 = _t2207
            _t2208 = parse_csv_config(parser)
            csv_config1394 = _t2208
            consume_literal!(parser, ")")
            _t2209 = construct_export_csv_config_with_location(parser, export_csv_output_location1392, export_csv_source1393, csv_config1394)
            _t2205 = _t2209
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2200 = _t2205
    end
    result1399 = _t2200
    record_span!(parser, span_start1398, "ExportCSVConfig")
    return result1399
end

function parse_export_csv_output_location(parser::ParserState)::Tuple{String, String}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "transaction_output_name", 1)
            _t2211 = 1
        else
            if match_lookahead_literal(parser, "path", 1)
                _t2212 = 0
            else
                _t2212 = -1
            end
            _t2211 = _t2212
        end
        _t2210 = _t2211
    else
        _t2210 = -1
    end
    prediction1400 = _t2210
    if prediction1400 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "transaction_output_name")
        _t2214 = parse_name(parser)
        name1402 = _t2214
        consume_literal!(parser, ")")
        _t2213 = ("", name1402,)
    else
        if prediction1400 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "path")
            string1401 = consume_terminal!(parser, "STRING")
            consume_literal!(parser, ")")
            _t2215 = (string1401, "",)
        else
            throw(ParseError("Unexpected token in export_csv_output_location" * ": " * string(lookahead(parser, 0))))
        end
        _t2213 = _t2215
    end
    return _t2213
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1409 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2217 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2218 = 0
            else
                _t2218 = -1
            end
            _t2217 = _t2218
        end
        _t2216 = _t2217
    else
        _t2216 = -1
    end
    prediction1403 = _t2216
    if prediction1403 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2220 = parse_relation_id(parser)
        relation_id1408 = _t2220
        consume_literal!(parser, ")")
        _t2221 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1408))
        _t2219 = _t2221
    else
        if prediction1403 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1404 = Proto.ExportCSVColumn[]
            cond1405 = match_lookahead_literal(parser, "(", 0)
            while cond1405
                _t2223 = parse_export_csv_column(parser)
                item1406 = _t2223
                push!(xs1404, item1406)
                cond1405 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1407 = xs1404
            consume_literal!(parser, ")")
            _t2224 = Proto.ExportCSVColumns(columns=export_csv_columns1407)
            _t2225 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2224))
            _t2222 = _t2225
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2219 = _t2222
    end
    result1410 = _t2219
    record_span!(parser, span_start1409, "ExportCSVSource")
    return result1410
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1413 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1411 = consume_terminal!(parser, "STRING")
    _t2226 = parse_relation_id(parser)
    relation_id1412 = _t2226
    consume_literal!(parser, ")")
    _t2227 = Proto.ExportCSVColumn(column_name=string1411, column_data=relation_id1412)
    result1414 = _t2227
    record_span!(parser, span_start1413, "ExportCSVColumn")
    return result1414
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1415 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1415
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1416 = Proto.ExportCSVColumn[]
    cond1417 = match_lookahead_literal(parser, "(", 0)
    while cond1417
        _t2228 = parse_export_csv_column(parser)
        item1418 = _t2228
        push!(xs1416, item1418)
        cond1417 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1419 = xs1416
    consume_literal!(parser, ")")
    return export_csv_columns1419
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1425 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2229 = parse_iceberg_locator(parser)
    iceberg_locator1420 = _t2229
    _t2230 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1421 = _t2230
    _t2231 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1422 = _t2231
    _t2232 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1423 = _t2232
    if match_lookahead_literal(parser, "{", 0)
        _t2234 = parse_config_dict(parser)
        _t2233 = _t2234
    else
        _t2233 = nothing
    end
    config_dict1424 = _t2233
    consume_literal!(parser, ")")
    _t2235 = construct_export_iceberg_config_full(parser, iceberg_locator1420, iceberg_catalog_config1421, export_iceberg_table_def1422, iceberg_table_properties1423, config_dict1424)
    result1426 = _t2235
    record_span!(parser, span_start1425, "ExportIcebergConfig")
    return result1426
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1428 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2236 = parse_relation_id(parser)
    relation_id1427 = _t2236
    consume_literal!(parser, ")")
    result1429 = relation_id1427
    record_span!(parser, span_start1428, "RelationId")
    return result1429
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1430 = Tuple{String, String}[]
    cond1431 = match_lookahead_literal(parser, "(", 0)
    while cond1431
        _t2237 = parse_iceberg_property_entry(parser)
        item1432 = _t2237
        push!(xs1430, item1432)
        cond1431 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1433 = xs1430
    consume_literal!(parser, ")")
    return iceberg_property_entrys1433
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
