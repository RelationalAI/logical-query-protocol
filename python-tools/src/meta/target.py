"""Abstract syntax tree for target language code.

This module defines the AST for target language expressions, including generated parser code,
and semantic actions that can be attached to grammar rules.

The target AST types represent the "least common denominator" for
Python, Julia, and Go expressions. All constructs in this AST should be easily
translatable to each of these target languages.
"""

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional, Sequence, TYPE_CHECKING
from .gensym import gensym

if TYPE_CHECKING:
    from .grammar import Nonterminal

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
]
