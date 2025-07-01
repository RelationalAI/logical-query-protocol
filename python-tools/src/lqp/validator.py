import lqp.ir as ir
import lqp.print as p
from typing import Any, Dict, List, Tuple, Sequence, Set
from dataclasses import dataclass, is_dataclass, fields

class ValidationError(Exception):
    pass

class LqpVisitor:
    def visit(self, node: ir.LqpNode, *args: Any) -> None:
        method_name = f'visit_{node.__class__.__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node, *args)

    def generic_visit(self, node: ir.LqpNode, *args: Any) -> None:
        if not is_dataclass(node):
            raise ValidationError(f"Expected dataclass, got {type(node)}")
        for field in fields(node):
            value = getattr(node, field.name)
            if isinstance(value, ir.LqpNode):
                self.visit(value, *args)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, ir.LqpNode):
                        self.visit(item, *args)
            elif isinstance(value, dict):
                for item in value.values():
                    if isinstance(item, ir.LqpNode):
                        self.visit(item, *args)

class UnusedVariableVisitor(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        self.scopes: List[Tuple[Set[str], Set[str]]] = []
        self.visit(txn)

    def _declare_var(self, var_name: str):
        if self.scopes:
            self.scopes[-1][0].add(var_name)

    def _mark_var_used(self, var: ir.Var):
        for declared, used in reversed(self.scopes):
            if var.name in declared:
                used.add(var.name)
                return
        raise ValidationError(f"Undeclared variable used at {var.meta}: '{var.name}'")

    def visit_Abstraction(self, node: ir.Abstraction):
        self.scopes.append((set(), set()))
        for var in node.vars:
            self._declare_var(var[0].name)
        self.visit(node.value)
        declared, used = self.scopes.pop()
        unused = declared - used
        if unused:
            for var_name in unused:
                raise ValidationError(f"Unused variable declared: '{var_name}'")

    def visit_Var(self, node: ir.Var, *args: Any):
        self._mark_var_used(node)

# Checks for shadowing of variables. Raises ValidationError upon encountering such.
class ShadowedVariableFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        self.visit(txn)

    # The varargs passed in must be a single set of strings.
    @staticmethod
    def args_ok(args: Sequence[Any]) -> bool:
        return (
            len(args) == 0 or
            (
                len(args) == 1 and
                isinstance(args[0], Set) and
                all(isinstance(s, str) for s in args[0])
            )
        )

    # Only Abstractions introduce variables.
    def visit_Abstraction(self, node: ir.Abstraction, *args: Any) -> None:
        assert ShadowedVariableFinder.args_ok(args)
        in_scope_names = set() if len(args) == 0 else args[0]

        for v in node.vars:
            var = v[0]
            if var.name in in_scope_names:
                raise ValidationError(f"Shadowed variable at {var.meta}: '{var.name}'")

        self.visit(node.value, in_scope_names | set(v[0].name for v in node.vars))

# Checks for duplicate RelationIds.
# Raises ValidationError upon encountering such.
class DuplicateRelationIdFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        self.seen_ids: ir.RelationId = set()
        self.visit(txn)

    def visit_Def(self, node: ir.Def, *args: Any) -> None:
        if node.name in self.seen_ids:
            raise ValidationError(
                f"Duplicate declaration at {node.meta}: '{node.name.id}'"
            )
        else:
            self.seen_ids.add(node.name)

    def visit_Loop(self, node: ir.Loop, *args: Any) -> None:
        # Only the Defs in init are globally visible so don't visit body Defs.
        # TODO: add test for non-/duplicates associated with loops.
        for d in node.init:
            self.visit(d)

# Checks that Atoms are applied to the correct number and types of terms.
# Assumes UnusedVariableVisitor has passed.
class AtomTypeChecker(LqpVisitor):
    # Helper to get all Defs defined in a Transaction. We are only interested
    # in globally visible Defs thus ignore Loop bodies.
    @staticmethod
    def collect_global_defs(txn: ir.Transaction) -> List[ir.Def]:
        # Visitor to do the work.
        class DefCollector(LqpVisitor):
            def __init__(self, txn: ir.Transaction):
                self.defs: List[ir.Def] = []
                self.visit(txn)


            def visit_Def(self, node: ir.Def) -> None:
                self.defs.append(node)

            def visit_Loop(self, node: ir.Def) -> None:
                self.defs.extend(node.init)
                # Don't touch the body, they are not globally visible. Treat
                # this node as a leaf.

        return DefCollector(txn).defs

    # Helper to map Constants to their RelType.
    @staticmethod
    def constant_type(c: ir.Constant) -> ir.RelType:
        if isinstance(c, str):
            return ir.PrimitiveType.STRING
        elif isinstance(c, int):
            return ir.PrimitiveType.INT
        elif isinstance(c, float):
            return ir.PrimitiveType.FLOAT
        elif isinstance(c, ir.UInt128):
            return ir.PrimitiveType.UINT128
        else:
            assert False

    @staticmethod
    def type_error_message(atom: ir.Atom, index: int, expected: ir.RelType, actual: ir.RelType) -> str:
        term = atom.terms[index]
        pretty_term = p.to_str(term, 0)
        return \
            f"Incorrect type for '{atom.name.id}' atom at index {index} ('{pretty_term}') at {atom.meta}: " +\
            f"expected {expected} term, got {actual}"

    # Return a list of the types of the parameters of a Def.
    @staticmethod
    def get_relation_sig(d: ir.Def):
        # v[1] holds the RelType.
        return [v[1] for v in d.body.vars]

    # The varargs passed be a State or nothing at all.
    @staticmethod
    def args_ok(args: List[Any]) -> bool:
        return len(args) == 1 and isinstance(args[0], AtomTypeChecker.State)

    # What we pass around to the visit methods.
    @dataclass(frozen=True)
    class State:
        # Maps relations in scope to their types.
        relation_types: Dict[ir.RelationId, List[ir.RelType]]
        # Maps variables in scope to their type.
        var_types: Dict[str, ir.RelType]

    def __init__(self, txn: ir.Transaction):
        state = AtomTypeChecker.State(
            {
                d.name : AtomTypeChecker.get_relation_sig(d)
                for d in AtomTypeChecker.collect_global_defs(txn)
            },
            # No variables declared yet.
            {},
        )
        self.visit(txn, state)

    # Visit Abstractions to collect the types of variables.
    def visit_Abstraction(self, node: ir.Abstraction, *args: Any) -> None:
        assert AtomTypeChecker.args_ok(args)
        state = args[0]

        self.generic_visit(
            node,
            AtomTypeChecker.State(
                state.relation_types,
                state.var_types | {v.name : t for (v, t) in node.vars},
            ),
        )

    # Visit Loops as body Defs are not global and need to be introduced to their
    # children.
    def visit_Loop(self, node: ir.Loop, *args: Any) -> None:
        assert AtomTypeChecker.args_ok(args)
        state = args[0]

        for d in node.init:
            self.visit(d, state)

        for decl in node.body:
            if isinstance(decl, ir.Def):
                self.visit(
                    decl,
                    AtomTypeChecker.State(
                        {decl.name : get_relation_sig(decl)} | state.relation_types,
                        state.var_types,
                    ),
                )
            else:
                self.visit(decl, state)

    def visit_Atom(self, node: ir.Atom, *args: Any) -> None:
        assert AtomTypeChecker.args_ok(args)
        state = args[0]

        # Relation may have been defined in another transaction, we don't know,
        # so ignore this atom.
        if node.name in state.relation_types:
            relation_type_sig = state.relation_types[node.name]

            # Check arity.
            atom_arity = len(node.terms)
            relation_arity = len(relation_type_sig)
            if atom_arity != relation_arity:
                raise ValidationError(
                    f"Incorrect arity for '{node.name.id}' atom at {node.meta}: " +\
                    f"expected {relation_arity} term{'' if relation_arity == 1 else 's'}, got {atom_arity}"
                )

            # Check types.
            for (i, (term, relation_type)) in enumerate(zip(node.terms, relation_type_sig)):
                # var_types[term] is okay because we assume UnusedVariableVisitor.
                term_type = state.var_types[term.name] if isinstance(term, ir.Var) else AtomTypeChecker.constant_type(term)
                if term_type != relation_type:
                    raise ValidationError(
                        AtomTypeChecker.type_error_message(node, i, relation_type, term_type)
                    )

        # This is a leaf for our purposes, no need to recurse further.

# Checks for the definition (Define) of duplicate Fragment(Ids) within an Epoch.
# Raises ValidationError upon encountering such.
class DuplicateFragmentDefinitionFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        # Instead of passing this back and forth, we are going to clear this
        # when we visit an Epoch and let it fill, checking for duplicates
        # when we visit descendent Fragments. When we visit another Epoch, it'll
        # be cleared again, etc.
        self.seen_ids: Set[ir.FragmentId] = set()
        self.visit(txn)

    def visit_Epoch(self, node: ir.Epoch, *args: Any) -> None:
        self.seen_ids.clear()
        self.generic_visit(node)

    # We could visit_Fragment instead (no node has a Fragment child except
    # Define) but the point of this pass is to find duplicate Fragments
    # being _defined_ so this is a bit more fitting.
    def visit_Define(self, node: ir.Define, *args: Any) -> None:
        if node.fragment.id in self.seen_ids:
            id_str = node.fragment.id.id.decode("utf-8")
            raise ValidationError(
                f"Duplicate fragment within an epoch at {node.meta}: '{id_str}'"
            )
        else:
            self.seen_ids.add(node.fragment.id)

        # No need to recurse further; no descendent Epochs/Fragments.

def validate_lqp(lqp: ir.Transaction):
    ShadowedVariableFinder(lqp)
    UnusedVariableVisitor(lqp)
    DuplicateRelationIdFinder(lqp)
    DuplicateFragmentDefinitionFinder(lqp)
    AtomTypeChecker(lqp)
