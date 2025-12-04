"""Abstract syntax tree for target language code.

This module defines the AST for target language expressions, including generated parser code,
and semantic actions that can be attached to grammar rules.

The target AST types represent the "least common denominator" for
Python, Julia, and Go expressions. All constructs in this AST should be easily
translatable to each of these target languages.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .grammar import Nonterminal


@dataclass
class TargetNode:
    """Base class for all target language AST nodes."""
    pass


@dataclass
class TargetExpr(TargetNode):
    """Base class for target language expressions."""
    pass



@dataclass
class Var(TargetExpr):
    """Variable reference."""
    name: str

    def __str__(self) -> str:
        return self.name

    def __post_init__(self):
        assert isinstance(self.name, str), f"Invalid name in {self}: {self.name}"
        if not self.name.isidentifier():
            raise ValueError(f"Invalid variable name: {self.name}")


@dataclass
class Lit(TargetExpr):
    """Literal value (string, number, boolean, None)."""
    value: Any

    def __str__(self) -> str:
        return repr(self.value)

@dataclass
class Symbol(TargetExpr):
    """Literal symbol (e.g., :cast)."""
    name: str

    def __str__(self) -> str:
        return f":{self.name}"

    def __post_init__(self):
        assert isinstance(self.name, str), f"Invalid name in {self}: {self.name}"
        if not self.name.isidentifier():
            raise ValueError(f"Invalid variable name: {self.name}")

@dataclass
class Builtin(TargetExpr):
    """Builtin function reference.

    Represents a built-in function provided by the runtime/parser framework.
    Examples: consume, consume_terminal, match_terminal, parse_X methods
    Code generators map these to the appropriate syntax (e.g., self.consume in Python).
    """
    name: str

    def __str__(self) -> str:
        return f"%{self.name}"

    def __post_init__(self):
        assert isinstance(self.name, str), f"Invalid name in {self}: {self.name}"
        if not self.name.isidentifier():
            raise ValueError(f"Invalid variable name: {self.name}")

@dataclass
class Constructor(TargetExpr):
    """Constructor call.

    name: Name of the type/constructor
    """
    name: str

    def __str__(self) -> str:
        return f"@{self.name}"

    def __post_init__(self):
        assert isinstance(self.name, str), f"Invalid name in {self}: {self.name}"
        if not self.name.isidentifier():
            raise ValueError(f"Invalid variable name: {self.name}")

@dataclass
class Call(TargetExpr):
    """Function call expression.

    func: Expression that evaluates to the function to call (typically Var or Symbol)
    args: List of argument expressions
    """
    func: 'TargetExpr'
    args: Sequence['TargetExpr'] = field(default_factory=list)

    def __str__(self) -> str:
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"{self.func}({args_str})"

    def __post_init__(self):
        assert isinstance(self.func, TargetExpr), f"Invalid function expression in {self}: {self.func}"
        assert isinstance(self.args, list), f"Invalid argument list in {self}: {self.args}"
        for arg in self.args:
            assert isinstance(arg, TargetExpr), f"Invalid argument expression in {self}: {arg}"


@dataclass
class Lambda(TargetExpr):
    """Lambda function (anonymous function)."""
    # TODO: params should have types
    params: Sequence[str]
    body: 'TargetExpr'
    return_type: Optional['Type'] = None

    def __str__(self) -> str:
        params_str = ', '.join(self.params)
        ret_str = f" -> {self.return_type}" if self.return_type else ""
        return f"lambda {params_str}{ret_str}: {self.body}"

    def __post_init__(self):
        assert isinstance(self.body, TargetExpr), f"Invalid function expression in {self}: {self.body}"
        if self.return_type is not None:
            assert isinstance(self.return_type, Type), f"Invalid function return type in {self}: {self.return_type}"
        for param in self.params:
            assert isinstance(param, str), f"Invalid parameter name in {self}: {param}"

@dataclass
class Let(TargetExpr):
    """Let-binding: let var = init in body.

    Evaluates init, binds the result to var, then evaluates body
    in the extended environment.
    """
    var: str
    init: 'TargetExpr'
    body: 'TargetExpr'
    # TODO PR make the Type non-optional
    init_type: Optional['Type'] = None  # Type of init

    def __str__(self) -> str:
        type_str = f": {self.init_type}" if self.init_type else ""
        return f"let {self.var}{type_str} = {self.init} in {self.body}"

    def __post_init__(self):
        assert isinstance(self.init, TargetExpr), f"Invalid let init expression in {self}: {self.init}"
        assert isinstance(self.body, TargetExpr), f"Invalid let body expression in {self}: {self.body}"
        if self.init_type is not None:
            assert isinstance(self.init_type, Type), f"Invalid let init type in {self}: {self.init_type}"

@dataclass
class IfElse(TargetExpr):
    """If-else conditional expression."""
    condition: TargetExpr
    then_branch: TargetExpr
    else_branch: TargetExpr

    def __str__(self) -> str:
        return f"if {self.condition} then {self.then_branch} else {self.else_branch}"

    def __post_init__(self):
        assert isinstance(self.condition, TargetExpr), f"Invalid if condition expression in {self}: {self.condition}"
        assert isinstance(self.then_branch, TargetExpr), f"Invalid if then expression in {self}: {self.then_branch}"
        assert isinstance(self.else_branch, TargetExpr), f"Invalid if else expression in {self}: {self.else_branch}"

@dataclass
class Seq(TargetExpr):
    """Sequence of expressions evaluated in order, returns last value."""
    exprs: Sequence['TargetExpr'] = field(default_factory=list)

    def __str__(self) -> str:
        return "; ".join(str(e) for e in self.exprs)

    def __post_init__(self):
        assert isinstance(self.exprs, list), f"Invalid sequence of expressions in {self}: {self.exprs}"
        assert len(self.exprs) > 1, f"Sequence must contain at least two expressions"
        for expr in self.exprs[:-1]:
            assert isinstance(expr, TargetExpr), f"Invalid statement in sequence: {expr}"
        assert isinstance(self.exprs[-1], TargetExpr), f"Invalid expression in sequence: {self.exprs[-1]}"


@dataclass
class While(TargetExpr):
    """While loop: while condition do body."""
    condition: TargetExpr
    body: TargetExpr

    def __str__(self) -> str:
        return f"while {self.condition} do {self.body}"

    def __post_init__(self):
        assert isinstance(self.condition, TargetExpr), f"Invalid while condition expression in {self}: {self.condition}"
        assert isinstance(self.body, TargetExpr), f"Invalid while body expression in {self}: {self.body}"

@dataclass
class TryCatch(TargetExpr):
    """Try-catch exception handling."""
    try_body: TargetExpr
    catch_body: TargetExpr
    exception_type: Optional[str] = None

    def __str__(self) -> str:
        exc_str = f" {self.exception_type}" if self.exception_type else ""
        return f"try {self.try_body} catch{exc_str} {self.catch_body}"


@dataclass
class Assign(TargetExpr):
    """Assignment statement: var = expr.

    Returns None after performing the assignment.
    """
    var: str
    expr: TargetExpr

    def __str__(self) -> str:
        return f"{self.var} = {self.expr}"

    def __post_init__(self):
        assert isinstance(self.var, str), f"Invalid assign LHS expression in {self}: {self.var}"
        assert isinstance(self.expr, TargetExpr), f"Invalid assign RHS expression in {self}: {self.expr}"


@dataclass
class Return(TargetExpr):
    """Return statement: return expr."""
    expr: TargetExpr

    def __str__(self) -> str:
        return f"return {self.expr}"

    def __post_init__(self):
        assert isinstance(self.expr, TargetExpr), f"Invalid return expression in {self}: {self.expr}"


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
class MessageType(Type):
    """Protobuf message types."""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class TupleType(Type):
    """Tuple type with fixed number of element types."""
    elements: Sequence[Type] = field(default_factory=list)

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
    params: Sequence[tuple[str, Type]] = field(default_factory=list)
    return_type: Optional[Type] = None
    body: Optional['TargetExpr'] = None

    def __str__(self) -> str:
        params_str = ', '.join(f"{name}: {typ}" for name, typ in self.params)
        ret_str = f" -> {self.return_type}" if self.return_type else ""
        return f"def {self.name}({params_str}){ret_str}: {self.body}"


@dataclass
class ParseNonterminalDef(TargetNode):
    """Parse method definition for a nonterminal.

    Like FunDef but specifically for parser methods, with a Nonterminal
    instead of a string name.
    """
    nonterminal: 'Nonterminal'
    params: Sequence[tuple[str, Type]] = field(default_factory=list)
    return_type: Optional[Type] = None
    body: Optional['TargetExpr'] = None

    def __str__(self) -> str:
        params_str = ', '.join(f"{name}: {typ}" for name, typ in self.params)
        ret_str = f" -> {self.return_type}" if self.return_type else ""
        return f"parse {self.nonterminal}({params_str}){ret_str}: {self.body}"


@dataclass
class ParseNonterminal(TargetExpr):
    """Parse method call for a nonterminal.

    Like Call but specifically for calling parser methods, with a Nonterminal
    instead of an expression for the function.
    """
    nonterminal: 'Nonterminal'
    args: Sequence['TargetExpr'] = field(default_factory=list)

    def __str__(self) -> str:
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"parse {self.nonterminal}({args_str})"


# Re-export all types for convenience
__all__ = [
    'TargetNode',
    'TargetExpr',
    'Var',
    'Lit',
    'Symbol',
    'Builtin',
    'Constructor',
    'Call',
    'Lambda',
    'Let',
    'IfElse',
    'Seq',
    'While',
    'TryCatch',
    'Assign',
    'Return',
    'Type',
    'BaseType',
    'TupleType',
    'ListType',
    'FunDef',
    'ParseNonterminalDef',
    'ParseNonterminal',
]
