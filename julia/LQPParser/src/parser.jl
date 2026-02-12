"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


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


struct Location
    line::Int
    column::Int
    offset::Int
end

struct Span
    start_::Location
    end_::Location
end

struct Token
    type::String
    value::Any
    start_pos::Int
    end_pos::Int
end

Base.show(io::IO, t::Token) = print(io, "Token(", t.type, ", ", repr(t.value), ", ", t.start_pos, ")")


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
        push!(lexer.tokens, Token(token_type, action(value), lexer.pos, end_pos))
        lexer.pos = end_pos
    end

    push!(lexer.tokens, Token("\$", "", lexer.pos, lexer.pos))
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
    provenance::Dict{Tuple{Vararg{Int}},Span}
    _path::Vector{Int}
    _line_starts::Vector{Int}

    function Parser(tokens::Vector{Token}, input::String)
        line_starts = _compute_line_starts(input)
        return new(tokens, 1, Dict(), nothing, Dict(), Dict(), Int[], line_starts)
    end
end

function _compute_line_starts(text::String)::Vector{Int}
    starts = [0]
    for (i, ch) in enumerate(text)
        if ch == '\n'
            push!(starts, i)
        end
    end
    return starts
end


function lookahead(parser::Parser, k::Int=0)::Token
    idx = parser.pos + k
    return idx <= length(parser.tokens) ? parser.tokens[idx] : Token("\$", "", -1, -1)
end


function consume_literal!(parser::Parser, expected::String)
    if !match_lookahead_literal(parser, expected, 0)
        token = lookahead(parser, 0)
        throw(ParseError("Expected literal $(repr(expected)) but got $(token.type)=`$(repr(token.value))` at position $(token.start_pos)"))
    end
    parser.pos += 1
    return nothing
end


function consume_terminal!(parser::Parser, expected::String)
    if !match_lookahead_terminal(parser, expected, 0)
        token = lookahead(parser, 0)
        throw(ParseError("Expected terminal $expected but got $(token.type)=`$(repr(token.value))` at position $(token.start_pos)"))
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


function push_path!(parser::Parser, n::Int)
    push!(parser._path, n)
    return nothing
end

function pop_path!(parser::Parser)
    pop!(parser._path)
    return nothing
end

function span_start(parser::Parser)::Int
    return parser.tokens[parser.pos].start_pos
end

function record_span!(parser::Parser, start_offset::Int)
    end_offset = parser.tokens[parser.pos - 1].end_pos
    start_loc = _make_location(parser, start_offset)
    end_loc = _make_location(parser, end_offset)
    parser.provenance[Tuple(parser._path)] = Span(start_loc, end_loc)
    return nothing
end

function _make_location(parser::Parser, offset::Int)::Location
    # Binary search for the line containing offset
    line = searchsortedlast(parser._line_starts, offset)
    column = offset - parser._line_starts[line] + 1
    return Location(line, column, offset)
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
    _t1211 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1211
    _t1212 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1212
    _t1213 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1213
    _t1214 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1214
    _t1215 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1215
    _t1216 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1216
    _t1217 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1217
    _t1218 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1218
    _t1219 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1219
    _t1220 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1220
    _t1221 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1221
    _t1222 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
    return _t1222
end

function construct_betree_info(parser::Parser, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1223 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1223
    _t1224 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1224
    _t1225 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1225
    _t1226 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1226
    _t1227 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1227
    _t1228 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1228
    _t1229 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1229
    _t1230 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1230
    _t1231 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1231
    _t1232 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1232
    _t1233 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1233
end

function default_configure(parser::Parser)::Proto.Configure
    _t1234 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1234
    _t1235 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1235
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
    _t1236 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1236
    _t1237 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1237
    _t1238 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1238
end

function export_csv_config(parser::Parser, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1239 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1239
    _t1240 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1240
    _t1241 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1241
    _t1242 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1242
    _t1243 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1243
    _t1244 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1244
    _t1245 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1245
    _t1246 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1246
end

function _make_value_int32(parser::Parser, v::Int32)::Proto.Value
    _t1247 = Proto.Value(value=OneOf(:int_value, Int64(v)))
    return _t1247
end

function _make_value_int64(parser::Parser, v::Int64)::Proto.Value
    _t1248 = Proto.Value(value=OneOf(:int_value, v))
    return _t1248
end

function _make_value_float64(parser::Parser, v::Float64)::Proto.Value
    _t1249 = Proto.Value(value=OneOf(:float_value, v))
    return _t1249
end

function _make_value_string(parser::Parser, v::String)::Proto.Value
    _t1250 = Proto.Value(value=OneOf(:string_value, v))
    return _t1250
end

function _make_value_boolean(parser::Parser, v::Bool)::Proto.Value
    _t1251 = Proto.Value(value=OneOf(:boolean_value, v))
    return _t1251
end

function _make_value_uint128(parser::Parser, v::Proto.UInt128Value)::Proto.Value
    _t1252 = Proto.Value(value=OneOf(:uint128_value, v))
    return _t1252
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
        _t1254 = _make_value_string(parser, "auto")
        push!(result, ("ivm.maintenance_level", _t1254,))
        _t1253 = nothing
    else
        
        if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
            _t1256 = _make_value_string(parser, "all")
            push!(result, ("ivm.maintenance_level", _t1256,))
            _t1255 = nothing
        else
            
            if msg.ivm_config.level == Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
                _t1258 = _make_value_string(parser, "off")
                push!(result, ("ivm.maintenance_level", _t1258,))
                _t1257 = nothing
            else
                _t1257 = nothing
            end
            _t1255 = _t1257
        end
        _t1253 = _t1255
    end
    _t1259 = _make_value_int64(parser, msg.semantics_version)
    push!(result, ("semantics_version", _t1259,))
    return sort(result)
end

function deconstruct_csv_config(parser::Parser, msg::Proto.CSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1260 = _make_value_int32(parser, msg.header_row)
    push!(result, ("csv_header_row", _t1260,))
    _t1261 = _make_value_int64(parser, msg.skip)
    push!(result, ("csv_skip", _t1261,))
    
    if msg.new_line != ""
        _t1263 = _make_value_string(parser, msg.new_line)
        push!(result, ("csv_new_line", _t1263,))
        _t1262 = nothing
    else
        _t1262 = nothing
    end
    _t1264 = _make_value_string(parser, msg.delimiter)
    push!(result, ("csv_delimiter", _t1264,))
    _t1265 = _make_value_string(parser, msg.quotechar)
    push!(result, ("csv_quotechar", _t1265,))
    _t1266 = _make_value_string(parser, msg.escapechar)
    push!(result, ("csv_escapechar", _t1266,))
    
    if msg.comment != ""
        _t1268 = _make_value_string(parser, msg.comment)
        push!(result, ("csv_comment", _t1268,))
        _t1267 = nothing
    else
        _t1267 = nothing
    end
    for missing_string in msg.missing_strings
        _t1269 = _make_value_string(parser, missing_string)
        push!(result, ("csv_missing_strings", _t1269,))
    end
    _t1270 = _make_value_string(parser, msg.decimal_separator)
    push!(result, ("csv_decimal_separator", _t1270,))
    _t1271 = _make_value_string(parser, msg.encoding)
    push!(result, ("csv_encoding", _t1271,))
    _t1272 = _make_value_string(parser, msg.compression)
    push!(result, ("csv_compression", _t1272,))
    return sort(result)
end

function _maybe_push_float64(parser::Parser, result::Vector{Tuple{String, Proto.Value}}, key::String, val::Union{Nothing, Float64})::Nothing
    
    if !isnothing(val)
        _t1274 = _make_value_float64(parser, val)
        push!(result, (key, _t1274,))
        _t1273 = nothing
    else
        _t1273 = nothing
    end
    return nothing
end

function _maybe_push_int64(parser::Parser, result::Vector{Tuple{String, Proto.Value}}, key::String, val::Union{Nothing, Int64})::Nothing
    
    if !isnothing(val)
        _t1276 = _make_value_int64(parser, val)
        push!(result, (key, _t1276,))
        _t1275 = nothing
    else
        _t1275 = nothing
    end
    return nothing
end

function _maybe_push_uint128(parser::Parser, result::Vector{Tuple{String, Proto.Value}}, key::String, val::Union{Nothing, Proto.UInt128Value})::Nothing
    
    if !isnothing(val)
        _t1278 = _make_value_uint128(parser, val)
        push!(result, (key, _t1278,))
        _t1277 = nothing
    else
        _t1277 = nothing
    end
    return nothing
end

function _maybe_push_bytes_as_string(parser::Parser, result::Vector{Tuple{String, Proto.Value}}, key::String, val::Union{Nothing, Vector{UInt8}})::Nothing
    
    if !isnothing(val)
        _t1280 = _make_value_string(parser, String(val))
        push!(result, (key, _t1280,))
        _t1279 = nothing
    else
        _t1279 = nothing
    end
    return nothing
end

function deconstruct_betree_info_config(parser::Parser, msg::Proto.BeTreeInfo)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    _t1281 = _make_value_float64(parser, msg.storage_config.epsilon)
    push!(result, ("betree_config_epsilon", _t1281,))
    _t1282 = _make_value_int64(parser, msg.storage_config.max_pivots)
    push!(result, ("betree_config_max_pivots", _t1282,))
    _t1283 = _make_value_int64(parser, msg.storage_config.max_deltas)
    push!(result, ("betree_config_max_deltas", _t1283,))
    _t1284 = _make_value_int64(parser, msg.storage_config.max_leaf)
    push!(result, ("betree_config_max_leaf", _t1284,))
    
    if _has_proto_field(msg.relation_locator, Symbol("root_pageid"))
        _t1286 = _maybe_push_uint128(parser, result, "betree_locator_root_pageid", _get_oneof_field(msg.relation_locator, :root_pageid))
        _t1285 = _t1286
    else
        _t1285 = nothing
    end
    
    if _has_proto_field(msg.relation_locator, Symbol("inline_data"))
        _t1288 = _maybe_push_bytes_as_string(parser, result, "betree_locator_inline_data", _get_oneof_field(msg.relation_locator, :inline_data))
        _t1287 = _t1288
    else
        _t1287 = nothing
    end
    _t1289 = _make_value_int64(parser, msg.relation_locator.element_count)
    push!(result, ("betree_locator_element_count", _t1289,))
    _t1290 = _make_value_int64(parser, msg.relation_locator.tree_height)
    push!(result, ("betree_locator_tree_height", _t1290,))
    return sort(result)
end

function deconstruct_export_csv_config(parser::Parser, msg::Proto.ExportCSVConfig)::Vector{Tuple{String, Proto.Value}}
    result = Tuple{String, Proto.Value}[]
    
    if !isnothing(msg.partition_size)
        _t1292 = _make_value_int64(parser, msg.partition_size)
        push!(result, ("partition_size", _t1292,))
        _t1291 = nothing
    else
        _t1291 = nothing
    end
    
    if !isnothing(msg.compression)
        _t1294 = _make_value_string(parser, msg.compression)
        push!(result, ("compression", _t1294,))
        _t1293 = nothing
    else
        _t1293 = nothing
    end
    
    if !isnothing(msg.syntax_header_row)
        _t1296 = _make_value_boolean(parser, msg.syntax_header_row)
        push!(result, ("syntax_header_row", _t1296,))
        _t1295 = nothing
    else
        _t1295 = nothing
    end
    
    if !isnothing(msg.syntax_missing_string)
        _t1298 = _make_value_string(parser, msg.syntax_missing_string)
        push!(result, ("syntax_missing_string", _t1298,))
        _t1297 = nothing
    else
        _t1297 = nothing
    end
    
    if !isnothing(msg.syntax_delim)
        _t1300 = _make_value_string(parser, msg.syntax_delim)
        push!(result, ("syntax_delim", _t1300,))
        _t1299 = nothing
    else
        _t1299 = nothing
    end
    
    if !isnothing(msg.syntax_quotechar)
        _t1302 = _make_value_string(parser, msg.syntax_quotechar)
        push!(result, ("syntax_quotechar", _t1302,))
        _t1301 = nothing
    else
        _t1301 = nothing
    end
    
    if !isnothing(msg.syntax_escapechar)
        _t1304 = _make_value_string(parser, msg.syntax_escapechar)
        push!(result, ("syntax_escapechar", _t1304,))
        _t1303 = nothing
    else
        _t1303 = nothing
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
    span_start7 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    push_path!(parser, 2)
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t620 = parse_configure(parser)
        _t619 = _t620
    else
        _t619 = nothing
    end
    configure0 = _t619
    pop_path!(parser)
    push_path!(parser, 3)
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t622 = parse_sync(parser)
        _t621 = _t622
    else
        _t621 = nothing
    end
    sync1 = _t621
    pop_path!(parser)
    push_path!(parser, 1)
    xs2 = Proto.Epoch[]
    cond3 = match_lookahead_literal(parser, "(", 0)
    idx5 = 0
    while cond3
        push_path!(parser, idx5)
        _t623 = parse_epoch(parser)
        item4 = _t623
        pop_path!(parser)
        push!(xs2, item4)
        idx5 = (idx5 + 1)
        cond3 = match_lookahead_literal(parser, "(", 0)
    end
    pop_path!(parser)
    epochs6 = xs2
    consume_literal!(parser, ")")
    _t624 = default_configure(parser)
    _t625 = Proto.Transaction(epochs=epochs6, configure=(!isnothing(configure0) ? configure0 : _t624), sync=sync1)
    result8 = _t625
    record_span!(parser, span_start7)
    return result8
end

function parse_configure(parser::Parser)::Proto.Configure
    span_start10 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t626 = parse_config_dict(parser)
    config_dict9 = _t626
    consume_literal!(parser, ")")
    _t627 = construct_configure(parser, config_dict9)
    result11 = _t627
    record_span!(parser, span_start10)
    return result11
end

function parse_config_dict(parser::Parser)::Vector{Tuple{String, Proto.Value}}
    span_start17 = span_start(parser)
    consume_literal!(parser, "{")
    xs12 = Tuple{String, Proto.Value}[]
    cond13 = match_lookahead_literal(parser, ":", 0)
    idx15 = 0
    while cond13
        push_path!(parser, idx15)
        _t628 = parse_config_key_value(parser)
        item14 = _t628
        pop_path!(parser)
        push!(xs12, item14)
        idx15 = (idx15 + 1)
        cond13 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values16 = xs12
    consume_literal!(parser, "}")
    result18 = config_key_values16
    record_span!(parser, span_start17)
    return result18
end

function parse_config_key_value(parser::Parser)::Tuple{String, Proto.Value}
    span_start21 = span_start(parser)
    consume_literal!(parser, ":")
    symbol19 = consume_terminal!(parser, "SYMBOL")
    _t629 = parse_value(parser)
    value20 = _t629
    result22 = (symbol19, value20,)
    record_span!(parser, span_start21)
    return result22
end

function parse_value(parser::Parser)::Proto.Value
    span_start33 = span_start(parser)
    
    if match_lookahead_literal(parser, "true", 0)
        _t630 = 9
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t631 = 8
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t632 = 9
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t634 = 1
                    else
                        
                        if match_lookahead_literal(parser, "date", 1)
                            _t635 = 0
                        else
                            _t635 = -1
                        end
                        _t634 = _t635
                    end
                    _t633 = _t634
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t636 = 5
                    else
                        
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t637 = 2
                        else
                            
                            if match_lookahead_terminal(parser, "INT128", 0)
                                _t638 = 6
                            else
                                
                                if match_lookahead_terminal(parser, "INT", 0)
                                    _t639 = 3
                                else
                                    
                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                        _t640 = 4
                                    else
                                        
                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                            _t641 = 7
                                        else
                                            _t641 = -1
                                        end
                                        _t640 = _t641
                                    end
                                    _t639 = _t640
                                end
                                _t638 = _t639
                            end
                            _t637 = _t638
                        end
                        _t636 = _t637
                    end
                    _t633 = _t636
                end
                _t632 = _t633
            end
            _t631 = _t632
        end
        _t630 = _t631
    end
    prediction23 = _t630
    
    if prediction23 == 9
        _t643 = parse_boolean_value(parser)
        boolean_value32 = _t643
        _t644 = Proto.Value(value=OneOf(:boolean_value, boolean_value32))
        _t642 = _t644
    else
        
        if prediction23 == 8
            consume_literal!(parser, "missing")
            _t646 = Proto.MissingValue()
            _t647 = Proto.Value(value=OneOf(:missing_value, _t646))
            _t645 = _t647
        else
            
            if prediction23 == 7
                decimal31 = consume_terminal!(parser, "DECIMAL")
                _t649 = Proto.Value(value=OneOf(:decimal_value, decimal31))
                _t648 = _t649
            else
                
                if prediction23 == 6
                    int12830 = consume_terminal!(parser, "INT128")
                    _t651 = Proto.Value(value=OneOf(:int128_value, int12830))
                    _t650 = _t651
                else
                    
                    if prediction23 == 5
                        uint12829 = consume_terminal!(parser, "UINT128")
                        _t653 = Proto.Value(value=OneOf(:uint128_value, uint12829))
                        _t652 = _t653
                    else
                        
                        if prediction23 == 4
                            float28 = consume_terminal!(parser, "FLOAT")
                            _t655 = Proto.Value(value=OneOf(:float_value, float28))
                            _t654 = _t655
                        else
                            
                            if prediction23 == 3
                                int27 = consume_terminal!(parser, "INT")
                                _t657 = Proto.Value(value=OneOf(:int_value, int27))
                                _t656 = _t657
                            else
                                
                                if prediction23 == 2
                                    string26 = consume_terminal!(parser, "STRING")
                                    _t659 = Proto.Value(value=OneOf(:string_value, string26))
                                    _t658 = _t659
                                else
                                    
                                    if prediction23 == 1
                                        _t661 = parse_datetime(parser)
                                        datetime25 = _t661
                                        _t662 = Proto.Value(value=OneOf(:datetime_value, datetime25))
                                        _t660 = _t662
                                    else
                                        
                                        if prediction23 == 0
                                            _t664 = parse_date(parser)
                                            date24 = _t664
                                            _t665 = Proto.Value(value=OneOf(:date_value, date24))
                                            _t663 = _t665
                                        else
                                            throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t660 = _t663
                                    end
                                    _t658 = _t660
                                end
                                _t656 = _t658
                            end
                            _t654 = _t656
                        end
                        _t652 = _t654
                    end
                    _t650 = _t652
                end
                _t648 = _t650
            end
            _t645 = _t648
        end
        _t642 = _t645
    end
    result34 = _t642
    record_span!(parser, span_start33)
    return result34
end

function parse_date(parser::Parser)::Proto.DateValue
    span_start38 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    push_path!(parser, 1)
    int35 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_336 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 3)
    int_437 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t666 = Proto.DateValue(year=Int32(int35), month=Int32(int_336), day=Int32(int_437))
    result39 = _t666
    record_span!(parser, span_start38)
    return result39
end

function parse_datetime(parser::Parser)::Proto.DateTimeValue
    span_start47 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    push_path!(parser, 1)
    int40 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_341 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 3)
    int_442 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 4)
    int_543 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 5)
    int_644 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 6)
    int_745 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    
    if match_lookahead_terminal(parser, "INT", 0)
        _t667 = consume_terminal!(parser, "INT")
    else
        _t667 = nothing
    end
    int_846 = _t667
    consume_literal!(parser, ")")
    _t668 = Proto.DateTimeValue(year=Int32(int40), month=Int32(int_341), day=Int32(int_442), hour=Int32(int_543), minute=Int32(int_644), second=Int32(int_745), microsecond=Int32((!isnothing(int_846) ? int_846 : 0)))
    result48 = _t668
    record_span!(parser, span_start47)
    return result48
end

function parse_boolean_value(parser::Parser)::Bool
    span_start50 = span_start(parser)
    
    if match_lookahead_literal(parser, "true", 0)
        _t669 = 0
    else
        
        if match_lookahead_literal(parser, "false", 0)
            _t670 = 1
        else
            _t670 = -1
        end
        _t669 = _t670
    end
    prediction49 = _t669
    
    if prediction49 == 1
        consume_literal!(parser, "false")
        _t671 = false
    else
        
        if prediction49 == 0
            consume_literal!(parser, "true")
            _t672 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t671 = _t672
    end
    result51 = _t671
    record_span!(parser, span_start50)
    return result51
end

function parse_sync(parser::Parser)::Proto.Sync
    span_start57 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    push_path!(parser, 1)
    xs52 = Proto.FragmentId[]
    cond53 = match_lookahead_literal(parser, ":", 0)
    idx55 = 0
    while cond53
        push_path!(parser, idx55)
        _t673 = parse_fragment_id(parser)
        item54 = _t673
        pop_path!(parser)
        push!(xs52, item54)
        idx55 = (idx55 + 1)
        cond53 = match_lookahead_literal(parser, ":", 0)
    end
    pop_path!(parser)
    fragment_ids56 = xs52
    consume_literal!(parser, ")")
    _t674 = Proto.Sync(fragments=fragment_ids56)
    result58 = _t674
    record_span!(parser, span_start57)
    return result58
end

function parse_fragment_id(parser::Parser)::Proto.FragmentId
    span_start60 = span_start(parser)
    consume_literal!(parser, ":")
    symbol59 = consume_terminal!(parser, "SYMBOL")
    result61 = Proto.FragmentId(Vector{UInt8}(symbol59))
    record_span!(parser, span_start60)
    return result61
end

function parse_epoch(parser::Parser)::Proto.Epoch
    span_start64 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    push_path!(parser, 1)
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t676 = parse_epoch_writes(parser)
        _t675 = _t676
    else
        _t675 = nothing
    end
    epoch_writes62 = _t675
    pop_path!(parser)
    push_path!(parser, 2)
    
    if match_lookahead_literal(parser, "(", 0)
        _t678 = parse_epoch_reads(parser)
        _t677 = _t678
    else
        _t677 = nothing
    end
    epoch_reads63 = _t677
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t679 = Proto.Epoch(writes=(!isnothing(epoch_writes62) ? epoch_writes62 : Proto.Write[]), reads=(!isnothing(epoch_reads63) ? epoch_reads63 : Proto.Read[]))
    result65 = _t679
    record_span!(parser, span_start64)
    return result65
end

function parse_epoch_writes(parser::Parser)::Vector{Proto.Write}
    span_start71 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs66 = Proto.Write[]
    cond67 = match_lookahead_literal(parser, "(", 0)
    idx69 = 0
    while cond67
        push_path!(parser, idx69)
        _t680 = parse_write(parser)
        item68 = _t680
        pop_path!(parser)
        push!(xs66, item68)
        idx69 = (idx69 + 1)
        cond67 = match_lookahead_literal(parser, "(", 0)
    end
    writes70 = xs66
    consume_literal!(parser, ")")
    result72 = writes70
    record_span!(parser, span_start71)
    return result72
end

function parse_write(parser::Parser)::Proto.Write
    span_start77 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "undefine", 1)
            _t682 = 1
        else
            
            if match_lookahead_literal(parser, "define", 1)
                _t683 = 0
            else
                
                if match_lookahead_literal(parser, "context", 1)
                    _t684 = 2
                else
                    _t684 = -1
                end
                _t683 = _t684
            end
            _t682 = _t683
        end
        _t681 = _t682
    else
        _t681 = -1
    end
    prediction73 = _t681
    
    if prediction73 == 2
        _t686 = parse_context(parser)
        context76 = _t686
        _t687 = Proto.Write(write_type=OneOf(:context, context76))
        _t685 = _t687
    else
        
        if prediction73 == 1
            _t689 = parse_undefine(parser)
            undefine75 = _t689
            _t690 = Proto.Write(write_type=OneOf(:undefine, undefine75))
            _t688 = _t690
        else
            
            if prediction73 == 0
                _t692 = parse_define(parser)
                define74 = _t692
                _t693 = Proto.Write(write_type=OneOf(:define, define74))
                _t691 = _t693
            else
                throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
            end
            _t688 = _t691
        end
        _t685 = _t688
    end
    result78 = _t685
    record_span!(parser, span_start77)
    return result78
end

function parse_define(parser::Parser)::Proto.Define
    span_start80 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    push_path!(parser, 1)
    _t694 = parse_fragment(parser)
    fragment79 = _t694
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t695 = Proto.Define(fragment=fragment79)
    result81 = _t695
    record_span!(parser, span_start80)
    return result81
end

function parse_fragment(parser::Parser)::Proto.Fragment
    span_start88 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t696 = parse_new_fragment_id(parser)
    new_fragment_id82 = _t696
    xs83 = Proto.Declaration[]
    cond84 = match_lookahead_literal(parser, "(", 0)
    idx86 = 0
    while cond84
        push_path!(parser, idx86)
        _t697 = parse_declaration(parser)
        item85 = _t697
        pop_path!(parser)
        push!(xs83, item85)
        idx86 = (idx86 + 1)
        cond84 = match_lookahead_literal(parser, "(", 0)
    end
    declarations87 = xs83
    consume_literal!(parser, ")")
    result89 = construct_fragment(parser, new_fragment_id82, declarations87)
    record_span!(parser, span_start88)
    return result89
end

function parse_new_fragment_id(parser::Parser)::Proto.FragmentId
    span_start91 = span_start(parser)
    _t698 = parse_fragment_id(parser)
    fragment_id90 = _t698
    start_fragment!(parser, fragment_id90)
    result92 = fragment_id90
    record_span!(parser, span_start91)
    return result92
end

function parse_declaration(parser::Parser)::Proto.Declaration
    span_start98 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t700 = 3
        else
            
            if match_lookahead_literal(parser, "functional_dependency", 1)
                _t701 = 2
            else
                
                if match_lookahead_literal(parser, "def", 1)
                    _t702 = 0
                else
                    
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t703 = 3
                    else
                        
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t704 = 3
                        else
                            
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t705 = 1
                            else
                                _t705 = -1
                            end
                            _t704 = _t705
                        end
                        _t703 = _t704
                    end
                    _t702 = _t703
                end
                _t701 = _t702
            end
            _t700 = _t701
        end
        _t699 = _t700
    else
        _t699 = -1
    end
    prediction93 = _t699
    
    if prediction93 == 3
        _t707 = parse_data(parser)
        data97 = _t707
        _t708 = Proto.Declaration(declaration_type=OneOf(:data, data97))
        _t706 = _t708
    else
        
        if prediction93 == 2
            _t710 = parse_constraint(parser)
            constraint96 = _t710
            _t711 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint96))
            _t709 = _t711
        else
            
            if prediction93 == 1
                _t713 = parse_algorithm(parser)
                algorithm95 = _t713
                _t714 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm95))
                _t712 = _t714
            else
                
                if prediction93 == 0
                    _t716 = parse_def(parser)
                    def94 = _t716
                    _t717 = Proto.Declaration(declaration_type=OneOf(:def, def94))
                    _t715 = _t717
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t712 = _t715
            end
            _t709 = _t712
        end
        _t706 = _t709
    end
    result99 = _t706
    record_span!(parser, span_start98)
    return result99
end

function parse_def(parser::Parser)::Proto.Def
    span_start103 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    push_path!(parser, 1)
    _t718 = parse_relation_id(parser)
    relation_id100 = _t718
    pop_path!(parser)
    push_path!(parser, 2)
    _t719 = parse_abstraction(parser)
    abstraction101 = _t719
    pop_path!(parser)
    push_path!(parser, 3)
    
    if match_lookahead_literal(parser, "(", 0)
        _t721 = parse_attrs(parser)
        _t720 = _t721
    else
        _t720 = nothing
    end
    attrs102 = _t720
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t722 = Proto.Def(name=relation_id100, body=abstraction101, attrs=(!isnothing(attrs102) ? attrs102 : Proto.Attribute[]))
    result104 = _t722
    record_span!(parser, span_start103)
    return result104
end

function parse_relation_id(parser::Parser)::Proto.RelationId
    span_start108 = span_start(parser)
    
    if match_lookahead_literal(parser, ":", 0)
        _t723 = 0
    else
        
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t724 = 1
        else
            _t724 = -1
        end
        _t723 = _t724
    end
    prediction105 = _t723
    
    if prediction105 == 1
        uint128107 = consume_terminal!(parser, "UINT128")
        _t725 = Proto.RelationId(uint128107.low, uint128107.high)
    else
        
        if prediction105 == 0
            consume_literal!(parser, ":")
            symbol106 = consume_terminal!(parser, "SYMBOL")
            _t726 = relation_id_from_string(parser, symbol106)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t725 = _t726
    end
    result109 = _t725
    record_span!(parser, span_start108)
    return result109
end

function parse_abstraction(parser::Parser)::Proto.Abstraction
    span_start112 = span_start(parser)
    consume_literal!(parser, "(")
    _t727 = parse_bindings(parser)
    bindings110 = _t727
    push_path!(parser, 2)
    _t728 = parse_formula(parser)
    formula111 = _t728
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t729 = Proto.Abstraction(vars=vcat(bindings110[1], !isnothing(bindings110[2]) ? bindings110[2] : []), value=formula111)
    result113 = _t729
    record_span!(parser, span_start112)
    return result113
end

function parse_bindings(parser::Parser)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    span_start120 = span_start(parser)
    consume_literal!(parser, "[")
    xs114 = Proto.Binding[]
    cond115 = match_lookahead_terminal(parser, "SYMBOL", 0)
    idx117 = 0
    while cond115
        push_path!(parser, idx117)
        _t730 = parse_binding(parser)
        item116 = _t730
        pop_path!(parser)
        push!(xs114, item116)
        idx117 = (idx117 + 1)
        cond115 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings118 = xs114
    
    if match_lookahead_literal(parser, "|", 0)
        _t732 = parse_value_bindings(parser)
        _t731 = _t732
    else
        _t731 = nothing
    end
    value_bindings119 = _t731
    consume_literal!(parser, "]")
    result121 = (bindings118, (!isnothing(value_bindings119) ? value_bindings119 : Proto.Binding[]),)
    record_span!(parser, span_start120)
    return result121
end

function parse_binding(parser::Parser)::Proto.Binding
    span_start124 = span_start(parser)
    symbol122 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    push_path!(parser, 2)
    _t733 = parse_type(parser)
    type123 = _t733
    pop_path!(parser)
    _t734 = Proto.Var(name=symbol122)
    _t735 = Proto.Binding(var=_t734, var"#type"=type123)
    result125 = _t735
    record_span!(parser, span_start124)
    return result125
end

function parse_type(parser::Parser)::Proto.var"#Type"
    span_start138 = span_start(parser)
    
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t736 = 0
    else
        
        if match_lookahead_literal(parser, "UINT128", 0)
            _t737 = 4
        else
            
            if match_lookahead_literal(parser, "STRING", 0)
                _t738 = 1
            else
                
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t739 = 8
                else
                    
                    if match_lookahead_literal(parser, "INT128", 0)
                        _t740 = 5
                    else
                        
                        if match_lookahead_literal(parser, "INT", 0)
                            _t741 = 2
                        else
                            
                            if match_lookahead_literal(parser, "FLOAT", 0)
                                _t742 = 3
                            else
                                
                                if match_lookahead_literal(parser, "DATETIME", 0)
                                    _t743 = 7
                                else
                                    
                                    if match_lookahead_literal(parser, "DATE", 0)
                                        _t744 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "BOOLEAN", 0)
                                            _t745 = 10
                                        else
                                            
                                            if match_lookahead_literal(parser, "(", 0)
                                                _t746 = 9
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
    prediction126 = _t736
    
    if prediction126 == 10
        _t748 = parse_boolean_type(parser)
        boolean_type137 = _t748
        _t749 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type137))
        _t747 = _t749
    else
        
        if prediction126 == 9
            _t751 = parse_decimal_type(parser)
            decimal_type136 = _t751
            _t752 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type136))
            _t750 = _t752
        else
            
            if prediction126 == 8
                _t754 = parse_missing_type(parser)
                missing_type135 = _t754
                _t755 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type135))
                _t753 = _t755
            else
                
                if prediction126 == 7
                    _t757 = parse_datetime_type(parser)
                    datetime_type134 = _t757
                    _t758 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type134))
                    _t756 = _t758
                else
                    
                    if prediction126 == 6
                        _t760 = parse_date_type(parser)
                        date_type133 = _t760
                        _t761 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type133))
                        _t759 = _t761
                    else
                        
                        if prediction126 == 5
                            _t763 = parse_int128_type(parser)
                            int128_type132 = _t763
                            _t764 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type132))
                            _t762 = _t764
                        else
                            
                            if prediction126 == 4
                                _t766 = parse_uint128_type(parser)
                                uint128_type131 = _t766
                                _t767 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type131))
                                _t765 = _t767
                            else
                                
                                if prediction126 == 3
                                    _t769 = parse_float_type(parser)
                                    float_type130 = _t769
                                    _t770 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type130))
                                    _t768 = _t770
                                else
                                    
                                    if prediction126 == 2
                                        _t772 = parse_int_type(parser)
                                        int_type129 = _t772
                                        _t773 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type129))
                                        _t771 = _t773
                                    else
                                        
                                        if prediction126 == 1
                                            _t775 = parse_string_type(parser)
                                            string_type128 = _t775
                                            _t776 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type128))
                                            _t774 = _t776
                                        else
                                            
                                            if prediction126 == 0
                                                _t778 = parse_unspecified_type(parser)
                                                unspecified_type127 = _t778
                                                _t779 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type127))
                                                _t777 = _t779
                                            else
                                                throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                            end
                                            _t774 = _t777
                                        end
                                        _t771 = _t774
                                    end
                                    _t768 = _t771
                                end
                                _t765 = _t768
                            end
                            _t762 = _t765
                        end
                        _t759 = _t762
                    end
                    _t756 = _t759
                end
                _t753 = _t756
            end
            _t750 = _t753
        end
        _t747 = _t750
    end
    result139 = _t747
    record_span!(parser, span_start138)
    return result139
end

function parse_unspecified_type(parser::Parser)::Proto.UnspecifiedType
    span_start140 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t780 = Proto.UnspecifiedType()
    result141 = _t780
    record_span!(parser, span_start140)
    return result141
end

function parse_string_type(parser::Parser)::Proto.StringType
    span_start142 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t781 = Proto.StringType()
    result143 = _t781
    record_span!(parser, span_start142)
    return result143
end

function parse_int_type(parser::Parser)::Proto.IntType
    span_start144 = span_start(parser)
    consume_literal!(parser, "INT")
    _t782 = Proto.IntType()
    result145 = _t782
    record_span!(parser, span_start144)
    return result145
end

function parse_float_type(parser::Parser)::Proto.FloatType
    span_start146 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t783 = Proto.FloatType()
    result147 = _t783
    record_span!(parser, span_start146)
    return result147
end

function parse_uint128_type(parser::Parser)::Proto.UInt128Type
    span_start148 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t784 = Proto.UInt128Type()
    result149 = _t784
    record_span!(parser, span_start148)
    return result149
end

function parse_int128_type(parser::Parser)::Proto.Int128Type
    span_start150 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t785 = Proto.Int128Type()
    result151 = _t785
    record_span!(parser, span_start150)
    return result151
end

function parse_date_type(parser::Parser)::Proto.DateType
    span_start152 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t786 = Proto.DateType()
    result153 = _t786
    record_span!(parser, span_start152)
    return result153
end

function parse_datetime_type(parser::Parser)::Proto.DateTimeType
    span_start154 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t787 = Proto.DateTimeType()
    result155 = _t787
    record_span!(parser, span_start154)
    return result155
end

function parse_missing_type(parser::Parser)::Proto.MissingType
    span_start156 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t788 = Proto.MissingType()
    result157 = _t788
    record_span!(parser, span_start156)
    return result157
end

function parse_decimal_type(parser::Parser)::Proto.DecimalType
    span_start160 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    push_path!(parser, 1)
    int158 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    push_path!(parser, 2)
    int_3159 = consume_terminal!(parser, "INT")
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t789 = Proto.DecimalType(precision=Int32(int158), scale=Int32(int_3159))
    result161 = _t789
    record_span!(parser, span_start160)
    return result161
end

function parse_boolean_type(parser::Parser)::Proto.BooleanType
    span_start162 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t790 = Proto.BooleanType()
    result163 = _t790
    record_span!(parser, span_start162)
    return result163
end

function parse_value_bindings(parser::Parser)::Vector{Proto.Binding}
    span_start169 = span_start(parser)
    consume_literal!(parser, "|")
    xs164 = Proto.Binding[]
    cond165 = match_lookahead_terminal(parser, "SYMBOL", 0)
    idx167 = 0
    while cond165
        push_path!(parser, idx167)
        _t791 = parse_binding(parser)
        item166 = _t791
        pop_path!(parser)
        push!(xs164, item166)
        idx167 = (idx167 + 1)
        cond165 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings168 = xs164
    result170 = bindings168
    record_span!(parser, span_start169)
    return result170
end

function parse_formula(parser::Parser)::Proto.Formula
    span_start185 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "true", 1)
            _t793 = 0
        else
            
            if match_lookahead_literal(parser, "relatom", 1)
                _t794 = 11
            else
                
                if match_lookahead_literal(parser, "reduce", 1)
                    _t795 = 3
                else
                    
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t796 = 10
                    else
                        
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t797 = 9
                        else
                            
                            if match_lookahead_literal(parser, "or", 1)
                                _t798 = 5
                            else
                                
                                if match_lookahead_literal(parser, "not", 1)
                                    _t799 = 6
                                else
                                    
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t800 = 7
                                    else
                                        
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t801 = 1
                                        else
                                            
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t802 = 2
                                            else
                                                
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t803 = 12
                                                else
                                                    
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t804 = 8
                                                    else
                                                        
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t805 = 4
                                                        else
                                                            
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t806 = 10
                                                            else
                                                                
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t807 = 10
                                                                else
                                                                    
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t808 = 10
                                                                    else
                                                                        
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t809 = 10
                                                                        else
                                                                            
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t810 = 10
                                                                            else
                                                                                
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t811 = 10
                                                                                else
                                                                                    
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t812 = 10
                                                                                    else
                                                                                        
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t813 = 10
                                                                                        else
                                                                                            
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t814 = 10
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
                                                                    end
                                                                    _t807 = _t808
                                                                end
                                                                _t806 = _t807
                                                            end
                                                            _t805 = _t806
                                                        end
                                                        _t804 = _t805
                                                    end
                                                    _t803 = _t804
                                                end
                                                _t802 = _t803
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
                    end
                    _t795 = _t796
                end
                _t794 = _t795
            end
            _t793 = _t794
        end
        _t792 = _t793
    else
        _t792 = -1
    end
    prediction171 = _t792
    
    if prediction171 == 12
        _t816 = parse_cast(parser)
        cast184 = _t816
        _t817 = Proto.Formula(formula_type=OneOf(:cast, cast184))
        _t815 = _t817
    else
        
        if prediction171 == 11
            _t819 = parse_rel_atom(parser)
            rel_atom183 = _t819
            _t820 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom183))
            _t818 = _t820
        else
            
            if prediction171 == 10
                _t822 = parse_primitive(parser)
                primitive182 = _t822
                _t823 = Proto.Formula(formula_type=OneOf(:primitive, primitive182))
                _t821 = _t823
            else
                
                if prediction171 == 9
                    _t825 = parse_pragma(parser)
                    pragma181 = _t825
                    _t826 = Proto.Formula(formula_type=OneOf(:pragma, pragma181))
                    _t824 = _t826
                else
                    
                    if prediction171 == 8
                        _t828 = parse_atom(parser)
                        atom180 = _t828
                        _t829 = Proto.Formula(formula_type=OneOf(:atom, atom180))
                        _t827 = _t829
                    else
                        
                        if prediction171 == 7
                            _t831 = parse_ffi(parser)
                            ffi179 = _t831
                            _t832 = Proto.Formula(formula_type=OneOf(:ffi, ffi179))
                            _t830 = _t832
                        else
                            
                            if prediction171 == 6
                                _t834 = parse_not(parser)
                                not178 = _t834
                                _t835 = Proto.Formula(formula_type=OneOf(:not, not178))
                                _t833 = _t835
                            else
                                
                                if prediction171 == 5
                                    _t837 = parse_disjunction(parser)
                                    disjunction177 = _t837
                                    _t838 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction177))
                                    _t836 = _t838
                                else
                                    
                                    if prediction171 == 4
                                        _t840 = parse_conjunction(parser)
                                        conjunction176 = _t840
                                        _t841 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction176))
                                        _t839 = _t841
                                    else
                                        
                                        if prediction171 == 3
                                            _t843 = parse_reduce(parser)
                                            reduce175 = _t843
                                            _t844 = Proto.Formula(formula_type=OneOf(:reduce, reduce175))
                                            _t842 = _t844
                                        else
                                            
                                            if prediction171 == 2
                                                _t846 = parse_exists(parser)
                                                exists174 = _t846
                                                _t847 = Proto.Formula(formula_type=OneOf(:exists, exists174))
                                                _t845 = _t847
                                            else
                                                
                                                if prediction171 == 1
                                                    _t849 = parse_false(parser)
                                                    false173 = _t849
                                                    _t850 = Proto.Formula(formula_type=OneOf(:disjunction, false173))
                                                    _t848 = _t850
                                                else
                                                    
                                                    if prediction171 == 0
                                                        _t852 = parse_true(parser)
                                                        true172 = _t852
                                                        _t853 = Proto.Formula(formula_type=OneOf(:conjunction, true172))
                                                        _t851 = _t853
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t848 = _t851
                                                end
                                                _t845 = _t848
                                            end
                                            _t842 = _t845
                                        end
                                        _t839 = _t842
                                    end
                                    _t836 = _t839
                                end
                                _t833 = _t836
                            end
                            _t830 = _t833
                        end
                        _t827 = _t830
                    end
                    _t824 = _t827
                end
                _t821 = _t824
            end
            _t818 = _t821
        end
        _t815 = _t818
    end
    result186 = _t815
    record_span!(parser, span_start185)
    return result186
end

function parse_true(parser::Parser)::Proto.Conjunction
    span_start187 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t854 = Proto.Conjunction(args=Proto.Formula[])
    result188 = _t854
    record_span!(parser, span_start187)
    return result188
end

function parse_false(parser::Parser)::Proto.Disjunction
    span_start189 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t855 = Proto.Disjunction(args=Proto.Formula[])
    result190 = _t855
    record_span!(parser, span_start189)
    return result190
end

function parse_exists(parser::Parser)::Proto.Exists
    span_start193 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t856 = parse_bindings(parser)
    bindings191 = _t856
    _t857 = parse_formula(parser)
    formula192 = _t857
    consume_literal!(parser, ")")
    _t858 = Proto.Abstraction(vars=vcat(bindings191[1], !isnothing(bindings191[2]) ? bindings191[2] : []), value=formula192)
    _t859 = Proto.Exists(body=_t858)
    result194 = _t859
    record_span!(parser, span_start193)
    return result194
end

function parse_reduce(parser::Parser)::Proto.Reduce
    span_start198 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    push_path!(parser, 1)
    _t860 = parse_abstraction(parser)
    abstraction195 = _t860
    pop_path!(parser)
    push_path!(parser, 2)
    _t861 = parse_abstraction(parser)
    abstraction_3196 = _t861
    pop_path!(parser)
    push_path!(parser, 3)
    _t862 = parse_terms(parser)
    terms197 = _t862
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t863 = Proto.Reduce(op=abstraction195, body=abstraction_3196, terms=terms197)
    result199 = _t863
    record_span!(parser, span_start198)
    return result199
end

function parse_terms(parser::Parser)::Vector{Proto.Term}
    span_start205 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs200 = Proto.Term[]
    cond201 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx203 = 0
    while cond201
        push_path!(parser, idx203)
        _t864 = parse_term(parser)
        item202 = _t864
        pop_path!(parser)
        push!(xs200, item202)
        idx203 = (idx203 + 1)
        cond201 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms204 = xs200
    consume_literal!(parser, ")")
    result206 = terms204
    record_span!(parser, span_start205)
    return result206
end

function parse_term(parser::Parser)::Proto.Term
    span_start210 = span_start(parser)
    
    if match_lookahead_literal(parser, "true", 0)
        _t865 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t866 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t867 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t868 = 1
                else
                    
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t869 = 1
                    else
                        
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t870 = 0
                        else
                            
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t871 = 1
                            else
                                
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t872 = 1
                                else
                                    
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t873 = 1
                                    else
                                        
                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                            _t874 = 1
                                        else
                                            
                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                _t875 = 1
                                            else
                                                _t875 = -1
                                            end
                                            _t874 = _t875
                                        end
                                        _t873 = _t874
                                    end
                                    _t872 = _t873
                                end
                                _t871 = _t872
                            end
                            _t870 = _t871
                        end
                        _t869 = _t870
                    end
                    _t868 = _t869
                end
                _t867 = _t868
            end
            _t866 = _t867
        end
        _t865 = _t866
    end
    prediction207 = _t865
    
    if prediction207 == 1
        _t877 = parse_constant(parser)
        constant209 = _t877
        _t878 = Proto.Term(term_type=OneOf(:constant, constant209))
        _t876 = _t878
    else
        
        if prediction207 == 0
            _t880 = parse_var(parser)
            var208 = _t880
            _t881 = Proto.Term(term_type=OneOf(:var, var208))
            _t879 = _t881
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t876 = _t879
    end
    result211 = _t876
    record_span!(parser, span_start210)
    return result211
end

function parse_var(parser::Parser)::Proto.Var
    span_start213 = span_start(parser)
    symbol212 = consume_terminal!(parser, "SYMBOL")
    _t882 = Proto.Var(name=symbol212)
    result214 = _t882
    record_span!(parser, span_start213)
    return result214
end

function parse_constant(parser::Parser)::Proto.Value
    span_start216 = span_start(parser)
    _t883 = parse_value(parser)
    value215 = _t883
    result217 = value215
    record_span!(parser, span_start216)
    return result217
end

function parse_conjunction(parser::Parser)::Proto.Conjunction
    span_start223 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    push_path!(parser, 1)
    xs218 = Proto.Formula[]
    cond219 = match_lookahead_literal(parser, "(", 0)
    idx221 = 0
    while cond219
        push_path!(parser, idx221)
        _t884 = parse_formula(parser)
        item220 = _t884
        pop_path!(parser)
        push!(xs218, item220)
        idx221 = (idx221 + 1)
        cond219 = match_lookahead_literal(parser, "(", 0)
    end
    pop_path!(parser)
    formulas222 = xs218
    consume_literal!(parser, ")")
    _t885 = Proto.Conjunction(args=formulas222)
    result224 = _t885
    record_span!(parser, span_start223)
    return result224
end

function parse_disjunction(parser::Parser)::Proto.Disjunction
    span_start230 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    push_path!(parser, 1)
    xs225 = Proto.Formula[]
    cond226 = match_lookahead_literal(parser, "(", 0)
    idx228 = 0
    while cond226
        push_path!(parser, idx228)
        _t886 = parse_formula(parser)
        item227 = _t886
        pop_path!(parser)
        push!(xs225, item227)
        idx228 = (idx228 + 1)
        cond226 = match_lookahead_literal(parser, "(", 0)
    end
    pop_path!(parser)
    formulas229 = xs225
    consume_literal!(parser, ")")
    _t887 = Proto.Disjunction(args=formulas229)
    result231 = _t887
    record_span!(parser, span_start230)
    return result231
end

function parse_not(parser::Parser)::Proto.Not
    span_start233 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    push_path!(parser, 1)
    _t888 = parse_formula(parser)
    formula232 = _t888
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t889 = Proto.Not(arg=formula232)
    result234 = _t889
    record_span!(parser, span_start233)
    return result234
end

function parse_ffi(parser::Parser)::Proto.FFI
    span_start238 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    push_path!(parser, 1)
    _t890 = parse_name(parser)
    name235 = _t890
    pop_path!(parser)
    push_path!(parser, 2)
    _t891 = parse_ffi_args(parser)
    ffi_args236 = _t891
    pop_path!(parser)
    push_path!(parser, 3)
    _t892 = parse_terms(parser)
    terms237 = _t892
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t893 = Proto.FFI(name=name235, args=ffi_args236, terms=terms237)
    result239 = _t893
    record_span!(parser, span_start238)
    return result239
end

function parse_name(parser::Parser)::String
    span_start241 = span_start(parser)
    consume_literal!(parser, ":")
    symbol240 = consume_terminal!(parser, "SYMBOL")
    result242 = symbol240
    record_span!(parser, span_start241)
    return result242
end

function parse_ffi_args(parser::Parser)::Vector{Proto.Abstraction}
    span_start248 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs243 = Proto.Abstraction[]
    cond244 = match_lookahead_literal(parser, "(", 0)
    idx246 = 0
    while cond244
        push_path!(parser, idx246)
        _t894 = parse_abstraction(parser)
        item245 = _t894
        pop_path!(parser)
        push!(xs243, item245)
        idx246 = (idx246 + 1)
        cond244 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions247 = xs243
    consume_literal!(parser, ")")
    result249 = abstractions247
    record_span!(parser, span_start248)
    return result249
end

function parse_atom(parser::Parser)::Proto.Atom
    span_start256 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    push_path!(parser, 1)
    _t895 = parse_relation_id(parser)
    relation_id250 = _t895
    pop_path!(parser)
    push_path!(parser, 2)
    xs251 = Proto.Term[]
    cond252 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx254 = 0
    while cond252
        push_path!(parser, idx254)
        _t896 = parse_term(parser)
        item253 = _t896
        pop_path!(parser)
        push!(xs251, item253)
        idx254 = (idx254 + 1)
        cond252 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    pop_path!(parser)
    terms255 = xs251
    consume_literal!(parser, ")")
    _t897 = Proto.Atom(name=relation_id250, terms=terms255)
    result257 = _t897
    record_span!(parser, span_start256)
    return result257
end

function parse_pragma(parser::Parser)::Proto.Pragma
    span_start264 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    push_path!(parser, 1)
    _t898 = parse_name(parser)
    name258 = _t898
    pop_path!(parser)
    push_path!(parser, 2)
    xs259 = Proto.Term[]
    cond260 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx262 = 0
    while cond260
        push_path!(parser, idx262)
        _t899 = parse_term(parser)
        item261 = _t899
        pop_path!(parser)
        push!(xs259, item261)
        idx262 = (idx262 + 1)
        cond260 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    pop_path!(parser)
    terms263 = xs259
    consume_literal!(parser, ")")
    _t900 = Proto.Pragma(name=name258, terms=terms263)
    result265 = _t900
    record_span!(parser, span_start264)
    return result265
end

function parse_primitive(parser::Parser)::Proto.Primitive
    span_start282 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "primitive", 1)
            _t902 = 9
        else
            
            if match_lookahead_literal(parser, ">=", 1)
                _t903 = 4
            else
                
                if match_lookahead_literal(parser, ">", 1)
                    _t904 = 3
                else
                    
                    if match_lookahead_literal(parser, "=", 1)
                        _t905 = 0
                    else
                        
                        if match_lookahead_literal(parser, "<=", 1)
                            _t906 = 2
                        else
                            
                            if match_lookahead_literal(parser, "<", 1)
                                _t907 = 1
                            else
                                
                                if match_lookahead_literal(parser, "/", 1)
                                    _t908 = 8
                                else
                                    
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t909 = 6
                                    else
                                        
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t910 = 5
                                        else
                                            
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t911 = 7
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
    else
        _t901 = -1
    end
    prediction266 = _t901
    
    if prediction266 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        push_path!(parser, 1)
        _t913 = parse_name(parser)
        name276 = _t913
        pop_path!(parser)
        push_path!(parser, 2)
        xs277 = Proto.RelTerm[]
        cond278 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        idx280 = 0
        while cond278
            push_path!(parser, idx280)
            _t914 = parse_rel_term(parser)
            item279 = _t914
            pop_path!(parser)
            push!(xs277, item279)
            idx280 = (idx280 + 1)
            cond278 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        pop_path!(parser)
        rel_terms281 = xs277
        consume_literal!(parser, ")")
        _t915 = Proto.Primitive(name=name276, terms=rel_terms281)
        _t912 = _t915
    else
        
        if prediction266 == 8
            _t917 = parse_divide(parser)
            divide275 = _t917
            _t916 = divide275
        else
            
            if prediction266 == 7
                _t919 = parse_multiply(parser)
                multiply274 = _t919
                _t918 = multiply274
            else
                
                if prediction266 == 6
                    _t921 = parse_minus(parser)
                    minus273 = _t921
                    _t920 = minus273
                else
                    
                    if prediction266 == 5
                        _t923 = parse_add(parser)
                        add272 = _t923
                        _t922 = add272
                    else
                        
                        if prediction266 == 4
                            _t925 = parse_gt_eq(parser)
                            gt_eq271 = _t925
                            _t924 = gt_eq271
                        else
                            
                            if prediction266 == 3
                                _t927 = parse_gt(parser)
                                gt270 = _t927
                                _t926 = gt270
                            else
                                
                                if prediction266 == 2
                                    _t929 = parse_lt_eq(parser)
                                    lt_eq269 = _t929
                                    _t928 = lt_eq269
                                else
                                    
                                    if prediction266 == 1
                                        _t931 = parse_lt(parser)
                                        lt268 = _t931
                                        _t930 = lt268
                                    else
                                        
                                        if prediction266 == 0
                                            _t933 = parse_eq(parser)
                                            eq267 = _t933
                                            _t932 = eq267
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t930 = _t932
                                    end
                                    _t928 = _t930
                                end
                                _t926 = _t928
                            end
                            _t924 = _t926
                        end
                        _t922 = _t924
                    end
                    _t920 = _t922
                end
                _t918 = _t920
            end
            _t916 = _t918
        end
        _t912 = _t916
    end
    result283 = _t912
    record_span!(parser, span_start282)
    return result283
end

function parse_eq(parser::Parser)::Proto.Primitive
    span_start286 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t934 = parse_term(parser)
    term284 = _t934
    _t935 = parse_term(parser)
    term_3285 = _t935
    consume_literal!(parser, ")")
    _t936 = Proto.RelTerm(rel_term_type=OneOf(:term, term284))
    _t937 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3285))
    _t938 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t936, _t937])
    result287 = _t938
    record_span!(parser, span_start286)
    return result287
end

function parse_lt(parser::Parser)::Proto.Primitive
    span_start290 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t939 = parse_term(parser)
    term288 = _t939
    _t940 = parse_term(parser)
    term_3289 = _t940
    consume_literal!(parser, ")")
    _t941 = Proto.RelTerm(rel_term_type=OneOf(:term, term288))
    _t942 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3289))
    _t943 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t941, _t942])
    result291 = _t943
    record_span!(parser, span_start290)
    return result291
end

function parse_lt_eq(parser::Parser)::Proto.Primitive
    span_start294 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t944 = parse_term(parser)
    term292 = _t944
    _t945 = parse_term(parser)
    term_3293 = _t945
    consume_literal!(parser, ")")
    _t946 = Proto.RelTerm(rel_term_type=OneOf(:term, term292))
    _t947 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3293))
    _t948 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t946, _t947])
    result295 = _t948
    record_span!(parser, span_start294)
    return result295
end

function parse_gt(parser::Parser)::Proto.Primitive
    span_start298 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t949 = parse_term(parser)
    term296 = _t949
    _t950 = parse_term(parser)
    term_3297 = _t950
    consume_literal!(parser, ")")
    _t951 = Proto.RelTerm(rel_term_type=OneOf(:term, term296))
    _t952 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3297))
    _t953 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t951, _t952])
    result299 = _t953
    record_span!(parser, span_start298)
    return result299
end

function parse_gt_eq(parser::Parser)::Proto.Primitive
    span_start302 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t954 = parse_term(parser)
    term300 = _t954
    _t955 = parse_term(parser)
    term_3301 = _t955
    consume_literal!(parser, ")")
    _t956 = Proto.RelTerm(rel_term_type=OneOf(:term, term300))
    _t957 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3301))
    _t958 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t956, _t957])
    result303 = _t958
    record_span!(parser, span_start302)
    return result303
end

function parse_add(parser::Parser)::Proto.Primitive
    span_start307 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t959 = parse_term(parser)
    term304 = _t959
    _t960 = parse_term(parser)
    term_3305 = _t960
    _t961 = parse_term(parser)
    term_4306 = _t961
    consume_literal!(parser, ")")
    _t962 = Proto.RelTerm(rel_term_type=OneOf(:term, term304))
    _t963 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3305))
    _t964 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4306))
    _t965 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t962, _t963, _t964])
    result308 = _t965
    record_span!(parser, span_start307)
    return result308
end

function parse_minus(parser::Parser)::Proto.Primitive
    span_start312 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t966 = parse_term(parser)
    term309 = _t966
    _t967 = parse_term(parser)
    term_3310 = _t967
    _t968 = parse_term(parser)
    term_4311 = _t968
    consume_literal!(parser, ")")
    _t969 = Proto.RelTerm(rel_term_type=OneOf(:term, term309))
    _t970 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3310))
    _t971 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4311))
    _t972 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t969, _t970, _t971])
    result313 = _t972
    record_span!(parser, span_start312)
    return result313
end

function parse_multiply(parser::Parser)::Proto.Primitive
    span_start317 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t973 = parse_term(parser)
    term314 = _t973
    _t974 = parse_term(parser)
    term_3315 = _t974
    _t975 = parse_term(parser)
    term_4316 = _t975
    consume_literal!(parser, ")")
    _t976 = Proto.RelTerm(rel_term_type=OneOf(:term, term314))
    _t977 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3315))
    _t978 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4316))
    _t979 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t976, _t977, _t978])
    result318 = _t979
    record_span!(parser, span_start317)
    return result318
end

function parse_divide(parser::Parser)::Proto.Primitive
    span_start322 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t980 = parse_term(parser)
    term319 = _t980
    _t981 = parse_term(parser)
    term_3320 = _t981
    _t982 = parse_term(parser)
    term_4321 = _t982
    consume_literal!(parser, ")")
    _t983 = Proto.RelTerm(rel_term_type=OneOf(:term, term319))
    _t984 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3320))
    _t985 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4321))
    _t986 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t983, _t984, _t985])
    result323 = _t986
    record_span!(parser, span_start322)
    return result323
end

function parse_rel_term(parser::Parser)::Proto.RelTerm
    span_start327 = span_start(parser)
    
    if match_lookahead_literal(parser, "true", 0)
        _t987 = 1
    else
        
        if match_lookahead_literal(parser, "missing", 0)
            _t988 = 1
        else
            
            if match_lookahead_literal(parser, "false", 0)
                _t989 = 1
            else
                
                if match_lookahead_literal(parser, "(", 0)
                    _t990 = 1
                else
                    
                    if match_lookahead_literal(parser, "#", 0)
                        _t991 = 0
                    else
                        
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t992 = 1
                        else
                            
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t993 = 1
                            else
                                
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t994 = 1
                                else
                                    
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t995 = 1
                                    else
                                        
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t996 = 1
                                        else
                                            
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t997 = 1
                                            else
                                                
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t998 = 1
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
        end
        _t987 = _t988
    end
    prediction324 = _t987
    
    if prediction324 == 1
        _t1000 = parse_term(parser)
        term326 = _t1000
        _t1001 = Proto.RelTerm(rel_term_type=OneOf(:term, term326))
        _t999 = _t1001
    else
        
        if prediction324 == 0
            _t1003 = parse_specialized_value(parser)
            specialized_value325 = _t1003
            _t1004 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value325))
            _t1002 = _t1004
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t999 = _t1002
    end
    result328 = _t999
    record_span!(parser, span_start327)
    return result328
end

function parse_specialized_value(parser::Parser)::Proto.Value
    span_start330 = span_start(parser)
    consume_literal!(parser, "#")
    _t1005 = parse_value(parser)
    value329 = _t1005
    result331 = value329
    record_span!(parser, span_start330)
    return result331
end

function parse_rel_atom(parser::Parser)::Proto.RelAtom
    span_start338 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    push_path!(parser, 3)
    _t1006 = parse_name(parser)
    name332 = _t1006
    pop_path!(parser)
    push_path!(parser, 2)
    xs333 = Proto.RelTerm[]
    cond334 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx336 = 0
    while cond334
        push_path!(parser, idx336)
        _t1007 = parse_rel_term(parser)
        item335 = _t1007
        pop_path!(parser)
        push!(xs333, item335)
        idx336 = (idx336 + 1)
        cond334 = (((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    pop_path!(parser)
    rel_terms337 = xs333
    consume_literal!(parser, ")")
    _t1008 = Proto.RelAtom(name=name332, terms=rel_terms337)
    result339 = _t1008
    record_span!(parser, span_start338)
    return result339
end

function parse_cast(parser::Parser)::Proto.Cast
    span_start342 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    push_path!(parser, 2)
    _t1009 = parse_term(parser)
    term340 = _t1009
    pop_path!(parser)
    push_path!(parser, 3)
    _t1010 = parse_term(parser)
    term_3341 = _t1010
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1011 = Proto.Cast(input=term340, result=term_3341)
    result343 = _t1011
    record_span!(parser, span_start342)
    return result343
end

function parse_attrs(parser::Parser)::Vector{Proto.Attribute}
    span_start349 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs344 = Proto.Attribute[]
    cond345 = match_lookahead_literal(parser, "(", 0)
    idx347 = 0
    while cond345
        push_path!(parser, idx347)
        _t1012 = parse_attribute(parser)
        item346 = _t1012
        pop_path!(parser)
        push!(xs344, item346)
        idx347 = (idx347 + 1)
        cond345 = match_lookahead_literal(parser, "(", 0)
    end
    attributes348 = xs344
    consume_literal!(parser, ")")
    result350 = attributes348
    record_span!(parser, span_start349)
    return result350
end

function parse_attribute(parser::Parser)::Proto.Attribute
    span_start357 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    push_path!(parser, 1)
    _t1013 = parse_name(parser)
    name351 = _t1013
    pop_path!(parser)
    push_path!(parser, 2)
    xs352 = Proto.Value[]
    cond353 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    idx355 = 0
    while cond353
        push_path!(parser, idx355)
        _t1014 = parse_value(parser)
        item354 = _t1014
        pop_path!(parser)
        push!(xs352, item354)
        idx355 = (idx355 + 1)
        cond353 = (((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    pop_path!(parser)
    values356 = xs352
    consume_literal!(parser, ")")
    _t1015 = Proto.Attribute(name=name351, args=values356)
    result358 = _t1015
    record_span!(parser, span_start357)
    return result358
end

function parse_algorithm(parser::Parser)::Proto.Algorithm
    span_start365 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    push_path!(parser, 1)
    xs359 = Proto.RelationId[]
    cond360 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    idx362 = 0
    while cond360
        push_path!(parser, idx362)
        _t1016 = parse_relation_id(parser)
        item361 = _t1016
        pop_path!(parser)
        push!(xs359, item361)
        idx362 = (idx362 + 1)
        cond360 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    pop_path!(parser)
    relation_ids363 = xs359
    push_path!(parser, 2)
    _t1017 = parse_script(parser)
    script364 = _t1017
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1018 = Proto.Algorithm(var"#global"=relation_ids363, body=script364)
    result366 = _t1018
    record_span!(parser, span_start365)
    return result366
end

function parse_script(parser::Parser)::Proto.Script
    span_start372 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    push_path!(parser, 1)
    xs367 = Proto.Construct[]
    cond368 = match_lookahead_literal(parser, "(", 0)
    idx370 = 0
    while cond368
        push_path!(parser, idx370)
        _t1019 = parse_construct(parser)
        item369 = _t1019
        pop_path!(parser)
        push!(xs367, item369)
        idx370 = (idx370 + 1)
        cond368 = match_lookahead_literal(parser, "(", 0)
    end
    pop_path!(parser)
    constructs371 = xs367
    consume_literal!(parser, ")")
    _t1020 = Proto.Script(constructs=constructs371)
    result373 = _t1020
    record_span!(parser, span_start372)
    return result373
end

function parse_construct(parser::Parser)::Proto.Construct
    span_start377 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t1022 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t1023 = 1
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1024 = 1
                else
                    
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1025 = 0
                    else
                        
                        if match_lookahead_literal(parser, "break", 1)
                            _t1026 = 1
                        else
                            
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1027 = 1
                            else
                                _t1027 = -1
                            end
                            _t1026 = _t1027
                        end
                        _t1025 = _t1026
                    end
                    _t1024 = _t1025
                end
                _t1023 = _t1024
            end
            _t1022 = _t1023
        end
        _t1021 = _t1022
    else
        _t1021 = -1
    end
    prediction374 = _t1021
    
    if prediction374 == 1
        _t1029 = parse_instruction(parser)
        instruction376 = _t1029
        _t1030 = Proto.Construct(construct_type=OneOf(:instruction, instruction376))
        _t1028 = _t1030
    else
        
        if prediction374 == 0
            _t1032 = parse_loop(parser)
            loop375 = _t1032
            _t1033 = Proto.Construct(construct_type=OneOf(:loop, loop375))
            _t1031 = _t1033
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1028 = _t1031
    end
    result378 = _t1028
    record_span!(parser, span_start377)
    return result378
end

function parse_loop(parser::Parser)::Proto.Loop
    span_start381 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    push_path!(parser, 1)
    _t1034 = parse_init(parser)
    init379 = _t1034
    pop_path!(parser)
    push_path!(parser, 2)
    _t1035 = parse_script(parser)
    script380 = _t1035
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1036 = Proto.Loop(init=init379, body=script380)
    result382 = _t1036
    record_span!(parser, span_start381)
    return result382
end

function parse_init(parser::Parser)::Vector{Proto.Instruction}
    span_start388 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs383 = Proto.Instruction[]
    cond384 = match_lookahead_literal(parser, "(", 0)
    idx386 = 0
    while cond384
        push_path!(parser, idx386)
        _t1037 = parse_instruction(parser)
        item385 = _t1037
        pop_path!(parser)
        push!(xs383, item385)
        idx386 = (idx386 + 1)
        cond384 = match_lookahead_literal(parser, "(", 0)
    end
    instructions387 = xs383
    consume_literal!(parser, ")")
    result389 = instructions387
    record_span!(parser, span_start388)
    return result389
end

function parse_instruction(parser::Parser)::Proto.Instruction
    span_start396 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "upsert", 1)
            _t1039 = 1
        else
            
            if match_lookahead_literal(parser, "monus", 1)
                _t1040 = 4
            else
                
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1041 = 3
                else
                    
                    if match_lookahead_literal(parser, "break", 1)
                        _t1042 = 2
                    else
                        
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1043 = 0
                        else
                            _t1043 = -1
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
    prediction390 = _t1038
    
    if prediction390 == 4
        _t1045 = parse_monus_def(parser)
        monus_def395 = _t1045
        _t1046 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def395))
        _t1044 = _t1046
    else
        
        if prediction390 == 3
            _t1048 = parse_monoid_def(parser)
            monoid_def394 = _t1048
            _t1049 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def394))
            _t1047 = _t1049
        else
            
            if prediction390 == 2
                _t1051 = parse_break(parser)
                break393 = _t1051
                _t1052 = Proto.Instruction(instr_type=OneOf(:var"#break", break393))
                _t1050 = _t1052
            else
                
                if prediction390 == 1
                    _t1054 = parse_upsert(parser)
                    upsert392 = _t1054
                    _t1055 = Proto.Instruction(instr_type=OneOf(:upsert, upsert392))
                    _t1053 = _t1055
                else
                    
                    if prediction390 == 0
                        _t1057 = parse_assign(parser)
                        assign391 = _t1057
                        _t1058 = Proto.Instruction(instr_type=OneOf(:assign, assign391))
                        _t1056 = _t1058
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1053 = _t1056
                end
                _t1050 = _t1053
            end
            _t1047 = _t1050
        end
        _t1044 = _t1047
    end
    result397 = _t1044
    record_span!(parser, span_start396)
    return result397
end

function parse_assign(parser::Parser)::Proto.Assign
    span_start401 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    push_path!(parser, 1)
    _t1059 = parse_relation_id(parser)
    relation_id398 = _t1059
    pop_path!(parser)
    push_path!(parser, 2)
    _t1060 = parse_abstraction(parser)
    abstraction399 = _t1060
    pop_path!(parser)
    push_path!(parser, 3)
    
    if match_lookahead_literal(parser, "(", 0)
        _t1062 = parse_attrs(parser)
        _t1061 = _t1062
    else
        _t1061 = nothing
    end
    attrs400 = _t1061
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1063 = Proto.Assign(name=relation_id398, body=abstraction399, attrs=(!isnothing(attrs400) ? attrs400 : Proto.Attribute[]))
    result402 = _t1063
    record_span!(parser, span_start401)
    return result402
end

function parse_upsert(parser::Parser)::Proto.Upsert
    span_start406 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    push_path!(parser, 1)
    _t1064 = parse_relation_id(parser)
    relation_id403 = _t1064
    pop_path!(parser)
    _t1065 = parse_abstraction_with_arity(parser)
    abstraction_with_arity404 = _t1065
    push_path!(parser, 3)
    
    if match_lookahead_literal(parser, "(", 0)
        _t1067 = parse_attrs(parser)
        _t1066 = _t1067
    else
        _t1066 = nothing
    end
    attrs405 = _t1066
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1068 = Proto.Upsert(name=relation_id403, body=abstraction_with_arity404[1], attrs=(!isnothing(attrs405) ? attrs405 : Proto.Attribute[]), value_arity=abstraction_with_arity404[2])
    result407 = _t1068
    record_span!(parser, span_start406)
    return result407
end

function parse_abstraction_with_arity(parser::Parser)::Tuple{Proto.Abstraction, Int64}
    span_start410 = span_start(parser)
    consume_literal!(parser, "(")
    _t1069 = parse_bindings(parser)
    bindings408 = _t1069
    _t1070 = parse_formula(parser)
    formula409 = _t1070
    consume_literal!(parser, ")")
    _t1071 = Proto.Abstraction(vars=vcat(bindings408[1], !isnothing(bindings408[2]) ? bindings408[2] : []), value=formula409)
    result411 = (_t1071, length(bindings408[2]),)
    record_span!(parser, span_start410)
    return result411
end

function parse_break(parser::Parser)::Proto.Break
    span_start415 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    push_path!(parser, 1)
    _t1072 = parse_relation_id(parser)
    relation_id412 = _t1072
    pop_path!(parser)
    push_path!(parser, 2)
    _t1073 = parse_abstraction(parser)
    abstraction413 = _t1073
    pop_path!(parser)
    push_path!(parser, 3)
    
    if match_lookahead_literal(parser, "(", 0)
        _t1075 = parse_attrs(parser)
        _t1074 = _t1075
    else
        _t1074 = nothing
    end
    attrs414 = _t1074
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1076 = Proto.Break(name=relation_id412, body=abstraction413, attrs=(!isnothing(attrs414) ? attrs414 : Proto.Attribute[]))
    result416 = _t1076
    record_span!(parser, span_start415)
    return result416
end

function parse_monoid_def(parser::Parser)::Proto.MonoidDef
    span_start421 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    push_path!(parser, 1)
    _t1077 = parse_monoid(parser)
    monoid417 = _t1077
    pop_path!(parser)
    push_path!(parser, 2)
    _t1078 = parse_relation_id(parser)
    relation_id418 = _t1078
    pop_path!(parser)
    _t1079 = parse_abstraction_with_arity(parser)
    abstraction_with_arity419 = _t1079
    push_path!(parser, 4)
    
    if match_lookahead_literal(parser, "(", 0)
        _t1081 = parse_attrs(parser)
        _t1080 = _t1081
    else
        _t1080 = nothing
    end
    attrs420 = _t1080
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1082 = Proto.MonoidDef(monoid=monoid417, name=relation_id418, body=abstraction_with_arity419[1], attrs=(!isnothing(attrs420) ? attrs420 : Proto.Attribute[]), value_arity=abstraction_with_arity419[2])
    result422 = _t1082
    record_span!(parser, span_start421)
    return result422
end

function parse_monoid(parser::Parser)::Proto.Monoid
    span_start428 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "sum", 1)
            _t1084 = 3
        else
            
            if match_lookahead_literal(parser, "or", 1)
                _t1085 = 0
            else
                
                if match_lookahead_literal(parser, "min", 1)
                    _t1086 = 1
                else
                    
                    if match_lookahead_literal(parser, "max", 1)
                        _t1087 = 2
                    else
                        _t1087 = -1
                    end
                    _t1086 = _t1087
                end
                _t1085 = _t1086
            end
            _t1084 = _t1085
        end
        _t1083 = _t1084
    else
        _t1083 = -1
    end
    prediction423 = _t1083
    
    if prediction423 == 3
        _t1089 = parse_sum_monoid(parser)
        sum_monoid427 = _t1089
        _t1090 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid427))
        _t1088 = _t1090
    else
        
        if prediction423 == 2
            _t1092 = parse_max_monoid(parser)
            max_monoid426 = _t1092
            _t1093 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid426))
            _t1091 = _t1093
        else
            
            if prediction423 == 1
                _t1095 = parse_min_monoid(parser)
                min_monoid425 = _t1095
                _t1096 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid425))
                _t1094 = _t1096
            else
                
                if prediction423 == 0
                    _t1098 = parse_or_monoid(parser)
                    or_monoid424 = _t1098
                    _t1099 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid424))
                    _t1097 = _t1099
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1094 = _t1097
            end
            _t1091 = _t1094
        end
        _t1088 = _t1091
    end
    result429 = _t1088
    record_span!(parser, span_start428)
    return result429
end

function parse_or_monoid(parser::Parser)::Proto.OrMonoid
    span_start430 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1100 = Proto.OrMonoid()
    result431 = _t1100
    record_span!(parser, span_start430)
    return result431
end

function parse_min_monoid(parser::Parser)::Proto.MinMonoid
    span_start433 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    push_path!(parser, 1)
    _t1101 = parse_type(parser)
    type432 = _t1101
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1102 = Proto.MinMonoid(var"#type"=type432)
    result434 = _t1102
    record_span!(parser, span_start433)
    return result434
end

function parse_max_monoid(parser::Parser)::Proto.MaxMonoid
    span_start436 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    push_path!(parser, 1)
    _t1103 = parse_type(parser)
    type435 = _t1103
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1104 = Proto.MaxMonoid(var"#type"=type435)
    result437 = _t1104
    record_span!(parser, span_start436)
    return result437
end

function parse_sum_monoid(parser::Parser)::Proto.SumMonoid
    span_start439 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    push_path!(parser, 1)
    _t1105 = parse_type(parser)
    type438 = _t1105
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1106 = Proto.SumMonoid(var"#type"=type438)
    result440 = _t1106
    record_span!(parser, span_start439)
    return result440
end

function parse_monus_def(parser::Parser)::Proto.MonusDef
    span_start445 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    push_path!(parser, 1)
    _t1107 = parse_monoid(parser)
    monoid441 = _t1107
    pop_path!(parser)
    push_path!(parser, 2)
    _t1108 = parse_relation_id(parser)
    relation_id442 = _t1108
    pop_path!(parser)
    _t1109 = parse_abstraction_with_arity(parser)
    abstraction_with_arity443 = _t1109
    push_path!(parser, 4)
    
    if match_lookahead_literal(parser, "(", 0)
        _t1111 = parse_attrs(parser)
        _t1110 = _t1111
    else
        _t1110 = nothing
    end
    attrs444 = _t1110
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1112 = Proto.MonusDef(monoid=monoid441, name=relation_id442, body=abstraction_with_arity443[1], attrs=(!isnothing(attrs444) ? attrs444 : Proto.Attribute[]), value_arity=abstraction_with_arity443[2])
    result446 = _t1112
    record_span!(parser, span_start445)
    return result446
end

function parse_constraint(parser::Parser)::Proto.Constraint
    span_start451 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    push_path!(parser, 2)
    _t1113 = parse_relation_id(parser)
    relation_id447 = _t1113
    pop_path!(parser)
    _t1114 = parse_abstraction(parser)
    abstraction448 = _t1114
    _t1115 = parse_functional_dependency_keys(parser)
    functional_dependency_keys449 = _t1115
    _t1116 = parse_functional_dependency_values(parser)
    functional_dependency_values450 = _t1116
    consume_literal!(parser, ")")
    _t1117 = Proto.FunctionalDependency(guard=abstraction448, keys=functional_dependency_keys449, values=functional_dependency_values450)
    _t1118 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1117), name=relation_id447)
    result452 = _t1118
    record_span!(parser, span_start451)
    return result452
end

function parse_functional_dependency_keys(parser::Parser)::Vector{Proto.Var}
    span_start458 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs453 = Proto.Var[]
    cond454 = match_lookahead_terminal(parser, "SYMBOL", 0)
    idx456 = 0
    while cond454
        push_path!(parser, idx456)
        _t1119 = parse_var(parser)
        item455 = _t1119
        pop_path!(parser)
        push!(xs453, item455)
        idx456 = (idx456 + 1)
        cond454 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars457 = xs453
    consume_literal!(parser, ")")
    result459 = vars457
    record_span!(parser, span_start458)
    return result459
end

function parse_functional_dependency_values(parser::Parser)::Vector{Proto.Var}
    span_start465 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs460 = Proto.Var[]
    cond461 = match_lookahead_terminal(parser, "SYMBOL", 0)
    idx463 = 0
    while cond461
        push_path!(parser, idx463)
        _t1120 = parse_var(parser)
        item462 = _t1120
        pop_path!(parser)
        push!(xs460, item462)
        idx463 = (idx463 + 1)
        cond461 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars464 = xs460
    consume_literal!(parser, ")")
    result466 = vars464
    record_span!(parser, span_start465)
    return result466
end

function parse_data(parser::Parser)::Proto.Data
    span_start471 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "rel_edb", 1)
            _t1122 = 0
        else
            
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1123 = 2
            else
                
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1124 = 1
                else
                    _t1124 = -1
                end
                _t1123 = _t1124
            end
            _t1122 = _t1123
        end
        _t1121 = _t1122
    else
        _t1121 = -1
    end
    prediction467 = _t1121
    
    if prediction467 == 2
        _t1126 = parse_csv_data(parser)
        csv_data470 = _t1126
        _t1127 = Proto.Data(data_type=OneOf(:csv_data, csv_data470))
        _t1125 = _t1127
    else
        
        if prediction467 == 1
            _t1129 = parse_betree_relation(parser)
            betree_relation469 = _t1129
            _t1130 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation469))
            _t1128 = _t1130
        else
            
            if prediction467 == 0
                _t1132 = parse_rel_edb(parser)
                rel_edb468 = _t1132
                _t1133 = Proto.Data(data_type=OneOf(:rel_edb, rel_edb468))
                _t1131 = _t1133
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1128 = _t1131
        end
        _t1125 = _t1128
    end
    result472 = _t1125
    record_span!(parser, span_start471)
    return result472
end

function parse_rel_edb(parser::Parser)::Proto.RelEDB
    span_start476 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "rel_edb")
    push_path!(parser, 1)
    _t1134 = parse_relation_id(parser)
    relation_id473 = _t1134
    pop_path!(parser)
    push_path!(parser, 2)
    _t1135 = parse_rel_edb_path(parser)
    rel_edb_path474 = _t1135
    pop_path!(parser)
    push_path!(parser, 3)
    _t1136 = parse_rel_edb_types(parser)
    rel_edb_types475 = _t1136
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1137 = Proto.RelEDB(target_id=relation_id473, path=rel_edb_path474, types=rel_edb_types475)
    result477 = _t1137
    record_span!(parser, span_start476)
    return result477
end

function parse_rel_edb_path(parser::Parser)::Vector{String}
    span_start483 = span_start(parser)
    consume_literal!(parser, "[")
    xs478 = String[]
    cond479 = match_lookahead_terminal(parser, "STRING", 0)
    idx481 = 0
    while cond479
        push_path!(parser, idx481)
        item480 = consume_terminal!(parser, "STRING")
        pop_path!(parser)
        push!(xs478, item480)
        idx481 = (idx481 + 1)
        cond479 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings482 = xs478
    consume_literal!(parser, "]")
    result484 = strings482
    record_span!(parser, span_start483)
    return result484
end

function parse_rel_edb_types(parser::Parser)::Vector{Proto.var"#Type"}
    span_start490 = span_start(parser)
    consume_literal!(parser, "[")
    xs485 = Proto.var"#Type"[]
    cond486 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx488 = 0
    while cond486
        push_path!(parser, idx488)
        _t1138 = parse_type(parser)
        item487 = _t1138
        pop_path!(parser)
        push!(xs485, item487)
        idx488 = (idx488 + 1)
        cond486 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types489 = xs485
    consume_literal!(parser, "]")
    result491 = types489
    record_span!(parser, span_start490)
    return result491
end

function parse_betree_relation(parser::Parser)::Proto.BeTreeRelation
    span_start494 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    push_path!(parser, 1)
    _t1139 = parse_relation_id(parser)
    relation_id492 = _t1139
    pop_path!(parser)
    push_path!(parser, 2)
    _t1140 = parse_betree_info(parser)
    betree_info493 = _t1140
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1141 = Proto.BeTreeRelation(name=relation_id492, relation_info=betree_info493)
    result495 = _t1141
    record_span!(parser, span_start494)
    return result495
end

function parse_betree_info(parser::Parser)::Proto.BeTreeInfo
    span_start499 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1142 = parse_betree_info_key_types(parser)
    betree_info_key_types496 = _t1142
    _t1143 = parse_betree_info_value_types(parser)
    betree_info_value_types497 = _t1143
    _t1144 = parse_config_dict(parser)
    config_dict498 = _t1144
    consume_literal!(parser, ")")
    _t1145 = construct_betree_info(parser, betree_info_key_types496, betree_info_value_types497, config_dict498)
    result500 = _t1145
    record_span!(parser, span_start499)
    return result500
end

function parse_betree_info_key_types(parser::Parser)::Vector{Proto.var"#Type"}
    span_start506 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs501 = Proto.var"#Type"[]
    cond502 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx504 = 0
    while cond502
        push_path!(parser, idx504)
        _t1146 = parse_type(parser)
        item503 = _t1146
        pop_path!(parser)
        push!(xs501, item503)
        idx504 = (idx504 + 1)
        cond502 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types505 = xs501
    consume_literal!(parser, ")")
    result507 = types505
    record_span!(parser, span_start506)
    return result507
end

function parse_betree_info_value_types(parser::Parser)::Vector{Proto.var"#Type"}
    span_start513 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs508 = Proto.var"#Type"[]
    cond509 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx511 = 0
    while cond509
        push_path!(parser, idx511)
        _t1147 = parse_type(parser)
        item510 = _t1147
        pop_path!(parser)
        push!(xs508, item510)
        idx511 = (idx511 + 1)
        cond509 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types512 = xs508
    consume_literal!(parser, ")")
    result514 = types512
    record_span!(parser, span_start513)
    return result514
end

function parse_csv_data(parser::Parser)::Proto.CSVData
    span_start519 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    push_path!(parser, 1)
    _t1148 = parse_csvlocator(parser)
    csvlocator515 = _t1148
    pop_path!(parser)
    push_path!(parser, 2)
    _t1149 = parse_csv_config(parser)
    csv_config516 = _t1149
    pop_path!(parser)
    push_path!(parser, 3)
    _t1150 = parse_csv_columns(parser)
    csv_columns517 = _t1150
    pop_path!(parser)
    push_path!(parser, 4)
    _t1151 = parse_csv_asof(parser)
    csv_asof518 = _t1151
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1152 = Proto.CSVData(locator=csvlocator515, config=csv_config516, columns=csv_columns517, asof=csv_asof518)
    result520 = _t1152
    record_span!(parser, span_start519)
    return result520
end

function parse_csvlocator(parser::Parser)::Proto.CSVLocator
    span_start523 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    push_path!(parser, 1)
    
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1154 = parse_csv_locator_paths(parser)
        _t1153 = _t1154
    else
        _t1153 = nothing
    end
    csv_locator_paths521 = _t1153
    pop_path!(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        _t1156 = parse_csv_locator_inline_data(parser)
        _t1155 = _t1156
    else
        _t1155 = nothing
    end
    csv_locator_inline_data522 = _t1155
    consume_literal!(parser, ")")
    _t1157 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths521) ? csv_locator_paths521 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data522) ? csv_locator_inline_data522 : "")))
    result524 = _t1157
    record_span!(parser, span_start523)
    return result524
end

function parse_csv_locator_paths(parser::Parser)::Vector{String}
    span_start530 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs525 = String[]
    cond526 = match_lookahead_terminal(parser, "STRING", 0)
    idx528 = 0
    while cond526
        push_path!(parser, idx528)
        item527 = consume_terminal!(parser, "STRING")
        pop_path!(parser)
        push!(xs525, item527)
        idx528 = (idx528 + 1)
        cond526 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings529 = xs525
    consume_literal!(parser, ")")
    result531 = strings529
    record_span!(parser, span_start530)
    return result531
end

function parse_csv_locator_inline_data(parser::Parser)::String
    span_start533 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string532 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result534 = string532
    record_span!(parser, span_start533)
    return result534
end

function parse_csv_config(parser::Parser)::Proto.CSVConfig
    span_start536 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1158 = parse_config_dict(parser)
    config_dict535 = _t1158
    consume_literal!(parser, ")")
    _t1159 = construct_csv_config(parser, config_dict535)
    result537 = _t1159
    record_span!(parser, span_start536)
    return result537
end

function parse_csv_columns(parser::Parser)::Vector{Proto.CSVColumn}
    span_start543 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs538 = Proto.CSVColumn[]
    cond539 = match_lookahead_literal(parser, "(", 0)
    idx541 = 0
    while cond539
        push_path!(parser, idx541)
        _t1160 = parse_csv_column(parser)
        item540 = _t1160
        pop_path!(parser)
        push!(xs538, item540)
        idx541 = (idx541 + 1)
        cond539 = match_lookahead_literal(parser, "(", 0)
    end
    csv_columns542 = xs538
    consume_literal!(parser, ")")
    result544 = csv_columns542
    record_span!(parser, span_start543)
    return result544
end

function parse_csv_column(parser::Parser)::Proto.CSVColumn
    span_start552 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    push_path!(parser, 1)
    string545 = consume_terminal!(parser, "STRING")
    pop_path!(parser)
    push_path!(parser, 2)
    _t1161 = parse_relation_id(parser)
    relation_id546 = _t1161
    pop_path!(parser)
    consume_literal!(parser, "[")
    push_path!(parser, 3)
    xs547 = Proto.var"#Type"[]
    cond548 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    idx550 = 0
    while cond548
        push_path!(parser, idx550)
        _t1162 = parse_type(parser)
        item549 = _t1162
        pop_path!(parser)
        push!(xs547, item549)
        idx550 = (idx550 + 1)
        cond548 = ((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    pop_path!(parser)
    types551 = xs547
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1163 = Proto.CSVColumn(column_name=string545, target_id=relation_id546, types=types551)
    result553 = _t1163
    record_span!(parser, span_start552)
    return result553
end

function parse_csv_asof(parser::Parser)::String
    span_start555 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string554 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result556 = string554
    record_span!(parser, span_start555)
    return result556
end

function parse_undefine(parser::Parser)::Proto.Undefine
    span_start558 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    push_path!(parser, 1)
    _t1164 = parse_fragment_id(parser)
    fragment_id557 = _t1164
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1165 = Proto.Undefine(fragment_id=fragment_id557)
    result559 = _t1165
    record_span!(parser, span_start558)
    return result559
end

function parse_context(parser::Parser)::Proto.Context
    span_start565 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    push_path!(parser, 1)
    xs560 = Proto.RelationId[]
    cond561 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    idx563 = 0
    while cond561
        push_path!(parser, idx563)
        _t1166 = parse_relation_id(parser)
        item562 = _t1166
        pop_path!(parser)
        push!(xs560, item562)
        idx563 = (idx563 + 1)
        cond561 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    pop_path!(parser)
    relation_ids564 = xs560
    consume_literal!(parser, ")")
    _t1167 = Proto.Context(relations=relation_ids564)
    result566 = _t1167
    record_span!(parser, span_start565)
    return result566
end

function parse_epoch_reads(parser::Parser)::Vector{Proto.Read}
    span_start572 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs567 = Proto.Read[]
    cond568 = match_lookahead_literal(parser, "(", 0)
    idx570 = 0
    while cond568
        push_path!(parser, idx570)
        _t1168 = parse_read(parser)
        item569 = _t1168
        pop_path!(parser)
        push!(xs567, item569)
        idx570 = (idx570 + 1)
        cond568 = match_lookahead_literal(parser, "(", 0)
    end
    reads571 = xs567
    consume_literal!(parser, ")")
    result573 = reads571
    record_span!(parser, span_start572)
    return result573
end

function parse_read(parser::Parser)::Proto.Read
    span_start580 = span_start(parser)
    
    if match_lookahead_literal(parser, "(", 0)
        
        if match_lookahead_literal(parser, "what_if", 1)
            _t1170 = 2
        else
            
            if match_lookahead_literal(parser, "output", 1)
                _t1171 = 1
            else
                
                if match_lookahead_literal(parser, "export", 1)
                    _t1172 = 4
                else
                    
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1173 = 0
                    else
                        
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1174 = 3
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
        end
        _t1169 = _t1170
    else
        _t1169 = -1
    end
    prediction574 = _t1169
    
    if prediction574 == 4
        _t1176 = parse_export(parser)
        export579 = _t1176
        _t1177 = Proto.Read(read_type=OneOf(:var"#export", export579))
        _t1175 = _t1177
    else
        
        if prediction574 == 3
            _t1179 = parse_abort(parser)
            abort578 = _t1179
            _t1180 = Proto.Read(read_type=OneOf(:abort, abort578))
            _t1178 = _t1180
        else
            
            if prediction574 == 2
                _t1182 = parse_what_if(parser)
                what_if577 = _t1182
                _t1183 = Proto.Read(read_type=OneOf(:what_if, what_if577))
                _t1181 = _t1183
            else
                
                if prediction574 == 1
                    _t1185 = parse_output(parser)
                    output576 = _t1185
                    _t1186 = Proto.Read(read_type=OneOf(:output, output576))
                    _t1184 = _t1186
                else
                    
                    if prediction574 == 0
                        _t1188 = parse_demand(parser)
                        demand575 = _t1188
                        _t1189 = Proto.Read(read_type=OneOf(:demand, demand575))
                        _t1187 = _t1189
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1184 = _t1187
                end
                _t1181 = _t1184
            end
            _t1178 = _t1181
        end
        _t1175 = _t1178
    end
    result581 = _t1175
    record_span!(parser, span_start580)
    return result581
end

function parse_demand(parser::Parser)::Proto.Demand
    span_start583 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    push_path!(parser, 1)
    _t1190 = parse_relation_id(parser)
    relation_id582 = _t1190
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1191 = Proto.Demand(relation_id=relation_id582)
    result584 = _t1191
    record_span!(parser, span_start583)
    return result584
end

function parse_output(parser::Parser)::Proto.Output
    span_start587 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    push_path!(parser, 1)
    _t1192 = parse_name(parser)
    name585 = _t1192
    pop_path!(parser)
    push_path!(parser, 2)
    _t1193 = parse_relation_id(parser)
    relation_id586 = _t1193
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1194 = Proto.Output(name=name585, relation_id=relation_id586)
    result588 = _t1194
    record_span!(parser, span_start587)
    return result588
end

function parse_what_if(parser::Parser)::Proto.WhatIf
    span_start591 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    push_path!(parser, 1)
    _t1195 = parse_name(parser)
    name589 = _t1195
    pop_path!(parser)
    push_path!(parser, 2)
    _t1196 = parse_epoch(parser)
    epoch590 = _t1196
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1197 = Proto.WhatIf(branch=name589, epoch=epoch590)
    result592 = _t1197
    record_span!(parser, span_start591)
    return result592
end

function parse_abort(parser::Parser)::Proto.Abort
    span_start595 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    push_path!(parser, 1)
    
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1199 = parse_name(parser)
        _t1198 = _t1199
    else
        _t1198 = nothing
    end
    name593 = _t1198
    pop_path!(parser)
    push_path!(parser, 2)
    _t1200 = parse_relation_id(parser)
    relation_id594 = _t1200
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1201 = Proto.Abort(name=(!isnothing(name593) ? name593 : "abort"), relation_id=relation_id594)
    result596 = _t1201
    record_span!(parser, span_start595)
    return result596
end

function parse_export(parser::Parser)::Proto.Export
    span_start598 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    push_path!(parser, 1)
    _t1202 = parse_export_csv_config(parser)
    export_csv_config597 = _t1202
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1203 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config597))
    result599 = _t1203
    record_span!(parser, span_start598)
    return result599
end

function parse_export_csv_config(parser::Parser)::Proto.ExportCSVConfig
    span_start603 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export_csv_config")
    _t1204 = parse_export_csv_path(parser)
    export_csv_path600 = _t1204
    _t1205 = parse_export_csv_columns(parser)
    export_csv_columns601 = _t1205
    _t1206 = parse_config_dict(parser)
    config_dict602 = _t1206
    consume_literal!(parser, ")")
    _t1207 = export_csv_config(parser, export_csv_path600, export_csv_columns601, config_dict602)
    result604 = _t1207
    record_span!(parser, span_start603)
    return result604
end

function parse_export_csv_path(parser::Parser)::String
    span_start606 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string605 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    result607 = string605
    record_span!(parser, span_start606)
    return result607
end

function parse_export_csv_columns(parser::Parser)::Vector{Proto.ExportCSVColumn}
    span_start613 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs608 = Proto.ExportCSVColumn[]
    cond609 = match_lookahead_literal(parser, "(", 0)
    idx611 = 0
    while cond609
        push_path!(parser, idx611)
        _t1208 = parse_export_csv_column(parser)
        item610 = _t1208
        pop_path!(parser)
        push!(xs608, item610)
        idx611 = (idx611 + 1)
        cond609 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns612 = xs608
    consume_literal!(parser, ")")
    result614 = export_csv_columns612
    record_span!(parser, span_start613)
    return result614
end

function parse_export_csv_column(parser::Parser)::Proto.ExportCSVColumn
    span_start617 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    push_path!(parser, 1)
    string615 = consume_terminal!(parser, "STRING")
    pop_path!(parser)
    push_path!(parser, 2)
    _t1209 = parse_relation_id(parser)
    relation_id616 = _t1209
    pop_path!(parser)
    consume_literal!(parser, ")")
    _t1210 = Proto.ExportCSVColumn(column_name=string615, column_data=relation_id616)
    result618 = _t1210
    record_span!(parser, span_start617)
    return result618
end


function parse(input::String)
    lexer = Lexer(input)
    parser = Parser(lexer.tokens, input)
    result = parse_transaction(parser)
    # Check for unconsumed tokens (except EOF)
    if parser.pos <= length(parser.tokens)
        remaining_token = lookahead(parser, 0)
        if remaining_token.type != "\$"
            throw(ParseError("Unexpected token at end of input: $remaining_token"))
        end
    end
    return result, parser.provenance
end
