"""S-expression visitors for target language constructs.

This module provides functions to convert s-expressions into TargetType
and TargetExpr objects from the target module.

Type syntax:
    String                          -> BaseType("String")
    Int64                           -> BaseType("Int64")
    Float64                         -> BaseType("Float64")
    Boolean                         -> BaseType("Boolean")
    (TypeVar name)                  -> VarType(name)
    (Message module name)           -> MessageType(module, name)
    (List elem_type)                -> ListType(elem_type)
    (Dict key_type value_type)      -> DictType(key_type, value_type)
    (Option elem_type)              -> OptionType(elem_type)
    (Tuple type1 type2 ...)         -> TupleType([type1, type2, ...])
    (Function (param_types...) ret) -> FunctionType(param_types, ret)

Expression syntax:
    (var name type)                             -> Var(name, type)
    (lit value)                                 -> Lit(value)
    (call func args...)                         -> Call(func, args)
    (lambda ((p1 T1) ...) RT body)              -> Lambda([Var(p1,T1)...], RT, body)
    (construct ((p1 T1) ...) RT body)           -> Lambda (alias for rule constructors)
    (let (name type) init body)                 -> Let(Var(name,type), init, body)
    (if cond then else)                         -> IfElse(cond, then, else)
    (builtin name)                              -> Builtin(name)
    (new-message module name (f1 e1) ...)       -> NewMessage(module, name, [(f1,e1)...])
    (oneof field)                               -> OneOf(field)
    (list type elems...)                        -> ListExpr(elems, type)
    (get-field object field)                    -> GetField(object, field)
    (get-element tuple index)                   -> GetElement(tuple, index)
    (dict-from-list pairs key_type value_type)  -> DictFromList(pairs, key_type, value_type)
    (dict-lookup dict key [default])            -> DictLookup(dict, key, default)
    (has-field message field_name)              -> HasField(message, field_name)
    (visit-nonterminal visitor_name nt_name T)  -> VisitNonterminal(visitor_name, Nonterminal(nt_name, T))
    (:symbol)                                   -> Symbol("symbol")
    (seq e1 e2 ...)                             -> Seq([e1, e2, ...])
    (while cond body)                           -> While(cond, body)
    (foreach (var type) coll body)              -> Foreach(Var(var,type), coll, body)
    (foreach-enumerated (idx T1) (var T2) c b)  -> ForeachEnumerated(Var(idx,T1), Var(var,T2), c, b)
    (assign (var type) expr)                    -> Assign(Var(var,type), expr)
    (return expr)                               -> Return(expr)
"""

from typing import List

from .sexp import SAtom, SList, SExpr
from .target import (
    TargetType, BaseType, VarType, MessageType, ListType, DictType, OptionType, TupleType, FunctionType,
    TargetExpr, Var, Lit, Symbol, Builtin, NamedFun, NewMessage, OneOf, ListExpr, Call, Lambda,
    Let, IfElse, Seq, While, Foreach, ForeachEnumerated, Assign, Return, GetField,
    GetElement, DictFromList, DictLookup, HasField, VisitNonterminal
)
from .grammar import Nonterminal
from .target_builtins import is_builtin, validate_builtin_call


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

    if tag == "TypeVar":
        if len(sexp) != 2:
            raise SExprConversionError(f"TypeVar requires name: {sexp}")
        name = _expect_symbol(sexp[1], "TypeVar name")
        return VarType(name)

    elif tag == "Message":
        if len(sexp) != 3:
            raise SExprConversionError(f"Message type requires module and name: {sexp}")
        module = _expect_symbol(sexp[1], "Message module")
        name = _expect_symbol(sexp[2], "Message name")
        return MessageType(module, name)

    elif tag == "List":
        if len(sexp) != 2:
            raise SExprConversionError(f"List type requires element type: {sexp}")
        return ListType(sexp_to_type(sexp[1]))

    elif tag == "Dict":
        if len(sexp) != 3:
            raise SExprConversionError(f"Dict type requires key and value types: {sexp}")
        return DictType(sexp_to_type(sexp[1]), sexp_to_type(sexp[2]))

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
            value = val_sexp.value
            # Convert string "true"/"false" to Python booleans
            if value == "true":
                return Lit(True)
            if value == "false":
                return Lit(False)
            return Lit(value)
        raise SExprConversionError(f"lit value must be an atom: {val_sexp}")

    elif tag == "call":
        if len(sexp) < 2:
            raise SExprConversionError(f"call requires function: {sexp}")
        func = sexp_to_expr(sexp[1])
        args = [sexp_to_expr(a) for a in sexp.elements[2:]]
        # Validate builtin calls
        if isinstance(func, Builtin):
            error = validate_builtin_call(func.name, len(args))
            if error:
                raise SExprConversionError(f"In call expression: {error}")
        return Call(func, args)

    elif tag == "lambda" or tag == "construct":
        if len(sexp) != 4:
            raise SExprConversionError(f"{tag} requires params, return type, and body: {sexp}")
        params_sexp = sexp[1]
        if not isinstance(params_sexp, SList):
            raise SExprConversionError(f"{tag} params must be a list: {params_sexp}")
        params: List[Var] = []
        for p in params_sexp.elements:
            if not isinstance(p, SList) or len(p) != 2:
                raise SExprConversionError(f"{tag} param must be (name type): {p}")
            name = _expect_symbol(p[0], "param name")
            typ = sexp_to_type(p[1])
            params.append(Var(name, typ))
        return_type = sexp_to_type(sexp[2])
        body = sexp_to_expr(sexp[3])
        return Lambda(params, return_type, body)

    elif tag == "let":
        # Support multiple bindings: (let (name1 type1) init1 (name2 type2) init2 ... body)
        # Desugar into nested lets: (let (name1 type1) init1 (let (name2 type2) init2 ... body))
        if len(sexp) < 4:
            raise SExprConversionError(f"let requires at least (name type), init, and body: {sexp}")

        # Parse bindings (pairs of (name type) and init)
        # The structure is: (let (name1 type1) init1 (name2 type2) init2 ... body)
        # Bindings come in pairs until we reach the body (last element)
        elements = sexp.elements[1:]  # Skip 'let' keyword

        # Check if we have an odd number of elements (binding pairs + body)
        if len(elements) < 3 or len(elements) % 2 == 0:
            raise SExprConversionError(
                f"let requires pairs of (name type) and init, followed by body: {sexp}")

        # Parse all bindings
        bindings = []
        i = 0
        while i < len(elements) - 1:  # Last element is body
            var_sexp = elements[i]
            if not isinstance(var_sexp, SList) or len(var_sexp) != 2:
                raise SExprConversionError(f"let binding must be (name type): {var_sexp}")
            name = _expect_symbol(var_sexp[0], "let variable name")
            typ = sexp_to_type(var_sexp[1])

            if i + 1 >= len(elements):
                raise SExprConversionError(f"let binding missing init expression: {var_sexp}")
            init = sexp_to_expr(elements[i + 1])

            bindings.append((Var(name, typ), init))
            i += 2

        # Parse body (last element)
        body = sexp_to_expr(elements[-1])

        # Desugar into nested lets from right to left
        result = body
        for var, init in reversed(bindings):
            result = Let(var, init, result)

        return result

    elif tag == "if":
        # Support both forms:
        # (if cond then-branch else-branch) - 3 arguments
        # (if cond then-branch) - 2 arguments, desugars to (if cond then-branch (lit true))
        if len(sexp) == 3:
            # Two-argument form: (if cond then)
            # Desugar to: (if cond then true) - equivalent to (cond and then)
            cond = sexp_to_expr(sexp[1])
            then_branch = sexp_to_expr(sexp[2])
            else_branch = Lit(True)  # Default else branch
            return IfElse(cond, then_branch, else_branch)
        elif len(sexp) == 4:
            # Three-argument form: (if cond then else)
            cond = sexp_to_expr(sexp[1])
            then_branch = sexp_to_expr(sexp[2])
            else_branch = sexp_to_expr(sexp[3])
            return IfElse(cond, then_branch, else_branch)
        else:
            raise SExprConversionError(f"if requires 2 or 3 arguments (cond, then, [else]): {sexp}")

    elif tag == "builtin":
        if len(sexp) != 2:
            raise SExprConversionError(f"builtin requires name: {sexp}")
        name = _expect_symbol(sexp[1], "builtin name")
        # Validate builtin exists (warning only for now to not break existing code)
        if not is_builtin(name):
            # For now just warn, don't error - allows defining new builtins in grammar
            pass
        return Builtin(name)

    elif tag == "named-fun":
        if len(sexp) != 2:
            raise SExprConversionError(f"named-fun requires name: {sexp}")
        name = _expect_symbol(sexp[1], "named-fun name")
        return NamedFun(name)

    elif tag == "new-message":
        if len(sexp) < 3:
            raise SExprConversionError(f"new-message requires module, name, and fields: {sexp}")
        module = _expect_symbol(sexp[1], "new-message module")
        name = _expect_symbol(sexp[2], "new-message name")
        fields = []
        for i in range(3, len(sexp)):
            field_sexp = sexp[i]
            if not isinstance(field_sexp, SList) or len(field_sexp) != 2:
                raise SExprConversionError(f"new-message field must be (field_name expr): {field_sexp}")
            field_name = _expect_symbol(field_sexp[0], "field name")
            field_expr = sexp_to_expr(field_sexp[1])
            fields.append((field_name, field_expr))
        return NewMessage(module, name, tuple(fields))

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

    elif tag == "get-field":
        if len(sexp) != 3:
            raise SExprConversionError(f"get-field requires object and field name: {sexp}")
        obj = sexp_to_expr(sexp[1])
        field_name = _expect_symbol(sexp[2], "field name")
        return GetField(obj, field_name)

    elif tag == "get-element":
        if len(sexp) != 3:
            raise SExprConversionError(f"get-element requires tuple and index: {sexp}")
        tuple_expr = sexp_to_expr(sexp[1])
        index_sexp = sexp[2]
        if not isinstance(index_sexp, SAtom) or not isinstance(index_sexp.value, int):
            raise SExprConversionError(f"get-element index must be an integer literal: {index_sexp}")
        return GetElement(tuple_expr, index_sexp.value)

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

    elif tag == "foreach-enumerated":
        if len(sexp) != 5:
            raise SExprConversionError(f"foreach-enumerated requires (idx type), (var type), collection, and body: {sexp}")
        idx_sexp = sexp[1]
        if not isinstance(idx_sexp, SList) or len(idx_sexp) != 2:
            raise SExprConversionError(f"foreach-enumerated index var must be (name type): {idx_sexp}")
        idx_name = _expect_symbol(idx_sexp[0], "foreach-enumerated index variable name")
        idx_type = sexp_to_type(idx_sexp[1])
        var_sexp = sexp[2]
        if not isinstance(var_sexp, SList) or len(var_sexp) != 2:
            raise SExprConversionError(f"foreach-enumerated var must be (name type): {var_sexp}")
        var_name = _expect_symbol(var_sexp[0], "foreach-enumerated variable name")
        var_type = sexp_to_type(var_sexp[1])
        collection = sexp_to_expr(sexp[3])
        body = sexp_to_expr(sexp[4])
        return ForeachEnumerated(Var(idx_name, idx_type), Var(var_name, var_type), collection, body)

    elif tag == "visit-nonterminal":
        if len(sexp) != 4:
            raise SExprConversionError(f"visit-nonterminal requires visitor_name, nonterminal name, and type: {sexp}")
        visitor_name = _expect_symbol(sexp[1], "visitor name")
        nt_name = _expect_symbol(sexp[2], "nonterminal name")
        nt_type = sexp_to_type(sexp[3])
        return VisitNonterminal(visitor_name, Nonterminal(nt_name, nt_type))

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

    elif tag == "dict-from-list":
        if len(sexp) != 4:
            raise SExprConversionError(f"dict-from-list requires pairs, key type, and value type: {sexp}")
        pairs = sexp_to_expr(sexp[1])
        key_type = sexp_to_type(sexp[2])
        value_type = sexp_to_type(sexp[3])
        return DictFromList(pairs, key_type, value_type)

    elif tag == "dict-lookup":
        if len(sexp) == 3:
            dict_expr = sexp_to_expr(sexp[1])
            key = sexp_to_expr(sexp[2])
            return DictLookup(dict_expr, key, None)
        elif len(sexp) == 4:
            dict_expr = sexp_to_expr(sexp[1])
            key = sexp_to_expr(sexp[2])
            default = sexp_to_expr(sexp[3])
            return DictLookup(dict_expr, key, default)
        else:
            raise SExprConversionError(f"dict-lookup requires dict, key, and optional default: {sexp}")

    elif tag == "has-field":
        if len(sexp) != 3:
            raise SExprConversionError(f"has-field requires message and field name: {sexp}")
        message = sexp_to_expr(sexp[1])
        field_name = _expect_symbol(sexp[2], "field name")
        return HasField(message, field_name)

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

    elif isinstance(typ, VarType):
        return SList((SAtom("TypeVar"), SAtom(typ.name)))

    elif isinstance(typ, MessageType):
        return SList((SAtom("Message"), SAtom(typ.module), SAtom(typ.name)))

    elif isinstance(typ, ListType):
        return SList((SAtom("List"), type_to_sexp(typ.element_type)))

    elif isinstance(typ, DictType):
        return SList((SAtom("Dict"), type_to_sexp(typ.key_type), type_to_sexp(typ.value_type)))

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
            # Serialize booleans as unquoted symbols "true" or "false"
            return SList((SAtom("lit"), SAtom("true" if expr.value else "false")))
        else:
            return SList((SAtom("lit"), SAtom(expr.value)))

    elif isinstance(expr, Symbol):
        return SAtom(":" + expr.name)

    elif isinstance(expr, Builtin):
        return SList((SAtom("builtin"), SAtom(expr.name)))

    elif isinstance(expr, NewMessage):
        field_sexps = tuple(
            SList((SAtom(field_name), expr_to_sexp(field_expr)))
            for field_name, field_expr in expr.fields
        )
        return SList((SAtom("new-message"), SAtom(expr.module), SAtom(expr.name)) + field_sexps)

    elif isinstance(expr, OneOf):
        return SList((SAtom("oneof"), SAtom(expr.field_name)))

    elif isinstance(expr, ListExpr):
        return SList((SAtom("list"), type_to_sexp(expr.element_type)) +
                     tuple(expr_to_sexp(e) for e in expr.elements))

    elif isinstance(expr, GetField):
        return SList((SAtom("get-field"), expr_to_sexp(expr.object), SAtom(expr.field_name)))

    elif isinstance(expr, GetElement):
        return SList((SAtom("get-element"), expr_to_sexp(expr.tuple_expr), SAtom(expr.index)))

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
        return SList((SAtom("foreach-enumerated"), idx_sexp, var_sexp,
                      expr_to_sexp(expr.collection), expr_to_sexp(expr.body)))

    elif isinstance(expr, VisitNonterminal):
        return SList((SAtom("visit-nonterminal"), SAtom(expr.visitor_name),
                      SAtom(expr.nonterminal.name), type_to_sexp(expr.nonterminal.type)))

    elif isinstance(expr, Assign):
        var_sexp = SList((SAtom(expr.var.name), type_to_sexp(expr.var.type)))
        return SList((SAtom("assign"), var_sexp, expr_to_sexp(expr.expr)))

    elif isinstance(expr, Return):
        return SList((SAtom("return"), expr_to_sexp(expr.expr)))

    elif isinstance(expr, DictFromList):
        return SList((SAtom("dict-from-list"), expr_to_sexp(expr.pairs),
                      type_to_sexp(expr.key_type), type_to_sexp(expr.value_type)))

    elif isinstance(expr, DictLookup):
        if expr.default is None:
            return SList((SAtom("dict-lookup"), expr_to_sexp(expr.dict_expr),
                          expr_to_sexp(expr.key)))
        else:
            return SList((SAtom("dict-lookup"), expr_to_sexp(expr.dict_expr),
                          expr_to_sexp(expr.key), expr_to_sexp(expr.default)))

    elif isinstance(expr, HasField):
        return SList((SAtom("has-field"), expr_to_sexp(expr.message),
                      SAtom(expr.field_name)))

    else:
        raise SExprConversionError(f"Unknown expression: {type(expr).__name__}")


def constructor_to_sexp(expr: Lambda) -> SExpr:
    """Convert a Lambda to an s-expression using 'construct' keyword.

    This is used for rule constructors, which use the 'construct' keyword
    instead of 'lambda' in the s-expression syntax.

    Args:
        expr: Lambda expression to convert

    Returns:
        S-expression using (construct ...) form
    """
    from .sexp import SAtom, SList

    params = SList(tuple(
        SList((SAtom(p.name), type_to_sexp(p.type))) for p in expr.params
    ))
    return SList((SAtom("construct"), params, type_to_sexp(expr.return_type),
                  expr_to_sexp(expr.body)))


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
    'constructor_to_sexp',
]
