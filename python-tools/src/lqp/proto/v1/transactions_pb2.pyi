from lqp.proto.v1 import fragments_pb2 as _fragments_pb2
from lqp.proto.v1 import logic_pb2 as _logic_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Transaction(_message.Message):
    __slots__ = ("epochs",)
    EPOCHS_FIELD_NUMBER: _ClassVar[int]
    epochs: _containers.RepeatedCompositeFieldContainer[Epoch]
    def __init__(self, epochs: _Optional[_Iterable[_Union[Epoch, _Mapping]]] = ...) -> None: ...

class Epoch(_message.Message):
    __slots__ = ("persistent_writes", "local_writes", "reads")
    PERSISTENT_WRITES_FIELD_NUMBER: _ClassVar[int]
    LOCAL_WRITES_FIELD_NUMBER: _ClassVar[int]
    READS_FIELD_NUMBER: _ClassVar[int]
    persistent_writes: _containers.RepeatedCompositeFieldContainer[Write]
    local_writes: _containers.RepeatedCompositeFieldContainer[Write]
    reads: _containers.RepeatedCompositeFieldContainer[Read]
    def __init__(self, persistent_writes: _Optional[_Iterable[_Union[Write, _Mapping]]] = ..., local_writes: _Optional[_Iterable[_Union[Write, _Mapping]]] = ..., reads: _Optional[_Iterable[_Union[Read, _Mapping]]] = ...) -> None: ...

class Write(_message.Message):
    __slots__ = ("define", "undefine", "context")
    DEFINE_FIELD_NUMBER: _ClassVar[int]
    UNDEFINE_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    define: Define
    undefine: Undefine
    context: Context
    def __init__(self, define: _Optional[_Union[Define, _Mapping]] = ..., undefine: _Optional[_Union[Undefine, _Mapping]] = ..., context: _Optional[_Union[Context, _Mapping]] = ...) -> None: ...

class Define(_message.Message):
    __slots__ = ("fragment",)
    FRAGMENT_FIELD_NUMBER: _ClassVar[int]
    fragment: _fragments_pb2.Fragment
    def __init__(self, fragment: _Optional[_Union[_fragments_pb2.Fragment, _Mapping]] = ...) -> None: ...

class Undefine(_message.Message):
    __slots__ = ("fragment_id",)
    FRAGMENT_ID_FIELD_NUMBER: _ClassVar[int]
    fragment_id: _fragments_pb2.FragmentId
    def __init__(self, fragment_id: _Optional[_Union[_fragments_pb2.FragmentId, _Mapping]] = ...) -> None: ...

class Context(_message.Message):
    __slots__ = ("relations",)
    RELATIONS_FIELD_NUMBER: _ClassVar[int]
    relations: _containers.RepeatedCompositeFieldContainer[_logic_pb2.RelationId]
    def __init__(self, relations: _Optional[_Iterable[_Union[_logic_pb2.RelationId, _Mapping]]] = ...) -> None: ...

class Read(_message.Message):
    __slots__ = ("demand", "output", "what_if", "abort")
    DEMAND_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    WHAT_IF_FIELD_NUMBER: _ClassVar[int]
    ABORT_FIELD_NUMBER: _ClassVar[int]
    demand: Demand
    output: Output
    what_if: WhatIf
    abort: Abort
    def __init__(self, demand: _Optional[_Union[Demand, _Mapping]] = ..., output: _Optional[_Union[Output, _Mapping]] = ..., what_if: _Optional[_Union[WhatIf, _Mapping]] = ..., abort: _Optional[_Union[Abort, _Mapping]] = ...) -> None: ...

class Demand(_message.Message):
    __slots__ = ("relation_id",)
    RELATION_ID_FIELD_NUMBER: _ClassVar[int]
    relation_id: _logic_pb2.RelationId
    def __init__(self, relation_id: _Optional[_Union[_logic_pb2.RelationId, _Mapping]] = ...) -> None: ...

class Output(_message.Message):
    __slots__ = ("name", "relation_id")
    NAME_FIELD_NUMBER: _ClassVar[int]
    RELATION_ID_FIELD_NUMBER: _ClassVar[int]
    name: str
    relation_id: _logic_pb2.RelationId
    def __init__(self, name: _Optional[str] = ..., relation_id: _Optional[_Union[_logic_pb2.RelationId, _Mapping]] = ...) -> None: ...

class WhatIf(_message.Message):
    __slots__ = ("branch", "epoch")
    BRANCH_FIELD_NUMBER: _ClassVar[int]
    EPOCH_FIELD_NUMBER: _ClassVar[int]
    branch: str
    epoch: Epoch
    def __init__(self, branch: _Optional[str] = ..., epoch: _Optional[_Union[Epoch, _Mapping]] = ...) -> None: ...

class Abort(_message.Message):
    __slots__ = ("name", "relation_id")
    NAME_FIELD_NUMBER: _ClassVar[int]
    RELATION_ID_FIELD_NUMBER: _ClassVar[int]
    name: str
    relation_id: _logic_pb2.RelationId
    def __init__(self, name: _Optional[str] = ..., relation_id: _Optional[_Union[_logic_pb2.RelationId, _Mapping]] = ...) -> None: ...
