"""Python-style pretty printer for target IR types and expressions.

This module provides functions to convert TargetType and TargetExpr objects
to Python-like string representations.
"""

from .target import (
    TargetType, BaseType, VarType, MessageType, ListType, DictType,
    OptionType, TupleType, FunctionType,
    TargetExpr, Var, Lit, Symbol, Builtin, NamedFun, NewMessage, OneOf,
    ListExpr, Call, Lambda, Let, IfElse, Seq, While, Foreach, ForeachEnumerated,
    Assign, Return, GetField, GetElement, DictFromList, DictLookup, HasProtoField,
    VisitNonterminal, FunDef
)


def type_to_str(typ: TargetType) -> str:
    """Convert a TargetType to a Python-style string.

    Examples:
        BaseType("String") -> "String"
        MessageType("logic", "Value") -> "logic.Value"
        ListType(BaseType("Int64")) -> "List[Int64]"
        OptionType(BaseType("String")) -> "Optional[String]"
        TupleType([BaseType("Int64"), BaseType("String")]) -> "Tuple[Int64, String]"
    """
    if isinstance(typ, BaseType):
        return typ.name

    elif isinstance(typ, VarType):
        return typ.name

    elif isinstance(typ, MessageType):
        return f"{typ.module}.{typ.name}"

    elif isinstance(typ, ListType):
        return f"List[{type_to_str(typ.element_type)}]"

    elif isinstance(typ, DictType):
        return f"Dict[{type_to_str(typ.key_type)}, {type_to_str(typ.value_type)}]"

    elif isinstance(typ, OptionType):
        return f"Optional[{type_to_str(typ.element_type)}]"

    elif isinstance(typ, TupleType):
        elems = ", ".join(type_to_str(e) for e in typ.elements)
        return f"Tuple[{elems}]"

    elif isinstance(typ, FunctionType):
        params = ", ".join(type_to_str(p) for p in typ.param_types)
        return f"Callable[[{params}], {type_to_str(typ.return_type)}]"

    else:
        return str(typ)


def expr_to_str(expr: TargetExpr) -> str:
    """Convert a TargetExpr to a Python-style string.

    Examples:
        Var("x", Int64) -> "x"
        Lit(42) -> "42"
        Call(Builtin("add"), [Var("x"), Lit(1)]) -> "add(x, 1)"
        NewMessage("logic", "Value", [("int_value", Var("x"))]) -> "logic.Value(int_value=x)"
    """
    if isinstance(expr, Var):
        return expr.name

    elif isinstance(expr, Lit):
        if isinstance(expr.value, str):
            return repr(expr.value)
        elif isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        else:
            return str(expr.value)

    elif isinstance(expr, Symbol):
        return f":{expr.name}"

    elif isinstance(expr, Builtin):
        return f"builtin.{expr.name}"

    elif isinstance(expr, NamedFun):
        return expr.name

    elif isinstance(expr, NewMessage):
        fields = ", ".join(f"{name}={expr_to_str(val)}" for name, val in expr.fields)
        return f"{expr.module}.{expr.name}({fields})"

    elif isinstance(expr, OneOf):
        return f"oneof({expr.field_name})"

    elif isinstance(expr, ListExpr):
        elems = ", ".join(expr_to_str(e) for e in expr.elements)
        return f"[{elems}]"

    elif isinstance(expr, Call):
        func_str = expr_to_str(expr.func)
        args_str = ", ".join(expr_to_str(a) for a in expr.args)
        return f"{func_str}({args_str})"

    elif isinstance(expr, Lambda):
        params = ", ".join(f"{p.name}" for p in expr.params)
        return f"lambda {params}: {expr_to_str(expr.body)}"

    elif isinstance(expr, Let):
        return f"(let {expr.var.name} = {expr_to_str(expr.init)} in {expr_to_str(expr.body)})"

    elif isinstance(expr, IfElse):
        return f"({expr_to_str(expr.then_branch)} if {expr_to_str(expr.condition)} else {expr_to_str(expr.else_branch)})"

    elif isinstance(expr, Seq):
        exprs = "; ".join(expr_to_str(e) for e in expr.exprs)
        return f"seq({exprs})"

    elif isinstance(expr, While):
        return f"while {expr_to_str(expr.condition)}: {expr_to_str(expr.body)}"

    elif isinstance(expr, Foreach):
        return f"for {expr.var.name} in {expr_to_str(expr.collection)}: {expr_to_str(expr.body)}"

    elif isinstance(expr, ForeachEnumerated):
        return f"for {expr.index_var.name}, {expr.var.name} in enumerate({expr_to_str(expr.collection)}): {expr_to_str(expr.body)}"

    elif isinstance(expr, Assign):
        return f"{expr.var.name} = {expr_to_str(expr.expr)}"

    elif isinstance(expr, Return):
        return f"return {expr_to_str(expr.expr)}"

    elif isinstance(expr, GetField):
        return f"{expr_to_str(expr.object)}.{expr.field_name}"

    elif isinstance(expr, GetElement):
        return f"{expr_to_str(expr.tuple_expr)}[{expr.index}]"

    elif isinstance(expr, DictFromList):
        return f"dict({expr_to_str(expr.pairs)})"

    elif isinstance(expr, DictLookup):
        if expr.default is not None:
            return f"{expr_to_str(expr.dict_expr)}.get({expr_to_str(expr.key)}, {expr_to_str(expr.default)})"
        else:
            return f"{expr_to_str(expr.dict_expr)}.get({expr_to_str(expr.key)})"

    elif isinstance(expr, HasProtoField):
        return f"{expr_to_str(expr.message)}.HasField({repr(expr.field_name)})"

    elif isinstance(expr, VisitNonterminal):
        return f"visit_{expr.nonterminal.name}()"

    else:
        return str(expr)


def fundef_to_str(func: FunDef) -> str:
    """Convert a FunDef to a Python-style function definition string."""
    params = ", ".join(f"{p.name}: {type_to_str(p.type)}" for p in func.params)
    if func.body is not None:
        return f"def {func.name}({params}) -> {type_to_str(func.return_type)}:\n    return {expr_to_str(func.body)}"
    else:
        return f"def {func.name}({params}) -> {type_to_str(func.return_type)}:\n    ..."
