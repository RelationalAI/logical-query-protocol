"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/transactions.proto --parser julia
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
        ("FLOAT", r"[-]?\d+\.\d+|inf|nan", scan_float),
        ("INT", r"[-]?\d+", scan_int),
        ("INT128", r"[-]?\d+i128", scan_int128),
        ("STRING", r"\"(?:[^\"\\]|\\.)*\"", scan_string),
        ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_.-]*", scan_symbol),
        ("UINT128", r"0x[0-9a-fA-F]+", scan_uint128),
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

# --- Helper functions ---

function _extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value}, default::int)::int
    
    if (!isnothing(value) && hasproperty(value, Symbol("int_value")) && !isnothing(getproperty(value, Symbol("int_value"))))
        return value.int_value
    else
        _t1058 = nothing
    end
    return default
end

function _extract_value_float64(parser::Parser, value::Union{Nothing, Proto.Value}, default::float)::float
    
    if (!isnothing(value) && hasproperty(value, Symbol("float_value")) && !isnothing(getproperty(value, Symbol("float_value"))))
        return value.float_value
    else
        _t1059 = nothing
    end
    return default
end

function _extract_value_string(parser::Parser, value::Union{Nothing, Proto.Value}, default::str)::str
    
    if (!isnothing(value) && hasproperty(value, Symbol("string_value")) && !isnothing(getproperty(value, Symbol("string_value"))))
        return value.string_value
    else
        _t1060 = nothing
    end
    return default
end

function _extract_value_boolean(parser::Parser, value::Union{Nothing, Proto.Value}, default::bool)::bool
    
    if (!isnothing(value) && hasproperty(value, Symbol("boolean_value")) && !isnothing(getproperty(value, Symbol("boolean_value"))))
        return value.boolean_value
    else
        _t1061 = nothing
    end
    return default
end

function _extract_value_bytes(parser::Parser, value::Union{Nothing, Proto.Value}, default::bytes)::bytes
    
    if (!isnothing(value) && hasproperty(value, Symbol("string_value")) && !isnothing(getproperty(value, Symbol("string_value"))))
        return Vector{UInt8}(value.string_value)
    else
        _t1062 = nothing
    end
    return default
end

function _extract_value_uint128(parser::Parser, value::Union{Nothing, Proto.Value}, default::Proto.UInt128Value)::Proto.UInt128Value
    
    if (!isnothing(value) && hasproperty(value, Symbol("uint128_value")) && !isnothing(getproperty(value, Symbol("uint128_value"))))
        return value.uint128_value
    else
        _t1063 = nothing
    end
    return default
end

function _extract_value_string_list(parser::Parser, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    
    if (!isnothing(value) && hasproperty(value, Symbol("string_value")) && !isnothing(getproperty(value, Symbol("string_value"))))
        return Any[value.string_value]
    else
        _t1064 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, int}
    
    if (!isnothing(value) && hasproperty(value, Symbol("int_value")) && !isnothing(getproperty(value, Symbol("int_value"))))
        return value.int_value
    else
        _t1065 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, float}
    
    if (!isnothing(value) && hasproperty(value, Symbol("float_value")) && !isnothing(getproperty(value, Symbol("float_value"))))
        return value.float_value
    else
        _t1066 = nothing
    end
    return nothing
end

function _try_extract_value_string(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, str}
    
    if (!isnothing(value) && hasproperty(value, Symbol("string_value")) && !isnothing(getproperty(value, Symbol("string_value"))))
        return value.string_value
    else
        _t1067 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, bytes}
    
    if (!isnothing(value) && hasproperty(value, Symbol("string_value")) && !isnothing(getproperty(value, Symbol("string_value"))))
        return Vector{UInt8}(value.string_value)
    else
        _t1068 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    
    if (!isnothing(value) && hasproperty(value, Symbol("uint128_value")) && !isnothing(getproperty(value, Symbol("uint128_value"))))
        return value.uint128_value
    else
        _t1069 = nothing
    end
    return nothing
end

function _try_extract_value_string_list(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{String}}
    
    if (!isnothing(value) && hasproperty(value, Symbol("string_value")) && !isnothing(getproperty(value, Symbol("string_value"))))
        return Any[value.string_value]
    else
        _t1070 = nothing
    end
    return nothing
end

function construct_csv_config(parser::Parser, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1071 = Parser._extract_value_int64(get(config, "csv_header_row", nothing), 1)
    header_row = _t1071
    _t1072 = Parser._extract_value_int64(get(config, "csv_skip", nothing), 0)
    skip = _t1072
    _t1073 = Parser._extract_value_string(get(config, "csv_new_line", nothing), "")
    new_line = _t1073
    _t1074 = Parser._extract_value_string(get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1074
    _t1075 = Parser._extract_value_string(get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1075
    _t1076 = Parser._extract_value_string(get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1076
    _t1077 = Parser._extract_value_string(get(config, "csv_comment", nothing), "")
    comment = _t1077
    _t1078 = Parser._extract_value_string_list(get(config, "csv_missing_strings", nothing), Never[])
    missing_strings = _t1078
    _t1079 = Parser._extract_value_string(get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1079
    _t1080 = Parser._extract_value_string(get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1080
    _t1081 = Parser._extract_value_string(get(config, "csv_compression", nothing), "auto")
    compression = _t1081
    _t1082 = Proto.CSVConfig(; header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1082
end

function construct_betree_info(parser::Parser, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1083 = Parser._try_extract_value_float64(get(config, "betree_config_epsilon", nothing))
    epsilon = _t1083
    _t1084 = Parser._try_extract_value_int64(get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1084
    _t1085 = Parser._try_extract_value_int64(get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1085
    _t1086 = Parser._try_extract_value_int64(get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1086
    _t1087 = Proto.BeTreeConfig(; epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1087
    _t1088 = Parser._try_extract_value_uint128(get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1088
    _t1089 = Parser._try_extract_value_bytes(get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1089
    _t1090 = Parser._try_extract_value_int64(get(config, "betree_locator_element_count", nothing))
    element_count = _t1090
    _t1091 = Parser._try_extract_value_int64(get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1091
    _t1092 = Proto.BeTreeLocator(; root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
    relation_locator = _t1092
    _t1093 = Proto.BeTreeInfo(; key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1093
end

function construct_configure(parser::Parser, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.Configure
    config = Dict(config_dict)
    maintenance_level_val = get(config, "ivm.maintenance_level", nothing)
    maintenance_level = nothing
    
    if (!isnothing(maintenance_level_val) && hasproperty(maintenance_level_val, Symbol("string_value")) && !isnothing(getproperty(maintenance_level_val, Symbol("string_value"))))
        
        if maintenance_level_val.string_value == "off"
            maintenance_level = "MAINTENANCE_LEVEL_OFF"
            _t1095 = nothing
        else
            
            if maintenance_level_val.string_value == "auto"
                maintenance_level = "MAINTENANCE_LEVEL_AUTO"
                _t1096 = nothing
            else
                
                if maintenance_level_val.string_value == "all"
                    maintenance_level = "MAINTENANCE_LEVEL_ALL"
                    _t1097 = nothing
                else
                    maintenance_level = "MAINTENANCE_LEVEL_OFF"
                    _t1097 = nothing
                end
                _t1096 = _t1097
            end
            _t1095 = _t1096
        end
        _t1094 = _t1095
    else
        maintenance_level = "MAINTENANCE_LEVEL_OFF"
        _t1094 = nothing
    end
    _t1098 = Proto.IVMConfig(; level=maintenance_level)
    ivm_config = _t1098
    _t1099 = Parser._extract_value_int64(get(config, "semantics_version", nothing), 0)
    semantics_version = _t1099
    _t1100 = Proto.Configure(; semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1100
end

function export_csv_config(parser::Parser, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1101 = Parser._extract_value_int64(get(config, "partition_size", nothing), 0)
    partition_size = _t1101
    _t1102 = Parser._extract_value_string(get(config, "compression", nothing), "")
    compression = _t1102
    _t1103 = Parser._extract_value_boolean(get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1103
    _t1104 = Parser._extract_value_string(get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1104
    _t1105 = Parser._extract_value_string(get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1105
    _t1106 = Parser._extract_value_string(get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1106
    _t1107 = Parser._extract_value_string(get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1107
    _t1108 = Proto.ExportCSVConfig(; path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1108
end

# --- Parse functions ---

function parse_transaction(parser::Parser)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t354 = parse_configure(parser)
        _t353 = _t354
    else
        _t353 = nothing
    end
    configure0 = _t353
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t356 = parse_sync(parser)
        _t355 = _t356
    else
        _t355 = nothing
    end
    sync1 = _t355
    xs2 = Proto.Epoch[]
    cond3 = match_lookahead_literal(parser, "(", 0)
    while cond3
        _t357 = parse_epoch(parser)
        item4 = _t357
        xs2 = vcat(xs2, !isnothing(Proto.Epoch[item4]) ? Proto.Epoch[item4] : [])
        cond3 = match_lookahead_literal(parser, "(", 0)
    end
    epochs5 = xs2
    consume_literal!(parser, ")")
    _t358 = Parser.construct_configure(Never[])
    _t359 = Proto.Transaction(; epochs=epochs5, configure=(!isnothing(configure0) ? configure0 : _t358), sync=sync1)
    return _t359
end

function parse_configure(parser::Parser)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t360 = parse_config_dict(parser)
    config_dict6 = _t360
    consume_literal!(parser, ")")
    _t361 = Parser.construct_configure(config_dict6)
    return _t361
end

function parse_config_dict(parser::Parser)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs7 = Tuple{String, Proto.Value}[]
    cond8 = match_lookahead_literal(parser, ":", 0)
    while cond8
        _t362 = parse_config_key_value(parser)
        item9 = _t362
        xs7 = vcat(xs7, !isnothing(Tuple{String, Proto.Value}[item9]) ? Tuple{String, Proto.Value}[item9] : [])
        cond8 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values10 = xs7
    consume_literal!(parser, "}")
    return config_key_values10
end

function parse_config_key_value(parser::Parser)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol11 = consume_terminal!(parser, "SYMBOL")
    _t363 = parse_value(parser)
    value12 = _t363
    return (symbol11, value12,)
end

function parse_value(parser::Parser)::Proto.Value
    
    if match_lookahead_literal(parser, "true", 0)
        _t364 = 9
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t365 = 8
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t366 = 9
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t369 = 1
                    else
                        
                        if match_lookahead_literal(parser, "date", 1)
                            _t370 = 0
                        else
                            _t370 = -1
                        end
                        _t369 = _t370
                    end
                    _t367 = _t369
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t371 = 5
                    else
                        
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t372 = 2
                        else
                            
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t373 = 6
                            else
                                
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t374 = 3
                                else
                                    
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t375 = 4
                                    else
                                        
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t376 = 7
                                        else
                                            _t376 = -1
                                        end
                                        _t375 = _t376
                                    end
                                    _t374 = _t375
                                end
                                _t373 = _t374
                            end
                            _t372 = _t373
                        end
                        _t371 = _t372
                    end
                    _t367 = _t371
                end
                _t366 = _t367
            end
            _t365 = _t366
        end
        _t364 = _t365
    end
    prediction13 = _t364
    
    if prediction13 == 9
        _t378 = parse_boolean_value(parser)
        boolean_value22 = _t378
        _t379 = Proto.Value(; boolean_value=boolean_value22)
        _t377 = _t379
    else
        
        if prediction13 == 8
            consume_literal!(parser, "missing")
            _t381 = Proto.MissingValue()
            _t382 = Proto.Value(; missing_value=_t381)
            _t380 = _t382
        else
            
            if prediction13 == 7
                decimal21 = consume_terminal!(parser, "DECIMAL")
                _t384 = Proto.Value(; decimal_value=decimal21)
                _t383 = _t384
            else
                
                if prediction13 == 6
                    int12820 = consume_terminal!(parser, "INT128")
                    _t386 = Proto.Value(; int128_value=int12820)
                    _t385 = _t386
                else
                    
                    if prediction13 == 5
                        uint12819 = consume_terminal!(parser, "UINT128")
                        _t388 = Proto.Value(; uint128_value=uint12819)
                        _t387 = _t388
                    else
                        
                        if prediction13 == 4
                            float18 = consume_terminal!(parser, "FLOAT")
                            _t390 = Proto.Value(; float_value=float18)
                            _t389 = _t390
                        else
                            
                            if prediction13 == 3
                                int17 = consume_terminal!(parser, "INT")
                                _t392 = Proto.Value(; int_value=int17)
                                _t391 = _t392
                            else
                                
                                if prediction13 == 2
                                    string16 = consume_terminal!(parser, "STRING")
                                    _t394 = Proto.Value(; string_value=string16)
                                    _t393 = _t394
                                else
                                    
                                    if prediction13 == 1
                                        _t396 = parse_datetime(parser)
                                        datetime15 = _t396
                                        _t397 = Proto.Value(; datetime_value=datetime15)
                                        _t395 = _t397
                                    else
                                        
                                        if prediction13 == 0
                                            _t399 = parse_date(parser)
                                            date14 = _t399
                                            _t400 = Proto.Value(; date_value=date14)
                                            _t398 = _t400
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(current_token(parser))))
                                        end
                                        _t395 = _t398
                                    end
                                    _t393 = _t395
                                end
                                _t391 = _t393
                            end
                            _t389 = _t391
                        end
                        _t387 = _t389
                    end
                    _t385 = _t387
                end
                _t383 = _t385
            end
            _t380 = _t383
        end
        _t377 = _t380
    end
    return _t377
end

function parse_date(parser::Parser)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int23 = consume_terminal!(parser, "INT")
    int_324 = consume_terminal!(parser, "INT")
    int_425 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t401 = Proto.DateValue(; year=Int32(int23), month=Int32(int_324), day=Int32(int_425))
    return _t401
end

function parse_datetime(parser::Parser)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int26 = consume_terminal!(parser, "INT")
    int_327 = consume_terminal!(parser, "INT")
    int_428 = consume_terminal!(parser, "INT")
    int_529 = consume_terminal!(parser, "INT")
    int_630 = consume_terminal!(parser, "INT")
    int_731 = consume_terminal!(parser, "INT")
    
    if match_lookahead_terminal(parser, "INT", 0)
        _t402 = consume_terminal!(parser, "INT")
    else
        _t402 = nothing
    end
    int_832 = _t402
    consume_literal!(parser, ")")
    _t403 = Proto.DateTimeValue(; year=Int32(int26), month=Int32(int_327), day=Int32(int_428), hour=Int32(int_529), minute=Int32(int_630), second=Int32(int_731), microsecond=Int32((!isnothing(int_832) ? int_832 : 0)))
    return _t403
end

function parse_boolean_value(parser::Parser)::Bool
    
    if match_lookahead_literal(parser, "true", 0)
        _t404 = 0
    else
        _t404 = (match_lookahead_literal(parser, "false", 0) || -1)
    end
    prediction33 = _t404
    
    if prediction33 == 1
        consume_literal!(parser, "false")
        _t405 = false
    else
        
        if prediction33 == 0
            consume_literal!(parser, "true")
            _t406 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(current_token(parser))))
        end
        _t405 = _t406
    end
    return _t405
end

function parse_sync(parser::Parser)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs34 = Proto.FragmentId[]
    cond35 = match_lookahead_literal(parser, ":", 0)
    while cond35
        _t407 = parse_fragment_id(parser)
        item36 = _t407
        xs34 = vcat(xs34, !isnothing(Proto.FragmentId[item36]) ? Proto.FragmentId[item36] : [])
        cond35 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids37 = xs34
    consume_literal!(parser, ")")
    _t408 = Proto.Sync(; fragments=fragment_ids37)
    return _t408
end

function parse_fragment_id(parser::Parser)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol38 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(; id=Vector{UInt8}(symbol38))
end

function parse_epoch(parser::Parser)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t410 = parse_epoch_writes(parser)
        _t409 = _t410
    else
        _t409 = nothing
    end
    epoch_writes39 = _t409
    
    if match_lookahead_literal(parser, "(", 0)
        _t412 = parse_epoch_reads(parser)
        _t411 = _t412
    else
        _t411 = nothing
    end
    epoch_reads40 = _t411
    consume_literal!(parser, ")")
    _t413 = Proto.Epoch(; writes=(!isnothing(epoch_writes39) ? epoch_writes39 : Never[]), reads=(!isnothing(epoch_reads40) ? epoch_reads40 : Never[]))
    return _t413
end

function parse_epoch_writes(parser::Parser)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs41 = Proto.Write[]
    cond42 = match_lookahead_literal(parser, "(", 0)
    while cond42
        _t414 = parse_write(parser)
        item43 = _t414
        xs41 = vcat(xs41, !isnothing(Proto.Write[item43]) ? Proto.Write[item43] : [])
        cond42 = match_lookahead_literal(parser, "(", 0)
    end
    writes44 = xs41
    consume_literal!(parser, ")")
    return writes44
end

function parse_write(parser::Parser)::Proto.Write
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "undefine", 1)
            _t418 = 1
        else
            
            if match_lookahead_literal(parser, "define", 1)
                _t419 = 0
            else
                
                if match_lookahead_literal(parser, "context", 1)
                    _t420 = 2
                else
                    _t420 = -1
                end
                _t419 = _t420
            end
            _t418 = _t419
        end
        _t415 = _t418
    else
        _t415 = -1
    end
    prediction45 = _t415
    
    if prediction45 == 2
        _t422 = parse_context(parser)
        context48 = _t422
        _t423 = Proto.Write(; context=context48)
        _t421 = _t423
    else
        
        if prediction45 == 1
            _t425 = parse_undefine(parser)
            undefine47 = _t425
            _t426 = Proto.Write(; undefine=undefine47)
            _t424 = _t426
        else
            
            if prediction45 == 0
                _t428 = parse_define(parser)
                define46 = _t428
                _t429 = Proto.Write(; define=define46)
                _t427 = _t429
            else
                throw(ParseError("Unexpected token in write" * ": " * string(current_token(parser))))
            end
            _t424 = _t427
        end
        _t421 = _t424
    end
    return _t421
end

function parse_define(parser::Parser)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t430 = parse_fragment(parser)
    fragment49 = _t430
    consume_literal!(parser, ")")
    _t431 = Proto.Define(; fragment=fragment49)
    return _t431
end

function parse_fragment(parser::Parser)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t432 = parse_new_fragment_id(parser)
    new_fragment_id50 = _t432
    xs51 = Proto.Declaration[]
    cond52 = match_lookahead_literal(parser, "(", 0)
    while cond52
        _t433 = parse_declaration(parser)
        item53 = _t433
        xs51 = vcat(xs51, !isnothing(Proto.Declaration[item53]) ? Proto.Declaration[item53] : [])
        cond52 = match_lookahead_literal(parser, "(", 0)
    end
    declarations54 = xs51
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id50, declarations54)
end

function parse_new_fragment_id(parser::Parser)::Proto.FragmentId
    _t434 = parse_fragment_id(parser)
    fragment_id55 = _t434
    start_fragment(parser, fragment_id55)
    return fragment_id55
end

function parse_declaration(parser::Parser)::Proto.Declaration
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t436 = 3
        else
            
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t437 = 2
            else
                
                if match_lookahead_literal(parser, "def", 1)
                    _t438 = 0
                else
                    
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t439 = 3
                    else
                        
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t440 = 3
                        else
                            _t440 = (match_lookahead_literal(parser, "algorithm", 1) || -1)
                        end
                        _t439 = _t440
                    end
                    _t438 = _t439
                end
                _t437 = _t438
            end
            _t436 = _t437
        end
        _t435 = _t436
    else
        _t435 = -1
    end
    prediction56 = _t435
    
    if prediction56 == 3
        _t442 = parse_data(parser)
        data60 = _t442
        _t443 = Proto.Declaration(; data=data60)
        _t441 = _t443
    else
        
        if prediction56 == 2
            _t445 = parse_constraint(parser)
            constraint59 = _t445
            _t446 = Proto.Declaration(; constraint=constraint59)
            _t444 = _t446
        else
            
            if prediction56 == 1
                _t448 = parse_algorithm(parser)
                algorithm58 = _t448
                _t449 = Proto.Declaration(; algorithm=algorithm58)
                _t447 = _t449
            else
                
                if prediction56 == 0
                    _t451 = parse_def(parser)
                    def57 = _t451
                    _t452 = Proto.Declaration(; def=def57)
                    _t450 = _t452
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(current_token(parser))))
                end
                _t447 = _t450
            end
            _t444 = _t447
        end
        _t441 = _t444
    end
    return _t441
end

function parse_def(parser::Parser)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t453 = parse_relation_id(parser)
    relation_id61 = _t453
    _t454 = parse_abstraction(parser)
    abstraction62 = _t454
    
    if match_lookahead_literal(parser, "(", 0)
        _t456 = parse_attrs(parser)
        _t455 = _t456
    else
        _t455 = nothing
    end
    attrs63 = _t455
    consume_literal!(parser, ")")
    _t457 = Proto.Def(; name=relation_id61, body=abstraction62, attrs=(!isnothing(attrs63) ? attrs63 : Never[]))
    return _t457
end

function parse_relation_id(parser::Parser)::Proto.RelationId
    
    if match_lookahead_literal(parser, ":", 0)
        _t458 = 0
    else
        _t458 = (match_lookahead_terminal(parser, "INT", 0) || -1)
    end
    prediction64 = _t458
    
    if prediction64 == 1
        int66 = consume_terminal!(parser, "INT")
        _t459 = Proto.RelationId(; id_low=int66 & 0xFFFFFFFFFFFFFFFF, id_high=(int66 >> 64) & 0xFFFFFFFFFFFFFFFF)
    else
        
        if prediction64 == 0
            consume_literal!(parser, ":")
            symbol65 = consume_terminal!(parser, "SYMBOL")
            _t460 = relation_id_from_string(parser, symbol65)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(current_token(parser))))
        end
        _t459 = _t460
    end
    return _t459
end

function parse_abstraction(parser::Parser)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t461 = parse_bindings(parser)
    bindings67 = _t461
    _t462 = parse_formula(parser)
    formula68 = _t462
    consume_literal!(parser, ")")
    _t463 = Proto.Abstraction(; vars=vcat(bindings67[1], !isnothing(bindings67[2]) ? bindings67[2] : []), value=formula68)
    return _t463
end

function parse_bindings(parser::Parser)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs69 = Proto.Binding[]
    cond70 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond70
        _t464 = parse_binding(parser)
        item71 = _t464
        xs69 = vcat(xs69, !isnothing(Proto.Binding[item71]) ? Proto.Binding[item71] : [])
        cond70 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings72 = xs69
    
    if match_lookahead_literal(parser, "|", 0)
        _t466 = parse_value_bindings(parser)
        _t465 = _t466
    else
        _t465 = nothing
    end
    value_bindings73 = _t465
    consume_literal!(parser, "]")
    return (bindings72, (!isnothing(value_bindings73) ? value_bindings73 : Never[]),)
end

function parse_binding(parser::Parser)::Proto.Binding
    symbol74 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t467 = parse_type(parser)
    type75 = _t467
    _t468 = Proto.Var(; name=symbol74)
    _t469 = Proto.Binding(; var=_t468, type_=type75)
    return _t469
end

function parse_type(parser::Parser)::Proto.var"#Type"
    
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t470 = 0
    else
        
        if match_lookahead_literal(parser, "UINT128", 0)
            _t471 = 4
        else
            
            if match_lookahead_literal(parser, "STRING", 0)
                _t480 = 1
            else
                
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t481 = 8
                else
                    
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t482 = 5
                    else
                        
                        if match_lookahead_literal(parser, "INT", 0)
                            _t483 = 2
                        else
                            
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t484 = 3
                            else
                                
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t485 = 7
                                else
                                    
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t486 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t487 = 10
                                        else
                                            
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t488 = 9
                                            else
                                                _t488 = -1
                                            end
                                            _t487 = _t488
                                        end
                                        _t486 = _t487
                                    end
                                    _t485 = _t486
                                end
                                _t484 = _t485
                            end
                            _t483 = _t484
                        end
                        _t482 = _t483
                    end
                    _t481 = _t482
                end
                _t480 = _t481
            end
            _t471 = _t480
        end
        _t470 = _t471
    end
    prediction76 = _t470
    
    if prediction76 == 10
        _t490 = parse_boolean_type(parser)
        boolean_type87 = _t490
        _t491 = Proto.var"#Type"(; boolean_type=boolean_type87)
        _t489 = _t491
    else
        
        if prediction76 == 9
            _t493 = parse_decimal_type(parser)
            decimal_type86 = _t493
            _t494 = Proto.var"#Type"(; decimal_type=decimal_type86)
            _t492 = _t494
        else
            
            if prediction76 == 8
                _t496 = parse_missing_type(parser)
                missing_type85 = _t496
                _t497 = Proto.var"#Type"(; missing_type=missing_type85)
                _t495 = _t497
            else
                
                if prediction76 == 7
                    _t499 = parse_datetime_type(parser)
                    datetime_type84 = _t499
                    _t500 = Proto.var"#Type"(; datetime_type=datetime_type84)
                    _t498 = _t500
                else
                    
                    if prediction76 == 6
                        _t502 = parse_date_type(parser)
                        date_type83 = _t502
                        _t503 = Proto.var"#Type"(; date_type=date_type83)
                        _t501 = _t503
                    else
                        
                        if prediction76 == 5
                            _t505 = parse_int128_type(parser)
                            int128_type82 = _t505
                            _t506 = Proto.var"#Type"(; int128_type=int128_type82)
                            _t504 = _t506
                        else
                            
                            if prediction76 == 4
                                _t508 = parse_uint128_type(parser)
                                uint128_type81 = _t508
                                _t509 = Proto.var"#Type"(; uint128_type=uint128_type81)
                                _t507 = _t509
                            else
                                
                                if prediction76 == 3
                                    _t511 = parse_float_type(parser)
                                    float_type80 = _t511
                                    _t512 = Proto.var"#Type"(; float_type=float_type80)
                                    _t510 = _t512
                                else
                                    
                                    if prediction76 == 2
                                        _t514 = parse_int_type(parser)
                                        int_type79 = _t514
                                        _t515 = Proto.var"#Type"(; int_type=int_type79)
                                        _t513 = _t515
                                    else
                                        
                                        if prediction76 == 1
                                            _t517 = parse_string_type(parser)
                                            string_type78 = _t517
                                            _t518 = Proto.var"#Type"(; string_type=string_type78)
                                            _t516 = _t518
                                        else
                                            
                                            if prediction76 == 0
                                                _t520 = parse_unspecified_type(parser)
                                                unspecified_type77 = _t520
                                                _t521 = Proto.var"#Type"(; unspecified_type=unspecified_type77)
                                                _t519 = _t521
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(current_token(parser))))
                                            end
                                            _t516 = _t519
                                        end
                                        _t513 = _t516
                                    end
                                    _t510 = _t513
                                end
                                _t507 = _t510
                            end
                            _t504 = _t507
                        end
                        _t501 = _t504
                    end
                    _t498 = _t501
                end
                _t495 = _t498
            end
            _t492 = _t495
        end
        _t489 = _t492
    end
    return _t489
end

function parse_unspecified_type(parser::Parser)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t522 = Proto.UnspecifiedType()
    return _t522
end

function parse_string_type(parser::Parser)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t523 = Proto.StringType()
    return _t523
end

function parse_int_type(parser::Parser)::Proto.IntType
    consume_literal!(parser, "INT")
    _t524 = Proto.IntType()
    return _t524
end

function parse_float_type(parser::Parser)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t525 = Proto.FloatType()
    return _t525
end

function parse_uint128_type(parser::Parser)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t526 = Proto.UInt128Type()
    return _t526
end

function parse_int128_type(parser::Parser)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t527 = Proto.Int128Type()
    return _t527
end

function parse_date_type(parser::Parser)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t528 = Proto.DateType()
    return _t528
end

function parse_datetime_type(parser::Parser)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t529 = Proto.DateTimeType()
    return _t529
end

function parse_missing_type(parser::Parser)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t530 = Proto.MissingType()
    return _t530
end

function parse_decimal_type(parser::Parser)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int88 = consume_terminal!(parser, "INT")
    int_389 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t531 = Proto.DecimalType(; precision=Int32(int88), scale=Int32(int_389))
    return _t531
end

function parse_boolean_type(parser::Parser)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t532 = Proto.BooleanType()
    return _t532
end

function parse_value_bindings(parser::Parser)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs90 = Proto.Binding[]
    cond91 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond91
        _t533 = parse_binding(parser)
        item92 = _t533
        xs90 = vcat(xs90, !isnothing(Proto.Binding[item92]) ? Proto.Binding[item92] : [])
        cond91 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings93 = xs90
    return bindings93
end

function parse_formula(parser::Parser)::Proto.Formula
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "true", 1)
            _t535 = 0
        else
            
            if match_lookahead_literal(parser, "relatom", 1)
                _t536 = 11
            else
                
                if match_lookahead_literal(parser, "reduce", 1)
                    _t537 = 3
                else
                    
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t538 = 10
                    else
                        
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t539 = 9
                        else
                            
                            if match_lookahead_literal(parser, "or", 1)
                                _t540 = 5
                            else
                                
                                if match_lookahead_literal(parser, "not", 1)
                                    _t541 = 6
                                else
                                    
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t542 = 7
                                    else
                                        
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t556 = 1
                                        else
                                            
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t557 = 2
                                            else
                                                
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t558 = 12
                                                else
                                                    
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t559 = 8
                                                    else
                                                        
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t560 = 4
                                                        else
                                                            
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t561 = 10
                                                            else
                                                                
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t562 = 10
                                                                else
                                                                    
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t563 = 10
                                                                    else
                                                                        
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t564 = 10
                                                                        else
                                                                            
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t565 = 10
                                                                            else
                                                                                
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t566 = 10
                                                                                else
                                                                                    
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t567 = 10
                                                                                    else
                                                                                        
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t568 = 10
                                                                                        else
                                                                                            
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t569 = 10
                                                                                            else
                                                                                                _t569 = -1
                                                                                            end
                                                                                            _t568 = _t569
                                                                                        end
                                                                                        _t567 = _t568
                                                                                    end
                                                                                    _t566 = _t567
                                                                                end
                                                                                _t565 = _t566
                                                                            end
                                                                            _t564 = _t565
                                                                        end
                                                                        _t563 = _t564
                                                                    end
                                                                    _t562 = _t563
                                                                end
                                                                _t561 = _t562
                                                            end
                                                            _t560 = _t561
                                                        end
                                                        _t559 = _t560
                                                    end
                                                    _t558 = _t559
                                                end
                                                _t557 = _t558
                                            end
                                            _t556 = _t557
                                        end
                                        _t542 = _t556
                                    end
                                    _t541 = _t542
                                end
                                _t540 = _t541
                            end
                            _t539 = _t540
                        end
                        _t538 = _t539
                    end
                    _t537 = _t538
                end
                _t536 = _t537
            end
            _t535 = _t536
        end
        _t534 = _t535
    else
        _t534 = -1
    end
    prediction94 = _t534
    
    if prediction94 == 12
        _t571 = parse_cast(parser)
        cast107 = _t571
        _t572 = Proto.Formula(; cast=cast107)
        _t570 = _t572
    else
        
        if prediction94 == 11
            _t574 = parse_rel_atom(parser)
            rel_atom106 = _t574
            _t575 = Proto.Formula(; rel_atom=rel_atom106)
            _t573 = _t575
        else
            
            if prediction94 == 10
                _t577 = parse_primitive(parser)
                primitive105 = _t577
                _t578 = Proto.Formula(; primitive_=primitive105)
                _t576 = _t578
            else
                
                if prediction94 == 9
                    _t580 = parse_pragma(parser)
                    pragma104 = _t580
                    _t581 = Proto.Formula(; pragma=pragma104)
                    _t579 = _t581
                else
                    
                    if prediction94 == 8
                        _t583 = parse_atom(parser)
                        atom103 = _t583
                        _t584 = Proto.Formula(; atom=atom103)
                        _t582 = _t584
                    else
                        
                        if prediction94 == 7
                            _t586 = parse_ffi(parser)
                            ffi102 = _t586
                            _t587 = Proto.Formula(; ffi=ffi102)
                            _t585 = _t587
                        else
                            
                            if prediction94 == 6
                                _t589 = parse_not(parser)
                                not101 = _t589
                                _t590 = Proto.Formula(; not=not101)
                                _t588 = _t590
                            else
                                
                                if prediction94 == 5
                                    _t592 = parse_disjunction(parser)
                                    disjunction100 = _t592
                                    _t593 = Proto.Formula(; disjunction=disjunction100)
                                    _t591 = _t593
                                else
                                    
                                    if prediction94 == 4
                                        _t595 = parse_conjunction(parser)
                                        conjunction99 = _t595
                                        _t596 = Proto.Formula(; conjunction=conjunction99)
                                        _t594 = _t596
                                    else
                                        
                                        if prediction94 == 3
                                            _t598 = parse_reduce(parser)
                                            reduce98 = _t598
                                            _t599 = Proto.Formula(; reduce=reduce98)
                                            _t597 = _t599
                                        else
                                            
                                            if prediction94 == 2
                                                _t601 = parse_exists(parser)
                                                exists97 = _t601
                                                _t602 = Proto.Formula(; exists=exists97)
                                                _t600 = _t602
                                            else
                                                
                                                if prediction94 == 1
                                                    _t604 = parse_false(parser)
                                                    false96 = _t604
                                                    _t605 = Proto.Formula(; disjunction=false96)
                                                    _t603 = _t605
                                                else
                                                    
                                                    if prediction94 == 0
                                                        _t607 = parse_true(parser)
                                                        true95 = _t607
                                                        _t608 = Proto.Formula(; conjunction=true95)
                                                        _t606 = _t608
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(current_token(parser))))
                                                    end
                                                    _t603 = _t606
                                                end
                                                _t600 = _t603
                                            end
                                            _t597 = _t600
                                        end
                                        _t594 = _t597
                                    end
                                    _t591 = _t594
                                end
                                _t588 = _t591
                            end
                            _t585 = _t588
                        end
                        _t582 = _t585
                    end
                    _t579 = _t582
                end
                _t576 = _t579
            end
            _t573 = _t576
        end
        _t570 = _t573
    end
    return _t570
end

function parse_true(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t609 = Proto.Conjunction(; args=Never[])
    return _t609
end

function parse_false(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t610 = Proto.Disjunction(; args=Never[])
    return _t610
end

function parse_exists(parser::Parser)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t611 = parse_bindings(parser)
    bindings108 = _t611
    _t612 = parse_formula(parser)
    formula109 = _t612
    consume_literal!(parser, ")")
    _t613 = Proto.Abstraction(; vars=vcat(bindings108[1], !isnothing(bindings108[2]) ? bindings108[2] : []), value=formula109)
    _t614 = Proto.Exists(; body=_t613)
    return _t614
end

function parse_reduce(parser::Parser)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t615 = parse_abstraction(parser)
    abstraction110 = _t615
    _t616 = parse_abstraction(parser)
    abstraction_3111 = _t616
    _t617 = parse_terms(parser)
    terms112 = _t617
    consume_literal!(parser, ")")
    _t618 = Proto.Reduce(; op=abstraction110, body=abstraction_3111, terms=terms112)
    return _t618
end

function parse_terms(parser::Parser)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs113 = Proto.Term[]
    cond114 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond114
        _t619 = parse_term(parser)
        item115 = _t619
        xs113 = vcat(xs113, !isnothing(Proto.Term[item115]) ? Proto.Term[item115] : [])
        cond114 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms116 = xs113
    consume_literal!(parser, ")")
    return terms116
end

function parse_term(parser::Parser)::Proto.Term
    
    if match_lookahead_literal(parser, "true", 0)
        _t651 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t667 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t675 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t679 = 1
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t681 = 1
                    else
                        
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t682 = 0
                        else
                            _t682 = (match_lookahead_terminal(parser, "STRING", 0) || (match_lookahead_terminal(parser, "INT128", 0) || (match_lookahead_terminal(parser, "INT", 0) || (match_lookahead_terminal(parser, "FLOAT", 0) || (match_lookahead_terminal(parser, "DECIMAL", 0) || -1)))))
                        end
                        _t681 = _t682
                    end
                    _t679 = _t681
                end
                _t675 = _t679
            end
            _t667 = _t675
        end
        _t651 = _t667
    end
    prediction117 = _t651
    
    if prediction117 == 1
        _t684 = parse_constant(parser)
        constant119 = _t684
        _t685 = Proto.Term(; constant=constant119)
        _t683 = _t685
    else
        
        if prediction117 == 0
            _t687 = parse_var(parser)
            var118 = _t687
            _t688 = Proto.Term(; var=var118)
            _t686 = _t688
        else
            throw(ParseError("Unexpected token in term" * ": " * string(current_token(parser))))
        end
        _t683 = _t686
    end
    return _t683
end

function parse_var(parser::Parser)::Proto.Var
    symbol120 = consume_terminal!(parser, "SYMBOL")
    _t689 = Proto.Var(; name=symbol120)
    return _t689
end

function parse_constant(parser::Parser)::Proto.Value
    _t690 = parse_value(parser)
    value121 = _t690
    return value121
end

function parse_conjunction(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs122 = Proto.Formula[]
    cond123 = match_lookahead_literal(parser, "(", 0)
    while cond123
        _t691 = parse_formula(parser)
        item124 = _t691
        xs122 = vcat(xs122, !isnothing(Proto.Formula[item124]) ? Proto.Formula[item124] : [])
        cond123 = match_lookahead_literal(parser, "(", 0)
    end
    formulas125 = xs122
    consume_literal!(parser, ")")
    _t692 = Proto.Conjunction(; args=formulas125)
    return _t692
end

function parse_disjunction(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs126 = Proto.Formula[]
    cond127 = match_lookahead_literal(parser, "(", 0)
    while cond127
        _t693 = parse_formula(parser)
        item128 = _t693
        xs126 = vcat(xs126, !isnothing(Proto.Formula[item128]) ? Proto.Formula[item128] : [])
        cond127 = match_lookahead_literal(parser, "(", 0)
    end
    formulas129 = xs126
    consume_literal!(parser, ")")
    _t694 = Proto.Disjunction(; args=formulas129)
    return _t694
end

function parse_not(parser::Parser)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t695 = parse_formula(parser)
    formula130 = _t695
    consume_literal!(parser, ")")
    _t696 = Proto.Not(; arg=formula130)
    return _t696
end

function parse_ffi(parser::Parser)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t697 = parse_name(parser)
    name131 = _t697
    _t698 = parse_ffi_args(parser)
    ffi_args132 = _t698
    _t699 = parse_terms(parser)
    terms133 = _t699
    consume_literal!(parser, ")")
    _t700 = Proto.FFI(; name=name131, args=ffi_args132, terms=terms133)
    return _t700
end

function parse_name(parser::Parser)::String
    consume_literal!(parser, ":")
    symbol134 = consume_terminal!(parser, "SYMBOL")
    return symbol134
end

function parse_ffi_args(parser::Parser)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs135 = Proto.Abstraction[]
    cond136 = match_lookahead_literal(parser, "(", 0)
    while cond136
        _t701 = parse_abstraction(parser)
        item137 = _t701
        xs135 = vcat(xs135, !isnothing(Proto.Abstraction[item137]) ? Proto.Abstraction[item137] : [])
        cond136 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions138 = xs135
    consume_literal!(parser, ")")
    return abstractions138
end

function parse_atom(parser::Parser)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t702 = parse_relation_id(parser)
    relation_id139 = _t702
    xs140 = Proto.Term[]
    cond141 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond141
        _t703 = parse_term(parser)
        item142 = _t703
        xs140 = vcat(xs140, !isnothing(Proto.Term[item142]) ? Proto.Term[item142] : [])
        cond141 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms143 = xs140
    consume_literal!(parser, ")")
    _t704 = Proto.Atom(; name=relation_id139, terms=terms143)
    return _t704
end

function parse_pragma(parser::Parser)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t705 = parse_name(parser)
    name144 = _t705
    xs145 = Proto.Term[]
    cond146 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond146
        _t706 = parse_term(parser)
        item147 = _t706
        xs145 = vcat(xs145, !isnothing(Proto.Term[item147]) ? Proto.Term[item147] : [])
        cond146 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms148 = xs145
    consume_literal!(parser, ")")
    _t707 = Proto.Pragma(; name=name144, terms=terms148)
    return _t707
end

function parse_primitive(parser::Parser)::Proto.Primitive
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "primitive", 1)
            _t709 = 9
        else
            
            if match_lookahead_literal(parser, ">=", 1)
                _t710 = 4
            else
                
                if match_lookahead_literal(parser, ">", 1)
                    _t711 = 3
                else
                    
                    if match_lookahead_literal(parser, "=", 1)
                        _t712 = 0
                    else
                        
                        if match_lookahead_literal(parser, "<=", 1)
                            _t713 = 2
                        else
                            
                            if match_lookahead_literal(parser, "<", 1)
                                _t718 = 1
                            else
                                
                                if match_lookahead_literal(parser, "/", 1)
                                    _t719 = 8
                                else
                                    
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t720 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t721 = 5
                                        else
                                            
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t722 = 7
                                            else
                                                _t722 = -1
                                            end
                                            _t721 = _t722
                                        end
                                        _t720 = _t721
                                    end
                                    _t719 = _t720
                                end
                                _t718 = _t719
                            end
                            _t713 = _t718
                        end
                        _t712 = _t713
                    end
                    _t711 = _t712
                end
                _t710 = _t711
            end
            _t709 = _t710
        end
        _t708 = _t709
    else
        _t708 = -1
    end
    prediction149 = _t708
    
    if prediction149 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t724 = parse_name(parser)
        name159 = _t724
        xs160 = Proto.RelTerm[]
        cond161 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond161
            _t725 = parse_rel_term(parser)
            item162 = _t725
            xs160 = vcat(xs160, !isnothing(Proto.RelTerm[item162]) ? Proto.RelTerm[item162] : [])
            cond161 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms163 = xs160
        consume_literal!(parser, ")")
        _t726 = Proto.Primitive(; name=name159, terms=rel_terms163)
        _t723 = _t726
    else
        
        if prediction149 == 8
            _t728 = parse_divide(parser)
            divide158 = _t728
            _t727 = divide158
        else
            
            if prediction149 == 7
                _t730 = parse_multiply(parser)
                multiply157 = _t730
                _t729 = multiply157
            else
                
                if prediction149 == 6
                    _t732 = parse_minus(parser)
                    minus156 = _t732
                    _t731 = minus156
                else
                    
                    if prediction149 == 5
                        _t734 = parse_add(parser)
                        add155 = _t734
                        _t733 = add155
                    else
                        
                        if prediction149 == 4
                            _t736 = parse_gt_eq(parser)
                            gt_eq154 = _t736
                            _t735 = gt_eq154
                        else
                            
                            if prediction149 == 3
                                _t738 = parse_gt(parser)
                                gt153 = _t738
                                _t737 = gt153
                            else
                                
                                if prediction149 == 2
                                    _t740 = parse_lt_eq(parser)
                                    lt_eq152 = _t740
                                    _t739 = lt_eq152
                                else
                                    
                                    if prediction149 == 1
                                        _t742 = parse_lt(parser)
                                        lt151 = _t742
                                        _t741 = lt151
                                    else
                                        
                                        if prediction149 == 0
                                            _t744 = parse_eq(parser)
                                            eq150 = _t744
                                            _t743 = eq150
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(current_token(parser))))
                                        end
                                        _t741 = _t743
                                    end
                                    _t739 = _t741
                                end
                                _t737 = _t739
                            end
                            _t735 = _t737
                        end
                        _t733 = _t735
                    end
                    _t731 = _t733
                end
                _t729 = _t731
            end
            _t727 = _t729
        end
        _t723 = _t727
    end
    return _t723
end

function parse_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t745 = parse_term(parser)
    term164 = _t745
    _t746 = parse_term(parser)
    term_3165 = _t746
    consume_literal!(parser, ")")
    _t747 = Proto.RelTerm(; term=term164)
    _t748 = Proto.RelTerm(; term=term_3165)
    _t749 = Proto.Primitive(; name="rel_primitive_eq", terms=Proto.RelTerm[_t747, _t748])
    return _t749
end

function parse_lt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t750 = parse_term(parser)
    term166 = _t750
    _t751 = parse_term(parser)
    term_3167 = _t751
    consume_literal!(parser, ")")
    _t752 = Proto.RelTerm(; term=term166)
    _t753 = Proto.RelTerm(; term=term_3167)
    _t754 = Proto.Primitive(; name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t752, _t753])
    return _t754
end

function parse_lt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t755 = parse_term(parser)
    term168 = _t755
    _t756 = parse_term(parser)
    term_3169 = _t756
    consume_literal!(parser, ")")
    _t757 = Proto.RelTerm(; term=term168)
    _t758 = Proto.RelTerm(; term=term_3169)
    _t759 = Proto.Primitive(; name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t757, _t758])
    return _t759
end

function parse_gt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t760 = parse_term(parser)
    term170 = _t760
    _t761 = parse_term(parser)
    term_3171 = _t761
    consume_literal!(parser, ")")
    _t762 = Proto.RelTerm(; term=term170)
    _t763 = Proto.RelTerm(; term=term_3171)
    _t764 = Proto.Primitive(; name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t762, _t763])
    return _t764
end

function parse_gt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t765 = parse_term(parser)
    term172 = _t765
    _t766 = parse_term(parser)
    term_3173 = _t766
    consume_literal!(parser, ")")
    _t767 = Proto.RelTerm(; term=term172)
    _t768 = Proto.RelTerm(; term=term_3173)
    _t769 = Proto.Primitive(; name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t767, _t768])
    return _t769
end

function parse_add(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t770 = parse_term(parser)
    term174 = _t770
    _t771 = parse_term(parser)
    term_3175 = _t771
    _t772 = parse_term(parser)
    term_4176 = _t772
    consume_literal!(parser, ")")
    _t773 = Proto.RelTerm(; term=term174)
    _t774 = Proto.RelTerm(; term=term_3175)
    _t775 = Proto.RelTerm(; term=term_4176)
    _t776 = Proto.Primitive(; name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t773, _t774, _t775])
    return _t776
end

function parse_minus(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t777 = parse_term(parser)
    term177 = _t777
    _t778 = parse_term(parser)
    term_3178 = _t778
    _t779 = parse_term(parser)
    term_4179 = _t779
    consume_literal!(parser, ")")
    _t780 = Proto.RelTerm(; term=term177)
    _t781 = Proto.RelTerm(; term=term_3178)
    _t782 = Proto.RelTerm(; term=term_4179)
    _t783 = Proto.Primitive(; name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t780, _t781, _t782])
    return _t783
end

function parse_multiply(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t784 = parse_term(parser)
    term180 = _t784
    _t785 = parse_term(parser)
    term_3181 = _t785
    _t786 = parse_term(parser)
    term_4182 = _t786
    consume_literal!(parser, ")")
    _t787 = Proto.RelTerm(; term=term180)
    _t788 = Proto.RelTerm(; term=term_3181)
    _t789 = Proto.RelTerm(; term=term_4182)
    _t790 = Proto.Primitive(; name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t787, _t788, _t789])
    return _t790
end

function parse_divide(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t791 = parse_term(parser)
    term183 = _t791
    _t792 = parse_term(parser)
    term_3184 = _t792
    _t793 = parse_term(parser)
    term_4185 = _t793
    consume_literal!(parser, ")")
    _t794 = Proto.RelTerm(; term=term183)
    _t795 = Proto.RelTerm(; term=term_3184)
    _t796 = Proto.RelTerm(; term=term_4185)
    _t797 = Proto.Primitive(; name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t794, _t795, _t796])
    return _t797
end

function parse_rel_term(parser::Parser)::Proto.RelTerm
    
    if match_lookahead_literal(parser, "true", 0)
        _t813 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t821 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t825 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t827 = 1
                else
                    
                    if match_lookahead_literal(parser, "#", 0)
                        _t828 = 0
                    else
                        _t828 = (match_lookahead_terminal(parser, "UINT128", 0) || (match_lookahead_terminal(parser, "SYMBOL", 0) || (match_lookahead_terminal(parser, "STRING", 0) || (match_lookahead_terminal(parser, "INT128", 0) || (match_lookahead_terminal(parser, "INT", 0) || (match_lookahead_terminal(parser, "FLOAT", 0) || (match_lookahead_terminal(parser, "DECIMAL", 0) || -1)))))))
                    end
                    _t827 = _t828
                end
                _t825 = _t827
            end
            _t821 = _t825
        end
        _t813 = _t821
    end
    prediction186 = _t813
    
    if prediction186 == 1
        _t830 = parse_term(parser)
        term188 = _t830
        _t831 = Proto.RelTerm(; term=term188)
        _t829 = _t831
    else
        
        if prediction186 == 0
            _t833 = parse_specialized_value(parser)
            specialized_value187 = _t833
            _t834 = Proto.RelTerm(; specialized_value=specialized_value187)
            _t832 = _t834
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(current_token(parser))))
        end
        _t829 = _t832
    end
    return _t829
end

function parse_specialized_value(parser::Parser)::Proto.Value
    consume_literal!(parser, "#")
    _t835 = parse_value(parser)
    value189 = _t835
    return value189
end

function parse_rel_atom(parser::Parser)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t836 = parse_name(parser)
    name190 = _t836
    xs191 = Proto.RelTerm[]
    cond192 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond192
        _t837 = parse_rel_term(parser)
        item193 = _t837
        xs191 = vcat(xs191, !isnothing(Proto.RelTerm[item193]) ? Proto.RelTerm[item193] : [])
        cond192 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms194 = xs191
    consume_literal!(parser, ")")
    _t838 = Proto.RelAtom(; name=name190, terms=rel_terms194)
    return _t838
end

function parse_cast(parser::Parser)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t839 = parse_term(parser)
    term195 = _t839
    _t840 = parse_term(parser)
    term_3196 = _t840
    consume_literal!(parser, ")")
    _t841 = Proto.Cast(; input=term195, result=term_3196)
    return _t841
end

function parse_attrs(parser::Parser)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs197 = Proto.Attribute[]
    cond198 = match_lookahead_literal(parser, "(", 0)
    while cond198
        _t842 = parse_attribute(parser)
        item199 = _t842
        xs197 = vcat(xs197, !isnothing(Proto.Attribute[item199]) ? Proto.Attribute[item199] : [])
        cond198 = match_lookahead_literal(parser, "(", 0)
    end
    attributes200 = xs197
    consume_literal!(parser, ")")
    return attributes200
end

function parse_attribute(parser::Parser)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t843 = parse_name(parser)
    name201 = _t843
    xs202 = Proto.Value[]
    cond203 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond203
        _t844 = parse_value(parser)
        item204 = _t844
        xs202 = vcat(xs202, !isnothing(Proto.Value[item204]) ? Proto.Value[item204] : [])
        cond203 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values205 = xs202
    consume_literal!(parser, ")")
    _t845 = Proto.Attribute(; name=name201, args=values205)
    return _t845
end

function parse_algorithm(parser::Parser)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs206 = Proto.RelationId[]
    cond207 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "INT", 0))
    while cond207
        _t846 = parse_relation_id(parser)
        item208 = _t846
        xs206 = vcat(xs206, !isnothing(Proto.RelationId[item208]) ? Proto.RelationId[item208] : [])
        cond207 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "INT", 0))
    end
    relation_ids209 = xs206
    _t847 = parse_script(parser)
    script210 = _t847
    consume_literal!(parser, ")")
    _t848 = Proto.Algorithm(; global_=relation_ids209, body=script210)
    return _t848
end

function parse_script(parser::Parser)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs211 = Proto.Construct[]
    cond212 = match_lookahead_literal(parser, "(", 0)
    while cond212
        _t849 = parse_construct(parser)
        item213 = _t849
        xs211 = vcat(xs211, !isnothing(Proto.Construct[item213]) ? Proto.Construct[item213] : [])
        cond212 = match_lookahead_literal(parser, "(", 0)
    end
    constructs214 = xs211
    consume_literal!(parser, ")")
    _t850 = Proto.Script(; constructs=constructs214)
    return _t850
end

function parse_construct(parser::Parser)::Proto.Construct
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t859 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t863 = 1
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t865 = 1
                else
                    
                    if match_lookahead_literal(parser, "loop", 1)
                        _t866 = 0
                    else
                        _t866 = (match_lookahead_literal(parser, "break", 1) || (match_lookahead_literal(parser, "assign", 1) || -1))
                    end
                    _t865 = _t866
                end
                _t863 = _t865
            end
            _t859 = _t863
        end
        _t851 = _t859
    else
        _t851 = -1
    end
    prediction215 = _t851
    
    if prediction215 == 1
        _t868 = parse_instruction(parser)
        instruction217 = _t868
        _t869 = Proto.Construct(; instruction=instruction217)
        _t867 = _t869
    else
        
        if prediction215 == 0
            _t871 = parse_loop(parser)
            loop216 = _t871
            _t872 = Proto.Construct(; loop=loop216)
            _t870 = _t872
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(current_token(parser))))
        end
        _t867 = _t870
    end
    return _t867
end

function parse_loop(parser::Parser)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t873 = parse_init(parser)
    init218 = _t873
    _t874 = parse_script(parser)
    script219 = _t874
    consume_literal!(parser, ")")
    _t875 = Proto.Loop(; init=init218, body=script219)
    return _t875
end

function parse_init(parser::Parser)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs220 = Proto.Instruction[]
    cond221 = match_lookahead_literal(parser, "(", 0)
    while cond221
        _t876 = parse_instruction(parser)
        item222 = _t876
        xs220 = vcat(xs220, !isnothing(Proto.Instruction[item222]) ? Proto.Instruction[item222] : [])
        cond221 = match_lookahead_literal(parser, "(", 0)
    end
    instructions223 = xs220
    consume_literal!(parser, ")")
    return instructions223
end

function parse_instruction(parser::Parser)::Proto.Instruction
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t882 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t883 = 4
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t884 = 3
                else
                    
                    if match_lookahead_literal(parser, "break", 1)
                        _t885 = 2
                    else
                        
                        if match_lookahead_literal(parser, "assign", 1)
                            _t886 = 0
                        else
                            _t886 = -1
                        end
                        _t885 = _t886
                    end
                    _t884 = _t885
                end
                _t883 = _t884
            end
            _t882 = _t883
        end
        _t877 = _t882
    else
        _t877 = -1
    end
    prediction224 = _t877
    
    if prediction224 == 4
        _t888 = parse_monus_def(parser)
        monus_def229 = _t888
        _t889 = Proto.Instruction(; monus_def=monus_def229)
        _t887 = _t889
    else
        
        if prediction224 == 3
            _t891 = parse_monoid_def(parser)
            monoid_def228 = _t891
            _t892 = Proto.Instruction(; monoid_def=monoid_def228)
            _t890 = _t892
        else
            
            if prediction224 == 2
                _t894 = parse_break(parser)
                break227 = _t894
                _t895 = Proto.Instruction(; break_=break227)
                _t893 = _t895
            else
                
                if prediction224 == 1
                    _t897 = parse_upsert(parser)
                    upsert226 = _t897
                    _t898 = Proto.Instruction(; upsert=upsert226)
                    _t896 = _t898
                else
                    
                    if prediction224 == 0
                        _t900 = parse_assign(parser)
                        assign225 = _t900
                        _t901 = Proto.Instruction(; assign=assign225)
                        _t899 = _t901
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(current_token(parser))))
                    end
                    _t896 = _t899
                end
                _t893 = _t896
            end
            _t890 = _t893
        end
        _t887 = _t890
    end
    return _t887
end

function parse_assign(parser::Parser)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t902 = parse_relation_id(parser)
    relation_id230 = _t902
    _t903 = parse_abstraction(parser)
    abstraction231 = _t903
    
    if match_lookahead_literal(parser, "(", 0)
        _t905 = parse_attrs(parser)
        _t904 = _t905
    else
        _t904 = nothing
    end
    attrs232 = _t904
    consume_literal!(parser, ")")
    _t906 = Proto.Assign(; name=relation_id230, body=abstraction231, attrs=(!isnothing(attrs232) ? attrs232 : Never[]))
    return _t906
end

function parse_upsert(parser::Parser)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t907 = parse_relation_id(parser)
    relation_id233 = _t907
    _t908 = parse_abstraction_with_arity(parser)
    abstraction_with_arity234 = _t908
    
    if match_lookahead_literal(parser, "(", 0)
        _t910 = parse_attrs(parser)
        _t909 = _t910
    else
        _t909 = nothing
    end
    attrs235 = _t909
    consume_literal!(parser, ")")
    _t911 = Proto.Upsert(; name=relation_id233, body=abstraction_with_arity234[1], attrs=(!isnothing(attrs235) ? attrs235 : Never[]), value_arity=abstraction_with_arity234[2])
    return _t911
end

function parse_abstraction_with_arity(parser::Parser)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t912 = parse_bindings(parser)
    bindings236 = _t912
    _t913 = parse_formula(parser)
    formula237 = _t913
    consume_literal!(parser, ")")
    _t914 = Proto.Abstraction(; vars=vcat(bindings236[1], !isnothing(bindings236[2]) ? bindings236[2] : []), value=formula237)
    return (_t914, length(bindings236[2]),)
end

function parse_break(parser::Parser)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t915 = parse_relation_id(parser)
    relation_id238 = _t915
    _t916 = parse_abstraction(parser)
    abstraction239 = _t916
    
    if match_lookahead_literal(parser, "(", 0)
        _t918 = parse_attrs(parser)
        _t917 = _t918
    else
        _t917 = nothing
    end
    attrs240 = _t917
    consume_literal!(parser, ")")
    _t919 = Proto.Break(; name=relation_id238, body=abstraction239, attrs=(!isnothing(attrs240) ? attrs240 : Never[]))
    return _t919
end

function parse_monoid_def(parser::Parser)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t920 = parse_monoid(parser)
    monoid241 = _t920
    _t921 = parse_relation_id(parser)
    relation_id242 = _t921
    _t922 = parse_abstraction_with_arity(parser)
    abstraction_with_arity243 = _t922
    
    if match_lookahead_literal(parser, "(", 0)
        _t924 = parse_attrs(parser)
        _t923 = _t924
    else
        _t923 = nothing
    end
    attrs244 = _t923
    consume_literal!(parser, ")")
    _t925 = Proto.MonoidDef(; monoid=monoid241, name=relation_id242, body=abstraction_with_arity243[1], attrs=(!isnothing(attrs244) ? attrs244 : Never[]), value_arity=abstraction_with_arity243[2])
    return _t925
end

function parse_monoid(parser::Parser)::Proto.Monoid
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "sum", 1)
            _t927 = 3
        else
            
            if match_lookahead_literal(parser, "or", 1)
                _t928 = 0
            else
                
                if match_lookahead_literal(parser, "min", 1)
                    _t930 = 1
                else
                    
                    if match_lookahead_literal(parser, "max", 1)
                        _t931 = 2
                    else
                        _t931 = -1
                    end
                    _t930 = _t931
                end
                _t928 = _t930
            end
            _t927 = _t928
        end
        _t926 = _t927
    else
        _t926 = -1
    end
    prediction245 = _t926
    
    if prediction245 == 3
        _t933 = parse_sum_monoid(parser)
        sum_monoid249 = _t933
        _t934 = Proto.Monoid(; sum_monoid=sum_monoid249)
        _t932 = _t934
    else
        
        if prediction245 == 2
            _t936 = parse_max_monoid(parser)
            max_monoid248 = _t936
            _t937 = Proto.Monoid(; max_monoid=max_monoid248)
            _t935 = _t937
        else
            
            if prediction245 == 1
                _t939 = parse_min_monoid(parser)
                min_monoid247 = _t939
                _t940 = Proto.Monoid(; min_monoid=min_monoid247)
                _t938 = _t940
            else
                
                if prediction245 == 0
                    _t942 = parse_or_monoid(parser)
                    or_monoid246 = _t942
                    _t943 = Proto.Monoid(; or_monoid=or_monoid246)
                    _t941 = _t943
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(current_token(parser))))
                end
                _t938 = _t941
            end
            _t935 = _t938
        end
        _t932 = _t935
    end
    return _t932
end

function parse_or_monoid(parser::Parser)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t944 = Proto.OrMonoid()
    return _t944
end

function parse_min_monoid(parser::Parser)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t945 = parse_type(parser)
    type250 = _t945
    consume_literal!(parser, ")")
    _t946 = Proto.MinMonoid(; type_=type250)
    return _t946
end

function parse_max_monoid(parser::Parser)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t947 = parse_type(parser)
    type251 = _t947
    consume_literal!(parser, ")")
    _t948 = Proto.MaxMonoid(; type_=type251)
    return _t948
end

function parse_sum_monoid(parser::Parser)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t949 = parse_type(parser)
    type252 = _t949
    consume_literal!(parser, ")")
    _t950 = Proto.SumMonoid(; type_=type252)
    return _t950
end

function parse_monus_def(parser::Parser)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t951 = parse_monoid(parser)
    monoid253 = _t951
    _t952 = parse_relation_id(parser)
    relation_id254 = _t952
    _t953 = parse_abstraction_with_arity(parser)
    abstraction_with_arity255 = _t953
    
    if match_lookahead_literal(parser, "(", 0)
        _t955 = parse_attrs(parser)
        _t954 = _t955
    else
        _t954 = nothing
    end
    attrs256 = _t954
    consume_literal!(parser, ")")
    _t956 = Proto.MonusDef(; monoid=monoid253, name=relation_id254, body=abstraction_with_arity255[1], attrs=(!isnothing(attrs256) ? attrs256 : Never[]), value_arity=abstraction_with_arity255[2])
    return _t956
end

function parse_constraint(parser::Parser)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t957 = parse_relation_id(parser)
    relation_id257 = _t957
    _t958 = parse_abstraction(parser)
    abstraction258 = _t958
    _t959 = parse_functional_dependency_keys(parser)
    functional_dependency_keys259 = _t959
    _t960 = parse_functional_dependency_values(parser)
    functional_dependency_values260 = _t960
    consume_literal!(parser, ")")
    _t961 = Proto.FunctionalDependency(; guard=abstraction258, keys=functional_dependency_keys259, values=functional_dependency_values260)
    _t962 = Proto.Constraint(; name=relation_id257, functional_dependency=_t961)
    return _t962
end

function parse_functional_dependency_keys(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs261 = Proto.Var[]
    cond262 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond262
        _t963 = parse_var(parser)
        item263 = _t963
        xs261 = vcat(xs261, !isnothing(Proto.Var[item263]) ? Proto.Var[item263] : [])
        cond262 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars264 = xs261
    consume_literal!(parser, ")")
    return vars264
end

function parse_functional_dependency_values(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs265 = Proto.Var[]
    cond266 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond266
        _t964 = parse_var(parser)
        item267 = _t964
        xs265 = vcat(xs265, !isnothing(Proto.Var[item267]) ? Proto.Var[item267] : [])
        cond266 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars268 = xs265
    consume_literal!(parser, ")")
    return vars268
end

function parse_data(parser::Parser)::Proto.Data
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t966 = 0
        else
            
            if match_lookahead_literal(parser, "csv_data", 1)
                _t967 = 2
            else
                _t967 = (match_lookahead_literal(parser, "betree_relation", 1) || -1)
            end
            _t966 = _t967
        end
        _t965 = _t966
    else
        _t965 = -1
    end
    prediction269 = _t965
    
    if prediction269 == 2
        _t969 = parse_csv_data(parser)
        csv_data272 = _t969
        _t970 = Proto.Data(; csv_data=csv_data272)
        _t968 = _t970
    else
        
        if prediction269 == 1
            _t972 = parse_betree_relation(parser)
            betree_relation271 = _t972
            _t973 = Proto.Data(; betree_relation=betree_relation271)
            _t971 = _t973
        else
            
            if prediction269 == 0
                _t975 = parse_rel_edb(parser)
                rel_edb270 = _t975
                _t976 = Proto.Data(; rel_edb=rel_edb270)
                _t974 = _t976
            else
                throw(ParseError("Unexpected token in data" * ": " * string(current_token(parser))))
            end
            _t971 = _t974
        end
        _t968 = _t971
    end
    return _t968
end

function parse_rel_edb(parser::Parser)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t977 = parse_relation_id(parser)
    relation_id273 = _t977
    _t978 = parse_rel_edb_path(parser)
    rel_edb_path274 = _t978
    _t979 = parse_rel_edb_types(parser)
    rel_edb_types275 = _t979
    consume_literal!(parser, ")")
    _t980 = Proto.RelEDB(; target_id=relation_id273, path=rel_edb_path274, types=rel_edb_types275)
    return _t980
end

function parse_rel_edb_path(parser::Parser)::Vector{String}
    consume_literal!(parser, "[")
    xs276 = String[]
    cond277 = match_lookahead_terminal(parser, "STRING", 0)
    while cond277
        item278 = consume_terminal!(parser, "STRING")
        xs276 = vcat(xs276, !isnothing(String[item278]) ? String[item278] : [])
        cond277 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings279 = xs276
    consume_literal!(parser, "]")
    return strings279
end

function parse_rel_edb_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs280 = Proto.var"#Type"[]
    cond281 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond281
        _t981 = parse_type(parser)
        item282 = _t981
        xs280 = vcat(xs280, !isnothing(Proto.var"#Type"[item282]) ? Proto.var"#Type"[item282] : [])
        cond281 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types283 = xs280
    consume_literal!(parser, "]")
    return types283
end

function parse_betree_relation(parser::Parser)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t982 = parse_relation_id(parser)
    relation_id284 = _t982
    _t983 = parse_betree_info(parser)
    betree_info285 = _t983
    consume_literal!(parser, ")")
    _t984 = Proto.BeTreeRelation(; name=relation_id284, relation_info=betree_info285)
    return _t984
end

function parse_betree_info(parser::Parser)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t985 = parse_betree_info_key_types(parser)
    betree_info_key_types286 = _t985
    _t986 = parse_betree_info_value_types(parser)
    betree_info_value_types287 = _t986
    _t987 = parse_config_dict(parser)
    config_dict288 = _t987
    consume_literal!(parser, ")")
    _t988 = Parser.construct_betree_info(betree_info_key_types286, betree_info_value_types287, config_dict288)
    return _t988
end

function parse_betree_info_key_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs289 = Proto.var"#Type"[]
    cond290 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond290
        _t989 = parse_type(parser)
        item291 = _t989
        xs289 = vcat(xs289, !isnothing(Proto.var"#Type"[item291]) ? Proto.var"#Type"[item291] : [])
        cond290 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types292 = xs289
    consume_literal!(parser, ")")
    return types292
end

function parse_betree_info_value_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs293 = Proto.var"#Type"[]
    cond294 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond294
        _t990 = parse_type(parser)
        item295 = _t990
        xs293 = vcat(xs293, !isnothing(Proto.var"#Type"[item295]) ? Proto.var"#Type"[item295] : [])
        cond294 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types296 = xs293
    consume_literal!(parser, ")")
    return types296
end

function parse_csv_data(parser::Parser)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t991 = parse_csvlocator(parser)
    csvlocator297 = _t991
    _t992 = parse_csv_config(parser)
    csv_config298 = _t992
    _t993 = parse_csv_columns(parser)
    csv_columns299 = _t993
    _t994 = parse_csv_asof(parser)
    csv_asof300 = _t994
    consume_literal!(parser, ")")
    _t995 = Proto.CSVData(; locator=csvlocator297, config=csv_config298, columns=csv_columns299, asof=csv_asof300)
    return _t995
end

function parse_csvlocator(parser::Parser)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t997 = parse_csv_locator_paths(parser)
        _t996 = _t997
    else
        _t996 = nothing
    end
    csv_locator_paths301 = _t996
    
    if match_lookahead_literal(parser, "(", 0)
        _t999 = parse_csv_locator_inline_data(parser)
        _t998 = _t999
    else
        _t998 = nothing
    end
    csv_locator_inline_data302 = _t998
    consume_literal!(parser, ")")
    _t1000 = Proto.CSVLocator(; paths=(!isnothing(csv_locator_paths301) ? csv_locator_paths301 : Never[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data302) ? csv_locator_inline_data302 : "")))
    return _t1000
end

function parse_csv_locator_paths(parser::Parser)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs303 = String[]
    cond304 = match_lookahead_terminal(parser, "STRING", 0)
    while cond304
        item305 = consume_terminal!(parser, "STRING")
        xs303 = vcat(xs303, !isnothing(String[item305]) ? String[item305] : [])
        cond304 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings306 = xs303
    consume_literal!(parser, ")")
    return strings306
end

function parse_csv_locator_inline_data(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string307 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string307
end

function parse_csv_config(parser::Parser)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1001 = parse_config_dict(parser)
    config_dict308 = _t1001
    consume_literal!(parser, ")")
    _t1002 = Parser.construct_csv_config(config_dict308)
    return _t1002
end

function parse_csv_columns(parser::Parser)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs309 = Proto.CSVColumn[]
    cond310 = match_lookahead_literal(parser, "(", 0)
    while cond310
        _t1003 = parse_csv_column(parser)
        item311 = _t1003
        xs309 = vcat(xs309, !isnothing(Proto.CSVColumn[item311]) ? Proto.CSVColumn[item311] : [])
        cond310 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns312 = xs309
    consume_literal!(parser, ")")
    return csv_columns312
end

function parse_csv_column(parser::Parser)::Proto.CSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string313 = consume_terminal!(parser, "STRING")
    _t1004 = parse_relation_id(parser)
    relation_id314 = _t1004
    consume_literal!(parser, "[")
    xs315 = Proto.var"#Type"[]
    cond316 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond316
        _t1005 = parse_type(parser)
        item317 = _t1005
        xs315 = vcat(xs315, !isnothing(Proto.var"#Type"[item317]) ? Proto.var"#Type"[item317] : [])
        cond316 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types318 = xs315
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1006 = Proto.CSVColumn(; column_name=string313, target_id=relation_id314, types=types318)
    return _t1006
end

function parse_csv_asof(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string319 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string319
end

function parse_undefine(parser::Parser)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1007 = parse_fragment_id(parser)
    fragment_id320 = _t1007
    consume_literal!(parser, ")")
    _t1008 = Proto.Undefine(; fragment_id=fragment_id320)
    return _t1008
end

function parse_context(parser::Parser)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs321 = Proto.RelationId[]
    cond322 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "INT", 0))
    while cond322
        _t1009 = parse_relation_id(parser)
        item323 = _t1009
        xs321 = vcat(xs321, !isnothing(Proto.RelationId[item323]) ? Proto.RelationId[item323] : [])
        cond322 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "INT", 0))
    end
    relation_ids324 = xs321
    consume_literal!(parser, ")")
    _t1010 = Proto.Context(; relations=relation_ids324)
    return _t1010
end

function parse_epoch_reads(parser::Parser)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs325 = Proto.Read[]
    cond326 = match_lookahead_literal(parser, "(", 0)
    while cond326
        _t1011 = parse_read(parser)
        item327 = _t1011
        xs325 = vcat(xs325, !isnothing(Proto.Read[item327]) ? Proto.Read[item327] : [])
        cond326 = match_lookahead_literal(parser, "(", 0)
    end
    reads328 = xs325
    consume_literal!(parser, ")")
    return reads328
end

function parse_read(parser::Parser)::Proto.Read
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "what_if", 1)
            _t1013 = 2
        else
            
            if match_lookahead_literal(parser, "output", 1)
                _t1017 = 1
            else
                
                if match_lookahead_literal(parser, "export", 1)
                    _t1018 = 4
                else
                    
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1019 = 0
                    else
                        
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1020 = 3
                        else
                            _t1020 = -1
                        end
                        _t1019 = _t1020
                    end
                    _t1018 = _t1019
                end
                _t1017 = _t1018
            end
            _t1013 = _t1017
        end
        _t1012 = _t1013
    else
        _t1012 = -1
    end
    prediction329 = _t1012
    
    if prediction329 == 4
        _t1022 = parse_export(parser)
        export334 = _t1022
        _t1023 = Proto.Read(; export_=export334)
        _t1021 = _t1023
    else
        
        if prediction329 == 3
            _t1025 = parse_abort(parser)
            abort333 = _t1025
            _t1026 = Proto.Read(; abort=abort333)
            _t1024 = _t1026
        else
            
            if prediction329 == 2
                _t1028 = parse_what_if(parser)
                what_if332 = _t1028
                _t1029 = Proto.Read(; what_if=what_if332)
                _t1027 = _t1029
            else
                
                if prediction329 == 1
                    _t1031 = parse_output(parser)
                    output331 = _t1031
                    _t1032 = Proto.Read(; output=output331)
                    _t1030 = _t1032
                else
                    
                    if prediction329 == 0
                        _t1034 = parse_demand(parser)
                        demand330 = _t1034
                        _t1035 = Proto.Read(; demand=demand330)
                        _t1033 = _t1035
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(current_token(parser))))
                    end
                    _t1030 = _t1033
                end
                _t1027 = _t1030
            end
            _t1024 = _t1027
        end
        _t1021 = _t1024
    end
    return _t1021
end

function parse_demand(parser::Parser)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1036 = parse_relation_id(parser)
    relation_id335 = _t1036
    consume_literal!(parser, ")")
    _t1037 = Proto.Demand(; relation_id=relation_id335)
    return _t1037
end

function parse_output(parser::Parser)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1039 = parse_name(parser)
        _t1038 = _t1039
    else
        _t1038 = nothing
    end
    name336 = _t1038
    _t1040 = parse_relation_id(parser)
    relation_id337 = _t1040
    consume_literal!(parser, ")")
    _t1041 = Proto.Output(; name=(!isnothing(name336) ? name336 : "output"), relation_id=relation_id337)
    return _t1041
end

function parse_what_if(parser::Parser)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1042 = parse_name(parser)
    name338 = _t1042
    _t1043 = parse_epoch(parser)
    epoch339 = _t1043
    consume_literal!(parser, ")")
    _t1044 = Proto.WhatIf(; branch=name338, epoch=epoch339)
    return _t1044
end

function parse_abort(parser::Parser)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1046 = parse_name(parser)
        _t1045 = _t1046
    else
        _t1045 = nothing
    end
    name340 = _t1045
    _t1047 = parse_relation_id(parser)
    relation_id341 = _t1047
    consume_literal!(parser, ")")
    _t1048 = Proto.Abort(; name=(!isnothing(name340) ? name340 : "abort"), relation_id=relation_id341)
    return _t1048
end

function parse_export(parser::Parser)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1049 = parse_export_csv_config(parser)
    export_csv_config342 = _t1049
    consume_literal!(parser, ")")
    _t1050 = Proto.Export(; csv_config=export_csv_config342)
    return _t1050
end

function parse_export_csv_config(parser::Parser)::Proto.ExportCSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1051 = parse_export_csv_path(parser)
    export_csv_path343 = _t1051
    _t1052 = parse_export_csv_columns(parser)
    export_csv_columns344 = _t1052
    _t1053 = parse_config_dict(parser)
    config_dict345 = _t1053
    consume_literal!(parser, ")")
    _t1054 = Parser.export_csv_config(export_csv_path343, export_csv_columns344, config_dict345)
    return _t1054
end

function parse_export_csv_path(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string346 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string346
end

function parse_export_csv_columns(parser::Parser)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs347 = Proto.ExportCSVColumn[]
    cond348 = match_lookahead_literal(parser, "(", 0)
    while cond348
        _t1055 = parse_export_csv_column(parser)
        item349 = _t1055
        xs347 = vcat(xs347, !isnothing(Proto.ExportCSVColumn[item349]) ? Proto.ExportCSVColumn[item349] : [])
        cond348 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns350 = xs347
    consume_literal!(parser, ")")
    return export_csv_columns350
end

function parse_export_csv_column(parser::Parser)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string351 = consume_terminal!(parser, "STRING")
    _t1056 = parse_relation_id(parser)
    relation_id352 = _t1056
    consume_literal!(parser, ")")
    _t1057 = Proto.ExportCSVColumn(; column_name=string351, column_data=relation_id352)
    return _t1057
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
