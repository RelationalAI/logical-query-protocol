from lqp.proto.v1 import logic_pb2 as _logic_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Fragment(_message.Message):
    __slots__ = ("id", "declarations", "debug_info")
    ID_FIELD_NUMBER: _ClassVar[int]
    DECLARATIONS_FIELD_NUMBER: _ClassVar[int]
    DEBUG_INFO_FIELD_NUMBER: _ClassVar[int]
    id: FragmentId
    declarations: _containers.RepeatedCompositeFieldContainer[_logic_pb2.Declaration]
    debug_info: DebugInfo
    def __init__(self, id: _Optional[_Union[FragmentId, _Mapping]] = ..., declarations: _Optional[_Iterable[_Union[_logic_pb2.Declaration, _Mapping]]] = ..., debug_info: _Optional[_Union[DebugInfo, _Mapping]] = ...) -> None: ...

class DebugInfo(_message.Message):
    __slots__ = ("ids", "orig_names")
    IDS_FIELD_NUMBER: _ClassVar[int]
    ORIG_NAMES_FIELD_NUMBER: _ClassVar[int]
    ids: _containers.RepeatedCompositeFieldContainer[_logic_pb2.RelationId]
    orig_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, ids: _Optional[_Iterable[_Union[_logic_pb2.RelationId, _Mapping]]] = ..., orig_names: _Optional[_Iterable[str]] = ...) -> None: ...

class FragmentId(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: bytes
    def __init__(self, id: _Optional[bytes] = ...) -> None: ...
