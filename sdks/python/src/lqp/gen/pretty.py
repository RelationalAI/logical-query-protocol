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

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == '':
            return self.relation_id_to_uint128(msg)
        return None

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1252 = logic_pb2.Value(int_value=v)
        return _t1252

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1253 = logic_pb2.Value(string_value=v)
        return _t1253

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1254 = logic_pb2.Value(float_value=v)
        return _t1254

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1255 = self._make_value_int64(msg.partition_size)
            result.append(('partition_size', _t1255,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1256 = self._make_value_string(msg.compression)
            result.append(('compression', _t1256,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1257 = self._make_value_boolean(msg.syntax_header_row)
            result.append(('syntax_header_row', _t1257,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1258 = self._make_value_string(msg.syntax_missing_string)
            result.append(('syntax_missing_string', _t1258,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1259 = self._make_value_string(msg.syntax_delim)
            result.append(('syntax_delim', _t1259,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1260 = self._make_value_string(msg.syntax_quotechar)
            result.append(('syntax_quotechar', _t1260,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1261 = self._make_value_string(msg.syntax_escapechar)
            result.append(('syntax_escapechar', _t1261,))
        return sorted(result)

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1262 = self._make_value_string('auto')
            result.append(('ivm.maintenance_level', _t1262,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1263 = self._make_value_string('all')
                result.append(('ivm.maintenance_level', _t1263,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1264 = self._make_value_string('off')
                    result.append(('ivm.maintenance_level', _t1264,))
        _t1265 = self._make_value_int64(msg.semantics_version)
        result.append(('semantics_version', _t1265,))
        return sorted(result)

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1266 = logic_pb2.Value(int_value=int(v))
        return _t1266

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1267 = logic_pb2.Value(uint128_value=v)
        return _t1267

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1268 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(('betree_config_epsilon', _t1268,))
        _t1269 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(('betree_config_max_pivots', _t1269,))
        _t1270 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(('betree_config_max_deltas', _t1270,))
        _t1271 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(('betree_config_max_leaf', _t1271,))
        if msg.relation_locator.HasField('root_pageid'):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1272 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(('betree_locator_root_pageid', _t1272,))
        if msg.relation_locator.HasField('inline_data'):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1273 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(('betree_locator_inline_data', _t1273,))
        _t1274 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(('betree_locator_element_count', _t1274,))
        _t1275 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(('betree_locator_tree_height', _t1275,))
        return sorted(result)

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        return (abs.vars[0:n], [],)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != '':
            return name
        return None

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1276 = self._make_value_int32(msg.header_row)
        result.append(('csv_header_row', _t1276,))
        _t1277 = self._make_value_int64(msg.skip)
        result.append(('csv_skip', _t1277,))
        if msg.new_line != '':
            _t1278 = self._make_value_string(msg.new_line)
            result.append(('csv_new_line', _t1278,))
        _t1279 = self._make_value_string(msg.delimiter)
        result.append(('csv_delimiter', _t1279,))
        _t1280 = self._make_value_string(msg.quotechar)
        result.append(('csv_quotechar', _t1280,))
        _t1281 = self._make_value_string(msg.escapechar)
        result.append(('csv_escapechar', _t1281,))
        if msg.comment != '':
            _t1282 = self._make_value_string(msg.comment)
            result.append(('csv_comment', _t1282,))
        for missing_string in msg.missing_strings:
            _t1283 = self._make_value_string(missing_string)
            result.append(('csv_missing_strings', _t1283,))
        _t1284 = self._make_value_string(msg.decimal_separator)
        result.append(('csv_decimal_separator', _t1284,))
        _t1285 = self._make_value_string(msg.encoding)
        result.append(('csv_encoding', _t1285,))
        _t1286 = self._make_value_string(msg.compression)
        result.append(('csv_compression', _t1286,))
        return sorted(result)

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1287 = logic_pb2.Value(boolean_value=v)
        return _t1287

    # --- Pretty-print methods ---

    def pretty_transaction(self, msg: transactions_pb2.Transaction):
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

    def pretty_configure(self, msg: transactions_pb2.Configure):
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

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        def _t503(_dollar_dollar):
            return _dollar_dollar
        _t504 = _t503(msg)
        fields11 = _t504
        assert fields11 is not None
        unwrapped_fields12 = fields11
        self.write('{')
        self.indent()
        if not len(unwrapped_fields12) == 0:
            self.write(' ')
            for i14, elem13 in enumerate(unwrapped_fields12):
                if (i14 > 0):
                    self.newline()
                _t505 = self.pretty_config_key_value(elem13)
        self.dedent()
        self.write('}')

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
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

    def pretty_value(self, msg: logic_pb2.Value):
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

    def pretty_date(self, msg: logic_pb2.DateValue):
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

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
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

    def pretty_boolean_value(self, msg: bool):
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

    def pretty_sync(self, msg: transactions_pb2.Sync):
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

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        def _t563(_dollar_dollar):
            return self.fragment_id_to_string(_dollar_dollar)
        _t564 = _t563(msg)
        fields51 = _t564
        assert fields51 is not None
        unwrapped_fields52 = fields51
        self.write(':')
        self.write(unwrapped_fields52)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
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

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
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

    def pretty_write(self, msg: transactions_pb2.Write):
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

    def pretty_define(self, msg: transactions_pb2.Define):
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

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        def _t594(_dollar_dollar):
            self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t595 = _t594(msg)
        fields68 = _t595
        assert fields68 is not None
        unwrapped_fields69 = fields68
        self.write('(')
        self.write('fragment')
        self.indent()
        self.newline()
        field70 = unwrapped_fields69[0]
        _t596 = self.pretty_new_fragment_id(field70)
        field71 = unwrapped_fields69[1]
        if not len(field71) == 0:
            self.newline()
            for i73, elem72 in enumerate(field71):
                if (i73 > 0):
                    self.newline()
                _t597 = self.pretty_declaration(elem72)
        self.dedent()
        self.write(')')

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        def _t598(_dollar_dollar):
            return _dollar_dollar
        _t599 = _t598(msg)
        fields74 = _t599
        assert fields74 is not None
        unwrapped_fields75 = fields74
        _t600 = self.pretty_fragment_id(unwrapped_fields75)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        def _t601(_dollar_dollar):
            
            if _dollar_dollar.HasField('def'):
                _t602 = getattr(_dollar_dollar, 'def')
            else:
                _t602 = None
            return _t602
        _t603 = _t601(msg)
        deconstruct_result79 = _t603
        
        if deconstruct_result79 is not None:
            _t605 = self.pretty_def(deconstruct_result79)
            _t604 = _t605
        else:
            def _t606(_dollar_dollar):
                
                if _dollar_dollar.HasField('algorithm'):
                    _t607 = _dollar_dollar.algorithm
                else:
                    _t607 = None
                return _t607
            _t608 = _t606(msg)
            deconstruct_result78 = _t608
            
            if deconstruct_result78 is not None:
                _t610 = self.pretty_algorithm(deconstruct_result78)
                _t609 = _t610
            else:
                def _t611(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('constraint'):
                        _t612 = _dollar_dollar.constraint
                    else:
                        _t612 = None
                    return _t612
                _t613 = _t611(msg)
                deconstruct_result77 = _t613
                
                if deconstruct_result77 is not None:
                    _t615 = self.pretty_constraint(deconstruct_result77)
                    _t614 = _t615
                else:
                    def _t616(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('data'):
                            _t617 = _dollar_dollar.data
                        else:
                            _t617 = None
                        return _t617
                    _t618 = _t616(msg)
                    deconstruct_result76 = _t618
                    
                    if deconstruct_result76 is not None:
                        _t620 = self.pretty_data(deconstruct_result76)
                        _t619 = _t620
                    else:
                        raise ParseError('No matching rule for declaration')
                    _t614 = _t619
                _t609 = _t614
            _t604 = _t609

    def pretty_def(self, msg: logic_pb2.Def):
        def _t621(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t622 = _dollar_dollar.attrs
            else:
                _t622 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t622,)
        _t623 = _t621(msg)
        fields80 = _t623
        assert fields80 is not None
        unwrapped_fields81 = fields80
        self.write('(')
        self.write('def')
        self.indent()
        self.newline()
        field82 = unwrapped_fields81[0]
        _t624 = self.pretty_relation_id(field82)
        self.newline()
        field83 = unwrapped_fields81[1]
        _t625 = self.pretty_abstraction(field83)
        field84 = unwrapped_fields81[2]
        
        if field84 is not None:
            self.newline()
            assert field84 is not None
            opt_val85 = field84
            _t627 = self.pretty_attrs(opt_val85)
            _t626 = _t627
        else:
            _t626 = None
        self.dedent()
        self.write(')')

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        def _t628(_dollar_dollar):
            _t629 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t629
        _t630 = _t628(msg)
        deconstruct_result87 = _t630
        if deconstruct_result87 is not None:
            self.write(':')
            self.write(deconstruct_result87)
        else:
            def _t631(_dollar_dollar):
                _t632 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t632
            _t633 = _t631(msg)
            deconstruct_result86 = _t633
            if deconstruct_result86 is not None:
                self.write(self.format_uint128(deconstruct_result86))
            else:
                raise ParseError('No matching rule for relation_id')

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        def _t634(_dollar_dollar):
            _t635 = self.deconstruct_bindings(_dollar_dollar)
            return (_t635, _dollar_dollar.value,)
        _t636 = _t634(msg)
        fields88 = _t636
        assert fields88 is not None
        unwrapped_fields89 = fields88
        self.write('(')
        field90 = unwrapped_fields89[0]
        _t637 = self.pretty_bindings(field90)
        self.write(' ')
        field91 = unwrapped_fields89[1]
        _t638 = self.pretty_formula(field91)
        self.write(')')

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        def _t639(_dollar_dollar):
            
            if not len(_dollar_dollar[1]) == 0:
                _t640 = _dollar_dollar[1]
            else:
                _t640 = None
            return (_dollar_dollar[0], _t640,)
        _t641 = _t639(msg)
        fields92 = _t641
        assert fields92 is not None
        unwrapped_fields93 = fields92
        self.write('[')
        field94 = unwrapped_fields93[0]
        for i96, elem95 in enumerate(field94):
            if (i96 > 0):
                self.newline()
            _t642 = self.pretty_binding(elem95)
        field97 = unwrapped_fields93[1]
        
        if field97 is not None:
            self.write(' ')
            assert field97 is not None
            opt_val98 = field97
            _t644 = self.pretty_value_bindings(opt_val98)
            _t643 = _t644
        else:
            _t643 = None
        self.write(']')

    def pretty_binding(self, msg: logic_pb2.Binding):
        def _t645(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t646 = _t645(msg)
        fields99 = _t646
        assert fields99 is not None
        unwrapped_fields100 = fields99
        field101 = unwrapped_fields100[0]
        self.write(field101)
        self.write('::')
        field102 = unwrapped_fields100[1]
        _t647 = self.pretty_type(field102)

    def pretty_type(self, msg: logic_pb2.Type):
        def _t648(_dollar_dollar):
            
            if _dollar_dollar.HasField('unspecified_type'):
                _t649 = _dollar_dollar.unspecified_type
            else:
                _t649 = None
            return _t649
        _t650 = _t648(msg)
        deconstruct_result113 = _t650
        
        if deconstruct_result113 is not None:
            _t652 = self.pretty_unspecified_type(deconstruct_result113)
            _t651 = _t652
        else:
            def _t653(_dollar_dollar):
                
                if _dollar_dollar.HasField('string_type'):
                    _t654 = _dollar_dollar.string_type
                else:
                    _t654 = None
                return _t654
            _t655 = _t653(msg)
            deconstruct_result112 = _t655
            
            if deconstruct_result112 is not None:
                _t657 = self.pretty_string_type(deconstruct_result112)
                _t656 = _t657
            else:
                def _t658(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('int_type'):
                        _t659 = _dollar_dollar.int_type
                    else:
                        _t659 = None
                    return _t659
                _t660 = _t658(msg)
                deconstruct_result111 = _t660
                
                if deconstruct_result111 is not None:
                    _t662 = self.pretty_int_type(deconstruct_result111)
                    _t661 = _t662
                else:
                    def _t663(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('float_type'):
                            _t664 = _dollar_dollar.float_type
                        else:
                            _t664 = None
                        return _t664
                    _t665 = _t663(msg)
                    deconstruct_result110 = _t665
                    
                    if deconstruct_result110 is not None:
                        _t667 = self.pretty_float_type(deconstruct_result110)
                        _t666 = _t667
                    else:
                        def _t668(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('uint128_type'):
                                _t669 = _dollar_dollar.uint128_type
                            else:
                                _t669 = None
                            return _t669
                        _t670 = _t668(msg)
                        deconstruct_result109 = _t670
                        
                        if deconstruct_result109 is not None:
                            _t672 = self.pretty_uint128_type(deconstruct_result109)
                            _t671 = _t672
                        else:
                            def _t673(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('int128_type'):
                                    _t674 = _dollar_dollar.int128_type
                                else:
                                    _t674 = None
                                return _t674
                            _t675 = _t673(msg)
                            deconstruct_result108 = _t675
                            
                            if deconstruct_result108 is not None:
                                _t677 = self.pretty_int128_type(deconstruct_result108)
                                _t676 = _t677
                            else:
                                def _t678(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('date_type'):
                                        _t679 = _dollar_dollar.date_type
                                    else:
                                        _t679 = None
                                    return _t679
                                _t680 = _t678(msg)
                                deconstruct_result107 = _t680
                                
                                if deconstruct_result107 is not None:
                                    _t682 = self.pretty_date_type(deconstruct_result107)
                                    _t681 = _t682
                                else:
                                    def _t683(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('datetime_type'):
                                            _t684 = _dollar_dollar.datetime_type
                                        else:
                                            _t684 = None
                                        return _t684
                                    _t685 = _t683(msg)
                                    deconstruct_result106 = _t685
                                    
                                    if deconstruct_result106 is not None:
                                        _t687 = self.pretty_datetime_type(deconstruct_result106)
                                        _t686 = _t687
                                    else:
                                        def _t688(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('missing_type'):
                                                _t689 = _dollar_dollar.missing_type
                                            else:
                                                _t689 = None
                                            return _t689
                                        _t690 = _t688(msg)
                                        deconstruct_result105 = _t690
                                        
                                        if deconstruct_result105 is not None:
                                            _t692 = self.pretty_missing_type(deconstruct_result105)
                                            _t691 = _t692
                                        else:
                                            def _t693(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('decimal_type'):
                                                    _t694 = _dollar_dollar.decimal_type
                                                else:
                                                    _t694 = None
                                                return _t694
                                            _t695 = _t693(msg)
                                            deconstruct_result104 = _t695
                                            
                                            if deconstruct_result104 is not None:
                                                _t697 = self.pretty_decimal_type(deconstruct_result104)
                                                _t696 = _t697
                                            else:
                                                def _t698(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('boolean_type'):
                                                        _t699 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t699 = None
                                                    return _t699
                                                _t700 = _t698(msg)
                                                deconstruct_result103 = _t700
                                                
                                                if deconstruct_result103 is not None:
                                                    _t702 = self.pretty_boolean_type(deconstruct_result103)
                                                    _t701 = _t702
                                                else:
                                                    raise ParseError('No matching rule for type')
                                                _t696 = _t701
                                            _t691 = _t696
                                        _t686 = _t691
                                    _t681 = _t686
                                _t676 = _t681
                            _t671 = _t676
                        _t666 = _t671
                    _t661 = _t666
                _t656 = _t661
            _t651 = _t656

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        def _t703(_dollar_dollar):
            return _dollar_dollar
        _t704 = _t703(msg)
        fields114 = _t704
        assert fields114 is not None
        unwrapped_fields115 = fields114
        self.write('UNKNOWN')

    def pretty_string_type(self, msg: logic_pb2.StringType):
        def _t705(_dollar_dollar):
            return _dollar_dollar
        _t706 = _t705(msg)
        fields116 = _t706
        assert fields116 is not None
        unwrapped_fields117 = fields116
        self.write('STRING')

    def pretty_int_type(self, msg: logic_pb2.IntType):
        def _t707(_dollar_dollar):
            return _dollar_dollar
        _t708 = _t707(msg)
        fields118 = _t708
        assert fields118 is not None
        unwrapped_fields119 = fields118
        self.write('INT')

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        def _t709(_dollar_dollar):
            return _dollar_dollar
        _t710 = _t709(msg)
        fields120 = _t710
        assert fields120 is not None
        unwrapped_fields121 = fields120
        self.write('FLOAT')

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        def _t711(_dollar_dollar):
            return _dollar_dollar
        _t712 = _t711(msg)
        fields122 = _t712
        assert fields122 is not None
        unwrapped_fields123 = fields122
        self.write('UINT128')

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        def _t713(_dollar_dollar):
            return _dollar_dollar
        _t714 = _t713(msg)
        fields124 = _t714
        assert fields124 is not None
        unwrapped_fields125 = fields124
        self.write('INT128')

    def pretty_date_type(self, msg: logic_pb2.DateType):
        def _t715(_dollar_dollar):
            return _dollar_dollar
        _t716 = _t715(msg)
        fields126 = _t716
        assert fields126 is not None
        unwrapped_fields127 = fields126
        self.write('DATE')

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        def _t717(_dollar_dollar):
            return _dollar_dollar
        _t718 = _t717(msg)
        fields128 = _t718
        assert fields128 is not None
        unwrapped_fields129 = fields128
        self.write('DATETIME')

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        def _t719(_dollar_dollar):
            return _dollar_dollar
        _t720 = _t719(msg)
        fields130 = _t720
        assert fields130 is not None
        unwrapped_fields131 = fields130
        self.write('MISSING')

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        def _t721(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t722 = _t721(msg)
        fields132 = _t722
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

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        def _t723(_dollar_dollar):
            return _dollar_dollar
        _t724 = _t723(msg)
        fields136 = _t724
        assert fields136 is not None
        unwrapped_fields137 = fields136
        self.write('BOOLEAN')

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        def _t725(_dollar_dollar):
            return _dollar_dollar
        _t726 = _t725(msg)
        fields138 = _t726
        assert fields138 is not None
        unwrapped_fields139 = fields138
        self.write('|')
        if not len(unwrapped_fields139) == 0:
            self.write(' ')
            for i141, elem140 in enumerate(unwrapped_fields139):
                if (i141 > 0):
                    self.newline()
                _t727 = self.pretty_binding(elem140)

    def pretty_formula(self, msg: logic_pb2.Formula):
        def _t728(_dollar_dollar):
            
            if (_dollar_dollar.HasField('conjunction') and len(_dollar_dollar.conjunction.args) == 0):
                _t729 = _dollar_dollar.conjunction
            else:
                _t729 = None
            return _t729
        _t730 = _t728(msg)
        deconstruct_result154 = _t730
        
        if deconstruct_result154 is not None:
            _t732 = self.pretty_true(deconstruct_result154)
            _t731 = _t732
        else:
            def _t733(_dollar_dollar):
                
                if (_dollar_dollar.HasField('disjunction') and len(_dollar_dollar.disjunction.args) == 0):
                    _t734 = _dollar_dollar.disjunction
                else:
                    _t734 = None
                return _t734
            _t735 = _t733(msg)
            deconstruct_result153 = _t735
            
            if deconstruct_result153 is not None:
                _t737 = self.pretty_false(deconstruct_result153)
                _t736 = _t737
            else:
                def _t738(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('exists'):
                        _t739 = _dollar_dollar.exists
                    else:
                        _t739 = None
                    return _t739
                _t740 = _t738(msg)
                deconstruct_result152 = _t740
                
                if deconstruct_result152 is not None:
                    _t742 = self.pretty_exists(deconstruct_result152)
                    _t741 = _t742
                else:
                    def _t743(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('reduce'):
                            _t744 = _dollar_dollar.reduce
                        else:
                            _t744 = None
                        return _t744
                    _t745 = _t743(msg)
                    deconstruct_result151 = _t745
                    
                    if deconstruct_result151 is not None:
                        _t747 = self.pretty_reduce(deconstruct_result151)
                        _t746 = _t747
                    else:
                        def _t748(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('conjunction'):
                                _t749 = _dollar_dollar.conjunction
                            else:
                                _t749 = None
                            return _t749
                        _t750 = _t748(msg)
                        deconstruct_result150 = _t750
                        
                        if deconstruct_result150 is not None:
                            _t752 = self.pretty_conjunction(deconstruct_result150)
                            _t751 = _t752
                        else:
                            def _t753(_dollar_dollar):
                                
                                if _dollar_dollar.HasField('disjunction'):
                                    _t754 = _dollar_dollar.disjunction
                                else:
                                    _t754 = None
                                return _t754
                            _t755 = _t753(msg)
                            deconstruct_result149 = _t755
                            
                            if deconstruct_result149 is not None:
                                _t757 = self.pretty_disjunction(deconstruct_result149)
                                _t756 = _t757
                            else:
                                def _t758(_dollar_dollar):
                                    
                                    if _dollar_dollar.HasField('not'):
                                        _t759 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t759 = None
                                    return _t759
                                _t760 = _t758(msg)
                                deconstruct_result148 = _t760
                                
                                if deconstruct_result148 is not None:
                                    _t762 = self.pretty_not(deconstruct_result148)
                                    _t761 = _t762
                                else:
                                    def _t763(_dollar_dollar):
                                        
                                        if _dollar_dollar.HasField('ffi'):
                                            _t764 = _dollar_dollar.ffi
                                        else:
                                            _t764 = None
                                        return _t764
                                    _t765 = _t763(msg)
                                    deconstruct_result147 = _t765
                                    
                                    if deconstruct_result147 is not None:
                                        _t767 = self.pretty_ffi(deconstruct_result147)
                                        _t766 = _t767
                                    else:
                                        def _t768(_dollar_dollar):
                                            
                                            if _dollar_dollar.HasField('atom'):
                                                _t769 = _dollar_dollar.atom
                                            else:
                                                _t769 = None
                                            return _t769
                                        _t770 = _t768(msg)
                                        deconstruct_result146 = _t770
                                        
                                        if deconstruct_result146 is not None:
                                            _t772 = self.pretty_atom(deconstruct_result146)
                                            _t771 = _t772
                                        else:
                                            def _t773(_dollar_dollar):
                                                
                                                if _dollar_dollar.HasField('pragma'):
                                                    _t774 = _dollar_dollar.pragma
                                                else:
                                                    _t774 = None
                                                return _t774
                                            _t775 = _t773(msg)
                                            deconstruct_result145 = _t775
                                            
                                            if deconstruct_result145 is not None:
                                                _t777 = self.pretty_pragma(deconstruct_result145)
                                                _t776 = _t777
                                            else:
                                                def _t778(_dollar_dollar):
                                                    
                                                    if _dollar_dollar.HasField('primitive'):
                                                        _t779 = _dollar_dollar.primitive
                                                    else:
                                                        _t779 = None
                                                    return _t779
                                                _t780 = _t778(msg)
                                                deconstruct_result144 = _t780
                                                
                                                if deconstruct_result144 is not None:
                                                    _t782 = self.pretty_primitive(deconstruct_result144)
                                                    _t781 = _t782
                                                else:
                                                    def _t783(_dollar_dollar):
                                                        
                                                        if _dollar_dollar.HasField('rel_atom'):
                                                            _t784 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t784 = None
                                                        return _t784
                                                    _t785 = _t783(msg)
                                                    deconstruct_result143 = _t785
                                                    
                                                    if deconstruct_result143 is not None:
                                                        _t787 = self.pretty_rel_atom(deconstruct_result143)
                                                        _t786 = _t787
                                                    else:
                                                        def _t788(_dollar_dollar):
                                                            
                                                            if _dollar_dollar.HasField('cast'):
                                                                _t789 = _dollar_dollar.cast
                                                            else:
                                                                _t789 = None
                                                            return _t789
                                                        _t790 = _t788(msg)
                                                        deconstruct_result142 = _t790
                                                        
                                                        if deconstruct_result142 is not None:
                                                            _t792 = self.pretty_cast(deconstruct_result142)
                                                            _t791 = _t792
                                                        else:
                                                            raise ParseError('No matching rule for formula')
                                                        _t786 = _t791
                                                    _t781 = _t786
                                                _t776 = _t781
                                            _t771 = _t776
                                        _t766 = _t771
                                    _t761 = _t766
                                _t756 = _t761
                            _t751 = _t756
                        _t746 = _t751
                    _t741 = _t746
                _t736 = _t741
            _t731 = _t736

    def pretty_true(self, msg: logic_pb2.Conjunction):
        def _t793(_dollar_dollar):
            return _dollar_dollar
        _t794 = _t793(msg)
        fields155 = _t794
        assert fields155 is not None
        unwrapped_fields156 = fields155
        self.write('(')
        self.write('true')
        self.write(')')

    def pretty_false(self, msg: logic_pb2.Disjunction):
        def _t795(_dollar_dollar):
            return _dollar_dollar
        _t796 = _t795(msg)
        fields157 = _t796
        assert fields157 is not None
        unwrapped_fields158 = fields157
        self.write('(')
        self.write('false')
        self.write(')')

    def pretty_exists(self, msg: logic_pb2.Exists):
        def _t797(_dollar_dollar):
            _t798 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t798, _dollar_dollar.body.value,)
        _t799 = _t797(msg)
        fields159 = _t799
        assert fields159 is not None
        unwrapped_fields160 = fields159
        self.write('(')
        self.write('exists')
        self.indent()
        self.newline()
        field161 = unwrapped_fields160[0]
        _t800 = self.pretty_bindings(field161)
        self.newline()
        field162 = unwrapped_fields160[1]
        _t801 = self.pretty_formula(field162)
        self.dedent()
        self.write(')')

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        def _t802(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t803 = _t802(msg)
        fields163 = _t803
        assert fields163 is not None
        unwrapped_fields164 = fields163
        self.write('(')
        self.write('reduce')
        self.indent()
        self.newline()
        field165 = unwrapped_fields164[0]
        _t804 = self.pretty_abstraction(field165)
        self.newline()
        field166 = unwrapped_fields164[1]
        _t805 = self.pretty_abstraction(field166)
        self.newline()
        field167 = unwrapped_fields164[2]
        _t806 = self.pretty_terms(field167)
        self.dedent()
        self.write(')')

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        def _t807(_dollar_dollar):
            return _dollar_dollar
        _t808 = _t807(msg)
        fields168 = _t808
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
                _t809 = self.pretty_term(elem170)
        self.dedent()
        self.write(')')

    def pretty_term(self, msg: logic_pb2.Term):
        def _t810(_dollar_dollar):
            
            if _dollar_dollar.HasField('var'):
                _t811 = _dollar_dollar.var
            else:
                _t811 = None
            return _t811
        _t812 = _t810(msg)
        deconstruct_result173 = _t812
        
        if deconstruct_result173 is not None:
            _t814 = self.pretty_var(deconstruct_result173)
            _t813 = _t814
        else:
            def _t815(_dollar_dollar):
                
                if _dollar_dollar.HasField('constant'):
                    _t816 = _dollar_dollar.constant
                else:
                    _t816 = None
                return _t816
            _t817 = _t815(msg)
            deconstruct_result172 = _t817
            
            if deconstruct_result172 is not None:
                _t819 = self.pretty_constant(deconstruct_result172)
                _t818 = _t819
            else:
                raise ParseError('No matching rule for term')
            _t813 = _t818

    def pretty_var(self, msg: logic_pb2.Var):
        def _t820(_dollar_dollar):
            return _dollar_dollar.name
        _t821 = _t820(msg)
        fields174 = _t821
        assert fields174 is not None
        unwrapped_fields175 = fields174
        self.write(unwrapped_fields175)

    def pretty_constant(self, msg: logic_pb2.Value):
        def _t822(_dollar_dollar):
            return _dollar_dollar
        _t823 = _t822(msg)
        fields176 = _t823
        assert fields176 is not None
        unwrapped_fields177 = fields176
        _t824 = self.pretty_value(unwrapped_fields177)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        def _t825(_dollar_dollar):
            return _dollar_dollar.args
        _t826 = _t825(msg)
        fields178 = _t826
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
                _t827 = self.pretty_formula(elem180)
        self.dedent()
        self.write(')')

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        def _t828(_dollar_dollar):
            return _dollar_dollar.args
        _t829 = _t828(msg)
        fields182 = _t829
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
                _t830 = self.pretty_formula(elem184)
        self.dedent()
        self.write(')')

    def pretty_not(self, msg: logic_pb2.Not):
        def _t831(_dollar_dollar):
            return _dollar_dollar.arg
        _t832 = _t831(msg)
        fields186 = _t832
        assert fields186 is not None
        unwrapped_fields187 = fields186
        self.write('(')
        self.write('not')
        self.indent()
        self.newline()
        _t833 = self.pretty_formula(unwrapped_fields187)
        self.dedent()
        self.write(')')

    def pretty_ffi(self, msg: logic_pb2.FFI):
        def _t834(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t835 = _t834(msg)
        fields188 = _t835
        assert fields188 is not None
        unwrapped_fields189 = fields188
        self.write('(')
        self.write('ffi')
        self.indent()
        self.newline()
        field190 = unwrapped_fields189[0]
        _t836 = self.pretty_name(field190)
        self.newline()
        field191 = unwrapped_fields189[1]
        _t837 = self.pretty_ffi_args(field191)
        self.newline()
        field192 = unwrapped_fields189[2]
        _t838 = self.pretty_terms(field192)
        self.dedent()
        self.write(')')

    def pretty_name(self, msg: str):
        def _t839(_dollar_dollar):
            return _dollar_dollar
        _t840 = _t839(msg)
        fields193 = _t840
        assert fields193 is not None
        unwrapped_fields194 = fields193
        self.write(':')
        self.write(unwrapped_fields194)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        def _t841(_dollar_dollar):
            return _dollar_dollar
        _t842 = _t841(msg)
        fields195 = _t842
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
                _t843 = self.pretty_abstraction(elem197)
        self.dedent()
        self.write(')')

    def pretty_atom(self, msg: logic_pb2.Atom):
        def _t844(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t845 = _t844(msg)
        fields199 = _t845
        assert fields199 is not None
        unwrapped_fields200 = fields199
        self.write('(')
        self.write('atom')
        self.indent()
        self.newline()
        field201 = unwrapped_fields200[0]
        _t846 = self.pretty_relation_id(field201)
        field202 = unwrapped_fields200[1]
        if not len(field202) == 0:
            self.newline()
            for i204, elem203 in enumerate(field202):
                if (i204 > 0):
                    self.newline()
                _t847 = self.pretty_term(elem203)
        self.dedent()
        self.write(')')

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        def _t848(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t849 = _t848(msg)
        fields205 = _t849
        assert fields205 is not None
        unwrapped_fields206 = fields205
        self.write('(')
        self.write('pragma')
        self.indent()
        self.newline()
        field207 = unwrapped_fields206[0]
        _t850 = self.pretty_name(field207)
        field208 = unwrapped_fields206[1]
        if not len(field208) == 0:
            self.newline()
            for i210, elem209 in enumerate(field208):
                if (i210 > 0):
                    self.newline()
                _t851 = self.pretty_term(elem209)
        self.dedent()
        self.write(')')

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        def _t852(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t853 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t853 = None
            return _t853
        _t854 = _t852(msg)
        guard_result225 = _t854
        
        if guard_result225 is not None:
            _t856 = self.pretty_eq(msg)
            _t855 = _t856
        else:
            def _t857(_dollar_dollar):
                
                if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                    _t858 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t858 = None
                return _t858
            _t859 = _t857(msg)
            guard_result224 = _t859
            
            if guard_result224 is not None:
                _t861 = self.pretty_lt(msg)
                _t860 = _t861
            else:
                def _t862(_dollar_dollar):
                    
                    if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                        _t863 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t863 = None
                    return _t863
                _t864 = _t862(msg)
                guard_result223 = _t864
                
                if guard_result223 is not None:
                    _t866 = self.pretty_lt_eq(msg)
                    _t865 = _t866
                else:
                    def _t867(_dollar_dollar):
                        
                        if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                            _t868 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t868 = None
                        return _t868
                    _t869 = _t867(msg)
                    guard_result222 = _t869
                    
                    if guard_result222 is not None:
                        _t871 = self.pretty_gt(msg)
                        _t870 = _t871
                    else:
                        def _t872(_dollar_dollar):
                            
                            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                                _t873 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t873 = None
                            return _t873
                        _t874 = _t872(msg)
                        guard_result221 = _t874
                        
                        if guard_result221 is not None:
                            _t876 = self.pretty_gt_eq(msg)
                            _t875 = _t876
                        else:
                            def _t877(_dollar_dollar):
                                
                                if _dollar_dollar.name == 'rel_primitive_add_monotype':
                                    _t878 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t878 = None
                                return _t878
                            _t879 = _t877(msg)
                            guard_result220 = _t879
                            
                            if guard_result220 is not None:
                                _t881 = self.pretty_add(msg)
                                _t880 = _t881
                            else:
                                def _t882(_dollar_dollar):
                                    
                                    if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                                        _t883 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t883 = None
                                    return _t883
                                _t884 = _t882(msg)
                                guard_result219 = _t884
                                
                                if guard_result219 is not None:
                                    _t886 = self.pretty_minus(msg)
                                    _t885 = _t886
                                else:
                                    def _t887(_dollar_dollar):
                                        
                                        if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                                            _t888 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t888 = None
                                        return _t888
                                    _t889 = _t887(msg)
                                    guard_result218 = _t889
                                    
                                    if guard_result218 is not None:
                                        _t891 = self.pretty_multiply(msg)
                                        _t890 = _t891
                                    else:
                                        def _t892(_dollar_dollar):
                                            
                                            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                                                _t893 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t893 = None
                                            return _t893
                                        _t894 = _t892(msg)
                                        guard_result217 = _t894
                                        
                                        if guard_result217 is not None:
                                            _t896 = self.pretty_divide(msg)
                                            _t895 = _t896
                                        else:
                                            def _t897(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t898 = _t897(msg)
                                            fields211 = _t898
                                            assert fields211 is not None
                                            unwrapped_fields212 = fields211
                                            self.write('(')
                                            self.write('primitive')
                                            self.indent()
                                            self.newline()
                                            field213 = unwrapped_fields212[0]
                                            _t899 = self.pretty_name(field213)
                                            field214 = unwrapped_fields212[1]
                                            if not len(field214) == 0:
                                                self.newline()
                                                for i216, elem215 in enumerate(field214):
                                                    if (i216 > 0):
                                                        self.newline()
                                                    _t900 = self.pretty_rel_term(elem215)
                                            self.dedent()
                                            self.write(')')
                                            _t895 = None
                                        _t890 = _t895
                                    _t885 = _t890
                                _t880 = _t885
                            _t875 = _t880
                        _t870 = _t875
                    _t865 = _t870
                _t860 = _t865
            _t855 = _t860

    def pretty_eq(self, msg: logic_pb2.Primitive):
        def _t901(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_eq':
                _t902 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t902 = None
            return _t902
        _t903 = _t901(msg)
        fields226 = _t903
        assert fields226 is not None
        unwrapped_fields227 = fields226
        self.write('(')
        self.write('=')
        self.indent()
        self.newline()
        field228 = unwrapped_fields227[0]
        _t904 = self.pretty_term(field228)
        self.newline()
        field229 = unwrapped_fields227[1]
        _t905 = self.pretty_term(field229)
        self.dedent()
        self.write(')')

    def pretty_lt(self, msg: logic_pb2.Primitive):
        def _t906(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_monotype':
                _t907 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t907 = None
            return _t907
        _t908 = _t906(msg)
        fields230 = _t908
        assert fields230 is not None
        unwrapped_fields231 = fields230
        self.write('(')
        self.write('<')
        self.indent()
        self.newline()
        field232 = unwrapped_fields231[0]
        _t909 = self.pretty_term(field232)
        self.newline()
        field233 = unwrapped_fields231[1]
        _t910 = self.pretty_term(field233)
        self.dedent()
        self.write(')')

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        def _t911(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_lt_eq_monotype':
                _t912 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t912 = None
            return _t912
        _t913 = _t911(msg)
        fields234 = _t913
        assert fields234 is not None
        unwrapped_fields235 = fields234
        self.write('(')
        self.write('<=')
        self.indent()
        self.newline()
        field236 = unwrapped_fields235[0]
        _t914 = self.pretty_term(field236)
        self.newline()
        field237 = unwrapped_fields235[1]
        _t915 = self.pretty_term(field237)
        self.dedent()
        self.write(')')

    def pretty_gt(self, msg: logic_pb2.Primitive):
        def _t916(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_monotype':
                _t917 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t917 = None
            return _t917
        _t918 = _t916(msg)
        fields238 = _t918
        assert fields238 is not None
        unwrapped_fields239 = fields238
        self.write('(')
        self.write('>')
        self.indent()
        self.newline()
        field240 = unwrapped_fields239[0]
        _t919 = self.pretty_term(field240)
        self.newline()
        field241 = unwrapped_fields239[1]
        _t920 = self.pretty_term(field241)
        self.dedent()
        self.write(')')

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        def _t921(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_gt_eq_monotype':
                _t922 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t922 = None
            return _t922
        _t923 = _t921(msg)
        fields242 = _t923
        assert fields242 is not None
        unwrapped_fields243 = fields242
        self.write('(')
        self.write('>=')
        self.indent()
        self.newline()
        field244 = unwrapped_fields243[0]
        _t924 = self.pretty_term(field244)
        self.newline()
        field245 = unwrapped_fields243[1]
        _t925 = self.pretty_term(field245)
        self.dedent()
        self.write(')')

    def pretty_add(self, msg: logic_pb2.Primitive):
        def _t926(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_add_monotype':
                _t927 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t927 = None
            return _t927
        _t928 = _t926(msg)
        fields246 = _t928
        assert fields246 is not None
        unwrapped_fields247 = fields246
        self.write('(')
        self.write('+')
        self.indent()
        self.newline()
        field248 = unwrapped_fields247[0]
        _t929 = self.pretty_term(field248)
        self.newline()
        field249 = unwrapped_fields247[1]
        _t930 = self.pretty_term(field249)
        self.newline()
        field250 = unwrapped_fields247[2]
        _t931 = self.pretty_term(field250)
        self.dedent()
        self.write(')')

    def pretty_minus(self, msg: logic_pb2.Primitive):
        def _t932(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_subtract_monotype':
                _t933 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t933 = None
            return _t933
        _t934 = _t932(msg)
        fields251 = _t934
        assert fields251 is not None
        unwrapped_fields252 = fields251
        self.write('(')
        self.write('-')
        self.indent()
        self.newline()
        field253 = unwrapped_fields252[0]
        _t935 = self.pretty_term(field253)
        self.newline()
        field254 = unwrapped_fields252[1]
        _t936 = self.pretty_term(field254)
        self.newline()
        field255 = unwrapped_fields252[2]
        _t937 = self.pretty_term(field255)
        self.dedent()
        self.write(')')

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        def _t938(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_multiply_monotype':
                _t939 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t939 = None
            return _t939
        _t940 = _t938(msg)
        fields256 = _t940
        assert fields256 is not None
        unwrapped_fields257 = fields256
        self.write('(')
        self.write('*')
        self.indent()
        self.newline()
        field258 = unwrapped_fields257[0]
        _t941 = self.pretty_term(field258)
        self.newline()
        field259 = unwrapped_fields257[1]
        _t942 = self.pretty_term(field259)
        self.newline()
        field260 = unwrapped_fields257[2]
        _t943 = self.pretty_term(field260)
        self.dedent()
        self.write(')')

    def pretty_divide(self, msg: logic_pb2.Primitive):
        def _t944(_dollar_dollar):
            
            if _dollar_dollar.name == 'rel_primitive_divide_monotype':
                _t945 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t945 = None
            return _t945
        _t946 = _t944(msg)
        fields261 = _t946
        assert fields261 is not None
        unwrapped_fields262 = fields261
        self.write('(')
        self.write('/')
        self.indent()
        self.newline()
        field263 = unwrapped_fields262[0]
        _t947 = self.pretty_term(field263)
        self.newline()
        field264 = unwrapped_fields262[1]
        _t948 = self.pretty_term(field264)
        self.newline()
        field265 = unwrapped_fields262[2]
        _t949 = self.pretty_term(field265)
        self.dedent()
        self.write(')')

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        def _t950(_dollar_dollar):
            
            if _dollar_dollar.HasField('specialized_value'):
                _t951 = _dollar_dollar.specialized_value
            else:
                _t951 = None
            return _t951
        _t952 = _t950(msg)
        deconstruct_result267 = _t952
        
        if deconstruct_result267 is not None:
            _t954 = self.pretty_specialized_value(deconstruct_result267)
            _t953 = _t954
        else:
            def _t955(_dollar_dollar):
                
                if _dollar_dollar.HasField('term'):
                    _t956 = _dollar_dollar.term
                else:
                    _t956 = None
                return _t956
            _t957 = _t955(msg)
            deconstruct_result266 = _t957
            
            if deconstruct_result266 is not None:
                _t959 = self.pretty_term(deconstruct_result266)
                _t958 = _t959
            else:
                raise ParseError('No matching rule for rel_term')
            _t953 = _t958

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        def _t960(_dollar_dollar):
            return _dollar_dollar
        _t961 = _t960(msg)
        fields268 = _t961
        assert fields268 is not None
        unwrapped_fields269 = fields268
        self.write('#')
        _t962 = self.pretty_value(unwrapped_fields269)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        def _t963(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t964 = _t963(msg)
        fields270 = _t964
        assert fields270 is not None
        unwrapped_fields271 = fields270
        self.write('(')
        self.write('relatom')
        self.indent()
        self.newline()
        field272 = unwrapped_fields271[0]
        _t965 = self.pretty_name(field272)
        field273 = unwrapped_fields271[1]
        if not len(field273) == 0:
            self.newline()
            for i275, elem274 in enumerate(field273):
                if (i275 > 0):
                    self.newline()
                _t966 = self.pretty_rel_term(elem274)
        self.dedent()
        self.write(')')

    def pretty_cast(self, msg: logic_pb2.Cast):
        def _t967(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t968 = _t967(msg)
        fields276 = _t968
        assert fields276 is not None
        unwrapped_fields277 = fields276
        self.write('(')
        self.write('cast')
        self.indent()
        self.newline()
        field278 = unwrapped_fields277[0]
        _t969 = self.pretty_term(field278)
        self.newline()
        field279 = unwrapped_fields277[1]
        _t970 = self.pretty_term(field279)
        self.dedent()
        self.write(')')

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        def _t971(_dollar_dollar):
            return _dollar_dollar
        _t972 = _t971(msg)
        fields280 = _t972
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
                _t973 = self.pretty_attribute(elem282)
        self.dedent()
        self.write(')')

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        def _t974(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t975 = _t974(msg)
        fields284 = _t975
        assert fields284 is not None
        unwrapped_fields285 = fields284
        self.write('(')
        self.write('attribute')
        self.indent()
        self.newline()
        field286 = unwrapped_fields285[0]
        _t976 = self.pretty_name(field286)
        field287 = unwrapped_fields285[1]
        if not len(field287) == 0:
            self.newline()
            for i289, elem288 in enumerate(field287):
                if (i289 > 0):
                    self.newline()
                _t977 = self.pretty_value(elem288)
        self.dedent()
        self.write(')')

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        def _t978(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t979 = _t978(msg)
        fields290 = _t979
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
                _t980 = self.pretty_relation_id(elem293)
        self.newline()
        field295 = unwrapped_fields291[1]
        _t981 = self.pretty_script(field295)
        self.dedent()
        self.write(')')

    def pretty_script(self, msg: logic_pb2.Script):
        def _t982(_dollar_dollar):
            return _dollar_dollar.constructs
        _t983 = _t982(msg)
        fields296 = _t983
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
                _t984 = self.pretty_construct(elem298)
        self.dedent()
        self.write(')')

    def pretty_construct(self, msg: logic_pb2.Construct):
        def _t985(_dollar_dollar):
            
            if _dollar_dollar.HasField('loop'):
                _t986 = _dollar_dollar.loop
            else:
                _t986 = None
            return _t986
        _t987 = _t985(msg)
        deconstruct_result301 = _t987
        
        if deconstruct_result301 is not None:
            _t989 = self.pretty_loop(deconstruct_result301)
            _t988 = _t989
        else:
            def _t990(_dollar_dollar):
                
                if _dollar_dollar.HasField('instruction'):
                    _t991 = _dollar_dollar.instruction
                else:
                    _t991 = None
                return _t991
            _t992 = _t990(msg)
            deconstruct_result300 = _t992
            
            if deconstruct_result300 is not None:
                _t994 = self.pretty_instruction(deconstruct_result300)
                _t993 = _t994
            else:
                raise ParseError('No matching rule for construct')
            _t988 = _t993

    def pretty_loop(self, msg: logic_pb2.Loop):
        def _t995(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t996 = _t995(msg)
        fields302 = _t996
        assert fields302 is not None
        unwrapped_fields303 = fields302
        self.write('(')
        self.write('loop')
        self.indent()
        self.newline()
        field304 = unwrapped_fields303[0]
        _t997 = self.pretty_init(field304)
        self.newline()
        field305 = unwrapped_fields303[1]
        _t998 = self.pretty_script(field305)
        self.dedent()
        self.write(')')

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        def _t999(_dollar_dollar):
            return _dollar_dollar
        _t1000 = _t999(msg)
        fields306 = _t1000
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
                _t1001 = self.pretty_instruction(elem308)
        self.dedent()
        self.write(')')

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        def _t1002(_dollar_dollar):
            
            if _dollar_dollar.HasField('assign'):
                _t1003 = _dollar_dollar.assign
            else:
                _t1003 = None
            return _t1003
        _t1004 = _t1002(msg)
        deconstruct_result314 = _t1004
        
        if deconstruct_result314 is not None:
            _t1006 = self.pretty_assign(deconstruct_result314)
            _t1005 = _t1006
        else:
            def _t1007(_dollar_dollar):
                
                if _dollar_dollar.HasField('upsert'):
                    _t1008 = _dollar_dollar.upsert
                else:
                    _t1008 = None
                return _t1008
            _t1009 = _t1007(msg)
            deconstruct_result313 = _t1009
            
            if deconstruct_result313 is not None:
                _t1011 = self.pretty_upsert(deconstruct_result313)
                _t1010 = _t1011
            else:
                def _t1012(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('break'):
                        _t1013 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1013 = None
                    return _t1013
                _t1014 = _t1012(msg)
                deconstruct_result312 = _t1014
                
                if deconstruct_result312 is not None:
                    _t1016 = self.pretty_break(deconstruct_result312)
                    _t1015 = _t1016
                else:
                    def _t1017(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('monoid_def'):
                            _t1018 = _dollar_dollar.monoid_def
                        else:
                            _t1018 = None
                        return _t1018
                    _t1019 = _t1017(msg)
                    deconstruct_result311 = _t1019
                    
                    if deconstruct_result311 is not None:
                        _t1021 = self.pretty_monoid_def(deconstruct_result311)
                        _t1020 = _t1021
                    else:
                        def _t1022(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('monus_def'):
                                _t1023 = _dollar_dollar.monus_def
                            else:
                                _t1023 = None
                            return _t1023
                        _t1024 = _t1022(msg)
                        deconstruct_result310 = _t1024
                        
                        if deconstruct_result310 is not None:
                            _t1026 = self.pretty_monus_def(deconstruct_result310)
                            _t1025 = _t1026
                        else:
                            raise ParseError('No matching rule for instruction')
                        _t1020 = _t1025
                    _t1015 = _t1020
                _t1010 = _t1015
            _t1005 = _t1010

    def pretty_assign(self, msg: logic_pb2.Assign):
        def _t1027(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1028 = _dollar_dollar.attrs
            else:
                _t1028 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1028,)
        _t1029 = _t1027(msg)
        fields315 = _t1029
        assert fields315 is not None
        unwrapped_fields316 = fields315
        self.write('(')
        self.write('assign')
        self.indent()
        self.newline()
        field317 = unwrapped_fields316[0]
        _t1030 = self.pretty_relation_id(field317)
        self.newline()
        field318 = unwrapped_fields316[1]
        _t1031 = self.pretty_abstraction(field318)
        field319 = unwrapped_fields316[2]
        
        if field319 is not None:
            self.newline()
            assert field319 is not None
            opt_val320 = field319
            _t1033 = self.pretty_attrs(opt_val320)
            _t1032 = _t1033
        else:
            _t1032 = None
        self.dedent()
        self.write(')')

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        def _t1034(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1035 = _dollar_dollar.attrs
            else:
                _t1035 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1035,)
        _t1036 = _t1034(msg)
        fields321 = _t1036
        assert fields321 is not None
        unwrapped_fields322 = fields321
        self.write('(')
        self.write('upsert')
        self.indent()
        self.newline()
        field323 = unwrapped_fields322[0]
        _t1037 = self.pretty_relation_id(field323)
        self.newline()
        field324 = unwrapped_fields322[1]
        _t1038 = self.pretty_abstraction_with_arity(field324)
        field325 = unwrapped_fields322[2]
        
        if field325 is not None:
            self.newline()
            assert field325 is not None
            opt_val326 = field325
            _t1040 = self.pretty_attrs(opt_val326)
            _t1039 = _t1040
        else:
            _t1039 = None
        self.dedent()
        self.write(')')

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        def _t1041(_dollar_dollar):
            _t1042 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1042, _dollar_dollar[0].value,)
        _t1043 = _t1041(msg)
        fields327 = _t1043
        assert fields327 is not None
        unwrapped_fields328 = fields327
        self.write('(')
        field329 = unwrapped_fields328[0]
        _t1044 = self.pretty_bindings(field329)
        self.write(' ')
        field330 = unwrapped_fields328[1]
        _t1045 = self.pretty_formula(field330)
        self.write(')')

    def pretty_break(self, msg: logic_pb2.Break):
        def _t1046(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1047 = _dollar_dollar.attrs
            else:
                _t1047 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1047,)
        _t1048 = _t1046(msg)
        fields331 = _t1048
        assert fields331 is not None
        unwrapped_fields332 = fields331
        self.write('(')
        self.write('break')
        self.indent()
        self.newline()
        field333 = unwrapped_fields332[0]
        _t1049 = self.pretty_relation_id(field333)
        self.newline()
        field334 = unwrapped_fields332[1]
        _t1050 = self.pretty_abstraction(field334)
        field335 = unwrapped_fields332[2]
        
        if field335 is not None:
            self.newline()
            assert field335 is not None
            opt_val336 = field335
            _t1052 = self.pretty_attrs(opt_val336)
            _t1051 = _t1052
        else:
            _t1051 = None
        self.dedent()
        self.write(')')

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        def _t1053(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1054 = _dollar_dollar.attrs
            else:
                _t1054 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1054,)
        _t1055 = _t1053(msg)
        fields337 = _t1055
        assert fields337 is not None
        unwrapped_fields338 = fields337
        self.write('(')
        self.write('monoid')
        self.indent()
        self.newline()
        field339 = unwrapped_fields338[0]
        _t1056 = self.pretty_monoid(field339)
        self.newline()
        field340 = unwrapped_fields338[1]
        _t1057 = self.pretty_relation_id(field340)
        self.newline()
        field341 = unwrapped_fields338[2]
        _t1058 = self.pretty_abstraction_with_arity(field341)
        field342 = unwrapped_fields338[3]
        
        if field342 is not None:
            self.newline()
            assert field342 is not None
            opt_val343 = field342
            _t1060 = self.pretty_attrs(opt_val343)
            _t1059 = _t1060
        else:
            _t1059 = None
        self.dedent()
        self.write(')')

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        def _t1061(_dollar_dollar):
            
            if _dollar_dollar.HasField('or_monoid'):
                _t1062 = _dollar_dollar.or_monoid
            else:
                _t1062 = None
            return _t1062
        _t1063 = _t1061(msg)
        deconstruct_result347 = _t1063
        
        if deconstruct_result347 is not None:
            _t1065 = self.pretty_or_monoid(deconstruct_result347)
            _t1064 = _t1065
        else:
            def _t1066(_dollar_dollar):
                
                if _dollar_dollar.HasField('min_monoid'):
                    _t1067 = _dollar_dollar.min_monoid
                else:
                    _t1067 = None
                return _t1067
            _t1068 = _t1066(msg)
            deconstruct_result346 = _t1068
            
            if deconstruct_result346 is not None:
                _t1070 = self.pretty_min_monoid(deconstruct_result346)
                _t1069 = _t1070
            else:
                def _t1071(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('max_monoid'):
                        _t1072 = _dollar_dollar.max_monoid
                    else:
                        _t1072 = None
                    return _t1072
                _t1073 = _t1071(msg)
                deconstruct_result345 = _t1073
                
                if deconstruct_result345 is not None:
                    _t1075 = self.pretty_max_monoid(deconstruct_result345)
                    _t1074 = _t1075
                else:
                    def _t1076(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('sum_monoid'):
                            _t1077 = _dollar_dollar.sum_monoid
                        else:
                            _t1077 = None
                        return _t1077
                    _t1078 = _t1076(msg)
                    deconstruct_result344 = _t1078
                    
                    if deconstruct_result344 is not None:
                        _t1080 = self.pretty_sum_monoid(deconstruct_result344)
                        _t1079 = _t1080
                    else:
                        raise ParseError('No matching rule for monoid')
                    _t1074 = _t1079
                _t1069 = _t1074
            _t1064 = _t1069

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        def _t1081(_dollar_dollar):
            return _dollar_dollar
        _t1082 = _t1081(msg)
        fields348 = _t1082
        assert fields348 is not None
        unwrapped_fields349 = fields348
        self.write('(')
        self.write('or')
        self.write(')')

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        def _t1083(_dollar_dollar):
            return _dollar_dollar.type
        _t1084 = _t1083(msg)
        fields350 = _t1084
        assert fields350 is not None
        unwrapped_fields351 = fields350
        self.write('(')
        self.write('min')
        self.indent()
        self.newline()
        _t1085 = self.pretty_type(unwrapped_fields351)
        self.dedent()
        self.write(')')

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        def _t1086(_dollar_dollar):
            return _dollar_dollar.type
        _t1087 = _t1086(msg)
        fields352 = _t1087
        assert fields352 is not None
        unwrapped_fields353 = fields352
        self.write('(')
        self.write('max')
        self.indent()
        self.newline()
        _t1088 = self.pretty_type(unwrapped_fields353)
        self.dedent()
        self.write(')')

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        def _t1089(_dollar_dollar):
            return _dollar_dollar.type
        _t1090 = _t1089(msg)
        fields354 = _t1090
        assert fields354 is not None
        unwrapped_fields355 = fields354
        self.write('(')
        self.write('sum')
        self.indent()
        self.newline()
        _t1091 = self.pretty_type(unwrapped_fields355)
        self.dedent()
        self.write(')')

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        def _t1092(_dollar_dollar):
            
            if not len(_dollar_dollar.attrs) == 0:
                _t1093 = _dollar_dollar.attrs
            else:
                _t1093 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1093,)
        _t1094 = _t1092(msg)
        fields356 = _t1094
        assert fields356 is not None
        unwrapped_fields357 = fields356
        self.write('(')
        self.write('monus')
        self.indent()
        self.newline()
        field358 = unwrapped_fields357[0]
        _t1095 = self.pretty_monoid(field358)
        self.newline()
        field359 = unwrapped_fields357[1]
        _t1096 = self.pretty_relation_id(field359)
        self.newline()
        field360 = unwrapped_fields357[2]
        _t1097 = self.pretty_abstraction_with_arity(field360)
        field361 = unwrapped_fields357[3]
        
        if field361 is not None:
            self.newline()
            assert field361 is not None
            opt_val362 = field361
            _t1099 = self.pretty_attrs(opt_val362)
            _t1098 = _t1099
        else:
            _t1098 = None
        self.dedent()
        self.write(')')

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        def _t1100(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1101 = _t1100(msg)
        fields363 = _t1101
        assert fields363 is not None
        unwrapped_fields364 = fields363
        self.write('(')
        self.write('functional_dependency')
        self.indent()
        self.newline()
        field365 = unwrapped_fields364[0]
        _t1102 = self.pretty_relation_id(field365)
        self.newline()
        field366 = unwrapped_fields364[1]
        _t1103 = self.pretty_abstraction(field366)
        self.newline()
        field367 = unwrapped_fields364[2]
        _t1104 = self.pretty_functional_dependency_keys(field367)
        self.newline()
        field368 = unwrapped_fields364[3]
        _t1105 = self.pretty_functional_dependency_values(field368)
        self.dedent()
        self.write(')')

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        def _t1106(_dollar_dollar):
            return _dollar_dollar
        _t1107 = _t1106(msg)
        fields369 = _t1107
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
                _t1108 = self.pretty_var(elem371)
        self.dedent()
        self.write(')')

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        def _t1109(_dollar_dollar):
            return _dollar_dollar
        _t1110 = _t1109(msg)
        fields373 = _t1110
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
                _t1111 = self.pretty_var(elem375)
        self.dedent()
        self.write(')')

    def pretty_data(self, msg: logic_pb2.Data):
        def _t1112(_dollar_dollar):
            
            if _dollar_dollar.HasField('rel_edb'):
                _t1113 = _dollar_dollar.rel_edb
            else:
                _t1113 = None
            return _t1113
        _t1114 = _t1112(msg)
        deconstruct_result379 = _t1114
        
        if deconstruct_result379 is not None:
            _t1116 = self.pretty_rel_edb(deconstruct_result379)
            _t1115 = _t1116
        else:
            def _t1117(_dollar_dollar):
                
                if _dollar_dollar.HasField('betree_relation'):
                    _t1118 = _dollar_dollar.betree_relation
                else:
                    _t1118 = None
                return _t1118
            _t1119 = _t1117(msg)
            deconstruct_result378 = _t1119
            
            if deconstruct_result378 is not None:
                _t1121 = self.pretty_betree_relation(deconstruct_result378)
                _t1120 = _t1121
            else:
                def _t1122(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('csv_data'):
                        _t1123 = _dollar_dollar.csv_data
                    else:
                        _t1123 = None
                    return _t1123
                _t1124 = _t1122(msg)
                deconstruct_result377 = _t1124
                
                if deconstruct_result377 is not None:
                    _t1126 = self.pretty_csv_data(deconstruct_result377)
                    _t1125 = _t1126
                else:
                    raise ParseError('No matching rule for data')
                _t1120 = _t1125
            _t1115 = _t1120

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB):
        def _t1127(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1128 = _t1127(msg)
        fields380 = _t1128
        assert fields380 is not None
        unwrapped_fields381 = fields380
        self.write('(')
        self.write('rel_edb')
        self.indent()
        self.newline()
        field382 = unwrapped_fields381[0]
        _t1129 = self.pretty_relation_id(field382)
        self.newline()
        field383 = unwrapped_fields381[1]
        _t1130 = self.pretty_rel_edb_path(field383)
        self.newline()
        field384 = unwrapped_fields381[2]
        _t1131 = self.pretty_rel_edb_types(field384)
        self.dedent()
        self.write(')')

    def pretty_rel_edb_path(self, msg: Sequence[str]):
        def _t1132(_dollar_dollar):
            return _dollar_dollar
        _t1133 = _t1132(msg)
        fields385 = _t1133
        assert fields385 is not None
        unwrapped_fields386 = fields385
        self.write('[')
        for i388, elem387 in enumerate(unwrapped_fields386):
            if (i388 > 0):
                self.newline()
            self.write(self.format_string_value(elem387))
        self.write(']')

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]):
        def _t1134(_dollar_dollar):
            return _dollar_dollar
        _t1135 = _t1134(msg)
        fields389 = _t1135
        assert fields389 is not None
        unwrapped_fields390 = fields389
        self.write('[')
        for i392, elem391 in enumerate(unwrapped_fields390):
            if (i392 > 0):
                self.newline()
            _t1136 = self.pretty_type(elem391)
        self.write(']')

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        def _t1137(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1138 = _t1137(msg)
        fields393 = _t1138
        assert fields393 is not None
        unwrapped_fields394 = fields393
        self.write('(')
        self.write('betree_relation')
        self.indent()
        self.newline()
        field395 = unwrapped_fields394[0]
        _t1139 = self.pretty_relation_id(field395)
        self.newline()
        field396 = unwrapped_fields394[1]
        _t1140 = self.pretty_betree_info(field396)
        self.dedent()
        self.write(')')

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        def _t1141(_dollar_dollar):
            _t1142 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1142,)
        _t1143 = _t1141(msg)
        fields397 = _t1143
        assert fields397 is not None
        unwrapped_fields398 = fields397
        self.write('(')
        self.write('betree_info')
        self.indent()
        self.newline()
        field399 = unwrapped_fields398[0]
        _t1144 = self.pretty_betree_info_key_types(field399)
        self.newline()
        field400 = unwrapped_fields398[1]
        _t1145 = self.pretty_betree_info_value_types(field400)
        self.newline()
        field401 = unwrapped_fields398[2]
        _t1146 = self.pretty_config_dict(field401)
        self.dedent()
        self.write(')')

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        def _t1147(_dollar_dollar):
            return _dollar_dollar
        _t1148 = _t1147(msg)
        fields402 = _t1148
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
                _t1149 = self.pretty_type(elem404)
        self.dedent()
        self.write(')')

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        def _t1150(_dollar_dollar):
            return _dollar_dollar
        _t1151 = _t1150(msg)
        fields406 = _t1151
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
                _t1152 = self.pretty_type(elem408)
        self.dedent()
        self.write(')')

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        def _t1153(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1154 = _t1153(msg)
        fields410 = _t1154
        assert fields410 is not None
        unwrapped_fields411 = fields410
        self.write('(')
        self.write('csv_data')
        self.indent()
        self.newline()
        field412 = unwrapped_fields411[0]
        _t1155 = self.pretty_csvlocator(field412)
        self.newline()
        field413 = unwrapped_fields411[1]
        _t1156 = self.pretty_csv_config(field413)
        self.newline()
        field414 = unwrapped_fields411[2]
        _t1157 = self.pretty_csv_columns(field414)
        self.newline()
        field415 = unwrapped_fields411[3]
        _t1158 = self.pretty_csv_asof(field415)
        self.dedent()
        self.write(')')

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        def _t1159(_dollar_dollar):
            
            if not len(_dollar_dollar.paths) == 0:
                _t1160 = _dollar_dollar.paths
            else:
                _t1160 = None
            
            if _dollar_dollar.inline_data.decode('utf-8') != '':
                _t1161 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1161 = None
            return (_t1160, _t1161,)
        _t1162 = _t1159(msg)
        fields416 = _t1162
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
            _t1164 = self.pretty_csv_locator_paths(opt_val419)
            _t1163 = _t1164
        else:
            _t1163 = None
        field420 = unwrapped_fields417[1]
        
        if field420 is not None:
            self.newline()
            assert field420 is not None
            opt_val421 = field420
            _t1166 = self.pretty_csv_locator_inline_data(opt_val421)
            _t1165 = _t1166
        else:
            _t1165 = None
        self.dedent()
        self.write(')')

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        def _t1167(_dollar_dollar):
            return _dollar_dollar
        _t1168 = _t1167(msg)
        fields422 = _t1168
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

    def pretty_csv_locator_inline_data(self, msg: str):
        def _t1169(_dollar_dollar):
            return _dollar_dollar
        _t1170 = _t1169(msg)
        fields426 = _t1170
        assert fields426 is not None
        unwrapped_fields427 = fields426
        self.write('(')
        self.write('inline_data')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields427))
        self.dedent()
        self.write(')')

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        def _t1171(_dollar_dollar):
            _t1172 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1172
        _t1173 = _t1171(msg)
        fields428 = _t1173
        assert fields428 is not None
        unwrapped_fields429 = fields428
        self.write('(')
        self.write('csv_config')
        self.indent()
        self.newline()
        _t1174 = self.pretty_config_dict(unwrapped_fields429)
        self.dedent()
        self.write(')')

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]):
        def _t1175(_dollar_dollar):
            return _dollar_dollar
        _t1176 = _t1175(msg)
        fields430 = _t1176
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
                _t1177 = self.pretty_csv_column(elem432)
        self.dedent()
        self.write(')')

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn):
        def _t1178(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1179 = _t1178(msg)
        fields434 = _t1179
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
        _t1180 = self.pretty_relation_id(field437)
        self.newline()
        self.write('[')
        field438 = unwrapped_fields435[2]
        for i440, elem439 in enumerate(field438):
            if (i440 > 0):
                self.newline()
            _t1181 = self.pretty_type(elem439)
        self.write(']')
        self.dedent()
        self.write(')')

    def pretty_csv_asof(self, msg: str):
        def _t1182(_dollar_dollar):
            return _dollar_dollar
        _t1183 = _t1182(msg)
        fields441 = _t1183
        assert fields441 is not None
        unwrapped_fields442 = fields441
        self.write('(')
        self.write('asof')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields442))
        self.dedent()
        self.write(')')

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        def _t1184(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1185 = _t1184(msg)
        fields443 = _t1185
        assert fields443 is not None
        unwrapped_fields444 = fields443
        self.write('(')
        self.write('undefine')
        self.indent()
        self.newline()
        _t1186 = self.pretty_fragment_id(unwrapped_fields444)
        self.dedent()
        self.write(')')

    def pretty_context(self, msg: transactions_pb2.Context):
        def _t1187(_dollar_dollar):
            return _dollar_dollar.relations
        _t1188 = _t1187(msg)
        fields445 = _t1188
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
                _t1189 = self.pretty_relation_id(elem447)
        self.dedent()
        self.write(')')

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        def _t1190(_dollar_dollar):
            return _dollar_dollar
        _t1191 = _t1190(msg)
        fields449 = _t1191
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
                _t1192 = self.pretty_read(elem451)
        self.dedent()
        self.write(')')

    def pretty_read(self, msg: transactions_pb2.Read):
        def _t1193(_dollar_dollar):
            
            if _dollar_dollar.HasField('demand'):
                _t1194 = _dollar_dollar.demand
            else:
                _t1194 = None
            return _t1194
        _t1195 = _t1193(msg)
        deconstruct_result457 = _t1195
        
        if deconstruct_result457 is not None:
            _t1197 = self.pretty_demand(deconstruct_result457)
            _t1196 = _t1197
        else:
            def _t1198(_dollar_dollar):
                
                if _dollar_dollar.HasField('output'):
                    _t1199 = _dollar_dollar.output
                else:
                    _t1199 = None
                return _t1199
            _t1200 = _t1198(msg)
            deconstruct_result456 = _t1200
            
            if deconstruct_result456 is not None:
                _t1202 = self.pretty_output(deconstruct_result456)
                _t1201 = _t1202
            else:
                def _t1203(_dollar_dollar):
                    
                    if _dollar_dollar.HasField('what_if'):
                        _t1204 = _dollar_dollar.what_if
                    else:
                        _t1204 = None
                    return _t1204
                _t1205 = _t1203(msg)
                deconstruct_result455 = _t1205
                
                if deconstruct_result455 is not None:
                    _t1207 = self.pretty_what_if(deconstruct_result455)
                    _t1206 = _t1207
                else:
                    def _t1208(_dollar_dollar):
                        
                        if _dollar_dollar.HasField('abort'):
                            _t1209 = _dollar_dollar.abort
                        else:
                            _t1209 = None
                        return _t1209
                    _t1210 = _t1208(msg)
                    deconstruct_result454 = _t1210
                    
                    if deconstruct_result454 is not None:
                        _t1212 = self.pretty_abort(deconstruct_result454)
                        _t1211 = _t1212
                    else:
                        def _t1213(_dollar_dollar):
                            
                            if _dollar_dollar.HasField('export'):
                                _t1214 = _dollar_dollar.export
                            else:
                                _t1214 = None
                            return _t1214
                        _t1215 = _t1213(msg)
                        deconstruct_result453 = _t1215
                        
                        if deconstruct_result453 is not None:
                            _t1217 = self.pretty_export(deconstruct_result453)
                            _t1216 = _t1217
                        else:
                            raise ParseError('No matching rule for read')
                        _t1211 = _t1216
                    _t1206 = _t1211
                _t1201 = _t1206
            _t1196 = _t1201

    def pretty_demand(self, msg: transactions_pb2.Demand):
        def _t1218(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1219 = _t1218(msg)
        fields458 = _t1219
        assert fields458 is not None
        unwrapped_fields459 = fields458
        self.write('(')
        self.write('demand')
        self.indent()
        self.newline()
        _t1220 = self.pretty_relation_id(unwrapped_fields459)
        self.dedent()
        self.write(')')

    def pretty_output(self, msg: transactions_pb2.Output):
        def _t1221(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        _t1222 = _t1221(msg)
        fields460 = _t1222
        assert fields460 is not None
        unwrapped_fields461 = fields460
        self.write('(')
        self.write('output')
        self.indent()
        self.newline()
        field462 = unwrapped_fields461[0]
        _t1223 = self.pretty_name(field462)
        self.newline()
        field463 = unwrapped_fields461[1]
        _t1224 = self.pretty_relation_id(field463)
        self.dedent()
        self.write(')')

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        def _t1225(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1226 = _t1225(msg)
        fields464 = _t1226
        assert fields464 is not None
        unwrapped_fields465 = fields464
        self.write('(')
        self.write('what_if')
        self.indent()
        self.newline()
        field466 = unwrapped_fields465[0]
        _t1227 = self.pretty_name(field466)
        self.newline()
        field467 = unwrapped_fields465[1]
        _t1228 = self.pretty_epoch(field467)
        self.dedent()
        self.write(')')

    def pretty_abort(self, msg: transactions_pb2.Abort):
        def _t1229(_dollar_dollar):
            
            if _dollar_dollar.name != 'abort':
                _t1230 = _dollar_dollar.name
            else:
                _t1230 = None
            return (_t1230, _dollar_dollar.relation_id,)
        _t1231 = _t1229(msg)
        fields468 = _t1231
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
            _t1233 = self.pretty_name(opt_val471)
            _t1232 = _t1233
        else:
            _t1232 = None
        self.newline()
        field472 = unwrapped_fields469[1]
        _t1234 = self.pretty_relation_id(field472)
        self.dedent()
        self.write(')')

    def pretty_export(self, msg: transactions_pb2.Export):
        def _t1235(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1236 = _t1235(msg)
        fields473 = _t1236
        assert fields473 is not None
        unwrapped_fields474 = fields473
        self.write('(')
        self.write('export')
        self.indent()
        self.newline()
        _t1237 = self.pretty_export_csv_config(unwrapped_fields474)
        self.dedent()
        self.write(')')

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        def _t1238(_dollar_dollar):
            _t1239 = self.deconstruct_export_csv_config(_dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1239,)
        _t1240 = _t1238(msg)
        fields475 = _t1240
        assert fields475 is not None
        unwrapped_fields476 = fields475
        self.write('(')
        self.write('export_csv_config')
        self.indent()
        self.newline()
        field477 = unwrapped_fields476[0]
        _t1241 = self.pretty_export_csv_path(field477)
        self.newline()
        field478 = unwrapped_fields476[1]
        _t1242 = self.pretty_export_csv_columns(field478)
        self.newline()
        field479 = unwrapped_fields476[2]
        _t1243 = self.pretty_config_dict(field479)
        self.dedent()
        self.write(')')

    def pretty_export_csv_path(self, msg: str):
        def _t1244(_dollar_dollar):
            return _dollar_dollar
        _t1245 = _t1244(msg)
        fields480 = _t1245
        assert fields480 is not None
        unwrapped_fields481 = fields480
        self.write('(')
        self.write('path')
        self.indent()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields481))
        self.dedent()
        self.write(')')

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        def _t1246(_dollar_dollar):
            return _dollar_dollar
        _t1247 = _t1246(msg)
        fields482 = _t1247
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
                _t1248 = self.pretty_export_csv_column(elem484)
        self.dedent()
        self.write(')')

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        def _t1249(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1250 = _t1249(msg)
        fields486 = _t1250
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
        _t1251 = self.pretty_relation_id(field489)
        self.dedent()
        self.write(')')


def pretty(msg: Any, io: Optional[IO[str]] = None) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
