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

function _extract_value_boolean(parser::Parser, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    end
    return default
end

function construct_export_csv_config(parser::Parser, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t974 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t974
    _t975 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t975
    _t976 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t976
    _t977 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t977
    _t978 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t978
    _t979 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t979
    _t980 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t980
    _t981 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t981
end

function _extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    end
    return default
end

function _extract_value_string(parser::Parser, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    end
    return default
end

function _try_extract_value_bytes(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    end
    return nothing
end

function construct_betree_info(parser::Parser, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t982 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t982
    _t983 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t983
    _t984 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t984
    _t985 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t985
    _t986 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t986
    _t987 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t987
    _t988 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t988
    _t989 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t989
    _t990 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t990
    _t991 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t991
    _t992 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t992
end

function default_configure(parser::Parser)::Proto.Configure
    _t993 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t993
    _t994 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t994
end

function _try_extract_value_float64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    end
    return nothing
end

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
    _t995 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t995
    _t996 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t996
    _t997 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t997
end

function _try_extract_value_uint128(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    end
    return nothing
end

function construct_csv_config(parser::Parser, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t998 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t998
    _t999 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t999
    _t1000 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1000
    _t1001 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1001
    _t1002 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1002
    _t1003 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1003
    _t1004 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1004
    _t1005 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1005
    _t1006 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1006
    _t1007 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1007
    _t1008 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1008
    _t1009 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size = _t1009
    _t1010 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size)
    return _t1010
end

function _try_extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    end
    return nothing
end

function _extract_value_int32(parser::Parser, value::Union{Nothing, Proto.Value}, default::Int64)::Int32
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return Int32(_get_oneof_field(value, :int_value))
    end
    return Int32(default)
end

function construct_export_csv_config_with_source(parser::Parser, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1011 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1011
end

function _extract_value_string_list(parser::Parser, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    end
    return default
end

# --- Parse functions ---

function parse_transaction(parser::Parser)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t364 = parse_configure(parser)
        _t363 = _t364
    else
        _t363 = nothing
    end
    configure0 = _t363
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t366 = parse_sync(parser)
        _t365 = _t366
    else
        _t365 = nothing
    end
    sync1 = _t365
    xs2 = Proto.Epoch[]
    cond3 = match_lookahead_literal(parser, "(", 0)
    while cond3
        _t367 = parse_epoch(parser)
        item4 = _t367
        push!(xs2, item4)
        cond3 = match_lookahead_literal(parser, "(", 0)
    end
    epochs5 = xs2
    consume_literal!(parser, ")")
    _t368 = default_configure(parser)
    _t369 = Proto.Transaction(epochs=epochs5, configure=(!isnothing(configure0) ? configure0 : _t368), sync=sync1)
    return _t369
end

function parse_configure(parser::Parser)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t370 = parse_config_dict(parser)
    config_dict6 = _t370
    consume_literal!(parser, ")")
    _t371 = construct_configure(parser, config_dict6)
    return _t371
end

function parse_config_dict(parser::Parser)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs7 = Tuple{String, Proto.Value}[]
    cond8 = match_lookahead_literal(parser, ":", 0)
    while cond8
        _t372 = parse_config_key_value(parser)
        item9 = _t372
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
    _t373 = parse_value(parser)
    value12 = _t373
    return (symbol11, value12,)
end

function parse_value(parser::Parser)::Proto.Value
    
    if match_lookahead_literal(parser, "true", 0)
        _t374 = 9
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t375 = 8
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t376 = 9
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t378 = 1
                    else
                        
                        if match_lookahead_literal(parser, "date", 1)
                            _t379 = 0
                        else
                            _t379 = -1
                        end
                        _t378 = _t379
                    end
                    _t377 = _t378
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t380 = 5
                    else
                        
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t381 = 2
                        else
                            
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t382 = 6
                            else
                                
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t383 = 3
                                else
                                    
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t384 = 4
                                    else
                                        
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t385 = 7
                                        else
                                            _t385 = -1
                                        end
                                        _t384 = _t385
                                    end
                                    _t383 = _t384
                                end
                                _t382 = _t383
                            end
                            _t381 = _t382
                        end
                        _t380 = _t381
                    end
                    _t377 = _t380
                end
                _t376 = _t377
            end
            _t375 = _t376
        end
        _t374 = _t375
    end
    prediction13 = _t374
    
    if prediction13 == 9
        _t387 = parse_boolean_value(parser)
        boolean_value22 = _t387
        _t388 = Proto.Value(value=OneOf(:boolean_value, boolean_value22))
        _t386 = _t388
    else
        
        if prediction13 == 8
            consume_literal!(parser, "missing")
            _t390 = Proto.MissingValue()
            _t391 = Proto.Value(value=OneOf(:missing_value, _t390))
            _t389 = _t391
        else
            
            if prediction13 == 7
                decimal21 = consume_terminal!(parser, "DECIMAL")
                _t393 = Proto.Value(value=OneOf(:decimal_value, decimal21))
                _t392 = _t393
            else
                
                if prediction13 == 6
                    int12820 = consume_terminal!(parser, "INT128")
                    _t395 = Proto.Value(value=OneOf(:int128_value, int12820))
                    _t394 = _t395
                else
                    
                    if prediction13 == 5
                        uint12819 = consume_terminal!(parser, "UINT128")
                        _t397 = Proto.Value(value=OneOf(:uint128_value, uint12819))
                        _t396 = _t397
                    else
                        
                        if prediction13 == 4
                            float18 = consume_terminal!(parser, "FLOAT")
                            _t399 = Proto.Value(value=OneOf(:float_value, float18))
                            _t398 = _t399
                        else
                            
                            if prediction13 == 3
                                int17 = consume_terminal!(parser, "INT")
                                _t401 = Proto.Value(value=OneOf(:int_value, int17))
                                _t400 = _t401
                            else
                                
                                if prediction13 == 2
                                    string16 = consume_terminal!(parser, "STRING")
                                    _t403 = Proto.Value(value=OneOf(:string_value, string16))
                                    _t402 = _t403
                                else
                                    
                                    if prediction13 == 1
                                        _t405 = parse_datetime(parser)
                                        datetime15 = _t405
                                        _t406 = Proto.Value(value=OneOf(:datetime_value, datetime15))
                                        _t404 = _t406
                                    else
                                        
                                        if prediction13 == 0
                                            _t408 = parse_date(parser)
                                            date14 = _t408
                                            _t409 = Proto.Value(value=OneOf(:date_value, date14))
                                            _t407 = _t409
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t404 = _t407
                                    end
                                    _t402 = _t404
                                end
                                _t400 = _t402
                            end
                            _t398 = _t400
                        end
                        _t396 = _t398
                    end
                    _t394 = _t396
                end
                _t392 = _t394
            end
            _t389 = _t392
        end
        _t386 = _t389
    end
    return _t386
end

function parse_date(parser::Parser)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int23 = consume_terminal!(parser, "INT")
    int_324 = consume_terminal!(parser, "INT")
    int_425 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t410 = Proto.DateValue(year=Int32(int23), month=Int32(int_324), day=Int32(int_425))
    return _t410
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
        _t411 = consume_terminal!(parser, "INT")
    else
        _t411 = nothing
    end
    int_832 = _t411
    consume_literal!(parser, ")")
    _t412 = Proto.DateTimeValue(year=Int32(int26), month=Int32(int_327), day=Int32(int_428), hour=Int32(int_529), minute=Int32(int_630), second=Int32(int_731), microsecond=Int32((!isnothing(int_832) ? int_832 : 0)))
    return _t412
end

function parse_boolean_value(parser::Parser)::Bool
    
    if match_lookahead_literal(parser, "true", 0)
        _t413 = 0
    else
        
        if match_lookahead_literal(parser, "false", 0)
            _t414 = 1
        else
            _t414 = -1
        end
        _t413 = _t414
    end
    prediction33 = _t413
    
    if prediction33 == 1
        consume_literal!(parser, "false")
        _t415 = false
    else
        
        if prediction33 == 0
            consume_literal!(parser, "true")
            _t416 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t415 = _t416
    end
    return _t415
end

function parse_sync(parser::Parser)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs34 = Proto.FragmentId[]
    cond35 = match_lookahead_literal(parser, ":", 0)
    while cond35
        _t417 = parse_fragment_id(parser)
        item36 = _t417
        push!(xs34, item36)
        cond35 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids37 = xs34
    consume_literal!(parser, ")")
    _t418 = Proto.Sync(fragments=fragment_ids37)
    return _t418
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
        _t420 = parse_epoch_writes(parser)
        _t419 = _t420
    else
        _t419 = nothing
    end
    epoch_writes39 = _t419
    
    if match_lookahead_literal(parser, "(", 0)
        _t422 = parse_epoch_reads(parser)
        _t421 = _t422
    else
        _t421 = nothing
    end
    epoch_reads40 = _t421
    consume_literal!(parser, ")")
    _t423 = Proto.Epoch(writes=(!isnothing(epoch_writes39) ? epoch_writes39 : Proto.Write[]), reads=(!isnothing(epoch_reads40) ? epoch_reads40 : Proto.Read[]))
    return _t423
end

function parse_epoch_writes(parser::Parser)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs41 = Proto.Write[]
    cond42 = match_lookahead_literal(parser, "(", 0)
    while cond42
        _t424 = parse_write(parser)
        item43 = _t424
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
            _t426 = 1
        else
            
            if match_lookahead_literal(parser, "define", 1)
                _t427 = 0
            else
                
                if match_lookahead_literal(parser, "context", 1)
                    _t428 = 2
                else
                    _t428 = -1
                end
                _t427 = _t428
            end
            _t426 = _t427
        end
        _t425 = _t426
    else
        _t425 = -1
    end
    prediction45 = _t425
    
    if prediction45 == 2
        _t430 = parse_context(parser)
        context48 = _t430
        _t431 = Proto.Write(write_type=OneOf(:context, context48))
        _t429 = _t431
    else
        
        if prediction45 == 1
            _t433 = parse_undefine(parser)
            undefine47 = _t433
            _t434 = Proto.Write(write_type=OneOf(:undefine, undefine47))
            _t432 = _t434
        else
            
            if prediction45 == 0
                _t436 = parse_define(parser)
                define46 = _t436
                _t437 = Proto.Write(write_type=OneOf(:define, define46))
                _t435 = _t437
            else
                throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
            end
            _t432 = _t435
        end
        _t429 = _t432
    end
    return _t429
end

function parse_define(parser::Parser)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t438 = parse_fragment(parser)
    fragment49 = _t438
    consume_literal!(parser, ")")
    _t439 = Proto.Define(fragment=fragment49)
    return _t439
end

function parse_fragment(parser::Parser)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t440 = parse_new_fragment_id(parser)
    new_fragment_id50 = _t440
    xs51 = Proto.Declaration[]
    cond52 = match_lookahead_literal(parser, "(", 0)
    while cond52
        _t441 = parse_declaration(parser)
        item53 = _t441
        push!(xs51, item53)
        cond52 = match_lookahead_literal(parser, "(", 0)
    end
    declarations54 = xs51
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id50, declarations54)
end

function parse_new_fragment_id(parser::Parser)::Proto.FragmentId
    _t442 = parse_fragment_id(parser)
    fragment_id55 = _t442
    start_fragment!(parser, fragment_id55)
    return fragment_id55
end

function parse_declaration(parser::Parser)::Proto.Declaration
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t444 = 3
        else
            
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t445 = 2
            else
                
                if match_lookahead_literal(parser, "def", 1)
                    _t446 = 0
                else
                    
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t447 = 3
                    else
                        
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t448 = 3
                        else
                            
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t449 = 1
                            else
                                _t449 = -1
                            end
                            _t448 = _t449
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
    else
        _t443 = -1
    end
    prediction56 = _t443
    
    if prediction56 == 3
        _t451 = parse_data(parser)
        data60 = _t451
        _t452 = Proto.Declaration(declaration_type=OneOf(:data, data60))
        _t450 = _t452
    else
        
        if prediction56 == 2
            _t454 = parse_constraint(parser)
            constraint59 = _t454
            _t455 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint59))
            _t453 = _t455
        else
            
            if prediction56 == 1
                _t457 = parse_algorithm(parser)
                algorithm58 = _t457
                _t458 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm58))
                _t456 = _t458
            else
                
                if prediction56 == 0
                    _t460 = parse_def(parser)
                    def57 = _t460
                    _t461 = Proto.Declaration(declaration_type=OneOf(:def, def57))
                    _t459 = _t461
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t456 = _t459
            end
            _t453 = _t456
        end
        _t450 = _t453
    end
    return _t450
end

function parse_def(parser::Parser)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t462 = parse_relation_id(parser)
    relation_id61 = _t462
    _t463 = parse_abstraction(parser)
    abstraction62 = _t463
    
    if match_lookahead_literal(parser, "(", 0)
        _t465 = parse_attrs(parser)
        _t464 = _t465
    else
        _t464 = nothing
    end
    attrs63 = _t464
    consume_literal!(parser, ")")
    _t466 = Proto.Def(name=relation_id61, body=abstraction62, attrs=(!isnothing(attrs63) ? attrs63 : Proto.Attribute[]))
    return _t466
end

function parse_relation_id(parser::Parser)::Proto.RelationId
    
    if match_lookahead_literal(parser, ":", 0)
        _t467 = 0
    else
        
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t468 = 1
        else
            _t468 = -1
        end
        _t467 = _t468
    end
    prediction64 = _t467
    
    if prediction64 == 1
        uint12866 = consume_terminal!(parser, "UINT128")
        _t469 = Proto.RelationId(uint12866.low, uint12866.high)
    else
        
        if prediction64 == 0
            consume_literal!(parser, ":")
            symbol65 = consume_terminal!(parser, "SYMBOL")
            _t470 = relation_id_from_string(parser, symbol65)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t469 = _t470
    end
    return _t469
end

function parse_abstraction(parser::Parser)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t471 = parse_bindings(parser)
    bindings67 = _t471
    _t472 = parse_formula(parser)
    formula68 = _t472
    consume_literal!(parser, ")")
    _t473 = Proto.Abstraction(vars=vcat(bindings67[1], !isnothing(bindings67[2]) ? bindings67[2] : []), value=formula68)
    return _t473
end

function parse_bindings(parser::Parser)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs69 = Proto.Binding[]
    cond70 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond70
        _t474 = parse_binding(parser)
        item71 = _t474
        push!(xs69, item71)
        cond70 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings72 = xs69
    
    if match_lookahead_literal(parser, "|", 0)
        _t476 = parse_value_bindings(parser)
        _t475 = _t476
    else
        _t475 = nothing
    end
    value_bindings73 = _t475
    consume_literal!(parser, "]")
    return (bindings72, (!isnothing(value_bindings73) ? value_bindings73 : Proto.Binding[]),)
end

function parse_binding(parser::Parser)::Proto.Binding
    symbol74 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t477 = parse_type(parser)
    type75 = _t477
    _t478 = Proto.Var(name=symbol74)
    _t479 = Proto.Binding(var=_t478, var"#type"=type75)
    return _t479
end

function parse_type(parser::Parser)::Proto.var"#Type"
    
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t480 = 0
    else
        
        if match_lookahead_literal(parser, "UINT128", 0)
            _t481 = 4
        else
            
            if match_lookahead_literal(parser, "STRING", 0)
                _t482 = 1
            else
                
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t483 = 8
                else
                    
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t484 = 5
                    else
                        
                        if match_lookahead_literal(parser, "INT", 0)
                            _t485 = 2
                        else
                            
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t486 = 3
                            else
                                
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t487 = 7
                                else
                                    
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t488 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t489 = 10
                                        else
                                            
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t490 = 9
                                            else
                                                _t490 = -1
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
                    end
                    _t483 = _t484
                end
                _t482 = _t483
            end
            _t481 = _t482
        end
        _t480 = _t481
    end
    prediction76 = _t480
    
    if prediction76 == 10
        _t492 = parse_boolean_type(parser)
        boolean_type87 = _t492
        _t493 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type87))
        _t491 = _t493
    else
        
        if prediction76 == 9
            _t495 = parse_decimal_type(parser)
            decimal_type86 = _t495
            _t496 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type86))
            _t494 = _t496
        else
            
            if prediction76 == 8
                _t498 = parse_missing_type(parser)
                missing_type85 = _t498
                _t499 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type85))
                _t497 = _t499
            else
                
                if prediction76 == 7
                    _t501 = parse_datetime_type(parser)
                    datetime_type84 = _t501
                    _t502 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type84))
                    _t500 = _t502
                else
                    
                    if prediction76 == 6
                        _t504 = parse_date_type(parser)
                        date_type83 = _t504
                        _t505 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type83))
                        _t503 = _t505
                    else
                        
                        if prediction76 == 5
                            _t507 = parse_int128_type(parser)
                            int128_type82 = _t507
                            _t508 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type82))
                            _t506 = _t508
                        else
                            
                            if prediction76 == 4
                                _t510 = parse_uint128_type(parser)
                                uint128_type81 = _t510
                                _t511 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type81))
                                _t509 = _t511
                            else
                                
                                if prediction76 == 3
                                    _t513 = parse_float_type(parser)
                                    float_type80 = _t513
                                    _t514 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type80))
                                    _t512 = _t514
                                else
                                    
                                    if prediction76 == 2
                                        _t516 = parse_int_type(parser)
                                        int_type79 = _t516
                                        _t517 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type79))
                                        _t515 = _t517
                                    else
                                        
                                        if prediction76 == 1
                                            _t519 = parse_string_type(parser)
                                            string_type78 = _t519
                                            _t520 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type78))
                                            _t518 = _t520
                                        else
                                            
                                            if prediction76 == 0
                                                _t522 = parse_unspecified_type(parser)
                                                unspecified_type77 = _t522
                                                _t523 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type77))
                                                _t521 = _t523
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                        _t503 = _t506
                    end
                    _t500 = _t503
                end
                _t497 = _t500
            end
            _t494 = _t497
        end
        _t491 = _t494
    end
    return _t491
end

function parse_unspecified_type(parser::Parser)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t524 = Proto.UnspecifiedType()
    return _t524
end

function parse_string_type(parser::Parser)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t525 = Proto.StringType()
    return _t525
end

function parse_int_type(parser::Parser)::Proto.IntType
    consume_literal!(parser, "INT")
    _t526 = Proto.IntType()
    return _t526
end

function parse_float_type(parser::Parser)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t527 = Proto.FloatType()
    return _t527
end

function parse_uint128_type(parser::Parser)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t528 = Proto.UInt128Type()
    return _t528
end

function parse_int128_type(parser::Parser)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t529 = Proto.Int128Type()
    return _t529
end

function parse_date_type(parser::Parser)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t530 = Proto.DateType()
    return _t530
end

function parse_datetime_type(parser::Parser)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t531 = Proto.DateTimeType()
    return _t531
end

function parse_missing_type(parser::Parser)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t532 = Proto.MissingType()
    return _t532
end

function parse_decimal_type(parser::Parser)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int88 = consume_terminal!(parser, "INT")
    int_389 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t533 = Proto.DecimalType(precision=Int32(int88), scale=Int32(int_389))
    return _t533
end

function parse_boolean_type(parser::Parser)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t534 = Proto.BooleanType()
    return _t534
end

function parse_value_bindings(parser::Parser)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs90 = Proto.Binding[]
    cond91 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond91
        _t535 = parse_binding(parser)
        item92 = _t535
        push!(xs90, item92)
        cond91 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings93 = xs90
    return bindings93
end

function parse_formula(parser::Parser)::Proto.Formula
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "true", 1)
            _t537 = 0
        else
            
            if match_lookahead_literal(parser, "relatom", 1)
                _t538 = 11
            else
                
                if match_lookahead_literal(parser, "reduce", 1)
                    _t539 = 3
                else
                    
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t540 = 10
                    else
                        
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t541 = 9
                        else
                            
                            if match_lookahead_literal(parser, "or", 1)
                                _t542 = 5
                            else
                                
                                if match_lookahead_literal(parser, "not", 1)
                                    _t543 = 6
                                else
                                    
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t544 = 7
                                    else
                                        
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t545 = 1
                                        else
                                            
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t546 = 2
                                            else
                                                
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t547 = 12
                                                else
                                                    
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t548 = 8
                                                    else
                                                        
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t549 = 4
                                                        else
                                                            
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t550 = 10
                                                            else
                                                                
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t551 = 10
                                                                else
                                                                    
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t552 = 10
                                                                    else
                                                                        
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t553 = 10
                                                                        else
                                                                            
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t554 = 10
                                                                            else
                                                                                
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t555 = 10
                                                                                else
                                                                                    
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t556 = 10
                                                                                    else
                                                                                        
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t557 = 10
                                                                                        else
                                                                                            
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t558 = 10
                                                                                            else
                                                                                                _t558 = -1
                                                                                            end
                                                                                            _t557 = _t558
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
    else
        _t536 = -1
    end
    prediction94 = _t536
    
    if prediction94 == 12
        _t560 = parse_cast(parser)
        cast107 = _t560
        _t561 = Proto.Formula(formula_type=OneOf(:cast, cast107))
        _t559 = _t561
    else
        
        if prediction94 == 11
            _t563 = parse_rel_atom(parser)
            rel_atom106 = _t563
            _t564 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom106))
            _t562 = _t564
        else
            
            if prediction94 == 10
                _t566 = parse_primitive(parser)
                primitive105 = _t566
                _t567 = Proto.Formula(formula_type=OneOf(:primitive, primitive105))
                _t565 = _t567
            else
                
                if prediction94 == 9
                    _t569 = parse_pragma(parser)
                    pragma104 = _t569
                    _t570 = Proto.Formula(formula_type=OneOf(:pragma, pragma104))
                    _t568 = _t570
                else
                    
                    if prediction94 == 8
                        _t572 = parse_atom(parser)
                        atom103 = _t572
                        _t573 = Proto.Formula(formula_type=OneOf(:atom, atom103))
                        _t571 = _t573
                    else
                        
                        if prediction94 == 7
                            _t575 = parse_ffi(parser)
                            ffi102 = _t575
                            _t576 = Proto.Formula(formula_type=OneOf(:ffi, ffi102))
                            _t574 = _t576
                        else
                            
                            if prediction94 == 6
                                _t578 = parse_not(parser)
                                not101 = _t578
                                _t579 = Proto.Formula(formula_type=OneOf(:not, not101))
                                _t577 = _t579
                            else
                                
                                if prediction94 == 5
                                    _t581 = parse_disjunction(parser)
                                    disjunction100 = _t581
                                    _t582 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction100))
                                    _t580 = _t582
                                else
                                    
                                    if prediction94 == 4
                                        _t584 = parse_conjunction(parser)
                                        conjunction99 = _t584
                                        _t585 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction99))
                                        _t583 = _t585
                                    else
                                        
                                        if prediction94 == 3
                                            _t587 = parse_reduce(parser)
                                            reduce98 = _t587
                                            _t588 = Proto.Formula(formula_type=OneOf(:reduce, reduce98))
                                            _t586 = _t588
                                        else
                                            
                                            if prediction94 == 2
                                                _t590 = parse_exists(parser)
                                                exists97 = _t590
                                                _t591 = Proto.Formula(formula_type=OneOf(:exists, exists97))
                                                _t589 = _t591
                                            else
                                                
                                                if prediction94 == 1
                                                    _t593 = parse_false(parser)
                                                    false96 = _t593
                                                    _t594 = Proto.Formula(formula_type=OneOf(:disjunction, false96))
                                                    _t592 = _t594
                                                else
                                                    
                                                    if prediction94 == 0
                                                        _t596 = parse_true(parser)
                                                        true95 = _t596
                                                        _t597 = Proto.Formula(formula_type=OneOf(:conjunction, true95))
                                                        _t595 = _t597
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t592 = _t595
                                                end
                                                _t589 = _t592
                                            end
                                            _t586 = _t589
                                        end
                                        _t583 = _t586
                                    end
                                    _t580 = _t583
                                end
                                _t577 = _t580
                            end
                            _t574 = _t577
                        end
                        _t571 = _t574
                    end
                    _t568 = _t571
                end
                _t565 = _t568
            end
            _t562 = _t565
        end
        _t559 = _t562
    end
    return _t559
end

function parse_true(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t598 = Proto.Conjunction(args=Proto.Formula[])
    return _t598
end

function parse_false(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t599 = Proto.Disjunction(args=Proto.Formula[])
    return _t599
end

function parse_exists(parser::Parser)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t600 = parse_bindings(parser)
    bindings108 = _t600
    _t601 = parse_formula(parser)
    formula109 = _t601
    consume_literal!(parser, ")")
    _t602 = Proto.Abstraction(vars=vcat(bindings108[1], !isnothing(bindings108[2]) ? bindings108[2] : []), value=formula109)
    _t603 = Proto.Exists(body=_t602)
    return _t603
end

function parse_reduce(parser::Parser)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t604 = parse_abstraction(parser)
    abstraction110 = _t604
    _t605 = parse_abstraction(parser)
    abstraction_3111 = _t605
    _t606 = parse_terms(parser)
    terms112 = _t606
    consume_literal!(parser, ")")
    _t607 = Proto.Reduce(op=abstraction110, body=abstraction_3111, terms=terms112)
    return _t607
end

function parse_terms(parser::Parser)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs113 = Proto.Term[]
    cond114 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond114
        _t608 = parse_term(parser)
        item115 = _t608
        push!(xs113, item115)
        cond114 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms116 = xs113
    consume_literal!(parser, ")")
    return terms116
end

function parse_term(parser::Parser)::Proto.Term
    
    if match_lookahead_literal(parser, "true", 0)
        _t609 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t610 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t611 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t612 = 1
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t613 = 1
                    else
                        
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t614 = 0
                        else
                            
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t615 = 1
                            else
                                
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t616 = 1
                                else
                                    
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t617 = 1
                                    else
                                        
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t618 = 1
                                        else
                                            
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t619 = 1
                                            else
                                                _t619 = -1
                                            end
                                            _t618 = _t619
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
    prediction117 = _t609
    
    if prediction117 == 1
        _t621 = parse_constant(parser)
        constant119 = _t621
        _t622 = Proto.Term(term_type=OneOf(:constant, constant119))
        _t620 = _t622
    else
        
        if prediction117 == 0
            _t624 = parse_var(parser)
            var118 = _t624
            _t625 = Proto.Term(term_type=OneOf(:var, var118))
            _t623 = _t625
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t620 = _t623
    end
    return _t620
end

function parse_var(parser::Parser)::Proto.Var
    symbol120 = consume_terminal!(parser, "SYMBOL")
    _t626 = Proto.Var(name=symbol120)
    return _t626
end

function parse_constant(parser::Parser)::Proto.Value
    _t627 = parse_value(parser)
    value121 = _t627
    return value121
end

function parse_conjunction(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs122 = Proto.Formula[]
    cond123 = match_lookahead_literal(parser, "(", 0)
    while cond123
        _t628 = parse_formula(parser)
        item124 = _t628
        push!(xs122, item124)
        cond123 = match_lookahead_literal(parser, "(", 0)
    end
    formulas125 = xs122
    consume_literal!(parser, ")")
    _t629 = Proto.Conjunction(args=formulas125)
    return _t629
end

function parse_disjunction(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs126 = Proto.Formula[]
    cond127 = match_lookahead_literal(parser, "(", 0)
    while cond127
        _t630 = parse_formula(parser)
        item128 = _t630
        push!(xs126, item128)
        cond127 = match_lookahead_literal(parser, "(", 0)
    end
    formulas129 = xs126
    consume_literal!(parser, ")")
    _t631 = Proto.Disjunction(args=formulas129)
    return _t631
end

function parse_not(parser::Parser)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t632 = parse_formula(parser)
    formula130 = _t632
    consume_literal!(parser, ")")
    _t633 = Proto.Not(arg=formula130)
    return _t633
end

function parse_ffi(parser::Parser)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t634 = parse_name(parser)
    name131 = _t634
    _t635 = parse_ffi_args(parser)
    ffi_args132 = _t635
    _t636 = parse_terms(parser)
    terms133 = _t636
    consume_literal!(parser, ")")
    _t637 = Proto.FFI(name=name131, args=ffi_args132, terms=terms133)
    return _t637
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
        _t638 = parse_abstraction(parser)
        item137 = _t638
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
    _t639 = parse_relation_id(parser)
    relation_id139 = _t639
    xs140 = Proto.Term[]
    cond141 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond141
        _t640 = parse_term(parser)
        item142 = _t640
        push!(xs140, item142)
        cond141 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms143 = xs140
    consume_literal!(parser, ")")
    _t641 = Proto.Atom(name=relation_id139, terms=terms143)
    return _t641
end

function parse_pragma(parser::Parser)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t642 = parse_name(parser)
    name144 = _t642
    xs145 = Proto.Term[]
    cond146 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond146
        _t643 = parse_term(parser)
        item147 = _t643
        push!(xs145, item147)
        cond146 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms148 = xs145
    consume_literal!(parser, ")")
    _t644 = Proto.Pragma(name=name144, terms=terms148)
    return _t644
end

function parse_primitive(parser::Parser)::Proto.Primitive
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "primitive", 1)
            _t646 = 9
        else
            
            if match_lookahead_literal(parser, ">=", 1)
                _t647 = 4
            else
                
                if match_lookahead_literal(parser, ">", 1)
                    _t648 = 3
                else
                    
                    if match_lookahead_literal(parser, "=", 1)
                        _t649 = 0
                    else
                        
                        if match_lookahead_literal(parser, "<=", 1)
                            _t650 = 2
                        else
                            
                            if match_lookahead_literal(parser, "<", 1)
                                _t651 = 1
                            else
                                
                                if match_lookahead_literal(parser, "/", 1)
                                    _t652 = 8
                                else
                                    
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t653 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t654 = 5
                                        else
                                            
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t655 = 7
                                            else
                                                _t655 = -1
                                            end
                                            _t654 = _t655
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
    else
        _t645 = -1
    end
    prediction149 = _t645
    
    if prediction149 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t657 = parse_name(parser)
        name159 = _t657
        xs160 = Proto.RelTerm[]
        cond161 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond161
            _t658 = parse_rel_term(parser)
            item162 = _t658
            push!(xs160, item162)
            cond161 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms163 = xs160
        consume_literal!(parser, ")")
        _t659 = Proto.Primitive(name=name159, terms=rel_terms163)
        _t656 = _t659
    else
        
        if prediction149 == 8
            _t661 = parse_divide(parser)
            divide158 = _t661
            _t660 = divide158
        else
            
            if prediction149 == 7
                _t663 = parse_multiply(parser)
                multiply157 = _t663
                _t662 = multiply157
            else
                
                if prediction149 == 6
                    _t665 = parse_minus(parser)
                    minus156 = _t665
                    _t664 = minus156
                else
                    
                    if prediction149 == 5
                        _t667 = parse_add(parser)
                        add155 = _t667
                        _t666 = add155
                    else
                        
                        if prediction149 == 4
                            _t669 = parse_gt_eq(parser)
                            gt_eq154 = _t669
                            _t668 = gt_eq154
                        else
                            
                            if prediction149 == 3
                                _t671 = parse_gt(parser)
                                gt153 = _t671
                                _t670 = gt153
                            else
                                
                                if prediction149 == 2
                                    _t673 = parse_lt_eq(parser)
                                    lt_eq152 = _t673
                                    _t672 = lt_eq152
                                else
                                    
                                    if prediction149 == 1
                                        _t675 = parse_lt(parser)
                                        lt151 = _t675
                                        _t674 = lt151
                                    else
                                        
                                        if prediction149 == 0
                                            _t677 = parse_eq(parser)
                                            eq150 = _t677
                                            _t676 = eq150
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t674 = _t676
                                    end
                                    _t672 = _t674
                                end
                                _t670 = _t672
                            end
                            _t668 = _t670
                        end
                        _t666 = _t668
                    end
                    _t664 = _t666
                end
                _t662 = _t664
            end
            _t660 = _t662
        end
        _t656 = _t660
    end
    return _t656
end

function parse_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t678 = parse_term(parser)
    term164 = _t678
    _t679 = parse_term(parser)
    term_3165 = _t679
    consume_literal!(parser, ")")
    _t680 = Proto.RelTerm(rel_term_type=OneOf(:term, term164))
    _t681 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3165))
    _t682 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t680, _t681])
    return _t682
end

function parse_lt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t683 = parse_term(parser)
    term166 = _t683
    _t684 = parse_term(parser)
    term_3167 = _t684
    consume_literal!(parser, ")")
    _t685 = Proto.RelTerm(rel_term_type=OneOf(:term, term166))
    _t686 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3167))
    _t687 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t685, _t686])
    return _t687
end

function parse_lt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t688 = parse_term(parser)
    term168 = _t688
    _t689 = parse_term(parser)
    term_3169 = _t689
    consume_literal!(parser, ")")
    _t690 = Proto.RelTerm(rel_term_type=OneOf(:term, term168))
    _t691 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3169))
    _t692 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t690, _t691])
    return _t692
end

function parse_gt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t693 = parse_term(parser)
    term170 = _t693
    _t694 = parse_term(parser)
    term_3171 = _t694
    consume_literal!(parser, ")")
    _t695 = Proto.RelTerm(rel_term_type=OneOf(:term, term170))
    _t696 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3171))
    _t697 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t695, _t696])
    return _t697
end

function parse_gt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t698 = parse_term(parser)
    term172 = _t698
    _t699 = parse_term(parser)
    term_3173 = _t699
    consume_literal!(parser, ")")
    _t700 = Proto.RelTerm(rel_term_type=OneOf(:term, term172))
    _t701 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3173))
    _t702 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t700, _t701])
    return _t702
end

function parse_add(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t703 = parse_term(parser)
    term174 = _t703
    _t704 = parse_term(parser)
    term_3175 = _t704
    _t705 = parse_term(parser)
    term_4176 = _t705
    consume_literal!(parser, ")")
    _t706 = Proto.RelTerm(rel_term_type=OneOf(:term, term174))
    _t707 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3175))
    _t708 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4176))
    _t709 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t706, _t707, _t708])
    return _t709
end

function parse_minus(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t710 = parse_term(parser)
    term177 = _t710
    _t711 = parse_term(parser)
    term_3178 = _t711
    _t712 = parse_term(parser)
    term_4179 = _t712
    consume_literal!(parser, ")")
    _t713 = Proto.RelTerm(rel_term_type=OneOf(:term, term177))
    _t714 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3178))
    _t715 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4179))
    _t716 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t713, _t714, _t715])
    return _t716
end

function parse_multiply(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t717 = parse_term(parser)
    term180 = _t717
    _t718 = parse_term(parser)
    term_3181 = _t718
    _t719 = parse_term(parser)
    term_4182 = _t719
    consume_literal!(parser, ")")
    _t720 = Proto.RelTerm(rel_term_type=OneOf(:term, term180))
    _t721 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3181))
    _t722 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4182))
    _t723 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t720, _t721, _t722])
    return _t723
end

function parse_divide(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t724 = parse_term(parser)
    term183 = _t724
    _t725 = parse_term(parser)
    term_3184 = _t725
    _t726 = parse_term(parser)
    term_4185 = _t726
    consume_literal!(parser, ")")
    _t727 = Proto.RelTerm(rel_term_type=OneOf(:term, term183))
    _t728 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3184))
    _t729 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4185))
    _t730 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t727, _t728, _t729])
    return _t730
end

function parse_rel_term(parser::Parser)::Proto.RelTerm
    
    if match_lookahead_literal(parser, "true", 0)
        _t731 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t732 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t733 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t734 = 1
                else
                    
                    if match_lookahead_literal(parser, "#", 0)
                        _t735 = 0
                    else
                        
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t736 = 1
                        else
                            
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t737 = 1
                            else
                                
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t738 = 1
                                else
                                    
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t739 = 1
                                    else
                                        
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t740 = 1
                                        else
                                            
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t741 = 1
                                            else
                                                
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t742 = 1
                                                else
                                                    _t742 = -1
                                                end
                                                _t741 = _t742
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
    prediction186 = _t731
    
    if prediction186 == 1
        _t744 = parse_term(parser)
        term188 = _t744
        _t745 = Proto.RelTerm(rel_term_type=OneOf(:term, term188))
        _t743 = _t745
    else
        
        if prediction186 == 0
            _t747 = parse_specialized_value(parser)
            specialized_value187 = _t747
            _t748 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value187))
            _t746 = _t748
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t743 = _t746
    end
    return _t743
end

function parse_specialized_value(parser::Parser)::Proto.Value
    consume_literal!(parser, "#")
    _t749 = parse_value(parser)
    value189 = _t749
    return value189
end

function parse_rel_atom(parser::Parser)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t750 = parse_name(parser)
    name190 = _t750
    xs191 = Proto.RelTerm[]
    cond192 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond192
        _t751 = parse_rel_term(parser)
        item193 = _t751
        push!(xs191, item193)
        cond192 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms194 = xs191
    consume_literal!(parser, ")")
    _t752 = Proto.RelAtom(name=name190, terms=rel_terms194)
    return _t752
end

function parse_cast(parser::Parser)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t753 = parse_term(parser)
    term195 = _t753
    _t754 = parse_term(parser)
    term_3196 = _t754
    consume_literal!(parser, ")")
    _t755 = Proto.Cast(input=term195, result=term_3196)
    return _t755
end

function parse_attrs(parser::Parser)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs197 = Proto.Attribute[]
    cond198 = match_lookahead_literal(parser, "(", 0)
    while cond198
        _t756 = parse_attribute(parser)
        item199 = _t756
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
    _t757 = parse_name(parser)
    name201 = _t757
    xs202 = Proto.Value[]
    cond203 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond203
        _t758 = parse_value(parser)
        item204 = _t758
        push!(xs202, item204)
        cond203 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values205 = xs202
    consume_literal!(parser, ")")
    _t759 = Proto.Attribute(name=name201, args=values205)
    return _t759
end

function parse_algorithm(parser::Parser)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs206 = Proto.RelationId[]
    cond207 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond207
        _t760 = parse_relation_id(parser)
        item208 = _t760
        push!(xs206, item208)
        cond207 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids209 = xs206
    _t761 = parse_script(parser)
    script210 = _t761
    consume_literal!(parser, ")")
    _t762 = Proto.Algorithm(var"#global"=relation_ids209, body=script210)
    return _t762
end

function parse_script(parser::Parser)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs211 = Proto.Construct[]
    cond212 = match_lookahead_literal(parser, "(", 0)
    while cond212
        _t763 = parse_construct(parser)
        item213 = _t763
        push!(xs211, item213)
        cond212 = match_lookahead_literal(parser, "(", 0)
    end
    constructs214 = xs211
    consume_literal!(parser, ")")
    _t764 = Proto.Script(constructs=constructs214)
    return _t764
end

function parse_construct(parser::Parser)::Proto.Construct
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t766 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t767 = 1
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t768 = 1
                else
                    
                    if match_lookahead_literal(parser, "loop", 1)
                        _t769 = 0
                    else
                        
                        if match_lookahead_literal(parser, "break", 1)
                            _t770 = 1
                        else
                            
                            if match_lookahead_literal(parser, "assign", 1)
                                _t771 = 1
                            else
                                _t771 = -1
                            end
                            _t770 = _t771
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
    else
        _t765 = -1
    end
    prediction215 = _t765
    
    if prediction215 == 1
        _t773 = parse_instruction(parser)
        instruction217 = _t773
        _t774 = Proto.Construct(construct_type=OneOf(:instruction, instruction217))
        _t772 = _t774
    else
        
        if prediction215 == 0
            _t776 = parse_loop(parser)
            loop216 = _t776
            _t777 = Proto.Construct(construct_type=OneOf(:loop, loop216))
            _t775 = _t777
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t772 = _t775
    end
    return _t772
end

function parse_loop(parser::Parser)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t778 = parse_init(parser)
    init218 = _t778
    _t779 = parse_script(parser)
    script219 = _t779
    consume_literal!(parser, ")")
    _t780 = Proto.Loop(init=init218, body=script219)
    return _t780
end

function parse_init(parser::Parser)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs220 = Proto.Instruction[]
    cond221 = match_lookahead_literal(parser, "(", 0)
    while cond221
        _t781 = parse_instruction(parser)
        item222 = _t781
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
            _t783 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t784 = 4
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t785 = 3
                else
                    
                    if match_lookahead_literal(parser, "break", 1)
                        _t786 = 2
                    else
                        
                        if match_lookahead_literal(parser, "assign", 1)
                            _t787 = 0
                        else
                            _t787 = -1
                        end
                        _t786 = _t787
                    end
                    _t785 = _t786
                end
                _t784 = _t785
            end
            _t783 = _t784
        end
        _t782 = _t783
    else
        _t782 = -1
    end
    prediction224 = _t782
    
    if prediction224 == 4
        _t789 = parse_monus_def(parser)
        monus_def229 = _t789
        _t790 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def229))
        _t788 = _t790
    else
        
        if prediction224 == 3
            _t792 = parse_monoid_def(parser)
            monoid_def228 = _t792
            _t793 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def228))
            _t791 = _t793
        else
            
            if prediction224 == 2
                _t795 = parse_break(parser)
                break227 = _t795
                _t796 = Proto.Instruction(instr_type=OneOf(:var"#break", break227))
                _t794 = _t796
            else
                
                if prediction224 == 1
                    _t798 = parse_upsert(parser)
                    upsert226 = _t798
                    _t799 = Proto.Instruction(instr_type=OneOf(:upsert, upsert226))
                    _t797 = _t799
                else
                    
                    if prediction224 == 0
                        _t801 = parse_assign(parser)
                        assign225 = _t801
                        _t802 = Proto.Instruction(instr_type=OneOf(:assign, assign225))
                        _t800 = _t802
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t797 = _t800
                end
                _t794 = _t797
            end
            _t791 = _t794
        end
        _t788 = _t791
    end
    return _t788
end

function parse_assign(parser::Parser)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t803 = parse_relation_id(parser)
    relation_id230 = _t803
    _t804 = parse_abstraction(parser)
    abstraction231 = _t804
    
    if match_lookahead_literal(parser, "(", 0)
        _t806 = parse_attrs(parser)
        _t805 = _t806
    else
        _t805 = nothing
    end
    attrs232 = _t805
    consume_literal!(parser, ")")
    _t807 = Proto.Assign(name=relation_id230, body=abstraction231, attrs=(!isnothing(attrs232) ? attrs232 : Proto.Attribute[]))
    return _t807
end

function parse_upsert(parser::Parser)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t808 = parse_relation_id(parser)
    relation_id233 = _t808
    _t809 = parse_abstraction_with_arity(parser)
    abstraction_with_arity234 = _t809
    
    if match_lookahead_literal(parser, "(", 0)
        _t811 = parse_attrs(parser)
        _t810 = _t811
    else
        _t810 = nothing
    end
    attrs235 = _t810
    consume_literal!(parser, ")")
    _t812 = Proto.Upsert(name=relation_id233, body=abstraction_with_arity234[1], attrs=(!isnothing(attrs235) ? attrs235 : Proto.Attribute[]), value_arity=abstraction_with_arity234[2])
    return _t812
end

function parse_abstraction_with_arity(parser::Parser)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t813 = parse_bindings(parser)
    bindings236 = _t813
    _t814 = parse_formula(parser)
    formula237 = _t814
    consume_literal!(parser, ")")
    _t815 = Proto.Abstraction(vars=vcat(bindings236[1], !isnothing(bindings236[2]) ? bindings236[2] : []), value=formula237)
    return (_t815, length(bindings236[2]),)
end

function parse_break(parser::Parser)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t816 = parse_relation_id(parser)
    relation_id238 = _t816
    _t817 = parse_abstraction(parser)
    abstraction239 = _t817
    
    if match_lookahead_literal(parser, "(", 0)
        _t819 = parse_attrs(parser)
        _t818 = _t819
    else
        _t818 = nothing
    end
    attrs240 = _t818
    consume_literal!(parser, ")")
    _t820 = Proto.Break(name=relation_id238, body=abstraction239, attrs=(!isnothing(attrs240) ? attrs240 : Proto.Attribute[]))
    return _t820
end

function parse_monoid_def(parser::Parser)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t821 = parse_monoid(parser)
    monoid241 = _t821
    _t822 = parse_relation_id(parser)
    relation_id242 = _t822
    _t823 = parse_abstraction_with_arity(parser)
    abstraction_with_arity243 = _t823
    
    if match_lookahead_literal(parser, "(", 0)
        _t825 = parse_attrs(parser)
        _t824 = _t825
    else
        _t824 = nothing
    end
    attrs244 = _t824
    consume_literal!(parser, ")")
    _t826 = Proto.MonoidDef(monoid=monoid241, name=relation_id242, body=abstraction_with_arity243[1], attrs=(!isnothing(attrs244) ? attrs244 : Proto.Attribute[]), value_arity=abstraction_with_arity243[2])
    return _t826
end

function parse_monoid(parser::Parser)::Proto.Monoid
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "sum", 1)
            _t828 = 3
        else
            
            if match_lookahead_literal(parser, "or", 1)
                _t829 = 0
            else
                
                if match_lookahead_literal(parser, "min", 1)
                    _t830 = 1
                else
                    
                    if match_lookahead_literal(parser, "max", 1)
                        _t831 = 2
                    else
                        _t831 = -1
                    end
                    _t830 = _t831
                end
                _t829 = _t830
            end
            _t828 = _t829
        end
        _t827 = _t828
    else
        _t827 = -1
    end
    prediction245 = _t827
    
    if prediction245 == 3
        _t833 = parse_sum_monoid(parser)
        sum_monoid249 = _t833
        _t834 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid249))
        _t832 = _t834
    else
        
        if prediction245 == 2
            _t836 = parse_max_monoid(parser)
            max_monoid248 = _t836
            _t837 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid248))
            _t835 = _t837
        else
            
            if prediction245 == 1
                _t839 = parse_min_monoid(parser)
                min_monoid247 = _t839
                _t840 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid247))
                _t838 = _t840
            else
                
                if prediction245 == 0
                    _t842 = parse_or_monoid(parser)
                    or_monoid246 = _t842
                    _t843 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid246))
                    _t841 = _t843
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t838 = _t841
            end
            _t835 = _t838
        end
        _t832 = _t835
    end
    return _t832
end

function parse_or_monoid(parser::Parser)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t844 = Proto.OrMonoid()
    return _t844
end

function parse_min_monoid(parser::Parser)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t845 = parse_type(parser)
    type250 = _t845
    consume_literal!(parser, ")")
    _t846 = Proto.MinMonoid(var"#type"=type250)
    return _t846
end

function parse_max_monoid(parser::Parser)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t847 = parse_type(parser)
    type251 = _t847
    consume_literal!(parser, ")")
    _t848 = Proto.MaxMonoid(var"#type"=type251)
    return _t848
end

function parse_sum_monoid(parser::Parser)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t849 = parse_type(parser)
    type252 = _t849
    consume_literal!(parser, ")")
    _t850 = Proto.SumMonoid(var"#type"=type252)
    return _t850
end

function parse_monus_def(parser::Parser)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t851 = parse_monoid(parser)
    monoid253 = _t851
    _t852 = parse_relation_id(parser)
    relation_id254 = _t852
    _t853 = parse_abstraction_with_arity(parser)
    abstraction_with_arity255 = _t853
    
    if match_lookahead_literal(parser, "(", 0)
        _t855 = parse_attrs(parser)
        _t854 = _t855
    else
        _t854 = nothing
    end
    attrs256 = _t854
    consume_literal!(parser, ")")
    _t856 = Proto.MonusDef(monoid=monoid253, name=relation_id254, body=abstraction_with_arity255[1], attrs=(!isnothing(attrs256) ? attrs256 : Proto.Attribute[]), value_arity=abstraction_with_arity255[2])
    return _t856
end

function parse_constraint(parser::Parser)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t857 = parse_relation_id(parser)
    relation_id257 = _t857
    _t858 = parse_abstraction(parser)
    abstraction258 = _t858
    _t859 = parse_functional_dependency_keys(parser)
    functional_dependency_keys259 = _t859
    _t860 = parse_functional_dependency_values(parser)
    functional_dependency_values260 = _t860
    consume_literal!(parser, ")")
    _t861 = Proto.FunctionalDependency(guard=abstraction258, keys=functional_dependency_keys259, values=functional_dependency_values260)
    _t862 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t861), name=relation_id257)
    return _t862
end

function parse_functional_dependency_keys(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs261 = Proto.Var[]
    cond262 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond262
        _t863 = parse_var(parser)
        item263 = _t863
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
        _t864 = parse_var(parser)
        item267 = _t864
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
            _t866 = 0
        else
            
            if match_lookahead_literal(parser, "csv_data", 1)
                _t867 = 2
            else
                
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t868 = 1
                else
                    _t868 = -1
                end
                _t867 = _t868
            end
            _t866 = _t867
        end
        _t865 = _t866
    else
        _t865 = -1
    end
    prediction269 = _t865
    
    if prediction269 == 2
        _t870 = parse_csv_data(parser)
        csv_data272 = _t870
        _t871 = Proto.Data(data_type=OneOf(:csv_data, csv_data272))
        _t869 = _t871
    else
        
        if prediction269 == 1
            _t873 = parse_betree_relation(parser)
            betree_relation271 = _t873
            _t874 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation271))
            _t872 = _t874
        else
            
            if prediction269 == 0
                _t876 = parse_rel_edb(parser)
                rel_edb270 = _t876
                _t877 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb270))
                _t875 = _t877
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t872 = _t875
        end
        _t869 = _t872
    end
    return _t869
end

function parse_rel_edb(parser::Parser)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t878 = parse_relation_id(parser)
    relation_id273 = _t878
    _t879 = parse_rel_edb_path(parser)
    rel_edb_path274 = _t879
    _t880 = parse_rel_edb_types(parser)
    rel_edb_types275 = _t880
    consume_literal!(parser, ")")
    _t881 = Proto.RelEDB(target_id=relation_id273, path=rel_edb_path274, types=rel_edb_types275)
    return _t881
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
        _t882 = parse_type(parser)
        item282 = _t882
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
    _t883 = parse_relation_id(parser)
    relation_id284 = _t883
    _t884 = parse_betree_info(parser)
    betree_info285 = _t884
    consume_literal!(parser, ")")
    _t885 = Proto.BeTreeRelation(name=relation_id284, relation_info=betree_info285)
    return _t885
end

function parse_betree_info(parser::Parser)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t886 = parse_betree_info_key_types(parser)
    betree_info_key_types286 = _t886
    _t887 = parse_betree_info_value_types(parser)
    betree_info_value_types287 = _t887
    _t888 = parse_config_dict(parser)
    config_dict288 = _t888
    consume_literal!(parser, ")")
    _t889 = construct_betree_info(parser, betree_info_key_types286, betree_info_value_types287, config_dict288)
    return _t889
end

function parse_betree_info_key_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs289 = Proto.var"#Type"[]
    cond290 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond290
        _t890 = parse_type(parser)
        item291 = _t890
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
        _t891 = parse_type(parser)
        item295 = _t891
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
    _t892 = parse_csvlocator(parser)
    csvlocator297 = _t892
    _t893 = parse_csv_config(parser)
    csv_config298 = _t893
    _t894 = parse_csv_columns(parser)
    csv_columns299 = _t894
    _t895 = parse_csv_asof(parser)
    csv_asof300 = _t895
    consume_literal!(parser, ")")
    _t896 = Proto.CSVData(locator=csvlocator297, config=csv_config298, columns=csv_columns299, asof=csv_asof300)
    return _t896
end

function parse_csvlocator(parser::Parser)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t898 = parse_csv_locator_paths(parser)
        _t897 = _t898
    else
        _t897 = nothing
    end
    csv_locator_paths301 = _t897
    
    if match_lookahead_literal(parser, "(", 0)
        _t900 = parse_csv_locator_inline_data(parser)
        _t899 = _t900
    else
        _t899 = nothing
    end
    csv_locator_inline_data302 = _t899
    consume_literal!(parser, ")")
    _t901 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths301) ? csv_locator_paths301 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data302) ? csv_locator_inline_data302 : "")))
    return _t901
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
    _t902 = parse_config_dict(parser)
    config_dict308 = _t902
    consume_literal!(parser, ")")
    _t903 = construct_csv_config(parser, config_dict308)
    return _t903
end

function parse_csv_columns(parser::Parser)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs309 = Proto.CSVColumn[]
    cond310 = match_lookahead_literal(parser, "(", 0)
    while cond310
        _t904 = parse_csv_column(parser)
        item311 = _t904
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
    _t905 = parse_relation_id(parser)
    relation_id314 = _t905
    consume_literal!(parser, "[")
    xs315 = Proto.var"#Type"[]
    cond316 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond316
        _t906 = parse_type(parser)
        item317 = _t906
        push!(xs315, item317)
        cond316 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types318 = xs315
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t907 = Proto.CSVColumn(column_name=string313, target_id=relation_id314, types=types318)
    return _t907
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
    _t908 = parse_fragment_id(parser)
    fragment_id320 = _t908
    consume_literal!(parser, ")")
    _t909 = Proto.Undefine(fragment_id=fragment_id320)
    return _t909
end

function parse_context(parser::Parser)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs321 = Proto.RelationId[]
    cond322 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond322
        _t910 = parse_relation_id(parser)
        item323 = _t910
        push!(xs321, item323)
        cond322 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids324 = xs321
    consume_literal!(parser, ")")
    _t911 = Proto.Context(relations=relation_ids324)
    return _t911
end

function parse_epoch_reads(parser::Parser)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs325 = Proto.Read[]
    cond326 = match_lookahead_literal(parser, "(", 0)
    while cond326
        _t912 = parse_read(parser)
        item327 = _t912
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
            _t914 = 2
        else
            
            if match_lookahead_literal(parser, "output", 1)
                _t915 = 1
            else
                
                if match_lookahead_literal(parser, "export", 1)
                    _t916 = 4
                else
                    
                    if match_lookahead_literal(parser, "demand", 1)
                        _t917 = 0
                    else
                        
                        if match_lookahead_literal(parser, "abort", 1)
                            _t918 = 3
                        else
                            _t918 = -1
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
    prediction329 = _t913
    
    if prediction329 == 4
        _t920 = parse_export(parser)
        export334 = _t920
        _t921 = Proto.Read(read_type=OneOf(:var"#export", export334))
        _t919 = _t921
    else
        
        if prediction329 == 3
            _t923 = parse_abort(parser)
            abort333 = _t923
            _t924 = Proto.Read(read_type=OneOf(:abort, abort333))
            _t922 = _t924
        else
            
            if prediction329 == 2
                _t926 = parse_what_if(parser)
                what_if332 = _t926
                _t927 = Proto.Read(read_type=OneOf(:what_if, what_if332))
                _t925 = _t927
            else
                
                if prediction329 == 1
                    _t929 = parse_output(parser)
                    output331 = _t929
                    _t930 = Proto.Read(read_type=OneOf(:output, output331))
                    _t928 = _t930
                else
                    
                    if prediction329 == 0
                        _t932 = parse_demand(parser)
                        demand330 = _t932
                        _t933 = Proto.Read(read_type=OneOf(:demand, demand330))
                        _t931 = _t933
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t928 = _t931
                end
                _t925 = _t928
            end
            _t922 = _t925
        end
        _t919 = _t922
    end
    return _t919
end

function parse_demand(parser::Parser)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t934 = parse_relation_id(parser)
    relation_id335 = _t934
    consume_literal!(parser, ")")
    _t935 = Proto.Demand(relation_id=relation_id335)
    return _t935
end

function parse_output(parser::Parser)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t936 = parse_name(parser)
    name336 = _t936
    _t937 = parse_relation_id(parser)
    relation_id337 = _t937
    consume_literal!(parser, ")")
    _t938 = Proto.Output(name=name336, relation_id=relation_id337)
    return _t938
end

function parse_what_if(parser::Parser)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t939 = parse_name(parser)
    name338 = _t939
    _t940 = parse_epoch(parser)
    epoch339 = _t940
    consume_literal!(parser, ")")
    _t941 = Proto.WhatIf(branch=name338, epoch=epoch339)
    return _t941
end

function parse_abort(parser::Parser)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t943 = parse_name(parser)
        _t942 = _t943
    else
        _t942 = nothing
    end
    name340 = _t942
    _t944 = parse_relation_id(parser)
    relation_id341 = _t944
    consume_literal!(parser, ")")
    _t945 = Proto.Abort(name=(!isnothing(name340) ? name340 : "abort"), relation_id=relation_id341)
    return _t945
end

function parse_export(parser::Parser)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t946 = parse_export_csv_config(parser)
    export_csv_config342 = _t946
    consume_literal!(parser, ")")
    _t947 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config342))
    return _t947
end

function parse_export_csv_config(parser::Parser)::Proto.ExportCSVConfig
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t949 = 0
        else
            
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t950 = 1
            else
                _t950 = -1
            end
            _t949 = _t950
        end
        _t948 = _t949
    else
        _t948 = -1
    end
    prediction343 = _t948
    
    if prediction343 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t952 = parse_export_csv_path(parser)
        export_csv_path347 = _t952
        _t953 = parse_export_csv_columns(parser)
        export_csv_columns348 = _t953
        _t954 = parse_config_dict(parser)
        config_dict349 = _t954
        consume_literal!(parser, ")")
        _t955 = construct_export_csv_config(parser, export_csv_path347, export_csv_columns348, config_dict349)
        _t951 = _t955
    else
        
        if prediction343 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t957 = parse_export_csv_path(parser)
            export_csv_path344 = _t957
            _t958 = parse_export_csv_source(parser)
            export_csv_source345 = _t958
            _t959 = parse_csv_config(parser)
            csv_config346 = _t959
            consume_literal!(parser, ")")
            _t960 = construct_export_csv_config_with_source(parser, export_csv_path344, export_csv_source345, csv_config346)
            _t956 = _t960
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t951 = _t956
    end
    return _t951
end

function parse_export_csv_path(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string350 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string350
end

function parse_export_csv_source(parser::Parser)::Proto.ExportCSVSource
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "table_def", 1)
            _t962 = 1
        else
            
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t963 = 0
            else
                _t963 = -1
            end
            _t962 = _t963
        end
        _t961 = _t962
    else
        _t961 = -1
    end
    prediction351 = _t961
    
    if prediction351 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t965 = parse_relation_id(parser)
        relation_id356 = _t965
        consume_literal!(parser, ")")
        _t966 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id356))
        _t964 = _t966
    else
        
        if prediction351 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs352 = Proto.ExportCSVColumn[]
            cond353 = match_lookahead_literal(parser, "(", 0)
            while cond353
                _t968 = parse_export_csv_column(parser)
                item354 = _t968
                push!(xs352, item354)
                cond353 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns355 = xs352
            consume_literal!(parser, ")")
            _t969 = Proto.ExportCSVColumns(columns=export_csv_columns355)
            _t970 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t969))
            _t967 = _t970
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t964 = _t967
    end
    return _t964
end

function parse_export_csv_column(parser::Parser)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string357 = consume_terminal!(parser, "STRING")
    _t971 = parse_relation_id(parser)
    relation_id358 = _t971
    consume_literal!(parser, ")")
    _t972 = Proto.ExportCSVColumn(column_name=string357, column_data=relation_id358)
    return _t972
end

function parse_export_csv_columns(parser::Parser)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs359 = Proto.ExportCSVColumn[]
    cond360 = match_lookahead_literal(parser, "(", 0)
    while cond360
        _t973 = parse_export_csv_column(parser)
        item361 = _t973
        push!(xs359, item361)
        cond360 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns362 = xs359
    consume_literal!(parser, ")")
    return export_csv_columns362
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
