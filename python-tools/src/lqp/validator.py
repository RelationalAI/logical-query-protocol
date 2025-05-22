import lqp.ir as ir
from typing import Any, List, Tuple, Set
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

class VariableCollector(LqpVisitor):
    def __init__(self):
        self.variables: Set[str] = set()
    def visit_Var(self, node: ir.Var, *args: Any) -> None:
        self.variables.add(node.name)

def variables(node: ir.LqpNode) -> Set[str]:
    collector = VariableCollector()
    collector.visit(node)
    return collector.variables

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

class _GroundingVisitor:
    def visit(self, node: ir.LqpNode, bound: Set[str]) -> Tuple[Set[str], Set[str], Set[str]]:
        return getattr(self, f"visit_{node.__class__.__name__}", self.generic_visit)(node, bound)

    def generic_visit(self, node: ir.LqpNode, bound: Set[str]) -> Tuple[Set[str], Set[str], Set[str]]:
        if not is_dataclass(node):
            return set(), set(), set()
        g = n = q = set()
        for f in fields(node):
            v = getattr(node, f.name)
            if isinstance(v, ir.LqpNode):
                g2, n2, q2 = self.visit(v, bound)
                g |= g2; n |= n2; q |= q2
            elif isinstance(v, (list, tuple)):
                for item in v:
                    if isinstance(item, ir.LqpNode):
                        g2, n2, q2 = self.visit(item, bound)
                        g |= g2; n |= n2; q |= q2
        return g, n, q

    def _vars(self, terms) -> Set[str]:
        out: Set[str] = set()
        for t in terms:
            if isinstance(t, ir.Var):
                out.add(t.name)
            elif isinstance(t, (list, tuple)):
                out |= self._vars(t)
        return out

    def visit_Atom(self, node: ir.Atom, bound: Set[str]):
        v = self._vars(node.terms)
        return v, set(), set()

    def visit_RelAtom(self, node: ir.RelAtom, bound: Set[str]):
        v = self._vars(node.terms)
        return v, set(), set()

    def visit_Primitive(self, node: ir.Primitive, bound: Set[str]):
        if not node.terms:
            return set(), set(), set()
        prev_vars = self._vars(node.terms[:-1])
        last = node.terms[-1]
        g = {last.name} if isinstance(last, ir.Var) and prev_vars <= bound else set()
        return g, set(), set()

    def visit_Not(self, node: ir.Not, bound: Set[str]):
        g, n, q = self.visit(node.arg, bound)
        return n, g, q

    def visit_Conjunction(self, node: ir.Conjunction, bound: Set[str]):
        gs: List[Set[str]] = []
        ns: List[Set[str]] = []
        qs: Set[str] = set()
        for a in node.args:
            g, n, q = self.visit(a, bound)
            gs.append(g); ns.append(n); qs |= q
        grounded = set().union(*gs) if gs else set()
        negated = set.intersection(*ns) if ns else set()
        return grounded, negated, qs

    def visit_Disjunction(self, node: ir.Disjunction, bound: Set[str]):
        gs: List[Set[str]] = []
        ns: List[Set[str]] = []
        qs: Set[str] = set()
        for a in node.args:
            g, n, q = self.visit(a, bound)
            gs.append(g); ns.append(n); qs |= q
        grounded = set.intersection(*gs) if gs else set()
        negated = set().union(*ns) if ns else set()
        return grounded, negated, qs

    def visit_Abstraction(self, node: ir.Abstraction, bound: Set[str]):
        declared = {v[0].name for v in node.vars}
        g, n, q = self.visit(node.value, bound)
        quant = declared & g
        g -= declared; n -= declared; q |= quant
        return g, n, q

def grounded(node: ir.LqpNode) -> Set[str]:
    bound: Set[str] = set()
    prev: Set[str] | None = None
    visitor = _GroundingVisitor()
    while bound != prev:
        prev = bound.copy()
        g, n, q = visitor.visit(node, bound)
        bound |= g | q
    return bound

def grounding_check(node: ir.LqpNode):
    bound = grounded(node)
    n = variables(node) - bound
    if n:
        raise ValidationError(f"Variables not grounded: {', '.join(sorted(n))}")

def validate_lqp(lqp: ir.LqpNode):
    UnusedVariableVisitor().visit(lqp)
    grounding_check(lqp)
