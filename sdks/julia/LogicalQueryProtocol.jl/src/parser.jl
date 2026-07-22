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
        _t2211 = nothing
    end
    if _has_proto_field(value, Symbol("int32_value"))
        return _get_oneof_field(value, :int32_value)
    else
        _t2212 = nothing
    end
    throw(ParseError("expected an int32 value (e.g. `1i32`) for this config field"))
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2213 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2214 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2215 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2216 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2217 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2218 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2219 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2220 = nothing
    end
    return nothing
end

function construct_non_cdc_relations(parser::ParserState, targets::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2221 = Proto.PlainTargets(targets=targets)
    _t2222 = Proto.TargetRelations(body=OneOf(:plain, _t2221), keys=Proto.NamedColumn[])
    return _t2222
end

function construct_cdc_relations(parser::ParserState, inserts::Vector{Proto.TargetRelation}, deletes::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2223 = Proto.CDCTargets(inserts=inserts, deletes=deletes)
    _t2224 = Proto.TargetRelations(body=OneOf(:cdc, _t2223), keys=Proto.NamedColumn[])
    return _t2224
end

function construct_synthetic_keys(parser::ParserState, marker::String)::Tuple{Vector{Proto.NamedColumn}, Bool}
    if marker != "synthetic_key"
        throw(ParseError("expected the `:synthetic_key` marker in the relation keys clause"))
    else
        _t2225 = nothing
    end
    return (Proto.NamedColumn[], true,)
end

function construct_relations(parser::ParserState, keys::Tuple{Vector{Proto.NamedColumn}, Bool}, body::Proto.TargetRelations)::Proto.TargetRelations
    if _has_proto_field(body, Symbol("plain"))
        _t2227 = Proto.TargetRelations(body=OneOf(:plain, _get_oneof_field(body, :plain)), keys=keys[1], synthetic_key=keys[2])
        return _t2227
    else
        _t2226 = nothing
    end
    _t2228 = Proto.TargetRelations(body=OneOf(:cdc, _get_oneof_field(body, :cdc)), keys=keys[1], synthetic_key=keys[2])
    return _t2228
end

function construct_csv_data(parser::ParserState, locator::Proto.CSVLocator, config::Proto.CSVConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, relations_opt::Union{Nothing, Proto.TargetRelations}, asof::String)::Proto.CSVData
    _t2229 = Proto.CSVData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), asof=asof, relations=relations_opt)
    return _t2229
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2230 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2230
    _t2231 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2231
    _t2232 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2232
    _t2233 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2233
    _t2234 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2234
    _t2235 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2235
    _t2236 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2236
    _t2237 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2237
    _t2238 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2238
    _t2239 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2239
    _t2240 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2240
    _t2241 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2241
    _t2242 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2242
    _t2243 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2243
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2244 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2245 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2246 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2247 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2248 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2249 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2250 = Proto.StorageIntegration(provider=_t2245, azure_sas_token=_t2246, s3_region=_t2247, s3_access_key_id=_t2248, s3_secret_access_key=_t2249)
    return _t2250
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2251 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2251
    _t2252 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2252
    _t2253 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2253
    _t2254 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2254
    _t2255 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2255
    _t2256 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2256
    _t2257 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2257
    _t2258 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2258
    _t2259 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2259
    _t2260 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2260
    _t2261 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2261
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2262 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2262
    _t2263 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2263
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
    _t2264 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2264
    _t2265 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2265
    _t2266 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2266
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2267 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2267
    _t2268 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2268
    _t2269 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2269
    _t2270 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2270
    _t2271 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2271
    _t2272 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2272
    _t2273 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2273
    _t2274 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2274
end

function construct_export_csv_config_with_location(parser::ParserState, location::Tuple{String, String}, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2275 = Proto.ExportCSVConfig(path=location[1], transaction_output_name=location[2], csv_source=csv_source, csv_config=csv_config)
    return _t2275
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2276 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2276
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2277 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2277
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2278 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2278
    _t2279 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2279
    _t2280 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2280
    table_props = Dict(table_property_pairs)
    _t2281 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2281
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start715 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1419 = parse_configure(parser)
        _t1418 = _t1419
    else
        _t1418 = nothing
    end
    configure709 = _t1418
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1421 = parse_sync(parser)
        _t1420 = _t1421
    else
        _t1420 = nothing
    end
    sync710 = _t1420
    xs711 = Proto.Epoch[]
    cond712 = match_lookahead_literal(parser, "(", 0)
    while cond712
        _t1422 = parse_epoch(parser)
        item713 = _t1422
        push!(xs711, item713)
        cond712 = match_lookahead_literal(parser, "(", 0)
    end
    epochs714 = xs711
    consume_literal!(parser, ")")
    _t1423 = default_configure(parser)
    _t1424 = Proto.Transaction(epochs=epochs714, configure=(!isnothing(configure709) ? configure709 : _t1423), sync=sync710)
    result716 = _t1424
    record_span!(parser, span_start715, "Transaction")
    return result716
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start718 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1425 = parse_config_dict(parser)
    config_dict717 = _t1425
    consume_literal!(parser, ")")
    _t1426 = construct_configure(parser, config_dict717)
    result719 = _t1426
    record_span!(parser, span_start718, "Configure")
    return result719
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs720 = Tuple{String, Proto.Value}[]
    cond721 = match_lookahead_literal(parser, ":", 0)
    while cond721
        _t1427 = parse_config_key_value(parser)
        item722 = _t1427
        push!(xs720, item722)
        cond721 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values723 = xs720
    consume_literal!(parser, "}")
    return config_key_values723
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol724 = consume_terminal!(parser, "SYMBOL")
    _t1428 = parse_raw_value(parser)
    raw_value725 = _t1428
    return (symbol724, raw_value725,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start739 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1429 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1430 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1431 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1433 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1434 = 0
                        else
                            _t1434 = -1
                        end
                        _t1433 = _t1434
                    end
                    _t1432 = _t1433
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1435 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1436 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1437 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1438 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1439 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1440 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1441 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1442 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1443 = 10
                                                    else
                                                        _t1443 = -1
                                                    end
                                                    _t1442 = _t1443
                                                end
                                                _t1441 = _t1442
                                            end
                                            _t1440 = _t1441
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
                    _t1432 = _t1435
                end
                _t1431 = _t1432
            end
            _t1430 = _t1431
        end
        _t1429 = _t1430
    end
    prediction726 = _t1429
    if prediction726 == 12
        _t1445 = parse_boolean_value(parser)
        boolean_value738 = _t1445
        _t1446 = Proto.Value(value=OneOf(:boolean_value, boolean_value738))
        _t1444 = _t1446
    else
        if prediction726 == 11
            consume_literal!(parser, "missing")
            _t1448 = Proto.MissingValue()
            _t1449 = Proto.Value(value=OneOf(:missing_value, _t1448))
            _t1447 = _t1449
        else
            if prediction726 == 10
                decimal737 = consume_terminal!(parser, "DECIMAL")
                _t1451 = Proto.Value(value=OneOf(:decimal_value, decimal737))
                _t1450 = _t1451
            else
                if prediction726 == 9
                    int128736 = consume_terminal!(parser, "INT128")
                    _t1453 = Proto.Value(value=OneOf(:int128_value, int128736))
                    _t1452 = _t1453
                else
                    if prediction726 == 8
                        uint128735 = consume_terminal!(parser, "UINT128")
                        _t1455 = Proto.Value(value=OneOf(:uint128_value, uint128735))
                        _t1454 = _t1455
                    else
                        if prediction726 == 7
                            uint32734 = consume_terminal!(parser, "UINT32")
                            _t1457 = Proto.Value(value=OneOf(:uint32_value, uint32734))
                            _t1456 = _t1457
                        else
                            if prediction726 == 6
                                float733 = consume_terminal!(parser, "FLOAT")
                                _t1459 = Proto.Value(value=OneOf(:float_value, float733))
                                _t1458 = _t1459
                            else
                                if prediction726 == 5
                                    float32732 = consume_terminal!(parser, "FLOAT32")
                                    _t1461 = Proto.Value(value=OneOf(:float32_value, float32732))
                                    _t1460 = _t1461
                                else
                                    if prediction726 == 4
                                        int731 = consume_terminal!(parser, "INT")
                                        _t1463 = Proto.Value(value=OneOf(:int_value, int731))
                                        _t1462 = _t1463
                                    else
                                        if prediction726 == 3
                                            int32730 = consume_terminal!(parser, "INT32")
                                            _t1465 = Proto.Value(value=OneOf(:int32_value, int32730))
                                            _t1464 = _t1465
                                        else
                                            if prediction726 == 2
                                                string729 = consume_terminal!(parser, "STRING")
                                                _t1467 = Proto.Value(value=OneOf(:string_value, string729))
                                                _t1466 = _t1467
                                            else
                                                if prediction726 == 1
                                                    _t1469 = parse_raw_datetime(parser)
                                                    raw_datetime728 = _t1469
                                                    _t1470 = Proto.Value(value=OneOf(:datetime_value, raw_datetime728))
                                                    _t1468 = _t1470
                                                else
                                                    if prediction726 == 0
                                                        _t1472 = parse_raw_date(parser)
                                                        raw_date727 = _t1472
                                                        _t1473 = Proto.Value(value=OneOf(:date_value, raw_date727))
                                                        _t1471 = _t1473
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1468 = _t1471
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
                        _t1454 = _t1456
                    end
                    _t1452 = _t1454
                end
                _t1450 = _t1452
            end
            _t1447 = _t1450
        end
        _t1444 = _t1447
    end
    result740 = _t1444
    record_span!(parser, span_start739, "Value")
    return result740
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start744 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int741 = consume_terminal!(parser, "INT")
    int_3742 = consume_terminal!(parser, "INT")
    int_4743 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1474 = Proto.DateValue(year=Int32(int741), month=Int32(int_3742), day=Int32(int_4743))
    result745 = _t1474
    record_span!(parser, span_start744, "DateValue")
    return result745
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start753 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int746 = consume_terminal!(parser, "INT")
    int_3747 = consume_terminal!(parser, "INT")
    int_4748 = consume_terminal!(parser, "INT")
    int_5749 = consume_terminal!(parser, "INT")
    int_6750 = consume_terminal!(parser, "INT")
    int_7751 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1475 = consume_terminal!(parser, "INT")
    else
        _t1475 = nothing
    end
    int_8752 = _t1475
    consume_literal!(parser, ")")
    _t1476 = Proto.DateTimeValue(year=Int32(int746), month=Int32(int_3747), day=Int32(int_4748), hour=Int32(int_5749), minute=Int32(int_6750), second=Int32(int_7751), microsecond=Int32((!isnothing(int_8752) ? int_8752 : 0)))
    result754 = _t1476
    record_span!(parser, span_start753, "DateTimeValue")
    return result754
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1477 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1478 = 1
        else
            _t1478 = -1
        end
        _t1477 = _t1478
    end
    prediction755 = _t1477
    if prediction755 == 1
        consume_literal!(parser, "false")
        _t1479 = false
    else
        if prediction755 == 0
            consume_literal!(parser, "true")
            _t1480 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1479 = _t1480
    end
    return _t1479
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start760 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs756 = Proto.FragmentId[]
    cond757 = match_lookahead_literal(parser, ":", 0)
    while cond757
        _t1481 = parse_fragment_id(parser)
        item758 = _t1481
        push!(xs756, item758)
        cond757 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids759 = xs756
    consume_literal!(parser, ")")
    _t1482 = Proto.Sync(fragments=fragment_ids759)
    result761 = _t1482
    record_span!(parser, span_start760, "Sync")
    return result761
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start763 = span_start(parser)
    consume_literal!(parser, ":")
    symbol762 = consume_terminal!(parser, "SYMBOL")
    result764 = Proto.FragmentId(Vector{UInt8}(symbol762))
    record_span!(parser, span_start763, "FragmentId")
    return result764
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start767 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1484 = parse_epoch_writes(parser)
        _t1483 = _t1484
    else
        _t1483 = nothing
    end
    epoch_writes765 = _t1483
    if match_lookahead_literal(parser, "(", 0)
        _t1486 = parse_epoch_reads(parser)
        _t1485 = _t1486
    else
        _t1485 = nothing
    end
    epoch_reads766 = _t1485
    consume_literal!(parser, ")")
    _t1487 = Proto.Epoch(writes=(!isnothing(epoch_writes765) ? epoch_writes765 : Proto.Write[]), reads=(!isnothing(epoch_reads766) ? epoch_reads766 : Proto.Read[]))
    result768 = _t1487
    record_span!(parser, span_start767, "Epoch")
    return result768
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs769 = Proto.Write[]
    cond770 = match_lookahead_literal(parser, "(", 0)
    while cond770
        _t1488 = parse_write(parser)
        item771 = _t1488
        push!(xs769, item771)
        cond770 = match_lookahead_literal(parser, "(", 0)
    end
    writes772 = xs769
    consume_literal!(parser, ")")
    return writes772
end

function parse_write(parser::ParserState)::Proto.Write
    span_start778 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1490 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1491 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1492 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1493 = 2
                    else
                        _t1493 = -1
                    end
                    _t1492 = _t1493
                end
                _t1491 = _t1492
            end
            _t1490 = _t1491
        end
        _t1489 = _t1490
    else
        _t1489 = -1
    end
    prediction773 = _t1489
    if prediction773 == 3
        _t1495 = parse_snapshot(parser)
        snapshot777 = _t1495
        _t1496 = Proto.Write(write_type=OneOf(:snapshot, snapshot777))
        _t1494 = _t1496
    else
        if prediction773 == 2
            _t1498 = parse_context(parser)
            context776 = _t1498
            _t1499 = Proto.Write(write_type=OneOf(:context, context776))
            _t1497 = _t1499
        else
            if prediction773 == 1
                _t1501 = parse_undefine(parser)
                undefine775 = _t1501
                _t1502 = Proto.Write(write_type=OneOf(:undefine, undefine775))
                _t1500 = _t1502
            else
                if prediction773 == 0
                    _t1504 = parse_define(parser)
                    define774 = _t1504
                    _t1505 = Proto.Write(write_type=OneOf(:define, define774))
                    _t1503 = _t1505
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1500 = _t1503
            end
            _t1497 = _t1500
        end
        _t1494 = _t1497
    end
    result779 = _t1494
    record_span!(parser, span_start778, "Write")
    return result779
end

function parse_define(parser::ParserState)::Proto.Define
    span_start781 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1506 = parse_fragment(parser)
    fragment780 = _t1506
    consume_literal!(parser, ")")
    _t1507 = Proto.Define(fragment=fragment780)
    result782 = _t1507
    record_span!(parser, span_start781, "Define")
    return result782
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start788 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1508 = parse_new_fragment_id(parser)
    new_fragment_id783 = _t1508
    xs784 = Proto.Declaration[]
    cond785 = match_lookahead_literal(parser, "(", 0)
    while cond785
        _t1509 = parse_declaration(parser)
        item786 = _t1509
        push!(xs784, item786)
        cond785 = match_lookahead_literal(parser, "(", 0)
    end
    declarations787 = xs784
    consume_literal!(parser, ")")
    result789 = construct_fragment(parser, new_fragment_id783, declarations787)
    record_span!(parser, span_start788, "Fragment")
    return result789
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start791 = span_start(parser)
    _t1510 = parse_fragment_id(parser)
    fragment_id790 = _t1510
    start_fragment!(parser, fragment_id790)
    result792 = fragment_id790
    record_span!(parser, span_start791, "FragmentId")
    return result792
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start798 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1512 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1513 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1514 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1515 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1516 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1517 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1518 = 1
                                else
                                    _t1518 = -1
                                end
                                _t1517 = _t1518
                            end
                            _t1516 = _t1517
                        end
                        _t1515 = _t1516
                    end
                    _t1514 = _t1515
                end
                _t1513 = _t1514
            end
            _t1512 = _t1513
        end
        _t1511 = _t1512
    else
        _t1511 = -1
    end
    prediction793 = _t1511
    if prediction793 == 3
        _t1520 = parse_data(parser)
        data797 = _t1520
        _t1521 = Proto.Declaration(declaration_type=OneOf(:data, data797))
        _t1519 = _t1521
    else
        if prediction793 == 2
            _t1523 = parse_constraint(parser)
            constraint796 = _t1523
            _t1524 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint796))
            _t1522 = _t1524
        else
            if prediction793 == 1
                _t1526 = parse_algorithm(parser)
                algorithm795 = _t1526
                _t1527 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm795))
                _t1525 = _t1527
            else
                if prediction793 == 0
                    _t1529 = parse_def(parser)
                    def794 = _t1529
                    _t1530 = Proto.Declaration(declaration_type=OneOf(:def, def794))
                    _t1528 = _t1530
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1525 = _t1528
            end
            _t1522 = _t1525
        end
        _t1519 = _t1522
    end
    result799 = _t1519
    record_span!(parser, span_start798, "Declaration")
    return result799
end

function parse_def(parser::ParserState)::Proto.Def
    span_start803 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1531 = parse_relation_id(parser)
    relation_id800 = _t1531
    _t1532 = parse_abstraction(parser)
    abstraction801 = _t1532
    if match_lookahead_literal(parser, "(", 0)
        _t1534 = parse_attrs(parser)
        _t1533 = _t1534
    else
        _t1533 = nothing
    end
    attrs802 = _t1533
    consume_literal!(parser, ")")
    _t1535 = Proto.Def(name=relation_id800, body=abstraction801, attrs=(!isnothing(attrs802) ? attrs802 : Proto.Attribute[]))
    result804 = _t1535
    record_span!(parser, span_start803, "Def")
    return result804
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start808 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1536 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1537 = 1
        else
            _t1537 = -1
        end
        _t1536 = _t1537
    end
    prediction805 = _t1536
    if prediction805 == 1
        uint128807 = consume_terminal!(parser, "UINT128")
        _t1538 = Proto.RelationId(uint128807.low, uint128807.high)
    else
        if prediction805 == 0
            consume_literal!(parser, ":")
            symbol806 = consume_terminal!(parser, "SYMBOL")
            _t1539 = relation_id_from_string(parser, symbol806)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1538 = _t1539
    end
    result809 = _t1538
    record_span!(parser, span_start808, "RelationId")
    return result809
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start812 = span_start(parser)
    consume_literal!(parser, "(")
    _t1540 = parse_bindings(parser)
    bindings810 = _t1540
    _t1541 = parse_formula(parser)
    formula811 = _t1541
    consume_literal!(parser, ")")
    _t1542 = Proto.Abstraction(vars=vcat(bindings810[1], !isnothing(bindings810[2]) ? bindings810[2] : []), value=formula811)
    result813 = _t1542
    record_span!(parser, span_start812, "Abstraction")
    return result813
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs814 = Proto.Binding[]
    cond815 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond815
        _t1543 = parse_binding(parser)
        item816 = _t1543
        push!(xs814, item816)
        cond815 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings817 = xs814
    if match_lookahead_literal(parser, "|", 0)
        _t1545 = parse_value_bindings(parser)
        _t1544 = _t1545
    else
        _t1544 = nothing
    end
    value_bindings818 = _t1544
    consume_literal!(parser, "]")
    return (bindings817, (!isnothing(value_bindings818) ? value_bindings818 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start821 = span_start(parser)
    symbol819 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1546 = parse_type(parser)
    type820 = _t1546
    _t1547 = Proto.Var(name=symbol819)
    _t1548 = Proto.Binding(var=_t1547, var"#type"=type820)
    result822 = _t1548
    record_span!(parser, span_start821, "Binding")
    return result822
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start838 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1549 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1550 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1551 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1552 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1553 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1554 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1555 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1556 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1557 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1558 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1559 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1560 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1561 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1562 = 9
                                                        else
                                                            _t1562 = -1
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
    prediction823 = _t1549
    if prediction823 == 13
        _t1564 = parse_uint32_type(parser)
        uint32_type837 = _t1564
        _t1565 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type837))
        _t1563 = _t1565
    else
        if prediction823 == 12
            _t1567 = parse_float32_type(parser)
            float32_type836 = _t1567
            _t1568 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type836))
            _t1566 = _t1568
        else
            if prediction823 == 11
                _t1570 = parse_int32_type(parser)
                int32_type835 = _t1570
                _t1571 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type835))
                _t1569 = _t1571
            else
                if prediction823 == 10
                    _t1573 = parse_boolean_type(parser)
                    boolean_type834 = _t1573
                    _t1574 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type834))
                    _t1572 = _t1574
                else
                    if prediction823 == 9
                        _t1576 = parse_decimal_type(parser)
                        decimal_type833 = _t1576
                        _t1577 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type833))
                        _t1575 = _t1577
                    else
                        if prediction823 == 8
                            _t1579 = parse_missing_type(parser)
                            missing_type832 = _t1579
                            _t1580 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type832))
                            _t1578 = _t1580
                        else
                            if prediction823 == 7
                                _t1582 = parse_datetime_type(parser)
                                datetime_type831 = _t1582
                                _t1583 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type831))
                                _t1581 = _t1583
                            else
                                if prediction823 == 6
                                    _t1585 = parse_date_type(parser)
                                    date_type830 = _t1585
                                    _t1586 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type830))
                                    _t1584 = _t1586
                                else
                                    if prediction823 == 5
                                        _t1588 = parse_int128_type(parser)
                                        int128_type829 = _t1588
                                        _t1589 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type829))
                                        _t1587 = _t1589
                                    else
                                        if prediction823 == 4
                                            _t1591 = parse_uint128_type(parser)
                                            uint128_type828 = _t1591
                                            _t1592 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type828))
                                            _t1590 = _t1592
                                        else
                                            if prediction823 == 3
                                                _t1594 = parse_float_type(parser)
                                                float_type827 = _t1594
                                                _t1595 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type827))
                                                _t1593 = _t1595
                                            else
                                                if prediction823 == 2
                                                    _t1597 = parse_int_type(parser)
                                                    int_type826 = _t1597
                                                    _t1598 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type826))
                                                    _t1596 = _t1598
                                                else
                                                    if prediction823 == 1
                                                        _t1600 = parse_string_type(parser)
                                                        string_type825 = _t1600
                                                        _t1601 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type825))
                                                        _t1599 = _t1601
                                                    else
                                                        if prediction823 == 0
                                                            _t1603 = parse_unspecified_type(parser)
                                                            unspecified_type824 = _t1603
                                                            _t1604 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type824))
                                                            _t1602 = _t1604
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
            _t1566 = _t1569
        end
        _t1563 = _t1566
    end
    result839 = _t1563
    record_span!(parser, span_start838, "Type")
    return result839
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start840 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1605 = Proto.UnspecifiedType()
    result841 = _t1605
    record_span!(parser, span_start840, "UnspecifiedType")
    return result841
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start842 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1606 = Proto.StringType()
    result843 = _t1606
    record_span!(parser, span_start842, "StringType")
    return result843
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start844 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1607 = Proto.IntType()
    result845 = _t1607
    record_span!(parser, span_start844, "IntType")
    return result845
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start846 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1608 = Proto.FloatType()
    result847 = _t1608
    record_span!(parser, span_start846, "FloatType")
    return result847
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start848 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1609 = Proto.UInt128Type()
    result849 = _t1609
    record_span!(parser, span_start848, "UInt128Type")
    return result849
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start850 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1610 = Proto.Int128Type()
    result851 = _t1610
    record_span!(parser, span_start850, "Int128Type")
    return result851
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start852 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1611 = Proto.DateType()
    result853 = _t1611
    record_span!(parser, span_start852, "DateType")
    return result853
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start854 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1612 = Proto.DateTimeType()
    result855 = _t1612
    record_span!(parser, span_start854, "DateTimeType")
    return result855
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start856 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1613 = Proto.MissingType()
    result857 = _t1613
    record_span!(parser, span_start856, "MissingType")
    return result857
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start860 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int858 = consume_terminal!(parser, "INT")
    int_3859 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1614 = Proto.DecimalType(precision=Int32(int858), scale=Int32(int_3859))
    result861 = _t1614
    record_span!(parser, span_start860, "DecimalType")
    return result861
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start862 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1615 = Proto.BooleanType()
    result863 = _t1615
    record_span!(parser, span_start862, "BooleanType")
    return result863
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start864 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1616 = Proto.Int32Type()
    result865 = _t1616
    record_span!(parser, span_start864, "Int32Type")
    return result865
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start866 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1617 = Proto.Float32Type()
    result867 = _t1617
    record_span!(parser, span_start866, "Float32Type")
    return result867
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start868 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1618 = Proto.UInt32Type()
    result869 = _t1618
    record_span!(parser, span_start868, "UInt32Type")
    return result869
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs870 = Proto.Binding[]
    cond871 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond871
        _t1619 = parse_binding(parser)
        item872 = _t1619
        push!(xs870, item872)
        cond871 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings873 = xs870
    return bindings873
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start888 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1621 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1622 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1623 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1624 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1625 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1626 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1627 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1628 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1629 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1630 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1631 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1632 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1633 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1634 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1635 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1636 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1637 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1638 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1639 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1640 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1641 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1642 = 10
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
        _t1620 = _t1621
    else
        _t1620 = -1
    end
    prediction874 = _t1620
    if prediction874 == 12
        _t1644 = parse_cast(parser)
        cast887 = _t1644
        _t1645 = Proto.Formula(formula_type=OneOf(:cast, cast887))
        _t1643 = _t1645
    else
        if prediction874 == 11
            _t1647 = parse_rel_atom(parser)
            rel_atom886 = _t1647
            _t1648 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom886))
            _t1646 = _t1648
        else
            if prediction874 == 10
                _t1650 = parse_primitive(parser)
                primitive885 = _t1650
                _t1651 = Proto.Formula(formula_type=OneOf(:primitive, primitive885))
                _t1649 = _t1651
            else
                if prediction874 == 9
                    _t1653 = parse_pragma(parser)
                    pragma884 = _t1653
                    _t1654 = Proto.Formula(formula_type=OneOf(:pragma, pragma884))
                    _t1652 = _t1654
                else
                    if prediction874 == 8
                        _t1656 = parse_atom(parser)
                        atom883 = _t1656
                        _t1657 = Proto.Formula(formula_type=OneOf(:atom, atom883))
                        _t1655 = _t1657
                    else
                        if prediction874 == 7
                            _t1659 = parse_ffi(parser)
                            ffi882 = _t1659
                            _t1660 = Proto.Formula(formula_type=OneOf(:ffi, ffi882))
                            _t1658 = _t1660
                        else
                            if prediction874 == 6
                                _t1662 = parse_not(parser)
                                not881 = _t1662
                                _t1663 = Proto.Formula(formula_type=OneOf(:not, not881))
                                _t1661 = _t1663
                            else
                                if prediction874 == 5
                                    _t1665 = parse_disjunction(parser)
                                    disjunction880 = _t1665
                                    _t1666 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction880))
                                    _t1664 = _t1666
                                else
                                    if prediction874 == 4
                                        _t1668 = parse_conjunction(parser)
                                        conjunction879 = _t1668
                                        _t1669 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction879))
                                        _t1667 = _t1669
                                    else
                                        if prediction874 == 3
                                            _t1671 = parse_reduce(parser)
                                            reduce878 = _t1671
                                            _t1672 = Proto.Formula(formula_type=OneOf(:reduce, reduce878))
                                            _t1670 = _t1672
                                        else
                                            if prediction874 == 2
                                                _t1674 = parse_exists(parser)
                                                exists877 = _t1674
                                                _t1675 = Proto.Formula(formula_type=OneOf(:exists, exists877))
                                                _t1673 = _t1675
                                            else
                                                if prediction874 == 1
                                                    _t1677 = parse_false(parser)
                                                    false876 = _t1677
                                                    _t1678 = Proto.Formula(formula_type=OneOf(:disjunction, false876))
                                                    _t1676 = _t1678
                                                else
                                                    if prediction874 == 0
                                                        _t1680 = parse_true(parser)
                                                        true875 = _t1680
                                                        _t1681 = Proto.Formula(formula_type=OneOf(:conjunction, true875))
                                                        _t1679 = _t1681
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
            _t1646 = _t1649
        end
        _t1643 = _t1646
    end
    result889 = _t1643
    record_span!(parser, span_start888, "Formula")
    return result889
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start890 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1682 = Proto.Conjunction(args=Proto.Formula[])
    result891 = _t1682
    record_span!(parser, span_start890, "Conjunction")
    return result891
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start892 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1683 = Proto.Disjunction(args=Proto.Formula[])
    result893 = _t1683
    record_span!(parser, span_start892, "Disjunction")
    return result893
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start896 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1684 = parse_bindings(parser)
    bindings894 = _t1684
    _t1685 = parse_formula(parser)
    formula895 = _t1685
    consume_literal!(parser, ")")
    _t1686 = Proto.Abstraction(vars=vcat(bindings894[1], !isnothing(bindings894[2]) ? bindings894[2] : []), value=formula895)
    _t1687 = Proto.Exists(body=_t1686)
    result897 = _t1687
    record_span!(parser, span_start896, "Exists")
    return result897
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start901 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1688 = parse_abstraction(parser)
    abstraction898 = _t1688
    _t1689 = parse_abstraction(parser)
    abstraction_3899 = _t1689
    _t1690 = parse_terms(parser)
    terms900 = _t1690
    consume_literal!(parser, ")")
    _t1691 = Proto.Reduce(op=abstraction898, body=abstraction_3899, terms=terms900)
    result902 = _t1691
    record_span!(parser, span_start901, "Reduce")
    return result902
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs903 = Proto.Term[]
    cond904 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond904
        _t1692 = parse_term(parser)
        item905 = _t1692
        push!(xs903, item905)
        cond904 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms906 = xs903
    consume_literal!(parser, ")")
    return terms906
end

function parse_term(parser::ParserState)::Proto.Term
    span_start910 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1693 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1694 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1695 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1696 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1697 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1698 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1699 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1700 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1701 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1702 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1703 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1704 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1705 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1706 = 1
                                                        else
                                                            _t1706 = -1
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
                            _t1698 = _t1699
                        end
                        _t1697 = _t1698
                    end
                    _t1696 = _t1697
                end
                _t1695 = _t1696
            end
            _t1694 = _t1695
        end
        _t1693 = _t1694
    end
    prediction907 = _t1693
    if prediction907 == 1
        _t1708 = parse_value(parser)
        value909 = _t1708
        _t1709 = Proto.Term(term_type=OneOf(:constant, value909))
        _t1707 = _t1709
    else
        if prediction907 == 0
            _t1711 = parse_var(parser)
            var908 = _t1711
            _t1712 = Proto.Term(term_type=OneOf(:var, var908))
            _t1710 = _t1712
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1707 = _t1710
    end
    result911 = _t1707
    record_span!(parser, span_start910, "Term")
    return result911
end

function parse_var(parser::ParserState)::Proto.Var
    span_start913 = span_start(parser)
    symbol912 = consume_terminal!(parser, "SYMBOL")
    _t1713 = Proto.Var(name=symbol912)
    result914 = _t1713
    record_span!(parser, span_start913, "Var")
    return result914
end

function parse_value(parser::ParserState)::Proto.Value
    span_start928 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1714 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1715 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1716 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1718 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1719 = 0
                        else
                            _t1719 = -1
                        end
                        _t1718 = _t1719
                    end
                    _t1717 = _t1718
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1720 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1721 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1722 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1723 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1724 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1725 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1726 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1727 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1728 = 10
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
                    _t1717 = _t1720
                end
                _t1716 = _t1717
            end
            _t1715 = _t1716
        end
        _t1714 = _t1715
    end
    prediction915 = _t1714
    if prediction915 == 12
        _t1730 = parse_boolean_value(parser)
        boolean_value927 = _t1730
        _t1731 = Proto.Value(value=OneOf(:boolean_value, boolean_value927))
        _t1729 = _t1731
    else
        if prediction915 == 11
            consume_literal!(parser, "missing")
            _t1733 = Proto.MissingValue()
            _t1734 = Proto.Value(value=OneOf(:missing_value, _t1733))
            _t1732 = _t1734
        else
            if prediction915 == 10
                formatted_decimal926 = consume_terminal!(parser, "DECIMAL")
                _t1736 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal926))
                _t1735 = _t1736
            else
                if prediction915 == 9
                    formatted_int128925 = consume_terminal!(parser, "INT128")
                    _t1738 = Proto.Value(value=OneOf(:int128_value, formatted_int128925))
                    _t1737 = _t1738
                else
                    if prediction915 == 8
                        formatted_uint128924 = consume_terminal!(parser, "UINT128")
                        _t1740 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128924))
                        _t1739 = _t1740
                    else
                        if prediction915 == 7
                            formatted_uint32923 = consume_terminal!(parser, "UINT32")
                            _t1742 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32923))
                            _t1741 = _t1742
                        else
                            if prediction915 == 6
                                formatted_float922 = consume_terminal!(parser, "FLOAT")
                                _t1744 = Proto.Value(value=OneOf(:float_value, formatted_float922))
                                _t1743 = _t1744
                            else
                                if prediction915 == 5
                                    formatted_float32921 = consume_terminal!(parser, "FLOAT32")
                                    _t1746 = Proto.Value(value=OneOf(:float32_value, formatted_float32921))
                                    _t1745 = _t1746
                                else
                                    if prediction915 == 4
                                        formatted_int920 = consume_terminal!(parser, "INT")
                                        _t1748 = Proto.Value(value=OneOf(:int_value, formatted_int920))
                                        _t1747 = _t1748
                                    else
                                        if prediction915 == 3
                                            formatted_int32919 = consume_terminal!(parser, "INT32")
                                            _t1750 = Proto.Value(value=OneOf(:int32_value, formatted_int32919))
                                            _t1749 = _t1750
                                        else
                                            if prediction915 == 2
                                                formatted_string918 = consume_terminal!(parser, "STRING")
                                                _t1752 = Proto.Value(value=OneOf(:string_value, formatted_string918))
                                                _t1751 = _t1752
                                            else
                                                if prediction915 == 1
                                                    _t1754 = parse_datetime(parser)
                                                    datetime917 = _t1754
                                                    _t1755 = Proto.Value(value=OneOf(:datetime_value, datetime917))
                                                    _t1753 = _t1755
                                                else
                                                    if prediction915 == 0
                                                        _t1757 = parse_date(parser)
                                                        date916 = _t1757
                                                        _t1758 = Proto.Value(value=OneOf(:date_value, date916))
                                                        _t1756 = _t1758
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1753 = _t1756
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
                        _t1739 = _t1741
                    end
                    _t1737 = _t1739
                end
                _t1735 = _t1737
            end
            _t1732 = _t1735
        end
        _t1729 = _t1732
    end
    result929 = _t1729
    record_span!(parser, span_start928, "Value")
    return result929
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start933 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int930 = consume_terminal!(parser, "INT")
    formatted_int_3931 = consume_terminal!(parser, "INT")
    formatted_int_4932 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1759 = Proto.DateValue(year=Int32(formatted_int930), month=Int32(formatted_int_3931), day=Int32(formatted_int_4932))
    result934 = _t1759
    record_span!(parser, span_start933, "DateValue")
    return result934
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start942 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int935 = consume_terminal!(parser, "INT")
    formatted_int_3936 = consume_terminal!(parser, "INT")
    formatted_int_4937 = consume_terminal!(parser, "INT")
    formatted_int_5938 = consume_terminal!(parser, "INT")
    formatted_int_6939 = consume_terminal!(parser, "INT")
    formatted_int_7940 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1760 = consume_terminal!(parser, "INT")
    else
        _t1760 = nothing
    end
    formatted_int_8941 = _t1760
    consume_literal!(parser, ")")
    _t1761 = Proto.DateTimeValue(year=Int32(formatted_int935), month=Int32(formatted_int_3936), day=Int32(formatted_int_4937), hour=Int32(formatted_int_5938), minute=Int32(formatted_int_6939), second=Int32(formatted_int_7940), microsecond=Int32((!isnothing(formatted_int_8941) ? formatted_int_8941 : 0)))
    result943 = _t1761
    record_span!(parser, span_start942, "DateTimeValue")
    return result943
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start948 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs944 = Proto.Formula[]
    cond945 = match_lookahead_literal(parser, "(", 0)
    while cond945
        _t1762 = parse_formula(parser)
        item946 = _t1762
        push!(xs944, item946)
        cond945 = match_lookahead_literal(parser, "(", 0)
    end
    formulas947 = xs944
    consume_literal!(parser, ")")
    _t1763 = Proto.Conjunction(args=formulas947)
    result949 = _t1763
    record_span!(parser, span_start948, "Conjunction")
    return result949
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start954 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs950 = Proto.Formula[]
    cond951 = match_lookahead_literal(parser, "(", 0)
    while cond951
        _t1764 = parse_formula(parser)
        item952 = _t1764
        push!(xs950, item952)
        cond951 = match_lookahead_literal(parser, "(", 0)
    end
    formulas953 = xs950
    consume_literal!(parser, ")")
    _t1765 = Proto.Disjunction(args=formulas953)
    result955 = _t1765
    record_span!(parser, span_start954, "Disjunction")
    return result955
end

function parse_not(parser::ParserState)::Proto.Not
    span_start957 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1766 = parse_formula(parser)
    formula956 = _t1766
    consume_literal!(parser, ")")
    _t1767 = Proto.Not(arg=formula956)
    result958 = _t1767
    record_span!(parser, span_start957, "Not")
    return result958
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start962 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1768 = parse_name(parser)
    name959 = _t1768
    _t1769 = parse_ffi_args(parser)
    ffi_args960 = _t1769
    _t1770 = parse_terms(parser)
    terms961 = _t1770
    consume_literal!(parser, ")")
    _t1771 = Proto.FFI(name=name959, args=ffi_args960, terms=terms961)
    result963 = _t1771
    record_span!(parser, span_start962, "FFI")
    return result963
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol964 = consume_terminal!(parser, "SYMBOL")
    return symbol964
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs965 = Proto.Abstraction[]
    cond966 = match_lookahead_literal(parser, "(", 0)
    while cond966
        _t1772 = parse_abstraction(parser)
        item967 = _t1772
        push!(xs965, item967)
        cond966 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions968 = xs965
    consume_literal!(parser, ")")
    return abstractions968
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1773 = parse_relation_id(parser)
    relation_id969 = _t1773
    xs970 = Proto.Term[]
    cond971 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond971
        _t1774 = parse_term(parser)
        item972 = _t1774
        push!(xs970, item972)
        cond971 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms973 = xs970
    consume_literal!(parser, ")")
    _t1775 = Proto.Atom(name=relation_id969, terms=terms973)
    result975 = _t1775
    record_span!(parser, span_start974, "Atom")
    return result975
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start981 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1776 = parse_name(parser)
    name976 = _t1776
    xs977 = Proto.Term[]
    cond978 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond978
        _t1777 = parse_term(parser)
        item979 = _t1777
        push!(xs977, item979)
        cond978 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms980 = xs977
    consume_literal!(parser, ")")
    _t1778 = Proto.Pragma(name=name976, terms=terms980)
    result982 = _t1778
    record_span!(parser, span_start981, "Pragma")
    return result982
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start998 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1780 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1781 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1782 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1783 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1784 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1785 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1786 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1787 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1788 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1789 = 7
                                            else
                                                _t1789 = -1
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
            _t1780 = _t1781
        end
        _t1779 = _t1780
    else
        _t1779 = -1
    end
    prediction983 = _t1779
    if prediction983 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1791 = parse_name(parser)
        name993 = _t1791
        xs994 = Proto.RelTerm[]
        cond995 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond995
            _t1792 = parse_rel_term(parser)
            item996 = _t1792
            push!(xs994, item996)
            cond995 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms997 = xs994
        consume_literal!(parser, ")")
        _t1793 = Proto.Primitive(name=name993, terms=rel_terms997)
        _t1790 = _t1793
    else
        if prediction983 == 8
            _t1795 = parse_divide(parser)
            divide992 = _t1795
            _t1794 = divide992
        else
            if prediction983 == 7
                _t1797 = parse_multiply(parser)
                multiply991 = _t1797
                _t1796 = multiply991
            else
                if prediction983 == 6
                    _t1799 = parse_minus(parser)
                    minus990 = _t1799
                    _t1798 = minus990
                else
                    if prediction983 == 5
                        _t1801 = parse_add(parser)
                        add989 = _t1801
                        _t1800 = add989
                    else
                        if prediction983 == 4
                            _t1803 = parse_gt_eq(parser)
                            gt_eq988 = _t1803
                            _t1802 = gt_eq988
                        else
                            if prediction983 == 3
                                _t1805 = parse_gt(parser)
                                gt987 = _t1805
                                _t1804 = gt987
                            else
                                if prediction983 == 2
                                    _t1807 = parse_lt_eq(parser)
                                    lt_eq986 = _t1807
                                    _t1806 = lt_eq986
                                else
                                    if prediction983 == 1
                                        _t1809 = parse_lt(parser)
                                        lt985 = _t1809
                                        _t1808 = lt985
                                    else
                                        if prediction983 == 0
                                            _t1811 = parse_eq(parser)
                                            eq984 = _t1811
                                            _t1810 = eq984
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
                    _t1798 = _t1800
                end
                _t1796 = _t1798
            end
            _t1794 = _t1796
        end
        _t1790 = _t1794
    end
    result999 = _t1790
    record_span!(parser, span_start998, "Primitive")
    return result999
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start1002 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1812 = parse_term(parser)
    term1000 = _t1812
    _t1813 = parse_term(parser)
    term_31001 = _t1813
    consume_literal!(parser, ")")
    _t1814 = Proto.RelTerm(rel_term_type=OneOf(:term, term1000))
    _t1815 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31001))
    _t1816 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1814, _t1815])
    result1003 = _t1816
    record_span!(parser, span_start1002, "Primitive")
    return result1003
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start1006 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1817 = parse_term(parser)
    term1004 = _t1817
    _t1818 = parse_term(parser)
    term_31005 = _t1818
    consume_literal!(parser, ")")
    _t1819 = Proto.RelTerm(rel_term_type=OneOf(:term, term1004))
    _t1820 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31005))
    _t1821 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1819, _t1820])
    result1007 = _t1821
    record_span!(parser, span_start1006, "Primitive")
    return result1007
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start1010 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1822 = parse_term(parser)
    term1008 = _t1822
    _t1823 = parse_term(parser)
    term_31009 = _t1823
    consume_literal!(parser, ")")
    _t1824 = Proto.RelTerm(rel_term_type=OneOf(:term, term1008))
    _t1825 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31009))
    _t1826 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1824, _t1825])
    result1011 = _t1826
    record_span!(parser, span_start1010, "Primitive")
    return result1011
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start1014 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1827 = parse_term(parser)
    term1012 = _t1827
    _t1828 = parse_term(parser)
    term_31013 = _t1828
    consume_literal!(parser, ")")
    _t1829 = Proto.RelTerm(rel_term_type=OneOf(:term, term1012))
    _t1830 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31013))
    _t1831 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1829, _t1830])
    result1015 = _t1831
    record_span!(parser, span_start1014, "Primitive")
    return result1015
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start1018 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1832 = parse_term(parser)
    term1016 = _t1832
    _t1833 = parse_term(parser)
    term_31017 = _t1833
    consume_literal!(parser, ")")
    _t1834 = Proto.RelTerm(rel_term_type=OneOf(:term, term1016))
    _t1835 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31017))
    _t1836 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1834, _t1835])
    result1019 = _t1836
    record_span!(parser, span_start1018, "Primitive")
    return result1019
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start1023 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1837 = parse_term(parser)
    term1020 = _t1837
    _t1838 = parse_term(parser)
    term_31021 = _t1838
    _t1839 = parse_term(parser)
    term_41022 = _t1839
    consume_literal!(parser, ")")
    _t1840 = Proto.RelTerm(rel_term_type=OneOf(:term, term1020))
    _t1841 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31021))
    _t1842 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41022))
    _t1843 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1840, _t1841, _t1842])
    result1024 = _t1843
    record_span!(parser, span_start1023, "Primitive")
    return result1024
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start1028 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1844 = parse_term(parser)
    term1025 = _t1844
    _t1845 = parse_term(parser)
    term_31026 = _t1845
    _t1846 = parse_term(parser)
    term_41027 = _t1846
    consume_literal!(parser, ")")
    _t1847 = Proto.RelTerm(rel_term_type=OneOf(:term, term1025))
    _t1848 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31026))
    _t1849 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41027))
    _t1850 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1847, _t1848, _t1849])
    result1029 = _t1850
    record_span!(parser, span_start1028, "Primitive")
    return result1029
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1033 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1851 = parse_term(parser)
    term1030 = _t1851
    _t1852 = parse_term(parser)
    term_31031 = _t1852
    _t1853 = parse_term(parser)
    term_41032 = _t1853
    consume_literal!(parser, ")")
    _t1854 = Proto.RelTerm(rel_term_type=OneOf(:term, term1030))
    _t1855 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31031))
    _t1856 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41032))
    _t1857 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1854, _t1855, _t1856])
    result1034 = _t1857
    record_span!(parser, span_start1033, "Primitive")
    return result1034
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1038 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1858 = parse_term(parser)
    term1035 = _t1858
    _t1859 = parse_term(parser)
    term_31036 = _t1859
    _t1860 = parse_term(parser)
    term_41037 = _t1860
    consume_literal!(parser, ")")
    _t1861 = Proto.RelTerm(rel_term_type=OneOf(:term, term1035))
    _t1862 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31036))
    _t1863 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41037))
    _t1864 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1861, _t1862, _t1863])
    result1039 = _t1864
    record_span!(parser, span_start1038, "Primitive")
    return result1039
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1043 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1865 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1866 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1867 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1868 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1869 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1870 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1871 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1872 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1873 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1874 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1875 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1876 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1877 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1878 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1879 = 1
                                                            else
                                                                _t1879 = -1
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
                            _t1870 = _t1871
                        end
                        _t1869 = _t1870
                    end
                    _t1868 = _t1869
                end
                _t1867 = _t1868
            end
            _t1866 = _t1867
        end
        _t1865 = _t1866
    end
    prediction1040 = _t1865
    if prediction1040 == 1
        _t1881 = parse_term(parser)
        term1042 = _t1881
        _t1882 = Proto.RelTerm(rel_term_type=OneOf(:term, term1042))
        _t1880 = _t1882
    else
        if prediction1040 == 0
            _t1884 = parse_specialized_value(parser)
            specialized_value1041 = _t1884
            _t1885 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1041))
            _t1883 = _t1885
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1880 = _t1883
    end
    result1044 = _t1880
    record_span!(parser, span_start1043, "RelTerm")
    return result1044
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1046 = span_start(parser)
    consume_literal!(parser, "#")
    _t1886 = parse_raw_value(parser)
    raw_value1045 = _t1886
    result1047 = raw_value1045
    record_span!(parser, span_start1046, "Value")
    return result1047
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1053 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1887 = parse_name(parser)
    name1048 = _t1887
    xs1049 = Proto.RelTerm[]
    cond1050 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1050
        _t1888 = parse_rel_term(parser)
        item1051 = _t1888
        push!(xs1049, item1051)
        cond1050 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1052 = xs1049
    consume_literal!(parser, ")")
    _t1889 = Proto.RelAtom(name=name1048, terms=rel_terms1052)
    result1054 = _t1889
    record_span!(parser, span_start1053, "RelAtom")
    return result1054
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1057 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1890 = parse_term(parser)
    term1055 = _t1890
    _t1891 = parse_term(parser)
    term_31056 = _t1891
    consume_literal!(parser, ")")
    _t1892 = Proto.Cast(input=term1055, result=term_31056)
    result1058 = _t1892
    record_span!(parser, span_start1057, "Cast")
    return result1058
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1059 = Proto.Attribute[]
    cond1060 = match_lookahead_literal(parser, "(", 0)
    while cond1060
        _t1893 = parse_attribute(parser)
        item1061 = _t1893
        push!(xs1059, item1061)
        cond1060 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1062 = xs1059
    consume_literal!(parser, ")")
    return attributes1062
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1068 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1894 = parse_name(parser)
    name1063 = _t1894
    xs1064 = Proto.Value[]
    cond1065 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1065
        _t1895 = parse_raw_value(parser)
        item1066 = _t1895
        push!(xs1064, item1066)
        cond1065 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1067 = xs1064
    consume_literal!(parser, ")")
    _t1896 = Proto.Attribute(name=name1063, args=raw_values1067)
    result1069 = _t1896
    record_span!(parser, span_start1068, "Attribute")
    return result1069
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1076 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1070 = Proto.RelationId[]
    cond1071 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1071
        _t1897 = parse_relation_id(parser)
        item1072 = _t1897
        push!(xs1070, item1072)
        cond1071 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1073 = xs1070
    _t1898 = parse_script(parser)
    script1074 = _t1898
    if match_lookahead_literal(parser, "(", 0)
        _t1900 = parse_attrs(parser)
        _t1899 = _t1900
    else
        _t1899 = nothing
    end
    attrs1075 = _t1899
    consume_literal!(parser, ")")
    _t1901 = Proto.Algorithm(var"#global"=relation_ids1073, body=script1074, attrs=(!isnothing(attrs1075) ? attrs1075 : Proto.Attribute[]))
    result1077 = _t1901
    record_span!(parser, span_start1076, "Algorithm")
    return result1077
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1082 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1078 = Proto.Construct[]
    cond1079 = match_lookahead_literal(parser, "(", 0)
    while cond1079
        _t1902 = parse_construct(parser)
        item1080 = _t1902
        push!(xs1078, item1080)
        cond1079 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1081 = xs1078
    consume_literal!(parser, ")")
    _t1903 = Proto.Script(constructs=constructs1081)
    result1083 = _t1903
    record_span!(parser, span_start1082, "Script")
    return result1083
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1087 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1905 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1906 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1907 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1908 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1909 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1910 = 1
                            else
                                _t1910 = -1
                            end
                            _t1909 = _t1910
                        end
                        _t1908 = _t1909
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
    prediction1084 = _t1904
    if prediction1084 == 1
        _t1912 = parse_instruction(parser)
        instruction1086 = _t1912
        _t1913 = Proto.Construct(construct_type=OneOf(:instruction, instruction1086))
        _t1911 = _t1913
    else
        if prediction1084 == 0
            _t1915 = parse_loop(parser)
            loop1085 = _t1915
            _t1916 = Proto.Construct(construct_type=OneOf(:loop, loop1085))
            _t1914 = _t1916
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1911 = _t1914
    end
    result1088 = _t1911
    record_span!(parser, span_start1087, "Construct")
    return result1088
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1092 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1917 = parse_init(parser)
    init1089 = _t1917
    _t1918 = parse_script(parser)
    script1090 = _t1918
    if match_lookahead_literal(parser, "(", 0)
        _t1920 = parse_attrs(parser)
        _t1919 = _t1920
    else
        _t1919 = nothing
    end
    attrs1091 = _t1919
    consume_literal!(parser, ")")
    _t1921 = Proto.Loop(init=init1089, body=script1090, attrs=(!isnothing(attrs1091) ? attrs1091 : Proto.Attribute[]))
    result1093 = _t1921
    record_span!(parser, span_start1092, "Loop")
    return result1093
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1094 = Proto.Instruction[]
    cond1095 = match_lookahead_literal(parser, "(", 0)
    while cond1095
        _t1922 = parse_instruction(parser)
        item1096 = _t1922
        push!(xs1094, item1096)
        cond1095 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1097 = xs1094
    consume_literal!(parser, ")")
    return instructions1097
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1104 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1924 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1925 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1926 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1927 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1928 = 0
                        else
                            _t1928 = -1
                        end
                        _t1927 = _t1928
                    end
                    _t1926 = _t1927
                end
                _t1925 = _t1926
            end
            _t1924 = _t1925
        end
        _t1923 = _t1924
    else
        _t1923 = -1
    end
    prediction1098 = _t1923
    if prediction1098 == 4
        _t1930 = parse_monus_def(parser)
        monus_def1103 = _t1930
        _t1931 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1103))
        _t1929 = _t1931
    else
        if prediction1098 == 3
            _t1933 = parse_monoid_def(parser)
            monoid_def1102 = _t1933
            _t1934 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1102))
            _t1932 = _t1934
        else
            if prediction1098 == 2
                _t1936 = parse_break(parser)
                break1101 = _t1936
                _t1937 = Proto.Instruction(instr_type=OneOf(:var"#break", break1101))
                _t1935 = _t1937
            else
                if prediction1098 == 1
                    _t1939 = parse_upsert(parser)
                    upsert1100 = _t1939
                    _t1940 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1100))
                    _t1938 = _t1940
                else
                    if prediction1098 == 0
                        _t1942 = parse_assign(parser)
                        assign1099 = _t1942
                        _t1943 = Proto.Instruction(instr_type=OneOf(:assign, assign1099))
                        _t1941 = _t1943
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1938 = _t1941
                end
                _t1935 = _t1938
            end
            _t1932 = _t1935
        end
        _t1929 = _t1932
    end
    result1105 = _t1929
    record_span!(parser, span_start1104, "Instruction")
    return result1105
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1109 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1944 = parse_relation_id(parser)
    relation_id1106 = _t1944
    _t1945 = parse_abstraction(parser)
    abstraction1107 = _t1945
    if match_lookahead_literal(parser, "(", 0)
        _t1947 = parse_attrs(parser)
        _t1946 = _t1947
    else
        _t1946 = nothing
    end
    attrs1108 = _t1946
    consume_literal!(parser, ")")
    _t1948 = Proto.Assign(name=relation_id1106, body=abstraction1107, attrs=(!isnothing(attrs1108) ? attrs1108 : Proto.Attribute[]))
    result1110 = _t1948
    record_span!(parser, span_start1109, "Assign")
    return result1110
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1114 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1949 = parse_relation_id(parser)
    relation_id1111 = _t1949
    _t1950 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1112 = _t1950
    if match_lookahead_literal(parser, "(", 0)
        _t1952 = parse_attrs(parser)
        _t1951 = _t1952
    else
        _t1951 = nothing
    end
    attrs1113 = _t1951
    consume_literal!(parser, ")")
    _t1953 = Proto.Upsert(name=relation_id1111, body=abstraction_with_arity1112[1], attrs=(!isnothing(attrs1113) ? attrs1113 : Proto.Attribute[]), value_arity=abstraction_with_arity1112[2])
    result1115 = _t1953
    record_span!(parser, span_start1114, "Upsert")
    return result1115
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1954 = parse_bindings(parser)
    bindings1116 = _t1954
    _t1955 = parse_formula(parser)
    formula1117 = _t1955
    consume_literal!(parser, ")")
    _t1956 = Proto.Abstraction(vars=vcat(bindings1116[1], !isnothing(bindings1116[2]) ? bindings1116[2] : []), value=formula1117)
    return (_t1956, length(bindings1116[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1121 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1957 = parse_relation_id(parser)
    relation_id1118 = _t1957
    _t1958 = parse_abstraction(parser)
    abstraction1119 = _t1958
    if match_lookahead_literal(parser, "(", 0)
        _t1960 = parse_attrs(parser)
        _t1959 = _t1960
    else
        _t1959 = nothing
    end
    attrs1120 = _t1959
    consume_literal!(parser, ")")
    _t1961 = Proto.Break(name=relation_id1118, body=abstraction1119, attrs=(!isnothing(attrs1120) ? attrs1120 : Proto.Attribute[]))
    result1122 = _t1961
    record_span!(parser, span_start1121, "Break")
    return result1122
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1127 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1962 = parse_monoid(parser)
    monoid1123 = _t1962
    _t1963 = parse_relation_id(parser)
    relation_id1124 = _t1963
    _t1964 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1125 = _t1964
    if match_lookahead_literal(parser, "(", 0)
        _t1966 = parse_attrs(parser)
        _t1965 = _t1966
    else
        _t1965 = nothing
    end
    attrs1126 = _t1965
    consume_literal!(parser, ")")
    _t1967 = Proto.MonoidDef(monoid=monoid1123, name=relation_id1124, body=abstraction_with_arity1125[1], attrs=(!isnothing(attrs1126) ? attrs1126 : Proto.Attribute[]), value_arity=abstraction_with_arity1125[2])
    result1128 = _t1967
    record_span!(parser, span_start1127, "MonoidDef")
    return result1128
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1134 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1969 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1970 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1971 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1972 = 2
                    else
                        _t1972 = -1
                    end
                    _t1971 = _t1972
                end
                _t1970 = _t1971
            end
            _t1969 = _t1970
        end
        _t1968 = _t1969
    else
        _t1968 = -1
    end
    prediction1129 = _t1968
    if prediction1129 == 3
        _t1974 = parse_sum_monoid(parser)
        sum_monoid1133 = _t1974
        _t1975 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1133))
        _t1973 = _t1975
    else
        if prediction1129 == 2
            _t1977 = parse_max_monoid(parser)
            max_monoid1132 = _t1977
            _t1978 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1132))
            _t1976 = _t1978
        else
            if prediction1129 == 1
                _t1980 = parse_min_monoid(parser)
                min_monoid1131 = _t1980
                _t1981 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1131))
                _t1979 = _t1981
            else
                if prediction1129 == 0
                    _t1983 = parse_or_monoid(parser)
                    or_monoid1130 = _t1983
                    _t1984 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1130))
                    _t1982 = _t1984
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1979 = _t1982
            end
            _t1976 = _t1979
        end
        _t1973 = _t1976
    end
    result1135 = _t1973
    record_span!(parser, span_start1134, "Monoid")
    return result1135
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1136 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1985 = Proto.OrMonoid()
    result1137 = _t1985
    record_span!(parser, span_start1136, "OrMonoid")
    return result1137
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1139 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1986 = parse_type(parser)
    type1138 = _t1986
    consume_literal!(parser, ")")
    _t1987 = Proto.MinMonoid(var"#type"=type1138)
    result1140 = _t1987
    record_span!(parser, span_start1139, "MinMonoid")
    return result1140
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1142 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1988 = parse_type(parser)
    type1141 = _t1988
    consume_literal!(parser, ")")
    _t1989 = Proto.MaxMonoid(var"#type"=type1141)
    result1143 = _t1989
    record_span!(parser, span_start1142, "MaxMonoid")
    return result1143
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1145 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1990 = parse_type(parser)
    type1144 = _t1990
    consume_literal!(parser, ")")
    _t1991 = Proto.SumMonoid(var"#type"=type1144)
    result1146 = _t1991
    record_span!(parser, span_start1145, "SumMonoid")
    return result1146
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1151 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1992 = parse_monoid(parser)
    monoid1147 = _t1992
    _t1993 = parse_relation_id(parser)
    relation_id1148 = _t1993
    _t1994 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1149 = _t1994
    if match_lookahead_literal(parser, "(", 0)
        _t1996 = parse_attrs(parser)
        _t1995 = _t1996
    else
        _t1995 = nothing
    end
    attrs1150 = _t1995
    consume_literal!(parser, ")")
    _t1997 = Proto.MonusDef(monoid=monoid1147, name=relation_id1148, body=abstraction_with_arity1149[1], attrs=(!isnothing(attrs1150) ? attrs1150 : Proto.Attribute[]), value_arity=abstraction_with_arity1149[2])
    result1152 = _t1997
    record_span!(parser, span_start1151, "MonusDef")
    return result1152
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1157 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1998 = parse_relation_id(parser)
    relation_id1153 = _t1998
    _t1999 = parse_abstraction(parser)
    abstraction1154 = _t1999
    _t2000 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1155 = _t2000
    _t2001 = parse_functional_dependency_values(parser)
    functional_dependency_values1156 = _t2001
    consume_literal!(parser, ")")
    _t2002 = Proto.FunctionalDependency(guard=abstraction1154, keys=functional_dependency_keys1155, values=functional_dependency_values1156)
    _t2003 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t2002), name=relation_id1153)
    result1158 = _t2003
    record_span!(parser, span_start1157, "Constraint")
    return result1158
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1159 = Proto.Var[]
    cond1160 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1160
        _t2004 = parse_var(parser)
        item1161 = _t2004
        push!(xs1159, item1161)
        cond1160 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1162 = xs1159
    consume_literal!(parser, ")")
    return vars1162
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1163 = Proto.Var[]
    cond1164 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1164
        _t2005 = parse_var(parser)
        item1165 = _t2005
        push!(xs1163, item1165)
        cond1164 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1166 = xs1163
    consume_literal!(parser, ")")
    return vars1166
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1172 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t2007 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t2008 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t2009 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t2010 = 1
                    else
                        _t2010 = -1
                    end
                    _t2009 = _t2010
                end
                _t2008 = _t2009
            end
            _t2007 = _t2008
        end
        _t2006 = _t2007
    else
        _t2006 = -1
    end
    prediction1167 = _t2006
    if prediction1167 == 3
        _t2012 = parse_iceberg_data(parser)
        iceberg_data1171 = _t2012
        _t2013 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1171))
        _t2011 = _t2013
    else
        if prediction1167 == 2
            _t2015 = parse_csv_data(parser)
            csv_data1170 = _t2015
            _t2016 = Proto.Data(data_type=OneOf(:csv_data, csv_data1170))
            _t2014 = _t2016
        else
            if prediction1167 == 1
                _t2018 = parse_betree_relation(parser)
                betree_relation1169 = _t2018
                _t2019 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1169))
                _t2017 = _t2019
            else
                if prediction1167 == 0
                    _t2021 = parse_edb(parser)
                    edb1168 = _t2021
                    _t2022 = Proto.Data(data_type=OneOf(:edb, edb1168))
                    _t2020 = _t2022
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t2017 = _t2020
            end
            _t2014 = _t2017
        end
        _t2011 = _t2014
    end
    result1173 = _t2011
    record_span!(parser, span_start1172, "Data")
    return result1173
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1177 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t2023 = parse_relation_id(parser)
    relation_id1174 = _t2023
    _t2024 = parse_edb_path(parser)
    edb_path1175 = _t2024
    _t2025 = parse_edb_types(parser)
    edb_types1176 = _t2025
    consume_literal!(parser, ")")
    _t2026 = Proto.EDB(target_id=relation_id1174, path=edb_path1175, types=edb_types1176)
    result1178 = _t2026
    record_span!(parser, span_start1177, "EDB")
    return result1178
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1179 = String[]
    cond1180 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1180
        item1181 = consume_terminal!(parser, "STRING")
        push!(xs1179, item1181)
        cond1180 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1182 = xs1179
    consume_literal!(parser, "]")
    return strings1182
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1183 = Proto.var"#Type"[]
    cond1184 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1184
        _t2027 = parse_type(parser)
        item1185 = _t2027
        push!(xs1183, item1185)
        cond1184 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1186 = xs1183
    consume_literal!(parser, "]")
    return types1186
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1189 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t2028 = parse_relation_id(parser)
    relation_id1187 = _t2028
    _t2029 = parse_betree_info(parser)
    betree_info1188 = _t2029
    consume_literal!(parser, ")")
    _t2030 = Proto.BeTreeRelation(name=relation_id1187, relation_info=betree_info1188)
    result1190 = _t2030
    record_span!(parser, span_start1189, "BeTreeRelation")
    return result1190
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1194 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t2031 = parse_betree_info_key_types(parser)
    betree_info_key_types1191 = _t2031
    _t2032 = parse_betree_info_value_types(parser)
    betree_info_value_types1192 = _t2032
    _t2033 = parse_config_dict(parser)
    config_dict1193 = _t2033
    consume_literal!(parser, ")")
    _t2034 = construct_betree_info(parser, betree_info_key_types1191, betree_info_value_types1192, config_dict1193)
    result1195 = _t2034
    record_span!(parser, span_start1194, "BeTreeInfo")
    return result1195
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1196 = Proto.var"#Type"[]
    cond1197 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1197
        _t2035 = parse_type(parser)
        item1198 = _t2035
        push!(xs1196, item1198)
        cond1197 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1199 = xs1196
    consume_literal!(parser, ")")
    return types1199
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1200 = Proto.var"#Type"[]
    cond1201 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1201
        _t2036 = parse_type(parser)
        item1202 = _t2036
        push!(xs1200, item1202)
        cond1201 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1203 = xs1200
    consume_literal!(parser, ")")
    return types1203
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1209 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t2037 = parse_csvlocator(parser)
    csvlocator1204 = _t2037
    _t2038 = parse_csv_config(parser)
    csv_config1205 = _t2038
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t2040 = parse_gnf_columns(parser)
        _t2039 = _t2040
    else
        _t2039 = nothing
    end
    gnf_columns1206 = _t2039
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relations", 1))
        _t2042 = parse_target_relations(parser)
        _t2041 = _t2042
    else
        _t2041 = nothing
    end
    target_relations1207 = _t2041
    _t2043 = parse_csv_asof(parser)
    csv_asof1208 = _t2043
    consume_literal!(parser, ")")
    _t2044 = construct_csv_data(parser, csvlocator1204, csv_config1205, gnf_columns1206, target_relations1207, csv_asof1208)
    result1210 = _t2044
    record_span!(parser, span_start1209, "CSVData")
    return result1210
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1213 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t2046 = parse_csv_locator_paths(parser)
        _t2045 = _t2046
    else
        _t2045 = nothing
    end
    csv_locator_paths1211 = _t2045
    if match_lookahead_literal(parser, "(", 0)
        _t2048 = parse_csv_locator_inline_data(parser)
        _t2047 = _t2048
    else
        _t2047 = nothing
    end
    csv_locator_inline_data1212 = _t2047
    consume_literal!(parser, ")")
    _t2049 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1211) ? csv_locator_paths1211 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1212) ? csv_locator_inline_data1212 : "")))
    result1214 = _t2049
    record_span!(parser, span_start1213, "CSVLocator")
    return result1214
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
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

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1219 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1219
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1222 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t2050 = parse_config_dict(parser)
    config_dict1220 = _t2050
    if match_lookahead_literal(parser, "(", 0)
        _t2052 = parse__storage_integration(parser)
        _t2051 = _t2052
    else
        _t2051 = nothing
    end
    _storage_integration1221 = _t2051
    consume_literal!(parser, ")")
    _t2053 = construct_csv_config(parser, config_dict1220, _storage_integration1221)
    result1223 = _t2053
    record_span!(parser, span_start1222, "CSVConfig")
    return result1223
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t2054 = parse_config_dict(parser)
    config_dict1224 = _t2054
    consume_literal!(parser, ")")
    return config_dict1224
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1225 = Proto.GNFColumn[]
    cond1226 = match_lookahead_literal(parser, "(", 0)
    while cond1226
        _t2055 = parse_gnf_column(parser)
        item1227 = _t2055
        push!(xs1225, item1227)
        cond1226 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1228 = xs1225
    consume_literal!(parser, ")")
    return gnf_columns1228
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1235 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t2056 = parse_gnf_column_path(parser)
    gnf_column_path1229 = _t2056
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t2058 = parse_relation_id(parser)
        _t2057 = _t2058
    else
        _t2057 = nothing
    end
    relation_id1230 = _t2057
    consume_literal!(parser, "[")
    xs1231 = Proto.var"#Type"[]
    cond1232 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1232
        _t2059 = parse_type(parser)
        item1233 = _t2059
        push!(xs1231, item1233)
        cond1232 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1234 = xs1231
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2060 = Proto.GNFColumn(column_path=gnf_column_path1229, target_id=relation_id1230, types=types1234)
    result1236 = _t2060
    record_span!(parser, span_start1235, "GNFColumn")
    return result1236
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t2061 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t2062 = 0
        else
            _t2062 = -1
        end
        _t2061 = _t2062
    end
    prediction1237 = _t2061
    if prediction1237 == 1
        consume_literal!(parser, "[")
        xs1239 = String[]
        cond1240 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1240
            item1241 = consume_terminal!(parser, "STRING")
            push!(xs1239, item1241)
            cond1240 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1242 = xs1239
        consume_literal!(parser, "]")
        _t2063 = strings1242
    else
        if prediction1237 == 0
            string1238 = consume_terminal!(parser, "STRING")
            _t2064 = String[string1238]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t2063 = _t2064
    end
    return _t2063
end

function parse_target_relations(parser::ParserState)::Proto.TargetRelations
    span_start1245 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relations")
    _t2065 = parse_relation_keys(parser)
    relation_keys1243 = _t2065
    _t2066 = parse_relation_body(parser)
    relation_body1244 = _t2066
    consume_literal!(parser, ")")
    _t2067 = construct_relations(parser, relation_keys1243, relation_body1244)
    result1246 = _t2067
    record_span!(parser, span_start1245, "TargetRelations")
    return result1246
end

function parse_relation_keys(parser::ParserState)::Tuple{Vector{Proto.NamedColumn}, Bool}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "keys", 1)
            if match_lookahead_literal(parser, ":", 2)
                _t2070 = 1
            else
                if match_lookahead_literal(parser, ")", 2)
                    _t2071 = 0
                else
                    if match_lookahead_literal(parser, "(", 2)
                        _t2072 = 0
                    else
                        _t2072 = -1
                    end
                    _t2071 = _t2072
                end
                _t2070 = _t2071
            end
            _t2069 = _t2070
        else
            _t2069 = -1
        end
        _t2068 = _t2069
    else
        _t2068 = -1
    end
    prediction1247 = _t2068
    if prediction1247 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "keys")
        consume_literal!(parser, ":")
        symbol1252 = consume_terminal!(parser, "SYMBOL")
        consume_literal!(parser, ")")
        _t2074 = construct_synthetic_keys(parser, symbol1252)
        _t2073 = _t2074
    else
        if prediction1247 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "keys")
            xs1248 = Proto.NamedColumn[]
            cond1249 = match_lookahead_literal(parser, "(", 0)
            while cond1249
                _t2076 = parse_named_column(parser)
                item1250 = _t2076
                push!(xs1248, item1250)
                cond1249 = match_lookahead_literal(parser, "(", 0)
            end
            named_columns1251 = xs1248
            consume_literal!(parser, ")")
            _t2075 = (named_columns1251, false,)
        else
            throw(ParseError("Unexpected token in relation_keys" * ": " * string(lookahead(parser, 0))))
        end
        _t2073 = _t2075
    end
    return _t2073
end

function parse_named_column(parser::ParserState)::Proto.NamedColumn
    span_start1255 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1253 = consume_terminal!(parser, "STRING")
    _t2077 = parse_type(parser)
    type1254 = _t2077
    consume_literal!(parser, ")")
    _t2078 = Proto.NamedColumn(name=string1253, var"#type"=type1254)
    result1256 = _t2078
    record_span!(parser, span_start1255, "NamedColumn")
    return result1256
end

function parse_relation_body(parser::ParserState)::Proto.TargetRelations
    span_start1261 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "relation", 1)
            _t2080 = 0
        else
            if match_lookahead_literal(parser, "inserts", 1)
                _t2081 = 1
            else
                _t2081 = 0
            end
            _t2080 = _t2081
        end
        _t2079 = _t2080
    else
        _t2079 = 0
    end
    prediction1257 = _t2079
    if prediction1257 == 1
        _t2083 = parse_cdc_inserts(parser)
        cdc_inserts1259 = _t2083
        _t2084 = parse_cdc_deletes(parser)
        cdc_deletes1260 = _t2084
        _t2085 = construct_cdc_relations(parser, cdc_inserts1259, cdc_deletes1260)
        _t2082 = _t2085
    else
        if prediction1257 == 0
            _t2087 = parse_non_cdc_relations(parser)
            non_cdc_relations1258 = _t2087
            _t2088 = construct_non_cdc_relations(parser, non_cdc_relations1258)
            _t2086 = _t2088
        else
            throw(ParseError("Unexpected token in relation_body" * ": " * string(lookahead(parser, 0))))
        end
        _t2082 = _t2086
    end
    result1262 = _t2082
    record_span!(parser, span_start1261, "TargetRelations")
    return result1262
end

function parse_non_cdc_relations(parser::ParserState)::Vector{Proto.TargetRelation}
    xs1263 = Proto.TargetRelation[]
    cond1264 = match_lookahead_literal(parser, "(", 0)
    while cond1264
        _t2089 = parse_target_relation(parser)
        item1265 = _t2089
        push!(xs1263, item1265)
        cond1264 = match_lookahead_literal(parser, "(", 0)
    end
    return xs1263
end

function parse_target_relation(parser::ParserState)::Proto.TargetRelation
    span_start1271 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relation")
    _t2090 = parse_relation_id(parser)
    relation_id1266 = _t2090
    xs1267 = Proto.NamedColumn[]
    cond1268 = match_lookahead_literal(parser, "(", 0)
    while cond1268
        _t2091 = parse_named_column(parser)
        item1269 = _t2091
        push!(xs1267, item1269)
        cond1268 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1270 = xs1267
    consume_literal!(parser, ")")
    _t2092 = Proto.TargetRelation(target_id=relation_id1266, values=named_columns1270)
    result1272 = _t2092
    record_span!(parser, span_start1271, "TargetRelation")
    return result1272
end

function parse_cdc_inserts(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "inserts")
    xs1273 = Proto.TargetRelation[]
    cond1274 = match_lookahead_literal(parser, "(", 0)
    while cond1274
        _t2093 = parse_target_relation(parser)
        item1275 = _t2093
        push!(xs1273, item1275)
        cond1274 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1276 = xs1273
    consume_literal!(parser, ")")
    return target_relations1276
end

function parse_cdc_deletes(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "deletes")
    xs1277 = Proto.TargetRelation[]
    cond1278 = match_lookahead_literal(parser, "(", 0)
    while cond1278
        _t2094 = parse_target_relation(parser)
        item1279 = _t2094
        push!(xs1277, item1279)
        cond1278 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1280 = xs1277
    consume_literal!(parser, ")")
    return target_relations1280
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1281 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1281
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1288 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t2095 = parse_iceberg_locator(parser)
    iceberg_locator1282 = _t2095
    _t2096 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1283 = _t2096
    _t2097 = parse_gnf_columns(parser)
    gnf_columns1284 = _t2097
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2099 = parse_iceberg_from_snapshot(parser)
        _t2098 = _t2099
    else
        _t2098 = nothing
    end
    iceberg_from_snapshot1285 = _t2098
    if match_lookahead_literal(parser, "(", 0)
        _t2101 = parse_iceberg_to_snapshot(parser)
        _t2100 = _t2101
    else
        _t2100 = nothing
    end
    iceberg_to_snapshot1286 = _t2100
    _t2102 = parse_boolean_value(parser)
    boolean_value1287 = _t2102
    consume_literal!(parser, ")")
    _t2103 = construct_iceberg_data(parser, iceberg_locator1282, iceberg_catalog_config1283, gnf_columns1284, iceberg_from_snapshot1285, iceberg_to_snapshot1286, boolean_value1287)
    result1289 = _t2103
    record_span!(parser, span_start1288, "IcebergData")
    return result1289
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1293 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2104 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1290 = _t2104
    _t2105 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1291 = _t2105
    _t2106 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1292 = _t2106
    consume_literal!(parser, ")")
    _t2107 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1290, namespace=iceberg_locator_namespace1291, warehouse=iceberg_locator_warehouse1292)
    result1294 = _t2107
    record_span!(parser, span_start1293, "IcebergLocator")
    return result1294
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1295 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1295
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1296 = String[]
    cond1297 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1297
        item1298 = consume_terminal!(parser, "STRING")
        push!(xs1296, item1298)
        cond1297 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1299 = xs1296
    consume_literal!(parser, ")")
    return strings1299
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1300 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1300
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1305 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2108 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1301 = _t2108
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2110 = parse_iceberg_catalog_config_scope(parser)
        _t2109 = _t2110
    else
        _t2109 = nothing
    end
    iceberg_catalog_config_scope1302 = _t2109
    _t2111 = parse_iceberg_properties(parser)
    iceberg_properties1303 = _t2111
    _t2112 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1304 = _t2112
    consume_literal!(parser, ")")
    _t2113 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1301, iceberg_catalog_config_scope1302, iceberg_properties1303, iceberg_auth_properties1304)
    result1306 = _t2113
    record_span!(parser, span_start1305, "IcebergCatalogConfig")
    return result1306
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1307 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1307
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1308 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1308
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1309 = Tuple{String, String}[]
    cond1310 = match_lookahead_literal(parser, "(", 0)
    while cond1310
        _t2114 = parse_iceberg_property_entry(parser)
        item1311 = _t2114
        push!(xs1309, item1311)
        cond1310 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1312 = xs1309
    consume_literal!(parser, ")")
    return iceberg_property_entrys1312
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1313 = consume_terminal!(parser, "STRING")
    string_31314 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1313, string_31314,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1315 = Tuple{String, String}[]
    cond1316 = match_lookahead_literal(parser, "(", 0)
    while cond1316
        _t2115 = parse_iceberg_masked_property_entry(parser)
        item1317 = _t2115
        push!(xs1315, item1317)
        cond1316 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1318 = xs1315
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1318
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1319 = consume_terminal!(parser, "STRING")
    string_31320 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1319, string_31320,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1321 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1321
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1322 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1322
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1324 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2116 = parse_fragment_id(parser)
    fragment_id1323 = _t2116
    consume_literal!(parser, ")")
    _t2117 = Proto.Undefine(fragment_id=fragment_id1323)
    result1325 = _t2117
    record_span!(parser, span_start1324, "Undefine")
    return result1325
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1330 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1326 = Proto.RelationId[]
    cond1327 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1327
        _t2118 = parse_relation_id(parser)
        item1328 = _t2118
        push!(xs1326, item1328)
        cond1327 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1329 = xs1326
    consume_literal!(parser, ")")
    _t2119 = Proto.Context(relations=relation_ids1329)
    result1331 = _t2119
    record_span!(parser, span_start1330, "Context")
    return result1331
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1337 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2120 = parse_edb_path(parser)
    edb_path1332 = _t2120
    xs1333 = Proto.SnapshotMapping[]
    cond1334 = match_lookahead_literal(parser, "[", 0)
    while cond1334
        _t2121 = parse_snapshot_mapping(parser)
        item1335 = _t2121
        push!(xs1333, item1335)
        cond1334 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1336 = xs1333
    consume_literal!(parser, ")")
    _t2122 = Proto.Snapshot(mappings=snapshot_mappings1336, prefix=edb_path1332)
    result1338 = _t2122
    record_span!(parser, span_start1337, "Snapshot")
    return result1338
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1341 = span_start(parser)
    _t2123 = parse_edb_path(parser)
    edb_path1339 = _t2123
    _t2124 = parse_relation_id(parser)
    relation_id1340 = _t2124
    _t2125 = Proto.SnapshotMapping(destination_path=edb_path1339, source_relation=relation_id1340)
    result1342 = _t2125
    record_span!(parser, span_start1341, "SnapshotMapping")
    return result1342
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1343 = Proto.Read[]
    cond1344 = match_lookahead_literal(parser, "(", 0)
    while cond1344
        _t2126 = parse_read(parser)
        item1345 = _t2126
        push!(xs1343, item1345)
        cond1344 = match_lookahead_literal(parser, "(", 0)
    end
    reads1346 = xs1343
    consume_literal!(parser, ")")
    return reads1346
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1353 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2128 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2129 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2130 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2131 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2132 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2133 = 3
                            else
                                _t2133 = -1
                            end
                            _t2132 = _t2133
                        end
                        _t2131 = _t2132
                    end
                    _t2130 = _t2131
                end
                _t2129 = _t2130
            end
            _t2128 = _t2129
        end
        _t2127 = _t2128
    else
        _t2127 = -1
    end
    prediction1347 = _t2127
    if prediction1347 == 4
        _t2135 = parse_export(parser)
        export1352 = _t2135
        _t2136 = Proto.Read(read_type=OneOf(:var"#export", export1352))
        _t2134 = _t2136
    else
        if prediction1347 == 3
            _t2138 = parse_abort(parser)
            abort1351 = _t2138
            _t2139 = Proto.Read(read_type=OneOf(:abort, abort1351))
            _t2137 = _t2139
        else
            if prediction1347 == 2
                _t2141 = parse_what_if(parser)
                what_if1350 = _t2141
                _t2142 = Proto.Read(read_type=OneOf(:what_if, what_if1350))
                _t2140 = _t2142
            else
                if prediction1347 == 1
                    _t2144 = parse_output(parser)
                    output1349 = _t2144
                    _t2145 = Proto.Read(read_type=OneOf(:output, output1349))
                    _t2143 = _t2145
                else
                    if prediction1347 == 0
                        _t2147 = parse_demand(parser)
                        demand1348 = _t2147
                        _t2148 = Proto.Read(read_type=OneOf(:demand, demand1348))
                        _t2146 = _t2148
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2143 = _t2146
                end
                _t2140 = _t2143
            end
            _t2137 = _t2140
        end
        _t2134 = _t2137
    end
    result1354 = _t2134
    record_span!(parser, span_start1353, "Read")
    return result1354
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1356 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2149 = parse_relation_id(parser)
    relation_id1355 = _t2149
    consume_literal!(parser, ")")
    _t2150 = Proto.Demand(relation_id=relation_id1355)
    result1357 = _t2150
    record_span!(parser, span_start1356, "Demand")
    return result1357
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1360 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2151 = parse_name(parser)
    name1358 = _t2151
    _t2152 = parse_relation_id(parser)
    relation_id1359 = _t2152
    consume_literal!(parser, ")")
    _t2153 = Proto.Output(name=name1358, relation_id=relation_id1359)
    result1361 = _t2153
    record_span!(parser, span_start1360, "Output")
    return result1361
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1364 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2154 = parse_name(parser)
    name1362 = _t2154
    _t2155 = parse_epoch(parser)
    epoch1363 = _t2155
    consume_literal!(parser, ")")
    _t2156 = Proto.WhatIf(branch=name1362, epoch=epoch1363)
    result1365 = _t2156
    record_span!(parser, span_start1364, "WhatIf")
    return result1365
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1368 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2158 = parse_name(parser)
        _t2157 = _t2158
    else
        _t2157 = nothing
    end
    name1366 = _t2157
    _t2159 = parse_relation_id(parser)
    relation_id1367 = _t2159
    consume_literal!(parser, ")")
    _t2160 = Proto.Abort(name=(!isnothing(name1366) ? name1366 : "abort"), relation_id=relation_id1367)
    result1369 = _t2160
    record_span!(parser, span_start1368, "Abort")
    return result1369
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1373 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2162 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2163 = 0
            else
                _t2163 = -1
            end
            _t2162 = _t2163
        end
        _t2161 = _t2162
    else
        _t2161 = -1
    end
    prediction1370 = _t2161
    if prediction1370 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2165 = parse_export_iceberg_config(parser)
        export_iceberg_config1372 = _t2165
        consume_literal!(parser, ")")
        _t2166 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1372))
        _t2164 = _t2166
    else
        if prediction1370 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2168 = parse_export_csv_config(parser)
            export_csv_config1371 = _t2168
            consume_literal!(parser, ")")
            _t2169 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1371))
            _t2167 = _t2169
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2164 = _t2167
    end
    result1374 = _t2164
    record_span!(parser, span_start1373, "Export")
    return result1374
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1382 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2171 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2172 = 1
            else
                _t2172 = -1
            end
            _t2171 = _t2172
        end
        _t2170 = _t2171
    else
        _t2170 = -1
    end
    prediction1375 = _t2170
    if prediction1375 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2174 = parse_export_csv_path(parser)
        export_csv_path1379 = _t2174
        _t2175 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1380 = _t2175
        _t2176 = parse_config_dict(parser)
        config_dict1381 = _t2176
        consume_literal!(parser, ")")
        _t2177 = construct_export_csv_config(parser, export_csv_path1379, export_csv_columns_list1380, config_dict1381)
        _t2173 = _t2177
    else
        if prediction1375 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2179 = parse_export_csv_output_location(parser)
            export_csv_output_location1376 = _t2179
            _t2180 = parse_export_csv_source(parser)
            export_csv_source1377 = _t2180
            _t2181 = parse_csv_config(parser)
            csv_config1378 = _t2181
            consume_literal!(parser, ")")
            _t2182 = construct_export_csv_config_with_location(parser, export_csv_output_location1376, export_csv_source1377, csv_config1378)
            _t2178 = _t2182
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2173 = _t2178
    end
    result1383 = _t2173
    record_span!(parser, span_start1382, "ExportCSVConfig")
    return result1383
end

function parse_export_csv_output_location(parser::ParserState)::Tuple{String, String}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "transaction_output_name", 1)
            _t2184 = 1
        else
            if match_lookahead_literal(parser, "path", 1)
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
        consume_literal!(parser, "transaction_output_name")
        _t2187 = parse_name(parser)
        name1386 = _t2187
        consume_literal!(parser, ")")
        _t2186 = ("", name1386,)
    else
        if prediction1384 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "path")
            string1385 = consume_terminal!(parser, "STRING")
            consume_literal!(parser, ")")
            _t2188 = (string1385, "",)
        else
            throw(ParseError("Unexpected token in export_csv_output_location" * ": " * string(lookahead(parser, 0))))
        end
        _t2186 = _t2188
    end
    return _t2186
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1393 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2190 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2191 = 0
            else
                _t2191 = -1
            end
            _t2190 = _t2191
        end
        _t2189 = _t2190
    else
        _t2189 = -1
    end
    prediction1387 = _t2189
    if prediction1387 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2193 = parse_relation_id(parser)
        relation_id1392 = _t2193
        consume_literal!(parser, ")")
        _t2194 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1392))
        _t2192 = _t2194
    else
        if prediction1387 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1388 = Proto.ExportCSVColumn[]
            cond1389 = match_lookahead_literal(parser, "(", 0)
            while cond1389
                _t2196 = parse_export_csv_column(parser)
                item1390 = _t2196
                push!(xs1388, item1390)
                cond1389 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1391 = xs1388
            consume_literal!(parser, ")")
            _t2197 = Proto.ExportCSVColumns(columns=export_csv_columns1391)
            _t2198 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2197))
            _t2195 = _t2198
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2192 = _t2195
    end
    result1394 = _t2192
    record_span!(parser, span_start1393, "ExportCSVSource")
    return result1394
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1397 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1395 = consume_terminal!(parser, "STRING")
    _t2199 = parse_relation_id(parser)
    relation_id1396 = _t2199
    consume_literal!(parser, ")")
    _t2200 = Proto.ExportCSVColumn(column_name=string1395, column_data=relation_id1396)
    result1398 = _t2200
    record_span!(parser, span_start1397, "ExportCSVColumn")
    return result1398
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1399 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1399
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1400 = Proto.ExportCSVColumn[]
    cond1401 = match_lookahead_literal(parser, "(", 0)
    while cond1401
        _t2201 = parse_export_csv_column(parser)
        item1402 = _t2201
        push!(xs1400, item1402)
        cond1401 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1403 = xs1400
    consume_literal!(parser, ")")
    return export_csv_columns1403
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1409 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2202 = parse_iceberg_locator(parser)
    iceberg_locator1404 = _t2202
    _t2203 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1405 = _t2203
    _t2204 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1406 = _t2204
    _t2205 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1407 = _t2205
    if match_lookahead_literal(parser, "{", 0)
        _t2207 = parse_config_dict(parser)
        _t2206 = _t2207
    else
        _t2206 = nothing
    end
    config_dict1408 = _t2206
    consume_literal!(parser, ")")
    _t2208 = construct_export_iceberg_config_full(parser, iceberg_locator1404, iceberg_catalog_config1405, export_iceberg_table_def1406, iceberg_table_properties1407, config_dict1408)
    result1410 = _t2208
    record_span!(parser, span_start1409, "ExportIcebergConfig")
    return result1410
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1412 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2209 = parse_relation_id(parser)
    relation_id1411 = _t2209
    consume_literal!(parser, ")")
    result1413 = relation_id1411
    record_span!(parser, span_start1412, "RelationId")
    return result1413
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1414 = Tuple{String, String}[]
    cond1415 = match_lookahead_literal(parser, "(", 0)
    while cond1415
        _t2210 = parse_iceberg_property_entry(parser)
        item1416 = _t2210
        push!(xs1414, item1416)
        cond1415 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1417 = xs1414
    consume_literal!(parser, ")")
    return iceberg_property_entrys1417
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
