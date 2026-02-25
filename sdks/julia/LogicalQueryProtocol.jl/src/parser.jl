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
        _t1348 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1349 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1350 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1351 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1352 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1353 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1354 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1355 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1356 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1357 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1357
    _t1358 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1358
    _t1359 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1359
    _t1360 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1360
    _t1361 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1361
    _t1362 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1362
    _t1363 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1363
    _t1364 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1364
    _t1365 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1365
    _t1366 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1366
    _t1367 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1367
    _t1368 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1368
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1369 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1369
    _t1370 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1370
    _t1371 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1371
    _t1372 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1372
    _t1373 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1373
    _t1374 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1374
    _t1375 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1375
    _t1376 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1376
    _t1377 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1377
    _t1378 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1378
    _t1379 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1379
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1380 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1380
    _t1381 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1381
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
    _t1382 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1382
    _t1383 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1383
    _t1384 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1384
end

function export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1385 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1385
    _t1386 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1386
    _t1387 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1387
    _t1388 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1388
    _t1389 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1389
    _t1390 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1390
    _t1391 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1391
    _t1392 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1392
end

function construct_csv_column(parser::ParserState, path::Vector{String}, tail::Union{Nothing, Tuple{Union{Nothing, Proto.RelationId}, Vector{Proto.var"#Type"}}})::Proto.CSVColumn
    if !isnothing(tail)
        t = tail
        _t1394 = Proto.CSVColumn(column_path=path, target_id=t[1], types=t[2])
        return _t1394
    else
        _t1393 = nothing
    end
    _t1395 = Proto.CSVColumn(column_path=path, target_id=nothing, types=Proto.var"#Type"[])
    return _t1395
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t737 = parse_configure(parser)
        _t736 = _t737
    else
        _t736 = nothing
    end
    configure368 = _t736
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t739 = parse_sync(parser)
        _t738 = _t739
    else
        _t738 = nothing
    end
    sync369 = _t738
    xs370 = Proto.Epoch[]
    cond371 = match_lookahead_literal(parser, "(", 0)
    while cond371
        _t740 = parse_epoch(parser)
        item372 = _t740
        push!(xs370, item372)
        cond371 = match_lookahead_literal(parser, "(", 0)
    end
    epochs373 = xs370
    consume_literal!(parser, ")")
    _t741 = default_configure(parser)
    _t742 = Proto.Transaction(epochs=epochs373, configure=(!isnothing(configure368) ? configure368 : _t741), sync=sync369)
    return _t742
end

function parse_configure(parser::ParserState)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t743 = parse_config_dict(parser)
    config_dict374 = _t743
    consume_literal!(parser, ")")
    _t744 = construct_configure(parser, config_dict374)
    return _t744
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs375 = Tuple{String, Proto.Value}[]
    cond376 = match_lookahead_literal(parser, ":", 0)
    while cond376
        _t745 = parse_config_key_value(parser)
        item377 = _t745
        push!(xs375, item377)
        cond376 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values378 = xs375
    consume_literal!(parser, "}")
    return config_key_values378
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol379 = consume_terminal!(parser, "SYMBOL")
    _t746 = parse_value(parser)
    value380 = _t746
    return (symbol379, value380,)
end

function parse_value(parser::ParserState)::Proto.Value
    if match_lookahead_literal(parser, "true", 0)
        _t747 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t748 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t749 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t751 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t752 = 0
                        else
                            _t752 = -1
                        end
                        _t751 = _t752
                    end
                    _t750 = _t751
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t753 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t754 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t755 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t756 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t757 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t758 = 7
                                        else
                                            _t758 = -1
                                        end
                                        _t757 = _t758
                                    end
                                    _t756 = _t757
                                end
                                _t755 = _t756
                            end
                            _t754 = _t755
                        end
                        _t753 = _t754
                    end
                    _t750 = _t753
                end
                _t749 = _t750
            end
            _t748 = _t749
        end
        _t747 = _t748
    end
    prediction381 = _t747
    if prediction381 == 9
        _t760 = parse_boolean_value(parser)
        boolean_value390 = _t760
        _t761 = Proto.Value(value=OneOf(:boolean_value, boolean_value390))
        _t759 = _t761
    else
        if prediction381 == 8
            consume_literal!(parser, "missing")
            _t763 = Proto.MissingValue()
            _t764 = Proto.Value(value=OneOf(:missing_value, _t763))
            _t762 = _t764
        else
            if prediction381 == 7
                decimal389 = consume_terminal!(parser, "DECIMAL")
                _t766 = Proto.Value(value=OneOf(:decimal_value, decimal389))
                _t765 = _t766
            else
                if prediction381 == 6
                    int128388 = consume_terminal!(parser, "INT128")
                    _t768 = Proto.Value(value=OneOf(:int128_value, int128388))
                    _t767 = _t768
                else
                    if prediction381 == 5
                        uint128387 = consume_terminal!(parser, "UINT128")
                        _t770 = Proto.Value(value=OneOf(:uint128_value, uint128387))
                        _t769 = _t770
                    else
                        if prediction381 == 4
                            float386 = consume_terminal!(parser, "FLOAT")
                            _t772 = Proto.Value(value=OneOf(:float_value, float386))
                            _t771 = _t772
                        else
                            if prediction381 == 3
                                int385 = consume_terminal!(parser, "INT")
                                _t774 = Proto.Value(value=OneOf(:int_value, int385))
                                _t773 = _t774
                            else
                                if prediction381 == 2
                                    string384 = consume_terminal!(parser, "STRING")
                                    _t776 = Proto.Value(value=OneOf(:string_value, string384))
                                    _t775 = _t776
                                else
                                    if prediction381 == 1
                                        _t778 = parse_datetime(parser)
                                        datetime383 = _t778
                                        _t779 = Proto.Value(value=OneOf(:datetime_value, datetime383))
                                        _t777 = _t779
                                    else
                                        if prediction381 == 0
                                            _t781 = parse_date(parser)
                                            date382 = _t781
                                            _t782 = Proto.Value(value=OneOf(:date_value, date382))
                                            _t780 = _t782
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t777 = _t780
                                    end
                                    _t775 = _t777
                                end
                                _t773 = _t775
                            end
                            _t771 = _t773
                        end
                        _t769 = _t771
                    end
                    _t767 = _t769
                end
                _t765 = _t767
            end
            _t762 = _t765
        end
        _t759 = _t762
    end
    return _t759
end

function parse_date(parser::ParserState)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int391 = consume_terminal!(parser, "INT")
    int_3392 = consume_terminal!(parser, "INT")
    int_4393 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t783 = Proto.DateValue(year=Int32(int391), month=Int32(int_3392), day=Int32(int_4393))
    return _t783
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int394 = consume_terminal!(parser, "INT")
    int_3395 = consume_terminal!(parser, "INT")
    int_4396 = consume_terminal!(parser, "INT")
    int_5397 = consume_terminal!(parser, "INT")
    int_6398 = consume_terminal!(parser, "INT")
    int_7399 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t784 = consume_terminal!(parser, "INT")
    else
        _t784 = nothing
    end
    int_8400 = _t784
    consume_literal!(parser, ")")
    _t785 = Proto.DateTimeValue(year=Int32(int394), month=Int32(int_3395), day=Int32(int_4396), hour=Int32(int_5397), minute=Int32(int_6398), second=Int32(int_7399), microsecond=Int32((!isnothing(int_8400) ? int_8400 : 0)))
    return _t785
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t786 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t787 = 1
        else
            _t787 = -1
        end
        _t786 = _t787
    end
    prediction401 = _t786
    if prediction401 == 1
        consume_literal!(parser, "false")
        _t788 = false
    else
        if prediction401 == 0
            consume_literal!(parser, "true")
            _t789 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t788 = _t789
    end
    return _t788
end

function parse_sync(parser::ParserState)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs402 = Proto.FragmentId[]
    cond403 = match_lookahead_literal(parser, ":", 0)
    while cond403
        _t790 = parse_fragment_id(parser)
        item404 = _t790
        push!(xs402, item404)
        cond403 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids405 = xs402
    consume_literal!(parser, ")")
    _t791 = Proto.Sync(fragments=fragment_ids405)
    return _t791
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol406 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol406))
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t793 = parse_epoch_writes(parser)
        _t792 = _t793
    else
        _t792 = nothing
    end
    epoch_writes407 = _t792
    if match_lookahead_literal(parser, "(", 0)
        _t795 = parse_epoch_reads(parser)
        _t794 = _t795
    else
        _t794 = nothing
    end
    epoch_reads408 = _t794
    consume_literal!(parser, ")")
    _t796 = Proto.Epoch(writes=(!isnothing(epoch_writes407) ? epoch_writes407 : Proto.Write[]), reads=(!isnothing(epoch_reads408) ? epoch_reads408 : Proto.Read[]))
    return _t796
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs409 = Proto.Write[]
    cond410 = match_lookahead_literal(parser, "(", 0)
    while cond410
        _t797 = parse_write(parser)
        item411 = _t797
        push!(xs409, item411)
        cond410 = match_lookahead_literal(parser, "(", 0)
    end
    writes412 = xs409
    consume_literal!(parser, ")")
    return writes412
end

function parse_write(parser::ParserState)::Proto.Write
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t799 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t800 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t801 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t802 = 2
                    else
                        _t802 = -1
                    end
                    _t801 = _t802
                end
                _t800 = _t801
            end
            _t799 = _t800
        end
        _t798 = _t799
    else
        _t798 = -1
    end
    prediction413 = _t798
    if prediction413 == 3
        _t804 = parse_snapshot(parser)
        snapshot417 = _t804
        _t805 = Proto.Write(write_type=OneOf(:snapshot, snapshot417))
        _t803 = _t805
    else
        if prediction413 == 2
            _t807 = parse_context(parser)
            context416 = _t807
            _t808 = Proto.Write(write_type=OneOf(:context, context416))
            _t806 = _t808
        else
            if prediction413 == 1
                _t810 = parse_undefine(parser)
                undefine415 = _t810
                _t811 = Proto.Write(write_type=OneOf(:undefine, undefine415))
                _t809 = _t811
            else
                if prediction413 == 0
                    _t813 = parse_define(parser)
                    define414 = _t813
                    _t814 = Proto.Write(write_type=OneOf(:define, define414))
                    _t812 = _t814
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t809 = _t812
            end
            _t806 = _t809
        end
        _t803 = _t806
    end
    return _t803
end

function parse_define(parser::ParserState)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t815 = parse_fragment(parser)
    fragment418 = _t815
    consume_literal!(parser, ")")
    _t816 = Proto.Define(fragment=fragment418)
    return _t816
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t817 = parse_new_fragment_id(parser)
    new_fragment_id419 = _t817
    xs420 = Proto.Declaration[]
    cond421 = match_lookahead_literal(parser, "(", 0)
    while cond421
        _t818 = parse_declaration(parser)
        item422 = _t818
        push!(xs420, item422)
        cond421 = match_lookahead_literal(parser, "(", 0)
    end
    declarations423 = xs420
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id419, declarations423)
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    _t819 = parse_fragment_id(parser)
    fragment_id424 = _t819
    start_fragment!(parser, fragment_id424)
    return fragment_id424
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t821 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t822 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t823 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t824 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t825 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t826 = 1
                            else
                                _t826 = -1
                            end
                            _t825 = _t826
                        end
                        _t824 = _t825
                    end
                    _t823 = _t824
                end
                _t822 = _t823
            end
            _t821 = _t822
        end
        _t820 = _t821
    else
        _t820 = -1
    end
    prediction425 = _t820
    if prediction425 == 3
        _t828 = parse_data(parser)
        data429 = _t828
        _t829 = Proto.Declaration(declaration_type=OneOf(:data, data429))
        _t827 = _t829
    else
        if prediction425 == 2
            _t831 = parse_constraint(parser)
            constraint428 = _t831
            _t832 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint428))
            _t830 = _t832
        else
            if prediction425 == 1
                _t834 = parse_algorithm(parser)
                algorithm427 = _t834
                _t835 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm427))
                _t833 = _t835
            else
                if prediction425 == 0
                    _t837 = parse_def(parser)
                    def426 = _t837
                    _t838 = Proto.Declaration(declaration_type=OneOf(:def, def426))
                    _t836 = _t838
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t833 = _t836
            end
            _t830 = _t833
        end
        _t827 = _t830
    end
    return _t827
end

function parse_def(parser::ParserState)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t839 = parse_relation_id(parser)
    relation_id430 = _t839
    _t840 = parse_abstraction(parser)
    abstraction431 = _t840
    if match_lookahead_literal(parser, "(", 0)
        _t842 = parse_attrs(parser)
        _t841 = _t842
    else
        _t841 = nothing
    end
    attrs432 = _t841
    consume_literal!(parser, ")")
    _t843 = Proto.Def(name=relation_id430, body=abstraction431, attrs=(!isnothing(attrs432) ? attrs432 : Proto.Attribute[]))
    return _t843
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    if match_lookahead_literal(parser, ":", 0)
        _t844 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t845 = 1
        else
            _t845 = -1
        end
        _t844 = _t845
    end
    prediction433 = _t844
    if prediction433 == 1
        uint128435 = consume_terminal!(parser, "UINT128")
        _t846 = Proto.RelationId(uint128435.low, uint128435.high)
    else
        if prediction433 == 0
            consume_literal!(parser, ":")
            symbol434 = consume_terminal!(parser, "SYMBOL")
            _t847 = relation_id_from_string(parser, symbol434)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t846 = _t847
    end
    return _t846
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t848 = parse_bindings(parser)
    bindings436 = _t848
    _t849 = parse_formula(parser)
    formula437 = _t849
    consume_literal!(parser, ")")
    _t850 = Proto.Abstraction(vars=vcat(bindings436[1], !isnothing(bindings436[2]) ? bindings436[2] : []), value=formula437)
    return _t850
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs438 = Proto.Binding[]
    cond439 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond439
        _t851 = parse_binding(parser)
        item440 = _t851
        push!(xs438, item440)
        cond439 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings441 = xs438
    if match_lookahead_literal(parser, "|", 0)
        _t853 = parse_value_bindings(parser)
        _t852 = _t853
    else
        _t852 = nothing
    end
    value_bindings442 = _t852
    consume_literal!(parser, "]")
    return (bindings441, (!isnothing(value_bindings442) ? value_bindings442 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    symbol443 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t854 = parse_type(parser)
    type444 = _t854
    _t855 = Proto.Var(name=symbol443)
    _t856 = Proto.Binding(var=_t855, var"#type"=type444)
    return _t856
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t857 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t858 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t859 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t860 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t861 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t862 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t863 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t864 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t865 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t866 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t867 = 9
                                            else
                                                _t867 = -1
                                            end
                                            _t866 = _t867
                                        end
                                        _t865 = _t866
                                    end
                                    _t864 = _t865
                                end
                                _t863 = _t864
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
    prediction445 = _t857
    if prediction445 == 10
        _t869 = parse_boolean_type(parser)
        boolean_type456 = _t869
        _t870 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type456))
        _t868 = _t870
    else
        if prediction445 == 9
            _t872 = parse_decimal_type(parser)
            decimal_type455 = _t872
            _t873 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type455))
            _t871 = _t873
        else
            if prediction445 == 8
                _t875 = parse_missing_type(parser)
                missing_type454 = _t875
                _t876 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type454))
                _t874 = _t876
            else
                if prediction445 == 7
                    _t878 = parse_datetime_type(parser)
                    datetime_type453 = _t878
                    _t879 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type453))
                    _t877 = _t879
                else
                    if prediction445 == 6
                        _t881 = parse_date_type(parser)
                        date_type452 = _t881
                        _t882 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type452))
                        _t880 = _t882
                    else
                        if prediction445 == 5
                            _t884 = parse_int128_type(parser)
                            int128_type451 = _t884
                            _t885 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type451))
                            _t883 = _t885
                        else
                            if prediction445 == 4
                                _t887 = parse_uint128_type(parser)
                                uint128_type450 = _t887
                                _t888 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type450))
                                _t886 = _t888
                            else
                                if prediction445 == 3
                                    _t890 = parse_float_type(parser)
                                    float_type449 = _t890
                                    _t891 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type449))
                                    _t889 = _t891
                                else
                                    if prediction445 == 2
                                        _t893 = parse_int_type(parser)
                                        int_type448 = _t893
                                        _t894 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type448))
                                        _t892 = _t894
                                    else
                                        if prediction445 == 1
                                            _t896 = parse_string_type(parser)
                                            string_type447 = _t896
                                            _t897 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type447))
                                            _t895 = _t897
                                        else
                                            if prediction445 == 0
                                                _t899 = parse_unspecified_type(parser)
                                                unspecified_type446 = _t899
                                                _t900 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type446))
                                                _t898 = _t900
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t895 = _t898
                                        end
                                        _t892 = _t895
                                    end
                                    _t889 = _t892
                                end
                                _t886 = _t889
                            end
                            _t883 = _t886
                        end
                        _t880 = _t883
                    end
                    _t877 = _t880
                end
                _t874 = _t877
            end
            _t871 = _t874
        end
        _t868 = _t871
    end
    return _t868
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t901 = Proto.UnspecifiedType()
    return _t901
end

function parse_string_type(parser::ParserState)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t902 = Proto.StringType()
    return _t902
end

function parse_int_type(parser::ParserState)::Proto.IntType
    consume_literal!(parser, "INT")
    _t903 = Proto.IntType()
    return _t903
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t904 = Proto.FloatType()
    return _t904
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t905 = Proto.UInt128Type()
    return _t905
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t906 = Proto.Int128Type()
    return _t906
end

function parse_date_type(parser::ParserState)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t907 = Proto.DateType()
    return _t907
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t908 = Proto.DateTimeType()
    return _t908
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t909 = Proto.MissingType()
    return _t909
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int457 = consume_terminal!(parser, "INT")
    int_3458 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t910 = Proto.DecimalType(precision=Int32(int457), scale=Int32(int_3458))
    return _t910
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t911 = Proto.BooleanType()
    return _t911
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs459 = Proto.Binding[]
    cond460 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond460
        _t912 = parse_binding(parser)
        item461 = _t912
        push!(xs459, item461)
        cond460 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings462 = xs459
    return bindings462
end

function parse_formula(parser::ParserState)::Proto.Formula
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t914 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t915 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t916 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t917 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t918 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t919 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t920 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t921 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t922 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t923 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t924 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t925 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t926 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t927 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t928 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t929 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t930 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t931 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t932 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t933 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t934 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t935 = 10
                                                                                            else
                                                                                                _t935 = -1
                                                                                            end
                                                                                            _t934 = _t935
                                                                                        end
                                                                                        _t933 = _t934
                                                                                    end
                                                                                    _t932 = _t933
                                                                                end
                                                                                _t931 = _t932
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
    else
        _t913 = -1
    end
    prediction463 = _t913
    if prediction463 == 12
        _t937 = parse_cast(parser)
        cast476 = _t937
        _t938 = Proto.Formula(formula_type=OneOf(:cast, cast476))
        _t936 = _t938
    else
        if prediction463 == 11
            _t940 = parse_rel_atom(parser)
            rel_atom475 = _t940
            _t941 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom475))
            _t939 = _t941
        else
            if prediction463 == 10
                _t943 = parse_primitive(parser)
                primitive474 = _t943
                _t944 = Proto.Formula(formula_type=OneOf(:primitive, primitive474))
                _t942 = _t944
            else
                if prediction463 == 9
                    _t946 = parse_pragma(parser)
                    pragma473 = _t946
                    _t947 = Proto.Formula(formula_type=OneOf(:pragma, pragma473))
                    _t945 = _t947
                else
                    if prediction463 == 8
                        _t949 = parse_atom(parser)
                        atom472 = _t949
                        _t950 = Proto.Formula(formula_type=OneOf(:atom, atom472))
                        _t948 = _t950
                    else
                        if prediction463 == 7
                            _t952 = parse_ffi(parser)
                            ffi471 = _t952
                            _t953 = Proto.Formula(formula_type=OneOf(:ffi, ffi471))
                            _t951 = _t953
                        else
                            if prediction463 == 6
                                _t955 = parse_not(parser)
                                not470 = _t955
                                _t956 = Proto.Formula(formula_type=OneOf(:not, not470))
                                _t954 = _t956
                            else
                                if prediction463 == 5
                                    _t958 = parse_disjunction(parser)
                                    disjunction469 = _t958
                                    _t959 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction469))
                                    _t957 = _t959
                                else
                                    if prediction463 == 4
                                        _t961 = parse_conjunction(parser)
                                        conjunction468 = _t961
                                        _t962 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction468))
                                        _t960 = _t962
                                    else
                                        if prediction463 == 3
                                            _t964 = parse_reduce(parser)
                                            reduce467 = _t964
                                            _t965 = Proto.Formula(formula_type=OneOf(:reduce, reduce467))
                                            _t963 = _t965
                                        else
                                            if prediction463 == 2
                                                _t967 = parse_exists(parser)
                                                exists466 = _t967
                                                _t968 = Proto.Formula(formula_type=OneOf(:exists, exists466))
                                                _t966 = _t968
                                            else
                                                if prediction463 == 1
                                                    _t970 = parse_false(parser)
                                                    false465 = _t970
                                                    _t971 = Proto.Formula(formula_type=OneOf(:disjunction, false465))
                                                    _t969 = _t971
                                                else
                                                    if prediction463 == 0
                                                        _t973 = parse_true(parser)
                                                        true464 = _t973
                                                        _t974 = Proto.Formula(formula_type=OneOf(:conjunction, true464))
                                                        _t972 = _t974
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t969 = _t972
                                                end
                                                _t966 = _t969
                                            end
                                            _t963 = _t966
                                        end
                                        _t960 = _t963
                                    end
                                    _t957 = _t960
                                end
                                _t954 = _t957
                            end
                            _t951 = _t954
                        end
                        _t948 = _t951
                    end
                    _t945 = _t948
                end
                _t942 = _t945
            end
            _t939 = _t942
        end
        _t936 = _t939
    end
    return _t936
end

function parse_true(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t975 = Proto.Conjunction(args=Proto.Formula[])
    return _t975
end

function parse_false(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t976 = Proto.Disjunction(args=Proto.Formula[])
    return _t976
end

function parse_exists(parser::ParserState)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t977 = parse_bindings(parser)
    bindings477 = _t977
    _t978 = parse_formula(parser)
    formula478 = _t978
    consume_literal!(parser, ")")
    _t979 = Proto.Abstraction(vars=vcat(bindings477[1], !isnothing(bindings477[2]) ? bindings477[2] : []), value=formula478)
    _t980 = Proto.Exists(body=_t979)
    return _t980
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t981 = parse_abstraction(parser)
    abstraction479 = _t981
    _t982 = parse_abstraction(parser)
    abstraction_3480 = _t982
    _t983 = parse_terms(parser)
    terms481 = _t983
    consume_literal!(parser, ")")
    _t984 = Proto.Reduce(op=abstraction479, body=abstraction_3480, terms=terms481)
    return _t984
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs482 = Proto.Term[]
    cond483 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond483
        _t985 = parse_term(parser)
        item484 = _t985
        push!(xs482, item484)
        cond483 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms485 = xs482
    consume_literal!(parser, ")")
    return terms485
end

function parse_term(parser::ParserState)::Proto.Term
    if match_lookahead_literal(parser, "true", 0)
        _t986 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t987 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t988 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t989 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t990 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t991 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t992 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t993 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t994 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t995 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t996 = 1
                                            else
                                                _t996 = -1
                                            end
                                            _t995 = _t996
                                        end
                                        _t994 = _t995
                                    end
                                    _t993 = _t994
                                end
                                _t992 = _t993
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
    prediction486 = _t986
    if prediction486 == 1
        _t998 = parse_constant(parser)
        constant488 = _t998
        _t999 = Proto.Term(term_type=OneOf(:constant, constant488))
        _t997 = _t999
    else
        if prediction486 == 0
            _t1001 = parse_var(parser)
            var487 = _t1001
            _t1002 = Proto.Term(term_type=OneOf(:var, var487))
            _t1000 = _t1002
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t997 = _t1000
    end
    return _t997
end

function parse_var(parser::ParserState)::Proto.Var
    symbol489 = consume_terminal!(parser, "SYMBOL")
    _t1003 = Proto.Var(name=symbol489)
    return _t1003
end

function parse_constant(parser::ParserState)::Proto.Value
    _t1004 = parse_value(parser)
    value490 = _t1004
    return value490
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs491 = Proto.Formula[]
    cond492 = match_lookahead_literal(parser, "(", 0)
    while cond492
        _t1005 = parse_formula(parser)
        item493 = _t1005
        push!(xs491, item493)
        cond492 = match_lookahead_literal(parser, "(", 0)
    end
    formulas494 = xs491
    consume_literal!(parser, ")")
    _t1006 = Proto.Conjunction(args=formulas494)
    return _t1006
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs495 = Proto.Formula[]
    cond496 = match_lookahead_literal(parser, "(", 0)
    while cond496
        _t1007 = parse_formula(parser)
        item497 = _t1007
        push!(xs495, item497)
        cond496 = match_lookahead_literal(parser, "(", 0)
    end
    formulas498 = xs495
    consume_literal!(parser, ")")
    _t1008 = Proto.Disjunction(args=formulas498)
    return _t1008
end

function parse_not(parser::ParserState)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1009 = parse_formula(parser)
    formula499 = _t1009
    consume_literal!(parser, ")")
    _t1010 = Proto.Not(arg=formula499)
    return _t1010
end

function parse_ffi(parser::ParserState)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1011 = parse_name(parser)
    name500 = _t1011
    _t1012 = parse_ffi_args(parser)
    ffi_args501 = _t1012
    _t1013 = parse_terms(parser)
    terms502 = _t1013
    consume_literal!(parser, ")")
    _t1014 = Proto.FFI(name=name500, args=ffi_args501, terms=terms502)
    return _t1014
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol503 = consume_terminal!(parser, "SYMBOL")
    return symbol503
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs504 = Proto.Abstraction[]
    cond505 = match_lookahead_literal(parser, "(", 0)
    while cond505
        _t1015 = parse_abstraction(parser)
        item506 = _t1015
        push!(xs504, item506)
        cond505 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions507 = xs504
    consume_literal!(parser, ")")
    return abstractions507
end

function parse_atom(parser::ParserState)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1016 = parse_relation_id(parser)
    relation_id508 = _t1016
    xs509 = Proto.Term[]
    cond510 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond510
        _t1017 = parse_term(parser)
        item511 = _t1017
        push!(xs509, item511)
        cond510 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms512 = xs509
    consume_literal!(parser, ")")
    _t1018 = Proto.Atom(name=relation_id508, terms=terms512)
    return _t1018
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1019 = parse_name(parser)
    name513 = _t1019
    xs514 = Proto.Term[]
    cond515 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond515
        _t1020 = parse_term(parser)
        item516 = _t1020
        push!(xs514, item516)
        cond515 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms517 = xs514
    consume_literal!(parser, ")")
    _t1021 = Proto.Pragma(name=name513, terms=terms517)
    return _t1021
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1023 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1024 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1025 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1026 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1027 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1028 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1029 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1030 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1031 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1032 = 7
                                            else
                                                _t1032 = -1
                                            end
                                            _t1031 = _t1032
                                        end
                                        _t1030 = _t1031
                                    end
                                    _t1029 = _t1030
                                end
                                _t1028 = _t1029
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
    else
        _t1022 = -1
    end
    prediction518 = _t1022
    if prediction518 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1034 = parse_name(parser)
        name528 = _t1034
        xs529 = Proto.RelTerm[]
        cond530 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond530
            _t1035 = parse_rel_term(parser)
            item531 = _t1035
            push!(xs529, item531)
            cond530 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms532 = xs529
        consume_literal!(parser, ")")
        _t1036 = Proto.Primitive(name=name528, terms=rel_terms532)
        _t1033 = _t1036
    else
        if prediction518 == 8
            _t1038 = parse_divide(parser)
            divide527 = _t1038
            _t1037 = divide527
        else
            if prediction518 == 7
                _t1040 = parse_multiply(parser)
                multiply526 = _t1040
                _t1039 = multiply526
            else
                if prediction518 == 6
                    _t1042 = parse_minus(parser)
                    minus525 = _t1042
                    _t1041 = minus525
                else
                    if prediction518 == 5
                        _t1044 = parse_add(parser)
                        add524 = _t1044
                        _t1043 = add524
                    else
                        if prediction518 == 4
                            _t1046 = parse_gt_eq(parser)
                            gt_eq523 = _t1046
                            _t1045 = gt_eq523
                        else
                            if prediction518 == 3
                                _t1048 = parse_gt(parser)
                                gt522 = _t1048
                                _t1047 = gt522
                            else
                                if prediction518 == 2
                                    _t1050 = parse_lt_eq(parser)
                                    lt_eq521 = _t1050
                                    _t1049 = lt_eq521
                                else
                                    if prediction518 == 1
                                        _t1052 = parse_lt(parser)
                                        lt520 = _t1052
                                        _t1051 = lt520
                                    else
                                        if prediction518 == 0
                                            _t1054 = parse_eq(parser)
                                            eq519 = _t1054
                                            _t1053 = eq519
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1051 = _t1053
                                    end
                                    _t1049 = _t1051
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
        _t1033 = _t1037
    end
    return _t1033
end

function parse_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1055 = parse_term(parser)
    term533 = _t1055
    _t1056 = parse_term(parser)
    term_3534 = _t1056
    consume_literal!(parser, ")")
    _t1057 = Proto.RelTerm(rel_term_type=OneOf(:term, term533))
    _t1058 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3534))
    _t1059 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1057, _t1058])
    return _t1059
end

function parse_lt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1060 = parse_term(parser)
    term535 = _t1060
    _t1061 = parse_term(parser)
    term_3536 = _t1061
    consume_literal!(parser, ")")
    _t1062 = Proto.RelTerm(rel_term_type=OneOf(:term, term535))
    _t1063 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3536))
    _t1064 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1062, _t1063])
    return _t1064
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1065 = parse_term(parser)
    term537 = _t1065
    _t1066 = parse_term(parser)
    term_3538 = _t1066
    consume_literal!(parser, ")")
    _t1067 = Proto.RelTerm(rel_term_type=OneOf(:term, term537))
    _t1068 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3538))
    _t1069 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1067, _t1068])
    return _t1069
end

function parse_gt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1070 = parse_term(parser)
    term539 = _t1070
    _t1071 = parse_term(parser)
    term_3540 = _t1071
    consume_literal!(parser, ")")
    _t1072 = Proto.RelTerm(rel_term_type=OneOf(:term, term539))
    _t1073 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3540))
    _t1074 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1072, _t1073])
    return _t1074
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1075 = parse_term(parser)
    term541 = _t1075
    _t1076 = parse_term(parser)
    term_3542 = _t1076
    consume_literal!(parser, ")")
    _t1077 = Proto.RelTerm(rel_term_type=OneOf(:term, term541))
    _t1078 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3542))
    _t1079 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1077, _t1078])
    return _t1079
end

function parse_add(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1080 = parse_term(parser)
    term543 = _t1080
    _t1081 = parse_term(parser)
    term_3544 = _t1081
    _t1082 = parse_term(parser)
    term_4545 = _t1082
    consume_literal!(parser, ")")
    _t1083 = Proto.RelTerm(rel_term_type=OneOf(:term, term543))
    _t1084 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3544))
    _t1085 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4545))
    _t1086 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1083, _t1084, _t1085])
    return _t1086
end

function parse_minus(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1087 = parse_term(parser)
    term546 = _t1087
    _t1088 = parse_term(parser)
    term_3547 = _t1088
    _t1089 = parse_term(parser)
    term_4548 = _t1089
    consume_literal!(parser, ")")
    _t1090 = Proto.RelTerm(rel_term_type=OneOf(:term, term546))
    _t1091 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3547))
    _t1092 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4548))
    _t1093 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1090, _t1091, _t1092])
    return _t1093
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1094 = parse_term(parser)
    term549 = _t1094
    _t1095 = parse_term(parser)
    term_3550 = _t1095
    _t1096 = parse_term(parser)
    term_4551 = _t1096
    consume_literal!(parser, ")")
    _t1097 = Proto.RelTerm(rel_term_type=OneOf(:term, term549))
    _t1098 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3550))
    _t1099 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4551))
    _t1100 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1097, _t1098, _t1099])
    return _t1100
end

function parse_divide(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1101 = parse_term(parser)
    term552 = _t1101
    _t1102 = parse_term(parser)
    term_3553 = _t1102
    _t1103 = parse_term(parser)
    term_4554 = _t1103
    consume_literal!(parser, ")")
    _t1104 = Proto.RelTerm(rel_term_type=OneOf(:term, term552))
    _t1105 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3553))
    _t1106 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4554))
    _t1107 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1104, _t1105, _t1106])
    return _t1107
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    if match_lookahead_literal(parser, "true", 0)
        _t1108 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1109 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1110 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1111 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1112 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1113 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1114 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1115 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1116 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1117 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1118 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1119 = 1
                                                else
                                                    _t1119 = -1
                                                end
                                                _t1118 = _t1119
                                            end
                                            _t1117 = _t1118
                                        end
                                        _t1116 = _t1117
                                    end
                                    _t1115 = _t1116
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
    prediction555 = _t1108
    if prediction555 == 1
        _t1121 = parse_term(parser)
        term557 = _t1121
        _t1122 = Proto.RelTerm(rel_term_type=OneOf(:term, term557))
        _t1120 = _t1122
    else
        if prediction555 == 0
            _t1124 = parse_specialized_value(parser)
            specialized_value556 = _t1124
            _t1125 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value556))
            _t1123 = _t1125
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1120 = _t1123
    end
    return _t1120
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    consume_literal!(parser, "#")
    _t1126 = parse_value(parser)
    value558 = _t1126
    return value558
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1127 = parse_name(parser)
    name559 = _t1127
    xs560 = Proto.RelTerm[]
    cond561 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond561
        _t1128 = parse_rel_term(parser)
        item562 = _t1128
        push!(xs560, item562)
        cond561 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms563 = xs560
    consume_literal!(parser, ")")
    _t1129 = Proto.RelAtom(name=name559, terms=rel_terms563)
    return _t1129
end

function parse_cast(parser::ParserState)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1130 = parse_term(parser)
    term564 = _t1130
    _t1131 = parse_term(parser)
    term_3565 = _t1131
    consume_literal!(parser, ")")
    _t1132 = Proto.Cast(input=term564, result=term_3565)
    return _t1132
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs566 = Proto.Attribute[]
    cond567 = match_lookahead_literal(parser, "(", 0)
    while cond567
        _t1133 = parse_attribute(parser)
        item568 = _t1133
        push!(xs566, item568)
        cond567 = match_lookahead_literal(parser, "(", 0)
    end
    attributes569 = xs566
    consume_literal!(parser, ")")
    return attributes569
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1134 = parse_name(parser)
    name570 = _t1134
    xs571 = Proto.Value[]
    cond572 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond572
        _t1135 = parse_value(parser)
        item573 = _t1135
        push!(xs571, item573)
        cond572 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values574 = xs571
    consume_literal!(parser, ")")
    _t1136 = Proto.Attribute(name=name570, args=values574)
    return _t1136
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs575 = Proto.RelationId[]
    cond576 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond576
        _t1137 = parse_relation_id(parser)
        item577 = _t1137
        push!(xs575, item577)
        cond576 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids578 = xs575
    _t1138 = parse_script(parser)
    script579 = _t1138
    consume_literal!(parser, ")")
    _t1139 = Proto.Algorithm(var"#global"=relation_ids578, body=script579)
    return _t1139
end

function parse_script(parser::ParserState)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs580 = Proto.Construct[]
    cond581 = match_lookahead_literal(parser, "(", 0)
    while cond581
        _t1140 = parse_construct(parser)
        item582 = _t1140
        push!(xs580, item582)
        cond581 = match_lookahead_literal(parser, "(", 0)
    end
    constructs583 = xs580
    consume_literal!(parser, ")")
    _t1141 = Proto.Script(constructs=constructs583)
    return _t1141
end

function parse_construct(parser::ParserState)::Proto.Construct
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1143 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1144 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1145 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1146 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1147 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1148 = 1
                            else
                                _t1148 = -1
                            end
                            _t1147 = _t1148
                        end
                        _t1146 = _t1147
                    end
                    _t1145 = _t1146
                end
                _t1144 = _t1145
            end
            _t1143 = _t1144
        end
        _t1142 = _t1143
    else
        _t1142 = -1
    end
    prediction584 = _t1142
    if prediction584 == 1
        _t1150 = parse_instruction(parser)
        instruction586 = _t1150
        _t1151 = Proto.Construct(construct_type=OneOf(:instruction, instruction586))
        _t1149 = _t1151
    else
        if prediction584 == 0
            _t1153 = parse_loop(parser)
            loop585 = _t1153
            _t1154 = Proto.Construct(construct_type=OneOf(:loop, loop585))
            _t1152 = _t1154
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1149 = _t1152
    end
    return _t1149
end

function parse_loop(parser::ParserState)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1155 = parse_init(parser)
    init587 = _t1155
    _t1156 = parse_script(parser)
    script588 = _t1156
    consume_literal!(parser, ")")
    _t1157 = Proto.Loop(init=init587, body=script588)
    return _t1157
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs589 = Proto.Instruction[]
    cond590 = match_lookahead_literal(parser, "(", 0)
    while cond590
        _t1158 = parse_instruction(parser)
        item591 = _t1158
        push!(xs589, item591)
        cond590 = match_lookahead_literal(parser, "(", 0)
    end
    instructions592 = xs589
    consume_literal!(parser, ")")
    return instructions592
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1160 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1161 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1162 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1163 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1164 = 0
                        else
                            _t1164 = -1
                        end
                        _t1163 = _t1164
                    end
                    _t1162 = _t1163
                end
                _t1161 = _t1162
            end
            _t1160 = _t1161
        end
        _t1159 = _t1160
    else
        _t1159 = -1
    end
    prediction593 = _t1159
    if prediction593 == 4
        _t1166 = parse_monus_def(parser)
        monus_def598 = _t1166
        _t1167 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def598))
        _t1165 = _t1167
    else
        if prediction593 == 3
            _t1169 = parse_monoid_def(parser)
            monoid_def597 = _t1169
            _t1170 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def597))
            _t1168 = _t1170
        else
            if prediction593 == 2
                _t1172 = parse_break(parser)
                break596 = _t1172
                _t1173 = Proto.Instruction(instr_type=OneOf(:var"#break", break596))
                _t1171 = _t1173
            else
                if prediction593 == 1
                    _t1175 = parse_upsert(parser)
                    upsert595 = _t1175
                    _t1176 = Proto.Instruction(instr_type=OneOf(:upsert, upsert595))
                    _t1174 = _t1176
                else
                    if prediction593 == 0
                        _t1178 = parse_assign(parser)
                        assign594 = _t1178
                        _t1179 = Proto.Instruction(instr_type=OneOf(:assign, assign594))
                        _t1177 = _t1179
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1174 = _t1177
                end
                _t1171 = _t1174
            end
            _t1168 = _t1171
        end
        _t1165 = _t1168
    end
    return _t1165
end

function parse_assign(parser::ParserState)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1180 = parse_relation_id(parser)
    relation_id599 = _t1180
    _t1181 = parse_abstraction(parser)
    abstraction600 = _t1181
    if match_lookahead_literal(parser, "(", 0)
        _t1183 = parse_attrs(parser)
        _t1182 = _t1183
    else
        _t1182 = nothing
    end
    attrs601 = _t1182
    consume_literal!(parser, ")")
    _t1184 = Proto.Assign(name=relation_id599, body=abstraction600, attrs=(!isnothing(attrs601) ? attrs601 : Proto.Attribute[]))
    return _t1184
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1185 = parse_relation_id(parser)
    relation_id602 = _t1185
    _t1186 = parse_abstraction_with_arity(parser)
    abstraction_with_arity603 = _t1186
    if match_lookahead_literal(parser, "(", 0)
        _t1188 = parse_attrs(parser)
        _t1187 = _t1188
    else
        _t1187 = nothing
    end
    attrs604 = _t1187
    consume_literal!(parser, ")")
    _t1189 = Proto.Upsert(name=relation_id602, body=abstraction_with_arity603[1], attrs=(!isnothing(attrs604) ? attrs604 : Proto.Attribute[]), value_arity=abstraction_with_arity603[2])
    return _t1189
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1190 = parse_bindings(parser)
    bindings605 = _t1190
    _t1191 = parse_formula(parser)
    formula606 = _t1191
    consume_literal!(parser, ")")
    _t1192 = Proto.Abstraction(vars=vcat(bindings605[1], !isnothing(bindings605[2]) ? bindings605[2] : []), value=formula606)
    return (_t1192, length(bindings605[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1193 = parse_relation_id(parser)
    relation_id607 = _t1193
    _t1194 = parse_abstraction(parser)
    abstraction608 = _t1194
    if match_lookahead_literal(parser, "(", 0)
        _t1196 = parse_attrs(parser)
        _t1195 = _t1196
    else
        _t1195 = nothing
    end
    attrs609 = _t1195
    consume_literal!(parser, ")")
    _t1197 = Proto.Break(name=relation_id607, body=abstraction608, attrs=(!isnothing(attrs609) ? attrs609 : Proto.Attribute[]))
    return _t1197
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1198 = parse_monoid(parser)
    monoid610 = _t1198
    _t1199 = parse_relation_id(parser)
    relation_id611 = _t1199
    _t1200 = parse_abstraction_with_arity(parser)
    abstraction_with_arity612 = _t1200
    if match_lookahead_literal(parser, "(", 0)
        _t1202 = parse_attrs(parser)
        _t1201 = _t1202
    else
        _t1201 = nothing
    end
    attrs613 = _t1201
    consume_literal!(parser, ")")
    _t1203 = Proto.MonoidDef(monoid=monoid610, name=relation_id611, body=abstraction_with_arity612[1], attrs=(!isnothing(attrs613) ? attrs613 : Proto.Attribute[]), value_arity=abstraction_with_arity612[2])
    return _t1203
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1205 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1206 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1207 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1208 = 2
                    else
                        _t1208 = -1
                    end
                    _t1207 = _t1208
                end
                _t1206 = _t1207
            end
            _t1205 = _t1206
        end
        _t1204 = _t1205
    else
        _t1204 = -1
    end
    prediction614 = _t1204
    if prediction614 == 3
        _t1210 = parse_sum_monoid(parser)
        sum_monoid618 = _t1210
        _t1211 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid618))
        _t1209 = _t1211
    else
        if prediction614 == 2
            _t1213 = parse_max_monoid(parser)
            max_monoid617 = _t1213
            _t1214 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid617))
            _t1212 = _t1214
        else
            if prediction614 == 1
                _t1216 = parse_min_monoid(parser)
                min_monoid616 = _t1216
                _t1217 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid616))
                _t1215 = _t1217
            else
                if prediction614 == 0
                    _t1219 = parse_or_monoid(parser)
                    or_monoid615 = _t1219
                    _t1220 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid615))
                    _t1218 = _t1220
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1215 = _t1218
            end
            _t1212 = _t1215
        end
        _t1209 = _t1212
    end
    return _t1209
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1221 = Proto.OrMonoid()
    return _t1221
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1222 = parse_type(parser)
    type619 = _t1222
    consume_literal!(parser, ")")
    _t1223 = Proto.MinMonoid(var"#type"=type619)
    return _t1223
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1224 = parse_type(parser)
    type620 = _t1224
    consume_literal!(parser, ")")
    _t1225 = Proto.MaxMonoid(var"#type"=type620)
    return _t1225
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1226 = parse_type(parser)
    type621 = _t1226
    consume_literal!(parser, ")")
    _t1227 = Proto.SumMonoid(var"#type"=type621)
    return _t1227
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1228 = parse_monoid(parser)
    monoid622 = _t1228
    _t1229 = parse_relation_id(parser)
    relation_id623 = _t1229
    _t1230 = parse_abstraction_with_arity(parser)
    abstraction_with_arity624 = _t1230
    if match_lookahead_literal(parser, "(", 0)
        _t1232 = parse_attrs(parser)
        _t1231 = _t1232
    else
        _t1231 = nothing
    end
    attrs625 = _t1231
    consume_literal!(parser, ")")
    _t1233 = Proto.MonusDef(monoid=monoid622, name=relation_id623, body=abstraction_with_arity624[1], attrs=(!isnothing(attrs625) ? attrs625 : Proto.Attribute[]), value_arity=abstraction_with_arity624[2])
    return _t1233
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1234 = parse_relation_id(parser)
    relation_id626 = _t1234
    _t1235 = parse_abstraction(parser)
    abstraction627 = _t1235
    _t1236 = parse_functional_dependency_keys(parser)
    functional_dependency_keys628 = _t1236
    _t1237 = parse_functional_dependency_values(parser)
    functional_dependency_values629 = _t1237
    consume_literal!(parser, ")")
    _t1238 = Proto.FunctionalDependency(guard=abstraction627, keys=functional_dependency_keys628, values=functional_dependency_values629)
    _t1239 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1238), name=relation_id626)
    return _t1239
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs630 = Proto.Var[]
    cond631 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond631
        _t1240 = parse_var(parser)
        item632 = _t1240
        push!(xs630, item632)
        cond631 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars633 = xs630
    consume_literal!(parser, ")")
    return vars633
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs634 = Proto.Var[]
    cond635 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond635
        _t1241 = parse_var(parser)
        item636 = _t1241
        push!(xs634, item636)
        cond635 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars637 = xs634
    consume_literal!(parser, ")")
    return vars637
end

function parse_data(parser::ParserState)::Proto.Data
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1243 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1244 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1245 = 1
                else
                    _t1245 = -1
                end
                _t1244 = _t1245
            end
            _t1243 = _t1244
        end
        _t1242 = _t1243
    else
        _t1242 = -1
    end
    prediction638 = _t1242
    if prediction638 == 2
        _t1247 = parse_csv_data(parser)
        csv_data641 = _t1247
        _t1248 = Proto.Data(data_type=OneOf(:csv_data, csv_data641))
        _t1246 = _t1248
    else
        if prediction638 == 1
            _t1250 = parse_betree_relation(parser)
            betree_relation640 = _t1250
            _t1251 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation640))
            _t1249 = _t1251
        else
            if prediction638 == 0
                _t1253 = parse_rel_edb(parser)
                rel_edb639 = _t1253
                _t1254 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb639))
                _t1252 = _t1254
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1249 = _t1252
        end
        _t1246 = _t1249
    end
    return _t1246
end

function parse_rel_edb(parser::ParserState)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t1255 = parse_relation_id(parser)
    relation_id642 = _t1255
    _t1256 = parse_rel_edb_path(parser)
    rel_edb_path643 = _t1256
    _t1257 = parse_rel_edb_types(parser)
    rel_edb_types644 = _t1257
    consume_literal!(parser, ")")
    _t1258 = Proto.RelEDB(target_id=relation_id642, path=rel_edb_path643, types=rel_edb_types644)
    return _t1258
end

function parse_rel_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs645 = String[]
    cond646 = match_lookahead_terminal(parser, "STRING", 0)
    while cond646
        item647 = consume_terminal!(parser, "STRING")
        push!(xs645, item647)
        cond646 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings648 = xs645
    consume_literal!(parser, "]")
    return strings648
end

function parse_rel_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs649 = Proto.var"#Type"[]
    cond650 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond650
        _t1259 = parse_type(parser)
        item651 = _t1259
        push!(xs649, item651)
        cond650 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types652 = xs649
    consume_literal!(parser, "]")
    return types652
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1260 = parse_relation_id(parser)
    relation_id653 = _t1260
    _t1261 = parse_betree_info(parser)
    betree_info654 = _t1261
    consume_literal!(parser, ")")
    _t1262 = Proto.BeTreeRelation(name=relation_id653, relation_info=betree_info654)
    return _t1262
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1263 = parse_betree_info_key_types(parser)
    betree_info_key_types655 = _t1263
    _t1264 = parse_betree_info_value_types(parser)
    betree_info_value_types656 = _t1264
    _t1265 = parse_config_dict(parser)
    config_dict657 = _t1265
    consume_literal!(parser, ")")
    _t1266 = construct_betree_info(parser, betree_info_key_types655, betree_info_value_types656, config_dict657)
    return _t1266
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs658 = Proto.var"#Type"[]
    cond659 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond659
        _t1267 = parse_type(parser)
        item660 = _t1267
        push!(xs658, item660)
        cond659 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types661 = xs658
    consume_literal!(parser, ")")
    return types661
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs662 = Proto.var"#Type"[]
    cond663 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond663
        _t1268 = parse_type(parser)
        item664 = _t1268
        push!(xs662, item664)
        cond663 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types665 = xs662
    consume_literal!(parser, ")")
    return types665
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1269 = parse_csvlocator(parser)
    csvlocator666 = _t1269
    _t1270 = parse_csv_config(parser)
    csv_config667 = _t1270
    _t1271 = parse_csv_columns(parser)
    csv_columns668 = _t1271
    _t1272 = parse_csv_asof(parser)
    csv_asof669 = _t1272
    consume_literal!(parser, ")")
    _t1273 = Proto.CSVData(locator=csvlocator666, config=csv_config667, columns=csv_columns668, asof=csv_asof669)
    return _t1273
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1275 = parse_csv_locator_paths(parser)
        _t1274 = _t1275
    else
        _t1274 = nothing
    end
    csv_locator_paths670 = _t1274
    if match_lookahead_literal(parser, "(", 0)
        _t1277 = parse_csv_locator_inline_data(parser)
        _t1276 = _t1277
    else
        _t1276 = nothing
    end
    csv_locator_inline_data671 = _t1276
    consume_literal!(parser, ")")
    _t1278 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths670) ? csv_locator_paths670 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data671) ? csv_locator_inline_data671 : "")))
    return _t1278
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs672 = String[]
    cond673 = match_lookahead_terminal(parser, "STRING", 0)
    while cond673
        item674 = consume_terminal!(parser, "STRING")
        push!(xs672, item674)
        cond673 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings675 = xs672
    consume_literal!(parser, ")")
    return strings675
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string676 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string676
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1279 = parse_config_dict(parser)
    config_dict677 = _t1279
    consume_literal!(parser, ")")
    _t1280 = construct_csv_config(parser, config_dict677)
    return _t1280
end

function parse_csv_columns(parser::ParserState)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs678 = Proto.CSVColumn[]
    cond679 = match_lookahead_literal(parser, "(", 0)
    while cond679
        _t1281 = parse_csv_column(parser)
        item680 = _t1281
        push!(xs678, item680)
        cond679 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns681 = xs678
    consume_literal!(parser, ")")
    return csv_columns681
end

function parse_csv_column(parser::ParserState)::Proto.CSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1282 = parse_csv_column_path(parser)
    csv_column_path682 = _t1282
    if ((match_lookahead_literal(parser, ":", 0) || match_lookahead_literal(parser, "[", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1284 = parse_csv_column_tail(parser)
        _t1283 = _t1284
    else
        _t1283 = nothing
    end
    csv_column_tail683 = _t1283
    consume_literal!(parser, ")")
    _t1285 = construct_csv_column(parser, csv_column_path682, csv_column_tail683)
    return _t1285
end

function parse_csv_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1286 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1287 = 0
        else
            _t1287 = -1
        end
        _t1286 = _t1287
    end
    prediction684 = _t1286
    if prediction684 == 1
        consume_literal!(parser, "[")
        xs686 = String[]
        cond687 = match_lookahead_terminal(parser, "STRING", 0)
        while cond687
            item688 = consume_terminal!(parser, "STRING")
            push!(xs686, item688)
            cond687 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings689 = xs686
        consume_literal!(parser, "]")
        _t1288 = strings689
    else
        if prediction684 == 0
            string685 = consume_terminal!(parser, "STRING")
            _t1289 = String[string685]
        else
            throw(ParseError("Unexpected token in csv_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1288 = _t1289
    end
    return _t1288
end

function parse_csv_column_tail(parser::ParserState)::Tuple{Union{Nothing, Proto.RelationId}, Vector{Proto.var"#Type"}}
    if match_lookahead_literal(parser, "[", 0)
        _t1290 = 1
    else
        if match_lookahead_literal(parser, ":", 0)
            _t1291 = 0
        else
            if match_lookahead_terminal(parser, "UINT128", 0)
                _t1292 = 0
            else
                _t1292 = -1
            end
            _t1291 = _t1292
        end
        _t1290 = _t1291
    end
    prediction690 = _t1290
    if prediction690 == 1
        consume_literal!(parser, "[")
        xs696 = Proto.var"#Type"[]
        cond697 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
        while cond697
            _t1294 = parse_type(parser)
            item698 = _t1294
            push!(xs696, item698)
            cond697 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
        end
        types699 = xs696
        consume_literal!(parser, "]")
        _t1293 = (nothing, types699,)
    else
        if prediction690 == 0
            _t1296 = parse_relation_id(parser)
            relation_id691 = _t1296
            consume_literal!(parser, "[")
            xs692 = Proto.var"#Type"[]
            cond693 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
            while cond693
                _t1297 = parse_type(parser)
                item694 = _t1297
                push!(xs692, item694)
                cond693 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
            end
            types695 = xs692
            consume_literal!(parser, "]")
            _t1295 = (relation_id691, types695,)
        else
            throw(ParseError("Unexpected token in csv_column_tail" * ": " * string(lookahead(parser, 0))))
        end
        _t1293 = _t1295
    end
    return _t1293
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string700 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string700
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1298 = parse_fragment_id(parser)
    fragment_id701 = _t1298
    consume_literal!(parser, ")")
    _t1299 = Proto.Undefine(fragment_id=fragment_id701)
    return _t1299
end

function parse_context(parser::ParserState)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs702 = Proto.RelationId[]
    cond703 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond703
        _t1300 = parse_relation_id(parser)
        item704 = _t1300
        push!(xs702, item704)
        cond703 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids705 = xs702
    consume_literal!(parser, ")")
    _t1301 = Proto.Context(relations=relation_ids705)
    return _t1301
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t1302 = parse_rel_edb_path(parser)
    rel_edb_path706 = _t1302
    _t1303 = parse_relation_id(parser)
    relation_id707 = _t1303
    consume_literal!(parser, ")")
    _t1304 = Proto.Snapshot(destination_path=rel_edb_path706, source_relation=relation_id707)
    return _t1304
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs708 = Proto.Read[]
    cond709 = match_lookahead_literal(parser, "(", 0)
    while cond709
        _t1305 = parse_read(parser)
        item710 = _t1305
        push!(xs708, item710)
        cond709 = match_lookahead_literal(parser, "(", 0)
    end
    reads711 = xs708
    consume_literal!(parser, ")")
    return reads711
end

function parse_read(parser::ParserState)::Proto.Read
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1307 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1308 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1309 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1310 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1311 = 3
                        else
                            _t1311 = -1
                        end
                        _t1310 = _t1311
                    end
                    _t1309 = _t1310
                end
                _t1308 = _t1309
            end
            _t1307 = _t1308
        end
        _t1306 = _t1307
    else
        _t1306 = -1
    end
    prediction712 = _t1306
    if prediction712 == 4
        _t1313 = parse_export(parser)
        export717 = _t1313
        _t1314 = Proto.Read(read_type=OneOf(:var"#export", export717))
        _t1312 = _t1314
    else
        if prediction712 == 3
            _t1316 = parse_abort(parser)
            abort716 = _t1316
            _t1317 = Proto.Read(read_type=OneOf(:abort, abort716))
            _t1315 = _t1317
        else
            if prediction712 == 2
                _t1319 = parse_what_if(parser)
                what_if715 = _t1319
                _t1320 = Proto.Read(read_type=OneOf(:what_if, what_if715))
                _t1318 = _t1320
            else
                if prediction712 == 1
                    _t1322 = parse_output(parser)
                    output714 = _t1322
                    _t1323 = Proto.Read(read_type=OneOf(:output, output714))
                    _t1321 = _t1323
                else
                    if prediction712 == 0
                        _t1325 = parse_demand(parser)
                        demand713 = _t1325
                        _t1326 = Proto.Read(read_type=OneOf(:demand, demand713))
                        _t1324 = _t1326
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1321 = _t1324
                end
                _t1318 = _t1321
            end
            _t1315 = _t1318
        end
        _t1312 = _t1315
    end
    return _t1312
end

function parse_demand(parser::ParserState)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1327 = parse_relation_id(parser)
    relation_id718 = _t1327
    consume_literal!(parser, ")")
    _t1328 = Proto.Demand(relation_id=relation_id718)
    return _t1328
end

function parse_output(parser::ParserState)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1329 = parse_name(parser)
    name719 = _t1329
    _t1330 = parse_relation_id(parser)
    relation_id720 = _t1330
    consume_literal!(parser, ")")
    _t1331 = Proto.Output(name=name719, relation_id=relation_id720)
    return _t1331
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1332 = parse_name(parser)
    name721 = _t1332
    _t1333 = parse_epoch(parser)
    epoch722 = _t1333
    consume_literal!(parser, ")")
    _t1334 = Proto.WhatIf(branch=name721, epoch=epoch722)
    return _t1334
end

function parse_abort(parser::ParserState)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1336 = parse_name(parser)
        _t1335 = _t1336
    else
        _t1335 = nothing
    end
    name723 = _t1335
    _t1337 = parse_relation_id(parser)
    relation_id724 = _t1337
    consume_literal!(parser, ")")
    _t1338 = Proto.Abort(name=(!isnothing(name723) ? name723 : "abort"), relation_id=relation_id724)
    return _t1338
end

function parse_export(parser::ParserState)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1339 = parse_export_csv_config(parser)
    export_csv_config725 = _t1339
    consume_literal!(parser, ")")
    _t1340 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config725))
    return _t1340
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1341 = parse_export_csv_path(parser)
    export_csv_path726 = _t1341
    _t1342 = parse_export_csv_columns(parser)
    export_csv_columns727 = _t1342
    _t1343 = parse_config_dict(parser)
    config_dict728 = _t1343
    consume_literal!(parser, ")")
    _t1344 = export_csv_config(parser, export_csv_path726, export_csv_columns727, config_dict728)
    return _t1344
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string729 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string729
end

function parse_export_csv_columns(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs730 = Proto.ExportCSVColumn[]
    cond731 = match_lookahead_literal(parser, "(", 0)
    while cond731
        _t1345 = parse_export_csv_column(parser)
        item732 = _t1345
        push!(xs730, item732)
        cond731 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns733 = xs730
    consume_literal!(parser, ")")
    return export_csv_columns733
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string734 = consume_terminal!(parser, "STRING")
    _t1346 = parse_relation_id(parser)
    relation_id735 = _t1346
    consume_literal!(parser, ")")
    _t1347 = Proto.ExportCSVColumn(column_name=string734, column_data=relation_id735)
    return _t1347
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
