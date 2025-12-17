from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Sequence, Set, Union, Optional

from lqp.proto.v1 import (
    fragments_pb2,
    logic_pb2,
    transactions_pb2,
)

class ValidationError(Exception):
    pass

class LqpProtoVisitor:
    def __init__(self):
        self._method_cache = {}

    def visit(self, node: Any, *args: Any) -> None:
        if not hasattr(node, "DESCRIPTOR"):
            return

        node_class = node.__class__
        if node_class not in self._method_cache:
            method_name = f'visit_{node_class.__name__}'
            self._method_cache[node_class] = getattr(self, method_name, self.generic_visit)

        visitor_method = self._method_cache[node_class]
        return visitor_method(node, *args)

    def generic_visit(self, node: Any, *args: Any) -> None:
        if not hasattr(node, "DESCRIPTOR"):
            return

        visited_oneofs = set()
        for field_descriptor in node.DESCRIPTOR.fields:
            if field_descriptor.containing_oneof:
                oneof_name = field_descriptor.containing_oneof.name
                if oneof_name in visited_oneofs:
                    continue
                visited_oneofs.add(oneof_name)

                field_name = node.WhichOneof(oneof_name)
                if field_name:
                    value = getattr(node, field_name)
                    self.visit(value, *args)
            elif field_descriptor.label == field_descriptor.LABEL_REPEATED:
                for item in getattr(node, field_descriptor.name):
                    self.visit(item, *args)
            elif field_descriptor.type == field_descriptor.TYPE_MESSAGE:
                 self.visit(getattr(node, field_descriptor.name), *args)


def validate_lqp_proto(txn: transactions_pb2.Transaction):
    """
    Validates a raw LQP protobuf transaction.
    """
    ShadowedVariableFinderProto(txn)
    UnusedVariableVisitorProto(txn)
    DuplicateRelationIdFinderProto(txn)
    DuplicateFragmentDefinitionFinderProto(txn)
    AtomTypeCheckerProto(txn)
    LoopyBadBreakFinderProto(txn)
    LoopyBadGlobalFinderProto(txn)
    LoopyUpdatesShouldBeAtomsProto(txn)
    CSVConfigCheckerProto(txn)
    FDVarsCheckerProto(txn)

class UnusedVariableVisitorProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        self.scopes: List[Tuple[Set[str], Set[str]]] = []
        self.visit(txn)

    def _declare_var(self, var_name: str):
        if self.scopes:
            self.scopes[-1][0].add(var_name)

    def _mark_var_used(self, var: logic_pb2.Var):
        for declared, used in reversed(self.scopes):
            if var.name in declared:
                used.add(var.name)
                return
        raise ValidationError(f"Undeclared variable used: '{var.name}'")

    def visit_Abstraction(self, node: logic_pb2.Abstraction, *args: Any):
        self.scopes.append((set(), set()))
        for var_binding in node.vars:
            self._declare_var(var_binding.var.name)
        self.visit(node.value)
        declared, used = self.scopes.pop()
        unused = declared - used
        if unused:
            for var_name in unused:
                # Allow an escape hatch for internal variables.
                if var_name.startswith("_"):
                    continue
                raise ValidationError(f"Unused variable declared: '{var_name}'")

    def visit_Var(self, node: logic_pb2.Var, *args: Any):
        self._mark_var_used(node)

    def visit_FunctionalDependency(self, node: logic_pb2.FunctionalDependency, *args: Any):
        self.visit(node.guard)

# Checks for shadowing of variables. Raises ValidationError upon encountering such.
class ShadowedVariableFinderProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        self.visit(txn, set())

    # The varargs passed in must be a single set of strings.
    @staticmethod
    def args_ok(args: Sequence[Any]) -> bool:
        return (
            len(args) == 0 or
            (
                len(args) == 1 and
                isinstance(args[0], set) and
                all(isinstance(s, str) for s in args[0])
            )
        )

    # Only Abstractions introduce variables.
    def visit_Abstraction(self, node: logic_pb2.Abstraction, *args: Any) -> None:
        assert ShadowedVariableFinderProto.args_ok(args)
        in_scope_names = set() if len(args) == 0 else args[0]

        new_scope = set()
        for v in node.vars:
            var = v.var
            if var.name in in_scope_names:
                raise ValidationError(f"Shadowed variable: '{var.name}'")
            new_scope.add(var.name)

        self.visit(node.value, in_scope_names | new_scope)

# Checks for invalid duplicate RelationIds. Duplicate relation IDs are only valid
# when they are within the same fragment in different epochs.
# Raises ValidationError upon encountering such.
class DuplicateRelationIdFinderProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        # RelationIds and where they have been defined. The integer represents
        # the epoch.
        self.seen_ids: Dict[Tuple[int, int], Tuple[int, bytes]] = dict()
        # We'll use this to give IDs to epochs as we visit them.
        self.curr_epoch: int = 0
        self.curr_fragment: Optional[bytes] = None

        self.visit(txn)

    def visit_Def(self, node: logic_pb2.Def, *args: Any) -> None:
        assert self.curr_fragment is not None
        assert self.curr_epoch > 0

        rel_id = (node.name.id_low, node.name.id_high)

        if rel_id in self.seen_ids:
            seen_in_epoch, seen_in_fragment = self.seen_ids[rel_id]
            if self.curr_fragment != seen_in_fragment:
                # Dup ID, different fragments, same or different epoch.
                raise ValidationError(
                    f"Duplicate declaration across fragments: '{rel_id}'"
                )
            elif self.curr_epoch == seen_in_epoch:
                # Dup ID, same fragment, same epoch.
                raise ValidationError(
                    f"Duplicate declaration within fragment in epoch: '{rel_id}'"
                )
            # else: the final case (dup ID, same fragment, different epoch) is valid.

        self.seen_ids[rel_id] = (self.curr_epoch, self.curr_fragment)

    def visit_Assign(self, node: logic_pb2.Assign, *args: Any) -> None:
        assert self.curr_fragment is not None
        assert self.curr_epoch > 0

        rel_id = (node.name.id_low, node.name.id_high)
        self.seen_ids[rel_id] = (self.curr_epoch, self.curr_fragment)

    def visit_Fragment(self, node: fragments_pb2.Fragment, *args: Any) -> None:
        self.curr_fragment = node.id.id
        self.generic_visit(node, *args)

    def visit_Epoch(self, node: transactions_pb2.Epoch, *args: Any) -> None:
        self.curr_epoch += 1
        self.generic_visit(node, *args)

    def visit_Algorithm(self, node: logic_pb2.Algorithm, *args: Any) -> None:
        # Only the Defs in init are globally visible so don't visit body Defs.
        for d in getattr(node, 'global'):
            rel_id = (d.id_low, d.id_high)
            if rel_id in self.seen_ids:
                raise ValidationError(
                    f"Duplicate declaration: '{rel_id}'"
                )
            else:
                assert self.curr_fragment is not None
                self.seen_ids[rel_id] = (self.curr_epoch, self.curr_fragment)

# Checks for the definition (Define) of duplicate Fragment(Ids) within an Epoch.
# Raises ValidationError upon encountering such.
class DuplicateFragmentDefinitionFinderProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        # Instead of passing this back and forth, we are going to clear this
        # when we visit an Epoch and let it fill, checking for duplicates
        # when we visit descendent Fragments. When we visit another Epoch, it'll
        # be cleared again, etc.
        self.seen_ids: Set[bytes] = set()
        self.visit(txn)

    def visit_Epoch(self, node: transactions_pb2.Epoch, *args: Any) -> None:
        self.seen_ids.clear()
        self.generic_visit(node, *args)

    # We could visit_Fragment instead (no node has a Fragment child except
    # Define) but the point of this pass is to find duplicate Fragments
    # being _defined_ so this is a bit more fitting.
    def visit_Define(self, node: transactions_pb2.Define, *args: Any) -> None:
        if node.fragment.id.id in self.seen_ids:
            id_str = node.fragment.id.id.decode("utf-8")
            raise ValidationError(
                f"Duplicate fragment within an epoch: '{id_str}'"
            )
        else:
            self.seen_ids.add(node.fragment.id.id)
        self.generic_visit(node, *args)

# Checks that Instructions are applied to the correct number and types of terms.
# Assumes UnusedVariableVisitor has passed.
class AtomTypeCheckerProto(LqpProtoVisitor):
    Instructions = Union[logic_pb2.Def, logic_pb2.Assign, logic_pb2.Break, logic_pb2.Upsert]
    # Helper to get all Defs defined in a Transaction. We are only interested
    # in globally visible Defs thus ignore Loop bodies.
    @staticmethod
    def collect_global_defs(txn: transactions_pb2.Transaction) -> List[AtomTypeCheckerProto.Instructions]:
        # Visitor to do the work.
        class DefCollector(LqpProtoVisitor):
            def __init__(self, txn: transactions_pb2.Transaction):
                super().__init__()
                self.atoms: List[AtomTypeCheckerProto.Instructions] = []
                self.visit(txn)

            def visit_Def(self, node: logic_pb2.Def) -> None:
                self.atoms.append(node)

            def visit_Algorithm(self, node:logic_pb2.Algorithm):
                for c in node.body.constructs:
                    instr = getattr(c, c.WhichOneof("construct_type"))
                    if hasattr(instr, "instr_type"):
                        self.atoms.append(getattr(instr, instr.WhichOneof("instr_type")))

            def visit_Loop(self, node: logic_pb2.Loop) -> None:
                for i in node.init:
                    self.atoms.append(getattr(i, i.WhichOneof("instr_type")))
                # Don't touch the body, they are not globally visible. Treat
                # this node as a leaf.
        return DefCollector(txn).atoms

    # Helper to map Constants to their TypeName.
    @staticmethod
    def constant_type(c: logic_pb2.Value) -> str: # type: ignore
        return c.WhichOneof("value")

    @staticmethod
    def type_error_message(atom: logic_pb2.Atom, original_name, index: int, expected: str, actual: str) -> str:
        return \
            f"Incorrect type for '{original_name}' atom at index {index}: " +\
            f"expected {expected} term, got {actual}"

    # Return a list of the types of the parameters of a Def.
    @staticmethod
    def get_relation_sig(d: AtomTypeCheckerProto.Instructions):
        # v[1] holds the TypeName.
        return [v.type.WhichOneof("type") for v in d.body.vars]

    # The varargs passed be a State or nothing at all.
    @staticmethod
    def args_ok(args: tuple[Any]) -> bool:
        return len(args) == 1 and isinstance(args[0], AtomTypeCheckerProto.State)

    # What we pass around to the visit methods.
    @dataclass(frozen=True)
    class State:
        # Maps relations in scope to their types.
        relation_types: Dict[Tuple[int, int], List[str]]
        # Maps variables in scope to their type.
        var_types: Dict[str, str]

    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        relation_types: Dict[Tuple[int, int], List[str]] = {
            (d.name.id_low, d.name.id_high) : AtomTypeCheckerProto.get_relation_sig(d)
            for d in AtomTypeCheckerProto.collect_global_defs(txn)
        }
        state = AtomTypeCheckerProto.State(
            relation_types,
            # No variables declared yet.
            {},
        )
        self.visit(txn, state)

    # Visit Abstractions to collect the types of variables.
    def visit_Abstraction(self, node: logic_pb2.Abstraction, *args: Any) -> None:
        assert AtomTypeCheckerProto.args_ok(args)
        state = args[0]

        self.generic_visit(
            node,
            AtomTypeCheckerProto.State(
                state.relation_types,
                state.var_types | {v.var.name : v.type.WhichOneof("type") for v in node.vars},
            ),
        )

    def visit_Loop(self, node: logic_pb2.Loop, *args: Any) -> None:
        assert AtomTypeCheckerProto.args_ok(args)
        state = args[0]

        for d in node.init:
            self.visit(d, state)

        for decl in node.body.constructs:
            instr = getattr(decl, decl.WhichOneof("construct_type"))
            if hasattr(instr, "instr_type"):
                actual_instr = getattr(instr, instr.WhichOneof("instr_type"))
                self.visit(
                    actual_instr,
                    AtomTypeCheckerProto.State(
                        {(actual_instr.name.id_low, actual_instr.name.id_high) : AtomTypeCheckerProto.get_relation_sig(actual_instr)} | state.relation_types, #type: ignore
                        state.var_types,
                    ),
                )
            else:
                self.visit(decl, state)

    def visit_Atom(self, node: logic_pb2.Atom, *args: Any) -> None:
        assert AtomTypeCheckerProto.args_ok(args)
        state = args[0]

        rel_id = (node.name.id_low, node.name.id_high)
        # Relation may have been defined in another transaction, we don't know,
        # so ignore this atom.
        if rel_id in state.relation_types:
            relation_type_sig = state.relation_types[rel_id]

            # Check arity.
            atom_arity = len(node.terms)
            relation_arity = len(relation_type_sig)
            if atom_arity != relation_arity:
                raise ValidationError(
                    f"Incorrect arity for '{rel_id}' atom: " +\
                    f"expected {relation_arity} term{'' if relation_arity == 1 else 's'}, got {atom_arity}"
                )

            # Check types.
            for (i, (term, relation_type)) in enumerate(zip(node.terms, relation_type_sig)):
                # var_types[term] is okay because we assume UnusedVariableVisitor.
                term_type_name = term.WhichOneof("term_type")
                term_val = getattr(term, term_type_name)

                term_type = state.var_types[term_val.name] if term_type_name == "var" else AtomTypeCheckerProto.constant_type(term_val)
                if term_type != relation_type:
                    raise ValidationError(
                        AtomTypeCheckerProto.type_error_message(node, rel_id, i, relation_type, term_type)
                    )

# Loopy contract: Break rules can only go in inits
class LoopyBadBreakFinderProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        self.visit(txn)

    def visit_Loop(self, node: logic_pb2.Loop, *args: Any) -> None:
        for i in node.init:
            if i.WhichOneof("instr_type") == "break":
                raise ValidationError(
                    f"Break rule found outside of body"
                )

# Loopy contract: Algorithm globals cannot be in loop body unless they were already in init
class LoopyBadGlobalFinderProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        self.globals: Set[Tuple[int, int]] = set()
        self.init: Set[Tuple[int, int]] = set()
        self.visit(txn)

    def visit_Algorithm(self, node: logic_pb2.Algorithm, *args: Any) -> None:
        self.globals = self.globals.union({(d.id_low, d.id_high) for d in getattr(node, 'global')})
        self.visit(node.body)
        self.globals.clear()

    def visit_Loop(self, node: logic_pb2.Loop, *args: Any) -> None:
        self.init = set()
        for x in node.init:
            instr = getattr(x, x.WhichOneof("instr_type"))
            self.init.add((instr.name.id_low, instr.name.id_high))

        for i in node.body.constructs:
            construct = getattr(i, i.WhichOneof("construct_type"))
            if isinstance(construct, logic_pb2.Instruction):
                instr = getattr(construct, construct.WhichOneof("instr_type"))
                rel_id = (instr.name.id_low, instr.name.id_high)
                if (rel_id in self.globals) and (rel_id not in self.init):
                    raise ValidationError(
                        f"Global rule found in body: '{rel_id}'"
                    )

class LoopyUpdatesShouldBeAtomsProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        self.visit(txn)

    def visit_instruction_with_atom_body(self, node: Any, *args: Any) -> None:
        if node.body.value.WhichOneof("formula_type") != "atom":
            instruction_type = node.__class__.__name__
            raise ValidationError(f"{instruction_type} must have an Atom as its value")

    visit_MonoidDef = visit_MonusDef = visit_Upsert = visit_instruction_with_atom_body

class CSVConfigCheckerProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        global_defs = AtomTypeCheckerProto.collect_global_defs(txn)
        self.relation_types: Dict[Tuple[int, int], List[str]] = {
            (d.name.id_low, d.name.id_high) : AtomTypeCheckerProto.get_relation_sig(d)
            for d in global_defs
        }
        self.visit(txn)

    def visit_ExportCSVConfig(self, node: transactions_pb2.ExportCSVConfig, *args: Any) -> None:
        if node.syntax_delim is not None and len(node.syntax_delim) != 1:
            raise ValidationError(f"CSV delimiter should be a single character, got '{node.syntax_delim}'")
        if node.syntax_quotechar is not None and len(node.syntax_quotechar) != 1:
            raise ValidationError(f"CSV quotechar should be a single character, got '{node.syntax_quotechar}'")
        if node.syntax_escapechar is not None and len(node.syntax_escapechar) != 1:
            raise ValidationError(f"CSV escapechar should be a single character, got '{node.syntax_escapechar}'")

        # Check compression is valid
        valid_compressions = {'', 'gzip'}
        if node.compression is not None and node.compression not in valid_compressions:
            raise ValidationError(f"CSV compression should be one of {valid_compressions}, got '{node.compression}'")

        # Check that the column relations have the same key types
        column_0_key_types = None
        column_0_relation_id = None
        for column in node.data_columns:
            # If the column relation is not defined in this transaction, we can't check it.
            col_rel_id: Tuple[int, int] = (column.column_data.id_low, column.column_data.id_high)
            if col_rel_id not in self.relation_types:
                continue

            column_types: List[str] = self.relation_types[col_rel_id]
            if len(column_types) < 1:
                raise ValidationError(f"Data column relation must have at least one column, got zero columns in '{col_rel_id}'")
            key_types = column_types[:-1]
            if column_0_key_types is None:
                column_0_key_types = key_types
                column_0_relation_id = col_rel_id
            else:
                assert column_0_key_types is not None
                assert column_0_relation_id is not None
                if column_0_key_types != key_types:
                    raise ValidationError(
                        f"All data columns in ExportCSVConfig must have the same key types. " +\
                        f"Got '{column_0_relation_id}' with key types {[str(t) for t in column_0_key_types]} " +\
                        f"and '{col_rel_id}' with key types {[str(t) for t in key_types]}."
                    )

# Checks that the variables used in an FD are drawn from free variables of the guard.
class FDVarsCheckerProto(LqpProtoVisitor):
    def __init__(self, txn: transactions_pb2.Transaction):
        super().__init__()
        self.visit(txn)

    def visit_FunctionalDependency(self, node: logic_pb2.FunctionalDependency):
        guard_var_names = {var.var.name for var in node.guard.vars}
        for var in node.keys:
            if var.name not in guard_var_names:
                raise ValidationError(f"Key variable '{var.name}' not declared in guard")
        for var in node.values:
            if var.name not in guard_var_names:
                raise ValidationError(f"Value variable '{var.name}' not declared in guard")
