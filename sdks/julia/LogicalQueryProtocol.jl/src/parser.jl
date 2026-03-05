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
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return Int32(_get_oneof_field(value, :int_value))
    else
        _t1794 = nothing
    end
    return Int32(default)
end

function _extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Int64)::Int64
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1795 = nothing
    end
    return default
end

function _extract_value_string(parser::ParserState, value::Union{Nothing, Proto.Value}, default::String)::String
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return _get_oneof_field(value, :string_value)
    else
        _t1796 = nothing
    end
    return default
end

function _extract_value_boolean(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Bool)::Bool
    if (!isnothing(value) && _has_proto_field(value, Symbol("boolean_value")))
        return _get_oneof_field(value, :boolean_value)
    else
        _t1797 = nothing
    end
    return default
end

function _extract_value_string_list(parser::ParserState, value::Union{Nothing, Proto.Value}, default::Vector{String})::Vector{String}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return String[_get_oneof_field(value, :string_value)]
    else
        _t1798 = nothing
    end
    return default
end

function _try_extract_value_int64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Int64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("int_value")))
        return _get_oneof_field(value, :int_value)
    else
        _t1799 = nothing
    end
    return nothing
end

function _try_extract_value_float64(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Float64}
    if (!isnothing(value) && _has_proto_field(value, Symbol("float_value")))
        return _get_oneof_field(value, :float_value)
    else
        _t1800 = nothing
    end
    return nothing
end

function _try_extract_value_bytes(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Vector{UInt8}}
    if (!isnothing(value) && _has_proto_field(value, Symbol("string_value")))
        return Vector{UInt8}(_get_oneof_field(value, :string_value))
    else
        _t1801 = nothing
    end
    return nothing
end

function _try_extract_value_uint128(parser::ParserState, value::Union{Nothing, Proto.Value})::Union{Nothing, Proto.UInt128Value}
    if (!isnothing(value) && _has_proto_field(value, Symbol("uint128_value")))
        return _get_oneof_field(value, :uint128_value)
    else
        _t1802 = nothing
    end
    return nothing
end

function construct_csv_config(parser::ParserState, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.CSVConfig
    config = Dict(config_dict)
    _t1803 = _extract_value_int32(parser, get(config, "csv_header_row", nothing), 1)
    header_row = _t1803
    _t1804 = _extract_value_int64(parser, get(config, "csv_skip", nothing), 0)
    skip = _t1804
    _t1805 = _extract_value_string(parser, get(config, "csv_new_line", nothing), "")
    new_line = _t1805
    _t1806 = _extract_value_string(parser, get(config, "csv_delimiter", nothing), ",")
    delimiter = _t1806
    _t1807 = _extract_value_string(parser, get(config, "csv_quotechar", nothing), "\"")
    quotechar = _t1807
    _t1808 = _extract_value_string(parser, get(config, "csv_escapechar", nothing), "\"")
    escapechar = _t1808
    _t1809 = _extract_value_string(parser, get(config, "csv_comment", nothing), "")
    comment = _t1809
    _t1810 = _extract_value_string_list(parser, get(config, "csv_missing_strings", nothing), String[])
    missing_strings = _t1810
    _t1811 = _extract_value_string(parser, get(config, "csv_decimal_separator", nothing), ".")
    decimal_separator = _t1811
    _t1812 = _extract_value_string(parser, get(config, "csv_encoding", nothing), "utf-8")
    encoding = _t1812
    _t1813 = _extract_value_string(parser, get(config, "csv_compression", nothing), "auto")
    compression = _t1813
    _t1814 = _extract_value_int64(parser, get(config, "csv_partition_size_mb", nothing), 0)
    partition_size_mb = _t1814
    _t1815 = Proto.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
    return _t1815
end

function construct_betree_info(parser::ParserState, key_types::Vector{Proto.var"#Type"}, value_types::Vector{Proto.var"#Type"}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.BeTreeInfo
    config = Dict(config_dict)
    _t1816 = _try_extract_value_float64(parser, get(config, "betree_config_epsilon", nothing))
    epsilon = _t1816
    _t1817 = _try_extract_value_int64(parser, get(config, "betree_config_max_pivots", nothing))
    max_pivots = _t1817
    _t1818 = _try_extract_value_int64(parser, get(config, "betree_config_max_deltas", nothing))
    max_deltas = _t1818
    _t1819 = _try_extract_value_int64(parser, get(config, "betree_config_max_leaf", nothing))
    max_leaf = _t1819
    _t1820 = Proto.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
    storage_config = _t1820
    _t1821 = _try_extract_value_uint128(parser, get(config, "betree_locator_root_pageid", nothing))
    root_pageid = _t1821
    _t1822 = _try_extract_value_bytes(parser, get(config, "betree_locator_inline_data", nothing))
    inline_data = _t1822
    _t1823 = _try_extract_value_int64(parser, get(config, "betree_locator_element_count", nothing))
    element_count = _t1823
    _t1824 = _try_extract_value_int64(parser, get(config, "betree_locator_tree_height", nothing))
    tree_height = _t1824
    _t1825 = Proto.BeTreeLocator(location=(!isnothing(root_pageid) ? OneOf(:root_pageid, root_pageid) : (!isnothing(inline_data) ? OneOf(:inline_data, inline_data) : nothing)), element_count=element_count, tree_height=tree_height)
    relation_locator = _t1825
    _t1826 = Proto.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
    return _t1826
end

function default_configure(parser::ParserState)::Proto.Configure
    _t1827 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm_config = _t1827
    _t1828 = Proto.Configure(semantics_version=0, ivm_config=ivm_config)
    return _t1828
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
    _t1829 = Proto.IVMConfig(level=maintenance_level)
    ivm_config = _t1829
    _t1830 = _extract_value_int64(parser, get(config, "semantics_version", nothing), 0)
    semantics_version = _t1830
    _t1831 = Proto.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
    return _t1831
end

function construct_export_csv_config(parser::ParserState, path::String, columns::Vector{Proto.ExportCSVColumn}, config_dict::Vector{Tuple{String, Proto.Value}})::Proto.ExportCSVConfig
    config = Dict(config_dict)
    _t1832 = _extract_value_int64(parser, get(config, "partition_size", nothing), 0)
    partition_size = _t1832
    _t1833 = _extract_value_string(parser, get(config, "compression", nothing), "")
    compression = _t1833
    _t1834 = _extract_value_boolean(parser, get(config, "syntax_header_row", nothing), true)
    syntax_header_row = _t1834
    _t1835 = _extract_value_string(parser, get(config, "syntax_missing_string", nothing), "")
    syntax_missing_string = _t1835
    _t1836 = _extract_value_string(parser, get(config, "syntax_delim", nothing), ",")
    syntax_delim = _t1836
    _t1837 = _extract_value_string(parser, get(config, "syntax_quotechar", nothing), "\"")
    syntax_quotechar = _t1837
    _t1838 = _extract_value_string(parser, get(config, "syntax_escapechar", nothing), "\\")
    syntax_escapechar = _t1838
    _t1839 = Proto.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
    return _t1839
end

function construct_export_csv_config_with_source(parser::ParserState, path::String, csv_source::Proto.ExportCSVSource, csv_config::Proto.CSVConfig)::Proto.ExportCSVConfig
    _t1840 = Proto.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
    return _t1840
end

# --- Parse functions ---

function parse_transaction(parser::ParserState)::Proto.Transaction
    span_start580 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "transaction")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "configure", 1))
        _t1149 = parse_configure(parser)
        _t1148 = _t1149
    else
        _t1148 = nothing
    end
    configure574 = _t1148
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "sync", 1))
        _t1151 = parse_sync(parser)
        _t1150 = _t1151
    else
        _t1150 = nothing
    end
    sync575 = _t1150
    xs576 = Proto.Epoch[]
    cond577 = match_lookahead_literal(parser, "(", 0)
    while cond577
        _t1152 = parse_epoch(parser)
        item578 = _t1152
        push!(xs576, item578)
        cond577 = match_lookahead_literal(parser, "(", 0)
    end
    epochs579 = xs576
    consume_literal!(parser, ")")
    _t1153 = default_configure(parser)
    _t1154 = Proto.Transaction(epochs=epochs579, configure=(!isnothing(configure574) ? configure574 : _t1153), sync=sync575)
    result581 = _t1154
    record_span!(parser, span_start580, "Transaction")
    return result581
end

function parse_configure(parser::ParserState)::Proto.Configure
    span_start583 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "configure")
    _t1155 = parse_config_dict(parser)
    config_dict582 = _t1155
    consume_literal!(parser, ")")
    _t1156 = construct_configure(parser, config_dict582)
    result584 = _t1156
    record_span!(parser, span_start583, "Configure")
    return result584
end

function parse_config_dict(parser::ParserState)::Vector{Tuple{String, Proto.Value}}
    consume_literal!(parser, "{")
    xs585 = Tuple{String, Proto.Value}[]
    cond586 = match_lookahead_literal(parser, ":", 0)
    while cond586
        _t1157 = parse_config_key_value(parser)
        item587 = _t1157
        push!(xs585, item587)
        cond586 = match_lookahead_literal(parser, ":", 0)
    end
    config_key_values588 = xs585
    consume_literal!(parser, "}")
    return config_key_values588
end

function parse_config_key_value(parser::ParserState)::Tuple{String, Proto.Value}
    consume_literal!(parser, ":")
    symbol589 = consume_terminal!(parser, "SYMBOL")
    _t1158 = parse_value(parser)
    value590 = _t1158
    return (symbol589, value590,)
end

function parse_value(parser::ParserState)::Proto.Value
    span_start603 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1159 = 9
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1160 = 8
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1161 = 9
            else
                if match_lookahead_literal(parser, "(", 0)
                    if match_lookahead_literal(parser, "datetime", 1)
                        _t1163 = 1
                    else
                        if match_lookahead_literal(parser, "date", 1)
                            _t1164 = 0
                        else
                            _t1164 = -1
                        end
                        _t1163 = _t1164
                    end
                    _t1162 = _t1163
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1165 = 5
                    else
                        if match_lookahead_terminal(parser, "STRING", 0)
                            _t1166 = 2
                        else
                            if match_lookahead_terminal(parser, "INT32", 0)
                                _t1167 = 10
                            else
                                if match_lookahead_terminal(parser, "INT128", 0)
                                    _t1168 = 6
                                else
                                    if match_lookahead_terminal(parser, "INT", 0)
                                        _t1169 = 3
                                    else
                                        if match_lookahead_terminal(parser, "FLOAT32", 0)
                                            _t1170 = 11
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT", 0)
                                                _t1171 = 4
                                            else
                                                if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                    _t1172 = 7
                                                else
                                                    _t1172 = -1
                                                end
                                                _t1171 = _t1172
                                            end
                                            _t1170 = _t1171
                                        end
                                        _t1169 = _t1170
                                    end
                                    _t1168 = _t1169
                                end
                                _t1167 = _t1168
                            end
                            _t1166 = _t1167
                        end
                        _t1165 = _t1166
                    end
                    _t1162 = _t1165
                end
                _t1161 = _t1162
            end
            _t1160 = _t1161
        end
        _t1159 = _t1160
    end
    prediction591 = _t1159
    if prediction591 == 11
        float32602 = consume_terminal!(parser, "FLOAT32")
        _t1174 = Proto.Value(value=OneOf(:float32_value, float32602))
        _t1173 = _t1174
    else
        if prediction591 == 10
            int32601 = consume_terminal!(parser, "INT32")
            _t1176 = Proto.Value(value=OneOf(:int32_value, int32601))
            _t1175 = _t1176
        else
            if prediction591 == 9
                _t1178 = parse_boolean_value(parser)
                boolean_value600 = _t1178
                _t1179 = Proto.Value(value=OneOf(:boolean_value, boolean_value600))
                _t1177 = _t1179
            else
                if prediction591 == 8
                    consume_literal!(parser, "missing")
                    _t1181 = Proto.MissingValue()
                    _t1182 = Proto.Value(value=OneOf(:missing_value, _t1181))
                    _t1180 = _t1182
                else
                    if prediction591 == 7
                        decimal599 = consume_terminal!(parser, "DECIMAL")
                        _t1184 = Proto.Value(value=OneOf(:decimal_value, decimal599))
                        _t1183 = _t1184
                    else
                        if prediction591 == 6
                            int128598 = consume_terminal!(parser, "INT128")
                            _t1186 = Proto.Value(value=OneOf(:int128_value, int128598))
                            _t1185 = _t1186
                        else
                            if prediction591 == 5
                                uint128597 = consume_terminal!(parser, "UINT128")
                                _t1188 = Proto.Value(value=OneOf(:uint128_value, uint128597))
                                _t1187 = _t1188
                            else
                                if prediction591 == 4
                                    float596 = consume_terminal!(parser, "FLOAT")
                                    _t1190 = Proto.Value(value=OneOf(:float_value, float596))
                                    _t1189 = _t1190
                                else
                                    if prediction591 == 3
                                        int595 = consume_terminal!(parser, "INT")
                                        _t1192 = Proto.Value(value=OneOf(:int_value, int595))
                                        _t1191 = _t1192
                                    else
                                        if prediction591 == 2
                                            string594 = consume_terminal!(parser, "STRING")
                                            _t1194 = Proto.Value(value=OneOf(:string_value, string594))
                                            _t1193 = _t1194
                                        else
                                            if prediction591 == 1
                                                _t1196 = parse_datetime(parser)
                                                datetime593 = _t1196
                                                _t1197 = Proto.Value(value=OneOf(:datetime_value, datetime593))
                                                _t1195 = _t1197
                                            else
                                                if prediction591 == 0
                                                    _t1199 = parse_date(parser)
                                                    date592 = _t1199
                                                    _t1200 = Proto.Value(value=OneOf(:date_value, date592))
                                                    _t1198 = _t1200
                                                else
                                                    throw(ParseError("Unexpected token in value" * ": " * string(lookahead(parser, 0))))
                                                end
                                                _t1195 = _t1198
                                            end
                                            _t1193 = _t1195
                                        end
                                        _t1191 = _t1193
                                    end
                                    _t1189 = _t1191
                                end
                                _t1187 = _t1189
                            end
                            _t1185 = _t1187
                        end
                        _t1183 = _t1185
                    end
                    _t1180 = _t1183
                end
                _t1177 = _t1180
            end
            _t1175 = _t1177
        end
        _t1173 = _t1175
    end
    result604 = _t1173
    record_span!(parser, span_start603, "Value")
    return result604
end

function parse_date(parser::ParserState)::Proto.DateValue
    span_start608 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "date")
    int605 = consume_terminal!(parser, "INT")
    int_3606 = consume_terminal!(parser, "INT")
    int_4607 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1201 = Proto.DateValue(year=Int32(int605), month=Int32(int_3606), day=Int32(int_4607))
    result609 = _t1201
    record_span!(parser, span_start608, "DateValue")
    return result609
end

function parse_datetime(parser::ParserState)::Proto.DateTimeValue
    span_start617 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "datetime")
    int610 = consume_terminal!(parser, "INT")
    int_3611 = consume_terminal!(parser, "INT")
    int_4612 = consume_terminal!(parser, "INT")
    int_5613 = consume_terminal!(parser, "INT")
    int_6614 = consume_terminal!(parser, "INT")
    int_7615 = consume_terminal!(parser, "INT")
    if match_lookahead_terminal(parser, "INT", 0)
        _t1202 = consume_terminal!(parser, "INT")
    else
        _t1202 = nothing
    end
    int_8616 = _t1202
    consume_literal!(parser, ")")
    _t1203 = Proto.DateTimeValue(year=Int32(int610), month=Int32(int_3611), day=Int32(int_4612), hour=Int32(int_5613), minute=Int32(int_6614), second=Int32(int_7615), microsecond=Int32((!isnothing(int_8616) ? int_8616 : 0)))
    result618 = _t1203
    record_span!(parser, span_start617, "DateTimeValue")
    return result618
end

function parse_boolean_value(parser::ParserState)::Bool
    if match_lookahead_literal(parser, "true", 0)
        _t1204 = 0
    else
        if match_lookahead_literal(parser, "false", 0)
            _t1205 = 1
        else
            _t1205 = -1
        end
        _t1204 = _t1205
    end
    prediction619 = _t1204
    if prediction619 == 1
        consume_literal!(parser, "false")
        _t1206 = false
    else
        if prediction619 == 0
            consume_literal!(parser, "true")
            _t1207 = true
        else
            throw(ParseError("Unexpected token in boolean_value" * ": " * string(lookahead(parser, 0))))
        end
        _t1206 = _t1207
    end
    return _t1206
end

function parse_sync(parser::ParserState)::Proto.Sync
    span_start624 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sync")
    xs620 = Proto.FragmentId[]
    cond621 = match_lookahead_literal(parser, ":", 0)
    while cond621
        _t1208 = parse_fragment_id(parser)
        item622 = _t1208
        push!(xs620, item622)
        cond621 = match_lookahead_literal(parser, ":", 0)
    end
    fragment_ids623 = xs620
    consume_literal!(parser, ")")
    _t1209 = Proto.Sync(fragments=fragment_ids623)
    result625 = _t1209
    record_span!(parser, span_start624, "Sync")
    return result625
end

function parse_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start627 = span_start(parser)
    consume_literal!(parser, ":")
    symbol626 = consume_terminal!(parser, "SYMBOL")
    result628 = Proto.FragmentId(Vector{UInt8}(symbol626))
    record_span!(parser, span_start627, "FragmentId")
    return result628
end

function parse_epoch(parser::ParserState)::Proto.Epoch
    span_start631 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "epoch")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "writes", 1))
        _t1211 = parse_epoch_writes(parser)
        _t1210 = _t1211
    else
        _t1210 = nothing
    end
    epoch_writes629 = _t1210
    if match_lookahead_literal(parser, "(", 0)
        _t1213 = parse_epoch_reads(parser)
        _t1212 = _t1213
    else
        _t1212 = nothing
    end
    epoch_reads630 = _t1212
    consume_literal!(parser, ")")
    _t1214 = Proto.Epoch(writes=(!isnothing(epoch_writes629) ? epoch_writes629 : Proto.Write[]), reads=(!isnothing(epoch_reads630) ? epoch_reads630 : Proto.Read[]))
    result632 = _t1214
    record_span!(parser, span_start631, "Epoch")
    return result632
end

function parse_epoch_writes(parser::ParserState)::Vector{Proto.Write}
    consume_literal!(parser, "(")
    consume_literal!(parser, "writes")
    xs633 = Proto.Write[]
    cond634 = match_lookahead_literal(parser, "(", 0)
    while cond634
        _t1215 = parse_write(parser)
        item635 = _t1215
        push!(xs633, item635)
        cond634 = match_lookahead_literal(parser, "(", 0)
    end
    writes636 = xs633
    consume_literal!(parser, ")")
    return writes636
end

function parse_write(parser::ParserState)::Proto.Write
    span_start642 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "undefine", 1)
            _t1217 = 1
        else
            if match_lookahead_literal(parser, "snapshot", 1)
                _t1218 = 3
            else
                if match_lookahead_literal(parser, "define", 1)
                    _t1219 = 0
                else
                    if match_lookahead_literal(parser, "context", 1)
                        _t1220 = 2
                    else
                        _t1220 = -1
                    end
                    _t1219 = _t1220
                end
                _t1218 = _t1219
            end
            _t1217 = _t1218
        end
        _t1216 = _t1217
    else
        _t1216 = -1
    end
    prediction637 = _t1216
    if prediction637 == 3
        _t1222 = parse_snapshot(parser)
        snapshot641 = _t1222
        _t1223 = Proto.Write(write_type=OneOf(:snapshot, snapshot641))
        _t1221 = _t1223
    else
        if prediction637 == 2
            _t1225 = parse_context(parser)
            context640 = _t1225
            _t1226 = Proto.Write(write_type=OneOf(:context, context640))
            _t1224 = _t1226
        else
            if prediction637 == 1
                _t1228 = parse_undefine(parser)
                undefine639 = _t1228
                _t1229 = Proto.Write(write_type=OneOf(:undefine, undefine639))
                _t1227 = _t1229
            else
                if prediction637 == 0
                    _t1231 = parse_define(parser)
                    define638 = _t1231
                    _t1232 = Proto.Write(write_type=OneOf(:define, define638))
                    _t1230 = _t1232
                else
                    throw(ParseError("Unexpected token in write" * ": " * string(lookahead(parser, 0))))
                end
                _t1227 = _t1230
            end
            _t1224 = _t1227
        end
        _t1221 = _t1224
    end
    result643 = _t1221
    record_span!(parser, span_start642, "Write")
    return result643
end

function parse_define(parser::ParserState)::Proto.Define
    span_start645 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "define")
    _t1233 = parse_fragment(parser)
    fragment644 = _t1233
    consume_literal!(parser, ")")
    _t1234 = Proto.Define(fragment=fragment644)
    result646 = _t1234
    record_span!(parser, span_start645, "Define")
    return result646
end

function parse_fragment(parser::ParserState)::Proto.Fragment
    span_start652 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "fragment")
    _t1235 = parse_new_fragment_id(parser)
    new_fragment_id647 = _t1235
    xs648 = Proto.Declaration[]
    cond649 = match_lookahead_literal(parser, "(", 0)
    while cond649
        _t1236 = parse_declaration(parser)
        item650 = _t1236
        push!(xs648, item650)
        cond649 = match_lookahead_literal(parser, "(", 0)
    end
    declarations651 = xs648
    consume_literal!(parser, ")")
    result653 = construct_fragment(parser, new_fragment_id647, declarations651)
    record_span!(parser, span_start652, "Fragment")
    return result653
end

function parse_new_fragment_id(parser::ParserState)::Proto.FragmentId
    span_start655 = span_start(parser)
    _t1237 = parse_fragment_id(parser)
    fragment_id654 = _t1237
    start_fragment!(parser, fragment_id654)
    result656 = fragment_id654
    record_span!(parser, span_start655, "FragmentId")
    return result656
end

function parse_declaration(parser::ParserState)::Proto.Declaration
    span_start662 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "functional_dependency", 1)
            _t1239 = 2
        else
            if match_lookahead_literal(parser, "edb", 1)
                _t1240 = 3
            else
                if match_lookahead_literal(parser, "def", 1)
                    _t1241 = 0
                else
                    if match_lookahead_literal(parser, "csv_data", 1)
                        _t1242 = 3
                    else
                        if match_lookahead_literal(parser, "betree_relation", 1)
                            _t1243 = 3
                        else
                            if match_lookahead_literal(parser, "algorithm", 1)
                                _t1244 = 1
                            else
                                _t1244 = -1
                            end
                            _t1243 = _t1244
                        end
                        _t1242 = _t1243
                    end
                    _t1241 = _t1242
                end
                _t1240 = _t1241
            end
            _t1239 = _t1240
        end
        _t1238 = _t1239
    else
        _t1238 = -1
    end
    prediction657 = _t1238
    if prediction657 == 3
        _t1246 = parse_data(parser)
        data661 = _t1246
        _t1247 = Proto.Declaration(declaration_type=OneOf(:data, data661))
        _t1245 = _t1247
    else
        if prediction657 == 2
            _t1249 = parse_constraint(parser)
            constraint660 = _t1249
            _t1250 = Proto.Declaration(declaration_type=OneOf(:constraint, constraint660))
            _t1248 = _t1250
        else
            if prediction657 == 1
                _t1252 = parse_algorithm(parser)
                algorithm659 = _t1252
                _t1253 = Proto.Declaration(declaration_type=OneOf(:algorithm, algorithm659))
                _t1251 = _t1253
            else
                if prediction657 == 0
                    _t1255 = parse_def(parser)
                    def658 = _t1255
                    _t1256 = Proto.Declaration(declaration_type=OneOf(:def, def658))
                    _t1254 = _t1256
                else
                    throw(ParseError("Unexpected token in declaration" * ": " * string(lookahead(parser, 0))))
                end
                _t1251 = _t1254
            end
            _t1248 = _t1251
        end
        _t1245 = _t1248
    end
    result663 = _t1245
    record_span!(parser, span_start662, "Declaration")
    return result663
end

function parse_def(parser::ParserState)::Proto.Def
    span_start667 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "def")
    _t1257 = parse_relation_id(parser)
    relation_id664 = _t1257
    _t1258 = parse_abstraction(parser)
    abstraction665 = _t1258
    if match_lookahead_literal(parser, "(", 0)
        _t1260 = parse_attrs(parser)
        _t1259 = _t1260
    else
        _t1259 = nothing
    end
    attrs666 = _t1259
    consume_literal!(parser, ")")
    _t1261 = Proto.Def(name=relation_id664, body=abstraction665, attrs=(!isnothing(attrs666) ? attrs666 : Proto.Attribute[]))
    result668 = _t1261
    record_span!(parser, span_start667, "Def")
    return result668
end

function parse_relation_id(parser::ParserState)::Proto.RelationId
    span_start672 = span_start(parser)
    if match_lookahead_literal(parser, ":", 0)
        _t1262 = 0
    else
        if match_lookahead_terminal(parser, "UINT128", 0)
            _t1263 = 1
        else
            _t1263 = -1
        end
        _t1262 = _t1263
    end
    prediction669 = _t1262
    if prediction669 == 1
        uint128671 = consume_terminal!(parser, "UINT128")
        _t1264 = Proto.RelationId(uint128671.low, uint128671.high)
    else
        if prediction669 == 0
            consume_literal!(parser, ":")
            symbol670 = consume_terminal!(parser, "SYMBOL")
            _t1265 = relation_id_from_string(parser, symbol670)
        else
            throw(ParseError("Unexpected token in relation_id" * ": " * string(lookahead(parser, 0))))
        end
        _t1264 = _t1265
    end
    result673 = _t1264
    record_span!(parser, span_start672, "RelationId")
    return result673
end

function parse_abstraction(parser::ParserState)::Proto.Abstraction
    span_start676 = span_start(parser)
    consume_literal!(parser, "(")
    _t1266 = parse_bindings(parser)
    bindings674 = _t1266
    _t1267 = parse_formula(parser)
    formula675 = _t1267
    consume_literal!(parser, ")")
    _t1268 = Proto.Abstraction(vars=vcat(bindings674[1], !isnothing(bindings674[2]) ? bindings674[2] : []), value=formula675)
    result677 = _t1268
    record_span!(parser, span_start676, "Abstraction")
    return result677
end

function parse_bindings(parser::ParserState)::Tuple{Vector{Proto.Binding}, Vector{Proto.Binding}}
    consume_literal!(parser, "[")
    xs678 = Proto.Binding[]
    cond679 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond679
        _t1269 = parse_binding(parser)
        item680 = _t1269
        push!(xs678, item680)
        cond679 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings681 = xs678
    if match_lookahead_literal(parser, "|", 0)
        _t1271 = parse_value_bindings(parser)
        _t1270 = _t1271
    else
        _t1270 = nothing
    end
    value_bindings682 = _t1270
    consume_literal!(parser, "]")
    return (bindings681, (!isnothing(value_bindings682) ? value_bindings682 : Proto.Binding[]),)
end

function parse_binding(parser::ParserState)::Proto.Binding
    span_start685 = span_start(parser)
    symbol683 = consume_terminal!(parser, "SYMBOL")
    consume_literal!(parser, "::")
    _t1272 = parse_type(parser)
    type684 = _t1272
    _t1273 = Proto.Var(name=symbol683)
    _t1274 = Proto.Binding(var=_t1273, var"#type"=type684)
    result686 = _t1274
    record_span!(parser, span_start685, "Binding")
    return result686
end

function parse_type(parser::ParserState)::Proto.var"#Type"
    span_start701 = span_start(parser)
    if match_lookahead_literal(parser, "UNKNOWN", 0)
        _t1275 = 0
    else
        if match_lookahead_literal(parser, "UINT128", 0)
            _t1276 = 4
        else
            if match_lookahead_literal(parser, "STRING", 0)
                _t1277 = 1
            else
                if match_lookahead_literal(parser, "MISSING", 0)
                    _t1278 = 8
                else
                    if match_lookahead_literal(parser, "INT32", 0)
                        _t1279 = 11
                    else
                        if match_lookahead_literal(parser, "INT128", 0)
                            _t1280 = 5
                        else
                            if match_lookahead_literal(parser, "INT", 0)
                                _t1281 = 2
                            else
                                if match_lookahead_literal(parser, "FLOAT32", 0)
                                    _t1282 = 12
                                else
                                    if match_lookahead_literal(parser, "FLOAT", 0)
                                        _t1283 = 3
                                    else
                                        if match_lookahead_literal(parser, "DATETIME", 0)
                                            _t1284 = 7
                                        else
                                            if match_lookahead_literal(parser, "DATE", 0)
                                                _t1285 = 6
                                            else
                                                if match_lookahead_literal(parser, "BOOLEAN", 0)
                                                    _t1286 = 10
                                                else
                                                    if match_lookahead_literal(parser, "(", 0)
                                                        _t1287 = 9
                                                    else
                                                        _t1287 = -1
                                                    end
                                                    _t1286 = _t1287
                                                end
                                                _t1285 = _t1286
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
                        _t1279 = _t1280
                    end
                    _t1278 = _t1279
                end
                _t1277 = _t1278
            end
            _t1276 = _t1277
        end
        _t1275 = _t1276
    end
    prediction687 = _t1275
    if prediction687 == 12
        _t1289 = parse_float32_type(parser)
        float32_type700 = _t1289
        _t1290 = Proto.var"#Type"(var"#type"=OneOf(:float32_type, float32_type700))
        _t1288 = _t1290
    else
        if prediction687 == 11
            _t1292 = parse_int32_type(parser)
            int32_type699 = _t1292
            _t1293 = Proto.var"#Type"(var"#type"=OneOf(:int32_type, int32_type699))
            _t1291 = _t1293
        else
            if prediction687 == 10
                _t1295 = parse_boolean_type(parser)
                boolean_type698 = _t1295
                _t1296 = Proto.var"#Type"(var"#type"=OneOf(:boolean_type, boolean_type698))
                _t1294 = _t1296
            else
                if prediction687 == 9
                    _t1298 = parse_decimal_type(parser)
                    decimal_type697 = _t1298
                    _t1299 = Proto.var"#Type"(var"#type"=OneOf(:decimal_type, decimal_type697))
                    _t1297 = _t1299
                else
                    if prediction687 == 8
                        _t1301 = parse_missing_type(parser)
                        missing_type696 = _t1301
                        _t1302 = Proto.var"#Type"(var"#type"=OneOf(:missing_type, missing_type696))
                        _t1300 = _t1302
                    else
                        if prediction687 == 7
                            _t1304 = parse_datetime_type(parser)
                            datetime_type695 = _t1304
                            _t1305 = Proto.var"#Type"(var"#type"=OneOf(:datetime_type, datetime_type695))
                            _t1303 = _t1305
                        else
                            if prediction687 == 6
                                _t1307 = parse_date_type(parser)
                                date_type694 = _t1307
                                _t1308 = Proto.var"#Type"(var"#type"=OneOf(:date_type, date_type694))
                                _t1306 = _t1308
                            else
                                if prediction687 == 5
                                    _t1310 = parse_int128_type(parser)
                                    int128_type693 = _t1310
                                    _t1311 = Proto.var"#Type"(var"#type"=OneOf(:int128_type, int128_type693))
                                    _t1309 = _t1311
                                else
                                    if prediction687 == 4
                                        _t1313 = parse_uint128_type(parser)
                                        uint128_type692 = _t1313
                                        _t1314 = Proto.var"#Type"(var"#type"=OneOf(:uint128_type, uint128_type692))
                                        _t1312 = _t1314
                                    else
                                        if prediction687 == 3
                                            _t1316 = parse_float_type(parser)
                                            float_type691 = _t1316
                                            _t1317 = Proto.var"#Type"(var"#type"=OneOf(:float_type, float_type691))
                                            _t1315 = _t1317
                                        else
                                            if prediction687 == 2
                                                _t1319 = parse_int_type(parser)
                                                int_type690 = _t1319
                                                _t1320 = Proto.var"#Type"(var"#type"=OneOf(:int_type, int_type690))
                                                _t1318 = _t1320
                                            else
                                                if prediction687 == 1
                                                    _t1322 = parse_string_type(parser)
                                                    string_type689 = _t1322
                                                    _t1323 = Proto.var"#Type"(var"#type"=OneOf(:string_type, string_type689))
                                                    _t1321 = _t1323
                                                else
                                                    if prediction687 == 0
                                                        _t1325 = parse_unspecified_type(parser)
                                                        unspecified_type688 = _t1325
                                                        _t1326 = Proto.var"#Type"(var"#type"=OneOf(:unspecified_type, unspecified_type688))
                                                        _t1324 = _t1326
                                                    else
                                                        throw(ParseError("Unexpected token in type" * ": " * string(lookahead(parser, 0))))
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
                    _t1297 = _t1300
                end
                _t1294 = _t1297
            end
            _t1291 = _t1294
        end
        _t1288 = _t1291
    end
    result702 = _t1288
    record_span!(parser, span_start701, "Type")
    return result702
end

function parse_unspecified_type(parser::ParserState)::Proto.UnspecifiedType
    span_start703 = span_start(parser)
    consume_literal!(parser, "UNKNOWN")
    _t1327 = Proto.UnspecifiedType()
    result704 = _t1327
    record_span!(parser, span_start703, "UnspecifiedType")
    return result704
end

function parse_string_type(parser::ParserState)::Proto.StringType
    span_start705 = span_start(parser)
    consume_literal!(parser, "STRING")
    _t1328 = Proto.StringType()
    result706 = _t1328
    record_span!(parser, span_start705, "StringType")
    return result706
end

function parse_int_type(parser::ParserState)::Proto.IntType
    span_start707 = span_start(parser)
    consume_literal!(parser, "INT")
    _t1329 = Proto.IntType()
    result708 = _t1329
    record_span!(parser, span_start707, "IntType")
    return result708
end

function parse_float_type(parser::ParserState)::Proto.FloatType
    span_start709 = span_start(parser)
    consume_literal!(parser, "FLOAT")
    _t1330 = Proto.FloatType()
    result710 = _t1330
    record_span!(parser, span_start709, "FloatType")
    return result710
end

function parse_uint128_type(parser::ParserState)::Proto.UInt128Type
    span_start711 = span_start(parser)
    consume_literal!(parser, "UINT128")
    _t1331 = Proto.UInt128Type()
    result712 = _t1331
    record_span!(parser, span_start711, "UInt128Type")
    return result712
end

function parse_int128_type(parser::ParserState)::Proto.Int128Type
    span_start713 = span_start(parser)
    consume_literal!(parser, "INT128")
    _t1332 = Proto.Int128Type()
    result714 = _t1332
    record_span!(parser, span_start713, "Int128Type")
    return result714
end

function parse_date_type(parser::ParserState)::Proto.DateType
    span_start715 = span_start(parser)
    consume_literal!(parser, "DATE")
    _t1333 = Proto.DateType()
    result716 = _t1333
    record_span!(parser, span_start715, "DateType")
    return result716
end

function parse_datetime_type(parser::ParserState)::Proto.DateTimeType
    span_start717 = span_start(parser)
    consume_literal!(parser, "DATETIME")
    _t1334 = Proto.DateTimeType()
    result718 = _t1334
    record_span!(parser, span_start717, "DateTimeType")
    return result718
end

function parse_missing_type(parser::ParserState)::Proto.MissingType
    span_start719 = span_start(parser)
    consume_literal!(parser, "MISSING")
    _t1335 = Proto.MissingType()
    result720 = _t1335
    record_span!(parser, span_start719, "MissingType")
    return result720
end

function parse_decimal_type(parser::ParserState)::Proto.DecimalType
    span_start723 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "DECIMAL")
    int721 = consume_terminal!(parser, "INT")
    int_3722 = consume_terminal!(parser, "INT")
    consume_literal!(parser, ")")
    _t1336 = Proto.DecimalType(precision=Int32(int721), scale=Int32(int_3722))
    result724 = _t1336
    record_span!(parser, span_start723, "DecimalType")
    return result724
end

function parse_boolean_type(parser::ParserState)::Proto.BooleanType
    span_start725 = span_start(parser)
    consume_literal!(parser, "BOOLEAN")
    _t1337 = Proto.BooleanType()
    result726 = _t1337
    record_span!(parser, span_start725, "BooleanType")
    return result726
end

function parse_int32_type(parser::ParserState)::Proto.Int32Type
    span_start727 = span_start(parser)
    consume_literal!(parser, "INT32")
    _t1338 = Proto.Int32Type()
    result728 = _t1338
    record_span!(parser, span_start727, "Int32Type")
    return result728
end

function parse_float32_type(parser::ParserState)::Proto.Float32Type
    span_start729 = span_start(parser)
    consume_literal!(parser, "FLOAT32")
    _t1339 = Proto.Float32Type()
    result730 = _t1339
    record_span!(parser, span_start729, "Float32Type")
    return result730
end

function parse_value_bindings(parser::ParserState)::Vector{Proto.Binding}
    consume_literal!(parser, "|")
    xs731 = Proto.Binding[]
    cond732 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond732
        _t1340 = parse_binding(parser)
        item733 = _t1340
        push!(xs731, item733)
        cond732 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    bindings734 = xs731
    return bindings734
end

function parse_formula(parser::ParserState)::Proto.Formula
    span_start749 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "true", 1)
            _t1342 = 0
        else
            if match_lookahead_literal(parser, "relatom", 1)
                _t1343 = 11
            else
                if match_lookahead_literal(parser, "reduce", 1)
                    _t1344 = 3
                else
                    if match_lookahead_literal(parser, "primitive", 1)
                        _t1345 = 10
                    else
                        if match_lookahead_literal(parser, "pragma", 1)
                            _t1346 = 9
                        else
                            if match_lookahead_literal(parser, "or", 1)
                                _t1347 = 5
                            else
                                if match_lookahead_literal(parser, "not", 1)
                                    _t1348 = 6
                                else
                                    if match_lookahead_literal(parser, "ffi", 1)
                                        _t1349 = 7
                                    else
                                        if match_lookahead_literal(parser, "false", 1)
                                            _t1350 = 1
                                        else
                                            if match_lookahead_literal(parser, "exists", 1)
                                                _t1351 = 2
                                            else
                                                if match_lookahead_literal(parser, "cast", 1)
                                                    _t1352 = 12
                                                else
                                                    if match_lookahead_literal(parser, "atom", 1)
                                                        _t1353 = 8
                                                    else
                                                        if match_lookahead_literal(parser, "and", 1)
                                                            _t1354 = 4
                                                        else
                                                            if match_lookahead_literal(parser, ">=", 1)
                                                                _t1355 = 10
                                                            else
                                                                if match_lookahead_literal(parser, ">", 1)
                                                                    _t1356 = 10
                                                                else
                                                                    if match_lookahead_literal(parser, "=", 1)
                                                                        _t1357 = 10
                                                                    else
                                                                        if match_lookahead_literal(parser, "<=", 1)
                                                                            _t1358 = 10
                                                                        else
                                                                            if match_lookahead_literal(parser, "<", 1)
                                                                                _t1359 = 10
                                                                            else
                                                                                if match_lookahead_literal(parser, "/", 1)
                                                                                    _t1360 = 10
                                                                                else
                                                                                    if match_lookahead_literal(parser, "-", 1)
                                                                                        _t1361 = 10
                                                                                    else
                                                                                        if match_lookahead_literal(parser, "+", 1)
                                                                                            _t1362 = 10
                                                                                        else
                                                                                            if match_lookahead_literal(parser, "*", 1)
                                                                                                _t1363 = 10
                                                                                            else
                                                                                                _t1363 = -1
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
                                                                    end
                                                                    _t1356 = _t1357
                                                                end
                                                                _t1355 = _t1356
                                                            end
                                                            _t1354 = _t1355
                                                        end
                                                        _t1353 = _t1354
                                                    end
                                                    _t1352 = _t1353
                                                end
                                                _t1351 = _t1352
                                            end
                                            _t1350 = _t1351
                                        end
                                        _t1349 = _t1350
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
            end
            _t1342 = _t1343
        end
        _t1341 = _t1342
    else
        _t1341 = -1
    end
    prediction735 = _t1341
    if prediction735 == 12
        _t1365 = parse_cast(parser)
        cast748 = _t1365
        _t1366 = Proto.Formula(formula_type=OneOf(:cast, cast748))
        _t1364 = _t1366
    else
        if prediction735 == 11
            _t1368 = parse_rel_atom(parser)
            rel_atom747 = _t1368
            _t1369 = Proto.Formula(formula_type=OneOf(:rel_atom, rel_atom747))
            _t1367 = _t1369
        else
            if prediction735 == 10
                _t1371 = parse_primitive(parser)
                primitive746 = _t1371
                _t1372 = Proto.Formula(formula_type=OneOf(:primitive, primitive746))
                _t1370 = _t1372
            else
                if prediction735 == 9
                    _t1374 = parse_pragma(parser)
                    pragma745 = _t1374
                    _t1375 = Proto.Formula(formula_type=OneOf(:pragma, pragma745))
                    _t1373 = _t1375
                else
                    if prediction735 == 8
                        _t1377 = parse_atom(parser)
                        atom744 = _t1377
                        _t1378 = Proto.Formula(formula_type=OneOf(:atom, atom744))
                        _t1376 = _t1378
                    else
                        if prediction735 == 7
                            _t1380 = parse_ffi(parser)
                            ffi743 = _t1380
                            _t1381 = Proto.Formula(formula_type=OneOf(:ffi, ffi743))
                            _t1379 = _t1381
                        else
                            if prediction735 == 6
                                _t1383 = parse_not(parser)
                                not742 = _t1383
                                _t1384 = Proto.Formula(formula_type=OneOf(:not, not742))
                                _t1382 = _t1384
                            else
                                if prediction735 == 5
                                    _t1386 = parse_disjunction(parser)
                                    disjunction741 = _t1386
                                    _t1387 = Proto.Formula(formula_type=OneOf(:disjunction, disjunction741))
                                    _t1385 = _t1387
                                else
                                    if prediction735 == 4
                                        _t1389 = parse_conjunction(parser)
                                        conjunction740 = _t1389
                                        _t1390 = Proto.Formula(formula_type=OneOf(:conjunction, conjunction740))
                                        _t1388 = _t1390
                                    else
                                        if prediction735 == 3
                                            _t1392 = parse_reduce(parser)
                                            reduce739 = _t1392
                                            _t1393 = Proto.Formula(formula_type=OneOf(:reduce, reduce739))
                                            _t1391 = _t1393
                                        else
                                            if prediction735 == 2
                                                _t1395 = parse_exists(parser)
                                                exists738 = _t1395
                                                _t1396 = Proto.Formula(formula_type=OneOf(:exists, exists738))
                                                _t1394 = _t1396
                                            else
                                                if prediction735 == 1
                                                    _t1398 = parse_false(parser)
                                                    false737 = _t1398
                                                    _t1399 = Proto.Formula(formula_type=OneOf(:disjunction, false737))
                                                    _t1397 = _t1399
                                                else
                                                    if prediction735 == 0
                                                        _t1401 = parse_true(parser)
                                                        true736 = _t1401
                                                        _t1402 = Proto.Formula(formula_type=OneOf(:conjunction, true736))
                                                        _t1400 = _t1402
                                                    else
                                                        throw(ParseError("Unexpected token in formula" * ": " * string(lookahead(parser, 0))))
                                                    end
                                                    _t1397 = _t1400
                                                end
                                                _t1394 = _t1397
                                            end
                                            _t1391 = _t1394
                                        end
                                        _t1388 = _t1391
                                    end
                                    _t1385 = _t1388
                                end
                                _t1382 = _t1385
                            end
                            _t1379 = _t1382
                        end
                        _t1376 = _t1379
                    end
                    _t1373 = _t1376
                end
                _t1370 = _t1373
            end
            _t1367 = _t1370
        end
        _t1364 = _t1367
    end
    result750 = _t1364
    record_span!(parser, span_start749, "Formula")
    return result750
end

function parse_true(parser::ParserState)::Proto.Conjunction
    span_start751 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "true")
    consume_literal!(parser, ")")
    _t1403 = Proto.Conjunction(args=Proto.Formula[])
    result752 = _t1403
    record_span!(parser, span_start751, "Conjunction")
    return result752
end

function parse_false(parser::ParserState)::Proto.Disjunction
    span_start753 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "false")
    consume_literal!(parser, ")")
    _t1404 = Proto.Disjunction(args=Proto.Formula[])
    result754 = _t1404
    record_span!(parser, span_start753, "Disjunction")
    return result754
end

function parse_exists(parser::ParserState)::Proto.Exists
    span_start757 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "exists")
    _t1405 = parse_bindings(parser)
    bindings755 = _t1405
    _t1406 = parse_formula(parser)
    formula756 = _t1406
    consume_literal!(parser, ")")
    _t1407 = Proto.Abstraction(vars=vcat(bindings755[1], !isnothing(bindings755[2]) ? bindings755[2] : []), value=formula756)
    _t1408 = Proto.Exists(body=_t1407)
    result758 = _t1408
    record_span!(parser, span_start757, "Exists")
    return result758
end

function parse_reduce(parser::ParserState)::Proto.Reduce
    span_start762 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "reduce")
    _t1409 = parse_abstraction(parser)
    abstraction759 = _t1409
    _t1410 = parse_abstraction(parser)
    abstraction_3760 = _t1410
    _t1411 = parse_terms(parser)
    terms761 = _t1411
    consume_literal!(parser, ")")
    _t1412 = Proto.Reduce(op=abstraction759, body=abstraction_3760, terms=terms761)
    result763 = _t1412
    record_span!(parser, span_start762, "Reduce")
    return result763
end

function parse_terms(parser::ParserState)::Vector{Proto.Term}
    consume_literal!(parser, "(")
    consume_literal!(parser, "terms")
    xs764 = Proto.Term[]
    cond765 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond765
        _t1413 = parse_term(parser)
        item766 = _t1413
        push!(xs764, item766)
        cond765 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms767 = xs764
    consume_literal!(parser, ")")
    return terms767
end

function parse_term(parser::ParserState)::Proto.Term
    span_start771 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1414 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1415 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1416 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1417 = 1
                else
                    if match_lookahead_terminal(parser, "UINT128", 0)
                        _t1418 = 1
                    else
                        if match_lookahead_terminal(parser, "SYMBOL", 0)
                            _t1419 = 0
                        else
                            if match_lookahead_terminal(parser, "STRING", 0)
                                _t1420 = 1
                            else
                                if match_lookahead_terminal(parser, "INT32", 0)
                                    _t1421 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT128", 0)
                                        _t1422 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT", 0)
                                            _t1423 = 1
                                        else
                                            if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                _t1424 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT", 0)
                                                    _t1425 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                        _t1426 = 1
                                                    else
                                                        _t1426 = -1
                                                    end
                                                    _t1425 = _t1426
                                                end
                                                _t1424 = _t1425
                                            end
                                            _t1423 = _t1424
                                        end
                                        _t1422 = _t1423
                                    end
                                    _t1421 = _t1422
                                end
                                _t1420 = _t1421
                            end
                            _t1419 = _t1420
                        end
                        _t1418 = _t1419
                    end
                    _t1417 = _t1418
                end
                _t1416 = _t1417
            end
            _t1415 = _t1416
        end
        _t1414 = _t1415
    end
    prediction768 = _t1414
    if prediction768 == 1
        _t1428 = parse_constant(parser)
        constant770 = _t1428
        _t1429 = Proto.Term(term_type=OneOf(:constant, constant770))
        _t1427 = _t1429
    else
        if prediction768 == 0
            _t1431 = parse_var(parser)
            var769 = _t1431
            _t1432 = Proto.Term(term_type=OneOf(:var, var769))
            _t1430 = _t1432
        else
            throw(ParseError("Unexpected token in term" * ": " * string(lookahead(parser, 0))))
        end
        _t1427 = _t1430
    end
    result772 = _t1427
    record_span!(parser, span_start771, "Term")
    return result772
end

function parse_var(parser::ParserState)::Proto.Var
    span_start774 = span_start(parser)
    symbol773 = consume_terminal!(parser, "SYMBOL")
    _t1433 = Proto.Var(name=symbol773)
    result775 = _t1433
    record_span!(parser, span_start774, "Var")
    return result775
end

function parse_constant(parser::ParserState)::Proto.Value
    span_start777 = span_start(parser)
    _t1434 = parse_value(parser)
    value776 = _t1434
    result778 = value776
    record_span!(parser, span_start777, "Value")
    return result778
end

function parse_conjunction(parser::ParserState)::Proto.Conjunction
    span_start783 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "and")
    xs779 = Proto.Formula[]
    cond780 = match_lookahead_literal(parser, "(", 0)
    while cond780
        _t1435 = parse_formula(parser)
        item781 = _t1435
        push!(xs779, item781)
        cond780 = match_lookahead_literal(parser, "(", 0)
    end
    formulas782 = xs779
    consume_literal!(parser, ")")
    _t1436 = Proto.Conjunction(args=formulas782)
    result784 = _t1436
    record_span!(parser, span_start783, "Conjunction")
    return result784
end

function parse_disjunction(parser::ParserState)::Proto.Disjunction
    span_start789 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    xs785 = Proto.Formula[]
    cond786 = match_lookahead_literal(parser, "(", 0)
    while cond786
        _t1437 = parse_formula(parser)
        item787 = _t1437
        push!(xs785, item787)
        cond786 = match_lookahead_literal(parser, "(", 0)
    end
    formulas788 = xs785
    consume_literal!(parser, ")")
    _t1438 = Proto.Disjunction(args=formulas788)
    result790 = _t1438
    record_span!(parser, span_start789, "Disjunction")
    return result790
end

function parse_not(parser::ParserState)::Proto.Not
    span_start792 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "not")
    _t1439 = parse_formula(parser)
    formula791 = _t1439
    consume_literal!(parser, ")")
    _t1440 = Proto.Not(arg=formula791)
    result793 = _t1440
    record_span!(parser, span_start792, "Not")
    return result793
end

function parse_ffi(parser::ParserState)::Proto.FFI
    span_start797 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "ffi")
    _t1441 = parse_name(parser)
    name794 = _t1441
    _t1442 = parse_ffi_args(parser)
    ffi_args795 = _t1442
    _t1443 = parse_terms(parser)
    terms796 = _t1443
    consume_literal!(parser, ")")
    _t1444 = Proto.FFI(name=name794, args=ffi_args795, terms=terms796)
    result798 = _t1444
    record_span!(parser, span_start797, "FFI")
    return result798
end

function parse_name(parser::ParserState)::String
    consume_literal!(parser, ":")
    symbol799 = consume_terminal!(parser, "SYMBOL")
    return symbol799
end

function parse_ffi_args(parser::ParserState)::Vector{Proto.Abstraction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "args")
    xs800 = Proto.Abstraction[]
    cond801 = match_lookahead_literal(parser, "(", 0)
    while cond801
        _t1445 = parse_abstraction(parser)
        item802 = _t1445
        push!(xs800, item802)
        cond801 = match_lookahead_literal(parser, "(", 0)
    end
    abstractions803 = xs800
    consume_literal!(parser, ")")
    return abstractions803
end

function parse_atom(parser::ParserState)::Proto.Atom
    span_start809 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "atom")
    _t1446 = parse_relation_id(parser)
    relation_id804 = _t1446
    xs805 = Proto.Term[]
    cond806 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond806
        _t1447 = parse_term(parser)
        item807 = _t1447
        push!(xs805, item807)
        cond806 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms808 = xs805
    consume_literal!(parser, ")")
    _t1448 = Proto.Atom(name=relation_id804, terms=terms808)
    result810 = _t1448
    record_span!(parser, span_start809, "Atom")
    return result810
end

function parse_pragma(parser::ParserState)::Proto.Pragma
    span_start816 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "pragma")
    _t1449 = parse_name(parser)
    name811 = _t1449
    xs812 = Proto.Term[]
    cond813 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond813
        _t1450 = parse_term(parser)
        item814 = _t1450
        push!(xs812, item814)
        cond813 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    terms815 = xs812
    consume_literal!(parser, ")")
    _t1451 = Proto.Pragma(name=name811, terms=terms815)
    result817 = _t1451
    record_span!(parser, span_start816, "Pragma")
    return result817
end

function parse_primitive(parser::ParserState)::Proto.Primitive
    span_start833 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "primitive", 1)
            _t1453 = 9
        else
            if match_lookahead_literal(parser, ">=", 1)
                _t1454 = 4
            else
                if match_lookahead_literal(parser, ">", 1)
                    _t1455 = 3
                else
                    if match_lookahead_literal(parser, "=", 1)
                        _t1456 = 0
                    else
                        if match_lookahead_literal(parser, "<=", 1)
                            _t1457 = 2
                        else
                            if match_lookahead_literal(parser, "<", 1)
                                _t1458 = 1
                            else
                                if match_lookahead_literal(parser, "/", 1)
                                    _t1459 = 8
                                else
                                    if match_lookahead_literal(parser, "-", 1)
                                        _t1460 = 6
                                    else
                                        if match_lookahead_literal(parser, "+", 1)
                                            _t1461 = 5
                                        else
                                            if match_lookahead_literal(parser, "*", 1)
                                                _t1462 = 7
                                            else
                                                _t1462 = -1
                                            end
                                            _t1461 = _t1462
                                        end
                                        _t1460 = _t1461
                                    end
                                    _t1459 = _t1460
                                end
                                _t1458 = _t1459
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
    else
        _t1452 = -1
    end
    prediction818 = _t1452
    if prediction818 == 9
        consume_literal!(parser, "(")
        consume_literal!(parser, "primitive")
        _t1464 = parse_name(parser)
        name828 = _t1464
        xs829 = Proto.RelTerm[]
        cond830 = (((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        while cond830
            _t1465 = parse_rel_term(parser)
            item831 = _t1465
            push!(xs829, item831)
            cond830 = (((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
        end
        rel_terms832 = xs829
        consume_literal!(parser, ")")
        _t1466 = Proto.Primitive(name=name828, terms=rel_terms832)
        _t1463 = _t1466
    else
        if prediction818 == 8
            _t1468 = parse_divide(parser)
            divide827 = _t1468
            _t1467 = divide827
        else
            if prediction818 == 7
                _t1470 = parse_multiply(parser)
                multiply826 = _t1470
                _t1469 = multiply826
            else
                if prediction818 == 6
                    _t1472 = parse_minus(parser)
                    minus825 = _t1472
                    _t1471 = minus825
                else
                    if prediction818 == 5
                        _t1474 = parse_add(parser)
                        add824 = _t1474
                        _t1473 = add824
                    else
                        if prediction818 == 4
                            _t1476 = parse_gt_eq(parser)
                            gt_eq823 = _t1476
                            _t1475 = gt_eq823
                        else
                            if prediction818 == 3
                                _t1478 = parse_gt(parser)
                                gt822 = _t1478
                                _t1477 = gt822
                            else
                                if prediction818 == 2
                                    _t1480 = parse_lt_eq(parser)
                                    lt_eq821 = _t1480
                                    _t1479 = lt_eq821
                                else
                                    if prediction818 == 1
                                        _t1482 = parse_lt(parser)
                                        lt820 = _t1482
                                        _t1481 = lt820
                                    else
                                        if prediction818 == 0
                                            _t1484 = parse_eq(parser)
                                            eq819 = _t1484
                                            _t1483 = eq819
                                        else
                                            throw(ParseError("Unexpected token in primitive" * ": " * string(lookahead(parser, 0))))
                                        end
                                        _t1481 = _t1483
                                    end
                                    _t1479 = _t1481
                                end
                                _t1477 = _t1479
                            end
                            _t1475 = _t1477
                        end
                        _t1473 = _t1475
                    end
                    _t1471 = _t1473
                end
                _t1469 = _t1471
            end
            _t1467 = _t1469
        end
        _t1463 = _t1467
    end
    result834 = _t1463
    record_span!(parser, span_start833, "Primitive")
    return result834
end

function parse_eq(parser::ParserState)::Proto.Primitive
    span_start837 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "=")
    _t1485 = parse_term(parser)
    term835 = _t1485
    _t1486 = parse_term(parser)
    term_3836 = _t1486
    consume_literal!(parser, ")")
    _t1487 = Proto.RelTerm(rel_term_type=OneOf(:term, term835))
    _t1488 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3836))
    _t1489 = Proto.Primitive(name="rel_primitive_eq", terms=Proto.RelTerm[_t1487, _t1488])
    result838 = _t1489
    record_span!(parser, span_start837, "Primitive")
    return result838
end

function parse_lt(parser::ParserState)::Proto.Primitive
    span_start841 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<")
    _t1490 = parse_term(parser)
    term839 = _t1490
    _t1491 = parse_term(parser)
    term_3840 = _t1491
    consume_literal!(parser, ")")
    _t1492 = Proto.RelTerm(rel_term_type=OneOf(:term, term839))
    _t1493 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3840))
    _t1494 = Proto.Primitive(name="rel_primitive_lt_monotype", terms=Proto.RelTerm[_t1492, _t1493])
    result842 = _t1494
    record_span!(parser, span_start841, "Primitive")
    return result842
end

function parse_lt_eq(parser::ParserState)::Proto.Primitive
    span_start845 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "<=")
    _t1495 = parse_term(parser)
    term843 = _t1495
    _t1496 = parse_term(parser)
    term_3844 = _t1496
    consume_literal!(parser, ")")
    _t1497 = Proto.RelTerm(rel_term_type=OneOf(:term, term843))
    _t1498 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3844))
    _t1499 = Proto.Primitive(name="rel_primitive_lt_eq_monotype", terms=Proto.RelTerm[_t1497, _t1498])
    result846 = _t1499
    record_span!(parser, span_start845, "Primitive")
    return result846
end

function parse_gt(parser::ParserState)::Proto.Primitive
    span_start849 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">")
    _t1500 = parse_term(parser)
    term847 = _t1500
    _t1501 = parse_term(parser)
    term_3848 = _t1501
    consume_literal!(parser, ")")
    _t1502 = Proto.RelTerm(rel_term_type=OneOf(:term, term847))
    _t1503 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3848))
    _t1504 = Proto.Primitive(name="rel_primitive_gt_monotype", terms=Proto.RelTerm[_t1502, _t1503])
    result850 = _t1504
    record_span!(parser, span_start849, "Primitive")
    return result850
end

function parse_gt_eq(parser::ParserState)::Proto.Primitive
    span_start853 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, ">=")
    _t1505 = parse_term(parser)
    term851 = _t1505
    _t1506 = parse_term(parser)
    term_3852 = _t1506
    consume_literal!(parser, ")")
    _t1507 = Proto.RelTerm(rel_term_type=OneOf(:term, term851))
    _t1508 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3852))
    _t1509 = Proto.Primitive(name="rel_primitive_gt_eq_monotype", terms=Proto.RelTerm[_t1507, _t1508])
    result854 = _t1509
    record_span!(parser, span_start853, "Primitive")
    return result854
end

function parse_add(parser::ParserState)::Proto.Primitive
    span_start858 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "+")
    _t1510 = parse_term(parser)
    term855 = _t1510
    _t1511 = parse_term(parser)
    term_3856 = _t1511
    _t1512 = parse_term(parser)
    term_4857 = _t1512
    consume_literal!(parser, ")")
    _t1513 = Proto.RelTerm(rel_term_type=OneOf(:term, term855))
    _t1514 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3856))
    _t1515 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4857))
    _t1516 = Proto.Primitive(name="rel_primitive_add_monotype", terms=Proto.RelTerm[_t1513, _t1514, _t1515])
    result859 = _t1516
    record_span!(parser, span_start858, "Primitive")
    return result859
end

function parse_minus(parser::ParserState)::Proto.Primitive
    span_start863 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "-")
    _t1517 = parse_term(parser)
    term860 = _t1517
    _t1518 = parse_term(parser)
    term_3861 = _t1518
    _t1519 = parse_term(parser)
    term_4862 = _t1519
    consume_literal!(parser, ")")
    _t1520 = Proto.RelTerm(rel_term_type=OneOf(:term, term860))
    _t1521 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3861))
    _t1522 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4862))
    _t1523 = Proto.Primitive(name="rel_primitive_subtract_monotype", terms=Proto.RelTerm[_t1520, _t1521, _t1522])
    result864 = _t1523
    record_span!(parser, span_start863, "Primitive")
    return result864
end

function parse_multiply(parser::ParserState)::Proto.Primitive
    span_start868 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "*")
    _t1524 = parse_term(parser)
    term865 = _t1524
    _t1525 = parse_term(parser)
    term_3866 = _t1525
    _t1526 = parse_term(parser)
    term_4867 = _t1526
    consume_literal!(parser, ")")
    _t1527 = Proto.RelTerm(rel_term_type=OneOf(:term, term865))
    _t1528 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3866))
    _t1529 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4867))
    _t1530 = Proto.Primitive(name="rel_primitive_multiply_monotype", terms=Proto.RelTerm[_t1527, _t1528, _t1529])
    result869 = _t1530
    record_span!(parser, span_start868, "Primitive")
    return result869
end

function parse_divide(parser::ParserState)::Proto.Primitive
    span_start873 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "/")
    _t1531 = parse_term(parser)
    term870 = _t1531
    _t1532 = parse_term(parser)
    term_3871 = _t1532
    _t1533 = parse_term(parser)
    term_4872 = _t1533
    consume_literal!(parser, ")")
    _t1534 = Proto.RelTerm(rel_term_type=OneOf(:term, term870))
    _t1535 = Proto.RelTerm(rel_term_type=OneOf(:term, term_3871))
    _t1536 = Proto.RelTerm(rel_term_type=OneOf(:term, term_4872))
    _t1537 = Proto.Primitive(name="rel_primitive_divide_monotype", terms=Proto.RelTerm[_t1534, _t1535, _t1536])
    result874 = _t1537
    record_span!(parser, span_start873, "Primitive")
    return result874
end

function parse_rel_term(parser::ParserState)::Proto.RelTerm
    span_start878 = span_start(parser)
    if match_lookahead_literal(parser, "true", 0)
        _t1538 = 1
    else
        if match_lookahead_literal(parser, "missing", 0)
            _t1539 = 1
        else
            if match_lookahead_literal(parser, "false", 0)
                _t1540 = 1
            else
                if match_lookahead_literal(parser, "(", 0)
                    _t1541 = 1
                else
                    if match_lookahead_literal(parser, "#", 0)
                        _t1542 = 0
                    else
                        if match_lookahead_terminal(parser, "UINT128", 0)
                            _t1543 = 1
                        else
                            if match_lookahead_terminal(parser, "SYMBOL", 0)
                                _t1544 = 1
                            else
                                if match_lookahead_terminal(parser, "STRING", 0)
                                    _t1545 = 1
                                else
                                    if match_lookahead_terminal(parser, "INT32", 0)
                                        _t1546 = 1
                                    else
                                        if match_lookahead_terminal(parser, "INT128", 0)
                                            _t1547 = 1
                                        else
                                            if match_lookahead_terminal(parser, "INT", 0)
                                                _t1548 = 1
                                            else
                                                if match_lookahead_terminal(parser, "FLOAT32", 0)
                                                    _t1549 = 1
                                                else
                                                    if match_lookahead_terminal(parser, "FLOAT", 0)
                                                        _t1550 = 1
                                                    else
                                                        if match_lookahead_terminal(parser, "DECIMAL", 0)
                                                            _t1551 = 1
                                                        else
                                                            _t1551 = -1
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
                                end
                                _t1544 = _t1545
                            end
                            _t1543 = _t1544
                        end
                        _t1542 = _t1543
                    end
                    _t1541 = _t1542
                end
                _t1540 = _t1541
            end
            _t1539 = _t1540
        end
        _t1538 = _t1539
    end
    prediction875 = _t1538
    if prediction875 == 1
        _t1553 = parse_term(parser)
        term877 = _t1553
        _t1554 = Proto.RelTerm(rel_term_type=OneOf(:term, term877))
        _t1552 = _t1554
    else
        if prediction875 == 0
            _t1556 = parse_specialized_value(parser)
            specialized_value876 = _t1556
            _t1557 = Proto.RelTerm(rel_term_type=OneOf(:specialized_value, specialized_value876))
            _t1555 = _t1557
        else
            throw(ParseError("Unexpected token in rel_term" * ": " * string(lookahead(parser, 0))))
        end
        _t1552 = _t1555
    end
    result879 = _t1552
    record_span!(parser, span_start878, "RelTerm")
    return result879
end

function parse_specialized_value(parser::ParserState)::Proto.Value
    span_start881 = span_start(parser)
    consume_literal!(parser, "#")
    _t1558 = parse_value(parser)
    value880 = _t1558
    result882 = value880
    record_span!(parser, span_start881, "Value")
    return result882
end

function parse_rel_atom(parser::ParserState)::Proto.RelAtom
    span_start888 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "relatom")
    _t1559 = parse_name(parser)
    name883 = _t1559
    xs884 = Proto.RelTerm[]
    cond885 = (((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond885
        _t1560 = parse_rel_term(parser)
        item886 = _t1560
        push!(xs884, item886)
        cond885 = (((((((((((((match_lookahead_literal(parser, "#", 0) || match_lookahead_literal(parser, "(", 0)) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "SYMBOL", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    rel_terms887 = xs884
    consume_literal!(parser, ")")
    _t1561 = Proto.RelAtom(name=name883, terms=rel_terms887)
    result889 = _t1561
    record_span!(parser, span_start888, "RelAtom")
    return result889
end

function parse_cast(parser::ParserState)::Proto.Cast
    span_start892 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "cast")
    _t1562 = parse_term(parser)
    term890 = _t1562
    _t1563 = parse_term(parser)
    term_3891 = _t1563
    consume_literal!(parser, ")")
    _t1564 = Proto.Cast(input=term890, result=term_3891)
    result893 = _t1564
    record_span!(parser, span_start892, "Cast")
    return result893
end

function parse_attrs(parser::ParserState)::Vector{Proto.Attribute}
    consume_literal!(parser, "(")
    consume_literal!(parser, "attrs")
    xs894 = Proto.Attribute[]
    cond895 = match_lookahead_literal(parser, "(", 0)
    while cond895
        _t1565 = parse_attribute(parser)
        item896 = _t1565
        push!(xs894, item896)
        cond895 = match_lookahead_literal(parser, "(", 0)
    end
    attributes897 = xs894
    consume_literal!(parser, ")")
    return attributes897
end

function parse_attribute(parser::ParserState)::Proto.Attribute
    span_start903 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "attribute")
    _t1566 = parse_name(parser)
    name898 = _t1566
    xs899 = Proto.Value[]
    cond900 = (((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond900
        _t1567 = parse_value(parser)
        item901 = _t1567
        push!(xs899, item901)
        cond900 = (((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "false", 0)) || match_lookahead_literal(parser, "missing", 0)) || match_lookahead_literal(parser, "true", 0)) || match_lookahead_terminal(parser, "DECIMAL", 0)) || match_lookahead_terminal(parser, "FLOAT", 0)) || match_lookahead_terminal(parser, "FLOAT32", 0)) || match_lookahead_terminal(parser, "INT", 0)) || match_lookahead_terminal(parser, "INT128", 0)) || match_lookahead_terminal(parser, "INT32", 0)) || match_lookahead_terminal(parser, "STRING", 0)) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    values902 = xs899
    consume_literal!(parser, ")")
    _t1568 = Proto.Attribute(name=name898, args=values902)
    result904 = _t1568
    record_span!(parser, span_start903, "Attribute")
    return result904
end

function parse_algorithm(parser::ParserState)::Proto.Algorithm
    span_start910 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "algorithm")
    xs905 = Proto.RelationId[]
    cond906 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond906
        _t1569 = parse_relation_id(parser)
        item907 = _t1569
        push!(xs905, item907)
        cond906 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids908 = xs905
    _t1570 = parse_script(parser)
    script909 = _t1570
    consume_literal!(parser, ")")
    _t1571 = Proto.Algorithm(var"#global"=relation_ids908, body=script909)
    result911 = _t1571
    record_span!(parser, span_start910, "Algorithm")
    return result911
end

function parse_script(parser::ParserState)::Proto.Script
    span_start916 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "script")
    xs912 = Proto.Construct[]
    cond913 = match_lookahead_literal(parser, "(", 0)
    while cond913
        _t1572 = parse_construct(parser)
        item914 = _t1572
        push!(xs912, item914)
        cond913 = match_lookahead_literal(parser, "(", 0)
    end
    constructs915 = xs912
    consume_literal!(parser, ")")
    _t1573 = Proto.Script(constructs=constructs915)
    result917 = _t1573
    record_span!(parser, span_start916, "Script")
    return result917
end

function parse_construct(parser::ParserState)::Proto.Construct
    span_start921 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1575 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1576 = 1
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1577 = 1
                else
                    if match_lookahead_literal(parser, "loop", 1)
                        _t1578 = 0
                    else
                        if match_lookahead_literal(parser, "break", 1)
                            _t1579 = 1
                        else
                            if match_lookahead_literal(parser, "assign", 1)
                                _t1580 = 1
                            else
                                _t1580 = -1
                            end
                            _t1579 = _t1580
                        end
                        _t1578 = _t1579
                    end
                    _t1577 = _t1578
                end
                _t1576 = _t1577
            end
            _t1575 = _t1576
        end
        _t1574 = _t1575
    else
        _t1574 = -1
    end
    prediction918 = _t1574
    if prediction918 == 1
        _t1582 = parse_instruction(parser)
        instruction920 = _t1582
        _t1583 = Proto.Construct(construct_type=OneOf(:instruction, instruction920))
        _t1581 = _t1583
    else
        if prediction918 == 0
            _t1585 = parse_loop(parser)
            loop919 = _t1585
            _t1586 = Proto.Construct(construct_type=OneOf(:loop, loop919))
            _t1584 = _t1586
        else
            throw(ParseError("Unexpected token in construct" * ": " * string(lookahead(parser, 0))))
        end
        _t1581 = _t1584
    end
    result922 = _t1581
    record_span!(parser, span_start921, "Construct")
    return result922
end

function parse_loop(parser::ParserState)::Proto.Loop
    span_start925 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "loop")
    _t1587 = parse_init(parser)
    init923 = _t1587
    _t1588 = parse_script(parser)
    script924 = _t1588
    consume_literal!(parser, ")")
    _t1589 = Proto.Loop(init=init923, body=script924)
    result926 = _t1589
    record_span!(parser, span_start925, "Loop")
    return result926
end

function parse_init(parser::ParserState)::Vector{Proto.Instruction}
    consume_literal!(parser, "(")
    consume_literal!(parser, "init")
    xs927 = Proto.Instruction[]
    cond928 = match_lookahead_literal(parser, "(", 0)
    while cond928
        _t1590 = parse_instruction(parser)
        item929 = _t1590
        push!(xs927, item929)
        cond928 = match_lookahead_literal(parser, "(", 0)
    end
    instructions930 = xs927
    consume_literal!(parser, ")")
    return instructions930
end

function parse_instruction(parser::ParserState)::Proto.Instruction
    span_start937 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "upsert", 1)
            _t1592 = 1
        else
            if match_lookahead_literal(parser, "monus", 1)
                _t1593 = 4
            else
                if match_lookahead_literal(parser, "monoid", 1)
                    _t1594 = 3
                else
                    if match_lookahead_literal(parser, "break", 1)
                        _t1595 = 2
                    else
                        if match_lookahead_literal(parser, "assign", 1)
                            _t1596 = 0
                        else
                            _t1596 = -1
                        end
                        _t1595 = _t1596
                    end
                    _t1594 = _t1595
                end
                _t1593 = _t1594
            end
            _t1592 = _t1593
        end
        _t1591 = _t1592
    else
        _t1591 = -1
    end
    prediction931 = _t1591
    if prediction931 == 4
        _t1598 = parse_monus_def(parser)
        monus_def936 = _t1598
        _t1599 = Proto.Instruction(instr_type=OneOf(:monus_def, monus_def936))
        _t1597 = _t1599
    else
        if prediction931 == 3
            _t1601 = parse_monoid_def(parser)
            monoid_def935 = _t1601
            _t1602 = Proto.Instruction(instr_type=OneOf(:monoid_def, monoid_def935))
            _t1600 = _t1602
        else
            if prediction931 == 2
                _t1604 = parse_break(parser)
                break934 = _t1604
                _t1605 = Proto.Instruction(instr_type=OneOf(:var"#break", break934))
                _t1603 = _t1605
            else
                if prediction931 == 1
                    _t1607 = parse_upsert(parser)
                    upsert933 = _t1607
                    _t1608 = Proto.Instruction(instr_type=OneOf(:upsert, upsert933))
                    _t1606 = _t1608
                else
                    if prediction931 == 0
                        _t1610 = parse_assign(parser)
                        assign932 = _t1610
                        _t1611 = Proto.Instruction(instr_type=OneOf(:assign, assign932))
                        _t1609 = _t1611
                    else
                        throw(ParseError("Unexpected token in instruction" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1606 = _t1609
                end
                _t1603 = _t1606
            end
            _t1600 = _t1603
        end
        _t1597 = _t1600
    end
    result938 = _t1597
    record_span!(parser, span_start937, "Instruction")
    return result938
end

function parse_assign(parser::ParserState)::Proto.Assign
    span_start942 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "assign")
    _t1612 = parse_relation_id(parser)
    relation_id939 = _t1612
    _t1613 = parse_abstraction(parser)
    abstraction940 = _t1613
    if match_lookahead_literal(parser, "(", 0)
        _t1615 = parse_attrs(parser)
        _t1614 = _t1615
    else
        _t1614 = nothing
    end
    attrs941 = _t1614
    consume_literal!(parser, ")")
    _t1616 = Proto.Assign(name=relation_id939, body=abstraction940, attrs=(!isnothing(attrs941) ? attrs941 : Proto.Attribute[]))
    result943 = _t1616
    record_span!(parser, span_start942, "Assign")
    return result943
end

function parse_upsert(parser::ParserState)::Proto.Upsert
    span_start947 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "upsert")
    _t1617 = parse_relation_id(parser)
    relation_id944 = _t1617
    _t1618 = parse_abstraction_with_arity(parser)
    abstraction_with_arity945 = _t1618
    if match_lookahead_literal(parser, "(", 0)
        _t1620 = parse_attrs(parser)
        _t1619 = _t1620
    else
        _t1619 = nothing
    end
    attrs946 = _t1619
    consume_literal!(parser, ")")
    _t1621 = Proto.Upsert(name=relation_id944, body=abstraction_with_arity945[1], attrs=(!isnothing(attrs946) ? attrs946 : Proto.Attribute[]), value_arity=abstraction_with_arity945[2])
    result948 = _t1621
    record_span!(parser, span_start947, "Upsert")
    return result948
end

function parse_abstraction_with_arity(parser::ParserState)::Tuple{Proto.Abstraction, Int64}
    consume_literal!(parser, "(")
    _t1622 = parse_bindings(parser)
    bindings949 = _t1622
    _t1623 = parse_formula(parser)
    formula950 = _t1623
    consume_literal!(parser, ")")
    _t1624 = Proto.Abstraction(vars=vcat(bindings949[1], !isnothing(bindings949[2]) ? bindings949[2] : []), value=formula950)
    return (_t1624, length(bindings949[2]),)
end

function parse_break(parser::ParserState)::Proto.Break
    span_start954 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "break")
    _t1625 = parse_relation_id(parser)
    relation_id951 = _t1625
    _t1626 = parse_abstraction(parser)
    abstraction952 = _t1626
    if match_lookahead_literal(parser, "(", 0)
        _t1628 = parse_attrs(parser)
        _t1627 = _t1628
    else
        _t1627 = nothing
    end
    attrs953 = _t1627
    consume_literal!(parser, ")")
    _t1629 = Proto.Break(name=relation_id951, body=abstraction952, attrs=(!isnothing(attrs953) ? attrs953 : Proto.Attribute[]))
    result955 = _t1629
    record_span!(parser, span_start954, "Break")
    return result955
end

function parse_monoid_def(parser::ParserState)::Proto.MonoidDef
    span_start960 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monoid")
    _t1630 = parse_monoid(parser)
    monoid956 = _t1630
    _t1631 = parse_relation_id(parser)
    relation_id957 = _t1631
    _t1632 = parse_abstraction_with_arity(parser)
    abstraction_with_arity958 = _t1632
    if match_lookahead_literal(parser, "(", 0)
        _t1634 = parse_attrs(parser)
        _t1633 = _t1634
    else
        _t1633 = nothing
    end
    attrs959 = _t1633
    consume_literal!(parser, ")")
    _t1635 = Proto.MonoidDef(monoid=monoid956, name=relation_id957, body=abstraction_with_arity958[1], attrs=(!isnothing(attrs959) ? attrs959 : Proto.Attribute[]), value_arity=abstraction_with_arity958[2])
    result961 = _t1635
    record_span!(parser, span_start960, "MonoidDef")
    return result961
end

function parse_monoid(parser::ParserState)::Proto.Monoid
    span_start967 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "sum", 1)
            _t1637 = 3
        else
            if match_lookahead_literal(parser, "or", 1)
                _t1638 = 0
            else
                if match_lookahead_literal(parser, "min", 1)
                    _t1639 = 1
                else
                    if match_lookahead_literal(parser, "max", 1)
                        _t1640 = 2
                    else
                        _t1640 = -1
                    end
                    _t1639 = _t1640
                end
                _t1638 = _t1639
            end
            _t1637 = _t1638
        end
        _t1636 = _t1637
    else
        _t1636 = -1
    end
    prediction962 = _t1636
    if prediction962 == 3
        _t1642 = parse_sum_monoid(parser)
        sum_monoid966 = _t1642
        _t1643 = Proto.Monoid(value=OneOf(:sum_monoid, sum_monoid966))
        _t1641 = _t1643
    else
        if prediction962 == 2
            _t1645 = parse_max_monoid(parser)
            max_monoid965 = _t1645
            _t1646 = Proto.Monoid(value=OneOf(:max_monoid, max_monoid965))
            _t1644 = _t1646
        else
            if prediction962 == 1
                _t1648 = parse_min_monoid(parser)
                min_monoid964 = _t1648
                _t1649 = Proto.Monoid(value=OneOf(:min_monoid, min_monoid964))
                _t1647 = _t1649
            else
                if prediction962 == 0
                    _t1651 = parse_or_monoid(parser)
                    or_monoid963 = _t1651
                    _t1652 = Proto.Monoid(value=OneOf(:or_monoid, or_monoid963))
                    _t1650 = _t1652
                else
                    throw(ParseError("Unexpected token in monoid" * ": " * string(lookahead(parser, 0))))
                end
                _t1647 = _t1650
            end
            _t1644 = _t1647
        end
        _t1641 = _t1644
    end
    result968 = _t1641
    record_span!(parser, span_start967, "Monoid")
    return result968
end

function parse_or_monoid(parser::ParserState)::Proto.OrMonoid
    span_start969 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "or")
    consume_literal!(parser, ")")
    _t1653 = Proto.OrMonoid()
    result970 = _t1653
    record_span!(parser, span_start969, "OrMonoid")
    return result970
end

function parse_min_monoid(parser::ParserState)::Proto.MinMonoid
    span_start972 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "min")
    _t1654 = parse_type(parser)
    type971 = _t1654
    consume_literal!(parser, ")")
    _t1655 = Proto.MinMonoid(var"#type"=type971)
    result973 = _t1655
    record_span!(parser, span_start972, "MinMonoid")
    return result973
end

function parse_max_monoid(parser::ParserState)::Proto.MaxMonoid
    span_start975 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "max")
    _t1656 = parse_type(parser)
    type974 = _t1656
    consume_literal!(parser, ")")
    _t1657 = Proto.MaxMonoid(var"#type"=type974)
    result976 = _t1657
    record_span!(parser, span_start975, "MaxMonoid")
    return result976
end

function parse_sum_monoid(parser::ParserState)::Proto.SumMonoid
    span_start978 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "sum")
    _t1658 = parse_type(parser)
    type977 = _t1658
    consume_literal!(parser, ")")
    _t1659 = Proto.SumMonoid(var"#type"=type977)
    result979 = _t1659
    record_span!(parser, span_start978, "SumMonoid")
    return result979
end

function parse_monus_def(parser::ParserState)::Proto.MonusDef
    span_start984 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "monus")
    _t1660 = parse_monoid(parser)
    monoid980 = _t1660
    _t1661 = parse_relation_id(parser)
    relation_id981 = _t1661
    _t1662 = parse_abstraction_with_arity(parser)
    abstraction_with_arity982 = _t1662
    if match_lookahead_literal(parser, "(", 0)
        _t1664 = parse_attrs(parser)
        _t1663 = _t1664
    else
        _t1663 = nothing
    end
    attrs983 = _t1663
    consume_literal!(parser, ")")
    _t1665 = Proto.MonusDef(monoid=monoid980, name=relation_id981, body=abstraction_with_arity982[1], attrs=(!isnothing(attrs983) ? attrs983 : Proto.Attribute[]), value_arity=abstraction_with_arity982[2])
    result985 = _t1665
    record_span!(parser, span_start984, "MonusDef")
    return result985
end

function parse_constraint(parser::ParserState)::Proto.Constraint
    span_start990 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "functional_dependency")
    _t1666 = parse_relation_id(parser)
    relation_id986 = _t1666
    _t1667 = parse_abstraction(parser)
    abstraction987 = _t1667
    _t1668 = parse_functional_dependency_keys(parser)
    functional_dependency_keys988 = _t1668
    _t1669 = parse_functional_dependency_values(parser)
    functional_dependency_values989 = _t1669
    consume_literal!(parser, ")")
    _t1670 = Proto.FunctionalDependency(guard=abstraction987, keys=functional_dependency_keys988, values=functional_dependency_values989)
    _t1671 = Proto.Constraint(constraint_type=OneOf(:functional_dependency, _t1670), name=relation_id986)
    result991 = _t1671
    record_span!(parser, span_start990, "Constraint")
    return result991
end

function parse_functional_dependency_keys(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "keys")
    xs992 = Proto.Var[]
    cond993 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond993
        _t1672 = parse_var(parser)
        item994 = _t1672
        push!(xs992, item994)
        cond993 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars995 = xs992
    consume_literal!(parser, ")")
    return vars995
end

function parse_functional_dependency_values(parser::ParserState)::Vector{Proto.Var}
    consume_literal!(parser, "(")
    consume_literal!(parser, "values")
    xs996 = Proto.Var[]
    cond997 = match_lookahead_terminal(parser, "SYMBOL", 0)
    while cond997
        _t1673 = parse_var(parser)
        item998 = _t1673
        push!(xs996, item998)
        cond997 = match_lookahead_terminal(parser, "SYMBOL", 0)
    end
    vars999 = xs996
    consume_literal!(parser, ")")
    return vars999
end

function parse_data(parser::ParserState)::Proto.Data
    span_start1004 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "edb", 1)
            _t1675 = 0
        else
            if match_lookahead_literal(parser, "csv_data", 1)
                _t1676 = 2
            else
                if match_lookahead_literal(parser, "betree_relation", 1)
                    _t1677 = 1
                else
                    _t1677 = -1
                end
                _t1676 = _t1677
            end
            _t1675 = _t1676
        end
        _t1674 = _t1675
    else
        _t1674 = -1
    end
    prediction1000 = _t1674
    if prediction1000 == 2
        _t1679 = parse_csv_data(parser)
        csv_data1003 = _t1679
        _t1680 = Proto.Data(data_type=OneOf(:csv_data, csv_data1003))
        _t1678 = _t1680
    else
        if prediction1000 == 1
            _t1682 = parse_betree_relation(parser)
            betree_relation1002 = _t1682
            _t1683 = Proto.Data(data_type=OneOf(:betree_relation, betree_relation1002))
            _t1681 = _t1683
        else
            if prediction1000 == 0
                _t1685 = parse_edb(parser)
                edb1001 = _t1685
                _t1686 = Proto.Data(data_type=OneOf(:edb, edb1001))
                _t1684 = _t1686
            else
                throw(ParseError("Unexpected token in data" * ": " * string(lookahead(parser, 0))))
            end
            _t1681 = _t1684
        end
        _t1678 = _t1681
    end
    result1005 = _t1678
    record_span!(parser, span_start1004, "Data")
    return result1005
end

function parse_edb(parser::ParserState)::Proto.EDB
    span_start1009 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "edb")
    _t1687 = parse_relation_id(parser)
    relation_id1006 = _t1687
    _t1688 = parse_edb_path(parser)
    edb_path1007 = _t1688
    _t1689 = parse_edb_types(parser)
    edb_types1008 = _t1689
    consume_literal!(parser, ")")
    _t1690 = Proto.EDB(target_id=relation_id1006, path=edb_path1007, types=edb_types1008)
    result1010 = _t1690
    record_span!(parser, span_start1009, "EDB")
    return result1010
end

function parse_edb_path(parser::ParserState)::Vector{String}
    consume_literal!(parser, "[")
    xs1011 = String[]
    cond1012 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1012
        item1013 = consume_terminal!(parser, "STRING")
        push!(xs1011, item1013)
        cond1012 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1014 = xs1011
    consume_literal!(parser, "]")
    return strings1014
end

function parse_edb_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "[")
    xs1015 = Proto.var"#Type"[]
    cond1016 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1016
        _t1691 = parse_type(parser)
        item1017 = _t1691
        push!(xs1015, item1017)
        cond1016 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1018 = xs1015
    consume_literal!(parser, "]")
    return types1018
end

function parse_betree_relation(parser::ParserState)::Proto.BeTreeRelation
    span_start1021 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_relation")
    _t1692 = parse_relation_id(parser)
    relation_id1019 = _t1692
    _t1693 = parse_betree_info(parser)
    betree_info1020 = _t1693
    consume_literal!(parser, ")")
    _t1694 = Proto.BeTreeRelation(name=relation_id1019, relation_info=betree_info1020)
    result1022 = _t1694
    record_span!(parser, span_start1021, "BeTreeRelation")
    return result1022
end

function parse_betree_info(parser::ParserState)::Proto.BeTreeInfo
    span_start1026 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "betree_info")
    _t1695 = parse_betree_info_key_types(parser)
    betree_info_key_types1023 = _t1695
    _t1696 = parse_betree_info_value_types(parser)
    betree_info_value_types1024 = _t1696
    _t1697 = parse_config_dict(parser)
    config_dict1025 = _t1697
    consume_literal!(parser, ")")
    _t1698 = construct_betree_info(parser, betree_info_key_types1023, betree_info_value_types1024, config_dict1025)
    result1027 = _t1698
    record_span!(parser, span_start1026, "BeTreeInfo")
    return result1027
end

function parse_betree_info_key_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "key_types")
    xs1028 = Proto.var"#Type"[]
    cond1029 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1029
        _t1699 = parse_type(parser)
        item1030 = _t1699
        push!(xs1028, item1030)
        cond1029 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1031 = xs1028
    consume_literal!(parser, ")")
    return types1031
end

function parse_betree_info_value_types(parser::ParserState)::Vector{Proto.var"#Type"}
    consume_literal!(parser, "(")
    consume_literal!(parser, "value_types")
    xs1032 = Proto.var"#Type"[]
    cond1033 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1033
        _t1700 = parse_type(parser)
        item1034 = _t1700
        push!(xs1032, item1034)
        cond1033 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1035 = xs1032
    consume_literal!(parser, ")")
    return types1035
end

function parse_csv_data(parser::ParserState)::Proto.CSVData
    span_start1040 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_data")
    _t1701 = parse_csvlocator(parser)
    csvlocator1036 = _t1701
    _t1702 = parse_csv_config(parser)
    csv_config1037 = _t1702
    _t1703 = parse_gnf_columns(parser)
    gnf_columns1038 = _t1703
    _t1704 = parse_csv_asof(parser)
    csv_asof1039 = _t1704
    consume_literal!(parser, ")")
    _t1705 = Proto.CSVData(locator=csvlocator1036, config=csv_config1037, columns=gnf_columns1038, asof=csv_asof1039)
    result1041 = _t1705
    record_span!(parser, span_start1040, "CSVData")
    return result1041
end

function parse_csvlocator(parser::ParserState)::Proto.CSVLocator
    span_start1044 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_locator")
    if (match_lookahead_literal(parser, "(", 0) && match_lookahead_literal(parser, "paths", 1))
        _t1707 = parse_csv_locator_paths(parser)
        _t1706 = _t1707
    else
        _t1706 = nothing
    end
    csv_locator_paths1042 = _t1706
    if match_lookahead_literal(parser, "(", 0)
        _t1709 = parse_csv_locator_inline_data(parser)
        _t1708 = _t1709
    else
        _t1708 = nothing
    end
    csv_locator_inline_data1043 = _t1708
    consume_literal!(parser, ")")
    _t1710 = Proto.CSVLocator(paths=(!isnothing(csv_locator_paths1042) ? csv_locator_paths1042 : String[]), inline_data=Vector{UInt8}((!isnothing(csv_locator_inline_data1043) ? csv_locator_inline_data1043 : "")))
    result1045 = _t1710
    record_span!(parser, span_start1044, "CSVLocator")
    return result1045
end

function parse_csv_locator_paths(parser::ParserState)::Vector{String}
    consume_literal!(parser, "(")
    consume_literal!(parser, "paths")
    xs1046 = String[]
    cond1047 = match_lookahead_terminal(parser, "STRING", 0)
    while cond1047
        item1048 = consume_terminal!(parser, "STRING")
        push!(xs1046, item1048)
        cond1047 = match_lookahead_terminal(parser, "STRING", 0)
    end
    strings1049 = xs1046
    consume_literal!(parser, ")")
    return strings1049
end

function parse_csv_locator_inline_data(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "inline_data")
    string1050 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1050
end

function parse_csv_config(parser::ParserState)::Proto.CSVConfig
    span_start1052 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "csv_config")
    _t1711 = parse_config_dict(parser)
    config_dict1051 = _t1711
    consume_literal!(parser, ")")
    _t1712 = construct_csv_config(parser, config_dict1051)
    result1053 = _t1712
    record_span!(parser, span_start1052, "CSVConfig")
    return result1053
end

function parse_gnf_columns(parser::ParserState)::Vector{Proto.GNFColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1054 = Proto.GNFColumn[]
    cond1055 = match_lookahead_literal(parser, "(", 0)
    while cond1055
        _t1713 = parse_gnf_column(parser)
        item1056 = _t1713
        push!(xs1054, item1056)
        cond1055 = match_lookahead_literal(parser, "(", 0)
    end
    gnf_columns1057 = xs1054
    consume_literal!(parser, ")")
    return gnf_columns1057
end

function parse_gnf_column(parser::ParserState)::Proto.GNFColumn
    span_start1064 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    _t1714 = parse_gnf_column_path(parser)
    gnf_column_path1058 = _t1714
    if (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
        _t1716 = parse_relation_id(parser)
        _t1715 = _t1716
    else
        _t1715 = nothing
    end
    relation_id1059 = _t1715
    consume_literal!(parser, "[")
    xs1060 = Proto.var"#Type"[]
    cond1061 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    while cond1061
        _t1717 = parse_type(parser)
        item1062 = _t1717
        push!(xs1060, item1062)
        cond1061 = ((((((((((((match_lookahead_literal(parser, "(", 0) || match_lookahead_literal(parser, "BOOLEAN", 0)) || match_lookahead_literal(parser, "DATE", 0)) || match_lookahead_literal(parser, "DATETIME", 0)) || match_lookahead_literal(parser, "FLOAT", 0)) || match_lookahead_literal(parser, "FLOAT32", 0)) || match_lookahead_literal(parser, "INT", 0)) || match_lookahead_literal(parser, "INT128", 0)) || match_lookahead_literal(parser, "INT32", 0)) || match_lookahead_literal(parser, "MISSING", 0)) || match_lookahead_literal(parser, "STRING", 0)) || match_lookahead_literal(parser, "UINT128", 0)) || match_lookahead_literal(parser, "UNKNOWN", 0))
    end
    types1063 = xs1060
    consume_literal!(parser, "]")
    consume_literal!(parser, ")")
    _t1718 = Proto.GNFColumn(column_path=gnf_column_path1058, target_id=relation_id1059, types=types1063)
    result1065 = _t1718
    record_span!(parser, span_start1064, "GNFColumn")
    return result1065
end

function parse_gnf_column_path(parser::ParserState)::Vector{String}
    if match_lookahead_literal(parser, "[", 0)
        _t1719 = 1
    else
        if match_lookahead_terminal(parser, "STRING", 0)
            _t1720 = 0
        else
            _t1720 = -1
        end
        _t1719 = _t1720
    end
    prediction1066 = _t1719
    if prediction1066 == 1
        consume_literal!(parser, "[")
        xs1068 = String[]
        cond1069 = match_lookahead_terminal(parser, "STRING", 0)
        while cond1069
            item1070 = consume_terminal!(parser, "STRING")
            push!(xs1068, item1070)
            cond1069 = match_lookahead_terminal(parser, "STRING", 0)
        end
        strings1071 = xs1068
        consume_literal!(parser, "]")
        _t1721 = strings1071
    else
        if prediction1066 == 0
            string1067 = consume_terminal!(parser, "STRING")
            _t1722 = String[string1067]
        else
            throw(ParseError("Unexpected token in gnf_column_path" * ": " * string(lookahead(parser, 0))))
        end
        _t1721 = _t1722
    end
    return _t1721
end

function parse_csv_asof(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "asof")
    string1072 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1072
end

function parse_undefine(parser::ParserState)::Proto.Undefine
    span_start1074 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "undefine")
    _t1723 = parse_fragment_id(parser)
    fragment_id1073 = _t1723
    consume_literal!(parser, ")")
    _t1724 = Proto.Undefine(fragment_id=fragment_id1073)
    result1075 = _t1724
    record_span!(parser, span_start1074, "Undefine")
    return result1075
end

function parse_context(parser::ParserState)::Proto.Context
    span_start1080 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "context")
    xs1076 = Proto.RelationId[]
    cond1077 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    while cond1077
        _t1725 = parse_relation_id(parser)
        item1078 = _t1725
        push!(xs1076, item1078)
        cond1077 = (match_lookahead_literal(parser, ":", 0) || match_lookahead_terminal(parser, "UINT128", 0))
    end
    relation_ids1079 = xs1076
    consume_literal!(parser, ")")
    _t1726 = Proto.Context(relations=relation_ids1079)
    result1081 = _t1726
    record_span!(parser, span_start1080, "Context")
    return result1081
end

function parse_snapshot(parser::ParserState)::Proto.Snapshot
    span_start1086 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "snapshot")
    xs1082 = Proto.SnapshotMapping[]
    cond1083 = match_lookahead_literal(parser, "[", 0)
    while cond1083
        _t1727 = parse_snapshot_mapping(parser)
        item1084 = _t1727
        push!(xs1082, item1084)
        cond1083 = match_lookahead_literal(parser, "[", 0)
    end
    snapshot_mappings1085 = xs1082
    consume_literal!(parser, ")")
    _t1728 = Proto.Snapshot(mappings=snapshot_mappings1085)
    result1087 = _t1728
    record_span!(parser, span_start1086, "Snapshot")
    return result1087
end

function parse_snapshot_mapping(parser::ParserState)::Proto.SnapshotMapping
    span_start1090 = span_start(parser)
    _t1729 = parse_edb_path(parser)
    edb_path1088 = _t1729
    _t1730 = parse_relation_id(parser)
    relation_id1089 = _t1730
    _t1731 = Proto.SnapshotMapping(destination_path=edb_path1088, source_relation=relation_id1089)
    result1091 = _t1731
    record_span!(parser, span_start1090, "SnapshotMapping")
    return result1091
end

function parse_epoch_reads(parser::ParserState)::Vector{Proto.Read}
    consume_literal!(parser, "(")
    consume_literal!(parser, "reads")
    xs1092 = Proto.Read[]
    cond1093 = match_lookahead_literal(parser, "(", 0)
    while cond1093
        _t1732 = parse_read(parser)
        item1094 = _t1732
        push!(xs1092, item1094)
        cond1093 = match_lookahead_literal(parser, "(", 0)
    end
    reads1095 = xs1092
    consume_literal!(parser, ")")
    return reads1095
end

function parse_read(parser::ParserState)::Proto.Read
    span_start1102 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "what_if", 1)
            _t1734 = 2
        else
            if match_lookahead_literal(parser, "output", 1)
                _t1735 = 1
            else
                if match_lookahead_literal(parser, "export", 1)
                    _t1736 = 4
                else
                    if match_lookahead_literal(parser, "demand", 1)
                        _t1737 = 0
                    else
                        if match_lookahead_literal(parser, "abort", 1)
                            _t1738 = 3
                        else
                            _t1738 = -1
                        end
                        _t1737 = _t1738
                    end
                    _t1736 = _t1737
                end
                _t1735 = _t1736
            end
            _t1734 = _t1735
        end
        _t1733 = _t1734
    else
        _t1733 = -1
    end
    prediction1096 = _t1733
    if prediction1096 == 4
        _t1740 = parse_export(parser)
        export1101 = _t1740
        _t1741 = Proto.Read(read_type=OneOf(:var"#export", export1101))
        _t1739 = _t1741
    else
        if prediction1096 == 3
            _t1743 = parse_abort(parser)
            abort1100 = _t1743
            _t1744 = Proto.Read(read_type=OneOf(:abort, abort1100))
            _t1742 = _t1744
        else
            if prediction1096 == 2
                _t1746 = parse_what_if(parser)
                what_if1099 = _t1746
                _t1747 = Proto.Read(read_type=OneOf(:what_if, what_if1099))
                _t1745 = _t1747
            else
                if prediction1096 == 1
                    _t1749 = parse_output(parser)
                    output1098 = _t1749
                    _t1750 = Proto.Read(read_type=OneOf(:output, output1098))
                    _t1748 = _t1750
                else
                    if prediction1096 == 0
                        _t1752 = parse_demand(parser)
                        demand1097 = _t1752
                        _t1753 = Proto.Read(read_type=OneOf(:demand, demand1097))
                        _t1751 = _t1753
                    else
                        throw(ParseError("Unexpected token in read" * ": " * string(lookahead(parser, 0))))
                    end
                    _t1748 = _t1751
                end
                _t1745 = _t1748
            end
            _t1742 = _t1745
        end
        _t1739 = _t1742
    end
    result1103 = _t1739
    record_span!(parser, span_start1102, "Read")
    return result1103
end

function parse_demand(parser::ParserState)::Proto.Demand
    span_start1105 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "demand")
    _t1754 = parse_relation_id(parser)
    relation_id1104 = _t1754
    consume_literal!(parser, ")")
    _t1755 = Proto.Demand(relation_id=relation_id1104)
    result1106 = _t1755
    record_span!(parser, span_start1105, "Demand")
    return result1106
end

function parse_output(parser::ParserState)::Proto.Output
    span_start1109 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "output")
    _t1756 = parse_name(parser)
    name1107 = _t1756
    _t1757 = parse_relation_id(parser)
    relation_id1108 = _t1757
    consume_literal!(parser, ")")
    _t1758 = Proto.Output(name=name1107, relation_id=relation_id1108)
    result1110 = _t1758
    record_span!(parser, span_start1109, "Output")
    return result1110
end

function parse_what_if(parser::ParserState)::Proto.WhatIf
    span_start1113 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "what_if")
    _t1759 = parse_name(parser)
    name1111 = _t1759
    _t1760 = parse_epoch(parser)
    epoch1112 = _t1760
    consume_literal!(parser, ")")
    _t1761 = Proto.WhatIf(branch=name1111, epoch=epoch1112)
    result1114 = _t1761
    record_span!(parser, span_start1113, "WhatIf")
    return result1114
end

function parse_abort(parser::ParserState)::Proto.Abort
    span_start1117 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "abort")
    if (match_lookahead_literal(parser, ":", 0) && match_lookahead_terminal(parser, "SYMBOL", 1))
        _t1763 = parse_name(parser)
        _t1762 = _t1763
    else
        _t1762 = nothing
    end
    name1115 = _t1762
    _t1764 = parse_relation_id(parser)
    relation_id1116 = _t1764
    consume_literal!(parser, ")")
    _t1765 = Proto.Abort(name=(!isnothing(name1115) ? name1115 : "abort"), relation_id=relation_id1116)
    result1118 = _t1765
    record_span!(parser, span_start1117, "Abort")
    return result1118
end

function parse_export(parser::ParserState)::Proto.Export
    span_start1120 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "export")
    _t1766 = parse_export_csv_config(parser)
    export_csv_config1119 = _t1766
    consume_literal!(parser, ")")
    _t1767 = Proto.Export(export_config=OneOf(:csv_config, export_csv_config1119))
    result1121 = _t1767
    record_span!(parser, span_start1120, "Export")
    return result1121
end

function parse_export_csv_config(parser::ParserState)::Proto.ExportCSVConfig
    span_start1129 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "export_csv_config_v2", 1)
            _t1769 = 0
        else
            if match_lookahead_literal(parser, "export_csv_config", 1)
                _t1770 = 1
            else
                _t1770 = -1
            end
            _t1769 = _t1770
        end
        _t1768 = _t1769
    else
        _t1768 = -1
    end
    prediction1122 = _t1768
    if prediction1122 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "export_csv_config")
        _t1772 = parse_export_csv_path(parser)
        export_csv_path1126 = _t1772
        _t1773 = parse_export_csv_columns_list(parser)
        export_csv_columns_list1127 = _t1773
        _t1774 = parse_config_dict(parser)
        config_dict1128 = _t1774
        consume_literal!(parser, ")")
        _t1775 = construct_export_csv_config(parser, export_csv_path1126, export_csv_columns_list1127, config_dict1128)
        _t1771 = _t1775
    else
        if prediction1122 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "export_csv_config_v2")
            _t1777 = parse_export_csv_path(parser)
            export_csv_path1123 = _t1777
            _t1778 = parse_export_csv_source(parser)
            export_csv_source1124 = _t1778
            _t1779 = parse_csv_config(parser)
            csv_config1125 = _t1779
            consume_literal!(parser, ")")
            _t1780 = construct_export_csv_config_with_source(parser, export_csv_path1123, export_csv_source1124, csv_config1125)
            _t1776 = _t1780
        else
            throw(ParseError("Unexpected token in export_csv_config" * ": " * string(lookahead(parser, 0))))
        end
        _t1771 = _t1776
    end
    result1130 = _t1771
    record_span!(parser, span_start1129, "ExportCSVConfig")
    return result1130
end

function parse_export_csv_path(parser::ParserState)::String
    consume_literal!(parser, "(")
    consume_literal!(parser, "path")
    string1131 = consume_terminal!(parser, "STRING")
    consume_literal!(parser, ")")
    return string1131
end

function parse_export_csv_source(parser::ParserState)::Proto.ExportCSVSource
    span_start1138 = span_start(parser)
    if match_lookahead_literal(parser, "(", 0)
        if match_lookahead_literal(parser, "table_def", 1)
            _t1782 = 1
        else
            if match_lookahead_literal(parser, "gnf_columns", 1)
                _t1783 = 0
            else
                _t1783 = -1
            end
            _t1782 = _t1783
        end
        _t1781 = _t1782
    else
        _t1781 = -1
    end
    prediction1132 = _t1781
    if prediction1132 == 1
        consume_literal!(parser, "(")
        consume_literal!(parser, "table_def")
        _t1785 = parse_relation_id(parser)
        relation_id1137 = _t1785
        consume_literal!(parser, ")")
        _t1786 = Proto.ExportCSVSource(csv_source=OneOf(:table_def, relation_id1137))
        _t1784 = _t1786
    else
        if prediction1132 == 0
            consume_literal!(parser, "(")
            consume_literal!(parser, "gnf_columns")
            xs1133 = Proto.ExportCSVColumn[]
            cond1134 = match_lookahead_literal(parser, "(", 0)
            while cond1134
                _t1788 = parse_export_csv_column(parser)
                item1135 = _t1788
                push!(xs1133, item1135)
                cond1134 = match_lookahead_literal(parser, "(", 0)
            end
            export_csv_columns1136 = xs1133
            consume_literal!(parser, ")")
            _t1789 = Proto.ExportCSVColumns(columns=export_csv_columns1136)
            _t1790 = Proto.ExportCSVSource(csv_source=OneOf(:gnf_columns, _t1789))
            _t1787 = _t1790
        else
            throw(ParseError("Unexpected token in export_csv_source" * ": " * string(lookahead(parser, 0))))
        end
        _t1784 = _t1787
    end
    result1139 = _t1784
    record_span!(parser, span_start1138, "ExportCSVSource")
    return result1139
end

function parse_export_csv_column(parser::ParserState)::Proto.ExportCSVColumn
    span_start1142 = span_start(parser)
    consume_literal!(parser, "(")
    consume_literal!(parser, "column")
    string1140 = consume_terminal!(parser, "STRING")
    _t1791 = parse_relation_id(parser)
    relation_id1141 = _t1791
    consume_literal!(parser, ")")
    _t1792 = Proto.ExportCSVColumn(column_name=string1140, column_data=relation_id1141)
    result1143 = _t1792
    record_span!(parser, span_start1142, "ExportCSVColumn")
    return result1143
end

function parse_export_csv_columns_list(parser::ParserState)::Vector{Proto.ExportCSVColumn}
    consume_literal!(parser, "(")
    consume_literal!(parser, "columns")
    xs1144 = Proto.ExportCSVColumn[]
    cond1145 = match_lookahead_literal(parser, "(", 0)
    while cond1145
        _t1793 = parse_export_csv_column(parser)
        item1146 = _t1793
        push!(xs1144, item1146)
        cond1145 = match_lookahead_literal(parser, "(", 0)
    end
    export_csv_columns1147 = xs1144
    consume_literal!(parser, ")")
    return export_csv_columns1147
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
export scan_string, scan_int, scan_int32, scan_float, scan_float32, scan_int128, scan_uint128, scan_decimal
# Export Lexer and provenance types for testing
export Lexer, Location, Span

end # module Parser
