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
    # Use the upper 128 bits of the hash in native byte order.
    id_low = reinterpret(UInt64, hash_bytes[1:8])[1]
    id_high = reinterpret(UInt64, hash_bytes[9:16])[1]
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
        _t2092 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2093 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2094 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2095 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2096 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2097 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2098 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2099 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2100 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2101 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2101
    _t2102 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2102
    _t2103 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2103
    _t2104 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2104
    _t2105 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2105
    _t2106 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2106
    _t2107 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2107
    _t2108 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2108
    _t2109 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2109
    _t2110 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2110
    _t2111 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2111
    _t2112 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2112
    _t2113 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2113
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2114 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2114
    _t2115 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2115
    _t2116 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2116
    _t2117 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2117
    _t2118 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2118
    _t2119 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2119
    _t2120 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2120
    _t2121 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2121
    _t2122 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2122
    _t2123 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2123
    _t2124 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2124
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2125 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2125
    _t2126 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2126
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
    _t2127 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2127
    _t2128 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2128
    _t2129 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2129
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2130 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2130
    _t2131 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2131
    _t2132 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2132
    _t2133 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2133
    _t2134 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2134
    _t2135 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2135
    _t2136 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2136
    _t2137 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2137
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2138 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2138
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2139 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2139
end

function construct_iceberg_data(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.GNFColumn}, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String}, returns_delta::Bool)::Proto.IcebergData
    _t2140 = Proto.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""), returns_delta=returns_delta)
    return _t2140
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, columns::Vector{Proto.ExportColumn}, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2141 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2141
    _t2142 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2142
    _t2143 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2143
    table_props = Dict(table_property_pairs)
    _t2144 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2144
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start677 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1343 = parse_configure(parser)
        _t1342 = _t1343
    else
        _t1342 = nothing
    end
    configure671 = _t1342
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1345 = parse_sync(parser)
        _t1344 = _t1345
    else
        _t1344 = nothing
    end
    sync672 = _t1344
    xs673 = Proto.Epoch[]
    cond674 = match_lookahead_literal(parser, "(", 0)
    while cond674
        _t1346 = parse_epoch(parser)
        item675 = _t1346
        push!(xs673, item675)
        cond674 = match_lookahead_literal(parser, "(", 0)
    end
    epochs676 = xs673
    consume_literal!(parser, ")")
    _t1347 = default_configure(parser)
    _t1348 = Proto.Transaction(epochs=epochs676, configure=(!isnothing(configure671) ? configure671 : _t1347), sync=sync672)
    result678 = _t1348
    record_span!(parser, span_start677, "Transaction")
    return result678
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start680 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1349 = parse_config_dict(parser)
    config_dict679 = _t1349
    consume_literal!(parser, ")")
    _t1350 = construct_configure(parser, config_dict679)
    result681 = _t1350
    record_span!(parser, span_start680, "Configure")
    return result681
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs682 = Tuple{String, Proto.Value}[]
    cond683 = match_lookahead_literal(parser, ":", 0)
    while cond683
        _t1351 = parse_config_key_value(parser)
        item684 = _t1351
        push!(xs682, item684)
        cond683 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values685 = xs682
    consume_literal!(parser, "}")
    return config_key_values685
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol686 = consume_terminal!(parser, "SYMBOL")
    _t1352 = parse_raw_value(parser)
    raw_value687 = _t1352
    return (symbol686, raw_value687,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start701 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1353 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1354 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1355 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1357 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1358 = 0
                        else
                            _t1358 = -1
                        end
                        _t1357 = _t1358
                    end
                    _t1356 = _t1357
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1359 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1360 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1361 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1362 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1363 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1364 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1365 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1366 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1367 = 10
                                                    else
                                                        _t1367 = -1
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
                            _t1360 = _t1361
                        end
                        _t1359 = _t1360
                    end
                    _t1356 = _t1359
                end
                _t1355 = _t1356
            end
            _t1354 = _t1355
        end
        _t1353 = _t1354
    end
    prediction688 = _t1353
    if prediction688 == 12
        _t1369 = parse_boolean_value(parser)
        boolean_value700 = _t1369
        _t1370 = Proto.Value(value=OneOf(:boolean_value, boolean_value700))
        _t1368 = _t1370
    else
        if prediction688 == 11
            consume_literal!(parser, "missing")
            _t1372 = Proto.MissingValue()
            _t1373 = Proto.Value(value=OneOf(:missing_value, _t1372))
            _t1371 = _t1373
        else
            if prediction688 == 10
                decimal699 = consume_terminal!(parser, "DECIMAL")
                _t1375 = Proto.Value(value=OneOf(:decimal_value, decimal699))
                _t1374 = _t1375
            else
                if prediction688 == 9
                    int128698 = consume_terminal!(parser, "INT128")
                    _t1377 = Proto.Value(value=OneOf(:int128_value, int128698))
                    _t1376 = _t1377
                else
                    if prediction688 == 8
                        uint128697 = consume_terminal!(parser, "UINT128")
                        _t1379 = Proto.Value(value=OneOf(:uint128_value, uint128697))
                        _t1378 = _t1379
                    else
                        if prediction688 == 7
                            uint32696 = consume_terminal!(parser, "UINT32")
                            _t1381 = Proto.Value(value=OneOf(:uint32_value, uint32696))
                            _t1380 = _t1381
                        else
                            if prediction688 == 6
                                float695 = consume_terminal!(parser, "FLOAT")
                                _t1383 = Proto.Value(value=OneOf(:float_value, float695))
                                _t1382 = _t1383
                            else
                                if prediction688 == 5
                                    float32694 = consume_terminal!(parser, "FLOAT32")
                                    _t1385 = Proto.Value(value=OneOf(:float32_value, float32694))
                                    _t1384 = _t1385
                                else
                                    if prediction688 == 4
                                        int693 = consume_terminal!(parser, "INT")
                                        _t1387 = Proto.Value(value=OneOf(:int_value, int693))
                                        _t1386 = _t1387
                                    else
                                        if prediction688 == 3
                                            int32692 = consume_terminal!(parser, "INT32")
                                            _t1389 = Proto.Value(value=OneOf(:int32_value, int32692))
                                            _t1388 = _t1389
                                        else
                                            if prediction688 == 2
                                                string691 = consume_terminal!(parser, "STRING")
                                                _t1391 = Proto.Value(value=OneOf(:string_value, string691))
                                                _t1390 = _t1391
                                            else
                                                if prediction688 == 1
                                                    _t1393 = parse_raw_datetime(parser)
                                                    raw_datetime690 = _t1393
                                                    _t1394 = Proto.Value(value=OneOf(:datetime_value, raw_datetime690))
                                                    _t1392 = _t1394
                                                else
                                                    if prediction688 == 0
                                                        _t1396 = parse_raw_date(parser)
                                                        raw_date689 = _t1396
                                                        _t1397 = Proto.Value(value=OneOf(:date_value, raw_date689))
                                                        _t1395 = _t1397
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1392 = _t1395
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
                _t1374 = _t1376
            end
            _t1371 = _t1374
        end
        _t1368 = _t1371
    end
    result702 = _t1368
    record_span!(parser, span_start701, "Value")
    return result702
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start706 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int703 = consume_terminal!(parser, "INT")
    int_3704 = consume_terminal!(parser, "INT")
    int_4705 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1398 = Proto.DateValue(year=Int32(int703), month=Int32(int_3704), day=Int32(int_4705))
    result707 = _t1398
    record_span!(parser, span_start706, "DateValue")
    return result707
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start715 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int708 = consume_terminal!(parser, "INT")
    int_3709 = consume_terminal!(parser, "INT")
    int_4710 = consume_terminal!(parser, "INT")
    int_5711 = consume_terminal!(parser, "INT")
    int_6712 = consume_terminal!(parser, "INT")
    int_7713 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1399 = consume_terminal!(parser, "INT")
    else
        _t1399 = nothing
    end
    int_8714 = _t1399
    consume_literal!(parser, ")")
    _t1400 = Proto.DateTimeValue(year=Int32(int708), month=Int32(int_3709), day=Int32(int_4710), hour=Int32(int_5711), minute=Int32(int_6712), second=Int32(int_7713), microsecond=Int32((!isnothing(int_8714) ? int_8714 : 0)))
    result716 = _t1400
    record_span!(parser, span_start715, "DateTimeValue")
    return result716
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1401 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1402 = 1
        else
            _t1402 = -1
        end
        _t1401 = _t1402
    end
    prediction717 = _t1401
    if prediction717 == 1
        consume_literal!(parser, "false")
        _t1403 = false
    else
        if prediction717 == 0
            consume_literal!(parser, "true")
            _t1404 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1403 = _t1404
    end
    return _t1403
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start722 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs718 = Proto.FragmentId[]
    cond719 = match_lookahead_literal(parser, ":", 0)
    while cond719
        _t1405 = parse_fragment_id(parser)
        item720 = _t1405
        push!(xs718, item720)
        cond719 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids721 = xs718
    consume_literal!(parser, ")")
    _t1406 = Proto.Sync(fragments=fragment_ids721)
    result723 = _t1406
    record_span!(parser, span_start722, "Sync")
    return result723
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start725 = span_start(parser)
    consume_literal!(parser, ":")
    symbol724 = consume_terminal!(parser, "SYMBOL")
    result726 = Proto.FragmentId(Vector{UInt8}(symbol724))
    record_span!(parser, span_start725, "FragmentId")
    return result726
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start729 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1408 = parse_epoch_writes(parser)
        _t1407 = _t1408
    else
        _t1407 = nothing
    end
    epoch_writes727 = _t1407
    if match_lookahead_literal(parser, "(", 0)
        _t1410 = parse_epoch_reads(parser)
        _t1409 = _t1410
    else
        _t1409 = nothing
    end
    epoch_reads728 = _t1409
    consume_literal!(parser, ")")
    _t1411 = Proto.Epoch(writes=(!isnothing(epoch_writes727) ? epoch_writes727 : Proto.Write[]), reads=(!isnothing(epoch_reads728) ? epoch_reads728 : Proto.Read[]))
    result730 = _t1411
    record_span!(parser, span_start729, "Epoch")
    return result730
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs731 = Proto.Write[]
    cond732 = match_lookahead_literal(parser, "(", 0)
    while cond732
        _t1412 = parse_write(parser)
        item733 = _t1412
        push!(xs731, item733)
        cond732 = match_lookahead_literal(parser, "(", 0)
    end
    writes734 = xs731
    consume_literal!(parser, ")")
    return writes734
end

function parse_write(parser::ParserState)::Proto.Write
    span_start740 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1414 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1415 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1416 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1417 = 2
                    else
                        _t1417 = -1
                    end
                    _t1416 = _t1417
                end
                _t1415 = _t1416
            end
            _t1414 = _t1415
        end
        _t1413 = _t1414
    else
        _t1413 = -1
    end
    prediction735 = _t1413
    if prediction735 == 3
        _t1419 = parse_snapshot(parser)
        snapshot739 = _t1419
        _t1420 = Proto.Write(write_type=OneOf(:snapshot, snapshot739))
        _t1418 = _t1420
    else
        if prediction735 == 2
            _t1422 = parse_context(parser)
            context738 = _t1422
            _t1423 = Proto.Write(write_type=OneOf(:context, context738))
            _t1421 = _t1423
        else
            if prediction735 == 1
                _t1425 = parse_undefine(parser)
                undefine737 = _t1425
                _t1426 = Proto.Write(write_type=OneOf(:undefine, undefine737))
                _t1424 = _t1426
            else
                if prediction735 == 0
                    _t1428 = parse_define(parser)
                    define736 = _t1428
                    _t1429 = Proto.Write(write_type=OneOf(:define, define736))
                    _t1427 = _t1429
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1424 = _t1427
            end
            _t1421 = _t1424
        end
        _t1418 = _t1421
    end
    result741 = _t1418
    record_span!(parser, span_start740, "Write")
    return result741
end

function parse_define(parser::ParserState)::Proto.Define
    span_start743 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1430 = parse_fragment(parser)
    fragment742 = _t1430
    consume_literal!(parser, ")")
    _t1431 = Proto.Define(fragment=fragment742)
    result744 = _t1431
    record_span!(parser, span_start743, "Define")
    return result744
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start750 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1432 = parse_new_fragment_id(parser)
    new_fragment_id745 = _t1432
    xs746 = Proto.Declaration[]
    cond747 = match_lookahead_literal(parser, "(", 0)
    while cond747
        _t1433 = parse_declaration(parser)
        item748 = _t1433
        push!(xs746, item748)
        cond747 = match_lookahead_literal(parser, "(", 0)
    end
    declarations749 = xs746
    consume_literal!(parser, ")")
    result751 = construct_fragment(parser, new_fragment_id745, declarations749)
    record_span!(parser, span_start750, "Fragment")
    return result751
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start753 = span_start(parser)
    _t1434 = parse_fragment_id(parser)
    fragment_id752 = _t1434
    start_fragment!(parser, fragment_id752)
    result754 = fragment_id752
    record_span!(parser, span_start753, "FragmentId")
    return result754
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start760 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1436 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1437 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1438 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1439 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1440 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1441 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1442 = 1
                                else
                                    _t1442 = -1
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
    else
        _t1435 = -1
    end
    prediction755 = _t1435
    if prediction755 == 3
        _t1444 = parse_data(parser)
        data759 = _t1444
        _t1445 = Proto.Declaration(declaration_type=OneOf(:data, data759))
        _t1443 = _t1445
    else
        if prediction755 == 2
            _t1447 = parse_constraint(parser)
            constraint758 = _t1447
            _t1448 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint758))
            _t1446 = _t1448
        else
            if prediction755 == 1
                _t1450 = parse_algorithm(parser)
                algorithm757 = _t1450
                _t1451 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm757))
                _t1449 = _t1451
            else
                if prediction755 == 0
                    _t1453 = parse_def(parser)
                    def756 = _t1453
                    _t1454 = Proto.Declaration(declaration_type=OneOf(:def, def756))
                    _t1452 = _t1454
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1449 = _t1452
            end
            _t1446 = _t1449
        end
        _t1443 = _t1446
    end
    result761 = _t1443
    record_span!(parser, span_start760, "Declaration")
    return result761
end

function parse_def(parser::ParserState)::Proto.Def
    span_start765 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1455 = parse_relation_id(parser)
    relation_id762 = _t1455
    _t1456 = parse_abstraction(parser)
    abstraction763 = _t1456
    if match_lookahead_literal(parser, "(", 0)
        _t1458 = parse_attrs(parser)
        _t1457 = _t1458
    else
        _t1457 = nothing
    end
    attrs764 = _t1457
    consume_literal!(parser, ")")
    _t1459 = Proto.Def(name=relation_id762, body=abstraction763, attrs=(!isnothing(attrs764) ? attrs764 : Proto.Attribute[]))
    result766 = _t1459
    record_span!(parser, span_start765, "Def")
    return result766
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start770 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1460 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1461 = 1
        else
            _t1461 = -1
        end
        _t1460 = _t1461
    end
    prediction767 = _t1460
    if prediction767 == 1
        uint128769 = consume_terminal!(parser, "UINT128")
        _t1462 = Proto.RelationId(uint128769.low, uint128769.high)
    else
        if prediction767 == 0
            consume_literal!(parser, ":")
            symbol768 = consume_terminal!(parser, "SYMBOL")
            _t1463 = relation_id_from_string(parser, symbol768)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1462 = _t1463
    end
    result771 = _t1462
    record_span!(parser, span_start770, "RelationId")
    return result771
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start774 = span_start(parser)
    consume_literal!(parser, "(")
    _t1464 = parse_bindings(parser)
    bindings772 = _t1464
    _t1465 = parse_formula(parser)
    formula773 = _t1465
    consume_literal!(parser, ")")
    _t1466 = Proto.Abstraction(vars=vcat(bindings772[1], !isnothing(bindings772[2]) ? bindings772[2] : []), value=formula773)
    result775 = _t1466
    record_span!(parser, span_start774, "Abstraction")
    return result775
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs776 = Proto.Binding[]
    cond777 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond777
        _t1467 = parse_binding(parser)
        item778 = _t1467
        push!(xs776, item778)
        cond777 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings779 = xs776
    if match_lookahead_literal(parser, "|", 0)
        _t1469 = parse_value_bindings(parser)
        _t1468 = _t1469
    else
        _t1468 = nothing
    end
    value_bindings780 = _t1468
    consume_literal!(parser, "]")
    return (bindings779, (!isnothing(value_bindings780) ? value_bindings780 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start783 = span_start(parser)
    symbol781 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1470 = parse_type(parser)
    type782 = _t1470
    _t1471 = Proto.Var(name=symbol781)
    _t1472 = Proto.Binding(var=_t1471, var"#type"=type782)
    result784 = _t1472
    record_span!(parser, span_start783, "Binding")
    return result784
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start800 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1473 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1474 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1475 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1476 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1477 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1478 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1479 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1480 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1481 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1482 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1483 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1484 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1485 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1486 = 9
                                                        else
                                                            _t1486 = -1
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
            _t1474 = _t1475
        end
        _t1473 = _t1474
    end
    prediction785 = _t1473
    if prediction785 == 13
        _t1488 = parse_uint32_type(parser)
        uint32_type799 = _t1488
        _t1489 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type799))
        _t1487 = _t1489
    else
        if prediction785 == 12
            _t1491 = parse_float32_type(parser)
            float32_type798 = _t1491
            _t1492 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type798))
            _t1490 = _t1492
        else
            if prediction785 == 11
                _t1494 = parse_int32_type(parser)
                int32_type797 = _t1494
                _t1495 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type797))
                _t1493 = _t1495
            else
                if prediction785 == 10
                    _t1497 = parse_boolean_type(parser)
                    boolean_type796 = _t1497
                    _t1498 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type796))
                    _t1496 = _t1498
                else
                    if prediction785 == 9
                        _t1500 = parse_decimal_type(parser)
                        decimal_type795 = _t1500
                        _t1501 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type795))
                        _t1499 = _t1501
                    else
                        if prediction785 == 8
                            _t1503 = parse_missing_type(parser)
                            missing_type794 = _t1503
                            _t1504 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type794))
                            _t1502 = _t1504
                        else
                            if prediction785 == 7
                                _t1506 = parse_datetime_type(parser)
                                datetime_type793 = _t1506
                                _t1507 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type793))
                                _t1505 = _t1507
                            else
                                if prediction785 == 6
                                    _t1509 = parse_date_type(parser)
                                    date_type792 = _t1509
                                    _t1510 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type792))
                                    _t1508 = _t1510
                                else
                                    if prediction785 == 5
                                        _t1512 = parse_int128_type(parser)
                                        int128_type791 = _t1512
                                        _t1513 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type791))
                                        _t1511 = _t1513
                                    else
                                        if prediction785 == 4
                                            _t1515 = parse_uint128_type(parser)
                                            uint128_type790 = _t1515
                                            _t1516 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type790))
                                            _t1514 = _t1516
                                        else
                                            if prediction785 == 3
                                                _t1518 = parse_float_type(parser)
                                                float_type789 = _t1518
                                                _t1519 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type789))
                                                _t1517 = _t1519
                                            else
                                                if prediction785 == 2
                                                    _t1521 = parse_int_type(parser)
                                                    int_type788 = _t1521
                                                    _t1522 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type788))
                                                    _t1520 = _t1522
                                                else
                                                    if prediction785 == 1
                                                        _t1524 = parse_string_type(parser)
                                                        string_type787 = _t1524
                                                        _t1525 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type787))
                                                        _t1523 = _t1525
                                                    else
                                                        if prediction785 == 0
                                                            _t1527 = parse_unspecified_type(parser)
                                                            unspecified_type786 = _t1527
                                                            _t1528 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type786))
                                                            _t1526 = _t1528
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1523 = _t1526
                                                    end
                                                    _t1520 = _t1523
                                                end
                                                _t1517 = _t1520
                                            end
                                            _t1514 = _t1517
                                        end
                                        _t1511 = _t1514
                                    end
                                    _t1508 = _t1511
                                end
                                _t1505 = _t1508
                            end
                            _t1502 = _t1505
                        end
                        _t1499 = _t1502
                    end
                    _t1496 = _t1499
                end
                _t1493 = _t1496
            end
            _t1490 = _t1493
        end
        _t1487 = _t1490
    end
    result801 = _t1487
    record_span!(parser, span_start800, "Type")
    return result801
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start802 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1529 = Proto.UnspecifiedType()
    result803 = _t1529
    record_span!(parser, span_start802, "UnspecifiedType")
    return result803
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start804 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1530 = Proto.StringType()
    result805 = _t1530
    record_span!(parser, span_start804, "StringType")
    return result805
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start806 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1531 = Proto.IntType()
    result807 = _t1531
    record_span!(parser, span_start806, "IntType")
    return result807
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start808 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1532 = Proto.FloatType()
    result809 = _t1532
    record_span!(parser, span_start808, "FloatType")
    return result809
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start810 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1533 = Proto.UInt128Type()
    result811 = _t1533
    record_span!(parser, span_start810, "UInt128Type")
    return result811
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start812 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1534 = Proto.Int128Type()
    result813 = _t1534
    record_span!(parser, span_start812, "Int128Type")
    return result813
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start814 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1535 = Proto.DateType()
    result815 = _t1535
    record_span!(parser, span_start814, "DateType")
    return result815
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start816 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1536 = Proto.DateTimeType()
    result817 = _t1536
    record_span!(parser, span_start816, "DateTimeType")
    return result817
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start818 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1537 = Proto.MissingType()
    result819 = _t1537
    record_span!(parser, span_start818, "MissingType")
    return result819
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start822 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int820 = consume_terminal!(parser, "INT")
    int_3821 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1538 = Proto.DecimalType(precision=Int32(int820), scale=Int32(int_3821))
    result823 = _t1538
    record_span!(parser, span_start822, "DecimalType")
    return result823
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start824 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1539 = Proto.BooleanType()
    result825 = _t1539
    record_span!(parser, span_start824, "BooleanType")
    return result825
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start826 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1540 = Proto.Int32Type()
    result827 = _t1540
    record_span!(parser, span_start826, "Int32Type")
    return result827
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start828 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1541 = Proto.Float32Type()
    result829 = _t1541
    record_span!(parser, span_start828, "Float32Type")
    return result829
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start830 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1542 = Proto.UInt32Type()
    result831 = _t1542
    record_span!(parser, span_start830, "UInt32Type")
    return result831
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs832 = Proto.Binding[]
    cond833 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond833
        _t1543 = parse_binding(parser)
        item834 = _t1543
        push!(xs832, item834)
        cond833 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings835 = xs832
    return bindings835
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start850 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1545 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1546 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1547 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1548 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1549 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1550 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1551 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1552 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1553 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1554 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1555 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1556 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1557 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1558 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1559 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1560 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1561 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1562 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1563 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1564 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1565 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1566 = 10
                                                                                            else
                                                                                                _t1566 = -1
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
            end
            _t1545 = _t1546
        end
        _t1544 = _t1545
    else
        _t1544 = -1
    end
    prediction836 = _t1544
    if prediction836 == 12
        _t1568 = parse_cast(parser)
        cast849 = _t1568
        _t1569 = Proto.Formula(formula_type=OneOf(:cast, cast849))
        _t1567 = _t1569
    else
        if prediction836 == 11
            _t1571 = parse_rel_atom(parser)
            rel_atom848 = _t1571
            _t1572 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom848))
            _t1570 = _t1572
        else
            if prediction836 == 10
                _t1574 = parse_primitive(parser)
                primitive847 = _t1574
                _t1575 = Proto.Formula(formula_type=OneOf(:primitive, primitive847))
                _t1573 = _t1575
            else
                if prediction836 == 9
                    _t1577 = parse_pragma(parser)
                    pragma846 = _t1577
                    _t1578 = Proto.Formula(formula_type=OneOf(:pragma, pragma846))
                    _t1576 = _t1578
                else
                    if prediction836 == 8
                        _t1580 = parse_atom(parser)
                        atom845 = _t1580
                        _t1581 = Proto.Formula(formula_type=OneOf(:atom, atom845))
                        _t1579 = _t1581
                    else
                        if prediction836 == 7
                            _t1583 = parse_ffi(parser)
                            ffi844 = _t1583
                            _t1584 = Proto.Formula(formula_type=OneOf(:ffi, ffi844))
                            _t1582 = _t1584
                        else
                            if prediction836 == 6
                                _t1586 = parse_not(parser)
                                not843 = _t1586
                                _t1587 = Proto.Formula(formula_type=OneOf(:not, not843))
                                _t1585 = _t1587
                            else
                                if prediction836 == 5
                                    _t1589 = parse_disjunction(parser)
                                    disjunction842 = _t1589
                                    _t1590 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction842))
                                    _t1588 = _t1590
                                else
                                    if prediction836 == 4
                                        _t1592 = parse_conjunction(parser)
                                        conjunction841 = _t1592
                                        _t1593 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction841))
                                        _t1591 = _t1593
                                    else
                                        if prediction836 == 3
                                            _t1595 = parse_reduce(parser)
                                            reduce840 = _t1595
                                            _t1596 = Proto.Formula(formula_type=OneOf(:reduce, reduce840))
                                            _t1594 = _t1596
                                        else
                                            if prediction836 == 2
                                                _t1598 = parse_exists(parser)
                                                exists839 = _t1598
                                                _t1599 = Proto.Formula(formula_type=OneOf(:exists, exists839))
                                                _t1597 = _t1599
                                            else
                                                if prediction836 == 1
                                                    _t1601 = parse_false(parser)
                                                    false838 = _t1601
                                                    _t1602 = Proto.Formula(formula_type=OneOf(:disjunction, false838))
                                                    _t1600 = _t1602
                                                else
                                                    if prediction836 == 0
                                                        _t1604 = parse_true(parser)
                                                        true837 = _t1604
                                                        _t1605 = Proto.Formula(formula_type=OneOf(:conjunction, true837))
                                                        _t1603 = _t1605
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
                    _t1576 = _t1579
                end
                _t1573 = _t1576
            end
            _t1570 = _t1573
        end
        _t1567 = _t1570
    end
    result851 = _t1567
    record_span!(parser, span_start850, "Formula")
    return result851
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start852 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1606 = Proto.Conjunction(args=Proto.Formula[])
    result853 = _t1606
    record_span!(parser, span_start852, "Conjunction")
    return result853
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start854 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1607 = Proto.Disjunction(args=Proto.Formula[])
    result855 = _t1607
    record_span!(parser, span_start854, "Disjunction")
    return result855
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start858 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1608 = parse_bindings(parser)
    bindings856 = _t1608
    _t1609 = parse_formula(parser)
    formula857 = _t1609
    consume_literal!(parser, ")")
    _t1610 = Proto.Abstraction(vars=vcat(bindings856[1], !isnothing(bindings856[2]) ? bindings856[2] : []), value=formula857)
    _t1611 = Proto.Exists(body=_t1610)
    result859 = _t1611
    record_span!(parser, span_start858, "Exists")
    return result859
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start863 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1612 = parse_abstraction(parser)
    abstraction860 = _t1612
    _t1613 = parse_abstraction(parser)
    abstraction_3861 = _t1613
    _t1614 = parse_terms(parser)
    terms862 = _t1614
    consume_literal!(parser, ")")
    _t1615 = Proto.Reduce(op=abstraction860, body=abstraction_3861, terms=terms862)
    result864 = _t1615
    record_span!(parser, span_start863, "Reduce")
    return result864
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs865 = Proto.Term[]
    cond866 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond866
        _t1616 = parse_term(parser)
        item867 = _t1616
        push!(xs865, item867)
        cond866 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms868 = xs865
    consume_literal!(parser, ")")
    return terms868
end

function parse_term(parser::ParserState)::Proto.Term
    span_start872 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1617 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1618 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1619 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1620 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1621 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1622 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1623 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1624 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1625 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1626 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1627 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1628 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1629 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1630 = 1
                                                        else
                                                            _t1630 = -1
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
    prediction869 = _t1617
    if prediction869 == 1
        _t1632 = parse_value(parser)
        value871 = _t1632
        _t1633 = Proto.Term(term_type=OneOf(:constant, value871))
        _t1631 = _t1633
    else
        if prediction869 == 0
            _t1635 = parse_var(parser)
            var870 = _t1635
            _t1636 = Proto.Term(term_type=OneOf(:var, var870))
            _t1634 = _t1636
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1631 = _t1634
    end
    result873 = _t1631
    record_span!(parser, span_start872, "Term")
    return result873
end

function parse_var(parser::ParserState)::Proto.Var
    span_start875 = span_start(parser)
    symbol874 = consume_terminal!(parser, "SYMBOL")
    _t1637 = Proto.Var(name=symbol874)
    result876 = _t1637
    record_span!(parser, span_start875, "Var")
    return result876
end

function parse_value(parser::ParserState)::Proto.Value
    span_start890 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1638 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1639 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1640 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1642 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1643 = 0
                        else
                            _t1643 = -1
                        end
                        _t1642 = _t1643
                    end
                    _t1641 = _t1642
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1644 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1645 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1646 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1647 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1648 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1649 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1650 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1651 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1652 = 10
                                                    else
                                                        _t1652 = -1
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
                    _t1641 = _t1644
                end
                _t1640 = _t1641
            end
            _t1639 = _t1640
        end
        _t1638 = _t1639
    end
    prediction877 = _t1638
    if prediction877 == 12
        _t1654 = parse_boolean_value(parser)
        boolean_value889 = _t1654
        _t1655 = Proto.Value(value=OneOf(:boolean_value, boolean_value889))
        _t1653 = _t1655
    else
        if prediction877 == 11
            consume_literal!(parser, "missing")
            _t1657 = Proto.MissingValue()
            _t1658 = Proto.Value(value=OneOf(:missing_value, _t1657))
            _t1656 = _t1658
        else
            if prediction877 == 10
                formatted_decimal888 = consume_terminal!(parser, "DECIMAL")
                _t1660 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal888))
                _t1659 = _t1660
            else
                if prediction877 == 9
                    formatted_int128887 = consume_terminal!(parser, "INT128")
                    _t1662 = Proto.Value(value=OneOf(:int128_value, formatted_int128887))
                    _t1661 = _t1662
                else
                    if prediction877 == 8
                        formatted_uint128886 = consume_terminal!(parser, "UINT128")
                        _t1664 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128886))
                        _t1663 = _t1664
                    else
                        if prediction877 == 7
                            formatted_uint32885 = consume_terminal!(parser, "UINT32")
                            _t1666 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32885))
                            _t1665 = _t1666
                        else
                            if prediction877 == 6
                                formatted_float884 = consume_terminal!(parser, "FLOAT")
                                _t1668 = Proto.Value(value=OneOf(:float_value, formatted_float884))
                                _t1667 = _t1668
                            else
                                if prediction877 == 5
                                    formatted_float32883 = consume_terminal!(parser, "FLOAT32")
                                    _t1670 = Proto.Value(value=OneOf(:float32_value, formatted_float32883))
                                    _t1669 = _t1670
                                else
                                    if prediction877 == 4
                                        formatted_int882 = consume_terminal!(parser, "INT")
                                        _t1672 = Proto.Value(value=OneOf(:int_value, formatted_int882))
                                        _t1671 = _t1672
                                    else
                                        if prediction877 == 3
                                            formatted_int32881 = consume_terminal!(parser, "INT32")
                                            _t1674 = Proto.Value(value=OneOf(:int32_value, formatted_int32881))
                                            _t1673 = _t1674
                                        else
                                            if prediction877 == 2
                                                formatted_string880 = consume_terminal!(parser, "STRING")
                                                _t1676 = Proto.Value(value=OneOf(:string_value, formatted_string880))
                                                _t1675 = _t1676
                                            else
                                                if prediction877 == 1
                                                    _t1678 = parse_datetime(parser)
                                                    datetime879 = _t1678
                                                    _t1679 = Proto.Value(value=OneOf(:datetime_value, datetime879))
                                                    _t1677 = _t1679
                                                else
                                                    if prediction877 == 0
                                                        _t1681 = parse_date(parser)
                                                        date878 = _t1681
                                                        _t1682 = Proto.Value(value=OneOf(:date_value, date878))
                                                        _t1680 = _t1682
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1677 = _t1680
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
                _t1659 = _t1661
            end
            _t1656 = _t1659
        end
        _t1653 = _t1656
    end
    result891 = _t1653
    record_span!(parser, span_start890, "Value")
    return result891
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start895 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int892 = consume_terminal!(parser, "INT")
    formatted_int_3893 = consume_terminal!(parser, "INT")
    formatted_int_4894 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1683 = Proto.DateValue(year=Int32(formatted_int892), month=Int32(formatted_int_3893), day=Int32(formatted_int_4894))
    result896 = _t1683
    record_span!(parser, span_start895, "DateValue")
    return result896
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start904 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int897 = consume_terminal!(parser, "INT")
    formatted_int_3898 = consume_terminal!(parser, "INT")
    formatted_int_4899 = consume_terminal!(parser, "INT")
    formatted_int_5900 = consume_terminal!(parser, "INT")
    formatted_int_6901 = consume_terminal!(parser, "INT")
    formatted_int_7902 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1684 = consume_terminal!(parser, "INT")
    else
        _t1684 = nothing
    end
    formatted_int_8903 = _t1684
    consume_literal!(parser, ")")
    _t1685 = Proto.DateTimeValue(year=Int32(formatted_int897), month=Int32(formatted_int_3898), day=Int32(formatted_int_4899), hour=Int32(formatted_int_5900), minute=Int32(formatted_int_6901), second=Int32(formatted_int_7902), microsecond=Int32((!isnothing(formatted_int_8903) ? formatted_int_8903 : 0)))
    result905 = _t1685
    record_span!(parser, span_start904, "DateTimeValue")
    return result905
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start910 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs906 = Proto.Formula[]
    cond907 = match_lookahead_literal(parser, "(", 0)
    while cond907
        _t1686 = parse_formula(parser)
        item908 = _t1686
        push!(xs906, item908)
        cond907 = match_lookahead_literal(parser, "(", 0)
    end
    formulas909 = xs906
    consume_literal!(parser, ")")
    _t1687 = Proto.Conjunction(args=formulas909)
    result911 = _t1687
    record_span!(parser, span_start910, "Conjunction")
    return result911
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start916 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs912 = Proto.Formula[]
    cond913 = match_lookahead_literal(parser, "(", 0)
    while cond913
        _t1688 = parse_formula(parser)
        item914 = _t1688
        push!(xs912, item914)
        cond913 = match_lookahead_literal(parser, "(", 0)
    end
    formulas915 = xs912
    consume_literal!(parser, ")")
    _t1689 = Proto.Disjunction(args=formulas915)
    result917 = _t1689
    record_span!(parser, span_start916, "Disjunction")
    return result917
end

function parse_not(parser::ParserState)::Proto.Not
    span_start919 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1690 = parse_formula(parser)
    formula918 = _t1690
    consume_literal!(parser, ")")
    _t1691 = Proto.Not(arg=formula918)
    result920 = _t1691
    record_span!(parser, span_start919, "Not")
    return result920
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start924 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1692 = parse_name(parser)
    name921 = _t1692
    _t1693 = parse_ffi_args(parser)
    ffi_args922 = _t1693
    _t1694 = parse_terms(parser)
    terms923 = _t1694
    consume_literal!(parser, ")")
    _t1695 = Proto.FFI(name=name921, args=ffi_args922, terms=terms923)
    result925 = _t1695
    record_span!(parser, span_start924, "FFI")
    return result925
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol926 = consume_terminal!(parser, "SYMBOL")
    return symbol926
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs927 = Proto.Abstraction[]
    cond928 = match_lookahead_literal(parser, "(", 0)
    while cond928
        _t1696 = parse_abstraction(parser)
        item929 = _t1696
        push!(xs927, item929)
        cond928 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions930 = xs927
    consume_literal!(parser, ")")
    return abstractions930
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start936 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1697 = parse_relation_id(parser)
    relation_id931 = _t1697
    xs932 = Proto.Term[]
    cond933 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond933
        _t1698 = parse_term(parser)
        item934 = _t1698
        push!(xs932, item934)
        cond933 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms935 = xs932
    consume_literal!(parser, ")")
    _t1699 = Proto.Atom(name=relation_id931, terms=terms935)
    result937 = _t1699
    record_span!(parser, span_start936, "Atom")
    return result937
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start943 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1700 = parse_name(parser)
    name938 = _t1700
    xs939 = Proto.Term[]
    cond940 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond940
        _t1701 = parse_term(parser)
        item941 = _t1701
        push!(xs939, item941)
        cond940 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms942 = xs939
    consume_literal!(parser, ")")
    _t1702 = Proto.Pragma(name=name938, terms=terms942)
    result944 = _t1702
    record_span!(parser, span_start943, "Pragma")
    return result944
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start960 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1704 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1705 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1706 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1707 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1708 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1709 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1710 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1711 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1712 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1713 = 7
                                            else
                                                _t1713 = -1
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
            end
            _t1704 = _t1705
        end
        _t1703 = _t1704
    else
        _t1703 = -1
    end
    prediction945 = _t1703
    if prediction945 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1715 = parse_name(parser)
        name955 = _t1715
        xs956 = Proto.RelTerm[]
        cond957 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond957
            _t1716 = parse_rel_term(parser)
            item958 = _t1716
            push!(xs956, item958)
            cond957 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms959 = xs956
        consume_literal!(parser, ")")
        _t1717 = Proto.Primitive(name=name955, terms=rel_terms959)
        _t1714 = _t1717
    else
        if prediction945 == 8
            _t1719 = parse_divide(parser)
            divide954 = _t1719
            _t1718 = divide954
        else
            if prediction945 == 7
                _t1721 = parse_multiply(parser)
                multiply953 = _t1721
                _t1720 = multiply953
            else
                if prediction945 == 6
                    _t1723 = parse_minus(parser)
                    minus952 = _t1723
                    _t1722 = minus952
                else
                    if prediction945 == 5
                        _t1725 = parse_add(parser)
                        add951 = _t1725
                        _t1724 = add951
                    else
                        if prediction945 == 4
                            _t1727 = parse_gt_eq(parser)
                            gt_eq950 = _t1727
                            _t1726 = gt_eq950
                        else
                            if prediction945 == 3
                                _t1729 = parse_gt(parser)
                                gt949 = _t1729
                                _t1728 = gt949
                            else
                                if prediction945 == 2
                                    _t1731 = parse_lt_eq(parser)
                                    lt_eq948 = _t1731
                                    _t1730 = lt_eq948
                                else
                                    if prediction945 == 1
                                        _t1733 = parse_lt(parser)
                                        lt947 = _t1733
                                        _t1732 = lt947
                                    else
                                        if prediction945 == 0
                                            _t1735 = parse_eq(parser)
                                            eq946 = _t1735
                                            _t1734 = eq946
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
            _t1718 = _t1720
        end
        _t1714 = _t1718
    end
    result961 = _t1714
    record_span!(parser, span_start960, "Primitive")
    return result961
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start964 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1736 = parse_term(parser)
    term962 = _t1736
    _t1737 = parse_term(parser)
    term_3963 = _t1737
    consume_literal!(parser, ")")
    _t1738 = Proto.RelTerm(rel_term_type=OneOf(:term, term962))
    _t1739 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3963))
    _t1740 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1738, _t1739])
    result965 = _t1740
    record_span!(parser, span_start964, "Primitive")
    return result965
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start968 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1741 = parse_term(parser)
    term966 = _t1741
    _t1742 = parse_term(parser)
    term_3967 = _t1742
    consume_literal!(parser, ")")
    _t1743 = Proto.RelTerm(rel_term_type=OneOf(:term, term966))
    _t1744 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3967))
    _t1745 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1743, _t1744])
    result969 = _t1745
    record_span!(parser, span_start968, "Primitive")
    return result969
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start972 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1746 = parse_term(parser)
    term970 = _t1746
    _t1747 = parse_term(parser)
    term_3971 = _t1747
    consume_literal!(parser, ")")
    _t1748 = Proto.RelTerm(rel_term_type=OneOf(:term, term970))
    _t1749 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3971))
    _t1750 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1748, _t1749])
    result973 = _t1750
    record_span!(parser, span_start972, "Primitive")
    return result973
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start976 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1751 = parse_term(parser)
    term974 = _t1751
    _t1752 = parse_term(parser)
    term_3975 = _t1752
    consume_literal!(parser, ")")
    _t1753 = Proto.RelTerm(rel_term_type=OneOf(:term, term974))
    _t1754 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3975))
    _t1755 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1753, _t1754])
    result977 = _t1755
    record_span!(parser, span_start976, "Primitive")
    return result977
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1756 = parse_term(parser)
    term978 = _t1756
    _t1757 = parse_term(parser)
    term_3979 = _t1757
    consume_literal!(parser, ")")
    _t1758 = Proto.RelTerm(rel_term_type=OneOf(:term, term978))
    _t1759 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3979))
    _t1760 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1758, _t1759])
    result981 = _t1760
    record_span!(parser, span_start980, "Primitive")
    return result981
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start985 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1761 = parse_term(parser)
    term982 = _t1761
    _t1762 = parse_term(parser)
    term_3983 = _t1762
    _t1763 = parse_term(parser)
    term_4984 = _t1763
    consume_literal!(parser, ")")
    _t1764 = Proto.RelTerm(rel_term_type=OneOf(:term, term982))
    _t1765 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3983))
    _t1766 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4984))
    _t1767 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1764, _t1765, _t1766])
    result986 = _t1767
    record_span!(parser, span_start985, "Primitive")
    return result986
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start990 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1768 = parse_term(parser)
    term987 = _t1768
    _t1769 = parse_term(parser)
    term_3988 = _t1769
    _t1770 = parse_term(parser)
    term_4989 = _t1770
    consume_literal!(parser, ")")
    _t1771 = Proto.RelTerm(rel_term_type=OneOf(:term, term987))
    _t1772 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3988))
    _t1773 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4989))
    _t1774 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1771, _t1772, _t1773])
    result991 = _t1774
    record_span!(parser, span_start990, "Primitive")
    return result991
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start995 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1775 = parse_term(parser)
    term992 = _t1775
    _t1776 = parse_term(parser)
    term_3993 = _t1776
    _t1777 = parse_term(parser)
    term_4994 = _t1777
    consume_literal!(parser, ")")
    _t1778 = Proto.RelTerm(rel_term_type=OneOf(:term, term992))
    _t1779 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3993))
    _t1780 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4994))
    _t1781 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1778, _t1779, _t1780])
    result996 = _t1781
    record_span!(parser, span_start995, "Primitive")
    return result996
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start1000 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1782 = parse_term(parser)
    term997 = _t1782
    _t1783 = parse_term(parser)
    term_3998 = _t1783
    _t1784 = parse_term(parser)
    term_4999 = _t1784
    consume_literal!(parser, ")")
    _t1785 = Proto.RelTerm(rel_term_type=OneOf(:term, term997))
    _t1786 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3998))
    _t1787 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4999))
    _t1788 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1785, _t1786, _t1787])
    result1001 = _t1788
    record_span!(parser, span_start1000, "Primitive")
    return result1001
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start1005 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1789 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1790 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1791 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1792 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1793 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1794 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1795 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1796 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1797 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1798 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1799 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1800 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1801 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1802 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1803 = 1
                                                            else
                                                                _t1803 = -1
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
            _t1790 = _t1791
        end
        _t1789 = _t1790
    end
    prediction1002 = _t1789
    if prediction1002 == 1
        _t1805 = parse_term(parser)
        term1004 = _t1805
        _t1806 = Proto.RelTerm(rel_term_type=OneOf(:term, term1004))
        _t1804 = _t1806
    else
        if prediction1002 == 0
            _t1808 = parse_specialized_value(parser)
            specialized_value1003 = _t1808
            _t1809 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1003))
            _t1807 = _t1809
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1804 = _t1807
    end
    result1006 = _t1804
    record_span!(parser, span_start1005, "RelTerm")
    return result1006
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start1008 = span_start(parser)
    consume_literal!(parser, "#")
    _t1810 = parse_raw_value(parser)
    raw_value1007 = _t1810
    result1009 = raw_value1007
    record_span!(parser, span_start1008, "Value")
    return result1009
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1015 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1811 = parse_name(parser)
    name1010 = _t1811
    xs1011 = Proto.RelTerm[]
    cond1012 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1012
        _t1812 = parse_rel_term(parser)
        item1013 = _t1812
        push!(xs1011, item1013)
        cond1012 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1014 = xs1011
    consume_literal!(parser, ")")
    _t1813 = Proto.RelAtom(name=name1010, terms=rel_terms1014)
    result1016 = _t1813
    record_span!(parser, span_start1015, "RelAtom")
    return result1016
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1019 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1814 = parse_term(parser)
    term1017 = _t1814
    _t1815 = parse_term(parser)
    term_31018 = _t1815
    consume_literal!(parser, ")")
    _t1816 = Proto.Cast(input=term1017, result=term_31018)
    result1020 = _t1816
    record_span!(parser, span_start1019, "Cast")
    return result1020
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1021 = Proto.Attribute[]
    cond1022 = match_lookahead_literal(parser, "(", 0)
    while cond1022
        _t1817 = parse_attribute(parser)
        item1023 = _t1817
        push!(xs1021, item1023)
        cond1022 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1024 = xs1021
    consume_literal!(parser, ")")
    return attributes1024
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1030 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1818 = parse_name(parser)
    name1025 = _t1818
    xs1026 = Proto.Value[]
    cond1027 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1027
        _t1819 = parse_raw_value(parser)
        item1028 = _t1819
        push!(xs1026, item1028)
        cond1027 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1029 = xs1026
    consume_literal!(parser, ")")
    _t1820 = Proto.Attribute(name=name1025, args=raw_values1029)
    result1031 = _t1820
    record_span!(parser, span_start1030, "Attribute")
    return result1031
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1037 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1032 = Proto.RelationId[]
    cond1033 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1033
        _t1821 = parse_relation_id(parser)
        item1034 = _t1821
        push!(xs1032, item1034)
        cond1033 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1035 = xs1032
    _t1822 = parse_script(parser)
    script1036 = _t1822
    consume_literal!(parser, ")")
    _t1823 = Proto.Algorithm(var"#global"=relation_ids1035, body=script1036)
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
    span_start1052 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1839 = parse_init(parser)
    init1050 = _t1839
    _t1840 = parse_script(parser)
    script1051 = _t1840
    consume_literal!(parser, ")")
    _t1841 = Proto.Loop(init=init1050, body=script1051)
    result1053 = _t1841
    record_span!(parser, span_start1052, "Loop")
    return result1053
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1054 = Proto.Instruction[]
    cond1055 = match_lookahead_literal(parser, "(", 0)
    while cond1055
        _t1842 = parse_instruction(parser)
        item1056 = _t1842
        push!(xs1054, item1056)
        cond1055 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1057 = xs1054
    consume_literal!(parser, ")")
    return instructions1057
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1064 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1844 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1845 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1846 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1847 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1848 = 0
                        else
                            _t1848 = -1
                        end
                        _t1847 = _t1848
                    end
                    _t1846 = _t1847
                end
                _t1845 = _t1846
            end
            _t1844 = _t1845
        end
        _t1843 = _t1844
    else
        _t1843 = -1
    end
    prediction1058 = _t1843
    if prediction1058 == 4
        _t1850 = parse_monus_def(parser)
        monus_def1063 = _t1850
        _t1851 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1063))
        _t1849 = _t1851
    else
        if prediction1058 == 3
            _t1853 = parse_monoid_def(parser)
            monoid_def1062 = _t1853
            _t1854 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1062))
            _t1852 = _t1854
        else
            if prediction1058 == 2
                _t1856 = parse_break(parser)
                break1061 = _t1856
                _t1857 = Proto.Instruction(instr_type=OneOf(:var"#break", break1061))
                _t1855 = _t1857
            else
                if prediction1058 == 1
                    _t1859 = parse_upsert(parser)
                    upsert1060 = _t1859
                    _t1860 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1060))
                    _t1858 = _t1860
                else
                    if prediction1058 == 0
                        _t1862 = parse_assign(parser)
                        assign1059 = _t1862
                        _t1863 = Proto.Instruction(instr_type=OneOf(:assign, assign1059))
                        _t1861 = _t1863
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1858 = _t1861
                end
                _t1855 = _t1858
            end
            _t1852 = _t1855
        end
        _t1849 = _t1852
    end
    result1065 = _t1849
    record_span!(parser, span_start1064, "Instruction")
    return result1065
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1069 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1864 = parse_relation_id(parser)
    relation_id1066 = _t1864
    _t1865 = parse_abstraction(parser)
    abstraction1067 = _t1865
    if match_lookahead_literal(parser, "(", 0)
        _t1867 = parse_attrs(parser)
        _t1866 = _t1867
    else
        _t1866 = nothing
    end
    attrs1068 = _t1866
    consume_literal!(parser, ")")
    _t1868 = Proto.Assign(name=relation_id1066, body=abstraction1067, attrs=(!isnothing(attrs1068) ? attrs1068 : Proto.Attribute[]))
    result1070 = _t1868
    record_span!(parser, span_start1069, "Assign")
    return result1070
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1074 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1869 = parse_relation_id(parser)
    relation_id1071 = _t1869
    _t1870 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1072 = _t1870
    if match_lookahead_literal(parser, "(", 0)
        _t1872 = parse_attrs(parser)
        _t1871 = _t1872
    else
        _t1871 = nothing
    end
    attrs1073 = _t1871
    consume_literal!(parser, ")")
    _t1873 = Proto.Upsert(name=relation_id1071, body=abstraction_with_arity1072[1], attrs=(!isnothing(attrs1073) ? attrs1073 : Proto.Attribute[]), value_arity=abstraction_with_arity1072[2])
    result1075 = _t1873
    record_span!(parser, span_start1074, "Upsert")
    return result1075
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1874 = parse_bindings(parser)
    bindings1076 = _t1874
    _t1875 = parse_formula(parser)
    formula1077 = _t1875
    consume_literal!(parser, ")")
    _t1876 = Proto.Abstraction(vars=vcat(bindings1076[1], !isnothing(bindings1076[2]) ? bindings1076[2] : []), value=formula1077)
    return (_t1876, length(bindings1076[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1081 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1877 = parse_relation_id(parser)
    relation_id1078 = _t1877
    _t1878 = parse_abstraction(parser)
    abstraction1079 = _t1878
    if match_lookahead_literal(parser, "(", 0)
        _t1880 = parse_attrs(parser)
        _t1879 = _t1880
    else
        _t1879 = nothing
    end
    attrs1080 = _t1879
    consume_literal!(parser, ")")
    _t1881 = Proto.Break(name=relation_id1078, body=abstraction1079, attrs=(!isnothing(attrs1080) ? attrs1080 : Proto.Attribute[]))
    result1082 = _t1881
    record_span!(parser, span_start1081, "Break")
    return result1082
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1087 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1882 = parse_monoid(parser)
    monoid1083 = _t1882
    _t1883 = parse_relation_id(parser)
    relation_id1084 = _t1883
    _t1884 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1085 = _t1884
    if match_lookahead_literal(parser, "(", 0)
        _t1886 = parse_attrs(parser)
        _t1885 = _t1886
    else
        _t1885 = nothing
    end
    attrs1086 = _t1885
    consume_literal!(parser, ")")
    _t1887 = Proto.MonoidDef(monoid=monoid1083, name=relation_id1084, body=abstraction_with_arity1085[1], attrs=(!isnothing(attrs1086) ? attrs1086 : Proto.Attribute[]), value_arity=abstraction_with_arity1085[2])
    result1088 = _t1887
    record_span!(parser, span_start1087, "MonoidDef")
    return result1088
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1094 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1889 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1890 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1891 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1892 = 2
                    else
                        _t1892 = -1
                    end
                    _t1891 = _t1892
                end
                _t1890 = _t1891
            end
            _t1889 = _t1890
        end
        _t1888 = _t1889
    else
        _t1888 = -1
    end
    prediction1089 = _t1888
    if prediction1089 == 3
        _t1894 = parse_sum_monoid(parser)
        sum_monoid1093 = _t1894
        _t1895 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1093))
        _t1893 = _t1895
    else
        if prediction1089 == 2
            _t1897 = parse_max_monoid(parser)
            max_monoid1092 = _t1897
            _t1898 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1092))
            _t1896 = _t1898
        else
            if prediction1089 == 1
                _t1900 = parse_min_monoid(parser)
                min_monoid1091 = _t1900
                _t1901 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1091))
                _t1899 = _t1901
            else
                if prediction1089 == 0
                    _t1903 = parse_or_monoid(parser)
                    or_monoid1090 = _t1903
                    _t1904 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1090))
                    _t1902 = _t1904
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1899 = _t1902
            end
            _t1896 = _t1899
        end
        _t1893 = _t1896
    end
    result1095 = _t1893
    record_span!(parser, span_start1094, "Monoid")
    return result1095
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1096 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1905 = Proto.OrMonoid()
    result1097 = _t1905
    record_span!(parser, span_start1096, "OrMonoid")
    return result1097
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1099 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1906 = parse_type(parser)
    type1098 = _t1906
    consume_literal!(parser, ")")
    _t1907 = Proto.MinMonoid(var"#type"=type1098)
    result1100 = _t1907
    record_span!(parser, span_start1099, "MinMonoid")
    return result1100
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1102 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1908 = parse_type(parser)
    type1101 = _t1908
    consume_literal!(parser, ")")
    _t1909 = Proto.MaxMonoid(var"#type"=type1101)
    result1103 = _t1909
    record_span!(parser, span_start1102, "MaxMonoid")
    return result1103
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1105 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1910 = parse_type(parser)
    type1104 = _t1910
    consume_literal!(parser, ")")
    _t1911 = Proto.SumMonoid(var"#type"=type1104)
    result1106 = _t1911
    record_span!(parser, span_start1105, "SumMonoid")
    return result1106
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1111 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1912 = parse_monoid(parser)
    monoid1107 = _t1912
    _t1913 = parse_relation_id(parser)
    relation_id1108 = _t1913
    _t1914 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1109 = _t1914
    if match_lookahead_literal(parser, "(", 0)
        _t1916 = parse_attrs(parser)
        _t1915 = _t1916
    else
        _t1915 = nothing
    end
    attrs1110 = _t1915
    consume_literal!(parser, ")")
    _t1917 = Proto.MonusDef(monoid=monoid1107, name=relation_id1108, body=abstraction_with_arity1109[1], attrs=(!isnothing(attrs1110) ? attrs1110 : Proto.Attribute[]), value_arity=abstraction_with_arity1109[2])
    result1112 = _t1917
    record_span!(parser, span_start1111, "MonusDef")
    return result1112
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1117 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1918 = parse_relation_id(parser)
    relation_id1113 = _t1918
    _t1919 = parse_abstraction(parser)
    abstraction1114 = _t1919
    _t1920 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1115 = _t1920
    _t1921 = parse_functional_dependency_values(parser)
    functional_dependency_values1116 = _t1921
    consume_literal!(parser, ")")
    _t1922 = Proto.FunctionalDependency(guard=abstraction1114, keys=functional_dependency_keys1115, values=functional_dependency_values1116)
    _t1923 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1922), name=relation_id1113)
    result1118 = _t1923
    record_span!(parser, span_start1117, "Constraint")
    return result1118
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1119 = Proto.Var[]
    cond1120 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1120
        _t1924 = parse_var(parser)
        item1121 = _t1924
        push!(xs1119, item1121)
        cond1120 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1122 = xs1119
    consume_literal!(parser, ")")
    return vars1122
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1123 = Proto.Var[]
    cond1124 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1124
        _t1925 = parse_var(parser)
        item1125 = _t1925
        push!(xs1123, item1125)
        cond1124 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1126 = xs1123
    consume_literal!(parser, ")")
    return vars1126
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1132 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1927 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1928 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1929 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
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
    else
        _t1926 = -1
    end
    prediction1127 = _t1926
    if prediction1127 == 3
        _t1932 = parse_iceberg_data(parser)
        iceberg_data1131 = _t1932
        _t1933 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1131))
        _t1931 = _t1933
    else
        if prediction1127 == 2
            _t1935 = parse_csv_data(parser)
            csv_data1130 = _t1935
            _t1936 = Proto.Data(data_type=OneOf(:csv_data, csv_data1130))
            _t1934 = _t1936
        else
            if prediction1127 == 1
                _t1938 = parse_betree_relation(parser)
                betree_relation1129 = _t1938
                _t1939 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1129))
                _t1937 = _t1939
            else
                if prediction1127 == 0
                    _t1941 = parse_edb(parser)
                    edb1128 = _t1941
                    _t1942 = Proto.Data(data_type=OneOf(:edb, edb1128))
                    _t1940 = _t1942
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1937 = _t1940
            end
            _t1934 = _t1937
        end
        _t1931 = _t1934
    end
    result1133 = _t1931
    record_span!(parser, span_start1132, "Data")
    return result1133
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1137 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1943 = parse_relation_id(parser)
    relation_id1134 = _t1943
    _t1944 = parse_edb_path(parser)
    edb_path1135 = _t1944
    _t1945 = parse_edb_types(parser)
    edb_types1136 = _t1945
    consume_literal!(parser, ")")
    _t1946 = Proto.EDB(target_id=relation_id1134, path=edb_path1135, types=edb_types1136)
    result1138 = _t1946
    record_span!(parser, span_start1137, "EDB")
    return result1138
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1139 = String[]
    cond1140 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1140
        item1141 = consume_terminal!(parser, "STRING")
        push!(xs1139, item1141)
        cond1140 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1142 = xs1139
    consume_literal!(parser, "]")
    return strings1142
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1143 = Proto.var"#Type"[]
    cond1144 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1144
        _t1947 = parse_type(parser)
        item1145 = _t1947
        push!(xs1143, item1145)
        cond1144 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1146 = xs1143
    consume_literal!(parser, "]")
    return types1146
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1149 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1948 = parse_relation_id(parser)
    relation_id1147 = _t1948
    _t1949 = parse_betree_info(parser)
    betree_info1148 = _t1949
    consume_literal!(parser, ")")
    _t1950 = Proto.BeTreeRelation(name=relation_id1147, relation_info=betree_info1148)
    result1150 = _t1950
    record_span!(parser, span_start1149, "BeTreeRelation")
    return result1150
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1154 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1951 = parse_betree_info_key_types(parser)
    betree_info_key_types1151 = _t1951
    _t1952 = parse_betree_info_value_types(parser)
    betree_info_value_types1152 = _t1952
    _t1953 = parse_config_dict(parser)
    config_dict1153 = _t1953
    consume_literal!(parser, ")")
    _t1954 = construct_betree_info(parser, betree_info_key_types1151, betree_info_value_types1152, config_dict1153)
    result1155 = _t1954
    record_span!(parser, span_start1154, "BeTreeInfo")
    return result1155
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1156 = Proto.var"#Type"[]
    cond1157 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1157
        _t1955 = parse_type(parser)
        item1158 = _t1955
        push!(xs1156, item1158)
        cond1157 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1159 = xs1156
    consume_literal!(parser, ")")
    return types1159
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1160 = Proto.var"#Type"[]
    cond1161 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1161
        _t1956 = parse_type(parser)
        item1162 = _t1956
        push!(xs1160, item1162)
        cond1161 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1163 = xs1160
    consume_literal!(parser, ")")
    return types1163
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1168 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1957 = parse_csvlocator(parser)
    csvlocator1164 = _t1957
    _t1958 = parse_csv_config(parser)
    csv_config1165 = _t1958
    _t1959 = parse_gnf_columns(parser)
    gnf_columns1166 = _t1959
    _t1960 = parse_csv_asof(parser)
    csv_asof1167 = _t1960
    consume_literal!(parser, ")")
    _t1961 = Proto.CSVData(locator=csvlocator1164, config=csv_config1165, columns=gnf_columns1166, asof=csv_asof1167)
    result1169 = _t1961
    record_span!(parser, span_start1168, "CSVData")
    return result1169
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1172 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1963 = parse_csv_locator_paths(parser)
        _t1962 = _t1963
    else
        _t1962 = nothing
    end
    csv_locator_paths1170 = _t1962
    if match_lookahead_literal(parser, "(", 0)
        _t1965 = parse_csv_locator_inline_data(parser)
        _t1964 = _t1965
    else
        _t1964 = nothing
    end
    csv_locator_inline_data1171 = _t1964
    consume_literal!(parser, ")")
    _t1966 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1170) ? csv_locator_paths1170 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1171) ? csv_locator_inline_data1171 : "")))
    result1173 = _t1966
    record_span!(parser, span_start1172, "CSVLocator")
    return result1173
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1174 = String[]
    cond1175 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1175
        item1176 = consume_terminal!(parser, "STRING")
        push!(xs1174, item1176)
        cond1175 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1177 = xs1174
    consume_literal!(parser, ")")
    return strings1177
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1178 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1178
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1180 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1967 = parse_config_dict(parser)
    config_dict1179 = _t1967
    consume_literal!(parser, ")")
    _t1968 = construct_csv_config(parser, config_dict1179)
    result1181 = _t1968
    record_span!(parser, span_start1180, "CSVConfig")
    return result1181
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1182 = Proto.GNFColumn[]
    cond1183 = match_lookahead_literal(parser, "(", 0)
    while cond1183
        _t1969 = parse_gnf_column(parser)
        item1184 = _t1969
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
    _t1970 = parse_gnf_column_path(parser)
    gnf_column_path1186 = _t1970
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1972 = parse_relation_id(parser)
        _t1971 = _t1972
    else
        _t1971 = nothing
    end
    relation_id1187 = _t1971
    consume_literal!(parser, "[")
    xs1188 = Proto.var"#Type"[]
    cond1189 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1189
        _t1973 = parse_type(parser)
        item1190 = _t1973
        push!(xs1188, item1190)
        cond1189 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1191 = xs1188
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1974 = Proto.GNFColumn(column_path=gnf_column_path1186, target_id=relation_id1187, types=types1191)
    result1193 = _t1974
    record_span!(parser, span_start1192, "GNFColumn")
    return result1193
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1975 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1976 = 0
        else
            _t1976 = -1
        end
        _t1975 = _t1976
    end
    prediction1194 = _t1975
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
        _t1977 = strings1199
    else
        if prediction1194 == 0
            string1195 = consume_terminal!(parser, "STRING")
            _t1978 = String[string1195]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1977 = _t1978
    end
    return _t1977
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
    _t1979 = parse_iceberg_locator(parser)
    iceberg_locator1201 = _t1979
    _t1980 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1202 = _t1980
    _t1981 = parse_gnf_columns(parser)
    gnf_columns1203 = _t1981
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1983 = parse_iceberg_from_snapshot(parser)
        _t1982 = _t1983
    else
        _t1982 = nothing
    end
    iceberg_from_snapshot1204 = _t1982
    if match_lookahead_literal(parser, "(", 0)
        _t1985 = parse_iceberg_to_snapshot(parser)
        _t1984 = _t1985
    else
        _t1984 = nothing
    end
    iceberg_to_snapshot1205 = _t1984
    _t1986 = parse_boolean_value(parser)
    boolean_value1206 = _t1986
    consume_literal!(parser, ")")
    _t1987 = construct_iceberg_data(parser, iceberg_locator1201, iceberg_catalog_config1202, gnf_columns1203, iceberg_from_snapshot1204, iceberg_to_snapshot1205, boolean_value1206)
    result1208 = _t1987
    record_span!(parser, span_start1207, "IcebergData")
    return result1208
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1212 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    _t1988 = parse_iceberg_locator_table_name(parser)
    iceberg_locator_table_name1209 = _t1988
    _t1989 = parse_iceberg_locator_namespace(parser)
    iceberg_locator_namespace1210 = _t1989
    _t1990 = parse_iceberg_locator_warehouse(parser)
    iceberg_locator_warehouse1211 = _t1990
    consume_literal!(parser, ")")
    _t1991 = Proto.IcebergLocator(table_name=iceberg_locator_table_name1209, namespace=iceberg_locator_namespace1210, warehouse=iceberg_locator_warehouse1211)
    result1213 = _t1991
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
    _t1992 = parse_iceberg_catalog_uri(parser)
    iceberg_catalog_uri1220 = _t1992
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1994 = parse_iceberg_catalog_config_scope(parser)
        _t1993 = _t1994
    else
        _t1993 = nothing
    end
    iceberg_catalog_config_scope1221 = _t1993
    _t1995 = parse_iceberg_properties(parser)
    iceberg_properties1222 = _t1995
    _t1996 = parse_iceberg_auth_properties(parser)
    iceberg_auth_properties1223 = _t1996
    consume_literal!(parser, ")")
    _t1997 = construct_iceberg_catalog_config(parser, iceberg_catalog_uri1220, iceberg_catalog_config_scope1221, iceberg_properties1222, iceberg_auth_properties1223)
    result1225 = _t1997
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
        _t1998 = parse_iceberg_property_entry(parser)
        item1230 = _t1998
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
        _t1999 = parse_iceberg_masked_property_entry(parser)
        item1236 = _t1999
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
    _t2000 = parse_fragment_id(parser)
    fragment_id1242 = _t2000
    consume_literal!(parser, ")")
    _t2001 = Proto.Undefine(fragment_id=fragment_id1242)
    result1244 = _t2001
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
        _t2002 = parse_relation_id(parser)
        item1247 = _t2002
        push!(xs1245, item1247)
        cond1246 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1248 = xs1245
    consume_literal!(parser, ")")
    _t2003 = Proto.Context(relations=relation_ids1248)
    result1250 = _t2003
    record_span!(parser, span_start1249, "Context")
    return result1250
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1255 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1251 = Proto.SnapshotMapping[]
    cond1252 = match_lookahead_literal(parser, "[", 0)
    while cond1252
        _t2004 = parse_snapshot_mapping(parser)
        item1253 = _t2004
        push!(xs1251, item1253)
        cond1252 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1254 = xs1251
    consume_literal!(parser, ")")
    _t2005 = Proto.Snapshot(mappings=snapshot_mappings1254)
    result1256 = _t2005
    record_span!(parser, span_start1255, "Snapshot")
    return result1256
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1259 = span_start(parser)
    _t2006 = parse_edb_path(parser)
    edb_path1257 = _t2006
    _t2007 = parse_relation_id(parser)
    relation_id1258 = _t2007
    _t2008 = Proto.SnapshotMapping(destination_path=edb_path1257, source_relation=relation_id1258)
    result1260 = _t2008
    record_span!(parser, span_start1259, "SnapshotMapping")
    return result1260
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1261 = Proto.Read[]
    cond1262 = match_lookahead_literal(parser, "(", 0)
    while cond1262
        _t2009 = parse_read(parser)
        item1263 = _t2009
        push!(xs1261, item1263)
        cond1262 = match_lookahead_literal(parser, "(", 0)
    end
    reads1264 = xs1261
    consume_literal!(parser, ")")
    return reads1264
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1271 = span_start(parser)
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
    prediction1265 = _t2010
    if prediction1265 == 4
        _t2018 = parse_export(parser)
        export1270 = _t2018
        _t2019 = Proto.Read(read_type=OneOf(:var"#export", export1270))
        _t2017 = _t2019
    else
        if prediction1265 == 3
            _t2021 = parse_abort(parser)
            abort1269 = _t2021
            _t2022 = Proto.Read(read_type=OneOf(:abort, abort1269))
            _t2020 = _t2022
        else
            if prediction1265 == 2
                _t2024 = parse_what_if(parser)
                what_if1268 = _t2024
                _t2025 = Proto.Read(read_type=OneOf(:what_if, what_if1268))
                _t2023 = _t2025
            else
                if prediction1265 == 1
                    _t2027 = parse_output(parser)
                    output1267 = _t2027
                    _t2028 = Proto.Read(read_type=OneOf(:output, output1267))
                    _t2026 = _t2028
                else
                    if prediction1265 == 0
                        _t2030 = parse_demand(parser)
                        demand1266 = _t2030
                        _t2031 = Proto.Read(read_type=OneOf(:demand, demand1266))
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
    result1272 = _t2017
    record_span!(parser, span_start1271, "Read")
    return result1272
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1274 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2032 = parse_relation_id(parser)
    relation_id1273 = _t2032
    consume_literal!(parser, ")")
    _t2033 = Proto.Demand(relation_id=relation_id1273)
    result1275 = _t2033
    record_span!(parser, span_start1274, "Demand")
    return result1275
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1278 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2034 = parse_name(parser)
    name1276 = _t2034
    _t2035 = parse_relation_id(parser)
    relation_id1277 = _t2035
    consume_literal!(parser, ")")
    _t2036 = Proto.Output(name=name1276, relation_id=relation_id1277)
    result1279 = _t2036
    record_span!(parser, span_start1278, "Output")
    return result1279
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1282 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2037 = parse_name(parser)
    name1280 = _t2037
    _t2038 = parse_epoch(parser)
    epoch1281 = _t2038
    consume_literal!(parser, ")")
    _t2039 = Proto.WhatIf(branch=name1280, epoch=epoch1281)
    result1283 = _t2039
    record_span!(parser, span_start1282, "WhatIf")
    return result1283
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1286 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2041 = parse_name(parser)
        _t2040 = _t2041
    else
        _t2040 = nothing
    end
    name1284 = _t2040
    _t2042 = parse_relation_id(parser)
    relation_id1285 = _t2042
    consume_literal!(parser, ")")
    _t2043 = Proto.Abort(name=(!isnothing(name1284) ? name1284 : "abort"), relation_id=relation_id1285)
    result1287 = _t2043
    record_span!(parser, span_start1286, "Abort")
    return result1287
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1291 = span_start(parser)
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
    prediction1288 = _t2044
    if prediction1288 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2048 = parse_export_iceberg_config(parser)
        export_iceberg_config1290 = _t2048
        consume_literal!(parser, ")")
        _t2049 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1290))
        _t2047 = _t2049
    else
        if prediction1288 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2051 = parse_export_csv_config(parser)
            export_csv_config1289 = _t2051
            consume_literal!(parser, ")")
            _t2052 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1289))
            _t2050 = _t2052
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2047 = _t2050
    end
    result1292 = _t2047
    record_span!(parser, span_start1291, "Export")
    return result1292
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1300 = span_start(parser)
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
    prediction1293 = _t2053
    if prediction1293 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2057 = parse_export_csv_path(parser)
        export_csv_path1297 = _t2057
        _t2058 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1298 = _t2058
        _t2059 = parse_config_dict(parser)
        config_dict1299 = _t2059
        consume_literal!(parser, ")")
        _t2060 = construct_export_csv_config(parser, export_csv_path1297, export_csv_columns_list1298, config_dict1299)
        _t2056 = _t2060
    else
        if prediction1293 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2062 = parse_export_csv_path(parser)
            export_csv_path1294 = _t2062
            _t2063 = parse_export_csv_source(parser)
            export_csv_source1295 = _t2063
            _t2064 = parse_csv_config(parser)
            csv_config1296 = _t2064
            consume_literal!(parser, ")")
            _t2065 = construct_export_csv_config_with_source(parser, export_csv_path1294, export_csv_source1295, csv_config1296)
            _t2061 = _t2065
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2056 = _t2061
    end
    result1301 = _t2056
    record_span!(parser, span_start1300, "ExportCSVConfig")
    return result1301
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1302 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1302
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1309 = span_start(parser)
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
    prediction1303 = _t2066
    if prediction1303 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2070 = parse_relation_id(parser)
        relation_id1308 = _t2070
        consume_literal!(parser, ")")
        _t2071 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1308))
        _t2069 = _t2071
    else
        if prediction1303 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1304 = Proto.ExportCSVColumn[]
            cond1305 = match_lookahead_literal(parser, "(", 0)
            while cond1305
                _t2073 = parse_export_csv_column(parser)
                item1306 = _t2073
                push!(xs1304, item1306)
                cond1305 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1307 = xs1304
            consume_literal!(parser, ")")
            _t2074 = Proto.ExportCSVColumns(columns=export_csv_columns1307)
            _t2075 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2074))
            _t2072 = _t2075
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2069 = _t2072
    end
    result1310 = _t2069
    record_span!(parser, span_start1309, "ExportCSVSource")
    return result1310
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1313 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1311 = consume_terminal!(parser, "STRING")
    _t2076 = parse_relation_id(parser)
    relation_id1312 = _t2076
    consume_literal!(parser, ")")
    _t2077 = Proto.ExportCSVColumn(column_name=string1311, column_data=relation_id1312)
    result1314 = _t2077
    record_span!(parser, span_start1313, "ExportCSVColumn")
    return result1314
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1315 = Proto.ExportCSVColumn[]
    cond1316 = match_lookahead_literal(parser, "(", 0)
    while cond1316
        _t2078 = parse_export_csv_column(parser)
        item1317 = _t2078
        push!(xs1315, item1317)
        cond1316 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1318 = xs1315
    consume_literal!(parser, ")")
    return export_csv_columns1318
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1325 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2079 = parse_iceberg_locator(parser)
    iceberg_locator1319 = _t2079
    _t2080 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1320 = _t2080
    _t2081 = parse_export_iceberg_table_def(parser)
    export_iceberg_table_def1321 = _t2081
    _t2082 = parse_export_iceberg_columns(parser)
    export_iceberg_columns1322 = _t2082
    _t2083 = parse_iceberg_table_properties(parser)
    iceberg_table_properties1323 = _t2083
    if match_lookahead_literal(parser, "{", 0)
        _t2085 = parse_config_dict(parser)
        _t2084 = _t2085
    else
        _t2084 = nothing
    end
    config_dict1324 = _t2084
    consume_literal!(parser, ")")
    _t2086 = construct_export_iceberg_config_full(parser, iceberg_locator1319, iceberg_catalog_config1320, export_iceberg_table_def1321, export_iceberg_columns1322, iceberg_table_properties1323, config_dict1324)
    result1326 = _t2086
    record_span!(parser, span_start1325, "ExportIcebergConfig")
    return result1326
end

function parse_export_iceberg_table_def(parser::ParserState)::Proto.RelationId
    span_start1328 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2087 = parse_relation_id(parser)
    relation_id1327 = _t2087
    consume_literal!(parser, ")")
    result1329 = relation_id1327
    record_span!(parser, span_start1328, "RelationId")
    return result1329
end

function parse_export_iceberg_columns(parser::ParserState)::Vector{Proto.ExportColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1330 = Proto.ExportColumn[]
    cond1331 = match_lookahead_literal(parser, "(", 0)
    while cond1331
        _t2088 = parse_export_iceberg_column(parser)
        item1332 = _t2088
        push!(xs1330, item1332)
        cond1331 = match_lookahead_literal(parser, "(", 0)
    end
    export_iceberg_columns1333 = xs1330
    consume_literal!(parser, ")")
    return export_iceberg_columns1333
end

function parse_export_iceberg_column(parser::ParserState)::Proto.ExportColumn
    span_start1336 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1334 = consume_terminal!(parser, "STRING")
    _t2089 = parse_boolean_value(parser)
    boolean_value1335 = _t2089
    consume_literal!(parser, ")")
    _t2090 = Proto.ExportColumn(name=string1334, nullable=boolean_value1335)
    result1337 = _t2090
    record_span!(parser, span_start1336, "ExportColumn")
    return result1337
end

function parse_iceberg_table_properties(parser::ParserState)::Vector{Tuple{String, String}}
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1338 = Tuple{String, String}[]
    cond1339 = match_lookahead_literal(parser, "(", 0)
    while cond1339
        _t2091 = parse_iceberg_property_entry(parser)
        item1340 = _t2091
        push!(xs1338, item1340)
        cond1339 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1341 = xs1338
    consume_literal!(parser, ")")
    return iceberg_property_entrys1341
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
