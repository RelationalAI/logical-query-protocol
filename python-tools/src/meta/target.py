"""Abstract syntax tree for semantic actions.

This module defines the AST for semantic actions that can be attached to
grammar rules. Actions are expressions that compute values from parsed elements.

The action expression AST types represent the "least common denominator" for
Python, Julia, and Go expressions. All constructs in this AST should be easily
translatable to each of these target languages. This design ensures that semantic
actions can be generated in any of the supported languages without loss of
expressiveness or idiomatic style.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TargetNode:
    """Base class for all target language AST nodes."""
    pass


@dataclass
class TargetExpr(TargetNode):
    """Base class for target language expressions."""
    pass


@dataclass
class Wildcard(TargetExpr):
    """Wildcard parameter (_) that ignores its value."""

    def __str__(self) -> str:
        return "_"


@dataclass
class Var(TargetExpr):
    """Variable reference."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Symbol(TargetExpr):
    """Literal symbol (e.g., :cast)."""
    name: str

    def __str__(self) -> str:
        return f":{self.name}"


@dataclass
class Call(TargetExpr):
    """Function call."""
    name: str
    args: List['TargetExpr'] = field(default_factory=list)

    def __str__(self) -> str:
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"{self.name}({args_str})"


@dataclass
class Lambda(TargetExpr):
    """Lambda function (anonymous function)."""
    params: List[str] = field(default_factory=list)
    body: Optional['TargetExpr'] = None
    return_type: Optional['Type'] = None

    def __str__(self) -> str:
        params_str = ', '.join(self.params)
        ret_str = f" -> {self.return_type}" if self.return_type else ""
        return f"lambda {params_str}{ret_str}: {self.body}"


@dataclass
class Let(TargetExpr):
    """Let-binding: let var = init in body.

    Evaluates init, binds the result to var, then evaluates body
    in the extended environment.
    """
    var: str
    init: 'TargetExpr'
    body: 'TargetExpr'
    init_type: Optional['Type'] = None  # Type of init

    def __str__(self) -> str:
        type_str = f": {self.init_type}" if self.init_type else ""
        return f"let {self.var}{type_str} = {self.init} in {self.body}"


@dataclass
class Type(TargetNode):
    """Base class for type expressions."""
    pass


@dataclass
class BaseType(Type):
    """Base types: Int64, Float64, String, Boolean."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class TupleType(Type):
    """Tuple type with fixed number of element types."""
    elements: List[Type] = field(default_factory=list)

    def __str__(self) -> str:
        elements_str = ', '.join(str(e) for e in self.elements)
        return f"({elements_str})"


@dataclass
class ListType(Type):
    """Parameterized list/array type."""
    element_type: Type

    def __str__(self) -> str:
        return f"List[{self.element_type}]"


@dataclass
class FunDef(TargetNode):
    """Function definition with parameters, return type, and body."""
    name: str
    params: List[tuple[str, Type]] = field(default_factory=list)
    return_type: Optional[Type] = None
    body: Optional['TargetExpr'] = None

    def __str__(self) -> str:
        params_str = ', '.join(f"{name}: {typ}" for name, typ in self.params)
        ret_str = f" -> {self.return_type}" if self.return_type else ""
        return f"def {self.name}({params_str}){ret_str}: {self.body}"


# Re-export all types for convenience
__all__ = [
    'TargetNode',
    'TargetExpr',
    'Wildcard',
    'Var',
    'Symbol',
    'Call',
    'Lambda',
    'Let',
    'Type',
    'BaseType',
    'TupleType',
    'ListType',
    'FunDef',
]
