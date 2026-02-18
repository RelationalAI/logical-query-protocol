"""
Auto-generated pretty printer.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the pretty printer, edit the generator code
in `meta/` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer python
"""

from io import StringIO
from collections.abc import Sequence
import sys

if sys.version_info >= (3, 11):
    from typing import Any, IO, Never, Optional
else:
    from typing import Any, IO, NoReturn as Never, Optional

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    pass


class PrettyPrinter:
    """Pretty printer for protobuf messages."""

    def __init__(self, io: Optional[IO[str]] = None, max_width: int = 92):
        self.io = io if io is not None else StringIO()
        self.indent_stack: list[int] = [0]
        self.column = 0
        self.at_line_start = True
        self.separator = '\n'
        self.max_width = max_width
        self._computing: set[int] = set()
        self._memo: dict[int, str] = {}
        self._memo_refs: list[Any] = []
        self._debug_info: dict[tuple[int, int], str] = {}

    @property
    def indent_level(self) -> int:
        """Current indentation column."""
        return self.indent_stack[-1] if self.indent_stack else 0

    def write(self, s: str) -> None:
        """Write a string to the output, with indentation at line start."""
        if self.separator == '\n' and self.at_line_start and s.strip():
            spaces = self.indent_level
            self.io.write(' ' * spaces)
            self.column = spaces
            self.at_line_start = False
        self.io.write(s)
        if '\n' in s:
            self.column = len(s) - s.rfind('\n') - 1
        else:
            self.column += len(s)

    def newline(self) -> None:
        """Write separator (newline or space depending on mode)."""
        self.io.write(self.separator)
        if self.separator == '\n':
            self.at_line_start = True
            self.column = 0

    def indent(self) -> None:
        """Push current column as new indentation level (no-op in flat mode)."""
        if self.separator == '\n':
            self.indent_stack.append(self.column)

    def indent_sexp(self) -> None:
        """Push parent indent + 2 for sexp body indentation (no-op in flat mode)."""
        if self.separator == '\n':
            self.indent_stack.append(self.indent_level + 2)

    def dedent(self) -> None:
        """Pop indentation level (no-op in flat mode)."""
        if self.separator == '\n':
            if len(self.indent_stack) > 1:
                self.indent_stack.pop()

    def _try_flat(self, msg: Any, pretty_fn: Any) -> Optional[str]:
        """Try to render msg flat (space-separated). Return flat string if it fits, else None."""
        msg_id = id(msg)
        if msg_id not in self._memo and msg_id not in self._computing:
            self._computing.add(msg_id)
            saved_io = self.io
            saved_sep = self.separator
            saved_indent = self.indent_stack
            saved_col = self.column
            saved_at_line_start = self.at_line_start
            try:
                self.io = StringIO()
                self.separator = ' '
                self.indent_stack = [0]
                self.column = 0
                self.at_line_start = False
                pretty_fn(msg)
                self._memo[msg_id] = self.io.getvalue()
                self._memo_refs.append(msg)
            finally:
                self.io = saved_io
                self.separator = saved_sep
                self.indent_stack = saved_indent
                self.column = saved_col
                self.at_line_start = saved_at_line_start
                self._computing.discard(msg_id)
        if msg_id in self._memo:
            flat = self._memo[msg_id]
            if self.separator != '\n':
                return flat
            effective_col = self.column if not self.at_line_start else self.indent_level
            if len(flat) + effective_col <= self.max_width:
                return flat
        return None

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

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1814 = logic_pb2.Value(int_value=int(v))
        return _t1814

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1815 = logic_pb2.Value(int_value=v)
        return _t1815

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1816 = logic_pb2.Value(float_value=v)
        return _t1816

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1817 = logic_pb2.Value(string_value=v)
        return _t1817

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1818 = logic_pb2.Value(boolean_value=v)
        return _t1818

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1819 = logic_pb2.Value(uint128_value=v)
        return _t1819

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1820 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1820,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1821 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1821,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1822 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1822,))
        _t1823 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1823,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1824 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1824,))
        _t1825 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1825,))
        if msg.new_line != "":
            _t1826 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1826,))
        _t1827 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1827,))
        _t1828 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1828,))
        _t1829 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1829,))
        if msg.comment != "":
            _t1830 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1830,))
        for missing_string in msg.missing_strings:
            _t1831 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1831,))
        _t1832 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1832,))
        _t1833 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1833,))
        _t1834 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1834,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1835 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1835,))
        _t1836 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1836,))
        _t1837 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1837,))
        _t1838 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1838,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1839 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1839,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1840 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1840,))
        _t1841 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1841,))
        _t1842 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1842,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1843 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1843,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1844 = self._make_value_string(msg.compression)
            result.append(("compression", _t1844,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1845 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1845,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1846 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1846,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1847 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1847,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1848 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1848,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1849 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1849,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != "":
            return name
        else:
            _t1850 = None
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == "":
            return self.relation_id_to_uint128(msg)
        else:
            _t1851 = None
        return None

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        return (abs.vars[0:n], [],)

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)

    # --- Pretty-print methods ---

    def pretty_transaction(self, msg: transactions_pb2.Transaction):
        flat683 = self._try_flat(msg, self.pretty_transaction)
        if flat683 is not None:
            assert flat683 is not None
            self.write(flat683)
            return None
        else:
            def _t1348(_dollar_dollar):
                if _dollar_dollar.HasField("configure"):
                    _t1349 = _dollar_dollar.configure
                else:
                    _t1349 = None
                if _dollar_dollar.HasField("sync"):
                    _t1350 = _dollar_dollar.sync
                else:
                    _t1350 = None
                return (_t1349, _t1350, _dollar_dollar.epochs,)
            _t1351 = _t1348(msg)
            fields674 = _t1351
            assert fields674 is not None
            unwrapped_fields675 = fields674
            self.write("(")
            self.write("transaction")
            self.indent_sexp()
            field676 = unwrapped_fields675[0]
            if field676 is not None:
                self.newline()
                assert field676 is not None
                opt_val677 = field676
                self.pretty_configure(opt_val677)
            field678 = unwrapped_fields675[1]
            if field678 is not None:
                self.newline()
                assert field678 is not None
                opt_val679 = field678
                self.pretty_sync(opt_val679)
            field680 = unwrapped_fields675[2]
            if not len(field680) == 0:
                self.newline()
                for i682, elem681 in enumerate(field680):
                    if (i682 > 0):
                        self.newline()
                    self.pretty_epoch(elem681)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat686 = self._try_flat(msg, self.pretty_configure)
        if flat686 is not None:
            assert flat686 is not None
            self.write(flat686)
            return None
        else:
            def _t1352(_dollar_dollar):
                _t1353 = self.deconstruct_configure(_dollar_dollar)
                return _t1353
            _t1354 = _t1352(msg)
            fields684 = _t1354
            assert fields684 is not None
            unwrapped_fields685 = fields684
            self.write("(")
            self.write("configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields685)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat691 = self._try_flat(msg, self.pretty_config_dict)
        if flat691 is not None:
            assert flat691 is not None
            self.write(flat691)
            return None
        else:
            def _t1355(_dollar_dollar):
                return _dollar_dollar
            _t1356 = _t1355(msg)
            fields687 = _t1356
            assert fields687 is not None
            unwrapped_fields688 = fields687
            self.write("{")
            self.indent()
            if not len(unwrapped_fields688) == 0:
                self.newline()
                for i690, elem689 in enumerate(unwrapped_fields688):
                    if (i690 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem689)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat696 = self._try_flat(msg, self.pretty_config_key_value)
        if flat696 is not None:
            assert flat696 is not None
            self.write(flat696)
            return None
        else:
            def _t1357(_dollar_dollar):
                return (_dollar_dollar[0], _dollar_dollar[1],)
            _t1358 = _t1357(msg)
            fields692 = _t1358
            assert fields692 is not None
            unwrapped_fields693 = fields692
            self.write(":")
            field694 = unwrapped_fields693[0]
            self.write(field694)
            self.write(" ")
            field695 = unwrapped_fields693[1]
            self.pretty_value(field695)

    def pretty_value(self, msg: logic_pb2.Value):
        flat717 = self._try_flat(msg, self.pretty_value)
        if flat717 is not None:
            assert flat717 is not None
            self.write(flat717)
            return None
        else:
            def _t1359(_dollar_dollar):
                if _dollar_dollar.HasField("date_value"):
                    _t1360 = _dollar_dollar.date_value
                else:
                    _t1360 = None
                return _t1360
            _t1361 = _t1359(msg)
            deconstruct_result715 = _t1361
            if deconstruct_result715 is not None:
                assert deconstruct_result715 is not None
                unwrapped716 = deconstruct_result715
                self.pretty_date(unwrapped716)
            else:
                def _t1362(_dollar_dollar):
                    if _dollar_dollar.HasField("datetime_value"):
                        _t1363 = _dollar_dollar.datetime_value
                    else:
                        _t1363 = None
                    return _t1363
                _t1364 = _t1362(msg)
                deconstruct_result713 = _t1364
                if deconstruct_result713 is not None:
                    assert deconstruct_result713 is not None
                    unwrapped714 = deconstruct_result713
                    self.pretty_datetime(unwrapped714)
                else:
                    def _t1365(_dollar_dollar):
                        if _dollar_dollar.HasField("string_value"):
                            _t1366 = _dollar_dollar.string_value
                        else:
                            _t1366 = None
                        return _t1366
                    _t1367 = _t1365(msg)
                    deconstruct_result711 = _t1367
                    if deconstruct_result711 is not None:
                        assert deconstruct_result711 is not None
                        unwrapped712 = deconstruct_result711
                        self.write(self.format_string_value(unwrapped712))
                    else:
                        def _t1368(_dollar_dollar):
                            if _dollar_dollar.HasField("int_value"):
                                _t1369 = _dollar_dollar.int_value
                            else:
                                _t1369 = None
                            return _t1369
                        _t1370 = _t1368(msg)
                        deconstruct_result709 = _t1370
                        if deconstruct_result709 is not None:
                            assert deconstruct_result709 is not None
                            unwrapped710 = deconstruct_result709
                            self.write(str(unwrapped710))
                        else:
                            def _t1371(_dollar_dollar):
                                if _dollar_dollar.HasField("float_value"):
                                    _t1372 = _dollar_dollar.float_value
                                else:
                                    _t1372 = None
                                return _t1372
                            _t1373 = _t1371(msg)
                            deconstruct_result707 = _t1373
                            if deconstruct_result707 is not None:
                                assert deconstruct_result707 is not None
                                unwrapped708 = deconstruct_result707
                                self.write(str(unwrapped708))
                            else:
                                def _t1374(_dollar_dollar):
                                    if _dollar_dollar.HasField("uint128_value"):
                                        _t1375 = _dollar_dollar.uint128_value
                                    else:
                                        _t1375 = None
                                    return _t1375
                                _t1376 = _t1374(msg)
                                deconstruct_result705 = _t1376
                                if deconstruct_result705 is not None:
                                    assert deconstruct_result705 is not None
                                    unwrapped706 = deconstruct_result705
                                    self.write(self.format_uint128(unwrapped706))
                                else:
                                    def _t1377(_dollar_dollar):
                                        if _dollar_dollar.HasField("int128_value"):
                                            _t1378 = _dollar_dollar.int128_value
                                        else:
                                            _t1378 = None
                                        return _t1378
                                    _t1379 = _t1377(msg)
                                    deconstruct_result703 = _t1379
                                    if deconstruct_result703 is not None:
                                        assert deconstruct_result703 is not None
                                        unwrapped704 = deconstruct_result703
                                        self.write(self.format_int128(unwrapped704))
                                    else:
                                        def _t1380(_dollar_dollar):
                                            if _dollar_dollar.HasField("decimal_value"):
                                                _t1381 = _dollar_dollar.decimal_value
                                            else:
                                                _t1381 = None
                                            return _t1381
                                        _t1382 = _t1380(msg)
                                        deconstruct_result701 = _t1382
                                        if deconstruct_result701 is not None:
                                            assert deconstruct_result701 is not None
                                            unwrapped702 = deconstruct_result701
                                            self.write(self.format_decimal(unwrapped702))
                                        else:
                                            def _t1383(_dollar_dollar):
                                                if _dollar_dollar.HasField("boolean_value"):
                                                    _t1384 = _dollar_dollar.boolean_value
                                                else:
                                                    _t1384 = None
                                                return _t1384
                                            _t1385 = _t1383(msg)
                                            deconstruct_result699 = _t1385
                                            if deconstruct_result699 is not None:
                                                assert deconstruct_result699 is not None
                                                unwrapped700 = deconstruct_result699
                                                self.pretty_boolean_value(unwrapped700)
                                            else:
                                                def _t1386(_dollar_dollar):
                                                    return _dollar_dollar
                                                _t1387 = _t1386(msg)
                                                fields697 = _t1387
                                                assert fields697 is not None
                                                unwrapped_fields698 = fields697
                                                self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat723 = self._try_flat(msg, self.pretty_date)
        if flat723 is not None:
            assert flat723 is not None
            self.write(flat723)
            return None
        else:
            def _t1388(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            _t1389 = _t1388(msg)
            fields718 = _t1389
            assert fields718 is not None
            unwrapped_fields719 = fields718
            self.write("(")
            self.write("date")
            self.indent_sexp()
            self.newline()
            field720 = unwrapped_fields719[0]
            self.write(str(field720))
            self.newline()
            field721 = unwrapped_fields719[1]
            self.write(str(field721))
            self.newline()
            field722 = unwrapped_fields719[2]
            self.write(str(field722))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat734 = self._try_flat(msg, self.pretty_datetime)
        if flat734 is not None:
            assert flat734 is not None
            self.write(flat734)
            return None
        else:
            def _t1390(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            _t1391 = _t1390(msg)
            fields724 = _t1391
            assert fields724 is not None
            unwrapped_fields725 = fields724
            self.write("(")
            self.write("datetime")
            self.indent_sexp()
            self.newline()
            field726 = unwrapped_fields725[0]
            self.write(str(field726))
            self.newline()
            field727 = unwrapped_fields725[1]
            self.write(str(field727))
            self.newline()
            field728 = unwrapped_fields725[2]
            self.write(str(field728))
            self.newline()
            field729 = unwrapped_fields725[3]
            self.write(str(field729))
            self.newline()
            field730 = unwrapped_fields725[4]
            self.write(str(field730))
            self.newline()
            field731 = unwrapped_fields725[5]
            self.write(str(field731))
            field732 = unwrapped_fields725[6]
            if field732 is not None:
                self.newline()
                assert field732 is not None
                opt_val733 = field732
                self.write(str(opt_val733))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        flat739 = self._try_flat(msg, self.pretty_boolean_value)
        if flat739 is not None:
            assert flat739 is not None
            self.write(flat739)
            return None
        else:
            def _t1392(_dollar_dollar):
                if _dollar_dollar:
                    _t1393 = ()
                else:
                    _t1393 = None
                return _t1393
            _t1394 = _t1392(msg)
            deconstruct_result737 = _t1394
            if deconstruct_result737 is not None:
                assert deconstruct_result737 is not None
                unwrapped738 = deconstruct_result737
                self.write("true")
            else:
                def _t1395(_dollar_dollar):
                    if not _dollar_dollar:
                        _t1396 = ()
                    else:
                        _t1396 = None
                    return _t1396
                _t1397 = _t1395(msg)
                deconstruct_result735 = _t1397
                if deconstruct_result735 is not None:
                    assert deconstruct_result735 is not None
                    unwrapped736 = deconstruct_result735
                    self.write("false")
                else:
                    raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat744 = self._try_flat(msg, self.pretty_sync)
        if flat744 is not None:
            assert flat744 is not None
            self.write(flat744)
            return None
        else:
            def _t1398(_dollar_dollar):
                return _dollar_dollar.fragments
            _t1399 = _t1398(msg)
            fields740 = _t1399
            assert fields740 is not None
            unwrapped_fields741 = fields740
            self.write("(")
            self.write("sync")
            self.indent_sexp()
            if not len(unwrapped_fields741) == 0:
                self.newline()
                for i743, elem742 in enumerate(unwrapped_fields741):
                    if (i743 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem742)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat747 = self._try_flat(msg, self.pretty_fragment_id)
        if flat747 is not None:
            assert flat747 is not None
            self.write(flat747)
            return None
        else:
            def _t1400(_dollar_dollar):
                return self.fragment_id_to_string(_dollar_dollar)
            _t1401 = _t1400(msg)
            fields745 = _t1401
            assert fields745 is not None
            unwrapped_fields746 = fields745
            self.write(":")
            self.write(unwrapped_fields746)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat754 = self._try_flat(msg, self.pretty_epoch)
        if flat754 is not None:
            assert flat754 is not None
            self.write(flat754)
            return None
        else:
            def _t1402(_dollar_dollar):
                if not len(_dollar_dollar.writes) == 0:
                    _t1403 = _dollar_dollar.writes
                else:
                    _t1403 = None
                if not len(_dollar_dollar.reads) == 0:
                    _t1404 = _dollar_dollar.reads
                else:
                    _t1404 = None
                return (_t1403, _t1404,)
            _t1405 = _t1402(msg)
            fields748 = _t1405
            assert fields748 is not None
            unwrapped_fields749 = fields748
            self.write("(")
            self.write("epoch")
            self.indent_sexp()
            field750 = unwrapped_fields749[0]
            if field750 is not None:
                self.newline()
                assert field750 is not None
                opt_val751 = field750
                self.pretty_epoch_writes(opt_val751)
            field752 = unwrapped_fields749[1]
            if field752 is not None:
                self.newline()
                assert field752 is not None
                opt_val753 = field752
                self.pretty_epoch_reads(opt_val753)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat759 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat759 is not None:
            assert flat759 is not None
            self.write(flat759)
            return None
        else:
            def _t1406(_dollar_dollar):
                return _dollar_dollar
            _t1407 = _t1406(msg)
            fields755 = _t1407
            assert fields755 is not None
            unwrapped_fields756 = fields755
            self.write("(")
            self.write("writes")
            self.indent_sexp()
            if not len(unwrapped_fields756) == 0:
                self.newline()
                for i758, elem757 in enumerate(unwrapped_fields756):
                    if (i758 > 0):
                        self.newline()
                    self.pretty_write(elem757)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat766 = self._try_flat(msg, self.pretty_write)
        if flat766 is not None:
            assert flat766 is not None
            self.write(flat766)
            return None
        else:
            def _t1408(_dollar_dollar):
                if _dollar_dollar.HasField("define"):
                    _t1409 = _dollar_dollar.define
                else:
                    _t1409 = None
                return _t1409
            _t1410 = _t1408(msg)
            deconstruct_result764 = _t1410
            if deconstruct_result764 is not None:
                assert deconstruct_result764 is not None
                unwrapped765 = deconstruct_result764
                self.pretty_define(unwrapped765)
            else:
                def _t1411(_dollar_dollar):
                    if _dollar_dollar.HasField("undefine"):
                        _t1412 = _dollar_dollar.undefine
                    else:
                        _t1412 = None
                    return _t1412
                _t1413 = _t1411(msg)
                deconstruct_result762 = _t1413
                if deconstruct_result762 is not None:
                    assert deconstruct_result762 is not None
                    unwrapped763 = deconstruct_result762
                    self.pretty_undefine(unwrapped763)
                else:
                    def _t1414(_dollar_dollar):
                        if _dollar_dollar.HasField("context"):
                            _t1415 = _dollar_dollar.context
                        else:
                            _t1415 = None
                        return _t1415
                    _t1416 = _t1414(msg)
                    deconstruct_result760 = _t1416
                    if deconstruct_result760 is not None:
                        assert deconstruct_result760 is not None
                        unwrapped761 = deconstruct_result760
                        self.pretty_context(unwrapped761)
                    else:
                        raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat769 = self._try_flat(msg, self.pretty_define)
        if flat769 is not None:
            assert flat769 is not None
            self.write(flat769)
            return None
        else:
            def _t1417(_dollar_dollar):
                return _dollar_dollar.fragment
            _t1418 = _t1417(msg)
            fields767 = _t1418
            assert fields767 is not None
            unwrapped_fields768 = fields767
            self.write("(")
            self.write("define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields768)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat776 = self._try_flat(msg, self.pretty_fragment)
        if flat776 is not None:
            assert flat776 is not None
            self.write(flat776)
            return None
        else:
            def _t1419(_dollar_dollar):
                self.start_pretty_fragment(_dollar_dollar)
                return (_dollar_dollar.id, _dollar_dollar.declarations,)
            _t1420 = _t1419(msg)
            fields770 = _t1420
            assert fields770 is not None
            unwrapped_fields771 = fields770
            self.write("(")
            self.write("fragment")
            self.indent_sexp()
            self.newline()
            field772 = unwrapped_fields771[0]
            self.pretty_new_fragment_id(field772)
            field773 = unwrapped_fields771[1]
            if not len(field773) == 0:
                self.newline()
                for i775, elem774 in enumerate(field773):
                    if (i775 > 0):
                        self.newline()
                    self.pretty_declaration(elem774)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat779 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat779 is not None:
            assert flat779 is not None
            self.write(flat779)
            return None
        else:
            def _t1421(_dollar_dollar):
                return _dollar_dollar
            _t1422 = _t1421(msg)
            fields777 = _t1422
            assert fields777 is not None
            unwrapped_fields778 = fields777
            self.pretty_fragment_id(unwrapped_fields778)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat788 = self._try_flat(msg, self.pretty_declaration)
        if flat788 is not None:
            assert flat788 is not None
            self.write(flat788)
            return None
        else:
            def _t1423(_dollar_dollar):
                if _dollar_dollar.HasField("def"):
                    _t1424 = getattr(_dollar_dollar, 'def')
                else:
                    _t1424 = None
                return _t1424
            _t1425 = _t1423(msg)
            deconstruct_result786 = _t1425
            if deconstruct_result786 is not None:
                assert deconstruct_result786 is not None
                unwrapped787 = deconstruct_result786
                self.pretty_def(unwrapped787)
            else:
                def _t1426(_dollar_dollar):
                    if _dollar_dollar.HasField("algorithm"):
                        _t1427 = _dollar_dollar.algorithm
                    else:
                        _t1427 = None
                    return _t1427
                _t1428 = _t1426(msg)
                deconstruct_result784 = _t1428
                if deconstruct_result784 is not None:
                    assert deconstruct_result784 is not None
                    unwrapped785 = deconstruct_result784
                    self.pretty_algorithm(unwrapped785)
                else:
                    def _t1429(_dollar_dollar):
                        if _dollar_dollar.HasField("constraint"):
                            _t1430 = _dollar_dollar.constraint
                        else:
                            _t1430 = None
                        return _t1430
                    _t1431 = _t1429(msg)
                    deconstruct_result782 = _t1431
                    if deconstruct_result782 is not None:
                        assert deconstruct_result782 is not None
                        unwrapped783 = deconstruct_result782
                        self.pretty_constraint(unwrapped783)
                    else:
                        def _t1432(_dollar_dollar):
                            if _dollar_dollar.HasField("data"):
                                _t1433 = _dollar_dollar.data
                            else:
                                _t1433 = None
                            return _t1433
                        _t1434 = _t1432(msg)
                        deconstruct_result780 = _t1434
                        if deconstruct_result780 is not None:
                            assert deconstruct_result780 is not None
                            unwrapped781 = deconstruct_result780
                            self.pretty_data(unwrapped781)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat795 = self._try_flat(msg, self.pretty_def)
        if flat795 is not None:
            assert flat795 is not None
            self.write(flat795)
            return None
        else:
            def _t1435(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1436 = _dollar_dollar.attrs
                else:
                    _t1436 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1436,)
            _t1437 = _t1435(msg)
            fields789 = _t1437
            assert fields789 is not None
            unwrapped_fields790 = fields789
            self.write("(")
            self.write("def")
            self.indent_sexp()
            self.newline()
            field791 = unwrapped_fields790[0]
            self.pretty_relation_id(field791)
            self.newline()
            field792 = unwrapped_fields790[1]
            self.pretty_abstraction(field792)
            field793 = unwrapped_fields790[2]
            if field793 is not None:
                self.newline()
                assert field793 is not None
                opt_val794 = field793
                self.pretty_attrs(opt_val794)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat800 = self._try_flat(msg, self.pretty_relation_id)
        if flat800 is not None:
            assert flat800 is not None
            self.write(flat800)
            return None
        else:
            def _t1438(_dollar_dollar):
                _t1439 = self.deconstruct_relation_id_string(_dollar_dollar)
                return _t1439
            _t1440 = _t1438(msg)
            deconstruct_result798 = _t1440
            if deconstruct_result798 is not None:
                assert deconstruct_result798 is not None
                unwrapped799 = deconstruct_result798
                self.write(":")
                self.write(unwrapped799)
            else:
                def _t1441(_dollar_dollar):
                    _t1442 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                    return _t1442
                _t1443 = _t1441(msg)
                deconstruct_result796 = _t1443
                if deconstruct_result796 is not None:
                    assert deconstruct_result796 is not None
                    unwrapped797 = deconstruct_result796
                    self.write(self.format_uint128(unwrapped797))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat805 = self._try_flat(msg, self.pretty_abstraction)
        if flat805 is not None:
            assert flat805 is not None
            self.write(flat805)
            return None
        else:
            def _t1444(_dollar_dollar):
                _t1445 = self.deconstruct_bindings(_dollar_dollar)
                return (_t1445, _dollar_dollar.value,)
            _t1446 = _t1444(msg)
            fields801 = _t1446
            assert fields801 is not None
            unwrapped_fields802 = fields801
            self.write("(")
            self.indent()
            field803 = unwrapped_fields802[0]
            self.pretty_bindings(field803)
            self.newline()
            field804 = unwrapped_fields802[1]
            self.pretty_formula(field804)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat813 = self._try_flat(msg, self.pretty_bindings)
        if flat813 is not None:
            assert flat813 is not None
            self.write(flat813)
            return None
        else:
            def _t1447(_dollar_dollar):
                if not len(_dollar_dollar[1]) == 0:
                    _t1448 = _dollar_dollar[1]
                else:
                    _t1448 = None
                return (_dollar_dollar[0], _t1448,)
            _t1449 = _t1447(msg)
            fields806 = _t1449
            assert fields806 is not None
            unwrapped_fields807 = fields806
            self.write("[")
            self.indent()
            field808 = unwrapped_fields807[0]
            for i810, elem809 in enumerate(field808):
                if (i810 > 0):
                    self.newline()
                self.pretty_binding(elem809)
            field811 = unwrapped_fields807[1]
            if field811 is not None:
                self.newline()
                assert field811 is not None
                opt_val812 = field811
                self.pretty_value_bindings(opt_val812)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat818 = self._try_flat(msg, self.pretty_binding)
        if flat818 is not None:
            assert flat818 is not None
            self.write(flat818)
            return None
        else:
            def _t1450(_dollar_dollar):
                return (_dollar_dollar.var.name, _dollar_dollar.type,)
            _t1451 = _t1450(msg)
            fields814 = _t1451
            assert fields814 is not None
            unwrapped_fields815 = fields814
            field816 = unwrapped_fields815[0]
            self.write(field816)
            self.write("::")
            field817 = unwrapped_fields815[1]
            self.pretty_type(field817)

    def pretty_type(self, msg: logic_pb2.Type):
        flat841 = self._try_flat(msg, self.pretty_type)
        if flat841 is not None:
            assert flat841 is not None
            self.write(flat841)
            return None
        else:
            def _t1452(_dollar_dollar):
                if _dollar_dollar.HasField("unspecified_type"):
                    _t1453 = _dollar_dollar.unspecified_type
                else:
                    _t1453 = None
                return _t1453
            _t1454 = _t1452(msg)
            deconstruct_result839 = _t1454
            if deconstruct_result839 is not None:
                assert deconstruct_result839 is not None
                unwrapped840 = deconstruct_result839
                self.pretty_unspecified_type(unwrapped840)
            else:
                def _t1455(_dollar_dollar):
                    if _dollar_dollar.HasField("string_type"):
                        _t1456 = _dollar_dollar.string_type
                    else:
                        _t1456 = None
                    return _t1456
                _t1457 = _t1455(msg)
                deconstruct_result837 = _t1457
                if deconstruct_result837 is not None:
                    assert deconstruct_result837 is not None
                    unwrapped838 = deconstruct_result837
                    self.pretty_string_type(unwrapped838)
                else:
                    def _t1458(_dollar_dollar):
                        if _dollar_dollar.HasField("int_type"):
                            _t1459 = _dollar_dollar.int_type
                        else:
                            _t1459 = None
                        return _t1459
                    _t1460 = _t1458(msg)
                    deconstruct_result835 = _t1460
                    if deconstruct_result835 is not None:
                        assert deconstruct_result835 is not None
                        unwrapped836 = deconstruct_result835
                        self.pretty_int_type(unwrapped836)
                    else:
                        def _t1461(_dollar_dollar):
                            if _dollar_dollar.HasField("float_type"):
                                _t1462 = _dollar_dollar.float_type
                            else:
                                _t1462 = None
                            return _t1462
                        _t1463 = _t1461(msg)
                        deconstruct_result833 = _t1463
                        if deconstruct_result833 is not None:
                            assert deconstruct_result833 is not None
                            unwrapped834 = deconstruct_result833
                            self.pretty_float_type(unwrapped834)
                        else:
                            def _t1464(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_type"):
                                    _t1465 = _dollar_dollar.uint128_type
                                else:
                                    _t1465 = None
                                return _t1465
                            _t1466 = _t1464(msg)
                            deconstruct_result831 = _t1466
                            if deconstruct_result831 is not None:
                                assert deconstruct_result831 is not None
                                unwrapped832 = deconstruct_result831
                                self.pretty_uint128_type(unwrapped832)
                            else:
                                def _t1467(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_type"):
                                        _t1468 = _dollar_dollar.int128_type
                                    else:
                                        _t1468 = None
                                    return _t1468
                                _t1469 = _t1467(msg)
                                deconstruct_result829 = _t1469
                                if deconstruct_result829 is not None:
                                    assert deconstruct_result829 is not None
                                    unwrapped830 = deconstruct_result829
                                    self.pretty_int128_type(unwrapped830)
                                else:
                                    def _t1470(_dollar_dollar):
                                        if _dollar_dollar.HasField("date_type"):
                                            _t1471 = _dollar_dollar.date_type
                                        else:
                                            _t1471 = None
                                        return _t1471
                                    _t1472 = _t1470(msg)
                                    deconstruct_result827 = _t1472
                                    if deconstruct_result827 is not None:
                                        assert deconstruct_result827 is not None
                                        unwrapped828 = deconstruct_result827
                                        self.pretty_date_type(unwrapped828)
                                    else:
                                        def _t1473(_dollar_dollar):
                                            if _dollar_dollar.HasField("datetime_type"):
                                                _t1474 = _dollar_dollar.datetime_type
                                            else:
                                                _t1474 = None
                                            return _t1474
                                        _t1475 = _t1473(msg)
                                        deconstruct_result825 = _t1475
                                        if deconstruct_result825 is not None:
                                            assert deconstruct_result825 is not None
                                            unwrapped826 = deconstruct_result825
                                            self.pretty_datetime_type(unwrapped826)
                                        else:
                                            def _t1476(_dollar_dollar):
                                                if _dollar_dollar.HasField("missing_type"):
                                                    _t1477 = _dollar_dollar.missing_type
                                                else:
                                                    _t1477 = None
                                                return _t1477
                                            _t1478 = _t1476(msg)
                                            deconstruct_result823 = _t1478
                                            if deconstruct_result823 is not None:
                                                assert deconstruct_result823 is not None
                                                unwrapped824 = deconstruct_result823
                                                self.pretty_missing_type(unwrapped824)
                                            else:
                                                def _t1479(_dollar_dollar):
                                                    if _dollar_dollar.HasField("decimal_type"):
                                                        _t1480 = _dollar_dollar.decimal_type
                                                    else:
                                                        _t1480 = None
                                                    return _t1480
                                                _t1481 = _t1479(msg)
                                                deconstruct_result821 = _t1481
                                                if deconstruct_result821 is not None:
                                                    assert deconstruct_result821 is not None
                                                    unwrapped822 = deconstruct_result821
                                                    self.pretty_decimal_type(unwrapped822)
                                                else:
                                                    def _t1482(_dollar_dollar):
                                                        if _dollar_dollar.HasField("boolean_type"):
                                                            _t1483 = _dollar_dollar.boolean_type
                                                        else:
                                                            _t1483 = None
                                                        return _t1483
                                                    _t1484 = _t1482(msg)
                                                    deconstruct_result819 = _t1484
                                                    if deconstruct_result819 is not None:
                                                        assert deconstruct_result819 is not None
                                                        unwrapped820 = deconstruct_result819
                                                        self.pretty_boolean_type(unwrapped820)
                                                    else:
                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        flat844 = self._try_flat(msg, self.pretty_unspecified_type)
        if flat844 is not None:
            assert flat844 is not None
            self.write(flat844)
            return None
        else:
            def _t1485(_dollar_dollar):
                return _dollar_dollar
            _t1486 = _t1485(msg)
            fields842 = _t1486
            assert fields842 is not None
            unwrapped_fields843 = fields842
            self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        flat847 = self._try_flat(msg, self.pretty_string_type)
        if flat847 is not None:
            assert flat847 is not None
            self.write(flat847)
            return None
        else:
            def _t1487(_dollar_dollar):
                return _dollar_dollar
            _t1488 = _t1487(msg)
            fields845 = _t1488
            assert fields845 is not None
            unwrapped_fields846 = fields845
            self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        flat850 = self._try_flat(msg, self.pretty_int_type)
        if flat850 is not None:
            assert flat850 is not None
            self.write(flat850)
            return None
        else:
            def _t1489(_dollar_dollar):
                return _dollar_dollar
            _t1490 = _t1489(msg)
            fields848 = _t1490
            assert fields848 is not None
            unwrapped_fields849 = fields848
            self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        flat853 = self._try_flat(msg, self.pretty_float_type)
        if flat853 is not None:
            assert flat853 is not None
            self.write(flat853)
            return None
        else:
            def _t1491(_dollar_dollar):
                return _dollar_dollar
            _t1492 = _t1491(msg)
            fields851 = _t1492
            assert fields851 is not None
            unwrapped_fields852 = fields851
            self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        flat856 = self._try_flat(msg, self.pretty_uint128_type)
        if flat856 is not None:
            assert flat856 is not None
            self.write(flat856)
            return None
        else:
            def _t1493(_dollar_dollar):
                return _dollar_dollar
            _t1494 = _t1493(msg)
            fields854 = _t1494
            assert fields854 is not None
            unwrapped_fields855 = fields854
            self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        flat859 = self._try_flat(msg, self.pretty_int128_type)
        if flat859 is not None:
            assert flat859 is not None
            self.write(flat859)
            return None
        else:
            def _t1495(_dollar_dollar):
                return _dollar_dollar
            _t1496 = _t1495(msg)
            fields857 = _t1496
            assert fields857 is not None
            unwrapped_fields858 = fields857
            self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        flat862 = self._try_flat(msg, self.pretty_date_type)
        if flat862 is not None:
            assert flat862 is not None
            self.write(flat862)
            return None
        else:
            def _t1497(_dollar_dollar):
                return _dollar_dollar
            _t1498 = _t1497(msg)
            fields860 = _t1498
            assert fields860 is not None
            unwrapped_fields861 = fields860
            self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        flat865 = self._try_flat(msg, self.pretty_datetime_type)
        if flat865 is not None:
            assert flat865 is not None
            self.write(flat865)
            return None
        else:
            def _t1499(_dollar_dollar):
                return _dollar_dollar
            _t1500 = _t1499(msg)
            fields863 = _t1500
            assert fields863 is not None
            unwrapped_fields864 = fields863
            self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        flat868 = self._try_flat(msg, self.pretty_missing_type)
        if flat868 is not None:
            assert flat868 is not None
            self.write(flat868)
            return None
        else:
            def _t1501(_dollar_dollar):
                return _dollar_dollar
            _t1502 = _t1501(msg)
            fields866 = _t1502
            assert fields866 is not None
            unwrapped_fields867 = fields866
            self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat873 = self._try_flat(msg, self.pretty_decimal_type)
        if flat873 is not None:
            assert flat873 is not None
            self.write(flat873)
            return None
        else:
            def _t1503(_dollar_dollar):
                return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            _t1504 = _t1503(msg)
            fields869 = _t1504
            assert fields869 is not None
            unwrapped_fields870 = fields869
            self.write("(")
            self.write("DECIMAL")
            self.indent_sexp()
            self.newline()
            field871 = unwrapped_fields870[0]
            self.write(str(field871))
            self.newline()
            field872 = unwrapped_fields870[1]
            self.write(str(field872))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        flat876 = self._try_flat(msg, self.pretty_boolean_type)
        if flat876 is not None:
            assert flat876 is not None
            self.write(flat876)
            return None
        else:
            def _t1505(_dollar_dollar):
                return _dollar_dollar
            _t1506 = _t1505(msg)
            fields874 = _t1506
            assert fields874 is not None
            unwrapped_fields875 = fields874
            self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat881 = self._try_flat(msg, self.pretty_value_bindings)
        if flat881 is not None:
            assert flat881 is not None
            self.write(flat881)
            return None
        else:
            def _t1507(_dollar_dollar):
                return _dollar_dollar
            _t1508 = _t1507(msg)
            fields877 = _t1508
            assert fields877 is not None
            unwrapped_fields878 = fields877
            self.write("|")
            if not len(unwrapped_fields878) == 0:
                self.write(" ")
                for i880, elem879 in enumerate(unwrapped_fields878):
                    if (i880 > 0):
                        self.newline()
                    self.pretty_binding(elem879)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat908 = self._try_flat(msg, self.pretty_formula)
        if flat908 is not None:
            assert flat908 is not None
            self.write(flat908)
            return None
        else:
            def _t1509(_dollar_dollar):
                if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                    _t1510 = _dollar_dollar.conjunction
                else:
                    _t1510 = None
                return _t1510
            _t1511 = _t1509(msg)
            deconstruct_result906 = _t1511
            if deconstruct_result906 is not None:
                assert deconstruct_result906 is not None
                unwrapped907 = deconstruct_result906
                self.pretty_true(unwrapped907)
            else:
                def _t1512(_dollar_dollar):
                    if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                        _t1513 = _dollar_dollar.disjunction
                    else:
                        _t1513 = None
                    return _t1513
                _t1514 = _t1512(msg)
                deconstruct_result904 = _t1514
                if deconstruct_result904 is not None:
                    assert deconstruct_result904 is not None
                    unwrapped905 = deconstruct_result904
                    self.pretty_false(unwrapped905)
                else:
                    def _t1515(_dollar_dollar):
                        if _dollar_dollar.HasField("exists"):
                            _t1516 = _dollar_dollar.exists
                        else:
                            _t1516 = None
                        return _t1516
                    _t1517 = _t1515(msg)
                    deconstruct_result902 = _t1517
                    if deconstruct_result902 is not None:
                        assert deconstruct_result902 is not None
                        unwrapped903 = deconstruct_result902
                        self.pretty_exists(unwrapped903)
                    else:
                        def _t1518(_dollar_dollar):
                            if _dollar_dollar.HasField("reduce"):
                                _t1519 = _dollar_dollar.reduce
                            else:
                                _t1519 = None
                            return _t1519
                        _t1520 = _t1518(msg)
                        deconstruct_result900 = _t1520
                        if deconstruct_result900 is not None:
                            assert deconstruct_result900 is not None
                            unwrapped901 = deconstruct_result900
                            self.pretty_reduce(unwrapped901)
                        else:
                            def _t1521(_dollar_dollar):
                                if _dollar_dollar.HasField("conjunction"):
                                    _t1522 = _dollar_dollar.conjunction
                                else:
                                    _t1522 = None
                                return _t1522
                            _t1523 = _t1521(msg)
                            deconstruct_result898 = _t1523
                            if deconstruct_result898 is not None:
                                assert deconstruct_result898 is not None
                                unwrapped899 = deconstruct_result898
                                self.pretty_conjunction(unwrapped899)
                            else:
                                def _t1524(_dollar_dollar):
                                    if _dollar_dollar.HasField("disjunction"):
                                        _t1525 = _dollar_dollar.disjunction
                                    else:
                                        _t1525 = None
                                    return _t1525
                                _t1526 = _t1524(msg)
                                deconstruct_result896 = _t1526
                                if deconstruct_result896 is not None:
                                    assert deconstruct_result896 is not None
                                    unwrapped897 = deconstruct_result896
                                    self.pretty_disjunction(unwrapped897)
                                else:
                                    def _t1527(_dollar_dollar):
                                        if _dollar_dollar.HasField("not"):
                                            _t1528 = getattr(_dollar_dollar, 'not')
                                        else:
                                            _t1528 = None
                                        return _t1528
                                    _t1529 = _t1527(msg)
                                    deconstruct_result894 = _t1529
                                    if deconstruct_result894 is not None:
                                        assert deconstruct_result894 is not None
                                        unwrapped895 = deconstruct_result894
                                        self.pretty_not(unwrapped895)
                                    else:
                                        def _t1530(_dollar_dollar):
                                            if _dollar_dollar.HasField("ffi"):
                                                _t1531 = _dollar_dollar.ffi
                                            else:
                                                _t1531 = None
                                            return _t1531
                                        _t1532 = _t1530(msg)
                                        deconstruct_result892 = _t1532
                                        if deconstruct_result892 is not None:
                                            assert deconstruct_result892 is not None
                                            unwrapped893 = deconstruct_result892
                                            self.pretty_ffi(unwrapped893)
                                        else:
                                            def _t1533(_dollar_dollar):
                                                if _dollar_dollar.HasField("atom"):
                                                    _t1534 = _dollar_dollar.atom
                                                else:
                                                    _t1534 = None
                                                return _t1534
                                            _t1535 = _t1533(msg)
                                            deconstruct_result890 = _t1535
                                            if deconstruct_result890 is not None:
                                                assert deconstruct_result890 is not None
                                                unwrapped891 = deconstruct_result890
                                                self.pretty_atom(unwrapped891)
                                            else:
                                                def _t1536(_dollar_dollar):
                                                    if _dollar_dollar.HasField("pragma"):
                                                        _t1537 = _dollar_dollar.pragma
                                                    else:
                                                        _t1537 = None
                                                    return _t1537
                                                _t1538 = _t1536(msg)
                                                deconstruct_result888 = _t1538
                                                if deconstruct_result888 is not None:
                                                    assert deconstruct_result888 is not None
                                                    unwrapped889 = deconstruct_result888
                                                    self.pretty_pragma(unwrapped889)
                                                else:
                                                    def _t1539(_dollar_dollar):
                                                        if _dollar_dollar.HasField("primitive"):
                                                            _t1540 = _dollar_dollar.primitive
                                                        else:
                                                            _t1540 = None
                                                        return _t1540
                                                    _t1541 = _t1539(msg)
                                                    deconstruct_result886 = _t1541
                                                    if deconstruct_result886 is not None:
                                                        assert deconstruct_result886 is not None
                                                        unwrapped887 = deconstruct_result886
                                                        self.pretty_primitive(unwrapped887)
                                                    else:
                                                        def _t1542(_dollar_dollar):
                                                            if _dollar_dollar.HasField("rel_atom"):
                                                                _t1543 = _dollar_dollar.rel_atom
                                                            else:
                                                                _t1543 = None
                                                            return _t1543
                                                        _t1544 = _t1542(msg)
                                                        deconstruct_result884 = _t1544
                                                        if deconstruct_result884 is not None:
                                                            assert deconstruct_result884 is not None
                                                            unwrapped885 = deconstruct_result884
                                                            self.pretty_rel_atom(unwrapped885)
                                                        else:
                                                            def _t1545(_dollar_dollar):
                                                                if _dollar_dollar.HasField("cast"):
                                                                    _t1546 = _dollar_dollar.cast
                                                                else:
                                                                    _t1546 = None
                                                                return _t1546
                                                            _t1547 = _t1545(msg)
                                                            deconstruct_result882 = _t1547
                                                            if deconstruct_result882 is not None:
                                                                assert deconstruct_result882 is not None
                                                                unwrapped883 = deconstruct_result882
                                                                self.pretty_cast(unwrapped883)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        flat911 = self._try_flat(msg, self.pretty_true)
        if flat911 is not None:
            assert flat911 is not None
            self.write(flat911)
            return None
        else:
            def _t1548(_dollar_dollar):
                return _dollar_dollar
            _t1549 = _t1548(msg)
            fields909 = _t1549
            assert fields909 is not None
            unwrapped_fields910 = fields909
            self.write("(")
            self.write("true")
            self.write(")")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        flat914 = self._try_flat(msg, self.pretty_false)
        if flat914 is not None:
            assert flat914 is not None
            self.write(flat914)
            return None
        else:
            def _t1550(_dollar_dollar):
                return _dollar_dollar
            _t1551 = _t1550(msg)
            fields912 = _t1551
            assert fields912 is not None
            unwrapped_fields913 = fields912
            self.write("(")
            self.write("false")
            self.write(")")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat919 = self._try_flat(msg, self.pretty_exists)
        if flat919 is not None:
            assert flat919 is not None
            self.write(flat919)
            return None
        else:
            def _t1552(_dollar_dollar):
                _t1553 = self.deconstruct_bindings(_dollar_dollar.body)
                return (_t1553, _dollar_dollar.body.value,)
            _t1554 = _t1552(msg)
            fields915 = _t1554
            assert fields915 is not None
            unwrapped_fields916 = fields915
            self.write("(")
            self.write("exists")
            self.indent_sexp()
            self.newline()
            field917 = unwrapped_fields916[0]
            self.pretty_bindings(field917)
            self.newline()
            field918 = unwrapped_fields916[1]
            self.pretty_formula(field918)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat925 = self._try_flat(msg, self.pretty_reduce)
        if flat925 is not None:
            assert flat925 is not None
            self.write(flat925)
            return None
        else:
            def _t1555(_dollar_dollar):
                return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            _t1556 = _t1555(msg)
            fields920 = _t1556
            assert fields920 is not None
            unwrapped_fields921 = fields920
            self.write("(")
            self.write("reduce")
            self.indent_sexp()
            self.newline()
            field922 = unwrapped_fields921[0]
            self.pretty_abstraction(field922)
            self.newline()
            field923 = unwrapped_fields921[1]
            self.pretty_abstraction(field923)
            self.newline()
            field924 = unwrapped_fields921[2]
            self.pretty_terms(field924)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat930 = self._try_flat(msg, self.pretty_terms)
        if flat930 is not None:
            assert flat930 is not None
            self.write(flat930)
            return None
        else:
            def _t1557(_dollar_dollar):
                return _dollar_dollar
            _t1558 = _t1557(msg)
            fields926 = _t1558
            assert fields926 is not None
            unwrapped_fields927 = fields926
            self.write("(")
            self.write("terms")
            self.indent_sexp()
            if not len(unwrapped_fields927) == 0:
                self.newline()
                for i929, elem928 in enumerate(unwrapped_fields927):
                    if (i929 > 0):
                        self.newline()
                    self.pretty_term(elem928)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat935 = self._try_flat(msg, self.pretty_term)
        if flat935 is not None:
            assert flat935 is not None
            self.write(flat935)
            return None
        else:
            def _t1559(_dollar_dollar):
                if _dollar_dollar.HasField("var"):
                    _t1560 = _dollar_dollar.var
                else:
                    _t1560 = None
                return _t1560
            _t1561 = _t1559(msg)
            deconstruct_result933 = _t1561
            if deconstruct_result933 is not None:
                assert deconstruct_result933 is not None
                unwrapped934 = deconstruct_result933
                self.pretty_var(unwrapped934)
            else:
                def _t1562(_dollar_dollar):
                    if _dollar_dollar.HasField("constant"):
                        _t1563 = _dollar_dollar.constant
                    else:
                        _t1563 = None
                    return _t1563
                _t1564 = _t1562(msg)
                deconstruct_result931 = _t1564
                if deconstruct_result931 is not None:
                    assert deconstruct_result931 is not None
                    unwrapped932 = deconstruct_result931
                    self.pretty_constant(unwrapped932)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat938 = self._try_flat(msg, self.pretty_var)
        if flat938 is not None:
            assert flat938 is not None
            self.write(flat938)
            return None
        else:
            def _t1565(_dollar_dollar):
                return _dollar_dollar.name
            _t1566 = _t1565(msg)
            fields936 = _t1566
            assert fields936 is not None
            unwrapped_fields937 = fields936
            self.write(unwrapped_fields937)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat941 = self._try_flat(msg, self.pretty_constant)
        if flat941 is not None:
            assert flat941 is not None
            self.write(flat941)
            return None
        else:
            def _t1567(_dollar_dollar):
                return _dollar_dollar
            _t1568 = _t1567(msg)
            fields939 = _t1568
            assert fields939 is not None
            unwrapped_fields940 = fields939
            self.pretty_value(unwrapped_fields940)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat946 = self._try_flat(msg, self.pretty_conjunction)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            def _t1569(_dollar_dollar):
                return _dollar_dollar.args
            _t1570 = _t1569(msg)
            fields942 = _t1570
            assert fields942 is not None
            unwrapped_fields943 = fields942
            self.write("(")
            self.write("and")
            self.indent_sexp()
            if not len(unwrapped_fields943) == 0:
                self.newline()
                for i945, elem944 in enumerate(unwrapped_fields943):
                    if (i945 > 0):
                        self.newline()
                    self.pretty_formula(elem944)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat951 = self._try_flat(msg, self.pretty_disjunction)
        if flat951 is not None:
            assert flat951 is not None
            self.write(flat951)
            return None
        else:
            def _t1571(_dollar_dollar):
                return _dollar_dollar.args
            _t1572 = _t1571(msg)
            fields947 = _t1572
            assert fields947 is not None
            unwrapped_fields948 = fields947
            self.write("(")
            self.write("or")
            self.indent_sexp()
            if not len(unwrapped_fields948) == 0:
                self.newline()
                for i950, elem949 in enumerate(unwrapped_fields948):
                    if (i950 > 0):
                        self.newline()
                    self.pretty_formula(elem949)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat954 = self._try_flat(msg, self.pretty_not)
        if flat954 is not None:
            assert flat954 is not None
            self.write(flat954)
            return None
        else:
            def _t1573(_dollar_dollar):
                return _dollar_dollar.arg
            _t1574 = _t1573(msg)
            fields952 = _t1574
            assert fields952 is not None
            unwrapped_fields953 = fields952
            self.write("(")
            self.write("not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields953)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat960 = self._try_flat(msg, self.pretty_ffi)
        if flat960 is not None:
            assert flat960 is not None
            self.write(flat960)
            return None
        else:
            def _t1575(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            _t1576 = _t1575(msg)
            fields955 = _t1576
            assert fields955 is not None
            unwrapped_fields956 = fields955
            self.write("(")
            self.write("ffi")
            self.indent_sexp()
            self.newline()
            field957 = unwrapped_fields956[0]
            self.pretty_name(field957)
            self.newline()
            field958 = unwrapped_fields956[1]
            self.pretty_ffi_args(field958)
            self.newline()
            field959 = unwrapped_fields956[2]
            self.pretty_terms(field959)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat963 = self._try_flat(msg, self.pretty_name)
        if flat963 is not None:
            assert flat963 is not None
            self.write(flat963)
            return None
        else:
            def _t1577(_dollar_dollar):
                return _dollar_dollar
            _t1578 = _t1577(msg)
            fields961 = _t1578
            assert fields961 is not None
            unwrapped_fields962 = fields961
            self.write(":")
            self.write(unwrapped_fields962)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat968 = self._try_flat(msg, self.pretty_ffi_args)
        if flat968 is not None:
            assert flat968 is not None
            self.write(flat968)
            return None
        else:
            def _t1579(_dollar_dollar):
                return _dollar_dollar
            _t1580 = _t1579(msg)
            fields964 = _t1580
            assert fields964 is not None
            unwrapped_fields965 = fields964
            self.write("(")
            self.write("args")
            self.indent_sexp()
            if not len(unwrapped_fields965) == 0:
                self.newline()
                for i967, elem966 in enumerate(unwrapped_fields965):
                    if (i967 > 0):
                        self.newline()
                    self.pretty_abstraction(elem966)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat975 = self._try_flat(msg, self.pretty_atom)
        if flat975 is not None:
            assert flat975 is not None
            self.write(flat975)
            return None
        else:
            def _t1581(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1582 = _t1581(msg)
            fields969 = _t1582
            assert fields969 is not None
            unwrapped_fields970 = fields969
            self.write("(")
            self.write("atom")
            self.indent_sexp()
            self.newline()
            field971 = unwrapped_fields970[0]
            self.pretty_relation_id(field971)
            field972 = unwrapped_fields970[1]
            if not len(field972) == 0:
                self.newline()
                for i974, elem973 in enumerate(field972):
                    if (i974 > 0):
                        self.newline()
                    self.pretty_term(elem973)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat982 = self._try_flat(msg, self.pretty_pragma)
        if flat982 is not None:
            assert flat982 is not None
            self.write(flat982)
            return None
        else:
            def _t1583(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1584 = _t1583(msg)
            fields976 = _t1584
            assert fields976 is not None
            unwrapped_fields977 = fields976
            self.write("(")
            self.write("pragma")
            self.indent_sexp()
            self.newline()
            field978 = unwrapped_fields977[0]
            self.pretty_name(field978)
            field979 = unwrapped_fields977[1]
            if not len(field979) == 0:
                self.newline()
                for i981, elem980 in enumerate(field979):
                    if (i981 > 0):
                        self.newline()
                    self.pretty_term(elem980)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat998 = self._try_flat(msg, self.pretty_primitive)
        if flat998 is not None:
            assert flat998 is not None
            self.write(flat998)
            return None
        else:
            def _t1585(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1586 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1586 = None
                return _t1586
            _t1587 = _t1585(msg)
            guard_result997 = _t1587
            if guard_result997 is not None:
                self.pretty_eq(msg)
            else:
                def _t1588(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_monotype":
                        _t1589 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1589 = None
                    return _t1589
                _t1590 = _t1588(msg)
                guard_result996 = _t1590
                if guard_result996 is not None:
                    self.pretty_lt(msg)
                else:
                    def _t1591(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                            _t1592 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1592 = None
                        return _t1592
                    _t1593 = _t1591(msg)
                    guard_result995 = _t1593
                    if guard_result995 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        def _t1594(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                                _t1595 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1595 = None
                            return _t1595
                        _t1596 = _t1594(msg)
                        guard_result994 = _t1596
                        if guard_result994 is not None:
                            self.pretty_gt(msg)
                        else:
                            def _t1597(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                    _t1598 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                                else:
                                    _t1598 = None
                                return _t1598
                            _t1599 = _t1597(msg)
                            guard_result993 = _t1599
                            if guard_result993 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                def _t1600(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_add_monotype":
                                        _t1601 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1601 = None
                                    return _t1601
                                _t1602 = _t1600(msg)
                                guard_result992 = _t1602
                                if guard_result992 is not None:
                                    self.pretty_add(msg)
                                else:
                                    def _t1603(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                            _t1604 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1604 = None
                                        return _t1604
                                    _t1605 = _t1603(msg)
                                    guard_result991 = _t1605
                                    if guard_result991 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        def _t1606(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                                _t1607 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1607 = None
                                            return _t1607
                                        _t1608 = _t1606(msg)
                                        guard_result990 = _t1608
                                        if guard_result990 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            def _t1609(_dollar_dollar):
                                                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                    _t1610 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                                else:
                                                    _t1610 = None
                                                return _t1610
                                            _t1611 = _t1609(msg)
                                            guard_result989 = _t1611
                                            if guard_result989 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                def _t1612(_dollar_dollar):
                                                    return (_dollar_dollar.name, _dollar_dollar.terms,)
                                                _t1613 = _t1612(msg)
                                                fields983 = _t1613
                                                assert fields983 is not None
                                                unwrapped_fields984 = fields983
                                                self.write("(")
                                                self.write("primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field985 = unwrapped_fields984[0]
                                                self.pretty_name(field985)
                                                field986 = unwrapped_fields984[1]
                                                if not len(field986) == 0:
                                                    self.newline()
                                                    for i988, elem987 in enumerate(field986):
                                                        if (i988 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem987)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1003 = self._try_flat(msg, self.pretty_eq)
        if flat1003 is not None:
            assert flat1003 is not None
            self.write(flat1003)
            return None
        else:
            def _t1614(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1615 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1615 = None
                return _t1615
            _t1616 = _t1614(msg)
            fields999 = _t1616
            assert fields999 is not None
            unwrapped_fields1000 = fields999
            self.write("(")
            self.write("=")
            self.indent_sexp()
            self.newline()
            field1001 = unwrapped_fields1000[0]
            self.pretty_term(field1001)
            self.newline()
            field1002 = unwrapped_fields1000[1]
            self.pretty_term(field1002)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1008 = self._try_flat(msg, self.pretty_lt)
        if flat1008 is not None:
            assert flat1008 is not None
            self.write(flat1008)
            return None
        else:
            def _t1617(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1618 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1618 = None
                return _t1618
            _t1619 = _t1617(msg)
            fields1004 = _t1619
            assert fields1004 is not None
            unwrapped_fields1005 = fields1004
            self.write("(")
            self.write("<")
            self.indent_sexp()
            self.newline()
            field1006 = unwrapped_fields1005[0]
            self.pretty_term(field1006)
            self.newline()
            field1007 = unwrapped_fields1005[1]
            self.pretty_term(field1007)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1013 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1013 is not None:
            assert flat1013 is not None
            self.write(flat1013)
            return None
        else:
            def _t1620(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                    _t1621 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1621 = None
                return _t1621
            _t1622 = _t1620(msg)
            fields1009 = _t1622
            assert fields1009 is not None
            unwrapped_fields1010 = fields1009
            self.write("(")
            self.write("<=")
            self.indent_sexp()
            self.newline()
            field1011 = unwrapped_fields1010[0]
            self.pretty_term(field1011)
            self.newline()
            field1012 = unwrapped_fields1010[1]
            self.pretty_term(field1012)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1018 = self._try_flat(msg, self.pretty_gt)
        if flat1018 is not None:
            assert flat1018 is not None
            self.write(flat1018)
            return None
        else:
            def _t1623(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_monotype":
                    _t1624 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1624 = None
                return _t1624
            _t1625 = _t1623(msg)
            fields1014 = _t1625
            assert fields1014 is not None
            unwrapped_fields1015 = fields1014
            self.write("(")
            self.write(">")
            self.indent_sexp()
            self.newline()
            field1016 = unwrapped_fields1015[0]
            self.pretty_term(field1016)
            self.newline()
            field1017 = unwrapped_fields1015[1]
            self.pretty_term(field1017)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1023 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1023 is not None:
            assert flat1023 is not None
            self.write(flat1023)
            return None
        else:
            def _t1626(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                    _t1627 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1627 = None
                return _t1627
            _t1628 = _t1626(msg)
            fields1019 = _t1628
            assert fields1019 is not None
            unwrapped_fields1020 = fields1019
            self.write("(")
            self.write(">=")
            self.indent_sexp()
            self.newline()
            field1021 = unwrapped_fields1020[0]
            self.pretty_term(field1021)
            self.newline()
            field1022 = unwrapped_fields1020[1]
            self.pretty_term(field1022)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1029 = self._try_flat(msg, self.pretty_add)
        if flat1029 is not None:
            assert flat1029 is not None
            self.write(flat1029)
            return None
        else:
            def _t1629(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_add_monotype":
                    _t1630 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1630 = None
                return _t1630
            _t1631 = _t1629(msg)
            fields1024 = _t1631
            assert fields1024 is not None
            unwrapped_fields1025 = fields1024
            self.write("(")
            self.write("+")
            self.indent_sexp()
            self.newline()
            field1026 = unwrapped_fields1025[0]
            self.pretty_term(field1026)
            self.newline()
            field1027 = unwrapped_fields1025[1]
            self.pretty_term(field1027)
            self.newline()
            field1028 = unwrapped_fields1025[2]
            self.pretty_term(field1028)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1035 = self._try_flat(msg, self.pretty_minus)
        if flat1035 is not None:
            assert flat1035 is not None
            self.write(flat1035)
            return None
        else:
            def _t1632(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                    _t1633 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1633 = None
                return _t1633
            _t1634 = _t1632(msg)
            fields1030 = _t1634
            assert fields1030 is not None
            unwrapped_fields1031 = fields1030
            self.write("(")
            self.write("-")
            self.indent_sexp()
            self.newline()
            field1032 = unwrapped_fields1031[0]
            self.pretty_term(field1032)
            self.newline()
            field1033 = unwrapped_fields1031[1]
            self.pretty_term(field1033)
            self.newline()
            field1034 = unwrapped_fields1031[2]
            self.pretty_term(field1034)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1041 = self._try_flat(msg, self.pretty_multiply)
        if flat1041 is not None:
            assert flat1041 is not None
            self.write(flat1041)
            return None
        else:
            def _t1635(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                    _t1636 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1636 = None
                return _t1636
            _t1637 = _t1635(msg)
            fields1036 = _t1637
            assert fields1036 is not None
            unwrapped_fields1037 = fields1036
            self.write("(")
            self.write("*")
            self.indent_sexp()
            self.newline()
            field1038 = unwrapped_fields1037[0]
            self.pretty_term(field1038)
            self.newline()
            field1039 = unwrapped_fields1037[1]
            self.pretty_term(field1039)
            self.newline()
            field1040 = unwrapped_fields1037[2]
            self.pretty_term(field1040)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1047 = self._try_flat(msg, self.pretty_divide)
        if flat1047 is not None:
            assert flat1047 is not None
            self.write(flat1047)
            return None
        else:
            def _t1638(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                    _t1639 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1639 = None
                return _t1639
            _t1640 = _t1638(msg)
            fields1042 = _t1640
            assert fields1042 is not None
            unwrapped_fields1043 = fields1042
            self.write("(")
            self.write("/")
            self.indent_sexp()
            self.newline()
            field1044 = unwrapped_fields1043[0]
            self.pretty_term(field1044)
            self.newline()
            field1045 = unwrapped_fields1043[1]
            self.pretty_term(field1045)
            self.newline()
            field1046 = unwrapped_fields1043[2]
            self.pretty_term(field1046)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1052 = self._try_flat(msg, self.pretty_rel_term)
        if flat1052 is not None:
            assert flat1052 is not None
            self.write(flat1052)
            return None
        else:
            def _t1641(_dollar_dollar):
                if _dollar_dollar.HasField("specialized_value"):
                    _t1642 = _dollar_dollar.specialized_value
                else:
                    _t1642 = None
                return _t1642
            _t1643 = _t1641(msg)
            deconstruct_result1050 = _t1643
            if deconstruct_result1050 is not None:
                assert deconstruct_result1050 is not None
                unwrapped1051 = deconstruct_result1050
                self.pretty_specialized_value(unwrapped1051)
            else:
                def _t1644(_dollar_dollar):
                    if _dollar_dollar.HasField("term"):
                        _t1645 = _dollar_dollar.term
                    else:
                        _t1645 = None
                    return _t1645
                _t1646 = _t1644(msg)
                deconstruct_result1048 = _t1646
                if deconstruct_result1048 is not None:
                    assert deconstruct_result1048 is not None
                    unwrapped1049 = deconstruct_result1048
                    self.pretty_term(unwrapped1049)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1055 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1055 is not None:
            assert flat1055 is not None
            self.write(flat1055)
            return None
        else:
            def _t1647(_dollar_dollar):
                return _dollar_dollar
            _t1648 = _t1647(msg)
            fields1053 = _t1648
            assert fields1053 is not None
            unwrapped_fields1054 = fields1053
            self.write("#")
            self.pretty_value(unwrapped_fields1054)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1062 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1062 is not None:
            assert flat1062 is not None
            self.write(flat1062)
            return None
        else:
            def _t1649(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1650 = _t1649(msg)
            fields1056 = _t1650
            assert fields1056 is not None
            unwrapped_fields1057 = fields1056
            self.write("(")
            self.write("relatom")
            self.indent_sexp()
            self.newline()
            field1058 = unwrapped_fields1057[0]
            self.pretty_name(field1058)
            field1059 = unwrapped_fields1057[1]
            if not len(field1059) == 0:
                self.newline()
                for i1061, elem1060 in enumerate(field1059):
                    if (i1061 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1060)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1067 = self._try_flat(msg, self.pretty_cast)
        if flat1067 is not None:
            assert flat1067 is not None
            self.write(flat1067)
            return None
        else:
            def _t1651(_dollar_dollar):
                return (_dollar_dollar.input, _dollar_dollar.result,)
            _t1652 = _t1651(msg)
            fields1063 = _t1652
            assert fields1063 is not None
            unwrapped_fields1064 = fields1063
            self.write("(")
            self.write("cast")
            self.indent_sexp()
            self.newline()
            field1065 = unwrapped_fields1064[0]
            self.pretty_term(field1065)
            self.newline()
            field1066 = unwrapped_fields1064[1]
            self.pretty_term(field1066)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1072 = self._try_flat(msg, self.pretty_attrs)
        if flat1072 is not None:
            assert flat1072 is not None
            self.write(flat1072)
            return None
        else:
            def _t1653(_dollar_dollar):
                return _dollar_dollar
            _t1654 = _t1653(msg)
            fields1068 = _t1654
            assert fields1068 is not None
            unwrapped_fields1069 = fields1068
            self.write("(")
            self.write("attrs")
            self.indent_sexp()
            if not len(unwrapped_fields1069) == 0:
                self.newline()
                for i1071, elem1070 in enumerate(unwrapped_fields1069):
                    if (i1071 > 0):
                        self.newline()
                    self.pretty_attribute(elem1070)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1079 = self._try_flat(msg, self.pretty_attribute)
        if flat1079 is not None:
            assert flat1079 is not None
            self.write(flat1079)
            return None
        else:
            def _t1655(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args,)
            _t1656 = _t1655(msg)
            fields1073 = _t1656
            assert fields1073 is not None
            unwrapped_fields1074 = fields1073
            self.write("(")
            self.write("attribute")
            self.indent_sexp()
            self.newline()
            field1075 = unwrapped_fields1074[0]
            self.pretty_name(field1075)
            field1076 = unwrapped_fields1074[1]
            if not len(field1076) == 0:
                self.newline()
                for i1078, elem1077 in enumerate(field1076):
                    if (i1078 > 0):
                        self.newline()
                    self.pretty_value(elem1077)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1086 = self._try_flat(msg, self.pretty_algorithm)
        if flat1086 is not None:
            assert flat1086 is not None
            self.write(flat1086)
            return None
        else:
            def _t1657(_dollar_dollar):
                return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            _t1658 = _t1657(msg)
            fields1080 = _t1658
            assert fields1080 is not None
            unwrapped_fields1081 = fields1080
            self.write("(")
            self.write("algorithm")
            self.indent_sexp()
            field1082 = unwrapped_fields1081[0]
            if not len(field1082) == 0:
                self.newline()
                for i1084, elem1083 in enumerate(field1082):
                    if (i1084 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1083)
            self.newline()
            field1085 = unwrapped_fields1081[1]
            self.pretty_script(field1085)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1091 = self._try_flat(msg, self.pretty_script)
        if flat1091 is not None:
            assert flat1091 is not None
            self.write(flat1091)
            return None
        else:
            def _t1659(_dollar_dollar):
                return _dollar_dollar.constructs
            _t1660 = _t1659(msg)
            fields1087 = _t1660
            assert fields1087 is not None
            unwrapped_fields1088 = fields1087
            self.write("(")
            self.write("script")
            self.indent_sexp()
            if not len(unwrapped_fields1088) == 0:
                self.newline()
                for i1090, elem1089 in enumerate(unwrapped_fields1088):
                    if (i1090 > 0):
                        self.newline()
                    self.pretty_construct(elem1089)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1096 = self._try_flat(msg, self.pretty_construct)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            def _t1661(_dollar_dollar):
                if _dollar_dollar.HasField("loop"):
                    _t1662 = _dollar_dollar.loop
                else:
                    _t1662 = None
                return _t1662
            _t1663 = _t1661(msg)
            deconstruct_result1094 = _t1663
            if deconstruct_result1094 is not None:
                assert deconstruct_result1094 is not None
                unwrapped1095 = deconstruct_result1094
                self.pretty_loop(unwrapped1095)
            else:
                def _t1664(_dollar_dollar):
                    if _dollar_dollar.HasField("instruction"):
                        _t1665 = _dollar_dollar.instruction
                    else:
                        _t1665 = None
                    return _t1665
                _t1666 = _t1664(msg)
                deconstruct_result1092 = _t1666
                if deconstruct_result1092 is not None:
                    assert deconstruct_result1092 is not None
                    unwrapped1093 = deconstruct_result1092
                    self.pretty_instruction(unwrapped1093)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1101 = self._try_flat(msg, self.pretty_loop)
        if flat1101 is not None:
            assert flat1101 is not None
            self.write(flat1101)
            return None
        else:
            def _t1667(_dollar_dollar):
                return (_dollar_dollar.init, _dollar_dollar.body,)
            _t1668 = _t1667(msg)
            fields1097 = _t1668
            assert fields1097 is not None
            unwrapped_fields1098 = fields1097
            self.write("(")
            self.write("loop")
            self.indent_sexp()
            self.newline()
            field1099 = unwrapped_fields1098[0]
            self.pretty_init(field1099)
            self.newline()
            field1100 = unwrapped_fields1098[1]
            self.pretty_script(field1100)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1106 = self._try_flat(msg, self.pretty_init)
        if flat1106 is not None:
            assert flat1106 is not None
            self.write(flat1106)
            return None
        else:
            def _t1669(_dollar_dollar):
                return _dollar_dollar
            _t1670 = _t1669(msg)
            fields1102 = _t1670
            assert fields1102 is not None
            unwrapped_fields1103 = fields1102
            self.write("(")
            self.write("init")
            self.indent_sexp()
            if not len(unwrapped_fields1103) == 0:
                self.newline()
                for i1105, elem1104 in enumerate(unwrapped_fields1103):
                    if (i1105 > 0):
                        self.newline()
                    self.pretty_instruction(elem1104)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1117 = self._try_flat(msg, self.pretty_instruction)
        if flat1117 is not None:
            assert flat1117 is not None
            self.write(flat1117)
            return None
        else:
            def _t1671(_dollar_dollar):
                if _dollar_dollar.HasField("assign"):
                    _t1672 = _dollar_dollar.assign
                else:
                    _t1672 = None
                return _t1672
            _t1673 = _t1671(msg)
            deconstruct_result1115 = _t1673
            if deconstruct_result1115 is not None:
                assert deconstruct_result1115 is not None
                unwrapped1116 = deconstruct_result1115
                self.pretty_assign(unwrapped1116)
            else:
                def _t1674(_dollar_dollar):
                    if _dollar_dollar.HasField("upsert"):
                        _t1675 = _dollar_dollar.upsert
                    else:
                        _t1675 = None
                    return _t1675
                _t1676 = _t1674(msg)
                deconstruct_result1113 = _t1676
                if deconstruct_result1113 is not None:
                    assert deconstruct_result1113 is not None
                    unwrapped1114 = deconstruct_result1113
                    self.pretty_upsert(unwrapped1114)
                else:
                    def _t1677(_dollar_dollar):
                        if _dollar_dollar.HasField("break"):
                            _t1678 = getattr(_dollar_dollar, 'break')
                        else:
                            _t1678 = None
                        return _t1678
                    _t1679 = _t1677(msg)
                    deconstruct_result1111 = _t1679
                    if deconstruct_result1111 is not None:
                        assert deconstruct_result1111 is not None
                        unwrapped1112 = deconstruct_result1111
                        self.pretty_break(unwrapped1112)
                    else:
                        def _t1680(_dollar_dollar):
                            if _dollar_dollar.HasField("monoid_def"):
                                _t1681 = _dollar_dollar.monoid_def
                            else:
                                _t1681 = None
                            return _t1681
                        _t1682 = _t1680(msg)
                        deconstruct_result1109 = _t1682
                        if deconstruct_result1109 is not None:
                            assert deconstruct_result1109 is not None
                            unwrapped1110 = deconstruct_result1109
                            self.pretty_monoid_def(unwrapped1110)
                        else:
                            def _t1683(_dollar_dollar):
                                if _dollar_dollar.HasField("monus_def"):
                                    _t1684 = _dollar_dollar.monus_def
                                else:
                                    _t1684 = None
                                return _t1684
                            _t1685 = _t1683(msg)
                            deconstruct_result1107 = _t1685
                            if deconstruct_result1107 is not None:
                                assert deconstruct_result1107 is not None
                                unwrapped1108 = deconstruct_result1107
                                self.pretty_monus_def(unwrapped1108)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1124 = self._try_flat(msg, self.pretty_assign)
        if flat1124 is not None:
            assert flat1124 is not None
            self.write(flat1124)
            return None
        else:
            def _t1686(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1687 = _dollar_dollar.attrs
                else:
                    _t1687 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1687,)
            _t1688 = _t1686(msg)
            fields1118 = _t1688
            assert fields1118 is not None
            unwrapped_fields1119 = fields1118
            self.write("(")
            self.write("assign")
            self.indent_sexp()
            self.newline()
            field1120 = unwrapped_fields1119[0]
            self.pretty_relation_id(field1120)
            self.newline()
            field1121 = unwrapped_fields1119[1]
            self.pretty_abstraction(field1121)
            field1122 = unwrapped_fields1119[2]
            if field1122 is not None:
                self.newline()
                assert field1122 is not None
                opt_val1123 = field1122
                self.pretty_attrs(opt_val1123)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1131 = self._try_flat(msg, self.pretty_upsert)
        if flat1131 is not None:
            assert flat1131 is not None
            self.write(flat1131)
            return None
        else:
            def _t1689(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1690 = _dollar_dollar.attrs
                else:
                    _t1690 = None
                return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1690,)
            _t1691 = _t1689(msg)
            fields1125 = _t1691
            assert fields1125 is not None
            unwrapped_fields1126 = fields1125
            self.write("(")
            self.write("upsert")
            self.indent_sexp()
            self.newline()
            field1127 = unwrapped_fields1126[0]
            self.pretty_relation_id(field1127)
            self.newline()
            field1128 = unwrapped_fields1126[1]
            self.pretty_abstraction_with_arity(field1128)
            field1129 = unwrapped_fields1126[2]
            if field1129 is not None:
                self.newline()
                assert field1129 is not None
                opt_val1130 = field1129
                self.pretty_attrs(opt_val1130)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1136 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1136 is not None:
            assert flat1136 is not None
            self.write(flat1136)
            return None
        else:
            def _t1692(_dollar_dollar):
                _t1693 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
                return (_t1693, _dollar_dollar[0].value,)
            _t1694 = _t1692(msg)
            fields1132 = _t1694
            assert fields1132 is not None
            unwrapped_fields1133 = fields1132
            self.write("(")
            self.indent()
            field1134 = unwrapped_fields1133[0]
            self.pretty_bindings(field1134)
            self.newline()
            field1135 = unwrapped_fields1133[1]
            self.pretty_formula(field1135)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1143 = self._try_flat(msg, self.pretty_break)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            def _t1695(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1696 = _dollar_dollar.attrs
                else:
                    _t1696 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1696,)
            _t1697 = _t1695(msg)
            fields1137 = _t1697
            assert fields1137 is not None
            unwrapped_fields1138 = fields1137
            self.write("(")
            self.write("break")
            self.indent_sexp()
            self.newline()
            field1139 = unwrapped_fields1138[0]
            self.pretty_relation_id(field1139)
            self.newline()
            field1140 = unwrapped_fields1138[1]
            self.pretty_abstraction(field1140)
            field1141 = unwrapped_fields1138[2]
            if field1141 is not None:
                self.newline()
                assert field1141 is not None
                opt_val1142 = field1141
                self.pretty_attrs(opt_val1142)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1151 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1151 is not None:
            assert flat1151 is not None
            self.write(flat1151)
            return None
        else:
            def _t1698(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1699 = _dollar_dollar.attrs
                else:
                    _t1699 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1699,)
            _t1700 = _t1698(msg)
            fields1144 = _t1700
            assert fields1144 is not None
            unwrapped_fields1145 = fields1144
            self.write("(")
            self.write("monoid")
            self.indent_sexp()
            self.newline()
            field1146 = unwrapped_fields1145[0]
            self.pretty_monoid(field1146)
            self.newline()
            field1147 = unwrapped_fields1145[1]
            self.pretty_relation_id(field1147)
            self.newline()
            field1148 = unwrapped_fields1145[2]
            self.pretty_abstraction_with_arity(field1148)
            field1149 = unwrapped_fields1145[3]
            if field1149 is not None:
                self.newline()
                assert field1149 is not None
                opt_val1150 = field1149
                self.pretty_attrs(opt_val1150)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1160 = self._try_flat(msg, self.pretty_monoid)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            def _t1701(_dollar_dollar):
                if _dollar_dollar.HasField("or_monoid"):
                    _t1702 = _dollar_dollar.or_monoid
                else:
                    _t1702 = None
                return _t1702
            _t1703 = _t1701(msg)
            deconstruct_result1158 = _t1703
            if deconstruct_result1158 is not None:
                assert deconstruct_result1158 is not None
                unwrapped1159 = deconstruct_result1158
                self.pretty_or_monoid(unwrapped1159)
            else:
                def _t1704(_dollar_dollar):
                    if _dollar_dollar.HasField("min_monoid"):
                        _t1705 = _dollar_dollar.min_monoid
                    else:
                        _t1705 = None
                    return _t1705
                _t1706 = _t1704(msg)
                deconstruct_result1156 = _t1706
                if deconstruct_result1156 is not None:
                    assert deconstruct_result1156 is not None
                    unwrapped1157 = deconstruct_result1156
                    self.pretty_min_monoid(unwrapped1157)
                else:
                    def _t1707(_dollar_dollar):
                        if _dollar_dollar.HasField("max_monoid"):
                            _t1708 = _dollar_dollar.max_monoid
                        else:
                            _t1708 = None
                        return _t1708
                    _t1709 = _t1707(msg)
                    deconstruct_result1154 = _t1709
                    if deconstruct_result1154 is not None:
                        assert deconstruct_result1154 is not None
                        unwrapped1155 = deconstruct_result1154
                        self.pretty_max_monoid(unwrapped1155)
                    else:
                        def _t1710(_dollar_dollar):
                            if _dollar_dollar.HasField("sum_monoid"):
                                _t1711 = _dollar_dollar.sum_monoid
                            else:
                                _t1711 = None
                            return _t1711
                        _t1712 = _t1710(msg)
                        deconstruct_result1152 = _t1712
                        if deconstruct_result1152 is not None:
                            assert deconstruct_result1152 is not None
                            unwrapped1153 = deconstruct_result1152
                            self.pretty_sum_monoid(unwrapped1153)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        flat1163 = self._try_flat(msg, self.pretty_or_monoid)
        if flat1163 is not None:
            assert flat1163 is not None
            self.write(flat1163)
            return None
        else:
            def _t1713(_dollar_dollar):
                return _dollar_dollar
            _t1714 = _t1713(msg)
            fields1161 = _t1714
            assert fields1161 is not None
            unwrapped_fields1162 = fields1161
            self.write("(")
            self.write("or")
            self.write(")")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1166 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1166 is not None:
            assert flat1166 is not None
            self.write(flat1166)
            return None
        else:
            def _t1715(_dollar_dollar):
                return _dollar_dollar.type
            _t1716 = _t1715(msg)
            fields1164 = _t1716
            assert fields1164 is not None
            unwrapped_fields1165 = fields1164
            self.write("(")
            self.write("min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1165)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1169 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1169 is not None:
            assert flat1169 is not None
            self.write(flat1169)
            return None
        else:
            def _t1717(_dollar_dollar):
                return _dollar_dollar.type
            _t1718 = _t1717(msg)
            fields1167 = _t1718
            assert fields1167 is not None
            unwrapped_fields1168 = fields1167
            self.write("(")
            self.write("max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1168)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1172 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            def _t1719(_dollar_dollar):
                return _dollar_dollar.type
            _t1720 = _t1719(msg)
            fields1170 = _t1720
            assert fields1170 is not None
            unwrapped_fields1171 = fields1170
            self.write("(")
            self.write("sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1171)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1180 = self._try_flat(msg, self.pretty_monus_def)
        if flat1180 is not None:
            assert flat1180 is not None
            self.write(flat1180)
            return None
        else:
            def _t1721(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1722 = _dollar_dollar.attrs
                else:
                    _t1722 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1722,)
            _t1723 = _t1721(msg)
            fields1173 = _t1723
            assert fields1173 is not None
            unwrapped_fields1174 = fields1173
            self.write("(")
            self.write("monus")
            self.indent_sexp()
            self.newline()
            field1175 = unwrapped_fields1174[0]
            self.pretty_monoid(field1175)
            self.newline()
            field1176 = unwrapped_fields1174[1]
            self.pretty_relation_id(field1176)
            self.newline()
            field1177 = unwrapped_fields1174[2]
            self.pretty_abstraction_with_arity(field1177)
            field1178 = unwrapped_fields1174[3]
            if field1178 is not None:
                self.newline()
                assert field1178 is not None
                opt_val1179 = field1178
                self.pretty_attrs(opt_val1179)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1187 = self._try_flat(msg, self.pretty_constraint)
        if flat1187 is not None:
            assert flat1187 is not None
            self.write(flat1187)
            return None
        else:
            def _t1724(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            _t1725 = _t1724(msg)
            fields1181 = _t1725
            assert fields1181 is not None
            unwrapped_fields1182 = fields1181
            self.write("(")
            self.write("functional_dependency")
            self.indent_sexp()
            self.newline()
            field1183 = unwrapped_fields1182[0]
            self.pretty_relation_id(field1183)
            self.newline()
            field1184 = unwrapped_fields1182[1]
            self.pretty_abstraction(field1184)
            self.newline()
            field1185 = unwrapped_fields1182[2]
            self.pretty_functional_dependency_keys(field1185)
            self.newline()
            field1186 = unwrapped_fields1182[3]
            self.pretty_functional_dependency_values(field1186)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1192 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1192 is not None:
            assert flat1192 is not None
            self.write(flat1192)
            return None
        else:
            def _t1726(_dollar_dollar):
                return _dollar_dollar
            _t1727 = _t1726(msg)
            fields1188 = _t1727
            assert fields1188 is not None
            unwrapped_fields1189 = fields1188
            self.write("(")
            self.write("keys")
            self.indent_sexp()
            if not len(unwrapped_fields1189) == 0:
                self.newline()
                for i1191, elem1190 in enumerate(unwrapped_fields1189):
                    if (i1191 > 0):
                        self.newline()
                    self.pretty_var(elem1190)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1197 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1197 is not None:
            assert flat1197 is not None
            self.write(flat1197)
            return None
        else:
            def _t1728(_dollar_dollar):
                return _dollar_dollar
            _t1729 = _t1728(msg)
            fields1193 = _t1729
            assert fields1193 is not None
            unwrapped_fields1194 = fields1193
            self.write("(")
            self.write("values")
            self.indent_sexp()
            if not len(unwrapped_fields1194) == 0:
                self.newline()
                for i1196, elem1195 in enumerate(unwrapped_fields1194):
                    if (i1196 > 0):
                        self.newline()
                    self.pretty_var(elem1195)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1204 = self._try_flat(msg, self.pretty_data)
        if flat1204 is not None:
            assert flat1204 is not None
            self.write(flat1204)
            return None
        else:
            def _t1730(_dollar_dollar):
                if _dollar_dollar.HasField("rel_edb"):
                    _t1731 = _dollar_dollar.rel_edb
                else:
                    _t1731 = None
                return _t1731
            _t1732 = _t1730(msg)
            deconstruct_result1202 = _t1732
            if deconstruct_result1202 is not None:
                assert deconstruct_result1202 is not None
                unwrapped1203 = deconstruct_result1202
                self.pretty_rel_edb(unwrapped1203)
            else:
                def _t1733(_dollar_dollar):
                    if _dollar_dollar.HasField("betree_relation"):
                        _t1734 = _dollar_dollar.betree_relation
                    else:
                        _t1734 = None
                    return _t1734
                _t1735 = _t1733(msg)
                deconstruct_result1200 = _t1735
                if deconstruct_result1200 is not None:
                    assert deconstruct_result1200 is not None
                    unwrapped1201 = deconstruct_result1200
                    self.pretty_betree_relation(unwrapped1201)
                else:
                    def _t1736(_dollar_dollar):
                        if _dollar_dollar.HasField("csv_data"):
                            _t1737 = _dollar_dollar.csv_data
                        else:
                            _t1737 = None
                        return _t1737
                    _t1738 = _t1736(msg)
                    deconstruct_result1198 = _t1738
                    if deconstruct_result1198 is not None:
                        assert deconstruct_result1198 is not None
                        unwrapped1199 = deconstruct_result1198
                        self.pretty_csv_data(unwrapped1199)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB):
        flat1210 = self._try_flat(msg, self.pretty_rel_edb)
        if flat1210 is not None:
            assert flat1210 is not None
            self.write(flat1210)
            return None
        else:
            def _t1739(_dollar_dollar):
                return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            _t1740 = _t1739(msg)
            fields1205 = _t1740
            assert fields1205 is not None
            unwrapped_fields1206 = fields1205
            self.write("(")
            self.write("rel_edb")
            self.indent_sexp()
            self.newline()
            field1207 = unwrapped_fields1206[0]
            self.pretty_relation_id(field1207)
            self.newline()
            field1208 = unwrapped_fields1206[1]
            self.pretty_rel_edb_path(field1208)
            self.newline()
            field1209 = unwrapped_fields1206[2]
            self.pretty_rel_edb_types(field1209)
            self.dedent()
            self.write(")")

    def pretty_rel_edb_path(self, msg: Sequence[str]):
        flat1215 = self._try_flat(msg, self.pretty_rel_edb_path)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            def _t1741(_dollar_dollar):
                return _dollar_dollar
            _t1742 = _t1741(msg)
            fields1211 = _t1742
            assert fields1211 is not None
            unwrapped_fields1212 = fields1211
            self.write("[")
            self.indent()
            for i1214, elem1213 in enumerate(unwrapped_fields1212):
                if (i1214 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1213))
            self.dedent()
            self.write("]")

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1220 = self._try_flat(msg, self.pretty_rel_edb_types)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            def _t1743(_dollar_dollar):
                return _dollar_dollar
            _t1744 = _t1743(msg)
            fields1216 = _t1744
            assert fields1216 is not None
            unwrapped_fields1217 = fields1216
            self.write("[")
            self.indent()
            for i1219, elem1218 in enumerate(unwrapped_fields1217):
                if (i1219 > 0):
                    self.newline()
                self.pretty_type(elem1218)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1225 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1225 is not None:
            assert flat1225 is not None
            self.write(flat1225)
            return None
        else:
            def _t1745(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_info,)
            _t1746 = _t1745(msg)
            fields1221 = _t1746
            assert fields1221 is not None
            unwrapped_fields1222 = fields1221
            self.write("(")
            self.write("betree_relation")
            self.indent_sexp()
            self.newline()
            field1223 = unwrapped_fields1222[0]
            self.pretty_relation_id(field1223)
            self.newline()
            field1224 = unwrapped_fields1222[1]
            self.pretty_betree_info(field1224)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1231 = self._try_flat(msg, self.pretty_betree_info)
        if flat1231 is not None:
            assert flat1231 is not None
            self.write(flat1231)
            return None
        else:
            def _t1747(_dollar_dollar):
                _t1748 = self.deconstruct_betree_info_config(_dollar_dollar)
                return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1748,)
            _t1749 = _t1747(msg)
            fields1226 = _t1749
            assert fields1226 is not None
            unwrapped_fields1227 = fields1226
            self.write("(")
            self.write("betree_info")
            self.indent_sexp()
            self.newline()
            field1228 = unwrapped_fields1227[0]
            self.pretty_betree_info_key_types(field1228)
            self.newline()
            field1229 = unwrapped_fields1227[1]
            self.pretty_betree_info_value_types(field1229)
            self.newline()
            field1230 = unwrapped_fields1227[2]
            self.pretty_config_dict(field1230)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1236 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1236 is not None:
            assert flat1236 is not None
            self.write(flat1236)
            return None
        else:
            def _t1750(_dollar_dollar):
                return _dollar_dollar
            _t1751 = _t1750(msg)
            fields1232 = _t1751
            assert fields1232 is not None
            unwrapped_fields1233 = fields1232
            self.write("(")
            self.write("key_types")
            self.indent_sexp()
            if not len(unwrapped_fields1233) == 0:
                self.newline()
                for i1235, elem1234 in enumerate(unwrapped_fields1233):
                    if (i1235 > 0):
                        self.newline()
                    self.pretty_type(elem1234)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1241 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1241 is not None:
            assert flat1241 is not None
            self.write(flat1241)
            return None
        else:
            def _t1752(_dollar_dollar):
                return _dollar_dollar
            _t1753 = _t1752(msg)
            fields1237 = _t1753
            assert fields1237 is not None
            unwrapped_fields1238 = fields1237
            self.write("(")
            self.write("value_types")
            self.indent_sexp()
            if not len(unwrapped_fields1238) == 0:
                self.newline()
                for i1240, elem1239 in enumerate(unwrapped_fields1238):
                    if (i1240 > 0):
                        self.newline()
                    self.pretty_type(elem1239)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1248 = self._try_flat(msg, self.pretty_csv_data)
        if flat1248 is not None:
            assert flat1248 is not None
            self.write(flat1248)
            return None
        else:
            def _t1754(_dollar_dollar):
                return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            _t1755 = _t1754(msg)
            fields1242 = _t1755
            assert fields1242 is not None
            unwrapped_fields1243 = fields1242
            self.write("(")
            self.write("csv_data")
            self.indent_sexp()
            self.newline()
            field1244 = unwrapped_fields1243[0]
            self.pretty_csvlocator(field1244)
            self.newline()
            field1245 = unwrapped_fields1243[1]
            self.pretty_csv_config(field1245)
            self.newline()
            field1246 = unwrapped_fields1243[2]
            self.pretty_csv_columns(field1246)
            self.newline()
            field1247 = unwrapped_fields1243[3]
            self.pretty_csv_asof(field1247)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1255 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1255 is not None:
            assert flat1255 is not None
            self.write(flat1255)
            return None
        else:
            def _t1756(_dollar_dollar):
                if not len(_dollar_dollar.paths) == 0:
                    _t1757 = _dollar_dollar.paths
                else:
                    _t1757 = None
                if _dollar_dollar.inline_data.decode('utf-8') != "":
                    _t1758 = _dollar_dollar.inline_data.decode('utf-8')
                else:
                    _t1758 = None
                return (_t1757, _t1758,)
            _t1759 = _t1756(msg)
            fields1249 = _t1759
            assert fields1249 is not None
            unwrapped_fields1250 = fields1249
            self.write("(")
            self.write("csv_locator")
            self.indent_sexp()
            field1251 = unwrapped_fields1250[0]
            if field1251 is not None:
                self.newline()
                assert field1251 is not None
                opt_val1252 = field1251
                self.pretty_csv_locator_paths(opt_val1252)
            field1253 = unwrapped_fields1250[1]
            if field1253 is not None:
                self.newline()
                assert field1253 is not None
                opt_val1254 = field1253
                self.pretty_csv_locator_inline_data(opt_val1254)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1260 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1260 is not None:
            assert flat1260 is not None
            self.write(flat1260)
            return None
        else:
            def _t1760(_dollar_dollar):
                return _dollar_dollar
            _t1761 = _t1760(msg)
            fields1256 = _t1761
            assert fields1256 is not None
            unwrapped_fields1257 = fields1256
            self.write("(")
            self.write("paths")
            self.indent_sexp()
            if not len(unwrapped_fields1257) == 0:
                self.newline()
                for i1259, elem1258 in enumerate(unwrapped_fields1257):
                    if (i1259 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1258))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1263 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1263 is not None:
            assert flat1263 is not None
            self.write(flat1263)
            return None
        else:
            def _t1762(_dollar_dollar):
                return _dollar_dollar
            _t1763 = _t1762(msg)
            fields1261 = _t1763
            assert fields1261 is not None
            unwrapped_fields1262 = fields1261
            self.write("(")
            self.write("inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(unwrapped_fields1262))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1266 = self._try_flat(msg, self.pretty_csv_config)
        if flat1266 is not None:
            assert flat1266 is not None
            self.write(flat1266)
            return None
        else:
            def _t1764(_dollar_dollar):
                _t1765 = self.deconstruct_csv_config(_dollar_dollar)
                return _t1765
            _t1766 = _t1764(msg)
            fields1264 = _t1766
            assert fields1264 is not None
            unwrapped_fields1265 = fields1264
            self.write("(")
            self.write("csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1265)
            self.dedent()
            self.write(")")

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]):
        flat1271 = self._try_flat(msg, self.pretty_csv_columns)
        if flat1271 is not None:
            assert flat1271 is not None
            self.write(flat1271)
            return None
        else:
            def _t1767(_dollar_dollar):
                return _dollar_dollar
            _t1768 = _t1767(msg)
            fields1267 = _t1768
            assert fields1267 is not None
            unwrapped_fields1268 = fields1267
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(unwrapped_fields1268) == 0:
                self.newline()
                for i1270, elem1269 in enumerate(unwrapped_fields1268):
                    if (i1270 > 0):
                        self.newline()
                    self.pretty_csv_column(elem1269)
            self.dedent()
            self.write(")")

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn):
        flat1279 = self._try_flat(msg, self.pretty_csv_column)
        if flat1279 is not None:
            assert flat1279 is not None
            self.write(flat1279)
            return None
        else:
            def _t1769(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
            _t1770 = _t1769(msg)
            fields1272 = _t1770
            assert fields1272 is not None
            unwrapped_fields1273 = fields1272
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1274 = unwrapped_fields1273[0]
            self.write(self.format_string_value(field1274))
            self.newline()
            field1275 = unwrapped_fields1273[1]
            self.pretty_relation_id(field1275)
            self.newline()
            self.write("[")
            field1276 = unwrapped_fields1273[2]
            for i1278, elem1277 in enumerate(field1276):
                if (i1278 > 0):
                    self.newline()
                self.pretty_type(elem1277)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1282 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1282 is not None:
            assert flat1282 is not None
            self.write(flat1282)
            return None
        else:
            def _t1771(_dollar_dollar):
                return _dollar_dollar
            _t1772 = _t1771(msg)
            fields1280 = _t1772
            assert fields1280 is not None
            unwrapped_fields1281 = fields1280
            self.write("(")
            self.write("asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(unwrapped_fields1281))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1285 = self._try_flat(msg, self.pretty_undefine)
        if flat1285 is not None:
            assert flat1285 is not None
            self.write(flat1285)
            return None
        else:
            def _t1773(_dollar_dollar):
                return _dollar_dollar.fragment_id
            _t1774 = _t1773(msg)
            fields1283 = _t1774
            assert fields1283 is not None
            unwrapped_fields1284 = fields1283
            self.write("(")
            self.write("undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1284)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1290 = self._try_flat(msg, self.pretty_context)
        if flat1290 is not None:
            assert flat1290 is not None
            self.write(flat1290)
            return None
        else:
            def _t1775(_dollar_dollar):
                return _dollar_dollar.relations
            _t1776 = _t1775(msg)
            fields1286 = _t1776
            assert fields1286 is not None
            unwrapped_fields1287 = fields1286
            self.write("(")
            self.write("context")
            self.indent_sexp()
            if not len(unwrapped_fields1287) == 0:
                self.newline()
                for i1289, elem1288 in enumerate(unwrapped_fields1287):
                    if (i1289 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1288)
            self.dedent()
            self.write(")")

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1295 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1295 is not None:
            assert flat1295 is not None
            self.write(flat1295)
            return None
        else:
            def _t1777(_dollar_dollar):
                return _dollar_dollar
            _t1778 = _t1777(msg)
            fields1291 = _t1778
            assert fields1291 is not None
            unwrapped_fields1292 = fields1291
            self.write("(")
            self.write("reads")
            self.indent_sexp()
            if not len(unwrapped_fields1292) == 0:
                self.newline()
                for i1294, elem1293 in enumerate(unwrapped_fields1292):
                    if (i1294 > 0):
                        self.newline()
                    self.pretty_read(elem1293)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1306 = self._try_flat(msg, self.pretty_read)
        if flat1306 is not None:
            assert flat1306 is not None
            self.write(flat1306)
            return None
        else:
            def _t1779(_dollar_dollar):
                if _dollar_dollar.HasField("demand"):
                    _t1780 = _dollar_dollar.demand
                else:
                    _t1780 = None
                return _t1780
            _t1781 = _t1779(msg)
            deconstruct_result1304 = _t1781
            if deconstruct_result1304 is not None:
                assert deconstruct_result1304 is not None
                unwrapped1305 = deconstruct_result1304
                self.pretty_demand(unwrapped1305)
            else:
                def _t1782(_dollar_dollar):
                    if _dollar_dollar.HasField("output"):
                        _t1783 = _dollar_dollar.output
                    else:
                        _t1783 = None
                    return _t1783
                _t1784 = _t1782(msg)
                deconstruct_result1302 = _t1784
                if deconstruct_result1302 is not None:
                    assert deconstruct_result1302 is not None
                    unwrapped1303 = deconstruct_result1302
                    self.pretty_output(unwrapped1303)
                else:
                    def _t1785(_dollar_dollar):
                        if _dollar_dollar.HasField("what_if"):
                            _t1786 = _dollar_dollar.what_if
                        else:
                            _t1786 = None
                        return _t1786
                    _t1787 = _t1785(msg)
                    deconstruct_result1300 = _t1787
                    if deconstruct_result1300 is not None:
                        assert deconstruct_result1300 is not None
                        unwrapped1301 = deconstruct_result1300
                        self.pretty_what_if(unwrapped1301)
                    else:
                        def _t1788(_dollar_dollar):
                            if _dollar_dollar.HasField("abort"):
                                _t1789 = _dollar_dollar.abort
                            else:
                                _t1789 = None
                            return _t1789
                        _t1790 = _t1788(msg)
                        deconstruct_result1298 = _t1790
                        if deconstruct_result1298 is not None:
                            assert deconstruct_result1298 is not None
                            unwrapped1299 = deconstruct_result1298
                            self.pretty_abort(unwrapped1299)
                        else:
                            def _t1791(_dollar_dollar):
                                if _dollar_dollar.HasField("export"):
                                    _t1792 = _dollar_dollar.export
                                else:
                                    _t1792 = None
                                return _t1792
                            _t1793 = _t1791(msg)
                            deconstruct_result1296 = _t1793
                            if deconstruct_result1296 is not None:
                                assert deconstruct_result1296 is not None
                                unwrapped1297 = deconstruct_result1296
                                self.pretty_export(unwrapped1297)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1309 = self._try_flat(msg, self.pretty_demand)
        if flat1309 is not None:
            assert flat1309 is not None
            self.write(flat1309)
            return None
        else:
            def _t1794(_dollar_dollar):
                return _dollar_dollar.relation_id
            _t1795 = _t1794(msg)
            fields1307 = _t1795
            assert fields1307 is not None
            unwrapped_fields1308 = fields1307
            self.write("(")
            self.write("demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1308)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1314 = self._try_flat(msg, self.pretty_output)
        if flat1314 is not None:
            assert flat1314 is not None
            self.write(flat1314)
            return None
        else:
            def _t1796(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_id,)
            _t1797 = _t1796(msg)
            fields1310 = _t1797
            assert fields1310 is not None
            unwrapped_fields1311 = fields1310
            self.write("(")
            self.write("output")
            self.indent_sexp()
            self.newline()
            field1312 = unwrapped_fields1311[0]
            self.pretty_name(field1312)
            self.newline()
            field1313 = unwrapped_fields1311[1]
            self.pretty_relation_id(field1313)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1319 = self._try_flat(msg, self.pretty_what_if)
        if flat1319 is not None:
            assert flat1319 is not None
            self.write(flat1319)
            return None
        else:
            def _t1798(_dollar_dollar):
                return (_dollar_dollar.branch, _dollar_dollar.epoch,)
            _t1799 = _t1798(msg)
            fields1315 = _t1799
            assert fields1315 is not None
            unwrapped_fields1316 = fields1315
            self.write("(")
            self.write("what_if")
            self.indent_sexp()
            self.newline()
            field1317 = unwrapped_fields1316[0]
            self.pretty_name(field1317)
            self.newline()
            field1318 = unwrapped_fields1316[1]
            self.pretty_epoch(field1318)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1325 = self._try_flat(msg, self.pretty_abort)
        if flat1325 is not None:
            assert flat1325 is not None
            self.write(flat1325)
            return None
        else:
            def _t1800(_dollar_dollar):
                if _dollar_dollar.name != "abort":
                    _t1801 = _dollar_dollar.name
                else:
                    _t1801 = None
                return (_t1801, _dollar_dollar.relation_id,)
            _t1802 = _t1800(msg)
            fields1320 = _t1802
            assert fields1320 is not None
            unwrapped_fields1321 = fields1320
            self.write("(")
            self.write("abort")
            self.indent_sexp()
            field1322 = unwrapped_fields1321[0]
            if field1322 is not None:
                self.newline()
                assert field1322 is not None
                opt_val1323 = field1322
                self.pretty_name(opt_val1323)
            self.newline()
            field1324 = unwrapped_fields1321[1]
            self.pretty_relation_id(field1324)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1328 = self._try_flat(msg, self.pretty_export)
        if flat1328 is not None:
            assert flat1328 is not None
            self.write(flat1328)
            return None
        else:
            def _t1803(_dollar_dollar):
                return _dollar_dollar.csv_config
            _t1804 = _t1803(msg)
            fields1326 = _t1804
            assert fields1326 is not None
            unwrapped_fields1327 = fields1326
            self.write("(")
            self.write("export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1327)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1334 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1334 is not None:
            assert flat1334 is not None
            self.write(flat1334)
            return None
        else:
            def _t1805(_dollar_dollar):
                _t1806 = self.deconstruct_export_csv_config(_dollar_dollar)
                return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1806,)
            _t1807 = _t1805(msg)
            fields1329 = _t1807
            assert fields1329 is not None
            unwrapped_fields1330 = fields1329
            self.write("(")
            self.write("export_csv_config")
            self.indent_sexp()
            self.newline()
            field1331 = unwrapped_fields1330[0]
            self.pretty_export_csv_path(field1331)
            self.newline()
            field1332 = unwrapped_fields1330[1]
            self.pretty_export_csv_columns(field1332)
            self.newline()
            field1333 = unwrapped_fields1330[2]
            self.pretty_config_dict(field1333)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1337 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1337 is not None:
            assert flat1337 is not None
            self.write(flat1337)
            return None
        else:
            def _t1808(_dollar_dollar):
                return _dollar_dollar
            _t1809 = _t1808(msg)
            fields1335 = _t1809
            assert fields1335 is not None
            unwrapped_fields1336 = fields1335
            self.write("(")
            self.write("path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(unwrapped_fields1336))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1342 = self._try_flat(msg, self.pretty_export_csv_columns)
        if flat1342 is not None:
            assert flat1342 is not None
            self.write(flat1342)
            return None
        else:
            def _t1810(_dollar_dollar):
                return _dollar_dollar
            _t1811 = _t1810(msg)
            fields1338 = _t1811
            assert fields1338 is not None
            unwrapped_fields1339 = fields1338
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(unwrapped_fields1339) == 0:
                self.newline()
                for i1341, elem1340 in enumerate(unwrapped_fields1339):
                    if (i1341 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1340)
            self.dedent()
            self.write(")")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1347 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1347 is not None:
            assert flat1347 is not None
            self.write(flat1347)
            return None
        else:
            def _t1812(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            _t1813 = _t1812(msg)
            fields1343 = _t1813
            assert fields1343 is not None
            unwrapped_fields1344 = fields1343
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1345 = unwrapped_fields1344[0]
            self.write(self.format_string_value(field1345))
            self.newline()
            field1346 = unwrapped_fields1344[1]
            self.pretty_relation_id(field1346)
            self.dedent()
            self.write(")")


def pretty(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
