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
        _t1311 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1312 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1313 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1314 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1315 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1316 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1317 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1318 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1319 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1320 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1320
    _t1321 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1321
    _t1322 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1322
    _t1323 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1323
    _t1324 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1324
    _t1325 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1325
    _t1326 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1326
    _t1327 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1327
    _t1328 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1328
    _t1329 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1329
    _t1330 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1330
    _t1331 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1331
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1332 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1332
    _t1333 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1333
    _t1334 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1334
    _t1335 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1335
    _t1336 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1336
    _t1337 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1337
    _t1338 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1338
    _t1339 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1339
    _t1340 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1340
    _t1341 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1341
    _t1342 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1342
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1343 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1343
    _t1344 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1344
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
    _t1345 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1345
    _t1346 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1346
    _t1347 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1347
end

function export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1348 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1348
    _t1349 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1349
    _t1350 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1350
    _t1351 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1351
    _t1352 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1352
    _t1353 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1353
    _t1354 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1354
    _t1355 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1355
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t713 = parse_configure(parser)
        _t712 = _t713
    else
        _t712 = nothing
    end
    configure356 = _t712
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t715 = parse_sync(parser)
        _t714 = _t715
    else
        _t714 = nothing
    end
    sync357 = _t714
    xs358 = Proto.Epoch[]
    cond359 = match_lookahead_literal(parser, "(", 0)
    while cond359
        _t716 = parse_epoch(parser)
        item360 = _t716
        push!(xs358, item360)
        cond359 = match_lookahead_literal(parser, "(", 0)
    end
    epochs361 = xs358
    consume_literal!(parser, ")")
    _t717 = default_configure(parser)
    _t718 = Proto.Transaction(epochs=epochs361, configure=(!isnothing(configure356) ? configure356 : _t717), sync=sync357)
    return _t718
end

function parse_configure(parser::ParserState)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t719 = parse_config_dict(parser)
    config_dict362 = _t719
    consume_literal!(parser, ")")
    _t720 = construct_configure(parser, config_dict362)
    return _t720
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs363 = Tuple{String, Proto.Value}[]
    cond364 = match_lookahead_literal(parser, ":", 0)
    while cond364
        _t721 = parse_config_key_value(parser)
        item365 = _t721
        push!(xs363, item365)
        cond364 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values366 = xs363
    consume_literal!(parser, "}")
    return config_key_values366
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol367 = consume_terminal!(parser, "SYMBOL")
    _t722 = parse_value(parser)
    value368 = _t722
    return (symbol367, value368,)
end

function parse_value(parser::ParserState)::Proto.Value
    if match_lookahead_literal(parser, "true", 0)
        _t723 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t724 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t725 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t727 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t728 = 0
                        else
                            _t728 = -1
                        end
                        _t727 = _t728
                    end
                    _t726 = _t727
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t729 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t730 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t731 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t732 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t733 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t734 = 7
                                        else
                                            _t734 = -1
                                        end
                                        _t733 = _t734
                                    end
                                    _t732 = _t733
                                end
                                _t731 = _t732
                            end
                            _t730 = _t731
                        end
                        _t729 = _t730
                    end
                    _t726 = _t729
                end
                _t725 = _t726
            end
            _t724 = _t725
        end
        _t723 = _t724
    end
    prediction369 = _t723
    if prediction369 == 9
        _t736 = parse_boolean_value(parser)
        boolean_value378 = _t736
        _t737 = Proto.Value(value=OneOf(:boolean_value, boolean_value378))
        _t735 = _t737
    else
        if prediction369 == 8
            consume_literal!(parser, "missing")
            _t739 = Proto.MissingValue()
            _t740 = Proto.Value(value=OneOf(:missing_value, _t739))
            _t738 = _t740
        else
            if prediction369 == 7
                decimal377 = consume_terminal!(parser, "DECIMAL")
                _t742 = Proto.Value(value=OneOf(:decimal_value, decimal377))
                _t741 = _t742
            else
                if prediction369 == 6
                    int128376 = consume_terminal!(parser, "INT128")
                    _t744 = Proto.Value(value=OneOf(:int128_value, int128376))
                    _t743 = _t744
                else
                    if prediction369 == 5
                        uint128375 = consume_terminal!(parser, "UINT128")
                        _t746 = Proto.Value(value=OneOf(:uint128_value, uint128375))
                        _t745 = _t746
                    else
                        if prediction369 == 4
                            float374 = consume_terminal!(parser, "FLOAT")
                            _t748 = Proto.Value(value=OneOf(:float_value, float374))
                            _t747 = _t748
                        else
                            if prediction369 == 3
                                int373 = consume_terminal!(parser, "INT")
                                _t750 = Proto.Value(value=OneOf(:int_value, int373))
                                _t749 = _t750
                            else
                                if prediction369 == 2
                                    string372 = consume_terminal!(parser, "STRING")
                                    _t752 = Proto.Value(value=OneOf(:string_value, string372))
                                    _t751 = _t752
                                else
                                    if prediction369 == 1
                                        _t754 = parse_datetime(parser)
                                        datetime371 = _t754
                                        _t755 = Proto.Value(value=OneOf(:datetime_value, datetime371))
                                        _t753 = _t755
                                    else
                                        if prediction369 == 0
                                            _t757 = parse_date(parser)
                                            date370 = _t757
                                            _t758 = Proto.Value(value=OneOf(:date_value, date370))
                                            _t756 = _t758
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t753 = _t756
                                    end
                                    _t751 = _t753
                                end
                                _t749 = _t751
                            end
                            _t747 = _t749
                        end
                        _t745 = _t747
                    end
                    _t743 = _t745
                end
                _t741 = _t743
            end
            _t738 = _t741
        end
        _t735 = _t738
    end
    return _t735
end

function parse_date(parser::ParserState)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int379 = consume_terminal!(parser, "INT")
    int_3380 = consume_terminal!(parser, "INT")
    int_4381 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t759 = Proto.DateValue(year=Int32(int379), month=Int32(int_3380), day=Int32(int_4381))
    return _t759
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int382 = consume_terminal!(parser, "INT")
    int_3383 = consume_terminal!(parser, "INT")
    int_4384 = consume_terminal!(parser, "INT")
    int_5385 = consume_terminal!(parser, "INT")
    int_6386 = consume_terminal!(parser, "INT")
    int_7387 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t760 = consume_terminal!(parser, "INT")
    else
        _t760 = nothing
    end
    int_8388 = _t760
    consume_literal!(parser, ")")
    _t761 = Proto.DateTimeValue(year=Int32(int382), month=Int32(int_3383), day=Int32(int_4384), hour=Int32(int_5385), minute=Int32(int_6386), second=Int32(int_7387), microsecond=Int32((!isnothing(int_8388) ? int_8388 : 0)))
    return _t761
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t762 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t763 = 1
        else
            _t763 = -1
        end
        _t762 = _t763
    end
    prediction389 = _t762
    if prediction389 == 1
        consume_literal!(parser, "false")
        _t764 = false
    else
        if prediction389 == 0
            consume_literal!(parser, "true")
            _t765 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t764 = _t765
    end
    return _t764
end

function parse_sync(parser::ParserState)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs390 = Proto.FragmentId[]
    cond391 = match_lookahead_literal(parser, ":", 0)
    while cond391
        _t766 = parse_fragment_id(parser)
        item392 = _t766
        push!(xs390, item392)
        cond391 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids393 = xs390
    consume_literal!(parser, ")")
    _t767 = Proto.Sync(fragments=fragment_ids393)
    return _t767
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol394 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol394))
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t769 = parse_epoch_writes(parser)
        _t768 = _t769
    else
        _t768 = nothing
    end
    epoch_writes395 = _t768
    if match_lookahead_literal(parser, "(", 0)
        _t771 = parse_epoch_reads(parser)
        _t770 = _t771
    else
        _t770 = nothing
    end
    epoch_reads396 = _t770
    consume_literal!(parser, ")")
    _t772 = Proto.Epoch(writes=(!isnothing(epoch_writes395) ? epoch_writes395 : Proto.Write[]), reads=(!isnothing(epoch_reads396) ? epoch_reads396 : Proto.Read[]))
    return _t772
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs397 = Proto.Write[]
    cond398 = match_lookahead_literal(parser, "(", 0)
    while cond398
        _t773 = parse_write(parser)
        item399 = _t773
        push!(xs397, item399)
        cond398 = match_lookahead_literal(parser, "(", 0)
    end
    writes400 = xs397
    consume_literal!(parser, ")")
    return writes400
end

function parse_write(parser::ParserState)::Proto.Write
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t775 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t776 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t777 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t778 = 2
                    else
                        _t778 = -1
                    end
                    _t777 = _t778
                end
                _t776 = _t777
            end
            _t775 = _t776
        end
        _t774 = _t775
    else
        _t774 = -1
    end
    prediction401 = _t774
    if prediction401 == 3
        _t780 = parse_snapshot(parser)
        snapshot405 = _t780
        _t781 = Proto.Write(write_type=OneOf(:snapshot, snapshot405))
        _t779 = _t781
    else
        if prediction401 == 2
            _t783 = parse_context(parser)
            context404 = _t783
            _t784 = Proto.Write(write_type=OneOf(:context, context404))
            _t782 = _t784
        else
            if prediction401 == 1
                _t786 = parse_undefine(parser)
                undefine403 = _t786
                _t787 = Proto.Write(write_type=OneOf(:undefine, undefine403))
                _t785 = _t787
            else
                if prediction401 == 0
                    _t789 = parse_define(parser)
                    define402 = _t789
                    _t790 = Proto.Write(write_type=OneOf(:define, define402))
                    _t788 = _t790
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t785 = _t788
            end
            _t782 = _t785
        end
        _t779 = _t782
    end
    return _t779
end

function parse_define(parser::ParserState)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t791 = parse_fragment(parser)
    fragment406 = _t791
    consume_literal!(parser, ")")
    _t792 = Proto.Define(fragment=fragment406)
    return _t792
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t793 = parse_new_fragment_id(parser)
    new_fragment_id407 = _t793
    xs408 = Proto.Declaration[]
    cond409 = match_lookahead_literal(parser, "(", 0)
    while cond409
        _t794 = parse_declaration(parser)
        item410 = _t794
        push!(xs408, item410)
        cond409 = match_lookahead_literal(parser, "(", 0)
    end
    declarations411 = xs408
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id407, declarations411)
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    _t795 = parse_fragment_id(parser)
    fragment_id412 = _t795
    start_fragment!(parser, fragment_id412)
    return fragment_id412
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t797 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t798 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t799 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t800 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t801 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t802 = 1
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
            end
            _t797 = _t798
        end
        _t796 = _t797
    else
        _t796 = -1
    end
    prediction413 = _t796
    if prediction413 == 3
        _t804 = parse_data(parser)
        data417 = _t804
        _t805 = Proto.Declaration(declaration_type=OneOf(:data, data417))
        _t803 = _t805
    else
        if prediction413 == 2
            _t807 = parse_constraint(parser)
            constraint416 = _t807
            _t808 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint416))
            _t806 = _t808
        else
            if prediction413 == 1
                _t810 = parse_algorithm(parser)
                algorithm415 = _t810
                _t811 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm415))
                _t809 = _t811
            else
                if prediction413 == 0
                    _t813 = parse_def(parser)
                    def414 = _t813
                    _t814 = Proto.Declaration(declaration_type=OneOf(:def, def414))
                    _t812 = _t814
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t809 = _t812
            end
            _t806 = _t809
        end
        _t803 = _t806
    end
    return _t803
end

function parse_def(parser::ParserState)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t815 = parse_relation_id(parser)
    relation_id418 = _t815
    _t816 = parse_abstraction(parser)
    abstraction419 = _t816
    if match_lookahead_literal(parser, "(", 0)
        _t818 = parse_attrs(parser)
        _t817 = _t818
    else
        _t817 = nothing
    end
    attrs420 = _t817
    consume_literal!(parser, ")")
    _t819 = Proto.Def(name=relation_id418, body=abstraction419, attrs=(!isnothing(attrs420) ? attrs420 : Proto.Attribute[]))
    return _t819
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    if match_lookahead_literal(parser, ":", 0)
        _t820 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t821 = 1
        else
            _t821 = -1
        end
        _t820 = _t821
    end
    prediction421 = _t820
    if prediction421 == 1
        uint128423 = consume_terminal!(parser, "UINT128")
        _t822 = Proto.RelationId(uint128423.low, uint128423.high)
    else
        if prediction421 == 0
            consume_literal!(parser, ":")
            symbol422 = consume_terminal!(parser, "SYMBOL")
            _t823 = relation_id_from_string(parser, symbol422)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t822 = _t823
    end
    return _t822
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t824 = parse_bindings(parser)
    bindings424 = _t824
    _t825 = parse_formula(parser)
    formula425 = _t825
    consume_literal!(parser, ")")
    _t826 = Proto.Abstraction(vars=vcat(bindings424[1], !isnothing(bindings424[2]) ? bindings424[2] : []), value=formula425)
    return _t826
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs426 = Proto.Binding[]
    cond427 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond427
        _t827 = parse_binding(parser)
        item428 = _t827
        push!(xs426, item428)
        cond427 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings429 = xs426
    if match_lookahead_literal(parser, "|", 0)
        _t829 = parse_value_bindings(parser)
        _t828 = _t829
    else
        _t828 = nothing
    end
    value_bindings430 = _t828
    consume_literal!(parser, "]")
    return (bindings429, (!isnothing(value_bindings430) ? value_bindings430 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    symbol431 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t830 = parse_type(parser)
    type432 = _t830
    _t831 = Proto.Var(name=symbol431)
    _t832 = Proto.Binding(var=_t831, var"#type"=type432)
    return _t832
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t833 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t834 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t835 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t836 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t837 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t838 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t839 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t840 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t841 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t842 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t843 = 9
                                            else
                                                _t843 = -1
                                            end
                                            _t842 = _t843
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
                end
                _t835 = _t836
            end
            _t834 = _t835
        end
        _t833 = _t834
    end
    prediction433 = _t833
    if prediction433 == 10
        _t845 = parse_boolean_type(parser)
        boolean_type444 = _t845
        _t846 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type444))
        _t844 = _t846
    else
        if prediction433 == 9
            _t848 = parse_decimal_type(parser)
            decimal_type443 = _t848
            _t849 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type443))
            _t847 = _t849
        else
            if prediction433 == 8
                _t851 = parse_missing_type(parser)
                missing_type442 = _t851
                _t852 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type442))
                _t850 = _t852
            else
                if prediction433 == 7
                    _t854 = parse_datetime_type(parser)
                    datetime_type441 = _t854
                    _t855 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type441))
                    _t853 = _t855
                else
                    if prediction433 == 6
                        _t857 = parse_date_type(parser)
                        date_type440 = _t857
                        _t858 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type440))
                        _t856 = _t858
                    else
                        if prediction433 == 5
                            _t860 = parse_int128_type(parser)
                            int128_type439 = _t860
                            _t861 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type439))
                            _t859 = _t861
                        else
                            if prediction433 == 4
                                _t863 = parse_uint128_type(parser)
                                uint128_type438 = _t863
                                _t864 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type438))
                                _t862 = _t864
                            else
                                if prediction433 == 3
                                    _t866 = parse_float_type(parser)
                                    float_type437 = _t866
                                    _t867 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type437))
                                    _t865 = _t867
                                else
                                    if prediction433 == 2
                                        _t869 = parse_int_type(parser)
                                        int_type436 = _t869
                                        _t870 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type436))
                                        _t868 = _t870
                                    else
                                        if prediction433 == 1
                                            _t872 = parse_string_type(parser)
                                            string_type435 = _t872
                                            _t873 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type435))
                                            _t871 = _t873
                                        else
                                            if prediction433 == 0
                                                _t875 = parse_unspecified_type(parser)
                                                unspecified_type434 = _t875
                                                _t876 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type434))
                                                _t874 = _t876
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t871 = _t874
                                        end
                                        _t868 = _t871
                                    end
                                    _t865 = _t868
                                end
                                _t862 = _t865
                            end
                            _t859 = _t862
                        end
                        _t856 = _t859
                    end
                    _t853 = _t856
                end
                _t850 = _t853
            end
            _t847 = _t850
        end
        _t844 = _t847
    end
    return _t844
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t877 = Proto.UnspecifiedType()
    return _t877
end

function parse_string_type(parser::ParserState)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t878 = Proto.StringType()
    return _t878
end

function parse_int_type(parser::ParserState)::Proto.IntType
    consume_literal!(parser, "INT")
    _t879 = Proto.IntType()
    return _t879
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t880 = Proto.FloatType()
    return _t880
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t881 = Proto.UInt128Type()
    return _t881
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t882 = Proto.Int128Type()
    return _t882
end

function parse_date_type(parser::ParserState)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t883 = Proto.DateType()
    return _t883
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t884 = Proto.DateTimeType()
    return _t884
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t885 = Proto.MissingType()
    return _t885
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int445 = consume_terminal!(parser, "INT")
    int_3446 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t886 = Proto.DecimalType(precision=Int32(int445), scale=Int32(int_3446))
    return _t886
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t887 = Proto.BooleanType()
    return _t887
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs447 = Proto.Binding[]
    cond448 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond448
        _t888 = parse_binding(parser)
        item449 = _t888
        push!(xs447, item449)
        cond448 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings450 = xs447
    return bindings450
end

function parse_formula(parser::ParserState)::Proto.Formula
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t890 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t891 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t892 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t893 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t894 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t895 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t896 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t897 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t898 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t899 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t900 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t901 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t902 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t903 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t904 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t905 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t906 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t907 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t908 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t909 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t910 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t911 = 10
                                                                                            else
                                                                                                _t911 = -1
                                                                                            end
                                                                                            _t910 = _t911
                                                                                        end
                                                                                        _t909 = _t910
                                                                                    end
                                                                                    _t908 = _t909
                                                                                end
                                                                                _t907 = _t908
                                                                            end
                                                                            _t906 = _t907
                                                                        end
                                                                        _t905 = _t906
                                                                    end
                                                                    _t904 = _t905
                                                                end
                                                                _t903 = _t904
                                                            end
                                                            _t902 = _t903
                                                        end
                                                        _t901 = _t902
                                                    end
                                                    _t900 = _t901
                                                end
                                                _t899 = _t900
                                            end
                                            _t898 = _t899
                                        end
                                        _t897 = _t898
                                    end
                                    _t896 = _t897
                                end
                                _t895 = _t896
                            end
                            _t894 = _t895
                        end
                        _t893 = _t894
                    end
                    _t892 = _t893
                end
                _t891 = _t892
            end
            _t890 = _t891
        end
        _t889 = _t890
    else
        _t889 = -1
    end
    prediction451 = _t889
    if prediction451 == 12
        _t913 = parse_cast(parser)
        cast464 = _t913
        _t914 = Proto.Formula(formula_type=OneOf(:cast, cast464))
        _t912 = _t914
    else
        if prediction451 == 11
            _t916 = parse_rel_atom(parser)
            rel_atom463 = _t916
            _t917 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom463))
            _t915 = _t917
        else
            if prediction451 == 10
                _t919 = parse_primitive(parser)
                primitive462 = _t919
                _t920 = Proto.Formula(formula_type=OneOf(:primitive, primitive462))
                _t918 = _t920
            else
                if prediction451 == 9
                    _t922 = parse_pragma(parser)
                    pragma461 = _t922
                    _t923 = Proto.Formula(formula_type=OneOf(:pragma, pragma461))
                    _t921 = _t923
                else
                    if prediction451 == 8
                        _t925 = parse_atom(parser)
                        atom460 = _t925
                        _t926 = Proto.Formula(formula_type=OneOf(:atom, atom460))
                        _t924 = _t926
                    else
                        if prediction451 == 7
                            _t928 = parse_ffi(parser)
                            ffi459 = _t928
                            _t929 = Proto.Formula(formula_type=OneOf(:ffi, ffi459))
                            _t927 = _t929
                        else
                            if prediction451 == 6
                                _t931 = parse_not(parser)
                                not458 = _t931
                                _t932 = Proto.Formula(formula_type=OneOf(:not, not458))
                                _t930 = _t932
                            else
                                if prediction451 == 5
                                    _t934 = parse_disjunction(parser)
                                    disjunction457 = _t934
                                    _t935 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction457))
                                    _t933 = _t935
                                else
                                    if prediction451 == 4
                                        _t937 = parse_conjunction(parser)
                                        conjunction456 = _t937
                                        _t938 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction456))
                                        _t936 = _t938
                                    else
                                        if prediction451 == 3
                                            _t940 = parse_reduce(parser)
                                            reduce455 = _t940
                                            _t941 = Proto.Formula(formula_type=OneOf(:reduce, reduce455))
                                            _t939 = _t941
                                        else
                                            if prediction451 == 2
                                                _t943 = parse_exists(parser)
                                                exists454 = _t943
                                                _t944 = Proto.Formula(formula_type=OneOf(:exists, exists454))
                                                _t942 = _t944
                                            else
                                                if prediction451 == 1
                                                    _t946 = parse_false(parser)
                                                    false453 = _t946
                                                    _t947 = Proto.Formula(formula_type=OneOf(:disjunction, false453))
                                                    _t945 = _t947
                                                else
                                                    if prediction451 == 0
                                                        _t949 = parse_true(parser)
                                                        true452 = _t949
                                                        _t950 = Proto.Formula(formula_type=OneOf(:conjunction, true452))
                                                        _t948 = _t950
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t945 = _t948
                                                end
                                                _t942 = _t945
                                            end
                                            _t939 = _t942
                                        end
                                        _t936 = _t939
                                    end
                                    _t933 = _t936
                                end
                                _t930 = _t933
                            end
                            _t927 = _t930
                        end
                        _t924 = _t927
                    end
                    _t921 = _t924
                end
                _t918 = _t921
            end
            _t915 = _t918
        end
        _t912 = _t915
    end
    return _t912
end

function parse_true(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t951 = Proto.Conjunction(args=Proto.Formula[])
    return _t951
end

function parse_false(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t952 = Proto.Disjunction(args=Proto.Formula[])
    return _t952
end

function parse_exists(parser::ParserState)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t953 = parse_bindings(parser)
    bindings465 = _t953
    _t954 = parse_formula(parser)
    formula466 = _t954
    consume_literal!(parser, ")")
    _t955 = Proto.Abstraction(vars=vcat(bindings465[1], !isnothing(bindings465[2]) ? bindings465[2] : []), value=formula466)
    _t956 = Proto.Exists(body=_t955)
    return _t956
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t957 = parse_abstraction(parser)
    abstraction467 = _t957
    _t958 = parse_abstraction(parser)
    abstraction_3468 = _t958
    _t959 = parse_terms(parser)
    terms469 = _t959
    consume_literal!(parser, ")")
    _t960 = Proto.Reduce(op=abstraction467, body=abstraction_3468, terms=terms469)
    return _t960
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs470 = Proto.Term[]
    cond471 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond471
        _t961 = parse_term(parser)
        item472 = _t961
        push!(xs470, item472)
        cond471 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms473 = xs470
    consume_literal!(parser, ")")
    return terms473
end

function parse_term(parser::ParserState)::Proto.Term
    if match_lookahead_literal(parser, "true", 0)
        _t962 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t963 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t964 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t965 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t966 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t967 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t968 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t969 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t970 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t971 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t972 = 1
                                            else
                                                _t972 = -1
                                            end
                                            _t971 = _t972
                                        end
                                        _t970 = _t971
                                    end
                                    _t969 = _t970
                                end
                                _t968 = _t969
                            end
                            _t967 = _t968
                        end
                        _t966 = _t967
                    end
                    _t965 = _t966
                end
                _t964 = _t965
            end
            _t963 = _t964
        end
        _t962 = _t963
    end
    prediction474 = _t962
    if prediction474 == 1
        _t974 = parse_constant(parser)
        constant476 = _t974
        _t975 = Proto.Term(term_type=OneOf(:constant, constant476))
        _t973 = _t975
    else
        if prediction474 == 0
            _t977 = parse_var(parser)
            var475 = _t977
            _t978 = Proto.Term(term_type=OneOf(:var, var475))
            _t976 = _t978
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t973 = _t976
    end
    return _t973
end

function parse_var(parser::ParserState)::Proto.Var
    symbol477 = consume_terminal!(parser, "SYMBOL")
    _t979 = Proto.Var(name=symbol477)
    return _t979
end

function parse_constant(parser::ParserState)::Proto.Value
    _t980 = parse_value(parser)
    value478 = _t980
    return value478
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs479 = Proto.Formula[]
    cond480 = match_lookahead_literal(parser, "(", 0)
    while cond480
        _t981 = parse_formula(parser)
        item481 = _t981
        push!(xs479, item481)
        cond480 = match_lookahead_literal(parser, "(", 0)
    end
    formulas482 = xs479
    consume_literal!(parser, ")")
    _t982 = Proto.Conjunction(args=formulas482)
    return _t982
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs483 = Proto.Formula[]
    cond484 = match_lookahead_literal(parser, "(", 0)
    while cond484
        _t983 = parse_formula(parser)
        item485 = _t983
        push!(xs483, item485)
        cond484 = match_lookahead_literal(parser, "(", 0)
    end
    formulas486 = xs483
    consume_literal!(parser, ")")
    _t984 = Proto.Disjunction(args=formulas486)
    return _t984
end

function parse_not(parser::ParserState)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t985 = parse_formula(parser)
    formula487 = _t985
    consume_literal!(parser, ")")
    _t986 = Proto.Not(arg=formula487)
    return _t986
end

function parse_ffi(parser::ParserState)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t987 = parse_name(parser)
    name488 = _t987
    _t988 = parse_ffi_args(parser)
    ffi_args489 = _t988
    _t989 = parse_terms(parser)
    terms490 = _t989
    consume_literal!(parser, ")")
    _t990 = Proto.FFI(name=name488, args=ffi_args489, terms=terms490)
    return _t990
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol491 = consume_terminal!(parser, "SYMBOL")
    return symbol491
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs492 = Proto.Abstraction[]
    cond493 = match_lookahead_literal(parser, "(", 0)
    while cond493
        _t991 = parse_abstraction(parser)
        item494 = _t991
        push!(xs492, item494)
        cond493 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions495 = xs492
    consume_literal!(parser, ")")
    return abstractions495
end

function parse_atom(parser::ParserState)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t992 = parse_relation_id(parser)
    relation_id496 = _t992
    xs497 = Proto.Term[]
    cond498 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond498
        _t993 = parse_term(parser)
        item499 = _t993
        push!(xs497, item499)
        cond498 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms500 = xs497
    consume_literal!(parser, ")")
    _t994 = Proto.Atom(name=relation_id496, terms=terms500)
    return _t994
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t995 = parse_name(parser)
    name501 = _t995
    xs502 = Proto.Term[]
    cond503 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond503
        _t996 = parse_term(parser)
        item504 = _t996
        push!(xs502, item504)
        cond503 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms505 = xs502
    consume_literal!(parser, ")")
    _t997 = Proto.Pragma(name=name501, terms=terms505)
    return _t997
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t999 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1000 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1001 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1002 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1003 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1004 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1005 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1006 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1007 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1008 = 7
                                            else
                                                _t1008 = -1
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
                    _t1001 = _t1002
                end
                _t1000 = _t1001
            end
            _t999 = _t1000
        end
        _t998 = _t999
    else
        _t998 = -1
    end
    prediction506 = _t998
    if prediction506 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1010 = parse_name(parser)
        name516 = _t1010
        xs517 = Proto.RelTerm[]
        cond518 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond518
            _t1011 = parse_rel_term(parser)
            item519 = _t1011
            push!(xs517, item519)
            cond518 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms520 = xs517
        consume_literal!(parser, ")")
        _t1012 = Proto.Primitive(name=name516, terms=rel_terms520)
        _t1009 = _t1012
    else
        if prediction506 == 8
            _t1014 = parse_divide(parser)
            divide515 = _t1014
            _t1013 = divide515
        else
            if prediction506 == 7
                _t1016 = parse_multiply(parser)
                multiply514 = _t1016
                _t1015 = multiply514
            else
                if prediction506 == 6
                    _t1018 = parse_minus(parser)
                    minus513 = _t1018
                    _t1017 = minus513
                else
                    if prediction506 == 5
                        _t1020 = parse_add(parser)
                        add512 = _t1020
                        _t1019 = add512
                    else
                        if prediction506 == 4
                            _t1022 = parse_gt_eq(parser)
                            gt_eq511 = _t1022
                            _t1021 = gt_eq511
                        else
                            if prediction506 == 3
                                _t1024 = parse_gt(parser)
                                gt510 = _t1024
                                _t1023 = gt510
                            else
                                if prediction506 == 2
                                    _t1026 = parse_lt_eq(parser)
                                    lt_eq509 = _t1026
                                    _t1025 = lt_eq509
                                else
                                    if prediction506 == 1
                                        _t1028 = parse_lt(parser)
                                        lt508 = _t1028
                                        _t1027 = lt508
                                    else
                                        if prediction506 == 0
                                            _t1030 = parse_eq(parser)
                                            eq507 = _t1030
                                            _t1029 = eq507
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1027 = _t1029
                                    end
                                    _t1025 = _t1027
                                end
                                _t1023 = _t1025
                            end
                            _t1021 = _t1023
                        end
                        _t1019 = _t1021
                    end
                    _t1017 = _t1019
                end
                _t1015 = _t1017
            end
            _t1013 = _t1015
        end
        _t1009 = _t1013
    end
    return _t1009
end

function parse_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1031 = parse_term(parser)
    term521 = _t1031
    _t1032 = parse_term(parser)
    term_3522 = _t1032
    consume_literal!(parser, ")")
    _t1033 = Proto.RelTerm(rel_term_type=OneOf(:term, term521))
    _t1034 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3522))
    _t1035 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1033, _t1034])
    return _t1035
end

function parse_lt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1036 = parse_term(parser)
    term523 = _t1036
    _t1037 = parse_term(parser)
    term_3524 = _t1037
    consume_literal!(parser, ")")
    _t1038 = Proto.RelTerm(rel_term_type=OneOf(:term, term523))
    _t1039 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3524))
    _t1040 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1038, _t1039])
    return _t1040
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1041 = parse_term(parser)
    term525 = _t1041
    _t1042 = parse_term(parser)
    term_3526 = _t1042
    consume_literal!(parser, ")")
    _t1043 = Proto.RelTerm(rel_term_type=OneOf(:term, term525))
    _t1044 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3526))
    _t1045 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1043, _t1044])
    return _t1045
end

function parse_gt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1046 = parse_term(parser)
    term527 = _t1046
    _t1047 = parse_term(parser)
    term_3528 = _t1047
    consume_literal!(parser, ")")
    _t1048 = Proto.RelTerm(rel_term_type=OneOf(:term, term527))
    _t1049 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3528))
    _t1050 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1048, _t1049])
    return _t1050
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1051 = parse_term(parser)
    term529 = _t1051
    _t1052 = parse_term(parser)
    term_3530 = _t1052
    consume_literal!(parser, ")")
    _t1053 = Proto.RelTerm(rel_term_type=OneOf(:term, term529))
    _t1054 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3530))
    _t1055 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1053, _t1054])
    return _t1055
end

function parse_add(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1056 = parse_term(parser)
    term531 = _t1056
    _t1057 = parse_term(parser)
    term_3532 = _t1057
    _t1058 = parse_term(parser)
    term_4533 = _t1058
    consume_literal!(parser, ")")
    _t1059 = Proto.RelTerm(rel_term_type=OneOf(:term, term531))
    _t1060 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3532))
    _t1061 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4533))
    _t1062 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1059, _t1060, _t1061])
    return _t1062
end

function parse_minus(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1063 = parse_term(parser)
    term534 = _t1063
    _t1064 = parse_term(parser)
    term_3535 = _t1064
    _t1065 = parse_term(parser)
    term_4536 = _t1065
    consume_literal!(parser, ")")
    _t1066 = Proto.RelTerm(rel_term_type=OneOf(:term, term534))
    _t1067 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3535))
    _t1068 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4536))
    _t1069 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1066, _t1067, _t1068])
    return _t1069
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1070 = parse_term(parser)
    term537 = _t1070
    _t1071 = parse_term(parser)
    term_3538 = _t1071
    _t1072 = parse_term(parser)
    term_4539 = _t1072
    consume_literal!(parser, ")")
    _t1073 = Proto.RelTerm(rel_term_type=OneOf(:term, term537))
    _t1074 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3538))
    _t1075 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4539))
    _t1076 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1073, _t1074, _t1075])
    return _t1076
end

function parse_divide(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1077 = parse_term(parser)
    term540 = _t1077
    _t1078 = parse_term(parser)
    term_3541 = _t1078
    _t1079 = parse_term(parser)
    term_4542 = _t1079
    consume_literal!(parser, ")")
    _t1080 = Proto.RelTerm(rel_term_type=OneOf(:term, term540))
    _t1081 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3541))
    _t1082 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4542))
    _t1083 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1080, _t1081, _t1082])
    return _t1083
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    if match_lookahead_literal(parser, "true", 0)
        _t1084 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1085 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1086 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1087 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1088 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1089 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1090 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1091 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1092 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1093 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1094 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1095 = 1
                                                else
                                                    _t1095 = -1
                                                end
                                                _t1094 = _t1095
                                            end
                                            _t1093 = _t1094
                                        end
                                        _t1092 = _t1093
                                    end
                                    _t1091 = _t1092
                                end
                                _t1090 = _t1091
                            end
                            _t1089 = _t1090
                        end
                        _t1088 = _t1089
                    end
                    _t1087 = _t1088
                end
                _t1086 = _t1087
            end
            _t1085 = _t1086
        end
        _t1084 = _t1085
    end
    prediction543 = _t1084
    if prediction543 == 1
        _t1097 = parse_term(parser)
        term545 = _t1097
        _t1098 = Proto.RelTerm(rel_term_type=OneOf(:term, term545))
        _t1096 = _t1098
    else
        if prediction543 == 0
            _t1100 = parse_specialized_value(parser)
            specialized_value544 = _t1100
            _t1101 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value544))
            _t1099 = _t1101
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1096 = _t1099
    end
    return _t1096
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    consume_literal!(parser, "#")
    _t1102 = parse_value(parser)
    value546 = _t1102
    return value546
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1103 = parse_name(parser)
    name547 = _t1103
    xs548 = Proto.RelTerm[]
    cond549 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond549
        _t1104 = parse_rel_term(parser)
        item550 = _t1104
        push!(xs548, item550)
        cond549 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms551 = xs548
    consume_literal!(parser, ")")
    _t1105 = Proto.RelAtom(name=name547, terms=rel_terms551)
    return _t1105
end

function parse_cast(parser::ParserState)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1106 = parse_term(parser)
    term552 = _t1106
    _t1107 = parse_term(parser)
    term_3553 = _t1107
    consume_literal!(parser, ")")
    _t1108 = Proto.Cast(input=term552, result=term_3553)
    return _t1108
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs554 = Proto.Attribute[]
    cond555 = match_lookahead_literal(parser, "(", 0)
    while cond555
        _t1109 = parse_attribute(parser)
        item556 = _t1109
        push!(xs554, item556)
        cond555 = match_lookahead_literal(parser, "(", 0)
    end
    attributes557 = xs554
    consume_literal!(parser, ")")
    return attributes557
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1110 = parse_name(parser)
    name558 = _t1110
    xs559 = Proto.Value[]
    cond560 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond560
        _t1111 = parse_value(parser)
        item561 = _t1111
        push!(xs559, item561)
        cond560 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values562 = xs559
    consume_literal!(parser, ")")
    _t1112 = Proto.Attribute(name=name558, args=values562)
    return _t1112
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs563 = Proto.RelationId[]
    cond564 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond564
        _t1113 = parse_relation_id(parser)
        item565 = _t1113
        push!(xs563, item565)
        cond564 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids566 = xs563
    _t1114 = parse_script(parser)
    script567 = _t1114
    consume_literal!(parser, ")")
    _t1115 = Proto.Algorithm(var"#global"=relation_ids566, body=script567)
    return _t1115
end

function parse_script(parser::ParserState)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs568 = Proto.Construct[]
    cond569 = match_lookahead_literal(parser, "(", 0)
    while cond569
        _t1116 = parse_construct(parser)
        item570 = _t1116
        push!(xs568, item570)
        cond569 = match_lookahead_literal(parser, "(", 0)
    end
    constructs571 = xs568
    consume_literal!(parser, ")")
    _t1117 = Proto.Script(constructs=constructs571)
    return _t1117
end

function parse_construct(parser::ParserState)::Proto.Construct
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1119 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1120 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1121 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1122 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1123 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1124 = 1
                            else
                                _t1124 = -1
                            end
                            _t1123 = _t1124
                        end
                        _t1122 = _t1123
                    end
                    _t1121 = _t1122
                end
                _t1120 = _t1121
            end
            _t1119 = _t1120
        end
        _t1118 = _t1119
    else
        _t1118 = -1
    end
    prediction572 = _t1118
    if prediction572 == 1
        _t1126 = parse_instruction(parser)
        instruction574 = _t1126
        _t1127 = Proto.Construct(construct_type=OneOf(:instruction, instruction574))
        _t1125 = _t1127
    else
        if prediction572 == 0
            _t1129 = parse_loop(parser)
            loop573 = _t1129
            _t1130 = Proto.Construct(construct_type=OneOf(:loop, loop573))
            _t1128 = _t1130
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1125 = _t1128
    end
    return _t1125
end

function parse_loop(parser::ParserState)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1131 = parse_init(parser)
    init575 = _t1131
    _t1132 = parse_script(parser)
    script576 = _t1132
    consume_literal!(parser, ")")
    _t1133 = Proto.Loop(init=init575, body=script576)
    return _t1133
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs577 = Proto.Instruction[]
    cond578 = match_lookahead_literal(parser, "(", 0)
    while cond578
        _t1134 = parse_instruction(parser)
        item579 = _t1134
        push!(xs577, item579)
        cond578 = match_lookahead_literal(parser, "(", 0)
    end
    instructions580 = xs577
    consume_literal!(parser, ")")
    return instructions580
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1136 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1137 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1138 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1139 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1140 = 0
                        else
                            _t1140 = -1
                        end
                        _t1139 = _t1140
                    end
                    _t1138 = _t1139
                end
                _t1137 = _t1138
            end
            _t1136 = _t1137
        end
        _t1135 = _t1136
    else
        _t1135 = -1
    end
    prediction581 = _t1135
    if prediction581 == 4
        _t1142 = parse_monus_def(parser)
        monus_def586 = _t1142
        _t1143 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def586))
        _t1141 = _t1143
    else
        if prediction581 == 3
            _t1145 = parse_monoid_def(parser)
            monoid_def585 = _t1145
            _t1146 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def585))
            _t1144 = _t1146
        else
            if prediction581 == 2
                _t1148 = parse_break(parser)
                break584 = _t1148
                _t1149 = Proto.Instruction(instr_type=OneOf(:var"#break", break584))
                _t1147 = _t1149
            else
                if prediction581 == 1
                    _t1151 = parse_upsert(parser)
                    upsert583 = _t1151
                    _t1152 = Proto.Instruction(instr_type=OneOf(:upsert, upsert583))
                    _t1150 = _t1152
                else
                    if prediction581 == 0
                        _t1154 = parse_assign(parser)
                        assign582 = _t1154
                        _t1155 = Proto.Instruction(instr_type=OneOf(:assign, assign582))
                        _t1153 = _t1155
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1150 = _t1153
                end
                _t1147 = _t1150
            end
            _t1144 = _t1147
        end
        _t1141 = _t1144
    end
    return _t1141
end

function parse_assign(parser::ParserState)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1156 = parse_relation_id(parser)
    relation_id587 = _t1156
    _t1157 = parse_abstraction(parser)
    abstraction588 = _t1157
    if match_lookahead_literal(parser, "(", 0)
        _t1159 = parse_attrs(parser)
        _t1158 = _t1159
    else
        _t1158 = nothing
    end
    attrs589 = _t1158
    consume_literal!(parser, ")")
    _t1160 = Proto.Assign(name=relation_id587, body=abstraction588, attrs=(!isnothing(attrs589) ? attrs589 : Proto.Attribute[]))
    return _t1160
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1161 = parse_relation_id(parser)
    relation_id590 = _t1161
    _t1162 = parse_abstraction_with_arity(parser)
    abstraction_with_arity591 = _t1162
    if match_lookahead_literal(parser, "(", 0)
        _t1164 = parse_attrs(parser)
        _t1163 = _t1164
    else
        _t1163 = nothing
    end
    attrs592 = _t1163
    consume_literal!(parser, ")")
    _t1165 = Proto.Upsert(name=relation_id590, body=abstraction_with_arity591[1], attrs=(!isnothing(attrs592) ? attrs592 : Proto.Attribute[]), value_arity=abstraction_with_arity591[2])
    return _t1165
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1166 = parse_bindings(parser)
    bindings593 = _t1166
    _t1167 = parse_formula(parser)
    formula594 = _t1167
    consume_literal!(parser, ")")
    _t1168 = Proto.Abstraction(vars=vcat(bindings593[1], !isnothing(bindings593[2]) ? bindings593[2] : []), value=formula594)
    return (_t1168, length(bindings593[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1169 = parse_relation_id(parser)
    relation_id595 = _t1169
    _t1170 = parse_abstraction(parser)
    abstraction596 = _t1170
    if match_lookahead_literal(parser, "(", 0)
        _t1172 = parse_attrs(parser)
        _t1171 = _t1172
    else
        _t1171 = nothing
    end
    attrs597 = _t1171
    consume_literal!(parser, ")")
    _t1173 = Proto.Break(name=relation_id595, body=abstraction596, attrs=(!isnothing(attrs597) ? attrs597 : Proto.Attribute[]))
    return _t1173
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1174 = parse_monoid(parser)
    monoid598 = _t1174
    _t1175 = parse_relation_id(parser)
    relation_id599 = _t1175
    _t1176 = parse_abstraction_with_arity(parser)
    abstraction_with_arity600 = _t1176
    if match_lookahead_literal(parser, "(", 0)
        _t1178 = parse_attrs(parser)
        _t1177 = _t1178
    else
        _t1177 = nothing
    end
    attrs601 = _t1177
    consume_literal!(parser, ")")
    _t1179 = Proto.MonoidDef(monoid=monoid598, name=relation_id599, body=abstraction_with_arity600[1], attrs=(!isnothing(attrs601) ? attrs601 : Proto.Attribute[]), value_arity=abstraction_with_arity600[2])
    return _t1179
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1181 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1182 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1183 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1184 = 2
                    else
                        _t1184 = -1
                    end
                    _t1183 = _t1184
                end
                _t1182 = _t1183
            end
            _t1181 = _t1182
        end
        _t1180 = _t1181
    else
        _t1180 = -1
    end
    prediction602 = _t1180
    if prediction602 == 3
        _t1186 = parse_sum_monoid(parser)
        sum_monoid606 = _t1186
        _t1187 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid606))
        _t1185 = _t1187
    else
        if prediction602 == 2
            _t1189 = parse_max_monoid(parser)
            max_monoid605 = _t1189
            _t1190 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid605))
            _t1188 = _t1190
        else
            if prediction602 == 1
                _t1192 = parse_min_monoid(parser)
                min_monoid604 = _t1192
                _t1193 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid604))
                _t1191 = _t1193
            else
                if prediction602 == 0
                    _t1195 = parse_or_monoid(parser)
                    or_monoid603 = _t1195
                    _t1196 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid603))
                    _t1194 = _t1196
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1191 = _t1194
            end
            _t1188 = _t1191
        end
        _t1185 = _t1188
    end
    return _t1185
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1197 = Proto.OrMonoid()
    return _t1197
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1198 = parse_type(parser)
    type607 = _t1198
    consume_literal!(parser, ")")
    _t1199 = Proto.MinMonoid(var"#type"=type607)
    return _t1199
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1200 = parse_type(parser)
    type608 = _t1200
    consume_literal!(parser, ")")
    _t1201 = Proto.MaxMonoid(var"#type"=type608)
    return _t1201
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1202 = parse_type(parser)
    type609 = _t1202
    consume_literal!(parser, ")")
    _t1203 = Proto.SumMonoid(var"#type"=type609)
    return _t1203
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1204 = parse_monoid(parser)
    monoid610 = _t1204
    _t1205 = parse_relation_id(parser)
    relation_id611 = _t1205
    _t1206 = parse_abstraction_with_arity(parser)
    abstraction_with_arity612 = _t1206
    if match_lookahead_literal(parser, "(", 0)
        _t1208 = parse_attrs(parser)
        _t1207 = _t1208
    else
        _t1207 = nothing
    end
    attrs613 = _t1207
    consume_literal!(parser, ")")
    _t1209 = Proto.MonusDef(monoid=monoid610, name=relation_id611, body=abstraction_with_arity612[1], attrs=(!isnothing(attrs613) ? attrs613 : Proto.Attribute[]), value_arity=abstraction_with_arity612[2])
    return _t1209
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1210 = parse_relation_id(parser)
    relation_id614 = _t1210
    _t1211 = parse_abstraction(parser)
    abstraction615 = _t1211
    _t1212 = parse_functional_dependency_keys(parser)
    functional_dependency_keys616 = _t1212
    _t1213 = parse_functional_dependency_values(parser)
    functional_dependency_values617 = _t1213
    consume_literal!(parser, ")")
    _t1214 = Proto.FunctionalDependency(guard=abstraction615, keys=functional_dependency_keys616, values=functional_dependency_values617)
    _t1215 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1214), name=relation_id614)
    return _t1215
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs618 = Proto.Var[]
    cond619 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond619
        _t1216 = parse_var(parser)
        item620 = _t1216
        push!(xs618, item620)
        cond619 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars621 = xs618
    consume_literal!(parser, ")")
    return vars621
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs622 = Proto.Var[]
    cond623 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond623
        _t1217 = parse_var(parser)
        item624 = _t1217
        push!(xs622, item624)
        cond623 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars625 = xs622
    consume_literal!(parser, ")")
    return vars625
end

function parse_data(parser::ParserState)::Proto.Data
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1219 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1220 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1221 = 1
                else
                    _t1221 = -1
                end
                _t1220 = _t1221
            end
            _t1219 = _t1220
        end
        _t1218 = _t1219
    else
        _t1218 = -1
    end
    prediction626 = _t1218
    if prediction626 == 2
        _t1223 = parse_csv_data(parser)
        csv_data629 = _t1223
        _t1224 = Proto.Data(data_type=OneOf(:csv_data, csv_data629))
        _t1222 = _t1224
    else
        if prediction626 == 1
            _t1226 = parse_betree_relation(parser)
            betree_relation628 = _t1226
            _t1227 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation628))
            _t1225 = _t1227
        else
            if prediction626 == 0
                _t1229 = parse_rel_edb(parser)
                rel_edb627 = _t1229
                _t1230 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb627))
                _t1228 = _t1230
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1225 = _t1228
        end
        _t1222 = _t1225
    end
    return _t1222
end

function parse_rel_edb(parser::ParserState)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t1231 = parse_relation_id(parser)
    relation_id630 = _t1231
    _t1232 = parse_rel_edb_path(parser)
    rel_edb_path631 = _t1232
    _t1233 = parse_rel_edb_types(parser)
    rel_edb_types632 = _t1233
    consume_literal!(parser, ")")
    _t1234 = Proto.RelEDB(target_id=relation_id630, path=rel_edb_path631, types=rel_edb_types632)
    return _t1234
end

function parse_rel_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs633 = String[]
    cond634 = match_lookahead_terminal(parser, "STRING", 0)
    while cond634
        item635 = consume_terminal!(parser, "STRING")
        push!(xs633, item635)
        cond634 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings636 = xs633
    consume_literal!(parser, "]")
    return strings636
end

function parse_rel_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs637 = Proto.var"#Type"[]
    cond638 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond638
        _t1235 = parse_type(parser)
        item639 = _t1235
        push!(xs637, item639)
        cond638 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types640 = xs637
    consume_literal!(parser, "]")
    return types640
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1236 = parse_relation_id(parser)
    relation_id641 = _t1236
    _t1237 = parse_betree_info(parser)
    betree_info642 = _t1237
    consume_literal!(parser, ")")
    _t1238 = Proto.BeTreeRelation(name=relation_id641, relation_info=betree_info642)
    return _t1238
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1239 = parse_betree_info_key_types(parser)
    betree_info_key_types643 = _t1239
    _t1240 = parse_betree_info_value_types(parser)
    betree_info_value_types644 = _t1240
    _t1241 = parse_config_dict(parser)
    config_dict645 = _t1241
    consume_literal!(parser, ")")
    _t1242 = construct_betree_info(parser, betree_info_key_types643, betree_info_value_types644, config_dict645)
    return _t1242
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs646 = Proto.var"#Type"[]
    cond647 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond647
        _t1243 = parse_type(parser)
        item648 = _t1243
        push!(xs646, item648)
        cond647 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types649 = xs646
    consume_literal!(parser, ")")
    return types649
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs650 = Proto.var"#Type"[]
    cond651 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond651
        _t1244 = parse_type(parser)
        item652 = _t1244
        push!(xs650, item652)
        cond651 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types653 = xs650
    consume_literal!(parser, ")")
    return types653
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1245 = parse_csvlocator(parser)
    csvlocator654 = _t1245
    _t1246 = parse_csv_config(parser)
    csv_config655 = _t1246
    _t1247 = parse_csv_columns(parser)
    csv_columns656 = _t1247
    _t1248 = parse_csv_asof(parser)
    csv_asof657 = _t1248
    consume_literal!(parser, ")")
    _t1249 = Proto.CSVData(locator=csvlocator654, config=csv_config655, columns=csv_columns656, asof=csv_asof657)
    return _t1249
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1251 = parse_csv_locator_paths(parser)
        _t1250 = _t1251
    else
        _t1250 = nothing
    end
    csv_locator_paths658 = _t1250
    if match_lookahead_literal(parser, "(", 0)
        _t1253 = parse_csv_locator_inline_data(parser)
        _t1252 = _t1253
    else
        _t1252 = nothing
    end
    csv_locator_inline_data659 = _t1252
    consume_literal!(parser, ")")
    _t1254 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths658) ? csv_locator_paths658 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data659) ? csv_locator_inline_data659 : "")))
    return _t1254
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs660 = String[]
    cond661 = match_lookahead_terminal(parser, "STRING", 0)
    while cond661
        item662 = consume_terminal!(parser, "STRING")
        push!(xs660, item662)
        cond661 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings663 = xs660
    consume_literal!(parser, ")")
    return strings663
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string664 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string664
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1255 = parse_config_dict(parser)
    config_dict665 = _t1255
    consume_literal!(parser, ")")
    _t1256 = construct_csv_config(parser, config_dict665)
    return _t1256
end

function parse_csv_columns(parser::ParserState)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs666 = Proto.CSVColumn[]
    cond667 = match_lookahead_literal(parser, "(", 0)
    while cond667
        _t1257 = parse_csv_column(parser)
        item668 = _t1257
        push!(xs666, item668)
        cond667 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns669 = xs666
    consume_literal!(parser, ")")
    return csv_columns669
end

function parse_csv_column(parser::ParserState)::Proto.CSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string670 = consume_terminal!(parser, "STRING")
    _t1258 = parse_relation_id(parser)
    relation_id671 = _t1258
    consume_literal!(parser, "[")
    xs672 = Proto.var"#Type"[]
    cond673 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond673
        _t1259 = parse_type(parser)
        item674 = _t1259
        push!(xs672, item674)
        cond673 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types675 = xs672
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1260 = Proto.CSVColumn(column_name=string670, target_id=relation_id671, types=types675)
    return _t1260
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string676 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string676
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1261 = parse_fragment_id(parser)
    fragment_id677 = _t1261
    consume_literal!(parser, ")")
    _t1262 = Proto.Undefine(fragment_id=fragment_id677)
    return _t1262
end

function parse_context(parser::ParserState)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs678 = Proto.RelationId[]
    cond679 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond679
        _t1263 = parse_relation_id(parser)
        item680 = _t1263
        push!(xs678, item680)
        cond679 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids681 = xs678
    consume_literal!(parser, ")")
    _t1264 = Proto.Context(relations=relation_ids681)
    return _t1264
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t1265 = parse_rel_edb_path(parser)
    rel_edb_path682 = _t1265
    _t1266 = parse_relation_id(parser)
    relation_id683 = _t1266
    consume_literal!(parser, ")")
    _t1267 = Proto.Snapshot(destination_path=rel_edb_path682, source_relation=relation_id683)
    return _t1267
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs684 = Proto.Read[]
    cond685 = match_lookahead_literal(parser, "(", 0)
    while cond685
        _t1268 = parse_read(parser)
        item686 = _t1268
        push!(xs684, item686)
        cond685 = match_lookahead_literal(parser, "(", 0)
    end
    reads687 = xs684
    consume_literal!(parser, ")")
    return reads687
end

function parse_read(parser::ParserState)::Proto.Read
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1270 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1271 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1272 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1273 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1274 = 3
                        else
                            _t1274 = -1
                        end
                        _t1273 = _t1274
                    end
                    _t1272 = _t1273
                end
                _t1271 = _t1272
            end
            _t1270 = _t1271
        end
        _t1269 = _t1270
    else
        _t1269 = -1
    end
    prediction688 = _t1269
    if prediction688 == 4
        _t1276 = parse_export(parser)
        export693 = _t1276
        _t1277 = Proto.Read(read_type=OneOf(:var"#export", export693))
        _t1275 = _t1277
    else
        if prediction688 == 3
            _t1279 = parse_abort(parser)
            abort692 = _t1279
            _t1280 = Proto.Read(read_type=OneOf(:abort, abort692))
            _t1278 = _t1280
        else
            if prediction688 == 2
                _t1282 = parse_what_if(parser)
                what_if691 = _t1282
                _t1283 = Proto.Read(read_type=OneOf(:what_if, what_if691))
                _t1281 = _t1283
            else
                if prediction688 == 1
                    _t1285 = parse_output(parser)
                    output690 = _t1285
                    _t1286 = Proto.Read(read_type=OneOf(:output, output690))
                    _t1284 = _t1286
                else
                    if prediction688 == 0
                        _t1288 = parse_demand(parser)
                        demand689 = _t1288
                        _t1289 = Proto.Read(read_type=OneOf(:demand, demand689))
                        _t1287 = _t1289
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1284 = _t1287
                end
                _t1281 = _t1284
            end
            _t1278 = _t1281
        end
        _t1275 = _t1278
    end
    return _t1275
end

function parse_demand(parser::ParserState)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1290 = parse_relation_id(parser)
    relation_id694 = _t1290
    consume_literal!(parser, ")")
    _t1291 = Proto.Demand(relation_id=relation_id694)
    return _t1291
end

function parse_output(parser::ParserState)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1292 = parse_name(parser)
    name695 = _t1292
    _t1293 = parse_relation_id(parser)
    relation_id696 = _t1293
    consume_literal!(parser, ")")
    _t1294 = Proto.Output(name=name695, relation_id=relation_id696)
    return _t1294
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1295 = parse_name(parser)
    name697 = _t1295
    _t1296 = parse_epoch(parser)
    epoch698 = _t1296
    consume_literal!(parser, ")")
    _t1297 = Proto.WhatIf(branch=name697, epoch=epoch698)
    return _t1297
end

function parse_abort(parser::ParserState)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1299 = parse_name(parser)
        _t1298 = _t1299
    else
        _t1298 = nothing
    end
    name699 = _t1298
    _t1300 = parse_relation_id(parser)
    relation_id700 = _t1300
    consume_literal!(parser, ")")
    _t1301 = Proto.Abort(name=(!isnothing(name699) ? name699 : "abort"), relation_id=relation_id700)
    return _t1301
end

function parse_export(parser::ParserState)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1302 = parse_export_csv_config(parser)
    export_csv_config701 = _t1302
    consume_literal!(parser, ")")
    _t1303 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config701))
    return _t1303
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1304 = parse_export_csv_path(parser)
    export_csv_path702 = _t1304
    _t1305 = parse_export_csv_columns(parser)
    export_csv_columns703 = _t1305
    _t1306 = parse_config_dict(parser)
    config_dict704 = _t1306
    consume_literal!(parser, ")")
    _t1307 = export_csv_config(parser, export_csv_path702, export_csv_columns703, config_dict704)
    return _t1307
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string705 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string705
end

function parse_export_csv_columns(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs706 = Proto.ExportCSVColumn[]
    cond707 = match_lookahead_literal(parser, "(", 0)
    while cond707
        _t1308 = parse_export_csv_column(parser)
        item708 = _t1308
        push!(xs706, item708)
        cond707 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns709 = xs706
    consume_literal!(parser, ")")
    return export_csv_columns709
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string710 = consume_terminal!(parser, "STRING")
    _t1309 = parse_relation_id(parser)
    relation_id711 = _t1309
    consume_literal!(parser, ")")
    _t1310 = Proto.ExportCSVColumn(column_name=string710, column_data=relation_id711)
    return _t1310
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
