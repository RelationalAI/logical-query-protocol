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
        _t1960 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1961 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1962 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1963 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1964 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1965 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1966 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1967 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1968 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1969 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1969
    _t1970 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1970
    _t1971 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1971
    _t1972 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1972
    _t1973 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1973
    _t1974 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1974
    _t1975 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1975
    _t1976 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1976
    _t1977 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1977
    _t1978 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1978
    _t1979 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1979
    _t1980 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t1980
    _t1981 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t1981
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1982 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1982
    _t1983 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1983
    _t1984 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1984
    _t1985 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1985
    _t1986 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1986
    _t1987 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1987
    _t1988 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1988
    _t1989 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1989
    _t1990 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1990
    _t1991 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1991
    _t1992 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1992
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1993 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1993
    _t1994 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1994
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
    _t1995 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1995
    _t1996 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1996
    _t1997 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1997
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1998 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1998
    _t1999 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1999
    _t2000 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t2000
    _t2001 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t2001
    _t2002 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t2002
    _t2003 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t2003
    _t2004 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t2004
    _t2005 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t2005
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t2006 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t2006
end

function construct_export_iceberg_config_from_optional(parser::ParserState, catalog_uri::String, namespace::Vector{String}, table_name::String, catalog_properties::Proto.IcebergCatalogProperties, schema::String, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.ExportIcebergConfig
    prefix = ""
    _t2007 = _extract_value_int64(parser, nothing, 0)
    target_file_size_bytes = _t2007
    compression = ""
    if !isnothing(config_dict)
        config = Dict(config_dict)
        _t2008 = _extract_value_string(parser, get(config, "prefix", nothing), "")
        prefix = _t2008
        _t2009 = _extract_value_int64(parser, get(config, "target_file_size_bytes", nothing), 0)
        target_file_size_bytes = _t2009
        _t2010 = _extract_value_string(parser, get(config, "compression", nothing), "")
        compression = _t2010
    end
    _t2011 = Proto.ExportIcebergConfig(catalog_uri=catalog_uri, namespace=namespace, table_name=table_name, catalog_properties=catalog_properties, schema=schema, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression)
    return _t2011
end

function construct_iceberg_catalog_properties_from_optional(parser::ParserState, warehouse::String, config_dict::Union{Nothing, Vector{Tuple{String, Proto.Value}}})::Proto.IcebergCatalogProperties
    token = ""
    credential = ""
    if !isnothing(config_dict)
        config = Dict(config_dict)
        _t2012 = _extract_value_string(parser, get(config, "token", nothing), "")
        token = _t2012
        _t2013 = _extract_value_string(parser, get(config, "credential", nothing), "")
        credential = _t2013
    end
    _t2014 = Proto.IcebergCatalogProperties(warehouse=warehouse, token=token, credential=credential)
    return _t2014
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start627 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1243 = parse_configure(parser)
        _t1242 = _t1243
    else
        _t1242 = nothing
    end
    configure621 = _t1242
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1245 = parse_sync(parser)
        _t1244 = _t1245
    else
        _t1244 = nothing
    end
    sync622 = _t1244
    xs623 = Proto.Epoch[]
    cond624 = match_lookahead_literal(parser, "(", 0)
    while cond624
        _t1246 = parse_epoch(parser)
        item625 = _t1246
        push!(xs623, item625)
        cond624 = match_lookahead_literal(parser, "(", 0)
    end
    epochs626 = xs623
    consume_literal!(parser, ")")
    _t1247 = default_configure(parser)
    _t1248 = Proto.Transaction(epochs=epochs626, configure=(!isnothing(configure621) ? configure621 : _t1247), sync=sync622)
    result628 = _t1248
    record_span!(parser, span_start627, "Transaction")
    return result628
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start630 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1249 = parse_config_dict(parser)
    config_dict629 = _t1249
    consume_literal!(parser, ")")
    _t1250 = construct_configure(parser, config_dict629)
    result631 = _t1250
    record_span!(parser, span_start630, "Configure")
    return result631
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs632 = Tuple{String, Proto.Value}[]
    cond633 = match_lookahead_literal(parser, ":", 0)
    while cond633
        _t1251 = parse_config_key_value(parser)
        item634 = _t1251
        push!(xs632, item634)
        cond633 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values635 = xs632
    consume_literal!(parser, "}")
    return config_key_values635
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol636 = consume_terminal!(parser, "SYMBOL")
    _t1252 = parse_raw_value(parser)
    raw_value637 = _t1252
    return (symbol636, raw_value637,)
end

function parse_raw_value(parser::ParserState)::Proto.Value
    span_start651 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1253 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1254 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1255 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1257 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1258 = 0
                        else
                            _t1258 = -1
                        end
                        _t1257 = _t1258
                    end
                    _t1256 = _t1257
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1259 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1260 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1261 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1262 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1263 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1264 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1265 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1266 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1267 = 10
                                                    else
                                                        _t1267 = -1
                                                    end
                                                    _t1266 = _t1267
                                                end
                                                _t1265 = _t1266
                                            end
                                            _t1264 = _t1265
                                        end
                                        _t1263 = _t1264
                                    end
                                    _t1262 = _t1263
                                end
                                _t1261 = _t1262
                            end
                            _t1260 = _t1261
                        end
                        _t1259 = _t1260
                    end
                    _t1256 = _t1259
                end
                _t1255 = _t1256
            end
            _t1254 = _t1255
        end
        _t1253 = _t1254
    end
    prediction638 = _t1253
    if prediction638 == 12
        _t1269 = parse_boolean_value(parser)
        boolean_value650 = _t1269
        _t1270 = Proto.Value(value=OneOf(:boolean_value, boolean_value650))
        _t1268 = _t1270
    else
        if prediction638 == 11
            consume_literal!(parser, "missing")
            _t1272 = Proto.MissingValue()
            _t1273 = Proto.Value(value=OneOf(:missing_value, _t1272))
            _t1271 = _t1273
        else
            if prediction638 == 10
                decimal649 = consume_terminal!(parser, "DECIMAL")
                _t1275 = Proto.Value(value=OneOf(:decimal_value, decimal649))
                _t1274 = _t1275
            else
                if prediction638 == 9
                    int128648 = consume_terminal!(parser, "INT128")
                    _t1277 = Proto.Value(value=OneOf(:int128_value, int128648))
                    _t1276 = _t1277
                else
                    if prediction638 == 8
                        uint128647 = consume_terminal!(parser, "UINT128")
                        _t1279 = Proto.Value(value=OneOf(:uint128_value, uint128647))
                        _t1278 = _t1279
                    else
                        if prediction638 == 7
                            uint32646 = consume_terminal!(parser, "UINT32")
                            _t1281 = Proto.Value(value=OneOf(:uint32_value, uint32646))
                            _t1280 = _t1281
                        else
                            if prediction638 == 6
                                float645 = consume_terminal!(parser, "FLOAT")
                                _t1283 = Proto.Value(value=OneOf(:float_value, float645))
                                _t1282 = _t1283
                            else
                                if prediction638 == 5
                                    float32644 = consume_terminal!(parser, "FLOAT32")
                                    _t1285 = Proto.Value(value=OneOf(:float32_value, float32644))
                                    _t1284 = _t1285
                                else
                                    if prediction638 == 4
                                        int643 = consume_terminal!(parser, "INT")
                                        _t1287 = Proto.Value(value=OneOf(:int_value, int643))
                                        _t1286 = _t1287
                                    else
                                        if prediction638 == 3
                                            int32642 = consume_terminal!(parser, "INT32")
                                            _t1289 = Proto.Value(value=OneOf(:int32_value, int32642))
                                            _t1288 = _t1289
                                        else
                                            if prediction638 == 2
                                                string641 = consume_terminal!(parser, "STRING")
                                                _t1291 = Proto.Value(value=OneOf(:string_value, string641))
                                                _t1290 = _t1291
                                            else
                                                if prediction638 == 1
                                                    _t1293 = parse_raw_datetime(parser)
                                                    raw_datetime640 = _t1293
                                                    _t1294 = Proto.Value(value=OneOf(:datetime_value, raw_datetime640))
                                                    _t1292 = _t1294
                                                else
                                                    if prediction638 == 0
                                                        _t1296 = parse_raw_date(parser)
                                                        raw_date639 = _t1296
                                                        _t1297 = Proto.Value(value=OneOf(:date_value, raw_date639))
                                                        _t1295 = _t1297
                                                    else
                                                        throw(ParseError("Unexpected token in raw_value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1292 = _t1295
                                                end
                                                _t1290 = _t1292
                                            end
                                            _t1288 = _t1290
                                        end
                                        _t1286 = _t1288
                                    end
                                    _t1284 = _t1286
                                end
                                _t1282 = _t1284
                            end
                            _t1280 = _t1282
                        end
                        _t1278 = _t1280
                    end
                    _t1276 = _t1278
                end
                _t1274 = _t1276
            end
            _t1271 = _t1274
        end
        _t1268 = _t1271
    end
    result652 = _t1268
    record_span!(parser, span_start651, "Value")
    return result652
end

function parse_raw_date(parser::ParserState)::Proto.DateValue
    span_start656 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int653 = consume_terminal!(parser, "INT")
    int_3654 = consume_terminal!(parser, "INT")
    int_4655 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1298 = Proto.DateValue(year=Int32(int653), month=Int32(int_3654), day=Int32(int_4655))
    result657 = _t1298
    record_span!(parser, span_start656, "DateValue")
    return result657
end

function parse_raw_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start665 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int658 = consume_terminal!(parser, "INT")
    int_3659 = consume_terminal!(parser, "INT")
    int_4660 = consume_terminal!(parser, "INT")
    int_5661 = consume_terminal!(parser, "INT")
    int_6662 = consume_terminal!(parser, "INT")
    int_7663 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1299 = consume_terminal!(parser, "INT")
    else
        _t1299 = nothing
    end
    int_8664 = _t1299
    consume_literal!(parser, ")")
    _t1300 = Proto.DateTimeValue(year=Int32(int658), month=Int32(int_3659), day=Int32(int_4660), hour=Int32(int_5661), minute=Int32(int_6662), second=Int32(int_7663), microsecond=Int32((!isnothing(int_8664) ? int_8664 : 0)))
    result666 = _t1300
    record_span!(parser, span_start665, "DateTimeValue")
    return result666
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1301 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1302 = 1
        else
            _t1302 = -1
        end
        _t1301 = _t1302
    end
    prediction667 = _t1301
    if prediction667 == 1
        consume_literal!(parser, "false")
        _t1303 = false
    else
        if prediction667 == 0
            consume_literal!(parser, "true")
            _t1304 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1303 = _t1304
    end
    return _t1303
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start672 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs668 = Proto.FragmentId[]
    cond669 = match_lookahead_literal(parser, ":", 0)
    while cond669
        _t1305 = parse_fragment_id(parser)
        item670 = _t1305
        push!(xs668, item670)
        cond669 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids671 = xs668
    consume_literal!(parser, ")")
    _t1306 = Proto.Sync(fragments=fragment_ids671)
    result673 = _t1306
    record_span!(parser, span_start672, "Sync")
    return result673
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start675 = span_start(parser)
    consume_literal!(parser, ":")
    symbol674 = consume_terminal!(parser, "SYMBOL")
    result676 = Proto.FragmentId(Vector{UInt8}(symbol674))
    record_span!(parser, span_start675, "FragmentId")
    return result676
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start679 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1308 = parse_epoch_writes(parser)
        _t1307 = _t1308
    else
        _t1307 = nothing
    end
    epoch_writes677 = _t1307
    if match_lookahead_literal(parser, "(", 0)
        _t1310 = parse_epoch_reads(parser)
        _t1309 = _t1310
    else
        _t1309 = nothing
    end
    epoch_reads678 = _t1309
    consume_literal!(parser, ")")
    _t1311 = Proto.Epoch(writes=(!isnothing(epoch_writes677) ? epoch_writes677 : Proto.Write[]), reads=(!isnothing(epoch_reads678) ? epoch_reads678 : Proto.Read[]))
    result680 = _t1311
    record_span!(parser, span_start679, "Epoch")
    return result680
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs681 = Proto.Write[]
    cond682 = match_lookahead_literal(parser, "(", 0)
    while cond682
        _t1312 = parse_write(parser)
        item683 = _t1312
        push!(xs681, item683)
        cond682 = match_lookahead_literal(parser, "(", 0)
    end
    writes684 = xs681
    consume_literal!(parser, ")")
    return writes684
end

function parse_write(parser::ParserState)::Proto.Write
    span_start690 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1314 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1315 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1316 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1317 = 2
                    else
                        _t1317 = -1
                    end
                    _t1316 = _t1317
                end
                _t1315 = _t1316
            end
            _t1314 = _t1315
        end
        _t1313 = _t1314
    else
        _t1313 = -1
    end
    prediction685 = _t1313
    if prediction685 == 3
        _t1319 = parse_snapshot(parser)
        snapshot689 = _t1319
        _t1320 = Proto.Write(write_type=OneOf(:snapshot, snapshot689))
        _t1318 = _t1320
    else
        if prediction685 == 2
            _t1322 = parse_context(parser)
            context688 = _t1322
            _t1323 = Proto.Write(write_type=OneOf(:context, context688))
            _t1321 = _t1323
        else
            if prediction685 == 1
                _t1325 = parse_undefine(parser)
                undefine687 = _t1325
                _t1326 = Proto.Write(write_type=OneOf(:undefine, undefine687))
                _t1324 = _t1326
            else
                if prediction685 == 0
                    _t1328 = parse_define(parser)
                    define686 = _t1328
                    _t1329 = Proto.Write(write_type=OneOf(:define, define686))
                    _t1327 = _t1329
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1324 = _t1327
            end
            _t1321 = _t1324
        end
        _t1318 = _t1321
    end
    result691 = _t1318
    record_span!(parser, span_start690, "Write")
    return result691
end

function parse_define(parser::ParserState)::Proto.Define
    span_start693 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1330 = parse_fragment(parser)
    fragment692 = _t1330
    consume_literal!(parser, ")")
    _t1331 = Proto.Define(fragment=fragment692)
    result694 = _t1331
    record_span!(parser, span_start693, "Define")
    return result694
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start700 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1332 = parse_new_fragment_id(parser)
    new_fragment_id695 = _t1332
    xs696 = Proto.Declaration[]
    cond697 = match_lookahead_literal(parser, "(", 0)
    while cond697
        _t1333 = parse_declaration(parser)
        item698 = _t1333
        push!(xs696, item698)
        cond697 = match_lookahead_literal(parser, "(", 0)
    end
    declarations699 = xs696
    consume_literal!(parser, ")")
    result701 = construct_fragment(parser, new_fragment_id695, declarations699)
    record_span!(parser, span_start700, "Fragment")
    return result701
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start703 = span_start(parser)
    _t1334 = parse_fragment_id(parser)
    fragment_id702 = _t1334
    start_fragment!(parser, fragment_id702)
    result704 = fragment_id702
    record_span!(parser, span_start703, "FragmentId")
    return result704
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start710 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "functional_dependency", 1)
            _t1336 = 2
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1337 = 3
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1338 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1339 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1340 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1341 = 1
                            else
                                _t1341 = -1
                            end
                            _t1340 = _t1341
                        end
                        _t1339 = _t1340
                    end
                    _t1338 = _t1339
                end
                _t1337 = _t1338
            end
            _t1336 = _t1337
        end
        _t1335 = _t1336
    else
        _t1335 = -1
    end
    prediction705 = _t1335
    if prediction705 == 3
        _t1343 = parse_data(parser)
        data709 = _t1343
        _t1344 = Proto.Declaration(declaration_type=OneOf(:data, data709))
        _t1342 = _t1344
    else
        if prediction705 == 2
            _t1346 = parse_constraint(parser)
            constraint708 = _t1346
            _t1347 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint708))
            _t1345 = _t1347
        else
            if prediction705 == 1
                _t1349 = parse_algorithm(parser)
                algorithm707 = _t1349
                _t1350 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm707))
                _t1348 = _t1350
            else
                if prediction705 == 0
                    _t1352 = parse_def(parser)
                    def706 = _t1352
                    _t1353 = Proto.Declaration(declaration_type=OneOf(:def, def706))
                    _t1351 = _t1353
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1348 = _t1351
            end
            _t1345 = _t1348
        end
        _t1342 = _t1345
    end
    result711 = _t1342
    record_span!(parser, span_start710, "Declaration")
    return result711
end

function parse_def(parser::ParserState)::Proto.Def
    span_start715 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1354 = parse_relation_id(parser)
    relation_id712 = _t1354
    _t1355 = parse_abstraction(parser)
    abstraction713 = _t1355
    if match_lookahead_literal(parser, "(", 0)
        _t1357 = parse_attrs(parser)
        _t1356 = _t1357
    else
        _t1356 = nothing
    end
    attrs714 = _t1356
    consume_literal!(parser, ")")
    _t1358 = Proto.Def(name=relation_id712, body=abstraction713, attrs=(!isnothing(attrs714) ? attrs714 : Proto.Attribute[]))
    result716 = _t1358
    record_span!(parser, span_start715, "Def")
    return result716
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start720 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1359 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1360 = 1
        else
            _t1360 = -1
        end
        _t1359 = _t1360
    end
    prediction717 = _t1359
    if prediction717 == 1
        uint128719 = consume_terminal!(parser, "UINT128")
        _t1361 = Proto.RelationId(uint128719.low, uint128719.high)
    else
        if prediction717 == 0
            consume_literal!(parser, ":")
            symbol718 = consume_terminal!(parser, "SYMBOL")
            _t1362 = relation_id_from_string(parser, symbol718)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1361 = _t1362
    end
    result721 = _t1361
    record_span!(parser, span_start720, "RelationId")
    return result721
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start724 = span_start(parser)
    consume_literal!(parser, "(")
    _t1363 = parse_bindings(parser)
    bindings722 = _t1363
    _t1364 = parse_formula(parser)
    formula723 = _t1364
    consume_literal!(parser, ")")
    _t1365 = Proto.Abstraction(vars=vcat(bindings722[1], !isnothing(bindings722[2]) ? bindings722[2] : []), value=formula723)
    result725 = _t1365
    record_span!(parser, span_start724, "Abstraction")
    return result725
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs726 = Proto.Binding[]
    cond727 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond727
        _t1366 = parse_binding(parser)
        item728 = _t1366
        push!(xs726, item728)
        cond727 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings729 = xs726
    if match_lookahead_literal(parser, "|", 0)
        _t1368 = parse_value_bindings(parser)
        _t1367 = _t1368
    else
        _t1367 = nothing
    end
    value_bindings730 = _t1367
    consume_literal!(parser, "]")
    return (bindings729, (!isnothing(value_bindings730) ? value_bindings730 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start733 = span_start(parser)
    symbol731 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1369 = parse_type(parser)
    type732 = _t1369
    _t1370 = Proto.Var(name=symbol731)
    _t1371 = Proto.Binding(var=_t1370, var"#type"=type732)
    result734 = _t1371
    record_span!(parser, span_start733, "Binding")
    return result734
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start750 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1372 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1373 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1374 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1375 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1376 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1377 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1378 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1379 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1380 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1381 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1382 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1383 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1384 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1385 = 9
                                                        else
                                                            _t1385 = -1
                                                        end
                                                        _t1384 = _t1385
                                                    end
                                                    _t1383 = _t1384
                                                end
                                                _t1382 = _t1383
                                            end
                                            _t1381 = _t1382
                                        end
                                        _t1380 = _t1381
                                    end
                                    _t1379 = _t1380
                                end
                                _t1378 = _t1379
                            end
                            _t1377 = _t1378
                        end
                        _t1376 = _t1377
                    end
                    _t1375 = _t1376
                end
                _t1374 = _t1375
            end
            _t1373 = _t1374
        end
        _t1372 = _t1373
    end
    prediction735 = _t1372
    if prediction735 == 13
        _t1387 = parse_uint32_type(parser)
        uint32_type749 = _t1387
        _t1388 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type749))
        _t1386 = _t1388
    else
        if prediction735 == 12
            _t1390 = parse_float32_type(parser)
            float32_type748 = _t1390
            _t1391 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type748))
            _t1389 = _t1391
        else
            if prediction735 == 11
                _t1393 = parse_int32_type(parser)
                int32_type747 = _t1393
                _t1394 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type747))
                _t1392 = _t1394
            else
                if prediction735 == 10
                    _t1396 = parse_boolean_type(parser)
                    boolean_type746 = _t1396
                    _t1397 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type746))
                    _t1395 = _t1397
                else
                    if prediction735 == 9
                        _t1399 = parse_decimal_type(parser)
                        decimal_type745 = _t1399
                        _t1400 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type745))
                        _t1398 = _t1400
                    else
                        if prediction735 == 8
                            _t1402 = parse_missing_type(parser)
                            missing_type744 = _t1402
                            _t1403 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type744))
                            _t1401 = _t1403
                        else
                            if prediction735 == 7
                                _t1405 = parse_datetime_type(parser)
                                datetime_type743 = _t1405
                                _t1406 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type743))
                                _t1404 = _t1406
                            else
                                if prediction735 == 6
                                    _t1408 = parse_date_type(parser)
                                    date_type742 = _t1408
                                    _t1409 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type742))
                                    _t1407 = _t1409
                                else
                                    if prediction735 == 5
                                        _t1411 = parse_int128_type(parser)
                                        int128_type741 = _t1411
                                        _t1412 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type741))
                                        _t1410 = _t1412
                                    else
                                        if prediction735 == 4
                                            _t1414 = parse_uint128_type(parser)
                                            uint128_type740 = _t1414
                                            _t1415 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type740))
                                            _t1413 = _t1415
                                        else
                                            if prediction735 == 3
                                                _t1417 = parse_float_type(parser)
                                                float_type739 = _t1417
                                                _t1418 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type739))
                                                _t1416 = _t1418
                                            else
                                                if prediction735 == 2
                                                    _t1420 = parse_int_type(parser)
                                                    int_type738 = _t1420
                                                    _t1421 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type738))
                                                    _t1419 = _t1421
                                                else
                                                    if prediction735 == 1
                                                        _t1423 = parse_string_type(parser)
                                                        string_type737 = _t1423
                                                        _t1424 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type737))
                                                        _t1422 = _t1424
                                                    else
                                                        if prediction735 == 0
                                                            _t1426 = parse_unspecified_type(parser)
                                                            unspecified_type736 = _t1426
                                                            _t1427 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type736))
                                                            _t1425 = _t1427
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1422 = _t1425
                                                    end
                                                    _t1419 = _t1422
                                                end
                                                _t1416 = _t1419
                                            end
                                            _t1413 = _t1416
                                        end
                                        _t1410 = _t1413
                                    end
                                    _t1407 = _t1410
                                end
                                _t1404 = _t1407
                            end
                            _t1401 = _t1404
                        end
                        _t1398 = _t1401
                    end
                    _t1395 = _t1398
                end
                _t1392 = _t1395
            end
            _t1389 = _t1392
        end
        _t1386 = _t1389
    end
    result751 = _t1386
    record_span!(parser, span_start750, "Type")
    return result751
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start752 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1428 = Proto.UnspecifiedType()
    result753 = _t1428
    record_span!(parser, span_start752, "UnspecifiedType")
    return result753
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start754 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1429 = Proto.StringType()
    result755 = _t1429
    record_span!(parser, span_start754, "StringType")
    return result755
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start756 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1430 = Proto.IntType()
    result757 = _t1430
    record_span!(parser, span_start756, "IntType")
    return result757
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start758 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1431 = Proto.FloatType()
    result759 = _t1431
    record_span!(parser, span_start758, "FloatType")
    return result759
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start760 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1432 = Proto.UInt128Type()
    result761 = _t1432
    record_span!(parser, span_start760, "UInt128Type")
    return result761
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start762 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1433 = Proto.Int128Type()
    result763 = _t1433
    record_span!(parser, span_start762, "Int128Type")
    return result763
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start764 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1434 = Proto.DateType()
    result765 = _t1434
    record_span!(parser, span_start764, "DateType")
    return result765
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start766 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1435 = Proto.DateTimeType()
    result767 = _t1435
    record_span!(parser, span_start766, "DateTimeType")
    return result767
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start768 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1436 = Proto.MissingType()
    result769 = _t1436
    record_span!(parser, span_start768, "MissingType")
    return result769
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start772 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int770 = consume_terminal!(parser, "INT")
    int_3771 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1437 = Proto.DecimalType(precision=Int32(int770), scale=Int32(int_3771))
    result773 = _t1437
    record_span!(parser, span_start772, "DecimalType")
    return result773
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start774 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1438 = Proto.BooleanType()
    result775 = _t1438
    record_span!(parser, span_start774, "BooleanType")
    return result775
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start776 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1439 = Proto.Int32Type()
    result777 = _t1439
    record_span!(parser, span_start776, "Int32Type")
    return result777
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start778 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1440 = Proto.Float32Type()
    result779 = _t1440
    record_span!(parser, span_start778, "Float32Type")
    return result779
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start780 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1441 = Proto.UInt32Type()
    result781 = _t1441
    record_span!(parser, span_start780, "UInt32Type")
    return result781
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs782 = Proto.Binding[]
    cond783 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond783
        _t1442 = parse_binding(parser)
        item784 = _t1442
        push!(xs782, item784)
        cond783 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings785 = xs782
    return bindings785
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start800 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1444 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1445 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1446 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1447 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1448 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1449 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1450 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1451 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1452 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1453 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1454 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1455 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1456 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1457 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1458 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1459 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1460 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1461 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1462 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1463 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1464 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1465 = 10
                                                                                            else
                                                                                                _t1465 = -1
                                                                                            end
                                                                                            _t1464 = _t1465
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
    else
        _t1443 = -1
    end
    prediction786 = _t1443
    if prediction786 == 12
        _t1467 = parse_cast(parser)
        cast799 = _t1467
        _t1468 = Proto.Formula(formula_type=OneOf(:cast, cast799))
        _t1466 = _t1468
    else
        if prediction786 == 11
            _t1470 = parse_rel_atom(parser)
            rel_atom798 = _t1470
            _t1471 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom798))
            _t1469 = _t1471
        else
            if prediction786 == 10
                _t1473 = parse_primitive(parser)
                primitive797 = _t1473
                _t1474 = Proto.Formula(formula_type=OneOf(:primitive, primitive797))
                _t1472 = _t1474
            else
                if prediction786 == 9
                    _t1476 = parse_pragma(parser)
                    pragma796 = _t1476
                    _t1477 = Proto.Formula(formula_type=OneOf(:pragma, pragma796))
                    _t1475 = _t1477
                else
                    if prediction786 == 8
                        _t1479 = parse_atom(parser)
                        atom795 = _t1479
                        _t1480 = Proto.Formula(formula_type=OneOf(:atom, atom795))
                        _t1478 = _t1480
                    else
                        if prediction786 == 7
                            _t1482 = parse_ffi(parser)
                            ffi794 = _t1482
                            _t1483 = Proto.Formula(formula_type=OneOf(:ffi, ffi794))
                            _t1481 = _t1483
                        else
                            if prediction786 == 6
                                _t1485 = parse_not(parser)
                                not793 = _t1485
                                _t1486 = Proto.Formula(formula_type=OneOf(:not, not793))
                                _t1484 = _t1486
                            else
                                if prediction786 == 5
                                    _t1488 = parse_disjunction(parser)
                                    disjunction792 = _t1488
                                    _t1489 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction792))
                                    _t1487 = _t1489
                                else
                                    if prediction786 == 4
                                        _t1491 = parse_conjunction(parser)
                                        conjunction791 = _t1491
                                        _t1492 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction791))
                                        _t1490 = _t1492
                                    else
                                        if prediction786 == 3
                                            _t1494 = parse_reduce(parser)
                                            reduce790 = _t1494
                                            _t1495 = Proto.Formula(formula_type=OneOf(:reduce, reduce790))
                                            _t1493 = _t1495
                                        else
                                            if prediction786 == 2
                                                _t1497 = parse_exists(parser)
                                                exists789 = _t1497
                                                _t1498 = Proto.Formula(formula_type=OneOf(:exists, exists789))
                                                _t1496 = _t1498
                                            else
                                                if prediction786 == 1
                                                    _t1500 = parse_false(parser)
                                                    false788 = _t1500
                                                    _t1501 = Proto.Formula(formula_type=OneOf(:disjunction, false788))
                                                    _t1499 = _t1501
                                                else
                                                    if prediction786 == 0
                                                        _t1503 = parse_true(parser)
                                                        true787 = _t1503
                                                        _t1504 = Proto.Formula(formula_type=OneOf(:conjunction, true787))
                                                        _t1502 = _t1504
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
    result801 = _t1466
    record_span!(parser, span_start800, "Formula")
    return result801
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start802 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1505 = Proto.Conjunction(args=Proto.Formula[])
    result803 = _t1505
    record_span!(parser, span_start802, "Conjunction")
    return result803
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start804 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1506 = Proto.Disjunction(args=Proto.Formula[])
    result805 = _t1506
    record_span!(parser, span_start804, "Disjunction")
    return result805
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start808 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1507 = parse_bindings(parser)
    bindings806 = _t1507
    _t1508 = parse_formula(parser)
    formula807 = _t1508
    consume_literal!(parser, ")")
    _t1509 = Proto.Abstraction(vars=vcat(bindings806[1], !isnothing(bindings806[2]) ? bindings806[2] : []), value=formula807)
    _t1510 = Proto.Exists(body=_t1509)
    result809 = _t1510
    record_span!(parser, span_start808, "Exists")
    return result809
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start813 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1511 = parse_abstraction(parser)
    abstraction810 = _t1511
    _t1512 = parse_abstraction(parser)
    abstraction_3811 = _t1512
    _t1513 = parse_terms(parser)
    terms812 = _t1513
    consume_literal!(parser, ")")
    _t1514 = Proto.Reduce(op=abstraction810, body=abstraction_3811, terms=terms812)
    result814 = _t1514
    record_span!(parser, span_start813, "Reduce")
    return result814
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs815 = Proto.Term[]
    cond816 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond816
        _t1515 = parse_term(parser)
        item817 = _t1515
        push!(xs815, item817)
        cond816 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms818 = xs815
    consume_literal!(parser, ")")
    return terms818
end

function parse_term(parser::ParserState)::Proto.Term
    span_start822 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1516 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1517 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1518 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1519 = 1
                else
                    if match_lookahead_terminal(parser, "SYMBOL", 0)
                        _t1520 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1521 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1522 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1523 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1524 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1525 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1526 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1527 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1528 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1529 = 1
                                                        else
                                                            _t1529 = -1
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
    prediction819 = _t1516
    if prediction819 == 1
        _t1531 = parse_value(parser)
        value821 = _t1531
        _t1532 = Proto.Term(term_type=OneOf(:constant, value821))
        _t1530 = _t1532
    else
        if prediction819 == 0
            _t1534 = parse_var(parser)
            var820 = _t1534
            _t1535 = Proto.Term(term_type=OneOf(:var, var820))
            _t1533 = _t1535
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1530 = _t1533
    end
    result823 = _t1530
    record_span!(parser, span_start822, "Term")
    return result823
end

function parse_var(parser::ParserState)::Proto.Var
    span_start825 = span_start(parser)
    symbol824 = consume_terminal!(parser, "SYMBOL")
    _t1536 = Proto.Var(name=symbol824)
    result826 = _t1536
    record_span!(parser, span_start825, "Var")
    return result826
end

function parse_value(parser::ParserState)::Proto.Value
    span_start840 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1537 = 12
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1538 = 11
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1539 = 12
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1541 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1542 = 0
                        else
                            _t1542 = -1
                        end
                        _t1541 = _t1542
                    end
                    _t1540 = _t1541
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1543 = 7
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1544 = 8
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1545 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1546 = 3
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1547 = 9
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1548 = 4
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1549 = 5
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1550 = 6
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1551 = 10
                                                    else
                                                        _t1551 = -1
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
                    _t1540 = _t1543
                end
                _t1539 = _t1540
            end
            _t1538 = _t1539
        end
        _t1537 = _t1538
    end
    prediction827 = _t1537
    if prediction827 == 12
        _t1553 = parse_boolean_value(parser)
        boolean_value839 = _t1553
        _t1554 = Proto.Value(value=OneOf(:boolean_value, boolean_value839))
        _t1552 = _t1554
    else
        if prediction827 == 11
            consume_literal!(parser, "missing")
            _t1556 = Proto.MissingValue()
            _t1557 = Proto.Value(value=OneOf(:missing_value, _t1556))
            _t1555 = _t1557
        else
            if prediction827 == 10
                formatted_decimal838 = consume_terminal!(parser, "DECIMAL")
                _t1559 = Proto.Value(value=OneOf(:decimal_value, formatted_decimal838))
                _t1558 = _t1559
            else
                if prediction827 == 9
                    formatted_int128837 = consume_terminal!(parser, "INT128")
                    _t1561 = Proto.Value(value=OneOf(:int128_value, formatted_int128837))
                    _t1560 = _t1561
                else
                    if prediction827 == 8
                        formatted_uint128836 = consume_terminal!(parser, "UINT128")
                        _t1563 = Proto.Value(value=OneOf(:uint128_value, formatted_uint128836))
                        _t1562 = _t1563
                    else
                        if prediction827 == 7
                            formatted_uint32835 = consume_terminal!(parser, "UINT32")
                            _t1565 = Proto.Value(value=OneOf(:uint32_value, formatted_uint32835))
                            _t1564 = _t1565
                        else
                            if prediction827 == 6
                                formatted_float834 = consume_terminal!(parser, "FLOAT")
                                _t1567 = Proto.Value(value=OneOf(:float_value, formatted_float834))
                                _t1566 = _t1567
                            else
                                if prediction827 == 5
                                    formatted_float32833 = consume_terminal!(parser, "FLOAT32")
                                    _t1569 = Proto.Value(value=OneOf(:float32_value, formatted_float32833))
                                    _t1568 = _t1569
                                else
                                    if prediction827 == 4
                                        formatted_int832 = consume_terminal!(parser, "INT")
                                        _t1571 = Proto.Value(value=OneOf(:int_value, formatted_int832))
                                        _t1570 = _t1571
                                    else
                                        if prediction827 == 3
                                            formatted_int32831 = consume_terminal!(parser, "INT32")
                                            _t1573 = Proto.Value(value=OneOf(:int32_value, formatted_int32831))
                                            _t1572 = _t1573
                                        else
                                            if prediction827 == 2
                                                formatted_string830 = consume_terminal!(parser, "STRING")
                                                _t1575 = Proto.Value(value=OneOf(:string_value, formatted_string830))
                                                _t1574 = _t1575
                                            else
                                                if prediction827 == 1
                                                    _t1577 = parse_datetime(parser)
                                                    datetime829 = _t1577
                                                    _t1578 = Proto.Value(value=OneOf(:datetime_value, datetime829))
                                                    _t1576 = _t1578
                                                else
                                                    if prediction827 == 0
                                                        _t1580 = parse_date(parser)
                                                        date828 = _t1580
                                                        _t1581 = Proto.Value(value=OneOf(:date_value, date828))
                                                        _t1579 = _t1581
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1576 = _t1579
                                                end
                                                _t1574 = _t1576
                                            end
                                            _t1572 = _t1574
                                        end
                                        _t1570 = _t1572
                                    end
                                    _t1568 = _t1570
                                end
                                _t1566 = _t1568
                            end
                            _t1564 = _t1566
                        end
                        _t1562 = _t1564
                    end
                    _t1560 = _t1562
                end
                _t1558 = _t1560
            end
            _t1555 = _t1558
        end
        _t1552 = _t1555
    end
    result841 = _t1552
    record_span!(parser, span_start840, "Value")
    return result841
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start845 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    formatted_int842 = consume_terminal!(parser, "INT")
    formatted_int_3843 = consume_terminal!(parser, "INT")
    formatted_int_4844 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1582 = Proto.DateValue(year=Int32(formatted_int842), month=Int32(formatted_int_3843), day=Int32(formatted_int_4844))
    result846 = _t1582
    record_span!(parser, span_start845, "DateValue")
    return result846
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start854 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    formatted_int847 = consume_terminal!(parser, "INT")
    formatted_int_3848 = consume_terminal!(parser, "INT")
    formatted_int_4849 = consume_terminal!(parser, "INT")
    formatted_int_5850 = consume_terminal!(parser, "INT")
    formatted_int_6851 = consume_terminal!(parser, "INT")
    formatted_int_7852 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1583 = consume_terminal!(parser, "INT")
    else
        _t1583 = nothing
    end
    formatted_int_8853 = _t1583
    consume_literal!(parser, ")")
    _t1584 = Proto.DateTimeValue(year=Int32(formatted_int847), month=Int32(formatted_int_3848), day=Int32(formatted_int_4849), hour=Int32(formatted_int_5850), minute=Int32(formatted_int_6851), second=Int32(formatted_int_7852), microsecond=Int32((!isnothing(formatted_int_8853) ? formatted_int_8853 : 0)))
    result855 = _t1584
    record_span!(parser, span_start854, "DateTimeValue")
    return result855
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start860 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs856 = Proto.Formula[]
    cond857 = match_lookahead_literal(parser, "(", 0)
    while cond857
        _t1585 = parse_formula(parser)
        item858 = _t1585
        push!(xs856, item858)
        cond857 = match_lookahead_literal(parser, "(", 0)
    end
    formulas859 = xs856
    consume_literal!(parser, ")")
    _t1586 = Proto.Conjunction(args=formulas859)
    result861 = _t1586
    record_span!(parser, span_start860, "Conjunction")
    return result861
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start866 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs862 = Proto.Formula[]
    cond863 = match_lookahead_literal(parser, "(", 0)
    while cond863
        _t1587 = parse_formula(parser)
        item864 = _t1587
        push!(xs862, item864)
        cond863 = match_lookahead_literal(parser, "(", 0)
    end
    formulas865 = xs862
    consume_literal!(parser, ")")
    _t1588 = Proto.Disjunction(args=formulas865)
    result867 = _t1588
    record_span!(parser, span_start866, "Disjunction")
    return result867
end

function parse_not(parser::ParserState)::Proto.Not
    span_start869 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1589 = parse_formula(parser)
    formula868 = _t1589
    consume_literal!(parser, ")")
    _t1590 = Proto.Not(arg=formula868)
    result870 = _t1590
    record_span!(parser, span_start869, "Not")
    return result870
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start874 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1591 = parse_name(parser)
    name871 = _t1591
    _t1592 = parse_ffi_args(parser)
    ffi_args872 = _t1592
    _t1593 = parse_terms(parser)
    terms873 = _t1593
    consume_literal!(parser, ")")
    _t1594 = Proto.FFI(name=name871, args=ffi_args872, terms=terms873)
    result875 = _t1594
    record_span!(parser, span_start874, "FFI")
    return result875
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol876 = consume_terminal!(parser, "SYMBOL")
    return symbol876
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs877 = Proto.Abstraction[]
    cond878 = match_lookahead_literal(parser, "(", 0)
    while cond878
        _t1595 = parse_abstraction(parser)
        item879 = _t1595
        push!(xs877, item879)
        cond878 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions880 = xs877
    consume_literal!(parser, ")")
    return abstractions880
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start886 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1596 = parse_relation_id(parser)
    relation_id881 = _t1596
    xs882 = Proto.Term[]
    cond883 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond883
        _t1597 = parse_term(parser)
        item884 = _t1597
        push!(xs882, item884)
        cond883 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms885 = xs882
    consume_literal!(parser, ")")
    _t1598 = Proto.Atom(name=relation_id881, terms=terms885)
    result887 = _t1598
    record_span!(parser, span_start886, "Atom")
    return result887
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start893 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1599 = parse_name(parser)
    name888 = _t1599
    xs889 = Proto.Term[]
    cond890 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond890
        _t1600 = parse_term(parser)
        item891 = _t1600
        push!(xs889, item891)
        cond890 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    terms892 = xs889
    consume_literal!(parser, ")")
    _t1601 = Proto.Pragma(name=name888, terms=terms892)
    result894 = _t1601
    record_span!(parser, span_start893, "Pragma")
    return result894
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start910 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1603 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1604 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1605 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1606 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1607 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1608 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1609 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1610 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1611 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1612 = 7
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
            _t1603 = _t1604
        end
        _t1602 = _t1603
    else
        _t1602 = -1
    end
    prediction895 = _t1602
    if prediction895 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1614 = parse_name(parser)
        name905 = _t1614
        xs906 = Proto.RelTerm[]
        cond907 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        while cond907
            _t1615 = parse_rel_term(parser)
            item908 = _t1615
            push!(xs906, item908)
            cond907 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
        end
        rel_terms909 = xs906
        consume_literal!(parser, ")")
        _t1616 = Proto.Primitive(name=name905, terms=rel_terms909)
        _t1613 = _t1616
    else
        if prediction895 == 8
            _t1618 = parse_divide(parser)
            divide904 = _t1618
            _t1617 = divide904
        else
            if prediction895 == 7
                _t1620 = parse_multiply(parser)
                multiply903 = _t1620
                _t1619 = multiply903
            else
                if prediction895 == 6
                    _t1622 = parse_minus(parser)
                    minus902 = _t1622
                    _t1621 = minus902
                else
                    if prediction895 == 5
                        _t1624 = parse_add(parser)
                        add901 = _t1624
                        _t1623 = add901
                    else
                        if prediction895 == 4
                            _t1626 = parse_gt_eq(parser)
                            gt_eq900 = _t1626
                            _t1625 = gt_eq900
                        else
                            if prediction895 == 3
                                _t1628 = parse_gt(parser)
                                gt899 = _t1628
                                _t1627 = gt899
                            else
                                if prediction895 == 2
                                    _t1630 = parse_lt_eq(parser)
                                    lt_eq898 = _t1630
                                    _t1629 = lt_eq898
                                else
                                    if prediction895 == 1
                                        _t1632 = parse_lt(parser)
                                        lt897 = _t1632
                                        _t1631 = lt897
                                    else
                                        if prediction895 == 0
                                            _t1634 = parse_eq(parser)
                                            eq896 = _t1634
                                            _t1633 = eq896
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
            _t1617 = _t1619
        end
        _t1613 = _t1617
    end
    result911 = _t1613
    record_span!(parser, span_start910, "Primitive")
    return result911
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start914 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1635 = parse_term(parser)
    term912 = _t1635
    _t1636 = parse_term(parser)
    term_3913 = _t1636
    consume_literal!(parser, ")")
    _t1637 = Proto.RelTerm(rel_term_type=OneOf(:term, term912))
    _t1638 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3913))
    _t1639 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1637, _t1638])
    result915 = _t1639
    record_span!(parser, span_start914, "Primitive")
    return result915
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start918 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1640 = parse_term(parser)
    term916 = _t1640
    _t1641 = parse_term(parser)
    term_3917 = _t1641
    consume_literal!(parser, ")")
    _t1642 = Proto.RelTerm(rel_term_type=OneOf(:term, term916))
    _t1643 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3917))
    _t1644 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1642, _t1643])
    result919 = _t1644
    record_span!(parser, span_start918, "Primitive")
    return result919
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start922 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1645 = parse_term(parser)
    term920 = _t1645
    _t1646 = parse_term(parser)
    term_3921 = _t1646
    consume_literal!(parser, ")")
    _t1647 = Proto.RelTerm(rel_term_type=OneOf(:term, term920))
    _t1648 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3921))
    _t1649 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1647, _t1648])
    result923 = _t1649
    record_span!(parser, span_start922, "Primitive")
    return result923
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start926 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1650 = parse_term(parser)
    term924 = _t1650
    _t1651 = parse_term(parser)
    term_3925 = _t1651
    consume_literal!(parser, ")")
    _t1652 = Proto.RelTerm(rel_term_type=OneOf(:term, term924))
    _t1653 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3925))
    _t1654 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1652, _t1653])
    result927 = _t1654
    record_span!(parser, span_start926, "Primitive")
    return result927
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start930 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1655 = parse_term(parser)
    term928 = _t1655
    _t1656 = parse_term(parser)
    term_3929 = _t1656
    consume_literal!(parser, ")")
    _t1657 = Proto.RelTerm(rel_term_type=OneOf(:term, term928))
    _t1658 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3929))
    _t1659 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1657, _t1658])
    result931 = _t1659
    record_span!(parser, span_start930, "Primitive")
    return result931
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start935 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1660 = parse_term(parser)
    term932 = _t1660
    _t1661 = parse_term(parser)
    term_3933 = _t1661
    _t1662 = parse_term(parser)
    term_4934 = _t1662
    consume_literal!(parser, ")")
    _t1663 = Proto.RelTerm(rel_term_type=OneOf(:term, term932))
    _t1664 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3933))
    _t1665 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4934))
    _t1666 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1663, _t1664, _t1665])
    result936 = _t1666
    record_span!(parser, span_start935, "Primitive")
    return result936
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start940 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1667 = parse_term(parser)
    term937 = _t1667
    _t1668 = parse_term(parser)
    term_3938 = _t1668
    _t1669 = parse_term(parser)
    term_4939 = _t1669
    consume_literal!(parser, ")")
    _t1670 = Proto.RelTerm(rel_term_type=OneOf(:term, term937))
    _t1671 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3938))
    _t1672 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4939))
    _t1673 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1670, _t1671, _t1672])
    result941 = _t1673
    record_span!(parser, span_start940, "Primitive")
    return result941
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start945 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1674 = parse_term(parser)
    term942 = _t1674
    _t1675 = parse_term(parser)
    term_3943 = _t1675
    _t1676 = parse_term(parser)
    term_4944 = _t1676
    consume_literal!(parser, ")")
    _t1677 = Proto.RelTerm(rel_term_type=OneOf(:term, term942))
    _t1678 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3943))
    _t1679 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4944))
    _t1680 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1677, _t1678, _t1679])
    result946 = _t1680
    record_span!(parser, span_start945, "Primitive")
    return result946
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start950 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1681 = parse_term(parser)
    term947 = _t1681
    _t1682 = parse_term(parser)
    term_3948 = _t1682
    _t1683 = parse_term(parser)
    term_4949 = _t1683
    consume_literal!(parser, ")")
    _t1684 = Proto.RelTerm(rel_term_type=OneOf(:term, term947))
    _t1685 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3948))
    _t1686 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4949))
    _t1687 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1684, _t1685, _t1686])
    result951 = _t1687
    record_span!(parser, span_start950, "Primitive")
    return result951
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start955 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1688 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1689 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1690 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1691 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1692 = 0
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1693 = 1
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
        _t1688 = _t1689
    end
    prediction952 = _t1688
    if prediction952 == 1
        _t1704 = parse_term(parser)
        term954 = _t1704
        _t1705 = Proto.RelTerm(rel_term_type=OneOf(:term, term954))
        _t1703 = _t1705
    else
        if prediction952 == 0
            _t1707 = parse_specialized_value(parser)
            specialized_value953 = _t1707
            _t1708 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value953))
            _t1706 = _t1708
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1703 = _t1706
    end
    result956 = _t1703
    record_span!(parser, span_start955, "RelTerm")
    return result956
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start958 = span_start(parser)
    consume_literal!(parser, "#")
    _t1709 = parse_raw_value(parser)
    raw_value957 = _t1709
    result959 = raw_value957
    record_span!(parser, span_start958, "Value")
    return result959
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start965 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1710 = parse_name(parser)
    name960 = _t1710
    xs961 = Proto.RelTerm[]
    cond962 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    while cond962
        _t1711 = parse_rel_term(parser)
        item963 = _t1711
        push!(xs961, item963)
        cond962 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0))
    end
    rel_terms964 = xs961
    consume_literal!(parser, ")")
    _t1712 = Proto.RelAtom(name=name960, terms=rel_terms964)
    result966 = _t1712
    record_span!(parser, span_start965, "RelAtom")
    return result966
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1713 = parse_term(parser)
    term967 = _t1713
    _t1714 = parse_term(parser)
    term_3968 = _t1714
    consume_literal!(parser, ")")
    _t1715 = Proto.Cast(input=term967, result=term_3968)
    result970 = _t1715
    record_span!(parser, span_start969, "Cast")
    return result970
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs971 = Proto.Attribute[]
    cond972 = match_lookahead_literal(parser, "(", 0)
    while cond972
        _t1716 = parse_attribute(parser)
        item973 = _t1716
        push!(xs971, item973)
        cond972 = match_lookahead_literal(parser, "(", 0)
    end
    attributes974 = xs971
    consume_literal!(parser, ")")
    return attributes974
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1717 = parse_name(parser)
    name975 = _t1717
    xs976 = Proto.Value[]
    cond977 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond977
        _t1718 = parse_raw_value(parser)
        item978 = _t1718
        push!(xs976, item978)
        cond977 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    raw_values979 = xs976
    consume_literal!(parser, ")")
    _t1719 = Proto.Attribute(name=name975, args=raw_values979)
    result981 = _t1719
    record_span!(parser, span_start980, "Attribute")
    return result981
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start987 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs982 = Proto.RelationId[]
    cond983 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond983
        _t1720 = parse_relation_id(parser)
        item984 = _t1720
        push!(xs982, item984)
        cond983 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids985 = xs982
    _t1721 = parse_script(parser)
    script986 = _t1721
    consume_literal!(parser, ")")
    _t1722 = Proto.Algorithm(var"#global"=relation_ids985, body=script986)
    result988 = _t1722
    record_span!(parser, span_start987, "Algorithm")
    return result988
end

function parse_script(parser::ParserState)::Proto.Script
    span_start993 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs989 = Proto.Construct[]
    cond990 = match_lookahead_literal(parser, "(", 0)
    while cond990
        _t1723 = parse_construct(parser)
        item991 = _t1723
        push!(xs989, item991)
        cond990 = match_lookahead_literal(parser, "(", 0)
    end
    constructs992 = xs989
    consume_literal!(parser, ")")
    _t1724 = Proto.Script(constructs=constructs992)
    result994 = _t1724
    record_span!(parser, span_start993, "Script")
    return result994
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start998 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1726 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1727 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1728 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1729 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1730 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1731 = 1
                            else
                                _t1731 = -1
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
        _t1725 = _t1726
    else
        _t1725 = -1
    end
    prediction995 = _t1725
    if prediction995 == 1
        _t1733 = parse_instruction(parser)
        instruction997 = _t1733
        _t1734 = Proto.Construct(construct_type=OneOf(:instruction, instruction997))
        _t1732 = _t1734
    else
        if prediction995 == 0
            _t1736 = parse_loop(parser)
            loop996 = _t1736
            _t1737 = Proto.Construct(construct_type=OneOf(:loop, loop996))
            _t1735 = _t1737
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1732 = _t1735
    end
    result999 = _t1732
    record_span!(parser, span_start998, "Construct")
    return result999
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start1002 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1738 = parse_init(parser)
    init1000 = _t1738
    _t1739 = parse_script(parser)
    script1001 = _t1739
    consume_literal!(parser, ")")
    _t1740 = Proto.Loop(init=init1000, body=script1001)
    result1003 = _t1740
    record_span!(parser, span_start1002, "Loop")
    return result1003
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1004 = Proto.Instruction[]
    cond1005 = match_lookahead_literal(parser, "(", 0)
    while cond1005
        _t1741 = parse_instruction(parser)
        item1006 = _t1741
        push!(xs1004, item1006)
        cond1005 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1007 = xs1004
    consume_literal!(parser, ")")
    return instructions1007
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start1014 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1743 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1744 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1745 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1746 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1747 = 0
                        else
                            _t1747 = -1
                        end
                        _t1746 = _t1747
                    end
                    _t1745 = _t1746
                end
                _t1744 = _t1745
            end
            _t1743 = _t1744
        end
        _t1742 = _t1743
    else
        _t1742 = -1
    end
    prediction1008 = _t1742
    if prediction1008 == 4
        _t1749 = parse_monus_def(parser)
        monus_def1013 = _t1749
        _t1750 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1013))
        _t1748 = _t1750
    else
        if prediction1008 == 3
            _t1752 = parse_monoid_def(parser)
            monoid_def1012 = _t1752
            _t1753 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1012))
            _t1751 = _t1753
        else
            if prediction1008 == 2
                _t1755 = parse_break(parser)
                break1011 = _t1755
                _t1756 = Proto.Instruction(instr_type=OneOf(:var"#break", break1011))
                _t1754 = _t1756
            else
                if prediction1008 == 1
                    _t1758 = parse_upsert(parser)
                    upsert1010 = _t1758
                    _t1759 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1010))
                    _t1757 = _t1759
                else
                    if prediction1008 == 0
                        _t1761 = parse_assign(parser)
                        assign1009 = _t1761
                        _t1762 = Proto.Instruction(instr_type=OneOf(:assign, assign1009))
                        _t1760 = _t1762
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1757 = _t1760
                end
                _t1754 = _t1757
            end
            _t1751 = _t1754
        end
        _t1748 = _t1751
    end
    result1015 = _t1748
    record_span!(parser, span_start1014, "Instruction")
    return result1015
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start1019 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1763 = parse_relation_id(parser)
    relation_id1016 = _t1763
    _t1764 = parse_abstraction(parser)
    abstraction1017 = _t1764
    if match_lookahead_literal(parser, "(", 0)
        _t1766 = parse_attrs(parser)
        _t1765 = _t1766
    else
        _t1765 = nothing
    end
    attrs1018 = _t1765
    consume_literal!(parser, ")")
    _t1767 = Proto.Assign(name=relation_id1016, body=abstraction1017, attrs=(!isnothing(attrs1018) ? attrs1018 : Proto.Attribute[]))
    result1020 = _t1767
    record_span!(parser, span_start1019, "Assign")
    return result1020
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start1024 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1768 = parse_relation_id(parser)
    relation_id1021 = _t1768
    _t1769 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1022 = _t1769
    if match_lookahead_literal(parser, "(", 0)
        _t1771 = parse_attrs(parser)
        _t1770 = _t1771
    else
        _t1770 = nothing
    end
    attrs1023 = _t1770
    consume_literal!(parser, ")")
    _t1772 = Proto.Upsert(name=relation_id1021, body=abstraction_with_arity1022[1], attrs=(!isnothing(attrs1023) ? attrs1023 : Proto.Attribute[]), value_arity=abstraction_with_arity1022[2])
    result1025 = _t1772
    record_span!(parser, span_start1024, "Upsert")
    return result1025
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1773 = parse_bindings(parser)
    bindings1026 = _t1773
    _t1774 = parse_formula(parser)
    formula1027 = _t1774
    consume_literal!(parser, ")")
    _t1775 = Proto.Abstraction(vars=vcat(bindings1026[1], !isnothing(bindings1026[2]) ? bindings1026[2] : []), value=formula1027)
    return (_t1775, length(bindings1026[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start1031 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1776 = parse_relation_id(parser)
    relation_id1028 = _t1776
    _t1777 = parse_abstraction(parser)
    abstraction1029 = _t1777
    if match_lookahead_literal(parser, "(", 0)
        _t1779 = parse_attrs(parser)
        _t1778 = _t1779
    else
        _t1778 = nothing
    end
    attrs1030 = _t1778
    consume_literal!(parser, ")")
    _t1780 = Proto.Break(name=relation_id1028, body=abstraction1029, attrs=(!isnothing(attrs1030) ? attrs1030 : Proto.Attribute[]))
    result1032 = _t1780
    record_span!(parser, span_start1031, "Break")
    return result1032
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start1037 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1781 = parse_monoid(parser)
    monoid1033 = _t1781
    _t1782 = parse_relation_id(parser)
    relation_id1034 = _t1782
    _t1783 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1035 = _t1783
    if match_lookahead_literal(parser, "(", 0)
        _t1785 = parse_attrs(parser)
        _t1784 = _t1785
    else
        _t1784 = nothing
    end
    attrs1036 = _t1784
    consume_literal!(parser, ")")
    _t1786 = Proto.MonoidDef(monoid=monoid1033, name=relation_id1034, body=abstraction_with_arity1035[1], attrs=(!isnothing(attrs1036) ? attrs1036 : Proto.Attribute[]), value_arity=abstraction_with_arity1035[2])
    result1038 = _t1786
    record_span!(parser, span_start1037, "MonoidDef")
    return result1038
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start1044 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1788 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1789 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1790 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1791 = 2
                    else
                        _t1791 = -1
                    end
                    _t1790 = _t1791
                end
                _t1789 = _t1790
            end
            _t1788 = _t1789
        end
        _t1787 = _t1788
    else
        _t1787 = -1
    end
    prediction1039 = _t1787
    if prediction1039 == 3
        _t1793 = parse_sum_monoid(parser)
        sum_monoid1043 = _t1793
        _t1794 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1043))
        _t1792 = _t1794
    else
        if prediction1039 == 2
            _t1796 = parse_max_monoid(parser)
            max_monoid1042 = _t1796
            _t1797 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1042))
            _t1795 = _t1797
        else
            if prediction1039 == 1
                _t1799 = parse_min_monoid(parser)
                min_monoid1041 = _t1799
                _t1800 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1041))
                _t1798 = _t1800
            else
                if prediction1039 == 0
                    _t1802 = parse_or_monoid(parser)
                    or_monoid1040 = _t1802
                    _t1803 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1040))
                    _t1801 = _t1803
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1798 = _t1801
            end
            _t1795 = _t1798
        end
        _t1792 = _t1795
    end
    result1045 = _t1792
    record_span!(parser, span_start1044, "Monoid")
    return result1045
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start1046 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1804 = Proto.OrMonoid()
    result1047 = _t1804
    record_span!(parser, span_start1046, "OrMonoid")
    return result1047
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start1049 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1805 = parse_type(parser)
    type1048 = _t1805
    consume_literal!(parser, ")")
    _t1806 = Proto.MinMonoid(var"#type"=type1048)
    result1050 = _t1806
    record_span!(parser, span_start1049, "MinMonoid")
    return result1050
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start1052 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1807 = parse_type(parser)
    type1051 = _t1807
    consume_literal!(parser, ")")
    _t1808 = Proto.MaxMonoid(var"#type"=type1051)
    result1053 = _t1808
    record_span!(parser, span_start1052, "MaxMonoid")
    return result1053
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start1055 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1809 = parse_type(parser)
    type1054 = _t1809
    consume_literal!(parser, ")")
    _t1810 = Proto.SumMonoid(var"#type"=type1054)
    result1056 = _t1810
    record_span!(parser, span_start1055, "SumMonoid")
    return result1056
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start1061 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1811 = parse_monoid(parser)
    monoid1057 = _t1811
    _t1812 = parse_relation_id(parser)
    relation_id1058 = _t1812
    _t1813 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1059 = _t1813
    if match_lookahead_literal(parser, "(", 0)
        _t1815 = parse_attrs(parser)
        _t1814 = _t1815
    else
        _t1814 = nothing
    end
    attrs1060 = _t1814
    consume_literal!(parser, ")")
    _t1816 = Proto.MonusDef(monoid=monoid1057, name=relation_id1058, body=abstraction_with_arity1059[1], attrs=(!isnothing(attrs1060) ? attrs1060 : Proto.Attribute[]), value_arity=abstraction_with_arity1059[2])
    result1062 = _t1816
    record_span!(parser, span_start1061, "MonusDef")
    return result1062
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start1067 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1817 = parse_relation_id(parser)
    relation_id1063 = _t1817
    _t1818 = parse_abstraction(parser)
    abstraction1064 = _t1818
    _t1819 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1065 = _t1819
    _t1820 = parse_functional_dependency_values(parser)
    functional_dependency_values1066 = _t1820
    consume_literal!(parser, ")")
    _t1821 = Proto.FunctionalDependency(guard=abstraction1064, keys=functional_dependency_keys1065, values=functional_dependency_values1066)
    _t1822 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1821), name=relation_id1063)
    result1068 = _t1822
    record_span!(parser, span_start1067, "Constraint")
    return result1068
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1069 = Proto.Var[]
    cond1070 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1070
        _t1823 = parse_var(parser)
        item1071 = _t1823
        push!(xs1069, item1071)
        cond1070 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1072 = xs1069
    consume_literal!(parser, ")")
    return vars1072
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1073 = Proto.Var[]
    cond1074 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1074
        _t1824 = parse_var(parser)
        item1075 = _t1824
        push!(xs1073, item1075)
        cond1074 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1076 = xs1073
    consume_literal!(parser, ")")
    return vars1076
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1081 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "edb", 1)
            _t1826 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1827 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1828 = 1
                else
                    _t1828 = -1
                end
                _t1827 = _t1828
            end
            _t1826 = _t1827
        end
        _t1825 = _t1826
    else
        _t1825 = -1
    end
    prediction1077 = _t1825
    if prediction1077 == 2
        _t1830 = parse_csv_data(parser)
        csv_data1080 = _t1830
        _t1831 = Proto.Data(data_type=OneOf(:csv_data, csv_data1080))
        _t1829 = _t1831
    else
        if prediction1077 == 1
            _t1833 = parse_betree_relation(parser)
            betree_relation1079 = _t1833
            _t1834 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1079))
            _t1832 = _t1834
        else
            if prediction1077 == 0
                _t1836 = parse_edb(parser)
                edb1078 = _t1836
                _t1837 = Proto.Data(data_type=OneOf(:edb, edb1078))
                _t1835 = _t1837
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1832 = _t1835
        end
        _t1829 = _t1832
    end
    result1082 = _t1829
    record_span!(parser, span_start1081, "Data")
    return result1082
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1086 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1838 = parse_relation_id(parser)
    relation_id1083 = _t1838
    _t1839 = parse_edb_path(parser)
    edb_path1084 = _t1839
    _t1840 = parse_edb_types(parser)
    edb_types1085 = _t1840
    consume_literal!(parser, ")")
    _t1841 = Proto.EDB(target_id=relation_id1083, path=edb_path1084, types=edb_types1085)
    result1087 = _t1841
    record_span!(parser, span_start1086, "EDB")
    return result1087
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1088 = String[]
    cond1089 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1089
        item1090 = consume_terminal!(parser, "STRING")
        push!(xs1088, item1090)
        cond1089 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1091 = xs1088
    consume_literal!(parser, "]")
    return strings1091
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1092 = Proto.var"#Type"[]
    cond1093 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1093
        _t1842 = parse_type(parser)
        item1094 = _t1842
        push!(xs1092, item1094)
        cond1093 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1095 = xs1092
    consume_literal!(parser, "]")
    return types1095
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1098 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1843 = parse_relation_id(parser)
    relation_id1096 = _t1843
    _t1844 = parse_betree_info(parser)
    betree_info1097 = _t1844
    consume_literal!(parser, ")")
    _t1845 = Proto.BeTreeRelation(name=relation_id1096, relation_info=betree_info1097)
    result1099 = _t1845
    record_span!(parser, span_start1098, "BeTreeRelation")
    return result1099
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1103 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1846 = parse_betree_info_key_types(parser)
    betree_info_key_types1100 = _t1846
    _t1847 = parse_betree_info_value_types(parser)
    betree_info_value_types1101 = _t1847
    _t1848 = parse_config_dict(parser)
    config_dict1102 = _t1848
    consume_literal!(parser, ")")
    _t1849 = construct_betree_info(parser, betree_info_key_types1100, betree_info_value_types1101, config_dict1102)
    result1104 = _t1849
    record_span!(parser, span_start1103, "BeTreeInfo")
    return result1104
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1105 = Proto.var"#Type"[]
    cond1106 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1106
        _t1850 = parse_type(parser)
        item1107 = _t1850
        push!(xs1105, item1107)
        cond1106 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1108 = xs1105
    consume_literal!(parser, ")")
    return types1108
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1109 = Proto.var"#Type"[]
    cond1110 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1110
        _t1851 = parse_type(parser)
        item1111 = _t1851
        push!(xs1109, item1111)
        cond1110 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1112 = xs1109
    consume_literal!(parser, ")")
    return types1112
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1117 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1852 = parse_csvlocator(parser)
    csvlocator1113 = _t1852
    _t1853 = parse_csv_config(parser)
    csv_config1114 = _t1853
    _t1854 = parse_gnf_columns(parser)
    gnf_columns1115 = _t1854
    _t1855 = parse_csv_asof(parser)
    csv_asof1116 = _t1855
    consume_literal!(parser, ")")
    _t1856 = Proto.CSVData(locator=csvlocator1113, config=csv_config1114, columns=gnf_columns1115, asof=csv_asof1116)
    result1118 = _t1856
    record_span!(parser, span_start1117, "CSVData")
    return result1118
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1121 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1858 = parse_csv_locator_paths(parser)
        _t1857 = _t1858
    else
        _t1857 = nothing
    end
    csv_locator_paths1119 = _t1857
    if match_lookahead_literal(parser, "(", 0)
        _t1860 = parse_csv_locator_inline_data(parser)
        _t1859 = _t1860
    else
        _t1859 = nothing
    end
    csv_locator_inline_data1120 = _t1859
    consume_literal!(parser, ")")
    _t1861 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1119) ? csv_locator_paths1119 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1120) ? csv_locator_inline_data1120 : "")))
    result1122 = _t1861
    record_span!(parser, span_start1121, "CSVLocator")
    return result1122
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1123 = String[]
    cond1124 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1124
        item1125 = consume_terminal!(parser, "STRING")
        push!(xs1123, item1125)
        cond1124 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1126 = xs1123
    consume_literal!(parser, ")")
    return strings1126
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1127 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1127
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1129 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1862 = parse_config_dict(parser)
    config_dict1128 = _t1862
    consume_literal!(parser, ")")
    _t1863 = construct_csv_config(parser, config_dict1128)
    result1130 = _t1863
    record_span!(parser, span_start1129, "CSVConfig")
    return result1130
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1131 = Proto.GNFColumn[]
    cond1132 = match_lookahead_literal(parser, "(", 0)
    while cond1132
        _t1864 = parse_gnf_column(parser)
        item1133 = _t1864
        push!(xs1131, item1133)
        cond1132 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1134 = xs1131
    consume_literal!(parser, ")")
    return gnf_columns1134
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1141 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1865 = parse_gnf_column_path(parser)
    gnf_column_path1135 = _t1865
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1867 = parse_relation_id(parser)
        _t1866 = _t1867
    else
        _t1866 = nothing
    end
    relation_id1136 = _t1866
    consume_literal!(parser, "[")
    xs1137 = Proto.var"#Type"[]
    cond1138 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1138
        _t1868 = parse_type(parser)
        item1139 = _t1868
        push!(xs1137, item1139)
        cond1138 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1140 = xs1137
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1869 = Proto.GNFColumn(column_path=gnf_column_path1135, target_id=relation_id1136, types=types1140)
    result1142 = _t1869
    record_span!(parser, span_start1141, "GNFColumn")
    return result1142
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1870 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1871 = 0
        else
            _t1871 = -1
        end
        _t1870 = _t1871
    end
    prediction1143 = _t1870
    if prediction1143 == 1
        consume_literal!(parser, "[")
        xs1145 = String[]
        cond1146 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1146
            item1147 = consume_terminal!(parser, "STRING")
            push!(xs1145, item1147)
            cond1146 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1148 = xs1145
        consume_literal!(parser, "]")
        _t1872 = strings1148
    else
        if prediction1143 == 0
            string1144 = consume_terminal!(parser, "STRING")
            _t1873 = String[string1144]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1872 = _t1873
    end
    return _t1872
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1149 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1149
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1151 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1874 = parse_fragment_id(parser)
    fragment_id1150 = _t1874
    consume_literal!(parser, ")")
    _t1875 = Proto.Undefine(fragment_id=fragment_id1150)
    result1152 = _t1875
    record_span!(parser, span_start1151, "Undefine")
    return result1152
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1157 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1153 = Proto.RelationId[]
    cond1154 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1154
        _t1876 = parse_relation_id(parser)
        item1155 = _t1876
        push!(xs1153, item1155)
        cond1154 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1156 = xs1153
    consume_literal!(parser, ")")
    _t1877 = Proto.Context(relations=relation_ids1156)
    result1158 = _t1877
    record_span!(parser, span_start1157, "Context")
    return result1158
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1163 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1159 = Proto.SnapshotMapping[]
    cond1160 = match_lookahead_literal(parser, "[", 0)
    while cond1160
        _t1878 = parse_snapshot_mapping(parser)
        item1161 = _t1878
        push!(xs1159, item1161)
        cond1160 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1162 = xs1159
    consume_literal!(parser, ")")
    _t1879 = Proto.Snapshot(mappings=snapshot_mappings1162)
    result1164 = _t1879
    record_span!(parser, span_start1163, "Snapshot")
    return result1164
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1167 = span_start(parser)
    _t1880 = parse_edb_path(parser)
    edb_path1165 = _t1880
    _t1881 = parse_relation_id(parser)
    relation_id1166 = _t1881
    _t1882 = Proto.SnapshotMapping(destination_path=edb_path1165, source_relation=relation_id1166)
    result1168 = _t1882
    record_span!(parser, span_start1167, "SnapshotMapping")
    return result1168
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1169 = Proto.Read[]
    cond1170 = match_lookahead_literal(parser, "(", 0)
    while cond1170
        _t1883 = parse_read(parser)
        item1171 = _t1883
        push!(xs1169, item1171)
        cond1170 = match_lookahead_literal(parser, "(", 0)
    end
    reads1172 = xs1169
    consume_literal!(parser, ")")
    return reads1172
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1179 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1885 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1886 = 1
            else
                if match_lookahead_literal(parser, "export_iceberg", 1)
                    _t1887 = 4
                else
                    if match_lookahead_literal(parser, "export", 1)
                        _t1888 = 4
                    else
                        if match_lookahead_literal(parser, "demand", 1)
                            _t1889 = 0
                        else
                            if match_lookahead_literal(parser, "abort", 1)
                                _t1890 = 3
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
            end
            _t1885 = _t1886
        end
        _t1884 = _t1885
    else
        _t1884 = -1
    end
    prediction1173 = _t1884
    if prediction1173 == 4
        _t1892 = parse_export(parser)
        export1178 = _t1892
        _t1893 = Proto.Read(read_type=OneOf(:var"#export", export1178))
        _t1891 = _t1893
    else
        if prediction1173 == 3
            _t1895 = parse_abort(parser)
            abort1177 = _t1895
            _t1896 = Proto.Read(read_type=OneOf(:abort, abort1177))
            _t1894 = _t1896
        else
            if prediction1173 == 2
                _t1898 = parse_what_if(parser)
                what_if1176 = _t1898
                _t1899 = Proto.Read(read_type=OneOf(:what_if, what_if1176))
                _t1897 = _t1899
            else
                if prediction1173 == 1
                    _t1901 = parse_output(parser)
                    output1175 = _t1901
                    _t1902 = Proto.Read(read_type=OneOf(:output, output1175))
                    _t1900 = _t1902
                else
                    if prediction1173 == 0
                        _t1904 = parse_demand(parser)
                        demand1174 = _t1904
                        _t1905 = Proto.Read(read_type=OneOf(:demand, demand1174))
                        _t1903 = _t1905
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1900 = _t1903
                end
                _t1897 = _t1900
            end
            _t1894 = _t1897
        end
        _t1891 = _t1894
    end
    result1180 = _t1891
    record_span!(parser, span_start1179, "Read")
    return result1180
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1182 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1906 = parse_relation_id(parser)
    relation_id1181 = _t1906
    consume_literal!(parser, ")")
    _t1907 = Proto.Demand(relation_id=relation_id1181)
    result1183 = _t1907
    record_span!(parser, span_start1182, "Demand")
    return result1183
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1186 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1908 = parse_name(parser)
    name1184 = _t1908
    _t1909 = parse_relation_id(parser)
    relation_id1185 = _t1909
    consume_literal!(parser, ")")
    _t1910 = Proto.Output(name=name1184, relation_id=relation_id1185)
    result1187 = _t1910
    record_span!(parser, span_start1186, "Output")
    return result1187
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1190 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1911 = parse_name(parser)
    name1188 = _t1911
    _t1912 = parse_epoch(parser)
    epoch1189 = _t1912
    consume_literal!(parser, ")")
    _t1913 = Proto.WhatIf(branch=name1188, epoch=epoch1189)
    result1191 = _t1913
    record_span!(parser, span_start1190, "WhatIf")
    return result1191
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1194 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1915 = parse_name(parser)
        _t1914 = _t1915
    else
        _t1914 = nothing
    end
    name1192 = _t1914
    _t1916 = parse_relation_id(parser)
    relation_id1193 = _t1916
    consume_literal!(parser, ")")
    _t1917 = Proto.Abort(name=(!isnothing(name1192) ? name1192 : "abort"), relation_id=relation_id1193)
    result1195 = _t1917
    record_span!(parser, span_start1194, "Abort")
    return result1195
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1199 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_iceberg", 1)
            _t1919 = 1
        else
            if match_lookahead_literal(parser, "export", 1)
                _t1920 = 0
            else
                _t1920 = -1
            end
            _t1919 = _t1920
        end
        _t1918 = _t1919
    else
        _t1918 = -1
    end
    prediction1196 = _t1918
    if prediction1196 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_iceberg")
        _t1922 = parse_export_iceberg_config(parser)
        export_iceberg_config1198 = _t1922
        consume_literal!(parser, ")")
        _t1923 = Proto.Export(export_config=OneOf(:iceberg_config, export_iceberg_config1198))
        _t1921 = _t1923
    else
        if prediction1196 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export")
            _t1925 = parse_export_csv_config(parser)
            export_csv_config1197 = _t1925
            consume_literal!(parser, ")")
            _t1926 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1197))
            _t1924 = _t1926
        else
            throw(ParseError("Unexpected token in export" * ": " * string(lookahead(parser, 0))))
        end
        _t1921 = _t1924
    end
    result1200 = _t1921
    record_span!(parser, span_start1199, "Export")
    return result1200
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1208 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1928 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1929 = 1
            else
                _t1929 = -1
            end
            _t1928 = _t1929
        end
        _t1927 = _t1928
    else
        _t1927 = -1
    end
    prediction1201 = _t1927
    if prediction1201 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1931 = parse_export_csv_path(parser)
        export_csv_path1205 = _t1931
        _t1932 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1206 = _t1932
        _t1933 = parse_config_dict(parser)
        config_dict1207 = _t1933
        consume_literal!(parser, ")")
        _t1934 = construct_export_csv_config(parser, export_csv_path1205, export_csv_columns_list1206, config_dict1207)
        _t1930 = _t1934
    else
        if prediction1201 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1936 = parse_export_csv_path(parser)
            export_csv_path1202 = _t1936
            _t1937 = parse_export_csv_source(parser)
            export_csv_source1203 = _t1937
            _t1938 = parse_csv_config(parser)
            csv_config1204 = _t1938
            consume_literal!(parser, ")")
            _t1939 = construct_export_csv_config_with_source(parser, export_csv_path1202, export_csv_source1203, csv_config1204)
            _t1935 = _t1939
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1930 = _t1935
    end
    result1209 = _t1930
    record_span!(parser, span_start1208, "ExportCSVConfig")
    return result1209
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1210 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1210
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1217 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1941 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1942 = 0
            else
                _t1942 = -1
            end
            _t1941 = _t1942
        end
        _t1940 = _t1941
    else
        _t1940 = -1
    end
    prediction1211 = _t1940
    if prediction1211 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1944 = parse_relation_id(parser)
        relation_id1216 = _t1944
        consume_literal!(parser, ")")
        _t1945 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1216))
        _t1943 = _t1945
    else
        if prediction1211 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1212 = Proto.ExportCSVColumn[]
            cond1213 = match_lookahead_literal(parser, "(", 0)
            while cond1213
                _t1947 = parse_export_csv_column(parser)
                item1214 = _t1947
                push!(xs1212, item1214)
                cond1213 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1215 = xs1212
            consume_literal!(parser, ")")
            _t1948 = Proto.ExportCSVColumns(columns=export_csv_columns1215)
            _t1949 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1948))
            _t1946 = _t1949
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1943 = _t1946
    end
    result1218 = _t1943
    record_span!(parser, span_start1217, "ExportCSVSource")
    return result1218
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1221 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1219 = consume_terminal!(parser, "STRING")
    _t1950 = parse_relation_id(parser)
    relation_id1220 = _t1950
    consume_literal!(parser, ")")
    _t1951 = Proto.ExportCSVColumn(column_name=string1219, column_data=relation_id1220)
    result1222 = _t1951
    record_span!(parser, span_start1221, "ExportCSVColumn")
    return result1222
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1223 = Proto.ExportCSVColumn[]
    cond1224 = match_lookahead_literal(parser, "(", 0)
    while cond1224
        _t1952 = parse_export_csv_column(parser)
        item1225 = _t1952
        push!(xs1223, item1225)
        cond1224 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1226 = xs1223
    consume_literal!(parser, ")")
    return export_csv_columns1226
end

function parse_export_iceberg_config(parser::ParserState)::Proto.ExportIcebergConfig
    span_start1236 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_iceberg_config")
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_uri")
    string1227 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "namespace")
    xs1228 = String[]
    cond1229 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1229
        item1230 = consume_terminal!(parser, "STRING")
        push!(xs1228, item1230)
        cond1229 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1231 = xs1228
    consume_literal!(parser, ")")
    consume_literal!(parser, "(")
    consume_literal!(parser, "table_name")
    string_121232 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    _t1953 = parse_export_iceberg_catalog_properties(parser)
    export_iceberg_catalog_properties1233 = _t1953
    consume_literal!(parser, "(")
    consume_literal!(parser, "schema")
    string_171234 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if match_lookahead_literal(parser, "{", 0)
        _t1955 = parse_config_dict(parser)
        _t1954 = _t1955
    else
        _t1954 = nothing
    end
    config_dict1235 = _t1954
    consume_literal!(parser, ")")
    _t1956 = construct_export_iceberg_config_from_optional(parser, string1227, strings1231, string_121232, export_iceberg_catalog_properties1233, string_171234, config_dict1235)
    result1237 = _t1956
    record_span!(parser, span_start1236, "ExportIcebergConfig")
    return result1237
end

function parse_export_iceberg_catalog_properties(parser::ParserState)::Proto.IcebergCatalogProperties
    span_start1240 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "catalog_properties")
    consume_literal!(parser, "(")
    consume_literal!(parser, "warehouse")
    string1238 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    if match_lookahead_literal(parser, "{", 0)
        _t1958 = parse_config_dict(parser)
        _t1957 = _t1958
    else
        _t1957 = nothing
    end
    config_dict1239 = _t1957
    consume_literal!(parser, ")")
    _t1959 = construct_iceberg_catalog_properties_from_optional(parser, string1238, config_dict1239)
    result1241 = _t1959
    record_span!(parser, span_start1240, "IcebergCatalogProperties")
    return result1241
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
