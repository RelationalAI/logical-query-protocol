"""
Auto-generated pretty printer.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the pretty printer, edit the generator code
in `meta/` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer python
"""

from io import StringIO
from collections.abc import Sequence
from typing import Any, IO, NoReturn, Optional

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

    # --- Helper functions ---

    def _extract_value_int32(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t1267 = value.HasField('int_value')
        else:
            _t1267 = False
        if _t1267:
            assert value is not None
            return int(value.int_value)
        return int(default)

    def _extract_value_int64(self, value: Optional[logic_pb2.Value], default: int) -> int:
        
        if value is not None:
            assert value is not None
            _t1268 = value.HasField('int_value')
        else:
            _t1268 = False
        if _t1268:
            assert value is not None
            return value.int_value
        return default

    def _extract_value_float64(self, value: Optional[logic_pb2.Value], default: float) -> float:
        
        if value is not None:
            assert value is not None
            _t1269 = value.HasField('float_value')
        else:
            _t1269 = False
        if _t1269:
            assert value is not None
            return value.float_value
        return default

    def _extract_value_string(self, value: Optional[logic_pb2.Value], default: str) -> str:
        
        if value is not None:
            assert value is not None
            _t1270 = value.HasField('string_value')
        else:
            _t1270 = False
        if _t1270:
            assert value is not None
            return value.string_value
        return default

    def _extract_value_boolean(self, value: Optional[logic_pb2.Value], default: bool) -> bool:
        
        if value is not None:
            assert value is not None
            _t1271 = value.HasField('boolean_value')
        else:
            _t1271 = False
        if _t1271:
            assert value is not None
            return value.boolean_value
        return default

    def _extract_value_bytes(self, value: Optional[logic_pb2.Value], default: bytes) -> bytes:
        
        if value is not None:
            assert value is not None
            _t1272 = value.HasField('string_value')
        else:
            _t1272 = False
        if _t1272:
            assert value is not None
            return value.string_value.encode()
        return default

    def _extract_value_uint128(self, value: Optional[logic_pb2.Value], default: logic_pb2.UInt128Value) -> logic_pb2.UInt128Value:
        
        if value is not None:
            assert value is not None
            _t1273 = value.HasField('uint128_value')
        else:
            _t1273 = False
        if _t1273:
            assert value is not None
            return value.uint128_value
        return default

    def _extract_value_string_list(self, value: Optional[logic_pb2.Value], default: Sequence[str]) -> Sequence[str]:
        
        if value is not None:
            assert value is not None
            _t1274 = value.HasField('string_value')
        else:
            _t1274 = False
        if _t1274:
            assert value is not None
            return [value.string_value]
        return default

    def _try_extract_value_int64(self, value: Optional[logic_pb2.Value]) -> Optional[int]:
        
        if value is not None:
            assert value is not None
            _t1275 = value.HasField('int_value')
        else:
            _t1275 = False
        if _t1275:
            assert value is not None
            return value.int_value
        return None

    def _try_extract_value_float64(self, value: Optional[logic_pb2.Value]) -> Optional[float]:
        
        if value is not None:
            assert value is not None
            _t1276 = value.HasField('float_value')
        else:
            _t1276 = False
        if _t1276:
            assert value is not None
            return value.float_value
        return None

    def _try_extract_value_string(self, value: Optional[logic_pb2.Value]) -> Optional[str]:
        
        if value is not None:
            assert value is not None
            _t1277 = value.HasField('string_value')
        else:
            _t1277 = False
        if _t1277:
            assert value is not None
            return value.string_value
        return None

    def _try_extract_value_bytes(self, value: Optional[logic_pb2.Value]) -> Optional[bytes]:
        
        if value is not None:
            assert value is not None
            _t1278 = value.HasField('string_value')
        else:
            _t1278 = False
        if _t1278:
            assert value is not None
            return value.string_value.encode()
        return None

    def _try_extract_value_uint128(self, value: Optional[logic_pb2.Value]) -> Optional[logic_pb2.UInt128Value]:
        
        if value is not None:
            assert value is not None
            _t1279 = value.HasField('uint128_value')
        else:
            _t1279 = False
        if _t1279:
            assert value is not None
            return value.uint128_value
        return None

    def _try_extract_value_string_list(self, value: Optional[logic_pb2.Value]) -> Optional[Sequence[str]]:
        
        if value is not None:
            assert value is not None
            _t1280 = value.HasField('string_value')
        else:
            _t1280 = False
        if _t1280:
            assert value is not None
            return [value.string_value]
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1281 = self._extract_value_int32(config.get('csv_header_row'), 1)
        header_row = _t1281
        _t1282 = self._extract_value_int64(config.get('csv_skip'), 0)
        skip = _t1282
        _t1283 = self._extract_value_string(config.get('csv_new_line'), '')
        new_line = _t1283
        _t1284 = self._extract_value_string(config.get('csv_delimiter'), ',')
        delimiter = _t1284
        _t1285 = self._extract_value_string(config.get('csv_quotechar'), '"')
        quotechar = _t1285
        _t1286 = self._extract_value_string(config.get('csv_escapechar'), '"')
        escapechar = _t1286
        _t1287 = self._extract_value_string(config.get('csv_comment'), '')
        comment = _t1287
        _t1288 = self._extract_value_string_list(config.get('csv_missing_strings'), [])
        missing_strings = _t1288
        _t1289 = self._extract_value_string(config.get('csv_decimal_separator'), '.')
        decimal_separator = _t1289
        _t1290 = self._extract_value_string(config.get('csv_encoding'), 'utf-8')
        encoding = _t1290
        _t1291 = self._extract_value_string(config.get('csv_compression'), 'auto')
        compression = _t1291
        _t1292 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1292

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1293 = self._try_extract_value_float64(config.get('betree_config_epsilon'))
        epsilon = _t1293
        _t1294 = self._try_extract_value_int64(config.get('betree_config_max_pivots'))
        max_pivots = _t1294
        _t1295 = self._try_extract_value_int64(config.get('betree_config_max_deltas'))
        max_deltas = _t1295
        _t1296 = self._try_extract_value_int64(config.get('betree_config_max_leaf'))
        max_leaf = _t1296
        _t1297 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1297
        _t1298 = self._try_extract_value_uint128(config.get('betree_locator_root_pageid'))
        root_pageid = _t1298
        _t1299 = self._try_extract_value_bytes(config.get('betree_locator_inline_data'))
        inline_data = _t1299
        _t1300 = self._try_extract_value_int64(config.get('betree_locator_element_count'))
        element_count = _t1300
        _t1301 = self._try_extract_value_int64(config.get('betree_locator_tree_height'))
        tree_height = _t1301
        _t1302 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1302
        _t1303 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1303

    def default_configure(self) -> transactions_pb2.Configure:
        _t1304 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1304
        _t1305 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1305

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
        _t1306 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1306
        _t1307 = self._extract_value_int64(config.get('semantics_version'), 0)
        semantics_version = _t1307
        _t1308 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1308

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1309 = self._extract_value_int64(config.get('partition_size'), 0)
        partition_size = _t1309
        _t1310 = self._extract_value_string(config.get('compression'), '')
        compression = _t1310
        _t1311 = self._extract_value_boolean(config.get('syntax_header_row'), True)
        syntax_header_row = _t1311
        _t1312 = self._extract_value_string(config.get('syntax_missing_string'), '')
        syntax_missing_string = _t1312
        _t1313 = self._extract_value_string(config.get('syntax_delim'), ',')
        syntax_delim = _t1313
        _t1314 = self._extract_value_string(config.get('syntax_quotechar'), '"')
        syntax_quotechar = _t1314
        _t1315 = self._extract_value_string(config.get('syntax_escapechar'), '\\')
        syntax_escapechar = _t1315
        _t1316 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1316

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1317 = logic_pb2.Value(int_value=int(v))
        return _t1317

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1318 = logic_pb2.Value(int_value=v)
        return _t1318

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1319 = logic_pb2.Value(float_value=v)
        return _t1319

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1320 = logic_pb2.Value(string_value=v)
        return _t1320

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1321 = logic_pb2.Value(boolean_value=v)
        return _t1321

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1322 = logic_pb2.Value(uint128_value=v)
        return _t1322

    def is_default_configure(self, cfg: transactions_pb2.Configure) -> bool:
        if cfg.semantics_version != 0:
            return False
        if cfg.ivm_config.level != transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
            return False
        return True

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1323 = self._make_value_string('auto')
            result.append(('ivm.maintenance_level', _t1323,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1324 = self._make_value_string('all')
                result.append(('ivm.maintenance_level', _t1324,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1325 = self._make_value_string('off')
                    result.append(('ivm.maintenance_level', _t1325,))
        _t1326 = self._make_value_int64(msg.semantics_version)
        result.append(('semantics_version', _t1326,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1327 = self._make_value_int32(msg.header_row)
        result.append(('csv_header_row', _t1327,))
        _t1328 = self._make_value_int64(msg.skip)
        result.append(('csv_skip', _t1328,))
        if msg.new_line != '':
            _t1329 = self._make_value_string(msg.new_line)
            result.append(('csv_new_line', _t1329,))
        _t1330 = self._make_value_string(msg.delimiter)
        result.append(('csv_delimiter', _t1330,))
        _t1331 = self._make_value_string(msg.quotechar)
        result.append(('csv_quotechar', _t1331,))
        _t1332 = self._make_value_string(msg.escapechar)
        result.append(('csv_escapechar', _t1332,))
        if msg.comment != '':
            _t1333 = self._make_value_string(msg.comment)
            result.append(('csv_comment', _t1333,))
        for missing_string in msg.missing_strings:
            _t1334 = self._make_value_string(missing_string)
            result.append(('csv_missing_strings', _t1334,))
        _t1335 = self._make_value_string(msg.decimal_separator)
        result.append(('csv_decimal_separator', _t1335,))
        _t1336 = self._make_value_string(msg.encoding)
        result.append(('csv_encoding', _t1336,))
        _t1337 = self._make_value_string(msg.compression)
        result.append(('csv_compression', _t1337,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1338 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(('betree_config_epsilon', _t1338,))
        _t1339 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(('betree_config_max_pivots', _t1339,))
        _t1340 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(('betree_config_max_deltas', _t1340,))
        _t1341 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(('betree_config_max_leaf', _t1341,))
        if msg.relation_locator.HasField('root_pageid'):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1342 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(('betree_locator_root_pageid', _t1342,))
        if msg.relation_locator.HasField('inline_data'):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1343 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(('betree_locator_inline_data', _t1343,))
        _t1344 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(('betree_locator_element_count', _t1344,))
        _t1345 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(('betree_locator_tree_height', _t1345,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1346 = self._make_value_int64(msg.partition_size)
            result.append(('partition_size', _t1346,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1347 = self._make_value_string(msg.compression)
            result.append(('compression', _t1347,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1348 = self._make_value_boolean(msg.syntax_header_row)
            result.append(('syntax_header_row', _t1348,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1349 = self._make_value_string(msg.syntax_missing_string)
            result.append(('syntax_missing_string', _t1349,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1350 = self._make_value_string(msg.syntax_delim)
            result.append(('syntax_delim', _t1350,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1351 = self._make_value_string(msg.syntax_quotechar)
            result.append(('syntax_quotechar', _t1351,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1352 = self._make_value_string(msg.syntax_escapechar)
            result.append(('syntax_escapechar', _t1352,))
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

    def pretty_transaction(self, msg: transactions_pb2.Transaction) -> Optional[NoReturn]:
        def _t495(_dollar_dollar):
            
            if _dollar_dollar.HasField('configure'):
                _t496 = _dollar_dollar.configure
            else:
                _t496 = None
            
            if _dollar_dollar.HasField('sync'):
                _t497 = _dollar_dollar.sync
            else:
                _t497 = None
            return (_t496, _t497, _dollar_dollar.epochs,)
        _t498 = _t495(msg)
        fields0 = _t498
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
            _t500 = self.pretty_configure(opt_val3)
            _t499 = _t500
        else:
            _t499 = None
        field4 = unwrapped_fields1[1]
        
        if field4 is not None:
            self.newline()
            assert field4 is not None
            opt_val5 = field4
            _t502 = self.pretty_sync(opt_val5)
            _t501 = _t502
        else:
            _t501 = None
        field6 = unwrapped_fields1[2]
        if not len(field6) == 0:
            self.newline()
            for i8, elem7 in enumerate(field6):
                if (i8 > 0):
                    self.newline()
                _t503 = self.pretty_epoch(elem7)
        self.dedent()
        self.write(')')
        return None

    def pretty_configure(self, msg: transactions_pb2.Configure) -> Optional[NoReturn]:
        def _t504(_dollar_dollar):
            _t505 = self.deconstruct_configure(_dollar_dollar)
            return _t505
        _t506 = _t504(msg)
        fields9 = _t506
        assert fields9 is not None
        unwrapped_fields10 = fields9
        self.write('(')
        self.write('configure')
        self.indent()
        self.newline()
        _t507 = self.pretty_config_dict(unwrapped_fields10)
        self.dedent()
        self.write(')')
        return None

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]) -> Optional[NoReturn]:
        def _t508(_dollar_dollar):
            return _dollar_dollar
        _t509 = _t508(msg)
        fields11 = _t509
        assert fields11 is not None
        unwrapped_fields12 = fields11
        self.write('{')
        if not len(unwrapped_fields12) == 0:
            self.write(' ')
            for i14, elem13 in enumerate(unwrapped_fields12):
                if (i14 > 0):
                    self.newline()
                _t510 = self.pretty_config_key_value(elem13)
        self.write('}')
        return None

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]) -> Optional[NoReturn]:
        def _t511(_dollar_dollar):
            return (_dollar_dollar[0], _dollar_dollar[1],)
        _t512 = _t511(msg)
        fields15 = _t512
        assert fields15 is not None
        unwrapped_fields16 = fields15
        self.write(':')
        field17 = unwrapped_fields16[0]
        self.write(field17)
        self.write(' ')
        field18 = unwrapped_fields16[1]
        _t513 = self.pretty_value(field18)
        return _t513

    def pretty_value(self, msg: logic_pb2.Value) -> Optional[NoReturn]:
        def _t514(_dollar_dollar):
            
            if _dollar_dollar.HasField('date_value'):
                _t515 = _dollar_dollar.date_value
            else:
                _t515 = None
            return _t515
        _t516 = _t514(msg)
        deconstruct_result29 = _t516
        
        if deconstruct_result29 is not None:
            _t518 = self.pretty_date(deconstruct_result29)
            _t517 = _t518
        else:
            def _t519(_dollar_dollar):
                
                if _dollar_dollar.HasField('datetime_value'):
                    _t520 = _dollar_dollar.datetime_value
                else:
                    _t520 = None
                return _t520
            _t521 = _t519(msg)
            deconstruct_result28 = _t521
            
            if deconstruct_result28 is not None:
                _t523 = self.pretty_datetime(deconstruct_result28)
                _t522 = _t523
            else:
                def _t524(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('string_value'):
                        _t525 = _dollar_dollar.string_value
                    else:
                        _t525 = None
                    return _t525
                _t526 = _t524(msg)
                deconstruct_result27 = _t526
                
                if deconstruct_result27 is not None:
                    self.write(self.format_string_value(deconstruct_result27))
                    _t527 = None
                else:
                    def _t528(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('int_value'):
                            _t529 = _dollar_dollar.int_value
                        else:
                            _t529 = None
                        return _t529
                    _t530 = _t528(msg)
                    deconstruct_result26 = _t530
                    
                    if deconstruct_result26 is not None:
                        self.write(str(deconstruct_result26))
                        _t531 = None
                    else:
                        def _t532(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('float_value'):
                                _t533 = _dollar_dollar.float_value
                            else:
                                _t533 = None
                            return _t533
                        _t534 = _t532(msg)
                        deconstruct_result25 = _t534
                        
                        if deconstruct_result25 is not None:
                            self.write(str(deconstruct_result25))
                            _t535 = None
                        else:
                            def _t536(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('uint128_value'):
                                    _t537 = _dollar_dollar.uint128_value
                                else:
                                    _t537 = None
                                return _t537
                            _t538 = _t536(msg)
                            deconstruct_result24 = _t538
                            
                            if deconstruct_result24 is not None:
                                self.write(self.format_uint128(deconstruct_result24))
                                _t539 = None
                            else:
                                def _t540(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('int128_value'):
                                        _t541 = _dollar_dollar.int128_value
                                    else:
                                        _t541 = None
                                    return _t541
                                _t542 = _t540(msg)
                                deconstruct_result23 = _t542
                                
                                if deconstruct_result23 is not None:
                                    self.write(self.format_int128(deconstruct_result23))
                                    _t543 = None
                                else:
                                    def _t544(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('decimal_value'):
                                            _t545 = _dollar_dollar.decimal_value
                                        else:
                                            _t545 = None
                                        return _t545
                                    _t546 = _t544(msg)
                                    deconstruct_result22 = _t546
                                    
                                    if deconstruct_result22 is not None:
                                        self.write(self.format_decimal(deconstruct_result22))
                                        _t547 = None
                                    else:
                                        def _t548(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('boolean_value'):
                                                _t549 = _dollar_dollar.boolean_value
                                            else:
                                                _t549 = None
                                            return _t549
                                        _t550 = _t548(msg)
                                        deconstruct_result21 = _t550
                                        
                                        if deconstruct_result21 is not None:
                                            _t552 = self.pretty_boolean_value(deconstruct_result21)
                                            _t551 = _t552
                                        else:
                                            def _t553(_dollar_dollar):
                                                return _dollar_dollar
                                            _t554 = _t553(msg)
                                            fields19 = _t554
                                            assert fields19 is not None
                                            unwrapped_fields20 = fields19
                                            self.write('missing')
                                            _t551 = None
                                        _t547 = _t551
                                    _t543 = _t547
                                _t539 = _t543
                            _t535 = _t539
                        _t531 = _t535
                    _t527 = _t531
                _t522 = _t527
            _t517 = _t522
        return _t517

    def pretty_date(self, msg: logic_pb2.DateValue) -> Optional[NoReturn]:
        def _t555(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
        _t556 = _t555(msg)
        fields30 = _t556
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

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue) -> Optional[NoReturn]:
        def _t557(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
        _t558 = _t557(msg)
        fields35 = _t558
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

    def pretty_boolean_value(self, msg: bool) -> Optional[NoReturn]:
        def _t559(_dollar_dollar):
            
            if _dollar_dollar:
                _t560 = ()
            else:
                _t560 = None
            return _t560
        _t561 = _t559(msg)
        deconstruct_result46 = _t561
        if deconstruct_result46 is not None:
            self.write('true')
        else:
            def _t562(_dollar_dollar):
                
                if not _dollar_dollar:
                    _t563 = ()
                else:
                    _t563 = None
                return _t563
            _t564 = _t562(msg)
            deconstruct_result45 = _t564
            if deconstruct_result45 is not None:
                self.write('false')
            else:
                raise ParseError('No matching rule for boolean_value')
        return None

    def pretty_sync(self, msg: transactions_pb2.Sync) -> Optional[NoReturn]:
        def _t565(_dollar_dollar):
            return _dollar_dollar.fragments
        _t566 = _t565(msg)
        fields47 = _t566
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
                _t567 = self.pretty_fragment_id(elem49)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[NoReturn]:
        def _t568(_dollar_dollar):
            return self.fragment_id_to_string(_dollar_dollar)
        _t569 = _t568(msg)
        fields51 = _t569
        assert fields51 is not None
        unwrapped_fields52 = fields51
        self.write(':')
        self.write(unwrapped_fields52)
        return None

    def pretty_epoch(self, msg: transactions_pb2.Epoch) -> Optional[NoReturn]:
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
        fields53 = _t573
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
            _t575 = self.pretty_epoch_writes(opt_val56)
            _t574 = _t575
        else:
            _t574 = None
        field57 = unwrapped_fields54[1]
        
        if field57 is not None:
            self.newline()
            assert field57 is not None
            opt_val58 = field57
            _t577 = self.pretty_epoch_reads(opt_val58)
            _t576 = _t577
        else:
            _t576 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]) -> Optional[NoReturn]:
        def _t578(_dollar_dollar):
            return _dollar_dollar
        _t579 = _t578(msg)
        fields59 = _t579
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
                _t580 = self.pretty_write(elem61)
        self.dedent()
        self.write(')')
        return None

    def pretty_write(self, msg: transactions_pb2.Write) -> Optional[NoReturn]:
        def _t581(_dollar_dollar):
            
            if _dollar_dollar.HasField('define'):
                _t582 = _dollar_dollar.define
            else:
                _t582 = None
            return _t582
        _t583 = _t581(msg)
        deconstruct_result66 = _t583
        
        if deconstruct_result66 is not None:
            _t585 = self.pretty_define(deconstruct_result66)
            _t584 = _t585
        else:
            def _t586(_dollar_dollar):
                
                if _dollar_dollar.HasField('undefine'):
                    _t587 = _dollar_dollar.undefine
                else:
                    _t587 = None
                return _t587
            _t588 = _t586(msg)
            deconstruct_result65 = _t588
            
            if deconstruct_result65 is not None:
                _t590 = self.pretty_undefine(deconstruct_result65)
                _t589 = _t590
            else:
                def _t591(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('context'):
                        _t592 = _dollar_dollar.context
                    else:
                        _t592 = None
                    return _t592
                _t593 = _t591(msg)
                deconstruct_result64 = _t593
                
                if deconstruct_result64 is not None:
                    _t595 = self.pretty_context(deconstruct_result64)
                    _t594 = _t595
                else:
                    def _t596(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('snapshot'):
                            _t597 = _dollar_dollar.snapshot
                        else:
                            _t597 = None
                        return _t597
                    _t598 = _t596(msg)
                    deconstruct_result63 = _t598
                    
                    if deconstruct_result63 is not None:
                        _t600 = self.pretty_snapshot(deconstruct_result63)
                        _t599 = _t600
                    else:
                        raise ParseError('No matching rule for write')
                    _t594 = _t599
                _t589 = _t594
            _t584 = _t589
        return _t584

    def pretty_define(self, msg: transactions_pb2.Define) -> Optional[NoReturn]:
        def _t601(_dollar_dollar):
            return _dollar_dollar.fragment
        _t602 = _t601(msg)
        fields67 = _t602
        assert fields67 is not None
        unwrapped_fields68 = fields67
        self.write('(')
        self.write('define')
        self.indent()
        self.newline()
        _t603 = self.pretty_fragment(unwrapped_fields68)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> Optional[NoReturn]:
        def _t604(_dollar_dollar):
            _t605 = self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t606 = _t604(msg)
        fields69 = _t606
        assert fields69 is not None
        unwrapped_fields70 = fields69
        self.write('(')
        self.write('fragment')
        self.indent()
        self.newline()
        field71 = unwrapped_fields70[0]
        _t607 = self.pretty_new_fragment_id(field71)
        field72 = unwrapped_fields70[1]
        if not len(field72) == 0:
            self.newline()
            for i74, elem73 in enumerate(field72):
                if (i74 > 0):
                    self.newline()
                _t608 = self.pretty_declaration(elem73)
        self.dedent()
        self.write(')')
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[NoReturn]:
        def _t609(_dollar_dollar):
            return _dollar_dollar
        _t610 = _t609(msg)
        fields75 = _t610
        assert fields75 is not None
        unwrapped_fields76 = fields75
        _t611 = self.pretty_fragment_id(unwrapped_fields76)
        return _t611

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> Optional[NoReturn]:
        def _t612(_dollar_dollar):
            
            if _dollar_dollar.HasField('def'):
                _t613 = getattr(_dollar_dollar, 'def')
            else:
                _t613 = None
            return _t613
        _t614 = _t612(msg)
        deconstruct_result80 = _t614
        
        if deconstruct_result80 is not None:
            _t616 = self.pretty_def(deconstruct_result80)
            _t615 = _t616
        else:
            def _t617(_dollar_dollar):
                
                if _dollar_dollar.HasField('algorithm'):
                    _t618 = _dollar_dollar.algorithm
                else:
                    _t618 = None
                return _t618
            _t619 = _t617(msg)
            deconstruct_result79 = _t619
            
            if deconstruct_result79 is not None:
                _t621 = self.pretty_algorithm(deconstruct_result79)
                _t620 = _t621
            else:
                def _t622(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('constraint'):
                        _t623 = _dollar_dollar.constraint
                    else:
                        _t623 = None
                    return _t623
                _t624 = _t622(msg)
                deconstruct_result78 = _t624
                
                if deconstruct_result78 is not None:
                    _t626 = self.pretty_constraint(deconstruct_result78)
                    _t625 = _t626
                else:
                    def _t627(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('data'):
                            _t628 = _dollar_dollar.data
                        else:
                            _t628 = None
                        return _t628
                    _t629 = _t627(msg)
                    deconstruct_result77 = _t629
                    
                    if deconstruct_result77 is not None:
                        _t631 = self.pretty_data(deconstruct_result77)
                        _t630 = _t631
                    else:
                        raise ParseError('No matching rule for declaration')
                    _t625 = _t630
                _t620 = _t625
            _t615 = _t620
        return _t615

    def pretty_def(self, msg: logic_pb2.Def) -> Optional[NoReturn]:
        def _t632(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t633 = _dollar_dollar.attrs
            else:
                _t633 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t633,)
        _t634 = _t632(msg)
        fields81 = _t634
        assert fields81 is not None
        unwrapped_fields82 = fields81
        self.write('(')
        self.write('def')
        self.indent()
        self.newline()
        field83 = unwrapped_fields82[0]
        _t635 = self.pretty_relation_id(field83)
        self.newline()
        field84 = unwrapped_fields82[1]
        _t636 = self.pretty_abstraction(field84)
        field85 = unwrapped_fields82[2]
        
        if field85 is not None:
            self.newline()
            assert field85 is not None
            opt_val86 = field85
            _t638 = self.pretty_attrs(opt_val86)
            _t637 = _t638
        else:
            _t637 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> Optional[NoReturn]:
        def _t639(_dollar_dollar):
            _t640 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t640
        _t641 = _t639(msg)
        deconstruct_result88 = _t641
        if deconstruct_result88 is not None:
            self.write(':')
            self.write(deconstruct_result88)
        else:
            def _t642(_dollar_dollar):
                _t643 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t643
            _t644 = _t642(msg)
            deconstruct_result87 = _t644
            if deconstruct_result87 is not None:
                self.write(self.format_uint128(deconstruct_result87))
            else:
                raise ParseError('No matching rule for relation_id')
        return None

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> Optional[NoReturn]:
        def _t645(_dollar_dollar):
            _t646 = self.deconstruct_bindings(_dollar_dollar)
            return (_t646, _dollar_dollar.value,)
        _t647 = _t645(msg)
        fields89 = _t647
        assert fields89 is not None
        unwrapped_fields90 = fields89
        self.write('(')
        field91 = unwrapped_fields90[0]
        _t648 = self.pretty_bindings(field91)
        self.write(' ')
        field92 = unwrapped_fields90[1]
        _t649 = self.pretty_formula(field92)
        self.write(')')
        return None

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]) -> Optional[NoReturn]:
        def _t650(_dollar_dollar):
            
            if not len(_dollar_dollar[1]) == 0:
                _t651 = _dollar_dollar[1]
            else:
                _t651 = None
            return (_dollar_dollar[0], _t651,)
        _t652 = _t650(msg)
        fields93 = _t652
        assert fields93 is not None
        unwrapped_fields94 = fields93
        self.write('[')
        field95 = unwrapped_fields94[0]
        for i97, elem96 in enumerate(field95):
            if (i97 > 0):
                self.newline()
            _t653 = self.pretty_binding(elem96)
        field98 = unwrapped_fields94[1]
        
        if field98 is not None:
            self.write(' ')
            assert field98 is not None
            opt_val99 = field98
            _t655 = self.pretty_value_bindings(opt_val99)
            _t654 = _t655
        else:
            _t654 = None
        self.write(']')
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> Optional[NoReturn]:
        def _t656(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t657 = _t656(msg)
        fields100 = _t657
        assert fields100 is not None
        unwrapped_fields101 = fields100
        field102 = unwrapped_fields101[0]
        self.write(field102)
        self.write('::')
        field103 = unwrapped_fields101[1]
        _t658 = self.pretty_type(field103)
        return _t658

    def pretty_type(self, msg: logic_pb2.Type) -> Optional[NoReturn]:
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

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> Optional[NoReturn]:
        def _t714(_dollar_dollar):
            return _dollar_dollar
        _t715 = _t714(msg)
        fields115 = _t715
        assert fields115 is not None
        unwrapped_fields116 = fields115
        self.write('UNKNOWN')
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> Optional[NoReturn]:
        def _t716(_dollar_dollar):
            return _dollar_dollar
        _t717 = _t716(msg)
        fields117 = _t717
        assert fields117 is not None
        unwrapped_fields118 = fields117
        self.write('STRING')
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> Optional[NoReturn]:
        def _t718(_dollar_dollar):
            return _dollar_dollar
        _t719 = _t718(msg)
        fields119 = _t719
        assert fields119 is not None
        unwrapped_fields120 = fields119
        self.write('INT')
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> Optional[NoReturn]:
        def _t720(_dollar_dollar):
            return _dollar_dollar
        _t721 = _t720(msg)
        fields121 = _t721
        assert fields121 is not None
        unwrapped_fields122 = fields121
        self.write('FLOAT')
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> Optional[NoReturn]:
        def _t722(_dollar_dollar):
            return _dollar_dollar
        _t723 = _t722(msg)
        fields123 = _t723
        assert fields123 is not None
        unwrapped_fields124 = fields123
        self.write('UINT128')
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> Optional[NoReturn]:
        def _t724(_dollar_dollar):
            return _dollar_dollar
        _t725 = _t724(msg)
        fields125 = _t725
        assert fields125 is not None
        unwrapped_fields126 = fields125
        self.write('INT128')
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> Optional[NoReturn]:
        def _t726(_dollar_dollar):
            return _dollar_dollar
        _t727 = _t726(msg)
        fields127 = _t727
        assert fields127 is not None
        unwrapped_fields128 = fields127
        self.write('DATE')
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> Optional[NoReturn]:
        def _t728(_dollar_dollar):
            return _dollar_dollar
        _t729 = _t728(msg)
        fields129 = _t729
        assert fields129 is not None
        unwrapped_fields130 = fields129
        self.write('DATETIME')
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> Optional[NoReturn]:
        def _t730(_dollar_dollar):
            return _dollar_dollar
        _t731 = _t730(msg)
        fields131 = _t731
        assert fields131 is not None
        unwrapped_fields132 = fields131
        self.write('MISSING')
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> Optional[NoReturn]:
        def _t732(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t733 = _t732(msg)
        fields133 = _t733
        assert fields133 is not None
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

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType) -> Optional[NoReturn]:
        def _t734(_dollar_dollar):
            return _dollar_dollar
        _t735 = _t734(msg)
        fields137 = _t735
        assert fields137 is not None
        unwrapped_fields138 = fields137
        self.write('BOOLEAN')
        return None

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]) -> Optional[NoReturn]:
        def _t736(_dollar_dollar):
            return _dollar_dollar
        _t737 = _t736(msg)
        fields139 = _t737
        assert fields139 is not None
        unwrapped_fields140 = fields139
        self.write('|')
        if not len(unwrapped_fields140) == 0:
            self.write(' ')
            for i142, elem141 in enumerate(unwrapped_fields140):
                if (i142 > 0):
                    self.newline()
                _t738 = self.pretty_binding(elem141)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> Optional[NoReturn]:
        def _t739(_dollar_dollar):
            
            if (_dollar_dollar.HasField('conjunction') and len(_dollar_dollar.conjunction.args) == 0):
                _t740 = _dollar_dollar.conjunction
            else:
                _t740 = None
            return _t740
        _t741 = _t739(msg)
        deconstruct_result155 = _t741
        
        if deconstruct_result155 is not None:
            _t743 = self.pretty_true(deconstruct_result155)
            _t742 = _t743
        else:
            def _t744(_dollar_dollar):
                
                if (_dollar_dollar.HasField('disjunction') and len(_dollar_dollar.disjunction.args) == 0):
                    _t745 = _dollar_dollar.disjunction
                else:
                    _t745 = None
                return _t745
            _t746 = _t744(msg)
            deconstruct_result154 = _t746
            
            if deconstruct_result154 is not None:
                _t748 = self.pretty_false(deconstruct_result154)
                _t747 = _t748
            else:
                def _t749(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('exists'):
                        _t750 = _dollar_dollar.exists
                    else:
                        _t750 = None
                    return _t750
                _t751 = _t749(msg)
                deconstruct_result153 = _t751
                
                if deconstruct_result153 is not None:
                    _t753 = self.pretty_exists(deconstruct_result153)
                    _t752 = _t753
                else:
                    def _t754(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('reduce'):
                            _t755 = _dollar_dollar.reduce
                        else:
                            _t755 = None
                        return _t755
                    _t756 = _t754(msg)
                    deconstruct_result152 = _t756
                    
                    if deconstruct_result152 is not None:
                        _t758 = self.pretty_reduce(deconstruct_result152)
                        _t757 = _t758
                    else:
                        def _t759(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('conjunction'):
                                _t760 = _dollar_dollar.conjunction
                            else:
                                _t760 = None
                            return _t760
                        _t761 = _t759(msg)
                        deconstruct_result151 = _t761
                        
                        if deconstruct_result151 is not None:
                            _t763 = self.pretty_conjunction(deconstruct_result151)
                            _t762 = _t763
                        else:
                            def _t764(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('disjunction'):
                                    _t765 = _dollar_dollar.disjunction
                                else:
                                    _t765 = None
                                return _t765
                            _t766 = _t764(msg)
                            deconstruct_result150 = _t766
                            
                            if deconstruct_result150 is not None:
                                _t768 = self.pretty_disjunction(deconstruct_result150)
                                _t767 = _t768
                            else:
                                def _t769(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('not'):
                                        _t770 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t770 = None
                                    return _t770
                                _t771 = _t769(msg)
                                deconstruct_result149 = _t771
                                
                                if deconstruct_result149 is not None:
                                    _t773 = self.pretty_not(deconstruct_result149)
                                    _t772 = _t773
                                else:
                                    def _t774(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('ffi'):
                                            _t775 = _dollar_dollar.ffi
                                        else:
                                            _t775 = None
                                        return _t775
                                    _t776 = _t774(msg)
                                    deconstruct_result148 = _t776
                                    
                                    if deconstruct_result148 is not None:
                                        _t778 = self.pretty_ffi(deconstruct_result148)
                                        _t777 = _t778
                                    else:
                                        def _t779(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('atom'):
                                                _t780 = _dollar_dollar.atom
                                            else:
                                                _t780 = None
                                            return _t780
                                        _t781 = _t779(msg)
                                        deconstruct_result147 = _t781
                                        
                                        if deconstruct_result147 is not None:
                                            _t783 = self.pretty_atom(deconstruct_result147)
                                            _t782 = _t783
                                        else:
                                            def _t784(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('pragma'):
                                                    _t785 = _dollar_dollar.pragma
                                                else:
                                                    _t785 = None
                                                return _t785
                                            _t786 = _t784(msg)
                                            deconstruct_result146 = _t786
                                            
                                            if deconstruct_result146 is not None:
                                                _t788 = self.pretty_pragma(deconstruct_result146)
                                                _t787 = _t788
                                            else:
                                                def _t789(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('primitive'):
                                                        _t790 = _dollar_dollar.primitive
                                                    else:
                                                        _t790 = None
                                                    return _t790
                                                _t791 = _t789(msg)
                                                deconstruct_result145 = _t791
                                                
                                                if deconstruct_result145 is not None:
                                                    _t793 = self.pretty_primitive(deconstruct_result145)
                                                    _t792 = _t793
                                                else:
                                                    def _t794(_dollar_dollar):
                                                        
                                                        if _dollar_dollar.HasField('rel_atom'):
                                                            _t795 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t795 = None
                                                        return _t795
                                                    _t796 = _t794(msg)
                                                    deconstruct_result144 = _t796
                                                    
                                                    if deconstruct_result144 is not None:
                                                        _t798 = self.pretty_rel_atom(deconstruct_result144)
                                                        _t797 = _t798
                                                    else:
                                                        def _t799(_dollar_dollar):
                                                            
                                                            if _dollar_dollar.HasField('cast'):
                                                                _t800 = _dollar_dollar.cast
                                                            else:
                                                                _t800 = None
                                                            return _t800
                                                        _t801 = _t799(msg)
                                                        deconstruct_result143 = _t801
                                                        
                                                        if deconstruct_result143 is not None:
                                                            _t803 = self.pretty_cast(deconstruct_result143)
                                                            _t802 = _t803
                                                        else:
                                                            raise ParseError('No matching rule for formula')
                                                        _t797 = _t802
                                                    _t792 = _t797
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
        return _t742

    def pretty_true(self, msg: logic_pb2.Conjunction) -> Optional[NoReturn]:
        def _t804(_dollar_dollar):
            return _dollar_dollar
        _t805 = _t804(msg)
        fields156 = _t805
        assert fields156 is not None
        unwrapped_fields157 = fields156
        self.write('(')
        self.write('true')
        self.write(')')
        return None

    def pretty_false(self, msg: logic_pb2.Disjunction) -> Optional[NoReturn]:
        def _t806(_dollar_dollar):
            return _dollar_dollar
        _t807 = _t806(msg)
        fields158 = _t807
        assert fields158 is not None
        unwrapped_fields159 = fields158
        self.write('(')
        self.write('false')
        self.write(')')
        return None

    def pretty_exists(self, msg: logic_pb2.Exists) -> Optional[NoReturn]:
        def _t808(_dollar_dollar):
            _t809 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t809, _dollar_dollar.body.value,)
        _t810 = _t808(msg)
        fields160 = _t810
        assert fields160 is not None
        unwrapped_fields161 = fields160
        self.write('(')
        self.write('exists')
        self.indent()
        self.newline()
        field162 = unwrapped_fields161[0]
        _t811 = self.pretty_bindings(field162)
        self.newline()
        field163 = unwrapped_fields161[1]
        _t812 = self.pretty_formula(field163)
        self.dedent()
        self.write(')')
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> Optional[NoReturn]:
        def _t813(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t814 = _t813(msg)
        fields164 = _t814
        assert fields164 is not None
        unwrapped_fields165 = fields164
        self.write('(')
        self.write('reduce')
        self.indent()
        self.newline()
        field166 = unwrapped_fields165[0]
        _t815 = self.pretty_abstraction(field166)
        self.newline()
        field167 = unwrapped_fields165[1]
        _t816 = self.pretty_abstraction(field167)
        self.newline()
        field168 = unwrapped_fields165[2]
        _t817 = self.pretty_terms(field168)
        self.dedent()
        self.write(')')
        return None

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]) -> Optional[NoReturn]:
        def _t818(_dollar_dollar):
            return _dollar_dollar
        _t819 = _t818(msg)
        fields169 = _t819
        assert fields169 is not None
        unwrapped_fields170 = fields169
        self.write('(')
        self.write('terms')
        self.indent()
        if not len(unwrapped_fields170) == 0:
            self.newline()
            for i172, elem171 in enumerate(unwrapped_fields170):
                if (i172 > 0):
                    self.newline()
                _t820 = self.pretty_term(elem171)
        self.dedent()
        self.write(')')
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> Optional[NoReturn]:
        def _t821(_dollar_dollar):
            
            if _dollar_dollar.HasField('var'):
                _t822 = _dollar_dollar.var
            else:
                _t822 = None
            return _t822
        _t823 = _t821(msg)
        deconstruct_result174 = _t823
        
        if deconstruct_result174 is not None:
            _t825 = self.pretty_var(deconstruct_result174)
            _t824 = _t825
        else:
            def _t826(_dollar_dollar):
                
                if _dollar_dollar.HasField('constant'):
                    _t827 = _dollar_dollar.constant
                else:
                    _t827 = None
                return _t827
            _t828 = _t826(msg)
            deconstruct_result173 = _t828
            
            if deconstruct_result173 is not None:
                _t830 = self.pretty_constant(deconstruct_result173)
                _t829 = _t830
            else:
                raise ParseError('No matching rule for term')
            _t824 = _t829
        return _t824

    def pretty_var(self, msg: logic_pb2.Var) -> Optional[NoReturn]:
        def _t831(_dollar_dollar):
            return _dollar_dollar.name
        _t832 = _t831(msg)
        fields175 = _t832
        assert fields175 is not None
        unwrapped_fields176 = fields175
        self.write(unwrapped_fields176)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> Optional[NoReturn]:
        def _t833(_dollar_dollar):
            return _dollar_dollar
        _t834 = _t833(msg)
        fields177 = _t834
        assert fields177 is not None
        unwrapped_fields178 = fields177
        _t835 = self.pretty_value(unwrapped_fields178)
        return _t835

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> Optional[NoReturn]:
        def _t836(_dollar_dollar):
            return _dollar_dollar.args
        _t837 = _t836(msg)
        fields179 = _t837
        assert fields179 is not None
        unwrapped_fields180 = fields179
        self.write('(')
        self.write('and')
        self.indent()
        if not len(unwrapped_fields180) == 0:
            self.newline()
            for i182, elem181 in enumerate(unwrapped_fields180):
                if (i182 > 0):
                    self.newline()
                _t838 = self.pretty_formula(elem181)
        self.dedent()
        self.write(')')
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> Optional[NoReturn]:
        def _t839(_dollar_dollar):
            return _dollar_dollar.args
        _t840 = _t839(msg)
        fields183 = _t840
        assert fields183 is not None
        unwrapped_fields184 = fields183
        self.write('(')
        self.write('or')
        self.indent()
        if not len(unwrapped_fields184) == 0:
            self.newline()
            for i186, elem185 in enumerate(unwrapped_fields184):
                if (i186 > 0):
                    self.newline()
                _t841 = self.pretty_formula(elem185)
        self.dedent()
        self.write(')')
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> Optional[NoReturn]:
        def _t842(_dollar_dollar):
            return _dollar_dollar.arg
        _t843 = _t842(msg)
        fields187 = _t843
        assert fields187 is not None
        unwrapped_fields188 = fields187
        self.write('(')
        self.write('not')
        self.indent()
        self.newline()
        _t844 = self.pretty_formula(unwrapped_fields188)
        self.dedent()
        self.write(')')
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> Optional[NoReturn]:
        def _t845(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t846 = _t845(msg)
        fields189 = _t846
        assert fields189 is not None
        unwrapped_fields190 = fields189
        self.write('(')
        self.write('ffi')
        self.indent()
        self.newline()
        field191 = unwrapped_fields190[0]
        _t847 = self.pretty_name(field191)
        self.newline()
        field192 = unwrapped_fields190[1]
        _t848 = self.pretty_ffi_args(field192)
        self.newline()
        field193 = unwrapped_fields190[2]
        _t849 = self.pretty_terms(field193)
        self.dedent()
        self.write(')')
        return None

    def pretty_name(self, msg: str) -> Optional[NoReturn]:
        def _t850(_dollar_dollar):
            return _dollar_dollar
        _t851 = _t850(msg)
        fields194 = _t851
        assert fields194 is not None
        unwrapped_fields195 = fields194
        self.write(':')
        self.write(unwrapped_fields195)
        return None

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]) -> Optional[NoReturn]:
        def _t852(_dollar_dollar):
            return _dollar_dollar
        _t853 = _t852(msg)
        fields196 = _t853
        assert fields196 is not None
        unwrapped_fields197 = fields196
        self.write('(')
        self.write('args')
        self.indent()
        if not len(unwrapped_fields197) == 0:
            self.newline()
            for i199, elem198 in enumerate(unwrapped_fields197):
                if (i199 > 0):
                    self.newline()
                _t854 = self.pretty_abstraction(elem198)
        self.dedent()
        self.write(')')
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> Optional[NoReturn]:
        def _t855(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t856 = _t855(msg)
        fields200 = _t856
        assert fields200 is not None
        unwrapped_fields201 = fields200
        self.write('(')
        self.write('atom')
        self.indent()
        self.newline()
        field202 = unwrapped_fields201[0]
        _t857 = self.pretty_relation_id(field202)
        field203 = unwrapped_fields201[1]
        if not len(field203) == 0:
            self.newline()
            for i205, elem204 in enumerate(field203):
                if (i205 > 0):
                    self.newline()
                _t858 = self.pretty_term(elem204)
        self.dedent()
        self.write(')')
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> Optional[NoReturn]:
        def _t859(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t860 = _t859(msg)
        fields206 = _t860
        assert fields206 is not None
        unwrapped_fields207 = fields206
        self.write('(')
        self.write('pragma')
        self.indent()
        self.newline()
        field208 = unwrapped_fields207[0]
        _t861 = self.pretty_name(field208)
        field209 = unwrapped_fields207[1]
        if not len(field209) == 0:
            self.newline()
            for i211, elem210 in enumerate(field209):
                if (i211 > 0):
                    self.newline()
                _t862 = self.pretty_term(elem210)
        self.dedent()
        self.write(')')
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t863(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t864 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t864 = None
            return _t864
        _t865 = _t863(msg)
        guard_result226 = _t865
        
        if guard_result226 is not None:
            _t867 = self.pretty_eq(msg)
            _t866 = _t867
        else:
            def _t868(_dollar_dollar):
                
                if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                    _t869 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t869 = None
                return _t869
            _t870 = _t868(msg)
            guard_result225 = _t870
            
            if guard_result225 is not None:
                _t872 = self.pretty_lt(msg)
                _t871 = _t872
            else:
                def _t873(_dollar_dollar):
                    
                    if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                        _t874 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t874 = None
                    return _t874
                _t875 = _t873(msg)
                guard_result224 = _t875
                
                if guard_result224 is not None:
                    _t877 = self.pretty_lt_eq(msg)
                    _t876 = _t877
                else:
                    def _t878(_dollar_dollar):
                        
                        if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                            _t879 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t879 = None
                        return _t879
                    _t880 = _t878(msg)
                    guard_result223 = _t880
                    
                    if guard_result223 is not None:
                        _t882 = self.pretty_gt(msg)
                        _t881 = _t882
                    else:
                        def _t883(_dollar_dollar):
                            
                            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                                _t884 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t884 = None
                            return _t884
                        _t885 = _t883(msg)
                        guard_result222 = _t885
                        
                        if guard_result222 is not None:
                            _t887 = self.pretty_gt_eq(msg)
                            _t886 = _t887
                        else:
                            def _t888(_dollar_dollar):
                                
                                if _dollar_dollar.name == 'rel_primitive_add_monotype':
                                    _t889 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t889 = None
                                return _t889
                            _t890 = _t888(msg)
                            guard_result221 = _t890
                            
                            if guard_result221 is not None:
                                _t892 = self.pretty_add(msg)
                                _t891 = _t892
                            else:
                                def _t893(_dollar_dollar):
                                    
                                    if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                                        _t894 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t894 = None
                                    return _t894
                                _t895 = _t893(msg)
                                guard_result220 = _t895
                                
                                if guard_result220 is not None:
                                    _t897 = self.pretty_minus(msg)
                                    _t896 = _t897
                                else:
                                    def _t898(_dollar_dollar):
                                        
                                        if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                                            _t899 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t899 = None
                                        return _t899
                                    _t900 = _t898(msg)
                                    guard_result219 = _t900
                                    
                                    if guard_result219 is not None:
                                        _t902 = self.pretty_multiply(msg)
                                        _t901 = _t902
                                    else:
                                        def _t903(_dollar_dollar):
                                            
                                            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                                                _t904 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t904 = None
                                            return _t904
                                        _t905 = _t903(msg)
                                        guard_result218 = _t905
                                        
                                        if guard_result218 is not None:
                                            _t907 = self.pretty_divide(msg)
                                            _t906 = _t907
                                        else:
                                            def _t908(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t909 = _t908(msg)
                                            fields212 = _t909
                                            assert fields212 is not None
                                            unwrapped_fields213 = fields212
                                            self.write('(')
                                            self.write('primitive')
                                            self.indent()
                                            self.newline()
                                            field214 = unwrapped_fields213[0]
                                            _t910 = self.pretty_name(field214)
                                            field215 = unwrapped_fields213[1]
                                            if not len(field215) == 0:
                                                self.newline()
                                                for i217, elem216 in enumerate(field215):
                                                    if (i217 > 0):
                                                        self.newline()
                                                    _t911 = self.pretty_rel_term(elem216)
                                            self.dedent()
                                            self.write(')')
                                            _t906 = None
                                        _t901 = _t906
                                    _t896 = _t901
                                _t891 = _t896
                            _t886 = _t891
                        _t881 = _t886
                    _t876 = _t881
                _t871 = _t876
            _t866 = _t871
        return _t866

    def pretty_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t912(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t913 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t913 = None
            return _t913
        _t914 = _t912(msg)
        fields227 = _t914
        assert fields227 is not None
        unwrapped_fields228 = fields227
        self.write('(')
        self.write('=')
        self.indent()
        self.newline()
        field229 = unwrapped_fields228[0]
        _t915 = self.pretty_term(field229)
        self.newline()
        field230 = unwrapped_fields228[1]
        _t916 = self.pretty_term(field230)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t917(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                _t918 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t918 = None
            return _t918
        _t919 = _t917(msg)
        fields231 = _t919
        assert fields231 is not None
        unwrapped_fields232 = fields231
        self.write('(')
        self.write('<')
        self.indent()
        self.newline()
        field233 = unwrapped_fields232[0]
        _t920 = self.pretty_term(field233)
        self.newline()
        field234 = unwrapped_fields232[1]
        _t921 = self.pretty_term(field234)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t922(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                _t923 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t923 = None
            return _t923
        _t924 = _t922(msg)
        fields235 = _t924
        assert fields235 is not None
        unwrapped_fields236 = fields235
        self.write('(')
        self.write('<=')
        self.indent()
        self.newline()
        field237 = unwrapped_fields236[0]
        _t925 = self.pretty_term(field237)
        self.newline()
        field238 = unwrapped_fields236[1]
        _t926 = self.pretty_term(field238)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t927(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                _t928 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t928 = None
            return _t928
        _t929 = _t927(msg)
        fields239 = _t929
        assert fields239 is not None
        unwrapped_fields240 = fields239
        self.write('(')
        self.write('>')
        self.indent()
        self.newline()
        field241 = unwrapped_fields240[0]
        _t930 = self.pretty_term(field241)
        self.newline()
        field242 = unwrapped_fields240[1]
        _t931 = self.pretty_term(field242)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t932(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                _t933 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t933 = None
            return _t933
        _t934 = _t932(msg)
        fields243 = _t934
        assert fields243 is not None
        unwrapped_fields244 = fields243
        self.write('(')
        self.write('>=')
        self.indent()
        self.newline()
        field245 = unwrapped_fields244[0]
        _t935 = self.pretty_term(field245)
        self.newline()
        field246 = unwrapped_fields244[1]
        _t936 = self.pretty_term(field246)
        self.dedent()
        self.write(')')
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t937(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_add_monotype':
                _t938 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t938 = None
            return _t938
        _t939 = _t937(msg)
        fields247 = _t939
        assert fields247 is not None
        unwrapped_fields248 = fields247
        self.write('(')
        self.write('+')
        self.indent()
        self.newline()
        field249 = unwrapped_fields248[0]
        _t940 = self.pretty_term(field249)
        self.newline()
        field250 = unwrapped_fields248[1]
        _t941 = self.pretty_term(field250)
        self.newline()
        field251 = unwrapped_fields248[2]
        _t942 = self.pretty_term(field251)
        self.dedent()
        self.write(')')
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t943(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                _t944 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t944 = None
            return _t944
        _t945 = _t943(msg)
        fields252 = _t945
        assert fields252 is not None
        unwrapped_fields253 = fields252
        self.write('(')
        self.write('-')
        self.indent()
        self.newline()
        field254 = unwrapped_fields253[0]
        _t946 = self.pretty_term(field254)
        self.newline()
        field255 = unwrapped_fields253[1]
        _t947 = self.pretty_term(field255)
        self.newline()
        field256 = unwrapped_fields253[2]
        _t948 = self.pretty_term(field256)
        self.dedent()
        self.write(')')
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t949(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                _t950 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t950 = None
            return _t950
        _t951 = _t949(msg)
        fields257 = _t951
        assert fields257 is not None
        unwrapped_fields258 = fields257
        self.write('(')
        self.write('*')
        self.indent()
        self.newline()
        field259 = unwrapped_fields258[0]
        _t952 = self.pretty_term(field259)
        self.newline()
        field260 = unwrapped_fields258[1]
        _t953 = self.pretty_term(field260)
        self.newline()
        field261 = unwrapped_fields258[2]
        _t954 = self.pretty_term(field261)
        self.dedent()
        self.write(')')
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t955(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                _t956 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t956 = None
            return _t956
        _t957 = _t955(msg)
        fields262 = _t957
        assert fields262 is not None
        unwrapped_fields263 = fields262
        self.write('(')
        self.write('/')
        self.indent()
        self.newline()
        field264 = unwrapped_fields263[0]
        _t958 = self.pretty_term(field264)
        self.newline()
        field265 = unwrapped_fields263[1]
        _t959 = self.pretty_term(field265)
        self.newline()
        field266 = unwrapped_fields263[2]
        _t960 = self.pretty_term(field266)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> Optional[NoReturn]:
        def _t961(_dollar_dollar):
            
            if _dollar_dollar.HasField('specialized_value'):
                _t962 = _dollar_dollar.specialized_value
            else:
                _t962 = None
            return _t962
        _t963 = _t961(msg)
        deconstruct_result268 = _t963
        
        if deconstruct_result268 is not None:
            _t965 = self.pretty_specialized_value(deconstruct_result268)
            _t964 = _t965
        else:
            def _t966(_dollar_dollar):
                
                if _dollar_dollar.HasField('term'):
                    _t967 = _dollar_dollar.term
                else:
                    _t967 = None
                return _t967
            _t968 = _t966(msg)
            deconstruct_result267 = _t968
            
            if deconstruct_result267 is not None:
                _t970 = self.pretty_term(deconstruct_result267)
                _t969 = _t970
            else:
                raise ParseError('No matching rule for rel_term')
            _t964 = _t969
        return _t964

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> Optional[NoReturn]:
        def _t971(_dollar_dollar):
            return _dollar_dollar
        _t972 = _t971(msg)
        fields269 = _t972
        assert fields269 is not None
        unwrapped_fields270 = fields269
        self.write('#')
        _t973 = self.pretty_value(unwrapped_fields270)
        return _t973

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> Optional[NoReturn]:
        def _t974(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t975 = _t974(msg)
        fields271 = _t975
        assert fields271 is not None
        unwrapped_fields272 = fields271
        self.write('(')
        self.write('relatom')
        self.indent()
        self.newline()
        field273 = unwrapped_fields272[0]
        _t976 = self.pretty_name(field273)
        field274 = unwrapped_fields272[1]
        if not len(field274) == 0:
            self.newline()
            for i276, elem275 in enumerate(field274):
                if (i276 > 0):
                    self.newline()
                _t977 = self.pretty_rel_term(elem275)
        self.dedent()
        self.write(')')
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> Optional[NoReturn]:
        def _t978(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t979 = _t978(msg)
        fields277 = _t979
        assert fields277 is not None
        unwrapped_fields278 = fields277
        self.write('(')
        self.write('cast')
        self.indent()
        self.newline()
        field279 = unwrapped_fields278[0]
        _t980 = self.pretty_term(field279)
        self.newline()
        field280 = unwrapped_fields278[1]
        _t981 = self.pretty_term(field280)
        self.dedent()
        self.write(')')
        return None

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]) -> Optional[NoReturn]:
        def _t982(_dollar_dollar):
            return _dollar_dollar
        _t983 = _t982(msg)
        fields281 = _t983
        assert fields281 is not None
        unwrapped_fields282 = fields281
        self.write('(')
        self.write('attrs')
        self.indent()
        if not len(unwrapped_fields282) == 0:
            self.newline()
            for i284, elem283 in enumerate(unwrapped_fields282):
                if (i284 > 0):
                    self.newline()
                _t984 = self.pretty_attribute(elem283)
        self.dedent()
        self.write(')')
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> Optional[NoReturn]:
        def _t985(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t986 = _t985(msg)
        fields285 = _t986
        assert fields285 is not None
        unwrapped_fields286 = fields285
        self.write('(')
        self.write('attribute')
        self.indent()
        self.newline()
        field287 = unwrapped_fields286[0]
        _t987 = self.pretty_name(field287)
        field288 = unwrapped_fields286[1]
        if not len(field288) == 0:
            self.newline()
            for i290, elem289 in enumerate(field288):
                if (i290 > 0):
                    self.newline()
                _t988 = self.pretty_value(elem289)
        self.dedent()
        self.write(')')
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> Optional[NoReturn]:
        def _t989(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t990 = _t989(msg)
        fields291 = _t990
        assert fields291 is not None
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
                _t991 = self.pretty_relation_id(elem294)
        self.newline()
        field296 = unwrapped_fields292[1]
        _t992 = self.pretty_script(field296)
        self.dedent()
        self.write(')')
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> Optional[NoReturn]:
        def _t993(_dollar_dollar):
            return _dollar_dollar.constructs
        _t994 = _t993(msg)
        fields297 = _t994
        assert fields297 is not None
        unwrapped_fields298 = fields297
        self.write('(')
        self.write('script')
        self.indent()
        if not len(unwrapped_fields298) == 0:
            self.newline()
            for i300, elem299 in enumerate(unwrapped_fields298):
                if (i300 > 0):
                    self.newline()
                _t995 = self.pretty_construct(elem299)
        self.dedent()
        self.write(')')
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> Optional[NoReturn]:
        def _t996(_dollar_dollar):
            
            if _dollar_dollar.HasField('loop'):
                _t997 = _dollar_dollar.loop
            else:
                _t997 = None
            return _t997
        _t998 = _t996(msg)
        deconstruct_result302 = _t998
        
        if deconstruct_result302 is not None:
            _t1000 = self.pretty_loop(deconstruct_result302)
            _t999 = _t1000
        else:
            def _t1001(_dollar_dollar):
                
                if _dollar_dollar.HasField('instruction'):
                    _t1002 = _dollar_dollar.instruction
                else:
                    _t1002 = None
                return _t1002
            _t1003 = _t1001(msg)
            deconstruct_result301 = _t1003
            
            if deconstruct_result301 is not None:
                _t1005 = self.pretty_instruction(deconstruct_result301)
                _t1004 = _t1005
            else:
                raise ParseError('No matching rule for construct')
            _t999 = _t1004
        return _t999

    def pretty_loop(self, msg: logic_pb2.Loop) -> Optional[NoReturn]:
        def _t1006(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t1007 = _t1006(msg)
        fields303 = _t1007
        assert fields303 is not None
        unwrapped_fields304 = fields303
        self.write('(')
        self.write('loop')
        self.indent()
        self.newline()
        field305 = unwrapped_fields304[0]
        _t1008 = self.pretty_init(field305)
        self.newline()
        field306 = unwrapped_fields304[1]
        _t1009 = self.pretty_script(field306)
        self.dedent()
        self.write(')')
        return None

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]) -> Optional[NoReturn]:
        def _t1010(_dollar_dollar):
            return _dollar_dollar
        _t1011 = _t1010(msg)
        fields307 = _t1011
        assert fields307 is not None
        unwrapped_fields308 = fields307
        self.write('(')
        self.write('init')
        self.indent()
        if not len(unwrapped_fields308) == 0:
            self.newline()
            for i310, elem309 in enumerate(unwrapped_fields308):
                if (i310 > 0):
                    self.newline()
                _t1012 = self.pretty_instruction(elem309)
        self.dedent()
        self.write(')')
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> Optional[NoReturn]:
        def _t1013(_dollar_dollar):
            
            if _dollar_dollar.HasField('assign'):
                _t1014 = _dollar_dollar.assign
            else:
                _t1014 = None
            return _t1014
        _t1015 = _t1013(msg)
        deconstruct_result315 = _t1015
        
        if deconstruct_result315 is not None:
            _t1017 = self.pretty_assign(deconstruct_result315)
            _t1016 = _t1017
        else:
            def _t1018(_dollar_dollar):
                
                if _dollar_dollar.HasField('upsert'):
                    _t1019 = _dollar_dollar.upsert
                else:
                    _t1019 = None
                return _t1019
            _t1020 = _t1018(msg)
            deconstruct_result314 = _t1020
            
            if deconstruct_result314 is not None:
                _t1022 = self.pretty_upsert(deconstruct_result314)
                _t1021 = _t1022
            else:
                def _t1023(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('break'):
                        _t1024 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1024 = None
                    return _t1024
                _t1025 = _t1023(msg)
                deconstruct_result313 = _t1025
                
                if deconstruct_result313 is not None:
                    _t1027 = self.pretty_break(deconstruct_result313)
                    _t1026 = _t1027
                else:
                    def _t1028(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('monoid_def'):
                            _t1029 = _dollar_dollar.monoid_def
                        else:
                            _t1029 = None
                        return _t1029
                    _t1030 = _t1028(msg)
                    deconstruct_result312 = _t1030
                    
                    if deconstruct_result312 is not None:
                        _t1032 = self.pretty_monoid_def(deconstruct_result312)
                        _t1031 = _t1032
                    else:
                        def _t1033(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('monus_def'):
                                _t1034 = _dollar_dollar.monus_def
                            else:
                                _t1034 = None
                            return _t1034
                        _t1035 = _t1033(msg)
                        deconstruct_result311 = _t1035
                        
                        if deconstruct_result311 is not None:
                            _t1037 = self.pretty_monus_def(deconstruct_result311)
                            _t1036 = _t1037
                        else:
                            raise ParseError('No matching rule for instruction')
                        _t1031 = _t1036
                    _t1026 = _t1031
                _t1021 = _t1026
            _t1016 = _t1021
        return _t1016

    def pretty_assign(self, msg: logic_pb2.Assign) -> Optional[NoReturn]:
        def _t1038(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1039 = _dollar_dollar.attrs
            else:
                _t1039 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1039,)
        _t1040 = _t1038(msg)
        fields316 = _t1040
        assert fields316 is not None
        unwrapped_fields317 = fields316
        self.write('(')
        self.write('assign')
        self.indent()
        self.newline()
        field318 = unwrapped_fields317[0]
        _t1041 = self.pretty_relation_id(field318)
        self.newline()
        field319 = unwrapped_fields317[1]
        _t1042 = self.pretty_abstraction(field319)
        field320 = unwrapped_fields317[2]
        
        if field320 is not None:
            self.newline()
            assert field320 is not None
            opt_val321 = field320
            _t1044 = self.pretty_attrs(opt_val321)
            _t1043 = _t1044
        else:
            _t1043 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> Optional[NoReturn]:
        def _t1045(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1046 = _dollar_dollar.attrs
            else:
                _t1046 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1046,)
        _t1047 = _t1045(msg)
        fields322 = _t1047
        assert fields322 is not None
        unwrapped_fields323 = fields322
        self.write('(')
        self.write('upsert')
        self.indent()
        self.newline()
        field324 = unwrapped_fields323[0]
        _t1048 = self.pretty_relation_id(field324)
        self.newline()
        field325 = unwrapped_fields323[1]
        _t1049 = self.pretty_abstraction_with_arity(field325)
        field326 = unwrapped_fields323[2]
        
        if field326 is not None:
            self.newline()
            assert field326 is not None
            opt_val327 = field326
            _t1051 = self.pretty_attrs(opt_val327)
            _t1050 = _t1051
        else:
            _t1050 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> Optional[NoReturn]:
        def _t1052(_dollar_dollar):
            _t1053 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1053, _dollar_dollar[0].value,)
        _t1054 = _t1052(msg)
        fields328 = _t1054
        assert fields328 is not None
        unwrapped_fields329 = fields328
        self.write('(')
        field330 = unwrapped_fields329[0]
        _t1055 = self.pretty_bindings(field330)
        self.write(' ')
        field331 = unwrapped_fields329[1]
        _t1056 = self.pretty_formula(field331)
        self.write(')')
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> Optional[NoReturn]:
        def _t1057(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1058 = _dollar_dollar.attrs
            else:
                _t1058 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1058,)
        _t1059 = _t1057(msg)
        fields332 = _t1059
        assert fields332 is not None
        unwrapped_fields333 = fields332
        self.write('(')
        self.write('break')
        self.indent()
        self.newline()
        field334 = unwrapped_fields333[0]
        _t1060 = self.pretty_relation_id(field334)
        self.newline()
        field335 = unwrapped_fields333[1]
        _t1061 = self.pretty_abstraction(field335)
        field336 = unwrapped_fields333[2]
        
        if field336 is not None:
            self.newline()
            assert field336 is not None
            opt_val337 = field336
            _t1063 = self.pretty_attrs(opt_val337)
            _t1062 = _t1063
        else:
            _t1062 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> Optional[NoReturn]:
        def _t1064(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1065 = _dollar_dollar.attrs
            else:
                _t1065 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1065,)
        _t1066 = _t1064(msg)
        fields338 = _t1066
        assert fields338 is not None
        unwrapped_fields339 = fields338
        self.write('(')
        self.write('monoid')
        self.indent()
        self.newline()
        field340 = unwrapped_fields339[0]
        _t1067 = self.pretty_monoid(field340)
        self.newline()
        field341 = unwrapped_fields339[1]
        _t1068 = self.pretty_relation_id(field341)
        self.newline()
        field342 = unwrapped_fields339[2]
        _t1069 = self.pretty_abstraction_with_arity(field342)
        field343 = unwrapped_fields339[3]
        
        if field343 is not None:
            self.newline()
            assert field343 is not None
            opt_val344 = field343
            _t1071 = self.pretty_attrs(opt_val344)
            _t1070 = _t1071
        else:
            _t1070 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> Optional[NoReturn]:
        def _t1072(_dollar_dollar):
            
            if _dollar_dollar.HasField('or_monoid'):
                _t1073 = _dollar_dollar.or_monoid
            else:
                _t1073 = None
            return _t1073
        _t1074 = _t1072(msg)
        deconstruct_result348 = _t1074
        
        if deconstruct_result348 is not None:
            _t1076 = self.pretty_or_monoid(deconstruct_result348)
            _t1075 = _t1076
        else:
            def _t1077(_dollar_dollar):
                
                if _dollar_dollar.HasField('min_monoid'):
                    _t1078 = _dollar_dollar.min_monoid
                else:
                    _t1078 = None
                return _t1078
            _t1079 = _t1077(msg)
            deconstruct_result347 = _t1079
            
            if deconstruct_result347 is not None:
                _t1081 = self.pretty_min_monoid(deconstruct_result347)
                _t1080 = _t1081
            else:
                def _t1082(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('max_monoid'):
                        _t1083 = _dollar_dollar.max_monoid
                    else:
                        _t1083 = None
                    return _t1083
                _t1084 = _t1082(msg)
                deconstruct_result346 = _t1084
                
                if deconstruct_result346 is not None:
                    _t1086 = self.pretty_max_monoid(deconstruct_result346)
                    _t1085 = _t1086
                else:
                    def _t1087(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('sum_monoid'):
                            _t1088 = _dollar_dollar.sum_monoid
                        else:
                            _t1088 = None
                        return _t1088
                    _t1089 = _t1087(msg)
                    deconstruct_result345 = _t1089
                    
                    if deconstruct_result345 is not None:
                        _t1091 = self.pretty_sum_monoid(deconstruct_result345)
                        _t1090 = _t1091
                    else:
                        raise ParseError('No matching rule for monoid')
                    _t1085 = _t1090
                _t1080 = _t1085
            _t1075 = _t1080
        return _t1075

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> Optional[NoReturn]:
        def _t1092(_dollar_dollar):
            return _dollar_dollar
        _t1093 = _t1092(msg)
        fields349 = _t1093
        assert fields349 is not None
        unwrapped_fields350 = fields349
        self.write('(')
        self.write('or')
        self.write(')')
        return None

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid) -> Optional[NoReturn]:
        def _t1094(_dollar_dollar):
            return _dollar_dollar.type
        _t1095 = _t1094(msg)
        fields351 = _t1095
        assert fields351 is not None
        unwrapped_fields352 = fields351
        self.write('(')
        self.write('min')
        self.indent()
        self.newline()
        _t1096 = self.pretty_type(unwrapped_fields352)
        self.dedent()
        self.write(')')
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> Optional[NoReturn]:
        def _t1097(_dollar_dollar):
            return _dollar_dollar.type
        _t1098 = _t1097(msg)
        fields353 = _t1098
        assert fields353 is not None
        unwrapped_fields354 = fields353
        self.write('(')
        self.write('max')
        self.indent()
        self.newline()
        _t1099 = self.pretty_type(unwrapped_fields354)
        self.dedent()
        self.write(')')
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> Optional[NoReturn]:
        def _t1100(_dollar_dollar):
            return _dollar_dollar.type
        _t1101 = _t1100(msg)
        fields355 = _t1101
        assert fields355 is not None
        unwrapped_fields356 = fields355
        self.write('(')
        self.write('sum')
        self.indent()
        self.newline()
        _t1102 = self.pretty_type(unwrapped_fields356)
        self.dedent()
        self.write(')')
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> Optional[NoReturn]:
        def _t1103(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1104 = _dollar_dollar.attrs
            else:
                _t1104 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1104,)
        _t1105 = _t1103(msg)
        fields357 = _t1105
        assert fields357 is not None
        unwrapped_fields358 = fields357
        self.write('(')
        self.write('monus')
        self.indent()
        self.newline()
        field359 = unwrapped_fields358[0]
        _t1106 = self.pretty_monoid(field359)
        self.newline()
        field360 = unwrapped_fields358[1]
        _t1107 = self.pretty_relation_id(field360)
        self.newline()
        field361 = unwrapped_fields358[2]
        _t1108 = self.pretty_abstraction_with_arity(field361)
        field362 = unwrapped_fields358[3]
        
        if field362 is not None:
            self.newline()
            assert field362 is not None
            opt_val363 = field362
            _t1110 = self.pretty_attrs(opt_val363)
            _t1109 = _t1110
        else:
            _t1109 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> Optional[NoReturn]:
        def _t1111(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1112 = _t1111(msg)
        fields364 = _t1112
        assert fields364 is not None
        unwrapped_fields365 = fields364
        self.write('(')
        self.write('functional_dependency')
        self.indent()
        self.newline()
        field366 = unwrapped_fields365[0]
        _t1113 = self.pretty_relation_id(field366)
        self.newline()
        field367 = unwrapped_fields365[1]
        _t1114 = self.pretty_abstraction(field367)
        self.newline()
        field368 = unwrapped_fields365[2]
        _t1115 = self.pretty_functional_dependency_keys(field368)
        self.newline()
        field369 = unwrapped_fields365[3]
        _t1116 = self.pretty_functional_dependency_values(field369)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]) -> Optional[NoReturn]:
        def _t1117(_dollar_dollar):
            return _dollar_dollar
        _t1118 = _t1117(msg)
        fields370 = _t1118
        assert fields370 is not None
        unwrapped_fields371 = fields370
        self.write('(')
        self.write('keys')
        self.indent()
        if not len(unwrapped_fields371) == 0:
            self.newline()
            for i373, elem372 in enumerate(unwrapped_fields371):
                if (i373 > 0):
                    self.newline()
                _t1119 = self.pretty_var(elem372)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]) -> Optional[NoReturn]:
        def _t1120(_dollar_dollar):
            return _dollar_dollar
        _t1121 = _t1120(msg)
        fields374 = _t1121
        assert fields374 is not None
        unwrapped_fields375 = fields374
        self.write('(')
        self.write('values')
        self.indent()
        if not len(unwrapped_fields375) == 0:
            self.newline()
            for i377, elem376 in enumerate(unwrapped_fields375):
                if (i377 > 0):
                    self.newline()
                _t1122 = self.pretty_var(elem376)
        self.dedent()
        self.write(')')
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> Optional[NoReturn]:
        def _t1123(_dollar_dollar):
            
            if _dollar_dollar.HasField('rel_edb'):
                _t1124 = _dollar_dollar.rel_edb
            else:
                _t1124 = None
            return _t1124
        _t1125 = _t1123(msg)
        deconstruct_result380 = _t1125
        
        if deconstruct_result380 is not None:
            _t1127 = self.pretty_rel_edb(deconstruct_result380)
            _t1126 = _t1127
        else:
            def _t1128(_dollar_dollar):
                
                if _dollar_dollar.HasField('betree_relation'):
                    _t1129 = _dollar_dollar.betree_relation
                else:
                    _t1129 = None
                return _t1129
            _t1130 = _t1128(msg)
            deconstruct_result379 = _t1130
            
            if deconstruct_result379 is not None:
                _t1132 = self.pretty_betree_relation(deconstruct_result379)
                _t1131 = _t1132
            else:
                def _t1133(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('csv_data'):
                        _t1134 = _dollar_dollar.csv_data
                    else:
                        _t1134 = None
                    return _t1134
                _t1135 = _t1133(msg)
                deconstruct_result378 = _t1135
                
                if deconstruct_result378 is not None:
                    _t1137 = self.pretty_csv_data(deconstruct_result378)
                    _t1136 = _t1137
                else:
                    raise ParseError('No matching rule for data')
                _t1131 = _t1136
            _t1126 = _t1131
        return _t1126

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> Optional[NoReturn]:
        def _t1138(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1139 = _t1138(msg)
        fields381 = _t1139
        assert fields381 is not None
        unwrapped_fields382 = fields381
        self.write('(')
        self.write('rel_edb')
        self.indent()
        self.newline()
        field383 = unwrapped_fields382[0]
        _t1140 = self.pretty_relation_id(field383)
        self.newline()
        field384 = unwrapped_fields382[1]
        _t1141 = self.pretty_rel_edb_path(field384)
        self.newline()
        field385 = unwrapped_fields382[2]
        _t1142 = self.pretty_rel_edb_types(field385)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_edb_path(self, msg: Sequence[str]) -> Optional[NoReturn]:
        def _t1143(_dollar_dollar):
            return _dollar_dollar
        _t1144 = _t1143(msg)
        fields386 = _t1144
        assert fields386 is not None
        unwrapped_fields387 = fields386
        self.write('[')
        for i389, elem388 in enumerate(unwrapped_fields387):
            if (i389 > 0):
                self.newline()
            self.write(self.format_string_value(elem388))
        self.write(']')
        return None

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[NoReturn]:
        def _t1145(_dollar_dollar):
            return _dollar_dollar
        _t1146 = _t1145(msg)
        fields390 = _t1146
        assert fields390 is not None
        unwrapped_fields391 = fields390
        self.write('[')
        for i393, elem392 in enumerate(unwrapped_fields391):
            if (i393 > 0):
                self.newline()
            _t1147 = self.pretty_type(elem392)
        self.write(']')
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> Optional[NoReturn]:
        def _t1148(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1149 = _t1148(msg)
        fields394 = _t1149
        assert fields394 is not None
        unwrapped_fields395 = fields394
        self.write('(')
        self.write('betree_relation')
        self.indent()
        self.newline()
        field396 = unwrapped_fields395[0]
        _t1150 = self.pretty_relation_id(field396)
        self.newline()
        field397 = unwrapped_fields395[1]
        _t1151 = self.pretty_betree_info(field397)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> Optional[NoReturn]:
        def _t1152(_dollar_dollar):
            _t1153 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1153,)
        _t1154 = _t1152(msg)
        fields398 = _t1154
        assert fields398 is not None
        unwrapped_fields399 = fields398
        self.write('(')
        self.write('betree_info')
        self.indent()
        self.newline()
        field400 = unwrapped_fields399[0]
        _t1155 = self.pretty_betree_info_key_types(field400)
        self.newline()
        field401 = unwrapped_fields399[1]
        _t1156 = self.pretty_betree_info_value_types(field401)
        self.newline()
        field402 = unwrapped_fields399[2]
        _t1157 = self.pretty_config_dict(field402)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[NoReturn]:
        def _t1158(_dollar_dollar):
            return _dollar_dollar
        _t1159 = _t1158(msg)
        fields403 = _t1159
        assert fields403 is not None
        unwrapped_fields404 = fields403
        self.write('(')
        self.write('key_types')
        self.indent()
        if not len(unwrapped_fields404) == 0:
            self.newline()
            for i406, elem405 in enumerate(unwrapped_fields404):
                if (i406 > 0):
                    self.newline()
                _t1160 = self.pretty_type(elem405)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[NoReturn]:
        def _t1161(_dollar_dollar):
            return _dollar_dollar
        _t1162 = _t1161(msg)
        fields407 = _t1162
        assert fields407 is not None
        unwrapped_fields408 = fields407
        self.write('(')
        self.write('value_types')
        self.indent()
        if not len(unwrapped_fields408) == 0:
            self.newline()
            for i410, elem409 in enumerate(unwrapped_fields408):
                if (i410 > 0):
                    self.newline()
                _t1163 = self.pretty_type(elem409)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> Optional[NoReturn]:
        def _t1164(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1165 = _t1164(msg)
        fields411 = _t1165
        assert fields411 is not None
        unwrapped_fields412 = fields411
        self.write('(')
        self.write('csv_data')
        self.indent()
        self.newline()
        field413 = unwrapped_fields412[0]
        _t1166 = self.pretty_csvlocator(field413)
        self.newline()
        field414 = unwrapped_fields412[1]
        _t1167 = self.pretty_csv_config(field414)
        self.newline()
        field415 = unwrapped_fields412[2]
        _t1168 = self.pretty_csv_columns(field415)
        self.newline()
        field416 = unwrapped_fields412[3]
        _t1169 = self.pretty_csv_asof(field416)
        self.dedent()
        self.write(')')
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> Optional[NoReturn]:
        def _t1170(_dollar_dollar):
            
            if not len(_dollar_dollar.paths) == 0:
                _t1171 = _dollar_dollar.paths
            else:
                _t1171 = None
            
            if _dollar_dollar.inline_data.decode('utf-8') != '':
                _t1172 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1172 = None
            return (_t1171, _t1172,)
        _t1173 = _t1170(msg)
        fields417 = _t1173
        assert fields417 is not None
        unwrapped_fields418 = fields417
        self.write('(')
        self.write('csv_locator')
        self.indent()
        field419 = unwrapped_fields418[0]
        
        if field419 is not None:
            self.newline()
            assert field419 is not None
            opt_val420 = field419
            _t1175 = self.pretty_csv_locator_paths(opt_val420)
            _t1174 = _t1175
        else:
            _t1174 = None
        field421 = unwrapped_fields418[1]
        
        if field421 is not None:
            self.newline()
            assert field421 is not None
            opt_val422 = field421
            _t1177 = self.pretty_csv_locator_inline_data(opt_val422)
            _t1176 = _t1177
        else:
            _t1176 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_locator_paths(self, msg: Sequence[str]) -> Optional[NoReturn]:
        def _t1178(_dollar_dollar):
            return _dollar_dollar
        _t1179 = _t1178(msg)
        fields423 = _t1179
        assert fields423 is not None
        unwrapped_fields424 = fields423
        self.write('(')
        self.write('paths')
        self.indent()
        if not len(unwrapped_fields424) == 0:
            self.newline()
            for i426, elem425 in enumerate(unwrapped_fields424):
                if (i426 > 0):
                    self.newline()
                self.write(self.format_string_value(elem425))
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_locator_inline_data(self, msg: str) -> Optional[NoReturn]:
        def _t1180(_dollar_dollar):
            return _dollar_dollar
        _t1181 = _t1180(msg)
        fields427 = _t1181
        assert fields427 is not None
        unwrapped_fields428 = fields427
        self.write('(')
        self.write('inline_data')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields428))
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig) -> Optional[NoReturn]:
        def _t1182(_dollar_dollar):
            _t1183 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1183
        _t1184 = _t1182(msg)
        fields429 = _t1184
        assert fields429 is not None
        unwrapped_fields430 = fields429
        self.write('(')
        self.write('csv_config')
        self.indent()
        self.newline()
        _t1185 = self.pretty_config_dict(unwrapped_fields430)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]) -> Optional[NoReturn]:
        def _t1186(_dollar_dollar):
            return _dollar_dollar
        _t1187 = _t1186(msg)
        fields431 = _t1187
        assert fields431 is not None
        unwrapped_fields432 = fields431
        self.write('(')
        self.write('columns')
        self.indent()
        if not len(unwrapped_fields432) == 0:
            self.newline()
            for i434, elem433 in enumerate(unwrapped_fields432):
                if (i434 > 0):
                    self.newline()
                _t1188 = self.pretty_csv_column(elem433)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> Optional[NoReturn]:
        def _t1189(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1190 = _t1189(msg)
        fields435 = _t1190
        assert fields435 is not None
        unwrapped_fields436 = fields435
        self.write('(')
        self.write('column')
        self.indent()
        self.newline()
        field437 = unwrapped_fields436[0]
        self.write(self.format_string_value(field437))
        self.newline()
        field438 = unwrapped_fields436[1]
        _t1191 = self.pretty_relation_id(field438)
        self.newline()
        self.write('[')
        field439 = unwrapped_fields436[2]
        for i441, elem440 in enumerate(field439):
            if (i441 > 0):
                self.newline()
            _t1192 = self.pretty_type(elem440)
        self.write(']')
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_asof(self, msg: str) -> Optional[NoReturn]:
        def _t1193(_dollar_dollar):
            return _dollar_dollar
        _t1194 = _t1193(msg)
        fields442 = _t1194
        assert fields442 is not None
        unwrapped_fields443 = fields442
        self.write('(')
        self.write('asof')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields443))
        self.dedent()
        self.write(')')
        return None

    def pretty_undefine(self, msg: transactions_pb2.Undefine) -> Optional[NoReturn]:
        def _t1195(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1196 = _t1195(msg)
        fields444 = _t1196
        assert fields444 is not None
        unwrapped_fields445 = fields444
        self.write('(')
        self.write('undefine')
        self.indent()
        self.newline()
        _t1197 = self.pretty_fragment_id(unwrapped_fields445)
        self.dedent()
        self.write(')')
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> Optional[NoReturn]:
        def _t1198(_dollar_dollar):
            return _dollar_dollar.relations
        _t1199 = _t1198(msg)
        fields446 = _t1199
        assert fields446 is not None
        unwrapped_fields447 = fields446
        self.write('(')
        self.write('context')
        self.indent()
        if not len(unwrapped_fields447) == 0:
            self.newline()
            for i449, elem448 in enumerate(unwrapped_fields447):
                if (i449 > 0):
                    self.newline()
                _t1200 = self.pretty_relation_id(elem448)
        self.dedent()
        self.write(')')
        return None

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot) -> Optional[NoReturn]:
        def _t1201(_dollar_dollar):
            return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
        _t1202 = _t1201(msg)
        fields450 = _t1202
        assert fields450 is not None
        unwrapped_fields451 = fields450
        self.write('(')
        self.write('snapshot')
        self.indent()
        self.newline()
        field452 = unwrapped_fields451[0]
        _t1203 = self.pretty_rel_edb_path(field452)
        self.newline()
        field453 = unwrapped_fields451[1]
        _t1204 = self.pretty_relation_id(field453)
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]) -> Optional[NoReturn]:
        def _t1205(_dollar_dollar):
            return _dollar_dollar
        _t1206 = _t1205(msg)
        fields454 = _t1206
        assert fields454 is not None
        unwrapped_fields455 = fields454
        self.write('(')
        self.write('reads')
        self.indent()
        if not len(unwrapped_fields455) == 0:
            self.newline()
            for i457, elem456 in enumerate(unwrapped_fields455):
                if (i457 > 0):
                    self.newline()
                _t1207 = self.pretty_read(elem456)
        self.dedent()
        self.write(')')
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> Optional[NoReturn]:
        def _t1208(_dollar_dollar):
            
            if _dollar_dollar.HasField('demand'):
                _t1209 = _dollar_dollar.demand
            else:
                _t1209 = None
            return _t1209
        _t1210 = _t1208(msg)
        deconstruct_result462 = _t1210
        
        if deconstruct_result462 is not None:
            _t1212 = self.pretty_demand(deconstruct_result462)
            _t1211 = _t1212
        else:
            def _t1213(_dollar_dollar):
                
                if _dollar_dollar.HasField('output'):
                    _t1214 = _dollar_dollar.output
                else:
                    _t1214 = None
                return _t1214
            _t1215 = _t1213(msg)
            deconstruct_result461 = _t1215
            
            if deconstruct_result461 is not None:
                _t1217 = self.pretty_output(deconstruct_result461)
                _t1216 = _t1217
            else:
                def _t1218(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('what_if'):
                        _t1219 = _dollar_dollar.what_if
                    else:
                        _t1219 = None
                    return _t1219
                _t1220 = _t1218(msg)
                deconstruct_result460 = _t1220
                
                if deconstruct_result460 is not None:
                    _t1222 = self.pretty_what_if(deconstruct_result460)
                    _t1221 = _t1222
                else:
                    def _t1223(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('abort'):
                            _t1224 = _dollar_dollar.abort
                        else:
                            _t1224 = None
                        return _t1224
                    _t1225 = _t1223(msg)
                    deconstruct_result459 = _t1225
                    
                    if deconstruct_result459 is not None:
                        _t1227 = self.pretty_abort(deconstruct_result459)
                        _t1226 = _t1227
                    else:
                        def _t1228(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('export'):
                                _t1229 = _dollar_dollar.export
                            else:
                                _t1229 = None
                            return _t1229
                        _t1230 = _t1228(msg)
                        deconstruct_result458 = _t1230
                        
                        if deconstruct_result458 is not None:
                            _t1232 = self.pretty_export(deconstruct_result458)
                            _t1231 = _t1232
                        else:
                            raise ParseError('No matching rule for read')
                        _t1226 = _t1231
                    _t1221 = _t1226
                _t1216 = _t1221
            _t1211 = _t1216
        return _t1211

    def pretty_demand(self, msg: transactions_pb2.Demand) -> Optional[NoReturn]:
        def _t1233(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1234 = _t1233(msg)
        fields463 = _t1234
        assert fields463 is not None
        unwrapped_fields464 = fields463
        self.write('(')
        self.write('demand')
        self.indent()
        self.newline()
        _t1235 = self.pretty_relation_id(unwrapped_fields464)
        self.dedent()
        self.write(')')
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> Optional[NoReturn]:
        def _t1236(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        _t1237 = _t1236(msg)
        fields465 = _t1237
        assert fields465 is not None
        unwrapped_fields466 = fields465
        self.write('(')
        self.write('output')
        self.indent()
        self.newline()
        field467 = unwrapped_fields466[0]
        _t1238 = self.pretty_name(field467)
        self.newline()
        field468 = unwrapped_fields466[1]
        _t1239 = self.pretty_relation_id(field468)
        self.dedent()
        self.write(')')
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> Optional[NoReturn]:
        def _t1240(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1241 = _t1240(msg)
        fields469 = _t1241
        assert fields469 is not None
        unwrapped_fields470 = fields469
        self.write('(')
        self.write('what_if')
        self.indent()
        self.newline()
        field471 = unwrapped_fields470[0]
        _t1242 = self.pretty_name(field471)
        self.newline()
        field472 = unwrapped_fields470[1]
        _t1243 = self.pretty_epoch(field472)
        self.dedent()
        self.write(')')
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> Optional[NoReturn]:
        def _t1244(_dollar_dollar):
            
            if _dollar_dollar.name != 'abort':
                _t1245 = _dollar_dollar.name
            else:
                _t1245 = None
            return (_t1245, _dollar_dollar.relation_id,)
        _t1246 = _t1244(msg)
        fields473 = _t1246
        assert fields473 is not None
        unwrapped_fields474 = fields473
        self.write('(')
        self.write('abort')
        self.indent()
        field475 = unwrapped_fields474[0]
        
        if field475 is not None:
            self.newline()
            assert field475 is not None
            opt_val476 = field475
            _t1248 = self.pretty_name(opt_val476)
            _t1247 = _t1248
        else:
            _t1247 = None
        self.newline()
        field477 = unwrapped_fields474[1]
        _t1249 = self.pretty_relation_id(field477)
        self.dedent()
        self.write(')')
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> Optional[NoReturn]:
        def _t1250(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1251 = _t1250(msg)
        fields478 = _t1251
        assert fields478 is not None
        unwrapped_fields479 = fields478
        self.write('(')
        self.write('export')
        self.indent()
        self.newline()
        _t1252 = self.pretty_export_csv_config(unwrapped_fields479)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> Optional[NoReturn]:
        def _t1253(_dollar_dollar):
            _t1254 = self.deconstruct_export_csv_config(_dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1254,)
        _t1255 = _t1253(msg)
        fields480 = _t1255
        assert fields480 is not None
        unwrapped_fields481 = fields480
        self.write('(')
        self.write('export_csv_config')
        self.indent()
        self.newline()
        field482 = unwrapped_fields481[0]
        _t1256 = self.pretty_export_csv_path(field482)
        self.newline()
        field483 = unwrapped_fields481[1]
        _t1257 = self.pretty_export_csv_columns(field483)
        self.newline()
        field484 = unwrapped_fields481[2]
        _t1258 = self.pretty_config_dict(field484)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_path(self, msg: str) -> Optional[NoReturn]:
        def _t1259(_dollar_dollar):
            return _dollar_dollar
        _t1260 = _t1259(msg)
        fields485 = _t1260
        assert fields485 is not None
        unwrapped_fields486 = fields485
        self.write('(')
        self.write('path')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields486))
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]) -> Optional[NoReturn]:
        def _t1261(_dollar_dollar):
            return _dollar_dollar
        _t1262 = _t1261(msg)
        fields487 = _t1262
        assert fields487 is not None
        unwrapped_fields488 = fields487
        self.write('(')
        self.write('columns')
        self.indent()
        if not len(unwrapped_fields488) == 0:
            self.newline()
            for i490, elem489 in enumerate(unwrapped_fields488):
                if (i490 > 0):
                    self.newline()
                _t1263 = self.pretty_export_csv_column(elem489)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> Optional[NoReturn]:
        def _t1264(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1265 = _t1264(msg)
        fields491 = _t1265
        assert fields491 is not None
        unwrapped_fields492 = fields491
        self.write('(')
        self.write('column')
        self.indent()
        self.newline()
        field493 = unwrapped_fields492[0]
        self.write(self.format_string_value(field493))
        self.newline()
        field494 = unwrapped_fields492[1]
        _t1266 = self.pretty_relation_id(field494)
        self.dedent()
        self.write(')')
        return None


def pretty(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
