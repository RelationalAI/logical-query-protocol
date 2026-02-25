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
        _t1329 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1330 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1331 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1332 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1333 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1334 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1335 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1336 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1337 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1338 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1338
    _t1339 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1339
    _t1340 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1340
    _t1341 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1341
    _t1342 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1342
    _t1343 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1343
    _t1344 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1344
    _t1345 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1345
    _t1346 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1346
    _t1347 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1347
    _t1348 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1348
    _t1349 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1349
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1350 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1350
    _t1351 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1351
    _t1352 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1352
    _t1353 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1353
    _t1354 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1354
    _t1355 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1355
    _t1356 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1356
    _t1357 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1357
    _t1358 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1358
    _t1359 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1359
    _t1360 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1360
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1361 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1361
    _t1362 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1362
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
    _t1363 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1363
    _t1364 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1364
    _t1365 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1365
end

function export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1366 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1366
    _t1367 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1367
    _t1368 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1368
    _t1369 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1369
    _t1370 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1370
    _t1371 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1371
    _t1372 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1372
    _t1373 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1373
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t725 = parse_configure(parser)
        _t724 = _t725
    else
        _t724 = nothing
    end
    configure362 = _t724
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t727 = parse_sync(parser)
        _t726 = _t727
    else
        _t726 = nothing
    end
    sync363 = _t726
    xs364 = Proto.Epoch[]
    cond365 = match_lookahead_literal(parser, "(", 0)
    while cond365
        _t728 = parse_epoch(parser)
        item366 = _t728
        push!(xs364, item366)
        cond365 = match_lookahead_literal(parser, "(", 0)
    end
    epochs367 = xs364
    consume_literal!(parser, ")")
    _t729 = default_configure(parser)
    _t730 = Proto.Transaction(epochs=epochs367, configure=(!isnothing(configure362) ? configure362 : _t729), sync=sync363)
    return _t730
end

function parse_configure(parser::ParserState)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t731 = parse_config_dict(parser)
    config_dict368 = _t731
    consume_literal!(parser, ")")
    _t732 = construct_configure(parser, config_dict368)
    return _t732
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs369 = Tuple{String, Proto.Value}[]
    cond370 = match_lookahead_literal(parser, ":", 0)
    while cond370
        _t733 = parse_config_key_value(parser)
        item371 = _t733
        push!(xs369, item371)
        cond370 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values372 = xs369
    consume_literal!(parser, "}")
    return config_key_values372
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol373 = consume_terminal!(parser, "SYMBOL")
    _t734 = parse_value(parser)
    value374 = _t734
    return (symbol373, value374,)
end

function parse_value(parser::ParserState)::Proto.Value
    if match_lookahead_literal(parser, "true", 0)
        _t735 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t736 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t737 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t739 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t740 = 0
                        else
                            _t740 = -1
                        end
                        _t739 = _t740
                    end
                    _t738 = _t739
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t741 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t742 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t743 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t744 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t745 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t746 = 7
                                        else
                                            _t746 = -1
                                        end
                                        _t745 = _t746
                                    end
                                    _t744 = _t745
                                end
                                _t743 = _t744
                            end
                            _t742 = _t743
                        end
                        _t741 = _t742
                    end
                    _t738 = _t741
                end
                _t737 = _t738
            end
            _t736 = _t737
        end
        _t735 = _t736
    end
    prediction375 = _t735
    if prediction375 == 9
        _t748 = parse_boolean_value(parser)
        boolean_value384 = _t748
        _t749 = Proto.Value(value=OneOf(:boolean_value, boolean_value384))
        _t747 = _t749
    else
        if prediction375 == 8
            consume_literal!(parser, "missing")
            _t751 = Proto.MissingValue()
            _t752 = Proto.Value(value=OneOf(:missing_value, _t751))
            _t750 = _t752
        else
            if prediction375 == 7
                decimal383 = consume_terminal!(parser, "DECIMAL")
                _t754 = Proto.Value(value=OneOf(:decimal_value, decimal383))
                _t753 = _t754
            else
                if prediction375 == 6
                    int128382 = consume_terminal!(parser, "INT128")
                    _t756 = Proto.Value(value=OneOf(:int128_value, int128382))
                    _t755 = _t756
                else
                    if prediction375 == 5
                        uint128381 = consume_terminal!(parser, "UINT128")
                        _t758 = Proto.Value(value=OneOf(:uint128_value, uint128381))
                        _t757 = _t758
                    else
                        if prediction375 == 4
                            float380 = consume_terminal!(parser, "FLOAT")
                            _t760 = Proto.Value(value=OneOf(:float_value, float380))
                            _t759 = _t760
                        else
                            if prediction375 == 3
                                int379 = consume_terminal!(parser, "INT")
                                _t762 = Proto.Value(value=OneOf(:int_value, int379))
                                _t761 = _t762
                            else
                                if prediction375 == 2
                                    string378 = consume_terminal!(parser, "STRING")
                                    _t764 = Proto.Value(value=OneOf(:string_value, string378))
                                    _t763 = _t764
                                else
                                    if prediction375 == 1
                                        _t766 = parse_datetime(parser)
                                        datetime377 = _t766
                                        _t767 = Proto.Value(value=OneOf(:datetime_value, datetime377))
                                        _t765 = _t767
                                    else
                                        if prediction375 == 0
                                            _t769 = parse_date(parser)
                                            date376 = _t769
                                            _t770 = Proto.Value(value=OneOf(:date_value, date376))
                                            _t768 = _t770
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t765 = _t768
                                    end
                                    _t763 = _t765
                                end
                                _t761 = _t763
                            end
                            _t759 = _t761
                        end
                        _t757 = _t759
                    end
                    _t755 = _t757
                end
                _t753 = _t755
            end
            _t750 = _t753
        end
        _t747 = _t750
    end
    return _t747
end

function parse_date(parser::ParserState)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int385 = consume_terminal!(parser, "INT")
    int_3386 = consume_terminal!(parser, "INT")
    int_4387 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t771 = Proto.DateValue(year=Int32(int385), month=Int32(int_3386), day=Int32(int_4387))
    return _t771
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int388 = consume_terminal!(parser, "INT")
    int_3389 = consume_terminal!(parser, "INT")
    int_4390 = consume_terminal!(parser, "INT")
    int_5391 = consume_terminal!(parser, "INT")
    int_6392 = consume_terminal!(parser, "INT")
    int_7393 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t772 = consume_terminal!(parser, "INT")
    else
        _t772 = nothing
    end
    int_8394 = _t772
    consume_literal!(parser, ")")
    _t773 = Proto.DateTimeValue(year=Int32(int388), month=Int32(int_3389), day=Int32(int_4390), hour=Int32(int_5391), minute=Int32(int_6392), second=Int32(int_7393), microsecond=Int32((!isnothing(int_8394) ? int_8394 : 0)))
    return _t773
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t774 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t775 = 1
        else
            _t775 = -1
        end
        _t774 = _t775
    end
    prediction395 = _t774
    if prediction395 == 1
        consume_literal!(parser, "false")
        _t776 = false
    else
        if prediction395 == 0
            consume_literal!(parser, "true")
            _t777 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t776 = _t777
    end
    return _t776
end

function parse_sync(parser::ParserState)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs396 = Proto.FragmentId[]
    cond397 = match_lookahead_literal(parser, ":", 0)
    while cond397
        _t778 = parse_fragment_id(parser)
        item398 = _t778
        push!(xs396, item398)
        cond397 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids399 = xs396
    consume_literal!(parser, ")")
    _t779 = Proto.Sync(fragments=fragment_ids399)
    return _t779
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol400 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol400))
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t781 = parse_epoch_writes(parser)
        _t780 = _t781
    else
        _t780 = nothing
    end
    epoch_writes401 = _t780
    if match_lookahead_literal(parser, "(", 0)
        _t783 = parse_epoch_reads(parser)
        _t782 = _t783
    else
        _t782 = nothing
    end
    epoch_reads402 = _t782
    consume_literal!(parser, ")")
    _t784 = Proto.Epoch(writes=(!isnothing(epoch_writes401) ? epoch_writes401 : Proto.Write[]), reads=(!isnothing(epoch_reads402) ? epoch_reads402 : Proto.Read[]))
    return _t784
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs403 = Proto.Write[]
    cond404 = match_lookahead_literal(parser, "(", 0)
    while cond404
        _t785 = parse_write(parser)
        item405 = _t785
        push!(xs403, item405)
        cond404 = match_lookahead_literal(parser, "(", 0)
    end
    writes406 = xs403
    consume_literal!(parser, ")")
    return writes406
end

function parse_write(parser::ParserState)::Proto.Write
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t787 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t788 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t789 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t790 = 2
                    else
                        _t790 = -1
                    end
                    _t789 = _t790
                end
                _t788 = _t789
            end
            _t787 = _t788
        end
        _t786 = _t787
    else
        _t786 = -1
    end
    prediction407 = _t786
    if prediction407 == 3
        _t792 = parse_snapshot(parser)
        snapshot411 = _t792
        _t793 = Proto.Write(write_type=OneOf(:snapshot, snapshot411))
        _t791 = _t793
    else
        if prediction407 == 2
            _t795 = parse_context(parser)
            context410 = _t795
            _t796 = Proto.Write(write_type=OneOf(:context, context410))
            _t794 = _t796
        else
            if prediction407 == 1
                _t798 = parse_undefine(parser)
                undefine409 = _t798
                _t799 = Proto.Write(write_type=OneOf(:undefine, undefine409))
                _t797 = _t799
            else
                if prediction407 == 0
                    _t801 = parse_define(parser)
                    define408 = _t801
                    _t802 = Proto.Write(write_type=OneOf(:define, define408))
                    _t800 = _t802
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t797 = _t800
            end
            _t794 = _t797
        end
        _t791 = _t794
    end
    return _t791
end

function parse_define(parser::ParserState)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t803 = parse_fragment(parser)
    fragment412 = _t803
    consume_literal!(parser, ")")
    _t804 = Proto.Define(fragment=fragment412)
    return _t804
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t805 = parse_new_fragment_id(parser)
    new_fragment_id413 = _t805
    xs414 = Proto.Declaration[]
    cond415 = match_lookahead_literal(parser, "(", 0)
    while cond415
        _t806 = parse_declaration(parser)
        item416 = _t806
        push!(xs414, item416)
        cond415 = match_lookahead_literal(parser, "(", 0)
    end
    declarations417 = xs414
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id413, declarations417)
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    _t807 = parse_fragment_id(parser)
    fragment_id418 = _t807
    start_fragment!(parser, fragment_id418)
    return fragment_id418
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "functional_dependency", 1)
            _t809 = 2
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t810 = 3
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t811 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t812 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t813 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t814 = 1
                            else
                                _t814 = -1
                            end
                            _t813 = _t814
                        end
                        _t812 = _t813
                    end
                    _t811 = _t812
                end
                _t810 = _t811
            end
            _t809 = _t810
        end
        _t808 = _t809
    else
        _t808 = -1
    end
    prediction419 = _t808
    if prediction419 == 3
        _t816 = parse_data(parser)
        data423 = _t816
        _t817 = Proto.Declaration(declaration_type=OneOf(:data, data423))
        _t815 = _t817
    else
        if prediction419 == 2
            _t819 = parse_constraint(parser)
            constraint422 = _t819
            _t820 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint422))
            _t818 = _t820
        else
            if prediction419 == 1
                _t822 = parse_algorithm(parser)
                algorithm421 = _t822
                _t823 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm421))
                _t821 = _t823
            else
                if prediction419 == 0
                    _t825 = parse_def(parser)
                    def420 = _t825
                    _t826 = Proto.Declaration(declaration_type=OneOf(:def, def420))
                    _t824 = _t826
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t821 = _t824
            end
            _t818 = _t821
        end
        _t815 = _t818
    end
    return _t815
end

function parse_def(parser::ParserState)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t827 = parse_relation_id(parser)
    relation_id424 = _t827
    _t828 = parse_abstraction(parser)
    abstraction425 = _t828
    if match_lookahead_literal(parser, "(", 0)
        _t830 = parse_attrs(parser)
        _t829 = _t830
    else
        _t829 = nothing
    end
    attrs426 = _t829
    consume_literal!(parser, ")")
    _t831 = Proto.Def(name=relation_id424, body=abstraction425, attrs=(!isnothing(attrs426) ? attrs426 : Proto.Attribute[]))
    return _t831
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    if match_lookahead_literal(parser, ":", 0)
        _t832 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t833 = 1
        else
            _t833 = -1
        end
        _t832 = _t833
    end
    prediction427 = _t832
    if prediction427 == 1
        uint128429 = consume_terminal!(parser, "UINT128")
        _t834 = Proto.RelationId(uint128429.low, uint128429.high)
    else
        if prediction427 == 0
            consume_literal!(parser, ":")
            symbol428 = consume_terminal!(parser, "SYMBOL")
            _t835 = relation_id_from_string(parser, symbol428)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t834 = _t835
    end
    return _t834
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t836 = parse_bindings(parser)
    bindings430 = _t836
    _t837 = parse_formula(parser)
    formula431 = _t837
    consume_literal!(parser, ")")
    _t838 = Proto.Abstraction(vars=vcat(bindings430[1], !isnothing(bindings430[2]) ? bindings430[2] : []), value=formula431)
    return _t838
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs432 = Proto.Binding[]
    cond433 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond433
        _t839 = parse_binding(parser)
        item434 = _t839
        push!(xs432, item434)
        cond433 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings435 = xs432
    if match_lookahead_literal(parser, "|", 0)
        _t841 = parse_value_bindings(parser)
        _t840 = _t841
    else
        _t840 = nothing
    end
    value_bindings436 = _t840
    consume_literal!(parser, "]")
    return (bindings435, (!isnothing(value_bindings436) ? value_bindings436 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    symbol437 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t842 = parse_type(parser)
    type438 = _t842
    _t843 = Proto.Var(name=symbol437)
    _t844 = Proto.Binding(var=_t843, var"#type"=type438)
    return _t844
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t845 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t846 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t847 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t848 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t849 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t850 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t851 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t852 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t853 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t854 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t855 = 9
                                            else
                                                _t855 = -1
                                            end
                                            _t854 = _t855
                                        end
                                        _t853 = _t854
                                    end
                                    _t852 = _t853
                                end
                                _t851 = _t852
                            end
                            _t850 = _t851
                        end
                        _t849 = _t850
                    end
                    _t848 = _t849
                end
                _t847 = _t848
            end
            _t846 = _t847
        end
        _t845 = _t846
    end
    prediction439 = _t845
    if prediction439 == 10
        _t857 = parse_boolean_type(parser)
        boolean_type450 = _t857
        _t858 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type450))
        _t856 = _t858
    else
        if prediction439 == 9
            _t860 = parse_decimal_type(parser)
            decimal_type449 = _t860
            _t861 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type449))
            _t859 = _t861
        else
            if prediction439 == 8
                _t863 = parse_missing_type(parser)
                missing_type448 = _t863
                _t864 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type448))
                _t862 = _t864
            else
                if prediction439 == 7
                    _t866 = parse_datetime_type(parser)
                    datetime_type447 = _t866
                    _t867 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type447))
                    _t865 = _t867
                else
                    if prediction439 == 6
                        _t869 = parse_date_type(parser)
                        date_type446 = _t869
                        _t870 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type446))
                        _t868 = _t870
                    else
                        if prediction439 == 5
                            _t872 = parse_int128_type(parser)
                            int128_type445 = _t872
                            _t873 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type445))
                            _t871 = _t873
                        else
                            if prediction439 == 4
                                _t875 = parse_uint128_type(parser)
                                uint128_type444 = _t875
                                _t876 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type444))
                                _t874 = _t876
                            else
                                if prediction439 == 3
                                    _t878 = parse_float_type(parser)
                                    float_type443 = _t878
                                    _t879 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type443))
                                    _t877 = _t879
                                else
                                    if prediction439 == 2
                                        _t881 = parse_int_type(parser)
                                        int_type442 = _t881
                                        _t882 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type442))
                                        _t880 = _t882
                                    else
                                        if prediction439 == 1
                                            _t884 = parse_string_type(parser)
                                            string_type441 = _t884
                                            _t885 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type441))
                                            _t883 = _t885
                                        else
                                            if prediction439 == 0
                                                _t887 = parse_unspecified_type(parser)
                                                unspecified_type440 = _t887
                                                _t888 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type440))
                                                _t886 = _t888
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                    _t865 = _t868
                end
                _t862 = _t865
            end
            _t859 = _t862
        end
        _t856 = _t859
    end
    return _t856
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t889 = Proto.UnspecifiedType()
    return _t889
end

function parse_string_type(parser::ParserState)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t890 = Proto.StringType()
    return _t890
end

function parse_int_type(parser::ParserState)::Proto.IntType
    consume_literal!(parser, "INT")
    _t891 = Proto.IntType()
    return _t891
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t892 = Proto.FloatType()
    return _t892
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t893 = Proto.UInt128Type()
    return _t893
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t894 = Proto.Int128Type()
    return _t894
end

function parse_date_type(parser::ParserState)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t895 = Proto.DateType()
    return _t895
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t896 = Proto.DateTimeType()
    return _t896
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t897 = Proto.MissingType()
    return _t897
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int451 = consume_terminal!(parser, "INT")
    int_3452 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t898 = Proto.DecimalType(precision=Int32(int451), scale=Int32(int_3452))
    return _t898
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t899 = Proto.BooleanType()
    return _t899
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs453 = Proto.Binding[]
    cond454 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond454
        _t900 = parse_binding(parser)
        item455 = _t900
        push!(xs453, item455)
        cond454 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings456 = xs453
    return bindings456
end

function parse_formula(parser::ParserState)::Proto.Formula
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t902 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t903 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t904 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t905 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t906 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t907 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t908 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t909 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t910 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t911 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t912 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t913 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t914 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t915 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t916 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t917 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t918 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t919 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t920 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t921 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t922 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t923 = 10
                                                                                            else
                                                                                                _t923 = -1
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
    else
        _t901 = -1
    end
    prediction457 = _t901
    if prediction457 == 12
        _t925 = parse_cast(parser)
        cast470 = _t925
        _t926 = Proto.Formula(formula_type=OneOf(:cast, cast470))
        _t924 = _t926
    else
        if prediction457 == 11
            _t928 = parse_rel_atom(parser)
            rel_atom469 = _t928
            _t929 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom469))
            _t927 = _t929
        else
            if prediction457 == 10
                _t931 = parse_primitive(parser)
                primitive468 = _t931
                _t932 = Proto.Formula(formula_type=OneOf(:primitive, primitive468))
                _t930 = _t932
            else
                if prediction457 == 9
                    _t934 = parse_pragma(parser)
                    pragma467 = _t934
                    _t935 = Proto.Formula(formula_type=OneOf(:pragma, pragma467))
                    _t933 = _t935
                else
                    if prediction457 == 8
                        _t937 = parse_atom(parser)
                        atom466 = _t937
                        _t938 = Proto.Formula(formula_type=OneOf(:atom, atom466))
                        _t936 = _t938
                    else
                        if prediction457 == 7
                            _t940 = parse_ffi(parser)
                            ffi465 = _t940
                            _t941 = Proto.Formula(formula_type=OneOf(:ffi, ffi465))
                            _t939 = _t941
                        else
                            if prediction457 == 6
                                _t943 = parse_not(parser)
                                not464 = _t943
                                _t944 = Proto.Formula(formula_type=OneOf(:not, not464))
                                _t942 = _t944
                            else
                                if prediction457 == 5
                                    _t946 = parse_disjunction(parser)
                                    disjunction463 = _t946
                                    _t947 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction463))
                                    _t945 = _t947
                                else
                                    if prediction457 == 4
                                        _t949 = parse_conjunction(parser)
                                        conjunction462 = _t949
                                        _t950 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction462))
                                        _t948 = _t950
                                    else
                                        if prediction457 == 3
                                            _t952 = parse_reduce(parser)
                                            reduce461 = _t952
                                            _t953 = Proto.Formula(formula_type=OneOf(:reduce, reduce461))
                                            _t951 = _t953
                                        else
                                            if prediction457 == 2
                                                _t955 = parse_exists(parser)
                                                exists460 = _t955
                                                _t956 = Proto.Formula(formula_type=OneOf(:exists, exists460))
                                                _t954 = _t956
                                            else
                                                if prediction457 == 1
                                                    _t958 = parse_false(parser)
                                                    false459 = _t958
                                                    _t959 = Proto.Formula(formula_type=OneOf(:disjunction, false459))
                                                    _t957 = _t959
                                                else
                                                    if prediction457 == 0
                                                        _t961 = parse_true(parser)
                                                        true458 = _t961
                                                        _t962 = Proto.Formula(formula_type=OneOf(:conjunction, true458))
                                                        _t960 = _t962
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
                    _t933 = _t936
                end
                _t930 = _t933
            end
            _t927 = _t930
        end
        _t924 = _t927
    end
    return _t924
end

function parse_true(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t963 = Proto.Conjunction(args=Proto.Formula[])
    return _t963
end

function parse_false(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t964 = Proto.Disjunction(args=Proto.Formula[])
    return _t964
end

function parse_exists(parser::ParserState)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t965 = parse_bindings(parser)
    bindings471 = _t965
    _t966 = parse_formula(parser)
    formula472 = _t966
    consume_literal!(parser, ")")
    _t967 = Proto.Abstraction(vars=vcat(bindings471[1], !isnothing(bindings471[2]) ? bindings471[2] : []), value=formula472)
    _t968 = Proto.Exists(body=_t967)
    return _t968
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t969 = parse_abstraction(parser)
    abstraction473 = _t969
    _t970 = parse_abstraction(parser)
    abstraction_3474 = _t970
    _t971 = parse_terms(parser)
    terms475 = _t971
    consume_literal!(parser, ")")
    _t972 = Proto.Reduce(op=abstraction473, body=abstraction_3474, terms=terms475)
    return _t972
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs476 = Proto.Term[]
    cond477 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond477
        _t973 = parse_term(parser)
        item478 = _t973
        push!(xs476, item478)
        cond477 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms479 = xs476
    consume_literal!(parser, ")")
    return terms479
end

function parse_term(parser::ParserState)::Proto.Term
    if match_lookahead_literal(parser, "true", 0)
        _t974 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t975 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t976 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t977 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t978 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t979 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t980 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t981 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t982 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t983 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t984 = 1
                                            else
                                                _t984 = -1
                                            end
                                            _t983 = _t984
                                        end
                                        _t982 = _t983
                                    end
                                    _t981 = _t982
                                end
                                _t980 = _t981
                            end
                            _t979 = _t980
                        end
                        _t978 = _t979
                    end
                    _t977 = _t978
                end
                _t976 = _t977
            end
            _t975 = _t976
        end
        _t974 = _t975
    end
    prediction480 = _t974
    if prediction480 == 1
        _t986 = parse_constant(parser)
        constant482 = _t986
        _t987 = Proto.Term(term_type=OneOf(:constant, constant482))
        _t985 = _t987
    else
        if prediction480 == 0
            _t989 = parse_var(parser)
            var481 = _t989
            _t990 = Proto.Term(term_type=OneOf(:var, var481))
            _t988 = _t990
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t985 = _t988
    end
    return _t985
end

function parse_var(parser::ParserState)::Proto.Var
    symbol483 = consume_terminal!(parser, "SYMBOL")
    _t991 = Proto.Var(name=symbol483)
    return _t991
end

function parse_constant(parser::ParserState)::Proto.Value
    _t992 = parse_value(parser)
    value484 = _t992
    return value484
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs485 = Proto.Formula[]
    cond486 = match_lookahead_literal(parser, "(", 0)
    while cond486
        _t993 = parse_formula(parser)
        item487 = _t993
        push!(xs485, item487)
        cond486 = match_lookahead_literal(parser, "(", 0)
    end
    formulas488 = xs485
    consume_literal!(parser, ")")
    _t994 = Proto.Conjunction(args=formulas488)
    return _t994
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs489 = Proto.Formula[]
    cond490 = match_lookahead_literal(parser, "(", 0)
    while cond490
        _t995 = parse_formula(parser)
        item491 = _t995
        push!(xs489, item491)
        cond490 = match_lookahead_literal(parser, "(", 0)
    end
    formulas492 = xs489
    consume_literal!(parser, ")")
    _t996 = Proto.Disjunction(args=formulas492)
    return _t996
end

function parse_not(parser::ParserState)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t997 = parse_formula(parser)
    formula493 = _t997
    consume_literal!(parser, ")")
    _t998 = Proto.Not(arg=formula493)
    return _t998
end

function parse_ffi(parser::ParserState)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t999 = parse_name(parser)
    name494 = _t999
    _t1000 = parse_ffi_args(parser)
    ffi_args495 = _t1000
    _t1001 = parse_terms(parser)
    terms496 = _t1001
    consume_literal!(parser, ")")
    _t1002 = Proto.FFI(name=name494, args=ffi_args495, terms=terms496)
    return _t1002
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol497 = consume_terminal!(parser, "SYMBOL")
    return symbol497
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs498 = Proto.Abstraction[]
    cond499 = match_lookahead_literal(parser, "(", 0)
    while cond499
        _t1003 = parse_abstraction(parser)
        item500 = _t1003
        push!(xs498, item500)
        cond499 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions501 = xs498
    consume_literal!(parser, ")")
    return abstractions501
end

function parse_atom(parser::ParserState)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1004 = parse_relation_id(parser)
    relation_id502 = _t1004
    xs503 = Proto.Term[]
    cond504 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond504
        _t1005 = parse_term(parser)
        item505 = _t1005
        push!(xs503, item505)
        cond504 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms506 = xs503
    consume_literal!(parser, ")")
    _t1006 = Proto.Atom(name=relation_id502, terms=terms506)
    return _t1006
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1007 = parse_name(parser)
    name507 = _t1007
    xs508 = Proto.Term[]
    cond509 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond509
        _t1008 = parse_term(parser)
        item510 = _t1008
        push!(xs508, item510)
        cond509 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms511 = xs508
    consume_literal!(parser, ")")
    _t1009 = Proto.Pragma(name=name507, terms=terms511)
    return _t1009
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1011 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1012 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1013 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1014 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1015 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1016 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1017 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1018 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1019 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1020 = 7
                                            else
                                                _t1020 = -1
                                            end
                                            _t1019 = _t1020
                                        end
                                        _t1018 = _t1019
                                    end
                                    _t1017 = _t1018
                                end
                                _t1016 = _t1017
                            end
                            _t1015 = _t1016
                        end
                        _t1014 = _t1015
                    end
                    _t1013 = _t1014
                end
                _t1012 = _t1013
            end
            _t1011 = _t1012
        end
        _t1010 = _t1011
    else
        _t1010 = -1
    end
    prediction512 = _t1010
    if prediction512 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1022 = parse_name(parser)
        name522 = _t1022
        xs523 = Proto.RelTerm[]
        cond524 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond524
            _t1023 = parse_rel_term(parser)
            item525 = _t1023
            push!(xs523, item525)
            cond524 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms526 = xs523
        consume_literal!(parser, ")")
        _t1024 = Proto.Primitive(name=name522, terms=rel_terms526)
        _t1021 = _t1024
    else
        if prediction512 == 8
            _t1026 = parse_divide(parser)
            divide521 = _t1026
            _t1025 = divide521
        else
            if prediction512 == 7
                _t1028 = parse_multiply(parser)
                multiply520 = _t1028
                _t1027 = multiply520
            else
                if prediction512 == 6
                    _t1030 = parse_minus(parser)
                    minus519 = _t1030
                    _t1029 = minus519
                else
                    if prediction512 == 5
                        _t1032 = parse_add(parser)
                        add518 = _t1032
                        _t1031 = add518
                    else
                        if prediction512 == 4
                            _t1034 = parse_gt_eq(parser)
                            gt_eq517 = _t1034
                            _t1033 = gt_eq517
                        else
                            if prediction512 == 3
                                _t1036 = parse_gt(parser)
                                gt516 = _t1036
                                _t1035 = gt516
                            else
                                if prediction512 == 2
                                    _t1038 = parse_lt_eq(parser)
                                    lt_eq515 = _t1038
                                    _t1037 = lt_eq515
                                else
                                    if prediction512 == 1
                                        _t1040 = parse_lt(parser)
                                        lt514 = _t1040
                                        _t1039 = lt514
                                    else
                                        if prediction512 == 0
                                            _t1042 = parse_eq(parser)
                                            eq513 = _t1042
                                            _t1041 = eq513
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1039 = _t1041
                                    end
                                    _t1037 = _t1039
                                end
                                _t1035 = _t1037
                            end
                            _t1033 = _t1035
                        end
                        _t1031 = _t1033
                    end
                    _t1029 = _t1031
                end
                _t1027 = _t1029
            end
            _t1025 = _t1027
        end
        _t1021 = _t1025
    end
    return _t1021
end

function parse_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1043 = parse_term(parser)
    term527 = _t1043
    _t1044 = parse_term(parser)
    term_3528 = _t1044
    consume_literal!(parser, ")")
    _t1045 = Proto.RelTerm(rel_term_type=OneOf(:term, term527))
    _t1046 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3528))
    _t1047 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1045, _t1046])
    return _t1047
end

function parse_lt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1048 = parse_term(parser)
    term529 = _t1048
    _t1049 = parse_term(parser)
    term_3530 = _t1049
    consume_literal!(parser, ")")
    _t1050 = Proto.RelTerm(rel_term_type=OneOf(:term, term529))
    _t1051 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3530))
    _t1052 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1050, _t1051])
    return _t1052
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1053 = parse_term(parser)
    term531 = _t1053
    _t1054 = parse_term(parser)
    term_3532 = _t1054
    consume_literal!(parser, ")")
    _t1055 = Proto.RelTerm(rel_term_type=OneOf(:term, term531))
    _t1056 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3532))
    _t1057 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1055, _t1056])
    return _t1057
end

function parse_gt(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1058 = parse_term(parser)
    term533 = _t1058
    _t1059 = parse_term(parser)
    term_3534 = _t1059
    consume_literal!(parser, ")")
    _t1060 = Proto.RelTerm(rel_term_type=OneOf(:term, term533))
    _t1061 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3534))
    _t1062 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1060, _t1061])
    return _t1062
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1063 = parse_term(parser)
    term535 = _t1063
    _t1064 = parse_term(parser)
    term_3536 = _t1064
    consume_literal!(parser, ")")
    _t1065 = Proto.RelTerm(rel_term_type=OneOf(:term, term535))
    _t1066 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3536))
    _t1067 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1065, _t1066])
    return _t1067
end

function parse_add(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1068 = parse_term(parser)
    term537 = _t1068
    _t1069 = parse_term(parser)
    term_3538 = _t1069
    _t1070 = parse_term(parser)
    term_4539 = _t1070
    consume_literal!(parser, ")")
    _t1071 = Proto.RelTerm(rel_term_type=OneOf(:term, term537))
    _t1072 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3538))
    _t1073 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4539))
    _t1074 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1071, _t1072, _t1073])
    return _t1074
end

function parse_minus(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1075 = parse_term(parser)
    term540 = _t1075
    _t1076 = parse_term(parser)
    term_3541 = _t1076
    _t1077 = parse_term(parser)
    term_4542 = _t1077
    consume_literal!(parser, ")")
    _t1078 = Proto.RelTerm(rel_term_type=OneOf(:term, term540))
    _t1079 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3541))
    _t1080 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4542))
    _t1081 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1078, _t1079, _t1080])
    return _t1081
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1082 = parse_term(parser)
    term543 = _t1082
    _t1083 = parse_term(parser)
    term_3544 = _t1083
    _t1084 = parse_term(parser)
    term_4545 = _t1084
    consume_literal!(parser, ")")
    _t1085 = Proto.RelTerm(rel_term_type=OneOf(:term, term543))
    _t1086 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3544))
    _t1087 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4545))
    _t1088 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1085, _t1086, _t1087])
    return _t1088
end

function parse_divide(parser::ParserState)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1089 = parse_term(parser)
    term546 = _t1089
    _t1090 = parse_term(parser)
    term_3547 = _t1090
    _t1091 = parse_term(parser)
    term_4548 = _t1091
    consume_literal!(parser, ")")
    _t1092 = Proto.RelTerm(rel_term_type=OneOf(:term, term546))
    _t1093 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3547))
    _t1094 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4548))
    _t1095 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1092, _t1093, _t1094])
    return _t1095
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    if match_lookahead_literal(parser, "true", 0)
        _t1096 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1097 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1098 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1099 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1100 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1101 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1102 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1103 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1104 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1105 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1106 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1107 = 1
                                                else
                                                    _t1107 = -1
                                                end
                                                _t1106 = _t1107
                                            end
                                            _t1105 = _t1106
                                        end
                                        _t1104 = _t1105
                                    end
                                    _t1103 = _t1104
                                end
                                _t1102 = _t1103
                            end
                            _t1101 = _t1102
                        end
                        _t1100 = _t1101
                    end
                    _t1099 = _t1100
                end
                _t1098 = _t1099
            end
            _t1097 = _t1098
        end
        _t1096 = _t1097
    end
    prediction549 = _t1096
    if prediction549 == 1
        _t1109 = parse_term(parser)
        term551 = _t1109
        _t1110 = Proto.RelTerm(rel_term_type=OneOf(:term, term551))
        _t1108 = _t1110
    else
        if prediction549 == 0
            _t1112 = parse_specialized_value(parser)
            specialized_value550 = _t1112
            _t1113 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value550))
            _t1111 = _t1113
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1108 = _t1111
    end
    return _t1108
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    consume_literal!(parser, "#")
    _t1114 = parse_value(parser)
    value552 = _t1114
    return value552
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1115 = parse_name(parser)
    name553 = _t1115
    xs554 = Proto.RelTerm[]
    cond555 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond555
        _t1116 = parse_rel_term(parser)
        item556 = _t1116
        push!(xs554, item556)
        cond555 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms557 = xs554
    consume_literal!(parser, ")")
    _t1117 = Proto.RelAtom(name=name553, terms=rel_terms557)
    return _t1117
end

function parse_cast(parser::ParserState)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1118 = parse_term(parser)
    term558 = _t1118
    _t1119 = parse_term(parser)
    term_3559 = _t1119
    consume_literal!(parser, ")")
    _t1120 = Proto.Cast(input=term558, result=term_3559)
    return _t1120
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs560 = Proto.Attribute[]
    cond561 = match_lookahead_literal(parser, "(", 0)
    while cond561
        _t1121 = parse_attribute(parser)
        item562 = _t1121
        push!(xs560, item562)
        cond561 = match_lookahead_literal(parser, "(", 0)
    end
    attributes563 = xs560
    consume_literal!(parser, ")")
    return attributes563
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1122 = parse_name(parser)
    name564 = _t1122
    xs565 = Proto.Value[]
    cond566 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond566
        _t1123 = parse_value(parser)
        item567 = _t1123
        push!(xs565, item567)
        cond566 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values568 = xs565
    consume_literal!(parser, ")")
    _t1124 = Proto.Attribute(name=name564, args=values568)
    return _t1124
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs569 = Proto.RelationId[]
    cond570 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond570
        _t1125 = parse_relation_id(parser)
        item571 = _t1125
        push!(xs569, item571)
        cond570 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids572 = xs569
    _t1126 = parse_script(parser)
    script573 = _t1126
    consume_literal!(parser, ")")
    _t1127 = Proto.Algorithm(var"#global"=relation_ids572, body=script573)
    return _t1127
end

function parse_script(parser::ParserState)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs574 = Proto.Construct[]
    cond575 = match_lookahead_literal(parser, "(", 0)
    while cond575
        _t1128 = parse_construct(parser)
        item576 = _t1128
        push!(xs574, item576)
        cond575 = match_lookahead_literal(parser, "(", 0)
    end
    constructs577 = xs574
    consume_literal!(parser, ")")
    _t1129 = Proto.Script(constructs=constructs577)
    return _t1129
end

function parse_construct(parser::ParserState)::Proto.Construct
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1131 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1132 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1133 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1134 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1135 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1136 = 1
                            else
                                _t1136 = -1
                            end
                            _t1135 = _t1136
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
    else
        _t1130 = -1
    end
    prediction578 = _t1130
    if prediction578 == 1
        _t1138 = parse_instruction(parser)
        instruction580 = _t1138
        _t1139 = Proto.Construct(construct_type=OneOf(:instruction, instruction580))
        _t1137 = _t1139
    else
        if prediction578 == 0
            _t1141 = parse_loop(parser)
            loop579 = _t1141
            _t1142 = Proto.Construct(construct_type=OneOf(:loop, loop579))
            _t1140 = _t1142
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1137 = _t1140
    end
    return _t1137
end

function parse_loop(parser::ParserState)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1143 = parse_init(parser)
    init581 = _t1143
    _t1144 = parse_script(parser)
    script582 = _t1144
    consume_literal!(parser, ")")
    _t1145 = Proto.Loop(init=init581, body=script582)
    return _t1145
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs583 = Proto.Instruction[]
    cond584 = match_lookahead_literal(parser, "(", 0)
    while cond584
        _t1146 = parse_instruction(parser)
        item585 = _t1146
        push!(xs583, item585)
        cond584 = match_lookahead_literal(parser, "(", 0)
    end
    instructions586 = xs583
    consume_literal!(parser, ")")
    return instructions586
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1148 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1149 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1150 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1151 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1152 = 0
                        else
                            _t1152 = -1
                        end
                        _t1151 = _t1152
                    end
                    _t1150 = _t1151
                end
                _t1149 = _t1150
            end
            _t1148 = _t1149
        end
        _t1147 = _t1148
    else
        _t1147 = -1
    end
    prediction587 = _t1147
    if prediction587 == 4
        _t1154 = parse_monus_def(parser)
        monus_def592 = _t1154
        _t1155 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def592))
        _t1153 = _t1155
    else
        if prediction587 == 3
            _t1157 = parse_monoid_def(parser)
            monoid_def591 = _t1157
            _t1158 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def591))
            _t1156 = _t1158
        else
            if prediction587 == 2
                _t1160 = parse_break(parser)
                break590 = _t1160
                _t1161 = Proto.Instruction(instr_type=OneOf(:var"#break", break590))
                _t1159 = _t1161
            else
                if prediction587 == 1
                    _t1163 = parse_upsert(parser)
                    upsert589 = _t1163
                    _t1164 = Proto.Instruction(instr_type=OneOf(:upsert, upsert589))
                    _t1162 = _t1164
                else
                    if prediction587 == 0
                        _t1166 = parse_assign(parser)
                        assign588 = _t1166
                        _t1167 = Proto.Instruction(instr_type=OneOf(:assign, assign588))
                        _t1165 = _t1167
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1162 = _t1165
                end
                _t1159 = _t1162
            end
            _t1156 = _t1159
        end
        _t1153 = _t1156
    end
    return _t1153
end

function parse_assign(parser::ParserState)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1168 = parse_relation_id(parser)
    relation_id593 = _t1168
    _t1169 = parse_abstraction(parser)
    abstraction594 = _t1169
    if match_lookahead_literal(parser, "(", 0)
        _t1171 = parse_attrs(parser)
        _t1170 = _t1171
    else
        _t1170 = nothing
    end
    attrs595 = _t1170
    consume_literal!(parser, ")")
    _t1172 = Proto.Assign(name=relation_id593, body=abstraction594, attrs=(!isnothing(attrs595) ? attrs595 : Proto.Attribute[]))
    return _t1172
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1173 = parse_relation_id(parser)
    relation_id596 = _t1173
    _t1174 = parse_abstraction_with_arity(parser)
    abstraction_with_arity597 = _t1174
    if match_lookahead_literal(parser, "(", 0)
        _t1176 = parse_attrs(parser)
        _t1175 = _t1176
    else
        _t1175 = nothing
    end
    attrs598 = _t1175
    consume_literal!(parser, ")")
    _t1177 = Proto.Upsert(name=relation_id596, body=abstraction_with_arity597[1], attrs=(!isnothing(attrs598) ? attrs598 : Proto.Attribute[]), value_arity=abstraction_with_arity597[2])
    return _t1177
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1178 = parse_bindings(parser)
    bindings599 = _t1178
    _t1179 = parse_formula(parser)
    formula600 = _t1179
    consume_literal!(parser, ")")
    _t1180 = Proto.Abstraction(vars=vcat(bindings599[1], !isnothing(bindings599[2]) ? bindings599[2] : []), value=formula600)
    return (_t1180, length(bindings599[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1181 = parse_relation_id(parser)
    relation_id601 = _t1181
    _t1182 = parse_abstraction(parser)
    abstraction602 = _t1182
    if match_lookahead_literal(parser, "(", 0)
        _t1184 = parse_attrs(parser)
        _t1183 = _t1184
    else
        _t1183 = nothing
    end
    attrs603 = _t1183
    consume_literal!(parser, ")")
    _t1185 = Proto.Break(name=relation_id601, body=abstraction602, attrs=(!isnothing(attrs603) ? attrs603 : Proto.Attribute[]))
    return _t1185
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1186 = parse_monoid(parser)
    monoid604 = _t1186
    _t1187 = parse_relation_id(parser)
    relation_id605 = _t1187
    _t1188 = parse_abstraction_with_arity(parser)
    abstraction_with_arity606 = _t1188
    if match_lookahead_literal(parser, "(", 0)
        _t1190 = parse_attrs(parser)
        _t1189 = _t1190
    else
        _t1189 = nothing
    end
    attrs607 = _t1189
    consume_literal!(parser, ")")
    _t1191 = Proto.MonoidDef(monoid=monoid604, name=relation_id605, body=abstraction_with_arity606[1], attrs=(!isnothing(attrs607) ? attrs607 : Proto.Attribute[]), value_arity=abstraction_with_arity606[2])
    return _t1191
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1193 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1194 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1195 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1196 = 2
                    else
                        _t1196 = -1
                    end
                    _t1195 = _t1196
                end
                _t1194 = _t1195
            end
            _t1193 = _t1194
        end
        _t1192 = _t1193
    else
        _t1192 = -1
    end
    prediction608 = _t1192
    if prediction608 == 3
        _t1198 = parse_sum_monoid(parser)
        sum_monoid612 = _t1198
        _t1199 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid612))
        _t1197 = _t1199
    else
        if prediction608 == 2
            _t1201 = parse_max_monoid(parser)
            max_monoid611 = _t1201
            _t1202 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid611))
            _t1200 = _t1202
        else
            if prediction608 == 1
                _t1204 = parse_min_monoid(parser)
                min_monoid610 = _t1204
                _t1205 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid610))
                _t1203 = _t1205
            else
                if prediction608 == 0
                    _t1207 = parse_or_monoid(parser)
                    or_monoid609 = _t1207
                    _t1208 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid609))
                    _t1206 = _t1208
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1203 = _t1206
            end
            _t1200 = _t1203
        end
        _t1197 = _t1200
    end
    return _t1197
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1209 = Proto.OrMonoid()
    return _t1209
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1210 = parse_type(parser)
    type613 = _t1210
    consume_literal!(parser, ")")
    _t1211 = Proto.MinMonoid(var"#type"=type613)
    return _t1211
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1212 = parse_type(parser)
    type614 = _t1212
    consume_literal!(parser, ")")
    _t1213 = Proto.MaxMonoid(var"#type"=type614)
    return _t1213
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1214 = parse_type(parser)
    type615 = _t1214
    consume_literal!(parser, ")")
    _t1215 = Proto.SumMonoid(var"#type"=type615)
    return _t1215
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1216 = parse_monoid(parser)
    monoid616 = _t1216
    _t1217 = parse_relation_id(parser)
    relation_id617 = _t1217
    _t1218 = parse_abstraction_with_arity(parser)
    abstraction_with_arity618 = _t1218
    if match_lookahead_literal(parser, "(", 0)
        _t1220 = parse_attrs(parser)
        _t1219 = _t1220
    else
        _t1219 = nothing
    end
    attrs619 = _t1219
    consume_literal!(parser, ")")
    _t1221 = Proto.MonusDef(monoid=monoid616, name=relation_id617, body=abstraction_with_arity618[1], attrs=(!isnothing(attrs619) ? attrs619 : Proto.Attribute[]), value_arity=abstraction_with_arity618[2])
    return _t1221
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1222 = parse_relation_id(parser)
    relation_id620 = _t1222
    _t1223 = parse_abstraction(parser)
    abstraction621 = _t1223
    _t1224 = parse_functional_dependency_keys(parser)
    functional_dependency_keys622 = _t1224
    _t1225 = parse_functional_dependency_values(parser)
    functional_dependency_values623 = _t1225
    consume_literal!(parser, ")")
    _t1226 = Proto.FunctionalDependency(guard=abstraction621, keys=functional_dependency_keys622, values=functional_dependency_values623)
    _t1227 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1226), name=relation_id620)
    return _t1227
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs624 = Proto.Var[]
    cond625 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond625
        _t1228 = parse_var(parser)
        item626 = _t1228
        push!(xs624, item626)
        cond625 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars627 = xs624
    consume_literal!(parser, ")")
    return vars627
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs628 = Proto.Var[]
    cond629 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond629
        _t1229 = parse_var(parser)
        item630 = _t1229
        push!(xs628, item630)
        cond629 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars631 = xs628
    consume_literal!(parser, ")")
    return vars631
end

function parse_data(parser::ParserState)::Proto.Data
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "edb", 1)
            _t1231 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1232 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1233 = 1
                else
                    _t1233 = -1
                end
                _t1232 = _t1233
            end
            _t1231 = _t1232
        end
        _t1230 = _t1231
    else
        _t1230 = -1
    end
    prediction632 = _t1230
    if prediction632 == 2
        _t1235 = parse_csv_data(parser)
        csv_data635 = _t1235
        _t1236 = Proto.Data(data_type=OneOf(:csv_data, csv_data635))
        _t1234 = _t1236
    else
        if prediction632 == 1
            _t1238 = parse_betree_relation(parser)
            betree_relation634 = _t1238
            _t1239 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation634))
            _t1237 = _t1239
        else
            if prediction632 == 0
                _t1241 = parse_edb(parser)
                edb633 = _t1241
                _t1242 = Proto.Data(data_type=OneOf(:edb, edb633))
                _t1240 = _t1242
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1237 = _t1240
        end
        _t1234 = _t1237
    end
    return _t1234
end

function parse_edb(parser::ParserState)::Proto.EDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1243 = parse_relation_id(parser)
    relation_id636 = _t1243
    _t1244 = parse_edb_path(parser)
    edb_path637 = _t1244
    _t1245 = parse_edb_types(parser)
    edb_types638 = _t1245
    consume_literal!(parser, ")")
    _t1246 = Proto.EDB(target_id=relation_id636, path=edb_path637, types=edb_types638)
    return _t1246
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs639 = String[]
    cond640 = match_lookahead_terminal(parser, "STRING", 0)
    while cond640
        item641 = consume_terminal!(parser, "STRING")
        push!(xs639, item641)
        cond640 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings642 = xs639
    consume_literal!(parser, "]")
    return strings642
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs643 = Proto.var"#Type"[]
    cond644 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond644
        _t1247 = parse_type(parser)
        item645 = _t1247
        push!(xs643, item645)
        cond644 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types646 = xs643
    consume_literal!(parser, "]")
    return types646
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1248 = parse_relation_id(parser)
    relation_id647 = _t1248
    _t1249 = parse_betree_info(parser)
    betree_info648 = _t1249
    consume_literal!(parser, ")")
    _t1250 = Proto.BeTreeRelation(name=relation_id647, relation_info=betree_info648)
    return _t1250
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1251 = parse_betree_info_key_types(parser)
    betree_info_key_types649 = _t1251
    _t1252 = parse_betree_info_value_types(parser)
    betree_info_value_types650 = _t1252
    _t1253 = parse_config_dict(parser)
    config_dict651 = _t1253
    consume_literal!(parser, ")")
    _t1254 = construct_betree_info(parser, betree_info_key_types649, betree_info_value_types650, config_dict651)
    return _t1254
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs652 = Proto.var"#Type"[]
    cond653 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond653
        _t1255 = parse_type(parser)
        item654 = _t1255
        push!(xs652, item654)
        cond653 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types655 = xs652
    consume_literal!(parser, ")")
    return types655
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs656 = Proto.var"#Type"[]
    cond657 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond657
        _t1256 = parse_type(parser)
        item658 = _t1256
        push!(xs656, item658)
        cond657 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types659 = xs656
    consume_literal!(parser, ")")
    return types659
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1257 = parse_csvlocator(parser)
    csvlocator660 = _t1257
    _t1258 = parse_csv_config(parser)
    csv_config661 = _t1258
    _t1259 = parse_gnf_columns(parser)
    gnf_columns662 = _t1259
    _t1260 = parse_csv_asof(parser)
    csv_asof663 = _t1260
    consume_literal!(parser, ")")
    _t1261 = Proto.CSVData(locator=csvlocator660, config=csv_config661, columns=gnf_columns662, asof=csv_asof663)
    return _t1261
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1263 = parse_csv_locator_paths(parser)
        _t1262 = _t1263
    else
        _t1262 = nothing
    end
    csv_locator_paths664 = _t1262
    if match_lookahead_literal(parser, "(", 0)
        _t1265 = parse_csv_locator_inline_data(parser)
        _t1264 = _t1265
    else
        _t1264 = nothing
    end
    csv_locator_inline_data665 = _t1264
    consume_literal!(parser, ")")
    _t1266 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths664) ? csv_locator_paths664 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data665) ? csv_locator_inline_data665 : "")))
    return _t1266
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs666 = String[]
    cond667 = match_lookahead_terminal(parser, "STRING", 0)
    while cond667
        item668 = consume_terminal!(parser, "STRING")
        push!(xs666, item668)
        cond667 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings669 = xs666
    consume_literal!(parser, ")")
    return strings669
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string670 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string670
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1267 = parse_config_dict(parser)
    config_dict671 = _t1267
    consume_literal!(parser, ")")
    _t1268 = construct_csv_config(parser, config_dict671)
    return _t1268
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs672 = Proto.GNFColumn[]
    cond673 = match_lookahead_literal(parser, "(", 0)
    while cond673
        _t1269 = parse_gnf_column(parser)
        item674 = _t1269
        push!(xs672, item674)
        cond673 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns675 = xs672
    consume_literal!(parser, ")")
    return gnf_columns675
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1270 = parse_gnf_column_path(parser)
    gnf_column_path676 = _t1270
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1272 = parse_relation_id(parser)
        _t1271 = _t1272
    else
        _t1271 = nothing
    end
    relation_id677 = _t1271
    consume_literal!(parser, "[")
    xs678 = Proto.var"#Type"[]
    cond679 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond679
        _t1273 = parse_type(parser)
        item680 = _t1273
        push!(xs678, item680)
        cond679 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types681 = xs678
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1274 = Proto.GNFColumn(column_path=gnf_column_path676, target_id=relation_id677, types=types681)
    return _t1274
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1275 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1276 = 0
        else
            _t1276 = -1
        end
        _t1275 = _t1276
    end
    prediction682 = _t1275
    if prediction682 == 1
        consume_literal!(parser, "[")
        xs684 = String[]
        cond685 = match_lookahead_terminal(parser, "STRING", 0)
        while cond685
            item686 = consume_terminal!(parser, "STRING")
            push!(xs684, item686)
            cond685 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings687 = xs684
        consume_literal!(parser, "]")
        _t1277 = strings687
    else
        if prediction682 == 0
            string683 = consume_terminal!(parser, "STRING")
            _t1278 = String[string683]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1277 = _t1278
    end
    return _t1277
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string688 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string688
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1279 = parse_fragment_id(parser)
    fragment_id689 = _t1279
    consume_literal!(parser, ")")
    _t1280 = Proto.Undefine(fragment_id=fragment_id689)
    return _t1280
end

function parse_context(parser::ParserState)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs690 = Proto.RelationId[]
    cond691 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond691
        _t1281 = parse_relation_id(parser)
        item692 = _t1281
        push!(xs690, item692)
        cond691 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids693 = xs690
    consume_literal!(parser, ")")
    _t1282 = Proto.Context(relations=relation_ids693)
    return _t1282
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t1283 = parse_edb_path(parser)
    edb_path694 = _t1283
    _t1284 = parse_relation_id(parser)
    relation_id695 = _t1284
    consume_literal!(parser, ")")
    _t1285 = Proto.Snapshot(destination_path=edb_path694, source_relation=relation_id695)
    return _t1285
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs696 = Proto.Read[]
    cond697 = match_lookahead_literal(parser, "(", 0)
    while cond697
        _t1286 = parse_read(parser)
        item698 = _t1286
        push!(xs696, item698)
        cond697 = match_lookahead_literal(parser, "(", 0)
    end
    reads699 = xs696
    consume_literal!(parser, ")")
    return reads699
end

function parse_read(parser::ParserState)::Proto.Read
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1288 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1289 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1290 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1291 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1292 = 3
                        else
                            _t1292 = -1
                        end
                        _t1291 = _t1292
                    end
                    _t1290 = _t1291
                end
                _t1289 = _t1290
            end
            _t1288 = _t1289
        end
        _t1287 = _t1288
    else
        _t1287 = -1
    end
    prediction700 = _t1287
    if prediction700 == 4
        _t1294 = parse_export(parser)
        export705 = _t1294
        _t1295 = Proto.Read(read_type=OneOf(:var"#export", export705))
        _t1293 = _t1295
    else
        if prediction700 == 3
            _t1297 = parse_abort(parser)
            abort704 = _t1297
            _t1298 = Proto.Read(read_type=OneOf(:abort, abort704))
            _t1296 = _t1298
        else
            if prediction700 == 2
                _t1300 = parse_what_if(parser)
                what_if703 = _t1300
                _t1301 = Proto.Read(read_type=OneOf(:what_if, what_if703))
                _t1299 = _t1301
            else
                if prediction700 == 1
                    _t1303 = parse_output(parser)
                    output702 = _t1303
                    _t1304 = Proto.Read(read_type=OneOf(:output, output702))
                    _t1302 = _t1304
                else
                    if prediction700 == 0
                        _t1306 = parse_demand(parser)
                        demand701 = _t1306
                        _t1307 = Proto.Read(read_type=OneOf(:demand, demand701))
                        _t1305 = _t1307
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1302 = _t1305
                end
                _t1299 = _t1302
            end
            _t1296 = _t1299
        end
        _t1293 = _t1296
    end
    return _t1293
end

function parse_demand(parser::ParserState)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1308 = parse_relation_id(parser)
    relation_id706 = _t1308
    consume_literal!(parser, ")")
    _t1309 = Proto.Demand(relation_id=relation_id706)
    return _t1309
end

function parse_output(parser::ParserState)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1310 = parse_name(parser)
    name707 = _t1310
    _t1311 = parse_relation_id(parser)
    relation_id708 = _t1311
    consume_literal!(parser, ")")
    _t1312 = Proto.Output(name=name707, relation_id=relation_id708)
    return _t1312
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1313 = parse_name(parser)
    name709 = _t1313
    _t1314 = parse_epoch(parser)
    epoch710 = _t1314
    consume_literal!(parser, ")")
    _t1315 = Proto.WhatIf(branch=name709, epoch=epoch710)
    return _t1315
end

function parse_abort(parser::ParserState)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1317 = parse_name(parser)
        _t1316 = _t1317
    else
        _t1316 = nothing
    end
    name711 = _t1316
    _t1318 = parse_relation_id(parser)
    relation_id712 = _t1318
    consume_literal!(parser, ")")
    _t1319 = Proto.Abort(name=(!isnothing(name711) ? name711 : "abort"), relation_id=relation_id712)
    return _t1319
end

function parse_export(parser::ParserState)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1320 = parse_export_csv_config(parser)
    export_csv_config713 = _t1320
    consume_literal!(parser, ")")
    _t1321 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config713))
    return _t1321
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1322 = parse_export_csv_path(parser)
    export_csv_path714 = _t1322
    _t1323 = parse_export_csv_columns(parser)
    export_csv_columns715 = _t1323
    _t1324 = parse_config_dict(parser)
    config_dict716 = _t1324
    consume_literal!(parser, ")")
    _t1325 = export_csv_config(parser, export_csv_path714, export_csv_columns715, config_dict716)
    return _t1325
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string717 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string717
end

function parse_export_csv_columns(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs718 = Proto.ExportCSVColumn[]
    cond719 = match_lookahead_literal(parser, "(", 0)
    while cond719
        _t1326 = parse_export_csv_column(parser)
        item720 = _t1326
        push!(xs718, item720)
        cond719 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns721 = xs718
    consume_literal!(parser, ")")
    return export_csv_columns721
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string722 = consume_terminal!(parser, "STRING")
    _t1327 = parse_relation_id(parser)
    relation_id723 = _t1327
    consume_literal!(parser, ")")
    _t1328 = Proto.ExportCSVColumn(column_name=string722, column_data=relation_id723)
    return _t1328
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
