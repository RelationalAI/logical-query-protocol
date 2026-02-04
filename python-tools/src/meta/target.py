"""Abstract syntax tree for target language code.

This module defines the AST for target language expressions, including generated parser code,
and semantic actions that can be attached to grammar rules.

The target AST types represent the "least common denominator" for
Python, Julia, and Go expressions. All constructs in this AST should be easily
translatable to each of these target languages.

Expression types (TargetExpr subclasses):
    Var                 - Variable reference
    Lit                 - Literal value (string, number, boolean, None)
    Symbol              - Literal symbol (e.g., :cast)
    Builtin             - Builtin function reference
    NewMessage          - Message constructor with field names
    OneOf               - OneOf field discriminator
    ListExpr            - List constructor expression
    VisitNonterminal    - Visitor method call for a nonterminal
    Call                - Function call expression
    GetField            - Field access expression
    GetElement          - Tuple element access with constant integer index
    Lambda              - Lambda function (anonymous function)
    Let                 - Let-binding: let var = init in body
    IfElse              - If-else conditional expression
    Seq                 - Sequence of expressions evaluated in order
    While               - While loop: while condition do body
    Foreach             - Foreach loop: for var in collection do body
    ForeachEnumerated   - Foreach loop with index: for index_var, var in enumerate(collection) do body
    Assign              - Assignment statement: var = expr
    Return              - Return statement: return expr

Type expressions (TargetType subclasses):
    BaseType            - Base types: Int64, Float64, String, Boolean
    VarType             - Type variable for polymorphic types
    MessageType         - Protobuf message types
    TupleType           - Tuple type with fixed number of element types
    ListType            - Parameterized list/array type
    OptionType          - Optional/Maybe type for values that may be None
    FunctionType        - Function type with parameter types and return type
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence, TYPE_CHECKING
from .gensym import gensym

if TYPE_CHECKING:
    from .grammar import Nonterminal


def _freeze_sequence(obj: object, attr: str) -> None:
    """Convert a list attribute to tuple and validate it's a tuple.

    Used in __post_init__ to ensure sequence fields are immutable tuples.
    """
    val = getattr(obj, attr)
    if isinstance(val, list):
        object.__setattr__(obj, attr, tuple(val))
        val = getattr(obj, attr)
    assert isinstance(val, tuple), f"Invalid {attr} in {obj}: {val}"

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
    """Variable reference.

    Represents a reference to a variable by name with an associated type.

    Example:
        Var("x", BaseType("Int64"))  # x :: Int64
        Var("msg", MessageType("logic", "Expr"))  # msg :: logic.Expr
    """
    name: str
    type: 'TargetType'

    def __str__(self) -> str:
        return f"{self.name}::{self.type}"

    def __post_init__(self):
        if not self.name.isidentifier():
            raise ValueError(f"Invalid variable name: {self.name}")

@dataclass(frozen=True)
class Lit(TargetExpr):
    """Literal value (string, number, boolean, None).

    Example:
        Lit(42)         # integer literal
        Lit("hello")    # string literal
        Lit(True)       # boolean literal
        Lit(None)       # None/null literal
    """
    value: Any

    def __str__(self) -> str:
        return repr(self.value)

@dataclass(frozen=True)
class Symbol(TargetExpr):
    """Literal symbol (e.g., :cast).

    Symbols are used as enumeration-like values or tags in the target language.
    Similar to keywords or atoms in Lisp-like languages.

    Example:
        Symbol("add")       # :add
        Symbol("multiply")  # :multiply
        Symbol("cast")      # :cast
    """
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
class NamedFun(TargetExpr):
    """Named function reference.

    Represents a user-defined function from the grammar (defined with 'def').
    Unlike Builtin, these have IR definitions and are generated as methods.
    Code generators map these to method calls (e.g., self.function_name in Python).
    """
    name: str

    def __str__(self) -> str:
        return f"@{self.name}"


@dataclass(frozen=True)
class NewMessage(TargetExpr):
    """Message constructor with explicit field names.

    Constructs a protobuf message with named fields.
    This allows field name validation during grammar validation.

    module: Module name (protobuf file stem)
    name: Name of the message type
    fields: Sequence of (field_name, field_expr) pairs
    """
    module: str
    name: str
    fields: Sequence[tuple[str, 'TargetExpr']]

    def __str__(self) -> str:
        if not self.fields:
            return f"@{self.module}.{self.name}()"
        fields_str = ', '.join(f"{name}={expr}" for name, expr in self.fields)
        return f"@{self.module}.{self.name}({fields_str})"

    def __post_init__(self):
        if not self.module.isidentifier():
            raise ValueError(f"Invalid message module: {self.module}")
        if not self.name.isidentifier():
            raise ValueError(f"Invalid message name: {self.name}")
        for field_name, _ in self.fields:
            if not isinstance(field_name, str) or not field_name.isidentifier():
                raise ValueError(f"Invalid field name: {field_name}")
        _freeze_sequence(self, 'fields')


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
        _freeze_sequence(self, 'elements')


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
        _freeze_sequence(self, 'args')


@dataclass(frozen=True)
class GetField(TargetExpr):
    """Field access expression.

    Accesses a field from an object (typically a message).

    object: Expression evaluating to the object
    field_name: Name of the field to access (string)

    Example:
        GetField(Var("msg", MessageType("logic", "Expr")), "term")
    """
    object: 'TargetExpr'
    field_name: str

    def __str__(self) -> str:
        return f"{self.object}.{self.field_name}"


@dataclass(frozen=True)
class GetElement(TargetExpr):
    """Tuple element access with constant integer index.

    Accesses an element from a tuple expression using a compile-time constant index.

    tuple_expr: Expression evaluating to a tuple
    index: Constant integer index (0-based)

    Example:
        GetElement(Var("pair", TupleType([INT64, STRING])), 0)  # pair[0]
        GetElement(Var("pair", TupleType([INT64, STRING])), 1)  # pair[1]
    """
    tuple_expr: 'TargetExpr'
    index: int

    def __str__(self) -> str:
        return f"{self.tuple_expr}[{self.index}]"

    def __post_init__(self):
        assert isinstance(self.index, int) and self.index >= 0, f"GetElement index must be non-negative integer: {self.index}"


@dataclass(frozen=True)
class DictFromList(TargetExpr):
    """Construct dictionary from list of (key, value) tuples: dict(pairs).

    Converts a list of tuples into a dictionary/map.

    pairs: Expression evaluating to a list of (key, value) tuples
    key_type: Type of dictionary keys
    value_type: Type of dictionary values

    Example:
        DictFromList(
            Var("pairs", ListType(TupleType([STRING, INT64]))),
            BaseType("String"),
            BaseType("Int64")
        )
    """
    pairs: 'TargetExpr'
    key_type: 'TargetType'
    value_type: 'TargetType'

    def __str__(self) -> str:
        return f"dict({self.pairs})"


@dataclass(frozen=True)
class DictLookup(TargetExpr):
    """Dictionary lookup with optional default: dict.get(key, default).

    Looks up a key in a dictionary, returning a default value if not found.

    dict_expr: Expression evaluating to a dictionary
    key: Expression for the key to lookup
    default: Optional default value if key not found (None means return None)

    Example:
        DictLookup(
            Var("config", DictType(STRING, INT64)),
            Lit("timeout"),
            Lit(30)
        )
    """
    dict_expr: 'TargetExpr'
    key: 'TargetExpr'
    default: Optional['TargetExpr'] = None

    def __str__(self) -> str:
        if self.default is None:
            return f"{self.dict_expr}.get({self.key})"
        return f"{self.dict_expr}.get({self.key}, {self.default})"


@dataclass(frozen=True)
class HasField(TargetExpr):
    """Check if protobuf message has field set (for oneOf): msg.HasField(field_name).

    Checks whether a protobuf message has a particular field set, typically used
    for oneOf discriminators.

    message: Expression evaluating to a protobuf message
    field_name: Name of the field to check (string literal)

    Example:
        HasField(
            Var("msg", MessageType("logic", "Value")),
            "string_value"
        )
    """
    message: 'TargetExpr'
    field_name: str

    def __str__(self) -> str:
        return f"{self.message}.HasField({repr(self.field_name)})"


@dataclass(frozen=True)
class Lambda(TargetExpr):
    """Lambda function (anonymous function).

    Example:
        # lambda x, y -> Int64: x + y
        Lambda(
            params=[Var("x", INT64_TYPE), Var("y", INT64_TYPE)],
            return_type=INT64_TYPE,
            body=Call(Builtin("add"), [Var("x", INT64_TYPE), Var("y", INT64_TYPE)])
        )
    """
    params: Sequence['Var']
    return_type: 'TargetType'
    body: 'TargetExpr'

    def __str__(self) -> str:
        params_str = ', '.join(str(p) for p in self.params)
        return f"lambda {params_str} -> {self.return_type}: {self.body}"

    def __post_init__(self):
        _freeze_sequence(self, 'params')

@dataclass(frozen=True)
class Let(TargetExpr):
    """Let-binding: let var = init in body.

    Evaluates init, binds the result to var, then evaluates body
    in the extended environment.

    Example:
        # let x = 42 in x + 1
        Let(
            var=Var("x", INT64_TYPE),
            init=Lit(42),
            body=Call(Builtin("add"), [Var("x", INT64_TYPE), Lit(1)])
        )
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
        _freeze_sequence(self, 'exprs')
        assert len(self.exprs) > 1, "Sequence must contain at least two expressions"


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
    """Base types: Int64, Float64, String, Boolean.

    Example:
        BaseType("Int64")
        BaseType("String")
        BaseType("Boolean")
    """
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class BottomType(TargetType):
    """The bottom type (empty type with no values).

    Bottom is a subtype of every type. Used for:
    - None literal has type Optional[Bottom]
    - Empty list [] has type List[Bottom]

    With covariant type constructors:
    - Optional[Bottom] <: Optional[T] for any T
    - List[Bottom] <: List[T] for any T
    """

    def __str__(self) -> str:
        return "Bottom"


@dataclass(frozen=True)
class VarType(TargetType):
    """Type variable for polymorphic types.

    Represents a type parameter in polymorphic function signatures.
    Used for builtins like unwrap_option_or, etc.

    Example:
        VarType("T")    # Type variable T
        VarType("T1")   # Type variable T1
        VarType("T2")   # Type variable T2
    """
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class MessageType(TargetType):
    """Protobuf message types.

    Example:
        MessageType("logic", "Expr")       # logic.Expr
        MessageType("transactions", "Transaction")  # transactions.Transaction
    """
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
        _freeze_sequence(self, 'elements')


@dataclass(frozen=True)
class ListType(TargetType):
    """Parameterized list/array type.

    Example:
        ListType(BaseType("Int64"))              # List[Int64]
        ListType(MessageType("logic", "Expr"))   # List[logic.Expr]
    """
    element_type: TargetType

    def __str__(self) -> str:
        return f"List[{self.element_type}]"


@dataclass(frozen=True)
class DictType(TargetType):
    """Parameterized dictionary/map type.

    Example:
        DictType(BaseType("String"), BaseType("Int64"))     # Dict[String, Int64]
        DictType(BaseType("String"), MessageType("logic", "Value"))  # Dict[String, logic.Value]
    """
    key_type: TargetType
    value_type: TargetType

    def __str__(self) -> str:
        return f"Dict[{self.key_type}, {self.value_type}]"


@dataclass(frozen=True)
class OptionType(TargetType):
    """Optional/Maybe type for values that may be None.

    Example:
        OptionType(BaseType("String"))          # Option[String]
        OptionType(MessageType("logic", "Expr")) # Option[logic.Expr]
    """
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
        _freeze_sequence(self, 'param_types')


@dataclass(frozen=True)
class FunDef(TargetNode):
    """Function definition with parameters, return type, and body.

    If body is None, this represents a builtin signature (primitive without implementation).
    """
    name: str
    params: Sequence['Var']
    return_type: TargetType
    body: Optional['TargetExpr']

    def __str__(self) -> str:
        params_str = ', '.join(f"{p.name}: {p.type}" for p in self.params)
        if self.body is None:
            return f"def {self.name}({params_str}) -> {self.return_type}"
        return f"def {self.name}({params_str}) -> {self.return_type}: {self.body}"

    def __post_init__(self):
        _freeze_sequence(self, 'params')


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
    indent: str = ""  # base indentation for code generation

    def __str__(self) -> str:
        params_str = ', '.join(f"{p.name}: {p.type}" for p in self.params)
        return f"{self.visitor_name}_{self.nonterminal.name}({params_str}) -> {self.return_type}: {self.body}"

    def __post_init__(self):
        _freeze_sequence(self, 'params')


__all__ = [
    'TargetNode',
    'TargetExpr',
    'Var',
    'Lit',
    'Symbol',
    'Builtin',
    'NamedFun',
    'NewMessage',
    'OneOf',
    'ListExpr',
    'Call',
    'GetField',
    'GetElement',
    'DictFromList',
    'DictLookup',
    'HasField',
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
    'BottomType',
    'VarType',
    'MessageType',
    'TupleType',
    'ListType',
    'DictType',
    'OptionType',
    'FunctionType',
    'FunDef',
    'VisitNonterminalDef',
    'VisitNonterminal',
    'gensym',
]
