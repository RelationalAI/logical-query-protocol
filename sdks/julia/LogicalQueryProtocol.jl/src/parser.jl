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


struct Token
    type::String
    value::Any
    pos::Int
end

Base.show(io::IO, t::Token) = print(io, "Token(", t.type, ", ", repr(t.value), ", ", t.pos, ")")


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
    ("FLOAT", r"([-]?\d+\.\d+|inf|nan)", scan_float),
    ("INT", r"[-]?\d+", scan_int),
    ("INT128", r"[-]?\d+i128", scan_int128),
    ("STRING", r"\"(?:[^\"\\]|\\.)*\"", scan_string),
    ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_.-]*", scan_symbol),
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
        push!(lexer.tokens, Token(token_type, action(value), lexer.pos))
        lexer.pos = end_pos
    end

    push!(lexer.tokens, Token("\$", "", lexer.pos))
    return nothing
end


mutable struct ParserState
    tokens::Vector{Token}
    pos::Int
    id_to_debuginfo::Dict{Vector{UInt8},Vector{Pair{Tuple{UInt64,UInt64},String}}}
    _current_fragment_id::Union{Nothing,Vector{UInt8}}
    _relation_id_to_name::Dict{Tuple{UInt64,UInt64},String}

    function ParserState(tokens::Vector{Token})
        return new(tokens, 1, Dict(), nothing, Dict())
    end
end


function lookahead(parser::ParserState, k::Int=0)::Token
    idx = parser.pos + k
    return idx <= length(parser.tokens) ? parser.tokens[idx] : Token("\$", "", -1)
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
    id_low = Base.parse(UInt64, bytes2hex(hash_bytes[1:8]), base=16)
    id_high = UInt64(0)
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
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return Int32(_get_oneof_field(value, :int_value))
    else
        _t1350 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1351 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1352 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1353 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1354 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1355 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1356 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1357 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1358 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1359 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1359
    _t1360 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1360
    _t1361 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1361
    _t1362 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1362
    _t1363 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1363
    _t1364 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1364
    _t1365 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1365
    _t1366 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1366
    _t1367 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1367
    _t1368 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1368
    _t1369 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1369
    _t1370 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size = _t1370
    _t1371 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size)
    return _t1371
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1372 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1372
    _t1373 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1373
    _t1374 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1374
    _t1375 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1375
    _t1376 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1376
    _t1377 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1377
    _t1378 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1378
    _t1379 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1379
    _t1380 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1380
    _t1381 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1381
    _t1382 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1382
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1383 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1383
    _t1384 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1384
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
    _t1385 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1385
    _t1386 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1386
    _t1387 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1387
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1388 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1388
    _t1389 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1389
    _t1390 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1390
    _t1391 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1391
    _t1392 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1392
    _t1393 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1393
    _t1394 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1394
    _t1395 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1395
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1396 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1396
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t733 = parse_configure(parser)
        _t732 = _t733
    else
        _t732 = nothing
    end
    configure366 = _t732
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t735 = parse_sync(parser)
        _t734 = _t735
    else
        _t734 = nothing
    end
    sync367 = _t734
    xs368 = Proto.Epoch[]
    cond369 = match_lookahead_literal(parser, "(", 0)
    while cond369
        _t736 = parse_epoch(parser)
        item370 = _t736
        push!(xs368, item370)
        cond369 = match_lookahead_literal(parser, "(", 0)
    end
    epochs371 = xs368
    consume_literal!(parser, ")")
    _t737 = default_configure(parser)
    _t738 = Proto.Transaction(epochs=epochs371, configure=(!isnothing(configure366) ? configure366 : _t737), sync=sync367)
    return _t738
end

function parse_configure(parser::ParserState)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t739 = parse_config_dict(parser)
    config_dict372 = _t739
    consume_literal!(parser, ")")
    _t740 = construct_configure(parser, config_dict372)
    return _t740
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs373 = Tuple{String, Proto.Value}[]
    cond374 = match_lookahead_literal(parser, ":", 0)
    while cond374
        _t741 = parse_config_key_value(parser)
        item375 = _t741
        push!(xs373, item375)
        cond374 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values376 = xs373
    consume_literal!(parser, "}")
    return config_key_values376
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol377 = consume_terminal!(parser, "SYMBOL")
    _t742 = parse_value(parser)
    value378 = _t742
    return (symbol377, value378,)
end

function parse_value(parser::ParserState)::Proto.Value
    if match_lookahead_literal(parser, "true", 0)
        _t743 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t744 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t745 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t747 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t748 = 0
                        else
                            _t748 = -1
                        end
                        _t747 = _t748
                    end
                    _t746 = _t747
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t749 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t750 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t751 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t752 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t753 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t754 = 7
                                        else
                                            _t754 = -1
                                        end
                                        _t753 = _t754
                                    end
                                    _t752 = _t753
                                end
                                _t751 = _t752
                            end
                            _t750 = _t751
                        end
                        _t749 = _t750
                    end
                    _t746 = _t749
                end
                _t745 = _t746
            end
            _t744 = _t745
        end
        _t743 = _t744
    end
    prediction379 = _t743
    if prediction379 == 9
        _t756 = parse_boolean_value(parser)
        boolean_value388 = _t756
        _t757 = Proto.Value(value=OneOf(:boolean_value, boolean_value388))
        _t755 = _t757
    else
        if prediction379 == 8
            consume_literal!(parser, "missing")
            _t759 = Proto.MissingValue()
            _t760 = Proto.Value(value=OneOf(:missing_value, _t759))
            _t758 = _t760
        else
            if prediction379 == 7
                decimal387 = consume_terminal!(parser, "DECIMAL")
                _t762 = Proto.Value(value=OneOf(:decimal_value, decimal387))
                _t761 = _t762
            else
                if prediction379 == 6
                    int128386 = consume_terminal!(parser, "INT128")
                    _t764 = Proto.Value(value=OneOf(:int128_value, int128386))
                    _t763 = _t764
                else
                    if prediction379 == 5
                        uint128385 = consume_terminal!(parser, "UINT128")
                        _t766 = Proto.Value(value=OneOf(:uint128_value, uint128385))
                        _t765 = _t766
                    else
                        if prediction379 == 4
                            float384 = consume_terminal!(parser, "FLOAT")
                            _t768 = Proto.Value(value=OneOf(:float_value, float384))
                            _t767 = _t768
                        else
                            if prediction379 == 3
                                int383 = consume_terminal!(parser, "INT")
                                _t770 = Proto.Value(value=OneOf(:int_value, int383))
                                _t769 = _t770
                            else
                                if prediction379 == 2
                                    string382 = consume_terminal!(parser, "STRING")
                                    _t772 = Proto.Value(value=OneOf(:string_value, string382))
                                    _t771 = _t772
                                else
                                    if prediction379 == 1
                                        _t774 = parse_datetime(parser)
                                        datetime381 = _t774
                                        _t775 = Proto.Value(value=OneOf(:datetime_value, datetime381))
                                        _t773 = _t775
                                    else
                                        if prediction379 == 0
                                            _t777 = parse_date(parser)
                                            date380 = _t777
                                            _t778 = Proto.Value(value=OneOf(:date_value, date380))
                                            _t776 = _t778
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t773 = _t776
                                    end
                                    _t771 = _t773
                                end
                                _t769 = _t771
                            end
                            _t767 = _t769
                        end
                        _t765 = _t767
                    end
                    _t763 = _t765
                end
                _t761 = _t763
            end
            _t758 = _t761
        end
        _t755 = _t758
    end
    return _t755
end

function parse_date(parser::ParserState)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int389 = consume_terminal!(parser, "INT")
    int_3390 = consume_terminal!(parser, "INT")
    int_4391 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t779 = Proto.DateValue(year=Int32(int389), month=Int32(int_3390), day=Int32(int_4391))
    return _t779
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int392 = consume_terminal!(parser, "INT")
    int_3393 = consume_terminal!(parser, "INT")
    int_4394 = consume_terminal!(parser, "INT")
    int_5395 = consume_terminal!(parser, "INT")
    int_6396 = consume_terminal!(parser, "INT")
    int_7397 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t780 = consume_terminal!(parser, "INT")
    else
        _t780 = nothing
    end
    int_8398 = _t780
    consume_literal!(parser, ")")
    _t781 = Proto.DateTimeValue(year=Int32(int392), month=Int32(int_3393), day=Int32(int_4394), hour=Int32(int_5395), minute=Int32(int_6396), second=Int32(int_7397), microsecond=Int32((!isnothing(int_8398) ? int_8398 : 0)))
    return _t781
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t782 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t783 = 1
        else
            _t783 = -1
        end
        _t782 = _t783
    end
    prediction399 = _t782
    if prediction399 == 1
        consume_literal!(parser, "false")
        _t784 = false
    else
        if prediction399 == 0
            consume_literal!(parser, "true")
            _t785 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t784 = _t785
    end
    return _t784
end

function parse_sync(parser::ParserState)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs400 = Proto.FragmentId[]
    cond401 = match_lookahead_literal(parser, ":", 0)
    while cond401
        _t786 = parse_fragment_id(parser)
        item402 = _t786
        push!(xs400, item402)
        cond401 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids403 = xs400
    consume_literal!(parser, ")")
    _t787 = Proto.Sync(fragments=fragment_ids403)
    return _t787
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol404 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol404))
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t789 = parse_epoch_writes(parser)
        _t788 = _t789
    else
        _t788 = nothing
    end
    epoch_writes405 = _t788
    if match_lookahead_literal(parser, "(", 0)
        _t791 = parse_epoch_reads(parser)
        _t790 = _t791
    else
        _t790 = nothing
    end
    epoch_reads406 = _t790
    consume_literal!(parser, ")")
    _t792 = Proto.Epoch(writes=(!isnothing(epoch_writes405) ? epoch_writes405 : Proto.Write[]), reads=(!isnothing(epoch_reads406) ? epoch_reads406 : Proto.Read[]))
    return _t792
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs407 = Proto.Write[]
    cond408 = match_lookahead_literal(parser, "(", 0)
    while cond408
        _t793 = parse_write(parser)
        item409 = _t793
        push!(xs407, item409)
        cond408 = match_lookahead_literal(parser, "(", 0)
    end
    writes410 = xs407
    consume_literal!(parser, ")")
    return writes410
end

function parse_write(parser::ParserState)::Proto.Write
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t795 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t796 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t797 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t798 = 2
                    else
                        _t798 = -1
                    end
                    _t797 = _t798
                end
                _t796 = _t797
            end
            _t795 = _t796
        end
        _t794 = _t795
    else
        _t794 = -1
    end
    prediction411 = _t794
    if prediction411 == 3
        _t800 = parse_snapshot(parser)
        snapshot415 = _t800
        _t801 = Proto.Write(write_type=OneOf(:snapshot, snapshot415))
        _t799 = _t801
    else
        if prediction411 == 2
            _t803 = parse_context(parser)
            context414 = _t803
            _t804 = Proto.Write(write_type=OneOf(:context, context414))
            _t802 = _t804
        else
            if prediction411 == 1
                _t806 = parse_undefine(parser)
                undefine413 = _t806
                _t807 = Proto.Write(write_type=OneOf(:undefine, undefine413))
                _t805 = _t807
            else
                if prediction411 == 0
                    _t809 = parse_define(parser)
                    define412 = _t809
                    _t810 = Proto.Write(write_type=OneOf(:define, define412))
                    _t808 = _t810
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t805 = _t808
            end
            _t802 = _t805
        end
        _t799 = _t802
    end
    return _t799
end

function parse_define(parser::ParserState)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t811 = parse_fragment(parser)
    fragment416 = _t811
    consume_literal!(parser, ")")
    _t812 = Proto.Define(fragment=fragment416)
    return _t812
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t813 = parse_new_fragment_id(parser)
    new_fragment_id417 = _t813
    xs418 = Proto.Declaration[]
    cond419 = match_lookahead_literal(parser, "(", 0)
    while cond419
        _t814 = parse_declaration(parser)
        item420 = _t814
        push!(xs418, item420)
        cond419 = match_lookahead_literal(parser, "(", 0)
    end
    declarations421 = xs418
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id417, declarations421)
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    _t815 = parse_fragment_id(parser)
    fragment_id422 = _t815
    start_fragment!(parser, fragment_id422)
    return fragment_id422
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t817 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t818 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t819 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t820 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t821 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t822 = 1
                            else
                                _t822 = -1
                            end
                            _t821 = _t822
                        end
                        _t820 = _t821
                    end
                    _t819 = _t820
                end
                _t818 = _t819
            end
            _t817 = _t818
        end
        _t816 = _t817
    else
        _t816 = -1
    end
    prediction423 = _t816
    if prediction423 == 3
        _t824 = parse_data(parser)
        data427 = _t824
        _t825 = Proto.Declaration(declaration_type=OneOf(:data, data427))
        _t823 = _t825
    else
        if prediction423 == 2
            _t827 = parse_constraint(parser)
            constraint426 = _t827
            _t828 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint426))
            _t826 = _t828
        else
            if prediction423 == 1
                _t830 = parse_algorithm(parser)
                algorithm425 = _t830
                _t831 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm425))
                _t829 = _t831
            else
                if prediction423 == 0
                    _t833 = parse_def(parser)
                    def424 = _t833
                    _t834 = Proto.Declaration(declaration_type=OneOf(:def, def424))
                    _t832 = _t834
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t829 = _t832
            end
            _t826 = _t829
        end
        _t823 = _t826
    end
    return _t823
end

function parse_def(parser::ParserState)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t835 = parse_relation_id(parser)
    relation_id428 = _t835
    _t836 = parse_abstraction(parser)
    abstraction429 = _t836
    if match_lookahead_literal(parser, "(", 0)
        _t838 = parse_attrs(parser)
        _t837 = _t838
    else
        _t837 = nothing
    end
    attrs430 = _t837
    consume_literal!(parser, ")")
    _t839 = Proto.Def(name=relation_id428, body=abstraction429, attrs=(!isnothing(attrs430) ? attrs430 : Proto.Attribute[]))
    return _t839
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    if match_lookahead_literal(parser, ":", 0)
        _t840 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t841 = 1
        else
            _t841 = -1
        end
        _t840 = _t841
    end
    prediction431 = _t840
    if prediction431 == 1
        uint128433 = consume_terminal!(parser, "UINT128")
        _t842 = Proto.RelationId(uint128433.low, uint128433.high)
    else
        if prediction431 == 0
            consume_literal!(parser, ":")
            symbol432 = consume_terminal!(parser, "SYMBOL")
            _t843 = relation_id_from_string(parser, symbol432)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t842 = _t843
    end
    return _t842
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t844 = parse_bindings(parser)
    bindings434 = _t844
    _t845 = parse_formula(parser)
    formula435 = _t845
    consume_literal!(parser, ")")
    _t846 = Proto.Abstraction(vars=vcat(bindings434[1], !isnothing(bindings434[2]) ? bindings434[2] : []), value=formula435)
    return _t846
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs436 = Proto.Binding[]
    cond437 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond437
        _t847 = parse_binding(parser)
        item438 = _t847
        push!(xs436, item438)
        cond437 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings439 = xs436
    if match_lookahead_literal(parser, "|", 0)
        _t849 = parse_value_bindings(parser)
        _t848 = _t849
    else
        _t848 = nothing
    end
    value_bindings440 = _t848
    consume_literal!(parser, "]")
    return (bindings439, (!isnothing(value_bindings440) ? value_bindings440 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    symbol441 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t850 = parse_type(parser)
    type442 = _t850
    _t851 = Proto.Var(name=symbol441)
    _t852 = Proto.Binding(var=_t851, var"#type"=type442)
    return _t852
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t853 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t854 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t855 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t856 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t857 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t858 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t859 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t860 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t861 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t862 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t863 = 9
                                            else
                                                _t863 = -1
                                            end
                                            _t862 = _t863
                                        end
                                        _t861 = _t862
                                    end
                                    _t860 = _t861
                                end
                                _t859 = _t860
                            end
                            _t858 = _t859
                        end
                        _t857 = _t858
                    end
                    _t856 = _t857
                end
                _t855 = _t856
            end
            _t854 = _t855
        end
        _t853 = _t854
    end
    prediction443 = _t853
    if prediction443 == 10
        _t865 = parse_boolean_type(parser)
        boolean_type454 = _t865
        _t866 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type454))
        _t864 = _t866
    else
        if prediction443 == 9
            _t868 = parse_decimal_type(parser)
            decimal_type453 = _t868
            _t869 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type453))
            _t867 = _t869
        else
            if prediction443 == 8
                _t871 = parse_missing_type(parser)
                missing_type452 = _t871
                _t872 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type452))
                _t870 = _t872
            else
                if prediction443 == 7
                    _t874 = parse_datetime_type(parser)
                    datetime_type451 = _t874
                    _t875 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type451))
                    _t873 = _t875
                else
                    if prediction443 == 6
                        _t877 = parse_date_type(parser)
                        date_type450 = _t877
                        _t878 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type450))
                        _t876 = _t878
                    else
                        if prediction443 == 5
                            _t880 = parse_int128_type(parser)
                            int128_type449 = _t880
                            _t881 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type449))
                            _t879 = _t881
                        else
                            if prediction443 == 4
                                _t883 = parse_uint128_type(parser)
                                uint128_type448 = _t883
                                _t884 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type448))
                                _t882 = _t884
                            else
                                if prediction443 == 3
                                    _t886 = parse_float_type(parser)
                                    float_type447 = _t886
                                    _t887 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type447))
                                    _t885 = _t887
                                else
                                    if prediction443 == 2
                                        _t889 = parse_int_type(parser)
                                        int_type446 = _t889
                                        _t890 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type446))
                                        _t888 = _t890
                                    else
                                        if prediction443 == 1
                                            _t892 = parse_string_type(parser)
                                            string_type445 = _t892
                                            _t893 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type445))
                                            _t891 = _t893
                                        else
                                            if prediction443 == 0
                                                _t895 = parse_unspecified_type(parser)
                                                unspecified_type444 = _t895
                                                _t896 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type444))
                                                _t894 = _t896
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t891 = _t894
                                        end
                                        _t888 = _t891
                                    end
                                    _t885 = _t888
                                end
                                _t882 = _t885
                            end
                            _t879 = _t882
                        end
                        _t876 = _t879
                    end
                    _t873 = _t876
                end
                _t870 = _t873
            end
            _t867 = _t870
        end
        _t864 = _t867
    end
    return _t864
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t897 = Proto.UnspecifiedType()
    return _t897
end

function parse_string_type(parser::ParserState)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t898 = Proto.StringType()
    return _t898
end

function parse_int_type(parser::ParserState)::Proto.IntType
    consume_literal!(parser, "INT")
    _t899 = Proto.IntType()
    return _t899
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t900 = Proto.FloatType()
    return _t900
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t901 = Proto.UInt128Type()
    return _t901
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t902 = Proto.Int128Type()
    return _t902
end

function parse_date_type(parser::ParserState)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t903 = Proto.DateType()
    return _t903
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t904 = Proto.DateTimeType()
    return _t904
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t905 = Proto.MissingType()
    return _t905
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int455 = consume_terminal!(parser, "INT")
    int_3456 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t906 = Proto.DecimalType(precision=Int32(int455), scale=Int32(int_3456))
    return _t906
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t907 = Proto.BooleanType()
    return _t907
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs457 = Proto.Binding[]
    cond458 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond458
        _t908 = parse_binding(parser)
        item459 = _t908
        push!(xs457, item459)
        cond458 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings460 = xs457
    return bindings460
end

function parse_formula(parser::ParserState)::Proto.Formula
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t910 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t911 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t912 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t913 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t914 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t915 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t916 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t917 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t918 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t919 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t920 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t921 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t922 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t923 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t924 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t925 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t926 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t927 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t928 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t929 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t930 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t931 = 10
                                                                                            else
                                                                                                _t931 = -1
                                                                                            end
                                                                                            _t930 = _t931
                                                                                        end
                                                                                        _t929 = _t930
                                                                                    end
                                                                                    _t928 = _t929
                                                                                end
                                                                                _t927 = _t928
                                                                            end
                                                                            _t926 = _t927
                                                                        end
                                                                        _t925 = _t926
                                                                    end
                                                                    _t924 = _t925
                                                                end
                                                                _t923 = _t924
                                                            end
                                                            _t922 = _t923
                                                        end
                                                        _t921 = _t922
                                                    end
                                                    _t920 = _t921
                                                end
                                                _t919 = _t920
                                            end
                                            _t918 = _t919
                                        end
                                        _t917 = _t918
                                    end
                                    _t916 = _t917
                                end
                                _t915 = _t916
                            end
                            _t914 = _t915
                        end
                        _t913 = _t914
                    end
                    _t912 = _t913
                end
                _t911 = _t912
            end
            _t910 = _t911
        end
        _t909 = _t910
    else
        _t909 = -1
    end
    prediction461 = _t909
    if prediction461 == 12
        _t933 = parse_cast(parser)
        cast474 = _t933
        _t934 = Proto.Formula(formula_type=OneOf(:cast, cast474))
        _t932 = _t934
    else
        if prediction461 == 11
            _t936 = parse_rel_atom(parser)
            rel_atom473 = _t936
            _t937 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom473))
            _t935 = _t937
        else
            if prediction461 == 10
                _t939 = parse_primitive(parser)
                primitive472 = _t939
                _t940 = Proto.Formula(formula_type=OneOf(:primitive, primitive472))
                _t938 = _t940
            else
                if prediction461 == 9
                    _t942 = parse_pragma(parser)
                    pragma471 = _t942
                    _t943 = Proto.Formula(formula_type=OneOf(:pragma, pragma471))
                    _t941 = _t943
                else
                    if prediction461 == 8
                        _t945 = parse_atom(parser)
                        atom470 = _t945
                        _t946 = Proto.Formula(formula_type=OneOf(:atom, atom470))
                        _t944 = _t946
                    else
                        if prediction461 == 7
                            _t948 = parse_ffi(parser)
                            ffi469 = _t948
                            _t949 = Proto.Formula(formula_type=OneOf(:ffi, ffi469))
                            _t947 = _t949
                        else
                            if prediction461 == 6
                                _t951 = parse_not(parser)
                                not468 = _t951
                                _t952 = Proto.Formula(formula_type=OneOf(:not, not468))
                                _t950 = _t952
                            else
                                if prediction461 == 5
                                    _t954 = parse_disjunction(parser)
                                    disjunction467 = _t954
                                    _t955 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction467))
                                    _t953 = _t955
                                else
                                    if prediction461 == 4
                                        _t957 = parse_conjunction(parser)
                                        conjunction466 = _t957
                                        _t958 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction466))
                                        _t956 = _t958
                                    else
                                        if prediction461 == 3
                                            _t960 = parse_reduce(parser)
                                            reduce465 = _t960
                                            _t961 = Proto.Formula(formula_type=OneOf(:reduce, reduce465))
                                            _t959 = _t961
                                        else
                                            if prediction461 == 2
                                                _t963 = parse_exists(parser)
                                                exists464 = _t963
                                                _t964 = Proto.Formula(formula_type=OneOf(:exists, exists464))
                                                _t962 = _t964
                                            else
                                                if prediction461 == 1
                                                    _t966 = parse_false(parser)
                                                    false463 = _t966
                                                    _t967 = Proto.Formula(formula_type=OneOf(:disjunction, false463))
                                                    _t965 = _t967
                                                else
                                                    if prediction461 == 0
                                                        _t969 = parse_true(parser)
                                                        true462 = _t969
                                                        _t970 = Proto.Formula(formula_type=OneOf(:conjunction, true462))
                                                        _t968 = _t970
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t965 = _t968
                                                end
                                                _t962 = _t965
                                            end
                                            _t959 = _t962
                                        end
                                        _t956 = _t959
                                    end
                                    _t953 = _t956
                                end
                                _t950 = _t953
                            end
                            _t947 = _t950
                        end
                        _t944 = _t947
                    end
                    _t941 = _t944
                end
                _t938 = _t941
            end
            _t935 = _t938
        end
        _t932 = _t935
    end
    return _t932
end

function parse_true(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t971 = Proto.Conjunction(args=Proto.Formula[])
    return _t971
end

function parse_false(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t972 = Proto.Disjunction(args=Proto.Formula[])
    return _t972
end

function parse_exists(parser::ParserState)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t973 = parse_bindings(parser)
    bindings475 = _t973
    _t974 = parse_formula(parser)
    formula476 = _t974
    consume_literal!(parser, ")")
    _t975 = Proto.Abstraction(vars=vcat(bindings475[1], !isnothing(bindings475[2]) ? bindings475[2] : []), value=formula476)
    _t976 = Proto.Exists(body=_t975)
    return _t976
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t977 = parse_abstraction(parser)
    abstraction477 = _t977
    _t978 = parse_abstraction(parser)
    abstraction_3478 = _t978
    _t979 = parse_terms(parser)
    terms479 = _t979
    consume_literal!(parser, ")")
    _t980 = Proto.Reduce(op=abstraction477, body=abstraction_3478, terms=terms479)
    return _t980
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs480 = Proto.Term[]
    cond481 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond481
        _t981 = parse_term(parser)
        item482 = _t981
        push!(xs480, item482)
        cond481 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms483 = xs480
    consume_literal!(parser, ")")
    return terms483
end

function parse_term(parser::ParserState)::Proto.Term
    if match_lookahead_literal(parser, "true", 0)
        _t982 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t983 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t984 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t985 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t986 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t987 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t988 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t989 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t990 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t991 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t992 = 1
                                            else
                                                _t992 = -1
                                            end
                                            _t991 = _t992
                                        end
                                        _t990 = _t991
                                    end
                                    _t989 = _t990
                                end
                                _t988 = _t989
                            end
                            _t987 = _t988
                        end
                        _t986 = _t987
                    end
                    _t985 = _t986
                end
                _t984 = _t985
            end
            _t983 = _t984
        end
        _t982 = _t983
    end
    prediction484 = _t982
    if prediction484 == 1
        _t994 = parse_constant(parser)
        constant486 = _t994
        _t995 = Proto.Term(term_type=OneOf(:constant, constant486))
        _t993 = _t995
    else
        if prediction484 == 0
            _t997 = parse_var(parser)
            var485 = _t997
            _t998 = Proto.Term(term_type=OneOf(:var, var485))
            _t996 = _t998
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t993 = _t996
    end
    return _t993
end

function parse_var(parser::ParserState)::Proto.Var
    symbol487 = consume_terminal!(parser, "SYMBOL")
    _t999 = Proto.Var(name=symbol487)
    return _t999
end

function parse_constant(parser::ParserState)::Proto.Value
    _t1000 = parse_value(parser)
    value488 = _t1000
    return value488
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs489 = Proto.Formula[]
    cond490 = match_lookahead_literal(parser, "(", 0)
    while cond490
        _t1001 = parse_formula(parser)
        item491 = _t1001
        push!(xs489, item491)
        cond490 = match_lookahead_literal(parser, "(", 0)
    end
    formulas492 = xs489
    consume_literal!(parser, ")")
    _t1002 = Proto.Conjunction(args=formulas492)
    return _t1002
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs493 = Proto.Formula[]
    cond494 = match_lookahead_literal(parser, "(", 0)
    while cond494
        _t1003 = parse_formula(parser)
        item495 = _t1003
        push!(xs493, item495)
        cond494 = match_lookahead_literal(parser, "(", 0)
    end
    formulas496 = xs493
    consume_literal!(parser, ")")
    _t1004 = Proto.Disjunction(args=formulas496)
    return _t1004
end

function parse_not(parser::ParserState)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1005 = parse_formula(parser)
    formula497 = _t1005
    consume_literal!(parser, ")")
    _t1006 = Proto.Not(arg=formula497)
    return _t1006
end

function parse_ffi(parser::ParserState)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1007 = parse_name(parser)
    name498 = _t1007
    _t1008 = parse_ffi_args(parser)
    ffi_args499 = _t1008
    _t1009 = parse_terms(parser)
    terms500 = _t1009
    consume_literal!(parser, ")")
    _t1010 = Proto.FFI(name=name498, args=ffi_args499, terms=terms500)
    return _t1010
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol501 = consume_terminal!(parser, "SYMBOL")
    return symbol501
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs502 = Proto.Abstraction[]
    cond503 = match_lookahead_literal(parser, "(", 0)
    while cond503
        _t1011 = parse_abstraction(parser)
        item504 = _t1011
        push!(xs502, item504)
        cond503 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions505 = xs502
    consume_literal!(parser, ")")
    return abstractions505
end

function parse_atom(parser::ParserState)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1012 = parse_relation_id(parser)
    relation_id506 = _t1012
    xs507 = Proto.Term[]
    cond508 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond508
        _t1013 = parse_term(parser)
        item509 = _t1013
        push!(xs507, item509)
        cond508 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms510 = xs507
    consume_literal!(parser, ")")
    _t1014 = Proto.Atom(name=relation_id506, terms=terms510)
    return _t1014
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1015 = parse_name(parser)
    name511 = _t1015
    xs512 = Proto.Term[]
    cond513 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond513
        _t1016 = parse_term(parser)
        item514 = _t1016
        push!(xs512, item514)
        cond513 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms515 = xs512
    consume_literal!(parser, ")")
    _t1017 = Proto.Pragma(name=name511, terms=terms515)
    return _t1017
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1019 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1020 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1021 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1022 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1023 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1024 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1025 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1026 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1027 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1028 = 7
                                            else
                                                _t1028 = -1
                                            end
                                            _t1027 = _t1028
                                        end
                                        _t1026 = _t1027
                                    end
                                    _t1025 = _t1026
                                end
                                _t1024 = _t1025
                            end
                            _t1023 = _t1024
                        end
                        _t1022 = _t1023
                    end
                    _t1021 = _t1022
                end
                _t1020 = _t1021
            end
            _t1019 = _t1020
        end
        _t1018 = _t1019
    else
        _t1018 = -1
    end
    prediction516 = _t1018
    if prediction516 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1030 = parse_name(parser)
        name526 = _t1030
        xs527 = Proto.RelTerm[]
        cond528 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond528
            _t1031 = parse_rel_term(parser)
            item529 = _t1031
            push!(xs527, item529)
            cond528 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms530 = xs527
        consume_literal!(parser, ")")
        _t1032 = Proto.Primitive(name=name526, terms=rel_terms530)
        _t1029 = _t1032
    else
        if prediction516 == 8
            _t1034 = parse_divide(parser)
            divide525 = _t1034
            _t1033 = divide525
        else
            if prediction516 == 7
                _t1036 = parse_multiply(parser)
                multiply524 = _t1036
                _t1035 = multiply524
            else
                if prediction516 == 6
                    _t1038 = parse_minus(parser)
                    minus523 = _t1038
                    _t1037 = minus523
                else
                    if prediction516 == 5
                        _t1040 = parse_add(parser)
                        add522 = _t1040
                        _t1039 = add522
                    else
                        if prediction516 == 4
                            _t1042 = parse_gt_eq(parser)
                            gt_eq521 = _t1042
                            _t1041 = gt_eq521
                        else
                            if prediction516 == 3
                                _t1044 = parse_gt(parser)
                                gt520 = _t1044
                                _t1043 = gt520
                            else
                                if prediction516 == 2
                                    _t1046 = parse_lt_eq(parser)
                                    lt_eq519 = _t1046
                                    _t1045 = lt_eq519
                                else
                                    if prediction516 == 1
                                        _t1048 = parse_lt(parser)
                                        lt518 = _t1048
                                        _t1047 = lt518
                                    else
                                        if prediction516 == 0
                                            _t1050 = parse_eq(parser)
                                            eq517 = _t1050
                                            _t1049 = eq517
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1047 = _t1049
                                    end
                                    _t1045 = _t1047
                                end
                                _t1043 = _t1045
                            end
                            _t1041 = _t1043
                        end
                        _t1039 = _t1041
                    end
                    _t1037 = _t1039
                end
                _t1035 = _t1037
            end
            _t1033 = _t1035
        end
        _t1029 = _t1033
    end
    return _t1029
end

function parse_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1051 = parse_term(parser)
    term531 = _t1051
    _t1052 = parse_term(parser)
    term_3532 = _t1052
    consume_literal!(parser, ")")
    _t1053 = Proto.RelTerm(rel_term_type=OneOf(:term, term531))
    _t1054 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3532))
    _t1055 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1053, _t1054])
    return _t1055
end

function parse_lt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1056 = parse_term(parser)
    term533 = _t1056
    _t1057 = parse_term(parser)
    term_3534 = _t1057
    consume_literal!(parser, ")")
    _t1058 = Proto.RelTerm(rel_term_type=OneOf(:term, term533))
    _t1059 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3534))
    _t1060 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1058, _t1059])
    return _t1060
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1061 = parse_term(parser)
    term535 = _t1061
    _t1062 = parse_term(parser)
    term_3536 = _t1062
    consume_literal!(parser, ")")
    _t1063 = Proto.RelTerm(rel_term_type=OneOf(:term, term535))
    _t1064 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3536))
    _t1065 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1063, _t1064])
    return _t1065
end

function parse_gt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1066 = parse_term(parser)
    term537 = _t1066
    _t1067 = parse_term(parser)
    term_3538 = _t1067
    consume_literal!(parser, ")")
    _t1068 = Proto.RelTerm(rel_term_type=OneOf(:term, term537))
    _t1069 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3538))
    _t1070 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1068, _t1069])
    return _t1070
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1071 = parse_term(parser)
    term539 = _t1071
    _t1072 = parse_term(parser)
    term_3540 = _t1072
    consume_literal!(parser, ")")
    _t1073 = Proto.RelTerm(rel_term_type=OneOf(:term, term539))
    _t1074 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3540))
    _t1075 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1073, _t1074])
    return _t1075
end

function parse_add(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1076 = parse_term(parser)
    term541 = _t1076
    _t1077 = parse_term(parser)
    term_3542 = _t1077
    _t1078 = parse_term(parser)
    term_4543 = _t1078
    consume_literal!(parser, ")")
    _t1079 = Proto.RelTerm(rel_term_type=OneOf(:term, term541))
    _t1080 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3542))
    _t1081 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4543))
    _t1082 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1079, _t1080, _t1081])
    return _t1082
end

function parse_minus(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1083 = parse_term(parser)
    term544 = _t1083
    _t1084 = parse_term(parser)
    term_3545 = _t1084
    _t1085 = parse_term(parser)
    term_4546 = _t1085
    consume_literal!(parser, ")")
    _t1086 = Proto.RelTerm(rel_term_type=OneOf(:term, term544))
    _t1087 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3545))
    _t1088 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4546))
    _t1089 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1086, _t1087, _t1088])
    return _t1089
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1090 = parse_term(parser)
    term547 = _t1090
    _t1091 = parse_term(parser)
    term_3548 = _t1091
    _t1092 = parse_term(parser)
    term_4549 = _t1092
    consume_literal!(parser, ")")
    _t1093 = Proto.RelTerm(rel_term_type=OneOf(:term, term547))
    _t1094 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3548))
    _t1095 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4549))
    _t1096 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1093, _t1094, _t1095])
    return _t1096
end

function parse_divide(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1097 = parse_term(parser)
    term550 = _t1097
    _t1098 = parse_term(parser)
    term_3551 = _t1098
    _t1099 = parse_term(parser)
    term_4552 = _t1099
    consume_literal!(parser, ")")
    _t1100 = Proto.RelTerm(rel_term_type=OneOf(:term, term550))
    _t1101 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3551))
    _t1102 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4552))
    _t1103 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1100, _t1101, _t1102])
    return _t1103
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    if match_lookahead_literal(parser, "true", 0)
        _t1104 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1105 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1106 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1107 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1108 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1109 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1110 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1111 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1112 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1113 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1114 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1115 = 1
                                                else
                                                    _t1115 = -1
                                                end
                                                _t1114 = _t1115
                                            end
                                            _t1113 = _t1114
                                        end
                                        _t1112 = _t1113
                                    end
                                    _t1111 = _t1112
                                end
                                _t1110 = _t1111
                            end
                            _t1109 = _t1110
                        end
                        _t1108 = _t1109
                    end
                    _t1107 = _t1108
                end
                _t1106 = _t1107
            end
            _t1105 = _t1106
        end
        _t1104 = _t1105
    end
    prediction553 = _t1104
    if prediction553 == 1
        _t1117 = parse_term(parser)
        term555 = _t1117
        _t1118 = Proto.RelTerm(rel_term_type=OneOf(:term, term555))
        _t1116 = _t1118
    else
        if prediction553 == 0
            _t1120 = parse_specialized_value(parser)
            specialized_value554 = _t1120
            _t1121 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value554))
            _t1119 = _t1121
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1116 = _t1119
    end
    return _t1116
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    consume_literal!(parser, "#")
    _t1122 = parse_value(parser)
    value556 = _t1122
    return value556
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1123 = parse_name(parser)
    name557 = _t1123
    xs558 = Proto.RelTerm[]
    cond559 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond559
        _t1124 = parse_rel_term(parser)
        item560 = _t1124
        push!(xs558, item560)
        cond559 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms561 = xs558
    consume_literal!(parser, ")")
    _t1125 = Proto.RelAtom(name=name557, terms=rel_terms561)
    return _t1125
end

function parse_cast(parser::ParserState)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1126 = parse_term(parser)
    term562 = _t1126
    _t1127 = parse_term(parser)
    term_3563 = _t1127
    consume_literal!(parser, ")")
    _t1128 = Proto.Cast(input=term562, result=term_3563)
    return _t1128
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs564 = Proto.Attribute[]
    cond565 = match_lookahead_literal(parser, "(", 0)
    while cond565
        _t1129 = parse_attribute(parser)
        item566 = _t1129
        push!(xs564, item566)
        cond565 = match_lookahead_literal(parser, "(", 0)
    end
    attributes567 = xs564
    consume_literal!(parser, ")")
    return attributes567
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1130 = parse_name(parser)
    name568 = _t1130
    xs569 = Proto.Value[]
    cond570 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond570
        _t1131 = parse_value(parser)
        item571 = _t1131
        push!(xs569, item571)
        cond570 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values572 = xs569
    consume_literal!(parser, ")")
    _t1132 = Proto.Attribute(name=name568, args=values572)
    return _t1132
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs573 = Proto.RelationId[]
    cond574 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond574
        _t1133 = parse_relation_id(parser)
        item575 = _t1133
        push!(xs573, item575)
        cond574 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids576 = xs573
    _t1134 = parse_script(parser)
    script577 = _t1134
    consume_literal!(parser, ")")
    _t1135 = Proto.Algorithm(var"#global"=relation_ids576, body=script577)
    return _t1135
end

function parse_script(parser::ParserState)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs578 = Proto.Construct[]
    cond579 = match_lookahead_literal(parser, "(", 0)
    while cond579
        _t1136 = parse_construct(parser)
        item580 = _t1136
        push!(xs578, item580)
        cond579 = match_lookahead_literal(parser, "(", 0)
    end
    constructs581 = xs578
    consume_literal!(parser, ")")
    _t1137 = Proto.Script(constructs=constructs581)
    return _t1137
end

function parse_construct(parser::ParserState)::Proto.Construct
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1139 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1140 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1141 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1142 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1143 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1144 = 1
                            else
                                _t1144 = -1
                            end
                            _t1143 = _t1144
                        end
                        _t1142 = _t1143
                    end
                    _t1141 = _t1142
                end
                _t1140 = _t1141
            end
            _t1139 = _t1140
        end
        _t1138 = _t1139
    else
        _t1138 = -1
    end
    prediction582 = _t1138
    if prediction582 == 1
        _t1146 = parse_instruction(parser)
        instruction584 = _t1146
        _t1147 = Proto.Construct(construct_type=OneOf(:instruction, instruction584))
        _t1145 = _t1147
    else
        if prediction582 == 0
            _t1149 = parse_loop(parser)
            loop583 = _t1149
            _t1150 = Proto.Construct(construct_type=OneOf(:loop, loop583))
            _t1148 = _t1150
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1145 = _t1148
    end
    return _t1145
end

function parse_loop(parser::ParserState)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1151 = parse_init(parser)
    init585 = _t1151
    _t1152 = parse_script(parser)
    script586 = _t1152
    consume_literal!(parser, ")")
    _t1153 = Proto.Loop(init=init585, body=script586)
    return _t1153
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs587 = Proto.Instruction[]
    cond588 = match_lookahead_literal(parser, "(", 0)
    while cond588
        _t1154 = parse_instruction(parser)
        item589 = _t1154
        push!(xs587, item589)
        cond588 = match_lookahead_literal(parser, "(", 0)
    end
    instructions590 = xs587
    consume_literal!(parser, ")")
    return instructions590
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1156 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1157 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1158 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1159 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1160 = 0
                        else
                            _t1160 = -1
                        end
                        _t1159 = _t1160
                    end
                    _t1158 = _t1159
                end
                _t1157 = _t1158
            end
            _t1156 = _t1157
        end
        _t1155 = _t1156
    else
        _t1155 = -1
    end
    prediction591 = _t1155
    if prediction591 == 4
        _t1162 = parse_monus_def(parser)
        monus_def596 = _t1162
        _t1163 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def596))
        _t1161 = _t1163
    else
        if prediction591 == 3
            _t1165 = parse_monoid_def(parser)
            monoid_def595 = _t1165
            _t1166 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def595))
            _t1164 = _t1166
        else
            if prediction591 == 2
                _t1168 = parse_break(parser)
                break594 = _t1168
                _t1169 = Proto.Instruction(instr_type=OneOf(:var"#break", break594))
                _t1167 = _t1169
            else
                if prediction591 == 1
                    _t1171 = parse_upsert(parser)
                    upsert593 = _t1171
                    _t1172 = Proto.Instruction(instr_type=OneOf(:upsert, upsert593))
                    _t1170 = _t1172
                else
                    if prediction591 == 0
                        _t1174 = parse_assign(parser)
                        assign592 = _t1174
                        _t1175 = Proto.Instruction(instr_type=OneOf(:assign, assign592))
                        _t1173 = _t1175
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1170 = _t1173
                end
                _t1167 = _t1170
            end
            _t1164 = _t1167
        end
        _t1161 = _t1164
    end
    return _t1161
end

function parse_assign(parser::ParserState)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1176 = parse_relation_id(parser)
    relation_id597 = _t1176
    _t1177 = parse_abstraction(parser)
    abstraction598 = _t1177
    if match_lookahead_literal(parser, "(", 0)
        _t1179 = parse_attrs(parser)
        _t1178 = _t1179
    else
        _t1178 = nothing
    end
    attrs599 = _t1178
    consume_literal!(parser, ")")
    _t1180 = Proto.Assign(name=relation_id597, body=abstraction598, attrs=(!isnothing(attrs599) ? attrs599 : Proto.Attribute[]))
    return _t1180
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1181 = parse_relation_id(parser)
    relation_id600 = _t1181
    _t1182 = parse_abstraction_with_arity(parser)
    abstraction_with_arity601 = _t1182
    if match_lookahead_literal(parser, "(", 0)
        _t1184 = parse_attrs(parser)
        _t1183 = _t1184
    else
        _t1183 = nothing
    end
    attrs602 = _t1183
    consume_literal!(parser, ")")
    _t1185 = Proto.Upsert(name=relation_id600, body=abstraction_with_arity601[1], attrs=(!isnothing(attrs602) ? attrs602 : Proto.Attribute[]), value_arity=abstraction_with_arity601[2])
    return _t1185
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1186 = parse_bindings(parser)
    bindings603 = _t1186
    _t1187 = parse_formula(parser)
    formula604 = _t1187
    consume_literal!(parser, ")")
    _t1188 = Proto.Abstraction(vars=vcat(bindings603[1], !isnothing(bindings603[2]) ? bindings603[2] : []), value=formula604)
    return (_t1188, length(bindings603[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1189 = parse_relation_id(parser)
    relation_id605 = _t1189
    _t1190 = parse_abstraction(parser)
    abstraction606 = _t1190
    if match_lookahead_literal(parser, "(", 0)
        _t1192 = parse_attrs(parser)
        _t1191 = _t1192
    else
        _t1191 = nothing
    end
    attrs607 = _t1191
    consume_literal!(parser, ")")
    _t1193 = Proto.Break(name=relation_id605, body=abstraction606, attrs=(!isnothing(attrs607) ? attrs607 : Proto.Attribute[]))
    return _t1193
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1194 = parse_monoid(parser)
    monoid608 = _t1194
    _t1195 = parse_relation_id(parser)
    relation_id609 = _t1195
    _t1196 = parse_abstraction_with_arity(parser)
    abstraction_with_arity610 = _t1196
    if match_lookahead_literal(parser, "(", 0)
        _t1198 = parse_attrs(parser)
        _t1197 = _t1198
    else
        _t1197 = nothing
    end
    attrs611 = _t1197
    consume_literal!(parser, ")")
    _t1199 = Proto.MonoidDef(monoid=monoid608, name=relation_id609, body=abstraction_with_arity610[1], attrs=(!isnothing(attrs611) ? attrs611 : Proto.Attribute[]), value_arity=abstraction_with_arity610[2])
    return _t1199
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1201 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1202 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1203 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1204 = 2
                    else
                        _t1204 = -1
                    end
                    _t1203 = _t1204
                end
                _t1202 = _t1203
            end
            _t1201 = _t1202
        end
        _t1200 = _t1201
    else
        _t1200 = -1
    end
    prediction612 = _t1200
    if prediction612 == 3
        _t1206 = parse_sum_monoid(parser)
        sum_monoid616 = _t1206
        _t1207 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid616))
        _t1205 = _t1207
    else
        if prediction612 == 2
            _t1209 = parse_max_monoid(parser)
            max_monoid615 = _t1209
            _t1210 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid615))
            _t1208 = _t1210
        else
            if prediction612 == 1
                _t1212 = parse_min_monoid(parser)
                min_monoid614 = _t1212
                _t1213 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid614))
                _t1211 = _t1213
            else
                if prediction612 == 0
                    _t1215 = parse_or_monoid(parser)
                    or_monoid613 = _t1215
                    _t1216 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid613))
                    _t1214 = _t1216
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1211 = _t1214
            end
            _t1208 = _t1211
        end
        _t1205 = _t1208
    end
    return _t1205
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1217 = Proto.OrMonoid()
    return _t1217
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1218 = parse_type(parser)
    type617 = _t1218
    consume_literal!(parser, ")")
    _t1219 = Proto.MinMonoid(var"#type"=type617)
    return _t1219
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1220 = parse_type(parser)
    type618 = _t1220
    consume_literal!(parser, ")")
    _t1221 = Proto.MaxMonoid(var"#type"=type618)
    return _t1221
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1222 = parse_type(parser)
    type619 = _t1222
    consume_literal!(parser, ")")
    _t1223 = Proto.SumMonoid(var"#type"=type619)
    return _t1223
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1224 = parse_monoid(parser)
    monoid620 = _t1224
    _t1225 = parse_relation_id(parser)
    relation_id621 = _t1225
    _t1226 = parse_abstraction_with_arity(parser)
    abstraction_with_arity622 = _t1226
    if match_lookahead_literal(parser, "(", 0)
        _t1228 = parse_attrs(parser)
        _t1227 = _t1228
    else
        _t1227 = nothing
    end
    attrs623 = _t1227
    consume_literal!(parser, ")")
    _t1229 = Proto.MonusDef(monoid=monoid620, name=relation_id621, body=abstraction_with_arity622[1], attrs=(!isnothing(attrs623) ? attrs623 : Proto.Attribute[]), value_arity=abstraction_with_arity622[2])
    return _t1229
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1230 = parse_relation_id(parser)
    relation_id624 = _t1230
    _t1231 = parse_abstraction(parser)
    abstraction625 = _t1231
    _t1232 = parse_functional_dependency_keys(parser)
    functional_dependency_keys626 = _t1232
    _t1233 = parse_functional_dependency_values(parser)
    functional_dependency_values627 = _t1233
    consume_literal!(parser, ")")
    _t1234 = Proto.FunctionalDependency(guard=abstraction625, keys=functional_dependency_keys626, values=functional_dependency_values627)
    _t1235 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1234), name=relation_id624)
    return _t1235
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs628 = Proto.Var[]
    cond629 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond629
        _t1236 = parse_var(parser)
        item630 = _t1236
        push!(xs628, item630)
        cond629 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars631 = xs628
    consume_literal!(parser, ")")
    return vars631
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs632 = Proto.Var[]
    cond633 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond633
        _t1237 = parse_var(parser)
        item634 = _t1237
        push!(xs632, item634)
        cond633 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars635 = xs632
    consume_literal!(parser, ")")
    return vars635
end

function parse_data(parser::ParserState)::Proto.Data
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1239 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1240 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1241 = 1
                else
                    _t1241 = -1
                end
                _t1240 = _t1241
            end
            _t1239 = _t1240
        end
        _t1238 = _t1239
    else
        _t1238 = -1
    end
    prediction636 = _t1238
    if prediction636 == 2
        _t1243 = parse_csv_data(parser)
        csv_data639 = _t1243
        _t1244 = Proto.Data(data_type=OneOf(:csv_data, csv_data639))
        _t1242 = _t1244
    else
        if prediction636 == 1
            _t1246 = parse_betree_relation(parser)
            betree_relation638 = _t1246
            _t1247 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation638))
            _t1245 = _t1247
        else
            if prediction636 == 0
                _t1249 = parse_rel_edb(parser)
                rel_edb637 = _t1249
                _t1250 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb637))
                _t1248 = _t1250
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1245 = _t1248
        end
        _t1242 = _t1245
    end
    return _t1242
end

function parse_rel_edb(parser::ParserState)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t1251 = parse_relation_id(parser)
    relation_id640 = _t1251
    _t1252 = parse_rel_edb_path(parser)
    rel_edb_path641 = _t1252
    _t1253 = parse_rel_edb_types(parser)
    rel_edb_types642 = _t1253
    consume_literal!(parser, ")")
    _t1254 = Proto.RelEDB(target_id=relation_id640, path=rel_edb_path641, types=rel_edb_types642)
    return _t1254
end

function parse_rel_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs643 = String[]
    cond644 = match_lookahead_terminal(parser, "STRING", 0)
    while cond644
        item645 = consume_terminal!(parser, "STRING")
        push!(xs643, item645)
        cond644 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings646 = xs643
    consume_literal!(parser, "]")
    return strings646
end

function parse_rel_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs647 = Proto.var"#Type"[]
    cond648 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond648
        _t1255 = parse_type(parser)
        item649 = _t1255
        push!(xs647, item649)
        cond648 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types650 = xs647
    consume_literal!(parser, "]")
    return types650
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1256 = parse_relation_id(parser)
    relation_id651 = _t1256
    _t1257 = parse_betree_info(parser)
    betree_info652 = _t1257
    consume_literal!(parser, ")")
    _t1258 = Proto.BeTreeRelation(name=relation_id651, relation_info=betree_info652)
    return _t1258
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1259 = parse_betree_info_key_types(parser)
    betree_info_key_types653 = _t1259
    _t1260 = parse_betree_info_value_types(parser)
    betree_info_value_types654 = _t1260
    _t1261 = parse_config_dict(parser)
    config_dict655 = _t1261
    consume_literal!(parser, ")")
    _t1262 = construct_betree_info(parser, betree_info_key_types653, betree_info_value_types654, config_dict655)
    return _t1262
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs656 = Proto.var"#Type"[]
    cond657 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond657
        _t1263 = parse_type(parser)
        item658 = _t1263
        push!(xs656, item658)
        cond657 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types659 = xs656
    consume_literal!(parser, ")")
    return types659
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs660 = Proto.var"#Type"[]
    cond661 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond661
        _t1264 = parse_type(parser)
        item662 = _t1264
        push!(xs660, item662)
        cond661 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types663 = xs660
    consume_literal!(parser, ")")
    return types663
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1265 = parse_csvlocator(parser)
    csvlocator664 = _t1265
    _t1266 = parse_csv_config(parser)
    csv_config665 = _t1266
    _t1267 = parse_csv_columns(parser)
    csv_columns666 = _t1267
    _t1268 = parse_csv_asof(parser)
    csv_asof667 = _t1268
    consume_literal!(parser, ")")
    _t1269 = Proto.CSVData(locator=csvlocator664, config=csv_config665, columns=csv_columns666, asof=csv_asof667)
    return _t1269
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1271 = parse_csv_locator_paths(parser)
        _t1270 = _t1271
    else
        _t1270 = nothing
    end
    csv_locator_paths668 = _t1270
    if match_lookahead_literal(parser, "(", 0)
        _t1273 = parse_csv_locator_inline_data(parser)
        _t1272 = _t1273
    else
        _t1272 = nothing
    end
    csv_locator_inline_data669 = _t1272
    consume_literal!(parser, ")")
    _t1274 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths668) ? csv_locator_paths668 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data669) ? csv_locator_inline_data669 : "")))
    return _t1274
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs670 = String[]
    cond671 = match_lookahead_terminal(parser, "STRING", 0)
    while cond671
        item672 = consume_terminal!(parser, "STRING")
        push!(xs670, item672)
        cond671 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings673 = xs670
    consume_literal!(parser, ")")
    return strings673
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string674 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string674
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1275 = parse_config_dict(parser)
    config_dict675 = _t1275
    consume_literal!(parser, ")")
    _t1276 = construct_csv_config(parser, config_dict675)
    return _t1276
end

function parse_csv_columns(parser::ParserState)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs676 = Proto.CSVColumn[]
    cond677 = match_lookahead_literal(parser, "(", 0)
    while cond677
        _t1277 = parse_csv_column(parser)
        item678 = _t1277
        push!(xs676, item678)
        cond677 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns679 = xs676
    consume_literal!(parser, ")")
    return csv_columns679
end

function parse_csv_column(parser::ParserState)::Proto.CSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string680 = consume_terminal!(parser, "STRING")
    _t1278 = parse_relation_id(parser)
    relation_id681 = _t1278
    consume_literal!(parser, "[")
    xs682 = Proto.var"#Type"[]
    cond683 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond683
        _t1279 = parse_type(parser)
        item684 = _t1279
        push!(xs682, item684)
        cond683 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types685 = xs682
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1280 = Proto.CSVColumn(column_name=string680, target_id=relation_id681, types=types685)
    return _t1280
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string686 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string686
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1281 = parse_fragment_id(parser)
    fragment_id687 = _t1281
    consume_literal!(parser, ")")
    _t1282 = Proto.Undefine(fragment_id=fragment_id687)
    return _t1282
end

function parse_context(parser::ParserState)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs688 = Proto.RelationId[]
    cond689 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond689
        _t1283 = parse_relation_id(parser)
        item690 = _t1283
        push!(xs688, item690)
        cond689 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids691 = xs688
    consume_literal!(parser, ")")
    _t1284 = Proto.Context(relations=relation_ids691)
    return _t1284
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t1285 = parse_rel_edb_path(parser)
    rel_edb_path692 = _t1285
    _t1286 = parse_relation_id(parser)
    relation_id693 = _t1286
    consume_literal!(parser, ")")
    _t1287 = Proto.Snapshot(destination_path=rel_edb_path692, source_relation=relation_id693)
    return _t1287
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs694 = Proto.Read[]
    cond695 = match_lookahead_literal(parser, "(", 0)
    while cond695
        _t1288 = parse_read(parser)
        item696 = _t1288
        push!(xs694, item696)
        cond695 = match_lookahead_literal(parser, "(", 0)
    end
    reads697 = xs694
    consume_literal!(parser, ")")
    return reads697
end

function parse_read(parser::ParserState)::Proto.Read
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1290 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1291 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1292 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1293 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1294 = 3
                        else
                            _t1294 = -1
                        end
                        _t1293 = _t1294
                    end
                    _t1292 = _t1293
                end
                _t1291 = _t1292
            end
            _t1290 = _t1291
        end
        _t1289 = _t1290
    else
        _t1289 = -1
    end
    prediction698 = _t1289
    if prediction698 == 4
        _t1296 = parse_export(parser)
        export703 = _t1296
        _t1297 = Proto.Read(read_type=OneOf(:var"#export", export703))
        _t1295 = _t1297
    else
        if prediction698 == 3
            _t1299 = parse_abort(parser)
            abort702 = _t1299
            _t1300 = Proto.Read(read_type=OneOf(:abort, abort702))
            _t1298 = _t1300
        else
            if prediction698 == 2
                _t1302 = parse_what_if(parser)
                what_if701 = _t1302
                _t1303 = Proto.Read(read_type=OneOf(:what_if, what_if701))
                _t1301 = _t1303
            else
                if prediction698 == 1
                    _t1305 = parse_output(parser)
                    output700 = _t1305
                    _t1306 = Proto.Read(read_type=OneOf(:output, output700))
                    _t1304 = _t1306
                else
                    if prediction698 == 0
                        _t1308 = parse_demand(parser)
                        demand699 = _t1308
                        _t1309 = Proto.Read(read_type=OneOf(:demand, demand699))
                        _t1307 = _t1309
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1304 = _t1307
                end
                _t1301 = _t1304
            end
            _t1298 = _t1301
        end
        _t1295 = _t1298
    end
    return _t1295
end

function parse_demand(parser::ParserState)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1310 = parse_relation_id(parser)
    relation_id704 = _t1310
    consume_literal!(parser, ")")
    _t1311 = Proto.Demand(relation_id=relation_id704)
    return _t1311
end

function parse_output(parser::ParserState)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1312 = parse_name(parser)
    name705 = _t1312
    _t1313 = parse_relation_id(parser)
    relation_id706 = _t1313
    consume_literal!(parser, ")")
    _t1314 = Proto.Output(name=name705, relation_id=relation_id706)
    return _t1314
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1315 = parse_name(parser)
    name707 = _t1315
    _t1316 = parse_epoch(parser)
    epoch708 = _t1316
    consume_literal!(parser, ")")
    _t1317 = Proto.WhatIf(branch=name707, epoch=epoch708)
    return _t1317
end

function parse_abort(parser::ParserState)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1319 = parse_name(parser)
        _t1318 = _t1319
    else
        _t1318 = nothing
    end
    name709 = _t1318
    _t1320 = parse_relation_id(parser)
    relation_id710 = _t1320
    consume_literal!(parser, ")")
    _t1321 = Proto.Abort(name=(!isnothing(name709) ? name709 : "abort"), relation_id=relation_id710)
    return _t1321
end

function parse_export(parser::ParserState)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1322 = parse_export_csv_config(parser)
    export_csv_config711 = _t1322
    consume_literal!(parser, ")")
    _t1323 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config711))
    return _t1323
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1325 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1326 = 1
            else
                _t1326 = -1
            end
            _t1325 = _t1326
        end
        _t1324 = _t1325
    else
        _t1324 = -1
    end
    prediction712 = _t1324
    if prediction712 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1328 = parse_export_csv_path(parser)
        export_csv_path716 = _t1328
        _t1329 = parse_export_csv_columns(parser)
        export_csv_columns717 = _t1329
        _t1330 = parse_config_dict(parser)
        config_dict718 = _t1330
        consume_literal!(parser, ")")
        _t1331 = construct_export_csv_config(parser, export_csv_path716, export_csv_columns717, config_dict718)
        _t1327 = _t1331
    else
        if prediction712 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1333 = parse_export_csv_path(parser)
            export_csv_path713 = _t1333
            _t1334 = parse_export_csv_source(parser)
            export_csv_source714 = _t1334
            _t1335 = parse_csv_config(parser)
            csv_config715 = _t1335
            consume_literal!(parser, ")")
            _t1336 = construct_export_csv_config_with_source(parser, export_csv_path713, export_csv_source714, csv_config715)
            _t1332 = _t1336
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1327 = _t1332
    end
    return _t1327
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string719 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string719
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1338 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1339 = 0
            else
                _t1339 = -1
            end
            _t1338 = _t1339
        end
        _t1337 = _t1338
    else
        _t1337 = -1
    end
    prediction720 = _t1337
    if prediction720 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1341 = parse_relation_id(parser)
        relation_id725 = _t1341
        consume_literal!(parser, ")")
        _t1342 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id725))
        _t1340 = _t1342
    else
        if prediction720 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs721 = Proto.ExportCSVColumn[]
            cond722 = match_lookahead_literal(parser, "(", 0)
            while cond722
                _t1344 = parse_export_csv_column(parser)
                item723 = _t1344
                push!(xs721, item723)
                cond722 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns724 = xs721
            consume_literal!(parser, ")")
            _t1345 = Proto.ExportCSVColumns(columns=export_csv_columns724)
            _t1346 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1345))
            _t1343 = _t1346
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1340 = _t1343
    end
    return _t1340
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string726 = consume_terminal!(parser, "STRING")
    _t1347 = parse_relation_id(parser)
    relation_id727 = _t1347
    consume_literal!(parser, ")")
    _t1348 = Proto.ExportCSVColumn(column_name=string726, column_data=relation_id727)
    return _t1348
end

function parse_export_csv_columns(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs728 = Proto.ExportCSVColumn[]
    cond729 = match_lookahead_literal(parser, "(", 0)
    while cond729
        _t1349 = parse_export_csv_column(parser)
        item730 = _t1349
        push!(xs728, item730)
        cond729 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns731 = xs728
    consume_literal!(parser, ")")
    return export_csv_columns731
end


function parse(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens)
    result = parse_transaction(parser)
    # Check for unconsumed tokens (except EOF)
    if parser.pos <= length(parser.tokens)
        remaining_token = lookahead(parser, 0)
        if remaining_token.type != "\$"
            throw(ParseError("Unexpected token at end of input: $remaining_token"))
        end
    end
    return result
end

# Export main parse function and error type
export parse, ParseError
# Export scanner functions for testing
export scan_string, scan_int, scan_float, scan_int128, scan_uint128, scan_decimal
# Export Lexer for testing
export Lexer

end # module Parser
