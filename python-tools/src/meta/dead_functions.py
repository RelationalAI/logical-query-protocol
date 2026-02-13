"""Dead function elimination for generated parsers.

Computes the set of user-defined functions reachable from the generated
parse function bodies and filters out unreachable ones.
"""

from typing import Dict, List, Set

from .target import (
    Assign, Call, Foreach, ForeachEnumerated, FunDef, GetElement, GetField,
    IfElse, Lambda, Let, ListExpr, NamedFun, NewMessage, Return, Seq,
    TargetExpr, Var, While,
)


def collect_named_fun_refs(expr: TargetExpr) -> Set[str]:
    """Collect names of all NamedFun references in an expression tree."""
    if isinstance(expr, NamedFun):
        return {expr.name}
    elif isinstance(expr, (Var,)):
        return set()
    elif isinstance(expr, Lambda):
        return collect_named_fun_refs(expr.body)
    elif isinstance(expr, Let):
        return collect_named_fun_refs(expr.init) | collect_named_fun_refs(expr.body)
    elif isinstance(expr, Assign):
        return collect_named_fun_refs(expr.expr)
    elif isinstance(expr, Call):
        refs = collect_named_fun_refs(expr.func)
        for arg in expr.args:
            refs |= collect_named_fun_refs(arg)
        return refs
    elif isinstance(expr, Seq):
        refs: Set[str] = set()
        for e in expr.exprs:
            refs |= collect_named_fun_refs(e)
        return refs
    elif isinstance(expr, IfElse):
        return (collect_named_fun_refs(expr.condition)
                | collect_named_fun_refs(expr.then_branch)
                | collect_named_fun_refs(expr.else_branch))
    elif isinstance(expr, While):
        return collect_named_fun_refs(expr.condition) | collect_named_fun_refs(expr.body)
    elif isinstance(expr, Foreach):
        return collect_named_fun_refs(expr.collection) | collect_named_fun_refs(expr.body)
    elif isinstance(expr, ForeachEnumerated):
        return collect_named_fun_refs(expr.collection) | collect_named_fun_refs(expr.body)
    elif isinstance(expr, Return):
        return collect_named_fun_refs(expr.expr)
    elif isinstance(expr, NewMessage):
        refs = set()
        for _, field_expr in expr.fields:
            refs |= collect_named_fun_refs(field_expr)
        return refs
    elif isinstance(expr, GetField):
        return collect_named_fun_refs(expr.object)
    elif isinstance(expr, GetElement):
        return collect_named_fun_refs(expr.tuple_expr)
    elif isinstance(expr, ListExpr):
        refs = set()
        for elem in expr.elements:
            refs |= collect_named_fun_refs(elem)
        return refs
    return set()


def live_functions(
    roots: List[TargetExpr],
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
