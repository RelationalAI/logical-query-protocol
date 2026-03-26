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
        _t2039 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2040 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t2041 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t2042 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t2043 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t2044 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t2045 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t2046 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t2047 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t2048 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t2048
    _t2049 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t2049
    _t2050 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t2050
    _t2051 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t2051
    _t2052 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t2052
    _t2053 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t2053
    _t2054 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t2054
    _t2055 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t2055
    _t2056 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t2056
    _t2057 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t2057
    _t2058 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t2058
    _t2059 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t2059
    _t2060 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t2060
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t2061 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t2061
    _t2062 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t2062
    _t2063 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t2063
    _t2064 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t2064
    _t2065 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t2065
    _t2066 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t2066
    _t2067 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t2067
    _t2068 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t2068
    _t2069 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t2069
    _t2070 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t2070
    _t2071 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t2071
end

function default_configure(parser::ParserState)::Proto.Configure
    _t2072 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t2072
    _t2073 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t2073
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
    _t2074 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t2074
    _t2075 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t2075
    _t2076 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t2076
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t2077 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t2077
    _t2078 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t2078
    _t2079 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2079
    _t2080 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2080
    _t2081 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2081
    _t2082 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2082
    _t2083 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2083
    _t2084 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2084
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2085 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2085
end

function construct_iceberg_config(parser::ParserState, catalog_uri::String, scope_opt::Union{Nothing, String}, property_pairs::Vector{Tuple{String, String}}, auth_property_pairs::Vector{Tuple{String, String}})::Proto.IcebergConfig
    props = Dict(property_pairs)
    auth_props = Dict(auth_property_pairs)
    scope_pb = (!isnothing(scope_opt) ? scope_opt : "")
    _t2086 = Proto.IcebergConfig(catalog_uri=catalog_uri, scope=scope_pb, properties=props, auth_properties=auth_props)
    return _t2086
end

function construct_export_iceberg_config_full(parser::ParserState, locator::Proto.IcebergLocator, config::Proto.IcebergConfig, columns::Vector{Proto.IcebergExportColumn}, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    prefix = ""
    target_file_size_bytes = 0
    compression = ""
    if !isnothing(config_dict)
        cfg = Dict(config_dict)
        _t2087 = _extract_value_string(parser, get(cfg, "prefix", nothing), "")
        prefix = _t2087
        _t2088 = _extract_value_int64(parser, get(cfg, "target_file_size_bytes", nothing), 0)
        target_file_size_bytes = _t2088
        _t2089 = _extract_value_string(parser, get(cfg, "compression", nothing), "")
        compression = _t2089
    end
    _t2090 = Proto.ExportIcebergConfig(locator=locator, config=config, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression)
    return _t2090
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start657 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1303 = parse_configure(parser)
        _t1302 = _t1303
    else
        _t1302 = nothing
    end
    configure651 = _t1302
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1305 = parse_sync(parser)
        _t1304 = _t1305
    else
        _t1304 = nothing
    end
    sync652 = _t1304
    xs653 = Proto.Epoch[]
    cond654 = match_lookahead_literal(parser, "(", 0)
    while cond654
        _t1306 = parse_epoch(parser)
        item655 = _t1306
        push!(xs653, item655)
        cond654 = match_lookahead_literal(parser, "(", 0)
    end
    epochs656 = xs653
    consume_literal!(parser, ")")
    _t1307 = default_configure(parser)
    _t1308 = Proto.Transaction(epochs=epochs656, configure=(!isnothing(configure651) ? configure651 : _t1307), sync=sync652)
    result658 = _t1308
    record_span!(parser, span_start657, "Transaction")
    return result658
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start660 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1309 = parse_config_dict(parser)
    config_dict659 = _t1309
    consume_literal!(parser, ")")
    _t1310 = construct_configure(parser, config_dict659)
    result661 = _t1310
    record_span!(parser, span_start660, "Configure")
    return result661
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs662 = Tuple{String, Proto.Value}[]
    cond663 = match_lookahead_literal(parser, ":", 0)
    while cond663
        _t1311 = parse_config_key_value(parser)
        item664 = _t1311
        push!(xs662, item664)
        cond663 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values665 = xs662
    consume_literal!(parser, "}")
    return config_key_values665
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol666 = consume_terminal!(parser, "SYMBOL")
    _t1312 = parse_raw_value(parser)
    raw_value667 = _t1312
    return (symbol666, raw_value667,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start681 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1313 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1314 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1315 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1317 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1318 = 0
                        else
                            _t1318 = -1
                        end
                        _t1317 = _t1318
                    end
                    _t1316 = _t1317
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1319 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1320 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1321 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1322 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1323 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1324 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1325 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1326 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1327 = 10
                                                    else
                                                        _t1327 = -1
                                                    end
                                                    _t1326 = _t1327
                                                end
                                                _t1325 = _t1326
                                            end
                                            _t1324 = _t1325
                                        end
                                        _t1323 = _t1324
                                    end
                                    _t1322 = _t1323
                                end
                                _t1321 = _t1322
                            end
                            _t1320 = _t1321
                        end
                        _t1319 = _t1320
                    end
                    _t1316 = _t1319
                end
                _t1315 = _t1316
            end
            _t1314 = _t1315
        end
        _t1313 = _t1314
    end
    prediction668 = _t1313
    if prediction668 == 12
        _t1329 = parse_boolean_value(parser)
        boolean_value680 = _t1329
        _t1330 = Proto.Value(value=OneOf(:boolean_value, boolean_value680))
        _t1328 = _t1330
    else
        if prediction668 == 11
            consume_literal!(parser, "missing")
            _t1332 = Proto.MissingValue()
            _t1333 = Proto.Value(value=OneOf(:missing_value, _t1332))
            _t1331 = _t1333
        else
            if prediction668 == 10
                decimal679 = consume_terminal!(parser, "DECIMAL")
                _t1335 = Proto.Value(value=OneOf(:decimal_value, decimal679))
                _t1334 = _t1335
            else
                if prediction668 == 9
                    int128678 = consume_terminal!(parser, "INT128")
                    _t1337 = Proto.Value(value=OneOf(:int128_value, int128678))
                    _t1336 = _t1337
                else
                    if prediction668 == 8
                        uint128677 = consume_terminal!(parser, "UINT128")
                        _t1339 = Proto.Value(value=OneOf(:uint128_value, uint128677))
                        _t1338 = _t1339
                    else
                        if prediction668 == 7
                            uint32676 = consume_terminal!(parser, "UINT32")
                            _t1341 = Proto.Value(value=OneOf(:uint32_value, uint32676))
                            _t1340 = _t1341
                        else
                            if prediction668 == 6
                                float675 = consume_terminal!(parser, "FLOAT")
                                _t1343 = Proto.Value(value=OneOf(:float_value, float675))
                                _t1342 = _t1343
                            else
                                if prediction668 == 5
                                    float32674 = consume_terminal!(parser, "FLOAT32")
                                    _t1345 = Proto.Value(value=OneOf(:float32_value, float32674))
                                    _t1344 = _t1345
                                else
                                    if prediction668 == 4
                                        int673 = consume_terminal!(parser, "INT")
                                        _t1347 = Proto.Value(value=OneOf(:int_value, int673))
                                        _t1346 = _t1347
                                    else
                                        if prediction668 == 3
                                            int32672 = consume_terminal!(parser, "INT32")
                                            _t1349 = Proto.Value(value=OneOf(:int32_value, int32672))
                                            _t1348 = _t1349
                                        else
                                            if prediction668 == 2
                                                string671 = consume_terminal!(parser, "STRING")
                                                _t1351 = Proto.Value(value=OneOf(:string_value, string671))
                                                _t1350 = _t1351
                                            else
                                                if prediction668 == 1
                                                    _t1353 = parse_raw_datetime(parser)
                                                    raw_datetime670 = _t1353
                                                    _t1354 = Proto.Value(value=OneOf(:datetime_value, raw_datetime670))
                                                    _t1352 = _t1354
                                                else
                                                    if prediction668 == 0
                                                        _t1356 = parse_raw_date(parser)
                                                        raw_date669 = _t1356
                                                        _t1357 = Proto.Value(value=OneOf(:date_value, raw_date669))
                                                        _t1355 = _t1357
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1352 = _t1355
                                                end
                                                _t1350 = _t1352
                                            end
                                            _t1348 = _t1350
                                        end
                                        _t1346 = _t1348
                                    end
                                    _t1344 = _t1346
                                end
                                _t1342 = _t1344
                            end
                            _t1340 = _t1342
                        end
                        _t1338 = _t1340
                    end
                    _t1336 = _t1338
                end
                _t1334 = _t1336
            end
            _t1331 = _t1334
        end
        _t1328 = _t1331
    end
    result682 = _t1328
    record_span!(parser, span_start681, "Value")
    return result682
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start686 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int683 = consume_terminal!(parser, "INT")
    int_3684 = consume_terminal!(parser, "INT")
    int_4685 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1358 = Proto.DateValue(year=Int32(int683), month=Int32(int_3684), day=Int32(int_4685))
    result687 = _t1358
    record_span!(parser, span_start686, "DateValue")
    return result687
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start695 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int688 = consume_terminal!(parser, "INT")
    int_3689 = consume_terminal!(parser, "INT")
    int_4690 = consume_terminal!(parser, "INT")
    int_5691 = consume_terminal!(parser, "INT")
    int_6692 = consume_terminal!(parser, "INT")
    int_7693 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1359 = consume_terminal!(parser, "INT")
    else
        _t1359 = nothing
    end
    int_8694 = _t1359
    consume_literal!(parser, ")")
    _t1360 = Proto.DateTimeValue(year=Int32(int688), month=Int32(int_3689), day=Int32(int_4690), hour=Int32(int_5691), minute=Int32(int_6692), second=Int32(int_7693), microsecond=Int32((!isnothing(int_8694) ? int_8694 : 0)))
    result696 = _t1360
    record_span!(parser, span_start695, "DateTimeValue")
    return result696
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1361 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1362 = 1
        else
            _t1362 = -1
        end
        _t1361 = _t1362
    end
    prediction697 = _t1361
    if prediction697 == 1
        consume_literal!(parser, "false")
        _t1363 = false
    else
        if prediction697 == 0
            consume_literal!(parser, "true")
            _t1364 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1363 = _t1364
    end
    return _t1363
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start702 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs698 = Proto.FragmentId[]
    cond699 = match_lookahead_literal(parser, ":", 0)
    while cond699
        _t1365 = parse_fragment_id(parser)
        item700 = _t1365
        push!(xs698, item700)
        cond699 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids701 = xs698
    consume_literal!(parser, ")")
    _t1366 = Proto.Sync(fragments=fragment_ids701)
    result703 = _t1366
    record_span!(parser, span_start702, "Sync")
    return result703
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start705 = span_start(parser)
    consume_literal!(parser, ":")
    symbol704 = consume_terminal!(parser, "SYMBOL")
    result706 = Proto.FragmentId(Vector{UInt8}(symbol704))
    record_span!(parser, span_start705, "FragmentId")
    return result706
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start709 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1368 = parse_epoch_writes(parser)
        _t1367 = _t1368
    else
        _t1367 = nothing
    end
    epoch_writes707 = _t1367
    if match_lookahead_literal(parser, "(", 0)
        _t1370 = parse_epoch_reads(parser)
        _t1369 = _t1370
    else
        _t1369 = nothing
    end
    epoch_reads708 = _t1369
    consume_literal!(parser, ")")
    _t1371 = Proto.Epoch(writes=(!isnothing(epoch_writes707) ? epoch_writes707 : Proto.Write[]), reads=(!isnothing(epoch_reads708) ? epoch_reads708 : Proto.Read[]))
    result710 = _t1371
    record_span!(parser, span_start709, "Epoch")
    return result710
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs711 = Proto.Write[]
    cond712 = match_lookahead_literal(parser, "(", 0)
    while cond712
        _t1372 = parse_write(parser)
        item713 = _t1372
        push!(xs711, item713)
        cond712 = match_lookahead_literal(parser, "(", 0)
    end
    writes714 = xs711
    consume_literal!(parser, ")")
    return writes714
end

function parse_write(parser::ParserState)::Proto.Write
    span_start720 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1374 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1375 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1376 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1377 = 2
                    else
                        _t1377 = -1
                    end
                    _t1376 = _t1377
                end
                _t1375 = _t1376
            end
            _t1374 = _t1375
        end
        _t1373 = _t1374
    else
        _t1373 = -1
    end
    prediction715 = _t1373
    if prediction715 == 3
        _t1379 = parse_snapshot(parser)
        snapshot719 = _t1379
        _t1380 = Proto.Write(write_type=OneOf(:snapshot, snapshot719))
        _t1378 = _t1380
    else
        if prediction715 == 2
            _t1382 = parse_context(parser)
            context718 = _t1382
            _t1383 = Proto.Write(write_type=OneOf(:context, context718))
            _t1381 = _t1383
        else
            if prediction715 == 1
                _t1385 = parse_undefine(parser)
                undefine717 = _t1385
                _t1386 = Proto.Write(write_type=OneOf(:undefine, undefine717))
                _t1384 = _t1386
            else
                if prediction715 == 0
                    _t1388 = parse_define(parser)
                    define716 = _t1388
                    _t1389 = Proto.Write(write_type=OneOf(:define, define716))
                    _t1387 = _t1389
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1384 = _t1387
            end
            _t1381 = _t1384
        end
        _t1378 = _t1381
    end
    result721 = _t1378
    record_span!(parser, span_start720, "Write")
    return result721
end

function parse_define(parser::ParserState)::Proto.Define
    span_start723 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1390 = parse_fragment(parser)
    fragment722 = _t1390
    consume_literal!(parser, ")")
    _t1391 = Proto.Define(fragment=fragment722)
    result724 = _t1391
    record_span!(parser, span_start723, "Define")
    return result724
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start730 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1392 = parse_new_fragment_id(parser)
    new_fragment_id725 = _t1392
    xs726 = Proto.Declaration[]
    cond727 = match_lookahead_literal(parser, "(", 0)
    while cond727
        _t1393 = parse_declaration(parser)
        item728 = _t1393
        push!(xs726, item728)
        cond727 = match_lookahead_literal(parser, "(", 0)
    end
    declarations729 = xs726
    consume_literal!(parser, ")")
    result731 = construct_fragment(parser, new_fragment_id725, declarations729)
    record_span!(parser, span_start730, "Fragment")
    return result731
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start733 = span_start(parser)
    _t1394 = parse_fragment_id(parser)
    fragment_id732 = _t1394
    start_fragment!(parser, fragment_id732)
    result734 = fragment_id732
    record_span!(parser, span_start733, "FragmentId")
    return result734
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start740 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1396 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1397 = 2
            else
                if match_lookahead_literal(parser, "edb", 1)
                    _t1398 = 3
                else
                    if match_lookahead_literal(parser, "def", 1)
                        _t1399 = 0
                    else
                        if match_lookahead_literal(parser, "csv_data", 1)
                            _t1400 = 3
                        else
                            if match_lookahead_literal(parser, "betree_relation", 1)
                                _t1401 = 3
                            else
                                if match_lookahead_literal(parser, "algorithm", 1)
                                    _t1402 = 1
                                else
                                    _t1402 = -1
                                end
                                _t1401 = _t1402
                            end
                            _t1400 = _t1401
                        end
                        _t1399 = _t1400
                    end
                    _t1398 = _t1399
                end
                _t1397 = _t1398
            end
            _t1396 = _t1397
        end
        _t1395 = _t1396
    else
        _t1395 = -1
    end
    prediction735 = _t1395
    if prediction735 == 3
        _t1404 = parse_data(parser)
        data739 = _t1404
        _t1405 = Proto.Declaration(declaration_type=OneOf(:data, data739))
        _t1403 = _t1405
    else
        if prediction735 == 2
            _t1407 = parse_constraint(parser)
            constraint738 = _t1407
            _t1408 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint738))
            _t1406 = _t1408
        else
            if prediction735 == 1
                _t1410 = parse_algorithm(parser)
                algorithm737 = _t1410
                _t1411 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm737))
                _t1409 = _t1411
            else
                if prediction735 == 0
                    _t1413 = parse_def(parser)
                    def736 = _t1413
                    _t1414 = Proto.Declaration(declaration_type=OneOf(:def, def736))
                    _t1412 = _t1414
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1409 = _t1412
            end
            _t1406 = _t1409
        end
        _t1403 = _t1406
    end
    result741 = _t1403
    record_span!(parser, span_start740, "Declaration")
    return result741
end

function parse_def(parser::ParserState)::Proto.Def
    span_start745 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1415 = parse_relation_id(parser)
    relation_id742 = _t1415
    _t1416 = parse_abstraction(parser)
    abstraction743 = _t1416
    if match_lookahead_literal(parser, "(", 0)
        _t1418 = parse_attrs(parser)
        _t1417 = _t1418
    else
        _t1417 = nothing
    end
    attrs744 = _t1417
    consume_literal!(parser, ")")
    _t1419 = Proto.Def(name=relation_id742, body=abstraction743, attrs=(!isnothing(attrs744) ? attrs744 : Proto.Attribute[]))
    result746 = _t1419
    record_span!(parser, span_start745, "Def")
    return result746
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start750 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1420 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1421 = 1
        else
            _t1421 = -1
        end
        _t1420 = _t1421
    end
    prediction747 = _t1420
    if prediction747 == 1
        uint128749 = consume_terminal!(parser, "UINT128")
        _t1422 = Proto.RelationId(uint128749.low, uint128749.high)
    else
        if prediction747 == 0
            consume_literal!(parser, ":")
            symbol748 = consume_terminal!(parser, "SYMBOL")
            _t1423 = relation_id_from_string(parser, symbol748)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1422 = _t1423
    end
    result751 = _t1422
    record_span!(parser, span_start750, "RelationId")
    return result751
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start754 = span_start(parser)
    consume_literal!(parser, "(")
    _t1424 = parse_bindings(parser)
    bindings752 = _t1424
    _t1425 = parse_formula(parser)
    formula753 = _t1425
    consume_literal!(parser, ")")
    _t1426 = Proto.Abstraction(vars=vcat(bindings752[1], !isnothing(bindings752[2]) ? bindings752[2] : []), value=formula753)
    result755 = _t1426
    record_span!(parser, span_start754, "Abstraction")
    return result755
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs756 = Proto.Binding[]
    cond757 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond757
        _t1427 = parse_binding(parser)
        item758 = _t1427
        push!(xs756, item758)
        cond757 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings759 = xs756
    if match_lookahead_literal(parser, "|", 0)
        _t1429 = parse_value_bindings(parser)
        _t1428 = _t1429
    else
        _t1428 = nothing
    end
    value_bindings760 = _t1428
    consume_literal!(parser, "]")
    return (bindings759, (!isnothing(value_bindings760) ? value_bindings760 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start763 = span_start(parser)
    symbol761 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1430 = parse_type(parser)
    type762 = _t1430
    _t1431 = Proto.Var(name=symbol761)
    _t1432 = Proto.Binding(var=_t1431, var"#type"=type762)
    result764 = _t1432
    record_span!(parser, span_start763, "Binding")
    return result764
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start780 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1433 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1434 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1435 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1436 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1437 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1438 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1439 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1440 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1441 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1442 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1443 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1444 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1445 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1446 = 9
                                                        else
                                                            _t1446 = -1
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
    prediction765 = _t1433
    if prediction765 == 13
        _t1448 = parse_uint32_type(parser)
        uint32_type779 = _t1448
        _t1449 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type779))
        _t1447 = _t1449
    else
        if prediction765 == 12
            _t1451 = parse_float32_type(parser)
            float32_type778 = _t1451
            _t1452 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type778))
            _t1450 = _t1452
        else
            if prediction765 == 11
                _t1454 = parse_int32_type(parser)
                int32_type777 = _t1454
                _t1455 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type777))
                _t1453 = _t1455
            else
                if prediction765 == 10
                    _t1457 = parse_boolean_type(parser)
                    boolean_type776 = _t1457
                    _t1458 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type776))
                    _t1456 = _t1458
                else
                    if prediction765 == 9
                        _t1460 = parse_decimal_type(parser)
                        decimal_type775 = _t1460
                        _t1461 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type775))
                        _t1459 = _t1461
                    else
                        if prediction765 == 8
                            _t1463 = parse_missing_type(parser)
                            missing_type774 = _t1463
                            _t1464 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type774))
                            _t1462 = _t1464
                        else
                            if prediction765 == 7
                                _t1466 = parse_datetime_type(parser)
                                datetime_type773 = _t1466
                                _t1467 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type773))
                                _t1465 = _t1467
                            else
                                if prediction765 == 6
                                    _t1469 = parse_date_type(parser)
                                    date_type772 = _t1469
                                    _t1470 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type772))
                                    _t1468 = _t1470
                                else
                                    if prediction765 == 5
                                        _t1472 = parse_int128_type(parser)
                                        int128_type771 = _t1472
                                        _t1473 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type771))
                                        _t1471 = _t1473
                                    else
                                        if prediction765 == 4
                                            _t1475 = parse_uint128_type(parser)
                                            uint128_type770 = _t1475
                                            _t1476 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type770))
                                            _t1474 = _t1476
                                        else
                                            if prediction765 == 3
                                                _t1478 = parse_float_type(parser)
                                                float_type769 = _t1478
                                                _t1479 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type769))
                                                _t1477 = _t1479
                                            else
                                                if prediction765 == 2
                                                    _t1481 = parse_int_type(parser)
                                                    int_type768 = _t1481
                                                    _t1482 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type768))
                                                    _t1480 = _t1482
                                                else
                                                    if prediction765 == 1
                                                        _t1484 = parse_string_type(parser)
                                                        string_type767 = _t1484
                                                        _t1485 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type767))
                                                        _t1483 = _t1485
                                                    else
                                                        if prediction765 == 0
                                                            _t1487 = parse_unspecified_type(parser)
                                                            unspecified_type766 = _t1487
                                                            _t1488 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type766))
                                                            _t1486 = _t1488
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                            _t1462 = _t1465
                        end
                        _t1459 = _t1462
                    end
                    _t1456 = _t1459
                end
                _t1453 = _t1456
            end
            _t1450 = _t1453
        end
        _t1447 = _t1450
    end
    result781 = _t1447
    record_span!(parser, span_start780, "Type")
    return result781
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start782 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1489 = Proto.UnspecifiedType()
    result783 = _t1489
    record_span!(parser, span_start782, "UnspecifiedType")
    return result783
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start784 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1490 = Proto.StringType()
    result785 = _t1490
    record_span!(parser, span_start784, "StringType")
    return result785
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start786 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1491 = Proto.IntType()
    result787 = _t1491
    record_span!(parser, span_start786, "IntType")
    return result787
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start788 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1492 = Proto.FloatType()
    result789 = _t1492
    record_span!(parser, span_start788, "FloatType")
    return result789
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start790 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1493 = Proto.UInt128Type()
    result791 = _t1493
    record_span!(parser, span_start790, "UInt128Type")
    return result791
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start792 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1494 = Proto.Int128Type()
    result793 = _t1494
    record_span!(parser, span_start792, "Int128Type")
    return result793
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start794 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1495 = Proto.DateType()
    result795 = _t1495
    record_span!(parser, span_start794, "DateType")
    return result795
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start796 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1496 = Proto.DateTimeType()
    result797 = _t1496
    record_span!(parser, span_start796, "DateTimeType")
    return result797
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start798 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1497 = Proto.MissingType()
    result799 = _t1497
    record_span!(parser, span_start798, "MissingType")
    return result799
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start802 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int800 = consume_terminal!(parser, "INT")
    int_3801 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1498 = Proto.DecimalType(precision=Int32(int800), scale=Int32(int_3801))
    result803 = _t1498
    record_span!(parser, span_start802, "DecimalType")
    return result803
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start804 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1499 = Proto.BooleanType()
    result805 = _t1499
    record_span!(parser, span_start804, "BooleanType")
    return result805
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start806 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1500 = Proto.Int32Type()
    result807 = _t1500
    record_span!(parser, span_start806, "Int32Type")
    return result807
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start808 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1501 = Proto.Float32Type()
    result809 = _t1501
    record_span!(parser, span_start808, "Float32Type")
    return result809
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start810 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1502 = Proto.UInt32Type()
    result811 = _t1502
    record_span!(parser, span_start810, "UInt32Type")
    return result811
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs812 = Proto.Binding[]
    cond813 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond813
        _t1503 = parse_binding(parser)
        item814 = _t1503
        push!(xs812, item814)
        cond813 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings815 = xs812
    return bindings815
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start830 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1505 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1506 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1507 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1508 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1509 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1510 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1511 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1512 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1513 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1514 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1515 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1516 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1517 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1518 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1519 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1520 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1521 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1522 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1523 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1524 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1525 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1526 = 10
                                                                                            else
                                                                                                _t1526 = -1
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
                end
                _t1506 = _t1507
            end
            _t1505 = _t1506
        end
        _t1504 = _t1505
    else
        _t1504 = -1
    end
    prediction816 = _t1504
    if prediction816 == 12
        _t1528 = parse_cast(parser)
        cast829 = _t1528
        _t1529 = Proto.Formula(formula_type=OneOf(:cast, cast829))
        _t1527 = _t1529
    else
        if prediction816 == 11
            _t1531 = parse_rel_atom(parser)
            rel_atom828 = _t1531
            _t1532 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom828))
            _t1530 = _t1532
        else
            if prediction816 == 10
                _t1534 = parse_primitive(parser)
                primitive827 = _t1534
                _t1535 = Proto.Formula(formula_type=OneOf(:primitive, primitive827))
                _t1533 = _t1535
            else
                if prediction816 == 9
                    _t1537 = parse_pragma(parser)
                    pragma826 = _t1537
                    _t1538 = Proto.Formula(formula_type=OneOf(:pragma, pragma826))
                    _t1536 = _t1538
                else
                    if prediction816 == 8
                        _t1540 = parse_atom(parser)
                        atom825 = _t1540
                        _t1541 = Proto.Formula(formula_type=OneOf(:atom, atom825))
                        _t1539 = _t1541
                    else
                        if prediction816 == 7
                            _t1543 = parse_ffi(parser)
                            ffi824 = _t1543
                            _t1544 = Proto.Formula(formula_type=OneOf(:ffi, ffi824))
                            _t1542 = _t1544
                        else
                            if prediction816 == 6
                                _t1546 = parse_not(parser)
                                not823 = _t1546
                                _t1547 = Proto.Formula(formula_type=OneOf(:not, not823))
                                _t1545 = _t1547
                            else
                                if prediction816 == 5
                                    _t1549 = parse_disjunction(parser)
                                    disjunction822 = _t1549
                                    _t1550 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction822))
                                    _t1548 = _t1550
                                else
                                    if prediction816 == 4
                                        _t1552 = parse_conjunction(parser)
                                        conjunction821 = _t1552
                                        _t1553 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction821))
                                        _t1551 = _t1553
                                    else
                                        if prediction816 == 3
                                            _t1555 = parse_reduce(parser)
                                            reduce820 = _t1555
                                            _t1556 = Proto.Formula(formula_type=OneOf(:reduce, reduce820))
                                            _t1554 = _t1556
                                        else
                                            if prediction816 == 2
                                                _t1558 = parse_exists(parser)
                                                exists819 = _t1558
                                                _t1559 = Proto.Formula(formula_type=OneOf(:exists, exists819))
                                                _t1557 = _t1559
                                            else
                                                if prediction816 == 1
                                                    _t1561 = parse_false(parser)
                                                    false818 = _t1561
                                                    _t1562 = Proto.Formula(formula_type=OneOf(:disjunction, false818))
                                                    _t1560 = _t1562
                                                else
                                                    if prediction816 == 0
                                                        _t1564 = parse_true(parser)
                                                        true817 = _t1564
                                                        _t1565 = Proto.Formula(formula_type=OneOf(:conjunction, true817))
                                                        _t1563 = _t1565
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
                            _t1542 = _t1545
                        end
                        _t1539 = _t1542
                    end
                    _t1536 = _t1539
                end
                _t1533 = _t1536
            end
            _t1530 = _t1533
        end
        _t1527 = _t1530
    end
    result831 = _t1527
    record_span!(parser, span_start830, "Formula")
    return result831
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start832 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1566 = Proto.Conjunction(args=Proto.Formula[])
    result833 = _t1566
    record_span!(parser, span_start832, "Conjunction")
    return result833
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start834 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1567 = Proto.Disjunction(args=Proto.Formula[])
    result835 = _t1567
    record_span!(parser, span_start834, "Disjunction")
    return result835
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start838 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1568 = parse_bindings(parser)
    bindings836 = _t1568
    _t1569 = parse_formula(parser)
    formula837 = _t1569
    consume_literal!(parser, ")")
    _t1570 = Proto.Abstraction(vars=vcat(bindings836[1], !isnothing(bindings836[2]) ? bindings836[2] : []), value=formula837)
    _t1571 = Proto.Exists(body=_t1570)
    result839 = _t1571
    record_span!(parser, span_start838, "Exists")
    return result839
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start843 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1572 = parse_abstraction(parser)
    abstraction840 = _t1572
    _t1573 = parse_abstraction(parser)
    abstraction_3841 = _t1573
    _t1574 = parse_terms(parser)
    terms842 = _t1574
    consume_literal!(parser, ")")
    _t1575 = Proto.Reduce(op=abstraction840, body=abstraction_3841, terms=terms842)
    result844 = _t1575
    record_span!(parser, span_start843, "Reduce")
    return result844
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs845 = Proto.Term[]
    cond846 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond846
        _t1576 = parse_term(parser)
        item847 = _t1576
        push!(xs845, item847)
        cond846 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms848 = xs845
    consume_literal!(parser, ")")
    return terms848
end

function parse_term(parser::ParserState)::Proto.Term
    span_start852 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1577 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1578 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1579 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1580 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1581 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1582 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1583 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1584 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1585 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1586 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1587 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1588 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1589 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1590 = 1
                                                        else
                                                            _t1590 = -1
                                                        end
                                                        _t1589 = _t1590
                                                    end
                                                    _t1588 = _t1589
                                                end
                                                _t1587 = _t1588
                                            end
                                            _t1586 = _t1587
                                        end
                                        _t1585 = _t1586
                                    end
                                    _t1584 = _t1585
                                end
                                _t1583 = _t1584
                            end
                            _t1582 = _t1583
                        end
                        _t1581 = _t1582
                    end
                    _t1580 = _t1581
                end
                _t1579 = _t1580
            end
            _t1578 = _t1579
        end
        _t1577 = _t1578
    end
    prediction849 = _t1577
    if prediction849 == 1
        _t1592 = parse_value(parser)
        value851 = _t1592
        _t1593 = Proto.Term(term_type=OneOf(:constant, value851))
        _t1591 = _t1593
    else
        if prediction849 == 0
            _t1595 = parse_var(parser)
            var850 = _t1595
            _t1596 = Proto.Term(term_type=OneOf(:var, var850))
            _t1594 = _t1596
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1591 = _t1594
    end
    result853 = _t1591
    record_span!(parser, span_start852, "Term")
    return result853
end

function parse_var(parser::ParserState)::Proto.Var
    span_start855 = span_start(parser)
    symbol854 = consume_terminal!(parser, "SYMBOL")
    _t1597 = Proto.Var(name=symbol854)
    result856 = _t1597
    record_span!(parser, span_start855, "Var")
    return result856
end

function parse_value(parser::ParserState)::Proto.Value
    span_start870 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1598 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1599 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1600 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1602 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1603 = 0
                        else
                            _t1603 = -1
                        end
                        _t1602 = _t1603
                    end
                    _t1601 = _t1602
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1604 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1605 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1606 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1607 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1608 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1609 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1610 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1611 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1612 = 10
                                                    else
                                                        _t1612 = -1
                                                    end
                                                    _t1611 = _t1612
                                                end
                                                _t1610 = _t1611
                                            end
                                            _t1609 = _t1610
                                        end
                                        _t1608 = _t1609
                                    end
                                    _t1607 = _t1608
                                end
                                _t1606 = _t1607
                            end
                            _t1605 = _t1606
                        end
                        _t1604 = _t1605
                    end
                    _t1601 = _t1604
                end
                _t1600 = _t1601
            end
            _t1599 = _t1600
        end
        _t1598 = _t1599
    end
    prediction857 = _t1598
    if prediction857 == 12
        _t1614 = parse_boolean_value(parser)
        boolean_value869 = _t1614
        _t1615 = Proto.Value(value=OneOf(:boolean_value, boolean_value869))
        _t1613 = _t1615
    else
        if prediction857 == 11
            consume_literal!(parser, "missing")
            _t1617 = Proto.MissingValue()
            _t1618 = Proto.Value(value=OneOf(:missing_value, _t1617))
            _t1616 = _t1618
        else
            if prediction857 == 10
                formatted_decimal868 = consume_terminal!(parser, "DECIMAL")
                _t1620 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal868))
                _t1619 = _t1620
            else
                if prediction857 == 9
                    formatted_int128867 = consume_terminal!(parser, "INT128")
                    _t1622 = Proto.Value(value=OneOf(:int128_value, formatted_int128867))
                    _t1621 = _t1622
                else
                    if prediction857 == 8
                        formatted_uint128866 = consume_terminal!(parser, "UINT128")
                        _t1624 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128866))
                        _t1623 = _t1624
                    else
                        if prediction857 == 7
                            formatted_uint32865 = consume_terminal!(parser, "UINT32")
                            _t1626 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32865))
                            _t1625 = _t1626
                        else
                            if prediction857 == 6
                                formatted_float864 = consume_terminal!(parser, "FLOAT")
                                _t1628 = Proto.Value(value=OneOf(:float_value, formatted_float864))
                                _t1627 = _t1628
                            else
                                if prediction857 == 5
                                    formatted_float32863 = consume_terminal!(parser, "FLOAT32")
                                    _t1630 = Proto.Value(value=OneOf(:float32_value, formatted_float32863))
                                    _t1629 = _t1630
                                else
                                    if prediction857 == 4
                                        formatted_int862 = consume_terminal!(parser, "INT")
                                        _t1632 = Proto.Value(value=OneOf(:int_value, formatted_int862))
                                        _t1631 = _t1632
                                    else
                                        if prediction857 == 3
                                            formatted_int32861 = consume_terminal!(parser, "INT32")
                                            _t1634 = Proto.Value(value=OneOf(:int32_value, formatted_int32861))
                                            _t1633 = _t1634
                                        else
                                            if prediction857 == 2
                                                formatted_string860 = consume_terminal!(parser, "STRING")
                                                _t1636 = Proto.Value(value=OneOf(:string_value, formatted_string860))
                                                _t1635 = _t1636
                                            else
                                                if prediction857 == 1
                                                    _t1638 = parse_datetime(parser)
                                                    datetime859 = _t1638
                                                    _t1639 = Proto.Value(value=OneOf(:datetime_value, datetime859))
                                                    _t1637 = _t1639
                                                else
                                                    if prediction857 == 0
                                                        _t1641 = parse_date(parser)
                                                        date858 = _t1641
                                                        _t1642 = Proto.Value(value=OneOf(:date_value, date858))
                                                        _t1640 = _t1642
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1637 = _t1640
                                                end
                                                _t1635 = _t1637
                                            end
                                            _t1633 = _t1635
                                        end
                                        _t1631 = _t1633
                                    end
                                    _t1629 = _t1631
                                end
                                _t1627 = _t1629
                            end
                            _t1625 = _t1627
                        end
                        _t1623 = _t1625
                    end
                    _t1621 = _t1623
                end
                _t1619 = _t1621
            end
            _t1616 = _t1619
        end
        _t1613 = _t1616
    end
    result871 = _t1613
    record_span!(parser, span_start870, "Value")
    return result871
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start875 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int872 = consume_terminal!(parser, "INT")
    formatted_int_3873 = consume_terminal!(parser, "INT")
    formatted_int_4874 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1643 = Proto.DateValue(year=Int32(formatted_int872), month=Int32(formatted_int_3873), day=Int32(formatted_int_4874))
    result876 = _t1643
    record_span!(parser, span_start875, "DateValue")
    return result876
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start884 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int877 = consume_terminal!(parser, "INT")
    formatted_int_3878 = consume_terminal!(parser, "INT")
    formatted_int_4879 = consume_terminal!(parser, "INT")
    formatted_int_5880 = consume_terminal!(parser, "INT")
    formatted_int_6881 = consume_terminal!(parser, "INT")
    formatted_int_7882 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1644 = consume_terminal!(parser, "INT")
    else
        _t1644 = nothing
    end
    formatted_int_8883 = _t1644
    consume_literal!(parser, ")")
    _t1645 = Proto.DateTimeValue(year=Int32(formatted_int877), month=Int32(formatted_int_3878), day=Int32(formatted_int_4879), hour=Int32(formatted_int_5880), minute=Int32(formatted_int_6881), second=Int32(formatted_int_7882), microsecond=Int32((!isnothing(formatted_int_8883) ? formatted_int_8883 : 0)))
    result885 = _t1645
    record_span!(parser, span_start884, "DateTimeValue")
    return result885
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start890 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs886 = Proto.Formula[]
    cond887 = match_lookahead_literal(parser, "(", 0)
    while cond887
        _t1646 = parse_formula(parser)
        item888 = _t1646
        push!(xs886, item888)
        cond887 = match_lookahead_literal(parser, "(", 0)
    end
    formulas889 = xs886
    consume_literal!(parser, ")")
    _t1647 = Proto.Conjunction(args=formulas889)
    result891 = _t1647
    record_span!(parser, span_start890, "Conjunction")
    return result891
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start896 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs892 = Proto.Formula[]
    cond893 = match_lookahead_literal(parser, "(", 0)
    while cond893
        _t1648 = parse_formula(parser)
        item894 = _t1648
        push!(xs892, item894)
        cond893 = match_lookahead_literal(parser, "(", 0)
    end
    formulas895 = xs892
    consume_literal!(parser, ")")
    _t1649 = Proto.Disjunction(args=formulas895)
    result897 = _t1649
    record_span!(parser, span_start896, "Disjunction")
    return result897
end

function parse_not(parser::ParserState)::Proto.Not
    span_start899 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1650 = parse_formula(parser)
    formula898 = _t1650
    consume_literal!(parser, ")")
    _t1651 = Proto.Not(arg=formula898)
    result900 = _t1651
    record_span!(parser, span_start899, "Not")
    return result900
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start904 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1652 = parse_name(parser)
    name901 = _t1652
    _t1653 = parse_ffi_args(parser)
    ffi_args902 = _t1653
    _t1654 = parse_terms(parser)
    terms903 = _t1654
    consume_literal!(parser, ")")
    _t1655 = Proto.FFI(name=name901, args=ffi_args902, terms=terms903)
    result905 = _t1655
    record_span!(parser, span_start904, "FFI")
    return result905
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol906 = consume_terminal!(parser, "SYMBOL")
    return symbol906
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs907 = Proto.Abstraction[]
    cond908 = match_lookahead_literal(parser, "(", 0)
    while cond908
        _t1656 = parse_abstraction(parser)
        item909 = _t1656
        push!(xs907, item909)
        cond908 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions910 = xs907
    consume_literal!(parser, ")")
    return abstractions910
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start916 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1657 = parse_relation_id(parser)
    relation_id911 = _t1657
    xs912 = Proto.Term[]
    cond913 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond913
        _t1658 = parse_term(parser)
        item914 = _t1658
        push!(xs912, item914)
        cond913 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms915 = xs912
    consume_literal!(parser, ")")
    _t1659 = Proto.Atom(name=relation_id911, terms=terms915)
    result917 = _t1659
    record_span!(parser, span_start916, "Atom")
    return result917
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start923 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1660 = parse_name(parser)
    name918 = _t1660
    xs919 = Proto.Term[]
    cond920 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond920
        _t1661 = parse_term(parser)
        item921 = _t1661
        push!(xs919, item921)
        cond920 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms922 = xs919
    consume_literal!(parser, ")")
    _t1662 = Proto.Pragma(name=name918, terms=terms922)
    result924 = _t1662
    record_span!(parser, span_start923, "Pragma")
    return result924
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start940 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1664 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1665 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1666 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1667 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1668 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1669 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1670 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1671 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1672 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1673 = 7
                                            else
                                                _t1673 = -1
                                            end
                                            _t1672 = _t1673
                                        end
                                        _t1671 = _t1672
                                    end
                                    _t1670 = _t1671
                                end
                                _t1669 = _t1670
                            end
                            _t1668 = _t1669
                        end
                        _t1667 = _t1668
                    end
                    _t1666 = _t1667
                end
                _t1665 = _t1666
            end
            _t1664 = _t1665
        end
        _t1663 = _t1664
    else
        _t1663 = -1
    end
    prediction925 = _t1663
    if prediction925 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1675 = parse_name(parser)
        name935 = _t1675
        xs936 = Proto.RelTerm[]
        cond937 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond937
            _t1676 = parse_rel_term(parser)
            item938 = _t1676
            push!(xs936, item938)
            cond937 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms939 = xs936
        consume_literal!(parser, ")")
        _t1677 = Proto.Primitive(name=name935, terms=rel_terms939)
        _t1674 = _t1677
    else
        if prediction925 == 8
            _t1679 = parse_divide(parser)
            divide934 = _t1679
            _t1678 = divide934
        else
            if prediction925 == 7
                _t1681 = parse_multiply(parser)
                multiply933 = _t1681
                _t1680 = multiply933
            else
                if prediction925 == 6
                    _t1683 = parse_minus(parser)
                    minus932 = _t1683
                    _t1682 = minus932
                else
                    if prediction925 == 5
                        _t1685 = parse_add(parser)
                        add931 = _t1685
                        _t1684 = add931
                    else
                        if prediction925 == 4
                            _t1687 = parse_gt_eq(parser)
                            gt_eq930 = _t1687
                            _t1686 = gt_eq930
                        else
                            if prediction925 == 3
                                _t1689 = parse_gt(parser)
                                gt929 = _t1689
                                _t1688 = gt929
                            else
                                if prediction925 == 2
                                    _t1691 = parse_lt_eq(parser)
                                    lt_eq928 = _t1691
                                    _t1690 = lt_eq928
                                else
                                    if prediction925 == 1
                                        _t1693 = parse_lt(parser)
                                        lt927 = _t1693
                                        _t1692 = lt927
                                    else
                                        if prediction925 == 0
                                            _t1695 = parse_eq(parser)
                                            eq926 = _t1695
                                            _t1694 = eq926
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1692 = _t1694
                                    end
                                    _t1690 = _t1692
                                end
                                _t1688 = _t1690
                            end
                            _t1686 = _t1688
                        end
                        _t1684 = _t1686
                    end
                    _t1682 = _t1684
                end
                _t1680 = _t1682
            end
            _t1678 = _t1680
        end
        _t1674 = _t1678
    end
    result941 = _t1674
    record_span!(parser, span_start940, "Primitive")
    return result941
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start944 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1696 = parse_term(parser)
    term942 = _t1696
    _t1697 = parse_term(parser)
    term_3943 = _t1697
    consume_literal!(parser, ")")
    _t1698 = Proto.RelTerm(rel_term_type=OneOf(:term, term942))
    _t1699 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3943))
    _t1700 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1698, _t1699])
    result945 = _t1700
    record_span!(parser, span_start944, "Primitive")
    return result945
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start948 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1701 = parse_term(parser)
    term946 = _t1701
    _t1702 = parse_term(parser)
    term_3947 = _t1702
    consume_literal!(parser, ")")
    _t1703 = Proto.RelTerm(rel_term_type=OneOf(:term, term946))
    _t1704 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3947))
    _t1705 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1703, _t1704])
    result949 = _t1705
    record_span!(parser, span_start948, "Primitive")
    return result949
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start952 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1706 = parse_term(parser)
    term950 = _t1706
    _t1707 = parse_term(parser)
    term_3951 = _t1707
    consume_literal!(parser, ")")
    _t1708 = Proto.RelTerm(rel_term_type=OneOf(:term, term950))
    _t1709 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3951))
    _t1710 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1708, _t1709])
    result953 = _t1710
    record_span!(parser, span_start952, "Primitive")
    return result953
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start956 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1711 = parse_term(parser)
    term954 = _t1711
    _t1712 = parse_term(parser)
    term_3955 = _t1712
    consume_literal!(parser, ")")
    _t1713 = Proto.RelTerm(rel_term_type=OneOf(:term, term954))
    _t1714 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3955))
    _t1715 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1713, _t1714])
    result957 = _t1715
    record_span!(parser, span_start956, "Primitive")
    return result957
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1716 = parse_term(parser)
    term958 = _t1716
    _t1717 = parse_term(parser)
    term_3959 = _t1717
    consume_literal!(parser, ")")
    _t1718 = Proto.RelTerm(rel_term_type=OneOf(:term, term958))
    _t1719 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3959))
    _t1720 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1718, _t1719])
    result961 = _t1720
    record_span!(parser, span_start960, "Primitive")
    return result961
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start965 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1721 = parse_term(parser)
    term962 = _t1721
    _t1722 = parse_term(parser)
    term_3963 = _t1722
    _t1723 = parse_term(parser)
    term_4964 = _t1723
    consume_literal!(parser, ")")
    _t1724 = Proto.RelTerm(rel_term_type=OneOf(:term, term962))
    _t1725 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3963))
    _t1726 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4964))
    _t1727 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1724, _t1725, _t1726])
    result966 = _t1727
    record_span!(parser, span_start965, "Primitive")
    return result966
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start970 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1728 = parse_term(parser)
    term967 = _t1728
    _t1729 = parse_term(parser)
    term_3968 = _t1729
    _t1730 = parse_term(parser)
    term_4969 = _t1730
    consume_literal!(parser, ")")
    _t1731 = Proto.RelTerm(rel_term_type=OneOf(:term, term967))
    _t1732 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3968))
    _t1733 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4969))
    _t1734 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1731, _t1732, _t1733])
    result971 = _t1734
    record_span!(parser, span_start970, "Primitive")
    return result971
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start975 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1735 = parse_term(parser)
    term972 = _t1735
    _t1736 = parse_term(parser)
    term_3973 = _t1736
    _t1737 = parse_term(parser)
    term_4974 = _t1737
    consume_literal!(parser, ")")
    _t1738 = Proto.RelTerm(rel_term_type=OneOf(:term, term972))
    _t1739 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3973))
    _t1740 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4974))
    _t1741 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1738, _t1739, _t1740])
    result976 = _t1741
    record_span!(parser, span_start975, "Primitive")
    return result976
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1742 = parse_term(parser)
    term977 = _t1742
    _t1743 = parse_term(parser)
    term_3978 = _t1743
    _t1744 = parse_term(parser)
    term_4979 = _t1744
    consume_literal!(parser, ")")
    _t1745 = Proto.RelTerm(rel_term_type=OneOf(:term, term977))
    _t1746 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3978))
    _t1747 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4979))
    _t1748 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1745, _t1746, _t1747])
    result981 = _t1748
    record_span!(parser, span_start980, "Primitive")
    return result981
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start985 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1749 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1750 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1751 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1752 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1753 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1754 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT32", 0)
                                _t1755 = 1
                            else
                                if match_lookahead_terminal(parser, "UINT128", 0)
                                    _t1756 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1757 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1758 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1759 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1760 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1761 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1762 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1763 = 1
                                                            else
                                                                _t1763 = -1
                                                            end
                                                            _t1762 = _t1763
                                                        end
                                                        _t1761 = _t1762
                                                    end
                                                    _t1760 = _t1761
                                                end
                                                _t1759 = _t1760
                                            end
                                            _t1758 = _t1759
                                        end
                                        _t1757 = _t1758
                                    end
                                    _t1756 = _t1757
                                end
                                _t1755 = _t1756
                            end
                            _t1754 = _t1755
                        end
                        _t1753 = _t1754
                    end
                    _t1752 = _t1753
                end
                _t1751 = _t1752
            end
            _t1750 = _t1751
        end
        _t1749 = _t1750
    end
    prediction982 = _t1749
    if prediction982 == 1
        _t1765 = parse_term(parser)
        term984 = _t1765
        _t1766 = Proto.RelTerm(rel_term_type=OneOf(:term, term984))
        _t1764 = _t1766
    else
        if prediction982 == 0
            _t1768 = parse_specialized_value(parser)
            specialized_value983 = _t1768
            _t1769 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value983))
            _t1767 = _t1769
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1764 = _t1767
    end
    result986 = _t1764
    record_span!(parser, span_start985, "RelTerm")
    return result986
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start988 = span_start(parser)
    consume_literal!(parser, "#")
    _t1770 = parse_raw_value(parser)
    raw_value987 = _t1770
    result989 = raw_value987
    record_span!(parser, span_start988, "Value")
    return result989
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start995 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1771 = parse_name(parser)
    name990 = _t1771
    xs991 = Proto.RelTerm[]
    cond992 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond992
        _t1772 = parse_rel_term(parser)
        item993 = _t1772
        push!(xs991, item993)
        cond992 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms994 = xs991
    consume_literal!(parser, ")")
    _t1773 = Proto.RelAtom(name=name990, terms=rel_terms994)
    result996 = _t1773
    record_span!(parser, span_start995, "RelAtom")
    return result996
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start999 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1774 = parse_term(parser)
    term997 = _t1774
    _t1775 = parse_term(parser)
    term_3998 = _t1775
    consume_literal!(parser, ")")
    _t1776 = Proto.Cast(input=term997, result=term_3998)
    result1000 = _t1776
    record_span!(parser, span_start999, "Cast")
    return result1000
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1001 = Proto.Attribute[]
    cond1002 = match_lookahead_literal(parser, "(", 0)
    while cond1002
        _t1777 = parse_attribute(parser)
        item1003 = _t1777
        push!(xs1001, item1003)
        cond1002 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1004 = xs1001
    consume_literal!(parser, ")")
    return attributes1004
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start1010 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1778 = parse_name(parser)
    name1005 = _t1778
    xs1006 = Proto.Value[]
    cond1007 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond1007
        _t1779 = parse_raw_value(parser)
        item1008 = _t1779
        push!(xs1006, item1008)
        cond1007 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values1009 = xs1006
    consume_literal!(parser, ")")
    _t1780 = Proto.Attribute(name=name1005, args=raw_values1009)
    result1011 = _t1780
    record_span!(parser, span_start1010, "Attribute")
    return result1011
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start1017 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1012 = Proto.RelationId[]
    cond1013 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1013
        _t1781 = parse_relation_id(parser)
        item1014 = _t1781
        push!(xs1012, item1014)
        cond1013 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1015 = xs1012
    _t1782 = parse_script(parser)
    script1016 = _t1782
    consume_literal!(parser, ")")
    _t1783 = Proto.Algorithm(var"#global"=relation_ids1015, body=script1016)
    result1018 = _t1783
    record_span!(parser, span_start1017, "Algorithm")
    return result1018
end

function parse_script(parser::ParserState)::Proto.Script
    span_start1023 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1019 = Proto.Construct[]
    cond1020 = match_lookahead_literal(parser, "(", 0)
    while cond1020
        _t1784 = parse_construct(parser)
        item1021 = _t1784
        push!(xs1019, item1021)
        cond1020 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1022 = xs1019
    consume_literal!(parser, ")")
    _t1785 = Proto.Script(constructs=constructs1022)
    result1024 = _t1785
    record_span!(parser, span_start1023, "Script")
    return result1024
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start1028 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1787 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1788 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1789 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1790 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1791 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1792 = 1
                            else
                                _t1792 = -1
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
    else
        _t1786 = -1
    end
    prediction1025 = _t1786
    if prediction1025 == 1
        _t1794 = parse_instruction(parser)
        instruction1027 = _t1794
        _t1795 = Proto.Construct(construct_type=OneOf(:instruction, instruction1027))
        _t1793 = _t1795
    else
        if prediction1025 == 0
            _t1797 = parse_loop(parser)
            loop1026 = _t1797
            _t1798 = Proto.Construct(construct_type=OneOf(:loop, loop1026))
            _t1796 = _t1798
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1793 = _t1796
    end
    result1029 = _t1793
    record_span!(parser, span_start1028, "Construct")
    return result1029
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1032 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1799 = parse_init(parser)
    init1030 = _t1799
    _t1800 = parse_script(parser)
    script1031 = _t1800
    consume_literal!(parser, ")")
    _t1801 = Proto.Loop(init=init1030, body=script1031)
    result1033 = _t1801
    record_span!(parser, span_start1032, "Loop")
    return result1033
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1034 = Proto.Instruction[]
    cond1035 = match_lookahead_literal(parser, "(", 0)
    while cond1035
        _t1802 = parse_instruction(parser)
        item1036 = _t1802
        push!(xs1034, item1036)
        cond1035 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1037 = xs1034
    consume_literal!(parser, ")")
    return instructions1037
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1044 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1804 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1805 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1806 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1807 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1808 = 0
                        else
                            _t1808 = -1
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
    else
        _t1803 = -1
    end
    prediction1038 = _t1803
    if prediction1038 == 4
        _t1810 = parse_monus_def(parser)
        monus_def1043 = _t1810
        _t1811 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1043))
        _t1809 = _t1811
    else
        if prediction1038 == 3
            _t1813 = parse_monoid_def(parser)
            monoid_def1042 = _t1813
            _t1814 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1042))
            _t1812 = _t1814
        else
            if prediction1038 == 2
                _t1816 = parse_break(parser)
                break1041 = _t1816
                _t1817 = Proto.Instruction(instr_type=OneOf(:var"#break", break1041))
                _t1815 = _t1817
            else
                if prediction1038 == 1
                    _t1819 = parse_upsert(parser)
                    upsert1040 = _t1819
                    _t1820 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1040))
                    _t1818 = _t1820
                else
                    if prediction1038 == 0
                        _t1822 = parse_assign(parser)
                        assign1039 = _t1822
                        _t1823 = Proto.Instruction(instr_type=OneOf(:assign, assign1039))
                        _t1821 = _t1823
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1818 = _t1821
                end
                _t1815 = _t1818
            end
            _t1812 = _t1815
        end
        _t1809 = _t1812
    end
    result1045 = _t1809
    record_span!(parser, span_start1044, "Instruction")
    return result1045
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1049 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1824 = parse_relation_id(parser)
    relation_id1046 = _t1824
    _t1825 = parse_abstraction(parser)
    abstraction1047 = _t1825
    if match_lookahead_literal(parser, "(", 0)
        _t1827 = parse_attrs(parser)
        _t1826 = _t1827
    else
        _t1826 = nothing
    end
    attrs1048 = _t1826
    consume_literal!(parser, ")")
    _t1828 = Proto.Assign(name=relation_id1046, body=abstraction1047, attrs=(!isnothing(attrs1048) ? attrs1048 : Proto.Attribute[]))
    result1050 = _t1828
    record_span!(parser, span_start1049, "Assign")
    return result1050
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1054 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1829 = parse_relation_id(parser)
    relation_id1051 = _t1829
    _t1830 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1052 = _t1830
    if match_lookahead_literal(parser, "(", 0)
        _t1832 = parse_attrs(parser)
        _t1831 = _t1832
    else
        _t1831 = nothing
    end
    attrs1053 = _t1831
    consume_literal!(parser, ")")
    _t1833 = Proto.Upsert(name=relation_id1051, body=abstraction_with_arity1052[1], attrs=(!isnothing(attrs1053) ? attrs1053 : Proto.Attribute[]), value_arity=abstraction_with_arity1052[2])
    result1055 = _t1833
    record_span!(parser, span_start1054, "Upsert")
    return result1055
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1834 = parse_bindings(parser)
    bindings1056 = _t1834
    _t1835 = parse_formula(parser)
    formula1057 = _t1835
    consume_literal!(parser, ")")
    _t1836 = Proto.Abstraction(vars=vcat(bindings1056[1], !isnothing(bindings1056[2]) ? bindings1056[2] : []), value=formula1057)
    return (_t1836, length(bindings1056[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1061 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1837 = parse_relation_id(parser)
    relation_id1058 = _t1837
    _t1838 = parse_abstraction(parser)
    abstraction1059 = _t1838
    if match_lookahead_literal(parser, "(", 0)
        _t1840 = parse_attrs(parser)
        _t1839 = _t1840
    else
        _t1839 = nothing
    end
    attrs1060 = _t1839
    consume_literal!(parser, ")")
    _t1841 = Proto.Break(name=relation_id1058, body=abstraction1059, attrs=(!isnothing(attrs1060) ? attrs1060 : Proto.Attribute[]))
    result1062 = _t1841
    record_span!(parser, span_start1061, "Break")
    return result1062
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1067 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1842 = parse_monoid(parser)
    monoid1063 = _t1842
    _t1843 = parse_relation_id(parser)
    relation_id1064 = _t1843
    _t1844 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1065 = _t1844
    if match_lookahead_literal(parser, "(", 0)
        _t1846 = parse_attrs(parser)
        _t1845 = _t1846
    else
        _t1845 = nothing
    end
    attrs1066 = _t1845
    consume_literal!(parser, ")")
    _t1847 = Proto.MonoidDef(monoid=monoid1063, name=relation_id1064, body=abstraction_with_arity1065[1], attrs=(!isnothing(attrs1066) ? attrs1066 : Proto.Attribute[]), value_arity=abstraction_with_arity1065[2])
    result1068 = _t1847
    record_span!(parser, span_start1067, "MonoidDef")
    return result1068
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1074 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1849 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1850 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1851 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1852 = 2
                    else
                        _t1852 = -1
                    end
                    _t1851 = _t1852
                end
                _t1850 = _t1851
            end
            _t1849 = _t1850
        end
        _t1848 = _t1849
    else
        _t1848 = -1
    end
    prediction1069 = _t1848
    if prediction1069 == 3
        _t1854 = parse_sum_monoid(parser)
        sum_monoid1073 = _t1854
        _t1855 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1073))
        _t1853 = _t1855
    else
        if prediction1069 == 2
            _t1857 = parse_max_monoid(parser)
            max_monoid1072 = _t1857
            _t1858 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1072))
            _t1856 = _t1858
        else
            if prediction1069 == 1
                _t1860 = parse_min_monoid(parser)
                min_monoid1071 = _t1860
                _t1861 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1071))
                _t1859 = _t1861
            else
                if prediction1069 == 0
                    _t1863 = parse_or_monoid(parser)
                    or_monoid1070 = _t1863
                    _t1864 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1070))
                    _t1862 = _t1864
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1859 = _t1862
            end
            _t1856 = _t1859
        end
        _t1853 = _t1856
    end
    result1075 = _t1853
    record_span!(parser, span_start1074, "Monoid")
    return result1075
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1076 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1865 = Proto.OrMonoid()
    result1077 = _t1865
    record_span!(parser, span_start1076, "OrMonoid")
    return result1077
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1079 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1866 = parse_type(parser)
    type1078 = _t1866
    consume_literal!(parser, ")")
    _t1867 = Proto.MinMonoid(var"#type"=type1078)
    result1080 = _t1867
    record_span!(parser, span_start1079, "MinMonoid")
    return result1080
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1082 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1868 = parse_type(parser)
    type1081 = _t1868
    consume_literal!(parser, ")")
    _t1869 = Proto.MaxMonoid(var"#type"=type1081)
    result1083 = _t1869
    record_span!(parser, span_start1082, "MaxMonoid")
    return result1083
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1085 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1870 = parse_type(parser)
    type1084 = _t1870
    consume_literal!(parser, ")")
    _t1871 = Proto.SumMonoid(var"#type"=type1084)
    result1086 = _t1871
    record_span!(parser, span_start1085, "SumMonoid")
    return result1086
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1091 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1872 = parse_monoid(parser)
    monoid1087 = _t1872
    _t1873 = parse_relation_id(parser)
    relation_id1088 = _t1873
    _t1874 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1089 = _t1874
    if match_lookahead_literal(parser, "(", 0)
        _t1876 = parse_attrs(parser)
        _t1875 = _t1876
    else
        _t1875 = nothing
    end
    attrs1090 = _t1875
    consume_literal!(parser, ")")
    _t1877 = Proto.MonusDef(monoid=monoid1087, name=relation_id1088, body=abstraction_with_arity1089[1], attrs=(!isnothing(attrs1090) ? attrs1090 : Proto.Attribute[]), value_arity=abstraction_with_arity1089[2])
    result1092 = _t1877
    record_span!(parser, span_start1091, "MonusDef")
    return result1092
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1097 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1878 = parse_relation_id(parser)
    relation_id1093 = _t1878
    _t1879 = parse_abstraction(parser)
    abstraction1094 = _t1879
    _t1880 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1095 = _t1880
    _t1881 = parse_functional_dependency_values(parser)
    functional_dependency_values1096 = _t1881
    consume_literal!(parser, ")")
    _t1882 = Proto.FunctionalDependency(guard=abstraction1094, keys=functional_dependency_keys1095, values=functional_dependency_values1096)
    _t1883 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1882), name=relation_id1093)
    result1098 = _t1883
    record_span!(parser, span_start1097, "Constraint")
    return result1098
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1099 = Proto.Var[]
    cond1100 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1100
        _t1884 = parse_var(parser)
        item1101 = _t1884
        push!(xs1099, item1101)
        cond1100 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1102 = xs1099
    consume_literal!(parser, ")")
    return vars1102
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1103 = Proto.Var[]
    cond1104 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1104
        _t1885 = parse_var(parser)
        item1105 = _t1885
        push!(xs1103, item1105)
        cond1104 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1106 = xs1103
    consume_literal!(parser, ")")
    return vars1106
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1112 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "iceberg_data", 1)
            _t1887 = 3
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1888 = 0
            else
                if match_lookahead_literal(parser, "csv_data", 1)
                    _t1889 = 2
                else
                    if match_lookahead_literal(parser, "betree_relation", 1)
                        _t1890 = 1
                    else
                        _t1890 = -1
                    end
                    _t1889 = _t1890
                end
                _t1888 = _t1889
            end
            _t1887 = _t1888
        end
        _t1886 = _t1887
    else
        _t1886 = -1
    end
    prediction1107 = _t1886
    if prediction1107 == 3
        _t1892 = parse_iceberg_data(parser)
        iceberg_data1111 = _t1892
        _t1893 = Proto.Data(data_type=OneOf(:iceberg_data, iceberg_data1111))
        _t1891 = _t1893
    else
        if prediction1107 == 2
            _t1895 = parse_csv_data(parser)
            csv_data1110 = _t1895
            _t1896 = Proto.Data(data_type=OneOf(:csv_data, csv_data1110))
            _t1894 = _t1896
        else
            if prediction1107 == 1
                _t1898 = parse_betree_relation(parser)
                betree_relation1109 = _t1898
                _t1899 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1109))
                _t1897 = _t1899
            else
                if prediction1107 == 0
                    _t1901 = parse_edb(parser)
                    edb1108 = _t1901
                    _t1902 = Proto.Data(data_type=OneOf(:edb, edb1108))
                    _t1900 = _t1902
                else
                    throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
                end
                _t1897 = _t1900
            end
            _t1894 = _t1897
        end
        _t1891 = _t1894
    end
    result1113 = _t1891
    record_span!(parser, span_start1112, "Data")
    return result1113
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1117 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1903 = parse_relation_id(parser)
    relation_id1114 = _t1903
    _t1904 = parse_edb_path(parser)
    edb_path1115 = _t1904
    _t1905 = parse_edb_types(parser)
    edb_types1116 = _t1905
    consume_literal!(parser, ")")
    _t1906 = Proto.EDB(target_id=relation_id1114, path=edb_path1115, types=edb_types1116)
    result1118 = _t1906
    record_span!(parser, span_start1117, "EDB")
    return result1118
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1119 = String[]
    cond1120 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1120
        item1121 = consume_terminal!(parser, "STRING")
        push!(xs1119, item1121)
        cond1120 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1122 = xs1119
    consume_literal!(parser, "]")
    return strings1122
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1123 = Proto.var"#Type"[]
    cond1124 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1124
        _t1907 = parse_type(parser)
        item1125 = _t1907
        push!(xs1123, item1125)
        cond1124 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1126 = xs1123
    consume_literal!(parser, "]")
    return types1126
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1129 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1908 = parse_relation_id(parser)
    relation_id1127 = _t1908
    _t1909 = parse_betree_info(parser)
    betree_info1128 = _t1909
    consume_literal!(parser, ")")
    _t1910 = Proto.BeTreeRelation(name=relation_id1127, relation_info=betree_info1128)
    result1130 = _t1910
    record_span!(parser, span_start1129, "BeTreeRelation")
    return result1130
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1134 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1911 = parse_betree_info_key_types(parser)
    betree_info_key_types1131 = _t1911
    _t1912 = parse_betree_info_value_types(parser)
    betree_info_value_types1132 = _t1912
    _t1913 = parse_config_dict(parser)
    config_dict1133 = _t1913
    consume_literal!(parser, ")")
    _t1914 = construct_betree_info(parser, betree_info_key_types1131, betree_info_value_types1132, config_dict1133)
    result1135 = _t1914
    record_span!(parser, span_start1134, "BeTreeInfo")
    return result1135
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1136 = Proto.var"#Type"[]
    cond1137 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1137
        _t1915 = parse_type(parser)
        item1138 = _t1915
        push!(xs1136, item1138)
        cond1137 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1139 = xs1136
    consume_literal!(parser, ")")
    return types1139
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1140 = Proto.var"#Type"[]
    cond1141 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1141
        _t1916 = parse_type(parser)
        item1142 = _t1916
        push!(xs1140, item1142)
        cond1141 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1143 = xs1140
    consume_literal!(parser, ")")
    return types1143
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1148 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1917 = parse_csvlocator(parser)
    csvlocator1144 = _t1917
    _t1918 = parse_csv_config(parser)
    csv_config1145 = _t1918
    _t1919 = parse_gnf_columns(parser)
    gnf_columns1146 = _t1919
    _t1920 = parse_csv_asof(parser)
    csv_asof1147 = _t1920
    consume_literal!(parser, ")")
    _t1921 = Proto.CSVData(locator=csvlocator1144, config=csv_config1145, columns=gnf_columns1146, asof=csv_asof1147)
    result1149 = _t1921
    record_span!(parser, span_start1148, "CSVData")
    return result1149
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1152 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1923 = parse_csv_locator_paths(parser)
        _t1922 = _t1923
    else
        _t1922 = nothing
    end
    csv_locator_paths1150 = _t1922
    if match_lookahead_literal(parser, "(", 0)
        _t1925 = parse_csv_locator_inline_data(parser)
        _t1924 = _t1925
    else
        _t1924 = nothing
    end
    csv_locator_inline_data1151 = _t1924
    consume_literal!(parser, ")")
    _t1926 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1150) ? csv_locator_paths1150 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1151) ? csv_locator_inline_data1151 : "")))
    result1153 = _t1926
    record_span!(parser, span_start1152, "CSVLocator")
    return result1153
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1154 = String[]
    cond1155 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1155
        item1156 = consume_terminal!(parser, "STRING")
        push!(xs1154, item1156)
        cond1155 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1157 = xs1154
    consume_literal!(parser, ")")
    return strings1157
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1158 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1158
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1160 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1927 = parse_config_dict(parser)
    config_dict1159 = _t1927
    consume_literal!(parser, ")")
    _t1928 = construct_csv_config(parser, config_dict1159)
    result1161 = _t1928
    record_span!(parser, span_start1160, "CSVConfig")
    return result1161
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1162 = Proto.GNFColumn[]
    cond1163 = match_lookahead_literal(parser, "(", 0)
    while cond1163
        _t1929 = parse_gnf_column(parser)
        item1164 = _t1929
        push!(xs1162, item1164)
        cond1163 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1165 = xs1162
    consume_literal!(parser, ")")
    return gnf_columns1165
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1172 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1930 = parse_gnf_column_path(parser)
    gnf_column_path1166 = _t1930
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1932 = parse_relation_id(parser)
        _t1931 = _t1932
    else
        _t1931 = nothing
    end
    relation_id1167 = _t1931
    consume_literal!(parser, "[")
    xs1168 = Proto.var"#Type"[]
    cond1169 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1169
        _t1933 = parse_type(parser)
        item1170 = _t1933
        push!(xs1168, item1170)
        cond1169 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1171 = xs1168
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1934 = Proto.GNFColumn(column_path=gnf_column_path1166, target_id=relation_id1167, types=types1171)
    result1173 = _t1934
    record_span!(parser, span_start1172, "GNFColumn")
    return result1173
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1935 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1936 = 0
        else
            _t1936 = -1
        end
        _t1935 = _t1936
    end
    prediction1174 = _t1935
    if prediction1174 == 1
        consume_literal!(parser, "[")
        xs1176 = String[]
        cond1177 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1177
            item1178 = consume_terminal!(parser, "STRING")
            push!(xs1176, item1178)
            cond1177 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1179 = xs1176
        consume_literal!(parser, "]")
        _t1937 = strings1179
    else
        if prediction1174 == 0
            string1175 = consume_terminal!(parser, "STRING")
            _t1938 = String[string1175]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1937 = _t1938
    end
    return _t1937
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1180 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1180
end

function parse_iceberg_data(parser::ParserState)::Proto.IcebergData
    span_start1185 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_data")
    _t1939 = parse_iceberg_locator(parser)
    iceberg_locator1181 = _t1939
    _t1940 = parse_iceberg_config(parser)
    iceberg_config1182 = _t1940
    _t1941 = parse_gnf_columns(parser)
    gnf_columns1183 = _t1941
    if match_lookahead_literal(parser, "(", 0)
        _t1943 = parse_iceberg_to_snapshot(parser)
        _t1942 = _t1943
    else
        _t1942 = nothing
    end
    iceberg_to_snapshot1184 = _t1942
    consume_literal!(parser, ")")
    _t1944 = Proto.IcebergData(locator=iceberg_locator1181, config=iceberg_config1182, columns=gnf_columns1183, to_snapshot=(!isnothing(iceberg_to_snapshot1184) ? iceberg_to_snapshot1184 : ""))
    result1186 = _t1944
    record_span!(parser, span_start1185, "IcebergData")
    return result1186
end

function parse_iceberg_locator(parser::ParserState)::Proto.IcebergLocator
    span_start1193 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_locator")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string1187 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1188 = String[]
    cond1189 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1189
        item1190 = consume_terminal!(parser, "STRING")
        push!(xs1188, item1190)
        cond1189 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1191 = xs1188
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string_121192 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1945 = Proto.IcebergLocator(table_name=string1187, namespace=strings1191, warehouse=string_121192)
    result1194 = _t1945
    record_span!(parser, span_start1193, "IcebergLocator")
    return result1194
end

function parse_iceberg_config(parser::ParserState)::Proto.IcebergConfig
    span_start1205 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_config")
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1195 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "scope", 1))
        _t1947 = parse_iceberg_config_scope(parser)
        _t1946 = _t1947
    else
        _t1946 = nothing
    end
    iceberg_config_scope1196 = _t1946
    consume_literal!(parser, "(")
    consume_literal!(parser, "properties")
    xs1197 = Tuple{String, String}[]
    cond1198 = match_lookahead_literal(parser, "(", 0)
    while cond1198
        _t1948 = parse_iceberg_property_entry(parser)
        item1199 = _t1948
        push!(xs1197, item1199)
        cond1198 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys1200 = xs1197
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "auth_properties")
    xs1201 = Tuple{String, String}[]
    cond1202 = match_lookahead_literal(parser, "(", 0)
    while cond1202
        _t1949 = parse_iceberg_property_entry(parser)
        item1203 = _t1949
        push!(xs1201, item1203)
        cond1202 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_property_entrys_131204 = xs1201
    consume_literal!(parser, ")")
    consume_literal!(parser, ")")
    _t1950 = construct_iceberg_config(parser, string1195, iceberg_config_scope1196, iceberg_property_entrys1200, iceberg_property_entrys_131204)
    result1206 = _t1950
    record_span!(parser, span_start1205, "IcebergConfig")
    return result1206
end

function parse_iceberg_config_scope(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "scope")
    string1207 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1207
end

function parse_iceberg_property_entry(parser::ParserState)::Tuple{String, String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "prop")
    string1208 = consume_terminal!(parser, "STRING")
    string_31209 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return (string1208, string_31209,)
end

function parse_iceberg_to_snapshot(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "to_snapshot")
    string1210 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1210
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1212 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1951 = parse_fragment_id(parser)
    fragment_id1211 = _t1951
    consume_literal!(parser, ")")
    _t1952 = Proto.Undefine(fragment_id=fragment_id1211)
    result1213 = _t1952
    record_span!(parser, span_start1212, "Undefine")
    return result1213
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1218 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1214 = Proto.RelationId[]
    cond1215 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1215
        _t1953 = parse_relation_id(parser)
        item1216 = _t1953
        push!(xs1214, item1216)
        cond1215 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1217 = xs1214
    consume_literal!(parser, ")")
    _t1954 = Proto.Context(relations=relation_ids1217)
    result1219 = _t1954
    record_span!(parser, span_start1218, "Context")
    return result1219
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1224 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1220 = Proto.SnapshotMapping[]
    cond1221 = match_lookahead_literal(parser, "[", 0)
    while cond1221
        _t1955 = parse_snapshot_mapping(parser)
        item1222 = _t1955
        push!(xs1220, item1222)
        cond1221 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1223 = xs1220
    consume_literal!(parser, ")")
    _t1956 = Proto.Snapshot(mappings=snapshot_mappings1223)
    result1225 = _t1956
    record_span!(parser, span_start1224, "Snapshot")
    return result1225
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1228 = span_start(parser)
    _t1957 = parse_edb_path(parser)
    edb_path1226 = _t1957
    _t1958 = parse_relation_id(parser)
    relation_id1227 = _t1958
    _t1959 = Proto.SnapshotMapping(destination_path=edb_path1226, source_relation=relation_id1227)
    result1229 = _t1959
    record_span!(parser, span_start1228, "SnapshotMapping")
    return result1229
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1230 = Proto.Read[]
    cond1231 = match_lookahead_literal(parser, "(", 0)
    while cond1231
        _t1960 = parse_read(parser)
        item1232 = _t1960
        push!(xs1230, item1232)
        cond1231 = match_lookahead_literal(parser, "(", 0)
    end
    reads1233 = xs1230
    consume_literal!(parser, ")")
    return reads1233
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1240 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1962 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1963 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t1964 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t1965 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t1966 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t1967 = 3
                            else
                                _t1967 = -1
                            end
                            _t1966 = _t1967
                        end
                        _t1965 = _t1966
                    end
                    _t1964 = _t1965
                end
                _t1963 = _t1964
            end
            _t1962 = _t1963
        end
        _t1961 = _t1962
    else
        _t1961 = -1
    end
    prediction1234 = _t1961
    if prediction1234 == 4
        _t1969 = parse_export(parser)
        export1239 = _t1969
        _t1970 = Proto.Read(read_type=OneOf(:var"#export", export1239))
        _t1968 = _t1970
    else
        if prediction1234 == 3
            _t1972 = parse_abort(parser)
            abort1238 = _t1972
            _t1973 = Proto.Read(read_type=OneOf(:abort, abort1238))
            _t1971 = _t1973
        else
            if prediction1234 == 2
                _t1975 = parse_what_if(parser)
                what_if1237 = _t1975
                _t1976 = Proto.Read(read_type=OneOf(:what_if, what_if1237))
                _t1974 = _t1976
            else
                if prediction1234 == 1
                    _t1978 = parse_output(parser)
                    output1236 = _t1978
                    _t1979 = Proto.Read(read_type=OneOf(:output, output1236))
                    _t1977 = _t1979
                else
                    if prediction1234 == 0
                        _t1981 = parse_demand(parser)
                        demand1235 = _t1981
                        _t1982 = Proto.Read(read_type=OneOf(:demand, demand1235))
                        _t1980 = _t1982
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1977 = _t1980
                end
                _t1974 = _t1977
            end
            _t1971 = _t1974
        end
        _t1968 = _t1971
    end
    result1241 = _t1968
    record_span!(parser, span_start1240, "Read")
    return result1241
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1243 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1983 = parse_relation_id(parser)
    relation_id1242 = _t1983
    consume_literal!(parser, ")")
    _t1984 = Proto.Demand(relation_id=relation_id1242)
    result1244 = _t1984
    record_span!(parser, span_start1243, "Demand")
    return result1244
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1247 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1985 = parse_name(parser)
    name1245 = _t1985
    _t1986 = parse_relation_id(parser)
    relation_id1246 = _t1986
    consume_literal!(parser, ")")
    _t1987 = Proto.Output(name=name1245, relation_id=relation_id1246)
    result1248 = _t1987
    record_span!(parser, span_start1247, "Output")
    return result1248
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1251 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1988 = parse_name(parser)
    name1249 = _t1988
    _t1989 = parse_epoch(parser)
    epoch1250 = _t1989
    consume_literal!(parser, ")")
    _t1990 = Proto.WhatIf(branch=name1249, epoch=epoch1250)
    result1252 = _t1990
    record_span!(parser, span_start1251, "WhatIf")
    return result1252
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1255 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1992 = parse_name(parser)
        _t1991 = _t1992
    else
        _t1991 = nothing
    end
    name1253 = _t1991
    _t1993 = parse_relation_id(parser)
    relation_id1254 = _t1993
    consume_literal!(parser, ")")
    _t1994 = Proto.Abort(name=(!isnothing(name1253) ? name1253 : "abort"), relation_id=relation_id1254)
    result1256 = _t1994
    record_span!(parser, span_start1255, "Abort")
    return result1256
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1260 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t1996 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t1997 = 0
            else
                _t1997 = -1
            end
            _t1996 = _t1997
        end
        _t1995 = _t1996
    else
        _t1995 = -1
    end
    prediction1257 = _t1995
    if prediction1257 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t1999 = parse_export_iceberg_config(parser)
        export_iceberg_config1259 = _t1999
        consume_literal!(parser, ")")
        _t2000 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1259))
        _t1998 = _t2000
    else
        if prediction1257 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t2002 = parse_export_csv_config(parser)
            export_csv_config1258 = _t2002
            consume_literal!(parser, ")")
            _t2003 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1258))
            _t2001 = _t2003
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t1998 = _t2001
    end
    result1261 = _t1998
    record_span!(parser, span_start1260, "Export")
    return result1261
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1269 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t2005 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t2006 = 1
            else
                _t2006 = -1
            end
            _t2005 = _t2006
        end
        _t2004 = _t2005
    else
        _t2004 = -1
    end
    prediction1262 = _t2004
    if prediction1262 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t2008 = parse_export_csv_path(parser)
        export_csv_path1266 = _t2008
        _t2009 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1267 = _t2009
        _t2010 = parse_config_dict(parser)
        config_dict1268 = _t2010
        consume_literal!(parser, ")")
        _t2011 = construct_export_csv_config(parser, export_csv_path1266, export_csv_columns_list1267, config_dict1268)
        _t2007 = _t2011
    else
        if prediction1262 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t2013 = parse_export_csv_path(parser)
            export_csv_path1263 = _t2013
            _t2014 = parse_export_csv_source(parser)
            export_csv_source1264 = _t2014
            _t2015 = parse_csv_config(parser)
            csv_config1265 = _t2015
            consume_literal!(parser, ")")
            _t2016 = construct_export_csv_config_with_source(parser, export_csv_path1263, export_csv_source1264, csv_config1265)
            _t2012 = _t2016
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t2007 = _t2012
    end
    result1270 = _t2007
    record_span!(parser, span_start1269, "ExportCSVConfig")
    return result1270
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1271 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1271
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1278 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t2018 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t2019 = 0
            else
                _t2019 = -1
            end
            _t2018 = _t2019
        end
        _t2017 = _t2018
    else
        _t2017 = -1
    end
    prediction1272 = _t2017
    if prediction1272 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t2021 = parse_relation_id(parser)
        relation_id1277 = _t2021
        consume_literal!(parser, ")")
        _t2022 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1277))
        _t2020 = _t2022
    else
        if prediction1272 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1273 = Proto.ExportCSVColumn[]
            cond1274 = match_lookahead_literal(parser, "(", 0)
            while cond1274
                _t2024 = parse_export_csv_column(parser)
                item1275 = _t2024
                push!(xs1273, item1275)
                cond1274 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1276 = xs1273
            consume_literal!(parser, ")")
            _t2025 = Proto.ExportCSVColumns(columns=export_csv_columns1276)
            _t2026 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t2025))
            _t2023 = _t2026
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t2020 = _t2023
    end
    result1279 = _t2020
    record_span!(parser, span_start1278, "ExportCSVSource")
    return result1279
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1282 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1280 = consume_terminal!(parser, "STRING")
    _t2027 = parse_relation_id(parser)
    relation_id1281 = _t2027
    consume_literal!(parser, ")")
    _t2028 = Proto.ExportCSVColumn(column_name=string1280, column_data=relation_id1281)
    result1283 = _t2028
    record_span!(parser, span_start1282, "ExportCSVColumn")
    return result1283
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1284 = Proto.ExportCSVColumn[]
    cond1285 = match_lookahead_literal(parser, "(", 0)
    while cond1285
        _t2029 = parse_export_csv_column(parser)
        item1286 = _t2029
        push!(xs1284, item1286)
        cond1285 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1287 = xs1284
    consume_literal!(parser, ")")
    return export_csv_columns1287
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1295 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    _t2030 = parse_iceberg_locator(parser)
    iceberg_locator1288 = _t2030
    _t2031 = parse_iceberg_config(parser)
    iceberg_config1289 = _t2031
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1290 = Proto.IcebergExportColumn[]
    cond1291 = match_lookahead_literal(parser, "(", 0)
    while cond1291
        _t2032 = parse_iceberg_export_column(parser)
        item1292 = _t2032
        push!(xs1290, item1292)
        cond1291 = match_lookahead_literal(parser, "(", 0)
    end
    iceberg_export_columns1293 = xs1290
    consume_literal!(parser, ")")
    if match_lookahead_literal(parser, "{", 0)
        _t2034 = parse_config_dict(parser)
        _t2033 = _t2034
    else
        _t2033 = nothing
    end
    config_dict1294 = _t2033
    consume_literal!(parser, ")")
    _t2035 = construct_export_iceberg_config_full(parser, iceberg_locator1288, iceberg_config1289, iceberg_export_columns1293, config_dict1294)
    result1296 = _t2035
    record_span!(parser, span_start1295, "ExportIcebergConfig")
    return result1296
end

function parse_iceberg_export_column(parser::ParserState)::Proto.IcebergExportColumn
    span_start1300 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "iceberg_column")
    string1297 = consume_terminal!(parser, "STRING")
    _t2036 = parse_type(parser)
    type1298 = _t2036
    _t2037 = parse_boolean_value(parser)
    boolean_value1299 = _t2037
    consume_literal!(parser, ")")
    _t2038 = Proto.IcebergExportColumn(name=string1297, var"#type"=type1298, nullable=boolean_value1299)
    result1301 = _t2038
    record_span!(parser, span_start1300, "IcebergExportColumn")
    return result1301
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
