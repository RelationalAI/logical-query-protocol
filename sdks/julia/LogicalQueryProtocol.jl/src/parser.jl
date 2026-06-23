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
        _t2187 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2188 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2189 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2190 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2191 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2192 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2193 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2194 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2195 = nothing
    end
    return nothing
end

function construct_non_cdc_relations(parser::ParserState, targets::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2196 = Proto.PlainTargets(targets=targets)
    _t2197 = Proto.TargetRelations(body=OneOf(:plain, _t2196), keys=Proto.NamedColumn[])
    return _t2197
end

function construct_cdc_relations(parser::ParserState, inserts::Vector{Proto.TargetRelation}, deletes::Vector{Proto.TargetRelation})::Proto.TargetRelations
    _t2198 = Proto.CDCTargets(inserts=inserts, deletes=deletes)
    _t2199 = Proto.TargetRelations(body=OneOf(:cdc, _t2198), keys=Proto.NamedColumn[])
    return _t2199
end

function construct_relations(parser::ParserState, keys::Vector{Proto.NamedColumn}, body::Proto.TargetRelations)::Proto.TargetRelations
    if _has_proto_field(body, Symbol("plain"))
        _t2201 = Proto.TargetRelations(body=OneOf(:plain, _get_oneof_field(body, :plain)), keys=keys)
        return _t2201
    else
        _t2200 = nothing
    end
    _t2202 = Proto.TargetRelations(body=OneOf(:cdc, _get_oneof_field(body, :cdc)), keys=keys)
    return _t2202
end

function construct_csv_data(parser::ParserState, locator::Proto.CSVLocator, config::Proto.CSVConfig, columns_opt::Union{Nothing, Vector{Proto.GNFColumn}}, relations_opt::Union{Nothing, Proto.TargetRelations}, asof::String)::Proto.CSVData
    _t2203 = Proto.CSVData(locator=locator, config=config, columns=(!isnothing(columns_opt) ? columns_opt : Proto.GNFColumn[]), asof=asof, relations=relations_opt)
    return _t2203
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}}, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2204 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2204
    _t2205 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2205
    _t2206 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2206
    _t2207 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2207
    _t2208 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2208
    _t2209 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2209
    _t2210 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2210
    _t2211 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2211
    _t2212 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2212
    _t2213 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2213
    _t2214 = _extract_value_string(parser, get(config, "csv_compression", nothing), "")
    compression = _t2214
    _t2215 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2215
    _t2216 = construct_csv_storage_integration(parser, storage_integration_opt)
    storage_integration = _t2216
    _t2217 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
    return _t2217
end

function construct_csv_storage_integration(parser::ParserState, storage_integration_opt::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Union{Nothing, Proto.StorageIntegration}
    if isnothing(storage_integration_opt)
        return nothing
    else
        _t2218 = nothing
    end
    config = Dict(storage_integration_opt)
    _t2219 = _extract_value_string(parser, get(config, "provider", nothing), "")
    _t2220 = _extract_value_string(parser, get(config, "azure_sas_token", nothing), "")
    _t2221 = _extract_value_string(parser, get(config, "s3_region", nothing), "")
    _t2222 = _extract_value_string(parser, get(config, "s3_access_key_id", nothing), "")
    _t2223 = _extract_value_string(parser, get(config, "s3_secret_access_key", nothing), "")
    _t2224 = Proto.StorageIntegration(provider=_t2219, azure_sas_token=_t2220, s3_region=_t2221, s3_access_key_id=_t2222, s3_secret_access_key=_t2223)
    return _t2224
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2225 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2225
    _t2226 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2226
    _t2227 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2227
    _t2228 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2228
    _t2229 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2229
    _t2230 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2230
    _t2231 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2231
    _t2232 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2232
    _t2233 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2233
    _t2234 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2234
    _t2235 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2235
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2236 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2236
    _t2237 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2237
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
    _t2238 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2238
    _t2239 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2239
    _t2240 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2240
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2241 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2241
    _t2242 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2242
    _t2243 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2243
    _t2244 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2244
    _t2245 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2245
    _t2246 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2246
    _t2247 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2247
    _t2248 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2248
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2249 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2249
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2250 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2250
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2251 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2251
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2252 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2252
    _t2253 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2253
    _t2254 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2254
    table_props = Dict(table_property_pairs)
    _t2255 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2255
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start710 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1409 = parse_configure(parser)
        _t1408 = _t1409
    else
        _t1408 = nothing
    end
    configure704 = _t1408
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1411 = parse_sync(parser)
        _t1410 = _t1411
    else
        _t1410 = nothing
    end
    sync705 = _t1410
    xs706 = Proto.Epoch[]
    cond707 = match_lookahead_literal(parser, "(", 0)
    while cond707
        _t1412 = parse_epoch(parser)
        item708 = _t1412
        push!(xs706, item708)
        cond707 = match_lookahead_literal(parser, "(", 0)
    end
    epochs709 = xs706
    consume_literal!(parser, ")")
    _t1413 = default_configure(parser)
    _t1414 = Proto.Transaction(epochs=epochs709, configure=(!isnothing(configure704) ? configure704 : _t1413), sync=sync705)
    result711 = _t1414
    record_span!(parser, span_start710, "Transaction")
    return result711
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start713 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1415 = parse_config_dict(parser)
    config_dict712 = _t1415
    consume_literal!(parser, ")")
    _t1416 = construct_configure(parser, config_dict712)
    result714 = _t1416
    record_span!(parser, span_start713, "Configure")
    return result714
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs715 = Tuple{String, Proto.Value}[]
    cond716 = match_lookahead_literal(parser, ":", 0)
    while cond716
        _t1417 = parse_config_key_value(parser)
        item717 = _t1417
        push!(xs715, item717)
        cond716 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values718 = xs715
    consume_literal!(parser, "}")
    return config_key_values718
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol719 = consume_terminal!(parser, "SYMBOL")
    _t1418 = parse_raw_value(parser)
    raw_value720 = _t1418
    return (symbol719, raw_value720,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start734 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1419 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1420 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1421 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1423 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1424 = 0
                        else
                            _t1424 = -1
                        end
                        _t1423 = _t1424
                    end
                    _t1422 = _t1423
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1425 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1426 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1427 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1428 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1429 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1430 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1431 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1432 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1433 = 10
                                                    else
                                                        _t1433 = -1
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
                            end
                            _t1426 = _t1427
                        end
                        _t1425 = _t1426
                    end
                    _t1422 = _t1425
                end
                _t1421 = _t1422
            end
            _t1420 = _t1421
        end
        _t1419 = _t1420
    end
    prediction721 = _t1419
    if prediction721 == 12
        _t1435 = parse_boolean_value(parser)
        boolean_value733 = _t1435
        _t1436 = Proto.Value(value=OneOf(:boolean_value, boolean_value733))
        _t1434 = _t1436
    else
        if prediction721 == 11
            consume_literal!(parser, "missing")
            _t1438 = Proto.MissingValue()
            _t1439 = Proto.Value(value=OneOf(:missing_value, _t1438))
            _t1437 = _t1439
        else
            if prediction721 == 10
                decimal732 = consume_terminal!(parser, "DECIMAL")
                _t1441 = Proto.Value(value=OneOf(:decimal_value, decimal732))
                _t1440 = _t1441
            else
                if prediction721 == 9
                    int128731 = consume_terminal!(parser, "INT128")
                    _t1443 = Proto.Value(value=OneOf(:int128_value, int128731))
                    _t1442 = _t1443
                else
                    if prediction721 == 8
                        uint128730 = consume_terminal!(parser, "UINT128")
                        _t1445 = Proto.Value(value=OneOf(:uint128_value, uint128730))
                        _t1444 = _t1445
                    else
                        if prediction721 == 7
                            uint32729 = consume_terminal!(parser, "UINT32")
                            _t1447 = Proto.Value(value=OneOf(:uint32_value, uint32729))
                            _t1446 = _t1447
                        else
                            if prediction721 == 6
                                float728 = consume_terminal!(parser, "FLOAT")
                                _t1449 = Proto.Value(value=OneOf(:float_value, float728))
                                _t1448 = _t1449
                            else
                                if prediction721 == 5
                                    float32727 = consume_terminal!(parser, "FLOAT32")
                                    _t1451 = Proto.Value(value=OneOf(:float32_value, float32727))
                                    _t1450 = _t1451
                                else
                                    if prediction721 == 4
                                        int726 = consume_terminal!(parser, "INT")
                                        _t1453 = Proto.Value(value=OneOf(:int_value, int726))
                                        _t1452 = _t1453
                                    else
                                        if prediction721 == 3
                                            int32725 = consume_terminal!(parser, "INT32")
                                            _t1455 = Proto.Value(value=OneOf(:int32_value, int32725))
                                            _t1454 = _t1455
                                        else
                                            if prediction721 == 2
                                                string724 = consume_terminal!(parser, "STRING")
                                                _t1457 = Proto.Value(value=OneOf(:string_value, string724))
                                                _t1456 = _t1457
                                            else
                                                if prediction721 == 1
                                                    _t1459 = parse_raw_datetime(parser)
                                                    raw_datetime723 = _t1459
                                                    _t1460 = Proto.Value(value=OneOf(:datetime_value, raw_datetime723))
                                                    _t1458 = _t1460
                                                else
                                                    if prediction721 == 0
                                                        _t1462 = parse_raw_date(parser)
                                                        raw_date722 = _t1462
                                                        _t1463 = Proto.Value(value=OneOf(:date_value, raw_date722))
                                                        _t1461 = _t1463
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1458 = _t1461
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
                        _t1444 = _t1446
                    end
                    _t1442 = _t1444
                end
                _t1440 = _t1442
            end
            _t1437 = _t1440
        end
        _t1434 = _t1437
    end
    result735 = _t1434
    record_span!(parser, span_start734, "Value")
    return result735
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start739 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int736 = consume_terminal!(parser, "INT")
    int_3737 = consume_terminal!(parser, "INT")
    int_4738 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1464 = Proto.DateValue(year=Int32(int736), month=Int32(int_3737), day=Int32(int_4738))
    result740 = _t1464
    record_span!(parser, span_start739, "DateValue")
    return result740
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start748 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int741 = consume_terminal!(parser, "INT")
    int_3742 = consume_terminal!(parser, "INT")
    int_4743 = consume_terminal!(parser, "INT")
    int_5744 = consume_terminal!(parser, "INT")
    int_6745 = consume_terminal!(parser, "INT")
    int_7746 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1465 = consume_terminal!(parser, "INT")
    else
        _t1465 = nothing
    end
    int_8747 = _t1465
    consume_literal!(parser, ")")
    _t1466 = Proto.DateTimeValue(year=Int32(int741), month=Int32(int_3742), day=Int32(int_4743), hour=Int32(int_5744), minute=Int32(int_6745), second=Int32(int_7746), microsecond=Int32((!isnothing(int_8747) ? int_8747 : 0)))
    result749 = _t1466
    record_span!(parser, span_start748, "DateTimeValue")
    return result749
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1467 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1468 = 1
        else
            _t1468 = -1
        end
        _t1467 = _t1468
    end
    prediction750 = _t1467
    if prediction750 == 1
        consume_literal!(parser, "false")
        _t1469 = false
    else
        if prediction750 == 0
            consume_literal!(parser, "true")
            _t1470 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1469 = _t1470
    end
    return _t1469
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start755 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs751 = Proto.FragmentId[]
    cond752 = match_lookahead_literal(parser, ":", 0)
    while cond752
        _t1471 = parse_fragment_id(parser)
        item753 = _t1471
        push!(xs751, item753)
        cond752 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids754 = xs751
    consume_literal!(parser, ")")
    _t1472 = Proto.Sync(fragments=fragment_ids754)
    result756 = _t1472
    record_span!(parser, span_start755, "Sync")
    return result756
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start758 = span_start(parser)
    consume_literal!(parser, ":")
    symbol757 = consume_terminal!(parser, "SYMBOL")
    result759 = Proto.FragmentId(Vector{UInt8}(symbol757))
    record_span!(parser, span_start758, "FragmentId")
    return result759
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start762 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1474 = parse_epoch_writes(parser)
        _t1473 = _t1474
    else
        _t1473 = nothing
    end
    epoch_writes760 = _t1473
    if match_lookahead_literal(parser, "(", 0)
        _t1476 = parse_epoch_reads(parser)
        _t1475 = _t1476
    else
        _t1475 = nothing
    end
    epoch_reads761 = _t1475
    consume_literal!(parser, ")")
    _t1477 = Proto.Epoch(writes=(!isnothing(epoch_writes760) ? epoch_writes760 : Proto.Write[]), reads=(!isnothing(epoch_reads761) ? epoch_reads761 : Proto.Read[]))
    result763 = _t1477
    record_span!(parser, span_start762, "Epoch")
    return result763
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs764 = Proto.Write[]
    cond765 = match_lookahead_literal(parser, "(", 0)
    while cond765
        _t1478 = parse_write(parser)
        item766 = _t1478
        push!(xs764, item766)
        cond765 = match_lookahead_literal(parser, "(", 0)
    end
    writes767 = xs764
    consume_literal!(parser, ")")
    return writes767
end

function parse_write(parser::ParserState)::Proto.Write
    span_start773 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1480 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1481 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1482 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1483 = 2
                    else
                        _t1483 = -1
                    end
                    _t1482 = _t1483
                end
                _t1481 = _t1482
            end
            _t1480 = _t1481
        end
        _t1479 = _t1480
    else
        _t1479 = -1
    end
    prediction768 = _t1479
    if prediction768 == 3
        _t1485 = parse_snapshot(parser)
        snapshot772 = _t1485
        _t1486 = Proto.Write(write_type=OneOf(:snapshot, snapshot772))
        _t1484 = _t1486
    else
        if prediction768 == 2
            _t1488 = parse_context(parser)
            context771 = _t1488
            _t1489 = Proto.Write(write_type=OneOf(:context, context771))
            _t1487 = _t1489
        else
            if prediction768 == 1
                _t1491 = parse_undefine(parser)
                undefine770 = _t1491
                _t1492 = Proto.Write(write_type=OneOf(:undefine, undefine770))
                _t1490 = _t1492
            else
                if prediction768 == 0
                    _t1494 = parse_define(parser)
                    define769 = _t1494
                    _t1495 = Proto.Write(write_type=OneOf(:define, define769))
                    _t1493 = _t1495
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1490 = _t1493
            end
            _t1487 = _t1490
        end
        _t1484 = _t1487
    end
    result774 = _t1484
    record_span!(parser, span_start773, "Write")
    return result774
end

function parse_define(parser::ParserState)::Proto.Define
    span_start776 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1496 = parse_fragment(parser)
    fragment775 = _t1496
    consume_literal!(parser, ")")
    _t1497 = Proto.Define(fragment=fragment775)
    result777 = _t1497
    record_span!(parser, span_start776, "Define")
    return result777
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start783 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1498 = parse_new_fragment_id(parser)
    new_fragment_id778 = _t1498
    xs779 = Proto.Declaration[]
    cond780 = match_lookahead_literal(parser, "(", 0)
    while cond780
        _t1499 = parse_declaration(parser)
        item781 = _t1499
        push!(xs779, item781)
        cond780 = match_lookahead_literal(parser, "(", 0)
    end
    declarations782 = xs779
    consume_literal!(parser, ")")
    result784 = construct_fragment(parser, new_fragment_id778, declarations782)
    record_span!(parser, span_start783, "Fragment")
    return result784
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start786 = span_start(parser)
    _t1500 = parse_fragment_id(parser)
    fragment_id785 = _t1500
    start_fragment!(parser, fragment_id785)
    result787 = fragment_id785
    record_span!(parser, span_start786, "FragmentId")
    return result787
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start793 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1502 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1503 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1504 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1505 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1506 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1507 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1508 = 1
                                else
                                    _t1508 = -1
                                end
                                _t1507 = _t1508
                            end
                            _t1506 = _t1507
                        end
                        _t1505 = _t1506
                    end
                    _t1504 = _t1505
                end
                _t1503 = _t1504
            end
            _t1502 = _t1503
        end
        _t1501 = _t1502
    else
        _t1501 = -1
    end
    prediction788 = _t1501
    if prediction788 == 3
        _t1510 = parse_data(parser)
        data792 = _t1510
        _t1511 = Proto.Declaration(declaration_type=OneOf(:data, data792))
        _t1509 = _t1511
    else
        if prediction788 == 2
            _t1513 = parse_constraint(parser)
            constraint791 = _t1513
            _t1514 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint791))
            _t1512 = _t1514
        else
            if prediction788 == 1
                _t1516 = parse_algorithm(parser)
                algorithm790 = _t1516
                _t1517 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm790))
                _t1515 = _t1517
            else
                if prediction788 == 0
                    _t1519 = parse_def(parser)
                    def789 = _t1519
                    _t1520 = Proto.Declaration(declaration_type=OneOf(:def, def789))
                    _t1518 = _t1520
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1515 = _t1518
            end
            _t1512 = _t1515
        end
        _t1509 = _t1512
    end
    result794 = _t1509
    record_span!(parser, span_start793, "Declaration")
    return result794
end

function parse_def(parser::ParserState)::Proto.Def
    span_start798 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1521 = parse_relation_id(parser)
    relation_id795 = _t1521
    _t1522 = parse_abstraction(parser)
    abstraction796 = _t1522
    if match_lookahead_literal(parser, "(", 0)
        _t1524 = parse_attrs(parser)
        _t1523 = _t1524
    else
        _t1523 = nothing
    end
    attrs797 = _t1523
    consume_literal!(parser, ")")
    _t1525 = Proto.Def(name=relation_id795, body=abstraction796, attrs=(!isnothing(attrs797) ? attrs797 : Proto.Attribute[]))
    result799 = _t1525
    record_span!(parser, span_start798, "Def")
    return result799
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start803 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1526 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1527 = 1
        else
            _t1527 = -1
        end
        _t1526 = _t1527
    end
    prediction800 = _t1526
    if prediction800 == 1
        uint128802 = consume_terminal!(parser, "UINT128")
        _t1528 = Proto.RelationId(uint128802.low, uint128802.high)
    else
        if prediction800 == 0
            consume_literal!(parser, ":")
            symbol801 = consume_terminal!(parser, "SYMBOL")
            _t1529 = relation_id_from_string(parser, symbol801)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1528 = _t1529
    end
    result804 = _t1528
    record_span!(parser, span_start803, "RelationId")
    return result804
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start807 = span_start(parser)
    consume_literal!(parser, "(")
    _t1530 = parse_bindings(parser)
    bindings805 = _t1530
    _t1531 = parse_formula(parser)
    formula806 = _t1531
    consume_literal!(parser, ")")
    _t1532 = Proto.Abstraction(vars=vcat(bindings805[1], !isnothing(bindings805[2]) ? bindings805[2] : []), value=formula806)
    result808 = _t1532
    record_span!(parser, span_start807, "Abstraction")
    return result808
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs809 = Proto.Binding[]
    cond810 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond810
        _t1533 = parse_binding(parser)
        item811 = _t1533
        push!(xs809, item811)
        cond810 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings812 = xs809
    if match_lookahead_literal(parser, "|", 0)
        _t1535 = parse_value_bindings(parser)
        _t1534 = _t1535
    else
        _t1534 = nothing
    end
    value_bindings813 = _t1534
    consume_literal!(parser, "]")
    return (bindings812, (!isnothing(value_bindings813) ? value_bindings813 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start816 = span_start(parser)
    symbol814 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1536 = parse_type(parser)
    type815 = _t1536
    _t1537 = Proto.Var(name=symbol814)
    _t1538 = Proto.Binding(var=_t1537, var"#type"=type815)
    result817 = _t1538
    record_span!(parser, span_start816, "Binding")
    return result817
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start833 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1539 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1540 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1541 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1542 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1543 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1544 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1545 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1546 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1547 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1548 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1549 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1550 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1551 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1552 = 9
                                                        else
                                                            _t1552 = -1
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
    prediction818 = _t1539
    if prediction818 == 13
        _t1554 = parse_uint32_type(parser)
        uint32_type832 = _t1554
        _t1555 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type832))
        _t1553 = _t1555
    else
        if prediction818 == 12
            _t1557 = parse_float32_type(parser)
            float32_type831 = _t1557
            _t1558 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type831))
            _t1556 = _t1558
        else
            if prediction818 == 11
                _t1560 = parse_int32_type(parser)
                int32_type830 = _t1560
                _t1561 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type830))
                _t1559 = _t1561
            else
                if prediction818 == 10
                    _t1563 = parse_boolean_type(parser)
                    boolean_type829 = _t1563
                    _t1564 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type829))
                    _t1562 = _t1564
                else
                    if prediction818 == 9
                        _t1566 = parse_decimal_type(parser)
                        decimal_type828 = _t1566
                        _t1567 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type828))
                        _t1565 = _t1567
                    else
                        if prediction818 == 8
                            _t1569 = parse_missing_type(parser)
                            missing_type827 = _t1569
                            _t1570 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type827))
                            _t1568 = _t1570
                        else
                            if prediction818 == 7
                                _t1572 = parse_datetime_type(parser)
                                datetime_type826 = _t1572
                                _t1573 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type826))
                                _t1571 = _t1573
                            else
                                if prediction818 == 6
                                    _t1575 = parse_date_type(parser)
                                    date_type825 = _t1575
                                    _t1576 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type825))
                                    _t1574 = _t1576
                                else
                                    if prediction818 == 5
                                        _t1578 = parse_int128_type(parser)
                                        int128_type824 = _t1578
                                        _t1579 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type824))
                                        _t1577 = _t1579
                                    else
                                        if prediction818 == 4
                                            _t1581 = parse_uint128_type(parser)
                                            uint128_type823 = _t1581
                                            _t1582 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type823))
                                            _t1580 = _t1582
                                        else
                                            if prediction818 == 3
                                                _t1584 = parse_float_type(parser)
                                                float_type822 = _t1584
                                                _t1585 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type822))
                                                _t1583 = _t1585
                                            else
                                                if prediction818 == 2
                                                    _t1587 = parse_int_type(parser)
                                                    int_type821 = _t1587
                                                    _t1588 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type821))
                                                    _t1586 = _t1588
                                                else
                                                    if prediction818 == 1
                                                        _t1590 = parse_string_type(parser)
                                                        string_type820 = _t1590
                                                        _t1591 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type820))
                                                        _t1589 = _t1591
                                                    else
                                                        if prediction818 == 0
                                                            _t1593 = parse_unspecified_type(parser)
                                                            unspecified_type819 = _t1593
                                                            _t1594 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type819))
                                                            _t1592 = _t1594
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
            _t1556 = _t1559
        end
        _t1553 = _t1556
    end
    result834 = _t1553
    record_span!(parser, span_start833, "Type")
    return result834
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start835 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1595 = Proto.UnspecifiedType()
    result836 = _t1595
    record_span!(parser, span_start835, "UnspecifiedType")
    return result836
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start837 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1596 = Proto.StringType()
    result838 = _t1596
    record_span!(parser, span_start837, "StringType")
    return result838
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start839 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1597 = Proto.IntType()
    result840 = _t1597
    record_span!(parser, span_start839, "IntType")
    return result840
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start841 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1598 = Proto.FloatType()
    result842 = _t1598
    record_span!(parser, span_start841, "FloatType")
    return result842
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start843 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1599 = Proto.UInt128Type()
    result844 = _t1599
    record_span!(parser, span_start843, "UInt128Type")
    return result844
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start845 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1600 = Proto.Int128Type()
    result846 = _t1600
    record_span!(parser, span_start845, "Int128Type")
    return result846
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start847 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1601 = Proto.DateType()
    result848 = _t1601
    record_span!(parser, span_start847, "DateType")
    return result848
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start849 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1602 = Proto.DateTimeType()
    result850 = _t1602
    record_span!(parser, span_start849, "DateTimeType")
    return result850
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start851 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1603 = Proto.MissingType()
    result852 = _t1603
    record_span!(parser, span_start851, "MissingType")
    return result852
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start855 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int853 = consume_terminal!(parser, "INT")
    int_3854 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1604 = Proto.DecimalType(precision=Int32(int853), scale=Int32(int_3854))
    result856 = _t1604
    record_span!(parser, span_start855, "DecimalType")
    return result856
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start857 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1605 = Proto.BooleanType()
    result858 = _t1605
    record_span!(parser, span_start857, "BooleanType")
    return result858
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start859 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1606 = Proto.Int32Type()
    result860 = _t1606
    record_span!(parser, span_start859, "Int32Type")
    return result860
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start861 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1607 = Proto.Float32Type()
    result862 = _t1607
    record_span!(parser, span_start861, "Float32Type")
    return result862
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start863 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1608 = Proto.UInt32Type()
    result864 = _t1608
    record_span!(parser, span_start863, "UInt32Type")
    return result864
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs865 = Proto.Binding[]
    cond866 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond866
        _t1609 = parse_binding(parser)
        item867 = _t1609
        push!(xs865, item867)
        cond866 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings868 = xs865
    return bindings868
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start883 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1611 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1612 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1613 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1614 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1615 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1616 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1617 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1618 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1619 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1620 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1621 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1622 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1623 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1624 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1625 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1626 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1627 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1628 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1629 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1630 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1631 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1632 = 10
                                                                                            else
                                                                                                _t1632 = -1
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
    else
        _t1610 = -1
    end
    prediction869 = _t1610
    if prediction869 == 12
        _t1634 = parse_cast(parser)
        cast882 = _t1634
        _t1635 = Proto.Formula(formula_type=OneOf(:cast, cast882))
        _t1633 = _t1635
    else
        if prediction869 == 11
            _t1637 = parse_rel_atom(parser)
            rel_atom881 = _t1637
            _t1638 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom881))
            _t1636 = _t1638
        else
            if prediction869 == 10
                _t1640 = parse_primitive(parser)
                primitive880 = _t1640
                _t1641 = Proto.Formula(formula_type=OneOf(:primitive, primitive880))
                _t1639 = _t1641
            else
                if prediction869 == 9
                    _t1643 = parse_pragma(parser)
                    pragma879 = _t1643
                    _t1644 = Proto.Formula(formula_type=OneOf(:pragma, pragma879))
                    _t1642 = _t1644
                else
                    if prediction869 == 8
                        _t1646 = parse_atom(parser)
                        atom878 = _t1646
                        _t1647 = Proto.Formula(formula_type=OneOf(:atom, atom878))
                        _t1645 = _t1647
                    else
                        if prediction869 == 7
                            _t1649 = parse_ffi(parser)
                            ffi877 = _t1649
                            _t1650 = Proto.Formula(formula_type=OneOf(:ffi, ffi877))
                            _t1648 = _t1650
                        else
                            if prediction869 == 6
                                _t1652 = parse_not(parser)
                                not876 = _t1652
                                _t1653 = Proto.Formula(formula_type=OneOf(:not, not876))
                                _t1651 = _t1653
                            else
                                if prediction869 == 5
                                    _t1655 = parse_disjunction(parser)
                                    disjunction875 = _t1655
                                    _t1656 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction875))
                                    _t1654 = _t1656
                                else
                                    if prediction869 == 4
                                        _t1658 = parse_conjunction(parser)
                                        conjunction874 = _t1658
                                        _t1659 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction874))
                                        _t1657 = _t1659
                                    else
                                        if prediction869 == 3
                                            _t1661 = parse_reduce(parser)
                                            reduce873 = _t1661
                                            _t1662 = Proto.Formula(formula_type=OneOf(:reduce, reduce873))
                                            _t1660 = _t1662
                                        else
                                            if prediction869 == 2
                                                _t1664 = parse_exists(parser)
                                                exists872 = _t1664
                                                _t1665 = Proto.Formula(formula_type=OneOf(:exists, exists872))
                                                _t1663 = _t1665
                                            else
                                                if prediction869 == 1
                                                    _t1667 = parse_false(parser)
                                                    false871 = _t1667
                                                    _t1668 = Proto.Formula(formula_type=OneOf(:disjunction, false871))
                                                    _t1666 = _t1668
                                                else
                                                    if prediction869 == 0
                                                        _t1670 = parse_true(parser)
                                                        true870 = _t1670
                                                        _t1671 = Proto.Formula(formula_type=OneOf(:conjunction, true870))
                                                        _t1669 = _t1671
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
            _t1636 = _t1639
        end
        _t1633 = _t1636
    end
    result884 = _t1633
    record_span!(parser, span_start883, "Formula")
    return result884
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start885 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1672 = Proto.Conjunction(args=Proto.Formula[])
    result886 = _t1672
    record_span!(parser, span_start885, "Conjunction")
    return result886
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start887 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1673 = Proto.Disjunction(args=Proto.Formula[])
    result888 = _t1673
    record_span!(parser, span_start887, "Disjunction")
    return result888
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start891 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1674 = parse_bindings(parser)
    bindings889 = _t1674
    _t1675 = parse_formula(parser)
    formula890 = _t1675
    consume_literal!(parser, ")")
    _t1676 = Proto.Abstraction(vars=vcat(bindings889[1], !isnothing(bindings889[2]) ? bindings889[2] : []), value=formula890)
    _t1677 = Proto.Exists(body=_t1676)
    result892 = _t1677
    record_span!(parser, span_start891, "Exists")
    return result892
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start896 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1678 = parse_abstraction(parser)
    abstraction893 = _t1678
    _t1679 = parse_abstraction(parser)
    abstraction_3894 = _t1679
    _t1680 = parse_terms(parser)
    terms895 = _t1680
    consume_literal!(parser, ")")
    _t1681 = Proto.Reduce(op=abstraction893, body=abstraction_3894, terms=terms895)
    result897 = _t1681
    record_span!(parser, span_start896, "Reduce")
    return result897
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs898 = Proto.Term[]
    cond899 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond899
        _t1682 = parse_term(parser)
        item900 = _t1682
        push!(xs898, item900)
        cond899 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms901 = xs898
    consume_literal!(parser, ")")
    return terms901
end

function parse_term(parser::ParserState)::Proto.Term
    span_start905 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1683 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1684 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1685 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1686 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1687 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1688 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1689 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1690 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1691 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1692 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1693 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1694 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1695 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1696 = 1
                                                        else
                                                            _t1696 = -1
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
                            _t1688 = _t1689
                        end
                        _t1687 = _t1688
                    end
                    _t1686 = _t1687
                end
                _t1685 = _t1686
            end
            _t1684 = _t1685
        end
        _t1683 = _t1684
    end
    prediction902 = _t1683
    if prediction902 == 1
        _t1698 = parse_value(parser)
        value904 = _t1698
        _t1699 = Proto.Term(term_type=OneOf(:constant, value904))
        _t1697 = _t1699
    else
        if prediction902 == 0
            _t1701 = parse_var(parser)
            var903 = _t1701
            _t1702 = Proto.Term(term_type=OneOf(:var, var903))
            _t1700 = _t1702
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1697 = _t1700
    end
    result906 = _t1697
    record_span!(parser, span_start905, "Term")
    return result906
end

function parse_var(parser::ParserState)::Proto.Var
    span_start908 = span_start(parser)
    symbol907 = consume_terminal!(parser, "SYMBOL")
    _t1703 = Proto.Var(name=symbol907)
    result909 = _t1703
    record_span!(parser, span_start908, "Var")
    return result909
end

function parse_value(parser::ParserState)::Proto.Value
    span_start923 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1704 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1705 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1706 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1708 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1709 = 0
                        else
                            _t1709 = -1
                        end
                        _t1708 = _t1709
                    end
                    _t1707 = _t1708
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1710 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1711 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1712 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1713 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1714 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1715 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1716 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1717 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1718 = 10
                                                    else
                                                        _t1718 = -1
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
                        end
                        _t1710 = _t1711
                    end
                    _t1707 = _t1710
                end
                _t1706 = _t1707
            end
            _t1705 = _t1706
        end
        _t1704 = _t1705
    end
    prediction910 = _t1704
    if prediction910 == 12
        _t1720 = parse_boolean_value(parser)
        boolean_value922 = _t1720
        _t1721 = Proto.Value(value=OneOf(:boolean_value, boolean_value922))
        _t1719 = _t1721
    else
        if prediction910 == 11
            consume_literal!(parser, "missing")
            _t1723 = Proto.MissingValue()
            _t1724 = Proto.Value(value=OneOf(:missing_value, _t1723))
            _t1722 = _t1724
        else
            if prediction910 == 10
                formatted_decimal921 = consume_terminal!(parser, "DECIMAL")
                _t1726 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal921))
                _t1725 = _t1726
            else
                if prediction910 == 9
                    formatted_int128920 = consume_terminal!(parser, "INT128")
                    _t1728 = Proto.Value(value=OneOf(:int128_value, formatted_int128920))
                    _t1727 = _t1728
                else
                    if prediction910 == 8
                        formatted_uint128919 = consume_terminal!(parser, "UINT128")
                        _t1730 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128919))
                        _t1729 = _t1730
                    else
                        if prediction910 == 7
                            formatted_uint32918 = consume_terminal!(parser, "UINT32")
                            _t1732 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32918))
                            _t1731 = _t1732
                        else
                            if prediction910 == 6
                                formatted_float917 = consume_terminal!(parser, "FLOAT")
                                _t1734 = Proto.Value(value=OneOf(:float_value, formatted_float917))
                                _t1733 = _t1734
                            else
                                if prediction910 == 5
                                    formatted_float32916 = consume_terminal!(parser, "FLOAT32")
                                    _t1736 = Proto.Value(value=OneOf(:float32_value, formatted_float32916))
                                    _t1735 = _t1736
                                else
                                    if prediction910 == 4
                                        formatted_int915 = consume_terminal!(parser, "INT")
                                        _t1738 = Proto.Value(value=OneOf(:int_value, formatted_int915))
                                        _t1737 = _t1738
                                    else
                                        if prediction910 == 3
                                            formatted_int32914 = consume_terminal!(parser, "INT32")
                                            _t1740 = Proto.Value(value=OneOf(:int32_value, formatted_int32914))
                                            _t1739 = _t1740
                                        else
                                            if prediction910 == 2
                                                formatted_string913 = consume_terminal!(parser, "STRING")
                                                _t1742 = Proto.Value(value=OneOf(:string_value, formatted_string913))
                                                _t1741 = _t1742
                                            else
                                                if prediction910 == 1
                                                    _t1744 = parse_datetime(parser)
                                                    datetime912 = _t1744
                                                    _t1745 = Proto.Value(value=OneOf(:datetime_value, datetime912))
                                                    _t1743 = _t1745
                                                else
                                                    if prediction910 == 0
                                                        _t1747 = parse_date(parser)
                                                        date911 = _t1747
                                                        _t1748 = Proto.Value(value=OneOf(:date_value, date911))
                                                        _t1746 = _t1748
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1743 = _t1746
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
                        _t1729 = _t1731
                    end
                    _t1727 = _t1729
                end
                _t1725 = _t1727
            end
            _t1722 = _t1725
        end
        _t1719 = _t1722
    end
    result924 = _t1719
    record_span!(parser, span_start923, "Value")
    return result924
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start928 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int925 = consume_terminal!(parser, "INT")
    formatted_int_3926 = consume_terminal!(parser, "INT")
    formatted_int_4927 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1749 = Proto.DateValue(year=Int32(formatted_int925), month=Int32(formatted_int_3926), day=Int32(formatted_int_4927))
    result929 = _t1749
    record_span!(parser, span_start928, "DateValue")
    return result929
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start937 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int930 = consume_terminal!(parser, "INT")
    formatted_int_3931 = consume_terminal!(parser, "INT")
    formatted_int_4932 = consume_terminal!(parser, "INT")
    formatted_int_5933 = consume_terminal!(parser, "INT")
    formatted_int_6934 = consume_terminal!(parser, "INT")
    formatted_int_7935 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1750 = consume_terminal!(parser, "INT")
    else
        _t1750 = nothing
    end
    formatted_int_8936 = _t1750
    consume_literal!(parser, ")")
    _t1751 = Proto.DateTimeValue(year=Int32(formatted_int930), month=Int32(formatted_int_3931), day=Int32(formatted_int_4932), hour=Int32(formatted_int_5933), minute=Int32(formatted_int_6934), second=Int32(formatted_int_7935), microsecond=Int32((!isnothing(formatted_int_8936) ? formatted_int_8936 : 0)))
    result938 = _t1751
    record_span!(parser, span_start937, "DateTimeValue")
    return result938
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start943 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs939 = Proto.Formula[]
    cond940 = match_lookahead_literal(parser, "(", 0)
    while cond940
        _t1752 = parse_formula(parser)
        item941 = _t1752
        push!(xs939, item941)
        cond940 = match_lookahead_literal(parser, "(", 0)
    end
    formulas942 = xs939
    consume_literal!(parser, ")")
    _t1753 = Proto.Conjunction(args=formulas942)
    result944 = _t1753
    record_span!(parser, span_start943, "Conjunction")
    return result944
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start949 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs945 = Proto.Formula[]
    cond946 = match_lookahead_literal(parser, "(", 0)
    while cond946
        _t1754 = parse_formula(parser)
        item947 = _t1754
        push!(xs945, item947)
        cond946 = match_lookahead_literal(parser, "(", 0)
    end
    formulas948 = xs945
    consume_literal!(parser, ")")
    _t1755 = Proto.Disjunction(args=formulas948)
    result950 = _t1755
    record_span!(parser, span_start949, "Disjunction")
    return result950
end

function parse_not(parser::ParserState)::Proto.Not
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1756 = parse_formula(parser)
    formula951 = _t1756
    consume_literal!(parser, ")")
    _t1757 = Proto.Not(arg=formula951)
    result953 = _t1757
    record_span!(parser, span_start952, "Not")
    return result953
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start957 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1758 = parse_name(parser)
    name954 = _t1758
    _t1759 = parse_ffi_args(parser)
    ffi_args955 = _t1759
    _t1760 = parse_terms(parser)
    terms956 = _t1760
    consume_literal!(parser, ")")
    _t1761 = Proto.FFI(name=name954, args=ffi_args955, terms=terms956)
    result958 = _t1761
    record_span!(parser, span_start957, "FFI")
    return result958
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol959 = consume_terminal!(parser, "SYMBOL")
    return symbol959
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs960 = Proto.Abstraction[]
    cond961 = match_lookahead_literal(parser, "(", 0)
    while cond961
        _t1762 = parse_abstraction(parser)
        item962 = _t1762
        push!(xs960, item962)
        cond961 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions963 = xs960
    consume_literal!(parser, ")")
    return abstractions963
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1763 = parse_relation_id(parser)
    relation_id964 = _t1763
    xs965 = Proto.Term[]
    cond966 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond966
        _t1764 = parse_term(parser)
        item967 = _t1764
        push!(xs965, item967)
        cond966 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms968 = xs965
    consume_literal!(parser, ")")
    _t1765 = Proto.Atom(name=relation_id964, terms=terms968)
    result970 = _t1765
    record_span!(parser, span_start969, "Atom")
    return result970
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start976 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1766 = parse_name(parser)
    name971 = _t1766
    xs972 = Proto.Term[]
    cond973 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond973
        _t1767 = parse_term(parser)
        item974 = _t1767
        push!(xs972, item974)
        cond973 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms975 = xs972
    consume_literal!(parser, ")")
    _t1768 = Proto.Pragma(name=name971, terms=terms975)
    result977 = _t1768
    record_span!(parser, span_start976, "Pragma")
    return result977
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start993 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1770 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1771 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1772 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1773 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1774 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1775 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1776 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1777 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1778 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1779 = 7
                                            else
                                                _t1779 = -1
                                            end
                                            _t1778 = _t1779
                                        end
                                        _t1777 = _t1778
                                    end
                                    _t1776 = _t1777
                                end
                                _t1775 = _t1776
                            end
                            _t1774 = _t1775
                        end
                        _t1773 = _t1774
                    end
                    _t1772 = _t1773
                end
                _t1771 = _t1772
            end
            _t1770 = _t1771
        end
        _t1769 = _t1770
    else
        _t1769 = -1
    end
    prediction978 = _t1769
    if prediction978 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1781 = parse_name(parser)
        name988 = _t1781
        xs989 = Proto.RelTerm[]
        cond990 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond990
            _t1782 = parse_rel_term(parser)
            item991 = _t1782
            push!(xs989, item991)
            cond990 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms992 = xs989
        consume_literal!(parser, ")")
        _t1783 = Proto.Primitive(name=name988, terms=rel_terms992)
        _t1780 = _t1783
    else
        if prediction978 == 8
            _t1785 = parse_divide(parser)
            divide987 = _t1785
            _t1784 = divide987
        else
            if prediction978 == 7
                _t1787 = parse_multiply(parser)
                multiply986 = _t1787
                _t1786 = multiply986
            else
                if prediction978 == 6
                    _t1789 = parse_minus(parser)
                    minus985 = _t1789
                    _t1788 = minus985
                else
                    if prediction978 == 5
                        _t1791 = parse_add(parser)
                        add984 = _t1791
                        _t1790 = add984
                    else
                        if prediction978 == 4
                            _t1793 = parse_gt_eq(parser)
                            gt_eq983 = _t1793
                            _t1792 = gt_eq983
                        else
                            if prediction978 == 3
                                _t1795 = parse_gt(parser)
                                gt982 = _t1795
                                _t1794 = gt982
                            else
                                if prediction978 == 2
                                    _t1797 = parse_lt_eq(parser)
                                    lt_eq981 = _t1797
                                    _t1796 = lt_eq981
                                else
                                    if prediction978 == 1
                                        _t1799 = parse_lt(parser)
                                        lt980 = _t1799
                                        _t1798 = lt980
                                    else
                                        if prediction978 == 0
                                            _t1801 = parse_eq(parser)
                                            eq979 = _t1801
                                            _t1800 = eq979
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
                    _t1788 = _t1790
                end
                _t1786 = _t1788
            end
            _t1784 = _t1786
        end
        _t1780 = _t1784
    end
    result994 = _t1780
    record_span!(parser, span_start993, "Primitive")
    return result994
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start997 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1802 = parse_term(parser)
    term995 = _t1802
    _t1803 = parse_term(parser)
    term_3996 = _t1803
    consume_literal!(parser, ")")
    _t1804 = Proto.RelTerm(rel_term_type=OneOf(:term, term995))
    _t1805 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3996))
    _t1806 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1804, _t1805])
    result998 = _t1806
    record_span!(parser, span_start997, "Primitive")
    return result998
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start1001 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1807 = parse_term(parser)
    term999 = _t1807
    _t1808 = parse_term(parser)
    term_31000 = _t1808
    consume_literal!(parser, ")")
    _t1809 = Proto.RelTerm(rel_term_type=OneOf(:term, term999))
    _t1810 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31000))
    _t1811 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1809, _t1810])
    result1002 = _t1811
    record_span!(parser, span_start1001, "Primitive")
    return result1002
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start1005 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1812 = parse_term(parser)
    term1003 = _t1812
    _t1813 = parse_term(parser)
    term_31004 = _t1813
    consume_literal!(parser, ")")
    _t1814 = Proto.RelTerm(rel_term_type=OneOf(:term, term1003))
    _t1815 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31004))
    _t1816 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1814, _t1815])
    result1006 = _t1816
    record_span!(parser, span_start1005, "Primitive")
    return result1006
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start1009 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1817 = parse_term(parser)
    term1007 = _t1817
    _t1818 = parse_term(parser)
    term_31008 = _t1818
    consume_literal!(parser, ")")
    _t1819 = Proto.RelTerm(rel_term_type=OneOf(:term, term1007))
    _t1820 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31008))
    _t1821 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1819, _t1820])
    result1010 = _t1821
    record_span!(parser, span_start1009, "Primitive")
    return result1010
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start1013 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1822 = parse_term(parser)
    term1011 = _t1822
    _t1823 = parse_term(parser)
    term_31012 = _t1823
    consume_literal!(parser, ")")
    _t1824 = Proto.RelTerm(rel_term_type=OneOf(:term, term1011))
    _t1825 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31012))
    _t1826 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1824, _t1825])
    result1014 = _t1826
    record_span!(parser, span_start1013, "Primitive")
    return result1014
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start1018 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1827 = parse_term(parser)
    term1015 = _t1827
    _t1828 = parse_term(parser)
    term_31016 = _t1828
    _t1829 = parse_term(parser)
    term_41017 = _t1829
    consume_literal!(parser, ")")
    _t1830 = Proto.RelTerm(rel_term_type=OneOf(:term, term1015))
    _t1831 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31016))
    _t1832 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41017))
    _t1833 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1830, _t1831, _t1832])
    result1019 = _t1833
    record_span!(parser, span_start1018, "Primitive")
    return result1019
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start1023 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1834 = parse_term(parser)
    term1020 = _t1834
    _t1835 = parse_term(parser)
    term_31021 = _t1835
    _t1836 = parse_term(parser)
    term_41022 = _t1836
    consume_literal!(parser, ")")
    _t1837 = Proto.RelTerm(rel_term_type=OneOf(:term, term1020))
    _t1838 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31021))
    _t1839 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41022))
    _t1840 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1837, _t1838, _t1839])
    result1024 = _t1840
    record_span!(parser, span_start1023, "Primitive")
    return result1024
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start1028 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1841 = parse_term(parser)
    term1025 = _t1841
    _t1842 = parse_term(parser)
    term_31026 = _t1842
    _t1843 = parse_term(parser)
    term_41027 = _t1843
    consume_literal!(parser, ")")
    _t1844 = Proto.RelTerm(rel_term_type=OneOf(:term, term1025))
    _t1845 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31026))
    _t1846 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41027))
    _t1847 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1844, _t1845, _t1846])
    result1029 = _t1847
    record_span!(parser, span_start1028, "Primitive")
    return result1029
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1033 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1848 = parse_term(parser)
    term1030 = _t1848
    _t1849 = parse_term(parser)
    term_31031 = _t1849
    _t1850 = parse_term(parser)
    term_41032 = _t1850
    consume_literal!(parser, ")")
    _t1851 = Proto.RelTerm(rel_term_type=OneOf(:term, term1030))
    _t1852 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31031))
    _t1853 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41032))
    _t1854 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1851, _t1852, _t1853])
    result1034 = _t1854
    record_span!(parser, span_start1033, "Primitive")
    return result1034
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1038 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1855 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1856 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1857 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1858 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1859 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1860 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1861 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1862 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1863 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1864 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1865 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1866 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1867 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1868 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1869 = 1
                                                            else
                                                                _t1869 = -1
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
                            _t1860 = _t1861
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
    end
    prediction1035 = _t1855
    if prediction1035 == 1
        _t1871 = parse_term(parser)
        term1037 = _t1871
        _t1872 = Proto.RelTerm(rel_term_type=OneOf(:term, term1037))
        _t1870 = _t1872
    else
        if prediction1035 == 0
            _t1874 = parse_specialized_value(parser)
            specialized_value1036 = _t1874
            _t1875 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1036))
            _t1873 = _t1875
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1870 = _t1873
    end
    result1039 = _t1870
    record_span!(parser, span_start1038, "RelTerm")
    return result1039
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1041 = span_start(parser)
    consume_literal!(parser, "#")
    _t1876 = parse_raw_value(parser)
    raw_value1040 = _t1876
    result1042 = raw_value1040
    record_span!(parser, span_start1041, "Value")
    return result1042
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1048 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1877 = parse_name(parser)
    name1043 = _t1877
    xs1044 = Proto.RelTerm[]
    cond1045 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1045
        _t1878 = parse_rel_term(parser)
        item1046 = _t1878
        push!(xs1044, item1046)
        cond1045 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1047 = xs1044
    consume_literal!(parser, ")")
    _t1879 = Proto.RelAtom(name=name1043, terms=rel_terms1047)
    result1049 = _t1879
    record_span!(parser, span_start1048, "RelAtom")
    return result1049
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1052 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1880 = parse_term(parser)
    term1050 = _t1880
    _t1881 = parse_term(parser)
    term_31051 = _t1881
    consume_literal!(parser, ")")
    _t1882 = Proto.Cast(input=term1050, result=term_31051)
    result1053 = _t1882
    record_span!(parser, span_start1052, "Cast")
    return result1053
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1054 = Proto.Attribute[]
    cond1055 = match_lookahead_literal(parser, "(", 0)
    while cond1055
        _t1883 = parse_attribute(parser)
        item1056 = _t1883
        push!(xs1054, item1056)
        cond1055 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1057 = xs1054
    consume_literal!(parser, ")")
    return attributes1057
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1063 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1884 = parse_name(parser)
    name1058 = _t1884
    xs1059 = Proto.Value[]
    cond1060 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1060
        _t1885 = parse_raw_value(parser)
        item1061 = _t1885
        push!(xs1059, item1061)
        cond1060 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1062 = xs1059
    consume_literal!(parser, ")")
    _t1886 = Proto.Attribute(name=name1058, args=raw_values1062)
    result1064 = _t1886
    record_span!(parser, span_start1063, "Attribute")
    return result1064
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1071 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1065 = Proto.RelationId[]
    cond1066 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1066
        _t1887 = parse_relation_id(parser)
        item1067 = _t1887
        push!(xs1065, item1067)
        cond1066 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1068 = xs1065
    _t1888 = parse_script(parser)
    script1069 = _t1888
    if match_lookahead_literal(parser, "(", 0)
        _t1890 = parse_attrs(parser)
        _t1889 = _t1890
    else
        _t1889 = nothing
    end
    attrs1070 = _t1889
    consume_literal!(parser, ")")
    _t1891 = Proto.Algorithm(var"#global"=relation_ids1068, body=script1069, attrs=(!isnothing(attrs1070) ? attrs1070 : Proto.Attribute[]))
    result1072 = _t1891
    record_span!(parser, span_start1071, "Algorithm")
    return result1072
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1077 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1073 = Proto.Construct[]
    cond1074 = match_lookahead_literal(parser, "(", 0)
    while cond1074
        _t1892 = parse_construct(parser)
        item1075 = _t1892
        push!(xs1073, item1075)
        cond1074 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1076 = xs1073
    consume_literal!(parser, ")")
    _t1893 = Proto.Script(constructs=constructs1076)
    result1078 = _t1893
    record_span!(parser, span_start1077, "Script")
    return result1078
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1082 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1895 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1896 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1897 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1898 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1899 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1900 = 1
                            else
                                _t1900 = -1
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
    else
        _t1894 = -1
    end
    prediction1079 = _t1894
    if prediction1079 == 1
        _t1902 = parse_instruction(parser)
        instruction1081 = _t1902
        _t1903 = Proto.Construct(construct_type=OneOf(:instruction, instruction1081))
        _t1901 = _t1903
    else
        if prediction1079 == 0
            _t1905 = parse_loop(parser)
            loop1080 = _t1905
            _t1906 = Proto.Construct(construct_type=OneOf(:loop, loop1080))
            _t1904 = _t1906
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1901 = _t1904
    end
    result1083 = _t1901
    record_span!(parser, span_start1082, "Construct")
    return result1083
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1087 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1907 = parse_init(parser)
    init1084 = _t1907
    _t1908 = parse_script(parser)
    script1085 = _t1908
    if match_lookahead_literal(parser, "(", 0)
        _t1910 = parse_attrs(parser)
        _t1909 = _t1910
    else
        _t1909 = nothing
    end
    attrs1086 = _t1909
    consume_literal!(parser, ")")
    _t1911 = Proto.Loop(init=init1084, body=script1085, attrs=(!isnothing(attrs1086) ? attrs1086 : Proto.Attribute[]))
    result1088 = _t1911
    record_span!(parser, span_start1087, "Loop")
    return result1088
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1089 = Proto.Instruction[]
    cond1090 = match_lookahead_literal(parser, "(", 0)
    while cond1090
        _t1912 = parse_instruction(parser)
        item1091 = _t1912
        push!(xs1089, item1091)
        cond1090 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1092 = xs1089
    consume_literal!(parser, ")")
    return instructions1092
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1099 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1914 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1915 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1916 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1917 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1918 = 0
                        else
                            _t1918 = -1
                        end
                        _t1917 = _t1918
                    end
                    _t1916 = _t1917
                end
                _t1915 = _t1916
            end
            _t1914 = _t1915
        end
        _t1913 = _t1914
    else
        _t1913 = -1
    end
    prediction1093 = _t1913
    if prediction1093 == 4
        _t1920 = parse_monus_def(parser)
        monus_def1098 = _t1920
        _t1921 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1098))
        _t1919 = _t1921
    else
        if prediction1093 == 3
            _t1923 = parse_monoid_def(parser)
            monoid_def1097 = _t1923
            _t1924 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1097))
            _t1922 = _t1924
        else
            if prediction1093 == 2
                _t1926 = parse_break(parser)
                break1096 = _t1926
                _t1927 = Proto.Instruction(instr_type=OneOf(:var"#break", break1096))
                _t1925 = _t1927
            else
                if prediction1093 == 1
                    _t1929 = parse_upsert(parser)
                    upsert1095 = _t1929
                    _t1930 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1095))
                    _t1928 = _t1930
                else
                    if prediction1093 == 0
                        _t1932 = parse_assign(parser)
                        assign1094 = _t1932
                        _t1933 = Proto.Instruction(instr_type=OneOf(:assign, assign1094))
                        _t1931 = _t1933
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1928 = _t1931
                end
                _t1925 = _t1928
            end
            _t1922 = _t1925
        end
        _t1919 = _t1922
    end
    result1100 = _t1919
    record_span!(parser, span_start1099, "Instruction")
    return result1100
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1104 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1934 = parse_relation_id(parser)
    relation_id1101 = _t1934
    _t1935 = parse_abstraction(parser)
    abstraction1102 = _t1935
    if match_lookahead_literal(parser, "(", 0)
        _t1937 = parse_attrs(parser)
        _t1936 = _t1937
    else
        _t1936 = nothing
    end
    attrs1103 = _t1936
    consume_literal!(parser, ")")
    _t1938 = Proto.Assign(name=relation_id1101, body=abstraction1102, attrs=(!isnothing(attrs1103) ? attrs1103 : Proto.Attribute[]))
    result1105 = _t1938
    record_span!(parser, span_start1104, "Assign")
    return result1105
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1109 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1939 = parse_relation_id(parser)
    relation_id1106 = _t1939
    _t1940 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1107 = _t1940
    if match_lookahead_literal(parser, "(", 0)
        _t1942 = parse_attrs(parser)
        _t1941 = _t1942
    else
        _t1941 = nothing
    end
    attrs1108 = _t1941
    consume_literal!(parser, ")")
    _t1943 = Proto.Upsert(name=relation_id1106, body=abstraction_with_arity1107[1], attrs=(!isnothing(attrs1108) ? attrs1108 : Proto.Attribute[]), value_arity=abstraction_with_arity1107[2])
    result1110 = _t1943
    record_span!(parser, span_start1109, "Upsert")
    return result1110
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1944 = parse_bindings(parser)
    bindings1111 = _t1944
    _t1945 = parse_formula(parser)
    formula1112 = _t1945
    consume_literal!(parser, ")")
    _t1946 = Proto.Abstraction(vars=vcat(bindings1111[1], !isnothing(bindings1111[2]) ? bindings1111[2] : []), value=formula1112)
    return (_t1946, length(bindings1111[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1116 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1947 = parse_relation_id(parser)
    relation_id1113 = _t1947
    _t1948 = parse_abstraction(parser)
    abstraction1114 = _t1948
    if match_lookahead_literal(parser, "(", 0)
        _t1950 = parse_attrs(parser)
        _t1949 = _t1950
    else
        _t1949 = nothing
    end
    attrs1115 = _t1949
    consume_literal!(parser, ")")
    _t1951 = Proto.Break(name=relation_id1113, body=abstraction1114, attrs=(!isnothing(attrs1115) ? attrs1115 : Proto.Attribute[]))
    result1117 = _t1951
    record_span!(parser, span_start1116, "Break")
    return result1117
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1122 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1952 = parse_monoid(parser)
    monoid1118 = _t1952
    _t1953 = parse_relation_id(parser)
    relation_id1119 = _t1953
    _t1954 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1120 = _t1954
    if match_lookahead_literal(parser, "(", 0)
        _t1956 = parse_attrs(parser)
        _t1955 = _t1956
    else
        _t1955 = nothing
    end
    attrs1121 = _t1955
    consume_literal!(parser, ")")
    _t1957 = Proto.MonoidDef(monoid=monoid1118, name=relation_id1119, body=abstraction_with_arity1120[1], attrs=(!isnothing(attrs1121) ? attrs1121 : Proto.Attribute[]), value_arity=abstraction_with_arity1120[2])
    result1123 = _t1957
    record_span!(parser, span_start1122, "MonoidDef")
    return result1123
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1129 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1959 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1960 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1961 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1962 = 2
                    else
                        _t1962 = -1
                    end
                    _t1961 = _t1962
                end
                _t1960 = _t1961
            end
            _t1959 = _t1960
        end
        _t1958 = _t1959
    else
        _t1958 = -1
    end
    prediction1124 = _t1958
    if prediction1124 == 3
        _t1964 = parse_sum_monoid(parser)
        sum_monoid1128 = _t1964
        _t1965 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1128))
        _t1963 = _t1965
    else
        if prediction1124 == 2
            _t1967 = parse_max_monoid(parser)
            max_monoid1127 = _t1967
            _t1968 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1127))
            _t1966 = _t1968
        else
            if prediction1124 == 1
                _t1970 = parse_min_monoid(parser)
                min_monoid1126 = _t1970
                _t1971 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1126))
                _t1969 = _t1971
            else
                if prediction1124 == 0
                    _t1973 = parse_or_monoid(parser)
                    or_monoid1125 = _t1973
                    _t1974 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1125))
                    _t1972 = _t1974
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1969 = _t1972
            end
            _t1966 = _t1969
        end
        _t1963 = _t1966
    end
    result1130 = _t1963
    record_span!(parser, span_start1129, "Monoid")
    return result1130
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1131 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1975 = Proto.OrMonoid()
    result1132 = _t1975
    record_span!(parser, span_start1131, "OrMonoid")
    return result1132
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1134 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1976 = parse_type(parser)
    type1133 = _t1976
    consume_literal!(parser, ")")
    _t1977 = Proto.MinMonoid(var"#type"=type1133)
    result1135 = _t1977
    record_span!(parser, span_start1134, "MinMonoid")
    return result1135
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1137 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1978 = parse_type(parser)
    type1136 = _t1978
    consume_literal!(parser, ")")
    _t1979 = Proto.MaxMonoid(var"#type"=type1136)
    result1138 = _t1979
    record_span!(parser, span_start1137, "MaxMonoid")
    return result1138
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1140 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1980 = parse_type(parser)
    type1139 = _t1980
    consume_literal!(parser, ")")
    _t1981 = Proto.SumMonoid(var"#type"=type1139)
    result1141 = _t1981
    record_span!(parser, span_start1140, "SumMonoid")
    return result1141
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1146 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1982 = parse_monoid(parser)
    monoid1142 = _t1982
    _t1983 = parse_relation_id(parser)
    relation_id1143 = _t1983
    _t1984 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1144 = _t1984
    if match_lookahead_literal(parser, "(", 0)
        _t1986 = parse_attrs(parser)
        _t1985 = _t1986
    else
        _t1985 = nothing
    end
    attrs1145 = _t1985
    consume_literal!(parser, ")")
    _t1987 = Proto.MonusDef(monoid=monoid1142, name=relation_id1143, body=abstraction_with_arity1144[1], attrs=(!isnothing(attrs1145) ? attrs1145 : Proto.Attribute[]), value_arity=abstraction_with_arity1144[2])
    result1147 = _t1987
    record_span!(parser, span_start1146, "MonusDef")
    return result1147
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1152 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1988 = parse_relation_id(parser)
    relation_id1148 = _t1988
    _t1989 = parse_abstraction(parser)
    abstraction1149 = _t1989
    _t1990 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1150 = _t1990
    _t1991 = parse_functional_dependency_values(parser)
    functional_dependency_values1151 = _t1991
    consume_literal!(parser, ")")
    _t1992 = Proto.FunctionalDependency(guard=abstraction1149, keys=functional_dependency_keys1150, values=functional_dependency_values1151)
    _t1993 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1992), name=relation_id1148)
    result1153 = _t1993
    record_span!(parser, span_start1152, "Constraint")
    return result1153
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1154 = Proto.Var[]
    cond1155 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1155
        _t1994 = parse_var(parser)
        item1156 = _t1994
        push!(xs1154, item1156)
        cond1155 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1157 = xs1154
    consume_literal!(parser, ")")
    return vars1157
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1158 = Proto.Var[]
    cond1159 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1159
        _t1995 = parse_var(parser)
        item1160 = _t1995
        push!(xs1158, item1160)
        cond1159 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1161 = xs1158
    consume_literal!(parser, ")")
    return vars1161
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1167 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1997 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1998 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1999 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t2000 = 1
                    else
                        _t2000 = -1
                    end
                    _t1999 = _t2000
                end
                _t1998 = _t1999
            end
            _t1997 = _t1998
        end
        _t1996 = _t1997
    else
        _t1996 = -1
    end
    prediction1162 = _t1996
    if prediction1162 == 3
        _t2002 = parse_iceberg_data(parser)
        iceberg_data1166 = _t2002
        _t2003 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1166))
        _t2001 = _t2003
    else
        if prediction1162 == 2
            _t2005 = parse_csv_data(parser)
            csv_data1165 = _t2005
            _t2006 = Proto.Data(data_type=OneOf(:csv_data, csv_data1165))
            _t2004 = _t2006
        else
            if prediction1162 == 1
                _t2008 = parse_betree_relation(parser)
                betree_relation1164 = _t2008
                _t2009 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1164))
                _t2007 = _t2009
            else
                if prediction1162 == 0
                    _t2011 = parse_edb(parser)
                    edb1163 = _t2011
                    _t2012 = Proto.Data(data_type=OneOf(:edb, edb1163))
                    _t2010 = _t2012
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t2007 = _t2010
            end
            _t2004 = _t2007
        end
        _t2001 = _t2004
    end
    result1168 = _t2001
    record_span!(parser, span_start1167, "Data")
    return result1168
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1172 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t2013 = parse_relation_id(parser)
    relation_id1169 = _t2013
    _t2014 = parse_edb_path(parser)
    edb_path1170 = _t2014
    _t2015 = parse_edb_types(parser)
    edb_types1171 = _t2015
    consume_literal!(parser, ")")
    _t2016 = Proto.EDB(target_id=relation_id1169, path=edb_path1170, types=edb_types1171)
    result1173 = _t2016
    record_span!(parser, span_start1172, "EDB")
    return result1173
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1174 = String[]
    cond1175 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1175
        item1176 = consume_terminal!(parser, "STRING")
        push!(xs1174, item1176)
        cond1175 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1177 = xs1174
    consume_literal!(parser, "]")
    return strings1177
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1178 = Proto.var"#Type"[]
    cond1179 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1179
        _t2017 = parse_type(parser)
        item1180 = _t2017
        push!(xs1178, item1180)
        cond1179 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1181 = xs1178
    consume_literal!(parser, "]")
    return types1181
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1184 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t2018 = parse_relation_id(parser)
    relation_id1182 = _t2018
    _t2019 = parse_betree_info(parser)
    betree_info1183 = _t2019
    consume_literal!(parser, ")")
    _t2020 = Proto.BeTreeRelation(name=relation_id1182, relation_info=betree_info1183)
    result1185 = _t2020
    record_span!(parser, span_start1184, "BeTreeRelation")
    return result1185
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1189 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t2021 = parse_betree_info_key_types(parser)
    betree_info_key_types1186 = _t2021
    _t2022 = parse_betree_info_value_types(parser)
    betree_info_value_types1187 = _t2022
    _t2023 = parse_config_dict(parser)
    config_dict1188 = _t2023
    consume_literal!(parser, ")")
    _t2024 = construct_betree_info(parser, betree_info_key_types1186, betree_info_value_types1187, config_dict1188)
    result1190 = _t2024
    record_span!(parser, span_start1189, "BeTreeInfo")
    return result1190
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1191 = Proto.var"#Type"[]
    cond1192 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1192
        _t2025 = parse_type(parser)
        item1193 = _t2025
        push!(xs1191, item1193)
        cond1192 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1194 = xs1191
    consume_literal!(parser, ")")
    return types1194
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1195 = Proto.var"#Type"[]
    cond1196 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1196
        _t2026 = parse_type(parser)
        item1197 = _t2026
        push!(xs1195, item1197)
        cond1196 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1198 = xs1195
    consume_literal!(parser, ")")
    return types1198
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1204 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t2027 = parse_csvlocator(parser)
    csvlocator1199 = _t2027
    _t2028 = parse_csv_config(parser)
    csv_config1200 = _t2028
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "columns", 1))
        _t2030 = parse_gnf_columns(parser)
        _t2029 = _t2030
    else
        _t2029 = nothing
    end
    gnf_columns1201 = _t2029
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "relations", 1))
        _t2032 = parse_target_relations(parser)
        _t2031 = _t2032
    else
        _t2031 = nothing
    end
    target_relations1202 = _t2031
    _t2033 = parse_csv_asof(parser)
    csv_asof1203 = _t2033
    consume_literal!(parser, ")")
    _t2034 = construct_csv_data(parser, csvlocator1199, csv_config1200, gnf_columns1201, target_relations1202, csv_asof1203)
    result1205 = _t2034
    record_span!(parser, span_start1204, "CSVData")
    return result1205
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1208 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t2036 = parse_csv_locator_paths(parser)
        _t2035 = _t2036
    else
        _t2035 = nothing
    end
    csv_locator_paths1206 = _t2035
    if match_lookahead_literal(parser, "(", 0)
        _t2038 = parse_csv_locator_inline_data(parser)
        _t2037 = _t2038
    else
        _t2037 = nothing
    end
    csv_locator_inline_data1207 = _t2037
    consume_literal!(parser, ")")
    _t2039 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1206) ? csv_locator_paths1206 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1207) ? csv_locator_inline_data1207 : "")))
    result1209 = _t2039
    record_span!(parser, span_start1208, "CSVLocator")
    return result1209
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1210 = String[]
    cond1211 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1211
        item1212 = consume_terminal!(parser, "STRING")
        push!(xs1210, item1212)
        cond1211 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1213 = xs1210
    consume_literal!(parser, ")")
    return strings1213
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    formatted_string1214 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return formatted_string1214
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1217 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t2040 = parse_config_dict(parser)
    config_dict1215 = _t2040
    if match_lookahead_literal(parser, "(", 0)
        _t2042 = parse__storage_integration(parser)
        _t2041 = _t2042
    else
        _t2041 = nothing
    end
    _storage_integration1216 = _t2041
    consume_literal!(parser, ")")
    _t2043 = construct_csv_config(parser, config_dict1215, _storage_integration1216)
    result1218 = _t2043
    record_span!(parser, span_start1217, "CSVConfig")
    return result1218
end

function parse__storage_integration(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "storage_integration")
    _t2044 = parse_config_dict(parser)
    config_dict1219 = _t2044
    consume_literal!(parser, ")")
    return config_dict1219
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1220 = Proto.GNFColumn[]
    cond1221 = match_lookahead_literal(parser, "(", 0)
    while cond1221
        _t2045 = parse_gnf_column(parser)
        item1222 = _t2045
        push!(xs1220, item1222)
        cond1221 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1223 = xs1220
    consume_literal!(parser, ")")
    return gnf_columns1223
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1230 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t2046 = parse_gnf_column_path(parser)
    gnf_column_path1224 = _t2046
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t2048 = parse_relation_id(parser)
        _t2047 = _t2048
    else
        _t2047 = nothing
    end
    relation_id1225 = _t2047
    consume_literal!(parser, "[")
    xs1226 = Proto.var"#Type"[]
    cond1227 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1227
        _t2049 = parse_type(parser)
        item1228 = _t2049
        push!(xs1226, item1228)
        cond1227 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1229 = xs1226
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t2050 = Proto.GNFColumn(column_path=gnf_column_path1224, target_id=relation_id1225, types=types1229)
    result1231 = _t2050
    record_span!(parser, span_start1230, "GNFColumn")
    return result1231
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t2051 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t2052 = 0
        else
            _t2052 = -1
        end
        _t2051 = _t2052
    end
    prediction1232 = _t2051
    if prediction1232 == 1
        consume_literal!(parser, "[")
        xs1234 = String[]
        cond1235 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1235
            item1236 = consume_terminal!(parser, "STRING")
            push!(xs1234, item1236)
            cond1235 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1237 = xs1234
        consume_literal!(parser, "]")
        _t2053 = strings1237
    else
        if prediction1232 == 0
            string1233 = consume_terminal!(parser, "STRING")
            _t2054 = String[string1233]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t2053 = _t2054
    end
    return _t2053
end

function parse_target_relations(parser::ParserState)::Proto.TargetRelations
    span_start1240 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relations")
    _t2055 = parse_relation_keys(parser)
    relation_keys1238 = _t2055
    _t2056 = parse_relation_body(parser)
    relation_body1239 = _t2056
    consume_literal!(parser, ")")
    _t2057 = construct_relations(parser, relation_keys1238, relation_body1239)
    result1241 = _t2057
    record_span!(parser, span_start1240, "TargetRelations")
    return result1241
end

function parse_relation_keys(parser::ParserState)::Vector{Proto.NamedColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1242 = Proto.NamedColumn[]
    cond1243 = match_lookahead_literal(parser, "(", 0)
    while cond1243
        _t2058 = parse_named_column(parser)
        item1244 = _t2058
        push!(xs1242, item1244)
        cond1243 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1245 = xs1242
    consume_literal!(parser, ")")
    return named_columns1245
end

function parse_named_column(parser::ParserState)::Proto.NamedColumn
    span_start1248 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1246 = consume_terminal!(parser, "STRING")
    _t2059 = parse_type(parser)
    type1247 = _t2059
    consume_literal!(parser, ")")
    _t2060 = Proto.NamedColumn(name=string1246, var"#type"=type1247)
    result1249 = _t2060
    record_span!(parser, span_start1248, "NamedColumn")
    return result1249
end

function parse_relation_body(parser::ParserState)::Proto.TargetRelations
    span_start1254 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "relation", 1)
            _t2062 = 0
        else
            if match_lookahead_literal(parser, "inserts", 1)
                _t2063 = 1
            else
                _t2063 = 0
            end
            _t2062 = _t2063
        end
        _t2061 = _t2062
    else
        _t2061 = 0
    end
    prediction1250 = _t2061
    if prediction1250 == 1
        _t2065 = parse_cdc_inserts(parser)
        cdc_inserts1252 = _t2065
        _t2066 = parse_cdc_deletes(parser)
        cdc_deletes1253 = _t2066
        _t2067 = construct_cdc_relations(parser, cdc_inserts1252, cdc_deletes1253)
        _t2064 = _t2067
    else
        if prediction1250 == 0
            _t2069 = parse_non_cdc_relations(parser)
            non_cdc_relations1251 = _t2069
            _t2070 = construct_non_cdc_relations(parser, non_cdc_relations1251)
            _t2068 = _t2070
        else
            throw(ParseError("Unexpected token in relation_body" * ": " * string(lookahead(parser, 0))))
        end
        _t2064 = _t2068
    end
    result1255 = _t2064
    record_span!(parser, span_start1254, "TargetRelations")
    return result1255
end

function parse_non_cdc_relations(parser::ParserState)::Vector{Proto.TargetRelation}
    xs1256 = Proto.TargetRelation[]
    cond1257 = match_lookahead_literal(parser, "(", 0)
    while cond1257
        _t2071 = parse_target_relation(parser)
        item1258 = _t2071
        push!(xs1256, item1258)
        cond1257 = match_lookahead_literal(parser, "(", 0)
    end
    return xs1256
end

function parse_target_relation(parser::ParserState)::Proto.TargetRelation
    span_start1264 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relation")
    _t2072 = parse_relation_id(parser)
    relation_id1259 = _t2072
    xs1260 = Proto.NamedColumn[]
    cond1261 = match_lookahead_literal(parser, "(", 0)
    while cond1261
        _t2073 = parse_named_column(parser)
        item1262 = _t2073
        push!(xs1260, item1262)
        cond1261 = match_lookahead_literal(parser, "(", 0)
    end
    named_columns1263 = xs1260
    consume_literal!(parser, ")")
    _t2074 = Proto.TargetRelation(target_id=relation_id1259, values=named_columns1263)
    result1265 = _t2074
    record_span!(parser, span_start1264, "TargetRelation")
    return result1265
end

function parse_cdc_inserts(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "inserts")
    xs1266 = Proto.TargetRelation[]
    cond1267 = match_lookahead_literal(parser, "(", 0)
    while cond1267
        _t2075 = parse_target_relation(parser)
        item1268 = _t2075
        push!(xs1266, item1268)
        cond1267 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1269 = xs1266
    consume_literal!(parser, ")")
    return target_relations1269
end

function parse_cdc_deletes(parser::ParserState)::Vector{Proto.TargetRelation}
    consume_literal!(parser, "(")
    consume_literal!(parser, "deletes")
    xs1270 = Proto.TargetRelation[]
    cond1271 = match_lookahead_literal(parser, "(", 0)
    while cond1271
        _t2076 = parse_target_relation(parser)
        item1272 = _t2076
        push!(xs1270, item1272)
        cond1271 = match_lookahead_literal(parser, "(", 0)
    end
    target_relations1273 = xs1270
    consume_literal!(parser, ")")
    return target_relations1273
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1274 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1274
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1281 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t2077 = parse_iceberg_locator(parser)
    iceberg_locator1275 = _t2077
    _t2078 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1276 = _t2078
    _t2079 = parse_gnf_columns(parser)
    gnf_columns1277 = _t2079
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t2081 = parse_iceberg_from_snapshot(parser)
        _t2080 = _t2081
    else
        _t2080 = nothing
    end
    iceberg_from_snapshot1278 = _t2080
    if match_lookahead_literal(parser, "(", 0)
        _t2083 = parse_iceberg_to_snapshot(parser)
        _t2082 = _t2083
    else
        _t2082 = nothing
    end
    iceberg_to_snapshot1279 = _t2082
    _t2084 = parse_boolean_value(parser)
    boolean_value1280 = _t2084
    consume_literal!(parser, ")")
    _t2085 = construct_iceberg_data(parser, iceberg_locator1275, iceberg_catalog_config1276, gnf_columns1277, iceberg_from_snapshot1278, iceberg_to_snapshot1279, boolean_value1280)
    result1282 = _t2085
    record_span!(parser, span_start1281, "IcebergData")
    return result1282
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1286 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t2086 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1283 = _t2086
    _t2087 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1284 = _t2087
    _t2088 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1285 = _t2088
    consume_literal!(parser, ")")
    _t2089 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1283, namespace=iceberg_locator_namespace1284, warehouse=iceberg_locator_warehouse1285)
    result1287 = _t2089
    record_span!(parser, span_start1286, "IcebergLocator")
    return result1287
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1288 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1288
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1289 = String[]
    cond1290 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1290
        item1291 = consume_terminal!(parser, "STRING")
        push!(xs1289, item1291)
        cond1290 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1292 = xs1289
    consume_literal!(parser, ")")
    return strings1292
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1293 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1293
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1298 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t2090 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1294 = _t2090
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t2092 = parse_iceberg_catalog_config_scope(parser)
        _t2091 = _t2092
    else
        _t2091 = nothing
    end
    iceberg_catalog_config_scope1295 = _t2091
    _t2093 = parse_iceberg_properties(parser)
    iceberg_properties1296 = _t2093
    _t2094 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1297 = _t2094
    consume_literal!(parser, ")")
    _t2095 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1294, iceberg_catalog_config_scope1295, iceberg_properties1296, iceberg_auth_properties1297)
    result1299 = _t2095
    record_span!(parser, span_start1298, "IcebergCatalogConfig")
    return result1299
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1300 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1300
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1301 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1301
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1302 = Tuple{String, String}[]
    cond1303 = match_lookahead_literal(parser, "(", 0)
    while cond1303
        _t2096 = parse_iceberg_property_entry(parser)
        item1304 = _t2096
        push!(xs1302, item1304)
        cond1303 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1305 = xs1302
    consume_literal!(parser, ")")
    return iceberg_property_entrys1305
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1306 = consume_terminal!(parser, "STRING")
    string_31307 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1306, string_31307,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1308 = Tuple{String, String}[]
    cond1309 = match_lookahead_literal(parser, "(", 0)
    while cond1309
        _t2097 = parse_iceberg_masked_property_entry(parser)
        item1310 = _t2097
        push!(xs1308, item1310)
        cond1309 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1311 = xs1308
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1311
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1312 = consume_terminal!(parser, "STRING")
    string_31313 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1312, string_31313,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1314 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1314
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1315 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1315
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1317 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2098 = parse_fragment_id(parser)
    fragment_id1316 = _t2098
    consume_literal!(parser, ")")
    _t2099 = Proto.Undefine(fragment_id=fragment_id1316)
    result1318 = _t2099
    record_span!(parser, span_start1317, "Undefine")
    return result1318
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1323 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1319 = Proto.RelationId[]
    cond1320 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1320
        _t2100 = parse_relation_id(parser)
        item1321 = _t2100
        push!(xs1319, item1321)
        cond1320 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1322 = xs1319
    consume_literal!(parser, ")")
    _t2101 = Proto.Context(relations=relation_ids1322)
    result1324 = _t2101
    record_span!(parser, span_start1323, "Context")
    return result1324
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1330 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2102 = parse_edb_path(parser)
    edb_path1325 = _t2102
    xs1326 = Proto.SnapshotMapping[]
    cond1327 = match_lookahead_literal(parser, "[", 0)
    while cond1327
        _t2103 = parse_snapshot_mapping(parser)
        item1328 = _t2103
        push!(xs1326, item1328)
        cond1327 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1329 = xs1326
    consume_literal!(parser, ")")
    _t2104 = Proto.Snapshot(mappings=snapshot_mappings1329, prefix=edb_path1325)
    result1331 = _t2104
    record_span!(parser, span_start1330, "Snapshot")
    return result1331
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1334 = span_start(parser)
    _t2105 = parse_edb_path(parser)
    edb_path1332 = _t2105
    _t2106 = parse_relation_id(parser)
    relation_id1333 = _t2106
    _t2107 = Proto.SnapshotMapping(destination_path=edb_path1332, source_relation=relation_id1333)
    result1335 = _t2107
    record_span!(parser, span_start1334, "SnapshotMapping")
    return result1335
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1336 = Proto.Read[]
    cond1337 = match_lookahead_literal(parser, "(", 0)
    while cond1337
        _t2108 = parse_read(parser)
        item1338 = _t2108
        push!(xs1336, item1338)
        cond1337 = match_lookahead_literal(parser, "(", 0)
    end
    reads1339 = xs1336
    consume_literal!(parser, ")")
    return reads1339
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1346 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2110 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2111 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2112 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2113 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2114 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2115 = 3
                            else
                                _t2115 = -1
                            end
                            _t2114 = _t2115
                        end
                        _t2113 = _t2114
                    end
                    _t2112 = _t2113
                end
                _t2111 = _t2112
            end
            _t2110 = _t2111
        end
        _t2109 = _t2110
    else
        _t2109 = -1
    end
    prediction1340 = _t2109
    if prediction1340 == 4
        _t2117 = parse_export(parser)
        export1345 = _t2117
        _t2118 = Proto.Read(read_type=OneOf(:var"#export", export1345))
        _t2116 = _t2118
    else
        if prediction1340 == 3
            _t2120 = parse_abort(parser)
            abort1344 = _t2120
            _t2121 = Proto.Read(read_type=OneOf(:abort, abort1344))
            _t2119 = _t2121
        else
            if prediction1340 == 2
                _t2123 = parse_what_if(parser)
                what_if1343 = _t2123
                _t2124 = Proto.Read(read_type=OneOf(:what_if, what_if1343))
                _t2122 = _t2124
            else
                if prediction1340 == 1
                    _t2126 = parse_output(parser)
                    output1342 = _t2126
                    _t2127 = Proto.Read(read_type=OneOf(:output, output1342))
                    _t2125 = _t2127
                else
                    if prediction1340 == 0
                        _t2129 = parse_demand(parser)
                        demand1341 = _t2129
                        _t2130 = Proto.Read(read_type=OneOf(:demand, demand1341))
                        _t2128 = _t2130
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2125 = _t2128
                end
                _t2122 = _t2125
            end
            _t2119 = _t2122
        end
        _t2116 = _t2119
    end
    result1347 = _t2116
    record_span!(parser, span_start1346, "Read")
    return result1347
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1349 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2131 = parse_relation_id(parser)
    relation_id1348 = _t2131
    consume_literal!(parser, ")")
    _t2132 = Proto.Demand(relation_id=relation_id1348)
    result1350 = _t2132
    record_span!(parser, span_start1349, "Demand")
    return result1350
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1353 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2133 = parse_name(parser)
    name1351 = _t2133
    _t2134 = parse_relation_id(parser)
    relation_id1352 = _t2134
    consume_literal!(parser, ")")
    _t2135 = Proto.Output(name=name1351, relation_id=relation_id1352)
    result1354 = _t2135
    record_span!(parser, span_start1353, "Output")
    return result1354
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1357 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2136 = parse_name(parser)
    name1355 = _t2136
    _t2137 = parse_epoch(parser)
    epoch1356 = _t2137
    consume_literal!(parser, ")")
    _t2138 = Proto.WhatIf(branch=name1355, epoch=epoch1356)
    result1358 = _t2138
    record_span!(parser, span_start1357, "WhatIf")
    return result1358
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1361 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2140 = parse_name(parser)
        _t2139 = _t2140
    else
        _t2139 = nothing
    end
    name1359 = _t2139
    _t2141 = parse_relation_id(parser)
    relation_id1360 = _t2141
    consume_literal!(parser, ")")
    _t2142 = Proto.Abort(name=(!isnothing(name1359) ? name1359 : "abort"), relation_id=relation_id1360)
    result1362 = _t2142
    record_span!(parser, span_start1361, "Abort")
    return result1362
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1366 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2144 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2145 = 0
            else
                _t2145 = -1
            end
            _t2144 = _t2145
        end
        _t2143 = _t2144
    else
        _t2143 = -1
    end
    prediction1363 = _t2143
    if prediction1363 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2147 = parse_export_iceberg_config(parser)
        export_iceberg_config1365 = _t2147
        consume_literal!(parser, ")")
        _t2148 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1365))
        _t2146 = _t2148
    else
        if prediction1363 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2150 = parse_export_csv_config(parser)
            export_csv_config1364 = _t2150
            consume_literal!(parser, ")")
            _t2151 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1364))
            _t2149 = _t2151
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2146 = _t2149
    end
    result1367 = _t2146
    record_span!(parser, span_start1366, "Export")
    return result1367
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1375 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2153 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2154 = 1
            else
                _t2154 = -1
            end
            _t2153 = _t2154
        end
        _t2152 = _t2153
    else
        _t2152 = -1
    end
    prediction1368 = _t2152
    if prediction1368 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2156 = parse_export_csv_path(parser)
        export_csv_path1372 = _t2156
        _t2157 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1373 = _t2157
        _t2158 = parse_config_dict(parser)
        config_dict1374 = _t2158
        consume_literal!(parser, ")")
        _t2159 = construct_export_csv_config(parser, export_csv_path1372, export_csv_columns_list1373, config_dict1374)
        _t2155 = _t2159
    else
        if prediction1368 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2161 = parse_export_csv_path(parser)
            export_csv_path1369 = _t2161
            _t2162 = parse_export_csv_source(parser)
            export_csv_source1370 = _t2162
            _t2163 = parse_csv_config(parser)
            csv_config1371 = _t2163
            consume_literal!(parser, ")")
            _t2164 = construct_export_csv_config_with_source(parser, export_csv_path1369, export_csv_source1370, csv_config1371)
            _t2160 = _t2164
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2155 = _t2160
    end
    result1376 = _t2155
    record_span!(parser, span_start1375, "ExportCSVConfig")
    return result1376
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1377 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1377
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1384 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2166 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2167 = 0
            else
                _t2167 = -1
            end
            _t2166 = _t2167
        end
        _t2165 = _t2166
    else
        _t2165 = -1
    end
    prediction1378 = _t2165
    if prediction1378 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2169 = parse_relation_id(parser)
        relation_id1383 = _t2169
        consume_literal!(parser, ")")
        _t2170 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1383))
        _t2168 = _t2170
    else
        if prediction1378 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1379 = Proto.ExportCSVColumn[]
            cond1380 = match_lookahead_literal(parser, "(", 0)
            while cond1380
                _t2172 = parse_export_csv_column(parser)
                item1381 = _t2172
                push!(xs1379, item1381)
                cond1380 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1382 = xs1379
            consume_literal!(parser, ")")
            _t2173 = Proto.ExportCSVColumns(columns=export_csv_columns1382)
            _t2174 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2173))
            _t2171 = _t2174
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2168 = _t2171
    end
    result1385 = _t2168
    record_span!(parser, span_start1384, "ExportCSVSource")
    return result1385
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1388 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1386 = consume_terminal!(parser, "STRING")
    _t2175 = parse_relation_id(parser)
    relation_id1387 = _t2175
    consume_literal!(parser, ")")
    _t2176 = Proto.ExportCSVColumn(column_name=string1386, column_data=relation_id1387)
    result1389 = _t2176
    record_span!(parser, span_start1388, "ExportCSVColumn")
    return result1389
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1390 = Proto.ExportCSVColumn[]
    cond1391 = match_lookahead_literal(parser, "(", 0)
    while cond1391
        _t2177 = parse_export_csv_column(parser)
        item1392 = _t2177
        push!(xs1390, item1392)
        cond1391 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1393 = xs1390
    consume_literal!(parser, ")")
    return export_csv_columns1393
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1399 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2178 = parse_iceberg_locator(parser)
    iceberg_locator1394 = _t2178
    _t2179 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1395 = _t2179
    _t2180 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1396 = _t2180
    _t2181 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1397 = _t2181
    if match_lookahead_literal(parser, "{", 0)
        _t2183 = parse_config_dict(parser)
        _t2182 = _t2183
    else
        _t2182 = nothing
    end
    config_dict1398 = _t2182
    consume_literal!(parser, ")")
    _t2184 = construct_export_iceberg_config_full(parser, iceberg_locator1394, iceberg_catalog_config1395, export_iceberg_table_def1396, iceberg_table_properties1397, config_dict1398)
    result1400 = _t2184
    record_span!(parser, span_start1399, "ExportIcebergConfig")
    return result1400
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1402 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2185 = parse_relation_id(parser)
    relation_id1401 = _t2185
    consume_literal!(parser, ")")
    result1403 = relation_id1401
    record_span!(parser, span_start1402, "RelationId")
    return result1403
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1404 = Tuple{String, String}[]
    cond1405 = match_lookahead_literal(parser, "(", 0)
    while cond1405
        _t2186 = parse_iceberg_property_entry(parser)
        item1406 = _t2186
        push!(xs1404, item1406)
        cond1405 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1407 = xs1404
    consume_literal!(parser, ")")
    return iceberg_property_entrys1407
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
