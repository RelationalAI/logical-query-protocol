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
        _t2219 = nothing
    end
    if _has_proto_field(value, Symbol("int32_value"))
        return _get_oneof_field(value, :int32_value)
    else
        _t2220 = nothing
    end
    throw(ParseError("expected an int32 value (e.g. `1i32`) for this config field"))
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2221 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2222 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2223 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2224 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2225 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2226 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2227 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2228 = nothing
    end
    return nothing
end

function construct_non_cdc_relations(parser::ParserState, targets::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2229 = Proto.PlainTargets(targets=targets)
    _t2230 = Proto.TargetRelations(body=OneOf(:plain, _t2229), keys=Proto.NamedColumn[])
    return _t2230
end

function construct_cdc_relations(parser::ParserState, inserts::Vector{Proto.TargetRelation}, deletes::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2231 = Proto.CDCTargets(inserts=inserts, deletes=deletes)
    _t2232 = Proto.TargetRelations(body=OneOf(:cdc, _t2231), keys=Proto.NamedColumn[])
    return _t2232
end

function construct_relations(parser::ParserState, keys::Tuple{Vector{Proto.NamedColumn}, Bool}, body::Proto.TargetRelations, load_errors_opt::Union{Nothing, Proto.RelationId})::Proto.TargetRelations
    if _has_proto_field(body, Symbol("plain"))
        _t2234 = Proto.TargetRelations(body=OneOf(:plain, _get_oneof_field(body, :plain)), keys=keys[1], synthetic_key=keys[2], load_errors=load_errors_opt)
        return _t2234
    else
        _t2233 = nothing
    end
    _t2235 = Proto.TargetRelations(body=OneOf(:cdc, _get_oneof_field(body, :cdc)), keys=keys[1], synthetic_key=keys[2], load_errors=load_errors_opt)
    return _t2235
end

function construct_csv_data(parser::ParserState, locator::Proto.CSVLocator, config::Proto.CSVConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, relations_opt::Union{Nothing, Proto.TargetRelations}, asof::String)::Proto.CSVData
    _t2236 = Proto.CSVData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), asof=asof, relations=relations_opt)
    return _t2236
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2237 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2237
    _t2238 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2238
    _t2239 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2239
    _t2240 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2240
    _t2241 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2241
    _t2242 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2242
    _t2243 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2243
    _t2244 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2244
    _t2245 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2245
    _t2246 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2246
    _t2247 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2247
    _t2248 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2248
    _t2249 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2249
    _t2250 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2250
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2251 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2252 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2253 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2254 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2255 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2256 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2257 = Proto.StorageIntegration(provider=_t2252, azure_sas_token=_t2253, s3_region=_t2254, s3_access_key_id=_t2255, s3_secret_access_key=_t2256)
    return _t2257
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2258 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2258
    _t2259 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2259
    _t2260 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2260
    _t2261 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2261
    _t2262 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2262
    _t2263 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2263
    _t2264 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2264
    _t2265 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2265
    _t2266 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2266
    _t2267 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2267
    _t2268 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2268
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2269 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2269
    _t2270 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2270
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
    _t2271 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2271
    _t2272 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2272
    config_values_pairs = Tuple{String, Proto.Value}[]
    for pair in config_dict
        if (pair[1] != "semantics_version" && pair[1] != "ivm.maintenance_level")
            push!(config_values_pairs, pair)
        end
    end
    configuration_values = Dict(config_values_pairs)
    _t2273 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config, configuration_values=configuration_values)
    return _t2273
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2274 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2274
    _t2275 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2275
    _t2276 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2276
    _t2277 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2277
    _t2278 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2278
    _t2279 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2279
    _t2280 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2280
    _t2281 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2281
end

function construct_export_csv_config_with_location(parser::ParserState, location::Tuple{String, String}, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2282 = Proto.ExportCSVConfig(path=location[1], transaction_output_name=location[2], csv_source=csv_source, csv_config=csv_config)
    return _t2282
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2283 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2283
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2284 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2284
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2285 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2285
    _t2286 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2286
    _t2287 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2287
    table_props = Dict(table_property_pairs)
    _t2288 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2288
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start718 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1425 = parse_configure(parser)
        _t1424 = _t1425
    else
        _t1424 = nothing
    end
    configure712 = _t1424
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1427 = parse_sync(parser)
        _t1426 = _t1427
    else
        _t1426 = nothing
    end
    sync713 = _t1426
    xs714 = Proto.Epoch[]
    cond715 = match_lookahead_literal(parser, "(", 0)
    while cond715
        _t1428 = parse_epoch(parser)
        item716 = _t1428
        push!(xs714, item716)
        cond715 = match_lookahead_literal(parser, "(", 0)
    end
    epochs717 = xs714
    consume_literal!(parser, ")")
    _t1429 = default_configure(parser)
    _t1430 = Proto.Transaction(epochs=epochs717, configure=(!isnothing(configure712) ? configure712 : _t1429), sync=sync713)
    result719 = _t1430
    record_span!(parser, span_start718, "Transaction")
    return result719
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start721 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1431 = parse_config_dict(parser)
    config_dict720 = _t1431
    consume_literal!(parser, ")")
    _t1432 = construct_configure(parser, config_dict720)
    result722 = _t1432
    record_span!(parser, span_start721, "Configure")
    return result722
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs723 = Tuple{String, Proto.Value}[]
    cond724 = match_lookahead_literal(parser, ":", 0)
    while cond724
        _t1433 = parse_config_key_value(parser)
        item725 = _t1433
        push!(xs723, item725)
        cond724 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values726 = xs723
    consume_literal!(parser, "}")
    return config_key_values726
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol727 = consume_terminal!(parser, "SYMBOL")
    _t1434 = parse_raw_value(parser)
    raw_value728 = _t1434
    return (symbol727, raw_value728,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start742 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1435 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1436 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1437 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1439 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1440 = 0
                        else
                            _t1440 = -1
                        end
                        _t1439 = _t1440
                    end
                    _t1438 = _t1439
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1441 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1442 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1443 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1444 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1445 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1446 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1447 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1448 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1449 = 10
                                                    else
                                                        _t1449 = -1
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
                            end
                            _t1442 = _t1443
                        end
                        _t1441 = _t1442
                    end
                    _t1438 = _t1441
                end
                _t1437 = _t1438
            end
            _t1436 = _t1437
        end
        _t1435 = _t1436
    end
    prediction729 = _t1435
    if prediction729 == 12
        _t1451 = parse_boolean_value(parser)
        boolean_value741 = _t1451
        _t1452 = Proto.Value(value=OneOf(:boolean_value, boolean_value741))
        _t1450 = _t1452
    else
        if prediction729 == 11
            consume_literal!(parser, "missing")
            _t1454 = Proto.MissingValue()
            _t1455 = Proto.Value(value=OneOf(:missing_value, _t1454))
            _t1453 = _t1455
        else
            if prediction729 == 10
                decimal740 = consume_terminal!(parser, "DECIMAL")
                _t1457 = Proto.Value(value=OneOf(:decimal_value, decimal740))
                _t1456 = _t1457
            else
                if prediction729 == 9
                    int128739 = consume_terminal!(parser, "INT128")
                    _t1459 = Proto.Value(value=OneOf(:int128_value, int128739))
                    _t1458 = _t1459
                else
                    if prediction729 == 8
                        uint128738 = consume_terminal!(parser, "UINT128")
                        _t1461 = Proto.Value(value=OneOf(:uint128_value, uint128738))
                        _t1460 = _t1461
                    else
                        if prediction729 == 7
                            uint32737 = consume_terminal!(parser, "UINT32")
                            _t1463 = Proto.Value(value=OneOf(:uint32_value, uint32737))
                            _t1462 = _t1463
                        else
                            if prediction729 == 6
                                float736 = consume_terminal!(parser, "FLOAT")
                                _t1465 = Proto.Value(value=OneOf(:float_value, float736))
                                _t1464 = _t1465
                            else
                                if prediction729 == 5
                                    float32735 = consume_terminal!(parser, "FLOAT32")
                                    _t1467 = Proto.Value(value=OneOf(:float32_value, float32735))
                                    _t1466 = _t1467
                                else
                                    if prediction729 == 4
                                        int734 = consume_terminal!(parser, "INT")
                                        _t1469 = Proto.Value(value=OneOf(:int_value, int734))
                                        _t1468 = _t1469
                                    else
                                        if prediction729 == 3
                                            int32733 = consume_terminal!(parser, "INT32")
                                            _t1471 = Proto.Value(value=OneOf(:int32_value, int32733))
                                            _t1470 = _t1471
                                        else
                                            if prediction729 == 2
                                                string732 = consume_terminal!(parser, "STRING")
                                                _t1473 = Proto.Value(value=OneOf(:string_value, string732))
                                                _t1472 = _t1473
                                            else
                                                if prediction729 == 1
                                                    _t1475 = parse_raw_datetime(parser)
                                                    raw_datetime731 = _t1475
                                                    _t1476 = Proto.Value(value=OneOf(:datetime_value, raw_datetime731))
                                                    _t1474 = _t1476
                                                else
                                                    if prediction729 == 0
                                                        _t1478 = parse_raw_date(parser)
                                                        raw_date730 = _t1478
                                                        _t1479 = Proto.Value(value=OneOf(:date_value, raw_date730))
                                                        _t1477 = _t1479
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1474 = _t1477
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
                            _t1462 = _t1464
                        end
                        _t1460 = _t1462
                    end
                    _t1458 = _t1460
                end
                _t1456 = _t1458
            end
            _t1453 = _t1456
        end
        _t1450 = _t1453
    end
    result743 = _t1450
    record_span!(parser, span_start742, "Value")
    return result743
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start747 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int744 = consume_terminal!(parser, "INT")
    int_3745 = consume_terminal!(parser, "INT")
    int_4746 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1480 = Proto.DateValue(year=Int32(int744), month=Int32(int_3745), day=Int32(int_4746))
    result748 = _t1480
    record_span!(parser, span_start747, "DateValue")
    return result748
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start756 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int749 = consume_terminal!(parser, "INT")
    int_3750 = consume_terminal!(parser, "INT")
    int_4751 = consume_terminal!(parser, "INT")
    int_5752 = consume_terminal!(parser, "INT")
    int_6753 = consume_terminal!(parser, "INT")
    int_7754 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1481 = consume_terminal!(parser, "INT")
    else
        _t1481 = nothing
    end
    int_8755 = _t1481
    consume_literal!(parser, ")")
    _t1482 = Proto.DateTimeValue(year=Int32(int749), month=Int32(int_3750), day=Int32(int_4751), hour=Int32(int_5752), minute=Int32(int_6753), second=Int32(int_7754), microsecond=Int32((!isnothing(int_8755) ? int_8755 : 0)))
    result757 = _t1482
    record_span!(parser, span_start756, "DateTimeValue")
    return result757
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1483 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1484 = 1
        else
            _t1484 = -1
        end
        _t1483 = _t1484
    end
    prediction758 = _t1483
    if prediction758 == 1
        consume_literal!(parser, "false")
        _t1485 = false
    else
        if prediction758 == 0
            consume_literal!(parser, "true")
            _t1486 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1485 = _t1486
    end
    return _t1485
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start763 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs759 = Proto.FragmentId[]
    cond760 = match_lookahead_literal(parser, ":", 0)
    while cond760
        _t1487 = parse_fragment_id(parser)
        item761 = _t1487
        push!(xs759, item761)
        cond760 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids762 = xs759
    consume_literal!(parser, ")")
    _t1488 = Proto.Sync(fragments=fragment_ids762)
    result764 = _t1488
    record_span!(parser, span_start763, "Sync")
    return result764
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start766 = span_start(parser)
    consume_literal!(parser, ":")
    symbol765 = consume_terminal!(parser, "SYMBOL")
    result767 = Proto.FragmentId(Vector{UInt8}(symbol765))
    record_span!(parser, span_start766, "FragmentId")
    return result767
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start770 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1490 = parse_epoch_writes(parser)
        _t1489 = _t1490
    else
        _t1489 = nothing
    end
    epoch_writes768 = _t1489
    if match_lookahead_literal(parser, "(", 0)
        _t1492 = parse_epoch_reads(parser)
        _t1491 = _t1492
    else
        _t1491 = nothing
    end
    epoch_reads769 = _t1491
    consume_literal!(parser, ")")
    _t1493 = Proto.Epoch(writes=(!isnothing(epoch_writes768) ? epoch_writes768 : Proto.Write[]), reads=(!isnothing(epoch_reads769) ? epoch_reads769 : Proto.Read[]))
    result771 = _t1493
    record_span!(parser, span_start770, "Epoch")
    return result771
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs772 = Proto.Write[]
    cond773 = match_lookahead_literal(parser, "(", 0)
    while cond773
        _t1494 = parse_write(parser)
        item774 = _t1494
        push!(xs772, item774)
        cond773 = match_lookahead_literal(parser, "(", 0)
    end
    writes775 = xs772
    consume_literal!(parser, ")")
    return writes775
end

function parse_write(parser::ParserState)::Proto.Write
    span_start781 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1496 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1497 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1498 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1499 = 2
                    else
                        _t1499 = -1
                    end
                    _t1498 = _t1499
                end
                _t1497 = _t1498
            end
            _t1496 = _t1497
        end
        _t1495 = _t1496
    else
        _t1495 = -1
    end
    prediction776 = _t1495
    if prediction776 == 3
        _t1501 = parse_snapshot(parser)
        snapshot780 = _t1501
        _t1502 = Proto.Write(write_type=OneOf(:snapshot, snapshot780))
        _t1500 = _t1502
    else
        if prediction776 == 2
            _t1504 = parse_context(parser)
            context779 = _t1504
            _t1505 = Proto.Write(write_type=OneOf(:context, context779))
            _t1503 = _t1505
        else
            if prediction776 == 1
                _t1507 = parse_undefine(parser)
                undefine778 = _t1507
                _t1508 = Proto.Write(write_type=OneOf(:undefine, undefine778))
                _t1506 = _t1508
            else
                if prediction776 == 0
                    _t1510 = parse_define(parser)
                    define777 = _t1510
                    _t1511 = Proto.Write(write_type=OneOf(:define, define777))
                    _t1509 = _t1511
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1506 = _t1509
            end
            _t1503 = _t1506
        end
        _t1500 = _t1503
    end
    result782 = _t1500
    record_span!(parser, span_start781, "Write")
    return result782
end

function parse_define(parser::ParserState)::Proto.Define
    span_start784 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1512 = parse_fragment(parser)
    fragment783 = _t1512
    consume_literal!(parser, ")")
    _t1513 = Proto.Define(fragment=fragment783)
    result785 = _t1513
    record_span!(parser, span_start784, "Define")
    return result785
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start791 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1514 = parse_new_fragment_id(parser)
    new_fragment_id786 = _t1514
    xs787 = Proto.Declaration[]
    cond788 = match_lookahead_literal(parser, "(", 0)
    while cond788
        _t1515 = parse_declaration(parser)
        item789 = _t1515
        push!(xs787, item789)
        cond788 = match_lookahead_literal(parser, "(", 0)
    end
    declarations790 = xs787
    consume_literal!(parser, ")")
    result792 = construct_fragment(parser, new_fragment_id786, declarations790)
    record_span!(parser, span_start791, "Fragment")
    return result792
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start794 = span_start(parser)
    _t1516 = parse_fragment_id(parser)
    fragment_id793 = _t1516
    start_fragment!(parser, fragment_id793)
    result795 = fragment_id793
    record_span!(parser, span_start794, "FragmentId")
    return result795
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start801 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1518 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1519 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1520 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1521 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1522 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1523 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1524 = 1
                                else
                                    _t1524 = -1
                                end
                                _t1523 = _t1524
                            end
                            _t1522 = _t1523
                        end
                        _t1521 = _t1522
                    end
                    _t1520 = _t1521
                end
                _t1519 = _t1520
            end
            _t1518 = _t1519
        end
        _t1517 = _t1518
    else
        _t1517 = -1
    end
    prediction796 = _t1517
    if prediction796 == 3
        _t1526 = parse_data(parser)
        data800 = _t1526
        _t1527 = Proto.Declaration(declaration_type=OneOf(:data, data800))
        _t1525 = _t1527
    else
        if prediction796 == 2
            _t1529 = parse_constraint(parser)
            constraint799 = _t1529
            _t1530 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint799))
            _t1528 = _t1530
        else
            if prediction796 == 1
                _t1532 = parse_algorithm(parser)
                algorithm798 = _t1532
                _t1533 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm798))
                _t1531 = _t1533
            else
                if prediction796 == 0
                    _t1535 = parse_def(parser)
                    def797 = _t1535
                    _t1536 = Proto.Declaration(declaration_type=OneOf(:def, def797))
                    _t1534 = _t1536
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1531 = _t1534
            end
            _t1528 = _t1531
        end
        _t1525 = _t1528
    end
    result802 = _t1525
    record_span!(parser, span_start801, "Declaration")
    return result802
end

function parse_def(parser::ParserState)::Proto.Def
    span_start806 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1537 = parse_relation_id(parser)
    relation_id803 = _t1537
    _t1538 = parse_abstraction(parser)
    abstraction804 = _t1538
    if match_lookahead_literal(parser, "(", 0)
        _t1540 = parse_attrs(parser)
        _t1539 = _t1540
    else
        _t1539 = nothing
    end
    attrs805 = _t1539
    consume_literal!(parser, ")")
    _t1541 = Proto.Def(name=relation_id803, body=abstraction804, attrs=(!isnothing(attrs805) ? attrs805 : Proto.Attribute[]))
    result807 = _t1541
    record_span!(parser, span_start806, "Def")
    return result807
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start811 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1542 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1543 = 1
        else
            _t1543 = -1
        end
        _t1542 = _t1543
    end
    prediction808 = _t1542
    if prediction808 == 1
        uint128810 = consume_terminal!(parser, "UINT128")
        _t1544 = Proto.RelationId(uint128810.low, uint128810.high)
    else
        if prediction808 == 0
            consume_literal!(parser, ":")
            symbol809 = consume_terminal!(parser, "SYMBOL")
            _t1545 = relation_id_from_string(parser, symbol809)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1544 = _t1545
    end
    result812 = _t1544
    record_span!(parser, span_start811, "RelationId")
    return result812
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start815 = span_start(parser)
    consume_literal!(parser, "(")
    _t1546 = parse_bindings(parser)
    bindings813 = _t1546
    _t1547 = parse_formula(parser)
    formula814 = _t1547
    consume_literal!(parser, ")")
    _t1548 = Proto.Abstraction(vars=vcat(bindings813[1], !isnothing(bindings813[2]) ? bindings813[2] : []), value=formula814)
    result816 = _t1548
    record_span!(parser, span_start815, "Abstraction")
    return result816
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs817 = Proto.Binding[]
    cond818 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond818
        _t1549 = parse_binding(parser)
        item819 = _t1549
        push!(xs817, item819)
        cond818 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings820 = xs817
    if match_lookahead_literal(parser, "|", 0)
        _t1551 = parse_value_bindings(parser)
        _t1550 = _t1551
    else
        _t1550 = nothing
    end
    value_bindings821 = _t1550
    consume_literal!(parser, "]")
    return (bindings820, (!isnothing(value_bindings821) ? value_bindings821 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start824 = span_start(parser)
    symbol822 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1552 = parse_type(parser)
    type823 = _t1552
    _t1553 = Proto.Var(name=symbol822)
    _t1554 = Proto.Binding(var=_t1553, var"#type"=type823)
    result825 = _t1554
    record_span!(parser, span_start824, "Binding")
    return result825
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start841 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1555 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1556 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1557 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1558 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1559 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1560 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1561 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1562 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1563 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1564 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1565 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1566 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1567 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1568 = 9
                                                        else
                                                            _t1568 = -1
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
    prediction826 = _t1555
    if prediction826 == 13
        _t1570 = parse_uint32_type(parser)
        uint32_type840 = _t1570
        _t1571 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type840))
        _t1569 = _t1571
    else
        if prediction826 == 12
            _t1573 = parse_float32_type(parser)
            float32_type839 = _t1573
            _t1574 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type839))
            _t1572 = _t1574
        else
            if prediction826 == 11
                _t1576 = parse_int32_type(parser)
                int32_type838 = _t1576
                _t1577 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type838))
                _t1575 = _t1577
            else
                if prediction826 == 10
                    _t1579 = parse_boolean_type(parser)
                    boolean_type837 = _t1579
                    _t1580 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type837))
                    _t1578 = _t1580
                else
                    if prediction826 == 9
                        _t1582 = parse_decimal_type(parser)
                        decimal_type836 = _t1582
                        _t1583 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type836))
                        _t1581 = _t1583
                    else
                        if prediction826 == 8
                            _t1585 = parse_missing_type(parser)
                            missing_type835 = _t1585
                            _t1586 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type835))
                            _t1584 = _t1586
                        else
                            if prediction826 == 7
                                _t1588 = parse_datetime_type(parser)
                                datetime_type834 = _t1588
                                _t1589 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type834))
                                _t1587 = _t1589
                            else
                                if prediction826 == 6
                                    _t1591 = parse_date_type(parser)
                                    date_type833 = _t1591
                                    _t1592 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type833))
                                    _t1590 = _t1592
                                else
                                    if prediction826 == 5
                                        _t1594 = parse_int128_type(parser)
                                        int128_type832 = _t1594
                                        _t1595 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type832))
                                        _t1593 = _t1595
                                    else
                                        if prediction826 == 4
                                            _t1597 = parse_uint128_type(parser)
                                            uint128_type831 = _t1597
                                            _t1598 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type831))
                                            _t1596 = _t1598
                                        else
                                            if prediction826 == 3
                                                _t1600 = parse_float_type(parser)
                                                float_type830 = _t1600
                                                _t1601 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type830))
                                                _t1599 = _t1601
                                            else
                                                if prediction826 == 2
                                                    _t1603 = parse_int_type(parser)
                                                    int_type829 = _t1603
                                                    _t1604 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type829))
                                                    _t1602 = _t1604
                                                else
                                                    if prediction826 == 1
                                                        _t1606 = parse_string_type(parser)
                                                        string_type828 = _t1606
                                                        _t1607 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type828))
                                                        _t1605 = _t1607
                                                    else
                                                        if prediction826 == 0
                                                            _t1609 = parse_unspecified_type(parser)
                                                            unspecified_type827 = _t1609
                                                            _t1610 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type827))
                                                            _t1608 = _t1610
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
            _t1572 = _t1575
        end
        _t1569 = _t1572
    end
    result842 = _t1569
    record_span!(parser, span_start841, "Type")
    return result842
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start843 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1611 = Proto.UnspecifiedType()
    result844 = _t1611
    record_span!(parser, span_start843, "UnspecifiedType")
    return result844
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start845 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1612 = Proto.StringType()
    result846 = _t1612
    record_span!(parser, span_start845, "StringType")
    return result846
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start847 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1613 = Proto.IntType()
    result848 = _t1613
    record_span!(parser, span_start847, "IntType")
    return result848
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start849 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1614 = Proto.FloatType()
    result850 = _t1614
    record_span!(parser, span_start849, "FloatType")
    return result850
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start851 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1615 = Proto.UInt128Type()
    result852 = _t1615
    record_span!(parser, span_start851, "UInt128Type")
    return result852
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start853 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1616 = Proto.Int128Type()
    result854 = _t1616
    record_span!(parser, span_start853, "Int128Type")
    return result854
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start855 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1617 = Proto.DateType()
    result856 = _t1617
    record_span!(parser, span_start855, "DateType")
    return result856
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start857 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1618 = Proto.DateTimeType()
    result858 = _t1618
    record_span!(parser, span_start857, "DateTimeType")
    return result858
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start859 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1619 = Proto.MissingType()
    result860 = _t1619
    record_span!(parser, span_start859, "MissingType")
    return result860
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start863 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int861 = consume_terminal!(parser, "INT")
    int_3862 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1620 = Proto.DecimalType(precision=Int32(int861), scale=Int32(int_3862))
    result864 = _t1620
    record_span!(parser, span_start863, "DecimalType")
    return result864
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start865 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1621 = Proto.BooleanType()
    result866 = _t1621
    record_span!(parser, span_start865, "BooleanType")
    return result866
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start867 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1622 = Proto.Int32Type()
    result868 = _t1622
    record_span!(parser, span_start867, "Int32Type")
    return result868
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start869 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1623 = Proto.Float32Type()
    result870 = _t1623
    record_span!(parser, span_start869, "Float32Type")
    return result870
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start871 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1624 = Proto.UInt32Type()
    result872 = _t1624
    record_span!(parser, span_start871, "UInt32Type")
    return result872
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs873 = Proto.Binding[]
    cond874 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond874
        _t1625 = parse_binding(parser)
        item875 = _t1625
        push!(xs873, item875)
        cond874 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings876 = xs873
    return bindings876
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start891 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1627 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1628 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1629 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1630 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1631 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1632 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1633 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1634 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1635 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1636 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1637 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1638 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1639 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1640 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1641 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1642 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1643 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1644 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1645 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1646 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1647 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1648 = 10
                                                                                            else
                                                                                                _t1648 = -1
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
        _t1626 = _t1627
    else
        _t1626 = -1
    end
    prediction877 = _t1626
    if prediction877 == 12
        _t1650 = parse_cast(parser)
        cast890 = _t1650
        _t1651 = Proto.Formula(formula_type=OneOf(:cast, cast890))
        _t1649 = _t1651
    else
        if prediction877 == 11
            _t1653 = parse_rel_atom(parser)
            rel_atom889 = _t1653
            _t1654 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom889))
            _t1652 = _t1654
        else
            if prediction877 == 10
                _t1656 = parse_primitive(parser)
                primitive888 = _t1656
                _t1657 = Proto.Formula(formula_type=OneOf(:primitive, primitive888))
                _t1655 = _t1657
            else
                if prediction877 == 9
                    _t1659 = parse_pragma(parser)
                    pragma887 = _t1659
                    _t1660 = Proto.Formula(formula_type=OneOf(:pragma, pragma887))
                    _t1658 = _t1660
                else
                    if prediction877 == 8
                        _t1662 = parse_atom(parser)
                        atom886 = _t1662
                        _t1663 = Proto.Formula(formula_type=OneOf(:atom, atom886))
                        _t1661 = _t1663
                    else
                        if prediction877 == 7
                            _t1665 = parse_ffi(parser)
                            ffi885 = _t1665
                            _t1666 = Proto.Formula(formula_type=OneOf(:ffi, ffi885))
                            _t1664 = _t1666
                        else
                            if prediction877 == 6
                                _t1668 = parse_not(parser)
                                not884 = _t1668
                                _t1669 = Proto.Formula(formula_type=OneOf(:not, not884))
                                _t1667 = _t1669
                            else
                                if prediction877 == 5
                                    _t1671 = parse_disjunction(parser)
                                    disjunction883 = _t1671
                                    _t1672 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction883))
                                    _t1670 = _t1672
                                else
                                    if prediction877 == 4
                                        _t1674 = parse_conjunction(parser)
                                        conjunction882 = _t1674
                                        _t1675 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction882))
                                        _t1673 = _t1675
                                    else
                                        if prediction877 == 3
                                            _t1677 = parse_reduce(parser)
                                            reduce881 = _t1677
                                            _t1678 = Proto.Formula(formula_type=OneOf(:reduce, reduce881))
                                            _t1676 = _t1678
                                        else
                                            if prediction877 == 2
                                                _t1680 = parse_exists(parser)
                                                exists880 = _t1680
                                                _t1681 = Proto.Formula(formula_type=OneOf(:exists, exists880))
                                                _t1679 = _t1681
                                            else
                                                if prediction877 == 1
                                                    _t1683 = parse_false(parser)
                                                    false879 = _t1683
                                                    _t1684 = Proto.Formula(formula_type=OneOf(:disjunction, false879))
                                                    _t1682 = _t1684
                                                else
                                                    if prediction877 == 0
                                                        _t1686 = parse_true(parser)
                                                        true878 = _t1686
                                                        _t1687 = Proto.Formula(formula_type=OneOf(:conjunction, true878))
                                                        _t1685 = _t1687
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1682 = _t1685
                                                end
                                                _t1679 = _t1682
                                            end
                                            _t1676 = _t1679
                                        end
                                        _t1673 = _t1676
                                    end
                                    _t1670 = _t1673
                                end
                                _t1667 = _t1670
                            end
                            _t1664 = _t1667
                        end
                        _t1661 = _t1664
                    end
                    _t1658 = _t1661
                end
                _t1655 = _t1658
            end
            _t1652 = _t1655
        end
        _t1649 = _t1652
    end
    result892 = _t1649
    record_span!(parser, span_start891, "Formula")
    return result892
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start893 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1688 = Proto.Conjunction(args=Proto.Formula[])
    result894 = _t1688
    record_span!(parser, span_start893, "Conjunction")
    return result894
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start895 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1689 = Proto.Disjunction(args=Proto.Formula[])
    result896 = _t1689
    record_span!(parser, span_start895, "Disjunction")
    return result896
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start899 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1690 = parse_bindings(parser)
    bindings897 = _t1690
    _t1691 = parse_formula(parser)
    formula898 = _t1691
    consume_literal!(parser, ")")
    _t1692 = Proto.Abstraction(vars=vcat(bindings897[1], !isnothing(bindings897[2]) ? bindings897[2] : []), value=formula898)
    _t1693 = Proto.Exists(body=_t1692)
    result900 = _t1693
    record_span!(parser, span_start899, "Exists")
    return result900
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start904 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1694 = parse_abstraction(parser)
    abstraction901 = _t1694
    _t1695 = parse_abstraction(parser)
    abstraction_3902 = _t1695
    _t1696 = parse_terms(parser)
    terms903 = _t1696
    consume_literal!(parser, ")")
    _t1697 = Proto.Reduce(op=abstraction901, body=abstraction_3902, terms=terms903)
    result905 = _t1697
    record_span!(parser, span_start904, "Reduce")
    return result905
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs906 = Proto.Term[]
    cond907 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond907
        _t1698 = parse_term(parser)
        item908 = _t1698
        push!(xs906, item908)
        cond907 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms909 = xs906
    consume_literal!(parser, ")")
    return terms909
end

function parse_term(parser::ParserState)::Proto.Term
    span_start913 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1699 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1700 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1701 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1702 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1703 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1704 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1705 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1706 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1707 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1708 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1709 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1710 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1711 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1712 = 1
                                                        else
                                                            _t1712 = -1
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
            end
            _t1700 = _t1701
        end
        _t1699 = _t1700
    end
    prediction910 = _t1699
    if prediction910 == 1
        _t1714 = parse_value(parser)
        value912 = _t1714
        _t1715 = Proto.Term(term_type=OneOf(:constant, value912))
        _t1713 = _t1715
    else
        if prediction910 == 0
            _t1717 = parse_var(parser)
            var911 = _t1717
            _t1718 = Proto.Term(term_type=OneOf(:var, var911))
            _t1716 = _t1718
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1713 = _t1716
    end
    result914 = _t1713
    record_span!(parser, span_start913, "Term")
    return result914
end

function parse_var(parser::ParserState)::Proto.Var
    span_start916 = span_start(parser)
    symbol915 = consume_terminal!(parser, "SYMBOL")
    _t1719 = Proto.Var(name=symbol915)
    result917 = _t1719
    record_span!(parser, span_start916, "Var")
    return result917
end

function parse_value(parser::ParserState)::Proto.Value
    span_start931 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1720 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1721 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1722 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1724 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1725 = 0
                        else
                            _t1725 = -1
                        end
                        _t1724 = _t1725
                    end
                    _t1723 = _t1724
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1726 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1727 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1728 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1729 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1730 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1731 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1732 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1733 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1734 = 10
                                                    else
                                                        _t1734 = -1
                                                    end
                                                    _t1733 = _t1734
                                                end
                                                _t1732 = _t1733
                                            end
                                            _t1731 = _t1732
                                        end
                                        _t1730 = _t1731
                                    end
                                    _t1729 = _t1730
                                end
                                _t1728 = _t1729
                            end
                            _t1727 = _t1728
                        end
                        _t1726 = _t1727
                    end
                    _t1723 = _t1726
                end
                _t1722 = _t1723
            end
            _t1721 = _t1722
        end
        _t1720 = _t1721
    end
    prediction918 = _t1720
    if prediction918 == 12
        _t1736 = parse_boolean_value(parser)
        boolean_value930 = _t1736
        _t1737 = Proto.Value(value=OneOf(:boolean_value, boolean_value930))
        _t1735 = _t1737
    else
        if prediction918 == 11
            consume_literal!(parser, "missing")
            _t1739 = Proto.MissingValue()
            _t1740 = Proto.Value(value=OneOf(:missing_value, _t1739))
            _t1738 = _t1740
        else
            if prediction918 == 10
                formatted_decimal929 = consume_terminal!(parser, "DECIMAL")
                _t1742 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal929))
                _t1741 = _t1742
            else
                if prediction918 == 9
                    formatted_int128928 = consume_terminal!(parser, "INT128")
                    _t1744 = Proto.Value(value=OneOf(:int128_value, formatted_int128928))
                    _t1743 = _t1744
                else
                    if prediction918 == 8
                        formatted_uint128927 = consume_terminal!(parser, "UINT128")
                        _t1746 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128927))
                        _t1745 = _t1746
                    else
                        if prediction918 == 7
                            formatted_uint32926 = consume_terminal!(parser, "UINT32")
                            _t1748 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32926))
                            _t1747 = _t1748
                        else
                            if prediction918 == 6
                                formatted_float925 = consume_terminal!(parser, "FLOAT")
                                _t1750 = Proto.Value(value=OneOf(:float_value, formatted_float925))
                                _t1749 = _t1750
                            else
                                if prediction918 == 5
                                    formatted_float32924 = consume_terminal!(parser, "FLOAT32")
                                    _t1752 = Proto.Value(value=OneOf(:float32_value, formatted_float32924))
                                    _t1751 = _t1752
                                else
                                    if prediction918 == 4
                                        formatted_int923 = consume_terminal!(parser, "INT")
                                        _t1754 = Proto.Value(value=OneOf(:int_value, formatted_int923))
                                        _t1753 = _t1754
                                    else
                                        if prediction918 == 3
                                            formatted_int32922 = consume_terminal!(parser, "INT32")
                                            _t1756 = Proto.Value(value=OneOf(:int32_value, formatted_int32922))
                                            _t1755 = _t1756
                                        else
                                            if prediction918 == 2
                                                formatted_string921 = consume_terminal!(parser, "STRING")
                                                _t1758 = Proto.Value(value=OneOf(:string_value, formatted_string921))
                                                _t1757 = _t1758
                                            else
                                                if prediction918 == 1
                                                    _t1760 = parse_datetime(parser)
                                                    datetime920 = _t1760
                                                    _t1761 = Proto.Value(value=OneOf(:datetime_value, datetime920))
                                                    _t1759 = _t1761
                                                else
                                                    if prediction918 == 0
                                                        _t1763 = parse_date(parser)
                                                        date919 = _t1763
                                                        _t1764 = Proto.Value(value=OneOf(:date_value, date919))
                                                        _t1762 = _t1764
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1759 = _t1762
                                                end
                                                _t1757 = _t1759
                                            end
                                            _t1755 = _t1757
                                        end
                                        _t1753 = _t1755
                                    end
                                    _t1751 = _t1753
                                end
                                _t1749 = _t1751
                            end
                            _t1747 = _t1749
                        end
                        _t1745 = _t1747
                    end
                    _t1743 = _t1745
                end
                _t1741 = _t1743
            end
            _t1738 = _t1741
        end
        _t1735 = _t1738
    end
    result932 = _t1735
    record_span!(parser, span_start931, "Value")
    return result932
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start936 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int933 = consume_terminal!(parser, "INT")
    formatted_int_3934 = consume_terminal!(parser, "INT")
    formatted_int_4935 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1765 = Proto.DateValue(year=Int32(formatted_int933), month=Int32(formatted_int_3934), day=Int32(formatted_int_4935))
    result937 = _t1765
    record_span!(parser, span_start936, "DateValue")
    return result937
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start945 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int938 = consume_terminal!(parser, "INT")
    formatted_int_3939 = consume_terminal!(parser, "INT")
    formatted_int_4940 = consume_terminal!(parser, "INT")
    formatted_int_5941 = consume_terminal!(parser, "INT")
    formatted_int_6942 = consume_terminal!(parser, "INT")
    formatted_int_7943 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1766 = consume_terminal!(parser, "INT")
    else
        _t1766 = nothing
    end
    formatted_int_8944 = _t1766
    consume_literal!(parser, ")")
    _t1767 = Proto.DateTimeValue(year=Int32(formatted_int938), month=Int32(formatted_int_3939), day=Int32(formatted_int_4940), hour=Int32(formatted_int_5941), minute=Int32(formatted_int_6942), second=Int32(formatted_int_7943), microsecond=Int32((!isnothing(formatted_int_8944) ? formatted_int_8944 : 0)))
    result946 = _t1767
    record_span!(parser, span_start945, "DateTimeValue")
    return result946
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start951 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs947 = Proto.Formula[]
    cond948 = match_lookahead_literal(parser, "(", 0)
    while cond948
        _t1768 = parse_formula(parser)
        item949 = _t1768
        push!(xs947, item949)
        cond948 = match_lookahead_literal(parser, "(", 0)
    end
    formulas950 = xs947
    consume_literal!(parser, ")")
    _t1769 = Proto.Conjunction(args=formulas950)
    result952 = _t1769
    record_span!(parser, span_start951, "Conjunction")
    return result952
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start957 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs953 = Proto.Formula[]
    cond954 = match_lookahead_literal(parser, "(", 0)
    while cond954
        _t1770 = parse_formula(parser)
        item955 = _t1770
        push!(xs953, item955)
        cond954 = match_lookahead_literal(parser, "(", 0)
    end
    formulas956 = xs953
    consume_literal!(parser, ")")
    _t1771 = Proto.Disjunction(args=formulas956)
    result958 = _t1771
    record_span!(parser, span_start957, "Disjunction")
    return result958
end

function parse_not(parser::ParserState)::Proto.Not
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1772 = parse_formula(parser)
    formula959 = _t1772
    consume_literal!(parser, ")")
    _t1773 = Proto.Not(arg=formula959)
    result961 = _t1773
    record_span!(parser, span_start960, "Not")
    return result961
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start965 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1774 = parse_name(parser)
    name962 = _t1774
    _t1775 = parse_ffi_args(parser)
    ffi_args963 = _t1775
    _t1776 = parse_terms(parser)
    terms964 = _t1776
    consume_literal!(parser, ")")
    _t1777 = Proto.FFI(name=name962, args=ffi_args963, terms=terms964)
    result966 = _t1777
    record_span!(parser, span_start965, "FFI")
    return result966
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol967 = consume_terminal!(parser, "SYMBOL")
    return symbol967
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs968 = Proto.Abstraction[]
    cond969 = match_lookahead_literal(parser, "(", 0)
    while cond969
        _t1778 = parse_abstraction(parser)
        item970 = _t1778
        push!(xs968, item970)
        cond969 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions971 = xs968
    consume_literal!(parser, ")")
    return abstractions971
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start977 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1779 = parse_relation_id(parser)
    relation_id972 = _t1779
    xs973 = Proto.Term[]
    cond974 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond974
        _t1780 = parse_term(parser)
        item975 = _t1780
        push!(xs973, item975)
        cond974 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms976 = xs973
    consume_literal!(parser, ")")
    _t1781 = Proto.Atom(name=relation_id972, terms=terms976)
    result978 = _t1781
    record_span!(parser, span_start977, "Atom")
    return result978
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start984 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1782 = parse_name(parser)
    name979 = _t1782
    xs980 = Proto.Term[]
    cond981 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond981
        _t1783 = parse_term(parser)
        item982 = _t1783
        push!(xs980, item982)
        cond981 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms983 = xs980
    consume_literal!(parser, ")")
    _t1784 = Proto.Pragma(name=name979, terms=terms983)
    result985 = _t1784
    record_span!(parser, span_start984, "Pragma")
    return result985
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start1001 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1786 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1787 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1788 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1789 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1790 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1791 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1792 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1793 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1794 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1795 = 7
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
    else
        _t1785 = -1
    end
    prediction986 = _t1785
    if prediction986 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1797 = parse_name(parser)
        name996 = _t1797
        xs997 = Proto.RelTerm[]
        cond998 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond998
            _t1798 = parse_rel_term(parser)
            item999 = _t1798
            push!(xs997, item999)
            cond998 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms1000 = xs997
        consume_literal!(parser, ")")
        _t1799 = Proto.Primitive(name=name996, terms=rel_terms1000)
        _t1796 = _t1799
    else
        if prediction986 == 8
            _t1801 = parse_divide(parser)
            divide995 = _t1801
            _t1800 = divide995
        else
            if prediction986 == 7
                _t1803 = parse_multiply(parser)
                multiply994 = _t1803
                _t1802 = multiply994
            else
                if prediction986 == 6
                    _t1805 = parse_minus(parser)
                    minus993 = _t1805
                    _t1804 = minus993
                else
                    if prediction986 == 5
                        _t1807 = parse_add(parser)
                        add992 = _t1807
                        _t1806 = add992
                    else
                        if prediction986 == 4
                            _t1809 = parse_gt_eq(parser)
                            gt_eq991 = _t1809
                            _t1808 = gt_eq991
                        else
                            if prediction986 == 3
                                _t1811 = parse_gt(parser)
                                gt990 = _t1811
                                _t1810 = gt990
                            else
                                if prediction986 == 2
                                    _t1813 = parse_lt_eq(parser)
                                    lt_eq989 = _t1813
                                    _t1812 = lt_eq989
                                else
                                    if prediction986 == 1
                                        _t1815 = parse_lt(parser)
                                        lt988 = _t1815
                                        _t1814 = lt988
                                    else
                                        if prediction986 == 0
                                            _t1817 = parse_eq(parser)
                                            eq987 = _t1817
                                            _t1816 = eq987
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1814 = _t1816
                                    end
                                    _t1812 = _t1814
                                end
                                _t1810 = _t1812
                            end
                            _t1808 = _t1810
                        end
                        _t1806 = _t1808
                    end
                    _t1804 = _t1806
                end
                _t1802 = _t1804
            end
            _t1800 = _t1802
        end
        _t1796 = _t1800
    end
    result1002 = _t1796
    record_span!(parser, span_start1001, "Primitive")
    return result1002
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start1005 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1818 = parse_term(parser)
    term1003 = _t1818
    _t1819 = parse_term(parser)
    term_31004 = _t1819
    consume_literal!(parser, ")")
    _t1820 = Proto.RelTerm(rel_term_type=OneOf(:term, term1003))
    _t1821 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31004))
    _t1822 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1820, _t1821])
    result1006 = _t1822
    record_span!(parser, span_start1005, "Primitive")
    return result1006
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start1009 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1823 = parse_term(parser)
    term1007 = _t1823
    _t1824 = parse_term(parser)
    term_31008 = _t1824
    consume_literal!(parser, ")")
    _t1825 = Proto.RelTerm(rel_term_type=OneOf(:term, term1007))
    _t1826 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31008))
    _t1827 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1825, _t1826])
    result1010 = _t1827
    record_span!(parser, span_start1009, "Primitive")
    return result1010
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start1013 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1828 = parse_term(parser)
    term1011 = _t1828
    _t1829 = parse_term(parser)
    term_31012 = _t1829
    consume_literal!(parser, ")")
    _t1830 = Proto.RelTerm(rel_term_type=OneOf(:term, term1011))
    _t1831 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31012))
    _t1832 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1830, _t1831])
    result1014 = _t1832
    record_span!(parser, span_start1013, "Primitive")
    return result1014
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start1017 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1833 = parse_term(parser)
    term1015 = _t1833
    _t1834 = parse_term(parser)
    term_31016 = _t1834
    consume_literal!(parser, ")")
    _t1835 = Proto.RelTerm(rel_term_type=OneOf(:term, term1015))
    _t1836 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31016))
    _t1837 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1835, _t1836])
    result1018 = _t1837
    record_span!(parser, span_start1017, "Primitive")
    return result1018
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start1021 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1838 = parse_term(parser)
    term1019 = _t1838
    _t1839 = parse_term(parser)
    term_31020 = _t1839
    consume_literal!(parser, ")")
    _t1840 = Proto.RelTerm(rel_term_type=OneOf(:term, term1019))
    _t1841 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31020))
    _t1842 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1840, _t1841])
    result1022 = _t1842
    record_span!(parser, span_start1021, "Primitive")
    return result1022
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start1026 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1843 = parse_term(parser)
    term1023 = _t1843
    _t1844 = parse_term(parser)
    term_31024 = _t1844
    _t1845 = parse_term(parser)
    term_41025 = _t1845
    consume_literal!(parser, ")")
    _t1846 = Proto.RelTerm(rel_term_type=OneOf(:term, term1023))
    _t1847 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31024))
    _t1848 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41025))
    _t1849 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1846, _t1847, _t1848])
    result1027 = _t1849
    record_span!(parser, span_start1026, "Primitive")
    return result1027
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start1031 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1850 = parse_term(parser)
    term1028 = _t1850
    _t1851 = parse_term(parser)
    term_31029 = _t1851
    _t1852 = parse_term(parser)
    term_41030 = _t1852
    consume_literal!(parser, ")")
    _t1853 = Proto.RelTerm(rel_term_type=OneOf(:term, term1028))
    _t1854 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31029))
    _t1855 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41030))
    _t1856 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1853, _t1854, _t1855])
    result1032 = _t1856
    record_span!(parser, span_start1031, "Primitive")
    return result1032
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1036 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1857 = parse_term(parser)
    term1033 = _t1857
    _t1858 = parse_term(parser)
    term_31034 = _t1858
    _t1859 = parse_term(parser)
    term_41035 = _t1859
    consume_literal!(parser, ")")
    _t1860 = Proto.RelTerm(rel_term_type=OneOf(:term, term1033))
    _t1861 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31034))
    _t1862 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41035))
    _t1863 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1860, _t1861, _t1862])
    result1037 = _t1863
    record_span!(parser, span_start1036, "Primitive")
    return result1037
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1041 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1864 = parse_term(parser)
    term1038 = _t1864
    _t1865 = parse_term(parser)
    term_31039 = _t1865
    _t1866 = parse_term(parser)
    term_41040 = _t1866
    consume_literal!(parser, ")")
    _t1867 = Proto.RelTerm(rel_term_type=OneOf(:term, term1038))
    _t1868 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31039))
    _t1869 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41040))
    _t1870 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1867, _t1868, _t1869])
    result1042 = _t1870
    record_span!(parser, span_start1041, "Primitive")
    return result1042
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1046 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1871 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1872 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1873 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1874 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1875 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1876 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1877 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1878 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1879 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1880 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1881 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1882 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1883 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1884 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1885 = 1
                                                            else
                                                                _t1885 = -1
                                                            end
                                                            _t1884 = _t1885
                                                        end
                                                        _t1883 = _t1884
                                                    end
                                                    _t1882 = _t1883
                                                end
                                                _t1881 = _t1882
                                            end
                                            _t1880 = _t1881
                                        end
                                        _t1879 = _t1880
                                    end
                                    _t1878 = _t1879
                                end
                                _t1877 = _t1878
                            end
                            _t1876 = _t1877
                        end
                        _t1875 = _t1876
                    end
                    _t1874 = _t1875
                end
                _t1873 = _t1874
            end
            _t1872 = _t1873
        end
        _t1871 = _t1872
    end
    prediction1043 = _t1871
    if prediction1043 == 1
        _t1887 = parse_term(parser)
        term1045 = _t1887
        _t1888 = Proto.RelTerm(rel_term_type=OneOf(:term, term1045))
        _t1886 = _t1888
    else
        if prediction1043 == 0
            _t1890 = parse_specialized_value(parser)
            specialized_value1044 = _t1890
            _t1891 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1044))
            _t1889 = _t1891
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1886 = _t1889
    end
    result1047 = _t1886
    record_span!(parser, span_start1046, "RelTerm")
    return result1047
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1049 = span_start(parser)
    consume_literal!(parser, "#")
    _t1892 = parse_raw_value(parser)
    raw_value1048 = _t1892
    result1050 = raw_value1048
    record_span!(parser, span_start1049, "Value")
    return result1050
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1056 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1893 = parse_name(parser)
    name1051 = _t1893
    xs1052 = Proto.RelTerm[]
    cond1053 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1053
        _t1894 = parse_rel_term(parser)
        item1054 = _t1894
        push!(xs1052, item1054)
        cond1053 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1055 = xs1052
    consume_literal!(parser, ")")
    _t1895 = Proto.RelAtom(name=name1051, terms=rel_terms1055)
    result1057 = _t1895
    record_span!(parser, span_start1056, "RelAtom")
    return result1057
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1060 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1896 = parse_term(parser)
    term1058 = _t1896
    _t1897 = parse_term(parser)
    term_31059 = _t1897
    consume_literal!(parser, ")")
    _t1898 = Proto.Cast(input=term1058, result=term_31059)
    result1061 = _t1898
    record_span!(parser, span_start1060, "Cast")
    return result1061
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1062 = Proto.Attribute[]
    cond1063 = match_lookahead_literal(parser, "(", 0)
    while cond1063
        _t1899 = parse_attribute(parser)
        item1064 = _t1899
        push!(xs1062, item1064)
        cond1063 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1065 = xs1062
    consume_literal!(parser, ")")
    return attributes1065
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1071 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1900 = parse_name(parser)
    name1066 = _t1900
    xs1067 = Proto.Value[]
    cond1068 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1068
        _t1901 = parse_raw_value(parser)
        item1069 = _t1901
        push!(xs1067, item1069)
        cond1068 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1070 = xs1067
    consume_literal!(parser, ")")
    _t1902 = Proto.Attribute(name=name1066, args=raw_values1070)
    result1072 = _t1902
    record_span!(parser, span_start1071, "Attribute")
    return result1072
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1079 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1073 = Proto.RelationId[]
    cond1074 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1074
        _t1903 = parse_relation_id(parser)
        item1075 = _t1903
        push!(xs1073, item1075)
        cond1074 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1076 = xs1073
    _t1904 = parse_script(parser)
    script1077 = _t1904
    if match_lookahead_literal(parser, "(", 0)
        _t1906 = parse_attrs(parser)
        _t1905 = _t1906
    else
        _t1905 = nothing
    end
    attrs1078 = _t1905
    consume_literal!(parser, ")")
    _t1907 = Proto.Algorithm(var"#global"=relation_ids1076, body=script1077, attrs=(!isnothing(attrs1078) ? attrs1078 : Proto.Attribute[]))
    result1080 = _t1907
    record_span!(parser, span_start1079, "Algorithm")
    return result1080
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1085 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1081 = Proto.Construct[]
    cond1082 = match_lookahead_literal(parser, "(", 0)
    while cond1082
        _t1908 = parse_construct(parser)
        item1083 = _t1908
        push!(xs1081, item1083)
        cond1082 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1084 = xs1081
    consume_literal!(parser, ")")
    _t1909 = Proto.Script(constructs=constructs1084)
    result1086 = _t1909
    record_span!(parser, span_start1085, "Script")
    return result1086
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1090 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1911 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1912 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1913 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1914 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1915 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1916 = 1
                            else
                                _t1916 = -1
                            end
                            _t1915 = _t1916
                        end
                        _t1914 = _t1915
                    end
                    _t1913 = _t1914
                end
                _t1912 = _t1913
            end
            _t1911 = _t1912
        end
        _t1910 = _t1911
    else
        _t1910 = -1
    end
    prediction1087 = _t1910
    if prediction1087 == 1
        _t1918 = parse_instruction(parser)
        instruction1089 = _t1918
        _t1919 = Proto.Construct(construct_type=OneOf(:instruction, instruction1089))
        _t1917 = _t1919
    else
        if prediction1087 == 0
            _t1921 = parse_loop(parser)
            loop1088 = _t1921
            _t1922 = Proto.Construct(construct_type=OneOf(:loop, loop1088))
            _t1920 = _t1922
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1917 = _t1920
    end
    result1091 = _t1917
    record_span!(parser, span_start1090, "Construct")
    return result1091
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1095 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1923 = parse_init(parser)
    init1092 = _t1923
    _t1924 = parse_script(parser)
    script1093 = _t1924
    if match_lookahead_literal(parser, "(", 0)
        _t1926 = parse_attrs(parser)
        _t1925 = _t1926
    else
        _t1925 = nothing
    end
    attrs1094 = _t1925
    consume_literal!(parser, ")")
    _t1927 = Proto.Loop(init=init1092, body=script1093, attrs=(!isnothing(attrs1094) ? attrs1094 : Proto.Attribute[]))
    result1096 = _t1927
    record_span!(parser, span_start1095, "Loop")
    return result1096
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1097 = Proto.Instruction[]
    cond1098 = match_lookahead_literal(parser, "(", 0)
    while cond1098
        _t1928 = parse_instruction(parser)
        item1099 = _t1928
        push!(xs1097, item1099)
        cond1098 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1100 = xs1097
    consume_literal!(parser, ")")
    return instructions1100
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1107 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1930 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1931 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1932 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1933 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1934 = 0
                        else
                            _t1934 = -1
                        end
                        _t1933 = _t1934
                    end
                    _t1932 = _t1933
                end
                _t1931 = _t1932
            end
            _t1930 = _t1931
        end
        _t1929 = _t1930
    else
        _t1929 = -1
    end
    prediction1101 = _t1929
    if prediction1101 == 4
        _t1936 = parse_monus_def(parser)
        monus_def1106 = _t1936
        _t1937 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1106))
        _t1935 = _t1937
    else
        if prediction1101 == 3
            _t1939 = parse_monoid_def(parser)
            monoid_def1105 = _t1939
            _t1940 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1105))
            _t1938 = _t1940
        else
            if prediction1101 == 2
                _t1942 = parse_break(parser)
                break1104 = _t1942
                _t1943 = Proto.Instruction(instr_type=OneOf(:var"#break", break1104))
                _t1941 = _t1943
            else
                if prediction1101 == 1
                    _t1945 = parse_upsert(parser)
                    upsert1103 = _t1945
                    _t1946 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1103))
                    _t1944 = _t1946
                else
                    if prediction1101 == 0
                        _t1948 = parse_assign(parser)
                        assign1102 = _t1948
                        _t1949 = Proto.Instruction(instr_type=OneOf(:assign, assign1102))
                        _t1947 = _t1949
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1944 = _t1947
                end
                _t1941 = _t1944
            end
            _t1938 = _t1941
        end
        _t1935 = _t1938
    end
    result1108 = _t1935
    record_span!(parser, span_start1107, "Instruction")
    return result1108
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1112 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1950 = parse_relation_id(parser)
    relation_id1109 = _t1950
    _t1951 = parse_abstraction(parser)
    abstraction1110 = _t1951
    if match_lookahead_literal(parser, "(", 0)
        _t1953 = parse_attrs(parser)
        _t1952 = _t1953
    else
        _t1952 = nothing
    end
    attrs1111 = _t1952
    consume_literal!(parser, ")")
    _t1954 = Proto.Assign(name=relation_id1109, body=abstraction1110, attrs=(!isnothing(attrs1111) ? attrs1111 : Proto.Attribute[]))
    result1113 = _t1954
    record_span!(parser, span_start1112, "Assign")
    return result1113
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1117 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1955 = parse_relation_id(parser)
    relation_id1114 = _t1955
    _t1956 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1115 = _t1956
    if match_lookahead_literal(parser, "(", 0)
        _t1958 = parse_attrs(parser)
        _t1957 = _t1958
    else
        _t1957 = nothing
    end
    attrs1116 = _t1957
    consume_literal!(parser, ")")
    _t1959 = Proto.Upsert(name=relation_id1114, body=abstraction_with_arity1115[1], attrs=(!isnothing(attrs1116) ? attrs1116 : Proto.Attribute[]), value_arity=abstraction_with_arity1115[2])
    result1118 = _t1959
    record_span!(parser, span_start1117, "Upsert")
    return result1118
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1960 = parse_bindings(parser)
    bindings1119 = _t1960
    _t1961 = parse_formula(parser)
    formula1120 = _t1961
    consume_literal!(parser, ")")
    _t1962 = Proto.Abstraction(vars=vcat(bindings1119[1], !isnothing(bindings1119[2]) ? bindings1119[2] : []), value=formula1120)
    return (_t1962, length(bindings1119[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1124 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1963 = parse_relation_id(parser)
    relation_id1121 = _t1963
    _t1964 = parse_abstraction(parser)
    abstraction1122 = _t1964
    if match_lookahead_literal(parser, "(", 0)
        _t1966 = parse_attrs(parser)
        _t1965 = _t1966
    else
        _t1965 = nothing
    end
    attrs1123 = _t1965
    consume_literal!(parser, ")")
    _t1967 = Proto.Break(name=relation_id1121, body=abstraction1122, attrs=(!isnothing(attrs1123) ? attrs1123 : Proto.Attribute[]))
    result1125 = _t1967
    record_span!(parser, span_start1124, "Break")
    return result1125
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1130 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1968 = parse_monoid(parser)
    monoid1126 = _t1968
    _t1969 = parse_relation_id(parser)
    relation_id1127 = _t1969
    _t1970 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1128 = _t1970
    if match_lookahead_literal(parser, "(", 0)
        _t1972 = parse_attrs(parser)
        _t1971 = _t1972
    else
        _t1971 = nothing
    end
    attrs1129 = _t1971
    consume_literal!(parser, ")")
    _t1973 = Proto.MonoidDef(monoid=monoid1126, name=relation_id1127, body=abstraction_with_arity1128[1], attrs=(!isnothing(attrs1129) ? attrs1129 : Proto.Attribute[]), value_arity=abstraction_with_arity1128[2])
    result1131 = _t1973
    record_span!(parser, span_start1130, "MonoidDef")
    return result1131
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1137 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1975 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1976 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1977 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1978 = 2
                    else
                        _t1978 = -1
                    end
                    _t1977 = _t1978
                end
                _t1976 = _t1977
            end
            _t1975 = _t1976
        end
        _t1974 = _t1975
    else
        _t1974 = -1
    end
    prediction1132 = _t1974
    if prediction1132 == 3
        _t1980 = parse_sum_monoid(parser)
        sum_monoid1136 = _t1980
        _t1981 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1136))
        _t1979 = _t1981
    else
        if prediction1132 == 2
            _t1983 = parse_max_monoid(parser)
            max_monoid1135 = _t1983
            _t1984 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1135))
            _t1982 = _t1984
        else
            if prediction1132 == 1
                _t1986 = parse_min_monoid(parser)
                min_monoid1134 = _t1986
                _t1987 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1134))
                _t1985 = _t1987
            else
                if prediction1132 == 0
                    _t1989 = parse_or_monoid(parser)
                    or_monoid1133 = _t1989
                    _t1990 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1133))
                    _t1988 = _t1990
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1985 = _t1988
            end
            _t1982 = _t1985
        end
        _t1979 = _t1982
    end
    result1138 = _t1979
    record_span!(parser, span_start1137, "Monoid")
    return result1138
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1139 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1991 = Proto.OrMonoid()
    result1140 = _t1991
    record_span!(parser, span_start1139, "OrMonoid")
    return result1140
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1142 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1992 = parse_type(parser)
    type1141 = _t1992
    consume_literal!(parser, ")")
    _t1993 = Proto.MinMonoid(var"#type"=type1141)
    result1143 = _t1993
    record_span!(parser, span_start1142, "MinMonoid")
    return result1143
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1145 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1994 = parse_type(parser)
    type1144 = _t1994
    consume_literal!(parser, ")")
    _t1995 = Proto.MaxMonoid(var"#type"=type1144)
    result1146 = _t1995
    record_span!(parser, span_start1145, "MaxMonoid")
    return result1146
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1148 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1996 = parse_type(parser)
    type1147 = _t1996
    consume_literal!(parser, ")")
    _t1997 = Proto.SumMonoid(var"#type"=type1147)
    result1149 = _t1997
    record_span!(parser, span_start1148, "SumMonoid")
    return result1149
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1154 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1998 = parse_monoid(parser)
    monoid1150 = _t1998
    _t1999 = parse_relation_id(parser)
    relation_id1151 = _t1999
    _t2000 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1152 = _t2000
    if match_lookahead_literal(parser, "(", 0)
        _t2002 = parse_attrs(parser)
        _t2001 = _t2002
    else
        _t2001 = nothing
    end
    attrs1153 = _t2001
    consume_literal!(parser, ")")
    _t2003 = Proto.MonusDef(monoid=monoid1150, name=relation_id1151, body=abstraction_with_arity1152[1], attrs=(!isnothing(attrs1153) ? attrs1153 : Proto.Attribute[]), value_arity=abstraction_with_arity1152[2])
    result1155 = _t2003
    record_span!(parser, span_start1154, "MonusDef")
    return result1155
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1160 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t2004 = parse_relation_id(parser)
    relation_id1156 = _t2004
    _t2005 = parse_abstraction(parser)
    abstraction1157 = _t2005
    _t2006 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1158 = _t2006
    _t2007 = parse_functional_dependency_values(parser)
    functional_dependency_values1159 = _t2007
    consume_literal!(parser, ")")
    _t2008 = Proto.FunctionalDependency(guard=abstraction1157, keys=functional_dependency_keys1158, values=functional_dependency_values1159)
    _t2009 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t2008), name=relation_id1156)
    result1161 = _t2009
    record_span!(parser, span_start1160, "Constraint")
    return result1161
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1162 = Proto.Var[]
    cond1163 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1163
        _t2010 = parse_var(parser)
        item1164 = _t2010
        push!(xs1162, item1164)
        cond1163 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1165 = xs1162
    consume_literal!(parser, ")")
    return vars1165
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1166 = Proto.Var[]
    cond1167 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1167
        _t2011 = parse_var(parser)
        item1168 = _t2011
        push!(xs1166, item1168)
        cond1167 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1169 = xs1166
    consume_literal!(parser, ")")
    return vars1169
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1175 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t2013 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t2014 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t2015 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t2016 = 1
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
    else
        _t2012 = -1
    end
    prediction1170 = _t2012
    if prediction1170 == 3
        _t2018 = parse_iceberg_data(parser)
        iceberg_data1174 = _t2018
        _t2019 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1174))
        _t2017 = _t2019
    else
        if prediction1170 == 2
            _t2021 = parse_csv_data(parser)
            csv_data1173 = _t2021
            _t2022 = Proto.Data(data_type=OneOf(:csv_data, csv_data1173))
            _t2020 = _t2022
        else
            if prediction1170 == 1
                _t2024 = parse_betree_relation(parser)
                betree_relation1172 = _t2024
                _t2025 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1172))
                _t2023 = _t2025
            else
                if prediction1170 == 0
                    _t2027 = parse_edb(parser)
                    edb1171 = _t2027
                    _t2028 = Proto.Data(data_type=OneOf(:edb, edb1171))
                    _t2026 = _t2028
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t2023 = _t2026
            end
            _t2020 = _t2023
        end
        _t2017 = _t2020
    end
    result1176 = _t2017
    record_span!(parser, span_start1175, "Data")
    return result1176
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1180 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t2029 = parse_relation_id(parser)
    relation_id1177 = _t2029
    _t2030 = parse_edb_path(parser)
    edb_path1178 = _t2030
    _t2031 = parse_edb_types(parser)
    edb_types1179 = _t2031
    consume_literal!(parser, ")")
    _t2032 = Proto.EDB(target_id=relation_id1177, path=edb_path1178, types=edb_types1179)
    result1181 = _t2032
    record_span!(parser, span_start1180, "EDB")
    return result1181
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1182 = String[]
    cond1183 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1183
        item1184 = consume_terminal!(parser, "STRING")
        push!(xs1182, item1184)
        cond1183 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1185 = xs1182
    consume_literal!(parser, "]")
    return strings1185
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1186 = Proto.var"#Type"[]
    cond1187 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1187
        _t2033 = parse_type(parser)
        item1188 = _t2033
        push!(xs1186, item1188)
        cond1187 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1189 = xs1186
    consume_literal!(parser, "]")
    return types1189
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1192 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t2034 = parse_relation_id(parser)
    relation_id1190 = _t2034
    _t2035 = parse_betree_info(parser)
    betree_info1191 = _t2035
    consume_literal!(parser, ")")
    _t2036 = Proto.BeTreeRelation(name=relation_id1190, relation_info=betree_info1191)
    result1193 = _t2036
    record_span!(parser, span_start1192, "BeTreeRelation")
    return result1193
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1197 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t2037 = parse_betree_info_key_types(parser)
    betree_info_key_types1194 = _t2037
    _t2038 = parse_betree_info_value_types(parser)
    betree_info_value_types1195 = _t2038
    _t2039 = parse_config_dict(parser)
    config_dict1196 = _t2039
    consume_literal!(parser, ")")
    _t2040 = construct_betree_info(parser, betree_info_key_types1194, betree_info_value_types1195, config_dict1196)
    result1198 = _t2040
    record_span!(parser, span_start1197, "BeTreeInfo")
    return result1198
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1199 = Proto.var"#Type"[]
    cond1200 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1200
        _t2041 = parse_type(parser)
        item1201 = _t2041
        push!(xs1199, item1201)
        cond1200 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1202 = xs1199
    consume_literal!(parser, ")")
    return types1202
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1203 = Proto.var"#Type"[]
    cond1204 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1204
        _t2042 = parse_type(parser)
        item1205 = _t2042
        push!(xs1203, item1205)
        cond1204 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1206 = xs1203
    consume_literal!(parser, ")")
    return types1206
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1212 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t2043 = parse_csvlocator(parser)
    csvlocator1207 = _t2043
    _t2044 = parse_csv_config(parser)
    csv_config1208 = _t2044
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t2046 = parse_gnf_columns(parser)
        _t2045 = _t2046
    else
        _t2045 = nothing
    end
    gnf_columns1209 = _t2045
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relations", 1))
        _t2048 = parse_target_relations(parser)
        _t2047 = _t2048
    else
        _t2047 = nothing
    end
    target_relations1210 = _t2047
    _t2049 = parse_csv_asof(parser)
    csv_asof1211 = _t2049
    consume_literal!(parser, ")")
    _t2050 = construct_csv_data(parser, csvlocator1207, csv_config1208, gnf_columns1209, target_relations1210, csv_asof1211)
    result1213 = _t2050
    record_span!(parser, span_start1212, "CSVData")
    return result1213
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1216 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t2052 = parse_csv_locator_paths(parser)
        _t2051 = _t2052
    else
        _t2051 = nothing
    end
    csv_locator_paths1214 = _t2051
    if match_lookahead_literal(parser, "(", 0)
        _t2054 = parse_csv_locator_inline_data(parser)
        _t2053 = _t2054
    else
        _t2053 = nothing
    end
    csv_locator_inline_data1215 = _t2053
    consume_literal!(parser, ")")
    _t2055 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1214) ? csv_locator_paths1214 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1215) ? csv_locator_inline_data1215 : "")))
    result1217 = _t2055
    record_span!(parser, span_start1216, "CSVLocator")
    return result1217
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
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

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1222 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1222
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1225 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t2056 = parse_config_dict(parser)
    config_dict1223 = _t2056
    if match_lookahead_literal(parser, "(", 0)
        _t2058 = parse__storage_integration(parser)
        _t2057 = _t2058
    else
        _t2057 = nothing
    end
    _storage_integration1224 = _t2057
    consume_literal!(parser, ")")
    _t2059 = construct_csv_config(parser, config_dict1223, _storage_integration1224)
    result1226 = _t2059
    record_span!(parser, span_start1225, "CSVConfig")
    return result1226
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t2060 = parse_config_dict(parser)
    config_dict1227 = _t2060
    consume_literal!(parser, ")")
    return config_dict1227
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1228 = Proto.GNFColumn[]
    cond1229 = match_lookahead_literal(parser, "(", 0)
    while cond1229
        _t2061 = parse_gnf_column(parser)
        item1230 = _t2061
        push!(xs1228, item1230)
        cond1229 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1231 = xs1228
    consume_literal!(parser, ")")
    return gnf_columns1231
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1238 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t2062 = parse_gnf_column_path(parser)
    gnf_column_path1232 = _t2062
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t2064 = parse_relation_id(parser)
        _t2063 = _t2064
    else
        _t2063 = nothing
    end
    relation_id1233 = _t2063
    consume_literal!(parser, "[")
    xs1234 = Proto.var"#Type"[]
    cond1235 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1235
        _t2065 = parse_type(parser)
        item1236 = _t2065
        push!(xs1234, item1236)
        cond1235 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1237 = xs1234
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2066 = Proto.GNFColumn(column_path=gnf_column_path1232, target_id=relation_id1233, types=types1237)
    result1239 = _t2066
    record_span!(parser, span_start1238, "GNFColumn")
    return result1239
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t2067 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t2068 = 0
        else
            _t2068 = -1
        end
        _t2067 = _t2068
    end
    prediction1240 = _t2067
    if prediction1240 == 1
        consume_literal!(parser, "[")
        xs1242 = String[]
        cond1243 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1243
            item1244 = consume_terminal!(parser, "STRING")
            push!(xs1242, item1244)
            cond1243 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1245 = xs1242
        consume_literal!(parser, "]")
        _t2069 = strings1245
    else
        if prediction1240 == 0
            string1241 = consume_terminal!(parser, "STRING")
            _t2070 = String[string1241]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t2069 = _t2070
    end
    return _t2069
end

function parse_target_relations(parser::ParserState)::Proto.TargetRelations
    span_start1249 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relations")
    _t2071 = parse_relation_keys(parser)
    relation_keys1246 = _t2071
    _t2072 = parse_relation_body(parser)
    relation_body1247 = _t2072
    if match_lookahead_literal(parser, "(", 0)
        _t2074 = parse_load_errors(parser)
        _t2073 = _t2074
    else
        _t2073 = nothing
    end
    load_errors1248 = _t2073
    consume_literal!(parser, ")")
    _t2075 = construct_relations(parser, relation_keys1246, relation_body1247, load_errors1248)
    result1250 = _t2075
    record_span!(parser, span_start1249, "TargetRelations")
    return result1250
end

function parse_relation_keys(parser::ParserState)::Tuple{Vector{Proto.NamedColumn}, Bool}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "keys", 1)
            if match_lookahead_literal(parser, "synthetic", 2)
                _t2078 = 1
            else
                if match_lookahead_literal(parser, ")", 2)
                    _t2079 = 0
                else
                    if match_lookahead_literal(parser, "(", 2)
                        _t2080 = 0
                    else
                        _t2080 = -1
                    end
                    _t2079 = _t2080
                end
                _t2078 = _t2079
            end
            _t2077 = _t2078
        else
            _t2077 = -1
        end
        _t2076 = _t2077
    else
        _t2076 = -1
    end
    prediction1251 = _t2076
    if prediction1251 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "keys")
        consume_literal!(parser, "synthetic")
        consume_literal!(parser, ")")
        _t2081 = (Proto.NamedColumn[], true,)
    else
        if prediction1251 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "keys")
            xs1252 = Proto.NamedColumn[]
            cond1253 = match_lookahead_literal(parser, "(", 0)
            while cond1253
                _t2083 = parse_named_column(parser)
                item1254 = _t2083
                push!(xs1252, item1254)
                cond1253 = match_lookahead_literal(parser, "(", 0)
            end
            named_columns1255 = xs1252
            consume_literal!(parser, ")")
            _t2082 = (named_columns1255, false,)
        else
            throw(ParseError("Unexpected token in relation_keys" * ": " * string(lookahead(parser, 0))))
        end
        _t2081 = _t2082
    end
    return _t2081
end

function parse_named_column(parser::ParserState)::Proto.NamedColumn
    span_start1258 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1256 = consume_terminal!(parser, "STRING")
    _t2084 = parse_type(parser)
    type1257 = _t2084
    consume_literal!(parser, ")")
    _t2085 = Proto.NamedColumn(name=string1256, var"#type"=type1257)
    result1259 = _t2085
    record_span!(parser, span_start1258, "NamedColumn")
    return result1259
end

function parse_relation_body(parser::ParserState)::Proto.TargetRelations
    span_start1264 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "relation", 1)
            _t2087 = 0
        else
            if match_lookahead_literal(parser, "inserts", 1)
                _t2088 = 1
            else
                _t2088 = 0
            end
            _t2087 = _t2088
        end
        _t2086 = _t2087
    else
        _t2086 = 0
    end
    prediction1260 = _t2086
    if prediction1260 == 1
        _t2090 = parse_cdc_inserts(parser)
        cdc_inserts1262 = _t2090
        _t2091 = parse_cdc_deletes(parser)
        cdc_deletes1263 = _t2091
        _t2092 = construct_cdc_relations(parser, cdc_inserts1262, cdc_deletes1263)
        _t2089 = _t2092
    else
        if prediction1260 == 0
            _t2094 = parse_non_cdc_relations(parser)
            non_cdc_relations1261 = _t2094
            _t2095 = construct_non_cdc_relations(parser, non_cdc_relations1261)
            _t2093 = _t2095
        else
            throw(ParseError("Unexpected token in relation_body" * ": " * string(lookahead(parser, 0))))
        end
        _t2089 = _t2093
    end
    result1265 = _t2089
    record_span!(parser, span_start1264, "TargetRelations")
    return result1265
end

function parse_non_cdc_relations(parser::ParserState)::Vector{Proto.TargetRelation}
    xs1266 = Proto.TargetRelation[]
    cond1267 = (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relation", 1))
    while cond1267
        _t2096 = parse_target_relation(parser)
        item1268 = _t2096
        push!(xs1266, item1268)
        cond1267 = (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relation", 1))
    end
    return xs1266
end

function parse_target_relation(parser::ParserState)::Proto.TargetRelation
    span_start1274 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relation")
    _t2097 = parse_relation_id(parser)
    relation_id1269 = _t2097
    xs1270 = Proto.NamedColumn[]
    cond1271 = match_lookahead_literal(parser, "(", 0)
    while cond1271
        _t2098 = parse_named_column(parser)
        item1272 = _t2098
        push!(xs1270, item1272)
        cond1271 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1273 = xs1270
    consume_literal!(parser, ")")
    _t2099 = Proto.TargetRelation(target_id=relation_id1269, values=named_columns1273)
    result1275 = _t2099
    record_span!(parser, span_start1274, "TargetRelation")
    return result1275
end

function parse_cdc_inserts(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "inserts")
    xs1276 = Proto.TargetRelation[]
    cond1277 = match_lookahead_literal(parser, "(", 0)
    while cond1277
        _t2100 = parse_target_relation(parser)
        item1278 = _t2100
        push!(xs1276, item1278)
        cond1277 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1279 = xs1276
    consume_literal!(parser, ")")
    return target_relations1279
end

function parse_cdc_deletes(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "deletes")
    xs1280 = Proto.TargetRelation[]
    cond1281 = match_lookahead_literal(parser, "(", 0)
    while cond1281
        _t2101 = parse_target_relation(parser)
        item1282 = _t2101
        push!(xs1280, item1282)
        cond1281 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1283 = xs1280
    consume_literal!(parser, ")")
    return target_relations1283
end

function parse_load_errors(parser::ParserState)::Proto.RelationId
    span_start1285 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "load_errors")
    _t2102 = parse_relation_id(parser)
    relation_id1284 = _t2102
    consume_literal!(parser, ")")
    result1286 = relation_id1284
    record_span!(parser, span_start1285, "RelationId")
    return result1286
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1287 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1287
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1294 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t2103 = parse_iceberg_locator(parser)
    iceberg_locator1288 = _t2103
    _t2104 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1289 = _t2104
    _t2105 = parse_gnf_columns(parser)
    gnf_columns1290 = _t2105
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2107 = parse_iceberg_from_snapshot(parser)
        _t2106 = _t2107
    else
        _t2106 = nothing
    end
    iceberg_from_snapshot1291 = _t2106
    if match_lookahead_literal(parser, "(", 0)
        _t2109 = parse_iceberg_to_snapshot(parser)
        _t2108 = _t2109
    else
        _t2108 = nothing
    end
    iceberg_to_snapshot1292 = _t2108
    _t2110 = parse_boolean_value(parser)
    boolean_value1293 = _t2110
    consume_literal!(parser, ")")
    _t2111 = construct_iceberg_data(parser, iceberg_locator1288, iceberg_catalog_config1289, gnf_columns1290, iceberg_from_snapshot1291, iceberg_to_snapshot1292, boolean_value1293)
    result1295 = _t2111
    record_span!(parser, span_start1294, "IcebergData")
    return result1295
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1299 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2112 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1296 = _t2112
    _t2113 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1297 = _t2113
    _t2114 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1298 = _t2114
    consume_literal!(parser, ")")
    _t2115 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1296, namespace=iceberg_locator_namespace1297, warehouse=iceberg_locator_warehouse1298)
    result1300 = _t2115
    record_span!(parser, span_start1299, "IcebergLocator")
    return result1300
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1301 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1301
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1302 = String[]
    cond1303 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1303
        item1304 = consume_terminal!(parser, "STRING")
        push!(xs1302, item1304)
        cond1303 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1305 = xs1302
    consume_literal!(parser, ")")
    return strings1305
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1306 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1306
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1311 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2116 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1307 = _t2116
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2118 = parse_iceberg_catalog_config_scope(parser)
        _t2117 = _t2118
    else
        _t2117 = nothing
    end
    iceberg_catalog_config_scope1308 = _t2117
    _t2119 = parse_iceberg_properties(parser)
    iceberg_properties1309 = _t2119
    _t2120 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1310 = _t2120
    consume_literal!(parser, ")")
    _t2121 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1307, iceberg_catalog_config_scope1308, iceberg_properties1309, iceberg_auth_properties1310)
    result1312 = _t2121
    record_span!(parser, span_start1311, "IcebergCatalogConfig")
    return result1312
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1313 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1313
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1314 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1314
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1315 = Tuple{String, String}[]
    cond1316 = match_lookahead_literal(parser, "(", 0)
    while cond1316
        _t2122 = parse_iceberg_property_entry(parser)
        item1317 = _t2122
        push!(xs1315, item1317)
        cond1316 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1318 = xs1315
    consume_literal!(parser, ")")
    return iceberg_property_entrys1318
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1319 = consume_terminal!(parser, "STRING")
    string_31320 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1319, string_31320,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1321 = Tuple{String, String}[]
    cond1322 = match_lookahead_literal(parser, "(", 0)
    while cond1322
        _t2123 = parse_iceberg_masked_property_entry(parser)
        item1323 = _t2123
        push!(xs1321, item1323)
        cond1322 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1324 = xs1321
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1324
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1325 = consume_terminal!(parser, "STRING")
    string_31326 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1325, string_31326,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1327 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1327
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1328 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1328
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1330 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2124 = parse_fragment_id(parser)
    fragment_id1329 = _t2124
    consume_literal!(parser, ")")
    _t2125 = Proto.Undefine(fragment_id=fragment_id1329)
    result1331 = _t2125
    record_span!(parser, span_start1330, "Undefine")
    return result1331
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1336 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1332 = Proto.RelationId[]
    cond1333 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1333
        _t2126 = parse_relation_id(parser)
        item1334 = _t2126
        push!(xs1332, item1334)
        cond1333 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1335 = xs1332
    consume_literal!(parser, ")")
    _t2127 = Proto.Context(relations=relation_ids1335)
    result1337 = _t2127
    record_span!(parser, span_start1336, "Context")
    return result1337
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1343 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2128 = parse_edb_path(parser)
    edb_path1338 = _t2128
    xs1339 = Proto.SnapshotMapping[]
    cond1340 = match_lookahead_literal(parser, "[", 0)
    while cond1340
        _t2129 = parse_snapshot_mapping(parser)
        item1341 = _t2129
        push!(xs1339, item1341)
        cond1340 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1342 = xs1339
    consume_literal!(parser, ")")
    _t2130 = Proto.Snapshot(mappings=snapshot_mappings1342, prefix=edb_path1338)
    result1344 = _t2130
    record_span!(parser, span_start1343, "Snapshot")
    return result1344
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1347 = span_start(parser)
    _t2131 = parse_edb_path(parser)
    edb_path1345 = _t2131
    _t2132 = parse_relation_id(parser)
    relation_id1346 = _t2132
    _t2133 = Proto.SnapshotMapping(destination_path=edb_path1345, source_relation=relation_id1346)
    result1348 = _t2133
    record_span!(parser, span_start1347, "SnapshotMapping")
    return result1348
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1349 = Proto.Read[]
    cond1350 = match_lookahead_literal(parser, "(", 0)
    while cond1350
        _t2134 = parse_read(parser)
        item1351 = _t2134
        push!(xs1349, item1351)
        cond1350 = match_lookahead_literal(parser, "(", 0)
    end
    reads1352 = xs1349
    consume_literal!(parser, ")")
    return reads1352
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1359 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2136 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2137 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2138 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2139 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2140 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2141 = 3
                            else
                                _t2141 = -1
                            end
                            _t2140 = _t2141
                        end
                        _t2139 = _t2140
                    end
                    _t2138 = _t2139
                end
                _t2137 = _t2138
            end
            _t2136 = _t2137
        end
        _t2135 = _t2136
    else
        _t2135 = -1
    end
    prediction1353 = _t2135
    if prediction1353 == 4
        _t2143 = parse_export(parser)
        export1358 = _t2143
        _t2144 = Proto.Read(read_type=OneOf(:var"#export", export1358))
        _t2142 = _t2144
    else
        if prediction1353 == 3
            _t2146 = parse_abort(parser)
            abort1357 = _t2146
            _t2147 = Proto.Read(read_type=OneOf(:abort, abort1357))
            _t2145 = _t2147
        else
            if prediction1353 == 2
                _t2149 = parse_what_if(parser)
                what_if1356 = _t2149
                _t2150 = Proto.Read(read_type=OneOf(:what_if, what_if1356))
                _t2148 = _t2150
            else
                if prediction1353 == 1
                    _t2152 = parse_output(parser)
                    output1355 = _t2152
                    _t2153 = Proto.Read(read_type=OneOf(:output, output1355))
                    _t2151 = _t2153
                else
                    if prediction1353 == 0
                        _t2155 = parse_demand(parser)
                        demand1354 = _t2155
                        _t2156 = Proto.Read(read_type=OneOf(:demand, demand1354))
                        _t2154 = _t2156
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2151 = _t2154
                end
                _t2148 = _t2151
            end
            _t2145 = _t2148
        end
        _t2142 = _t2145
    end
    result1360 = _t2142
    record_span!(parser, span_start1359, "Read")
    return result1360
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1362 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2157 = parse_relation_id(parser)
    relation_id1361 = _t2157
    consume_literal!(parser, ")")
    _t2158 = Proto.Demand(relation_id=relation_id1361)
    result1363 = _t2158
    record_span!(parser, span_start1362, "Demand")
    return result1363
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1366 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2159 = parse_name(parser)
    name1364 = _t2159
    _t2160 = parse_relation_id(parser)
    relation_id1365 = _t2160
    consume_literal!(parser, ")")
    _t2161 = Proto.Output(name=name1364, relation_id=relation_id1365)
    result1367 = _t2161
    record_span!(parser, span_start1366, "Output")
    return result1367
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1370 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2162 = parse_name(parser)
    name1368 = _t2162
    _t2163 = parse_epoch(parser)
    epoch1369 = _t2163
    consume_literal!(parser, ")")
    _t2164 = Proto.WhatIf(branch=name1368, epoch=epoch1369)
    result1371 = _t2164
    record_span!(parser, span_start1370, "WhatIf")
    return result1371
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1374 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2166 = parse_name(parser)
        _t2165 = _t2166
    else
        _t2165 = nothing
    end
    name1372 = _t2165
    _t2167 = parse_relation_id(parser)
    relation_id1373 = _t2167
    consume_literal!(parser, ")")
    _t2168 = Proto.Abort(name=(!isnothing(name1372) ? name1372 : "abort"), relation_id=relation_id1373)
    result1375 = _t2168
    record_span!(parser, span_start1374, "Abort")
    return result1375
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1379 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2170 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2171 = 0
            else
                _t2171 = -1
            end
            _t2170 = _t2171
        end
        _t2169 = _t2170
    else
        _t2169 = -1
    end
    prediction1376 = _t2169
    if prediction1376 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2173 = parse_export_iceberg_config(parser)
        export_iceberg_config1378 = _t2173
        consume_literal!(parser, ")")
        _t2174 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1378))
        _t2172 = _t2174
    else
        if prediction1376 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2176 = parse_export_csv_config(parser)
            export_csv_config1377 = _t2176
            consume_literal!(parser, ")")
            _t2177 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1377))
            _t2175 = _t2177
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2172 = _t2175
    end
    result1380 = _t2172
    record_span!(parser, span_start1379, "Export")
    return result1380
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1388 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2179 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2180 = 1
            else
                _t2180 = -1
            end
            _t2179 = _t2180
        end
        _t2178 = _t2179
    else
        _t2178 = -1
    end
    prediction1381 = _t2178
    if prediction1381 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2182 = parse_export_csv_path(parser)
        export_csv_path1385 = _t2182
        _t2183 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1386 = _t2183
        _t2184 = parse_config_dict(parser)
        config_dict1387 = _t2184
        consume_literal!(parser, ")")
        _t2185 = construct_export_csv_config(parser, export_csv_path1385, export_csv_columns_list1386, config_dict1387)
        _t2181 = _t2185
    else
        if prediction1381 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2187 = parse_export_csv_output_location(parser)
            export_csv_output_location1382 = _t2187
            _t2188 = parse_export_csv_source(parser)
            export_csv_source1383 = _t2188
            _t2189 = parse_csv_config(parser)
            csv_config1384 = _t2189
            consume_literal!(parser, ")")
            _t2190 = construct_export_csv_config_with_location(parser, export_csv_output_location1382, export_csv_source1383, csv_config1384)
            _t2186 = _t2190
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2181 = _t2186
    end
    result1389 = _t2181
    record_span!(parser, span_start1388, "ExportCSVConfig")
    return result1389
end

function parse_export_csv_output_location(parser::ParserState)::Tuple{String, String}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "transaction_output_name", 1)
            _t2192 = 1
        else
            if match_lookahead_literal(parser, "path", 1)
                _t2193 = 0
            else
                _t2193 = -1
            end
            _t2192 = _t2193
        end
        _t2191 = _t2192
    else
        _t2191 = -1
    end
    prediction1390 = _t2191
    if prediction1390 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "transaction_output_name")
        _t2195 = parse_name(parser)
        name1392 = _t2195
        consume_literal!(parser, ")")
        _t2194 = ("", name1392,)
    else
        if prediction1390 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "path")
            string1391 = consume_terminal!(parser, "STRING")
            consume_literal!(parser, ")")
            _t2196 = (string1391, "",)
        else
            throw(ParseError("Unexpected token in export_csv_output_location" * ": " * string(lookahead(parser, 0))))
        end
        _t2194 = _t2196
    end
    return _t2194
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1399 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2198 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2199 = 0
            else
                _t2199 = -1
            end
            _t2198 = _t2199
        end
        _t2197 = _t2198
    else
        _t2197 = -1
    end
    prediction1393 = _t2197
    if prediction1393 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2201 = parse_relation_id(parser)
        relation_id1398 = _t2201
        consume_literal!(parser, ")")
        _t2202 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1398))
        _t2200 = _t2202
    else
        if prediction1393 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1394 = Proto.ExportCSVColumn[]
            cond1395 = match_lookahead_literal(parser, "(", 0)
            while cond1395
                _t2204 = parse_export_csv_column(parser)
                item1396 = _t2204
                push!(xs1394, item1396)
                cond1395 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1397 = xs1394
            consume_literal!(parser, ")")
            _t2205 = Proto.ExportCSVColumns(columns=export_csv_columns1397)
            _t2206 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2205))
            _t2203 = _t2206
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2200 = _t2203
    end
    result1400 = _t2200
    record_span!(parser, span_start1399, "ExportCSVSource")
    return result1400
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1403 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1401 = consume_terminal!(parser, "STRING")
    _t2207 = parse_relation_id(parser)
    relation_id1402 = _t2207
    consume_literal!(parser, ")")
    _t2208 = Proto.ExportCSVColumn(column_name=string1401, column_data=relation_id1402)
    result1404 = _t2208
    record_span!(parser, span_start1403, "ExportCSVColumn")
    return result1404
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1405 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1405
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1406 = Proto.ExportCSVColumn[]
    cond1407 = match_lookahead_literal(parser, "(", 0)
    while cond1407
        _t2209 = parse_export_csv_column(parser)
        item1408 = _t2209
        push!(xs1406, item1408)
        cond1407 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1409 = xs1406
    consume_literal!(parser, ")")
    return export_csv_columns1409
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1415 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2210 = parse_iceberg_locator(parser)
    iceberg_locator1410 = _t2210
    _t2211 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1411 = _t2211
    _t2212 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1412 = _t2212
    _t2213 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1413 = _t2213
    if match_lookahead_literal(parser, "{", 0)
        _t2215 = parse_config_dict(parser)
        _t2214 = _t2215
    else
        _t2214 = nothing
    end
    config_dict1414 = _t2214
    consume_literal!(parser, ")")
    _t2216 = construct_export_iceberg_config_full(parser, iceberg_locator1410, iceberg_catalog_config1411, export_iceberg_table_def1412, iceberg_table_properties1413, config_dict1414)
    result1416 = _t2216
    record_span!(parser, span_start1415, "ExportIcebergConfig")
    return result1416
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1418 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2217 = parse_relation_id(parser)
    relation_id1417 = _t2217
    consume_literal!(parser, ")")
    result1419 = relation_id1417
    record_span!(parser, span_start1418, "RelationId")
    return result1419
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1420 = Tuple{String, String}[]
    cond1421 = match_lookahead_literal(parser, "(", 0)
    while cond1421
        _t2218 = parse_iceberg_property_entry(parser)
        item1422 = _t2218
        push!(xs1420, item1422)
        cond1421 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1423 = xs1420
    consume_literal!(parser, ")")
    return iceberg_property_entrys1423
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
