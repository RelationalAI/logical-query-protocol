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

    def target_type(self) -> 'TargetType':
        """Return the type of this expression."""
        raise NotImplementedError(f"target_type not implemented for {type(self).__name__}")

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

    def target_type(self) -> 'TargetType':
        return self.type

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

    def target_type(self) -> 'TargetType':
        if isinstance(self.value, bool):
            return BaseType("Boolean")
        if isinstance(self.value, int):
            return BaseType("Int64")
        if isinstance(self.value, float):
            return BaseType("Float64")
        if isinstance(self.value, str):
            return BaseType("String")
        if self.value is None:
            return OptionType(BaseType("Never"))
        raise ValueError(f"Cannot determine type of literal: {self.value!r}")

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

    def target_type(self) -> 'TargetType':
        return BaseType("Symbol")

@dataclass(frozen=True)
class Builtin(TargetExpr):
    """Builtin function reference.

    Represents a built-in function provided by the runtime/parser framework.
    Examples: consume, consume_terminal, match_terminal, parse_X methods
    Code generators map these to the appropriate syntax (e.g., self.consume in Python).
    """
    name: str
    type: 'FunctionType'

    def __str__(self) -> str:
        return f"%{self.name}"

    def target_type(self) -> 'TargetType':
        return self.type


@dataclass(frozen=True)
class NamedFun(TargetExpr):
    """Named function reference.

    Represents a user-defined function from the grammar (defined with 'def').
    Unlike Builtin, these have IR definitions and are generated as methods.
    Code generators map these to method calls (e.g., self.function_name in Python).
    """
    name: str
    type: 'FunctionType'

    def __str__(self) -> str:
        return f"@{self.name}"

    def target_type(self) -> 'TargetType':
        return self.type


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

    def target_type(self) -> 'TargetType':
        return MessageType(self.module, self.name)


@dataclass(frozen=True)
class EnumValue(TargetExpr):
    """Enum value reference: module.EnumName.VALUE_NAME

    Represents a reference to a protobuf enum value.

    module: Module name (protobuf file stem)
    enum_name: Name of the enum type
    value_name: Name of the enum value
    """
    module: str
    enum_name: str
    value_name: str

    def __str__(self) -> str:
        return f"{self.module}.{self.enum_name}.{self.value_name}"

    def target_type(self) -> 'TargetType':
        # EnumType is defined later in the file
        return EnumType(self.module, self.enum_name)  # noqa: F821


@dataclass(frozen=True)
class OneOf(TargetExpr):
    """OneOf field discriminator.

    field_name: str representing the field name
    type: FunctionType from the value type to the value type
    Call this with a value to create a oneof field: Call(OneOf('field', type), [value])
    """
    field_name: str
    type: 'FunctionType'

    def __str__(self) -> str:
        return f"OneOf({self.field_name})"

    def target_type(self) -> 'TargetType':
        return self.type


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

    def target_type(self) -> 'TargetType':
        return ListType(self.element_type)


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

    def target_type(self) -> 'TargetType':
        """Return the type of the nonterminal."""
        return self.nonterminal.target_type()


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

    def target_type(self) -> 'TargetType':
        # For VisitNonterminal, the type is the nonterminal's target type directly
        if isinstance(self.func, VisitNonterminal):
            return self.func.target_type()
        func_type = self.func.target_type()
        if isinstance(func_type, FunctionType):
            # Match parameter types against argument types to build type variable mapping
            mapping: dict[str, TargetType] = {}
            for param_type, arg in zip(func_type.param_types, self.args):
                match_types(param_type, arg.target_type(), mapping)
            # Substitute type variables in return type
            return subst_type(func_type.return_type, mapping)
        raise ValueError(f"Cannot determine return type of call to {self.func}")


@dataclass(frozen=True)
class GetField(TargetExpr):
    """Field access expression.

    Accesses a field from an object (typically a message).

    object: Expression evaluating to the object
    field_name: Name of the field to access (string)
    message_type: The expected message type of the object
    field_type: The type of the field being accessed

    Example:
        GetField(
            Var("msg", MessageType("logic", "Expr")),
            "term",
            MessageType("logic", "Expr"),
            MessageType("logic", "Term")
        )
    """
    object: 'TargetExpr'
    field_name: str
    message_type: 'MessageType'
    field_type: 'TargetType'

    def __str__(self) -> str:
        return f"{self.object}.{self.field_name}"

    def target_type(self) -> 'TargetType':
        return self.field_type


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

    def target_type(self) -> 'TargetType':
        tuple_type = self.tuple_expr.target_type()
        if isinstance(tuple_type, TupleType):
            if 0 <= self.index < len(tuple_type.elements):
                return tuple_type.elements[self.index]
            raise ValueError(f"Tuple index {self.index} out of range for {tuple_type}")
        raise ValueError(f"Cannot get element from non-tuple type: {tuple_type}")


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

    def target_type(self) -> 'TargetType':
        return FunctionType([p.type for p in self.params], self.return_type)

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

    def target_type(self) -> 'TargetType':
        return self.body.target_type()


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

    def target_type(self) -> 'TargetType':
        return self.then_branch.target_type()


@dataclass(frozen=True)
class Seq(TargetExpr):
    """Sequence of expressions evaluated in order, returns last value."""
    exprs: Sequence['TargetExpr'] = field(default_factory=tuple)

    def __str__(self) -> str:
        return "; ".join(str(e) for e in self.exprs)

    def __post_init__(self):
        _freeze_sequence(self, 'exprs')
        assert len(self.exprs) > 1, "Sequence must contain at least two expressions"

    def target_type(self) -> 'TargetType':
        return self.exprs[-1].target_type()


@dataclass(frozen=True)
class While(TargetExpr):
    """While loop: while condition do body."""
    condition: TargetExpr
    body: TargetExpr

    def __str__(self) -> str:
        return f"while ({self.condition}) {self.body}"

    def target_type(self) -> 'TargetType':
        return OptionType(BaseType("Never"))

@dataclass(frozen=True)
class Foreach(TargetExpr):
    """Foreach loop: for var in collection do body."""
    var: 'Var'
    collection: TargetExpr
    body: TargetExpr

    def __str__(self) -> str:
        return f"for {self.var.name} in {self.collection} do {self.body}"

    def target_type(self) -> 'TargetType':
        return OptionType(BaseType("Never"))

@dataclass(frozen=True)
class ForeachEnumerated(TargetExpr):
    """Foreach loop with index: for index_var, var in enumerate(collection) do body."""
    index_var: 'Var'
    var: 'Var'
    collection: TargetExpr
    body: TargetExpr

    def __str__(self) -> str:
        return f"for {self.index_var.name}, {self.var.name} in enumerate({self.collection}) do {self.body}"

    def target_type(self) -> 'TargetType':
        return OptionType(BaseType("Never"))

@dataclass(frozen=True)
class Assign(TargetExpr):
    """Assignment statement: var = expr.

    Returns None after performing the assignment.
    """
    var: 'Var'
    expr: TargetExpr

    def __str__(self) -> str:
        return f"{self.var.name} = {self.expr}"

    def target_type(self) -> 'TargetType':
        return OptionType(BaseType("Never"))

@dataclass(frozen=True)
class Return(TargetExpr):
    """Return statement: return expr."""
    expr: TargetExpr

    def __str__(self) -> str:
        return f"return {self.expr}"

    def __post_init__(self):
        assert isinstance(self.expr, TargetExpr) and not isinstance(self.expr, Return), f"Invalid return expression in {self}: {self.expr}"

    def target_type(self) -> 'TargetType':
        return self.expr.target_type()


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
class EnumType(TargetType):
    """Protobuf enum types.

    Example:
        EnumType("transactions", "MaintenanceLevel")
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


def subst_type(typ: 'TargetType', mapping: dict[str, 'TargetType']) -> 'TargetType':
    """Substitute type variables in a type according to the mapping."""
    if isinstance(typ, VarType):
        return mapping.get(typ.name, typ)
    if isinstance(typ, (BaseType, MessageType, EnumType)):
        return typ
    if isinstance(typ, ListType):
        return ListType(subst_type(typ.element_type, mapping))
    if isinstance(typ, OptionType):
        return OptionType(subst_type(typ.element_type, mapping))
    if isinstance(typ, DictType):
        return DictType(subst_type(typ.key_type, mapping), subst_type(typ.value_type, mapping))
    if isinstance(typ, TupleType):
        return TupleType([subst_type(t, mapping) for t in typ.elements])
    if isinstance(typ, FunctionType):
        return FunctionType(
            [subst_type(t, mapping) for t in typ.param_types],
            subst_type(typ.return_type, mapping)
        )
    return typ


def match_types(param_type: 'TargetType', arg_type: 'TargetType', mapping: dict[str, 'TargetType']) -> None:
    """Match a parameter type against an argument type, updating the type variable mapping.

    This performs simple unification: if param_type is a VarType, it binds to arg_type.
    For compound types, it recursively matches components.
    """
    if isinstance(param_type, VarType):
        if param_type.name not in mapping:
            mapping[param_type.name] = arg_type
        return
    if isinstance(param_type, ListType) and isinstance(arg_type, ListType):
        match_types(param_type.element_type, arg_type.element_type, mapping)
    elif isinstance(param_type, OptionType) and isinstance(arg_type, OptionType):
        match_types(param_type.element_type, arg_type.element_type, mapping)
    elif isinstance(param_type, DictType) and isinstance(arg_type, DictType):
        match_types(param_type.key_type, arg_type.key_type, mapping)
        match_types(param_type.value_type, arg_type.value_type, mapping)
    elif isinstance(param_type, TupleType) and isinstance(arg_type, TupleType):
        for p, a in zip(param_type.elements, arg_type.elements):
            match_types(p, a, mapping)
    elif isinstance(param_type, FunctionType) and isinstance(arg_type, FunctionType):
        for p, a in zip(param_type.param_types, arg_type.param_types):
            match_types(p, a, mapping)
        match_types(param_type.return_type, arg_type.return_type, mapping)


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

    def function_type(self) -> 'FunctionType':
        """Return the function type of this visitor method."""
        return FunctionType([p.type for p in self.params], self.return_type)


__all__ = [
    'TargetNode',
    'TargetExpr',
    'Var',
    'Lit',
    'Symbol',
    'Builtin',
    'NamedFun',
    'NewMessage',
    'EnumValue',
    'OneOf',
    'ListExpr',
    'Call',
    'GetField',
    'GetElement',
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
    'VarType',
    'MessageType',
    'EnumType',
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
