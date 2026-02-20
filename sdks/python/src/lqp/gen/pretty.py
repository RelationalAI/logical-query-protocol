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

    def relation_id_to_uint128(self, msg: logic_pb2.RelationId) -> logic_pb2.UInt128Value:
        """Convert RelationId to UInt128Value representation."""
        return logic_pb2.UInt128Value(low=msg.id_low, high=msg.id_high)

    def format_string_value(self, s: str) -> str:
        """Format a string value with double quotes for LQP output."""
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return '"' + escaped + '"'

    # --- Helper functions ---

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1687 = logic_pb2.Value(int_value=int(v))
        return _t1687

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1688 = logic_pb2.Value(int_value=v)
        return _t1688

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1689 = logic_pb2.Value(float_value=v)
        return _t1689

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1690 = logic_pb2.Value(string_value=v)
        return _t1690

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1691 = logic_pb2.Value(boolean_value=v)
        return _t1691

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1692 = logic_pb2.Value(uint128_value=v)
        return _t1692

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1693 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1693,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1694 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1694,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1695 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1695,))
        _t1696 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1696,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1697 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1697,))
        _t1698 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1698,))
        if msg.new_line != "":
            _t1699 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1699,))
        _t1700 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1700,))
        _t1701 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1701,))
        _t1702 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1702,))
        if msg.comment != "":
            _t1703 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1703,))
        for missing_string in msg.missing_strings:
            _t1704 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1704,))
        _t1705 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1705,))
        _t1706 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1706,))
        _t1707 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1707,))
        if msg.partition_size_mb != 0:
            _t1708 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1708,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1709 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1709,))
        _t1710 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1710,))
        _t1711 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1711,))
        _t1712 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1712,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1713 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1713,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1714 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1714,))
        _t1715 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1715,))
        _t1716 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1716,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1717 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1717,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1718 = self._make_value_string(msg.compression)
            result.append(("compression", _t1718,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1719 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1719,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1720 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1720,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1721 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1721,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1722 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1722,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1723 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1723,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != "":
            return name
        else:
            _t1724 = None
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == "":
            return self.relation_id_to_uint128(msg)
        else:
            _t1725 = None
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
        flat650 = self._try_flat(msg, self.pretty_transaction)
        if flat650 is not None:
            assert flat650 is not None
            self.write(flat650)
            return None
        else:
            def _t1282(_dollar_dollar):
                if _dollar_dollar.HasField("configure"):
                    _t1283 = _dollar_dollar.configure
                else:
                    _t1283 = None
                if _dollar_dollar.HasField("sync"):
                    _t1284 = _dollar_dollar.sync
                else:
                    _t1284 = None
                return (_t1283, _t1284, _dollar_dollar.epochs,)
            _t1285 = _t1282(msg)
            fields641 = _t1285
            assert fields641 is not None
            unwrapped_fields642 = fields641
            self.write("(")
            self.write("transaction")
            self.indent_sexp()
            field643 = unwrapped_fields642[0]
            if field643 is not None:
                self.newline()
                assert field643 is not None
                opt_val644 = field643
                self.pretty_configure(opt_val644)
            field645 = unwrapped_fields642[1]
            if field645 is not None:
                self.newline()
                assert field645 is not None
                opt_val646 = field645
                self.pretty_sync(opt_val646)
            field647 = unwrapped_fields642[2]
            if not len(field647) == 0:
                self.newline()
                for i649, elem648 in enumerate(field647):
                    if (i649 > 0):
                        self.newline()
                    self.pretty_epoch(elem648)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat653 = self._try_flat(msg, self.pretty_configure)
        if flat653 is not None:
            assert flat653 is not None
            self.write(flat653)
            return None
        else:
            def _t1286(_dollar_dollar):
                _t1287 = self.deconstruct_configure(_dollar_dollar)
                return _t1287
            _t1288 = _t1286(msg)
            fields651 = _t1288
            assert fields651 is not None
            unwrapped_fields652 = fields651
            self.write("(")
            self.write("configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields652)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat657 = self._try_flat(msg, self.pretty_config_dict)
        if flat657 is not None:
            assert flat657 is not None
            self.write(flat657)
            return None
        else:
            fields654 = msg
            self.write("{")
            self.indent()
            if not len(fields654) == 0:
                self.newline()
                for i656, elem655 in enumerate(fields654):
                    if (i656 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem655)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat662 = self._try_flat(msg, self.pretty_config_key_value)
        if flat662 is not None:
            assert flat662 is not None
            self.write(flat662)
            return None
        else:
            def _t1289(_dollar_dollar):
                return (_dollar_dollar[0], _dollar_dollar[1],)
            _t1290 = _t1289(msg)
            fields658 = _t1290
            assert fields658 is not None
            unwrapped_fields659 = fields658
            self.write(":")
            field660 = unwrapped_fields659[0]
            self.write(field660)
            self.write(" ")
            field661 = unwrapped_fields659[1]
            self.pretty_value(field661)

    def pretty_value(self, msg: logic_pb2.Value):
        flat682 = self._try_flat(msg, self.pretty_value)
        if flat682 is not None:
            assert flat682 is not None
            self.write(flat682)
            return None
        else:
            def _t1291(_dollar_dollar):
                if _dollar_dollar.HasField("date_value"):
                    _t1292 = _dollar_dollar.date_value
                else:
                    _t1292 = None
                return _t1292
            _t1293 = _t1291(msg)
            deconstruct_result680 = _t1293
            if deconstruct_result680 is not None:
                assert deconstruct_result680 is not None
                unwrapped681 = deconstruct_result680
                self.pretty_date(unwrapped681)
            else:
                def _t1294(_dollar_dollar):
                    if _dollar_dollar.HasField("datetime_value"):
                        _t1295 = _dollar_dollar.datetime_value
                    else:
                        _t1295 = None
                    return _t1295
                _t1296 = _t1294(msg)
                deconstruct_result678 = _t1296
                if deconstruct_result678 is not None:
                    assert deconstruct_result678 is not None
                    unwrapped679 = deconstruct_result678
                    self.pretty_datetime(unwrapped679)
                else:
                    def _t1297(_dollar_dollar):
                        if _dollar_dollar.HasField("string_value"):
                            _t1298 = _dollar_dollar.string_value
                        else:
                            _t1298 = None
                        return _t1298
                    _t1299 = _t1297(msg)
                    deconstruct_result676 = _t1299
                    if deconstruct_result676 is not None:
                        assert deconstruct_result676 is not None
                        unwrapped677 = deconstruct_result676
                        self.write(self.format_string_value(unwrapped677))
                    else:
                        def _t1300(_dollar_dollar):
                            if _dollar_dollar.HasField("int_value"):
                                _t1301 = _dollar_dollar.int_value
                            else:
                                _t1301 = None
                            return _t1301
                        _t1302 = _t1300(msg)
                        deconstruct_result674 = _t1302
                        if deconstruct_result674 is not None:
                            assert deconstruct_result674 is not None
                            unwrapped675 = deconstruct_result674
                            self.write(str(unwrapped675))
                        else:
                            def _t1303(_dollar_dollar):
                                if _dollar_dollar.HasField("float_value"):
                                    _t1304 = _dollar_dollar.float_value
                                else:
                                    _t1304 = None
                                return _t1304
                            _t1305 = _t1303(msg)
                            deconstruct_result672 = _t1305
                            if deconstruct_result672 is not None:
                                assert deconstruct_result672 is not None
                                unwrapped673 = deconstruct_result672
                                self.write(str(unwrapped673))
                            else:
                                def _t1306(_dollar_dollar):
                                    if _dollar_dollar.HasField("uint128_value"):
                                        _t1307 = _dollar_dollar.uint128_value
                                    else:
                                        _t1307 = None
                                    return _t1307
                                _t1308 = _t1306(msg)
                                deconstruct_result670 = _t1308
                                if deconstruct_result670 is not None:
                                    assert deconstruct_result670 is not None
                                    unwrapped671 = deconstruct_result670
                                    self.write(self.format_uint128(unwrapped671))
                                else:
                                    def _t1309(_dollar_dollar):
                                        if _dollar_dollar.HasField("int128_value"):
                                            _t1310 = _dollar_dollar.int128_value
                                        else:
                                            _t1310 = None
                                        return _t1310
                                    _t1311 = _t1309(msg)
                                    deconstruct_result668 = _t1311
                                    if deconstruct_result668 is not None:
                                        assert deconstruct_result668 is not None
                                        unwrapped669 = deconstruct_result668
                                        self.write(self.format_int128(unwrapped669))
                                    else:
                                        def _t1312(_dollar_dollar):
                                            if _dollar_dollar.HasField("decimal_value"):
                                                _t1313 = _dollar_dollar.decimal_value
                                            else:
                                                _t1313 = None
                                            return _t1313
                                        _t1314 = _t1312(msg)
                                        deconstruct_result666 = _t1314
                                        if deconstruct_result666 is not None:
                                            assert deconstruct_result666 is not None
                                            unwrapped667 = deconstruct_result666
                                            self.write(self.format_decimal(unwrapped667))
                                        else:
                                            def _t1315(_dollar_dollar):
                                                if _dollar_dollar.HasField("boolean_value"):
                                                    _t1316 = _dollar_dollar.boolean_value
                                                else:
                                                    _t1316 = None
                                                return _t1316
                                            _t1317 = _t1315(msg)
                                            deconstruct_result664 = _t1317
                                            if deconstruct_result664 is not None:
                                                assert deconstruct_result664 is not None
                                                unwrapped665 = deconstruct_result664
                                                self.pretty_boolean_value(unwrapped665)
                                            else:
                                                fields663 = msg
                                                self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat688 = self._try_flat(msg, self.pretty_date)
        if flat688 is not None:
            assert flat688 is not None
            self.write(flat688)
            return None
        else:
            def _t1318(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            _t1319 = _t1318(msg)
            fields683 = _t1319
            assert fields683 is not None
            unwrapped_fields684 = fields683
            self.write("(")
            self.write("date")
            self.indent_sexp()
            self.newline()
            field685 = unwrapped_fields684[0]
            self.write(str(field685))
            self.newline()
            field686 = unwrapped_fields684[1]
            self.write(str(field686))
            self.newline()
            field687 = unwrapped_fields684[2]
            self.write(str(field687))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat699 = self._try_flat(msg, self.pretty_datetime)
        if flat699 is not None:
            assert flat699 is not None
            self.write(flat699)
            return None
        else:
            def _t1320(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            _t1321 = _t1320(msg)
            fields689 = _t1321
            assert fields689 is not None
            unwrapped_fields690 = fields689
            self.write("(")
            self.write("datetime")
            self.indent_sexp()
            self.newline()
            field691 = unwrapped_fields690[0]
            self.write(str(field691))
            self.newline()
            field692 = unwrapped_fields690[1]
            self.write(str(field692))
            self.newline()
            field693 = unwrapped_fields690[2]
            self.write(str(field693))
            self.newline()
            field694 = unwrapped_fields690[3]
            self.write(str(field694))
            self.newline()
            field695 = unwrapped_fields690[4]
            self.write(str(field695))
            self.newline()
            field696 = unwrapped_fields690[5]
            self.write(str(field696))
            field697 = unwrapped_fields690[6]
            if field697 is not None:
                self.newline()
                assert field697 is not None
                opt_val698 = field697
                self.write(str(opt_val698))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        def _t1322(_dollar_dollar):
            if _dollar_dollar:
                _t1323 = ()
            else:
                _t1323 = None
            return _t1323
        _t1324 = _t1322(msg)
        deconstruct_result702 = _t1324
        if deconstruct_result702 is not None:
            assert deconstruct_result702 is not None
            unwrapped703 = deconstruct_result702
            self.write("true")
        else:
            def _t1325(_dollar_dollar):
                if not _dollar_dollar:
                    _t1326 = ()
                else:
                    _t1326 = None
                return _t1326
            _t1327 = _t1325(msg)
            deconstruct_result700 = _t1327
            if deconstruct_result700 is not None:
                assert deconstruct_result700 is not None
                unwrapped701 = deconstruct_result700
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat708 = self._try_flat(msg, self.pretty_sync)
        if flat708 is not None:
            assert flat708 is not None
            self.write(flat708)
            return None
        else:
            def _t1328(_dollar_dollar):
                return _dollar_dollar.fragments
            _t1329 = _t1328(msg)
            fields704 = _t1329
            assert fields704 is not None
            unwrapped_fields705 = fields704
            self.write("(")
            self.write("sync")
            self.indent_sexp()
            if not len(unwrapped_fields705) == 0:
                self.newline()
                for i707, elem706 in enumerate(unwrapped_fields705):
                    if (i707 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem706)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat711 = self._try_flat(msg, self.pretty_fragment_id)
        if flat711 is not None:
            assert flat711 is not None
            self.write(flat711)
            return None
        else:
            def _t1330(_dollar_dollar):
                return self.fragment_id_to_string(_dollar_dollar)
            _t1331 = _t1330(msg)
            fields709 = _t1331
            assert fields709 is not None
            unwrapped_fields710 = fields709
            self.write(":")
            self.write(unwrapped_fields710)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat718 = self._try_flat(msg, self.pretty_epoch)
        if flat718 is not None:
            assert flat718 is not None
            self.write(flat718)
            return None
        else:
            def _t1332(_dollar_dollar):
                if not len(_dollar_dollar.writes) == 0:
                    _t1333 = _dollar_dollar.writes
                else:
                    _t1333 = None
                if not len(_dollar_dollar.reads) == 0:
                    _t1334 = _dollar_dollar.reads
                else:
                    _t1334 = None
                return (_t1333, _t1334,)
            _t1335 = _t1332(msg)
            fields712 = _t1335
            assert fields712 is not None
            unwrapped_fields713 = fields712
            self.write("(")
            self.write("epoch")
            self.indent_sexp()
            field714 = unwrapped_fields713[0]
            if field714 is not None:
                self.newline()
                assert field714 is not None
                opt_val715 = field714
                self.pretty_epoch_writes(opt_val715)
            field716 = unwrapped_fields713[1]
            if field716 is not None:
                self.newline()
                assert field716 is not None
                opt_val717 = field716
                self.pretty_epoch_reads(opt_val717)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat722 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat722 is not None:
            assert flat722 is not None
            self.write(flat722)
            return None
        else:
            fields719 = msg
            self.write("(")
            self.write("writes")
            self.indent_sexp()
            if not len(fields719) == 0:
                self.newline()
                for i721, elem720 in enumerate(fields719):
                    if (i721 > 0):
                        self.newline()
                    self.pretty_write(elem720)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat731 = self._try_flat(msg, self.pretty_write)
        if flat731 is not None:
            assert flat731 is not None
            self.write(flat731)
            return None
        else:
            def _t1336(_dollar_dollar):
                if _dollar_dollar.HasField("define"):
                    _t1337 = _dollar_dollar.define
                else:
                    _t1337 = None
                return _t1337
            _t1338 = _t1336(msg)
            deconstruct_result729 = _t1338
            if deconstruct_result729 is not None:
                assert deconstruct_result729 is not None
                unwrapped730 = deconstruct_result729
                self.pretty_define(unwrapped730)
            else:
                def _t1339(_dollar_dollar):
                    if _dollar_dollar.HasField("undefine"):
                        _t1340 = _dollar_dollar.undefine
                    else:
                        _t1340 = None
                    return _t1340
                _t1341 = _t1339(msg)
                deconstruct_result727 = _t1341
                if deconstruct_result727 is not None:
                    assert deconstruct_result727 is not None
                    unwrapped728 = deconstruct_result727
                    self.pretty_undefine(unwrapped728)
                else:
                    def _t1342(_dollar_dollar):
                        if _dollar_dollar.HasField("context"):
                            _t1343 = _dollar_dollar.context
                        else:
                            _t1343 = None
                        return _t1343
                    _t1344 = _t1342(msg)
                    deconstruct_result725 = _t1344
                    if deconstruct_result725 is not None:
                        assert deconstruct_result725 is not None
                        unwrapped726 = deconstruct_result725
                        self.pretty_context(unwrapped726)
                    else:
                        def _t1345(_dollar_dollar):
                            if _dollar_dollar.HasField("snapshot"):
                                _t1346 = _dollar_dollar.snapshot
                            else:
                                _t1346 = None
                            return _t1346
                        _t1347 = _t1345(msg)
                        deconstruct_result723 = _t1347
                        if deconstruct_result723 is not None:
                            assert deconstruct_result723 is not None
                            unwrapped724 = deconstruct_result723
                            self.pretty_snapshot(unwrapped724)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat734 = self._try_flat(msg, self.pretty_define)
        if flat734 is not None:
            assert flat734 is not None
            self.write(flat734)
            return None
        else:
            def _t1348(_dollar_dollar):
                return _dollar_dollar.fragment
            _t1349 = _t1348(msg)
            fields732 = _t1349
            assert fields732 is not None
            unwrapped_fields733 = fields732
            self.write("(")
            self.write("define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields733)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat741 = self._try_flat(msg, self.pretty_fragment)
        if flat741 is not None:
            assert flat741 is not None
            self.write(flat741)
            return None
        else:
            def _t1350(_dollar_dollar):
                self.start_pretty_fragment(_dollar_dollar)
                return (_dollar_dollar.id, _dollar_dollar.declarations,)
            _t1351 = _t1350(msg)
            fields735 = _t1351
            assert fields735 is not None
            unwrapped_fields736 = fields735
            self.write("(")
            self.write("fragment")
            self.indent_sexp()
            self.newline()
            field737 = unwrapped_fields736[0]
            self.pretty_new_fragment_id(field737)
            field738 = unwrapped_fields736[1]
            if not len(field738) == 0:
                self.newline()
                for i740, elem739 in enumerate(field738):
                    if (i740 > 0):
                        self.newline()
                    self.pretty_declaration(elem739)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat743 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat743 is not None:
            assert flat743 is not None
            self.write(flat743)
            return None
        else:
            fields742 = msg
            self.pretty_fragment_id(fields742)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat752 = self._try_flat(msg, self.pretty_declaration)
        if flat752 is not None:
            assert flat752 is not None
            self.write(flat752)
            return None
        else:
            def _t1352(_dollar_dollar):
                if _dollar_dollar.HasField("def"):
                    _t1353 = getattr(_dollar_dollar, 'def')
                else:
                    _t1353 = None
                return _t1353
            _t1354 = _t1352(msg)
            deconstruct_result750 = _t1354
            if deconstruct_result750 is not None:
                assert deconstruct_result750 is not None
                unwrapped751 = deconstruct_result750
                self.pretty_def(unwrapped751)
            else:
                def _t1355(_dollar_dollar):
                    if _dollar_dollar.HasField("algorithm"):
                        _t1356 = _dollar_dollar.algorithm
                    else:
                        _t1356 = None
                    return _t1356
                _t1357 = _t1355(msg)
                deconstruct_result748 = _t1357
                if deconstruct_result748 is not None:
                    assert deconstruct_result748 is not None
                    unwrapped749 = deconstruct_result748
                    self.pretty_algorithm(unwrapped749)
                else:
                    def _t1358(_dollar_dollar):
                        if _dollar_dollar.HasField("constraint"):
                            _t1359 = _dollar_dollar.constraint
                        else:
                            _t1359 = None
                        return _t1359
                    _t1360 = _t1358(msg)
                    deconstruct_result746 = _t1360
                    if deconstruct_result746 is not None:
                        assert deconstruct_result746 is not None
                        unwrapped747 = deconstruct_result746
                        self.pretty_constraint(unwrapped747)
                    else:
                        def _t1361(_dollar_dollar):
                            if _dollar_dollar.HasField("data"):
                                _t1362 = _dollar_dollar.data
                            else:
                                _t1362 = None
                            return _t1362
                        _t1363 = _t1361(msg)
                        deconstruct_result744 = _t1363
                        if deconstruct_result744 is not None:
                            assert deconstruct_result744 is not None
                            unwrapped745 = deconstruct_result744
                            self.pretty_data(unwrapped745)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat759 = self._try_flat(msg, self.pretty_def)
        if flat759 is not None:
            assert flat759 is not None
            self.write(flat759)
            return None
        else:
            def _t1364(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1365 = _dollar_dollar.attrs
                else:
                    _t1365 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1365,)
            _t1366 = _t1364(msg)
            fields753 = _t1366
            assert fields753 is not None
            unwrapped_fields754 = fields753
            self.write("(")
            self.write("def")
            self.indent_sexp()
            self.newline()
            field755 = unwrapped_fields754[0]
            self.pretty_relation_id(field755)
            self.newline()
            field756 = unwrapped_fields754[1]
            self.pretty_abstraction(field756)
            field757 = unwrapped_fields754[2]
            if field757 is not None:
                self.newline()
                assert field757 is not None
                opt_val758 = field757
                self.pretty_attrs(opt_val758)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat764 = self._try_flat(msg, self.pretty_relation_id)
        if flat764 is not None:
            assert flat764 is not None
            self.write(flat764)
            return None
        else:
            def _t1367(_dollar_dollar):
                _t1368 = self.deconstruct_relation_id_string(_dollar_dollar)
                return _t1368
            _t1369 = _t1367(msg)
            deconstruct_result762 = _t1369
            if deconstruct_result762 is not None:
                assert deconstruct_result762 is not None
                unwrapped763 = deconstruct_result762
                self.write(":")
                self.write(unwrapped763)
            else:
                def _t1370(_dollar_dollar):
                    _t1371 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                    return _t1371
                _t1372 = _t1370(msg)
                deconstruct_result760 = _t1372
                if deconstruct_result760 is not None:
                    assert deconstruct_result760 is not None
                    unwrapped761 = deconstruct_result760
                    self.write(self.format_uint128(unwrapped761))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat769 = self._try_flat(msg, self.pretty_abstraction)
        if flat769 is not None:
            assert flat769 is not None
            self.write(flat769)
            return None
        else:
            def _t1373(_dollar_dollar):
                _t1374 = self.deconstruct_bindings(_dollar_dollar)
                return (_t1374, _dollar_dollar.value,)
            _t1375 = _t1373(msg)
            fields765 = _t1375
            assert fields765 is not None
            unwrapped_fields766 = fields765
            self.write("(")
            self.indent()
            field767 = unwrapped_fields766[0]
            self.pretty_bindings(field767)
            self.newline()
            field768 = unwrapped_fields766[1]
            self.pretty_formula(field768)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat777 = self._try_flat(msg, self.pretty_bindings)
        if flat777 is not None:
            assert flat777 is not None
            self.write(flat777)
            return None
        else:
            def _t1376(_dollar_dollar):
                if not len(_dollar_dollar[1]) == 0:
                    _t1377 = _dollar_dollar[1]
                else:
                    _t1377 = None
                return (_dollar_dollar[0], _t1377,)
            _t1378 = _t1376(msg)
            fields770 = _t1378
            assert fields770 is not None
            unwrapped_fields771 = fields770
            self.write("[")
            self.indent()
            field772 = unwrapped_fields771[0]
            for i774, elem773 in enumerate(field772):
                if (i774 > 0):
                    self.newline()
                self.pretty_binding(elem773)
            field775 = unwrapped_fields771[1]
            if field775 is not None:
                self.newline()
                assert field775 is not None
                opt_val776 = field775
                self.pretty_value_bindings(opt_val776)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat782 = self._try_flat(msg, self.pretty_binding)
        if flat782 is not None:
            assert flat782 is not None
            self.write(flat782)
            return None
        else:
            def _t1379(_dollar_dollar):
                return (_dollar_dollar.var.name, _dollar_dollar.type,)
            _t1380 = _t1379(msg)
            fields778 = _t1380
            assert fields778 is not None
            unwrapped_fields779 = fields778
            field780 = unwrapped_fields779[0]
            self.write(field780)
            self.write("::")
            field781 = unwrapped_fields779[1]
            self.pretty_type(field781)

    def pretty_type(self, msg: logic_pb2.Type):
        flat805 = self._try_flat(msg, self.pretty_type)
        if flat805 is not None:
            assert flat805 is not None
            self.write(flat805)
            return None
        else:
            def _t1381(_dollar_dollar):
                if _dollar_dollar.HasField("unspecified_type"):
                    _t1382 = _dollar_dollar.unspecified_type
                else:
                    _t1382 = None
                return _t1382
            _t1383 = _t1381(msg)
            deconstruct_result803 = _t1383
            if deconstruct_result803 is not None:
                assert deconstruct_result803 is not None
                unwrapped804 = deconstruct_result803
                self.pretty_unspecified_type(unwrapped804)
            else:
                def _t1384(_dollar_dollar):
                    if _dollar_dollar.HasField("string_type"):
                        _t1385 = _dollar_dollar.string_type
                    else:
                        _t1385 = None
                    return _t1385
                _t1386 = _t1384(msg)
                deconstruct_result801 = _t1386
                if deconstruct_result801 is not None:
                    assert deconstruct_result801 is not None
                    unwrapped802 = deconstruct_result801
                    self.pretty_string_type(unwrapped802)
                else:
                    def _t1387(_dollar_dollar):
                        if _dollar_dollar.HasField("int_type"):
                            _t1388 = _dollar_dollar.int_type
                        else:
                            _t1388 = None
                        return _t1388
                    _t1389 = _t1387(msg)
                    deconstruct_result799 = _t1389
                    if deconstruct_result799 is not None:
                        assert deconstruct_result799 is not None
                        unwrapped800 = deconstruct_result799
                        self.pretty_int_type(unwrapped800)
                    else:
                        def _t1390(_dollar_dollar):
                            if _dollar_dollar.HasField("float_type"):
                                _t1391 = _dollar_dollar.float_type
                            else:
                                _t1391 = None
                            return _t1391
                        _t1392 = _t1390(msg)
                        deconstruct_result797 = _t1392
                        if deconstruct_result797 is not None:
                            assert deconstruct_result797 is not None
                            unwrapped798 = deconstruct_result797
                            self.pretty_float_type(unwrapped798)
                        else:
                            def _t1393(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_type"):
                                    _t1394 = _dollar_dollar.uint128_type
                                else:
                                    _t1394 = None
                                return _t1394
                            _t1395 = _t1393(msg)
                            deconstruct_result795 = _t1395
                            if deconstruct_result795 is not None:
                                assert deconstruct_result795 is not None
                                unwrapped796 = deconstruct_result795
                                self.pretty_uint128_type(unwrapped796)
                            else:
                                def _t1396(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_type"):
                                        _t1397 = _dollar_dollar.int128_type
                                    else:
                                        _t1397 = None
                                    return _t1397
                                _t1398 = _t1396(msg)
                                deconstruct_result793 = _t1398
                                if deconstruct_result793 is not None:
                                    assert deconstruct_result793 is not None
                                    unwrapped794 = deconstruct_result793
                                    self.pretty_int128_type(unwrapped794)
                                else:
                                    def _t1399(_dollar_dollar):
                                        if _dollar_dollar.HasField("date_type"):
                                            _t1400 = _dollar_dollar.date_type
                                        else:
                                            _t1400 = None
                                        return _t1400
                                    _t1401 = _t1399(msg)
                                    deconstruct_result791 = _t1401
                                    if deconstruct_result791 is not None:
                                        assert deconstruct_result791 is not None
                                        unwrapped792 = deconstruct_result791
                                        self.pretty_date_type(unwrapped792)
                                    else:
                                        def _t1402(_dollar_dollar):
                                            if _dollar_dollar.HasField("datetime_type"):
                                                _t1403 = _dollar_dollar.datetime_type
                                            else:
                                                _t1403 = None
                                            return _t1403
                                        _t1404 = _t1402(msg)
                                        deconstruct_result789 = _t1404
                                        if deconstruct_result789 is not None:
                                            assert deconstruct_result789 is not None
                                            unwrapped790 = deconstruct_result789
                                            self.pretty_datetime_type(unwrapped790)
                                        else:
                                            def _t1405(_dollar_dollar):
                                                if _dollar_dollar.HasField("missing_type"):
                                                    _t1406 = _dollar_dollar.missing_type
                                                else:
                                                    _t1406 = None
                                                return _t1406
                                            _t1407 = _t1405(msg)
                                            deconstruct_result787 = _t1407
                                            if deconstruct_result787 is not None:
                                                assert deconstruct_result787 is not None
                                                unwrapped788 = deconstruct_result787
                                                self.pretty_missing_type(unwrapped788)
                                            else:
                                                def _t1408(_dollar_dollar):
                                                    if _dollar_dollar.HasField("decimal_type"):
                                                        _t1409 = _dollar_dollar.decimal_type
                                                    else:
                                                        _t1409 = None
                                                    return _t1409
                                                _t1410 = _t1408(msg)
                                                deconstruct_result785 = _t1410
                                                if deconstruct_result785 is not None:
                                                    assert deconstruct_result785 is not None
                                                    unwrapped786 = deconstruct_result785
                                                    self.pretty_decimal_type(unwrapped786)
                                                else:
                                                    def _t1411(_dollar_dollar):
                                                        if _dollar_dollar.HasField("boolean_type"):
                                                            _t1412 = _dollar_dollar.boolean_type
                                                        else:
                                                            _t1412 = None
                                                        return _t1412
                                                    _t1413 = _t1411(msg)
                                                    deconstruct_result783 = _t1413
                                                    if deconstruct_result783 is not None:
                                                        assert deconstruct_result783 is not None
                                                        unwrapped784 = deconstruct_result783
                                                        self.pretty_boolean_type(unwrapped784)
                                                    else:
                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields806 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields807 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields808 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields809 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields810 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields811 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields812 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields813 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields814 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat819 = self._try_flat(msg, self.pretty_decimal_type)
        if flat819 is not None:
            assert flat819 is not None
            self.write(flat819)
            return None
        else:
            def _t1414(_dollar_dollar):
                return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            _t1415 = _t1414(msg)
            fields815 = _t1415
            assert fields815 is not None
            unwrapped_fields816 = fields815
            self.write("(")
            self.write("DECIMAL")
            self.indent_sexp()
            self.newline()
            field817 = unwrapped_fields816[0]
            self.write(str(field817))
            self.newline()
            field818 = unwrapped_fields816[1]
            self.write(str(field818))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields820 = msg
        self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat824 = self._try_flat(msg, self.pretty_value_bindings)
        if flat824 is not None:
            assert flat824 is not None
            self.write(flat824)
            return None
        else:
            fields821 = msg
            self.write("|")
            if not len(fields821) == 0:
                self.write(" ")
                for i823, elem822 in enumerate(fields821):
                    if (i823 > 0):
                        self.newline()
                    self.pretty_binding(elem822)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat851 = self._try_flat(msg, self.pretty_formula)
        if flat851 is not None:
            assert flat851 is not None
            self.write(flat851)
            return None
        else:
            def _t1416(_dollar_dollar):
                if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                    _t1417 = _dollar_dollar.conjunction
                else:
                    _t1417 = None
                return _t1417
            _t1418 = _t1416(msg)
            deconstruct_result849 = _t1418
            if deconstruct_result849 is not None:
                assert deconstruct_result849 is not None
                unwrapped850 = deconstruct_result849
                self.pretty_true(unwrapped850)
            else:
                def _t1419(_dollar_dollar):
                    if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                        _t1420 = _dollar_dollar.disjunction
                    else:
                        _t1420 = None
                    return _t1420
                _t1421 = _t1419(msg)
                deconstruct_result847 = _t1421
                if deconstruct_result847 is not None:
                    assert deconstruct_result847 is not None
                    unwrapped848 = deconstruct_result847
                    self.pretty_false(unwrapped848)
                else:
                    def _t1422(_dollar_dollar):
                        if _dollar_dollar.HasField("exists"):
                            _t1423 = _dollar_dollar.exists
                        else:
                            _t1423 = None
                        return _t1423
                    _t1424 = _t1422(msg)
                    deconstruct_result845 = _t1424
                    if deconstruct_result845 is not None:
                        assert deconstruct_result845 is not None
                        unwrapped846 = deconstruct_result845
                        self.pretty_exists(unwrapped846)
                    else:
                        def _t1425(_dollar_dollar):
                            if _dollar_dollar.HasField("reduce"):
                                _t1426 = _dollar_dollar.reduce
                            else:
                                _t1426 = None
                            return _t1426
                        _t1427 = _t1425(msg)
                        deconstruct_result843 = _t1427
                        if deconstruct_result843 is not None:
                            assert deconstruct_result843 is not None
                            unwrapped844 = deconstruct_result843
                            self.pretty_reduce(unwrapped844)
                        else:
                            def _t1428(_dollar_dollar):
                                if _dollar_dollar.HasField("conjunction"):
                                    _t1429 = _dollar_dollar.conjunction
                                else:
                                    _t1429 = None
                                return _t1429
                            _t1430 = _t1428(msg)
                            deconstruct_result841 = _t1430
                            if deconstruct_result841 is not None:
                                assert deconstruct_result841 is not None
                                unwrapped842 = deconstruct_result841
                                self.pretty_conjunction(unwrapped842)
                            else:
                                def _t1431(_dollar_dollar):
                                    if _dollar_dollar.HasField("disjunction"):
                                        _t1432 = _dollar_dollar.disjunction
                                    else:
                                        _t1432 = None
                                    return _t1432
                                _t1433 = _t1431(msg)
                                deconstruct_result839 = _t1433
                                if deconstruct_result839 is not None:
                                    assert deconstruct_result839 is not None
                                    unwrapped840 = deconstruct_result839
                                    self.pretty_disjunction(unwrapped840)
                                else:
                                    def _t1434(_dollar_dollar):
                                        if _dollar_dollar.HasField("not"):
                                            _t1435 = getattr(_dollar_dollar, 'not')
                                        else:
                                            _t1435 = None
                                        return _t1435
                                    _t1436 = _t1434(msg)
                                    deconstruct_result837 = _t1436
                                    if deconstruct_result837 is not None:
                                        assert deconstruct_result837 is not None
                                        unwrapped838 = deconstruct_result837
                                        self.pretty_not(unwrapped838)
                                    else:
                                        def _t1437(_dollar_dollar):
                                            if _dollar_dollar.HasField("ffi"):
                                                _t1438 = _dollar_dollar.ffi
                                            else:
                                                _t1438 = None
                                            return _t1438
                                        _t1439 = _t1437(msg)
                                        deconstruct_result835 = _t1439
                                        if deconstruct_result835 is not None:
                                            assert deconstruct_result835 is not None
                                            unwrapped836 = deconstruct_result835
                                            self.pretty_ffi(unwrapped836)
                                        else:
                                            def _t1440(_dollar_dollar):
                                                if _dollar_dollar.HasField("atom"):
                                                    _t1441 = _dollar_dollar.atom
                                                else:
                                                    _t1441 = None
                                                return _t1441
                                            _t1442 = _t1440(msg)
                                            deconstruct_result833 = _t1442
                                            if deconstruct_result833 is not None:
                                                assert deconstruct_result833 is not None
                                                unwrapped834 = deconstruct_result833
                                                self.pretty_atom(unwrapped834)
                                            else:
                                                def _t1443(_dollar_dollar):
                                                    if _dollar_dollar.HasField("pragma"):
                                                        _t1444 = _dollar_dollar.pragma
                                                    else:
                                                        _t1444 = None
                                                    return _t1444
                                                _t1445 = _t1443(msg)
                                                deconstruct_result831 = _t1445
                                                if deconstruct_result831 is not None:
                                                    assert deconstruct_result831 is not None
                                                    unwrapped832 = deconstruct_result831
                                                    self.pretty_pragma(unwrapped832)
                                                else:
                                                    def _t1446(_dollar_dollar):
                                                        if _dollar_dollar.HasField("primitive"):
                                                            _t1447 = _dollar_dollar.primitive
                                                        else:
                                                            _t1447 = None
                                                        return _t1447
                                                    _t1448 = _t1446(msg)
                                                    deconstruct_result829 = _t1448
                                                    if deconstruct_result829 is not None:
                                                        assert deconstruct_result829 is not None
                                                        unwrapped830 = deconstruct_result829
                                                        self.pretty_primitive(unwrapped830)
                                                    else:
                                                        def _t1449(_dollar_dollar):
                                                            if _dollar_dollar.HasField("rel_atom"):
                                                                _t1450 = _dollar_dollar.rel_atom
                                                            else:
                                                                _t1450 = None
                                                            return _t1450
                                                        _t1451 = _t1449(msg)
                                                        deconstruct_result827 = _t1451
                                                        if deconstruct_result827 is not None:
                                                            assert deconstruct_result827 is not None
                                                            unwrapped828 = deconstruct_result827
                                                            self.pretty_rel_atom(unwrapped828)
                                                        else:
                                                            def _t1452(_dollar_dollar):
                                                                if _dollar_dollar.HasField("cast"):
                                                                    _t1453 = _dollar_dollar.cast
                                                                else:
                                                                    _t1453 = None
                                                                return _t1453
                                                            _t1454 = _t1452(msg)
                                                            deconstruct_result825 = _t1454
                                                            if deconstruct_result825 is not None:
                                                                assert deconstruct_result825 is not None
                                                                unwrapped826 = deconstruct_result825
                                                                self.pretty_cast(unwrapped826)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields852 = msg
        self.write("(")
        self.write("true")
        self.write(")")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields853 = msg
        self.write("(")
        self.write("false")
        self.write(")")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat858 = self._try_flat(msg, self.pretty_exists)
        if flat858 is not None:
            assert flat858 is not None
            self.write(flat858)
            return None
        else:
            def _t1455(_dollar_dollar):
                _t1456 = self.deconstruct_bindings(_dollar_dollar.body)
                return (_t1456, _dollar_dollar.body.value,)
            _t1457 = _t1455(msg)
            fields854 = _t1457
            assert fields854 is not None
            unwrapped_fields855 = fields854
            self.write("(")
            self.write("exists")
            self.indent_sexp()
            self.newline()
            field856 = unwrapped_fields855[0]
            self.pretty_bindings(field856)
            self.newline()
            field857 = unwrapped_fields855[1]
            self.pretty_formula(field857)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat864 = self._try_flat(msg, self.pretty_reduce)
        if flat864 is not None:
            assert flat864 is not None
            self.write(flat864)
            return None
        else:
            def _t1458(_dollar_dollar):
                return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            _t1459 = _t1458(msg)
            fields859 = _t1459
            assert fields859 is not None
            unwrapped_fields860 = fields859
            self.write("(")
            self.write("reduce")
            self.indent_sexp()
            self.newline()
            field861 = unwrapped_fields860[0]
            self.pretty_abstraction(field861)
            self.newline()
            field862 = unwrapped_fields860[1]
            self.pretty_abstraction(field862)
            self.newline()
            field863 = unwrapped_fields860[2]
            self.pretty_terms(field863)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat868 = self._try_flat(msg, self.pretty_terms)
        if flat868 is not None:
            assert flat868 is not None
            self.write(flat868)
            return None
        else:
            fields865 = msg
            self.write("(")
            self.write("terms")
            self.indent_sexp()
            if not len(fields865) == 0:
                self.newline()
                for i867, elem866 in enumerate(fields865):
                    if (i867 > 0):
                        self.newline()
                    self.pretty_term(elem866)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat873 = self._try_flat(msg, self.pretty_term)
        if flat873 is not None:
            assert flat873 is not None
            self.write(flat873)
            return None
        else:
            def _t1460(_dollar_dollar):
                if _dollar_dollar.HasField("var"):
                    _t1461 = _dollar_dollar.var
                else:
                    _t1461 = None
                return _t1461
            _t1462 = _t1460(msg)
            deconstruct_result871 = _t1462
            if deconstruct_result871 is not None:
                assert deconstruct_result871 is not None
                unwrapped872 = deconstruct_result871
                self.pretty_var(unwrapped872)
            else:
                def _t1463(_dollar_dollar):
                    if _dollar_dollar.HasField("constant"):
                        _t1464 = _dollar_dollar.constant
                    else:
                        _t1464 = None
                    return _t1464
                _t1465 = _t1463(msg)
                deconstruct_result869 = _t1465
                if deconstruct_result869 is not None:
                    assert deconstruct_result869 is not None
                    unwrapped870 = deconstruct_result869
                    self.pretty_constant(unwrapped870)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat876 = self._try_flat(msg, self.pretty_var)
        if flat876 is not None:
            assert flat876 is not None
            self.write(flat876)
            return None
        else:
            def _t1466(_dollar_dollar):
                return _dollar_dollar.name
            _t1467 = _t1466(msg)
            fields874 = _t1467
            assert fields874 is not None
            unwrapped_fields875 = fields874
            self.write(unwrapped_fields875)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat878 = self._try_flat(msg, self.pretty_constant)
        if flat878 is not None:
            assert flat878 is not None
            self.write(flat878)
            return None
        else:
            fields877 = msg
            self.pretty_value(fields877)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat883 = self._try_flat(msg, self.pretty_conjunction)
        if flat883 is not None:
            assert flat883 is not None
            self.write(flat883)
            return None
        else:
            def _t1468(_dollar_dollar):
                return _dollar_dollar.args
            _t1469 = _t1468(msg)
            fields879 = _t1469
            assert fields879 is not None
            unwrapped_fields880 = fields879
            self.write("(")
            self.write("and")
            self.indent_sexp()
            if not len(unwrapped_fields880) == 0:
                self.newline()
                for i882, elem881 in enumerate(unwrapped_fields880):
                    if (i882 > 0):
                        self.newline()
                    self.pretty_formula(elem881)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat888 = self._try_flat(msg, self.pretty_disjunction)
        if flat888 is not None:
            assert flat888 is not None
            self.write(flat888)
            return None
        else:
            def _t1470(_dollar_dollar):
                return _dollar_dollar.args
            _t1471 = _t1470(msg)
            fields884 = _t1471
            assert fields884 is not None
            unwrapped_fields885 = fields884
            self.write("(")
            self.write("or")
            self.indent_sexp()
            if not len(unwrapped_fields885) == 0:
                self.newline()
                for i887, elem886 in enumerate(unwrapped_fields885):
                    if (i887 > 0):
                        self.newline()
                    self.pretty_formula(elem886)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat891 = self._try_flat(msg, self.pretty_not)
        if flat891 is not None:
            assert flat891 is not None
            self.write(flat891)
            return None
        else:
            def _t1472(_dollar_dollar):
                return _dollar_dollar.arg
            _t1473 = _t1472(msg)
            fields889 = _t1473
            assert fields889 is not None
            unwrapped_fields890 = fields889
            self.write("(")
            self.write("not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields890)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat897 = self._try_flat(msg, self.pretty_ffi)
        if flat897 is not None:
            assert flat897 is not None
            self.write(flat897)
            return None
        else:
            def _t1474(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            _t1475 = _t1474(msg)
            fields892 = _t1475
            assert fields892 is not None
            unwrapped_fields893 = fields892
            self.write("(")
            self.write("ffi")
            self.indent_sexp()
            self.newline()
            field894 = unwrapped_fields893[0]
            self.pretty_name(field894)
            self.newline()
            field895 = unwrapped_fields893[1]
            self.pretty_ffi_args(field895)
            self.newline()
            field896 = unwrapped_fields893[2]
            self.pretty_terms(field896)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat899 = self._try_flat(msg, self.pretty_name)
        if flat899 is not None:
            assert flat899 is not None
            self.write(flat899)
            return None
        else:
            fields898 = msg
            self.write(":")
            self.write(fields898)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat903 = self._try_flat(msg, self.pretty_ffi_args)
        if flat903 is not None:
            assert flat903 is not None
            self.write(flat903)
            return None
        else:
            fields900 = msg
            self.write("(")
            self.write("args")
            self.indent_sexp()
            if not len(fields900) == 0:
                self.newline()
                for i902, elem901 in enumerate(fields900):
                    if (i902 > 0):
                        self.newline()
                    self.pretty_abstraction(elem901)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat910 = self._try_flat(msg, self.pretty_atom)
        if flat910 is not None:
            assert flat910 is not None
            self.write(flat910)
            return None
        else:
            def _t1476(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1477 = _t1476(msg)
            fields904 = _t1477
            assert fields904 is not None
            unwrapped_fields905 = fields904
            self.write("(")
            self.write("atom")
            self.indent_sexp()
            self.newline()
            field906 = unwrapped_fields905[0]
            self.pretty_relation_id(field906)
            field907 = unwrapped_fields905[1]
            if not len(field907) == 0:
                self.newline()
                for i909, elem908 in enumerate(field907):
                    if (i909 > 0):
                        self.newline()
                    self.pretty_term(elem908)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat917 = self._try_flat(msg, self.pretty_pragma)
        if flat917 is not None:
            assert flat917 is not None
            self.write(flat917)
            return None
        else:
            def _t1478(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1479 = _t1478(msg)
            fields911 = _t1479
            assert fields911 is not None
            unwrapped_fields912 = fields911
            self.write("(")
            self.write("pragma")
            self.indent_sexp()
            self.newline()
            field913 = unwrapped_fields912[0]
            self.pretty_name(field913)
            field914 = unwrapped_fields912[1]
            if not len(field914) == 0:
                self.newline()
                for i916, elem915 in enumerate(field914):
                    if (i916 > 0):
                        self.newline()
                    self.pretty_term(elem915)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat933 = self._try_flat(msg, self.pretty_primitive)
        if flat933 is not None:
            assert flat933 is not None
            self.write(flat933)
            return None
        else:
            def _t1480(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1481 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1481 = None
                return _t1481
            _t1482 = _t1480(msg)
            guard_result932 = _t1482
            if guard_result932 is not None:
                self.pretty_eq(msg)
            else:
                def _t1483(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_monotype":
                        _t1484 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1484 = None
                    return _t1484
                _t1485 = _t1483(msg)
                guard_result931 = _t1485
                if guard_result931 is not None:
                    self.pretty_lt(msg)
                else:
                    def _t1486(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                            _t1487 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1487 = None
                        return _t1487
                    _t1488 = _t1486(msg)
                    guard_result930 = _t1488
                    if guard_result930 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        def _t1489(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                                _t1490 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1490 = None
                            return _t1490
                        _t1491 = _t1489(msg)
                        guard_result929 = _t1491
                        if guard_result929 is not None:
                            self.pretty_gt(msg)
                        else:
                            def _t1492(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                    _t1493 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                                else:
                                    _t1493 = None
                                return _t1493
                            _t1494 = _t1492(msg)
                            guard_result928 = _t1494
                            if guard_result928 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                def _t1495(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_add_monotype":
                                        _t1496 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1496 = None
                                    return _t1496
                                _t1497 = _t1495(msg)
                                guard_result927 = _t1497
                                if guard_result927 is not None:
                                    self.pretty_add(msg)
                                else:
                                    def _t1498(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                            _t1499 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1499 = None
                                        return _t1499
                                    _t1500 = _t1498(msg)
                                    guard_result926 = _t1500
                                    if guard_result926 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        def _t1501(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                                _t1502 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1502 = None
                                            return _t1502
                                        _t1503 = _t1501(msg)
                                        guard_result925 = _t1503
                                        if guard_result925 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            def _t1504(_dollar_dollar):
                                                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                    _t1505 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                                else:
                                                    _t1505 = None
                                                return _t1505
                                            _t1506 = _t1504(msg)
                                            guard_result924 = _t1506
                                            if guard_result924 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                def _t1507(_dollar_dollar):
                                                    return (_dollar_dollar.name, _dollar_dollar.terms,)
                                                _t1508 = _t1507(msg)
                                                fields918 = _t1508
                                                assert fields918 is not None
                                                unwrapped_fields919 = fields918
                                                self.write("(")
                                                self.write("primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field920 = unwrapped_fields919[0]
                                                self.pretty_name(field920)
                                                field921 = unwrapped_fields919[1]
                                                if not len(field921) == 0:
                                                    self.newline()
                                                    for i923, elem922 in enumerate(field921):
                                                        if (i923 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem922)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat938 = self._try_flat(msg, self.pretty_eq)
        if flat938 is not None:
            assert flat938 is not None
            self.write(flat938)
            return None
        else:
            def _t1509(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1510 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1510 = None
                return _t1510
            _t1511 = _t1509(msg)
            fields934 = _t1511
            assert fields934 is not None
            unwrapped_fields935 = fields934
            self.write("(")
            self.write("=")
            self.indent_sexp()
            self.newline()
            field936 = unwrapped_fields935[0]
            self.pretty_term(field936)
            self.newline()
            field937 = unwrapped_fields935[1]
            self.pretty_term(field937)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat943 = self._try_flat(msg, self.pretty_lt)
        if flat943 is not None:
            assert flat943 is not None
            self.write(flat943)
            return None
        else:
            def _t1512(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1513 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1513 = None
                return _t1513
            _t1514 = _t1512(msg)
            fields939 = _t1514
            assert fields939 is not None
            unwrapped_fields940 = fields939
            self.write("(")
            self.write("<")
            self.indent_sexp()
            self.newline()
            field941 = unwrapped_fields940[0]
            self.pretty_term(field941)
            self.newline()
            field942 = unwrapped_fields940[1]
            self.pretty_term(field942)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat948 = self._try_flat(msg, self.pretty_lt_eq)
        if flat948 is not None:
            assert flat948 is not None
            self.write(flat948)
            return None
        else:
            def _t1515(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                    _t1516 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1516 = None
                return _t1516
            _t1517 = _t1515(msg)
            fields944 = _t1517
            assert fields944 is not None
            unwrapped_fields945 = fields944
            self.write("(")
            self.write("<=")
            self.indent_sexp()
            self.newline()
            field946 = unwrapped_fields945[0]
            self.pretty_term(field946)
            self.newline()
            field947 = unwrapped_fields945[1]
            self.pretty_term(field947)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat953 = self._try_flat(msg, self.pretty_gt)
        if flat953 is not None:
            assert flat953 is not None
            self.write(flat953)
            return None
        else:
            def _t1518(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_monotype":
                    _t1519 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1519 = None
                return _t1519
            _t1520 = _t1518(msg)
            fields949 = _t1520
            assert fields949 is not None
            unwrapped_fields950 = fields949
            self.write("(")
            self.write(">")
            self.indent_sexp()
            self.newline()
            field951 = unwrapped_fields950[0]
            self.pretty_term(field951)
            self.newline()
            field952 = unwrapped_fields950[1]
            self.pretty_term(field952)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat958 = self._try_flat(msg, self.pretty_gt_eq)
        if flat958 is not None:
            assert flat958 is not None
            self.write(flat958)
            return None
        else:
            def _t1521(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                    _t1522 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1522 = None
                return _t1522
            _t1523 = _t1521(msg)
            fields954 = _t1523
            assert fields954 is not None
            unwrapped_fields955 = fields954
            self.write("(")
            self.write(">=")
            self.indent_sexp()
            self.newline()
            field956 = unwrapped_fields955[0]
            self.pretty_term(field956)
            self.newline()
            field957 = unwrapped_fields955[1]
            self.pretty_term(field957)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat964 = self._try_flat(msg, self.pretty_add)
        if flat964 is not None:
            assert flat964 is not None
            self.write(flat964)
            return None
        else:
            def _t1524(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_add_monotype":
                    _t1525 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1525 = None
                return _t1525
            _t1526 = _t1524(msg)
            fields959 = _t1526
            assert fields959 is not None
            unwrapped_fields960 = fields959
            self.write("(")
            self.write("+")
            self.indent_sexp()
            self.newline()
            field961 = unwrapped_fields960[0]
            self.pretty_term(field961)
            self.newline()
            field962 = unwrapped_fields960[1]
            self.pretty_term(field962)
            self.newline()
            field963 = unwrapped_fields960[2]
            self.pretty_term(field963)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat970 = self._try_flat(msg, self.pretty_minus)
        if flat970 is not None:
            assert flat970 is not None
            self.write(flat970)
            return None
        else:
            def _t1527(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                    _t1528 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1528 = None
                return _t1528
            _t1529 = _t1527(msg)
            fields965 = _t1529
            assert fields965 is not None
            unwrapped_fields966 = fields965
            self.write("(")
            self.write("-")
            self.indent_sexp()
            self.newline()
            field967 = unwrapped_fields966[0]
            self.pretty_term(field967)
            self.newline()
            field968 = unwrapped_fields966[1]
            self.pretty_term(field968)
            self.newline()
            field969 = unwrapped_fields966[2]
            self.pretty_term(field969)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat976 = self._try_flat(msg, self.pretty_multiply)
        if flat976 is not None:
            assert flat976 is not None
            self.write(flat976)
            return None
        else:
            def _t1530(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                    _t1531 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1531 = None
                return _t1531
            _t1532 = _t1530(msg)
            fields971 = _t1532
            assert fields971 is not None
            unwrapped_fields972 = fields971
            self.write("(")
            self.write("*")
            self.indent_sexp()
            self.newline()
            field973 = unwrapped_fields972[0]
            self.pretty_term(field973)
            self.newline()
            field974 = unwrapped_fields972[1]
            self.pretty_term(field974)
            self.newline()
            field975 = unwrapped_fields972[2]
            self.pretty_term(field975)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat982 = self._try_flat(msg, self.pretty_divide)
        if flat982 is not None:
            assert flat982 is not None
            self.write(flat982)
            return None
        else:
            def _t1533(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                    _t1534 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1534 = None
                return _t1534
            _t1535 = _t1533(msg)
            fields977 = _t1535
            assert fields977 is not None
            unwrapped_fields978 = fields977
            self.write("(")
            self.write("/")
            self.indent_sexp()
            self.newline()
            field979 = unwrapped_fields978[0]
            self.pretty_term(field979)
            self.newline()
            field980 = unwrapped_fields978[1]
            self.pretty_term(field980)
            self.newline()
            field981 = unwrapped_fields978[2]
            self.pretty_term(field981)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat987 = self._try_flat(msg, self.pretty_rel_term)
        if flat987 is not None:
            assert flat987 is not None
            self.write(flat987)
            return None
        else:
            def _t1536(_dollar_dollar):
                if _dollar_dollar.HasField("specialized_value"):
                    _t1537 = _dollar_dollar.specialized_value
                else:
                    _t1537 = None
                return _t1537
            _t1538 = _t1536(msg)
            deconstruct_result985 = _t1538
            if deconstruct_result985 is not None:
                assert deconstruct_result985 is not None
                unwrapped986 = deconstruct_result985
                self.pretty_specialized_value(unwrapped986)
            else:
                def _t1539(_dollar_dollar):
                    if _dollar_dollar.HasField("term"):
                        _t1540 = _dollar_dollar.term
                    else:
                        _t1540 = None
                    return _t1540
                _t1541 = _t1539(msg)
                deconstruct_result983 = _t1541
                if deconstruct_result983 is not None:
                    assert deconstruct_result983 is not None
                    unwrapped984 = deconstruct_result983
                    self.pretty_term(unwrapped984)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat989 = self._try_flat(msg, self.pretty_specialized_value)
        if flat989 is not None:
            assert flat989 is not None
            self.write(flat989)
            return None
        else:
            fields988 = msg
            self.write("#")
            self.pretty_value(fields988)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat996 = self._try_flat(msg, self.pretty_rel_atom)
        if flat996 is not None:
            assert flat996 is not None
            self.write(flat996)
            return None
        else:
            def _t1542(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1543 = _t1542(msg)
            fields990 = _t1543
            assert fields990 is not None
            unwrapped_fields991 = fields990
            self.write("(")
            self.write("relatom")
            self.indent_sexp()
            self.newline()
            field992 = unwrapped_fields991[0]
            self.pretty_name(field992)
            field993 = unwrapped_fields991[1]
            if not len(field993) == 0:
                self.newline()
                for i995, elem994 in enumerate(field993):
                    if (i995 > 0):
                        self.newline()
                    self.pretty_rel_term(elem994)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1001 = self._try_flat(msg, self.pretty_cast)
        if flat1001 is not None:
            assert flat1001 is not None
            self.write(flat1001)
            return None
        else:
            def _t1544(_dollar_dollar):
                return (_dollar_dollar.input, _dollar_dollar.result,)
            _t1545 = _t1544(msg)
            fields997 = _t1545
            assert fields997 is not None
            unwrapped_fields998 = fields997
            self.write("(")
            self.write("cast")
            self.indent_sexp()
            self.newline()
            field999 = unwrapped_fields998[0]
            self.pretty_term(field999)
            self.newline()
            field1000 = unwrapped_fields998[1]
            self.pretty_term(field1000)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1005 = self._try_flat(msg, self.pretty_attrs)
        if flat1005 is not None:
            assert flat1005 is not None
            self.write(flat1005)
            return None
        else:
            fields1002 = msg
            self.write("(")
            self.write("attrs")
            self.indent_sexp()
            if not len(fields1002) == 0:
                self.newline()
                for i1004, elem1003 in enumerate(fields1002):
                    if (i1004 > 0):
                        self.newline()
                    self.pretty_attribute(elem1003)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1012 = self._try_flat(msg, self.pretty_attribute)
        if flat1012 is not None:
            assert flat1012 is not None
            self.write(flat1012)
            return None
        else:
            def _t1546(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args,)
            _t1547 = _t1546(msg)
            fields1006 = _t1547
            assert fields1006 is not None
            unwrapped_fields1007 = fields1006
            self.write("(")
            self.write("attribute")
            self.indent_sexp()
            self.newline()
            field1008 = unwrapped_fields1007[0]
            self.pretty_name(field1008)
            field1009 = unwrapped_fields1007[1]
            if not len(field1009) == 0:
                self.newline()
                for i1011, elem1010 in enumerate(field1009):
                    if (i1011 > 0):
                        self.newline()
                    self.pretty_value(elem1010)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1019 = self._try_flat(msg, self.pretty_algorithm)
        if flat1019 is not None:
            assert flat1019 is not None
            self.write(flat1019)
            return None
        else:
            def _t1548(_dollar_dollar):
                return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            _t1549 = _t1548(msg)
            fields1013 = _t1549
            assert fields1013 is not None
            unwrapped_fields1014 = fields1013
            self.write("(")
            self.write("algorithm")
            self.indent_sexp()
            field1015 = unwrapped_fields1014[0]
            if not len(field1015) == 0:
                self.newline()
                for i1017, elem1016 in enumerate(field1015):
                    if (i1017 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1016)
            self.newline()
            field1018 = unwrapped_fields1014[1]
            self.pretty_script(field1018)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1024 = self._try_flat(msg, self.pretty_script)
        if flat1024 is not None:
            assert flat1024 is not None
            self.write(flat1024)
            return None
        else:
            def _t1550(_dollar_dollar):
                return _dollar_dollar.constructs
            _t1551 = _t1550(msg)
            fields1020 = _t1551
            assert fields1020 is not None
            unwrapped_fields1021 = fields1020
            self.write("(")
            self.write("script")
            self.indent_sexp()
            if not len(unwrapped_fields1021) == 0:
                self.newline()
                for i1023, elem1022 in enumerate(unwrapped_fields1021):
                    if (i1023 > 0):
                        self.newline()
                    self.pretty_construct(elem1022)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1029 = self._try_flat(msg, self.pretty_construct)
        if flat1029 is not None:
            assert flat1029 is not None
            self.write(flat1029)
            return None
        else:
            def _t1552(_dollar_dollar):
                if _dollar_dollar.HasField("loop"):
                    _t1553 = _dollar_dollar.loop
                else:
                    _t1553 = None
                return _t1553
            _t1554 = _t1552(msg)
            deconstruct_result1027 = _t1554
            if deconstruct_result1027 is not None:
                assert deconstruct_result1027 is not None
                unwrapped1028 = deconstruct_result1027
                self.pretty_loop(unwrapped1028)
            else:
                def _t1555(_dollar_dollar):
                    if _dollar_dollar.HasField("instruction"):
                        _t1556 = _dollar_dollar.instruction
                    else:
                        _t1556 = None
                    return _t1556
                _t1557 = _t1555(msg)
                deconstruct_result1025 = _t1557
                if deconstruct_result1025 is not None:
                    assert deconstruct_result1025 is not None
                    unwrapped1026 = deconstruct_result1025
                    self.pretty_instruction(unwrapped1026)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1034 = self._try_flat(msg, self.pretty_loop)
        if flat1034 is not None:
            assert flat1034 is not None
            self.write(flat1034)
            return None
        else:
            def _t1558(_dollar_dollar):
                return (_dollar_dollar.init, _dollar_dollar.body,)
            _t1559 = _t1558(msg)
            fields1030 = _t1559
            assert fields1030 is not None
            unwrapped_fields1031 = fields1030
            self.write("(")
            self.write("loop")
            self.indent_sexp()
            self.newline()
            field1032 = unwrapped_fields1031[0]
            self.pretty_init(field1032)
            self.newline()
            field1033 = unwrapped_fields1031[1]
            self.pretty_script(field1033)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1038 = self._try_flat(msg, self.pretty_init)
        if flat1038 is not None:
            assert flat1038 is not None
            self.write(flat1038)
            return None
        else:
            fields1035 = msg
            self.write("(")
            self.write("init")
            self.indent_sexp()
            if not len(fields1035) == 0:
                self.newline()
                for i1037, elem1036 in enumerate(fields1035):
                    if (i1037 > 0):
                        self.newline()
                    self.pretty_instruction(elem1036)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1049 = self._try_flat(msg, self.pretty_instruction)
        if flat1049 is not None:
            assert flat1049 is not None
            self.write(flat1049)
            return None
        else:
            def _t1560(_dollar_dollar):
                if _dollar_dollar.HasField("assign"):
                    _t1561 = _dollar_dollar.assign
                else:
                    _t1561 = None
                return _t1561
            _t1562 = _t1560(msg)
            deconstruct_result1047 = _t1562
            if deconstruct_result1047 is not None:
                assert deconstruct_result1047 is not None
                unwrapped1048 = deconstruct_result1047
                self.pretty_assign(unwrapped1048)
            else:
                def _t1563(_dollar_dollar):
                    if _dollar_dollar.HasField("upsert"):
                        _t1564 = _dollar_dollar.upsert
                    else:
                        _t1564 = None
                    return _t1564
                _t1565 = _t1563(msg)
                deconstruct_result1045 = _t1565
                if deconstruct_result1045 is not None:
                    assert deconstruct_result1045 is not None
                    unwrapped1046 = deconstruct_result1045
                    self.pretty_upsert(unwrapped1046)
                else:
                    def _t1566(_dollar_dollar):
                        if _dollar_dollar.HasField("break"):
                            _t1567 = getattr(_dollar_dollar, 'break')
                        else:
                            _t1567 = None
                        return _t1567
                    _t1568 = _t1566(msg)
                    deconstruct_result1043 = _t1568
                    if deconstruct_result1043 is not None:
                        assert deconstruct_result1043 is not None
                        unwrapped1044 = deconstruct_result1043
                        self.pretty_break(unwrapped1044)
                    else:
                        def _t1569(_dollar_dollar):
                            if _dollar_dollar.HasField("monoid_def"):
                                _t1570 = _dollar_dollar.monoid_def
                            else:
                                _t1570 = None
                            return _t1570
                        _t1571 = _t1569(msg)
                        deconstruct_result1041 = _t1571
                        if deconstruct_result1041 is not None:
                            assert deconstruct_result1041 is not None
                            unwrapped1042 = deconstruct_result1041
                            self.pretty_monoid_def(unwrapped1042)
                        else:
                            def _t1572(_dollar_dollar):
                                if _dollar_dollar.HasField("monus_def"):
                                    _t1573 = _dollar_dollar.monus_def
                                else:
                                    _t1573 = None
                                return _t1573
                            _t1574 = _t1572(msg)
                            deconstruct_result1039 = _t1574
                            if deconstruct_result1039 is not None:
                                assert deconstruct_result1039 is not None
                                unwrapped1040 = deconstruct_result1039
                                self.pretty_monus_def(unwrapped1040)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1056 = self._try_flat(msg, self.pretty_assign)
        if flat1056 is not None:
            assert flat1056 is not None
            self.write(flat1056)
            return None
        else:
            def _t1575(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1576 = _dollar_dollar.attrs
                else:
                    _t1576 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1576,)
            _t1577 = _t1575(msg)
            fields1050 = _t1577
            assert fields1050 is not None
            unwrapped_fields1051 = fields1050
            self.write("(")
            self.write("assign")
            self.indent_sexp()
            self.newline()
            field1052 = unwrapped_fields1051[0]
            self.pretty_relation_id(field1052)
            self.newline()
            field1053 = unwrapped_fields1051[1]
            self.pretty_abstraction(field1053)
            field1054 = unwrapped_fields1051[2]
            if field1054 is not None:
                self.newline()
                assert field1054 is not None
                opt_val1055 = field1054
                self.pretty_attrs(opt_val1055)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1063 = self._try_flat(msg, self.pretty_upsert)
        if flat1063 is not None:
            assert flat1063 is not None
            self.write(flat1063)
            return None
        else:
            def _t1578(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1579 = _dollar_dollar.attrs
                else:
                    _t1579 = None
                return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1579,)
            _t1580 = _t1578(msg)
            fields1057 = _t1580
            assert fields1057 is not None
            unwrapped_fields1058 = fields1057
            self.write("(")
            self.write("upsert")
            self.indent_sexp()
            self.newline()
            field1059 = unwrapped_fields1058[0]
            self.pretty_relation_id(field1059)
            self.newline()
            field1060 = unwrapped_fields1058[1]
            self.pretty_abstraction_with_arity(field1060)
            field1061 = unwrapped_fields1058[2]
            if field1061 is not None:
                self.newline()
                assert field1061 is not None
                opt_val1062 = field1061
                self.pretty_attrs(opt_val1062)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1068 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1068 is not None:
            assert flat1068 is not None
            self.write(flat1068)
            return None
        else:
            def _t1581(_dollar_dollar):
                _t1582 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
                return (_t1582, _dollar_dollar[0].value,)
            _t1583 = _t1581(msg)
            fields1064 = _t1583
            assert fields1064 is not None
            unwrapped_fields1065 = fields1064
            self.write("(")
            self.indent()
            field1066 = unwrapped_fields1065[0]
            self.pretty_bindings(field1066)
            self.newline()
            field1067 = unwrapped_fields1065[1]
            self.pretty_formula(field1067)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1075 = self._try_flat(msg, self.pretty_break)
        if flat1075 is not None:
            assert flat1075 is not None
            self.write(flat1075)
            return None
        else:
            def _t1584(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1585 = _dollar_dollar.attrs
                else:
                    _t1585 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1585,)
            _t1586 = _t1584(msg)
            fields1069 = _t1586
            assert fields1069 is not None
            unwrapped_fields1070 = fields1069
            self.write("(")
            self.write("break")
            self.indent_sexp()
            self.newline()
            field1071 = unwrapped_fields1070[0]
            self.pretty_relation_id(field1071)
            self.newline()
            field1072 = unwrapped_fields1070[1]
            self.pretty_abstraction(field1072)
            field1073 = unwrapped_fields1070[2]
            if field1073 is not None:
                self.newline()
                assert field1073 is not None
                opt_val1074 = field1073
                self.pretty_attrs(opt_val1074)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1083 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1083 is not None:
            assert flat1083 is not None
            self.write(flat1083)
            return None
        else:
            def _t1587(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1588 = _dollar_dollar.attrs
                else:
                    _t1588 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1588,)
            _t1589 = _t1587(msg)
            fields1076 = _t1589
            assert fields1076 is not None
            unwrapped_fields1077 = fields1076
            self.write("(")
            self.write("monoid")
            self.indent_sexp()
            self.newline()
            field1078 = unwrapped_fields1077[0]
            self.pretty_monoid(field1078)
            self.newline()
            field1079 = unwrapped_fields1077[1]
            self.pretty_relation_id(field1079)
            self.newline()
            field1080 = unwrapped_fields1077[2]
            self.pretty_abstraction_with_arity(field1080)
            field1081 = unwrapped_fields1077[3]
            if field1081 is not None:
                self.newline()
                assert field1081 is not None
                opt_val1082 = field1081
                self.pretty_attrs(opt_val1082)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1092 = self._try_flat(msg, self.pretty_monoid)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            def _t1590(_dollar_dollar):
                if _dollar_dollar.HasField("or_monoid"):
                    _t1591 = _dollar_dollar.or_monoid
                else:
                    _t1591 = None
                return _t1591
            _t1592 = _t1590(msg)
            deconstruct_result1090 = _t1592
            if deconstruct_result1090 is not None:
                assert deconstruct_result1090 is not None
                unwrapped1091 = deconstruct_result1090
                self.pretty_or_monoid(unwrapped1091)
            else:
                def _t1593(_dollar_dollar):
                    if _dollar_dollar.HasField("min_monoid"):
                        _t1594 = _dollar_dollar.min_monoid
                    else:
                        _t1594 = None
                    return _t1594
                _t1595 = _t1593(msg)
                deconstruct_result1088 = _t1595
                if deconstruct_result1088 is not None:
                    assert deconstruct_result1088 is not None
                    unwrapped1089 = deconstruct_result1088
                    self.pretty_min_monoid(unwrapped1089)
                else:
                    def _t1596(_dollar_dollar):
                        if _dollar_dollar.HasField("max_monoid"):
                            _t1597 = _dollar_dollar.max_monoid
                        else:
                            _t1597 = None
                        return _t1597
                    _t1598 = _t1596(msg)
                    deconstruct_result1086 = _t1598
                    if deconstruct_result1086 is not None:
                        assert deconstruct_result1086 is not None
                        unwrapped1087 = deconstruct_result1086
                        self.pretty_max_monoid(unwrapped1087)
                    else:
                        def _t1599(_dollar_dollar):
                            if _dollar_dollar.HasField("sum_monoid"):
                                _t1600 = _dollar_dollar.sum_monoid
                            else:
                                _t1600 = None
                            return _t1600
                        _t1601 = _t1599(msg)
                        deconstruct_result1084 = _t1601
                        if deconstruct_result1084 is not None:
                            assert deconstruct_result1084 is not None
                            unwrapped1085 = deconstruct_result1084
                            self.pretty_sum_monoid(unwrapped1085)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1093 = msg
        self.write("(")
        self.write("or")
        self.write(")")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1096 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            def _t1602(_dollar_dollar):
                return _dollar_dollar.type
            _t1603 = _t1602(msg)
            fields1094 = _t1603
            assert fields1094 is not None
            unwrapped_fields1095 = fields1094
            self.write("(")
            self.write("min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1095)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1099 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1099 is not None:
            assert flat1099 is not None
            self.write(flat1099)
            return None
        else:
            def _t1604(_dollar_dollar):
                return _dollar_dollar.type
            _t1605 = _t1604(msg)
            fields1097 = _t1605
            assert fields1097 is not None
            unwrapped_fields1098 = fields1097
            self.write("(")
            self.write("max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1098)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1102 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1102 is not None:
            assert flat1102 is not None
            self.write(flat1102)
            return None
        else:
            def _t1606(_dollar_dollar):
                return _dollar_dollar.type
            _t1607 = _t1606(msg)
            fields1100 = _t1607
            assert fields1100 is not None
            unwrapped_fields1101 = fields1100
            self.write("(")
            self.write("sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1101)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1110 = self._try_flat(msg, self.pretty_monus_def)
        if flat1110 is not None:
            assert flat1110 is not None
            self.write(flat1110)
            return None
        else:
            def _t1608(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1609 = _dollar_dollar.attrs
                else:
                    _t1609 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1609,)
            _t1610 = _t1608(msg)
            fields1103 = _t1610
            assert fields1103 is not None
            unwrapped_fields1104 = fields1103
            self.write("(")
            self.write("monus")
            self.indent_sexp()
            self.newline()
            field1105 = unwrapped_fields1104[0]
            self.pretty_monoid(field1105)
            self.newline()
            field1106 = unwrapped_fields1104[1]
            self.pretty_relation_id(field1106)
            self.newline()
            field1107 = unwrapped_fields1104[2]
            self.pretty_abstraction_with_arity(field1107)
            field1108 = unwrapped_fields1104[3]
            if field1108 is not None:
                self.newline()
                assert field1108 is not None
                opt_val1109 = field1108
                self.pretty_attrs(opt_val1109)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1117 = self._try_flat(msg, self.pretty_constraint)
        if flat1117 is not None:
            assert flat1117 is not None
            self.write(flat1117)
            return None
        else:
            def _t1611(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            _t1612 = _t1611(msg)
            fields1111 = _t1612
            assert fields1111 is not None
            unwrapped_fields1112 = fields1111
            self.write("(")
            self.write("functional_dependency")
            self.indent_sexp()
            self.newline()
            field1113 = unwrapped_fields1112[0]
            self.pretty_relation_id(field1113)
            self.newline()
            field1114 = unwrapped_fields1112[1]
            self.pretty_abstraction(field1114)
            self.newline()
            field1115 = unwrapped_fields1112[2]
            self.pretty_functional_dependency_keys(field1115)
            self.newline()
            field1116 = unwrapped_fields1112[3]
            self.pretty_functional_dependency_values(field1116)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1121 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1121 is not None:
            assert flat1121 is not None
            self.write(flat1121)
            return None
        else:
            fields1118 = msg
            self.write("(")
            self.write("keys")
            self.indent_sexp()
            if not len(fields1118) == 0:
                self.newline()
                for i1120, elem1119 in enumerate(fields1118):
                    if (i1120 > 0):
                        self.newline()
                    self.pretty_var(elem1119)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1125 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1125 is not None:
            assert flat1125 is not None
            self.write(flat1125)
            return None
        else:
            fields1122 = msg
            self.write("(")
            self.write("values")
            self.indent_sexp()
            if not len(fields1122) == 0:
                self.newline()
                for i1124, elem1123 in enumerate(fields1122):
                    if (i1124 > 0):
                        self.newline()
                    self.pretty_var(elem1123)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1132 = self._try_flat(msg, self.pretty_data)
        if flat1132 is not None:
            assert flat1132 is not None
            self.write(flat1132)
            return None
        else:
            def _t1613(_dollar_dollar):
                if _dollar_dollar.HasField("rel_edb"):
                    _t1614 = _dollar_dollar.rel_edb
                else:
                    _t1614 = None
                return _t1614
            _t1615 = _t1613(msg)
            deconstruct_result1130 = _t1615
            if deconstruct_result1130 is not None:
                assert deconstruct_result1130 is not None
                unwrapped1131 = deconstruct_result1130
                self.pretty_rel_edb(unwrapped1131)
            else:
                def _t1616(_dollar_dollar):
                    if _dollar_dollar.HasField("betree_relation"):
                        _t1617 = _dollar_dollar.betree_relation
                    else:
                        _t1617 = None
                    return _t1617
                _t1618 = _t1616(msg)
                deconstruct_result1128 = _t1618
                if deconstruct_result1128 is not None:
                    assert deconstruct_result1128 is not None
                    unwrapped1129 = deconstruct_result1128
                    self.pretty_betree_relation(unwrapped1129)
                else:
                    def _t1619(_dollar_dollar):
                        if _dollar_dollar.HasField("csv_data"):
                            _t1620 = _dollar_dollar.csv_data
                        else:
                            _t1620 = None
                        return _t1620
                    _t1621 = _t1619(msg)
                    deconstruct_result1126 = _t1621
                    if deconstruct_result1126 is not None:
                        assert deconstruct_result1126 is not None
                        unwrapped1127 = deconstruct_result1126
                        self.pretty_csv_data(unwrapped1127)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB):
        flat1138 = self._try_flat(msg, self.pretty_rel_edb)
        if flat1138 is not None:
            assert flat1138 is not None
            self.write(flat1138)
            return None
        else:
            def _t1622(_dollar_dollar):
                return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            _t1623 = _t1622(msg)
            fields1133 = _t1623
            assert fields1133 is not None
            unwrapped_fields1134 = fields1133
            self.write("(")
            self.write("rel_edb")
            self.indent_sexp()
            self.newline()
            field1135 = unwrapped_fields1134[0]
            self.pretty_relation_id(field1135)
            self.newline()
            field1136 = unwrapped_fields1134[1]
            self.pretty_rel_edb_path(field1136)
            self.newline()
            field1137 = unwrapped_fields1134[2]
            self.pretty_rel_edb_types(field1137)
            self.dedent()
            self.write(")")

    def pretty_rel_edb_path(self, msg: Sequence[str]):
        flat1142 = self._try_flat(msg, self.pretty_rel_edb_path)
        if flat1142 is not None:
            assert flat1142 is not None
            self.write(flat1142)
            return None
        else:
            fields1139 = msg
            self.write("[")
            self.indent()
            for i1141, elem1140 in enumerate(fields1139):
                if (i1141 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1140))
            self.dedent()
            self.write("]")

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1146 = self._try_flat(msg, self.pretty_rel_edb_types)
        if flat1146 is not None:
            assert flat1146 is not None
            self.write(flat1146)
            return None
        else:
            fields1143 = msg
            self.write("[")
            self.indent()
            for i1145, elem1144 in enumerate(fields1143):
                if (i1145 > 0):
                    self.newline()
                self.pretty_type(elem1144)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1151 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1151 is not None:
            assert flat1151 is not None
            self.write(flat1151)
            return None
        else:
            def _t1624(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_info,)
            _t1625 = _t1624(msg)
            fields1147 = _t1625
            assert fields1147 is not None
            unwrapped_fields1148 = fields1147
            self.write("(")
            self.write("betree_relation")
            self.indent_sexp()
            self.newline()
            field1149 = unwrapped_fields1148[0]
            self.pretty_relation_id(field1149)
            self.newline()
            field1150 = unwrapped_fields1148[1]
            self.pretty_betree_info(field1150)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1157 = self._try_flat(msg, self.pretty_betree_info)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            def _t1626(_dollar_dollar):
                _t1627 = self.deconstruct_betree_info_config(_dollar_dollar)
                return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1627,)
            _t1628 = _t1626(msg)
            fields1152 = _t1628
            assert fields1152 is not None
            unwrapped_fields1153 = fields1152
            self.write("(")
            self.write("betree_info")
            self.indent_sexp()
            self.newline()
            field1154 = unwrapped_fields1153[0]
            self.pretty_betree_info_key_types(field1154)
            self.newline()
            field1155 = unwrapped_fields1153[1]
            self.pretty_betree_info_value_types(field1155)
            self.newline()
            field1156 = unwrapped_fields1153[2]
            self.pretty_config_dict(field1156)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1161 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1161 is not None:
            assert flat1161 is not None
            self.write(flat1161)
            return None
        else:
            fields1158 = msg
            self.write("(")
            self.write("key_types")
            self.indent_sexp()
            if not len(fields1158) == 0:
                self.newline()
                for i1160, elem1159 in enumerate(fields1158):
                    if (i1160 > 0):
                        self.newline()
                    self.pretty_type(elem1159)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1165 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1165 is not None:
            assert flat1165 is not None
            self.write(flat1165)
            return None
        else:
            fields1162 = msg
            self.write("(")
            self.write("value_types")
            self.indent_sexp()
            if not len(fields1162) == 0:
                self.newline()
                for i1164, elem1163 in enumerate(fields1162):
                    if (i1164 > 0):
                        self.newline()
                    self.pretty_type(elem1163)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1172 = self._try_flat(msg, self.pretty_csv_data)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            def _t1629(_dollar_dollar):
                return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            _t1630 = _t1629(msg)
            fields1166 = _t1630
            assert fields1166 is not None
            unwrapped_fields1167 = fields1166
            self.write("(")
            self.write("csv_data")
            self.indent_sexp()
            self.newline()
            field1168 = unwrapped_fields1167[0]
            self.pretty_csvlocator(field1168)
            self.newline()
            field1169 = unwrapped_fields1167[1]
            self.pretty_csv_config(field1169)
            self.newline()
            field1170 = unwrapped_fields1167[2]
            self.pretty_csv_columns(field1170)
            self.newline()
            field1171 = unwrapped_fields1167[3]
            self.pretty_csv_asof(field1171)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1179 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            def _t1631(_dollar_dollar):
                if not len(_dollar_dollar.paths) == 0:
                    _t1632 = _dollar_dollar.paths
                else:
                    _t1632 = None
                if _dollar_dollar.inline_data.decode('utf-8') != "":
                    _t1633 = _dollar_dollar.inline_data.decode('utf-8')
                else:
                    _t1633 = None
                return (_t1632, _t1633,)
            _t1634 = _t1631(msg)
            fields1173 = _t1634
            assert fields1173 is not None
            unwrapped_fields1174 = fields1173
            self.write("(")
            self.write("csv_locator")
            self.indent_sexp()
            field1175 = unwrapped_fields1174[0]
            if field1175 is not None:
                self.newline()
                assert field1175 is not None
                opt_val1176 = field1175
                self.pretty_csv_locator_paths(opt_val1176)
            field1177 = unwrapped_fields1174[1]
            if field1177 is not None:
                self.newline()
                assert field1177 is not None
                opt_val1178 = field1177
                self.pretty_csv_locator_inline_data(opt_val1178)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1183 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1183 is not None:
            assert flat1183 is not None
            self.write(flat1183)
            return None
        else:
            fields1180 = msg
            self.write("(")
            self.write("paths")
            self.indent_sexp()
            if not len(fields1180) == 0:
                self.newline()
                for i1182, elem1181 in enumerate(fields1180):
                    if (i1182 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1181))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1185 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1185 is not None:
            assert flat1185 is not None
            self.write(flat1185)
            return None
        else:
            fields1184 = msg
            self.write("(")
            self.write("inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1184))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1188 = self._try_flat(msg, self.pretty_csv_config)
        if flat1188 is not None:
            assert flat1188 is not None
            self.write(flat1188)
            return None
        else:
            def _t1635(_dollar_dollar):
                _t1636 = self.deconstruct_csv_config(_dollar_dollar)
                return _t1636
            _t1637 = _t1635(msg)
            fields1186 = _t1637
            assert fields1186 is not None
            unwrapped_fields1187 = fields1186
            self.write("(")
            self.write("csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1187)
            self.dedent()
            self.write(")")

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]):
        flat1192 = self._try_flat(msg, self.pretty_csv_columns)
        if flat1192 is not None:
            assert flat1192 is not None
            self.write(flat1192)
            return None
        else:
            fields1189 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1189) == 0:
                self.newline()
                for i1191, elem1190 in enumerate(fields1189):
                    if (i1191 > 0):
                        self.newline()
                    self.pretty_csv_column(elem1190)
            self.dedent()
            self.write(")")

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn):
        flat1200 = self._try_flat(msg, self.pretty_csv_column)
        if flat1200 is not None:
            assert flat1200 is not None
            self.write(flat1200)
            return None
        else:
            def _t1638(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
            _t1639 = _t1638(msg)
            fields1193 = _t1639
            assert fields1193 is not None
            unwrapped_fields1194 = fields1193
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1195 = unwrapped_fields1194[0]
            self.write(self.format_string_value(field1195))
            self.newline()
            field1196 = unwrapped_fields1194[1]
            self.pretty_relation_id(field1196)
            self.newline()
            self.write("[")
            field1197 = unwrapped_fields1194[2]
            for i1199, elem1198 in enumerate(field1197):
                if (i1199 > 0):
                    self.newline()
                self.pretty_type(elem1198)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1202 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1202 is not None:
            assert flat1202 is not None
            self.write(flat1202)
            return None
        else:
            fields1201 = msg
            self.write("(")
            self.write("asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1201))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1205 = self._try_flat(msg, self.pretty_undefine)
        if flat1205 is not None:
            assert flat1205 is not None
            self.write(flat1205)
            return None
        else:
            def _t1640(_dollar_dollar):
                return _dollar_dollar.fragment_id
            _t1641 = _t1640(msg)
            fields1203 = _t1641
            assert fields1203 is not None
            unwrapped_fields1204 = fields1203
            self.write("(")
            self.write("undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1204)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1210 = self._try_flat(msg, self.pretty_context)
        if flat1210 is not None:
            assert flat1210 is not None
            self.write(flat1210)
            return None
        else:
            def _t1642(_dollar_dollar):
                return _dollar_dollar.relations
            _t1643 = _t1642(msg)
            fields1206 = _t1643
            assert fields1206 is not None
            unwrapped_fields1207 = fields1206
            self.write("(")
            self.write("context")
            self.indent_sexp()
            if not len(unwrapped_fields1207) == 0:
                self.newline()
                for i1209, elem1208 in enumerate(unwrapped_fields1207):
                    if (i1209 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1208)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1215 = self._try_flat(msg, self.pretty_snapshot)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            def _t1644(_dollar_dollar):
                return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            _t1645 = _t1644(msg)
            fields1211 = _t1645
            assert fields1211 is not None
            unwrapped_fields1212 = fields1211
            self.write("(")
            self.write("snapshot")
            self.indent_sexp()
            self.newline()
            field1213 = unwrapped_fields1212[0]
            self.pretty_rel_edb_path(field1213)
            self.newline()
            field1214 = unwrapped_fields1212[1]
            self.pretty_relation_id(field1214)
            self.dedent()
            self.write(")")

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1219 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1219 is not None:
            assert flat1219 is not None
            self.write(flat1219)
            return None
        else:
            fields1216 = msg
            self.write("(")
            self.write("reads")
            self.indent_sexp()
            if not len(fields1216) == 0:
                self.newline()
                for i1218, elem1217 in enumerate(fields1216):
                    if (i1218 > 0):
                        self.newline()
                    self.pretty_read(elem1217)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1230 = self._try_flat(msg, self.pretty_read)
        if flat1230 is not None:
            assert flat1230 is not None
            self.write(flat1230)
            return None
        else:
            def _t1646(_dollar_dollar):
                if _dollar_dollar.HasField("demand"):
                    _t1647 = _dollar_dollar.demand
                else:
                    _t1647 = None
                return _t1647
            _t1648 = _t1646(msg)
            deconstruct_result1228 = _t1648
            if deconstruct_result1228 is not None:
                assert deconstruct_result1228 is not None
                unwrapped1229 = deconstruct_result1228
                self.pretty_demand(unwrapped1229)
            else:
                def _t1649(_dollar_dollar):
                    if _dollar_dollar.HasField("output"):
                        _t1650 = _dollar_dollar.output
                    else:
                        _t1650 = None
                    return _t1650
                _t1651 = _t1649(msg)
                deconstruct_result1226 = _t1651
                if deconstruct_result1226 is not None:
                    assert deconstruct_result1226 is not None
                    unwrapped1227 = deconstruct_result1226
                    self.pretty_output(unwrapped1227)
                else:
                    def _t1652(_dollar_dollar):
                        if _dollar_dollar.HasField("what_if"):
                            _t1653 = _dollar_dollar.what_if
                        else:
                            _t1653 = None
                        return _t1653
                    _t1654 = _t1652(msg)
                    deconstruct_result1224 = _t1654
                    if deconstruct_result1224 is not None:
                        assert deconstruct_result1224 is not None
                        unwrapped1225 = deconstruct_result1224
                        self.pretty_what_if(unwrapped1225)
                    else:
                        def _t1655(_dollar_dollar):
                            if _dollar_dollar.HasField("abort"):
                                _t1656 = _dollar_dollar.abort
                            else:
                                _t1656 = None
                            return _t1656
                        _t1657 = _t1655(msg)
                        deconstruct_result1222 = _t1657
                        if deconstruct_result1222 is not None:
                            assert deconstruct_result1222 is not None
                            unwrapped1223 = deconstruct_result1222
                            self.pretty_abort(unwrapped1223)
                        else:
                            def _t1658(_dollar_dollar):
                                if _dollar_dollar.HasField("export"):
                                    _t1659 = _dollar_dollar.export
                                else:
                                    _t1659 = None
                                return _t1659
                            _t1660 = _t1658(msg)
                            deconstruct_result1220 = _t1660
                            if deconstruct_result1220 is not None:
                                assert deconstruct_result1220 is not None
                                unwrapped1221 = deconstruct_result1220
                                self.pretty_export(unwrapped1221)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1233 = self._try_flat(msg, self.pretty_demand)
        if flat1233 is not None:
            assert flat1233 is not None
            self.write(flat1233)
            return None
        else:
            def _t1661(_dollar_dollar):
                return _dollar_dollar.relation_id
            _t1662 = _t1661(msg)
            fields1231 = _t1662
            assert fields1231 is not None
            unwrapped_fields1232 = fields1231
            self.write("(")
            self.write("demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1232)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1238 = self._try_flat(msg, self.pretty_output)
        if flat1238 is not None:
            assert flat1238 is not None
            self.write(flat1238)
            return None
        else:
            def _t1663(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_id,)
            _t1664 = _t1663(msg)
            fields1234 = _t1664
            assert fields1234 is not None
            unwrapped_fields1235 = fields1234
            self.write("(")
            self.write("output")
            self.indent_sexp()
            self.newline()
            field1236 = unwrapped_fields1235[0]
            self.pretty_name(field1236)
            self.newline()
            field1237 = unwrapped_fields1235[1]
            self.pretty_relation_id(field1237)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1243 = self._try_flat(msg, self.pretty_what_if)
        if flat1243 is not None:
            assert flat1243 is not None
            self.write(flat1243)
            return None
        else:
            def _t1665(_dollar_dollar):
                return (_dollar_dollar.branch, _dollar_dollar.epoch,)
            _t1666 = _t1665(msg)
            fields1239 = _t1666
            assert fields1239 is not None
            unwrapped_fields1240 = fields1239
            self.write("(")
            self.write("what_if")
            self.indent_sexp()
            self.newline()
            field1241 = unwrapped_fields1240[0]
            self.pretty_name(field1241)
            self.newline()
            field1242 = unwrapped_fields1240[1]
            self.pretty_epoch(field1242)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1249 = self._try_flat(msg, self.pretty_abort)
        if flat1249 is not None:
            assert flat1249 is not None
            self.write(flat1249)
            return None
        else:
            def _t1667(_dollar_dollar):
                if _dollar_dollar.name != "abort":
                    _t1668 = _dollar_dollar.name
                else:
                    _t1668 = None
                return (_t1668, _dollar_dollar.relation_id,)
            _t1669 = _t1667(msg)
            fields1244 = _t1669
            assert fields1244 is not None
            unwrapped_fields1245 = fields1244
            self.write("(")
            self.write("abort")
            self.indent_sexp()
            field1246 = unwrapped_fields1245[0]
            if field1246 is not None:
                self.newline()
                assert field1246 is not None
                opt_val1247 = field1246
                self.pretty_name(opt_val1247)
            self.newline()
            field1248 = unwrapped_fields1245[1]
            self.pretty_relation_id(field1248)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1252 = self._try_flat(msg, self.pretty_export)
        if flat1252 is not None:
            assert flat1252 is not None
            self.write(flat1252)
            return None
        else:
            def _t1670(_dollar_dollar):
                return _dollar_dollar.csv_config
            _t1671 = _t1670(msg)
            fields1250 = _t1671
            assert fields1250 is not None
            unwrapped_fields1251 = fields1250
            self.write("(")
            self.write("export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1251)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1263 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1263 is not None:
            assert flat1263 is not None
            self.write(flat1263)
            return None
        else:
            def _t1672(_dollar_dollar):
                if len(_dollar_dollar.data_columns) == 0:
                    _t1673 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
                else:
                    _t1673 = None
                return _t1673
            _t1674 = _t1672(msg)
            deconstruct_result1258 = _t1674
            if deconstruct_result1258 is not None:
                assert deconstruct_result1258 is not None
                unwrapped1259 = deconstruct_result1258
                self.write("(")
                self.write("export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1260 = unwrapped1259[0]
                self.pretty_export_csv_path(field1260)
                self.newline()
                field1261 = unwrapped1259[1]
                self.pretty_export_csv_source(field1261)
                self.newline()
                field1262 = unwrapped1259[2]
                self.pretty_csv_config(field1262)
                self.dedent()
                self.write(")")
            else:
                def _t1675(_dollar_dollar):
                    if len(_dollar_dollar.data_columns) != 0:
                        _t1677 = self.deconstruct_export_csv_config(_dollar_dollar)
                        _t1676 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1677,)
                    else:
                        _t1676 = None
                    return _t1676
                _t1678 = _t1675(msg)
                deconstruct_result1253 = _t1678
                if deconstruct_result1253 is not None:
                    assert deconstruct_result1253 is not None
                    unwrapped1254 = deconstruct_result1253
                    self.write("(")
                    self.write("export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1255 = unwrapped1254[0]
                    self.pretty_export_csv_path(field1255)
                    self.newline()
                    field1256 = unwrapped1254[1]
                    self.pretty_export_csv_columns(field1256)
                    self.newline()
                    field1257 = unwrapped1254[2]
                    self.pretty_config_dict(field1257)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1265 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1265 is not None:
            assert flat1265 is not None
            self.write(flat1265)
            return None
        else:
            fields1264 = msg
            self.write("(")
            self.write("path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1264))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1272 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1272 is not None:
            assert flat1272 is not None
            self.write(flat1272)
            return None
        else:
            def _t1679(_dollar_dollar):
                if _dollar_dollar.HasField("gnf_columns"):
                    _t1680 = _dollar_dollar.gnf_columns.columns
                else:
                    _t1680 = None
                return _t1680
            _t1681 = _t1679(msg)
            deconstruct_result1268 = _t1681
            if deconstruct_result1268 is not None:
                assert deconstruct_result1268 is not None
                unwrapped1269 = deconstruct_result1268
                self.write("(")
                self.write("gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1269) == 0:
                    self.newline()
                    for i1271, elem1270 in enumerate(unwrapped1269):
                        if (i1271 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1270)
                self.dedent()
                self.write(")")
            else:
                def _t1682(_dollar_dollar):
                    if _dollar_dollar.HasField("table_def"):
                        _t1683 = _dollar_dollar.table_def
                    else:
                        _t1683 = None
                    return _t1683
                _t1684 = _t1682(msg)
                deconstruct_result1266 = _t1684
                if deconstruct_result1266 is not None:
                    assert deconstruct_result1266 is not None
                    unwrapped1267 = deconstruct_result1266
                    self.write("(")
                    self.write("table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1267)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1277 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1277 is not None:
            assert flat1277 is not None
            self.write(flat1277)
            return None
        else:
            def _t1685(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            _t1686 = _t1685(msg)
            fields1273 = _t1686
            assert fields1273 is not None
            unwrapped_fields1274 = fields1273
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1275 = unwrapped_fields1274[0]
            self.write(self.format_string_value(field1275))
            self.newline()
            field1276 = unwrapped_fields1274[1]
            self.pretty_relation_id(field1276)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1281 = self._try_flat(msg, self.pretty_export_csv_columns)
        if flat1281 is not None:
            assert flat1281 is not None
            self.write(flat1281)
            return None
        else:
            fields1278 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1278) == 0:
                self.newline()
                for i1280, elem1279 in enumerate(fields1278):
                    if (i1280 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1279)
            self.dedent()
            self.write(")")


def pretty(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
