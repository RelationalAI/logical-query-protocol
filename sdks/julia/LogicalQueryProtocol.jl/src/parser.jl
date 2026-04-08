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
        _t2095 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2096 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2097 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2098 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2099 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2100 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2101 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2102 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2103 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2104 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2104
    _t2105 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2105
    _t2106 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2106
    _t2107 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2107
    _t2108 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2108
    _t2109 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2109
    _t2110 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2110
    _t2111 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2111
    _t2112 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2112
    _t2113 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2113
    _t2114 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2114
    _t2115 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2115
    _t2116 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2116
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2117 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2117
    _t2118 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2118
    _t2119 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2119
    _t2120 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2120
    _t2121 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2121
    _t2122 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2122
    _t2123 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2123
    _t2124 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2124
    _t2125 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2125
    _t2126 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2126
    _t2127 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2127
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2128 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2128
    _t2129 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2129
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
    _t2130 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2130
    _t2131 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2131
    _t2132 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2132
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2133 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2133
    _t2134 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2134
    _t2135 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2135
    _t2136 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2136
    _t2137 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2137
    _t2138 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2138
    _t2139 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2139
    _t2140 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2140
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2141 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2141
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2142 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2142
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2143 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2143
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, columns::Vector{Proto.ExportColumn}, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2144 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2144
    _t2145 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2145
    _t2146 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2146
    table_props = Dict(table_property_pairs)
    _t2147 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2147
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start678 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1345 = parse_configure(parser)
        _t1344 = _t1345
    else
        _t1344 = nothing
    end
    configure672 = _t1344
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1347 = parse_sync(parser)
        _t1346 = _t1347
    else
        _t1346 = nothing
    end
    sync673 = _t1346
    xs674 = Proto.Epoch[]
    cond675 = match_lookahead_literal(parser, "(", 0)
    while cond675
        _t1348 = parse_epoch(parser)
        item676 = _t1348
        push!(xs674, item676)
        cond675 = match_lookahead_literal(parser, "(", 0)
    end
    epochs677 = xs674
    consume_literal!(parser, ")")
    _t1349 = default_configure(parser)
    _t1350 = Proto.Transaction(epochs=epochs677, configure=(!isnothing(configure672) ? configure672 : _t1349), sync=sync673)
    result679 = _t1350
    record_span!(parser, span_start678, "Transaction")
    return result679
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start681 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1351 = parse_config_dict(parser)
    config_dict680 = _t1351
    consume_literal!(parser, ")")
    _t1352 = construct_configure(parser, config_dict680)
    result682 = _t1352
    record_span!(parser, span_start681, "Configure")
    return result682
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs683 = Tuple{String, Proto.Value}[]
    cond684 = match_lookahead_literal(parser, ":", 0)
    while cond684
        _t1353 = parse_config_key_value(parser)
        item685 = _t1353
        push!(xs683, item685)
        cond684 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values686 = xs683
    consume_literal!(parser, "}")
    return config_key_values686
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol687 = consume_terminal!(parser, "SYMBOL")
    _t1354 = parse_raw_value(parser)
    raw_value688 = _t1354
    return (symbol687, raw_value688,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start702 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1355 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1356 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1357 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1359 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1360 = 0
                        else
                            _t1360 = -1
                        end
                        _t1359 = _t1360
                    end
                    _t1358 = _t1359
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1361 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1362 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1363 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1364 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1365 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1366 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1367 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1368 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1369 = 10
                                                    else
                                                        _t1369 = -1
                                                    end
                                                    _t1368 = _t1369
                                                end
                                                _t1367 = _t1368
                                            end
                                            _t1366 = _t1367
                                        end
                                        _t1365 = _t1366
                                    end
                                    _t1364 = _t1365
                                end
                                _t1363 = _t1364
                            end
                            _t1362 = _t1363
                        end
                        _t1361 = _t1362
                    end
                    _t1358 = _t1361
                end
                _t1357 = _t1358
            end
            _t1356 = _t1357
        end
        _t1355 = _t1356
    end
    prediction689 = _t1355
    if prediction689 == 12
        _t1371 = parse_boolean_value(parser)
        boolean_value701 = _t1371
        _t1372 = Proto.Value(value=OneOf(:boolean_value, boolean_value701))
        _t1370 = _t1372
    else
        if prediction689 == 11
            consume_literal!(parser, "missing")
            _t1374 = Proto.MissingValue()
            _t1375 = Proto.Value(value=OneOf(:missing_value, _t1374))
            _t1373 = _t1375
        else
            if prediction689 == 10
                decimal700 = consume_terminal!(parser, "DECIMAL")
                _t1377 = Proto.Value(value=OneOf(:decimal_value, decimal700))
                _t1376 = _t1377
            else
                if prediction689 == 9
                    int128699 = consume_terminal!(parser, "INT128")
                    _t1379 = Proto.Value(value=OneOf(:int128_value, int128699))
                    _t1378 = _t1379
                else
                    if prediction689 == 8
                        uint128698 = consume_terminal!(parser, "UINT128")
                        _t1381 = Proto.Value(value=OneOf(:uint128_value, uint128698))
                        _t1380 = _t1381
                    else
                        if prediction689 == 7
                            uint32697 = consume_terminal!(parser, "UINT32")
                            _t1383 = Proto.Value(value=OneOf(:uint32_value, uint32697))
                            _t1382 = _t1383
                        else
                            if prediction689 == 6
                                float696 = consume_terminal!(parser, "FLOAT")
                                _t1385 = Proto.Value(value=OneOf(:float_value, float696))
                                _t1384 = _t1385
                            else
                                if prediction689 == 5
                                    float32695 = consume_terminal!(parser, "FLOAT32")
                                    _t1387 = Proto.Value(value=OneOf(:float32_value, float32695))
                                    _t1386 = _t1387
                                else
                                    if prediction689 == 4
                                        int694 = consume_terminal!(parser, "INT")
                                        _t1389 = Proto.Value(value=OneOf(:int_value, int694))
                                        _t1388 = _t1389
                                    else
                                        if prediction689 == 3
                                            int32693 = consume_terminal!(parser, "INT32")
                                            _t1391 = Proto.Value(value=OneOf(:int32_value, int32693))
                                            _t1390 = _t1391
                                        else
                                            if prediction689 == 2
                                                string692 = consume_terminal!(parser, "STRING")
                                                _t1393 = Proto.Value(value=OneOf(:string_value, string692))
                                                _t1392 = _t1393
                                            else
                                                if prediction689 == 1
                                                    _t1395 = parse_raw_datetime(parser)
                                                    raw_datetime691 = _t1395
                                                    _t1396 = Proto.Value(value=OneOf(:datetime_value, raw_datetime691))
                                                    _t1394 = _t1396
                                                else
                                                    if prediction689 == 0
                                                        _t1398 = parse_raw_date(parser)
                                                        raw_date690 = _t1398
                                                        _t1399 = Proto.Value(value=OneOf(:date_value, raw_date690))
                                                        _t1397 = _t1399
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1394 = _t1397
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
                        _t1380 = _t1382
                    end
                    _t1378 = _t1380
                end
                _t1376 = _t1378
            end
            _t1373 = _t1376
        end
        _t1370 = _t1373
    end
    result703 = _t1370
    record_span!(parser, span_start702, "Value")
    return result703
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start707 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int704 = consume_terminal!(parser, "INT")
    int_3705 = consume_terminal!(parser, "INT")
    int_4706 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1400 = Proto.DateValue(year=Int32(int704), month=Int32(int_3705), day=Int32(int_4706))
    result708 = _t1400
    record_span!(parser, span_start707, "DateValue")
    return result708
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start716 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int709 = consume_terminal!(parser, "INT")
    int_3710 = consume_terminal!(parser, "INT")
    int_4711 = consume_terminal!(parser, "INT")
    int_5712 = consume_terminal!(parser, "INT")
    int_6713 = consume_terminal!(parser, "INT")
    int_7714 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1401 = consume_terminal!(parser, "INT")
    else
        _t1401 = nothing
    end
    int_8715 = _t1401
    consume_literal!(parser, ")")
    _t1402 = Proto.DateTimeValue(year=Int32(int709), month=Int32(int_3710), day=Int32(int_4711), hour=Int32(int_5712), minute=Int32(int_6713), second=Int32(int_7714), microsecond=Int32((!isnothing(int_8715) ? int_8715 : 0)))
    result717 = _t1402
    record_span!(parser, span_start716, "DateTimeValue")
    return result717
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1403 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1404 = 1
        else
            _t1404 = -1
        end
        _t1403 = _t1404
    end
    prediction718 = _t1403
    if prediction718 == 1
        consume_literal!(parser, "false")
        _t1405 = false
    else
        if prediction718 == 0
            consume_literal!(parser, "true")
            _t1406 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1405 = _t1406
    end
    return _t1405
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start723 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs719 = Proto.FragmentId[]
    cond720 = match_lookahead_literal(parser, ":", 0)
    while cond720
        _t1407 = parse_fragment_id(parser)
        item721 = _t1407
        push!(xs719, item721)
        cond720 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids722 = xs719
    consume_literal!(parser, ")")
    _t1408 = Proto.Sync(fragments=fragment_ids722)
    result724 = _t1408
    record_span!(parser, span_start723, "Sync")
    return result724
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start726 = span_start(parser)
    consume_literal!(parser, ":")
    symbol725 = consume_terminal!(parser, "SYMBOL")
    result727 = Proto.FragmentId(Vector{UInt8}(symbol725))
    record_span!(parser, span_start726, "FragmentId")
    return result727
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start730 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1410 = parse_epoch_writes(parser)
        _t1409 = _t1410
    else
        _t1409 = nothing
    end
    epoch_writes728 = _t1409
    if match_lookahead_literal(parser, "(", 0)
        _t1412 = parse_epoch_reads(parser)
        _t1411 = _t1412
    else
        _t1411 = nothing
    end
    epoch_reads729 = _t1411
    consume_literal!(parser, ")")
    _t1413 = Proto.Epoch(writes=(!isnothing(epoch_writes728) ? epoch_writes728 : Proto.Write[]), reads=(!isnothing(epoch_reads729) ? epoch_reads729 : Proto.Read[]))
    result731 = _t1413
    record_span!(parser, span_start730, "Epoch")
    return result731
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs732 = Proto.Write[]
    cond733 = match_lookahead_literal(parser, "(", 0)
    while cond733
        _t1414 = parse_write(parser)
        item734 = _t1414
        push!(xs732, item734)
        cond733 = match_lookahead_literal(parser, "(", 0)
    end
    writes735 = xs732
    consume_literal!(parser, ")")
    return writes735
end

function parse_write(parser::ParserState)::Proto.Write
    span_start741 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1416 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1417 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1418 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1419 = 2
                    else
                        _t1419 = -1
                    end
                    _t1418 = _t1419
                end
                _t1417 = _t1418
            end
            _t1416 = _t1417
        end
        _t1415 = _t1416
    else
        _t1415 = -1
    end
    prediction736 = _t1415
    if prediction736 == 3
        _t1421 = parse_snapshot(parser)
        snapshot740 = _t1421
        _t1422 = Proto.Write(write_type=OneOf(:snapshot, snapshot740))
        _t1420 = _t1422
    else
        if prediction736 == 2
            _t1424 = parse_context(parser)
            context739 = _t1424
            _t1425 = Proto.Write(write_type=OneOf(:context, context739))
            _t1423 = _t1425
        else
            if prediction736 == 1
                _t1427 = parse_undefine(parser)
                undefine738 = _t1427
                _t1428 = Proto.Write(write_type=OneOf(:undefine, undefine738))
                _t1426 = _t1428
            else
                if prediction736 == 0
                    _t1430 = parse_define(parser)
                    define737 = _t1430
                    _t1431 = Proto.Write(write_type=OneOf(:define, define737))
                    _t1429 = _t1431
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1426 = _t1429
            end
            _t1423 = _t1426
        end
        _t1420 = _t1423
    end
    result742 = _t1420
    record_span!(parser, span_start741, "Write")
    return result742
end

function parse_define(parser::ParserState)::Proto.Define
    span_start744 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1432 = parse_fragment(parser)
    fragment743 = _t1432
    consume_literal!(parser, ")")
    _t1433 = Proto.Define(fragment=fragment743)
    result745 = _t1433
    record_span!(parser, span_start744, "Define")
    return result745
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start751 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1434 = parse_new_fragment_id(parser)
    new_fragment_id746 = _t1434
    xs747 = Proto.Declaration[]
    cond748 = match_lookahead_literal(parser, "(", 0)
    while cond748
        _t1435 = parse_declaration(parser)
        item749 = _t1435
        push!(xs747, item749)
        cond748 = match_lookahead_literal(parser, "(", 0)
    end
    declarations750 = xs747
    consume_literal!(parser, ")")
    result752 = construct_fragment(parser, new_fragment_id746, declarations750)
    record_span!(parser, span_start751, "Fragment")
    return result752
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start754 = span_start(parser)
    _t1436 = parse_fragment_id(parser)
    fragment_id753 = _t1436
    start_fragment!(parser, fragment_id753)
    result755 = fragment_id753
    record_span!(parser, span_start754, "FragmentId")
    return result755
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start761 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1438 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1439 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1440 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1441 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1442 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1443 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1444 = 1
                                else
                                    _t1444 = -1
                                end
                                _t1443 = _t1444
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
    else
        _t1437 = -1
    end
    prediction756 = _t1437
    if prediction756 == 3
        _t1446 = parse_data(parser)
        data760 = _t1446
        _t1447 = Proto.Declaration(declaration_type=OneOf(:data, data760))
        _t1445 = _t1447
    else
        if prediction756 == 2
            _t1449 = parse_constraint(parser)
            constraint759 = _t1449
            _t1450 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint759))
            _t1448 = _t1450
        else
            if prediction756 == 1
                _t1452 = parse_algorithm(parser)
                algorithm758 = _t1452
                _t1453 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm758))
                _t1451 = _t1453
            else
                if prediction756 == 0
                    _t1455 = parse_def(parser)
                    def757 = _t1455
                    _t1456 = Proto.Declaration(declaration_type=OneOf(:def, def757))
                    _t1454 = _t1456
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1451 = _t1454
            end
            _t1448 = _t1451
        end
        _t1445 = _t1448
    end
    result762 = _t1445
    record_span!(parser, span_start761, "Declaration")
    return result762
end

function parse_def(parser::ParserState)::Proto.Def
    span_start766 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1457 = parse_relation_id(parser)
    relation_id763 = _t1457
    _t1458 = parse_abstraction(parser)
    abstraction764 = _t1458
    if match_lookahead_literal(parser, "(", 0)
        _t1460 = parse_attrs(parser)
        _t1459 = _t1460
    else
        _t1459 = nothing
    end
    attrs765 = _t1459
    consume_literal!(parser, ")")
    _t1461 = Proto.Def(name=relation_id763, body=abstraction764, attrs=(!isnothing(attrs765) ? attrs765 : Proto.Attribute[]))
    result767 = _t1461
    record_span!(parser, span_start766, "Def")
    return result767
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start771 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1462 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1463 = 1
        else
            _t1463 = -1
        end
        _t1462 = _t1463
    end
    prediction768 = _t1462
    if prediction768 == 1
        uint128770 = consume_terminal!(parser, "UINT128")
        _t1464 = Proto.RelationId(uint128770.low, uint128770.high)
    else
        if prediction768 == 0
            consume_literal!(parser, ":")
            symbol769 = consume_terminal!(parser, "SYMBOL")
            _t1465 = relation_id_from_string(parser, symbol769)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1464 = _t1465
    end
    result772 = _t1464
    record_span!(parser, span_start771, "RelationId")
    return result772
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start775 = span_start(parser)
    consume_literal!(parser, "(")
    _t1466 = parse_bindings(parser)
    bindings773 = _t1466
    _t1467 = parse_formula(parser)
    formula774 = _t1467
    consume_literal!(parser, ")")
    _t1468 = Proto.Abstraction(vars=vcat(bindings773[1], !isnothing(bindings773[2]) ? bindings773[2] : []), value=formula774)
    result776 = _t1468
    record_span!(parser, span_start775, "Abstraction")
    return result776
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs777 = Proto.Binding[]
    cond778 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond778
        _t1469 = parse_binding(parser)
        item779 = _t1469
        push!(xs777, item779)
        cond778 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings780 = xs777
    if match_lookahead_literal(parser, "|", 0)
        _t1471 = parse_value_bindings(parser)
        _t1470 = _t1471
    else
        _t1470 = nothing
    end
    value_bindings781 = _t1470
    consume_literal!(parser, "]")
    return (bindings780, (!isnothing(value_bindings781) ? value_bindings781 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start784 = span_start(parser)
    symbol782 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1472 = parse_type(parser)
    type783 = _t1472
    _t1473 = Proto.Var(name=symbol782)
    _t1474 = Proto.Binding(var=_t1473, var"#type"=type783)
    result785 = _t1474
    record_span!(parser, span_start784, "Binding")
    return result785
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start801 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1475 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1476 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1477 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1478 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1479 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1480 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1481 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1482 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1483 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1484 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1485 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1486 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1487 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1488 = 9
                                                        else
                                                            _t1488 = -1
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
    prediction786 = _t1475
    if prediction786 == 13
        _t1490 = parse_uint32_type(parser)
        uint32_type800 = _t1490
        _t1491 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type800))
        _t1489 = _t1491
    else
        if prediction786 == 12
            _t1493 = parse_float32_type(parser)
            float32_type799 = _t1493
            _t1494 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type799))
            _t1492 = _t1494
        else
            if prediction786 == 11
                _t1496 = parse_int32_type(parser)
                int32_type798 = _t1496
                _t1497 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type798))
                _t1495 = _t1497
            else
                if prediction786 == 10
                    _t1499 = parse_boolean_type(parser)
                    boolean_type797 = _t1499
                    _t1500 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type797))
                    _t1498 = _t1500
                else
                    if prediction786 == 9
                        _t1502 = parse_decimal_type(parser)
                        decimal_type796 = _t1502
                        _t1503 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type796))
                        _t1501 = _t1503
                    else
                        if prediction786 == 8
                            _t1505 = parse_missing_type(parser)
                            missing_type795 = _t1505
                            _t1506 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type795))
                            _t1504 = _t1506
                        else
                            if prediction786 == 7
                                _t1508 = parse_datetime_type(parser)
                                datetime_type794 = _t1508
                                _t1509 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type794))
                                _t1507 = _t1509
                            else
                                if prediction786 == 6
                                    _t1511 = parse_date_type(parser)
                                    date_type793 = _t1511
                                    _t1512 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type793))
                                    _t1510 = _t1512
                                else
                                    if prediction786 == 5
                                        _t1514 = parse_int128_type(parser)
                                        int128_type792 = _t1514
                                        _t1515 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type792))
                                        _t1513 = _t1515
                                    else
                                        if prediction786 == 4
                                            _t1517 = parse_uint128_type(parser)
                                            uint128_type791 = _t1517
                                            _t1518 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type791))
                                            _t1516 = _t1518
                                        else
                                            if prediction786 == 3
                                                _t1520 = parse_float_type(parser)
                                                float_type790 = _t1520
                                                _t1521 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type790))
                                                _t1519 = _t1521
                                            else
                                                if prediction786 == 2
                                                    _t1523 = parse_int_type(parser)
                                                    int_type789 = _t1523
                                                    _t1524 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type789))
                                                    _t1522 = _t1524
                                                else
                                                    if prediction786 == 1
                                                        _t1526 = parse_string_type(parser)
                                                        string_type788 = _t1526
                                                        _t1527 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type788))
                                                        _t1525 = _t1527
                                                    else
                                                        if prediction786 == 0
                                                            _t1529 = parse_unspecified_type(parser)
                                                            unspecified_type787 = _t1529
                                                            _t1530 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type787))
                                                            _t1528 = _t1530
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
            _t1492 = _t1495
        end
        _t1489 = _t1492
    end
    result802 = _t1489
    record_span!(parser, span_start801, "Type")
    return result802
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start803 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1531 = Proto.UnspecifiedType()
    result804 = _t1531
    record_span!(parser, span_start803, "UnspecifiedType")
    return result804
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start805 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1532 = Proto.StringType()
    result806 = _t1532
    record_span!(parser, span_start805, "StringType")
    return result806
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start807 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1533 = Proto.IntType()
    result808 = _t1533
    record_span!(parser, span_start807, "IntType")
    return result808
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start809 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1534 = Proto.FloatType()
    result810 = _t1534
    record_span!(parser, span_start809, "FloatType")
    return result810
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start811 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1535 = Proto.UInt128Type()
    result812 = _t1535
    record_span!(parser, span_start811, "UInt128Type")
    return result812
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start813 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1536 = Proto.Int128Type()
    result814 = _t1536
    record_span!(parser, span_start813, "Int128Type")
    return result814
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start815 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1537 = Proto.DateType()
    result816 = _t1537
    record_span!(parser, span_start815, "DateType")
    return result816
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start817 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1538 = Proto.DateTimeType()
    result818 = _t1538
    record_span!(parser, span_start817, "DateTimeType")
    return result818
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start819 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1539 = Proto.MissingType()
    result820 = _t1539
    record_span!(parser, span_start819, "MissingType")
    return result820
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start823 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int821 = consume_terminal!(parser, "INT")
    int_3822 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1540 = Proto.DecimalType(precision=Int32(int821), scale=Int32(int_3822))
    result824 = _t1540
    record_span!(parser, span_start823, "DecimalType")
    return result824
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start825 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1541 = Proto.BooleanType()
    result826 = _t1541
    record_span!(parser, span_start825, "BooleanType")
    return result826
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start827 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1542 = Proto.Int32Type()
    result828 = _t1542
    record_span!(parser, span_start827, "Int32Type")
    return result828
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start829 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1543 = Proto.Float32Type()
    result830 = _t1543
    record_span!(parser, span_start829, "Float32Type")
    return result830
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start831 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1544 = Proto.UInt32Type()
    result832 = _t1544
    record_span!(parser, span_start831, "UInt32Type")
    return result832
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs833 = Proto.Binding[]
    cond834 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond834
        _t1545 = parse_binding(parser)
        item835 = _t1545
        push!(xs833, item835)
        cond834 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings836 = xs833
    return bindings836
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start851 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1547 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1548 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1549 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1550 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1551 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1552 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1553 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1554 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1555 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1556 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1557 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1558 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1559 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1560 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1561 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1562 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1563 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1564 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1565 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1566 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1567 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1568 = 10
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
    else
        _t1546 = -1
    end
    prediction837 = _t1546
    if prediction837 == 12
        _t1570 = parse_cast(parser)
        cast850 = _t1570
        _t1571 = Proto.Formula(formula_type=OneOf(:cast, cast850))
        _t1569 = _t1571
    else
        if prediction837 == 11
            _t1573 = parse_rel_atom(parser)
            rel_atom849 = _t1573
            _t1574 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom849))
            _t1572 = _t1574
        else
            if prediction837 == 10
                _t1576 = parse_primitive(parser)
                primitive848 = _t1576
                _t1577 = Proto.Formula(formula_type=OneOf(:primitive, primitive848))
                _t1575 = _t1577
            else
                if prediction837 == 9
                    _t1579 = parse_pragma(parser)
                    pragma847 = _t1579
                    _t1580 = Proto.Formula(formula_type=OneOf(:pragma, pragma847))
                    _t1578 = _t1580
                else
                    if prediction837 == 8
                        _t1582 = parse_atom(parser)
                        atom846 = _t1582
                        _t1583 = Proto.Formula(formula_type=OneOf(:atom, atom846))
                        _t1581 = _t1583
                    else
                        if prediction837 == 7
                            _t1585 = parse_ffi(parser)
                            ffi845 = _t1585
                            _t1586 = Proto.Formula(formula_type=OneOf(:ffi, ffi845))
                            _t1584 = _t1586
                        else
                            if prediction837 == 6
                                _t1588 = parse_not(parser)
                                not844 = _t1588
                                _t1589 = Proto.Formula(formula_type=OneOf(:not, not844))
                                _t1587 = _t1589
                            else
                                if prediction837 == 5
                                    _t1591 = parse_disjunction(parser)
                                    disjunction843 = _t1591
                                    _t1592 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction843))
                                    _t1590 = _t1592
                                else
                                    if prediction837 == 4
                                        _t1594 = parse_conjunction(parser)
                                        conjunction842 = _t1594
                                        _t1595 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction842))
                                        _t1593 = _t1595
                                    else
                                        if prediction837 == 3
                                            _t1597 = parse_reduce(parser)
                                            reduce841 = _t1597
                                            _t1598 = Proto.Formula(formula_type=OneOf(:reduce, reduce841))
                                            _t1596 = _t1598
                                        else
                                            if prediction837 == 2
                                                _t1600 = parse_exists(parser)
                                                exists840 = _t1600
                                                _t1601 = Proto.Formula(formula_type=OneOf(:exists, exists840))
                                                _t1599 = _t1601
                                            else
                                                if prediction837 == 1
                                                    _t1603 = parse_false(parser)
                                                    false839 = _t1603
                                                    _t1604 = Proto.Formula(formula_type=OneOf(:disjunction, false839))
                                                    _t1602 = _t1604
                                                else
                                                    if prediction837 == 0
                                                        _t1606 = parse_true(parser)
                                                        true838 = _t1606
                                                        _t1607 = Proto.Formula(formula_type=OneOf(:conjunction, true838))
                                                        _t1605 = _t1607
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
    result852 = _t1569
    record_span!(parser, span_start851, "Formula")
    return result852
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start853 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1608 = Proto.Conjunction(args=Proto.Formula[])
    result854 = _t1608
    record_span!(parser, span_start853, "Conjunction")
    return result854
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start855 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1609 = Proto.Disjunction(args=Proto.Formula[])
    result856 = _t1609
    record_span!(parser, span_start855, "Disjunction")
    return result856
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start859 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1610 = parse_bindings(parser)
    bindings857 = _t1610
    _t1611 = parse_formula(parser)
    formula858 = _t1611
    consume_literal!(parser, ")")
    _t1612 = Proto.Abstraction(vars=vcat(bindings857[1], !isnothing(bindings857[2]) ? bindings857[2] : []), value=formula858)
    _t1613 = Proto.Exists(body=_t1612)
    result860 = _t1613
    record_span!(parser, span_start859, "Exists")
    return result860
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start864 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1614 = parse_abstraction(parser)
    abstraction861 = _t1614
    _t1615 = parse_abstraction(parser)
    abstraction_3862 = _t1615
    _t1616 = parse_terms(parser)
    terms863 = _t1616
    consume_literal!(parser, ")")
    _t1617 = Proto.Reduce(op=abstraction861, body=abstraction_3862, terms=terms863)
    result865 = _t1617
    record_span!(parser, span_start864, "Reduce")
    return result865
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs866 = Proto.Term[]
    cond867 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond867
        _t1618 = parse_term(parser)
        item868 = _t1618
        push!(xs866, item868)
        cond867 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms869 = xs866
    consume_literal!(parser, ")")
    return terms869
end

function parse_term(parser::ParserState)::Proto.Term
    span_start873 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1619 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1620 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1621 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1622 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1623 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1624 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1625 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1626 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1627 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1628 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1629 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1630 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1631 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1632 = 1
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
    prediction870 = _t1619
    if prediction870 == 1
        _t1634 = parse_value(parser)
        value872 = _t1634
        _t1635 = Proto.Term(term_type=OneOf(:constant, value872))
        _t1633 = _t1635
    else
        if prediction870 == 0
            _t1637 = parse_var(parser)
            var871 = _t1637
            _t1638 = Proto.Term(term_type=OneOf(:var, var871))
            _t1636 = _t1638
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1633 = _t1636
    end
    result874 = _t1633
    record_span!(parser, span_start873, "Term")
    return result874
end

function parse_var(parser::ParserState)::Proto.Var
    span_start876 = span_start(parser)
    symbol875 = consume_terminal!(parser, "SYMBOL")
    _t1639 = Proto.Var(name=symbol875)
    result877 = _t1639
    record_span!(parser, span_start876, "Var")
    return result877
end

function parse_value(parser::ParserState)::Proto.Value
    span_start891 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1640 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1641 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1642 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1644 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1645 = 0
                        else
                            _t1645 = -1
                        end
                        _t1644 = _t1645
                    end
                    _t1643 = _t1644
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1646 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1647 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1648 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1649 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1650 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1651 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1652 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1653 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1654 = 10
                                                    else
                                                        _t1654 = -1
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
                    _t1643 = _t1646
                end
                _t1642 = _t1643
            end
            _t1641 = _t1642
        end
        _t1640 = _t1641
    end
    prediction878 = _t1640
    if prediction878 == 12
        _t1656 = parse_boolean_value(parser)
        boolean_value890 = _t1656
        _t1657 = Proto.Value(value=OneOf(:boolean_value, boolean_value890))
        _t1655 = _t1657
    else
        if prediction878 == 11
            consume_literal!(parser, "missing")
            _t1659 = Proto.MissingValue()
            _t1660 = Proto.Value(value=OneOf(:missing_value, _t1659))
            _t1658 = _t1660
        else
            if prediction878 == 10
                formatted_decimal889 = consume_terminal!(parser, "DECIMAL")
                _t1662 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal889))
                _t1661 = _t1662
            else
                if prediction878 == 9
                    formatted_int128888 = consume_terminal!(parser, "INT128")
                    _t1664 = Proto.Value(value=OneOf(:int128_value, formatted_int128888))
                    _t1663 = _t1664
                else
                    if prediction878 == 8
                        formatted_uint128887 = consume_terminal!(parser, "UINT128")
                        _t1666 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128887))
                        _t1665 = _t1666
                    else
                        if prediction878 == 7
                            formatted_uint32886 = consume_terminal!(parser, "UINT32")
                            _t1668 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32886))
                            _t1667 = _t1668
                        else
                            if prediction878 == 6
                                formatted_float885 = consume_terminal!(parser, "FLOAT")
                                _t1670 = Proto.Value(value=OneOf(:float_value, formatted_float885))
                                _t1669 = _t1670
                            else
                                if prediction878 == 5
                                    formatted_float32884 = consume_terminal!(parser, "FLOAT32")
                                    _t1672 = Proto.Value(value=OneOf(:float32_value, formatted_float32884))
                                    _t1671 = _t1672
                                else
                                    if prediction878 == 4
                                        formatted_int883 = consume_terminal!(parser, "INT")
                                        _t1674 = Proto.Value(value=OneOf(:int_value, formatted_int883))
                                        _t1673 = _t1674
                                    else
                                        if prediction878 == 3
                                            formatted_int32882 = consume_terminal!(parser, "INT32")
                                            _t1676 = Proto.Value(value=OneOf(:int32_value, formatted_int32882))
                                            _t1675 = _t1676
                                        else
                                            if prediction878 == 2
                                                formatted_string881 = consume_terminal!(parser, "STRING")
                                                _t1678 = Proto.Value(value=OneOf(:string_value, formatted_string881))
                                                _t1677 = _t1678
                                            else
                                                if prediction878 == 1
                                                    _t1680 = parse_datetime(parser)
                                                    datetime880 = _t1680
                                                    _t1681 = Proto.Value(value=OneOf(:datetime_value, datetime880))
                                                    _t1679 = _t1681
                                                else
                                                    if prediction878 == 0
                                                        _t1683 = parse_date(parser)
                                                        date879 = _t1683
                                                        _t1684 = Proto.Value(value=OneOf(:date_value, date879))
                                                        _t1682 = _t1684
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1679 = _t1682
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
                        _t1665 = _t1667
                    end
                    _t1663 = _t1665
                end
                _t1661 = _t1663
            end
            _t1658 = _t1661
        end
        _t1655 = _t1658
    end
    result892 = _t1655
    record_span!(parser, span_start891, "Value")
    return result892
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start896 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int893 = consume_terminal!(parser, "INT")
    formatted_int_3894 = consume_terminal!(parser, "INT")
    formatted_int_4895 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1685 = Proto.DateValue(year=Int32(formatted_int893), month=Int32(formatted_int_3894), day=Int32(formatted_int_4895))
    result897 = _t1685
    record_span!(parser, span_start896, "DateValue")
    return result897
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start905 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int898 = consume_terminal!(parser, "INT")
    formatted_int_3899 = consume_terminal!(parser, "INT")
    formatted_int_4900 = consume_terminal!(parser, "INT")
    formatted_int_5901 = consume_terminal!(parser, "INT")
    formatted_int_6902 = consume_terminal!(parser, "INT")
    formatted_int_7903 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1686 = consume_terminal!(parser, "INT")
    else
        _t1686 = nothing
    end
    formatted_int_8904 = _t1686
    consume_literal!(parser, ")")
    _t1687 = Proto.DateTimeValue(year=Int32(formatted_int898), month=Int32(formatted_int_3899), day=Int32(formatted_int_4900), hour=Int32(formatted_int_5901), minute=Int32(formatted_int_6902), second=Int32(formatted_int_7903), microsecond=Int32((!isnothing(formatted_int_8904) ? formatted_int_8904 : 0)))
    result906 = _t1687
    record_span!(parser, span_start905, "DateTimeValue")
    return result906
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start911 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs907 = Proto.Formula[]
    cond908 = match_lookahead_literal(parser, "(", 0)
    while cond908
        _t1688 = parse_formula(parser)
        item909 = _t1688
        push!(xs907, item909)
        cond908 = match_lookahead_literal(parser, "(", 0)
    end
    formulas910 = xs907
    consume_literal!(parser, ")")
    _t1689 = Proto.Conjunction(args=formulas910)
    result912 = _t1689
    record_span!(parser, span_start911, "Conjunction")
    return result912
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start917 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs913 = Proto.Formula[]
    cond914 = match_lookahead_literal(parser, "(", 0)
    while cond914
        _t1690 = parse_formula(parser)
        item915 = _t1690
        push!(xs913, item915)
        cond914 = match_lookahead_literal(parser, "(", 0)
    end
    formulas916 = xs913
    consume_literal!(parser, ")")
    _t1691 = Proto.Disjunction(args=formulas916)
    result918 = _t1691
    record_span!(parser, span_start917, "Disjunction")
    return result918
end

function parse_not(parser::ParserState)::Proto.Not
    span_start920 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1692 = parse_formula(parser)
    formula919 = _t1692
    consume_literal!(parser, ")")
    _t1693 = Proto.Not(arg=formula919)
    result921 = _t1693
    record_span!(parser, span_start920, "Not")
    return result921
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start925 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1694 = parse_name(parser)
    name922 = _t1694
    _t1695 = parse_ffi_args(parser)
    ffi_args923 = _t1695
    _t1696 = parse_terms(parser)
    terms924 = _t1696
    consume_literal!(parser, ")")
    _t1697 = Proto.FFI(name=name922, args=ffi_args923, terms=terms924)
    result926 = _t1697
    record_span!(parser, span_start925, "FFI")
    return result926
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol927 = consume_terminal!(parser, "SYMBOL")
    return symbol927
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs928 = Proto.Abstraction[]
    cond929 = match_lookahead_literal(parser, "(", 0)
    while cond929
        _t1698 = parse_abstraction(parser)
        item930 = _t1698
        push!(xs928, item930)
        cond929 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions931 = xs928
    consume_literal!(parser, ")")
    return abstractions931
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start937 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1699 = parse_relation_id(parser)
    relation_id932 = _t1699
    xs933 = Proto.Term[]
    cond934 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond934
        _t1700 = parse_term(parser)
        item935 = _t1700
        push!(xs933, item935)
        cond934 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms936 = xs933
    consume_literal!(parser, ")")
    _t1701 = Proto.Atom(name=relation_id932, terms=terms936)
    result938 = _t1701
    record_span!(parser, span_start937, "Atom")
    return result938
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start944 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1702 = parse_name(parser)
    name939 = _t1702
    xs940 = Proto.Term[]
    cond941 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond941
        _t1703 = parse_term(parser)
        item942 = _t1703
        push!(xs940, item942)
        cond941 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms943 = xs940
    consume_literal!(parser, ")")
    _t1704 = Proto.Pragma(name=name939, terms=terms943)
    result945 = _t1704
    record_span!(parser, span_start944, "Pragma")
    return result945
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start961 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1706 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1707 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1708 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1709 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1710 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1711 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1712 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1713 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1714 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1715 = 7
                                            else
                                                _t1715 = -1
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
                        _t1709 = _t1710
                    end
                    _t1708 = _t1709
                end
                _t1707 = _t1708
            end
            _t1706 = _t1707
        end
        _t1705 = _t1706
    else
        _t1705 = -1
    end
    prediction946 = _t1705
    if prediction946 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1717 = parse_name(parser)
        name956 = _t1717
        xs957 = Proto.RelTerm[]
        cond958 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond958
            _t1718 = parse_rel_term(parser)
            item959 = _t1718
            push!(xs957, item959)
            cond958 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms960 = xs957
        consume_literal!(parser, ")")
        _t1719 = Proto.Primitive(name=name956, terms=rel_terms960)
        _t1716 = _t1719
    else
        if prediction946 == 8
            _t1721 = parse_divide(parser)
            divide955 = _t1721
            _t1720 = divide955
        else
            if prediction946 == 7
                _t1723 = parse_multiply(parser)
                multiply954 = _t1723
                _t1722 = multiply954
            else
                if prediction946 == 6
                    _t1725 = parse_minus(parser)
                    minus953 = _t1725
                    _t1724 = minus953
                else
                    if prediction946 == 5
                        _t1727 = parse_add(parser)
                        add952 = _t1727
                        _t1726 = add952
                    else
                        if prediction946 == 4
                            _t1729 = parse_gt_eq(parser)
                            gt_eq951 = _t1729
                            _t1728 = gt_eq951
                        else
                            if prediction946 == 3
                                _t1731 = parse_gt(parser)
                                gt950 = _t1731
                                _t1730 = gt950
                            else
                                if prediction946 == 2
                                    _t1733 = parse_lt_eq(parser)
                                    lt_eq949 = _t1733
                                    _t1732 = lt_eq949
                                else
                                    if prediction946 == 1
                                        _t1735 = parse_lt(parser)
                                        lt948 = _t1735
                                        _t1734 = lt948
                                    else
                                        if prediction946 == 0
                                            _t1737 = parse_eq(parser)
                                            eq947 = _t1737
                                            _t1736 = eq947
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
                    _t1724 = _t1726
                end
                _t1722 = _t1724
            end
            _t1720 = _t1722
        end
        _t1716 = _t1720
    end
    result962 = _t1716
    record_span!(parser, span_start961, "Primitive")
    return result962
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start965 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1738 = parse_term(parser)
    term963 = _t1738
    _t1739 = parse_term(parser)
    term_3964 = _t1739
    consume_literal!(parser, ")")
    _t1740 = Proto.RelTerm(rel_term_type=OneOf(:term, term963))
    _t1741 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3964))
    _t1742 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1740, _t1741])
    result966 = _t1742
    record_span!(parser, span_start965, "Primitive")
    return result966
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1743 = parse_term(parser)
    term967 = _t1743
    _t1744 = parse_term(parser)
    term_3968 = _t1744
    consume_literal!(parser, ")")
    _t1745 = Proto.RelTerm(rel_term_type=OneOf(:term, term967))
    _t1746 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3968))
    _t1747 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1745, _t1746])
    result970 = _t1747
    record_span!(parser, span_start969, "Primitive")
    return result970
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start973 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1748 = parse_term(parser)
    term971 = _t1748
    _t1749 = parse_term(parser)
    term_3972 = _t1749
    consume_literal!(parser, ")")
    _t1750 = Proto.RelTerm(rel_term_type=OneOf(:term, term971))
    _t1751 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3972))
    _t1752 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1750, _t1751])
    result974 = _t1752
    record_span!(parser, span_start973, "Primitive")
    return result974
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start977 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1753 = parse_term(parser)
    term975 = _t1753
    _t1754 = parse_term(parser)
    term_3976 = _t1754
    consume_literal!(parser, ")")
    _t1755 = Proto.RelTerm(rel_term_type=OneOf(:term, term975))
    _t1756 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3976))
    _t1757 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1755, _t1756])
    result978 = _t1757
    record_span!(parser, span_start977, "Primitive")
    return result978
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start981 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1758 = parse_term(parser)
    term979 = _t1758
    _t1759 = parse_term(parser)
    term_3980 = _t1759
    consume_literal!(parser, ")")
    _t1760 = Proto.RelTerm(rel_term_type=OneOf(:term, term979))
    _t1761 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3980))
    _t1762 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1760, _t1761])
    result982 = _t1762
    record_span!(parser, span_start981, "Primitive")
    return result982
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start986 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1763 = parse_term(parser)
    term983 = _t1763
    _t1764 = parse_term(parser)
    term_3984 = _t1764
    _t1765 = parse_term(parser)
    term_4985 = _t1765
    consume_literal!(parser, ")")
    _t1766 = Proto.RelTerm(rel_term_type=OneOf(:term, term983))
    _t1767 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3984))
    _t1768 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4985))
    _t1769 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1766, _t1767, _t1768])
    result987 = _t1769
    record_span!(parser, span_start986, "Primitive")
    return result987
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start991 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1770 = parse_term(parser)
    term988 = _t1770
    _t1771 = parse_term(parser)
    term_3989 = _t1771
    _t1772 = parse_term(parser)
    term_4990 = _t1772
    consume_literal!(parser, ")")
    _t1773 = Proto.RelTerm(rel_term_type=OneOf(:term, term988))
    _t1774 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3989))
    _t1775 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4990))
    _t1776 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1773, _t1774, _t1775])
    result992 = _t1776
    record_span!(parser, span_start991, "Primitive")
    return result992
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start996 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1777 = parse_term(parser)
    term993 = _t1777
    _t1778 = parse_term(parser)
    term_3994 = _t1778
    _t1779 = parse_term(parser)
    term_4995 = _t1779
    consume_literal!(parser, ")")
    _t1780 = Proto.RelTerm(rel_term_type=OneOf(:term, term993))
    _t1781 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3994))
    _t1782 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4995))
    _t1783 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1780, _t1781, _t1782])
    result997 = _t1783
    record_span!(parser, span_start996, "Primitive")
    return result997
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1001 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1784 = parse_term(parser)
    term998 = _t1784
    _t1785 = parse_term(parser)
    term_3999 = _t1785
    _t1786 = parse_term(parser)
    term_41000 = _t1786
    consume_literal!(parser, ")")
    _t1787 = Proto.RelTerm(rel_term_type=OneOf(:term, term998))
    _t1788 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3999))
    _t1789 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41000))
    _t1790 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1787, _t1788, _t1789])
    result1002 = _t1790
    record_span!(parser, span_start1001, "Primitive")
    return result1002
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1006 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1791 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1792 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1793 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1794 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1795 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1796 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1797 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1798 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1799 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1800 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1801 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1802 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1803 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1804 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1805 = 1
                                                            else
                                                                _t1805 = -1
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
    prediction1003 = _t1791
    if prediction1003 == 1
        _t1807 = parse_term(parser)
        term1005 = _t1807
        _t1808 = Proto.RelTerm(rel_term_type=OneOf(:term, term1005))
        _t1806 = _t1808
    else
        if prediction1003 == 0
            _t1810 = parse_specialized_value(parser)
            specialized_value1004 = _t1810
            _t1811 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1004))
            _t1809 = _t1811
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1806 = _t1809
    end
    result1007 = _t1806
    record_span!(parser, span_start1006, "RelTerm")
    return result1007
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1009 = span_start(parser)
    consume_literal!(parser, "#")
    _t1812 = parse_raw_value(parser)
    raw_value1008 = _t1812
    result1010 = raw_value1008
    record_span!(parser, span_start1009, "Value")
    return result1010
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1016 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1813 = parse_name(parser)
    name1011 = _t1813
    xs1012 = Proto.RelTerm[]
    cond1013 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1013
        _t1814 = parse_rel_term(parser)
        item1014 = _t1814
        push!(xs1012, item1014)
        cond1013 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1015 = xs1012
    consume_literal!(parser, ")")
    _t1815 = Proto.RelAtom(name=name1011, terms=rel_terms1015)
    result1017 = _t1815
    record_span!(parser, span_start1016, "RelAtom")
    return result1017
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1020 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1816 = parse_term(parser)
    term1018 = _t1816
    _t1817 = parse_term(parser)
    term_31019 = _t1817
    consume_literal!(parser, ")")
    _t1818 = Proto.Cast(input=term1018, result=term_31019)
    result1021 = _t1818
    record_span!(parser, span_start1020, "Cast")
    return result1021
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1022 = Proto.Attribute[]
    cond1023 = match_lookahead_literal(parser, "(", 0)
    while cond1023
        _t1819 = parse_attribute(parser)
        item1024 = _t1819
        push!(xs1022, item1024)
        cond1023 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1025 = xs1022
    consume_literal!(parser, ")")
    return attributes1025
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1031 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1820 = parse_name(parser)
    name1026 = _t1820
    xs1027 = Proto.Value[]
    cond1028 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1028
        _t1821 = parse_raw_value(parser)
        item1029 = _t1821
        push!(xs1027, item1029)
        cond1028 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1030 = xs1027
    consume_literal!(parser, ")")
    _t1822 = Proto.Attribute(name=name1026, args=raw_values1030)
    result1032 = _t1822
    record_span!(parser, span_start1031, "Attribute")
    return result1032
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1038 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1033 = Proto.RelationId[]
    cond1034 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1034
        _t1823 = parse_relation_id(parser)
        item1035 = _t1823
        push!(xs1033, item1035)
        cond1034 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1036 = xs1033
    _t1824 = parse_script(parser)
    script1037 = _t1824
    consume_literal!(parser, ")")
    _t1825 = Proto.Algorithm(var"#global"=relation_ids1036, body=script1037)
    result1039 = _t1825
    record_span!(parser, span_start1038, "Algorithm")
    return result1039
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1044 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1040 = Proto.Construct[]
    cond1041 = match_lookahead_literal(parser, "(", 0)
    while cond1041
        _t1826 = parse_construct(parser)
        item1042 = _t1826
        push!(xs1040, item1042)
        cond1041 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1043 = xs1040
    consume_literal!(parser, ")")
    _t1827 = Proto.Script(constructs=constructs1043)
    result1045 = _t1827
    record_span!(parser, span_start1044, "Script")
    return result1045
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1049 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1829 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1830 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1831 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1832 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1833 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1834 = 1
                            else
                                _t1834 = -1
                            end
                            _t1833 = _t1834
                        end
                        _t1832 = _t1833
                    end
                    _t1831 = _t1832
                end
                _t1830 = _t1831
            end
            _t1829 = _t1830
        end
        _t1828 = _t1829
    else
        _t1828 = -1
    end
    prediction1046 = _t1828
    if prediction1046 == 1
        _t1836 = parse_instruction(parser)
        instruction1048 = _t1836
        _t1837 = Proto.Construct(construct_type=OneOf(:instruction, instruction1048))
        _t1835 = _t1837
    else
        if prediction1046 == 0
            _t1839 = parse_loop(parser)
            loop1047 = _t1839
            _t1840 = Proto.Construct(construct_type=OneOf(:loop, loop1047))
            _t1838 = _t1840
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1835 = _t1838
    end
    result1050 = _t1835
    record_span!(parser, span_start1049, "Construct")
    return result1050
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1053 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1841 = parse_init(parser)
    init1051 = _t1841
    _t1842 = parse_script(parser)
    script1052 = _t1842
    consume_literal!(parser, ")")
    _t1843 = Proto.Loop(init=init1051, body=script1052)
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
    string1179 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1179
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1181 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1969 = parse_config_dict(parser)
    config_dict1180 = _t1969
    consume_literal!(parser, ")")
    _t1970 = construct_csv_config(parser, config_dict1180)
    result1182 = _t1970
    record_span!(parser, span_start1181, "CSVConfig")
    return result1182
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1183 = Proto.GNFColumn[]
    cond1184 = match_lookahead_literal(parser, "(", 0)
    while cond1184
        _t1971 = parse_gnf_column(parser)
        item1185 = _t1971
        push!(xs1183, item1185)
        cond1184 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1186 = xs1183
    consume_literal!(parser, ")")
    return gnf_columns1186
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1193 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1972 = parse_gnf_column_path(parser)
    gnf_column_path1187 = _t1972
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1974 = parse_relation_id(parser)
        _t1973 = _t1974
    else
        _t1973 = nothing
    end
    relation_id1188 = _t1973
    consume_literal!(parser, "[")
    xs1189 = Proto.var"#Type"[]
    cond1190 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1190
        _t1975 = parse_type(parser)
        item1191 = _t1975
        push!(xs1189, item1191)
        cond1190 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1192 = xs1189
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1976 = Proto.GNFColumn(column_path=gnf_column_path1187, target_id=relation_id1188, types=types1192)
    result1194 = _t1976
    record_span!(parser, span_start1193, "GNFColumn")
    return result1194
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1977 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1978 = 0
        else
            _t1978 = -1
        end
        _t1977 = _t1978
    end
    prediction1195 = _t1977
    if prediction1195 == 1
        consume_literal!(parser, "[")
        xs1197 = String[]
        cond1198 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1198
            item1199 = consume_terminal!(parser, "STRING")
            push!(xs1197, item1199)
            cond1198 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1200 = xs1197
        consume_literal!(parser, "]")
        _t1979 = strings1200
    else
        if prediction1195 == 0
            string1196 = consume_terminal!(parser, "STRING")
            _t1980 = String[string1196]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1979 = _t1980
    end
    return _t1979
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1201 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1201
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1208 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1981 = parse_iceberg_locator(parser)
    iceberg_locator1202 = _t1981
    _t1982 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1203 = _t1982
    _t1983 = parse_gnf_columns(parser)
    gnf_columns1204 = _t1983
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1985 = parse_iceberg_from_snapshot(parser)
        _t1984 = _t1985
    else
        _t1984 = nothing
    end
    iceberg_from_snapshot1205 = _t1984
    if match_lookahead_literal(parser, "(", 0)
        _t1987 = parse_iceberg_to_snapshot(parser)
        _t1986 = _t1987
    else
        _t1986 = nothing
    end
    iceberg_to_snapshot1206 = _t1986
    _t1988 = parse_boolean_value(parser)
    boolean_value1207 = _t1988
    consume_literal!(parser, ")")
    _t1989 = construct_iceberg_data(parser, iceberg_locator1202, iceberg_catalog_config1203, gnf_columns1204, iceberg_from_snapshot1205, iceberg_to_snapshot1206, boolean_value1207)
    result1209 = _t1989
    record_span!(parser, span_start1208, "IcebergData")
    return result1209
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1213 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t1990 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1210 = _t1990
    _t1991 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1211 = _t1991
    _t1992 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1212 = _t1992
    consume_literal!(parser, ")")
    _t1993 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1210, namespace=iceberg_locator_namespace1211, warehouse=iceberg_locator_warehouse1212)
    result1214 = _t1993
    record_span!(parser, span_start1213, "IcebergLocator")
    return result1214
end

function parse_iceberg_locator_table_name(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1215 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1215
end

function parse_iceberg_locator_namespace(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1216 = String[]
    cond1217 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1217
        item1218 = consume_terminal!(parser, "STRING")
        push!(xs1216, item1218)
        cond1217 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1219 = xs1216
    consume_literal!(parser, ")")
    return strings1219
end

function parse_iceberg_locator_warehouse(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1220 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1220
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1225 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    _t1994 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1221 = _t1994
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1996 = parse_iceberg_catalog_config_scope(parser)
        _t1995 = _t1996
    else
        _t1995 = nothing
    end
    iceberg_catalog_config_scope1222 = _t1995
    _t1997 = parse_iceberg_properties(parser)
    iceberg_properties1223 = _t1997
    _t1998 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1224 = _t1998
    consume_literal!(parser, ")")
    _t1999 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1221, iceberg_catalog_config_scope1222, iceberg_properties1223, iceberg_auth_properties1224)
    result1226 = _t1999
    record_span!(parser, span_start1225, "IcebergCatalogConfig")
    return result1226
end

function parse_iceberg_catalog_uri(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1227 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1227
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1228 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1228
end

function parse_iceberg_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1229 = Tuple{String, String}[]
    cond1230 = match_lookahead_literal(parser, "(", 0)
    while cond1230
        _t2000 = parse_iceberg_property_entry(parser)
        item1231 = _t2000
        push!(xs1229, item1231)
        cond1230 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1232 = xs1229
    consume_literal!(parser, ")")
    return iceberg_property_entrys1232
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1233 = consume_terminal!(parser, "STRING")
    string_31234 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1233, string_31234,)
end

function parse_iceberg_auth_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1235 = Tuple{String, String}[]
    cond1236 = match_lookahead_literal(parser, "(", 0)
    while cond1236
        _t2001 = parse_iceberg_masked_property_entry(parser)
        item1237 = _t2001
        push!(xs1235, item1237)
        cond1236 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1238 = xs1235
    consume_literal!(parser, ")")
    return iceberg_masked_property_entrys1238
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1239 = consume_terminal!(parser, "STRING")
    string_31240 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1239, string_31240,)
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1241 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1241
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1242 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1242
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1244 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t2002 = parse_fragment_id(parser)
    fragment_id1243 = _t2002
    consume_literal!(parser, ")")
    _t2003 = Proto.Undefine(fragment_id=fragment_id1243)
    result1245 = _t2003
    record_span!(parser, span_start1244, "Undefine")
    return result1245
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1250 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1246 = Proto.RelationId[]
    cond1247 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1247
        _t2004 = parse_relation_id(parser)
        item1248 = _t2004
        push!(xs1246, item1248)
        cond1247 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1249 = xs1246
    consume_literal!(parser, ")")
    _t2005 = Proto.Context(relations=relation_ids1249)
    result1251 = _t2005
    record_span!(parser, span_start1250, "Context")
    return result1251
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1257 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t2006 = parse_edb_path(parser)
    edb_path1252 = _t2006
    xs1253 = Proto.SnapshotMapping[]
    cond1254 = match_lookahead_literal(parser, "[", 0)
    while cond1254
        _t2007 = parse_snapshot_mapping(parser)
        item1255 = _t2007
        push!(xs1253, item1255)
        cond1254 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1256 = xs1253
    consume_literal!(parser, ")")
    _t2008 = Proto.Snapshot(mappings=snapshot_mappings1256, prefix=edb_path1252)
    result1258 = _t2008
    record_span!(parser, span_start1257, "Snapshot")
    return result1258
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1261 = span_start(parser)
    _t2009 = parse_edb_path(parser)
    edb_path1259 = _t2009
    _t2010 = parse_relation_id(parser)
    relation_id1260 = _t2010
    _t2011 = Proto.SnapshotMapping(destination_path=edb_path1259, source_relation=relation_id1260)
    result1262 = _t2011
    record_span!(parser, span_start1261, "SnapshotMapping")
    return result1262
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1263 = Proto.Read[]
    cond1264 = match_lookahead_literal(parser, "(", 0)
    while cond1264
        _t2012 = parse_read(parser)
        item1265 = _t2012
        push!(xs1263, item1265)
        cond1264 = match_lookahead_literal(parser, "(", 0)
    end
    reads1266 = xs1263
    consume_literal!(parser, ")")
    return reads1266
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1273 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t2014 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t2015 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t2016 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t2017 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t2018 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t2019 = 3
                            else
                                _t2019 = -1
                            end
                            _t2018 = _t2019
                        end
                        _t2017 = _t2018
                    end
                    _t2016 = _t2017
                end
                _t2015 = _t2016
            end
            _t2014 = _t2015
        end
        _t2013 = _t2014
    else
        _t2013 = -1
    end
    prediction1267 = _t2013
    if prediction1267 == 4
        _t2021 = parse_export(parser)
        export1272 = _t2021
        _t2022 = Proto.Read(read_type=OneOf(:var"#export", export1272))
        _t2020 = _t2022
    else
        if prediction1267 == 3
            _t2024 = parse_abort(parser)
            abort1271 = _t2024
            _t2025 = Proto.Read(read_type=OneOf(:abort, abort1271))
            _t2023 = _t2025
        else
            if prediction1267 == 2
                _t2027 = parse_what_if(parser)
                what_if1270 = _t2027
                _t2028 = Proto.Read(read_type=OneOf(:what_if, what_if1270))
                _t2026 = _t2028
            else
                if prediction1267 == 1
                    _t2030 = parse_output(parser)
                    output1269 = _t2030
                    _t2031 = Proto.Read(read_type=OneOf(:output, output1269))
                    _t2029 = _t2031
                else
                    if prediction1267 == 0
                        _t2033 = parse_demand(parser)
                        demand1268 = _t2033
                        _t2034 = Proto.Read(read_type=OneOf(:demand, demand1268))
                        _t2032 = _t2034
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t2029 = _t2032
                end
                _t2026 = _t2029
            end
            _t2023 = _t2026
        end
        _t2020 = _t2023
    end
    result1274 = _t2020
    record_span!(parser, span_start1273, "Read")
    return result1274
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1276 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2035 = parse_relation_id(parser)
    relation_id1275 = _t2035
    consume_literal!(parser, ")")
    _t2036 = Proto.Demand(relation_id=relation_id1275)
    result1277 = _t2036
    record_span!(parser, span_start1276, "Demand")
    return result1277
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1280 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2037 = parse_name(parser)
    name1278 = _t2037
    _t2038 = parse_relation_id(parser)
    relation_id1279 = _t2038
    consume_literal!(parser, ")")
    _t2039 = Proto.Output(name=name1278, relation_id=relation_id1279)
    result1281 = _t2039
    record_span!(parser, span_start1280, "Output")
    return result1281
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1284 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2040 = parse_name(parser)
    name1282 = _t2040
    _t2041 = parse_epoch(parser)
    epoch1283 = _t2041
    consume_literal!(parser, ")")
    _t2042 = Proto.WhatIf(branch=name1282, epoch=epoch1283)
    result1285 = _t2042
    record_span!(parser, span_start1284, "WhatIf")
    return result1285
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1288 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2044 = parse_name(parser)
        _t2043 = _t2044
    else
        _t2043 = nothing
    end
    name1286 = _t2043
    _t2045 = parse_relation_id(parser)
    relation_id1287 = _t2045
    consume_literal!(parser, ")")
    _t2046 = Proto.Abort(name=(!isnothing(name1286) ? name1286 : "abort"), relation_id=relation_id1287)
    result1289 = _t2046
    record_span!(parser, span_start1288, "Abort")
    return result1289
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1293 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2048 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2049 = 0
            else
                _t2049 = -1
            end
            _t2048 = _t2049
        end
        _t2047 = _t2048
    else
        _t2047 = -1
    end
    prediction1290 = _t2047
    if prediction1290 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2051 = parse_export_iceberg_config(parser)
        export_iceberg_config1292 = _t2051
        consume_literal!(parser, ")")
        _t2052 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1292))
        _t2050 = _t2052
    else
        if prediction1290 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2054 = parse_export_csv_config(parser)
            export_csv_config1291 = _t2054
            consume_literal!(parser, ")")
            _t2055 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1291))
            _t2053 = _t2055
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2050 = _t2053
    end
    result1294 = _t2050
    record_span!(parser, span_start1293, "Export")
    return result1294
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1302 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2057 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2058 = 1
            else
                _t2058 = -1
            end
            _t2057 = _t2058
        end
        _t2056 = _t2057
    else
        _t2056 = -1
    end
    prediction1295 = _t2056
    if prediction1295 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2060 = parse_export_csv_path(parser)
        export_csv_path1299 = _t2060
        _t2061 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1300 = _t2061
        _t2062 = parse_config_dict(parser)
        config_dict1301 = _t2062
        consume_literal!(parser, ")")
        _t2063 = construct_export_csv_config(parser, export_csv_path1299, export_csv_columns_list1300, config_dict1301)
        _t2059 = _t2063
    else
        if prediction1295 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2065 = parse_export_csv_path(parser)
            export_csv_path1296 = _t2065
            _t2066 = parse_export_csv_source(parser)
            export_csv_source1297 = _t2066
            _t2067 = parse_csv_config(parser)
            csv_config1298 = _t2067
            consume_literal!(parser, ")")
            _t2068 = construct_export_csv_config_with_source(parser, export_csv_path1296, export_csv_source1297, csv_config1298)
            _t2064 = _t2068
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2059 = _t2064
    end
    result1303 = _t2059
    record_span!(parser, span_start1302, "ExportCSVConfig")
    return result1303
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1304 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1304
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1311 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2070 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2071 = 0
            else
                _t2071 = -1
            end
            _t2070 = _t2071
        end
        _t2069 = _t2070
    else
        _t2069 = -1
    end
    prediction1305 = _t2069
    if prediction1305 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2073 = parse_relation_id(parser)
        relation_id1310 = _t2073
        consume_literal!(parser, ")")
        _t2074 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1310))
        _t2072 = _t2074
    else
        if prediction1305 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1306 = Proto.ExportCSVColumn[]
            cond1307 = match_lookahead_literal(parser, "(", 0)
            while cond1307
                _t2076 = parse_export_csv_column(parser)
                item1308 = _t2076
                push!(xs1306, item1308)
                cond1307 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1309 = xs1306
            consume_literal!(parser, ")")
            _t2077 = Proto.ExportCSVColumns(columns=export_csv_columns1309)
            _t2078 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2077))
            _t2075 = _t2078
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2072 = _t2075
    end
    result1312 = _t2072
    record_span!(parser, span_start1311, "ExportCSVSource")
    return result1312
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1315 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1313 = consume_terminal!(parser, "STRING")
    _t2079 = parse_relation_id(parser)
    relation_id1314 = _t2079
    consume_literal!(parser, ")")
    _t2080 = Proto.ExportCSVColumn(column_name=string1313, column_data=relation_id1314)
    result1316 = _t2080
    record_span!(parser, span_start1315, "ExportCSVColumn")
    return result1316
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1317 = Proto.ExportCSVColumn[]
    cond1318 = match_lookahead_literal(parser, "(", 0)
    while cond1318
        _t2081 = parse_export_csv_column(parser)
        item1319 = _t2081
        push!(xs1317, item1319)
        cond1318 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1320 = xs1317
    consume_literal!(parser, ")")
    return export_csv_columns1320
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1327 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2082 = parse_iceberg_locator(parser)
    iceberg_locator1321 = _t2082
    _t2083 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1322 = _t2083
    _t2084 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1323 = _t2084
    _t2085 = parse_export_iceberg_columns(parser)
    export_iceberg_columns1324 = _t2085
    _t2086 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1325 = _t2086
    if match_lookahead_literal(parser, "{", 0)
        _t2088 = parse_config_dict(parser)
        _t2087 = _t2088
    else
        _t2087 = nothing
    end
    config_dict1326 = _t2087
    consume_literal!(parser, ")")
    _t2089 = construct_export_iceberg_config_full(parser, iceberg_locator1321, iceberg_catalog_config1322, export_iceberg_table_def1323, export_iceberg_columns1324, iceberg_table_properties1325, config_dict1326)
    result1328 = _t2089
    record_span!(parser, span_start1327, "ExportIcebergConfig")
    return result1328
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1330 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2090 = parse_relation_id(parser)
    relation_id1329 = _t2090
    consume_literal!(parser, ")")
    result1331 = relation_id1329
    record_span!(parser, span_start1330, "RelationId")
    return result1331
end

function parse_export_iceberg_columns(parser::ParserState)::Vector{Proto.ExportColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1332 = Proto.ExportColumn[]
    cond1333 = match_lookahead_literal(parser, "(", 0)
    while cond1333
        _t2091 = parse_export_iceberg_column(parser)
        item1334 = _t2091
        push!(xs1332, item1334)
        cond1333 = match_lookahead_literal(parser, "(", 0)
    end
    export_iceberg_columns1335 = xs1332
    consume_literal!(parser, ")")
    return export_iceberg_columns1335
end

function parse_export_iceberg_column(parser::ParserState)::Proto.ExportColumn
    span_start1338 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1336 = consume_terminal!(parser, "STRING")
    _t2092 = parse_boolean_value(parser)
    boolean_value1337 = _t2092
    consume_literal!(parser, ")")
    _t2093 = Proto.ExportColumn(name=string1336, nullable=boolean_value1337)
    result1339 = _t2093
    record_span!(parser, span_start1338, "ExportColumn")
    return result1339
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1340 = Tuple{String, String}[]
    cond1341 = match_lookahead_literal(parser, "(", 0)
    while cond1341
        _t2094 = parse_iceberg_property_entry(parser)
        item1342 = _t2094
        push!(xs1340, item1342)
        cond1341 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1343 = xs1340
    consume_literal!(parser, ")")
    return iceberg_property_entrys1343
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
