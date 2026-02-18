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
    else
        _t1855 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1856 = nothing
    end
    return default
end

function _extract_value_string(parser::Parser, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1857 = nothing
    end
    return default
end

function _extract_value_boolean(parser::Parser, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1858 = nothing
    end
    return default
end

function _extract_value_string_list(parser::Parser, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1859 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1860 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1861 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1862 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1863 = nothing
    end
    return nothing
end

function construct_csv_config(parser::Parser, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1864 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1864
    _t1865 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1865
    _t1866 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1866
    _t1867 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1867
    _t1868 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1868
    _t1869 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1869
    _t1870 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1870
    _t1871 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1871
    _t1872 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1872
    _t1873 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1873
    _t1874 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1874
    _t1875 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1875
end

function construct_betree_info(parser::Parser, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1876 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1876
    _t1877 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1877
    _t1878 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1878
    _t1879 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1879
    _t1880 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1880
    _t1881 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1881
    _t1882 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1882
    _t1883 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1883
    _t1884 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1884
    _t1885 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1885
    _t1886 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1886
end

function default_configure(parser::Parser)::Proto.Configure
    _t1887 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1887
    _t1888 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1888
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
    _t1889 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1889
    _t1890 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1890
    _t1891 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1891
end

function export_csv_config(parser::Parser, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1892 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1892
    _t1893 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1893
    _t1894 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1894
    _t1895 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1895
    _t1896 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1896
    _t1897 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1897
    _t1898 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1898
    _t1899 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1899
end

# --- Parse functions ---

function parse_transaction(parser::Parser)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1264 = parse_configure(parser)
        _t1263 = _t1264
    else
        _t1263 = nothing
    end
    configure910 = _t1263
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1266 = parse_sync(parser)
        _t1265 = _t1266
    else
        _t1265 = nothing
    end
    sync911 = _t1265
    xs912 = Proto.Epoch[]
    cond913 = match_lookahead_literal(parser, "(", 0)
    while cond913
        _t1267 = parse_epoch(parser)
        item914 = _t1267
        push!(xs912, item914)
        cond913 = match_lookahead_literal(parser, "(", 0)
    end
    epochs915 = xs912
    consume_literal!(parser, ")")
    _t1268 = default_configure(parser)
    _t1269 = Proto.Transaction(epochs=epochs915, configure=(!isnothing(configure910) ? configure910 : _t1268), sync=sync911)
    return _t1269
end

function parse_configure(parser::Parser)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1270 = parse_config_dict(parser)
    config_dict916 = _t1270
    consume_literal!(parser, ")")
    _t1271 = construct_configure(parser, config_dict916)
    return _t1271
end

function parse_config_dict(parser::Parser)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs917 = Tuple{String, Proto.Value}[]
    cond918 = match_lookahead_literal(parser, ":", 0)
    while cond918
        _t1272 = parse_config_key_value(parser)
        item919 = _t1272
        push!(xs917, item919)
        cond918 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values920 = xs917
    consume_literal!(parser, "}")
    return config_key_values920
end

function parse_config_key_value(parser::Parser)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol921 = consume_terminal!(parser, "SYMBOL")
    _t1273 = parse_value(parser)
    value922 = _t1273
    return (symbol921, value922,)
end

function parse_value(parser::Parser)::Proto.Value
    if match_lookahead_literal(parser, "true", 0)
        _t1274 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1275 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1276 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1278 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1279 = 0
                        else
                            _t1279 = -1
                        end
                        _t1278 = _t1279
                    end
                    _t1277 = _t1278
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1280 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1281 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t1282 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t1283 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t1284 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t1285 = 7
                                        else
                                            _t1285 = -1
                                        end
                                        _t1284 = _t1285
                                    end
                                    _t1283 = _t1284
                                end
                                _t1282 = _t1283
                            end
                            _t1281 = _t1282
                        end
                        _t1280 = _t1281
                    end
                    _t1277 = _t1280
                end
                _t1276 = _t1277
            end
            _t1275 = _t1276
        end
        _t1274 = _t1275
    end
    prediction923 = _t1274
    if prediction923 == 9
        _t1287 = parse_boolean_value(parser)
        boolean_value932 = _t1287
        _t1288 = Proto.Value(value=OneOf(:boolean_value, boolean_value932))
        _t1286 = _t1288
    else
        if prediction923 == 8
            consume_literal!(parser, "missing")
            _t1290 = Proto.MissingValue()
            _t1291 = Proto.Value(value=OneOf(:missing_value, _t1290))
            _t1289 = _t1291
        else
            if prediction923 == 7
                decimal931 = consume_terminal!(parser, "DECIMAL")
                _t1293 = Proto.Value(value=OneOf(:decimal_value, decimal931))
                _t1292 = _t1293
            else
                if prediction923 == 6
                    int128930 = consume_terminal!(parser, "INT128")
                    _t1295 = Proto.Value(value=OneOf(:int128_value, int128930))
                    _t1294 = _t1295
                else
                    if prediction923 == 5
                        uint128929 = consume_terminal!(parser, "UINT128")
                        _t1297 = Proto.Value(value=OneOf(:uint128_value, uint128929))
                        _t1296 = _t1297
                    else
                        if prediction923 == 4
                            float928 = consume_terminal!(parser, "FLOAT")
                            _t1299 = Proto.Value(value=OneOf(:float_value, float928))
                            _t1298 = _t1299
                        else
                            if prediction923 == 3
                                int927 = consume_terminal!(parser, "INT")
                                _t1301 = Proto.Value(value=OneOf(:int_value, int927))
                                _t1300 = _t1301
                            else
                                if prediction923 == 2
                                    string926 = consume_terminal!(parser, "STRING")
                                    _t1303 = Proto.Value(value=OneOf(:string_value, string926))
                                    _t1302 = _t1303
                                else
                                    if prediction923 == 1
                                        _t1305 = parse_datetime(parser)
                                        datetime925 = _t1305
                                        _t1306 = Proto.Value(value=OneOf(:datetime_value, datetime925))
                                        _t1304 = _t1306
                                    else
                                        if prediction923 == 0
                                            _t1308 = parse_date(parser)
                                            date924 = _t1308
                                            _t1309 = Proto.Value(value=OneOf(:date_value, date924))
                                            _t1307 = _t1309
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1304 = _t1307
                                    end
                                    _t1302 = _t1304
                                end
                                _t1300 = _t1302
                            end
                            _t1298 = _t1300
                        end
                        _t1296 = _t1298
                    end
                    _t1294 = _t1296
                end
                _t1292 = _t1294
            end
            _t1289 = _t1292
        end
        _t1286 = _t1289
    end
    return _t1286
end

function parse_date(parser::Parser)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int933 = consume_terminal!(parser, "INT")
    int_3934 = consume_terminal!(parser, "INT")
    int_4935 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1310 = Proto.DateValue(year=Int32(int933), month=Int32(int_3934), day=Int32(int_4935))
    return _t1310
end

function parse_datetime(parser::Parser)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int936 = consume_terminal!(parser, "INT")
    int_3937 = consume_terminal!(parser, "INT")
    int_4938 = consume_terminal!(parser, "INT")
    int_5939 = consume_terminal!(parser, "INT")
    int_6940 = consume_terminal!(parser, "INT")
    int_7941 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1311 = consume_terminal!(parser, "INT")
    else
        _t1311 = nothing
    end
    int_8942 = _t1311
    consume_literal!(parser, ")")
    _t1312 = Proto.DateTimeValue(year=Int32(int936), month=Int32(int_3937), day=Int32(int_4938), hour=Int32(int_5939), minute=Int32(int_6940), second=Int32(int_7941), microsecond=Int32((!isnothing(int_8942) ? int_8942 : 0)))
    return _t1312
end

function parse_boolean_value(parser::Parser)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1313 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1314 = 1
        else
            _t1314 = -1
        end
        _t1313 = _t1314
    end
    prediction943 = _t1313
    if prediction943 == 1
        consume_literal!(parser, "false")
        _t1315 = false
    else
        if prediction943 == 0
            consume_literal!(parser, "true")
            _t1316 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1315 = _t1316
    end
    return _t1315
end

function parse_sync(parser::Parser)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs944 = Proto.FragmentId[]
    cond945 = match_lookahead_literal(parser, ":", 0)
    while cond945
        _t1317 = parse_fragment_id(parser)
        item946 = _t1317
        push!(xs944, item946)
        cond945 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids947 = xs944
    consume_literal!(parser, ")")
    _t1318 = Proto.Sync(fragments=fragment_ids947)
    return _t1318
end

function parse_fragment_id(parser::Parser)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol948 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol948))
end

function parse_epoch(parser::Parser)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1320 = parse_epoch_writes(parser)
        _t1319 = _t1320
    else
        _t1319 = nothing
    end
    epoch_writes949 = _t1319
    if match_lookahead_literal(parser, "(", 0)
        _t1322 = parse_epoch_reads(parser)
        _t1321 = _t1322
    else
        _t1321 = nothing
    end
    epoch_reads950 = _t1321
    consume_literal!(parser, ")")
    _t1323 = Proto.Epoch(writes=(!isnothing(epoch_writes949) ? epoch_writes949 : Proto.Write[]), reads=(!isnothing(epoch_reads950) ? epoch_reads950 : Proto.Read[]))
    return _t1323
end

function parse_epoch_writes(parser::Parser)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs951 = Proto.Write[]
    cond952 = match_lookahead_literal(parser, "(", 0)
    while cond952
        _t1324 = parse_write(parser)
        item953 = _t1324
        push!(xs951, item953)
        cond952 = match_lookahead_literal(parser, "(", 0)
    end
    writes954 = xs951
    consume_literal!(parser, ")")
    return writes954
end

function parse_write(parser::Parser)::Proto.Write
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1326 = 1
        else
            if match_lookahead_literal(parser, "define", 1)
                _t1327 = 0
            else
                if match_lookahead_literal(parser, "context", 1)
                    _t1328 = 2
                else
                    _t1328 = -1
                end
                _t1327 = _t1328
            end
            _t1326 = _t1327
        end
        _t1325 = _t1326
    else
        _t1325 = -1
    end
    prediction955 = _t1325
    if prediction955 == 2
        _t1330 = parse_context(parser)
        context958 = _t1330
        _t1331 = Proto.Write(write_type=OneOf(:context, context958))
        _t1329 = _t1331
    else
        if prediction955 == 1
            _t1333 = parse_undefine(parser)
            undefine957 = _t1333
            _t1334 = Proto.Write(write_type=OneOf(:undefine, undefine957))
            _t1332 = _t1334
        else
            if prediction955 == 0
                _t1336 = parse_define(parser)
                define956 = _t1336
                _t1337 = Proto.Write(write_type=OneOf(:define, define956))
                _t1335 = _t1337
            else
                throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
            end
            _t1332 = _t1335
        end
        _t1329 = _t1332
    end
    return _t1329
end

function parse_define(parser::Parser)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1338 = parse_fragment(parser)
    fragment959 = _t1338
    consume_literal!(parser, ")")
    _t1339 = Proto.Define(fragment=fragment959)
    return _t1339
end

function parse_fragment(parser::Parser)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1340 = parse_new_fragment_id(parser)
    new_fragment_id960 = _t1340
    xs961 = Proto.Declaration[]
    cond962 = match_lookahead_literal(parser, "(", 0)
    while cond962
        _t1341 = parse_declaration(parser)
        item963 = _t1341
        push!(xs961, item963)
        cond962 = match_lookahead_literal(parser, "(", 0)
    end
    declarations964 = xs961
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id960, declarations964)
end

function parse_new_fragment_id(parser::Parser)::Proto.FragmentId
    _t1342 = parse_fragment_id(parser)
    fragment_id965 = _t1342
    start_fragment!(parser, fragment_id965)
    return fragment_id965
end

function parse_declaration(parser::Parser)::Proto.Declaration
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1344 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t1345 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1346 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1347 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1348 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1349 = 1
                            else
                                _t1349 = -1
                            end
                            _t1348 = _t1349
                        end
                        _t1347 = _t1348
                    end
                    _t1346 = _t1347
                end
                _t1345 = _t1346
            end
            _t1344 = _t1345
        end
        _t1343 = _t1344
    else
        _t1343 = -1
    end
    prediction966 = _t1343
    if prediction966 == 3
        _t1351 = parse_data(parser)
        data970 = _t1351
        _t1352 = Proto.Declaration(declaration_type=OneOf(:data, data970))
        _t1350 = _t1352
    else
        if prediction966 == 2
            _t1354 = parse_constraint(parser)
            constraint969 = _t1354
            _t1355 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint969))
            _t1353 = _t1355
        else
            if prediction966 == 1
                _t1357 = parse_algorithm(parser)
                algorithm968 = _t1357
                _t1358 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm968))
                _t1356 = _t1358
            else
                if prediction966 == 0
                    _t1360 = parse_def(parser)
                    def967 = _t1360
                    _t1361 = Proto.Declaration(declaration_type=OneOf(:def, def967))
                    _t1359 = _t1361
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1356 = _t1359
            end
            _t1353 = _t1356
        end
        _t1350 = _t1353
    end
    return _t1350
end

function parse_def(parser::Parser)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1362 = parse_relation_id(parser)
    relation_id971 = _t1362
    _t1363 = parse_abstraction(parser)
    abstraction972 = _t1363
    if match_lookahead_literal(parser, "(", 0)
        _t1365 = parse_attrs(parser)
        _t1364 = _t1365
    else
        _t1364 = nothing
    end
    attrs973 = _t1364
    consume_literal!(parser, ")")
    _t1366 = Proto.Def(name=relation_id971, body=abstraction972, attrs=(!isnothing(attrs973) ? attrs973 : Proto.Attribute[]))
    return _t1366
end

function parse_relation_id(parser::Parser)::Proto.RelationId
    if match_lookahead_literal(parser, ":", 0)
        _t1367 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1368 = 1
        else
            _t1368 = -1
        end
        _t1367 = _t1368
    end
    prediction974 = _t1367
    if prediction974 == 1
        uint128976 = consume_terminal!(parser, "UINT128")
        _t1369 = Proto.RelationId(uint128976.low, uint128976.high)
    else
        if prediction974 == 0
            consume_literal!(parser, ":")
            symbol975 = consume_terminal!(parser, "SYMBOL")
            _t1370 = relation_id_from_string(parser, symbol975)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1369 = _t1370
    end
    return _t1369
end

function parse_abstraction(parser::Parser)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t1371 = parse_bindings(parser)
    bindings977 = _t1371
    _t1372 = parse_formula(parser)
    formula978 = _t1372
    consume_literal!(parser, ")")
    _t1373 = Proto.Abstraction(vars=vcat(bindings977[1], !isnothing(bindings977[2]) ? bindings977[2] : []), value=formula978)
    return _t1373
end

function parse_bindings(parser::Parser)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs979 = Proto.Binding[]
    cond980 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond980
        _t1374 = parse_binding(parser)
        item981 = _t1374
        push!(xs979, item981)
        cond980 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings982 = xs979
    if match_lookahead_literal(parser, "|", 0)
        _t1376 = parse_value_bindings(parser)
        _t1375 = _t1376
    else
        _t1375 = nothing
    end
    value_bindings983 = _t1375
    consume_literal!(parser, "]")
    return (bindings982, (!isnothing(value_bindings983) ? value_bindings983 : Proto.Binding[]),)
end

function parse_binding(parser::Parser)::Proto.Binding
    symbol984 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1377 = parse_type(parser)
    type985 = _t1377
    _t1378 = Proto.Var(name=symbol984)
    _t1379 = Proto.Binding(var=_t1378, var"#type"=type985)
    return _t1379
end

function parse_type(parser::Parser)::Proto.var"#Type"
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1380 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t1381 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t1382 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t1383 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t1384 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t1385 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t1386 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t1387 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t1388 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t1389 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t1390 = 9
                                            else
                                                _t1390 = -1
                                            end
                                            _t1389 = _t1390
                                        end
                                        _t1388 = _t1389
                                    end
                                    _t1387 = _t1388
                                end
                                _t1386 = _t1387
                            end
                            _t1385 = _t1386
                        end
                        _t1384 = _t1385
                    end
                    _t1383 = _t1384
                end
                _t1382 = _t1383
            end
            _t1381 = _t1382
        end
        _t1380 = _t1381
    end
    prediction986 = _t1380
    if prediction986 == 10
        _t1392 = parse_boolean_type(parser)
        boolean_type997 = _t1392
        _t1393 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type997))
        _t1391 = _t1393
    else
        if prediction986 == 9
            _t1395 = parse_decimal_type(parser)
            decimal_type996 = _t1395
            _t1396 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type996))
            _t1394 = _t1396
        else
            if prediction986 == 8
                _t1398 = parse_missing_type(parser)
                missing_type995 = _t1398
                _t1399 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type995))
                _t1397 = _t1399
            else
                if prediction986 == 7
                    _t1401 = parse_datetime_type(parser)
                    datetime_type994 = _t1401
                    _t1402 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type994))
                    _t1400 = _t1402
                else
                    if prediction986 == 6
                        _t1404 = parse_date_type(parser)
                        date_type993 = _t1404
                        _t1405 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type993))
                        _t1403 = _t1405
                    else
                        if prediction986 == 5
                            _t1407 = parse_int128_type(parser)
                            int128_type992 = _t1407
                            _t1408 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type992))
                            _t1406 = _t1408
                        else
                            if prediction986 == 4
                                _t1410 = parse_uint128_type(parser)
                                uint128_type991 = _t1410
                                _t1411 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type991))
                                _t1409 = _t1411
                            else
                                if prediction986 == 3
                                    _t1413 = parse_float_type(parser)
                                    float_type990 = _t1413
                                    _t1414 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type990))
                                    _t1412 = _t1414
                                else
                                    if prediction986 == 2
                                        _t1416 = parse_int_type(parser)
                                        int_type989 = _t1416
                                        _t1417 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type989))
                                        _t1415 = _t1417
                                    else
                                        if prediction986 == 1
                                            _t1419 = parse_string_type(parser)
                                            string_type988 = _t1419
                                            _t1420 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type988))
                                            _t1418 = _t1420
                                        else
                                            if prediction986 == 0
                                                _t1422 = parse_unspecified_type(parser)
                                                unspecified_type987 = _t1422
                                                _t1423 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type987))
                                                _t1421 = _t1423
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t1418 = _t1421
                                        end
                                        _t1415 = _t1418
                                    end
                                    _t1412 = _t1415
                                end
                                _t1409 = _t1412
                            end
                            _t1406 = _t1409
                        end
                        _t1403 = _t1406
                    end
                    _t1400 = _t1403
                end
                _t1397 = _t1400
            end
            _t1394 = _t1397
        end
        _t1391 = _t1394
    end
    return _t1391
end

function parse_unspecified_type(parser::Parser)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t1424 = Proto.UnspecifiedType()
    return _t1424
end

function parse_string_type(parser::Parser)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t1425 = Proto.StringType()
    return _t1425
end

function parse_int_type(parser::Parser)::Proto.IntType
    consume_literal!(parser, "INT")
    _t1426 = Proto.IntType()
    return _t1426
end

function parse_float_type(parser::Parser)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t1427 = Proto.FloatType()
    return _t1427
end

function parse_uint128_type(parser::Parser)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t1428 = Proto.UInt128Type()
    return _t1428
end

function parse_int128_type(parser::Parser)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t1429 = Proto.Int128Type()
    return _t1429
end

function parse_date_type(parser::Parser)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t1430 = Proto.DateType()
    return _t1430
end

function parse_datetime_type(parser::Parser)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t1431 = Proto.DateTimeType()
    return _t1431
end

function parse_missing_type(parser::Parser)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t1432 = Proto.MissingType()
    return _t1432
end

function parse_decimal_type(parser::Parser)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int998 = consume_terminal!(parser, "INT")
    int_3999 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1433 = Proto.DecimalType(precision=Int32(int998), scale=Int32(int_3999))
    return _t1433
end

function parse_boolean_type(parser::Parser)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t1434 = Proto.BooleanType()
    return _t1434
end

function parse_value_bindings(parser::Parser)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs1000 = Proto.Binding[]
    cond1001 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1001
        _t1435 = parse_binding(parser)
        item1002 = _t1435
        push!(xs1000, item1002)
        cond1001 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings1003 = xs1000
    return bindings1003
end

function parse_formula(parser::Parser)::Proto.Formula
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1437 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1438 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1439 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1440 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1441 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1442 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1443 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1444 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1445 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1446 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1447 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1448 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1449 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1450 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1451 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1452 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1453 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1454 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1455 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1456 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1457 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1458 = 10
                                                                                            else
                                                                                                _t1458 = -1
                                                                                            end
                                                                                            _t1457 = _t1458
                                                                                        end
                                                                                        _t1456 = _t1457
                                                                                    end
                                                                                    _t1455 = _t1456
                                                                                end
                                                                                _t1454 = _t1455
                                                                            end
                                                                            _t1453 = _t1454
                                                                        end
                                                                        _t1452 = _t1453
                                                                    end
                                                                    _t1451 = _t1452
                                                                end
                                                                _t1450 = _t1451
                                                            end
                                                            _t1449 = _t1450
                                                        end
                                                        _t1448 = _t1449
                                                    end
                                                    _t1447 = _t1448
                                                end
                                                _t1446 = _t1447
                                            end
                                            _t1445 = _t1446
                                        end
                                        _t1444 = _t1445
                                    end
                                    _t1443 = _t1444
                                end
                                _t1442 = _t1443
                            end
                            _t1441 = _t1442
                        end
                        _t1440 = _t1441
                    end
                    _t1439 = _t1440
                end
                _t1438 = _t1439
            end
            _t1437 = _t1438
        end
        _t1436 = _t1437
    else
        _t1436 = -1
    end
    prediction1004 = _t1436
    if prediction1004 == 12
        _t1460 = parse_cast(parser)
        cast1017 = _t1460
        _t1461 = Proto.Formula(formula_type=OneOf(:cast, cast1017))
        _t1459 = _t1461
    else
        if prediction1004 == 11
            _t1463 = parse_rel_atom(parser)
            rel_atom1016 = _t1463
            _t1464 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom1016))
            _t1462 = _t1464
        else
            if prediction1004 == 10
                _t1466 = parse_primitive(parser)
                primitive1015 = _t1466
                _t1467 = Proto.Formula(formula_type=OneOf(:primitive, primitive1015))
                _t1465 = _t1467
            else
                if prediction1004 == 9
                    _t1469 = parse_pragma(parser)
                    pragma1014 = _t1469
                    _t1470 = Proto.Formula(formula_type=OneOf(:pragma, pragma1014))
                    _t1468 = _t1470
                else
                    if prediction1004 == 8
                        _t1472 = parse_atom(parser)
                        atom1013 = _t1472
                        _t1473 = Proto.Formula(formula_type=OneOf(:atom, atom1013))
                        _t1471 = _t1473
                    else
                        if prediction1004 == 7
                            _t1475 = parse_ffi(parser)
                            ffi1012 = _t1475
                            _t1476 = Proto.Formula(formula_type=OneOf(:ffi, ffi1012))
                            _t1474 = _t1476
                        else
                            if prediction1004 == 6
                                _t1478 = parse_not(parser)
                                not1011 = _t1478
                                _t1479 = Proto.Formula(formula_type=OneOf(:not, not1011))
                                _t1477 = _t1479
                            else
                                if prediction1004 == 5
                                    _t1481 = parse_disjunction(parser)
                                    disjunction1010 = _t1481
                                    _t1482 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction1010))
                                    _t1480 = _t1482
                                else
                                    if prediction1004 == 4
                                        _t1484 = parse_conjunction(parser)
                                        conjunction1009 = _t1484
                                        _t1485 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction1009))
                                        _t1483 = _t1485
                                    else
                                        if prediction1004 == 3
                                            _t1487 = parse_reduce(parser)
                                            reduce1008 = _t1487
                                            _t1488 = Proto.Formula(formula_type=OneOf(:reduce, reduce1008))
                                            _t1486 = _t1488
                                        else
                                            if prediction1004 == 2
                                                _t1490 = parse_exists(parser)
                                                exists1007 = _t1490
                                                _t1491 = Proto.Formula(formula_type=OneOf(:exists, exists1007))
                                                _t1489 = _t1491
                                            else
                                                if prediction1004 == 1
                                                    _t1493 = parse_false(parser)
                                                    false1006 = _t1493
                                                    _t1494 = Proto.Formula(formula_type=OneOf(:disjunction, false1006))
                                                    _t1492 = _t1494
                                                else
                                                    if prediction1004 == 0
                                                        _t1496 = parse_true(parser)
                                                        true1005 = _t1496
                                                        _t1497 = Proto.Formula(formula_type=OneOf(:conjunction, true1005))
                                                        _t1495 = _t1497
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1492 = _t1495
                                                end
                                                _t1489 = _t1492
                                            end
                                            _t1486 = _t1489
                                        end
                                        _t1483 = _t1486
                                    end
                                    _t1480 = _t1483
                                end
                                _t1477 = _t1480
                            end
                            _t1474 = _t1477
                        end
                        _t1471 = _t1474
                    end
                    _t1468 = _t1471
                end
                _t1465 = _t1468
            end
            _t1462 = _t1465
        end
        _t1459 = _t1462
    end
    return _t1459
end

function parse_true(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1498 = Proto.Conjunction(args=Proto.Formula[])
    return _t1498
end

function parse_false(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1499 = Proto.Disjunction(args=Proto.Formula[])
    return _t1499
end

function parse_exists(parser::Parser)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1500 = parse_bindings(parser)
    bindings1018 = _t1500
    _t1501 = parse_formula(parser)
    formula1019 = _t1501
    consume_literal!(parser, ")")
    _t1502 = Proto.Abstraction(vars=vcat(bindings1018[1], !isnothing(bindings1018[2]) ? bindings1018[2] : []), value=formula1019)
    _t1503 = Proto.Exists(body=_t1502)
    return _t1503
end

function parse_reduce(parser::Parser)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1504 = parse_abstraction(parser)
    abstraction1020 = _t1504
    _t1505 = parse_abstraction(parser)
    abstraction_31021 = _t1505
    _t1506 = parse_terms(parser)
    terms1022 = _t1506
    consume_literal!(parser, ")")
    _t1507 = Proto.Reduce(op=abstraction1020, body=abstraction_31021, terms=terms1022)
    return _t1507
end

function parse_terms(parser::Parser)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs1023 = Proto.Term[]
    cond1024 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1024
        _t1508 = parse_term(parser)
        item1025 = _t1508
        push!(xs1023, item1025)
        cond1024 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms1026 = xs1023
    consume_literal!(parser, ")")
    return terms1026
end

function parse_term(parser::Parser)::Proto.Term
    if match_lookahead_literal(parser, "true", 0)
        _t1509 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1510 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1511 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1512 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1513 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1514 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1515 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1516 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1517 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t1518 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t1519 = 1
                                            else
                                                _t1519 = -1
                                            end
                                            _t1518 = _t1519
                                        end
                                        _t1517 = _t1518
                                    end
                                    _t1516 = _t1517
                                end
                                _t1515 = _t1516
                            end
                            _t1514 = _t1515
                        end
                        _t1513 = _t1514
                    end
                    _t1512 = _t1513
                end
                _t1511 = _t1512
            end
            _t1510 = _t1511
        end
        _t1509 = _t1510
    end
    prediction1027 = _t1509
    if prediction1027 == 1
        _t1521 = parse_constant(parser)
        constant1029 = _t1521
        _t1522 = Proto.Term(term_type=OneOf(:constant, constant1029))
        _t1520 = _t1522
    else
        if prediction1027 == 0
            _t1524 = parse_var(parser)
            var1028 = _t1524
            _t1525 = Proto.Term(term_type=OneOf(:var, var1028))
            _t1523 = _t1525
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1520 = _t1523
    end
    return _t1520
end

function parse_var(parser::Parser)::Proto.Var
    symbol1030 = consume_terminal!(parser, "SYMBOL")
    _t1526 = Proto.Var(name=symbol1030)
    return _t1526
end

function parse_constant(parser::Parser)::Proto.Value
    _t1527 = parse_value(parser)
    value1031 = _t1527
    return value1031
end

function parse_conjunction(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs1032 = Proto.Formula[]
    cond1033 = match_lookahead_literal(parser, "(", 0)
    while cond1033
        _t1528 = parse_formula(parser)
        item1034 = _t1528
        push!(xs1032, item1034)
        cond1033 = match_lookahead_literal(parser, "(", 0)
    end
    formulas1035 = xs1032
    consume_literal!(parser, ")")
    _t1529 = Proto.Conjunction(args=formulas1035)
    return _t1529
end

function parse_disjunction(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs1036 = Proto.Formula[]
    cond1037 = match_lookahead_literal(parser, "(", 0)
    while cond1037
        _t1530 = parse_formula(parser)
        item1038 = _t1530
        push!(xs1036, item1038)
        cond1037 = match_lookahead_literal(parser, "(", 0)
    end
    formulas1039 = xs1036
    consume_literal!(parser, ")")
    _t1531 = Proto.Disjunction(args=formulas1039)
    return _t1531
end

function parse_not(parser::Parser)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1532 = parse_formula(parser)
    formula1040 = _t1532
    consume_literal!(parser, ")")
    _t1533 = Proto.Not(arg=formula1040)
    return _t1533
end

function parse_ffi(parser::Parser)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1534 = parse_name(parser)
    name1041 = _t1534
    _t1535 = parse_ffi_args(parser)
    ffi_args1042 = _t1535
    _t1536 = parse_terms(parser)
    terms1043 = _t1536
    consume_literal!(parser, ")")
    _t1537 = Proto.FFI(name=name1041, args=ffi_args1042, terms=terms1043)
    return _t1537
end

function parse_name(parser::Parser)::String
    consume_literal!(parser, ":")
    symbol1044 = consume_terminal!(parser, "SYMBOL")
    return symbol1044
end

function parse_ffi_args(parser::Parser)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs1045 = Proto.Abstraction[]
    cond1046 = match_lookahead_literal(parser, "(", 0)
    while cond1046
        _t1538 = parse_abstraction(parser)
        item1047 = _t1538
        push!(xs1045, item1047)
        cond1046 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions1048 = xs1045
    consume_literal!(parser, ")")
    return abstractions1048
end

function parse_atom(parser::Parser)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1539 = parse_relation_id(parser)
    relation_id1049 = _t1539
    xs1050 = Proto.Term[]
    cond1051 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1051
        _t1540 = parse_term(parser)
        item1052 = _t1540
        push!(xs1050, item1052)
        cond1051 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms1053 = xs1050
    consume_literal!(parser, ")")
    _t1541 = Proto.Atom(name=relation_id1049, terms=terms1053)
    return _t1541
end

function parse_pragma(parser::Parser)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1542 = parse_name(parser)
    name1054 = _t1542
    xs1055 = Proto.Term[]
    cond1056 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1056
        _t1543 = parse_term(parser)
        item1057 = _t1543
        push!(xs1055, item1057)
        cond1056 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms1058 = xs1055
    consume_literal!(parser, ")")
    _t1544 = Proto.Pragma(name=name1054, terms=terms1058)
    return _t1544
end

function parse_primitive(parser::Parser)::Proto.Primitive
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1546 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1547 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1548 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1549 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1550 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1551 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1552 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1553 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1554 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1555 = 7
                                            else
                                                _t1555 = -1
                                            end
                                            _t1554 = _t1555
                                        end
                                        _t1553 = _t1554
                                    end
                                    _t1552 = _t1553
                                end
                                _t1551 = _t1552
                            end
                            _t1550 = _t1551
                        end
                        _t1549 = _t1550
                    end
                    _t1548 = _t1549
                end
                _t1547 = _t1548
            end
            _t1546 = _t1547
        end
        _t1545 = _t1546
    else
        _t1545 = -1
    end
    prediction1059 = _t1545
    if prediction1059 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1557 = parse_name(parser)
        name1069 = _t1557
        xs1070 = Proto.RelTerm[]
        cond1071 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond1071
            _t1558 = parse_rel_term(parser)
            item1072 = _t1558
            push!(xs1070, item1072)
            cond1071 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms1073 = xs1070
        consume_literal!(parser, ")")
        _t1559 = Proto.Primitive(name=name1069, terms=rel_terms1073)
        _t1556 = _t1559
    else
        if prediction1059 == 8
            _t1561 = parse_divide(parser)
            divide1068 = _t1561
            _t1560 = divide1068
        else
            if prediction1059 == 7
                _t1563 = parse_multiply(parser)
                multiply1067 = _t1563
                _t1562 = multiply1067
            else
                if prediction1059 == 6
                    _t1565 = parse_minus(parser)
                    minus1066 = _t1565
                    _t1564 = minus1066
                else
                    if prediction1059 == 5
                        _t1567 = parse_add(parser)
                        add1065 = _t1567
                        _t1566 = add1065
                    else
                        if prediction1059 == 4
                            _t1569 = parse_gt_eq(parser)
                            gt_eq1064 = _t1569
                            _t1568 = gt_eq1064
                        else
                            if prediction1059 == 3
                                _t1571 = parse_gt(parser)
                                gt1063 = _t1571
                                _t1570 = gt1063
                            else
                                if prediction1059 == 2
                                    _t1573 = parse_lt_eq(parser)
                                    lt_eq1062 = _t1573
                                    _t1572 = lt_eq1062
                                else
                                    if prediction1059 == 1
                                        _t1575 = parse_lt(parser)
                                        lt1061 = _t1575
                                        _t1574 = lt1061
                                    else
                                        if prediction1059 == 0
                                            _t1577 = parse_eq(parser)
                                            eq1060 = _t1577
                                            _t1576 = eq1060
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1574 = _t1576
                                    end
                                    _t1572 = _t1574
                                end
                                _t1570 = _t1572
                            end
                            _t1568 = _t1570
                        end
                        _t1566 = _t1568
                    end
                    _t1564 = _t1566
                end
                _t1562 = _t1564
            end
            _t1560 = _t1562
        end
        _t1556 = _t1560
    end
    return _t1556
end

function parse_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1578 = parse_term(parser)
    term1074 = _t1578
    _t1579 = parse_term(parser)
    term_31075 = _t1579
    consume_literal!(parser, ")")
    _t1580 = Proto.RelTerm(rel_term_type=OneOf(:term, term1074))
    _t1581 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31075))
    _t1582 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1580, _t1581])
    return _t1582
end

function parse_lt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1583 = parse_term(parser)
    term1076 = _t1583
    _t1584 = parse_term(parser)
    term_31077 = _t1584
    consume_literal!(parser, ")")
    _t1585 = Proto.RelTerm(rel_term_type=OneOf(:term, term1076))
    _t1586 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31077))
    _t1587 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1585, _t1586])
    return _t1587
end

function parse_lt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1588 = parse_term(parser)
    term1078 = _t1588
    _t1589 = parse_term(parser)
    term_31079 = _t1589
    consume_literal!(parser, ")")
    _t1590 = Proto.RelTerm(rel_term_type=OneOf(:term, term1078))
    _t1591 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31079))
    _t1592 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1590, _t1591])
    return _t1592
end

function parse_gt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1593 = parse_term(parser)
    term1080 = _t1593
    _t1594 = parse_term(parser)
    term_31081 = _t1594
    consume_literal!(parser, ")")
    _t1595 = Proto.RelTerm(rel_term_type=OneOf(:term, term1080))
    _t1596 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31081))
    _t1597 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1595, _t1596])
    return _t1597
end

function parse_gt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1598 = parse_term(parser)
    term1082 = _t1598
    _t1599 = parse_term(parser)
    term_31083 = _t1599
    consume_literal!(parser, ")")
    _t1600 = Proto.RelTerm(rel_term_type=OneOf(:term, term1082))
    _t1601 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31083))
    _t1602 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1600, _t1601])
    return _t1602
end

function parse_add(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1603 = parse_term(parser)
    term1084 = _t1603
    _t1604 = parse_term(parser)
    term_31085 = _t1604
    _t1605 = parse_term(parser)
    term_41086 = _t1605
    consume_literal!(parser, ")")
    _t1606 = Proto.RelTerm(rel_term_type=OneOf(:term, term1084))
    _t1607 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31085))
    _t1608 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41086))
    _t1609 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1606, _t1607, _t1608])
    return _t1609
end

function parse_minus(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1610 = parse_term(parser)
    term1087 = _t1610
    _t1611 = parse_term(parser)
    term_31088 = _t1611
    _t1612 = parse_term(parser)
    term_41089 = _t1612
    consume_literal!(parser, ")")
    _t1613 = Proto.RelTerm(rel_term_type=OneOf(:term, term1087))
    _t1614 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31088))
    _t1615 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41089))
    _t1616 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1613, _t1614, _t1615])
    return _t1616
end

function parse_multiply(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1617 = parse_term(parser)
    term1090 = _t1617
    _t1618 = parse_term(parser)
    term_31091 = _t1618
    _t1619 = parse_term(parser)
    term_41092 = _t1619
    consume_literal!(parser, ")")
    _t1620 = Proto.RelTerm(rel_term_type=OneOf(:term, term1090))
    _t1621 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31091))
    _t1622 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41092))
    _t1623 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1620, _t1621, _t1622])
    return _t1623
end

function parse_divide(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1624 = parse_term(parser)
    term1093 = _t1624
    _t1625 = parse_term(parser)
    term_31094 = _t1625
    _t1626 = parse_term(parser)
    term_41095 = _t1626
    consume_literal!(parser, ")")
    _t1627 = Proto.RelTerm(rel_term_type=OneOf(:term, term1093))
    _t1628 = Proto.RelTerm(rel_term_type=OneOf(:term, term_31094))
    _t1629 = Proto.RelTerm(rel_term_type=OneOf(:term, term_41095))
    _t1630 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1627, _t1628, _t1629])
    return _t1630
end

function parse_rel_term(parser::Parser)::Proto.RelTerm
    if match_lookahead_literal(parser, "true", 0)
        _t1631 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1632 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1633 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1634 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1635 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1636 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1637 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1638 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1639 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1640 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1641 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1642 = 1
                                                else
                                                    _t1642 = -1
                                                end
                                                _t1641 = _t1642
                                            end
                                            _t1640 = _t1641
                                        end
                                        _t1639 = _t1640
                                    end
                                    _t1638 = _t1639
                                end
                                _t1637 = _t1638
                            end
                            _t1636 = _t1637
                        end
                        _t1635 = _t1636
                    end
                    _t1634 = _t1635
                end
                _t1633 = _t1634
            end
            _t1632 = _t1633
        end
        _t1631 = _t1632
    end
    prediction1096 = _t1631
    if prediction1096 == 1
        _t1644 = parse_term(parser)
        term1098 = _t1644
        _t1645 = Proto.RelTerm(rel_term_type=OneOf(:term, term1098))
        _t1643 = _t1645
    else
        if prediction1096 == 0
            _t1647 = parse_specialized_value(parser)
            specialized_value1097 = _t1647
            _t1648 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value1097))
            _t1646 = _t1648
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1643 = _t1646
    end
    return _t1643
end

function parse_specialized_value(parser::Parser)::Proto.Value
    consume_literal!(parser, "#")
    _t1649 = parse_value(parser)
    value1099 = _t1649
    return value1099
end

function parse_rel_atom(parser::Parser)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1650 = parse_name(parser)
    name1100 = _t1650
    xs1101 = Proto.RelTerm[]
    cond1102 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1102
        _t1651 = parse_rel_term(parser)
        item1103 = _t1651
        push!(xs1101, item1103)
        cond1102 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms1104 = xs1101
    consume_literal!(parser, ")")
    _t1652 = Proto.RelAtom(name=name1100, terms=rel_terms1104)
    return _t1652
end

function parse_cast(parser::Parser)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1653 = parse_term(parser)
    term1105 = _t1653
    _t1654 = parse_term(parser)
    term_31106 = _t1654
    consume_literal!(parser, ")")
    _t1655 = Proto.Cast(input=term1105, result=term_31106)
    return _t1655
end

function parse_attrs(parser::Parser)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs1107 = Proto.Attribute[]
    cond1108 = match_lookahead_literal(parser, "(", 0)
    while cond1108
        _t1656 = parse_attribute(parser)
        item1109 = _t1656
        push!(xs1107, item1109)
        cond1108 = match_lookahead_literal(parser, "(", 0)
    end
    attributes1110 = xs1107
    consume_literal!(parser, ")")
    return attributes1110
end

function parse_attribute(parser::Parser)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1657 = parse_name(parser)
    name1111 = _t1657
    xs1112 = Proto.Value[]
    cond1113 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1113
        _t1658 = parse_value(parser)
        item1114 = _t1658
        push!(xs1112, item1114)
        cond1113 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values1115 = xs1112
    consume_literal!(parser, ")")
    _t1659 = Proto.Attribute(name=name1111, args=values1115)
    return _t1659
end

function parse_algorithm(parser::Parser)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs1116 = Proto.RelationId[]
    cond1117 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1117
        _t1660 = parse_relation_id(parser)
        item1118 = _t1660
        push!(xs1116, item1118)
        cond1117 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1119 = xs1116
    _t1661 = parse_script(parser)
    script1120 = _t1661
    consume_literal!(parser, ")")
    _t1662 = Proto.Algorithm(var"#global"=relation_ids1119, body=script1120)
    return _t1662
end

function parse_script(parser::Parser)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs1121 = Proto.Construct[]
    cond1122 = match_lookahead_literal(parser, "(", 0)
    while cond1122
        _t1663 = parse_construct(parser)
        item1123 = _t1663
        push!(xs1121, item1123)
        cond1122 = match_lookahead_literal(parser, "(", 0)
    end
    constructs1124 = xs1121
    consume_literal!(parser, ")")
    _t1664 = Proto.Script(constructs=constructs1124)
    return _t1664
end

function parse_construct(parser::Parser)::Proto.Construct
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1666 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1667 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1668 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1669 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1670 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1671 = 1
                            else
                                _t1671 = -1
                            end
                            _t1670 = _t1671
                        end
                        _t1669 = _t1670
                    end
                    _t1668 = _t1669
                end
                _t1667 = _t1668
            end
            _t1666 = _t1667
        end
        _t1665 = _t1666
    else
        _t1665 = -1
    end
    prediction1125 = _t1665
    if prediction1125 == 1
        _t1673 = parse_instruction(parser)
        instruction1127 = _t1673
        _t1674 = Proto.Construct(construct_type=OneOf(:instruction, instruction1127))
        _t1672 = _t1674
    else
        if prediction1125 == 0
            _t1676 = parse_loop(parser)
            loop1126 = _t1676
            _t1677 = Proto.Construct(construct_type=OneOf(:loop, loop1126))
            _t1675 = _t1677
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1672 = _t1675
    end
    return _t1672
end

function parse_loop(parser::Parser)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1678 = parse_init(parser)
    init1128 = _t1678
    _t1679 = parse_script(parser)
    script1129 = _t1679
    consume_literal!(parser, ")")
    _t1680 = Proto.Loop(init=init1128, body=script1129)
    return _t1680
end

function parse_init(parser::Parser)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs1130 = Proto.Instruction[]
    cond1131 = match_lookahead_literal(parser, "(", 0)
    while cond1131
        _t1681 = parse_instruction(parser)
        item1132 = _t1681
        push!(xs1130, item1132)
        cond1131 = match_lookahead_literal(parser, "(", 0)
    end
    instructions1133 = xs1130
    consume_literal!(parser, ")")
    return instructions1133
end

function parse_instruction(parser::Parser)::Proto.Instruction
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1683 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1684 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1685 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1686 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1687 = 0
                        else
                            _t1687 = -1
                        end
                        _t1686 = _t1687
                    end
                    _t1685 = _t1686
                end
                _t1684 = _t1685
            end
            _t1683 = _t1684
        end
        _t1682 = _t1683
    else
        _t1682 = -1
    end
    prediction1134 = _t1682
    if prediction1134 == 4
        _t1689 = parse_monus_def(parser)
        monus_def1139 = _t1689
        _t1690 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def1139))
        _t1688 = _t1690
    else
        if prediction1134 == 3
            _t1692 = parse_monoid_def(parser)
            monoid_def1138 = _t1692
            _t1693 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def1138))
            _t1691 = _t1693
        else
            if prediction1134 == 2
                _t1695 = parse_break(parser)
                break1137 = _t1695
                _t1696 = Proto.Instruction(instr_type=OneOf(:var"#break", break1137))
                _t1694 = _t1696
            else
                if prediction1134 == 1
                    _t1698 = parse_upsert(parser)
                    upsert1136 = _t1698
                    _t1699 = Proto.Instruction(instr_type=OneOf(:upsert, upsert1136))
                    _t1697 = _t1699
                else
                    if prediction1134 == 0
                        _t1701 = parse_assign(parser)
                        assign1135 = _t1701
                        _t1702 = Proto.Instruction(instr_type=OneOf(:assign, assign1135))
                        _t1700 = _t1702
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1697 = _t1700
                end
                _t1694 = _t1697
            end
            _t1691 = _t1694
        end
        _t1688 = _t1691
    end
    return _t1688
end

function parse_assign(parser::Parser)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1703 = parse_relation_id(parser)
    relation_id1140 = _t1703
    _t1704 = parse_abstraction(parser)
    abstraction1141 = _t1704
    if match_lookahead_literal(parser, "(", 0)
        _t1706 = parse_attrs(parser)
        _t1705 = _t1706
    else
        _t1705 = nothing
    end
    attrs1142 = _t1705
    consume_literal!(parser, ")")
    _t1707 = Proto.Assign(name=relation_id1140, body=abstraction1141, attrs=(!isnothing(attrs1142) ? attrs1142 : Proto.Attribute[]))
    return _t1707
end

function parse_upsert(parser::Parser)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1708 = parse_relation_id(parser)
    relation_id1143 = _t1708
    _t1709 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1144 = _t1709
    if match_lookahead_literal(parser, "(", 0)
        _t1711 = parse_attrs(parser)
        _t1710 = _t1711
    else
        _t1710 = nothing
    end
    attrs1145 = _t1710
    consume_literal!(parser, ")")
    _t1712 = Proto.Upsert(name=relation_id1143, body=abstraction_with_arity1144[1], attrs=(!isnothing(attrs1145) ? attrs1145 : Proto.Attribute[]), value_arity=abstraction_with_arity1144[2])
    return _t1712
end

function parse_abstraction_with_arity(parser::Parser)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1713 = parse_bindings(parser)
    bindings1146 = _t1713
    _t1714 = parse_formula(parser)
    formula1147 = _t1714
    consume_literal!(parser, ")")
    _t1715 = Proto.Abstraction(vars=vcat(bindings1146[1], !isnothing(bindings1146[2]) ? bindings1146[2] : []), value=formula1147)
    return (_t1715, length(bindings1146[2]),)
end

function parse_break(parser::Parser)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1716 = parse_relation_id(parser)
    relation_id1148 = _t1716
    _t1717 = parse_abstraction(parser)
    abstraction1149 = _t1717
    if match_lookahead_literal(parser, "(", 0)
        _t1719 = parse_attrs(parser)
        _t1718 = _t1719
    else
        _t1718 = nothing
    end
    attrs1150 = _t1718
    consume_literal!(parser, ")")
    _t1720 = Proto.Break(name=relation_id1148, body=abstraction1149, attrs=(!isnothing(attrs1150) ? attrs1150 : Proto.Attribute[]))
    return _t1720
end

function parse_monoid_def(parser::Parser)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1721 = parse_monoid(parser)
    monoid1151 = _t1721
    _t1722 = parse_relation_id(parser)
    relation_id1152 = _t1722
    _t1723 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1153 = _t1723
    if match_lookahead_literal(parser, "(", 0)
        _t1725 = parse_attrs(parser)
        _t1724 = _t1725
    else
        _t1724 = nothing
    end
    attrs1154 = _t1724
    consume_literal!(parser, ")")
    _t1726 = Proto.MonoidDef(monoid=monoid1151, name=relation_id1152, body=abstraction_with_arity1153[1], attrs=(!isnothing(attrs1154) ? attrs1154 : Proto.Attribute[]), value_arity=abstraction_with_arity1153[2])
    return _t1726
end

function parse_monoid(parser::Parser)::Proto.Monoid
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1728 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1729 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1730 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1731 = 2
                    else
                        _t1731 = -1
                    end
                    _t1730 = _t1731
                end
                _t1729 = _t1730
            end
            _t1728 = _t1729
        end
        _t1727 = _t1728
    else
        _t1727 = -1
    end
    prediction1155 = _t1727
    if prediction1155 == 3
        _t1733 = parse_sum_monoid(parser)
        sum_monoid1159 = _t1733
        _t1734 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid1159))
        _t1732 = _t1734
    else
        if prediction1155 == 2
            _t1736 = parse_max_monoid(parser)
            max_monoid1158 = _t1736
            _t1737 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid1158))
            _t1735 = _t1737
        else
            if prediction1155 == 1
                _t1739 = parse_min_monoid(parser)
                min_monoid1157 = _t1739
                _t1740 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid1157))
                _t1738 = _t1740
            else
                if prediction1155 == 0
                    _t1742 = parse_or_monoid(parser)
                    or_monoid1156 = _t1742
                    _t1743 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid1156))
                    _t1741 = _t1743
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1738 = _t1741
            end
            _t1735 = _t1738
        end
        _t1732 = _t1735
    end
    return _t1732
end

function parse_or_monoid(parser::Parser)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1744 = Proto.OrMonoid()
    return _t1744
end

function parse_min_monoid(parser::Parser)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1745 = parse_type(parser)
    type1160 = _t1745
    consume_literal!(parser, ")")
    _t1746 = Proto.MinMonoid(var"#type"=type1160)
    return _t1746
end

function parse_max_monoid(parser::Parser)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1747 = parse_type(parser)
    type1161 = _t1747
    consume_literal!(parser, ")")
    _t1748 = Proto.MaxMonoid(var"#type"=type1161)
    return _t1748
end

function parse_sum_monoid(parser::Parser)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1749 = parse_type(parser)
    type1162 = _t1749
    consume_literal!(parser, ")")
    _t1750 = Proto.SumMonoid(var"#type"=type1162)
    return _t1750
end

function parse_monus_def(parser::Parser)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1751 = parse_monoid(parser)
    monoid1163 = _t1751
    _t1752 = parse_relation_id(parser)
    relation_id1164 = _t1752
    _t1753 = parse_abstraction_with_arity(parser)
    abstraction_with_arity1165 = _t1753
    if match_lookahead_literal(parser, "(", 0)
        _t1755 = parse_attrs(parser)
        _t1754 = _t1755
    else
        _t1754 = nothing
    end
    attrs1166 = _t1754
    consume_literal!(parser, ")")
    _t1756 = Proto.MonusDef(monoid=monoid1163, name=relation_id1164, body=abstraction_with_arity1165[1], attrs=(!isnothing(attrs1166) ? attrs1166 : Proto.Attribute[]), value_arity=abstraction_with_arity1165[2])
    return _t1756
end

function parse_constraint(parser::Parser)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1757 = parse_relation_id(parser)
    relation_id1167 = _t1757
    _t1758 = parse_abstraction(parser)
    abstraction1168 = _t1758
    _t1759 = parse_functional_dependency_keys(parser)
    functional_dependency_keys1169 = _t1759
    _t1760 = parse_functional_dependency_values(parser)
    functional_dependency_values1170 = _t1760
    consume_literal!(parser, ")")
    _t1761 = Proto.FunctionalDependency(guard=abstraction1168, keys=functional_dependency_keys1169, values=functional_dependency_values1170)
    _t1762 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1761), name=relation_id1167)
    return _t1762
end

function parse_functional_dependency_keys(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1171 = Proto.Var[]
    cond1172 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1172
        _t1763 = parse_var(parser)
        item1173 = _t1763
        push!(xs1171, item1173)
        cond1172 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1174 = xs1171
    consume_literal!(parser, ")")
    return vars1174
end

function parse_functional_dependency_values(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1175 = Proto.Var[]
    cond1176 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1176
        _t1764 = parse_var(parser)
        item1177 = _t1764
        push!(xs1175, item1177)
        cond1176 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1178 = xs1175
    consume_literal!(parser, ")")
    return vars1178
end

function parse_data(parser::Parser)::Proto.Data
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1766 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1767 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1768 = 1
                else
                    _t1768 = -1
                end
                _t1767 = _t1768
            end
            _t1766 = _t1767
        end
        _t1765 = _t1766
    else
        _t1765 = -1
    end
    prediction1179 = _t1765
    if prediction1179 == 2
        _t1770 = parse_csv_data(parser)
        csv_data1182 = _t1770
        _t1771 = Proto.Data(data_type=OneOf(:csv_data, csv_data1182))
        _t1769 = _t1771
    else
        if prediction1179 == 1
            _t1773 = parse_betree_relation(parser)
            betree_relation1181 = _t1773
            _t1774 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1181))
            _t1772 = _t1774
        else
            if prediction1179 == 0
                _t1776 = parse_rel_edb(parser)
                rel_edb1180 = _t1776
                _t1777 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb1180))
                _t1775 = _t1777
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1772 = _t1775
        end
        _t1769 = _t1772
    end
    return _t1769
end

function parse_rel_edb(parser::Parser)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t1778 = parse_relation_id(parser)
    relation_id1183 = _t1778
    _t1779 = parse_rel_edb_path(parser)
    rel_edb_path1184 = _t1779
    _t1780 = parse_rel_edb_types(parser)
    rel_edb_types1185 = _t1780
    consume_literal!(parser, ")")
    _t1781 = Proto.RelEDB(target_id=relation_id1183, path=rel_edb_path1184, types=rel_edb_types1185)
    return _t1781
end

function parse_rel_edb_path(parser::Parser)::Vector{String}
    consume_literal!(parser, "[")
    xs1186 = String[]
    cond1187 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1187
        item1188 = consume_terminal!(parser, "STRING")
        push!(xs1186, item1188)
        cond1187 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1189 = xs1186
    consume_literal!(parser, "]")
    return strings1189
end

function parse_rel_edb_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1190 = Proto.var"#Type"[]
    cond1191 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1191
        _t1782 = parse_type(parser)
        item1192 = _t1782
        push!(xs1190, item1192)
        cond1191 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1193 = xs1190
    consume_literal!(parser, "]")
    return types1193
end

function parse_betree_relation(parser::Parser)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1783 = parse_relation_id(parser)
    relation_id1194 = _t1783
    _t1784 = parse_betree_info(parser)
    betree_info1195 = _t1784
    consume_literal!(parser, ")")
    _t1785 = Proto.BeTreeRelation(name=relation_id1194, relation_info=betree_info1195)
    return _t1785
end

function parse_betree_info(parser::Parser)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1786 = parse_betree_info_key_types(parser)
    betree_info_key_types1196 = _t1786
    _t1787 = parse_betree_info_value_types(parser)
    betree_info_value_types1197 = _t1787
    _t1788 = parse_config_dict(parser)
    config_dict1198 = _t1788
    consume_literal!(parser, ")")
    _t1789 = construct_betree_info(parser, betree_info_key_types1196, betree_info_value_types1197, config_dict1198)
    return _t1789
end

function parse_betree_info_key_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1199 = Proto.var"#Type"[]
    cond1200 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1200
        _t1790 = parse_type(parser)
        item1201 = _t1790
        push!(xs1199, item1201)
        cond1200 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1202 = xs1199
    consume_literal!(parser, ")")
    return types1202
end

function parse_betree_info_value_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1203 = Proto.var"#Type"[]
    cond1204 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1204
        _t1791 = parse_type(parser)
        item1205 = _t1791
        push!(xs1203, item1205)
        cond1204 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1206 = xs1203
    consume_literal!(parser, ")")
    return types1206
end

function parse_csv_data(parser::Parser)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1792 = parse_csvlocator(parser)
    csvlocator1207 = _t1792
    _t1793 = parse_csv_config(parser)
    csv_config1208 = _t1793
    _t1794 = parse_csv_columns(parser)
    csv_columns1209 = _t1794
    _t1795 = parse_csv_asof(parser)
    csv_asof1210 = _t1795
    consume_literal!(parser, ")")
    _t1796 = Proto.CSVData(locator=csvlocator1207, config=csv_config1208, columns=csv_columns1209, asof=csv_asof1210)
    return _t1796
end

function parse_csvlocator(parser::Parser)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1798 = parse_csv_locator_paths(parser)
        _t1797 = _t1798
    else
        _t1797 = nothing
    end
    csv_locator_paths1211 = _t1797
    if match_lookahead_literal(parser, "(", 0)
        _t1800 = parse_csv_locator_inline_data(parser)
        _t1799 = _t1800
    else
        _t1799 = nothing
    end
    csv_locator_inline_data1212 = _t1799
    consume_literal!(parser, ")")
    _t1801 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1211) ? csv_locator_paths1211 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1212) ? csv_locator_inline_data1212 : "")))
    return _t1801
end

function parse_csv_locator_paths(parser::Parser)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1213 = String[]
    cond1214 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1214
        item1215 = consume_terminal!(parser, "STRING")
        push!(xs1213, item1215)
        cond1214 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1216 = xs1213
    consume_literal!(parser, ")")
    return strings1216
end

function parse_csv_locator_inline_data(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1217 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1217
end

function parse_csv_config(parser::Parser)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1802 = parse_config_dict(parser)
    config_dict1218 = _t1802
    consume_literal!(parser, ")")
    _t1803 = construct_csv_config(parser, config_dict1218)
    return _t1803
end

function parse_csv_columns(parser::Parser)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1219 = Proto.CSVColumn[]
    cond1220 = match_lookahead_literal(parser, "(", 0)
    while cond1220
        _t1804 = parse_csv_column(parser)
        item1221 = _t1804
        push!(xs1219, item1221)
        cond1220 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns1222 = xs1219
    consume_literal!(parser, ")")
    return csv_columns1222
end

function parse_csv_column(parser::Parser)::Proto.CSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1223 = consume_terminal!(parser, "STRING")
    _t1805 = parse_relation_id(parser)
    relation_id1224 = _t1805
    consume_literal!(parser, "[")
    xs1225 = Proto.var"#Type"[]
    cond1226 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1226
        _t1806 = parse_type(parser)
        item1227 = _t1806
        push!(xs1225, item1227)
        cond1226 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1228 = xs1225
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1807 = Proto.CSVColumn(column_name=string1223, target_id=relation_id1224, types=types1228)
    return _t1807
end

function parse_csv_asof(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1229 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1229
end

function parse_undefine(parser::Parser)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1808 = parse_fragment_id(parser)
    fragment_id1230 = _t1808
    consume_literal!(parser, ")")
    _t1809 = Proto.Undefine(fragment_id=fragment_id1230)
    return _t1809
end

function parse_context(parser::Parser)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1231 = Proto.RelationId[]
    cond1232 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1232
        _t1810 = parse_relation_id(parser)
        item1233 = _t1810
        push!(xs1231, item1233)
        cond1232 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1234 = xs1231
    consume_literal!(parser, ")")
    _t1811 = Proto.Context(relations=relation_ids1234)
    return _t1811
end

function parse_epoch_reads(parser::Parser)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1235 = Proto.Read[]
    cond1236 = match_lookahead_literal(parser, "(", 0)
    while cond1236
        _t1812 = parse_read(parser)
        item1237 = _t1812
        push!(xs1235, item1237)
        cond1236 = match_lookahead_literal(parser, "(", 0)
    end
    reads1238 = xs1235
    consume_literal!(parser, ")")
    return reads1238
end

function parse_read(parser::Parser)::Proto.Read
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1814 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1815 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1816 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1817 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1818 = 3
                        else
                            _t1818 = -1
                        end
                        _t1817 = _t1818
                    end
                    _t1816 = _t1817
                end
                _t1815 = _t1816
            end
            _t1814 = _t1815
        end
        _t1813 = _t1814
    else
        _t1813 = -1
    end
    prediction1239 = _t1813
    if prediction1239 == 4
        _t1820 = parse_export(parser)
        export1244 = _t1820
        _t1821 = Proto.Read(read_type=OneOf(:var"#export", export1244))
        _t1819 = _t1821
    else
        if prediction1239 == 3
            _t1823 = parse_abort(parser)
            abort1243 = _t1823
            _t1824 = Proto.Read(read_type=OneOf(:abort, abort1243))
            _t1822 = _t1824
        else
            if prediction1239 == 2
                _t1826 = parse_what_if(parser)
                what_if1242 = _t1826
                _t1827 = Proto.Read(read_type=OneOf(:what_if, what_if1242))
                _t1825 = _t1827
            else
                if prediction1239 == 1
                    _t1829 = parse_output(parser)
                    output1241 = _t1829
                    _t1830 = Proto.Read(read_type=OneOf(:output, output1241))
                    _t1828 = _t1830
                else
                    if prediction1239 == 0
                        _t1832 = parse_demand(parser)
                        demand1240 = _t1832
                        _t1833 = Proto.Read(read_type=OneOf(:demand, demand1240))
                        _t1831 = _t1833
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1828 = _t1831
                end
                _t1825 = _t1828
            end
            _t1822 = _t1825
        end
        _t1819 = _t1822
    end
    return _t1819
end

function parse_demand(parser::Parser)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1834 = parse_relation_id(parser)
    relation_id1245 = _t1834
    consume_literal!(parser, ")")
    _t1835 = Proto.Demand(relation_id=relation_id1245)
    return _t1835
end

function parse_output(parser::Parser)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1836 = parse_name(parser)
    name1246 = _t1836
    _t1837 = parse_relation_id(parser)
    relation_id1247 = _t1837
    consume_literal!(parser, ")")
    _t1838 = Proto.Output(name=name1246, relation_id=relation_id1247)
    return _t1838
end

function parse_what_if(parser::Parser)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1839 = parse_name(parser)
    name1248 = _t1839
    _t1840 = parse_epoch(parser)
    epoch1249 = _t1840
    consume_literal!(parser, ")")
    _t1841 = Proto.WhatIf(branch=name1248, epoch=epoch1249)
    return _t1841
end

function parse_abort(parser::Parser)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1843 = parse_name(parser)
        _t1842 = _t1843
    else
        _t1842 = nothing
    end
    name1250 = _t1842
    _t1844 = parse_relation_id(parser)
    relation_id1251 = _t1844
    consume_literal!(parser, ")")
    _t1845 = Proto.Abort(name=(!isnothing(name1250) ? name1250 : "abort"), relation_id=relation_id1251)
    return _t1845
end

function parse_export(parser::Parser)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1846 = parse_export_csv_config(parser)
    export_csv_config1252 = _t1846
    consume_literal!(parser, ")")
    _t1847 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1252))
    return _t1847
end

function parse_export_csv_config(parser::Parser)::Proto.ExportCSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1848 = parse_export_csv_path(parser)
    export_csv_path1253 = _t1848
    _t1849 = parse_export_csv_columns(parser)
    export_csv_columns1254 = _t1849
    _t1850 = parse_config_dict(parser)
    config_dict1255 = _t1850
    consume_literal!(parser, ")")
    _t1851 = export_csv_config(parser, export_csv_path1253, export_csv_columns1254, config_dict1255)
    return _t1851
end

function parse_export_csv_path(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1256 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1256
end

function parse_export_csv_columns(parser::Parser)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1257 = Proto.ExportCSVColumn[]
    cond1258 = match_lookahead_literal(parser, "(", 0)
    while cond1258
        _t1852 = parse_export_csv_column(parser)
        item1259 = _t1852
        push!(xs1257, item1259)
        cond1258 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1260 = xs1257
    consume_literal!(parser, ")")
    return export_csv_columns1260
end

function parse_export_csv_column(parser::Parser)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1261 = consume_terminal!(parser, "STRING")
    _t1853 = parse_relation_id(parser)
    relation_id1262 = _t1853
    consume_literal!(parser, ")")
    _t1854 = Proto.ExportCSVColumn(column_name=string1261, column_data=relation_id1262)
    return _t1854
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
