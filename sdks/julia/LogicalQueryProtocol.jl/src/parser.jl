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
        _t2199 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2200 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2201 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2202 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2203 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2204 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2205 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2206 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2207 = nothing
    end
    return nothing
end

function construct_non_cdc_relations(parser::ParserState, targets::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2208 = Proto.PlainTargets(targets=targets)
    _t2209 = Proto.TargetRelations(body=OneOf(:plain, _t2208), keys=Proto.NamedColumn[])
    return _t2209
end

function construct_cdc_relations(parser::ParserState, inserts::Vector{Proto.TargetRelation}, deletes::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2210 = Proto.CDCTargets(inserts=inserts, deletes=deletes)
    _t2211 = Proto.TargetRelations(body=OneOf(:cdc, _t2210), keys=Proto.NamedColumn[])
    return _t2211
end

function construct_relations(parser::ParserState, keys::Vector{Proto.NamedColumn}, body::Proto.TargetRelations)::Proto.TargetRelations
    if _has_proto_field(body, Symbol("plain"))
        _t2213 = Proto.TargetRelations(body=OneOf(:plain, _get_oneof_field(body, :plain)), keys=keys)
        return _t2213
    else
        _t2212 = nothing
    end
    _t2214 = Proto.TargetRelations(body=OneOf(:cdc, _get_oneof_field(body, :cdc)), keys=keys)
    return _t2214
end

function construct_csv_data(parser::ParserState, locator::Proto.CSVLocator, config::Proto.CSVConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, relations_opt::Union{Nothing, Proto.TargetRelations}, asof::String)::Proto.CSVData
    _t2215 = Proto.CSVData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), asof=asof, relations=relations_opt)
    return _t2215
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2216 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2216
    _t2217 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2217
    _t2218 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2218
    _t2219 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2219
    _t2220 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2220
    _t2221 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2221
    _t2222 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2222
    _t2223 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2223
    _t2224 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2224
    _t2225 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2225
    _t2226 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2226
    _t2227 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2227
    _t2228 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2228
    _t2229 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2229
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2230 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2231 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2232 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2233 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2234 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2235 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2236 = Proto.StorageIntegration(provider=_t2231, azure_sas_token=_t2232, s3_region=_t2233, s3_access_key_id=_t2234, s3_secret_access_key=_t2235)
    return _t2236
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2237 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2237
    _t2238 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2238
    _t2239 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2239
    _t2240 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2240
    _t2241 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2241
    _t2242 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2242
    _t2243 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2243
    _t2244 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2244
    _t2245 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2245
    _t2246 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2246
    _t2247 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2247
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2248 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2248
    _t2249 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2249
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
    _t2250 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2250
    _t2251 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2251
    _t2252 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2252
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2253 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2253
    _t2254 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2254
    _t2255 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2255
    _t2256 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2256
    _t2257 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2257
    _t2258 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2258
    _t2259 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2259
    _t2260 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2260
end

function construct_export_csv_config_with_location(parser::ParserState, location::Tuple{String, String}, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2261 = Proto.ExportCSVConfig(path=location[1], transaction_output_name=location[2], csv_source=csv_source, csv_config=csv_config)
    return _t2261
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2262 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2262
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2263 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2263
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2264 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2264
    _t2265 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2265
    _t2266 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2266
    table_props = Dict(table_property_pairs)
    _t2267 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2267
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start713 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1415 = parse_configure(parser)
        _t1414 = _t1415
    else
        _t1414 = nothing
    end
    configure707 = _t1414
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1417 = parse_sync(parser)
        _t1416 = _t1417
    else
        _t1416 = nothing
    end
    sync708 = _t1416
    xs709 = Proto.Epoch[]
    cond710 = match_lookahead_literal(parser, "(", 0)
    while cond710
        _t1418 = parse_epoch(parser)
        item711 = _t1418
        push!(xs709, item711)
        cond710 = match_lookahead_literal(parser, "(", 0)
    end
    epochs712 = xs709
    consume_literal!(parser, ")")
    _t1419 = default_configure(parser)
    _t1420 = Proto.Transaction(epochs=epochs712, configure=(!isnothing(configure707) ? configure707 : _t1419), sync=sync708)
    result714 = _t1420
    record_span!(parser, span_start713, "Transaction")
    return result714
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start716 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1421 = parse_config_dict(parser)
    config_dict715 = _t1421
    consume_literal!(parser, ")")
    _t1422 = construct_configure(parser, config_dict715)
    result717 = _t1422
    record_span!(parser, span_start716, "Configure")
    return result717
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs718 = Tuple{String, Proto.Value}[]
    cond719 = match_lookahead_literal(parser, ":", 0)
    while cond719
        _t1423 = parse_config_key_value(parser)
        item720 = _t1423
        push!(xs718, item720)
        cond719 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values721 = xs718
    consume_literal!(parser, "}")
    return config_key_values721
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol722 = consume_terminal!(parser, "SYMBOL")
    _t1424 = parse_raw_value(parser)
    raw_value723 = _t1424
    return (symbol722, raw_value723,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start737 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1425 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1426 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1427 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1429 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1430 = 0
                        else
                            _t1430 = -1
                        end
                        _t1429 = _t1430
                    end
                    _t1428 = _t1429
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1431 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1432 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1433 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1434 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1435 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1436 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1437 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1438 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1439 = 10
                                                    else
                                                        _t1439 = -1
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
                            _t1432 = _t1433
                        end
                        _t1431 = _t1432
                    end
                    _t1428 = _t1431
                end
                _t1427 = _t1428
            end
            _t1426 = _t1427
        end
        _t1425 = _t1426
    end
    prediction724 = _t1425
    if prediction724 == 12
        _t1441 = parse_boolean_value(parser)
        boolean_value736 = _t1441
        _t1442 = Proto.Value(value=OneOf(:boolean_value, boolean_value736))
        _t1440 = _t1442
    else
        if prediction724 == 11
            consume_literal!(parser, "missing")
            _t1444 = Proto.MissingValue()
            _t1445 = Proto.Value(value=OneOf(:missing_value, _t1444))
            _t1443 = _t1445
        else
            if prediction724 == 10
                decimal735 = consume_terminal!(parser, "DECIMAL")
                _t1447 = Proto.Value(value=OneOf(:decimal_value, decimal735))
                _t1446 = _t1447
            else
                if prediction724 == 9
                    int128734 = consume_terminal!(parser, "INT128")
                    _t1449 = Proto.Value(value=OneOf(:int128_value, int128734))
                    _t1448 = _t1449
                else
                    if prediction724 == 8
                        uint128733 = consume_terminal!(parser, "UINT128")
                        _t1451 = Proto.Value(value=OneOf(:uint128_value, uint128733))
                        _t1450 = _t1451
                    else
                        if prediction724 == 7
                            uint32732 = consume_terminal!(parser, "UINT32")
                            _t1453 = Proto.Value(value=OneOf(:uint32_value, uint32732))
                            _t1452 = _t1453
                        else
                            if prediction724 == 6
                                float731 = consume_terminal!(parser, "FLOAT")
                                _t1455 = Proto.Value(value=OneOf(:float_value, float731))
                                _t1454 = _t1455
                            else
                                if prediction724 == 5
                                    float32730 = consume_terminal!(parser, "FLOAT32")
                                    _t1457 = Proto.Value(value=OneOf(:float32_value, float32730))
                                    _t1456 = _t1457
                                else
                                    if prediction724 == 4
                                        int729 = consume_terminal!(parser, "INT")
                                        _t1459 = Proto.Value(value=OneOf(:int_value, int729))
                                        _t1458 = _t1459
                                    else
                                        if prediction724 == 3
                                            int32728 = consume_terminal!(parser, "INT32")
                                            _t1461 = Proto.Value(value=OneOf(:int32_value, int32728))
                                            _t1460 = _t1461
                                        else
                                            if prediction724 == 2
                                                string727 = consume_terminal!(parser, "STRING")
                                                _t1463 = Proto.Value(value=OneOf(:string_value, string727))
                                                _t1462 = _t1463
                                            else
                                                if prediction724 == 1
                                                    _t1465 = parse_raw_datetime(parser)
                                                    raw_datetime726 = _t1465
                                                    _t1466 = Proto.Value(value=OneOf(:datetime_value, raw_datetime726))
                                                    _t1464 = _t1466
                                                else
                                                    if prediction724 == 0
                                                        _t1468 = parse_raw_date(parser)
                                                        raw_date725 = _t1468
                                                        _t1469 = Proto.Value(value=OneOf(:date_value, raw_date725))
                                                        _t1467 = _t1469
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1464 = _t1467
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
                _t1446 = _t1448
            end
            _t1443 = _t1446
        end
        _t1440 = _t1443
    end
    result738 = _t1440
    record_span!(parser, span_start737, "Value")
    return result738
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start742 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int739 = consume_terminal!(parser, "INT")
    int_3740 = consume_terminal!(parser, "INT")
    int_4741 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1470 = Proto.DateValue(year=Int32(int739), month=Int32(int_3740), day=Int32(int_4741))
    result743 = _t1470
    record_span!(parser, span_start742, "DateValue")
    return result743
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start751 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int744 = consume_terminal!(parser, "INT")
    int_3745 = consume_terminal!(parser, "INT")
    int_4746 = consume_terminal!(parser, "INT")
    int_5747 = consume_terminal!(parser, "INT")
    int_6748 = consume_terminal!(parser, "INT")
    int_7749 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1471 = consume_terminal!(parser, "INT")
    else
        _t1471 = nothing
    end
    int_8750 = _t1471
    consume_literal!(parser, ")")
    _t1472 = Proto.DateTimeValue(year=Int32(int744), month=Int32(int_3745), day=Int32(int_4746), hour=Int32(int_5747), minute=Int32(int_6748), second=Int32(int_7749), microsecond=Int32((!isnothing(int_8750) ? int_8750 : 0)))
    result752 = _t1472
    record_span!(parser, span_start751, "DateTimeValue")
    return result752
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1473 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1474 = 1
        else
            _t1474 = -1
        end
        _t1473 = _t1474
    end
    prediction753 = _t1473
    if prediction753 == 1
        consume_literal!(parser, "false")
        _t1475 = false
    else
        if prediction753 == 0
            consume_literal!(parser, "true")
            _t1476 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1475 = _t1476
    end
    return _t1475
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start758 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs754 = Proto.FragmentId[]
    cond755 = match_lookahead_literal(parser, ":", 0)
    while cond755
        _t1477 = parse_fragment_id(parser)
        item756 = _t1477
        push!(xs754, item756)
        cond755 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids757 = xs754
    consume_literal!(parser, ")")
    _t1478 = Proto.Sync(fragments=fragment_ids757)
    result759 = _t1478
    record_span!(parser, span_start758, "Sync")
    return result759
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start761 = span_start(parser)
    consume_literal!(parser, ":")
    symbol760 = consume_terminal!(parser, "SYMBOL")
    result762 = Proto.FragmentId(Vector{UInt8}(symbol760))
    record_span!(parser, span_start761, "FragmentId")
    return result762
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start765 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1480 = parse_epoch_writes(parser)
        _t1479 = _t1480
    else
        _t1479 = nothing
    end
    epoch_writes763 = _t1479
    if match_lookahead_literal(parser, "(", 0)
        _t1482 = parse_epoch_reads(parser)
        _t1481 = _t1482
    else
        _t1481 = nothing
    end
    epoch_reads764 = _t1481
    consume_literal!(parser, ")")
    _t1483 = Proto.Epoch(writes=(!isnothing(epoch_writes763) ? epoch_writes763 : Proto.Write[]), reads=(!isnothing(epoch_reads764) ? epoch_reads764 : Proto.Read[]))
    result766 = _t1483
    record_span!(parser, span_start765, "Epoch")
    return result766
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs767 = Proto.Write[]
    cond768 = match_lookahead_literal(parser, "(", 0)
    while cond768
        _t1484 = parse_write(parser)
        item769 = _t1484
        push!(xs767, item769)
        cond768 = match_lookahead_literal(parser, "(", 0)
    end
    writes770 = xs767
    consume_literal!(parser, ")")
    return writes770
end

function parse_write(parser::ParserState)::Proto.Write
    span_start776 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1486 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1487 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1488 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1489 = 2
                    else
                        _t1489 = -1
                    end
                    _t1488 = _t1489
                end
                _t1487 = _t1488
            end
            _t1486 = _t1487
        end
        _t1485 = _t1486
    else
        _t1485 = -1
    end
    prediction771 = _t1485
    if prediction771 == 3
        _t1491 = parse_snapshot(parser)
        snapshot775 = _t1491
        _t1492 = Proto.Write(write_type=OneOf(:snapshot, snapshot775))
        _t1490 = _t1492
    else
        if prediction771 == 2
            _t1494 = parse_context(parser)
            context774 = _t1494
            _t1495 = Proto.Write(write_type=OneOf(:context, context774))
            _t1493 = _t1495
        else
            if prediction771 == 1
                _t1497 = parse_undefine(parser)
                undefine773 = _t1497
                _t1498 = Proto.Write(write_type=OneOf(:undefine, undefine773))
                _t1496 = _t1498
            else
                if prediction771 == 0
                    _t1500 = parse_define(parser)
                    define772 = _t1500
                    _t1501 = Proto.Write(write_type=OneOf(:define, define772))
                    _t1499 = _t1501
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1496 = _t1499
            end
            _t1493 = _t1496
        end
        _t1490 = _t1493
    end
    result777 = _t1490
    record_span!(parser, span_start776, "Write")
    return result777
end

function parse_define(parser::ParserState)::Proto.Define
    span_start779 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1502 = parse_fragment(parser)
    fragment778 = _t1502
    consume_literal!(parser, ")")
    _t1503 = Proto.Define(fragment=fragment778)
    result780 = _t1503
    record_span!(parser, span_start779, "Define")
    return result780
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start786 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1504 = parse_new_fragment_id(parser)
    new_fragment_id781 = _t1504
    xs782 = Proto.Declaration[]
    cond783 = match_lookahead_literal(parser, "(", 0)
    while cond783
        _t1505 = parse_declaration(parser)
        item784 = _t1505
        push!(xs782, item784)
        cond783 = match_lookahead_literal(parser, "(", 0)
    end
    declarations785 = xs782
    consume_literal!(parser, ")")
    result787 = construct_fragment(parser, new_fragment_id781, declarations785)
    record_span!(parser, span_start786, "Fragment")
    return result787
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start789 = span_start(parser)
    _t1506 = parse_fragment_id(parser)
    fragment_id788 = _t1506
    start_fragment!(parser, fragment_id788)
    result790 = fragment_id788
    record_span!(parser, span_start789, "FragmentId")
    return result790
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start796 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1508 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1509 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1510 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1511 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1512 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1513 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1514 = 1
                                else
                                    _t1514 = -1
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
            end
            _t1508 = _t1509
        end
        _t1507 = _t1508
    else
        _t1507 = -1
    end
    prediction791 = _t1507
    if prediction791 == 3
        _t1516 = parse_data(parser)
        data795 = _t1516
        _t1517 = Proto.Declaration(declaration_type=OneOf(:data, data795))
        _t1515 = _t1517
    else
        if prediction791 == 2
            _t1519 = parse_constraint(parser)
            constraint794 = _t1519
            _t1520 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint794))
            _t1518 = _t1520
        else
            if prediction791 == 1
                _t1522 = parse_algorithm(parser)
                algorithm793 = _t1522
                _t1523 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm793))
                _t1521 = _t1523
            else
                if prediction791 == 0
                    _t1525 = parse_def(parser)
                    def792 = _t1525
                    _t1526 = Proto.Declaration(declaration_type=OneOf(:def, def792))
                    _t1524 = _t1526
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1521 = _t1524
            end
            _t1518 = _t1521
        end
        _t1515 = _t1518
    end
    result797 = _t1515
    record_span!(parser, span_start796, "Declaration")
    return result797
end

function parse_def(parser::ParserState)::Proto.Def
    span_start801 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1527 = parse_relation_id(parser)
    relation_id798 = _t1527
    _t1528 = parse_abstraction(parser)
    abstraction799 = _t1528
    if match_lookahead_literal(parser, "(", 0)
        _t1530 = parse_attrs(parser)
        _t1529 = _t1530
    else
        _t1529 = nothing
    end
    attrs800 = _t1529
    consume_literal!(parser, ")")
    _t1531 = Proto.Def(name=relation_id798, body=abstraction799, attrs=(!isnothing(attrs800) ? attrs800 : Proto.Attribute[]))
    result802 = _t1531
    record_span!(parser, span_start801, "Def")
    return result802
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start806 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1532 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1533 = 1
        else
            _t1533 = -1
        end
        _t1532 = _t1533
    end
    prediction803 = _t1532
    if prediction803 == 1
        uint128805 = consume_terminal!(parser, "UINT128")
        _t1534 = Proto.RelationId(uint128805.low, uint128805.high)
    else
        if prediction803 == 0
            consume_literal!(parser, ":")
            symbol804 = consume_terminal!(parser, "SYMBOL")
            _t1535 = relation_id_from_string(parser, symbol804)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1534 = _t1535
    end
    result807 = _t1534
    record_span!(parser, span_start806, "RelationId")
    return result807
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start810 = span_start(parser)
    consume_literal!(parser, "(")
    _t1536 = parse_bindings(parser)
    bindings808 = _t1536
    _t1537 = parse_formula(parser)
    formula809 = _t1537
    consume_literal!(parser, ")")
    _t1538 = Proto.Abstraction(vars=vcat(bindings808[1], !isnothing(bindings808[2]) ? bindings808[2] : []), value=formula809)
    result811 = _t1538
    record_span!(parser, span_start810, "Abstraction")
    return result811
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs812 = Proto.Binding[]
    cond813 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond813
        _t1539 = parse_binding(parser)
        item814 = _t1539
        push!(xs812, item814)
        cond813 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings815 = xs812
    if match_lookahead_literal(parser, "|", 0)
        _t1541 = parse_value_bindings(parser)
        _t1540 = _t1541
    else
        _t1540 = nothing
    end
    value_bindings816 = _t1540
    consume_literal!(parser, "]")
    return (bindings815, (!isnothing(value_bindings816) ? value_bindings816 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start819 = span_start(parser)
    symbol817 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1542 = parse_type(parser)
    type818 = _t1542
    _t1543 = Proto.Var(name=symbol817)
    _t1544 = Proto.Binding(var=_t1543, var"#type"=type818)
    result820 = _t1544
    record_span!(parser, span_start819, "Binding")
    return result820
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start836 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1545 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1546 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1547 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1548 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1549 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1550 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1551 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1552 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1553 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1554 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1555 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1556 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1557 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1558 = 9
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
    prediction821 = _t1545
    if prediction821 == 13
        _t1560 = parse_uint32_type(parser)
        uint32_type835 = _t1560
        _t1561 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type835))
        _t1559 = _t1561
    else
        if prediction821 == 12
            _t1563 = parse_float32_type(parser)
            float32_type834 = _t1563
            _t1564 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type834))
            _t1562 = _t1564
        else
            if prediction821 == 11
                _t1566 = parse_int32_type(parser)
                int32_type833 = _t1566
                _t1567 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type833))
                _t1565 = _t1567
            else
                if prediction821 == 10
                    _t1569 = parse_boolean_type(parser)
                    boolean_type832 = _t1569
                    _t1570 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type832))
                    _t1568 = _t1570
                else
                    if prediction821 == 9
                        _t1572 = parse_decimal_type(parser)
                        decimal_type831 = _t1572
                        _t1573 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type831))
                        _t1571 = _t1573
                    else
                        if prediction821 == 8
                            _t1575 = parse_missing_type(parser)
                            missing_type830 = _t1575
                            _t1576 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type830))
                            _t1574 = _t1576
                        else
                            if prediction821 == 7
                                _t1578 = parse_datetime_type(parser)
                                datetime_type829 = _t1578
                                _t1579 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type829))
                                _t1577 = _t1579
                            else
                                if prediction821 == 6
                                    _t1581 = parse_date_type(parser)
                                    date_type828 = _t1581
                                    _t1582 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type828))
                                    _t1580 = _t1582
                                else
                                    if prediction821 == 5
                                        _t1584 = parse_int128_type(parser)
                                        int128_type827 = _t1584
                                        _t1585 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type827))
                                        _t1583 = _t1585
                                    else
                                        if prediction821 == 4
                                            _t1587 = parse_uint128_type(parser)
                                            uint128_type826 = _t1587
                                            _t1588 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type826))
                                            _t1586 = _t1588
                                        else
                                            if prediction821 == 3
                                                _t1590 = parse_float_type(parser)
                                                float_type825 = _t1590
                                                _t1591 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type825))
                                                _t1589 = _t1591
                                            else
                                                if prediction821 == 2
                                                    _t1593 = parse_int_type(parser)
                                                    int_type824 = _t1593
                                                    _t1594 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type824))
                                                    _t1592 = _t1594
                                                else
                                                    if prediction821 == 1
                                                        _t1596 = parse_string_type(parser)
                                                        string_type823 = _t1596
                                                        _t1597 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type823))
                                                        _t1595 = _t1597
                                                    else
                                                        if prediction821 == 0
                                                            _t1599 = parse_unspecified_type(parser)
                                                            unspecified_type822 = _t1599
                                                            _t1600 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type822))
                                                            _t1598 = _t1600
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
            _t1562 = _t1565
        end
        _t1559 = _t1562
    end
    result837 = _t1559
    record_span!(parser, span_start836, "Type")
    return result837
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start838 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1601 = Proto.UnspecifiedType()
    result839 = _t1601
    record_span!(parser, span_start838, "UnspecifiedType")
    return result839
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start840 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1602 = Proto.StringType()
    result841 = _t1602
    record_span!(parser, span_start840, "StringType")
    return result841
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start842 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1603 = Proto.IntType()
    result843 = _t1603
    record_span!(parser, span_start842, "IntType")
    return result843
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start844 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1604 = Proto.FloatType()
    result845 = _t1604
    record_span!(parser, span_start844, "FloatType")
    return result845
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start846 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1605 = Proto.UInt128Type()
    result847 = _t1605
    record_span!(parser, span_start846, "UInt128Type")
    return result847
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start848 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1606 = Proto.Int128Type()
    result849 = _t1606
    record_span!(parser, span_start848, "Int128Type")
    return result849
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start850 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1607 = Proto.DateType()
    result851 = _t1607
    record_span!(parser, span_start850, "DateType")
    return result851
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start852 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1608 = Proto.DateTimeType()
    result853 = _t1608
    record_span!(parser, span_start852, "DateTimeType")
    return result853
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start854 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1609 = Proto.MissingType()
    result855 = _t1609
    record_span!(parser, span_start854, "MissingType")
    return result855
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start858 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int856 = consume_terminal!(parser, "INT")
    int_3857 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1610 = Proto.DecimalType(precision=Int32(int856), scale=Int32(int_3857))
    result859 = _t1610
    record_span!(parser, span_start858, "DecimalType")
    return result859
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start860 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1611 = Proto.BooleanType()
    result861 = _t1611
    record_span!(parser, span_start860, "BooleanType")
    return result861
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start862 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1612 = Proto.Int32Type()
    result863 = _t1612
    record_span!(parser, span_start862, "Int32Type")
    return result863
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start864 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1613 = Proto.Float32Type()
    result865 = _t1613
    record_span!(parser, span_start864, "Float32Type")
    return result865
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start866 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1614 = Proto.UInt32Type()
    result867 = _t1614
    record_span!(parser, span_start866, "UInt32Type")
    return result867
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs868 = Proto.Binding[]
    cond869 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond869
        _t1615 = parse_binding(parser)
        item870 = _t1615
        push!(xs868, item870)
        cond869 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings871 = xs868
    return bindings871
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start886 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1617 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1618 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1619 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1620 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1621 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1622 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1623 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1624 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1625 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1626 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1627 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1628 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1629 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1630 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1631 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1632 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1633 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1634 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1635 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1636 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1637 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1638 = 10
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
    else
        _t1616 = -1
    end
    prediction872 = _t1616
    if prediction872 == 12
        _t1640 = parse_cast(parser)
        cast885 = _t1640
        _t1641 = Proto.Formula(formula_type=OneOf(:cast, cast885))
        _t1639 = _t1641
    else
        if prediction872 == 11
            _t1643 = parse_rel_atom(parser)
            rel_atom884 = _t1643
            _t1644 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom884))
            _t1642 = _t1644
        else
            if prediction872 == 10
                _t1646 = parse_primitive(parser)
                primitive883 = _t1646
                _t1647 = Proto.Formula(formula_type=OneOf(:primitive, primitive883))
                _t1645 = _t1647
            else
                if prediction872 == 9
                    _t1649 = parse_pragma(parser)
                    pragma882 = _t1649
                    _t1650 = Proto.Formula(formula_type=OneOf(:pragma, pragma882))
                    _t1648 = _t1650
                else
                    if prediction872 == 8
                        _t1652 = parse_atom(parser)
                        atom881 = _t1652
                        _t1653 = Proto.Formula(formula_type=OneOf(:atom, atom881))
                        _t1651 = _t1653
                    else
                        if prediction872 == 7
                            _t1655 = parse_ffi(parser)
                            ffi880 = _t1655
                            _t1656 = Proto.Formula(formula_type=OneOf(:ffi, ffi880))
                            _t1654 = _t1656
                        else
                            if prediction872 == 6
                                _t1658 = parse_not(parser)
                                not879 = _t1658
                                _t1659 = Proto.Formula(formula_type=OneOf(:not, not879))
                                _t1657 = _t1659
                            else
                                if prediction872 == 5
                                    _t1661 = parse_disjunction(parser)
                                    disjunction878 = _t1661
                                    _t1662 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction878))
                                    _t1660 = _t1662
                                else
                                    if prediction872 == 4
                                        _t1664 = parse_conjunction(parser)
                                        conjunction877 = _t1664
                                        _t1665 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction877))
                                        _t1663 = _t1665
                                    else
                                        if prediction872 == 3
                                            _t1667 = parse_reduce(parser)
                                            reduce876 = _t1667
                                            _t1668 = Proto.Formula(formula_type=OneOf(:reduce, reduce876))
                                            _t1666 = _t1668
                                        else
                                            if prediction872 == 2
                                                _t1670 = parse_exists(parser)
                                                exists875 = _t1670
                                                _t1671 = Proto.Formula(formula_type=OneOf(:exists, exists875))
                                                _t1669 = _t1671
                                            else
                                                if prediction872 == 1
                                                    _t1673 = parse_false(parser)
                                                    false874 = _t1673
                                                    _t1674 = Proto.Formula(formula_type=OneOf(:disjunction, false874))
                                                    _t1672 = _t1674
                                                else
                                                    if prediction872 == 0
                                                        _t1676 = parse_true(parser)
                                                        true873 = _t1676
                                                        _t1677 = Proto.Formula(formula_type=OneOf(:conjunction, true873))
                                                        _t1675 = _t1677
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1672 = _t1675
                                                end
                                                _t1669 = _t1672
                                            end
                                            _t1666 = _t1669
                                        end
                                        _t1663 = _t1666
                                    end
                                    _t1660 = _t1663
                                end
                                _t1657 = _t1660
                            end
                            _t1654 = _t1657
                        end
                        _t1651 = _t1654
                    end
                    _t1648 = _t1651
                end
                _t1645 = _t1648
            end
            _t1642 = _t1645
        end
        _t1639 = _t1642
    end
    result887 = _t1639
    record_span!(parser, span_start886, "Formula")
    return result887
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start888 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1678 = Proto.Conjunction(args=Proto.Formula[])
    result889 = _t1678
    record_span!(parser, span_start888, "Conjunction")
    return result889
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start890 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1679 = Proto.Disjunction(args=Proto.Formula[])
    result891 = _t1679
    record_span!(parser, span_start890, "Disjunction")
    return result891
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start894 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1680 = parse_bindings(parser)
    bindings892 = _t1680
    _t1681 = parse_formula(parser)
    formula893 = _t1681
    consume_literal!(parser, ")")
    _t1682 = Proto.Abstraction(vars=vcat(bindings892[1], !isnothing(bindings892[2]) ? bindings892[2] : []), value=formula893)
    _t1683 = Proto.Exists(body=_t1682)
    result895 = _t1683
    record_span!(parser, span_start894, "Exists")
    return result895
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start899 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1684 = parse_abstraction(parser)
    abstraction896 = _t1684
    _t1685 = parse_abstraction(parser)
    abstraction_3897 = _t1685
    _t1686 = parse_terms(parser)
    terms898 = _t1686
    consume_literal!(parser, ")")
    _t1687 = Proto.Reduce(op=abstraction896, body=abstraction_3897, terms=terms898)
    result900 = _t1687
    record_span!(parser, span_start899, "Reduce")
    return result900
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs901 = Proto.Term[]
    cond902 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond902
        _t1688 = parse_term(parser)
        item903 = _t1688
        push!(xs901, item903)
        cond902 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms904 = xs901
    consume_literal!(parser, ")")
    return terms904
end

function parse_term(parser::ParserState)::Proto.Term
    span_start908 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1689 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1690 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1691 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1692 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1693 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1694 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1695 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1696 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1697 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1698 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1699 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1700 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1701 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1702 = 1
                                                        else
                                                            _t1702 = -1
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
            _t1690 = _t1691
        end
        _t1689 = _t1690
    end
    prediction905 = _t1689
    if prediction905 == 1
        _t1704 = parse_value(parser)
        value907 = _t1704
        _t1705 = Proto.Term(term_type=OneOf(:constant, value907))
        _t1703 = _t1705
    else
        if prediction905 == 0
            _t1707 = parse_var(parser)
            var906 = _t1707
            _t1708 = Proto.Term(term_type=OneOf(:var, var906))
            _t1706 = _t1708
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1703 = _t1706
    end
    result909 = _t1703
    record_span!(parser, span_start908, "Term")
    return result909
end

function parse_var(parser::ParserState)::Proto.Var
    span_start911 = span_start(parser)
    symbol910 = consume_terminal!(parser, "SYMBOL")
    _t1709 = Proto.Var(name=symbol910)
    result912 = _t1709
    record_span!(parser, span_start911, "Var")
    return result912
end

function parse_value(parser::ParserState)::Proto.Value
    span_start926 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1710 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1711 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1712 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1714 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1715 = 0
                        else
                            _t1715 = -1
                        end
                        _t1714 = _t1715
                    end
                    _t1713 = _t1714
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1716 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1717 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1718 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1719 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1720 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1721 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1722 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1723 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1724 = 10
                                                    else
                                                        _t1724 = -1
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
                    _t1713 = _t1716
                end
                _t1712 = _t1713
            end
            _t1711 = _t1712
        end
        _t1710 = _t1711
    end
    prediction913 = _t1710
    if prediction913 == 12
        _t1726 = parse_boolean_value(parser)
        boolean_value925 = _t1726
        _t1727 = Proto.Value(value=OneOf(:boolean_value, boolean_value925))
        _t1725 = _t1727
    else
        if prediction913 == 11
            consume_literal!(parser, "missing")
            _t1729 = Proto.MissingValue()
            _t1730 = Proto.Value(value=OneOf(:missing_value, _t1729))
            _t1728 = _t1730
        else
            if prediction913 == 10
                formatted_decimal924 = consume_terminal!(parser, "DECIMAL")
                _t1732 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal924))
                _t1731 = _t1732
            else
                if prediction913 == 9
                    formatted_int128923 = consume_terminal!(parser, "INT128")
                    _t1734 = Proto.Value(value=OneOf(:int128_value, formatted_int128923))
                    _t1733 = _t1734
                else
                    if prediction913 == 8
                        formatted_uint128922 = consume_terminal!(parser, "UINT128")
                        _t1736 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128922))
                        _t1735 = _t1736
                    else
                        if prediction913 == 7
                            formatted_uint32921 = consume_terminal!(parser, "UINT32")
                            _t1738 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32921))
                            _t1737 = _t1738
                        else
                            if prediction913 == 6
                                formatted_float920 = consume_terminal!(parser, "FLOAT")
                                _t1740 = Proto.Value(value=OneOf(:float_value, formatted_float920))
                                _t1739 = _t1740
                            else
                                if prediction913 == 5
                                    formatted_float32919 = consume_terminal!(parser, "FLOAT32")
                                    _t1742 = Proto.Value(value=OneOf(:float32_value, formatted_float32919))
                                    _t1741 = _t1742
                                else
                                    if prediction913 == 4
                                        formatted_int918 = consume_terminal!(parser, "INT")
                                        _t1744 = Proto.Value(value=OneOf(:int_value, formatted_int918))
                                        _t1743 = _t1744
                                    else
                                        if prediction913 == 3
                                            formatted_int32917 = consume_terminal!(parser, "INT32")
                                            _t1746 = Proto.Value(value=OneOf(:int32_value, formatted_int32917))
                                            _t1745 = _t1746
                                        else
                                            if prediction913 == 2
                                                formatted_string916 = consume_terminal!(parser, "STRING")
                                                _t1748 = Proto.Value(value=OneOf(:string_value, formatted_string916))
                                                _t1747 = _t1748
                                            else
                                                if prediction913 == 1
                                                    _t1750 = parse_datetime(parser)
                                                    datetime915 = _t1750
                                                    _t1751 = Proto.Value(value=OneOf(:datetime_value, datetime915))
                                                    _t1749 = _t1751
                                                else
                                                    if prediction913 == 0
                                                        _t1753 = parse_date(parser)
                                                        date914 = _t1753
                                                        _t1754 = Proto.Value(value=OneOf(:date_value, date914))
                                                        _t1752 = _t1754
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1749 = _t1752
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
                _t1731 = _t1733
            end
            _t1728 = _t1731
        end
        _t1725 = _t1728
    end
    result927 = _t1725
    record_span!(parser, span_start926, "Value")
    return result927
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start931 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int928 = consume_terminal!(parser, "INT")
    formatted_int_3929 = consume_terminal!(parser, "INT")
    formatted_int_4930 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1755 = Proto.DateValue(year=Int32(formatted_int928), month=Int32(formatted_int_3929), day=Int32(formatted_int_4930))
    result932 = _t1755
    record_span!(parser, span_start931, "DateValue")
    return result932
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start940 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int933 = consume_terminal!(parser, "INT")
    formatted_int_3934 = consume_terminal!(parser, "INT")
    formatted_int_4935 = consume_terminal!(parser, "INT")
    formatted_int_5936 = consume_terminal!(parser, "INT")
    formatted_int_6937 = consume_terminal!(parser, "INT")
    formatted_int_7938 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1756 = consume_terminal!(parser, "INT")
    else
        _t1756 = nothing
    end
    formatted_int_8939 = _t1756
    consume_literal!(parser, ")")
    _t1757 = Proto.DateTimeValue(year=Int32(formatted_int933), month=Int32(formatted_int_3934), day=Int32(formatted_int_4935), hour=Int32(formatted_int_5936), minute=Int32(formatted_int_6937), second=Int32(formatted_int_7938), microsecond=Int32((!isnothing(formatted_int_8939) ? formatted_int_8939 : 0)))
    result941 = _t1757
    record_span!(parser, span_start940, "DateTimeValue")
    return result941
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start946 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs942 = Proto.Formula[]
    cond943 = match_lookahead_literal(parser, "(", 0)
    while cond943
        _t1758 = parse_formula(parser)
        item944 = _t1758
        push!(xs942, item944)
        cond943 = match_lookahead_literal(parser, "(", 0)
    end
    formulas945 = xs942
    consume_literal!(parser, ")")
    _t1759 = Proto.Conjunction(args=formulas945)
    result947 = _t1759
    record_span!(parser, span_start946, "Conjunction")
    return result947
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs948 = Proto.Formula[]
    cond949 = match_lookahead_literal(parser, "(", 0)
    while cond949
        _t1760 = parse_formula(parser)
        item950 = _t1760
        push!(xs948, item950)
        cond949 = match_lookahead_literal(parser, "(", 0)
    end
    formulas951 = xs948
    consume_literal!(parser, ")")
    _t1761 = Proto.Disjunction(args=formulas951)
    result953 = _t1761
    record_span!(parser, span_start952, "Disjunction")
    return result953
end

function parse_not(parser::ParserState)::Proto.Not
    span_start955 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1762 = parse_formula(parser)
    formula954 = _t1762
    consume_literal!(parser, ")")
    _t1763 = Proto.Not(arg=formula954)
    result956 = _t1763
    record_span!(parser, span_start955, "Not")
    return result956
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1764 = parse_name(parser)
    name957 = _t1764
    _t1765 = parse_ffi_args(parser)
    ffi_args958 = _t1765
    _t1766 = parse_terms(parser)
    terms959 = _t1766
    consume_literal!(parser, ")")
    _t1767 = Proto.FFI(name=name957, args=ffi_args958, terms=terms959)
    result961 = _t1767
    record_span!(parser, span_start960, "FFI")
    return result961
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol962 = consume_terminal!(parser, "SYMBOL")
    return symbol962
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs963 = Proto.Abstraction[]
    cond964 = match_lookahead_literal(parser, "(", 0)
    while cond964
        _t1768 = parse_abstraction(parser)
        item965 = _t1768
        push!(xs963, item965)
        cond964 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions966 = xs963
    consume_literal!(parser, ")")
    return abstractions966
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start972 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1769 = parse_relation_id(parser)
    relation_id967 = _t1769
    xs968 = Proto.Term[]
    cond969 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond969
        _t1770 = parse_term(parser)
        item970 = _t1770
        push!(xs968, item970)
        cond969 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms971 = xs968
    consume_literal!(parser, ")")
    _t1771 = Proto.Atom(name=relation_id967, terms=terms971)
    result973 = _t1771
    record_span!(parser, span_start972, "Atom")
    return result973
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start979 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1772 = parse_name(parser)
    name974 = _t1772
    xs975 = Proto.Term[]
    cond976 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond976
        _t1773 = parse_term(parser)
        item977 = _t1773
        push!(xs975, item977)
        cond976 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms978 = xs975
    consume_literal!(parser, ")")
    _t1774 = Proto.Pragma(name=name974, terms=terms978)
    result980 = _t1774
    record_span!(parser, span_start979, "Pragma")
    return result980
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start996 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1776 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1777 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1778 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1779 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1780 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1781 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1782 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1783 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1784 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1785 = 7
                                            else
                                                _t1785 = -1
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
            end
            _t1776 = _t1777
        end
        _t1775 = _t1776
    else
        _t1775 = -1
    end
    prediction981 = _t1775
    if prediction981 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1787 = parse_name(parser)
        name991 = _t1787
        xs992 = Proto.RelTerm[]
        cond993 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond993
            _t1788 = parse_rel_term(parser)
            item994 = _t1788
            push!(xs992, item994)
            cond993 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms995 = xs992
        consume_literal!(parser, ")")
        _t1789 = Proto.Primitive(name=name991, terms=rel_terms995)
        _t1786 = _t1789
    else
        if prediction981 == 8
            _t1791 = parse_divide(parser)
            divide990 = _t1791
            _t1790 = divide990
        else
            if prediction981 == 7
                _t1793 = parse_multiply(parser)
                multiply989 = _t1793
                _t1792 = multiply989
            else
                if prediction981 == 6
                    _t1795 = parse_minus(parser)
                    minus988 = _t1795
                    _t1794 = minus988
                else
                    if prediction981 == 5
                        _t1797 = parse_add(parser)
                        add987 = _t1797
                        _t1796 = add987
                    else
                        if prediction981 == 4
                            _t1799 = parse_gt_eq(parser)
                            gt_eq986 = _t1799
                            _t1798 = gt_eq986
                        else
                            if prediction981 == 3
                                _t1801 = parse_gt(parser)
                                gt985 = _t1801
                                _t1800 = gt985
                            else
                                if prediction981 == 2
                                    _t1803 = parse_lt_eq(parser)
                                    lt_eq984 = _t1803
                                    _t1802 = lt_eq984
                                else
                                    if prediction981 == 1
                                        _t1805 = parse_lt(parser)
                                        lt983 = _t1805
                                        _t1804 = lt983
                                    else
                                        if prediction981 == 0
                                            _t1807 = parse_eq(parser)
                                            eq982 = _t1807
                                            _t1806 = eq982
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
            _t1790 = _t1792
        end
        _t1786 = _t1790
    end
    result997 = _t1786
    record_span!(parser, span_start996, "Primitive")
    return result997
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start1000 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1808 = parse_term(parser)
    term998 = _t1808
    _t1809 = parse_term(parser)
    term_3999 = _t1809
    consume_literal!(parser, ")")
    _t1810 = Proto.RelTerm(rel_term_type=OneOf(:term, term998))
    _t1811 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3999))
    _t1812 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1810, _t1811])
    result1001 = _t1812
    record_span!(parser, span_start1000, "Primitive")
    return result1001
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start1004 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1813 = parse_term(parser)
    term1002 = _t1813
    _t1814 = parse_term(parser)
    term_31003 = _t1814
    consume_literal!(parser, ")")
    _t1815 = Proto.RelTerm(rel_term_type=OneOf(:term, term1002))
    _t1816 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31003))
    _t1817 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1815, _t1816])
    result1005 = _t1817
    record_span!(parser, span_start1004, "Primitive")
    return result1005
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start1008 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1818 = parse_term(parser)
    term1006 = _t1818
    _t1819 = parse_term(parser)
    term_31007 = _t1819
    consume_literal!(parser, ")")
    _t1820 = Proto.RelTerm(rel_term_type=OneOf(:term, term1006))
    _t1821 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31007))
    _t1822 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1820, _t1821])
    result1009 = _t1822
    record_span!(parser, span_start1008, "Primitive")
    return result1009
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start1012 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1823 = parse_term(parser)
    term1010 = _t1823
    _t1824 = parse_term(parser)
    term_31011 = _t1824
    consume_literal!(parser, ")")
    _t1825 = Proto.RelTerm(rel_term_type=OneOf(:term, term1010))
    _t1826 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31011))
    _t1827 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1825, _t1826])
    result1013 = _t1827
    record_span!(parser, span_start1012, "Primitive")
    return result1013
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start1016 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1828 = parse_term(parser)
    term1014 = _t1828
    _t1829 = parse_term(parser)
    term_31015 = _t1829
    consume_literal!(parser, ")")
    _t1830 = Proto.RelTerm(rel_term_type=OneOf(:term, term1014))
    _t1831 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31015))
    _t1832 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1830, _t1831])
    result1017 = _t1832
    record_span!(parser, span_start1016, "Primitive")
    return result1017
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start1021 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1833 = parse_term(parser)
    term1018 = _t1833
    _t1834 = parse_term(parser)
    term_31019 = _t1834
    _t1835 = parse_term(parser)
    term_41020 = _t1835
    consume_literal!(parser, ")")
    _t1836 = Proto.RelTerm(rel_term_type=OneOf(:term, term1018))
    _t1837 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31019))
    _t1838 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41020))
    _t1839 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1836, _t1837, _t1838])
    result1022 = _t1839
    record_span!(parser, span_start1021, "Primitive")
    return result1022
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start1026 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1840 = parse_term(parser)
    term1023 = _t1840
    _t1841 = parse_term(parser)
    term_31024 = _t1841
    _t1842 = parse_term(parser)
    term_41025 = _t1842
    consume_literal!(parser, ")")
    _t1843 = Proto.RelTerm(rel_term_type=OneOf(:term, term1023))
    _t1844 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31024))
    _t1845 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41025))
    _t1846 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1843, _t1844, _t1845])
    result1027 = _t1846
    record_span!(parser, span_start1026, "Primitive")
    return result1027
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1031 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1847 = parse_term(parser)
    term1028 = _t1847
    _t1848 = parse_term(parser)
    term_31029 = _t1848
    _t1849 = parse_term(parser)
    term_41030 = _t1849
    consume_literal!(parser, ")")
    _t1850 = Proto.RelTerm(rel_term_type=OneOf(:term, term1028))
    _t1851 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31029))
    _t1852 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41030))
    _t1853 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1850, _t1851, _t1852])
    result1032 = _t1853
    record_span!(parser, span_start1031, "Primitive")
    return result1032
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1036 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1854 = parse_term(parser)
    term1033 = _t1854
    _t1855 = parse_term(parser)
    term_31034 = _t1855
    _t1856 = parse_term(parser)
    term_41035 = _t1856
    consume_literal!(parser, ")")
    _t1857 = Proto.RelTerm(rel_term_type=OneOf(:term, term1033))
    _t1858 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31034))
    _t1859 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41035))
    _t1860 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1857, _t1858, _t1859])
    result1037 = _t1860
    record_span!(parser, span_start1036, "Primitive")
    return result1037
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1041 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1861 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1862 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1863 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1864 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1865 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1866 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1867 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1868 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1869 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1870 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1871 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1872 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1873 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1874 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1875 = 1
                                                            else
                                                                _t1875 = -1
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
            _t1862 = _t1863
        end
        _t1861 = _t1862
    end
    prediction1038 = _t1861
    if prediction1038 == 1
        _t1877 = parse_term(parser)
        term1040 = _t1877
        _t1878 = Proto.RelTerm(rel_term_type=OneOf(:term, term1040))
        _t1876 = _t1878
    else
        if prediction1038 == 0
            _t1880 = parse_specialized_value(parser)
            specialized_value1039 = _t1880
            _t1881 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1039))
            _t1879 = _t1881
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1876 = _t1879
    end
    result1042 = _t1876
    record_span!(parser, span_start1041, "RelTerm")
    return result1042
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1044 = span_start(parser)
    consume_literal!(parser, "#")
    _t1882 = parse_raw_value(parser)
    raw_value1043 = _t1882
    result1045 = raw_value1043
    record_span!(parser, span_start1044, "Value")
    return result1045
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1051 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1883 = parse_name(parser)
    name1046 = _t1883
    xs1047 = Proto.RelTerm[]
    cond1048 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1048
        _t1884 = parse_rel_term(parser)
        item1049 = _t1884
        push!(xs1047, item1049)
        cond1048 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1050 = xs1047
    consume_literal!(parser, ")")
    _t1885 = Proto.RelAtom(name=name1046, terms=rel_terms1050)
    result1052 = _t1885
    record_span!(parser, span_start1051, "RelAtom")
    return result1052
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1055 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1886 = parse_term(parser)
    term1053 = _t1886
    _t1887 = parse_term(parser)
    term_31054 = _t1887
    consume_literal!(parser, ")")
    _t1888 = Proto.Cast(input=term1053, result=term_31054)
    result1056 = _t1888
    record_span!(parser, span_start1055, "Cast")
    return result1056
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1057 = Proto.Attribute[]
    cond1058 = match_lookahead_literal(parser, "(", 0)
    while cond1058
        _t1889 = parse_attribute(parser)
        item1059 = _t1889
        push!(xs1057, item1059)
        cond1058 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1060 = xs1057
    consume_literal!(parser, ")")
    return attributes1060
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1066 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1890 = parse_name(parser)
    name1061 = _t1890
    xs1062 = Proto.Value[]
    cond1063 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1063
        _t1891 = parse_raw_value(parser)
        item1064 = _t1891
        push!(xs1062, item1064)
        cond1063 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1065 = xs1062
    consume_literal!(parser, ")")
    _t1892 = Proto.Attribute(name=name1061, args=raw_values1065)
    result1067 = _t1892
    record_span!(parser, span_start1066, "Attribute")
    return result1067
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1074 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1068 = Proto.RelationId[]
    cond1069 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1069
        _t1893 = parse_relation_id(parser)
        item1070 = _t1893
        push!(xs1068, item1070)
        cond1069 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1071 = xs1068
    _t1894 = parse_script(parser)
    script1072 = _t1894
    if match_lookahead_literal(parser, "(", 0)
        _t1896 = parse_attrs(parser)
        _t1895 = _t1896
    else
        _t1895 = nothing
    end
    attrs1073 = _t1895
    consume_literal!(parser, ")")
    _t1897 = Proto.Algorithm(var"#global"=relation_ids1071, body=script1072, attrs=(!isnothing(attrs1073) ? attrs1073 : Proto.Attribute[]))
    result1075 = _t1897
    record_span!(parser, span_start1074, "Algorithm")
    return result1075
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1080 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1076 = Proto.Construct[]
    cond1077 = match_lookahead_literal(parser, "(", 0)
    while cond1077
        _t1898 = parse_construct(parser)
        item1078 = _t1898
        push!(xs1076, item1078)
        cond1077 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1079 = xs1076
    consume_literal!(parser, ")")
    _t1899 = Proto.Script(constructs=constructs1079)
    result1081 = _t1899
    record_span!(parser, span_start1080, "Script")
    return result1081
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1085 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1901 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1902 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1903 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1904 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1905 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1906 = 1
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
            end
            _t1901 = _t1902
        end
        _t1900 = _t1901
    else
        _t1900 = -1
    end
    prediction1082 = _t1900
    if prediction1082 == 1
        _t1908 = parse_instruction(parser)
        instruction1084 = _t1908
        _t1909 = Proto.Construct(construct_type=OneOf(:instruction, instruction1084))
        _t1907 = _t1909
    else
        if prediction1082 == 0
            _t1911 = parse_loop(parser)
            loop1083 = _t1911
            _t1912 = Proto.Construct(construct_type=OneOf(:loop, loop1083))
            _t1910 = _t1912
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1907 = _t1910
    end
    result1086 = _t1907
    record_span!(parser, span_start1085, "Construct")
    return result1086
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1090 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1913 = parse_init(parser)
    init1087 = _t1913
    _t1914 = parse_script(parser)
    script1088 = _t1914
    if match_lookahead_literal(parser, "(", 0)
        _t1916 = parse_attrs(parser)
        _t1915 = _t1916
    else
        _t1915 = nothing
    end
    attrs1089 = _t1915
    consume_literal!(parser, ")")
    _t1917 = Proto.Loop(init=init1087, body=script1088, attrs=(!isnothing(attrs1089) ? attrs1089 : Proto.Attribute[]))
    result1091 = _t1917
    record_span!(parser, span_start1090, "Loop")
    return result1091
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1092 = Proto.Instruction[]
    cond1093 = match_lookahead_literal(parser, "(", 0)
    while cond1093
        _t1918 = parse_instruction(parser)
        item1094 = _t1918
        push!(xs1092, item1094)
        cond1093 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1095 = xs1092
    consume_literal!(parser, ")")
    return instructions1095
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1102 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1920 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1921 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1922 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1923 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1924 = 0
                        else
                            _t1924 = -1
                        end
                        _t1923 = _t1924
                    end
                    _t1922 = _t1923
                end
                _t1921 = _t1922
            end
            _t1920 = _t1921
        end
        _t1919 = _t1920
    else
        _t1919 = -1
    end
    prediction1096 = _t1919
    if prediction1096 == 4
        _t1926 = parse_monus_def(parser)
        monus_def1101 = _t1926
        _t1927 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1101))
        _t1925 = _t1927
    else
        if prediction1096 == 3
            _t1929 = parse_monoid_def(parser)
            monoid_def1100 = _t1929
            _t1930 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1100))
            _t1928 = _t1930
        else
            if prediction1096 == 2
                _t1932 = parse_break(parser)
                break1099 = _t1932
                _t1933 = Proto.Instruction(instr_type=OneOf(:var"#break", break1099))
                _t1931 = _t1933
            else
                if prediction1096 == 1
                    _t1935 = parse_upsert(parser)
                    upsert1098 = _t1935
                    _t1936 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1098))
                    _t1934 = _t1936
                else
                    if prediction1096 == 0
                        _t1938 = parse_assign(parser)
                        assign1097 = _t1938
                        _t1939 = Proto.Instruction(instr_type=OneOf(:assign, assign1097))
                        _t1937 = _t1939
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1934 = _t1937
                end
                _t1931 = _t1934
            end
            _t1928 = _t1931
        end
        _t1925 = _t1928
    end
    result1103 = _t1925
    record_span!(parser, span_start1102, "Instruction")
    return result1103
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1107 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1940 = parse_relation_id(parser)
    relation_id1104 = _t1940
    _t1941 = parse_abstraction(parser)
    abstraction1105 = _t1941
    if match_lookahead_literal(parser, "(", 0)
        _t1943 = parse_attrs(parser)
        _t1942 = _t1943
    else
        _t1942 = nothing
    end
    attrs1106 = _t1942
    consume_literal!(parser, ")")
    _t1944 = Proto.Assign(name=relation_id1104, body=abstraction1105, attrs=(!isnothing(attrs1106) ? attrs1106 : Proto.Attribute[]))
    result1108 = _t1944
    record_span!(parser, span_start1107, "Assign")
    return result1108
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1112 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1945 = parse_relation_id(parser)
    relation_id1109 = _t1945
    _t1946 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1110 = _t1946
    if match_lookahead_literal(parser, "(", 0)
        _t1948 = parse_attrs(parser)
        _t1947 = _t1948
    else
        _t1947 = nothing
    end
    attrs1111 = _t1947
    consume_literal!(parser, ")")
    _t1949 = Proto.Upsert(name=relation_id1109, body=abstraction_with_arity1110[1], attrs=(!isnothing(attrs1111) ? attrs1111 : Proto.Attribute[]), value_arity=abstraction_with_arity1110[2])
    result1113 = _t1949
    record_span!(parser, span_start1112, "Upsert")
    return result1113
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1950 = parse_bindings(parser)
    bindings1114 = _t1950
    _t1951 = parse_formula(parser)
    formula1115 = _t1951
    consume_literal!(parser, ")")
    _t1952 = Proto.Abstraction(vars=vcat(bindings1114[1], !isnothing(bindings1114[2]) ? bindings1114[2] : []), value=formula1115)
    return (_t1952, length(bindings1114[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1119 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1953 = parse_relation_id(parser)
    relation_id1116 = _t1953
    _t1954 = parse_abstraction(parser)
    abstraction1117 = _t1954
    if match_lookahead_literal(parser, "(", 0)
        _t1956 = parse_attrs(parser)
        _t1955 = _t1956
    else
        _t1955 = nothing
    end
    attrs1118 = _t1955
    consume_literal!(parser, ")")
    _t1957 = Proto.Break(name=relation_id1116, body=abstraction1117, attrs=(!isnothing(attrs1118) ? attrs1118 : Proto.Attribute[]))
    result1120 = _t1957
    record_span!(parser, span_start1119, "Break")
    return result1120
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1125 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1958 = parse_monoid(parser)
    monoid1121 = _t1958
    _t1959 = parse_relation_id(parser)
    relation_id1122 = _t1959
    _t1960 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1123 = _t1960
    if match_lookahead_literal(parser, "(", 0)
        _t1962 = parse_attrs(parser)
        _t1961 = _t1962
    else
        _t1961 = nothing
    end
    attrs1124 = _t1961
    consume_literal!(parser, ")")
    _t1963 = Proto.MonoidDef(monoid=monoid1121, name=relation_id1122, body=abstraction_with_arity1123[1], attrs=(!isnothing(attrs1124) ? attrs1124 : Proto.Attribute[]), value_arity=abstraction_with_arity1123[2])
    result1126 = _t1963
    record_span!(parser, span_start1125, "MonoidDef")
    return result1126
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1132 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1965 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1966 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1967 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1968 = 2
                    else
                        _t1968 = -1
                    end
                    _t1967 = _t1968
                end
                _t1966 = _t1967
            end
            _t1965 = _t1966
        end
        _t1964 = _t1965
    else
        _t1964 = -1
    end
    prediction1127 = _t1964
    if prediction1127 == 3
        _t1970 = parse_sum_monoid(parser)
        sum_monoid1131 = _t1970
        _t1971 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1131))
        _t1969 = _t1971
    else
        if prediction1127 == 2
            _t1973 = parse_max_monoid(parser)
            max_monoid1130 = _t1973
            _t1974 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1130))
            _t1972 = _t1974
        else
            if prediction1127 == 1
                _t1976 = parse_min_monoid(parser)
                min_monoid1129 = _t1976
                _t1977 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1129))
                _t1975 = _t1977
            else
                if prediction1127 == 0
                    _t1979 = parse_or_monoid(parser)
                    or_monoid1128 = _t1979
                    _t1980 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1128))
                    _t1978 = _t1980
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1975 = _t1978
            end
            _t1972 = _t1975
        end
        _t1969 = _t1972
    end
    result1133 = _t1969
    record_span!(parser, span_start1132, "Monoid")
    return result1133
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1134 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1981 = Proto.OrMonoid()
    result1135 = _t1981
    record_span!(parser, span_start1134, "OrMonoid")
    return result1135
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1137 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1982 = parse_type(parser)
    type1136 = _t1982
    consume_literal!(parser, ")")
    _t1983 = Proto.MinMonoid(var"#type"=type1136)
    result1138 = _t1983
    record_span!(parser, span_start1137, "MinMonoid")
    return result1138
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1140 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1984 = parse_type(parser)
    type1139 = _t1984
    consume_literal!(parser, ")")
    _t1985 = Proto.MaxMonoid(var"#type"=type1139)
    result1141 = _t1985
    record_span!(parser, span_start1140, "MaxMonoid")
    return result1141
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1143 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1986 = parse_type(parser)
    type1142 = _t1986
    consume_literal!(parser, ")")
    _t1987 = Proto.SumMonoid(var"#type"=type1142)
    result1144 = _t1987
    record_span!(parser, span_start1143, "SumMonoid")
    return result1144
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1149 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1988 = parse_monoid(parser)
    monoid1145 = _t1988
    _t1989 = parse_relation_id(parser)
    relation_id1146 = _t1989
    _t1990 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1147 = _t1990
    if match_lookahead_literal(parser, "(", 0)
        _t1992 = parse_attrs(parser)
        _t1991 = _t1992
    else
        _t1991 = nothing
    end
    attrs1148 = _t1991
    consume_literal!(parser, ")")
    _t1993 = Proto.MonusDef(monoid=monoid1145, name=relation_id1146, body=abstraction_with_arity1147[1], attrs=(!isnothing(attrs1148) ? attrs1148 : Proto.Attribute[]), value_arity=abstraction_with_arity1147[2])
    result1150 = _t1993
    record_span!(parser, span_start1149, "MonusDef")
    return result1150
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1155 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1994 = parse_relation_id(parser)
    relation_id1151 = _t1994
    _t1995 = parse_abstraction(parser)
    abstraction1152 = _t1995
    _t1996 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1153 = _t1996
    _t1997 = parse_functional_dependency_values(parser)
    functional_dependency_values1154 = _t1997
    consume_literal!(parser, ")")
    _t1998 = Proto.FunctionalDependency(guard=abstraction1152, keys=functional_dependency_keys1153, values=functional_dependency_values1154)
    _t1999 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1998), name=relation_id1151)
    result1156 = _t1999
    record_span!(parser, span_start1155, "Constraint")
    return result1156
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1157 = Proto.Var[]
    cond1158 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1158
        _t2000 = parse_var(parser)
        item1159 = _t2000
        push!(xs1157, item1159)
        cond1158 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1160 = xs1157
    consume_literal!(parser, ")")
    return vars1160
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1161 = Proto.Var[]
    cond1162 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1162
        _t2001 = parse_var(parser)
        item1163 = _t2001
        push!(xs1161, item1163)
        cond1162 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1164 = xs1161
    consume_literal!(parser, ")")
    return vars1164
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1170 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t2003 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t2004 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t2005 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t2006 = 1
                    else
                        _t2006 = -1
                    end
                    _t2005 = _t2006
                end
                _t2004 = _t2005
            end
            _t2003 = _t2004
        end
        _t2002 = _t2003
    else
        _t2002 = -1
    end
    prediction1165 = _t2002
    if prediction1165 == 3
        _t2008 = parse_iceberg_data(parser)
        iceberg_data1169 = _t2008
        _t2009 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1169))
        _t2007 = _t2009
    else
        if prediction1165 == 2
            _t2011 = parse_csv_data(parser)
            csv_data1168 = _t2011
            _t2012 = Proto.Data(data_type=OneOf(:csv_data, csv_data1168))
            _t2010 = _t2012
        else
            if prediction1165 == 1
                _t2014 = parse_betree_relation(parser)
                betree_relation1167 = _t2014
                _t2015 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1167))
                _t2013 = _t2015
            else
                if prediction1165 == 0
                    _t2017 = parse_edb(parser)
                    edb1166 = _t2017
                    _t2018 = Proto.Data(data_type=OneOf(:edb, edb1166))
                    _t2016 = _t2018
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t2013 = _t2016
            end
            _t2010 = _t2013
        end
        _t2007 = _t2010
    end
    result1171 = _t2007
    record_span!(parser, span_start1170, "Data")
    return result1171
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1175 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t2019 = parse_relation_id(parser)
    relation_id1172 = _t2019
    _t2020 = parse_edb_path(parser)
    edb_path1173 = _t2020
    _t2021 = parse_edb_types(parser)
    edb_types1174 = _t2021
    consume_literal!(parser, ")")
    _t2022 = Proto.EDB(target_id=relation_id1172, path=edb_path1173, types=edb_types1174)
    result1176 = _t2022
    record_span!(parser, span_start1175, "EDB")
    return result1176
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1177 = String[]
    cond1178 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1178
        item1179 = consume_terminal!(parser, "STRING")
        push!(xs1177, item1179)
        cond1178 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1180 = xs1177
    consume_literal!(parser, "]")
    return strings1180
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1181 = Proto.var"#Type"[]
    cond1182 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1182
        _t2023 = parse_type(parser)
        item1183 = _t2023
        push!(xs1181, item1183)
        cond1182 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1184 = xs1181
    consume_literal!(parser, "]")
    return types1184
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1187 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t2024 = parse_relation_id(parser)
    relation_id1185 = _t2024
    _t2025 = parse_betree_info(parser)
    betree_info1186 = _t2025
    consume_literal!(parser, ")")
    _t2026 = Proto.BeTreeRelation(name=relation_id1185, relation_info=betree_info1186)
    result1188 = _t2026
    record_span!(parser, span_start1187, "BeTreeRelation")
    return result1188
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1192 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t2027 = parse_betree_info_key_types(parser)
    betree_info_key_types1189 = _t2027
    _t2028 = parse_betree_info_value_types(parser)
    betree_info_value_types1190 = _t2028
    _t2029 = parse_config_dict(parser)
    config_dict1191 = _t2029
    consume_literal!(parser, ")")
    _t2030 = construct_betree_info(parser, betree_info_key_types1189, betree_info_value_types1190, config_dict1191)
    result1193 = _t2030
    record_span!(parser, span_start1192, "BeTreeInfo")
    return result1193
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1194 = Proto.var"#Type"[]
    cond1195 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1195
        _t2031 = parse_type(parser)
        item1196 = _t2031
        push!(xs1194, item1196)
        cond1195 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1197 = xs1194
    consume_literal!(parser, ")")
    return types1197
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1198 = Proto.var"#Type"[]
    cond1199 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1199
        _t2032 = parse_type(parser)
        item1200 = _t2032
        push!(xs1198, item1200)
        cond1199 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1201 = xs1198
    consume_literal!(parser, ")")
    return types1201
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1207 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t2033 = parse_csvlocator(parser)
    csvlocator1202 = _t2033
    _t2034 = parse_csv_config(parser)
    csv_config1203 = _t2034
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t2036 = parse_gnf_columns(parser)
        _t2035 = _t2036
    else
        _t2035 = nothing
    end
    gnf_columns1204 = _t2035
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relations", 1))
        _t2038 = parse_target_relations(parser)
        _t2037 = _t2038
    else
        _t2037 = nothing
    end
    target_relations1205 = _t2037
    _t2039 = parse_csv_asof(parser)
    csv_asof1206 = _t2039
    consume_literal!(parser, ")")
    _t2040 = construct_csv_data(parser, csvlocator1202, csv_config1203, gnf_columns1204, target_relations1205, csv_asof1206)
    result1208 = _t2040
    record_span!(parser, span_start1207, "CSVData")
    return result1208
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1211 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t2042 = parse_csv_locator_paths(parser)
        _t2041 = _t2042
    else
        _t2041 = nothing
    end
    csv_locator_paths1209 = _t2041
    if match_lookahead_literal(parser, "(", 0)
        _t2044 = parse_csv_locator_inline_data(parser)
        _t2043 = _t2044
    else
        _t2043 = nothing
    end
    csv_locator_inline_data1210 = _t2043
    consume_literal!(parser, ")")
    _t2045 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1209) ? csv_locator_paths1209 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1210) ? csv_locator_inline_data1210 : "")))
    result1212 = _t2045
    record_span!(parser, span_start1211, "CSVLocator")
    return result1212
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1213 = String[]
    cond1214 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1214
        item1215 = consume_terminal!(parser, "STRING")
        push!(xs1213, item1215)
        cond1214 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1216 = xs1213
    consume_literal!(parser, ")")
    return strings1216
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1217 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1217
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1220 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t2046 = parse_config_dict(parser)
    config_dict1218 = _t2046
    if match_lookahead_literal(parser, "(", 0)
        _t2048 = parse__storage_integration(parser)
        _t2047 = _t2048
    else
        _t2047 = nothing
    end
    _storage_integration1219 = _t2047
    consume_literal!(parser, ")")
    _t2049 = construct_csv_config(parser, config_dict1218, _storage_integration1219)
    result1221 = _t2049
    record_span!(parser, span_start1220, "CSVConfig")
    return result1221
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t2050 = parse_config_dict(parser)
    config_dict1222 = _t2050
    consume_literal!(parser, ")")
    return config_dict1222
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1223 = Proto.GNFColumn[]
    cond1224 = match_lookahead_literal(parser, "(", 0)
    while cond1224
        _t2051 = parse_gnf_column(parser)
        item1225 = _t2051
        push!(xs1223, item1225)
        cond1224 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1226 = xs1223
    consume_literal!(parser, ")")
    return gnf_columns1226
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1233 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t2052 = parse_gnf_column_path(parser)
    gnf_column_path1227 = _t2052
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t2054 = parse_relation_id(parser)
        _t2053 = _t2054
    else
        _t2053 = nothing
    end
    relation_id1228 = _t2053
    consume_literal!(parser, "[")
    xs1229 = Proto.var"#Type"[]
    cond1230 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1230
        _t2055 = parse_type(parser)
        item1231 = _t2055
        push!(xs1229, item1231)
        cond1230 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1232 = xs1229
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2056 = Proto.GNFColumn(column_path=gnf_column_path1227, target_id=relation_id1228, types=types1232)
    result1234 = _t2056
    record_span!(parser, span_start1233, "GNFColumn")
    return result1234
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t2057 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t2058 = 0
        else
            _t2058 = -1
        end
        _t2057 = _t2058
    end
    prediction1235 = _t2057
    if prediction1235 == 1
        consume_literal!(parser, "[")
        xs1237 = String[]
        cond1238 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1238
            item1239 = consume_terminal!(parser, "STRING")
            push!(xs1237, item1239)
            cond1238 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1240 = xs1237
        consume_literal!(parser, "]")
        _t2059 = strings1240
    else
        if prediction1235 == 0
            string1236 = consume_terminal!(parser, "STRING")
            _t2060 = String[string1236]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t2059 = _t2060
    end
    return _t2059
end

function parse_target_relations(parser::ParserState)::Proto.TargetRelations
    span_start1243 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relations")
    _t2061 = parse_relation_keys(parser)
    relation_keys1241 = _t2061
    _t2062 = parse_relation_body(parser)
    relation_body1242 = _t2062
    consume_literal!(parser, ")")
    _t2063 = construct_relations(parser, relation_keys1241, relation_body1242)
    result1244 = _t2063
    record_span!(parser, span_start1243, "TargetRelations")
    return result1244
end

function parse_relation_keys(parser::ParserState)::Vector{Proto.NamedColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1245 = Proto.NamedColumn[]
    cond1246 = match_lookahead_literal(parser, "(", 0)
    while cond1246
        _t2064 = parse_named_column(parser)
        item1247 = _t2064
        push!(xs1245, item1247)
        cond1246 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1248 = xs1245
    consume_literal!(parser, ")")
    return named_columns1248
end

function parse_named_column(parser::ParserState)::Proto.NamedColumn
    span_start1251 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1249 = consume_terminal!(parser, "STRING")
    _t2065 = parse_type(parser)
    type1250 = _t2065
    consume_literal!(parser, ")")
    _t2066 = Proto.NamedColumn(name=string1249, var"#type"=type1250)
    result1252 = _t2066
    record_span!(parser, span_start1251, "NamedColumn")
    return result1252
end

function parse_relation_body(parser::ParserState)::Proto.TargetRelations
    span_start1257 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "relation", 1)
            _t2068 = 0
        else
            if match_lookahead_literal(parser, "inserts", 1)
                _t2069 = 1
            else
                _t2069 = 0
            end
            _t2068 = _t2069
        end
        _t2067 = _t2068
    else
        _t2067 = 0
    end
    prediction1253 = _t2067
    if prediction1253 == 1
        _t2071 = parse_cdc_inserts(parser)
        cdc_inserts1255 = _t2071
        _t2072 = parse_cdc_deletes(parser)
        cdc_deletes1256 = _t2072
        _t2073 = construct_cdc_relations(parser, cdc_inserts1255, cdc_deletes1256)
        _t2070 = _t2073
    else
        if prediction1253 == 0
            _t2075 = parse_non_cdc_relations(parser)
            non_cdc_relations1254 = _t2075
            _t2076 = construct_non_cdc_relations(parser, non_cdc_relations1254)
            _t2074 = _t2076
        else
            throw(ParseError("Unexpected token in relation_body" * ": " * string(lookahead(parser, 0))))
        end
        _t2070 = _t2074
    end
    result1258 = _t2070
    record_span!(parser, span_start1257, "TargetRelations")
    return result1258
end

function parse_non_cdc_relations(parser::ParserState)::Vector{Proto.TargetRelation}
    xs1259 = Proto.TargetRelation[]
    cond1260 = match_lookahead_literal(parser, "(", 0)
    while cond1260
        _t2077 = parse_target_relation(parser)
        item1261 = _t2077
        push!(xs1259, item1261)
        cond1260 = match_lookahead_literal(parser, "(", 0)
    end
    return xs1259
end

function parse_target_relation(parser::ParserState)::Proto.TargetRelation
    span_start1267 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relation")
    _t2078 = parse_relation_id(parser)
    relation_id1262 = _t2078
    xs1263 = Proto.NamedColumn[]
    cond1264 = match_lookahead_literal(parser, "(", 0)
    while cond1264
        _t2079 = parse_named_column(parser)
        item1265 = _t2079
        push!(xs1263, item1265)
        cond1264 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1266 = xs1263
    consume_literal!(parser, ")")
    _t2080 = Proto.TargetRelation(target_id=relation_id1262, values=named_columns1266)
    result1268 = _t2080
    record_span!(parser, span_start1267, "TargetRelation")
    return result1268
end

function parse_cdc_inserts(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "inserts")
    xs1269 = Proto.TargetRelation[]
    cond1270 = match_lookahead_literal(parser, "(", 0)
    while cond1270
        _t2081 = parse_target_relation(parser)
        item1271 = _t2081
        push!(xs1269, item1271)
        cond1270 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1272 = xs1269
    consume_literal!(parser, ")")
    return target_relations1272
end

function parse_cdc_deletes(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "deletes")
    xs1273 = Proto.TargetRelation[]
    cond1274 = match_lookahead_literal(parser, "(", 0)
    while cond1274
        _t2082 = parse_target_relation(parser)
        item1275 = _t2082
        push!(xs1273, item1275)
        cond1274 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1276 = xs1273
    consume_literal!(parser, ")")
    return target_relations1276
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1277 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1277
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1284 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t2083 = parse_iceberg_locator(parser)
    iceberg_locator1278 = _t2083
    _t2084 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1279 = _t2084
    _t2085 = parse_gnf_columns(parser)
    gnf_columns1280 = _t2085
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2087 = parse_iceberg_from_snapshot(parser)
        _t2086 = _t2087
    else
        _t2086 = nothing
    end
    iceberg_from_snapshot1281 = _t2086
    if match_lookahead_literal(parser, "(", 0)
        _t2089 = parse_iceberg_to_snapshot(parser)
        _t2088 = _t2089
    else
        _t2088 = nothing
    end
    iceberg_to_snapshot1282 = _t2088
    _t2090 = parse_boolean_value(parser)
    boolean_value1283 = _t2090
    consume_literal!(parser, ")")
    _t2091 = construct_iceberg_data(parser, iceberg_locator1278, iceberg_catalog_config1279, gnf_columns1280, iceberg_from_snapshot1281, iceberg_to_snapshot1282, boolean_value1283)
    result1285 = _t2091
    record_span!(parser, span_start1284, "IcebergData")
    return result1285
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1289 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2092 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1286 = _t2092
    _t2093 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1287 = _t2093
    _t2094 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1288 = _t2094
    consume_literal!(parser, ")")
    _t2095 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1286, namespace=iceberg_locator_namespace1287, warehouse=iceberg_locator_warehouse1288)
    result1290 = _t2095
    record_span!(parser, span_start1289, "IcebergLocator")
    return result1290
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1291 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1291
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1292 = String[]
    cond1293 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1293
        item1294 = consume_terminal!(parser, "STRING")
        push!(xs1292, item1294)
        cond1293 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1295 = xs1292
    consume_literal!(parser, ")")
    return strings1295
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1296 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1296
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1301 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2096 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1297 = _t2096
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2098 = parse_iceberg_catalog_config_scope(parser)
        _t2097 = _t2098
    else
        _t2097 = nothing
    end
    iceberg_catalog_config_scope1298 = _t2097
    _t2099 = parse_iceberg_properties(parser)
    iceberg_properties1299 = _t2099
    _t2100 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1300 = _t2100
    consume_literal!(parser, ")")
    _t2101 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1297, iceberg_catalog_config_scope1298, iceberg_properties1299, iceberg_auth_properties1300)
    result1302 = _t2101
    record_span!(parser, span_start1301, "IcebergCatalogConfig")
    return result1302
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1303 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1303
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1304 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1304
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1305 = Tuple{String, String}[]
    cond1306 = match_lookahead_literal(parser, "(", 0)
    while cond1306
        _t2102 = parse_iceberg_property_entry(parser)
        item1307 = _t2102
        push!(xs1305, item1307)
        cond1306 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1308 = xs1305
    consume_literal!(parser, ")")
    return iceberg_property_entrys1308
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1309 = consume_terminal!(parser, "STRING")
    string_31310 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1309, string_31310,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1311 = Tuple{String, String}[]
    cond1312 = match_lookahead_literal(parser, "(", 0)
    while cond1312
        _t2103 = parse_iceberg_masked_property_entry(parser)
        item1313 = _t2103
        push!(xs1311, item1313)
        cond1312 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1314 = xs1311
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1314
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1315 = consume_terminal!(parser, "STRING")
    string_31316 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1315, string_31316,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1317 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1317
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1318 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1318
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1320 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2104 = parse_fragment_id(parser)
    fragment_id1319 = _t2104
    consume_literal!(parser, ")")
    _t2105 = Proto.Undefine(fragment_id=fragment_id1319)
    result1321 = _t2105
    record_span!(parser, span_start1320, "Undefine")
    return result1321
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1326 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1322 = Proto.RelationId[]
    cond1323 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1323
        _t2106 = parse_relation_id(parser)
        item1324 = _t2106
        push!(xs1322, item1324)
        cond1323 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1325 = xs1322
    consume_literal!(parser, ")")
    _t2107 = Proto.Context(relations=relation_ids1325)
    result1327 = _t2107
    record_span!(parser, span_start1326, "Context")
    return result1327
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1333 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2108 = parse_edb_path(parser)
    edb_path1328 = _t2108
    xs1329 = Proto.SnapshotMapping[]
    cond1330 = match_lookahead_literal(parser, "[", 0)
    while cond1330
        _t2109 = parse_snapshot_mapping(parser)
        item1331 = _t2109
        push!(xs1329, item1331)
        cond1330 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1332 = xs1329
    consume_literal!(parser, ")")
    _t2110 = Proto.Snapshot(mappings=snapshot_mappings1332, prefix=edb_path1328)
    result1334 = _t2110
    record_span!(parser, span_start1333, "Snapshot")
    return result1334
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1337 = span_start(parser)
    _t2111 = parse_edb_path(parser)
    edb_path1335 = _t2111
    _t2112 = parse_relation_id(parser)
    relation_id1336 = _t2112
    _t2113 = Proto.SnapshotMapping(destination_path=edb_path1335, source_relation=relation_id1336)
    result1338 = _t2113
    record_span!(parser, span_start1337, "SnapshotMapping")
    return result1338
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1339 = Proto.Read[]
    cond1340 = match_lookahead_literal(parser, "(", 0)
    while cond1340
        _t2114 = parse_read(parser)
        item1341 = _t2114
        push!(xs1339, item1341)
        cond1340 = match_lookahead_literal(parser, "(", 0)
    end
    reads1342 = xs1339
    consume_literal!(parser, ")")
    return reads1342
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1349 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2116 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2117 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2118 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2119 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2120 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2121 = 3
                            else
                                _t2121 = -1
                            end
                            _t2120 = _t2121
                        end
                        _t2119 = _t2120
                    end
                    _t2118 = _t2119
                end
                _t2117 = _t2118
            end
            _t2116 = _t2117
        end
        _t2115 = _t2116
    else
        _t2115 = -1
    end
    prediction1343 = _t2115
    if prediction1343 == 4
        _t2123 = parse_export(parser)
        export1348 = _t2123
        _t2124 = Proto.Read(read_type=OneOf(:var"#export", export1348))
        _t2122 = _t2124
    else
        if prediction1343 == 3
            _t2126 = parse_abort(parser)
            abort1347 = _t2126
            _t2127 = Proto.Read(read_type=OneOf(:abort, abort1347))
            _t2125 = _t2127
        else
            if prediction1343 == 2
                _t2129 = parse_what_if(parser)
                what_if1346 = _t2129
                _t2130 = Proto.Read(read_type=OneOf(:what_if, what_if1346))
                _t2128 = _t2130
            else
                if prediction1343 == 1
                    _t2132 = parse_output(parser)
                    output1345 = _t2132
                    _t2133 = Proto.Read(read_type=OneOf(:output, output1345))
                    _t2131 = _t2133
                else
                    if prediction1343 == 0
                        _t2135 = parse_demand(parser)
                        demand1344 = _t2135
                        _t2136 = Proto.Read(read_type=OneOf(:demand, demand1344))
                        _t2134 = _t2136
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2131 = _t2134
                end
                _t2128 = _t2131
            end
            _t2125 = _t2128
        end
        _t2122 = _t2125
    end
    result1350 = _t2122
    record_span!(parser, span_start1349, "Read")
    return result1350
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1352 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2137 = parse_relation_id(parser)
    relation_id1351 = _t2137
    consume_literal!(parser, ")")
    _t2138 = Proto.Demand(relation_id=relation_id1351)
    result1353 = _t2138
    record_span!(parser, span_start1352, "Demand")
    return result1353
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1356 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2139 = parse_name(parser)
    name1354 = _t2139
    _t2140 = parse_relation_id(parser)
    relation_id1355 = _t2140
    consume_literal!(parser, ")")
    _t2141 = Proto.Output(name=name1354, relation_id=relation_id1355)
    result1357 = _t2141
    record_span!(parser, span_start1356, "Output")
    return result1357
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1360 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2142 = parse_name(parser)
    name1358 = _t2142
    _t2143 = parse_epoch(parser)
    epoch1359 = _t2143
    consume_literal!(parser, ")")
    _t2144 = Proto.WhatIf(branch=name1358, epoch=epoch1359)
    result1361 = _t2144
    record_span!(parser, span_start1360, "WhatIf")
    return result1361
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1364 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2146 = parse_name(parser)
        _t2145 = _t2146
    else
        _t2145 = nothing
    end
    name1362 = _t2145
    _t2147 = parse_relation_id(parser)
    relation_id1363 = _t2147
    consume_literal!(parser, ")")
    _t2148 = Proto.Abort(name=(!isnothing(name1362) ? name1362 : "abort"), relation_id=relation_id1363)
    result1365 = _t2148
    record_span!(parser, span_start1364, "Abort")
    return result1365
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1369 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2150 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2151 = 0
            else
                _t2151 = -1
            end
            _t2150 = _t2151
        end
        _t2149 = _t2150
    else
        _t2149 = -1
    end
    prediction1366 = _t2149
    if prediction1366 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2153 = parse_export_iceberg_config(parser)
        export_iceberg_config1368 = _t2153
        consume_literal!(parser, ")")
        _t2154 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1368))
        _t2152 = _t2154
    else
        if prediction1366 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2156 = parse_export_csv_config(parser)
            export_csv_config1367 = _t2156
            consume_literal!(parser, ")")
            _t2157 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1367))
            _t2155 = _t2157
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2152 = _t2155
    end
    result1370 = _t2152
    record_span!(parser, span_start1369, "Export")
    return result1370
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1378 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2159 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2160 = 1
            else
                _t2160 = -1
            end
            _t2159 = _t2160
        end
        _t2158 = _t2159
    else
        _t2158 = -1
    end
    prediction1371 = _t2158
    if prediction1371 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2162 = parse_export_csv_path(parser)
        export_csv_path1375 = _t2162
        _t2163 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1376 = _t2163
        _t2164 = parse_config_dict(parser)
        config_dict1377 = _t2164
        consume_literal!(parser, ")")
        _t2165 = construct_export_csv_config(parser, export_csv_path1375, export_csv_columns_list1376, config_dict1377)
        _t2161 = _t2165
    else
        if prediction1371 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2167 = parse_export_csv_output_location(parser)
            export_csv_output_location1372 = _t2167
            _t2168 = parse_export_csv_source(parser)
            export_csv_source1373 = _t2168
            _t2169 = parse_csv_config(parser)
            csv_config1374 = _t2169
            consume_literal!(parser, ")")
            _t2170 = construct_export_csv_config_with_location(parser, export_csv_output_location1372, export_csv_source1373, csv_config1374)
            _t2166 = _t2170
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2161 = _t2166
    end
    result1379 = _t2161
    record_span!(parser, span_start1378, "ExportCSVConfig")
    return result1379
end

function parse_export_csv_output_location(parser::ParserState)::Tuple{String, String}
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "transaction_output_name", 1)
            _t2172 = 1
        else
            if match_lookahead_literal(parser, "path", 1)
                _t2173 = 0
            else
                _t2173 = -1
            end
            _t2172 = _t2173
        end
        _t2171 = _t2172
    else
        _t2171 = -1
    end
    prediction1380 = _t2171
    if prediction1380 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "transaction_output_name")
        _t2175 = parse_name(parser)
        name1382 = _t2175
        consume_literal!(parser, ")")
        _t2174 = ("", name1382,)
    else
        if prediction1380 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "path")
            string1381 = consume_terminal!(parser, "STRING")
            consume_literal!(parser, ")")
            _t2176 = (string1381, "",)
        else
            throw(ParseError("Unexpected token in export_csv_output_location" * ": " * string(lookahead(parser, 0))))
        end
        _t2174 = _t2176
    end
    return _t2174
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1389 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2178 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2179 = 0
            else
                _t2179 = -1
            end
            _t2178 = _t2179
        end
        _t2177 = _t2178
    else
        _t2177 = -1
    end
    prediction1383 = _t2177
    if prediction1383 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2181 = parse_relation_id(parser)
        relation_id1388 = _t2181
        consume_literal!(parser, ")")
        _t2182 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1388))
        _t2180 = _t2182
    else
        if prediction1383 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1384 = Proto.ExportCSVColumn[]
            cond1385 = match_lookahead_literal(parser, "(", 0)
            while cond1385
                _t2184 = parse_export_csv_column(parser)
                item1386 = _t2184
                push!(xs1384, item1386)
                cond1385 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1387 = xs1384
            consume_literal!(parser, ")")
            _t2185 = Proto.ExportCSVColumns(columns=export_csv_columns1387)
            _t2186 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2185))
            _t2183 = _t2186
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2180 = _t2183
    end
    result1390 = _t2180
    record_span!(parser, span_start1389, "ExportCSVSource")
    return result1390
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1393 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1391 = consume_terminal!(parser, "STRING")
    _t2187 = parse_relation_id(parser)
    relation_id1392 = _t2187
    consume_literal!(parser, ")")
    _t2188 = Proto.ExportCSVColumn(column_name=string1391, column_data=relation_id1392)
    result1394 = _t2188
    record_span!(parser, span_start1393, "ExportCSVColumn")
    return result1394
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1395 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1395
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1396 = Proto.ExportCSVColumn[]
    cond1397 = match_lookahead_literal(parser, "(", 0)
    while cond1397
        _t2189 = parse_export_csv_column(parser)
        item1398 = _t2189
        push!(xs1396, item1398)
        cond1397 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1399 = xs1396
    consume_literal!(parser, ")")
    return export_csv_columns1399
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1405 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2190 = parse_iceberg_locator(parser)
    iceberg_locator1400 = _t2190
    _t2191 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1401 = _t2191
    _t2192 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1402 = _t2192
    _t2193 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1403 = _t2193
    if match_lookahead_literal(parser, "{", 0)
        _t2195 = parse_config_dict(parser)
        _t2194 = _t2195
    else
        _t2194 = nothing
    end
    config_dict1404 = _t2194
    consume_literal!(parser, ")")
    _t2196 = construct_export_iceberg_config_full(parser, iceberg_locator1400, iceberg_catalog_config1401, export_iceberg_table_def1402, iceberg_table_properties1403, config_dict1404)
    result1406 = _t2196
    record_span!(parser, span_start1405, "ExportIcebergConfig")
    return result1406
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1408 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2197 = parse_relation_id(parser)
    relation_id1407 = _t2197
    consume_literal!(parser, ")")
    result1409 = relation_id1407
    record_span!(parser, span_start1408, "RelationId")
    return result1409
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1410 = Tuple{String, String}[]
    cond1411 = match_lookahead_literal(parser, "(", 0)
    while cond1411
        _t2198 = parse_iceberg_property_entry(parser)
        item1412 = _t2198
        push!(xs1410, item1412)
        cond1411 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1413 = xs1410
    consume_literal!(parser, ")")
    return iceberg_property_entrys1413
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
