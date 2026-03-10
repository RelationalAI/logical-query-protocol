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


struct Location
    line::Int
    column::Int
    offset::Int
end

struct Span
    start::Location
    stop::Location
    type_name::String
end

struct Token
    type::String
    value::Any
    start_pos::Int
    end_pos::Int
end

Base.show(io::IO, t::Token) = print(io, "Token(", t.type, ", ", repr(t.value), ", ", t.start_pos, ")")
Base.getproperty(t::Token, s::Symbol) = s === :pos ? getfield(t, :start_pos) : getfield(t, s)


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

scan_int32(n::String) = Base.parse(Int32, n[1:end-3])  # Remove "i32" suffix

scan_uint32(n::String) = Base.parse(UInt32, n[1:end-3])  # Remove "u32" suffix

scan_float32(f::String) = Base.parse(Float32, f[1:end-3])  # Remove "f32" suffix

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
    ("FLOAT32", r"[-]?\d+\.\d+f32", scan_float32),
    ("INT", r"[-]?\d+", scan_int),
    ("INT32", r"[-]?\d+i32", scan_int32),
    ("UINT32", r"\d+u32", scan_uint32),
    ("INT128", r"[-]?\d+i128", scan_int128),
    ("STRING", r"\"(?:[^\"\\]|\\.)*\"", scan_string),
    ("SYMBOL", r"[a-zA-Z_][a-zA-Z0-9_./#-]*", scan_symbol),
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
        push!(lexer.tokens, Token(token_type, action(value), lexer.pos, end_pos))
        lexer.pos = end_pos
    end

    push!(lexer.tokens, Token("\$", "", lexer.pos, lexer.pos))
    return nothing
end


function _compute_line_starts(text::String)::Vector{Int}
    starts = [1]
    for i in eachindex(text)
        if text[i] == '\n'
            push!(starts, nextind(text, i))
        end
    end
    return starts
end

mutable struct ParserState
    tokens::Vector{Token}
    pos::Int
    id_to_debuginfo::Dict{Vector{UInt8},Vector{Pair{Tuple{UInt64,UInt64},String}}}
    _current_fragment_id::Union{Nothing,Vector{UInt8}}
    _relation_id_to_name::Dict{Tuple{UInt64,UInt64},String}
    provenance::Dict{Any,Span}
    _line_starts::Vector{Int}

    function ParserState(tokens::Vector{Token}, input_str::String)
        return new(tokens, 1, Dict(), nothing, Dict(), Dict{Any,Span}(), _compute_line_starts(input_str))
    end
end


function _make_location(parser::ParserState, offset::Int)::Location
    line_idx = searchsortedlast(parser._line_starts, offset)
    col = offset - parser._line_starts[line_idx]
    return Location(line_idx, col + 1, offset)
end

function span_start(parser::ParserState)::Int
    return lookahead(parser, 0).start_pos
end

function record_span!(parser::ParserState, start_offset::Int, type_name::String="")
    # First-wins: innermost parse function records first; outer wrappers
    # that share the same offset do not overwrite.
    haskey(parser.provenance, start_offset) && return nothing
    if parser.pos > 1
        end_offset = parser.tokens[parser.pos - 1].end_pos
    else
        end_offset = start_offset
    end
    s = Span(_make_location(parser, start_offset), _make_location(parser, end_offset), type_name)
    parser.provenance[start_offset] = s
    return nothing
end

function lookahead(parser::ParserState, k::Int=0)::Token
    idx = parser.pos + k
    return idx <= length(parser.tokens) ? parser.tokens[idx] : Token("\$", "", -1, -1)
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
    # Use big-endian and the lower 128 bits of the hash, consistent with pyrel.
    id_high = ntoh(reinterpret(UInt64, hash_bytes[17:24])[1])
    id_low = ntoh(reinterpret(UInt64, hash_bytes[25:32])[1])
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
    if (!isnothing(value) && _has_proto_field(value, Symbol("int32_value")))
        return _get_oneof_field(value, :int32_value)
    else
        _t1812 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1813 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1814 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1815 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1816 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1817 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1818 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1819 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1820 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1821 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1821
    _t1822 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1822
    _t1823 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1823
    _t1824 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1824
    _t1825 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1825
    _t1826 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1826
    _t1827 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1827
    _t1828 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1828
    _t1829 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1829
    _t1830 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1830
    _t1831 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1831
    _t1832 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t1832
    _t1833 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t1833
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1834 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1834
    _t1835 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1835
    _t1836 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1836
    _t1837 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1837
    _t1838 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1838
    _t1839 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1839
    _t1840 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1840
    _t1841 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1841
    _t1842 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1842
    _t1843 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1843
    _t1844 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1844
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1845 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1845
    _t1846 = Proto.Configure(semantics_version=0, ivm_config=ivm_config, optimization_level=Proto.OptimizationLevel.OPTIMIZATION_LEVEL_DEFAULT)
    return _t1846
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
    _t1847 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1847
    _t1848 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1848
    optimization_level_val = get(config, "optimization_level", nothing)
    optimization_level = Proto.OptimizationLevel.OPTIMIZATION_LEVEL_DEFAULT
    if (!isnothing(optimization_level_val) && _has_proto_field(optimization_level_val, Symbol("string_value")))
        if _get_oneof_field(optimization_level_val, :string_value) == "default"
            optimization_level = Proto.OptimizationLevel.OPTIMIZATION_LEVEL_DEFAULT
        else
            if _get_oneof_field(optimization_level_val, :string_value) == "conservative"
                optimization_level = Proto.OptimizationLevel.OPTIMIZATION_LEVEL_CONSERVATIVE
            else
                if _get_oneof_field(optimization_level_val, :string_value) == "aggressive"
                    optimization_level = Proto.OptimizationLevel.OPTIMIZATION_LEVEL_AGGRESSIVE
                else
                    optimization_level = Proto.OptimizationLevel.OPTIMIZATION_LEVEL_DEFAULT
                end
            end
        end
    end
    _t1849 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config, optimization_level=optimization_level)
    return _t1849
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1850 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1850
    _t1851 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1851
    _t1852 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1852
    _t1853 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1853
    _t1854 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1854
    _t1855 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1855
    _t1856 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1856
    _t1857 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1857
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1858 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1858
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start584 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1157 = parse_configure(parser)
        _t1156 = _t1157
    else
        _t1156 = nothing
    end
    configure578 = _t1156
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1159 = parse_sync(parser)
        _t1158 = _t1159
    else
        _t1158 = nothing
    end
    sync579 = _t1158
    xs580 = Proto.Epoch[]
    cond581 = match_lookahead_literal(parser, "(", 0)
    while cond581
        _t1160 = parse_epoch(parser)
        item582 = _t1160
        push!(xs580, item582)
        cond581 = match_lookahead_literal(parser, "(", 0)
    end
    epochs583 = xs580
    consume_literal!(parser, ")")
    _t1161 = default_configure(parser)
    _t1162 = Proto.Transaction(epochs=epochs583, configure=(!isnothing(configure578) ? configure578 : _t1161), sync=sync579)
    result585 = _t1162
    record_span!(parser, span_start584, "Transaction")
    return result585
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start587 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1163 = parse_config_dict(parser)
    config_dict586 = _t1163
    consume_literal!(parser, ")")
    _t1164 = construct_configure(parser, config_dict586)
    result588 = _t1164
    record_span!(parser, span_start587, "Configure")
    return result588
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs589 = Tuple{String, Proto.Value}[]
    cond590 = match_lookahead_literal(parser, ":", 0)
    while cond590
        _t1165 = parse_config_key_value(parser)
        item591 = _t1165
        push!(xs589, item591)
        cond590 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values592 = xs589
    consume_literal!(parser, "}")
    return config_key_values592
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol593 = consume_terminal!(parser, "SYMBOL")
    _t1166 = parse_value(parser)
    value594 = _t1166
    return (symbol593, value594,)
end

function parse_value(parser::ParserState)::Proto.Value
    span_start608 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1167 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1168 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1169 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1171 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1172 = 0
                        else
                            _t1172 = -1
                        end
                        _t1171 = _t1172
                    end
                    _t1170 = _t1171
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1173 = 12
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1174 = 5
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1175 = 2
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1176 = 10
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1177 = 6
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1178 = 3
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1179 = 11
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1180 = 4
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1181 = 7
                                                    else
                                                        _t1181 = -1
                                                    end
                                                    _t1180 = _t1181
                                                end
                                                _t1179 = _t1180
                                            end
                                            _t1178 = _t1179
                                        end
                                        _t1177 = _t1178
                                    end
                                    _t1176 = _t1177
                                end
                                _t1175 = _t1176
                            end
                            _t1174 = _t1175
                        end
                        _t1173 = _t1174
                    end
                    _t1170 = _t1173
                end
                _t1169 = _t1170
            end
            _t1168 = _t1169
        end
        _t1167 = _t1168
    end
    prediction595 = _t1167
    if prediction595 == 12
        uint32607 = consume_terminal!(parser, "UINT32")
        _t1183 = Proto.Value(value=OneOf(:uint32_value, uint32607))
        _t1182 = _t1183
    else
        if prediction595 == 11
            float32606 = consume_terminal!(parser, "FLOAT32")
            _t1185 = Proto.Value(value=OneOf(:float32_value, float32606))
            _t1184 = _t1185
        else
            if prediction595 == 10
                int32605 = consume_terminal!(parser, "INT32")
                _t1187 = Proto.Value(value=OneOf(:int32_value, int32605))
                _t1186 = _t1187
            else
                if prediction595 == 9
                    _t1189 = parse_boolean_value(parser)
                    boolean_value604 = _t1189
                    _t1190 = Proto.Value(value=OneOf(:boolean_value, boolean_value604))
                    _t1188 = _t1190
                else
                    if prediction595 == 8
                        consume_literal!(parser, "missing")
                        _t1192 = Proto.MissingValue()
                        _t1193 = Proto.Value(value=OneOf(:missing_value, _t1192))
                        _t1191 = _t1193
                    else
                        if prediction595 == 7
                            decimal603 = consume_terminal!(parser, "DECIMAL")
                            _t1195 = Proto.Value(value=OneOf(:decimal_value, decimal603))
                            _t1194 = _t1195
                        else
                            if prediction595 == 6
                                int128602 = consume_terminal!(parser, "INT128")
                                _t1197 = Proto.Value(value=OneOf(:int128_value, int128602))
                                _t1196 = _t1197
                            else
                                if prediction595 == 5
                                    uint128601 = consume_terminal!(parser, "UINT128")
                                    _t1199 = Proto.Value(value=OneOf(:uint128_value, uint128601))
                                    _t1198 = _t1199
                                else
                                    if prediction595 == 4
                                        float600 = consume_terminal!(parser, "FLOAT")
                                        _t1201 = Proto.Value(value=OneOf(:float_value, float600))
                                        _t1200 = _t1201
                                    else
                                        if prediction595 == 3
                                            int599 = consume_terminal!(parser, "INT")
                                            _t1203 = Proto.Value(value=OneOf(:int_value, int599))
                                            _t1202 = _t1203
                                        else
                                            if prediction595 == 2
                                                string598 = consume_terminal!(parser, "STRING")
                                                _t1205 = Proto.Value(value=OneOf(:string_value, string598))
                                                _t1204 = _t1205
                                            else
                                                if prediction595 == 1
                                                    _t1207 = parse_datetime(parser)
                                                    datetime597 = _t1207
                                                    _t1208 = Proto.Value(value=OneOf(:datetime_value, datetime597))
                                                    _t1206 = _t1208
                                                else
                                                    if prediction595 == 0
                                                        _t1210 = parse_date(parser)
                                                        date596 = _t1210
                                                        _t1211 = Proto.Value(value=OneOf(:date_value, date596))
                                                        _t1209 = _t1211
                                                    else
                                                        throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1206 = _t1209
                                                end
                                                _t1204 = _t1206
                                            end
                                            _t1202 = _t1204
                                        end
                                        _t1200 = _t1202
                                    end
                                    _t1198 = _t1200
                                end
                                _t1196 = _t1198
                            end
                            _t1194 = _t1196
                        end
                        _t1191 = _t1194
                    end
                    _t1188 = _t1191
                end
                _t1186 = _t1188
            end
            _t1184 = _t1186
        end
        _t1182 = _t1184
    end
    result609 = _t1182
    record_span!(parser, span_start608, "Value")
    return result609
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start613 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int610 = consume_terminal!(parser, "INT")
    int_3611 = consume_terminal!(parser, "INT")
    int_4612 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1212 = Proto.DateValue(year=Int32(int610), month=Int32(int_3611), day=Int32(int_4612))
    result614 = _t1212
    record_span!(parser, span_start613, "DateValue")
    return result614
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start622 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int615 = consume_terminal!(parser, "INT")
    int_3616 = consume_terminal!(parser, "INT")
    int_4617 = consume_terminal!(parser, "INT")
    int_5618 = consume_terminal!(parser, "INT")
    int_6619 = consume_terminal!(parser, "INT")
    int_7620 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1213 = consume_terminal!(parser, "INT")
    else
        _t1213 = nothing
    end
    int_8621 = _t1213
    consume_literal!(parser, ")")
    _t1214 = Proto.DateTimeValue(year=Int32(int615), month=Int32(int_3616), day=Int32(int_4617), hour=Int32(int_5618), minute=Int32(int_6619), second=Int32(int_7620), microsecond=Int32((!isnothing(int_8621) ? int_8621 : 0)))
    result623 = _t1214
    record_span!(parser, span_start622, "DateTimeValue")
    return result623
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1215 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1216 = 1
        else
            _t1216 = -1
        end
        _t1215 = _t1216
    end
    prediction624 = _t1215
    if prediction624 == 1
        consume_literal!(parser, "false")
        _t1217 = false
    else
        if prediction624 == 0
            consume_literal!(parser, "true")
            _t1218 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1217 = _t1218
    end
    return _t1217
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start629 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs625 = Proto.FragmentId[]
    cond626 = match_lookahead_literal(parser, ":", 0)
    while cond626
        _t1219 = parse_fragment_id(parser)
        item627 = _t1219
        push!(xs625, item627)
        cond626 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids628 = xs625
    consume_literal!(parser, ")")
    _t1220 = Proto.Sync(fragments=fragment_ids628)
    result630 = _t1220
    record_span!(parser, span_start629, "Sync")
    return result630
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start632 = span_start(parser)
    consume_literal!(parser, ":")
    symbol631 = consume_terminal!(parser, "SYMBOL")
    result633 = Proto.FragmentId(Vector{UInt8}(symbol631))
    record_span!(parser, span_start632, "FragmentId")
    return result633
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start636 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1222 = parse_epoch_writes(parser)
        _t1221 = _t1222
    else
        _t1221 = nothing
    end
    epoch_writes634 = _t1221
    if match_lookahead_literal(parser, "(", 0)
        _t1224 = parse_epoch_reads(parser)
        _t1223 = _t1224
    else
        _t1223 = nothing
    end
    epoch_reads635 = _t1223
    consume_literal!(parser, ")")
    _t1225 = Proto.Epoch(writes=(!isnothing(epoch_writes634) ? epoch_writes634 : Proto.Write[]), reads=(!isnothing(epoch_reads635) ? epoch_reads635 : Proto.Read[]))
    result637 = _t1225
    record_span!(parser, span_start636, "Epoch")
    return result637
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs638 = Proto.Write[]
    cond639 = match_lookahead_literal(parser, "(", 0)
    while cond639
        _t1226 = parse_write(parser)
        item640 = _t1226
        push!(xs638, item640)
        cond639 = match_lookahead_literal(parser, "(", 0)
    end
    writes641 = xs638
    consume_literal!(parser, ")")
    return writes641
end

function parse_write(parser::ParserState)::Proto.Write
    span_start647 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1228 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1229 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1230 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1231 = 2
                    else
                        _t1231 = -1
                    end
                    _t1230 = _t1231
                end
                _t1229 = _t1230
            end
            _t1228 = _t1229
        end
        _t1227 = _t1228
    else
        _t1227 = -1
    end
    prediction642 = _t1227
    if prediction642 == 3
        _t1233 = parse_snapshot(parser)
        snapshot646 = _t1233
        _t1234 = Proto.Write(write_type=OneOf(:snapshot, snapshot646))
        _t1232 = _t1234
    else
        if prediction642 == 2
            _t1236 = parse_context(parser)
            context645 = _t1236
            _t1237 = Proto.Write(write_type=OneOf(:context, context645))
            _t1235 = _t1237
        else
            if prediction642 == 1
                _t1239 = parse_undefine(parser)
                undefine644 = _t1239
                _t1240 = Proto.Write(write_type=OneOf(:undefine, undefine644))
                _t1238 = _t1240
            else
                if prediction642 == 0
                    _t1242 = parse_define(parser)
                    define643 = _t1242
                    _t1243 = Proto.Write(write_type=OneOf(:define, define643))
                    _t1241 = _t1243
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1238 = _t1241
            end
            _t1235 = _t1238
        end
        _t1232 = _t1235
    end
    result648 = _t1232
    record_span!(parser, span_start647, "Write")
    return result648
end

function parse_define(parser::ParserState)::Proto.Define
    span_start650 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1244 = parse_fragment(parser)
    fragment649 = _t1244
    consume_literal!(parser, ")")
    _t1245 = Proto.Define(fragment=fragment649)
    result651 = _t1245
    record_span!(parser, span_start650, "Define")
    return result651
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start657 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1246 = parse_new_fragment_id(parser)
    new_fragment_id652 = _t1246
    xs653 = Proto.Declaration[]
    cond654 = match_lookahead_literal(parser, "(", 0)
    while cond654
        _t1247 = parse_declaration(parser)
        item655 = _t1247
        push!(xs653, item655)
        cond654 = match_lookahead_literal(parser, "(", 0)
    end
    declarations656 = xs653
    consume_literal!(parser, ")")
    result658 = construct_fragment(parser, new_fragment_id652, declarations656)
    record_span!(parser, span_start657, "Fragment")
    return result658
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start660 = span_start(parser)
    _t1248 = parse_fragment_id(parser)
    fragment_id659 = _t1248
    start_fragment!(parser, fragment_id659)
    result661 = fragment_id659
    record_span!(parser, span_start660, "FragmentId")
    return result661
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start667 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "functional_dependency", 1)
            _t1250 = 2
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1251 = 3
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1252 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1253 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1254 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1255 = 1
                            else
                                _t1255 = -1
                            end
                            _t1254 = _t1255
                        end
                        _t1253 = _t1254
                    end
                    _t1252 = _t1253
                end
                _t1251 = _t1252
            end
            _t1250 = _t1251
        end
        _t1249 = _t1250
    else
        _t1249 = -1
    end
    prediction662 = _t1249
    if prediction662 == 3
        _t1257 = parse_data(parser)
        data666 = _t1257
        _t1258 = Proto.Declaration(declaration_type=OneOf(:data, data666))
        _t1256 = _t1258
    else
        if prediction662 == 2
            _t1260 = parse_constraint(parser)
            constraint665 = _t1260
            _t1261 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint665))
            _t1259 = _t1261
        else
            if prediction662 == 1
                _t1263 = parse_algorithm(parser)
                algorithm664 = _t1263
                _t1264 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm664))
                _t1262 = _t1264
            else
                if prediction662 == 0
                    _t1266 = parse_def(parser)
                    def663 = _t1266
                    _t1267 = Proto.Declaration(declaration_type=OneOf(:def, def663))
                    _t1265 = _t1267
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1262 = _t1265
            end
            _t1259 = _t1262
        end
        _t1256 = _t1259
    end
    result668 = _t1256
    record_span!(parser, span_start667, "Declaration")
    return result668
end

function parse_def(parser::ParserState)::Proto.Def
    span_start672 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1268 = parse_relation_id(parser)
    relation_id669 = _t1268
    _t1269 = parse_abstraction(parser)
    abstraction670 = _t1269
    if match_lookahead_literal(parser, "(", 0)
        _t1271 = parse_attrs(parser)
        _t1270 = _t1271
    else
        _t1270 = nothing
    end
    attrs671 = _t1270
    consume_literal!(parser, ")")
    _t1272 = Proto.Def(name=relation_id669, body=abstraction670, attrs=(!isnothing(attrs671) ? attrs671 : Proto.Attribute[]))
    result673 = _t1272
    record_span!(parser, span_start672, "Def")
    return result673
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start677 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1273 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1274 = 1
        else
            _t1274 = -1
        end
        _t1273 = _t1274
    end
    prediction674 = _t1273
    if prediction674 == 1
        uint128676 = consume_terminal!(parser, "UINT128")
        _t1275 = Proto.RelationId(uint128676.low, uint128676.high)
    else
        if prediction674 == 0
            consume_literal!(parser, ":")
            symbol675 = consume_terminal!(parser, "SYMBOL")
            _t1276 = relation_id_from_string(parser, symbol675)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1275 = _t1276
    end
    result678 = _t1275
    record_span!(parser, span_start677, "RelationId")
    return result678
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start681 = span_start(parser)
    consume_literal!(parser, "(")
    _t1277 = parse_bindings(parser)
    bindings679 = _t1277
    _t1278 = parse_formula(parser)
    formula680 = _t1278
    consume_literal!(parser, ")")
    _t1279 = Proto.Abstraction(vars=vcat(bindings679[1], !isnothing(bindings679[2]) ? bindings679[2] : []), value=formula680)
    result682 = _t1279
    record_span!(parser, span_start681, "Abstraction")
    return result682
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs683 = Proto.Binding[]
    cond684 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond684
        _t1280 = parse_binding(parser)
        item685 = _t1280
        push!(xs683, item685)
        cond684 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings686 = xs683
    if match_lookahead_literal(parser, "|", 0)
        _t1282 = parse_value_bindings(parser)
        _t1281 = _t1282
    else
        _t1281 = nothing
    end
    value_bindings687 = _t1281
    consume_literal!(parser, "]")
    return (bindings686, (!isnothing(value_bindings687) ? value_bindings687 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start690 = span_start(parser)
    symbol688 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1283 = parse_type(parser)
    type689 = _t1283
    _t1284 = Proto.Var(name=symbol688)
    _t1285 = Proto.Binding(var=_t1284, var"#type"=type689)
    result691 = _t1285
    record_span!(parser, span_start690, "Binding")
    return result691
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start707 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1286 = 0
    else
        if match_lookahead_literal(parser, "UINT32", 0)
            _t1287 = 13
        else
            if match_lookahead_literal(parser, "UINT128", 0)
                _t1288 = 4
            else
                if match_lookahead_literal(parser, "STRING", 0)
                    _t1289 = 1
                else
                    if match_lookahead_literal(parser, "MISSING", 0)
                        _t1290 = 8
                    else
                        if match_lookahead_literal(parser, "INT32", 0)
                            _t1291 = 11
                        else
                            if match_lookahead_literal(parser, "INT128", 0)
                                _t1292 = 5
                            else
                                if match_lookahead_literal(parser, "INT", 0)
                                    _t1293 = 2
                                else
                                    if match_lookahead_literal(parser, "FLOAT32", 0)
                                        _t1294 = 12
                                    else
                                        if match_lookahead_literal(parser, "FLOAT", 0)
                                            _t1295 = 3
                                        else
                                            if match_lookahead_literal(parser, "DATETIME", 0)
                                                _t1296 = 7
                                            else
                                                if match_lookahead_literal(parser, "DATE", 0)
                                                    _t1297 = 6
                                                else
                                                    if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                        _t1298 = 10
                                                    else
                                                        if match_lookahead_literal(parser, "(", 0)
                                                            _t1299 = 9
                                                        else
                                                            _t1299 = -1
                                                        end
                                                        _t1298 = _t1299
                                                    end
                                                    _t1297 = _t1298
                                                end
                                                _t1296 = _t1297
                                            end
                                            _t1295 = _t1296
                                        end
                                        _t1294 = _t1295
                                    end
                                    _t1293 = _t1294
                                end
                                _t1292 = _t1293
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
        end
        _t1286 = _t1287
    end
    prediction692 = _t1286
    if prediction692 == 13
        _t1301 = parse_uint32_type(parser)
        uint32_type706 = _t1301
        _t1302 = Proto.var"#Type"(var"#type"=OneOf(:uint32_type, uint32_type706))
        _t1300 = _t1302
    else
        if prediction692 == 12
            _t1304 = parse_float32_type(parser)
            float32_type705 = _t1304
            _t1305 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type705))
            _t1303 = _t1305
        else
            if prediction692 == 11
                _t1307 = parse_int32_type(parser)
                int32_type704 = _t1307
                _t1308 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type704))
                _t1306 = _t1308
            else
                if prediction692 == 10
                    _t1310 = parse_boolean_type(parser)
                    boolean_type703 = _t1310
                    _t1311 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type703))
                    _t1309 = _t1311
                else
                    if prediction692 == 9
                        _t1313 = parse_decimal_type(parser)
                        decimal_type702 = _t1313
                        _t1314 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type702))
                        _t1312 = _t1314
                    else
                        if prediction692 == 8
                            _t1316 = parse_missing_type(parser)
                            missing_type701 = _t1316
                            _t1317 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type701))
                            _t1315 = _t1317
                        else
                            if prediction692 == 7
                                _t1319 = parse_datetime_type(parser)
                                datetime_type700 = _t1319
                                _t1320 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type700))
                                _t1318 = _t1320
                            else
                                if prediction692 == 6
                                    _t1322 = parse_date_type(parser)
                                    date_type699 = _t1322
                                    _t1323 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type699))
                                    _t1321 = _t1323
                                else
                                    if prediction692 == 5
                                        _t1325 = parse_int128_type(parser)
                                        int128_type698 = _t1325
                                        _t1326 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type698))
                                        _t1324 = _t1326
                                    else
                                        if prediction692 == 4
                                            _t1328 = parse_uint128_type(parser)
                                            uint128_type697 = _t1328
                                            _t1329 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type697))
                                            _t1327 = _t1329
                                        else
                                            if prediction692 == 3
                                                _t1331 = parse_float_type(parser)
                                                float_type696 = _t1331
                                                _t1332 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type696))
                                                _t1330 = _t1332
                                            else
                                                if prediction692 == 2
                                                    _t1334 = parse_int_type(parser)
                                                    int_type695 = _t1334
                                                    _t1335 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type695))
                                                    _t1333 = _t1335
                                                else
                                                    if prediction692 == 1
                                                        _t1337 = parse_string_type(parser)
                                                        string_type694 = _t1337
                                                        _t1338 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type694))
                                                        _t1336 = _t1338
                                                    else
                                                        if prediction692 == 0
                                                            _t1340 = parse_unspecified_type(parser)
                                                            unspecified_type693 = _t1340
                                                            _t1341 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type693))
                                                            _t1339 = _t1341
                                                        else
                                                            throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
                                                        end
                                                        _t1336 = _t1339
                                                    end
                                                    _t1333 = _t1336
                                                end
                                                _t1330 = _t1333
                                            end
                                            _t1327 = _t1330
                                        end
                                        _t1324 = _t1327
                                    end
                                    _t1321 = _t1324
                                end
                                _t1318 = _t1321
                            end
                            _t1315 = _t1318
                        end
                        _t1312 = _t1315
                    end
                    _t1309 = _t1312
                end
                _t1306 = _t1309
            end
            _t1303 = _t1306
        end
        _t1300 = _t1303
    end
    result708 = _t1300
    record_span!(parser, span_start707, "Type")
    return result708
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start709 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1342 = Proto.UnspecifiedType()
    result710 = _t1342
    record_span!(parser, span_start709, "UnspecifiedType")
    return result710
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start711 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1343 = Proto.StringType()
    result712 = _t1343
    record_span!(parser, span_start711, "StringType")
    return result712
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start713 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1344 = Proto.IntType()
    result714 = _t1344
    record_span!(parser, span_start713, "IntType")
    return result714
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start715 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1345 = Proto.FloatType()
    result716 = _t1345
    record_span!(parser, span_start715, "FloatType")
    return result716
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start717 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1346 = Proto.UInt128Type()
    result718 = _t1346
    record_span!(parser, span_start717, "UInt128Type")
    return result718
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start719 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1347 = Proto.Int128Type()
    result720 = _t1347
    record_span!(parser, span_start719, "Int128Type")
    return result720
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start721 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1348 = Proto.DateType()
    result722 = _t1348
    record_span!(parser, span_start721, "DateType")
    return result722
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start723 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1349 = Proto.DateTimeType()
    result724 = _t1349
    record_span!(parser, span_start723, "DateTimeType")
    return result724
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start725 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1350 = Proto.MissingType()
    result726 = _t1350
    record_span!(parser, span_start725, "MissingType")
    return result726
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start729 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int727 = consume_terminal!(parser, "INT")
    int_3728 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1351 = Proto.DecimalType(precision=Int32(int727), scale=Int32(int_3728))
    result730 = _t1351
    record_span!(parser, span_start729, "DecimalType")
    return result730
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start731 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1352 = Proto.BooleanType()
    result732 = _t1352
    record_span!(parser, span_start731, "BooleanType")
    return result732
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start733 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1353 = Proto.Int32Type()
    result734 = _t1353
    record_span!(parser, span_start733, "Int32Type")
    return result734
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start735 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1354 = Proto.Float32Type()
    result736 = _t1354
    record_span!(parser, span_start735, "Float32Type")
    return result736
end

function parse_uint32_type(parser::ParserState)::Proto.UInt32Type
    span_start737 = span_start(parser)
    consume_literal!(parser, "UINT32")
    _t1355 = Proto.UInt32Type()
    result738 = _t1355
    record_span!(parser, span_start737, "UInt32Type")
    return result738
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs739 = Proto.Binding[]
    cond740 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond740
        _t1356 = parse_binding(parser)
        item741 = _t1356
        push!(xs739, item741)
        cond740 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings742 = xs739
    return bindings742
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start757 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1358 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1359 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1360 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1361 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1362 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1363 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1364 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1365 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1366 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1367 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1368 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1369 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1370 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1371 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1372 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1373 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1374 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1375 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1376 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1377 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1378 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1379 = 10
                                                                                            else
                                                                                                _t1379 = -1
                                                                                            end
                                                                                            _t1378 = _t1379
                                                                                        end
                                                                                        _t1377 = _t1378
                                                                                    end
                                                                                    _t1376 = _t1377
                                                                                end
                                                                                _t1375 = _t1376
                                                                            end
                                                                            _t1374 = _t1375
                                                                        end
                                                                        _t1373 = _t1374
                                                                    end
                                                                    _t1372 = _t1373
                                                                end
                                                                _t1371 = _t1372
                                                            end
                                                            _t1370 = _t1371
                                                        end
                                                        _t1369 = _t1370
                                                    end
                                                    _t1368 = _t1369
                                                end
                                                _t1367 = _t1368
                                            end
                                            _t1366 = _t1367
                                        end
                                        _t1365 = _t1366
                                    end
                                    _t1364 = _t1365
                                end
                                _t1363 = _t1364
                            end
                            _t1362 = _t1363
                        end
                        _t1361 = _t1362
                    end
                    _t1360 = _t1361
                end
                _t1359 = _t1360
            end
            _t1358 = _t1359
        end
        _t1357 = _t1358
    else
        _t1357 = -1
    end
    prediction743 = _t1357
    if prediction743 == 12
        _t1381 = parse_cast(parser)
        cast756 = _t1381
        _t1382 = Proto.Formula(formula_type=OneOf(:cast, cast756))
        _t1380 = _t1382
    else
        if prediction743 == 11
            _t1384 = parse_rel_atom(parser)
            rel_atom755 = _t1384
            _t1385 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom755))
            _t1383 = _t1385
        else
            if prediction743 == 10
                _t1387 = parse_primitive(parser)
                primitive754 = _t1387
                _t1388 = Proto.Formula(formula_type=OneOf(:primitive, primitive754))
                _t1386 = _t1388
            else
                if prediction743 == 9
                    _t1390 = parse_pragma(parser)
                    pragma753 = _t1390
                    _t1391 = Proto.Formula(formula_type=OneOf(:pragma, pragma753))
                    _t1389 = _t1391
                else
                    if prediction743 == 8
                        _t1393 = parse_atom(parser)
                        atom752 = _t1393
                        _t1394 = Proto.Formula(formula_type=OneOf(:atom, atom752))
                        _t1392 = _t1394
                    else
                        if prediction743 == 7
                            _t1396 = parse_ffi(parser)
                            ffi751 = _t1396
                            _t1397 = Proto.Formula(formula_type=OneOf(:ffi, ffi751))
                            _t1395 = _t1397
                        else
                            if prediction743 == 6
                                _t1399 = parse_not(parser)
                                not750 = _t1399
                                _t1400 = Proto.Formula(formula_type=OneOf(:not, not750))
                                _t1398 = _t1400
                            else
                                if prediction743 == 5
                                    _t1402 = parse_disjunction(parser)
                                    disjunction749 = _t1402
                                    _t1403 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction749))
                                    _t1401 = _t1403
                                else
                                    if prediction743 == 4
                                        _t1405 = parse_conjunction(parser)
                                        conjunction748 = _t1405
                                        _t1406 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction748))
                                        _t1404 = _t1406
                                    else
                                        if prediction743 == 3
                                            _t1408 = parse_reduce(parser)
                                            reduce747 = _t1408
                                            _t1409 = Proto.Formula(formula_type=OneOf(:reduce, reduce747))
                                            _t1407 = _t1409
                                        else
                                            if prediction743 == 2
                                                _t1411 = parse_exists(parser)
                                                exists746 = _t1411
                                                _t1412 = Proto.Formula(formula_type=OneOf(:exists, exists746))
                                                _t1410 = _t1412
                                            else
                                                if prediction743 == 1
                                                    _t1414 = parse_false(parser)
                                                    false745 = _t1414
                                                    _t1415 = Proto.Formula(formula_type=OneOf(:disjunction, false745))
                                                    _t1413 = _t1415
                                                else
                                                    if prediction743 == 0
                                                        _t1417 = parse_true(parser)
                                                        true744 = _t1417
                                                        _t1418 = Proto.Formula(formula_type=OneOf(:conjunction, true744))
                                                        _t1416 = _t1418
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1413 = _t1416
                                                end
                                                _t1410 = _t1413
                                            end
                                            _t1407 = _t1410
                                        end
                                        _t1404 = _t1407
                                    end
                                    _t1401 = _t1404
                                end
                                _t1398 = _t1401
                            end
                            _t1395 = _t1398
                        end
                        _t1392 = _t1395
                    end
                    _t1389 = _t1392
                end
                _t1386 = _t1389
            end
            _t1383 = _t1386
        end
        _t1380 = _t1383
    end
    result758 = _t1380
    record_span!(parser, span_start757, "Formula")
    return result758
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start759 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1419 = Proto.Conjunction(args=Proto.Formula[])
    result760 = _t1419
    record_span!(parser, span_start759, "Conjunction")
    return result760
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start761 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1420 = Proto.Disjunction(args=Proto.Formula[])
    result762 = _t1420
    record_span!(parser, span_start761, "Disjunction")
    return result762
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start765 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1421 = parse_bindings(parser)
    bindings763 = _t1421
    _t1422 = parse_formula(parser)
    formula764 = _t1422
    consume_literal!(parser, ")")
    _t1423 = Proto.Abstraction(vars=vcat(bindings763[1], !isnothing(bindings763[2]) ? bindings763[2] : []), value=formula764)
    _t1424 = Proto.Exists(body=_t1423)
    result766 = _t1424
    record_span!(parser, span_start765, "Exists")
    return result766
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start770 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1425 = parse_abstraction(parser)
    abstraction767 = _t1425
    _t1426 = parse_abstraction(parser)
    abstraction_3768 = _t1426
    _t1427 = parse_terms(parser)
    terms769 = _t1427
    consume_literal!(parser, ")")
    _t1428 = Proto.Reduce(op=abstraction767, body=abstraction_3768, terms=terms769)
    result771 = _t1428
    record_span!(parser, span_start770, "Reduce")
    return result771
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs772 = Proto.Term[]
    cond773 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond773
        _t1429 = parse_term(parser)
        item774 = _t1429
        push!(xs772, item774)
        cond773 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    terms775 = xs772
    consume_literal!(parser, ")")
    return terms775
end

function parse_term(parser::ParserState)::Proto.Term
    span_start779 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1430 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1431 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1432 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1433 = 1
                else
                    if match_lookahead_terminal(parser, "UINT32", 0)
                        _t1434 = 1
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1435 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1436 = 0
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1437 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1438 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1439 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1440 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1441 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1442 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1443 = 1
                                                        else
                                                            _t1443 = -1
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
                            end
                            _t1435 = _t1436
                        end
                        _t1434 = _t1435
                    end
                    _t1433 = _t1434
                end
                _t1432 = _t1433
            end
            _t1431 = _t1432
        end
        _t1430 = _t1431
    end
    prediction776 = _t1430
    if prediction776 == 1
        _t1445 = parse_constant(parser)
        constant778 = _t1445
        _t1446 = Proto.Term(term_type=OneOf(:constant, constant778))
        _t1444 = _t1446
    else
        if prediction776 == 0
            _t1448 = parse_var(parser)
            var777 = _t1448
            _t1449 = Proto.Term(term_type=OneOf(:var, var777))
            _t1447 = _t1449
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1444 = _t1447
    end
    result780 = _t1444
    record_span!(parser, span_start779, "Term")
    return result780
end

function parse_var(parser::ParserState)::Proto.Var
    span_start782 = span_start(parser)
    symbol781 = consume_terminal!(parser, "SYMBOL")
    _t1450 = Proto.Var(name=symbol781)
    result783 = _t1450
    record_span!(parser, span_start782, "Var")
    return result783
end

function parse_constant(parser::ParserState)::Proto.Value
    span_start785 = span_start(parser)
    _t1451 = parse_value(parser)
    value784 = _t1451
    result786 = value784
    record_span!(parser, span_start785, "Value")
    return result786
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start791 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs787 = Proto.Formula[]
    cond788 = match_lookahead_literal(parser, "(", 0)
    while cond788
        _t1452 = parse_formula(parser)
        item789 = _t1452
        push!(xs787, item789)
        cond788 = match_lookahead_literal(parser, "(", 0)
    end
    formulas790 = xs787
    consume_literal!(parser, ")")
    _t1453 = Proto.Conjunction(args=formulas790)
    result792 = _t1453
    record_span!(parser, span_start791, "Conjunction")
    return result792
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start797 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs793 = Proto.Formula[]
    cond794 = match_lookahead_literal(parser, "(", 0)
    while cond794
        _t1454 = parse_formula(parser)
        item795 = _t1454
        push!(xs793, item795)
        cond794 = match_lookahead_literal(parser, "(", 0)
    end
    formulas796 = xs793
    consume_literal!(parser, ")")
    _t1455 = Proto.Disjunction(args=formulas796)
    result798 = _t1455
    record_span!(parser, span_start797, "Disjunction")
    return result798
end

function parse_not(parser::ParserState)::Proto.Not
    span_start800 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1456 = parse_formula(parser)
    formula799 = _t1456
    consume_literal!(parser, ")")
    _t1457 = Proto.Not(arg=formula799)
    result801 = _t1457
    record_span!(parser, span_start800, "Not")
    return result801
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start805 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1458 = parse_name(parser)
    name802 = _t1458
    _t1459 = parse_ffi_args(parser)
    ffi_args803 = _t1459
    _t1460 = parse_terms(parser)
    terms804 = _t1460
    consume_literal!(parser, ")")
    _t1461 = Proto.FFI(name=name802, args=ffi_args803, terms=terms804)
    result806 = _t1461
    record_span!(parser, span_start805, "FFI")
    return result806
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol807 = consume_terminal!(parser, "SYMBOL")
    return symbol807
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs808 = Proto.Abstraction[]
    cond809 = match_lookahead_literal(parser, "(", 0)
    while cond809
        _t1462 = parse_abstraction(parser)
        item810 = _t1462
        push!(xs808, item810)
        cond809 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions811 = xs808
    consume_literal!(parser, ")")
    return abstractions811
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start817 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1463 = parse_relation_id(parser)
    relation_id812 = _t1463
    xs813 = Proto.Term[]
    cond814 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond814
        _t1464 = parse_term(parser)
        item815 = _t1464
        push!(xs813, item815)
        cond814 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    terms816 = xs813
    consume_literal!(parser, ")")
    _t1465 = Proto.Atom(name=relation_id812, terms=terms816)
    result818 = _t1465
    record_span!(parser, span_start817, "Atom")
    return result818
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start824 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1466 = parse_name(parser)
    name819 = _t1466
    xs820 = Proto.Term[]
    cond821 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond821
        _t1467 = parse_term(parser)
        item822 = _t1467
        push!(xs820, item822)
        cond821 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    terms823 = xs820
    consume_literal!(parser, ")")
    _t1468 = Proto.Pragma(name=name819, terms=terms823)
    result825 = _t1468
    record_span!(parser, span_start824, "Pragma")
    return result825
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start841 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1470 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1471 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1472 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1473 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1474 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1475 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1476 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1477 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1478 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1479 = 7
                                            else
                                                _t1479 = -1
                                            end
                                            _t1478 = _t1479
                                        end
                                        _t1477 = _t1478
                                    end
                                    _t1476 = _t1477
                                end
                                _t1475 = _t1476
                            end
                            _t1474 = _t1475
                        end
                        _t1473 = _t1474
                    end
                    _t1472 = _t1473
                end
                _t1471 = _t1472
            end
            _t1470 = _t1471
        end
        _t1469 = _t1470
    else
        _t1469 = -1
    end
    prediction826 = _t1469
    if prediction826 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1481 = parse_name(parser)
        name836 = _t1481
        xs837 = Proto.RelTerm[]
        cond838 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
        while cond838
            _t1482 = parse_rel_term(parser)
            item839 = _t1482
            push!(xs837, item839)
            cond838 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
        end
        rel_terms840 = xs837
        consume_literal!(parser, ")")
        _t1483 = Proto.Primitive(name=name836, terms=rel_terms840)
        _t1480 = _t1483
    else
        if prediction826 == 8
            _t1485 = parse_divide(parser)
            divide835 = _t1485
            _t1484 = divide835
        else
            if prediction826 == 7
                _t1487 = parse_multiply(parser)
                multiply834 = _t1487
                _t1486 = multiply834
            else
                if prediction826 == 6
                    _t1489 = parse_minus(parser)
                    minus833 = _t1489
                    _t1488 = minus833
                else
                    if prediction826 == 5
                        _t1491 = parse_add(parser)
                        add832 = _t1491
                        _t1490 = add832
                    else
                        if prediction826 == 4
                            _t1493 = parse_gt_eq(parser)
                            gt_eq831 = _t1493
                            _t1492 = gt_eq831
                        else
                            if prediction826 == 3
                                _t1495 = parse_gt(parser)
                                gt830 = _t1495
                                _t1494 = gt830
                            else
                                if prediction826 == 2
                                    _t1497 = parse_lt_eq(parser)
                                    lt_eq829 = _t1497
                                    _t1496 = lt_eq829
                                else
                                    if prediction826 == 1
                                        _t1499 = parse_lt(parser)
                                        lt828 = _t1499
                                        _t1498 = lt828
                                    else
                                        if prediction826 == 0
                                            _t1501 = parse_eq(parser)
                                            eq827 = _t1501
                                            _t1500 = eq827
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1498 = _t1500
                                    end
                                    _t1496 = _t1498
                                end
                                _t1494 = _t1496
                            end
                            _t1492 = _t1494
                        end
                        _t1490 = _t1492
                    end
                    _t1488 = _t1490
                end
                _t1486 = _t1488
            end
            _t1484 = _t1486
        end
        _t1480 = _t1484
    end
    result842 = _t1480
    record_span!(parser, span_start841, "Primitive")
    return result842
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start845 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1502 = parse_term(parser)
    term843 = _t1502
    _t1503 = parse_term(parser)
    term_3844 = _t1503
    consume_literal!(parser, ")")
    _t1504 = Proto.RelTerm(rel_term_type=OneOf(:term, term843))
    _t1505 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3844))
    _t1506 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1504, _t1505])
    result846 = _t1506
    record_span!(parser, span_start845, "Primitive")
    return result846
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start849 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1507 = parse_term(parser)
    term847 = _t1507
    _t1508 = parse_term(parser)
    term_3848 = _t1508
    consume_literal!(parser, ")")
    _t1509 = Proto.RelTerm(rel_term_type=OneOf(:term, term847))
    _t1510 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3848))
    _t1511 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1509, _t1510])
    result850 = _t1511
    record_span!(parser, span_start849, "Primitive")
    return result850
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start853 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1512 = parse_term(parser)
    term851 = _t1512
    _t1513 = parse_term(parser)
    term_3852 = _t1513
    consume_literal!(parser, ")")
    _t1514 = Proto.RelTerm(rel_term_type=OneOf(:term, term851))
    _t1515 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3852))
    _t1516 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1514, _t1515])
    result854 = _t1516
    record_span!(parser, span_start853, "Primitive")
    return result854
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start857 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1517 = parse_term(parser)
    term855 = _t1517
    _t1518 = parse_term(parser)
    term_3856 = _t1518
    consume_literal!(parser, ")")
    _t1519 = Proto.RelTerm(rel_term_type=OneOf(:term, term855))
    _t1520 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3856))
    _t1521 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1519, _t1520])
    result858 = _t1521
    record_span!(parser, span_start857, "Primitive")
    return result858
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start861 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1522 = parse_term(parser)
    term859 = _t1522
    _t1523 = parse_term(parser)
    term_3860 = _t1523
    consume_literal!(parser, ")")
    _t1524 = Proto.RelTerm(rel_term_type=OneOf(:term, term859))
    _t1525 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3860))
    _t1526 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1524, _t1525])
    result862 = _t1526
    record_span!(parser, span_start861, "Primitive")
    return result862
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start866 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1527 = parse_term(parser)
    term863 = _t1527
    _t1528 = parse_term(parser)
    term_3864 = _t1528
    _t1529 = parse_term(parser)
    term_4865 = _t1529
    consume_literal!(parser, ")")
    _t1530 = Proto.RelTerm(rel_term_type=OneOf(:term, term863))
    _t1531 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3864))
    _t1532 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4865))
    _t1533 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1530, _t1531, _t1532])
    result867 = _t1533
    record_span!(parser, span_start866, "Primitive")
    return result867
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start871 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1534 = parse_term(parser)
    term868 = _t1534
    _t1535 = parse_term(parser)
    term_3869 = _t1535
    _t1536 = parse_term(parser)
    term_4870 = _t1536
    consume_literal!(parser, ")")
    _t1537 = Proto.RelTerm(rel_term_type=OneOf(:term, term868))
    _t1538 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3869))
    _t1539 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4870))
    _t1540 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1537, _t1538, _t1539])
    result872 = _t1540
    record_span!(parser, span_start871, "Primitive")
    return result872
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start876 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1541 = parse_term(parser)
    term873 = _t1541
    _t1542 = parse_term(parser)
    term_3874 = _t1542
    _t1543 = parse_term(parser)
    term_4875 = _t1543
    consume_literal!(parser, ")")
    _t1544 = Proto.RelTerm(rel_term_type=OneOf(:term, term873))
    _t1545 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3874))
    _t1546 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4875))
    _t1547 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1544, _t1545, _t1546])
    result877 = _t1547
    record_span!(parser, span_start876, "Primitive")
    return result877
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start881 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1548 = parse_term(parser)
    term878 = _t1548
    _t1549 = parse_term(parser)
    term_3879 = _t1549
    _t1550 = parse_term(parser)
    term_4880 = _t1550
    consume_literal!(parser, ")")
    _t1551 = Proto.RelTerm(rel_term_type=OneOf(:term, term878))
    _t1552 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3879))
    _t1553 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4880))
    _t1554 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1551, _t1552, _t1553])
    result882 = _t1554
    record_span!(parser, span_start881, "Primitive")
    return result882
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start886 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1555 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1556 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1557 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1558 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1559 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT32", 0)
                            _t1560 = 1
                        else
                            if match_lookahead_terminal(parser, "UINT128", 0)
                                _t1561 = 1
                            else
                                if match_lookahead_terminal(parser, "SYMBOL", 0)
                                    _t1562 = 1
                                else
                                    if match_lookahead_terminal(parser, "STRING", 0)
                                        _t1563 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT32", 0)
                                            _t1564 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT128", 0)
                                                _t1565 = 1
                                            else
                                                if match_lookahead_terminal(parser, "INT", 0)
                                                    _t1566 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                        _t1567 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "FLOAT", 0)
                                                            _t1568 = 1
                                                        else
                                                            if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                                _t1569 = 1
                                                            else
                                                                _t1569 = -1
                                                            end
                                                            _t1568 = _t1569
                                                        end
                                                        _t1567 = _t1568
                                                    end
                                                    _t1566 = _t1567
                                                end
                                                _t1565 = _t1566
                                            end
                                            _t1564 = _t1565
                                        end
                                        _t1563 = _t1564
                                    end
                                    _t1562 = _t1563
                                end
                                _t1561 = _t1562
                            end
                            _t1560 = _t1561
                        end
                        _t1559 = _t1560
                    end
                    _t1558 = _t1559
                end
                _t1557 = _t1558
            end
            _t1556 = _t1557
        end
        _t1555 = _t1556
    end
    prediction883 = _t1555
    if prediction883 == 1
        _t1571 = parse_term(parser)
        term885 = _t1571
        _t1572 = Proto.RelTerm(rel_term_type=OneOf(:term, term885))
        _t1570 = _t1572
    else
        if prediction883 == 0
            _t1574 = parse_specialized_value(parser)
            specialized_value884 = _t1574
            _t1575 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value884))
            _t1573 = _t1575
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1570 = _t1573
    end
    result887 = _t1570
    record_span!(parser, span_start886, "RelTerm")
    return result887
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start889 = span_start(parser)
    consume_literal!(parser, "#")
    _t1576 = parse_value(parser)
    value888 = _t1576
    result890 = value888
    record_span!(parser, span_start889, "Value")
    return result890
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start896 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1577 = parse_name(parser)
    name891 = _t1577
    xs892 = Proto.RelTerm[]
    cond893 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond893
        _t1578 = parse_rel_term(parser)
        item894 = _t1578
        push!(xs892, item894)
        cond893 = ((((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    rel_terms895 = xs892
    consume_literal!(parser, ")")
    _t1579 = Proto.RelAtom(name=name891, terms=rel_terms895)
    result897 = _t1579
    record_span!(parser, span_start896, "RelAtom")
    return result897
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start900 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1580 = parse_term(parser)
    term898 = _t1580
    _t1581 = parse_term(parser)
    term_3899 = _t1581
    consume_literal!(parser, ")")
    _t1582 = Proto.Cast(input=term898, result=term_3899)
    result901 = _t1582
    record_span!(parser, span_start900, "Cast")
    return result901
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs902 = Proto.Attribute[]
    cond903 = match_lookahead_literal(parser, "(", 0)
    while cond903
        _t1583 = parse_attribute(parser)
        item904 = _t1583
        push!(xs902, item904)
        cond903 = match_lookahead_literal(parser, "(", 0)
    end
    attributes905 = xs902
    consume_literal!(parser, ")")
    return attributes905
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start911 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1584 = parse_name(parser)
    name906 = _t1584
    xs907 = Proto.Value[]
    cond908 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    while cond908
        _t1585 = parse_value(parser)
        item909 = _t1585
        push!(xs907, item909)
        cond908 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0)) || match_lookahead_terminal(parser, "UINT32", 0))
    end
    values910 = xs907
    consume_literal!(parser, ")")
    _t1586 = Proto.Attribute(name=name906, args=values910)
    result912 = _t1586
    record_span!(parser, span_start911, "Attribute")
    return result912
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start918 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs913 = Proto.RelationId[]
    cond914 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond914
        _t1587 = parse_relation_id(parser)
        item915 = _t1587
        push!(xs913, item915)
        cond914 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids916 = xs913
    _t1588 = parse_script(parser)
    script917 = _t1588
    consume_literal!(parser, ")")
    _t1589 = Proto.Algorithm(var"#global"=relation_ids916, body=script917)
    result919 = _t1589
    record_span!(parser, span_start918, "Algorithm")
    return result919
end

function parse_script(parser::ParserState)::Proto.Script
    span_start924 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs920 = Proto.Construct[]
    cond921 = match_lookahead_literal(parser, "(", 0)
    while cond921
        _t1590 = parse_construct(parser)
        item922 = _t1590
        push!(xs920, item922)
        cond921 = match_lookahead_literal(parser, "(", 0)
    end
    constructs923 = xs920
    consume_literal!(parser, ")")
    _t1591 = Proto.Script(constructs=constructs923)
    result925 = _t1591
    record_span!(parser, span_start924, "Script")
    return result925
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start929 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1593 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1594 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1595 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1596 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1597 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1598 = 1
                            else
                                _t1598 = -1
                            end
                            _t1597 = _t1598
                        end
                        _t1596 = _t1597
                    end
                    _t1595 = _t1596
                end
                _t1594 = _t1595
            end
            _t1593 = _t1594
        end
        _t1592 = _t1593
    else
        _t1592 = -1
    end
    prediction926 = _t1592
    if prediction926 == 1
        _t1600 = parse_instruction(parser)
        instruction928 = _t1600
        _t1601 = Proto.Construct(construct_type=OneOf(:instruction, instruction928))
        _t1599 = _t1601
    else
        if prediction926 == 0
            _t1603 = parse_loop(parser)
            loop927 = _t1603
            _t1604 = Proto.Construct(construct_type=OneOf(:loop, loop927))
            _t1602 = _t1604
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1599 = _t1602
    end
    result930 = _t1599
    record_span!(parser, span_start929, "Construct")
    return result930
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start933 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1605 = parse_init(parser)
    init931 = _t1605
    _t1606 = parse_script(parser)
    script932 = _t1606
    consume_literal!(parser, ")")
    _t1607 = Proto.Loop(init=init931, body=script932)
    result934 = _t1607
    record_span!(parser, span_start933, "Loop")
    return result934
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs935 = Proto.Instruction[]
    cond936 = match_lookahead_literal(parser, "(", 0)
    while cond936
        _t1608 = parse_instruction(parser)
        item937 = _t1608
        push!(xs935, item937)
        cond936 = match_lookahead_literal(parser, "(", 0)
    end
    instructions938 = xs935
    consume_literal!(parser, ")")
    return instructions938
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start945 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1610 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1611 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1612 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1613 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1614 = 0
                        else
                            _t1614 = -1
                        end
                        _t1613 = _t1614
                    end
                    _t1612 = _t1613
                end
                _t1611 = _t1612
            end
            _t1610 = _t1611
        end
        _t1609 = _t1610
    else
        _t1609 = -1
    end
    prediction939 = _t1609
    if prediction939 == 4
        _t1616 = parse_monus_def(parser)
        monus_def944 = _t1616
        _t1617 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def944))
        _t1615 = _t1617
    else
        if prediction939 == 3
            _t1619 = parse_monoid_def(parser)
            monoid_def943 = _t1619
            _t1620 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def943))
            _t1618 = _t1620
        else
            if prediction939 == 2
                _t1622 = parse_break(parser)
                break942 = _t1622
                _t1623 = Proto.Instruction(instr_type=OneOf(:var"#break", break942))
                _t1621 = _t1623
            else
                if prediction939 == 1
                    _t1625 = parse_upsert(parser)
                    upsert941 = _t1625
                    _t1626 = Proto.Instruction(instr_type=OneOf(:upsert, upsert941))
                    _t1624 = _t1626
                else
                    if prediction939 == 0
                        _t1628 = parse_assign(parser)
                        assign940 = _t1628
                        _t1629 = Proto.Instruction(instr_type=OneOf(:assign, assign940))
                        _t1627 = _t1629
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1624 = _t1627
                end
                _t1621 = _t1624
            end
            _t1618 = _t1621
        end
        _t1615 = _t1618
    end
    result946 = _t1615
    record_span!(parser, span_start945, "Instruction")
    return result946
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start950 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1630 = parse_relation_id(parser)
    relation_id947 = _t1630
    _t1631 = parse_abstraction(parser)
    abstraction948 = _t1631
    if match_lookahead_literal(parser, "(", 0)
        _t1633 = parse_attrs(parser)
        _t1632 = _t1633
    else
        _t1632 = nothing
    end
    attrs949 = _t1632
    consume_literal!(parser, ")")
    _t1634 = Proto.Assign(name=relation_id947, body=abstraction948, attrs=(!isnothing(attrs949) ? attrs949 : Proto.Attribute[]))
    result951 = _t1634
    record_span!(parser, span_start950, "Assign")
    return result951
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start955 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1635 = parse_relation_id(parser)
    relation_id952 = _t1635
    _t1636 = parse_abstraction_with_arity(parser)
    abstraction_with_arity953 = _t1636
    if match_lookahead_literal(parser, "(", 0)
        _t1638 = parse_attrs(parser)
        _t1637 = _t1638
    else
        _t1637 = nothing
    end
    attrs954 = _t1637
    consume_literal!(parser, ")")
    _t1639 = Proto.Upsert(name=relation_id952, body=abstraction_with_arity953[1], attrs=(!isnothing(attrs954) ? attrs954 : Proto.Attribute[]), value_arity=abstraction_with_arity953[2])
    result956 = _t1639
    record_span!(parser, span_start955, "Upsert")
    return result956
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1640 = parse_bindings(parser)
    bindings957 = _t1640
    _t1641 = parse_formula(parser)
    formula958 = _t1641
    consume_literal!(parser, ")")
    _t1642 = Proto.Abstraction(vars=vcat(bindings957[1], !isnothing(bindings957[2]) ? bindings957[2] : []), value=formula958)
    return (_t1642, length(bindings957[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start962 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1643 = parse_relation_id(parser)
    relation_id959 = _t1643
    _t1644 = parse_abstraction(parser)
    abstraction960 = _t1644
    if match_lookahead_literal(parser, "(", 0)
        _t1646 = parse_attrs(parser)
        _t1645 = _t1646
    else
        _t1645 = nothing
    end
    attrs961 = _t1645
    consume_literal!(parser, ")")
    _t1647 = Proto.Break(name=relation_id959, body=abstraction960, attrs=(!isnothing(attrs961) ? attrs961 : Proto.Attribute[]))
    result963 = _t1647
    record_span!(parser, span_start962, "Break")
    return result963
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start968 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1648 = parse_monoid(parser)
    monoid964 = _t1648
    _t1649 = parse_relation_id(parser)
    relation_id965 = _t1649
    _t1650 = parse_abstraction_with_arity(parser)
    abstraction_with_arity966 = _t1650
    if match_lookahead_literal(parser, "(", 0)
        _t1652 = parse_attrs(parser)
        _t1651 = _t1652
    else
        _t1651 = nothing
    end
    attrs967 = _t1651
    consume_literal!(parser, ")")
    _t1653 = Proto.MonoidDef(monoid=monoid964, name=relation_id965, body=abstraction_with_arity966[1], attrs=(!isnothing(attrs967) ? attrs967 : Proto.Attribute[]), value_arity=abstraction_with_arity966[2])
    result969 = _t1653
    record_span!(parser, span_start968, "MonoidDef")
    return result969
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start975 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1655 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1656 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1657 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1658 = 2
                    else
                        _t1658 = -1
                    end
                    _t1657 = _t1658
                end
                _t1656 = _t1657
            end
            _t1655 = _t1656
        end
        _t1654 = _t1655
    else
        _t1654 = -1
    end
    prediction970 = _t1654
    if prediction970 == 3
        _t1660 = parse_sum_monoid(parser)
        sum_monoid974 = _t1660
        _t1661 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid974))
        _t1659 = _t1661
    else
        if prediction970 == 2
            _t1663 = parse_max_monoid(parser)
            max_monoid973 = _t1663
            _t1664 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid973))
            _t1662 = _t1664
        else
            if prediction970 == 1
                _t1666 = parse_min_monoid(parser)
                min_monoid972 = _t1666
                _t1667 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid972))
                _t1665 = _t1667
            else
                if prediction970 == 0
                    _t1669 = parse_or_monoid(parser)
                    or_monoid971 = _t1669
                    _t1670 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid971))
                    _t1668 = _t1670
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1665 = _t1668
            end
            _t1662 = _t1665
        end
        _t1659 = _t1662
    end
    result976 = _t1659
    record_span!(parser, span_start975, "Monoid")
    return result976
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start977 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1671 = Proto.OrMonoid()
    result978 = _t1671
    record_span!(parser, span_start977, "OrMonoid")
    return result978
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start980 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1672 = parse_type(parser)
    type979 = _t1672
    consume_literal!(parser, ")")
    _t1673 = Proto.MinMonoid(var"#type"=type979)
    result981 = _t1673
    record_span!(parser, span_start980, "MinMonoid")
    return result981
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start983 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1674 = parse_type(parser)
    type982 = _t1674
    consume_literal!(parser, ")")
    _t1675 = Proto.MaxMonoid(var"#type"=type982)
    result984 = _t1675
    record_span!(parser, span_start983, "MaxMonoid")
    return result984
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start986 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1676 = parse_type(parser)
    type985 = _t1676
    consume_literal!(parser, ")")
    _t1677 = Proto.SumMonoid(var"#type"=type985)
    result987 = _t1677
    record_span!(parser, span_start986, "SumMonoid")
    return result987
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start992 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1678 = parse_monoid(parser)
    monoid988 = _t1678
    _t1679 = parse_relation_id(parser)
    relation_id989 = _t1679
    _t1680 = parse_abstraction_with_arity(parser)
    abstraction_with_arity990 = _t1680
    if match_lookahead_literal(parser, "(", 0)
        _t1682 = parse_attrs(parser)
        _t1681 = _t1682
    else
        _t1681 = nothing
    end
    attrs991 = _t1681
    consume_literal!(parser, ")")
    _t1683 = Proto.MonusDef(monoid=monoid988, name=relation_id989, body=abstraction_with_arity990[1], attrs=(!isnothing(attrs991) ? attrs991 : Proto.Attribute[]), value_arity=abstraction_with_arity990[2])
    result993 = _t1683
    record_span!(parser, span_start992, "MonusDef")
    return result993
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start998 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1684 = parse_relation_id(parser)
    relation_id994 = _t1684
    _t1685 = parse_abstraction(parser)
    abstraction995 = _t1685
    _t1686 = parse_functional_dependency_keys(parser)
    functional_dependency_keys996 = _t1686
    _t1687 = parse_functional_dependency_values(parser)
    functional_dependency_values997 = _t1687
    consume_literal!(parser, ")")
    _t1688 = Proto.FunctionalDependency(guard=abstraction995, keys=functional_dependency_keys996, values=functional_dependency_values997)
    _t1689 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1688), name=relation_id994)
    result999 = _t1689
    record_span!(parser, span_start998, "Constraint")
    return result999
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs1000 = Proto.Var[]
    cond1001 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1001
        _t1690 = parse_var(parser)
        item1002 = _t1690
        push!(xs1000, item1002)
        cond1001 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1003 = xs1000
    consume_literal!(parser, ")")
    return vars1003
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs1004 = Proto.Var[]
    cond1005 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond1005
        _t1691 = parse_var(parser)
        item1006 = _t1691
        push!(xs1004, item1006)
        cond1005 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars1007 = xs1004
    consume_literal!(parser, ")")
    return vars1007
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1012 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "edb", 1)
            _t1693 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1694 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1695 = 1
                else
                    _t1695 = -1
                end
                _t1694 = _t1695
            end
            _t1693 = _t1694
        end
        _t1692 = _t1693
    else
        _t1692 = -1
    end
    prediction1008 = _t1692
    if prediction1008 == 2
        _t1697 = parse_csv_data(parser)
        csv_data1011 = _t1697
        _t1698 = Proto.Data(data_type=OneOf(:csv_data, csv_data1011))
        _t1696 = _t1698
    else
        if prediction1008 == 1
            _t1700 = parse_betree_relation(parser)
            betree_relation1010 = _t1700
            _t1701 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1010))
            _t1699 = _t1701
        else
            if prediction1008 == 0
                _t1703 = parse_edb(parser)
                edb1009 = _t1703
                _t1704 = Proto.Data(data_type=OneOf(:edb, edb1009))
                _t1702 = _t1704
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1699 = _t1702
        end
        _t1696 = _t1699
    end
    result1013 = _t1696
    record_span!(parser, span_start1012, "Data")
    return result1013
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1017 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1705 = parse_relation_id(parser)
    relation_id1014 = _t1705
    _t1706 = parse_edb_path(parser)
    edb_path1015 = _t1706
    _t1707 = parse_edb_types(parser)
    edb_types1016 = _t1707
    consume_literal!(parser, ")")
    _t1708 = Proto.EDB(target_id=relation_id1014, path=edb_path1015, types=edb_types1016)
    result1018 = _t1708
    record_span!(parser, span_start1017, "EDB")
    return result1018
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1019 = String[]
    cond1020 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1020
        item1021 = consume_terminal!(parser, "STRING")
        push!(xs1019, item1021)
        cond1020 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1022 = xs1019
    consume_literal!(parser, "]")
    return strings1022
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1023 = Proto.var"#Type"[]
    cond1024 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1024
        _t1709 = parse_type(parser)
        item1025 = _t1709
        push!(xs1023, item1025)
        cond1024 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1026 = xs1023
    consume_literal!(parser, "]")
    return types1026
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1029 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1710 = parse_relation_id(parser)
    relation_id1027 = _t1710
    _t1711 = parse_betree_info(parser)
    betree_info1028 = _t1711
    consume_literal!(parser, ")")
    _t1712 = Proto.BeTreeRelation(name=relation_id1027, relation_info=betree_info1028)
    result1030 = _t1712
    record_span!(parser, span_start1029, "BeTreeRelation")
    return result1030
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1034 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1713 = parse_betree_info_key_types(parser)
    betree_info_key_types1031 = _t1713
    _t1714 = parse_betree_info_value_types(parser)
    betree_info_value_types1032 = _t1714
    _t1715 = parse_config_dict(parser)
    config_dict1033 = _t1715
    consume_literal!(parser, ")")
    _t1716 = construct_betree_info(parser, betree_info_key_types1031, betree_info_value_types1032, config_dict1033)
    result1035 = _t1716
    record_span!(parser, span_start1034, "BeTreeInfo")
    return result1035
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1036 = Proto.var"#Type"[]
    cond1037 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1037
        _t1717 = parse_type(parser)
        item1038 = _t1717
        push!(xs1036, item1038)
        cond1037 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1039 = xs1036
    consume_literal!(parser, ")")
    return types1039
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1040 = Proto.var"#Type"[]
    cond1041 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1041
        _t1718 = parse_type(parser)
        item1042 = _t1718
        push!(xs1040, item1042)
        cond1041 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1043 = xs1040
    consume_literal!(parser, ")")
    return types1043
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1048 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1719 = parse_csvlocator(parser)
    csvlocator1044 = _t1719
    _t1720 = parse_csv_config(parser)
    csv_config1045 = _t1720
    _t1721 = parse_gnf_columns(parser)
    gnf_columns1046 = _t1721
    _t1722 = parse_csv_asof(parser)
    csv_asof1047 = _t1722
    consume_literal!(parser, ")")
    _t1723 = Proto.CSVData(locator=csvlocator1044, config=csv_config1045, columns=gnf_columns1046, asof=csv_asof1047)
    result1049 = _t1723
    record_span!(parser, span_start1048, "CSVData")
    return result1049
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1052 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1725 = parse_csv_locator_paths(parser)
        _t1724 = _t1725
    else
        _t1724 = nothing
    end
    csv_locator_paths1050 = _t1724
    if match_lookahead_literal(parser, "(", 0)
        _t1727 = parse_csv_locator_inline_data(parser)
        _t1726 = _t1727
    else
        _t1726 = nothing
    end
    csv_locator_inline_data1051 = _t1726
    consume_literal!(parser, ")")
    _t1728 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1050) ? csv_locator_paths1050 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1051) ? csv_locator_inline_data1051 : "")))
    result1053 = _t1728
    record_span!(parser, span_start1052, "CSVLocator")
    return result1053
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1054 = String[]
    cond1055 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1055
        item1056 = consume_terminal!(parser, "STRING")
        push!(xs1054, item1056)
        cond1055 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1057 = xs1054
    consume_literal!(parser, ")")
    return strings1057
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1058 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1058
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1060 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1729 = parse_config_dict(parser)
    config_dict1059 = _t1729
    consume_literal!(parser, ")")
    _t1730 = construct_csv_config(parser, config_dict1059)
    result1061 = _t1730
    record_span!(parser, span_start1060, "CSVConfig")
    return result1061
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1062 = Proto.GNFColumn[]
    cond1063 = match_lookahead_literal(parser, "(", 0)
    while cond1063
        _t1731 = parse_gnf_column(parser)
        item1064 = _t1731
        push!(xs1062, item1064)
        cond1063 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1065 = xs1062
    consume_literal!(parser, ")")
    return gnf_columns1065
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1072 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1732 = parse_gnf_column_path(parser)
    gnf_column_path1066 = _t1732
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1734 = parse_relation_id(parser)
        _t1733 = _t1734
    else
        _t1733 = nothing
    end
    relation_id1067 = _t1733
    consume_literal!(parser, "[")
    xs1068 = Proto.var"#Type"[]
    cond1069 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1069
        _t1735 = parse_type(parser)
        item1070 = _t1735
        push!(xs1068, item1070)
        cond1069 = (((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UINT32", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1071 = xs1068
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1736 = Proto.GNFColumn(column_path=gnf_column_path1066, target_id=relation_id1067, types=types1071)
    result1073 = _t1736
    record_span!(parser, span_start1072, "GNFColumn")
    return result1073
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1737 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1738 = 0
        else
            _t1738 = -1
        end
        _t1737 = _t1738
    end
    prediction1074 = _t1737
    if prediction1074 == 1
        consume_literal!(parser, "[")
        xs1076 = String[]
        cond1077 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1077
            item1078 = consume_terminal!(parser, "STRING")
            push!(xs1076, item1078)
            cond1077 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1079 = xs1076
        consume_literal!(parser, "]")
        _t1739 = strings1079
    else
        if prediction1074 == 0
            string1075 = consume_terminal!(parser, "STRING")
            _t1740 = String[string1075]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1739 = _t1740
    end
    return _t1739
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1080 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1080
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1082 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1741 = parse_fragment_id(parser)
    fragment_id1081 = _t1741
    consume_literal!(parser, ")")
    _t1742 = Proto.Undefine(fragment_id=fragment_id1081)
    result1083 = _t1742
    record_span!(parser, span_start1082, "Undefine")
    return result1083
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1088 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1084 = Proto.RelationId[]
    cond1085 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1085
        _t1743 = parse_relation_id(parser)
        item1086 = _t1743
        push!(xs1084, item1086)
        cond1085 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1087 = xs1084
    consume_literal!(parser, ")")
    _t1744 = Proto.Context(relations=relation_ids1087)
    result1089 = _t1744
    record_span!(parser, span_start1088, "Context")
    return result1089
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1094 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1090 = Proto.SnapshotMapping[]
    cond1091 = match_lookahead_literal(parser, "[", 0)
    while cond1091
        _t1745 = parse_snapshot_mapping(parser)
        item1092 = _t1745
        push!(xs1090, item1092)
        cond1091 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1093 = xs1090
    consume_literal!(parser, ")")
    _t1746 = Proto.Snapshot(mappings=snapshot_mappings1093)
    result1095 = _t1746
    record_span!(parser, span_start1094, "Snapshot")
    return result1095
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1098 = span_start(parser)
    _t1747 = parse_edb_path(parser)
    edb_path1096 = _t1747
    _t1748 = parse_relation_id(parser)
    relation_id1097 = _t1748
    _t1749 = Proto.SnapshotMapping(destination_path=edb_path1096, source_relation=relation_id1097)
    result1099 = _t1749
    record_span!(parser, span_start1098, "SnapshotMapping")
    return result1099
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1100 = Proto.Read[]
    cond1101 = match_lookahead_literal(parser, "(", 0)
    while cond1101
        _t1750 = parse_read(parser)
        item1102 = _t1750
        push!(xs1100, item1102)
        cond1101 = match_lookahead_literal(parser, "(", 0)
    end
    reads1103 = xs1100
    consume_literal!(parser, ")")
    return reads1103
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1110 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1752 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1753 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1754 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1755 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1756 = 3
                        else
                            _t1756 = -1
                        end
                        _t1755 = _t1756
                    end
                    _t1754 = _t1755
                end
                _t1753 = _t1754
            end
            _t1752 = _t1753
        end
        _t1751 = _t1752
    else
        _t1751 = -1
    end
    prediction1104 = _t1751
    if prediction1104 == 4
        _t1758 = parse_export(parser)
        export1109 = _t1758
        _t1759 = Proto.Read(read_type=OneOf(:var"#export", export1109))
        _t1757 = _t1759
    else
        if prediction1104 == 3
            _t1761 = parse_abort(parser)
            abort1108 = _t1761
            _t1762 = Proto.Read(read_type=OneOf(:abort, abort1108))
            _t1760 = _t1762
        else
            if prediction1104 == 2
                _t1764 = parse_what_if(parser)
                what_if1107 = _t1764
                _t1765 = Proto.Read(read_type=OneOf(:what_if, what_if1107))
                _t1763 = _t1765
            else
                if prediction1104 == 1
                    _t1767 = parse_output(parser)
                    output1106 = _t1767
                    _t1768 = Proto.Read(read_type=OneOf(:output, output1106))
                    _t1766 = _t1768
                else
                    if prediction1104 == 0
                        _t1770 = parse_demand(parser)
                        demand1105 = _t1770
                        _t1771 = Proto.Read(read_type=OneOf(:demand, demand1105))
                        _t1769 = _t1771
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1766 = _t1769
                end
                _t1763 = _t1766
            end
            _t1760 = _t1763
        end
        _t1757 = _t1760
    end
    result1111 = _t1757
    record_span!(parser, span_start1110, "Read")
    return result1111
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1113 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1772 = parse_relation_id(parser)
    relation_id1112 = _t1772
    consume_literal!(parser, ")")
    _t1773 = Proto.Demand(relation_id=relation_id1112)
    result1114 = _t1773
    record_span!(parser, span_start1113, "Demand")
    return result1114
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1117 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1774 = parse_name(parser)
    name1115 = _t1774
    _t1775 = parse_relation_id(parser)
    relation_id1116 = _t1775
    consume_literal!(parser, ")")
    _t1776 = Proto.Output(name=name1115, relation_id=relation_id1116)
    result1118 = _t1776
    record_span!(parser, span_start1117, "Output")
    return result1118
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1121 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1777 = parse_name(parser)
    name1119 = _t1777
    _t1778 = parse_epoch(parser)
    epoch1120 = _t1778
    consume_literal!(parser, ")")
    _t1779 = Proto.WhatIf(branch=name1119, epoch=epoch1120)
    result1122 = _t1779
    record_span!(parser, span_start1121, "WhatIf")
    return result1122
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1125 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1781 = parse_name(parser)
        _t1780 = _t1781
    else
        _t1780 = nothing
    end
    name1123 = _t1780
    _t1782 = parse_relation_id(parser)
    relation_id1124 = _t1782
    consume_literal!(parser, ")")
    _t1783 = Proto.Abort(name=(!isnothing(name1123) ? name1123 : "abort"), relation_id=relation_id1124)
    result1126 = _t1783
    record_span!(parser, span_start1125, "Abort")
    return result1126
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1128 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1784 = parse_export_csv_config(parser)
    export_csv_config1127 = _t1784
    consume_literal!(parser, ")")
    _t1785 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1127))
    result1129 = _t1785
    record_span!(parser, span_start1128, "Export")
    return result1129
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1137 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1787 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1788 = 1
            else
                _t1788 = -1
            end
            _t1787 = _t1788
        end
        _t1786 = _t1787
    else
        _t1786 = -1
    end
    prediction1130 = _t1786
    if prediction1130 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1790 = parse_export_csv_path(parser)
        export_csv_path1134 = _t1790
        _t1791 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1135 = _t1791
        _t1792 = parse_config_dict(parser)
        config_dict1136 = _t1792
        consume_literal!(parser, ")")
        _t1793 = construct_export_csv_config(parser, export_csv_path1134, export_csv_columns_list1135, config_dict1136)
        _t1789 = _t1793
    else
        if prediction1130 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1795 = parse_export_csv_path(parser)
            export_csv_path1131 = _t1795
            _t1796 = parse_export_csv_source(parser)
            export_csv_source1132 = _t1796
            _t1797 = parse_csv_config(parser)
            csv_config1133 = _t1797
            consume_literal!(parser, ")")
            _t1798 = construct_export_csv_config_with_source(parser, export_csv_path1131, export_csv_source1132, csv_config1133)
            _t1794 = _t1798
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1789 = _t1794
    end
    result1138 = _t1789
    record_span!(parser, span_start1137, "ExportCSVConfig")
    return result1138
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1139 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1139
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1146 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1800 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1801 = 0
            else
                _t1801 = -1
            end
            _t1800 = _t1801
        end
        _t1799 = _t1800
    else
        _t1799 = -1
    end
    prediction1140 = _t1799
    if prediction1140 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1803 = parse_relation_id(parser)
        relation_id1145 = _t1803
        consume_literal!(parser, ")")
        _t1804 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1145))
        _t1802 = _t1804
    else
        if prediction1140 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1141 = Proto.ExportCSVColumn[]
            cond1142 = match_lookahead_literal(parser, "(", 0)
            while cond1142
                _t1806 = parse_export_csv_column(parser)
                item1143 = _t1806
                push!(xs1141, item1143)
                cond1142 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1144 = xs1141
            consume_literal!(parser, ")")
            _t1807 = Proto.ExportCSVColumns(columns=export_csv_columns1144)
            _t1808 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1807))
            _t1805 = _t1808
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1802 = _t1805
    end
    result1147 = _t1802
    record_span!(parser, span_start1146, "ExportCSVSource")
    return result1147
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1150 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1148 = consume_terminal!(parser, "STRING")
    _t1809 = parse_relation_id(parser)
    relation_id1149 = _t1809
    consume_literal!(parser, ")")
    _t1810 = Proto.ExportCSVColumn(column_name=string1148, column_data=relation_id1149)
    result1151 = _t1810
    record_span!(parser, span_start1150, "ExportCSVColumn")
    return result1151
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1152 = Proto.ExportCSVColumn[]
    cond1153 = match_lookahead_literal(parser, "(", 0)
    while cond1153
        _t1811 = parse_export_csv_column(parser)
        item1154 = _t1811
        push!(xs1152, item1154)
        cond1153 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1155 = xs1152
    consume_literal!(parser, ")")
    return export_csv_columns1155
end


function _check_eof(parser::ParserState)
    if parser.pos <= length(parser.tokens)
        remaining_token = lookahead(parser, 0)
        if remaining_token.type != "\$"
            throw(ParseError("Unexpected token at end of input: $remaining_token"))
        end
    end
    return nothing
end

function parse_transaction(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens, input)
    result = parse_transaction(parser)
    _check_eof(parser)
    return result
end

function parse_fragment(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens, input)
    result = parse_fragment(parser)
    _check_eof(parser)
    return result
end

function parse(input::String)
    lexer = Lexer(input)
    parser = ParserState(lexer.tokens, input)
    result = parse_transaction(parser)
    _check_eof(parser)
    # Add root span at () key
    root_offset = lexer.tokens[1].start_pos
    if haskey(parser.provenance, root_offset)
        parser.provenance[()] = parser.provenance[root_offset]
    end
    return result, parser.provenance
end

# Export main parse functions and error type
export parse, parse_transaction, parse_fragment, ParseError
# Export scanner functions for testing
export scan_string, scan_int, scan_int32, scan_uint32, scan_float, scan_float32, scan_int128, scan_uint128, scan_decimal
# Export Lexer and provenance types for testing
export Lexer, Location, Span

end # module Parser
