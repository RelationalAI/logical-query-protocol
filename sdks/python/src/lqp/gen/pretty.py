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

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1270 = self._make_value_string('auto')
            result.append(('ivm.maintenance_level', _t1270,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1271 = self._make_value_string('all')
                result.append(('ivm.maintenance_level', _t1271,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1272 = self._make_value_string('off')
                    result.append(('ivm.maintenance_level', _t1272,))
        _t1273 = self._make_value_int64(msg.semantics_version)
        result.append(('semantics_version', _t1273,))
        return sorted(result)

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1274 = logic_pb2.Value(int_value=v)
        return _t1274

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1275 = logic_pb2.Value(string_value=v)
        return _t1275

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1276 = logic_pb2.Value(boolean_value=v)
        return _t1276

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1277 = logic_pb2.Value(int_value=int(v))
        return _t1277

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1278 = logic_pb2.Value(uint128_value=v)
        return _t1278

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1279 = self._make_value_int64(msg.partition_size)
            result.append(('partition_size', _t1279,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1280 = self._make_value_string(msg.compression)
            result.append(('compression', _t1280,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1281 = self._make_value_boolean(msg.syntax_header_row)
            result.append(('syntax_header_row', _t1281,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1282 = self._make_value_string(msg.syntax_missing_string)
            result.append(('syntax_missing_string', _t1282,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1283 = self._make_value_string(msg.syntax_delim)
            result.append(('syntax_delim', _t1283,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1284 = self._make_value_string(msg.syntax_quotechar)
            result.append(('syntax_quotechar', _t1284,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1285 = self._make_value_string(msg.syntax_escapechar)
            result.append(('syntax_escapechar', _t1285,))
        return sorted(result)

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == '':
            return self.relation_id_to_uint128(msg)
        return None

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1286 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(('betree_config_epsilon', _t1286,))
        _t1287 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(('betree_config_max_pivots', _t1287,))
        _t1288 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(('betree_config_max_deltas', _t1288,))
        _t1289 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(('betree_config_max_leaf', _t1289,))
        if msg.relation_locator.HasField('root_pageid'):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1290 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(('betree_locator_root_pageid', _t1290,))
        if msg.relation_locator.HasField('inline_data'):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1291 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(('betree_locator_inline_data', _t1291,))
        _t1292 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(('betree_locator_element_count', _t1292,))
        _t1293 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(('betree_locator_tree_height', _t1293,))
        return sorted(result)

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1294 = logic_pb2.Value(float_value=v)
        return _t1294

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1295 = self._make_value_int32(msg.header_row)
        result.append(('csv_header_row', _t1295,))
        _t1296 = self._make_value_int64(msg.skip)
        result.append(('csv_skip', _t1296,))
        if msg.new_line != '':
            _t1297 = self._make_value_string(msg.new_line)
            result.append(('csv_new_line', _t1297,))
        _t1298 = self._make_value_string(msg.delimiter)
        result.append(('csv_delimiter', _t1298,))
        _t1299 = self._make_value_string(msg.quotechar)
        result.append(('csv_quotechar', _t1299,))
        _t1300 = self._make_value_string(msg.escapechar)
        result.append(('csv_escapechar', _t1300,))
        if msg.comment != '':
            _t1301 = self._make_value_string(msg.comment)
            result.append(('csv_comment', _t1301,))
        for missing_string in msg.missing_strings:
            _t1302 = self._make_value_string(missing_string)
            result.append(('csv_missing_strings', _t1302,))
        _t1303 = self._make_value_string(msg.decimal_separator)
        result.append(('csv_decimal_separator', _t1303,))
        _t1304 = self._make_value_string(msg.encoding)
        result.append(('csv_encoding', _t1304,))
        _t1305 = self._make_value_string(msg.compression)
        result.append(('csv_compression', _t1305,))
        if msg.partition_size_mb != 0:
            _t1306 = self._make_value_int64(msg.partition_size_mb)
            result.append(('csv_partition_size_mb', _t1306,))
        return sorted(result)

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        return (abs.vars[0:n], [],)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != '':
            return name
        return None

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
        deconstruct_result65 = _t583
        
        if deconstruct_result65 is not None:
            _t585 = self.pretty_define(deconstruct_result65)
            _t584 = _t585
        else:
            def _t586(_dollar_dollar):
                
                if _dollar_dollar.HasField('undefine'):
                    _t587 = _dollar_dollar.undefine
                else:
                    _t587 = None
                return _t587
            _t588 = _t586(msg)
            deconstruct_result64 = _t588
            
            if deconstruct_result64 is not None:
                _t590 = self.pretty_undefine(deconstruct_result64)
                _t589 = _t590
            else:
                def _t591(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('context'):
                        _t592 = _dollar_dollar.context
                    else:
                        _t592 = None
                    return _t592
                _t593 = _t591(msg)
                deconstruct_result63 = _t593
                
                if deconstruct_result63 is not None:
                    _t595 = self.pretty_context(deconstruct_result63)
                    _t594 = _t595
                else:
                    raise ParseError('No matching rule for write')
                _t589 = _t594
            _t584 = _t589
        return _t584

    def pretty_define(self, msg: transactions_pb2.Define) -> Optional[NoReturn]:
        def _t596(_dollar_dollar):
            return _dollar_dollar.fragment
        _t597 = _t596(msg)
        fields66 = _t597
        assert fields66 is not None
        unwrapped_fields67 = fields66
        self.write('(')
        self.write('define')
        self.indent()
        self.newline()
        _t598 = self.pretty_fragment(unwrapped_fields67)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> Optional[NoReturn]:
        def _t599(_dollar_dollar):
            _t600 = self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t601 = _t599(msg)
        fields68 = _t601
        assert fields68 is not None
        unwrapped_fields69 = fields68
        self.write('(')
        self.write('fragment')
        self.indent()
        self.newline()
        field70 = unwrapped_fields69[0]
        _t602 = self.pretty_new_fragment_id(field70)
        field71 = unwrapped_fields69[1]
        if not len(field71) == 0:
            self.newline()
            for i73, elem72 in enumerate(field71):
                if (i73 > 0):
                    self.newline()
                _t603 = self.pretty_declaration(elem72)
        self.dedent()
        self.write(')')
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[NoReturn]:
        def _t604(_dollar_dollar):
            return _dollar_dollar
        _t605 = _t604(msg)
        fields74 = _t605
        assert fields74 is not None
        unwrapped_fields75 = fields74
        _t606 = self.pretty_fragment_id(unwrapped_fields75)
        return _t606

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> Optional[NoReturn]:
        def _t607(_dollar_dollar):
            
            if _dollar_dollar.HasField('def'):
                _t608 = getattr(_dollar_dollar, 'def')
            else:
                _t608 = None
            return _t608
        _t609 = _t607(msg)
        deconstruct_result79 = _t609
        
        if deconstruct_result79 is not None:
            _t611 = self.pretty_def(deconstruct_result79)
            _t610 = _t611
        else:
            def _t612(_dollar_dollar):
                
                if _dollar_dollar.HasField('algorithm'):
                    _t613 = _dollar_dollar.algorithm
                else:
                    _t613 = None
                return _t613
            _t614 = _t612(msg)
            deconstruct_result78 = _t614
            
            if deconstruct_result78 is not None:
                _t616 = self.pretty_algorithm(deconstruct_result78)
                _t615 = _t616
            else:
                def _t617(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('constraint'):
                        _t618 = _dollar_dollar.constraint
                    else:
                        _t618 = None
                    return _t618
                _t619 = _t617(msg)
                deconstruct_result77 = _t619
                
                if deconstruct_result77 is not None:
                    _t621 = self.pretty_constraint(deconstruct_result77)
                    _t620 = _t621
                else:
                    def _t622(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('data'):
                            _t623 = _dollar_dollar.data
                        else:
                            _t623 = None
                        return _t623
                    _t624 = _t622(msg)
                    deconstruct_result76 = _t624
                    
                    if deconstruct_result76 is not None:
                        _t626 = self.pretty_data(deconstruct_result76)
                        _t625 = _t626
                    else:
                        raise ParseError('No matching rule for declaration')
                    _t620 = _t625
                _t615 = _t620
            _t610 = _t615
        return _t610

    def pretty_def(self, msg: logic_pb2.Def) -> Optional[NoReturn]:
        def _t627(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t628 = _dollar_dollar.attrs
            else:
                _t628 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t628,)
        _t629 = _t627(msg)
        fields80 = _t629
        assert fields80 is not None
        unwrapped_fields81 = fields80
        self.write('(')
        self.write('def')
        self.indent()
        self.newline()
        field82 = unwrapped_fields81[0]
        _t630 = self.pretty_relation_id(field82)
        self.newline()
        field83 = unwrapped_fields81[1]
        _t631 = self.pretty_abstraction(field83)
        field84 = unwrapped_fields81[2]
        
        if field84 is not None:
            self.newline()
            assert field84 is not None
            opt_val85 = field84
            _t633 = self.pretty_attrs(opt_val85)
            _t632 = _t633
        else:
            _t632 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> Optional[NoReturn]:
        def _t634(_dollar_dollar):
            _t635 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t635
        _t636 = _t634(msg)
        deconstruct_result87 = _t636
        if deconstruct_result87 is not None:
            self.write(':')
            self.write(deconstruct_result87)
        else:
            def _t637(_dollar_dollar):
                _t638 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t638
            _t639 = _t637(msg)
            deconstruct_result86 = _t639
            if deconstruct_result86 is not None:
                self.write(self.format_uint128(deconstruct_result86))
            else:
                raise ParseError('No matching rule for relation_id')
        return None

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> Optional[NoReturn]:
        def _t640(_dollar_dollar):
            _t641 = self.deconstruct_bindings(_dollar_dollar)
            return (_t641, _dollar_dollar.value,)
        _t642 = _t640(msg)
        fields88 = _t642
        assert fields88 is not None
        unwrapped_fields89 = fields88
        self.write('(')
        field90 = unwrapped_fields89[0]
        _t643 = self.pretty_bindings(field90)
        self.write(' ')
        field91 = unwrapped_fields89[1]
        _t644 = self.pretty_formula(field91)
        self.write(')')
        return None

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]) -> Optional[NoReturn]:
        def _t645(_dollar_dollar):
            
            if not len(_dollar_dollar[1]) == 0:
                _t646 = _dollar_dollar[1]
            else:
                _t646 = None
            return (_dollar_dollar[0], _t646,)
        _t647 = _t645(msg)
        fields92 = _t647
        assert fields92 is not None
        unwrapped_fields93 = fields92
        self.write('[')
        field94 = unwrapped_fields93[0]
        for i96, elem95 in enumerate(field94):
            if (i96 > 0):
                self.newline()
            _t648 = self.pretty_binding(elem95)
        field97 = unwrapped_fields93[1]
        
        if field97 is not None:
            self.write(' ')
            assert field97 is not None
            opt_val98 = field97
            _t650 = self.pretty_value_bindings(opt_val98)
            _t649 = _t650
        else:
            _t649 = None
        self.write(']')
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> Optional[NoReturn]:
        def _t651(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t652 = _t651(msg)
        fields99 = _t652
        assert fields99 is not None
        unwrapped_fields100 = fields99
        field101 = unwrapped_fields100[0]
        self.write(field101)
        self.write('::')
        field102 = unwrapped_fields100[1]
        _t653 = self.pretty_type(field102)
        return _t653

    def pretty_type(self, msg: logic_pb2.Type) -> Optional[NoReturn]:
        def _t654(_dollar_dollar):
            
            if _dollar_dollar.HasField('unspecified_type'):
                _t655 = _dollar_dollar.unspecified_type
            else:
                _t655 = None
            return _t655
        _t656 = _t654(msg)
        deconstruct_result113 = _t656
        
        if deconstruct_result113 is not None:
            _t658 = self.pretty_unspecified_type(deconstruct_result113)
            _t657 = _t658
        else:
            def _t659(_dollar_dollar):
                
                if _dollar_dollar.HasField('string_type'):
                    _t660 = _dollar_dollar.string_type
                else:
                    _t660 = None
                return _t660
            _t661 = _t659(msg)
            deconstruct_result112 = _t661
            
            if deconstruct_result112 is not None:
                _t663 = self.pretty_string_type(deconstruct_result112)
                _t662 = _t663
            else:
                def _t664(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('int_type'):
                        _t665 = _dollar_dollar.int_type
                    else:
                        _t665 = None
                    return _t665
                _t666 = _t664(msg)
                deconstruct_result111 = _t666
                
                if deconstruct_result111 is not None:
                    _t668 = self.pretty_int_type(deconstruct_result111)
                    _t667 = _t668
                else:
                    def _t669(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('float_type'):
                            _t670 = _dollar_dollar.float_type
                        else:
                            _t670 = None
                        return _t670
                    _t671 = _t669(msg)
                    deconstruct_result110 = _t671
                    
                    if deconstruct_result110 is not None:
                        _t673 = self.pretty_float_type(deconstruct_result110)
                        _t672 = _t673
                    else:
                        def _t674(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('uint128_type'):
                                _t675 = _dollar_dollar.uint128_type
                            else:
                                _t675 = None
                            return _t675
                        _t676 = _t674(msg)
                        deconstruct_result109 = _t676
                        
                        if deconstruct_result109 is not None:
                            _t678 = self.pretty_uint128_type(deconstruct_result109)
                            _t677 = _t678
                        else:
                            def _t679(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('int128_type'):
                                    _t680 = _dollar_dollar.int128_type
                                else:
                                    _t680 = None
                                return _t680
                            _t681 = _t679(msg)
                            deconstruct_result108 = _t681
                            
                            if deconstruct_result108 is not None:
                                _t683 = self.pretty_int128_type(deconstruct_result108)
                                _t682 = _t683
                            else:
                                def _t684(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('date_type'):
                                        _t685 = _dollar_dollar.date_type
                                    else:
                                        _t685 = None
                                    return _t685
                                _t686 = _t684(msg)
                                deconstruct_result107 = _t686
                                
                                if deconstruct_result107 is not None:
                                    _t688 = self.pretty_date_type(deconstruct_result107)
                                    _t687 = _t688
                                else:
                                    def _t689(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('datetime_type'):
                                            _t690 = _dollar_dollar.datetime_type
                                        else:
                                            _t690 = None
                                        return _t690
                                    _t691 = _t689(msg)
                                    deconstruct_result106 = _t691
                                    
                                    if deconstruct_result106 is not None:
                                        _t693 = self.pretty_datetime_type(deconstruct_result106)
                                        _t692 = _t693
                                    else:
                                        def _t694(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('missing_type'):
                                                _t695 = _dollar_dollar.missing_type
                                            else:
                                                _t695 = None
                                            return _t695
                                        _t696 = _t694(msg)
                                        deconstruct_result105 = _t696
                                        
                                        if deconstruct_result105 is not None:
                                            _t698 = self.pretty_missing_type(deconstruct_result105)
                                            _t697 = _t698
                                        else:
                                            def _t699(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('decimal_type'):
                                                    _t700 = _dollar_dollar.decimal_type
                                                else:
                                                    _t700 = None
                                                return _t700
                                            _t701 = _t699(msg)
                                            deconstruct_result104 = _t701
                                            
                                            if deconstruct_result104 is not None:
                                                _t703 = self.pretty_decimal_type(deconstruct_result104)
                                                _t702 = _t703
                                            else:
                                                def _t704(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('boolean_type'):
                                                        _t705 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t705 = None
                                                    return _t705
                                                _t706 = _t704(msg)
                                                deconstruct_result103 = _t706
                                                
                                                if deconstruct_result103 is not None:
                                                    _t708 = self.pretty_boolean_type(deconstruct_result103)
                                                    _t707 = _t708
                                                else:
                                                    raise ParseError('No matching rule for type')
                                                _t702 = _t707
                                            _t697 = _t702
                                        _t692 = _t697
                                    _t687 = _t692
                                _t682 = _t687
                            _t677 = _t682
                        _t672 = _t677
                    _t667 = _t672
                _t662 = _t667
            _t657 = _t662
        return _t657

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> Optional[NoReturn]:
        def _t709(_dollar_dollar):
            return _dollar_dollar
        _t710 = _t709(msg)
        fields114 = _t710
        assert fields114 is not None
        unwrapped_fields115 = fields114
        self.write('UNKNOWN')
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> Optional[NoReturn]:
        def _t711(_dollar_dollar):
            return _dollar_dollar
        _t712 = _t711(msg)
        fields116 = _t712
        assert fields116 is not None
        unwrapped_fields117 = fields116
        self.write('STRING')
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> Optional[NoReturn]:
        def _t713(_dollar_dollar):
            return _dollar_dollar
        _t714 = _t713(msg)
        fields118 = _t714
        assert fields118 is not None
        unwrapped_fields119 = fields118
        self.write('INT')
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> Optional[NoReturn]:
        def _t715(_dollar_dollar):
            return _dollar_dollar
        _t716 = _t715(msg)
        fields120 = _t716
        assert fields120 is not None
        unwrapped_fields121 = fields120
        self.write('FLOAT')
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> Optional[NoReturn]:
        def _t717(_dollar_dollar):
            return _dollar_dollar
        _t718 = _t717(msg)
        fields122 = _t718
        assert fields122 is not None
        unwrapped_fields123 = fields122
        self.write('UINT128')
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> Optional[NoReturn]:
        def _t719(_dollar_dollar):
            return _dollar_dollar
        _t720 = _t719(msg)
        fields124 = _t720
        assert fields124 is not None
        unwrapped_fields125 = fields124
        self.write('INT128')
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> Optional[NoReturn]:
        def _t721(_dollar_dollar):
            return _dollar_dollar
        _t722 = _t721(msg)
        fields126 = _t722
        assert fields126 is not None
        unwrapped_fields127 = fields126
        self.write('DATE')
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> Optional[NoReturn]:
        def _t723(_dollar_dollar):
            return _dollar_dollar
        _t724 = _t723(msg)
        fields128 = _t724
        assert fields128 is not None
        unwrapped_fields129 = fields128
        self.write('DATETIME')
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> Optional[NoReturn]:
        def _t725(_dollar_dollar):
            return _dollar_dollar
        _t726 = _t725(msg)
        fields130 = _t726
        assert fields130 is not None
        unwrapped_fields131 = fields130
        self.write('MISSING')
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> Optional[NoReturn]:
        def _t727(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t728 = _t727(msg)
        fields132 = _t728
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

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType) -> Optional[NoReturn]:
        def _t729(_dollar_dollar):
            return _dollar_dollar
        _t730 = _t729(msg)
        fields136 = _t730
        assert fields136 is not None
        unwrapped_fields137 = fields136
        self.write('BOOLEAN')
        return None

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]) -> Optional[NoReturn]:
        def _t731(_dollar_dollar):
            return _dollar_dollar
        _t732 = _t731(msg)
        fields138 = _t732
        assert fields138 is not None
        unwrapped_fields139 = fields138
        self.write('|')
        if not len(unwrapped_fields139) == 0:
            self.write(' ')
            for i141, elem140 in enumerate(unwrapped_fields139):
                if (i141 > 0):
                    self.newline()
                _t733 = self.pretty_binding(elem140)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> Optional[NoReturn]:
        def _t734(_dollar_dollar):
            
            if (_dollar_dollar.HasField('conjunction') and len(_dollar_dollar.conjunction.args) == 0):
                _t735 = _dollar_dollar.conjunction
            else:
                _t735 = None
            return _t735
        _t736 = _t734(msg)
        deconstruct_result154 = _t736
        
        if deconstruct_result154 is not None:
            _t738 = self.pretty_true(deconstruct_result154)
            _t737 = _t738
        else:
            def _t739(_dollar_dollar):
                
                if (_dollar_dollar.HasField('disjunction') and len(_dollar_dollar.disjunction.args) == 0):
                    _t740 = _dollar_dollar.disjunction
                else:
                    _t740 = None
                return _t740
            _t741 = _t739(msg)
            deconstruct_result153 = _t741
            
            if deconstruct_result153 is not None:
                _t743 = self.pretty_false(deconstruct_result153)
                _t742 = _t743
            else:
                def _t744(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('exists'):
                        _t745 = _dollar_dollar.exists
                    else:
                        _t745 = None
                    return _t745
                _t746 = _t744(msg)
                deconstruct_result152 = _t746
                
                if deconstruct_result152 is not None:
                    _t748 = self.pretty_exists(deconstruct_result152)
                    _t747 = _t748
                else:
                    def _t749(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('reduce'):
                            _t750 = _dollar_dollar.reduce
                        else:
                            _t750 = None
                        return _t750
                    _t751 = _t749(msg)
                    deconstruct_result151 = _t751
                    
                    if deconstruct_result151 is not None:
                        _t753 = self.pretty_reduce(deconstruct_result151)
                        _t752 = _t753
                    else:
                        def _t754(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('conjunction'):
                                _t755 = _dollar_dollar.conjunction
                            else:
                                _t755 = None
                            return _t755
                        _t756 = _t754(msg)
                        deconstruct_result150 = _t756
                        
                        if deconstruct_result150 is not None:
                            _t758 = self.pretty_conjunction(deconstruct_result150)
                            _t757 = _t758
                        else:
                            def _t759(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('disjunction'):
                                    _t760 = _dollar_dollar.disjunction
                                else:
                                    _t760 = None
                                return _t760
                            _t761 = _t759(msg)
                            deconstruct_result149 = _t761
                            
                            if deconstruct_result149 is not None:
                                _t763 = self.pretty_disjunction(deconstruct_result149)
                                _t762 = _t763
                            else:
                                def _t764(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('not'):
                                        _t765 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t765 = None
                                    return _t765
                                _t766 = _t764(msg)
                                deconstruct_result148 = _t766
                                
                                if deconstruct_result148 is not None:
                                    _t768 = self.pretty_not(deconstruct_result148)
                                    _t767 = _t768
                                else:
                                    def _t769(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('ffi'):
                                            _t770 = _dollar_dollar.ffi
                                        else:
                                            _t770 = None
                                        return _t770
                                    _t771 = _t769(msg)
                                    deconstruct_result147 = _t771
                                    
                                    if deconstruct_result147 is not None:
                                        _t773 = self.pretty_ffi(deconstruct_result147)
                                        _t772 = _t773
                                    else:
                                        def _t774(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('atom'):
                                                _t775 = _dollar_dollar.atom
                                            else:
                                                _t775 = None
                                            return _t775
                                        _t776 = _t774(msg)
                                        deconstruct_result146 = _t776
                                        
                                        if deconstruct_result146 is not None:
                                            _t778 = self.pretty_atom(deconstruct_result146)
                                            _t777 = _t778
                                        else:
                                            def _t779(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('pragma'):
                                                    _t780 = _dollar_dollar.pragma
                                                else:
                                                    _t780 = None
                                                return _t780
                                            _t781 = _t779(msg)
                                            deconstruct_result145 = _t781
                                            
                                            if deconstruct_result145 is not None:
                                                _t783 = self.pretty_pragma(deconstruct_result145)
                                                _t782 = _t783
                                            else:
                                                def _t784(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('primitive'):
                                                        _t785 = _dollar_dollar.primitive
                                                    else:
                                                        _t785 = None
                                                    return _t785
                                                _t786 = _t784(msg)
                                                deconstruct_result144 = _t786
                                                
                                                if deconstruct_result144 is not None:
                                                    _t788 = self.pretty_primitive(deconstruct_result144)
                                                    _t787 = _t788
                                                else:
                                                    def _t789(_dollar_dollar):
                                                        
                                                        if _dollar_dollar.HasField('rel_atom'):
                                                            _t790 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t790 = None
                                                        return _t790
                                                    _t791 = _t789(msg)
                                                    deconstruct_result143 = _t791
                                                    
                                                    if deconstruct_result143 is not None:
                                                        _t793 = self.pretty_rel_atom(deconstruct_result143)
                                                        _t792 = _t793
                                                    else:
                                                        def _t794(_dollar_dollar):
                                                            
                                                            if _dollar_dollar.HasField('cast'):
                                                                _t795 = _dollar_dollar.cast
                                                            else:
                                                                _t795 = None
                                                            return _t795
                                                        _t796 = _t794(msg)
                                                        deconstruct_result142 = _t796
                                                        
                                                        if deconstruct_result142 is not None:
                                                            _t798 = self.pretty_cast(deconstruct_result142)
                                                            _t797 = _t798
                                                        else:
                                                            raise ParseError('No matching rule for formula')
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
            _t737 = _t742
        return _t737

    def pretty_true(self, msg: logic_pb2.Conjunction) -> Optional[NoReturn]:
        def _t799(_dollar_dollar):
            return _dollar_dollar
        _t800 = _t799(msg)
        fields155 = _t800
        assert fields155 is not None
        unwrapped_fields156 = fields155
        self.write('(')
        self.write('true')
        self.write(')')
        return None

    def pretty_false(self, msg: logic_pb2.Disjunction) -> Optional[NoReturn]:
        def _t801(_dollar_dollar):
            return _dollar_dollar
        _t802 = _t801(msg)
        fields157 = _t802
        assert fields157 is not None
        unwrapped_fields158 = fields157
        self.write('(')
        self.write('false')
        self.write(')')
        return None

    def pretty_exists(self, msg: logic_pb2.Exists) -> Optional[NoReturn]:
        def _t803(_dollar_dollar):
            _t804 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t804, _dollar_dollar.body.value,)
        _t805 = _t803(msg)
        fields159 = _t805
        assert fields159 is not None
        unwrapped_fields160 = fields159
        self.write('(')
        self.write('exists')
        self.indent()
        self.newline()
        field161 = unwrapped_fields160[0]
        _t806 = self.pretty_bindings(field161)
        self.newline()
        field162 = unwrapped_fields160[1]
        _t807 = self.pretty_formula(field162)
        self.dedent()
        self.write(')')
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> Optional[NoReturn]:
        def _t808(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t809 = _t808(msg)
        fields163 = _t809
        assert fields163 is not None
        unwrapped_fields164 = fields163
        self.write('(')
        self.write('reduce')
        self.indent()
        self.newline()
        field165 = unwrapped_fields164[0]
        _t810 = self.pretty_abstraction(field165)
        self.newline()
        field166 = unwrapped_fields164[1]
        _t811 = self.pretty_abstraction(field166)
        self.newline()
        field167 = unwrapped_fields164[2]
        _t812 = self.pretty_terms(field167)
        self.dedent()
        self.write(')')
        return None

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]) -> Optional[NoReturn]:
        def _t813(_dollar_dollar):
            return _dollar_dollar
        _t814 = _t813(msg)
        fields168 = _t814
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
                _t815 = self.pretty_term(elem170)
        self.dedent()
        self.write(')')
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> Optional[NoReturn]:
        def _t816(_dollar_dollar):
            
            if _dollar_dollar.HasField('var'):
                _t817 = _dollar_dollar.var
            else:
                _t817 = None
            return _t817
        _t818 = _t816(msg)
        deconstruct_result173 = _t818
        
        if deconstruct_result173 is not None:
            _t820 = self.pretty_var(deconstruct_result173)
            _t819 = _t820
        else:
            def _t821(_dollar_dollar):
                
                if _dollar_dollar.HasField('constant'):
                    _t822 = _dollar_dollar.constant
                else:
                    _t822 = None
                return _t822
            _t823 = _t821(msg)
            deconstruct_result172 = _t823
            
            if deconstruct_result172 is not None:
                _t825 = self.pretty_constant(deconstruct_result172)
                _t824 = _t825
            else:
                raise ParseError('No matching rule for term')
            _t819 = _t824
        return _t819

    def pretty_var(self, msg: logic_pb2.Var) -> Optional[NoReturn]:
        def _t826(_dollar_dollar):
            return _dollar_dollar.name
        _t827 = _t826(msg)
        fields174 = _t827
        assert fields174 is not None
        unwrapped_fields175 = fields174
        self.write(unwrapped_fields175)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> Optional[NoReturn]:
        def _t828(_dollar_dollar):
            return _dollar_dollar
        _t829 = _t828(msg)
        fields176 = _t829
        assert fields176 is not None
        unwrapped_fields177 = fields176
        _t830 = self.pretty_value(unwrapped_fields177)
        return _t830

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> Optional[NoReturn]:
        def _t831(_dollar_dollar):
            return _dollar_dollar.args
        _t832 = _t831(msg)
        fields178 = _t832
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
                _t833 = self.pretty_formula(elem180)
        self.dedent()
        self.write(')')
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> Optional[NoReturn]:
        def _t834(_dollar_dollar):
            return _dollar_dollar.args
        _t835 = _t834(msg)
        fields182 = _t835
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
                _t836 = self.pretty_formula(elem184)
        self.dedent()
        self.write(')')
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> Optional[NoReturn]:
        def _t837(_dollar_dollar):
            return _dollar_dollar.arg
        _t838 = _t837(msg)
        fields186 = _t838
        assert fields186 is not None
        unwrapped_fields187 = fields186
        self.write('(')
        self.write('not')
        self.indent()
        self.newline()
        _t839 = self.pretty_formula(unwrapped_fields187)
        self.dedent()
        self.write(')')
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> Optional[NoReturn]:
        def _t840(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t841 = _t840(msg)
        fields188 = _t841
        assert fields188 is not None
        unwrapped_fields189 = fields188
        self.write('(')
        self.write('ffi')
        self.indent()
        self.newline()
        field190 = unwrapped_fields189[0]
        _t842 = self.pretty_name(field190)
        self.newline()
        field191 = unwrapped_fields189[1]
        _t843 = self.pretty_ffi_args(field191)
        self.newline()
        field192 = unwrapped_fields189[2]
        _t844 = self.pretty_terms(field192)
        self.dedent()
        self.write(')')
        return None

    def pretty_name(self, msg: str) -> Optional[NoReturn]:
        def _t845(_dollar_dollar):
            return _dollar_dollar
        _t846 = _t845(msg)
        fields193 = _t846
        assert fields193 is not None
        unwrapped_fields194 = fields193
        self.write(':')
        self.write(unwrapped_fields194)
        return None

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]) -> Optional[NoReturn]:
        def _t847(_dollar_dollar):
            return _dollar_dollar
        _t848 = _t847(msg)
        fields195 = _t848
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
                _t849 = self.pretty_abstraction(elem197)
        self.dedent()
        self.write(')')
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> Optional[NoReturn]:
        def _t850(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t851 = _t850(msg)
        fields199 = _t851
        assert fields199 is not None
        unwrapped_fields200 = fields199
        self.write('(')
        self.write('atom')
        self.indent()
        self.newline()
        field201 = unwrapped_fields200[0]
        _t852 = self.pretty_relation_id(field201)
        field202 = unwrapped_fields200[1]
        if not len(field202) == 0:
            self.newline()
            for i204, elem203 in enumerate(field202):
                if (i204 > 0):
                    self.newline()
                _t853 = self.pretty_term(elem203)
        self.dedent()
        self.write(')')
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> Optional[NoReturn]:
        def _t854(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t855 = _t854(msg)
        fields205 = _t855
        assert fields205 is not None
        unwrapped_fields206 = fields205
        self.write('(')
        self.write('pragma')
        self.indent()
        self.newline()
        field207 = unwrapped_fields206[0]
        _t856 = self.pretty_name(field207)
        field208 = unwrapped_fields206[1]
        if not len(field208) == 0:
            self.newline()
            for i210, elem209 in enumerate(field208):
                if (i210 > 0):
                    self.newline()
                _t857 = self.pretty_term(elem209)
        self.dedent()
        self.write(')')
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t858(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t859 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t859 = None
            return _t859
        _t860 = _t858(msg)
        guard_result225 = _t860
        
        if guard_result225 is not None:
            _t862 = self.pretty_eq(msg)
            _t861 = _t862
        else:
            def _t863(_dollar_dollar):
                
                if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                    _t864 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t864 = None
                return _t864
            _t865 = _t863(msg)
            guard_result224 = _t865
            
            if guard_result224 is not None:
                _t867 = self.pretty_lt(msg)
                _t866 = _t867
            else:
                def _t868(_dollar_dollar):
                    
                    if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                        _t869 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t869 = None
                    return _t869
                _t870 = _t868(msg)
                guard_result223 = _t870
                
                if guard_result223 is not None:
                    _t872 = self.pretty_lt_eq(msg)
                    _t871 = _t872
                else:
                    def _t873(_dollar_dollar):
                        
                        if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                            _t874 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t874 = None
                        return _t874
                    _t875 = _t873(msg)
                    guard_result222 = _t875
                    
                    if guard_result222 is not None:
                        _t877 = self.pretty_gt(msg)
                        _t876 = _t877
                    else:
                        def _t878(_dollar_dollar):
                            
                            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                                _t879 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t879 = None
                            return _t879
                        _t880 = _t878(msg)
                        guard_result221 = _t880
                        
                        if guard_result221 is not None:
                            _t882 = self.pretty_gt_eq(msg)
                            _t881 = _t882
                        else:
                            def _t883(_dollar_dollar):
                                
                                if _dollar_dollar.name == 'rel_primitive_add_monotype':
                                    _t884 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t884 = None
                                return _t884
                            _t885 = _t883(msg)
                            guard_result220 = _t885
                            
                            if guard_result220 is not None:
                                _t887 = self.pretty_add(msg)
                                _t886 = _t887
                            else:
                                def _t888(_dollar_dollar):
                                    
                                    if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                                        _t889 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t889 = None
                                    return _t889
                                _t890 = _t888(msg)
                                guard_result219 = _t890
                                
                                if guard_result219 is not None:
                                    _t892 = self.pretty_minus(msg)
                                    _t891 = _t892
                                else:
                                    def _t893(_dollar_dollar):
                                        
                                        if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                                            _t894 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t894 = None
                                        return _t894
                                    _t895 = _t893(msg)
                                    guard_result218 = _t895
                                    
                                    if guard_result218 is not None:
                                        _t897 = self.pretty_multiply(msg)
                                        _t896 = _t897
                                    else:
                                        def _t898(_dollar_dollar):
                                            
                                            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                                                _t899 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t899 = None
                                            return _t899
                                        _t900 = _t898(msg)
                                        guard_result217 = _t900
                                        
                                        if guard_result217 is not None:
                                            _t902 = self.pretty_divide(msg)
                                            _t901 = _t902
                                        else:
                                            def _t903(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t904 = _t903(msg)
                                            fields211 = _t904
                                            assert fields211 is not None
                                            unwrapped_fields212 = fields211
                                            self.write('(')
                                            self.write('primitive')
                                            self.indent()
                                            self.newline()
                                            field213 = unwrapped_fields212[0]
                                            _t905 = self.pretty_name(field213)
                                            field214 = unwrapped_fields212[1]
                                            if not len(field214) == 0:
                                                self.newline()
                                                for i216, elem215 in enumerate(field214):
                                                    if (i216 > 0):
                                                        self.newline()
                                                    _t906 = self.pretty_rel_term(elem215)
                                            self.dedent()
                                            self.write(')')
                                            _t901 = None
                                        _t896 = _t901
                                    _t891 = _t896
                                _t886 = _t891
                            _t881 = _t886
                        _t876 = _t881
                    _t871 = _t876
                _t866 = _t871
            _t861 = _t866
        return _t861

    def pretty_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t907(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t908 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t908 = None
            return _t908
        _t909 = _t907(msg)
        fields226 = _t909
        assert fields226 is not None
        unwrapped_fields227 = fields226
        self.write('(')
        self.write('=')
        self.indent()
        self.newline()
        field228 = unwrapped_fields227[0]
        _t910 = self.pretty_term(field228)
        self.newline()
        field229 = unwrapped_fields227[1]
        _t911 = self.pretty_term(field229)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t912(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                _t913 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t913 = None
            return _t913
        _t914 = _t912(msg)
        fields230 = _t914
        assert fields230 is not None
        unwrapped_fields231 = fields230
        self.write('(')
        self.write('<')
        self.indent()
        self.newline()
        field232 = unwrapped_fields231[0]
        _t915 = self.pretty_term(field232)
        self.newline()
        field233 = unwrapped_fields231[1]
        _t916 = self.pretty_term(field233)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t917(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                _t918 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t918 = None
            return _t918
        _t919 = _t917(msg)
        fields234 = _t919
        assert fields234 is not None
        unwrapped_fields235 = fields234
        self.write('(')
        self.write('<=')
        self.indent()
        self.newline()
        field236 = unwrapped_fields235[0]
        _t920 = self.pretty_term(field236)
        self.newline()
        field237 = unwrapped_fields235[1]
        _t921 = self.pretty_term(field237)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t922(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                _t923 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t923 = None
            return _t923
        _t924 = _t922(msg)
        fields238 = _t924
        assert fields238 is not None
        unwrapped_fields239 = fields238
        self.write('(')
        self.write('>')
        self.indent()
        self.newline()
        field240 = unwrapped_fields239[0]
        _t925 = self.pretty_term(field240)
        self.newline()
        field241 = unwrapped_fields239[1]
        _t926 = self.pretty_term(field241)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t927(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                _t928 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t928 = None
            return _t928
        _t929 = _t927(msg)
        fields242 = _t929
        assert fields242 is not None
        unwrapped_fields243 = fields242
        self.write('(')
        self.write('>=')
        self.indent()
        self.newline()
        field244 = unwrapped_fields243[0]
        _t930 = self.pretty_term(field244)
        self.newline()
        field245 = unwrapped_fields243[1]
        _t931 = self.pretty_term(field245)
        self.dedent()
        self.write(')')
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t932(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_add_monotype':
                _t933 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t933 = None
            return _t933
        _t934 = _t932(msg)
        fields246 = _t934
        assert fields246 is not None
        unwrapped_fields247 = fields246
        self.write('(')
        self.write('+')
        self.indent()
        self.newline()
        field248 = unwrapped_fields247[0]
        _t935 = self.pretty_term(field248)
        self.newline()
        field249 = unwrapped_fields247[1]
        _t936 = self.pretty_term(field249)
        self.newline()
        field250 = unwrapped_fields247[2]
        _t937 = self.pretty_term(field250)
        self.dedent()
        self.write(')')
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t938(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                _t939 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t939 = None
            return _t939
        _t940 = _t938(msg)
        fields251 = _t940
        assert fields251 is not None
        unwrapped_fields252 = fields251
        self.write('(')
        self.write('-')
        self.indent()
        self.newline()
        field253 = unwrapped_fields252[0]
        _t941 = self.pretty_term(field253)
        self.newline()
        field254 = unwrapped_fields252[1]
        _t942 = self.pretty_term(field254)
        self.newline()
        field255 = unwrapped_fields252[2]
        _t943 = self.pretty_term(field255)
        self.dedent()
        self.write(')')
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t944(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                _t945 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t945 = None
            return _t945
        _t946 = _t944(msg)
        fields256 = _t946
        assert fields256 is not None
        unwrapped_fields257 = fields256
        self.write('(')
        self.write('*')
        self.indent()
        self.newline()
        field258 = unwrapped_fields257[0]
        _t947 = self.pretty_term(field258)
        self.newline()
        field259 = unwrapped_fields257[1]
        _t948 = self.pretty_term(field259)
        self.newline()
        field260 = unwrapped_fields257[2]
        _t949 = self.pretty_term(field260)
        self.dedent()
        self.write(')')
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t950(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                _t951 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t951 = None
            return _t951
        _t952 = _t950(msg)
        fields261 = _t952
        assert fields261 is not None
        unwrapped_fields262 = fields261
        self.write('(')
        self.write('/')
        self.indent()
        self.newline()
        field263 = unwrapped_fields262[0]
        _t953 = self.pretty_term(field263)
        self.newline()
        field264 = unwrapped_fields262[1]
        _t954 = self.pretty_term(field264)
        self.newline()
        field265 = unwrapped_fields262[2]
        _t955 = self.pretty_term(field265)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> Optional[NoReturn]:
        def _t956(_dollar_dollar):
            
            if _dollar_dollar.HasField('specialized_value'):
                _t957 = _dollar_dollar.specialized_value
            else:
                _t957 = None
            return _t957
        _t958 = _t956(msg)
        deconstruct_result267 = _t958
        
        if deconstruct_result267 is not None:
            _t960 = self.pretty_specialized_value(deconstruct_result267)
            _t959 = _t960
        else:
            def _t961(_dollar_dollar):
                
                if _dollar_dollar.HasField('term'):
                    _t962 = _dollar_dollar.term
                else:
                    _t962 = None
                return _t962
            _t963 = _t961(msg)
            deconstruct_result266 = _t963
            
            if deconstruct_result266 is not None:
                _t965 = self.pretty_term(deconstruct_result266)
                _t964 = _t965
            else:
                raise ParseError('No matching rule for rel_term')
            _t959 = _t964
        return _t959

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> Optional[NoReturn]:
        def _t966(_dollar_dollar):
            return _dollar_dollar
        _t967 = _t966(msg)
        fields268 = _t967
        assert fields268 is not None
        unwrapped_fields269 = fields268
        self.write('#')
        _t968 = self.pretty_value(unwrapped_fields269)
        return _t968

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> Optional[NoReturn]:
        def _t969(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t970 = _t969(msg)
        fields270 = _t970
        assert fields270 is not None
        unwrapped_fields271 = fields270
        self.write('(')
        self.write('relatom')
        self.indent()
        self.newline()
        field272 = unwrapped_fields271[0]
        _t971 = self.pretty_name(field272)
        field273 = unwrapped_fields271[1]
        if not len(field273) == 0:
            self.newline()
            for i275, elem274 in enumerate(field273):
                if (i275 > 0):
                    self.newline()
                _t972 = self.pretty_rel_term(elem274)
        self.dedent()
        self.write(')')
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> Optional[NoReturn]:
        def _t973(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t974 = _t973(msg)
        fields276 = _t974
        assert fields276 is not None
        unwrapped_fields277 = fields276
        self.write('(')
        self.write('cast')
        self.indent()
        self.newline()
        field278 = unwrapped_fields277[0]
        _t975 = self.pretty_term(field278)
        self.newline()
        field279 = unwrapped_fields277[1]
        _t976 = self.pretty_term(field279)
        self.dedent()
        self.write(')')
        return None

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]) -> Optional[NoReturn]:
        def _t977(_dollar_dollar):
            return _dollar_dollar
        _t978 = _t977(msg)
        fields280 = _t978
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
                _t979 = self.pretty_attribute(elem282)
        self.dedent()
        self.write(')')
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> Optional[NoReturn]:
        def _t980(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t981 = _t980(msg)
        fields284 = _t981
        assert fields284 is not None
        unwrapped_fields285 = fields284
        self.write('(')
        self.write('attribute')
        self.indent()
        self.newline()
        field286 = unwrapped_fields285[0]
        _t982 = self.pretty_name(field286)
        field287 = unwrapped_fields285[1]
        if not len(field287) == 0:
            self.newline()
            for i289, elem288 in enumerate(field287):
                if (i289 > 0):
                    self.newline()
                _t983 = self.pretty_value(elem288)
        self.dedent()
        self.write(')')
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> Optional[NoReturn]:
        def _t984(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t985 = _t984(msg)
        fields290 = _t985
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
                _t986 = self.pretty_relation_id(elem293)
        self.newline()
        field295 = unwrapped_fields291[1]
        _t987 = self.pretty_script(field295)
        self.dedent()
        self.write(')')
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> Optional[NoReturn]:
        def _t988(_dollar_dollar):
            return _dollar_dollar.constructs
        _t989 = _t988(msg)
        fields296 = _t989
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
                _t990 = self.pretty_construct(elem298)
        self.dedent()
        self.write(')')
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> Optional[NoReturn]:
        def _t991(_dollar_dollar):
            
            if _dollar_dollar.HasField('loop'):
                _t992 = _dollar_dollar.loop
            else:
                _t992 = None
            return _t992
        _t993 = _t991(msg)
        deconstruct_result301 = _t993
        
        if deconstruct_result301 is not None:
            _t995 = self.pretty_loop(deconstruct_result301)
            _t994 = _t995
        else:
            def _t996(_dollar_dollar):
                
                if _dollar_dollar.HasField('instruction'):
                    _t997 = _dollar_dollar.instruction
                else:
                    _t997 = None
                return _t997
            _t998 = _t996(msg)
            deconstruct_result300 = _t998
            
            if deconstruct_result300 is not None:
                _t1000 = self.pretty_instruction(deconstruct_result300)
                _t999 = _t1000
            else:
                raise ParseError('No matching rule for construct')
            _t994 = _t999
        return _t994

    def pretty_loop(self, msg: logic_pb2.Loop) -> Optional[NoReturn]:
        def _t1001(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t1002 = _t1001(msg)
        fields302 = _t1002
        assert fields302 is not None
        unwrapped_fields303 = fields302
        self.write('(')
        self.write('loop')
        self.indent()
        self.newline()
        field304 = unwrapped_fields303[0]
        _t1003 = self.pretty_init(field304)
        self.newline()
        field305 = unwrapped_fields303[1]
        _t1004 = self.pretty_script(field305)
        self.dedent()
        self.write(')')
        return None

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]) -> Optional[NoReturn]:
        def _t1005(_dollar_dollar):
            return _dollar_dollar
        _t1006 = _t1005(msg)
        fields306 = _t1006
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
                _t1007 = self.pretty_instruction(elem308)
        self.dedent()
        self.write(')')
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> Optional[NoReturn]:
        def _t1008(_dollar_dollar):
            
            if _dollar_dollar.HasField('assign'):
                _t1009 = _dollar_dollar.assign
            else:
                _t1009 = None
            return _t1009
        _t1010 = _t1008(msg)
        deconstruct_result314 = _t1010
        
        if deconstruct_result314 is not None:
            _t1012 = self.pretty_assign(deconstruct_result314)
            _t1011 = _t1012
        else:
            def _t1013(_dollar_dollar):
                
                if _dollar_dollar.HasField('upsert'):
                    _t1014 = _dollar_dollar.upsert
                else:
                    _t1014 = None
                return _t1014
            _t1015 = _t1013(msg)
            deconstruct_result313 = _t1015
            
            if deconstruct_result313 is not None:
                _t1017 = self.pretty_upsert(deconstruct_result313)
                _t1016 = _t1017
            else:
                def _t1018(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('break'):
                        _t1019 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1019 = None
                    return _t1019
                _t1020 = _t1018(msg)
                deconstruct_result312 = _t1020
                
                if deconstruct_result312 is not None:
                    _t1022 = self.pretty_break(deconstruct_result312)
                    _t1021 = _t1022
                else:
                    def _t1023(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('monoid_def'):
                            _t1024 = _dollar_dollar.monoid_def
                        else:
                            _t1024 = None
                        return _t1024
                    _t1025 = _t1023(msg)
                    deconstruct_result311 = _t1025
                    
                    if deconstruct_result311 is not None:
                        _t1027 = self.pretty_monoid_def(deconstruct_result311)
                        _t1026 = _t1027
                    else:
                        def _t1028(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('monus_def'):
                                _t1029 = _dollar_dollar.monus_def
                            else:
                                _t1029 = None
                            return _t1029
                        _t1030 = _t1028(msg)
                        deconstruct_result310 = _t1030
                        
                        if deconstruct_result310 is not None:
                            _t1032 = self.pretty_monus_def(deconstruct_result310)
                            _t1031 = _t1032
                        else:
                            raise ParseError('No matching rule for instruction')
                        _t1026 = _t1031
                    _t1021 = _t1026
                _t1016 = _t1021
            _t1011 = _t1016
        return _t1011

    def pretty_assign(self, msg: logic_pb2.Assign) -> Optional[NoReturn]:
        def _t1033(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1034 = _dollar_dollar.attrs
            else:
                _t1034 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1034,)
        _t1035 = _t1033(msg)
        fields315 = _t1035
        assert fields315 is not None
        unwrapped_fields316 = fields315
        self.write('(')
        self.write('assign')
        self.indent()
        self.newline()
        field317 = unwrapped_fields316[0]
        _t1036 = self.pretty_relation_id(field317)
        self.newline()
        field318 = unwrapped_fields316[1]
        _t1037 = self.pretty_abstraction(field318)
        field319 = unwrapped_fields316[2]
        
        if field319 is not None:
            self.newline()
            assert field319 is not None
            opt_val320 = field319
            _t1039 = self.pretty_attrs(opt_val320)
            _t1038 = _t1039
        else:
            _t1038 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> Optional[NoReturn]:
        def _t1040(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1041 = _dollar_dollar.attrs
            else:
                _t1041 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1041,)
        _t1042 = _t1040(msg)
        fields321 = _t1042
        assert fields321 is not None
        unwrapped_fields322 = fields321
        self.write('(')
        self.write('upsert')
        self.indent()
        self.newline()
        field323 = unwrapped_fields322[0]
        _t1043 = self.pretty_relation_id(field323)
        self.newline()
        field324 = unwrapped_fields322[1]
        _t1044 = self.pretty_abstraction_with_arity(field324)
        field325 = unwrapped_fields322[2]
        
        if field325 is not None:
            self.newline()
            assert field325 is not None
            opt_val326 = field325
            _t1046 = self.pretty_attrs(opt_val326)
            _t1045 = _t1046
        else:
            _t1045 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> Optional[NoReturn]:
        def _t1047(_dollar_dollar):
            _t1048 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1048, _dollar_dollar[0].value,)
        _t1049 = _t1047(msg)
        fields327 = _t1049
        assert fields327 is not None
        unwrapped_fields328 = fields327
        self.write('(')
        field329 = unwrapped_fields328[0]
        _t1050 = self.pretty_bindings(field329)
        self.write(' ')
        field330 = unwrapped_fields328[1]
        _t1051 = self.pretty_formula(field330)
        self.write(')')
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> Optional[NoReturn]:
        def _t1052(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1053 = _dollar_dollar.attrs
            else:
                _t1053 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1053,)
        _t1054 = _t1052(msg)
        fields331 = _t1054
        assert fields331 is not None
        unwrapped_fields332 = fields331
        self.write('(')
        self.write('break')
        self.indent()
        self.newline()
        field333 = unwrapped_fields332[0]
        _t1055 = self.pretty_relation_id(field333)
        self.newline()
        field334 = unwrapped_fields332[1]
        _t1056 = self.pretty_abstraction(field334)
        field335 = unwrapped_fields332[2]
        
        if field335 is not None:
            self.newline()
            assert field335 is not None
            opt_val336 = field335
            _t1058 = self.pretty_attrs(opt_val336)
            _t1057 = _t1058
        else:
            _t1057 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> Optional[NoReturn]:
        def _t1059(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1060 = _dollar_dollar.attrs
            else:
                _t1060 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1060,)
        _t1061 = _t1059(msg)
        fields337 = _t1061
        assert fields337 is not None
        unwrapped_fields338 = fields337
        self.write('(')
        self.write('monoid')
        self.indent()
        self.newline()
        field339 = unwrapped_fields338[0]
        _t1062 = self.pretty_monoid(field339)
        self.newline()
        field340 = unwrapped_fields338[1]
        _t1063 = self.pretty_relation_id(field340)
        self.newline()
        field341 = unwrapped_fields338[2]
        _t1064 = self.pretty_abstraction_with_arity(field341)
        field342 = unwrapped_fields338[3]
        
        if field342 is not None:
            self.newline()
            assert field342 is not None
            opt_val343 = field342
            _t1066 = self.pretty_attrs(opt_val343)
            _t1065 = _t1066
        else:
            _t1065 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> Optional[NoReturn]:
        def _t1067(_dollar_dollar):
            
            if _dollar_dollar.HasField('or_monoid'):
                _t1068 = _dollar_dollar.or_monoid
            else:
                _t1068 = None
            return _t1068
        _t1069 = _t1067(msg)
        deconstruct_result347 = _t1069
        
        if deconstruct_result347 is not None:
            _t1071 = self.pretty_or_monoid(deconstruct_result347)
            _t1070 = _t1071
        else:
            def _t1072(_dollar_dollar):
                
                if _dollar_dollar.HasField('min_monoid'):
                    _t1073 = _dollar_dollar.min_monoid
                else:
                    _t1073 = None
                return _t1073
            _t1074 = _t1072(msg)
            deconstruct_result346 = _t1074
            
            if deconstruct_result346 is not None:
                _t1076 = self.pretty_min_monoid(deconstruct_result346)
                _t1075 = _t1076
            else:
                def _t1077(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('max_monoid'):
                        _t1078 = _dollar_dollar.max_monoid
                    else:
                        _t1078 = None
                    return _t1078
                _t1079 = _t1077(msg)
                deconstruct_result345 = _t1079
                
                if deconstruct_result345 is not None:
                    _t1081 = self.pretty_max_monoid(deconstruct_result345)
                    _t1080 = _t1081
                else:
                    def _t1082(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('sum_monoid'):
                            _t1083 = _dollar_dollar.sum_monoid
                        else:
                            _t1083 = None
                        return _t1083
                    _t1084 = _t1082(msg)
                    deconstruct_result344 = _t1084
                    
                    if deconstruct_result344 is not None:
                        _t1086 = self.pretty_sum_monoid(deconstruct_result344)
                        _t1085 = _t1086
                    else:
                        raise ParseError('No matching rule for monoid')
                    _t1080 = _t1085
                _t1075 = _t1080
            _t1070 = _t1075
        return _t1070

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> Optional[NoReturn]:
        def _t1087(_dollar_dollar):
            return _dollar_dollar
        _t1088 = _t1087(msg)
        fields348 = _t1088
        assert fields348 is not None
        unwrapped_fields349 = fields348
        self.write('(')
        self.write('or')
        self.write(')')
        return None

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid) -> Optional[NoReturn]:
        def _t1089(_dollar_dollar):
            return _dollar_dollar.type
        _t1090 = _t1089(msg)
        fields350 = _t1090
        assert fields350 is not None
        unwrapped_fields351 = fields350
        self.write('(')
        self.write('min')
        self.indent()
        self.newline()
        _t1091 = self.pretty_type(unwrapped_fields351)
        self.dedent()
        self.write(')')
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> Optional[NoReturn]:
        def _t1092(_dollar_dollar):
            return _dollar_dollar.type
        _t1093 = _t1092(msg)
        fields352 = _t1093
        assert fields352 is not None
        unwrapped_fields353 = fields352
        self.write('(')
        self.write('max')
        self.indent()
        self.newline()
        _t1094 = self.pretty_type(unwrapped_fields353)
        self.dedent()
        self.write(')')
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> Optional[NoReturn]:
        def _t1095(_dollar_dollar):
            return _dollar_dollar.type
        _t1096 = _t1095(msg)
        fields354 = _t1096
        assert fields354 is not None
        unwrapped_fields355 = fields354
        self.write('(')
        self.write('sum')
        self.indent()
        self.newline()
        _t1097 = self.pretty_type(unwrapped_fields355)
        self.dedent()
        self.write(')')
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> Optional[NoReturn]:
        def _t1098(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1099 = _dollar_dollar.attrs
            else:
                _t1099 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1099,)
        _t1100 = _t1098(msg)
        fields356 = _t1100
        assert fields356 is not None
        unwrapped_fields357 = fields356
        self.write('(')
        self.write('monus')
        self.indent()
        self.newline()
        field358 = unwrapped_fields357[0]
        _t1101 = self.pretty_monoid(field358)
        self.newline()
        field359 = unwrapped_fields357[1]
        _t1102 = self.pretty_relation_id(field359)
        self.newline()
        field360 = unwrapped_fields357[2]
        _t1103 = self.pretty_abstraction_with_arity(field360)
        field361 = unwrapped_fields357[3]
        
        if field361 is not None:
            self.newline()
            assert field361 is not None
            opt_val362 = field361
            _t1105 = self.pretty_attrs(opt_val362)
            _t1104 = _t1105
        else:
            _t1104 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> Optional[NoReturn]:
        def _t1106(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1107 = _t1106(msg)
        fields363 = _t1107
        assert fields363 is not None
        unwrapped_fields364 = fields363
        self.write('(')
        self.write('functional_dependency')
        self.indent()
        self.newline()
        field365 = unwrapped_fields364[0]
        _t1108 = self.pretty_relation_id(field365)
        self.newline()
        field366 = unwrapped_fields364[1]
        _t1109 = self.pretty_abstraction(field366)
        self.newline()
        field367 = unwrapped_fields364[2]
        _t1110 = self.pretty_functional_dependency_keys(field367)
        self.newline()
        field368 = unwrapped_fields364[3]
        _t1111 = self.pretty_functional_dependency_values(field368)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]) -> Optional[NoReturn]:
        def _t1112(_dollar_dollar):
            return _dollar_dollar
        _t1113 = _t1112(msg)
        fields369 = _t1113
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
                _t1114 = self.pretty_var(elem371)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]) -> Optional[NoReturn]:
        def _t1115(_dollar_dollar):
            return _dollar_dollar
        _t1116 = _t1115(msg)
        fields373 = _t1116
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
                _t1117 = self.pretty_var(elem375)
        self.dedent()
        self.write(')')
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> Optional[NoReturn]:
        def _t1118(_dollar_dollar):
            
            if _dollar_dollar.HasField('rel_edb'):
                _t1119 = _dollar_dollar.rel_edb
            else:
                _t1119 = None
            return _t1119
        _t1120 = _t1118(msg)
        deconstruct_result379 = _t1120
        
        if deconstruct_result379 is not None:
            _t1122 = self.pretty_rel_edb(deconstruct_result379)
            _t1121 = _t1122
        else:
            def _t1123(_dollar_dollar):
                
                if _dollar_dollar.HasField('betree_relation'):
                    _t1124 = _dollar_dollar.betree_relation
                else:
                    _t1124 = None
                return _t1124
            _t1125 = _t1123(msg)
            deconstruct_result378 = _t1125
            
            if deconstruct_result378 is not None:
                _t1127 = self.pretty_betree_relation(deconstruct_result378)
                _t1126 = _t1127
            else:
                def _t1128(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('csv_data'):
                        _t1129 = _dollar_dollar.csv_data
                    else:
                        _t1129 = None
                    return _t1129
                _t1130 = _t1128(msg)
                deconstruct_result377 = _t1130
                
                if deconstruct_result377 is not None:
                    _t1132 = self.pretty_csv_data(deconstruct_result377)
                    _t1131 = _t1132
                else:
                    raise ParseError('No matching rule for data')
                _t1126 = _t1131
            _t1121 = _t1126
        return _t1121

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> Optional[NoReturn]:
        def _t1133(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1134 = _t1133(msg)
        fields380 = _t1134
        assert fields380 is not None
        unwrapped_fields381 = fields380
        self.write('(')
        self.write('rel_edb')
        self.indent()
        self.newline()
        field382 = unwrapped_fields381[0]
        _t1135 = self.pretty_relation_id(field382)
        self.newline()
        field383 = unwrapped_fields381[1]
        _t1136 = self.pretty_rel_edb_path(field383)
        self.newline()
        field384 = unwrapped_fields381[2]
        _t1137 = self.pretty_rel_edb_types(field384)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_edb_path(self, msg: Sequence[str]) -> Optional[NoReturn]:
        def _t1138(_dollar_dollar):
            return _dollar_dollar
        _t1139 = _t1138(msg)
        fields385 = _t1139
        assert fields385 is not None
        unwrapped_fields386 = fields385
        self.write('[')
        for i388, elem387 in enumerate(unwrapped_fields386):
            if (i388 > 0):
                self.newline()
            self.write(self.format_string_value(elem387))
        self.write(']')
        return None

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[NoReturn]:
        def _t1140(_dollar_dollar):
            return _dollar_dollar
        _t1141 = _t1140(msg)
        fields389 = _t1141
        assert fields389 is not None
        unwrapped_fields390 = fields389
        self.write('[')
        for i392, elem391 in enumerate(unwrapped_fields390):
            if (i392 > 0):
                self.newline()
            _t1142 = self.pretty_type(elem391)
        self.write(']')
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> Optional[NoReturn]:
        def _t1143(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1144 = _t1143(msg)
        fields393 = _t1144
        assert fields393 is not None
        unwrapped_fields394 = fields393
        self.write('(')
        self.write('betree_relation')
        self.indent()
        self.newline()
        field395 = unwrapped_fields394[0]
        _t1145 = self.pretty_relation_id(field395)
        self.newline()
        field396 = unwrapped_fields394[1]
        _t1146 = self.pretty_betree_info(field396)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> Optional[NoReturn]:
        def _t1147(_dollar_dollar):
            _t1148 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1148,)
        _t1149 = _t1147(msg)
        fields397 = _t1149
        assert fields397 is not None
        unwrapped_fields398 = fields397
        self.write('(')
        self.write('betree_info')
        self.indent()
        self.newline()
        field399 = unwrapped_fields398[0]
        _t1150 = self.pretty_betree_info_key_types(field399)
        self.newline()
        field400 = unwrapped_fields398[1]
        _t1151 = self.pretty_betree_info_value_types(field400)
        self.newline()
        field401 = unwrapped_fields398[2]
        _t1152 = self.pretty_config_dict(field401)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[NoReturn]:
        def _t1153(_dollar_dollar):
            return _dollar_dollar
        _t1154 = _t1153(msg)
        fields402 = _t1154
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
                _t1155 = self.pretty_type(elem404)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[NoReturn]:
        def _t1156(_dollar_dollar):
            return _dollar_dollar
        _t1157 = _t1156(msg)
        fields406 = _t1157
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
                _t1158 = self.pretty_type(elem408)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> Optional[NoReturn]:
        def _t1159(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1160 = _t1159(msg)
        fields410 = _t1160
        assert fields410 is not None
        unwrapped_fields411 = fields410
        self.write('(')
        self.write('csv_data')
        self.indent()
        self.newline()
        field412 = unwrapped_fields411[0]
        _t1161 = self.pretty_csvlocator(field412)
        self.newline()
        field413 = unwrapped_fields411[1]
        _t1162 = self.pretty_csv_config(field413)
        self.newline()
        field414 = unwrapped_fields411[2]
        _t1163 = self.pretty_csv_columns(field414)
        self.newline()
        field415 = unwrapped_fields411[3]
        _t1164 = self.pretty_csv_asof(field415)
        self.dedent()
        self.write(')')
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> Optional[NoReturn]:
        def _t1165(_dollar_dollar):
            
            if not len(_dollar_dollar.paths) == 0:
                _t1166 = _dollar_dollar.paths
            else:
                _t1166 = None
            
            if _dollar_dollar.inline_data.decode('utf-8') != '':
                _t1167 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1167 = None
            return (_t1166, _t1167,)
        _t1168 = _t1165(msg)
        fields416 = _t1168
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
            _t1170 = self.pretty_csv_locator_paths(opt_val419)
            _t1169 = _t1170
        else:
            _t1169 = None
        field420 = unwrapped_fields417[1]
        
        if field420 is not None:
            self.newline()
            assert field420 is not None
            opt_val421 = field420
            _t1172 = self.pretty_csv_locator_inline_data(opt_val421)
            _t1171 = _t1172
        else:
            _t1171 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_locator_paths(self, msg: Sequence[str]) -> Optional[NoReturn]:
        def _t1173(_dollar_dollar):
            return _dollar_dollar
        _t1174 = _t1173(msg)
        fields422 = _t1174
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

    def pretty_csv_locator_inline_data(self, msg: str) -> Optional[NoReturn]:
        def _t1175(_dollar_dollar):
            return _dollar_dollar
        _t1176 = _t1175(msg)
        fields426 = _t1176
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

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig) -> Optional[NoReturn]:
        def _t1177(_dollar_dollar):
            _t1178 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1178
        _t1179 = _t1177(msg)
        fields428 = _t1179
        assert fields428 is not None
        unwrapped_fields429 = fields428
        self.write('(')
        self.write('csv_config')
        self.indent()
        self.newline()
        _t1180 = self.pretty_config_dict(unwrapped_fields429)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]) -> Optional[NoReturn]:
        def _t1181(_dollar_dollar):
            return _dollar_dollar
        _t1182 = _t1181(msg)
        fields430 = _t1182
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
                _t1183 = self.pretty_csv_column(elem432)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> Optional[NoReturn]:
        def _t1184(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1185 = _t1184(msg)
        fields434 = _t1185
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
        _t1186 = self.pretty_relation_id(field437)
        self.newline()
        self.write('[')
        field438 = unwrapped_fields435[2]
        for i440, elem439 in enumerate(field438):
            if (i440 > 0):
                self.newline()
            _t1187 = self.pretty_type(elem439)
        self.write(']')
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_asof(self, msg: str) -> Optional[NoReturn]:
        def _t1188(_dollar_dollar):
            return _dollar_dollar
        _t1189 = _t1188(msg)
        fields441 = _t1189
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

    def pretty_undefine(self, msg: transactions_pb2.Undefine) -> Optional[NoReturn]:
        def _t1190(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1191 = _t1190(msg)
        fields443 = _t1191
        assert fields443 is not None
        unwrapped_fields444 = fields443
        self.write('(')
        self.write('undefine')
        self.indent()
        self.newline()
        _t1192 = self.pretty_fragment_id(unwrapped_fields444)
        self.dedent()
        self.write(')')
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> Optional[NoReturn]:
        def _t1193(_dollar_dollar):
            return _dollar_dollar.relations
        _t1194 = _t1193(msg)
        fields445 = _t1194
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
                _t1195 = self.pretty_relation_id(elem447)
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]) -> Optional[NoReturn]:
        def _t1196(_dollar_dollar):
            return _dollar_dollar
        _t1197 = _t1196(msg)
        fields449 = _t1197
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
                _t1198 = self.pretty_read(elem451)
        self.dedent()
        self.write(')')
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> Optional[NoReturn]:
        def _t1199(_dollar_dollar):
            
            if _dollar_dollar.HasField('demand'):
                _t1200 = _dollar_dollar.demand
            else:
                _t1200 = None
            return _t1200
        _t1201 = _t1199(msg)
        deconstruct_result457 = _t1201
        
        if deconstruct_result457 is not None:
            _t1203 = self.pretty_demand(deconstruct_result457)
            _t1202 = _t1203
        else:
            def _t1204(_dollar_dollar):
                
                if _dollar_dollar.HasField('output'):
                    _t1205 = _dollar_dollar.output
                else:
                    _t1205 = None
                return _t1205
            _t1206 = _t1204(msg)
            deconstruct_result456 = _t1206
            
            if deconstruct_result456 is not None:
                _t1208 = self.pretty_output(deconstruct_result456)
                _t1207 = _t1208
            else:
                def _t1209(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('what_if'):
                        _t1210 = _dollar_dollar.what_if
                    else:
                        _t1210 = None
                    return _t1210
                _t1211 = _t1209(msg)
                deconstruct_result455 = _t1211
                
                if deconstruct_result455 is not None:
                    _t1213 = self.pretty_what_if(deconstruct_result455)
                    _t1212 = _t1213
                else:
                    def _t1214(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('abort'):
                            _t1215 = _dollar_dollar.abort
                        else:
                            _t1215 = None
                        return _t1215
                    _t1216 = _t1214(msg)
                    deconstruct_result454 = _t1216
                    
                    if deconstruct_result454 is not None:
                        _t1218 = self.pretty_abort(deconstruct_result454)
                        _t1217 = _t1218
                    else:
                        def _t1219(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('export'):
                                _t1220 = _dollar_dollar.export
                            else:
                                _t1220 = None
                            return _t1220
                        _t1221 = _t1219(msg)
                        deconstruct_result453 = _t1221
                        
                        if deconstruct_result453 is not None:
                            _t1223 = self.pretty_export(deconstruct_result453)
                            _t1222 = _t1223
                        else:
                            raise ParseError('No matching rule for read')
                        _t1217 = _t1222
                    _t1212 = _t1217
                _t1207 = _t1212
            _t1202 = _t1207
        return _t1202

    def pretty_demand(self, msg: transactions_pb2.Demand) -> Optional[NoReturn]:
        def _t1224(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1225 = _t1224(msg)
        fields458 = _t1225
        assert fields458 is not None
        unwrapped_fields459 = fields458
        self.write('(')
        self.write('demand')
        self.indent()
        self.newline()
        _t1226 = self.pretty_relation_id(unwrapped_fields459)
        self.dedent()
        self.write(')')
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> Optional[NoReturn]:
        def _t1227(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        _t1228 = _t1227(msg)
        fields460 = _t1228
        assert fields460 is not None
        unwrapped_fields461 = fields460
        self.write('(')
        self.write('output')
        self.indent()
        self.newline()
        field462 = unwrapped_fields461[0]
        _t1229 = self.pretty_name(field462)
        self.newline()
        field463 = unwrapped_fields461[1]
        _t1230 = self.pretty_relation_id(field463)
        self.dedent()
        self.write(')')
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> Optional[NoReturn]:
        def _t1231(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1232 = _t1231(msg)
        fields464 = _t1232
        assert fields464 is not None
        unwrapped_fields465 = fields464
        self.write('(')
        self.write('what_if')
        self.indent()
        self.newline()
        field466 = unwrapped_fields465[0]
        _t1233 = self.pretty_name(field466)
        self.newline()
        field467 = unwrapped_fields465[1]
        _t1234 = self.pretty_epoch(field467)
        self.dedent()
        self.write(')')
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> Optional[NoReturn]:
        def _t1235(_dollar_dollar):
            
            if _dollar_dollar.name != 'abort':
                _t1236 = _dollar_dollar.name
            else:
                _t1236 = None
            return (_t1236, _dollar_dollar.relation_id,)
        _t1237 = _t1235(msg)
        fields468 = _t1237
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
            _t1239 = self.pretty_name(opt_val471)
            _t1238 = _t1239
        else:
            _t1238 = None
        self.newline()
        field472 = unwrapped_fields469[1]
        _t1240 = self.pretty_relation_id(field472)
        self.dedent()
        self.write(')')
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> Optional[NoReturn]:
        def _t1241(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1242 = _t1241(msg)
        fields473 = _t1242
        assert fields473 is not None
        unwrapped_fields474 = fields473
        self.write('(')
        self.write('export')
        self.indent()
        self.newline()
        _t1243 = self.pretty_export_csv_config(unwrapped_fields474)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> Optional[NoReturn]:
        def _t1244(_dollar_dollar):
            
            if len(_dollar_dollar.data_columns) == 0:
                _t1245 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1245 = None
            return _t1245
        _t1246 = _t1244(msg)
        deconstruct_result481 = _t1246
        if deconstruct_result481 is not None:
            self.write('(')
            self.write('export_csv_config_v2')
            self.indent()
            self.newline()
            field482 = deconstruct_result481[0]
            _t1247 = self.pretty_export_csv_path(field482)
            self.newline()
            field483 = deconstruct_result481[1]
            _t1248 = self.pretty_export_csv_source(field483)
            self.newline()
            field484 = deconstruct_result481[2]
            _t1249 = self.pretty_csv_config(field484)
            self.dedent()
            self.write(')')
        else:
            def _t1250(_dollar_dollar):
                
                if len(_dollar_dollar.data_columns) != 0:
                    _t1252 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1251 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1252,)
                else:
                    _t1251 = None
                return _t1251
            _t1253 = _t1250(msg)
            deconstruct_result475 = _t1253
            if deconstruct_result475 is not None:
                self.write('(')
                self.write('export_csv_config')
                self.indent()
                self.newline()
                field476 = deconstruct_result475[0]
                _t1254 = self.pretty_export_csv_path(field476)
                self.newline()
                self.write('(')
                self.newline()
                self.write('columns')
                field477 = deconstruct_result475[1]
                if not len(field477) == 0:
                    self.newline()
                    for i479, elem478 in enumerate(field477):
                        if (i479 > 0):
                            self.newline()
                        _t1255 = self.pretty_export_csv_column(elem478)
                self.dedent()
                self.write(')')
                self.newline()
                field480 = deconstruct_result475[2]
                _t1256 = self.pretty_config_dict(field480)
                self.dedent()
                self.write(')')
            else:
                raise ParseError('No matching rule for export_csv_config')
        return None

    def pretty_export_csv_path(self, msg: str) -> Optional[NoReturn]:
        def _t1257(_dollar_dollar):
            return _dollar_dollar
        _t1258 = _t1257(msg)
        fields485 = _t1258
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

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource) -> Optional[NoReturn]:
        def _t1259(_dollar_dollar):
            
            if _dollar_dollar.HasField('gnf_columns'):
                _t1260 = _dollar_dollar.gnf_columns.columns
            else:
                _t1260 = None
            return _t1260
        _t1261 = _t1259(msg)
        deconstruct_result488 = _t1261
        if deconstruct_result488 is not None:
            self.write('(')
            self.write('gnf_columns')
            self.indent()
            if not len(deconstruct_result488) == 0:
                self.newline()
                for i490, elem489 in enumerate(deconstruct_result488):
                    if (i490 > 0):
                        self.newline()
                    _t1262 = self.pretty_export_csv_column(elem489)
            self.dedent()
            self.write(')')
        else:
            def _t1263(_dollar_dollar):
                
                if _dollar_dollar.HasField('table_def'):
                    _t1264 = _dollar_dollar.table_def
                else:
                    _t1264 = None
                return _t1264
            _t1265 = _t1263(msg)
            deconstruct_result487 = _t1265
            if deconstruct_result487 is not None:
                self.write('(')
                self.write('table_def')
                self.indent()
                self.newline()
                _t1266 = self.pretty_relation_id(deconstruct_result487)
                self.dedent()
                self.write(')')
            else:
                raise ParseError('No matching rule for export_csv_source')
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> Optional[NoReturn]:
        def _t1267(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1268 = _t1267(msg)
        fields491 = _t1268
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
        _t1269 = self.pretty_relation_id(field494)
        self.dedent()
        self.write(')')
        return None


def pretty(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
