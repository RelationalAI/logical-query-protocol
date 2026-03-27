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
        _t2051 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2052 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2053 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2054 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2055 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2056 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2057 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2058 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2059 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2060 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2060
    _t2061 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2061
    _t2062 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2062
    _t2063 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2063
    _t2064 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2064
    _t2065 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2065
    _t2066 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2066
    _t2067 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2067
    _t2068 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2068
    _t2069 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2069
    _t2070 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2070
    _t2071 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2071
    _t2072 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2072
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2073 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2073
    _t2074 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2074
    _t2075 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2075
    _t2076 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2076
    _t2077 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2077
    _t2078 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2078
    _t2079 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2079
    _t2080 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2080
    _t2081 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2081
    _t2082 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2082
    _t2083 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2083
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2084 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2084
    _t2085 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2085
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
    _t2086 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2086
    _t2087 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2087
    _t2088 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2088
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2089 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2089
    _t2090 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2090
    _t2091 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2091
    _t2092 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2092
    _t2093 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2093
    _t2094 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2094
    _t2095 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2095
    _t2096 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2096
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2097 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2097
end

function construct_iceberg_catalog_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergCatalogConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    _t2098 = Proto.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(!isnothing(scope_opt) ? scope_opt : ""), properties=props, auth_properties=auth_props)
    return _t2098
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergCatalogConfig, columns::Vector{Proto.ExportIcebergColumn}, create_table_property_pairs::Vector{Tuple{String, String}}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    cfg = Dict((!isnothing(config_dict) ? config_dict : Tuple{String, Proto.Value}[]))
    _t2099 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
    prefix = _t2099
    _t2100 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
    target_file_size_bytes = _t2100
    _t2101 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
    compression = _t2101
    create_table_props = Dict(create_table_property_pairs)
    _t2102 = Proto.ExportIcebergConfig(locator=locator, config=config, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, create_table_properties=create_table_props)
    return _t2102
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start662 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1313 = parse_configure(parser)
        _t1312 = _t1313
    else
        _t1312 = nothing
    end
    configure656 = _t1312
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1315 = parse_sync(parser)
        _t1314 = _t1315
    else
        _t1314 = nothing
    end
    sync657 = _t1314
    xs658 = Proto.Epoch[]
    cond659 = match_lookahead_literal(parser, "(", 0)
    while cond659
        _t1316 = parse_epoch(parser)
        item660 = _t1316
        push!(xs658, item660)
        cond659 = match_lookahead_literal(parser, "(", 0)
    end
    epochs661 = xs658
    consume_literal!(parser, ")")
    _t1317 = default_configure(parser)
    _t1318 = Proto.Transaction(epochs=epochs661, configure=(!isnothing(configure656) ? configure656 : _t1317), sync=sync657)
    result663 = _t1318
    record_span!(parser, span_start662, "Transaction")
    return result663
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start665 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1319 = parse_config_dict(parser)
    config_dict664 = _t1319
    consume_literal!(parser, ")")
    _t1320 = construct_configure(parser, config_dict664)
    result666 = _t1320
    record_span!(parser, span_start665, "Configure")
    return result666
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs667 = Tuple{String, Proto.Value}[]
    cond668 = match_lookahead_literal(parser, ":", 0)
    while cond668
        _t1321 = parse_config_key_value(parser)
        item669 = _t1321
        push!(xs667, item669)
        cond668 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values670 = xs667
    consume_literal!(parser, "}")
    return config_key_values670
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol671 = consume_terminal!(parser, "SYMBOL")
    _t1322 = parse_raw_value(parser)
    raw_value672 = _t1322
    return (symbol671, raw_value672,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start686 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1323 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1324 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1325 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1327 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1328 = 0
                        else
                            _t1328 = -1
                        end
                        _t1327 = _t1328
                    end
                    _t1326 = _t1327
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1329 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1330 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1331 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1332 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1333 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1334 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1335 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1336 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1337 = 10
                                                    else
                                                        _t1337 = -1
                                                    end
                                                    _t1336 = _t1337
                                                end
                                                _t1335 = _t1336
                                            end
                                            _t1334 = _t1335
                                        end
                                        _t1333 = _t1334
                                    end
                                    _t1332 = _t1333
                                end
                                _t1331 = _t1332
                            end
                            _t1330 = _t1331
                        end
                        _t1329 = _t1330
                    end
                    _t1326 = _t1329
                end
                _t1325 = _t1326
            end
            _t1324 = _t1325
        end
        _t1323 = _t1324
    end
    prediction673 = _t1323
    if prediction673 == 12
        _t1339 = parse_boolean_value(parser)
        boolean_value685 = _t1339
        _t1340 = Proto.Value(value=OneOf(:boolean_value, boolean_value685))
        _t1338 = _t1340
    else
        if prediction673 == 11
            consume_literal!(parser, "missing")
            _t1342 = Proto.MissingValue()
            _t1343 = Proto.Value(value=OneOf(:missing_value, _t1342))
            _t1341 = _t1343
        else
            if prediction673 == 10
                decimal684 = consume_terminal!(parser, "DECIMAL")
                _t1345 = Proto.Value(value=OneOf(:decimal_value, decimal684))
                _t1344 = _t1345
            else
                if prediction673 == 9
                    int128683 = consume_terminal!(parser, "INT128")
                    _t1347 = Proto.Value(value=OneOf(:int128_value, int128683))
                    _t1346 = _t1347
                else
                    if prediction673 == 8
                        uint128682 = consume_terminal!(parser, "UINT128")
                        _t1349 = Proto.Value(value=OneOf(:uint128_value, uint128682))
                        _t1348 = _t1349
                    else
                        if prediction673 == 7
                            uint32681 = consume_terminal!(parser, "UINT32")
                            _t1351 = Proto.Value(value=OneOf(:uint32_value, uint32681))
                            _t1350 = _t1351
                        else
                            if prediction673 == 6
                                float680 = consume_terminal!(parser, "FLOAT")
                                _t1353 = Proto.Value(value=OneOf(:float_value, float680))
                                _t1352 = _t1353
                            else
                                if prediction673 == 5
                                    float32679 = consume_terminal!(parser, "FLOAT32")
                                    _t1355 = Proto.Value(value=OneOf(:float32_value, float32679))
                                    _t1354 = _t1355
                                else
                                    if prediction673 == 4
                                        int678 = consume_terminal!(parser, "INT")
                                        _t1357 = Proto.Value(value=OneOf(:int_value, int678))
                                        _t1356 = _t1357
                                    else
                                        if prediction673 == 3
                                            int32677 = consume_terminal!(parser, "INT32")
                                            _t1359 = Proto.Value(value=OneOf(:int32_value, int32677))
                                            _t1358 = _t1359
                                        else
                                            if prediction673 == 2
                                                string676 = consume_terminal!(parser, "STRING")
                                                _t1361 = Proto.Value(value=OneOf(:string_value, string676))
                                                _t1360 = _t1361
                                            else
                                                if prediction673 == 1
                                                    _t1363 = parse_raw_datetime(parser)
                                                    raw_datetime675 = _t1363
                                                    _t1364 = Proto.Value(value=OneOf(:datetime_value, raw_datetime675))
                                                    _t1362 = _t1364
                                                else
                                                    if prediction673 == 0
                                                        _t1366 = parse_raw_date(parser)
                                                        raw_date674 = _t1366
                                                        _t1367 = Proto.Value(value=OneOf(:date_value, raw_date674))
                                                        _t1365 = _t1367
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1362 = _t1365
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
                            _t1350 = _t1352
                        end
                        _t1348 = _t1350
                    end
                    _t1346 = _t1348
                end
                _t1344 = _t1346
            end
            _t1341 = _t1344
        end
        _t1338 = _t1341
    end
    result687 = _t1338
    record_span!(parser, span_start686, "Value")
    return result687
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start691 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int688 = consume_terminal!(parser, "INT")
    int_3689 = consume_terminal!(parser, "INT")
    int_4690 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1368 = Proto.DateValue(year=Int32(int688), month=Int32(int_3689), day=Int32(int_4690))
    result692 = _t1368
    record_span!(parser, span_start691, "DateValue")
    return result692
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start700 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int693 = consume_terminal!(parser, "INT")
    int_3694 = consume_terminal!(parser, "INT")
    int_4695 = consume_terminal!(parser, "INT")
    int_5696 = consume_terminal!(parser, "INT")
    int_6697 = consume_terminal!(parser, "INT")
    int_7698 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1369 = consume_terminal!(parser, "INT")
    else
        _t1369 = nothing
    end
    int_8699 = _t1369
    consume_literal!(parser, ")")
    _t1370 = Proto.DateTimeValue(year=Int32(int693), month=Int32(int_3694), day=Int32(int_4695), hour=Int32(int_5696), minute=Int32(int_6697), second=Int32(int_7698), microsecond=Int32((!isnothing(int_8699) ? int_8699 : 0)))
    result701 = _t1370
    record_span!(parser, span_start700, "DateTimeValue")
    return result701
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1371 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1372 = 1
        else
            _t1372 = -1
        end
        _t1371 = _t1372
    end
    prediction702 = _t1371
    if prediction702 == 1
        consume_literal!(parser, "false")
        _t1373 = false
    else
        if prediction702 == 0
            consume_literal!(parser, "true")
            _t1374 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1373 = _t1374
    end
    return _t1373
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start707 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs703 = Proto.FragmentId[]
    cond704 = match_lookahead_literal(parser, ":", 0)
    while cond704
        _t1375 = parse_fragment_id(parser)
        item705 = _t1375
        push!(xs703, item705)
        cond704 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids706 = xs703
    consume_literal!(parser, ")")
    _t1376 = Proto.Sync(fragments=fragment_ids706)
    result708 = _t1376
    record_span!(parser, span_start707, "Sync")
    return result708
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start710 = span_start(parser)
    consume_literal!(parser, ":")
    symbol709 = consume_terminal!(parser, "SYMBOL")
    result711 = Proto.FragmentId(Vector{UInt8}(symbol709))
    record_span!(parser, span_start710, "FragmentId")
    return result711
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start714 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1378 = parse_epoch_writes(parser)
        _t1377 = _t1378
    else
        _t1377 = nothing
    end
    epoch_writes712 = _t1377
    if match_lookahead_literal(parser, "(", 0)
        _t1380 = parse_epoch_reads(parser)
        _t1379 = _t1380
    else
        _t1379 = nothing
    end
    epoch_reads713 = _t1379
    consume_literal!(parser, ")")
    _t1381 = Proto.Epoch(writes=(!isnothing(epoch_writes712) ? epoch_writes712 : Proto.Write[]), reads=(!isnothing(epoch_reads713) ? epoch_reads713 : Proto.Read[]))
    result715 = _t1381
    record_span!(parser, span_start714, "Epoch")
    return result715
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs716 = Proto.Write[]
    cond717 = match_lookahead_literal(parser, "(", 0)
    while cond717
        _t1382 = parse_write(parser)
        item718 = _t1382
        push!(xs716, item718)
        cond717 = match_lookahead_literal(parser, "(", 0)
    end
    writes719 = xs716
    consume_literal!(parser, ")")
    return writes719
end

function parse_write(parser::ParserState)::Proto.Write
    span_start725 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1384 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1385 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1386 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1387 = 2
                    else
                        _t1387 = -1
                    end
                    _t1386 = _t1387
                end
                _t1385 = _t1386
            end
            _t1384 = _t1385
        end
        _t1383 = _t1384
    else
        _t1383 = -1
    end
    prediction720 = _t1383
    if prediction720 == 3
        _t1389 = parse_snapshot(parser)
        snapshot724 = _t1389
        _t1390 = Proto.Write(write_type=OneOf(:snapshot, snapshot724))
        _t1388 = _t1390
    else
        if prediction720 == 2
            _t1392 = parse_context(parser)
            context723 = _t1392
            _t1393 = Proto.Write(write_type=OneOf(:context, context723))
            _t1391 = _t1393
        else
            if prediction720 == 1
                _t1395 = parse_undefine(parser)
                undefine722 = _t1395
                _t1396 = Proto.Write(write_type=OneOf(:undefine, undefine722))
                _t1394 = _t1396
            else
                if prediction720 == 0
                    _t1398 = parse_define(parser)
                    define721 = _t1398
                    _t1399 = Proto.Write(write_type=OneOf(:define, define721))
                    _t1397 = _t1399
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1394 = _t1397
            end
            _t1391 = _t1394
        end
        _t1388 = _t1391
    end
    result726 = _t1388
    record_span!(parser, span_start725, "Write")
    return result726
end

function parse_define(parser::ParserState)::Proto.Define
    span_start728 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1400 = parse_fragment(parser)
    fragment727 = _t1400
    consume_literal!(parser, ")")
    _t1401 = Proto.Define(fragment=fragment727)
    result729 = _t1401
    record_span!(parser, span_start728, "Define")
    return result729
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start735 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1402 = parse_new_fragment_id(parser)
    new_fragment_id730 = _t1402
    xs731 = Proto.Declaration[]
    cond732 = match_lookahead_literal(parser, "(", 0)
    while cond732
        _t1403 = parse_declaration(parser)
        item733 = _t1403
        push!(xs731, item733)
        cond732 = match_lookahead_literal(parser, "(", 0)
    end
    declarations734 = xs731
    consume_literal!(parser, ")")
    result736 = construct_fragment(parser, new_fragment_id730, declarations734)
    record_span!(parser, span_start735, "Fragment")
    return result736
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start738 = span_start(parser)
    _t1404 = parse_fragment_id(parser)
    fragment_id737 = _t1404
    start_fragment!(parser, fragment_id737)
    result739 = fragment_id737
    record_span!(parser, span_start738, "FragmentId")
    return result739
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start745 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1406 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1407 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1408 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1409 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1410 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1411 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1412 = 1
                                else
                                    _t1412 = -1
                                end
                                _t1411 = _t1412
                            end
                            _t1410 = _t1411
                        end
                        _t1409 = _t1410
                    end
                    _t1408 = _t1409
                end
                _t1407 = _t1408
            end
            _t1406 = _t1407
        end
        _t1405 = _t1406
    else
        _t1405 = -1
    end
    prediction740 = _t1405
    if prediction740 == 3
        _t1414 = parse_data(parser)
        data744 = _t1414
        _t1415 = Proto.Declaration(declaration_type=OneOf(:data, data744))
        _t1413 = _t1415
    else
        if prediction740 == 2
            _t1417 = parse_constraint(parser)
            constraint743 = _t1417
            _t1418 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint743))
            _t1416 = _t1418
        else
            if prediction740 == 1
                _t1420 = parse_algorithm(parser)
                algorithm742 = _t1420
                _t1421 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm742))
                _t1419 = _t1421
            else
                if prediction740 == 0
                    _t1423 = parse_def(parser)
                    def741 = _t1423
                    _t1424 = Proto.Declaration(declaration_type=OneOf(:def, def741))
                    _t1422 = _t1424
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1419 = _t1422
            end
            _t1416 = _t1419
        end
        _t1413 = _t1416
    end
    result746 = _t1413
    record_span!(parser, span_start745, "Declaration")
    return result746
end

function parse_def(parser::ParserState)::Proto.Def
    span_start750 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1425 = parse_relation_id(parser)
    relation_id747 = _t1425
    _t1426 = parse_abstraction(parser)
    abstraction748 = _t1426
    if match_lookahead_literal(parser, "(", 0)
        _t1428 = parse_attrs(parser)
        _t1427 = _t1428
    else
        _t1427 = nothing
    end
    attrs749 = _t1427
    consume_literal!(parser, ")")
    _t1429 = Proto.Def(name=relation_id747, body=abstraction748, attrs=(!isnothing(attrs749) ? attrs749 : Proto.Attribute[]))
    result751 = _t1429
    record_span!(parser, span_start750, "Def")
    return result751
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start755 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1430 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1431 = 1
        else
            _t1431 = -1
        end
        _t1430 = _t1431
    end
    prediction752 = _t1430
    if prediction752 == 1
        uint128754 = consume_terminal!(parser, "UINT128")
        _t1432 = Proto.RelationId(uint128754.low, uint128754.high)
    else
        if prediction752 == 0
            consume_literal!(parser, ":")
            symbol753 = consume_terminal!(parser, "SYMBOL")
            _t1433 = relation_id_from_string(parser, symbol753)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1432 = _t1433
    end
    result756 = _t1432
    record_span!(parser, span_start755, "RelationId")
    return result756
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start759 = span_start(parser)
    consume_literal!(parser, "(")
    _t1434 = parse_bindings(parser)
    bindings757 = _t1434
    _t1435 = parse_formula(parser)
    formula758 = _t1435
    consume_literal!(parser, ")")
    _t1436 = Proto.Abstraction(vars=vcat(bindings757[1], !isnothing(bindings757[2]) ? bindings757[2] : []), value=formula758)
    result760 = _t1436
    record_span!(parser, span_start759, "Abstraction")
    return result760
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs761 = Proto.Binding[]
    cond762 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond762
        _t1437 = parse_binding(parser)
        item763 = _t1437
        push!(xs761, item763)
        cond762 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings764 = xs761
    if match_lookahead_literal(parser, "|", 0)
        _t1439 = parse_value_bindings(parser)
        _t1438 = _t1439
    else
        _t1438 = nothing
    end
    value_bindings765 = _t1438
    consume_literal!(parser, "]")
    return (bindings764, (!isnothing(value_bindings765) ? value_bindings765 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start768 = span_start(parser)
    symbol766 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1440 = parse_type(parser)
    type767 = _t1440
    _t1441 = Proto.Var(name=symbol766)
    _t1442 = Proto.Binding(var=_t1441, var"#type"=type767)
    result769 = _t1442
    record_span!(parser, span_start768, "Binding")
    return result769
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start785 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1443 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1444 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1445 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1446 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1447 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1448 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1449 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1450 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1451 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1452 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1453 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1454 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1455 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1456 = 9
                                                        else
                                                            _t1456 = -1
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
    prediction770 = _t1443
    if prediction770 == 13
        _t1458 = parse_uint32_type(parser)
        uint32_type784 = _t1458
        _t1459 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type784))
        _t1457 = _t1459
    else
        if prediction770 == 12
            _t1461 = parse_float32_type(parser)
            float32_type783 = _t1461
            _t1462 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type783))
            _t1460 = _t1462
        else
            if prediction770 == 11
                _t1464 = parse_int32_type(parser)
                int32_type782 = _t1464
                _t1465 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type782))
                _t1463 = _t1465
            else
                if prediction770 == 10
                    _t1467 = parse_boolean_type(parser)
                    boolean_type781 = _t1467
                    _t1468 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type781))
                    _t1466 = _t1468
                else
                    if prediction770 == 9
                        _t1470 = parse_decimal_type(parser)
                        decimal_type780 = _t1470
                        _t1471 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type780))
                        _t1469 = _t1471
                    else
                        if prediction770 == 8
                            _t1473 = parse_missing_type(parser)
                            missing_type779 = _t1473
                            _t1474 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type779))
                            _t1472 = _t1474
                        else
                            if prediction770 == 7
                                _t1476 = parse_datetime_type(parser)
                                datetime_type778 = _t1476
                                _t1477 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type778))
                                _t1475 = _t1477
                            else
                                if prediction770 == 6
                                    _t1479 = parse_date_type(parser)
                                    date_type777 = _t1479
                                    _t1480 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type777))
                                    _t1478 = _t1480
                                else
                                    if prediction770 == 5
                                        _t1482 = parse_int128_type(parser)
                                        int128_type776 = _t1482
                                        _t1483 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type776))
                                        _t1481 = _t1483
                                    else
                                        if prediction770 == 4
                                            _t1485 = parse_uint128_type(parser)
                                            uint128_type775 = _t1485
                                            _t1486 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type775))
                                            _t1484 = _t1486
                                        else
                                            if prediction770 == 3
                                                _t1488 = parse_float_type(parser)
                                                float_type774 = _t1488
                                                _t1489 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type774))
                                                _t1487 = _t1489
                                            else
                                                if prediction770 == 2
                                                    _t1491 = parse_int_type(parser)
                                                    int_type773 = _t1491
                                                    _t1492 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type773))
                                                    _t1490 = _t1492
                                                else
                                                    if prediction770 == 1
                                                        _t1494 = parse_string_type(parser)
                                                        string_type772 = _t1494
                                                        _t1495 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type772))
                                                        _t1493 = _t1495
                                                    else
                                                        if prediction770 == 0
                                                            _t1497 = parse_unspecified_type(parser)
                                                            unspecified_type771 = _t1497
                                                            _t1498 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type771))
                                                            _t1496 = _t1498
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1493 = _t1496
                                                    end
                                                    _t1490 = _t1493
                                                end
                                                _t1487 = _t1490
                                            end
                                            _t1484 = _t1487
                                        end
                                        _t1481 = _t1484
                                    end
                                    _t1478 = _t1481
                                end
                                _t1475 = _t1478
                            end
                            _t1472 = _t1475
                        end
                        _t1469 = _t1472
                    end
                    _t1466 = _t1469
                end
                _t1463 = _t1466
            end
            _t1460 = _t1463
        end
        _t1457 = _t1460
    end
    result786 = _t1457
    record_span!(parser, span_start785, "Type")
    return result786
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start787 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1499 = Proto.UnspecifiedType()
    result788 = _t1499
    record_span!(parser, span_start787, "UnspecifiedType")
    return result788
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start789 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1500 = Proto.StringType()
    result790 = _t1500
    record_span!(parser, span_start789, "StringType")
    return result790
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start791 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1501 = Proto.IntType()
    result792 = _t1501
    record_span!(parser, span_start791, "IntType")
    return result792
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start793 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1502 = Proto.FloatType()
    result794 = _t1502
    record_span!(parser, span_start793, "FloatType")
    return result794
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start795 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1503 = Proto.UInt128Type()
    result796 = _t1503
    record_span!(parser, span_start795, "UInt128Type")
    return result796
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start797 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1504 = Proto.Int128Type()
    result798 = _t1504
    record_span!(parser, span_start797, "Int128Type")
    return result798
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start799 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1505 = Proto.DateType()
    result800 = _t1505
    record_span!(parser, span_start799, "DateType")
    return result800
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start801 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1506 = Proto.DateTimeType()
    result802 = _t1506
    record_span!(parser, span_start801, "DateTimeType")
    return result802
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start803 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1507 = Proto.MissingType()
    result804 = _t1507
    record_span!(parser, span_start803, "MissingType")
    return result804
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start807 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int805 = consume_terminal!(parser, "INT")
    int_3806 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1508 = Proto.DecimalType(precision=Int32(int805), scale=Int32(int_3806))
    result808 = _t1508
    record_span!(parser, span_start807, "DecimalType")
    return result808
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start809 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1509 = Proto.BooleanType()
    result810 = _t1509
    record_span!(parser, span_start809, "BooleanType")
    return result810
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start811 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1510 = Proto.Int32Type()
    result812 = _t1510
    record_span!(parser, span_start811, "Int32Type")
    return result812
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start813 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1511 = Proto.Float32Type()
    result814 = _t1511
    record_span!(parser, span_start813, "Float32Type")
    return result814
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start815 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1512 = Proto.UInt32Type()
    result816 = _t1512
    record_span!(parser, span_start815, "UInt32Type")
    return result816
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs817 = Proto.Binding[]
    cond818 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond818
        _t1513 = parse_binding(parser)
        item819 = _t1513
        push!(xs817, item819)
        cond818 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings820 = xs817
    return bindings820
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start835 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1515 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1516 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1517 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1518 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1519 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1520 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1521 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1522 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1523 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1524 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1525 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1526 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1527 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1528 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1529 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1530 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1531 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1532 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1533 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1534 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1535 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1536 = 10
                                                                                            else
                                                                                                _t1536 = -1
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
                end
                _t1516 = _t1517
            end
            _t1515 = _t1516
        end
        _t1514 = _t1515
    else
        _t1514 = -1
    end
    prediction821 = _t1514
    if prediction821 == 12
        _t1538 = parse_cast(parser)
        cast834 = _t1538
        _t1539 = Proto.Formula(formula_type=OneOf(:cast, cast834))
        _t1537 = _t1539
    else
        if prediction821 == 11
            _t1541 = parse_rel_atom(parser)
            rel_atom833 = _t1541
            _t1542 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom833))
            _t1540 = _t1542
        else
            if prediction821 == 10
                _t1544 = parse_primitive(parser)
                primitive832 = _t1544
                _t1545 = Proto.Formula(formula_type=OneOf(:primitive, primitive832))
                _t1543 = _t1545
            else
                if prediction821 == 9
                    _t1547 = parse_pragma(parser)
                    pragma831 = _t1547
                    _t1548 = Proto.Formula(formula_type=OneOf(:pragma, pragma831))
                    _t1546 = _t1548
                else
                    if prediction821 == 8
                        _t1550 = parse_atom(parser)
                        atom830 = _t1550
                        _t1551 = Proto.Formula(formula_type=OneOf(:atom, atom830))
                        _t1549 = _t1551
                    else
                        if prediction821 == 7
                            _t1553 = parse_ffi(parser)
                            ffi829 = _t1553
                            _t1554 = Proto.Formula(formula_type=OneOf(:ffi, ffi829))
                            _t1552 = _t1554
                        else
                            if prediction821 == 6
                                _t1556 = parse_not(parser)
                                not828 = _t1556
                                _t1557 = Proto.Formula(formula_type=OneOf(:not, not828))
                                _t1555 = _t1557
                            else
                                if prediction821 == 5
                                    _t1559 = parse_disjunction(parser)
                                    disjunction827 = _t1559
                                    _t1560 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction827))
                                    _t1558 = _t1560
                                else
                                    if prediction821 == 4
                                        _t1562 = parse_conjunction(parser)
                                        conjunction826 = _t1562
                                        _t1563 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction826))
                                        _t1561 = _t1563
                                    else
                                        if prediction821 == 3
                                            _t1565 = parse_reduce(parser)
                                            reduce825 = _t1565
                                            _t1566 = Proto.Formula(formula_type=OneOf(:reduce, reduce825))
                                            _t1564 = _t1566
                                        else
                                            if prediction821 == 2
                                                _t1568 = parse_exists(parser)
                                                exists824 = _t1568
                                                _t1569 = Proto.Formula(formula_type=OneOf(:exists, exists824))
                                                _t1567 = _t1569
                                            else
                                                if prediction821 == 1
                                                    _t1571 = parse_false(parser)
                                                    false823 = _t1571
                                                    _t1572 = Proto.Formula(formula_type=OneOf(:disjunction, false823))
                                                    _t1570 = _t1572
                                                else
                                                    if prediction821 == 0
                                                        _t1574 = parse_true(parser)
                                                        true822 = _t1574
                                                        _t1575 = Proto.Formula(formula_type=OneOf(:conjunction, true822))
                                                        _t1573 = _t1575
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1570 = _t1573
                                                end
                                                _t1567 = _t1570
                                            end
                                            _t1564 = _t1567
                                        end
                                        _t1561 = _t1564
                                    end
                                    _t1558 = _t1561
                                end
                                _t1555 = _t1558
                            end
                            _t1552 = _t1555
                        end
                        _t1549 = _t1552
                    end
                    _t1546 = _t1549
                end
                _t1543 = _t1546
            end
            _t1540 = _t1543
        end
        _t1537 = _t1540
    end
    result836 = _t1537
    record_span!(parser, span_start835, "Formula")
    return result836
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start837 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1576 = Proto.Conjunction(args=Proto.Formula[])
    result838 = _t1576
    record_span!(parser, span_start837, "Conjunction")
    return result838
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start839 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1577 = Proto.Disjunction(args=Proto.Formula[])
    result840 = _t1577
    record_span!(parser, span_start839, "Disjunction")
    return result840
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start843 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1578 = parse_bindings(parser)
    bindings841 = _t1578
    _t1579 = parse_formula(parser)
    formula842 = _t1579
    consume_literal!(parser, ")")
    _t1580 = Proto.Abstraction(vars=vcat(bindings841[1], !isnothing(bindings841[2]) ? bindings841[2] : []), value=formula842)
    _t1581 = Proto.Exists(body=_t1580)
    result844 = _t1581
    record_span!(parser, span_start843, "Exists")
    return result844
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start848 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1582 = parse_abstraction(parser)
    abstraction845 = _t1582
    _t1583 = parse_abstraction(parser)
    abstraction_3846 = _t1583
    _t1584 = parse_terms(parser)
    terms847 = _t1584
    consume_literal!(parser, ")")
    _t1585 = Proto.Reduce(op=abstraction845, body=abstraction_3846, terms=terms847)
    result849 = _t1585
    record_span!(parser, span_start848, "Reduce")
    return result849
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs850 = Proto.Term[]
    cond851 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond851
        _t1586 = parse_term(parser)
        item852 = _t1586
        push!(xs850, item852)
        cond851 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms853 = xs850
    consume_literal!(parser, ")")
    return terms853
end

function parse_term(parser::ParserState)::Proto.Term
    span_start857 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1587 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1588 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1589 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1590 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1591 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1592 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1593 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1594 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1595 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1596 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1597 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1598 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1599 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1600 = 1
                                                        else
                                                            _t1600 = -1
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
                                    _t1594 = _t1595
                                end
                                _t1593 = _t1594
                            end
                            _t1592 = _t1593
                        end
                        _t1591 = _t1592
                    end
                    _t1590 = _t1591
                end
                _t1589 = _t1590
            end
            _t1588 = _t1589
        end
        _t1587 = _t1588
    end
    prediction854 = _t1587
    if prediction854 == 1
        _t1602 = parse_value(parser)
        value856 = _t1602
        _t1603 = Proto.Term(term_type=OneOf(:constant, value856))
        _t1601 = _t1603
    else
        if prediction854 == 0
            _t1605 = parse_var(parser)
            var855 = _t1605
            _t1606 = Proto.Term(term_type=OneOf(:var, var855))
            _t1604 = _t1606
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1601 = _t1604
    end
    result858 = _t1601
    record_span!(parser, span_start857, "Term")
    return result858
end

function parse_var(parser::ParserState)::Proto.Var
    span_start860 = span_start(parser)
    symbol859 = consume_terminal!(parser, "SYMBOL")
    _t1607 = Proto.Var(name=symbol859)
    result861 = _t1607
    record_span!(parser, span_start860, "Var")
    return result861
end

function parse_value(parser::ParserState)::Proto.Value
    span_start875 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1608 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1609 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1610 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1612 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1613 = 0
                        else
                            _t1613 = -1
                        end
                        _t1612 = _t1613
                    end
                    _t1611 = _t1612
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1614 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1615 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1616 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1617 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1618 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1619 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1620 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1621 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1622 = 10
                                                    else
                                                        _t1622 = -1
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
                    _t1611 = _t1614
                end
                _t1610 = _t1611
            end
            _t1609 = _t1610
        end
        _t1608 = _t1609
    end
    prediction862 = _t1608
    if prediction862 == 12
        _t1624 = parse_boolean_value(parser)
        boolean_value874 = _t1624
        _t1625 = Proto.Value(value=OneOf(:boolean_value, boolean_value874))
        _t1623 = _t1625
    else
        if prediction862 == 11
            consume_literal!(parser, "missing")
            _t1627 = Proto.MissingValue()
            _t1628 = Proto.Value(value=OneOf(:missing_value, _t1627))
            _t1626 = _t1628
        else
            if prediction862 == 10
                formatted_decimal873 = consume_terminal!(parser, "DECIMAL")
                _t1630 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal873))
                _t1629 = _t1630
            else
                if prediction862 == 9
                    formatted_int128872 = consume_terminal!(parser, "INT128")
                    _t1632 = Proto.Value(value=OneOf(:int128_value, formatted_int128872))
                    _t1631 = _t1632
                else
                    if prediction862 == 8
                        formatted_uint128871 = consume_terminal!(parser, "UINT128")
                        _t1634 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128871))
                        _t1633 = _t1634
                    else
                        if prediction862 == 7
                            formatted_uint32870 = consume_terminal!(parser, "UINT32")
                            _t1636 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32870))
                            _t1635 = _t1636
                        else
                            if prediction862 == 6
                                formatted_float869 = consume_terminal!(parser, "FLOAT")
                                _t1638 = Proto.Value(value=OneOf(:float_value, formatted_float869))
                                _t1637 = _t1638
                            else
                                if prediction862 == 5
                                    formatted_float32868 = consume_terminal!(parser, "FLOAT32")
                                    _t1640 = Proto.Value(value=OneOf(:float32_value, formatted_float32868))
                                    _t1639 = _t1640
                                else
                                    if prediction862 == 4
                                        formatted_int867 = consume_terminal!(parser, "INT")
                                        _t1642 = Proto.Value(value=OneOf(:int_value, formatted_int867))
                                        _t1641 = _t1642
                                    else
                                        if prediction862 == 3
                                            formatted_int32866 = consume_terminal!(parser, "INT32")
                                            _t1644 = Proto.Value(value=OneOf(:int32_value, formatted_int32866))
                                            _t1643 = _t1644
                                        else
                                            if prediction862 == 2
                                                formatted_string865 = consume_terminal!(parser, "STRING")
                                                _t1646 = Proto.Value(value=OneOf(:string_value, formatted_string865))
                                                _t1645 = _t1646
                                            else
                                                if prediction862 == 1
                                                    _t1648 = parse_datetime(parser)
                                                    datetime864 = _t1648
                                                    _t1649 = Proto.Value(value=OneOf(:datetime_value, datetime864))
                                                    _t1647 = _t1649
                                                else
                                                    if prediction862 == 0
                                                        _t1651 = parse_date(parser)
                                                        date863 = _t1651
                                                        _t1652 = Proto.Value(value=OneOf(:date_value, date863))
                                                        _t1650 = _t1652
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1647 = _t1650
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
                            _t1635 = _t1637
                        end
                        _t1633 = _t1635
                    end
                    _t1631 = _t1633
                end
                _t1629 = _t1631
            end
            _t1626 = _t1629
        end
        _t1623 = _t1626
    end
    result876 = _t1623
    record_span!(parser, span_start875, "Value")
    return result876
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start880 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int877 = consume_terminal!(parser, "INT")
    formatted_int_3878 = consume_terminal!(parser, "INT")
    formatted_int_4879 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1653 = Proto.DateValue(year=Int32(formatted_int877), month=Int32(formatted_int_3878), day=Int32(formatted_int_4879))
    result881 = _t1653
    record_span!(parser, span_start880, "DateValue")
    return result881
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start889 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int882 = consume_terminal!(parser, "INT")
    formatted_int_3883 = consume_terminal!(parser, "INT")
    formatted_int_4884 = consume_terminal!(parser, "INT")
    formatted_int_5885 = consume_terminal!(parser, "INT")
    formatted_int_6886 = consume_terminal!(parser, "INT")
    formatted_int_7887 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1654 = consume_terminal!(parser, "INT")
    else
        _t1654 = nothing
    end
    formatted_int_8888 = _t1654
    consume_literal!(parser, ")")
    _t1655 = Proto.DateTimeValue(year=Int32(formatted_int882), month=Int32(formatted_int_3883), day=Int32(formatted_int_4884), hour=Int32(formatted_int_5885), minute=Int32(formatted_int_6886), second=Int32(formatted_int_7887), microsecond=Int32((!isnothing(formatted_int_8888) ? formatted_int_8888 : 0)))
    result890 = _t1655
    record_span!(parser, span_start889, "DateTimeValue")
    return result890
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start895 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs891 = Proto.Formula[]
    cond892 = match_lookahead_literal(parser, "(", 0)
    while cond892
        _t1656 = parse_formula(parser)
        item893 = _t1656
        push!(xs891, item893)
        cond892 = match_lookahead_literal(parser, "(", 0)
    end
    formulas894 = xs891
    consume_literal!(parser, ")")
    _t1657 = Proto.Conjunction(args=formulas894)
    result896 = _t1657
    record_span!(parser, span_start895, "Conjunction")
    return result896
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start901 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs897 = Proto.Formula[]
    cond898 = match_lookahead_literal(parser, "(", 0)
    while cond898
        _t1658 = parse_formula(parser)
        item899 = _t1658
        push!(xs897, item899)
        cond898 = match_lookahead_literal(parser, "(", 0)
    end
    formulas900 = xs897
    consume_literal!(parser, ")")
    _t1659 = Proto.Disjunction(args=formulas900)
    result902 = _t1659
    record_span!(parser, span_start901, "Disjunction")
    return result902
end

function parse_not(parser::ParserState)::Proto.Not
    span_start904 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1660 = parse_formula(parser)
    formula903 = _t1660
    consume_literal!(parser, ")")
    _t1661 = Proto.Not(arg=formula903)
    result905 = _t1661
    record_span!(parser, span_start904, "Not")
    return result905
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start909 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1662 = parse_name(parser)
    name906 = _t1662
    _t1663 = parse_ffi_args(parser)
    ffi_args907 = _t1663
    _t1664 = parse_terms(parser)
    terms908 = _t1664
    consume_literal!(parser, ")")
    _t1665 = Proto.FFI(name=name906, args=ffi_args907, terms=terms908)
    result910 = _t1665
    record_span!(parser, span_start909, "FFI")
    return result910
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol911 = consume_terminal!(parser, "SYMBOL")
    return symbol911
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs912 = Proto.Abstraction[]
    cond913 = match_lookahead_literal(parser, "(", 0)
    while cond913
        _t1666 = parse_abstraction(parser)
        item914 = _t1666
        push!(xs912, item914)
        cond913 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions915 = xs912
    consume_literal!(parser, ")")
    return abstractions915
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start921 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1667 = parse_relation_id(parser)
    relation_id916 = _t1667
    xs917 = Proto.Term[]
    cond918 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond918
        _t1668 = parse_term(parser)
        item919 = _t1668
        push!(xs917, item919)
        cond918 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms920 = xs917
    consume_literal!(parser, ")")
    _t1669 = Proto.Atom(name=relation_id916, terms=terms920)
    result922 = _t1669
    record_span!(parser, span_start921, "Atom")
    return result922
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start928 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1670 = parse_name(parser)
    name923 = _t1670
    xs924 = Proto.Term[]
    cond925 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond925
        _t1671 = parse_term(parser)
        item926 = _t1671
        push!(xs924, item926)
        cond925 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms927 = xs924
    consume_literal!(parser, ")")
    _t1672 = Proto.Pragma(name=name923, terms=terms927)
    result929 = _t1672
    record_span!(parser, span_start928, "Pragma")
    return result929
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start945 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1674 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1675 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1676 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1677 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1678 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1679 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1680 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1681 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1682 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1683 = 7
                                            else
                                                _t1683 = -1
                                            end
                                            _t1682 = _t1683
                                        end
                                        _t1681 = _t1682
                                    end
                                    _t1680 = _t1681
                                end
                                _t1679 = _t1680
                            end
                            _t1678 = _t1679
                        end
                        _t1677 = _t1678
                    end
                    _t1676 = _t1677
                end
                _t1675 = _t1676
            end
            _t1674 = _t1675
        end
        _t1673 = _t1674
    else
        _t1673 = -1
    end
    prediction930 = _t1673
    if prediction930 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1685 = parse_name(parser)
        name940 = _t1685
        xs941 = Proto.RelTerm[]
        cond942 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond942
            _t1686 = parse_rel_term(parser)
            item943 = _t1686
            push!(xs941, item943)
            cond942 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms944 = xs941
        consume_literal!(parser, ")")
        _t1687 = Proto.Primitive(name=name940, terms=rel_terms944)
        _t1684 = _t1687
    else
        if prediction930 == 8
            _t1689 = parse_divide(parser)
            divide939 = _t1689
            _t1688 = divide939
        else
            if prediction930 == 7
                _t1691 = parse_multiply(parser)
                multiply938 = _t1691
                _t1690 = multiply938
            else
                if prediction930 == 6
                    _t1693 = parse_minus(parser)
                    minus937 = _t1693
                    _t1692 = minus937
                else
                    if prediction930 == 5
                        _t1695 = parse_add(parser)
                        add936 = _t1695
                        _t1694 = add936
                    else
                        if prediction930 == 4
                            _t1697 = parse_gt_eq(parser)
                            gt_eq935 = _t1697
                            _t1696 = gt_eq935
                        else
                            if prediction930 == 3
                                _t1699 = parse_gt(parser)
                                gt934 = _t1699
                                _t1698 = gt934
                            else
                                if prediction930 == 2
                                    _t1701 = parse_lt_eq(parser)
                                    lt_eq933 = _t1701
                                    _t1700 = lt_eq933
                                else
                                    if prediction930 == 1
                                        _t1703 = parse_lt(parser)
                                        lt932 = _t1703
                                        _t1702 = lt932
                                    else
                                        if prediction930 == 0
                                            _t1705 = parse_eq(parser)
                                            eq931 = _t1705
                                            _t1704 = eq931
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1702 = _t1704
                                    end
                                    _t1700 = _t1702
                                end
                                _t1698 = _t1700
                            end
                            _t1696 = _t1698
                        end
                        _t1694 = _t1696
                    end
                    _t1692 = _t1694
                end
                _t1690 = _t1692
            end
            _t1688 = _t1690
        end
        _t1684 = _t1688
    end
    result946 = _t1684
    record_span!(parser, span_start945, "Primitive")
    return result946
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start949 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1706 = parse_term(parser)
    term947 = _t1706
    _t1707 = parse_term(parser)
    term_3948 = _t1707
    consume_literal!(parser, ")")
    _t1708 = Proto.RelTerm(rel_term_type=OneOf(:term, term947))
    _t1709 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3948))
    _t1710 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1708, _t1709])
    result950 = _t1710
    record_span!(parser, span_start949, "Primitive")
    return result950
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start953 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1711 = parse_term(parser)
    term951 = _t1711
    _t1712 = parse_term(parser)
    term_3952 = _t1712
    consume_literal!(parser, ")")
    _t1713 = Proto.RelTerm(rel_term_type=OneOf(:term, term951))
    _t1714 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3952))
    _t1715 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1713, _t1714])
    result954 = _t1715
    record_span!(parser, span_start953, "Primitive")
    return result954
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start957 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1716 = parse_term(parser)
    term955 = _t1716
    _t1717 = parse_term(parser)
    term_3956 = _t1717
    consume_literal!(parser, ")")
    _t1718 = Proto.RelTerm(rel_term_type=OneOf(:term, term955))
    _t1719 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3956))
    _t1720 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1718, _t1719])
    result958 = _t1720
    record_span!(parser, span_start957, "Primitive")
    return result958
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start961 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1721 = parse_term(parser)
    term959 = _t1721
    _t1722 = parse_term(parser)
    term_3960 = _t1722
    consume_literal!(parser, ")")
    _t1723 = Proto.RelTerm(rel_term_type=OneOf(:term, term959))
    _t1724 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3960))
    _t1725 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1723, _t1724])
    result962 = _t1725
    record_span!(parser, span_start961, "Primitive")
    return result962
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start965 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1726 = parse_term(parser)
    term963 = _t1726
    _t1727 = parse_term(parser)
    term_3964 = _t1727
    consume_literal!(parser, ")")
    _t1728 = Proto.RelTerm(rel_term_type=OneOf(:term, term963))
    _t1729 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3964))
    _t1730 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1728, _t1729])
    result966 = _t1730
    record_span!(parser, span_start965, "Primitive")
    return result966
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start970 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1731 = parse_term(parser)
    term967 = _t1731
    _t1732 = parse_term(parser)
    term_3968 = _t1732
    _t1733 = parse_term(parser)
    term_4969 = _t1733
    consume_literal!(parser, ")")
    _t1734 = Proto.RelTerm(rel_term_type=OneOf(:term, term967))
    _t1735 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3968))
    _t1736 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4969))
    _t1737 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1734, _t1735, _t1736])
    result971 = _t1737
    record_span!(parser, span_start970, "Primitive")
    return result971
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start975 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1738 = parse_term(parser)
    term972 = _t1738
    _t1739 = parse_term(parser)
    term_3973 = _t1739
    _t1740 = parse_term(parser)
    term_4974 = _t1740
    consume_literal!(parser, ")")
    _t1741 = Proto.RelTerm(rel_term_type=OneOf(:term, term972))
    _t1742 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3973))
    _t1743 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4974))
    _t1744 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1741, _t1742, _t1743])
    result976 = _t1744
    record_span!(parser, span_start975, "Primitive")
    return result976
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1745 = parse_term(parser)
    term977 = _t1745
    _t1746 = parse_term(parser)
    term_3978 = _t1746
    _t1747 = parse_term(parser)
    term_4979 = _t1747
    consume_literal!(parser, ")")
    _t1748 = Proto.RelTerm(rel_term_type=OneOf(:term, term977))
    _t1749 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3978))
    _t1750 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4979))
    _t1751 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1748, _t1749, _t1750])
    result981 = _t1751
    record_span!(parser, span_start980, "Primitive")
    return result981
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start985 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1752 = parse_term(parser)
    term982 = _t1752
    _t1753 = parse_term(parser)
    term_3983 = _t1753
    _t1754 = parse_term(parser)
    term_4984 = _t1754
    consume_literal!(parser, ")")
    _t1755 = Proto.RelTerm(rel_term_type=OneOf(:term, term982))
    _t1756 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3983))
    _t1757 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4984))
    _t1758 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1755, _t1756, _t1757])
    result986 = _t1758
    record_span!(parser, span_start985, "Primitive")
    return result986
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start990 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1759 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1760 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1761 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1762 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1763 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1764 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1765 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1766 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1767 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1768 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1769 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1770 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1771 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1772 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1773 = 1
                                                            else
                                                                _t1773 = -1
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
                                    _t1766 = _t1767
                                end
                                _t1765 = _t1766
                            end
                            _t1764 = _t1765
                        end
                        _t1763 = _t1764
                    end
                    _t1762 = _t1763
                end
                _t1761 = _t1762
            end
            _t1760 = _t1761
        end
        _t1759 = _t1760
    end
    prediction987 = _t1759
    if prediction987 == 1
        _t1775 = parse_term(parser)
        term989 = _t1775
        _t1776 = Proto.RelTerm(rel_term_type=OneOf(:term, term989))
        _t1774 = _t1776
    else
        if prediction987 == 0
            _t1778 = parse_specialized_value(parser)
            specialized_value988 = _t1778
            _t1779 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value988))
            _t1777 = _t1779
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1774 = _t1777
    end
    result991 = _t1774
    record_span!(parser, span_start990, "RelTerm")
    return result991
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start993 = span_start(parser)
    consume_literal!(parser, "#")
    _t1780 = parse_raw_value(parser)
    raw_value992 = _t1780
    result994 = raw_value992
    record_span!(parser, span_start993, "Value")
    return result994
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start1000 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1781 = parse_name(parser)
    name995 = _t1781
    xs996 = Proto.RelTerm[]
    cond997 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond997
        _t1782 = parse_rel_term(parser)
        item998 = _t1782
        push!(xs996, item998)
        cond997 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms999 = xs996
    consume_literal!(parser, ")")
    _t1783 = Proto.RelAtom(name=name995, terms=rel_terms999)
    result1001 = _t1783
    record_span!(parser, span_start1000, "RelAtom")
    return result1001
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start1004 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1784 = parse_term(parser)
    term1002 = _t1784
    _t1785 = parse_term(parser)
    term_31003 = _t1785
    consume_literal!(parser, ")")
    _t1786 = Proto.Cast(input=term1002, result=term_31003)
    result1005 = _t1786
    record_span!(parser, span_start1004, "Cast")
    return result1005
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1006 = Proto.Attribute[]
    cond1007 = match_lookahead_literal(parser, "(", 0)
    while cond1007
        _t1787 = parse_attribute(parser)
        item1008 = _t1787
        push!(xs1006, item1008)
        cond1007 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1009 = xs1006
    consume_literal!(parser, ")")
    return attributes1009
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1015 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1788 = parse_name(parser)
    name1010 = _t1788
    xs1011 = Proto.Value[]
    cond1012 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1012
        _t1789 = parse_raw_value(parser)
        item1013 = _t1789
        push!(xs1011, item1013)
        cond1012 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1014 = xs1011
    consume_literal!(parser, ")")
    _t1790 = Proto.Attribute(name=name1010, args=raw_values1014)
    result1016 = _t1790
    record_span!(parser, span_start1015, "Attribute")
    return result1016
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1022 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1017 = Proto.RelationId[]
    cond1018 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1018
        _t1791 = parse_relation_id(parser)
        item1019 = _t1791
        push!(xs1017, item1019)
        cond1018 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1020 = xs1017
    _t1792 = parse_script(parser)
    script1021 = _t1792
    consume_literal!(parser, ")")
    _t1793 = Proto.Algorithm(var"#global"=relation_ids1020, body=script1021)
    result1023 = _t1793
    record_span!(parser, span_start1022, "Algorithm")
    return result1023
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1028 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1024 = Proto.Construct[]
    cond1025 = match_lookahead_literal(parser, "(", 0)
    while cond1025
        _t1794 = parse_construct(parser)
        item1026 = _t1794
        push!(xs1024, item1026)
        cond1025 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1027 = xs1024
    consume_literal!(parser, ")")
    _t1795 = Proto.Script(constructs=constructs1027)
    result1029 = _t1795
    record_span!(parser, span_start1028, "Script")
    return result1029
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1033 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1797 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1798 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1799 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1800 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1801 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1802 = 1
                            else
                                _t1802 = -1
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
    else
        _t1796 = -1
    end
    prediction1030 = _t1796
    if prediction1030 == 1
        _t1804 = parse_instruction(parser)
        instruction1032 = _t1804
        _t1805 = Proto.Construct(construct_type=OneOf(:instruction, instruction1032))
        _t1803 = _t1805
    else
        if prediction1030 == 0
            _t1807 = parse_loop(parser)
            loop1031 = _t1807
            _t1808 = Proto.Construct(construct_type=OneOf(:loop, loop1031))
            _t1806 = _t1808
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1803 = _t1806
    end
    result1034 = _t1803
    record_span!(parser, span_start1033, "Construct")
    return result1034
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1037 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1809 = parse_init(parser)
    init1035 = _t1809
    _t1810 = parse_script(parser)
    script1036 = _t1810
    consume_literal!(parser, ")")
    _t1811 = Proto.Loop(init=init1035, body=script1036)
    result1038 = _t1811
    record_span!(parser, span_start1037, "Loop")
    return result1038
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1039 = Proto.Instruction[]
    cond1040 = match_lookahead_literal(parser, "(", 0)
    while cond1040
        _t1812 = parse_instruction(parser)
        item1041 = _t1812
        push!(xs1039, item1041)
        cond1040 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1042 = xs1039
    consume_literal!(parser, ")")
    return instructions1042
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1049 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1814 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1815 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1816 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1817 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1818 = 0
                        else
                            _t1818 = -1
                        end
                        _t1817 = _t1818
                    end
                    _t1816 = _t1817
                end
                _t1815 = _t1816
            end
            _t1814 = _t1815
        end
        _t1813 = _t1814
    else
        _t1813 = -1
    end
    prediction1043 = _t1813
    if prediction1043 == 4
        _t1820 = parse_monus_def(parser)
        monus_def1048 = _t1820
        _t1821 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1048))
        _t1819 = _t1821
    else
        if prediction1043 == 3
            _t1823 = parse_monoid_def(parser)
            monoid_def1047 = _t1823
            _t1824 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1047))
            _t1822 = _t1824
        else
            if prediction1043 == 2
                _t1826 = parse_break(parser)
                break1046 = _t1826
                _t1827 = Proto.Instruction(instr_type=OneOf(:var"#break", break1046))
                _t1825 = _t1827
            else
                if prediction1043 == 1
                    _t1829 = parse_upsert(parser)
                    upsert1045 = _t1829
                    _t1830 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1045))
                    _t1828 = _t1830
                else
                    if prediction1043 == 0
                        _t1832 = parse_assign(parser)
                        assign1044 = _t1832
                        _t1833 = Proto.Instruction(instr_type=OneOf(:assign, assign1044))
                        _t1831 = _t1833
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1828 = _t1831
                end
                _t1825 = _t1828
            end
            _t1822 = _t1825
        end
        _t1819 = _t1822
    end
    result1050 = _t1819
    record_span!(parser, span_start1049, "Instruction")
    return result1050
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1054 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1834 = parse_relation_id(parser)
    relation_id1051 = _t1834
    _t1835 = parse_abstraction(parser)
    abstraction1052 = _t1835
    if match_lookahead_literal(parser, "(", 0)
        _t1837 = parse_attrs(parser)
        _t1836 = _t1837
    else
        _t1836 = nothing
    end
    attrs1053 = _t1836
    consume_literal!(parser, ")")
    _t1838 = Proto.Assign(name=relation_id1051, body=abstraction1052, attrs=(!isnothing(attrs1053) ? attrs1053 : Proto.Attribute[]))
    result1055 = _t1838
    record_span!(parser, span_start1054, "Assign")
    return result1055
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1059 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1839 = parse_relation_id(parser)
    relation_id1056 = _t1839
    _t1840 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1057 = _t1840
    if match_lookahead_literal(parser, "(", 0)
        _t1842 = parse_attrs(parser)
        _t1841 = _t1842
    else
        _t1841 = nothing
    end
    attrs1058 = _t1841
    consume_literal!(parser, ")")
    _t1843 = Proto.Upsert(name=relation_id1056, body=abstraction_with_arity1057[1], attrs=(!isnothing(attrs1058) ? attrs1058 : Proto.Attribute[]), value_arity=abstraction_with_arity1057[2])
    result1060 = _t1843
    record_span!(parser, span_start1059, "Upsert")
    return result1060
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1844 = parse_bindings(parser)
    bindings1061 = _t1844
    _t1845 = parse_formula(parser)
    formula1062 = _t1845
    consume_literal!(parser, ")")
    _t1846 = Proto.Abstraction(vars=vcat(bindings1061[1], !isnothing(bindings1061[2]) ? bindings1061[2] : []), value=formula1062)
    return (_t1846, length(bindings1061[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1066 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1847 = parse_relation_id(parser)
    relation_id1063 = _t1847
    _t1848 = parse_abstraction(parser)
    abstraction1064 = _t1848
    if match_lookahead_literal(parser, "(", 0)
        _t1850 = parse_attrs(parser)
        _t1849 = _t1850
    else
        _t1849 = nothing
    end
    attrs1065 = _t1849
    consume_literal!(parser, ")")
    _t1851 = Proto.Break(name=relation_id1063, body=abstraction1064, attrs=(!isnothing(attrs1065) ? attrs1065 : Proto.Attribute[]))
    result1067 = _t1851
    record_span!(parser, span_start1066, "Break")
    return result1067
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1072 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1852 = parse_monoid(parser)
    monoid1068 = _t1852
    _t1853 = parse_relation_id(parser)
    relation_id1069 = _t1853
    _t1854 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1070 = _t1854
    if match_lookahead_literal(parser, "(", 0)
        _t1856 = parse_attrs(parser)
        _t1855 = _t1856
    else
        _t1855 = nothing
    end
    attrs1071 = _t1855
    consume_literal!(parser, ")")
    _t1857 = Proto.MonoidDef(monoid=monoid1068, name=relation_id1069, body=abstraction_with_arity1070[1], attrs=(!isnothing(attrs1071) ? attrs1071 : Proto.Attribute[]), value_arity=abstraction_with_arity1070[2])
    result1073 = _t1857
    record_span!(parser, span_start1072, "MonoidDef")
    return result1073
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1079 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1859 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1860 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1861 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1862 = 2
                    else
                        _t1862 = -1
                    end
                    _t1861 = _t1862
                end
                _t1860 = _t1861
            end
            _t1859 = _t1860
        end
        _t1858 = _t1859
    else
        _t1858 = -1
    end
    prediction1074 = _t1858
    if prediction1074 == 3
        _t1864 = parse_sum_monoid(parser)
        sum_monoid1078 = _t1864
        _t1865 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1078))
        _t1863 = _t1865
    else
        if prediction1074 == 2
            _t1867 = parse_max_monoid(parser)
            max_monoid1077 = _t1867
            _t1868 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1077))
            _t1866 = _t1868
        else
            if prediction1074 == 1
                _t1870 = parse_min_monoid(parser)
                min_monoid1076 = _t1870
                _t1871 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1076))
                _t1869 = _t1871
            else
                if prediction1074 == 0
                    _t1873 = parse_or_monoid(parser)
                    or_monoid1075 = _t1873
                    _t1874 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1075))
                    _t1872 = _t1874
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1869 = _t1872
            end
            _t1866 = _t1869
        end
        _t1863 = _t1866
    end
    result1080 = _t1863
    record_span!(parser, span_start1079, "Monoid")
    return result1080
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1081 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1875 = Proto.OrMonoid()
    result1082 = _t1875
    record_span!(parser, span_start1081, "OrMonoid")
    return result1082
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1084 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1876 = parse_type(parser)
    type1083 = _t1876
    consume_literal!(parser, ")")
    _t1877 = Proto.MinMonoid(var"#type"=type1083)
    result1085 = _t1877
    record_span!(parser, span_start1084, "MinMonoid")
    return result1085
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1087 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1878 = parse_type(parser)
    type1086 = _t1878
    consume_literal!(parser, ")")
    _t1879 = Proto.MaxMonoid(var"#type"=type1086)
    result1088 = _t1879
    record_span!(parser, span_start1087, "MaxMonoid")
    return result1088
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1090 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1880 = parse_type(parser)
    type1089 = _t1880
    consume_literal!(parser, ")")
    _t1881 = Proto.SumMonoid(var"#type"=type1089)
    result1091 = _t1881
    record_span!(parser, span_start1090, "SumMonoid")
    return result1091
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1096 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1882 = parse_monoid(parser)
    monoid1092 = _t1882
    _t1883 = parse_relation_id(parser)
    relation_id1093 = _t1883
    _t1884 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1094 = _t1884
    if match_lookahead_literal(parser, "(", 0)
        _t1886 = parse_attrs(parser)
        _t1885 = _t1886
    else
        _t1885 = nothing
    end
    attrs1095 = _t1885
    consume_literal!(parser, ")")
    _t1887 = Proto.MonusDef(monoid=monoid1092, name=relation_id1093, body=abstraction_with_arity1094[1], attrs=(!isnothing(attrs1095) ? attrs1095 : Proto.Attribute[]), value_arity=abstraction_with_arity1094[2])
    result1097 = _t1887
    record_span!(parser, span_start1096, "MonusDef")
    return result1097
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1102 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1888 = parse_relation_id(parser)
    relation_id1098 = _t1888
    _t1889 = parse_abstraction(parser)
    abstraction1099 = _t1889
    _t1890 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1100 = _t1890
    _t1891 = parse_functional_dependency_values(parser)
    functional_dependency_values1101 = _t1891
    consume_literal!(parser, ")")
    _t1892 = Proto.FunctionalDependency(guard=abstraction1099, keys=functional_dependency_keys1100, values=functional_dependency_values1101)
    _t1893 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1892), name=relation_id1098)
    result1103 = _t1893
    record_span!(parser, span_start1102, "Constraint")
    return result1103
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1104 = Proto.Var[]
    cond1105 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1105
        _t1894 = parse_var(parser)
        item1106 = _t1894
        push!(xs1104, item1106)
        cond1105 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1107 = xs1104
    consume_literal!(parser, ")")
    return vars1107
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1108 = Proto.Var[]
    cond1109 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1109
        _t1895 = parse_var(parser)
        item1110 = _t1895
        push!(xs1108, item1110)
        cond1109 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1111 = xs1108
    consume_literal!(parser, ")")
    return vars1111
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1117 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1897 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1898 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1899 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
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
    else
        _t1896 = -1
    end
    prediction1112 = _t1896
    if prediction1112 == 3
        _t1902 = parse_iceberg_data(parser)
        iceberg_data1116 = _t1902
        _t1903 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1116))
        _t1901 = _t1903
    else
        if prediction1112 == 2
            _t1905 = parse_csv_data(parser)
            csv_data1115 = _t1905
            _t1906 = Proto.Data(data_type=OneOf(:csv_data, csv_data1115))
            _t1904 = _t1906
        else
            if prediction1112 == 1
                _t1908 = parse_betree_relation(parser)
                betree_relation1114 = _t1908
                _t1909 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1114))
                _t1907 = _t1909
            else
                if prediction1112 == 0
                    _t1911 = parse_edb(parser)
                    edb1113 = _t1911
                    _t1912 = Proto.Data(data_type=OneOf(:edb, edb1113))
                    _t1910 = _t1912
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1907 = _t1910
            end
            _t1904 = _t1907
        end
        _t1901 = _t1904
    end
    result1118 = _t1901
    record_span!(parser, span_start1117, "Data")
    return result1118
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1122 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1913 = parse_relation_id(parser)
    relation_id1119 = _t1913
    _t1914 = parse_edb_path(parser)
    edb_path1120 = _t1914
    _t1915 = parse_edb_types(parser)
    edb_types1121 = _t1915
    consume_literal!(parser, ")")
    _t1916 = Proto.EDB(target_id=relation_id1119, path=edb_path1120, types=edb_types1121)
    result1123 = _t1916
    record_span!(parser, span_start1122, "EDB")
    return result1123
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1124 = String[]
    cond1125 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1125
        item1126 = consume_terminal!(parser, "STRING")
        push!(xs1124, item1126)
        cond1125 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1127 = xs1124
    consume_literal!(parser, "]")
    return strings1127
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1128 = Proto.var"#Type"[]
    cond1129 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1129
        _t1917 = parse_type(parser)
        item1130 = _t1917
        push!(xs1128, item1130)
        cond1129 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1131 = xs1128
    consume_literal!(parser, "]")
    return types1131
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1134 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1918 = parse_relation_id(parser)
    relation_id1132 = _t1918
    _t1919 = parse_betree_info(parser)
    betree_info1133 = _t1919
    consume_literal!(parser, ")")
    _t1920 = Proto.BeTreeRelation(name=relation_id1132, relation_info=betree_info1133)
    result1135 = _t1920
    record_span!(parser, span_start1134, "BeTreeRelation")
    return result1135
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1139 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1921 = parse_betree_info_key_types(parser)
    betree_info_key_types1136 = _t1921
    _t1922 = parse_betree_info_value_types(parser)
    betree_info_value_types1137 = _t1922
    _t1923 = parse_config_dict(parser)
    config_dict1138 = _t1923
    consume_literal!(parser, ")")
    _t1924 = construct_betree_info(parser, betree_info_key_types1136, betree_info_value_types1137, config_dict1138)
    result1140 = _t1924
    record_span!(parser, span_start1139, "BeTreeInfo")
    return result1140
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1141 = Proto.var"#Type"[]
    cond1142 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1142
        _t1925 = parse_type(parser)
        item1143 = _t1925
        push!(xs1141, item1143)
        cond1142 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1144 = xs1141
    consume_literal!(parser, ")")
    return types1144
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1145 = Proto.var"#Type"[]
    cond1146 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1146
        _t1926 = parse_type(parser)
        item1147 = _t1926
        push!(xs1145, item1147)
        cond1146 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1148 = xs1145
    consume_literal!(parser, ")")
    return types1148
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1153 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1927 = parse_csvlocator(parser)
    csvlocator1149 = _t1927
    _t1928 = parse_csv_config(parser)
    csv_config1150 = _t1928
    _t1929 = parse_gnf_columns(parser)
    gnf_columns1151 = _t1929
    _t1930 = parse_csv_asof(parser)
    csv_asof1152 = _t1930
    consume_literal!(parser, ")")
    _t1931 = Proto.CSVData(locator=csvlocator1149, config=csv_config1150, columns=gnf_columns1151, asof=csv_asof1152)
    result1154 = _t1931
    record_span!(parser, span_start1153, "CSVData")
    return result1154
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1157 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1933 = parse_csv_locator_paths(parser)
        _t1932 = _t1933
    else
        _t1932 = nothing
    end
    csv_locator_paths1155 = _t1932
    if match_lookahead_literal(parser, "(", 0)
        _t1935 = parse_csv_locator_inline_data(parser)
        _t1934 = _t1935
    else
        _t1934 = nothing
    end
    csv_locator_inline_data1156 = _t1934
    consume_literal!(parser, ")")
    _t1936 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1155) ? csv_locator_paths1155 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1156) ? csv_locator_inline_data1156 : "")))
    result1158 = _t1936
    record_span!(parser, span_start1157, "CSVLocator")
    return result1158
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1159 = String[]
    cond1160 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1160
        item1161 = consume_terminal!(parser, "STRING")
        push!(xs1159, item1161)
        cond1160 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1162 = xs1159
    consume_literal!(parser, ")")
    return strings1162
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1163 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1163
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1165 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1937 = parse_config_dict(parser)
    config_dict1164 = _t1937
    consume_literal!(parser, ")")
    _t1938 = construct_csv_config(parser, config_dict1164)
    result1166 = _t1938
    record_span!(parser, span_start1165, "CSVConfig")
    return result1166
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1167 = Proto.GNFColumn[]
    cond1168 = match_lookahead_literal(parser, "(", 0)
    while cond1168
        _t1939 = parse_gnf_column(parser)
        item1169 = _t1939
        push!(xs1167, item1169)
        cond1168 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1170 = xs1167
    consume_literal!(parser, ")")
    return gnf_columns1170
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1177 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1940 = parse_gnf_column_path(parser)
    gnf_column_path1171 = _t1940
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1942 = parse_relation_id(parser)
        _t1941 = _t1942
    else
        _t1941 = nothing
    end
    relation_id1172 = _t1941
    consume_literal!(parser, "[")
    xs1173 = Proto.var"#Type"[]
    cond1174 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1174
        _t1943 = parse_type(parser)
        item1175 = _t1943
        push!(xs1173, item1175)
        cond1174 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1176 = xs1173
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1944 = Proto.GNFColumn(column_path=gnf_column_path1171, target_id=relation_id1172, types=types1176)
    result1178 = _t1944
    record_span!(parser, span_start1177, "GNFColumn")
    return result1178
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1945 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1946 = 0
        else
            _t1946 = -1
        end
        _t1945 = _t1946
    end
    prediction1179 = _t1945
    if prediction1179 == 1
        consume_literal!(parser, "[")
        xs1181 = String[]
        cond1182 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1182
            item1183 = consume_terminal!(parser, "STRING")
            push!(xs1181, item1183)
            cond1182 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1184 = xs1181
        consume_literal!(parser, "]")
        _t1947 = strings1184
    else
        if prediction1179 == 0
            string1180 = consume_terminal!(parser, "STRING")
            _t1948 = String[string1180]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1947 = _t1948
    end
    return _t1947
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1185 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1185
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1190 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1949 = parse_iceberg_locator(parser)
    iceberg_locator1186 = _t1949
    _t1950 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1187 = _t1950
    _t1951 = parse_gnf_columns(parser)
    gnf_columns1188 = _t1951
    if match_lookahead_literal(parser, "(", 0)
        _t1953 = parse_iceberg_to_snapshot(parser)
        _t1952 = _t1953
    else
        _t1952 = nothing
    end
    iceberg_to_snapshot1189 = _t1952
    consume_literal!(parser, ")")
    _t1954 = Proto.IcebergData(locator=iceberg_locator1186, config=iceberg_catalog_config1187, columns=gnf_columns1188, to_snapshot=(!isnothing(iceberg_to_snapshot1189) ? iceberg_to_snapshot1189 : ""))
    result1191 = _t1954
    record_span!(parser, span_start1190, "IcebergData")
    return result1191
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1198 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1192 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1193 = String[]
    cond1194 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1194
        item1195 = consume_terminal!(parser, "STRING")
        push!(xs1193, item1195)
        cond1194 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1196 = xs1193
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string_121197 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1955 = Proto.IcebergLocator(table_name=string1192, namespace=strings1196, warehouse=string_121197)
    result1199 = _t1955
    record_span!(parser, span_start1198, "IcebergLocator")
    return result1199
end

function parse_iceberg_catalog_config(parser::ParserState)::Proto.IcebergCatalogConfig
    span_start1210 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_catalog_config")
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1200 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1957 = parse_iceberg_catalog_config_scope(parser)
        _t1956 = _t1957
    else
        _t1956 = nothing
    end
    iceberg_catalog_config_scope1201 = _t1956
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1202 = Tuple{String, String}[]
    cond1203 = match_lookahead_literal(parser, "(", 0)
    while cond1203
        _t1958 = parse_iceberg_property_entry(parser)
        item1204 = _t1958
        push!(xs1202, item1204)
        cond1203 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1205 = xs1202
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1206 = Tuple{String, String}[]
    cond1207 = match_lookahead_literal(parser, "(", 0)
    while cond1207
        _t1959 = parse_iceberg_property_entry(parser)
        item1208 = _t1959
        push!(xs1206, item1208)
        cond1207 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys_131209 = xs1206
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1960 = construct_iceberg_catalog_config(parser, string1200, iceberg_catalog_config_scope1201, iceberg_property_entrys1205, iceberg_property_entrys_131209)
    result1211 = _t1960
    record_span!(parser, span_start1210, "IcebergCatalogConfig")
    return result1211
end

function parse_iceberg_catalog_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1212 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1212
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1213 = consume_terminal!(parser, "STRING")
    string_31214 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1213, string_31214,)
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1215 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1215
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1217 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1961 = parse_fragment_id(parser)
    fragment_id1216 = _t1961
    consume_literal!(parser, ")")
    _t1962 = Proto.Undefine(fragment_id=fragment_id1216)
    result1218 = _t1962
    record_span!(parser, span_start1217, "Undefine")
    return result1218
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1223 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1219 = Proto.RelationId[]
    cond1220 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1220
        _t1963 = parse_relation_id(parser)
        item1221 = _t1963
        push!(xs1219, item1221)
        cond1220 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1222 = xs1219
    consume_literal!(parser, ")")
    _t1964 = Proto.Context(relations=relation_ids1222)
    result1224 = _t1964
    record_span!(parser, span_start1223, "Context")
    return result1224
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1229 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1225 = Proto.SnapshotMapping[]
    cond1226 = match_lookahead_literal(parser, "[", 0)
    while cond1226
        _t1965 = parse_snapshot_mapping(parser)
        item1227 = _t1965
        push!(xs1225, item1227)
        cond1226 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1228 = xs1225
    consume_literal!(parser, ")")
    _t1966 = Proto.Snapshot(mappings=snapshot_mappings1228)
    result1230 = _t1966
    record_span!(parser, span_start1229, "Snapshot")
    return result1230
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1233 = span_start(parser)
    _t1967 = parse_edb_path(parser)
    edb_path1231 = _t1967
    _t1968 = parse_relation_id(parser)
    relation_id1232 = _t1968
    _t1969 = Proto.SnapshotMapping(destination_path=edb_path1231, source_relation=relation_id1232)
    result1234 = _t1969
    record_span!(parser, span_start1233, "SnapshotMapping")
    return result1234
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1235 = Proto.Read[]
    cond1236 = match_lookahead_literal(parser, "(", 0)
    while cond1236
        _t1970 = parse_read(parser)
        item1237 = _t1970
        push!(xs1235, item1237)
        cond1236 = match_lookahead_literal(parser, "(", 0)
    end
    reads1238 = xs1235
    consume_literal!(parser, ")")
    return reads1238
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1245 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1972 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1973 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t1974 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t1975 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t1976 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t1977 = 3
                            else
                                _t1977 = -1
                            end
                            _t1976 = _t1977
                        end
                        _t1975 = _t1976
                    end
                    _t1974 = _t1975
                end
                _t1973 = _t1974
            end
            _t1972 = _t1973
        end
        _t1971 = _t1972
    else
        _t1971 = -1
    end
    prediction1239 = _t1971
    if prediction1239 == 4
        _t1979 = parse_export(parser)
        export1244 = _t1979
        _t1980 = Proto.Read(read_type=OneOf(:var"#export", export1244))
        _t1978 = _t1980
    else
        if prediction1239 == 3
            _t1982 = parse_abort(parser)
            abort1243 = _t1982
            _t1983 = Proto.Read(read_type=OneOf(:abort, abort1243))
            _t1981 = _t1983
        else
            if prediction1239 == 2
                _t1985 = parse_what_if(parser)
                what_if1242 = _t1985
                _t1986 = Proto.Read(read_type=OneOf(:what_if, what_if1242))
                _t1984 = _t1986
            else
                if prediction1239 == 1
                    _t1988 = parse_output(parser)
                    output1241 = _t1988
                    _t1989 = Proto.Read(read_type=OneOf(:output, output1241))
                    _t1987 = _t1989
                else
                    if prediction1239 == 0
                        _t1991 = parse_demand(parser)
                        demand1240 = _t1991
                        _t1992 = Proto.Read(read_type=OneOf(:demand, demand1240))
                        _t1990 = _t1992
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1987 = _t1990
                end
                _t1984 = _t1987
            end
            _t1981 = _t1984
        end
        _t1978 = _t1981
    end
    result1246 = _t1978
    record_span!(parser, span_start1245, "Read")
    return result1246
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1248 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1993 = parse_relation_id(parser)
    relation_id1247 = _t1993
    consume_literal!(parser, ")")
    _t1994 = Proto.Demand(relation_id=relation_id1247)
    result1249 = _t1994
    record_span!(parser, span_start1248, "Demand")
    return result1249
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1252 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1995 = parse_name(parser)
    name1250 = _t1995
    _t1996 = parse_relation_id(parser)
    relation_id1251 = _t1996
    consume_literal!(parser, ")")
    _t1997 = Proto.Output(name=name1250, relation_id=relation_id1251)
    result1253 = _t1997
    record_span!(parser, span_start1252, "Output")
    return result1253
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1256 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1998 = parse_name(parser)
    name1254 = _t1998
    _t1999 = parse_epoch(parser)
    epoch1255 = _t1999
    consume_literal!(parser, ")")
    _t2000 = Proto.WhatIf(branch=name1254, epoch=epoch1255)
    result1257 = _t2000
    record_span!(parser, span_start1256, "WhatIf")
    return result1257
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1260 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t2002 = parse_name(parser)
        _t2001 = _t2002
    else
        _t2001 = nothing
    end
    name1258 = _t2001
    _t2003 = parse_relation_id(parser)
    relation_id1259 = _t2003
    consume_literal!(parser, ")")
    _t2004 = Proto.Abort(name=(!isnothing(name1258) ? name1258 : "abort"), relation_id=relation_id1259)
    result1261 = _t2004
    record_span!(parser, span_start1260, "Abort")
    return result1261
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1265 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t2006 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t2007 = 0
            else
                _t2007 = -1
            end
            _t2006 = _t2007
        end
        _t2005 = _t2006
    else
        _t2005 = -1
    end
    prediction1262 = _t2005
    if prediction1262 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t2009 = parse_export_iceberg_config(parser)
        export_iceberg_config1264 = _t2009
        consume_literal!(parser, ")")
        _t2010 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1264))
        _t2008 = _t2010
    else
        if prediction1262 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2012 = parse_export_csv_config(parser)
            export_csv_config1263 = _t2012
            consume_literal!(parser, ")")
            _t2013 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1263))
            _t2011 = _t2013
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t2008 = _t2011
    end
    result1266 = _t2008
    record_span!(parser, span_start1265, "Export")
    return result1266
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1274 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2015 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2016 = 1
            else
                _t2016 = -1
            end
            _t2015 = _t2016
        end
        _t2014 = _t2015
    else
        _t2014 = -1
    end
    prediction1267 = _t2014
    if prediction1267 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2018 = parse_export_csv_path(parser)
        export_csv_path1271 = _t2018
        _t2019 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1272 = _t2019
        _t2020 = parse_config_dict(parser)
        config_dict1273 = _t2020
        consume_literal!(parser, ")")
        _t2021 = construct_export_csv_config(parser, export_csv_path1271, export_csv_columns_list1272, config_dict1273)
        _t2017 = _t2021
    else
        if prediction1267 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2023 = parse_export_csv_path(parser)
            export_csv_path1268 = _t2023
            _t2024 = parse_export_csv_source(parser)
            export_csv_source1269 = _t2024
            _t2025 = parse_csv_config(parser)
            csv_config1270 = _t2025
            consume_literal!(parser, ")")
            _t2026 = construct_export_csv_config_with_source(parser, export_csv_path1268, export_csv_source1269, csv_config1270)
            _t2022 = _t2026
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2017 = _t2022
    end
    result1275 = _t2017
    record_span!(parser, span_start1274, "ExportCSVConfig")
    return result1275
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1276 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1276
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1283 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2028 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2029 = 0
            else
                _t2029 = -1
            end
            _t2028 = _t2029
        end
        _t2027 = _t2028
    else
        _t2027 = -1
    end
    prediction1277 = _t2027
    if prediction1277 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2031 = parse_relation_id(parser)
        relation_id1282 = _t2031
        consume_literal!(parser, ")")
        _t2032 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1282))
        _t2030 = _t2032
    else
        if prediction1277 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1278 = Proto.ExportCSVColumn[]
            cond1279 = match_lookahead_literal(parser, "(", 0)
            while cond1279
                _t2034 = parse_export_csv_column(parser)
                item1280 = _t2034
                push!(xs1278, item1280)
                cond1279 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1281 = xs1278
            consume_literal!(parser, ")")
            _t2035 = Proto.ExportCSVColumns(columns=export_csv_columns1281)
            _t2036 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2035))
            _t2033 = _t2036
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2030 = _t2033
    end
    result1284 = _t2030
    record_span!(parser, span_start1283, "ExportCSVSource")
    return result1284
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1287 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1285 = consume_terminal!(parser, "STRING")
    _t2037 = parse_relation_id(parser)
    relation_id1286 = _t2037
    consume_literal!(parser, ")")
    _t2038 = Proto.ExportCSVColumn(column_name=string1285, column_data=relation_id1286)
    result1288 = _t2038
    record_span!(parser, span_start1287, "ExportCSVColumn")
    return result1288
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1289 = Proto.ExportCSVColumn[]
    cond1290 = match_lookahead_literal(parser, "(", 0)
    while cond1290
        _t2039 = parse_export_csv_column(parser)
        item1291 = _t2039
        push!(xs1289, item1291)
        cond1290 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1292 = xs1289
    consume_literal!(parser, ")")
    return export_csv_columns1292
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1304 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2040 = parse_iceberg_locator(parser)
    iceberg_locator1293 = _t2040
    _t2041 = parse_iceberg_catalog_config(parser)
    iceberg_catalog_config1294 = _t2041
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1295 = Proto.ExportIcebergColumn[]
    cond1296 = match_lookahead_literal(parser, "(", 0)
    while cond1296
        _t2042 = parse_iceberg_export_column(parser)
        item1297 = _t2042
        push!(xs1295, item1297)
        cond1296 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_export_columns1298 = xs1295
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "create_table_properties")
    xs1299 = Tuple{String, String}[]
    cond1300 = match_lookahead_literal(parser, "(", 0)
    while cond1300
        _t2043 = parse_iceberg_property_entry(parser)
        item1301 = _t2043
        push!(xs1299, item1301)
        cond1300 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1302 = xs1299
    consume_literal!(parser, ")")
    if match_lookahead_literal(parser, "{", 0)
        _t2045 = parse_config_dict(parser)
        _t2044 = _t2045
    else
        _t2044 = nothing
    end
    config_dict1303 = _t2044
    consume_literal!(parser, ")")
    _t2046 = construct_export_iceberg_config_full(parser, iceberg_locator1293, iceberg_catalog_config1294, iceberg_export_columns1298, iceberg_property_entrys1302, config_dict1303)
    result1305 = _t2046
    record_span!(parser, span_start1304, "ExportIcebergConfig")
    return result1305
end

function parse_iceberg_export_column(parser::ParserState)::Proto.ExportIcebergColumn
    span_start1310 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_column")
    string1306 = consume_terminal!(parser, "STRING")
    _t2047 = parse_relation_id(parser)
    relation_id1307 = _t2047
    _t2048 = parse_type(parser)
    type1308 = _t2048
    _t2049 = parse_boolean_value(parser)
    boolean_value1309 = _t2049
    consume_literal!(parser, ")")
    _t2050 = Proto.ExportIcebergColumn(name=string1306, column_data=relation_id1307, var"#type"=type1308, nullable=boolean_value1309)
    result1311 = _t2050
    record_span!(parser, span_start1310, "ExportIcebergColumn")
    return result1311
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
