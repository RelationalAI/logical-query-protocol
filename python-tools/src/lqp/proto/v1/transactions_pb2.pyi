from lqp.proto.v1 import fragments_pb2 as _fragments_pb2
from lqp.proto.v1 import logic_pb2 as _logic_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MaintenanceLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MAINTENANCE_LEVEL_UNSPECIFIED: _ClassVar[MaintenanceLevel]
    MAINTENANCE_LEVEL_OFF: _ClassVar[MaintenanceLevel]
    MAINTENANCE_LEVEL_AUTO: _ClassVar[MaintenanceLevel]
    MAINTENANCE_LEVEL_ALL: _ClassVar[MaintenanceLevel]
MAINTENANCE_LEVEL_UNSPECIFIED: MaintenanceLevel
MAINTENANCE_LEVEL_OFF: MaintenanceLevel
MAINTENANCE_LEVEL_AUTO: MaintenanceLevel
MAINTENANCE_LEVEL_ALL: MaintenanceLevel

class Transaction(_message.Message):
    __slots__ = ("epochs", "configure", "sync")
    EPOCHS_FIELD_NUMBER: _ClassVar[int]
    CONFIGURE_FIELD_NUMBER: _ClassVar[int]
    SYNC_FIELD_NUMBER: _ClassVar[int]
    epochs: _containers.RepeatedCompositeFieldContainer[Epoch]
    configure: Configure
    sync: Sync
    def __init__(self, epochs: _Optional[_Iterable[_Union[Epoch, _Mapping]]] = ..., configure: _Optional[_Union[Configure, _Mapping]] = ..., sync: _Optional[_Union[Sync, _Mapping]] = ...) -> None: ...

class Configure(_message.Message):
    __slots__ = ("semantics_version", "ivm_config")
    SEMANTICS_VERSION_FIELD_NUMBER: _ClassVar[int]
    IVM_CONFIG_FIELD_NUMBER: _ClassVar[int]
    semantics_version: int
    ivm_config: IVMConfig
    def __init__(self, semantics_version: _Optional[int] = ..., ivm_config: _Optional[_Union[IVMConfig, _Mapping]] = ...) -> None: ...

class IVMConfig(_message.Message):
    __slots__ = ("level",)
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    level: MaintenanceLevel
    def __init__(self, level: _Optional[_Union[MaintenanceLevel, str]] = ...) -> None: ...

class Sync(_message.Message):
    __slots__ = ("fragments",)
    FRAGMENTS_FIELD_NUMBER: _ClassVar[int]
    fragments: _containers.RepeatedCompositeFieldContainer[_fragments_pb2.FragmentId]
    def __init__(self, fragments: _Optional[_Iterable[_Union[_fragments_pb2.FragmentId, _Mapping]]] = ...) -> None: ...

class Epoch(_message.Message):
    __slots__ = ("writes", "reads")
    WRITES_FIELD_NUMBER: _ClassVar[int]
    READS_FIELD_NUMBER: _ClassVar[int]
    writes: _containers.RepeatedCompositeFieldContainer[Write]
    reads: _containers.RepeatedCompositeFieldContainer[Read]
    def __init__(self, writes: _Optional[_Iterable[_Union[Write, _Mapping]]] = ..., reads: _Optional[_Iterable[_Union[Read, _Mapping]]] = ...) -> None: ...

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

class ExportCSVConfig(_message.Message):
    __slots__ = ("path", "data_columns", "partition_size", "compression", "syntax_header_row", "syntax_missing_string", "syntax_delim", "syntax_quotechar", "syntax_escapechar")
    PATH_FIELD_NUMBER: _ClassVar[int]
    DATA_COLUMNS_FIELD_NUMBER: _ClassVar[int]
    PARTITION_SIZE_FIELD_NUMBER: _ClassVar[int]
    COMPRESSION_FIELD_NUMBER: _ClassVar[int]
    SYNTAX_HEADER_ROW_FIELD_NUMBER: _ClassVar[int]
    SYNTAX_MISSING_STRING_FIELD_NUMBER: _ClassVar[int]
    SYNTAX_DELIM_FIELD_NUMBER: _ClassVar[int]
    SYNTAX_QUOTECHAR_FIELD_NUMBER: _ClassVar[int]
    SYNTAX_ESCAPECHAR_FIELD_NUMBER: _ClassVar[int]
    path: str
    data_columns: _containers.RepeatedCompositeFieldContainer[ExportCSVColumn]
    partition_size: int
    compression: str
    syntax_header_row: bool
    syntax_missing_string: str
    syntax_delim: str
    syntax_quotechar: str
    syntax_escapechar: str
    def __init__(self, path: _Optional[str] = ..., data_columns: _Optional[_Iterable[_Union[ExportCSVColumn, _Mapping]]] = ..., partition_size: _Optional[int] = ..., compression: _Optional[str] = ..., syntax_header_row: bool = ..., syntax_missing_string: _Optional[str] = ..., syntax_delim: _Optional[str] = ..., syntax_quotechar: _Optional[str] = ..., syntax_escapechar: _Optional[str] = ...) -> None: ...

class ExportCSVColumn(_message.Message):
    __slots__ = ("column_name", "column_data")
    COLUMN_NAME_FIELD_NUMBER: _ClassVar[int]
    COLUMN_DATA_FIELD_NUMBER: _ClassVar[int]
    column_name: str
    column_data: _logic_pb2.RelationId
    def __init__(self, column_name: _Optional[str] = ..., column_data: _Optional[_Union[_logic_pb2.RelationId, _Mapping]] = ...) -> None: ...

class Read(_message.Message):
    __slots__ = ("demand", "output", "what_if", "abort", "export")
    DEMAND_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    WHAT_IF_FIELD_NUMBER: _ClassVar[int]
    ABORT_FIELD_NUMBER: _ClassVar[int]
    EXPORT_FIELD_NUMBER: _ClassVar[int]
    demand: Demand
    output: Output
    what_if: WhatIf
    abort: Abort
    export: Export
    def __init__(self, demand: _Optional[_Union[Demand, _Mapping]] = ..., output: _Optional[_Union[Output, _Mapping]] = ..., what_if: _Optional[_Union[WhatIf, _Mapping]] = ..., abort: _Optional[_Union[Abort, _Mapping]] = ..., export: _Optional[_Union[Export, _Mapping]] = ...) -> None: ...

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

class Export(_message.Message):
    __slots__ = ("csv_config",)
    CSV_CONFIG_FIELD_NUMBER: _ClassVar[int]
    csv_config: ExportCSVConfig
    def __init__(self, csv_config: _Optional[_Union[ExportCSVConfig, _Mapping]] = ...) -> None: ...

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
