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
    ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_./#-]*", scan_symbol),
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
        _t2061 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2062 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2063 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2064 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2065 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2066 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2067 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2068 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2069 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2070 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2070
    _t2071 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2071
    _t2072 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2072
    _t2073 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2073
    _t2074 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2074
    _t2075 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2075
    _t2076 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2076
    _t2077 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2077
    _t2078 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2078
    _t2079 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2079
    _t2080 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2080
    _t2081 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2081
    _t2082 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2082
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2083 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2083
    _t2084 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2084
    _t2085 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2085
    _t2086 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2086
    _t2087 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2087
    _t2088 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2088
    _t2089 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2089
    _t2090 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2090
    _t2091 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2091
    _t2092 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2092
    _t2093 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2093
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2094 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2094
    _t2095 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2095
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
    _t2096 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2096
    _t2097 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2097
    _t2098 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2098
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2099 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2099
    _t2100 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2100
    _t2101 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2101
    _t2102 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2102
    _t2103 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2103
    _t2104 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2104
    _t2105 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2105
    _t2106 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2106
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2107 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2107
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2108 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2108
end

function construct_iceberg_locator(parser::ParserState, table_name::String, namespace::Vector{String}, warehouse::String, from_snapshot_opt::Union{Nothing, String}, to_snapshot_opt::Union{Nothing, String})::Proto.IcebergLocator
    _t2109 = Proto.IcebergLocator(table_name=table_name, namespace=namespace, warehouse=warehouse, from_snapshot=(!isnothing(from_snapshot_opt) ? from_snapshot_opt : ""), to_snapshot=(!isnothing(to_snapshot_opt) ? to_snapshot_opt : ""))
    return _t2109
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, table_def::Proto.RelationId, columns::Vector{Proto.ExportGNFColumn}, table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2110 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2110
    _t2111 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2111
    _t2112 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2112
    table_props = Dict(table_property_pairs)
    _t2113 = Proto.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
    return _t2113
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start666 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1321 = parse_configure(parser)
        _t1320 = _t1321
    else
        _t1320 = nothing
    end
    configure660 = _t1320
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1323 = parse_sync(parser)
        _t1322 = _t1323
    else
        _t1322 = nothing
    end
    sync661 = _t1322
    xs662 = Proto.Epoch[]
    cond663 = match_lookahead_literal(parser, "(", 0)
    while cond663
        _t1324 = parse_epoch(parser)
        item664 = _t1324
        push!(xs662, item664)
        cond663 = match_lookahead_literal(parser, "(", 0)
    end
    epochs665 = xs662
    consume_literal!(parser, ")")
    _t1325 = default_configure(parser)
    _t1326 = Proto.Transaction(epochs=epochs665, configure=(!isnothing(configure660) ? configure660 : _t1325), sync=sync661)
    result667 = _t1326
    record_span!(parser, span_start666, "Transaction")
    return result667
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start669 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1327 = parse_config_dict(parser)
    config_dict668 = _t1327
    consume_literal!(parser, ")")
    _t1328 = construct_configure(parser, config_dict668)
    result670 = _t1328
    record_span!(parser, span_start669, "Configure")
    return result670
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs671 = Tuple{String, Proto.Value}[]
    cond672 = match_lookahead_literal(parser, ":", 0)
    while cond672
        _t1329 = parse_config_key_value(parser)
        item673 = _t1329
        push!(xs671, item673)
        cond672 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values674 = xs671
    consume_literal!(parser, "}")
    return config_key_values674
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol675 = consume_terminal!(parser, "SYMBOL")
    _t1330 = parse_raw_value(parser)
    raw_value676 = _t1330
    return (symbol675, raw_value676,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start690 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1331 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1332 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1333 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1335 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1336 = 0
                        else
                            _t1336 = -1
                        end
                        _t1335 = _t1336
                    end
                    _t1334 = _t1335
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1337 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1338 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1339 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1340 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1341 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1342 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1343 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1344 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1345 = 10
                                                    else
                                                        _t1345 = -1
                                                    end
                                                    _t1344 = _t1345
                                                end
                                                _t1343 = _t1344
                                            end
                                            _t1342 = _t1343
                                        end
                                        _t1341 = _t1342
                                    end
                                    _t1340 = _t1341
                                end
                                _t1339 = _t1340
                            end
                            _t1338 = _t1339
                        end
                        _t1337 = _t1338
                    end
                    _t1334 = _t1337
                end
                _t1333 = _t1334
            end
            _t1332 = _t1333
        end
        _t1331 = _t1332
    end
    prediction677 = _t1331
    if prediction677 == 12
        _t1347 = parse_boolean_value(parser)
        boolean_value689 = _t1347
        _t1348 = Proto.Value(value=OneOf(:boolean_value, boolean_value689))
        _t1346 = _t1348
    else
        if prediction677 == 11
            consume_literal!(parser, "missing")
            _t1350 = Proto.MissingValue()
            _t1351 = Proto.Value(value=OneOf(:missing_value, _t1350))
            _t1349 = _t1351
        else
            if prediction677 == 10
                decimal688 = consume_terminal!(parser, "DECIMAL")
                _t1353 = Proto.Value(value=OneOf(:decimal_value, decimal688))
                _t1352 = _t1353
            else
                if prediction677 == 9
                    int128687 = consume_terminal!(parser, "INT128")
                    _t1355 = Proto.Value(value=OneOf(:int128_value, int128687))
                    _t1354 = _t1355
                else
                    if prediction677 == 8
                        uint128686 = consume_terminal!(parser, "UINT128")
                        _t1357 = Proto.Value(value=OneOf(:uint128_value, uint128686))
                        _t1356 = _t1357
                    else
                        if prediction677 == 7
                            uint32685 = consume_terminal!(parser, "UINT32")
                            _t1359 = Proto.Value(value=OneOf(:uint32_value, uint32685))
                            _t1358 = _t1359
                        else
                            if prediction677 == 6
                                float684 = consume_terminal!(parser, "FLOAT")
                                _t1361 = Proto.Value(value=OneOf(:float_value, float684))
                                _t1360 = _t1361
                            else
                                if prediction677 == 5
                                    float32683 = consume_terminal!(parser, "FLOAT32")
                                    _t1363 = Proto.Value(value=OneOf(:float32_value, float32683))
                                    _t1362 = _t1363
                                else
                                    if prediction677 == 4
                                        int682 = consume_terminal!(parser, "INT")
                                        _t1365 = Proto.Value(value=OneOf(:int_value, int682))
                                        _t1364 = _t1365
                                    else
                                        if prediction677 == 3
                                            int32681 = consume_terminal!(parser, "INT32")
                                            _t1367 = Proto.Value(value=OneOf(:int32_value, int32681))
                                            _t1366 = _t1367
                                        else
                                            if prediction677 == 2
                                                string680 = consume_terminal!(parser, "STRING")
                                                _t1369 = Proto.Value(value=OneOf(:string_value, string680))
                                                _t1368 = _t1369
                                            else
                                                if prediction677 == 1
                                                    _t1371 = parse_raw_datetime(parser)
                                                    raw_datetime679 = _t1371
                                                    _t1372 = Proto.Value(value=OneOf(:datetime_value, raw_datetime679))
                                                    _t1370 = _t1372
                                                else
                                                    if prediction677 == 0
                                                        _t1374 = parse_raw_date(parser)
                                                        raw_date678 = _t1374
                                                        _t1375 = Proto.Value(value=OneOf(:date_value, raw_date678))
                                                        _t1373 = _t1375
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1370 = _t1373
                                                end
                                                _t1368 = _t1370
                                            end
                                            _t1366 = _t1368
                                        end
                                        _t1364 = _t1366
                                    end
                                    _t1362 = _t1364
                                end
                                _t1360 = _t1362
                            end
                            _t1358 = _t1360
                        end
                        _t1356 = _t1358
                    end
                    _t1354 = _t1356
                end
                _t1352 = _t1354
            end
            _t1349 = _t1352
        end
        _t1346 = _t1349
    end
    result691 = _t1346
    record_span!(parser, span_start690, "Value")
    return result691
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start695 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int692 = consume_terminal!(parser, "INT")
    int_3693 = consume_terminal!(parser, "INT")
    int_4694 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1376 = Proto.DateValue(year=Int32(int692), month=Int32(int_3693), day=Int32(int_4694))
    result696 = _t1376
    record_span!(parser, span_start695, "DateValue")
    return result696
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start704 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int697 = consume_terminal!(parser, "INT")
    int_3698 = consume_terminal!(parser, "INT")
    int_4699 = consume_terminal!(parser, "INT")
    int_5700 = consume_terminal!(parser, "INT")
    int_6701 = consume_terminal!(parser, "INT")
    int_7702 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1377 = consume_terminal!(parser, "INT")
    else
        _t1377 = nothing
    end
    int_8703 = _t1377
    consume_literal!(parser, ")")
    _t1378 = Proto.DateTimeValue(year=Int32(int697), month=Int32(int_3698), day=Int32(int_4699), hour=Int32(int_5700), minute=Int32(int_6701), second=Int32(int_7702), microsecond=Int32((!isnothing(int_8703) ? int_8703 : 0)))
    result705 = _t1378
    record_span!(parser, span_start704, "DateTimeValue")
    return result705
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1379 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1380 = 1
        else
            _t1380 = -1
        end
        _t1379 = _t1380
    end
    prediction706 = _t1379
    if prediction706 == 1
        consume_literal!(parser, "false")
        _t1381 = false
    else
        if prediction706 == 0
            consume_literal!(parser, "true")
            _t1382 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1381 = _t1382
    end
    return _t1381
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start711 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs707 = Proto.FragmentId[]
    cond708 = match_lookahead_literal(parser, ":", 0)
    while cond708
        _t1383 = parse_fragment_id(parser)
        item709 = _t1383
        push!(xs707, item709)
        cond708 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids710 = xs707
    consume_literal!(parser, ")")
    _t1384 = Proto.Sync(fragments=fragment_ids710)
    result712 = _t1384
    record_span!(parser, span_start711, "Sync")
    return result712
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start714 = span_start(parser)
    consume_literal!(parser, ":")
    symbol713 = consume_terminal!(parser, "SYMBOL")
    result715 = Proto.FragmentId(Vector{UInt8}(symbol713))
    record_span!(parser, span_start714, "FragmentId")
    return result715
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start718 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1386 = parse_epoch_writes(parser)
        _t1385 = _t1386
    else
        _t1385 = nothing
    end
    epoch_writes716 = _t1385
    if match_lookahead_literal(parser, "(", 0)
        _t1388 = parse_epoch_reads(parser)
        _t1387 = _t1388
    else
        _t1387 = nothing
    end
    epoch_reads717 = _t1387
    consume_literal!(parser, ")")
    _t1389 = Proto.Epoch(writes=(!isnothing(epoch_writes716) ? epoch_writes716 : Proto.Write[]), reads=(!isnothing(epoch_reads717) ? epoch_reads717 : Proto.Read[]))
    result719 = _t1389
    record_span!(parser, span_start718, "Epoch")
    return result719
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs720 = Proto.Write[]
    cond721 = match_lookahead_literal(parser, "(", 0)
    while cond721
        _t1390 = parse_write(parser)
        item722 = _t1390
        push!(xs720, item722)
        cond721 = match_lookahead_literal(parser, "(", 0)
    end
    writes723 = xs720
    consume_literal!(parser, ")")
    return writes723
end

function parse_write(parser::ParserState)::Proto.Write
    span_start729 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1392 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1393 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1394 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1395 = 2
                    else
                        _t1395 = -1
                    end
                    _t1394 = _t1395
                end
                _t1393 = _t1394
            end
            _t1392 = _t1393
        end
        _t1391 = _t1392
    else
        _t1391 = -1
    end
    prediction724 = _t1391
    if prediction724 == 3
        _t1397 = parse_snapshot(parser)
        snapshot728 = _t1397
        _t1398 = Proto.Write(write_type=OneOf(:snapshot, snapshot728))
        _t1396 = _t1398
    else
        if prediction724 == 2
            _t1400 = parse_context(parser)
            context727 = _t1400
            _t1401 = Proto.Write(write_type=OneOf(:context, context727))
            _t1399 = _t1401
        else
            if prediction724 == 1
                _t1403 = parse_undefine(parser)
                undefine726 = _t1403
                _t1404 = Proto.Write(write_type=OneOf(:undefine, undefine726))
                _t1402 = _t1404
            else
                if prediction724 == 0
                    _t1406 = parse_define(parser)
                    define725 = _t1406
                    _t1407 = Proto.Write(write_type=OneOf(:define, define725))
                    _t1405 = _t1407
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1402 = _t1405
            end
            _t1399 = _t1402
        end
        _t1396 = _t1399
    end
    result730 = _t1396
    record_span!(parser, span_start729, "Write")
    return result730
end

function parse_define(parser::ParserState)::Proto.Define
    span_start732 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1408 = parse_fragment(parser)
    fragment731 = _t1408
    consume_literal!(parser, ")")
    _t1409 = Proto.Define(fragment=fragment731)
    result733 = _t1409
    record_span!(parser, span_start732, "Define")
    return result733
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start739 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1410 = parse_new_fragment_id(parser)
    new_fragment_id734 = _t1410
    xs735 = Proto.Declaration[]
    cond736 = match_lookahead_literal(parser, "(", 0)
    while cond736
        _t1411 = parse_declaration(parser)
        item737 = _t1411
        push!(xs735, item737)
        cond736 = match_lookahead_literal(parser, "(", 0)
    end
    declarations738 = xs735
    consume_literal!(parser, ")")
    result740 = construct_fragment(parser, new_fragment_id734, declarations738)
    record_span!(parser, span_start739, "Fragment")
    return result740
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start742 = span_start(parser)
    _t1412 = parse_fragment_id(parser)
    fragment_id741 = _t1412
    start_fragment!(parser, fragment_id741)
    result743 = fragment_id741
    record_span!(parser, span_start742, "FragmentId")
    return result743
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start749 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1414 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1415 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1416 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1417 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1418 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1419 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1420 = 1
                                else
                                    _t1420 = -1
                                end
                                _t1419 = _t1420
                            end
                            _t1418 = _t1419
                        end
                        _t1417 = _t1418
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
    prediction744 = _t1413
    if prediction744 == 3
        _t1422 = parse_data(parser)
        data748 = _t1422
        _t1423 = Proto.Declaration(declaration_type=OneOf(:data, data748))
        _t1421 = _t1423
    else
        if prediction744 == 2
            _t1425 = parse_constraint(parser)
            constraint747 = _t1425
            _t1426 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint747))
            _t1424 = _t1426
        else
            if prediction744 == 1
                _t1428 = parse_algorithm(parser)
                algorithm746 = _t1428
                _t1429 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm746))
                _t1427 = _t1429
            else
                if prediction744 == 0
                    _t1431 = parse_def(parser)
                    def745 = _t1431
                    _t1432 = Proto.Declaration(declaration_type=OneOf(:def, def745))
                    _t1430 = _t1432
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1427 = _t1430
            end
            _t1424 = _t1427
        end
        _t1421 = _t1424
    end
    result750 = _t1421
    record_span!(parser, span_start749, "Declaration")
    return result750
end

function parse_def(parser::ParserState)::Proto.Def
    span_start754 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1433 = parse_relation_id(parser)
    relation_id751 = _t1433
    _t1434 = parse_abstraction(parser)
    abstraction752 = _t1434
    if match_lookahead_literal(parser, "(", 0)
        _t1436 = parse_attrs(parser)
        _t1435 = _t1436
    else
        _t1435 = nothing
    end
    attrs753 = _t1435
    consume_literal!(parser, ")")
    _t1437 = Proto.Def(name=relation_id751, body=abstraction752, attrs=(!isnothing(attrs753) ? attrs753 : Proto.Attribute[]))
    result755 = _t1437
    record_span!(parser, span_start754, "Def")
    return result755
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start759 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1438 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1439 = 1
        else
            _t1439 = -1
        end
        _t1438 = _t1439
    end
    prediction756 = _t1438
    if prediction756 == 1
        uint128758 = consume_terminal!(parser, "UINT128")
        _t1440 = Proto.RelationId(uint128758.low, uint128758.high)
    else
        if prediction756 == 0
            consume_literal!(parser, ":")
            symbol757 = consume_terminal!(parser, "SYMBOL")
            _t1441 = relation_id_from_string(parser, symbol757)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1440 = _t1441
    end
    result760 = _t1440
    record_span!(parser, span_start759, "RelationId")
    return result760
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start763 = span_start(parser)
    consume_literal!(parser, "(")
    _t1442 = parse_bindings(parser)
    bindings761 = _t1442
    _t1443 = parse_formula(parser)
    formula762 = _t1443
    consume_literal!(parser, ")")
    _t1444 = Proto.Abstraction(vars=vcat(bindings761[1], !isnothing(bindings761[2]) ? bindings761[2] : []), value=formula762)
    result764 = _t1444
    record_span!(parser, span_start763, "Abstraction")
    return result764
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs765 = Proto.Binding[]
    cond766 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond766
        _t1445 = parse_binding(parser)
        item767 = _t1445
        push!(xs765, item767)
        cond766 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings768 = xs765
    if match_lookahead_literal(parser, "|", 0)
        _t1447 = parse_value_bindings(parser)
        _t1446 = _t1447
    else
        _t1446 = nothing
    end
    value_bindings769 = _t1446
    consume_literal!(parser, "]")
    return (bindings768, (!isnothing(value_bindings769) ? value_bindings769 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start772 = span_start(parser)
    symbol770 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1448 = parse_type(parser)
    type771 = _t1448
    _t1449 = Proto.Var(name=symbol770)
    _t1450 = Proto.Binding(var=_t1449, var"#type"=type771)
    result773 = _t1450
    record_span!(parser, span_start772, "Binding")
    return result773
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start789 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1451 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1452 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1453 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1454 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1455 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1456 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1457 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1458 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1459 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1460 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1461 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1462 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1463 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1464 = 9
                                                        else
                                                            _t1464 = -1
                                                        end
                                                        _t1463 = _t1464
                                                    end
                                                    _t1462 = _t1463
                                                end
                                                _t1461 = _t1462
                                            end
                                            _t1460 = _t1461
                                        end
                                        _t1459 = _t1460
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
    prediction774 = _t1451
    if prediction774 == 13
        _t1466 = parse_uint32_type(parser)
        uint32_type788 = _t1466
        _t1467 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type788))
        _t1465 = _t1467
    else
        if prediction774 == 12
            _t1469 = parse_float32_type(parser)
            float32_type787 = _t1469
            _t1470 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type787))
            _t1468 = _t1470
        else
            if prediction774 == 11
                _t1472 = parse_int32_type(parser)
                int32_type786 = _t1472
                _t1473 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type786))
                _t1471 = _t1473
            else
                if prediction774 == 10
                    _t1475 = parse_boolean_type(parser)
                    boolean_type785 = _t1475
                    _t1476 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type785))
                    _t1474 = _t1476
                else
                    if prediction774 == 9
                        _t1478 = parse_decimal_type(parser)
                        decimal_type784 = _t1478
                        _t1479 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type784))
                        _t1477 = _t1479
                    else
                        if prediction774 == 8
                            _t1481 = parse_missing_type(parser)
                            missing_type783 = _t1481
                            _t1482 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type783))
                            _t1480 = _t1482
                        else
                            if prediction774 == 7
                                _t1484 = parse_datetime_type(parser)
                                datetime_type782 = _t1484
                                _t1485 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type782))
                                _t1483 = _t1485
                            else
                                if prediction774 == 6
                                    _t1487 = parse_date_type(parser)
                                    date_type781 = _t1487
                                    _t1488 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type781))
                                    _t1486 = _t1488
                                else
                                    if prediction774 == 5
                                        _t1490 = parse_int128_type(parser)
                                        int128_type780 = _t1490
                                        _t1491 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type780))
                                        _t1489 = _t1491
                                    else
                                        if prediction774 == 4
                                            _t1493 = parse_uint128_type(parser)
                                            uint128_type779 = _t1493
                                            _t1494 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type779))
                                            _t1492 = _t1494
                                        else
                                            if prediction774 == 3
                                                _t1496 = parse_float_type(parser)
                                                float_type778 = _t1496
                                                _t1497 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type778))
                                                _t1495 = _t1497
                                            else
                                                if prediction774 == 2
                                                    _t1499 = parse_int_type(parser)
                                                    int_type777 = _t1499
                                                    _t1500 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type777))
                                                    _t1498 = _t1500
                                                else
                                                    if prediction774 == 1
                                                        _t1502 = parse_string_type(parser)
                                                        string_type776 = _t1502
                                                        _t1503 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type776))
                                                        _t1501 = _t1503
                                                    else
                                                        if prediction774 == 0
                                                            _t1505 = parse_unspecified_type(parser)
                                                            unspecified_type775 = _t1505
                                                            _t1506 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type775))
                                                            _t1504 = _t1506
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                                    _t1486 = _t1489
                                end
                                _t1483 = _t1486
                            end
                            _t1480 = _t1483
                        end
                        _t1477 = _t1480
                    end
                    _t1474 = _t1477
                end
                _t1471 = _t1474
            end
            _t1468 = _t1471
        end
        _t1465 = _t1468
    end
    result790 = _t1465
    record_span!(parser, span_start789, "Type")
    return result790
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start791 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1507 = Proto.UnspecifiedType()
    result792 = _t1507
    record_span!(parser, span_start791, "UnspecifiedType")
    return result792
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start793 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1508 = Proto.StringType()
    result794 = _t1508
    record_span!(parser, span_start793, "StringType")
    return result794
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start795 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1509 = Proto.IntType()
    result796 = _t1509
    record_span!(parser, span_start795, "IntType")
    return result796
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start797 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1510 = Proto.FloatType()
    result798 = _t1510
    record_span!(parser, span_start797, "FloatType")
    return result798
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start799 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1511 = Proto.UInt128Type()
    result800 = _t1511
    record_span!(parser, span_start799, "UInt128Type")
    return result800
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start801 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1512 = Proto.Int128Type()
    result802 = _t1512
    record_span!(parser, span_start801, "Int128Type")
    return result802
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start803 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1513 = Proto.DateType()
    result804 = _t1513
    record_span!(parser, span_start803, "DateType")
    return result804
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start805 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1514 = Proto.DateTimeType()
    result806 = _t1514
    record_span!(parser, span_start805, "DateTimeType")
    return result806
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start807 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1515 = Proto.MissingType()
    result808 = _t1515
    record_span!(parser, span_start807, "MissingType")
    return result808
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start811 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int809 = consume_terminal!(parser, "INT")
    int_3810 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1516 = Proto.DecimalType(precision=Int32(int809), scale=Int32(int_3810))
    result812 = _t1516
    record_span!(parser, span_start811, "DecimalType")
    return result812
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start813 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1517 = Proto.BooleanType()
    result814 = _t1517
    record_span!(parser, span_start813, "BooleanType")
    return result814
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start815 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1518 = Proto.Int32Type()
    result816 = _t1518
    record_span!(parser, span_start815, "Int32Type")
    return result816
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start817 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1519 = Proto.Float32Type()
    result818 = _t1519
    record_span!(parser, span_start817, "Float32Type")
    return result818
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start819 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1520 = Proto.UInt32Type()
    result820 = _t1520
    record_span!(parser, span_start819, "UInt32Type")
    return result820
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs821 = Proto.Binding[]
    cond822 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond822
        _t1521 = parse_binding(parser)
        item823 = _t1521
        push!(xs821, item823)
        cond822 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings824 = xs821
    return bindings824
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start839 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1523 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1524 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1525 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1526 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1527 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1528 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1529 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1530 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1531 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1532 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1533 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1534 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1535 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1536 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1537 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1538 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1539 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1540 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1541 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1542 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1543 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1544 = 10
                                                                                            else
                                                                                                _t1544 = -1
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
                                                                        _t1538 = _t1539
                                                                    end
                                                                    _t1537 = _t1538
                                                                end
                                                                _t1536 = _t1537
                                                            end
                                                            _t1535 = _t1536
                                                        end
                                                        _t1534 = _t1535
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
                        end
                        _t1526 = _t1527
                    end
                    _t1525 = _t1526
                end
                _t1524 = _t1525
            end
            _t1523 = _t1524
        end
        _t1522 = _t1523
    else
        _t1522 = -1
    end
    prediction825 = _t1522
    if prediction825 == 12
        _t1546 = parse_cast(parser)
        cast838 = _t1546
        _t1547 = Proto.Formula(formula_type=OneOf(:cast, cast838))
        _t1545 = _t1547
    else
        if prediction825 == 11
            _t1549 = parse_rel_atom(parser)
            rel_atom837 = _t1549
            _t1550 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom837))
            _t1548 = _t1550
        else
            if prediction825 == 10
                _t1552 = parse_primitive(parser)
                primitive836 = _t1552
                _t1553 = Proto.Formula(formula_type=OneOf(:primitive, primitive836))
                _t1551 = _t1553
            else
                if prediction825 == 9
                    _t1555 = parse_pragma(parser)
                    pragma835 = _t1555
                    _t1556 = Proto.Formula(formula_type=OneOf(:pragma, pragma835))
                    _t1554 = _t1556
                else
                    if prediction825 == 8
                        _t1558 = parse_atom(parser)
                        atom834 = _t1558
                        _t1559 = Proto.Formula(formula_type=OneOf(:atom, atom834))
                        _t1557 = _t1559
                    else
                        if prediction825 == 7
                            _t1561 = parse_ffi(parser)
                            ffi833 = _t1561
                            _t1562 = Proto.Formula(formula_type=OneOf(:ffi, ffi833))
                            _t1560 = _t1562
                        else
                            if prediction825 == 6
                                _t1564 = parse_not(parser)
                                not832 = _t1564
                                _t1565 = Proto.Formula(formula_type=OneOf(:not, not832))
                                _t1563 = _t1565
                            else
                                if prediction825 == 5
                                    _t1567 = parse_disjunction(parser)
                                    disjunction831 = _t1567
                                    _t1568 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction831))
                                    _t1566 = _t1568
                                else
                                    if prediction825 == 4
                                        _t1570 = parse_conjunction(parser)
                                        conjunction830 = _t1570
                                        _t1571 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction830))
                                        _t1569 = _t1571
                                    else
                                        if prediction825 == 3
                                            _t1573 = parse_reduce(parser)
                                            reduce829 = _t1573
                                            _t1574 = Proto.Formula(formula_type=OneOf(:reduce, reduce829))
                                            _t1572 = _t1574
                                        else
                                            if prediction825 == 2
                                                _t1576 = parse_exists(parser)
                                                exists828 = _t1576
                                                _t1577 = Proto.Formula(formula_type=OneOf(:exists, exists828))
                                                _t1575 = _t1577
                                            else
                                                if prediction825 == 1
                                                    _t1579 = parse_false(parser)
                                                    false827 = _t1579
                                                    _t1580 = Proto.Formula(formula_type=OneOf(:disjunction, false827))
                                                    _t1578 = _t1580
                                                else
                                                    if prediction825 == 0
                                                        _t1582 = parse_true(parser)
                                                        true826 = _t1582
                                                        _t1583 = Proto.Formula(formula_type=OneOf(:conjunction, true826))
                                                        _t1581 = _t1583
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
                            _t1560 = _t1563
                        end
                        _t1557 = _t1560
                    end
                    _t1554 = _t1557
                end
                _t1551 = _t1554
            end
            _t1548 = _t1551
        end
        _t1545 = _t1548
    end
    result840 = _t1545
    record_span!(parser, span_start839, "Formula")
    return result840
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start841 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1584 = Proto.Conjunction(args=Proto.Formula[])
    result842 = _t1584
    record_span!(parser, span_start841, "Conjunction")
    return result842
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start843 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1585 = Proto.Disjunction(args=Proto.Formula[])
    result844 = _t1585
    record_span!(parser, span_start843, "Disjunction")
    return result844
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start847 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1586 = parse_bindings(parser)
    bindings845 = _t1586
    _t1587 = parse_formula(parser)
    formula846 = _t1587
    consume_literal!(parser, ")")
    _t1588 = Proto.Abstraction(vars=vcat(bindings845[1], !isnothing(bindings845[2]) ? bindings845[2] : []), value=formula846)
    _t1589 = Proto.Exists(body=_t1588)
    result848 = _t1589
    record_span!(parser, span_start847, "Exists")
    return result848
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start852 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1590 = parse_abstraction(parser)
    abstraction849 = _t1590
    _t1591 = parse_abstraction(parser)
    abstraction_3850 = _t1591
    _t1592 = parse_terms(parser)
    terms851 = _t1592
    consume_literal!(parser, ")")
    _t1593 = Proto.Reduce(op=abstraction849, body=abstraction_3850, terms=terms851)
    result853 = _t1593
    record_span!(parser, span_start852, "Reduce")
    return result853
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs854 = Proto.Term[]
    cond855 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond855
        _t1594 = parse_term(parser)
        item856 = _t1594
        push!(xs854, item856)
        cond855 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms857 = xs854
    consume_literal!(parser, ")")
    return terms857
end

function parse_term(parser::ParserState)::Proto.Term
    span_start861 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1595 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1596 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1597 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1598 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1599 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1600 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1601 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1602 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1603 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1604 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1605 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1606 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1607 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1608 = 1
                                                        else
                                                            _t1608 = -1
                                                        end
                                                        _t1607 = _t1608
                                                    end
                                                    _t1606 = _t1607
                                                end
                                                _t1605 = _t1606
                                            end
                                            _t1604 = _t1605
                                        end
                                        _t1603 = _t1604
                                    end
                                    _t1602 = _t1603
                                end
                                _t1601 = _t1602
                            end
                            _t1600 = _t1601
                        end
                        _t1599 = _t1600
                    end
                    _t1598 = _t1599
                end
                _t1597 = _t1598
            end
            _t1596 = _t1597
        end
        _t1595 = _t1596
    end
    prediction858 = _t1595
    if prediction858 == 1
        _t1610 = parse_value(parser)
        value860 = _t1610
        _t1611 = Proto.Term(term_type=OneOf(:constant, value860))
        _t1609 = _t1611
    else
        if prediction858 == 0
            _t1613 = parse_var(parser)
            var859 = _t1613
            _t1614 = Proto.Term(term_type=OneOf(:var, var859))
            _t1612 = _t1614
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1609 = _t1612
    end
    result862 = _t1609
    record_span!(parser, span_start861, "Term")
    return result862
end

function parse_var(parser::ParserState)::Proto.Var
    span_start864 = span_start(parser)
    symbol863 = consume_terminal!(parser, "SYMBOL")
    _t1615 = Proto.Var(name=symbol863)
    result865 = _t1615
    record_span!(parser, span_start864, "Var")
    return result865
end

function parse_value(parser::ParserState)::Proto.Value
    span_start879 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1616 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1617 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1618 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1620 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1621 = 0
                        else
                            _t1621 = -1
                        end
                        _t1620 = _t1621
                    end
                    _t1619 = _t1620
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1622 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1623 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1624 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1625 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1626 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1627 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1628 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1629 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1630 = 10
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
                    _t1619 = _t1622
                end
                _t1618 = _t1619
            end
            _t1617 = _t1618
        end
        _t1616 = _t1617
    end
    prediction866 = _t1616
    if prediction866 == 12
        _t1632 = parse_boolean_value(parser)
        boolean_value878 = _t1632
        _t1633 = Proto.Value(value=OneOf(:boolean_value, boolean_value878))
        _t1631 = _t1633
    else
        if prediction866 == 11
            consume_literal!(parser, "missing")
            _t1635 = Proto.MissingValue()
            _t1636 = Proto.Value(value=OneOf(:missing_value, _t1635))
            _t1634 = _t1636
        else
            if prediction866 == 10
                formatted_decimal877 = consume_terminal!(parser, "DECIMAL")
                _t1638 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal877))
                _t1637 = _t1638
            else
                if prediction866 == 9
                    formatted_int128876 = consume_terminal!(parser, "INT128")
                    _t1640 = Proto.Value(value=OneOf(:int128_value, formatted_int128876))
                    _t1639 = _t1640
                else
                    if prediction866 == 8
                        formatted_uint128875 = consume_terminal!(parser, "UINT128")
                        _t1642 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128875))
                        _t1641 = _t1642
                    else
                        if prediction866 == 7
                            formatted_uint32874 = consume_terminal!(parser, "UINT32")
                            _t1644 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32874))
                            _t1643 = _t1644
                        else
                            if prediction866 == 6
                                formatted_float873 = consume_terminal!(parser, "FLOAT")
                                _t1646 = Proto.Value(value=OneOf(:float_value, formatted_float873))
                                _t1645 = _t1646
                            else
                                if prediction866 == 5
                                    formatted_float32872 = consume_terminal!(parser, "FLOAT32")
                                    _t1648 = Proto.Value(value=OneOf(:float32_value, formatted_float32872))
                                    _t1647 = _t1648
                                else
                                    if prediction866 == 4
                                        formatted_int871 = consume_terminal!(parser, "INT")
                                        _t1650 = Proto.Value(value=OneOf(:int_value, formatted_int871))
                                        _t1649 = _t1650
                                    else
                                        if prediction866 == 3
                                            formatted_int32870 = consume_terminal!(parser, "INT32")
                                            _t1652 = Proto.Value(value=OneOf(:int32_value, formatted_int32870))
                                            _t1651 = _t1652
                                        else
                                            if prediction866 == 2
                                                formatted_string869 = consume_terminal!(parser, "STRING")
                                                _t1654 = Proto.Value(value=OneOf(:string_value, formatted_string869))
                                                _t1653 = _t1654
                                            else
                                                if prediction866 == 1
                                                    _t1656 = parse_datetime(parser)
                                                    datetime868 = _t1656
                                                    _t1657 = Proto.Value(value=OneOf(:datetime_value, datetime868))
                                                    _t1655 = _t1657
                                                else
                                                    if prediction866 == 0
                                                        _t1659 = parse_date(parser)
                                                        date867 = _t1659
                                                        _t1660 = Proto.Value(value=OneOf(:date_value, date867))
                                                        _t1658 = _t1660
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1655 = _t1658
                                                end
                                                _t1653 = _t1655
                                            end
                                            _t1651 = _t1653
                                        end
                                        _t1649 = _t1651
                                    end
                                    _t1647 = _t1649
                                end
                                _t1645 = _t1647
                            end
                            _t1643 = _t1645
                        end
                        _t1641 = _t1643
                    end
                    _t1639 = _t1641
                end
                _t1637 = _t1639
            end
            _t1634 = _t1637
        end
        _t1631 = _t1634
    end
    result880 = _t1631
    record_span!(parser, span_start879, "Value")
    return result880
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start884 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int881 = consume_terminal!(parser, "INT")
    formatted_int_3882 = consume_terminal!(parser, "INT")
    formatted_int_4883 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1661 = Proto.DateValue(year=Int32(formatted_int881), month=Int32(formatted_int_3882), day=Int32(formatted_int_4883))
    result885 = _t1661
    record_span!(parser, span_start884, "DateValue")
    return result885
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start893 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int886 = consume_terminal!(parser, "INT")
    formatted_int_3887 = consume_terminal!(parser, "INT")
    formatted_int_4888 = consume_terminal!(parser, "INT")
    formatted_int_5889 = consume_terminal!(parser, "INT")
    formatted_int_6890 = consume_terminal!(parser, "INT")
    formatted_int_7891 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1662 = consume_terminal!(parser, "INT")
    else
        _t1662 = nothing
    end
    formatted_int_8892 = _t1662
    consume_literal!(parser, ")")
    _t1663 = Proto.DateTimeValue(year=Int32(formatted_int886), month=Int32(formatted_int_3887), day=Int32(formatted_int_4888), hour=Int32(formatted_int_5889), minute=Int32(formatted_int_6890), second=Int32(formatted_int_7891), microsecond=Int32((!isnothing(formatted_int_8892) ? formatted_int_8892 : 0)))
    result894 = _t1663
    record_span!(parser, span_start893, "DateTimeValue")
    return result894
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start899 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs895 = Proto.Formula[]
    cond896 = match_lookahead_literal(parser, "(", 0)
    while cond896
        _t1664 = parse_formula(parser)
        item897 = _t1664
        push!(xs895, item897)
        cond896 = match_lookahead_literal(parser, "(", 0)
    end
    formulas898 = xs895
    consume_literal!(parser, ")")
    _t1665 = Proto.Conjunction(args=formulas898)
    result900 = _t1665
    record_span!(parser, span_start899, "Conjunction")
    return result900
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start905 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs901 = Proto.Formula[]
    cond902 = match_lookahead_literal(parser, "(", 0)
    while cond902
        _t1666 = parse_formula(parser)
        item903 = _t1666
        push!(xs901, item903)
        cond902 = match_lookahead_literal(parser, "(", 0)
    end
    formulas904 = xs901
    consume_literal!(parser, ")")
    _t1667 = Proto.Disjunction(args=formulas904)
    result906 = _t1667
    record_span!(parser, span_start905, "Disjunction")
    return result906
end

function parse_not(parser::ParserState)::Proto.Not
    span_start908 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1668 = parse_formula(parser)
    formula907 = _t1668
    consume_literal!(parser, ")")
    _t1669 = Proto.Not(arg=formula907)
    result909 = _t1669
    record_span!(parser, span_start908, "Not")
    return result909
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start913 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1670 = parse_name(parser)
    name910 = _t1670
    _t1671 = parse_ffi_args(parser)
    ffi_args911 = _t1671
    _t1672 = parse_terms(parser)
    terms912 = _t1672
    consume_literal!(parser, ")")
    _t1673 = Proto.FFI(name=name910, args=ffi_args911, terms=terms912)
    result914 = _t1673
    record_span!(parser, span_start913, "FFI")
    return result914
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol915 = consume_terminal!(parser, "SYMBOL")
    return symbol915
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs916 = Proto.Abstraction[]
    cond917 = match_lookahead_literal(parser, "(", 0)
    while cond917
        _t1674 = parse_abstraction(parser)
        item918 = _t1674
        push!(xs916, item918)
        cond917 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions919 = xs916
    consume_literal!(parser, ")")
    return abstractions919
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start925 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1675 = parse_relation_id(parser)
    relation_id920 = _t1675
    xs921 = Proto.Term[]
    cond922 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond922
        _t1676 = parse_term(parser)
        item923 = _t1676
        push!(xs921, item923)
        cond922 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms924 = xs921
    consume_literal!(parser, ")")
    _t1677 = Proto.Atom(name=relation_id920, terms=terms924)
    result926 = _t1677
    record_span!(parser, span_start925, "Atom")
    return result926
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start932 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1678 = parse_name(parser)
    name927 = _t1678
    xs928 = Proto.Term[]
    cond929 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond929
        _t1679 = parse_term(parser)
        item930 = _t1679
        push!(xs928, item930)
        cond929 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms931 = xs928
    consume_literal!(parser, ")")
    _t1680 = Proto.Pragma(name=name927, terms=terms931)
    result933 = _t1680
    record_span!(parser, span_start932, "Pragma")
    return result933
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start949 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1682 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1683 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1684 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1685 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1686 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1687 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1688 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1689 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1690 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1691 = 7
                                            else
                                                _t1691 = -1
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
            _t1682 = _t1683
        end
        _t1681 = _t1682
    else
        _t1681 = -1
    end
    prediction934 = _t1681
    if prediction934 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1693 = parse_name(parser)
        name944 = _t1693
        xs945 = Proto.RelTerm[]
        cond946 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond946
            _t1694 = parse_rel_term(parser)
            item947 = _t1694
            push!(xs945, item947)
            cond946 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms948 = xs945
        consume_literal!(parser, ")")
        _t1695 = Proto.Primitive(name=name944, terms=rel_terms948)
        _t1692 = _t1695
    else
        if prediction934 == 8
            _t1697 = parse_divide(parser)
            divide943 = _t1697
            _t1696 = divide943
        else
            if prediction934 == 7
                _t1699 = parse_multiply(parser)
                multiply942 = _t1699
                _t1698 = multiply942
            else
                if prediction934 == 6
                    _t1701 = parse_minus(parser)
                    minus941 = _t1701
                    _t1700 = minus941
                else
                    if prediction934 == 5
                        _t1703 = parse_add(parser)
                        add940 = _t1703
                        _t1702 = add940
                    else
                        if prediction934 == 4
                            _t1705 = parse_gt_eq(parser)
                            gt_eq939 = _t1705
                            _t1704 = gt_eq939
                        else
                            if prediction934 == 3
                                _t1707 = parse_gt(parser)
                                gt938 = _t1707
                                _t1706 = gt938
                            else
                                if prediction934 == 2
                                    _t1709 = parse_lt_eq(parser)
                                    lt_eq937 = _t1709
                                    _t1708 = lt_eq937
                                else
                                    if prediction934 == 1
                                        _t1711 = parse_lt(parser)
                                        lt936 = _t1711
                                        _t1710 = lt936
                                    else
                                        if prediction934 == 0
                                            _t1713 = parse_eq(parser)
                                            eq935 = _t1713
                                            _t1712 = eq935
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1710 = _t1712
                                    end
                                    _t1708 = _t1710
                                end
                                _t1706 = _t1708
                            end
                            _t1704 = _t1706
                        end
                        _t1702 = _t1704
                    end
                    _t1700 = _t1702
                end
                _t1698 = _t1700
            end
            _t1696 = _t1698
        end
        _t1692 = _t1696
    end
    result950 = _t1692
    record_span!(parser, span_start949, "Primitive")
    return result950
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start953 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1714 = parse_term(parser)
    term951 = _t1714
    _t1715 = parse_term(parser)
    term_3952 = _t1715
    consume_literal!(parser, ")")
    _t1716 = Proto.RelTerm(rel_term_type=OneOf(:term, term951))
    _t1717 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3952))
    _t1718 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1716, _t1717])
    result954 = _t1718
    record_span!(parser, span_start953, "Primitive")
    return result954
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start957 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1719 = parse_term(parser)
    term955 = _t1719
    _t1720 = parse_term(parser)
    term_3956 = _t1720
    consume_literal!(parser, ")")
    _t1721 = Proto.RelTerm(rel_term_type=OneOf(:term, term955))
    _t1722 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3956))
    _t1723 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1721, _t1722])
    result958 = _t1723
    record_span!(parser, span_start957, "Primitive")
    return result958
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start961 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1724 = parse_term(parser)
    term959 = _t1724
    _t1725 = parse_term(parser)
    term_3960 = _t1725
    consume_literal!(parser, ")")
    _t1726 = Proto.RelTerm(rel_term_type=OneOf(:term, term959))
    _t1727 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3960))
    _t1728 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1726, _t1727])
    result962 = _t1728
    record_span!(parser, span_start961, "Primitive")
    return result962
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start965 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1729 = parse_term(parser)
    term963 = _t1729
    _t1730 = parse_term(parser)
    term_3964 = _t1730
    consume_literal!(parser, ")")
    _t1731 = Proto.RelTerm(rel_term_type=OneOf(:term, term963))
    _t1732 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3964))
    _t1733 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1731, _t1732])
    result966 = _t1733
    record_span!(parser, span_start965, "Primitive")
    return result966
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1734 = parse_term(parser)
    term967 = _t1734
    _t1735 = parse_term(parser)
    term_3968 = _t1735
    consume_literal!(parser, ")")
    _t1736 = Proto.RelTerm(rel_term_type=OneOf(:term, term967))
    _t1737 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3968))
    _t1738 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1736, _t1737])
    result970 = _t1738
    record_span!(parser, span_start969, "Primitive")
    return result970
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start974 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1739 = parse_term(parser)
    term971 = _t1739
    _t1740 = parse_term(parser)
    term_3972 = _t1740
    _t1741 = parse_term(parser)
    term_4973 = _t1741
    consume_literal!(parser, ")")
    _t1742 = Proto.RelTerm(rel_term_type=OneOf(:term, term971))
    _t1743 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3972))
    _t1744 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4973))
    _t1745 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1742, _t1743, _t1744])
    result975 = _t1745
    record_span!(parser, span_start974, "Primitive")
    return result975
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start979 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1746 = parse_term(parser)
    term976 = _t1746
    _t1747 = parse_term(parser)
    term_3977 = _t1747
    _t1748 = parse_term(parser)
    term_4978 = _t1748
    consume_literal!(parser, ")")
    _t1749 = Proto.RelTerm(rel_term_type=OneOf(:term, term976))
    _t1750 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3977))
    _t1751 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4978))
    _t1752 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1749, _t1750, _t1751])
    result980 = _t1752
    record_span!(parser, span_start979, "Primitive")
    return result980
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start984 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1753 = parse_term(parser)
    term981 = _t1753
    _t1754 = parse_term(parser)
    term_3982 = _t1754
    _t1755 = parse_term(parser)
    term_4983 = _t1755
    consume_literal!(parser, ")")
    _t1756 = Proto.RelTerm(rel_term_type=OneOf(:term, term981))
    _t1757 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3982))
    _t1758 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4983))
    _t1759 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1756, _t1757, _t1758])
    result985 = _t1759
    record_span!(parser, span_start984, "Primitive")
    return result985
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start989 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1760 = parse_term(parser)
    term986 = _t1760
    _t1761 = parse_term(parser)
    term_3987 = _t1761
    _t1762 = parse_term(parser)
    term_4988 = _t1762
    consume_literal!(parser, ")")
    _t1763 = Proto.RelTerm(rel_term_type=OneOf(:term, term986))
    _t1764 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3987))
    _t1765 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4988))
    _t1766 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1763, _t1764, _t1765])
    result990 = _t1766
    record_span!(parser, span_start989, "Primitive")
    return result990
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start994 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1767 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1768 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1769 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1770 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1771 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1772 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1773 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1774 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1775 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1776 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1777 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1778 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1779 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1780 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1781 = 1
                                                            else
                                                                _t1781 = -1
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
            end
            _t1768 = _t1769
        end
        _t1767 = _t1768
    end
    prediction991 = _t1767
    if prediction991 == 1
        _t1783 = parse_term(parser)
        term993 = _t1783
        _t1784 = Proto.RelTerm(rel_term_type=OneOf(:term, term993))
        _t1782 = _t1784
    else
        if prediction991 == 0
            _t1786 = parse_specialized_value(parser)
            specialized_value992 = _t1786
            _t1787 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value992))
            _t1785 = _t1787
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1782 = _t1785
    end
    result995 = _t1782
    record_span!(parser, span_start994, "RelTerm")
    return result995
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start997 = span_start(parser)
    consume_literal!(parser, "#")
    _t1788 = parse_raw_value(parser)
    raw_value996 = _t1788
    result998 = raw_value996
    record_span!(parser, span_start997, "Value")
    return result998
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1004 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1789 = parse_name(parser)
    name999 = _t1789
    xs1000 = Proto.RelTerm[]
    cond1001 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond1001
        _t1790 = parse_rel_term(parser)
        item1002 = _t1790
        push!(xs1000, item1002)
        cond1001 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms1003 = xs1000
    consume_literal!(parser, ")")
    _t1791 = Proto.RelAtom(name=name999, terms=rel_terms1003)
    result1005 = _t1791
    record_span!(parser, span_start1004, "RelAtom")
    return result1005
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1008 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1792 = parse_term(parser)
    term1006 = _t1792
    _t1793 = parse_term(parser)
    term_31007 = _t1793
    consume_literal!(parser, ")")
    _t1794 = Proto.Cast(input=term1006, result=term_31007)
    result1009 = _t1794
    record_span!(parser, span_start1008, "Cast")
    return result1009
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1010 = Proto.Attribute[]
    cond1011 = match_lookahead_literal(parser, "(", 0)
    while cond1011
        _t1795 = parse_attribute(parser)
        item1012 = _t1795
        push!(xs1010, item1012)
        cond1011 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1013 = xs1010
    consume_literal!(parser, ")")
    return attributes1013
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1019 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1796 = parse_name(parser)
    name1014 = _t1796
    xs1015 = Proto.Value[]
    cond1016 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1016
        _t1797 = parse_raw_value(parser)
        item1017 = _t1797
        push!(xs1015, item1017)
        cond1016 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1018 = xs1015
    consume_literal!(parser, ")")
    _t1798 = Proto.Attribute(name=name1014, args=raw_values1018)
    result1020 = _t1798
    record_span!(parser, span_start1019, "Attribute")
    return result1020
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1026 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1021 = Proto.RelationId[]
    cond1022 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1022
        _t1799 = parse_relation_id(parser)
        item1023 = _t1799
        push!(xs1021, item1023)
        cond1022 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1024 = xs1021
    _t1800 = parse_script(parser)
    script1025 = _t1800
    consume_literal!(parser, ")")
    _t1801 = Proto.Algorithm(var"#global"=relation_ids1024, body=script1025)
    result1027 = _t1801
    record_span!(parser, span_start1026, "Algorithm")
    return result1027
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1032 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1028 = Proto.Construct[]
    cond1029 = match_lookahead_literal(parser, "(", 0)
    while cond1029
        _t1802 = parse_construct(parser)
        item1030 = _t1802
        push!(xs1028, item1030)
        cond1029 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1031 = xs1028
    consume_literal!(parser, ")")
    _t1803 = Proto.Script(constructs=constructs1031)
    result1033 = _t1803
    record_span!(parser, span_start1032, "Script")
    return result1033
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1037 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1805 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1806 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1807 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1808 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1809 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1810 = 1
                            else
                                _t1810 = -1
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
    else
        _t1804 = -1
    end
    prediction1034 = _t1804
    if prediction1034 == 1
        _t1812 = parse_instruction(parser)
        instruction1036 = _t1812
        _t1813 = Proto.Construct(construct_type=OneOf(:instruction, instruction1036))
        _t1811 = _t1813
    else
        if prediction1034 == 0
            _t1815 = parse_loop(parser)
            loop1035 = _t1815
            _t1816 = Proto.Construct(construct_type=OneOf(:loop, loop1035))
            _t1814 = _t1816
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1811 = _t1814
    end
    result1038 = _t1811
    record_span!(parser, span_start1037, "Construct")
    return result1038
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1041 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1817 = parse_init(parser)
    init1039 = _t1817
    _t1818 = parse_script(parser)
    script1040 = _t1818
    consume_literal!(parser, ")")
    _t1819 = Proto.Loop(init=init1039, body=script1040)
    result1042 = _t1819
    record_span!(parser, span_start1041, "Loop")
    return result1042
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1043 = Proto.Instruction[]
    cond1044 = match_lookahead_literal(parser, "(", 0)
    while cond1044
        _t1820 = parse_instruction(parser)
        item1045 = _t1820
        push!(xs1043, item1045)
        cond1044 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1046 = xs1043
    consume_literal!(parser, ")")
    return instructions1046
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1053 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1822 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1823 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1824 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1825 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1826 = 0
                        else
                            _t1826 = -1
                        end
                        _t1825 = _t1826
                    end
                    _t1824 = _t1825
                end
                _t1823 = _t1824
            end
            _t1822 = _t1823
        end
        _t1821 = _t1822
    else
        _t1821 = -1
    end
    prediction1047 = _t1821
    if prediction1047 == 4
        _t1828 = parse_monus_def(parser)
        monus_def1052 = _t1828
        _t1829 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1052))
        _t1827 = _t1829
    else
        if prediction1047 == 3
            _t1831 = parse_monoid_def(parser)
            monoid_def1051 = _t1831
            _t1832 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1051))
            _t1830 = _t1832
        else
            if prediction1047 == 2
                _t1834 = parse_break(parser)
                break1050 = _t1834
                _t1835 = Proto.Instruction(instr_type=OneOf(:var"#break", break1050))
                _t1833 = _t1835
            else
                if prediction1047 == 1
                    _t1837 = parse_upsert(parser)
                    upsert1049 = _t1837
                    _t1838 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1049))
                    _t1836 = _t1838
                else
                    if prediction1047 == 0
                        _t1840 = parse_assign(parser)
                        assign1048 = _t1840
                        _t1841 = Proto.Instruction(instr_type=OneOf(:assign, assign1048))
                        _t1839 = _t1841
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1836 = _t1839
                end
                _t1833 = _t1836
            end
            _t1830 = _t1833
        end
        _t1827 = _t1830
    end
    result1054 = _t1827
    record_span!(parser, span_start1053, "Instruction")
    return result1054
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1058 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1842 = parse_relation_id(parser)
    relation_id1055 = _t1842
    _t1843 = parse_abstraction(parser)
    abstraction1056 = _t1843
    if match_lookahead_literal(parser, "(", 0)
        _t1845 = parse_attrs(parser)
        _t1844 = _t1845
    else
        _t1844 = nothing
    end
    attrs1057 = _t1844
    consume_literal!(parser, ")")
    _t1846 = Proto.Assign(name=relation_id1055, body=abstraction1056, attrs=(!isnothing(attrs1057) ? attrs1057 : Proto.Attribute[]))
    result1059 = _t1846
    record_span!(parser, span_start1058, "Assign")
    return result1059
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1063 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1847 = parse_relation_id(parser)
    relation_id1060 = _t1847
    _t1848 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1061 = _t1848
    if match_lookahead_literal(parser, "(", 0)
        _t1850 = parse_attrs(parser)
        _t1849 = _t1850
    else
        _t1849 = nothing
    end
    attrs1062 = _t1849
    consume_literal!(parser, ")")
    _t1851 = Proto.Upsert(name=relation_id1060, body=abstraction_with_arity1061[1], attrs=(!isnothing(attrs1062) ? attrs1062 : Proto.Attribute[]), value_arity=abstraction_with_arity1061[2])
    result1064 = _t1851
    record_span!(parser, span_start1063, "Upsert")
    return result1064
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1852 = parse_bindings(parser)
    bindings1065 = _t1852
    _t1853 = parse_formula(parser)
    formula1066 = _t1853
    consume_literal!(parser, ")")
    _t1854 = Proto.Abstraction(vars=vcat(bindings1065[1], !isnothing(bindings1065[2]) ? bindings1065[2] : []), value=formula1066)
    return (_t1854, length(bindings1065[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1070 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1855 = parse_relation_id(parser)
    relation_id1067 = _t1855
    _t1856 = parse_abstraction(parser)
    abstraction1068 = _t1856
    if match_lookahead_literal(parser, "(", 0)
        _t1858 = parse_attrs(parser)
        _t1857 = _t1858
    else
        _t1857 = nothing
    end
    attrs1069 = _t1857
    consume_literal!(parser, ")")
    _t1859 = Proto.Break(name=relation_id1067, body=abstraction1068, attrs=(!isnothing(attrs1069) ? attrs1069 : Proto.Attribute[]))
    result1071 = _t1859
    record_span!(parser, span_start1070, "Break")
    return result1071
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1076 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1860 = parse_monoid(parser)
    monoid1072 = _t1860
    _t1861 = parse_relation_id(parser)
    relation_id1073 = _t1861
    _t1862 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1074 = _t1862
    if match_lookahead_literal(parser, "(", 0)
        _t1864 = parse_attrs(parser)
        _t1863 = _t1864
    else
        _t1863 = nothing
    end
    attrs1075 = _t1863
    consume_literal!(parser, ")")
    _t1865 = Proto.MonoidDef(monoid=monoid1072, name=relation_id1073, body=abstraction_with_arity1074[1], attrs=(!isnothing(attrs1075) ? attrs1075 : Proto.Attribute[]), value_arity=abstraction_with_arity1074[2])
    result1077 = _t1865
    record_span!(parser, span_start1076, "MonoidDef")
    return result1077
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1083 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1867 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1868 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1869 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1870 = 2
                    else
                        _t1870 = -1
                    end
                    _t1869 = _t1870
                end
                _t1868 = _t1869
            end
            _t1867 = _t1868
        end
        _t1866 = _t1867
    else
        _t1866 = -1
    end
    prediction1078 = _t1866
    if prediction1078 == 3
        _t1872 = parse_sum_monoid(parser)
        sum_monoid1082 = _t1872
        _t1873 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1082))
        _t1871 = _t1873
    else
        if prediction1078 == 2
            _t1875 = parse_max_monoid(parser)
            max_monoid1081 = _t1875
            _t1876 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1081))
            _t1874 = _t1876
        else
            if prediction1078 == 1
                _t1878 = parse_min_monoid(parser)
                min_monoid1080 = _t1878
                _t1879 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1080))
                _t1877 = _t1879
            else
                if prediction1078 == 0
                    _t1881 = parse_or_monoid(parser)
                    or_monoid1079 = _t1881
                    _t1882 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1079))
                    _t1880 = _t1882
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1877 = _t1880
            end
            _t1874 = _t1877
        end
        _t1871 = _t1874
    end
    result1084 = _t1871
    record_span!(parser, span_start1083, "Monoid")
    return result1084
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1085 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1883 = Proto.OrMonoid()
    result1086 = _t1883
    record_span!(parser, span_start1085, "OrMonoid")
    return result1086
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1088 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1884 = parse_type(parser)
    type1087 = _t1884
    consume_literal!(parser, ")")
    _t1885 = Proto.MinMonoid(var"#type"=type1087)
    result1089 = _t1885
    record_span!(parser, span_start1088, "MinMonoid")
    return result1089
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1091 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1886 = parse_type(parser)
    type1090 = _t1886
    consume_literal!(parser, ")")
    _t1887 = Proto.MaxMonoid(var"#type"=type1090)
    result1092 = _t1887
    record_span!(parser, span_start1091, "MaxMonoid")
    return result1092
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1094 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1888 = parse_type(parser)
    type1093 = _t1888
    consume_literal!(parser, ")")
    _t1889 = Proto.SumMonoid(var"#type"=type1093)
    result1095 = _t1889
    record_span!(parser, span_start1094, "SumMonoid")
    return result1095
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1100 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1890 = parse_monoid(parser)
    monoid1096 = _t1890
    _t1891 = parse_relation_id(parser)
    relation_id1097 = _t1891
    _t1892 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1098 = _t1892
    if match_lookahead_literal(parser, "(", 0)
        _t1894 = parse_attrs(parser)
        _t1893 = _t1894
    else
        _t1893 = nothing
    end
    attrs1099 = _t1893
    consume_literal!(parser, ")")
    _t1895 = Proto.MonusDef(monoid=monoid1096, name=relation_id1097, body=abstraction_with_arity1098[1], attrs=(!isnothing(attrs1099) ? attrs1099 : Proto.Attribute[]), value_arity=abstraction_with_arity1098[2])
    result1101 = _t1895
    record_span!(parser, span_start1100, "MonusDef")
    return result1101
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1106 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1896 = parse_relation_id(parser)
    relation_id1102 = _t1896
    _t1897 = parse_abstraction(parser)
    abstraction1103 = _t1897
    _t1898 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1104 = _t1898
    _t1899 = parse_functional_dependency_values(parser)
    functional_dependency_values1105 = _t1899
    consume_literal!(parser, ")")
    _t1900 = Proto.FunctionalDependency(guard=abstraction1103, keys=functional_dependency_keys1104, values=functional_dependency_values1105)
    _t1901 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1900), name=relation_id1102)
    result1107 = _t1901
    record_span!(parser, span_start1106, "Constraint")
    return result1107
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1108 = Proto.Var[]
    cond1109 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1109
        _t1902 = parse_var(parser)
        item1110 = _t1902
        push!(xs1108, item1110)
        cond1109 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1111 = xs1108
    consume_literal!(parser, ")")
    return vars1111
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1112 = Proto.Var[]
    cond1113 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1113
        _t1903 = parse_var(parser)
        item1114 = _t1903
        push!(xs1112, item1114)
        cond1113 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1115 = xs1112
    consume_literal!(parser, ")")
    return vars1115
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1121 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1905 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1906 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1907 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
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
    else
        _t1904 = -1
    end
    prediction1116 = _t1904
    if prediction1116 == 3
        _t1910 = parse_iceberg_data(parser)
        iceberg_data1120 = _t1910
        _t1911 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1120))
        _t1909 = _t1911
    else
        if prediction1116 == 2
            _t1913 = parse_csv_data(parser)
            csv_data1119 = _t1913
            _t1914 = Proto.Data(data_type=OneOf(:csv_data, csv_data1119))
            _t1912 = _t1914
        else
            if prediction1116 == 1
                _t1916 = parse_betree_relation(parser)
                betree_relation1118 = _t1916
                _t1917 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1118))
                _t1915 = _t1917
            else
                if prediction1116 == 0
                    _t1919 = parse_edb(parser)
                    edb1117 = _t1919
                    _t1920 = Proto.Data(data_type=OneOf(:edb, edb1117))
                    _t1918 = _t1920
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1915 = _t1918
            end
            _t1912 = _t1915
        end
        _t1909 = _t1912
    end
    result1122 = _t1909
    record_span!(parser, span_start1121, "Data")
    return result1122
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1126 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1921 = parse_relation_id(parser)
    relation_id1123 = _t1921
    _t1922 = parse_edb_path(parser)
    edb_path1124 = _t1922
    _t1923 = parse_edb_types(parser)
    edb_types1125 = _t1923
    consume_literal!(parser, ")")
    _t1924 = Proto.EDB(target_id=relation_id1123, path=edb_path1124, types=edb_types1125)
    result1127 = _t1924
    record_span!(parser, span_start1126, "EDB")
    return result1127
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1128 = String[]
    cond1129 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1129
        item1130 = consume_terminal!(parser, "STRING")
        push!(xs1128, item1130)
        cond1129 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1131 = xs1128
    consume_literal!(parser, "]")
    return strings1131
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1132 = Proto.var"#Type"[]
    cond1133 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1133
        _t1925 = parse_type(parser)
        item1134 = _t1925
        push!(xs1132, item1134)
        cond1133 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1135 = xs1132
    consume_literal!(parser, "]")
    return types1135
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1138 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1926 = parse_relation_id(parser)
    relation_id1136 = _t1926
    _t1927 = parse_betree_info(parser)
    betree_info1137 = _t1927
    consume_literal!(parser, ")")
    _t1928 = Proto.BeTreeRelation(name=relation_id1136, relation_info=betree_info1137)
    result1139 = _t1928
    record_span!(parser, span_start1138, "BeTreeRelation")
    return result1139
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1143 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1929 = parse_betree_info_key_types(parser)
    betree_info_key_types1140 = _t1929
    _t1930 = parse_betree_info_value_types(parser)
    betree_info_value_types1141 = _t1930
    _t1931 = parse_config_dict(parser)
    config_dict1142 = _t1931
    consume_literal!(parser, ")")
    _t1932 = construct_betree_info(parser, betree_info_key_types1140, betree_info_value_types1141, config_dict1142)
    result1144 = _t1932
    record_span!(parser, span_start1143, "BeTreeInfo")
    return result1144
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1145 = Proto.var"#Type"[]
    cond1146 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1146
        _t1933 = parse_type(parser)
        item1147 = _t1933
        push!(xs1145, item1147)
        cond1146 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1148 = xs1145
    consume_literal!(parser, ")")
    return types1148
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1149 = Proto.var"#Type"[]
    cond1150 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1150
        _t1934 = parse_type(parser)
        item1151 = _t1934
        push!(xs1149, item1151)
        cond1150 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1152 = xs1149
    consume_literal!(parser, ")")
    return types1152
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1157 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1935 = parse_csvlocator(parser)
    csvlocator1153 = _t1935
    _t1936 = parse_csv_config(parser)
    csv_config1154 = _t1936
    _t1937 = parse_gnf_columns(parser)
    gnf_columns1155 = _t1937
    _t1938 = parse_csv_asof(parser)
    csv_asof1156 = _t1938
    consume_literal!(parser, ")")
    _t1939 = Proto.CSVData(locator=csvlocator1153, config=csv_config1154, columns=gnf_columns1155, asof=csv_asof1156)
    result1158 = _t1939
    record_span!(parser, span_start1157, "CSVData")
    return result1158
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1161 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1941 = parse_csv_locator_paths(parser)
        _t1940 = _t1941
    else
        _t1940 = nothing
    end
    csv_locator_paths1159 = _t1940
    if match_lookahead_literal(parser, "(", 0)
        _t1943 = parse_csv_locator_inline_data(parser)
        _t1942 = _t1943
    else
        _t1942 = nothing
    end
    csv_locator_inline_data1160 = _t1942
    consume_literal!(parser, ")")
    _t1944 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1159) ? csv_locator_paths1159 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1160) ? csv_locator_inline_data1160 : "")))
    result1162 = _t1944
    record_span!(parser, span_start1161, "CSVLocator")
    return result1162
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1163 = String[]
    cond1164 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1164
        item1165 = consume_terminal!(parser, "STRING")
        push!(xs1163, item1165)
        cond1164 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1166 = xs1163
    consume_literal!(parser, ")")
    return strings1166
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1167 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1167
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1169 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1945 = parse_config_dict(parser)
    config_dict1168 = _t1945
    consume_literal!(parser, ")")
    _t1946 = construct_csv_config(parser, config_dict1168)
    result1170 = _t1946
    record_span!(parser, span_start1169, "CSVConfig")
    return result1170
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1171 = Proto.GNFColumn[]
    cond1172 = match_lookahead_literal(parser, "(", 0)
    while cond1172
        _t1947 = parse_gnf_column(parser)
        item1173 = _t1947
        push!(xs1171, item1173)
        cond1172 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1174 = xs1171
    consume_literal!(parser, ")")
    return gnf_columns1174
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1181 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1948 = parse_gnf_column_path(parser)
    gnf_column_path1175 = _t1948
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1950 = parse_relation_id(parser)
        _t1949 = _t1950
    else
        _t1949 = nothing
    end
    relation_id1176 = _t1949
    consume_literal!(parser, "[")
    xs1177 = Proto.var"#Type"[]
    cond1178 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1178
        _t1951 = parse_type(parser)
        item1179 = _t1951
        push!(xs1177, item1179)
        cond1178 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1180 = xs1177
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1952 = Proto.GNFColumn(column_path=gnf_column_path1175, target_id=relation_id1176, types=types1180)
    result1182 = _t1952
    record_span!(parser, span_start1181, "GNFColumn")
    return result1182
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1953 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1954 = 0
        else
            _t1954 = -1
        end
        _t1953 = _t1954
    end
    prediction1183 = _t1953
    if prediction1183 == 1
        consume_literal!(parser, "[")
        xs1185 = String[]
        cond1186 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1186
            item1187 = consume_terminal!(parser, "STRING")
            push!(xs1185, item1187)
            cond1186 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1188 = xs1185
        consume_literal!(parser, "]")
        _t1955 = strings1188
    else
        if prediction1183 == 0
            string1184 = consume_terminal!(parser, "STRING")
            _t1956 = String[string1184]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1955 = _t1956
    end
    return _t1955
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1189 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1189
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1194 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1957 = parse_iceberg_locator(parser)
    iceberg_locator1190 = _t1957
    _t1958 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1191 = _t1958
    _t1959 = parse_gnf_columns(parser)
    gnf_columns1192 = _t1959
    _t1960 = parse_boolean_value(parser)
    boolean_value1193 = _t1960
    consume_literal!(parser, ")")
    _t1961 = Proto.IcebergData(locator=iceberg_locator1190, config=iceberg_catalog_config1191, columns=gnf_columns1192, returns_delta=boolean_value1193)
    result1195 = _t1961
    record_span!(parser, span_start1194, "IcebergData")
    return result1195
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1204 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1196 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1197 = String[]
    cond1198 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1198
        item1199 = consume_terminal!(parser, "STRING")
        push!(xs1197, item1199)
        cond1198 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1200 = xs1197
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string_121201 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "from_snapshot", 1))
        _t1963 = parse_iceberg_from_snapshot(parser)
        _t1962 = _t1963
    else
        _t1962 = nothing
    end
    iceberg_from_snapshot1202 = _t1962
    if match_lookahead_literal(parser, "(", 0)
        _t1965 = parse_iceberg_to_snapshot(parser)
        _t1964 = _t1965
    else
        _t1964 = nothing
    end
    iceberg_to_snapshot1203 = _t1964
    consume_literal!(parser, ")")
    _t1966 = construct_iceberg_locator(parser, string1196, strings1200, string_121201, iceberg_from_snapshot1202, iceberg_to_snapshot1203)
    result1205 = _t1966
    record_span!(parser, span_start1204, "IcebergLocator")
    return result1205
end

function parse_iceberg_from_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "from_snapshot")
    string1206 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1206
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1207 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1207
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1218 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1208 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1968 = parse_iceberg_catalog_config_scope(parser)
        _t1967 = _t1968
    else
        _t1967 = nothing
    end
    iceberg_catalog_config_scope1209 = _t1967
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1210 = Tuple{String, String}[]
    cond1211 = match_lookahead_literal(parser, "(", 0)
    while cond1211
        _t1969 = parse_iceberg_property_entry(parser)
        item1212 = _t1969
        push!(xs1210, item1212)
        cond1211 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1213 = xs1210
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1214 = Tuple{String, String}[]
    cond1215 = match_lookahead_literal(parser, "(", 0)
    while cond1215
        _t1970 = parse_iceberg_masked_property_entry(parser)
        item1216 = _t1970
        push!(xs1214, item1216)
        cond1215 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_masked_property_entrys1217 = xs1214
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1971 = construct_iceberg_catalog_config(parser, string1208, iceberg_catalog_config_scope1209, iceberg_property_entrys1213, iceberg_masked_property_entrys1217)
    result1219 = _t1971
    record_span!(parser, span_start1218, "IcebergCatalogConfig")
    return result1219
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1220 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1220
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1221 = consume_terminal!(parser, "STRING")
    string_31222 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1221, string_31222,)
end

function parse_iceberg_masked_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1223 = consume_terminal!(parser, "STRING")
    string_31224 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1223, string_31224,)
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1226 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1972 = parse_fragment_id(parser)
    fragment_id1225 = _t1972
    consume_literal!(parser, ")")
    _t1973 = Proto.Undefine(fragment_id=fragment_id1225)
    result1227 = _t1973
    record_span!(parser, span_start1226, "Undefine")
    return result1227
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1232 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1228 = Proto.RelationId[]
    cond1229 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1229
        _t1974 = parse_relation_id(parser)
        item1230 = _t1974
        push!(xs1228, item1230)
        cond1229 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1231 = xs1228
    consume_literal!(parser, ")")
    _t1975 = Proto.Context(relations=relation_ids1231)
    result1233 = _t1975
    record_span!(parser, span_start1232, "Context")
    return result1233
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1238 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1234 = Proto.SnapshotMapping[]
    cond1235 = match_lookahead_literal(parser, "[", 0)
    while cond1235
        _t1976 = parse_snapshot_mapping(parser)
        item1236 = _t1976
        push!(xs1234, item1236)
        cond1235 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1237 = xs1234
    consume_literal!(parser, ")")
    _t1977 = Proto.Snapshot(mappings=snapshot_mappings1237)
    result1239 = _t1977
    record_span!(parser, span_start1238, "Snapshot")
    return result1239
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1242 = span_start(parser)
    _t1978 = parse_edb_path(parser)
    edb_path1240 = _t1978
    _t1979 = parse_relation_id(parser)
    relation_id1241 = _t1979
    _t1980 = Proto.SnapshotMapping(destination_path=edb_path1240, source_relation=relation_id1241)
    result1243 = _t1980
    record_span!(parser, span_start1242, "SnapshotMapping")
    return result1243
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1244 = Proto.Read[]
    cond1245 = match_lookahead_literal(parser, "(", 0)
    while cond1245
        _t1981 = parse_read(parser)
        item1246 = _t1981
        push!(xs1244, item1246)
        cond1245 = match_lookahead_literal(parser, "(", 0)
    end
    reads1247 = xs1244
    consume_literal!(parser, ")")
    return reads1247
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1254 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1983 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1984 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t1985 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t1986 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t1987 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t1988 = 3
                            else
                                _t1988 = -1
                            end
                            _t1987 = _t1988
                        end
                        _t1986 = _t1987
                    end
                    _t1985 = _t1986
                end
                _t1984 = _t1985
            end
            _t1983 = _t1984
        end
        _t1982 = _t1983
    else
        _t1982 = -1
    end
    prediction1248 = _t1982
    if prediction1248 == 4
        _t1990 = parse_export(parser)
        export1253 = _t1990
        _t1991 = Proto.Read(read_type=OneOf(:var"#export", export1253))
        _t1989 = _t1991
    else
        if prediction1248 == 3
            _t1993 = parse_abort(parser)
            abort1252 = _t1993
            _t1994 = Proto.Read(read_type=OneOf(:abort, abort1252))
            _t1992 = _t1994
        else
            if prediction1248 == 2
                _t1996 = parse_what_if(parser)
                what_if1251 = _t1996
                _t1997 = Proto.Read(read_type=OneOf(:what_if, what_if1251))
                _t1995 = _t1997
            else
                if prediction1248 == 1
                    _t1999 = parse_output(parser)
                    output1250 = _t1999
                    _t2000 = Proto.Read(read_type=OneOf(:output, output1250))
                    _t1998 = _t2000
                else
                    if prediction1248 == 0
                        _t2002 = parse_demand(parser)
                        demand1249 = _t2002
                        _t2003 = Proto.Read(read_type=OneOf(:demand, demand1249))
                        _t2001 = _t2003
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1998 = _t2001
                end
                _t1995 = _t1998
            end
            _t1992 = _t1995
        end
        _t1989 = _t1992
    end
    result1255 = _t1989
    record_span!(parser, span_start1254, "Read")
    return result1255
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1257 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t2004 = parse_relation_id(parser)
    relation_id1256 = _t2004
    consume_literal!(parser, ")")
    _t2005 = Proto.Demand(relation_id=relation_id1256)
    result1258 = _t2005
    record_span!(parser, span_start1257, "Demand")
    return result1258
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1261 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t2006 = parse_name(parser)
    name1259 = _t2006
    _t2007 = parse_relation_id(parser)
    relation_id1260 = _t2007
    consume_literal!(parser, ")")
    _t2008 = Proto.Output(name=name1259, relation_id=relation_id1260)
    result1262 = _t2008
    record_span!(parser, span_start1261, "Output")
    return result1262
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1265 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t2009 = parse_name(parser)
    name1263 = _t2009
    _t2010 = parse_epoch(parser)
    epoch1264 = _t2010
    consume_literal!(parser, ")")
    _t2011 = Proto.WhatIf(branch=name1263, epoch=epoch1264)
    result1266 = _t2011
    record_span!(parser, span_start1265, "WhatIf")
    return result1266
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1269 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2013 = parse_name(parser)
        _t2012 = _t2013
    else
        _t2012 = nothing
    end
    name1267 = _t2012
    _t2014 = parse_relation_id(parser)
    relation_id1268 = _t2014
    consume_literal!(parser, ")")
    _t2015 = Proto.Abort(name=(!isnothing(name1267) ? name1267 : "abort"), relation_id=relation_id1268)
    result1270 = _t2015
    record_span!(parser, span_start1269, "Abort")
    return result1270
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1274 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2017 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2018 = 0
            else
                _t2018 = -1
            end
            _t2017 = _t2018
        end
        _t2016 = _t2017
    else
        _t2016 = -1
    end
    prediction1271 = _t2016
    if prediction1271 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2020 = parse_export_iceberg_config(parser)
        export_iceberg_config1273 = _t2020
        consume_literal!(parser, ")")
        _t2021 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1273))
        _t2019 = _t2021
    else
        if prediction1271 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2023 = parse_export_csv_config(parser)
            export_csv_config1272 = _t2023
            consume_literal!(parser, ")")
            _t2024 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1272))
            _t2022 = _t2024
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2019 = _t2022
    end
    result1275 = _t2019
    record_span!(parser, span_start1274, "Export")
    return result1275
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1283 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2026 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2027 = 1
            else
                _t2027 = -1
            end
            _t2026 = _t2027
        end
        _t2025 = _t2026
    else
        _t2025 = -1
    end
    prediction1276 = _t2025
    if prediction1276 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2029 = parse_export_csv_path(parser)
        export_csv_path1280 = _t2029
        _t2030 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1281 = _t2030
        _t2031 = parse_config_dict(parser)
        config_dict1282 = _t2031
        consume_literal!(parser, ")")
        _t2032 = construct_export_csv_config(parser, export_csv_path1280, export_csv_columns_list1281, config_dict1282)
        _t2028 = _t2032
    else
        if prediction1276 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2034 = parse_export_csv_path(parser)
            export_csv_path1277 = _t2034
            _t2035 = parse_export_csv_source(parser)
            export_csv_source1278 = _t2035
            _t2036 = parse_csv_config(parser)
            csv_config1279 = _t2036
            consume_literal!(parser, ")")
            _t2037 = construct_export_csv_config_with_source(parser, export_csv_path1277, export_csv_source1278, csv_config1279)
            _t2033 = _t2037
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2028 = _t2033
    end
    result1284 = _t2028
    record_span!(parser, span_start1283, "ExportCSVConfig")
    return result1284
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1285 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1285
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1292 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2039 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2040 = 0
            else
                _t2040 = -1
            end
            _t2039 = _t2040
        end
        _t2038 = _t2039
    else
        _t2038 = -1
    end
    prediction1286 = _t2038
    if prediction1286 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2042 = parse_relation_id(parser)
        relation_id1291 = _t2042
        consume_literal!(parser, ")")
        _t2043 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1291))
        _t2041 = _t2043
    else
        if prediction1286 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1287 = Proto.ExportCSVColumn[]
            cond1288 = match_lookahead_literal(parser, "(", 0)
            while cond1288
                _t2045 = parse_export_csv_column(parser)
                item1289 = _t2045
                push!(xs1287, item1289)
                cond1288 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1290 = xs1287
            consume_literal!(parser, ")")
            _t2046 = Proto.ExportCSVColumns(columns=export_csv_columns1290)
            _t2047 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2046))
            _t2044 = _t2047
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2041 = _t2044
    end
    result1293 = _t2041
    record_span!(parser, span_start1292, "ExportCSVSource")
    return result1293
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1296 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1294 = consume_terminal!(parser, "STRING")
    _t2048 = parse_relation_id(parser)
    relation_id1295 = _t2048
    consume_literal!(parser, ")")
    _t2049 = Proto.ExportCSVColumn(column_name=string1294, column_data=relation_id1295)
    result1297 = _t2049
    record_span!(parser, span_start1296, "ExportCSVColumn")
    return result1297
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1298 = Proto.ExportCSVColumn[]
    cond1299 = match_lookahead_literal(parser, "(", 0)
    while cond1299
        _t2050 = parse_export_csv_column(parser)
        item1300 = _t2050
        push!(xs1298, item1300)
        cond1299 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1301 = xs1298
    consume_literal!(parser, ")")
    return export_csv_columns1301
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1314 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2051 = parse_iceberg_locator(parser)
    iceberg_locator1302 = _t2051
    _t2052 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1303 = _t2052
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_def")
    _t2053 = parse_relation_id(parser)
    relation_id1304 = _t2053
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1305 = Proto.ExportGNFColumn[]
    cond1306 = match_lookahead_literal(parser, "(", 0)
    while cond1306
        _t2054 = parse_export_gnf_column(parser)
        item1307 = _t2054
        push!(xs1305, item1307)
        cond1306 = match_lookahead_literal(parser, "(", 0)
    end
    export_gnf_columns1308 = xs1305
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_properties")
    xs1309 = Tuple{String, String}[]
    cond1310 = match_lookahead_literal(parser, "(", 0)
    while cond1310
        _t2055 = parse_iceberg_property_entry(parser)
        item1311 = _t2055
        push!(xs1309, item1311)
        cond1310 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1312 = xs1309
    consume_literal!(parser, ")")
    if match_lookahead_literal(parser, "{", 0)
        _t2057 = parse_config_dict(parser)
        _t2056 = _t2057
    else
        _t2056 = nothing
    end
    config_dict1313 = _t2056
    consume_literal!(parser, ")")
    _t2058 = construct_export_iceberg_config_full(parser, iceberg_locator1302, iceberg_catalog_config1303, relation_id1304, export_gnf_columns1308, iceberg_property_entrys1312, config_dict1313)
    result1315 = _t2058
    record_span!(parser, span_start1314, "ExportIcebergConfig")
    return result1315
end

function parse_export_gnf_column(parser::ParserState)::Proto.ExportGNFColumn
    span_start1318 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "gnf_column")
    string1316 = consume_terminal!(parser, "STRING")
    _t2059 = parse_boolean_value(parser)
    boolean_value1317 = _t2059
    consume_literal!(parser, ")")
    _t2060 = Proto.ExportGNFColumn(name=string1316, nullable=boolean_value1317)
    result1319 = _t2060
    record_span!(parser, span_start1318, "ExportGNFColumn")
    return result1319
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
