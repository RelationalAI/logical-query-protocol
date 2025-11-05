import lqp.ir as ir
import lqp.print as p
from typing import Any, Dict, List, Tuple, Sequence, Set, Union, Optional
from dataclasses import dataclass, is_dataclass, fields

class ValidationError(Exception):
    pass

class LqpVisitor:
    def __init__(self):
        self.original_names = {}

    # Gets original name if it exists. If not, print the raw RelationId
    def get_original_name(self, relation_id: ir.RelationId):
        return self.original_names.get(relation_id, relation_id.id)

    def visit(self, node: ir.LqpNode, *args: Any) -> None:
        if isinstance(node, ir.Fragment):
            self.original_names = node.debug_info.id_to_orig_name
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
        super().__init__()
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

    def visit_FunctionalDependency(self, node: ir.FunctionalDependency):
        self.visit(node.guard)

# Checks for shadowing of variables. Raises ValidationError upon encountering such.
class ShadowedVariableFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        super().__init__()
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
        super().__init__()
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
                original_name = self.get_original_name(node.name)
                # Dup ID, different fragments, same or different epoch.
                raise ValidationError(
                    f"Duplicate declaration across fragments at {node.meta}: '{original_name}'"
                )
            elif self.curr_epoch == seen_in_epoch:
                original_name = self.get_original_name(node.name)
                # Dup ID, same fragment, same epoch.
                raise ValidationError(
                    f"Duplicate declaration within fragment in epoch at {node.meta}: '{original_name}'"
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
                original_name = self.get_original_name(d)
                raise ValidationError(
                    f"Duplicate declaration at {d.meta}: '{original_name}'"
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
    def type_error_message(atom: ir.Atom, original_name, index: int, expected: ir.TypeName, actual: ir.TypeName) -> str:
        term = atom.terms[index]
        pretty_term = p.to_str(term, 0)
        return \
            f"Incorrect type for '{original_name}' atom at index {index} ('{pretty_term}') at {atom.meta}: " +\
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
        super().__init__()
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
                original_name = self.get_original_name(node.name)
                raise ValidationError(
                    f"Incorrect arity for '{original_name}' atom at {node.meta}: " +\
                    f"expected {relation_arity} term{'' if relation_arity == 1 else 's'}, got {atom_arity}"
                )

            # Check types.
            for (i, (term, relation_type)) in enumerate(zip(node.terms, relation_type_sig)):
                # var_types[term] is okay because we assume UnusedVariableVisitor.
                term_type = state.var_types[term.name] if isinstance(term, ir.Var) else AtomTypeChecker.constant_type(term)
                if term_type.value != relation_type.value:
                    original_name = self.get_original_name(node.name)
                    raise ValidationError(
                        AtomTypeChecker.type_error_message(node, original_name, i, relation_type, term_type)
                    )

        # This is a leaf for our purposes, no need to recurse further.

# Checks for the definition (Define) of duplicate Fragment(Ids) within an Epoch.
# Raises ValidationError upon encountering such.
class DuplicateFragmentDefinitionFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        super().__init__()
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
        super().__init__()
        self.visit(txn)

    def visit_Loop(self, node: ir.Loop, *args: Any) -> None:
        for i in node.init:
            if isinstance(i, ir.Break):
                original_name = self.get_original_name(i.name)
                raise ValidationError(
                    f"Break rule found outside of body at {i.meta}: '{original_name}'"
                )

# Loopy contract: Algorithm globals cannot be in loop body unless they were already in init
class LoopyBadGlobalFinder(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        super().__init__()
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
                    original_name = self.get_original_name(i.name)
                    raise ValidationError(
                        f"Global rule found in body at {i.meta}: '{original_name}'"
                    )

class LoopyUpdatesShouldBeAtoms(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        super().__init__()
        self.generic_visit(txn)

    def visit_instruction_with_atom_body(self, node: Any, *args: Any) -> None:
        if not isinstance(node.body.value, ir.Atom):
            instruction_type = node.__class__.__name__
            raise ValidationError(f"{instruction_type} at {node.meta} must have an Atom as its value")

    visit_MonoidDef = visit_MonusDef = visit_Upsert = visit_instruction_with_atom_body

class CSVConfigChecker(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        super().__init__()
        self.relation_types: Dict[ir.RelationId, List[ir.TypeName]] = {
            d.name : AtomTypeChecker.get_relation_sig(d)
            for d in AtomTypeChecker.collect_global_defs(txn)
        }
        self.visit(txn)

    def visit_ExportCSVConfig(self, node: ir.ExportCSVConfig, *args: Any) -> None:
        if node.syntax_delim is not None and len(node.syntax_delim) != 1:
            raise ValidationError(f"CSV delimiter should be a single character at {node.meta}, got '{node.syntax_delim}'")
        if node.syntax_quotechar is not None and len(node.syntax_quotechar) != 1:
            raise ValidationError(f"CSV quotechar should be a single character at {node.meta}, got '{node.syntax_quotechar}'")
        if node.syntax_escapechar is not None and len(node.syntax_escapechar) != 1:
            raise ValidationError(f"CSV escapechar should be a single character at {node.meta}, got '{node.syntax_escapechar}'")

        # Check compression is valid
        valid_compressions = {'', 'gzip'}
        if node.compression is not None and node.compression not in valid_compressions:
            raise ValidationError(f"CSV compression should be one of {valid_compressions} at {node.meta}, got '{node.compression}'")

        # Check that the column relations have the same key types
        column_0_key_types = None
        column_0_relation_id = None
        for column in node.data_columns:
            # If the column relation is not defined in this transaction, we can't check it.
            if column.column_data not in self.relation_types:
                continue

            column_types = self.relation_types[column.column_data]  # type: ignore
            if len(column_types) < 1:
                raise ValidationError(f"Data column relation must have at least one column at {node.meta}, got zero columns in '{self.get_original_name(column.column_data)}'")
            key_types = column_types[:-1]
            if column_0_key_types is None:
                column_0_key_types = key_types
                column_0_relation_id = column.column_data
            else:
                assert column_0_key_types is not None
                assert column_0_relation_id is not None
                if column_0_key_types != key_types:
                    raise ValidationError(
                        f"All data columns in ExportCSVConfig at {node.meta} must have the same key types. " +\
                        f"Got '{self.get_original_name(column_0_relation_id)}' with key types {[str(t) for t in column_0_key_types]} " +\
                        f"and '{self.get_original_name(column.column_data)}' with key types {[str(t) for t in key_types]}."
                    )

# Checks that the variables used in an FD are drawn from free variables of the guard.
class FDVarsChecker(LqpVisitor):
    def __init__(self, txn: ir.Transaction):
        super().__init__()
        self.visit(txn)

    def visit_FunctionalDependency(self, node: ir.FunctionalDependency):
        guard_var_names = {var.name for (var, _) in node.guard.vars}
        for var in node.keys:
            if var.name not in guard_var_names:
                raise ValidationError(f"Key variable '{var.name}' not declared in guard at {var.meta}")
        for var in node.values:
            if var.name not in guard_var_names:
                raise ValidationError(f"Value variable '{var.name}' not declared in guard at {var.meta}")

def validate_lqp(lqp: ir.Transaction):
    ShadowedVariableFinder(lqp)
    UnusedVariableVisitor(lqp)
    DuplicateRelationIdFinder(lqp)
    DuplicateFragmentDefinitionFinder(lqp)
    AtomTypeChecker(lqp)
    LoopyBadBreakFinder(lqp)
    LoopyBadGlobalFinder(lqp)
    LoopyUpdatesShouldBeAtoms(lqp)
    CSVConfigChecker(lqp)
    FDVarsChecker(lqp)
