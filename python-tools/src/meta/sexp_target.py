"""S-expression visitors for target language constructs.

This module provides functions to convert s-expressions into TargetType
and TargetExpr objects from the target module.

Type syntax:
    String                          -> BaseType("String")
    Int64                           -> BaseType("Int64")
    Float64                         -> BaseType("Float64")
    Boolean                         -> BaseType("Boolean")
    (Message module name)           -> MessageType(module, name)
    (List elem_type)                -> ListType(elem_type)
    (Option elem_type)              -> OptionType(elem_type)
    (Tuple type1 type2 ...)         -> TupleType([type1, type2, ...])
    (Function (param_types...) ret) -> FunctionType(param_types, ret)

Expression syntax:
    (var name type)                 -> Var(name, type)
    (lit value)                     -> Lit(value)
    (call func args...)             -> Call(func, args)
    (lambda ((p1 T1) ...) RT body)  -> Lambda([Var(p1,T1)...], RT, body)
    (let (name type) init body)     -> Let(Var(name,type), init, body)
    (if cond then else)             -> IfElse(cond, then, else)
    (builtin name)                  -> Builtin(name)
    (message module name)           -> Message(module, name)
    (oneof field)                   -> OneOf(field)
    (list type elems...)            -> ListExpr(elems, type)
    (:symbol)                       -> Symbol("symbol")
    (seq e1 e2 ...)                 -> Seq([e1, e2, ...])
"""

from typing import List

from .sexp import SAtom, SList, SExpr
from .target import (
    TargetType, BaseType, MessageType, ListType, OptionType, TupleType, FunctionType,
    TargetExpr, Var, Lit, Symbol, Builtin, Message, OneOf, ListExpr, Call, Lambda,
    Let, IfElse, Seq, While, Foreach, ForeachEnumerated, Assign, Return
)


class SExprConversionError(Exception):
    """Error during s-expression to target conversion."""
    pass


def sexp_to_type(sexp: SExpr) -> TargetType:
    """Convert an s-expression to a TargetType.

    Args:
        sexp: S-expression representing a type

    Returns:
        Corresponding TargetType

    Raises:
        SExprConversionError: If the s-expression is not a valid type
    """
    if isinstance(sexp, SAtom):
        if sexp.quoted:
            raise SExprConversionError(f"Unexpected string literal in type: {sexp}")
        if isinstance(sexp.value, str):
            return BaseType(sexp.value)
        raise SExprConversionError(f"Invalid type atom: {sexp}")

    if not isinstance(sexp, SList) or len(sexp) == 0:
        raise SExprConversionError(f"Invalid type expression: {sexp}")

    head = sexp.head()
    if not isinstance(head, SAtom) or head.quoted:
        raise SExprConversionError(f"Type expression must start with a symbol: {sexp}")

    tag = head.value

    if tag == "Message":
        if len(sexp) != 3:
            raise SExprConversionError(f"Message type requires module and name: {sexp}")
        module = _expect_symbol(sexp[1], "Message module")
        name = _expect_symbol(sexp[2], "Message name")
        return MessageType(module, name)

    elif tag == "List":
        if len(sexp) != 2:
            raise SExprConversionError(f"List type requires element type: {sexp}")
        return ListType(sexp_to_type(sexp[1]))

    elif tag == "Option":
        if len(sexp) != 2:
            raise SExprConversionError(f"Option type requires element type: {sexp}")
        return OptionType(sexp_to_type(sexp[1]))

    elif tag == "Tuple":
        elem_types = [sexp_to_type(e) for e in sexp.elements[1:]]
        return TupleType(elem_types)

    elif tag == "Function":
        if len(sexp) != 3:
            raise SExprConversionError(f"Function type requires param types and return type: {sexp}")
        param_list = sexp[1]
        if not isinstance(param_list, SList):
            raise SExprConversionError(f"Function param types must be a list: {param_list}")
        param_types = [sexp_to_type(p) for p in param_list.elements]
        return_type = sexp_to_type(sexp[2])
        return FunctionType(param_types, return_type)

    else:
        raise SExprConversionError(f"Unknown type constructor: {tag}")


def sexp_to_expr(sexp: SExpr) -> TargetExpr:
    """Convert an s-expression to a TargetExpr.

    Args:
        sexp: S-expression representing an expression

    Returns:
        Corresponding TargetExpr

    Raises:
        SExprConversionError: If the s-expression is not a valid expression
    """
    if isinstance(sexp, SAtom):
        # Literal values
        if sexp.quoted:
            return Lit(sexp.value)
        if isinstance(sexp.value, (int, float)):
            return Lit(sexp.value)
        if isinstance(sexp.value, bool):
            return Lit(sexp.value)
        # Symbol starting with : is a Symbol literal
        if isinstance(sexp.value, str) and sexp.value.startswith(':'):
            return Symbol(sexp.value[1:])
        # Otherwise it's an untyped variable reference - not allowed at top level
        raise SExprConversionError(f"Untyped symbol in expression context: {sexp.value}")

    if not isinstance(sexp, SList) or len(sexp) == 0:
        raise SExprConversionError(f"Invalid expression: {sexp}")

    head = sexp.head()
    if not isinstance(head, SAtom) or head.quoted:
        raise SExprConversionError(f"Expression must start with a symbol: {sexp}")

    tag = head.value

    if tag == "var":
        if len(sexp) != 3:
            raise SExprConversionError(f"var requires name and type: {sexp}")
        name = _expect_symbol(sexp[1], "variable name")
        typ = sexp_to_type(sexp[2])
        return Var(name, typ)

    elif tag == "lit":
        if len(sexp) != 2:
            raise SExprConversionError(f"lit requires a value: {sexp}")
        val_sexp = sexp[1]
        if isinstance(val_sexp, SAtom):
            return Lit(val_sexp.value)
        raise SExprConversionError(f"lit value must be an atom: {val_sexp}")

    elif tag == "call":
        if len(sexp) < 2:
            raise SExprConversionError(f"call requires function: {sexp}")
        func = sexp_to_expr(sexp[1])
        args = [sexp_to_expr(a) for a in sexp.elements[2:]]
        return Call(func, args)

    elif tag == "lambda":
        if len(sexp) != 4:
            raise SExprConversionError(f"lambda requires params, return type, and body: {sexp}")
        params_sexp = sexp[1]
        if not isinstance(params_sexp, SList):
            raise SExprConversionError(f"lambda params must be a list: {params_sexp}")
        params: List[Var] = []
        for p in params_sexp.elements:
            if not isinstance(p, SList) or len(p) != 2:
                raise SExprConversionError(f"lambda param must be (name type): {p}")
            name = _expect_symbol(p[0], "param name")
            typ = sexp_to_type(p[1])
            params.append(Var(name, typ))
        return_type = sexp_to_type(sexp[2])
        body = sexp_to_expr(sexp[3])
        return Lambda(params, return_type, body)

    elif tag == "let":
        if len(sexp) != 4:
            raise SExprConversionError(f"let requires (name type), init, and body: {sexp}")
        var_sexp = sexp[1]
        if not isinstance(var_sexp, SList) or len(var_sexp) != 2:
            raise SExprConversionError(f"let binding must be (name type): {var_sexp}")
        name = _expect_symbol(var_sexp[0], "let variable name")
        typ = sexp_to_type(var_sexp[1])
        init = sexp_to_expr(sexp[2])
        body = sexp_to_expr(sexp[3])
        return Let(Var(name, typ), init, body)

    elif tag == "if":
        if len(sexp) != 4:
            raise SExprConversionError(f"if requires condition, then, and else: {sexp}")
        cond = sexp_to_expr(sexp[1])
        then_branch = sexp_to_expr(sexp[2])
        else_branch = sexp_to_expr(sexp[3])
        return IfElse(cond, then_branch, else_branch)

    elif tag == "builtin":
        if len(sexp) != 2:
            raise SExprConversionError(f"builtin requires name: {sexp}")
        name = _expect_symbol(sexp[1], "builtin name")
        return Builtin(name)

    elif tag == "message":
        if len(sexp) != 3:
            raise SExprConversionError(f"message requires module and name: {sexp}")
        module = _expect_symbol(sexp[1], "message module")
        name = _expect_symbol(sexp[2], "message name")
        return Message(module, name)

    elif tag == "oneof":
        if len(sexp) != 2:
            raise SExprConversionError(f"oneof requires field name: {sexp}")
        field = _expect_symbol(sexp[1], "oneof field")
        return OneOf(field)

    elif tag == "list":
        if len(sexp) < 2:
            raise SExprConversionError(f"list requires element type: {sexp}")
        elem_type = sexp_to_type(sexp[1])
        elements = [sexp_to_expr(e) for e in sexp.elements[2:]]
        return ListExpr(elements, elem_type)

    elif tag == "seq":
        if len(sexp) < 3:
            raise SExprConversionError(f"seq requires at least 2 expressions: {sexp}")
        exprs = [sexp_to_expr(e) for e in sexp.elements[1:]]
        return Seq(exprs)

    elif tag == "while":
        if len(sexp) != 3:
            raise SExprConversionError(f"while requires condition and body: {sexp}")
        cond = sexp_to_expr(sexp[1])
        body = sexp_to_expr(sexp[2])
        return While(cond, body)

    elif tag == "foreach":
        if len(sexp) != 4:
            raise SExprConversionError(f"foreach requires (var type), collection, and body: {sexp}")
        var_sexp = sexp[1]
        if not isinstance(var_sexp, SList) or len(var_sexp) != 2:
            raise SExprConversionError(f"foreach var must be (name type): {var_sexp}")
        name = _expect_symbol(var_sexp[0], "foreach variable name")
        typ = sexp_to_type(var_sexp[1])
        collection = sexp_to_expr(sexp[2])
        body = sexp_to_expr(sexp[3])
        return Foreach(Var(name, typ), collection, body)

    elif tag == "assign":
        if len(sexp) != 3:
            raise SExprConversionError(f"assign requires (var type) and expr: {sexp}")
        var_sexp = sexp[1]
        if not isinstance(var_sexp, SList) or len(var_sexp) != 2:
            raise SExprConversionError(f"assign var must be (name type): {var_sexp}")
        name = _expect_symbol(var_sexp[0], "assign variable name")
        typ = sexp_to_type(var_sexp[1])
        expr = sexp_to_expr(sexp[2])
        return Assign(Var(name, typ), expr)

    elif tag == "return":
        if len(sexp) != 2:
            raise SExprConversionError(f"return requires expression: {sexp}")
        expr = sexp_to_expr(sexp[1])
        return Return(expr)

    else:
        raise SExprConversionError(f"Unknown expression form: {tag}")


def type_to_sexp(typ: TargetType) -> SExpr:
    """Convert a TargetType to an s-expression.

    Args:
        typ: TargetType to convert

    Returns:
        S-expression representation
    """
    from .sexp import SAtom, SList

    if isinstance(typ, BaseType):
        return SAtom(typ.name)

    elif isinstance(typ, MessageType):
        return SList((SAtom("Message"), SAtom(typ.module), SAtom(typ.name)))

    elif isinstance(typ, ListType):
        return SList((SAtom("List"), type_to_sexp(typ.element_type)))

    elif isinstance(typ, OptionType):
        return SList((SAtom("Option"), type_to_sexp(typ.element_type)))

    elif isinstance(typ, TupleType):
        return SList((SAtom("Tuple"),) + tuple(type_to_sexp(t) for t in typ.elements))

    elif isinstance(typ, FunctionType):
        param_types = SList(tuple(type_to_sexp(t) for t in typ.param_types))
        return SList((SAtom("Function"), param_types, type_to_sexp(typ.return_type)))

    else:
        raise SExprConversionError(f"Unknown type: {type(typ).__name__}")


def expr_to_sexp(expr: TargetExpr) -> SExpr:
    """Convert a TargetExpr to an s-expression.

    Args:
        expr: TargetExpr to convert

    Returns:
        S-expression representation
    """
    from .sexp import SAtom, SList

    if isinstance(expr, Var):
        return SList((SAtom("var"), SAtom(expr.name), type_to_sexp(expr.type)))

    elif isinstance(expr, Lit):
        if isinstance(expr.value, str):
            return SList((SAtom("lit"), SAtom(expr.value, quoted=True)))
        elif isinstance(expr.value, bool):
            return SList((SAtom("lit"), SAtom(expr.value)))
        else:
            return SList((SAtom("lit"), SAtom(expr.value)))

    elif isinstance(expr, Symbol):
        return SAtom(":" + expr.name)

    elif isinstance(expr, Builtin):
        return SList((SAtom("builtin"), SAtom(expr.name)))

    elif isinstance(expr, Message):
        return SList((SAtom("message"), SAtom(expr.module), SAtom(expr.name)))

    elif isinstance(expr, OneOf):
        return SList((SAtom("oneof"), SAtom(expr.field_name)))

    elif isinstance(expr, ListExpr):
        return SList((SAtom("list"), type_to_sexp(expr.element_type)) +
                     tuple(expr_to_sexp(e) for e in expr.elements))

    elif isinstance(expr, Call):
        return SList((SAtom("call"), expr_to_sexp(expr.func)) +
                     tuple(expr_to_sexp(a) for a in expr.args))

    elif isinstance(expr, Lambda):
        params = SList(tuple(
            SList((SAtom(p.name), type_to_sexp(p.type))) for p in expr.params
        ))
        return SList((SAtom("lambda"), params, type_to_sexp(expr.return_type),
                      expr_to_sexp(expr.body)))

    elif isinstance(expr, Let):
        var_sexp = SList((SAtom(expr.var.name), type_to_sexp(expr.var.type)))
        return SList((SAtom("let"), var_sexp, expr_to_sexp(expr.init),
                      expr_to_sexp(expr.body)))

    elif isinstance(expr, IfElse):
        return SList((SAtom("if"), expr_to_sexp(expr.condition),
                      expr_to_sexp(expr.then_branch), expr_to_sexp(expr.else_branch)))

    elif isinstance(expr, Seq):
        return SList((SAtom("seq"),) + tuple(expr_to_sexp(e) for e in expr.exprs))

    elif isinstance(expr, While):
        return SList((SAtom("while"), expr_to_sexp(expr.condition),
                      expr_to_sexp(expr.body)))

    elif isinstance(expr, Foreach):
        var_sexp = SList((SAtom(expr.var.name), type_to_sexp(expr.var.type)))
        return SList((SAtom("foreach"), var_sexp, expr_to_sexp(expr.collection),
                      expr_to_sexp(expr.body)))

    elif isinstance(expr, ForeachEnumerated):
        idx_sexp = SList((SAtom(expr.index_var.name), type_to_sexp(expr.index_var.type)))
        var_sexp = SList((SAtom(expr.var.name), type_to_sexp(expr.var.type)))
        return SList((SAtom("foreach_enumerated"), idx_sexp, var_sexp,
                      expr_to_sexp(expr.collection), expr_to_sexp(expr.body)))

    elif isinstance(expr, Assign):
        var_sexp = SList((SAtom(expr.var.name), type_to_sexp(expr.var.type)))
        return SList((SAtom("assign"), var_sexp, expr_to_sexp(expr.expr)))

    elif isinstance(expr, Return):
        return SList((SAtom("return"), expr_to_sexp(expr.expr)))

    else:
        raise SExprConversionError(f"Unknown expression: {type(expr).__name__}")


def _expect_symbol(sexp: SExpr, context: str) -> str:
    """Expect an unquoted symbol and return its string value."""
    if not isinstance(sexp, SAtom):
        raise SExprConversionError(f"{context} must be a symbol, got: {sexp}")
    if sexp.quoted:
        raise SExprConversionError(f"{context} must be unquoted symbol, got string: {sexp}")
    if not isinstance(sexp.value, str):
        raise SExprConversionError(f"{context} must be a symbol, got: {sexp}")
    return sexp.value


__all__ = [
    'SExprConversionError',
    'sexp_to_type',
    'sexp_to_expr',
    'type_to_sexp',
    'expr_to_sexp',
]
