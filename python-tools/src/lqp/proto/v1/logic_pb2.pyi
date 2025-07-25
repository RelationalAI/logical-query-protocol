from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PrimitiveType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PRIMITIVE_TYPE_UNSPECIFIED: _ClassVar[PrimitiveType]
    PRIMITIVE_TYPE_STRING: _ClassVar[PrimitiveType]
    PRIMITIVE_TYPE_INT: _ClassVar[PrimitiveType]
    PRIMITIVE_TYPE_FLOAT: _ClassVar[PrimitiveType]
    PRIMITIVE_TYPE_UINT128: _ClassVar[PrimitiveType]
    PRIMITIVE_TYPE_INT128: _ClassVar[PrimitiveType]
    PRIMITIVE_TYPE_DATE: _ClassVar[PrimitiveType]
    PRIMITIVE_TYPE_DATETIME: _ClassVar[PrimitiveType]
    PRIMITIVE_TYPE_MISSING: _ClassVar[PrimitiveType]

class ParameterizedTypeName(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PARAMETERIZED_TYPE_NAME_UNSPECIFIED: _ClassVar[ParameterizedTypeName]
    PARAMETERIZED_TYPE_NAME_DECIMAL: _ClassVar[ParameterizedTypeName]
PRIMITIVE_TYPE_UNSPECIFIED: PrimitiveType
PRIMITIVE_TYPE_STRING: PrimitiveType
PRIMITIVE_TYPE_INT: PrimitiveType
PRIMITIVE_TYPE_FLOAT: PrimitiveType
PRIMITIVE_TYPE_UINT128: PrimitiveType
PRIMITIVE_TYPE_INT128: PrimitiveType
PRIMITIVE_TYPE_DATE: PrimitiveType
PRIMITIVE_TYPE_DATETIME: PrimitiveType
PRIMITIVE_TYPE_MISSING: PrimitiveType
PARAMETERIZED_TYPE_NAME_UNSPECIFIED: ParameterizedTypeName
PARAMETERIZED_TYPE_NAME_DECIMAL: ParameterizedTypeName

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
    type: RelType
    def __init__(self, type: _Optional[_Union[RelType, _Mapping]] = ...) -> None: ...

class MaxMonoid(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: RelType
    def __init__(self, type: _Optional[_Union[RelType, _Mapping]] = ...) -> None: ...

class SumMonoid(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: RelType
    def __init__(self, type: _Optional[_Union[RelType, _Mapping]] = ...) -> None: ...

class Binding(_message.Message):
    __slots__ = ("var", "type")
    VAR_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    var: Var
    type: RelType
    def __init__(self, var: _Optional[_Union[Var, _Mapping]] = ..., type: _Optional[_Union[RelType, _Mapping]] = ...) -> None: ...

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

class RelType(_message.Message):
    __slots__ = ("primitive_type", "parameterized_type")
    PRIMITIVE_TYPE_FIELD_NUMBER: _ClassVar[int]
    PARAMETERIZED_TYPE_FIELD_NUMBER: _ClassVar[int]
    primitive_type: PrimitiveType
    parameterized_type: ParameterizedType
    def __init__(self, primitive_type: _Optional[_Union[PrimitiveType, str]] = ..., parameterized_type: _Optional[_Union[ParameterizedType, _Mapping]] = ...) -> None: ...

class ParameterizedType(_message.Message):
    __slots__ = ("type_name", "parameters")
    TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    type_name: ParameterizedTypeName
    parameters: _containers.RepeatedCompositeFieldContainer[Value]
    def __init__(self, type_name: _Optional[_Union[ParameterizedTypeName, str]] = ..., parameters: _Optional[_Iterable[_Union[Value, _Mapping]]] = ...) -> None: ...

class Value(_message.Message):
    __slots__ = ("string_value", "int_value", "float_value", "uint128_value", "int128_value", "missing_value")
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    UINT128_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT128_VALUE_FIELD_NUMBER: _ClassVar[int]
    MISSING_VALUE_FIELD_NUMBER: _ClassVar[int]
    string_value: str
    int_value: int
    float_value: float
    uint128_value: UInt128
    int128_value: Int128
    missing_value: bool
    def __init__(self, string_value: _Optional[str] = ..., int_value: _Optional[int] = ..., float_value: _Optional[float] = ..., uint128_value: _Optional[_Union[UInt128, _Mapping]] = ..., int128_value: _Optional[_Union[Int128, _Mapping]] = ..., missing_value: bool = ...) -> None: ...

class UInt128(_message.Message):
    __slots__ = ("low", "high")
    LOW_FIELD_NUMBER: _ClassVar[int]
    HIGH_FIELD_NUMBER: _ClassVar[int]
    low: int
    high: int
    def __init__(self, low: _Optional[int] = ..., high: _Optional[int] = ...) -> None: ...

class Int128(_message.Message):
    __slots__ = ("low", "high")
    LOW_FIELD_NUMBER: _ClassVar[int]
    HIGH_FIELD_NUMBER: _ClassVar[int]
    low: int
    high: int
    def __init__(self, low: _Optional[int] = ..., high: _Optional[int] = ...) -> None: ...
