"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.

"""

using SHA
using ProtoBuf: OneOf

# Import protobuf modules
include("proto_generated.jl")
using .Proto


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


function tokenize!(lexer::Lexer)
    token_specs = [
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
        ("LITERAL", r"<", identity),
        ("LITERAL", r"=", identity),
        ("LITERAL", r">", identity),
        ("LITERAL", r"\[", identity),
        ("LITERAL", r"\]", identity),
        ("LITERAL", r"\{", identity),
        ("LITERAL", r"\|", identity),
        ("LITERAL", r"\}", identity),
        ("STRING", r"\"(?:[^\"\\]|\\.)*\"", scan_string),
        ("DECIMAL", r"[-]?\d+\.\d+d\d+", scan_decimal),
        ("FLOAT", r"(?:[-]?\d+\.\d+|inf|nan)", scan_float),
        ("INT128", r"[-]?\d+i128", scan_int128),
        ("UINT128", r"0x[0-9a-fA-F]+", scan_uint128),
        ("INT", r"[-]?\d+", scan_int),
        ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_.-]*", scan_symbol),
        ("COLON_SYMBOL", r":[a-zA-Z_][a-zA-Z0-9_.-]*", scan_colon_symbol),
    ]

    whitespace_re = r"\s+"
    comment_re = r";;.*"

    while lexer.pos <= length(lexer.input)
        # Skip whitespace
        m = match(whitespace_re, lexer.input, lexer.pos)
        if m !== nothing && m.offset == lexer.pos
            lexer.pos = m.offset + length(m.match)
            continue
        end

        # Skip comments
        m = match(comment_re, lexer.input, lexer.pos)
        if m !== nothing && m.offset == lexer.pos
            lexer.pos = m.offset + length(m.match)
            continue
        end

        # Collect all matching tokens
        candidates = Tuple{String,String,Function,Int}[]

        for (token_type, regex, action) in token_specs
            m = match(regex, lexer.input, lexer.pos)
            if m !== nothing && m.offset == lexer.pos
                value = m.match
                push!(candidates, (token_type, value, action, m.offset + length(value)))
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


# Scanner functions for each token type
scan_symbol(s::String) = s
scan_colon_symbol(s::String) = s[2:end]

function scan_string(s::String)
    # Strip quotes and process escaping
    content = s[2:end-1]
    # Simple escape processing - Julia handles most escapes natively
    result = replace(content, "\\n" => "\n")
    result = replace(result, "\\t" => "\t")
    result = replace(result, "\\r" => "\r")
    result = replace(result, "\\\\" => "\\")
    result = replace(result, "\\\"" => "\"")
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


mutable struct Parser
    tokens::Vector{Token}
    pos::Int
    id_to_debuginfo::Dict{Vector{UInt8},Dict{Tuple{UInt64,UInt64},String}}
    _current_fragment_id::Union{Nothing,Vector{UInt8}}
    _relation_id_to_name::Dict{Tuple{UInt64,UInt64},String}

    function Parser(tokens::Vector{Token})
        return new(tokens, 1, Dict(), nothing, Dict())
    end
end


function lookahead(parser::Parser, k::Int=0)::Token
    idx = parser.pos + k
    return idx <= length(parser.tokens) ? parser.tokens[idx] : Token("\$", "", -1)
end


function consume_literal!(parser::Parser, expected::String)
    if !match_lookahead_literal(parser, expected, 0)
        token = lookahead(parser, 0)
        throw(ParseError("Expected literal $(repr(expected)) but got $(token.type)=`$(repr(token.value))` at position $(token.pos)"))
    end
    parser.pos += 1
    return nothing
end


function consume_terminal!(parser::Parser, expected::String)
    if !match_lookahead_terminal(parser, expected, 0)
        token = lookahead(parser, 0)
        throw(ParseError("Expected terminal $expected but got $(token.type)=`$(repr(token.value))` at position $(token.pos)"))
    end
    token = lookahead(parser, 0)
    parser.pos += 1
    return token.value
end


function match_lookahead_literal(parser::Parser, literal::String, k::Int)::Bool
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


function match_lookahead_terminal(parser::Parser, terminal::String, k::Int)::Bool
    token = lookahead(parser, k)
    return token.type == terminal
end


function start_fragment!(parser::Parser, fragment_id::Proto.FragmentId)
    parser._current_fragment_id = fragment_id.id
    return fragment_id
end


function relation_id_from_string(parser::Parser, name::String)
    # Create RelationId from string and track mapping for debug info
    hash_bytes = sha256(name)
    val = Base.parse(UInt64, bytes2hex(hash_bytes[1:8]), base=16)
    id_low = UInt64(val & 0xFFFFFFFFFFFFFFFF)
    id_high = UInt64((val >> 64) & 0xFFFFFFFFFFFFFFFF)
    relation_id = Proto.RelationId(id_low, id_high)

    # Store the mapping for the current fragment if we're inside one
    if parser._current_fragment_id !== nothing
        if !haskey(parser.id_to_debuginfo, parser._current_fragment_id)
            parser.id_to_debuginfo[parser._current_fragment_id] = Dict()
        end
        parser.id_to_debuginfo[parser._current_fragment_id][(relation_id.id_low, relation_id.id_high)] = name
    end

    return relation_id
end


function extract_value(val::Union{Nothing,Proto.Value}, value_type::String, default::Any)
    if val === nothing
        return default
    end
    if value_type == "int"
        return hasfield(typeof(val), :int_value) ? val.int_value : default
    elseif value_type == "float"
        return hasfield(typeof(val), :float_value) ? val.float_value : default
    elseif value_type == "str"
        return hasfield(typeof(val), :string_value) ? val.string_value : default
    elseif value_type == "bool"
        return hasfield(typeof(val), :boolean_value) ? val.boolean_value : default
    elseif value_type == "uint128"
        if hasfield(typeof(val), :uint128_value)
            return val.uint128_value
        end
        return val !== nothing ? val : default
    elseif value_type == "bytes"
        if hasfield(typeof(val), :string_value)
            return Vector{UInt8}(val.string_value)
        end
        return val !== nothing ? val : default
    elseif value_type == "str_list"
        if hasfield(typeof(val), :string_value)
            return [val.string_value]
        end
        return default
    end
    return default
end


function construct_from_schema(
    parser::Parser,
    config_list::Vector{Tuple{String,Any}},
    schema::Vector{Tuple{String,String,String,Any}},
    message_constructor::Function
)
    config = Dict(config_list)
    kwargs = Dict{Symbol,Any}()
    for (config_key, proto_field, value_type, default) in schema
        val = get(config, config_key, nothing)
        kwargs[Symbol(proto_field)] = extract_value(val, value_type, default)
    end
    return message_constructor(; kwargs...)
end


function construct_configure(parser::Parser, config_dict::Vector{Tuple{String,Proto.Value}})
    config = Dict(config_dict)

    # Special handling for maintenance level enum
    maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
    maintenance_level_val = get(config, "ivm.maintenance_level", nothing)
    if maintenance_level_val !== nothing && hasfield(typeof(maintenance_level_val), :string_value)
        level_str = uppercase(maintenance_level_val.string_value)
        if level_str == "OFF"
            maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        elseif level_str == "AUTO"
            maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        elseif level_str == "ALL"
            maintenance_level = Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
        else
            # Try to use the string directly as enum name
            maintenance_level = getproperty(Proto.MaintenanceLevel, Symbol(level_str))
        end
    end

    ivm_config = Proto.IVMConfig(maintenance_level)
    semantics_version = extract_value(get(config, "semantics_version", nothing), "int", 0)
    return Proto.Configure(semantics_version, ivm_config)
end


function export_csv_config(
    parser::Parser,
    path::String,
    columns::Vector{Any},
    config_dict::Vector{Tuple{String,Proto.Value}}
)
    schema = [
        ("partition_size", "partition_size", "int", 0),
        ("compression", "compression", "str", ""),
        ("syntax_header_row", "syntax_header_row", "bool", true),
        ("syntax_missing_string", "syntax_missing_string", "str", ""),
        ("syntax_delim", "syntax_delim", "str", ","),
        ("syntax_quotechar", "syntax_quotechar", "str", "\""),
        ("syntax_escapechar", "syntax_escapechar", "str", "\\"),
    ]
    msg = construct_from_schema(parser, config_dict, schema, Proto.ExportCSVConfig)
    msg.path = path
    append!(msg.data_columns, columns)
    return msg
end


function construct_betree_info(
    parser::Parser,
    key_types::Vector{Any},
    value_types::Vector{Any},
    config_dict::Vector{Tuple{String,Any}}
)
    config_schema = [
        ("betree_config_epsilon", "epsilon", "float", 0.5),
        ("betree_config_max_pivots", "max_pivots", "int", 4),
        ("betree_config_max_deltas", "max_deltas", "int", 16),
        ("betree_config_max_leaf", "max_leaf", "int", 16),
    ]
    storage_config = construct_from_schema(parser, config_dict, config_schema, Proto.BeTreeConfig)

    locator_schema = [
        ("betree_locator_root_pageid", "root_pageid", "uint128", nothing),
        ("betree_locator_inline_data", "inline_data", "bytes", nothing),
        ("betree_locator_element_count", "element_count", "int", 0),
        ("betree_locator_tree_height", "tree_height", "int", 0),
    ]
    relation_locator = construct_from_schema(parser, config_dict, locator_schema, Proto.BeTreeLocator)

    return Proto.BeTreeInfo(
        key_types=key_types,
        value_types=value_types,
        storage_config=storage_config,
        relation_locator=relation_locator
    )
end


function construct_csv_config(parser::Parser, config_dict::Vector{Tuple{String,Any}})
    schema = [
        ("csv_header_row", "header_row", "int", 1),
        ("csv_skip", "skip", "int", 0),
        ("csv_new_line", "new_line", "str", ""),
        ("csv_delimiter", "delimiter", "str", ","),
        ("csv_quotechar", "quotechar", "str", "\""),
        ("csv_escapechar", "escapechar", "str", "\""),
        ("csv_comment", "comment", "str", ""),
        ("csv_missing_strings", "missing_strings", "str_list", String[]),
        ("csv_decimal_separator", "decimal_separator", "str", "."),
        ("csv_encoding", "encoding", "str", "utf-8"),
        ("csv_compression", "compression", "str", "auto"),
    ]
    return construct_from_schema(parser, config_dict, schema, Proto.CSVConfig)
end


function construct_fragment(
    parser::Parser,
    fragment_id::Proto.FragmentId,
    declarations::Vector{Proto.Declaration}
)
    # Get the debug info for this fragment
    debug_info_dict = get(parser.id_to_debuginfo, fragment_id.id, Dict())

    # Convert to DebugInfo protobuf
    ids = Proto.RelationId[]
    orig_names = String[]
    for ((id_low, id_high), name) in debug_info_dict
        push!(ids, Proto.RelationId(id_low, id_high))
        push!(orig_names, name)
    end

    # Create DebugInfo
    debug_info = Proto.DebugInfo(ids, orig_names)

    # Clear _current_fragment_id before the return
    parser._current_fragment_id = nothing

    # Create and return Fragment
    return Proto.Fragment(fragment_id, declarations, debug_info)
end


function parse_transaction(parser::Parser)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t320 = parse_configure(parser)
        _t319 = _t320
    else
        _t319 = nothing
    end
    configure0 = _t319
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t322 = parse_sync(parser)
        _t321 = _t322
    else
        _t321 = nothing
    end
    sync1 = _t321
    xs2 = Proto.Epoch[]
    cond3 = match_lookahead_literal(parser, "(", 0)
    while cond3
        _t323 = parse_epoch(parser)
        push!(xs2, _t323)
        cond3 = match_lookahead_literal(parser, "(", 0)
    end
    epochs4 = xs2
    consume_literal!(parser, ")")
    _t324 = Proto.Transaction(epochs4, something(configure0, construct_configure(parser, Tuple{String, Proto.Value}[])), sync1)
    return _t324
end

function parse_configure(parser::Parser)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t325 = parse_config_dict(parser)
    config_dict5 = _t325
    consume_literal!(parser, ")")
    return construct_configure(parser, config_dict5)
end

function parse_config_dict(parser::Parser)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs6 = Tuple{String, Proto.Value}[]
    cond7 = match_lookahead_terminal(parser, "COLON_SYMBOL", 0)
    while cond7
        _t326 = parse_config_key_value(parser)
        push!(xs6, _t326)
        cond7 = match_lookahead_terminal(parser, "COLON_SYMBOL", 0)
    end
    x8 = xs6
    consume_literal!(parser, "}")
    return x8
end

function parse_config_key_value(parser::Parser)::Tuple{String, Proto.Value}
    symbol9 = consume_terminal!(parser, "COLON_SYMBOL")
    _t327 = parse_value(parser)
    value10 = _t327
    return (symbol9, value10,)
end

function parse_value(parser::Parser)::Proto.Value
    if match_lookahead_literal(parser, "true", 0)
        _t328 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t329 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t330 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                        if match_lookahead_literal(parser, "date", 1)
                            _t332 = 0
                        else
                            _t332 = -1
                        end
                    _t331 = (match_lookahead_literal(parser, "datetime", 1) || _t332)
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t333 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t334 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t335 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t336 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t337 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t338 = 7
                                        else
                                            _t338 = -1
                                        end
                                        _t337 = _t338
                                    end
                                    _t336 = _t337
                                end
                                _t335 = _t336
                            end
                            _t334 = _t335
                        end
                        _t333 = _t334
                    end
                    _t331 = _t333
                end
                _t330 = _t331
            end
            _t329 = _t330
        end
        _t328 = _t329
    end
    prediction11 = _t328
    if prediction11 == 9
        _t340 = parse_boolean_value(parser)
        value20 = _t340
        _t341 = Proto.Value(OneOf(:boolean_value, value20))
        _t339 = _t341
    else
        if prediction11 == 8
            consume_literal!(parser, "missing")
            _t343 = Proto.MissingValue()
            _t344 = Proto.Value(OneOf(:missing_value, _t343))
            _t342 = _t344
        else
            if prediction11 == 7
                value19 = consume_terminal!(parser, "DECIMAL")
                _t346 = Proto.Value(OneOf(:decimal_value, value19))
                _t345 = _t346
            else
                if prediction11 == 6
                    value18 = consume_terminal!(parser, "INT128")
                    _t348 = Proto.Value(OneOf(:int128_value, value18))
                    _t347 = _t348
                else
                    if prediction11 == 5
                        value17 = consume_terminal!(parser, "UINT128")
                        _t350 = Proto.Value(OneOf(:uint128_value, value17))
                        _t349 = _t350
                    else
                        if prediction11 == 4
                            value16 = consume_terminal!(parser, "FLOAT")
                            _t352 = Proto.Value(OneOf(:float_value, value16))
                            _t351 = _t352
                        else
                            if prediction11 == 3
                                value15 = consume_terminal!(parser, "INT")
                                _t354 = Proto.Value(OneOf(:int_value, value15))
                                _t353 = _t354
                            else
                                if prediction11 == 2
                                    value14 = consume_terminal!(parser, "STRING")
                                    _t356 = Proto.Value(OneOf(:string_value, value14))
                                    _t355 = _t356
                                else
                                    if prediction11 == 1
                                        _t358 = parse_datetime(parser)
                                        value13 = _t358
                                        _t359 = Proto.Value(OneOf(:datetime_value, value13))
                                        _t357 = _t359
                                    else
                                        if prediction11 == 0
                                            _t361 = parse_date(parser)
                                            value12 = _t361
                                            _t362 = Proto.Value(OneOf(:date_value, value12))
                                            _t360 = _t362
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(current_token(parser))))
                                            _t360 = nothing
                                        end
                                        _t357 = _t360
                                    end
                                    _t355 = _t357
                                end
                                _t353 = _t355
                            end
                            _t351 = _t353
                        end
                        _t349 = _t351
                    end
                    _t347 = _t349
                end
                _t345 = _t347
            end
            _t342 = _t345
        end
        _t339 = _t342
    end
    return _t339
end

function parse_date(parser::Parser)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    year21 = consume_terminal!(parser, "INT")
    month22 = consume_terminal!(parser, "INT")
    day23 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t363 = Proto.DateValue(year21, month22, day23)
    return _t363
end

function parse_datetime(parser::Parser)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    year24 = consume_terminal!(parser, "INT")
    month25 = consume_terminal!(parser, "INT")
    day26 = consume_terminal!(parser, "INT")
    hour27 = consume_terminal!(parser, "INT")
    minute28 = consume_terminal!(parser, "INT")
    second29 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t364 = consume_terminal!(parser, "INT")
    else
        _t364 = nothing
    end
    microsecond30 = _t364
    consume_literal!(parser, ")")
    _t365 = Proto.DateTimeValue(year24, month25, day26, hour27, minute28, second29, something(microsecond30, 0))
    return _t365
end

function parse_boolean_value(parser::Parser)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t366 = 0
    else
        _t366 = (match_lookahead_literal(parser, "false", 0) || -1)
    end
    prediction31 = _t366
    if prediction31 == 1
        consume_literal!(parser, "false")
        _t367 = false
    else
        if prediction31 == 0
            consume_literal!(parser, "true")
            _t368 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(current_token(parser))))
            _t368 = nothing
        end
        _t367 = _t368
    end
    return _t367
end

function parse_sync(parser::Parser)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs32 = Proto.FragmentId[]
    cond33 = match_lookahead_terminal(parser, "COLON_SYMBOL", 0)
    while cond33
        _t369 = parse_fragment_id(parser)
        push!(xs32, _t369)
        cond33 = match_lookahead_terminal(parser, "COLON_SYMBOL", 0)
    end
    fragments34 = xs32
    consume_literal!(parser, ")")
    _t370 = Proto.Sync(fragments34)
    return _t370
end

function parse_fragment_id(parser::Parser)::Proto.FragmentId
    symbol35 = consume_terminal!(parser, "COLON_SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol35))
end

function parse_epoch(parser::Parser)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t372 = parse_epoch_writes(parser)
        _t371 = _t372
    else
        _t371 = nothing
    end
    writes36 = _t371
    if match_lookahead_literal(parser, "(", 0)
        _t374 = parse_epoch_reads(parser)
        _t373 = _t374
    else
        _t373 = nothing
    end
    reads37 = _t373
    consume_literal!(parser, ")")
    _t375 = Proto.Epoch(something(writes36, Proto.Write[]), something(reads37, Proto.Read[]))
    return _t375
end

function parse_epoch_writes(parser::Parser)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs38 = Proto.Write[]
    cond39 = match_lookahead_literal(parser, "(", 0)
    while cond39
        _t376 = parse_write(parser)
        push!(xs38, _t376)
        cond39 = match_lookahead_literal(parser, "(", 0)
    end
    x40 = xs38
    consume_literal!(parser, ")")
    return x40
end

function parse_write(parser::Parser)::Proto.Write
    if match_lookahead_literal(parser, "(", 0)
            if match_lookahead_literal(parser, "define", 1)
                _t378 = 0
            else
                if match_lookahead_literal(parser, "context", 1)
                    _t379 = 2
                else
                    _t379 = -1
                end
                _t378 = _t379
            end
        _t377 = (match_lookahead_literal(parser, "undefine", 1) || _t378)
    else
        _t377 = -1
    end
    prediction41 = _t377
    if prediction41 == 2
        _t381 = parse_context(parser)
        value44 = _t381
        _t382 = Proto.Write(OneOf(:context, value44))
        _t380 = _t382
    else
        if prediction41 == 1
            _t384 = parse_undefine(parser)
            value43 = _t384
            _t385 = Proto.Write(OneOf(:undefine, value43))
            _t383 = _t385
        else
            if prediction41 == 0
                _t387 = parse_define(parser)
                value42 = _t387
                _t388 = Proto.Write(OneOf(:define, value42))
                _t386 = _t388
            else
                throw(ParseError("Unexpected token in write" * ": " * string(current_token(parser))))
                _t386 = nothing
            end
            _t383 = _t386
        end
        _t380 = _t383
    end
    return _t380
end

function parse_define(parser::Parser)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t389 = parse_fragment(parser)
    fragment45 = _t389
    consume_literal!(parser, ")")
    _t390 = Proto.Define(fragment45)
    return _t390
end

function parse_fragment(parser::Parser)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t391 = parse_new_fragment_id(parser)
    fragment_id46 = _t391
    xs47 = Proto.Declaration[]
    cond48 = match_lookahead_literal(parser, "(", 0)
    while cond48
        _t392 = parse_declaration(parser)
        push!(xs47, _t392)
        cond48 = match_lookahead_literal(parser, "(", 0)
    end
    declarations49 = xs47
    consume_literal!(parser, ")")
    return construct_fragment(parser, fragment_id46, declarations49)
end

function parse_new_fragment_id(parser::Parser)::Proto.FragmentId
    _t393 = parse_fragment_id(parser)
    fragment_id50 = _t393
    return fragment_id50
end

function parse_declaration(parser::Parser)::Proto.Declaration
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t395 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t396 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t397 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t398 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t399 = 3
                        else
                            _t399 = (match_lookahead_literal(parser, "algorithm", 1) || -1)
                        end
                        _t398 = _t399
                    end
                    _t397 = _t398
                end
                _t396 = _t397
            end
            _t395 = _t396
        end
        _t394 = _t395
    else
        _t394 = -1
    end
    prediction51 = _t394
    if prediction51 == 3
        _t401 = parse_data(parser)
        value55 = _t401
        _t402 = Proto.Declaration(OneOf(:data, value55))
        _t400 = _t402
    else
        if prediction51 == 2
            _t404 = parse_constraint(parser)
            value54 = _t404
            _t405 = Proto.Declaration(OneOf(:constraint, value54))
            _t403 = _t405
        else
            if prediction51 == 1
                _t407 = parse_algorithm(parser)
                value53 = _t407
                _t408 = Proto.Declaration(OneOf(:algorithm, value53))
                _t406 = _t408
            else
                if prediction51 == 0
                    _t410 = parse_def(parser)
                    value52 = _t410
                    _t411 = Proto.Declaration(OneOf(:def, value52))
                    _t409 = _t411
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(current_token(parser))))
                    _t409 = nothing
                end
                _t406 = _t409
            end
            _t403 = _t406
        end
        _t400 = _t403
    end
    return _t400
end

function parse_def(parser::Parser)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t412 = parse_relation_id(parser)
    name56 = _t412
    _t413 = parse_abstraction(parser)
    body57 = _t413
    if match_lookahead_literal(parser, "(", 0)
        _t415 = parse_attrs(parser)
        _t414 = _t415
    else
        _t414 = nothing
    end
    attrs58 = _t414
    consume_literal!(parser, ")")
    _t416 = Proto.Def(name56, body57, something(attrs58, Proto.Attribute[]))
    return _t416
end

function parse_relation_id(parser::Parser)::Proto.RelationId
        if match_lookahead_terminal(parser, "COLON_SYMBOL", 0)
            _t417 = 0
        else
            _t417 = -1
        end
    prediction59 = (match_lookahead_terminal(parser, "INT", 0) || _t417)
    if prediction59 == 1
        INT61 = consume_terminal!(parser, "INT")
        _t418 = Proto.RelationId(INT61, 0)
    else
        if prediction59 == 0
            symbol60 = consume_terminal!(parser, "COLON_SYMBOL")
            _t419 = Proto.RelationId(Base.parse(UInt64, bytes2hex(sha256(symbol60)[1:8]), base=16), 0)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(current_token(parser))))
            _t419 = nothing
        end
        _t418 = _t419
    end
    return _t418
end

function parse_abstraction(parser::Parser)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t420 = parse_bindings(parser)
    bindings62 = _t420
    _t421 = parse_formula(parser)
    formula63 = _t421
    consume_literal!(parser, ")")
    _t422 = Proto.Abstraction(vcat(bindings62[1], bindings62[2]), formula63)
    return _t422
end

function parse_bindings(parser::Parser)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs64 = Proto.Binding[]
    cond65 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond65
        _t423 = parse_binding(parser)
        push!(xs64, _t423)
        cond65 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    keys66 = xs64
    if match_lookahead_literal(parser, "|", 0)
        _t425 = parse_value_bindings(parser)
        _t424 = _t425
    else
        _t424 = nothing
    end
    values67 = _t424
    consume_literal!(parser, "]")
    return (keys66, something(values67, Proto.Binding[]),)
end

function parse_binding(parser::Parser)::Proto.Binding
    symbol68 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t426 = parse_type(parser)
    type69 = _t426
    _t427 = Proto.Var(symbol68)
    _t428 = Proto.Binding(_t427, type69)
    return _t428
end

function parse_type(parser::Parser)::Proto.var"#Type"
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t429 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t430 = 4
        else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t431 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t432 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t433 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t434 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t435 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t436 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t437 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t438 = 9
                                            else
                                                _t438 = -1
                                            end
                                            _t437 = _t438
                                        end
                                        _t436 = _t437
                                    end
                                    _t435 = _t436
                                end
                                _t434 = _t435
                            end
                            _t433 = _t434
                        end
                        _t432 = _t433
                    end
                    _t431 = _t432
                end
            _t430 = (match_lookahead_literal(parser, "STRING", 0) || _t431)
        end
        _t429 = _t430
    end
    prediction70 = _t429
    if prediction70 == 10
        _t440 = parse_boolean_type(parser)
        value81 = _t440
        _t441 = Proto.var"#Type"(OneOf(:boolean_type, value81))
        _t439 = _t441
    else
        if prediction70 == 9
            _t443 = parse_decimal_type(parser)
            value80 = _t443
            _t444 = Proto.var"#Type"(OneOf(:decimal_type, value80))
            _t442 = _t444
        else
            if prediction70 == 8
                _t446 = parse_missing_type(parser)
                value79 = _t446
                _t447 = Proto.var"#Type"(OneOf(:missing_type, value79))
                _t445 = _t447
            else
                if prediction70 == 7
                    _t449 = parse_datetime_type(parser)
                    value78 = _t449
                    _t450 = Proto.var"#Type"(OneOf(:datetime_type, value78))
                    _t448 = _t450
                else
                    if prediction70 == 6
                        _t452 = parse_date_type(parser)
                        value77 = _t452
                        _t453 = Proto.var"#Type"(OneOf(:date_type, value77))
                        _t451 = _t453
                    else
                        if prediction70 == 5
                            _t455 = parse_int128_type(parser)
                            value76 = _t455
                            _t456 = Proto.var"#Type"(OneOf(:int128_type, value76))
                            _t454 = _t456
                        else
                            if prediction70 == 4
                                _t458 = parse_uint128_type(parser)
                                value75 = _t458
                                _t459 = Proto.var"#Type"(OneOf(:uint128_type, value75))
                                _t457 = _t459
                            else
                                if prediction70 == 3
                                    _t461 = parse_float_type(parser)
                                    value74 = _t461
                                    _t462 = Proto.var"#Type"(OneOf(:float_type, value74))
                                    _t460 = _t462
                                else
                                    if prediction70 == 2
                                        _t464 = parse_int_type(parser)
                                        value73 = _t464
                                        _t465 = Proto.var"#Type"(OneOf(:int_type, value73))
                                        _t463 = _t465
                                    else
                                        if prediction70 == 1
                                            _t467 = parse_string_type(parser)
                                            value72 = _t467
                                            _t468 = Proto.var"#Type"(OneOf(:string_type, value72))
                                            _t466 = _t468
                                        else
                                            if prediction70 == 0
                                                _t470 = parse_unspecified_type(parser)
                                                value71 = _t470
                                                _t471 = Proto.var"#Type"(OneOf(:unspecified_type, value71))
                                                _t469 = _t471
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(current_token(parser))))
                                                _t469 = nothing
                                            end
                                            _t466 = _t469
                                        end
                                        _t463 = _t466
                                    end
                                    _t460 = _t463
                                end
                                _t457 = _t460
                            end
                            _t454 = _t457
                        end
                        _t451 = _t454
                    end
                    _t448 = _t451
                end
                _t445 = _t448
            end
            _t442 = _t445
        end
        _t439 = _t442
    end
    return _t439
end

function parse_unspecified_type(parser::Parser)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t472 = Proto.UnspecifiedType()
    return _t472
end

function parse_string_type(parser::Parser)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t473 = Proto.StringType()
    return _t473
end

function parse_int_type(parser::Parser)::Proto.IntType
    consume_literal!(parser, "INT")
    _t474 = Proto.IntType()
    return _t474
end

function parse_float_type(parser::Parser)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t475 = Proto.FloatType()
    return _t475
end

function parse_uint128_type(parser::Parser)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t476 = Proto.UInt128Type()
    return _t476
end

function parse_int128_type(parser::Parser)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t477 = Proto.Int128Type()
    return _t477
end

function parse_date_type(parser::Parser)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t478 = Proto.DateType()
    return _t478
end

function parse_datetime_type(parser::Parser)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t479 = Proto.DateTimeType()
    return _t479
end

function parse_missing_type(parser::Parser)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t480 = Proto.MissingType()
    return _t480
end

function parse_decimal_type(parser::Parser)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    precision82 = consume_terminal!(parser, "INT")
    scale83 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t481 = Proto.DecimalType(precision82, scale83)
    return _t481
end

function parse_boolean_type(parser::Parser)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t482 = Proto.BooleanType()
    return _t482
end

function parse_value_bindings(parser::Parser)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs84 = Proto.Binding[]
    cond85 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond85
        _t483 = parse_binding(parser)
        push!(xs84, _t483)
        cond85 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    x86 = xs84
    return x86
end

function parse_formula(parser::Parser)::Proto.Formula
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t485 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t486 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t487 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t488 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t489 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t490 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t491 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t492 = 7
                                    else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t493 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t494 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t495 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t496 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t497 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t498 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t499 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t500 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t501 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t502 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t503 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t504 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t505 = 10
                                                                                            else
                                                                                                _t505 = -1
                                                                                            end
                                                                                            _t504 = _t505
                                                                                        end
                                                                                        _t503 = _t504
                                                                                    end
                                                                                    _t502 = _t503
                                                                                end
                                                                                _t501 = _t502
                                                                            end
                                                                            _t500 = _t501
                                                                        end
                                                                        _t499 = _t500
                                                                    end
                                                                    _t498 = _t499
                                                                end
                                                                _t497 = _t498
                                                            end
                                                            _t496 = _t497
                                                        end
                                                        _t495 = _t496
                                                    end
                                                    _t494 = _t495
                                                end
                                                _t493 = _t494
                                            end
                                        _t492 = (match_lookahead_literal(parser, "false", 1) || _t493)
                                    end
                                    _t491 = _t492
                                end
                                _t490 = _t491
                            end
                            _t489 = _t490
                        end
                        _t488 = _t489
                    end
                    _t487 = _t488
                end
                _t486 = _t487
            end
            _t485 = _t486
        end
        _t484 = _t485
    else
        _t484 = -1
    end
    prediction87 = _t484
    if prediction87 == 12
        _t507 = parse_cast(parser)
        value100 = _t507
        _t508 = Proto.Formula(OneOf(:cast, value100))
        _t506 = _t508
    else
        if prediction87 == 11
            _t510 = parse_rel_atom(parser)
            value99 = _t510
            _t511 = Proto.Formula(OneOf(:rel_atom, value99))
            _t509 = _t511
        else
            if prediction87 == 10
                _t513 = parse_primitive(parser)
                value98 = _t513
                _t514 = Proto.Formula(OneOf(:primitive, value98))
                _t512 = _t514
            else
                if prediction87 == 9
                    _t516 = parse_pragma(parser)
                    value97 = _t516
                    _t517 = Proto.Formula(OneOf(:pragma, value97))
                    _t515 = _t517
                else
                    if prediction87 == 8
                        _t519 = parse_atom(parser)
                        value96 = _t519
                        _t520 = Proto.Formula(OneOf(:atom, value96))
                        _t518 = _t520
                    else
                        if prediction87 == 7
                            _t522 = parse_ffi(parser)
                            value95 = _t522
                            _t523 = Proto.Formula(OneOf(:ffi, value95))
                            _t521 = _t523
                        else
                            if prediction87 == 6
                                _t525 = parse_not(parser)
                                value94 = _t525
                                _t526 = Proto.Formula(OneOf(:not, value94))
                                _t524 = _t526
                            else
                                if prediction87 == 5
                                    _t528 = parse_disjunction(parser)
                                    value93 = _t528
                                    _t529 = Proto.Formula(OneOf(:disjunction, value93))
                                    _t527 = _t529
                                else
                                    if prediction87 == 4
                                        _t531 = parse_conjunction(parser)
                                        value92 = _t531
                                        _t532 = Proto.Formula(OneOf(:conjunction, value92))
                                        _t530 = _t532
                                    else
                                        if prediction87 == 3
                                            _t534 = parse_reduce(parser)
                                            value91 = _t534
                                            _t535 = Proto.Formula(OneOf(:reduce, value91))
                                            _t533 = _t535
                                        else
                                            if prediction87 == 2
                                                _t537 = parse_exists(parser)
                                                value90 = _t537
                                                _t538 = Proto.Formula(OneOf(:exists, value90))
                                                _t536 = _t538
                                            else
                                                if prediction87 == 1
                                                    _t540 = parse_false(parser)
                                                    value89 = _t540
                                                    _t541 = Proto.Formula(OneOf(:disjunction, value89))
                                                    _t539 = _t541
                                                else
                                                    if prediction87 == 0
                                                        _t543 = parse_true(parser)
                                                        value88 = _t543
                                                        _t544 = Proto.Formula(OneOf(:conjunction, value88))
                                                        _t542 = _t544
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(current_token(parser))))
                                                        _t542 = nothing
                                                    end
                                                    _t539 = _t542
                                                end
                                                _t536 = _t539
                                            end
                                            _t533 = _t536
                                        end
                                        _t530 = _t533
                                    end
                                    _t527 = _t530
                                end
                                _t524 = _t527
                            end
                            _t521 = _t524
                        end
                        _t518 = _t521
                    end
                    _t515 = _t518
                end
                _t512 = _t515
            end
            _t509 = _t512
        end
        _t506 = _t509
    end
    return _t506
end

function parse_true(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t545 = Proto.Conjunction(Proto.Formula[])
    return _t545
end

function parse_false(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t546 = Proto.Disjunction(Proto.Formula[])
    return _t546
end

function parse_exists(parser::Parser)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t547 = parse_bindings(parser)
    bindings101 = _t547
    _t548 = parse_formula(parser)
    formula102 = _t548
    consume_literal!(parser, ")")
    _t549 = Proto.Abstraction(vcat(bindings101[1], bindings101[2]), formula102)
    _t550 = Proto.Exists(_t549)
    return _t550
end

function parse_reduce(parser::Parser)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t551 = parse_abstraction(parser)
    op103 = _t551
    _t552 = parse_abstraction(parser)
    body104 = _t552
    _t553 = parse_terms(parser)
    terms105 = _t553
    consume_literal!(parser, ")")
    _t554 = Proto.Reduce(op103, body104, terms105)
    return _t554
end

function parse_terms(parser::Parser)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs106 = Proto.Term[]
    cond107 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond107
        _t555 = parse_term(parser)
        push!(xs106, _t555)
        cond107 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    x108 = xs106
    consume_literal!(parser, ")")
    return x108
end

function parse_term(parser::Parser)::Proto.Term
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t556 = 0
                        else
                            _t556 = (match_lookahead_terminal(parser, "STRING", 0) || (match_lookahead_terminal(parser, "INT128", 0) || (match_lookahead_terminal(parser, "INT", 0) || (match_lookahead_terminal(parser, "FLOAT", 0) || (match_lookahead_terminal(parser, "DECIMAL", 0) || -1)))))
                        end
    prediction109 = (match_lookahead_literal(parser, "true", 0) || (match_lookahead_literal(parser, "missing", 0) || (match_lookahead_literal(parser, "false", 0) || (match_lookahead_literal(parser, "(", 0) || (match_lookahead_terminal(parser, "UINT128", 0) || _t556)))))
    if prediction109 == 1
        _t558 = parse_constant(parser)
        value111 = _t558
        _t559 = Proto.Term(OneOf(:constant, value111))
        _t557 = _t559
    else
        if prediction109 == 0
            _t561 = parse_var(parser)
            value110 = _t561
            _t562 = Proto.Term(OneOf(:var, value110))
            _t560 = _t562
        else
            throw(ParseError("Unexpected token in term" * ": " * string(current_token(parser))))
            _t560 = nothing
        end
        _t557 = _t560
    end
    return _t557
end

function parse_var(parser::Parser)::Proto.Var
    symbol112 = consume_terminal!(parser, "SYMBOL")
    _t563 = Proto.Var(symbol112)
    return _t563
end

function parse_constant(parser::Parser)::Proto.Value
    _t564 = parse_value(parser)
    x113 = _t564
    return x113
end

function parse_conjunction(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs114 = Proto.Formula[]
    cond115 = match_lookahead_literal(parser, "(", 0)
    while cond115
        _t565 = parse_formula(parser)
        push!(xs114, _t565)
        cond115 = match_lookahead_literal(parser, "(", 0)
    end
    args116 = xs114
    consume_literal!(parser, ")")
    _t566 = Proto.Conjunction(args116)
    return _t566
end

function parse_disjunction(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs117 = Proto.Formula[]
    cond118 = match_lookahead_literal(parser, "(", 0)
    while cond118
        _t567 = parse_formula(parser)
        push!(xs117, _t567)
        cond118 = match_lookahead_literal(parser, "(", 0)
    end
    args119 = xs117
    consume_literal!(parser, ")")
    _t568 = Proto.Disjunction(args119)
    return _t568
end

function parse_not(parser::Parser)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t569 = parse_formula(parser)
    arg120 = _t569
    consume_literal!(parser, ")")
    _t570 = Proto.Not(arg120)
    return _t570
end

function parse_ffi(parser::Parser)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t571 = parse_name(parser)
    name121 = _t571
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "args", 1))
        _t573 = parse_ffi_args(parser)
        _t572 = _t573
    else
        _t572 = nothing
    end
    args122 = _t572
    if match_lookahead_literal(parser, "(", 0)
        _t575 = parse_terms(parser)
        _t574 = _t575
    else
        _t574 = nothing
    end
    terms123 = _t574
    consume_literal!(parser, ")")
    _t576 = Proto.FFI(name121, something(args122, Proto.Abstraction[]), something(terms123, Proto.Term[]))
    return _t576
end

function parse_name(parser::Parser)::String
    x124 = consume_terminal!(parser, "COLON_SYMBOL")
    return x124
end

function parse_ffi_args(parser::Parser)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs125 = Proto.Abstraction[]
    cond126 = match_lookahead_literal(parser, "(", 0)
    while cond126
        _t577 = parse_abstraction(parser)
        push!(xs125, _t577)
        cond126 = match_lookahead_literal(parser, "(", 0)
    end
    x127 = xs125
    consume_literal!(parser, ")")
    return x127
end

function parse_atom(parser::Parser)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t578 = parse_relation_id(parser)
    name128 = _t578
    xs129 = Proto.Term[]
    cond130 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond130
        _t579 = parse_term(parser)
        push!(xs129, _t579)
        cond130 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms131 = xs129
    consume_literal!(parser, ")")
    _t580 = Proto.Atom(name128, terms131)
    return _t580
end

function parse_pragma(parser::Parser)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t581 = parse_name(parser)
    name132 = _t581
    xs133 = Proto.Term[]
    cond134 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond134
        _t582 = parse_term(parser)
        push!(xs133, _t582)
        cond134 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms135 = xs133
    consume_literal!(parser, ")")
    _t583 = Proto.Pragma(name132, terms135)
    return _t583
end

function parse_primitive(parser::Parser)::Proto.Primitive
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t585 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t586 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t587 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t588 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t589 = 2
                        else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t590 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t591 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t592 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t593 = 7
                                            else
                                                _t593 = -1
                                            end
                                            _t592 = _t593
                                        end
                                        _t591 = _t592
                                    end
                                    _t590 = _t591
                                end
                            _t589 = (match_lookahead_literal(parser, "<", 1) || _t590)
                        end
                        _t588 = _t589
                    end
                    _t587 = _t588
                end
                _t586 = _t587
            end
            _t585 = _t586
        end
        _t584 = _t585
    else
        _t584 = -1
    end
    prediction136 = _t584
    if prediction136 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t595 = parse_name(parser)
        name146 = _t595
        xs147 = Proto.RelTerm[]
        cond148 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond148
            _t596 = parse_rel_term(parser)
            push!(xs147, _t596)
            cond148 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        terms149 = xs147
        consume_literal!(parser, ")")
        _t597 = Proto.Primitive(name146, terms149)
        _t594 = _t597
    else
        if prediction136 == 8
            _t599 = parse_divide(parser)
            op145 = _t599
            _t598 = op145
        else
            if prediction136 == 7
                _t601 = parse_multiply(parser)
                op144 = _t601
                _t600 = op144
            else
                if prediction136 == 6
                    _t603 = parse_minus(parser)
                    op143 = _t603
                    _t602 = op143
                else
                    if prediction136 == 5
                        _t605 = parse_add(parser)
                        op142 = _t605
                        _t604 = op142
                    else
                        if prediction136 == 4
                            _t607 = parse_gt_eq(parser)
                            op141 = _t607
                            _t606 = op141
                        else
                            if prediction136 == 3
                                _t609 = parse_gt(parser)
                                op140 = _t609
                                _t608 = op140
                            else
                                if prediction136 == 2
                                    _t611 = parse_lt_eq(parser)
                                    op139 = _t611
                                    _t610 = op139
                                else
                                    if prediction136 == 1
                                        _t613 = parse_lt(parser)
                                        op138 = _t613
                                        _t612 = op138
                                    else
                                        if prediction136 == 0
                                            _t615 = parse_eq(parser)
                                            op137 = _t615
                                            _t614 = op137
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(current_token(parser))))
                                            _t614 = nothing
                                        end
                                        _t612 = _t614
                                    end
                                    _t610 = _t612
                                end
                                _t608 = _t610
                            end
                            _t606 = _t608
                        end
                        _t604 = _t606
                    end
                    _t602 = _t604
                end
                _t600 = _t602
            end
            _t598 = _t600
        end
        _t594 = _t598
    end
    return _t594
end

function parse_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t616 = parse_term(parser)
    left150 = _t616
    _t617 = parse_term(parser)
    right151 = _t617
    consume_literal!(parser, ")")
    _t618 = Proto.RelTerm(OneOf(:term, left150))
    _t619 = Proto.RelTerm(OneOf(:term, right151))
    _t620 = Proto.Primitive("rel_primitive_eq", [_t618, _t619])
    return _t620
end

function parse_lt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t621 = parse_term(parser)
    left152 = _t621
    _t622 = parse_term(parser)
    right153 = _t622
    consume_literal!(parser, ")")
    _t623 = Proto.RelTerm(OneOf(:term, left152))
    _t624 = Proto.RelTerm(OneOf(:term, right153))
    _t625 = Proto.Primitive("rel_primitive_lt_monotype", [_t623, _t624])
    return _t625
end

function parse_lt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t626 = parse_term(parser)
    left154 = _t626
    _t627 = parse_term(parser)
    right155 = _t627
    consume_literal!(parser, ")")
    _t628 = Proto.RelTerm(OneOf(:term, left154))
    _t629 = Proto.RelTerm(OneOf(:term, right155))
    _t630 = Proto.Primitive("rel_primitive_lt_eq_monotype", [_t628, _t629])
    return _t630
end

function parse_gt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t631 = parse_term(parser)
    left156 = _t631
    _t632 = parse_term(parser)
    right157 = _t632
    consume_literal!(parser, ")")
    _t633 = Proto.RelTerm(OneOf(:term, left156))
    _t634 = Proto.RelTerm(OneOf(:term, right157))
    _t635 = Proto.Primitive("rel_primitive_gt_monotype", [_t633, _t634])
    return _t635
end

function parse_gt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t636 = parse_term(parser)
    left158 = _t636
    _t637 = parse_term(parser)
    right159 = _t637
    consume_literal!(parser, ")")
    _t638 = Proto.RelTerm(OneOf(:term, left158))
    _t639 = Proto.RelTerm(OneOf(:term, right159))
    _t640 = Proto.Primitive("rel_primitive_gt_eq_monotype", [_t638, _t639])
    return _t640
end

function parse_add(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t641 = parse_term(parser)
    left160 = _t641
    _t642 = parse_term(parser)
    right161 = _t642
    _t643 = parse_term(parser)
    result162 = _t643
    consume_literal!(parser, ")")
    _t644 = Proto.RelTerm(OneOf(:term, left160))
    _t645 = Proto.RelTerm(OneOf(:term, right161))
    _t646 = Proto.RelTerm(OneOf(:term, result162))
    _t647 = Proto.Primitive("rel_primitive_add_monotype", [_t644, _t645, _t646])
    return _t647
end

function parse_minus(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t648 = parse_term(parser)
    left163 = _t648
    _t649 = parse_term(parser)
    right164 = _t649
    _t650 = parse_term(parser)
    result165 = _t650
    consume_literal!(parser, ")")
    _t651 = Proto.RelTerm(OneOf(:term, left163))
    _t652 = Proto.RelTerm(OneOf(:term, right164))
    _t653 = Proto.RelTerm(OneOf(:term, result165))
    _t654 = Proto.Primitive("rel_primitive_subtract_monotype", [_t651, _t652, _t653])
    return _t654
end

function parse_multiply(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t655 = parse_term(parser)
    left166 = _t655
    _t656 = parse_term(parser)
    right167 = _t656
    _t657 = parse_term(parser)
    result168 = _t657
    consume_literal!(parser, ")")
    _t658 = Proto.RelTerm(OneOf(:term, left166))
    _t659 = Proto.RelTerm(OneOf(:term, right167))
    _t660 = Proto.RelTerm(OneOf(:term, result168))
    _t661 = Proto.Primitive("rel_primitive_multiply_monotype", [_t658, _t659, _t660])
    return _t661
end

function parse_divide(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t662 = parse_term(parser)
    left169 = _t662
    _t663 = parse_term(parser)
    right170 = _t663
    _t664 = parse_term(parser)
    result171 = _t664
    consume_literal!(parser, ")")
    _t665 = Proto.RelTerm(OneOf(:term, left169))
    _t666 = Proto.RelTerm(OneOf(:term, right170))
    _t667 = Proto.RelTerm(OneOf(:term, result171))
    _t668 = Proto.Primitive("rel_primitive_divide_monotype", [_t665, _t666, _t667])
    return _t668
end

function parse_rel_term(parser::Parser)::Proto.RelTerm
                    if match_lookahead_literal(parser, "#", 0)
                        _t669 = 0
                    else
                        _t669 = (match_lookahead_terminal(parser, "UINT128", 0) || (match_lookahead_terminal(parser, "SYMBOL", 0) || (match_lookahead_terminal(parser, "STRING", 0) || (match_lookahead_terminal(parser, "INT128", 0) || (match_lookahead_terminal(parser, "INT", 0) || (match_lookahead_terminal(parser, "FLOAT", 0) || (match_lookahead_terminal(parser, "DECIMAL", 0) || -1)))))))
                    end
    prediction172 = (match_lookahead_literal(parser, "true", 0) || (match_lookahead_literal(parser, "missing", 0) || (match_lookahead_literal(parser, "false", 0) || (match_lookahead_literal(parser, "(", 0) || _t669))))
    if prediction172 == 1
        _t671 = parse_term(parser)
        value174 = _t671
        _t672 = Proto.RelTerm(OneOf(:term, value174))
        _t670 = _t672
    else
        if prediction172 == 0
            _t674 = parse_specialized_value(parser)
            value173 = _t674
            _t675 = Proto.RelTerm(OneOf(:specialized_value, value173))
            _t673 = _t675
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(current_token(parser))))
            _t673 = nothing
        end
        _t670 = _t673
    end
    return _t670
end

function parse_specialized_value(parser::Parser)::Proto.Value
    consume_literal!(parser, "#")
    _t676 = parse_value(parser)
    value175 = _t676
    return value175
end

function parse_rel_atom(parser::Parser)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t677 = parse_name(parser)
    name176 = _t677
    xs177 = Proto.RelTerm[]
    cond178 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond178
        _t678 = parse_rel_term(parser)
        push!(xs177, _t678)
        cond178 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms179 = xs177
    consume_literal!(parser, ")")
    _t679 = Proto.RelAtom(name176, terms179)
    return _t679
end

function parse_cast(parser::Parser)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t680 = parse_term(parser)
    input180 = _t680
    _t681 = parse_term(parser)
    result181 = _t681
    consume_literal!(parser, ")")
    _t682 = Proto.Cast(input180, result181)
    return _t682
end

function parse_attrs(parser::Parser)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs182 = Proto.Attribute[]
    cond183 = match_lookahead_literal(parser, "(", 0)
    while cond183
        _t683 = parse_attribute(parser)
        push!(xs182, _t683)
        cond183 = match_lookahead_literal(parser, "(", 0)
    end
    x184 = xs182
    consume_literal!(parser, ")")
    return x184
end

function parse_attribute(parser::Parser)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t684 = parse_name(parser)
    name185 = _t684
    xs186 = Proto.Value[]
    cond187 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond187
        _t685 = parse_value(parser)
        push!(xs186, _t685)
        cond187 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    args188 = xs186
    consume_literal!(parser, ")")
    _t686 = Proto.Attribute(name185, args188)
    return _t686
end

function parse_algorithm(parser::Parser)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs189 = Proto.RelationId[]
    cond190 = (match_lookahead_terminal(parser, "COLON_SYMBOL", 0) || match_lookahead_terminal(parser, "INT", 0))
    while cond190
        _t687 = parse_relation_id(parser)
        push!(xs189, _t687)
        cond190 = (match_lookahead_terminal(parser, "COLON_SYMBOL", 0) || match_lookahead_terminal(parser, "INT", 0))
    end
    global191 = xs189
    _t688 = parse_script(parser)
    body192 = _t688
    consume_literal!(parser, ")")
    _t689 = Proto.Algorithm(global191, body192)
    return _t689
end

function parse_script(parser::Parser)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs193 = Proto.Construct[]
    cond194 = match_lookahead_literal(parser, "(", 0)
    while cond194
        _t690 = parse_construct(parser)
        push!(xs193, _t690)
        cond194 = match_lookahead_literal(parser, "(", 0)
    end
    constructs195 = xs193
    consume_literal!(parser, ")")
    _t691 = Proto.Script(constructs195)
    return _t691
end

function parse_construct(parser::Parser)::Proto.Construct
    if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "loop", 1)
                        _t693 = 0
                    else
                        _t693 = (match_lookahead_literal(parser, "break", 1) || (match_lookahead_literal(parser, "assign", 1) || -1))
                    end
        _t692 = (match_lookahead_literal(parser, "upsert", 1) || (match_lookahead_literal(parser, "monus", 1) || (match_lookahead_literal(parser, "monoid", 1) || _t693)))
    else
        _t692 = -1
    end
    prediction196 = _t692
    if prediction196 == 1
        _t695 = parse_instruction(parser)
        value198 = _t695
        _t696 = Proto.Construct(OneOf(:instruction, value198))
        _t694 = _t696
    else
        if prediction196 == 0
            _t698 = parse_loop(parser)
            value197 = _t698
            _t699 = Proto.Construct(OneOf(:loop, value197))
            _t697 = _t699
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(current_token(parser))))
            _t697 = nothing
        end
        _t694 = _t697
    end
    return _t694
end

function parse_loop(parser::Parser)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "init", 1))
        _t701 = parse_loop_init(parser)
        _t700 = _t701
    else
        _t700 = nothing
    end
    init199 = _t700
    _t702 = parse_script(parser)
    body200 = _t702
    consume_literal!(parser, ")")
    _t703 = Proto.Loop(something(init199, Proto.Instruction[]), body200)
    return _t703
end

function parse_loop_init(parser::Parser)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs201 = Proto.Instruction[]
    cond202 = match_lookahead_literal(parser, "(", 0)
    while cond202
        _t704 = parse_instruction(parser)
        push!(xs201, _t704)
        cond202 = match_lookahead_literal(parser, "(", 0)
    end
    x203 = xs201
    consume_literal!(parser, ")")
    return x203
end

function parse_instruction(parser::Parser)::Proto.Instruction
    if match_lookahead_literal(parser, "(", 0)
            if match_lookahead_literal(parser, "monus", 1)
                _t706 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t707 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t708 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t709 = 0
                        else
                            _t709 = -1
                        end
                        _t708 = _t709
                    end
                    _t707 = _t708
                end
                _t706 = _t707
            end
        _t705 = (match_lookahead_literal(parser, "upsert", 1) || _t706)
    else
        _t705 = -1
    end
    prediction204 = _t705
    if prediction204 == 4
        _t711 = parse_monus_def(parser)
        value209 = _t711
        _t712 = Proto.Instruction(OneOf(:monus_def, value209))
        _t710 = _t712
    else
        if prediction204 == 3
            _t714 = parse_monoid_def(parser)
            value208 = _t714
            _t715 = Proto.Instruction(OneOf(:monoid_def, value208))
            _t713 = _t715
        else
            if prediction204 == 2
                _t717 = parse_break(parser)
                value207 = _t717
                _t718 = Proto.Instruction(OneOf(:break, value207))
                _t716 = _t718
            else
                if prediction204 == 1
                    _t720 = parse_upsert(parser)
                    value206 = _t720
                    _t721 = Proto.Instruction(OneOf(:upsert, value206))
                    _t719 = _t721
                else
                    if prediction204 == 0
                        _t723 = parse_assign(parser)
                        value205 = _t723
                        _t724 = Proto.Instruction(OneOf(:assign, value205))
                        _t722 = _t724
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(current_token(parser))))
                        _t722 = nothing
                    end
                    _t719 = _t722
                end
                _t716 = _t719
            end
            _t713 = _t716
        end
        _t710 = _t713
    end
    return _t710
end

function parse_assign(parser::Parser)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t725 = parse_relation_id(parser)
    name210 = _t725
    _t726 = parse_abstraction(parser)
    body211 = _t726
    if match_lookahead_literal(parser, "(", 0)
        _t728 = parse_attrs(parser)
        _t727 = _t728
    else
        _t727 = nothing
    end
    attrs212 = _t727
    consume_literal!(parser, ")")
    _t729 = Proto.Assign(name210, body211, something(attrs212, Proto.Attribute[]))
    return _t729
end

function parse_upsert(parser::Parser)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t730 = parse_relation_id(parser)
    name213 = _t730
    _t731 = parse_abstraction_with_arity(parser)
    abstraction_with_arity214 = _t731
    if match_lookahead_literal(parser, "(", 0)
        _t733 = parse_attrs(parser)
        _t732 = _t733
    else
        _t732 = nothing
    end
    attrs215 = _t732
    consume_literal!(parser, ")")
    _t734 = parser.get_tuple_element(abstraction_with_arity214, 0)
    abstraction = _t734
    _t735 = parser.get_tuple_element(abstraction_with_arity214, 1)
    arity = _t735
    _t736 = Proto.Upsert(name213, abstraction, something(attrs215, Proto.Attribute[]), arity)
    return _t736
end

function parse_abstraction_with_arity(parser::Parser)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t737 = parse_bindings(parser)
    bindings216 = _t737
    _t738 = parse_formula(parser)
    formula217 = _t738
    consume_literal!(parser, ")")
    _t739 = Proto.Abstraction(vcat(bindings216[1], bindings216[2]), formula217)
    return (_t739, length(bindings216[2]),)
end

function parse_break(parser::Parser)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t740 = parse_relation_id(parser)
    name218 = _t740
    _t741 = parse_abstraction(parser)
    body219 = _t741
    if match_lookahead_literal(parser, "(", 0)
        _t743 = parse_attrs(parser)
        _t742 = _t743
    else
        _t742 = nothing
    end
    attrs220 = _t742
    consume_literal!(parser, ")")
    _t744 = Proto.Break(name218, body219, something(attrs220, Proto.Attribute[]))
    return _t744
end

function parse_monoid_def(parser::Parser)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t745 = parse_monoid(parser)
    monoid221 = _t745
    _t746 = parse_relation_id(parser)
    name222 = _t746
    _t747 = parse_abstraction_with_arity(parser)
    abstraction_with_arity223 = _t747
    if match_lookahead_literal(parser, "(", 0)
        _t749 = parse_attrs(parser)
        _t748 = _t749
    else
        _t748 = nothing
    end
    attrs224 = _t748
    consume_literal!(parser, ")")
    _t750 = parser.get_tuple_element(abstraction_with_arity223, 0)
    abstraction = _t750
    _t751 = parser.get_tuple_element(abstraction_with_arity223, 1)
    arity = _t751
    _t752 = Proto.MonoidDef(monoid221, name222, abstraction, something(attrs224, Proto.Attribute[]), arity)
    return _t752
end

function parse_monoid(parser::Parser)::Proto.Monoid
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t754 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t755 = 0
            else
                    if match_lookahead_literal(parser, "max", 1)
                        _t756 = 2
                    else
                        _t756 = -1
                    end
                _t755 = (match_lookahead_literal(parser, "min", 1) || _t756)
            end
            _t754 = _t755
        end
        _t753 = _t754
    else
        _t753 = -1
    end
    prediction225 = _t753
    if prediction225 == 3
        _t758 = parse_sum_monoid(parser)
        value229 = _t758
        _t759 = Proto.Monoid(OneOf(:sum_monoid, value229))
        _t757 = _t759
    else
        if prediction225 == 2
            _t761 = parse_max_monoid(parser)
            value228 = _t761
            _t762 = Proto.Monoid(OneOf(:max_monoid, value228))
            _t760 = _t762
        else
            if prediction225 == 1
                _t764 = parse_min_monoid(parser)
                value227 = _t764
                _t765 = Proto.Monoid(OneOf(:min_monoid, value227))
                _t763 = _t765
            else
                if prediction225 == 0
                    _t767 = parse_or_monoid(parser)
                    value226 = _t767
                    _t768 = Proto.Monoid(OneOf(:or_monoid, value226))
                    _t766 = _t768
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(current_token(parser))))
                    _t766 = nothing
                end
                _t763 = _t766
            end
            _t760 = _t763
        end
        _t757 = _t760
    end
    return _t757
end

function parse_or_monoid(parser::Parser)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t769 = Proto.OrMonoid()
    return _t769
end

function parse_min_monoid(parser::Parser)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t770 = parse_type(parser)
    type230 = _t770
    consume_literal!(parser, ")")
    _t771 = Proto.MinMonoid(type230)
    return _t771
end

function parse_max_monoid(parser::Parser)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t772 = parse_type(parser)
    type231 = _t772
    consume_literal!(parser, ")")
    _t773 = Proto.MaxMonoid(type231)
    return _t773
end

function parse_sum_monoid(parser::Parser)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t774 = parse_type(parser)
    type232 = _t774
    consume_literal!(parser, ")")
    _t775 = Proto.SumMonoid(type232)
    return _t775
end

function parse_monus_def(parser::Parser)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t776 = parse_monoid(parser)
    monoid233 = _t776
    _t777 = parse_relation_id(parser)
    name234 = _t777
    _t778 = parse_abstraction_with_arity(parser)
    abstraction_with_arity235 = _t778
    if match_lookahead_literal(parser, "(", 0)
        _t780 = parse_attrs(parser)
        _t779 = _t780
    else
        _t779 = nothing
    end
    attrs236 = _t779
    consume_literal!(parser, ")")
    _t781 = parser.get_tuple_element(abstraction_with_arity235, 0)
    abstraction = _t781
    _t782 = parser.get_tuple_element(abstraction_with_arity235, 1)
    arity = _t782
    _t783 = Proto.MonusDef(monoid233, name234, abstraction, something(attrs236, Proto.Attribute[]), arity)
    return _t783
end

function parse_constraint(parser::Parser)::Proto.Constraint
    _t784 = parse_functional_dependency(parser)
    value237 = _t784
    _t785 = Proto.Constraint(OneOf(:functional_dependency, value237))
    return _t785
end

function parse_functional_dependency(parser::Parser)::Proto.FunctionalDependency
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t786 = parse_abstraction(parser)
    guard238 = _t786
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "keys", 1))
        _t788 = parse_functional_dependency_keys(parser)
        _t787 = _t788
    else
        _t787 = nothing
    end
    keys239 = _t787
    if match_lookahead_literal(parser, "(", 0)
        _t790 = parse_functional_dependency_values(parser)
        _t789 = _t790
    else
        _t789 = nothing
    end
    values240 = _t789
    consume_literal!(parser, ")")
    _t791 = Proto.FunctionalDependency(guard238, something(keys239, Proto.Var[]), something(values240, Proto.Var[]))
    return _t791
end

function parse_functional_dependency_keys(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs241 = Proto.Var[]
    cond242 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond242
        _t792 = parse_var(parser)
        push!(xs241, _t792)
        cond242 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    x243 = xs241
    consume_literal!(parser, ")")
    return x243
end

function parse_functional_dependency_values(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs244 = Proto.Var[]
    cond245 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond245
        _t793 = parse_var(parser)
        push!(xs244, _t793)
        cond245 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    x246 = xs244
    consume_literal!(parser, ")")
    return x246
end

function parse_data(parser::Parser)::Proto.Data
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t795 = 2
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t796 = 0
            else
                _t796 = (match_lookahead_literal(parser, "betree_relation", 1) || -1)
            end
            _t795 = _t796
        end
        _t794 = _t795
    else
        _t794 = -1
    end
    prediction247 = _t794
    if prediction247 == 2
        _t798 = parse_rel_edb(parser)
        rel_edb250 = _t798
        _t799 = Proto.Data(OneOf(:rel_edb, rel_edb250))
        _t797 = _t799
    else
        if prediction247 == 1
            _t801 = parse_betree_relation(parser)
            betree_relation249 = _t801
            _t802 = Proto.Data(OneOf(:betree_relation, betree_relation249))
            _t800 = _t802
        else
            if prediction247 == 0
                _t804 = parse_csv_data(parser)
                csv_data248 = _t804
                _t805 = Proto.Data(OneOf(:csv_data, csv_data248))
                _t803 = _t805
            else
                throw(ParseError("Unexpected token in data" * ": " * string(current_token(parser))))
                _t803 = nothing
            end
            _t800 = _t803
        end
        _t797 = _t800
    end
    return _t797
end

function parse_csv_data(parser::Parser)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t806 = parse_csv_locator(parser)
    locator251 = _t806
    _t807 = parse_csv_config(parser)
    config252 = _t807
    _t808 = parse_csv_columns(parser)
    columns253 = _t808
    _t809 = parse_csv_asof(parser)
    asof254 = _t809
    consume_literal!(parser, ")")
    _t810 = Proto.CSVData(locator251, config252, columns253, asof254)
    return _t810
end

function parse_csv_locator(parser::Parser)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    _t811 = parse_csv_locator_content(parser)
    x255 = _t811
    consume_literal!(parser, ")")
    return x255
end

function parse_csv_locator_content(parser::Parser)::Proto.CSVLocator
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "paths", 1)
            _t813 = 0
        else
            _t813 = (match_lookahead_literal(parser, "inline_data", 1) || -1)
        end
        _t812 = _t813
    else
        _t812 = -1
    end
    prediction256 = _t812
    if prediction256 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "inline_data")
        data260 = consume_terminal!(parser, "STRING")
        consume_literal!(parser, ")")
        _t815 = parser.encode_string(data260)
        _t816 = Proto.CSVLocator(String[], _t815)
        _t814 = _t816
    else
        if prediction256 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "paths")
            xs257 = String[]
            cond258 = match_lookahead_terminal(parser, "STRING", 0)
            while cond258
                push!(xs257, consume_terminal!(parser, "STRING"))
                cond258 = match_lookahead_terminal(parser, "STRING", 0)
            end
            paths259 = xs257
            consume_literal!(parser, ")")
            _t818 = Proto.CSVLocator(paths259, nothing)
            _t817 = _t818
        else
            throw(ParseError("Unexpected token in csv_locator_content" * ": " * string(current_token(parser))))
            _t817 = nothing
        end
        _t814 = _t817
    end
    return _t814
end

function parse_csv_config(parser::Parser)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t819 = parse_config_dict(parser)
    config261 = _t819
    consume_literal!(parser, ")")
    _t820 = parser.construct_csv_config(config261)
    return _t820
end

function parse_csv_columns(parser::Parser)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs262 = Proto.CSVColumn[]
    cond263 = match_lookahead_literal(parser, "(", 0)
    while cond263
        _t821 = parse_csv_column(parser)
        push!(xs262, _t821)
        cond263 = match_lookahead_literal(parser, "(", 0)
    end
    x264 = xs262
    consume_literal!(parser, ")")
    return x264
end

function parse_csv_column(parser::Parser)::Proto.CSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    column_name265 = consume_terminal!(parser, "STRING")
    _t822 = parse_relation_id(parser)
    target_id266 = _t822
    _t823 = parse_type_list(parser)
    types267 = _t823
    consume_literal!(parser, ")")
    _t824 = Proto.CSVColumn(column_name265, target_id266, types267)
    return _t824
end

function parse_type_list(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs268 = Proto.var"#Type"[]
    cond269 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond269
        _t825 = parse_type(parser)
        push!(xs268, _t825)
        cond269 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    x270 = xs268
    consume_literal!(parser, "]")
    return x270
end

function parse_csv_asof(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    x271 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return x271
end

function parse_betree_relation(parser::Parser)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t826 = parse_relation_id(parser)
    name272 = _t826
    _t827 = parse_betree_info(parser)
    info273 = _t827
    consume_literal!(parser, ")")
    _t828 = Proto.BeTreeRelation(name272, info273)
    return _t828
end

function parse_betree_info(parser::Parser)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t829 = parse_betree_key_types(parser)
    key_types274 = _t829
    _t830 = parse_betree_value_types(parser)
    value_types275 = _t830
    _t831 = parse_config_dict(parser)
    config276 = _t831
    consume_literal!(parser, ")")
    _t832 = parser.construct_betree_info(key_types274, value_types275, config276)
    return _t832
end

function parse_betree_key_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs277 = Proto.var"#Type"[]
    cond278 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond278
        _t833 = parse_type(parser)
        push!(xs277, _t833)
        cond278 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    x279 = xs277
    consume_literal!(parser, ")")
    return x279
end

function parse_betree_value_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs280 = Proto.var"#Type"[]
    cond281 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond281
        _t834 = parse_type(parser)
        push!(xs280, _t834)
        cond281 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    x282 = xs280
    consume_literal!(parser, ")")
    return x282
end

function parse_rel_edb(parser::Parser)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t835 = parse_relation_id(parser)
    target_id283 = _t835
    _t836 = parse_string_list(parser)
    path284 = _t836
    _t837 = parse_type_list(parser)
    types285 = _t837
    consume_literal!(parser, ")")
    _t838 = Proto.RelEDB(target_id283, path284, types285)
    return _t838
end

function parse_string_list(parser::Parser)::Vector{String}
    consume_literal!(parser, "[")
    xs286 = String[]
    cond287 = match_lookahead_terminal(parser, "STRING", 0)
    while cond287
        push!(xs286, consume_terminal!(parser, "STRING"))
        cond287 = match_lookahead_terminal(parser, "STRING", 0)
    end
    x288 = xs286
    consume_literal!(parser, "]")
    return x288
end

function parse_undefine(parser::Parser)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t839 = parse_fragment_id(parser)
    fragment_id289 = _t839
    consume_literal!(parser, ")")
    _t840 = Proto.Undefine(fragment_id289)
    return _t840
end

function parse_context(parser::Parser)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs290 = Proto.RelationId[]
    cond291 = (match_lookahead_terminal(parser, "COLON_SYMBOL", 0) || match_lookahead_terminal(parser, "INT", 0))
    while cond291
        _t841 = parse_relation_id(parser)
        push!(xs290, _t841)
        cond291 = (match_lookahead_terminal(parser, "COLON_SYMBOL", 0) || match_lookahead_terminal(parser, "INT", 0))
    end
    relations292 = xs290
    consume_literal!(parser, ")")
    _t842 = Proto.Context(relations292)
    return _t842
end

function parse_epoch_reads(parser::Parser)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs293 = Proto.Read[]
    cond294 = match_lookahead_literal(parser, "(", 0)
    while cond294
        _t843 = parse_read(parser)
        push!(xs293, _t843)
        cond294 = match_lookahead_literal(parser, "(", 0)
    end
    x295 = xs293
    consume_literal!(parser, ")")
    return x295
end

function parse_read(parser::Parser)::Proto.Read
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t845 = 2
        else
                if match_lookahead_literal(parser, "export", 1)
                    _t846 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t847 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t848 = 3
                        else
                            _t848 = -1
                        end
                        _t847 = _t848
                    end
                    _t846 = _t847
                end
            _t845 = (match_lookahead_literal(parser, "output", 1) || _t846)
        end
        _t844 = _t845
    else
        _t844 = -1
    end
    prediction296 = _t844
    if prediction296 == 4
        _t850 = parse_export(parser)
        value301 = _t850
        _t851 = Proto.Read(OneOf(:export, value301))
        _t849 = _t851
    else
        if prediction296 == 3
            _t853 = parse_abort(parser)
            value300 = _t853
            _t854 = Proto.Read(OneOf(:abort, value300))
            _t852 = _t854
        else
            if prediction296 == 2
                _t856 = parse_what_if(parser)
                value299 = _t856
                _t857 = Proto.Read(OneOf(:what_if, value299))
                _t855 = _t857
            else
                if prediction296 == 1
                    _t859 = parse_output(parser)
                    value298 = _t859
                    _t860 = Proto.Read(OneOf(:output, value298))
                    _t858 = _t860
                else
                    if prediction296 == 0
                        _t862 = parse_demand(parser)
                        value297 = _t862
                        _t863 = Proto.Read(OneOf(:demand, value297))
                        _t861 = _t863
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(current_token(parser))))
                        _t861 = nothing
                    end
                    _t858 = _t861
                end
                _t855 = _t858
            end
            _t852 = _t855
        end
        _t849 = _t852
    end
    return _t849
end

function parse_demand(parser::Parser)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t864 = parse_relation_id(parser)
    relation_id302 = _t864
    consume_literal!(parser, ")")
    _t865 = Proto.Demand(relation_id302)
    return _t865
end

function parse_output(parser::Parser)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    if match_lookahead_terminal(parser, "COLON_SYMBOL", 0)
        _t867 = parse_name(parser)
        _t866 = _t867
    else
        _t866 = nothing
    end
    name303 = _t866
    _t868 = parse_relation_id(parser)
    relation_id304 = _t868
    consume_literal!(parser, ")")
    _t869 = Proto.Output(something(name303, "output"), relation_id304)
    return _t869
end

function parse_what_if(parser::Parser)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t870 = parse_name(parser)
    branch305 = _t870
    _t871 = parse_epoch(parser)
    epoch306 = _t871
    consume_literal!(parser, ")")
    _t872 = Proto.WhatIf(branch305, epoch306)
    return _t872
end

function parse_abort(parser::Parser)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if match_lookahead_terminal(parser, "COLON_SYMBOL", 0)
        _t874 = parse_name(parser)
        _t873 = _t874
    else
        _t873 = nothing
    end
    name307 = _t873
    _t875 = parse_relation_id(parser)
    relation_id308 = _t875
    consume_literal!(parser, ")")
    _t876 = Proto.Abort(something(name307, "abort"), relation_id308)
    return _t876
end

function parse_export(parser::Parser)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t877 = parse_export_csvconfig(parser)
    config309 = _t877
    consume_literal!(parser, ")")
    _t878 = Proto.Export(OneOf(:csv_config, config309))
    return _t878
end

function parse_export_csvconfig(parser::Parser)::Proto.ExportCSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t879 = parse_export_csv_path(parser)
    path310 = _t879
    _t880 = parse_export_csv_columns(parser)
    columns311 = _t880
    _t881 = parse_config_dict(parser)
    config312 = _t881
    consume_literal!(parser, ")")
    return export_csv_config(parser, path310, columns311, config312)
end

function parse_export_csv_path(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    x313 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return x313
end

function parse_export_csv_columns(parser::Parser)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs314 = Proto.ExportCSVColumn[]
    cond315 = match_lookahead_literal(parser, "(", 0)
    while cond315
        _t882 = parse_export_csv_column(parser)
        push!(xs314, _t882)
        cond315 = match_lookahead_literal(parser, "(", 0)
    end
    x316 = xs314
    consume_literal!(parser, ")")
    return x316
end

function parse_export_csv_column(parser::Parser)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    name317 = consume_terminal!(parser, "STRING")
    _t883 = parse_relation_id(parser)
    relation_id318 = _t883
    consume_literal!(parser, ")")
    _t884 = Proto.ExportCSVColumn(name317, relation_id318)
    return _t884
end


function parse(input::String)
    lexer = Lexer(input)
    parser = Parser(lexer.tokens)
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
