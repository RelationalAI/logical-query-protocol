"""Dead function elimination for generated parsers.

Computes the set of user-defined functions reachable from the generated
parse function bodies and filters out unreachable ones.
"""

from typing import Dict, List, Sequence, Set

from .target import FunDef, NamedFun, TargetExpr
from .target_visitor import TargetExprVisitor


class _NamedFunCollector(TargetExprVisitor):
    """Collect names of all NamedFun references in an expression tree."""

    def __init__(self):
        super().__init__()
        self.refs: Set[str] = set()

    def visit_NamedFun(self, expr: NamedFun) -> None:
        self.refs.add(expr.name)


def collect_named_fun_refs(expr: TargetExpr) -> Set[str]:
    """Collect names of all NamedFun references in an expression tree."""
    collector = _NamedFunCollector()
    collector.visit(expr)
    return collector.refs


def live_functions(
    roots: Sequence[TargetExpr],
    function_defs: Dict[str, FunDef],
) -> Dict[str, FunDef]:
    """Return the subset of function_defs reachable from roots.

    Uses a worklist algorithm: seed with NamedFun refs in roots, then
    transitively follow refs through function bodies.
    """
    seen: Set[str] = set()
    worklist: List[str] = []

    for root in roots:
        for name in collect_named_fun_refs(root):
            if name not in seen:
                seen.add(name)
                worklist.append(name)

    while worklist:
        name = worklist.pop()
        fundef = function_defs.get(name)
        if fundef is None or fundef.body is None:
            continue
        for ref in collect_named_fun_refs(fundef.body):
            if ref not in seen:
                seen.add(ref)
                worklist.append(ref)

    return {name: function_defs[name] for name in seen if name in function_defs}
