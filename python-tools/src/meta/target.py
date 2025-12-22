"""Abstract syntax tree for target language code.

This module defines the AST for target language expressions, including generated parser code,
and semantic actions that can be attached to grammar rules.

The target AST types represent the "least common denominator" for
Python, Julia, and Go expressions. All constructs in this AST should be easily
translatable to each of these target languages.
"""

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional, Sequence, TYPE_CHECKING, Iterator
from itertools import count

if TYPE_CHECKING:
    from .grammar import Nonterminal

_global_id: Iterator[int] = count(0)
def next_id():
    return next(_global_id)

def gensym(prefix: str = "_t") -> str:
    return f"{prefix}{next_id()}"

@dataclass(frozen=True)
class TargetNode:
    """Base class for all target language AST nodes."""
    pass

@dataclass(frozen=True)
class TargetExpr(TargetNode):
    """Base class for target language expressions."""
    pass

@dataclass(frozen=True)
class Var(TargetExpr):
    """Variable reference."""
    name: str
    type: 'TargetType'

    def __str__(self) -> str:
        return f"{self.name}::{self.type}"

    def __post_init__(self):
        if not self.name.isidentifier():
            raise ValueError(f"Invalid variable name: {self.name}")

@dataclass(frozen=True)
class Lit(TargetExpr):
    """Literal value (string, number, boolean, None)."""
    value: Any

    def __str__(self) -> str:
        return repr(self.value)

@dataclass(frozen=True)
class Symbol(TargetExpr):
    """Literal symbol (e.g., :cast)."""
    name: str

    def __str__(self) -> str:
        return f":{self.name}"

    def __post_init__(self):
        if not self.name.isidentifier():
            raise ValueError(f"Invalid variable name: {self.name}")

@dataclass(frozen=True)
class Builtin(TargetExpr):
    """Builtin function reference.

    Represents a built-in function provided by the runtime/parser framework.
    Examples: consume, consume_terminal, match_terminal, parse_X methods
    Code generators map these to the appropriate syntax (e.g., self.consume in Python).
    """
    name: str

    def __str__(self) -> str:
        return f"%{self.name}"


@dataclass(frozen=True)
class Message(TargetExpr):
    """Message constructor call.

    module: Module name (protobuf file stem)
    name: Name of the message type
    """
    module: str
    name: str

    def __str__(self) -> str:
        return f"@{self.module}.{self.name}"

    def __post_init__(self):
        if not self.module.isidentifier():
            raise ValueError(f"Invalid message module: {self.module}")
        if not self.name.isidentifier():
            raise ValueError(f"Invalid message name: {self.name}")


@dataclass(frozen=True)
class OneOf(TargetExpr):
    """OneOf field discriminator.

    field_name: str representing the field name
    Call this with a value to create a oneof field: Call(OneOf('field'), [value])
    """
    field_name: str

    def __str__(self) -> str:
        return f"OneOf({self.field_name})"


@dataclass(frozen=True)
class ListExpr(TargetExpr):
    """List constructor expression.

    Creates a list with the given elements and element type.
    """
    elements: Sequence['TargetExpr']
    element_type: 'TargetType'

    def __str__(self) -> str:
        if not self.elements:
            return f"List[{self.element_type}]()"
        elements_str = ', '.join(str(e) for e in self.elements)
        return f"List[{self.element_type}]({elements_str})"

    def __post_init__(self):
        if isinstance(self.elements, list):
            object.__setattr__(self, 'elements', tuple(self.elements))
        assert isinstance(self.elements, tuple), f"Invalid elements in {self}: {self.elements}"


@dataclass(frozen=True)
class VisitNonterminal(TargetExpr):
    """Visitor method call for a nonterminal.

    Like Call but specifically for calling visitor methods, with a Nonterminal
    instead of an expression for the function.
    """
    visitor_name: str  # e.g., 'parse', 'pretty'
    nonterminal: 'Nonterminal'

    def __str__(self) -> str:
        return f"{self.visitor_name}_{self.nonterminal.name}"


@dataclass(frozen=True)
class Call(TargetExpr):
    """Function call expression.

    func: Expression that evaluates to the function to call (typically Var or Symbol)
    args: List of argument expressions
    """
    func: 'TargetExpr'
    args: Sequence['TargetExpr'] = field(default_factory=tuple)

    def __str__(self) -> str:
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"{self.func}({args_str})"

    def __post_init__(self):
        if isinstance(self.args, list):
            object.__setattr__(self, 'args', tuple(self.args))
        assert isinstance(self.args, tuple), f"Invalid argument list in {self}: {self.args}"


@dataclass(frozen=True)
class Lambda(TargetExpr):
    """Lambda function (anonymous function)."""
    params: Sequence['Var']
    return_type: 'TargetType'
    body: 'TargetExpr'

    def __str__(self) -> str:
        params_str = ', '.join(str(p) for p in self.params)
        return f"lambda {params_str} -> {self.return_type}: {self.body}"

    def __post_init__(self):
        if isinstance(self.params, list):
            object.__setattr__(self, 'params', tuple(self.params))
        assert isinstance(self.params, tuple), f"Invalid parameter list in {self}: {self.params}"

@dataclass(frozen=True)
class Let(TargetExpr):
    """Let-binding: let var = init in body.

    Evaluates init, binds the result to var, then evaluates body
    in the extended environment.
    """
    var: 'Var'
    init: 'TargetExpr'
    body: 'TargetExpr'

    def __str__(self) -> str:
        type_str = f": {self.var.type}" if self.var.type else ""
        return f"let {self.var.name}{type_str} = {self.init} in {self.body}"


@dataclass(frozen=True)
class IfElse(TargetExpr):
    """If-else conditional expression."""
    condition: TargetExpr
    then_branch: TargetExpr
    else_branch: TargetExpr

    def __str__(self) -> str:
        if self.then_branch == Lit(True):
            return f"{self.condition} or {self.else_branch}"
        elif self.else_branch == Lit(False):
            return f"{self.condition} and {self.then_branch}"
        else:
            return f"if ({self.condition}) then {self.then_branch} else {self.else_branch}"


@dataclass(frozen=True)
class Seq(TargetExpr):
    """Sequence of expressions evaluated in order, returns last value."""
    exprs: Sequence['TargetExpr'] = field(default_factory=tuple)

    def __str__(self) -> str:
        return "; ".join(str(e) for e in self.exprs)

    def __post_init__(self):
        if isinstance(self.exprs, list):
            object.__setattr__(self, 'exprs', tuple(self.exprs))
        assert isinstance(self.exprs, tuple), f"Invalid sequence of expressions in {self}: {self.exprs}"
        assert len(self.exprs) > 1, f"Sequence must contain at least two expressions"


@dataclass(frozen=True)
class While(TargetExpr):
    """While loop: while condition do body."""
    condition: TargetExpr
    body: TargetExpr

    def __str__(self) -> str:
        return f"while ({self.condition}) {self.body}"

@dataclass(frozen=True)
class Foreach(TargetExpr):
    """Foreach loop: for var in collection do body."""
    var: 'Var'
    collection: TargetExpr
    body: TargetExpr

    def __str__(self) -> str:
        return f"for {self.var.name} in {self.collection} do {self.body}"

@dataclass(frozen=True)
class ForeachEnumerated(TargetExpr):
    """Foreach loop with index: for index_var, var in enumerate(collection) do body."""
    index_var: 'Var'
    var: 'Var'
    collection: TargetExpr
    body: TargetExpr

    def __str__(self) -> str:
        return f"for {self.index_var.name}, {self.var.name} in enumerate({self.collection}) do {self.body}"

@dataclass(frozen=True)
class Assign(TargetExpr):
    """Assignment statement: var = expr.

    Returns None after performing the assignment.
    """
    var: 'Var'
    expr: TargetExpr

    def __str__(self) -> str:
        return f"{self.var.name} = {self.expr}"

@dataclass(frozen=True)
class Return(TargetExpr):
    """Return statement: return expr."""
    expr: TargetExpr

    def __str__(self) -> str:
        return f"return {self.expr}"

    def __post_init__(self):
        assert isinstance(self.expr, TargetExpr) and not isinstance(self.expr, Return), f"Invalid return expression in {self}: {self.expr}"


@dataclass(frozen=True)
class TargetType(TargetNode):
    """Base class for type expressions."""
    pass


@dataclass(frozen=True)
class BaseType(TargetType):
    """Base types: Int64, Float64, String, Boolean."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class MessageType(TargetType):
    """Protobuf message types."""
    module: str
    name: str

    def __str__(self) -> str:
        return f"{self.module}.{self.name}"


@dataclass(frozen=True)
class TupleType(TargetType):
    """Tuple type with fixed number of element types."""
    elements: Sequence[TargetType]

    def __str__(self) -> str:
        elements_str = ', '.join(str(e) for e in self.elements)
        return f"({elements_str})"

    def __post_init__(self):
        if isinstance(self.elements, list):
            object.__setattr__(self, 'elements', tuple(self.elements))
        assert isinstance(self.elements, tuple), f"Invalid tuple elements in {self}: {self.elements}"


@dataclass(frozen=True)
class ListType(TargetType):
    """Parameterized list/array type."""
    element_type: TargetType

    def __str__(self) -> str:
        return f"List[{self.element_type}]"


@dataclass(frozen=True)
class OptionType(TargetType):
    """Optional/Maybe type for values that may be None."""
    element_type: TargetType

    def __str__(self) -> str:
        return f"Option[{self.element_type}]"


@dataclass(frozen=True)
class FunctionType(TargetType):
    """Function type with parameter types and return type."""
    param_types: Sequence[TargetType]
    return_type: TargetType

    def __str__(self) -> str:
        params_str = ', '.join(str(t) for t in self.param_types)
        return f"({params_str}) -> {self.return_type}"

    def __post_init__(self):
        if isinstance(self.param_types, list):
            object.__setattr__(self, 'param_types', tuple(self.param_types))
        assert isinstance(self.param_types, tuple), f"Invalid parameter types in {self}: {self.param_types}"


@dataclass(frozen=True)
class FunDef(TargetNode):
    """Function definition with parameters, return type, and body."""
    name: str
    params: Sequence['Var']
    return_type: TargetType
    body: 'TargetExpr'

    def __str__(self) -> str:
        params_str = ', '.join(f"{p.name}: {p.type}" for p in self.params)
        return f"def {self.name}({params_str}) -> {self.return_type}: {self.body}"

    def __post_init__(self):
        if isinstance(self.params, list):
            object.__setattr__(self, 'params', tuple(self.params))
        assert isinstance(self.params, tuple), f"Invalid params types in {self}: {self.params}"


@dataclass(frozen=True)
class VisitNonterminalDef(TargetNode):
    """Visitor method definition for a nonterminal.

    Like FunDef but specifically for visitor methods, with a Nonterminal
    instead of a string name.
    """
    visitor_name: str  # e.g., 'parse', 'pretty'
    nonterminal: 'Nonterminal'
    params: Sequence['Var']
    return_type: TargetType
    body: 'TargetExpr'

    def __str__(self) -> str:
        params_str = ', '.join(f"{p.name}: {p.type}" for p in self.params)
        return f"{self.visitor_name}_{self.nonterminal.name}({params_str}) -> {self.return_type}: {self.body}"

    def __post_init__(self):
        if isinstance(self.params, list):
            object.__setattr__(self, 'params', tuple(self.params))
        assert isinstance(self.params, tuple), f"Invalid params types in {self}: {self.params}"

def create_identity_function(param_type: 'TargetType') -> 'Lambda':
    """Create an identity function: lambda x -> x with the given type.

    Args:
        param_type: The type of the parameter and return value

    Returns:
        Lambda expression representing the identity function
    """
    param = Var('x', param_type)
    return Lambda([param], param_type, param)

def create_identity_option_function(param_type: 'TargetType') -> 'Lambda':
    """Create an identity function: lambda x -> Some(x) with the given type.

    Args:
        param_type: The type of the parameter and return value element type

    Returns:
        Lambda expression representing the identity function
    """
    param = Var('x', param_type)
    return Lambda([param], OptionType(param_type), Call(Builtin('Some'), [param]))


def _is_simple_expr(expr: 'TargetExpr') -> bool:
    """Check if an expression is cheap to evaluate and has no side effects."""
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


def _count_var_occurrences(expr: 'TargetExpr', var: str) -> int:
    """Count occurrences of a variable in an expression."""
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


def _new_mapping(mapping: Mapping[str, 'TargetExpr'], shadowed: List[str]):
    if shadowed:
        return {k: v for k, v in mapping.items() if k not in shadowed}
    return mapping


def _subst_inner(expr: 'TargetExpr', mapping: Mapping[str, 'TargetExpr']) -> 'TargetExpr':
    """Inner substitution helper - performs actual substitution."""
    if isinstance(expr, Var) and expr.name in mapping:
        return mapping[expr.name]
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


def subst(expr: 'TargetExpr', mapping: Mapping[str, 'TargetExpr']) -> 'TargetExpr':
    """Substitute variables with values in expression.

    Args:
        expr: Expression to substitute into
        mapping: Map from variable names to replacement expressions

    Returns:
        Expression with substitutions applied. If a value has side effects
        and its variable occurs more than once, introduces a Let binding
        to avoid duplicating side effects.
    """
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
            fresh_var = Var(gensym('subst'), val.type if isinstance(val, Var) else BaseType('Any'))
            lets_needed.append((fresh_var, val))
            simple_mapping[var] = fresh_var

    result = _subst_inner(expr, simple_mapping)

    # Wrap in Let bindings for side-effecting values
    for fresh_var, val in lets_needed:
        result = Let(fresh_var, val, result)

    return result


def apply_lambda(func: 'Lambda', args: Sequence['TargetExpr']) -> 'TargetExpr':
    """Apply a lambda to arguments, inlining where possible.

    If all args are simple (Var or Lit), substitutes directly.
    Otherwise, generates Let bindings.

    Args:
        func: Lambda to apply
        args: Arguments to apply

    Returns:
        Expression with lambda applied
    """
    if len(args) == 0 and len(func.params) == 0:
        return func.body
    if len(func.params) > 0 and len(args) > 0:
        body = apply_lambda(Lambda(params=func.params[1:], return_type=func.return_type, body=func.body), args[1:])
        if isinstance(args[0], (Var, Lit)):
            return subst(body, {func.params[0].name: args[0]})
        return Let(func.params[0], args[0], body)
    return Call(func, args)


__all__ = [
    'TargetNode',
    'TargetExpr',
    'Var',
    'Lit',
    'Symbol',
    'Builtin',
    'Message',
    'OneOf',
    'ListExpr',
    'Call',
    'Lambda',
    'Let',
    'IfElse',
    'Seq',
    'While',
    'Foreach',
    'ForeachEnumerated',
    'Assign',
    'Return',
    'TargetType',
    'BaseType',
    'MessageType',
    'TupleType',
    'ListType',
    'OptionType',
    'FunctionType',
    'FunDef',
    'VisitNonterminalDef',
    'VisitNonterminal',
    'gensym',
    'create_identity_function',
    'create_identity_option_function',
    'apply_lambda',
    'subst',
]
