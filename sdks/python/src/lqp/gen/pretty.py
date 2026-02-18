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

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1275 = logic_pb2.Value(float_value=v)
        return _t1275

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == '':
            return self.relation_id_to_uint128(msg)
        return None

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1276 = logic_pb2.Value(int_value=v)
        return _t1276

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        return (abs.vars[0:n], [],)

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1277 = logic_pb2.Value(boolean_value=v)
        return _t1277

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1278 = logic_pb2.Value(uint128_value=v)
        return _t1278

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1279 = self._make_value_int32(msg.header_row)
        result.append(('csv_header_row', _t1279,))
        _t1280 = self._make_value_int64(msg.skip)
        result.append(('csv_skip', _t1280,))
        if msg.new_line != '':
            _t1281 = self._make_value_string(msg.new_line)
            result.append(('csv_new_line', _t1281,))
        _t1282 = self._make_value_string(msg.delimiter)
        result.append(('csv_delimiter', _t1282,))
        _t1283 = self._make_value_string(msg.quotechar)
        result.append(('csv_quotechar', _t1283,))
        _t1284 = self._make_value_string(msg.escapechar)
        result.append(('csv_escapechar', _t1284,))
        if msg.comment != '':
            _t1285 = self._make_value_string(msg.comment)
            result.append(('csv_comment', _t1285,))
        for missing_string in msg.missing_strings:
            _t1286 = self._make_value_string(missing_string)
            result.append(('csv_missing_strings', _t1286,))
        _t1287 = self._make_value_string(msg.decimal_separator)
        result.append(('csv_decimal_separator', _t1287,))
        _t1288 = self._make_value_string(msg.encoding)
        result.append(('csv_encoding', _t1288,))
        _t1289 = self._make_value_string(msg.compression)
        result.append(('csv_compression', _t1289,))
        if msg.partition_size_mb != 0:
            _t1290 = self._make_value_int64(msg.partition_size_mb)
            result.append(('csv_partition_size_mb', _t1290,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1291 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(('betree_config_epsilon', _t1291,))
        _t1292 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(('betree_config_max_pivots', _t1292,))
        _t1293 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(('betree_config_max_deltas', _t1293,))
        _t1294 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(('betree_config_max_leaf', _t1294,))
        if msg.relation_locator.HasField('root_pageid'):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1295 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(('betree_locator_root_pageid', _t1295,))
        if msg.relation_locator.HasField('inline_data'):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1296 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(('betree_locator_inline_data', _t1296,))
        _t1297 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(('betree_locator_element_count', _t1297,))
        _t1298 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(('betree_locator_tree_height', _t1298,))
        return sorted(result)

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1299 = logic_pb2.Value(int_value=int(v))
        return _t1299

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != '':
            return name
        return None

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1300 = logic_pb2.Value(string_value=v)
        return _t1300

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1301 = self._make_value_string('auto')
            result.append(('ivm.maintenance_level', _t1301,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1302 = self._make_value_string('all')
                result.append(('ivm.maintenance_level', _t1302,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1303 = self._make_value_string('off')
                    result.append(('ivm.maintenance_level', _t1303,))
        _t1304 = self._make_value_int64(msg.semantics_version)
        result.append(('semantics_version', _t1304,))
        return sorted(result)

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1305 = self._make_value_int64(msg.partition_size)
            result.append(('partition_size', _t1305,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1306 = self._make_value_string(msg.compression)
            result.append(('compression', _t1306,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1307 = self._make_value_boolean(msg.syntax_header_row)
            result.append(('syntax_header_row', _t1307,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1308 = self._make_value_string(msg.syntax_missing_string)
            result.append(('syntax_missing_string', _t1308,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1309 = self._make_value_string(msg.syntax_delim)
            result.append(('syntax_delim', _t1309,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1310 = self._make_value_string(msg.syntax_quotechar)
            result.append(('syntax_quotechar', _t1310,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1311 = self._make_value_string(msg.syntax_escapechar)
            result.append(('syntax_escapechar', _t1311,))
        return sorted(result)

    # --- Pretty-print methods ---

    def pretty_transaction(self, msg: transactions_pb2.Transaction) -> Optional[NoReturn]:
        def _t497(_dollar_dollar):
            
            if _dollar_dollar.HasField('configure'):
                _t498 = _dollar_dollar.configure
            else:
                _t498 = None
            
            if _dollar_dollar.HasField('sync'):
                _t499 = _dollar_dollar.sync
            else:
                _t499 = None
            return (_t498, _t499, _dollar_dollar.epochs,)
        _t500 = _t497(msg)
        fields0 = _t500
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
            _t502 = self.pretty_configure(opt_val3)
            _t501 = _t502
        else:
            _t501 = None
        field4 = unwrapped_fields1[1]
        
        if field4 is not None:
            self.newline()
            assert field4 is not None
            opt_val5 = field4
            _t504 = self.pretty_sync(opt_val5)
            _t503 = _t504
        else:
            _t503 = None
        field6 = unwrapped_fields1[2]
        if not len(field6) == 0:
            self.newline()
            for i8, elem7 in enumerate(field6):
                if (i8 > 0):
                    self.newline()
                _t505 = self.pretty_epoch(elem7)
        self.dedent()
        self.write(')')
        return None

    def pretty_configure(self, msg: transactions_pb2.Configure) -> Optional[NoReturn]:
        def _t506(_dollar_dollar):
            _t507 = self.deconstruct_configure(_dollar_dollar)
            return _t507
        _t508 = _t506(msg)
        fields9 = _t508
        assert fields9 is not None
        unwrapped_fields10 = fields9
        self.write('(')
        self.write('configure')
        self.indent()
        self.newline()
        _t509 = self.pretty_config_dict(unwrapped_fields10)
        self.dedent()
        self.write(')')
        return None

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]) -> Optional[NoReturn]:
        def _t510(_dollar_dollar):
            return _dollar_dollar
        _t511 = _t510(msg)
        fields11 = _t511
        assert fields11 is not None
        unwrapped_fields12 = fields11
        self.write('{')
        if not len(unwrapped_fields12) == 0:
            self.write(' ')
            for i14, elem13 in enumerate(unwrapped_fields12):
                if (i14 > 0):
                    self.newline()
                _t512 = self.pretty_config_key_value(elem13)
        self.write('}')
        return None

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]) -> Optional[NoReturn]:
        def _t513(_dollar_dollar):
            return (_dollar_dollar[0], _dollar_dollar[1],)
        _t514 = _t513(msg)
        fields15 = _t514
        assert fields15 is not None
        unwrapped_fields16 = fields15
        self.write(':')
        field17 = unwrapped_fields16[0]
        self.write(field17)
        self.write(' ')
        field18 = unwrapped_fields16[1]
        _t515 = self.pretty_value(field18)
        return _t515

    def pretty_value(self, msg: logic_pb2.Value) -> Optional[NoReturn]:
        def _t516(_dollar_dollar):
            
            if _dollar_dollar.HasField('date_value'):
                _t517 = _dollar_dollar.date_value
            else:
                _t517 = None
            return _t517
        _t518 = _t516(msg)
        deconstruct_result29 = _t518
        
        if deconstruct_result29 is not None:
            _t520 = self.pretty_date(deconstruct_result29)
            _t519 = _t520
        else:
            def _t521(_dollar_dollar):
                
                if _dollar_dollar.HasField('datetime_value'):
                    _t522 = _dollar_dollar.datetime_value
                else:
                    _t522 = None
                return _t522
            _t523 = _t521(msg)
            deconstruct_result28 = _t523
            
            if deconstruct_result28 is not None:
                _t525 = self.pretty_datetime(deconstruct_result28)
                _t524 = _t525
            else:
                def _t526(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('string_value'):
                        _t527 = _dollar_dollar.string_value
                    else:
                        _t527 = None
                    return _t527
                _t528 = _t526(msg)
                deconstruct_result27 = _t528
                
                if deconstruct_result27 is not None:
                    self.write(self.format_string_value(deconstruct_result27))
                    _t529 = None
                else:
                    def _t530(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('int_value'):
                            _t531 = _dollar_dollar.int_value
                        else:
                            _t531 = None
                        return _t531
                    _t532 = _t530(msg)
                    deconstruct_result26 = _t532
                    
                    if deconstruct_result26 is not None:
                        self.write(str(deconstruct_result26))
                        _t533 = None
                    else:
                        def _t534(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('float_value'):
                                _t535 = _dollar_dollar.float_value
                            else:
                                _t535 = None
                            return _t535
                        _t536 = _t534(msg)
                        deconstruct_result25 = _t536
                        
                        if deconstruct_result25 is not None:
                            self.write(str(deconstruct_result25))
                            _t537 = None
                        else:
                            def _t538(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('uint128_value'):
                                    _t539 = _dollar_dollar.uint128_value
                                else:
                                    _t539 = None
                                return _t539
                            _t540 = _t538(msg)
                            deconstruct_result24 = _t540
                            
                            if deconstruct_result24 is not None:
                                self.write(self.format_uint128(deconstruct_result24))
                                _t541 = None
                            else:
                                def _t542(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('int128_value'):
                                        _t543 = _dollar_dollar.int128_value
                                    else:
                                        _t543 = None
                                    return _t543
                                _t544 = _t542(msg)
                                deconstruct_result23 = _t544
                                
                                if deconstruct_result23 is not None:
                                    self.write(self.format_int128(deconstruct_result23))
                                    _t545 = None
                                else:
                                    def _t546(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('decimal_value'):
                                            _t547 = _dollar_dollar.decimal_value
                                        else:
                                            _t547 = None
                                        return _t547
                                    _t548 = _t546(msg)
                                    deconstruct_result22 = _t548
                                    
                                    if deconstruct_result22 is not None:
                                        self.write(self.format_decimal(deconstruct_result22))
                                        _t549 = None
                                    else:
                                        def _t550(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('boolean_value'):
                                                _t551 = _dollar_dollar.boolean_value
                                            else:
                                                _t551 = None
                                            return _t551
                                        _t552 = _t550(msg)
                                        deconstruct_result21 = _t552
                                        
                                        if deconstruct_result21 is not None:
                                            _t554 = self.pretty_boolean_value(deconstruct_result21)
                                            _t553 = _t554
                                        else:
                                            def _t555(_dollar_dollar):
                                                return _dollar_dollar
                                            _t556 = _t555(msg)
                                            fields19 = _t556
                                            assert fields19 is not None
                                            unwrapped_fields20 = fields19
                                            self.write('missing')
                                            _t553 = None
                                        _t549 = _t553
                                    _t545 = _t549
                                _t541 = _t545
                            _t537 = _t541
                        _t533 = _t537
                    _t529 = _t533
                _t524 = _t529
            _t519 = _t524
        return _t519

    def pretty_date(self, msg: logic_pb2.DateValue) -> Optional[NoReturn]:
        def _t557(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
        _t558 = _t557(msg)
        fields30 = _t558
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
        def _t559(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
        _t560 = _t559(msg)
        fields35 = _t560
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
        def _t561(_dollar_dollar):
            
            if _dollar_dollar:
                _t562 = ()
            else:
                _t562 = None
            return _t562
        _t563 = _t561(msg)
        deconstruct_result46 = _t563
        if deconstruct_result46 is not None:
            self.write('true')
        else:
            def _t564(_dollar_dollar):
                
                if not _dollar_dollar:
                    _t565 = ()
                else:
                    _t565 = None
                return _t565
            _t566 = _t564(msg)
            deconstruct_result45 = _t566
            if deconstruct_result45 is not None:
                self.write('false')
            else:
                raise ParseError('No matching rule for boolean_value')
        return None

    def pretty_sync(self, msg: transactions_pb2.Sync) -> Optional[NoReturn]:
        def _t567(_dollar_dollar):
            return _dollar_dollar.fragments
        _t568 = _t567(msg)
        fields47 = _t568
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
                _t569 = self.pretty_fragment_id(elem49)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[NoReturn]:
        def _t570(_dollar_dollar):
            return self.fragment_id_to_string(_dollar_dollar)
        _t571 = _t570(msg)
        fields51 = _t571
        assert fields51 is not None
        unwrapped_fields52 = fields51
        self.write(':')
        self.write(unwrapped_fields52)
        return None

    def pretty_epoch(self, msg: transactions_pb2.Epoch) -> Optional[NoReturn]:
        def _t572(_dollar_dollar):
            
            if not len(_dollar_dollar.writes) == 0:
                _t573 = _dollar_dollar.writes
            else:
                _t573 = None
            
            if not len(_dollar_dollar.reads) == 0:
                _t574 = _dollar_dollar.reads
            else:
                _t574 = None
            return (_t573, _t574,)
        _t575 = _t572(msg)
        fields53 = _t575
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
            _t577 = self.pretty_epoch_writes(opt_val56)
            _t576 = _t577
        else:
            _t576 = None
        field57 = unwrapped_fields54[1]
        
        if field57 is not None:
            self.newline()
            assert field57 is not None
            opt_val58 = field57
            _t579 = self.pretty_epoch_reads(opt_val58)
            _t578 = _t579
        else:
            _t578 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]) -> Optional[NoReturn]:
        def _t580(_dollar_dollar):
            return _dollar_dollar
        _t581 = _t580(msg)
        fields59 = _t581
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
                _t582 = self.pretty_write(elem61)
        self.dedent()
        self.write(')')
        return None

    def pretty_write(self, msg: transactions_pb2.Write) -> Optional[NoReturn]:
        def _t583(_dollar_dollar):
            
            if _dollar_dollar.HasField('define'):
                _t584 = _dollar_dollar.define
            else:
                _t584 = None
            return _t584
        _t585 = _t583(msg)
        deconstruct_result65 = _t585
        
        if deconstruct_result65 is not None:
            _t587 = self.pretty_define(deconstruct_result65)
            _t586 = _t587
        else:
            def _t588(_dollar_dollar):
                
                if _dollar_dollar.HasField('undefine'):
                    _t589 = _dollar_dollar.undefine
                else:
                    _t589 = None
                return _t589
            _t590 = _t588(msg)
            deconstruct_result64 = _t590
            
            if deconstruct_result64 is not None:
                _t592 = self.pretty_undefine(deconstruct_result64)
                _t591 = _t592
            else:
                def _t593(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('context'):
                        _t594 = _dollar_dollar.context
                    else:
                        _t594 = None
                    return _t594
                _t595 = _t593(msg)
                deconstruct_result63 = _t595
                
                if deconstruct_result63 is not None:
                    _t597 = self.pretty_context(deconstruct_result63)
                    _t596 = _t597
                else:
                    raise ParseError('No matching rule for write')
                _t591 = _t596
            _t586 = _t591
        return _t586

    def pretty_define(self, msg: transactions_pb2.Define) -> Optional[NoReturn]:
        def _t598(_dollar_dollar):
            return _dollar_dollar.fragment
        _t599 = _t598(msg)
        fields66 = _t599
        assert fields66 is not None
        unwrapped_fields67 = fields66
        self.write('(')
        self.write('define')
        self.indent()
        self.newline()
        _t600 = self.pretty_fragment(unwrapped_fields67)
        self.dedent()
        self.write(')')
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> Optional[NoReturn]:
        def _t601(_dollar_dollar):
            _t602 = self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t603 = _t601(msg)
        fields68 = _t603
        assert fields68 is not None
        unwrapped_fields69 = fields68
        self.write('(')
        self.write('fragment')
        self.indent()
        self.newline()
        field70 = unwrapped_fields69[0]
        _t604 = self.pretty_new_fragment_id(field70)
        field71 = unwrapped_fields69[1]
        if not len(field71) == 0:
            self.newline()
            for i73, elem72 in enumerate(field71):
                if (i73 > 0):
                    self.newline()
                _t605 = self.pretty_declaration(elem72)
        self.dedent()
        self.write(')')
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> Optional[NoReturn]:
        def _t606(_dollar_dollar):
            return _dollar_dollar
        _t607 = _t606(msg)
        fields74 = _t607
        assert fields74 is not None
        unwrapped_fields75 = fields74
        _t608 = self.pretty_fragment_id(unwrapped_fields75)
        return _t608

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> Optional[NoReturn]:
        def _t609(_dollar_dollar):
            
            if _dollar_dollar.HasField('def'):
                _t610 = getattr(_dollar_dollar, 'def')
            else:
                _t610 = None
            return _t610
        _t611 = _t609(msg)
        deconstruct_result79 = _t611
        
        if deconstruct_result79 is not None:
            _t613 = self.pretty_def(deconstruct_result79)
            _t612 = _t613
        else:
            def _t614(_dollar_dollar):
                
                if _dollar_dollar.HasField('algorithm'):
                    _t615 = _dollar_dollar.algorithm
                else:
                    _t615 = None
                return _t615
            _t616 = _t614(msg)
            deconstruct_result78 = _t616
            
            if deconstruct_result78 is not None:
                _t618 = self.pretty_algorithm(deconstruct_result78)
                _t617 = _t618
            else:
                def _t619(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('constraint'):
                        _t620 = _dollar_dollar.constraint
                    else:
                        _t620 = None
                    return _t620
                _t621 = _t619(msg)
                deconstruct_result77 = _t621
                
                if deconstruct_result77 is not None:
                    _t623 = self.pretty_constraint(deconstruct_result77)
                    _t622 = _t623
                else:
                    def _t624(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('data'):
                            _t625 = _dollar_dollar.data
                        else:
                            _t625 = None
                        return _t625
                    _t626 = _t624(msg)
                    deconstruct_result76 = _t626
                    
                    if deconstruct_result76 is not None:
                        _t628 = self.pretty_data(deconstruct_result76)
                        _t627 = _t628
                    else:
                        raise ParseError('No matching rule for declaration')
                    _t622 = _t627
                _t617 = _t622
            _t612 = _t617
        return _t612

    def pretty_def(self, msg: logic_pb2.Def) -> Optional[NoReturn]:
        def _t629(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t630 = _dollar_dollar.attrs
            else:
                _t630 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t630,)
        _t631 = _t629(msg)
        fields80 = _t631
        assert fields80 is not None
        unwrapped_fields81 = fields80
        self.write('(')
        self.write('def')
        self.indent()
        self.newline()
        field82 = unwrapped_fields81[0]
        _t632 = self.pretty_relation_id(field82)
        self.newline()
        field83 = unwrapped_fields81[1]
        _t633 = self.pretty_abstraction(field83)
        field84 = unwrapped_fields81[2]
        
        if field84 is not None:
            self.newline()
            assert field84 is not None
            opt_val85 = field84
            _t635 = self.pretty_attrs(opt_val85)
            _t634 = _t635
        else:
            _t634 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> Optional[NoReturn]:
        def _t636(_dollar_dollar):
            _t637 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t637
        _t638 = _t636(msg)
        deconstruct_result87 = _t638
        if deconstruct_result87 is not None:
            self.write(':')
            self.write(deconstruct_result87)
        else:
            def _t639(_dollar_dollar):
                _t640 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t640
            _t641 = _t639(msg)
            deconstruct_result86 = _t641
            if deconstruct_result86 is not None:
                self.write(self.format_uint128(deconstruct_result86))
            else:
                raise ParseError('No matching rule for relation_id')
        return None

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> Optional[NoReturn]:
        def _t642(_dollar_dollar):
            _t643 = self.deconstruct_bindings(_dollar_dollar)
            return (_t643, _dollar_dollar.value,)
        _t644 = _t642(msg)
        fields88 = _t644
        assert fields88 is not None
        unwrapped_fields89 = fields88
        self.write('(')
        field90 = unwrapped_fields89[0]
        _t645 = self.pretty_bindings(field90)
        self.write(' ')
        field91 = unwrapped_fields89[1]
        _t646 = self.pretty_formula(field91)
        self.write(')')
        return None

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]) -> Optional[NoReturn]:
        def _t647(_dollar_dollar):
            
            if not len(_dollar_dollar[1]) == 0:
                _t648 = _dollar_dollar[1]
            else:
                _t648 = None
            return (_dollar_dollar[0], _t648,)
        _t649 = _t647(msg)
        fields92 = _t649
        assert fields92 is not None
        unwrapped_fields93 = fields92
        self.write('[')
        field94 = unwrapped_fields93[0]
        for i96, elem95 in enumerate(field94):
            if (i96 > 0):
                self.newline()
            _t650 = self.pretty_binding(elem95)
        field97 = unwrapped_fields93[1]
        
        if field97 is not None:
            self.write(' ')
            assert field97 is not None
            opt_val98 = field97
            _t652 = self.pretty_value_bindings(opt_val98)
            _t651 = _t652
        else:
            _t651 = None
        self.write(']')
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> Optional[NoReturn]:
        def _t653(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t654 = _t653(msg)
        fields99 = _t654
        assert fields99 is not None
        unwrapped_fields100 = fields99
        field101 = unwrapped_fields100[0]
        self.write(field101)
        self.write('::')
        field102 = unwrapped_fields100[1]
        _t655 = self.pretty_type(field102)
        return _t655

    def pretty_type(self, msg: logic_pb2.Type) -> Optional[NoReturn]:
        def _t656(_dollar_dollar):
            
            if _dollar_dollar.HasField('unspecified_type'):
                _t657 = _dollar_dollar.unspecified_type
            else:
                _t657 = None
            return _t657
        _t658 = _t656(msg)
        deconstruct_result113 = _t658
        
        if deconstruct_result113 is not None:
            _t660 = self.pretty_unspecified_type(deconstruct_result113)
            _t659 = _t660
        else:
            def _t661(_dollar_dollar):
                
                if _dollar_dollar.HasField('string_type'):
                    _t662 = _dollar_dollar.string_type
                else:
                    _t662 = None
                return _t662
            _t663 = _t661(msg)
            deconstruct_result112 = _t663
            
            if deconstruct_result112 is not None:
                _t665 = self.pretty_string_type(deconstruct_result112)
                _t664 = _t665
            else:
                def _t666(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('int_type'):
                        _t667 = _dollar_dollar.int_type
                    else:
                        _t667 = None
                    return _t667
                _t668 = _t666(msg)
                deconstruct_result111 = _t668
                
                if deconstruct_result111 is not None:
                    _t670 = self.pretty_int_type(deconstruct_result111)
                    _t669 = _t670
                else:
                    def _t671(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('float_type'):
                            _t672 = _dollar_dollar.float_type
                        else:
                            _t672 = None
                        return _t672
                    _t673 = _t671(msg)
                    deconstruct_result110 = _t673
                    
                    if deconstruct_result110 is not None:
                        _t675 = self.pretty_float_type(deconstruct_result110)
                        _t674 = _t675
                    else:
                        def _t676(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('uint128_type'):
                                _t677 = _dollar_dollar.uint128_type
                            else:
                                _t677 = None
                            return _t677
                        _t678 = _t676(msg)
                        deconstruct_result109 = _t678
                        
                        if deconstruct_result109 is not None:
                            _t680 = self.pretty_uint128_type(deconstruct_result109)
                            _t679 = _t680
                        else:
                            def _t681(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('int128_type'):
                                    _t682 = _dollar_dollar.int128_type
                                else:
                                    _t682 = None
                                return _t682
                            _t683 = _t681(msg)
                            deconstruct_result108 = _t683
                            
                            if deconstruct_result108 is not None:
                                _t685 = self.pretty_int128_type(deconstruct_result108)
                                _t684 = _t685
                            else:
                                def _t686(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('date_type'):
                                        _t687 = _dollar_dollar.date_type
                                    else:
                                        _t687 = None
                                    return _t687
                                _t688 = _t686(msg)
                                deconstruct_result107 = _t688
                                
                                if deconstruct_result107 is not None:
                                    _t690 = self.pretty_date_type(deconstruct_result107)
                                    _t689 = _t690
                                else:
                                    def _t691(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('datetime_type'):
                                            _t692 = _dollar_dollar.datetime_type
                                        else:
                                            _t692 = None
                                        return _t692
                                    _t693 = _t691(msg)
                                    deconstruct_result106 = _t693
                                    
                                    if deconstruct_result106 is not None:
                                        _t695 = self.pretty_datetime_type(deconstruct_result106)
                                        _t694 = _t695
                                    else:
                                        def _t696(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('missing_type'):
                                                _t697 = _dollar_dollar.missing_type
                                            else:
                                                _t697 = None
                                            return _t697
                                        _t698 = _t696(msg)
                                        deconstruct_result105 = _t698
                                        
                                        if deconstruct_result105 is not None:
                                            _t700 = self.pretty_missing_type(deconstruct_result105)
                                            _t699 = _t700
                                        else:
                                            def _t701(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('decimal_type'):
                                                    _t702 = _dollar_dollar.decimal_type
                                                else:
                                                    _t702 = None
                                                return _t702
                                            _t703 = _t701(msg)
                                            deconstruct_result104 = _t703
                                            
                                            if deconstruct_result104 is not None:
                                                _t705 = self.pretty_decimal_type(deconstruct_result104)
                                                _t704 = _t705
                                            else:
                                                def _t706(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('boolean_type'):
                                                        _t707 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t707 = None
                                                    return _t707
                                                _t708 = _t706(msg)
                                                deconstruct_result103 = _t708
                                                
                                                if deconstruct_result103 is not None:
                                                    _t710 = self.pretty_boolean_type(deconstruct_result103)
                                                    _t709 = _t710
                                                else:
                                                    raise ParseError('No matching rule for type')
                                                _t704 = _t709
                                            _t699 = _t704
                                        _t694 = _t699
                                    _t689 = _t694
                                _t684 = _t689
                            _t679 = _t684
                        _t674 = _t679
                    _t669 = _t674
                _t664 = _t669
            _t659 = _t664
        return _t659

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> Optional[NoReturn]:
        def _t711(_dollar_dollar):
            return _dollar_dollar
        _t712 = _t711(msg)
        fields114 = _t712
        assert fields114 is not None
        unwrapped_fields115 = fields114
        self.write('UNKNOWN')
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> Optional[NoReturn]:
        def _t713(_dollar_dollar):
            return _dollar_dollar
        _t714 = _t713(msg)
        fields116 = _t714
        assert fields116 is not None
        unwrapped_fields117 = fields116
        self.write('STRING')
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> Optional[NoReturn]:
        def _t715(_dollar_dollar):
            return _dollar_dollar
        _t716 = _t715(msg)
        fields118 = _t716
        assert fields118 is not None
        unwrapped_fields119 = fields118
        self.write('INT')
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> Optional[NoReturn]:
        def _t717(_dollar_dollar):
            return _dollar_dollar
        _t718 = _t717(msg)
        fields120 = _t718
        assert fields120 is not None
        unwrapped_fields121 = fields120
        self.write('FLOAT')
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> Optional[NoReturn]:
        def _t719(_dollar_dollar):
            return _dollar_dollar
        _t720 = _t719(msg)
        fields122 = _t720
        assert fields122 is not None
        unwrapped_fields123 = fields122
        self.write('UINT128')
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> Optional[NoReturn]:
        def _t721(_dollar_dollar):
            return _dollar_dollar
        _t722 = _t721(msg)
        fields124 = _t722
        assert fields124 is not None
        unwrapped_fields125 = fields124
        self.write('INT128')
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> Optional[NoReturn]:
        def _t723(_dollar_dollar):
            return _dollar_dollar
        _t724 = _t723(msg)
        fields126 = _t724
        assert fields126 is not None
        unwrapped_fields127 = fields126
        self.write('DATE')
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> Optional[NoReturn]:
        def _t725(_dollar_dollar):
            return _dollar_dollar
        _t726 = _t725(msg)
        fields128 = _t726
        assert fields128 is not None
        unwrapped_fields129 = fields128
        self.write('DATETIME')
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> Optional[NoReturn]:
        def _t727(_dollar_dollar):
            return _dollar_dollar
        _t728 = _t727(msg)
        fields130 = _t728
        assert fields130 is not None
        unwrapped_fields131 = fields130
        self.write('MISSING')
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> Optional[NoReturn]:
        def _t729(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t730 = _t729(msg)
        fields132 = _t730
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
        def _t731(_dollar_dollar):
            return _dollar_dollar
        _t732 = _t731(msg)
        fields136 = _t732
        assert fields136 is not None
        unwrapped_fields137 = fields136
        self.write('BOOLEAN')
        return None

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]) -> Optional[NoReturn]:
        def _t733(_dollar_dollar):
            return _dollar_dollar
        _t734 = _t733(msg)
        fields138 = _t734
        assert fields138 is not None
        unwrapped_fields139 = fields138
        self.write('|')
        if not len(unwrapped_fields139) == 0:
            self.write(' ')
            for i141, elem140 in enumerate(unwrapped_fields139):
                if (i141 > 0):
                    self.newline()
                _t735 = self.pretty_binding(elem140)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> Optional[NoReturn]:
        def _t736(_dollar_dollar):
            
            if (_dollar_dollar.HasField('conjunction') and len(_dollar_dollar.conjunction.args) == 0):
                _t737 = _dollar_dollar.conjunction
            else:
                _t737 = None
            return _t737
        _t738 = _t736(msg)
        deconstruct_result154 = _t738
        
        if deconstruct_result154 is not None:
            _t740 = self.pretty_true(deconstruct_result154)
            _t739 = _t740
        else:
            def _t741(_dollar_dollar):
                
                if (_dollar_dollar.HasField('disjunction') and len(_dollar_dollar.disjunction.args) == 0):
                    _t742 = _dollar_dollar.disjunction
                else:
                    _t742 = None
                return _t742
            _t743 = _t741(msg)
            deconstruct_result153 = _t743
            
            if deconstruct_result153 is not None:
                _t745 = self.pretty_false(deconstruct_result153)
                _t744 = _t745
            else:
                def _t746(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('exists'):
                        _t747 = _dollar_dollar.exists
                    else:
                        _t747 = None
                    return _t747
                _t748 = _t746(msg)
                deconstruct_result152 = _t748
                
                if deconstruct_result152 is not None:
                    _t750 = self.pretty_exists(deconstruct_result152)
                    _t749 = _t750
                else:
                    def _t751(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('reduce'):
                            _t752 = _dollar_dollar.reduce
                        else:
                            _t752 = None
                        return _t752
                    _t753 = _t751(msg)
                    deconstruct_result151 = _t753
                    
                    if deconstruct_result151 is not None:
                        _t755 = self.pretty_reduce(deconstruct_result151)
                        _t754 = _t755
                    else:
                        def _t756(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('conjunction'):
                                _t757 = _dollar_dollar.conjunction
                            else:
                                _t757 = None
                            return _t757
                        _t758 = _t756(msg)
                        deconstruct_result150 = _t758
                        
                        if deconstruct_result150 is not None:
                            _t760 = self.pretty_conjunction(deconstruct_result150)
                            _t759 = _t760
                        else:
                            def _t761(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('disjunction'):
                                    _t762 = _dollar_dollar.disjunction
                                else:
                                    _t762 = None
                                return _t762
                            _t763 = _t761(msg)
                            deconstruct_result149 = _t763
                            
                            if deconstruct_result149 is not None:
                                _t765 = self.pretty_disjunction(deconstruct_result149)
                                _t764 = _t765
                            else:
                                def _t766(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('not'):
                                        _t767 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t767 = None
                                    return _t767
                                _t768 = _t766(msg)
                                deconstruct_result148 = _t768
                                
                                if deconstruct_result148 is not None:
                                    _t770 = self.pretty_not(deconstruct_result148)
                                    _t769 = _t770
                                else:
                                    def _t771(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('ffi'):
                                            _t772 = _dollar_dollar.ffi
                                        else:
                                            _t772 = None
                                        return _t772
                                    _t773 = _t771(msg)
                                    deconstruct_result147 = _t773
                                    
                                    if deconstruct_result147 is not None:
                                        _t775 = self.pretty_ffi(deconstruct_result147)
                                        _t774 = _t775
                                    else:
                                        def _t776(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('atom'):
                                                _t777 = _dollar_dollar.atom
                                            else:
                                                _t777 = None
                                            return _t777
                                        _t778 = _t776(msg)
                                        deconstruct_result146 = _t778
                                        
                                        if deconstruct_result146 is not None:
                                            _t780 = self.pretty_atom(deconstruct_result146)
                                            _t779 = _t780
                                        else:
                                            def _t781(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('pragma'):
                                                    _t782 = _dollar_dollar.pragma
                                                else:
                                                    _t782 = None
                                                return _t782
                                            _t783 = _t781(msg)
                                            deconstruct_result145 = _t783
                                            
                                            if deconstruct_result145 is not None:
                                                _t785 = self.pretty_pragma(deconstruct_result145)
                                                _t784 = _t785
                                            else:
                                                def _t786(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('primitive'):
                                                        _t787 = _dollar_dollar.primitive
                                                    else:
                                                        _t787 = None
                                                    return _t787
                                                _t788 = _t786(msg)
                                                deconstruct_result144 = _t788
                                                
                                                if deconstruct_result144 is not None:
                                                    _t790 = self.pretty_primitive(deconstruct_result144)
                                                    _t789 = _t790
                                                else:
                                                    def _t791(_dollar_dollar):
                                                        
                                                        if _dollar_dollar.HasField('rel_atom'):
                                                            _t792 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t792 = None
                                                        return _t792
                                                    _t793 = _t791(msg)
                                                    deconstruct_result143 = _t793
                                                    
                                                    if deconstruct_result143 is not None:
                                                        _t795 = self.pretty_rel_atom(deconstruct_result143)
                                                        _t794 = _t795
                                                    else:
                                                        def _t796(_dollar_dollar):
                                                            
                                                            if _dollar_dollar.HasField('cast'):
                                                                _t797 = _dollar_dollar.cast
                                                            else:
                                                                _t797 = None
                                                            return _t797
                                                        _t798 = _t796(msg)
                                                        deconstruct_result142 = _t798
                                                        
                                                        if deconstruct_result142 is not None:
                                                            _t800 = self.pretty_cast(deconstruct_result142)
                                                            _t799 = _t800
                                                        else:
                                                            raise ParseError('No matching rule for formula')
                                                        _t794 = _t799
                                                    _t789 = _t794
                                                _t784 = _t789
                                            _t779 = _t784
                                        _t774 = _t779
                                    _t769 = _t774
                                _t764 = _t769
                            _t759 = _t764
                        _t754 = _t759
                    _t749 = _t754
                _t744 = _t749
            _t739 = _t744
        return _t739

    def pretty_true(self, msg: logic_pb2.Conjunction) -> Optional[NoReturn]:
        def _t801(_dollar_dollar):
            return _dollar_dollar
        _t802 = _t801(msg)
        fields155 = _t802
        assert fields155 is not None
        unwrapped_fields156 = fields155
        self.write('(')
        self.write('true')
        self.write(')')
        return None

    def pretty_false(self, msg: logic_pb2.Disjunction) -> Optional[NoReturn]:
        def _t803(_dollar_dollar):
            return _dollar_dollar
        _t804 = _t803(msg)
        fields157 = _t804
        assert fields157 is not None
        unwrapped_fields158 = fields157
        self.write('(')
        self.write('false')
        self.write(')')
        return None

    def pretty_exists(self, msg: logic_pb2.Exists) -> Optional[NoReturn]:
        def _t805(_dollar_dollar):
            _t806 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t806, _dollar_dollar.body.value,)
        _t807 = _t805(msg)
        fields159 = _t807
        assert fields159 is not None
        unwrapped_fields160 = fields159
        self.write('(')
        self.write('exists')
        self.indent()
        self.newline()
        field161 = unwrapped_fields160[0]
        _t808 = self.pretty_bindings(field161)
        self.newline()
        field162 = unwrapped_fields160[1]
        _t809 = self.pretty_formula(field162)
        self.dedent()
        self.write(')')
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> Optional[NoReturn]:
        def _t810(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t811 = _t810(msg)
        fields163 = _t811
        assert fields163 is not None
        unwrapped_fields164 = fields163
        self.write('(')
        self.write('reduce')
        self.indent()
        self.newline()
        field165 = unwrapped_fields164[0]
        _t812 = self.pretty_abstraction(field165)
        self.newline()
        field166 = unwrapped_fields164[1]
        _t813 = self.pretty_abstraction(field166)
        self.newline()
        field167 = unwrapped_fields164[2]
        _t814 = self.pretty_terms(field167)
        self.dedent()
        self.write(')')
        return None

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]) -> Optional[NoReturn]:
        def _t815(_dollar_dollar):
            return _dollar_dollar
        _t816 = _t815(msg)
        fields168 = _t816
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
                _t817 = self.pretty_term(elem170)
        self.dedent()
        self.write(')')
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> Optional[NoReturn]:
        def _t818(_dollar_dollar):
            
            if _dollar_dollar.HasField('var'):
                _t819 = _dollar_dollar.var
            else:
                _t819 = None
            return _t819
        _t820 = _t818(msg)
        deconstruct_result173 = _t820
        
        if deconstruct_result173 is not None:
            _t822 = self.pretty_var(deconstruct_result173)
            _t821 = _t822
        else:
            def _t823(_dollar_dollar):
                
                if _dollar_dollar.HasField('constant'):
                    _t824 = _dollar_dollar.constant
                else:
                    _t824 = None
                return _t824
            _t825 = _t823(msg)
            deconstruct_result172 = _t825
            
            if deconstruct_result172 is not None:
                _t827 = self.pretty_constant(deconstruct_result172)
                _t826 = _t827
            else:
                raise ParseError('No matching rule for term')
            _t821 = _t826
        return _t821

    def pretty_var(self, msg: logic_pb2.Var) -> Optional[NoReturn]:
        def _t828(_dollar_dollar):
            return _dollar_dollar.name
        _t829 = _t828(msg)
        fields174 = _t829
        assert fields174 is not None
        unwrapped_fields175 = fields174
        self.write(unwrapped_fields175)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> Optional[NoReturn]:
        def _t830(_dollar_dollar):
            return _dollar_dollar
        _t831 = _t830(msg)
        fields176 = _t831
        assert fields176 is not None
        unwrapped_fields177 = fields176
        _t832 = self.pretty_value(unwrapped_fields177)
        return _t832

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> Optional[NoReturn]:
        def _t833(_dollar_dollar):
            return _dollar_dollar.args
        _t834 = _t833(msg)
        fields178 = _t834
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
                _t835 = self.pretty_formula(elem180)
        self.dedent()
        self.write(')')
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> Optional[NoReturn]:
        def _t836(_dollar_dollar):
            return _dollar_dollar.args
        _t837 = _t836(msg)
        fields182 = _t837
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
                _t838 = self.pretty_formula(elem184)
        self.dedent()
        self.write(')')
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> Optional[NoReturn]:
        def _t839(_dollar_dollar):
            return _dollar_dollar.arg
        _t840 = _t839(msg)
        fields186 = _t840
        assert fields186 is not None
        unwrapped_fields187 = fields186
        self.write('(')
        self.write('not')
        self.indent()
        self.newline()
        _t841 = self.pretty_formula(unwrapped_fields187)
        self.dedent()
        self.write(')')
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> Optional[NoReturn]:
        def _t842(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t843 = _t842(msg)
        fields188 = _t843
        assert fields188 is not None
        unwrapped_fields189 = fields188
        self.write('(')
        self.write('ffi')
        self.indent()
        self.newline()
        field190 = unwrapped_fields189[0]
        _t844 = self.pretty_name(field190)
        self.newline()
        field191 = unwrapped_fields189[1]
        _t845 = self.pretty_ffi_args(field191)
        self.newline()
        field192 = unwrapped_fields189[2]
        _t846 = self.pretty_terms(field192)
        self.dedent()
        self.write(')')
        return None

    def pretty_name(self, msg: str) -> Optional[NoReturn]:
        def _t847(_dollar_dollar):
            return _dollar_dollar
        _t848 = _t847(msg)
        fields193 = _t848
        assert fields193 is not None
        unwrapped_fields194 = fields193
        self.write(':')
        self.write(unwrapped_fields194)
        return None

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]) -> Optional[NoReturn]:
        def _t849(_dollar_dollar):
            return _dollar_dollar
        _t850 = _t849(msg)
        fields195 = _t850
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
                _t851 = self.pretty_abstraction(elem197)
        self.dedent()
        self.write(')')
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> Optional[NoReturn]:
        def _t852(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t853 = _t852(msg)
        fields199 = _t853
        assert fields199 is not None
        unwrapped_fields200 = fields199
        self.write('(')
        self.write('atom')
        self.indent()
        self.newline()
        field201 = unwrapped_fields200[0]
        _t854 = self.pretty_relation_id(field201)
        field202 = unwrapped_fields200[1]
        if not len(field202) == 0:
            self.newline()
            for i204, elem203 in enumerate(field202):
                if (i204 > 0):
                    self.newline()
                _t855 = self.pretty_term(elem203)
        self.dedent()
        self.write(')')
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> Optional[NoReturn]:
        def _t856(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t857 = _t856(msg)
        fields205 = _t857
        assert fields205 is not None
        unwrapped_fields206 = fields205
        self.write('(')
        self.write('pragma')
        self.indent()
        self.newline()
        field207 = unwrapped_fields206[0]
        _t858 = self.pretty_name(field207)
        field208 = unwrapped_fields206[1]
        if not len(field208) == 0:
            self.newline()
            for i210, elem209 in enumerate(field208):
                if (i210 > 0):
                    self.newline()
                _t859 = self.pretty_term(elem209)
        self.dedent()
        self.write(')')
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t860(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t861 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t861 = None
            return _t861
        _t862 = _t860(msg)
        guard_result225 = _t862
        
        if guard_result225 is not None:
            _t864 = self.pretty_eq(msg)
            _t863 = _t864
        else:
            def _t865(_dollar_dollar):
                
                if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                    _t866 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t866 = None
                return _t866
            _t867 = _t865(msg)
            guard_result224 = _t867
            
            if guard_result224 is not None:
                _t869 = self.pretty_lt(msg)
                _t868 = _t869
            else:
                def _t870(_dollar_dollar):
                    
                    if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                        _t871 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t871 = None
                    return _t871
                _t872 = _t870(msg)
                guard_result223 = _t872
                
                if guard_result223 is not None:
                    _t874 = self.pretty_lt_eq(msg)
                    _t873 = _t874
                else:
                    def _t875(_dollar_dollar):
                        
                        if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                            _t876 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t876 = None
                        return _t876
                    _t877 = _t875(msg)
                    guard_result222 = _t877
                    
                    if guard_result222 is not None:
                        _t879 = self.pretty_gt(msg)
                        _t878 = _t879
                    else:
                        def _t880(_dollar_dollar):
                            
                            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                                _t881 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t881 = None
                            return _t881
                        _t882 = _t880(msg)
                        guard_result221 = _t882
                        
                        if guard_result221 is not None:
                            _t884 = self.pretty_gt_eq(msg)
                            _t883 = _t884
                        else:
                            def _t885(_dollar_dollar):
                                
                                if _dollar_dollar.name == 'rel_primitive_add_monotype':
                                    _t886 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t886 = None
                                return _t886
                            _t887 = _t885(msg)
                            guard_result220 = _t887
                            
                            if guard_result220 is not None:
                                _t889 = self.pretty_add(msg)
                                _t888 = _t889
                            else:
                                def _t890(_dollar_dollar):
                                    
                                    if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                                        _t891 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t891 = None
                                    return _t891
                                _t892 = _t890(msg)
                                guard_result219 = _t892
                                
                                if guard_result219 is not None:
                                    _t894 = self.pretty_minus(msg)
                                    _t893 = _t894
                                else:
                                    def _t895(_dollar_dollar):
                                        
                                        if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                                            _t896 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t896 = None
                                        return _t896
                                    _t897 = _t895(msg)
                                    guard_result218 = _t897
                                    
                                    if guard_result218 is not None:
                                        _t899 = self.pretty_multiply(msg)
                                        _t898 = _t899
                                    else:
                                        def _t900(_dollar_dollar):
                                            
                                            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                                                _t901 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t901 = None
                                            return _t901
                                        _t902 = _t900(msg)
                                        guard_result217 = _t902
                                        
                                        if guard_result217 is not None:
                                            _t904 = self.pretty_divide(msg)
                                            _t903 = _t904
                                        else:
                                            def _t905(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t906 = _t905(msg)
                                            fields211 = _t906
                                            assert fields211 is not None
                                            unwrapped_fields212 = fields211
                                            self.write('(')
                                            self.write('primitive')
                                            self.indent()
                                            self.newline()
                                            field213 = unwrapped_fields212[0]
                                            _t907 = self.pretty_name(field213)
                                            field214 = unwrapped_fields212[1]
                                            if not len(field214) == 0:
                                                self.newline()
                                                for i216, elem215 in enumerate(field214):
                                                    if (i216 > 0):
                                                        self.newline()
                                                    _t908 = self.pretty_rel_term(elem215)
                                            self.dedent()
                                            self.write(')')
                                            _t903 = None
                                        _t898 = _t903
                                    _t893 = _t898
                                _t888 = _t893
                            _t883 = _t888
                        _t878 = _t883
                    _t873 = _t878
                _t868 = _t873
            _t863 = _t868
        return _t863

    def pretty_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t909(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t910 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t910 = None
            return _t910
        _t911 = _t909(msg)
        fields226 = _t911
        assert fields226 is not None
        unwrapped_fields227 = fields226
        self.write('(')
        self.write('=')
        self.indent()
        self.newline()
        field228 = unwrapped_fields227[0]
        _t912 = self.pretty_term(field228)
        self.newline()
        field229 = unwrapped_fields227[1]
        _t913 = self.pretty_term(field229)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t914(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                _t915 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t915 = None
            return _t915
        _t916 = _t914(msg)
        fields230 = _t916
        assert fields230 is not None
        unwrapped_fields231 = fields230
        self.write('(')
        self.write('<')
        self.indent()
        self.newline()
        field232 = unwrapped_fields231[0]
        _t917 = self.pretty_term(field232)
        self.newline()
        field233 = unwrapped_fields231[1]
        _t918 = self.pretty_term(field233)
        self.dedent()
        self.write(')')
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t919(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                _t920 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t920 = None
            return _t920
        _t921 = _t919(msg)
        fields234 = _t921
        assert fields234 is not None
        unwrapped_fields235 = fields234
        self.write('(')
        self.write('<=')
        self.indent()
        self.newline()
        field236 = unwrapped_fields235[0]
        _t922 = self.pretty_term(field236)
        self.newline()
        field237 = unwrapped_fields235[1]
        _t923 = self.pretty_term(field237)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t924(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                _t925 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t925 = None
            return _t925
        _t926 = _t924(msg)
        fields238 = _t926
        assert fields238 is not None
        unwrapped_fields239 = fields238
        self.write('(')
        self.write('>')
        self.indent()
        self.newline()
        field240 = unwrapped_fields239[0]
        _t927 = self.pretty_term(field240)
        self.newline()
        field241 = unwrapped_fields239[1]
        _t928 = self.pretty_term(field241)
        self.dedent()
        self.write(')')
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t929(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                _t930 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t930 = None
            return _t930
        _t931 = _t929(msg)
        fields242 = _t931
        assert fields242 is not None
        unwrapped_fields243 = fields242
        self.write('(')
        self.write('>=')
        self.indent()
        self.newline()
        field244 = unwrapped_fields243[0]
        _t932 = self.pretty_term(field244)
        self.newline()
        field245 = unwrapped_fields243[1]
        _t933 = self.pretty_term(field245)
        self.dedent()
        self.write(')')
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t934(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_add_monotype':
                _t935 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t935 = None
            return _t935
        _t936 = _t934(msg)
        fields246 = _t936
        assert fields246 is not None
        unwrapped_fields247 = fields246
        self.write('(')
        self.write('+')
        self.indent()
        self.newline()
        field248 = unwrapped_fields247[0]
        _t937 = self.pretty_term(field248)
        self.newline()
        field249 = unwrapped_fields247[1]
        _t938 = self.pretty_term(field249)
        self.newline()
        field250 = unwrapped_fields247[2]
        _t939 = self.pretty_term(field250)
        self.dedent()
        self.write(')')
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t940(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                _t941 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t941 = None
            return _t941
        _t942 = _t940(msg)
        fields251 = _t942
        assert fields251 is not None
        unwrapped_fields252 = fields251
        self.write('(')
        self.write('-')
        self.indent()
        self.newline()
        field253 = unwrapped_fields252[0]
        _t943 = self.pretty_term(field253)
        self.newline()
        field254 = unwrapped_fields252[1]
        _t944 = self.pretty_term(field254)
        self.newline()
        field255 = unwrapped_fields252[2]
        _t945 = self.pretty_term(field255)
        self.dedent()
        self.write(')')
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t946(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                _t947 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t947 = None
            return _t947
        _t948 = _t946(msg)
        fields256 = _t948
        assert fields256 is not None
        unwrapped_fields257 = fields256
        self.write('(')
        self.write('*')
        self.indent()
        self.newline()
        field258 = unwrapped_fields257[0]
        _t949 = self.pretty_term(field258)
        self.newline()
        field259 = unwrapped_fields257[1]
        _t950 = self.pretty_term(field259)
        self.newline()
        field260 = unwrapped_fields257[2]
        _t951 = self.pretty_term(field260)
        self.dedent()
        self.write(')')
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> Optional[NoReturn]:
        def _t952(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                _t953 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t953 = None
            return _t953
        _t954 = _t952(msg)
        fields261 = _t954
        assert fields261 is not None
        unwrapped_fields262 = fields261
        self.write('(')
        self.write('/')
        self.indent()
        self.newline()
        field263 = unwrapped_fields262[0]
        _t955 = self.pretty_term(field263)
        self.newline()
        field264 = unwrapped_fields262[1]
        _t956 = self.pretty_term(field264)
        self.newline()
        field265 = unwrapped_fields262[2]
        _t957 = self.pretty_term(field265)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> Optional[NoReturn]:
        def _t958(_dollar_dollar):
            
            if _dollar_dollar.HasField('specialized_value'):
                _t959 = _dollar_dollar.specialized_value
            else:
                _t959 = None
            return _t959
        _t960 = _t958(msg)
        deconstruct_result267 = _t960
        
        if deconstruct_result267 is not None:
            _t962 = self.pretty_specialized_value(deconstruct_result267)
            _t961 = _t962
        else:
            def _t963(_dollar_dollar):
                
                if _dollar_dollar.HasField('term'):
                    _t964 = _dollar_dollar.term
                else:
                    _t964 = None
                return _t964
            _t965 = _t963(msg)
            deconstruct_result266 = _t965
            
            if deconstruct_result266 is not None:
                _t967 = self.pretty_term(deconstruct_result266)
                _t966 = _t967
            else:
                raise ParseError('No matching rule for rel_term')
            _t961 = _t966
        return _t961

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> Optional[NoReturn]:
        def _t968(_dollar_dollar):
            return _dollar_dollar
        _t969 = _t968(msg)
        fields268 = _t969
        assert fields268 is not None
        unwrapped_fields269 = fields268
        self.write('#')
        _t970 = self.pretty_value(unwrapped_fields269)
        return _t970

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> Optional[NoReturn]:
        def _t971(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t972 = _t971(msg)
        fields270 = _t972
        assert fields270 is not None
        unwrapped_fields271 = fields270
        self.write('(')
        self.write('relatom')
        self.indent()
        self.newline()
        field272 = unwrapped_fields271[0]
        _t973 = self.pretty_name(field272)
        field273 = unwrapped_fields271[1]
        if not len(field273) == 0:
            self.newline()
            for i275, elem274 in enumerate(field273):
                if (i275 > 0):
                    self.newline()
                _t974 = self.pretty_rel_term(elem274)
        self.dedent()
        self.write(')')
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> Optional[NoReturn]:
        def _t975(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t976 = _t975(msg)
        fields276 = _t976
        assert fields276 is not None
        unwrapped_fields277 = fields276
        self.write('(')
        self.write('cast')
        self.indent()
        self.newline()
        field278 = unwrapped_fields277[0]
        _t977 = self.pretty_term(field278)
        self.newline()
        field279 = unwrapped_fields277[1]
        _t978 = self.pretty_term(field279)
        self.dedent()
        self.write(')')
        return None

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]) -> Optional[NoReturn]:
        def _t979(_dollar_dollar):
            return _dollar_dollar
        _t980 = _t979(msg)
        fields280 = _t980
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
                _t981 = self.pretty_attribute(elem282)
        self.dedent()
        self.write(')')
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> Optional[NoReturn]:
        def _t982(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t983 = _t982(msg)
        fields284 = _t983
        assert fields284 is not None
        unwrapped_fields285 = fields284
        self.write('(')
        self.write('attribute')
        self.indent()
        self.newline()
        field286 = unwrapped_fields285[0]
        _t984 = self.pretty_name(field286)
        field287 = unwrapped_fields285[1]
        if not len(field287) == 0:
            self.newline()
            for i289, elem288 in enumerate(field287):
                if (i289 > 0):
                    self.newline()
                _t985 = self.pretty_value(elem288)
        self.dedent()
        self.write(')')
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> Optional[NoReturn]:
        def _t986(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t987 = _t986(msg)
        fields290 = _t987
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
                _t988 = self.pretty_relation_id(elem293)
        self.newline()
        field295 = unwrapped_fields291[1]
        _t989 = self.pretty_script(field295)
        self.dedent()
        self.write(')')
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> Optional[NoReturn]:
        def _t990(_dollar_dollar):
            return _dollar_dollar.constructs
        _t991 = _t990(msg)
        fields296 = _t991
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
                _t992 = self.pretty_construct(elem298)
        self.dedent()
        self.write(')')
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> Optional[NoReturn]:
        def _t993(_dollar_dollar):
            
            if _dollar_dollar.HasField('loop'):
                _t994 = _dollar_dollar.loop
            else:
                _t994 = None
            return _t994
        _t995 = _t993(msg)
        deconstruct_result301 = _t995
        
        if deconstruct_result301 is not None:
            _t997 = self.pretty_loop(deconstruct_result301)
            _t996 = _t997
        else:
            def _t998(_dollar_dollar):
                
                if _dollar_dollar.HasField('instruction'):
                    _t999 = _dollar_dollar.instruction
                else:
                    _t999 = None
                return _t999
            _t1000 = _t998(msg)
            deconstruct_result300 = _t1000
            
            if deconstruct_result300 is not None:
                _t1002 = self.pretty_instruction(deconstruct_result300)
                _t1001 = _t1002
            else:
                raise ParseError('No matching rule for construct')
            _t996 = _t1001
        return _t996

    def pretty_loop(self, msg: logic_pb2.Loop) -> Optional[NoReturn]:
        def _t1003(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t1004 = _t1003(msg)
        fields302 = _t1004
        assert fields302 is not None
        unwrapped_fields303 = fields302
        self.write('(')
        self.write('loop')
        self.indent()
        self.newline()
        field304 = unwrapped_fields303[0]
        _t1005 = self.pretty_init(field304)
        self.newline()
        field305 = unwrapped_fields303[1]
        _t1006 = self.pretty_script(field305)
        self.dedent()
        self.write(')')
        return None

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]) -> Optional[NoReturn]:
        def _t1007(_dollar_dollar):
            return _dollar_dollar
        _t1008 = _t1007(msg)
        fields306 = _t1008
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
                _t1009 = self.pretty_instruction(elem308)
        self.dedent()
        self.write(')')
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> Optional[NoReturn]:
        def _t1010(_dollar_dollar):
            
            if _dollar_dollar.HasField('assign'):
                _t1011 = _dollar_dollar.assign
            else:
                _t1011 = None
            return _t1011
        _t1012 = _t1010(msg)
        deconstruct_result314 = _t1012
        
        if deconstruct_result314 is not None:
            _t1014 = self.pretty_assign(deconstruct_result314)
            _t1013 = _t1014
        else:
            def _t1015(_dollar_dollar):
                
                if _dollar_dollar.HasField('upsert'):
                    _t1016 = _dollar_dollar.upsert
                else:
                    _t1016 = None
                return _t1016
            _t1017 = _t1015(msg)
            deconstruct_result313 = _t1017
            
            if deconstruct_result313 is not None:
                _t1019 = self.pretty_upsert(deconstruct_result313)
                _t1018 = _t1019
            else:
                def _t1020(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('break'):
                        _t1021 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1021 = None
                    return _t1021
                _t1022 = _t1020(msg)
                deconstruct_result312 = _t1022
                
                if deconstruct_result312 is not None:
                    _t1024 = self.pretty_break(deconstruct_result312)
                    _t1023 = _t1024
                else:
                    def _t1025(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('monoid_def'):
                            _t1026 = _dollar_dollar.monoid_def
                        else:
                            _t1026 = None
                        return _t1026
                    _t1027 = _t1025(msg)
                    deconstruct_result311 = _t1027
                    
                    if deconstruct_result311 is not None:
                        _t1029 = self.pretty_monoid_def(deconstruct_result311)
                        _t1028 = _t1029
                    else:
                        def _t1030(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('monus_def'):
                                _t1031 = _dollar_dollar.monus_def
                            else:
                                _t1031 = None
                            return _t1031
                        _t1032 = _t1030(msg)
                        deconstruct_result310 = _t1032
                        
                        if deconstruct_result310 is not None:
                            _t1034 = self.pretty_monus_def(deconstruct_result310)
                            _t1033 = _t1034
                        else:
                            raise ParseError('No matching rule for instruction')
                        _t1028 = _t1033
                    _t1023 = _t1028
                _t1018 = _t1023
            _t1013 = _t1018
        return _t1013

    def pretty_assign(self, msg: logic_pb2.Assign) -> Optional[NoReturn]:
        def _t1035(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1036 = _dollar_dollar.attrs
            else:
                _t1036 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1036,)
        _t1037 = _t1035(msg)
        fields315 = _t1037
        assert fields315 is not None
        unwrapped_fields316 = fields315
        self.write('(')
        self.write('assign')
        self.indent()
        self.newline()
        field317 = unwrapped_fields316[0]
        _t1038 = self.pretty_relation_id(field317)
        self.newline()
        field318 = unwrapped_fields316[1]
        _t1039 = self.pretty_abstraction(field318)
        field319 = unwrapped_fields316[2]
        
        if field319 is not None:
            self.newline()
            assert field319 is not None
            opt_val320 = field319
            _t1041 = self.pretty_attrs(opt_val320)
            _t1040 = _t1041
        else:
            _t1040 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> Optional[NoReturn]:
        def _t1042(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1043 = _dollar_dollar.attrs
            else:
                _t1043 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1043,)
        _t1044 = _t1042(msg)
        fields321 = _t1044
        assert fields321 is not None
        unwrapped_fields322 = fields321
        self.write('(')
        self.write('upsert')
        self.indent()
        self.newline()
        field323 = unwrapped_fields322[0]
        _t1045 = self.pretty_relation_id(field323)
        self.newline()
        field324 = unwrapped_fields322[1]
        _t1046 = self.pretty_abstraction_with_arity(field324)
        field325 = unwrapped_fields322[2]
        
        if field325 is not None:
            self.newline()
            assert field325 is not None
            opt_val326 = field325
            _t1048 = self.pretty_attrs(opt_val326)
            _t1047 = _t1048
        else:
            _t1047 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> Optional[NoReturn]:
        def _t1049(_dollar_dollar):
            _t1050 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1050, _dollar_dollar[0].value,)
        _t1051 = _t1049(msg)
        fields327 = _t1051
        assert fields327 is not None
        unwrapped_fields328 = fields327
        self.write('(')
        field329 = unwrapped_fields328[0]
        _t1052 = self.pretty_bindings(field329)
        self.write(' ')
        field330 = unwrapped_fields328[1]
        _t1053 = self.pretty_formula(field330)
        self.write(')')
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> Optional[NoReturn]:
        def _t1054(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1055 = _dollar_dollar.attrs
            else:
                _t1055 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1055,)
        _t1056 = _t1054(msg)
        fields331 = _t1056
        assert fields331 is not None
        unwrapped_fields332 = fields331
        self.write('(')
        self.write('break')
        self.indent()
        self.newline()
        field333 = unwrapped_fields332[0]
        _t1057 = self.pretty_relation_id(field333)
        self.newline()
        field334 = unwrapped_fields332[1]
        _t1058 = self.pretty_abstraction(field334)
        field335 = unwrapped_fields332[2]
        
        if field335 is not None:
            self.newline()
            assert field335 is not None
            opt_val336 = field335
            _t1060 = self.pretty_attrs(opt_val336)
            _t1059 = _t1060
        else:
            _t1059 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> Optional[NoReturn]:
        def _t1061(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1062 = _dollar_dollar.attrs
            else:
                _t1062 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1062,)
        _t1063 = _t1061(msg)
        fields337 = _t1063
        assert fields337 is not None
        unwrapped_fields338 = fields337
        self.write('(')
        self.write('monoid')
        self.indent()
        self.newline()
        field339 = unwrapped_fields338[0]
        _t1064 = self.pretty_monoid(field339)
        self.newline()
        field340 = unwrapped_fields338[1]
        _t1065 = self.pretty_relation_id(field340)
        self.newline()
        field341 = unwrapped_fields338[2]
        _t1066 = self.pretty_abstraction_with_arity(field341)
        field342 = unwrapped_fields338[3]
        
        if field342 is not None:
            self.newline()
            assert field342 is not None
            opt_val343 = field342
            _t1068 = self.pretty_attrs(opt_val343)
            _t1067 = _t1068
        else:
            _t1067 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> Optional[NoReturn]:
        def _t1069(_dollar_dollar):
            
            if _dollar_dollar.HasField('or_monoid'):
                _t1070 = _dollar_dollar.or_monoid
            else:
                _t1070 = None
            return _t1070
        _t1071 = _t1069(msg)
        deconstruct_result347 = _t1071
        
        if deconstruct_result347 is not None:
            _t1073 = self.pretty_or_monoid(deconstruct_result347)
            _t1072 = _t1073
        else:
            def _t1074(_dollar_dollar):
                
                if _dollar_dollar.HasField('min_monoid'):
                    _t1075 = _dollar_dollar.min_monoid
                else:
                    _t1075 = None
                return _t1075
            _t1076 = _t1074(msg)
            deconstruct_result346 = _t1076
            
            if deconstruct_result346 is not None:
                _t1078 = self.pretty_min_monoid(deconstruct_result346)
                _t1077 = _t1078
            else:
                def _t1079(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('max_monoid'):
                        _t1080 = _dollar_dollar.max_monoid
                    else:
                        _t1080 = None
                    return _t1080
                _t1081 = _t1079(msg)
                deconstruct_result345 = _t1081
                
                if deconstruct_result345 is not None:
                    _t1083 = self.pretty_max_monoid(deconstruct_result345)
                    _t1082 = _t1083
                else:
                    def _t1084(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('sum_monoid'):
                            _t1085 = _dollar_dollar.sum_monoid
                        else:
                            _t1085 = None
                        return _t1085
                    _t1086 = _t1084(msg)
                    deconstruct_result344 = _t1086
                    
                    if deconstruct_result344 is not None:
                        _t1088 = self.pretty_sum_monoid(deconstruct_result344)
                        _t1087 = _t1088
                    else:
                        raise ParseError('No matching rule for monoid')
                    _t1082 = _t1087
                _t1077 = _t1082
            _t1072 = _t1077
        return _t1072

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> Optional[NoReturn]:
        def _t1089(_dollar_dollar):
            return _dollar_dollar
        _t1090 = _t1089(msg)
        fields348 = _t1090
        assert fields348 is not None
        unwrapped_fields349 = fields348
        self.write('(')
        self.write('or')
        self.write(')')
        return None

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid) -> Optional[NoReturn]:
        def _t1091(_dollar_dollar):
            return _dollar_dollar.type
        _t1092 = _t1091(msg)
        fields350 = _t1092
        assert fields350 is not None
        unwrapped_fields351 = fields350
        self.write('(')
        self.write('min')
        self.indent()
        self.newline()
        _t1093 = self.pretty_type(unwrapped_fields351)
        self.dedent()
        self.write(')')
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> Optional[NoReturn]:
        def _t1094(_dollar_dollar):
            return _dollar_dollar.type
        _t1095 = _t1094(msg)
        fields352 = _t1095
        assert fields352 is not None
        unwrapped_fields353 = fields352
        self.write('(')
        self.write('max')
        self.indent()
        self.newline()
        _t1096 = self.pretty_type(unwrapped_fields353)
        self.dedent()
        self.write(')')
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> Optional[NoReturn]:
        def _t1097(_dollar_dollar):
            return _dollar_dollar.type
        _t1098 = _t1097(msg)
        fields354 = _t1098
        assert fields354 is not None
        unwrapped_fields355 = fields354
        self.write('(')
        self.write('sum')
        self.indent()
        self.newline()
        _t1099 = self.pretty_type(unwrapped_fields355)
        self.dedent()
        self.write(')')
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> Optional[NoReturn]:
        def _t1100(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1101 = _dollar_dollar.attrs
            else:
                _t1101 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1101,)
        _t1102 = _t1100(msg)
        fields356 = _t1102
        assert fields356 is not None
        unwrapped_fields357 = fields356
        self.write('(')
        self.write('monus')
        self.indent()
        self.newline()
        field358 = unwrapped_fields357[0]
        _t1103 = self.pretty_monoid(field358)
        self.newline()
        field359 = unwrapped_fields357[1]
        _t1104 = self.pretty_relation_id(field359)
        self.newline()
        field360 = unwrapped_fields357[2]
        _t1105 = self.pretty_abstraction_with_arity(field360)
        field361 = unwrapped_fields357[3]
        
        if field361 is not None:
            self.newline()
            assert field361 is not None
            opt_val362 = field361
            _t1107 = self.pretty_attrs(opt_val362)
            _t1106 = _t1107
        else:
            _t1106 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> Optional[NoReturn]:
        def _t1108(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1109 = _t1108(msg)
        fields363 = _t1109
        assert fields363 is not None
        unwrapped_fields364 = fields363
        self.write('(')
        self.write('functional_dependency')
        self.indent()
        self.newline()
        field365 = unwrapped_fields364[0]
        _t1110 = self.pretty_relation_id(field365)
        self.newline()
        field366 = unwrapped_fields364[1]
        _t1111 = self.pretty_abstraction(field366)
        self.newline()
        field367 = unwrapped_fields364[2]
        _t1112 = self.pretty_functional_dependency_keys(field367)
        self.newline()
        field368 = unwrapped_fields364[3]
        _t1113 = self.pretty_functional_dependency_values(field368)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]) -> Optional[NoReturn]:
        def _t1114(_dollar_dollar):
            return _dollar_dollar
        _t1115 = _t1114(msg)
        fields369 = _t1115
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
                _t1116 = self.pretty_var(elem371)
        self.dedent()
        self.write(')')
        return None

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]) -> Optional[NoReturn]:
        def _t1117(_dollar_dollar):
            return _dollar_dollar
        _t1118 = _t1117(msg)
        fields373 = _t1118
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
                _t1119 = self.pretty_var(elem375)
        self.dedent()
        self.write(')')
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> Optional[NoReturn]:
        def _t1120(_dollar_dollar):
            
            if _dollar_dollar.HasField('rel_edb'):
                _t1121 = _dollar_dollar.rel_edb
            else:
                _t1121 = None
            return _t1121
        _t1122 = _t1120(msg)
        deconstruct_result379 = _t1122
        
        if deconstruct_result379 is not None:
            _t1124 = self.pretty_rel_edb(deconstruct_result379)
            _t1123 = _t1124
        else:
            def _t1125(_dollar_dollar):
                
                if _dollar_dollar.HasField('betree_relation'):
                    _t1126 = _dollar_dollar.betree_relation
                else:
                    _t1126 = None
                return _t1126
            _t1127 = _t1125(msg)
            deconstruct_result378 = _t1127
            
            if deconstruct_result378 is not None:
                _t1129 = self.pretty_betree_relation(deconstruct_result378)
                _t1128 = _t1129
            else:
                def _t1130(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('csv_data'):
                        _t1131 = _dollar_dollar.csv_data
                    else:
                        _t1131 = None
                    return _t1131
                _t1132 = _t1130(msg)
                deconstruct_result377 = _t1132
                
                if deconstruct_result377 is not None:
                    _t1134 = self.pretty_csv_data(deconstruct_result377)
                    _t1133 = _t1134
                else:
                    raise ParseError('No matching rule for data')
                _t1128 = _t1133
            _t1123 = _t1128
        return _t1123

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> Optional[NoReturn]:
        def _t1135(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1136 = _t1135(msg)
        fields380 = _t1136
        assert fields380 is not None
        unwrapped_fields381 = fields380
        self.write('(')
        self.write('rel_edb')
        self.indent()
        self.newline()
        field382 = unwrapped_fields381[0]
        _t1137 = self.pretty_relation_id(field382)
        self.newline()
        field383 = unwrapped_fields381[1]
        _t1138 = self.pretty_rel_edb_path(field383)
        self.newline()
        field384 = unwrapped_fields381[2]
        _t1139 = self.pretty_rel_edb_types(field384)
        self.dedent()
        self.write(')')
        return None

    def pretty_rel_edb_path(self, msg: Sequence[str]) -> Optional[NoReturn]:
        def _t1140(_dollar_dollar):
            return _dollar_dollar
        _t1141 = _t1140(msg)
        fields385 = _t1141
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
        def _t1142(_dollar_dollar):
            return _dollar_dollar
        _t1143 = _t1142(msg)
        fields389 = _t1143
        assert fields389 is not None
        unwrapped_fields390 = fields389
        self.write('[')
        for i392, elem391 in enumerate(unwrapped_fields390):
            if (i392 > 0):
                self.newline()
            _t1144 = self.pretty_type(elem391)
        self.write(']')
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> Optional[NoReturn]:
        def _t1145(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1146 = _t1145(msg)
        fields393 = _t1146
        assert fields393 is not None
        unwrapped_fields394 = fields393
        self.write('(')
        self.write('betree_relation')
        self.indent()
        self.newline()
        field395 = unwrapped_fields394[0]
        _t1147 = self.pretty_relation_id(field395)
        self.newline()
        field396 = unwrapped_fields394[1]
        _t1148 = self.pretty_betree_info(field396)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> Optional[NoReturn]:
        def _t1149(_dollar_dollar):
            _t1150 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1150,)
        _t1151 = _t1149(msg)
        fields397 = _t1151
        assert fields397 is not None
        unwrapped_fields398 = fields397
        self.write('(')
        self.write('betree_info')
        self.indent()
        self.newline()
        field399 = unwrapped_fields398[0]
        _t1152 = self.pretty_betree_info_key_types(field399)
        self.newline()
        field400 = unwrapped_fields398[1]
        _t1153 = self.pretty_betree_info_value_types(field400)
        self.newline()
        field401 = unwrapped_fields398[2]
        _t1154 = self.pretty_config_dict(field401)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[NoReturn]:
        def _t1155(_dollar_dollar):
            return _dollar_dollar
        _t1156 = _t1155(msg)
        fields402 = _t1156
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
                _t1157 = self.pretty_type(elem404)
        self.dedent()
        self.write(')')
        return None

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]) -> Optional[NoReturn]:
        def _t1158(_dollar_dollar):
            return _dollar_dollar
        _t1159 = _t1158(msg)
        fields406 = _t1159
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
                _t1160 = self.pretty_type(elem408)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> Optional[NoReturn]:
        def _t1161(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1162 = _t1161(msg)
        fields410 = _t1162
        assert fields410 is not None
        unwrapped_fields411 = fields410
        self.write('(')
        self.write('csv_data')
        self.indent()
        self.newline()
        field412 = unwrapped_fields411[0]
        _t1163 = self.pretty_csvlocator(field412)
        self.newline()
        field413 = unwrapped_fields411[1]
        _t1164 = self.pretty_csv_config(field413)
        self.newline()
        field414 = unwrapped_fields411[2]
        _t1165 = self.pretty_csv_columns(field414)
        self.newline()
        field415 = unwrapped_fields411[3]
        _t1166 = self.pretty_csv_asof(field415)
        self.dedent()
        self.write(')')
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> Optional[NoReturn]:
        def _t1167(_dollar_dollar):
            
            if not len(_dollar_dollar.paths) == 0:
                _t1168 = _dollar_dollar.paths
            else:
                _t1168 = None
            
            if _dollar_dollar.inline_data.decode('utf-8') != '':
                _t1169 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1169 = None
            return (_t1168, _t1169,)
        _t1170 = _t1167(msg)
        fields416 = _t1170
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
            _t1172 = self.pretty_csv_locator_paths(opt_val419)
            _t1171 = _t1172
        else:
            _t1171 = None
        field420 = unwrapped_fields417[1]
        
        if field420 is not None:
            self.newline()
            assert field420 is not None
            opt_val421 = field420
            _t1174 = self.pretty_csv_locator_inline_data(opt_val421)
            _t1173 = _t1174
        else:
            _t1173 = None
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_locator_paths(self, msg: Sequence[str]) -> Optional[NoReturn]:
        def _t1175(_dollar_dollar):
            return _dollar_dollar
        _t1176 = _t1175(msg)
        fields422 = _t1176
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
        def _t1177(_dollar_dollar):
            return _dollar_dollar
        _t1178 = _t1177(msg)
        fields426 = _t1178
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
        def _t1179(_dollar_dollar):
            _t1180 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1180
        _t1181 = _t1179(msg)
        fields428 = _t1181
        assert fields428 is not None
        unwrapped_fields429 = fields428
        self.write('(')
        self.write('csv_config')
        self.indent()
        self.newline()
        _t1182 = self.pretty_config_dict(unwrapped_fields429)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]) -> Optional[NoReturn]:
        def _t1183(_dollar_dollar):
            return _dollar_dollar
        _t1184 = _t1183(msg)
        fields430 = _t1184
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
                _t1185 = self.pretty_csv_column(elem432)
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> Optional[NoReturn]:
        def _t1186(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1187 = _t1186(msg)
        fields434 = _t1187
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
        _t1188 = self.pretty_relation_id(field437)
        self.newline()
        self.write('[')
        field438 = unwrapped_fields435[2]
        for i440, elem439 in enumerate(field438):
            if (i440 > 0):
                self.newline()
            _t1189 = self.pretty_type(elem439)
        self.write(']')
        self.dedent()
        self.write(')')
        return None

    def pretty_csv_asof(self, msg: str) -> Optional[NoReturn]:
        def _t1190(_dollar_dollar):
            return _dollar_dollar
        _t1191 = _t1190(msg)
        fields441 = _t1191
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
        def _t1192(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1193 = _t1192(msg)
        fields443 = _t1193
        assert fields443 is not None
        unwrapped_fields444 = fields443
        self.write('(')
        self.write('undefine')
        self.indent()
        self.newline()
        _t1194 = self.pretty_fragment_id(unwrapped_fields444)
        self.dedent()
        self.write(')')
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> Optional[NoReturn]:
        def _t1195(_dollar_dollar):
            return _dollar_dollar.relations
        _t1196 = _t1195(msg)
        fields445 = _t1196
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
                _t1197 = self.pretty_relation_id(elem447)
        self.dedent()
        self.write(')')
        return None

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]) -> Optional[NoReturn]:
        def _t1198(_dollar_dollar):
            return _dollar_dollar
        _t1199 = _t1198(msg)
        fields449 = _t1199
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
                _t1200 = self.pretty_read(elem451)
        self.dedent()
        self.write(')')
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> Optional[NoReturn]:
        def _t1201(_dollar_dollar):
            
            if _dollar_dollar.HasField('demand'):
                _t1202 = _dollar_dollar.demand
            else:
                _t1202 = None
            return _t1202
        _t1203 = _t1201(msg)
        deconstruct_result457 = _t1203
        
        if deconstruct_result457 is not None:
            _t1205 = self.pretty_demand(deconstruct_result457)
            _t1204 = _t1205
        else:
            def _t1206(_dollar_dollar):
                
                if _dollar_dollar.HasField('output'):
                    _t1207 = _dollar_dollar.output
                else:
                    _t1207 = None
                return _t1207
            _t1208 = _t1206(msg)
            deconstruct_result456 = _t1208
            
            if deconstruct_result456 is not None:
                _t1210 = self.pretty_output(deconstruct_result456)
                _t1209 = _t1210
            else:
                def _t1211(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('what_if'):
                        _t1212 = _dollar_dollar.what_if
                    else:
                        _t1212 = None
                    return _t1212
                _t1213 = _t1211(msg)
                deconstruct_result455 = _t1213
                
                if deconstruct_result455 is not None:
                    _t1215 = self.pretty_what_if(deconstruct_result455)
                    _t1214 = _t1215
                else:
                    def _t1216(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('abort'):
                            _t1217 = _dollar_dollar.abort
                        else:
                            _t1217 = None
                        return _t1217
                    _t1218 = _t1216(msg)
                    deconstruct_result454 = _t1218
                    
                    if deconstruct_result454 is not None:
                        _t1220 = self.pretty_abort(deconstruct_result454)
                        _t1219 = _t1220
                    else:
                        def _t1221(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('export'):
                                _t1222 = _dollar_dollar.export
                            else:
                                _t1222 = None
                            return _t1222
                        _t1223 = _t1221(msg)
                        deconstruct_result453 = _t1223
                        
                        if deconstruct_result453 is not None:
                            _t1225 = self.pretty_export(deconstruct_result453)
                            _t1224 = _t1225
                        else:
                            raise ParseError('No matching rule for read')
                        _t1219 = _t1224
                    _t1214 = _t1219
                _t1209 = _t1214
            _t1204 = _t1209
        return _t1204

    def pretty_demand(self, msg: transactions_pb2.Demand) -> Optional[NoReturn]:
        def _t1226(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1227 = _t1226(msg)
        fields458 = _t1227
        assert fields458 is not None
        unwrapped_fields459 = fields458
        self.write('(')
        self.write('demand')
        self.indent()
        self.newline()
        _t1228 = self.pretty_relation_id(unwrapped_fields459)
        self.dedent()
        self.write(')')
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> Optional[NoReturn]:
        def _t1229(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        _t1230 = _t1229(msg)
        fields460 = _t1230
        assert fields460 is not None
        unwrapped_fields461 = fields460
        self.write('(')
        self.write('output')
        self.indent()
        self.newline()
        field462 = unwrapped_fields461[0]
        _t1231 = self.pretty_name(field462)
        self.newline()
        field463 = unwrapped_fields461[1]
        _t1232 = self.pretty_relation_id(field463)
        self.dedent()
        self.write(')')
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> Optional[NoReturn]:
        def _t1233(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1234 = _t1233(msg)
        fields464 = _t1234
        assert fields464 is not None
        unwrapped_fields465 = fields464
        self.write('(')
        self.write('what_if')
        self.indent()
        self.newline()
        field466 = unwrapped_fields465[0]
        _t1235 = self.pretty_name(field466)
        self.newline()
        field467 = unwrapped_fields465[1]
        _t1236 = self.pretty_epoch(field467)
        self.dedent()
        self.write(')')
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> Optional[NoReturn]:
        def _t1237(_dollar_dollar):
            
            if _dollar_dollar.name != 'abort':
                _t1238 = _dollar_dollar.name
            else:
                _t1238 = None
            return (_t1238, _dollar_dollar.relation_id,)
        _t1239 = _t1237(msg)
        fields468 = _t1239
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
            _t1241 = self.pretty_name(opt_val471)
            _t1240 = _t1241
        else:
            _t1240 = None
        self.newline()
        field472 = unwrapped_fields469[1]
        _t1242 = self.pretty_relation_id(field472)
        self.dedent()
        self.write(')')
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> Optional[NoReturn]:
        def _t1243(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1244 = _t1243(msg)
        fields473 = _t1244
        assert fields473 is not None
        unwrapped_fields474 = fields473
        self.write('(')
        self.write('export')
        self.indent()
        self.newline()
        _t1245 = self.pretty_export_csv_config(unwrapped_fields474)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> Optional[NoReturn]:
        def _t1246(_dollar_dollar):
            
            if len(_dollar_dollar.data_columns) == 0:
                _t1247 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1247 = None
            return _t1247
        _t1248 = _t1246(msg)
        deconstruct_result479 = _t1248
        if deconstruct_result479 is not None:
            self.write('(')
            self.write('export_csv_config_v2')
            self.indent()
            self.newline()
            field480 = deconstruct_result479[0]
            _t1249 = self.pretty_export_csv_path(field480)
            self.newline()
            field481 = deconstruct_result479[1]
            _t1250 = self.pretty_export_csv_source(field481)
            self.newline()
            field482 = deconstruct_result479[2]
            _t1251 = self.pretty_csv_config(field482)
            self.dedent()
            self.write(')')
        else:
            def _t1252(_dollar_dollar):
                
                if len(_dollar_dollar.data_columns) != 0:
                    _t1254 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1253 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1254,)
                else:
                    _t1253 = None
                return _t1253
            _t1255 = _t1252(msg)
            deconstruct_result475 = _t1255
            if deconstruct_result475 is not None:
                self.write('(')
                self.write('export_csv_config')
                self.indent()
                self.newline()
                field476 = deconstruct_result475[0]
                _t1256 = self.pretty_export_csv_path(field476)
                self.newline()
                field477 = deconstruct_result475[1]
                _t1257 = self.pretty_export_csv_columns(field477)
                self.newline()
                field478 = deconstruct_result475[2]
                _t1258 = self.pretty_config_dict(field478)
                self.dedent()
                self.write(')')
            else:
                raise ParseError('No matching rule for export_csv_config')
        return None

    def pretty_export_csv_path(self, msg: str) -> Optional[NoReturn]:
        def _t1259(_dollar_dollar):
            return _dollar_dollar
        _t1260 = _t1259(msg)
        fields483 = _t1260
        assert fields483 is not None
        unwrapped_fields484 = fields483
        self.write('(')
        self.write('path')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields484))
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource) -> Optional[NoReturn]:
        def _t1261(_dollar_dollar):
            
            if _dollar_dollar.HasField('gnf_columns'):
                _t1262 = _dollar_dollar.gnf_columns.columns
            else:
                _t1262 = None
            return _t1262
        _t1263 = _t1261(msg)
        deconstruct_result486 = _t1263
        if deconstruct_result486 is not None:
            self.write('(')
            self.write('gnf_columns')
            self.indent()
            if not len(deconstruct_result486) == 0:
                self.newline()
                for i488, elem487 in enumerate(deconstruct_result486):
                    if (i488 > 0):
                        self.newline()
                    _t1264 = self.pretty_export_csv_column(elem487)
            self.dedent()
            self.write(')')
        else:
            def _t1265(_dollar_dollar):
                
                if _dollar_dollar.HasField('table_def'):
                    _t1266 = _dollar_dollar.table_def
                else:
                    _t1266 = None
                return _t1266
            _t1267 = _t1265(msg)
            deconstruct_result485 = _t1267
            if deconstruct_result485 is not None:
                self.write('(')
                self.write('table_def')
                self.indent()
                self.newline()
                _t1268 = self.pretty_relation_id(deconstruct_result485)
                self.dedent()
                self.write(')')
            else:
                raise ParseError('No matching rule for export_csv_source')
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> Optional[NoReturn]:
        def _t1269(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1270 = _t1269(msg)
        fields489 = _t1270
        assert fields489 is not None
        unwrapped_fields490 = fields489
        self.write('(')
        self.write('column')
        self.indent()
        self.newline()
        field491 = unwrapped_fields490[0]
        self.write(self.format_string_value(field491))
        self.newline()
        field492 = unwrapped_fields490[1]
        _t1271 = self.pretty_relation_id(field492)
        self.dedent()
        self.write(')')
        return None

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]) -> Optional[NoReturn]:
        def _t1272(_dollar_dollar):
            return _dollar_dollar
        _t1273 = _t1272(msg)
        fields493 = _t1273
        assert fields493 is not None
        unwrapped_fields494 = fields493
        self.write('(')
        self.write('columns')
        self.indent()
        if not len(unwrapped_fields494) == 0:
            self.newline()
            for i496, elem495 in enumerate(unwrapped_fields494):
                if (i496 > 0):
                    self.newline()
                _t1274 = self.pretty_export_csv_column(elem495)
        self.dedent()
        self.write(')')
        return None


def pretty(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
