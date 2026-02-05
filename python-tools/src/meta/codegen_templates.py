"""Builtin templates for code generation.

This module defines templates for generating code from builtin function calls.
Templates use placeholders like {0}, {1} for arguments and {args} for variadic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BuiltinTemplate:
    """Template for a builtin function.

    value_template: Template for the value expression (e.g., "!{0}"), or None for non-returning builtins.
    statement_templates: Templates for statements to execute (may be empty)
    """
    value_template: Optional[str]
    statement_templates: List[str] = field(default_factory=list)


# Python builtin templates
PYTHON_TEMPLATES: Dict[str, BuiltinTemplate] = {
    "some": BuiltinTemplate("{0}"),
    "not": BuiltinTemplate("not {0}"),
    "and": BuiltinTemplate("({0} and {1})"),
    "or": BuiltinTemplate("({0} or {1})"),
    "equal": BuiltinTemplate("{0} == {1}"),
    "not_equal": BuiltinTemplate("{0} != {1}"),
    "add": BuiltinTemplate("({0} + {1})"),
    "is_none": BuiltinTemplate("{0} is None"),
    "is_some": BuiltinTemplate("{0} is not None"),
    "unwrap_option": BuiltinTemplate("{0}"),
    "none": BuiltinTemplate("None"),
    "make_empty_bytes": BuiltinTemplate("b''"),
    "dict_from_list": BuiltinTemplate("dict({0})"),
    "dict_get": BuiltinTemplate("{0}.get({1})"),
    "has_proto_field": BuiltinTemplate("{0}.HasField({1})"),
    "string_to_upper": BuiltinTemplate("{0}.upper()"),
    "string_in_list": BuiltinTemplate("{0} in {1}"),
    "string_concat": BuiltinTemplate("({0} + {1})"),
    "encode_string": BuiltinTemplate("{0}.encode()"),
    "tuple": BuiltinTemplate("({args},)"),
    "length": BuiltinTemplate("len({0})"),
    "unwrap_option_or": BuiltinTemplate("({0} if {0} is not None else {1})"),
    "int64_to_int32": BuiltinTemplate("int({0})"),
    "map": BuiltinTemplate("[{0}(x) for x in {1}]"),
    "list_concat": BuiltinTemplate("({0} + ({1} if {1} is not None else []))"),
    "fragment_id_from_string": BuiltinTemplate("fragments_pb2.FragmentId(id={0}.encode())"),
    "relation_id_from_string": BuiltinTemplate("self.relation_id_from_string({0})"),
    "relation_id_from_int": BuiltinTemplate(
        "logic_pb2.RelationId(id_low={0} & 0xFFFFFFFFFFFFFFFF, id_high=({0} >> 64) & 0xFFFFFFFFFFFFFFFF)"
    ),
    "match_lookahead_terminal": BuiltinTemplate("self.match_lookahead_terminal({0}, {1})"),
    "match_lookahead_literal": BuiltinTemplate("self.match_lookahead_literal({0}, {1})"),
    "consume_literal": BuiltinTemplate("None", ["self.consume_literal({0})"]),
    "consume_terminal": BuiltinTemplate("self.consume_terminal({0})"),
    "current_token": BuiltinTemplate("self.lookahead(0)"),
    "start_fragment": BuiltinTemplate("{0}", ["self.start_fragment({0})"]),
    "construct_fragment": BuiltinTemplate("self.construct_fragment({0}, {1})"),
    "error": BuiltinTemplate(None, ["raise ParseError({0})"]),
    "error_with_token": BuiltinTemplate(
        None, ['raise ParseError(f"{{{0}}}: {{{1}.type}}=`{{{1}.value}}`")']
    ),
}


# Julia builtin templates
JULIA_TEMPLATES: Dict[str, BuiltinTemplate] = {
    "some": BuiltinTemplate("{0}"),
    "not": BuiltinTemplate("!{0}"),
    "and": BuiltinTemplate("({0} && {1})"),
    "or": BuiltinTemplate("({0} || {1})"),
    "equal": BuiltinTemplate("{0} == {1}"),
    "not_equal": BuiltinTemplate("{0} != {1}"),
    "add": BuiltinTemplate("({0} + {1})"),
    "is_none": BuiltinTemplate("isnothing({0})"),
    "is_some": BuiltinTemplate("!isnothing({0})"),
    "unwrap_option": BuiltinTemplate("{0}"),
    "none": BuiltinTemplate("nothing"),
    "make_empty_bytes": BuiltinTemplate("UInt8[]"),
    "dict_from_list": BuiltinTemplate("Dict({0})"),
    "dict_get": BuiltinTemplate("get({0}, {1}, nothing)"),
    "has_proto_field": BuiltinTemplate(
        "hasproperty({0}, Symbol({1})) && !isnothing(getproperty({0}, Symbol({1})))"
    ),
    "string_to_upper": BuiltinTemplate("uppercase({0})"),
    "string_in_list": BuiltinTemplate("({0} in {1})"),
    "string_concat": BuiltinTemplate("({0} * {1})"),
    "encode_string": BuiltinTemplate("Vector{{UInt8}}({0})"),
    "tuple": BuiltinTemplate("({args},)"),
    "length": BuiltinTemplate("length({0})"),
    "unwrap_option_or": BuiltinTemplate("(!isnothing({0}) ? {0} : {1})"),
    "int64_to_int32": BuiltinTemplate("Int32({0})"),
    "map": BuiltinTemplate("map({0}, {1})"),
    "list_concat": BuiltinTemplate("vcat({0}, !isnothing({1}) ? {1} : [])"),
    "fragment_id_from_string": BuiltinTemplate("Proto.FragmentId(; id=Vector{{UInt8}}({0}))"),
    "relation_id_from_string": BuiltinTemplate("relation_id_from_string(parser, {0})"),
    "relation_id_from_int": BuiltinTemplate(
        "Proto.RelationId(; id_low={0} & 0xFFFFFFFFFFFFFFFF, id_high=({0} >> 64) & 0xFFFFFFFFFFFFFFFF)"
    ),
    "match_lookahead_terminal": BuiltinTemplate("match_lookahead_terminal(parser, {0}, {1})"),
    "match_lookahead_literal": BuiltinTemplate("match_lookahead_literal(parser, {0}, {1})"),
    "consume_literal": BuiltinTemplate("nothing", ["consume_literal!(parser, {0})"]),
    "consume_terminal": BuiltinTemplate("consume_terminal!(parser, {0})"),
    "current_token": BuiltinTemplate("current_token(parser)"),
    "start_fragment": BuiltinTemplate("{0}", ["start_fragment(parser, {0})"]),
    "construct_fragment": BuiltinTemplate("construct_fragment(parser, {0}, {1})"),
    "error": BuiltinTemplate(None, ["throw(ParseError({0}))"]),
    "error_with_token": BuiltinTemplate(None, ['throw(ParseError({0} * ": " * string({1})))']),
}


__all__ = [
    'BuiltinTemplate',
    'PYTHON_TEMPLATES',
    'JULIA_TEMPLATES',
]
