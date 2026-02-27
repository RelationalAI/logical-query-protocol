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
    # Use little-endian to match the Go and Python SDKs.
    id_low = htol(reinterpret(UInt64, hash_bytes[1:8])[1])
    id_high = htol(reinterpret(UInt64, hash_bytes[9:16])[1])
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
        _t1378 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1379 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1380 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1381 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1382 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1383 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1384 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1385 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1386 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1387 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1387
    _t1388 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1388
    _t1389 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1389
    _t1390 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1390
    _t1391 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1391
    _t1392 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1392
    _t1393 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1393
    _t1394 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1394
    _t1395 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1395
    _t1396 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1396
    _t1397 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1397
    _t1398 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t1398
    _t1399 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t1399
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1400 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1400
    _t1401 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1401
    _t1402 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1402
    _t1403 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1403
    _t1404 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1404
    _t1405 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1405
    _t1406 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1406
    _t1407 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1407
    _t1408 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1408
    _t1409 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1409
    _t1410 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1410
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1411 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1411
    _t1412 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1412
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
    _t1413 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1413
    _t1414 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1414
    _t1415 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1415
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1416 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1416
    _t1417 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1417
    _t1418 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1418
    _t1419 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1419
    _t1420 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1420
    _t1421 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1421
    _t1422 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1422
    _t1423 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1423
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1424 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1424
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t753 = parse_configure(parser)
        _t752 = _t753
    else
        _t752 = nothing
    end
    configure376 = _t752
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t755 = parse_sync(parser)
        _t754 = _t755
    else
        _t754 = nothing
    end
    sync377 = _t754
    xs378 = Proto.Epoch[]
    cond379 = match_lookahead_literal(parser, "(", 0)
    while cond379
        _t756 = parse_epoch(parser)
        item380 = _t756
        push!(xs378, item380)
        cond379 = match_lookahead_literal(parser, "(", 0)
    end
    epochs381 = xs378
    consume_literal!(parser, ")")
    _t757 = default_configure(parser)
    _t758 = Proto.Transaction(epochs=epochs381, configure=(!isnothing(configure376) ? configure376 : _t757), sync=sync377)
    return _t758
end

function parse_configure(parser::ParserState)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t759 = parse_config_dict(parser)
    config_dict382 = _t759
    consume_literal!(parser, ")")
    _t760 = construct_configure(parser, config_dict382)
    return _t760
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs383 = Tuple{String, Proto.Value}[]
    cond384 = match_lookahead_literal(parser, ":", 0)
    while cond384
        _t761 = parse_config_key_value(parser)
        item385 = _t761
        push!(xs383, item385)
        cond384 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values386 = xs383
    consume_literal!(parser, "}")
    return config_key_values386
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol387 = consume_terminal!(parser, "SYMBOL")
    _t762 = parse_value(parser)
    value388 = _t762
    return (symbol387, value388,)
end

function parse_value(parser::ParserState)::Proto.Value
    if match_lookahead_literal(parser, "true", 0)
        _t763 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t764 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t765 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t767 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t768 = 0
                        else
                            _t768 = -1
                        end
                        _t767 = _t768
                    end
                    _t766 = _t767
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t769 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t770 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t771 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t772 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t773 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t774 = 7
                                        else
                                            _t774 = -1
                                        end
                                        _t773 = _t774
                                    end
                                    _t772 = _t773
                                end
                                _t771 = _t772
                            end
                            _t770 = _t771
                        end
                        _t769 = _t770
                    end
                    _t766 = _t769
                end
                _t765 = _t766
            end
            _t764 = _t765
        end
        _t763 = _t764
    end
    prediction389 = _t763
    if prediction389 == 9
        _t776 = parse_boolean_value(parser)
        boolean_value398 = _t776
        _t777 = Proto.Value(value=OneOf(:boolean_value, boolean_value398))
        _t775 = _t777
    else
        if prediction389 == 8
            consume_literal!(parser, "missing")
            _t779 = Proto.MissingValue()
            _t780 = Proto.Value(value=OneOf(:missing_value, _t779))
            _t778 = _t780
        else
            if prediction389 == 7
                decimal397 = consume_terminal!(parser, "DECIMAL")
                _t782 = Proto.Value(value=OneOf(:decimal_value, decimal397))
                _t781 = _t782
            else
                if prediction389 == 6
                    int128396 = consume_terminal!(parser, "INT128")
                    _t784 = Proto.Value(value=OneOf(:int128_value, int128396))
                    _t783 = _t784
                else
                    if prediction389 == 5
                        uint128395 = consume_terminal!(parser, "UINT128")
                        _t786 = Proto.Value(value=OneOf(:uint128_value, uint128395))
                        _t785 = _t786
                    else
                        if prediction389 == 4
                            float394 = consume_terminal!(parser, "FLOAT")
                            _t788 = Proto.Value(value=OneOf(:float_value, float394))
                            _t787 = _t788
                        else
                            if prediction389 == 3
                                int393 = consume_terminal!(parser, "INT")
                                _t790 = Proto.Value(value=OneOf(:int_value, int393))
                                _t789 = _t790
                            else
                                if prediction389 == 2
                                    string392 = consume_terminal!(parser, "STRING")
                                    _t792 = Proto.Value(value=OneOf(:string_value, string392))
                                    _t791 = _t792
                                else
                                    if prediction389 == 1
                                        _t794 = parse_datetime(parser)
                                        datetime391 = _t794
                                        _t795 = Proto.Value(value=OneOf(:datetime_value, datetime391))
                                        _t793 = _t795
                                    else
                                        if prediction389 == 0
                                            _t797 = parse_date(parser)
                                            date390 = _t797
                                            _t798 = Proto.Value(value=OneOf(:date_value, date390))
                                            _t796 = _t798
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t793 = _t796
                                    end
                                    _t791 = _t793
                                end
                                _t789 = _t791
                            end
                            _t787 = _t789
                        end
                        _t785 = _t787
                    end
                    _t783 = _t785
                end
                _t781 = _t783
            end
            _t778 = _t781
        end
        _t775 = _t778
    end
    return _t775
end

function parse_date(parser::ParserState)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int399 = consume_terminal!(parser, "INT")
    int_3400 = consume_terminal!(parser, "INT")
    int_4401 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t799 = Proto.DateValue(year=Int32(int399), month=Int32(int_3400), day=Int32(int_4401))
    return _t799
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int402 = consume_terminal!(parser, "INT")
    int_3403 = consume_terminal!(parser, "INT")
    int_4404 = consume_terminal!(parser, "INT")
    int_5405 = consume_terminal!(parser, "INT")
    int_6406 = consume_terminal!(parser, "INT")
    int_7407 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t800 = consume_terminal!(parser, "INT")
    else
        _t800 = nothing
    end
    int_8408 = _t800
    consume_literal!(parser, ")")
    _t801 = Proto.DateTimeValue(year=Int32(int402), month=Int32(int_3403), day=Int32(int_4404), hour=Int32(int_5405), minute=Int32(int_6406), second=Int32(int_7407), microsecond=Int32((!isnothing(int_8408) ? int_8408 : 0)))
    return _t801
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t802 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t803 = 1
        else
            _t803 = -1
        end
        _t802 = _t803
    end
    prediction409 = _t802
    if prediction409 == 1
        consume_literal!(parser, "false")
        _t804 = false
    else
        if prediction409 == 0
            consume_literal!(parser, "true")
            _t805 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t804 = _t805
    end
    return _t804
end

function parse_sync(parser::ParserState)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs410 = Proto.FragmentId[]
    cond411 = match_lookahead_literal(parser, ":", 0)
    while cond411
        _t806 = parse_fragment_id(parser)
        item412 = _t806
        push!(xs410, item412)
        cond411 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids413 = xs410
    consume_literal!(parser, ")")
    _t807 = Proto.Sync(fragments=fragment_ids413)
    return _t807
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol414 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol414))
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t809 = parse_epoch_writes(parser)
        _t808 = _t809
    else
        _t808 = nothing
    end
    epoch_writes415 = _t808
    if match_lookahead_literal(parser, "(", 0)
        _t811 = parse_epoch_reads(parser)
        _t810 = _t811
    else
        _t810 = nothing
    end
    epoch_reads416 = _t810
    consume_literal!(parser, ")")
    _t812 = Proto.Epoch(writes=(!isnothing(epoch_writes415) ? epoch_writes415 : Proto.Write[]), reads=(!isnothing(epoch_reads416) ? epoch_reads416 : Proto.Read[]))
    return _t812
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs417 = Proto.Write[]
    cond418 = match_lookahead_literal(parser, "(", 0)
    while cond418
        _t813 = parse_write(parser)
        item419 = _t813
        push!(xs417, item419)
        cond418 = match_lookahead_literal(parser, "(", 0)
    end
    writes420 = xs417
    consume_literal!(parser, ")")
    return writes420
end

function parse_write(parser::ParserState)::Proto.Write
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t815 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t816 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t817 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t818 = 2
                    else
                        _t818 = -1
                    end
                    _t817 = _t818
                end
                _t816 = _t817
            end
            _t815 = _t816
        end
        _t814 = _t815
    else
        _t814 = -1
    end
    prediction421 = _t814
    if prediction421 == 3
        _t820 = parse_snapshot(parser)
        snapshot425 = _t820
        _t821 = Proto.Write(write_type=OneOf(:snapshot, snapshot425))
        _t819 = _t821
    else
        if prediction421 == 2
            _t823 = parse_context(parser)
            context424 = _t823
            _t824 = Proto.Write(write_type=OneOf(:context, context424))
            _t822 = _t824
        else
            if prediction421 == 1
                _t826 = parse_undefine(parser)
                undefine423 = _t826
                _t827 = Proto.Write(write_type=OneOf(:undefine, undefine423))
                _t825 = _t827
            else
                if prediction421 == 0
                    _t829 = parse_define(parser)
                    define422 = _t829
                    _t830 = Proto.Write(write_type=OneOf(:define, define422))
                    _t828 = _t830
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t825 = _t828
            end
            _t822 = _t825
        end
        _t819 = _t822
    end
    return _t819
end

function parse_define(parser::ParserState)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t831 = parse_fragment(parser)
    fragment426 = _t831
    consume_literal!(parser, ")")
    _t832 = Proto.Define(fragment=fragment426)
    return _t832
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t833 = parse_new_fragment_id(parser)
    new_fragment_id427 = _t833
    xs428 = Proto.Declaration[]
    cond429 = match_lookahead_literal(parser, "(", 0)
    while cond429
        _t834 = parse_declaration(parser)
        item430 = _t834
        push!(xs428, item430)
        cond429 = match_lookahead_literal(parser, "(", 0)
    end
    declarations431 = xs428
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id427, declarations431)
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    _t835 = parse_fragment_id(parser)
    fragment_id432 = _t835
    start_fragment!(parser, fragment_id432)
    return fragment_id432
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "functional_dependency", 1)
            _t837 = 2
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t838 = 3
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t839 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t840 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t841 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t842 = 1
                            else
                                _t842 = -1
                            end
                            _t841 = _t842
                        end
                        _t840 = _t841
                    end
                    _t839 = _t840
                end
                _t838 = _t839
            end
            _t837 = _t838
        end
        _t836 = _t837
    else
        _t836 = -1
    end
    prediction433 = _t836
    if prediction433 == 3
        _t844 = parse_data(parser)
        data437 = _t844
        _t845 = Proto.Declaration(declaration_type=OneOf(:data, data437))
        _t843 = _t845
    else
        if prediction433 == 2
            _t847 = parse_constraint(parser)
            constraint436 = _t847
            _t848 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint436))
            _t846 = _t848
        else
            if prediction433 == 1
                _t850 = parse_algorithm(parser)
                algorithm435 = _t850
                _t851 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm435))
                _t849 = _t851
            else
                if prediction433 == 0
                    _t853 = parse_def(parser)
                    def434 = _t853
                    _t854 = Proto.Declaration(declaration_type=OneOf(:def, def434))
                    _t852 = _t854
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t849 = _t852
            end
            _t846 = _t849
        end
        _t843 = _t846
    end
    return _t843
end

function parse_def(parser::ParserState)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t855 = parse_relation_id(parser)
    relation_id438 = _t855
    _t856 = parse_abstraction(parser)
    abstraction439 = _t856
    if match_lookahead_literal(parser, "(", 0)
        _t858 = parse_attrs(parser)
        _t857 = _t858
    else
        _t857 = nothing
    end
    attrs440 = _t857
    consume_literal!(parser, ")")
    _t859 = Proto.Def(name=relation_id438, body=abstraction439, attrs=(!isnothing(attrs440) ? attrs440 : Proto.Attribute[]))
    return _t859
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    if match_lookahead_literal(parser, ":", 0)
        _t860 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t861 = 1
        else
            _t861 = -1
        end
        _t860 = _t861
    end
    prediction441 = _t860
    if prediction441 == 1
        uint128443 = consume_terminal!(parser, "UINT128")
        _t862 = Proto.RelationId(uint128443.low, uint128443.high)
    else
        if prediction441 == 0
            consume_literal!(parser, ":")
            symbol442 = consume_terminal!(parser, "SYMBOL")
            _t863 = relation_id_from_string(parser, symbol442)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t862 = _t863
    end
    return _t862
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t864 = parse_bindings(parser)
    bindings444 = _t864
    _t865 = parse_formula(parser)
    formula445 = _t865
    consume_literal!(parser, ")")
    _t866 = Proto.Abstraction(vars=vcat(bindings444[1], !isnothing(bindings444[2]) ? bindings444[2] : []), value=formula445)
    return _t866
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs446 = Proto.Binding[]
    cond447 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond447
        _t867 = parse_binding(parser)
        item448 = _t867
        push!(xs446, item448)
        cond447 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings449 = xs446
    if match_lookahead_literal(parser, "|", 0)
        _t869 = parse_value_bindings(parser)
        _t868 = _t869
    else
        _t868 = nothing
    end
    value_bindings450 = _t868
    consume_literal!(parser, "]")
    return (bindings449, (!isnothing(value_bindings450) ? value_bindings450 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    symbol451 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t870 = parse_type(parser)
    type452 = _t870
    _t871 = Proto.Var(name=symbol451)
    _t872 = Proto.Binding(var=_t871, var"#type"=type452)
    return _t872
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t873 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t874 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t875 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t876 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t877 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t878 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t879 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t880 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t881 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t882 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t883 = 9
                                            else
                                                _t883 = -1
                                            end
                                            _t882 = _t883
                                        end
                                        _t881 = _t882
                                    end
                                    _t880 = _t881
                                end
                                _t879 = _t880
                            end
                            _t878 = _t879
                        end
                        _t877 = _t878
                    end
                    _t876 = _t877
                end
                _t875 = _t876
            end
            _t874 = _t875
        end
        _t873 = _t874
    end
    prediction453 = _t873
    if prediction453 == 10
        _t885 = parse_boolean_type(parser)
        boolean_type464 = _t885
        _t886 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type464))
        _t884 = _t886
    else
        if prediction453 == 9
            _t888 = parse_decimal_type(parser)
            decimal_type463 = _t888
            _t889 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type463))
            _t887 = _t889
        else
            if prediction453 == 8
                _t891 = parse_missing_type(parser)
                missing_type462 = _t891
                _t892 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type462))
                _t890 = _t892
            else
                if prediction453 == 7
                    _t894 = parse_datetime_type(parser)
                    datetime_type461 = _t894
                    _t895 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type461))
                    _t893 = _t895
                else
                    if prediction453 == 6
                        _t897 = parse_date_type(parser)
                        date_type460 = _t897
                        _t898 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type460))
                        _t896 = _t898
                    else
                        if prediction453 == 5
                            _t900 = parse_int128_type(parser)
                            int128_type459 = _t900
                            _t901 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type459))
                            _t899 = _t901
                        else
                            if prediction453 == 4
                                _t903 = parse_uint128_type(parser)
                                uint128_type458 = _t903
                                _t904 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type458))
                                _t902 = _t904
                            else
                                if prediction453 == 3
                                    _t906 = parse_float_type(parser)
                                    float_type457 = _t906
                                    _t907 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type457))
                                    _t905 = _t907
                                else
                                    if prediction453 == 2
                                        _t909 = parse_int_type(parser)
                                        int_type456 = _t909
                                        _t910 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type456))
                                        _t908 = _t910
                                    else
                                        if prediction453 == 1
                                            _t912 = parse_string_type(parser)
                                            string_type455 = _t912
                                            _t913 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type455))
                                            _t911 = _t913
                                        else
                                            if prediction453 == 0
                                                _t915 = parse_unspecified_type(parser)
                                                unspecified_type454 = _t915
                                                _t916 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type454))
                                                _t914 = _t916
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t911 = _t914
                                        end
                                        _t908 = _t911
                                    end
                                    _t905 = _t908
                                end
                                _t902 = _t905
                            end
                            _t899 = _t902
                        end
                        _t896 = _t899
                    end
                    _t893 = _t896
                end
                _t890 = _t893
            end
            _t887 = _t890
        end
        _t884 = _t887
    end
    return _t884
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t917 = Proto.UnspecifiedType()
    return _t917
end

function parse_string_type(parser::ParserState)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t918 = Proto.StringType()
    return _t918
end

function parse_int_type(parser::ParserState)::Proto.IntType
    consume_literal!(parser, "INT")
    _t919 = Proto.IntType()
    return _t919
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t920 = Proto.FloatType()
    return _t920
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t921 = Proto.UInt128Type()
    return _t921
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t922 = Proto.Int128Type()
    return _t922
end

function parse_date_type(parser::ParserState)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t923 = Proto.DateType()
    return _t923
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t924 = Proto.DateTimeType()
    return _t924
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t925 = Proto.MissingType()
    return _t925
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int465 = consume_terminal!(parser, "INT")
    int_3466 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t926 = Proto.DecimalType(precision=Int32(int465), scale=Int32(int_3466))
    return _t926
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t927 = Proto.BooleanType()
    return _t927
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs467 = Proto.Binding[]
    cond468 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond468
        _t928 = parse_binding(parser)
        item469 = _t928
        push!(xs467, item469)
        cond468 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings470 = xs467
    return bindings470
end

function parse_formula(parser::ParserState)::Proto.Formula
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t930 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t931 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t932 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t933 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t934 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t935 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t936 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t937 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t938 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t939 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t940 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t941 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t942 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t943 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t944 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t945 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t946 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t947 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t948 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t949 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t950 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t951 = 10
                                                                                            else
                                                                                                _t951 = -1
                                                                                            end
                                                                                            _t950 = _t951
                                                                                        end
                                                                                        _t949 = _t950
                                                                                    end
                                                                                    _t948 = _t949
                                                                                end
                                                                                _t947 = _t948
                                                                            end
                                                                            _t946 = _t947
                                                                        end
                                                                        _t945 = _t946
                                                                    end
                                                                    _t944 = _t945
                                                                end
                                                                _t943 = _t944
                                                            end
                                                            _t942 = _t943
                                                        end
                                                        _t941 = _t942
                                                    end
                                                    _t940 = _t941
                                                end
                                                _t939 = _t940
                                            end
                                            _t938 = _t939
                                        end
                                        _t937 = _t938
                                    end
                                    _t936 = _t937
                                end
                                _t935 = _t936
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
    else
        _t929 = -1
    end
    prediction471 = _t929
    if prediction471 == 12
        _t953 = parse_cast(parser)
        cast484 = _t953
        _t954 = Proto.Formula(formula_type=OneOf(:cast, cast484))
        _t952 = _t954
    else
        if prediction471 == 11
            _t956 = parse_rel_atom(parser)
            rel_atom483 = _t956
            _t957 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom483))
            _t955 = _t957
        else
            if prediction471 == 10
                _t959 = parse_primitive(parser)
                primitive482 = _t959
                _t960 = Proto.Formula(formula_type=OneOf(:primitive, primitive482))
                _t958 = _t960
            else
                if prediction471 == 9
                    _t962 = parse_pragma(parser)
                    pragma481 = _t962
                    _t963 = Proto.Formula(formula_type=OneOf(:pragma, pragma481))
                    _t961 = _t963
                else
                    if prediction471 == 8
                        _t965 = parse_atom(parser)
                        atom480 = _t965
                        _t966 = Proto.Formula(formula_type=OneOf(:atom, atom480))
                        _t964 = _t966
                    else
                        if prediction471 == 7
                            _t968 = parse_ffi(parser)
                            ffi479 = _t968
                            _t969 = Proto.Formula(formula_type=OneOf(:ffi, ffi479))
                            _t967 = _t969
                        else
                            if prediction471 == 6
                                _t971 = parse_not(parser)
                                not478 = _t971
                                _t972 = Proto.Formula(formula_type=OneOf(:not, not478))
                                _t970 = _t972
                            else
                                if prediction471 == 5
                                    _t974 = parse_disjunction(parser)
                                    disjunction477 = _t974
                                    _t975 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction477))
                                    _t973 = _t975
                                else
                                    if prediction471 == 4
                                        _t977 = parse_conjunction(parser)
                                        conjunction476 = _t977
                                        _t978 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction476))
                                        _t976 = _t978
                                    else
                                        if prediction471 == 3
                                            _t980 = parse_reduce(parser)
                                            reduce475 = _t980
                                            _t981 = Proto.Formula(formula_type=OneOf(:reduce, reduce475))
                                            _t979 = _t981
                                        else
                                            if prediction471 == 2
                                                _t983 = parse_exists(parser)
                                                exists474 = _t983
                                                _t984 = Proto.Formula(formula_type=OneOf(:exists, exists474))
                                                _t982 = _t984
                                            else
                                                if prediction471 == 1
                                                    _t986 = parse_false(parser)
                                                    false473 = _t986
                                                    _t987 = Proto.Formula(formula_type=OneOf(:disjunction, false473))
                                                    _t985 = _t987
                                                else
                                                    if prediction471 == 0
                                                        _t989 = parse_true(parser)
                                                        true472 = _t989
                                                        _t990 = Proto.Formula(formula_type=OneOf(:conjunction, true472))
                                                        _t988 = _t990
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t985 = _t988
                                                end
                                                _t982 = _t985
                                            end
                                            _t979 = _t982
                                        end
                                        _t976 = _t979
                                    end
                                    _t973 = _t976
                                end
                                _t970 = _t973
                            end
                            _t967 = _t970
                        end
                        _t964 = _t967
                    end
                    _t961 = _t964
                end
                _t958 = _t961
            end
            _t955 = _t958
        end
        _t952 = _t955
    end
    return _t952
end

function parse_true(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t991 = Proto.Conjunction(args=Proto.Formula[])
    return _t991
end

function parse_false(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t992 = Proto.Disjunction(args=Proto.Formula[])
    return _t992
end

function parse_exists(parser::ParserState)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t993 = parse_bindings(parser)
    bindings485 = _t993
    _t994 = parse_formula(parser)
    formula486 = _t994
    consume_literal!(parser, ")")
    _t995 = Proto.Abstraction(vars=vcat(bindings485[1], !isnothing(bindings485[2]) ? bindings485[2] : []), value=formula486)
    _t996 = Proto.Exists(body=_t995)
    return _t996
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t997 = parse_abstraction(parser)
    abstraction487 = _t997
    _t998 = parse_abstraction(parser)
    abstraction_3488 = _t998
    _t999 = parse_terms(parser)
    terms489 = _t999
    consume_literal!(parser, ")")
    _t1000 = Proto.Reduce(op=abstraction487, body=abstraction_3488, terms=terms489)
    return _t1000
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs490 = Proto.Term[]
    cond491 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond491
        _t1001 = parse_term(parser)
        item492 = _t1001
        push!(xs490, item492)
        cond491 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms493 = xs490
    consume_literal!(parser, ")")
    return terms493
end

function parse_term(parser::ParserState)::Proto.Term
    if match_lookahead_literal(parser, "true", 0)
        _t1002 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1003 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1004 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1005 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1006 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1007 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1008 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1009 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1010 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t1011 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t1012 = 1
                                            else
                                                _t1012 = -1
                                            end
                                            _t1011 = _t1012
                                        end
                                        _t1010 = _t1011
                                    end
                                    _t1009 = _t1010
                                end
                                _t1008 = _t1009
                            end
                            _t1007 = _t1008
                        end
                        _t1006 = _t1007
                    end
                    _t1005 = _t1006
                end
                _t1004 = _t1005
            end
            _t1003 = _t1004
        end
        _t1002 = _t1003
    end
    prediction494 = _t1002
    if prediction494 == 1
        _t1014 = parse_constant(parser)
        constant496 = _t1014
        _t1015 = Proto.Term(term_type=OneOf(:constant, constant496))
        _t1013 = _t1015
    else
        if prediction494 == 0
            _t1017 = parse_var(parser)
            var495 = _t1017
            _t1018 = Proto.Term(term_type=OneOf(:var, var495))
            _t1016 = _t1018
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1013 = _t1016
    end
    return _t1013
end

function parse_var(parser::ParserState)::Proto.Var
    symbol497 = consume_terminal!(parser, "SYMBOL")
    _t1019 = Proto.Var(name=symbol497)
    return _t1019
end

function parse_constant(parser::ParserState)::Proto.Value
    _t1020 = parse_value(parser)
    value498 = _t1020
    return value498
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs499 = Proto.Formula[]
    cond500 = match_lookahead_literal(parser, "(", 0)
    while cond500
        _t1021 = parse_formula(parser)
        item501 = _t1021
        push!(xs499, item501)
        cond500 = match_lookahead_literal(parser, "(", 0)
    end
    formulas502 = xs499
    consume_literal!(parser, ")")
    _t1022 = Proto.Conjunction(args=formulas502)
    return _t1022
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs503 = Proto.Formula[]
    cond504 = match_lookahead_literal(parser, "(", 0)
    while cond504
        _t1023 = parse_formula(parser)
        item505 = _t1023
        push!(xs503, item505)
        cond504 = match_lookahead_literal(parser, "(", 0)
    end
    formulas506 = xs503
    consume_literal!(parser, ")")
    _t1024 = Proto.Disjunction(args=formulas506)
    return _t1024
end

function parse_not(parser::ParserState)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1025 = parse_formula(parser)
    formula507 = _t1025
    consume_literal!(parser, ")")
    _t1026 = Proto.Not(arg=formula507)
    return _t1026
end

function parse_ffi(parser::ParserState)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1027 = parse_name(parser)
    name508 = _t1027
    _t1028 = parse_ffi_args(parser)
    ffi_args509 = _t1028
    _t1029 = parse_terms(parser)
    terms510 = _t1029
    consume_literal!(parser, ")")
    _t1030 = Proto.FFI(name=name508, args=ffi_args509, terms=terms510)
    return _t1030
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol511 = consume_terminal!(parser, "SYMBOL")
    return symbol511
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs512 = Proto.Abstraction[]
    cond513 = match_lookahead_literal(parser, "(", 0)
    while cond513
        _t1031 = parse_abstraction(parser)
        item514 = _t1031
        push!(xs512, item514)
        cond513 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions515 = xs512
    consume_literal!(parser, ")")
    return abstractions515
end

function parse_atom(parser::ParserState)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1032 = parse_relation_id(parser)
    relation_id516 = _t1032
    xs517 = Proto.Term[]
    cond518 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond518
        _t1033 = parse_term(parser)
        item519 = _t1033
        push!(xs517, item519)
        cond518 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms520 = xs517
    consume_literal!(parser, ")")
    _t1034 = Proto.Atom(name=relation_id516, terms=terms520)
    return _t1034
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1035 = parse_name(parser)
    name521 = _t1035
    xs522 = Proto.Term[]
    cond523 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond523
        _t1036 = parse_term(parser)
        item524 = _t1036
        push!(xs522, item524)
        cond523 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms525 = xs522
    consume_literal!(parser, ")")
    _t1037 = Proto.Pragma(name=name521, terms=terms525)
    return _t1037
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1039 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1040 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1041 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1042 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1043 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1044 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1045 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1046 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1047 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1048 = 7
                                            else
                                                _t1048 = -1
                                            end
                                            _t1047 = _t1048
                                        end
                                        _t1046 = _t1047
                                    end
                                    _t1045 = _t1046
                                end
                                _t1044 = _t1045
                            end
                            _t1043 = _t1044
                        end
                        _t1042 = _t1043
                    end
                    _t1041 = _t1042
                end
                _t1040 = _t1041
            end
            _t1039 = _t1040
        end
        _t1038 = _t1039
    else
        _t1038 = -1
    end
    prediction526 = _t1038
    if prediction526 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1050 = parse_name(parser)
        name536 = _t1050
        xs537 = Proto.RelTerm[]
        cond538 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond538
            _t1051 = parse_rel_term(parser)
            item539 = _t1051
            push!(xs537, item539)
            cond538 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms540 = xs537
        consume_literal!(parser, ")")
        _t1052 = Proto.Primitive(name=name536, terms=rel_terms540)
        _t1049 = _t1052
    else
        if prediction526 == 8
            _t1054 = parse_divide(parser)
            divide535 = _t1054
            _t1053 = divide535
        else
            if prediction526 == 7
                _t1056 = parse_multiply(parser)
                multiply534 = _t1056
                _t1055 = multiply534
            else
                if prediction526 == 6
                    _t1058 = parse_minus(parser)
                    minus533 = _t1058
                    _t1057 = minus533
                else
                    if prediction526 == 5
                        _t1060 = parse_add(parser)
                        add532 = _t1060
                        _t1059 = add532
                    else
                        if prediction526 == 4
                            _t1062 = parse_gt_eq(parser)
                            gt_eq531 = _t1062
                            _t1061 = gt_eq531
                        else
                            if prediction526 == 3
                                _t1064 = parse_gt(parser)
                                gt530 = _t1064
                                _t1063 = gt530
                            else
                                if prediction526 == 2
                                    _t1066 = parse_lt_eq(parser)
                                    lt_eq529 = _t1066
                                    _t1065 = lt_eq529
                                else
                                    if prediction526 == 1
                                        _t1068 = parse_lt(parser)
                                        lt528 = _t1068
                                        _t1067 = lt528
                                    else
                                        if prediction526 == 0
                                            _t1070 = parse_eq(parser)
                                            eq527 = _t1070
                                            _t1069 = eq527
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1067 = _t1069
                                    end
                                    _t1065 = _t1067
                                end
                                _t1063 = _t1065
                            end
                            _t1061 = _t1063
                        end
                        _t1059 = _t1061
                    end
                    _t1057 = _t1059
                end
                _t1055 = _t1057
            end
            _t1053 = _t1055
        end
        _t1049 = _t1053
    end
    return _t1049
end

function parse_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1071 = parse_term(parser)
    term541 = _t1071
    _t1072 = parse_term(parser)
    term_3542 = _t1072
    consume_literal!(parser, ")")
    _t1073 = Proto.RelTerm(rel_term_type=OneOf(:term, term541))
    _t1074 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3542))
    _t1075 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1073, _t1074])
    return _t1075
end

function parse_lt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1076 = parse_term(parser)
    term543 = _t1076
    _t1077 = parse_term(parser)
    term_3544 = _t1077
    consume_literal!(parser, ")")
    _t1078 = Proto.RelTerm(rel_term_type=OneOf(:term, term543))
    _t1079 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3544))
    _t1080 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1078, _t1079])
    return _t1080
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1081 = parse_term(parser)
    term545 = _t1081
    _t1082 = parse_term(parser)
    term_3546 = _t1082
    consume_literal!(parser, ")")
    _t1083 = Proto.RelTerm(rel_term_type=OneOf(:term, term545))
    _t1084 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3546))
    _t1085 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1083, _t1084])
    return _t1085
end

function parse_gt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1086 = parse_term(parser)
    term547 = _t1086
    _t1087 = parse_term(parser)
    term_3548 = _t1087
    consume_literal!(parser, ")")
    _t1088 = Proto.RelTerm(rel_term_type=OneOf(:term, term547))
    _t1089 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3548))
    _t1090 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1088, _t1089])
    return _t1090
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1091 = parse_term(parser)
    term549 = _t1091
    _t1092 = parse_term(parser)
    term_3550 = _t1092
    consume_literal!(parser, ")")
    _t1093 = Proto.RelTerm(rel_term_type=OneOf(:term, term549))
    _t1094 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3550))
    _t1095 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1093, _t1094])
    return _t1095
end

function parse_add(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1096 = parse_term(parser)
    term551 = _t1096
    _t1097 = parse_term(parser)
    term_3552 = _t1097
    _t1098 = parse_term(parser)
    term_4553 = _t1098
    consume_literal!(parser, ")")
    _t1099 = Proto.RelTerm(rel_term_type=OneOf(:term, term551))
    _t1100 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3552))
    _t1101 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4553))
    _t1102 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1099, _t1100, _t1101])
    return _t1102
end

function parse_minus(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1103 = parse_term(parser)
    term554 = _t1103
    _t1104 = parse_term(parser)
    term_3555 = _t1104
    _t1105 = parse_term(parser)
    term_4556 = _t1105
    consume_literal!(parser, ")")
    _t1106 = Proto.RelTerm(rel_term_type=OneOf(:term, term554))
    _t1107 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3555))
    _t1108 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4556))
    _t1109 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1106, _t1107, _t1108])
    return _t1109
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1110 = parse_term(parser)
    term557 = _t1110
    _t1111 = parse_term(parser)
    term_3558 = _t1111
    _t1112 = parse_term(parser)
    term_4559 = _t1112
    consume_literal!(parser, ")")
    _t1113 = Proto.RelTerm(rel_term_type=OneOf(:term, term557))
    _t1114 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3558))
    _t1115 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4559))
    _t1116 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1113, _t1114, _t1115])
    return _t1116
end

function parse_divide(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1117 = parse_term(parser)
    term560 = _t1117
    _t1118 = parse_term(parser)
    term_3561 = _t1118
    _t1119 = parse_term(parser)
    term_4562 = _t1119
    consume_literal!(parser, ")")
    _t1120 = Proto.RelTerm(rel_term_type=OneOf(:term, term560))
    _t1121 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3561))
    _t1122 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4562))
    _t1123 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1120, _t1121, _t1122])
    return _t1123
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    if match_lookahead_literal(parser, "true", 0)
        _t1124 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1125 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1126 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1127 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1128 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1129 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1130 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1131 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1132 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1133 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1134 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1135 = 1
                                                else
                                                    _t1135 = -1
                                                end
                                                _t1134 = _t1135
                                            end
                                            _t1133 = _t1134
                                        end
                                        _t1132 = _t1133
                                    end
                                    _t1131 = _t1132
                                end
                                _t1130 = _t1131
                            end
                            _t1129 = _t1130
                        end
                        _t1128 = _t1129
                    end
                    _t1127 = _t1128
                end
                _t1126 = _t1127
            end
            _t1125 = _t1126
        end
        _t1124 = _t1125
    end
    prediction563 = _t1124
    if prediction563 == 1
        _t1137 = parse_term(parser)
        term565 = _t1137
        _t1138 = Proto.RelTerm(rel_term_type=OneOf(:term, term565))
        _t1136 = _t1138
    else
        if prediction563 == 0
            _t1140 = parse_specialized_value(parser)
            specialized_value564 = _t1140
            _t1141 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value564))
            _t1139 = _t1141
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1136 = _t1139
    end
    return _t1136
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    consume_literal!(parser, "#")
    _t1142 = parse_value(parser)
    value566 = _t1142
    return value566
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1143 = parse_name(parser)
    name567 = _t1143
    xs568 = Proto.RelTerm[]
    cond569 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond569
        _t1144 = parse_rel_term(parser)
        item570 = _t1144
        push!(xs568, item570)
        cond569 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms571 = xs568
    consume_literal!(parser, ")")
    _t1145 = Proto.RelAtom(name=name567, terms=rel_terms571)
    return _t1145
end

function parse_cast(parser::ParserState)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1146 = parse_term(parser)
    term572 = _t1146
    _t1147 = parse_term(parser)
    term_3573 = _t1147
    consume_literal!(parser, ")")
    _t1148 = Proto.Cast(input=term572, result=term_3573)
    return _t1148
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs574 = Proto.Attribute[]
    cond575 = match_lookahead_literal(parser, "(", 0)
    while cond575
        _t1149 = parse_attribute(parser)
        item576 = _t1149
        push!(xs574, item576)
        cond575 = match_lookahead_literal(parser, "(", 0)
    end
    attributes577 = xs574
    consume_literal!(parser, ")")
    return attributes577
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1150 = parse_name(parser)
    name578 = _t1150
    xs579 = Proto.Value[]
    cond580 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond580
        _t1151 = parse_value(parser)
        item581 = _t1151
        push!(xs579, item581)
        cond580 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values582 = xs579
    consume_literal!(parser, ")")
    _t1152 = Proto.Attribute(name=name578, args=values582)
    return _t1152
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs583 = Proto.RelationId[]
    cond584 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond584
        _t1153 = parse_relation_id(parser)
        item585 = _t1153
        push!(xs583, item585)
        cond584 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids586 = xs583
    _t1154 = parse_script(parser)
    script587 = _t1154
    consume_literal!(parser, ")")
    _t1155 = Proto.Algorithm(var"#global"=relation_ids586, body=script587)
    return _t1155
end

function parse_script(parser::ParserState)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs588 = Proto.Construct[]
    cond589 = match_lookahead_literal(parser, "(", 0)
    while cond589
        _t1156 = parse_construct(parser)
        item590 = _t1156
        push!(xs588, item590)
        cond589 = match_lookahead_literal(parser, "(", 0)
    end
    constructs591 = xs588
    consume_literal!(parser, ")")
    _t1157 = Proto.Script(constructs=constructs591)
    return _t1157
end

function parse_construct(parser::ParserState)::Proto.Construct
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1159 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1160 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1161 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1162 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1163 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1164 = 1
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
        end
        _t1158 = _t1159
    else
        _t1158 = -1
    end
    prediction592 = _t1158
    if prediction592 == 1
        _t1166 = parse_instruction(parser)
        instruction594 = _t1166
        _t1167 = Proto.Construct(construct_type=OneOf(:instruction, instruction594))
        _t1165 = _t1167
    else
        if prediction592 == 0
            _t1169 = parse_loop(parser)
            loop593 = _t1169
            _t1170 = Proto.Construct(construct_type=OneOf(:loop, loop593))
            _t1168 = _t1170
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1165 = _t1168
    end
    return _t1165
end

function parse_loop(parser::ParserState)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1171 = parse_init(parser)
    init595 = _t1171
    _t1172 = parse_script(parser)
    script596 = _t1172
    consume_literal!(parser, ")")
    _t1173 = Proto.Loop(init=init595, body=script596)
    return _t1173
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs597 = Proto.Instruction[]
    cond598 = match_lookahead_literal(parser, "(", 0)
    while cond598
        _t1174 = parse_instruction(parser)
        item599 = _t1174
        push!(xs597, item599)
        cond598 = match_lookahead_literal(parser, "(", 0)
    end
    instructions600 = xs597
    consume_literal!(parser, ")")
    return instructions600
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1176 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1177 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1178 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1179 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1180 = 0
                        else
                            _t1180 = -1
                        end
                        _t1179 = _t1180
                    end
                    _t1178 = _t1179
                end
                _t1177 = _t1178
            end
            _t1176 = _t1177
        end
        _t1175 = _t1176
    else
        _t1175 = -1
    end
    prediction601 = _t1175
    if prediction601 == 4
        _t1182 = parse_monus_def(parser)
        monus_def606 = _t1182
        _t1183 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def606))
        _t1181 = _t1183
    else
        if prediction601 == 3
            _t1185 = parse_monoid_def(parser)
            monoid_def605 = _t1185
            _t1186 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def605))
            _t1184 = _t1186
        else
            if prediction601 == 2
                _t1188 = parse_break(parser)
                break604 = _t1188
                _t1189 = Proto.Instruction(instr_type=OneOf(:var"#break", break604))
                _t1187 = _t1189
            else
                if prediction601 == 1
                    _t1191 = parse_upsert(parser)
                    upsert603 = _t1191
                    _t1192 = Proto.Instruction(instr_type=OneOf(:upsert, upsert603))
                    _t1190 = _t1192
                else
                    if prediction601 == 0
                        _t1194 = parse_assign(parser)
                        assign602 = _t1194
                        _t1195 = Proto.Instruction(instr_type=OneOf(:assign, assign602))
                        _t1193 = _t1195
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1190 = _t1193
                end
                _t1187 = _t1190
            end
            _t1184 = _t1187
        end
        _t1181 = _t1184
    end
    return _t1181
end

function parse_assign(parser::ParserState)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1196 = parse_relation_id(parser)
    relation_id607 = _t1196
    _t1197 = parse_abstraction(parser)
    abstraction608 = _t1197
    if match_lookahead_literal(parser, "(", 0)
        _t1199 = parse_attrs(parser)
        _t1198 = _t1199
    else
        _t1198 = nothing
    end
    attrs609 = _t1198
    consume_literal!(parser, ")")
    _t1200 = Proto.Assign(name=relation_id607, body=abstraction608, attrs=(!isnothing(attrs609) ? attrs609 : Proto.Attribute[]))
    return _t1200
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1201 = parse_relation_id(parser)
    relation_id610 = _t1201
    _t1202 = parse_abstraction_with_arity(parser)
    abstraction_with_arity611 = _t1202
    if match_lookahead_literal(parser, "(", 0)
        _t1204 = parse_attrs(parser)
        _t1203 = _t1204
    else
        _t1203 = nothing
    end
    attrs612 = _t1203
    consume_literal!(parser, ")")
    _t1205 = Proto.Upsert(name=relation_id610, body=abstraction_with_arity611[1], attrs=(!isnothing(attrs612) ? attrs612 : Proto.Attribute[]), value_arity=abstraction_with_arity611[2])
    return _t1205
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1206 = parse_bindings(parser)
    bindings613 = _t1206
    _t1207 = parse_formula(parser)
    formula614 = _t1207
    consume_literal!(parser, ")")
    _t1208 = Proto.Abstraction(vars=vcat(bindings613[1], !isnothing(bindings613[2]) ? bindings613[2] : []), value=formula614)
    return (_t1208, length(bindings613[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1209 = parse_relation_id(parser)
    relation_id615 = _t1209
    _t1210 = parse_abstraction(parser)
    abstraction616 = _t1210
    if match_lookahead_literal(parser, "(", 0)
        _t1212 = parse_attrs(parser)
        _t1211 = _t1212
    else
        _t1211 = nothing
    end
    attrs617 = _t1211
    consume_literal!(parser, ")")
    _t1213 = Proto.Break(name=relation_id615, body=abstraction616, attrs=(!isnothing(attrs617) ? attrs617 : Proto.Attribute[]))
    return _t1213
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1214 = parse_monoid(parser)
    monoid618 = _t1214
    _t1215 = parse_relation_id(parser)
    relation_id619 = _t1215
    _t1216 = parse_abstraction_with_arity(parser)
    abstraction_with_arity620 = _t1216
    if match_lookahead_literal(parser, "(", 0)
        _t1218 = parse_attrs(parser)
        _t1217 = _t1218
    else
        _t1217 = nothing
    end
    attrs621 = _t1217
    consume_literal!(parser, ")")
    _t1219 = Proto.MonoidDef(monoid=monoid618, name=relation_id619, body=abstraction_with_arity620[1], attrs=(!isnothing(attrs621) ? attrs621 : Proto.Attribute[]), value_arity=abstraction_with_arity620[2])
    return _t1219
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1221 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1222 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1223 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1224 = 2
                    else
                        _t1224 = -1
                    end
                    _t1223 = _t1224
                end
                _t1222 = _t1223
            end
            _t1221 = _t1222
        end
        _t1220 = _t1221
    else
        _t1220 = -1
    end
    prediction622 = _t1220
    if prediction622 == 3
        _t1226 = parse_sum_monoid(parser)
        sum_monoid626 = _t1226
        _t1227 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid626))
        _t1225 = _t1227
    else
        if prediction622 == 2
            _t1229 = parse_max_monoid(parser)
            max_monoid625 = _t1229
            _t1230 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid625))
            _t1228 = _t1230
        else
            if prediction622 == 1
                _t1232 = parse_min_monoid(parser)
                min_monoid624 = _t1232
                _t1233 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid624))
                _t1231 = _t1233
            else
                if prediction622 == 0
                    _t1235 = parse_or_monoid(parser)
                    or_monoid623 = _t1235
                    _t1236 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid623))
                    _t1234 = _t1236
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1231 = _t1234
            end
            _t1228 = _t1231
        end
        _t1225 = _t1228
    end
    return _t1225
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1237 = Proto.OrMonoid()
    return _t1237
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1238 = parse_type(parser)
    type627 = _t1238
    consume_literal!(parser, ")")
    _t1239 = Proto.MinMonoid(var"#type"=type627)
    return _t1239
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1240 = parse_type(parser)
    type628 = _t1240
    consume_literal!(parser, ")")
    _t1241 = Proto.MaxMonoid(var"#type"=type628)
    return _t1241
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1242 = parse_type(parser)
    type629 = _t1242
    consume_literal!(parser, ")")
    _t1243 = Proto.SumMonoid(var"#type"=type629)
    return _t1243
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1244 = parse_monoid(parser)
    monoid630 = _t1244
    _t1245 = parse_relation_id(parser)
    relation_id631 = _t1245
    _t1246 = parse_abstraction_with_arity(parser)
    abstraction_with_arity632 = _t1246
    if match_lookahead_literal(parser, "(", 0)
        _t1248 = parse_attrs(parser)
        _t1247 = _t1248
    else
        _t1247 = nothing
    end
    attrs633 = _t1247
    consume_literal!(parser, ")")
    _t1249 = Proto.MonusDef(monoid=monoid630, name=relation_id631, body=abstraction_with_arity632[1], attrs=(!isnothing(attrs633) ? attrs633 : Proto.Attribute[]), value_arity=abstraction_with_arity632[2])
    return _t1249
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1250 = parse_relation_id(parser)
    relation_id634 = _t1250
    _t1251 = parse_abstraction(parser)
    abstraction635 = _t1251
    _t1252 = parse_functional_dependency_keys(parser)
    functional_dependency_keys636 = _t1252
    _t1253 = parse_functional_dependency_values(parser)
    functional_dependency_values637 = _t1253
    consume_literal!(parser, ")")
    _t1254 = Proto.FunctionalDependency(guard=abstraction635, keys=functional_dependency_keys636, values=functional_dependency_values637)
    _t1255 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1254), name=relation_id634)
    return _t1255
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs638 = Proto.Var[]
    cond639 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond639
        _t1256 = parse_var(parser)
        item640 = _t1256
        push!(xs638, item640)
        cond639 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars641 = xs638
    consume_literal!(parser, ")")
    return vars641
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs642 = Proto.Var[]
    cond643 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond643
        _t1257 = parse_var(parser)
        item644 = _t1257
        push!(xs642, item644)
        cond643 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars645 = xs642
    consume_literal!(parser, ")")
    return vars645
end

function parse_data(parser::ParserState)::Proto.Data
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "edb", 1)
            _t1259 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1260 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1261 = 1
                else
                    _t1261 = -1
                end
                _t1260 = _t1261
            end
            _t1259 = _t1260
        end
        _t1258 = _t1259
    else
        _t1258 = -1
    end
    prediction646 = _t1258
    if prediction646 == 2
        _t1263 = parse_csv_data(parser)
        csv_data649 = _t1263
        _t1264 = Proto.Data(data_type=OneOf(:csv_data, csv_data649))
        _t1262 = _t1264
    else
        if prediction646 == 1
            _t1266 = parse_betree_relation(parser)
            betree_relation648 = _t1266
            _t1267 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation648))
            _t1265 = _t1267
        else
            if prediction646 == 0
                _t1269 = parse_edb(parser)
                edb647 = _t1269
                _t1270 = Proto.Data(data_type=OneOf(:edb, edb647))
                _t1268 = _t1270
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1265 = _t1268
        end
        _t1262 = _t1265
    end
    return _t1262
end

function parse_edb(parser::ParserState)::Proto.EDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1271 = parse_relation_id(parser)
    relation_id650 = _t1271
    _t1272 = parse_edb_path(parser)
    edb_path651 = _t1272
    _t1273 = parse_edb_types(parser)
    edb_types652 = _t1273
    consume_literal!(parser, ")")
    _t1274 = Proto.EDB(target_id=relation_id650, path=edb_path651, types=edb_types652)
    return _t1274
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs653 = String[]
    cond654 = match_lookahead_terminal(parser, "STRING", 0)
    while cond654
        item655 = consume_terminal!(parser, "STRING")
        push!(xs653, item655)
        cond654 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings656 = xs653
    consume_literal!(parser, "]")
    return strings656
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs657 = Proto.var"#Type"[]
    cond658 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond658
        _t1275 = parse_type(parser)
        item659 = _t1275
        push!(xs657, item659)
        cond658 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types660 = xs657
    consume_literal!(parser, "]")
    return types660
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1276 = parse_relation_id(parser)
    relation_id661 = _t1276
    _t1277 = parse_betree_info(parser)
    betree_info662 = _t1277
    consume_literal!(parser, ")")
    _t1278 = Proto.BeTreeRelation(name=relation_id661, relation_info=betree_info662)
    return _t1278
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1279 = parse_betree_info_key_types(parser)
    betree_info_key_types663 = _t1279
    _t1280 = parse_betree_info_value_types(parser)
    betree_info_value_types664 = _t1280
    _t1281 = parse_config_dict(parser)
    config_dict665 = _t1281
    consume_literal!(parser, ")")
    _t1282 = construct_betree_info(parser, betree_info_key_types663, betree_info_value_types664, config_dict665)
    return _t1282
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs666 = Proto.var"#Type"[]
    cond667 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond667
        _t1283 = parse_type(parser)
        item668 = _t1283
        push!(xs666, item668)
        cond667 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types669 = xs666
    consume_literal!(parser, ")")
    return types669
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs670 = Proto.var"#Type"[]
    cond671 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond671
        _t1284 = parse_type(parser)
        item672 = _t1284
        push!(xs670, item672)
        cond671 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types673 = xs670
    consume_literal!(parser, ")")
    return types673
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1285 = parse_csvlocator(parser)
    csvlocator674 = _t1285
    _t1286 = parse_csv_config(parser)
    csv_config675 = _t1286
    _t1287 = parse_gnf_columns(parser)
    gnf_columns676 = _t1287
    _t1288 = parse_csv_asof(parser)
    csv_asof677 = _t1288
    consume_literal!(parser, ")")
    _t1289 = Proto.CSVData(locator=csvlocator674, config=csv_config675, columns=gnf_columns676, asof=csv_asof677)
    return _t1289
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1291 = parse_csv_locator_paths(parser)
        _t1290 = _t1291
    else
        _t1290 = nothing
    end
    csv_locator_paths678 = _t1290
    if match_lookahead_literal(parser, "(", 0)
        _t1293 = parse_csv_locator_inline_data(parser)
        _t1292 = _t1293
    else
        _t1292 = nothing
    end
    csv_locator_inline_data679 = _t1292
    consume_literal!(parser, ")")
    _t1294 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths678) ? csv_locator_paths678 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data679) ? csv_locator_inline_data679 : "")))
    return _t1294
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs680 = String[]
    cond681 = match_lookahead_terminal(parser, "STRING", 0)
    while cond681
        item682 = consume_terminal!(parser, "STRING")
        push!(xs680, item682)
        cond681 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings683 = xs680
    consume_literal!(parser, ")")
    return strings683
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string684 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string684
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1295 = parse_config_dict(parser)
    config_dict685 = _t1295
    consume_literal!(parser, ")")
    _t1296 = construct_csv_config(parser, config_dict685)
    return _t1296
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs686 = Proto.GNFColumn[]
    cond687 = match_lookahead_literal(parser, "(", 0)
    while cond687
        _t1297 = parse_gnf_column(parser)
        item688 = _t1297
        push!(xs686, item688)
        cond687 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns689 = xs686
    consume_literal!(parser, ")")
    return gnf_columns689
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1298 = parse_gnf_column_path(parser)
    gnf_column_path690 = _t1298
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1300 = parse_relation_id(parser)
        _t1299 = _t1300
    else
        _t1299 = nothing
    end
    relation_id691 = _t1299
    consume_literal!(parser, "[")
    xs692 = Proto.var"#Type"[]
    cond693 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond693
        _t1301 = parse_type(parser)
        item694 = _t1301
        push!(xs692, item694)
        cond693 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types695 = xs692
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1302 = Proto.GNFColumn(column_path=gnf_column_path690, target_id=relation_id691, types=types695)
    return _t1302
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1303 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1304 = 0
        else
            _t1304 = -1
        end
        _t1303 = _t1304
    end
    prediction696 = _t1303
    if prediction696 == 1
        consume_literal!(parser, "[")
        xs698 = String[]
        cond699 = match_lookahead_terminal(parser, "STRING", 0)
        while cond699
            item700 = consume_terminal!(parser, "STRING")
            push!(xs698, item700)
            cond699 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings701 = xs698
        consume_literal!(parser, "]")
        _t1305 = strings701
    else
        if prediction696 == 0
            string697 = consume_terminal!(parser, "STRING")
            _t1306 = String[string697]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1305 = _t1306
    end
    return _t1305
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string702 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string702
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1307 = parse_fragment_id(parser)
    fragment_id703 = _t1307
    consume_literal!(parser, ")")
    _t1308 = Proto.Undefine(fragment_id=fragment_id703)
    return _t1308
end

function parse_context(parser::ParserState)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs704 = Proto.RelationId[]
    cond705 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond705
        _t1309 = parse_relation_id(parser)
        item706 = _t1309
        push!(xs704, item706)
        cond705 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids707 = xs704
    consume_literal!(parser, ")")
    _t1310 = Proto.Context(relations=relation_ids707)
    return _t1310
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs708 = Proto.SnapshotMapping[]
    cond709 = match_lookahead_literal(parser, "[", 0)
    while cond709
        _t1311 = parse_snapshot_mapping(parser)
        item710 = _t1311
        push!(xs708, item710)
        cond709 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings711 = xs708
    consume_literal!(parser, ")")
    _t1312 = Proto.Snapshot(mappings=snapshot_mappings711)
    return _t1312
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    _t1313 = parse_edb_path(parser)
    edb_path712 = _t1313
    _t1314 = parse_relation_id(parser)
    relation_id713 = _t1314
    _t1315 = Proto.SnapshotMapping(destination_path=edb_path712, source_relation=relation_id713)
    return _t1315
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs714 = Proto.Read[]
    cond715 = match_lookahead_literal(parser, "(", 0)
    while cond715
        _t1316 = parse_read(parser)
        item716 = _t1316
        push!(xs714, item716)
        cond715 = match_lookahead_literal(parser, "(", 0)
    end
    reads717 = xs714
    consume_literal!(parser, ")")
    return reads717
end

function parse_read(parser::ParserState)::Proto.Read
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1318 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1319 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1320 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1321 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1322 = 3
                        else
                            _t1322 = -1
                        end
                        _t1321 = _t1322
                    end
                    _t1320 = _t1321
                end
                _t1319 = _t1320
            end
            _t1318 = _t1319
        end
        _t1317 = _t1318
    else
        _t1317 = -1
    end
    prediction718 = _t1317
    if prediction718 == 4
        _t1324 = parse_export(parser)
        export723 = _t1324
        _t1325 = Proto.Read(read_type=OneOf(:var"#export", export723))
        _t1323 = _t1325
    else
        if prediction718 == 3
            _t1327 = parse_abort(parser)
            abort722 = _t1327
            _t1328 = Proto.Read(read_type=OneOf(:abort, abort722))
            _t1326 = _t1328
        else
            if prediction718 == 2
                _t1330 = parse_what_if(parser)
                what_if721 = _t1330
                _t1331 = Proto.Read(read_type=OneOf(:what_if, what_if721))
                _t1329 = _t1331
            else
                if prediction718 == 1
                    _t1333 = parse_output(parser)
                    output720 = _t1333
                    _t1334 = Proto.Read(read_type=OneOf(:output, output720))
                    _t1332 = _t1334
                else
                    if prediction718 == 0
                        _t1336 = parse_demand(parser)
                        demand719 = _t1336
                        _t1337 = Proto.Read(read_type=OneOf(:demand, demand719))
                        _t1335 = _t1337
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1332 = _t1335
                end
                _t1329 = _t1332
            end
            _t1326 = _t1329
        end
        _t1323 = _t1326
    end
    return _t1323
end

function parse_demand(parser::ParserState)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1338 = parse_relation_id(parser)
    relation_id724 = _t1338
    consume_literal!(parser, ")")
    _t1339 = Proto.Demand(relation_id=relation_id724)
    return _t1339
end

function parse_output(parser::ParserState)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1340 = parse_name(parser)
    name725 = _t1340
    _t1341 = parse_relation_id(parser)
    relation_id726 = _t1341
    consume_literal!(parser, ")")
    _t1342 = Proto.Output(name=name725, relation_id=relation_id726)
    return _t1342
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1343 = parse_name(parser)
    name727 = _t1343
    _t1344 = parse_epoch(parser)
    epoch728 = _t1344
    consume_literal!(parser, ")")
    _t1345 = Proto.WhatIf(branch=name727, epoch=epoch728)
    return _t1345
end

function parse_abort(parser::ParserState)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1347 = parse_name(parser)
        _t1346 = _t1347
    else
        _t1346 = nothing
    end
    name729 = _t1346
    _t1348 = parse_relation_id(parser)
    relation_id730 = _t1348
    consume_literal!(parser, ")")
    _t1349 = Proto.Abort(name=(!isnothing(name729) ? name729 : "abort"), relation_id=relation_id730)
    return _t1349
end

function parse_export(parser::ParserState)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1350 = parse_export_csv_config(parser)
    export_csv_config731 = _t1350
    consume_literal!(parser, ")")
    _t1351 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config731))
    return _t1351
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1353 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1354 = 1
            else
                _t1354 = -1
            end
            _t1353 = _t1354
        end
        _t1352 = _t1353
    else
        _t1352 = -1
    end
    prediction732 = _t1352
    if prediction732 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1356 = parse_export_csv_path(parser)
        export_csv_path736 = _t1356
        _t1357 = parse_export_csv_columns_list(parser)
        export_csv_columns_list737 = _t1357
        _t1358 = parse_config_dict(parser)
        config_dict738 = _t1358
        consume_literal!(parser, ")")
        _t1359 = construct_export_csv_config(parser, export_csv_path736, export_csv_columns_list737, config_dict738)
        _t1355 = _t1359
    else
        if prediction732 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1361 = parse_export_csv_path(parser)
            export_csv_path733 = _t1361
            _t1362 = parse_export_csv_source(parser)
            export_csv_source734 = _t1362
            _t1363 = parse_csv_config(parser)
            csv_config735 = _t1363
            consume_literal!(parser, ")")
            _t1364 = construct_export_csv_config_with_source(parser, export_csv_path733, export_csv_source734, csv_config735)
            _t1360 = _t1364
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1355 = _t1360
    end
    return _t1355
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string739 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string739
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1366 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1367 = 0
            else
                _t1367 = -1
            end
            _t1366 = _t1367
        end
        _t1365 = _t1366
    else
        _t1365 = -1
    end
    prediction740 = _t1365
    if prediction740 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1369 = parse_relation_id(parser)
        relation_id745 = _t1369
        consume_literal!(parser, ")")
        _t1370 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id745))
        _t1368 = _t1370
    else
        if prediction740 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs741 = Proto.ExportCSVColumn[]
            cond742 = match_lookahead_literal(parser, "(", 0)
            while cond742
                _t1372 = parse_export_csv_column(parser)
                item743 = _t1372
                push!(xs741, item743)
                cond742 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns744 = xs741
            consume_literal!(parser, ")")
            _t1373 = Proto.ExportCSVColumns(columns=export_csv_columns744)
            _t1374 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1373))
            _t1371 = _t1374
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1368 = _t1371
    end
    return _t1368
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string746 = consume_terminal!(parser, "STRING")
    _t1375 = parse_relation_id(parser)
    relation_id747 = _t1375
    consume_literal!(parser, ")")
    _t1376 = Proto.ExportCSVColumn(column_name=string746, column_data=relation_id747)
    return _t1376
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs748 = Proto.ExportCSVColumn[]
    cond749 = match_lookahead_literal(parser, "(", 0)
    while cond749
        _t1377 = parse_export_csv_column(parser)
        item750 = _t1377
        push!(xs748, item750)
        cond749 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns751 = xs748
    consume_literal!(parser, ")")
    return export_csv_columns751
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
