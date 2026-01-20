"""Julia-specific parser code generation.

This module generates LL(k) recursive-descent parsers in Julia from grammars.
Handles Julia-specific code generation including:
- Prologue (imports, Token, Lexer, Parser struct with helpers)
- Parse method generation
- Epilogue (parse function)
"""

import re
from typing import List, Optional, Set

from .grammar import Grammar, Nonterminal
from .grammar_utils import get_literals
from .codegen_julia import JuliaCodeGenerator
from .parser_gen import generate_parse_functions


# Template for the generated parser prologue
PROLOGUE_TEMPLATE = r'''"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.

{command_line_comment}"""

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
    tokens::Vector{{Token}}

    function Lexer(input::String)
        lexer = new(input, 1, Token[])
        tokenize!(lexer)
        return lexer
    end
end


function tokenize!(lexer::Lexer)
    token_specs = [
{token_specs}    ]

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
        candidates = Tuple{{String,String,Function,Int}}[]

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
    tokens::Vector{{Token}}
    pos::Int
    id_to_debuginfo::Dict{{Vector{{UInt8}},Dict{{Tuple{{UInt64,UInt64}},String}}}}
    _current_fragment_id::Union{{Nothing,Vector{{UInt8}}}}
    _relation_id_to_name::Dict{{Tuple{{UInt64,UInt64}},String}}

    function Parser(tokens::Vector{{Token}})
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


function extract_value(val::Union{{Nothing,Proto.Value}}, value_type::String, default::Any)
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
            return Vector{{UInt8}}(val.string_value)
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
    config_list::Vector{{Tuple{{String,Any}}}},
    schema::Vector{{Tuple{{String,String,String,Any}}}},
    message_constructor::Function
)
    config = Dict(config_list)
    kwargs = Dict{{Symbol,Any}}()
    for (config_key, proto_field, value_type, default) in schema
        val = get(config, config_key, nothing)
        kwargs[Symbol(proto_field)] = extract_value(val, value_type, default)
    end
    return message_constructor(; kwargs...)
end


function construct_configure(parser::Parser, config_dict::Vector{{Tuple{{String,Proto.Value}}}})
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
    columns::Vector{{Any}},
    config_dict::Vector{{Tuple{{String,Proto.Value}}}}
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
    key_types::Vector{{Any}},
    value_types::Vector{{Any}},
    config_dict::Vector{{Tuple{{String,Any}}}}
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


function construct_csv_config(parser::Parser, config_dict::Vector{{Tuple{{String,Any}}}})
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
    declarations::Vector{{Proto.Declaration}}
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

'''


EPILOGUE_TEMPLATE = r'''

function parse(input::String)
    lexer = Lexer(input)
    parser = Parser(lexer.tokens)
    result = parse_{start_name}(parser)
    # Check for unconsumed tokens (except EOF)
    if parser.pos <= length(parser.tokens)
        remaining_token = lookahead(parser, 0)
        if remaining_token.type != "\$"
            throw(ParseError("Unexpected token at end of input: $remaining_token"))
        end
    end
    return result
end
'''


def generate_parser_julia(grammar: Grammar, reachable: Optional[Set[Nonterminal]] = None, command_line: Optional[str] = None, proto_messages=None) -> str:
    """Generate LL(k) recursive-descent parser in Julia."""
    # Generate prologue (lexer, token, error, helper structs and functions)
    prologue = _generate_prologue(grammar, command_line)

    # Create code generator with proto message info
    codegen = JuliaCodeGenerator(proto_messages=proto_messages)

    # Generate parser methods as strings
    defns = generate_parse_functions(grammar)
    lines = []
    for defn in defns:
        lines.append("")
        lines.append(codegen.generate_def(defn, ""))
    lines.append("")

    # Generate epilogue (parse function)
    epilogue = _generate_epilogue(grammar.start)

    return prologue + "\n".join(lines) + epilogue


def _generate_prologue(grammar: Grammar, command_line: Optional[str] = None) -> str:
    """Generate parser prologue with imports, token struct, lexer, and parser struct."""
    # Build command line comment
    command_line_comment = f"\nCommand: {command_line}\n" if command_line else ""

    # Collect literals (sorted by length, longest first)
    literals = set()
    for rules_list in grammar.rules.values():
        for rule in rules_list:
            literals.update(get_literals(rule.rhs))
    sorted_literals = sorted(literals, key=lambda x: (-len(x.name), x.name))

    # Build token specs with literals first, then other tokens
    token_specs_lines = []

    # Add literals to token_specs
    # Only add non-alphanumeric literals (punctuation) as LITERAL tokens.
    # Alphanumeric keywords become "soft keywords" - they're lexed as SYMBOL
    # and matched by value in match_lookahead_literal.
    for lit in sorted_literals:
        # Skip alphanumeric literals - they'll be lexed as SYMBOL tokens
        if lit.name[0].isalnum():
            continue
        # Escape regex special characters in literal
        escaped = re.escape(lit.name)
        token_specs_lines.append(
            f'        ("LITERAL", r"{escaped}", identity),'
        )

    # Add other tokens
    for token in grammar.tokens:
        # Escape double quotes in the pattern for Julia raw strings
        escaped_pattern = token.pattern.replace('"', '\\"')
        token_specs_lines.append(
            f'        ("{token.name}", r"{escaped_pattern}", scan_{token.name.lower()}),'
        )

    token_specs = "\n".join(token_specs_lines) + "\n" if token_specs_lines else ""

    return PROLOGUE_TEMPLATE.format(
        command_line_comment=command_line_comment,
        token_specs=token_specs,
    )


def _generate_epilogue(start: Nonterminal) -> str:
    """Generate parse function."""
    return EPILOGUE_TEMPLATE.format(start_name=start.name.lower())


__all__ = [
    'generate_parser_julia',
]
