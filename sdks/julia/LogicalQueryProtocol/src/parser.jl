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
        _t1298 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1299 = nothing
    end
    return default
end

function _extract_value_string(parser::Parser, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1300 = nothing
    end
    return default
end

function _extract_value_boolean(parser::Parser, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1301 = nothing
    end
    return default
end

function _extract_value_string_list(parser::Parser, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1302 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1303 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1304 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1305 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::Parser, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1306 = nothing
    end
    return nothing
end

function construct_csv_config(parser::Parser, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1307 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1307
    _t1308 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1308
    _t1309 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1309
    _t1310 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1310
    _t1311 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1311
    _t1312 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1312
    _t1313 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1313
    _t1314 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1314
    _t1315 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1315
    _t1316 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1316
    _t1317 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1317
    _t1318 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1318
end

function construct_betree_info(parser::Parser, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1319 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1319
    _t1320 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1320
    _t1321 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1321
    _t1322 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1322
    _t1323 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1323
    _t1324 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1324
    _t1325 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1325
    _t1326 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1326
    _t1327 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1327
    _t1328 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1328
    _t1329 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1329
end

function default_configure(parser::Parser)::Proto.Configure
    _t1330 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1330
    _t1331 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1331
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
    _t1332 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1332
    _t1333 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1333
    _t1334 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1334
end

function export_csv_config(parser::Parser, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1335 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1335
    _t1336 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1336
    _t1337 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1337
    _t1338 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1338
    _t1339 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1339
    _t1340 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1340
    _t1341 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1341
    _t1342 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1342
end

# --- Parse functions ---

function parse_transaction(parser::Parser)::Proto.Transaction
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t707 = parse_configure(parser)
        _t706 = _t707
    else
        _t706 = nothing
    end
    configure353 = _t706
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t709 = parse_sync(parser)
        _t708 = _t709
    else
        _t708 = nothing
    end
    sync354 = _t708
    xs355 = Proto.Epoch[]
    cond356 = match_lookahead_literal(parser, "(", 0)
    while cond356
        _t710 = parse_epoch(parser)
        item357 = _t710
        push!(xs355, item357)
        cond356 = match_lookahead_literal(parser, "(", 0)
    end
    epochs358 = xs355
    consume_literal!(parser, ")")
    _t711 = default_configure(parser)
    _t712 = Proto.Transaction(epochs=epochs358, configure=(!isnothing(configure353) ? configure353 : _t711), sync=sync354)
    return _t712
end

function parse_configure(parser::Parser)::Proto.Configure
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t713 = parse_config_dict(parser)
    config_dict359 = _t713
    consume_literal!(parser, ")")
    _t714 = construct_configure(parser, config_dict359)
    return _t714
end

function parse_config_dict(parser::Parser)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs360 = Tuple{String, Proto.Value}[]
    cond361 = match_lookahead_literal(parser, ":", 0)
    while cond361
        _t715 = parse_config_key_value(parser)
        item362 = _t715
        push!(xs360, item362)
        cond361 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values363 = xs360
    consume_literal!(parser, "}")
    return config_key_values363
end

function parse_config_key_value(parser::Parser)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol364 = consume_terminal!(parser, "SYMBOL")
    _t716 = parse_value(parser)
    value365 = _t716
    return (symbol364, value365,)
end

function parse_value(parser::Parser)::Proto.Value
    if match_lookahead_literal(parser, "true", 0)
        _t717 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t718 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t719 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t721 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t722 = 0
                        else
                            _t722 = -1
                        end
                        _t721 = _t722
                    end
                    _t720 = _t721
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t723 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t724 = 2
                        else
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t725 = 6
                            else
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t726 = 3
                                else
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t727 = 4
                                    else
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t728 = 7
                                        else
                                            _t728 = -1
                                        end
                                        _t727 = _t728
                                    end
                                    _t726 = _t727
                                end
                                _t725 = _t726
                            end
                            _t724 = _t725
                        end
                        _t723 = _t724
                    end
                    _t720 = _t723
                end
                _t719 = _t720
            end
            _t718 = _t719
        end
        _t717 = _t718
    end
    prediction366 = _t717
    if prediction366 == 9
        _t730 = parse_boolean_value(parser)
        boolean_value375 = _t730
        _t731 = Proto.Value(value=OneOf(:boolean_value, boolean_value375))
        _t729 = _t731
    else
        if prediction366 == 8
            consume_literal!(parser, "missing")
            _t733 = Proto.MissingValue()
            _t734 = Proto.Value(value=OneOf(:missing_value, _t733))
            _t732 = _t734
        else
            if prediction366 == 7
                decimal374 = consume_terminal!(parser, "DECIMAL")
                _t736 = Proto.Value(value=OneOf(:decimal_value, decimal374))
                _t735 = _t736
            else
                if prediction366 == 6
                    int128373 = consume_terminal!(parser, "INT128")
                    _t738 = Proto.Value(value=OneOf(:int128_value, int128373))
                    _t737 = _t738
                else
                    if prediction366 == 5
                        uint128372 = consume_terminal!(parser, "UINT128")
                        _t740 = Proto.Value(value=OneOf(:uint128_value, uint128372))
                        _t739 = _t740
                    else
                        if prediction366 == 4
                            float371 = consume_terminal!(parser, "FLOAT")
                            _t742 = Proto.Value(value=OneOf(:float_value, float371))
                            _t741 = _t742
                        else
                            if prediction366 == 3
                                int370 = consume_terminal!(parser, "INT")
                                _t744 = Proto.Value(value=OneOf(:int_value, int370))
                                _t743 = _t744
                            else
                                if prediction366 == 2
                                    string369 = consume_terminal!(parser, "STRING")
                                    _t746 = Proto.Value(value=OneOf(:string_value, string369))
                                    _t745 = _t746
                                else
                                    if prediction366 == 1
                                        _t748 = parse_datetime(parser)
                                        datetime368 = _t748
                                        _t749 = Proto.Value(value=OneOf(:datetime_value, datetime368))
                                        _t747 = _t749
                                    else
                                        if prediction366 == 0
                                            _t751 = parse_date(parser)
                                            date367 = _t751
                                            _t752 = Proto.Value(value=OneOf(:date_value, date367))
                                            _t750 = _t752
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t747 = _t750
                                    end
                                    _t745 = _t747
                                end
                                _t743 = _t745
                            end
                            _t741 = _t743
                        end
                        _t739 = _t741
                    end
                    _t737 = _t739
                end
                _t735 = _t737
            end
            _t732 = _t735
        end
        _t729 = _t732
    end
    return _t729
end

function parse_date(parser::Parser)::Proto.DateValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int376 = consume_terminal!(parser, "INT")
    int_3377 = consume_terminal!(parser, "INT")
    int_4378 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t753 = Proto.DateValue(year=Int32(int376), month=Int32(int_3377), day=Int32(int_4378))
    return _t753
end

function parse_datetime(parser::Parser)::Proto.DateTimeValue
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int379 = consume_terminal!(parser, "INT")
    int_3380 = consume_terminal!(parser, "INT")
    int_4381 = consume_terminal!(parser, "INT")
    int_5382 = consume_terminal!(parser, "INT")
    int_6383 = consume_terminal!(parser, "INT")
    int_7384 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t754 = consume_terminal!(parser, "INT")
    else
        _t754 = nothing
    end
    int_8385 = _t754
    consume_literal!(parser, ")")
    _t755 = Proto.DateTimeValue(year=Int32(int379), month=Int32(int_3380), day=Int32(int_4381), hour=Int32(int_5382), minute=Int32(int_6383), second=Int32(int_7384), microsecond=Int32((!isnothing(int_8385) ? int_8385 : 0)))
    return _t755
end

function parse_boolean_value(parser::Parser)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t756 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t757 = 1
        else
            _t757 = -1
        end
        _t756 = _t757
    end
    prediction386 = _t756
    if prediction386 == 1
        consume_literal!(parser, "false")
        _t758 = false
    else
        if prediction386 == 0
            consume_literal!(parser, "true")
            _t759 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t758 = _t759
    end
    return _t758
end

function parse_sync(parser::Parser)::Proto.Sync
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs387 = Proto.FragmentId[]
    cond388 = match_lookahead_literal(parser, ":", 0)
    while cond388
        _t760 = parse_fragment_id(parser)
        item389 = _t760
        push!(xs387, item389)
        cond388 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids390 = xs387
    consume_literal!(parser, ")")
    _t761 = Proto.Sync(fragments=fragment_ids390)
    return _t761
end

function parse_fragment_id(parser::Parser)::Proto.FragmentId
    consume_literal!(parser, ":")
    symbol391 = consume_terminal!(parser, "SYMBOL")
    return Proto.FragmentId(Vector{UInt8}(symbol391))
end

function parse_epoch(parser::Parser)::Proto.Epoch
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t763 = parse_epoch_writes(parser)
        _t762 = _t763
    else
        _t762 = nothing
    end
    epoch_writes392 = _t762
    if match_lookahead_literal(parser, "(", 0)
        _t765 = parse_epoch_reads(parser)
        _t764 = _t765
    else
        _t764 = nothing
    end
    epoch_reads393 = _t764
    consume_literal!(parser, ")")
    _t766 = Proto.Epoch(writes=(!isnothing(epoch_writes392) ? epoch_writes392 : Proto.Write[]), reads=(!isnothing(epoch_reads393) ? epoch_reads393 : Proto.Read[]))
    return _t766
end

function parse_epoch_writes(parser::Parser)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs394 = Proto.Write[]
    cond395 = match_lookahead_literal(parser, "(", 0)
    while cond395
        _t767 = parse_write(parser)
        item396 = _t767
        push!(xs394, item396)
        cond395 = match_lookahead_literal(parser, "(", 0)
    end
    writes397 = xs394
    consume_literal!(parser, ")")
    return writes397
end

function parse_write(parser::Parser)::Proto.Write
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t769 = 1
        else
            if match_lookahead_literal(parser, "define", 1)
                _t770 = 0
            else
                if match_lookahead_literal(parser, "context", 1)
                    _t771 = 2
                else
                    _t771 = -1
                end
                _t770 = _t771
            end
            _t769 = _t770
        end
        _t768 = _t769
    else
        _t768 = -1
    end
    prediction398 = _t768
    if prediction398 == 2
        _t773 = parse_context(parser)
        context401 = _t773
        _t774 = Proto.Write(write_type=OneOf(:context, context401))
        _t772 = _t774
    else
        if prediction398 == 1
            _t776 = parse_undefine(parser)
            undefine400 = _t776
            _t777 = Proto.Write(write_type=OneOf(:undefine, undefine400))
            _t775 = _t777
        else
            if prediction398 == 0
                _t779 = parse_define(parser)
                define399 = _t779
                _t780 = Proto.Write(write_type=OneOf(:define, define399))
                _t778 = _t780
            else
                throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
            end
            _t775 = _t778
        end
        _t772 = _t775
    end
    return _t772
end

function parse_define(parser::Parser)::Proto.Define
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t781 = parse_fragment(parser)
    fragment402 = _t781
    consume_literal!(parser, ")")
    _t782 = Proto.Define(fragment=fragment402)
    return _t782
end

function parse_fragment(parser::Parser)::Proto.Fragment
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t783 = parse_new_fragment_id(parser)
    new_fragment_id403 = _t783
    xs404 = Proto.Declaration[]
    cond405 = match_lookahead_literal(parser, "(", 0)
    while cond405
        _t784 = parse_declaration(parser)
        item406 = _t784
        push!(xs404, item406)
        cond405 = match_lookahead_literal(parser, "(", 0)
    end
    declarations407 = xs404
    consume_literal!(parser, ")")
    return construct_fragment(parser, new_fragment_id403, declarations407)
end

function parse_new_fragment_id(parser::Parser)::Proto.FragmentId
    _t785 = parse_fragment_id(parser)
    fragment_id408 = _t785
    start_fragment!(parser, fragment_id408)
    return fragment_id408
end

function parse_declaration(parser::Parser)::Proto.Declaration
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t787 = 3
        else
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t788 = 2
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t789 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t790 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t791 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t792 = 1
                            else
                                _t792 = -1
                            end
                            _t791 = _t792
                        end
                        _t790 = _t791
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
    prediction409 = _t786
    if prediction409 == 3
        _t794 = parse_data(parser)
        data413 = _t794
        _t795 = Proto.Declaration(declaration_type=OneOf(:data, data413))
        _t793 = _t795
    else
        if prediction409 == 2
            _t797 = parse_constraint(parser)
            constraint412 = _t797
            _t798 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint412))
            _t796 = _t798
        else
            if prediction409 == 1
                _t800 = parse_algorithm(parser)
                algorithm411 = _t800
                _t801 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm411))
                _t799 = _t801
            else
                if prediction409 == 0
                    _t803 = parse_def(parser)
                    def410 = _t803
                    _t804 = Proto.Declaration(declaration_type=OneOf(:def, def410))
                    _t802 = _t804
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t799 = _t802
            end
            _t796 = _t799
        end
        _t793 = _t796
    end
    return _t793
end

function parse_def(parser::Parser)::Proto.Def
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t805 = parse_relation_id(parser)
    relation_id414 = _t805
    _t806 = parse_abstraction(parser)
    abstraction415 = _t806
    if match_lookahead_literal(parser, "(", 0)
        _t808 = parse_attrs(parser)
        _t807 = _t808
    else
        _t807 = nothing
    end
    attrs416 = _t807
    consume_literal!(parser, ")")
    _t809 = Proto.Def(name=relation_id414, body=abstraction415, attrs=(!isnothing(attrs416) ? attrs416 : Proto.Attribute[]))
    return _t809
end

function parse_relation_id(parser::Parser)::Proto.RelationId
    if match_lookahead_literal(parser, ":", 0)
        _t810 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t811 = 1
        else
            _t811 = -1
        end
        _t810 = _t811
    end
    prediction417 = _t810
    if prediction417 == 1
        uint128419 = consume_terminal!(parser, "UINT128")
        _t812 = Proto.RelationId(uint128419.low, uint128419.high)
    else
        if prediction417 == 0
            consume_literal!(parser, ":")
            symbol418 = consume_terminal!(parser, "SYMBOL")
            _t813 = relation_id_from_string(parser, symbol418)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t812 = _t813
    end
    return _t812
end

function parse_abstraction(parser::Parser)::Proto.Abstraction
    consume_literal!(parser, "(")
    _t814 = parse_bindings(parser)
    bindings420 = _t814
    _t815 = parse_formula(parser)
    formula421 = _t815
    consume_literal!(parser, ")")
    _t816 = Proto.Abstraction(vars=vcat(bindings420[1], !isnothing(bindings420[2]) ? bindings420[2] : []), value=formula421)
    return _t816
end

function parse_bindings(parser::Parser)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs422 = Proto.Binding[]
    cond423 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond423
        _t817 = parse_binding(parser)
        item424 = _t817
        push!(xs422, item424)
        cond423 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings425 = xs422
    if match_lookahead_literal(parser, "|", 0)
        _t819 = parse_value_bindings(parser)
        _t818 = _t819
    else
        _t818 = nothing
    end
    value_bindings426 = _t818
    consume_literal!(parser, "]")
    return (bindings425, (!isnothing(value_bindings426) ? value_bindings426 : Proto.Binding[]),)
end

function parse_binding(parser::Parser)::Proto.Binding
    symbol427 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t820 = parse_type(parser)
    type428 = _t820
    _t821 = Proto.Var(name=symbol427)
    _t822 = Proto.Binding(var=_t821, var"#type"=type428)
    return _t822
end

function parse_type(parser::Parser)::Proto.var"#Type"
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t823 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t824 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t825 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t826 = 8
                else
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t827 = 5
                    else
                        if match_lookahead_literal(parser, "INT", 0)
                            _t828 = 2
                        else
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t829 = 3
                            else
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t830 = 7
                                else
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t831 = 6
                                    else
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t832 = 10
                                        else
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t833 = 9
                                            else
                                                _t833 = -1
                                            end
                                            _t832 = _t833
                                        end
                                        _t831 = _t832
                                    end
                                    _t830 = _t831
                                end
                                _t829 = _t830
                            end
                            _t828 = _t829
                        end
                        _t827 = _t828
                    end
                    _t826 = _t827
                end
                _t825 = _t826
            end
            _t824 = _t825
        end
        _t823 = _t824
    end
    prediction429 = _t823
    if prediction429 == 10
        _t835 = parse_boolean_type(parser)
        boolean_type440 = _t835
        _t836 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type440))
        _t834 = _t836
    else
        if prediction429 == 9
            _t838 = parse_decimal_type(parser)
            decimal_type439 = _t838
            _t839 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type439))
            _t837 = _t839
        else
            if prediction429 == 8
                _t841 = parse_missing_type(parser)
                missing_type438 = _t841
                _t842 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type438))
                _t840 = _t842
            else
                if prediction429 == 7
                    _t844 = parse_datetime_type(parser)
                    datetime_type437 = _t844
                    _t845 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type437))
                    _t843 = _t845
                else
                    if prediction429 == 6
                        _t847 = parse_date_type(parser)
                        date_type436 = _t847
                        _t848 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type436))
                        _t846 = _t848
                    else
                        if prediction429 == 5
                            _t850 = parse_int128_type(parser)
                            int128_type435 = _t850
                            _t851 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type435))
                            _t849 = _t851
                        else
                            if prediction429 == 4
                                _t853 = parse_uint128_type(parser)
                                uint128_type434 = _t853
                                _t854 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type434))
                                _t852 = _t854
                            else
                                if prediction429 == 3
                                    _t856 = parse_float_type(parser)
                                    float_type433 = _t856
                                    _t857 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type433))
                                    _t855 = _t857
                                else
                                    if prediction429 == 2
                                        _t859 = parse_int_type(parser)
                                        int_type432 = _t859
                                        _t860 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type432))
                                        _t858 = _t860
                                    else
                                        if prediction429 == 1
                                            _t862 = parse_string_type(parser)
                                            string_type431 = _t862
                                            _t863 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type431))
                                            _t861 = _t863
                                        else
                                            if prediction429 == 0
                                                _t865 = parse_unspecified_type(parser)
                                                unspecified_type430 = _t865
                                                _t866 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type430))
                                                _t864 = _t866
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t861 = _t864
                                        end
                                        _t858 = _t861
                                    end
                                    _t855 = _t858
                                end
                                _t852 = _t855
                            end
                            _t849 = _t852
                        end
                        _t846 = _t849
                    end
                    _t843 = _t846
                end
                _t840 = _t843
            end
            _t837 = _t840
        end
        _t834 = _t837
    end
    return _t834
end

function parse_unspecified_type(parser::Parser)::Proto.UnspecifiedType
    consume_literal!(parser, "UNKNOWN")
    _t867 = Proto.UnspecifiedType()
    return _t867
end

function parse_string_type(parser::Parser)::Proto.StringType
    consume_literal!(parser, "STRING")
    _t868 = Proto.StringType()
    return _t868
end

function parse_int_type(parser::Parser)::Proto.IntType
    consume_literal!(parser, "INT")
    _t869 = Proto.IntType()
    return _t869
end

function parse_float_type(parser::Parser)::Proto.FloatType
    consume_literal!(parser, "FLOAT")
    _t870 = Proto.FloatType()
    return _t870
end

function parse_uint128_type(parser::Parser)::Proto.UInt128Type
    consume_literal!(parser, "UINT128")
    _t871 = Proto.UInt128Type()
    return _t871
end

function parse_int128_type(parser::Parser)::Proto.Int128Type
    consume_literal!(parser, "INT128")
    _t872 = Proto.Int128Type()
    return _t872
end

function parse_date_type(parser::Parser)::Proto.DateType
    consume_literal!(parser, "DATE")
    _t873 = Proto.DateType()
    return _t873
end

function parse_datetime_type(parser::Parser)::Proto.DateTimeType
    consume_literal!(parser, "DATETIME")
    _t874 = Proto.DateTimeType()
    return _t874
end

function parse_missing_type(parser::Parser)::Proto.MissingType
    consume_literal!(parser, "MISSING")
    _t875 = Proto.MissingType()
    return _t875
end

function parse_decimal_type(parser::Parser)::Proto.DecimalType
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int441 = consume_terminal!(parser, "INT")
    int_3442 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t876 = Proto.DecimalType(precision=Int32(int441), scale=Int32(int_3442))
    return _t876
end

function parse_boolean_type(parser::Parser)::Proto.BooleanType
    consume_literal!(parser, "BOOLEAN")
    _t877 = Proto.BooleanType()
    return _t877
end

function parse_value_bindings(parser::Parser)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs443 = Proto.Binding[]
    cond444 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond444
        _t878 = parse_binding(parser)
        item445 = _t878
        push!(xs443, item445)
        cond444 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings446 = xs443
    return bindings446
end

function parse_formula(parser::Parser)::Proto.Formula
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t880 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t881 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t882 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t883 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t884 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t885 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t886 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t887 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t888 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t889 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t890 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t891 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t892 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t893 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t894 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t895 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t896 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t897 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t898 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t899 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t900 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t901 = 10
                                                                                            else
                                                                                                _t901 = -1
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
                                            end
                                            _t888 = _t889
                                        end
                                        _t887 = _t888
                                    end
                                    _t886 = _t887
                                end
                                _t885 = _t886
                            end
                            _t884 = _t885
                        end
                        _t883 = _t884
                    end
                    _t882 = _t883
                end
                _t881 = _t882
            end
            _t880 = _t881
        end
        _t879 = _t880
    else
        _t879 = -1
    end
    prediction447 = _t879
    if prediction447 == 12
        _t903 = parse_cast(parser)
        cast460 = _t903
        _t904 = Proto.Formula(formula_type=OneOf(:cast, cast460))
        _t902 = _t904
    else
        if prediction447 == 11
            _t906 = parse_rel_atom(parser)
            rel_atom459 = _t906
            _t907 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom459))
            _t905 = _t907
        else
            if prediction447 == 10
                _t909 = parse_primitive(parser)
                primitive458 = _t909
                _t910 = Proto.Formula(formula_type=OneOf(:primitive, primitive458))
                _t908 = _t910
            else
                if prediction447 == 9
                    _t912 = parse_pragma(parser)
                    pragma457 = _t912
                    _t913 = Proto.Formula(formula_type=OneOf(:pragma, pragma457))
                    _t911 = _t913
                else
                    if prediction447 == 8
                        _t915 = parse_atom(parser)
                        atom456 = _t915
                        _t916 = Proto.Formula(formula_type=OneOf(:atom, atom456))
                        _t914 = _t916
                    else
                        if prediction447 == 7
                            _t918 = parse_ffi(parser)
                            ffi455 = _t918
                            _t919 = Proto.Formula(formula_type=OneOf(:ffi, ffi455))
                            _t917 = _t919
                        else
                            if prediction447 == 6
                                _t921 = parse_not(parser)
                                not454 = _t921
                                _t922 = Proto.Formula(formula_type=OneOf(:not, not454))
                                _t920 = _t922
                            else
                                if prediction447 == 5
                                    _t924 = parse_disjunction(parser)
                                    disjunction453 = _t924
                                    _t925 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction453))
                                    _t923 = _t925
                                else
                                    if prediction447 == 4
                                        _t927 = parse_conjunction(parser)
                                        conjunction452 = _t927
                                        _t928 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction452))
                                        _t926 = _t928
                                    else
                                        if prediction447 == 3
                                            _t930 = parse_reduce(parser)
                                            reduce451 = _t930
                                            _t931 = Proto.Formula(formula_type=OneOf(:reduce, reduce451))
                                            _t929 = _t931
                                        else
                                            if prediction447 == 2
                                                _t933 = parse_exists(parser)
                                                exists450 = _t933
                                                _t934 = Proto.Formula(formula_type=OneOf(:exists, exists450))
                                                _t932 = _t934
                                            else
                                                if prediction447 == 1
                                                    _t936 = parse_false(parser)
                                                    false449 = _t936
                                                    _t937 = Proto.Formula(formula_type=OneOf(:disjunction, false449))
                                                    _t935 = _t937
                                                else
                                                    if prediction447 == 0
                                                        _t939 = parse_true(parser)
                                                        true448 = _t939
                                                        _t940 = Proto.Formula(formula_type=OneOf(:conjunction, true448))
                                                        _t938 = _t940
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t935 = _t938
                                                end
                                                _t932 = _t935
                                            end
                                            _t929 = _t932
                                        end
                                        _t926 = _t929
                                    end
                                    _t923 = _t926
                                end
                                _t920 = _t923
                            end
                            _t917 = _t920
                        end
                        _t914 = _t917
                    end
                    _t911 = _t914
                end
                _t908 = _t911
            end
            _t905 = _t908
        end
        _t902 = _t905
    end
    return _t902
end

function parse_true(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t941 = Proto.Conjunction(args=Proto.Formula[])
    return _t941
end

function parse_false(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t942 = Proto.Disjunction(args=Proto.Formula[])
    return _t942
end

function parse_exists(parser::Parser)::Proto.Exists
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t943 = parse_bindings(parser)
    bindings461 = _t943
    _t944 = parse_formula(parser)
    formula462 = _t944
    consume_literal!(parser, ")")
    _t945 = Proto.Abstraction(vars=vcat(bindings461[1], !isnothing(bindings461[2]) ? bindings461[2] : []), value=formula462)
    _t946 = Proto.Exists(body=_t945)
    return _t946
end

function parse_reduce(parser::Parser)::Proto.Reduce
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t947 = parse_abstraction(parser)
    abstraction463 = _t947
    _t948 = parse_abstraction(parser)
    abstraction_3464 = _t948
    _t949 = parse_terms(parser)
    terms465 = _t949
    consume_literal!(parser, ")")
    _t950 = Proto.Reduce(op=abstraction463, body=abstraction_3464, terms=terms465)
    return _t950
end

function parse_terms(parser::Parser)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs466 = Proto.Term[]
    cond467 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond467
        _t951 = parse_term(parser)
        item468 = _t951
        push!(xs466, item468)
        cond467 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms469 = xs466
    consume_literal!(parser, ")")
    return terms469
end

function parse_term(parser::Parser)::Proto.Term
    if match_lookahead_literal(parser, "true", 0)
        _t952 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t953 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t954 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t955 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t956 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t957 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t958 = 1
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t959 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t960 = 1
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t961 = 1
                                        else
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t962 = 1
                                            else
                                                _t962 = -1
                                            end
                                            _t961 = _t962
                                        end
                                        _t960 = _t961
                                    end
                                    _t959 = _t960
                                end
                                _t958 = _t959
                            end
                            _t957 = _t958
                        end
                        _t956 = _t957
                    end
                    _t955 = _t956
                end
                _t954 = _t955
            end
            _t953 = _t954
        end
        _t952 = _t953
    end
    prediction470 = _t952
    if prediction470 == 1
        _t964 = parse_constant(parser)
        constant472 = _t964
        _t965 = Proto.Term(term_type=OneOf(:constant, constant472))
        _t963 = _t965
    else
        if prediction470 == 0
            _t967 = parse_var(parser)
            var471 = _t967
            _t968 = Proto.Term(term_type=OneOf(:var, var471))
            _t966 = _t968
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t963 = _t966
    end
    return _t963
end

function parse_var(parser::Parser)::Proto.Var
    symbol473 = consume_terminal!(parser, "SYMBOL")
    _t969 = Proto.Var(name=symbol473)
    return _t969
end

function parse_constant(parser::Parser)::Proto.Value
    _t970 = parse_value(parser)
    value474 = _t970
    return value474
end

function parse_conjunction(parser::Parser)::Proto.Conjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs475 = Proto.Formula[]
    cond476 = match_lookahead_literal(parser, "(", 0)
    while cond476
        _t971 = parse_formula(parser)
        item477 = _t971
        push!(xs475, item477)
        cond476 = match_lookahead_literal(parser, "(", 0)
    end
    formulas478 = xs475
    consume_literal!(parser, ")")
    _t972 = Proto.Conjunction(args=formulas478)
    return _t972
end

function parse_disjunction(parser::Parser)::Proto.Disjunction
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs479 = Proto.Formula[]
    cond480 = match_lookahead_literal(parser, "(", 0)
    while cond480
        _t973 = parse_formula(parser)
        item481 = _t973
        push!(xs479, item481)
        cond480 = match_lookahead_literal(parser, "(", 0)
    end
    formulas482 = xs479
    consume_literal!(parser, ")")
    _t974 = Proto.Disjunction(args=formulas482)
    return _t974
end

function parse_not(parser::Parser)::Proto.Not
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t975 = parse_formula(parser)
    formula483 = _t975
    consume_literal!(parser, ")")
    _t976 = Proto.Not(arg=formula483)
    return _t976
end

function parse_ffi(parser::Parser)::Proto.FFI
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t977 = parse_name(parser)
    name484 = _t977
    _t978 = parse_ffi_args(parser)
    ffi_args485 = _t978
    _t979 = parse_terms(parser)
    terms486 = _t979
    consume_literal!(parser, ")")
    _t980 = Proto.FFI(name=name484, args=ffi_args485, terms=terms486)
    return _t980
end

function parse_name(parser::Parser)::String
    consume_literal!(parser, ":")
    symbol487 = consume_terminal!(parser, "SYMBOL")
    return symbol487
end

function parse_ffi_args(parser::Parser)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs488 = Proto.Abstraction[]
    cond489 = match_lookahead_literal(parser, "(", 0)
    while cond489
        _t981 = parse_abstraction(parser)
        item490 = _t981
        push!(xs488, item490)
        cond489 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions491 = xs488
    consume_literal!(parser, ")")
    return abstractions491
end

function parse_atom(parser::Parser)::Proto.Atom
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t982 = parse_relation_id(parser)
    relation_id492 = _t982
    xs493 = Proto.Term[]
    cond494 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond494
        _t983 = parse_term(parser)
        item495 = _t983
        push!(xs493, item495)
        cond494 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms496 = xs493
    consume_literal!(parser, ")")
    _t984 = Proto.Atom(name=relation_id492, terms=terms496)
    return _t984
end

function parse_pragma(parser::Parser)::Proto.Pragma
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t985 = parse_name(parser)
    name497 = _t985
    xs498 = Proto.Term[]
    cond499 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond499
        _t986 = parse_term(parser)
        item500 = _t986
        push!(xs498, item500)
        cond499 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms501 = xs498
    consume_literal!(parser, ")")
    _t987 = Proto.Pragma(name=name497, terms=terms501)
    return _t987
end

function parse_primitive(parser::Parser)::Proto.Primitive
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t989 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t990 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t991 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t992 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t993 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t994 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t995 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t996 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t997 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t998 = 7
                                            else
                                                _t998 = -1
                                            end
                                            _t997 = _t998
                                        end
                                        _t996 = _t997
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
    else
        _t988 = -1
    end
    prediction502 = _t988
    if prediction502 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1000 = parse_name(parser)
        name512 = _t1000
        xs513 = Proto.RelTerm[]
        cond514 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond514
            _t1001 = parse_rel_term(parser)
            item515 = _t1001
            push!(xs513, item515)
            cond514 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms516 = xs513
        consume_literal!(parser, ")")
        _t1002 = Proto.Primitive(name=name512, terms=rel_terms516)
        _t999 = _t1002
    else
        if prediction502 == 8
            _t1004 = parse_divide(parser)
            divide511 = _t1004
            _t1003 = divide511
        else
            if prediction502 == 7
                _t1006 = parse_multiply(parser)
                multiply510 = _t1006
                _t1005 = multiply510
            else
                if prediction502 == 6
                    _t1008 = parse_minus(parser)
                    minus509 = _t1008
                    _t1007 = minus509
                else
                    if prediction502 == 5
                        _t1010 = parse_add(parser)
                        add508 = _t1010
                        _t1009 = add508
                    else
                        if prediction502 == 4
                            _t1012 = parse_gt_eq(parser)
                            gt_eq507 = _t1012
                            _t1011 = gt_eq507
                        else
                            if prediction502 == 3
                                _t1014 = parse_gt(parser)
                                gt506 = _t1014
                                _t1013 = gt506
                            else
                                if prediction502 == 2
                                    _t1016 = parse_lt_eq(parser)
                                    lt_eq505 = _t1016
                                    _t1015 = lt_eq505
                                else
                                    if prediction502 == 1
                                        _t1018 = parse_lt(parser)
                                        lt504 = _t1018
                                        _t1017 = lt504
                                    else
                                        if prediction502 == 0
                                            _t1020 = parse_eq(parser)
                                            eq503 = _t1020
                                            _t1019 = eq503
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1017 = _t1019
                                    end
                                    _t1015 = _t1017
                                end
                                _t1013 = _t1015
                            end
                            _t1011 = _t1013
                        end
                        _t1009 = _t1011
                    end
                    _t1007 = _t1009
                end
                _t1005 = _t1007
            end
            _t1003 = _t1005
        end
        _t999 = _t1003
    end
    return _t999
end

function parse_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1021 = parse_term(parser)
    term517 = _t1021
    _t1022 = parse_term(parser)
    term_3518 = _t1022
    consume_literal!(parser, ")")
    _t1023 = Proto.RelTerm(rel_term_type=OneOf(:term, term517))
    _t1024 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3518))
    _t1025 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1023, _t1024])
    return _t1025
end

function parse_lt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1026 = parse_term(parser)
    term519 = _t1026
    _t1027 = parse_term(parser)
    term_3520 = _t1027
    consume_literal!(parser, ")")
    _t1028 = Proto.RelTerm(rel_term_type=OneOf(:term, term519))
    _t1029 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3520))
    _t1030 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1028, _t1029])
    return _t1030
end

function parse_lt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1031 = parse_term(parser)
    term521 = _t1031
    _t1032 = parse_term(parser)
    term_3522 = _t1032
    consume_literal!(parser, ")")
    _t1033 = Proto.RelTerm(rel_term_type=OneOf(:term, term521))
    _t1034 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3522))
    _t1035 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1033, _t1034])
    return _t1035
end

function parse_gt(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1036 = parse_term(parser)
    term523 = _t1036
    _t1037 = parse_term(parser)
    term_3524 = _t1037
    consume_literal!(parser, ")")
    _t1038 = Proto.RelTerm(rel_term_type=OneOf(:term, term523))
    _t1039 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3524))
    _t1040 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1038, _t1039])
    return _t1040
end

function parse_gt_eq(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1041 = parse_term(parser)
    term525 = _t1041
    _t1042 = parse_term(parser)
    term_3526 = _t1042
    consume_literal!(parser, ")")
    _t1043 = Proto.RelTerm(rel_term_type=OneOf(:term, term525))
    _t1044 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3526))
    _t1045 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1043, _t1044])
    return _t1045
end

function parse_add(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1046 = parse_term(parser)
    term527 = _t1046
    _t1047 = parse_term(parser)
    term_3528 = _t1047
    _t1048 = parse_term(parser)
    term_4529 = _t1048
    consume_literal!(parser, ")")
    _t1049 = Proto.RelTerm(rel_term_type=OneOf(:term, term527))
    _t1050 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3528))
    _t1051 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4529))
    _t1052 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1049, _t1050, _t1051])
    return _t1052
end

function parse_minus(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1053 = parse_term(parser)
    term530 = _t1053
    _t1054 = parse_term(parser)
    term_3531 = _t1054
    _t1055 = parse_term(parser)
    term_4532 = _t1055
    consume_literal!(parser, ")")
    _t1056 = Proto.RelTerm(rel_term_type=OneOf(:term, term530))
    _t1057 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3531))
    _t1058 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4532))
    _t1059 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1056, _t1057, _t1058])
    return _t1059
end

function parse_multiply(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1060 = parse_term(parser)
    term533 = _t1060
    _t1061 = parse_term(parser)
    term_3534 = _t1061
    _t1062 = parse_term(parser)
    term_4535 = _t1062
    consume_literal!(parser, ")")
    _t1063 = Proto.RelTerm(rel_term_type=OneOf(:term, term533))
    _t1064 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3534))
    _t1065 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4535))
    _t1066 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1063, _t1064, _t1065])
    return _t1066
end

function parse_divide(parser::Parser)::Proto.Primitive
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1067 = parse_term(parser)
    term536 = _t1067
    _t1068 = parse_term(parser)
    term_3537 = _t1068
    _t1069 = parse_term(parser)
    term_4538 = _t1069
    consume_literal!(parser, ")")
    _t1070 = Proto.RelTerm(rel_term_type=OneOf(:term, term536))
    _t1071 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3537))
    _t1072 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4538))
    _t1073 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1070, _t1071, _t1072])
    return _t1073
end

function parse_rel_term(parser::Parser)::Proto.RelTerm
    if match_lookahead_literal(parser, "true", 0)
        _t1074 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1075 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1076 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1077 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1078 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1079 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1080 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1081 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1082 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1083 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1084 = 1
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1085 = 1
                                                else
                                                    _t1085 = -1
                                                end
                                                _t1084 = _t1085
                                            end
                                            _t1083 = _t1084
                                        end
                                        _t1082 = _t1083
                                    end
                                    _t1081 = _t1082
                                end
                                _t1080 = _t1081
                            end
                            _t1079 = _t1080
                        end
                        _t1078 = _t1079
                    end
                    _t1077 = _t1078
                end
                _t1076 = _t1077
            end
            _t1075 = _t1076
        end
        _t1074 = _t1075
    end
    prediction539 = _t1074
    if prediction539 == 1
        _t1087 = parse_term(parser)
        term541 = _t1087
        _t1088 = Proto.RelTerm(rel_term_type=OneOf(:term, term541))
        _t1086 = _t1088
    else
        if prediction539 == 0
            _t1090 = parse_specialized_value(parser)
            specialized_value540 = _t1090
            _t1091 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value540))
            _t1089 = _t1091
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1086 = _t1089
    end
    return _t1086
end

function parse_specialized_value(parser::Parser)::Proto.Value
    consume_literal!(parser, "#")
    _t1092 = parse_value(parser)
    value542 = _t1092
    return value542
end

function parse_rel_atom(parser::Parser)::Proto.RelAtom
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1093 = parse_name(parser)
    name543 = _t1093
    xs544 = Proto.RelTerm[]
    cond545 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond545
        _t1094 = parse_rel_term(parser)
        item546 = _t1094
        push!(xs544, item546)
        cond545 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms547 = xs544
    consume_literal!(parser, ")")
    _t1095 = Proto.RelAtom(name=name543, terms=rel_terms547)
    return _t1095
end

function parse_cast(parser::Parser)::Proto.Cast
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1096 = parse_term(parser)
    term548 = _t1096
    _t1097 = parse_term(parser)
    term_3549 = _t1097
    consume_literal!(parser, ")")
    _t1098 = Proto.Cast(input=term548, result=term_3549)
    return _t1098
end

function parse_attrs(parser::Parser)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs550 = Proto.Attribute[]
    cond551 = match_lookahead_literal(parser, "(", 0)
    while cond551
        _t1099 = parse_attribute(parser)
        item552 = _t1099
        push!(xs550, item552)
        cond551 = match_lookahead_literal(parser, "(", 0)
    end
    attributes553 = xs550
    consume_literal!(parser, ")")
    return attributes553
end

function parse_attribute(parser::Parser)::Proto.Attribute
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1100 = parse_name(parser)
    name554 = _t1100
    xs555 = Proto.Value[]
    cond556 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond556
        _t1101 = parse_value(parser)
        item557 = _t1101
        push!(xs555, item557)
        cond556 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values558 = xs555
    consume_literal!(parser, ")")
    _t1102 = Proto.Attribute(name=name554, args=values558)
    return _t1102
end

function parse_algorithm(parser::Parser)::Proto.Algorithm
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs559 = Proto.RelationId[]
    cond560 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond560
        _t1103 = parse_relation_id(parser)
        item561 = _t1103
        push!(xs559, item561)
        cond560 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids562 = xs559
    _t1104 = parse_script(parser)
    script563 = _t1104
    consume_literal!(parser, ")")
    _t1105 = Proto.Algorithm(var"#global"=relation_ids562, body=script563)
    return _t1105
end

function parse_script(parser::Parser)::Proto.Script
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs564 = Proto.Construct[]
    cond565 = match_lookahead_literal(parser, "(", 0)
    while cond565
        _t1106 = parse_construct(parser)
        item566 = _t1106
        push!(xs564, item566)
        cond565 = match_lookahead_literal(parser, "(", 0)
    end
    constructs567 = xs564
    consume_literal!(parser, ")")
    _t1107 = Proto.Script(constructs=constructs567)
    return _t1107
end

function parse_construct(parser::Parser)::Proto.Construct
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1109 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1110 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1111 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1112 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1113 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1114 = 1
                            else
                                _t1114 = -1
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
    else
        _t1108 = -1
    end
    prediction568 = _t1108
    if prediction568 == 1
        _t1116 = parse_instruction(parser)
        instruction570 = _t1116
        _t1117 = Proto.Construct(construct_type=OneOf(:instruction, instruction570))
        _t1115 = _t1117
    else
        if prediction568 == 0
            _t1119 = parse_loop(parser)
            loop569 = _t1119
            _t1120 = Proto.Construct(construct_type=OneOf(:loop, loop569))
            _t1118 = _t1120
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1115 = _t1118
    end
    return _t1115
end

function parse_loop(parser::Parser)::Proto.Loop
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1121 = parse_init(parser)
    init571 = _t1121
    _t1122 = parse_script(parser)
    script572 = _t1122
    consume_literal!(parser, ")")
    _t1123 = Proto.Loop(init=init571, body=script572)
    return _t1123
end

function parse_init(parser::Parser)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs573 = Proto.Instruction[]
    cond574 = match_lookahead_literal(parser, "(", 0)
    while cond574
        _t1124 = parse_instruction(parser)
        item575 = _t1124
        push!(xs573, item575)
        cond574 = match_lookahead_literal(parser, "(", 0)
    end
    instructions576 = xs573
    consume_literal!(parser, ")")
    return instructions576
end

function parse_instruction(parser::Parser)::Proto.Instruction
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1126 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1127 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1128 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1129 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1130 = 0
                        else
                            _t1130 = -1
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
    else
        _t1125 = -1
    end
    prediction577 = _t1125
    if prediction577 == 4
        _t1132 = parse_monus_def(parser)
        monus_def582 = _t1132
        _t1133 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def582))
        _t1131 = _t1133
    else
        if prediction577 == 3
            _t1135 = parse_monoid_def(parser)
            monoid_def581 = _t1135
            _t1136 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def581))
            _t1134 = _t1136
        else
            if prediction577 == 2
                _t1138 = parse_break(parser)
                break580 = _t1138
                _t1139 = Proto.Instruction(instr_type=OneOf(:var"#break", break580))
                _t1137 = _t1139
            else
                if prediction577 == 1
                    _t1141 = parse_upsert(parser)
                    upsert579 = _t1141
                    _t1142 = Proto.Instruction(instr_type=OneOf(:upsert, upsert579))
                    _t1140 = _t1142
                else
                    if prediction577 == 0
                        _t1144 = parse_assign(parser)
                        assign578 = _t1144
                        _t1145 = Proto.Instruction(instr_type=OneOf(:assign, assign578))
                        _t1143 = _t1145
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1140 = _t1143
                end
                _t1137 = _t1140
            end
            _t1134 = _t1137
        end
        _t1131 = _t1134
    end
    return _t1131
end

function parse_assign(parser::Parser)::Proto.Assign
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1146 = parse_relation_id(parser)
    relation_id583 = _t1146
    _t1147 = parse_abstraction(parser)
    abstraction584 = _t1147
    if match_lookahead_literal(parser, "(", 0)
        _t1149 = parse_attrs(parser)
        _t1148 = _t1149
    else
        _t1148 = nothing
    end
    attrs585 = _t1148
    consume_literal!(parser, ")")
    _t1150 = Proto.Assign(name=relation_id583, body=abstraction584, attrs=(!isnothing(attrs585) ? attrs585 : Proto.Attribute[]))
    return _t1150
end

function parse_upsert(parser::Parser)::Proto.Upsert
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1151 = parse_relation_id(parser)
    relation_id586 = _t1151
    _t1152 = parse_abstraction_with_arity(parser)
    abstraction_with_arity587 = _t1152
    if match_lookahead_literal(parser, "(", 0)
        _t1154 = parse_attrs(parser)
        _t1153 = _t1154
    else
        _t1153 = nothing
    end
    attrs588 = _t1153
    consume_literal!(parser, ")")
    _t1155 = Proto.Upsert(name=relation_id586, body=abstraction_with_arity587[1], attrs=(!isnothing(attrs588) ? attrs588 : Proto.Attribute[]), value_arity=abstraction_with_arity587[2])
    return _t1155
end

function parse_abstraction_with_arity(parser::Parser)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1156 = parse_bindings(parser)
    bindings589 = _t1156
    _t1157 = parse_formula(parser)
    formula590 = _t1157
    consume_literal!(parser, ")")
    _t1158 = Proto.Abstraction(vars=vcat(bindings589[1], !isnothing(bindings589[2]) ? bindings589[2] : []), value=formula590)
    return (_t1158, length(bindings589[2]),)
end

function parse_break(parser::Parser)::Proto.Break
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1159 = parse_relation_id(parser)
    relation_id591 = _t1159
    _t1160 = parse_abstraction(parser)
    abstraction592 = _t1160
    if match_lookahead_literal(parser, "(", 0)
        _t1162 = parse_attrs(parser)
        _t1161 = _t1162
    else
        _t1161 = nothing
    end
    attrs593 = _t1161
    consume_literal!(parser, ")")
    _t1163 = Proto.Break(name=relation_id591, body=abstraction592, attrs=(!isnothing(attrs593) ? attrs593 : Proto.Attribute[]))
    return _t1163
end

function parse_monoid_def(parser::Parser)::Proto.MonoidDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1164 = parse_monoid(parser)
    monoid594 = _t1164
    _t1165 = parse_relation_id(parser)
    relation_id595 = _t1165
    _t1166 = parse_abstraction_with_arity(parser)
    abstraction_with_arity596 = _t1166
    if match_lookahead_literal(parser, "(", 0)
        _t1168 = parse_attrs(parser)
        _t1167 = _t1168
    else
        _t1167 = nothing
    end
    attrs597 = _t1167
    consume_literal!(parser, ")")
    _t1169 = Proto.MonoidDef(monoid=monoid594, name=relation_id595, body=abstraction_with_arity596[1], attrs=(!isnothing(attrs597) ? attrs597 : Proto.Attribute[]), value_arity=abstraction_with_arity596[2])
    return _t1169
end

function parse_monoid(parser::Parser)::Proto.Monoid
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1171 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1172 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1173 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1174 = 2
                    else
                        _t1174 = -1
                    end
                    _t1173 = _t1174
                end
                _t1172 = _t1173
            end
            _t1171 = _t1172
        end
        _t1170 = _t1171
    else
        _t1170 = -1
    end
    prediction598 = _t1170
    if prediction598 == 3
        _t1176 = parse_sum_monoid(parser)
        sum_monoid602 = _t1176
        _t1177 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid602))
        _t1175 = _t1177
    else
        if prediction598 == 2
            _t1179 = parse_max_monoid(parser)
            max_monoid601 = _t1179
            _t1180 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid601))
            _t1178 = _t1180
        else
            if prediction598 == 1
                _t1182 = parse_min_monoid(parser)
                min_monoid600 = _t1182
                _t1183 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid600))
                _t1181 = _t1183
            else
                if prediction598 == 0
                    _t1185 = parse_or_monoid(parser)
                    or_monoid599 = _t1185
                    _t1186 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid599))
                    _t1184 = _t1186
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1181 = _t1184
            end
            _t1178 = _t1181
        end
        _t1175 = _t1178
    end
    return _t1175
end

function parse_or_monoid(parser::Parser)::Proto.OrMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1187 = Proto.OrMonoid()
    return _t1187
end

function parse_min_monoid(parser::Parser)::Proto.MinMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1188 = parse_type(parser)
    type603 = _t1188
    consume_literal!(parser, ")")
    _t1189 = Proto.MinMonoid(var"#type"=type603)
    return _t1189
end

function parse_max_monoid(parser::Parser)::Proto.MaxMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1190 = parse_type(parser)
    type604 = _t1190
    consume_literal!(parser, ")")
    _t1191 = Proto.MaxMonoid(var"#type"=type604)
    return _t1191
end

function parse_sum_monoid(parser::Parser)::Proto.SumMonoid
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1192 = parse_type(parser)
    type605 = _t1192
    consume_literal!(parser, ")")
    _t1193 = Proto.SumMonoid(var"#type"=type605)
    return _t1193
end

function parse_monus_def(parser::Parser)::Proto.MonusDef
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1194 = parse_monoid(parser)
    monoid606 = _t1194
    _t1195 = parse_relation_id(parser)
    relation_id607 = _t1195
    _t1196 = parse_abstraction_with_arity(parser)
    abstraction_with_arity608 = _t1196
    if match_lookahead_literal(parser, "(", 0)
        _t1198 = parse_attrs(parser)
        _t1197 = _t1198
    else
        _t1197 = nothing
    end
    attrs609 = _t1197
    consume_literal!(parser, ")")
    _t1199 = Proto.MonusDef(monoid=monoid606, name=relation_id607, body=abstraction_with_arity608[1], attrs=(!isnothing(attrs609) ? attrs609 : Proto.Attribute[]), value_arity=abstraction_with_arity608[2])
    return _t1199
end

function parse_constraint(parser::Parser)::Proto.Constraint
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1200 = parse_relation_id(parser)
    relation_id610 = _t1200
    _t1201 = parse_abstraction(parser)
    abstraction611 = _t1201
    _t1202 = parse_functional_dependency_keys(parser)
    functional_dependency_keys612 = _t1202
    _t1203 = parse_functional_dependency_values(parser)
    functional_dependency_values613 = _t1203
    consume_literal!(parser, ")")
    _t1204 = Proto.FunctionalDependency(guard=abstraction611, keys=functional_dependency_keys612, values=functional_dependency_values613)
    _t1205 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1204), name=relation_id610)
    return _t1205
end

function parse_functional_dependency_keys(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs614 = Proto.Var[]
    cond615 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond615
        _t1206 = parse_var(parser)
        item616 = _t1206
        push!(xs614, item616)
        cond615 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars617 = xs614
    consume_literal!(parser, ")")
    return vars617
end

function parse_functional_dependency_values(parser::Parser)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs618 = Proto.Var[]
    cond619 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond619
        _t1207 = parse_var(parser)
        item620 = _t1207
        push!(xs618, item620)
        cond619 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars621 = xs618
    consume_literal!(parser, ")")
    return vars621
end

function parse_data(parser::Parser)::Proto.Data
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1209 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1210 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1211 = 1
                else
                    _t1211 = -1
                end
                _t1210 = _t1211
            end
            _t1209 = _t1210
        end
        _t1208 = _t1209
    else
        _t1208 = -1
    end
    prediction622 = _t1208
    if prediction622 == 2
        _t1213 = parse_csv_data(parser)
        csv_data625 = _t1213
        _t1214 = Proto.Data(data_type=OneOf(:csv_data, csv_data625))
        _t1212 = _t1214
    else
        if prediction622 == 1
            _t1216 = parse_betree_relation(parser)
            betree_relation624 = _t1216
            _t1217 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation624))
            _t1215 = _t1217
        else
            if prediction622 == 0
                _t1219 = parse_rel_edb(parser)
                rel_edb623 = _t1219
                _t1220 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb623))
                _t1218 = _t1220
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1215 = _t1218
        end
        _t1212 = _t1215
    end
    return _t1212
end

function parse_rel_edb(parser::Parser)::Proto.RelEDB
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    _t1221 = parse_relation_id(parser)
    relation_id626 = _t1221
    _t1222 = parse_rel_edb_path(parser)
    rel_edb_path627 = _t1222
    _t1223 = parse_rel_edb_types(parser)
    rel_edb_types628 = _t1223
    consume_literal!(parser, ")")
    _t1224 = Proto.RelEDB(target_id=relation_id626, path=rel_edb_path627, types=rel_edb_types628)
    return _t1224
end

function parse_rel_edb_path(parser::Parser)::Vector{String}
    consume_literal!(parser, "[")
    xs629 = String[]
    cond630 = match_lookahead_terminal(parser, "STRING", 0)
    while cond630
        item631 = consume_terminal!(parser, "STRING")
        push!(xs629, item631)
        cond630 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings632 = xs629
    consume_literal!(parser, "]")
    return strings632
end

function parse_rel_edb_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs633 = Proto.var"#Type"[]
    cond634 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond634
        _t1225 = parse_type(parser)
        item635 = _t1225
        push!(xs633, item635)
        cond634 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types636 = xs633
    consume_literal!(parser, "]")
    return types636
end

function parse_betree_relation(parser::Parser)::Proto.BeTreeRelation
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1226 = parse_relation_id(parser)
    relation_id637 = _t1226
    _t1227 = parse_betree_info(parser)
    betree_info638 = _t1227
    consume_literal!(parser, ")")
    _t1228 = Proto.BeTreeRelation(name=relation_id637, relation_info=betree_info638)
    return _t1228
end

function parse_betree_info(parser::Parser)::Proto.BeTreeInfo
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1229 = parse_betree_info_key_types(parser)
    betree_info_key_types639 = _t1229
    _t1230 = parse_betree_info_value_types(parser)
    betree_info_value_types640 = _t1230
    _t1231 = parse_config_dict(parser)
    config_dict641 = _t1231
    consume_literal!(parser, ")")
    _t1232 = construct_betree_info(parser, betree_info_key_types639, betree_info_value_types640, config_dict641)
    return _t1232
end

function parse_betree_info_key_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs642 = Proto.var"#Type"[]
    cond643 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond643
        _t1233 = parse_type(parser)
        item644 = _t1233
        push!(xs642, item644)
        cond643 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types645 = xs642
    consume_literal!(parser, ")")
    return types645
end

function parse_betree_info_value_types(parser::Parser)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs646 = Proto.var"#Type"[]
    cond647 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond647
        _t1234 = parse_type(parser)
        item648 = _t1234
        push!(xs646, item648)
        cond647 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types649 = xs646
    consume_literal!(parser, ")")
    return types649
end

function parse_csv_data(parser::Parser)::Proto.CSVData
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1235 = parse_csvlocator(parser)
    csvlocator650 = _t1235
    _t1236 = parse_csv_config(parser)
    csv_config651 = _t1236
    _t1237 = parse_csv_columns(parser)
    csv_columns652 = _t1237
    _t1238 = parse_csv_asof(parser)
    csv_asof653 = _t1238
    consume_literal!(parser, ")")
    _t1239 = Proto.CSVData(locator=csvlocator650, config=csv_config651, columns=csv_columns652, asof=csv_asof653)
    return _t1239
end

function parse_csvlocator(parser::Parser)::Proto.CSVLocator
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1241 = parse_csv_locator_paths(parser)
        _t1240 = _t1241
    else
        _t1240 = nothing
    end
    csv_locator_paths654 = _t1240
    if match_lookahead_literal(parser, "(", 0)
        _t1243 = parse_csv_locator_inline_data(parser)
        _t1242 = _t1243
    else
        _t1242 = nothing
    end
    csv_locator_inline_data655 = _t1242
    consume_literal!(parser, ")")
    _t1244 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths654) ? csv_locator_paths654 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data655) ? csv_locator_inline_data655 : "")))
    return _t1244
end

function parse_csv_locator_paths(parser::Parser)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs656 = String[]
    cond657 = match_lookahead_terminal(parser, "STRING", 0)
    while cond657
        item658 = consume_terminal!(parser, "STRING")
        push!(xs656, item658)
        cond657 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings659 = xs656
    consume_literal!(parser, ")")
    return strings659
end

function parse_csv_locator_inline_data(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string660 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string660
end

function parse_csv_config(parser::Parser)::Proto.CSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1245 = parse_config_dict(parser)
    config_dict661 = _t1245
    consume_literal!(parser, ")")
    _t1246 = construct_csv_config(parser, config_dict661)
    return _t1246
end

function parse_csv_columns(parser::Parser)::Vector{Proto.CSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs662 = Proto.CSVColumn[]
    cond663 = match_lookahead_literal(parser, "(", 0)
    while cond663
        _t1247 = parse_csv_column(parser)
        item664 = _t1247
        push!(xs662, item664)
        cond663 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns665 = xs662
    consume_literal!(parser, ")")
    return csv_columns665
end

function parse_csv_column(parser::Parser)::Proto.CSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string666 = consume_terminal!(parser, "STRING")
    _t1248 = parse_relation_id(parser)
    relation_id667 = _t1248
    consume_literal!(parser, "[")
    xs668 = Proto.var"#Type"[]
    cond669 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond669
        _t1249 = parse_type(parser)
        item670 = _t1249
        push!(xs668, item670)
        cond669 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types671 = xs668
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1250 = Proto.CSVColumn(column_name=string666, target_id=relation_id667, types=types671)
    return _t1250
end

function parse_csv_asof(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string672 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string672
end

function parse_undefine(parser::Parser)::Proto.Undefine
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1251 = parse_fragment_id(parser)
    fragment_id673 = _t1251
    consume_literal!(parser, ")")
    _t1252 = Proto.Undefine(fragment_id=fragment_id673)
    return _t1252
end

function parse_context(parser::Parser)::Proto.Context
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs674 = Proto.RelationId[]
    cond675 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond675
        _t1253 = parse_relation_id(parser)
        item676 = _t1253
        push!(xs674, item676)
        cond675 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids677 = xs674
    consume_literal!(parser, ")")
    _t1254 = Proto.Context(relations=relation_ids677)
    return _t1254
end

function parse_epoch_reads(parser::Parser)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs678 = Proto.Read[]
    cond679 = match_lookahead_literal(parser, "(", 0)
    while cond679
        _t1255 = parse_read(parser)
        item680 = _t1255
        push!(xs678, item680)
        cond679 = match_lookahead_literal(parser, "(", 0)
    end
    reads681 = xs678
    consume_literal!(parser, ")")
    return reads681
end

function parse_read(parser::Parser)::Proto.Read
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1257 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1258 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1259 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1260 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1261 = 3
                        else
                            _t1261 = -1
                        end
                        _t1260 = _t1261
                    end
                    _t1259 = _t1260
                end
                _t1258 = _t1259
            end
            _t1257 = _t1258
        end
        _t1256 = _t1257
    else
        _t1256 = -1
    end
    prediction682 = _t1256
    if prediction682 == 4
        _t1263 = parse_export(parser)
        export687 = _t1263
        _t1264 = Proto.Read(read_type=OneOf(:var"#export", export687))
        _t1262 = _t1264
    else
        if prediction682 == 3
            _t1266 = parse_abort(parser)
            abort686 = _t1266
            _t1267 = Proto.Read(read_type=OneOf(:abort, abort686))
            _t1265 = _t1267
        else
            if prediction682 == 2
                _t1269 = parse_what_if(parser)
                what_if685 = _t1269
                _t1270 = Proto.Read(read_type=OneOf(:what_if, what_if685))
                _t1268 = _t1270
            else
                if prediction682 == 1
                    _t1272 = parse_output(parser)
                    output684 = _t1272
                    _t1273 = Proto.Read(read_type=OneOf(:output, output684))
                    _t1271 = _t1273
                else
                    if prediction682 == 0
                        _t1275 = parse_demand(parser)
                        demand683 = _t1275
                        _t1276 = Proto.Read(read_type=OneOf(:demand, demand683))
                        _t1274 = _t1276
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1271 = _t1274
                end
                _t1268 = _t1271
            end
            _t1265 = _t1268
        end
        _t1262 = _t1265
    end
    return _t1262
end

function parse_demand(parser::Parser)::Proto.Demand
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1277 = parse_relation_id(parser)
    relation_id688 = _t1277
    consume_literal!(parser, ")")
    _t1278 = Proto.Demand(relation_id=relation_id688)
    return _t1278
end

function parse_output(parser::Parser)::Proto.Output
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1279 = parse_name(parser)
    name689 = _t1279
    _t1280 = parse_relation_id(parser)
    relation_id690 = _t1280
    consume_literal!(parser, ")")
    _t1281 = Proto.Output(name=name689, relation_id=relation_id690)
    return _t1281
end

function parse_what_if(parser::Parser)::Proto.WhatIf
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1282 = parse_name(parser)
    name691 = _t1282
    _t1283 = parse_epoch(parser)
    epoch692 = _t1283
    consume_literal!(parser, ")")
    _t1284 = Proto.WhatIf(branch=name691, epoch=epoch692)
    return _t1284
end

function parse_abort(parser::Parser)::Proto.Abort
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1286 = parse_name(parser)
        _t1285 = _t1286
    else
        _t1285 = nothing
    end
    name693 = _t1285
    _t1287 = parse_relation_id(parser)
    relation_id694 = _t1287
    consume_literal!(parser, ")")
    _t1288 = Proto.Abort(name=(!isnothing(name693) ? name693 : "abort"), relation_id=relation_id694)
    return _t1288
end

function parse_export(parser::Parser)::Proto.Export
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1289 = parse_export_csv_config(parser)
    export_csv_config695 = _t1289
    consume_literal!(parser, ")")
    _t1290 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config695))
    return _t1290
end

function parse_export_csv_config(parser::Parser)::Proto.ExportCSVConfig
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1291 = parse_export_csv_path(parser)
    export_csv_path696 = _t1291
    _t1292 = parse_export_csv_columns(parser)
    export_csv_columns697 = _t1292
    _t1293 = parse_config_dict(parser)
    config_dict698 = _t1293
    consume_literal!(parser, ")")
    _t1294 = export_csv_config(parser, export_csv_path696, export_csv_columns697, config_dict698)
    return _t1294
end

function parse_export_csv_path(parser::Parser)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string699 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string699
end

function parse_export_csv_columns(parser::Parser)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs700 = Proto.ExportCSVColumn[]
    cond701 = match_lookahead_literal(parser, "(", 0)
    while cond701
        _t1295 = parse_export_csv_column(parser)
        item702 = _t1295
        push!(xs700, item702)
        cond701 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns703 = xs700
    consume_literal!(parser, ")")
    return export_csv_columns703
end

function parse_export_csv_column(parser::Parser)::Proto.ExportCSVColumn
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string704 = consume_terminal!(parser, "STRING")
    _t1296 = parse_relation_id(parser)
    relation_id705 = _t1296
    consume_literal!(parser, ")")
    _t1297 = Proto.ExportCSVColumn(column_name=string704, column_data=relation_id705)
    return _t1297
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
