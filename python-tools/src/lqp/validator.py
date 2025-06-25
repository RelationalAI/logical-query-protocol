import lqp.ir as ir
from typing import Any, Dict, List, Tuple, Sequence, Set
from dataclasses import is_dataclass, fields

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
    def __init__(self):
        self.scopes: List[Tuple[Set[str], Set[str]]] = []

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

# Checks for duplicate RelationIds within a fragment.
# Raises ValidationError upon encountering such.
class DuplicateRelationIdFinder(LqpVisitor):
    def visit_Fragment(self, node: ir.Fragment, *args: Any) -> None:
        seen_ids = set()
        for decl in node.declarations:
            # Of Declarations, only Defs have relation IDs.
            if isinstance(decl, ir.Def):
                if decl.name in seen_ids:
                    raise ValidationError(
                        f"Duplicate declaration within fragment at {decl.meta}: '{decl.name.id}'"
                    )
                else:
                    seen_ids.add(decl.name)

# Checks that Atoms are applied to the correct number and types of terms.
class AtomTypeChecker(LqpVisitor):
    # Helper to get all Defs defined in a Transaction
    @staticmethod
    def collect_defs(txn: ir.Transaction) -> List[ir.Def]:
        # Visitor to do the work.
        class DefCollector(LqpVisitor):
            def __init__(self):
                self.defs: List[ir.Def] = []

            def visit_Def(self, node: ir.Def) -> None:
                self.defs.append(node)

        dc = DefCollector()
        dc.visit(txn)
        return dc.defs

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

    # The varargs passed in (visit_Abstraction and visit_Atom) must be a Dict
    # of strings to RelTypes (or nothing at all).
    @staticmethod
    def args_ok(args: List[Any]) -> bool:
        return (
            len(args) == 0 or
            (
                len(args) == 1 and
                isinstance(args[0], Dict) and
                all((isinstance(k, str) and isinstance(v, ir.RelType)) for (k, v) in args[0].items())
            )
        )

    @staticmethod
    def type_error_message(atom: ir.Atom, index: int, expected: ir.RelType, actual: ir.RelType) -> str:
        term = atom.terms[index]
        # How should we print the offending term?
        pretty_term = None
        if isinstance(term, ir.Var):
            pretty_term = term.name
        else:
            assert isinstance(term, ir.Constant)
            if isinstance(term, str):
                pretty_term = f"\"{term}\""
            else:
                pretty_term = term

        return \
            f"Incorrect type for '{atom.name.id}' atom at index {index} ('{pretty_term}') at {atom.meta}: " +\
            f"expected {expected} term, got {actual}"


    def __init__(self):
        # Map of relation names to their expected types.
        # We say Option as we cannot perform this pass properly without `visit`
        # being passed a Transaction, which, decisively, contains all relations.
        # Thus, we will populate this in `visit_Transaction`, and if we never
        # `visit_Transaction`, we'll give a warning.
        self.relation_types: Option[Dict[ir.RelationId, List[ir.RelType]]] = None
        # If we try to visit an Atom to check types and `relation_types` is
        # false, we want to warn. But we want to only warn once and this
        # field ensures that.
        self.warned: bool = False

    def visit_Transaction(self, node: ir.Transaction, *args: Any) -> None:
        self.relation_types = {
            # v[1] holds the RelType.
            d.name : [v[1] for v in d.body.vars] for d in AtomTypeChecker.collect_defs(node)
        }
        self.generic_visit(node)

    def visit_Abstraction(self, node: ir.Abstraction, *args: Any) -> None:
        assert AtomTypeChecker.args_ok(args)
        types = {} if len(args) == 0 else args[0]
        self.generic_visit(node, types | {v.name : t for (v, t) in node.vars})

    def visit_Atom(self, node: ir.Atom, *args: Any) -> None:
        assert AtomTypeChecker.args_ok(args)

        if self.relation_types is None:
            if not self.warned:
                print("WARNING: not given a Transaction, cannot typecheck Atoms")
            self.warned = True
        else:
            assert node.name in self.relation_types
            relation_types = self.relation_types[node.name]

            # Check arity.
            atom_arity = len(node.terms)
            relation_arity = len(relation_types)
            if atom_arity != relation_arity:
                raise ValidationError(
                    f"Incorrect arity for '{node.name.id}' atom at {node.meta}: " +\
                    f"expected {relation_arity} term{'' if relation_arity == 1 else 's'}, got {atom_arity}"
                )

            # Check types.
            var_types = {} if len(args) == 0 else args[0]
            for (i, (term, relation_type)) in enumerate(zip(node.terms, relation_types)):
                # var_types[term] is okay because we assume UnusedVariableVisitor.
                term_type = var_types[term.name] if isinstance(term, ir.Var) else AtomTypeChecker.constant_type(term)
                if term_type != relation_type:
                    raise ValidationError(
                        AtomTypeChecker.type_error_message(node, i, relation_type, term_type)
                    )

        # This is a leaf for our purposes, no need to recurse further.


def validate_lqp(lqp: ir.LqpNode):
    ShadowedVariableFinder().visit(lqp)
    UnusedVariableVisitor().visit(lqp)
    DuplicateRelationIdFinder().visit(lqp)
    AtomTypeChecker().visit(lqp)
