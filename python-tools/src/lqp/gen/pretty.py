"""
Auto-generated pretty printer.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the pretty printer, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer python
"""

from io import StringIO
from collections.abc import Sequence
from typing import Any, IO, Never, Optional

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    pass


class PrettyPrinter:
    """Pretty printer for protobuf messages."""

    def __init__(self, io: Optional[IO[str]] = None, print_symbolic_relation_ids: bool = True):
        self.io = io if io is not None else StringIO()
        self.indent_level = 0
        self.at_line_start = True
        self.print_symbolic_relation_ids = print_symbolic_relation_ids
        self._debug_info: dict[tuple[int, int], str] = {}

    def write(self, s: str) -> None:
        """Write a string to the output, with indentation at line start."""
        if self.at_line_start and s.strip():
            self.io.write('  ' * self.indent_level)
            self.at_line_start = False
        self.io.write(s)

    def newline(self) -> None:
        """Write a newline to the output."""
        self.io.write('\n')
        self.at_line_start = True

    def indent(self, delta: int = 1) -> None:
        """Increase indentation level."""
        self.indent_level += delta

    def dedent(self, delta: int = 1) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - delta)

    def get_output(self) -> str:
        """Get the accumulated output as a string."""
        if isinstance(self.io, StringIO):
            return self.io.getvalue()
        return ""

    def format_decimal(self, msg: logic_pb2.DecimalValue) -> str:
        """Format a DecimalValue as '<digits>.<digits>d<precision>'."""
        int_val: int = (msg.value.high << 64) | msg.value.low
        if msg.value.high & (1 << 63):
            int_val -= (1 << 128)
        sign = ""
        if int_val < 0:
            sign = "-"
            int_val = -int_val
        digits = str(int_val)
        scale = msg.scale
        if scale <= 0:
            decimal_str = digits + "." + "0" * (-scale)
        elif scale >= len(digits):
            decimal_str = "0." + "0" * (scale - len(digits)) + digits
        else:
            decimal_str = digits[:-scale] + "." + digits[-scale:]
        return sign + decimal_str + "d" + str(msg.precision)

    def format_int128(self, msg: logic_pb2.Int128Value) -> str:
        """Format an Int128Value protobuf message as a string with i128 suffix."""
        value = (msg.high << 64) | msg.low
        if msg.high & (1 << 63):
            value -= (1 << 128)
        return str(value) + "i128"

    def format_uint128(self, msg: logic_pb2.UInt128Value) -> str:
        """Format a UInt128Value protobuf message as a hex string."""
        value = (msg.high << 64) | msg.low
        return f"0x{value:x}"

    def fragment_id_to_string(self, msg: fragments_pb2.FragmentId) -> str:
        """Convert FragmentId to string representation."""
        return msg.id.decode('utf-8') if msg.id else ""

    def start_pretty_fragment(self, msg: fragments_pb2.Fragment) -> None:
        """Extract debug info from Fragment for relation ID lookup."""
        debug_info = msg.debug_info
        for rid, name in zip(debug_info.ids, debug_info.orig_names):
            self._debug_info[(rid.id_low, rid.id_high)] = name

    def relation_id_to_string(self, msg: logic_pb2.RelationId) -> str:
        """Convert RelationId to string representation using debug info."""
        if not self.print_symbolic_relation_ids:
            return ""
        return self._debug_info.get((msg.id_low, msg.id_high), "")

    def relation_id_to_int(self, msg: logic_pb2.RelationId) -> Optional[int]:
        """Convert RelationId to int if it fits in signed 64-bit range."""
        value = (msg.id_high << 64) | msg.id_low
        if value <= 0x7FFFFFFFFFFFFFFF:
            return value
        return None

    def relation_id_to_uint128(self, msg: logic_pb2.RelationId) -> logic_pb2.UInt128Value:
        """Convert RelationId to UInt128Value representation."""
        return logic_pb2.UInt128Value(low=msg.id_low, high=msg.id_high)

    def format_string_value(self, s: str) -> str:
        """Format a string value with double quotes for LQP output."""
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return '"' + escaped + '"'

    def write_debug_info(self) -> None:
        """Write accumulated debug info as comments at the end of the output."""
        if not self._debug_info:
            return
        self.io.write('\n;; Debug information\n')
        self.io.write(';; -----------------------\n')
        self.io.write(';; Original names\n')
        for (id_low, id_high), name in self._debug_info.items():
            value = (id_high << 64) | id_low
            self.io.write(f';; \t ID `0x{value:x}` -> `{name}`\n')

    # --- Helper functions ---

    def _extract_value_int32(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t1253 = value.HasField('int_value')
        else:
            _t1253 = False
        if _t1253:
            assert value is not None
            return int(value.int_value)
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t1254 = value.HasField('int_value')
        else:
            _t1254 = False
        if _t1254:
            assert value is not None
            return value.int_value
        return default

    def _extract_value_float64(self, value: Optional[logic_pb2.Value], default: float) -> float:
        
        if value is not None:
            assert value is not None
            _t1255 = value.HasField('float_value')
        else:
            _t1255 = False
        if _t1255:
            assert value is not None
            return value.float_value
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        
        if value is not None:
            assert value is not None
            _t1256 = value.HasField('string_value')
        else:
            _t1256 = False
        if _t1256:
            assert value is not None
            return value.string_value
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        
        if value is not None:
            assert value is not None
            _t1257 = value.HasField('boolean_value')
        else:
            _t1257 = False
        if _t1257:
            assert value is not None
            return value.boolean_value
        return default

    def _extract_value_bytes(self, value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        
        if value is not None:
            assert value is not None
            _t1258 = value.HasField('string_value')
        else:
            _t1258 = False
        if _t1258:
            assert value is not None
            return value.string_value.encode()
        return default

    def _extract_value_uint128(self, value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        
        if value is not None:
            assert value is not None
            _t1259 = value.HasField('uint128_value')
        else:
            _t1259 = False
        if _t1259:
            assert value is not None
            return value.uint128_value
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        
        if value is not None:
            assert value is not None
            _t1260 = value.HasField('string_value')
        else:
            _t1260 = False
        if _t1260:
            assert value is not None
            return [value.string_value]
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        
        if value is not None:
            assert value is not None
            _t1261 = value.HasField('int_value')
        else:
            _t1261 = False
        if _t1261:
            assert value is not None
            return value.int_value
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        
        if value is not None:
            assert value is not None
            _t1262 = value.HasField('float_value')
        else:
            _t1262 = False
        if _t1262:
            assert value is not None
            return value.float_value
        return None

    def _try_extract_value_string(self, value: Optional[logic_pb2.Value]) -> Optional[str]:
        
        if value is not None:
            assert value is not None
            _t1263 = value.HasField('string_value')
        else:
            _t1263 = False
        if _t1263:
            assert value is not None
            return value.string_value
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        
        if value is not None:
            assert value is not None
            _t1264 = value.HasField('string_value')
        else:
            _t1264 = False
        if _t1264:
            assert value is not None
            return value.string_value.encode()
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        
        if value is not None:
            assert value is not None
            _t1265 = value.HasField('uint128_value')
        else:
            _t1265 = False
        if _t1265:
            assert value is not None
            return value.uint128_value
        return None

    def _try_extract_value_string_list(self, value: Optional[logic_pb2.Value]) -> Optional[Sequence[str]]:
        
        if value is not None:
            assert value is not None
            _t1266 = value.HasField('string_value')
        else:
            _t1266 = False
        if _t1266:
            assert value is not None
            return [value.string_value]
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1267 = self._extract_value_int32(config.get('csv_header_row'), 1)
        header_row = _t1267
        _t1268 = self._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1268
        _t1269 = self._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1269
        _t1270 = self._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1270
        _t1271 = self._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1271
        _t1272 = self._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1272
        _t1273 = self._extract_value_string(config.get('csv_comment'), '')
        comment = _t1273
        _t1274 = self._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1274
        _t1275 = self._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1275
        _t1276 = self._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1276
        _t1277 = self._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1277
        _t1278 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1278

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1279 = self._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t1279
        _t1280 = self._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t1280
        _t1281 = self._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t1281
        _t1282 = self._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t1282
        _t1283 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1283
        _t1284 = self._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t1284
        _t1285 = self._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t1285
        _t1286 = self._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t1286
        _t1287 = self._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t1287
        _t1288 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1288
        _t1289 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1289

    def default_configure(self) -> transactions_pb2.Configure:
        _t1290 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1290
        _t1291 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1291

    def construct_configure(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get('ivm.maintenance_level')
        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        if (maintenance_level_val is not None and maintenance_level_val.HasField('string_value')):
            if maintenance_level_val.string_value == 'off':
                maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
            else:
                if maintenance_level_val.string_value == 'auto':
                    maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
                else:
                    if maintenance_level_val.string_value == 'all':
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
                    else:
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        _t1292 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1292
        _t1293 = self._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1293
        _t1294 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1294

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1295 = self._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1295
        _t1296 = self._extract_value_string(config.get('compression'), '')
        compression = _t1296
        _t1297 = self._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1297
        _t1298 = self._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1298
        _t1299 = self._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1299
        _t1300 = self._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1300
        _t1301 = self._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1301
        _t1302 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1302

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1303 = logic_pb2.Value(int_value=int(v))
        return _t1303

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1304 = logic_pb2.Value(int_value=v)
        return _t1304

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1305 = logic_pb2.Value(float_value=v)
        return _t1305

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1306 = logic_pb2.Value(string_value=v)
        return _t1306

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1307 = logic_pb2.Value(boolean_value=v)
        return _t1307

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1308 = logic_pb2.Value(uint128_value=v)
        return _t1308

    def is_default_configure(self, cfg: transactions_pb2.Configure) -> bool:
        if cfg.semantics_version != 0:
            return False
        if cfg.ivm_config.level != transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
            return False
        return True

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1309 = self._make_value_string('auto')
            result.append(('ivm.maintenance_level', _t1309,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1310 = self._make_value_string('all')
                result.append(('ivm.maintenance_level', _t1310,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1311 = self._make_value_string('off')
                    result.append(('ivm.maintenance_level', _t1311,))
        _t1312 = self._make_value_int64(msg.semantics_version)
        result.append(('semantics_version', _t1312,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1313 = self._make_value_int32(msg.header_row)
        result.append(('csv_header_row', _t1313,))
        _t1314 = self._make_value_int64(msg.skip)
        result.append(('csv_skip', _t1314,))
        if msg.new_line != '':
            _t1315 = self._make_value_string(msg.new_line)
            result.append(('csv_new_line', _t1315,))
        _t1316 = self._make_value_string(msg.delimiter)
        result.append(('csv_delimiter', _t1316,))
        _t1317 = self._make_value_string(msg.quotechar)
        result.append(('csv_quotechar', _t1317,))
        _t1318 = self._make_value_string(msg.escapechar)
        result.append(('csv_escapechar', _t1318,))
        if msg.comment != '':
            _t1319 = self._make_value_string(msg.comment)
            result.append(('csv_comment', _t1319,))
        for missing_string in msg.missing_strings:
            _t1320 = self._make_value_string(missing_string)
            result.append(('csv_missing_strings', _t1320,))
        _t1321 = self._make_value_string(msg.decimal_separator)
        result.append(('csv_decimal_separator', _t1321,))
        _t1322 = self._make_value_string(msg.encoding)
        result.append(('csv_encoding', _t1322,))
        _t1323 = self._make_value_string(msg.compression)
        result.append(('csv_compression', _t1323,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1324 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(('betree_config_epsilon', _t1324,))
        _t1325 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(('betree_config_max_pivots', _t1325,))
        _t1326 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(('betree_config_max_deltas', _t1326,))
        _t1327 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(('betree_config_max_leaf', _t1327,))
        if msg.relation_locator.HasField('root_pageid'):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1328 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(('betree_locator_root_pageid', _t1328,))
        if msg.relation_locator.HasField('inline_data'):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1329 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(('betree_locator_inline_data', _t1329,))
        _t1330 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(('betree_locator_element_count', _t1330,))
        _t1331 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(('betree_locator_tree_height', _t1331,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1332 = self._make_value_int64(msg.partition_size)
            result.append(('partition_size', _t1332,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1333 = self._make_value_string(msg.compression)
            result.append(('compression', _t1333,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1334 = self._make_value_boolean(msg.syntax_header_row)
            result.append(('syntax_header_row', _t1334,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1335 = self._make_value_string(msg.syntax_missing_string)
            result.append(('syntax_missing_string', _t1335,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1336 = self._make_value_string(msg.syntax_delim)
            result.append(('syntax_delim', _t1336,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1337 = self._make_value_string(msg.syntax_quotechar)
            result.append(('syntax_quotechar', _t1337,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1338 = self._make_value_string(msg.syntax_escapechar)
            result.append(('syntax_escapechar', _t1338,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != '':
            return name
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == '':
            return self.relation_id_to_uint128(msg)
        return None

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        return (abs.vars[0:n], [],)

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)

    # --- Pretty-print methods ---

    def pretty_transaction(self, msg: transactions_pb2.Transaction) -> Optional[Never]:
        def _t490(_dollar_dollar):
            
            if _dollar_dollar.HasField('configure'):
                _t491 = _dollar_dollar.configure
            else:
                _t491 = None
            
            if _dollar_dollar.HasField('sync'):
                _t492 = _dollar_dollar.sync
            else:
                _t492 = None
            return (_t491, _t492, _dollar_dollar.epochs,)
        _t493 = _t490(msg)
        fields0 = _t493
        assert fields0 is not None
        unwrapped_fields1 = fields0
        self.write('(')
        self.write('transaction')
        self.indent()
        field2 = unwrapped_fields1[0]
        
        if field2 is not None:
            self.newline()
            assert field2 is not None
            opt_val3 = field2
            _t495 = self.pretty_configure(opt_val3)
            _t494 = _t495
        else:
            _t494 = None
        field4 = unwrapped_fields1[1]
        
        if field4 is not None:
            self.newline()
            assert field4 is not None
            opt_val5 = field4
            _t497 = self.pretty_sync(opt_val5)
            _t496 = _t497
        else:
            _t496 = None
        field6 = unwrapped_fields1[2]
        if not len(field6) == 0:
            self.newline()
            for i8, elem7 in enumerate(field6):
                if (i8 > 0):
                    self.newline()
                _t498 = self.pretty_epoch(elem7)
        self.dedent()
        self.write(')')
        return None

    def pretty_configure(self, msg: transactions_pb2.Configure) -> Optional[Never]:
        def _t499(_dollar_dollar):
            _t500 = self.deconstruct_configure(_dollar_dollar)
            return _t500
        _t501 = _t499(msg)
        fields9 = _t501
        assert fields9 is not None
        unwrapped_fields10 = fields9
        self.write('(')
        self.write('configure')
        self.indent()
        self.newline()
        _t502 = self.pretty_config_dict(unwrapped_fields10)
        self.dedent()
        self.write(')')
        return None

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]) -> Optional[Never]:
        def _t503(_dollar_dollar):
            return _dollar_dollar
        _t504 = _t503(msg)
        fields11 = _t504
        assert fields11 is not None
        unwrapped_fields12 = fields11
        self.write('{')
        if not len(unwrapped_fields12) == 0:
            self.write(' ')
            for i14, elem13 in enumerate(unwrapped_fields12):
                if (i14 > 0):
                    self.newline()
                _t505 = self.pretty_config_key_value(elem13)
        self.write('}')
        return None

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]) -> Optional[Never]:
        def _t506(_dollar_dollar):
            return (_dollar_dollar[0], _dollar_dollar[1],)
        _t507 = _t506(msg)
        fields15 = _t507
        assert fields15 is not None
        unwrapped_fields16 = fields15
        self.write(':')
        field17 = unwrapped_fields16[0]
        self.write(field17)
        self.write(' ')
        field18 = unwrapped_fields16[1]
        _t508 = self.pretty_value(field18)
        return _t508

    def pretty_value(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t509(_dollar_dollar):
            
            if _dollar_dollar.HasField('date_value'):
                _t510 = _dollar_dollar.date_value
            else:
                _t510 = None
            return _t510
        _t511 = _t509(msg)
        deconstruct_result29 = _t511
        
        if deconstruct_result29 is not None:
            _t513 = self.pretty_date(deconstruct_result29)
            _t512 = _t513
        else:
            def _t514(_dollar_dollar):
                
                if _dollar_dollar.HasField('datetime_value'):
                    _t515 = _dollar_dollar.datetime_value
                else:
                    _t515 = None
                return _t515
            _t516 = _t514(msg)
            deconstruct_result28 = _t516
            
            if deconstruct_result28 is not None:
                _t518 = self.pretty_datetime(deconstruct_result28)
                _t517 = _t518
            else:
                def _t519(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('string_value'):
                        _t520 = _dollar_dollar.string_value
                    else:
                        _t520 = None
                    return _t520
                _t521 = _t519(msg)
                deconstruct_result27 = _t521
                
                if deconstruct_result27 is not None:
                    self.write(self.format_string_value(deconstruct_result27))
                    _t522 = None
                else:
                    def _t523(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('int_value'):
                            _t524 = _dollar_dollar.int_value
                        else:
                            _t524 = None
                        return _t524
                    _t525 = _t523(msg)
                    deconstruct_result26 = _t525
                    
                    if deconstruct_result26 is not None:
                        self.write(str(deconstruct_result26))
                        _t526 = None
                    else:
                        def _t527(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('float_value'):
                                _t528 = _dollar_dollar.float_value
                            else:
                                _t528 = None
                            return _t528
                        _t529 = _t527(msg)
                        deconstruct_result25 = _t529
                        
                        if deconstruct_result25 is not None:
                            self.write(str(deconstruct_result25))
                            _t530 = None
                        else:
                            def _t531(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('uint128_value'):
                                    _t532 = _dollar_dollar.uint128_value
                                else:
                                    _t532 = None
                                return _t532
                            _t533 = _t531(msg)
                            deconstruct_result24 = _t533
                            
                            if deconstruct_result24 is not None:
                                self.write(self.format_uint128(deconstruct_result24))
                                _t534 = None
                            else:
                                def _t535(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('int128_value'):
                                        _t536 = _dollar_dollar.int128_value
                                    else:
                                        _t536 = None
                                    return _t536
                                _t537 = _t535(msg)
                                deconstruct_result23 = _t537
                                
                                if deconstruct_result23 is not None:
                                    self.write(self.format_int128(deconstruct_result23))
                                    _t538 = None
                                else:
                                    def _t539(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('decimal_value'):
                                            _t540 = _dollar_dollar.decimal_value
                                        else:
                                            _t540 = None
                                        return _t540
                                    _t541 = _t539(msg)
                                    deconstruct_result22 = _t541
                                    
                                    if deconstruct_result22 is not None:
                                        self.write(self.format_decimal(deconstruct_result22))
                                        _t542 = None
                                    else:
                                        def _t543(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('boolean_value'):
                                                _t544 = _dollar_dollar.boolean_value
                                            else:
                                                _t544 = None
                                            return _t544
                                        _t545 = _t543(msg)
                                        deconstruct_result21 = _t545
                                        
                                        if deconstruct_result21 is not None:
                                            _t547 = self.pretty_boolean_value(deconstruct_result21)
                                            _t546 = _t547
                                        else:
                                            def _t548(_dollar_dollar):
                                                return _dollar_dollar
                                            _t549 = _t548(msg)
                                            fields19 = _t549
                                            assert fields19 is not None
                                            unwrapped_fields20 = fields19
                                            self.write('missing')
                                            _t546 = None
                                        _t542 = _t546
                                    _t538 = _t542
                                _t534 = _t538
                            _t530 = _t534
                        _t526 = _t530
                    _t522 = _t526
                _t517 = _t522
            _t512 = _t517
        return _t512

    def pretty_date(self, msg: logic_pb2.DateValue) -> Optional[Never]:
        def _t550(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
        _t551 = _t550(msg)
        fields30 = _t551
        assert fields30 is not None
        unwrapped_fields31 = fields30
        self.write('(')
        self.write('date')
        self.indent()
        self.newline()
        field32 = unwrapped_fields31[0]
        self.write(str(field32))
        self.newline()
        field33 = unwrapped_fields31[1]
        self.write(str(field33))
        self.newline()
        field34 = unwrapped_fields31[2]
        self.write(str(field34))
        self.dedent()
        self.write(')')
        return None

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue) -> Optional[Never]:
        def _t552(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
        _t553 = _t552(msg)
        fields35 = _t553
        assert fields35 is not None
        unwrapped_fields36 = fields35
        self.write('(')
        self.write('datetime')
        self.indent()
        self.newline()
        field37 = unwrapped_fields36[0]
        self.write(str(field37))
        self.newline()
        field38 = unwrapped_fields36[1]
        self.write(str(field38))
        self.newline()
        field39 = unwrapped_fields36[2]
        self.write(str(field39))
        self.newline()
        field40 = unwrapped_fields36[3]
        self.write(str(field40))
        self.newline()
        field41 = unwrapped_fields36[4]
        self.write(str(field41))
        self.newline()
        field42 = unwrapped_fields36[5]
        self.write(str(field42))
        field43 = unwrapped_fields36[6]
        if field43 is not None:
            self.newline()
            assert field43 is not None
            opt_val44 = field43
            self.write(str(opt_val44))
        self.dedent()
        self.write(')')
        return None

    def pretty_boolean_value(self, msg: bool) -> Optional[Never]:
        def _t554(_dollar_dollar):
            
            if _dollar_dollar:
                _t555 = ()
            else:
                _t555 = None
            return _t555
        _t556 = _t554(msg)
        deconstruct_result46 = _t556
        if deconstruct_result46 is not None:
            self.write('true')
        else:
            def _t557(_dollar_dollar):
                
                if not _dollar_dollar:
                    _t558 = ()
                else:
                    _t558 = None
                return _t558
            _t559 = _t557(msg)
            deconstruct_result45 = _t559
            if deconstruct_result45 is not None:
                self.write('false')
            else:
                raise ParseError('No matching rule for boolean_value')
        return None

    def pretty_sync(self, msg: transactions_pb2.Sync) -> Optional[Never]:
        def _t560(_dollar_dollar):
            return _dollar_dollar.fragments
        _t561 = _t560(msg)
        fields47 = _t561
        assert fields47 is not None
        unwrapped_fields48 = fields47
        self.write('(')
        self.write('sync')
        self.indent()
        if not len(unwrapped_fields48) == 0:
            self.newline()
            for i50, elem49 in enumerate(unwrapped_fields48):
                if (i50 > 0):
                    self.newline()
                _t562 = self.pretty_fragment_id(elem49)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[Never]:
        def _t563(_dollar_dollar):
            return self.fragment_id_to_string(_dollar_dollar)
        _t564 = _t563(msg)
        fields51 = _t564
        assert fields51 is not None
        unwrapped_fields52 = fields51
        self.write(':')
        self.write(unwrapped_fields52)
        return None

    def pretty_epoch(self, msg: transactions_pb2.Epoch) -> Optional[Never]:
        def _t565(_dollar_dollar):
            
            if not len(_dollar_dollar.writes) == 0:
                _t566 = _dollar_dollar.writes
            else:
                _t566 = None
            
            if not len(_dollar_dollar.reads) == 0:
                _t567 = _dollar_dollar.reads
            else:
                _t567 = None
            return (_t566, _t567,)
        _t568 = _t565(msg)
        fields53 = _t568
        assert fields53 is not None
        unwrapped_fields54 = fields53
        self.write('(')
        self.write('epoch')
        self.indent()
        field55 = unwrapped_fields54[0]
        
        if field55 is not None:
            self.newline()
            assert field55 is not None
            opt_val56 = field55
            _t570 = self.pretty_epoch_writes(opt_val56)
            _t569 = _t570
        else:
            _t569 = None
        field57 = unwrapped_fields54[1]
        
        if field57 is not None:
            self.newline()
            assert field57 is not None
            opt_val58 = field57
            _t572 = self.pretty_epoch_reads(opt_val58)
            _t571 = _t572
        else:
            _t571 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]) -> Optional[Never]:
        def _t573(_dollar_dollar):
            return _dollar_dollar
        _t574 = _t573(msg)
        fields59 = _t574
        assert fields59 is not None
        unwrapped_fields60 = fields59
        self.write('(')
        self.write('writes')
        self.indent()
        if not len(unwrapped_fields60) == 0:
            self.newline()
            for i62, elem61 in enumerate(unwrapped_fields60):
                if (i62 > 0):
                    self.newline()
                _t575 = self.pretty_write(elem61)
        self.dedent()
        self.write(')')
        return None

    def pretty_write(self, msg: transactions_pb2.Write) -> Optional[Never]:
        def _t576(_dollar_dollar):
            
            if _dollar_dollar.HasField('define'):
                _t577 = _dollar_dollar.define
            else:
                _t577 = None
            return _t577
        _t578 = _t576(msg)
        deconstruct_result65 = _t578
        
        if deconstruct_result65 is not None:
            _t580 = self.pretty_define(deconstruct_result65)
            _t579 = _t580
        else:
            def _t581(_dollar_dollar):
                
                if _dollar_dollar.HasField('undefine'):
                    _t582 = _dollar_dollar.undefine
                else:
                    _t582 = None
                return _t582
            _t583 = _t581(msg)
            deconstruct_result64 = _t583
            
            if deconstruct_result64 is not None:
                _t585 = self.pretty_undefine(deconstruct_result64)
                _t584 = _t585
            else:
                def _t586(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('context'):
                        _t587 = _dollar_dollar.context
                    else:
                        _t587 = None
                    return _t587
                _t588 = _t586(msg)
                deconstruct_result63 = _t588
                
                if deconstruct_result63 is not None:
                    _t590 = self.pretty_context(deconstruct_result63)
                    _t589 = _t590
                else:
                    raise ParseError('No matching rule for write')
                _t584 = _t589
            _t579 = _t584
        return _t579

    def pretty_define(self, msg: transactions_pb2.Define) -> Optional[Never]:
        def _t591(_dollar_dollar):
            return _dollar_dollar.fragment
        _t592 = _t591(msg)
        fields66 = _t592
        assert fields66 is not None
        unwrapped_fields67 = fields66
        self.write('(')
        self.write('define')
        self.indent()
        self.newline()
        _t593 = self.pretty_fragment(unwrapped_fields67)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> Optional[Never]:
        def _t594(_dollar_dollar):
            _t595 = self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t596 = _t594(msg)
        fields68 = _t596
        assert fields68 is not None
        unwrapped_fields69 = fields68
        self.write('(')
        self.write('fragment')
        self.indent()
        self.newline()
        field70 = unwrapped_fields69[0]
        _t597 = self.pretty_new_fragment_id(field70)
        field71 = unwrapped_fields69[1]
        if not len(field71) == 0:
            self.newline()
            for i73, elem72 in enumerate(field71):
                if (i73 > 0):
                    self.newline()
                _t598 = self.pretty_declaration(elem72)
        self.dedent()
        self.write(')')
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[Never]:
        def _t599(_dollar_dollar):
            return _dollar_dollar
        _t600 = _t599(msg)
        fields74 = _t600
        assert fields74 is not None
        unwrapped_fields75 = fields74
        _t601 = self.pretty_fragment_id(unwrapped_fields75)
        return _t601

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> Optional[Never]:
        def _t602(_dollar_dollar):
            
            if _dollar_dollar.HasField('def'):
                _t603 = getattr(_dollar_dollar, 'def')
            else:
                _t603 = None
            return _t603
        _t604 = _t602(msg)
        deconstruct_result79 = _t604
        
        if deconstruct_result79 is not None:
            _t606 = self.pretty_def(deconstruct_result79)
            _t605 = _t606
        else:
            def _t607(_dollar_dollar):
                
                if _dollar_dollar.HasField('algorithm'):
                    _t608 = _dollar_dollar.algorithm
                else:
                    _t608 = None
                return _t608
            _t609 = _t607(msg)
            deconstruct_result78 = _t609
            
            if deconstruct_result78 is not None:
                _t611 = self.pretty_algorithm(deconstruct_result78)
                _t610 = _t611
            else:
                def _t612(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('constraint'):
                        _t613 = _dollar_dollar.constraint
                    else:
                        _t613 = None
                    return _t613
                _t614 = _t612(msg)
                deconstruct_result77 = _t614
                
                if deconstruct_result77 is not None:
                    _t616 = self.pretty_constraint(deconstruct_result77)
                    _t615 = _t616
                else:
                    def _t617(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('data'):
                            _t618 = _dollar_dollar.data
                        else:
                            _t618 = None
                        return _t618
                    _t619 = _t617(msg)
                    deconstruct_result76 = _t619
                    
                    if deconstruct_result76 is not None:
                        _t621 = self.pretty_data(deconstruct_result76)
                        _t620 = _t621
                    else:
                        raise ParseError('No matching rule for declaration')
                    _t615 = _t620
                _t610 = _t615
            _t605 = _t610
        return _t605

    def pretty_def(self, msg: logic_pb2.Def) -> Optional[Never]:
        def _t622(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t623 = _dollar_dollar.attrs
            else:
                _t623 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t623,)
        _t624 = _t622(msg)
        fields80 = _t624
        assert fields80 is not None
        unwrapped_fields81 = fields80
        self.write('(')
        self.write('def')
        self.indent()
        self.newline()
        field82 = unwrapped_fields81[0]
        _t625 = self.pretty_relation_id(field82)
        self.newline()
        field83 = unwrapped_fields81[1]
        _t626 = self.pretty_abstraction(field83)
        field84 = unwrapped_fields81[2]
        
        if field84 is not None:
            self.newline()
            assert field84 is not None
            opt_val85 = field84
            _t628 = self.pretty_attrs(opt_val85)
            _t627 = _t628
        else:
            _t627 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> Optional[Never]:
        def _t629(_dollar_dollar):
            _t630 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t630
        _t631 = _t629(msg)
        deconstruct_result87 = _t631
        if deconstruct_result87 is not None:
            self.write(':')
            self.write(deconstruct_result87)
        else:
            def _t632(_dollar_dollar):
                _t633 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t633
            _t634 = _t632(msg)
            deconstruct_result86 = _t634
            if deconstruct_result86 is not None:
                self.write(self.format_uint128(deconstruct_result86))
            else:
                raise ParseError('No matching rule for relation_id')
        return None

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> Optional[Never]:
        def _t635(_dollar_dollar):
            _t636 = self.deconstruct_bindings(_dollar_dollar)
            return (_t636, _dollar_dollar.value,)
        _t637 = _t635(msg)
        fields88 = _t637
        assert fields88 is not None
        unwrapped_fields89 = fields88
        self.write('(')
        field90 = unwrapped_fields89[0]
        _t638 = self.pretty_bindings(field90)
        self.write(' ')
        field91 = unwrapped_fields89[1]
        _t639 = self.pretty_formula(field91)
        self.write(')')
        return None

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]) -> Optional[Never]:
        def _t640(_dollar_dollar):
            
            if not len(_dollar_dollar[1]) == 0:
                _t641 = _dollar_dollar[1]
            else:
                _t641 = None
            return (_dollar_dollar[0], _t641,)
        _t642 = _t640(msg)
        fields92 = _t642
        assert fields92 is not None
        unwrapped_fields93 = fields92
        self.write('[')
        field94 = unwrapped_fields93[0]
        for i96, elem95 in enumerate(field94):
            if (i96 > 0):
                self.newline()
            _t643 = self.pretty_binding(elem95)
        field97 = unwrapped_fields93[1]
        
        if field97 is not None:
            self.write(' ')
            assert field97 is not None
            opt_val98 = field97
            _t645 = self.pretty_value_bindings(opt_val98)
            _t644 = _t645
        else:
            _t644 = None
        self.write(']')
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> Optional[Never]:
        def _t646(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t647 = _t646(msg)
        fields99 = _t647
        assert fields99 is not None
        unwrapped_fields100 = fields99
        field101 = unwrapped_fields100[0]
        self.write(field101)
        self.write('::')
        field102 = unwrapped_fields100[1]
        _t648 = self.pretty_type(field102)
        return _t648

    def pretty_type(self, msg: logic_pb2.Type) -> Optional[Never]:
        def _t649(_dollar_dollar):
            
            if _dollar_dollar.HasField('unspecified_type'):
                _t650 = _dollar_dollar.unspecified_type
            else:
                _t650 = None
            return _t650
        _t651 = _t649(msg)
        deconstruct_result113 = _t651
        
        if deconstruct_result113 is not None:
            _t653 = self.pretty_unspecified_type(deconstruct_result113)
            _t652 = _t653
        else:
            def _t654(_dollar_dollar):
                
                if _dollar_dollar.HasField('string_type'):
                    _t655 = _dollar_dollar.string_type
                else:
                    _t655 = None
                return _t655
            _t656 = _t654(msg)
            deconstruct_result112 = _t656
            
            if deconstruct_result112 is not None:
                _t658 = self.pretty_string_type(deconstruct_result112)
                _t657 = _t658
            else:
                def _t659(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('int_type'):
                        _t660 = _dollar_dollar.int_type
                    else:
                        _t660 = None
                    return _t660
                _t661 = _t659(msg)
                deconstruct_result111 = _t661
                
                if deconstruct_result111 is not None:
                    _t663 = self.pretty_int_type(deconstruct_result111)
                    _t662 = _t663
                else:
                    def _t664(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('float_type'):
                            _t665 = _dollar_dollar.float_type
                        else:
                            _t665 = None
                        return _t665
                    _t666 = _t664(msg)
                    deconstruct_result110 = _t666
                    
                    if deconstruct_result110 is not None:
                        _t668 = self.pretty_float_type(deconstruct_result110)
                        _t667 = _t668
                    else:
                        def _t669(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('uint128_type'):
                                _t670 = _dollar_dollar.uint128_type
                            else:
                                _t670 = None
                            return _t670
                        _t671 = _t669(msg)
                        deconstruct_result109 = _t671
                        
                        if deconstruct_result109 is not None:
                            _t673 = self.pretty_uint128_type(deconstruct_result109)
                            _t672 = _t673
                        else:
                            def _t674(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('int128_type'):
                                    _t675 = _dollar_dollar.int128_type
                                else:
                                    _t675 = None
                                return _t675
                            _t676 = _t674(msg)
                            deconstruct_result108 = _t676
                            
                            if deconstruct_result108 is not None:
                                _t678 = self.pretty_int128_type(deconstruct_result108)
                                _t677 = _t678
                            else:
                                def _t679(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('date_type'):
                                        _t680 = _dollar_dollar.date_type
                                    else:
                                        _t680 = None
                                    return _t680
                                _t681 = _t679(msg)
                                deconstruct_result107 = _t681
                                
                                if deconstruct_result107 is not None:
                                    _t683 = self.pretty_date_type(deconstruct_result107)
                                    _t682 = _t683
                                else:
                                    def _t684(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('datetime_type'):
                                            _t685 = _dollar_dollar.datetime_type
                                        else:
                                            _t685 = None
                                        return _t685
                                    _t686 = _t684(msg)
                                    deconstruct_result106 = _t686
                                    
                                    if deconstruct_result106 is not None:
                                        _t688 = self.pretty_datetime_type(deconstruct_result106)
                                        _t687 = _t688
                                    else:
                                        def _t689(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('missing_type'):
                                                _t690 = _dollar_dollar.missing_type
                                            else:
                                                _t690 = None
                                            return _t690
                                        _t691 = _t689(msg)
                                        deconstruct_result105 = _t691
                                        
                                        if deconstruct_result105 is not None:
                                            _t693 = self.pretty_missing_type(deconstruct_result105)
                                            _t692 = _t693
                                        else:
                                            def _t694(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('decimal_type'):
                                                    _t695 = _dollar_dollar.decimal_type
                                                else:
                                                    _t695 = None
                                                return _t695
                                            _t696 = _t694(msg)
                                            deconstruct_result104 = _t696
                                            
                                            if deconstruct_result104 is not None:
                                                _t698 = self.pretty_decimal_type(deconstruct_result104)
                                                _t697 = _t698
                                            else:
                                                def _t699(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('boolean_type'):
                                                        _t700 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t700 = None
                                                    return _t700
                                                _t701 = _t699(msg)
                                                deconstruct_result103 = _t701
                                                
                                                if deconstruct_result103 is not None:
                                                    _t703 = self.pretty_boolean_type(deconstruct_result103)
                                                    _t702 = _t703
                                                else:
                                                    raise ParseError('No matching rule for type')
                                                _t697 = _t702
                                            _t692 = _t697
                                        _t687 = _t692
                                    _t682 = _t687
                                _t677 = _t682
                            _t672 = _t677
                        _t667 = _t672
                    _t662 = _t667
                _t657 = _t662
            _t652 = _t657
        return _t652

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> Optional[Never]:
        def _t704(_dollar_dollar):
            return _dollar_dollar
        _t705 = _t704(msg)
        fields114 = _t705
        assert fields114 is not None
        unwrapped_fields115 = fields114
        self.write('UNKNOWN')
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> Optional[Never]:
        def _t706(_dollar_dollar):
            return _dollar_dollar
        _t707 = _t706(msg)
        fields116 = _t707
        assert fields116 is not None
        unwrapped_fields117 = fields116
        self.write('STRING')
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> Optional[Never]:
        def _t708(_dollar_dollar):
            return _dollar_dollar
        _t709 = _t708(msg)
        fields118 = _t709
        assert fields118 is not None
        unwrapped_fields119 = fields118
        self.write('INT')
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> Optional[Never]:
        def _t710(_dollar_dollar):
            return _dollar_dollar
        _t711 = _t710(msg)
        fields120 = _t711
        assert fields120 is not None
        unwrapped_fields121 = fields120
        self.write('FLOAT')
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> Optional[Never]:
        def _t712(_dollar_dollar):
            return _dollar_dollar
        _t713 = _t712(msg)
        fields122 = _t713
        assert fields122 is not None
        unwrapped_fields123 = fields122
        self.write('UINT128')
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> Optional[Never]:
        def _t714(_dollar_dollar):
            return _dollar_dollar
        _t715 = _t714(msg)
        fields124 = _t715
        assert fields124 is not None
        unwrapped_fields125 = fields124
        self.write('INT128')
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> Optional[Never]:
        def _t716(_dollar_dollar):
            return _dollar_dollar
        _t717 = _t716(msg)
        fields126 = _t717
        assert fields126 is not None
        unwrapped_fields127 = fields126
        self.write('DATE')
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> Optional[Never]:
        def _t718(_dollar_dollar):
            return _dollar_dollar
        _t719 = _t718(msg)
        fields128 = _t719
        assert fields128 is not None
        unwrapped_fields129 = fields128
        self.write('DATETIME')
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> Optional[Never]:
        def _t720(_dollar_dollar):
            return _dollar_dollar
        _t721 = _t720(msg)
        fields130 = _t721
        assert fields130 is not None
        unwrapped_fields131 = fields130
        self.write('MISSING')
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> Optional[Never]:
        def _t722(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t723 = _t722(msg)
        fields132 = _t723
        assert fields132 is not None
        unwrapped_fields133 = fields132
        self.write('(')
        self.write('DECIMAL')
        self.indent()
        self.newline()
        field134 = unwrapped_fields133[0]
        self.write(str(field134))
        self.newline()
        field135 = unwrapped_fields133[1]
        self.write(str(field135))
        self.dedent()
        self.write(')')
        return None

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType) -> Optional[Never]:
        def _t724(_dollar_dollar):
            return _dollar_dollar
        _t725 = _t724(msg)
        fields136 = _t725
        assert fields136 is not None
        unwrapped_fields137 = fields136
        self.write('BOOLEAN')
        return None

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]) -> Optional[Never]:
        def _t726(_dollar_dollar):
            return _dollar_dollar
        _t727 = _t726(msg)
        fields138 = _t727
        assert fields138 is not None
        unwrapped_fields139 = fields138
        self.write('|')
        if not len(unwrapped_fields139) == 0:
            self.write(' ')
            for i141, elem140 in enumerate(unwrapped_fields139):
                if (i141 > 0):
                    self.newline()
                _t728 = self.pretty_binding(elem140)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> Optional[Never]:
        def _t729(_dollar_dollar):
            
            if (_dollar_dollar.HasField('conjunction') and len(_dollar_dollar.conjunction.args) == 0):
                _t730 = _dollar_dollar.conjunction
            else:
                _t730 = None
            return _t730
        _t731 = _t729(msg)
        deconstruct_result154 = _t731
        
        if deconstruct_result154 is not None:
            _t733 = self.pretty_true(deconstruct_result154)
            _t732 = _t733
        else:
            def _t734(_dollar_dollar):
                
                if (_dollar_dollar.HasField('disjunction') and len(_dollar_dollar.disjunction.args) == 0):
                    _t735 = _dollar_dollar.disjunction
                else:
                    _t735 = None
                return _t735
            _t736 = _t734(msg)
            deconstruct_result153 = _t736
            
            if deconstruct_result153 is not None:
                _t738 = self.pretty_false(deconstruct_result153)
                _t737 = _t738
            else:
                def _t739(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('exists'):
                        _t740 = _dollar_dollar.exists
                    else:
                        _t740 = None
                    return _t740
                _t741 = _t739(msg)
                deconstruct_result152 = _t741
                
                if deconstruct_result152 is not None:
                    _t743 = self.pretty_exists(deconstruct_result152)
                    _t742 = _t743
                else:
                    def _t744(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('reduce'):
                            _t745 = _dollar_dollar.reduce
                        else:
                            _t745 = None
                        return _t745
                    _t746 = _t744(msg)
                    deconstruct_result151 = _t746
                    
                    if deconstruct_result151 is not None:
                        _t748 = self.pretty_reduce(deconstruct_result151)
                        _t747 = _t748
                    else:
                        def _t749(_dollar_dollar):
                            
                            if (_dollar_dollar.HasField('conjunction') and not len(_dollar_dollar.conjunction.args) == 0):
                                _t750 = _dollar_dollar.conjunction
                            else:
                                _t750 = None
                            return _t750
                        _t751 = _t749(msg)
                        deconstruct_result150 = _t751
                        
                        if deconstruct_result150 is not None:
                            _t753 = self.pretty_conjunction(deconstruct_result150)
                            _t752 = _t753
                        else:
                            def _t754(_dollar_dollar):
                                
                                if (_dollar_dollar.HasField('disjunction') and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t755 = _dollar_dollar.disjunction
                                else:
                                    _t755 = None
                                return _t755
                            _t756 = _t754(msg)
                            deconstruct_result149 = _t756
                            
                            if deconstruct_result149 is not None:
                                _t758 = self.pretty_disjunction(deconstruct_result149)
                                _t757 = _t758
                            else:
                                def _t759(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('not'):
                                        _t760 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t760 = None
                                    return _t760
                                _t761 = _t759(msg)
                                deconstruct_result148 = _t761
                                
                                if deconstruct_result148 is not None:
                                    _t763 = self.pretty_not(deconstruct_result148)
                                    _t762 = _t763
                                else:
                                    def _t764(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('ffi'):
                                            _t765 = _dollar_dollar.ffi
                                        else:
                                            _t765 = None
                                        return _t765
                                    _t766 = _t764(msg)
                                    deconstruct_result147 = _t766
                                    
                                    if deconstruct_result147 is not None:
                                        _t768 = self.pretty_ffi(deconstruct_result147)
                                        _t767 = _t768
                                    else:
                                        def _t769(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('atom'):
                                                _t770 = _dollar_dollar.atom
                                            else:
                                                _t770 = None
                                            return _t770
                                        _t771 = _t769(msg)
                                        deconstruct_result146 = _t771
                                        
                                        if deconstruct_result146 is not None:
                                            _t773 = self.pretty_atom(deconstruct_result146)
                                            _t772 = _t773
                                        else:
                                            def _t774(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('pragma'):
                                                    _t775 = _dollar_dollar.pragma
                                                else:
                                                    _t775 = None
                                                return _t775
                                            _t776 = _t774(msg)
                                            deconstruct_result145 = _t776
                                            
                                            if deconstruct_result145 is not None:
                                                _t778 = self.pretty_pragma(deconstruct_result145)
                                                _t777 = _t778
                                            else:
                                                def _t779(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('primitive'):
                                                        _t780 = _dollar_dollar.primitive
                                                    else:
                                                        _t780 = None
                                                    return _t780
                                                _t781 = _t779(msg)
                                                deconstruct_result144 = _t781
                                                
                                                if deconstruct_result144 is not None:
                                                    _t783 = self.pretty_primitive(deconstruct_result144)
                                                    _t782 = _t783
                                                else:
                                                    def _t784(_dollar_dollar):
                                                        
                                                        if _dollar_dollar.HasField('rel_atom'):
                                                            _t785 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t785 = None
                                                        return _t785
                                                    _t786 = _t784(msg)
                                                    deconstruct_result143 = _t786
                                                    
                                                    if deconstruct_result143 is not None:
                                                        _t788 = self.pretty_rel_atom(deconstruct_result143)
                                                        _t787 = _t788
                                                    else:
                                                        def _t789(_dollar_dollar):
                                                            
                                                            if _dollar_dollar.HasField('cast'):
                                                                _t790 = _dollar_dollar.cast
                                                            else:
                                                                _t790 = None
                                                            return _t790
                                                        _t791 = _t789(msg)
                                                        deconstruct_result142 = _t791
                                                        
                                                        if deconstruct_result142 is not None:
                                                            _t793 = self.pretty_cast(deconstruct_result142)
                                                            _t792 = _t793
                                                        else:
                                                            raise ParseError('No matching rule for formula')
                                                        _t787 = _t792
                                                    _t782 = _t787
                                                _t777 = _t782
                                            _t772 = _t777
                                        _t767 = _t772
                                    _t762 = _t767
                                _t757 = _t762
                            _t752 = _t757
                        _t747 = _t752
                    _t742 = _t747
                _t737 = _t742
            _t732 = _t737
        return _t732

    def pretty_true(self, msg: logic_pb2.Conjunction) -> Optional[Never]:
        def _t794(_dollar_dollar):
            return _dollar_dollar
        _t795 = _t794(msg)
        fields155 = _t795
        assert fields155 is not None
        unwrapped_fields156 = fields155
        self.write('(')
        self.write('true')
        self.write(')')
        return None

    def pretty_false(self, msg: logic_pb2.Disjunction) -> Optional[Never]:
        def _t796(_dollar_dollar):
            return _dollar_dollar
        _t797 = _t796(msg)
        fields157 = _t797
        assert fields157 is not None
        unwrapped_fields158 = fields157
        self.write('(')
        self.write('false')
        self.write(')')
        return None

    def pretty_exists(self, msg: logic_pb2.Exists) -> Optional[Never]:
        def _t798(_dollar_dollar):
            _t799 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t799, _dollar_dollar.body.value,)
        _t800 = _t798(msg)
        fields159 = _t800
        assert fields159 is not None
        unwrapped_fields160 = fields159
        self.write('(')
        self.write('exists')
        self.indent()
        self.newline()
        field161 = unwrapped_fields160[0]
        _t801 = self.pretty_bindings(field161)
        self.newline()
        field162 = unwrapped_fields160[1]
        _t802 = self.pretty_formula(field162)
        self.dedent()
        self.write(')')
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> Optional[Never]:
        def _t803(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t804 = _t803(msg)
        fields163 = _t804
        assert fields163 is not None
        unwrapped_fields164 = fields163
        self.write('(')
        self.write('reduce')
        self.indent()
        self.newline()
        field165 = unwrapped_fields164[0]
        _t805 = self.pretty_abstraction(field165)
        self.newline()
        field166 = unwrapped_fields164[1]
        _t806 = self.pretty_abstraction(field166)
        self.newline()
        field167 = unwrapped_fields164[2]
        _t807 = self.pretty_terms(field167)
        self.dedent()
        self.write(')')
        return None

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]) -> Optional[Never]:
        def _t808(_dollar_dollar):
            return _dollar_dollar
        _t809 = _t808(msg)
        fields168 = _t809
        assert fields168 is not None
        unwrapped_fields169 = fields168
        self.write('(')
        self.write('terms')
        self.indent()
        if not len(unwrapped_fields169) == 0:
            self.newline()
            for i171, elem170 in enumerate(unwrapped_fields169):
                if (i171 > 0):
                    self.newline()
                _t810 = self.pretty_term(elem170)
        self.dedent()
        self.write(')')
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> Optional[Never]:
        def _t811(_dollar_dollar):
            
            if _dollar_dollar.HasField('var'):
                _t812 = _dollar_dollar.var
            else:
                _t812 = None
            return _t812
        _t813 = _t811(msg)
        deconstruct_result173 = _t813
        
        if deconstruct_result173 is not None:
            _t815 = self.pretty_var(deconstruct_result173)
            _t814 = _t815
        else:
            def _t816(_dollar_dollar):
                
                if _dollar_dollar.HasField('constant'):
                    _t817 = _dollar_dollar.constant
                else:
                    _t817 = None
                return _t817
            _t818 = _t816(msg)
            deconstruct_result172 = _t818
            
            if deconstruct_result172 is not None:
                _t820 = self.pretty_constant(deconstruct_result172)
                _t819 = _t820
            else:
                raise ParseError('No matching rule for term')
            _t814 = _t819
        return _t814

    def pretty_var(self, msg: logic_pb2.Var) -> Optional[Never]:
        def _t821(_dollar_dollar):
            return _dollar_dollar.name
        _t822 = _t821(msg)
        fields174 = _t822
        assert fields174 is not None
        unwrapped_fields175 = fields174
        self.write(unwrapped_fields175)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t823(_dollar_dollar):
            return _dollar_dollar
        _t824 = _t823(msg)
        fields176 = _t824
        assert fields176 is not None
        unwrapped_fields177 = fields176
        _t825 = self.pretty_value(unwrapped_fields177)
        return _t825

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> Optional[Never]:
        def _t826(_dollar_dollar):
            return _dollar_dollar.args
        _t827 = _t826(msg)
        fields178 = _t827
        assert fields178 is not None
        unwrapped_fields179 = fields178
        self.write('(')
        self.write('and')
        self.indent()
        if not len(unwrapped_fields179) == 0:
            self.newline()
            for i181, elem180 in enumerate(unwrapped_fields179):
                if (i181 > 0):
                    self.newline()
                _t828 = self.pretty_formula(elem180)
        self.dedent()
        self.write(')')
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> Optional[Never]:
        def _t829(_dollar_dollar):
            return _dollar_dollar.args
        _t830 = _t829(msg)
        fields182 = _t830
        assert fields182 is not None
        unwrapped_fields183 = fields182
        self.write('(')
        self.write('or')
        self.indent()
        if not len(unwrapped_fields183) == 0:
            self.newline()
            for i185, elem184 in enumerate(unwrapped_fields183):
                if (i185 > 0):
                    self.newline()
                _t831 = self.pretty_formula(elem184)
        self.dedent()
        self.write(')')
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> Optional[Never]:
        def _t832(_dollar_dollar):
            return _dollar_dollar.arg
        _t833 = _t832(msg)
        fields186 = _t833
        assert fields186 is not None
        unwrapped_fields187 = fields186
        self.write('(')
        self.write('not')
        self.indent()
        self.newline()
        _t834 = self.pretty_formula(unwrapped_fields187)
        self.dedent()
        self.write(')')
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> Optional[Never]:
        def _t835(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t836 = _t835(msg)
        fields188 = _t836
        assert fields188 is not None
        unwrapped_fields189 = fields188
        self.write('(')
        self.write('ffi')
        self.indent()
        self.newline()
        field190 = unwrapped_fields189[0]
        _t837 = self.pretty_name(field190)
        self.newline()
        field191 = unwrapped_fields189[1]
        _t838 = self.pretty_ffi_args(field191)
        self.newline()
        field192 = unwrapped_fields189[2]
        _t839 = self.pretty_terms(field192)
        self.dedent()
        self.write(')')
        return None

    def pretty_name(self, msg: str) -> Optional[Never]:
        def _t840(_dollar_dollar):
            return _dollar_dollar
        _t841 = _t840(msg)
        fields193 = _t841
        assert fields193 is not None
        unwrapped_fields194 = fields193
        self.write(':')
        self.write(unwrapped_fields194)
        return None

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]) -> Optional[Never]:
        def _t842(_dollar_dollar):
            return _dollar_dollar
        _t843 = _t842(msg)
        fields195 = _t843
        assert fields195 is not None
        unwrapped_fields196 = fields195
        self.write('(')
        self.write('args')
        self.indent()
        if not len(unwrapped_fields196) == 0:
            self.newline()
            for i198, elem197 in enumerate(unwrapped_fields196):
                if (i198 > 0):
                    self.newline()
                _t844 = self.pretty_abstraction(elem197)
        self.dedent()
        self.write(')')
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> Optional[Never]:
        def _t845(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t846 = _t845(msg)
        fields199 = _t846
        assert fields199 is not None
        unwrapped_fields200 = fields199
        self.write('(')
        self.write('atom')
        self.indent()
        self.newline()
        field201 = unwrapped_fields200[0]
        _t847 = self.pretty_relation_id(field201)
        field202 = unwrapped_fields200[1]
        if not len(field202) == 0:
            self.newline()
            for i204, elem203 in enumerate(field202):
                if (i204 > 0):
                    self.newline()
                _t848 = self.pretty_term(elem203)
        self.dedent()
        self.write(')')
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> Optional[Never]:
        def _t849(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t850 = _t849(msg)
        fields205 = _t850
        assert fields205 is not None
        unwrapped_fields206 = fields205
        self.write('(')
        self.write('pragma')
        self.indent()
        self.newline()
        field207 = unwrapped_fields206[0]
        _t851 = self.pretty_name(field207)
        field208 = unwrapped_fields206[1]
        if not len(field208) == 0:
            self.newline()
            for i210, elem209 in enumerate(field208):
                if (i210 > 0):
                    self.newline()
                _t852 = self.pretty_term(elem209)
        self.dedent()
        self.write(')')
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t853(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t854 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t854 = None
            return _t854
        _t855 = _t853(msg)
        guard_result225 = _t855
        
        if guard_result225 is not None:
            _t857 = self.pretty_eq(msg)
            _t856 = _t857
        else:
            def _t858(_dollar_dollar):
                
                if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                    _t859 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t859 = None
                return _t859
            _t860 = _t858(msg)
            guard_result224 = _t860
            
            if guard_result224 is not None:
                _t862 = self.pretty_lt(msg)
                _t861 = _t862
            else:
                def _t863(_dollar_dollar):
                    
                    if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                        _t864 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t864 = None
                    return _t864
                _t865 = _t863(msg)
                guard_result223 = _t865
                
                if guard_result223 is not None:
                    _t867 = self.pretty_lt_eq(msg)
                    _t866 = _t867
                else:
                    def _t868(_dollar_dollar):
                        
                        if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                            _t869 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t869 = None
                        return _t869
                    _t870 = _t868(msg)
                    guard_result222 = _t870
                    
                    if guard_result222 is not None:
                        _t872 = self.pretty_gt(msg)
                        _t871 = _t872
                    else:
                        def _t873(_dollar_dollar):
                            
                            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                                _t874 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t874 = None
                            return _t874
                        _t875 = _t873(msg)
                        guard_result221 = _t875
                        
                        if guard_result221 is not None:
                            _t877 = self.pretty_gt_eq(msg)
                            _t876 = _t877
                        else:
                            def _t878(_dollar_dollar):
                                
                                if _dollar_dollar.name == 'rel_primitive_add_monotype':
                                    _t879 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t879 = None
                                return _t879
                            _t880 = _t878(msg)
                            guard_result220 = _t880
                            
                            if guard_result220 is not None:
                                _t882 = self.pretty_add(msg)
                                _t881 = _t882
                            else:
                                def _t883(_dollar_dollar):
                                    
                                    if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                                        _t884 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t884 = None
                                    return _t884
                                _t885 = _t883(msg)
                                guard_result219 = _t885
                                
                                if guard_result219 is not None:
                                    _t887 = self.pretty_minus(msg)
                                    _t886 = _t887
                                else:
                                    def _t888(_dollar_dollar):
                                        
                                        if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                                            _t889 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t889 = None
                                        return _t889
                                    _t890 = _t888(msg)
                                    guard_result218 = _t890
                                    
                                    if guard_result218 is not None:
                                        _t892 = self.pretty_multiply(msg)
                                        _t891 = _t892
                                    else:
                                        def _t893(_dollar_dollar):
                                            
                                            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                                                _t894 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t894 = None
                                            return _t894
                                        _t895 = _t893(msg)
                                        guard_result217 = _t895
                                        
                                        if guard_result217 is not None:
                                            _t897 = self.pretty_divide(msg)
                                            _t896 = _t897
                                        else:
                                            def _t898(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t899 = _t898(msg)
                                            fields211 = _t899
                                            assert fields211 is not None
                                            unwrapped_fields212 = fields211
                                            self.write('(')
                                            self.write('primitive')
                                            self.indent()
                                            self.newline()
                                            field213 = unwrapped_fields212[0]
                                            _t900 = self.pretty_name(field213)
                                            field214 = unwrapped_fields212[1]
                                            if not len(field214) == 0:
                                                self.newline()
                                                for i216, elem215 in enumerate(field214):
                                                    if (i216 > 0):
                                                        self.newline()
                                                    _t901 = self.pretty_rel_term(elem215)
                                            self.dedent()
                                            self.write(')')
                                            _t896 = None
                                        _t891 = _t896
                                    _t886 = _t891
                                _t881 = _t886
                            _t876 = _t881
                        _t871 = _t876
                    _t866 = _t871
                _t861 = _t866
            _t856 = _t861
        return _t856

    def pretty_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t902(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t903 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t903 = None
            return _t903
        _t904 = _t902(msg)
        fields226 = _t904
        assert fields226 is not None
        unwrapped_fields227 = fields226
        self.write('(')
        self.write('=')
        self.indent()
        self.newline()
        field228 = unwrapped_fields227[0]
        _t905 = self.pretty_term(field228)
        self.newline()
        field229 = unwrapped_fields227[1]
        _t906 = self.pretty_term(field229)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t907(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                _t908 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t908 = None
            return _t908
        _t909 = _t907(msg)
        fields230 = _t909
        assert fields230 is not None
        unwrapped_fields231 = fields230
        self.write('(')
        self.write('<')
        self.indent()
        self.newline()
        field232 = unwrapped_fields231[0]
        _t910 = self.pretty_term(field232)
        self.newline()
        field233 = unwrapped_fields231[1]
        _t911 = self.pretty_term(field233)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t912(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                _t913 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t913 = None
            return _t913
        _t914 = _t912(msg)
        fields234 = _t914
        assert fields234 is not None
        unwrapped_fields235 = fields234
        self.write('(')
        self.write('<=')
        self.indent()
        self.newline()
        field236 = unwrapped_fields235[0]
        _t915 = self.pretty_term(field236)
        self.newline()
        field237 = unwrapped_fields235[1]
        _t916 = self.pretty_term(field237)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t917(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                _t918 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t918 = None
            return _t918
        _t919 = _t917(msg)
        fields238 = _t919
        assert fields238 is not None
        unwrapped_fields239 = fields238
        self.write('(')
        self.write('>')
        self.indent()
        self.newline()
        field240 = unwrapped_fields239[0]
        _t920 = self.pretty_term(field240)
        self.newline()
        field241 = unwrapped_fields239[1]
        _t921 = self.pretty_term(field241)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t922(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                _t923 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t923 = None
            return _t923
        _t924 = _t922(msg)
        fields242 = _t924
        assert fields242 is not None
        unwrapped_fields243 = fields242
        self.write('(')
        self.write('>=')
        self.indent()
        self.newline()
        field244 = unwrapped_fields243[0]
        _t925 = self.pretty_term(field244)
        self.newline()
        field245 = unwrapped_fields243[1]
        _t926 = self.pretty_term(field245)
        self.dedent()
        self.write(')')
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t927(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_add_monotype':
                _t928 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t928 = None
            return _t928
        _t929 = _t927(msg)
        fields246 = _t929
        assert fields246 is not None
        unwrapped_fields247 = fields246
        self.write('(')
        self.write('+')
        self.indent()
        self.newline()
        field248 = unwrapped_fields247[0]
        _t930 = self.pretty_term(field248)
        self.newline()
        field249 = unwrapped_fields247[1]
        _t931 = self.pretty_term(field249)
        self.newline()
        field250 = unwrapped_fields247[2]
        _t932 = self.pretty_term(field250)
        self.dedent()
        self.write(')')
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t933(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                _t934 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t934 = None
            return _t934
        _t935 = _t933(msg)
        fields251 = _t935
        assert fields251 is not None
        unwrapped_fields252 = fields251
        self.write('(')
        self.write('-')
        self.indent()
        self.newline()
        field253 = unwrapped_fields252[0]
        _t936 = self.pretty_term(field253)
        self.newline()
        field254 = unwrapped_fields252[1]
        _t937 = self.pretty_term(field254)
        self.newline()
        field255 = unwrapped_fields252[2]
        _t938 = self.pretty_term(field255)
        self.dedent()
        self.write(')')
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t939(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                _t940 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t940 = None
            return _t940
        _t941 = _t939(msg)
        fields256 = _t941
        assert fields256 is not None
        unwrapped_fields257 = fields256
        self.write('(')
        self.write('*')
        self.indent()
        self.newline()
        field258 = unwrapped_fields257[0]
        _t942 = self.pretty_term(field258)
        self.newline()
        field259 = unwrapped_fields257[1]
        _t943 = self.pretty_term(field259)
        self.newline()
        field260 = unwrapped_fields257[2]
        _t944 = self.pretty_term(field260)
        self.dedent()
        self.write(')')
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t945(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                _t946 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t946 = None
            return _t946
        _t947 = _t945(msg)
        fields261 = _t947
        assert fields261 is not None
        unwrapped_fields262 = fields261
        self.write('(')
        self.write('/')
        self.indent()
        self.newline()
        field263 = unwrapped_fields262[0]
        _t948 = self.pretty_term(field263)
        self.newline()
        field264 = unwrapped_fields262[1]
        _t949 = self.pretty_term(field264)
        self.newline()
        field265 = unwrapped_fields262[2]
        _t950 = self.pretty_term(field265)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> Optional[Never]:
        def _t951(_dollar_dollar):
            
            if _dollar_dollar.HasField('specialized_value'):
                _t952 = _dollar_dollar.specialized_value
            else:
                _t952 = None
            return _t952
        _t953 = _t951(msg)
        deconstruct_result267 = _t953
        
        if deconstruct_result267 is not None:
            _t955 = self.pretty_specialized_value(deconstruct_result267)
            _t954 = _t955
        else:
            def _t956(_dollar_dollar):
                
                if _dollar_dollar.HasField('term'):
                    _t957 = _dollar_dollar.term
                else:
                    _t957 = None
                return _t957
            _t958 = _t956(msg)
            deconstruct_result266 = _t958
            
            if deconstruct_result266 is not None:
                _t960 = self.pretty_term(deconstruct_result266)
                _t959 = _t960
            else:
                raise ParseError('No matching rule for rel_term')
            _t954 = _t959
        return _t954

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t961(_dollar_dollar):
            return _dollar_dollar
        _t962 = _t961(msg)
        fields268 = _t962
        assert fields268 is not None
        unwrapped_fields269 = fields268
        self.write('#')
        _t963 = self.pretty_value(unwrapped_fields269)
        return _t963

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> Optional[Never]:
        def _t964(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t965 = _t964(msg)
        fields270 = _t965
        assert fields270 is not None
        unwrapped_fields271 = fields270
        self.write('(')
        self.write('relatom')
        self.indent()
        self.newline()
        field272 = unwrapped_fields271[0]
        _t966 = self.pretty_name(field272)
        field273 = unwrapped_fields271[1]
        if not len(field273) == 0:
            self.newline()
            for i275, elem274 in enumerate(field273):
                if (i275 > 0):
                    self.newline()
                _t967 = self.pretty_rel_term(elem274)
        self.dedent()
        self.write(')')
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> Optional[Never]:
        def _t968(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t969 = _t968(msg)
        fields276 = _t969
        assert fields276 is not None
        unwrapped_fields277 = fields276
        self.write('(')
        self.write('cast')
        self.indent()
        self.newline()
        field278 = unwrapped_fields277[0]
        _t970 = self.pretty_term(field278)
        self.newline()
        field279 = unwrapped_fields277[1]
        _t971 = self.pretty_term(field279)
        self.dedent()
        self.write(')')
        return None

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]) -> Optional[Never]:
        def _t972(_dollar_dollar):
            return _dollar_dollar
        _t973 = _t972(msg)
        fields280 = _t973
        assert fields280 is not None
        unwrapped_fields281 = fields280
        self.write('(')
        self.write('attrs')
        self.indent()
        if not len(unwrapped_fields281) == 0:
            self.newline()
            for i283, elem282 in enumerate(unwrapped_fields281):
                if (i283 > 0):
                    self.newline()
                _t974 = self.pretty_attribute(elem282)
        self.dedent()
        self.write(')')
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> Optional[Never]:
        def _t975(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t976 = _t975(msg)
        fields284 = _t976
        assert fields284 is not None
        unwrapped_fields285 = fields284
        self.write('(')
        self.write('attribute')
        self.indent()
        self.newline()
        field286 = unwrapped_fields285[0]
        _t977 = self.pretty_name(field286)
        field287 = unwrapped_fields285[1]
        if not len(field287) == 0:
            self.newline()
            for i289, elem288 in enumerate(field287):
                if (i289 > 0):
                    self.newline()
                _t978 = self.pretty_value(elem288)
        self.dedent()
        self.write(')')
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> Optional[Never]:
        def _t979(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t980 = _t979(msg)
        fields290 = _t980
        assert fields290 is not None
        unwrapped_fields291 = fields290
        self.write('(')
        self.write('algorithm')
        self.indent()
        field292 = unwrapped_fields291[0]
        if not len(field292) == 0:
            self.newline()
            for i294, elem293 in enumerate(field292):
                if (i294 > 0):
                    self.newline()
                _t981 = self.pretty_relation_id(elem293)
        self.newline()
        field295 = unwrapped_fields291[1]
        _t982 = self.pretty_script(field295)
        self.dedent()
        self.write(')')
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> Optional[Never]:
        def _t983(_dollar_dollar):
            return _dollar_dollar.constructs
        _t984 = _t983(msg)
        fields296 = _t984
        assert fields296 is not None
        unwrapped_fields297 = fields296
        self.write('(')
        self.write('script')
        self.indent()
        if not len(unwrapped_fields297) == 0:
            self.newline()
            for i299, elem298 in enumerate(unwrapped_fields297):
                if (i299 > 0):
                    self.newline()
                _t985 = self.pretty_construct(elem298)
        self.dedent()
        self.write(')')
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> Optional[Never]:
        def _t986(_dollar_dollar):
            
            if _dollar_dollar.HasField('loop'):
                _t987 = _dollar_dollar.loop
            else:
                _t987 = None
            return _t987
        _t988 = _t986(msg)
        deconstruct_result301 = _t988
        
        if deconstruct_result301 is not None:
            _t990 = self.pretty_loop(deconstruct_result301)
            _t989 = _t990
        else:
            def _t991(_dollar_dollar):
                
                if _dollar_dollar.HasField('instruction'):
                    _t992 = _dollar_dollar.instruction
                else:
                    _t992 = None
                return _t992
            _t993 = _t991(msg)
            deconstruct_result300 = _t993
            
            if deconstruct_result300 is not None:
                _t995 = self.pretty_instruction(deconstruct_result300)
                _t994 = _t995
            else:
                raise ParseError('No matching rule for construct')
            _t989 = _t994
        return _t989

    def pretty_loop(self, msg: logic_pb2.Loop) -> Optional[Never]:
        def _t996(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t997 = _t996(msg)
        fields302 = _t997
        assert fields302 is not None
        unwrapped_fields303 = fields302
        self.write('(')
        self.write('loop')
        self.indent()
        self.newline()
        field304 = unwrapped_fields303[0]
        _t998 = self.pretty_init(field304)
        self.newline()
        field305 = unwrapped_fields303[1]
        _t999 = self.pretty_script(field305)
        self.dedent()
        self.write(')')
        return None

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]) -> Optional[Never]:
        def _t1000(_dollar_dollar):
            return _dollar_dollar
        _t1001 = _t1000(msg)
        fields306 = _t1001
        assert fields306 is not None
        unwrapped_fields307 = fields306
        self.write('(')
        self.write('init')
        self.indent()
        if not len(unwrapped_fields307) == 0:
            self.newline()
            for i309, elem308 in enumerate(unwrapped_fields307):
                if (i309 > 0):
                    self.newline()
                _t1002 = self.pretty_instruction(elem308)
        self.dedent()
        self.write(')')
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> Optional[Never]:
        def _t1003(_dollar_dollar):
            
            if _dollar_dollar.HasField('assign'):
                _t1004 = _dollar_dollar.assign
            else:
                _t1004 = None
            return _t1004
        _t1005 = _t1003(msg)
        deconstruct_result314 = _t1005
        
        if deconstruct_result314 is not None:
            _t1007 = self.pretty_assign(deconstruct_result314)
            _t1006 = _t1007
        else:
            def _t1008(_dollar_dollar):
                
                if _dollar_dollar.HasField('upsert'):
                    _t1009 = _dollar_dollar.upsert
                else:
                    _t1009 = None
                return _t1009
            _t1010 = _t1008(msg)
            deconstruct_result313 = _t1010
            
            if deconstruct_result313 is not None:
                _t1012 = self.pretty_upsert(deconstruct_result313)
                _t1011 = _t1012
            else:
                def _t1013(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('break'):
                        _t1014 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1014 = None
                    return _t1014
                _t1015 = _t1013(msg)
                deconstruct_result312 = _t1015
                
                if deconstruct_result312 is not None:
                    _t1017 = self.pretty_break(deconstruct_result312)
                    _t1016 = _t1017
                else:
                    def _t1018(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('monoid_def'):
                            _t1019 = _dollar_dollar.monoid_def
                        else:
                            _t1019 = None
                        return _t1019
                    _t1020 = _t1018(msg)
                    deconstruct_result311 = _t1020
                    
                    if deconstruct_result311 is not None:
                        _t1022 = self.pretty_monoid_def(deconstruct_result311)
                        _t1021 = _t1022
                    else:
                        def _t1023(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('monus_def'):
                                _t1024 = _dollar_dollar.monus_def
                            else:
                                _t1024 = None
                            return _t1024
                        _t1025 = _t1023(msg)
                        deconstruct_result310 = _t1025
                        
                        if deconstruct_result310 is not None:
                            _t1027 = self.pretty_monus_def(deconstruct_result310)
                            _t1026 = _t1027
                        else:
                            raise ParseError('No matching rule for instruction')
                        _t1021 = _t1026
                    _t1016 = _t1021
                _t1011 = _t1016
            _t1006 = _t1011
        return _t1006

    def pretty_assign(self, msg: logic_pb2.Assign) -> Optional[Never]:
        def _t1028(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1029 = _dollar_dollar.attrs
            else:
                _t1029 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1029,)
        _t1030 = _t1028(msg)
        fields315 = _t1030
        assert fields315 is not None
        unwrapped_fields316 = fields315
        self.write('(')
        self.write('assign')
        self.indent()
        self.newline()
        field317 = unwrapped_fields316[0]
        _t1031 = self.pretty_relation_id(field317)
        self.newline()
        field318 = unwrapped_fields316[1]
        _t1032 = self.pretty_abstraction(field318)
        field319 = unwrapped_fields316[2]
        
        if field319 is not None:
            self.newline()
            assert field319 is not None
            opt_val320 = field319
            _t1034 = self.pretty_attrs(opt_val320)
            _t1033 = _t1034
        else:
            _t1033 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> Optional[Never]:
        def _t1035(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1036 = _dollar_dollar.attrs
            else:
                _t1036 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1036,)
        _t1037 = _t1035(msg)
        fields321 = _t1037
        assert fields321 is not None
        unwrapped_fields322 = fields321
        self.write('(')
        self.write('upsert')
        self.indent()
        self.newline()
        field323 = unwrapped_fields322[0]
        _t1038 = self.pretty_relation_id(field323)
        self.newline()
        field324 = unwrapped_fields322[1]
        _t1039 = self.pretty_abstraction_with_arity(field324)
        field325 = unwrapped_fields322[2]
        
        if field325 is not None:
            self.newline()
            assert field325 is not None
            opt_val326 = field325
            _t1041 = self.pretty_attrs(opt_val326)
            _t1040 = _t1041
        else:
            _t1040 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> Optional[Never]:
        def _t1042(_dollar_dollar):
            _t1043 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1043, _dollar_dollar[0].value,)
        _t1044 = _t1042(msg)
        fields327 = _t1044
        assert fields327 is not None
        unwrapped_fields328 = fields327
        self.write('(')
        field329 = unwrapped_fields328[0]
        _t1045 = self.pretty_bindings(field329)
        self.write(' ')
        field330 = unwrapped_fields328[1]
        _t1046 = self.pretty_formula(field330)
        self.write(')')
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> Optional[Never]:
        def _t1047(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1048 = _dollar_dollar.attrs
            else:
                _t1048 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1048,)
        _t1049 = _t1047(msg)
        fields331 = _t1049
        assert fields331 is not None
        unwrapped_fields332 = fields331
        self.write('(')
        self.write('break')
        self.indent()
        self.newline()
        field333 = unwrapped_fields332[0]
        _t1050 = self.pretty_relation_id(field333)
        self.newline()
        field334 = unwrapped_fields332[1]
        _t1051 = self.pretty_abstraction(field334)
        field335 = unwrapped_fields332[2]
        
        if field335 is not None:
            self.newline()
            assert field335 is not None
            opt_val336 = field335
            _t1053 = self.pretty_attrs(opt_val336)
            _t1052 = _t1053
        else:
            _t1052 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> Optional[Never]:
        def _t1054(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1055 = _dollar_dollar.attrs
            else:
                _t1055 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1055,)
        _t1056 = _t1054(msg)
        fields337 = _t1056
        assert fields337 is not None
        unwrapped_fields338 = fields337
        self.write('(')
        self.write('monoid')
        self.indent()
        self.newline()
        field339 = unwrapped_fields338[0]
        _t1057 = self.pretty_monoid(field339)
        self.newline()
        field340 = unwrapped_fields338[1]
        _t1058 = self.pretty_relation_id(field340)
        self.newline()
        field341 = unwrapped_fields338[2]
        _t1059 = self.pretty_abstraction_with_arity(field341)
        field342 = unwrapped_fields338[3]
        
        if field342 is not None:
            self.newline()
            assert field342 is not None
            opt_val343 = field342
            _t1061 = self.pretty_attrs(opt_val343)
            _t1060 = _t1061
        else:
            _t1060 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> Optional[Never]:
        def _t1062(_dollar_dollar):
            
            if _dollar_dollar.HasField('or_monoid'):
                _t1063 = _dollar_dollar.or_monoid
            else:
                _t1063 = None
            return _t1063
        _t1064 = _t1062(msg)
        deconstruct_result347 = _t1064
        
        if deconstruct_result347 is not None:
            _t1066 = self.pretty_or_monoid(deconstruct_result347)
            _t1065 = _t1066
        else:
            def _t1067(_dollar_dollar):
                
                if _dollar_dollar.HasField('min_monoid'):
                    _t1068 = _dollar_dollar.min_monoid
                else:
                    _t1068 = None
                return _t1068
            _t1069 = _t1067(msg)
            deconstruct_result346 = _t1069
            
            if deconstruct_result346 is not None:
                _t1071 = self.pretty_min_monoid(deconstruct_result346)
                _t1070 = _t1071
            else:
                def _t1072(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('max_monoid'):
                        _t1073 = _dollar_dollar.max_monoid
                    else:
                        _t1073 = None
                    return _t1073
                _t1074 = _t1072(msg)
                deconstruct_result345 = _t1074
                
                if deconstruct_result345 is not None:
                    _t1076 = self.pretty_max_monoid(deconstruct_result345)
                    _t1075 = _t1076
                else:
                    def _t1077(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('sum_monoid'):
                            _t1078 = _dollar_dollar.sum_monoid
                        else:
                            _t1078 = None
                        return _t1078
                    _t1079 = _t1077(msg)
                    deconstruct_result344 = _t1079
                    
                    if deconstruct_result344 is not None:
                        _t1081 = self.pretty_sum_monoid(deconstruct_result344)
                        _t1080 = _t1081
                    else:
                        raise ParseError('No matching rule for monoid')
                    _t1075 = _t1080
                _t1070 = _t1075
            _t1065 = _t1070
        return _t1065

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> Optional[Never]:
        def _t1082(_dollar_dollar):
            return _dollar_dollar
        _t1083 = _t1082(msg)
        fields348 = _t1083
        assert fields348 is not None
        unwrapped_fields349 = fields348
        self.write('(')
        self.write('or')
        self.write(')')
        return None

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid) -> Optional[Never]:
        def _t1084(_dollar_dollar):
            return _dollar_dollar.type
        _t1085 = _t1084(msg)
        fields350 = _t1085
        assert fields350 is not None
        unwrapped_fields351 = fields350
        self.write('(')
        self.write('min')
        self.indent()
        self.newline()
        _t1086 = self.pretty_type(unwrapped_fields351)
        self.dedent()
        self.write(')')
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> Optional[Never]:
        def _t1087(_dollar_dollar):
            return _dollar_dollar.type
        _t1088 = _t1087(msg)
        fields352 = _t1088
        assert fields352 is not None
        unwrapped_fields353 = fields352
        self.write('(')
        self.write('max')
        self.indent()
        self.newline()
        _t1089 = self.pretty_type(unwrapped_fields353)
        self.dedent()
        self.write(')')
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> Optional[Never]:
        def _t1090(_dollar_dollar):
            return _dollar_dollar.type
        _t1091 = _t1090(msg)
        fields354 = _t1091
        assert fields354 is not None
        unwrapped_fields355 = fields354
        self.write('(')
        self.write('sum')
        self.indent()
        self.newline()
        _t1092 = self.pretty_type(unwrapped_fields355)
        self.dedent()
        self.write(')')
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> Optional[Never]:
        def _t1093(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1094 = _dollar_dollar.attrs
            else:
                _t1094 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1094,)
        _t1095 = _t1093(msg)
        fields356 = _t1095
        assert fields356 is not None
        unwrapped_fields357 = fields356
        self.write('(')
        self.write('monus')
        self.indent()
        self.newline()
        field358 = unwrapped_fields357[0]
        _t1096 = self.pretty_monoid(field358)
        self.newline()
        field359 = unwrapped_fields357[1]
        _t1097 = self.pretty_relation_id(field359)
        self.newline()
        field360 = unwrapped_fields357[2]
        _t1098 = self.pretty_abstraction_with_arity(field360)
        field361 = unwrapped_fields357[3]
        
        if field361 is not None:
            self.newline()
            assert field361 is not None
            opt_val362 = field361
            _t1100 = self.pretty_attrs(opt_val362)
            _t1099 = _t1100
        else:
            _t1099 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> Optional[Never]:
        def _t1101(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1102 = _t1101(msg)
        fields363 = _t1102
        assert fields363 is not None
        unwrapped_fields364 = fields363
        self.write('(')
        self.write('functional_dependency')
        self.indent()
        self.newline()
        field365 = unwrapped_fields364[0]
        _t1103 = self.pretty_relation_id(field365)
        self.newline()
        field366 = unwrapped_fields364[1]
        _t1104 = self.pretty_abstraction(field366)
        self.newline()
        field367 = unwrapped_fields364[2]
        _t1105 = self.pretty_functional_dependency_keys(field367)
        self.newline()
        field368 = unwrapped_fields364[3]
        _t1106 = self.pretty_functional_dependency_values(field368)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]) -> Optional[Never]:
        def _t1107(_dollar_dollar):
            return _dollar_dollar
        _t1108 = _t1107(msg)
        fields369 = _t1108
        assert fields369 is not None
        unwrapped_fields370 = fields369
        self.write('(')
        self.write('keys')
        self.indent()
        if not len(unwrapped_fields370) == 0:
            self.newline()
            for i372, elem371 in enumerate(unwrapped_fields370):
                if (i372 > 0):
                    self.newline()
                _t1109 = self.pretty_var(elem371)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]) -> Optional[Never]:
        def _t1110(_dollar_dollar):
            return _dollar_dollar
        _t1111 = _t1110(msg)
        fields373 = _t1111
        assert fields373 is not None
        unwrapped_fields374 = fields373
        self.write('(')
        self.write('values')
        self.indent()
        if not len(unwrapped_fields374) == 0:
            self.newline()
            for i376, elem375 in enumerate(unwrapped_fields374):
                if (i376 > 0):
                    self.newline()
                _t1112 = self.pretty_var(elem375)
        self.dedent()
        self.write(')')
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> Optional[Never]:
        def _t1113(_dollar_dollar):
            
            if _dollar_dollar.HasField('rel_edb'):
                _t1114 = _dollar_dollar.rel_edb
            else:
                _t1114 = None
            return _t1114
        _t1115 = _t1113(msg)
        deconstruct_result379 = _t1115
        
        if deconstruct_result379 is not None:
            _t1117 = self.pretty_rel_edb(deconstruct_result379)
            _t1116 = _t1117
        else:
            def _t1118(_dollar_dollar):
                
                if _dollar_dollar.HasField('betree_relation'):
                    _t1119 = _dollar_dollar.betree_relation
                else:
                    _t1119 = None
                return _t1119
            _t1120 = _t1118(msg)
            deconstruct_result378 = _t1120
            
            if deconstruct_result378 is not None:
                _t1122 = self.pretty_betree_relation(deconstruct_result378)
                _t1121 = _t1122
            else:
                def _t1123(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('csv_data'):
                        _t1124 = _dollar_dollar.csv_data
                    else:
                        _t1124 = None
                    return _t1124
                _t1125 = _t1123(msg)
                deconstruct_result377 = _t1125
                
                if deconstruct_result377 is not None:
                    _t1127 = self.pretty_csv_data(deconstruct_result377)
                    _t1126 = _t1127
                else:
                    raise ParseError('No matching rule for data')
                _t1121 = _t1126
            _t1116 = _t1121
        return _t1116

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> Optional[Never]:
        def _t1128(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1129 = _t1128(msg)
        fields380 = _t1129
        assert fields380 is not None
        unwrapped_fields381 = fields380
        self.write('(')
        self.write('rel_edb')
        self.indent()
        self.newline()
        field382 = unwrapped_fields381[0]
        _t1130 = self.pretty_relation_id(field382)
        self.newline()
        field383 = unwrapped_fields381[1]
        _t1131 = self.pretty_rel_edb_path(field383)
        self.newline()
        field384 = unwrapped_fields381[2]
        _t1132 = self.pretty_rel_edb_types(field384)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_edb_path(self, msg: Sequence[str]) -> Optional[Never]:
        def _t1133(_dollar_dollar):
            return _dollar_dollar
        _t1134 = _t1133(msg)
        fields385 = _t1134
        assert fields385 is not None
        unwrapped_fields386 = fields385
        self.write('[')
        for i388, elem387 in enumerate(unwrapped_fields386):
            if (i388 > 0):
                self.newline()
            self.write(self.format_string_value(elem387))
        self.write(']')
        return None

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[Never]:
        def _t1135(_dollar_dollar):
            return _dollar_dollar
        _t1136 = _t1135(msg)
        fields389 = _t1136
        assert fields389 is not None
        unwrapped_fields390 = fields389
        self.write('[')
        for i392, elem391 in enumerate(unwrapped_fields390):
            if (i392 > 0):
                self.newline()
            _t1137 = self.pretty_type(elem391)
        self.write(']')
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> Optional[Never]:
        def _t1138(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1139 = _t1138(msg)
        fields393 = _t1139
        assert fields393 is not None
        unwrapped_fields394 = fields393
        self.write('(')
        self.write('betree_relation')
        self.indent()
        self.newline()
        field395 = unwrapped_fields394[0]
        _t1140 = self.pretty_relation_id(field395)
        self.newline()
        field396 = unwrapped_fields394[1]
        _t1141 = self.pretty_betree_info(field396)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> Optional[Never]:
        def _t1142(_dollar_dollar):
            _t1143 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1143,)
        _t1144 = _t1142(msg)
        fields397 = _t1144
        assert fields397 is not None
        unwrapped_fields398 = fields397
        self.write('(')
        self.write('betree_info')
        self.indent()
        self.newline()
        field399 = unwrapped_fields398[0]
        _t1145 = self.pretty_betree_info_key_types(field399)
        self.newline()
        field400 = unwrapped_fields398[1]
        _t1146 = self.pretty_betree_info_value_types(field400)
        self.newline()
        field401 = unwrapped_fields398[2]
        _t1147 = self.pretty_config_dict(field401)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[Never]:
        def _t1148(_dollar_dollar):
            return _dollar_dollar
        _t1149 = _t1148(msg)
        fields402 = _t1149
        assert fields402 is not None
        unwrapped_fields403 = fields402
        self.write('(')
        self.write('key_types')
        self.indent()
        if not len(unwrapped_fields403) == 0:
            self.newline()
            for i405, elem404 in enumerate(unwrapped_fields403):
                if (i405 > 0):
                    self.newline()
                _t1150 = self.pretty_type(elem404)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[Never]:
        def _t1151(_dollar_dollar):
            return _dollar_dollar
        _t1152 = _t1151(msg)
        fields406 = _t1152
        assert fields406 is not None
        unwrapped_fields407 = fields406
        self.write('(')
        self.write('value_types')
        self.indent()
        if not len(unwrapped_fields407) == 0:
            self.newline()
            for i409, elem408 in enumerate(unwrapped_fields407):
                if (i409 > 0):
                    self.newline()
                _t1153 = self.pretty_type(elem408)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> Optional[Never]:
        def _t1154(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1155 = _t1154(msg)
        fields410 = _t1155
        assert fields410 is not None
        unwrapped_fields411 = fields410
        self.write('(')
        self.write('csv_data')
        self.indent()
        self.newline()
        field412 = unwrapped_fields411[0]
        _t1156 = self.pretty_csvlocator(field412)
        self.newline()
        field413 = unwrapped_fields411[1]
        _t1157 = self.pretty_csv_config(field413)
        self.newline()
        field414 = unwrapped_fields411[2]
        _t1158 = self.pretty_csv_columns(field414)
        self.newline()
        field415 = unwrapped_fields411[3]
        _t1159 = self.pretty_csv_asof(field415)
        self.dedent()
        self.write(')')
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> Optional[Never]:
        def _t1160(_dollar_dollar):
            
            if not len(_dollar_dollar.paths) == 0:
                _t1161 = _dollar_dollar.paths
            else:
                _t1161 = None
            
            if _dollar_dollar.inline_data.decode('utf-8') != '':
                _t1162 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1162 = None
            return (_t1161, _t1162,)
        _t1163 = _t1160(msg)
        fields416 = _t1163
        assert fields416 is not None
        unwrapped_fields417 = fields416
        self.write('(')
        self.write('csv_locator')
        self.indent()
        field418 = unwrapped_fields417[0]
        
        if field418 is not None:
            self.newline()
            assert field418 is not None
            opt_val419 = field418
            _t1165 = self.pretty_csv_locator_paths(opt_val419)
            _t1164 = _t1165
        else:
            _t1164 = None
        field420 = unwrapped_fields417[1]
        
        if field420 is not None:
            self.newline()
            assert field420 is not None
            opt_val421 = field420
            _t1167 = self.pretty_csv_locator_inline_data(opt_val421)
            _t1166 = _t1167
        else:
            _t1166 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_locator_paths(self, msg: Sequence[str]) -> Optional[Never]:
        def _t1168(_dollar_dollar):
            return _dollar_dollar
        _t1169 = _t1168(msg)
        fields422 = _t1169
        assert fields422 is not None
        unwrapped_fields423 = fields422
        self.write('(')
        self.write('paths')
        self.indent()
        if not len(unwrapped_fields423) == 0:
            self.newline()
            for i425, elem424 in enumerate(unwrapped_fields423):
                if (i425 > 0):
                    self.newline()
                self.write(self.format_string_value(elem424))
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_locator_inline_data(self, msg: str) -> Optional[Never]:
        def _t1170(_dollar_dollar):
            return _dollar_dollar
        _t1171 = _t1170(msg)
        fields426 = _t1171
        assert fields426 is not None
        unwrapped_fields427 = fields426
        self.write('(')
        self.write('inline_data')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields427))
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig) -> Optional[Never]:
        def _t1172(_dollar_dollar):
            _t1173 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1173
        _t1174 = _t1172(msg)
        fields428 = _t1174
        assert fields428 is not None
        unwrapped_fields429 = fields428
        self.write('(')
        self.write('csv_config')
        self.indent()
        self.newline()
        _t1175 = self.pretty_config_dict(unwrapped_fields429)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]) -> Optional[Never]:
        def _t1176(_dollar_dollar):
            return _dollar_dollar
        _t1177 = _t1176(msg)
        fields430 = _t1177
        assert fields430 is not None
        unwrapped_fields431 = fields430
        self.write('(')
        self.write('columns')
        self.indent()
        if not len(unwrapped_fields431) == 0:
            self.newline()
            for i433, elem432 in enumerate(unwrapped_fields431):
                if (i433 > 0):
                    self.newline()
                _t1178 = self.pretty_csv_column(elem432)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> Optional[Never]:
        def _t1179(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1180 = _t1179(msg)
        fields434 = _t1180
        assert fields434 is not None
        unwrapped_fields435 = fields434
        self.write('(')
        self.write('column')
        self.indent()
        self.newline()
        field436 = unwrapped_fields435[0]
        self.write(self.format_string_value(field436))
        self.newline()
        field437 = unwrapped_fields435[1]
        _t1181 = self.pretty_relation_id(field437)
        self.newline()
        self.write('[')
        field438 = unwrapped_fields435[2]
        for i440, elem439 in enumerate(field438):
            if (i440 > 0):
                self.newline()
            _t1182 = self.pretty_type(elem439)
        self.write(']')
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_asof(self, msg: str) -> Optional[Never]:
        def _t1183(_dollar_dollar):
            return _dollar_dollar
        _t1184 = _t1183(msg)
        fields441 = _t1184
        assert fields441 is not None
        unwrapped_fields442 = fields441
        self.write('(')
        self.write('asof')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields442))
        self.dedent()
        self.write(')')
        return None

    def pretty_undefine(self, msg: transactions_pb2.Undefine) -> Optional[Never]:
        def _t1185(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1186 = _t1185(msg)
        fields443 = _t1186
        assert fields443 is not None
        unwrapped_fields444 = fields443
        self.write('(')
        self.write('undefine')
        self.indent()
        self.newline()
        _t1187 = self.pretty_fragment_id(unwrapped_fields444)
        self.dedent()
        self.write(')')
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> Optional[Never]:
        def _t1188(_dollar_dollar):
            return _dollar_dollar.relations
        _t1189 = _t1188(msg)
        fields445 = _t1189
        assert fields445 is not None
        unwrapped_fields446 = fields445
        self.write('(')
        self.write('context')
        self.indent()
        if not len(unwrapped_fields446) == 0:
            self.newline()
            for i448, elem447 in enumerate(unwrapped_fields446):
                if (i448 > 0):
                    self.newline()
                _t1190 = self.pretty_relation_id(elem447)
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]) -> Optional[Never]:
        def _t1191(_dollar_dollar):
            return _dollar_dollar
        _t1192 = _t1191(msg)
        fields449 = _t1192
        assert fields449 is not None
        unwrapped_fields450 = fields449
        self.write('(')
        self.write('reads')
        self.indent()
        if not len(unwrapped_fields450) == 0:
            self.newline()
            for i452, elem451 in enumerate(unwrapped_fields450):
                if (i452 > 0):
                    self.newline()
                _t1193 = self.pretty_read(elem451)
        self.dedent()
        self.write(')')
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> Optional[Never]:
        def _t1194(_dollar_dollar):
            
            if _dollar_dollar.HasField('demand'):
                _t1195 = _dollar_dollar.demand
            else:
                _t1195 = None
            return _t1195
        _t1196 = _t1194(msg)
        deconstruct_result457 = _t1196
        
        if deconstruct_result457 is not None:
            _t1198 = self.pretty_demand(deconstruct_result457)
            _t1197 = _t1198
        else:
            def _t1199(_dollar_dollar):
                
                if _dollar_dollar.HasField('output'):
                    _t1200 = _dollar_dollar.output
                else:
                    _t1200 = None
                return _t1200
            _t1201 = _t1199(msg)
            deconstruct_result456 = _t1201
            
            if deconstruct_result456 is not None:
                _t1203 = self.pretty_output(deconstruct_result456)
                _t1202 = _t1203
            else:
                def _t1204(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('what_if'):
                        _t1205 = _dollar_dollar.what_if
                    else:
                        _t1205 = None
                    return _t1205
                _t1206 = _t1204(msg)
                deconstruct_result455 = _t1206
                
                if deconstruct_result455 is not None:
                    _t1208 = self.pretty_what_if(deconstruct_result455)
                    _t1207 = _t1208
                else:
                    def _t1209(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('abort'):
                            _t1210 = _dollar_dollar.abort
                        else:
                            _t1210 = None
                        return _t1210
                    _t1211 = _t1209(msg)
                    deconstruct_result454 = _t1211
                    
                    if deconstruct_result454 is not None:
                        _t1213 = self.pretty_abort(deconstruct_result454)
                        _t1212 = _t1213
                    else:
                        def _t1214(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('export'):
                                _t1215 = _dollar_dollar.export
                            else:
                                _t1215 = None
                            return _t1215
                        _t1216 = _t1214(msg)
                        deconstruct_result453 = _t1216
                        
                        if deconstruct_result453 is not None:
                            _t1218 = self.pretty_export(deconstruct_result453)
                            _t1217 = _t1218
                        else:
                            raise ParseError('No matching rule for read')
                        _t1212 = _t1217
                    _t1207 = _t1212
                _t1202 = _t1207
            _t1197 = _t1202
        return _t1197

    def pretty_demand(self, msg: transactions_pb2.Demand) -> Optional[Never]:
        def _t1219(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1220 = _t1219(msg)
        fields458 = _t1220
        assert fields458 is not None
        unwrapped_fields459 = fields458
        self.write('(')
        self.write('demand')
        self.indent()
        self.newline()
        _t1221 = self.pretty_relation_id(unwrapped_fields459)
        self.dedent()
        self.write(')')
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> Optional[Never]:
        def _t1222(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        _t1223 = _t1222(msg)
        fields460 = _t1223
        assert fields460 is not None
        unwrapped_fields461 = fields460
        self.write('(')
        self.write('output')
        self.indent()
        self.newline()
        field462 = unwrapped_fields461[0]
        _t1224 = self.pretty_name(field462)
        self.newline()
        field463 = unwrapped_fields461[1]
        _t1225 = self.pretty_relation_id(field463)
        self.dedent()
        self.write(')')
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> Optional[Never]:
        def _t1226(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1227 = _t1226(msg)
        fields464 = _t1227
        assert fields464 is not None
        unwrapped_fields465 = fields464
        self.write('(')
        self.write('what_if')
        self.indent()
        self.newline()
        field466 = unwrapped_fields465[0]
        _t1228 = self.pretty_name(field466)
        self.newline()
        field467 = unwrapped_fields465[1]
        _t1229 = self.pretty_epoch(field467)
        self.dedent()
        self.write(')')
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> Optional[Never]:
        def _t1230(_dollar_dollar):
            
            if _dollar_dollar.name != 'abort':
                _t1231 = _dollar_dollar.name
            else:
                _t1231 = None
            return (_t1231, _dollar_dollar.relation_id,)
        _t1232 = _t1230(msg)
        fields468 = _t1232
        assert fields468 is not None
        unwrapped_fields469 = fields468
        self.write('(')
        self.write('abort')
        self.indent()
        field470 = unwrapped_fields469[0]
        
        if field470 is not None:
            self.newline()
            assert field470 is not None
            opt_val471 = field470
            _t1234 = self.pretty_name(opt_val471)
            _t1233 = _t1234
        else:
            _t1233 = None
        self.newline()
        field472 = unwrapped_fields469[1]
        _t1235 = self.pretty_relation_id(field472)
        self.dedent()
        self.write(')')
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> Optional[Never]:
        def _t1236(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1237 = _t1236(msg)
        fields473 = _t1237
        assert fields473 is not None
        unwrapped_fields474 = fields473
        self.write('(')
        self.write('export')
        self.indent()
        self.newline()
        _t1238 = self.pretty_export_csv_config(unwrapped_fields474)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> Optional[Never]:
        def _t1239(_dollar_dollar):
            _t1240 = self.deconstruct_export_csv_config(_dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1240,)
        _t1241 = _t1239(msg)
        fields475 = _t1241
        assert fields475 is not None
        unwrapped_fields476 = fields475
        self.write('(')
        self.write('export_csv_config')
        self.indent()
        self.newline()
        field477 = unwrapped_fields476[0]
        _t1242 = self.pretty_export_csv_path(field477)
        self.newline()
        field478 = unwrapped_fields476[1]
        _t1243 = self.pretty_export_csv_columns(field478)
        self.newline()
        field479 = unwrapped_fields476[2]
        _t1244 = self.pretty_config_dict(field479)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_path(self, msg: str) -> Optional[Never]:
        def _t1245(_dollar_dollar):
            return _dollar_dollar
        _t1246 = _t1245(msg)
        fields480 = _t1246
        assert fields480 is not None
        unwrapped_fields481 = fields480
        self.write('(')
        self.write('path')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields481))
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]) -> Optional[Never]:
        def _t1247(_dollar_dollar):
            return _dollar_dollar
        _t1248 = _t1247(msg)
        fields482 = _t1248
        assert fields482 is not None
        unwrapped_fields483 = fields482
        self.write('(')
        self.write('columns')
        self.indent()
        if not len(unwrapped_fields483) == 0:
            self.newline()
            for i485, elem484 in enumerate(unwrapped_fields483):
                if (i485 > 0):
                    self.newline()
                _t1249 = self.pretty_export_csv_column(elem484)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> Optional[Never]:
        def _t1250(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1251 = _t1250(msg)
        fields486 = _t1251
        assert fields486 is not None
        unwrapped_fields487 = fields486
        self.write('(')
        self.write('column')
        self.indent()
        self.newline()
        field488 = unwrapped_fields487[0]
        self.write(self.format_string_value(field488))
        self.newline()
        field489 = unwrapped_fields487[1]
        _t1252 = self.pretty_relation_id(field489)
        self.dedent()
        self.write(')')
        return None


def pretty(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message, resolving relation IDs to names."""
    printer = PrettyPrinter(io)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()


def pretty_debug(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message with raw relation IDs and debug info appended as comments."""
    printer = PrettyPrinter(io, print_symbolic_relation_ids=False)
    printer.pretty_transaction(msg)
    printer.newline()
    printer.write_debug_info()
    return printer.get_output()
