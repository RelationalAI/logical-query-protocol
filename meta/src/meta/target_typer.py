"""Type checker for the target IR.

Validates type consistency of TargetExpr trees before codegen.
Runs on the output of parser_gen / pretty_gen.
"""

from .target import (
    Assign,
    BaseType,
    Call,
    Foreach,
    ForeachEnumerated,
    FunctionType,
    FunDef,
    GetElement,
    GetField,
    IfElse,
    Lambda,
    Let,
    ListExpr,
    ListType,
    NewMessage,
    OptionType,
    ParseNonterminal,
    ParseNonterminalDef,
    PrintNonterminal,
    PrintNonterminalDef,
    Return,
    Seq,
    SequenceType,
    TargetExpr,
    TargetType,
    TupleType,
    VarType,
    While,
    match_types,
    subst_type,
)
from .target_utils import is_subtype, type_join
from .target_visitor import TargetExprVisitor


def _contains_var_type(t: TargetType) -> bool:
    """Check if a type contains any unresolved VarType."""
    if isinstance(t, VarType):
        return True
    if isinstance(t, (BaseType,)):
        return False
    if isinstance(t, SequenceType):
        return _contains_var_type(t.element_type)
    if isinstance(t, ListType):
        return _contains_var_type(t.element_type)
    if isinstance(t, OptionType):
        return _contains_var_type(t.element_type)
    if isinstance(t, TupleType):
        return any(_contains_var_type(e) for e in t.elements)
    if isinstance(t, FunctionType):
        return any(_contains_var_type(p) for p in t.param_types) or _contains_var_type(
            t.return_type
        )
    return False


class _TypeCheckVisitor(TargetExprVisitor):
    """Walks a TargetExpr tree and collects type errors."""

    def __init__(self, context: str, return_type: TargetType | None = None):
        super().__init__()
        self._context = context
        self._return_type = return_type
        self.errors: list[str] = []

    def _err(self, msg: str) -> None:
        self.errors.append(f"[{self._context}] {msg}")

    def _expr_type(self, expr: TargetExpr) -> TargetType | None:
        try:
            t = expr.target_type()
            if isinstance(t, VarType):
                return None
            return t
        except (NotImplementedError, ValueError, TypeError):
            return None

    # --- visitors ---

    def visit_Let(self, expr: Let) -> None:
        self.visit(expr.init)
        init_type = self._expr_type(expr.init)
        var_type = expr.var.type
        if init_type is not None and not is_subtype(init_type, var_type):
            self._err(
                f"Let '{expr.var.name}': init type {init_type} "
                f"is not a subtype of var type {var_type}"
            )
        self.visit(expr.body)

    def visit_Assign(self, expr: Assign) -> None:
        self.visit(expr.expr)
        expr_type = self._expr_type(expr.expr)
        var_type = expr.var.type
        if expr_type is not None and not is_subtype(expr_type, var_type):
            self._err(
                f"Assign '{expr.var.name}': expr type {expr_type} "
                f"is not a subtype of var type {var_type}"
            )

    def visit_IfElse(self, expr: IfElse) -> None:
        self.visit(expr.condition)
        cond_type = self._expr_type(expr.condition)
        if cond_type is not None and cond_type != BaseType("Boolean"):
            self._err(f"IfElse condition has type {cond_type}, expected Boolean")
        self.visit(expr.then_branch)
        self.visit(expr.else_branch)
        then_type = self._expr_type(expr.then_branch)
        else_type = self._expr_type(expr.else_branch)
        if then_type is not None and else_type is not None:
            try:
                type_join(then_type, else_type)
            except TypeError as e:
                self._err(f"IfElse branches have incompatible types: {e}")

    def visit_Call(self, expr: Call) -> None:
        if not isinstance(expr.func, (ParseNonterminal, PrintNonterminal)):
            self.visit(expr.func)
        for arg in expr.args:
            self.visit(arg)
        if isinstance(expr.func, (ParseNonterminal, PrintNonterminal)):
            return
        func_type = self._expr_type(expr.func)
        if func_type is None:
            return
        if not isinstance(func_type, FunctionType):
            self._err(f"Call target has type {func_type}, expected FunctionType")
            return
        # Skip arity check for variadic builtins (empty param_types)
        if len(func_type.param_types) == 0:
            return
        if len(expr.args) != len(func_type.param_types):
            self._err(
                f"Call arity mismatch: expected {len(func_type.param_types)} args, "
                f"got {len(expr.args)}"
            )
            return
        for i, (param_type, arg) in enumerate(zip(func_type.param_types, expr.args)):
            arg_type = self._expr_type(arg)
            if arg_type is None:
                continue
            if isinstance(param_type, VarType):
                continue
            # Resolve type variables from all args
            mapping: dict[str, TargetType] = {}
            for pt, a in zip(func_type.param_types, expr.args):
                at = self._expr_type(a)
                if at is not None:
                    match_types(pt, at, mapping)
            resolved = subst_type(param_type, mapping)
            if _contains_var_type(resolved):
                continue
            if not is_subtype(arg_type, resolved):
                self._err(
                    f"Call arg {i}: type {arg_type} "
                    f"is not a subtype of param type {resolved}"
                )

    def visit_While(self, expr: While) -> None:
        self.visit(expr.condition)
        cond_type = self._expr_type(expr.condition)
        if cond_type is not None and cond_type != BaseType("Boolean"):
            self._err(f"While condition has type {cond_type}, expected Boolean")
        self.visit(expr.body)

    def visit_Foreach(self, expr: Foreach) -> None:
        self.visit(expr.collection)
        coll_type = self._expr_type(expr.collection)
        if coll_type is not None and not isinstance(
            coll_type, (SequenceType, ListType)
        ):
            self._err(
                f"Foreach collection has type {coll_type}, expected Sequence or List"
            )
        self.visit(expr.body)

    def visit_ForeachEnumerated(self, expr: ForeachEnumerated) -> None:
        self.visit(expr.collection)
        coll_type = self._expr_type(expr.collection)
        if coll_type is not None and not isinstance(
            coll_type, (SequenceType, ListType)
        ):
            self._err(
                f"ForeachEnumerated collection has type {coll_type}, "
                f"expected Sequence or List"
            )
        self.visit(expr.body)

    def visit_Lambda(self, expr: Lambda) -> None:
        self.visit(expr.body)
        body_type = self._expr_type(expr.body)
        if (body_type is not None
            and not _contains_var_type(body_type)
            and not is_subtype(body_type, expr.return_type)
        ):
            self._err(
                f"Lambda body has type {body_type}, "
                f"expected subtype of {expr.return_type}"
            )

    def visit_GetElement(self, expr: GetElement) -> None:
        self.visit(expr.tuple_expr)
        tuple_type = self._expr_type(expr.tuple_expr)
        if tuple_type is None:
            return
        if isinstance(tuple_type, TupleType):
            if expr.index < 0 or expr.index >= len(tuple_type.elements):
                self._err(
                    f"GetElement index {expr.index} out of bounds "
                    f"for tuple with {len(tuple_type.elements)} elements"
                )
        elif not isinstance(tuple_type, (SequenceType, ListType)):
            self._err(f"GetElement on non-tuple/sequence type: {tuple_type}")

    def visit_GetField(self, expr: GetField) -> None:
        self.visit(expr.object)

    def visit_ListExpr(self, expr: ListExpr) -> None:
        for elem in expr.elements:
            self.visit(elem)
            elem_type = self._expr_type(elem)
            if elem_type is not None and not is_subtype(elem_type, expr.element_type):
                self._err(
                    f"ListExpr element has type {elem_type}, "
                    f"expected subtype of {expr.element_type}"
                )

    def visit_NewMessage(self, expr: NewMessage) -> None:
        for _, field_expr in expr.fields:
            self.visit(field_expr)

    def visit_Return(self, expr: Return) -> None:
        self.visit(expr.expr)

    def visit_Seq(self, expr: Seq) -> None:
        for e in expr.exprs:
            self.visit(e)


def typecheck_def(
    defn: ParseNonterminalDef | PrintNonterminalDef | FunDef,
) -> list[str]:
    """Type-check a single definition. Returns list of error messages."""
    if isinstance(defn, ParseNonterminalDef):
        name = f"parse_{defn.nonterminal.name}"
    elif isinstance(defn, PrintNonterminalDef):
        name = f"pretty_{defn.nonterminal.name}"
    else:
        name = defn.name

    if defn.body is None:
        return []

    visitor = _TypeCheckVisitor(name, defn.return_type)
    visitor.visit(defn.body)
    return visitor.errors


def typecheck_ir(
    parse_defs: list[ParseNonterminalDef],
    pretty_defs: list[PrintNonterminalDef],
    fun_defs: list[FunDef],
) -> list[str]:
    """Type-check all definitions. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    for defn in parse_defs:
        errors.extend(typecheck_def(defn))
    for defn in pretty_defs:
        errors.extend(typecheck_def(defn))
    for defn in fun_defs:
        errors.extend(typecheck_def(defn))
    return errors
