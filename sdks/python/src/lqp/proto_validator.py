"""
Validator for protobuf-based LQP messages.

Operates on protobuf messages (transactions_pb2.Transaction).
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from google.protobuf.descriptor import Descriptor, FieldDescriptor
from google.protobuf.message import Message

from lqp.proto.v1 import fragments_pb2, logic_pb2, transactions_pb2


class ValidationError(Exception):
    pass


# --- Helpers ---


def relation_id_key(rid: logic_pb2.RelationId) -> tuple[int, int]:
    """Hashable key for a RelationId."""
    return (rid.id_low, rid.id_high)


def relation_id_hex(rid: logic_pb2.RelationId) -> str:
    """Hex string for a RelationId, for error messages."""
    val = rid.id_low | (rid.id_high << 64)
    return hex(val)


_TYPE_ONEOF_TO_NAME = {
    "unspecified_type": "UNSPECIFIED",
    "string_type": "STRING",
    "int_type": "INT",
    "float_type": "FLOAT",
    "uint128_type": "UINT128",
    "int128_type": "INT128",
    "date_type": "DATE",
    "datetime_type": "DATETIME",
    "missing_type": "MISSING",
    "decimal_type": "DECIMAL",
    "boolean_type": "BOOLEAN",
}


def get_type_name(type_msg: logic_pb2.Type) -> str:
    """Map a Type message's oneof to a name like 'STRING', 'INT', etc."""
    which = type_msg.WhichOneof("type")
    if which is None:
        return "UNSPECIFIED"
    return _TYPE_ONEOF_TO_NAME.get(which, "UNSPECIFIED")


_VALUE_ONEOF_TO_TYPE_NAME = {
    "string_value": "STRING",
    "int_value": "INT",
    "float_value": "FLOAT",
    "uint128_value": "UINT128",
    "int128_value": "INT128",
    "missing_value": "MISSING",
    "date_value": "DATE",
    "datetime_value": "DATETIME",
    "decimal_value": "DECIMAL",
    "boolean_value": "BOOLEAN",
}


def get_value_type_name(value_msg: logic_pb2.Value) -> str:
    """Map a Value message's oneof to the corresponding type name."""
    which = value_msg.WhichOneof("value")
    if which is None:
        return "UNSPECIFIED"
    return _VALUE_ONEOF_TO_TYPE_NAME.get(which, "UNSPECIFIED")


def build_debug_info(debug_info: fragments_pb2.DebugInfo) -> dict[tuple[int, int], str]:
    """Convert DebugInfo parallel arrays to a dict keyed by (id_low, id_high)."""
    result = {}
    for rid, name in zip(debug_info.ids, debug_info.orig_names):
        result[relation_id_key(rid)] = name
    return result


def proto_term_str(term: logic_pb2.Term) -> str:
    """Format a Term for error messages."""
    which = term.WhichOneof("term_type")
    if which == "var":
        return term.var.name
    elif which == "constant":
        return _format_value(term.constant)
    return "?"


def _format_value(val: logic_pb2.Value) -> str:
    """Format a Value for error messages."""
    which = val.WhichOneof("value")
    if which == "string_value":
        return repr(val.string_value)
    elif which == "int_value":
        return str(val.int_value)
    elif which == "float_value":
        return str(val.float_value)
    elif which == "boolean_value":
        return str(val.boolean_value).lower()
    elif which == "uint128_value":
        v = val.uint128_value.low | (val.uint128_value.high << 64)
        return hex(v)
    elif which == "int128_value":
        v = val.int128_value.low | (val.int128_value.high << 64)
        return str(v)
    elif which == "missing_value":
        return "missing"
    elif which == "date_value":
        d = val.date_value
        return f"{d.year}-{d.month:02d}-{d.day:02d}"
    elif which == "datetime_value":
        dt = val.datetime_value
        return f"{dt.year}-{dt.month:02d}-{dt.day:02d}T{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
    elif which == "decimal_value":
        return f"decimal({val.decimal_value.precision},{val.decimal_value.scale})"
    return f"<{which}>" if which else "?"


# --- Oneof unwrappers ---


def unwrap_declaration(decl: logic_pb2.Declaration) -> Message | None:
    which = decl.WhichOneof("declaration_type")
    if which is None:
        return None
    return getattr(decl, which)


def unwrap_instruction(instr: logic_pb2.Instruction) -> Message | None:
    which = instr.WhichOneof("instr_type")
    if which is None:
        return None
    return getattr(instr, which)


def unwrap_formula(formula: logic_pb2.Formula) -> Message | None:
    which = formula.WhichOneof("formula_type")
    if which is None:
        return None
    return getattr(formula, which)


def unwrap_construct(construct: logic_pb2.Construct) -> Message | None:
    which = construct.WhichOneof("construct_type")
    if which is None:
        return None
    return getattr(construct, which)


def unwrap_write(write: transactions_pb2.Write) -> Message | None:
    which = write.WhichOneof("write_type")
    if which is None:
        return None
    return getattr(write, which)


def unwrap_read(read: transactions_pb2.Read) -> Message | None:
    which = read.WhichOneof("read_type")
    if which is None:
        return None
    return getattr(read, which)


def unwrap_constraint(constraint: logic_pb2.Constraint) -> Message | None:
    which = constraint.WhichOneof("constraint_type")
    if which is None:
        return None
    return getattr(constraint, which)


def unwrap_data(data: logic_pb2.Data) -> Message | None:
    which = data.WhichOneof("data_type")
    if which is None:
        return None
    return getattr(data, which)


# --- Identity-based provenance ---

_Unwrapper = Callable[[Message], Message | None]

# Wrapper types whose oneof should be unwrapped before visiting.
# New proto wrapper types must be added here or they silently fall through to generic_visit.
_WRAPPER_TYPES: dict[str, _Unwrapper] = {
    "Declaration": cast(_Unwrapper, unwrap_declaration),
    "Instruction": cast(_Unwrapper, unwrap_instruction),
    "Formula": cast(_Unwrapper, unwrap_formula),
    "Construct": cast(_Unwrapper, unwrap_construct),
    "Write": cast(_Unwrapper, unwrap_write),
    "Read": cast(_Unwrapper, unwrap_read),
    "Constraint": cast(_Unwrapper, unwrap_constraint),
    "Data": cast(_Unwrapper, unwrap_data),
}


class _NodeSpans:
    """Identity-based provenance: maps id(node) -> span.

    Keeps strong references to all nodes so their ids remain stable.
    """

    __slots__ = ("_spans", "_refs")

    def __init__(self) -> None:
        self._spans: dict[int, Any] = {}
        self._refs: list[Message] = []

    def record(self, node: Message, span: Any) -> None:
        self._refs.append(node)
        self._spans[id(node)] = span

    def get(self, node_id: int) -> Any:
        return self._spans.get(node_id)


def _unwrap_oneof(node: Message) -> Message | None:
    """Unwrap a oneof message to its inner message."""
    desc: Descriptor = node.DESCRIPTOR  # type: ignore[assignment]
    if not desc.oneofs:
        return None
    oneof = desc.oneofs[0]
    which = node.WhichOneof(oneof.name)
    if which is None:
        return None
    inner = getattr(node, which)
    if isinstance(inner, Message):
        return inner
    return None


# Types whose parse function immediately dispatches to the inner type's
# parse function without consuming any tokens. These share the same parse
# offset as their inner message and must be skipped during offset matching.
_TRANSPARENT_WRAPPERS: set[str] = {
    "Declaration", "Instruction", "Formula", "Construct",
    "Write", "Read", "Data",
    "Term", "Type", "RelTerm", "Monoid",
}


class _SpanNode:
    """Node in the span nesting tree."""

    __slots__ = ("offset", "span", "children", "_idx")

    def __init__(self, offset: int, span: Any) -> None:
        self.offset = offset
        self.span = span
        self.children: list[_SpanNode] = []
        self._idx = 0

    def next_child(self) -> "_SpanNode | None":
        if self._idx < len(self.children):
            child = self.children[self._idx]
            self._idx += 1
            return child
        return None

    def peek_child(self) -> "_SpanNode | None":
        if self._idx < len(self.children):
            return self.children[self._idx]
        return None


def _build_span_tree(provenance: dict[int, Any]) -> _SpanNode:
    """Build a nesting tree from spans based on containment.

    Each span's children are the spans directly contained within it.
    Spans are sorted by start offset, with wider spans first for ties.
    """
    sorted_items = sorted(
        provenance.items(), key=lambda x: (x[0], -x[1].stop.offset)
    )
    sentinel = _SpanNode(-1, None)
    stack: list[tuple[_SpanNode, int]] = [(sentinel, 2**63)]
    for offset, span in sorted_items:
        end = span.stop.offset
        while end > stack[-1][1]:
            stack.pop()
        node = _SpanNode(offset, span)
        stack[-1][0].children.append(node)
        stack.append((node, end))
    return sentinel


def _build_node_spans(
    root: Message,
    offset_provenance: dict[int, Any],
) -> _NodeSpans:
    """Convert offset-based provenance to identity-based provenance.

    Builds a span nesting tree and walks it alongside the protobuf tree.
    Each proto node is matched to the next span child at the current
    nesting level. Proto nodes without a corresponding span (inline
    constructions) are skipped and their children use the parent's span
    context.
    """
    result = _NodeSpans()
    span_tree = _build_span_tree(offset_provenance)
    _walk_and_match(root, span_tree, result)
    return result


def _walk_fields(
    node: Message,
    active: _SpanNode,
    result: _NodeSpans,
) -> None:
    """Walk all message-typed fields of a node."""
    descriptor: Descriptor = node.DESCRIPTOR  # type: ignore[assignment]
    for field_desc in descriptor.fields:
        value = getattr(node, field_desc.name)
        if field_desc.label == FieldDescriptor.LABEL_REPEATED:
            for item in value:
                if isinstance(item, Message):
                    _walk_and_match(item, active, result)
        elif field_desc.message_type is not None and node.HasField(field_desc.name):
            if isinstance(value, Message):
                _walk_and_match(value, active, result)


def _try_consume(
    type_name: str,
    span_parent: _SpanNode,
) -> _SpanNode | None:
    """Consume the next span child if its type_name matches, else return None."""
    peeked = span_parent.peek_child()
    if peeked is not None and peeked.span.type_name == type_name:
        return span_parent.next_child()
    return None


def _walk_and_match(
    node: Message,
    span_parent: _SpanNode,
    result: _NodeSpans,
) -> None:
    """Walk proto tree and span nesting tree simultaneously.

    Each span carries a type_name recorded by the parser. A proto node
    only consumes a span child whose type_name matches. Nodes created
    inline (without their own parse function) have no matching span and
    are skipped, preventing them from stealing sibling spans.
    """
    type_name = type(node).__name__

    # Transparent wrappers: skip entirely, pass through to inner.
    if type_name in _TRANSPARENT_WRAPPERS:
        inner = _unwrap_oneof(node)
        if inner is not None:
            _walk_and_match(inner, span_parent, result)
        return

    # Non-transparent wrapper types (e.g. Constraint): consume a span,
    # walk non-oneof fields first (they were parsed before the inner
    # type's fields), then unwrap the oneof and walk the inner type's
    # fields directly without consuming an additional span.
    unwrapper = _WRAPPER_TYPES.get(type_name)
    if unwrapper is not None:
        matched = _try_consume(type_name, span_parent)
        if matched is not None:
            result.record(node, matched.span)
        active = matched if matched is not None else span_parent

        desc: Descriptor = node.DESCRIPTOR  # type: ignore[assignment]
        oneof_field_names: set[str] = set()
        for oneof_desc in desc.oneofs:
            for field in oneof_desc.fields:
                oneof_field_names.add(field.name)
        for field_desc in desc.fields:
            if field_desc.name in oneof_field_names:
                continue
            value = getattr(node, field_desc.name)
            if field_desc.label == FieldDescriptor.LABEL_REPEATED:
                for item in value:
                    if isinstance(item, Message):
                        _walk_and_match(item, active, result)
            elif field_desc.message_type is not None and node.HasField(field_desc.name):
                if isinstance(value, Message):
                    _walk_and_match(value, active, result)

        inner = unwrapper(node)
        if inner is not None:
            if matched is not None:
                result.record(inner, matched.span)
            _walk_fields(inner, active, result)
        return

    # Regular node: consume span only if type_name matches.
    matched = _try_consume(type_name, span_parent)
    if matched is not None:
        result.record(node, matched.span)
    active = matched if matched is not None else span_parent
    _walk_fields(node, active, result)


# --- Base visitor ---


class ProtoVisitor:
    def __init__(
        self,
        provenance: _NodeSpans | None = None,
        filename: str | None = None,
    ):
        self.original_names: dict[tuple[int, int], str] = {}
        self._visit_cache: dict[str, Any] = {}
        self._provenance = provenance or _NodeSpans()
        self._filename = filename or ""

    def get_original_name(self, rid: logic_pb2.RelationId) -> str:
        key = relation_id_key(rid)
        return self.original_names.get(key, relation_id_hex(rid))

    def _location_str(self, node: Message) -> str:
        """Return ' at file:line:col' for the given node, or '' if unavailable."""
        span = self._provenance.get(id(node))
        if span is not None:
            loc = span.start
            if self._filename:
                return f" at {self._filename}:{loc.line}:{loc.column}"
            return f" at {loc.line}:{loc.column}"
        return ""

    def _resolve_visitor(self, type_name: str):
        method = self._visit_cache.get(type_name)
        if method is None:
            method = getattr(self, f"visit_{type_name}", self.generic_visit)
            self._visit_cache[type_name] = method
        return method

    def visit(self, node: Message, *args: Any) -> None:
        if isinstance(node, fragments_pb2.Fragment):
            self.original_names = build_debug_info(node.debug_info)

        type_name = type(node).__name__

        unwrapper = _WRAPPER_TYPES.get(type_name)
        if unwrapper is not None:
            inner = unwrapper(node)
            if inner is not None:
                self.visit(inner, *args)
            return

        return self._resolve_visitor(type_name)(node, *args)

    def generic_visit(self, node: Message, *args: Any) -> None:
        descriptor: Descriptor = node.DESCRIPTOR  # type: ignore[assignment]
        for field_desc in descriptor.fields:
            value = getattr(node, field_desc.name)
            if field_desc.label == FieldDescriptor.LABEL_REPEATED:
                for item in value:
                    if isinstance(item, Message):
                        self.visit(item, *args)
            elif field_desc.message_type is not None and node.HasField(field_desc.name):
                if isinstance(value, Message):
                    self.visit(value, *args)


# --- Validation visitors ---


class UnusedVariableVisitor(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        self.scopes: list[tuple[set[str], set[str]]] = []
        self.visit(txn)

    def _declare_var(self, var_name: str):
        if self.scopes:
            self.scopes[-1][0].add(var_name)

    def _mark_var_used(self, var_name: str, node: Message):
        for declared, used in reversed(self.scopes):
            if var_name in declared:
                used.add(var_name)
                return
        raise ValidationError(
            f"Undeclared variable used{self._location_str(node)}: '{var_name}'"
        )

    def visit_Abstraction(self, node: logic_pb2.Abstraction, *args: Any):
        self.scopes.append((set(), set()))
        for binding in node.vars:
            self._declare_var(binding.var.name)
        self.visit(node.value, *args)
        declared, used = self.scopes.pop()
        unused = declared - used
        if unused:
            for var_name in unused:
                if var_name.startswith("_"):
                    continue
                raise ValidationError(f"Unused variable declared: '{var_name}'")

    def visit_Var(self, node: logic_pb2.Var, *args: Any):
        self._mark_var_used(node.name, node)

    def visit_FunctionalDependency(
        self, node: logic_pb2.FunctionalDependency, *args: Any
    ):
        self.visit(node.guard, *args)


class ShadowedVariableFinder(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        self.visit(txn)

    def visit_Abstraction(self, node: logic_pb2.Abstraction, *args: Any):
        in_scope_names: set[str] = set() if len(args) == 0 else args[0]
        for binding in node.vars:
            name = binding.var.name
            if name in in_scope_names:
                raise ValidationError(
                    f"Shadowed variable{self._location_str(binding)}: '{name}'"
                )
        new_scope = in_scope_names | {b.var.name for b in node.vars}
        self.visit(node.value, new_scope)


class DuplicateRelationIdFinder(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        self.seen_ids: dict[tuple[int, int], tuple[int, bytes | None]] = {}
        self.curr_epoch: int = 0
        self.curr_fragment: bytes | None = None
        self.visit(txn)

    def visit_Def(self, node: logic_pb2.Def, *args: Any):
        self._check_relation_id(node.name, node)

    def _check_relation_id(self, rid: logic_pb2.RelationId, node: Message):
        key = relation_id_key(rid)
        if key in self.seen_ids:
            seen_epoch, seen_frag = self.seen_ids[key]
            if self.curr_fragment != seen_frag:
                original_name = self.get_original_name(rid)
                raise ValidationError(
                    f"Duplicate declaration across fragments{self._location_str(node)}: '{original_name}'"
                )
            elif self.curr_epoch == seen_epoch:
                original_name = self.get_original_name(rid)
                raise ValidationError(
                    f"Duplicate declaration within fragment in epoch{self._location_str(node)}: '{original_name}'"
                )
        self.seen_ids[key] = (self.curr_epoch, self.curr_fragment)

    def visit_Fragment(self, node: fragments_pb2.Fragment, *args: Any):
        self.curr_fragment = node.id.id
        self.generic_visit(node, *args)

    def visit_Epoch(self, node: transactions_pb2.Epoch, *args: Any):
        self.curr_epoch += 1
        self.generic_visit(node, *args)

    def visit_Algorithm(self, node: logic_pb2.Algorithm, *args: Any):
        for rid in getattr(node, "global"):
            key = relation_id_key(rid)
            if key in self.seen_ids:
                original_name = self.get_original_name(rid)
                raise ValidationError(
                    f"Duplicate declaration{self._location_str(rid)}: '{original_name}'"
                )
            else:
                self.seen_ids[key] = (self.curr_epoch, self.curr_fragment)


class DuplicateFragmentDefinitionFinder(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        self.seen_ids: set[bytes] = set()
        self.visit(txn)

    def visit_Epoch(self, node: transactions_pb2.Epoch, *args: Any):
        self.seen_ids.clear()
        self.generic_visit(node)

    def visit_Define(self, node: transactions_pb2.Define, *args: Any):
        frag_id = node.fragment.id.id
        if frag_id in self.seen_ids:
            id_str = frag_id.decode("utf-8")
            raise ValidationError(
                f"Duplicate fragment within an epoch{self._location_str(node)}: '{id_str}'"
            )
        else:
            self.seen_ids.add(frag_id)


class AtomTypeChecker(ProtoVisitor):
    @staticmethod
    def collect_global_defs(txn: transactions_pb2.Transaction) -> list:
        """Collect globally visible instruction-like declarations."""

        class DefCollector(ProtoVisitor):
            def __init__(self, txn):
                self.atoms = []
                super().__init__()
                self.visit(txn)

            def visit_Def(self, node: logic_pb2.Def):
                self.atoms.append(("Def", node))

            def visit_Algorithm(self, node: logic_pb2.Algorithm):
                for construct in node.body.constructs:
                    inner = unwrap_construct(construct)
                    if inner is not None:
                        inner_name = type(inner).__name__
                        if inner_name == "Instruction":
                            instr = unwrap_instruction(inner)  # type: ignore[arg-type]
                            if instr is not None:
                                self.atoms.append((type(instr).__name__, instr))
                        elif inner_name in (
                            "Assign",
                            "Upsert",
                            "Break",
                            "MonoidDef",
                            "MonusDef",
                        ):
                            self.atoms.append((inner_name, inner))

            def visit_Loop(self, node: logic_pb2.Loop):
                for instr_wrapper in node.init:
                    instr = unwrap_instruction(instr_wrapper)
                    if instr is not None:
                        self.atoms.append((type(instr).__name__, instr))

        return DefCollector(txn).atoms

    @staticmethod
    def get_relation_sig(node) -> list[str]:
        """Return a list of the type names of the parameters of a Def-like node."""
        return [get_type_name(b.type) for b in node.body.vars]

    @staticmethod
    def get_relation_id(node) -> logic_pb2.RelationId:
        return node.name

    @dataclass(frozen=True)
    class State:
        relation_types: dict[tuple[int, int], list[str]]
        var_types: dict[str, str]

    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        global_defs = AtomTypeChecker.collect_global_defs(txn)
        relation_types = {}
        for _, node in global_defs:
            rid = AtomTypeChecker.get_relation_id(node)
            key = relation_id_key(rid)
            sig = AtomTypeChecker.get_relation_sig(node)
            relation_types[key] = sig
        state = AtomTypeChecker.State(relation_types, {})
        self.visit(txn, state)

    def visit_Abstraction(self, node: logic_pb2.Abstraction, *args: Any):
        state = args[0]
        new_var_types = dict(state.var_types)
        for binding in node.vars:
            new_var_types[binding.var.name] = get_type_name(binding.type)
        self.generic_visit(
            node,
            AtomTypeChecker.State(state.relation_types, new_var_types),
        )

    def visit_Loop(self, node: logic_pb2.Loop, *args: Any):
        state = args[0]
        for instr_wrapper in node.init:
            self.visit(instr_wrapper, state)
        for construct in node.body.constructs:
            inner = unwrap_construct(construct)
            if inner is None:
                continue
            inner_name = type(inner).__name__
            if inner_name == "Instruction":
                actual_instr = unwrap_instruction(inner)  # type: ignore[arg-type]
                if actual_instr is not None:
                    key = relation_id_key(actual_instr.name)  # type: ignore[union-attr]
                    sig = [get_type_name(b.type) for b in actual_instr.body.vars]  # type: ignore[union-attr]
                    new_state = AtomTypeChecker.State(
                        {key: sig, **state.relation_types},
                        state.var_types,
                    )
                    self.visit(actual_instr, new_state)
            elif inner_name in ("Assign", "Upsert", "Break", "MonoidDef", "MonusDef"):
                key = relation_id_key(inner.name)  # type: ignore[union-attr]
                sig = [get_type_name(b.type) for b in inner.body.vars]  # type: ignore[union-attr]
                new_state = AtomTypeChecker.State(
                    {key: sig, **state.relation_types},
                    state.var_types,
                )
                self.visit(inner, new_state)
            else:
                self.visit(construct, state)

    def visit_Atom(self, node: logic_pb2.Atom, *args: Any):
        state = args[0]
        key = relation_id_key(node.name)
        if key not in state.relation_types:
            return

        relation_type_sig = state.relation_types[key]
        atom_arity = len(node.terms)
        relation_arity = len(relation_type_sig)
        if atom_arity != relation_arity:
            original_name = self.get_original_name(node.name)
            raise ValidationError(
                f"Incorrect arity for '{original_name}' atom{self._location_str(node)}: "
                f"expected {relation_arity} term{'' if relation_arity == 1 else 's'}, got {atom_arity}"
            )

        for i, (term, expected_type) in enumerate(zip(node.terms, relation_type_sig)):
            which = term.WhichOneof("term_type")
            if which == "var":
                term_type = state.var_types.get(term.var.name)
                if term_type is None:
                    continue
            elif which == "constant":
                term_type = get_value_type_name(term.constant)
            else:
                continue
            if term_type != expected_type:
                original_name = self.get_original_name(node.name)
                pretty_term = proto_term_str(term)
                raise ValidationError(
                    f"Incorrect type for '{original_name}' atom at index {i} ('{pretty_term}'){self._location_str(node)}: "
                    f"expected {expected_type} term, got {term_type}"
                )


class LoopyBadBreakFinder(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        self.visit(txn)

    def visit_Loop(self, node: logic_pb2.Loop, *args: Any):
        for instr_wrapper in node.init:
            if instr_wrapper.HasField("break"):
                brk = getattr(instr_wrapper, "break")
                original_name = self.get_original_name(brk.name)
                raise ValidationError(
                    f"Break rule found outside of body{self._location_str(brk)}: '{original_name}'"
                )


class LoopyBadGlobalFinder(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        self.globals: set[tuple[int, int]] = set()
        self.init: set[tuple[int, int]] = set()
        self.visit(txn)

    _ALGORITHM_INIT_TYPES = {"Assign", "Upsert", "MonoidDef", "MonusDef"}
    _LOOP_INSTR_TYPES = {"Break", "Assign", "Upsert"}

    def visit_Algorithm(self, node: logic_pb2.Algorithm, *args: Any):
        for rid in getattr(node, "global"):
            self.globals.add(relation_id_key(rid))
        for construct in node.body.constructs:
            inner = unwrap_construct(construct)
            if inner is None:
                continue
            inner_name = type(inner).__name__
            if inner_name == "Instruction":
                actual = unwrap_instruction(inner)  # type: ignore[arg-type]
                if (
                    actual is not None
                    and type(actual).__name__ in self._ALGORITHM_INIT_TYPES
                ):
                    self.init.add(relation_id_key(actual.name))  # type: ignore[union-attr]
            elif inner_name == "Loop":
                self.visit(inner)
        self.globals.clear()

    def visit_Loop(self, node: logic_pb2.Loop, *args: Any):
        for instr_wrapper in node.init:
            instr = unwrap_instruction(instr_wrapper)
            if instr is not None and type(instr).__name__ in self._LOOP_INSTR_TYPES:
                self.init.add(relation_id_key(instr.name))  # type: ignore[union-attr]
        for construct in node.body.constructs:
            inner = unwrap_construct(construct)
            if inner is None:
                continue
            inner_name = type(inner).__name__
            if inner_name == "Instruction":
                actual = unwrap_instruction(inner)  # type: ignore[arg-type]
                if (
                    actual is not None
                    and type(actual).__name__ in self._LOOP_INSTR_TYPES
                ):
                    key = relation_id_key(actual.name)  # type: ignore[union-attr]
                    if key in self.globals and key not in self.init:
                        original_name = self.get_original_name(actual.name)  # type: ignore[union-attr]
                        raise ValidationError(
                            f"Global rule found in body{self._location_str(actual)}: '{original_name}'"
                        )


class LoopyUpdatesShouldBeAtoms(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        self.visit(txn)

    def _check_atom_body(self, node: Message, instr_type_name: str):
        formula = node.body.value  # type: ignore[union-attr]
        which = formula.WhichOneof("formula_type")
        if which != "atom":
            raise ValidationError(
                f"{instr_type_name}{self._location_str(node)} must have an Atom as its value"
            )

    def visit_Upsert(self, node: logic_pb2.Upsert, *args: Any):
        self._check_atom_body(node, "Upsert")

    def visit_MonoidDef(self, node: logic_pb2.MonoidDef, *args: Any):
        self._check_atom_body(node, "MonoidDef")

    def visit_MonusDef(self, node: logic_pb2.MonusDef, *args: Any):
        self._check_atom_body(node, "MonusDef")


class CSVConfigChecker(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        global_defs = AtomTypeChecker.collect_global_defs(txn)
        self.relation_types: dict[tuple[int, int], list[str]] = {}
        for _, node in global_defs:
            rid = AtomTypeChecker.get_relation_id(node)
            key = relation_id_key(rid)
            sig = AtomTypeChecker.get_relation_sig(node)
            self.relation_types[key] = sig
        self.visit(txn)

    def visit_ExportCSVConfig(self, node: transactions_pb2.ExportCSVConfig, *args: Any):
        loc = self._location_str(node)
        if node.HasField("syntax_delim") and len(node.syntax_delim) != 1:
            raise ValidationError(
                f"CSV delimiter should be a single character{loc}, got '{node.syntax_delim}'"
            )
        if node.HasField("syntax_quotechar") and len(node.syntax_quotechar) != 1:
            raise ValidationError(
                f"CSV quotechar should be a single character{loc}, got '{node.syntax_quotechar}'"
            )
        if node.HasField("syntax_escapechar") and len(node.syntax_escapechar) != 1:
            raise ValidationError(
                f"CSV escapechar should be a single character{loc}, got '{node.syntax_escapechar}'"
            )

        valid_compressions = {"", "gzip"}
        if node.HasField("compression") and node.compression not in valid_compressions:
            raise ValidationError(
                f"CSV compression should be one of {valid_compressions}{loc}, got '{node.compression}'"
            )

        column_0_key_types: list[str] | None = None
        column_0_name: str | None = None
        for column in node.data_columns:
            key = relation_id_key(column.column_data)
            if key not in self.relation_types:
                continue

            column_types = self.relation_types[key]
            if len(column_types) < 1:
                raise ValidationError(
                    f"Data column relation must have at least one column{loc}, "
                    f"got zero columns in '{self.get_original_name(column.column_data)}'"
                )
            key_types = column_types[:-1]
            if column_0_key_types is None:
                column_0_key_types = key_types
                column_0_name = self.get_original_name(column.column_data)
            else:
                if column_0_key_types != key_types:
                    raise ValidationError(
                        f"All data columns in ExportCSVConfig{loc} must have the same key types. "
                        f"Got '{column_0_name}' with key types {[str(t) for t in column_0_key_types]} "
                        f"and '{self.get_original_name(column.column_data)}' with key types {[str(t) for t in key_types]}."
                    )


class FDVarsChecker(ProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction, **kwargs: Any):
        super().__init__(**kwargs)
        self.visit(txn)

    def visit_FunctionalDependency(
        self, node: logic_pb2.FunctionalDependency, *args: Any
    ):
        guard_var_names = {b.var.name for b in node.guard.vars}
        for var in node.keys:
            if var.name not in guard_var_names:
                raise ValidationError(
                    f"Key variable '{var.name}' not declared in guard{self._location_str(var)}"
                )
        for var in node.values:
            if var.name not in guard_var_names:
                raise ValidationError(
                    f"Value variable '{var.name}' not declared in guard{self._location_str(var)}"
                )


# --- Entry point ---


_VALIDATORS: list[tuple[str, Any]] = [
    ("shadowed variable check", ShadowedVariableFinder),
    ("unused variable check", UnusedVariableVisitor),
    ("duplicate relation ID check", DuplicateRelationIdFinder),
    ("duplicate fragment check", DuplicateFragmentDefinitionFinder),
    ("atom type check", AtomTypeChecker),
    ("loop break check", LoopyBadBreakFinder),
    ("loop global check", LoopyBadGlobalFinder),
    ("loop update check", LoopyUpdatesShouldBeAtoms),
    ("CSV config check", CSVConfigChecker),
    ("FD variable check", FDVarsChecker),
]


def validate_proto(
    txn: transactions_pb2.Transaction,
    provenance: dict[int, Any] | None = None,
    filename: str | None = None,
) -> None:
    """Validate a protobuf Transaction message.

    If provenance and filename are provided, error messages will include
    source locations (e.g. 'at file.lqp:10:5').
    """
    kwargs: dict[str, Any] = {}
    if provenance is not None:
        kwargs["provenance"] = _build_node_spans(txn, provenance)
    if filename is not None:
        kwargs["filename"] = filename
    for name, validator_cls in _VALIDATORS:
        try:
            validator_cls(txn, **kwargs)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"{name}: {e}") from e
