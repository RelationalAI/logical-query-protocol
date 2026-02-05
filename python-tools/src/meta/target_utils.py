"""Utility functions and common type definitions for target language constructs.

This module provides utilities for working with the target language AST,
including:
- Common type constants (STRING_TYPE, INT64_TYPE, etc.)
- Expression substitution with proper handling of side effects
- Helper functions for constructing common builtin calls
- Lambda application with inlining optimization

The substitution function is particularly important for grammar transformations,
as it correctly handles variables with multiple occurrences and side-effecting
expressions by introducing Let bindings when necessary.

Example:
    >>> from meta.target import Var, Lit, Call, Builtin
    >>> from meta.target_utils import subst, make_equal, STRING_TYPE
    >>> # Substitute variable 'x' with literal "hello"
    >>> expr = Call(Builtin('print'), [Var('x', STRING_TYPE)])
    >>> subst(expr, {'x': Lit("hello")})
    Call(Builtin('print'), [Lit("hello")])
"""

from typing import Mapping, Sequence

from .target import (
    BaseType, Builtin, Lambda, Var, Lit, Call, TargetExpr, TargetType,
    ListType, OptionType, TupleType, VarType
)
from .target_builtins import make_builtin


def is_subtype(t1: TargetType, t2: TargetType) -> bool:
    """Check if t1 is a subtype of t2 (t1 <: t2).

    Subtyping rules:
    - Reflexivity: T <: T
    - Never <: T for all T (Never is the bottom type)
    - T <: Any for all T (Any is the top type)
    - T <: VarType for all T (type variables are wildcards)
    - List is covariant: List[A] <: List[B] if A <: B
    - Option is covariant: Option[A] <: Option[B] if A <: B
    - Tuple is covariant: (A1, A2, ...) <: (B1, B2, ...) if Ai <: Bi for all i
    """
    if t1 == t2:
        return True
    # Never is a subtype of everything (bottom type)
    if isinstance(t1, BaseType) and t1.name == "Never":
        return True
    # T <: Any for all T (Any is the top type)
    if isinstance(t2, BaseType) and t2.name == "Any":
        return True
    # T <: VarType for all T (type variables are wildcards)
    if isinstance(t2, VarType):
        return True
    # List is covariant: List[A] <: List[B] if A <: B
    if isinstance(t1, ListType) and isinstance(t2, ListType):
        return is_subtype(t1.element_type, t2.element_type)
    # Option is covariant: Option[A] <: Option[B] if A <: B
    if isinstance(t1, OptionType) and isinstance(t2, OptionType):
        return is_subtype(t1.element_type, t2.element_type)
    # Tuple is covariant: check element-wise
    if isinstance(t1, TupleType) and isinstance(t2, TupleType):
        if len(t1.elements) != len(t2.elements):
            return False
        return all(is_subtype(e1, e2) for e1, e2 in zip(t1.elements, t2.elements))
    return False


# Common types used throughout grammar generation
# These correspond to protobuf primitive types
STRING_TYPE = BaseType('String')     # string, bytes
INT64_TYPE = BaseType('Int64')       # int32, int64, uint32, uint64, fixed64
FLOAT64_TYPE = BaseType('Float64')   # double, float
BOOLEAN_TYPE = BaseType('Boolean')   # bool

def create_identity_function(param_type: TargetType) -> Lambda:
    """Create an identity function: lambda x -> x with the given type.

    Args:
        param_type: The type of the parameter and return value

    Returns:
        Lambda expression representing the identity function
    """
    param = Var('x', param_type)
    return Lambda([param], param_type, param)





def _is_simple_expr(expr: TargetExpr) -> bool:
    """Check if an expression is cheap to evaluate and has no side effects."""
    from .target import IfElse, Let
    if isinstance(expr, (Var, Lit)):
        return True
    if isinstance(expr, Call):
        if not all(_is_simple_expr(arg) for arg in expr.args):
            return False
        if isinstance(expr.func, Builtin):
            return expr.func.name in ('equal', 'greater', 'not_equal', 'Some', 'is_none', 'unwrap_option_or')
    if isinstance(expr, IfElse):
        return _is_simple_expr(expr.condition) and _is_simple_expr(expr.then_branch) and _is_simple_expr(expr.else_branch)
    if isinstance(expr, Let):
        return _is_simple_expr(expr.init) and _is_simple_expr(expr.body)
    return False


def _count_var_occurrences(expr: TargetExpr, var: str) -> int:
    """Count occurrences of a variable in an expression."""
    from .target import Let, Foreach, ForeachEnumerated, Assign, Seq, IfElse, While, Return
    if isinstance(expr, Var) and expr.name == var:
        return 1
    elif isinstance(expr, Lambda):
        if var in [p.name for p in expr.params]:
            return 0
        return _count_var_occurrences(expr.body, var)
    elif isinstance(expr, Let):
        if expr.var.name == var:
            return _count_var_occurrences(expr.init, var)
        return _count_var_occurrences(expr.init, var) + _count_var_occurrences(expr.body, var)
    elif isinstance(expr, Foreach):
        if expr.var.name == var:
            return _count_var_occurrences(expr.collection, var)
        return _count_var_occurrences(expr.collection, var) + _count_var_occurrences(expr.body, var)
    elif isinstance(expr, ForeachEnumerated):
        if expr.var.name == var or expr.index_var.name == var:
            return _count_var_occurrences(expr.collection, var)
        return _count_var_occurrences(expr.collection, var) + _count_var_occurrences(expr.body, var)
    elif isinstance(expr, Assign):
        return _count_var_occurrences(expr.expr, var)
    elif isinstance(expr, Call):
        count = _count_var_occurrences(expr.func, var)
        for arg in expr.args:
            count += _count_var_occurrences(arg, var)
        return count
    elif isinstance(expr, Seq):
        count = 0
        for e in expr.exprs:
            count += _count_var_occurrences(e, var)
        return count
    elif isinstance(expr, IfElse):
        return (_count_var_occurrences(expr.condition, var) +
                _count_var_occurrences(expr.then_branch, var) +
                _count_var_occurrences(expr.else_branch, var))
    elif isinstance(expr, While):
        return _count_var_occurrences(expr.condition, var) + _count_var_occurrences(expr.body, var)
    elif isinstance(expr, Return):
        return _count_var_occurrences(expr.expr, var)
    return 0


def _new_mapping(mapping: Mapping[str, TargetExpr], shadowed: list[str]):
    if shadowed:
        return {k: v for k, v in mapping.items() if k not in shadowed}
    return mapping


def _subst_inner(expr: TargetExpr, mapping: Mapping[str, TargetExpr]) -> TargetExpr:
    """Inner substitution helper - performs actual substitution."""
    from .target import Let, Foreach, ForeachEnumerated, Assign, Seq, IfElse, While, Return
    if isinstance(expr, Var) and expr.name in mapping:
        val = mapping[expr.name]
        assert is_subtype(val.target_type(), expr.type), \
            f"Type mismatch in subst: {expr.name} has type {expr.type} but value has type {val.target_type()}"
        return val
    elif isinstance(expr, Lambda):
        shadowed = [p.name for p in expr.params if p.name in mapping]
        new_mapping = _new_mapping(mapping, shadowed)
        return Lambda(params=expr.params, return_type=expr.return_type, body=_subst_inner(expr.body, new_mapping))
    elif isinstance(expr, Let):
        new_mapping = _new_mapping(mapping, [expr.var.name])
        return Let(expr.var, _subst_inner(expr.init, mapping), _subst_inner(expr.body, new_mapping))
    elif isinstance(expr, Foreach):
        new_mapping = _new_mapping(mapping, [expr.var.name])
        return Foreach(expr.var, _subst_inner(expr.collection, mapping), _subst_inner(expr.body, new_mapping))
    elif isinstance(expr, ForeachEnumerated):
        new_mapping = _new_mapping(mapping, [expr.var.name, expr.index_var.name])
        return ForeachEnumerated(expr.index_var, expr.var, _subst_inner(expr.collection, mapping), _subst_inner(expr.body, new_mapping))
    elif isinstance(expr, Assign):
        return Assign(expr.var, _subst_inner(expr.expr, mapping))
    elif isinstance(expr, Call):
        return Call(_subst_inner(expr.func, mapping), [_subst_inner(arg, mapping) for arg in expr.args])
    elif isinstance(expr, Seq):
        return Seq([_subst_inner(arg, mapping) for arg in expr.exprs])
    elif isinstance(expr, IfElse):
        return IfElse(_subst_inner(expr.condition, mapping), _subst_inner(expr.then_branch, mapping), _subst_inner(expr.else_branch, mapping))
    elif isinstance(expr, While):
        return While(_subst_inner(expr.condition, mapping), _subst_inner(expr.body, mapping))
    elif isinstance(expr, Return):
        return Return(_subst_inner(expr.expr, mapping))
    return expr


def subst(expr: TargetExpr, mapping: Mapping[str, TargetExpr]) -> TargetExpr:
    """Substitute variables with values in expression.

    Args:
        expr: Expression to substitute into
        mapping: Map from variable names to replacement expressions

    Returns:
        Expression with substitutions applied. If a value has side effects
        and its variable occurs more than once, introduces a Let binding
        to avoid duplicating side effects.
    """
    from .target import Let
    from .gensym import gensym
    if not mapping:
        return expr

    # Check for side effects and multiple occurrences
    lets_needed = []
    simple_mapping = {}

    for var, val in mapping.items():
        occurrences = _count_var_occurrences(expr, var)
        if occurrences == 0:
            continue
        elif occurrences == 1 or _is_simple_expr(val):
            simple_mapping[var] = val
        else:
            # Multiple occurrences and val has side effects - need Let
            fresh_var = Var(gensym('subst'), val.target_type())
            lets_needed.append((fresh_var, val))
            simple_mapping[var] = fresh_var

    result = _subst_inner(expr, simple_mapping)

    # Wrap in Let bindings for side-effecting values
    for fresh_var, val in lets_needed:
        result = Let(fresh_var, val, result)

    return result


# Common Builtin functions that return Call instances
# These functions construct calls to builtin operations that must be
# implemented by the target language runtime

def make_equal(left, right):
    """Construct equality test: left == right."""
    return Call(make_builtin('equal'), [left, right])

def make_which_oneof(msg, oneof_name):
    """Get which field is set in a oneof group."""
    return Call(make_builtin('which_one_of'), [msg, oneof_name])

def make_get_field(obj, field_name, message_type, field_type):
    """Get field value from message: obj.field_name."""
    from .target import GetField
    # If field_name is a Lit, extract the string value
    if isinstance(field_name, Lit):
        field_name = field_name.value
    return GetField(obj, field_name, message_type, field_type)

def make_some(value):
    """Wrap value in Option/Maybe: Some(value)."""
    return Call(make_builtin('some'), [value])

def make_tuple(*args):
    """Construct tuple from values: (arg1, arg2, ...)."""
    return Call(make_builtin('tuple'), list(args))

def make_get_element(tuple_expr, index):
    """Extract element from tuple at constant index: tuple_expr[index]."""
    from .target import GetElement
    return GetElement(tuple_expr, index)

def make_fst(pair):
    """Extract first element of tuple: pair[0]."""
    return make_get_element(pair, 0)

def make_snd(pair):
    """Extract second element of tuple: pair[1]."""
    return make_get_element(pair, 1)

def make_is_empty(collection):
    """Check if collection is empty: len(collection) == 0."""
    return Call(make_builtin('is_empty'), [collection])

def make_concat(left, right):
    """Concatenate two lists: left + right."""
    return Call(make_builtin('list_concat'), [left, right])

def make_length(collection):
    """Get collection length: len(collection)."""
    return Call(make_builtin('length'), [collection])

def make_unwrap_option_or(option, default):
    """Unwrap Option with default: option if Some(x) else default."""
    return Call(make_builtin('unwrap_option_or'), [option, default])


def apply_lambda(func: Lambda, args: Sequence[TargetExpr]) -> TargetExpr:
    """Apply a lambda to arguments, inlining where possible.

    If all args are simple (Var or Lit), substitutes directly.
    Otherwise, generates Let bindings.

    Args:
        func: Lambda to apply
        args: Arguments to apply

    Returns:
        Expression with lambda applied
    """
    from .target import Let
    if len(args) == 0 and len(func.params) == 0:
        return func.body
    if len(func.params) > 0 and len(args) > 0:
        body = apply_lambda(Lambda(params=func.params[1:], return_type=func.return_type, body=func.body), args[1:])
        if isinstance(args[0], (Var, Lit)):
            return subst(body, {func.params[0].name: args[0]})
        return Let(func.params[0], args[0], body)
    return Call(func, args)
