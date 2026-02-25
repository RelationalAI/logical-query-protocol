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

    def __init__(self, io: Optional[IO[str]] = None, max_width: int = 92, print_symbolic_relation_ids: bool = True):
        self.io = io if io is not None else StringIO()
        self.indent_stack: list[int] = [0]
        self.column = 0
        self.at_line_start = True
        self.separator = '\n'
        self.max_width = max_width
        self._computing: set[int] = set()
        self._memo: dict[int, str] = {}
        self._memo_refs: list[Any] = []
        self.print_symbolic_relation_ids = print_symbolic_relation_ids
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

    def relation_id_to_string(self, msg: logic_pb2.RelationId) -> str | None:
        """Convert RelationId to string representation using debug info."""
        if not self.print_symbolic_relation_ids:
            return None
        return self._debug_info.get((msg.id_low, msg.id_high), None)

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
        for (id_low, id_high), name in sorted(self._debug_info.items(), key=lambda x: x[1]):
            value = (id_high << 64) | id_low
            self.io.write(f';; \t ID `0x{value:x}` -> `{name}`\n')

    # --- Helper functions ---

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1698 = logic_pb2.Value(int_value=int(v))
        return _t1698

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1699 = logic_pb2.Value(int_value=v)
        return _t1699

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1700 = logic_pb2.Value(float_value=v)
        return _t1700

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1701 = logic_pb2.Value(string_value=v)
        return _t1701

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1702 = logic_pb2.Value(boolean_value=v)
        return _t1702

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1703 = logic_pb2.Value(uint128_value=v)
        return _t1703

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1704 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1704,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1705 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1705,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1706 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1706,))
        _t1707 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1707,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1708 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1708,))
        _t1709 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1709,))
        if msg.new_line != "":
            _t1710 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1710,))
        _t1711 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1711,))
        _t1712 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1712,))
        _t1713 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1713,))
        if msg.comment != "":
            _t1714 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1714,))
        for missing_string in msg.missing_strings:
            _t1715 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1715,))
        _t1716 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1716,))
        _t1717 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1717,))
        _t1718 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1718,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1719 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1719,))
        _t1720 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1720,))
        _t1721 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1721,))
        _t1722 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1722,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1723 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1723,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1724 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1724,))
        _t1725 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1725,))
        _t1726 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1726,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1727 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1727,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1728 = self._make_value_string(msg.compression)
            result.append(("compression", _t1728,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1729 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1729,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1730 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1730,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1731 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1731,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1732 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1732,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1733 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1733,))
        return sorted(result)

    def deconstruct_csv_column_tail(self, col: logic_pb2.CSVColumn) -> Optional[tuple[Optional[logic_pb2.RelationId], Sequence[logic_pb2.Type]]]:
        if (col.HasField("target_id") or not len(col.types) == 0):
            return (col.target_id, col.types,)
        else:
            _t1734 = None
        return None

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> str:
        name = self.relation_id_to_string(msg)
        assert name is not None
        return name

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name is None:
            return self.relation_id_to_uint128(msg)
        else:
            _t1735 = None
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
        flat654 = self._try_flat(msg, self.pretty_transaction)
        if flat654 is not None:
            assert flat654 is not None
            self.write(flat654)
            return None
        else:
            def _t1290(_dollar_dollar):
                if _dollar_dollar.HasField("configure"):
                    _t1291 = _dollar_dollar.configure
                else:
                    _t1291 = None
                if _dollar_dollar.HasField("sync"):
                    _t1292 = _dollar_dollar.sync
                else:
                    _t1292 = None
                return (_t1291, _t1292, _dollar_dollar.epochs,)
            _t1293 = _t1290(msg)
            fields645 = _t1293
            assert fields645 is not None
            unwrapped_fields646 = fields645
            self.write("(")
            self.write("transaction")
            self.indent_sexp()
            field647 = unwrapped_fields646[0]
            if field647 is not None:
                self.newline()
                assert field647 is not None
                opt_val648 = field647
                self.pretty_configure(opt_val648)
            field649 = unwrapped_fields646[1]
            if field649 is not None:
                self.newline()
                assert field649 is not None
                opt_val650 = field649
                self.pretty_sync(opt_val650)
            field651 = unwrapped_fields646[2]
            if not len(field651) == 0:
                self.newline()
                for i653, elem652 in enumerate(field651):
                    if (i653 > 0):
                        self.newline()
                    self.pretty_epoch(elem652)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat657 = self._try_flat(msg, self.pretty_configure)
        if flat657 is not None:
            assert flat657 is not None
            self.write(flat657)
            return None
        else:
            def _t1294(_dollar_dollar):
                _t1295 = self.deconstruct_configure(_dollar_dollar)
                return _t1295
            _t1296 = _t1294(msg)
            fields655 = _t1296
            assert fields655 is not None
            unwrapped_fields656 = fields655
            self.write("(")
            self.write("configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields656)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat661 = self._try_flat(msg, self.pretty_config_dict)
        if flat661 is not None:
            assert flat661 is not None
            self.write(flat661)
            return None
        else:
            fields658 = msg
            self.write("{")
            self.indent()
            if not len(fields658) == 0:
                self.newline()
                for i660, elem659 in enumerate(fields658):
                    if (i660 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem659)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat666 = self._try_flat(msg, self.pretty_config_key_value)
        if flat666 is not None:
            assert flat666 is not None
            self.write(flat666)
            return None
        else:
            def _t1297(_dollar_dollar):
                return (_dollar_dollar[0], _dollar_dollar[1],)
            _t1298 = _t1297(msg)
            fields662 = _t1298
            assert fields662 is not None
            unwrapped_fields663 = fields662
            self.write(":")
            field664 = unwrapped_fields663[0]
            self.write(field664)
            self.write(" ")
            field665 = unwrapped_fields663[1]
            self.pretty_value(field665)

    def pretty_value(self, msg: logic_pb2.Value):
        flat686 = self._try_flat(msg, self.pretty_value)
        if flat686 is not None:
            assert flat686 is not None
            self.write(flat686)
            return None
        else:
            def _t1299(_dollar_dollar):
                if _dollar_dollar.HasField("date_value"):
                    _t1300 = _dollar_dollar.date_value
                else:
                    _t1300 = None
                return _t1300
            _t1301 = _t1299(msg)
            deconstruct_result684 = _t1301
            if deconstruct_result684 is not None:
                assert deconstruct_result684 is not None
                unwrapped685 = deconstruct_result684
                self.pretty_date(unwrapped685)
            else:
                def _t1302(_dollar_dollar):
                    if _dollar_dollar.HasField("datetime_value"):
                        _t1303 = _dollar_dollar.datetime_value
                    else:
                        _t1303 = None
                    return _t1303
                _t1304 = _t1302(msg)
                deconstruct_result682 = _t1304
                if deconstruct_result682 is not None:
                    assert deconstruct_result682 is not None
                    unwrapped683 = deconstruct_result682
                    self.pretty_datetime(unwrapped683)
                else:
                    def _t1305(_dollar_dollar):
                        if _dollar_dollar.HasField("string_value"):
                            _t1306 = _dollar_dollar.string_value
                        else:
                            _t1306 = None
                        return _t1306
                    _t1307 = _t1305(msg)
                    deconstruct_result680 = _t1307
                    if deconstruct_result680 is not None:
                        assert deconstruct_result680 is not None
                        unwrapped681 = deconstruct_result680
                        self.write(self.format_string_value(unwrapped681))
                    else:
                        def _t1308(_dollar_dollar):
                            if _dollar_dollar.HasField("int_value"):
                                _t1309 = _dollar_dollar.int_value
                            else:
                                _t1309 = None
                            return _t1309
                        _t1310 = _t1308(msg)
                        deconstruct_result678 = _t1310
                        if deconstruct_result678 is not None:
                            assert deconstruct_result678 is not None
                            unwrapped679 = deconstruct_result678
                            self.write(str(unwrapped679))
                        else:
                            def _t1311(_dollar_dollar):
                                if _dollar_dollar.HasField("float_value"):
                                    _t1312 = _dollar_dollar.float_value
                                else:
                                    _t1312 = None
                                return _t1312
                            _t1313 = _t1311(msg)
                            deconstruct_result676 = _t1313
                            if deconstruct_result676 is not None:
                                assert deconstruct_result676 is not None
                                unwrapped677 = deconstruct_result676
                                self.write(str(unwrapped677))
                            else:
                                def _t1314(_dollar_dollar):
                                    if _dollar_dollar.HasField("uint128_value"):
                                        _t1315 = _dollar_dollar.uint128_value
                                    else:
                                        _t1315 = None
                                    return _t1315
                                _t1316 = _t1314(msg)
                                deconstruct_result674 = _t1316
                                if deconstruct_result674 is not None:
                                    assert deconstruct_result674 is not None
                                    unwrapped675 = deconstruct_result674
                                    self.write(self.format_uint128(unwrapped675))
                                else:
                                    def _t1317(_dollar_dollar):
                                        if _dollar_dollar.HasField("int128_value"):
                                            _t1318 = _dollar_dollar.int128_value
                                        else:
                                            _t1318 = None
                                        return _t1318
                                    _t1319 = _t1317(msg)
                                    deconstruct_result672 = _t1319
                                    if deconstruct_result672 is not None:
                                        assert deconstruct_result672 is not None
                                        unwrapped673 = deconstruct_result672
                                        self.write(self.format_int128(unwrapped673))
                                    else:
                                        def _t1320(_dollar_dollar):
                                            if _dollar_dollar.HasField("decimal_value"):
                                                _t1321 = _dollar_dollar.decimal_value
                                            else:
                                                _t1321 = None
                                            return _t1321
                                        _t1322 = _t1320(msg)
                                        deconstruct_result670 = _t1322
                                        if deconstruct_result670 is not None:
                                            assert deconstruct_result670 is not None
                                            unwrapped671 = deconstruct_result670
                                            self.write(self.format_decimal(unwrapped671))
                                        else:
                                            def _t1323(_dollar_dollar):
                                                if _dollar_dollar.HasField("boolean_value"):
                                                    _t1324 = _dollar_dollar.boolean_value
                                                else:
                                                    _t1324 = None
                                                return _t1324
                                            _t1325 = _t1323(msg)
                                            deconstruct_result668 = _t1325
                                            if deconstruct_result668 is not None:
                                                assert deconstruct_result668 is not None
                                                unwrapped669 = deconstruct_result668
                                                self.pretty_boolean_value(unwrapped669)
                                            else:
                                                fields667 = msg
                                                self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat692 = self._try_flat(msg, self.pretty_date)
        if flat692 is not None:
            assert flat692 is not None
            self.write(flat692)
            return None
        else:
            def _t1326(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            _t1327 = _t1326(msg)
            fields687 = _t1327
            assert fields687 is not None
            unwrapped_fields688 = fields687
            self.write("(")
            self.write("date")
            self.indent_sexp()
            self.newline()
            field689 = unwrapped_fields688[0]
            self.write(str(field689))
            self.newline()
            field690 = unwrapped_fields688[1]
            self.write(str(field690))
            self.newline()
            field691 = unwrapped_fields688[2]
            self.write(str(field691))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat703 = self._try_flat(msg, self.pretty_datetime)
        if flat703 is not None:
            assert flat703 is not None
            self.write(flat703)
            return None
        else:
            def _t1328(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            _t1329 = _t1328(msg)
            fields693 = _t1329
            assert fields693 is not None
            unwrapped_fields694 = fields693
            self.write("(")
            self.write("datetime")
            self.indent_sexp()
            self.newline()
            field695 = unwrapped_fields694[0]
            self.write(str(field695))
            self.newline()
            field696 = unwrapped_fields694[1]
            self.write(str(field696))
            self.newline()
            field697 = unwrapped_fields694[2]
            self.write(str(field697))
            self.newline()
            field698 = unwrapped_fields694[3]
            self.write(str(field698))
            self.newline()
            field699 = unwrapped_fields694[4]
            self.write(str(field699))
            self.newline()
            field700 = unwrapped_fields694[5]
            self.write(str(field700))
            field701 = unwrapped_fields694[6]
            if field701 is not None:
                self.newline()
                assert field701 is not None
                opt_val702 = field701
                self.write(str(opt_val702))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        def _t1330(_dollar_dollar):
            if _dollar_dollar:
                _t1331 = ()
            else:
                _t1331 = None
            return _t1331
        _t1332 = _t1330(msg)
        deconstruct_result706 = _t1332
        if deconstruct_result706 is not None:
            assert deconstruct_result706 is not None
            unwrapped707 = deconstruct_result706
            self.write("true")
        else:
            def _t1333(_dollar_dollar):
                if not _dollar_dollar:
                    _t1334 = ()
                else:
                    _t1334 = None
                return _t1334
            _t1335 = _t1333(msg)
            deconstruct_result704 = _t1335
            if deconstruct_result704 is not None:
                assert deconstruct_result704 is not None
                unwrapped705 = deconstruct_result704
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat712 = self._try_flat(msg, self.pretty_sync)
        if flat712 is not None:
            assert flat712 is not None
            self.write(flat712)
            return None
        else:
            def _t1336(_dollar_dollar):
                return _dollar_dollar.fragments
            _t1337 = _t1336(msg)
            fields708 = _t1337
            assert fields708 is not None
            unwrapped_fields709 = fields708
            self.write("(")
            self.write("sync")
            self.indent_sexp()
            if not len(unwrapped_fields709) == 0:
                self.newline()
                for i711, elem710 in enumerate(unwrapped_fields709):
                    if (i711 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem710)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat715 = self._try_flat(msg, self.pretty_fragment_id)
        if flat715 is not None:
            assert flat715 is not None
            self.write(flat715)
            return None
        else:
            def _t1338(_dollar_dollar):
                return self.fragment_id_to_string(_dollar_dollar)
            _t1339 = _t1338(msg)
            fields713 = _t1339
            assert fields713 is not None
            unwrapped_fields714 = fields713
            self.write(":")
            self.write(unwrapped_fields714)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat722 = self._try_flat(msg, self.pretty_epoch)
        if flat722 is not None:
            assert flat722 is not None
            self.write(flat722)
            return None
        else:
            def _t1340(_dollar_dollar):
                if not len(_dollar_dollar.writes) == 0:
                    _t1341 = _dollar_dollar.writes
                else:
                    _t1341 = None
                if not len(_dollar_dollar.reads) == 0:
                    _t1342 = _dollar_dollar.reads
                else:
                    _t1342 = None
                return (_t1341, _t1342,)
            _t1343 = _t1340(msg)
            fields716 = _t1343
            assert fields716 is not None
            unwrapped_fields717 = fields716
            self.write("(")
            self.write("epoch")
            self.indent_sexp()
            field718 = unwrapped_fields717[0]
            if field718 is not None:
                self.newline()
                assert field718 is not None
                opt_val719 = field718
                self.pretty_epoch_writes(opt_val719)
            field720 = unwrapped_fields717[1]
            if field720 is not None:
                self.newline()
                assert field720 is not None
                opt_val721 = field720
                self.pretty_epoch_reads(opt_val721)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat726 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat726 is not None:
            assert flat726 is not None
            self.write(flat726)
            return None
        else:
            fields723 = msg
            self.write("(")
            self.write("writes")
            self.indent_sexp()
            if not len(fields723) == 0:
                self.newline()
                for i725, elem724 in enumerate(fields723):
                    if (i725 > 0):
                        self.newline()
                    self.pretty_write(elem724)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat735 = self._try_flat(msg, self.pretty_write)
        if flat735 is not None:
            assert flat735 is not None
            self.write(flat735)
            return None
        else:
            def _t1344(_dollar_dollar):
                if _dollar_dollar.HasField("define"):
                    _t1345 = _dollar_dollar.define
                else:
                    _t1345 = None
                return _t1345
            _t1346 = _t1344(msg)
            deconstruct_result733 = _t1346
            if deconstruct_result733 is not None:
                assert deconstruct_result733 is not None
                unwrapped734 = deconstruct_result733
                self.pretty_define(unwrapped734)
            else:
                def _t1347(_dollar_dollar):
                    if _dollar_dollar.HasField("undefine"):
                        _t1348 = _dollar_dollar.undefine
                    else:
                        _t1348 = None
                    return _t1348
                _t1349 = _t1347(msg)
                deconstruct_result731 = _t1349
                if deconstruct_result731 is not None:
                    assert deconstruct_result731 is not None
                    unwrapped732 = deconstruct_result731
                    self.pretty_undefine(unwrapped732)
                else:
                    def _t1350(_dollar_dollar):
                        if _dollar_dollar.HasField("context"):
                            _t1351 = _dollar_dollar.context
                        else:
                            _t1351 = None
                        return _t1351
                    _t1352 = _t1350(msg)
                    deconstruct_result729 = _t1352
                    if deconstruct_result729 is not None:
                        assert deconstruct_result729 is not None
                        unwrapped730 = deconstruct_result729
                        self.pretty_context(unwrapped730)
                    else:
                        def _t1353(_dollar_dollar):
                            if _dollar_dollar.HasField("snapshot"):
                                _t1354 = _dollar_dollar.snapshot
                            else:
                                _t1354 = None
                            return _t1354
                        _t1355 = _t1353(msg)
                        deconstruct_result727 = _t1355
                        if deconstruct_result727 is not None:
                            assert deconstruct_result727 is not None
                            unwrapped728 = deconstruct_result727
                            self.pretty_snapshot(unwrapped728)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat738 = self._try_flat(msg, self.pretty_define)
        if flat738 is not None:
            assert flat738 is not None
            self.write(flat738)
            return None
        else:
            def _t1356(_dollar_dollar):
                return _dollar_dollar.fragment
            _t1357 = _t1356(msg)
            fields736 = _t1357
            assert fields736 is not None
            unwrapped_fields737 = fields736
            self.write("(")
            self.write("define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields737)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat745 = self._try_flat(msg, self.pretty_fragment)
        if flat745 is not None:
            assert flat745 is not None
            self.write(flat745)
            return None
        else:
            def _t1358(_dollar_dollar):
                self.start_pretty_fragment(_dollar_dollar)
                return (_dollar_dollar.id, _dollar_dollar.declarations,)
            _t1359 = _t1358(msg)
            fields739 = _t1359
            assert fields739 is not None
            unwrapped_fields740 = fields739
            self.write("(")
            self.write("fragment")
            self.indent_sexp()
            self.newline()
            field741 = unwrapped_fields740[0]
            self.pretty_new_fragment_id(field741)
            field742 = unwrapped_fields740[1]
            if not len(field742) == 0:
                self.newline()
                for i744, elem743 in enumerate(field742):
                    if (i744 > 0):
                        self.newline()
                    self.pretty_declaration(elem743)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat747 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat747 is not None:
            assert flat747 is not None
            self.write(flat747)
            return None
        else:
            fields746 = msg
            self.pretty_fragment_id(fields746)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat756 = self._try_flat(msg, self.pretty_declaration)
        if flat756 is not None:
            assert flat756 is not None
            self.write(flat756)
            return None
        else:
            def _t1360(_dollar_dollar):
                if _dollar_dollar.HasField("def"):
                    _t1361 = getattr(_dollar_dollar, 'def')
                else:
                    _t1361 = None
                return _t1361
            _t1362 = _t1360(msg)
            deconstruct_result754 = _t1362
            if deconstruct_result754 is not None:
                assert deconstruct_result754 is not None
                unwrapped755 = deconstruct_result754
                self.pretty_def(unwrapped755)
            else:
                def _t1363(_dollar_dollar):
                    if _dollar_dollar.HasField("algorithm"):
                        _t1364 = _dollar_dollar.algorithm
                    else:
                        _t1364 = None
                    return _t1364
                _t1365 = _t1363(msg)
                deconstruct_result752 = _t1365
                if deconstruct_result752 is not None:
                    assert deconstruct_result752 is not None
                    unwrapped753 = deconstruct_result752
                    self.pretty_algorithm(unwrapped753)
                else:
                    def _t1366(_dollar_dollar):
                        if _dollar_dollar.HasField("constraint"):
                            _t1367 = _dollar_dollar.constraint
                        else:
                            _t1367 = None
                        return _t1367
                    _t1368 = _t1366(msg)
                    deconstruct_result750 = _t1368
                    if deconstruct_result750 is not None:
                        assert deconstruct_result750 is not None
                        unwrapped751 = deconstruct_result750
                        self.pretty_constraint(unwrapped751)
                    else:
                        def _t1369(_dollar_dollar):
                            if _dollar_dollar.HasField("data"):
                                _t1370 = _dollar_dollar.data
                            else:
                                _t1370 = None
                            return _t1370
                        _t1371 = _t1369(msg)
                        deconstruct_result748 = _t1371
                        if deconstruct_result748 is not None:
                            assert deconstruct_result748 is not None
                            unwrapped749 = deconstruct_result748
                            self.pretty_data(unwrapped749)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat763 = self._try_flat(msg, self.pretty_def)
        if flat763 is not None:
            assert flat763 is not None
            self.write(flat763)
            return None
        else:
            def _t1372(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1373 = _dollar_dollar.attrs
                else:
                    _t1373 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1373,)
            _t1374 = _t1372(msg)
            fields757 = _t1374
            assert fields757 is not None
            unwrapped_fields758 = fields757
            self.write("(")
            self.write("def")
            self.indent_sexp()
            self.newline()
            field759 = unwrapped_fields758[0]
            self.pretty_relation_id(field759)
            self.newline()
            field760 = unwrapped_fields758[1]
            self.pretty_abstraction(field760)
            field761 = unwrapped_fields758[2]
            if field761 is not None:
                self.newline()
                assert field761 is not None
                opt_val762 = field761
                self.pretty_attrs(opt_val762)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat768 = self._try_flat(msg, self.pretty_relation_id)
        if flat768 is not None:
            assert flat768 is not None
            self.write(flat768)
            return None
        else:
            def _t1375(_dollar_dollar):
                if self.relation_id_to_string(_dollar_dollar) is not None:
                    _t1377 = self.deconstruct_relation_id_string(_dollar_dollar)
                    _t1376 = _t1377
                else:
                    _t1376 = None
                return _t1376
            _t1378 = _t1375(msg)
            deconstruct_result766 = _t1378
            if deconstruct_result766 is not None:
                assert deconstruct_result766 is not None
                unwrapped767 = deconstruct_result766
                self.write(":")
                self.write(unwrapped767)
            else:
                def _t1379(_dollar_dollar):
                    _t1380 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                    return _t1380
                _t1381 = _t1379(msg)
                deconstruct_result764 = _t1381
                if deconstruct_result764 is not None:
                    assert deconstruct_result764 is not None
                    unwrapped765 = deconstruct_result764
                    self.write(self.format_uint128(unwrapped765))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat773 = self._try_flat(msg, self.pretty_abstraction)
        if flat773 is not None:
            assert flat773 is not None
            self.write(flat773)
            return None
        else:
            def _t1382(_dollar_dollar):
                _t1383 = self.deconstruct_bindings(_dollar_dollar)
                return (_t1383, _dollar_dollar.value,)
            _t1384 = _t1382(msg)
            fields769 = _t1384
            assert fields769 is not None
            unwrapped_fields770 = fields769
            self.write("(")
            self.indent()
            field771 = unwrapped_fields770[0]
            self.pretty_bindings(field771)
            self.newline()
            field772 = unwrapped_fields770[1]
            self.pretty_formula(field772)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat781 = self._try_flat(msg, self.pretty_bindings)
        if flat781 is not None:
            assert flat781 is not None
            self.write(flat781)
            return None
        else:
            def _t1385(_dollar_dollar):
                if not len(_dollar_dollar[1]) == 0:
                    _t1386 = _dollar_dollar[1]
                else:
                    _t1386 = None
                return (_dollar_dollar[0], _t1386,)
            _t1387 = _t1385(msg)
            fields774 = _t1387
            assert fields774 is not None
            unwrapped_fields775 = fields774
            self.write("[")
            self.indent()
            field776 = unwrapped_fields775[0]
            for i778, elem777 in enumerate(field776):
                if (i778 > 0):
                    self.newline()
                self.pretty_binding(elem777)
            field779 = unwrapped_fields775[1]
            if field779 is not None:
                self.newline()
                assert field779 is not None
                opt_val780 = field779
                self.pretty_value_bindings(opt_val780)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat786 = self._try_flat(msg, self.pretty_binding)
        if flat786 is not None:
            assert flat786 is not None
            self.write(flat786)
            return None
        else:
            def _t1388(_dollar_dollar):
                return (_dollar_dollar.var.name, _dollar_dollar.type,)
            _t1389 = _t1388(msg)
            fields782 = _t1389
            assert fields782 is not None
            unwrapped_fields783 = fields782
            field784 = unwrapped_fields783[0]
            self.write(field784)
            self.write("::")
            field785 = unwrapped_fields783[1]
            self.pretty_type(field785)

    def pretty_type(self, msg: logic_pb2.Type):
        flat809 = self._try_flat(msg, self.pretty_type)
        if flat809 is not None:
            assert flat809 is not None
            self.write(flat809)
            return None
        else:
            def _t1390(_dollar_dollar):
                if _dollar_dollar.HasField("unspecified_type"):
                    _t1391 = _dollar_dollar.unspecified_type
                else:
                    _t1391 = None
                return _t1391
            _t1392 = _t1390(msg)
            deconstruct_result807 = _t1392
            if deconstruct_result807 is not None:
                assert deconstruct_result807 is not None
                unwrapped808 = deconstruct_result807
                self.pretty_unspecified_type(unwrapped808)
            else:
                def _t1393(_dollar_dollar):
                    if _dollar_dollar.HasField("string_type"):
                        _t1394 = _dollar_dollar.string_type
                    else:
                        _t1394 = None
                    return _t1394
                _t1395 = _t1393(msg)
                deconstruct_result805 = _t1395
                if deconstruct_result805 is not None:
                    assert deconstruct_result805 is not None
                    unwrapped806 = deconstruct_result805
                    self.pretty_string_type(unwrapped806)
                else:
                    def _t1396(_dollar_dollar):
                        if _dollar_dollar.HasField("int_type"):
                            _t1397 = _dollar_dollar.int_type
                        else:
                            _t1397 = None
                        return _t1397
                    _t1398 = _t1396(msg)
                    deconstruct_result803 = _t1398
                    if deconstruct_result803 is not None:
                        assert deconstruct_result803 is not None
                        unwrapped804 = deconstruct_result803
                        self.pretty_int_type(unwrapped804)
                    else:
                        def _t1399(_dollar_dollar):
                            if _dollar_dollar.HasField("float_type"):
                                _t1400 = _dollar_dollar.float_type
                            else:
                                _t1400 = None
                            return _t1400
                        _t1401 = _t1399(msg)
                        deconstruct_result801 = _t1401
                        if deconstruct_result801 is not None:
                            assert deconstruct_result801 is not None
                            unwrapped802 = deconstruct_result801
                            self.pretty_float_type(unwrapped802)
                        else:
                            def _t1402(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_type"):
                                    _t1403 = _dollar_dollar.uint128_type
                                else:
                                    _t1403 = None
                                return _t1403
                            _t1404 = _t1402(msg)
                            deconstruct_result799 = _t1404
                            if deconstruct_result799 is not None:
                                assert deconstruct_result799 is not None
                                unwrapped800 = deconstruct_result799
                                self.pretty_uint128_type(unwrapped800)
                            else:
                                def _t1405(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_type"):
                                        _t1406 = _dollar_dollar.int128_type
                                    else:
                                        _t1406 = None
                                    return _t1406
                                _t1407 = _t1405(msg)
                                deconstruct_result797 = _t1407
                                if deconstruct_result797 is not None:
                                    assert deconstruct_result797 is not None
                                    unwrapped798 = deconstruct_result797
                                    self.pretty_int128_type(unwrapped798)
                                else:
                                    def _t1408(_dollar_dollar):
                                        if _dollar_dollar.HasField("date_type"):
                                            _t1409 = _dollar_dollar.date_type
                                        else:
                                            _t1409 = None
                                        return _t1409
                                    _t1410 = _t1408(msg)
                                    deconstruct_result795 = _t1410
                                    if deconstruct_result795 is not None:
                                        assert deconstruct_result795 is not None
                                        unwrapped796 = deconstruct_result795
                                        self.pretty_date_type(unwrapped796)
                                    else:
                                        def _t1411(_dollar_dollar):
                                            if _dollar_dollar.HasField("datetime_type"):
                                                _t1412 = _dollar_dollar.datetime_type
                                            else:
                                                _t1412 = None
                                            return _t1412
                                        _t1413 = _t1411(msg)
                                        deconstruct_result793 = _t1413
                                        if deconstruct_result793 is not None:
                                            assert deconstruct_result793 is not None
                                            unwrapped794 = deconstruct_result793
                                            self.pretty_datetime_type(unwrapped794)
                                        else:
                                            def _t1414(_dollar_dollar):
                                                if _dollar_dollar.HasField("missing_type"):
                                                    _t1415 = _dollar_dollar.missing_type
                                                else:
                                                    _t1415 = None
                                                return _t1415
                                            _t1416 = _t1414(msg)
                                            deconstruct_result791 = _t1416
                                            if deconstruct_result791 is not None:
                                                assert deconstruct_result791 is not None
                                                unwrapped792 = deconstruct_result791
                                                self.pretty_missing_type(unwrapped792)
                                            else:
                                                def _t1417(_dollar_dollar):
                                                    if _dollar_dollar.HasField("decimal_type"):
                                                        _t1418 = _dollar_dollar.decimal_type
                                                    else:
                                                        _t1418 = None
                                                    return _t1418
                                                _t1419 = _t1417(msg)
                                                deconstruct_result789 = _t1419
                                                if deconstruct_result789 is not None:
                                                    assert deconstruct_result789 is not None
                                                    unwrapped790 = deconstruct_result789
                                                    self.pretty_decimal_type(unwrapped790)
                                                else:
                                                    def _t1420(_dollar_dollar):
                                                        if _dollar_dollar.HasField("boolean_type"):
                                                            _t1421 = _dollar_dollar.boolean_type
                                                        else:
                                                            _t1421 = None
                                                        return _t1421
                                                    _t1422 = _t1420(msg)
                                                    deconstruct_result787 = _t1422
                                                    if deconstruct_result787 is not None:
                                                        assert deconstruct_result787 is not None
                                                        unwrapped788 = deconstruct_result787
                                                        self.pretty_boolean_type(unwrapped788)
                                                    else:
                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields810 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields811 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields812 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields813 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields814 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields815 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields816 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields817 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields818 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat823 = self._try_flat(msg, self.pretty_decimal_type)
        if flat823 is not None:
            assert flat823 is not None
            self.write(flat823)
            return None
        else:
            def _t1423(_dollar_dollar):
                return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            _t1424 = _t1423(msg)
            fields819 = _t1424
            assert fields819 is not None
            unwrapped_fields820 = fields819
            self.write("(")
            self.write("DECIMAL")
            self.indent_sexp()
            self.newline()
            field821 = unwrapped_fields820[0]
            self.write(str(field821))
            self.newline()
            field822 = unwrapped_fields820[1]
            self.write(str(field822))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields824 = msg
        self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat828 = self._try_flat(msg, self.pretty_value_bindings)
        if flat828 is not None:
            assert flat828 is not None
            self.write(flat828)
            return None
        else:
            fields825 = msg
            self.write("|")
            if not len(fields825) == 0:
                self.write(" ")
                for i827, elem826 in enumerate(fields825):
                    if (i827 > 0):
                        self.newline()
                    self.pretty_binding(elem826)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat855 = self._try_flat(msg, self.pretty_formula)
        if flat855 is not None:
            assert flat855 is not None
            self.write(flat855)
            return None
        else:
            def _t1425(_dollar_dollar):
                if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                    _t1426 = _dollar_dollar.conjunction
                else:
                    _t1426 = None
                return _t1426
            _t1427 = _t1425(msg)
            deconstruct_result853 = _t1427
            if deconstruct_result853 is not None:
                assert deconstruct_result853 is not None
                unwrapped854 = deconstruct_result853
                self.pretty_true(unwrapped854)
            else:
                def _t1428(_dollar_dollar):
                    if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                        _t1429 = _dollar_dollar.disjunction
                    else:
                        _t1429 = None
                    return _t1429
                _t1430 = _t1428(msg)
                deconstruct_result851 = _t1430
                if deconstruct_result851 is not None:
                    assert deconstruct_result851 is not None
                    unwrapped852 = deconstruct_result851
                    self.pretty_false(unwrapped852)
                else:
                    def _t1431(_dollar_dollar):
                        if _dollar_dollar.HasField("exists"):
                            _t1432 = _dollar_dollar.exists
                        else:
                            _t1432 = None
                        return _t1432
                    _t1433 = _t1431(msg)
                    deconstruct_result849 = _t1433
                    if deconstruct_result849 is not None:
                        assert deconstruct_result849 is not None
                        unwrapped850 = deconstruct_result849
                        self.pretty_exists(unwrapped850)
                    else:
                        def _t1434(_dollar_dollar):
                            if _dollar_dollar.HasField("reduce"):
                                _t1435 = _dollar_dollar.reduce
                            else:
                                _t1435 = None
                            return _t1435
                        _t1436 = _t1434(msg)
                        deconstruct_result847 = _t1436
                        if deconstruct_result847 is not None:
                            assert deconstruct_result847 is not None
                            unwrapped848 = deconstruct_result847
                            self.pretty_reduce(unwrapped848)
                        else:
                            def _t1437(_dollar_dollar):
                                if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                    _t1438 = _dollar_dollar.conjunction
                                else:
                                    _t1438 = None
                                return _t1438
                            _t1439 = _t1437(msg)
                            deconstruct_result845 = _t1439
                            if deconstruct_result845 is not None:
                                assert deconstruct_result845 is not None
                                unwrapped846 = deconstruct_result845
                                self.pretty_conjunction(unwrapped846)
                            else:
                                def _t1440(_dollar_dollar):
                                    if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                        _t1441 = _dollar_dollar.disjunction
                                    else:
                                        _t1441 = None
                                    return _t1441
                                _t1442 = _t1440(msg)
                                deconstruct_result843 = _t1442
                                if deconstruct_result843 is not None:
                                    assert deconstruct_result843 is not None
                                    unwrapped844 = deconstruct_result843
                                    self.pretty_disjunction(unwrapped844)
                                else:
                                    def _t1443(_dollar_dollar):
                                        if _dollar_dollar.HasField("not"):
                                            _t1444 = getattr(_dollar_dollar, 'not')
                                        else:
                                            _t1444 = None
                                        return _t1444
                                    _t1445 = _t1443(msg)
                                    deconstruct_result841 = _t1445
                                    if deconstruct_result841 is not None:
                                        assert deconstruct_result841 is not None
                                        unwrapped842 = deconstruct_result841
                                        self.pretty_not(unwrapped842)
                                    else:
                                        def _t1446(_dollar_dollar):
                                            if _dollar_dollar.HasField("ffi"):
                                                _t1447 = _dollar_dollar.ffi
                                            else:
                                                _t1447 = None
                                            return _t1447
                                        _t1448 = _t1446(msg)
                                        deconstruct_result839 = _t1448
                                        if deconstruct_result839 is not None:
                                            assert deconstruct_result839 is not None
                                            unwrapped840 = deconstruct_result839
                                            self.pretty_ffi(unwrapped840)
                                        else:
                                            def _t1449(_dollar_dollar):
                                                if _dollar_dollar.HasField("atom"):
                                                    _t1450 = _dollar_dollar.atom
                                                else:
                                                    _t1450 = None
                                                return _t1450
                                            _t1451 = _t1449(msg)
                                            deconstruct_result837 = _t1451
                                            if deconstruct_result837 is not None:
                                                assert deconstruct_result837 is not None
                                                unwrapped838 = deconstruct_result837
                                                self.pretty_atom(unwrapped838)
                                            else:
                                                def _t1452(_dollar_dollar):
                                                    if _dollar_dollar.HasField("pragma"):
                                                        _t1453 = _dollar_dollar.pragma
                                                    else:
                                                        _t1453 = None
                                                    return _t1453
                                                _t1454 = _t1452(msg)
                                                deconstruct_result835 = _t1454
                                                if deconstruct_result835 is not None:
                                                    assert deconstruct_result835 is not None
                                                    unwrapped836 = deconstruct_result835
                                                    self.pretty_pragma(unwrapped836)
                                                else:
                                                    def _t1455(_dollar_dollar):
                                                        if _dollar_dollar.HasField("primitive"):
                                                            _t1456 = _dollar_dollar.primitive
                                                        else:
                                                            _t1456 = None
                                                        return _t1456
                                                    _t1457 = _t1455(msg)
                                                    deconstruct_result833 = _t1457
                                                    if deconstruct_result833 is not None:
                                                        assert deconstruct_result833 is not None
                                                        unwrapped834 = deconstruct_result833
                                                        self.pretty_primitive(unwrapped834)
                                                    else:
                                                        def _t1458(_dollar_dollar):
                                                            if _dollar_dollar.HasField("rel_atom"):
                                                                _t1459 = _dollar_dollar.rel_atom
                                                            else:
                                                                _t1459 = None
                                                            return _t1459
                                                        _t1460 = _t1458(msg)
                                                        deconstruct_result831 = _t1460
                                                        if deconstruct_result831 is not None:
                                                            assert deconstruct_result831 is not None
                                                            unwrapped832 = deconstruct_result831
                                                            self.pretty_rel_atom(unwrapped832)
                                                        else:
                                                            def _t1461(_dollar_dollar):
                                                                if _dollar_dollar.HasField("cast"):
                                                                    _t1462 = _dollar_dollar.cast
                                                                else:
                                                                    _t1462 = None
                                                                return _t1462
                                                            _t1463 = _t1461(msg)
                                                            deconstruct_result829 = _t1463
                                                            if deconstruct_result829 is not None:
                                                                assert deconstruct_result829 is not None
                                                                unwrapped830 = deconstruct_result829
                                                                self.pretty_cast(unwrapped830)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields856 = msg
        self.write("(")
        self.write("true")
        self.write(")")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields857 = msg
        self.write("(")
        self.write("false")
        self.write(")")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat862 = self._try_flat(msg, self.pretty_exists)
        if flat862 is not None:
            assert flat862 is not None
            self.write(flat862)
            return None
        else:
            def _t1464(_dollar_dollar):
                _t1465 = self.deconstruct_bindings(_dollar_dollar.body)
                return (_t1465, _dollar_dollar.body.value,)
            _t1466 = _t1464(msg)
            fields858 = _t1466
            assert fields858 is not None
            unwrapped_fields859 = fields858
            self.write("(")
            self.write("exists")
            self.indent_sexp()
            self.newline()
            field860 = unwrapped_fields859[0]
            self.pretty_bindings(field860)
            self.newline()
            field861 = unwrapped_fields859[1]
            self.pretty_formula(field861)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat868 = self._try_flat(msg, self.pretty_reduce)
        if flat868 is not None:
            assert flat868 is not None
            self.write(flat868)
            return None
        else:
            def _t1467(_dollar_dollar):
                return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            _t1468 = _t1467(msg)
            fields863 = _t1468
            assert fields863 is not None
            unwrapped_fields864 = fields863
            self.write("(")
            self.write("reduce")
            self.indent_sexp()
            self.newline()
            field865 = unwrapped_fields864[0]
            self.pretty_abstraction(field865)
            self.newline()
            field866 = unwrapped_fields864[1]
            self.pretty_abstraction(field866)
            self.newline()
            field867 = unwrapped_fields864[2]
            self.pretty_terms(field867)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat872 = self._try_flat(msg, self.pretty_terms)
        if flat872 is not None:
            assert flat872 is not None
            self.write(flat872)
            return None
        else:
            fields869 = msg
            self.write("(")
            self.write("terms")
            self.indent_sexp()
            if not len(fields869) == 0:
                self.newline()
                for i871, elem870 in enumerate(fields869):
                    if (i871 > 0):
                        self.newline()
                    self.pretty_term(elem870)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat877 = self._try_flat(msg, self.pretty_term)
        if flat877 is not None:
            assert flat877 is not None
            self.write(flat877)
            return None
        else:
            def _t1469(_dollar_dollar):
                if _dollar_dollar.HasField("var"):
                    _t1470 = _dollar_dollar.var
                else:
                    _t1470 = None
                return _t1470
            _t1471 = _t1469(msg)
            deconstruct_result875 = _t1471
            if deconstruct_result875 is not None:
                assert deconstruct_result875 is not None
                unwrapped876 = deconstruct_result875
                self.pretty_var(unwrapped876)
            else:
                def _t1472(_dollar_dollar):
                    if _dollar_dollar.HasField("constant"):
                        _t1473 = _dollar_dollar.constant
                    else:
                        _t1473 = None
                    return _t1473
                _t1474 = _t1472(msg)
                deconstruct_result873 = _t1474
                if deconstruct_result873 is not None:
                    assert deconstruct_result873 is not None
                    unwrapped874 = deconstruct_result873
                    self.pretty_constant(unwrapped874)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat880 = self._try_flat(msg, self.pretty_var)
        if flat880 is not None:
            assert flat880 is not None
            self.write(flat880)
            return None
        else:
            def _t1475(_dollar_dollar):
                return _dollar_dollar.name
            _t1476 = _t1475(msg)
            fields878 = _t1476
            assert fields878 is not None
            unwrapped_fields879 = fields878
            self.write(unwrapped_fields879)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat882 = self._try_flat(msg, self.pretty_constant)
        if flat882 is not None:
            assert flat882 is not None
            self.write(flat882)
            return None
        else:
            fields881 = msg
            self.pretty_value(fields881)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat887 = self._try_flat(msg, self.pretty_conjunction)
        if flat887 is not None:
            assert flat887 is not None
            self.write(flat887)
            return None
        else:
            def _t1477(_dollar_dollar):
                return _dollar_dollar.args
            _t1478 = _t1477(msg)
            fields883 = _t1478
            assert fields883 is not None
            unwrapped_fields884 = fields883
            self.write("(")
            self.write("and")
            self.indent_sexp()
            if not len(unwrapped_fields884) == 0:
                self.newline()
                for i886, elem885 in enumerate(unwrapped_fields884):
                    if (i886 > 0):
                        self.newline()
                    self.pretty_formula(elem885)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat892 = self._try_flat(msg, self.pretty_disjunction)
        if flat892 is not None:
            assert flat892 is not None
            self.write(flat892)
            return None
        else:
            def _t1479(_dollar_dollar):
                return _dollar_dollar.args
            _t1480 = _t1479(msg)
            fields888 = _t1480
            assert fields888 is not None
            unwrapped_fields889 = fields888
            self.write("(")
            self.write("or")
            self.indent_sexp()
            if not len(unwrapped_fields889) == 0:
                self.newline()
                for i891, elem890 in enumerate(unwrapped_fields889):
                    if (i891 > 0):
                        self.newline()
                    self.pretty_formula(elem890)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat895 = self._try_flat(msg, self.pretty_not)
        if flat895 is not None:
            assert flat895 is not None
            self.write(flat895)
            return None
        else:
            def _t1481(_dollar_dollar):
                return _dollar_dollar.arg
            _t1482 = _t1481(msg)
            fields893 = _t1482
            assert fields893 is not None
            unwrapped_fields894 = fields893
            self.write("(")
            self.write("not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields894)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat901 = self._try_flat(msg, self.pretty_ffi)
        if flat901 is not None:
            assert flat901 is not None
            self.write(flat901)
            return None
        else:
            def _t1483(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            _t1484 = _t1483(msg)
            fields896 = _t1484
            assert fields896 is not None
            unwrapped_fields897 = fields896
            self.write("(")
            self.write("ffi")
            self.indent_sexp()
            self.newline()
            field898 = unwrapped_fields897[0]
            self.pretty_name(field898)
            self.newline()
            field899 = unwrapped_fields897[1]
            self.pretty_ffi_args(field899)
            self.newline()
            field900 = unwrapped_fields897[2]
            self.pretty_terms(field900)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat903 = self._try_flat(msg, self.pretty_name)
        if flat903 is not None:
            assert flat903 is not None
            self.write(flat903)
            return None
        else:
            fields902 = msg
            self.write(":")
            self.write(fields902)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat907 = self._try_flat(msg, self.pretty_ffi_args)
        if flat907 is not None:
            assert flat907 is not None
            self.write(flat907)
            return None
        else:
            fields904 = msg
            self.write("(")
            self.write("args")
            self.indent_sexp()
            if not len(fields904) == 0:
                self.newline()
                for i906, elem905 in enumerate(fields904):
                    if (i906 > 0):
                        self.newline()
                    self.pretty_abstraction(elem905)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat914 = self._try_flat(msg, self.pretty_atom)
        if flat914 is not None:
            assert flat914 is not None
            self.write(flat914)
            return None
        else:
            def _t1485(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1486 = _t1485(msg)
            fields908 = _t1486
            assert fields908 is not None
            unwrapped_fields909 = fields908
            self.write("(")
            self.write("atom")
            self.indent_sexp()
            self.newline()
            field910 = unwrapped_fields909[0]
            self.pretty_relation_id(field910)
            field911 = unwrapped_fields909[1]
            if not len(field911) == 0:
                self.newline()
                for i913, elem912 in enumerate(field911):
                    if (i913 > 0):
                        self.newline()
                    self.pretty_term(elem912)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat921 = self._try_flat(msg, self.pretty_pragma)
        if flat921 is not None:
            assert flat921 is not None
            self.write(flat921)
            return None
        else:
            def _t1487(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1488 = _t1487(msg)
            fields915 = _t1488
            assert fields915 is not None
            unwrapped_fields916 = fields915
            self.write("(")
            self.write("pragma")
            self.indent_sexp()
            self.newline()
            field917 = unwrapped_fields916[0]
            self.pretty_name(field917)
            field918 = unwrapped_fields916[1]
            if not len(field918) == 0:
                self.newline()
                for i920, elem919 in enumerate(field918):
                    if (i920 > 0):
                        self.newline()
                    self.pretty_term(elem919)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat937 = self._try_flat(msg, self.pretty_primitive)
        if flat937 is not None:
            assert flat937 is not None
            self.write(flat937)
            return None
        else:
            def _t1489(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1490 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1490 = None
                return _t1490
            _t1491 = _t1489(msg)
            guard_result936 = _t1491
            if guard_result936 is not None:
                self.pretty_eq(msg)
            else:
                def _t1492(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_monotype":
                        _t1493 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1493 = None
                    return _t1493
                _t1494 = _t1492(msg)
                guard_result935 = _t1494
                if guard_result935 is not None:
                    self.pretty_lt(msg)
                else:
                    def _t1495(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                            _t1496 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1496 = None
                        return _t1496
                    _t1497 = _t1495(msg)
                    guard_result934 = _t1497
                    if guard_result934 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        def _t1498(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                                _t1499 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1499 = None
                            return _t1499
                        _t1500 = _t1498(msg)
                        guard_result933 = _t1500
                        if guard_result933 is not None:
                            self.pretty_gt(msg)
                        else:
                            def _t1501(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                    _t1502 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                                else:
                                    _t1502 = None
                                return _t1502
                            _t1503 = _t1501(msg)
                            guard_result932 = _t1503
                            if guard_result932 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                def _t1504(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_add_monotype":
                                        _t1505 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1505 = None
                                    return _t1505
                                _t1506 = _t1504(msg)
                                guard_result931 = _t1506
                                if guard_result931 is not None:
                                    self.pretty_add(msg)
                                else:
                                    def _t1507(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                            _t1508 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1508 = None
                                        return _t1508
                                    _t1509 = _t1507(msg)
                                    guard_result930 = _t1509
                                    if guard_result930 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        def _t1510(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                                _t1511 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1511 = None
                                            return _t1511
                                        _t1512 = _t1510(msg)
                                        guard_result929 = _t1512
                                        if guard_result929 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            def _t1513(_dollar_dollar):
                                                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                    _t1514 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                                else:
                                                    _t1514 = None
                                                return _t1514
                                            _t1515 = _t1513(msg)
                                            guard_result928 = _t1515
                                            if guard_result928 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                def _t1516(_dollar_dollar):
                                                    return (_dollar_dollar.name, _dollar_dollar.terms,)
                                                _t1517 = _t1516(msg)
                                                fields922 = _t1517
                                                assert fields922 is not None
                                                unwrapped_fields923 = fields922
                                                self.write("(")
                                                self.write("primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field924 = unwrapped_fields923[0]
                                                self.pretty_name(field924)
                                                field925 = unwrapped_fields923[1]
                                                if not len(field925) == 0:
                                                    self.newline()
                                                    for i927, elem926 in enumerate(field925):
                                                        if (i927 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem926)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat942 = self._try_flat(msg, self.pretty_eq)
        if flat942 is not None:
            assert flat942 is not None
            self.write(flat942)
            return None
        else:
            def _t1518(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1519 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1519 = None
                return _t1519
            _t1520 = _t1518(msg)
            fields938 = _t1520
            assert fields938 is not None
            unwrapped_fields939 = fields938
            self.write("(")
            self.write("=")
            self.indent_sexp()
            self.newline()
            field940 = unwrapped_fields939[0]
            self.pretty_term(field940)
            self.newline()
            field941 = unwrapped_fields939[1]
            self.pretty_term(field941)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat947 = self._try_flat(msg, self.pretty_lt)
        if flat947 is not None:
            assert flat947 is not None
            self.write(flat947)
            return None
        else:
            def _t1521(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1522 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1522 = None
                return _t1522
            _t1523 = _t1521(msg)
            fields943 = _t1523
            assert fields943 is not None
            unwrapped_fields944 = fields943
            self.write("(")
            self.write("<")
            self.indent_sexp()
            self.newline()
            field945 = unwrapped_fields944[0]
            self.pretty_term(field945)
            self.newline()
            field946 = unwrapped_fields944[1]
            self.pretty_term(field946)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat952 = self._try_flat(msg, self.pretty_lt_eq)
        if flat952 is not None:
            assert flat952 is not None
            self.write(flat952)
            return None
        else:
            def _t1524(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                    _t1525 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1525 = None
                return _t1525
            _t1526 = _t1524(msg)
            fields948 = _t1526
            assert fields948 is not None
            unwrapped_fields949 = fields948
            self.write("(")
            self.write("<=")
            self.indent_sexp()
            self.newline()
            field950 = unwrapped_fields949[0]
            self.pretty_term(field950)
            self.newline()
            field951 = unwrapped_fields949[1]
            self.pretty_term(field951)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat957 = self._try_flat(msg, self.pretty_gt)
        if flat957 is not None:
            assert flat957 is not None
            self.write(flat957)
            return None
        else:
            def _t1527(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_monotype":
                    _t1528 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1528 = None
                return _t1528
            _t1529 = _t1527(msg)
            fields953 = _t1529
            assert fields953 is not None
            unwrapped_fields954 = fields953
            self.write("(")
            self.write(">")
            self.indent_sexp()
            self.newline()
            field955 = unwrapped_fields954[0]
            self.pretty_term(field955)
            self.newline()
            field956 = unwrapped_fields954[1]
            self.pretty_term(field956)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat962 = self._try_flat(msg, self.pretty_gt_eq)
        if flat962 is not None:
            assert flat962 is not None
            self.write(flat962)
            return None
        else:
            def _t1530(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                    _t1531 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1531 = None
                return _t1531
            _t1532 = _t1530(msg)
            fields958 = _t1532
            assert fields958 is not None
            unwrapped_fields959 = fields958
            self.write("(")
            self.write(">=")
            self.indent_sexp()
            self.newline()
            field960 = unwrapped_fields959[0]
            self.pretty_term(field960)
            self.newline()
            field961 = unwrapped_fields959[1]
            self.pretty_term(field961)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat968 = self._try_flat(msg, self.pretty_add)
        if flat968 is not None:
            assert flat968 is not None
            self.write(flat968)
            return None
        else:
            def _t1533(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_add_monotype":
                    _t1534 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1534 = None
                return _t1534
            _t1535 = _t1533(msg)
            fields963 = _t1535
            assert fields963 is not None
            unwrapped_fields964 = fields963
            self.write("(")
            self.write("+")
            self.indent_sexp()
            self.newline()
            field965 = unwrapped_fields964[0]
            self.pretty_term(field965)
            self.newline()
            field966 = unwrapped_fields964[1]
            self.pretty_term(field966)
            self.newline()
            field967 = unwrapped_fields964[2]
            self.pretty_term(field967)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat974 = self._try_flat(msg, self.pretty_minus)
        if flat974 is not None:
            assert flat974 is not None
            self.write(flat974)
            return None
        else:
            def _t1536(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                    _t1537 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1537 = None
                return _t1537
            _t1538 = _t1536(msg)
            fields969 = _t1538
            assert fields969 is not None
            unwrapped_fields970 = fields969
            self.write("(")
            self.write("-")
            self.indent_sexp()
            self.newline()
            field971 = unwrapped_fields970[0]
            self.pretty_term(field971)
            self.newline()
            field972 = unwrapped_fields970[1]
            self.pretty_term(field972)
            self.newline()
            field973 = unwrapped_fields970[2]
            self.pretty_term(field973)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat980 = self._try_flat(msg, self.pretty_multiply)
        if flat980 is not None:
            assert flat980 is not None
            self.write(flat980)
            return None
        else:
            def _t1539(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                    _t1540 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1540 = None
                return _t1540
            _t1541 = _t1539(msg)
            fields975 = _t1541
            assert fields975 is not None
            unwrapped_fields976 = fields975
            self.write("(")
            self.write("*")
            self.indent_sexp()
            self.newline()
            field977 = unwrapped_fields976[0]
            self.pretty_term(field977)
            self.newline()
            field978 = unwrapped_fields976[1]
            self.pretty_term(field978)
            self.newline()
            field979 = unwrapped_fields976[2]
            self.pretty_term(field979)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat986 = self._try_flat(msg, self.pretty_divide)
        if flat986 is not None:
            assert flat986 is not None
            self.write(flat986)
            return None
        else:
            def _t1542(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                    _t1543 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1543 = None
                return _t1543
            _t1544 = _t1542(msg)
            fields981 = _t1544
            assert fields981 is not None
            unwrapped_fields982 = fields981
            self.write("(")
            self.write("/")
            self.indent_sexp()
            self.newline()
            field983 = unwrapped_fields982[0]
            self.pretty_term(field983)
            self.newline()
            field984 = unwrapped_fields982[1]
            self.pretty_term(field984)
            self.newline()
            field985 = unwrapped_fields982[2]
            self.pretty_term(field985)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat991 = self._try_flat(msg, self.pretty_rel_term)
        if flat991 is not None:
            assert flat991 is not None
            self.write(flat991)
            return None
        else:
            def _t1545(_dollar_dollar):
                if _dollar_dollar.HasField("specialized_value"):
                    _t1546 = _dollar_dollar.specialized_value
                else:
                    _t1546 = None
                return _t1546
            _t1547 = _t1545(msg)
            deconstruct_result989 = _t1547
            if deconstruct_result989 is not None:
                assert deconstruct_result989 is not None
                unwrapped990 = deconstruct_result989
                self.pretty_specialized_value(unwrapped990)
            else:
                def _t1548(_dollar_dollar):
                    if _dollar_dollar.HasField("term"):
                        _t1549 = _dollar_dollar.term
                    else:
                        _t1549 = None
                    return _t1549
                _t1550 = _t1548(msg)
                deconstruct_result987 = _t1550
                if deconstruct_result987 is not None:
                    assert deconstruct_result987 is not None
                    unwrapped988 = deconstruct_result987
                    self.pretty_term(unwrapped988)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat993 = self._try_flat(msg, self.pretty_specialized_value)
        if flat993 is not None:
            assert flat993 is not None
            self.write(flat993)
            return None
        else:
            fields992 = msg
            self.write("#")
            self.pretty_value(fields992)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1000 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1000 is not None:
            assert flat1000 is not None
            self.write(flat1000)
            return None
        else:
            def _t1551(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1552 = _t1551(msg)
            fields994 = _t1552
            assert fields994 is not None
            unwrapped_fields995 = fields994
            self.write("(")
            self.write("relatom")
            self.indent_sexp()
            self.newline()
            field996 = unwrapped_fields995[0]
            self.pretty_name(field996)
            field997 = unwrapped_fields995[1]
            if not len(field997) == 0:
                self.newline()
                for i999, elem998 in enumerate(field997):
                    if (i999 > 0):
                        self.newline()
                    self.pretty_rel_term(elem998)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1005 = self._try_flat(msg, self.pretty_cast)
        if flat1005 is not None:
            assert flat1005 is not None
            self.write(flat1005)
            return None
        else:
            def _t1553(_dollar_dollar):
                return (_dollar_dollar.input, _dollar_dollar.result,)
            _t1554 = _t1553(msg)
            fields1001 = _t1554
            assert fields1001 is not None
            unwrapped_fields1002 = fields1001
            self.write("(")
            self.write("cast")
            self.indent_sexp()
            self.newline()
            field1003 = unwrapped_fields1002[0]
            self.pretty_term(field1003)
            self.newline()
            field1004 = unwrapped_fields1002[1]
            self.pretty_term(field1004)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1009 = self._try_flat(msg, self.pretty_attrs)
        if flat1009 is not None:
            assert flat1009 is not None
            self.write(flat1009)
            return None
        else:
            fields1006 = msg
            self.write("(")
            self.write("attrs")
            self.indent_sexp()
            if not len(fields1006) == 0:
                self.newline()
                for i1008, elem1007 in enumerate(fields1006):
                    if (i1008 > 0):
                        self.newline()
                    self.pretty_attribute(elem1007)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1016 = self._try_flat(msg, self.pretty_attribute)
        if flat1016 is not None:
            assert flat1016 is not None
            self.write(flat1016)
            return None
        else:
            def _t1555(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args,)
            _t1556 = _t1555(msg)
            fields1010 = _t1556
            assert fields1010 is not None
            unwrapped_fields1011 = fields1010
            self.write("(")
            self.write("attribute")
            self.indent_sexp()
            self.newline()
            field1012 = unwrapped_fields1011[0]
            self.pretty_name(field1012)
            field1013 = unwrapped_fields1011[1]
            if not len(field1013) == 0:
                self.newline()
                for i1015, elem1014 in enumerate(field1013):
                    if (i1015 > 0):
                        self.newline()
                    self.pretty_value(elem1014)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1023 = self._try_flat(msg, self.pretty_algorithm)
        if flat1023 is not None:
            assert flat1023 is not None
            self.write(flat1023)
            return None
        else:
            def _t1557(_dollar_dollar):
                return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            _t1558 = _t1557(msg)
            fields1017 = _t1558
            assert fields1017 is not None
            unwrapped_fields1018 = fields1017
            self.write("(")
            self.write("algorithm")
            self.indent_sexp()
            field1019 = unwrapped_fields1018[0]
            if not len(field1019) == 0:
                self.newline()
                for i1021, elem1020 in enumerate(field1019):
                    if (i1021 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1020)
            self.newline()
            field1022 = unwrapped_fields1018[1]
            self.pretty_script(field1022)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1028 = self._try_flat(msg, self.pretty_script)
        if flat1028 is not None:
            assert flat1028 is not None
            self.write(flat1028)
            return None
        else:
            def _t1559(_dollar_dollar):
                return _dollar_dollar.constructs
            _t1560 = _t1559(msg)
            fields1024 = _t1560
            assert fields1024 is not None
            unwrapped_fields1025 = fields1024
            self.write("(")
            self.write("script")
            self.indent_sexp()
            if not len(unwrapped_fields1025) == 0:
                self.newline()
                for i1027, elem1026 in enumerate(unwrapped_fields1025):
                    if (i1027 > 0):
                        self.newline()
                    self.pretty_construct(elem1026)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1033 = self._try_flat(msg, self.pretty_construct)
        if flat1033 is not None:
            assert flat1033 is not None
            self.write(flat1033)
            return None
        else:
            def _t1561(_dollar_dollar):
                if _dollar_dollar.HasField("loop"):
                    _t1562 = _dollar_dollar.loop
                else:
                    _t1562 = None
                return _t1562
            _t1563 = _t1561(msg)
            deconstruct_result1031 = _t1563
            if deconstruct_result1031 is not None:
                assert deconstruct_result1031 is not None
                unwrapped1032 = deconstruct_result1031
                self.pretty_loop(unwrapped1032)
            else:
                def _t1564(_dollar_dollar):
                    if _dollar_dollar.HasField("instruction"):
                        _t1565 = _dollar_dollar.instruction
                    else:
                        _t1565 = None
                    return _t1565
                _t1566 = _t1564(msg)
                deconstruct_result1029 = _t1566
                if deconstruct_result1029 is not None:
                    assert deconstruct_result1029 is not None
                    unwrapped1030 = deconstruct_result1029
                    self.pretty_instruction(unwrapped1030)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1038 = self._try_flat(msg, self.pretty_loop)
        if flat1038 is not None:
            assert flat1038 is not None
            self.write(flat1038)
            return None
        else:
            def _t1567(_dollar_dollar):
                return (_dollar_dollar.init, _dollar_dollar.body,)
            _t1568 = _t1567(msg)
            fields1034 = _t1568
            assert fields1034 is not None
            unwrapped_fields1035 = fields1034
            self.write("(")
            self.write("loop")
            self.indent_sexp()
            self.newline()
            field1036 = unwrapped_fields1035[0]
            self.pretty_init(field1036)
            self.newline()
            field1037 = unwrapped_fields1035[1]
            self.pretty_script(field1037)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1042 = self._try_flat(msg, self.pretty_init)
        if flat1042 is not None:
            assert flat1042 is not None
            self.write(flat1042)
            return None
        else:
            fields1039 = msg
            self.write("(")
            self.write("init")
            self.indent_sexp()
            if not len(fields1039) == 0:
                self.newline()
                for i1041, elem1040 in enumerate(fields1039):
                    if (i1041 > 0):
                        self.newline()
                    self.pretty_instruction(elem1040)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1053 = self._try_flat(msg, self.pretty_instruction)
        if flat1053 is not None:
            assert flat1053 is not None
            self.write(flat1053)
            return None
        else:
            def _t1569(_dollar_dollar):
                if _dollar_dollar.HasField("assign"):
                    _t1570 = _dollar_dollar.assign
                else:
                    _t1570 = None
                return _t1570
            _t1571 = _t1569(msg)
            deconstruct_result1051 = _t1571
            if deconstruct_result1051 is not None:
                assert deconstruct_result1051 is not None
                unwrapped1052 = deconstruct_result1051
                self.pretty_assign(unwrapped1052)
            else:
                def _t1572(_dollar_dollar):
                    if _dollar_dollar.HasField("upsert"):
                        _t1573 = _dollar_dollar.upsert
                    else:
                        _t1573 = None
                    return _t1573
                _t1574 = _t1572(msg)
                deconstruct_result1049 = _t1574
                if deconstruct_result1049 is not None:
                    assert deconstruct_result1049 is not None
                    unwrapped1050 = deconstruct_result1049
                    self.pretty_upsert(unwrapped1050)
                else:
                    def _t1575(_dollar_dollar):
                        if _dollar_dollar.HasField("break"):
                            _t1576 = getattr(_dollar_dollar, 'break')
                        else:
                            _t1576 = None
                        return _t1576
                    _t1577 = _t1575(msg)
                    deconstruct_result1047 = _t1577
                    if deconstruct_result1047 is not None:
                        assert deconstruct_result1047 is not None
                        unwrapped1048 = deconstruct_result1047
                        self.pretty_break(unwrapped1048)
                    else:
                        def _t1578(_dollar_dollar):
                            if _dollar_dollar.HasField("monoid_def"):
                                _t1579 = _dollar_dollar.monoid_def
                            else:
                                _t1579 = None
                            return _t1579
                        _t1580 = _t1578(msg)
                        deconstruct_result1045 = _t1580
                        if deconstruct_result1045 is not None:
                            assert deconstruct_result1045 is not None
                            unwrapped1046 = deconstruct_result1045
                            self.pretty_monoid_def(unwrapped1046)
                        else:
                            def _t1581(_dollar_dollar):
                                if _dollar_dollar.HasField("monus_def"):
                                    _t1582 = _dollar_dollar.monus_def
                                else:
                                    _t1582 = None
                                return _t1582
                            _t1583 = _t1581(msg)
                            deconstruct_result1043 = _t1583
                            if deconstruct_result1043 is not None:
                                assert deconstruct_result1043 is not None
                                unwrapped1044 = deconstruct_result1043
                                self.pretty_monus_def(unwrapped1044)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1060 = self._try_flat(msg, self.pretty_assign)
        if flat1060 is not None:
            assert flat1060 is not None
            self.write(flat1060)
            return None
        else:
            def _t1584(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1585 = _dollar_dollar.attrs
                else:
                    _t1585 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1585,)
            _t1586 = _t1584(msg)
            fields1054 = _t1586
            assert fields1054 is not None
            unwrapped_fields1055 = fields1054
            self.write("(")
            self.write("assign")
            self.indent_sexp()
            self.newline()
            field1056 = unwrapped_fields1055[0]
            self.pretty_relation_id(field1056)
            self.newline()
            field1057 = unwrapped_fields1055[1]
            self.pretty_abstraction(field1057)
            field1058 = unwrapped_fields1055[2]
            if field1058 is not None:
                self.newline()
                assert field1058 is not None
                opt_val1059 = field1058
                self.pretty_attrs(opt_val1059)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1067 = self._try_flat(msg, self.pretty_upsert)
        if flat1067 is not None:
            assert flat1067 is not None
            self.write(flat1067)
            return None
        else:
            def _t1587(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1588 = _dollar_dollar.attrs
                else:
                    _t1588 = None
                return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1588,)
            _t1589 = _t1587(msg)
            fields1061 = _t1589
            assert fields1061 is not None
            unwrapped_fields1062 = fields1061
            self.write("(")
            self.write("upsert")
            self.indent_sexp()
            self.newline()
            field1063 = unwrapped_fields1062[0]
            self.pretty_relation_id(field1063)
            self.newline()
            field1064 = unwrapped_fields1062[1]
            self.pretty_abstraction_with_arity(field1064)
            field1065 = unwrapped_fields1062[2]
            if field1065 is not None:
                self.newline()
                assert field1065 is not None
                opt_val1066 = field1065
                self.pretty_attrs(opt_val1066)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1072 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1072 is not None:
            assert flat1072 is not None
            self.write(flat1072)
            return None
        else:
            def _t1590(_dollar_dollar):
                _t1591 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
                return (_t1591, _dollar_dollar[0].value,)
            _t1592 = _t1590(msg)
            fields1068 = _t1592
            assert fields1068 is not None
            unwrapped_fields1069 = fields1068
            self.write("(")
            self.indent()
            field1070 = unwrapped_fields1069[0]
            self.pretty_bindings(field1070)
            self.newline()
            field1071 = unwrapped_fields1069[1]
            self.pretty_formula(field1071)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1079 = self._try_flat(msg, self.pretty_break)
        if flat1079 is not None:
            assert flat1079 is not None
            self.write(flat1079)
            return None
        else:
            def _t1593(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1594 = _dollar_dollar.attrs
                else:
                    _t1594 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1594,)
            _t1595 = _t1593(msg)
            fields1073 = _t1595
            assert fields1073 is not None
            unwrapped_fields1074 = fields1073
            self.write("(")
            self.write("break")
            self.indent_sexp()
            self.newline()
            field1075 = unwrapped_fields1074[0]
            self.pretty_relation_id(field1075)
            self.newline()
            field1076 = unwrapped_fields1074[1]
            self.pretty_abstraction(field1076)
            field1077 = unwrapped_fields1074[2]
            if field1077 is not None:
                self.newline()
                assert field1077 is not None
                opt_val1078 = field1077
                self.pretty_attrs(opt_val1078)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1087 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1087 is not None:
            assert flat1087 is not None
            self.write(flat1087)
            return None
        else:
            def _t1596(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1597 = _dollar_dollar.attrs
                else:
                    _t1597 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1597,)
            _t1598 = _t1596(msg)
            fields1080 = _t1598
            assert fields1080 is not None
            unwrapped_fields1081 = fields1080
            self.write("(")
            self.write("monoid")
            self.indent_sexp()
            self.newline()
            field1082 = unwrapped_fields1081[0]
            self.pretty_monoid(field1082)
            self.newline()
            field1083 = unwrapped_fields1081[1]
            self.pretty_relation_id(field1083)
            self.newline()
            field1084 = unwrapped_fields1081[2]
            self.pretty_abstraction_with_arity(field1084)
            field1085 = unwrapped_fields1081[3]
            if field1085 is not None:
                self.newline()
                assert field1085 is not None
                opt_val1086 = field1085
                self.pretty_attrs(opt_val1086)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1096 = self._try_flat(msg, self.pretty_monoid)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            def _t1599(_dollar_dollar):
                if _dollar_dollar.HasField("or_monoid"):
                    _t1600 = _dollar_dollar.or_monoid
                else:
                    _t1600 = None
                return _t1600
            _t1601 = _t1599(msg)
            deconstruct_result1094 = _t1601
            if deconstruct_result1094 is not None:
                assert deconstruct_result1094 is not None
                unwrapped1095 = deconstruct_result1094
                self.pretty_or_monoid(unwrapped1095)
            else:
                def _t1602(_dollar_dollar):
                    if _dollar_dollar.HasField("min_monoid"):
                        _t1603 = _dollar_dollar.min_monoid
                    else:
                        _t1603 = None
                    return _t1603
                _t1604 = _t1602(msg)
                deconstruct_result1092 = _t1604
                if deconstruct_result1092 is not None:
                    assert deconstruct_result1092 is not None
                    unwrapped1093 = deconstruct_result1092
                    self.pretty_min_monoid(unwrapped1093)
                else:
                    def _t1605(_dollar_dollar):
                        if _dollar_dollar.HasField("max_monoid"):
                            _t1606 = _dollar_dollar.max_monoid
                        else:
                            _t1606 = None
                        return _t1606
                    _t1607 = _t1605(msg)
                    deconstruct_result1090 = _t1607
                    if deconstruct_result1090 is not None:
                        assert deconstruct_result1090 is not None
                        unwrapped1091 = deconstruct_result1090
                        self.pretty_max_monoid(unwrapped1091)
                    else:
                        def _t1608(_dollar_dollar):
                            if _dollar_dollar.HasField("sum_monoid"):
                                _t1609 = _dollar_dollar.sum_monoid
                            else:
                                _t1609 = None
                            return _t1609
                        _t1610 = _t1608(msg)
                        deconstruct_result1088 = _t1610
                        if deconstruct_result1088 is not None:
                            assert deconstruct_result1088 is not None
                            unwrapped1089 = deconstruct_result1088
                            self.pretty_sum_monoid(unwrapped1089)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1097 = msg
        self.write("(")
        self.write("or")
        self.write(")")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1100 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            def _t1611(_dollar_dollar):
                return _dollar_dollar.type
            _t1612 = _t1611(msg)
            fields1098 = _t1612
            assert fields1098 is not None
            unwrapped_fields1099 = fields1098
            self.write("(")
            self.write("min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1099)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1103 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1103 is not None:
            assert flat1103 is not None
            self.write(flat1103)
            return None
        else:
            def _t1613(_dollar_dollar):
                return _dollar_dollar.type
            _t1614 = _t1613(msg)
            fields1101 = _t1614
            assert fields1101 is not None
            unwrapped_fields1102 = fields1101
            self.write("(")
            self.write("max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1102)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1106 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1106 is not None:
            assert flat1106 is not None
            self.write(flat1106)
            return None
        else:
            def _t1615(_dollar_dollar):
                return _dollar_dollar.type
            _t1616 = _t1615(msg)
            fields1104 = _t1616
            assert fields1104 is not None
            unwrapped_fields1105 = fields1104
            self.write("(")
            self.write("sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1105)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1114 = self._try_flat(msg, self.pretty_monus_def)
        if flat1114 is not None:
            assert flat1114 is not None
            self.write(flat1114)
            return None
        else:
            def _t1617(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1618 = _dollar_dollar.attrs
                else:
                    _t1618 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1618,)
            _t1619 = _t1617(msg)
            fields1107 = _t1619
            assert fields1107 is not None
            unwrapped_fields1108 = fields1107
            self.write("(")
            self.write("monus")
            self.indent_sexp()
            self.newline()
            field1109 = unwrapped_fields1108[0]
            self.pretty_monoid(field1109)
            self.newline()
            field1110 = unwrapped_fields1108[1]
            self.pretty_relation_id(field1110)
            self.newline()
            field1111 = unwrapped_fields1108[2]
            self.pretty_abstraction_with_arity(field1111)
            field1112 = unwrapped_fields1108[3]
            if field1112 is not None:
                self.newline()
                assert field1112 is not None
                opt_val1113 = field1112
                self.pretty_attrs(opt_val1113)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1121 = self._try_flat(msg, self.pretty_constraint)
        if flat1121 is not None:
            assert flat1121 is not None
            self.write(flat1121)
            return None
        else:
            def _t1620(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            _t1621 = _t1620(msg)
            fields1115 = _t1621
            assert fields1115 is not None
            unwrapped_fields1116 = fields1115
            self.write("(")
            self.write("functional_dependency")
            self.indent_sexp()
            self.newline()
            field1117 = unwrapped_fields1116[0]
            self.pretty_relation_id(field1117)
            self.newline()
            field1118 = unwrapped_fields1116[1]
            self.pretty_abstraction(field1118)
            self.newline()
            field1119 = unwrapped_fields1116[2]
            self.pretty_functional_dependency_keys(field1119)
            self.newline()
            field1120 = unwrapped_fields1116[3]
            self.pretty_functional_dependency_values(field1120)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1125 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1125 is not None:
            assert flat1125 is not None
            self.write(flat1125)
            return None
        else:
            fields1122 = msg
            self.write("(")
            self.write("keys")
            self.indent_sexp()
            if not len(fields1122) == 0:
                self.newline()
                for i1124, elem1123 in enumerate(fields1122):
                    if (i1124 > 0):
                        self.newline()
                    self.pretty_var(elem1123)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1129 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1129 is not None:
            assert flat1129 is not None
            self.write(flat1129)
            return None
        else:
            fields1126 = msg
            self.write("(")
            self.write("values")
            self.indent_sexp()
            if not len(fields1126) == 0:
                self.newline()
                for i1128, elem1127 in enumerate(fields1126):
                    if (i1128 > 0):
                        self.newline()
                    self.pretty_var(elem1127)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1136 = self._try_flat(msg, self.pretty_data)
        if flat1136 is not None:
            assert flat1136 is not None
            self.write(flat1136)
            return None
        else:
            def _t1622(_dollar_dollar):
                if _dollar_dollar.HasField("rel_edb"):
                    _t1623 = _dollar_dollar.rel_edb
                else:
                    _t1623 = None
                return _t1623
            _t1624 = _t1622(msg)
            deconstruct_result1134 = _t1624
            if deconstruct_result1134 is not None:
                assert deconstruct_result1134 is not None
                unwrapped1135 = deconstruct_result1134
                self.pretty_rel_edb(unwrapped1135)
            else:
                def _t1625(_dollar_dollar):
                    if _dollar_dollar.HasField("betree_relation"):
                        _t1626 = _dollar_dollar.betree_relation
                    else:
                        _t1626 = None
                    return _t1626
                _t1627 = _t1625(msg)
                deconstruct_result1132 = _t1627
                if deconstruct_result1132 is not None:
                    assert deconstruct_result1132 is not None
                    unwrapped1133 = deconstruct_result1132
                    self.pretty_betree_relation(unwrapped1133)
                else:
                    def _t1628(_dollar_dollar):
                        if _dollar_dollar.HasField("csv_data"):
                            _t1629 = _dollar_dollar.csv_data
                        else:
                            _t1629 = None
                        return _t1629
                    _t1630 = _t1628(msg)
                    deconstruct_result1130 = _t1630
                    if deconstruct_result1130 is not None:
                        assert deconstruct_result1130 is not None
                        unwrapped1131 = deconstruct_result1130
                        self.pretty_csv_data(unwrapped1131)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB):
        flat1142 = self._try_flat(msg, self.pretty_rel_edb)
        if flat1142 is not None:
            assert flat1142 is not None
            self.write(flat1142)
            return None
        else:
            def _t1631(_dollar_dollar):
                return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            _t1632 = _t1631(msg)
            fields1137 = _t1632
            assert fields1137 is not None
            unwrapped_fields1138 = fields1137
            self.write("(")
            self.write("rel_edb")
            self.indent_sexp()
            self.newline()
            field1139 = unwrapped_fields1138[0]
            self.pretty_relation_id(field1139)
            self.newline()
            field1140 = unwrapped_fields1138[1]
            self.pretty_rel_edb_path(field1140)
            self.newline()
            field1141 = unwrapped_fields1138[2]
            self.pretty_rel_edb_types(field1141)
            self.dedent()
            self.write(")")

    def pretty_rel_edb_path(self, msg: Sequence[str]):
        flat1146 = self._try_flat(msg, self.pretty_rel_edb_path)
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
                self.write(self.format_string_value(elem1144))
            self.dedent()
            self.write("]")

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1150 = self._try_flat(msg, self.pretty_rel_edb_types)
        if flat1150 is not None:
            assert flat1150 is not None
            self.write(flat1150)
            return None
        else:
            fields1147 = msg
            self.write("[")
            self.indent()
            for i1149, elem1148 in enumerate(fields1147):
                if (i1149 > 0):
                    self.newline()
                self.pretty_type(elem1148)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1155 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1155 is not None:
            assert flat1155 is not None
            self.write(flat1155)
            return None
        else:
            def _t1633(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_info,)
            _t1634 = _t1633(msg)
            fields1151 = _t1634
            assert fields1151 is not None
            unwrapped_fields1152 = fields1151
            self.write("(")
            self.write("betree_relation")
            self.indent_sexp()
            self.newline()
            field1153 = unwrapped_fields1152[0]
            self.pretty_relation_id(field1153)
            self.newline()
            field1154 = unwrapped_fields1152[1]
            self.pretty_betree_info(field1154)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1161 = self._try_flat(msg, self.pretty_betree_info)
        if flat1161 is not None:
            assert flat1161 is not None
            self.write(flat1161)
            return None
        else:
            def _t1635(_dollar_dollar):
                _t1636 = self.deconstruct_betree_info_config(_dollar_dollar)
                return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1636,)
            _t1637 = _t1635(msg)
            fields1156 = _t1637
            assert fields1156 is not None
            unwrapped_fields1157 = fields1156
            self.write("(")
            self.write("betree_info")
            self.indent_sexp()
            self.newline()
            field1158 = unwrapped_fields1157[0]
            self.pretty_betree_info_key_types(field1158)
            self.newline()
            field1159 = unwrapped_fields1157[1]
            self.pretty_betree_info_value_types(field1159)
            self.newline()
            field1160 = unwrapped_fields1157[2]
            self.pretty_config_dict(field1160)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1165 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1165 is not None:
            assert flat1165 is not None
            self.write(flat1165)
            return None
        else:
            fields1162 = msg
            self.write("(")
            self.write("key_types")
            self.indent_sexp()
            if not len(fields1162) == 0:
                self.newline()
                for i1164, elem1163 in enumerate(fields1162):
                    if (i1164 > 0):
                        self.newline()
                    self.pretty_type(elem1163)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1169 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1169 is not None:
            assert flat1169 is not None
            self.write(flat1169)
            return None
        else:
            fields1166 = msg
            self.write("(")
            self.write("value_types")
            self.indent_sexp()
            if not len(fields1166) == 0:
                self.newline()
                for i1168, elem1167 in enumerate(fields1166):
                    if (i1168 > 0):
                        self.newline()
                    self.pretty_type(elem1167)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1176 = self._try_flat(msg, self.pretty_csv_data)
        if flat1176 is not None:
            assert flat1176 is not None
            self.write(flat1176)
            return None
        else:
            def _t1638(_dollar_dollar):
                return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            _t1639 = _t1638(msg)
            fields1170 = _t1639
            assert fields1170 is not None
            unwrapped_fields1171 = fields1170
            self.write("(")
            self.write("csv_data")
            self.indent_sexp()
            self.newline()
            field1172 = unwrapped_fields1171[0]
            self.pretty_csvlocator(field1172)
            self.newline()
            field1173 = unwrapped_fields1171[1]
            self.pretty_csv_config(field1173)
            self.newline()
            field1174 = unwrapped_fields1171[2]
            self.pretty_csv_columns(field1174)
            self.newline()
            field1175 = unwrapped_fields1171[3]
            self.pretty_csv_asof(field1175)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1183 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1183 is not None:
            assert flat1183 is not None
            self.write(flat1183)
            return None
        else:
            def _t1640(_dollar_dollar):
                if not len(_dollar_dollar.paths) == 0:
                    _t1641 = _dollar_dollar.paths
                else:
                    _t1641 = None
                if _dollar_dollar.inline_data.decode('utf-8') != "":
                    _t1642 = _dollar_dollar.inline_data.decode('utf-8')
                else:
                    _t1642 = None
                return (_t1641, _t1642,)
            _t1643 = _t1640(msg)
            fields1177 = _t1643
            assert fields1177 is not None
            unwrapped_fields1178 = fields1177
            self.write("(")
            self.write("csv_locator")
            self.indent_sexp()
            field1179 = unwrapped_fields1178[0]
            if field1179 is not None:
                self.newline()
                assert field1179 is not None
                opt_val1180 = field1179
                self.pretty_csv_locator_paths(opt_val1180)
            field1181 = unwrapped_fields1178[1]
            if field1181 is not None:
                self.newline()
                assert field1181 is not None
                opt_val1182 = field1181
                self.pretty_csv_locator_inline_data(opt_val1182)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1187 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1187 is not None:
            assert flat1187 is not None
            self.write(flat1187)
            return None
        else:
            fields1184 = msg
            self.write("(")
            self.write("paths")
            self.indent_sexp()
            if not len(fields1184) == 0:
                self.newline()
                for i1186, elem1185 in enumerate(fields1184):
                    if (i1186 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1185))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1189 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1189 is not None:
            assert flat1189 is not None
            self.write(flat1189)
            return None
        else:
            fields1188 = msg
            self.write("(")
            self.write("inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1188))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1192 = self._try_flat(msg, self.pretty_csv_config)
        if flat1192 is not None:
            assert flat1192 is not None
            self.write(flat1192)
            return None
        else:
            def _t1644(_dollar_dollar):
                _t1645 = self.deconstruct_csv_config(_dollar_dollar)
                return _t1645
            _t1646 = _t1644(msg)
            fields1190 = _t1646
            assert fields1190 is not None
            unwrapped_fields1191 = fields1190
            self.write("(")
            self.write("csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1191)
            self.dedent()
            self.write(")")

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]):
        flat1196 = self._try_flat(msg, self.pretty_csv_columns)
        if flat1196 is not None:
            assert flat1196 is not None
            self.write(flat1196)
            return None
        else:
            fields1193 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1193) == 0:
                self.newline()
                for i1195, elem1194 in enumerate(fields1193):
                    if (i1195 > 0):
                        self.newline()
                    self.pretty_csv_column(elem1194)
            self.dedent()
            self.write(")")

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn):
        flat1202 = self._try_flat(msg, self.pretty_csv_column)
        if flat1202 is not None:
            assert flat1202 is not None
            self.write(flat1202)
            return None
        else:
            def _t1647(_dollar_dollar):
                _t1648 = self.deconstruct_csv_column_tail(_dollar_dollar)
                return (_dollar_dollar.column_path, _t1648,)
            _t1649 = _t1647(msg)
            fields1197 = _t1649
            assert fields1197 is not None
            unwrapped_fields1198 = fields1197
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1199 = unwrapped_fields1198[0]
            self.pretty_csv_column_path(field1199)
            field1200 = unwrapped_fields1198[1]
            if field1200 is not None:
                self.newline()
                assert field1200 is not None
                opt_val1201 = field1200
                self.pretty_csv_column_tail(opt_val1201)
            self.dedent()
            self.write(")")

    def pretty_csv_column_path(self, msg: Sequence[str]):
        flat1209 = self._try_flat(msg, self.pretty_csv_column_path)
        if flat1209 is not None:
            assert flat1209 is not None
            self.write(flat1209)
            return None
        else:
            def _t1650(_dollar_dollar):
                if len(_dollar_dollar) == 1:
                    _t1651 = _dollar_dollar[0]
                else:
                    _t1651 = None
                return _t1651
            _t1652 = _t1650(msg)
            deconstruct_result1207 = _t1652
            if deconstruct_result1207 is not None:
                assert deconstruct_result1207 is not None
                unwrapped1208 = deconstruct_result1207
                self.write(self.format_string_value(unwrapped1208))
            else:
                def _t1653(_dollar_dollar):
                    if len(_dollar_dollar) != 1:
                        _t1654 = _dollar_dollar
                    else:
                        _t1654 = None
                    return _t1654
                _t1655 = _t1653(msg)
                deconstruct_result1203 = _t1655
                if deconstruct_result1203 is not None:
                    assert deconstruct_result1203 is not None
                    unwrapped1204 = deconstruct_result1203
                    self.write("[")
                    self.indent()
                    for i1206, elem1205 in enumerate(unwrapped1204):
                        if (i1206 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1205))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for csv_column_path")

    def pretty_csv_column_tail(self, msg: tuple[Optional[logic_pb2.RelationId], Sequence[logic_pb2.Type]]):
        flat1220 = self._try_flat(msg, self.pretty_csv_column_tail)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            def _t1656(_dollar_dollar):
                if _dollar_dollar[0] is not None:
                    _t1657 = (_dollar_dollar[0], _dollar_dollar[1],)
                else:
                    _t1657 = None
                return _t1657
            _t1658 = _t1656(msg)
            deconstruct_result1214 = _t1658
            if deconstruct_result1214 is not None:
                assert deconstruct_result1214 is not None
                unwrapped1215 = deconstruct_result1214
                field1216 = unwrapped1215[0]
                self.pretty_relation_id(field1216)
                self.write(" ")
                self.write("[")
                field1217 = unwrapped1215[1]
                for i1219, elem1218 in enumerate(field1217):
                    if (i1219 > 0):
                        self.newline()
                    self.pretty_type(elem1218)
                self.write("]")
            else:
                def _t1659(_dollar_dollar):
                    return _dollar_dollar[1]
                _t1660 = _t1659(msg)
                fields1210 = _t1660
                assert fields1210 is not None
                unwrapped_fields1211 = fields1210
                self.write("[")
                self.indent()
                for i1213, elem1212 in enumerate(unwrapped_fields1211):
                    if (i1213 > 0):
                        self.newline()
                    self.pretty_type(elem1212)
                self.dedent()
                self.write("]")

    def pretty_csv_asof(self, msg: str):
        flat1222 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1222 is not None:
            assert flat1222 is not None
            self.write(flat1222)
            return None
        else:
            fields1221 = msg
            self.write("(")
            self.write("asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1221))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1225 = self._try_flat(msg, self.pretty_undefine)
        if flat1225 is not None:
            assert flat1225 is not None
            self.write(flat1225)
            return None
        else:
            def _t1661(_dollar_dollar):
                return _dollar_dollar.fragment_id
            _t1662 = _t1661(msg)
            fields1223 = _t1662
            assert fields1223 is not None
            unwrapped_fields1224 = fields1223
            self.write("(")
            self.write("undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1224)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1230 = self._try_flat(msg, self.pretty_context)
        if flat1230 is not None:
            assert flat1230 is not None
            self.write(flat1230)
            return None
        else:
            def _t1663(_dollar_dollar):
                return _dollar_dollar.relations
            _t1664 = _t1663(msg)
            fields1226 = _t1664
            assert fields1226 is not None
            unwrapped_fields1227 = fields1226
            self.write("(")
            self.write("context")
            self.indent_sexp()
            if not len(unwrapped_fields1227) == 0:
                self.newline()
                for i1229, elem1228 in enumerate(unwrapped_fields1227):
                    if (i1229 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1228)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1235 = self._try_flat(msg, self.pretty_snapshot)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            def _t1665(_dollar_dollar):
                return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            _t1666 = _t1665(msg)
            fields1231 = _t1666
            assert fields1231 is not None
            unwrapped_fields1232 = fields1231
            self.write("(")
            self.write("snapshot")
            self.indent_sexp()
            self.newline()
            field1233 = unwrapped_fields1232[0]
            self.pretty_rel_edb_path(field1233)
            self.newline()
            field1234 = unwrapped_fields1232[1]
            self.pretty_relation_id(field1234)
            self.dedent()
            self.write(")")

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1239 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1239 is not None:
            assert flat1239 is not None
            self.write(flat1239)
            return None
        else:
            fields1236 = msg
            self.write("(")
            self.write("reads")
            self.indent_sexp()
            if not len(fields1236) == 0:
                self.newline()
                for i1238, elem1237 in enumerate(fields1236):
                    if (i1238 > 0):
                        self.newline()
                    self.pretty_read(elem1237)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1250 = self._try_flat(msg, self.pretty_read)
        if flat1250 is not None:
            assert flat1250 is not None
            self.write(flat1250)
            return None
        else:
            def _t1667(_dollar_dollar):
                if _dollar_dollar.HasField("demand"):
                    _t1668 = _dollar_dollar.demand
                else:
                    _t1668 = None
                return _t1668
            _t1669 = _t1667(msg)
            deconstruct_result1248 = _t1669
            if deconstruct_result1248 is not None:
                assert deconstruct_result1248 is not None
                unwrapped1249 = deconstruct_result1248
                self.pretty_demand(unwrapped1249)
            else:
                def _t1670(_dollar_dollar):
                    if _dollar_dollar.HasField("output"):
                        _t1671 = _dollar_dollar.output
                    else:
                        _t1671 = None
                    return _t1671
                _t1672 = _t1670(msg)
                deconstruct_result1246 = _t1672
                if deconstruct_result1246 is not None:
                    assert deconstruct_result1246 is not None
                    unwrapped1247 = deconstruct_result1246
                    self.pretty_output(unwrapped1247)
                else:
                    def _t1673(_dollar_dollar):
                        if _dollar_dollar.HasField("what_if"):
                            _t1674 = _dollar_dollar.what_if
                        else:
                            _t1674 = None
                        return _t1674
                    _t1675 = _t1673(msg)
                    deconstruct_result1244 = _t1675
                    if deconstruct_result1244 is not None:
                        assert deconstruct_result1244 is not None
                        unwrapped1245 = deconstruct_result1244
                        self.pretty_what_if(unwrapped1245)
                    else:
                        def _t1676(_dollar_dollar):
                            if _dollar_dollar.HasField("abort"):
                                _t1677 = _dollar_dollar.abort
                            else:
                                _t1677 = None
                            return _t1677
                        _t1678 = _t1676(msg)
                        deconstruct_result1242 = _t1678
                        if deconstruct_result1242 is not None:
                            assert deconstruct_result1242 is not None
                            unwrapped1243 = deconstruct_result1242
                            self.pretty_abort(unwrapped1243)
                        else:
                            def _t1679(_dollar_dollar):
                                if _dollar_dollar.HasField("export"):
                                    _t1680 = _dollar_dollar.export
                                else:
                                    _t1680 = None
                                return _t1680
                            _t1681 = _t1679(msg)
                            deconstruct_result1240 = _t1681
                            if deconstruct_result1240 is not None:
                                assert deconstruct_result1240 is not None
                                unwrapped1241 = deconstruct_result1240
                                self.pretty_export(unwrapped1241)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1253 = self._try_flat(msg, self.pretty_demand)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            def _t1682(_dollar_dollar):
                return _dollar_dollar.relation_id
            _t1683 = _t1682(msg)
            fields1251 = _t1683
            assert fields1251 is not None
            unwrapped_fields1252 = fields1251
            self.write("(")
            self.write("demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1252)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1258 = self._try_flat(msg, self.pretty_output)
        if flat1258 is not None:
            assert flat1258 is not None
            self.write(flat1258)
            return None
        else:
            def _t1684(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_id,)
            _t1685 = _t1684(msg)
            fields1254 = _t1685
            assert fields1254 is not None
            unwrapped_fields1255 = fields1254
            self.write("(")
            self.write("output")
            self.indent_sexp()
            self.newline()
            field1256 = unwrapped_fields1255[0]
            self.pretty_name(field1256)
            self.newline()
            field1257 = unwrapped_fields1255[1]
            self.pretty_relation_id(field1257)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1263 = self._try_flat(msg, self.pretty_what_if)
        if flat1263 is not None:
            assert flat1263 is not None
            self.write(flat1263)
            return None
        else:
            def _t1686(_dollar_dollar):
                return (_dollar_dollar.branch, _dollar_dollar.epoch,)
            _t1687 = _t1686(msg)
            fields1259 = _t1687
            assert fields1259 is not None
            unwrapped_fields1260 = fields1259
            self.write("(")
            self.write("what_if")
            self.indent_sexp()
            self.newline()
            field1261 = unwrapped_fields1260[0]
            self.pretty_name(field1261)
            self.newline()
            field1262 = unwrapped_fields1260[1]
            self.pretty_epoch(field1262)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1269 = self._try_flat(msg, self.pretty_abort)
        if flat1269 is not None:
            assert flat1269 is not None
            self.write(flat1269)
            return None
        else:
            def _t1688(_dollar_dollar):
                if _dollar_dollar.name != "abort":
                    _t1689 = _dollar_dollar.name
                else:
                    _t1689 = None
                return (_t1689, _dollar_dollar.relation_id,)
            _t1690 = _t1688(msg)
            fields1264 = _t1690
            assert fields1264 is not None
            unwrapped_fields1265 = fields1264
            self.write("(")
            self.write("abort")
            self.indent_sexp()
            field1266 = unwrapped_fields1265[0]
            if field1266 is not None:
                self.newline()
                assert field1266 is not None
                opt_val1267 = field1266
                self.pretty_name(opt_val1267)
            self.newline()
            field1268 = unwrapped_fields1265[1]
            self.pretty_relation_id(field1268)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1272 = self._try_flat(msg, self.pretty_export)
        if flat1272 is not None:
            assert flat1272 is not None
            self.write(flat1272)
            return None
        else:
            def _t1691(_dollar_dollar):
                return _dollar_dollar.csv_config
            _t1692 = _t1691(msg)
            fields1270 = _t1692
            assert fields1270 is not None
            unwrapped_fields1271 = fields1270
            self.write("(")
            self.write("export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1271)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1278 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            def _t1693(_dollar_dollar):
                _t1694 = self.deconstruct_export_csv_config(_dollar_dollar)
                return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1694,)
            _t1695 = _t1693(msg)
            fields1273 = _t1695
            assert fields1273 is not None
            unwrapped_fields1274 = fields1273
            self.write("(")
            self.write("export_csv_config")
            self.indent_sexp()
            self.newline()
            field1275 = unwrapped_fields1274[0]
            self.pretty_export_csv_path(field1275)
            self.newline()
            field1276 = unwrapped_fields1274[1]
            self.pretty_export_csv_columns(field1276)
            self.newline()
            field1277 = unwrapped_fields1274[2]
            self.pretty_config_dict(field1277)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1280 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1280 is not None:
            assert flat1280 is not None
            self.write(flat1280)
            return None
        else:
            fields1279 = msg
            self.write("(")
            self.write("path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1279))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1284 = self._try_flat(msg, self.pretty_export_csv_columns)
        if flat1284 is not None:
            assert flat1284 is not None
            self.write(flat1284)
            return None
        else:
            fields1281 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1281) == 0:
                self.newline()
                for i1283, elem1282 in enumerate(fields1281):
                    if (i1283 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1282)
            self.dedent()
            self.write(")")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1289 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1289 is not None:
            assert flat1289 is not None
            self.write(flat1289)
            return None
        else:
            def _t1696(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            _t1697 = _t1696(msg)
            fields1285 = _t1697
            assert fields1285 is not None
            unwrapped_fields1286 = fields1285
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1287 = unwrapped_fields1286[0]
            self.write(self.format_string_value(field1287))
            self.newline()
            field1288 = unwrapped_fields1286[1]
            self.pretty_relation_id(field1288)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1736 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1736)
            self.write(" ")
            self.write(self.format_string_value(msg.orig_names[_idx]))
            self.write(")")
        self.write(")")
        self.dedent()

    def pretty_be_tree_config(self, msg: logic_pb2.BeTreeConfig):
        self.write("(be_tree_config")
        self.indent_sexp()
        self.newline()
        self.write(":epsilon ")
        self.write(str(msg.epsilon))
        self.newline()
        self.write(":max_pivots ")
        self.write(str(msg.max_pivots))
        self.newline()
        self.write(":max_deltas ")
        self.write(str(msg.max_deltas))
        self.newline()
        self.write(":max_leaf ")
        self.write(str(msg.max_leaf))
        self.write(")")
        self.dedent()

    def pretty_be_tree_locator(self, msg: logic_pb2.BeTreeLocator):
        self.write("(be_tree_locator")
        self.indent_sexp()
        self.newline()
        self.write(":element_count ")
        self.write(str(msg.element_count))
        self.newline()
        self.write(":tree_height ")
        self.write(str(msg.tree_height))
        self.newline()
        self.write(":location ")
        if msg.HasField("root_pageid"):
            self.write("(:root_pageid ")
            self.pprint_dispatch(msg.root_pageid)
            self.write(")")
        else:
            if msg.HasField("inline_data"):
                self.write("(:inline_data ")
                self.write("0x" + msg.inline_data.hex())
                self.write(")")
            else:
                self.write("nothing")
        self.write(")")
        self.dedent()

    def pretty_decimal_value(self, msg: logic_pb2.DecimalValue):
        self.write(self.format_decimal(msg))

    def pretty_functional_dependency(self, msg: logic_pb2.FunctionalDependency):
        self.write("(functional_dependency")
        self.indent_sexp()
        self.newline()
        self.write(":guard ")
        self.pprint_dispatch(msg.guard)
        self.newline()
        self.write(":keys ")
        self.write("(")
        for _idx, _elem in enumerate(msg.keys):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write(")")
        self.newline()
        self.write(":values ")
        self.write("(")
        for _idx, _elem in enumerate(msg.values):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write(")")
        self.write(")")
        self.dedent()

    def pretty_int128_value(self, msg: logic_pb2.Int128Value):
        self.write(self.format_int128(msg))

    def pretty_missing_value(self, msg: logic_pb2.MissingValue):
        self.write("missing")

    def pretty_u_int128_value(self, msg: logic_pb2.UInt128Value):
        self.write(self.format_uint128(msg))

    def pretty_ivm_config(self, msg: transactions_pb2.IVMConfig):
        self.write("(ivm_config")
        self.indent_sexp()
        self.newline()
        self.write(":level ")
        self.pprint_dispatch(msg.level)
        self.write(")")
        self.dedent()

    def pretty_maintenance_level(self, x: int):
        if x == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_UNSPECIFIED:
            self.write("unspecified")
        else:
            if x == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                self.write("off")
            else:
                if x == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
                    self.write("auto")
                else:
                    if x == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                        self.write("all")

    # --- Dispatch ---

    def pprint_dispatch(self, msg):
        if isinstance(msg, transactions_pb2.Transaction):
            self.pretty_transaction(msg)
        elif isinstance(msg, transactions_pb2.Configure):
            self.pretty_configure(msg)
        elif isinstance(msg, logic_pb2.Value):
            self.pretty_value(msg)
        elif isinstance(msg, logic_pb2.DateValue):
            self.pretty_date(msg)
        elif isinstance(msg, logic_pb2.DateTimeValue):
            self.pretty_datetime(msg)
        elif isinstance(msg, bool):
            self.pretty_boolean_value(msg)
        elif isinstance(msg, transactions_pb2.Sync):
            self.pretty_sync(msg)
        elif isinstance(msg, fragments_pb2.FragmentId):
            self.pretty_fragment_id(msg)
        elif isinstance(msg, transactions_pb2.Epoch):
            self.pretty_epoch(msg)
        elif isinstance(msg, transactions_pb2.Write):
            self.pretty_write(msg)
        elif isinstance(msg, transactions_pb2.Define):
            self.pretty_define(msg)
        elif isinstance(msg, fragments_pb2.Fragment):
            self.pretty_fragment(msg)
        elif isinstance(msg, logic_pb2.Declaration):
            self.pretty_declaration(msg)
        elif isinstance(msg, logic_pb2.Def):
            self.pretty_def(msg)
        elif isinstance(msg, logic_pb2.RelationId):
            self.pretty_relation_id(msg)
        elif isinstance(msg, logic_pb2.Abstraction):
            self.pretty_abstraction(msg)
        elif isinstance(msg, logic_pb2.Binding):
            self.pretty_binding(msg)
        elif isinstance(msg, logic_pb2.Type):
            self.pretty_type(msg)
        elif isinstance(msg, logic_pb2.UnspecifiedType):
            self.pretty_unspecified_type(msg)
        elif isinstance(msg, logic_pb2.StringType):
            self.pretty_string_type(msg)
        elif isinstance(msg, logic_pb2.IntType):
            self.pretty_int_type(msg)
        elif isinstance(msg, logic_pb2.FloatType):
            self.pretty_float_type(msg)
        elif isinstance(msg, logic_pb2.UInt128Type):
            self.pretty_uint128_type(msg)
        elif isinstance(msg, logic_pb2.Int128Type):
            self.pretty_int128_type(msg)
        elif isinstance(msg, logic_pb2.DateType):
            self.pretty_date_type(msg)
        elif isinstance(msg, logic_pb2.DateTimeType):
            self.pretty_datetime_type(msg)
        elif isinstance(msg, logic_pb2.MissingType):
            self.pretty_missing_type(msg)
        elif isinstance(msg, logic_pb2.DecimalType):
            self.pretty_decimal_type(msg)
        elif isinstance(msg, logic_pb2.BooleanType):
            self.pretty_boolean_type(msg)
        elif isinstance(msg, logic_pb2.Formula):
            self.pretty_formula(msg)
        elif isinstance(msg, logic_pb2.Conjunction):
            self.pretty_conjunction(msg)
        elif isinstance(msg, logic_pb2.Disjunction):
            self.pretty_disjunction(msg)
        elif isinstance(msg, logic_pb2.Exists):
            self.pretty_exists(msg)
        elif isinstance(msg, logic_pb2.Reduce):
            self.pretty_reduce(msg)
        elif isinstance(msg, logic_pb2.Term):
            self.pretty_term(msg)
        elif isinstance(msg, logic_pb2.Var):
            self.pretty_var(msg)
        elif isinstance(msg, logic_pb2.Not):
            self.pretty_not(msg)
        elif isinstance(msg, logic_pb2.FFI):
            self.pretty_ffi(msg)
        elif isinstance(msg, str):
            self.pretty_name(msg)
        elif isinstance(msg, logic_pb2.Atom):
            self.pretty_atom(msg)
        elif isinstance(msg, logic_pb2.Pragma):
            self.pretty_pragma(msg)
        elif isinstance(msg, logic_pb2.Primitive):
            self.pretty_primitive(msg)
        elif isinstance(msg, logic_pb2.RelTerm):
            self.pretty_rel_term(msg)
        elif isinstance(msg, logic_pb2.RelAtom):
            self.pretty_rel_atom(msg)
        elif isinstance(msg, logic_pb2.Cast):
            self.pretty_cast(msg)
        elif isinstance(msg, logic_pb2.Attribute):
            self.pretty_attribute(msg)
        elif isinstance(msg, logic_pb2.Algorithm):
            self.pretty_algorithm(msg)
        elif isinstance(msg, logic_pb2.Script):
            self.pretty_script(msg)
        elif isinstance(msg, logic_pb2.Construct):
            self.pretty_construct(msg)
        elif isinstance(msg, logic_pb2.Loop):
            self.pretty_loop(msg)
        elif isinstance(msg, logic_pb2.Instruction):
            self.pretty_instruction(msg)
        elif isinstance(msg, logic_pb2.Assign):
            self.pretty_assign(msg)
        elif isinstance(msg, logic_pb2.Upsert):
            self.pretty_upsert(msg)
        elif isinstance(msg, logic_pb2.Break):
            self.pretty_break(msg)
        elif isinstance(msg, logic_pb2.MonoidDef):
            self.pretty_monoid_def(msg)
        elif isinstance(msg, logic_pb2.Monoid):
            self.pretty_monoid(msg)
        elif isinstance(msg, logic_pb2.OrMonoid):
            self.pretty_or_monoid(msg)
        elif isinstance(msg, logic_pb2.MinMonoid):
            self.pretty_min_monoid(msg)
        elif isinstance(msg, logic_pb2.MaxMonoid):
            self.pretty_max_monoid(msg)
        elif isinstance(msg, logic_pb2.SumMonoid):
            self.pretty_sum_monoid(msg)
        elif isinstance(msg, logic_pb2.MonusDef):
            self.pretty_monus_def(msg)
        elif isinstance(msg, logic_pb2.Constraint):
            self.pretty_constraint(msg)
        elif isinstance(msg, logic_pb2.Data):
            self.pretty_data(msg)
        elif isinstance(msg, logic_pb2.RelEDB):
            self.pretty_rel_edb(msg)
        elif isinstance(msg, logic_pb2.BeTreeRelation):
            self.pretty_betree_relation(msg)
        elif isinstance(msg, logic_pb2.BeTreeInfo):
            self.pretty_betree_info(msg)
        elif isinstance(msg, logic_pb2.CSVData):
            self.pretty_csv_data(msg)
        elif isinstance(msg, logic_pb2.CSVLocator):
            self.pretty_csvlocator(msg)
        elif isinstance(msg, logic_pb2.CSVConfig):
            self.pretty_csv_config(msg)
        elif isinstance(msg, logic_pb2.CSVColumn):
            self.pretty_csv_column(msg)
        elif isinstance(msg, transactions_pb2.Undefine):
            self.pretty_undefine(msg)
        elif isinstance(msg, transactions_pb2.Context):
            self.pretty_context(msg)
        elif isinstance(msg, transactions_pb2.Snapshot):
            self.pretty_snapshot(msg)
        elif isinstance(msg, transactions_pb2.Read):
            self.pretty_read(msg)
        elif isinstance(msg, transactions_pb2.Demand):
            self.pretty_demand(msg)
        elif isinstance(msg, transactions_pb2.Output):
            self.pretty_output(msg)
        elif isinstance(msg, transactions_pb2.WhatIf):
            self.pretty_what_if(msg)
        elif isinstance(msg, transactions_pb2.Abort):
            self.pretty_abort(msg)
        elif isinstance(msg, transactions_pb2.Export):
            self.pretty_export(msg)
        elif isinstance(msg, transactions_pb2.ExportCSVConfig):
            self.pretty_export_csv_config(msg)
        elif isinstance(msg, transactions_pb2.ExportCSVColumn):
            self.pretty_export_csv_column(msg)
        elif isinstance(msg, fragments_pb2.DebugInfo):
            self.pretty_debug_info(msg)
        elif isinstance(msg, logic_pb2.BeTreeConfig):
            self.pretty_be_tree_config(msg)
        elif isinstance(msg, logic_pb2.BeTreeLocator):
            self.pretty_be_tree_locator(msg)
        elif isinstance(msg, logic_pb2.DecimalValue):
            self.pretty_decimal_value(msg)
        elif isinstance(msg, logic_pb2.FunctionalDependency):
            self.pretty_functional_dependency(msg)
        elif isinstance(msg, logic_pb2.Int128Value):
            self.pretty_int128_value(msg)
        elif isinstance(msg, logic_pb2.MissingValue):
            self.pretty_missing_value(msg)
        elif isinstance(msg, logic_pb2.UInt128Value):
            self.pretty_u_int128_value(msg)
        elif isinstance(msg, transactions_pb2.IVMConfig):
            self.pretty_ivm_config(msg)
        # enum: int
        elif isinstance(msg, int):
            self.pretty_maintenance_level(msg)
        else:
            raise ParseError(f"no pretty printer for {type(msg)}")

def pretty(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()


def pretty_debug(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message with raw relation IDs and debug info appended as comments."""
    printer = PrettyPrinter(io, max_width=max_width, print_symbolic_relation_ids=False)
    printer.pretty_transaction(msg)
    printer.newline()
    printer.write_debug_info()
    return printer.get_output()
