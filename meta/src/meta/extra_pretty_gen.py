"""Generate target IR for extra pretty printers (uncovered proto types).

Builds PrintNonterminalDef IR nodes for proto messages and enums not
covered by grammar rules. The IR flows through the existing
codegen.generate_def() pipeline, eliminating per-language duplication.
"""

import re
from typing import Any

from .grammar import Nonterminal
from .proto_ast import ProtoEnum, ProtoField, ProtoMessage, ProtoOneof
from .target import (
    BaseType,
    Call,
    EnumType,
    EnumValue,
    ForeachEnumerated,
    GetField,
    IfElse,
    Lit,
    MessageType,
    NewMessage,
    OptionType,
    PrintNonterminalDef,
    Seq,
    SequenceType,
    TargetExpr,
    TargetType,
    Var,
)
from .target_builtins import INT64, STRING, VOID, make_builtin

# Token-type messages that have format_* helpers in the templates.
TOKEN_MESSAGES: dict[str, str] = {
    "DecimalValue": "format_decimal",
    "Int128Value": "format_int128",
    "UInt128Value": "format_uint128",
}

# Proto scalar type -> target IR base type
PROTO_TYPE_MAP: dict[str, BaseType] = {
    "string": BaseType("String"),
    "int32": BaseType("Int32"),
    "int64": BaseType("Int64"),
    "uint32": BaseType("UInt32"),
    "uint64": BaseType("UInt64"),
    "fixed64": BaseType("UInt64"),
    "float": BaseType("Float64"),
    "double": BaseType("Float64"),
    "bool": BaseType("Boolean"),
    "bytes": BaseType("Bytes"),
}

# Proto scalar type -> format builtin name
PROTO_FORMAT_MAP: dict[str, str] = {
    "string": "format_string",
    "int32": "format_int32",
    "int64": "format_int64",
    "uint32": "format_int64",
    "uint64": "format_int64",
    "fixed64": "format_int64",
    "float": "format_float64",
    "double": "format_float64",
    "bool": "format_bool",
    "bytes": "format_bytes",
}


def snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def enum_common_prefix(values: list[tuple[str, int]]) -> str:
    """Find the common uppercase prefix of enum value names.

    Ensures the prefix ends at an underscore boundary.
    """
    if not values:
        return ""
    names = [v[0] for v in values]
    prefix = names[0]
    for name in names[1:]:
        while not name.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    if prefix and not prefix.endswith("_"):
        last_underscore = prefix.rfind("_")
        if last_underscore >= 0:
            prefix = prefix[: last_underscore + 1]
        else:
            prefix = ""
    return prefix


def _proto_field_type(proto_type: str, module: str) -> TargetType:
    """Convert a proto type string to a target IR type."""
    if proto_type in PROTO_TYPE_MAP:
        return PROTO_TYPE_MAP[proto_type]
    return MessageType(module, proto_type)


def _is_scalar(proto_type: str) -> bool:
    """Check if a proto type is a scalar (has a format builtin)."""
    return proto_type in PROTO_FORMAT_MAP


# ---------------------------------------------------------------------------
# IR construction helpers
# ---------------------------------------------------------------------------


def _call(name: str, args: list[TargetExpr] | None = None) -> Call:
    """Build Call(make_builtin(name), args)."""
    return Call(make_builtin(name), args or [])


def _write(s: str) -> Call:
    """write_io(Lit(s))."""
    return _call("write_io", [Lit(s)])


def _write_expr(expr: TargetExpr) -> Call:
    """write_io(expr)."""
    return _call("write_io", [expr])


def _format_scalar(proto_type: str, value: TargetExpr) -> Call:
    """Call the appropriate format_* builtin for a scalar value."""
    return _call(PROTO_FORMAT_MAP[proto_type], [value])


def _print_value(proto_type: str, value: TargetExpr) -> TargetExpr:
    """Print a value: write(format(v)) for scalars, pp_dispatch for messages."""
    if _is_scalar(proto_type):
        return _write_expr(_format_scalar(proto_type, value))
    return _call("pp_dispatch", [value])


# ---------------------------------------------------------------------------
# Field and oneof IR builders
# ---------------------------------------------------------------------------


def _field_stmts(
    msg_var: Var,
    field: ProtoField,
    msg_type: MessageType,
    module: str,
) -> list[TargetExpr]:
    """Build IR statements for printing a single proto field."""
    field_target = _proto_field_type(field.type, module)
    stmts: list[TargetExpr] = [
        _call("newline_io"),
        _write(f":{field.name} "),
    ]

    if field.is_repeated:
        seq_type = SequenceType(field_target)
        collection = GetField(msg_var, field.name, msg_type, seq_type)
        idx = Var("_idx", INT64)
        elem = Var("_elem", field_target)
        loop_body = Seq(
            [
                IfElse(
                    _call("greater", [idx, Lit(0)]),
                    _write(" "),
                    Lit(None),
                ),
                _print_value(field.type, elem),
            ]
        )
        stmts.append(_write("("))
        stmts.append(ForeachEnumerated(idx, elem, collection, loop_body))
        stmts.append(_write(")"))

    elif field.is_optional:
        opt_type = OptionType(field_target)
        field_expr = GetField(msg_var, field.name, msg_type, opt_type)
        stmts.append(
            IfElse(
                _call("is_some", [field_expr]),
                _print_value(field.type, field_expr),
                _write("nothing"),
            )
        )

    else:
        field_expr = GetField(msg_var, field.name, msg_type, field_target)
        stmts.append(_print_value(field.type, field_expr))

    return stmts


def _oneof_stmts(
    msg_var: Var,
    oneof: ProtoOneof,
    msg_type: MessageType,
    module: str,
) -> list[TargetExpr]:
    """Build IR statements for printing a oneof group."""
    stmts: list[TargetExpr] = [
        _call("newline_io"),
        _write(f":{oneof.name} "),
    ]

    # Build nested IfElse: check each variant, else "nothing"
    else_branch: TargetExpr = _write("nothing")
    for variant in reversed(oneof.fields):
        v_type = _proto_field_type(variant.type, module)
        v_field = GetField(msg_var, variant.name, msg_type, v_type)
        then_branch = Seq(
            [
                _write(f"(:{variant.name} "),
                _print_value(variant.type, v_field),
                _write(")"),
            ]
        )
        condition = _call("has_proto_field", [msg_var, Lit(variant.name)])
        else_branch = IfElse(condition, then_branch, else_branch)

    stmts.append(else_branch)
    return stmts


# ---------------------------------------------------------------------------
# PrintNonterminalDef builders per category
# ---------------------------------------------------------------------------


def _build_generic_message_def(msg: ProtoMessage) -> PrintNonterminalDef:
    """Build a generic field-by-field S-expression printer."""
    sname = snake_case(msg.name)
    msg_type = MessageType(msg.module, msg.name)
    msg_var = Var("msg", msg_type)

    has_content = bool(msg.fields) or bool(msg.oneofs)
    if not has_content:
        body: TargetExpr = _write(sname)
    else:
        items: list[TargetExpr] = [
            _write(f"({sname}"),
            _call("indent_sexp_io"),
        ]
        for field in msg.fields:
            items.extend(_field_stmts(msg_var, field, msg_type, msg.module))
        for oneof in msg.oneofs:
            items.extend(_oneof_stmts(msg_var, oneof, msg_type, msg.module))
        items.append(_write(")"))
        items.append(_call("dedent_io"))
        body = Seq(items)

    return PrintNonterminalDef(
        nonterminal=Nonterminal(sname, msg_type),
        params=[msg_var],
        return_type=VOID,
        body=body,
    )


def _build_token_message_def(
    msg_name: str,
    module: str,
    format_fn: str,
) -> PrintNonterminalDef:
    """Build a printer that wraps a format_* helper (DecimalValue, etc.)."""
    sname = snake_case(msg_name)
    msg_type = MessageType(module, msg_name)
    msg_var = Var("msg", msg_type)
    body = _write_expr(_call(format_fn, [msg_var]))
    return PrintNonterminalDef(
        nonterminal=Nonterminal(sname, msg_type),
        params=[msg_var],
        return_type=VOID,
        body=body,
    )


def _build_missing_value_def(module: str) -> PrintNonterminalDef:
    """Build a printer for MissingValue."""
    msg_type = MessageType(module, "MissingValue")
    msg_var = Var("msg", msg_type)
    return PrintNonterminalDef(
        nonterminal=Nonterminal("missing_value", msg_type),
        params=[msg_var],
        return_type=VOID,
        body=_write("missing"),
    )


def _build_debug_info_def() -> PrintNonterminalDef:
    """Build a printer for DebugInfo (paired ids + orig_names)."""
    msg_type = MessageType("fragments", "DebugInfo")
    msg_var = Var("msg", msg_type)
    rid_type = MessageType("logic", "RelationId")

    idx_var = Var("_idx", INT64)
    rid_var = Var("_rid", rid_type)

    ids_field = GetField(msg_var, "ids", msg_type, SequenceType(rid_type))
    names_field = GetField(msg_var, "orig_names", msg_type, SequenceType(STRING))

    uint128_msg = NewMessage(
        "logic",
        "UInt128Value",
        [
            ("low", GetField(rid_var, "id_low", rid_type, INT64)),
            ("high", GetField(rid_var, "id_high", rid_type, INT64)),
        ],
    )

    name_at_idx = _call("get_at", [names_field, idx_var])

    loop_body = Seq(
        [
            _call("newline_io"),
            _write("("),
            _call("pp_dispatch", [uint128_msg]),
            _write(" "),
            _write_expr(_call("format_string", [name_at_idx])),
            _write(")"),
        ]
    )

    body = Seq(
        [
            _write("(debug_info"),
            _call("indent_sexp_io"),
            ForeachEnumerated(idx_var, rid_var, ids_field, loop_body),
            _write(")"),
            _call("dedent_io"),
        ]
    )

    return PrintNonterminalDef(
        nonterminal=Nonterminal("debug_info", msg_type),
        params=[msg_var],
        return_type=VOID,
        body=body,
    )


def _build_enum_def(enum: ProtoEnum) -> PrintNonterminalDef:
    """Build a printer for an enum type (if-else chain with common-prefix stripping)."""
    sname = snake_case(enum.name)
    enum_type = EnumType(enum.module, enum.name)
    x_var = Var("x", enum_type)

    prefix = enum_common_prefix(enum.values)

    # Build nested IfElse chain (last else is Lit(None) — no match)
    body: TargetExpr = Lit(None)
    for val_name, _ in reversed(enum.values):
        short = (
            val_name[len(prefix) :].lower()
            if val_name.startswith(prefix)
            else val_name.lower()
        )
        condition = _call(
            "equal",
            [x_var, EnumValue(enum.module, enum.name, val_name)],
        )
        body = IfElse(condition, _write(short), body)

    return PrintNonterminalDef(
        nonterminal=Nonterminal(sname, enum_type),
        params=[x_var],
        return_type=VOID,
        body=body,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def generate_extra_pretty_defs(
    proto_messages: dict[tuple[str, str], Any],
    proto_enums: dict[str, ProtoEnum] | None,
    grammar_covered_types: set[tuple[str, str]],
) -> list[PrintNonterminalDef]:
    """Generate PrintNonterminalDef for all uncovered proto types.

    Args:
        proto_messages: (module, name) -> ProtoMessage
        proto_enums: name -> ProtoEnum
        grammar_covered_types: (module, name) pairs already covered by grammar

    Returns:
        List of PrintNonterminalDef IR nodes.
    """
    defs: list[PrintNonterminalDef] = []

    for (module, msg_name), proto_msg in sorted(proto_messages.items()):
        if (module, msg_name) in grammar_covered_types:
            continue

        if msg_name in TOKEN_MESSAGES:
            defs.append(
                _build_token_message_def(msg_name, module, TOKEN_MESSAGES[msg_name])
            )
        elif msg_name == "MissingValue":
            defs.append(_build_missing_value_def(module))
        elif msg_name == "DebugInfo":
            defs.append(_build_debug_info_def())
        else:
            defs.append(_build_generic_message_def(proto_msg))

    if proto_enums:
        for proto_enum in sorted(proto_enums.values(), key=lambda e: e.name):
            defs.append(_build_enum_def(proto_enum))

    return defs
