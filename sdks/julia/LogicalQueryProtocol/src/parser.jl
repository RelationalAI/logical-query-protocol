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

function _extract_value_int32(parser::Parser, value::Union{Nothing, Proto.Value}, default::Int64)::Int32
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return Int32(_get_oneof_field(value, :int_value))
    end
    return Int32(default)
end

function _extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    end
    return default
end

function _extract_value_float64(parser::Parser, value::Union{Nothing, Proto.Value}, default::Float64)::Float64
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    end
    return default
end

function _extract_value_string(parser::Parser, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    end
    return default
end

function _extract_value_boolean(parser::Parser, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    end
    return default
end

function _extract_value_bytes(parser::Parser, value::Union{Nothing, Proto.Value}, default::Vector{UInt8})::Vector{UInt8}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    end
    return default
end

function _extract_value_uint128(parser::Parser, value::Union{Nothing, Proto.Value}, default::Proto.UInt128Value)::Proto.UInt128Value
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    end
    return default
end

function _extract_value_string_list(parser::Parser, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    end
    return default
end

function _try_extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    end
    return nothing
end

function _try_extract_value_float64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    end
    return nothing
end

function _try_extract_value_string(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    end
    return nothing
end

function _try_extract_value_bytes(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    end
    return nothing
end

function _try_extract_value_uint128(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    end
    return nothing
end

function _try_extract_value_string_list(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{String}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    end
    return nothing
end

function construct_csv_config(parser::Parser, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t955 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t955
    _t956 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t956
    _t957 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t957
    _t958 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t958
    _t959 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t959
    _t960 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t960
    _t961 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t961
    _t962 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t962
    _t963 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t963
    _t964 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t964
    _t965 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t965
    _t966 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t966
end

function construct_betree_info(parser::Parser, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t967 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t967
    _t968 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t968
    _t969 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t969
    _t970 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t970
    _t971 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t971
    _t972 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t972
    _t973 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t973
    _t974 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t974
    _t975 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t975
    _t976 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t976
    _t977 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t977
end

function default_configure(parser::Parser)::Proto.Configure
    _t978 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t978
    _t979 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t979
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
    _t980 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t980
    _t981 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t981
    _t982 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t982
end

function export_csv_config(parser::Parser, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t983 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t983
    _t984 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t984
    _t985 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t985
    _t986 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t986
    _t987 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t987
    _t988 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t988
    _t989 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t989
    _t990 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t990
end

function _make_value_int32(parser::Parser, v::Int32)::Proto.Value
    _t991 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t991
end

function _make_value_int64(parser::Parser, v::Int64)::Proto.Value
    _t992 = Proto.Value(value=OneOf(:int_value, v))
    return _t992
end

function _make_value_float64(parser::Parser, v::Float64)::Proto.Value
    _t993 = Proto.Value(value=OneOf(:float_value, v))
    return _t993
end

function _make_value_string(parser::Parser, v::String)::Proto.Value
    _t994 = Proto.Value(value=OneOf(:string_value, v))
    return _t994
end

function _make_value_boolean(parser::Parser, v::Bool)::Proto.Value
    _t995 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t995
end

function _make_value_uint128(parser::Parser, v::Proto.UInt128Value)::Proto.Value
    _t996 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t996
end

function is_default_configure(parser::Parser, cfg::Proto.Configure)::Bool
    if cfg.semantics_version != 0
        return false
    end
    if cfg.ivm_config.level != Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        return false
    end
    return true
end

function deconstruct_configure(parser::Parser, msg::Proto.Configure)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        _t997 = _make_value_string(parser, "auto")
        push!(result, ("ivm.maintenance_level", _t997,))
    else
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t998 = _make_value_string(parser, "all")
            push!(result, ("ivm.maintenance_level", _t998,))
        else
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t999 = _make_value_string(parser, "off")
                push!(result, ("ivm.maintenance_level", _t999,))
            end
        end
    end
    _t1000 = _make_value_int64(parser, msg.semantics_version)
    push!(result, ("semantics_version", _t1000,))
    return sort(result)
end

function deconstruct_csv_config(parser::Parser, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1001 = _make_value_int32(parser, msg.header_row)
    push!(result, ("csv_header_row", _t1001,))
    _t1002 = _make_value_int64(parser, msg.skip)
    push!(result, ("csv_skip", _t1002,))
    if msg.new_line != ""
        _t1003 = _make_value_string(parser, msg.new_line)
        push!(result, ("csv_new_line", _t1003,))
    end
    _t1004 = _make_value_string(parser, msg.delimiter)
    push!(result, ("csv_delimiter", _t1004,))
    _t1005 = _make_value_string(parser, msg.quotechar)
    push!(result, ("csv_quotechar", _t1005,))
    _t1006 = _make_value_string(parser, msg.escapechar)
    push!(result, ("csv_escapechar", _t1006,))
    if msg.comment != ""
        _t1007 = _make_value_string(parser, msg.comment)
        push!(result, ("csv_comment", _t1007,))
    end
    for missing_string in msg.missing_strings
        _t1008 = _make_value_string(parser, missing_string)
        push!(result, ("csv_missing_strings", _t1008,))
    end
    _t1009 = _make_value_string(parser, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1009,))
    _t1010 = _make_value_string(parser, msg.encoding)
    push!(result, ("csv_encoding", _t1010,))
    _t1011 = _make_value_string(parser, msg.compression)
    push!(result, ("csv_compression", _t1011,))
    return sort(result)
end

function deconstruct_betree_info_config(parser::Parser, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1012 = _make_value_float64(parser, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1012,))
    _t1013 = _make_value_int64(parser, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1013,))
    _t1014 = _make_value_int64(parser, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1014,))
    _t1015 = _make_value_int64(parser, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1015,))
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :root_pageid))
            _t1016 = _make_value_uint128(parser, _get_oneof_field(msg.relation_locator, :root_pageid))
            push!(result, ("betree_locator_root_pageid", _t1016,))
        end
    end
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        if !isnothing(_get_oneof_field(msg.relation_locator, :inline_data))
            _t1017 = _make_value_string(parser, String(_get_oneof_field(msg.relation_locator, :inline_data)))
            push!(result, ("betree_locator_inline_data", _t1017,))
        end
    end
    _t1018 = _make_value_int64(parser, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1018,))
    _t1019 = _make_value_int64(parser, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1019,))
    return sort(result)
end

function deconstruct_export_csv_config(parser::Parser, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    if !isnothing(msg.partition_size)
        _t1020 = _make_value_int64(parser, msg.partition_size)
        push!(result, ("partition_size", _t1020,))
    end
    if !isnothing(msg.compression)
        _t1021 = _make_value_string(parser, msg.compression)
        push!(result, ("compression", _t1021,))
    end
    if !isnothing(msg.syntax_header_row)
        _t1022 = _make_value_boolean(parser, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1022,))
    end
    if !isnothing(msg.syntax_missing_string)
        _t1023 = _make_value_string(parser, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1023,))
    end
    if !isnothing(msg.syntax_delim)
        _t1024 = _make_value_string(parser, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1024,))
    end
    if !isnothing(msg.syntax_quotechar)
        _t1025 = _make_value_string(parser, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1025,))
    end
    if !isnothing(msg.syntax_escapechar)
        _t1026 = _make_value_string(parser, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1026,))
    end
    return sort(result)
end

function deconstruct_relation_id_string(parser::Parser, msg::Proto.RelationId)::Union{Nothing, String}
    name = relation_id_to_string(pp, msg)
    if name != ""
        return name
    end
    return nothing
end

function deconstruct_relation_id_uint128(parser::Parser, msg::Proto.RelationId)::Union{Nothing, Proto.UInt128Value}
    name = relation_id_to_string(pp, msg)
    if name == ""
        return relation_id_to_uint128(pp, msg)
    end
    return nothing
end

function deconstruct_bindings(parser::Parser, abs::Proto.Abstraction)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    n = length(abs.vars)
    return (abs.vars[0:n], Proto.Binding[],)
end

function deconstruct_bindings_with_arity(parser::Parser, abs::Proto.Abstraction, value_arity::Int64)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    n = length(abs.vars)
    key_end = (n - value_arity)
    return (abs.vars[0:key_end], abs.vars[key_end:n],)
end

# --- Parse functions ---

function parse_transaction(parser::Parser)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t357 = parse_configure(parser)
        _t356 = _t357
    else
        _t356 = nothing
    end
    configure0 = _t356
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t359 = parse_sync(parser)
        _t358 = _t359
    else
        _t358 = nothing
    end
    sync1 = _t358
    xs2 = Proto.Epoch[]
    cond3 = match_lookahead_literal(parser, "(", 0)
    while cond3
        _t360 = parse_epoch(parser)
        item4 = _t360
        push!(xs2, item4)
        cond3 = match_lookahead_literal(parser, "(", 0)
    end
    epochs5 = xs2
    consume_literal!(parser, ")")
    _t361 = default_configure(parser)
    _t362 = Proto.Transaction(epochs=epochs5, configure=(!isnothing(configure0) ? configure0 : _t361), sync=sync1)
    return _t362
end

function parse_configure(parser::Parser)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t363 = parse_config_dict(parser)
    config_dict6 = _t363
    consume_literal!(parser, ")")
    _t364 = construct_configure(parser, config_dict6)
    return _t364
end

function parse_config_dict(parser::Parser)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs7 = Tuple{String, Proto.Value}[]
    cond8 = match_lookahead_literal(parser, ":", 0)
    while cond8
        _t365 = parse_config_key_value(parser)
        item9 = _t365
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
    _t366 = parse_value(parser)
    value12 = _t366
    return (symbol11, value12,)
end

function parse_value(parser::Parser)::Proto.Value
    
    if match_lookahead_literal(parser, "true", 0)
        _t367 = 9
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t368 = 8
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t369 = 9
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t371 = 1
                    else
                        
                        if match_lookahead_literal(parser, "date", 1)
                            _t372 = 0
                        else
                            _t372 = -1
                        end
                        _t371 = _t372
                    end
                    _t370 = _t371
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t373 = 5
                    else
                        
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t374 = 2
                        else
                            
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t375 = 6
                            else
                                
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t376 = 3
                                else
                                    
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t377 = 4
                                    else
                                        
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t378 = 7
                                        else
                                            _t378 = -1
                                        end
                                        _t377 = _t378
                                    end
                                    _t376 = _t377
                                end
                                _t375 = _t376
                            end
                            _t374 = _t375
                        end
                        _t373 = _t374
                    end
                    _t370 = _t373
                end
                _t369 = _t370
            end
            _t368 = _t369
        end
        _t367 = _t368
    end
    prediction13 = _t367
    
    if prediction13 == 9
        _t380 = parse_boolean_value(parser)
        boolean_value22 = _t380
        _t381 = Proto.Value(value=OneOf(:boolean_value, boolean_value22))
        _t379 = _t381
    else
        
        if prediction13 == 8
            consume_literal!(parser, "missing")
            _t383 = Proto.MissingValue()
            _t384 = Proto.Value(value=OneOf(:missing_value, _t383))
            _t382 = _t384
        else
            
            if prediction13 == 7
                decimal21 = consume_terminal!(parser, "DECIMAL")
                _t386 = Proto.Value(value=OneOf(:decimal_value, decimal21))
                _t385 = _t386
            else
                
                if prediction13 == 6
                    int12820 = consume_terminal!(parser, "INT128")
                    _t388 = Proto.Value(value=OneOf(:int128_value, int12820))
                    _t387 = _t388
                else
                    
                    if prediction13 == 5
                        uint12819 = consume_terminal!(parser, "UINT128")
                        _t390 = Proto.Value(value=OneOf(:uint128_value, uint12819))
                        _t389 = _t390
                    else
                        
                        if prediction13 == 4
                            float18 = consume_terminal!(parser, "FLOAT")
                            _t392 = Proto.Value(value=OneOf(:float_value, float18))
                            _t391 = _t392
                        else
                            
                            if prediction13 == 3
                                int17 = consume_terminal!(parser, "INT")
                                _t394 = Proto.Value(value=OneOf(:int_value, int17))
                                _t393 = _t394
                            else
                                
                                if prediction13 == 2
                                    string16 = consume_terminal!(parser, "STRING")
                                    _t396 = Proto.Value(value=OneOf(:string_value, string16))
                                    _t395 = _t396
                                else
                                    
                                    if prediction13 == 1
                                        _t398 = parse_datetime(parser)
                                        datetime15 = _t398
                                        _t399 = Proto.Value(value=OneOf(:datetime_value, datetime15))
                                        _t397 = _t399
                                    else
                                        
                                        if prediction13 == 0
                                            _t401 = parse_date(parser)
                                            date14 = _t401
                                            _t402 = Proto.Value(value=OneOf(:date_value, date14))
                                            _t400 = _t402
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t397 = _t400
                                    end
                                    _t395 = _t397
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
            _t382 = _t385
        end
        _t379 = _t382
    end
    return _t379
end

function parse_date(parser::Parser)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int23 = consume_terminal!(parser, "INT")
    int_324 = consume_terminal!(parser, "INT")
    int_425 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t403 = Proto.DateValue(year=Int32(int23), month=Int32(int_324), day=Int32(int_425))
    return _t403
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
        _t404 = consume_terminal!(parser, "INT")
    else
        _t404 = nothing
    end
    int_832 = _t404
    consume_literal!(parser, ")")
    _t405 = Proto.DateTimeValue(year=Int32(int26), month=Int32(int_327), day=Int32(int_428), hour=Int32(int_529), minute=Int32(int_630), second=Int32(int_731), microsecond=Int32((!isnothing(int_832) ? int_832 : 0)))
    return _t405
end

function parse_boolean_value(parser::Parser)::Bool
    
    if match_lookahead_literal(parser, "true", 0)
        _t406 = 0
    else
        
        if match_lookahead_literal(parser, "false", 0)
            _t407 = 1
        else
            _t407 = -1
        end
        _t406 = _t407
    end
    prediction33 = _t406
    
    if prediction33 == 1
        consume_literal!(parser, "false")
        _t408 = false
    else
        
        if prediction33 == 0
            consume_literal!(parser, "true")
            _t409 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t408 = _t409
    end
    return _t408
end

function parse_sync(parser::Parser)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs34 = Proto.FragmentId[]
    cond35 = match_lookahead_literal(parser, ":", 0)
    while cond35
        _t410 = parse_fragment_id(parser)
        item36 = _t410
        push!(xs34, item36)
        cond35 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids37 = xs34
    consume_literal!(parser, ")")
    _t411 = Proto.Sync(fragments=fragment_ids37)
    return _t411
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
        _t413 = parse_epoch_writes(parser)
        _t412 = _t413
    else
        _t412 = nothing
    end
    epoch_writes39 = _t412
    
    if match_lookahead_literal(parser, "(", 0)
        _t415 = parse_epoch_reads(parser)
        _t414 = _t415
    else
        _t414 = nothing
    end
    epoch_reads40 = _t414
    consume_literal!(parser, ")")
    _t416 = Proto.Epoch(writes=(!isnothing(epoch_writes39) ? epoch_writes39 : Proto.Write[]), reads=(!isnothing(epoch_reads40) ? epoch_reads40 : Proto.Read[]))
    return _t416
end

function parse_epoch_writes(parser::Parser)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs41 = Proto.Write[]
    cond42 = match_lookahead_literal(parser, "(", 0)
    while cond42
        _t417 = parse_write(parser)
        item43 = _t417
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
            _t419 = 1
        else
            
            if match_lookahead_literal(parser, "snapshot", 1)
                _t420 = 3
            else
                
                if match_lookahead_literal(parser, "define", 1)
                    _t421 = 0
                else
                    
                    if match_lookahead_literal(parser, "context", 1)
                        _t422 = 2
                    else
                        _t422 = -1
                    end
                    _t421 = _t422
                end
                _t420 = _t421
            end
            _t419 = _t420
        end
        _t418 = _t419
    else
        _t418 = -1
    end
    prediction45 = _t418
    
    if prediction45 == 3
        _t424 = parse_snapshot(parser)
        snapshot49 = _t424
        _t425 = Proto.Write(write_type=OneOf(:snapshot, snapshot49))
        _t423 = _t425
    else
        
        if prediction45 == 2
            _t427 = parse_context(parser)
            context48 = _t427
            _t428 = Proto.Write(write_type=OneOf(:context, context48))
            _t426 = _t428
        else
            
            if prediction45 == 1
                _t430 = parse_undefine(parser)
                undefine47 = _t430
                _t431 = Proto.Write(write_type=OneOf(:undefine, undefine47))
                _t429 = _t431
            else
                
                if prediction45 == 0
                    _t433 = parse_define(parser)
                    define46 = _t433
                    _t434 = Proto.Write(write_type=OneOf(:define, define46))
                    _t432 = _t434
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t429 = _t432
            end
            _t426 = _t429
        end
        _t423 = _t426
    end
    return _t423
end

function parse_define(parser::Parser)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t435 = parse_fragment(parser)
    fragment50 = _t435
    consume_literal!(parser, ")")
    _t436 = Proto.Define(fragment=fragment50)
    return _t436
end

function parse_fragment(parser::Parser)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t437 = parse_new_fragment_id(parser)
    new_fragment_id51 = _t437
    xs52 = Proto.Declaration[]
    cond53 = match_lookahead_literal(parser, "(", 0)
    while cond53
        _t438 = parse_declaration(parser)
        item54 = _t438
        push!(xs52, item54)
        cond53 = match_lookahead_literal(parser, "(", 0)
    end
    declarations55 = xs52
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id51, declarations55)
end

function parse_new_fragment_id(parser::Parser)::Proto.FragmentId
    _t439 = parse_fragment_id(parser)
    fragment_id56 = _t439
    start_fragment!(parser, fragment_id56)
    return fragment_id56
end

function parse_declaration(parser::Parser)::Proto.Declaration
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t441 = 3
        else
            
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t442 = 2
            else
                
                if match_lookahead_literal(parser, "def", 1)
                    _t443 = 0
                else
                    
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t444 = 3
                    else
                        
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t445 = 3
                        else
                            
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t446 = 1
                            else
                                _t446 = -1
                            end
                            _t445 = _t446
                        end
                        _t444 = _t445
                    end
                    _t443 = _t444
                end
                _t442 = _t443
            end
            _t441 = _t442
        end
        _t440 = _t441
    else
        _t440 = -1
    end
    prediction57 = _t440
    
    if prediction57 == 3
        _t448 = parse_data(parser)
        data61 = _t448
        _t449 = Proto.Declaration(declaration_type=OneOf(:data, data61))
        _t447 = _t449
    else
        
        if prediction57 == 2
            _t451 = parse_constraint(parser)
            constraint60 = _t451
            _t452 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint60))
            _t450 = _t452
        else
            
            if prediction57 == 1
                _t454 = parse_algorithm(parser)
                algorithm59 = _t454
                _t455 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm59))
                _t453 = _t455
            else
                
                if prediction57 == 0
                    _t457 = parse_def(parser)
                    def58 = _t457
                    _t458 = Proto.Declaration(declaration_type=OneOf(:def, def58))
                    _t456 = _t458
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t453 = _t456
            end
            _t450 = _t453
        end
        _t447 = _t450
    end
    return _t447
end

function parse_def(parser::Parser)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t459 = parse_relation_id(parser)
    relation_id62 = _t459
    _t460 = parse_abstraction(parser)
    abstraction63 = _t460
    
    if match_lookahead_literal(parser, "(", 0)
        _t462 = parse_attrs(parser)
        _t461 = _t462
    else
        _t461 = nothing
    end
    attrs64 = _t461
    consume_literal!(parser, ")")
    _t463 = Proto.Def(name=relation_id62, body=abstraction63, attrs=(!isnothing(attrs64) ? attrs64 : Proto.Attribute[]))
    return _t463
end

function parse_relation_id(parser::Parser)::Proto.RelationId
    
    if match_lookahead_literal(parser, ":", 0)
        _t464 = 0
    else
        
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t465 = 1
        else
            _t465 = -1
        end
        _t464 = _t465
    end
    prediction65 = _t464
    
    if prediction65 == 1
        uint12867 = consume_terminal!(parser, "UINT128")
        _t466 = Proto.RelationId(uint12867.low, uint12867.high)
    else
        
        if prediction65 == 0
            consume_literal!(parser, ":")
            symbol66 = consume_terminal!(parser, "SYMBOL")
            _t467 = relation_id_from_string(parser, symbol66)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t466 = _t467
    end
    return _t466
end

function parse_abstraction(parser::Parser)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t468 = parse_bindings(parser)
    bindings68 = _t468
    _t469 = parse_formula(parser)
    formula69 = _t469
    consume_literal!(parser, ")")
    _t470 = Proto.Abstraction(vars=vcat(bindings68[1], !isnothing(bindings68[2]) ? bindings68[2] : []), value=formula69)
    return _t470
end

function parse_bindings(parser::Parser)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs70 = Proto.Binding[]
    cond71 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond71
        _t471 = parse_binding(parser)
        item72 = _t471
        push!(xs70, item72)
        cond71 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings73 = xs70
    
    if match_lookahead_literal(parser, "|", 0)
        _t473 = parse_value_bindings(parser)
        _t472 = _t473
    else
        _t472 = nothing
    end
    value_bindings74 = _t472
    consume_literal!(parser, "]")
    return (bindings73, (!isnothing(value_bindings74) ? value_bindings74 : Proto.Binding[]),)
end

function parse_binding(parser::Parser)::Proto.Binding
    symbol75 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t474 = parse_type(parser)
    type76 = _t474
    _t475 = Proto.Var(name=symbol75)
    _t476 = Proto.Binding(var=_t475, var"#type"=type76)
    return _t476
end

function parse_type(parser::Parser)::Proto.var"#Type"
    
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t477 = 0
    else
        
        if match_lookahead_literal(parser, "UINT128", 0)
            _t478 = 4
        else
            
            if match_lookahead_literal(parser, "STRING", 0)
                _t479 = 1
            else
                
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t480 = 8
                else
                    
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t481 = 5
                    else
                        
                        if match_lookahead_literal(parser, "INT", 0)
                            _t482 = 2
                        else
                            
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t483 = 3
                            else
                                
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t484 = 7
                                else
                                    
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t485 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t486 = 10
                                        else
                                            
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t487 = 9
                                            else
                                                _t487 = -1
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
            _t478 = _t479
        end
        _t477 = _t478
    end
    prediction77 = _t477
    
    if prediction77 == 10
        _t489 = parse_boolean_type(parser)
        boolean_type88 = _t489
        _t490 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type88))
        _t488 = _t490
    else
        
        if prediction77 == 9
            _t492 = parse_decimal_type(parser)
            decimal_type87 = _t492
            _t493 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type87))
            _t491 = _t493
        else
            
            if prediction77 == 8
                _t495 = parse_missing_type(parser)
                missing_type86 = _t495
                _t496 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type86))
                _t494 = _t496
            else
                
                if prediction77 == 7
                    _t498 = parse_datetime_type(parser)
                    datetime_type85 = _t498
                    _t499 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type85))
                    _t497 = _t499
                else
                    
                    if prediction77 == 6
                        _t501 = parse_date_type(parser)
                        date_type84 = _t501
                        _t502 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type84))
                        _t500 = _t502
                    else
                        
                        if prediction77 == 5
                            _t504 = parse_int128_type(parser)
                            int128_type83 = _t504
                            _t505 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type83))
                            _t503 = _t505
                        else
                            
                            if prediction77 == 4
                                _t507 = parse_uint128_type(parser)
                                uint128_type82 = _t507
                                _t508 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type82))
                                _t506 = _t508
                            else
                                
                                if prediction77 == 3
                                    _t510 = parse_float_type(parser)
                                    float_type81 = _t510
                                    _t511 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type81))
                                    _t509 = _t511
                                else
                                    
                                    if prediction77 == 2
                                        _t513 = parse_int_type(parser)
                                        int_type80 = _t513
                                        _t514 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type80))
                                        _t512 = _t514
                                    else
                                        
                                        if prediction77 == 1
                                            _t516 = parse_string_type(parser)
                                            string_type79 = _t516
                                            _t517 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type79))
                                            _t515 = _t517
                                        else
                                            
                                            if prediction77 == 0
                                                _t519 = parse_unspecified_type(parser)
                                                unspecified_type78 = _t519
                                                _t520 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type78))
                                                _t518 = _t520
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
        _t488 = _t491
    end
    return _t488
end

function parse_unspecified_type(parser::Parser)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t521 = Proto.UnspecifiedType()
    return _t521
end

function parse_string_type(parser::Parser)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t522 = Proto.StringType()
    return _t522
end

function parse_int_type(parser::Parser)::Proto.IntType
    consume_literal!(parser, "INT")
    _t523 = Proto.IntType()
    return _t523
end

function parse_float_type(parser::Parser)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t524 = Proto.FloatType()
    return _t524
end

function parse_uint128_type(parser::Parser)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t525 = Proto.UInt128Type()
    return _t525
end

function parse_int128_type(parser::Parser)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t526 = Proto.Int128Type()
    return _t526
end

function parse_date_type(parser::Parser)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t527 = Proto.DateType()
    return _t527
end

function parse_datetime_type(parser::Parser)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t528 = Proto.DateTimeType()
    return _t528
end

function parse_missing_type(parser::Parser)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t529 = Proto.MissingType()
    return _t529
end

function parse_decimal_type(parser::Parser)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int89 = consume_terminal!(parser, "INT")
    int_390 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t530 = Proto.DecimalType(precision=Int32(int89), scale=Int32(int_390))
    return _t530
end

function parse_boolean_type(parser::Parser)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t531 = Proto.BooleanType()
    return _t531
end

function parse_value_bindings(parser::Parser)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs91 = Proto.Binding[]
    cond92 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond92
        _t532 = parse_binding(parser)
        item93 = _t532
        push!(xs91, item93)
        cond92 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings94 = xs91
    return bindings94
end

function parse_formula(parser::Parser)::Proto.Formula
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "true", 1)
            _t534 = 0
        else
            
            if match_lookahead_literal(parser, "relatom", 1)
                _t535 = 11
            else
                
                if match_lookahead_literal(parser, "reduce", 1)
                    _t536 = 3
                else
                    
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t537 = 10
                    else
                        
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t538 = 9
                        else
                            
                            if match_lookahead_literal(parser, "or", 1)
                                _t539 = 5
                            else
                                
                                if match_lookahead_literal(parser, "not", 1)
                                    _t540 = 6
                                else
                                    
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t541 = 7
                                    else
                                        
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t542 = 1
                                        else
                                            
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t543 = 2
                                            else
                                                
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t544 = 12
                                                else
                                                    
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t545 = 8
                                                    else
                                                        
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t546 = 4
                                                        else
                                                            
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t547 = 10
                                                            else
                                                                
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t548 = 10
                                                                else
                                                                    
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t549 = 10
                                                                    else
                                                                        
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t550 = 10
                                                                        else
                                                                            
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t551 = 10
                                                                            else
                                                                                
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t552 = 10
                                                                                else
                                                                                    
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t553 = 10
                                                                                    else
                                                                                        
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t554 = 10
                                                                                        else
                                                                                            
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t555 = 10
                                                                                            else
                                                                                                _t555 = -1
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
            end
            _t534 = _t535
        end
        _t533 = _t534
    else
        _t533 = -1
    end
    prediction95 = _t533
    
    if prediction95 == 12
        _t557 = parse_cast(parser)
        cast108 = _t557
        _t558 = Proto.Formula(formula_type=OneOf(:cast, cast108))
        _t556 = _t558
    else
        
        if prediction95 == 11
            _t560 = parse_rel_atom(parser)
            rel_atom107 = _t560
            _t561 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom107))
            _t559 = _t561
        else
            
            if prediction95 == 10
                _t563 = parse_primitive(parser)
                primitive106 = _t563
                _t564 = Proto.Formula(formula_type=OneOf(:primitive, primitive106))
                _t562 = _t564
            else
                
                if prediction95 == 9
                    _t566 = parse_pragma(parser)
                    pragma105 = _t566
                    _t567 = Proto.Formula(formula_type=OneOf(:pragma, pragma105))
                    _t565 = _t567
                else
                    
                    if prediction95 == 8
                        _t569 = parse_atom(parser)
                        atom104 = _t569
                        _t570 = Proto.Formula(formula_type=OneOf(:atom, atom104))
                        _t568 = _t570
                    else
                        
                        if prediction95 == 7
                            _t572 = parse_ffi(parser)
                            ffi103 = _t572
                            _t573 = Proto.Formula(formula_type=OneOf(:ffi, ffi103))
                            _t571 = _t573
                        else
                            
                            if prediction95 == 6
                                _t575 = parse_not(parser)
                                not102 = _t575
                                _t576 = Proto.Formula(formula_type=OneOf(:not, not102))
                                _t574 = _t576
                            else
                                
                                if prediction95 == 5
                                    _t578 = parse_disjunction(parser)
                                    disjunction101 = _t578
                                    _t579 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction101))
                                    _t577 = _t579
                                else
                                    
                                    if prediction95 == 4
                                        _t581 = parse_conjunction(parser)
                                        conjunction100 = _t581
                                        _t582 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction100))
                                        _t580 = _t582
                                    else
                                        
                                        if prediction95 == 3
                                            _t584 = parse_reduce(parser)
                                            reduce99 = _t584
                                            _t585 = Proto.Formula(formula_type=OneOf(:reduce, reduce99))
                                            _t583 = _t585
                                        else
                                            
                                            if prediction95 == 2
                                                _t587 = parse_exists(parser)
                                                exists98 = _t587
                                                _t588 = Proto.Formula(formula_type=OneOf(:exists, exists98))
                                                _t586 = _t588
                                            else
                                                
                                                if prediction95 == 1
                                                    _t590 = parse_false(parser)
                                                    false97 = _t590
                                                    _t591 = Proto.Formula(formula_type=OneOf(:disjunction, false97))
                                                    _t589 = _t591
                                                else
                                                    
                                                    if prediction95 == 0
                                                        _t593 = parse_true(parser)
                                                        true96 = _t593
                                                        _t594 = Proto.Formula(formula_type=OneOf(:conjunction, true96))
                                                        _t592 = _t594
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
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
        _t556 = _t559
    end
    return _t556
end

function parse_true(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t595 = Proto.Conjunction(args=Proto.Formula[])
    return _t595
end

function parse_false(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t596 = Proto.Disjunction(args=Proto.Formula[])
    return _t596
end

function parse_exists(parser::Parser)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t597 = parse_bindings(parser)
    bindings109 = _t597
    _t598 = parse_formula(parser)
    formula110 = _t598
    consume_literal!(parser, ")")
    _t599 = Proto.Abstraction(vars=vcat(bindings109[1], !isnothing(bindings109[2]) ? bindings109[2] : []), value=formula110)
    _t600 = Proto.Exists(body=_t599)
    return _t600
end

function parse_reduce(parser::Parser)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t601 = parse_abstraction(parser)
    abstraction111 = _t601
    _t602 = parse_abstraction(parser)
    abstraction_3112 = _t602
    _t603 = parse_terms(parser)
    terms113 = _t603
    consume_literal!(parser, ")")
    _t604 = Proto.Reduce(op=abstraction111, body=abstraction_3112, terms=terms113)
    return _t604
end

function parse_terms(parser::Parser)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs114 = Proto.Term[]
    cond115 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond115
        _t605 = parse_term(parser)
        item116 = _t605
        push!(xs114, item116)
        cond115 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms117 = xs114
    consume_literal!(parser, ")")
    return terms117
end

function parse_term(parser::Parser)::Proto.Term
    
    if match_lookahead_literal(parser, "true", 0)
        _t606 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t607 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t608 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t609 = 1
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t610 = 1
                    else
                        
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t611 = 0
                        else
                            
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t612 = 1
                            else
                                
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t613 = 1
                                else
                                    
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t614 = 1
                                    else
                                        
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t615 = 1
                                        else
                                            
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t616 = 1
                                            else
                                                _t616 = -1
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
            _t607 = _t608
        end
        _t606 = _t607
    end
    prediction118 = _t606
    
    if prediction118 == 1
        _t618 = parse_constant(parser)
        constant120 = _t618
        _t619 = Proto.Term(term_type=OneOf(:constant, constant120))
        _t617 = _t619
    else
        
        if prediction118 == 0
            _t621 = parse_var(parser)
            var119 = _t621
            _t622 = Proto.Term(term_type=OneOf(:var, var119))
            _t620 = _t622
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t617 = _t620
    end
    return _t617
end

function parse_var(parser::Parser)::Proto.Var
    symbol121 = consume_terminal!(parser, "SYMBOL")
    _t623 = Proto.Var(name=symbol121)
    return _t623
end

function parse_constant(parser::Parser)::Proto.Value
    _t624 = parse_value(parser)
    value122 = _t624
    return value122
end

function parse_conjunction(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs123 = Proto.Formula[]
    cond124 = match_lookahead_literal(parser, "(", 0)
    while cond124
        _t625 = parse_formula(parser)
        item125 = _t625
        push!(xs123, item125)
        cond124 = match_lookahead_literal(parser, "(", 0)
    end
    formulas126 = xs123
    consume_literal!(parser, ")")
    _t626 = Proto.Conjunction(args=formulas126)
    return _t626
end

function parse_disjunction(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs127 = Proto.Formula[]
    cond128 = match_lookahead_literal(parser, "(", 0)
    while cond128
        _t627 = parse_formula(parser)
        item129 = _t627
        push!(xs127, item129)
        cond128 = match_lookahead_literal(parser, "(", 0)
    end
    formulas130 = xs127
    consume_literal!(parser, ")")
    _t628 = Proto.Disjunction(args=formulas130)
    return _t628
end

function parse_not(parser::Parser)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t629 = parse_formula(parser)
    formula131 = _t629
    consume_literal!(parser, ")")
    _t630 = Proto.Not(arg=formula131)
    return _t630
end

function parse_ffi(parser::Parser)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t631 = parse_name(parser)
    name132 = _t631
    _t632 = parse_ffi_args(parser)
    ffi_args133 = _t632
    _t633 = parse_terms(parser)
    terms134 = _t633
    consume_literal!(parser, ")")
    _t634 = Proto.FFI(name=name132, args=ffi_args133, terms=terms134)
    return _t634
end

function parse_name(parser::Parser)::String
    consume_literal!(parser, ":")
    symbol135 = consume_terminal!(parser, "SYMBOL")
    return symbol135
end

function parse_ffi_args(parser::Parser)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs136 = Proto.Abstraction[]
    cond137 = match_lookahead_literal(parser, "(", 0)
    while cond137
        _t635 = parse_abstraction(parser)
        item138 = _t635
        push!(xs136, item138)
        cond137 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions139 = xs136
    consume_literal!(parser, ")")
    return abstractions139
end

function parse_atom(parser::Parser)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t636 = parse_relation_id(parser)
    relation_id140 = _t636
    xs141 = Proto.Term[]
    cond142 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond142
        _t637 = parse_term(parser)
        item143 = _t637
        push!(xs141, item143)
        cond142 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms144 = xs141
    consume_literal!(parser, ")")
    _t638 = Proto.Atom(name=relation_id140, terms=terms144)
    return _t638
end

function parse_pragma(parser::Parser)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t639 = parse_name(parser)
    name145 = _t639
    xs146 = Proto.Term[]
    cond147 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond147
        _t640 = parse_term(parser)
        item148 = _t640
        push!(xs146, item148)
        cond147 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms149 = xs146
    consume_literal!(parser, ")")
    _t641 = Proto.Pragma(name=name145, terms=terms149)
    return _t641
end

function parse_primitive(parser::Parser)::Proto.Primitive
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "primitive", 1)
            _t643 = 9
        else
            
            if match_lookahead_literal(parser, ">=", 1)
                _t644 = 4
            else
                
                if match_lookahead_literal(parser, ">", 1)
                    _t645 = 3
                else
                    
                    if match_lookahead_literal(parser, "=", 1)
                        _t646 = 0
                    else
                        
                        if match_lookahead_literal(parser, "<=", 1)
                            _t647 = 2
                        else
                            
                            if match_lookahead_literal(parser, "<", 1)
                                _t648 = 1
                            else
                                
                                if match_lookahead_literal(parser, "/", 1)
                                    _t649 = 8
                                else
                                    
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t650 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t651 = 5
                                        else
                                            
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t652 = 7
                                            else
                                                _t652 = -1
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
            end
            _t643 = _t644
        end
        _t642 = _t643
    else
        _t642 = -1
    end
    prediction150 = _t642
    
    if prediction150 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t654 = parse_name(parser)
        name160 = _t654
        xs161 = Proto.RelTerm[]
        cond162 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond162
            _t655 = parse_rel_term(parser)
            item163 = _t655
            push!(xs161, item163)
            cond162 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms164 = xs161
        consume_literal!(parser, ")")
        _t656 = Proto.Primitive(name=name160, terms=rel_terms164)
        _t653 = _t656
    else
        
        if prediction150 == 8
            _t658 = parse_divide(parser)
            divide159 = _t658
            _t657 = divide159
        else
            
            if prediction150 == 7
                _t660 = parse_multiply(parser)
                multiply158 = _t660
                _t659 = multiply158
            else
                
                if prediction150 == 6
                    _t662 = parse_minus(parser)
                    minus157 = _t662
                    _t661 = minus157
                else
                    
                    if prediction150 == 5
                        _t664 = parse_add(parser)
                        add156 = _t664
                        _t663 = add156
                    else
                        
                        if prediction150 == 4
                            _t666 = parse_gt_eq(parser)
                            gt_eq155 = _t666
                            _t665 = gt_eq155
                        else
                            
                            if prediction150 == 3
                                _t668 = parse_gt(parser)
                                gt154 = _t668
                                _t667 = gt154
                            else
                                
                                if prediction150 == 2
                                    _t670 = parse_lt_eq(parser)
                                    lt_eq153 = _t670
                                    _t669 = lt_eq153
                                else
                                    
                                    if prediction150 == 1
                                        _t672 = parse_lt(parser)
                                        lt152 = _t672
                                        _t671 = lt152
                                    else
                                        
                                        if prediction150 == 0
                                            _t674 = parse_eq(parser)
                                            eq151 = _t674
                                            _t673 = eq151
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
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
            _t657 = _t659
        end
        _t653 = _t657
    end
    return _t653
end

function parse_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t675 = parse_term(parser)
    term165 = _t675
    _t676 = parse_term(parser)
    term_3166 = _t676
    consume_literal!(parser, ")")
    _t677 = Proto.RelTerm(rel_term_type=OneOf(:term, term165))
    _t678 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3166))
    _t679 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t677, _t678])
    return _t679
end

function parse_lt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t680 = parse_term(parser)
    term167 = _t680
    _t681 = parse_term(parser)
    term_3168 = _t681
    consume_literal!(parser, ")")
    _t682 = Proto.RelTerm(rel_term_type=OneOf(:term, term167))
    _t683 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3168))
    _t684 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t682, _t683])
    return _t684
end

function parse_lt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t685 = parse_term(parser)
    term169 = _t685
    _t686 = parse_term(parser)
    term_3170 = _t686
    consume_literal!(parser, ")")
    _t687 = Proto.RelTerm(rel_term_type=OneOf(:term, term169))
    _t688 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3170))
    _t689 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t687, _t688])
    return _t689
end

function parse_gt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t690 = parse_term(parser)
    term171 = _t690
    _t691 = parse_term(parser)
    term_3172 = _t691
    consume_literal!(parser, ")")
    _t692 = Proto.RelTerm(rel_term_type=OneOf(:term, term171))
    _t693 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3172))
    _t694 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t692, _t693])
    return _t694
end

function parse_gt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t695 = parse_term(parser)
    term173 = _t695
    _t696 = parse_term(parser)
    term_3174 = _t696
    consume_literal!(parser, ")")
    _t697 = Proto.RelTerm(rel_term_type=OneOf(:term, term173))
    _t698 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3174))
    _t699 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t697, _t698])
    return _t699
end

function parse_add(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t700 = parse_term(parser)
    term175 = _t700
    _t701 = parse_term(parser)
    term_3176 = _t701
    _t702 = parse_term(parser)
    term_4177 = _t702
    consume_literal!(parser, ")")
    _t703 = Proto.RelTerm(rel_term_type=OneOf(:term, term175))
    _t704 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3176))
    _t705 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4177))
    _t706 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t703, _t704, _t705])
    return _t706
end

function parse_minus(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t707 = parse_term(parser)
    term178 = _t707
    _t708 = parse_term(parser)
    term_3179 = _t708
    _t709 = parse_term(parser)
    term_4180 = _t709
    consume_literal!(parser, ")")
    _t710 = Proto.RelTerm(rel_term_type=OneOf(:term, term178))
    _t711 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3179))
    _t712 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4180))
    _t713 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t710, _t711, _t712])
    return _t713
end

function parse_multiply(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t714 = parse_term(parser)
    term181 = _t714
    _t715 = parse_term(parser)
    term_3182 = _t715
    _t716 = parse_term(parser)
    term_4183 = _t716
    consume_literal!(parser, ")")
    _t717 = Proto.RelTerm(rel_term_type=OneOf(:term, term181))
    _t718 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3182))
    _t719 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4183))
    _t720 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t717, _t718, _t719])
    return _t720
end

function parse_divide(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t721 = parse_term(parser)
    term184 = _t721
    _t722 = parse_term(parser)
    term_3185 = _t722
    _t723 = parse_term(parser)
    term_4186 = _t723
    consume_literal!(parser, ")")
    _t724 = Proto.RelTerm(rel_term_type=OneOf(:term, term184))
    _t725 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3185))
    _t726 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4186))
    _t727 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t724, _t725, _t726])
    return _t727
end

function parse_rel_term(parser::Parser)::Proto.RelTerm
    
    if match_lookahead_literal(parser, "true", 0)
        _t728 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t729 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t730 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t731 = 1
                else
                    
                    if match_lookahead_literal(parser, "#", 0)
                        _t732 = 0
                    else
                        
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t733 = 1
                        else
                            
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t734 = 1
                            else
                                
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t735 = 1
                                else
                                    
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t736 = 1
                                    else
                                        
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t737 = 1
                                        else
                                            
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t738 = 1
                                            else
                                                
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t739 = 1
                                                else
                                                    _t739 = -1
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
            _t729 = _t730
        end
        _t728 = _t729
    end
    prediction187 = _t728
    
    if prediction187 == 1
        _t741 = parse_term(parser)
        term189 = _t741
        _t742 = Proto.RelTerm(rel_term_type=OneOf(:term, term189))
        _t740 = _t742
    else
        
        if prediction187 == 0
            _t744 = parse_specialized_value(parser)
            specialized_value188 = _t744
            _t745 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value188))
            _t743 = _t745
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t740 = _t743
    end
    return _t740
end

function parse_specialized_value(parser::Parser)::Proto.Value
    consume_literal!(parser, "#")
    _t746 = parse_value(parser)
    value190 = _t746
    return value190
end

function parse_rel_atom(parser::Parser)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t747 = parse_name(parser)
    name191 = _t747
    xs192 = Proto.RelTerm[]
    cond193 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond193
        _t748 = parse_rel_term(parser)
        item194 = _t748
        push!(xs192, item194)
        cond193 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms195 = xs192
    consume_literal!(parser, ")")
    _t749 = Proto.RelAtom(name=name191, terms=rel_terms195)
    return _t749
end

function parse_cast(parser::Parser)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t750 = parse_term(parser)
    term196 = _t750
    _t751 = parse_term(parser)
    term_3197 = _t751
    consume_literal!(parser, ")")
    _t752 = Proto.Cast(input=term196, result=term_3197)
    return _t752
end

function parse_attrs(parser::Parser)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs198 = Proto.Attribute[]
    cond199 = match_lookahead_literal(parser, "(", 0)
    while cond199
        _t753 = parse_attribute(parser)
        item200 = _t753
        push!(xs198, item200)
        cond199 = match_lookahead_literal(parser, "(", 0)
    end
    attributes201 = xs198
    consume_literal!(parser, ")")
    return attributes201
end

function parse_attribute(parser::Parser)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t754 = parse_name(parser)
    name202 = _t754
    xs203 = Proto.Value[]
    cond204 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond204
        _t755 = parse_value(parser)
        item205 = _t755
        push!(xs203, item205)
        cond204 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values206 = xs203
    consume_literal!(parser, ")")
    _t756 = Proto.Attribute(name=name202, args=values206)
    return _t756
end

function parse_algorithm(parser::Parser)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs207 = Proto.RelationId[]
    cond208 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond208
        _t757 = parse_relation_id(parser)
        item209 = _t757
        push!(xs207, item209)
        cond208 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids210 = xs207
    _t758 = parse_script(parser)
    script211 = _t758
    consume_literal!(parser, ")")
    _t759 = Proto.Algorithm(var"#global"=relation_ids210, body=script211)
    return _t759
end

function parse_script(parser::Parser)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs212 = Proto.Construct[]
    cond213 = match_lookahead_literal(parser, "(", 0)
    while cond213
        _t760 = parse_construct(parser)
        item214 = _t760
        push!(xs212, item214)
        cond213 = match_lookahead_literal(parser, "(", 0)
    end
    constructs215 = xs212
    consume_literal!(parser, ")")
    _t761 = Proto.Script(constructs=constructs215)
    return _t761
end

function parse_construct(parser::Parser)::Proto.Construct
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t763 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t764 = 1
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t765 = 1
                else
                    
                    if match_lookahead_literal(parser, "loop", 1)
                        _t766 = 0
                    else
                        
                        if match_lookahead_literal(parser, "break", 1)
                            _t767 = 1
                        else
                            
                            if match_lookahead_literal(parser, "assign", 1)
                                _t768 = 1
                            else
                                _t768 = -1
                            end
                            _t767 = _t768
                        end
                        _t766 = _t767
                    end
                    _t765 = _t766
                end
                _t764 = _t765
            end
            _t763 = _t764
        end
        _t762 = _t763
    else
        _t762 = -1
    end
    prediction216 = _t762
    
    if prediction216 == 1
        _t770 = parse_instruction(parser)
        instruction218 = _t770
        _t771 = Proto.Construct(construct_type=OneOf(:instruction, instruction218))
        _t769 = _t771
    else
        
        if prediction216 == 0
            _t773 = parse_loop(parser)
            loop217 = _t773
            _t774 = Proto.Construct(construct_type=OneOf(:loop, loop217))
            _t772 = _t774
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t769 = _t772
    end
    return _t769
end

function parse_loop(parser::Parser)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t775 = parse_init(parser)
    init219 = _t775
    _t776 = parse_script(parser)
    script220 = _t776
    consume_literal!(parser, ")")
    _t777 = Proto.Loop(init=init219, body=script220)
    return _t777
end

function parse_init(parser::Parser)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs221 = Proto.Instruction[]
    cond222 = match_lookahead_literal(parser, "(", 0)
    while cond222
        _t778 = parse_instruction(parser)
        item223 = _t778
        push!(xs221, item223)
        cond222 = match_lookahead_literal(parser, "(", 0)
    end
    instructions224 = xs221
    consume_literal!(parser, ")")
    return instructions224
end

function parse_instruction(parser::Parser)::Proto.Instruction
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t780 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t781 = 4
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t782 = 3
                else
                    
                    if match_lookahead_literal(parser, "break", 1)
                        _t783 = 2
                    else
                        
                        if match_lookahead_literal(parser, "assign", 1)
                            _t784 = 0
                        else
                            _t784 = -1
                        end
                        _t783 = _t784
                    end
                    _t782 = _t783
                end
                _t781 = _t782
            end
            _t780 = _t781
        end
        _t779 = _t780
    else
        _t779 = -1
    end
    prediction225 = _t779
    
    if prediction225 == 4
        _t786 = parse_monus_def(parser)
        monus_def230 = _t786
        _t787 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def230))
        _t785 = _t787
    else
        
        if prediction225 == 3
            _t789 = parse_monoid_def(parser)
            monoid_def229 = _t789
            _t790 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def229))
            _t788 = _t790
        else
            
            if prediction225 == 2
                _t792 = parse_break(parser)
                break228 = _t792
                _t793 = Proto.Instruction(instr_type=OneOf(:var"#break", break228))
                _t791 = _t793
            else
                
                if prediction225 == 1
                    _t795 = parse_upsert(parser)
                    upsert227 = _t795
                    _t796 = Proto.Instruction(instr_type=OneOf(:upsert, upsert227))
                    _t794 = _t796
                else
                    
                    if prediction225 == 0
                        _t798 = parse_assign(parser)
                        assign226 = _t798
                        _t799 = Proto.Instruction(instr_type=OneOf(:assign, assign226))
                        _t797 = _t799
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t794 = _t797
                end
                _t791 = _t794
            end
            _t788 = _t791
        end
        _t785 = _t788
    end
    return _t785
end

function parse_assign(parser::Parser)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t800 = parse_relation_id(parser)
    relation_id231 = _t800
    _t801 = parse_abstraction(parser)
    abstraction232 = _t801
    
    if match_lookahead_literal(parser, "(", 0)
        _t803 = parse_attrs(parser)
        _t802 = _t803
    else
        _t802 = nothing
    end
    attrs233 = _t802
    consume_literal!(parser, ")")
    _t804 = Proto.Assign(name=relation_id231, body=abstraction232, attrs=(!isnothing(attrs233) ? attrs233 : Proto.Attribute[]))
    return _t804
end

function parse_upsert(parser::Parser)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t805 = parse_relation_id(parser)
    relation_id234 = _t805
    _t806 = parse_abstraction_with_arity(parser)
    abstraction_with_arity235 = _t806
    
    if match_lookahead_literal(parser, "(", 0)
        _t808 = parse_attrs(parser)
        _t807 = _t808
    else
        _t807 = nothing
    end
    attrs236 = _t807
    consume_literal!(parser, ")")
    _t809 = Proto.Upsert(name=relation_id234, body=abstraction_with_arity235[1], attrs=(!isnothing(attrs236) ? attrs236 : Proto.Attribute[]), value_arity=abstraction_with_arity235[2])
    return _t809
end

function parse_abstraction_with_arity(parser::Parser)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t810 = parse_bindings(parser)
    bindings237 = _t810
    _t811 = parse_formula(parser)
    formula238 = _t811
    consume_literal!(parser, ")")
    _t812 = Proto.Abstraction(vars=vcat(bindings237[1], !isnothing(bindings237[2]) ? bindings237[2] : []), value=formula238)
    return (_t812, length(bindings237[2]),)
end

function parse_break(parser::Parser)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t813 = parse_relation_id(parser)
    relation_id239 = _t813
    _t814 = parse_abstraction(parser)
    abstraction240 = _t814
    
    if match_lookahead_literal(parser, "(", 0)
        _t816 = parse_attrs(parser)
        _t815 = _t816
    else
        _t815 = nothing
    end
    attrs241 = _t815
    consume_literal!(parser, ")")
    _t817 = Proto.Break(name=relation_id239, body=abstraction240, attrs=(!isnothing(attrs241) ? attrs241 : Proto.Attribute[]))
    return _t817
end

function parse_monoid_def(parser::Parser)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t818 = parse_monoid(parser)
    monoid242 = _t818
    _t819 = parse_relation_id(parser)
    relation_id243 = _t819
    _t820 = parse_abstraction_with_arity(parser)
    abstraction_with_arity244 = _t820
    
    if match_lookahead_literal(parser, "(", 0)
        _t822 = parse_attrs(parser)
        _t821 = _t822
    else
        _t821 = nothing
    end
    attrs245 = _t821
    consume_literal!(parser, ")")
    _t823 = Proto.MonoidDef(monoid=monoid242, name=relation_id243, body=abstraction_with_arity244[1], attrs=(!isnothing(attrs245) ? attrs245 : Proto.Attribute[]), value_arity=abstraction_with_arity244[2])
    return _t823
end

function parse_monoid(parser::Parser)::Proto.Monoid
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "sum", 1)
            _t825 = 3
        else
            
            if match_lookahead_literal(parser, "or", 1)
                _t826 = 0
            else
                
                if match_lookahead_literal(parser, "min", 1)
                    _t827 = 1
                else
                    
                    if match_lookahead_literal(parser, "max", 1)
                        _t828 = 2
                    else
                        _t828 = -1
                    end
                    _t827 = _t828
                end
                _t826 = _t827
            end
            _t825 = _t826
        end
        _t824 = _t825
    else
        _t824 = -1
    end
    prediction246 = _t824
    
    if prediction246 == 3
        _t830 = parse_sum_monoid(parser)
        sum_monoid250 = _t830
        _t831 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid250))
        _t829 = _t831
    else
        
        if prediction246 == 2
            _t833 = parse_max_monoid(parser)
            max_monoid249 = _t833
            _t834 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid249))
            _t832 = _t834
        else
            
            if prediction246 == 1
                _t836 = parse_min_monoid(parser)
                min_monoid248 = _t836
                _t837 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid248))
                _t835 = _t837
            else
                
                if prediction246 == 0
                    _t839 = parse_or_monoid(parser)
                    or_monoid247 = _t839
                    _t840 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid247))
                    _t838 = _t840
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t835 = _t838
            end
            _t832 = _t835
        end
        _t829 = _t832
    end
    return _t829
end

function parse_or_monoid(parser::Parser)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t841 = Proto.OrMonoid()
    return _t841
end

function parse_min_monoid(parser::Parser)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t842 = parse_type(parser)
    type251 = _t842
    consume_literal!(parser, ")")
    _t843 = Proto.MinMonoid(var"#type"=type251)
    return _t843
end

function parse_max_monoid(parser::Parser)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t844 = parse_type(parser)
    type252 = _t844
    consume_literal!(parser, ")")
    _t845 = Proto.MaxMonoid(var"#type"=type252)
    return _t845
end

function parse_sum_monoid(parser::Parser)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t846 = parse_type(parser)
    type253 = _t846
    consume_literal!(parser, ")")
    _t847 = Proto.SumMonoid(var"#type"=type253)
    return _t847
end

function parse_monus_def(parser::Parser)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t848 = parse_monoid(parser)
    monoid254 = _t848
    _t849 = parse_relation_id(parser)
    relation_id255 = _t849
    _t850 = parse_abstraction_with_arity(parser)
    abstraction_with_arity256 = _t850
    
    if match_lookahead_literal(parser, "(", 0)
        _t852 = parse_attrs(parser)
        _t851 = _t852
    else
        _t851 = nothing
    end
    attrs257 = _t851
    consume_literal!(parser, ")")
    _t853 = Proto.MonusDef(monoid=monoid254, name=relation_id255, body=abstraction_with_arity256[1], attrs=(!isnothing(attrs257) ? attrs257 : Proto.Attribute[]), value_arity=abstraction_with_arity256[2])
    return _t853
end

function parse_constraint(parser::Parser)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t854 = parse_relation_id(parser)
    relation_id258 = _t854
    _t855 = parse_abstraction(parser)
    abstraction259 = _t855
    _t856 = parse_functional_dependency_keys(parser)
    functional_dependency_keys260 = _t856
    _t857 = parse_functional_dependency_values(parser)
    functional_dependency_values261 = _t857
    consume_literal!(parser, ")")
    _t858 = Proto.FunctionalDependency(guard=abstraction259, keys=functional_dependency_keys260, values=functional_dependency_values261)
    _t859 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t858), name=relation_id258)
    return _t859
end

function parse_functional_dependency_keys(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs262 = Proto.Var[]
    cond263 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond263
        _t860 = parse_var(parser)
        item264 = _t860
        push!(xs262, item264)
        cond263 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars265 = xs262
    consume_literal!(parser, ")")
    return vars265
end

function parse_functional_dependency_values(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs266 = Proto.Var[]
    cond267 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond267
        _t861 = parse_var(parser)
        item268 = _t861
        push!(xs266, item268)
        cond267 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars269 = xs266
    consume_literal!(parser, ")")
    return vars269
end

function parse_data(parser::Parser)::Proto.Data
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t863 = 0
        else
            
            if match_lookahead_literal(parser, "csv_data", 1)
                _t864 = 2
            else
                
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t865 = 1
                else
                    _t865 = -1
                end
                _t864 = _t865
            end
            _t863 = _t864
        end
        _t862 = _t863
    else
        _t862 = -1
    end
    prediction270 = _t862
    
    if prediction270 == 2
        _t867 = parse_csv_data(parser)
        csv_data273 = _t867
        _t868 = Proto.Data(data_type=OneOf(:csv_data, csv_data273))
        _t866 = _t868
    else
        
        if prediction270 == 1
            _t870 = parse_betree_relation(parser)
            betree_relation272 = _t870
            _t871 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation272))
            _t869 = _t871
        else
            
            if prediction270 == 0
                _t873 = parse_rel_edb(parser)
                rel_edb271 = _t873
                _t874 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb271))
                _t872 = _t874
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t869 = _t872
        end
        _t866 = _t869
    end
    return _t866
end

function parse_rel_edb(parser::Parser)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t875 = parse_relation_id(parser)
    relation_id274 = _t875
    _t876 = parse_rel_edb_path(parser)
    rel_edb_path275 = _t876
    _t877 = parse_rel_edb_types(parser)
    rel_edb_types276 = _t877
    consume_literal!(parser, ")")
    _t878 = Proto.RelEDB(target_id=relation_id274, path=rel_edb_path275, types=rel_edb_types276)
    return _t878
end

function parse_rel_edb_path(parser::Parser)::Vector{String}
    consume_literal!(parser, "[")
    xs277 = String[]
    cond278 = match_lookahead_terminal(parser, "STRING", 0)
    while cond278
        item279 = consume_terminal!(parser, "STRING")
        push!(xs277, item279)
        cond278 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings280 = xs277
    consume_literal!(parser, "]")
    return strings280
end

function parse_rel_edb_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs281 = Proto.var"#Type"[]
    cond282 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond282
        _t879 = parse_type(parser)
        item283 = _t879
        push!(xs281, item283)
        cond282 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types284 = xs281
    consume_literal!(parser, "]")
    return types284
end

function parse_betree_relation(parser::Parser)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t880 = parse_relation_id(parser)
    relation_id285 = _t880
    _t881 = parse_betree_info(parser)
    betree_info286 = _t881
    consume_literal!(parser, ")")
    _t882 = Proto.BeTreeRelation(name=relation_id285, relation_info=betree_info286)
    return _t882
end

function parse_betree_info(parser::Parser)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t883 = parse_betree_info_key_types(parser)
    betree_info_key_types287 = _t883
    _t884 = parse_betree_info_value_types(parser)
    betree_info_value_types288 = _t884
    _t885 = parse_config_dict(parser)
    config_dict289 = _t885
    consume_literal!(parser, ")")
    _t886 = construct_betree_info(parser, betree_info_key_types287, betree_info_value_types288, config_dict289)
    return _t886
end

function parse_betree_info_key_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs290 = Proto.var"#Type"[]
    cond291 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond291
        _t887 = parse_type(parser)
        item292 = _t887
        push!(xs290, item292)
        cond291 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types293 = xs290
    consume_literal!(parser, ")")
    return types293
end

function parse_betree_info_value_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs294 = Proto.var"#Type"[]
    cond295 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond295
        _t888 = parse_type(parser)
        item296 = _t888
        push!(xs294, item296)
        cond295 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types297 = xs294
    consume_literal!(parser, ")")
    return types297
end

function parse_csv_data(parser::Parser)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t889 = parse_csvlocator(parser)
    csvlocator298 = _t889
    _t890 = parse_csv_config(parser)
    csv_config299 = _t890
    _t891 = parse_csv_columns(parser)
    csv_columns300 = _t891
    _t892 = parse_csv_asof(parser)
    csv_asof301 = _t892
    consume_literal!(parser, ")")
    _t893 = Proto.CSVData(locator=csvlocator298, config=csv_config299, columns=csv_columns300, asof=csv_asof301)
    return _t893
end

function parse_csvlocator(parser::Parser)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t895 = parse_csv_locator_paths(parser)
        _t894 = _t895
    else
        _t894 = nothing
    end
    csv_locator_paths302 = _t894
    
    if match_lookahead_literal(parser, "(", 0)
        _t897 = parse_csv_locator_inline_data(parser)
        _t896 = _t897
    else
        _t896 = nothing
    end
    csv_locator_inline_data303 = _t896
    consume_literal!(parser, ")")
    _t898 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths302) ? csv_locator_paths302 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data303) ? csv_locator_inline_data303 : "")))
    return _t898
end

function parse_csv_locator_paths(parser::Parser)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs304 = String[]
    cond305 = match_lookahead_terminal(parser, "STRING", 0)
    while cond305
        item306 = consume_terminal!(parser, "STRING")
        push!(xs304, item306)
        cond305 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings307 = xs304
    consume_literal!(parser, ")")
    return strings307
end

function parse_csv_locator_inline_data(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string308 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string308
end

function parse_csv_config(parser::Parser)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t899 = parse_config_dict(parser)
    config_dict309 = _t899
    consume_literal!(parser, ")")
    _t900 = construct_csv_config(parser, config_dict309)
    return _t900
end

function parse_csv_columns(parser::Parser)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs310 = Proto.CSVColumn[]
    cond311 = match_lookahead_literal(parser, "(", 0)
    while cond311
        _t901 = parse_csv_column(parser)
        item312 = _t901
        push!(xs310, item312)
        cond311 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns313 = xs310
    consume_literal!(parser, ")")
    return csv_columns313
end

function parse_csv_column(parser::Parser)::Proto.CSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string314 = consume_terminal!(parser, "STRING")
    _t902 = parse_relation_id(parser)
    relation_id315 = _t902
    consume_literal!(parser, "[")
    xs316 = Proto.var"#Type"[]
    cond317 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond317
        _t903 = parse_type(parser)
        item318 = _t903
        push!(xs316, item318)
        cond317 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types319 = xs316
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t904 = Proto.CSVColumn(column_name=string314, target_id=relation_id315, types=types319)
    return _t904
end

function parse_csv_asof(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string320 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string320
end

function parse_undefine(parser::Parser)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t905 = parse_fragment_id(parser)
    fragment_id321 = _t905
    consume_literal!(parser, ")")
    _t906 = Proto.Undefine(fragment_id=fragment_id321)
    return _t906
end

function parse_context(parser::Parser)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs322 = Proto.RelationId[]
    cond323 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond323
        _t907 = parse_relation_id(parser)
        item324 = _t907
        push!(xs322, item324)
        cond323 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids325 = xs322
    consume_literal!(parser, ")")
    _t908 = Proto.Context(relations=relation_ids325)
    return _t908
end

function parse_snapshot(parser::Parser)::Proto.Snapshot
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    _t909 = parse_rel_edb_path(parser)
    rel_edb_path326 = _t909
    _t910 = parse_relation_id(parser)
    relation_id327 = _t910
    consume_literal!(parser, ")")
    _t911 = Proto.Snapshot(destination_path=rel_edb_path326, source_relation=relation_id327)
    return _t911
end

function parse_epoch_reads(parser::Parser)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs328 = Proto.Read[]
    cond329 = match_lookahead_literal(parser, "(", 0)
    while cond329
        _t912 = parse_read(parser)
        item330 = _t912
        push!(xs328, item330)
        cond329 = match_lookahead_literal(parser, "(", 0)
    end
    reads331 = xs328
    consume_literal!(parser, ")")
    return reads331
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
    prediction332 = _t913
    
    if prediction332 == 4
        _t920 = parse_export(parser)
        export337 = _t920
        _t921 = Proto.Read(read_type=OneOf(:var"#export", export337))
        _t919 = _t921
    else
        
        if prediction332 == 3
            _t923 = parse_abort(parser)
            abort336 = _t923
            _t924 = Proto.Read(read_type=OneOf(:abort, abort336))
            _t922 = _t924
        else
            
            if prediction332 == 2
                _t926 = parse_what_if(parser)
                what_if335 = _t926
                _t927 = Proto.Read(read_type=OneOf(:what_if, what_if335))
                _t925 = _t927
            else
                
                if prediction332 == 1
                    _t929 = parse_output(parser)
                    output334 = _t929
                    _t930 = Proto.Read(read_type=OneOf(:output, output334))
                    _t928 = _t930
                else
                    
                    if prediction332 == 0
                        _t932 = parse_demand(parser)
                        demand333 = _t932
                        _t933 = Proto.Read(read_type=OneOf(:demand, demand333))
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
    relation_id338 = _t934
    consume_literal!(parser, ")")
    _t935 = Proto.Demand(relation_id=relation_id338)
    return _t935
end

function parse_output(parser::Parser)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t936 = parse_name(parser)
    name339 = _t936
    _t937 = parse_relation_id(parser)
    relation_id340 = _t937
    consume_literal!(parser, ")")
    _t938 = Proto.Output(name=name339, relation_id=relation_id340)
    return _t938
end

function parse_what_if(parser::Parser)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t939 = parse_name(parser)
    name341 = _t939
    _t940 = parse_epoch(parser)
    epoch342 = _t940
    consume_literal!(parser, ")")
    _t941 = Proto.WhatIf(branch=name341, epoch=epoch342)
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
    name343 = _t942
    _t944 = parse_relation_id(parser)
    relation_id344 = _t944
    consume_literal!(parser, ")")
    _t945 = Proto.Abort(name=(!isnothing(name343) ? name343 : "abort"), relation_id=relation_id344)
    return _t945
end

function parse_export(parser::Parser)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t946 = parse_export_csv_config(parser)
    export_csv_config345 = _t946
    consume_literal!(parser, ")")
    _t947 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config345))
    return _t947
end

function parse_export_csv_config(parser::Parser)::Proto.ExportCSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t948 = parse_export_csv_path(parser)
    export_csv_path346 = _t948
    _t949 = parse_export_csv_columns(parser)
    export_csv_columns347 = _t949
    _t950 = parse_config_dict(parser)
    config_dict348 = _t950
    consume_literal!(parser, ")")
    _t951 = export_csv_config(parser, export_csv_path346, export_csv_columns347, config_dict348)
    return _t951
end

function parse_export_csv_path(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string349 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string349
end

function parse_export_csv_columns(parser::Parser)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs350 = Proto.ExportCSVColumn[]
    cond351 = match_lookahead_literal(parser, "(", 0)
    while cond351
        _t952 = parse_export_csv_column(parser)
        item352 = _t952
        push!(xs350, item352)
        cond351 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns353 = xs350
    consume_literal!(parser, ")")
    return export_csv_columns353
end

function parse_export_csv_column(parser::Parser)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string354 = consume_terminal!(parser, "STRING")
    _t953 = parse_relation_id(parser)
    relation_id355 = _t953
    consume_literal!(parser, ")")
    _t954 = Proto.ExportCSVColumn(column_name=string354, column_data=relation_id355)
    return _t954
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
