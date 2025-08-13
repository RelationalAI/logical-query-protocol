from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Declaration(_message.Message):
    __slots__ = ("algorithm",)
    DEF_FIELD_NUMBER: _ClassVar[int]
    ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    algorithm: Algorithm
    def __init__(self, algorithm: _Optional[_Union[Algorithm, _Mapping]] = ..., **kwargs) -> None: ...

class Def(_message.Message):
    __slots__ = ("name", "body", "attrs")
    NAME_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    ATTRS_FIELD_NUMBER: _ClassVar[int]
    name: RelationId
    body: Abstraction
    attrs: _containers.RepeatedCompositeFieldContainer[Attribute]
    def __init__(self, name: _Optional[_Union[RelationId, _Mapping]] = ..., body: _Optional[_Union[Abstraction, _Mapping]] = ..., attrs: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class Algorithm(_message.Message):
    __slots__ = ("body",)
    GLOBAL_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    body: Script
    def __init__(self, body: _Optional[_Union[Script, _Mapping]] = ..., **kwargs) -> None: ...

class Script(_message.Message):
    __slots__ = ("constructs",)
    CONSTRUCTS_FIELD_NUMBER: _ClassVar[int]
    constructs: _containers.RepeatedCompositeFieldContainer[Construct]
    def __init__(self, constructs: _Optional[_Iterable[_Union[Construct, _Mapping]]] = ...) -> None: ...

class Construct(_message.Message):
    __slots__ = ("loop", "instruction")
    LOOP_FIELD_NUMBER: _ClassVar[int]
    INSTRUCTION_FIELD_NUMBER: _ClassVar[int]
    loop: Loop
    instruction: Instruction
    def __init__(self, loop: _Optional[_Union[Loop, _Mapping]] = ..., instruction: _Optional[_Union[Instruction, _Mapping]] = ...) -> None: ...

class Loop(_message.Message):
    __slots__ = ("init", "body")
    INIT_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    init: _containers.RepeatedCompositeFieldContainer[Instruction]
    body: Script
    def __init__(self, init: _Optional[_Iterable[_Union[Instruction, _Mapping]]] = ..., body: _Optional[_Union[Script, _Mapping]] = ...) -> None: ...

class Instruction(_message.Message):
    __slots__ = ("assign", "upsert", "copy", "monoid_def", "monus_def")
    ASSIGN_FIELD_NUMBER: _ClassVar[int]
    UPSERT_FIELD_NUMBER: _ClassVar[int]
    BREAK_FIELD_NUMBER: _ClassVar[int]
    COPY_FIELD_NUMBER: _ClassVar[int]
    MONOID_DEF_FIELD_NUMBER: _ClassVar[int]
    MONUS_DEF_FIELD_NUMBER: _ClassVar[int]
    assign: Assign
    upsert: Upsert
    copy: Copy
    monoid_def: MonoidDef
    monus_def: MonusDef
    def __init__(self, assign: _Optional[_Union[Assign, _Mapping]] = ..., upsert: _Optional[_Union[Upsert, _Mapping]] = ..., copy: _Optional[_Union[Copy, _Mapping]] = ..., monoid_def: _Optional[_Union[MonoidDef, _Mapping]] = ..., monus_def: _Optional[_Union[MonusDef, _Mapping]] = ..., **kwargs) -> None: ...

class Assign(_message.Message):
    __slots__ = ("name", "body", "attrs")
    NAME_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    ATTRS_FIELD_NUMBER: _ClassVar[int]
    name: RelationId
    body: Abstraction
    attrs: _containers.RepeatedCompositeFieldContainer[Attribute]
    def __init__(self, name: _Optional[_Union[RelationId, _Mapping]] = ..., body: _Optional[_Union[Abstraction, _Mapping]] = ..., attrs: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class Upsert(_message.Message):
    __slots__ = ("name", "body", "attrs")
    NAME_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    ATTRS_FIELD_NUMBER: _ClassVar[int]
    name: RelationId
    body: Abstraction
    attrs: _containers.RepeatedCompositeFieldContainer[Attribute]
    def __init__(self, name: _Optional[_Union[RelationId, _Mapping]] = ..., body: _Optional[_Union[Abstraction, _Mapping]] = ..., attrs: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class Break(_message.Message):
    __slots__ = ("name", "body", "attrs")
    NAME_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    ATTRS_FIELD_NUMBER: _ClassVar[int]
    name: RelationId
    body: Abstraction
    attrs: _containers.RepeatedCompositeFieldContainer[Attribute]
    def __init__(self, name: _Optional[_Union[RelationId, _Mapping]] = ..., body: _Optional[_Union[Abstraction, _Mapping]] = ..., attrs: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class Copy(_message.Message):
    __slots__ = ("name", "body", "attrs")
    NAME_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    ATTRS_FIELD_NUMBER: _ClassVar[int]
    name: RelationId
    body: Abstraction
    attrs: _containers.RepeatedCompositeFieldContainer[Attribute]
    def __init__(self, name: _Optional[_Union[RelationId, _Mapping]] = ..., body: _Optional[_Union[Abstraction, _Mapping]] = ..., attrs: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class MonoidDef(_message.Message):
    __slots__ = ("monoid", "name", "body", "attrs")
    MONOID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    ATTRS_FIELD_NUMBER: _ClassVar[int]
    monoid: Monoid
    name: RelationId
    body: Abstraction
    attrs: _containers.RepeatedCompositeFieldContainer[Attribute]
    def __init__(self, monoid: _Optional[_Union[Monoid, _Mapping]] = ..., name: _Optional[_Union[RelationId, _Mapping]] = ..., body: _Optional[_Union[Abstraction, _Mapping]] = ..., attrs: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class MonusDef(_message.Message):
    __slots__ = ("monoid", "name", "body", "attrs")
    MONOID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    ATTRS_FIELD_NUMBER: _ClassVar[int]
    monoid: Monoid
    name: RelationId
    body: Abstraction
    attrs: _containers.RepeatedCompositeFieldContainer[Attribute]
    def __init__(self, monoid: _Optional[_Union[Monoid, _Mapping]] = ..., name: _Optional[_Union[RelationId, _Mapping]] = ..., body: _Optional[_Union[Abstraction, _Mapping]] = ..., attrs: _Optional[_Iterable[_Union[Attribute, _Mapping]]] = ...) -> None: ...

class Monoid(_message.Message):
    __slots__ = ("or_monoid", "min_monoid", "max_monoid", "sum_monoid")
    OR_MONOID_FIELD_NUMBER: _ClassVar[int]
    MIN_MONOID_FIELD_NUMBER: _ClassVar[int]
    MAX_MONOID_FIELD_NUMBER: _ClassVar[int]
    SUM_MONOID_FIELD_NUMBER: _ClassVar[int]
    or_monoid: OrMonoid
    min_monoid: MinMonoid
    max_monoid: MaxMonoid
    sum_monoid: SumMonoid
    def __init__(self, or_monoid: _Optional[_Union[OrMonoid, _Mapping]] = ..., min_monoid: _Optional[_Union[MinMonoid, _Mapping]] = ..., max_monoid: _Optional[_Union[MaxMonoid, _Mapping]] = ..., sum_monoid: _Optional[_Union[SumMonoid, _Mapping]] = ...) -> None: ...

class OrMonoid(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MinMonoid(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: Type
    def __init__(self, type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class MaxMonoid(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: Type
    def __init__(self, type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class SumMonoid(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: Type
    def __init__(self, type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class Binding(_message.Message):
    __slots__ = ("var", "type")
    VAR_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    var: Var
    type: Type
    def __init__(self, var: _Optional[_Union[Var, _Mapping]] = ..., type: _Optional[_Union[Type, _Mapping]] = ...) -> None: ...

class Abstraction(_message.Message):
    __slots__ = ("vars", "value")
    VARS_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    vars: _containers.RepeatedCompositeFieldContainer[Binding]
    value: Formula
    def __init__(self, vars: _Optional[_Iterable[_Union[Binding, _Mapping]]] = ..., value: _Optional[_Union[Formula, _Mapping]] = ...) -> None: ...

class Formula(_message.Message):
    __slots__ = ("exists", "reduce", "conjunction", "disjunction", "ffi", "atom", "pragma", "primitive", "rel_atom", "cast")
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    REDUCE_FIELD_NUMBER: _ClassVar[int]
    CONJUNCTION_FIELD_NUMBER: _ClassVar[int]
    DISJUNCTION_FIELD_NUMBER: _ClassVar[int]
    NOT_FIELD_NUMBER: _ClassVar[int]
    FFI_FIELD_NUMBER: _ClassVar[int]
    ATOM_FIELD_NUMBER: _ClassVar[int]
    PRAGMA_FIELD_NUMBER: _ClassVar[int]
    PRIMITIVE_FIELD_NUMBER: _ClassVar[int]
    REL_ATOM_FIELD_NUMBER: _ClassVar[int]
    CAST_FIELD_NUMBER: _ClassVar[int]
    exists: Exists
    reduce: Reduce
    conjunction: Conjunction
    disjunction: Disjunction
    ffi: FFI
    atom: Atom
    pragma: Pragma
    primitive: Primitive
    rel_atom: RelAtom
    cast: Cast
    def __init__(self, exists: _Optional[_Union[Exists, _Mapping]] = ..., reduce: _Optional[_Union[Reduce, _Mapping]] = ..., conjunction: _Optional[_Union[Conjunction, _Mapping]] = ..., disjunction: _Optional[_Union[Disjunction, _Mapping]] = ..., ffi: _Optional[_Union[FFI, _Mapping]] = ..., atom: _Optional[_Union[Atom, _Mapping]] = ..., pragma: _Optional[_Union[Pragma, _Mapping]] = ..., primitive: _Optional[_Union[Primitive, _Mapping]] = ..., rel_atom: _Optional[_Union[RelAtom, _Mapping]] = ..., cast: _Optional[_Union[Cast, _Mapping]] = ..., **kwargs) -> None: ...

class Exists(_message.Message):
    __slots__ = ("body",)
    BODY_FIELD_NUMBER: _ClassVar[int]
    body: Abstraction
    def __init__(self, body: _Optional[_Union[Abstraction, _Mapping]] = ...) -> None: ...

class Reduce(_message.Message):
    __slots__ = ("op", "body", "terms")
    OP_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    TERMS_FIELD_NUMBER: _ClassVar[int]
    op: Abstraction
    body: Abstraction
    terms: _containers.RepeatedCompositeFieldContainer[Term]
    def __init__(self, op: _Optional[_Union[Abstraction, _Mapping]] = ..., body: _Optional[_Union[Abstraction, _Mapping]] = ..., terms: _Optional[_Iterable[_Union[Term, _Mapping]]] = ...) -> None: ...

class Conjunction(_message.Message):
    __slots__ = ("args",)
    ARGS_FIELD_NUMBER: _ClassVar[int]
    args: _containers.RepeatedCompositeFieldContainer[Formula]
    def __init__(self, args: _Optional[_Iterable[_Union[Formula, _Mapping]]] = ...) -> None: ...

class Disjunction(_message.Message):
    __slots__ = ("args",)
    ARGS_FIELD_NUMBER: _ClassVar[int]
    args: _containers.RepeatedCompositeFieldContainer[Formula]
    def __init__(self, args: _Optional[_Iterable[_Union[Formula, _Mapping]]] = ...) -> None: ...

class Not(_message.Message):
    __slots__ = ("arg",)
    ARG_FIELD_NUMBER: _ClassVar[int]
    arg: Formula
    def __init__(self, arg: _Optional[_Union[Formula, _Mapping]] = ...) -> None: ...

class FFI(_message.Message):
    __slots__ = ("name", "args", "terms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    TERMS_FIELD_NUMBER: _ClassVar[int]
    name: str
    args: _containers.RepeatedCompositeFieldContainer[Abstraction]
    terms: _containers.RepeatedCompositeFieldContainer[Term]
    def __init__(self, name: _Optional[str] = ..., args: _Optional[_Iterable[_Union[Abstraction, _Mapping]]] = ..., terms: _Optional[_Iterable[_Union[Term, _Mapping]]] = ...) -> None: ...

class Atom(_message.Message):
    __slots__ = ("name", "terms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TERMS_FIELD_NUMBER: _ClassVar[int]
    name: RelationId
    terms: _containers.RepeatedCompositeFieldContainer[Term]
    def __init__(self, name: _Optional[_Union[RelationId, _Mapping]] = ..., terms: _Optional[_Iterable[_Union[Term, _Mapping]]] = ...) -> None: ...

class Pragma(_message.Message):
    __slots__ = ("name", "terms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TERMS_FIELD_NUMBER: _ClassVar[int]
    name: str
    terms: _containers.RepeatedCompositeFieldContainer[Term]
    def __init__(self, name: _Optional[str] = ..., terms: _Optional[_Iterable[_Union[Term, _Mapping]]] = ...) -> None: ...

class Primitive(_message.Message):
    __slots__ = ("name", "terms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TERMS_FIELD_NUMBER: _ClassVar[int]
    name: str
    terms: _containers.RepeatedCompositeFieldContainer[RelTerm]
    def __init__(self, name: _Optional[str] = ..., terms: _Optional[_Iterable[_Union[RelTerm, _Mapping]]] = ...) -> None: ...

class RelAtom(_message.Message):
    __slots__ = ("name", "terms")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TERMS_FIELD_NUMBER: _ClassVar[int]
    name: str
    terms: _containers.RepeatedCompositeFieldContainer[RelTerm]
    def __init__(self, name: _Optional[str] = ..., terms: _Optional[_Iterable[_Union[RelTerm, _Mapping]]] = ...) -> None: ...

class Cast(_message.Message):
    __slots__ = ("input", "result")
    INPUT_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    input: Term
    result: Term
    def __init__(self, input: _Optional[_Union[Term, _Mapping]] = ..., result: _Optional[_Union[Term, _Mapping]] = ...) -> None: ...

class RelTerm(_message.Message):
    __slots__ = ("specialized_value", "term")
    SPECIALIZED_VALUE_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    specialized_value: Value
    term: Term
    def __init__(self, specialized_value: _Optional[_Union[Value, _Mapping]] = ..., term: _Optional[_Union[Term, _Mapping]] = ...) -> None: ...

class Term(_message.Message):
    __slots__ = ("var", "constant")
    VAR_FIELD_NUMBER: _ClassVar[int]
    CONSTANT_FIELD_NUMBER: _ClassVar[int]
    var: Var
    constant: Value
    def __init__(self, var: _Optional[_Union[Var, _Mapping]] = ..., constant: _Optional[_Union[Value, _Mapping]] = ...) -> None: ...

class Var(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class Attribute(_message.Message):
    __slots__ = ("name", "args")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    name: str
    args: _containers.RepeatedCompositeFieldContainer[Value]
    def __init__(self, name: _Optional[str] = ..., args: _Optional[_Iterable[_Union[Value, _Mapping]]] = ...) -> None: ...

class RelationId(_message.Message):
    __slots__ = ("id_low", "id_high")
    ID_LOW_FIELD_NUMBER: _ClassVar[int]
    ID_HIGH_FIELD_NUMBER: _ClassVar[int]
    id_low: int
    id_high: int
    def __init__(self, id_low: _Optional[int] = ..., id_high: _Optional[int] = ...) -> None: ...

class Type(_message.Message):
    __slots__ = ("unspecified_type", "string_type", "int_type", "float_type", "uint128_type", "int128_type", "date_type", "datetime_type", "missing_type", "decimal_type", "boolean_type")
    UNSPECIFIED_TYPE_FIELD_NUMBER: _ClassVar[int]
    STRING_TYPE_FIELD_NUMBER: _ClassVar[int]
    INT_TYPE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_TYPE_FIELD_NUMBER: _ClassVar[int]
    UINT128_TYPE_FIELD_NUMBER: _ClassVar[int]
    INT128_TYPE_FIELD_NUMBER: _ClassVar[int]
    DATE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DATETIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    MISSING_TYPE_FIELD_NUMBER: _ClassVar[int]
    DECIMAL_TYPE_FIELD_NUMBER: _ClassVar[int]
    BOOLEAN_TYPE_FIELD_NUMBER: _ClassVar[int]
    unspecified_type: UnspecifiedType
    string_type: StringType
    int_type: IntType
    float_type: FloatType
    uint128_type: UInt128Type
    int128_type: Int128Type
    date_type: DateType
    datetime_type: DateTimeType
    missing_type: MissingType
    decimal_type: DecimalType
    boolean_type: BooleanType
    def __init__(self, unspecified_type: _Optional[_Union[UnspecifiedType, _Mapping]] = ..., string_type: _Optional[_Union[StringType, _Mapping]] = ..., int_type: _Optional[_Union[IntType, _Mapping]] = ..., float_type: _Optional[_Union[FloatType, _Mapping]] = ..., uint128_type: _Optional[_Union[UInt128Type, _Mapping]] = ..., int128_type: _Optional[_Union[Int128Type, _Mapping]] = ..., date_type: _Optional[_Union[DateType, _Mapping]] = ..., datetime_type: _Optional[_Union[DateTimeType, _Mapping]] = ..., missing_type: _Optional[_Union[MissingType, _Mapping]] = ..., decimal_type: _Optional[_Union[DecimalType, _Mapping]] = ..., boolean_type: _Optional[_Union[BooleanType, _Mapping]] = ...) -> None: ...

class UnspecifiedType(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StringType(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IntType(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FloatType(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UInt128Type(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Int128Type(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DateType(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DateTimeType(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MissingType(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DecimalType(_message.Message):
    __slots__ = ("precision", "scale")
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    precision: int
    scale: int
    def __init__(self, precision: _Optional[int] = ..., scale: _Optional[int] = ...) -> None: ...

class BooleanType(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Value(_message.Message):
    __slots__ = ("string_value", "int_value", "float_value", "uint128_value", "int128_value", "missing_value", "date_value", "datetime_value", "decimal_value", "boolean_value")
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT128_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT128_VALUE_FIELD_NUMBER: _ClassVar[int]
    MISSING_VALUE_FIELD_NUMBER: _ClassVar[int]
    DATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    DATETIME_VALUE_FIELD_NUMBER: _ClassVar[int]
    DECIMAL_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOLEAN_VALUE_FIELD_NUMBER: _ClassVar[int]
    string_value: str
    int_value: int
    float_value: float
    uint128_value: UInt128Value
    int128_value: Int128Value
    missing_value: MissingValue
    date_value: DateValue
    datetime_value: DateTimeValue
    decimal_value: DecimalValue
    boolean_value: bool
    def __init__(self, string_value: _Optional[str] = ..., int_value: _Optional[int] = ..., float_value: _Optional[float] = ..., uint128_value: _Optional[_Union[UInt128Value, _Mapping]] = ..., int128_value: _Optional[_Union[Int128Value, _Mapping]] = ..., missing_value: _Optional[_Union[MissingValue, _Mapping]] = ..., date_value: _Optional[_Union[DateValue, _Mapping]] = ..., datetime_value: _Optional[_Union[DateTimeValue, _Mapping]] = ..., decimal_value: _Optional[_Union[DecimalValue, _Mapping]] = ..., boolean_value: bool = ...) -> None: ...

class UInt128Value(_message.Message):
    __slots__ = ("low", "high")
    LOW_FIELD_NUMBER: _ClassVar[int]
    HIGH_FIELD_NUMBER: _ClassVar[int]
    low: int
    high: int
    def __init__(self, low: _Optional[int] = ..., high: _Optional[int] = ...) -> None: ...

class Int128Value(_message.Message):
    __slots__ = ("low", "high")
    LOW_FIELD_NUMBER: _ClassVar[int]
    HIGH_FIELD_NUMBER: _ClassVar[int]
    low: int
    high: int
    def __init__(self, low: _Optional[int] = ..., high: _Optional[int] = ...) -> None: ...

class MissingValue(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DateValue(_message.Message):
    __slots__ = ("year", "month", "day")
    YEAR_FIELD_NUMBER: _ClassVar[int]
    MONTH_FIELD_NUMBER: _ClassVar[int]
    DAY_FIELD_NUMBER: _ClassVar[int]
    year: int
    month: int
    day: int
    def __init__(self, year: _Optional[int] = ..., month: _Optional[int] = ..., day: _Optional[int] = ...) -> None: ...

class DateTimeValue(_message.Message):
    __slots__ = ("year", "month", "day", "hour", "minute", "second", "microsecond")
    YEAR_FIELD_NUMBER: _ClassVar[int]
    MONTH_FIELD_NUMBER: _ClassVar[int]
    DAY_FIELD_NUMBER: _ClassVar[int]
    HOUR_FIELD_NUMBER: _ClassVar[int]
    MINUTE_FIELD_NUMBER: _ClassVar[int]
    SECOND_FIELD_NUMBER: _ClassVar[int]
    MICROSECOND_FIELD_NUMBER: _ClassVar[int]
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    microsecond: int
    def __init__(self, year: _Optional[int] = ..., month: _Optional[int] = ..., day: _Optional[int] = ..., hour: _Optional[int] = ..., minute: _Optional[int] = ..., second: _Optional[int] = ..., microsecond: _Optional[int] = ...) -> None: ...

class DecimalValue(_message.Message):
    __slots__ = ("precision", "scale", "value")
    PRECISION_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    precision: int
    scale: int
    value: Int128Value
    def __init__(self, precision: _Optional[int] = ..., scale: _Optional[int] = ..., value: _Optional[_Union[Int128Value, _Mapping]] = ...) -> None: ...
