"""Visitor base class for TargetExpr trees.

TargetExprVisitor walks a TargetExpr tree for side effects (returns None).
Subclasses override visit_Foo methods and call self.visit_children(expr)
when they want default recursion.
"""

from typing import Callable

from .target import (
    TargetExpr, Var, Lit, Symbol, Builtin, NamedFun, EnumValue, OneOf,
    ParseNonterminal, PrintNonterminal,
    NewMessage, ListExpr, Call, GetField, GetElement,
    Lambda, Let, IfElse, Seq, While, Foreach, ForeachEnumerated,
    Assign, Return,
)


class TargetExprVisitor:
    """Side-effecting tree walker over TargetExpr nodes.

    For each node, visit() dispatches to visit_ClassName (e.g., visit_Call).
    If no such method exists, falls back to visit_children which recurses
    into child TargetExpr nodes.

    Subclasses override visit_Foo to add behavior, calling
    self.visit_children(expr) when they want default recursion.
    """

    def __init__(self):
        self._visit_cache: dict[type, Callable] = {}

    def visit(self, expr: TargetExpr) -> None:
        t = type(expr)
        method = self._visit_cache.get(t)
        if method is None:
            method = getattr(self, f'visit_{t.__name__}', self.visit_children)
            self._visit_cache[t] = method
        method(expr)

    def visit_children(self, expr: TargetExpr) -> None:
        """Visit all child TargetExpr nodes."""
        if isinstance(expr, (Var, Lit, Symbol, Builtin, NamedFun, EnumValue,
                             OneOf, ParseNonterminal, PrintNonterminal)):
            return None
        if isinstance(expr, NewMessage):
            for _, field_expr in expr.fields:
                self.visit(field_expr)
        elif isinstance(expr, ListExpr):
            for elem in expr.elements:
                self.visit(elem)
        elif isinstance(expr, Call):
            self.visit(expr.func)
            for arg in expr.args:
                self.visit(arg)
        elif isinstance(expr, GetField):
            self.visit(expr.object)
        elif isinstance(expr, GetElement):
            self.visit(expr.tuple_expr)
        elif isinstance(expr, Lambda):
            self.visit(expr.body)
        elif isinstance(expr, Let):
            self.visit(expr.init)
            self.visit(expr.body)
        elif isinstance(expr, IfElse):
            self.visit(expr.condition)
            self.visit(expr.then_branch)
            self.visit(expr.else_branch)
        elif isinstance(expr, Seq):
            for e in expr.exprs:
                self.visit(e)
        elif isinstance(expr, While):
            self.visit(expr.condition)
            self.visit(expr.body)
        elif isinstance(expr, Foreach):
            self.visit(expr.collection)
            self.visit(expr.body)
        elif isinstance(expr, ForeachEnumerated):
            self.visit(expr.collection)
            self.visit(expr.body)
        elif isinstance(expr, Assign):
            self.visit(expr.expr)
        elif isinstance(expr, Return):
            self.visit(expr.expr)
        return None
