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
        _t2208 = nothing
    end
    if _has_proto_field(value, Symbol("int32_value"))
        return _get_oneof_field(value, :int32_value)
    else
        _t2209 = nothing
    end
    throw(ParseError("expected an int32 value (e.g. `1i32`) for this config field"))
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2210 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2211 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2212 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2213 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2214 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2215 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2216 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2217 = nothing
    end
    return nothing
end

function construct_non_cdc_relations(parser::ParserState, targets::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2218 = Proto.PlainTargets(targets=targets)
    _t2219 = Proto.TargetRelations(body=OneOf(:plain, _t2218), keys=Proto.NamedColumn[])
    return _t2219
end

function construct_cdc_relations(parser::ParserState, inserts::Vector{Proto.TargetRelation}, deletes::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2220 = Proto.CDCTargets(inserts=inserts, deletes=deletes)
    _t2221 = Proto.TargetRelations(body=OneOf(:cdc, _t2220), keys=Proto.NamedColumn[])
    return _t2221
end

function construct_relations(parser::ParserState, keys::Tuple{Vector{Proto.NamedColumn}, Bool}, body::Proto.TargetRelations)::Proto.TargetRelations
    if _has_proto_field(body, Symbol("plain"))
        _t2223 = Proto.TargetRelations(body=OneOf(:plain, _get_oneof_field(body, :plain)), keys=keys[1], synthetic_key=keys[2])
        return _t2223
    else
        _t2222 = nothing
    end
    _t2224 = Proto.TargetRelations(body=OneOf(:cdc, _get_oneof_field(body, :cdc)), keys=keys[1], synthetic_key=keys[2])
    return _t2224
end

function construct_csv_data(parser::ParserState, locator::Proto.CSVLocator, config::Proto.CSVConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, relations_opt::Union{Nothing, Proto.TargetRelations}, asof::String)::Proto.CSVData
    _t2225 = Proto.CSVData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), asof=asof, relations=relations_opt)
    return _t2225
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2226 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2226
    _t2227 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2227
    _t2228 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2228
    _t2229 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2229
    _t2230 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2230
    _t2231 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2231
    _t2232 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2232
    _t2233 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2233
    _t2234 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2234
    _t2235 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2235
    _t2236 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2236
    _t2237 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2237
    _t2238 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2238
    _t2239 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2239
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2240 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2241 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2242 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2243 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2244 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2245 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2246 = Proto.StorageIntegration(provider=_t2241, azure_sas_token=_t2242, s3_region=_t2243, s3_access_key_id=_t2244, s3_secret_access_key=_t2245)
    return _t2246
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2247 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2247
    _t2248 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2248
    _t2249 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2249
    _t2250 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2250
    _t2251 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2251
    _t2252 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2252
    _t2253 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2253
    _t2254 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2254
    _t2255 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2255
    _t2256 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2256
    _t2257 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2257
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2258 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2258
    _t2259 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2259
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
    _t2260 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2260
    _t2261 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2261
    _t2262 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2262
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2263 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2263
    _t2264 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2264
    _t2265 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2265
    _t2266 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2266
    _t2267 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2267
    _t2268 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2268
    _t2269 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2269
    _t2270 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2270
end

function construct_export_csv_config_with_location(parser::ParserState, location::Tuple{String, String}, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2271 = Proto.ExportCSVConfig(path=location[1], transaction_output_name=location[2], csv_source=csv_source, csv_config=csv_config)
    return _t2271
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2272 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2272
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2273 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2273
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2274 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2274
    _t2275 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2275
    _t2276 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2276
    table_props = Dict(table_property_pairs)
    _t2277 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2277
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start714 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1417 = parse_configure(parser)
        _t1416 = _t1417
    else
        _t1416 = nothing
    end
    configure708 = _t1416
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1419 = parse_sync(parser)
        _t1418 = _t1419
    else
        _t1418 = nothing
    end
    sync709 = _t1418
    xs710 = Proto.Epoch[]
    cond711 = match_lookahead_literal(parser, "(", 0)
    while cond711
        _t1420 = parse_epoch(parser)
        item712 = _t1420
        push!(xs710, item712)
        cond711 = match_lookahead_literal(parser, "(", 0)
    end
    epochs713 = xs710
    consume_literal!(parser, ")")
    _t1421 = default_configure(parser)
    _t1422 = Proto.Transaction(epochs=epochs713, configure=(!isnothing(configure708) ? configure708 : _t1421), sync=sync709)
    result715 = _t1422
    record_span!(parser, span_start714, "Transaction")
    return result715
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start717 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1423 = parse_config_dict(parser)
    config_dict716 = _t1423
    consume_literal!(parser, ")")
    _t1424 = construct_configure(parser, config_dict716)
    result718 = _t1424
    record_span!(parser, span_start717, "Configure")
    return result718
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs719 = Tuple{String, Proto.Value}[]
    cond720 = match_lookahead_literal(parser, ":", 0)
    while cond720
        _t1425 = parse_config_key_value(parser)
        item721 = _t1425
        push!(xs719, item721)
        cond720 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values722 = xs719
    consume_literal!(parser, "}")
    return config_key_values722
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol723 = consume_terminal!(parser, "SYMBOL")
    _t1426 = parse_raw_value(parser)
    raw_value724 = _t1426
    return (symbol723, raw_value724,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start738 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1427 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1428 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1429 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1431 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1432 = 0
                        else
                            _t1432 = -1
                        end
                        _t1431 = _t1432
                    end
                    _t1430 = _t1431
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1433 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1434 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1435 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1436 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1437 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1438 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1439 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1440 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1441 = 10
                                                    else
                                                        _t1441 = -1
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
                            _t1434 = _t1435
                        end
                        _t1433 = _t1434
                    end
                    _t1430 = _t1433
                end
                _t1429 = _t1430
            end
            _t1428 = _t1429
        end
        _t1427 = _t1428
    end
    prediction725 = _t1427
    if prediction725 == 12
        _t1443 = parse_boolean_value(parser)
        boolean_value737 = _t1443
        _t1444 = Proto.Value(value=OneOf(:boolean_value, boolean_value737))
        _t1442 = _t1444
    else
        if prediction725 == 11
            consume_literal!(parser, "missing")
            _t1446 = Proto.MissingValue()
            _t1447 = Proto.Value(value=OneOf(:missing_value, _t1446))
            _t1445 = _t1447
        else
            if prediction725 == 10
                decimal736 = consume_terminal!(parser, "DECIMAL")
                _t1449 = Proto.Value(value=OneOf(:decimal_value, decimal736))
                _t1448 = _t1449
            else
                if prediction725 == 9
                    int128735 = consume_terminal!(parser, "INT128")
                    _t1451 = Proto.Value(value=OneOf(:int128_value, int128735))
                    _t1450 = _t1451
                else
                    if prediction725 == 8
                        uint128734 = consume_terminal!(parser, "UINT128")
                        _t1453 = Proto.Value(value=OneOf(:uint128_value, uint128734))
                        _t1452 = _t1453
                    else
                        if prediction725 == 7
                            uint32733 = consume_terminal!(parser, "UINT32")
                            _t1455 = Proto.Value(value=OneOf(:uint32_value, uint32733))
                            _t1454 = _t1455
                        else
                            if prediction725 == 6
                                float732 = consume_terminal!(parser, "FLOAT")
                                _t1457 = Proto.Value(value=OneOf(:float_value, float732))
                                _t1456 = _t1457
                            else
                                if prediction725 == 5
                                    float32731 = consume_terminal!(parser, "FLOAT32")
                                    _t1459 = Proto.Value(value=OneOf(:float32_value, float32731))
                                    _t1458 = _t1459
                                else
                                    if prediction725 == 4
                                        int730 = consume_terminal!(parser, "INT")
                                        _t1461 = Proto.Value(value=OneOf(:int_value, int730))
                                        _t1460 = _t1461
                                    else
                                        if prediction725 == 3
                                            int32729 = consume_terminal!(parser, "INT32")
                                            _t1463 = Proto.Value(value=OneOf(:int32_value, int32729))
                                            _t1462 = _t1463
                                        else
                                            if prediction725 == 2
                                                string728 = consume_terminal!(parser, "STRING")
                                                _t1465 = Proto.Value(value=OneOf(:string_value, string728))
                                                _t1464 = _t1465
                                            else
                                                if prediction725 == 1
                                                    _t1467 = parse_raw_datetime(parser)
                                                    raw_datetime727 = _t1467
                                                    _t1468 = Proto.Value(value=OneOf(:datetime_value, raw_datetime727))
                                                    _t1466 = _t1468
                                                else
                                                    if prediction725 == 0
                                                        _t1470 = parse_raw_date(parser)
                                                        raw_date726 = _t1470
                                                        _t1471 = Proto.Value(value=OneOf(:date_value, raw_date726))
                                                        _t1469 = _t1471
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1466 = _t1469
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
                _t1448 = _t1450
            end
            _t1445 = _t1448
        end
        _t1442 = _t1445
    end
    result739 = _t1442
    record_span!(parser, span_start738, "Value")
    return result739
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start743 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int740 = consume_terminal!(parser, "INT")
    int_3741 = consume_terminal!(parser, "INT")
    int_4742 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1472 = Proto.DateValue(year=Int32(int740), month=Int32(int_3741), day=Int32(int_4742))
    result744 = _t1472
    record_span!(parser, span_start743, "DateValue")
    return result744
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start752 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int745 = consume_terminal!(parser, "INT")
    int_3746 = consume_terminal!(parser, "INT")
    int_4747 = consume_terminal!(parser, "INT")
    int_5748 = consume_terminal!(parser, "INT")
    int_6749 = consume_terminal!(parser, "INT")
    int_7750 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1473 = consume_terminal!(parser, "INT")
    else
        _t1473 = nothing
    end
    int_8751 = _t1473
    consume_literal!(parser, ")")
    _t1474 = Proto.DateTimeValue(year=Int32(int745), month=Int32(int_3746), day=Int32(int_4747), hour=Int32(int_5748), minute=Int32(int_6749), second=Int32(int_7750), microsecond=Int32((!isnothing(int_8751) ? int_8751 : 0)))
    result753 = _t1474
    record_span!(parser, span_start752, "DateTimeValue")
    return result753
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1475 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1476 = 1
        else
            _t1476 = -1
        end
        _t1475 = _t1476
    end
    prediction754 = _t1475
    if prediction754 == 1
        consume_literal!(parser, "false")
        _t1477 = false
    else
        if prediction754 == 0
            consume_literal!(parser, "true")
            _t1478 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1477 = _t1478
    end
    return _t1477
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start759 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs755 = Proto.FragmentId[]
    cond756 = match_lookahead_literal(parser, ":", 0)
    while cond756
        _t1479 = parse_fragment_id(parser)
        item757 = _t1479
        push!(xs755, item757)
        cond756 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids758 = xs755
    consume_literal!(parser, ")")
    _t1480 = Proto.Sync(fragments=fragment_ids758)
    result760 = _t1480
    record_span!(parser, span_start759, "Sync")
    return result760
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start762 = span_start(parser)
    consume_literal!(parser, ":")
    symbol761 = consume_terminal!(parser, "SYMBOL")
    result763 = Proto.FragmentId(Vector{UInt8}(symbol761))
    record_span!(parser, span_start762, "FragmentId")
    return result763
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start766 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1482 = parse_epoch_writes(parser)
        _t1481 = _t1482
    else
        _t1481 = nothing
    end
    epoch_writes764 = _t1481
    if match_lookahead_literal(parser, "(", 0)
        _t1484 = parse_epoch_reads(parser)
        _t1483 = _t1484
    else
        _t1483 = nothing
    end
    epoch_reads765 = _t1483
    consume_literal!(parser, ")")
    _t1485 = Proto.Epoch(writes=(!isnothing(epoch_writes764) ? epoch_writes764 : Proto.Write[]), reads=(!isnothing(epoch_reads765) ? epoch_reads765 : Proto.Read[]))
    result767 = _t1485
    record_span!(parser, span_start766, "Epoch")
    return result767
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs768 = Proto.Write[]
    cond769 = match_lookahead_literal(parser, "(", 0)
    while cond769
        _t1486 = parse_write(parser)
        item770 = _t1486
        push!(xs768, item770)
        cond769 = match_lookahead_literal(parser, "(", 0)
    end
    writes771 = xs768
    consume_literal!(parser, ")")
    return writes771
end

function parse_write(parser::ParserState)::Proto.Write
    span_start777 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1488 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1489 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1490 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1491 = 2
                    else
                        _t1491 = -1
                    end
                    _t1490 = _t1491
                end
                _t1489 = _t1490
            end
            _t1488 = _t1489
        end
        _t1487 = _t1488
    else
        _t1487 = -1
    end
    prediction772 = _t1487
    if prediction772 == 3
        _t1493 = parse_snapshot(parser)
        snapshot776 = _t1493
        _t1494 = Proto.Write(write_type=OneOf(:snapshot, snapshot776))
        _t1492 = _t1494
    else
        if prediction772 == 2
            _t1496 = parse_context(parser)
            context775 = _t1496
            _t1497 = Proto.Write(write_type=OneOf(:context, context775))
            _t1495 = _t1497
        else
            if prediction772 == 1
                _t1499 = parse_undefine(parser)
                undefine774 = _t1499
                _t1500 = Proto.Write(write_type=OneOf(:undefine, undefine774))
                _t1498 = _t1500
            else
                if prediction772 == 0
                    _t1502 = parse_define(parser)
                    define773 = _t1502
                    _t1503 = Proto.Write(write_type=OneOf(:define, define773))
                    _t1501 = _t1503
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1498 = _t1501
            end
            _t1495 = _t1498
        end
        _t1492 = _t1495
    end
    result778 = _t1492
    record_span!(parser, span_start777, "Write")
    return result778
end

function parse_define(parser::ParserState)::Proto.Define
    span_start780 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1504 = parse_fragment(parser)
    fragment779 = _t1504
    consume_literal!(parser, ")")
    _t1505 = Proto.Define(fragment=fragment779)
    result781 = _t1505
    record_span!(parser, span_start780, "Define")
    return result781
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start787 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1506 = parse_new_fragment_id(parser)
    new_fragment_id782 = _t1506
    xs783 = Proto.Declaration[]
    cond784 = match_lookahead_literal(parser, "(", 0)
    while cond784
        _t1507 = parse_declaration(parser)
        item785 = _t1507
        push!(xs783, item785)
        cond784 = match_lookahead_literal(parser, "(", 0)
    end
    declarations786 = xs783
    consume_literal!(parser, ")")
    result788 = construct_fragment(parser, new_fragment_id782, declarations786)
    record_span!(parser, span_start787, "Fragment")
    return result788
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start790 = span_start(parser)
    _t1508 = parse_fragment_id(parser)
    fragment_id789 = _t1508
    start_fragment!(parser, fragment_id789)
    result791 = fragment_id789
    record_span!(parser, span_start790, "FragmentId")
    return result791
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start797 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1510 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1511 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1512 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1513 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1514 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1515 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1516 = 1
                                else
                                    _t1516 = -1
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
            end
            _t1510 = _t1511
        end
        _t1509 = _t1510
    else
        _t1509 = -1
    end
    prediction792 = _t1509
    if prediction792 == 3
        _t1518 = parse_data(parser)
        data796 = _t1518
        _t1519 = Proto.Declaration(declaration_type=OneOf(:data, data796))
        _t1517 = _t1519
    else
        if prediction792 == 2
            _t1521 = parse_constraint(parser)
            constraint795 = _t1521
            _t1522 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint795))
            _t1520 = _t1522
        else
            if prediction792 == 1
                _t1524 = parse_algorithm(parser)
                algorithm794 = _t1524
                _t1525 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm794))
                _t1523 = _t1525
            else
                if prediction792 == 0
                    _t1527 = parse_def(parser)
                    def793 = _t1527
                    _t1528 = Proto.Declaration(declaration_type=OneOf(:def, def793))
                    _t1526 = _t1528
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1523 = _t1526
            end
            _t1520 = _t1523
        end
        _t1517 = _t1520
    end
    result798 = _t1517
    record_span!(parser, span_start797, "Declaration")
    return result798
end

function parse_def(parser::ParserState)::Proto.Def
    span_start802 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1529 = parse_relation_id(parser)
    relation_id799 = _t1529
    _t1530 = parse_abstraction(parser)
    abstraction800 = _t1530
    if match_lookahead_literal(parser, "(", 0)
        _t1532 = parse_attrs(parser)
        _t1531 = _t1532
    else
        _t1531 = nothing
    end
    attrs801 = _t1531
    consume_literal!(parser, ")")
    _t1533 = Proto.Def(name=relation_id799, body=abstraction800, attrs=(!isnothing(attrs801) ? attrs801 : Proto.Attribute[]))
    result803 = _t1533
    record_span!(parser, span_start802, "Def")
    return result803
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start807 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1534 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1535 = 1
        else
            _t1535 = -1
        end
        _t1534 = _t1535
    end
    prediction804 = _t1534
    if prediction804 == 1
        uint128806 = consume_terminal!(parser, "UINT128")
        _t1536 = Proto.RelationId(uint128806.low, uint128806.high)
    else
        if prediction804 == 0
            consume_literal!(parser, ":")
            symbol805 = consume_terminal!(parser, "SYMBOL")
            _t1537 = relation_id_from_string(parser, symbol805)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1536 = _t1537
    end
    result808 = _t1536
    record_span!(parser, span_start807, "RelationId")
    return result808
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start811 = span_start(parser)
    consume_literal!(parser, "(")
    _t1538 = parse_bindings(parser)
    bindings809 = _t1538
    _t1539 = parse_formula(parser)
    formula810 = _t1539
    consume_literal!(parser, ")")
    _t1540 = Proto.Abstraction(vars=vcat(bindings809[1], !isnothing(bindings809[2]) ? bindings809[2] : []), value=formula810)
    result812 = _t1540
    record_span!(parser, span_start811, "Abstraction")
    return result812
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs813 = Proto.Binding[]
    cond814 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond814
        _t1541 = parse_binding(parser)
        item815 = _t1541
        push!(xs813, item815)
        cond814 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings816 = xs813
    if match_lookahead_literal(parser, "|", 0)
        _t1543 = parse_value_bindings(parser)
        _t1542 = _t1543
    else
        _t1542 = nothing
    end
    value_bindings817 = _t1542
    consume_literal!(parser, "]")
    return (bindings816, (!isnothing(value_bindings817) ? value_bindings817 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start820 = span_start(parser)
    symbol818 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1544 = parse_type(parser)
    type819 = _t1544
    _t1545 = Proto.Var(name=symbol818)
    _t1546 = Proto.Binding(var=_t1545, var"#type"=type819)
    result821 = _t1546
    record_span!(parser, span_start820, "Binding")
    return result821
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start837 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1547 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1548 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1549 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1550 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1551 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1552 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1553 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1554 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1555 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1556 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1557 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1558 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1559 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1560 = 9
                                                        else
                                                            _t1560 = -1
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
    prediction822 = _t1547
    if prediction822 == 13
        _t1562 = parse_uint32_type(parser)
        uint32_type836 = _t1562
        _t1563 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type836))
        _t1561 = _t1563
    else
        if prediction822 == 12
            _t1565 = parse_float32_type(parser)
            float32_type835 = _t1565
            _t1566 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type835))
            _t1564 = _t1566
        else
            if prediction822 == 11
                _t1568 = parse_int32_type(parser)
                int32_type834 = _t1568
                _t1569 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type834))
                _t1567 = _t1569
            else
                if prediction822 == 10
                    _t1571 = parse_boolean_type(parser)
                    boolean_type833 = _t1571
                    _t1572 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type833))
                    _t1570 = _t1572
                else
                    if prediction822 == 9
                        _t1574 = parse_decimal_type(parser)
                        decimal_type832 = _t1574
                        _t1575 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type832))
                        _t1573 = _t1575
                    else
                        if prediction822 == 8
                            _t1577 = parse_missing_type(parser)
                            missing_type831 = _t1577
                            _t1578 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type831))
                            _t1576 = _t1578
                        else
                            if prediction822 == 7
                                _t1580 = parse_datetime_type(parser)
                                datetime_type830 = _t1580
                                _t1581 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type830))
                                _t1579 = _t1581
                            else
                                if prediction822 == 6
                                    _t1583 = parse_date_type(parser)
                                    date_type829 = _t1583
                                    _t1584 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type829))
                                    _t1582 = _t1584
                                else
                                    if prediction822 == 5
                                        _t1586 = parse_int128_type(parser)
                                        int128_type828 = _t1586
                                        _t1587 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type828))
                                        _t1585 = _t1587
                                    else
                                        if prediction822 == 4
                                            _t1589 = parse_uint128_type(parser)
                                            uint128_type827 = _t1589
                                            _t1590 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type827))
                                            _t1588 = _t1590
                                        else
                                            if prediction822 == 3
                                                _t1592 = parse_float_type(parser)
                                                float_type826 = _t1592
                                                _t1593 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type826))
                                                _t1591 = _t1593
                                            else
                                                if prediction822 == 2
                                                    _t1595 = parse_int_type(parser)
                                                    int_type825 = _t1595
                                                    _t1596 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type825))
                                                    _t1594 = _t1596
                                                else
                                                    if prediction822 == 1
                                                        _t1598 = parse_string_type(parser)
                                                        string_type824 = _t1598
                                                        _t1599 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type824))
                                                        _t1597 = _t1599
                                                    else
                                                        if prediction822 == 0
                                                            _t1601 = parse_unspecified_type(parser)
                                                            unspecified_type823 = _t1601
                                                            _t1602 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type823))
                                                            _t1600 = _t1602
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                    _t1570 = _t1573
                end
                _t1567 = _t1570
            end
            _t1564 = _t1567
        end
        _t1561 = _t1564
    end
    result838 = _t1561
    record_span!(parser, span_start837, "Type")
    return result838
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start839 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1603 = Proto.UnspecifiedType()
    result840 = _t1603
    record_span!(parser, span_start839, "UnspecifiedType")
    return result840
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start841 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1604 = Proto.StringType()
    result842 = _t1604
    record_span!(parser, span_start841, "StringType")
    return result842
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start843 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1605 = Proto.IntType()
    result844 = _t1605
    record_span!(parser, span_start843, "IntType")
    return result844
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start845 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1606 = Proto.FloatType()
    result846 = _t1606
    record_span!(parser, span_start845, "FloatType")
    return result846
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start847 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1607 = Proto.UInt128Type()
    result848 = _t1607
    record_span!(parser, span_start847, "UInt128Type")
    return result848
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start849 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1608 = Proto.Int128Type()
    result850 = _t1608
    record_span!(parser, span_start849, "Int128Type")
    return result850
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start851 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1609 = Proto.DateType()
    result852 = _t1609
    record_span!(parser, span_start851, "DateType")
    return result852
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start853 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1610 = Proto.DateTimeType()
    result854 = _t1610
    record_span!(parser, span_start853, "DateTimeType")
    return result854
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start855 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1611 = Proto.MissingType()
    result856 = _t1611
    record_span!(parser, span_start855, "MissingType")
    return result856
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start859 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int857 = consume_terminal!(parser, "INT")
    int_3858 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1612 = Proto.DecimalType(precision=Int32(int857), scale=Int32(int_3858))
    result860 = _t1612
    record_span!(parser, span_start859, "DecimalType")
    return result860
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start861 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1613 = Proto.BooleanType()
    result862 = _t1613
    record_span!(parser, span_start861, "BooleanType")
    return result862
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start863 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1614 = Proto.Int32Type()
    result864 = _t1614
    record_span!(parser, span_start863, "Int32Type")
    return result864
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start865 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1615 = Proto.Float32Type()
    result866 = _t1615
    record_span!(parser, span_start865, "Float32Type")
    return result866
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start867 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1616 = Proto.UInt32Type()
    result868 = _t1616
    record_span!(parser, span_start867, "UInt32Type")
    return result868
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs869 = Proto.Binding[]
    cond870 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond870
        _t1617 = parse_binding(parser)
        item871 = _t1617
        push!(xs869, item871)
        cond870 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings872 = xs869
    return bindings872
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start887 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1619 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1620 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1621 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1622 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1623 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1624 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1625 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1626 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1627 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1628 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1629 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1630 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1631 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1632 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1633 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1634 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1635 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1636 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1637 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1638 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1639 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1640 = 10
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
    else
        _t1618 = -1
    end
    prediction873 = _t1618
    if prediction873 == 12
        _t1642 = parse_cast(parser)
        cast886 = _t1642
        _t1643 = Proto.Formula(formula_type=OneOf(:cast, cast886))
        _t1641 = _t1643
    else
        if prediction873 == 11
            _t1645 = parse_rel_atom(parser)
            rel_atom885 = _t1645
            _t1646 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom885))
            _t1644 = _t1646
        else
            if prediction873 == 10
                _t1648 = parse_primitive(parser)
                primitive884 = _t1648
                _t1649 = Proto.Formula(formula_type=OneOf(:primitive, primitive884))
                _t1647 = _t1649
            else
                if prediction873 == 9
                    _t1651 = parse_pragma(parser)
                    pragma883 = _t1651
                    _t1652 = Proto.Formula(formula_type=OneOf(:pragma, pragma883))
                    _t1650 = _t1652
                else
                    if prediction873 == 8
                        _t1654 = parse_atom(parser)
                        atom882 = _t1654
                        _t1655 = Proto.Formula(formula_type=OneOf(:atom, atom882))
                        _t1653 = _t1655
                    else
                        if prediction873 == 7
                            _t1657 = parse_ffi(parser)
                            ffi881 = _t1657
                            _t1658 = Proto.Formula(formula_type=OneOf(:ffi, ffi881))
                            _t1656 = _t1658
                        else
                            if prediction873 == 6
                                _t1660 = parse_not(parser)
                                not880 = _t1660
                                _t1661 = Proto.Formula(formula_type=OneOf(:not, not880))
                                _t1659 = _t1661
                            else
                                if prediction873 == 5
                                    _t1663 = parse_disjunction(parser)
                                    disjunction879 = _t1663
                                    _t1664 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction879))
                                    _t1662 = _t1664
                                else
                                    if prediction873 == 4
                                        _t1666 = parse_conjunction(parser)
                                        conjunction878 = _t1666
                                        _t1667 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction878))
                                        _t1665 = _t1667
                                    else
                                        if prediction873 == 3
                                            _t1669 = parse_reduce(parser)
                                            reduce877 = _t1669
                                            _t1670 = Proto.Formula(formula_type=OneOf(:reduce, reduce877))
                                            _t1668 = _t1670
                                        else
                                            if prediction873 == 2
                                                _t1672 = parse_exists(parser)
                                                exists876 = _t1672
                                                _t1673 = Proto.Formula(formula_type=OneOf(:exists, exists876))
                                                _t1671 = _t1673
                                            else
                                                if prediction873 == 1
                                                    _t1675 = parse_false(parser)
                                                    false875 = _t1675
                                                    _t1676 = Proto.Formula(formula_type=OneOf(:disjunction, false875))
                                                    _t1674 = _t1676
                                                else
                                                    if prediction873 == 0
                                                        _t1678 = parse_true(parser)
                                                        true874 = _t1678
                                                        _t1679 = Proto.Formula(formula_type=OneOf(:conjunction, true874))
                                                        _t1677 = _t1679
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1674 = _t1677
                                                end
                                                _t1671 = _t1674
                                            end
                                            _t1668 = _t1671
                                        end
                                        _t1665 = _t1668
                                    end
                                    _t1662 = _t1665
                                end
                                _t1659 = _t1662
                            end
                            _t1656 = _t1659
                        end
                        _t1653 = _t1656
                    end
                    _t1650 = _t1653
                end
                _t1647 = _t1650
            end
            _t1644 = _t1647
        end
        _t1641 = _t1644
    end
    result888 = _t1641
    record_span!(parser, span_start887, "Formula")
    return result888
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start889 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1680 = Proto.Conjunction(args=Proto.Formula[])
    result890 = _t1680
    record_span!(parser, span_start889, "Conjunction")
    return result890
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start891 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1681 = Proto.Disjunction(args=Proto.Formula[])
    result892 = _t1681
    record_span!(parser, span_start891, "Disjunction")
    return result892
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start895 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1682 = parse_bindings(parser)
    bindings893 = _t1682
    _t1683 = parse_formula(parser)
    formula894 = _t1683
    consume_literal!(parser, ")")
    _t1684 = Proto.Abstraction(vars=vcat(bindings893[1], !isnothing(bindings893[2]) ? bindings893[2] : []), value=formula894)
    _t1685 = Proto.Exists(body=_t1684)
    result896 = _t1685
    record_span!(parser, span_start895, "Exists")
    return result896
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start900 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1686 = parse_abstraction(parser)
    abstraction897 = _t1686
    _t1687 = parse_abstraction(parser)
    abstraction_3898 = _t1687
    _t1688 = parse_terms(parser)
    terms899 = _t1688
    consume_literal!(parser, ")")
    _t1689 = Proto.Reduce(op=abstraction897, body=abstraction_3898, terms=terms899)
    result901 = _t1689
    record_span!(parser, span_start900, "Reduce")
    return result901
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs902 = Proto.Term[]
    cond903 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond903
        _t1690 = parse_term(parser)
        item904 = _t1690
        push!(xs902, item904)
        cond903 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms905 = xs902
    consume_literal!(parser, ")")
    return terms905
end

function parse_term(parser::ParserState)::Proto.Term
    span_start909 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1691 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1692 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1693 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1694 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1695 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1696 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1697 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1698 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1699 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1700 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1701 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1702 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1703 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1704 = 1
                                                        else
                                                            _t1704 = -1
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
            _t1692 = _t1693
        end
        _t1691 = _t1692
    end
    prediction906 = _t1691
    if prediction906 == 1
        _t1706 = parse_value(parser)
        value908 = _t1706
        _t1707 = Proto.Term(term_type=OneOf(:constant, value908))
        _t1705 = _t1707
    else
        if prediction906 == 0
            _t1709 = parse_var(parser)
            var907 = _t1709
            _t1710 = Proto.Term(term_type=OneOf(:var, var907))
            _t1708 = _t1710
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1705 = _t1708
    end
    result910 = _t1705
    record_span!(parser, span_start909, "Term")
    return result910
end

function parse_var(parser::ParserState)::Proto.Var
    span_start912 = span_start(parser)
    symbol911 = consume_terminal!(parser, "SYMBOL")
    _t1711 = Proto.Var(name=symbol911)
    result913 = _t1711
    record_span!(parser, span_start912, "Var")
    return result913
end

function parse_value(parser::ParserState)::Proto.Value
    span_start927 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1712 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1713 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1714 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1716 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1717 = 0
                        else
                            _t1717 = -1
                        end
                        _t1716 = _t1717
                    end
                    _t1715 = _t1716
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1718 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1719 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1720 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1721 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1722 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1723 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1724 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1725 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1726 = 10
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
                    _t1715 = _t1718
                end
                _t1714 = _t1715
            end
            _t1713 = _t1714
        end
        _t1712 = _t1713
    end
    prediction914 = _t1712
    if prediction914 == 12
        _t1728 = parse_boolean_value(parser)
        boolean_value926 = _t1728
        _t1729 = Proto.Value(value=OneOf(:boolean_value, boolean_value926))
        _t1727 = _t1729
    else
        if prediction914 == 11
            consume_literal!(parser, "missing")
            _t1731 = Proto.MissingValue()
            _t1732 = Proto.Value(value=OneOf(:missing_value, _t1731))
            _t1730 = _t1732
        else
            if prediction914 == 10
                formatted_decimal925 = consume_terminal!(parser, "DECIMAL")
                _t1734 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal925))
                _t1733 = _t1734
            else
                if prediction914 == 9
                    formatted_int128924 = consume_terminal!(parser, "INT128")
                    _t1736 = Proto.Value(value=OneOf(:int128_value, formatted_int128924))
                    _t1735 = _t1736
                else
                    if prediction914 == 8
                        formatted_uint128923 = consume_terminal!(parser, "UINT128")
                        _t1738 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128923))
                        _t1737 = _t1738
                    else
                        if prediction914 == 7
                            formatted_uint32922 = consume_terminal!(parser, "UINT32")
                            _t1740 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32922))
                            _t1739 = _t1740
                        else
                            if prediction914 == 6
                                formatted_float921 = consume_terminal!(parser, "FLOAT")
                                _t1742 = Proto.Value(value=OneOf(:float_value, formatted_float921))
                                _t1741 = _t1742
                            else
                                if prediction914 == 5
                                    formatted_float32920 = consume_terminal!(parser, "FLOAT32")
                                    _t1744 = Proto.Value(value=OneOf(:float32_value, formatted_float32920))
                                    _t1743 = _t1744
                                else
                                    if prediction914 == 4
                                        formatted_int919 = consume_terminal!(parser, "INT")
                                        _t1746 = Proto.Value(value=OneOf(:int_value, formatted_int919))
                                        _t1745 = _t1746
                                    else
                                        if prediction914 == 3
                                            formatted_int32918 = consume_terminal!(parser, "INT32")
                                            _t1748 = Proto.Value(value=OneOf(:int32_value, formatted_int32918))
                                            _t1747 = _t1748
                                        else
                                            if prediction914 == 2
                                                formatted_string917 = consume_terminal!(parser, "STRING")
                                                _t1750 = Proto.Value(value=OneOf(:string_value, formatted_string917))
                                                _t1749 = _t1750
                                            else
                                                if prediction914 == 1
                                                    _t1752 = parse_datetime(parser)
                                                    datetime916 = _t1752
                                                    _t1753 = Proto.Value(value=OneOf(:datetime_value, datetime916))
                                                    _t1751 = _t1753
                                                else
                                                    if prediction914 == 0
                                                        _t1755 = parse_date(parser)
                                                        date915 = _t1755
                                                        _t1756 = Proto.Value(value=OneOf(:date_value, date915))
                                                        _t1754 = _t1756
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1751 = _t1754
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
                _t1733 = _t1735
            end
            _t1730 = _t1733
        end
        _t1727 = _t1730
    end
    result928 = _t1727
    record_span!(parser, span_start927, "Value")
    return result928
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start932 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int929 = consume_terminal!(parser, "INT")
    formatted_int_3930 = consume_terminal!(parser, "INT")
    formatted_int_4931 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1757 = Proto.DateValue(year=Int32(formatted_int929), month=Int32(formatted_int_3930), day=Int32(formatted_int_4931))
    result933 = _t1757
    record_span!(parser, span_start932, "DateValue")
    return result933
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start941 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int934 = consume_terminal!(parser, "INT")
    formatted_int_3935 = consume_terminal!(parser, "INT")
    formatted_int_4936 = consume_terminal!(parser, "INT")
    formatted_int_5937 = consume_terminal!(parser, "INT")
    formatted_int_6938 = consume_terminal!(parser, "INT")
    formatted_int_7939 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1758 = consume_terminal!(parser, "INT")
    else
        _t1758 = nothing
    end
    formatted_int_8940 = _t1758
    consume_literal!(parser, ")")
    _t1759 = Proto.DateTimeValue(year=Int32(formatted_int934), month=Int32(formatted_int_3935), day=Int32(formatted_int_4936), hour=Int32(formatted_int_5937), minute=Int32(formatted_int_6938), second=Int32(formatted_int_7939), microsecond=Int32((!isnothing(formatted_int_8940) ? formatted_int_8940 : 0)))
    result942 = _t1759
    record_span!(parser, span_start941, "DateTimeValue")
    return result942
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start947 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs943 = Proto.Formula[]
    cond944 = match_lookahead_literal(parser, "(", 0)
    while cond944
        _t1760 = parse_formula(parser)
        item945 = _t1760
        push!(xs943, item945)
        cond944 = match_lookahead_literal(parser, "(", 0)
    end
    formulas946 = xs943
    consume_literal!(parser, ")")
    _t1761 = Proto.Conjunction(args=formulas946)
    result948 = _t1761
    record_span!(parser, span_start947, "Conjunction")
    return result948
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start953 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs949 = Proto.Formula[]
    cond950 = match_lookahead_literal(parser, "(", 0)
    while cond950
        _t1762 = parse_formula(parser)
        item951 = _t1762
        push!(xs949, item951)
        cond950 = match_lookahead_literal(parser, "(", 0)
    end
    formulas952 = xs949
    consume_literal!(parser, ")")
    _t1763 = Proto.Disjunction(args=formulas952)
    result954 = _t1763
    record_span!(parser, span_start953, "Disjunction")
    return result954
end

function parse_not(parser::ParserState)::Proto.Not
    span_start956 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1764 = parse_formula(parser)
    formula955 = _t1764
    consume_literal!(parser, ")")
    _t1765 = Proto.Not(arg=formula955)
    result957 = _t1765
    record_span!(parser, span_start956, "Not")
    return result957
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start961 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1766 = parse_name(parser)
    name958 = _t1766
    _t1767 = parse_ffi_args(parser)
    ffi_args959 = _t1767
    _t1768 = parse_terms(parser)
    terms960 = _t1768
    consume_literal!(parser, ")")
    _t1769 = Proto.FFI(name=name958, args=ffi_args959, terms=terms960)
    result962 = _t1769
    record_span!(parser, span_start961, "FFI")
    return result962
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol963 = consume_terminal!(parser, "SYMBOL")
    return symbol963
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs964 = Proto.Abstraction[]
    cond965 = match_lookahead_literal(parser, "(", 0)
    while cond965
        _t1770 = parse_abstraction(parser)
        item966 = _t1770
        push!(xs964, item966)
        cond965 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions967 = xs964
    consume_literal!(parser, ")")
    return abstractions967
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start973 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1771 = parse_relation_id(parser)
    relation_id968 = _t1771
    xs969 = Proto.Term[]
    cond970 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond970
        _t1772 = parse_term(parser)
        item971 = _t1772
        push!(xs969, item971)
        cond970 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms972 = xs969
    consume_literal!(parser, ")")
    _t1773 = Proto.Atom(name=relation_id968, terms=terms972)
    result974 = _t1773
    record_span!(parser, span_start973, "Atom")
    return result974
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1774 = parse_name(parser)
    name975 = _t1774
    xs976 = Proto.Term[]
    cond977 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond977
        _t1775 = parse_term(parser)
        item978 = _t1775
        push!(xs976, item978)
        cond977 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms979 = xs976
    consume_literal!(parser, ")")
    _t1776 = Proto.Pragma(name=name975, terms=terms979)
    result981 = _t1776
    record_span!(parser, span_start980, "Pragma")
    return result981
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start997 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1778 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1779 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1780 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1781 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1782 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1783 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1784 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1785 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1786 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1787 = 7
                                            else
                                                _t1787 = -1
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
            end
            _t1778 = _t1779
        end
        _t1777 = _t1778
    else
        _t1777 = -1
    end
    prediction982 = _t1777
    if prediction982 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1789 = parse_name(parser)
        name992 = _t1789
        xs993 = Proto.RelTerm[]
        cond994 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond994
            _t1790 = parse_rel_term(parser)
            item995 = _t1790
            push!(xs993, item995)
            cond994 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms996 = xs993
        consume_literal!(parser, ")")
        _t1791 = Proto.Primitive(name=name992, terms=rel_terms996)
        _t1788 = _t1791
    else
        if prediction982 == 8
            _t1793 = parse_divide(parser)
            divide991 = _t1793
            _t1792 = divide991
        else
            if prediction982 == 7
                _t1795 = parse_multiply(parser)
                multiply990 = _t1795
                _t1794 = multiply990
            else
                if prediction982 == 6
                    _t1797 = parse_minus(parser)
                    minus989 = _t1797
                    _t1796 = minus989
                else
                    if prediction982 == 5
                        _t1799 = parse_add(parser)
                        add988 = _t1799
                        _t1798 = add988
                    else
                        if prediction982 == 4
                            _t1801 = parse_gt_eq(parser)
                            gt_eq987 = _t1801
                            _t1800 = gt_eq987
                        else
                            if prediction982 == 3
                                _t1803 = parse_gt(parser)
                                gt986 = _t1803
                                _t1802 = gt986
                            else
                                if prediction982 == 2
                                    _t1805 = parse_lt_eq(parser)
                                    lt_eq985 = _t1805
                                    _t1804 = lt_eq985
                                else
                                    if prediction982 == 1
                                        _t1807 = parse_lt(parser)
                                        lt984 = _t1807
                                        _t1806 = lt984
                                    else
                                        if prediction982 == 0
                                            _t1809 = parse_eq(parser)
                                            eq983 = _t1809
                                            _t1808 = eq983
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
            _t1792 = _t1794
        end
        _t1788 = _t1792
    end
    result998 = _t1788
    record_span!(parser, span_start997, "Primitive")
    return result998
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start1001 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1810 = parse_term(parser)
    term999 = _t1810
    _t1811 = parse_term(parser)
    term_31000 = _t1811
    consume_literal!(parser, ")")
    _t1812 = Proto.RelTerm(rel_term_type=OneOf(:term, term999))
    _t1813 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31000))
    _t1814 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1812, _t1813])
    result1002 = _t1814
    record_span!(parser, span_start1001, "Primitive")
    return result1002
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start1005 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1815 = parse_term(parser)
    term1003 = _t1815
    _t1816 = parse_term(parser)
    term_31004 = _t1816
    consume_literal!(parser, ")")
    _t1817 = Proto.RelTerm(rel_term_type=OneOf(:term, term1003))
    _t1818 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31004))
    _t1819 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1817, _t1818])
    result1006 = _t1819
    record_span!(parser, span_start1005, "Primitive")
    return result1006
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start1009 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1820 = parse_term(parser)
    term1007 = _t1820
    _t1821 = parse_term(parser)
    term_31008 = _t1821
    consume_literal!(parser, ")")
    _t1822 = Proto.RelTerm(rel_term_type=OneOf(:term, term1007))
    _t1823 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31008))
    _t1824 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1822, _t1823])
    result1010 = _t1824
    record_span!(parser, span_start1009, "Primitive")
    return result1010
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start1013 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1825 = parse_term(parser)
    term1011 = _t1825
    _t1826 = parse_term(parser)
    term_31012 = _t1826
    consume_literal!(parser, ")")
    _t1827 = Proto.RelTerm(rel_term_type=OneOf(:term, term1011))
    _t1828 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31012))
    _t1829 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1827, _t1828])
    result1014 = _t1829
    record_span!(parser, span_start1013, "Primitive")
    return result1014
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start1017 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1830 = parse_term(parser)
    term1015 = _t1830
    _t1831 = parse_term(parser)
    term_31016 = _t1831
    consume_literal!(parser, ")")
    _t1832 = Proto.RelTerm(rel_term_type=OneOf(:term, term1015))
    _t1833 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31016))
    _t1834 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1832, _t1833])
    result1018 = _t1834
    record_span!(parser, span_start1017, "Primitive")
    return result1018
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start1022 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1835 = parse_term(parser)
    term1019 = _t1835
    _t1836 = parse_term(parser)
    term_31020 = _t1836
    _t1837 = parse_term(parser)
    term_41021 = _t1837
    consume_literal!(parser, ")")
    _t1838 = Proto.RelTerm(rel_term_type=OneOf(:term, term1019))
    _t1839 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31020))
    _t1840 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41021))
    _t1841 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1838, _t1839, _t1840])
    result1023 = _t1841
    record_span!(parser, span_start1022, "Primitive")
    return result1023
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start1027 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1842 = parse_term(parser)
    term1024 = _t1842
    _t1843 = parse_term(parser)
    term_31025 = _t1843
    _t1844 = parse_term(parser)
    term_41026 = _t1844
    consume_literal!(parser, ")")
    _t1845 = Proto.RelTerm(rel_term_type=OneOf(:term, term1024))
    _t1846 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31025))
    _t1847 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41026))
    _t1848 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1845, _t1846, _t1847])
    result1028 = _t1848
    record_span!(parser, span_start1027, "Primitive")
    return result1028
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1032 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1849 = parse_term(parser)
    term1029 = _t1849
    _t1850 = parse_term(parser)
    term_31030 = _t1850
    _t1851 = parse_term(parser)
    term_41031 = _t1851
    consume_literal!(parser, ")")
    _t1852 = Proto.RelTerm(rel_term_type=OneOf(:term, term1029))
    _t1853 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31030))
    _t1854 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41031))
    _t1855 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1852, _t1853, _t1854])
    result1033 = _t1855
    record_span!(parser, span_start1032, "Primitive")
    return result1033
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1037 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1856 = parse_term(parser)
    term1034 = _t1856
    _t1857 = parse_term(parser)
    term_31035 = _t1857
    _t1858 = parse_term(parser)
    term_41036 = _t1858
    consume_literal!(parser, ")")
    _t1859 = Proto.RelTerm(rel_term_type=OneOf(:term, term1034))
    _t1860 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31035))
    _t1861 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41036))
    _t1862 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1859, _t1860, _t1861])
    result1038 = _t1862
    record_span!(parser, span_start1037, "Primitive")
    return result1038
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1042 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1863 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1864 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1865 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1866 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1867 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1868 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1869 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1870 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1871 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1872 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1873 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1874 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1875 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1876 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1877 = 1
                                                            else
                                                                _t1877 = -1
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
            _t1864 = _t1865
        end
        _t1863 = _t1864
    end
    prediction1039 = _t1863
    if prediction1039 == 1
        _t1879 = parse_term(parser)
        term1041 = _t1879
        _t1880 = Proto.RelTerm(rel_term_type=OneOf(:term, term1041))
        _t1878 = _t1880
    else
        if prediction1039 == 0
            _t1882 = parse_specialized_value(parser)
            specialized_value1040 = _t1882
            _t1883 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1040))
            _t1881 = _t1883
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1878 = _t1881
    end
    result1043 = _t1878
    record_span!(parser, span_start1042, "RelTerm")
    return result1043
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1045 = span_start(parser)
    consume_literal!(parser, "#")
    _t1884 = parse_raw_value(parser)
    raw_value1044 = _t1884
    result1046 = raw_value1044
    record_span!(parser, span_start1045, "Value")
    return result1046
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1052 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1885 = parse_name(parser)
    name1047 = _t1885
    xs1048 = Proto.RelTerm[]
    cond1049 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1049
        _t1886 = parse_rel_term(parser)
        item1050 = _t1886
        push!(xs1048, item1050)
        cond1049 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1051 = xs1048
    consume_literal!(parser, ")")
    _t1887 = Proto.RelAtom(name=name1047, terms=rel_terms1051)
    result1053 = _t1887
    record_span!(parser, span_start1052, "RelAtom")
    return result1053
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1056 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1888 = parse_term(parser)
    term1054 = _t1888
    _t1889 = parse_term(parser)
    term_31055 = _t1889
    consume_literal!(parser, ")")
    _t1890 = Proto.Cast(input=term1054, result=term_31055)
    result1057 = _t1890
    record_span!(parser, span_start1056, "Cast")
    return result1057
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1058 = Proto.Attribute[]
    cond1059 = match_lookahead_literal(parser, "(", 0)
    while cond1059
        _t1891 = parse_attribute(parser)
        item1060 = _t1891
        push!(xs1058, item1060)
        cond1059 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1061 = xs1058
    consume_literal!(parser, ")")
    return attributes1061
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1067 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1892 = parse_name(parser)
    name1062 = _t1892
    xs1063 = Proto.Value[]
    cond1064 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1064
        _t1893 = parse_raw_value(parser)
        item1065 = _t1893
        push!(xs1063, item1065)
        cond1064 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1066 = xs1063
    consume_literal!(parser, ")")
    _t1894 = Proto.Attribute(name=name1062, args=raw_values1066)
    result1068 = _t1894
    record_span!(parser, span_start1067, "Attribute")
    return result1068
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1075 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1069 = Proto.RelationId[]
    cond1070 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1070
        _t1895 = parse_relation_id(parser)
        item1071 = _t1895
        push!(xs1069, item1071)
        cond1070 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1072 = xs1069
    _t1896 = parse_script(parser)
    script1073 = _t1896
    if match_lookahead_literal(parser, "(", 0)
        _t1898 = parse_attrs(parser)
        _t1897 = _t1898
    else
        _t1897 = nothing
    end
    attrs1074 = _t1897
    consume_literal!(parser, ")")
    _t1899 = Proto.Algorithm(var"#global"=relation_ids1072, body=script1073, attrs=(!isnothing(attrs1074) ? attrs1074 : Proto.Attribute[]))
    result1076 = _t1899
    record_span!(parser, span_start1075, "Algorithm")
    return result1076
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1081 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1077 = Proto.Construct[]
    cond1078 = match_lookahead_literal(parser, "(", 0)
    while cond1078
        _t1900 = parse_construct(parser)
        item1079 = _t1900
        push!(xs1077, item1079)
        cond1078 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1080 = xs1077
    consume_literal!(parser, ")")
    _t1901 = Proto.Script(constructs=constructs1080)
    result1082 = _t1901
    record_span!(parser, span_start1081, "Script")
    return result1082
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1086 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1903 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1904 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1905 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1906 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1907 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1908 = 1
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
            end
            _t1903 = _t1904
        end
        _t1902 = _t1903
    else
        _t1902 = -1
    end
    prediction1083 = _t1902
    if prediction1083 == 1
        _t1910 = parse_instruction(parser)
        instruction1085 = _t1910
        _t1911 = Proto.Construct(construct_type=OneOf(:instruction, instruction1085))
        _t1909 = _t1911
    else
        if prediction1083 == 0
            _t1913 = parse_loop(parser)
            loop1084 = _t1913
            _t1914 = Proto.Construct(construct_type=OneOf(:loop, loop1084))
            _t1912 = _t1914
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1909 = _t1912
    end
    result1087 = _t1909
    record_span!(parser, span_start1086, "Construct")
    return result1087
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1091 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1915 = parse_init(parser)
    init1088 = _t1915
    _t1916 = parse_script(parser)
    script1089 = _t1916
    if match_lookahead_literal(parser, "(", 0)
        _t1918 = parse_attrs(parser)
        _t1917 = _t1918
    else
        _t1917 = nothing
    end
    attrs1090 = _t1917
    consume_literal!(parser, ")")
    _t1919 = Proto.Loop(init=init1088, body=script1089, attrs=(!isnothing(attrs1090) ? attrs1090 : Proto.Attribute[]))
    result1092 = _t1919
    record_span!(parser, span_start1091, "Loop")
    return result1092
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1093 = Proto.Instruction[]
    cond1094 = match_lookahead_literal(parser, "(", 0)
    while cond1094
        _t1920 = parse_instruction(parser)
        item1095 = _t1920
        push!(xs1093, item1095)
        cond1094 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1096 = xs1093
    consume_literal!(parser, ")")
    return instructions1096
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1103 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1922 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1923 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1924 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1925 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1926 = 0
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
        end
        _t1921 = _t1922
    else
        _t1921 = -1
    end
    prediction1097 = _t1921
    if prediction1097 == 4
        _t1928 = parse_monus_def(parser)
        monus_def1102 = _t1928
        _t1929 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1102))
        _t1927 = _t1929
    else
        if prediction1097 == 3
            _t1931 = parse_monoid_def(parser)
            monoid_def1101 = _t1931
            _t1932 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1101))
            _t1930 = _t1932
        else
            if prediction1097 == 2
                _t1934 = parse_break(parser)
                break1100 = _t1934
                _t1935 = Proto.Instruction(instr_type=OneOf(:var"#break", break1100))
                _t1933 = _t1935
            else
                if prediction1097 == 1
                    _t1937 = parse_upsert(parser)
                    upsert1099 = _t1937
                    _t1938 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1099))
                    _t1936 = _t1938
                else
                    if prediction1097 == 0
                        _t1940 = parse_assign(parser)
                        assign1098 = _t1940
                        _t1941 = Proto.Instruction(instr_type=OneOf(:assign, assign1098))
                        _t1939 = _t1941
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1936 = _t1939
                end
                _t1933 = _t1936
            end
            _t1930 = _t1933
        end
        _t1927 = _t1930
    end
    result1104 = _t1927
    record_span!(parser, span_start1103, "Instruction")
    return result1104
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1108 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1942 = parse_relation_id(parser)
    relation_id1105 = _t1942
    _t1943 = parse_abstraction(parser)
    abstraction1106 = _t1943
    if match_lookahead_literal(parser, "(", 0)
        _t1945 = parse_attrs(parser)
        _t1944 = _t1945
    else
        _t1944 = nothing
    end
    attrs1107 = _t1944
    consume_literal!(parser, ")")
    _t1946 = Proto.Assign(name=relation_id1105, body=abstraction1106, attrs=(!isnothing(attrs1107) ? attrs1107 : Proto.Attribute[]))
    result1109 = _t1946
    record_span!(parser, span_start1108, "Assign")
    return result1109
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1113 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1947 = parse_relation_id(parser)
    relation_id1110 = _t1947
    _t1948 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1111 = _t1948
    if match_lookahead_literal(parser, "(", 0)
        _t1950 = parse_attrs(parser)
        _t1949 = _t1950
    else
        _t1949 = nothing
    end
    attrs1112 = _t1949
    consume_literal!(parser, ")")
    _t1951 = Proto.Upsert(name=relation_id1110, body=abstraction_with_arity1111[1], attrs=(!isnothing(attrs1112) ? attrs1112 : Proto.Attribute[]), value_arity=abstraction_with_arity1111[2])
    result1114 = _t1951
    record_span!(parser, span_start1113, "Upsert")
    return result1114
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1952 = parse_bindings(parser)
    bindings1115 = _t1952
    _t1953 = parse_formula(parser)
    formula1116 = _t1953
    consume_literal!(parser, ")")
    _t1954 = Proto.Abstraction(vars=vcat(bindings1115[1], !isnothing(bindings1115[2]) ? bindings1115[2] : []), value=formula1116)
    return (_t1954, length(bindings1115[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1120 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1955 = parse_relation_id(parser)
    relation_id1117 = _t1955
    _t1956 = parse_abstraction(parser)
    abstraction1118 = _t1956
    if match_lookahead_literal(parser, "(", 0)
        _t1958 = parse_attrs(parser)
        _t1957 = _t1958
    else
        _t1957 = nothing
    end
    attrs1119 = _t1957
    consume_literal!(parser, ")")
    _t1959 = Proto.Break(name=relation_id1117, body=abstraction1118, attrs=(!isnothing(attrs1119) ? attrs1119 : Proto.Attribute[]))
    result1121 = _t1959
    record_span!(parser, span_start1120, "Break")
    return result1121
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1126 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1960 = parse_monoid(parser)
    monoid1122 = _t1960
    _t1961 = parse_relation_id(parser)
    relation_id1123 = _t1961
    _t1962 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1124 = _t1962
    if match_lookahead_literal(parser, "(", 0)
        _t1964 = parse_attrs(parser)
        _t1963 = _t1964
    else
        _t1963 = nothing
    end
    attrs1125 = _t1963
    consume_literal!(parser, ")")
    _t1965 = Proto.MonoidDef(monoid=monoid1122, name=relation_id1123, body=abstraction_with_arity1124[1], attrs=(!isnothing(attrs1125) ? attrs1125 : Proto.Attribute[]), value_arity=abstraction_with_arity1124[2])
    result1127 = _t1965
    record_span!(parser, span_start1126, "MonoidDef")
    return result1127
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1133 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1967 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1968 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1969 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1970 = 2
                    else
                        _t1970 = -1
                    end
                    _t1969 = _t1970
                end
                _t1968 = _t1969
            end
            _t1967 = _t1968
        end
        _t1966 = _t1967
    else
        _t1966 = -1
    end
    prediction1128 = _t1966
    if prediction1128 == 3
        _t1972 = parse_sum_monoid(parser)
        sum_monoid1132 = _t1972
        _t1973 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1132))
        _t1971 = _t1973
    else
        if prediction1128 == 2
            _t1975 = parse_max_monoid(parser)
            max_monoid1131 = _t1975
            _t1976 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1131))
            _t1974 = _t1976
        else
            if prediction1128 == 1
                _t1978 = parse_min_monoid(parser)
                min_monoid1130 = _t1978
                _t1979 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1130))
                _t1977 = _t1979
            else
                if prediction1128 == 0
                    _t1981 = parse_or_monoid(parser)
                    or_monoid1129 = _t1981
                    _t1982 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1129))
                    _t1980 = _t1982
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1977 = _t1980
            end
            _t1974 = _t1977
        end
        _t1971 = _t1974
    end
    result1134 = _t1971
    record_span!(parser, span_start1133, "Monoid")
    return result1134
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1135 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1983 = Proto.OrMonoid()
    result1136 = _t1983
    record_span!(parser, span_start1135, "OrMonoid")
    return result1136
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1138 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1984 = parse_type(parser)
    type1137 = _t1984
    consume_literal!(parser, ")")
    _t1985 = Proto.MinMonoid(var"#type"=type1137)
    result1139 = _t1985
    record_span!(parser, span_start1138, "MinMonoid")
    return result1139
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1141 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1986 = parse_type(parser)
    type1140 = _t1986
    consume_literal!(parser, ")")
    _t1987 = Proto.MaxMonoid(var"#type"=type1140)
    result1142 = _t1987
    record_span!(parser, span_start1141, "MaxMonoid")
    return result1142
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1144 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1988 = parse_type(parser)
    type1143 = _t1988
    consume_literal!(parser, ")")
    _t1989 = Proto.SumMonoid(var"#type"=type1143)
    result1145 = _t1989
    record_span!(parser, span_start1144, "SumMonoid")
    return result1145
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1150 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1990 = parse_monoid(parser)
    monoid1146 = _t1990
    _t1991 = parse_relation_id(parser)
    relation_id1147 = _t1991
    _t1992 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1148 = _t1992
    if match_lookahead_literal(parser, "(", 0)
        _t1994 = parse_attrs(parser)
        _t1993 = _t1994
    else
        _t1993 = nothing
    end
    attrs1149 = _t1993
    consume_literal!(parser, ")")
    _t1995 = Proto.MonusDef(monoid=monoid1146, name=relation_id1147, body=abstraction_with_arity1148[1], attrs=(!isnothing(attrs1149) ? attrs1149 : Proto.Attribute[]), value_arity=abstraction_with_arity1148[2])
    result1151 = _t1995
    record_span!(parser, span_start1150, "MonusDef")
    return result1151
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1156 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1996 = parse_relation_id(parser)
    relation_id1152 = _t1996
    _t1997 = parse_abstraction(parser)
    abstraction1153 = _t1997
    _t1998 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1154 = _t1998
    _t1999 = parse_functional_dependency_values(parser)
    functional_dependency_values1155 = _t1999
    consume_literal!(parser, ")")
    _t2000 = Proto.FunctionalDependency(guard=abstraction1153, keys=functional_dependency_keys1154, values=functional_dependency_values1155)
    _t2001 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t2000), name=relation_id1152)
    result1157 = _t2001
    record_span!(parser, span_start1156, "Constraint")
    return result1157
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1158 = Proto.Var[]
    cond1159 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1159
        _t2002 = parse_var(parser)
        item1160 = _t2002
        push!(xs1158, item1160)
        cond1159 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1161 = xs1158
    consume_literal!(parser, ")")
    return vars1161
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1162 = Proto.Var[]
    cond1163 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1163
        _t2003 = parse_var(parser)
        item1164 = _t2003
        push!(xs1162, item1164)
        cond1163 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1165 = xs1162
    consume_literal!(parser, ")")
    return vars1165
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1171 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t2005 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t2006 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t2007 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t2008 = 1
                    else
                        _t2008 = -1
                    end
                    _t2007 = _t2008
                end
                _t2006 = _t2007
            end
            _t2005 = _t2006
        end
        _t2004 = _t2005
    else
        _t2004 = -1
    end
    prediction1166 = _t2004
    if prediction1166 == 3
        _t2010 = parse_iceberg_data(parser)
        iceberg_data1170 = _t2010
        _t2011 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1170))
        _t2009 = _t2011
    else
        if prediction1166 == 2
            _t2013 = parse_csv_data(parser)
            csv_data1169 = _t2013
            _t2014 = Proto.Data(data_type=OneOf(:csv_data, csv_data1169))
            _t2012 = _t2014
        else
            if prediction1166 == 1
                _t2016 = parse_betree_relation(parser)
                betree_relation1168 = _t2016
                _t2017 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1168))
                _t2015 = _t2017
            else
                if prediction1166 == 0
                    _t2019 = parse_edb(parser)
                    edb1167 = _t2019
                    _t2020 = Proto.Data(data_type=OneOf(:edb, edb1167))
                    _t2018 = _t2020
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t2015 = _t2018
            end
            _t2012 = _t2015
        end
        _t2009 = _t2012
    end
    result1172 = _t2009
    record_span!(parser, span_start1171, "Data")
    return result1172
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1176 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t2021 = parse_relation_id(parser)
    relation_id1173 = _t2021
    _t2022 = parse_edb_path(parser)
    edb_path1174 = _t2022
    _t2023 = parse_edb_types(parser)
    edb_types1175 = _t2023
    consume_literal!(parser, ")")
    _t2024 = Proto.EDB(target_id=relation_id1173, path=edb_path1174, types=edb_types1175)
    result1177 = _t2024
    record_span!(parser, span_start1176, "EDB")
    return result1177
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1178 = String[]
    cond1179 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1179
        item1180 = consume_terminal!(parser, "STRING")
        push!(xs1178, item1180)
        cond1179 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1181 = xs1178
    consume_literal!(parser, "]")
    return strings1181
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1182 = Proto.var"#Type"[]
    cond1183 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1183
        _t2025 = parse_type(parser)
        item1184 = _t2025
        push!(xs1182, item1184)
        cond1183 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1185 = xs1182
    consume_literal!(parser, "]")
    return types1185
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1188 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t2026 = parse_relation_id(parser)
    relation_id1186 = _t2026
    _t2027 = parse_betree_info(parser)
    betree_info1187 = _t2027
    consume_literal!(parser, ")")
    _t2028 = Proto.BeTreeRelation(name=relation_id1186, relation_info=betree_info1187)
    result1189 = _t2028
    record_span!(parser, span_start1188, "BeTreeRelation")
    return result1189
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1193 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t2029 = parse_betree_info_key_types(parser)
    betree_info_key_types1190 = _t2029
    _t2030 = parse_betree_info_value_types(parser)
    betree_info_value_types1191 = _t2030
    _t2031 = parse_config_dict(parser)
    config_dict1192 = _t2031
    consume_literal!(parser, ")")
    _t2032 = construct_betree_info(parser, betree_info_key_types1190, betree_info_value_types1191, config_dict1192)
    result1194 = _t2032
    record_span!(parser, span_start1193, "BeTreeInfo")
    return result1194
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1195 = Proto.var"#Type"[]
    cond1196 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1196
        _t2033 = parse_type(parser)
        item1197 = _t2033
        push!(xs1195, item1197)
        cond1196 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1198 = xs1195
    consume_literal!(parser, ")")
    return types1198
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1199 = Proto.var"#Type"[]
    cond1200 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1200
        _t2034 = parse_type(parser)
        item1201 = _t2034
        push!(xs1199, item1201)
        cond1200 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1202 = xs1199
    consume_literal!(parser, ")")
    return types1202
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1208 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t2035 = parse_csvlocator(parser)
    csvlocator1203 = _t2035
    _t2036 = parse_csv_config(parser)
    csv_config1204 = _t2036
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t2038 = parse_gnf_columns(parser)
        _t2037 = _t2038
    else
        _t2037 = nothing
    end
    gnf_columns1205 = _t2037
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relations", 1))
        _t2040 = parse_target_relations(parser)
        _t2039 = _t2040
    else
        _t2039 = nothing
    end
    target_relations1206 = _t2039
    _t2041 = parse_csv_asof(parser)
    csv_asof1207 = _t2041
    consume_literal!(parser, ")")
    _t2042 = construct_csv_data(parser, csvlocator1203, csv_config1204, gnf_columns1205, target_relations1206, csv_asof1207)
    result1209 = _t2042
    record_span!(parser, span_start1208, "CSVData")
    return result1209
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1212 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t2044 = parse_csv_locator_paths(parser)
        _t2043 = _t2044
    else
        _t2043 = nothing
    end
    csv_locator_paths1210 = _t2043
    if match_lookahead_literal(parser, "(", 0)
        _t2046 = parse_csv_locator_inline_data(parser)
        _t2045 = _t2046
    else
        _t2045 = nothing
    end
    csv_locator_inline_data1211 = _t2045
    consume_literal!(parser, ")")
    _t2047 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1210) ? csv_locator_paths1210 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1211) ? csv_locator_inline_data1211 : "")))
    result1213 = _t2047
    record_span!(parser, span_start1212, "CSVLocator")
    return result1213
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1214 = String[]
    cond1215 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1215
        item1216 = consume_terminal!(parser, "STRING")
        push!(xs1214, item1216)
        cond1215 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1217 = xs1214
    consume_literal!(parser, ")")
    return strings1217
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1218 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1218
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1221 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t2048 = parse_config_dict(parser)
    config_dict1219 = _t2048
    if match_lookahead_literal(parser, "(", 0)
        _t2050 = parse__storage_integration(parser)
        _t2049 = _t2050
    else
        _t2049 = nothing
    end
    _storage_integration1220 = _t2049
    consume_literal!(parser, ")")
    _t2051 = construct_csv_config(parser, config_dict1219, _storage_integration1220)
    result1222 = _t2051
    record_span!(parser, span_start1221, "CSVConfig")
    return result1222
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t2052 = parse_config_dict(parser)
    config_dict1223 = _t2052
    consume_literal!(parser, ")")
    return config_dict1223
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1224 = Proto.GNFColumn[]
    cond1225 = match_lookahead_literal(parser, "(", 0)
    while cond1225
        _t2053 = parse_gnf_column(parser)
        item1226 = _t2053
        push!(xs1224, item1226)
        cond1225 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1227 = xs1224
    consume_literal!(parser, ")")
    return gnf_columns1227
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1234 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t2054 = parse_gnf_column_path(parser)
    gnf_column_path1228 = _t2054
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t2056 = parse_relation_id(parser)
        _t2055 = _t2056
    else
        _t2055 = nothing
    end
    relation_id1229 = _t2055
    consume_literal!(parser, "[")
    xs1230 = Proto.var"#Type"[]
    cond1231 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1231
        _t2057 = parse_type(parser)
        item1232 = _t2057
        push!(xs1230, item1232)
        cond1231 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1233 = xs1230
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2058 = Proto.GNFColumn(column_path=gnf_column_path1228, target_id=relation_id1229, types=types1233)
    result1235 = _t2058
    record_span!(parser, span_start1234, "GNFColumn")
    return result1235
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t2059 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t2060 = 0
        else
            _t2060 = -1
        end
        _t2059 = _t2060
    end
    prediction1236 = _t2059
    if prediction1236 == 1
        consume_literal!(parser, "[")
        xs1238 = String[]
        cond1239 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1239
            item1240 = consume_terminal!(parser, "STRING")
            push!(xs1238, item1240)
            cond1239 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1241 = xs1238
        consume_literal!(parser, "]")
        _t2061 = strings1241
    else
        if prediction1236 == 0
            string1237 = consume_terminal!(parser, "STRING")
            _t2062 = String[string1237]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t2061 = _t2062
    end
    return _t2061
end

function parse_target_relations(parser::ParserState)::Proto.TargetRelations
    span_start1244 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relations")
    _t2063 = parse_relation_keys(parser)
    relation_keys1242 = _t2063
    _t2064 = parse_relation_body(parser)
    relation_body1243 = _t2064
    consume_literal!(parser, ")")
    _t2065 = construct_relations(parser, relation_keys1242, relation_body1243)
    result1245 = _t2065
    record_span!(parser, span_start1244, "TargetRelations")
    return result1245
end

function parse_relation_keys(parser::ParserState)::Tuple{Vector{Proto.NamedColumn}, Bool}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "keys", 1)
            if match_lookahead_literal(parser, "synthetic", 2)
                _t2068 = 1
            else
                if match_lookahead_literal(parser, ")", 2)
                    _t2069 = 0
                else
                    if match_lookahead_literal(parser, "(", 2)
                        _t2070 = 0
                    else
                        _t2070 = -1
                    end
                    _t2069 = _t2070
                end
                _t2068 = _t2069
            end
            _t2067 = _t2068
        else
            _t2067 = -1
        end
        _t2066 = _t2067
    else
        _t2066 = -1
    end
    prediction1246 = _t2066
    if prediction1246 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "keys")
        consume_literal!(parser, "synthetic")
        consume_literal!(parser, ")")
        _t2071 = (Proto.NamedColumn[], true,)
    else
        if prediction1246 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "keys")
            xs1247 = Proto.NamedColumn[]
            cond1248 = match_lookahead_literal(parser, "(", 0)
            while cond1248
                _t2073 = parse_named_column(parser)
                item1249 = _t2073
                push!(xs1247, item1249)
                cond1248 = match_lookahead_literal(parser, "(", 0)
            end
            named_columns1250 = xs1247
            consume_literal!(parser, ")")
            _t2072 = (named_columns1250, false,)
        else
            throw(ParseError("Unexpected token in relation_keys" * ": " * string(lookahead(parser, 0))))
        end
        _t2071 = _t2072
    end
    return _t2071
end

function parse_named_column(parser::ParserState)::Proto.NamedColumn
    span_start1253 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1251 = consume_terminal!(parser, "STRING")
    _t2074 = parse_type(parser)
    type1252 = _t2074
    consume_literal!(parser, ")")
    _t2075 = Proto.NamedColumn(name=string1251, var"#type"=type1252)
    result1254 = _t2075
    record_span!(parser, span_start1253, "NamedColumn")
    return result1254
end

function parse_relation_body(parser::ParserState)::Proto.TargetRelations
    span_start1259 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "relation", 1)
            _t2077 = 0
        else
            if match_lookahead_literal(parser, "inserts", 1)
                _t2078 = 1
            else
                _t2078 = 0
            end
            _t2077 = _t2078
        end
        _t2076 = _t2077
    else
        _t2076 = 0
    end
    prediction1255 = _t2076
    if prediction1255 == 1
        _t2080 = parse_cdc_inserts(parser)
        cdc_inserts1257 = _t2080
        _t2081 = parse_cdc_deletes(parser)
        cdc_deletes1258 = _t2081
        _t2082 = construct_cdc_relations(parser, cdc_inserts1257, cdc_deletes1258)
        _t2079 = _t2082
    else
        if prediction1255 == 0
            _t2084 = parse_non_cdc_relations(parser)
            non_cdc_relations1256 = _t2084
            _t2085 = construct_non_cdc_relations(parser, non_cdc_relations1256)
            _t2083 = _t2085
        else
            throw(ParseError("Unexpected token in relation_body" * ": " * string(lookahead(parser, 0))))
        end
        _t2079 = _t2083
    end
    result1260 = _t2079
    record_span!(parser, span_start1259, "TargetRelations")
    return result1260
end

function parse_non_cdc_relations(parser::ParserState)::Vector{Proto.TargetRelation}
    xs1261 = Proto.TargetRelation[]
    cond1262 = match_lookahead_literal(parser, "(", 0)
    while cond1262
        _t2086 = parse_target_relation(parser)
        item1263 = _t2086
        push!(xs1261, item1263)
        cond1262 = match_lookahead_literal(parser, "(", 0)
    end
    return xs1261
end

function parse_target_relation(parser::ParserState)::Proto.TargetRelation
    span_start1269 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relation")
    _t2087 = parse_relation_id(parser)
    relation_id1264 = _t2087
    xs1265 = Proto.NamedColumn[]
    cond1266 = match_lookahead_literal(parser, "(", 0)
    while cond1266
        _t2088 = parse_named_column(parser)
        item1267 = _t2088
        push!(xs1265, item1267)
        cond1266 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1268 = xs1265
    consume_literal!(parser, ")")
    _t2089 = Proto.TargetRelation(target_id=relation_id1264, values=named_columns1268)
    result1270 = _t2089
    record_span!(parser, span_start1269, "TargetRelation")
    return result1270
end

function parse_cdc_inserts(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "inserts")
    xs1271 = Proto.TargetRelation[]
    cond1272 = match_lookahead_literal(parser, "(", 0)
    while cond1272
        _t2090 = parse_target_relation(parser)
        item1273 = _t2090
        push!(xs1271, item1273)
        cond1272 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1274 = xs1271
    consume_literal!(parser, ")")
    return target_relations1274
end

function parse_cdc_deletes(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "deletes")
    xs1275 = Proto.TargetRelation[]
    cond1276 = match_lookahead_literal(parser, "(", 0)
    while cond1276
        _t2091 = parse_target_relation(parser)
        item1277 = _t2091
        push!(xs1275, item1277)
        cond1276 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1278 = xs1275
    consume_literal!(parser, ")")
    return target_relations1278
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1279 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1279
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1286 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t2092 = parse_iceberg_locator(parser)
    iceberg_locator1280 = _t2092
    _t2093 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1281 = _t2093
    _t2094 = parse_gnf_columns(parser)
    gnf_columns1282 = _t2094
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2096 = parse_iceberg_from_snapshot(parser)
        _t2095 = _t2096
    else
        _t2095 = nothing
    end
    iceberg_from_snapshot1283 = _t2095
    if match_lookahead_literal(parser, "(", 0)
        _t2098 = parse_iceberg_to_snapshot(parser)
        _t2097 = _t2098
    else
        _t2097 = nothing
    end
    iceberg_to_snapshot1284 = _t2097
    _t2099 = parse_boolean_value(parser)
    boolean_value1285 = _t2099
    consume_literal!(parser, ")")
    _t2100 = construct_iceberg_data(parser, iceberg_locator1280, iceberg_catalog_config1281, gnf_columns1282, iceberg_from_snapshot1283, iceberg_to_snapshot1284, boolean_value1285)
    result1287 = _t2100
    record_span!(parser, span_start1286, "IcebergData")
    return result1287
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1291 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2101 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1288 = _t2101
    _t2102 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1289 = _t2102
    _t2103 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1290 = _t2103
    consume_literal!(parser, ")")
    _t2104 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1288, namespace=iceberg_locator_namespace1289, warehouse=iceberg_locator_warehouse1290)
    result1292 = _t2104
    record_span!(parser, span_start1291, "IcebergLocator")
    return result1292
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1293 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1293
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1294 = String[]
    cond1295 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1295
        item1296 = consume_terminal!(parser, "STRING")
        push!(xs1294, item1296)
        cond1295 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1297 = xs1294
    consume_literal!(parser, ")")
    return strings1297
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1298 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1298
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1303 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2105 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1299 = _t2105
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2107 = parse_iceberg_catalog_config_scope(parser)
        _t2106 = _t2107
    else
        _t2106 = nothing
    end
    iceberg_catalog_config_scope1300 = _t2106
    _t2108 = parse_iceberg_properties(parser)
    iceberg_properties1301 = _t2108
    _t2109 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1302 = _t2109
    consume_literal!(parser, ")")
    _t2110 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1299, iceberg_catalog_config_scope1300, iceberg_properties1301, iceberg_auth_properties1302)
    result1304 = _t2110
    record_span!(parser, span_start1303, "IcebergCatalogConfig")
    return result1304
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1305 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1305
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1306 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1306
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1307 = Tuple{String, String}[]
    cond1308 = match_lookahead_literal(parser, "(", 0)
    while cond1308
        _t2111 = parse_iceberg_property_entry(parser)
        item1309 = _t2111
        push!(xs1307, item1309)
        cond1308 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1310 = xs1307
    consume_literal!(parser, ")")
    return iceberg_property_entrys1310
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1311 = consume_terminal!(parser, "STRING")
    string_31312 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1311, string_31312,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1313 = Tuple{String, String}[]
    cond1314 = match_lookahead_literal(parser, "(", 0)
    while cond1314
        _t2112 = parse_iceberg_masked_property_entry(parser)
        item1315 = _t2112
        push!(xs1313, item1315)
        cond1314 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1316 = xs1313
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1316
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1317 = consume_terminal!(parser, "STRING")
    string_31318 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1317, string_31318,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1319 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1319
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1320 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1320
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1322 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2113 = parse_fragment_id(parser)
    fragment_id1321 = _t2113
    consume_literal!(parser, ")")
    _t2114 = Proto.Undefine(fragment_id=fragment_id1321)
    result1323 = _t2114
    record_span!(parser, span_start1322, "Undefine")
    return result1323
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1328 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1324 = Proto.RelationId[]
    cond1325 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1325
        _t2115 = parse_relation_id(parser)
        item1326 = _t2115
        push!(xs1324, item1326)
        cond1325 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1327 = xs1324
    consume_literal!(parser, ")")
    _t2116 = Proto.Context(relations=relation_ids1327)
    result1329 = _t2116
    record_span!(parser, span_start1328, "Context")
    return result1329
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1335 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2117 = parse_edb_path(parser)
    edb_path1330 = _t2117
    xs1331 = Proto.SnapshotMapping[]
    cond1332 = match_lookahead_literal(parser, "[", 0)
    while cond1332
        _t2118 = parse_snapshot_mapping(parser)
        item1333 = _t2118
        push!(xs1331, item1333)
        cond1332 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1334 = xs1331
    consume_literal!(parser, ")")
    _t2119 = Proto.Snapshot(mappings=snapshot_mappings1334, prefix=edb_path1330)
    result1336 = _t2119
    record_span!(parser, span_start1335, "Snapshot")
    return result1336
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1339 = span_start(parser)
    _t2120 = parse_edb_path(parser)
    edb_path1337 = _t2120
    _t2121 = parse_relation_id(parser)
    relation_id1338 = _t2121
    _t2122 = Proto.SnapshotMapping(destination_path=edb_path1337, source_relation=relation_id1338)
    result1340 = _t2122
    record_span!(parser, span_start1339, "SnapshotMapping")
    return result1340
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1341 = Proto.Read[]
    cond1342 = match_lookahead_literal(parser, "(", 0)
    while cond1342
        _t2123 = parse_read(parser)
        item1343 = _t2123
        push!(xs1341, item1343)
        cond1342 = match_lookahead_literal(parser, "(", 0)
    end
    reads1344 = xs1341
    consume_literal!(parser, ")")
    return reads1344
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1351 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2125 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2126 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2127 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2128 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2129 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2130 = 3
                            else
                                _t2130 = -1
                            end
                            _t2129 = _t2130
                        end
                        _t2128 = _t2129
                    end
                    _t2127 = _t2128
                end
                _t2126 = _t2127
            end
            _t2125 = _t2126
        end
        _t2124 = _t2125
    else
        _t2124 = -1
    end
    prediction1345 = _t2124
    if prediction1345 == 4
        _t2132 = parse_export(parser)
        export1350 = _t2132
        _t2133 = Proto.Read(read_type=OneOf(:var"#export", export1350))
        _t2131 = _t2133
    else
        if prediction1345 == 3
            _t2135 = parse_abort(parser)
            abort1349 = _t2135
            _t2136 = Proto.Read(read_type=OneOf(:abort, abort1349))
            _t2134 = _t2136
        else
            if prediction1345 == 2
                _t2138 = parse_what_if(parser)
                what_if1348 = _t2138
                _t2139 = Proto.Read(read_type=OneOf(:what_if, what_if1348))
                _t2137 = _t2139
            else
                if prediction1345 == 1
                    _t2141 = parse_output(parser)
                    output1347 = _t2141
                    _t2142 = Proto.Read(read_type=OneOf(:output, output1347))
                    _t2140 = _t2142
                else
                    if prediction1345 == 0
                        _t2144 = parse_demand(parser)
                        demand1346 = _t2144
                        _t2145 = Proto.Read(read_type=OneOf(:demand, demand1346))
                        _t2143 = _t2145
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2140 = _t2143
                end
                _t2137 = _t2140
            end
            _t2134 = _t2137
        end
        _t2131 = _t2134
    end
    result1352 = _t2131
    record_span!(parser, span_start1351, "Read")
    return result1352
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1354 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2146 = parse_relation_id(parser)
    relation_id1353 = _t2146
    consume_literal!(parser, ")")
    _t2147 = Proto.Demand(relation_id=relation_id1353)
    result1355 = _t2147
    record_span!(parser, span_start1354, "Demand")
    return result1355
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1358 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2148 = parse_name(parser)
    name1356 = _t2148
    _t2149 = parse_relation_id(parser)
    relation_id1357 = _t2149
    consume_literal!(parser, ")")
    _t2150 = Proto.Output(name=name1356, relation_id=relation_id1357)
    result1359 = _t2150
    record_span!(parser, span_start1358, "Output")
    return result1359
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1362 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2151 = parse_name(parser)
    name1360 = _t2151
    _t2152 = parse_epoch(parser)
    epoch1361 = _t2152
    consume_literal!(parser, ")")
    _t2153 = Proto.WhatIf(branch=name1360, epoch=epoch1361)
    result1363 = _t2153
    record_span!(parser, span_start1362, "WhatIf")
    return result1363
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1366 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2155 = parse_name(parser)
        _t2154 = _t2155
    else
        _t2154 = nothing
    end
    name1364 = _t2154
    _t2156 = parse_relation_id(parser)
    relation_id1365 = _t2156
    consume_literal!(parser, ")")
    _t2157 = Proto.Abort(name=(!isnothing(name1364) ? name1364 : "abort"), relation_id=relation_id1365)
    result1367 = _t2157
    record_span!(parser, span_start1366, "Abort")
    return result1367
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1371 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2159 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2160 = 0
            else
                _t2160 = -1
            end
            _t2159 = _t2160
        end
        _t2158 = _t2159
    else
        _t2158 = -1
    end
    prediction1368 = _t2158
    if prediction1368 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2162 = parse_export_iceberg_config(parser)
        export_iceberg_config1370 = _t2162
        consume_literal!(parser, ")")
        _t2163 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1370))
        _t2161 = _t2163
    else
        if prediction1368 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2165 = parse_export_csv_config(parser)
            export_csv_config1369 = _t2165
            consume_literal!(parser, ")")
            _t2166 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1369))
            _t2164 = _t2166
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2161 = _t2164
    end
    result1372 = _t2161
    record_span!(parser, span_start1371, "Export")
    return result1372
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1380 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2168 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2169 = 1
            else
                _t2169 = -1
            end
            _t2168 = _t2169
        end
        _t2167 = _t2168
    else
        _t2167 = -1
    end
    prediction1373 = _t2167
    if prediction1373 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2171 = parse_export_csv_path(parser)
        export_csv_path1377 = _t2171
        _t2172 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1378 = _t2172
        _t2173 = parse_config_dict(parser)
        config_dict1379 = _t2173
        consume_literal!(parser, ")")
        _t2174 = construct_export_csv_config(parser, export_csv_path1377, export_csv_columns_list1378, config_dict1379)
        _t2170 = _t2174
    else
        if prediction1373 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2176 = parse_export_csv_output_location(parser)
            export_csv_output_location1374 = _t2176
            _t2177 = parse_export_csv_source(parser)
            export_csv_source1375 = _t2177
            _t2178 = parse_csv_config(parser)
            csv_config1376 = _t2178
            consume_literal!(parser, ")")
            _t2179 = construct_export_csv_config_with_location(parser, export_csv_output_location1374, export_csv_source1375, csv_config1376)
            _t2175 = _t2179
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2170 = _t2175
    end
    result1381 = _t2170
    record_span!(parser, span_start1380, "ExportCSVConfig")
    return result1381
end

function parse_export_csv_output_location(parser::ParserState)::Tuple{String, String}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "transaction_output_name", 1)
            _t2181 = 1
        else
            if match_lookahead_literal(parser, "path", 1)
                _t2182 = 0
            else
                _t2182 = -1
            end
            _t2181 = _t2182
        end
        _t2180 = _t2181
    else
        _t2180 = -1
    end
    prediction1382 = _t2180
    if prediction1382 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "transaction_output_name")
        _t2184 = parse_name(parser)
        name1384 = _t2184
        consume_literal!(parser, ")")
        _t2183 = ("", name1384,)
    else
        if prediction1382 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "path")
            string1383 = consume_terminal!(parser, "STRING")
            consume_literal!(parser, ")")
            _t2185 = (string1383, "",)
        else
            throw(ParseError("Unexpected token in export_csv_output_location" * ": " * string(lookahead(parser, 0))))
        end
        _t2183 = _t2185
    end
    return _t2183
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1391 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2187 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2188 = 0
            else
                _t2188 = -1
            end
            _t2187 = _t2188
        end
        _t2186 = _t2187
    else
        _t2186 = -1
    end
    prediction1385 = _t2186
    if prediction1385 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2190 = parse_relation_id(parser)
        relation_id1390 = _t2190
        consume_literal!(parser, ")")
        _t2191 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1390))
        _t2189 = _t2191
    else
        if prediction1385 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1386 = Proto.ExportCSVColumn[]
            cond1387 = match_lookahead_literal(parser, "(", 0)
            while cond1387
                _t2193 = parse_export_csv_column(parser)
                item1388 = _t2193
                push!(xs1386, item1388)
                cond1387 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1389 = xs1386
            consume_literal!(parser, ")")
            _t2194 = Proto.ExportCSVColumns(columns=export_csv_columns1389)
            _t2195 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2194))
            _t2192 = _t2195
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2189 = _t2192
    end
    result1392 = _t2189
    record_span!(parser, span_start1391, "ExportCSVSource")
    return result1392
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1395 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1393 = consume_terminal!(parser, "STRING")
    _t2196 = parse_relation_id(parser)
    relation_id1394 = _t2196
    consume_literal!(parser, ")")
    _t2197 = Proto.ExportCSVColumn(column_name=string1393, column_data=relation_id1394)
    result1396 = _t2197
    record_span!(parser, span_start1395, "ExportCSVColumn")
    return result1396
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1397 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1397
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1398 = Proto.ExportCSVColumn[]
    cond1399 = match_lookahead_literal(parser, "(", 0)
    while cond1399
        _t2198 = parse_export_csv_column(parser)
        item1400 = _t2198
        push!(xs1398, item1400)
        cond1399 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1401 = xs1398
    consume_literal!(parser, ")")
    return export_csv_columns1401
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1407 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2199 = parse_iceberg_locator(parser)
    iceberg_locator1402 = _t2199
    _t2200 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1403 = _t2200
    _t2201 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1404 = _t2201
    _t2202 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1405 = _t2202
    if match_lookahead_literal(parser, "{", 0)
        _t2204 = parse_config_dict(parser)
        _t2203 = _t2204
    else
        _t2203 = nothing
    end
    config_dict1406 = _t2203
    consume_literal!(parser, ")")
    _t2205 = construct_export_iceberg_config_full(parser, iceberg_locator1402, iceberg_catalog_config1403, export_iceberg_table_def1404, iceberg_table_properties1405, config_dict1406)
    result1408 = _t2205
    record_span!(parser, span_start1407, "ExportIcebergConfig")
    return result1408
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1410 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2206 = parse_relation_id(parser)
    relation_id1409 = _t2206
    consume_literal!(parser, ")")
    result1411 = relation_id1409
    record_span!(parser, span_start1410, "RelationId")
    return result1411
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1412 = Tuple{String, String}[]
    cond1413 = match_lookahead_literal(parser, "(", 0)
    while cond1413
        _t2207 = parse_iceberg_property_entry(parser)
        item1414 = _t2207
        push!(xs1412, item1414)
        cond1413 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1415 = xs1412
    consume_literal!(parser, ")")
    return iceberg_property_entrys1415
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
