import lqp.ir as ir
import lqp.print as p
from typing import Any, Dict, List, Tuple, Sequence, Set, Union, Optional
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
                # Allow an escape hatch for internal variables.
                if var_name.startswith("_"):
                    continue
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

# Checks for invalid duplicate RelationIds. Duplicate relation IDs are only valid
# when they are within the same fragment in different epochs.
# Raises ValidationError upon encountering such.
class DuplicateRelationIdFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        # RelationIds and where they have been defined. The integer represents
        # the epoch.
        self.seen_ids: Dict[ir.RelationId, Tuple[int, ir.FragmentId]] = dict()
        # We'll use this to give IDs to epochs as we visit them.
        self.curr_epoch: int = 0
        self.curr_fragment: Optional[ir.FragmentId] = None

        self.visit(txn)

    def visit_Def(self, node: ir.Def, *args: Any) -> None:
        assert self.curr_fragment is not None
        assert self.curr_epoch > 0

        if node.name in self.seen_ids:
            seen_in_epoch, seen_in_fragment = self.seen_ids[node.name]
            if self.curr_fragment != seen_in_fragment:
                # Dup ID, different fragments, same or different epoch.
                raise ValidationError(
                    f"Duplicate declaration across fragments at {node.meta}: '{node.name.id}'"
                )
            elif self.curr_epoch == seen_in_epoch:
                # Dup ID, same fragment, same epoch.
                raise ValidationError(
                    f"Duplicate declaration within fragment in epoch at {node.meta}: '{node.name.id}'"
                )
            # else: the final case (dup ID, same fragment, different epoch) is valid.

        self.seen_ids[node.name] = (self.curr_epoch, self.curr_fragment)

    def visit_Fragment(self, node: ir.Fragment, *args: Any) -> None:
        self.curr_fragment = node.id
        self.generic_visit(node, args)

    def visit_Epoch(self, node: ir.Epoch, *args: Any) -> None:
        self.curr_epoch += 1
        self.generic_visit(node, args)

    def visit_Algorithm(self, node: ir.Algorithm, *args: Any) -> None:
        # Only the Defs in init are globally visible so don't visit body Defs.
        for d in node.global_:
            if d in self.seen_ids:
                raise ValidationError(
                    f"Duplicate declaration at {d.meta}: '{d.id}'"
                )
            else:
                assert self.curr_fragment is not None
                self.seen_ids[d] = (self.curr_epoch, self.curr_fragment)

# Checks that Instructions are applied to the correct number and types of terms.
# Assumes UnusedVariableVisitor has passed.
class AtomTypeChecker(LqpVisitor):
    Instructions = Union[ir.Def, ir.Assign, ir.Break, ir.Upsert]
    # Helper to get all Defs defined in a Transaction. We are only interested
    # in globally visible Defs thus ignore Loop bodies.
    @staticmethod
    def collect_global_defs(txn: ir.Transaction) -> List[Instructions]:
        # Visitor to do the work.
        class DefCollector(LqpVisitor):
            def __init__(self, txn: ir.Transaction):
                self.atoms: List[AtomTypeChecker.Instructions] = []
                self.visit(txn)

            def visit_Def(self, node: ir.Def) -> None:
                self.atoms.append(node)

            def visit_Algorithm(self, node:ir.Algorithm):
                self.atoms.extend([d for d in node.body.constructs if isinstance(d, AtomTypeChecker.Instructions)])

            def visit_Loop(self, node: ir.Loop) -> None:
                self.atoms.extend([d for d in node.init if isinstance(d, AtomTypeChecker.Instructions)])
                # Don't touch the body, they are not globally visible. Treat
                # this node as a leaf.
        return DefCollector(txn).atoms

    # Helper to map Constants to their TypeName.
    @staticmethod
    def constant_type(c: ir.Value) -> ir.TypeName: # type: ignore
        if isinstance(c.value, str):
            return ir.TypeName.STRING
        elif isinstance(c.value, int):
            return ir.TypeName.INT
        elif isinstance(c.value, float):
            return ir.TypeName.FLOAT
        elif isinstance(c.value, ir.Int128Value):
            return ir.TypeName.INT128
        elif isinstance(c.value, ir.UInt128Value):
            return ir.TypeName.UINT128
        elif isinstance(c.value, ir.MissingValue):
            return ir.TypeName.MISSING
        elif isinstance(c.value, ir.DecimalValue):
            return ir.TypeName.DECIMAL
        elif isinstance(c.value, ir.DateValue):
            return ir.TypeName.DATE
        elif isinstance(c.value, ir.DateTimeValue):
            return ir.TypeName.DATETIME
        elif isinstance(c.value, ir.BooleanValue):
            return ir.TypeName.BOOLEAN
        else:
            assert False, f"Unknown constant type: {type(c.value)}"

    @staticmethod
    def type_error_message(atom: ir.Atom, index: int, expected: ir.TypeName, actual: ir.TypeName) -> str:
        term = atom.terms[index]
        pretty_term = p.to_str(term, 0)
        return \
            f"Incorrect type for '{atom.name.id}' atom at index {index} ('{pretty_term}') at {atom.meta}: " +\
            f"expected {expected} term, got {actual}"

    # Return a list of the types of the parameters of a Def.
    @staticmethod
    def get_relation_sig(d: Instructions):
        # v[1] holds the TypeName.
        return [v[1].type_name for v in d.body.vars]

    # The varargs passed be a State or nothing at all.
    @staticmethod
    def args_ok(args: tuple[Any]) -> bool:
        return len(args) == 1 and isinstance(args[0], AtomTypeChecker.State)

    # What we pass around to the visit methods.
    @dataclass(frozen=True)
    class State:
        # Maps relations in scope to their types.
        relation_types: Dict[ir.RelationId, List[ir.TypeName]]
        # Maps variables in scope to their type.
        var_types: Dict[str, ir.TypeName]

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
                state.var_types | {v.name : t.type_name for (v, t) in node.vars},
            ),
        )

    # Visit Loops as body Defs are not global and need to be introduced to their
    # children.
    def visit_Loop(self, node: ir.Loop, *args: Any) -> None:
        assert AtomTypeChecker.args_ok(args)
        state = args[0]

        for d in node.init:
            self.visit(d, state)

        for decl in node.body.constructs:
            if isinstance(decl, ir.Instruction):
                self.visit(
                    decl,
                    AtomTypeChecker.State(
                        {decl.name : AtomTypeChecker.get_relation_sig(decl)} | state.relation_types, #type: ignore
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
                if term_type.value != relation_type.value:
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


# Loopy contract: Break rules can only go in inits
class LoopyBadBreakFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        self.visit(txn)

    def visit_Loop(self, node: ir.Loop, *args: Any) -> None:
        for i in node.init:
            if isinstance(i, ir.Break):
                raise ValidationError(
                    f"Break rule found outside of body at {i.meta}: '{i.name.id}'"
                )

# Loopy contract: Algorithm globals cannot be in loop body unless they were already in init
class LoopyBadGlobalFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        self.globals: Set[ir.RelationId] = set()
        self.init: Set[ir.RelationId] = set()
        self.visit(txn)

    def visit_Algorithm(self, node: ir.Algorithm, *args: Any) -> None:
        self.globals = self.globals.union(node.global_)
        self.visit(node.body)
        self.globals.clear()

    def visit_Loop(self, node: ir.Loop, *args: Any) -> None:
        self.init = {x.name for x in node.init if isinstance(x, (ir.Break, ir.Assign, ir.Upsert))}
        for i in node.body.constructs:
            if isinstance(i, (ir.Break, ir.Assign, ir.Upsert)):
                if (i.name in self.globals) and (i.name not in self.init):
                    raise ValidationError(
                        f"Global rule found in body at {i.meta}: '{i.name.id}'"
                    )

class LoopyUpdatesShouldBeAtoms(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        self.generic_visit(txn)

    def visit_instruction_with_atom_body(self, node: Any, *args: Any) -> None:
        if not isinstance(node.body.value, ir.Atom):
            instruction_type = node.__class__.__name__
            raise ValidationError(f"{instruction_type} at {node.meta} must have an Atom as its value")

    visit_Copy = visit_MonoidDef = visit_MonusDef = visit_Upsert = visit_instruction_with_atom_body

def validate_lqp(lqp: ir.Transaction):
    ShadowedVariableFinder(lqp)
    UnusedVariableVisitor(lqp)
    DuplicateRelationIdFinder(lqp)
    DuplicateFragmentDefinitionFinder(lqp)
    AtomTypeChecker(lqp)
    LoopyBadBreakFinder(lqp)
    LoopyBadGlobalFinder(lqp)
    LoopyUpdatesShouldBeAtoms(lqp)
