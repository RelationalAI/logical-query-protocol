"""
Auto-generated pretty printer.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the pretty printer, edit the generator code
in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli /Users/nystrom/rai/nn-meta-13-pretty/proto/relationalai/lqp/v1/logic.proto /Users/nystrom/rai/nn-meta-13-pretty/proto/relationalai/lqp/v1/fragments.proto /Users/nystrom/rai/nn-meta-13-pretty/proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer python
"""

from io import StringIO
from typing import Any, IO, Never, Optional

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    pass


class PrettyPrinter:
    """Pretty printer for protobuf messages."""

    def __init__(self, io: Optional[IO[str]] = None):
        self.io = io if io is not None else StringIO()
        self.indent_level = 0
        self.at_line_start = True
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

    def format_decimal(self, msg) -> str:
        """Format a DecimalValue as '<digits>.<digits>d<precision>'."""
        int_val = (msg.value.high << 64) | msg.value.low
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

    def format_int128(self, msg) -> str:
        """Format an Int128Value protobuf message as a string with i128 suffix."""
        value = (msg.high << 64) | msg.low
        if msg.high & (1 << 63):
            value -= (1 << 128)
        return str(value) + "i128"

    def format_uint128(self, msg) -> str:
        """Format a UInt128Value protobuf message as a hex string."""
        value = (msg.high << 64) | msg.low
        return f"0x{value:x}"

    def fragment_id_to_string(self, msg) -> str:
        """Convert FragmentId to string representation."""
        return msg.id.decode('utf-8') if msg.id else ""

    def start_pretty_fragment(self, msg) -> None:
        """Extract debug info from Fragment for relation ID lookup."""
        debug_info = msg.debug_info
        for rid, name in zip(debug_info.ids, debug_info.orig_names):
            self._debug_info[(rid.id_low, rid.id_high)] = name

    def relation_id_to_string(self, msg):
        """Convert RelationId to string representation using debug info."""
        return self._debug_info.get((msg.id_low, msg.id_high), "")

    def relation_id_to_int(self, msg):
        """Convert RelationId to int if it fits in signed 64-bit range."""
        value = (msg.id_high << 64) | msg.id_low
        if value <= 0x7FFFFFFFFFFFFFFF:
            return value
        return None

    def relation_id_to_uint128(self, msg):
        """Convert RelationId to UInt128Value representation."""
        return logic_pb2.UInt128Value(low=msg.id_low, high=msg.id_high)

    def format_string_value(self, s: str) -> str:
        """Format a string value with double quotes for LQP output."""
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return '"' + escaped + '"'

    # --- Helper functions ---

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        if (value is not None and value.HasField('int_value')):
            return value.int_value
        return default

    def _extract_value_float64(self, value: Optional[logic_pb2.Value], default: float) -> float:
        if (value is not None and value.HasField('float_value')):
            return value.float_value
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        if (value is not None and value.HasField('string_value')):
            return value.string_value
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        if (value is not None and value.HasField('boolean_value')):
            return value.boolean_value
        return default

    def _extract_value_bytes(self, value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        if (value is not None and value.HasField('string_value')):
            return value.string_value.encode()
        return default

    def _extract_value_uint128(self, value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        if (value is not None and value.HasField('uint128_value')):
            return value.uint128_value
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: list[str]) -> list[str]:
        if (value is not None and value.HasField('string_value')):
            return [value.string_value]
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        if (value is not None and value.HasField('int_value')):
            return value.int_value
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        if (value is not None and value.HasField('float_value')):
            return value.float_value
        return None

    def _try_extract_value_string(self, value: Optional[logic_pb2.Value]) -> Optional[str]:
        if (value is not None and value.HasField('string_value')):
            return value.string_value
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        if (value is not None and value.HasField('string_value')):
            return value.string_value.encode()
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        if (value is not None and value.HasField('uint128_value')):
            return value.uint128_value
        return None

    def _try_extract_value_string_list(self, value: Optional[logic_pb2.Value]) -> Optional[list[str]]:
        if (value is not None and value.HasField('string_value')):
            return [value.string_value]
        return None

    def construct_csv_config(self, config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1289 = self._extract_value_int64(config.get('csv_header_row'), 1)
        header_row = _t1289
        _t1290 = self._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1290
        _t1291 = self._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1291
        _t1292 = self._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1292
        _t1293 = self._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1293
        _t1294 = self._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1294
        _t1295 = self._extract_value_string(config.get('csv_comment'), '')
        comment = _t1295
        _t1296 = self._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1296
        _t1297 = self._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1297
        _t1298 = self._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1298
        _t1299 = self._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1299
        _t1300 = logic_pb2.CSVConfig(header_row=int(header_row), skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1300

    def construct_betree_info(self, key_types: list[logic_pb2.Type], value_types: list[logic_pb2.Type], config_dict: list[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1301 = self._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t1301
        _t1302 = self._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t1302
        _t1303 = self._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t1303
        _t1304 = self._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t1304
        _t1305 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1305
        _t1306 = self._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t1306
        _t1307 = self._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t1307
        _t1308 = self._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t1308
        _t1309 = self._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t1309
        _t1310 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1310
        _t1311 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1311

    def default_configure(self) -> transactions_pb2.Configure:
        _t1312 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1312
        _t1313 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1313

    def construct_configure(self, config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
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
        _t1314 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1314
        _t1315 = self._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1315
        _t1316 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1316

    def export_csv_config(self, path: str, columns: list[transactions_pb2.ExportCSVColumn], config_dict: list[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1317 = self._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1317
        _t1318 = self._extract_value_string(config.get('compression'), '')
        compression = _t1318
        _t1319 = self._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1319
        _t1320 = self._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1320
        _t1321 = self._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1321
        _t1322 = self._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1322
        _t1323 = self._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1323
        _t1324 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1324

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1325 = logic_pb2.Value(int_value=v)
        return _t1325

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1326 = logic_pb2.Value(float_value=v)
        return _t1326

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1327 = logic_pb2.Value(string_value=v)
        return _t1327

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1328 = logic_pb2.Value(boolean_value=v)
        return _t1328

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1329 = logic_pb2.Value(uint128_value=v)
        return _t1329

    def is_default_configure(self, cfg: transactions_pb2.Configure) -> bool:
        if cfg.semantics_version != 0:
            return False
        if cfg.ivm_config.level != transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
            return False
        return True

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1331 = self._make_value_string('auto')
            result.append(('ivm.maintenance_level', _t1331,))
            _t1330 = None
        else:
            
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1333 = self._make_value_string('all')
                result.append(('ivm.maintenance_level', _t1333,))
                _t1332 = None
            else:
                
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1335 = self._make_value_string('off')
                    result.append(('ivm.maintenance_level', _t1335,))
                    _t1334 = None
                else:
                    _t1334 = None
                _t1332 = _t1334
            _t1330 = _t1332
        _t1336 = self._make_value_int64(msg.semantics_version)
        result.append(('semantics_version', _t1336,))
        return result

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        
        if msg.header_row != 1:
            _t1338 = self._make_value_int64(int(msg.header_row))
            result.append(('csv_header_row', _t1338,))
            _t1337 = None
        else:
            _t1337 = None
        
        if msg.skip != 0:
            _t1340 = self._make_value_int64(msg.skip)
            result.append(('csv_skip', _t1340,))
            _t1339 = None
        else:
            _t1339 = None
        
        if msg.new_line != '':
            _t1342 = self._make_value_string(msg.new_line)
            result.append(('csv_new_line', _t1342,))
            _t1341 = None
        else:
            _t1341 = None
        
        if msg.delimiter != ',':
            _t1344 = self._make_value_string(msg.delimiter)
            result.append(('csv_delimiter', _t1344,))
            _t1343 = None
        else:
            _t1343 = None
        
        if msg.quotechar != '"':
            _t1346 = self._make_value_string(msg.quotechar)
            result.append(('csv_quotechar', _t1346,))
            _t1345 = None
        else:
            _t1345 = None
        
        if msg.escapechar != '"':
            _t1348 = self._make_value_string(msg.escapechar)
            result.append(('csv_escapechar', _t1348,))
            _t1347 = None
        else:
            _t1347 = None
        
        if msg.comment != '':
            _t1350 = self._make_value_string(msg.comment)
            result.append(('csv_comment', _t1350,))
            _t1349 = None
        else:
            _t1349 = None
        
        if not len(msg.missing_strings) == 0:
            _t1352 = self._make_value_string(msg.missing_strings[0])
            result.append(('csv_missing_strings', _t1352,))
            _t1351 = None
        else:
            _t1351 = None
        
        if msg.decimal_separator != '.':
            _t1354 = self._make_value_string(msg.decimal_separator)
            result.append(('csv_decimal_separator', _t1354,))
            _t1353 = None
        else:
            _t1353 = None
        
        if msg.encoding != 'utf-8':
            _t1356 = self._make_value_string(msg.encoding)
            result.append(('csv_encoding', _t1356,))
            _t1355 = None
        else:
            _t1355 = None
        
        if msg.compression != 'auto':
            _t1358 = self._make_value_string(msg.compression)
            result.append(('csv_compression', _t1358,))
            _t1357 = None
        else:
            _t1357 = None
        return result

    def _maybe_push_float64(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[float]) -> None:
        
        if val is not None:
            _t1360 = self._make_value_float64(val)
            result.append((key, _t1360,))
            _t1359 = None
        else:
            _t1359 = None
        return None

    def _maybe_push_int64(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[int]) -> None:
        
        if val is not None:
            _t1362 = self._make_value_int64(val)
            result.append((key, _t1362,))
            _t1361 = None
        else:
            _t1361 = None
        return None

    def _maybe_push_uint128(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[logic_pb2.UInt128Value]) -> None:
        
        if val is not None:
            _t1364 = self._make_value_uint128(val)
            result.append((key, _t1364,))
            _t1363 = None
        else:
            _t1363 = None
        return None

    def _maybe_push_bytes_as_string(self, result: list[tuple[str, logic_pb2.Value]], key: str, val: Optional[bytes]) -> None:
        
        if val is not None:
            _t1366 = self._make_value_string(val.decode('utf-8'))
            result.append((key, _t1366,))
            _t1365 = None
        else:
            _t1365 = None
        return None

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1367 = self._maybe_push_float64(result, 'betree_config_epsilon', msg.storage_config.epsilon)
        _t1368 = self._maybe_push_int64(result, 'betree_config_max_pivots', msg.storage_config.max_pivots)
        _t1369 = self._maybe_push_int64(result, 'betree_config_max_deltas', msg.storage_config.max_deltas)
        _t1370 = self._maybe_push_int64(result, 'betree_config_max_leaf', msg.storage_config.max_leaf)
        
        if msg.relation_locator.HasField('root_pageid'):
            _t1372 = self._maybe_push_uint128(result, 'betree_locator_root_pageid', msg.relation_locator.root_pageid)
            _t1371 = _t1372
        else:
            _t1371 = None
        
        if msg.relation_locator.HasField('inline_data'):
            _t1374 = self._maybe_push_bytes_as_string(result, 'betree_locator_inline_data', msg.relation_locator.inline_data)
            _t1373 = _t1374
        else:
            _t1373 = None
        _t1375 = self._maybe_push_int64(result, 'betree_locator_element_count', msg.relation_locator.element_count)
        _t1376 = self._maybe_push_int64(result, 'betree_locator_tree_height', msg.relation_locator.tree_height)
        return result

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        
        if (msg.partition_size is not None and msg.partition_size != 0):
            _t1378 = self._make_value_int64(msg.partition_size)
            result.append(('partition_size', _t1378,))
            _t1377 = None
        else:
            _t1377 = None
        
        if (msg.compression is not None and msg.compression != ''):
            _t1380 = self._make_value_string(msg.compression)
            result.append(('compression', _t1380,))
            _t1379 = None
        else:
            _t1379 = None
        
        if msg.syntax_header_row is not None:
            _t1382 = self._make_value_boolean(msg.syntax_header_row)
            result.append(('syntax_header_row', _t1382,))
            _t1381 = None
        else:
            _t1381 = None
        
        if (msg.syntax_missing_string is not None and msg.syntax_missing_string != ''):
            _t1384 = self._make_value_string(msg.syntax_missing_string)
            result.append(('syntax_missing_string', _t1384,))
            _t1383 = None
        else:
            _t1383 = None
        
        if (msg.syntax_delim is not None and msg.syntax_delim != ','):
            _t1386 = self._make_value_string(msg.syntax_delim)
            result.append(('syntax_delim', _t1386,))
            _t1385 = None
        else:
            _t1385 = None
        
        if (msg.syntax_quotechar is not None and msg.syntax_quotechar != '"'):
            _t1388 = self._make_value_string(msg.syntax_quotechar)
            result.append(('syntax_quotechar', _t1388,))
            _t1387 = None
        else:
            _t1387 = None
        
        if (msg.syntax_escapechar is not None and msg.syntax_escapechar != '\\'):
            _t1390 = self._make_value_string(msg.syntax_escapechar)
            result.append(('syntax_escapechar', _t1390,))
            _t1389 = None
        else:
            _t1389 = None
        return result

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

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        return (abs.vars, [],)

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)

    # --- Pretty-print methods ---

    def pretty_transaction(self, msg: transactions_pb2.Transaction) -> Optional[Never]:
        def _t491(_dollar_dollar):
            
            if _dollar_dollar.HasField('configure'):
                _t492 = _dollar_dollar.configure
            else:
                _t492 = None
            
            if _dollar_dollar.HasField('sync'):
                _t493 = _dollar_dollar.sync
            else:
                _t493 = None
            return (_t492, _t493, _dollar_dollar.epochs,)
        _t494 = _t491(msg)
        fields0 = _t494
        unwrapped_fields1 = fields0
        self.write('(')
        self.write('transaction')
        self.indent()
        field2 = unwrapped_fields1[0]
        
        if field2 is not None:
            self.newline()
            opt_val3 = field2
            _t496 = self.pretty_configure(opt_val3)
            _t495 = _t496
        else:
            _t495 = None
        field4 = unwrapped_fields1[1]
        
        if field4 is not None:
            self.newline()
            opt_val5 = field4
            _t498 = self.pretty_sync(opt_val5)
            _t497 = _t498
        else:
            _t497 = None
        field6 = unwrapped_fields1[2]
        if not len(field6) == 0:
            self.newline()
            for i8, elem7 in enumerate(field6):
                
                if (i8 > 0):
                    self.newline()
                    _t499 = None
                else:
                    _t499 = None
                _t500 = self.pretty_epoch(elem7)
        self.dedent()
        self.write(')')
        return None

    def pretty_configure(self, msg: transactions_pb2.Configure) -> Optional[Never]:
        def _t501(_dollar_dollar):
            _t502 = self.deconstruct_configure(_dollar_dollar)
            return _t502
        _t503 = _t501(msg)
        fields9 = _t503
        unwrapped_fields10 = fields9
        self.write('(')
        self.write('configure')
        self.indent()
        self.newline()
        _t504 = self.pretty_config_dict(unwrapped_fields10)
        self.dedent()
        self.write(')')
        return None

    def pretty_config_dict(self, msg: list[tuple[str, logic_pb2.Value]]) -> Optional[Never]:
        def _t505(_dollar_dollar):
            return _dollar_dollar
        _t506 = _t505(msg)
        fields11 = _t506
        unwrapped_fields12 = fields11
        self.write('{')
        if not len(unwrapped_fields12) == 0:
            self.write(' ')
            for i14, elem13 in enumerate(unwrapped_fields12):
                
                if (i14 > 0):
                    self.newline()
                    _t507 = None
                else:
                    _t507 = None
                _t508 = self.pretty_config_key_value(elem13)
        self.write('}')
        return None

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]) -> Optional[Never]:
        def _t509(_dollar_dollar):
            return (_dollar_dollar[0], _dollar_dollar[1],)
        _t510 = _t509(msg)
        fields15 = _t510
        unwrapped_fields16 = fields15
        self.write(':')
        field17 = unwrapped_fields16[0]
        self.write(field17)
        self.write(' ')
        field18 = unwrapped_fields16[1]
        _t511 = self.pretty_value(field18)
        return _t511

    def pretty_value(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t512(_dollar_dollar):
            
            if _dollar_dollar.HasField('date_value'):
                _t513 = _dollar_dollar.date_value
            else:
                _t513 = None
            return _t513
        _t514 = _t512(msg)
        deconstruct_result29 = _t514
        
        if deconstruct_result29 is not None:
            _t516 = self.pretty_date(deconstruct_result29)
            _t515 = _t516
        else:
            def _t517(_dollar_dollar):
                
                if _dollar_dollar.HasField('datetime_value'):
                    _t518 = _dollar_dollar.datetime_value
                else:
                    _t518 = None
                return _t518
            _t519 = _t517(msg)
            deconstruct_result28 = _t519
            
            if deconstruct_result28 is not None:
                _t521 = self.pretty_datetime(deconstruct_result28)
                _t520 = _t521
            else:
                def _t522(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('string_value'):
                        _t523 = _dollar_dollar.string_value
                    else:
                        _t523 = None
                    return _t523
                _t524 = _t522(msg)
                deconstruct_result27 = _t524
                
                if deconstruct_result27 is not None:
                    self.write(self.format_string_value(deconstruct_result27))
                    _t525 = None
                else:
                    def _t526(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('int_value'):
                            _t527 = _dollar_dollar.int_value
                        else:
                            _t527 = None
                        return _t527
                    _t528 = _t526(msg)
                    deconstruct_result26 = _t528
                    
                    if deconstruct_result26 is not None:
                        self.write(str(deconstruct_result26))
                        _t529 = None
                    else:
                        def _t530(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('float_value'):
                                _t531 = _dollar_dollar.float_value
                            else:
                                _t531 = None
                            return _t531
                        _t532 = _t530(msg)
                        deconstruct_result25 = _t532
                        
                        if deconstruct_result25 is not None:
                            self.write(str(deconstruct_result25))
                            _t533 = None
                        else:
                            def _t534(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('uint128_value'):
                                    _t535 = _dollar_dollar.uint128_value
                                else:
                                    _t535 = None
                                return _t535
                            _t536 = _t534(msg)
                            deconstruct_result24 = _t536
                            
                            if deconstruct_result24 is not None:
                                self.write(self.format_uint128(deconstruct_result24))
                                _t537 = None
                            else:
                                def _t538(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('int128_value'):
                                        _t539 = _dollar_dollar.int128_value
                                    else:
                                        _t539 = None
                                    return _t539
                                _t540 = _t538(msg)
                                deconstruct_result23 = _t540
                                
                                if deconstruct_result23 is not None:
                                    self.write(self.format_int128(deconstruct_result23))
                                    _t541 = None
                                else:
                                    def _t542(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('decimal_value'):
                                            _t543 = _dollar_dollar.decimal_value
                                        else:
                                            _t543 = None
                                        return _t543
                                    _t544 = _t542(msg)
                                    deconstruct_result22 = _t544
                                    
                                    if deconstruct_result22 is not None:
                                        self.write(self.format_decimal(deconstruct_result22))
                                        _t545 = None
                                    else:
                                        def _t546(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('boolean_value'):
                                                _t547 = _dollar_dollar.boolean_value
                                            else:
                                                _t547 = None
                                            return _t547
                                        _t548 = _t546(msg)
                                        deconstruct_result21 = _t548
                                        
                                        if deconstruct_result21 is not None:
                                            _t550 = self.pretty_boolean_value(deconstruct_result21)
                                            _t549 = _t550
                                        else:
                                            def _t551(_dollar_dollar):
                                                return _dollar_dollar
                                            _t552 = _t551(msg)
                                            fields19 = _t552
                                            unwrapped_fields20 = fields19
                                            self.write('missing')
                                            _t549 = None
                                        _t545 = _t549
                                    _t541 = _t545
                                _t537 = _t541
                            _t533 = _t537
                        _t529 = _t533
                    _t525 = _t529
                _t520 = _t525
            _t515 = _t520
        return _t515

    def pretty_date(self, msg: logic_pb2.DateValue) -> Optional[Never]:
        def _t553(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
        _t554 = _t553(msg)
        fields30 = _t554
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
        def _t555(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
        _t556 = _t555(msg)
        fields35 = _t556
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
            opt_val44 = field43
            self.write(str(opt_val44))
            _t557 = None
        else:
            _t557 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_boolean_value(self, msg: bool) -> Optional[Never]:
        def _t558(_dollar_dollar):
            
            if _dollar_dollar:
                _t559 = ()
            else:
                _t559 = None
            return _t559
        _t560 = _t558(msg)
        deconstruct_result47 = _t560
        
        if deconstruct_result47 is not None:
            self.write('true')
            _t561 = None
        else:
            def _t562(_dollar_dollar):
                return _dollar_dollar
            _t563 = _t562(msg)
            fields45 = _t563
            unwrapped_fields46 = fields45
            self.write('false')
            _t561 = None
        return _t561

    def pretty_sync(self, msg: transactions_pb2.Sync) -> Optional[Never]:
        def _t564(_dollar_dollar):
            return _dollar_dollar.fragments
        _t565 = _t564(msg)
        fields48 = _t565
        unwrapped_fields49 = fields48
        self.write('(')
        self.write('sync')
        self.indent()
        if not len(unwrapped_fields49) == 0:
            self.newline()
            for i51, elem50 in enumerate(unwrapped_fields49):
                
                if (i51 > 0):
                    self.newline()
                    _t566 = None
                else:
                    _t566 = None
                _t567 = self.pretty_fragment_id(elem50)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[Never]:
        def _t568(_dollar_dollar):
            return self.fragment_id_to_string(_dollar_dollar)
        _t569 = _t568(msg)
        fields52 = _t569
        unwrapped_fields53 = fields52
        self.write(':')
        self.write(unwrapped_fields53)
        return None

    def pretty_epoch(self, msg: transactions_pb2.Epoch) -> Optional[Never]:
        def _t570(_dollar_dollar):
            
            if not len(_dollar_dollar.writes) == 0:
                _t571 = _dollar_dollar.writes
            else:
                _t571 = None
            
            if not len(_dollar_dollar.reads) == 0:
                _t572 = _dollar_dollar.reads
            else:
                _t572 = None
            return (_t571, _t572,)
        _t573 = _t570(msg)
        fields54 = _t573
        unwrapped_fields55 = fields54
        self.write('(')
        self.write('epoch')
        self.indent()
        field56 = unwrapped_fields55[0]
        
        if field56 is not None:
            self.newline()
            opt_val57 = field56
            _t575 = self.pretty_epoch_writes(opt_val57)
            _t574 = _t575
        else:
            _t574 = None
        field58 = unwrapped_fields55[1]
        
        if field58 is not None:
            self.newline()
            opt_val59 = field58
            _t577 = self.pretty_epoch_reads(opt_val59)
            _t576 = _t577
        else:
            _t576 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_writes(self, msg: list[transactions_pb2.Write]) -> Optional[Never]:
        def _t578(_dollar_dollar):
            return _dollar_dollar
        _t579 = _t578(msg)
        fields60 = _t579
        unwrapped_fields61 = fields60
        self.write('(')
        self.write('writes')
        self.indent()
        if not len(unwrapped_fields61) == 0:
            self.newline()
            for i63, elem62 in enumerate(unwrapped_fields61):
                
                if (i63 > 0):
                    self.newline()
                    _t580 = None
                else:
                    _t580 = None
                _t581 = self.pretty_write(elem62)
        self.dedent()
        self.write(')')
        return None

    def pretty_write(self, msg: transactions_pb2.Write) -> Optional[Never]:
        def _t582(_dollar_dollar):
            
            if _dollar_dollar.HasField('define'):
                _t583 = _dollar_dollar.define
            else:
                _t583 = None
            return _t583
        _t584 = _t582(msg)
        deconstruct_result66 = _t584
        
        if deconstruct_result66 is not None:
            _t586 = self.pretty_define(deconstruct_result66)
            _t585 = _t586
        else:
            def _t587(_dollar_dollar):
                
                if _dollar_dollar.HasField('undefine'):
                    _t588 = _dollar_dollar.undefine
                else:
                    _t588 = None
                return _t588
            _t589 = _t587(msg)
            deconstruct_result65 = _t589
            
            if deconstruct_result65 is not None:
                _t591 = self.pretty_undefine(deconstruct_result65)
                _t590 = _t591
            else:
                def _t592(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('context'):
                        _t593 = _dollar_dollar.context
                    else:
                        _t593 = None
                    return _t593
                _t594 = _t592(msg)
                deconstruct_result64 = _t594
                
                if deconstruct_result64 is not None:
                    _t596 = self.pretty_context(deconstruct_result64)
                    _t595 = _t596
                else:
                    raise ParseError('No matching rule for write')
                _t590 = _t595
            _t585 = _t590
        return _t585

    def pretty_define(self, msg: transactions_pb2.Define) -> Optional[Never]:
        def _t597(_dollar_dollar):
            return _dollar_dollar.fragment
        _t598 = _t597(msg)
        fields67 = _t598
        unwrapped_fields68 = fields67
        self.write('(')
        self.write('define')
        self.indent()
        self.newline()
        _t599 = self.pretty_fragment(unwrapped_fields68)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> Optional[Never]:
        def _t600(_dollar_dollar):
            _t601 = self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t602 = _t600(msg)
        fields69 = _t602
        unwrapped_fields70 = fields69
        self.write('(')
        self.write('fragment')
        self.indent()
        self.newline()
        field71 = unwrapped_fields70[0]
        _t603 = self.pretty_new_fragment_id(field71)
        field72 = unwrapped_fields70[1]
        if not len(field72) == 0:
            self.newline()
            for i74, elem73 in enumerate(field72):
                
                if (i74 > 0):
                    self.newline()
                    _t604 = None
                else:
                    _t604 = None
                _t605 = self.pretty_declaration(elem73)
        self.dedent()
        self.write(')')
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[Never]:
        def _t606(_dollar_dollar):
            return _dollar_dollar
        _t607 = _t606(msg)
        fields75 = _t607
        unwrapped_fields76 = fields75
        _t608 = self.pretty_fragment_id(unwrapped_fields76)
        return _t608

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> Optional[Never]:
        def _t609(_dollar_dollar):
            
            if _dollar_dollar.HasField('def'):
                _t610 = getattr(_dollar_dollar, 'def')
            else:
                _t610 = None
            return _t610
        _t611 = _t609(msg)
        deconstruct_result80 = _t611
        
        if deconstruct_result80 is not None:
            _t613 = self.pretty_def(deconstruct_result80)
            _t612 = _t613
        else:
            def _t614(_dollar_dollar):
                
                if _dollar_dollar.HasField('algorithm'):
                    _t615 = _dollar_dollar.algorithm
                else:
                    _t615 = None
                return _t615
            _t616 = _t614(msg)
            deconstruct_result79 = _t616
            
            if deconstruct_result79 is not None:
                _t618 = self.pretty_algorithm(deconstruct_result79)
                _t617 = _t618
            else:
                def _t619(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('constraint'):
                        _t620 = _dollar_dollar.constraint
                    else:
                        _t620 = None
                    return _t620
                _t621 = _t619(msg)
                deconstruct_result78 = _t621
                
                if deconstruct_result78 is not None:
                    _t623 = self.pretty_constraint(deconstruct_result78)
                    _t622 = _t623
                else:
                    def _t624(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('data'):
                            _t625 = _dollar_dollar.data
                        else:
                            _t625 = None
                        return _t625
                    _t626 = _t624(msg)
                    deconstruct_result77 = _t626
                    
                    if deconstruct_result77 is not None:
                        _t628 = self.pretty_data(deconstruct_result77)
                        _t627 = _t628
                    else:
                        raise ParseError('No matching rule for declaration')
                    _t622 = _t627
                _t617 = _t622
            _t612 = _t617
        return _t612

    def pretty_def(self, msg: logic_pb2.Def) -> Optional[Never]:
        def _t629(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t630 = _dollar_dollar.attrs
            else:
                _t630 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t630,)
        _t631 = _t629(msg)
        fields81 = _t631
        unwrapped_fields82 = fields81
        self.write('(')
        self.write('def')
        self.indent()
        self.newline()
        field83 = unwrapped_fields82[0]
        _t632 = self.pretty_relation_id(field83)
        self.newline()
        field84 = unwrapped_fields82[1]
        _t633 = self.pretty_abstraction(field84)
        field85 = unwrapped_fields82[2]
        
        if field85 is not None:
            self.newline()
            opt_val86 = field85
            _t635 = self.pretty_attrs(opt_val86)
            _t634 = _t635
        else:
            _t634 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> Optional[Never]:
        def _t636(_dollar_dollar):
            _t637 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t637
        _t638 = _t636(msg)
        deconstruct_result88 = _t638
        
        if deconstruct_result88 is not None:
            self.write(':')
            self.write(deconstruct_result88)
            _t639 = None
        else:
            def _t640(_dollar_dollar):
                _t641 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t641
            _t642 = _t640(msg)
            deconstruct_result87 = _t642
            
            if deconstruct_result87 is not None:
                self.write(self.format_uint128(deconstruct_result87))
                _t643 = None
            else:
                raise ParseError('No matching rule for relation_id')
            _t639 = _t643
        return _t639

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> Optional[Never]:
        def _t644(_dollar_dollar):
            _t645 = self.deconstruct_bindings(_dollar_dollar)
            return (_t645, _dollar_dollar.value,)
        _t646 = _t644(msg)
        fields89 = _t646
        unwrapped_fields90 = fields89
        self.write('(')
        field91 = unwrapped_fields90[0]
        _t647 = self.pretty_bindings(field91)
        self.write(' ')
        field92 = unwrapped_fields90[1]
        _t648 = self.pretty_formula(field92)
        self.write(')')
        return None

    def pretty_bindings(self, msg: tuple[list[logic_pb2.Binding], list[logic_pb2.Binding]]) -> Optional[Never]:
        def _t649(_dollar_dollar):
            
            if not len(_dollar_dollar[1]) == 0:
                _t650 = _dollar_dollar[1]
            else:
                _t650 = None
            return (_dollar_dollar[0], _t650,)
        _t651 = _t649(msg)
        fields93 = _t651
        unwrapped_fields94 = fields93
        self.write('[')
        field95 = unwrapped_fields94[0]
        for i97, elem96 in enumerate(field95):
            
            if (i97 > 0):
                self.newline()
                _t652 = None
            else:
                _t652 = None
            _t653 = self.pretty_binding(elem96)
        field98 = unwrapped_fields94[1]
        
        if field98 is not None:
            self.write(' ')
            opt_val99 = field98
            _t655 = self.pretty_value_bindings(opt_val99)
            _t654 = _t655
        else:
            _t654 = None
        self.write(']')
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> Optional[Never]:
        def _t656(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t657 = _t656(msg)
        fields100 = _t657
        unwrapped_fields101 = fields100
        field102 = unwrapped_fields101[0]
        self.write(field102)
        self.write('::')
        field103 = unwrapped_fields101[1]
        _t658 = self.pretty_type(field103)
        return _t658

    def pretty_type(self, msg: logic_pb2.Type) -> Optional[Never]:
        def _t659(_dollar_dollar):
            
            if _dollar_dollar.HasField('unspecified_type'):
                _t660 = _dollar_dollar.unspecified_type
            else:
                _t660 = None
            return _t660
        _t661 = _t659(msg)
        deconstruct_result114 = _t661
        
        if deconstruct_result114 is not None:
            _t663 = self.pretty_unspecified_type(deconstruct_result114)
            _t662 = _t663
        else:
            def _t664(_dollar_dollar):
                
                if _dollar_dollar.HasField('string_type'):
                    _t665 = _dollar_dollar.string_type
                else:
                    _t665 = None
                return _t665
            _t666 = _t664(msg)
            deconstruct_result113 = _t666
            
            if deconstruct_result113 is not None:
                _t668 = self.pretty_string_type(deconstruct_result113)
                _t667 = _t668
            else:
                def _t669(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('int_type'):
                        _t670 = _dollar_dollar.int_type
                    else:
                        _t670 = None
                    return _t670
                _t671 = _t669(msg)
                deconstruct_result112 = _t671
                
                if deconstruct_result112 is not None:
                    _t673 = self.pretty_int_type(deconstruct_result112)
                    _t672 = _t673
                else:
                    def _t674(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('float_type'):
                            _t675 = _dollar_dollar.float_type
                        else:
                            _t675 = None
                        return _t675
                    _t676 = _t674(msg)
                    deconstruct_result111 = _t676
                    
                    if deconstruct_result111 is not None:
                        _t678 = self.pretty_float_type(deconstruct_result111)
                        _t677 = _t678
                    else:
                        def _t679(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('uint128_type'):
                                _t680 = _dollar_dollar.uint128_type
                            else:
                                _t680 = None
                            return _t680
                        _t681 = _t679(msg)
                        deconstruct_result110 = _t681
                        
                        if deconstruct_result110 is not None:
                            _t683 = self.pretty_uint128_type(deconstruct_result110)
                            _t682 = _t683
                        else:
                            def _t684(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('int128_type'):
                                    _t685 = _dollar_dollar.int128_type
                                else:
                                    _t685 = None
                                return _t685
                            _t686 = _t684(msg)
                            deconstruct_result109 = _t686
                            
                            if deconstruct_result109 is not None:
                                _t688 = self.pretty_int128_type(deconstruct_result109)
                                _t687 = _t688
                            else:
                                def _t689(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('date_type'):
                                        _t690 = _dollar_dollar.date_type
                                    else:
                                        _t690 = None
                                    return _t690
                                _t691 = _t689(msg)
                                deconstruct_result108 = _t691
                                
                                if deconstruct_result108 is not None:
                                    _t693 = self.pretty_date_type(deconstruct_result108)
                                    _t692 = _t693
                                else:
                                    def _t694(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('datetime_type'):
                                            _t695 = _dollar_dollar.datetime_type
                                        else:
                                            _t695 = None
                                        return _t695
                                    _t696 = _t694(msg)
                                    deconstruct_result107 = _t696
                                    
                                    if deconstruct_result107 is not None:
                                        _t698 = self.pretty_datetime_type(deconstruct_result107)
                                        _t697 = _t698
                                    else:
                                        def _t699(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('missing_type'):
                                                _t700 = _dollar_dollar.missing_type
                                            else:
                                                _t700 = None
                                            return _t700
                                        _t701 = _t699(msg)
                                        deconstruct_result106 = _t701
                                        
                                        if deconstruct_result106 is not None:
                                            _t703 = self.pretty_missing_type(deconstruct_result106)
                                            _t702 = _t703
                                        else:
                                            def _t704(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('decimal_type'):
                                                    _t705 = _dollar_dollar.decimal_type
                                                else:
                                                    _t705 = None
                                                return _t705
                                            _t706 = _t704(msg)
                                            deconstruct_result105 = _t706
                                            
                                            if deconstruct_result105 is not None:
                                                _t708 = self.pretty_decimal_type(deconstruct_result105)
                                                _t707 = _t708
                                            else:
                                                def _t709(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('boolean_type'):
                                                        _t710 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t710 = None
                                                    return _t710
                                                _t711 = _t709(msg)
                                                deconstruct_result104 = _t711
                                                
                                                if deconstruct_result104 is not None:
                                                    _t713 = self.pretty_boolean_type(deconstruct_result104)
                                                    _t712 = _t713
                                                else:
                                                    raise ParseError('No matching rule for type')
                                                _t707 = _t712
                                            _t702 = _t707
                                        _t697 = _t702
                                    _t692 = _t697
                                _t687 = _t692
                            _t682 = _t687
                        _t677 = _t682
                    _t672 = _t677
                _t667 = _t672
            _t662 = _t667
        return _t662

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> Optional[Never]:
        def _t714(_dollar_dollar):
            return _dollar_dollar
        _t715 = _t714(msg)
        fields115 = _t715
        unwrapped_fields116 = fields115
        self.write('UNKNOWN')
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> Optional[Never]:
        def _t716(_dollar_dollar):
            return _dollar_dollar
        _t717 = _t716(msg)
        fields117 = _t717
        unwrapped_fields118 = fields117
        self.write('STRING')
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> Optional[Never]:
        def _t718(_dollar_dollar):
            return _dollar_dollar
        _t719 = _t718(msg)
        fields119 = _t719
        unwrapped_fields120 = fields119
        self.write('INT')
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> Optional[Never]:
        def _t720(_dollar_dollar):
            return _dollar_dollar
        _t721 = _t720(msg)
        fields121 = _t721
        unwrapped_fields122 = fields121
        self.write('FLOAT')
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> Optional[Never]:
        def _t722(_dollar_dollar):
            return _dollar_dollar
        _t723 = _t722(msg)
        fields123 = _t723
        unwrapped_fields124 = fields123
        self.write('UINT128')
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> Optional[Never]:
        def _t724(_dollar_dollar):
            return _dollar_dollar
        _t725 = _t724(msg)
        fields125 = _t725
        unwrapped_fields126 = fields125
        self.write('INT128')
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> Optional[Never]:
        def _t726(_dollar_dollar):
            return _dollar_dollar
        _t727 = _t726(msg)
        fields127 = _t727
        unwrapped_fields128 = fields127
        self.write('DATE')
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> Optional[Never]:
        def _t728(_dollar_dollar):
            return _dollar_dollar
        _t729 = _t728(msg)
        fields129 = _t729
        unwrapped_fields130 = fields129
        self.write('DATETIME')
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> Optional[Never]:
        def _t730(_dollar_dollar):
            return _dollar_dollar
        _t731 = _t730(msg)
        fields131 = _t731
        unwrapped_fields132 = fields131
        self.write('MISSING')
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> Optional[Never]:
        def _t732(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t733 = _t732(msg)
        fields133 = _t733
        unwrapped_fields134 = fields133
        self.write('(')
        self.write('DECIMAL')
        self.indent()
        self.newline()
        field135 = unwrapped_fields134[0]
        self.write(str(field135))
        self.newline()
        field136 = unwrapped_fields134[1]
        self.write(str(field136))
        self.dedent()
        self.write(')')
        return None

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType) -> Optional[Never]:
        def _t734(_dollar_dollar):
            return _dollar_dollar
        _t735 = _t734(msg)
        fields137 = _t735
        unwrapped_fields138 = fields137
        self.write('BOOLEAN')
        return None

    def pretty_value_bindings(self, msg: list[logic_pb2.Binding]) -> Optional[Never]:
        def _t736(_dollar_dollar):
            return _dollar_dollar
        _t737 = _t736(msg)
        fields139 = _t737
        unwrapped_fields140 = fields139
        self.write('|')
        if not len(unwrapped_fields140) == 0:
            self.write(' ')
            for i142, elem141 in enumerate(unwrapped_fields140):
                
                if (i142 > 0):
                    self.newline()
                    _t738 = None
                else:
                    _t738 = None
                _t739 = self.pretty_binding(elem141)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> Optional[Never]:
        def _t740(_dollar_dollar):
            
            if (_dollar_dollar.HasField('conjunction') and len(_dollar_dollar.conjunction.args) == 0):
                _t741 = _dollar_dollar.conjunction
            else:
                _t741 = None
            return _t741
        _t742 = _t740(msg)
        deconstruct_result155 = _t742
        
        if deconstruct_result155 is not None:
            _t744 = self.pretty_true(deconstruct_result155)
            _t743 = _t744
        else:
            def _t745(_dollar_dollar):
                
                if (_dollar_dollar.HasField('disjunction') and len(_dollar_dollar.disjunction.args) == 0):
                    _t746 = _dollar_dollar.disjunction
                else:
                    _t746 = None
                return _t746
            _t747 = _t745(msg)
            deconstruct_result154 = _t747
            
            if deconstruct_result154 is not None:
                _t749 = self.pretty_false(deconstruct_result154)
                _t748 = _t749
            else:
                def _t750(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('exists'):
                        _t751 = _dollar_dollar.exists
                    else:
                        _t751 = None
                    return _t751
                _t752 = _t750(msg)
                deconstruct_result153 = _t752
                
                if deconstruct_result153 is not None:
                    _t754 = self.pretty_exists(deconstruct_result153)
                    _t753 = _t754
                else:
                    def _t755(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('reduce'):
                            _t756 = _dollar_dollar.reduce
                        else:
                            _t756 = None
                        return _t756
                    _t757 = _t755(msg)
                    deconstruct_result152 = _t757
                    
                    if deconstruct_result152 is not None:
                        _t759 = self.pretty_reduce(deconstruct_result152)
                        _t758 = _t759
                    else:
                        def _t760(_dollar_dollar):
                            
                            if (_dollar_dollar.HasField('conjunction') and not len(_dollar_dollar.conjunction.args) == 0):
                                _t761 = _dollar_dollar.conjunction
                            else:
                                _t761 = None
                            return _t761
                        _t762 = _t760(msg)
                        deconstruct_result151 = _t762
                        
                        if deconstruct_result151 is not None:
                            _t764 = self.pretty_conjunction(deconstruct_result151)
                            _t763 = _t764
                        else:
                            def _t765(_dollar_dollar):
                                
                                if (_dollar_dollar.HasField('disjunction') and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t766 = _dollar_dollar.disjunction
                                else:
                                    _t766 = None
                                return _t766
                            _t767 = _t765(msg)
                            deconstruct_result150 = _t767
                            
                            if deconstruct_result150 is not None:
                                _t769 = self.pretty_disjunction(deconstruct_result150)
                                _t768 = _t769
                            else:
                                def _t770(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('not'):
                                        _t771 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t771 = None
                                    return _t771
                                _t772 = _t770(msg)
                                deconstruct_result149 = _t772
                                
                                if deconstruct_result149 is not None:
                                    _t774 = self.pretty_not(deconstruct_result149)
                                    _t773 = _t774
                                else:
                                    def _t775(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('ffi'):
                                            _t776 = _dollar_dollar.ffi
                                        else:
                                            _t776 = None
                                        return _t776
                                    _t777 = _t775(msg)
                                    deconstruct_result148 = _t777
                                    
                                    if deconstruct_result148 is not None:
                                        _t779 = self.pretty_ffi(deconstruct_result148)
                                        _t778 = _t779
                                    else:
                                        def _t780(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('atom'):
                                                _t781 = _dollar_dollar.atom
                                            else:
                                                _t781 = None
                                            return _t781
                                        _t782 = _t780(msg)
                                        deconstruct_result147 = _t782
                                        
                                        if deconstruct_result147 is not None:
                                            _t784 = self.pretty_atom(deconstruct_result147)
                                            _t783 = _t784
                                        else:
                                            def _t785(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('pragma'):
                                                    _t786 = _dollar_dollar.pragma
                                                else:
                                                    _t786 = None
                                                return _t786
                                            _t787 = _t785(msg)
                                            deconstruct_result146 = _t787
                                            
                                            if deconstruct_result146 is not None:
                                                _t789 = self.pretty_pragma(deconstruct_result146)
                                                _t788 = _t789
                                            else:
                                                def _t790(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('primitive'):
                                                        _t791 = _dollar_dollar.primitive
                                                    else:
                                                        _t791 = None
                                                    return _t791
                                                _t792 = _t790(msg)
                                                deconstruct_result145 = _t792
                                                
                                                if deconstruct_result145 is not None:
                                                    _t794 = self.pretty_primitive(deconstruct_result145)
                                                    _t793 = _t794
                                                else:
                                                    def _t795(_dollar_dollar):
                                                        
                                                        if _dollar_dollar.HasField('rel_atom'):
                                                            _t796 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t796 = None
                                                        return _t796
                                                    _t797 = _t795(msg)
                                                    deconstruct_result144 = _t797
                                                    
                                                    if deconstruct_result144 is not None:
                                                        _t799 = self.pretty_rel_atom(deconstruct_result144)
                                                        _t798 = _t799
                                                    else:
                                                        def _t800(_dollar_dollar):
                                                            
                                                            if _dollar_dollar.HasField('cast'):
                                                                _t801 = _dollar_dollar.cast
                                                            else:
                                                                _t801 = None
                                                            return _t801
                                                        _t802 = _t800(msg)
                                                        deconstruct_result143 = _t802
                                                        
                                                        if deconstruct_result143 is not None:
                                                            _t804 = self.pretty_cast(deconstruct_result143)
                                                            _t803 = _t804
                                                        else:
                                                            raise ParseError('No matching rule for formula')
                                                        _t798 = _t803
                                                    _t793 = _t798
                                                _t788 = _t793
                                            _t783 = _t788
                                        _t778 = _t783
                                    _t773 = _t778
                                _t768 = _t773
                            _t763 = _t768
                        _t758 = _t763
                    _t753 = _t758
                _t748 = _t753
            _t743 = _t748
        return _t743

    def pretty_true(self, msg: logic_pb2.Conjunction) -> Optional[Never]:
        def _t805(_dollar_dollar):
            return _dollar_dollar
        _t806 = _t805(msg)
        fields156 = _t806
        unwrapped_fields157 = fields156
        self.write('(')
        self.write('true')
        self.write(')')
        return None

    def pretty_false(self, msg: logic_pb2.Disjunction) -> Optional[Never]:
        def _t807(_dollar_dollar):
            return _dollar_dollar
        _t808 = _t807(msg)
        fields158 = _t808
        unwrapped_fields159 = fields158
        self.write('(')
        self.write('false')
        self.write(')')
        return None

    def pretty_exists(self, msg: logic_pb2.Exists) -> Optional[Never]:
        def _t809(_dollar_dollar):
            _t810 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t810, _dollar_dollar.body.value,)
        _t811 = _t809(msg)
        fields160 = _t811
        unwrapped_fields161 = fields160
        self.write('(')
        self.write('exists')
        self.indent()
        self.newline()
        field162 = unwrapped_fields161[0]
        _t812 = self.pretty_bindings(field162)
        self.newline()
        field163 = unwrapped_fields161[1]
        _t813 = self.pretty_formula(field163)
        self.dedent()
        self.write(')')
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> Optional[Never]:
        def _t814(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t815 = _t814(msg)
        fields164 = _t815
        unwrapped_fields165 = fields164
        self.write('(')
        self.write('reduce')
        self.indent()
        self.newline()
        field166 = unwrapped_fields165[0]
        _t816 = self.pretty_abstraction(field166)
        self.newline()
        field167 = unwrapped_fields165[1]
        _t817 = self.pretty_abstraction(field167)
        self.newline()
        field168 = unwrapped_fields165[2]
        _t818 = self.pretty_terms(field168)
        self.dedent()
        self.write(')')
        return None

    def pretty_terms(self, msg: list[logic_pb2.Term]) -> Optional[Never]:
        def _t819(_dollar_dollar):
            return _dollar_dollar
        _t820 = _t819(msg)
        fields169 = _t820
        unwrapped_fields170 = fields169
        self.write('(')
        self.write('terms')
        self.indent()
        if not len(unwrapped_fields170) == 0:
            self.newline()
            for i172, elem171 in enumerate(unwrapped_fields170):
                
                if (i172 > 0):
                    self.newline()
                    _t821 = None
                else:
                    _t821 = None
                _t822 = self.pretty_term(elem171)
        self.dedent()
        self.write(')')
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> Optional[Never]:
        def _t823(_dollar_dollar):
            
            if _dollar_dollar.HasField('var'):
                _t824 = _dollar_dollar.var
            else:
                _t824 = None
            return _t824
        _t825 = _t823(msg)
        deconstruct_result174 = _t825
        
        if deconstruct_result174 is not None:
            _t827 = self.pretty_var(deconstruct_result174)
            _t826 = _t827
        else:
            def _t828(_dollar_dollar):
                
                if _dollar_dollar.HasField('constant'):
                    _t829 = _dollar_dollar.constant
                else:
                    _t829 = None
                return _t829
            _t830 = _t828(msg)
            deconstruct_result173 = _t830
            
            if deconstruct_result173 is not None:
                _t832 = self.pretty_constant(deconstruct_result173)
                _t831 = _t832
            else:
                raise ParseError('No matching rule for term')
            _t826 = _t831
        return _t826

    def pretty_var(self, msg: logic_pb2.Var) -> Optional[Never]:
        def _t833(_dollar_dollar):
            return _dollar_dollar.name
        _t834 = _t833(msg)
        fields175 = _t834
        unwrapped_fields176 = fields175
        self.write(unwrapped_fields176)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t835(_dollar_dollar):
            return _dollar_dollar
        _t836 = _t835(msg)
        fields177 = _t836
        unwrapped_fields178 = fields177
        _t837 = self.pretty_value(unwrapped_fields178)
        return _t837

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> Optional[Never]:
        def _t838(_dollar_dollar):
            return _dollar_dollar.args
        _t839 = _t838(msg)
        fields179 = _t839
        unwrapped_fields180 = fields179
        self.write('(')
        self.write('and')
        self.indent()
        if not len(unwrapped_fields180) == 0:
            self.newline()
            for i182, elem181 in enumerate(unwrapped_fields180):
                
                if (i182 > 0):
                    self.newline()
                    _t840 = None
                else:
                    _t840 = None
                _t841 = self.pretty_formula(elem181)
        self.dedent()
        self.write(')')
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> Optional[Never]:
        def _t842(_dollar_dollar):
            return _dollar_dollar.args
        _t843 = _t842(msg)
        fields183 = _t843
        unwrapped_fields184 = fields183
        self.write('(')
        self.write('or')
        self.indent()
        if not len(unwrapped_fields184) == 0:
            self.newline()
            for i186, elem185 in enumerate(unwrapped_fields184):
                
                if (i186 > 0):
                    self.newline()
                    _t844 = None
                else:
                    _t844 = None
                _t845 = self.pretty_formula(elem185)
        self.dedent()
        self.write(')')
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> Optional[Never]:
        def _t846(_dollar_dollar):
            return _dollar_dollar.arg
        _t847 = _t846(msg)
        fields187 = _t847
        unwrapped_fields188 = fields187
        self.write('(')
        self.write('not')
        self.indent()
        self.newline()
        _t848 = self.pretty_formula(unwrapped_fields188)
        self.dedent()
        self.write(')')
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> Optional[Never]:
        def _t849(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t850 = _t849(msg)
        fields189 = _t850
        unwrapped_fields190 = fields189
        self.write('(')
        self.write('ffi')
        self.indent()
        self.newline()
        field191 = unwrapped_fields190[0]
        _t851 = self.pretty_name(field191)
        self.newline()
        field192 = unwrapped_fields190[1]
        _t852 = self.pretty_ffi_args(field192)
        self.newline()
        field193 = unwrapped_fields190[2]
        _t853 = self.pretty_terms(field193)
        self.dedent()
        self.write(')')
        return None

    def pretty_name(self, msg: str) -> Optional[Never]:
        def _t854(_dollar_dollar):
            return _dollar_dollar
        _t855 = _t854(msg)
        fields194 = _t855
        unwrapped_fields195 = fields194
        self.write(':')
        self.write(unwrapped_fields195)
        return None

    def pretty_ffi_args(self, msg: list[logic_pb2.Abstraction]) -> Optional[Never]:
        def _t856(_dollar_dollar):
            return _dollar_dollar
        _t857 = _t856(msg)
        fields196 = _t857
        unwrapped_fields197 = fields196
        self.write('(')
        self.write('args')
        self.indent()
        if not len(unwrapped_fields197) == 0:
            self.newline()
            for i199, elem198 in enumerate(unwrapped_fields197):
                
                if (i199 > 0):
                    self.newline()
                    _t858 = None
                else:
                    _t858 = None
                _t859 = self.pretty_abstraction(elem198)
        self.dedent()
        self.write(')')
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> Optional[Never]:
        def _t860(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t861 = _t860(msg)
        fields200 = _t861
        unwrapped_fields201 = fields200
        self.write('(')
        self.write('atom')
        self.indent()
        self.newline()
        field202 = unwrapped_fields201[0]
        _t862 = self.pretty_relation_id(field202)
        field203 = unwrapped_fields201[1]
        if not len(field203) == 0:
            self.newline()
            for i205, elem204 in enumerate(field203):
                
                if (i205 > 0):
                    self.newline()
                    _t863 = None
                else:
                    _t863 = None
                _t864 = self.pretty_term(elem204)
        self.dedent()
        self.write(')')
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> Optional[Never]:
        def _t865(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t866 = _t865(msg)
        fields206 = _t866
        unwrapped_fields207 = fields206
        self.write('(')
        self.write('pragma')
        self.indent()
        self.newline()
        field208 = unwrapped_fields207[0]
        _t867 = self.pretty_name(field208)
        field209 = unwrapped_fields207[1]
        if not len(field209) == 0:
            self.newline()
            for i211, elem210 in enumerate(field209):
                
                if (i211 > 0):
                    self.newline()
                    _t868 = None
                else:
                    _t868 = None
                _t869 = self.pretty_term(elem210)
        self.dedent()
        self.write(')')
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t870(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t871 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t871 = None
            return _t871
        _t872 = _t870(msg)
        guard_result226 = _t872
        
        if guard_result226 is not None:
            _t874 = self.pretty_eq(msg)
            _t873 = _t874
        else:
            def _t875(_dollar_dollar):
                
                if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                    _t876 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t876 = None
                return _t876
            _t877 = _t875(msg)
            guard_result225 = _t877
            
            if guard_result225 is not None:
                _t879 = self.pretty_lt(msg)
                _t878 = _t879
            else:
                def _t880(_dollar_dollar):
                    
                    if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                        _t881 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t881 = None
                    return _t881
                _t882 = _t880(msg)
                guard_result224 = _t882
                
                if guard_result224 is not None:
                    _t884 = self.pretty_lt_eq(msg)
                    _t883 = _t884
                else:
                    def _t885(_dollar_dollar):
                        
                        if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                            _t886 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t886 = None
                        return _t886
                    _t887 = _t885(msg)
                    guard_result223 = _t887
                    
                    if guard_result223 is not None:
                        _t889 = self.pretty_gt(msg)
                        _t888 = _t889
                    else:
                        def _t890(_dollar_dollar):
                            
                            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                                _t891 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t891 = None
                            return _t891
                        _t892 = _t890(msg)
                        guard_result222 = _t892
                        
                        if guard_result222 is not None:
                            _t894 = self.pretty_gt_eq(msg)
                            _t893 = _t894
                        else:
                            def _t895(_dollar_dollar):
                                
                                if _dollar_dollar.name == 'rel_primitive_add_monotype':
                                    _t896 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t896 = None
                                return _t896
                            _t897 = _t895(msg)
                            guard_result221 = _t897
                            
                            if guard_result221 is not None:
                                _t899 = self.pretty_add(msg)
                                _t898 = _t899
                            else:
                                def _t900(_dollar_dollar):
                                    
                                    if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                                        _t901 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t901 = None
                                    return _t901
                                _t902 = _t900(msg)
                                guard_result220 = _t902
                                
                                if guard_result220 is not None:
                                    _t904 = self.pretty_minus(msg)
                                    _t903 = _t904
                                else:
                                    def _t905(_dollar_dollar):
                                        
                                        if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                                            _t906 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t906 = None
                                        return _t906
                                    _t907 = _t905(msg)
                                    guard_result219 = _t907
                                    
                                    if guard_result219 is not None:
                                        _t909 = self.pretty_multiply(msg)
                                        _t908 = _t909
                                    else:
                                        def _t910(_dollar_dollar):
                                            
                                            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                                                _t911 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t911 = None
                                            return _t911
                                        _t912 = _t910(msg)
                                        guard_result218 = _t912
                                        
                                        if guard_result218 is not None:
                                            _t914 = self.pretty_divide(msg)
                                            _t913 = _t914
                                        else:
                                            def _t915(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t916 = _t915(msg)
                                            fields212 = _t916
                                            unwrapped_fields213 = fields212
                                            self.write('(')
                                            self.write('primitive')
                                            self.indent()
                                            self.newline()
                                            field214 = unwrapped_fields213[0]
                                            _t917 = self.pretty_name(field214)
                                            field215 = unwrapped_fields213[1]
                                            if not len(field215) == 0:
                                                self.newline()
                                                for i217, elem216 in enumerate(field215):
                                                    
                                                    if (i217 > 0):
                                                        self.newline()
                                                        _t918 = None
                                                    else:
                                                        _t918 = None
                                                    _t919 = self.pretty_rel_term(elem216)
                                            self.dedent()
                                            self.write(')')
                                            _t913 = None
                                        _t908 = _t913
                                    _t903 = _t908
                                _t898 = _t903
                            _t893 = _t898
                        _t888 = _t893
                    _t883 = _t888
                _t878 = _t883
            _t873 = _t878
        return _t873

    def pretty_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t920(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t921 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t921 = None
            return _t921
        _t922 = _t920(msg)
        fields227 = _t922
        unwrapped_fields228 = fields227
        self.write('(')
        self.write('=')
        self.indent()
        self.newline()
        field229 = unwrapped_fields228[0]
        _t923 = self.pretty_term(field229)
        self.newline()
        field230 = unwrapped_fields228[1]
        _t924 = self.pretty_term(field230)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t925(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                _t926 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t926 = None
            return _t926
        _t927 = _t925(msg)
        fields231 = _t927
        unwrapped_fields232 = fields231
        self.write('(')
        self.write('<')
        self.indent()
        self.newline()
        field233 = unwrapped_fields232[0]
        _t928 = self.pretty_term(field233)
        self.newline()
        field234 = unwrapped_fields232[1]
        _t929 = self.pretty_term(field234)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t930(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                _t931 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t931 = None
            return _t931
        _t932 = _t930(msg)
        fields235 = _t932
        unwrapped_fields236 = fields235
        self.write('(')
        self.write('<=')
        self.indent()
        self.newline()
        field237 = unwrapped_fields236[0]
        _t933 = self.pretty_term(field237)
        self.newline()
        field238 = unwrapped_fields236[1]
        _t934 = self.pretty_term(field238)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t935(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                _t936 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t936 = None
            return _t936
        _t937 = _t935(msg)
        fields239 = _t937
        unwrapped_fields240 = fields239
        self.write('(')
        self.write('>')
        self.indent()
        self.newline()
        field241 = unwrapped_fields240[0]
        _t938 = self.pretty_term(field241)
        self.newline()
        field242 = unwrapped_fields240[1]
        _t939 = self.pretty_term(field242)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t940(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                _t941 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t941 = None
            return _t941
        _t942 = _t940(msg)
        fields243 = _t942
        unwrapped_fields244 = fields243
        self.write('(')
        self.write('>=')
        self.indent()
        self.newline()
        field245 = unwrapped_fields244[0]
        _t943 = self.pretty_term(field245)
        self.newline()
        field246 = unwrapped_fields244[1]
        _t944 = self.pretty_term(field246)
        self.dedent()
        self.write(')')
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t945(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_add_monotype':
                _t946 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t946 = None
            return _t946
        _t947 = _t945(msg)
        fields247 = _t947
        unwrapped_fields248 = fields247
        self.write('(')
        self.write('+')
        self.indent()
        self.newline()
        field249 = unwrapped_fields248[0]
        _t948 = self.pretty_term(field249)
        self.newline()
        field250 = unwrapped_fields248[1]
        _t949 = self.pretty_term(field250)
        self.newline()
        field251 = unwrapped_fields248[2]
        _t950 = self.pretty_term(field251)
        self.dedent()
        self.write(')')
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t951(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                _t952 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t952 = None
            return _t952
        _t953 = _t951(msg)
        fields252 = _t953
        unwrapped_fields253 = fields252
        self.write('(')
        self.write('-')
        self.indent()
        self.newline()
        field254 = unwrapped_fields253[0]
        _t954 = self.pretty_term(field254)
        self.newline()
        field255 = unwrapped_fields253[1]
        _t955 = self.pretty_term(field255)
        self.newline()
        field256 = unwrapped_fields253[2]
        _t956 = self.pretty_term(field256)
        self.dedent()
        self.write(')')
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t957(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                _t958 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t958 = None
            return _t958
        _t959 = _t957(msg)
        fields257 = _t959
        unwrapped_fields258 = fields257
        self.write('(')
        self.write('*')
        self.indent()
        self.newline()
        field259 = unwrapped_fields258[0]
        _t960 = self.pretty_term(field259)
        self.newline()
        field260 = unwrapped_fields258[1]
        _t961 = self.pretty_term(field260)
        self.newline()
        field261 = unwrapped_fields258[2]
        _t962 = self.pretty_term(field261)
        self.dedent()
        self.write(')')
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> Optional[Never]:
        def _t963(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                _t964 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t964 = None
            return _t964
        _t965 = _t963(msg)
        fields262 = _t965
        unwrapped_fields263 = fields262
        self.write('(')
        self.write('/')
        self.indent()
        self.newline()
        field264 = unwrapped_fields263[0]
        _t966 = self.pretty_term(field264)
        self.newline()
        field265 = unwrapped_fields263[1]
        _t967 = self.pretty_term(field265)
        self.newline()
        field266 = unwrapped_fields263[2]
        _t968 = self.pretty_term(field266)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> Optional[Never]:
        def _t969(_dollar_dollar):
            
            if _dollar_dollar.HasField('specialized_value'):
                _t970 = _dollar_dollar.specialized_value
            else:
                _t970 = None
            return _t970
        _t971 = _t969(msg)
        deconstruct_result268 = _t971
        
        if deconstruct_result268 is not None:
            _t973 = self.pretty_specialized_value(deconstruct_result268)
            _t972 = _t973
        else:
            def _t974(_dollar_dollar):
                
                if _dollar_dollar.HasField('term'):
                    _t975 = _dollar_dollar.term
                else:
                    _t975 = None
                return _t975
            _t976 = _t974(msg)
            deconstruct_result267 = _t976
            
            if deconstruct_result267 is not None:
                _t978 = self.pretty_term(deconstruct_result267)
                _t977 = _t978
            else:
                raise ParseError('No matching rule for rel_term')
            _t972 = _t977
        return _t972

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> Optional[Never]:
        def _t979(_dollar_dollar):
            return _dollar_dollar
        _t980 = _t979(msg)
        fields269 = _t980
        unwrapped_fields270 = fields269
        self.write('#')
        _t981 = self.pretty_value(unwrapped_fields270)
        return _t981

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> Optional[Never]:
        def _t982(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t983 = _t982(msg)
        fields271 = _t983
        unwrapped_fields272 = fields271
        self.write('(')
        self.write('relatom')
        self.indent()
        self.newline()
        field273 = unwrapped_fields272[0]
        _t984 = self.pretty_name(field273)
        field274 = unwrapped_fields272[1]
        if not len(field274) == 0:
            self.newline()
            for i276, elem275 in enumerate(field274):
                
                if (i276 > 0):
                    self.newline()
                    _t985 = None
                else:
                    _t985 = None
                _t986 = self.pretty_rel_term(elem275)
        self.dedent()
        self.write(')')
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> Optional[Never]:
        def _t987(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t988 = _t987(msg)
        fields277 = _t988
        unwrapped_fields278 = fields277
        self.write('(')
        self.write('cast')
        self.indent()
        self.newline()
        field279 = unwrapped_fields278[0]
        _t989 = self.pretty_term(field279)
        self.newline()
        field280 = unwrapped_fields278[1]
        _t990 = self.pretty_term(field280)
        self.dedent()
        self.write(')')
        return None

    def pretty_attrs(self, msg: list[logic_pb2.Attribute]) -> Optional[Never]:
        def _t991(_dollar_dollar):
            return _dollar_dollar
        _t992 = _t991(msg)
        fields281 = _t992
        unwrapped_fields282 = fields281
        self.write('(')
        self.write('attrs')
        self.indent()
        if not len(unwrapped_fields282) == 0:
            self.newline()
            for i284, elem283 in enumerate(unwrapped_fields282):
                
                if (i284 > 0):
                    self.newline()
                    _t993 = None
                else:
                    _t993 = None
                _t994 = self.pretty_attribute(elem283)
        self.dedent()
        self.write(')')
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> Optional[Never]:
        def _t995(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t996 = _t995(msg)
        fields285 = _t996
        unwrapped_fields286 = fields285
        self.write('(')
        self.write('attribute')
        self.indent()
        self.newline()
        field287 = unwrapped_fields286[0]
        _t997 = self.pretty_name(field287)
        field288 = unwrapped_fields286[1]
        if not len(field288) == 0:
            self.newline()
            for i290, elem289 in enumerate(field288):
                
                if (i290 > 0):
                    self.newline()
                    _t998 = None
                else:
                    _t998 = None
                _t999 = self.pretty_value(elem289)
        self.dedent()
        self.write(')')
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> Optional[Never]:
        def _t1000(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t1001 = _t1000(msg)
        fields291 = _t1001
        unwrapped_fields292 = fields291
        self.write('(')
        self.write('algorithm')
        self.indent()
        field293 = unwrapped_fields292[0]
        if not len(field293) == 0:
            self.newline()
            for i295, elem294 in enumerate(field293):
                
                if (i295 > 0):
                    self.newline()
                    _t1002 = None
                else:
                    _t1002 = None
                _t1003 = self.pretty_relation_id(elem294)
        self.newline()
        field296 = unwrapped_fields292[1]
        _t1004 = self.pretty_script(field296)
        self.dedent()
        self.write(')')
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> Optional[Never]:
        def _t1005(_dollar_dollar):
            return _dollar_dollar.constructs
        _t1006 = _t1005(msg)
        fields297 = _t1006
        unwrapped_fields298 = fields297
        self.write('(')
        self.write('script')
        self.indent()
        if not len(unwrapped_fields298) == 0:
            self.newline()
            for i300, elem299 in enumerate(unwrapped_fields298):
                
                if (i300 > 0):
                    self.newline()
                    _t1007 = None
                else:
                    _t1007 = None
                _t1008 = self.pretty_construct(elem299)
        self.dedent()
        self.write(')')
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> Optional[Never]:
        def _t1009(_dollar_dollar):
            
            if _dollar_dollar.HasField('loop'):
                _t1010 = _dollar_dollar.loop
            else:
                _t1010 = None
            return _t1010
        _t1011 = _t1009(msg)
        deconstruct_result302 = _t1011
        
        if deconstruct_result302 is not None:
            _t1013 = self.pretty_loop(deconstruct_result302)
            _t1012 = _t1013
        else:
            def _t1014(_dollar_dollar):
                
                if _dollar_dollar.HasField('instruction'):
                    _t1015 = _dollar_dollar.instruction
                else:
                    _t1015 = None
                return _t1015
            _t1016 = _t1014(msg)
            deconstruct_result301 = _t1016
            
            if deconstruct_result301 is not None:
                _t1018 = self.pretty_instruction(deconstruct_result301)
                _t1017 = _t1018
            else:
                raise ParseError('No matching rule for construct')
            _t1012 = _t1017
        return _t1012

    def pretty_loop(self, msg: logic_pb2.Loop) -> Optional[Never]:
        def _t1019(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t1020 = _t1019(msg)
        fields303 = _t1020
        unwrapped_fields304 = fields303
        self.write('(')
        self.write('loop')
        self.indent()
        self.newline()
        field305 = unwrapped_fields304[0]
        _t1021 = self.pretty_init(field305)
        self.newline()
        field306 = unwrapped_fields304[1]
        _t1022 = self.pretty_script(field306)
        self.dedent()
        self.write(')')
        return None

    def pretty_init(self, msg: list[logic_pb2.Instruction]) -> Optional[Never]:
        def _t1023(_dollar_dollar):
            return _dollar_dollar
        _t1024 = _t1023(msg)
        fields307 = _t1024
        unwrapped_fields308 = fields307
        self.write('(')
        self.write('init')
        self.indent()
        if not len(unwrapped_fields308) == 0:
            self.newline()
            for i310, elem309 in enumerate(unwrapped_fields308):
                
                if (i310 > 0):
                    self.newline()
                    _t1025 = None
                else:
                    _t1025 = None
                _t1026 = self.pretty_instruction(elem309)
        self.dedent()
        self.write(')')
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> Optional[Never]:
        def _t1027(_dollar_dollar):
            
            if _dollar_dollar.HasField('assign'):
                _t1028 = _dollar_dollar.assign
            else:
                _t1028 = None
            return _t1028
        _t1029 = _t1027(msg)
        deconstruct_result315 = _t1029
        
        if deconstruct_result315 is not None:
            _t1031 = self.pretty_assign(deconstruct_result315)
            _t1030 = _t1031
        else:
            def _t1032(_dollar_dollar):
                
                if _dollar_dollar.HasField('upsert'):
                    _t1033 = _dollar_dollar.upsert
                else:
                    _t1033 = None
                return _t1033
            _t1034 = _t1032(msg)
            deconstruct_result314 = _t1034
            
            if deconstruct_result314 is not None:
                _t1036 = self.pretty_upsert(deconstruct_result314)
                _t1035 = _t1036
            else:
                def _t1037(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('break'):
                        _t1038 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1038 = None
                    return _t1038
                _t1039 = _t1037(msg)
                deconstruct_result313 = _t1039
                
                if deconstruct_result313 is not None:
                    _t1041 = self.pretty_break(deconstruct_result313)
                    _t1040 = _t1041
                else:
                    def _t1042(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('monoid_def'):
                            _t1043 = _dollar_dollar.monoid_def
                        else:
                            _t1043 = None
                        return _t1043
                    _t1044 = _t1042(msg)
                    deconstruct_result312 = _t1044
                    
                    if deconstruct_result312 is not None:
                        _t1046 = self.pretty_monoid_def(deconstruct_result312)
                        _t1045 = _t1046
                    else:
                        def _t1047(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('monus_def'):
                                _t1048 = _dollar_dollar.monus_def
                            else:
                                _t1048 = None
                            return _t1048
                        _t1049 = _t1047(msg)
                        deconstruct_result311 = _t1049
                        
                        if deconstruct_result311 is not None:
                            _t1051 = self.pretty_monus_def(deconstruct_result311)
                            _t1050 = _t1051
                        else:
                            raise ParseError('No matching rule for instruction')
                        _t1045 = _t1050
                    _t1040 = _t1045
                _t1035 = _t1040
            _t1030 = _t1035
        return _t1030

    def pretty_assign(self, msg: logic_pb2.Assign) -> Optional[Never]:
        def _t1052(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1053 = _dollar_dollar.attrs
            else:
                _t1053 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1053,)
        _t1054 = _t1052(msg)
        fields316 = _t1054
        unwrapped_fields317 = fields316
        self.write('(')
        self.write('assign')
        self.indent()
        self.newline()
        field318 = unwrapped_fields317[0]
        _t1055 = self.pretty_relation_id(field318)
        self.newline()
        field319 = unwrapped_fields317[1]
        _t1056 = self.pretty_abstraction(field319)
        field320 = unwrapped_fields317[2]
        
        if field320 is not None:
            self.newline()
            opt_val321 = field320
            _t1058 = self.pretty_attrs(opt_val321)
            _t1057 = _t1058
        else:
            _t1057 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> Optional[Never]:
        def _t1059(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1060 = _dollar_dollar.attrs
            else:
                _t1060 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1060,)
        _t1061 = _t1059(msg)
        fields322 = _t1061
        unwrapped_fields323 = fields322
        self.write('(')
        self.write('upsert')
        self.indent()
        self.newline()
        field324 = unwrapped_fields323[0]
        _t1062 = self.pretty_relation_id(field324)
        self.newline()
        field325 = unwrapped_fields323[1]
        _t1063 = self.pretty_abstraction_with_arity(field325)
        field326 = unwrapped_fields323[2]
        
        if field326 is not None:
            self.newline()
            opt_val327 = field326
            _t1065 = self.pretty_attrs(opt_val327)
            _t1064 = _t1065
        else:
            _t1064 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> Optional[Never]:
        def _t1066(_dollar_dollar):
            _t1067 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1067, _dollar_dollar[0].value,)
        _t1068 = _t1066(msg)
        fields328 = _t1068
        unwrapped_fields329 = fields328
        self.write('(')
        field330 = unwrapped_fields329[0]
        _t1069 = self.pretty_bindings(field330)
        self.write(' ')
        field331 = unwrapped_fields329[1]
        _t1070 = self.pretty_formula(field331)
        self.write(')')
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> Optional[Never]:
        def _t1071(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1072 = _dollar_dollar.attrs
            else:
                _t1072 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1072,)
        _t1073 = _t1071(msg)
        fields332 = _t1073
        unwrapped_fields333 = fields332
        self.write('(')
        self.write('break')
        self.indent()
        self.newline()
        field334 = unwrapped_fields333[0]
        _t1074 = self.pretty_relation_id(field334)
        self.newline()
        field335 = unwrapped_fields333[1]
        _t1075 = self.pretty_abstraction(field335)
        field336 = unwrapped_fields333[2]
        
        if field336 is not None:
            self.newline()
            opt_val337 = field336
            _t1077 = self.pretty_attrs(opt_val337)
            _t1076 = _t1077
        else:
            _t1076 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> Optional[Never]:
        def _t1078(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1079 = _dollar_dollar.attrs
            else:
                _t1079 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1079,)
        _t1080 = _t1078(msg)
        fields338 = _t1080
        unwrapped_fields339 = fields338
        self.write('(')
        self.write('monoid')
        self.indent()
        self.newline()
        field340 = unwrapped_fields339[0]
        _t1081 = self.pretty_monoid(field340)
        self.newline()
        field341 = unwrapped_fields339[1]
        _t1082 = self.pretty_relation_id(field341)
        self.newline()
        field342 = unwrapped_fields339[2]
        _t1083 = self.pretty_abstraction_with_arity(field342)
        field343 = unwrapped_fields339[3]
        
        if field343 is not None:
            self.newline()
            opt_val344 = field343
            _t1085 = self.pretty_attrs(opt_val344)
            _t1084 = _t1085
        else:
            _t1084 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> Optional[Never]:
        def _t1086(_dollar_dollar):
            
            if _dollar_dollar.HasField('or_monoid'):
                _t1087 = _dollar_dollar.or_monoid
            else:
                _t1087 = None
            return _t1087
        _t1088 = _t1086(msg)
        deconstruct_result348 = _t1088
        
        if deconstruct_result348 is not None:
            _t1090 = self.pretty_or_monoid(deconstruct_result348)
            _t1089 = _t1090
        else:
            def _t1091(_dollar_dollar):
                
                if _dollar_dollar.HasField('min_monoid'):
                    _t1092 = _dollar_dollar.min_monoid
                else:
                    _t1092 = None
                return _t1092
            _t1093 = _t1091(msg)
            deconstruct_result347 = _t1093
            
            if deconstruct_result347 is not None:
                _t1095 = self.pretty_min_monoid(deconstruct_result347)
                _t1094 = _t1095
            else:
                def _t1096(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('max_monoid'):
                        _t1097 = _dollar_dollar.max_monoid
                    else:
                        _t1097 = None
                    return _t1097
                _t1098 = _t1096(msg)
                deconstruct_result346 = _t1098
                
                if deconstruct_result346 is not None:
                    _t1100 = self.pretty_max_monoid(deconstruct_result346)
                    _t1099 = _t1100
                else:
                    def _t1101(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('sum_monoid'):
                            _t1102 = _dollar_dollar.sum_monoid
                        else:
                            _t1102 = None
                        return _t1102
                    _t1103 = _t1101(msg)
                    deconstruct_result345 = _t1103
                    
                    if deconstruct_result345 is not None:
                        _t1105 = self.pretty_sum_monoid(deconstruct_result345)
                        _t1104 = _t1105
                    else:
                        raise ParseError('No matching rule for monoid')
                    _t1099 = _t1104
                _t1094 = _t1099
            _t1089 = _t1094
        return _t1089

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> Optional[Never]:
        def _t1106(_dollar_dollar):
            return _dollar_dollar
        _t1107 = _t1106(msg)
        fields349 = _t1107
        unwrapped_fields350 = fields349
        self.write('(')
        self.write('or')
        self.write(')')
        return None

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid) -> Optional[Never]:
        def _t1108(_dollar_dollar):
            return _dollar_dollar.type
        _t1109 = _t1108(msg)
        fields351 = _t1109
        unwrapped_fields352 = fields351
        self.write('(')
        self.write('min')
        self.indent()
        self.newline()
        _t1110 = self.pretty_type(unwrapped_fields352)
        self.dedent()
        self.write(')')
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> Optional[Never]:
        def _t1111(_dollar_dollar):
            return _dollar_dollar.type
        _t1112 = _t1111(msg)
        fields353 = _t1112
        unwrapped_fields354 = fields353
        self.write('(')
        self.write('max')
        self.indent()
        self.newline()
        _t1113 = self.pretty_type(unwrapped_fields354)
        self.dedent()
        self.write(')')
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> Optional[Never]:
        def _t1114(_dollar_dollar):
            return _dollar_dollar.type
        _t1115 = _t1114(msg)
        fields355 = _t1115
        unwrapped_fields356 = fields355
        self.write('(')
        self.write('sum')
        self.indent()
        self.newline()
        _t1116 = self.pretty_type(unwrapped_fields356)
        self.dedent()
        self.write(')')
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> Optional[Never]:
        def _t1117(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1118 = _dollar_dollar.attrs
            else:
                _t1118 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1118,)
        _t1119 = _t1117(msg)
        fields357 = _t1119
        unwrapped_fields358 = fields357
        self.write('(')
        self.write('monus')
        self.indent()
        self.newline()
        field359 = unwrapped_fields358[0]
        _t1120 = self.pretty_monoid(field359)
        self.newline()
        field360 = unwrapped_fields358[1]
        _t1121 = self.pretty_relation_id(field360)
        self.newline()
        field361 = unwrapped_fields358[2]
        _t1122 = self.pretty_abstraction_with_arity(field361)
        field362 = unwrapped_fields358[3]
        
        if field362 is not None:
            self.newline()
            opt_val363 = field362
            _t1124 = self.pretty_attrs(opt_val363)
            _t1123 = _t1124
        else:
            _t1123 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> Optional[Never]:
        def _t1125(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1126 = _t1125(msg)
        fields364 = _t1126
        unwrapped_fields365 = fields364
        self.write('(')
        self.write('functional_dependency')
        self.indent()
        self.newline()
        field366 = unwrapped_fields365[0]
        _t1127 = self.pretty_relation_id(field366)
        self.newline()
        field367 = unwrapped_fields365[1]
        _t1128 = self.pretty_abstraction(field367)
        self.newline()
        field368 = unwrapped_fields365[2]
        _t1129 = self.pretty_functional_dependency_keys(field368)
        self.newline()
        field369 = unwrapped_fields365[3]
        _t1130 = self.pretty_functional_dependency_values(field369)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_keys(self, msg: list[logic_pb2.Var]) -> Optional[Never]:
        def _t1131(_dollar_dollar):
            return _dollar_dollar
        _t1132 = _t1131(msg)
        fields370 = _t1132
        unwrapped_fields371 = fields370
        self.write('(')
        self.write('keys')
        self.indent()
        if not len(unwrapped_fields371) == 0:
            self.newline()
            for i373, elem372 in enumerate(unwrapped_fields371):
                
                if (i373 > 0):
                    self.newline()
                    _t1133 = None
                else:
                    _t1133 = None
                _t1134 = self.pretty_var(elem372)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_values(self, msg: list[logic_pb2.Var]) -> Optional[Never]:
        def _t1135(_dollar_dollar):
            return _dollar_dollar
        _t1136 = _t1135(msg)
        fields374 = _t1136
        unwrapped_fields375 = fields374
        self.write('(')
        self.write('values')
        self.indent()
        if not len(unwrapped_fields375) == 0:
            self.newline()
            for i377, elem376 in enumerate(unwrapped_fields375):
                
                if (i377 > 0):
                    self.newline()
                    _t1137 = None
                else:
                    _t1137 = None
                _t1138 = self.pretty_var(elem376)
        self.dedent()
        self.write(')')
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> Optional[Never]:
        def _t1139(_dollar_dollar):
            
            if _dollar_dollar.HasField('rel_edb'):
                _t1140 = _dollar_dollar.rel_edb
            else:
                _t1140 = None
            return _t1140
        _t1141 = _t1139(msg)
        deconstruct_result380 = _t1141
        
        if deconstruct_result380 is not None:
            _t1143 = self.pretty_rel_edb(deconstruct_result380)
            _t1142 = _t1143
        else:
            def _t1144(_dollar_dollar):
                
                if _dollar_dollar.HasField('betree_relation'):
                    _t1145 = _dollar_dollar.betree_relation
                else:
                    _t1145 = None
                return _t1145
            _t1146 = _t1144(msg)
            deconstruct_result379 = _t1146
            
            if deconstruct_result379 is not None:
                _t1148 = self.pretty_betree_relation(deconstruct_result379)
                _t1147 = _t1148
            else:
                def _t1149(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('csv_data'):
                        _t1150 = _dollar_dollar.csv_data
                    else:
                        _t1150 = None
                    return _t1150
                _t1151 = _t1149(msg)
                deconstruct_result378 = _t1151
                
                if deconstruct_result378 is not None:
                    _t1153 = self.pretty_csv_data(deconstruct_result378)
                    _t1152 = _t1153
                else:
                    raise ParseError('No matching rule for data')
                _t1147 = _t1152
            _t1142 = _t1147
        return _t1142

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> Optional[Never]:
        def _t1154(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1155 = _t1154(msg)
        fields381 = _t1155
        unwrapped_fields382 = fields381
        self.write('(')
        self.write('rel_edb')
        self.indent()
        self.newline()
        field383 = unwrapped_fields382[0]
        _t1156 = self.pretty_relation_id(field383)
        self.newline()
        field384 = unwrapped_fields382[1]
        _t1157 = self.pretty_rel_edb_path(field384)
        self.newline()
        field385 = unwrapped_fields382[2]
        _t1158 = self.pretty_rel_edb_types(field385)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_edb_path(self, msg: list[str]) -> Optional[Never]:
        def _t1159(_dollar_dollar):
            return _dollar_dollar
        _t1160 = _t1159(msg)
        fields386 = _t1160
        unwrapped_fields387 = fields386
        self.write('[')
        for i389, elem388 in enumerate(unwrapped_fields387):
            
            if (i389 > 0):
                self.newline()
                _t1161 = None
            else:
                _t1161 = None
            self.write(self.format_string_value(elem388))
        self.write(']')
        return None

    def pretty_rel_edb_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1162(_dollar_dollar):
            return _dollar_dollar
        _t1163 = _t1162(msg)
        fields390 = _t1163
        unwrapped_fields391 = fields390
        self.write('[')
        for i393, elem392 in enumerate(unwrapped_fields391):
            
            if (i393 > 0):
                self.newline()
                _t1164 = None
            else:
                _t1164 = None
            _t1165 = self.pretty_type(elem392)
        self.write(']')
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> Optional[Never]:
        def _t1166(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1167 = _t1166(msg)
        fields394 = _t1167
        unwrapped_fields395 = fields394
        self.write('(')
        self.write('betree_relation')
        self.indent()
        self.newline()
        field396 = unwrapped_fields395[0]
        _t1168 = self.pretty_relation_id(field396)
        self.newline()
        field397 = unwrapped_fields395[1]
        _t1169 = self.pretty_betree_info(field397)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> Optional[Never]:
        def _t1170(_dollar_dollar):
            _t1171 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1171,)
        _t1172 = _t1170(msg)
        fields398 = _t1172
        unwrapped_fields399 = fields398
        self.write('(')
        self.write('betree_info')
        self.indent()
        self.newline()
        field400 = unwrapped_fields399[0]
        _t1173 = self.pretty_betree_info_key_types(field400)
        self.newline()
        field401 = unwrapped_fields399[1]
        _t1174 = self.pretty_betree_info_value_types(field401)
        self.newline()
        field402 = unwrapped_fields399[2]
        _t1175 = self.pretty_config_dict(field402)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_key_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1176(_dollar_dollar):
            return _dollar_dollar
        _t1177 = _t1176(msg)
        fields403 = _t1177
        unwrapped_fields404 = fields403
        self.write('(')
        self.write('key_types')
        self.indent()
        if not len(unwrapped_fields404) == 0:
            self.newline()
            for i406, elem405 in enumerate(unwrapped_fields404):
                
                if (i406 > 0):
                    self.newline()
                    _t1178 = None
                else:
                    _t1178 = None
                _t1179 = self.pretty_type(elem405)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_value_types(self, msg: list[logic_pb2.Type]) -> Optional[Never]:
        def _t1180(_dollar_dollar):
            return _dollar_dollar
        _t1181 = _t1180(msg)
        fields407 = _t1181
        unwrapped_fields408 = fields407
        self.write('(')
        self.write('value_types')
        self.indent()
        if not len(unwrapped_fields408) == 0:
            self.newline()
            for i410, elem409 in enumerate(unwrapped_fields408):
                
                if (i410 > 0):
                    self.newline()
                    _t1182 = None
                else:
                    _t1182 = None
                _t1183 = self.pretty_type(elem409)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> Optional[Never]:
        def _t1184(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1185 = _t1184(msg)
        fields411 = _t1185
        unwrapped_fields412 = fields411
        self.write('(')
        self.write('csv_data')
        self.indent()
        self.newline()
        field413 = unwrapped_fields412[0]
        _t1186 = self.pretty_csvlocator(field413)
        self.newline()
        field414 = unwrapped_fields412[1]
        _t1187 = self.pretty_csv_config(field414)
        self.newline()
        field415 = unwrapped_fields412[2]
        _t1188 = self.pretty_csv_columns(field415)
        self.newline()
        field416 = unwrapped_fields412[3]
        _t1189 = self.pretty_csv_asof(field416)
        self.dedent()
        self.write(')')
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> Optional[Never]:
        def _t1190(_dollar_dollar):
            
            if not len(_dollar_dollar.paths) == 0:
                _t1191 = _dollar_dollar.paths
            else:
                _t1191 = None
            
            if _dollar_dollar.inline_data.decode('utf-8') != '':
                _t1192 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1192 = None
            return (_t1191, _t1192,)
        _t1193 = _t1190(msg)
        fields417 = _t1193
        unwrapped_fields418 = fields417
        self.write('(')
        self.write('csv_locator')
        self.indent()
        field419 = unwrapped_fields418[0]
        
        if field419 is not None:
            self.newline()
            opt_val420 = field419
            _t1195 = self.pretty_csv_locator_paths(opt_val420)
            _t1194 = _t1195
        else:
            _t1194 = None
        field421 = unwrapped_fields418[1]
        
        if field421 is not None:
            self.newline()
            opt_val422 = field421
            _t1197 = self.pretty_csv_locator_inline_data(opt_val422)
            _t1196 = _t1197
        else:
            _t1196 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_locator_paths(self, msg: list[str]) -> Optional[Never]:
        def _t1198(_dollar_dollar):
            return _dollar_dollar
        _t1199 = _t1198(msg)
        fields423 = _t1199
        unwrapped_fields424 = fields423
        self.write('(')
        self.write('paths')
        self.indent()
        if not len(unwrapped_fields424) == 0:
            self.newline()
            for i426, elem425 in enumerate(unwrapped_fields424):
                
                if (i426 > 0):
                    self.newline()
                    _t1200 = None
                else:
                    _t1200 = None
                self.write(self.format_string_value(elem425))
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_locator_inline_data(self, msg: str) -> Optional[Never]:
        def _t1201(_dollar_dollar):
            return _dollar_dollar
        _t1202 = _t1201(msg)
        fields427 = _t1202
        unwrapped_fields428 = fields427
        self.write('(')
        self.write('inline_data')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields428))
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig) -> Optional[Never]:
        def _t1203(_dollar_dollar):
            _t1204 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1204
        _t1205 = _t1203(msg)
        fields429 = _t1205
        unwrapped_fields430 = fields429
        self.write('(')
        self.write('csv_config')
        self.indent()
        self.newline()
        _t1206 = self.pretty_config_dict(unwrapped_fields430)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_columns(self, msg: list[logic_pb2.CSVColumn]) -> Optional[Never]:
        def _t1207(_dollar_dollar):
            return _dollar_dollar
        _t1208 = _t1207(msg)
        fields431 = _t1208
        unwrapped_fields432 = fields431
        self.write('(')
        self.write('columns')
        self.indent()
        if not len(unwrapped_fields432) == 0:
            self.newline()
            for i434, elem433 in enumerate(unwrapped_fields432):
                
                if (i434 > 0):
                    self.newline()
                    _t1209 = None
                else:
                    _t1209 = None
                _t1210 = self.pretty_csv_column(elem433)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> Optional[Never]:
        def _t1211(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1212 = _t1211(msg)
        fields435 = _t1212
        unwrapped_fields436 = fields435
        self.write('(')
        self.write('column')
        self.indent()
        self.newline()
        field437 = unwrapped_fields436[0]
        self.write(self.format_string_value(field437))
        self.newline()
        field438 = unwrapped_fields436[1]
        _t1213 = self.pretty_relation_id(field438)
        self.write('[')
        field439 = unwrapped_fields436[2]
        if not len(field439) == 0:
            self.newline()
            for i441, elem440 in enumerate(field439):
                
                if (i441 > 0):
                    self.newline()
                    _t1214 = None
                else:
                    _t1214 = None
                _t1215 = self.pretty_type(elem440)
        self.write(']')
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_asof(self, msg: str) -> Optional[Never]:
        def _t1216(_dollar_dollar):
            return _dollar_dollar
        _t1217 = _t1216(msg)
        fields442 = _t1217
        unwrapped_fields443 = fields442
        self.write('(')
        self.write('asof')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields443))
        self.dedent()
        self.write(')')
        return None

    def pretty_undefine(self, msg: transactions_pb2.Undefine) -> Optional[Never]:
        def _t1218(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1219 = _t1218(msg)
        fields444 = _t1219
        unwrapped_fields445 = fields444
        self.write('(')
        self.write('undefine')
        self.indent()
        self.newline()
        _t1220 = self.pretty_fragment_id(unwrapped_fields445)
        self.dedent()
        self.write(')')
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> Optional[Never]:
        def _t1221(_dollar_dollar):
            return _dollar_dollar.relations
        _t1222 = _t1221(msg)
        fields446 = _t1222
        unwrapped_fields447 = fields446
        self.write('(')
        self.write('context')
        self.indent()
        if not len(unwrapped_fields447) == 0:
            self.newline()
            for i449, elem448 in enumerate(unwrapped_fields447):
                
                if (i449 > 0):
                    self.newline()
                    _t1223 = None
                else:
                    _t1223 = None
                _t1224 = self.pretty_relation_id(elem448)
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_reads(self, msg: list[transactions_pb2.Read]) -> Optional[Never]:
        def _t1225(_dollar_dollar):
            return _dollar_dollar
        _t1226 = _t1225(msg)
        fields450 = _t1226
        unwrapped_fields451 = fields450
        self.write('(')
        self.write('reads')
        self.indent()
        if not len(unwrapped_fields451) == 0:
            self.newline()
            for i453, elem452 in enumerate(unwrapped_fields451):
                
                if (i453 > 0):
                    self.newline()
                    _t1227 = None
                else:
                    _t1227 = None
                _t1228 = self.pretty_read(elem452)
        self.dedent()
        self.write(')')
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> Optional[Never]:
        def _t1229(_dollar_dollar):
            
            if _dollar_dollar.HasField('demand'):
                _t1230 = _dollar_dollar.demand
            else:
                _t1230 = None
            return _t1230
        _t1231 = _t1229(msg)
        deconstruct_result458 = _t1231
        
        if deconstruct_result458 is not None:
            _t1233 = self.pretty_demand(deconstruct_result458)
            _t1232 = _t1233
        else:
            def _t1234(_dollar_dollar):
                
                if _dollar_dollar.HasField('output'):
                    _t1235 = _dollar_dollar.output
                else:
                    _t1235 = None
                return _t1235
            _t1236 = _t1234(msg)
            deconstruct_result457 = _t1236
            
            if deconstruct_result457 is not None:
                _t1238 = self.pretty_output(deconstruct_result457)
                _t1237 = _t1238
            else:
                def _t1239(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('what_if'):
                        _t1240 = _dollar_dollar.what_if
                    else:
                        _t1240 = None
                    return _t1240
                _t1241 = _t1239(msg)
                deconstruct_result456 = _t1241
                
                if deconstruct_result456 is not None:
                    _t1243 = self.pretty_what_if(deconstruct_result456)
                    _t1242 = _t1243
                else:
                    def _t1244(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('abort'):
                            _t1245 = _dollar_dollar.abort
                        else:
                            _t1245 = None
                        return _t1245
                    _t1246 = _t1244(msg)
                    deconstruct_result455 = _t1246
                    
                    if deconstruct_result455 is not None:
                        _t1248 = self.pretty_abort(deconstruct_result455)
                        _t1247 = _t1248
                    else:
                        def _t1249(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('export'):
                                _t1250 = _dollar_dollar.export
                            else:
                                _t1250 = None
                            return _t1250
                        _t1251 = _t1249(msg)
                        deconstruct_result454 = _t1251
                        
                        if deconstruct_result454 is not None:
                            _t1253 = self.pretty_export(deconstruct_result454)
                            _t1252 = _t1253
                        else:
                            raise ParseError('No matching rule for read')
                        _t1247 = _t1252
                    _t1242 = _t1247
                _t1237 = _t1242
            _t1232 = _t1237
        return _t1232

    def pretty_demand(self, msg: transactions_pb2.Demand) -> Optional[Never]:
        def _t1254(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1255 = _t1254(msg)
        fields459 = _t1255
        unwrapped_fields460 = fields459
        self.write('(')
        self.write('demand')
        self.indent()
        self.newline()
        _t1256 = self.pretty_relation_id(unwrapped_fields460)
        self.dedent()
        self.write(')')
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> Optional[Never]:
        def _t1257(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        _t1258 = _t1257(msg)
        fields461 = _t1258
        unwrapped_fields462 = fields461
        self.write('(')
        self.write('output')
        self.indent()
        self.newline()
        field463 = unwrapped_fields462[0]
        _t1259 = self.pretty_name(field463)
        self.newline()
        field464 = unwrapped_fields462[1]
        _t1260 = self.pretty_relation_id(field464)
        self.dedent()
        self.write(')')
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> Optional[Never]:
        def _t1261(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1262 = _t1261(msg)
        fields465 = _t1262
        unwrapped_fields466 = fields465
        self.write('(')
        self.write('what_if')
        self.indent()
        self.newline()
        field467 = unwrapped_fields466[0]
        _t1263 = self.pretty_name(field467)
        self.newline()
        field468 = unwrapped_fields466[1]
        _t1264 = self.pretty_epoch(field468)
        self.dedent()
        self.write(')')
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> Optional[Never]:
        def _t1265(_dollar_dollar):
            
            if _dollar_dollar.name != 'abort':
                _t1266 = _dollar_dollar.name
            else:
                _t1266 = None
            return (_t1266, _dollar_dollar.relation_id,)
        _t1267 = _t1265(msg)
        fields469 = _t1267
        unwrapped_fields470 = fields469
        self.write('(')
        self.write('abort')
        self.indent()
        field471 = unwrapped_fields470[0]
        
        if field471 is not None:
            self.newline()
            opt_val472 = field471
            _t1269 = self.pretty_name(opt_val472)
            _t1268 = _t1269
        else:
            _t1268 = None
        self.newline()
        field473 = unwrapped_fields470[1]
        _t1270 = self.pretty_relation_id(field473)
        self.dedent()
        self.write(')')
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> Optional[Never]:
        def _t1271(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1272 = _t1271(msg)
        fields474 = _t1272
        unwrapped_fields475 = fields474
        self.write('(')
        self.write('export')
        self.indent()
        self.newline()
        _t1273 = self.pretty_export_csv_config(unwrapped_fields475)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> Optional[Never]:
        def _t1274(_dollar_dollar):
            _t1275 = self.deconstruct_export_csv_config(_dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1275,)
        _t1276 = _t1274(msg)
        fields476 = _t1276
        unwrapped_fields477 = fields476
        self.write('(')
        self.write('export_csv_config')
        self.indent()
        self.newline()
        field478 = unwrapped_fields477[0]
        _t1277 = self.pretty_export_csv_path(field478)
        self.newline()
        field479 = unwrapped_fields477[1]
        _t1278 = self.pretty_export_csv_columns(field479)
        self.newline()
        field480 = unwrapped_fields477[2]
        _t1279 = self.pretty_config_dict(field480)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_path(self, msg: str) -> Optional[Never]:
        def _t1280(_dollar_dollar):
            return _dollar_dollar
        _t1281 = _t1280(msg)
        fields481 = _t1281
        unwrapped_fields482 = fields481
        self.write('(')
        self.write('path')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields482))
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_columns(self, msg: list[transactions_pb2.ExportCSVColumn]) -> Optional[Never]:
        def _t1282(_dollar_dollar):
            return _dollar_dollar
        _t1283 = _t1282(msg)
        fields483 = _t1283
        unwrapped_fields484 = fields483
        self.write('(')
        self.write('columns')
        self.indent()
        if not len(unwrapped_fields484) == 0:
            self.newline()
            for i486, elem485 in enumerate(unwrapped_fields484):
                
                if (i486 > 0):
                    self.newline()
                    _t1284 = None
                else:
                    _t1284 = None
                _t1285 = self.pretty_export_csv_column(elem485)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> Optional[Never]:
        def _t1286(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1287 = _t1286(msg)
        fields487 = _t1287
        unwrapped_fields488 = fields487
        self.write('(')
        self.write('column')
        self.indent()
        self.newline()
        field489 = unwrapped_fields488[0]
        self.write(self.format_string_value(field489))
        self.newline()
        field490 = unwrapped_fields488[1]
        _t1288 = self.pretty_relation_id(field490)
        self.dedent()
        self.write(')')
        return None


def pretty(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
