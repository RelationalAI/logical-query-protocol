"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `meta/` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --parser julia
"""

using SHA
using ProtoBuf: OneOf

# Import protobuf modules
include("proto_generated.jl")
using .Proto


function _has_proto_field(obj, field_sym::Symbol)::Bool
    if hasproperty(obj, field_sym)
        return !isnothing(getproperty(obj, field_sym))
    end
    for fname in fieldnames(typeof(obj))
        fval = getfield(obj, fname)
        if fval isa OneOf && fval.name == field_sym
            return true
        end
    end
    return false
end

function _get_oneof_field(obj, field_sym::Symbol)
    for fname in fieldnames(typeof(obj))
        fval = getfield(obj, fname)
        if fval isa OneOf && fval.name == field_sym
            return fval[]
        end
    end
    error("No oneof field $field_sym on $(typeof(obj))")
end


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

    # Use ncodeunits for byte-based position tracking (UTF-8 safe)
    while lexer.pos <= ncodeunits(lexer.input)
        # Skip whitespace
        m = match(whitespace_re, lexer.input, lexer.pos)
        if m !== nothing && m.offset == lexer.pos
            lexer.pos = m.offset + ncodeunits(m.match)
            continue
        end

        # Skip comments
        m = match(comment_re, lexer.input, lexer.pos)
        if m !== nothing && m.offset == lexer.pos
            lexer.pos = m.offset + ncodeunits(m.match)
            continue
        end

        # Collect all matching tokens
        candidates = Tuple{String,String,Function,Int}[]

        for (token_type, regex, action) in token_specs
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


# Scanner functions for each token type
scan_symbol(s::String) = s
scan_colon_symbol(s::String) = chop(s, head=1, tail=0)

function scan_string(s::String)
    # Strip quotes using Unicode-safe chop (handles multi-byte characters)
    content = chop(s, head=1, tail=1)
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
    id_to_debuginfo::Dict{Vector{UInt8},Vector{Pair{Tuple{UInt64,UInt64},String}}}
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
    parser::Parser,
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

function construct_configure(parser::Parser, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.Configure
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
    _t972 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t972
    _t973 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t973
    _t974 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t974
end

function default_configure(parser::Parser)::Proto.Configure
    _t975 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t975
    _t976 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t976
end

function construct_export_csv_config_with_source(parser::Parser, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t977 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t977
end

function _extract_value_string(parser::Parser, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    end
    return default
end

function _extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    end
    return default
end

function _extract_value_int32(parser::Parser, value::Union{Nothing, Proto.Value}, default::Int64)::Int32
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return Int32(_get_oneof_field(value, :int_value))
    end
    return Int32(default)
end

function _try_extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    end
    return nothing
end

function _try_extract_value_bytes(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    end
    return nothing
end

function _extract_value_boolean(parser::Parser, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    end
    return default
end

function construct_export_csv_config(parser::Parser, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t978 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t978
    _t979 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t979
    _t980 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t980
    _t981 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t981
    _t982 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t982
    _t983 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t983
    _t984 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t984
    _t985 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t985
end

function _extract_value_string_list(parser::Parser, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    end
    return default
end

function _try_extract_value_uint128(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    end
    return nothing
end

function construct_csv_config(parser::Parser, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t986 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t986
    _t987 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t987
    _t988 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t988
    _t989 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t989
    _t990 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t990
    _t991 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t991
    _t992 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t992
    _t993 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t993
    _t994 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t994
    _t995 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t995
    _t996 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t996
    _t997 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size = _t997
    _t998 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size)
    return _t998
end

function _try_extract_value_float64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    end
    return nothing
end

function construct_betree_info(parser::Parser, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t999 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t999
    _t1000 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1000
    _t1001 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1001
    _t1002 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1002
    _t1003 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1003
    _t1004 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1004
    _t1005 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1005
    _t1006 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1006
    _t1007 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1007
    _t1008 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1008
    _t1009 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1009
end

# --- Parse functions ---

function parse_transaction(parser::Parser)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t363 = parse_configure(parser)
        _t362 = _t363
    else
        _t362 = nothing
    end
    configure0 = _t362
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t365 = parse_sync(parser)
        _t364 = _t365
    else
        _t364 = nothing
    end
    sync1 = _t364
    xs2 = Proto.Epoch[]
    cond3 = match_lookahead_literal(parser, "(", 0)
    while cond3
        _t366 = parse_epoch(parser)
        item4 = _t366
        push!(xs2, item4)
        cond3 = match_lookahead_literal(parser, "(", 0)
    end
    epochs5 = xs2
    consume_literal!(parser, ")")
    _t367 = default_configure(parser)
    _t368 = Proto.Transaction(epochs=epochs5, configure=(!isnothing(configure0) ? configure0 : _t367), sync=sync1)
    return _t368
end

function parse_configure(parser::Parser)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t369 = parse_config_dict(parser)
    config_dict6 = _t369
    consume_literal!(parser, ")")
    _t370 = construct_configure(parser, config_dict6)
    return _t370
end

function parse_config_dict(parser::Parser)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs7 = Tuple{String, Proto.Value}[]
    cond8 = match_lookahead_literal(parser, ":", 0)
    while cond8
        _t371 = parse_config_key_value(parser)
        item9 = _t371
        push!(xs7, item9)
        cond8 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values10 = xs7
    consume_literal!(parser, "}")
    return config_key_values10
end

function parse_config_key_value(parser::Parser)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol11 = consume_terminal!(parser, "SYMBOL")
    _t372 = parse_value(parser)
    value12 = _t372
    return (symbol11, value12,)
end

function parse_value(parser::Parser)::Proto.Value
    
    if match_lookahead_literal(parser, "true", 0)
        _t373 = 9
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t374 = 8
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t375 = 9
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t377 = 1
                    else
                        
                        if match_lookahead_literal(parser, "date", 1)
                            _t378 = 0
                        else
                            _t378 = -1
                        end
                        _t377 = _t378
                    end
                    _t376 = _t377
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t379 = 5
                    else
                        
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t380 = 2
                        else
                            
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t381 = 6
                            else
                                
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t382 = 3
                                else
                                    
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t383 = 4
                                    else
                                        
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t384 = 7
                                        else
                                            _t384 = -1
                                        end
                                        _t383 = _t384
                                    end
                                    _t382 = _t383
                                end
                                _t381 = _t382
                            end
                            _t380 = _t381
                        end
                        _t379 = _t380
                    end
                    _t376 = _t379
                end
                _t375 = _t376
            end
            _t374 = _t375
        end
        _t373 = _t374
    end
    prediction13 = _t373
    
    if prediction13 == 9
        _t386 = parse_boolean_value(parser)
        boolean_value22 = _t386
        _t387 = Proto.Value(value=OneOf(:boolean_value, boolean_value22))
        _t385 = _t387
    else
        
        if prediction13 == 8
            consume_literal!(parser, "missing")
            _t389 = Proto.MissingValue()
            _t390 = Proto.Value(value=OneOf(:missing_value, _t389))
            _t388 = _t390
        else
            
            if prediction13 == 7
                decimal21 = consume_terminal!(parser, "DECIMAL")
                _t392 = Proto.Value(value=OneOf(:decimal_value, decimal21))
                _t391 = _t392
            else
                
                if prediction13 == 6
                    int12820 = consume_terminal!(parser, "INT128")
                    _t394 = Proto.Value(value=OneOf(:int128_value, int12820))
                    _t393 = _t394
                else
                    
                    if prediction13 == 5
                        uint12819 = consume_terminal!(parser, "UINT128")
                        _t396 = Proto.Value(value=OneOf(:uint128_value, uint12819))
                        _t395 = _t396
                    else
                        
                        if prediction13 == 4
                            float18 = consume_terminal!(parser, "FLOAT")
                            _t398 = Proto.Value(value=OneOf(:float_value, float18))
                            _t397 = _t398
                        else
                            
                            if prediction13 == 3
                                int17 = consume_terminal!(parser, "INT")
                                _t400 = Proto.Value(value=OneOf(:int_value, int17))
                                _t399 = _t400
                            else
                                
                                if prediction13 == 2
                                    string16 = consume_terminal!(parser, "STRING")
                                    _t402 = Proto.Value(value=OneOf(:string_value, string16))
                                    _t401 = _t402
                                else
                                    
                                    if prediction13 == 1
                                        _t404 = parse_datetime(parser)
                                        datetime15 = _t404
                                        _t405 = Proto.Value(value=OneOf(:datetime_value, datetime15))
                                        _t403 = _t405
                                    else
                                        
                                        if prediction13 == 0
                                            _t407 = parse_date(parser)
                                            date14 = _t407
                                            _t408 = Proto.Value(value=OneOf(:date_value, date14))
                                            _t406 = _t408
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t403 = _t406
                                    end
                                    _t401 = _t403
                                end
                                _t399 = _t401
                            end
                            _t397 = _t399
                        end
                        _t395 = _t397
                    end
                    _t393 = _t395
                end
                _t391 = _t393
            end
            _t388 = _t391
        end
        _t385 = _t388
    end
    return _t385
end

function parse_date(parser::Parser)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int23 = consume_terminal!(parser, "INT")
    int_324 = consume_terminal!(parser, "INT")
    int_425 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t409 = Proto.DateValue(year=Int32(int23), month=Int32(int_324), day=Int32(int_425))
    return _t409
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
        _t410 = consume_terminal!(parser, "INT")
    else
        _t410 = nothing
    end
    int_832 = _t410
    consume_literal!(parser, ")")
    _t411 = Proto.DateTimeValue(year=Int32(int26), month=Int32(int_327), day=Int32(int_428), hour=Int32(int_529), minute=Int32(int_630), second=Int32(int_731), microsecond=Int32((!isnothing(int_832) ? int_832 : 0)))
    return _t411
end

function parse_boolean_value(parser::Parser)::Bool
    
    if match_lookahead_literal(parser, "true", 0)
        _t412 = 0
    else
        
        if match_lookahead_literal(parser, "false", 0)
            _t413 = 1
        else
            _t413 = -1
        end
        _t412 = _t413
    end
    prediction33 = _t412
    
    if prediction33 == 1
        consume_literal!(parser, "false")
        _t414 = false
    else
        
        if prediction33 == 0
            consume_literal!(parser, "true")
            _t415 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t414 = _t415
    end
    return _t414
end

function parse_sync(parser::Parser)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs34 = Proto.FragmentId[]
    cond35 = match_lookahead_literal(parser, ":", 0)
    while cond35
        _t416 = parse_fragment_id(parser)
        item36 = _t416
        push!(xs34, item36)
        cond35 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids37 = xs34
    consume_literal!(parser, ")")
    _t417 = Proto.Sync(fragments=fragment_ids37)
    return _t417
end

function parse_fragment_id(parser::Parser)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol38 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol38))
end

function parse_epoch(parser::Parser)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t419 = parse_epoch_writes(parser)
        _t418 = _t419
    else
        _t418 = nothing
    end
    epoch_writes39 = _t418
    
    if match_lookahead_literal(parser, "(", 0)
        _t421 = parse_epoch_reads(parser)
        _t420 = _t421
    else
        _t420 = nothing
    end
    epoch_reads40 = _t420
    consume_literal!(parser, ")")
    _t422 = Proto.Epoch(writes=(!isnothing(epoch_writes39) ? epoch_writes39 : Proto.Write[]), reads=(!isnothing(epoch_reads40) ? epoch_reads40 : Proto.Read[]))
    return _t422
end

function parse_epoch_writes(parser::Parser)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs41 = Proto.Write[]
    cond42 = match_lookahead_literal(parser, "(", 0)
    while cond42
        _t423 = parse_write(parser)
        item43 = _t423
        push!(xs41, item43)
        cond42 = match_lookahead_literal(parser, "(", 0)
    end
    writes44 = xs41
    consume_literal!(parser, ")")
    return writes44
end

function parse_write(parser::Parser)::Proto.Write
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "undefine", 1)
            _t425 = 1
        else
            
            if match_lookahead_literal(parser, "define", 1)
                _t426 = 0
            else
                
                if match_lookahead_literal(parser, "context", 1)
                    _t427 = 2
                else
                    _t427 = -1
                end
                _t426 = _t427
            end
            _t425 = _t426
        end
        _t424 = _t425
    else
        _t424 = -1
    end
    prediction45 = _t424
    
    if prediction45 == 2
        _t429 = parse_context(parser)
        context48 = _t429
        _t430 = Proto.Write(write_type=OneOf(:context, context48))
        _t428 = _t430
    else
        
        if prediction45 == 1
            _t432 = parse_undefine(parser)
            undefine47 = _t432
            _t433 = Proto.Write(write_type=OneOf(:undefine, undefine47))
            _t431 = _t433
        else
            
            if prediction45 == 0
                _t435 = parse_define(parser)
                define46 = _t435
                _t436 = Proto.Write(write_type=OneOf(:define, define46))
                _t434 = _t436
            else
                throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
            end
            _t431 = _t434
        end
        _t428 = _t431
    end
    return _t428
end

function parse_define(parser::Parser)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t437 = parse_fragment(parser)
    fragment49 = _t437
    consume_literal!(parser, ")")
    _t438 = Proto.Define(fragment=fragment49)
    return _t438
end

function parse_fragment(parser::Parser)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t439 = parse_new_fragment_id(parser)
    new_fragment_id50 = _t439
    xs51 = Proto.Declaration[]
    cond52 = match_lookahead_literal(parser, "(", 0)
    while cond52
        _t440 = parse_declaration(parser)
        item53 = _t440
        push!(xs51, item53)
        cond52 = match_lookahead_literal(parser, "(", 0)
    end
    declarations54 = xs51
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id50, declarations54)
end

function parse_new_fragment_id(parser::Parser)::Proto.FragmentId
    _t441 = parse_fragment_id(parser)
    fragment_id55 = _t441
    start_fragment!(parser, fragment_id55)
    return fragment_id55
end

function parse_declaration(parser::Parser)::Proto.Declaration
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t443 = 3
        else
            
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t444 = 2
            else
                
                if match_lookahead_literal(parser, "def", 1)
                    _t445 = 0
                else
                    
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t446 = 3
                    else
                        
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t447 = 3
                        else
                            
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t448 = 1
                            else
                                _t448 = -1
                            end
                            _t447 = _t448
                        end
                        _t446 = _t447
                    end
                    _t445 = _t446
                end
                _t444 = _t445
            end
            _t443 = _t444
        end
        _t442 = _t443
    else
        _t442 = -1
    end
    prediction56 = _t442
    
    if prediction56 == 3
        _t450 = parse_data(parser)
        data60 = _t450
        _t451 = Proto.Declaration(declaration_type=OneOf(:data, data60))
        _t449 = _t451
    else
        
        if prediction56 == 2
            _t453 = parse_constraint(parser)
            constraint59 = _t453
            _t454 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint59))
            _t452 = _t454
        else
            
            if prediction56 == 1
                _t456 = parse_algorithm(parser)
                algorithm58 = _t456
                _t457 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm58))
                _t455 = _t457
            else
                
                if prediction56 == 0
                    _t459 = parse_def(parser)
                    def57 = _t459
                    _t460 = Proto.Declaration(declaration_type=OneOf(:def, def57))
                    _t458 = _t460
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t455 = _t458
            end
            _t452 = _t455
        end
        _t449 = _t452
    end
    return _t449
end

function parse_def(parser::Parser)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t461 = parse_relation_id(parser)
    relation_id61 = _t461
    _t462 = parse_abstraction(parser)
    abstraction62 = _t462
    
    if match_lookahead_literal(parser, "(", 0)
        _t464 = parse_attrs(parser)
        _t463 = _t464
    else
        _t463 = nothing
    end
    attrs63 = _t463
    consume_literal!(parser, ")")
    _t465 = Proto.Def(name=relation_id61, body=abstraction62, attrs=(!isnothing(attrs63) ? attrs63 : Proto.Attribute[]))
    return _t465
end

function parse_relation_id(parser::Parser)::Proto.RelationId
    
    if match_lookahead_literal(parser, ":", 0)
        _t466 = 0
    else
        
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t467 = 1
        else
            _t467 = -1
        end
        _t466 = _t467
    end
    prediction64 = _t466
    
    if prediction64 == 1
        uint12866 = consume_terminal!(parser, "UINT128")
        _t468 = Proto.RelationId(uint12866.low, uint12866.high)
    else
        
        if prediction64 == 0
            consume_literal!(parser, ":")
            symbol65 = consume_terminal!(parser, "SYMBOL")
            _t469 = relation_id_from_string(parser, symbol65)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t468 = _t469
    end
    return _t468
end

function parse_abstraction(parser::Parser)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t470 = parse_bindings(parser)
    bindings67 = _t470
    _t471 = parse_formula(parser)
    formula68 = _t471
    consume_literal!(parser, ")")
    _t472 = Proto.Abstraction(vars=vcat(bindings67[1], !isnothing(bindings67[2]) ? bindings67[2] : []), value=formula68)
    return _t472
end

function parse_bindings(parser::Parser)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs69 = Proto.Binding[]
    cond70 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond70
        _t473 = parse_binding(parser)
        item71 = _t473
        push!(xs69, item71)
        cond70 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings72 = xs69
    
    if match_lookahead_literal(parser, "|", 0)
        _t475 = parse_value_bindings(parser)
        _t474 = _t475
    else
        _t474 = nothing
    end
    value_bindings73 = _t474
    consume_literal!(parser, "]")
    return (bindings72, (!isnothing(value_bindings73) ? value_bindings73 : Proto.Binding[]),)
end

function parse_binding(parser::Parser)::Proto.Binding
    symbol74 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t476 = parse_type(parser)
    type75 = _t476
    _t477 = Proto.Var(name=symbol74)
    _t478 = Proto.Binding(var=_t477, var"#type"=type75)
    return _t478
end

function parse_type(parser::Parser)::Proto.var"#Type"
    
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t479 = 0
    else
        
        if match_lookahead_literal(parser, "UINT128", 0)
            _t480 = 4
        else
            
            if match_lookahead_literal(parser, "STRING", 0)
                _t481 = 1
            else
                
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t482 = 8
                else
                    
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t483 = 5
                    else
                        
                        if match_lookahead_literal(parser, "INT", 0)
                            _t484 = 2
                        else
                            
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t485 = 3
                            else
                                
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t486 = 7
                                else
                                    
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t487 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t488 = 10
                                        else
                                            
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t489 = 9
                                            else
                                                _t489 = -1
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
                        end
                        _t483 = _t484
                    end
                    _t482 = _t483
                end
                _t481 = _t482
            end
            _t480 = _t481
        end
        _t479 = _t480
    end
    prediction76 = _t479
    
    if prediction76 == 10
        _t491 = parse_boolean_type(parser)
        boolean_type87 = _t491
        _t492 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type87))
        _t490 = _t492
    else
        
        if prediction76 == 9
            _t494 = parse_decimal_type(parser)
            decimal_type86 = _t494
            _t495 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type86))
            _t493 = _t495
        else
            
            if prediction76 == 8
                _t497 = parse_missing_type(parser)
                missing_type85 = _t497
                _t498 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type85))
                _t496 = _t498
            else
                
                if prediction76 == 7
                    _t500 = parse_datetime_type(parser)
                    datetime_type84 = _t500
                    _t501 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type84))
                    _t499 = _t501
                else
                    
                    if prediction76 == 6
                        _t503 = parse_date_type(parser)
                        date_type83 = _t503
                        _t504 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type83))
                        _t502 = _t504
                    else
                        
                        if prediction76 == 5
                            _t506 = parse_int128_type(parser)
                            int128_type82 = _t506
                            _t507 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type82))
                            _t505 = _t507
                        else
                            
                            if prediction76 == 4
                                _t509 = parse_uint128_type(parser)
                                uint128_type81 = _t509
                                _t510 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type81))
                                _t508 = _t510
                            else
                                
                                if prediction76 == 3
                                    _t512 = parse_float_type(parser)
                                    float_type80 = _t512
                                    _t513 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type80))
                                    _t511 = _t513
                                else
                                    
                                    if prediction76 == 2
                                        _t515 = parse_int_type(parser)
                                        int_type79 = _t515
                                        _t516 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type79))
                                        _t514 = _t516
                                    else
                                        
                                        if prediction76 == 1
                                            _t518 = parse_string_type(parser)
                                            string_type78 = _t518
                                            _t519 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type78))
                                            _t517 = _t519
                                        else
                                            
                                            if prediction76 == 0
                                                _t521 = parse_unspecified_type(parser)
                                                unspecified_type77 = _t521
                                                _t522 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type77))
                                                _t520 = _t522
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t517 = _t520
                                        end
                                        _t514 = _t517
                                    end
                                    _t511 = _t514
                                end
                                _t508 = _t511
                            end
                            _t505 = _t508
                        end
                        _t502 = _t505
                    end
                    _t499 = _t502
                end
                _t496 = _t499
            end
            _t493 = _t496
        end
        _t490 = _t493
    end
    return _t490
end

function parse_unspecified_type(parser::Parser)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t523 = Proto.UnspecifiedType()
    return _t523
end

function parse_string_type(parser::Parser)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t524 = Proto.StringType()
    return _t524
end

function parse_int_type(parser::Parser)::Proto.IntType
    consume_literal!(parser, "INT")
    _t525 = Proto.IntType()
    return _t525
end

function parse_float_type(parser::Parser)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t526 = Proto.FloatType()
    return _t526
end

function parse_uint128_type(parser::Parser)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t527 = Proto.UInt128Type()
    return _t527
end

function parse_int128_type(parser::Parser)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t528 = Proto.Int128Type()
    return _t528
end

function parse_date_type(parser::Parser)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t529 = Proto.DateType()
    return _t529
end

function parse_datetime_type(parser::Parser)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t530 = Proto.DateTimeType()
    return _t530
end

function parse_missing_type(parser::Parser)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t531 = Proto.MissingType()
    return _t531
end

function parse_decimal_type(parser::Parser)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int88 = consume_terminal!(parser, "INT")
    int_389 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t532 = Proto.DecimalType(precision=Int32(int88), scale=Int32(int_389))
    return _t532
end

function parse_boolean_type(parser::Parser)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t533 = Proto.BooleanType()
    return _t533
end

function parse_value_bindings(parser::Parser)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs90 = Proto.Binding[]
    cond91 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond91
        _t534 = parse_binding(parser)
        item92 = _t534
        push!(xs90, item92)
        cond91 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings93 = xs90
    return bindings93
end

function parse_formula(parser::Parser)::Proto.Formula
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "true", 1)
            _t536 = 0
        else
            
            if match_lookahead_literal(parser, "relatom", 1)
                _t537 = 11
            else
                
                if match_lookahead_literal(parser, "reduce", 1)
                    _t538 = 3
                else
                    
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t539 = 10
                    else
                        
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t540 = 9
                        else
                            
                            if match_lookahead_literal(parser, "or", 1)
                                _t541 = 5
                            else
                                
                                if match_lookahead_literal(parser, "not", 1)
                                    _t542 = 6
                                else
                                    
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t543 = 7
                                    else
                                        
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t544 = 1
                                        else
                                            
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t545 = 2
                                            else
                                                
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t546 = 12
                                                else
                                                    
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t547 = 8
                                                    else
                                                        
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t548 = 4
                                                        else
                                                            
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t549 = 10
                                                            else
                                                                
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t550 = 10
                                                                else
                                                                    
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t551 = 10
                                                                    else
                                                                        
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t552 = 10
                                                                        else
                                                                            
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t553 = 10
                                                                            else
                                                                                
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t554 = 10
                                                                                else
                                                                                    
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t555 = 10
                                                                                    else
                                                                                        
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t556 = 10
                                                                                        else
                                                                                            
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t557 = 10
                                                                                            else
                                                                                                _t557 = -1
                                                                                            end
                                                                                            _t556 = _t557
                                                                                        end
                                                                                        _t555 = _t556
                                                                                    end
                                                                                    _t554 = _t555
                                                                                end
                                                                                _t553 = _t554
                                                                            end
                                                                            _t552 = _t553
                                                                        end
                                                                        _t551 = _t552
                                                                    end
                                                                    _t550 = _t551
                                                                end
                                                                _t549 = _t550
                                                            end
                                                            _t548 = _t549
                                                        end
                                                        _t547 = _t548
                                                    end
                                                    _t546 = _t547
                                                end
                                                _t545 = _t546
                                            end
                                            _t544 = _t545
                                        end
                                        _t543 = _t544
                                    end
                                    _t542 = _t543
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
    else
        _t535 = -1
    end
    prediction94 = _t535
    
    if prediction94 == 12
        _t559 = parse_cast(parser)
        cast107 = _t559
        _t560 = Proto.Formula(formula_type=OneOf(:cast, cast107))
        _t558 = _t560
    else
        
        if prediction94 == 11
            _t562 = parse_rel_atom(parser)
            rel_atom106 = _t562
            _t563 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom106))
            _t561 = _t563
        else
            
            if prediction94 == 10
                _t565 = parse_primitive(parser)
                primitive105 = _t565
                _t566 = Proto.Formula(formula_type=OneOf(:primitive, primitive105))
                _t564 = _t566
            else
                
                if prediction94 == 9
                    _t568 = parse_pragma(parser)
                    pragma104 = _t568
                    _t569 = Proto.Formula(formula_type=OneOf(:pragma, pragma104))
                    _t567 = _t569
                else
                    
                    if prediction94 == 8
                        _t571 = parse_atom(parser)
                        atom103 = _t571
                        _t572 = Proto.Formula(formula_type=OneOf(:atom, atom103))
                        _t570 = _t572
                    else
                        
                        if prediction94 == 7
                            _t574 = parse_ffi(parser)
                            ffi102 = _t574
                            _t575 = Proto.Formula(formula_type=OneOf(:ffi, ffi102))
                            _t573 = _t575
                        else
                            
                            if prediction94 == 6
                                _t577 = parse_not(parser)
                                not101 = _t577
                                _t578 = Proto.Formula(formula_type=OneOf(:not, not101))
                                _t576 = _t578
                            else
                                
                                if prediction94 == 5
                                    _t580 = parse_disjunction(parser)
                                    disjunction100 = _t580
                                    _t581 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction100))
                                    _t579 = _t581
                                else
                                    
                                    if prediction94 == 4
                                        _t583 = parse_conjunction(parser)
                                        conjunction99 = _t583
                                        _t584 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction99))
                                        _t582 = _t584
                                    else
                                        
                                        if prediction94 == 3
                                            _t586 = parse_reduce(parser)
                                            reduce98 = _t586
                                            _t587 = Proto.Formula(formula_type=OneOf(:reduce, reduce98))
                                            _t585 = _t587
                                        else
                                            
                                            if prediction94 == 2
                                                _t589 = parse_exists(parser)
                                                exists97 = _t589
                                                _t590 = Proto.Formula(formula_type=OneOf(:exists, exists97))
                                                _t588 = _t590
                                            else
                                                
                                                if prediction94 == 1
                                                    _t592 = parse_false(parser)
                                                    false96 = _t592
                                                    _t593 = Proto.Formula(formula_type=OneOf(:disjunction, false96))
                                                    _t591 = _t593
                                                else
                                                    
                                                    if prediction94 == 0
                                                        _t595 = parse_true(parser)
                                                        true95 = _t595
                                                        _t596 = Proto.Formula(formula_type=OneOf(:conjunction, true95))
                                                        _t594 = _t596
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
                    _t567 = _t570
                end
                _t564 = _t567
            end
            _t561 = _t564
        end
        _t558 = _t561
    end
    return _t558
end

function parse_true(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t597 = Proto.Conjunction(args=Proto.Formula[])
    return _t597
end

function parse_false(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t598 = Proto.Disjunction(args=Proto.Formula[])
    return _t598
end

function parse_exists(parser::Parser)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t599 = parse_bindings(parser)
    bindings108 = _t599
    _t600 = parse_formula(parser)
    formula109 = _t600
    consume_literal!(parser, ")")
    _t601 = Proto.Abstraction(vars=vcat(bindings108[1], !isnothing(bindings108[2]) ? bindings108[2] : []), value=formula109)
    _t602 = Proto.Exists(body=_t601)
    return _t602
end

function parse_reduce(parser::Parser)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t603 = parse_abstraction(parser)
    abstraction110 = _t603
    _t604 = parse_abstraction(parser)
    abstraction_3111 = _t604
    _t605 = parse_terms(parser)
    terms112 = _t605
    consume_literal!(parser, ")")
    _t606 = Proto.Reduce(op=abstraction110, body=abstraction_3111, terms=terms112)
    return _t606
end

function parse_terms(parser::Parser)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs113 = Proto.Term[]
    cond114 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond114
        _t607 = parse_term(parser)
        item115 = _t607
        push!(xs113, item115)
        cond114 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms116 = xs113
    consume_literal!(parser, ")")
    return terms116
end

function parse_term(parser::Parser)::Proto.Term
    
    if match_lookahead_literal(parser, "true", 0)
        _t608 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t609 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t610 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t611 = 1
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t612 = 1
                    else
                        
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t613 = 0
                        else
                            
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t614 = 1
                            else
                                
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t615 = 1
                                else
                                    
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t616 = 1
                                    else
                                        
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t617 = 1
                                        else
                                            
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t618 = 1
                                            else
                                                _t618 = -1
                                            end
                                            _t617 = _t618
                                        end
                                        _t616 = _t617
                                    end
                                    _t615 = _t616
                                end
                                _t614 = _t615
                            end
                            _t613 = _t614
                        end
                        _t612 = _t613
                    end
                    _t611 = _t612
                end
                _t610 = _t611
            end
            _t609 = _t610
        end
        _t608 = _t609
    end
    prediction117 = _t608
    
    if prediction117 == 1
        _t620 = parse_constant(parser)
        constant119 = _t620
        _t621 = Proto.Term(term_type=OneOf(:constant, constant119))
        _t619 = _t621
    else
        
        if prediction117 == 0
            _t623 = parse_var(parser)
            var118 = _t623
            _t624 = Proto.Term(term_type=OneOf(:var, var118))
            _t622 = _t624
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t619 = _t622
    end
    return _t619
end

function parse_var(parser::Parser)::Proto.Var
    symbol120 = consume_terminal!(parser, "SYMBOL")
    _t625 = Proto.Var(name=symbol120)
    return _t625
end

function parse_constant(parser::Parser)::Proto.Value
    _t626 = parse_value(parser)
    value121 = _t626
    return value121
end

function parse_conjunction(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs122 = Proto.Formula[]
    cond123 = match_lookahead_literal(parser, "(", 0)
    while cond123
        _t627 = parse_formula(parser)
        item124 = _t627
        push!(xs122, item124)
        cond123 = match_lookahead_literal(parser, "(", 0)
    end
    formulas125 = xs122
    consume_literal!(parser, ")")
    _t628 = Proto.Conjunction(args=formulas125)
    return _t628
end

function parse_disjunction(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs126 = Proto.Formula[]
    cond127 = match_lookahead_literal(parser, "(", 0)
    while cond127
        _t629 = parse_formula(parser)
        item128 = _t629
        push!(xs126, item128)
        cond127 = match_lookahead_literal(parser, "(", 0)
    end
    formulas129 = xs126
    consume_literal!(parser, ")")
    _t630 = Proto.Disjunction(args=formulas129)
    return _t630
end

function parse_not(parser::Parser)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t631 = parse_formula(parser)
    formula130 = _t631
    consume_literal!(parser, ")")
    _t632 = Proto.Not(arg=formula130)
    return _t632
end

function parse_ffi(parser::Parser)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t633 = parse_name(parser)
    name131 = _t633
    _t634 = parse_ffi_args(parser)
    ffi_args132 = _t634
    _t635 = parse_terms(parser)
    terms133 = _t635
    consume_literal!(parser, ")")
    _t636 = Proto.FFI(name=name131, args=ffi_args132, terms=terms133)
    return _t636
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
        _t637 = parse_abstraction(parser)
        item137 = _t637
        push!(xs135, item137)
        cond136 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions138 = xs135
    consume_literal!(parser, ")")
    return abstractions138
end

function parse_atom(parser::Parser)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t638 = parse_relation_id(parser)
    relation_id139 = _t638
    xs140 = Proto.Term[]
    cond141 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond141
        _t639 = parse_term(parser)
        item142 = _t639
        push!(xs140, item142)
        cond141 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms143 = xs140
    consume_literal!(parser, ")")
    _t640 = Proto.Atom(name=relation_id139, terms=terms143)
    return _t640
end

function parse_pragma(parser::Parser)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t641 = parse_name(parser)
    name144 = _t641
    xs145 = Proto.Term[]
    cond146 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond146
        _t642 = parse_term(parser)
        item147 = _t642
        push!(xs145, item147)
        cond146 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms148 = xs145
    consume_literal!(parser, ")")
    _t643 = Proto.Pragma(name=name144, terms=terms148)
    return _t643
end

function parse_primitive(parser::Parser)::Proto.Primitive
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "primitive", 1)
            _t645 = 9
        else
            
            if match_lookahead_literal(parser, ">=", 1)
                _t646 = 4
            else
                
                if match_lookahead_literal(parser, ">", 1)
                    _t647 = 3
                else
                    
                    if match_lookahead_literal(parser, "=", 1)
                        _t648 = 0
                    else
                        
                        if match_lookahead_literal(parser, "<=", 1)
                            _t649 = 2
                        else
                            
                            if match_lookahead_literal(parser, "<", 1)
                                _t650 = 1
                            else
                                
                                if match_lookahead_literal(parser, "/", 1)
                                    _t651 = 8
                                else
                                    
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t652 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t653 = 5
                                        else
                                            
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t654 = 7
                                            else
                                                _t654 = -1
                                            end
                                            _t653 = _t654
                                        end
                                        _t652 = _t653
                                    end
                                    _t651 = _t652
                                end
                                _t650 = _t651
                            end
                            _t649 = _t650
                        end
                        _t648 = _t649
                    end
                    _t647 = _t648
                end
                _t646 = _t647
            end
            _t645 = _t646
        end
        _t644 = _t645
    else
        _t644 = -1
    end
    prediction149 = _t644
    
    if prediction149 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t656 = parse_name(parser)
        name159 = _t656
        xs160 = Proto.RelTerm[]
        cond161 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond161
            _t657 = parse_rel_term(parser)
            item162 = _t657
            push!(xs160, item162)
            cond161 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms163 = xs160
        consume_literal!(parser, ")")
        _t658 = Proto.Primitive(name=name159, terms=rel_terms163)
        _t655 = _t658
    else
        
        if prediction149 == 8
            _t660 = parse_divide(parser)
            divide158 = _t660
            _t659 = divide158
        else
            
            if prediction149 == 7
                _t662 = parse_multiply(parser)
                multiply157 = _t662
                _t661 = multiply157
            else
                
                if prediction149 == 6
                    _t664 = parse_minus(parser)
                    minus156 = _t664
                    _t663 = minus156
                else
                    
                    if prediction149 == 5
                        _t666 = parse_add(parser)
                        add155 = _t666
                        _t665 = add155
                    else
                        
                        if prediction149 == 4
                            _t668 = parse_gt_eq(parser)
                            gt_eq154 = _t668
                            _t667 = gt_eq154
                        else
                            
                            if prediction149 == 3
                                _t670 = parse_gt(parser)
                                gt153 = _t670
                                _t669 = gt153
                            else
                                
                                if prediction149 == 2
                                    _t672 = parse_lt_eq(parser)
                                    lt_eq152 = _t672
                                    _t671 = lt_eq152
                                else
                                    
                                    if prediction149 == 1
                                        _t674 = parse_lt(parser)
                                        lt151 = _t674
                                        _t673 = lt151
                                    else
                                        
                                        if prediction149 == 0
                                            _t676 = parse_eq(parser)
                                            eq150 = _t676
                                            _t675 = eq150
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t673 = _t675
                                    end
                                    _t671 = _t673
                                end
                                _t669 = _t671
                            end
                            _t667 = _t669
                        end
                        _t665 = _t667
                    end
                    _t663 = _t665
                end
                _t661 = _t663
            end
            _t659 = _t661
        end
        _t655 = _t659
    end
    return _t655
end

function parse_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t677 = parse_term(parser)
    term164 = _t677
    _t678 = parse_term(parser)
    term_3165 = _t678
    consume_literal!(parser, ")")
    _t679 = Proto.RelTerm(rel_term_type=OneOf(:term, term164))
    _t680 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3165))
    _t681 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t679, _t680])
    return _t681
end

function parse_lt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t682 = parse_term(parser)
    term166 = _t682
    _t683 = parse_term(parser)
    term_3167 = _t683
    consume_literal!(parser, ")")
    _t684 = Proto.RelTerm(rel_term_type=OneOf(:term, term166))
    _t685 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3167))
    _t686 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t684, _t685])
    return _t686
end

function parse_lt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t687 = parse_term(parser)
    term168 = _t687
    _t688 = parse_term(parser)
    term_3169 = _t688
    consume_literal!(parser, ")")
    _t689 = Proto.RelTerm(rel_term_type=OneOf(:term, term168))
    _t690 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3169))
    _t691 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t689, _t690])
    return _t691
end

function parse_gt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t692 = parse_term(parser)
    term170 = _t692
    _t693 = parse_term(parser)
    term_3171 = _t693
    consume_literal!(parser, ")")
    _t694 = Proto.RelTerm(rel_term_type=OneOf(:term, term170))
    _t695 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3171))
    _t696 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t694, _t695])
    return _t696
end

function parse_gt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t697 = parse_term(parser)
    term172 = _t697
    _t698 = parse_term(parser)
    term_3173 = _t698
    consume_literal!(parser, ")")
    _t699 = Proto.RelTerm(rel_term_type=OneOf(:term, term172))
    _t700 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3173))
    _t701 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t699, _t700])
    return _t701
end

function parse_add(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t702 = parse_term(parser)
    term174 = _t702
    _t703 = parse_term(parser)
    term_3175 = _t703
    _t704 = parse_term(parser)
    term_4176 = _t704
    consume_literal!(parser, ")")
    _t705 = Proto.RelTerm(rel_term_type=OneOf(:term, term174))
    _t706 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3175))
    _t707 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4176))
    _t708 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t705, _t706, _t707])
    return _t708
end

function parse_minus(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t709 = parse_term(parser)
    term177 = _t709
    _t710 = parse_term(parser)
    term_3178 = _t710
    _t711 = parse_term(parser)
    term_4179 = _t711
    consume_literal!(parser, ")")
    _t712 = Proto.RelTerm(rel_term_type=OneOf(:term, term177))
    _t713 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3178))
    _t714 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4179))
    _t715 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t712, _t713, _t714])
    return _t715
end

function parse_multiply(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t716 = parse_term(parser)
    term180 = _t716
    _t717 = parse_term(parser)
    term_3181 = _t717
    _t718 = parse_term(parser)
    term_4182 = _t718
    consume_literal!(parser, ")")
    _t719 = Proto.RelTerm(rel_term_type=OneOf(:term, term180))
    _t720 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3181))
    _t721 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4182))
    _t722 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t719, _t720, _t721])
    return _t722
end

function parse_divide(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t723 = parse_term(parser)
    term183 = _t723
    _t724 = parse_term(parser)
    term_3184 = _t724
    _t725 = parse_term(parser)
    term_4185 = _t725
    consume_literal!(parser, ")")
    _t726 = Proto.RelTerm(rel_term_type=OneOf(:term, term183))
    _t727 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3184))
    _t728 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4185))
    _t729 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t726, _t727, _t728])
    return _t729
end

function parse_rel_term(parser::Parser)::Proto.RelTerm
    
    if match_lookahead_literal(parser, "true", 0)
        _t730 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t731 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t732 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t733 = 1
                else
                    
                    if match_lookahead_literal(parser, "#", 0)
                        _t734 = 0
                    else
                        
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t735 = 1
                        else
                            
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t736 = 1
                            else
                                
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t737 = 1
                                else
                                    
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t738 = 1
                                    else
                                        
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t739 = 1
                                        else
                                            
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t740 = 1
                                            else
                                                
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t741 = 1
                                                else
                                                    _t741 = -1
                                                end
                                                _t740 = _t741
                                            end
                                            _t739 = _t740
                                        end
                                        _t738 = _t739
                                    end
                                    _t737 = _t738
                                end
                                _t736 = _t737
                            end
                            _t735 = _t736
                        end
                        _t734 = _t735
                    end
                    _t733 = _t734
                end
                _t732 = _t733
            end
            _t731 = _t732
        end
        _t730 = _t731
    end
    prediction186 = _t730
    
    if prediction186 == 1
        _t743 = parse_term(parser)
        term188 = _t743
        _t744 = Proto.RelTerm(rel_term_type=OneOf(:term, term188))
        _t742 = _t744
    else
        
        if prediction186 == 0
            _t746 = parse_specialized_value(parser)
            specialized_value187 = _t746
            _t747 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value187))
            _t745 = _t747
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t742 = _t745
    end
    return _t742
end

function parse_specialized_value(parser::Parser)::Proto.Value
    consume_literal!(parser, "#")
    _t748 = parse_value(parser)
    value189 = _t748
    return value189
end

function parse_rel_atom(parser::Parser)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t749 = parse_name(parser)
    name190 = _t749
    xs191 = Proto.RelTerm[]
    cond192 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond192
        _t750 = parse_rel_term(parser)
        item193 = _t750
        push!(xs191, item193)
        cond192 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms194 = xs191
    consume_literal!(parser, ")")
    _t751 = Proto.RelAtom(name=name190, terms=rel_terms194)
    return _t751
end

function parse_cast(parser::Parser)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t752 = parse_term(parser)
    term195 = _t752
    _t753 = parse_term(parser)
    term_3196 = _t753
    consume_literal!(parser, ")")
    _t754 = Proto.Cast(input=term195, result=term_3196)
    return _t754
end

function parse_attrs(parser::Parser)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs197 = Proto.Attribute[]
    cond198 = match_lookahead_literal(parser, "(", 0)
    while cond198
        _t755 = parse_attribute(parser)
        item199 = _t755
        push!(xs197, item199)
        cond198 = match_lookahead_literal(parser, "(", 0)
    end
    attributes200 = xs197
    consume_literal!(parser, ")")
    return attributes200
end

function parse_attribute(parser::Parser)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t756 = parse_name(parser)
    name201 = _t756
    xs202 = Proto.Value[]
    cond203 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond203
        _t757 = parse_value(parser)
        item204 = _t757
        push!(xs202, item204)
        cond203 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values205 = xs202
    consume_literal!(parser, ")")
    _t758 = Proto.Attribute(name=name201, args=values205)
    return _t758
end

function parse_algorithm(parser::Parser)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs206 = Proto.RelationId[]
    cond207 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond207
        _t759 = parse_relation_id(parser)
        item208 = _t759
        push!(xs206, item208)
        cond207 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids209 = xs206
    _t760 = parse_script(parser)
    script210 = _t760
    consume_literal!(parser, ")")
    _t761 = Proto.Algorithm(var"#global"=relation_ids209, body=script210)
    return _t761
end

function parse_script(parser::Parser)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs211 = Proto.Construct[]
    cond212 = match_lookahead_literal(parser, "(", 0)
    while cond212
        _t762 = parse_construct(parser)
        item213 = _t762
        push!(xs211, item213)
        cond212 = match_lookahead_literal(parser, "(", 0)
    end
    constructs214 = xs211
    consume_literal!(parser, ")")
    _t763 = Proto.Script(constructs=constructs214)
    return _t763
end

function parse_construct(parser::Parser)::Proto.Construct
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t765 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t766 = 1
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t767 = 1
                else
                    
                    if match_lookahead_literal(parser, "loop", 1)
                        _t768 = 0
                    else
                        
                        if match_lookahead_literal(parser, "break", 1)
                            _t769 = 1
                        else
                            
                            if match_lookahead_literal(parser, "assign", 1)
                                _t770 = 1
                            else
                                _t770 = -1
                            end
                            _t769 = _t770
                        end
                        _t768 = _t769
                    end
                    _t767 = _t768
                end
                _t766 = _t767
            end
            _t765 = _t766
        end
        _t764 = _t765
    else
        _t764 = -1
    end
    prediction215 = _t764
    
    if prediction215 == 1
        _t772 = parse_instruction(parser)
        instruction217 = _t772
        _t773 = Proto.Construct(construct_type=OneOf(:instruction, instruction217))
        _t771 = _t773
    else
        
        if prediction215 == 0
            _t775 = parse_loop(parser)
            loop216 = _t775
            _t776 = Proto.Construct(construct_type=OneOf(:loop, loop216))
            _t774 = _t776
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t771 = _t774
    end
    return _t771
end

function parse_loop(parser::Parser)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t777 = parse_init(parser)
    init218 = _t777
    _t778 = parse_script(parser)
    script219 = _t778
    consume_literal!(parser, ")")
    _t779 = Proto.Loop(init=init218, body=script219)
    return _t779
end

function parse_init(parser::Parser)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs220 = Proto.Instruction[]
    cond221 = match_lookahead_literal(parser, "(", 0)
    while cond221
        _t780 = parse_instruction(parser)
        item222 = _t780
        push!(xs220, item222)
        cond221 = match_lookahead_literal(parser, "(", 0)
    end
    instructions223 = xs220
    consume_literal!(parser, ")")
    return instructions223
end

function parse_instruction(parser::Parser)::Proto.Instruction
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t782 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t783 = 4
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t784 = 3
                else
                    
                    if match_lookahead_literal(parser, "break", 1)
                        _t785 = 2
                    else
                        
                        if match_lookahead_literal(parser, "assign", 1)
                            _t786 = 0
                        else
                            _t786 = -1
                        end
                        _t785 = _t786
                    end
                    _t784 = _t785
                end
                _t783 = _t784
            end
            _t782 = _t783
        end
        _t781 = _t782
    else
        _t781 = -1
    end
    prediction224 = _t781
    
    if prediction224 == 4
        _t788 = parse_monus_def(parser)
        monus_def229 = _t788
        _t789 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def229))
        _t787 = _t789
    else
        
        if prediction224 == 3
            _t791 = parse_monoid_def(parser)
            monoid_def228 = _t791
            _t792 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def228))
            _t790 = _t792
        else
            
            if prediction224 == 2
                _t794 = parse_break(parser)
                break227 = _t794
                _t795 = Proto.Instruction(instr_type=OneOf(:var"#break", break227))
                _t793 = _t795
            else
                
                if prediction224 == 1
                    _t797 = parse_upsert(parser)
                    upsert226 = _t797
                    _t798 = Proto.Instruction(instr_type=OneOf(:upsert, upsert226))
                    _t796 = _t798
                else
                    
                    if prediction224 == 0
                        _t800 = parse_assign(parser)
                        assign225 = _t800
                        _t801 = Proto.Instruction(instr_type=OneOf(:assign, assign225))
                        _t799 = _t801
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t796 = _t799
                end
                _t793 = _t796
            end
            _t790 = _t793
        end
        _t787 = _t790
    end
    return _t787
end

function parse_assign(parser::Parser)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t802 = parse_relation_id(parser)
    relation_id230 = _t802
    _t803 = parse_abstraction(parser)
    abstraction231 = _t803
    
    if match_lookahead_literal(parser, "(", 0)
        _t805 = parse_attrs(parser)
        _t804 = _t805
    else
        _t804 = nothing
    end
    attrs232 = _t804
    consume_literal!(parser, ")")
    _t806 = Proto.Assign(name=relation_id230, body=abstraction231, attrs=(!isnothing(attrs232) ? attrs232 : Proto.Attribute[]))
    return _t806
end

function parse_upsert(parser::Parser)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t807 = parse_relation_id(parser)
    relation_id233 = _t807
    _t808 = parse_abstraction_with_arity(parser)
    abstraction_with_arity234 = _t808
    
    if match_lookahead_literal(parser, "(", 0)
        _t810 = parse_attrs(parser)
        _t809 = _t810
    else
        _t809 = nothing
    end
    attrs235 = _t809
    consume_literal!(parser, ")")
    _t811 = Proto.Upsert(name=relation_id233, body=abstraction_with_arity234[1], attrs=(!isnothing(attrs235) ? attrs235 : Proto.Attribute[]), value_arity=abstraction_with_arity234[2])
    return _t811
end

function parse_abstraction_with_arity(parser::Parser)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t812 = parse_bindings(parser)
    bindings236 = _t812
    _t813 = parse_formula(parser)
    formula237 = _t813
    consume_literal!(parser, ")")
    _t814 = Proto.Abstraction(vars=vcat(bindings236[1], !isnothing(bindings236[2]) ? bindings236[2] : []), value=formula237)
    return (_t814, length(bindings236[2]),)
end

function parse_break(parser::Parser)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t815 = parse_relation_id(parser)
    relation_id238 = _t815
    _t816 = parse_abstraction(parser)
    abstraction239 = _t816
    
    if match_lookahead_literal(parser, "(", 0)
        _t818 = parse_attrs(parser)
        _t817 = _t818
    else
        _t817 = nothing
    end
    attrs240 = _t817
    consume_literal!(parser, ")")
    _t819 = Proto.Break(name=relation_id238, body=abstraction239, attrs=(!isnothing(attrs240) ? attrs240 : Proto.Attribute[]))
    return _t819
end

function parse_monoid_def(parser::Parser)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t820 = parse_monoid(parser)
    monoid241 = _t820
    _t821 = parse_relation_id(parser)
    relation_id242 = _t821
    _t822 = parse_abstraction_with_arity(parser)
    abstraction_with_arity243 = _t822
    
    if match_lookahead_literal(parser, "(", 0)
        _t824 = parse_attrs(parser)
        _t823 = _t824
    else
        _t823 = nothing
    end
    attrs244 = _t823
    consume_literal!(parser, ")")
    _t825 = Proto.MonoidDef(monoid=monoid241, name=relation_id242, body=abstraction_with_arity243[1], attrs=(!isnothing(attrs244) ? attrs244 : Proto.Attribute[]), value_arity=abstraction_with_arity243[2])
    return _t825
end

function parse_monoid(parser::Parser)::Proto.Monoid
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "sum", 1)
            _t827 = 3
        else
            
            if match_lookahead_literal(parser, "or", 1)
                _t828 = 0
            else
                
                if match_lookahead_literal(parser, "min", 1)
                    _t829 = 1
                else
                    
                    if match_lookahead_literal(parser, "max", 1)
                        _t830 = 2
                    else
                        _t830 = -1
                    end
                    _t829 = _t830
                end
                _t828 = _t829
            end
            _t827 = _t828
        end
        _t826 = _t827
    else
        _t826 = -1
    end
    prediction245 = _t826
    
    if prediction245 == 3
        _t832 = parse_sum_monoid(parser)
        sum_monoid249 = _t832
        _t833 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid249))
        _t831 = _t833
    else
        
        if prediction245 == 2
            _t835 = parse_max_monoid(parser)
            max_monoid248 = _t835
            _t836 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid248))
            _t834 = _t836
        else
            
            if prediction245 == 1
                _t838 = parse_min_monoid(parser)
                min_monoid247 = _t838
                _t839 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid247))
                _t837 = _t839
            else
                
                if prediction245 == 0
                    _t841 = parse_or_monoid(parser)
                    or_monoid246 = _t841
                    _t842 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid246))
                    _t840 = _t842
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t837 = _t840
            end
            _t834 = _t837
        end
        _t831 = _t834
    end
    return _t831
end

function parse_or_monoid(parser::Parser)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t843 = Proto.OrMonoid()
    return _t843
end

function parse_min_monoid(parser::Parser)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t844 = parse_type(parser)
    type250 = _t844
    consume_literal!(parser, ")")
    _t845 = Proto.MinMonoid(var"#type"=type250)
    return _t845
end

function parse_max_monoid(parser::Parser)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t846 = parse_type(parser)
    type251 = _t846
    consume_literal!(parser, ")")
    _t847 = Proto.MaxMonoid(var"#type"=type251)
    return _t847
end

function parse_sum_monoid(parser::Parser)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t848 = parse_type(parser)
    type252 = _t848
    consume_literal!(parser, ")")
    _t849 = Proto.SumMonoid(var"#type"=type252)
    return _t849
end

function parse_monus_def(parser::Parser)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t850 = parse_monoid(parser)
    monoid253 = _t850
    _t851 = parse_relation_id(parser)
    relation_id254 = _t851
    _t852 = parse_abstraction_with_arity(parser)
    abstraction_with_arity255 = _t852
    
    if match_lookahead_literal(parser, "(", 0)
        _t854 = parse_attrs(parser)
        _t853 = _t854
    else
        _t853 = nothing
    end
    attrs256 = _t853
    consume_literal!(parser, ")")
    _t855 = Proto.MonusDef(monoid=monoid253, name=relation_id254, body=abstraction_with_arity255[1], attrs=(!isnothing(attrs256) ? attrs256 : Proto.Attribute[]), value_arity=abstraction_with_arity255[2])
    return _t855
end

function parse_constraint(parser::Parser)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t856 = parse_relation_id(parser)
    relation_id257 = _t856
    _t857 = parse_abstraction(parser)
    abstraction258 = _t857
    _t858 = parse_functional_dependency_keys(parser)
    functional_dependency_keys259 = _t858
    _t859 = parse_functional_dependency_values(parser)
    functional_dependency_values260 = _t859
    consume_literal!(parser, ")")
    _t860 = Proto.FunctionalDependency(guard=abstraction258, keys=functional_dependency_keys259, values=functional_dependency_values260)
    _t861 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t860), name=relation_id257)
    return _t861
end

function parse_functional_dependency_keys(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs261 = Proto.Var[]
    cond262 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond262
        _t862 = parse_var(parser)
        item263 = _t862
        push!(xs261, item263)
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
        _t863 = parse_var(parser)
        item267 = _t863
        push!(xs265, item267)
        cond266 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars268 = xs265
    consume_literal!(parser, ")")
    return vars268
end

function parse_data(parser::Parser)::Proto.Data
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t865 = 0
        else
            
            if match_lookahead_literal(parser, "csv_data", 1)
                _t866 = 2
            else
                
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t867 = 1
                else
                    _t867 = -1
                end
                _t866 = _t867
            end
            _t865 = _t866
        end
        _t864 = _t865
    else
        _t864 = -1
    end
    prediction269 = _t864
    
    if prediction269 == 2
        _t869 = parse_csv_data(parser)
        csv_data272 = _t869
        _t870 = Proto.Data(data_type=OneOf(:csv_data, csv_data272))
        _t868 = _t870
    else
        
        if prediction269 == 1
            _t872 = parse_betree_relation(parser)
            betree_relation271 = _t872
            _t873 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation271))
            _t871 = _t873
        else
            
            if prediction269 == 0
                _t875 = parse_rel_edb(parser)
                rel_edb270 = _t875
                _t876 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb270))
                _t874 = _t876
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t871 = _t874
        end
        _t868 = _t871
    end
    return _t868
end

function parse_rel_edb(parser::Parser)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t877 = parse_relation_id(parser)
    relation_id273 = _t877
    _t878 = parse_rel_edb_path(parser)
    rel_edb_path274 = _t878
    _t879 = parse_rel_edb_types(parser)
    rel_edb_types275 = _t879
    consume_literal!(parser, ")")
    _t880 = Proto.RelEDB(target_id=relation_id273, path=rel_edb_path274, types=rel_edb_types275)
    return _t880
end

function parse_rel_edb_path(parser::Parser)::Vector{String}
    consume_literal!(parser, "[")
    xs276 = String[]
    cond277 = match_lookahead_terminal(parser, "STRING", 0)
    while cond277
        item278 = consume_terminal!(parser, "STRING")
        push!(xs276, item278)
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
        _t881 = parse_type(parser)
        item282 = _t881
        push!(xs280, item282)
        cond281 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types283 = xs280
    consume_literal!(parser, "]")
    return types283
end

function parse_betree_relation(parser::Parser)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t882 = parse_relation_id(parser)
    relation_id284 = _t882
    _t883 = parse_betree_info(parser)
    betree_info285 = _t883
    consume_literal!(parser, ")")
    _t884 = Proto.BeTreeRelation(name=relation_id284, relation_info=betree_info285)
    return _t884
end

function parse_betree_info(parser::Parser)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t885 = parse_betree_info_key_types(parser)
    betree_info_key_types286 = _t885
    _t886 = parse_betree_info_value_types(parser)
    betree_info_value_types287 = _t886
    _t887 = parse_config_dict(parser)
    config_dict288 = _t887
    consume_literal!(parser, ")")
    _t888 = construct_betree_info(parser, betree_info_key_types286, betree_info_value_types287, config_dict288)
    return _t888
end

function parse_betree_info_key_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs289 = Proto.var"#Type"[]
    cond290 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond290
        _t889 = parse_type(parser)
        item291 = _t889
        push!(xs289, item291)
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
        _t890 = parse_type(parser)
        item295 = _t890
        push!(xs293, item295)
        cond294 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types296 = xs293
    consume_literal!(parser, ")")
    return types296
end

function parse_csv_data(parser::Parser)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t891 = parse_csvlocator(parser)
    csvlocator297 = _t891
    _t892 = parse_csv_config(parser)
    csv_config298 = _t892
    _t893 = parse_csv_columns(parser)
    csv_columns299 = _t893
    _t894 = parse_csv_asof(parser)
    csv_asof300 = _t894
    consume_literal!(parser, ")")
    _t895 = Proto.CSVData(locator=csvlocator297, config=csv_config298, columns=csv_columns299, asof=csv_asof300)
    return _t895
end

function parse_csvlocator(parser::Parser)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t897 = parse_csv_locator_paths(parser)
        _t896 = _t897
    else
        _t896 = nothing
    end
    csv_locator_paths301 = _t896
    
    if match_lookahead_literal(parser, "(", 0)
        _t899 = parse_csv_locator_inline_data(parser)
        _t898 = _t899
    else
        _t898 = nothing
    end
    csv_locator_inline_data302 = _t898
    consume_literal!(parser, ")")
    _t900 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths301) ? csv_locator_paths301 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data302) ? csv_locator_inline_data302 : "")))
    return _t900
end

function parse_csv_locator_paths(parser::Parser)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs303 = String[]
    cond304 = match_lookahead_terminal(parser, "STRING", 0)
    while cond304
        item305 = consume_terminal!(parser, "STRING")
        push!(xs303, item305)
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
    _t901 = parse_config_dict(parser)
    config_dict308 = _t901
    consume_literal!(parser, ")")
    _t902 = construct_csv_config(parser, config_dict308)
    return _t902
end

function parse_csv_columns(parser::Parser)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs309 = Proto.CSVColumn[]
    cond310 = match_lookahead_literal(parser, "(", 0)
    while cond310
        _t903 = parse_csv_column(parser)
        item311 = _t903
        push!(xs309, item311)
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
    _t904 = parse_relation_id(parser)
    relation_id314 = _t904
    consume_literal!(parser, "[")
    xs315 = Proto.var"#Type"[]
    cond316 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond316
        _t905 = parse_type(parser)
        item317 = _t905
        push!(xs315, item317)
        cond316 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types318 = xs315
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t906 = Proto.CSVColumn(column_name=string313, target_id=relation_id314, types=types318)
    return _t906
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
    _t907 = parse_fragment_id(parser)
    fragment_id320 = _t907
    consume_literal!(parser, ")")
    _t908 = Proto.Undefine(fragment_id=fragment_id320)
    return _t908
end

function parse_context(parser::Parser)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs321 = Proto.RelationId[]
    cond322 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond322
        _t909 = parse_relation_id(parser)
        item323 = _t909
        push!(xs321, item323)
        cond322 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids324 = xs321
    consume_literal!(parser, ")")
    _t910 = Proto.Context(relations=relation_ids324)
    return _t910
end

function parse_epoch_reads(parser::Parser)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs325 = Proto.Read[]
    cond326 = match_lookahead_literal(parser, "(", 0)
    while cond326
        _t911 = parse_read(parser)
        item327 = _t911
        push!(xs325, item327)
        cond326 = match_lookahead_literal(parser, "(", 0)
    end
    reads328 = xs325
    consume_literal!(parser, ")")
    return reads328
end

function parse_read(parser::Parser)::Proto.Read
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "what_if", 1)
            _t913 = 2
        else
            
            if match_lookahead_literal(parser, "output", 1)
                _t914 = 1
            else
                
                if match_lookahead_literal(parser, "export", 1)
                    _t915 = 4
                else
                    
                    if match_lookahead_literal(parser, "demand", 1)
                        _t916 = 0
                    else
                        
                        if match_lookahead_literal(parser, "abort", 1)
                            _t917 = 3
                        else
                            _t917 = -1
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
    else
        _t912 = -1
    end
    prediction329 = _t912
    
    if prediction329 == 4
        _t919 = parse_export(parser)
        export334 = _t919
        _t920 = Proto.Read(read_type=OneOf(:var"#export", export334))
        _t918 = _t920
    else
        
        if prediction329 == 3
            _t922 = parse_abort(parser)
            abort333 = _t922
            _t923 = Proto.Read(read_type=OneOf(:abort, abort333))
            _t921 = _t923
        else
            
            if prediction329 == 2
                _t925 = parse_what_if(parser)
                what_if332 = _t925
                _t926 = Proto.Read(read_type=OneOf(:what_if, what_if332))
                _t924 = _t926
            else
                
                if prediction329 == 1
                    _t928 = parse_output(parser)
                    output331 = _t928
                    _t929 = Proto.Read(read_type=OneOf(:output, output331))
                    _t927 = _t929
                else
                    
                    if prediction329 == 0
                        _t931 = parse_demand(parser)
                        demand330 = _t931
                        _t932 = Proto.Read(read_type=OneOf(:demand, demand330))
                        _t930 = _t932
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t927 = _t930
                end
                _t924 = _t927
            end
            _t921 = _t924
        end
        _t918 = _t921
    end
    return _t918
end

function parse_demand(parser::Parser)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t933 = parse_relation_id(parser)
    relation_id335 = _t933
    consume_literal!(parser, ")")
    _t934 = Proto.Demand(relation_id=relation_id335)
    return _t934
end

function parse_output(parser::Parser)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t935 = parse_name(parser)
    name336 = _t935
    _t936 = parse_relation_id(parser)
    relation_id337 = _t936
    consume_literal!(parser, ")")
    _t937 = Proto.Output(name=name336, relation_id=relation_id337)
    return _t937
end

function parse_what_if(parser::Parser)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t938 = parse_name(parser)
    name338 = _t938
    _t939 = parse_epoch(parser)
    epoch339 = _t939
    consume_literal!(parser, ")")
    _t940 = Proto.WhatIf(branch=name338, epoch=epoch339)
    return _t940
end

function parse_abort(parser::Parser)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t942 = parse_name(parser)
        _t941 = _t942
    else
        _t941 = nothing
    end
    name340 = _t941
    _t943 = parse_relation_id(parser)
    relation_id341 = _t943
    consume_literal!(parser, ")")
    _t944 = Proto.Abort(name=(!isnothing(name340) ? name340 : "abort"), relation_id=relation_id341)
    return _t944
end

function parse_export(parser::Parser)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t945 = parse_export_csv_config(parser)
    export_csv_config342 = _t945
    consume_literal!(parser, ")")
    _t946 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config342))
    return _t946
end

function parse_export_csv_config(parser::Parser)::Proto.ExportCSVConfig
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t948 = 0
        else
            
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t949 = 1
            else
                _t949 = -1
            end
            _t948 = _t949
        end
        _t947 = _t948
    else
        _t947 = -1
    end
    prediction343 = _t947
    
    if prediction343 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t951 = parse_export_csv_path(parser)
        export_csv_path347 = _t951
        consume_literal!(parser, "(")
        consume_literal!(parser, "columns")
        xs348 = Proto.ExportCSVColumn[]
        cond349 = match_lookahead_literal(parser, "(", 0)
        while cond349
            _t952 = parse_export_csv_column(parser)
            item350 = _t952
            push!(xs348, item350)
            cond349 = match_lookahead_literal(parser, "(", 0)
        end
        export_csv_columns351 = xs348
        consume_literal!(parser, ")")
        _t953 = parse_config_dict(parser)
        config_dict352 = _t953
        consume_literal!(parser, ")")
        _t954 = construct_export_csv_config(parser, export_csv_path347, export_csv_columns351, config_dict352)
        _t950 = _t954
    else
        
        if prediction343 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t956 = parse_export_csv_path(parser)
            export_csv_path344 = _t956
            _t957 = parse_export_csv_source(parser)
            export_csv_source345 = _t957
            _t958 = parse_csv_config(parser)
            csv_config346 = _t958
            consume_literal!(parser, ")")
            _t959 = construct_export_csv_config_with_source(parser, export_csv_path344, export_csv_source345, csv_config346)
            _t955 = _t959
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t950 = _t955
    end
    return _t950
end

function parse_export_csv_path(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string353 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string353
end

function parse_export_csv_source(parser::Parser)::Proto.ExportCSVSource
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "table_def", 1)
            _t961 = 1
        else
            
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t962 = 0
            else
                _t962 = -1
            end
            _t961 = _t962
        end
        _t960 = _t961
    else
        _t960 = -1
    end
    prediction354 = _t960
    
    if prediction354 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t964 = parse_relation_id(parser)
        relation_id359 = _t964
        consume_literal!(parser, ")")
        _t965 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id359))
        _t963 = _t965
    else
        
        if prediction354 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs355 = Proto.ExportCSVColumn[]
            cond356 = match_lookahead_literal(parser, "(", 0)
            while cond356
                _t967 = parse_export_csv_column(parser)
                item357 = _t967
                push!(xs355, item357)
                cond356 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns358 = xs355
            consume_literal!(parser, ")")
            _t968 = Proto.ExportCSVColumns(columns=export_csv_columns358)
            _t969 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t968))
            _t966 = _t969
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t963 = _t966
    end
    return _t963
end

function parse_export_csv_column(parser::Parser)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string360 = consume_terminal!(parser, "STRING")
    _t970 = parse_relation_id(parser)
    relation_id361 = _t970
    consume_literal!(parser, ")")
    _t971 = Proto.ExportCSVColumn(column_name=string360, column_data=relation_id361)
    return _t971
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
