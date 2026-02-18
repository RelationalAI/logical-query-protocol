"""Builtin templates for code generation.

This module defines templates for generating code from builtin function calls.
Templates use placeholders like {0}, {1} for arguments and {args} for variadic.
"""

from dataclasses import dataclass, field


@dataclass
class BuiltinTemplate:
    """Template for a builtin function.

    value_template: Template for the value expression (e.g., "!{0}"), or None for non-returning builtins.
    statement_templates: Templates for statements to execute (may be empty)
    """

    value_template: str | None
    statement_templates: list[str] = field(default_factory=list)


# Python builtin templates
PYTHON_TEMPLATES: dict[str, BuiltinTemplate] = {
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
    "subtract": BuiltinTemplate("({0} - {1})"),
    "string_concat": BuiltinTemplate("({0} + {1})"),
    "encode_string": BuiltinTemplate("{0}.encode()"),
    "tuple": BuiltinTemplate("({args},)"),
    "length": BuiltinTemplate("len({0})"),
    "unwrap_option_or": BuiltinTemplate("({0} if {0} is not None else {1})"),
    "int64_to_int32": BuiltinTemplate("int({0})"),
    "to_ptr_int64": BuiltinTemplate("{0}"),  # Python doesn't need pointers
    "to_ptr_string": BuiltinTemplate("{0}"),
    "to_ptr_bool": BuiltinTemplate("{0}"),
    "map": BuiltinTemplate("[{0}(x) for x in {1}]"),
    "list_concat": BuiltinTemplate(
        "(list({0}) + list({1} if {1} is not None else []))"
    ),
    "list_push": BuiltinTemplate("None", ["{0}.append({1})"]),
    "list_slice": BuiltinTemplate("{0}[{1}:{2}]"),
    "list_sort": BuiltinTemplate("sorted({0})"),
    "fragment_id_from_string": BuiltinTemplate(
        "fragments_pb2.FragmentId(id={0}.encode())"
    ),
    "relation_id_from_string": BuiltinTemplate("self.relation_id_from_string({0})"),
    "relation_id_from_int": BuiltinTemplate(
        "logic_pb2.RelationId(id_low={0} & 0xFFFFFFFFFFFFFFFF, id_high=({0} >> 64) & 0xFFFFFFFFFFFFFFFF)"
    ),
    "relation_id_from_uint128": BuiltinTemplate(
        "logic_pb2.RelationId(id_low={0}.low, id_high={0}.high)"
    ),
    "match_lookahead_terminal": BuiltinTemplate(
        "self.match_lookahead_terminal({0}, {1})"
    ),
    "match_lookahead_literal": BuiltinTemplate(
        "self.match_lookahead_literal({0}, {1})"
    ),
    "consume_literal": BuiltinTemplate("None", ["self.consume_literal({0})"]),
    "consume_terminal": BuiltinTemplate("self.consume_terminal({0})"),
    "current_token": BuiltinTemplate("self.lookahead(0)"),
    "start_fragment": BuiltinTemplate("{0}", ["self.start_fragment({0})"]),
    "construct_fragment": BuiltinTemplate("self.construct_fragment({0}, {1})"),
    "error": BuiltinTemplate(None, ["raise ParseError({0})"]),
    "error_with_token": BuiltinTemplate(
        None, ['raise ParseError(f"{{{0}}}: {{{1}.type}}=`{{{1}.value}}`")']
    ),
    # Pretty-printing builtins
    "write_io": BuiltinTemplate("None", ["self.write({0})"]),
    "newline_io": BuiltinTemplate("None", ["self.newline()"]),
    "indent_io": BuiltinTemplate("None", ["self.indent()"]),
    "dedent_io": BuiltinTemplate("None", ["self.dedent()"]),
    "format_int64": BuiltinTemplate("str({0})"),
    "format_int32": BuiltinTemplate("str({0})"),
    "format_float64": BuiltinTemplate("str({0})"),
    "format_string": BuiltinTemplate("self.format_string_value({0})"),
    "format_symbol": BuiltinTemplate("{0}"),
    "format_bool": BuiltinTemplate("('true' if {0} else 'false')"),
    "format_decimal": BuiltinTemplate("self.format_decimal({0})"),
    "format_int128": BuiltinTemplate("self.format_int128({0})"),
    "format_uint128": BuiltinTemplate("self.format_uint128({0})"),
    "greater": BuiltinTemplate("({0} > {1})"),
    "to_string": BuiltinTemplate("str({0})"),
    # Type conversions used by pretty printer
    "int32_to_int64": BuiltinTemplate("int({0})"),
    "is_empty": BuiltinTemplate("len({0}) == 0"),
    "decode_string": BuiltinTemplate("{0}.decode('utf-8')"),
    "fragment_id_to_string": BuiltinTemplate("self.fragment_id_to_string({0})"),
    "relation_id_to_string": BuiltinTemplate("self.relation_id_to_string({0})"),
    "relation_id_to_int": BuiltinTemplate("self.relation_id_to_int({0})"),
    "relation_id_to_uint128": BuiltinTemplate("self.relation_id_to_uint128({0})"),
    "start_pretty_fragment": BuiltinTemplate(
        "{0}", ["self.start_pretty_fragment({0})"]
    ),
}


# Julia builtin templates
JULIA_TEMPLATES: dict[str, BuiltinTemplate] = {
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
    "has_proto_field": BuiltinTemplate("_has_proto_field({0}, Symbol({1}))"),
    "string_to_upper": BuiltinTemplate("uppercase({0})"),
    "string_in_list": BuiltinTemplate("({0} in {1})"),
    "subtract": BuiltinTemplate("({0} - {1})"),
    "string_concat": BuiltinTemplate("({0} * {1})"),
    "encode_string": BuiltinTemplate("Vector{{UInt8}}({0})"),
    "tuple": BuiltinTemplate("({args},)"),
    "length": BuiltinTemplate("length({0})"),
    "unwrap_option_or": BuiltinTemplate("(!isnothing({0}) ? {0} : {1})"),
    "int64_to_int32": BuiltinTemplate("Int32({0})"),
    "to_ptr_int64": BuiltinTemplate("{0}"),  # Julia doesn't need pointers
    "to_ptr_string": BuiltinTemplate("{0}"),
    "to_ptr_bool": BuiltinTemplate("{0}"),
    "map": BuiltinTemplate("map({0}, {1})"),
    "list_concat": BuiltinTemplate("vcat({0}, !isnothing({1}) ? {1} : [])"),
    "list_push": BuiltinTemplate("nothing", ["push!({0}, {1})"]),
    "list_slice": BuiltinTemplate("{0}[{1} + 1:{2}]"),
    "list_sort": BuiltinTemplate("sort({0})"),
    "fragment_id_from_string": BuiltinTemplate(
        "Proto.FragmentId(Vector{{UInt8}}({0}))"
    ),
    "relation_id_from_string": BuiltinTemplate("relation_id_from_string(parser, {0})"),
    "relation_id_from_int": BuiltinTemplate(
        "Proto.RelationId({0} & 0xFFFFFFFFFFFFFFFF, ({0} >> 64) & 0xFFFFFFFFFFFFFFFF)"
    ),
    "relation_id_from_uint128": BuiltinTemplate("Proto.RelationId({0}.low, {0}.high)"),
    "match_lookahead_terminal": BuiltinTemplate(
        "match_lookahead_terminal(parser, {0}, {1})"
    ),
    "match_lookahead_literal": BuiltinTemplate(
        "match_lookahead_literal(parser, {0}, {1})"
    ),
    "consume_literal": BuiltinTemplate("nothing", ["consume_literal!(parser, {0})"]),
    "consume_terminal": BuiltinTemplate("consume_terminal!(parser, {0})"),
    "current_token": BuiltinTemplate("lookahead(parser, 0)"),
    "start_fragment": BuiltinTemplate("{0}", ["start_fragment!(parser, {0})"]),
    "construct_fragment": BuiltinTemplate("construct_fragment(parser, {0}, {1})"),
    "error": BuiltinTemplate(None, ["throw(ParseError({0}))"]),
    "error_with_token": BuiltinTemplate(
        None, ['throw(ParseError({0} * ": " * string({1})))']
    ),
    # Pretty-printing builtins
    "write_io": BuiltinTemplate("nothing", ["write(pp, {0})"]),
    "newline_io": BuiltinTemplate("nothing", ["newline(pp)"]),
    "indent_io": BuiltinTemplate("nothing", ["indent!(pp)"]),
    "dedent_io": BuiltinTemplate("nothing", ["dedent!(pp)"]),
    "format_int64": BuiltinTemplate("string({0})"),
    "format_int32": BuiltinTemplate("string({0})"),
    "format_float64": BuiltinTemplate("format_float64({0})"),
    "format_string": BuiltinTemplate("format_string_value({0})"),
    "format_symbol": BuiltinTemplate("{0}"),
    "format_bool": BuiltinTemplate('({0} ? "true" : "false")'),
    "format_decimal": BuiltinTemplate("format_decimal(pp, {0})"),
    "format_int128": BuiltinTemplate("format_int128(pp, {0})"),
    "format_uint128": BuiltinTemplate("format_uint128(pp, {0})"),
    "greater": BuiltinTemplate("({0} > {1})"),
    "to_string": BuiltinTemplate("string({0})"),
    # Type conversions used by pretty printer
    "int32_to_int64": BuiltinTemplate("Int64({0})"),
    "is_empty": BuiltinTemplate("isempty({0})"),
    "decode_string": BuiltinTemplate("String(copy({0}))"),
    "fragment_id_to_string": BuiltinTemplate("fragment_id_to_string(pp, {0})"),
    "relation_id_to_string": BuiltinTemplate("relation_id_to_string(pp, {0})"),
    "relation_id_to_int": BuiltinTemplate("relation_id_to_int(pp, {0})"),
    "relation_id_to_uint128": BuiltinTemplate("relation_id_to_uint128(pp, {0})"),
    "start_pretty_fragment": BuiltinTemplate("{0}", ["start_pretty_fragment(pp, {0})"]),
}


# Go builtin templates
# Note: option-related builtins (some, is_none, is_some, unwrap_option, unwrap_option_or)
# are intercepted at the AST level in codegen_go.py._generate_option_builtin.
# The templates here serve as fallbacks.
GO_TEMPLATES: dict[str, BuiltinTemplate] = {
    "some": BuiltinTemplate("ptr({0})"),
    "not": BuiltinTemplate("!({0})"),
    "and": BuiltinTemplate("({0} && {1})"),
    "or": BuiltinTemplate("({0} || {1})"),
    "equal": BuiltinTemplate("{0} == {1}"),
    "not_equal": BuiltinTemplate("{0} != {1}"),
    "add": BuiltinTemplate("({0} + {1})"),
    "is_none": BuiltinTemplate("{0} == nil"),
    "is_some": BuiltinTemplate("{0} != nil"),
    "unwrap_option": BuiltinTemplate("*{0}"),
    "none": BuiltinTemplate("nil"),
    "make_empty_bytes": BuiltinTemplate("[]byte{}"),
    "dict_from_list": BuiltinTemplate("dictFromList({0})"),
    "dict_get": BuiltinTemplate("dictGetValue({0}, {1})"),
    "has_proto_field": BuiltinTemplate("hasProtoField({0}, {1})"),
    "string_to_upper": BuiltinTemplate("strings.ToUpper({0})"),
    "string_in_list": BuiltinTemplate("stringInList({0}, {1})"),
    "subtract": BuiltinTemplate("({0} - {1})"),
    "string_concat": BuiltinTemplate("({0} + {1})"),
    "encode_string": BuiltinTemplate("[]byte({0})"),
    "tuple": BuiltinTemplate("[]interface{}{{args}}"),
    "length": BuiltinTemplate("int64(len({0}))"),
    # unwrap_option_or is handled specially in codegen_go.py due to Go's lack of ternary
    "unwrap_option_or": BuiltinTemplate("{0}"),  # Placeholder - overridden in codegen
    "int64_to_int32": BuiltinTemplate("int32({0})"),
    "to_ptr_int64": BuiltinTemplate("ptrInt64({0})"),
    "to_ptr_string": BuiltinTemplate("ptrString({0})"),
    "to_ptr_bool": BuiltinTemplate("ptrBool({0})"),
    "map": BuiltinTemplate("mapSlice({1}, {0})"),
    "list_push": BuiltinTemplate("nil", ["{0} = append({0}, {1})"]),
    "list_concat": BuiltinTemplate("listConcat({0}, {1})"),
    "list_sort": BuiltinTemplate("listSort({0})"),
    "fragment_id_from_string": BuiltinTemplate("&pb.FragmentId{{Id: []byte({0})}}"),
    "relation_id_from_string": BuiltinTemplate("p.relationIdFromString({0})"),
    "relation_id_from_int": BuiltinTemplate(
        "&pb.RelationId{{IdLow: uint64({0}) & 0xFFFFFFFFFFFFFFFF, IdHigh: uint64({0}) >> 64 & 0xFFFFFFFFFFFFFFFF}}"
    ),
    "relation_id_from_uint128": BuiltinTemplate(
        "&pb.RelationId{{IdLow: {0}.Low, IdHigh: {0}.High}}"
    ),
    "match_lookahead_terminal": BuiltinTemplate("p.matchLookaheadTerminal({0}, {1})"),
    "match_lookahead_literal": BuiltinTemplate("p.matchLookaheadLiteral({0}, {1})"),
    "consume_literal": BuiltinTemplate("nil", ["p.consumeLiteral({0})"]),
    "consume_terminal": BuiltinTemplate("p.consumeTerminal({0})"),
    "current_token": BuiltinTemplate("p.lookahead(0)"),
    "start_fragment": BuiltinTemplate("{0}", ["p.startFragment({0})"]),
    "construct_fragment": BuiltinTemplate("p.constructFragment({0}, {1})"),
    "error": BuiltinTemplate(None, ["panic(ParseError{{msg: {0}}})"]),
    "error_with_token": BuiltinTemplate(
        None,
        [
            'panic(ParseError{{msg: fmt.Sprintf("%s: %s=`%v`", {0}, {1}.Type, {1}.Value)}})'
        ],
    ),
    # Pretty-printing builtins
    "write_io": BuiltinTemplate("nil", ["p.write({0})"]),
    "newline_io": BuiltinTemplate("nil", ["p.newline()"]),
    "indent_io": BuiltinTemplate("nil", ["p.indent()"]),
    "dedent_io": BuiltinTemplate("nil", ["p.dedent()"]),
    "format_int64": BuiltinTemplate('fmt.Sprintf("%d", {0})'),
    "format_int32": BuiltinTemplate('fmt.Sprintf("%d", {0})'),
    "format_float64": BuiltinTemplate('fmt.Sprintf("%g", {0})'),
    "format_string": BuiltinTemplate("p.formatStringValue({0})"),
    "format_symbol": BuiltinTemplate("{0}"),
    "format_bool": BuiltinTemplate("formatBool({0})"),
    "format_decimal": BuiltinTemplate("p.formatDecimal({0})"),
    "format_int128": BuiltinTemplate("p.formatInt128({0})"),
    "format_uint128": BuiltinTemplate("p.formatUint128({0})"),
    "greater": BuiltinTemplate("({0} > {1})"),
    "to_string": BuiltinTemplate('fmt.Sprintf("%v", {0})'),
    # Type conversions used by pretty printer
    "int32_to_int64": BuiltinTemplate("int64({0})"),
    "is_empty": BuiltinTemplate("len({0}) == 0"),
    "decode_string": BuiltinTemplate("string({0})"),
    "fragment_id_to_string": BuiltinTemplate("p.fragmentIdToString({0})"),
    "relation_id_to_string": BuiltinTemplate("p.relationIdToString({0})"),
    "relation_id_to_int": BuiltinTemplate("p.relationIdToInt({0})"),
    "relation_id_to_uint128": BuiltinTemplate("p.relationIdToUint128({0})"),
}

__all__ = [
    "BuiltinTemplate",
    "PYTHON_TEMPLATES",
    "JULIA_TEMPLATES",
    "GO_TEMPLATES",
]
